# -*- coding: utf-8 -*-

import os
import json
# from log.my_logger import logger
from utils import util
import hashlib
import urllib.parse
import time

import requests
import random
import string


class QQAIBot(object):
    def __init__(self, appkey, appid):
        self.appkey = appkey
        self.appid = appid

    def nlp_textchat(self, question, session):
        """
        基础闲聊接口
        :param question:
        :return:
        """
        url = 'https://api.ai.qq.com/fcgi-bin/nlp/nlp_textchat'
        params = {
            "app_id": self.appid,
            "time_stamp": int(time.time()),
            "nonce_str": self.generate_random_str(randomlength=16),
            "session": session,
            'question': question
        }
        r = requests.post(url, self.make_post_params(params), headers=self.header()).json()
        print(r)
        if r['ret'] == 0:
            print(r['data']['answer'])
            return r['data']['answer']
        else:
            print('调用基础闲聊接口出错，错误码: %s, msg: %s' % (r['ret'], r['msg']))

    def header(self):
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.40',
        }
        return header

    def make_post_params(self, post_fields):
        """
        获取post请求需要的参数
        :param post_fields:
        :return:
        """
        sign = self.make_sign(post_fields)
        post_fields['sign'] = sign
        return post_fields

    def generate_random_str(self, randomlength=16):
        """
        生成随机字符串
        string.digits=0123456789
        string.ascii_letters=abcdefghigklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
        :param randomlength:
        :return:
        """
        str_list = [random.choice(string.digits + string.ascii_letters) for i in range(randomlength)]
        random_str = ''.join(str_list)
        return random_str

    def make_sign(self, post_fields):
        """
        计算签名
        1.将<key, value>请求参数对按key进行字典升序排序，得到有序的参数对列表N
        2.将列表N中的参数对按URL键值对的格式拼接成字符串，得到字符串T（如：key1=value1&key2=value2），URL键值拼接过程value部分需要URL编码，URL编码算法用大写字母，例如%E8，而不是小写%e8
        3.将应用密钥以app_key为键名，组成URL键值拼接到字符串T末尾，得到字符串S（如：key1=value1&key2=value2&app_key=密钥)
        4.对字符串S进行MD5运算，将得到的MD5值所有字符转换成大写，得到接口请求签名
        :param post_fields:
        :return:
        """
        post_fields_sorted = util.ksort(post_fields)
        url_string = urllib.parse.urlencode(post_fields_sorted)
        url_string += '&app_key=%s' % self.appkey
        print(url_string)
        sign = hashlib.md5(url_string.encode('utf-8')).hexdigest()
        print(sign)
        sign = sign.upper()
        print(sign)
        return sign


if __name__ == '__main__':
    QQAIBot('***', '***').nlp_textchat('SNH48第五届偶像年度人气总决选', 10001)
