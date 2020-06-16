# -*- coding:utf-8 -*-
import requests
import json
import sqlite3
import os
import time
from utils import util
from log.my_logger import pocket48_logger as logger
import xlwt

rst = {}
workbook = xlwt.Workbook(encoding='utf-8')
worksheet = workbook.add_sheet('My Worksheet')
worksheet2 = workbook.add_sheet('total')


class Fan:
    def __init__(self, user_id, nick_name, level, gender=0, is_vip=False, verification=False):
        self.user_id = user_id
        self.nick_name = nick_name
        self.level = level
        self.gender = gender
        self.is_vip = is_vip
        self.verification = verification

    def __eq__(self, other):
        return self.user_id == other.user_id

    def __hash__(self):
        return hash(self.user_id)

    def __str__(self):
        return 'user_id: {}, nickname: {}, 等级: {}, 性别: {}, 是否为vip: {}, 是否已实名认证: {}'.format(
            self.user_id, self.nick_name, self.level, self.gender, self.is_vip, self.verification
        )


def get_header():
    header = {
        'Content-Type': 'application/json;charset=utf-8',
        'User-Agent': 'PocketFans201807/6.0.13 (iPad; iOS 13.5; Scale/2.00)',
        'pa': util.generate_pa(),
        'appInfo': json.dumps({
            'vendor': 'apple',
            'deviceId': 0,
            "appVersion": "6.0.13",
            "appBuild": "200513",
            "osVersion": "13.5.0",
            "osType": "ios",
            "deviceName": "unknow",
            "os": "ios"
        }),
        'token': "wlOMD+ilcqVK2rwx5HLvLAs4YnFZPwUzc+i+TCf/awDRC3Wpta9lz9NbHK66DAPXeQ3oO6f4NnQ="
    }
    return header


def get_room_history_comments(room_id, start_time, end_time=0):
    next_start_time = get_room_comments(room_id, start_time, end_time)
    print(end_time)
    while next_start_time >= end_time:
        next_start_time = get_room_comments(room_id, next_start_time, end_time)
    print('done')


def get_room_comments(room_id, last_time, end_time):
    time.sleep(1.5)
    url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/all'
    params = {
        "roomId": room_id,
        "needTop1Msg": False,
        "nextTime": last_time
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).text
    except Exception as e:
        print(e)

    try:
        rsp_json = json.loads(r)
        msgs = rsp_json['content']['message']
        if not msgs:
            return -1
        parse_room_comments(msgs, end_time)
        next_time = rsp_json['content']['nextTime']
        return next_time
    except Exception as e:
        print(e)
        return -1


def parse_room_comments(msgs, end_time):
    try:
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id

            msg_time_0 = msg["msgTime"]
            if msg_time_0 < end_time:
                return

            msg_time = util.convert_timestamp_to_timestr(msg["msgTime"])
            if 'userId'  in extInfo['user'].keys():
                user_id = int(extInfo['user']['userId'])
            else:
                user_id = 0
            if 'gender' in extInfo['user'].keys():
                gender = int(extInfo['user']['gender'])
            else:
                gender = 0
            user_name = extInfo['user']['nickName']
            if 'level' in extInfo['user'].keys():
                level = int(extInfo['user']['level'])
            else:
                level = 1
            if 'vip' in extInfo['user'].keys():
                is_vip = extInfo['user']['vip']
            else:
                is_vip = False
            if 'Verification' in extInfo['user'].keys():
                verification = extInfo['user']['Verification']
            else:
                verification = False
            room_id = int(extInfo['sourceId'])

            fan = Fan(user_id, user_name, level, gender, is_vip, verification)
            rst[room_id].add(fan)

    except Exception as e:
        print(e)


def get_room_list():
    url = 'https://pocketapi.48.cn/im/api/v1/conversation/page'
    params = {
        "targetType": 0
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).json()
    except Exception as e:
        print(e)
    room_list = r['content']['conversations']
    rst = []
    for conv in room_list:
        if conv['ownerId'] == 63:
            continue
        room = {
            "name": conv['ownerName'],
            "id": int(conv['ownerId']),
            "room_id": int(conv['targetId'])
        }
        rst.append(room)
    return rst


if __name__ == '__main__':
    room_list = get_room_list()
    line = 1
    line2 = 1
    worksheet.write(0, 0, '成员姓名')
    worksheet.write(0, 1, '房间ID')
    worksheet.write(0, 2, '粉丝ID')
    worksheet.write(0, 3, '粉丝昵称')
    worksheet.write(0, 4, '等级')
    worksheet.write(0, 5, '性别')
    worksheet.write(0, 6, '是否为vip')
    worksheet.write(0, 7, '是否已实名认证')

    worksheet2.write(0, 0, '成员姓名')
    worksheet2.write(0, 1, '留言粉丝数')
    worksheet2.write(0, 2, '1-2级粉丝数占比')
    worksheet2.write(0, 3, '3-6级粉丝数占比')
    worksheet2.write(0, 4, '7-9级粉丝数占比')
    worksheet2.write(0, 5, '10级以上粉丝数占比')

    try:

        for room in room_list:
            print(room['name'])
            if room['room_id'] in [67236601]:
                continue
            rst[room['room_id']] = set()
            get_room_history_comments(room['room_id'], 1592236800000, 1592150400000)
            print('留言粉丝数: {}'.format(len(rst[room['room_id']])))

            level1_2 = 0
            level3_6 = 0
            level7_9 = 0
            level10_12 = 0
            for fan in rst[room['room_id']]:
                try:
                    print(fan)
                    if int(room['id']) == int(fan.user_id):
                        continue
                    worksheet.write(line, 0, room['name'])
                    worksheet.write(line, 1, room['room_id'])
                    worksheet.write(line, 2, fan.user_id)
                    worksheet.write(line, 3, fan.nick_name)
                    worksheet.write(line, 4, fan.level)
                    if fan.level <= 2:
                        level1_2 += 1
                    elif fan.level <= 6:
                        level3_6 += 1
                    elif fan.level <= 9:
                        level7_9 += 1
                    else:
                        level10_12 += 1
                    if fan.gender == 0:
                        worksheet.write(line, 5, '未知')
                    elif fan.gender == 1:
                        worksheet.write(line, 5, '男')
                    else:
                        worksheet.write(line, 5, '女')
                    if fan.is_vip:
                        worksheet.write(line, 6, '是')
                    else:
                        worksheet.write(line, 6, '否')
                    worksheet.write(line, 7, '是' if fan.verification else '否')
                    line += 1
                except Exception as e:
                    logger.exception(e)
                    continue
            worksheet2.write(line2, 0, room['name'])
            total = len(rst[room['room_id']])
            worksheet2.write(line2, 1, total)
            worksheet2.write(line2, 2, '%2f%%' % (level1_2 / total * 100))
            worksheet2.write(line2, 3, '%2f%%' % (level3_6 / total * 100))
            worksheet2.write(line2, 4, '%2f%%' % (level7_9 / total * 100))
            worksheet2.write(line2, 5, '%2f%%' % (level10_12 / total * 100))
            print('1-2级粉丝占比: {}, 3-6级占比: {}, 7-9级占比: {}, 10级以上占比: {}'.format('%2f%%' % (level1_2 / total * 100),
                                                                             '%2f%%' % (level3_6 / total * 100),
                                                                             '%2f%%' % (level7_9 / total * 100),
                                                                             '%2f%%' % (level10_12 / total * 100)))
            line2 += 1
    except Exception as e:
        print(e)
    finally:
        workbook.save('comments_data_20200615.xls')
