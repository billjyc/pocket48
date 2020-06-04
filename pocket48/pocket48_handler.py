# -*- coding:utf-8 -*-

import json
import os
import sqlite3
import time

import requests

from log.my_logger import pocket48_logger as logger
from qq.qqhandler import QQHandler
from utils import global_config, util


class Member:
    def __init__(self, name, member_id, room_id, weibo_uid=0, pinyin=''):
        self.name = name
        self.member_id = member_id
        self.room_id = room_id
        self.weibo_uid = weibo_uid
        self.pinyin = pinyin


class MessageType:
    TEXT = 'TEXT'  # 文字消息
    IMAGE = 'IMAGE'  # 图片消息
    EXPRESS = 'EXPRESS'  # 大表情
    AUDIO = 'AUDIO'  # 语音
    VIDEO = 'VIDEO'  # 视频


class TextMessageType:
    TEXT = 'TEXT'  # 普通文字消息
    REPLY = 'REPLY'  # 普通翻牌
    FLIPCARD = 'FLIPCARD'  # 鸡腿翻牌
    LIVEPUSH = 'LIVEPUSH'  # 直播
    VOTE = 'VOTE'  # 投票
    PASSWORD_REDPACKAGE = 'PASSWORD_REDPACKAGE'  # 红包消息


class Pocket48ListenTask:
    def __init__(self, member):
        self.member = member
        self.member_room_msg_groups = []
        self.member_live_groups = []
        self.member_room_msg_lite_groups = []
        self.room_comment_groups = []
        self.lite_message = ''

        self.member_room_msg_ids = []
        self.member_room_comment_ids = []
        self.member_live_ids = []

        # 成员房间未读消息数量
        self.unread_msg_amount = 0
        # 成员房间其他成员的未读消息数量
        self.unread_other_member_msg_amount = 0

        self.other_members_names = []
        self.last_other_member_msg_time = -1
        self.last_msg_time = -1


