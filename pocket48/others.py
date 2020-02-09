# -*- coding:utf-8 -*-
import json
import os
import time

import requests
import xlwt

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workbook = xlwt.Workbook(encoding = 'utf-8')
worksheet = workbook.add_sheet('My Worksheet')


def get_header():
    header = {
        'Content-Type': 'application/json;charset=utf-8',
        'User-Agent': 'PocketFans201807/6.0.10 (iPhone; iOS 13.3; Scale/2.00)',
        'appInfo': json.dumps({
            'vendor': 'apple',
            'deviceId': 0,
            "appVersion": "6.0.10",
            "appBuild": "200120",
            "osVersion": "13.3.0",
            "osType": "ios",
            "deviceName": "iphone",
            "os": "ios"
        }),
        'token': "1WmtLFXVWnOSG36rlCa1v7leX71Cj1IjIvX/cSe9JiRxttXyp/VHZ3AtL0dTOh1ccMSn3nbVHb0="
    }
    return header


def get_room_msg(member_id, room_id, last_time):
    print('member_id: {}, room id: {}'.format(member_id, room_id))
    time.sleep(10)
    url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner'
    params = {
        "ownerId": member_id,
        "roomId": room_id,
        "nextTime": last_time
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).text
    except Exception as e:
        print(e)

    rsp_json = json.loads(r)
    try:
        msgs = rsp_json['content']['message']
        return msgs
    except Exception as e:
        print(e)
        return []


def get_device_info(msgs):
    if not msgs:
        return None
    device_info = {}
    for msg in msgs:
        extInfo = json.loads(msg['extInfo'])
        print(extInfo)
        try:
            if extInfo['sessionRole'] != 2:
                continue
            if 'config' in extInfo:
                device_info = extInfo['config']
                print(device_info)
                print('手机: {}, 版本: {}, 运营商: {}'.format(device_info['phoneName'], device_info['phoneSystemVersion'],
                                                       device_info['mobileOperators']))
                break
            else:
                continue
        except Exception as e:
            print(e)
    return device_info


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
            "id": conv['ownerId'],
            "room_id": conv['targetId']
        }
        rst.append(room)
    return rst


if __name__ == '__main__':
    # msgs = get_room_msg(9, 67313805, 0)
    # print(get_device_info(msgs))
    try:
        room_list = get_room_list()
        line = 1
        worksheet.write(0, 0, '姓名')
        worksheet.write(0, 1, '手机')
        worksheet.write(0, 2, '版本')
        worksheet.write(0, 3, '运营商')
        for room in room_list:
            msgs = get_room_msg(room['id'], room['room_id'], 0)
            print(room['name'])
            worksheet.write(line, 0, room['name'])
            device_info = get_device_info(msgs)
            if device_info:
                worksheet.write(line, 1, device_info['phoneName'])
                worksheet.write(line, 2, device_info['phoneSystemVersion'])
                worksheet.write(line, 3, device_info['mobileOperators'])
            line += 1
    except Exception as e:
        print(e)
    finally:
        workbook.save('device_list.xls')
