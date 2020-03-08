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

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
workbook = xlwt.Workbook(encoding='utf-8')
worksheet = workbook.add_sheet('My Worksheet')

member_messages = {}


class MessageType:
    TEXT = 'TEXT'  # 文字消息
    IMAGE = 'IMAGE'  # 图片消息
    EXPRESS = 'EXPRESS'  # 大表情
    AUDIO = 'AUDIO'  # 语音
    VIDEO = 'VIDEO'  # 视频


class TextMessageType:
    TEXT = 'TEXT'  # 普通文字消息
    REPLY = 'REPLY'  # 普通翻牌
    FLIPCARD = 'FLIPCARD'  # 鸡腿翻牌
    LIVEPUSH = 'LIVEPUSH'  # 直播
    VOTE = 'VOTE'  # 投票
    PASSWORD_REDPACKAGE = 'PASSWORD_REDPACKAGE'  # 红包消息


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
        'token': global_config.POCKET48_TOKEN
        # 'token': 'z4Jy8aeTC2CVoC/LLulzuHrCv84qaYfPxwLijUOsjPD7s1eKk0oITczIz42VyZ7bBWrGHjP8/mg='
    }
    return header


def get_room_history_msg(member_id, room_id, start_time, end_time=1555344000000):
    next_start_time = get_room_msg(member_id, room_id, start_time, end_time)
    while next_start_time >= end_time:
        next_start_time = get_room_msg(member_id, room_id, next_start_time, end_time)
    print('done')


def get_room_msg(member_id, room_id, last_time, end_time):
    print('member_id: {}, room id: {}'.format(member_id, room_id))
    time.sleep(5)
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

    try:
        rsp_json = json.loads(r)
        msgs = rsp_json['content']['message']
        if not msgs:
            return -1
        parse_room_msg(msgs, end_time)
        next_time = rsp_json['content']['nextTime']
        return next_time
    except Exception as e:
        print(e)
        return -1


def parse_room_msg(msgs, end_time):
    try:
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id
            # rst = cursor.execute("""
            #     SELECT * FROM 'room_message' WHERE message_id=?
            # """, msg_id)

            msg_time_0 = msg["msgTime"]
            if msg_time_0 < end_time:
                return

            msg_time = util.convert_timestamp_to_timestr(msg["msgTime"])
            user_id = extInfo['user']['userId']
            user_name = extInfo['user']['nickName']
            if int(user_id) != member_messages['id']:
                continue
            # print('extInfo.keys():' + ','.join(extInfo.keys()))
            if msg['msgType'] == MessageType.TEXT:  # 文字消息
                text_message_type = extInfo['messageType'].strip()
                if text_message_type == MessageType.TEXT:  # 普通消息
                    print('普通消息: %s' % extInfo['text'])
                    member_messages['100'] += 1
                elif text_message_type == TextMessageType.REPLY:  # 翻牌消息
                    print('翻牌')
                    member_msg = extInfo['text']
                    fanpai_msg = extInfo['replyText']
                    fanpai_id = extInfo['replyName']
                    if fanpai_id:
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s: %s\n' % (
                            msg_time, user_name, member_msg, fanpai_id, fanpai_msg))
                    else:
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                            msg_time, user_name, member_msg, fanpai_msg))
                    print(message)
                    member_messages['101'] += 1
                elif text_message_type == TextMessageType.LIVEPUSH:  # 露脸直播
                    print('露脸直播')
                    live_title = extInfo['liveTitle']
                    live_id = extInfo['liveId']
                    print(live_title + ' ' + live_id)
                    member_messages['102'] += 1
                elif text_message_type == TextMessageType.VOTE:  # 投票
                    print('投票消息')
                    vote_content = extInfo['text']
                    message = '【发起投票】{}: {}\n'.format(user_name, vote_content)
                    print(message)
                    member_messages['104'] += 1
                elif text_message_type == TextMessageType.FLIPCARD:
                    print('付费翻牌功能')
                    content = extInfo['question']
                    question_id = extInfo['questionId']
                    answer_id = extInfo['answerId']
                    source = extInfo['sourceId']
                    answer = extInfo['answer']

                    message = '【问】{}\n【答】{}'.format(content, answer)
                    print(message)
                    member_messages['105'] += 1
                elif text_message_type == TextMessageType.PASSWORD_REDPACKAGE:
                    print('红包消息')
                    content = '【红包】{}'.format(extInfo['redPackageTitle'])
                    print(content)
                    member_messages['106'] += 1
            elif msg['msgType'] == MessageType.IMAGE:  # 图片消息
                print('图片')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【图片】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    print(message)
                    member_messages['200'] += 1
            elif msg['msgType'] == MessageType.AUDIO:  # 语音消息
                print('语音消息')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【语音】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    print(message)
                    member_messages['201'] += 1
            elif msg['msgType'] == MessageType.VIDEO:  # 小视频
                print('房间小视频')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【小视频】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    print(message)
                    member_messages['202'] += 1
            elif msg['msgType'] == MessageType.EXPRESS:  # 大表情
                print('大表情')
                emotion_name = extInfo['emotionName']
                print(emotion_name)
                member_messages['203'] += 1
    except Exception as e:
        print(e)


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
            "id": int(conv['ownerId']),
            "room_id": int(conv['targetId'])
        }
        rst.append(room)
    return rst


