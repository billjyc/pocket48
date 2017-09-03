# -*- coding:utf-8 -*-

import requests
import json


class Pocket48Handler:
    def __init__(self):
        pass

    def get_member_room_msg(self, roomId):
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/chat'
        params = {
            "roomId": roomId, "lastTime": 0, "limit": 10
        }
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        print response.text

    def get_memger_room_comment(self, roomId):
        url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/comment'
        params = {
            "roomId": roomId, "lastTime": 0, "limit": 10
        }
        # 收到响应  
        response = requests.post(url, data=json.dumps(params), headers=self.header_args(), verify=False)
        print response.text

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
    handler = Pocket48Handler()
    handler.get_member_room_msg(5780791)