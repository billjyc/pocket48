# -*- coding:utf-8 -*-

import requests
import json

from config_reader import ConfigReader
import time
from qqhandler import QQHandler
from qqbot.utf8logger import INFO,ERROR,DEBUG
from download import Download

import Queue

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class Pocket48Handler:
    def __init__(self, auto_reply_groups, member_room_msg_groups, member_room_comment_msg_groups,
                 member_live_groups):
        self.session = requests.session()
        self.token = '0'
        self.is_login = False

        self.last_monitor_time = -1
        self.auto_reply_groups = auto_reply_groups
        self.member_room_msg_groups = member_room_msg_groups
        self.member_room_comment_msg_groups = member_room_comment_msg_groups
        self.member_live_groups = member_live_groups

        self.member_room_msg_ids = []
        self.member_room_comment_ids = []
        self.member_live_ids = []
        self.live_urls = Queue.Queue(20)
        self.download = Download(self.live_urls)
        self.download.setDaemon(True)
        self.download.start()

    def login(self, username, password):
        """
        登录
        :param username:
        :param password:
        :return:
        """
        if username is None or password is None:
            ERROR('用户名或密码为空')
            return
        login_url = 'https://puser.48.cn/usersystem/api/user/v1/login/phone'
        params = {
            'latitude': '0',
            'longitude': '0',
            'password': str(self.password),
            'account': str(self.phonenum),
        }
        res = self.session.post(login_url, json=params).json()
        # 登录成功
        if res['status'] == 200:
            self.token = res['content']['token']
            self.is_login = True
            return True
        else:
            ERROR('登录失败')
        return False

    def logout(self):
        """
        登出
        :return:
        """

    def get_member_live_msg(self):
        """
        获取所有直播间信息
        :return:
        """
        # if not self.is_login:
        #     ERROR('尚未登录')
        url = 'https://plive.48.cn/livesystem/api/live/v1/memberLivePage'
        params = {
            "giftUpdTime": 1503766100000,
            "groupId": 0,  # SNH48 Group所有人
            "lastTime": 0,
            "limit": 50,
            "memberId": 0,
            "type": 0
        }
        try:
            r = requests.post(url, data=json.dumps(params), headers=self.live_header_args(), verify=False)
        except Exception as e:
            ERROR('获取成员直播失败')
            ERROR(e)
        return r.text

    def get_member_room_msg(self, room_id):
        """
        获取成员房间消息
        :param room_id: 房间id
        :return:
        """
        # if not self.is_login:
        #     ERROR('尚未登录')
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 10
        }
        try:
            r = requests.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
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
        except Exception as e:
            ERROR('初始化消息队列失败')
            ERROR(e)

    def parse_room_msg(self, response):
        """
        对成员消息进行处理
        :param response:
        :return:
        """
        # DEBUG(response)
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']

        message = ''
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id

            if msg_id in self.member_room_msg_ids:
                continue

            DEBUG('成员消息')
            self.member_room_msg_ids.append(msg_id)

            DEBUG('extInfo.keys():' + ','.join(extInfo.keys()))
            if msg['msgType'] == 0:  # 文字消息
                if 'text' in extInfo.keys():  # 普通消息
                    DEBUG('普通消息')
                    message = ('【成员消息】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])) + message
                elif 'messageText' in extInfo.keys():  # 翻牌消息
                    DEBUG('翻牌')
                    member_msg = extInfo['messageText']
                    fanpai_msg = extInfo['faipaiContent']
                    fanpai_id = extInfo['faipaiName']
                    message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s:%s\n' % (msg['msgTimeStr'], extInfo['senderName'], member_msg, fanpai_id, fanpai_msg)) + message
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

        if message and len(self.member_room_msg_groups) > 0:
            QQHandler.send_to_groups(self.member_room_msg_groups, message)
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
        DEBUG(response)
        message = ''
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            platform = extInfo['platform']
            msg_id = msg['msgidClient']

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

    def get_member_room_comment(self, room_id):
        """
        获取成员房间的粉丝评论
        :param room_id: 房间id
        :return:
        """
        # if not self.is_login:
        #     ERROR('尚未登录')
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 20
        }
        # 收到响应
        try:
            r = requests.post(url, data=json.dumps(params), headers=self.juju_header_args(), verify=False)
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
        DEBUG(rsp_json['content'].keys())
        # 当前没有人在直播
        if 'liveList' not in rsp_json['content'].keys():
            # print 'no live'
            DEBUG('当前没有人在直播')
            return
        live_list = rsp_json['content']["liveList"]
        DEBUG('当前正在直播的人数: %d', len(live_list))
        # print '当前正在直播的人数: %d' % len(live_list)
        msg = ''
        DEBUG('直播ID列表: %s', ','.join(self.member_live_ids))
        for live in live_list:
            live_id = live['liveId']
            DEBUG(live.keys())
            # print '直播人: %s' % live['memberId']
            # DEBUG('直播人(response): %s, 类型: %s', live['memberId'], type(live['memberId']))
            # DEBUG('member_id(参数): %s, 类型: %s', member_id, type(member_id))
            DEBUG('memberId %s is in live: %s', live['memberId'], live['title'])
            DEBUG('stream path: %s', live['streamPath'])
            # DEBUG('member_live_ids list: %s', ','.join(self.member_live_ids))
            # DEBUG('live_id is in member_live_ids: %s', str(live_id in self.member_live_ids))
            if live['memberId'] == int(member_id) and live_id not in self.member_live_ids:
                DEBUG('[被监控成员正在直播]member_id: %s, live_id: %', member_id, live_id)
                start_time = self.convert_timestamp_to_timestr(live['startTime'])
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
                self.download.setName(member_id + start_time)
                self.live_urls.put(stream_path)

        DEBUG(msg)
        if msg and len(self.member_live_groups) > 0:
            QQHandler.send_to_groups(self.member_live_groups, msg)

    def convert_timestamp_to_timestr(self, timestamp):
        """
        将13位时间戳转换为字符串
        :param timestamp:
        :return:
        """
        timeArray = time.localtime(timestamp / 1000)
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return time_str

    def live_header_args(self):
        """
        构造直播请求头信息
        :return:
        """
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': '863526430773465',
            # TODO: 替换为登录后获取的token
            'token': '1HMD6/i9yO4b2myk2c7K9seuVtXP+QCpqxRpB8ja8dQDLWR0RXXobiz87FeoVYYYOY4eAF9ifbM=',
            'version': '4.1.2',
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
            # TODO: 替换为登录后获取的token
            'token': '1HMD6/i9yO4b2myk2c7K9seuVtXP+QCpqxRpB8ja8dQDLWR0RXXobiz87FeoVYYYOY4eAF9ifbM=',
            'version': '4.1.2',
            'Content-Type': 'application/json;charset=utf-8',
            'Content-Length': '42',
            'Host': 'pjuju.48.cn',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'Cache-Control': 'no-cache'
        }
        return header


if __name__ == '__main__':
    handler = Pocket48Handler([], [], [], [])
    # response = handler.get_member_live_msg()
    # handler.parse_member_live(response, 6432)

    url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/hot'
    data = {
        "groupId": 10,
        "needRootRoom": True,
        "page": 1,
        "topMemberIds": []
    }
    header = {
        'Host': 'pjuju.48.cn',
        'app-type': 'fans',
        'Accept': '*/*',
        'version': '4.1.6',
        'os': 'ios',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-Hans-CN;q=1',
        'imei': '863526430773465',
        'token': '',
        'User-Agent': 'Mobile_Pocket',
        'Content-Length': '60',
        'Connection': 'keep-alive',
        'Content-Type': 'application/json;charset=utf-8',
    }
    r = requests.post(url, data=json.dumps(data), headers=header, verify=False)
    print r.text

    r = handler.get_member_room_msg(5758972)
    print r
    # print handler.convert_timestamp_to_timestr(1504970619679)
