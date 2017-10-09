# -*- coding:utf-8 -*-

import requests
import json

import time
from qqhandler import QQHandler
from qqbot.utf8logger import INFO, ERROR, DEBUG
from bs4 import BeautifulSoup

import Queue
import utils
import global_config

import sys

reload(sys)
sys.setdefaultencoding('utf8')


class WDSHandler:
    def __init__(self, wds_notify_groups):
        self.comment_id_queue = []
        self.session = requests.session()
        self.wds_notify_groups = wds_notify_groups

        # self.init_comment_queues()

    def init_comment_queues(self):
        """
        初始化回复队列
        :param moxi_id:
        :param pro_id:
        :return:
        """
        try:
            self.comment_id_queue = []
            r = self.monitor_wds_comment()

            for reply in r['des']:
                reply_id = reply['reply_id']
                self.comment_id_queue.append(reply_id)
            DEBUG('微打赏评论队列: %d', len(self.comment_id_queue))
        except Exception as e:
            ERROR('初始化微打赏评论队列失败')
            ERROR(e)

    def wds_header(self):
        """
        微打赏header信息
        """
        header = {
            # 'Host': 'wds.modian.com',
            # 'Accept': 'application/json',
            # 'Accept-Encoding': 'gzip,deflate,br',
            # 'Connection': 'keep-alive',
            # 'Content-Length': '37',
            # 'Content-Type': 'application/x-www-form-urlencoded',
            # 'Origin': 'https://wds.modian.com',
            # 'X-Requested-With': 'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.40',
        }
        return header

    def monitor_wds_comment(self, page_num=1):
        """
        获取微打赏项目下的评论信息
        :param: moxi_id
        :param: pro_id
        :return:
        """
        jizi_url = 'https://wds.modian.com/ajax_comment'
        params = {
            'pageNum': page_num,
            'moxi_id': global_config.WDS_MOXI_ID,
            'pro_id': global_config.WDS_PRO_ID
        }
        try:
            # 注意，这里的param不用转换成json了，因为参数格式为x-www-form-urlencoded
            r = self.session.post(jizi_url, params, headers=self.wds_header())
        except Exception as e:
            ERROR('获取微打赏评论失败')
            ERROR(e)
        DEBUG('response: %s', r.text)
        print r.text
        r_json = r.json()
        if int(r_json['status']) != 0:
            ERROR('获取失败!')
        return r_json

    def parse_wds_comment(self, r):
        """
        对评论进行处理
        :param r:
        :return:
        """
        des = r['des']
        DEBUG(json.dumps(des))
        DEBUG('LENGTH OF DES: %d', len(des))
        msg = ''
        for reply in des:
            reply_id = reply['reply_id']

            if reply_id in self.comment_id_queue:
                continue
            self.comment_id_queue.append(reply_id)

            pay_amount = reply['pay_amount']
            if pay_amount == '':  # 去除单纯的评论
                continue

            user_info = reply['c_userinfo']
            user_id = user_info['nickname']

            sub_msg = '%s集资%s元\n' % (user_id, pay_amount)
            msg += sub_msg

        if msg and len(msg) > 0:
            project_info = self.get_current_and_target()
            msg += project_info
            msg += '集资项目: %s, 集资链接: %s' % (global_config.WDS_TITLE, global_config.WDS_LINK)
            QQHandler.send_to_groups(self.wds_notify_groups, msg)
            INFO('wds_message: %s', msg)
        DEBUG('集资评论队列: %d', len(self.comment_id_queue))

    def get_wds_rank(self, type0=1, page=1, page_size=50):
        """
        获取微打赏聚聚榜
        :param pro_id:
        :param type0:
        :param page:
        :param page_size:
        :return:
        """
        jizi_url = 'https://wds.modian.com/ajax_backer_list'
        params = {
            'pro_id': global_config.WDS_PRO_ID,
            'type': type0,
            'page': page,
            'pageSize': page_size
        }
        try:
            # 注意，这里的param不用转换成json了，因为参数格式为x-www-form-urlencoded
            r = self.session.post(jizi_url, params, headers=self.wds_header())
        except Exception as e:
            ERROR('获取微打赏评论失败')
            ERROR(e)
        r_json = r.json()
        print r.text
        DEBUG('response: %s', r.text)
        if int(r_json['status']) != 0:
            ERROR('获取失败!')
        return r_json

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
    global_config.WDS_PRO_ID = 7974
    global_config.WDS_MOXI_ID = 17011
    handler = WDSHandler([])
    handler.monitor_wds_comment()
    handler.get_wds_rank()
