# -*- coding:utf-8 -*-
import json
import os
import time

import requests
import xlwt
from utils import util
import traceback
from utils import global_config
import urllib.request

rst = {}
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workbook = xlwt.Workbook(encoding='utf-8')
worksheet = workbook.add_sheet('My Worksheet')


def get_header():
    header = {
        'Content-Type': 'application/json;charset=utf-8',
        'User-Agent': 'PocketFans201807/6.0.13 (iPad; iOS 13.5; Scale/2.00)',
        'pa': util.generate_pa(),
        'Host': 'pocketapi.48.cn',
        'appInfo': json.dumps({
            'vendor': 'apple',
            'deviceId': '0',
            "appVersion": "6.0.13",
            "appBuild": "200513",
            "osVersion": "13.5.0",
            "osType": "ios",
            "deviceName": "unknow",
            "os": "ios"
        }),
        'token': "oYf9xUxJ/GOY76RZdvww0wAz5FOzrMQj4yO3SnpKZfmjTHQ2y2FHNVFs8KtEAVYqjV6Cy/pIkd8="
    }
    return header


def get_single_week_rank(week_id):
    """
    获取单周的应援榜
    :param week_id:
    :return:
    """
    url = 'https://pocketapi.48.cn/gift/api/v1/melee/rank/getMeleeWeekRank'
    next_id = 0
    pre_next_id = -1

    global rst
    print(week_id)
    time.sleep(5)

    while next_id != pre_next_id:
        print(next_id)
        time.sleep(1)
        try:
            params = {
                "rankId": week_id,
                "nextId": next_id,
            }
            r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).json()
            print(r)

            if r["status"] == 200:
                rank_user_list = r["content"]["rankUserList"]
                for user in rank_user_list:
                    user_id = str(user['baseUserInfo']['userId'])
                    user_name = user['baseUserInfo']['nickname']
                    melee = user['melee']
                    if user_id not in rst:
                        rst[user_id] = {
                            'name': user_name,
                            'melee': melee
                        }
                    else:
                        rst[user_id]['melee'] = rst[user_id]['melee'] + melee
                pre_next_id = next_id
                next_id = r["content"]["nextId"]
        except Exception as e:
            print(e)
    print(rst)


if __name__ == "__main__":
    line = 1
    worksheet.write(0, 0, 'ID')
    worksheet.write(0, 1, '姓名')
    worksheet.write(0, 2, '鸡腿数')
    for i in range(88, 93):
        get_single_week_rank(i)

    for k, v in rst.items():
        worksheet.write(line, 0, k)
        worksheet.write(line, 1, v['name'])
        worksheet.write(line, 2, v['melee'])
        line += 1

    workbook.save('melee.xls')