def get_member_all_posts(member_id, next_id="0"):
    """
    获取成员全部动态
    :param member_id: 
    :param next_id: 
    :return: 
    """
    url = 'https://pocketapi.48.cn/posts/api/v1/posts/timeline/home/new'
    print('next_id: {}'.format(next_id))
    params = {
        "nextId": next_id,
        "userId": member_id
    }
    r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).json()
    if r['status'] == 200:
        next_id = r['content']['nextId']
        post_list = r['content']['postsInfo']

        for post in post_list:
            post = post['data']['postsInfo']
            print(util.convert_timestamp_to_timestr(int(post['createAt'])))
            print(handle_weibo_text(post['postContent'].rstrip('\n')))
            if 'previewImg' in post and post['previewImg']:
                print("图片：")
                for img in post['previewImg']:
                    print('https://source.48.cn/{}'.format(img['imgUrl']))

        get_member_all_posts(member_id, next_id)


def handle_weibo_text(weibo_text):
    """
    处理动态文字，去除html标签
    :param weibo_text:
    :return:
    """
    from bs4 import BeautifulSoup
    weibo_text = '<div>' + weibo_text + '</div>'
    soup = BeautifulSoup(weibo_text.replace('<br />', '\n').replace('<br/>', '\n'), 'lxml')
    return soup.text


def get_member_all_images(member_id, next_id="0"):
    """
    获取成员全部图片
    :param member_id:
    :param next_id:
    :return:
    """
    url = 'https://pocketapi.48.cn/posts/api/v1/posts/img/list'
    print('next_id: {}'.format(next_id))
    params = {
        "nextId": next_id,
        "userId": member_id
    }
    r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).json()
    if r['status'] == 200:
        img_list = r['content']['list']
        next_id = r['content']['next']
        img_header = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
            'upgrade-insecure-requests': '1',
            'accept-encoding': 'gzip, deflate, br',
        }

        for img in img_list:
            img_url = 'https://source.48.cn/{}'.format(img['imgUrl'])
            print(img_url)

            # 生成图片名
            strs = img['imgUrl'].split('/')
            if len(strs) >= 3:
                date_str = strs[len(strs) - 2]
                file_name = strs[len(strs) - 1]

            if not os.path.exists('./{}'.format(date_str)):
                os.mkdir(date_str)
            img_name = './{}/{}'.format(date_str, file_name)
            html = requests.get(img_url, headers=img_header, verify=False)
            with open(img_name, 'wb') as f:
                f.write(html.content)
            f.close()

        get_member_all_images(member_id, next_id)


if __name__ == '__main__':
    # msgs = get_room_msg(9, 67313805, 0)
    # print(get_device_info(msgs))
    # 获取房间列表
    # try:
    #     room_list = get_room_list()
    #     line = 1
    #     worksheet.write(0, 0, '姓名')
    #     worksheet.write(0, 1, '手机')
    #     worksheet.write(0, 2, '版本')
    #     worksheet.write(0, 3, '运营商')
    #     for room in room_list:
    #         msgs = get_room_msg(room['id'], room['room_id'], 0)
    #         print(room['name'])
    #         worksheet.write(line, 0, room['name'])
    #         device_info = get_device_info(msgs)
    #         if device_info:
    #             worksheet.write(line, 1, device_info['phoneName'])
    #             worksheet.write(line, 2, device_info['phoneSystemVersion'])
    #             worksheet.write(line, 3, device_info['mobileOperators'])
    #         line += 1
    # except Exception as e:
    #     print(e)
    # finally:
    #     workbook.save('device_list.xls')
    # try:
    #     room_list = get_room_list()
    #     line = 1
    #     worksheet.write(0, 0, 'ID')
    #     worksheet.write(0, 1, '姓名')
    #     worksheet.write(0, 2, '房间id')
    #     worksheet.write(0, 3, '文字消息数')
    #     worksheet.write(0, 4, '普通翻牌数')
    #     worksheet.write(0, 5, '直播')
    #     worksheet.write(0, 6, '投票')
    #     worksheet.write(0, 7, '付费翻牌')
    #     worksheet.write(0, 8, '红包')
    #     worksheet.write(0, 9, '图片')
    #     worksheet.write(0, 10, '语音')
    #     worksheet.write(0, 11, '视频')
    #     worksheet.write(0, 12, '总数')
    #     for room in room_list:
    #         member_messages = {'id': room['id'], 'name': room['name'], 'room_id': room['room_id'], '100': 0, '101': 0,
    #                            '102': 0, '103': 0, '104': 0, '105': 0, '106': 0, '200': 0, '201': 0, '202': 0, '203': 0}
    #         print(room['name'])
    #         if room['id'] in [63, 327683, 21, 8, 63554, 6738, 38, 1, 327597, 5566, 327682, 5973]:
    #             continue
    #         get_room_history_msg(room['id'], room['room_id'], 1581177599000)
    #         print(member_messages)
    #         sum = member_messages['100'] + member_messages['101'] + member_messages['102'] + member_messages['103'] + member_messages['104'] + member_messages['105'] + member_messages['106'] + member_messages['201'] + member_messages['202'] + member_messages['203']
    #         worksheet.write(line, 0, member_messages['id'])
    #         worksheet.write(line, 1, member_messages['name'])
    #         worksheet.write(line, 2, member_messages['room_id'])
    #         worksheet.write(line, 3, member_messages['100'])
    #         worksheet.write(line, 4, member_messages['101'])
    #         worksheet.write(line, 5, member_messages['102'])
    #         worksheet.write(line, 6, member_messages['104'])
    #         worksheet.write(line, 7, member_messages['105'])
    #         worksheet.write(line, 8, member_messages['106'])
    #         worksheet.write(line, 9, member_messages['200'])
    #         worksheet.write(line, 10, member_messages['201'])
    #         worksheet.write(line, 11, member_messages['202'])
    #         worksheet.write(line, 12, sum)
    #         line += 1
    # except Exception as e:
    #     print(e)
    #     traceback.print_exc()
    # finally:
    #     workbook.save('spring_festival.xls')
    # get_member_all_images(6432, "61674")
    get_member_all_posts(6432, "0")
