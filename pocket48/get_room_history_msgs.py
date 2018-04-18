# -*- coding:utf-8 -*-
import requests
import json
import sqlite3
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'statistic', 'statistics.db')
conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
                CREATE TABLE IF NOT EXISTS room_message (
                    message_id   VARCHAR,
                    type         INTEGER,
                    user_id      INTEGER,
                    user_name    VARCHAR,
                    message_time DATETIME,
                    content      VARCHAR,
                    fans_comment VARCHAR
                );
""")
cursor.close()


def get_room_history_msg(room_id, start_time):
    next_start_time = _get_room_msg(room_id, start_time, 300)
    while next_start_time != -1:
        next_start_time = _get_room_msg(room_id, next_start_time, 300)
    print('done')


def _get_room_msg(room_id, last_time, limit):
    url = 'https://pjuju.48.cn/imsystem/api/im/v1/member/room/message/mainpage'
    header = {
        'os': 'android',
        'User-Agent': 'Mobile_Pocket',
        'IMEI': '863526430773465',
        'token': 'VRb3GStAbywb2myk2c7K9seuVtXP+QCppdX5dR8xQbToO345jE1Mw11w/IIG1wLuOY4eAF9ifbM=',
        'version': '5.2.2',
        'Content-Type': 'application/json;charset=utf-8',
        'Host': 'pjuju.48.cn',
        'Connection': 'Keep-Alive',
        'Accept-Encoding': 'gzip'
        # 'Cache-Control': 'no-cache'
    }
    params = {
        "roomId": room_id, "lastTime": last_time, "limit": limit, "chatType": 0
    }
    try:
        r = requests.post(url, data=json.dumps(params), headers=header, verify=False).json()
    except Exception as e:
        print(e)

    msgs = r['content']['data']
    if len(msgs) == 0:
        return -1
    cursor = conn.cursor()
    msg_time = last_time

    try:
        for msg in msgs:
            extInfo = json.loads(msg['extInfo'])
            msg_id = msg['msgidClient']  # 消息id

            message_object = extInfo['messageObject']

            # print('extInfo.keys():' + ','.join(extInfo.keys()))
            if msg['msgType'] == 0:  # 文字消息
                if message_object == 'text':  # 普通消息
                    print('普通消息: %s' % extInfo['text'])
                    cursor.execute("""
                        INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                        (?, ?, ?, ?, ?, ?)
                    """, (msg_id, 100, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], extInfo['text']))
                elif message_object == 'faipaiText':  # 翻牌消息
                    print('翻牌')
                    member_msg = extInfo['messageText']
                    fanpai_msg = extInfo['faipaiContent']

                    message = ('【翻牌】[%s]-%s: %s\n【被翻牌】%s\n' % (
                        msg['msgTimeStr'], extInfo['senderName'], member_msg, fanpai_msg))
                    print(message)
                    cursor.execute("""
                                    INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content, fans_comment) VALUES
                                    (?, ?, ?, ?, ?, ?, ?)
                            """, (
                    msg_id, 101, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], member_msg, fanpai_msg))
                elif message_object == 'diantai':  # 电台直播
                    print('电台直播')
                    reference_content = extInfo['referenceContent']
                    live_id = extInfo['referenceObjectId']
                elif message_object == 'live':  # 露脸直播
                    print('露脸直播')
                    reference_content = extInfo['referenceContent']
                    live_id = extInfo['referenceObjectId']
                elif message_object == 'idolFlip':
                    print('付费翻牌功能')
                    user_name = extInfo['idolFlipUserName']
                    title = extInfo['idolFlipTitle']
                    content = extInfo['idolFlipContent']

                    question_id = extInfo['idolFlipQuestionId']
                    answer_id = extInfo['idolFlipAnswerId']
                    source = extInfo['idolFlipSource']
                    answer = parse_idol_flip(question_id, answer_id, source)

                    flip_message = ('【问】%s: %s\n【答】%s: %s\n翻牌时间: %s\n' % (
                        user_name, content, extInfo['senderName'], answer, msg['msgTimeStr']))
                    print(flip_message)

                    cursor.execute("""
                        INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content, fans_comment) VALUES
                        (?, ?, ?, ?, ?, ?, ?)
                        """, (msg_id, 105, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], answer,
                              user_name + ': ' + content))
            elif msg['msgType'] == 1:  # 图片消息
                bodys = json.loads(msg['bodys'])
                print('图片')
                if 'url' in bodys.keys():
                    url = bodys['url']

                    message = ('【图片】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url))
                    print(message)
                    cursor.execute("""
                       INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                                                        (?, ?, ?, ?, ?, ?)
                    """, (msg_id, 200, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], url))

            elif msg['msgType'] == 2:  # 语音消息
                print('语音消息')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']

                    message = ('【语音】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url))
                    print(message)
                    cursor.execute("""
                        INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                                                   (?, ?, ?, ?, ?, ?)
                     """, (msg_id, 201, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], url))
            elif msg['msgType'] == 3:  # 小视频
                print('房间小视频')
                bodys = json.loads(msg['bodys'])
                if 'url' in bodys.keys():
                    url = bodys['url']
                    message = ('【小视频】[%s]-%s: %s\n' % (msg['msgTimeStr'], extInfo['senderName'], url))
                    print(message)
                    cursor.execute("""
                     INSERT INTO 'room_message' (message_id, type, user_id, user_name, message_time, content) VALUES
                                    (?, ?, ?, ?, ?, ?)
                    """, (msg_id, 202, extInfo['senderId'], extInfo['senderName'], msg['msgTimeStr'], url))
            msg_time = msg['msgTime']
    except Exception as e:
        print(e)
    finally:
        conn.commit()
        cursor.close()
        return msg_time


def parse_idol_flip(question_id, answer_id, source):
    url = 'https://ppayqa.48.cn/idolanswersystem/api/idolanswer/v1/question_answer/detail'
    header = {
        'os': 'android',
        'User-Agent': 'Mobile_Pocket',
        'IMEI': '863526430773465',
        'token': 'VRb3GStAbywb2myk2c7K9seuVtXP+QCppdX5dR8xQbToO345jE1Mw11w/IIG1wLuOY4eAF9ifbM=',
        'version': '5.2.2',
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
    get_room_history_msg(5780791, 1519610400*1000)
