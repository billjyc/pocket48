# -*- coding:utf-8 -*-
"""
六选之后，摩点关闭了粉丝应援类项目，API就不能使用了，在这里临时改为直接爬取网页
"""

import hashlib
import time
import urllib.parse
import uuid

import requests
import logging
import json
from bs4 import BeautifulSoup

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)

from modian.modian_card_draw import handler as card_draw_handler
from qq.qqhandler import QQHandler
from utils import global_config, util
from utils.mysql_util import mysql_util, Base, DBSession
from sqlalchemy import Column, String, Integer, Float, DateTime

from modian.modian_handler import ModianCountFlagEntity, ModianJiebangEntity


class ModianEntity:
    def __init__(self, link, title, pro_id, need_display_rank=False, broadcast_groups=[], current=0.0, target=0.0,
                 support_num=0):
        self.link = link
        self.title = title
        self.pro_id = pro_id
        self.need_display_rank = need_display_rank
        self.broadcast_groups = broadcast_groups
        self.current = current
        self.target = target
        self.support_num = support_num
        # 以下的2个参数很重要，获取订单时需要使用
        self.pro_class = 201
        self.post_id = 0


class ModianHandlerBS4:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, modian_notify_groups, modian_project_array):
        self.session = requests.session()
        self.modian_notify_groups = modian_notify_groups
        self.modian_project_array = modian_project_array

        self.card_draw_handler = card_draw_handler
        self.order_queues = {}

    def init_order_queues(self):
        for modian_entity in self.modian_project_array:
            try:
                my_logger.info('初始化%s的订单队列', modian_entity.pro_id)
                my_logger.debug(self.order_queues)
                if modian_entity.pro_id not in self.order_queues:
                    self.order_queues[modian_entity.pro_id] = set()
                    my_logger.debug('队列为空，重新初始化队列')
                else:
                    my_logger.debug('队列不为空，不重新初始化队列')
                    continue
                my_logger.debug('项目%s队列长度: %s', modian_entity.pro_id, len(self.order_queues[modian_entity.pro_id]))
                # 先拉一把项目的基本资料
                self.get_project_profiles(modian_entity)
                orders = self.query_project_orders(modian_entity)

                for order in orders:
                    user_id = order['user_id']
                    pay_time = order['pay_time']

                    oid = uuid.uuid3(uuid.NAMESPACE_OID, str(user_id) + pay_time)
                    self.order_queues[modian_entity.pro_id].add(oid)
            except Exception as e:
                my_logger.error('初始化订单队列失败！')
                my_logger.exception(e)

    def get_project_profiles(self, modian_entity):
        """
        获取集资项目基本资料
        :param modian_entity:
        :return:
        """
        my_logger.info('获取集资项目基本资料, 摩点id: {}'.format(modian_entity.pro_id))
        url = 'https://zhongchou.modian.com/realtime/get_simple_product?jsonpcallback=jQuery1_1&ids={}&if_all=1&_=2'.format(modian_entity.pro_id)
        rsp = self.session.get(url, headers=self.modian_header()).text
        # 中间结果是个json字符串，需要把头尾过滤掉
        rsp = rsp[41: -3]
        my_logger.info('返回结果: {}'.format(rsp))
        project_profile_json = json.loads(rsp, encoding='utf-8')
        modian_entity.pro_class = project_profile_json['pro_class']
        modian_entity.target = project_profile_json['goal']
        modian_entity.current = project_profile_json['backer_money']
        modian_entity.support_num = project_profile_json['backer_count']
        modian_entity.post_id = project_profile_json['moxi_post_id']

    def query_project_orders(self, modian_entity, page=1):
        """
        查询项目订单（bs4版本）
        :param page:
        :param modian_entity:
        :return:
        """
        my_logger.info('查询项目订单, pro_id: %s', modian_entity.pro_id)
        api = 'https://zhongchou.modian.com/comment/ajax_comments?jsonpcallback=jQuery1_1&post_id={}&pro_class={}&page=1&page_size=10&_=2'.format(modian_entity.post_id, modian_entity.pro_class)
        r = self.session.get(api, headers=self.modian_header()).text
        r = r[41: -2]
        order_html = json.loads(r, encoding='utf-8')['html']

        soup = BeautifulSoup(order_html, 'lxml')
        print(soup.prettify())

    def parse_order_details(self, orders, modian_entity):
        pass

    def modian_header(self):
        """
        微打赏header信息
        """
        header = {
            'Accept': 'text/javascript, application/javascript, application/ecmascript, application/x-ecmascript, */*; q=0.01',
            'Host': 'zhongchou.modian.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.104 Safari/537.36 Core/1.53.3408.400 QQBrowser/9.6.12028.40',
        }
        return header


