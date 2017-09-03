# -*- coding:utf-8 -*-

import requests
import json
from config_reader import ConfigReader
import time
from qqhandler import QQHandler


class Pocket48Handler:
    def __init__(self, group):
        self.last_monitor_time = int(time.time())
        self.group = group

    def get_member_room_msg(self, room_id):
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 2
        }
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        print response.text
        return response.text

    def parse_room_msg(self, response):
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']
        for msg in msgs:
            if msg['msgTime'] < self.convert_timestamp(self.last_monitor_time):
                break
            extInfo = json.loads(msg['extInfo'])
            message = '[%s]-%s: %s' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])
            QQHandler.send(self.group, message)
            print '[%s]-%s: %s' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])

    def get_member_room_comment(self, room_id):
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        params = {
            "roomId": room_id, "lastTime": 0, "limit": 2
        }
        # 收到响应  
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        print response.text
        return response.text

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

    qq_handler = QQHandler()
    qq_handler.login(qq_number)
    groups = qq_handler.list_group('483548995')
    if groups:
        group = groups[0]
        handler = Pocket48Handler(group)

        while True:
            r1 = handler.get_member_room_msg(roomId)
            handler.parse_room_msg(r1)
            r2 = handler.get_member_room_comment(roomId)
            handler.parse_room_msg(r2)
            handler.last_monitor_time = int(time.time())
            time.sleep(60)
    else:
        print '群号输入不正确！'