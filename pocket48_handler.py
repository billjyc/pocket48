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
        DEBUG(response)
        rsp_json = json.loads(response)
        msgs = rsp_json['content']['data']

        message = ''
        is_member_msg = True
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            platform = extInfo['platform']
            # bodys = json.loads(msg['bodys'])
            if msg['msgTime'] < self.convert_timestamp(self.last_monitor_time):
                break
            # 判断是否为成员
            if self.is_member(extInfo['senderRole']):
                is_member_msg = True
                DEBUG('成员消息')
                DEBUG('extInfo.keys():' + ','.join(extInfo.keys()))
                if 'text' in extInfo.keys():  # 普通消息
                    DEBUG('普通消息')
                    message += '【成员消息】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], extInfo['text'])
                elif 'messageText' in extInfo.keys():  # 翻牌消息
                    DEBUG('翻牌')
                    member_msg = extInfo['messageText']
                    fanpai_msg = extInfo['faipaiContent']
                    fanpai_id = extInfo['faipaiName']
                    message += '【翻牌】[%s]-%s\n【被翻牌】冯晓菲的%s:%s\n' % (msg['msgTimeStr'], member_msg, fanpai_id, fanpai_msg)
                elif self.check_json_format(msg['bodys']):  # 图片
                    DEBUG('图片消息')
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
                pass
                # QQHandler.send(self.group, message)

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
            except ValueError, e:
                ERROR(e)
                return False
            DEBUG('is json')
            return True
        else:
            DEBUG('is not string')
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
    pocket48_handler = Pocket48Handler('0','0')
    response = """
    {
    "status": 200,
    "message": "success",
    "content": {
        "data": [
            {
                "msgidClient": "69a4d58e-68c5-436d-9bf8-515ebbf4c9f2",
                "msgTime": 1504593232216,
                "msgTimeStr": "2017-09-05 14:33:52",
                "userId": 0,
                "msgType": 1,
                "bodys": "{\"size\":543698,\"ext\":\"jpg\",\"w\":2668,\"url\":\"https://nos.netease.com/nim/NDA5MzEwOA==/bmltYV8xNzc5NzQyNDlfMTUwMjcwOTY0MDQ0OV84MTI2ZTI2ZC0wMDJlLTQzODctOTNlZC1kODdjOTYzYWQ5N2Q=\",\"md5\":\"2a7ba548dda48a02b82e9b6e1264400b\",\"h\":2668}",
                "extInfo": "{\"source\":\"juju\",\"fromApp\":2,\"messageObject\":\"image\",\"senderAvatar\":\"/mediasource/avatar/149914554773652wp2jnnu6.jpg\",\"senderHonor\":\"\",\"referenceNumber\":0,\"dianzanNumber\":0,\"senderId\":6432,\"version\":\"2.1.3\",\"senderName\":\"冯晓菲\",\"senderRole\":1,\"chatBackgroundBubbles2\":7,\"platform\":\"ios\",\"roomType\":1,\"sourceId\":\"5780791\",\"chatBackgroundBubbles\":0,\"contentType\":1,\"build\":18300,\"role\":2,\"senderLevel\":\"X\",\"content\":\"\"}"
            },
            {
                "msgidClient": "a25eb045-1805-4a51-9d7e-2bbc830df4d9",
                "msgTime": 1504587916063,
                "msgTimeStr": "2017-09-05 13:05:16",
                "userId": 0,
                "msgType": 0,
                "bodys": "🤦🏻‍♀️",
                "extInfo": "{\"source\":\"juju\",\"fromApp\":2,\"messageObject\":\"text\",\"senderAvatar\":\"/mediasource/avatar/149914554773652wp2jnnu6.jpg\",\"senderHonor\":\"\",\"referenceNumber\":0,\"dianzanNumber\":0,\"senderId\":6432,\"version\":\"2.1.3\",\"senderName\":\"冯晓菲\",\"senderRole\":1,\"chatBackgroundBubbles2\":7,\"platform\":\"ios\",\"roomType\":1,\"sourceId\":\"5780791\",\"chatBackgroundBubbles\":0,\"contentType\":1,\"build\":18300,\"role\":2,\"senderLevel\":\"X\",\"text\":\"🤦🏻‍♀️\",\"content\":\"\"}"
            },
            {
                "msgidClient": "dfd4479a-4658-43a2-a6cc-f9ac18f07e4c",
                "msgTime": 1504587908224,
                "msgTimeStr": "2017-09-05 13:05:08",
                "userId": 0,
                "msgType": 0,
                "bodys": "午饭还是米线",
                "extInfo": "{\"source\":\"juju\",\"fromApp\":2,\"messageObject\":\"text\",\"senderAvatar\":\"/mediasource/avatar/149914554773652wp2jnnu6.jpg\",\"senderHonor\":\"\",\"referenceNumber\":0,\"dianzanNumber\":0,\"senderId\":6432,\"version\":\"2.1.3\",\"senderName\":\"冯晓菲\",\"senderRole\":1,\"chatBackgroundBubbles2\":7,\"platform\":\"ios\",\"roomType\":1,\"sourceId\":\"5780791\",\"chatBackgroundBubbles\":0,\"contentType\":1,\"build\":18300,\"role\":2,\"senderLevel\":\"X\",\"text\":\"午饭还是米线\",\"content\":\"\"}"
            },
            {
                "msgidClient": "5e84ad4c-8270-4175-bbe6-0a738ca55e46",
                "msgTime": 1504585888427,
                "msgTimeStr": "2017-09-05 12:31:28",
                "userId": 0,
                "msgType": 0,
                "bodys": "",
                "extInfo": "{\"faipaiName\":\"酸甜苦辣小熊猫歪\",\"source\":\"juju\",\"fromApp\":2,\"messageObject\":\"faipaiText\",\"senderAvatar\":\"/mediasource/avatar/149914554773652wp2jnnu6.jpg\",\"faipaiContent\":\"灰灰醒啦\",\"faipaiPortrait\":\"/mediasource/avatar/1502129005082wq5YVONR68.png\",\"senderHonor\":\"\",\"referenceNumber\":0,\"messageText\":\"早就醒了 已经化好妆了\",\"dianzanNumber\":0,\"senderId\":6432,\"version\":\"2.1.3\",\"senderName\":\"冯晓菲\",\"senderRole\":1,\"chatBackgroundBubbles2\":7,\"platform\":\"ios\",\"roomType\":1,\"sourceId\":\"5780791\",\"chatBackgroundBubbles\":0,\"contentType\":1,\"build\":18300,\"faipaiUserId\":386361,\"role\":2,\"senderLevel\":\"X\",\"content\":\"\"}"
            },
            {
                "msgidClient": "ea6e1664-1949-492e-a0a9-0cc2ac0bdd18",
                "msgTime": 1504585785454,
                "msgTimeStr": "2017-09-05 12:29:45",
                "userId": 0,
                "msgType": 0,
                "bodys": "睡了十个小时",
                "extInfo": "{\"source\":\"juju\",\"fromApp\":2,\"messageObject\":\"text\",\"senderAvatar\":\"/mediasource/avatar/149914554773652wp2jnnu6.jpg\",\"senderHonor\":\"\",\"referenceNumber\":0,\"dianzanNumber\":0,\"senderId\":6432,\"version\":\"2.1.3\",\"senderName\":\"冯晓菲\",\"senderRole\":1,\"chatBackgroundBubbles2\":7,\"platform\":\"ios\",\"roomType\":1,\"sourceId\":\"5780791\",\"chatBackgroundBubbles\":0,\"contentType\":1,\"build\":18300,\"role\":2,\"senderLevel\":\"X\",\"text\":\"睡了十个小时\",\"content\":\"\"}"
            }
        ],
        "lastTime": 1504585785454
    }
}
    """
    json_str = json.loads(response)
    # print response
    # pocket48_handler.parse_room_msg(response)
