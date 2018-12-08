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
                    message_id   VARCHAR,
                    type         INTEGER,
                    user_id      INTEGER,
                    user_name    VARCHAR,
                    message_time DATETIME,
                    content      VARCHAR,
                    fans_comment VARCHAR
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

        login_url = 'https://puser.48.cn/usersystem/api/user/v1/login/phone'
        params = {
            'latitude': '0',
            'longitude': '0',
            'password': str(password),
            'account': str(username),
        }
        res = self.session.post(login_url, json=params, headers=self.login_header_args()).json()
        # 登录成功
        if res['status'] == 200:
            self.token = res['content']['token']
            self.is_login = True
            logger.info('登录成功, 用户名: %s', username)
            logger.info('TOKEN: %s', self.token)
            return True
        else:
            logger.error('登录失败')
        return False

    def logout(self):
        """
        登出
        :return:
        """
        self.is_login = False
        self.token = '0'

    def get_member_live_msg(self, limit=50):
        """
        获取所有直播间信息
        :return:
        """
        if not self.is_login:
            logger.error('尚未登录')
        url = 'https://plive.48.cn/livesystem/api/live/v1/memberLivePage'
        params = {
            "giftUpdTime": int(time.time() * 1000),
            "groupId": 0,  # SNH48 Group所有人
            "lastTime": 0,
            "limit": limit,
            "memberId": 0,
            "type": 0
        }
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.live_header_args(), verify=False)
        except Exception as e:
            logger.error('获取成员直播失败')
            logger.exception(e)
        return r.text

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
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/mainpage'
        params = {
            "roomId": task.member.room_id, "lastTime": 0, "limit": limit, "chatType": 0
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

            r1 = self.get_member_room_msg(task.member.room_id)
            r2 = self.get_member_room_comment(task.member.room_id)

            r1_json = json.loads(r1)
            r2_json = json.loads(r2)
            for r in r1_json['content']['data']:
                msg_id = r['msgidClient']
                task.member_room_msg_ids.append(msg_id)

            for r in r2_json['content']['data']:
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
        msgs = rsp_json['content']['data']
        cursor = self.conn.cursor()

        message = ''
        try:
            for msg in msgs:
                extInfo = json.loads(msg['extInfo'])
                msg_id = msg['msgidClient']  # 消息id

                if msg_id in task.member_room_msg_ids:
                    continue

                if extInfo['role'] != 2:  # 其他成员的消息
                    task.unread_other_member_msg_amount += 1
                    member_name = extInfo['senderName']
                    if member_name == '你们的小可爱':
                        member_name = 'YBY'
                    if member_name not in task.other_members_names:
                        task.other_members_names.append(member_name)
                else:
                    task.unread_msg_amount += 1

                logger.debug('成员消息')
                task.member_room_msg_ids.append(msg_id)

                message_object = extInfo['messageObject']

                logger.debug('extInfo.keys():' + ','.join(extInfo.keys()))
                if msg['msgType'] == 0:  # 文字消息
                    if message_object == 'text':  # 普通消息
                        logger.debug('普通消息')
                        message = ('【成员消息】[%s]-%s: %s\n' % (
                            msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])) + message
                        cursor.execute("""
                            INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                            (?, ?, ?, ?, ?, ?)
                        """, (
                            msg_id, 100, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'],
                            extInfo['text']))
                    elif message_object == 'faipaiText':  # 翻牌消息
                        logger.debug('翻牌')
                        member_msg = extInfo['messageText']
                        fanpai_msg = extInfo['faipaiContent']
                        # fanpai_id = extInfo['faipaiName']
                        # message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s:%s\n' % (msg['msgTimeStr'], extInfo['senderName'], member_msg, fanpai_id, fanpai_msg)) + message
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                            msg['msgTimeStr'], extInfo['senderName'], member_msg, fanpai_msg)) + message
                        cursor.execute("""
                                        INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content, fans_comment) VALUES
                                        (?, ?, ?, ?, ?, ?, ?)
                                """, (
                            msg_id, 101, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], member_msg,
                            fanpai_msg))
                    # TODO: 直播可以直接在房间里监控
                    elif message_object == 'diantai':  # 电台直播
                        logger.debug('电台直播')
                        reference_content = extInfo['referenceContent']
                        live_id = extInfo['referenceObjectId']
                    elif message_object == 'live':  # 露脸直播
                        logger.debug('露脸直播')
                        reference_content = extInfo['referenceContent']
                        live_id = extInfo['referenceObjectId']
                    elif message_object == 'idolFlip':
                        logger.debug('付费翻牌功能')
                        user_name = extInfo['idolFlipUserName']
                        title = extInfo['idolFlipTitle']
                        content = extInfo['idolFlipContent']

                        question_id = extInfo['idolFlipQuestionId']
                        answer_id = extInfo['idolFlipAnswerId']
                        source = extInfo['idolFlipSource']
                        answer = self.parse_idol_flip(question_id, answer_id, source)

                        flip_message = ('【问】%s: %s\n【答】%s: %s\n翻牌时间: %s\n' % (
                            user_name, content, extInfo['senderName'], answer, msg['msgTimeStr']))
                        message = flip_message + message
                        QQHandler.send_to_groups(['108323016'], flip_message)
                        cursor.execute("""
                            INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content, fans_comment) VALUES
                            (?, ?, ?, ?, ?, ?, ?)
                            """, (msg_id, 105, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], answer,
                                  user_name + ': ' + content))
                elif msg['msgType'] == 1:  # 图片消息
                    bodys = json.loads(msg['bodys'])
                    logger.debug('图片')
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        if global_config.USING_COOLQ_PRO is True:
                            message = ('【图片】[%s]-%s: [CQ:image,file=%s]\n' % (
                                msg['msgTimeStr'], extInfo['senderName'], url)) + message
                        else:
                            message = ('【图片】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url)) + message
                        cursor.execute("""
                           INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                                                            (?, ?, ?, ?, ?, ?)
                        """, (msg_id, 200, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], url))

                elif msg['msgType'] == 2:  # 语音消息
                    logger.debug('语音消息')
                    bodys = json.loads(msg['bodys'])
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        if global_config.USING_COOLQ_PRO is True:
                            message3 = ('【语音】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url))
                            logger.info(message3)
                            # 语音消息直接单条发送
                            message2 = '[CQ:record,file=%s]\n' % url
                            QQHandler.send_to_groups(task.member_room_msg_groups, message2)
                        else:
                            message = ('【语音】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url)) + message
                        cursor.execute("""
                            INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                                                       (?, ?, ?, ?, ?, ?)
                         """, (msg_id, 201, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], url))
                elif msg['msgType'] == 3:  # 小视频
                    logger.debug('房间小视频')
                    bodys = json.loads(msg['bodys'])
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        message = ('【小视频】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url)) + message
                        cursor.execute("""
                         INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                                        (?, ?, ?, ?, ?, ?)
                        """, (msg_id, 202, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], url))

            if message and len(task.member_room_msg_groups) > 0:
                QQHandler.send_to_groups(task.member_room_msg_groups, message)
                self.get_member_room_msg_lite(task)
                logger.info('message: %s', message)
            logger.debug('成员{}消息队列: {}'.format(task.member.name, len(task.member_room_msg_ids)))
        except Exception as e:
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
        msgs = rsp_json['content']['data']
        # logger.debug('parse room comment reponse: %s', response)
        message = ''
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            platform = extInfo['platform']
            msg_id = msg['msgidClient']
            message_object = extInfo['messageObject']

            if msg_id in task.member_room_comment_ids:
                continue
            task.member_room_comment_ids.append(msg_id)
            if extInfo['contentType'] == 1:  # 普通评论
                logger.debug('房间评论')
                message = ('【房间评论】[%s]-%s: %s\n' % (
                    msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])) + message
            elif extInfo['contentType'] == 3:  # 房间礼物
                logger.debug('礼物')
            else:
                logger.debug('其他类型评论')

        logger.info('message: %s', message)
        logger.debug('length of comment groups: %d', len(task.member_room_comment_msg_groups))
        if message and len(task.member_room_comment_msg_groups) > 0:
            QQHandler.send_to_groups(task.member_room_comment_msg_groups, message)
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
        # url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/boardpage'
        params = {
            "roomId": task.member.room_id, "lastTime": 0, "limit": limit, "isFirst": "true"
        }
        # 收到响应
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
        except Exception as e:
            logger.error('获取房间评论失败！name: {}, room_id: {}'.format(task.member.name, task.member.room_id))
            logger.exception(e)
        return r.text

    def parse_member_live(self, response, task):
        """
        对直播列表进行处理，找到正在直播的指定成员
        :param response:
        :param task
        :return:
        """
        rsp_json = json.loads(response)
        logger.debug('rsp_json: %s' % rsp_json)
        logger.debug('keys of parse member live: %s', rsp_json['content'].keys())
        member_id = task.member.member_id
        # 当前没有人在直播
        if 'liveList' not in rsp_json['content'].keys():
            # print 'no live'
            logger.debug('当前没有人在直播')
            return
        live_list = rsp_json['content']["liveList"]
        logger.debug('当前正在直播的人数: %d', len(live_list))
        # print '当前正在直播的人数: %d' % len(live_list)
        msg = ''
        # logger.debug('直播ID列表: %s', ','.join(self.member_live_ids))
        for live in live_list:
            live_id = live['liveId']
            # logger.debug(live.keys())
            # print '直播人: %s' % live['memberId']
            # logger.debug('直播人(response): %s, 类型: %s', live['memberId'], type(live['memberId']))
            # logger.debug('member_id(参数): %s, 类型: %s', member_id, type(member_id))
            logger.debug('memberId %s is in live: %s, live_id: %s', live['memberId'], live['title'], live_id)
            logger.debug('stream path: %s', live['streamPath'])
            # logger.debug('member_live_ids list: %s', ','.join(self.member_live_ids))
            # logger.debug('live_id is in member_live_ids: %s', str(live_id in self.member_live_ids))
            if live['memberId'] == int(member_id) and live_id not in task.member_live_ids:
                logger.debug('[被监控成员正在直播]member_id: %s, live_id: %', member_id, live_id)
                start_time = util.convert_timestamp_to_timestr(live['startTime'])
                stream_path = live['streamPath']  # 流地址
                sub_title = live['subTitle']  # 直播名称
                live_type = live['liveType']
                url = 'https://h5.48.cn/2017appshare/memberLiveShare/index.html?id=%s' % live_id
                if live_type == 1:  # 露脸直播
                    msg += '你的小宝贝儿开露脸直播了: %s\n直播链接: %s\n开始时间: %s' % (sub_title, url, start_time)
                elif live_type == 2:  # 电台直播
                    msg += '你的小宝贝儿开电台直播了: %s\n直播链接: %s\n开始时间: %s' % (sub_title, url, start_time)
                task.member_live_ids.append(live_id)

        logger.debug(msg)
        if msg and len(task.member_live_groups) > 0:
            QQHandler.send_to_groups(task.member_live_groups, msg)

    def login_header_args(self):
        """
        构造登录请求头信息
        :return:
        """
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': global_config.IMEI,
            'token': '0',
            'version': global_config.POCKET48_VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            # 'Content-Length': '74',
            'Host': 'puser.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
        }
        return header

    def live_header_args(self):
        """
        构造直播请求头信息
        :return:
        """
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': global_config.IMEI,
            'token': self.token,
            'version': global_config.POCKET48_VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            'Host': 'plive.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
            # 'Cache-Control': 'no-cache'
        }
        return header

    def juju_header_args(self):
        """
        构造聚聚房间请求头信息
        :return:
        """
        logger.debug('token: %s', self.token)
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': global_config.IMEI,
            'token': self.token,
            'version': global_config.POCKET48_VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            'Host': 'pjuju.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
            # 'Cache-Control': 'no-cache'
        }
        return header

    def idol_flip_header_args(self):
        """
        构造收费翻牌请求头信息
        :return:
        """
        logger.debug('token: %s', self.token)
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': global_config.IMEI,
            'token': self.token,
            'version': global_config.POCKET48_VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            'Host': 'ppayqa.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip'
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
            diff = perform_time - time.time()
            if 0 < diff <= 15 * 60:
                live_link = '\n'.join(global_config.LIVE_LINK)
                live_msg = '直播传送门: %s' % live_link
                notify_str = '%s\n公演: %s\n时间: %s\n队伍: %s\n%s' % (
                    global_config.PERFORMANCE_NOTIFY, s['name'], s['time'], s['team'], live_msg)
                logger.info('notify str: %s', notify_str)
                QQHandler.send_to_groups(self.test_groups, notify_str)


pocket48_handler = Pocket48Handler()

if __name__ == '__main__':
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
