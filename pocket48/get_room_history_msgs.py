# -*- coding:utf-8 -*-
import requests
import json
import sqlite3
import os
import time
from utils import util
from log.my_logger import pocket48_logger as logger

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'statistic', 'statistics.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_message (
                    message_id   VARCHAR PRIMARY KEY UNIQUE,
                    type         INTEGER,
                    user_id      INTEGER,
                    user_name    VARCHAR,
                    message_time DATETIME,
                    content      VARCHAR,
                    fans_comment VARCHAR
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


def get_room_history_msg(member_id, room_id, start_time):
    next_start_time = _get_room_msg(member_id, room_id, start_time, 30)
    while next_start_time != -1:
        next_start_time = _get_room_msg(member_id, room_id, next_start_time, 30)
    print('done')


def _get_room_msg(member_id, room_id, last_time, limit):
    time.sleep(15)
    url = 'https://pocketapi.48.cn/im/api/v1/chatroom/msg/list/homeowner'
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
        'token': "yMSKOykEsD+8u6jTBAg5m4PkNRhttI0DmqI9ZWADjpyG/omNfCnSX622NLFn8OU2jMjJuBc4te0="
    }
    params = {
        "ownerId": member_id,
        "roomId": room_id,
        "nextTime": last_time
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=header, verify=False).text
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
                    if msg['bodys'] == '红包消息':
                        print('红包消息')
                        content = '【红包】{}'.format(extInfo['redPackageTitle'])
                        save_msg_to_db(cursor, 106, msg_id, user_id, user_name, msg_time, content)
                    else:
                        print('普通消息: %s' % extInfo['text'])
                        cursor.execute("""
                            INSERT OR IGNORE INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                            (?, ?, ?, ?, ?, ?)
                        """, (msg_id, 100, user_id, user_name, msg_time, extInfo['text']))
                elif text_message_type == TextMessageType.REPLY:  # 翻牌消息
                    print('翻牌')
                    member_msg = extInfo['text']
                    fanpai_msg = extInfo['replyText']
                    fanpai_id = extInfo['replyName']
                    if fanpai_id:
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s: %s\n' % (
                            msg_time, user_name, member_msg, fanpai_id, fanpai_msg))
                        save_msg_to_db(cursor, 101, msg_id, user_id, user_name, msg_time, member_msg,
                                            fanpai_id + ': ' + fanpai_msg)
                    else:
                        message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                            msg_time, user_name, member_msg, fanpai_msg))
                        save_msg_to_db(cursor, 101, msg_id, user_id, user_name, msg_time, member_msg, fanpai_msg)

                    print(message)
                elif text_message_type == TextMessageType.LIVEPUSH:  # 露脸直播
                    print('露脸直播')
                    live_title = extInfo['liveTitle']
                    live_id = extInfo['liveId']
                    save_msg_to_db(cursor, 102, msg_id, user_id, user_name, msg_time, live_title)
                elif text_message_type == TextMessageType.VOTE:  # 投票
                    logger.debug('投票消息')
                    vote_content = extInfo['text']
                    message = '【发起投票】{}: {}\n'.format(user_name, vote_content)
                    save_msg_to_db(cursor, 104, msg_id, user_id, user_name, msg_time, vote_content)
                elif text_message_type == TextMessageType.FLIPCARD:
                    print('付费翻牌功能')
                    content = extInfo['question']

                    question_id = extInfo['questionId']
                    answer_id = extInfo['answerId']
                    source = extInfo['sourceId']
                    answer = extInfo['answer']

                    flip_message = ('【问】%s\n【答】%s: %s\n翻牌时间: %s\n' % (
                        content, user_name, answer, msg_time))
                    message = flip_message
                    save_msg_to_db(cursor, 105, msg_id, user_id, user_name, msg_time, answer, content)
            elif msg['msgType'] == MessageType.IMAGE:  # 图片消息
                print('图片')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']

                    message = ('【图片】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    save_msg_to_db(cursor, 200, msg_id, user_id, user_name, msg_time, url)

            elif msg['msgType'] == MessageType.AUDIO:  # 语音消息
                print('语音消息')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【语音】[%s]-%s: %s\n' % (msg_time, user_name, url))
                save_msg_to_db(cursor, 201, msg_id, user_id, user_name, msg_time, url)
            elif msg['msgType'] == MessageType.VIDEO:  # 小视频
                print('房间小视频')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【小视频】[%s]-%s: %s\n' % (msg_time, user_name, url))
                    save_msg_to_db(cursor, 202, msg_id, user_id, user_name, msg_time, url)
            elif msg['msgType'] == MessageType.EXPRESS:  # 大表情
                logger.debug('大表情')
                emotion_name = extInfo['emotionName']
                save_msg_to_db(cursor, 203, msg_id, user_id, user_name, msg_time, emotion_name)
            msg_time = msg['msgTime']
    except Exception as e:
        print(e)
    finally:
        conn.commit()
        cursor.close()
        return msg_time


def save_msg_to_db(cursor, op_code, message_id, user_id, user_name, message_time, content, fans_comment=''):
    """
    将消息存进db
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
                        INSERT OR IGNORE INTO 'room_message' (message_id, type, user_id, user_name, message_time, content, fans_comment) VALUES
                                                   (?, ?, ?, ?, ?, ?, ?)
                     """, (message_id, op_code, user_id, user_name, message_time, content, fans_comment))
    except Exception as e:
        logger.error('将口袋房间消息存入数据库')
        logger.exception(e)


def parse_idol_flip(question_id, answer_id, source):
    url = 'https://ppayqa.48.cn/idolanswersystem/api/idolanswer/v1/question_answer/detail'
    header = {
        'os': 'android',
        'User-Agent': 'Mobile_Pocket',
        'IMEI': '863526430773465',
        'token': 'HqSvVhnlxN89rywJREAtaCuzlDt3VtE8Md6Ye223vbuooVH3NaSAwoMEdjvq93Fn1zpDQgt3ayw=',
        'version': '6.0.0',
        'Content-Type': 'application/json;charset=utf-8',
        'Host': 'ppayqa.48.cn',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
    }
    params = {
            "questionId": question_id, "answerId": answer_id, "idolFlipSource": source
    }

    res = requests.post(url, data=json.dumps(params), headers=header).json()
    return res['content']['answer']


if __name__ == '__main__':
    import time
    get_room_history_msg(6432, 5780791, 0)
