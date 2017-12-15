# -*- coding:utf-8 -*-
"""
摩点API文档地址：https://www.showdoc.cc/1702718?page_id=15700669
"""
import sys

import requests
from qqbot.utf8logger import INFO, ERROR, DEBUG
import time
from utils import global_config, util
import hashlib
import urllib

from qq.qqhandler import QQHandler

reload(sys)
sys.setdefaultencoding('utf8')


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
        api = 'https://wds.modian.com/api/project/orders'
        params = {
            'pro_id': modian_entity.pro_id,
            'page': page
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if r['status'] == 0:
            # pro_name = r['data']['pro_name']
            orders = r['data']
            return orders
        else:
            raise RuntimeError('获取项目订单查询失败')

    def get_modian_rankings(self, modian_entity, type=1, page=1):
        """
        查询项目集资榜和打卡榜
        :param type: 排名类型，1代表集资榜，2代表打卡榜
        :param modian_entity:
        :param page: 页号，每页默认返回20条
        :return:
        """
        api = 'https://wds.modian.com/api/project/orders'
        params = {
            'pro_id': modian_entity.pro_id,
            'type': type,
            'page': page
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if r['status'] == 0:
            # pro_name = r['data']['pro_name']
            rankings = r['data']
            return rankings
        else:
            raise RuntimeError('获取项目排名失败, type=%d', type)

    def get_current_and_target(self, modian_entity):
        """
        获取当前进度和总额（摩点API版本）
        :param modian_entity:
        :return:
        """
        api = 'https://wds.modian.com/api/project/detail'
        params = {
            'pro_id': modian_entity.pro_id
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if r['status'] == 0:
            pro_name = r['data']['pro_name']
            target = r['data']['goal']
            current = r['data']['already_raised']
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
            $sign = substr(md5($md5_string), 5, 16);

        :param post_fields: post请求的参数
        :return:
        """
        post_fields_sorted = util.ksort(post_fields)
        md5_string = urllib.urlencode(post_fields_sorted) + '&p=das41aq6'
        sign = hashlib.md5(md5_string).hexdigest()[5:21]
        return sign


if __name__ == '__main__':
    pass
