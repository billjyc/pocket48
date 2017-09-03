# -*- coding:utf-8 -*-

import requests
import json
from config_reader import ConfigReader
import time
from qqhandler import QQHandler
from qqbot.utf8logger import INFO,ERROR,DEBUG

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class Pocket48Handler:
    def __init__(self, group, test_group):
        self.last_monitor_time = int(time.time())
        self.group = group
        self.test_group = test_group

    def get_member_room_msg(self, room_id):
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 10
        }
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        DEBUG(response.text)
        return response.text

    def parse_room_msg(self, response):
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']
        for msg in msgs:
            if msg['msgTime'] < self.convert_timestamp(self.last_monitor_time):
                break
            extInfo = json.loads(msg['extInfo'])
            message = '[%s]-%s: %s' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])
            INFO(message)

            # 判断是否为成员
            if self.is_member(extInfo['senderRole']):
                message = '【成员消息】' + message
                QQHandler.send(self.group, message)
            else:
                message = '【房间评论】' + message

            QQHandler.send(self.test_group, message)

            # print '[%s]-%s: %s' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])

    def get_member_room_comment(self, room_id):
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 10
        }
        # 收到响应  
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        DEBUG(response.text)
        return response.text

    def is_member(self, role):
        return role == 1

    '''
    将10位时间戳转化为13位
    '''
    def convert_timestamp(self, timestamp):
        return timestamp * 1000

    '''
    请求头信息
    '''
    def header_args(self):
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
    roomId = ConfigReader.get_member_room_number('fengxiaofei')
    qq_number = ConfigReader.get_qq_number()
    group_number = ConfigReader.get_group_number()
    test_group_number = ConfigReader.get_test_group_number()

    qq_handler = QQHandler()
    qq_handler.login('fxftest')
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

        INFO('Group: ' + group)
        INFO('Test Group: ' + test_group)
        handler = Pocket48Handler(group, test_group)

        while True:
            r1 = handler.get_member_room_msg(roomId)
            handler.parse_room_msg(r1)
            r2 = handler.get_member_room_comment(roomId)
            handler.parse_room_msg(r2)
            handler.last_monitor_time = int(time.time())
            time.sleep(60)
    else:
        ERROR('群号输入不正确！')