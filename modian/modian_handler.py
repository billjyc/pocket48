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
import random
import sqlite3
import uuid
from modian.modian_card_draw import CardDrawHandler, Card

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


class ModianJiebangEntity:
    def __init__(self, name, pro_id, current_stick_num, last_record_time, start_time, end_time, target_stick_num,
                 min_stick_amount):
        self.name = name
        self.pro_id = pro_id
        self.current_stick_num = current_stick_num
        self.last_record_time = last_record_time
        self.start_time = start_time
        self.end_time = end_time
        self.target_stick_num = target_stick_num
        self.min_stick_amount = min_stick_amount


class ModianFlagEntity:
    def __init__(self, name, pro_id, target_flag_amount, end_time, remark):
        self.name = name
        self.pro_id = pro_id
        self.target_flag_amount = target_flag_amount
        self.end_time = end_time
        self.remark = remark


class ModianHandler:
    def __init__(self, modian_notify_groups, modian_project_array):
        self.session = requests.session()
        self.modian_notify_groups = modian_notify_groups
        self.modian_project_array = modian_project_array

        self.jizi_rank_list = []
        self.daka_rank_list = []

        self.card_draw_handler = CardDrawHandler()
        self.order_queues = {}

        # self.init_order_queues()

    def init_order_queues(self):
        for modian_entity in self.modian_project_array:
            try:
                my_logger.info('初始化%s的订单队列', modian_entity.pro_id)
                self.order_queues[modian_entity.pro_id] = set()
                orders = self.query_project_orders(modian_entity)
                retry_time = 0
                while retry_time < 5:
                    retry_time += 1
                    if len(orders) == 0:
                        my_logger.debug('请求订单失败，第%s次重试', retry_time)
                        orders = self.query_project_orders(modian_entity)
                    else:
                        break

                for order in orders:
                    user_id = order['user_id']
                    pay_time = order['pay_time']

                    oid = uuid.uuid3(uuid.NAMESPACE_OID, str(user_id) + pay_time)
                    self.order_queues[modian_entity.pro_id].add(oid)
            except Exception as e:
                my_logger.error('初始化订单队列失败！')
                my_logger.error(e)

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
        my_logger.info('查询项目订单, pro_id: %s', modian_entity.pro_id)
        api = 'https://wds.modian.com/api/project/orders'
        params = {
            'pro_id': modian_entity.pro_id,
            'page': page
        }
        r = requests.post(api, self.make_post_params(params), headers=self.modian_header()).json()
        if int(r['status']) == 0:
            orders = r['data']
            my_logger.info('项目订单: page: %s, orders: %s', page, orders)
            return orders
        if int(r['status']) == 2:  # 该页没有订单
            my_logger.info('项目订单: page: %s, 数据为空', page)
            return []
        else:
            raise RuntimeError('获取项目订单查询失败')

    def parse_order_details(self, orders, modian_entity):
        if len(self.order_queues[modian_entity.pro_id]) == 0:
            my_logger.debug('订单队列为空')
            return
        # time_tmp = time.time()
        jiebang_activities = global_config.MODIAN_JIEBANG_ACTIVITIES[modian_entity.pro_id]
        flag_activities = global_config.MODIAN_FLAG_ACTIVITIES[modian_entity.pro_id]
        # 查询集资情况
        target, current, pro_name = self.get_current_and_target(modian_entity)
        project_info = '当前进度: %s元, 目标金额: %s元\n当前集资人数: %s' % (current, target, len(self.jizi_rank_list))

        modian_entity.current = current
        modian_entity.title = pro_name
        modian_entity.target = target
        modian_entity.support_num = len(self.jizi_rank_list)

        for order in orders:
            user_id = order['user_id']
            nickname = order['nickname']
            pay_time = order['pay_time']
            backer_money = order['backer_money']

            oid = uuid.uuid3(uuid.NAMESPACE_OID, str(user_id) + pay_time)
            my_logger.debug('oid: %s', oid)
            my_logger.debug('size of order %s queue: %s', modian_entity.pro_id, len(self.order_queues[modian_entity.pro_id]))
            if oid in self.order_queues[modian_entity.pro_id]:
                continue

            msg = '感谢 %s 支持了%s元, %s\n' % (nickname, backer_money, util.random_str(global_config.MODIAN_POSTSCRIPTS))
            daka_rank, support_days = self.find_user_daka_rank(self.daka_rank_list, nickname)

            if support_days:
                msg += '当前项目已打卡%s天\n' % support_days
            
            # 集福
            # fu_switch = True #集福开关
            # fu_rate = [22,22,22,22,11,1] #五福概率，可调，合计需为100
            # fu_list = ['爱国福', '富强福', '和谐福', '友善福', '敬业福', '五福礼包']
            # fu_num = [0,0,0,0,0,0]
            # full_percentage = 0
            # result_list = []
            # drafts = 0
            # fu_result_str = ''
            #
            # for item in fu_rate:
            #     full_percentage += item
            # if not (full_percentage == 100):
            #     raise RuntimeError('概率设置错误')
            # else:
            #     if backer_money < 10.17:
            #         result_list = None
            #         pass
            #     else:
            #         drafts = int(backer_money // 10)
            #
            #         for i in range(0,drafts):
            #             start = 0
            #             rand = random.randint(1,sum(fu_rate))
            #             for index, item in enumerate(fu_rate):
            #                 start += item
            #                 if rand <= start:
            #                     break
            #             result_list.append((fu_list[index]))
            #
            # if result_list == None:
            #     pass
            # else:
            #     fu_result_str = '\n恭喜抽到 '
            #     for item in result_list:
            #         if item == '爱国福':
            #             fu_num[0] += 1
            #         if item == '富强福':
            #             fu_num[1] += 1
            #         if item == '和谐福':
            #             fu_num[2] += 1
            #         if item == '友善福':
            #             fu_num[3] += 1
            #         if item == '敬业福':
            #             fu_num[4] += 1
            #         if item == '五福礼包':
            #             fu_num[5] += 1
            #
            #     for index in range(0,6):
            #         if fu_num[index] == 0:
            #             pass
            #         else:
            #             fu_result_str += '%s*%s ' % (fu_list[index], str(fu_num[index]))
            #     fu_result_str += '~'
            # 集福结束

            # 接棒相关
            my_logger.debug('接棒情况更新')

            for jiebang in jiebang_activities:
                my_logger.debug('接棒活动详情: 【%s】', jiebang.name)
                my_logger.debug('集资金额: %s, 接棒最小金额: %s', backer_money, jiebang.min_stick_amount)
                if backer_money >= jiebang.min_stick_amount:
                    stick_num = util.compute_stick_num(jiebang.min_stick_amount, backer_money)
                    jiebang.current_stick_num += stick_num
                    
                    jiebang.last_record_time = util.convert_timestamp_to_timestr(time.time()*1000)
                    test_msg = '接棒活动: 【%s】, 当前第%s棒, 目标%s棒\n' \
                               % (jiebang.name, jiebang.current_stick_num, jiebang.target_stick_num)
                    my_logger.debug(test_msg)
                    if len(test_msg) > 0:
                        msg += test_msg
                        QQHandler.send_to_groups(['483548995'], test_msg)

            # flag相关
            my_logger.debug('flag情况更新')
            flag_test_msgs = ''
            for flag in flag_activities:
                my_logger.debug('Flag活动详情: %s', flag.name)
                my_logger.debug('Flag金额: %s, 结束时间: %s', flag.target_flag_amount, flag.end_time)
                diff = flag.target_flag_amount - current
                test_msgs = 'Flag活动名称: 【%s】, 目标金额: %s元, ' % (flag.name, flag.target_flag_amount)
                if diff > 0:
                    test_msgs += '距离目标还差%s元，继续加油！\n' % round(diff, 2)
                    flag_test_msgs += test_msgs
                else:
                    test_msgs += '已经达成目标，干得漂亮~'
            my_logger.debug(flag_test_msgs)
            if len(flag_test_msgs) > 0:
                # QQHandler.send_to_groups(['483548995'], flag_test_msgs)
                msg += flag_test_msgs
            
            if modian_entity.need_display_rank is True:
                jizi_rank, backer_money = self.find_user_jizi_rank(self.jizi_rank_list, nickname)
                msg += '当前项目已集资%s元, 排名: %s' % (backer_money, jizi_rank)
            else:
                pass
            msg += '%s\n集资项目: %s\n链接: %s' % (project_info, pro_name, modian_entity.link)
            
            # 集福播报
            # if fu_switch:
            #     msg += fu_result_str
            # else:
            #     pass

            # 抽卡播报
            cards_msg = ''
            if global_config.MODIAN_CARD_DRAW:
                cards_msg += '恭喜抽中'
                cards = self.card_draw_handler.draw(user_id, nickname, backer_money, pay_time)
                for k, v in cards.items():
                    cards_msg += '%s*%d,' % (k.name, v)
                my_logger.debug(cards_msg)
                cards_msg = cards_msg[:-1] + '\n'
                # 加上图片
                if global_config.USING_COOLQ_PRO is True:
                    for k, v in cards.items():
                        cards_msg += '[CQ:image,file=%s]' % k.url
                if cards_msg:
                    msg += '\n%s' % cards_msg
                # if cards_msg:
                #     QQHandler.send_to_groups(['483548995'], cards_msg)

            my_logger.info(msg)
            # if global_config.USING_COOLQ_PRO is True and cards_img_msg:
            #     my_logger.debug('使用酷Q PRO发送图片')
            #     msg +=  cards_img_msg
            QQHandler.send_to_groups(self.modian_notify_groups, msg)
            self.order_queues[modian_entity.pro_id].add(oid)

        # 更新接棒的数据库
        conn = sqlite3.connect('data/modian.db', check_same_thread=False)
        cursor = conn.cursor()
        try:
            my_logger.debug('更新接棒活动信息:')
            for jiebang in jiebang_activities:
                my_logger.debug('current_stick_num: %s, last_record_time: %s, name: %s',
                                jiebang.current_stick_num, jiebang.last_record_time, jiebang.name)
                cursor.execute("""
                    UPDATE jiebang SET current_stick_num=?, last_record_time=? WHERE name=?
                """, (jiebang.current_stick_num, jiebang.last_record_time, jiebang.name))

        except Exception as e:
            my_logger.error(e)
        finally:
            conn.commit()
            cursor.close()
            conn.close()

    def get_ranking_list(self, modian_entity, type0=1):
        """
        获取排名所有的列表
        :param modian_entity:
        :param type0: 1为集资，2为打卡
        :return:
        """
        ranking_list = []
        page = 1
        while True:
            rank_page = self.get_modian_rankings(modian_entity, type0, page)
            if len(rank_page) > 0:
                ranking_list.extend(rank_page)
                page += 1
            else:
                return ranking_list

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
        api = 'https://wds.modian.com/api/project/rankings'
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
        elif int(r['status'] == 2):
            return []
        else:
            raise RuntimeError('获取项目排名失败, type=%d', type0)

    def find_user_jizi_rank(self, ranking_list, user_name):
        """
        在集资榜中找到用户的排名
        :param ranking_list:
        :param user_name:
        :return:
        """
        my_logger.info('找到用户名为%s的集资排名', user_name)
        for rank in ranking_list:
            if 'backer_money' in rank.keys() and rank['nickname'] == user_name:
                return rank['rank'], rank['backer_money']
        return None, None

    def find_user_daka_rank(self, ranking_list, user_name):
        """
        在打卡榜中找到用户的排名
        :param ranking_list:
        :param user_name:
        :return:
        """
        my_logger.info('找到用户名为%s的打卡排名', user_name)
        for rank in ranking_list:
            if 'support_days' in rank.keys() and rank['nickname'] == user_name:
                return rank['rank'], rank['support_days']
        return None, None

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
        my_logger.debug('post_fields: %s', post_fields)
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
    user_id = '123456'
    back_time = '2018-02-28 12:00'
    oid = uuid.uuid3(uuid.NAMESPACE_OID, user_id+back_time)
    oid2 = uuid.uuid3(uuid.NAMESPACE_OID, user_id+back_time)

    print(oid == oid2)

    global_config.MODIAN_POSTSCRIPTS = ['123', '333']
    modian1 = ModianEntity('https://zhongchou.modian.com/item/10358.html', 'SNH48江真仪生日应援集资1.0',
                           10358)
    modian2 = ModianEntity('https://zhongchou.modian.com/item/10506.html', 'SNH48-洪珮雲17岁生诞集资2.0',
                           10506)
    arrays = [modian1, modian2]
    modian_handler = ModianHandler(['483548995'], arrays)
    modian_handler.jizi_rank_list = modian_handler.get_ranking_list(modian1, 1)
    time.sleep(5)
    modian_handler.daka_rank_list = modian_handler.get_ranking_list(modian1, 2)
    orders = modian_handler.query_project_orders(modian1)
    modian_handler.parse_order_details(orders, modian1)
    #
    # orders2 = modian_handler.query_project_orders(modian2)
    # modian_handler.parse_order_details(orders2, modian2)
    #
    # sorted(arrays, key=lambda x: x.current, reverse=True)
    # pass
    # modian_handler.get_current_and_target(modian1)
    modian_handler.get_modian_rankings(modian1, 2, page=1)