if __name__ == '__main__':
    text = """window[decodeURIComponent('jQuery1_1')
]({
    "status": 1,
    "comment_count": "31",
    "html": "    <!--   精彩评论列表  -->\n    \n    <!--  精彩评论分割线  -->\n    \n    <!--   普通评论列表   -->\n            <ul class=\"comment-lists\">\n                            <li class=\"comment-list\" data-reply-id=\"1023064\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=1684035\">\n                    <img src=\"https://p.moimg.net/ico/2018/03/18/20180318_1521366215_3346.jpg\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=1684035\">billjyc1_h4u</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span><span class=\"honor big_star_3\"></span>\n                                    </p>\n                <p class=\"time\">今天17:08</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1023064\" data-post_id=\"106056\" data-reply_ruid=\"1684035\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"1684035\" data-favor_count=\"0\" data-reply_id=\"1023064\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                test\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022993\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=3933343\">\n                    <img src=\"https://p.moimg.net/ico/2019/04/18/20190418_1555580252_9213.jpg?imageMogr2/auto-orient/strip\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=3933343\">弥晨</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天16:19</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022993\" data-post_id=\"106056\" data-reply_ruid=\"3933343\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"3933343\" data-favor_count=\"0\" data-reply_id=\"1022993\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 203.4 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022943\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=2134888\">\n                    <img src=\"https://qzapp.qlogo.cn/qzapp/101119044/5ECF6CC524045EBEC3D26A73FCE36348/30\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=2134888\">木殇</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天15:38</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022943\" data-post_id=\"106056\" data-reply_ruid=\"2134888\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"2134888\" data-favor_count=\"0\" data-reply_id=\"1022943\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 101.7 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022787\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=1363430\">\n                    <img src=\"https://p.moimg.net/ico/2018/06/06/20180606_1528253464_2879.jpg?imageMogr2/auto-orient/strip\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=1363430\">远方0327</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span><span class=\"honor big_star_3\"></span>\n                                    </p>\n                <p class=\"time\">今天13:15</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022787\" data-post_id=\"106056\" data-reply_ruid=\"1363430\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"1363430\" data-favor_count=\"0\" data-reply_id=\"1022787\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 101.7 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022770\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=1166034\">\n                    <img src=\"https://p.moimg.net/ico/2019/04/29/20190429_1556470414_8195.jpg?imageMogr2/auto-orient/strip\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=1166034\">浪漫幻想家天崽</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天13:05</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022770\" data-post_id=\"106056\" data-reply_ruid=\"1166034\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"1166034\" data-favor_count=\"0\" data-reply_id=\"1022770\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 153.7 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022629\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=2134888\">\n                    <img src=\"https://qzapp.qlogo.cn/qzapp/101119044/5ECF6CC524045EBEC3D26A73FCE36348/30\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=2134888\">木殇</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天10:56</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022629\" data-post_id=\"106056\" data-reply_ruid=\"2134888\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"2134888\" data-favor_count=\"0\" data-reply_id=\"1022629\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 10.17 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022620\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=2113312\">\n                    <img src=\"https://qzapp.qlogo.cn/qzapp/101119044/8D975E534CB782BF8AF67BE61DD5D99B/30\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=2113312\">欠揍青年</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天10:46</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022620\" data-post_id=\"106056\" data-reply_ruid=\"2113312\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"2113312\" data-favor_count=\"0\" data-reply_id=\"1022620\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 10.17 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022612\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=1179445\">\n                    <img src=\"https://p.moimg.net/ico/1179445_1484279412.jpg\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=1179445\">didi滴滴滴滴</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天10:43</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022612\" data-post_id=\"106056\" data-reply_ruid=\"1179445\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"1179445\" data-favor_count=\"0\" data-reply_id=\"1022612\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 10.17 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022607\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=1184642\">\n                    <img src=\"https://p.moimg.net/project/project_20190621_1561119768_1049_crop.png?imageMogr2/auto-orient/strip\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=1184642\">我会有黄灰的</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天10:41</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022607\" data-post_id=\"106056\" data-reply_ruid=\"1184642\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"1184642\" data-favor_count=\"0\" data-reply_id=\"1022607\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 101.7 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                            <li class=\"comment-list\" data-reply-id=\"1022606\" data-isshow=\"1\">\n    <div class=\"comment-item-top clearfix\">\n        <div class=\"top-left\">\n            <div class=\"avater\">\n                <a href=\"https://me.modian.com/u/detail?uid=1592253\">\n                    <img src=\"https://p.moimg.net/icon/2018/01/26/1592253_1516976409.jpeg\" onerror=\"javascript:this.src='https://s.moimg.net/img/web4-0/default_profile@3x.png'\" alt=\"\">\n                                            \n                                    </a>\n            </div>\n            <div class=\"user-info\">\n                <p class=\"nickname\">\n                    <a href=\"https://me.modian.com/u/detail?uid=1592253\">慕容</a>\n                                            <span class=\"honor gold_pig_8\"></span><span class=\"honor commenter_3\"></span>\n                                    </p>\n                <p class=\"time\">今天10:40</p>\n            </div>\n        </div>\n                    <div class=\"top-right\">\n                <span style=\"display:none\">\n                    <i class=\"iconfont icon-report\"></i> <i>举报</i>\n                </span>\n                <span class=\"comment-replay\" data-cur=\"parent\" data-reply_rid=\"1022606\" data-post_id=\"106056\" data-reply_ruid=\"1592253\">\n                    <i class=\"iconfont icon-edit\"></i> <i>回复</i>\n                </span>\n                <span  data-post_id=\"106056\" data-favor_uid=\"1592253\" data-favor_count=\"0\" data-reply_id=\"1022606\">\n                    <i class=\"iconfont icon-like\"></i> <i class=\"favor_count\"></i>\n                </span>\n            </div>\n            </div>\n    <div class=\"comment-txt\">\n                    <i class=\"iconfont icon-payment\" style=\"color:#7a8087;\"></i>\n                支持了 101.7 元\n    </div>\n\n    \n    <!--   二级评论  -->\n        <!--   二级评论  -->\n</li>\n                    </ul>\n    "
});"""
    print(text[41:-2])
