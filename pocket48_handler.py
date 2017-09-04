# -*- coding:utf-8 -*-

import requests
import json
from config_reader import ConfigReader
import time
from qqhandler import QQHandler
from qqbot.utf8logger import INFO,ERROR,DEBUG
import urllib2

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class Pocket48Handler:
    def __init__(self, group, test_group):
        self.last_monitor_time = int(time.time())
        self.group = group
        self.test_group = test_group

    def get_member_room_msg(self, room_id):
        """
        获取成员房间消息
        :param room_id: 房间id
        :return:
        """
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 5
        }
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        return response.text

    def parse_room_msg(self, response):
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']
        message = ''
        is_member_msg = True
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            # bodys = json.loads(msg['bodys'])
            DEBUG(msg['extInfo'])
            if msg['msgTime'] < self.convert_timestamp(self.last_monitor_time):
                break
            # 判断是否为成员
            if self.is_member(extInfo['senderRole']):
                is_member_msg = True
                DEBUG('成员消息')
                DEBUG('extInfo.keys():' + ','.join(extInfo.keys()))
                if 'text' in extInfo.keys():  # 普通消息
                    DEBUG('图片消息')
                    message += '【成员消息】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])
                elif 'messageText' in extInfo.keys():  # 翻牌消息
                    DEBUG('翻牌')
                    member_msg = extInfo['messageText']
                    fanpai_msg = extInfo['faipaiContent']
                    fanpai_id = extInfo['faipaiName']
                    message += '【翻牌】[%s]-%s\n【被翻牌】冯晓菲的%s:%s\n' % (msg['msgTimeStr'], member_msg, fanpai_id, fanpai_msg)
                elif self.check_json_format(msg['bodys']):  # 图片
                    DEBUG('图片')
                    bodys = json.loads(msg['bodys'])
                    if 'url' in bodys.keys():
                        url = bodys['url']
                        message += '【图片】[%s]-%s\n' % (msg['msgTimeStr'], url)
            else:
                DEBUG('房间评论')
                is_member_msg = False
                message += '【房间评论】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])
        INFO('message: %s', message)
        if message:
            QQHandler.send(self.test_group, message)
            if is_member_msg:  # 海底捞只接收成员消息
                QQHandler.send(self.group, message)

        # print '[%s]-%s: %s' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])

    def get_member_room_comment(self, room_id):
        """
        获取成员房间的粉丝评论
        :param room_id: 房间id
        :return:
        """
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 10
        }
        # 收到响应  
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        return response.text

    def is_member(self, role):
        """
        判断是否为成员
        :param role: 成员为1
        :return:
        """
        return role == 1

    def convert_timestamp(self, timestamp):
        """
        将10位时间戳转化为13位
        :param timestamp:
        :return:
        """
        return timestamp * 1000

    def check_json_format(self, raw_msg):
        """
        判断给定字符串是不是符合json格式
        :param raw_msg:
        :return:
        """
        if isinstance(raw_msg, str):  # 首先判断变量是否为字符串
            try:
                json.loads(raw_msg, encoding='utf-8')
            except ValueError:
                return False
            return True
        else:
            return False

    def header_args(self):
        """
        构造请求头信息
        :return:
        """
        header = {
            'os': 'android',
            'User-Agent': 'Mobile_Pocket',
            'IMEI': '863526430773465',
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
    # proxy = 'proxy.tencent.com:8080'
    # opener = urllib2.build_opener(urllib2.ProxyHandler({'http': proxy}))
    # urllib2.install_opener(opener)
    roomId = ConfigReader.get_member_room_number('fengxiaofei')
    qq_number = ConfigReader.get_qq_number('qq')
    group_number = ConfigReader.get_group_number()
    test_group_number = ConfigReader.get_test_group_number()

    qq_handler = QQHandler()
    qq_handler.login('fxftest')
    # qq_handler.login(qq_number)
    qq_handler.update()
    groups = qq_handler.list_group(group_number)
    test_groups = qq_handler.list_group(test_group_number)
    DEBUG('Group: ' + str(groups is None))
    DEBUG('Test Group: ' + str(test_groups is None))

    if groups or test_groups:
        if test_groups:
            test_group = test_groups[0]
        if groups:
            group = groups[0]
        else:
            group = test_groups[0]

        # INFO('Group: ' + group)
        # INFO('Test Group: ' + test_group)
        handler = Pocket48Handler(group, test_group)

        while True:
            r1 = handler.get_member_room_msg(roomId)
            handler.parse_room_msg(r1)
            # r2 = handler.get_member_room_comment(roomId)
            # handler.parse_room_msg(r2)
            # handler.last_monitor_time = int(time.time())
            time.sleep(60)
    else:
        ERROR('群号输入不正确！')