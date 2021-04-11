# -*- coding:utf-8 -*-
import requests
import json
import sqlite3
import os
import time
from utils import util
from log.my_logger import pocket48_logger as logger
import m3u8

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'statistic', 'statistics.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

total_time = 0
total_online_num = 0

cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_message (
                    message_id   VARCHAR PRIMARY KEY UNIQUE,
                    type         INTEGER,
                    user_id      INTEGER,
                    user_name    VARCHAR,
                    message_time DATETIME,
                    content      VARCHAR,
                    fans_comment VARCHAR,
                    fans_name VARCHAR
                );
""")
cursor.close()


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
        'User-Agent': 'PocketFans201807/6.1.1 (iPad; iOS 14.4; Scale/2.00)',
        'appInfo': json.dumps({
            'vendor': 'apple',
            'deviceId': 0,
            "appVersion": "6.1.1",
            "appBuild": "210202",
            "osVersion": "14.4.0",
            "osType": "ios",
            "deviceName": "iphone",
            "os": "ios"
        }),
        'token': "1xc3SYA7ZIjAXsDLu7Xgthg8YCwqswa5OCTh3ypGW4my7yDLscpsnTsnQCte/rnz3IL4TJ/QG/s="
    }
    return header


def get_room_history_live(member_id, room_id, start_time):
    next_start_time = _get_room_live(member_id, room_id, start_time, 30)
    while next_start_time != -1:
        next_start_time = _get_room_live(member_id, room_id, next_start_time, 30)
    print('done')


def get_live_one(live_id):
    time.sleep(1)
    global total_time, total_online_num
    url = 'https://pocketapi.48.cn/live/api/v1/live/getLiveOne'
    params = {
        "liveId": live_id,
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).text
    except Exception as e:
        print(e)

    rsp_json = json.loads(r)
    infos = rsp_json['content']
    online_num = infos['onlineNum']
    total_online_num += online_num
    play_stream_path = infos['playStreamPath']
    print(live_id)
    print(play_stream_path)

    playlist = m3u8.load(play_stream_path, verify_ssl=False)
    for segment in playlist.data['segments']:
        total_time += segment['duration']


def _get_room_live(member_id, room_id, last_time, limit):
    time.sleep(3)
    url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/aim/type'
    params = {
        "extMsgType": "USER_LIVE",
        "roomId": room_id,
        "ownerId": member_id,
        "nextTime": last_time
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=get_header(), verify=False).text
    except Exception as e:
        print(e)

    rsp_json = json.loads(r)
    msgs = rsp_json['content']['message']
    if len(msgs) == 0:
        return -1
    cursor = conn.cursor()
    msg_time = last_time
    try:
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id
            live_id = extInfo['id']

            get_live_one(live_id)
            msg_time = msg['msgTime']
    except Exception as e:
        print(e)
    finally:
        conn.commit()
        cursor.close()
        return rsp_json['content']['nextTime']


def get_room_history_msg(member_id, room_id, start_time):
    next_start_time = _get_room_msg(member_id, room_id, start_time, 30)
    while next_start_time != -1:
        next_start_time = _get_room_msg(member_id, room_id, next_start_time, 30)
    print('done')


def _get_room_msg(member_id, room_id, last_time, limit):
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
    msgs = rsp_json['content']['message']
    if len(msgs) == 0:
        return -1
    cursor = conn.cursor()
    msg_time = last_time

    try:
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id
            # rst = cursor.execute("""
            #     SELECT * FROM 'room_message' WHERE message_id=?
            # """, msg_id)

            msg_time = util.convert_timestamp_to_timestr(msg["msgTime"])
            user_id = extInfo['user']['userId']
            user_name = extInfo['user']['nickName']

            # print('extInfo.keys():' + ','.join(extInfo.keys()))
            if msg['msgType'] == MessageType.TEXT:  # 文字消息
                text_message_type = extInfo['messageType'].strip()
                if text_message_type == MessageType.TEXT:  # 普通消息
                    print('普通消息: %s' % extInfo['text'])
                    save_msg_to_db(cursor, 100, msg_id, user_id, user_name, msg_time, extInfo['text'])
                elif text_message_type == TextMessageType.REPLY:  # 翻牌消息
                    print('翻牌')
                    member_msg = extInfo['text']
                    fanpai_msg = extInfo['replyText']
                    fanpai_id = extInfo['replyName']
                    if fanpai_id:
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s: %s\n' % (
                            msg_time, user_name, member_msg, fanpai_id, fanpai_msg))
                        save_msg_to_db(cursor, 101, msg_id, user_id, user_name, msg_time, member_msg,
                                       fanpai_msg, fanpai_id)
                    else:
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                            msg_time, user_name, member_msg, fanpai_msg))
                        save_msg_to_db(cursor, 101, msg_id, user_id, user_name, msg_time, member_msg, fanpai_msg)

                    print(message)
                elif text_message_type == TextMessageType.LIVEPUSH:  # 露脸直播
                    print('露脸直播')
                    live_title = extInfo['liveTitle']
                    live_id = extInfo['liveId']
                    print(live_title + ' ' + live_id)
                    save_msg_to_db(cursor, 102, msg_id, user_id, user_name, msg_time, live_title)
                elif text_message_type == TextMessageType.VOTE:  # 投票
                    logger.debug('投票消息')
                    vote_content = extInfo['text']
                    message = '【发起投票】{}: {}\n'.format(user_name, vote_content)
                    print(message)
                    save_msg_to_db(cursor, 104, msg_id, user_id, user_name, msg_time, vote_content)
                elif text_message_type == TextMessageType.FLIPCARD:
                    print('付费翻牌功能')
                    content = extInfo['question']

                    question_id = extInfo['questionId']
                    answer_id = extInfo['answerId']
                    source = extInfo['sourceId']
                    answer = extInfo['answer']

                    fan_name = get_idol_flip_name(answer_id, question_id)
                    if fan_name:
                        print('付费翻牌id: {}'.format(fan_name))
                        flip_message = ('【问】%s: %s\n【答】%s: %s\n翻牌时间: %s\n' % (
                            fan_name, content, user_name, answer, msg_time))
                        save_msg_to_db(cursor, 105, msg_id, user_id, user_name, msg_time, answer, content, fan_name)
                    else:
                        flip_message = ('【问】%s\n【答】%s: %s\n翻牌时间: %s\n' % (
                            content, user_name, answer, msg_time))
                        save_msg_to_db(cursor, 105, msg_id, user_id, user_name, msg_time, answer, content)
                    message = flip_message
                    print(message)
                elif text_message_type == TextMessageType.PASSWORD_REDPACKAGE:
                    print('红包消息')
                    content = '【红包】{}'.format(extInfo['redPackageTitle'])
                    print(content)
                    save_msg_to_db(cursor, 106, msg_id, user_id, user_name, msg_time, content)
            elif msg['msgType'] == MessageType.IMAGE:  # 图片消息
                print('图片')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【图片】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    print(message)
                    save_msg_to_db(cursor, 200, msg_id, user_id, user_name, msg_time, url)
            elif msg['msgType'] == MessageType.AUDIO:  # 语音消息
                print('语音消息')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【语音】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    print(message)
                save_msg_to_db(cursor, 201, msg_id, user_id, user_name, msg_time, url)
            elif msg['msgType'] == MessageType.VIDEO:  # 小视频
                print('房间小视频')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【小视频】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    print(message)
                    save_msg_to_db(cursor, 202, msg_id, user_id, user_name, msg_time, url)
            elif msg['msgType'] == MessageType.EXPRESS:  # 大表情
                logger.debug('大表情')
                emotion_name = extInfo['emotionName']
                print(emotion_name)
                save_msg_to_db(cursor, 203, msg_id, user_id, user_name, msg_time, emotion_name)
            msg_time = msg['msgTime']
    except Exception as e:
        print(e)
    finally:
        conn.commit()
        cursor.close()
        return msg_time


