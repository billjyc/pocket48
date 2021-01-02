# -*- coding:utf-8 -*-
"""
六选之后，摩点关闭了粉丝应援类项目，API就不能使用了，在这里临时改为直接爬取网页
"""

import json
import logging
import time

import requests
from bs4 import BeautifulSoup

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)

from modian.modian_card_draw import handler as card_draw_handler
from qq.qqhandler import QQHandler
from utils import global_config, util
from utils.mysql_util import mysql_util


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
                    backer_money_icon = order.find(class_='icon-payment')
                    if not backer_money_icon:  # 纯评论，直接跳过
                        continue
                    comment_id = order.get('data-reply-id')

                    # oid使用项目id和评论id拼装
                    oid = str(modian_entity.pro_id) + str(comment_id)
                    my_logger.debug('oid: %s', oid)
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
        url = 'https://zhongchou.modian.com/realtime/get_simple_product?jsonpcallback=jQuery1_1&ids={}&if_all=1&_=2'.format(
            modian_entity.pro_id)
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
        modian_entity.title = project_profile_json['name']
        return modian_entity.target, modian_entity.current, modian_entity.title, modian_entity.support_num

    def query_project_orders(self, modian_entity, page=1, page_size=20):
        """
        查询项目订单（bs4版本）
        :param page_size:
        :param page:
        :param modian_entity:
        :return:
        """
        my_logger.info('查询项目订单, pro_id: %s', modian_entity.pro_id)
        api = 'https://zhongchou.modian.com/comment/ajax_comments?jsonpcallback=jQuery1_1&post_id={}&pro_class={}&page={}&page_size={}&_=2'.format(
            modian_entity.post_id,
            modian_entity.pro_class, page, page_size)
        r = self.session.get(api, headers=self.modian_header()).text
        r = r[40: -2]
        order_html = json.loads(r, encoding='utf-8')['html']
        soup = BeautifulSoup(order_html, 'lxml')
        # print(soup.prettify())
        # 对评论列表进行处理
        comment_list = soup.find_all(name='li')
        return comment_list

    def parse_order_details(self, orders, modian_entity):
        if len(self.order_queues[modian_entity.pro_id]) == 0 and len(orders) == 0:
            my_logger.debug('订单队列为空')
            return
        jiebang_activities = global_config.MODIAN_JIEBANG_ACTIVITIES[modian_entity.pro_id]
        flag_activities = global_config.MODIAN_FLAG_ACTIVITIES[modian_entity.pro_id]
        count_flag_activities = global_config.MODIAN_COUNT_FLAG_ACTIVITIES[modian_entity.pro_id]

        # 查询集资情况
        target, current, pro_name, backer_count = self.get_project_profiles(modian_entity)
        project_info = '当前进度: %s元, 目标金额: %s元' % (modian_entity.current, modian_entity.target)

        my_logger.debug('size of order %s queue: %s', modian_entity.pro_id,
                        len(self.order_queues[modian_entity.pro_id]))

        for comment in orders:
            user_id = comment.find(class_='comment-replay').get('data-reply_ruid')
            nickname = comment.find(class_='nickname').get_text().strip('\n')
            pay_time = util.convert_timestamp_to_timestr(time.time() * 1000)
            backer_money_icon = comment.find(class_='icon-payment')
            if not backer_money_icon:  # 纯评论，直接跳过
                continue
            backer_money = comment.find(class_='comment-txt').get_text().strip()[4:-1]
            backer_money = float(backer_money)
            comment_id = comment.get('data-reply-id')

            # oid使用项目id和评论id拼装
            oid = str(modian_entity.pro_id) + str(comment_id)
            my_logger.debug('oid: %s', oid)

            if oid in self.order_queues[modian_entity.pro_id]:
                continue
            my_logger.debug('项目%s队列长度: %s', modian_entity.pro_id, len(self.order_queues[modian_entity.pro_id]))

            # 每次需要更新一下昵称
            try:
                mysql_util.query("""
                                INSERT INTO `supporter` (`id`, `name`) VALUES (%s, %s)  ON DUPLICATE KEY
                                    UPDATE `name`=%s
                        """, (user_id, nickname, nickname))
            except Exception as e:
                my_logger.exception(e)

            try:
                mysql_util.query("""
                                INSERT INTO `order` (`id`,`supporter_id`,`backer_money`,`pay_time`, `pro_id`) 
                                    VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY
                                    UPDATE `id`=%s
                        """, (str(oid), user_id, backer_money, pay_time, modian_entity.pro_id, str(oid)))
            except Exception as e:
                my_logger.exception(e)

            msg = '感谢 %s(%s) 支持了%s元, %s\n' % (
                nickname, user_id, backer_money, util.random_str(global_config.MODIAN_POSTSCRIPTS))

            daka_rank, support_days = self.find_user_daka_rank(user_id, modian_entity.pro_id)

            if daka_rank != -1 and support_days:
                msg += '当前项目已打卡%s天\n' % support_days

            if modian_entity.need_display_rank is True:
                jizi_rank, backer_money = self.find_user_jizi_rank(user_id, modian_entity.pro_id)
                if jizi_rank != -1:
                    msg += '当前项目已集资%s元, 排名: %s' % (backer_money, jizi_rank)
            else:
                pass
            # 统计当前人数
            msg += '当前集资人数: %s\n' % backer_count

            # 抽卡播报
            card_report = ''
            if global_config.MODIAN_CARD_DRAW:
                card_report = self.card_draw_handler.draw(user_id, nickname, backer_money, pay_time)

            '''接棒相关'''
            my_logger.debug('接棒情况更新')
            for jiebang in jiebang_activities:
                # if jiebang.start_time > time.time():
                #     continue
                my_logger.debug('接棒活动详情: 【%s】', jiebang.name)
                my_logger.debug('集资金额: %s, 接棒最小金额: %s', backer_money, jiebang.min_stick_amount)
                if backer_money >= jiebang.min_stick_amount:

                    stick_num = util.compute_stick_num(jiebang.min_stick_amount, backer_money)
                    jiebang.current_stick_num += stick_num

                    jiebang.last_record_time = util.convert_timestamp_to_timestr(int(time.time() * 1000))
                    # 数据库也要更新
                    try:
                        mysql_util.query("""
                                        UPDATE jiebang SET `current_stick_num`=%s, `last_record_time`=%s WHERE `name`=%s
                                    """, (jiebang.current_stick_num, jiebang.last_record_time, jiebang.name))
                    except Exception as e:
                        my_logger.error('更新接棒数据失败')
                        my_logger.exception(e)
                    my_logger.debug('数据库接棒数据更新完成')
                    test_msg = ''
                    if jiebang.need_detail == 1:
                        test_msg = '【%s】, 当前第%s棒, 目标%s棒\n' \
                                   % (jiebang.name, jiebang.current_stick_num, jiebang.target_stick_num)
                    elif jiebang.need_detail == 0:
                        test_msg = '【%s】\n' % jiebang.name
                    elif jiebang.need_detail == 2:
                        test_msg = '【%s】, 当前第%s棒\n' \
                                   % (jiebang.name, jiebang.current_stick_num)
                    elif jiebang.need_detail == 3:
                        if stick_num > 1:
                            test_msg = '抽奖号: {}~{}\n'.format(jiebang.current_stick_num - stick_num + 1,
                                                             jiebang.current_stick_num)
                        else:
                            test_msg = '抽奖号: {}\n'.format(jiebang.current_stick_num)
                    my_logger.debug(test_msg)
                    if len(test_msg) > 0:
                        msg += test_msg
                        QQHandler.send_to_groups(['483548995'], test_msg)

            '''金额类flag相关'''
            my_logger.debug('flag情况更新')
            flag_test_msgs = ''
            for flag in flag_activities:
                my_logger.debug('Flag活动详情: %s', flag.name)
                my_logger.debug('Flag金额: %s, 结束时间: %s', flag.target_flag_amount, flag.end_time)
                diff = flag.target_flag_amount - current
                test_msgs = '【%s】, 目标金额: %s元, ' % (flag.name, flag.target_flag_amount)
                if diff > 0:
                    test_msgs += '距离目标还差%s元\n' % round(diff, 2)
                    flag_test_msgs += test_msgs
                else:
                    test_msgs += '已经达成目标\n'
            my_logger.debug(flag_test_msgs)
            if len(flag_test_msgs) > 0:
                QQHandler.send_to_groups(['483548995'], flag_test_msgs)
                # msg += flag_test_msgs

            '''人头类flag相关'''
            my_logger.debug('人头flag情况更新')
            count_flag_test_msgs = ''
            for flag in count_flag_activities:
                my_logger.debug('人头Flag活动详情: %s', flag.name)
                my_logger.debug('人头Flag目标: %s, 开始时间: %s, 结束时间: %s', flag.target_flag_amount,
                                flag.start_time, flag.end_time)
                target = flag.target_flag_amount

                # 统计当前人数
                rst = mysql_util.select_one("""
                                select count(distinct(`supporter_id`)) from `order` 
                                where `pro_id` = %s and `pay_time` <= %s and `pay_time` >= %s
                            """, (modian_entity.pro_id, flag.end_time, flag.start_time))

                # 目标人数为0，代表特殊类flag，只报人数
                if target == 0:
                    count_flag_test_msgs += '【%s】, 当前人数: %s ' % (flag.name, rst[0])
                else:
                    count_flag_test_msgs += '【%s】, 当前人数: %s, 目标人数: %s ' % (flag.name, rst[0], flag.target_flag_amount)

            my_logger.debug(count_flag_test_msgs)
            if len(count_flag_test_msgs) > 0:
                QQHandler.send_to_groups(['483548995'], count_flag_test_msgs)
                # msg += flag_test_msgs

            msg += '%s\n集资项目: %s\n链接: %s\n' % (project_info, pro_name, modian_entity.link)
            # msg += jizi_pk_report

            my_logger.info(msg)
            if global_config.USING_COOLQ_PRO is True:
                my_logger.debug('使用酷Q PRO发送图片')
                msg += '\n[CQ:image,file=http://wx1.sinaimg.cn/large/439a9f3fgy1fpllweknr6j201i01g0lz.jpg]\n'

            # if global_config.MODIAN_NEED_DISPLAY_PK:
            #     msg += self.pk_modian_activity()

            QQHandler.send_to_groups(modian_entity.broadcast_groups, msg)
            if card_report:
                QQHandler.send_to_groups(modian_entity.broadcast_groups, card_report)
                # QQHandler.send_to_groups(['483548995'], card_report)
            self.order_queues[modian_entity.pro_id].add(oid)

        # 更新接棒的数据库
        try:
            my_logger.debug('更新接棒活动信息:')
            for jiebang in jiebang_activities:
                my_logger.debug('current_stick_num: %s, last_record_time: %s, name: %s',
                                jiebang.current_stick_num, jiebang.last_record_time, jiebang.name)
                mysql_util.query("""
                            UPDATE jiebang SET current_stick_num=%s WHERE name=%s
                        """, (jiebang.current_stick_num, jiebang.name))
        except Exception as e:
            my_logger.exception(e)

    def find_user_jizi_rank(self, user_id, pro_id):
        """
        在集资榜中找到用户的排名
        :param user_id:
        :param pro_id:
        :return:
        """
        my_logger.info('找到id为%s的集资排名', user_id)
        ranking_list = mysql_util.select_all("""
                select supporter_id, sum(backer_money) as c 
                    from `order` where pro_id=%s group by supporter_id order by c desc;
                """, (pro_id,))
        cur_rank = 0
        for temp_id, total in ranking_list:
            cur_rank += 1
            if temp_id == user_id:
                return cur_rank, total
        return -1, -1

    def find_user_daka_rank(self, user_id, pro_id):
        """
        在打卡榜中找到用户的排名
        :param user_id:
        :param pro_id:
        :return:
        """
        my_logger.info('找到用户id为%s的打卡排名', user_id)
        ranking_list = mysql_util.select_all("""
            select supporter_id, count(distinct(date(pay_time))) as c 
            from `order` where pro_id=%s group by supporter_id order by c desc; 
        """, (pro_id,))
        cur_rank = 0
        for temp_id, days in ranking_list:
            cur_rank += 1
            if temp_id == user_id:
                return cur_rank, days
        return -1, -1

    def get_all_orders(self, modian_entity):
        """
        获取全部订单
        :return:
        """
        orders = []
        page = 1
        while True:
            my_logger.debug('获取全部订单，第{}页'.format(page))
            sub_orders = self.query_project_orders(modian_entity, page)
            # TODO: 这里需要处理
            if len(sub_orders) > 0:
                orders.extend(sub_orders)
                page += 1
            else:
                break
        return orders

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
    entity_array = []
    entity1 = ModianEntity('http://www.baidu.com', 'test', 79264)
    entity_array.append(entity1)
    handler = ModianHandlerBS4(['483548995'], entity_array)
    handler.init_order_queues()