class Pocket48Handler:
    def __init__(self):
        self.session = requests.session()
        self.token = '0'
        self.is_login = False
        self.auto_reply_groups = []
        self.test_groups = []

        self.listen_tasks = []

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'statistic', 'statistics.db')
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = self.conn.cursor()

        cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_message (
                    message_id   VARCHAR PRIMARY KEY UNIQUE,
                    type         INTEGER,
                    user_id      INTEGER,
                    user_name    VARCHAR,
                    message_time DATETIME,
                    content      VARCHAR,
                    fans_comment VARCHAR,
                    fans_name VARCHAR
                );
                """)
        cursor.close()

    def login(self, username, password):
        """
        登录
        :param username:
        :param password:
        :return:
        """
        if self.is_login is True:
            logger.error('已经登录！')
            return
        if username is None or password is None:
            logger.error('用户名或密码为空')
            return

        login_url = 'https://pocketapi.48.cn/user/api/v1/login/app/mobile'
        params = {
            'pwd': str(password),
            'mobile': str(username),
        }
        res = self.session.post(login_url, json=params, headers=self.login_header_args()).json()
        # 登录成功
        if res['status'] == 200:
            self.token = res['content']['token']
            global_config.POCKET48_TOKEN = res['content']['token']
            self.is_login = True
            logger.info('登录成功, 用户名: %s', username)
            logger.info('TOKEN: %s', self.token)
            return True
        else:
            logger.error('登录失败, 原因: {}'.format(res['message']))
        return False

    def logout(self):
        """
        登出
        :return:
        """
        self.is_login = False
        self.token = '0'

    # def get_member_live_msg(self, limit=50):
    #     """
    #     获取所有直播间信息
    #     :return:
    #     """
    #     if not self.is_login:
    #         logger.error('尚未登录')
    #     url = 'https://plive.48.cn/livesystem/api/live/v1/memberLivePage'
    #     params = {
    #         "giftUpdTime": int(time.time() * 1000),
    #         "groupId": 0,  # SNH48 Group所有人
    #         "lastTime": 0,
    #         "limit": limit,
    #         "memberId": 0,
    #         "type": 0
    #     }
    #     try:
    #         r = self.session.post(url, data=json.dumps(params), headers=self.live_header_args(), verify=False)
    #     except Exception as e:
    #         logger.error('获取成员直播失败')
    #         logger.exception(e)
    #     return r.text

    def get_member_room_msg(self, task, limit=20):
        """
        获取成员房间消息
        :param limit:
        :param task: 监听任务
        :return:
        """
        if not self.is_login:
            logger.error('尚未登录')
        # url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner'
        params = {
            "ownerId": task.member.member_id,
            "roomId": task.member.room_id,
            "nextTime": 0
        }
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
        except Exception as e:
            logger.error('获取成员消息失败, room_id={}, name={}'.format(task.member.room_id, task.member.name))
            logger.exception(e)
        return r.text

    def init_msg_queues(self, task):
        """
        初始化房间消息队列
        :param task:
        :return:
        """
        try:
            task.member_room_msg_ids = []
            task.member_room_comment_ids = []
            task.member_live_ids = []

            task.unread_msg_amount = 0

            r1 = self.get_member_room_msg(task)
            r2 = self.get_member_room_comment(task)

            r1_json = json.loads(r1)
            r2_json = json.loads(r2)
            for r in r1_json['content']['message']:
                msg_id = r['msgidClient']
                task.member_room_msg_ids.append(msg_id)

            for r in r2_json['content']['message']:
                msg_id = r['msgidClient']
                task.member_room_comment_ids.append(msg_id)

            logger.debug('成员{}消息队列: {}'.format(task.member.name, len(task.member_room_msg_ids)))
            logger.debug('{}房间评论队列: {}'.format(task.member.name, len(task.member_room_comment_ids)))
            logger.debug('{}房间未读消息数量: {}'.format(task.member.name, task.unread_msg_amount))
        except Exception as e:
            logger.error('初始化{}消息队列失败'.format(task.member.name))
            logger.exception(e)

    def get_member_room_msg_lite(self, task):
        """
        发送成员房间消息提醒（简易版，只提醒在房间里出现）
        :param task:
        :return:
        """
        time_now = time.time()
        msg = ''
        logger.debug('timenow: %s', time_now)
        logger.debug('unread_other_member_msg_amount=%s', task.unread_other_member_msg_amount)
        logger.debug('last_other_member_msg_time: %s', task.last_other_member_msg_time)
        logger.debug('time_now - self.last_other_member_msg_time: %s', time_now - task.last_other_member_msg_time)

        if task.unread_other_member_msg_amount > 0 and len(task.member_room_msg_lite_groups) > 0:
            if task.last_other_member_msg_time < 0 or time_now - task.last_other_member_msg_time >= 10 * 60:
                logger.debug('其他成员出现在房间中')
                member_name = ', '.join(task.other_members_names)
                QQHandler.send_to_groups(task.member_room_msg_lite_groups, '%s来你们灰的房间里串门啦~' % member_name)
            task.unread_other_member_msg_amount = 0
            task.last_other_member_msg_time = time_now
            task.other_members_names.clear()

        logger.debug('unread_msg_amount=%s', task.unread_msg_amount)
        logger.debug('last_msg_time: %s', task.last_msg_time)
        logger.debug('time_now - self.last_msg_time: %s', time_now - task.last_msg_time)

        if task.unread_msg_amount > 0 and len(task.member_room_msg_lite_groups) > 0:
            # 距离上一次提醒时间超过10分钟且有未读消息
            if task.last_msg_time < 0 or time_now - task.last_msg_time >= 10 * 60:
                logger.debug('向大群发送简易版提醒')
                msg = util.random_str(global_config.ROOM_MSG_LITE_NOTIFY)
                if global_config.USING_COOLQ_PRO:
                    msg += '[CQ:image,file=http://wx3.sinaimg.cn/large/789c06f9gy1fq4dl21j0rj20k00k0jsl.jpg]'
                logger.debug(task.member_room_msg_lite_groups)
                QQHandler.send_to_groups(task.member_room_msg_lite_groups, msg)
                logger.info(msg)

            else:
                logger.debug('不向大群发送简易版提醒')
            task.last_msg_time = time_now
            task.unread_msg_amount = 0
        else:
            logger.info('最近10分钟内没有未读消息')

    def parse_room_msg(self, response, task):
        """
        对成员消息进行处理
        :param response:
        :param task:
        :return:
        """
        logger.debug('parse room msg response: %s', response)
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['message']
        cursor = self.conn.cursor()

        message = ''
        try:
            for msg in msgs:
                extInfo = json.loads(msg['extInfo'])
                msg_id = msg['msgidClient']  # 消息id

                if msg_id in task.member_room_msg_ids:
                    continue
                logger.debug('session role: {}'.format(extInfo['sessionRole']))
                if int(extInfo['sessionRole']) != 2:  # 其他成员的消息
                    task.unread_other_member_msg_amount += 1
                    member_name = extInfo['user']['nickName']
                    if member_name == '19岁了还是小可爱':
                        member_name = 'YBY'
                    if member_name not in task.other_members_names:
                        task.other_members_names.append(member_name)
                else:
                    task.unread_msg_amount += 1

                logger.debug('成员消息')
                task.member_room_msg_ids.append(msg_id)

                msg_time = util.convert_timestamp_to_timestr(msg["msgTime"])
                user_id = extInfo['user']['userId']
                user_name = extInfo['user']['nickName']

                logger.debug('extInfo.keys():' + ','.join(extInfo.keys()))
                if msg['msgType'] == MessageType.TEXT:  # 文字消息
                    text_message_type = extInfo['messageType'].strip()
                    if text_message_type == TextMessageType.TEXT:  # 普通消息
                        logger.debug('普通消息')
                        message = ('【成员消息】[%s]-%s: %s\n' % (
                            msg_time, user_name, extInfo['text'])) + message
                        self.save_msg_to_db(100, msg_id, user_id, user_name, msg_time, extInfo['text'])
                    elif text_message_type == TextMessageType.REPLY:  # 翻牌消息
                        logger.debug('翻牌')
                        member_msg = extInfo['text']
                        fanpai_msg = extInfo['replyText']
                        fanpai_id = extInfo['replyName']
                        if fanpai_id:
                            message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s: %s\n' % (
                                msg_time, user_name, member_msg, fanpai_id, fanpai_msg)) + message
                            self.save_msg_to_db(101, msg_id, user_id, user_name, msg_time, member_msg,
                                                fanpai_msg, fanpai_id)
                        else:
                            message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                                msg_time, user_name, member_msg, fanpai_msg)) + message
                            self.save_msg_to_db(101, msg_id, user_id, user_name, msg_time, member_msg, fanpai_msg)
                    elif text_message_type == TextMessageType.LIVEPUSH:  # 直播
                        logger.debug('直播')
                        live_title = extInfo['liveTitle']
                        live_id = extInfo['liveId']
                        playStreamPath, playDetail = self.get_live_detail(live_id)
                        self.save_msg_to_db(102, msg_id, user_id, user_name, msg_time, live_title)

                        live_message = '你们的崽崽开直播了\n直播标题: {}\n开始时间: {}'.format(live_title, msg_time)
                        QQHandler.send_to_groups(task.member_room_msg_groups, live_message)
                    elif text_message_type == TextMessageType.VOTE:  # 投票
                        logger.debug('投票消息')
                        vote_content = extInfo['text']
                        message = '【发起投票】{}: {}\n'.format(user_name, vote_content) + message
                        self.save_msg_to_db(104, msg_id, user_id, user_name, msg_time, vote_content)
                    elif text_message_type == TextMessageType.FLIPCARD:
                        logger.debug('付费翻牌功能')
                        content = extInfo['question']

                        question_id = extInfo['questionId']
                        answer_id = extInfo['answerId']
                        source = extInfo['sourceId']
                        answer = extInfo['answer']

                        fan_name = self.get_idol_flip_name(answer_id, question_id)
                        if fan_name:
                            flip_message = ('【问】%s: %s\n【答】%s: %s\n翻牌时间: %s\n' % (
                                fan_name, content, user_name, answer, msg_time))
                            self.save_msg_to_db(105, msg_id, user_id, user_name, msg_time, answer, content, fan_name)
                        else:
                            flip_message = ('【问】%s\n【答】%s: %s\n翻牌时间: %s\n' % (
                                content, user_name, answer, msg_time))
                            self.save_msg_to_db(105, msg_id, user_id, user_name, msg_time, answer, content)
                        message = flip_message + message

                    elif text_message_type == TextMessageType.PASSWORD_REDPACKAGE:
                        print('红包消息')
                        content = '【红包】{}'.format(extInfo['redPackageTitle'])
                        self.save_msg_to_db(106, msg_id, user_id, user_name, msg_time, content)
                elif msg['msgType'] == MessageType.IMAGE:  # 图片消息
                    logger.debug('图片')
                    bodys = json.loads(msg['bodys'])
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        if global_config.USING_COOLQ_PRO is True:
                            message = ('【图片】[%s]-%s: [CQ:image,file=%s]\n' % (
                                msg_time, user_name, url)) + message
                        else:
                            message = ('【图片】[%s]-%s: %s\n' % (msg_time, user_name, url)) + message
                        self.save_msg_to_db(200, msg_id, user_id, user_name, msg_time, url)
                elif msg['msgType'] == MessageType.AUDIO:  # 语音消息
                    logger.debug('语音消息')
                    bodys = json.loads(msg['bodys'])
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        if global_config.USING_COOLQ_PRO is True:
                            message3 = ('【语音】[%s]-%s: %s\n' % (msg_time, user_name, url))
                            logger.info(message3)
                            # 语音消息直接单条发送
                            message2 = '[CQ:record,file={}]\n'.format(url)
                            QQHandler.send_to_groups(task.member_room_msg_groups, message2)
                        else:
                            message = ('【语音】[%s]-%s: %s\n' % (msg_time, user_name, url)) + message
                        self.save_msg_to_db(201, msg_id, user_id, user_name, msg_time, url)
                elif msg['msgType'] == MessageType.VIDEO:  # 小视频
                    logger.debug('房间小视频')
                    bodys = json.loads(msg['bodys'])
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        message = ('【小视频】[%s]-%s: %s\n' % (msg_time, user_name, url)) + message
                        self.save_msg_to_db(202, msg_id, user_id, user_name, msg_time, url)
                elif msg['msgType'] == MessageType.EXPRESS:  # 大表情
                    logger.debug('大表情')
                    emotion_name = extInfo['emotionName']
                    if global_config.USING_COOLQ_PRO is True:
                        if 'tsj' in emotion_name:
                            express_message = '[%s]-%s: [CQ:image,file=%s]' % (
                                msg_time, user_name, '{}.gif'.format(emotion_name))
                        else:
                            express_message = '[%s]-%s: [CQ:image,file=%s]' % (
                                msg_time, user_name, '{}.png'.format(emotion_name))
                        message = express_message + message
                    self.save_msg_to_db(203, msg_id, user_id, user_name, msg_time, emotion_name)
            if message and len(task.member_room_msg_groups) > 0:
                # express_message = '[CQ:image,file=%s]' % (
                #      'express\\tsj000.gif')
                # express_message2 = '[CQ:image,file=%s]' % (
                #      'express\\lt001.png')
                QQHandler.send_to_groups(task.member_room_msg_groups, message)
                self.get_member_room_msg_lite(task)
                logger.info('message: %s', message)
                # QQHandler.send_to_groups(task.member_room_msg_groups, express_message)
                # QQHandler.send_to_groups(task.member_room_msg_groups, express_message2)
            logger.debug('成员{}消息队列: {}'.format(task.member.name, len(task.member_room_msg_ids)))
        except Exception as e:
            logger.exception(e)
        finally:
            self.conn.commit()
            cursor.close()

    def save_msg_to_db(self, op_code, message_id, user_id, user_name, message_time, content, fans_comment='',
                       fans_name=''):
        """
        将消息存进db
        :param fans_name:
        :param op_code:
        :param message_id:
        :param user_id:
        :param user_name:
        :param message_time:
        :param content:
        :param fans_comment:
        :return:
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                            INSERT OR IGNORE INTO 'room_message' (message_id, type, user_id, user_name, message_time, 
                            content, fans_comment, fans_name) VALUES
                                                       (?, ?, ?, ?, ?, ?, ?, ?)
                         """, (message_id, op_code, user_id, user_name, message_time, content, fans_comment, fans_name))
        except Exception as e:
            logger.error('将口袋房间消息存入数据库')
            logger.exception(e)
        finally:
            self.conn.commit()
            cursor.close()

    def parse_idol_flip(self, question_id, answer_id, source):
        url = 'https://ppayqa.48.cn/idolanswersystem/api/idolanswer/v1/question_answer/detail'
        params = {
            "questionId": question_id, "answerId": answer_id, "idolFlipSource": source
        }

        res = self.session.post(url, data=json.dumps(params), headers=self.idol_flip_header_args()).json()
        return res['content']['answer']

    def parse_room_comment(self, response, task):
        """
        对房间评论进行处理
        :param response:
        :param task:
        :return:
        """
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['message']
        logger.debug('parse room comment reponse: %s', response)
        message = ''
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']
            total_msg_type = msg['msgType']
            msg_type = extInfo['messageType']
            msg_time = util.convert_timestamp_to_timestr(msg['msgTime'])

            if msg_id in task.member_room_comment_ids:
                continue
            logger.debug('该评论{}不在队列中，需要打印'.format(msg_id))
            task.member_room_comment_ids.append(msg_id)
            user_id = extInfo['user']['nickName']

            if total_msg_type == 'TEXT':
                if msg_type == 'TEXT':
                    logger.debug('房间评论')
                    logger.debug('【房间评论】[%s]-%s: %s\n' % (
                        msg_time,
                        user_id, extInfo['text']))
                elif msg_type == 'PRESENT_TEXT':
                    gift_num = extInfo['giftInfo']['giftNum']
                    gift_name = extInfo['giftInfo']['giftName']
                    if extInfo['giftInfo']['isVote']:
                        logger.debug('投票')
                        message = '感谢{}送出的{}票，爱你呦~\n【{}】'.format(user_id, gift_num,
                                                                 msg_time)
                        logger.debug(message)
                        if message and len(task.member_room_msg_groups) > 0:
                            QQHandler.send_to_groups(task.member_room_msg_groups, message)
                    else:
                        logger.debug('礼物')
                        logger.debug('感谢{}送出的{}个{}，爱你呦~'.format(user_id, gift_num, gift_name))
                else:
                    logger.debug('其他类型评论')

        # logger.info('message: %s', message)
        # logger.debug('length of comment groups: %d', len(task.member_room_comment_msg_groups))
        logger.debug('房间评论队列: %s', len(task.member_room_comment_ids))

    def get_member_room_comment(self, task, limit=20):
        """
        获取成员房间的粉丝评论
        :param limit:
        :param task:
        :return:
        """
        if not self.is_login:
            logger.error('尚未登录')
        url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/all'
        params = {
            "roomId": task.member.room_id, "ownerId": task.member.member_id
        }
        # 收到响应
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
        except Exception as e:
            logger.error('获取房间评论失败！name: {}, room_id: {}'.format(task.member.name, task.member.room_id))
            logger.exception(e)
        return r.text

    def checkin(self):
        """
        签到
        :return:
        """
        if not self.is_login:
            logger.error('尚未登录')
        url = 'https://pocketapi.48.cn/user/api/v1/checkin'
        # 收到响应
        try:
            r = self.session.post(url, headers=self.juju_header_args(), verify=False).json()
            if r['status'] == 200:
                logger.info('签到成功，经验+{}, 应援力+{}'.format(r['content']['addExp'], r['content']['addSupport']))
                return True
            else:
                return False
        except Exception as e:
            logger.error('签到失败！')
            logger.exception(e)
            return False

    def kuan_time_broadcast(self):
        """
        款时播报
        :return:
        """
        QQHandler.send_to_groups(['101724227'], '款时')

    # def parse_member_live(self, response, task):
    #     """
    #     对直播列表进行处理，找到正在直播的指定成员
    #     :param response:
    #     :param task
    #     :return:
    #     """
    #     rsp_json = json.loads(response)
    #     # logger.debug('rsp_json: %s' % rsp_json)
    #     logger.debug('keys of parse member live: %s', rsp_json['content'].keys())
    #     member_id = task.member.member_id
    #     # 当前没有人在直播
    #     if 'liveList' not in rsp_json['content'].keys():
    #         # print 'no live'
    #         logger.debug('当前没有人在直播')
    #         return
    #     live_list = rsp_json['content']["liveList"]
    #     logger.debug('当前正在直播的人数: %d', len(live_list))
    #     # print '当前正在直播的人数: %d' % len(live_list)
    #     msg = ''
    #     # logger.debug('直播ID列表: %s', ','.join(self.member_live_ids))
    #     for live in live_list:
    #         live_id = live['liveId']
    #         # logger.debug(live.keys())
    #         # print '直播人: %s' % live['memberId']
    #         # logger.debug('直播人(response): %s, 类型: %s', live['memberId'], type(live['memberId']))
    #         # logger.debug('member_id(参数): %s, 类型: %s', member_id, type(member_id))
    #         logger.debug('memberId %s is in live: %s, live_id: %s', live['memberId'], live['title'], live_id)
    #         logger.debug('stream path: %s', live['streamPath'])
    #         # logger.debug('member_live_ids list: %s', ','.join(self.member_live_ids))
    #         # logger.debug('live_id is in member_live_ids: %s', str(live_id in self.member_live_ids))
    #         if live['memberId'] == int(member_id) and live_id not in task.member_live_ids:
    #             logger.debug('[被监控成员正在直播]member_id: %s, live_id: %s', member_id, live_id)
    #             start_time = util.convert_timestamp_to_timestr(live['startTime'])
    #             stream_path = live['streamPath']  # 流地址
    #             sub_title = live['subTitle']  # 直播名称
    #             live_type = live['liveType']
    #             url = 'https://h5.48.cn/2017appshare/memberLiveShare/index.html?id=%s' % live_id
    #             if live_type == 1:  # 露脸直播
    #                 msg += '你的小宝贝儿开露脸直播了: %s\n直播链接: %s\n开始时间: %s' % (sub_title, url, start_time)
    #             elif live_type == 2:  # 电台直播
    #                 msg += '你的小宝贝儿开电台直播了: %s\n直播链接: %s\n开始时间: %s' % (sub_title, url, start_time)
    #             task.member_live_ids.append(live_id)
    #
    #     logger.debug(msg)
    #     if msg and len(task.member_live_groups) > 0:
    #         QQHandler.send_to_groups(task.member_live_groups, msg)

    def login_header_args(self):
        """
        构造登录请求头信息
        :return:
        """
        header = {
            'Content-Type': 'application/json;charset=utf-8',
            'User-Agent': 'PocketFans201807/6.0.13 (iPad; iOS 13.5; Scale/2.00)',
            'pa': 'MTU5MTE5NzQzNjAwMCwzNTcxLDNDRTAxM0ZCNTk1NUI0RUE2RURCOENFN0IzMjBCNzdG',
            'Host': 'pocketapi.48.cn',
            'appInfo': json.dumps({
                'vendor': 'apple',
                'deviceId': '1A9A4601-4D1A-49AD-AEF0-EE2462025A2C',
                "appVersion": global_config.POCKET48_VERSION,
                "appBuild": "200513",
                "osVersion": "13.5.0",
                "osType": "ios",
                "deviceName": "unknow",
                "os": "ios"
            }),
        }
        return header

    def live_header_args(self):
        """
        构造直播请求头信息
        :return:
        """
        header = {
            'Content-Type': 'application/json;charset=utf-8',
            'User-Agent': 'PocketFans201807/6.0.13 (iPad; iOS 13.5; Scale/2.00)',
            'pa': 'MTU5MTE5NzQzNjAwMCwzNTcxLDNDRTAxM0ZCNTk1NUI0RUE2RURCOENFN0IzMjBCNzdG',
            'Host': 'pocketapi.48.cn',
            'appInfo': json.dumps({
                'vendor': 'apple',
                'deviceId': '1A9A4601-4D1A-49AD-AEF0-EE2462025A2C',
                "appVersion": global_config.POCKET48_VERSION,
                "appBuild": "200513",
                "osVersion": "13.5.0",
                "osType": "ios",
                "deviceName": "unknow",
                "os": "ios"
            }),
            'token': self.token
        }
        return header

    def juju_header_args(self):
        """
        构造聚聚房间请求头信息
        :return:
        """
        logger.debug('token: %s', self.token)
        header = {
            'Content-Type': 'application/json;charset=utf-8',
            'User-Agent': 'PocketFans201807/6.0.13 (iPad; iOS 13.5; Scale/2.00)',
            'pa': 'MTU5MTE5NzQzNjAwMCwzNTcxLDNDRTAxM0ZCNTk1NUI0RUE2RURCOENFN0IzMjBCNzdG',
            'Host': 'pocketapi.48.cn',
            'appInfo': json.dumps({
                'vendor': 'apple',
                'deviceId': '1A9A4601-4D1A-49AD-AEF0-EE2462025A2C',
                "appVersion": global_config.POCKET48_VERSION,
                "appBuild": "200513",
                "osVersion": "13.5.0",
                "osType": "ios",
                "deviceName": "unknow",
                "os": "ios"
            }),
            'token': self.token
        }
        return header

    def idol_flip_header_args(self):
        """
        构造收费翻牌请求头信息
        :return:
        """
        logger.debug('token: %s', self.token)
        header = {
            'Content-Type': 'application/json;charset=utf-8',
            'User-Agent': 'PocketFans201807/6.0.13 (iPad; iOS 13.5; Scale/2.00)',
            'pa': 'MTU5MTE5NzQzNjAwMCwzNTcxLDNDRTAxM0ZCNTk1NUI0RUE2RURCOENFN0IzMjBCNzdG',
            'Host': 'pocketapi.48.cn',
            'appInfo': json.dumps({
                'vendor': 'apple',
                'deviceId': '1A9A4601-4D1A-49AD-AEF0-EE2462025A2C',
                "appVersion": global_config.POCKET48_VERSION,
                "appBuild": "200513",
                "osVersion": "13.5.0",
                "osType": "ios",
                "deviceName": "unknow",
                "os": "ios"
            }),
            'token': self.token
        }
        return header

    def notify_performance(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'data', 'schedule.json')
        f = open(db_path, encoding='utf8')

        schedules = json.load(f)
        for s in schedules['schedules']:
            logger.debug(s)
            perform_time = util.convert_timestr_to_timestamp(s['time'])
            logger.debug('【日程提醒】perform_time: {}, current_time: {}'.format(perform_time, time.time()))
            diff = perform_time - time.time()
            if 0 < diff <= 15 * 60:
                live_link = ''.join(global_config.LIVE_LINK)
                live_msg = '直播传送门: %s' % live_link
                notify_str = '%s\n公演: %s\n时间: %s\n队伍: %s\n%s' % (
                    global_config.PERFORMANCE_NOTIFY, s['name'], s['time'], s['team'], live_msg)
                logger.info('notify str: %s', notify_str)
                QQHandler.send_to_groups(self.auto_reply_groups, notify_str)

    # def get_fanpai_name(self, fanpai_user_id):
    #     """
    #     获取普通翻牌用户的昵称
    #     :param fanpai_user_id:
    #     :return:
    #     """
    #     if not self.is_login:
    #         logger.exception('尚未登录')
    #         return
    #     url = 'http://zhibo.ckg48.com/Recharge/ajax_post_checkinfo'
    #     params = {
    #         "pocket_id": int(fanpai_user_id)
    #     }
    #     try:
    #         r = requests.post(url, data=params, verify=False, header=self.idol_flip_header_args()).json()
    #         logger.info('获取普通翻牌用户的昵称，user_id: {}'.format(fanpai_user_id))
    #         logger.info(r)
    #         return r['nickName']
    #     except Exception as e:
    #         logger.exception(e)
    #         return None

    def get_idol_flip_name(self, answer_id, question_id):
        """
        获取付费翻牌的提问id
        :param answer_id:
        :param question_id:
        :return:
        """
        if not self.is_login:
            logger.exception('尚未登录')
            return
        url = 'https://pocketapi.48.cn/idolanswer/api/idolanswer/v1/question_answer/detail'
        params = {
            "answerId": str(answer_id),
            "questionId": str(question_id)
        }
        try:
            r = requests.post(url, data=json.dumps(params), verify=False, headers=self.idol_flip_header_args()).json()
            logger.info('获取付费翻牌用户的昵称，user_id: {}'.format(r['content']['userName']))
            logger.info(r)
            return r['content']['userName']
        except Exception as e:
            logger.exception(e)
            return None

    def get_live_detail(self, live_id):
        """
        获取直播详情
        :param live_id:
        :return:
        """
        url = "https://pocketapi.48.cn/live/api/v1/live/getLiveOne"
        params = {
            "liveId": str(live_id)
        }
        r = self.session.post(url, data=params, headers=self.live_header_args(), verify=False,
                              timeout=15).json()
        if r['status'] == 200:
            playStreamPath = r['content']['playStreamPath']
            return playStreamPath, r
        else:
            return False, False


