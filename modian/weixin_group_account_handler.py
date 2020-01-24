# -*- coding:utf-8 -*-
"""
微信小经费
"""

import json
import logging
import time

import requests

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)

from modian.modian_card_draw import handler as card_draw_handler
from urllib.parse import unquote
from modian.special import modian_wufu_handler
from qq.qqhandler import QQHandler
from utils import global_config, util
from utils.mysql_util import mysql_util


class GroupAccountEntity:
    def __init__(self, link, title, group_account_id, broadcast_groups=[], qrcode='', current=0.0, support_num=0):
        self.link = link
        self.title = title
        self.group_account_id = group_account_id
        # self.need_display_rank = need_display_rank
        self.broadcast_groups = broadcast_groups
        self.qrcode = qrcode
        self.current = current
        # self.target = target
        self.support_num = support_num


class WeixinGroupAccountHandler:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, group_account_notify_groups, group_account_project_array):
        self.session = requests.session()
        self.group_account_notify_groups = group_account_notify_groups
        self.group_account_project_array = group_account_project_array

        self.card_draw_handler = card_draw_handler
        self.order_queues = {}

    def init_order_queues(self):
        for group_account_entity in self.group_account_project_array:
            try:
                my_logger.info('初始化%s的订单队列', group_account_entity.group_account_id)
                my_logger.debug(self.order_queues)
                if group_account_entity.group_account_id not in self.order_queues:
                    self.order_queues[group_account_entity.group_account_id] = set()
                    my_logger.debug('队列为空，重新初始化队列')
                else:
                    my_logger.debug('队列不为空，不重新初始化队列')
                    continue
                my_logger.debug('项目%s队列长度: %s', group_account_entity.group_account_id,
                                len(self.order_queues[group_account_entity.group_account_id]))

                orders = self.query_project_orders(group_account_entity)

                for order in orders:
                    listid = int(order['listid'])
                    self.order_queues[group_account_entity.group_account_id].add(listid)
            except Exception as e:
                my_logger.error('初始化订单队列失败！')
                my_logger.exception(e)

    def weixin_header(self):
        """
        header信息
        """
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cookie': 'grp_qlskey=v0ae789cc115e00b0a1c1ca186f09b45;grp_qluin=91be027df85334c678b99fe50566e8eb',  # cookie要换成自己的
            'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/7.0.8(0x17000820) NetType/WIFI Language/zh_CN',
        }
        return header

    def query_project_orders(self, group_account_entity, page=1, limit=10):
        """
        批量获取订单
        :param group_account_entity:
        :param page:
        :param limit:
        :return:
        """
        my_logger.info('查询项目订单, id: %s', group_account_entity.group_account_id)
        url = 'https://groupaccount.tenpay.com/fcgi-bin/grp_qry_group_water.fcgi'
        data = {
            "group_account_id": group_account_entity.group_account_id,
            "start_time": '2017-01-01 00:00:00',
            "end_time": '2100-01-31 00:00:00',
            "qry_ver": 1,
            "lastbkid": '',
            "offset": page - 1,
            "limit": limit,
            "type": 2,
            "target_unionid": ""
        }
        r = self.session.post(url=url, data=data, headers=self.weixin_header()).json()
        if int(r['retcode']) != 0:
            raise RuntimeError('获取订单信息失败')
        orders = json.loads(unquote(r['water_array']))
        my_logger.info('项目订单: page: %s, orders: %s', page, orders)
        return orders['water_array']

    def get_current_and_target(self, group_account_entity):
        """
        查询当前项目情况
        :param group_account_entity:
        :return:
        """
        my_logger.info('获取当前进度和总额: pro_id: %s', group_account_entity.group_account_id)
        api = 'https://groupaccount.tenpay.com/fcgi-bin/grp_qry_group_info.fcgi'
        data = {
            "group_account_id": group_account_entity.group_account_id
        }
        r = self.session.post(api, data=data, headers=self.weixin_header()).json()
        if int(r['retcode']) == 0:
            name = r['name']
            current = float(r['balance']) / 100
            user_num = r['user_num']
            my_logger.info('支持人数: %s, 当前进度: %s', user_num, current)
            return name, current, user_num
        else:
            raise RuntimeError('获取项目筹款结果查询失败')

    def parse_order_details(self, orders, group_account_entity):
        if len(self.order_queues[group_account_entity.group_account_id]) == 0 and len(orders) == 0:
            my_logger.debug('订单队列为空')
            return
        jiebang_activities = global_config.MODIAN_JIEBANG_ACTIVITIES[group_account_entity.group_account_id]
        flag_activities = global_config.MODIAN_FLAG_ACTIVITIES[group_account_entity.group_account_id]
        count_flag_activities = global_config.MODIAN_COUNT_FLAG_ACTIVITIES[group_account_entity.group_account_id]

        # 查询集资情况
        pro_name, current, backer_count = self.get_current_and_target(group_account_entity)
        project_info = '当前进度: %s元' % current

        group_account_entity.current = current
        group_account_entity.title = pro_name
        # group_account_entity.target = target
        group_account_entity.support_num = backer_count
        my_logger.debug('size of order %s queue: %s', group_account_entity.group_account_id,
                        len(self.order_queues[group_account_entity.group_account_id]))

        for order in orders:
            if 'remark' in order.keys():
                user_id = order['remark']
                nickname = order['remark']
            else:
                user_id = order['nickname']
                nickname = order['nickname']
            pay_time = order['time']
            backer_money = float(order['fee']) / 100
            listid = int(order['listid'])

            my_logger.debug('oid: %s', listid)

            if listid in self.order_queues[group_account_entity.group_account_id]:
                continue
            my_logger.debug('项目%s队列长度: %s', group_account_entity.group_account_id,
                            len(self.order_queues[group_account_entity.group_account_id]))

            # 每次需要更新一下昵称
            try:
                mysql_util.query("""
                                        INSERT INTO `supporter` (`id`, `name`) VALUES (%s, %s)  ON DUPLICATE KEY
                                            UPDATE `name`=%s
                                        """, (user_id, nickname, nickname))
            except Exception as e:
                my_logger.exception(e)

            try:
                # 创建对象
                mysql_util.query("""
                                    INSERT INTO `order` (`id`,`supporter_id`,`backer_money`,`pay_time`, `pro_id`) 
                                    VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY
                                            UPDATE `id`=%s
                                """, (str(listid), user_id, backer_money, pay_time, group_account_entity.group_account_id, str(listid)))
            except Exception as e:
                my_logger.exception(e)

            msg = '感谢 %s(%s) 支持了%s元, %s\n' % (
                nickname, user_id, backer_money, util.random_str(global_config.MODIAN_POSTSCRIPTS))
            # daka_rank, support_days = self.find_user_daka_rank(user_id, group_account_entity.pro_id)

            # if daka_rank != -1 and support_days:
            #     msg += '当前项目已打卡%s天\n' % support_days

            # if group_account_entity.need_display_rank is True:
            #     jizi_rank, backer_money = self.find_user_jizi_rank(user_id, group_account_entity.pro_id)
            #     if jizi_rank != -1:
            #         msg += '当前项目已集资%s元, 排名: %s' % (backer_money, jizi_rank)
            # else:
            #     pass

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
                """, (group_account_entity.group_account_id, flag.end_time, flag.start_time))

                # 目标人数为0，代表特殊类flag，只报人数
                if target == 0:
                    count_flag_test_msgs += '【%s】, 当前人数: %s ' % (flag.name, rst[0])
                else:
                    count_flag_test_msgs += '【%s】, 当前人数: %s, 目标人数: %s ' % (flag.name, rst[0], flag.target_flag_amount)

            my_logger.debug(count_flag_test_msgs)
            if len(count_flag_test_msgs) > 0:
                QQHandler.send_to_groups(['483548995'], count_flag_test_msgs)
                # msg += flag_test_msgs

            msg += '%s\n集资项目: %s\n集资方式: %s\n' % (project_info, pro_name, group_account_entity.link)
            # msg += jizi_pk_report

            my_logger.info(msg)
            if global_config.USING_COOLQ_PRO is True:
                my_logger.debug('使用酷Q PRO发送图片')
                msg += '\n[CQ:image,file={}]\n'.format(group_account_entity.qrcode)

            # if global_config.MODIAN_NEED_DISPLAY_PK:
            #     msg += self.pk_modian_activity()

            QQHandler.send_to_groups(group_account_entity.broadcast_groups, msg)
            if card_report:
                QQHandler.send_to_groups(group_account_entity.broadcast_groups, card_report)
                # QQHandler.send_to_groups(['483548995'], card_report)

            # 集五福
            wufu_report = modian_wufu_handler.draw(user_id, nickname, backer_money, pay_time)
            if wufu_report:
                QQHandler.send_to_groups(group_account_entity.broadcast_groups, wufu_report)

            self.order_queues[group_account_entity.group_account_id].add(listid)

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

        # self.alchemy_session.commit()
        # finally:
        #     conn.commit()
        #     cursor.close()
        #     conn.close()


if __name__ == "__main__":
    entity = GroupAccountEntity('ssss', '400场', '4mr9Xz920100009000043331')
    handler = WeixinGroupAccountHandler([], [entity])
    handler.init_order_queues()
    # orders = handler.query_project_orders(entity)

