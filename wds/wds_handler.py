# -*- coding:utf-8 -*-

import requests
import json

import time
from qqhandler import QQHandler
from qqbot.utf8logger import INFO, ERROR, DEBUG
from bs4 import BeautifulSoup

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
            r = self.session.post(jizi_url, data=json.dumps(params), headers=self.wds_header(), verify=False)
        except Exception as e:
            ERROR('获取微打赏评论失败')
            ERROR(e)
        return r.json()

    def get_current_and_target(self):
        """
        获取当前进度和总额
        :return:
        """
        header = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip,deflate,sdch,br',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Host': 'wds.modian.com',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.400'
        }
        r = requests.get('https://wds.modian.com/show_weidashang_pro/7974', headers=header)
        soup = BeautifulSoup(r.text, 'lxml')
        # print soup.prettify()

        project_info = soup.find_all(class_="project-info")[0]
        support_num = project_info.find_all(class_="b")[0].find_all(name="span")[0].contents[0].strip()
        DEBUG('当前集资人数: %s', support_num)
        print support_num

        current = project_info.find_all(class_="current")[0].find_all(name="span")[1].contents[1].strip()
        DEBUG('当前进度: %s', current)
        print current
        target = project_info.find_all(class_="target")[0].find_all(name="span")[1].contents[1].strip()
        DEBUG('目标金额: %s', target)
        print target

        msg = '当前进度: %s, 目标金额: %s; 当前集资人数: %s' % (current, target, support_num)
        return msg


if __name__ == '__main__':
    handler = WDSHandler()
    handler.get_current_and_target()