pocket48_handler = Pocket48Handler()

if __name__ == '__main__':
    # print(json.dumps({
    #     'vendor': 'apple',
    #     'deviceId': 0,
    #     "appVersion": '6.0.2',
    #     "appBuild": "190409",
    #     "osVersion": "12.2.0",
    #     "osType": "ios",
    #     "deviceName": "iphone",
    #     "os": "ios"
    # }))
    global_config.POCKET48_PA = util.generate_random_string(68)
    member = Member('左婧媛', '327577', '67380556')
    task = Pocket48ListenTask(member)
    pocket48_handler.login('****', '***')
    r = pocket48_handler.get_member_room_msg(task)
    pocket48_handler.parse_room_msg(r, task)
    # base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # db_path = os.path.join(base_dir, 'statistic', 'statistics.db')
    # print(db_path)
    # print(os.path.exists(db_path))
    #
    # params = {
    #     "questionId": 10513, "answerId": 7675, "questionFlipSource": 2
    # }
    # a = json.dumps(params)

    # bot.send_group_msg(group_id=483548995, message='test')
    # handler = Pocket48Handler([], [], [], [], [])
    #
    # handler.notify_performance()
    #
    # handler.login('*', '*')

    # response = handler.get_member_live_msg()
    # handler.parse_member_live(response, 528331)

    # r1 = handler.get_member_room_msg(5777252)
    # print(r1)
    #
    # r3 = handler.parse_idol_flip(10513, 7675, 2)
    # print(r3)

    # handler.parse_room_msg(r1)
    # r2 = handler.get_member_room_comment(5780791)
    # print(r2)
    # handler.parse_room_comment(r2)
    # print handler.convert_timestamp_to_timestr(1504970619679)
    pass
