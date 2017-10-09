# -*- coding:utf-8 -*-

import requests
import json

import time
from qqhandler import QQHandler
from qqbot.utf8logger import INFO, ERROR, DEBUG

import Queue
import utils

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class WDSHandler():
    def __init__(self):
        self.comment_queue = []
        self.session = requests.session()

    def wds_header(self):
        """
        微打赏header信息
        """
        header = {
            'Host': 'wds.modian.com',
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Content-Length': '35',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://wds.modian.com',
            'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.40'
        }
        return header

    def monitor_wds_comment(self, moxi_id, pro_id):
        """
        获取微打赏项目下的评论信息
        :param: moxi_id
        :param: pro_id
        :return:
        """
        jizi_url = 'https://wds.modian.com/ajax_comment'
        params = {
            'pageNum': 2,
            'moxi_id': moxi_id,
            'pro_id': pro_id
        }
        try:
            r = self.session.post(jizi_url, data=json.dumps(params), header=self.wds_header(), verify=False)
        except Exception as e:
            ERROR('获取微打赏评论失败')
            ERROR(e)
        return r.json()
