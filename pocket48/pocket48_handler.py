# -*- coding:utf-8 -*-

import requests
import json

import time
from qq.qqhandler import QQHandler
from qqbot.utf8logger import INFO, ERROR, DEBUG
from utils.download import Download

from utils import global_config, util

import Queue

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class Member:
    def __init__(self, name, member_id, room_id):
        self.name = name
        self.member_id = member_id
        self.room_id = room_id


class Pocket48Handler:
    VERSION = '5.1.0'

    def __init__(self, auto_reply_groups, member_room_msg_groups, member_room_comment_msg_groups,
                 member_live_groups, member_room_msg_lite_groups):
        self.session = requests.session()
        self.token = '0'
        self.is_login = False

        self.last_msg_time = -1
        self.auto_reply_groups = auto_reply_groups
        self.member_room_msg_groups = member_room_msg_groups
        self.member_room_comment_msg_groups = member_room_comment_msg_groups
        self.member_live_groups = member_live_groups
        self.member_room_msg_lite_groups = member_room_msg_lite_groups

        self.member_room_msg_ids = []
        self.member_room_comment_ids = []
        self.member_live_ids = []

        # 成员房间未读消息数量
        self.unread_msg_amount = 0
        # 成员房间其他成员的未读消息数量
        self.unread_other_member_msg_amount = 0

        self.other_members_names = []
        self.last_other_member_msg_time = -1

        # self.live_urls = Queue.Queue(20)
        # self.download = Download(self.live_urls)
        # self.download.setDaemon(True)
        # self.download.start()

    def login(self, username, password):
        """
        登录
        :param username:
        :param password:
        :return:
        """
        if self.is_login is True:
            ERROR('已经登录！')
            return
        if username is None or password is None:
            ERROR('用户名或密码为空')
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
            INFO('登录成功, 用户名: %s', username)
            INFO('TOKEN: %s', self.token)
            return True
        else:
            ERROR('登录失败')
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
            ERROR('尚未登录')
        url = 'https://plive.48.cn/livesystem/api/live/v1/memberLivePage'
        params = {
            "giftUpdTime": 1503766100000,
            "groupId": 0,  # SNH48 Group所有人
            "lastTime": 0,
            "limit": limit,
            "memberId": 0,
            "type": 0
        }
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.live_header_args(), verify=False)
        except Exception as e:
            ERROR('获取成员直播失败')
            ERROR(e)
        return r.text

    def get_member_room_msg(self, room_id, limit=20):
        """
        获取成员房间消息
        :param limit:
        :param room_id: 房间id
        :return:
        """
        if not self.is_login:
            ERROR('尚未登录')
        # url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/mainpage'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": limit, "chatType": 0
        }
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
        except Exception as e:
            ERROR('获取成员消息失败')
            ERROR(e)
        return r.text

    def init_msg_queues(self, room_id):
        """
        初始化房间消息队列
        :param room_id:
        :return:
        """
        try:
            self.member_room_msg_ids = []
            self.member_room_comment_ids = []
            self.member_live_ids = []

            self.unread_msg_amount = 0

            r1 = self.get_member_room_msg(room_id)
            r2 = self.get_member_room_comment(room_id)

            r1_json = json.loads(r1)
            r2_json = json.loads(r2)
            for r in r1_json['content']['data']:
                msg_id = r['msgidClient']
                self.member_room_msg_ids.append(msg_id)

            for r in r2_json['content']['data']:
                msg_id = r['msgidClient']
                self.member_room_comment_ids.append(msg_id)

            DEBUG('成员消息队列: %s', len(self.member_room_msg_ids))
            DEBUG('房间评论队列: %s', len(self.member_room_comment_ids))
            DEBUG('房间未读消息数量: %d', self.unread_msg_amount)
        except Exception as e:
            ERROR('初始化消息队列失败')
            ERROR(e)

    def get_member_room_msg_lite(self):
        """
        发送成员房间消息（简易版，只提醒在房间里出现）
        :return:
        """
        time_now = time.time()
        msg = ''

        if self.unread_other_member_msg_amount > 0 and len(self.member_room_msg_lite_groups) > 0:
            if self.last_other_member_msg_time < 0 or time_now - self.last_msg_time >= 10 * 60:
                DEBUG('其他成员出现在房间中')
                member_name = ', '.join(self.other_members_names)
                QQHandler.send_to_groups(self.member_room_msg_lite_groups, '%s来你们灰的房间里串门啦~' % member_name)
                self.unread_other_member_msg_amount = 0
                self.last_other_member_msg_time = time_now
        if self.unread_msg_amount > 0 and len(self.member_room_msg_lite_groups) > 0:
            # 距离上一次提醒时间超过10分钟且有未读消息
            if self.last_msg_time < 0 or time_now - self.last_msg_time >= 10 * 60:
                DEBUG('向大群发送简易版提醒')
                msg = util.random_str(global_config.ROOM_MSG_LITE_NOTIFY)
                QQHandler.send_to_groups(self.member_room_msg_lite_groups, msg)
                INFO(msg)
                self.unread_msg_amount = 0
            else:
                DEBUG('不向大群发送简易版提醒')
            self.last_msg_time = time_now
        else:
            INFO('最近10分钟内没有未读消息')

    def parse_room_msg(self, response):
        """
        对成员消息进行处理
        :param response:
        :return:
        """
        DEBUG('parse room msg response: %s', response)
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']

        message = ''
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id

            if msg_id in self.member_room_msg_ids:
                continue

            if extInfo['role'] != 2:  # 其他成员的消息
                self.unread_other_member_msg_amount += 1
                member_name = extInfo['senderName']
                if member_name == '你们的小可爱':
                    member_name = 'YBY'
                if member_name not in self.other_members_names:
                    self.other_members_names.append(member_name)
            else:
                self.unread_msg_amount += 1

            DEBUG('成员消息')
            self.member_room_msg_ids.append(msg_id)

            message_object = extInfo['messageObject']

            DEBUG('extInfo.keys():' + ','.join(extInfo.keys()))
            if msg['msgType'] == 0:  # 文字消息
                if message_object == 'text':  # 普通消息
                    DEBUG('普通消息')
                    message = ('【成员消息】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])) + message
                elif message_object == 'faipaiText':  # 翻牌消息
                    DEBUG('翻牌')
                    member_msg = extInfo['messageText']
                    fanpai_msg = extInfo['faipaiContent']
                    # fanpai_id = extInfo['faipaiName']
                    # message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s:%s\n' % (msg['msgTimeStr'], extInfo['senderName'], member_msg, fanpai_id, fanpai_msg)) + message
                    message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                    msg['msgTimeStr'], extInfo['senderName'], member_msg, fanpai_msg)) + message
                # TODO: 直播可以直接在房间里监控
                elif message_object == 'diantai':  # 电台直播
                    DEBUG('电台直播')
                    reference_content = extInfo['referenceContent']
                    live_id = extInfo['referenceObjectId']
                elif message_object == 'live':  # 露脸直播
                    DEBUG('露脸直播')
                    reference_content = extInfo['referenceContent']
                    live_id = extInfo['referenceObjectId']
            elif msg['msgType'] == 1:  # 图片消息
                bodys = json.loads(msg['bodys'])
                DEBUG('图片')
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【图片】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url)) + message
            elif msg['msgType'] == 2:  # 语音消息
                DEBUG('语音消息')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【语音】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url)) + message
            elif msg['msgType'] == 3:  # 小视频
                DEBUG('房间小视频')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【小视频】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url)) + message

        if message and len(self.member_room_msg_groups) > 0:
            QQHandler.send_to_groups(self.member_room_msg_groups, message)
            self.get_member_room_msg_lite()
            INFO('message: %s', message)
        DEBUG('成员消息队列: %s', len(self.member_room_msg_ids))

    def parse_room_comment(self, response):
        """
        对房间评论进行处理
        :param response:
        :return:
        """
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']
        # DEBUG('parse room comment reponse: %s', response)
        message = ''
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            platform = extInfo['platform']
            msg_id = msg['msgidClient']
            message_object = extInfo['messageObject']

            if msg_id in self.member_room_comment_ids:
                continue
            self.member_room_comment_ids.append(msg_id)
            if extInfo['contentType'] == 1:  # 普通评论
                DEBUG('房间评论')
                message = ('【房间评论】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])) + message
            elif extInfo['contentType'] == 3:  # 房间礼物
                DEBUG('礼物')
            else:
                DEBUG('其他类型评论')

        INFO('message: %s', message)
        DEBUG('length of comment groups: %d', len(self.member_room_comment_msg_groups))
        if message and len(self.member_room_comment_msg_groups) > 0:
            QQHandler.send_to_groups(self.member_room_comment_msg_groups, message)
        DEBUG('房间评论队列: %s', len(self.member_room_comment_ids))

    def get_member_room_comment(self, room_id, limit=20):
        """
        获取成员房间的粉丝评论
        :param limit:
        :param room_id: 房间id
        :return:
        """
        if not self.is_login:
            ERROR('尚未登录')
        # url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/boardpage'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": limit, "isFirst": "true"
        }
        # 收到响应
        try:
            r = self.session.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
        except Exception as e:
            ERROR('获取房间评论失败')
            ERROR(e)
        return r.text

    def parse_member_live(self, response, member_id):
        """
        对直播列表进行处理，找到正在直播的指定成员
        :param member_id:
        :param response:
        :return:
        """
        rsp_json = json.loads(response)
        # DEBUG('keys of parse member live: %s', rsp_json['content'].keys())
        # 当前没有人在直播
        if 'liveList' not in rsp_json['content'].keys():
            # print 'no live'
            DEBUG('当前没有人在直播')
            return
        live_list = rsp_json['content']["liveList"]
        DEBUG('当前正在直播的人数: %d', len(live_list))
        # print '当前正在直播的人数: %d' % len(live_list)
        msg = ''
        # DEBUG('直播ID列表: %s', ','.join(self.member_live_ids))
        for live in live_list:
            live_id = live['liveId']
            # DEBUG(live.keys())
            # print '直播人: %s' % live['memberId']
            # DEBUG('直播人(response): %s, 类型: %s', live['memberId'], type(live['memberId']))
            # DEBUG('member_id(参数): %s, 类型: %s', member_id, type(member_id))
            DEBUG('memberId %s is in live: %s, live_id: %s', live['memberId'], live['title'], live_id)
            DEBUG('stream path: %s', live['streamPath'])
            # DEBUG('member_live_ids list: %s', ','.join(self.member_live_ids))
            # DEBUG('live_id is in member_live_ids: %s', str(live_id in self.member_live_ids))
            if live['memberId'] == int(member_id) and live_id not in self.member_live_ids:
                DEBUG('[被监控成员正在直播]member_id: %s, live_id: %', member_id, live_id)
                start_time = util.convert_timestamp_to_timestr(live['startTime'])
                stream_path = live['streamPath']  # 流地址
                sub_title = live['subTitle']  # 直播名称
                live_type = live['liveType']
                url = 'https://h5.48.cn/2017appshare/memberLiveShare/index.html?id=%s' % live_id
                if live_type == 1:  # 露脸直播
                    msg += '你的小宝贝儿开露脸直播了: %s\n直播链接: %s\n开始时间: %s' % (sub_title, url, start_time)
                elif live_type == 2:  # 电台直播
                    msg += '你的小宝贝儿开电台直播了: %s\n直播链接: %s\n开始时间: %s' % (sub_title, url, start_time)
                self.member_live_ids.append(live_id)

                # 录制直播
                # name = '%s_%s' % (member_id, live['startTime'])
                # # self.download.setName(name)
                # self.live_urls.put(name)
                # self.live_urls.put(stream_path)

        DEBUG(msg)
        if msg and len(self.member_live_groups) > 0:
            QQHandler.send_to_groups(self.member_live_groups, msg)

    def login_header_args(self):
        """
        构造登录请求头信息
        :return:
        """
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': '863526430773465',
            'token': '0',
            'version': self.VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            'Content-Length': '74',
            'Host': 'puser.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'Cache-Control': 'no-cache'
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
            'IMEI': '863526430773465',
            'token': self.token,
            'version': self.VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            'Content-Length': '89',
            'Host': 'plive.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'Cache-Control': 'no-cache'
        }
        return header

    def juju_header_args(self):
        """
        构造聚聚房间请求头信息
        :return:
        """
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': '863526430773465',
            'token': self.token,
            'version': self.VERSION,
            'Content-Type': 'application/json;charset=utf-8',
            'Content-Length': '57',
            'Host': 'pjuju.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'Cache-Control': 'no-cache'
        }
        return header

    def notify_performance(self):
        f = open('data/schedule.json')

        schedules = json.load(f)
        for s in schedules['schedules']:
            perform_time = util.convert_timestr_to_timestamp(s['time'])
            diff = perform_time - time.time()
            if 0 < diff <= 15 * 60:
                live_link = '\n'.join(global_config.LIVE_LINK)
                live_msg = '直播传送门: %s' % live_link
                notify_str = '%s\n公演: %s\n时间: %s\n队伍: %s\n%s' % (
                global_config.PERFORMANCE_NOTIFY, s['name'], s['time'], s['team'], live_msg)
                INFO('notify str: %s', notify_str)
                QQHandler.send_to_groups(self.member_room_msg_lite_groups, notify_str)


if __name__ == '__main__':
    handler = Pocket48Handler([], [], [], [], [])

    # handler.notify_performance()

    handler.login('*', '*')

    # response = handler.get_member_live_msg()
    # handler.parse_member_live(response, 528331)

    r = handler.get_member_room_msg(5780791)
    print r
    handler.parse_room_msg(r)
    r2 = handler.get_member_room_comment(5780791)
    print r2
    handler.parse_room_comment(r2)
    # print handler.convert_timestamp_to_timestr(1504970619679)
