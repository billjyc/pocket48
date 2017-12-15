# -*- coding:utf-8 -*-

import re
import sys
import time

import requests
from bs4 import BeautifulSoup
from qqbot.utf8logger import INFO, ERROR, DEBUG

from qq.qqhandler import QQHandler
from utils import global_config, util

reload(sys)
sys.setdefaultencoding('utf8')


class WDS:
    def __init__(self, link, title, post_id, pro_id, need_display_rank=False, current=0.0, target=0.0, support_num=0):
        self.link = link
        self.title = title
        self.post_id = post_id
        self.pro_id = pro_id
        self.need_display_rank = need_display_rank
        self.current = current
        self.target = target
        self.support_num = support_num


class WDSHandler:
    def __init__(self, wds_notify_groups, wds_array):
        # self.comment_id_queue = []
        self.session = requests.session()
        self.wds_notify_groups = wds_notify_groups
        self.wds_array = wds_array

        self.wds_queue_map = {}
        self.comment_id_queues = []

    def init_comment_queues(self):
        """
        初始化回复队列
        :return:
        """
        try:
            self.comment_id_queues = []
            for i in range(len(self.wds_array)):
                self.comment_id_queues.append([])

            for i in range(len(self.wds_array)):
                queue = self.comment_id_queues[i]
                r = self.monitor_wds_comment(self.wds_array[i])

                soup = BeautifulSoup(r, 'lxml')
                comment_list = soup.findAll(name='li')
                for comment in comment_list:
                    comment_id = comment.find(class_='add-jubao').get('to_comid')
                    queue.append(comment_id)

                self.wds_queue_map[self.wds_array[i]] = queue
        except Exception as e:
            ERROR('初始化微打赏评论队列失败')
            ERROR(e)

    def wds_header(self):
        """
        微打赏header信息
        """
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.40',
        }
        return header

    def monitor_wds_comment(self, wds, page_num=1):
        """
        获取微打赏项目下的评论信息
        :return:
        """
        jizi_url = 'https://wds.modian.com/ajax/comment_list'
        params = {
            'pageNum': page_num,
            'post_id': wds.post_id,
            'pro_id': wds.pro_id
        }
        try:
            # 注意，这里的param不用转换成json了，因为参数格式为x-www-form-urlencoded
            r = self.session.post(jizi_url, params, headers=self.wds_header())
        except Exception as e:
            ERROR('获取微打赏评论失败')
            ERROR(e)
        # DEBUG('response: %s', r.text)
        # print r.text
        r_json = r.json()
        if int(r_json['status']) != 0:
            ERROR('获取失败!')
        return r_json['data']['html']

    def parse_wds_comment2(self, r, wds):
        """
        对评论进行处理（微打赏接口变更，r变为html）
        :param r:
        :param wds:
        :return:
        """
        PAGE_SIZE = 20
        soup = BeautifulSoup(r, 'lxml')
        # print soup.prettify()
        comment_list = soup.findAll(name='li')
        support_num, current, target = self.get_current_and_target(wds)
        # project_info = '当前进度: %s元, 目标金额: %s元\n当前集资人数: %s\n' % (current, target, support_num)

        page_num = int(support_num) / PAGE_SIZE + 1
        wds_rank_list = []
        for i in range(page_num):
            rank_html = self.get_wds_rank(wds, page=i+1)
            if rank_html is None:
                break
            soup2 = BeautifulSoup(rank_html, 'lxml')
            wds_rank_list.extend(soup2.findAll(name='li'))

        project_info = '当前进度: %s元, 目标金额: %s元\n当前集资人数: %s\n' % (current, target, len(wds_rank_list))

        for comment in comment_list:
            comment_id = comment.find(class_='add-jubao').get('to_comid')
            # print comment_id

            comment_id_queue = self.wds_queue_map[wds]
            if comment_id in comment_id_queue:
                continue
            comment_id_queue.append(comment_id)

            nickname = comment.find(class_='nick').string
            nick_sup = comment.find(class_='nick_sup').string
            user_id = comment.find(class_='add-jubao').get('to_user')

            msg = '感谢 %s %s, %s\n' % (nickname, nick_sup, util.random_str(global_config.WDS_POSTSCRIPTS))

            rank_msg = ''
            DEBUG('WDS USER ID: %s', user_id)
            for rank in wds_rank_list:
                user_a = rank.a['href']
                uid = re.findall(r"\d+\.?\d*", user_a)[0]
                DEBUG('user_a: %s, uid: %s', user_a, uid)
                if uid == user_id:
                    cur_rank = rank.find(class_='suport_ran').string
                    total_amount = rank.find(class_='money').string
                    total_amount = total_amount.replace('¥ ', '')

                    if wds.need_display_rank is True:
                        rank_msg = "当前累计集资%s元，当前排名: %s\n" % (total_amount, cur_rank)
                    else:
                        rank_msg = "当前累计集资%s元\n" % total_amount
                    break
            if rank_msg and len(rank_msg) > 0:
                msg += rank_msg

            if msg and len(msg) > 0:
                msg += project_info
                msg += '集资项目: %s\n链接: %s' % (wds.title, wds.link)
                QQHandler.send_to_groups(self.wds_notify_groups, msg)
                INFO('wds_message: %s', msg)
                DEBUG('集资评论队列: %d', len(comment_id_queue))

            time.sleep(3)

    def get_wds_rank(self, wds, type0=1, page=1, page_size=20):
        """
        获取微打赏聚聚榜
        :param wds:
        :param pro_id:
        :param type0:
        :param page:
        :param page_size:
        :return:
        """
        jizi_url = 'https://wds.modian.com/ajax/backer_ranking_list'
        params = {
            'pro_id': wds.pro_id,
            'type': type0,
            'page': page,
            'page_size': page_size
        }
        try:
            # 注意，这里的param不用转换成json了，因为参数格式为x-www-form-urlencoded
            r = self.session.post(jizi_url, params, headers=self.wds_header())
        except Exception as e:
            ERROR('获取微打赏排名失败')
            ERROR(e)
        r_json = r.json()
        # DEBUG('response: %s', r.text)
        # 微打赏有bug，首页上和排名页上的人数不一致
        if 'data' not in r_json or int(r_json['status']) != 0:
            ERROR('微打赏排名获取失败!')
            return None
        return r_json['data']['html']

    def get_current_and_target(self, wds):
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
        r = requests.get(wds.link, headers=header)
        soup = BeautifulSoup(r.text, 'lxml')
        # print soup.prettify()

        DEBUG('集资项目: %s', wds.title)
        DEBUG('集资链接: %s', wds.link)
        project_info = soup.find_all(class_="project-info")[0]
        support_num = project_info.find_all(class_="b")[0].find_all(name="span")[0].contents[0].strip()
        DEBUG('当前集资人数: %s', support_num)
        wds.support_num = int(support_num.replace(',', ''))

        current = project_info.find_all(class_="current")[0].find_all(name="span")[1].contents[1].strip()
        DEBUG('当前进度: %s元', current)
        wds.current = float(current.replace(',', ''))
        target = project_info.find_all(class_="target")[0].find_all(name="span")[1].contents[1].strip()
        DEBUG('目标金额: %s元', target)
        wds.target = float(current.replace(',', ''))

        return support_num, current, target


if __name__ == '__main__':
    wds1 = WDS('https://wds.modian.com/show_weidashang_pro/9372', '冯晓菲《暗夜脚步声》集资活动2.0', 19274, 9372, False)
    wds2 = WDS('https://wds.modian.com/show_weidashang_pro/8303', '《暴走少女》冯晓菲应援会2017年第四届金曲大赏集资', 17526, 8303, False)
    wds_array = [wds1, wds2]
    handler = WDSHandler([], [])
    handler.wds_array = wds_array

    handler.init_comment_queues()

    r1 = handler.monitor_wds_comment(wds1)
    handler.parse_wds_comment2(r1, wds1)
    # handler.get_wds_rank(wds1)

    # handler.monitor_wds_comment(wds2)
    # handler.get_wds_rank(wds2)
