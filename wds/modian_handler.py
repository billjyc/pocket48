# -*- coding:utf-8 -*-
"""
摩点API文档地址：https://www.showdoc.cc/1702718?page_id=15700669
"""
import sys

import requests
from log.my_logger import logger as my_logger

import time
from utils import global_config, util
import hashlib
import urllib.parse

from qq.qqhandler import QQHandler


class ModianEntity:
    def __init__(self, link, title, pro_id, need_display_rank=False, current=0.0, target=0.0, support_num=0):
        self.link = link
        self.title = title
        self.pro_id = pro_id
        self.need_display_rank = need_display_rank
        self.current = current
        self.target = target
        self.support_num = support_num


class ModianHandler:
    def __init__(self, modian_notify_groups, modian_project_array):
        self.session = requests.session()
        self.modian_notify_groups = modian_notify_groups
        self.modian_project_array = modian_project_array

        self.wds_queue_map = {}
        self.order_queues = []

    def init_order_queues(self):
        # TODO: 初始化订单队列，用于发送集资播报
        pass

    def modian_header(self):
        """
        微打赏header信息
        """
        header = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.40',
        }
        return header

    def query_project_orders(self, modian_entity, page=1):
        """
        查询项目订单（摩点API版本）
        :param page:
        :param modian_entity:
        :return:
        """
        my_logger.info('查询项目订单, pro_id: %s', modian_entity.pro_id, modian_entity.title)
        api = 'https://wds.modian.com/api/project/orders'
        params = {
            'pro_id': modian_entity.pro_id,
            'page': page
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if int(r['status'] == 0):
            # pro_name = r['data']['pro_name']
            orders = r['data']
            my_logger.info('项目订单, page: %s, orders: %s', page, orders)
            return orders
        else:
            raise RuntimeError('获取项目订单查询失败')

    def get_modian_rankings(self, modian_entity, type0=1, page=1):
        """
        查询项目集资榜和打卡榜
        :param type0: 排名类型，1代表集资榜，2代表打卡榜
        :param modian_entity:
        :param page: 页号，每页默认返回20条
        :return:
        """
        if type0 == 1:
            my_logger.info('查询项目集资榜')
        elif type0 == 2:
            my_logger.info('查询项目打卡榜')
        else:
            my_logger.error('type0参数不合法')
            raise RuntimeError('type0参数不合法！')
        api = 'https://wds.modian.com/api/project/orders'
        params = {
            'pro_id': modian_entity.pro_id,
            'type': type0,
            'page': page
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if int(r['status']) == 0:
            # pro_name = r['data']['pro_name']
            rankings = r['data']
            my_logger.info('查询项目排名: %s', rankings)
            return rankings
        else:
            raise RuntimeError('获取项目排名失败, type=%d', type0)

    def get_current_and_target(self, modian_entity):
        """
        获取当前进度和总额（摩点API版本）
        :param modian_entity:
        :return:
        """
        my_logger.info('获取当前进度和总额: pro_id: %s', modian_entity.pro_id)
        api = 'https://wds.modian.com/api/project/detail'
        params = {
            'pro_id': modian_entity.pro_id
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if int(r['status']) == 0:
            data_json = r['data'][0]
            pro_name = data_json['pro_name']
            target = data_json['goal']
            current = data_json['already_raised']
            my_logger.info('目标: %s, 当前进度: %s', target, current)
            return target, current, pro_name
        else:
            raise RuntimeError('获取项目筹款结果查询失败')

    def make_post_params(self, post_fields):
        """
        获取post请求需要的参数
        :param post_fields:
        :return:
        """
        sign = self.__make_signature(post_fields)
        post_fields['sign'] = sign
        return post_fields

    def __make_signature(self, post_fields):
        """
        生成调用微打赏接口所需的签名

        PHP的例子：
            $post_fields = $_POST;
            ksort($post_fields);
            $md5_string = http_build_query($post_fields);
            $sign = substr(md5($md5_string), 5, 21);

        :param post_fields: post请求的参数
        :return:
        """
        post_fields_sorted = util.ksort(post_fields)
        md5_string = urllib.parse.urlencode(post_fields_sorted) + '&p=das41aq6'
        sign = hashlib.md5(md5_string.encode('utf-8')).hexdigest()[5:21]
        return sign


if __name__ == '__main__':
    modian1 = ModianEntity('https://zhongchou.modian.com/item/10358.html', 'SNH48江真仪生日应援集资1.0',
                           10358)
    modian_handler = ModianHandler(['483548995'], [modian1])
    modian_handler.get_current_and_target(modian1)
    modian_handler.get_modian_rankings(modian1, 1)