def save_msg_to_db(cursor, op_code, message_id, user_id, user_name, message_time, content, fans_comment='',
                   fans_name=''):
    """
    将消息存进db
    :param fans_name:
    :param cursor:
    :param op_code:
    :param message_id:
    :param user_id:
    :param user_name:
    :param message_time:
    :param content:
    :param fans_comment:
    :return:
    """
    try:
        cursor.execute("""
        INSERT OR REPLACE INTO 'room_message' (message_id, type, user_id, user_name, message_time, 
        content, fans_comment, fans_name) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                     """, (message_id, op_code, user_id, user_name, message_time, content, fans_comment, fans_name))
    except Exception as e:
        logger.error('将口袋房间消息存入数据库')
        logger.exception(e)


def get_idol_flip_name(answer_id, question_id):
    """
    获取付费翻牌的提问id
    :param answer_id:
    :param question_id:
    :return:
    """
    url = 'https://pocketapi.48.cn/idolanswer/api/idolanswer/v1/question_answer/detail'
    params = {
        "answerId": str(answer_id),
        "questionId": str(question_id)
    }
    try:
        r = requests.post(url, data=json.dumps(params), verify=False, headers=get_header()).json()
        logger.info('获取付费翻牌用户的昵称，user_id: {}'.format(r['content']['userName']))
        logger.info(r)
        return r['content']['userName']
    except Exception as e:
        logger.exception(e)
        return None


if __name__ == '__main__':
    import time
    # path = 'https://cychengyuan-vod.48.cn/42402830/20210411/cy/588101487630815232-g2l4jmcrls26wvcy1iv9.m3u8'
    # playlist = m3u8.load(path, verify_ssl=False)
    # for segment in playlist.data['segments']:
    #     total_time += segment['duration']
    # print(total_time)
    # get_room_history_msg(6432, 67246079, 0)
    get_room_history_live(42402868, 248602943, 0)
    print('总时间: {}'.format(total_time))
    print('总人数: {}'.format(total_online_num))
