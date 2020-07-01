# -*- coding:utf-8 -*-
"""
微信小经费
"""

import json
import logging
import time
import zlib
import base64

import requests

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)

from modian.modian_card_draw import handler as card_draw_handler
from urllib.parse import unquote
from qq.qqhandler import QQHandler
from utils import global_config, util
from utils.mysql_util import mysql_util


class TaoBaEntity:
    def __init__(self, link, title, taoba_id, broadcast_groups=[], qrcode='', current=0.0, support_num=0):
        self.link = link
        self.title = title
        self.taoba_id = taoba_id
        # self.need_display_rank = need_display_rank
        self.broadcast_groups = broadcast_groups
        self.qrcode = qrcode
        self.current = current
        # self.target = target
        self.support_num = support_num
        self.pk_group = None


class TaoBaAccountHandler:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, taoba_notify_groups, taoba_project_array):
        self.session = requests.session()
        self.taoba_notify_groups = taoba_notify_groups
        self.taoba_project_array = taoba_project_array

        self.card_draw_handler = card_draw_handler
        self.order_queues = {}
        self.token = 0

    def init_order_queues(self):
        for taoba_entity in self.taoba_project_array:
            try:
                my_logger.info('初始化%s的订单队列', taoba_entity.taoba_id)
                my_logger.debug(self.order_queues)
                if taoba_entity.taoba_id not in self.order_queues:
                    self.order_queues[taoba_entity.taoba_id] = set()
                    my_logger.debug('队列为空，重新初始化队列')
                else:
                    my_logger.debug('队列不为空，不重新初始化队列')
                    continue
                my_logger.debug('项目%s队列长度: %s', taoba_entity.taoba_id,
                                len(self.order_queues[taoba_entity.taoba_id]))

                orders = self.query_project_orders(taoba_entity)

                for order in orders:
                    listid = int(order['id'])
                    self.order_queues[taoba_entity.taoba_id].add(listid)
            except Exception as e:
                my_logger.error('初始化订单队列失败！')
                my_logger.exception(e)

    def taoba_header(self):
        """
        header信息
        """
        header = {
            'Content-Type': 'application/json',
            'SIGNATURE': self.token,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        }
        return header

    def query_project_orders(self, taoba_entity, page=1, limit=10):
        """
        批量获取订单
        :param taoba_entity:
        :param page:
        :param limit:
        :return:
        """
        all_orders = []
        my_logger.info('查询项目订单, id: %s', taoba_entity.taoba_id)
        url = 'https://www.tao-ba.club/idols/refund/orders'
        page = 0
        while True:
            data = {'id': taoba_entity.taoba_id, 'offset': page * 25, 'ismore': False, 'requestTime': int(time.time() * 1000),
                    'pf': 'h5'}
            my_logger.info('taoba token: {}'.format(self.token))
            my_logger.debug('data: {}'.format(data))
            my_logger.debug('data: {}'.format(self.encrypt(data)))
            my_logger.debug('header: {}'.format(self.taoba_header()))
            r = self.session.post(url=url, data=self.encrypt(data), headers=self.taoba_header())
            r = self.decrypt(r.text)

            if int(r['code']) != 0:
                raise RuntimeError('获取订单信息失败')
            orders = r['list']
            my_logger.info('项目订单: page: %s, orders: %s, len: %s', page + 1, orders, len(orders))
            if not orders:
                break
            all_orders.extend(orders)
            page += 1
        return all_orders

    def get_current_and_target(self, taoba_entity):
        """
        查询当前项目情况
        :param taoba_entity:
        :return:
        """
        my_logger.info('获取当前进度和总额: pro_id: %s', taoba_entity.taoba_id)
        api = 'https://www.tao-ba.club/idols/detail'
        data = {'id': taoba_entity.taoba_id, 'requestTime': int(time.time() * 1000), 'pf': 'h5'}
        r = self.session.post(api, data=self.encrypt(data), headers=self.taoba_header())
        r = self.decrypt(r.text)
        if int(r['code']) == 0:
            name = r['datas']['title']
            current = r['datas']['donation']
            # user_num = r['user_num']
            if 'pkgroup' in r['datas'].keys() and r['datas']['pkgroup']:
                taoba_entity.pk_group = r['datas']['pkgroup']
            user_num = 0
            my_logger.info('支持人数: %s, 当前进度: %s', user_num, current)
            return name, current, user_num
        else:
            raise RuntimeError('获取项目筹款结果查询失败')

    def get_pk_group(self, pk_group):
        """
        获取PK情况
        :param pk_group:
        :return:
        """
        my_logger.info('获取PK战况，pk group id: {}'.format(pk_group))
        api = 'https://www.tao-ba.club/idols/pkgroup/pkstats'
        data = {'pkgroup': pk_group, 'requestTime': int(time.time() * 1000), '_version_': 1, 'pf': 'h5'}
        r = self.session.post(api, data=self.encrypt(data), headers=self.taoba_header())
        r = self.decrypt(r.text)
        if int(r['code']) == 0:
            return r['list']
        else:
            return []


    def parse_order_details(self, orders, taoba_entity):
        my_logger.debug('taoba_entity: {}'.format(taoba_entity.taoba_id))
        my_logger.debug('keys: {}'.format(self.order_queues.keys()))
        if len(self.order_queues[taoba_entity.taoba_id]) == 0 and len(orders) == 0:
            my_logger.debug('订单队列为空')
            return
        jiebang_activities = global_config.MODIAN_JIEBANG_ACTIVITIES[taoba_entity.taoba_id]
        flag_activities = global_config.MODIAN_FLAG_ACTIVITIES[taoba_entity.taoba_id]
        count_flag_activities = global_config.MODIAN_COUNT_FLAG_ACTIVITIES[taoba_entity.taoba_id]

        # 查询集资情况
        pro_name, current, backer_count = self.get_current_and_target(taoba_entity)
        project_info = '当前进度: %s元' % current

        taoba_entity.current = current
        taoba_entity.title = pro_name
        # group_account_entity.target = target
        taoba_entity.support_num = backer_count
        my_logger.debug('size of order %s queue: %s', taoba_entity.taoba_id,
                        len(self.order_queues[taoba_entity.taoba_id]))

        for order in orders:
            user_id = order['userid']
            nickname = order['nickname']
            pay_time = util.convert_timestamp_to_timestr(order['addtime'] * 1000)

            single_price = order['amount']
            pay_amount = order['nums']

            backer_money = single_price
            listid = int(order['id'])

            my_logger.debug('oid: %s', listid)

            if listid in self.order_queues[taoba_entity.taoba_id]:
                continue
            my_logger.debug('项目%s队列长度: %s', taoba_entity.taoba_id,
                            len(self.order_queues[taoba_entity.taoba_id]))

            # 每次需要更新一下昵称
            try:
                mysql_util.query("""
                                        INSERT INTO `supporter` (`id`, `name`) VALUES (%s, %s)  ON DUPLICATE KEY
                                            UPDATE `id`=%s
                                        """, (user_id, nickname, user_id))
            except Exception as e:
                my_logger.exception(e)

            try:
                # 创建对象
                mysql_util.query("""
                                    INSERT INTO `order` (`id`,`supporter_id`,`backer_money`,`pay_time`, `pro_id`) 
                                    VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY
                                            UPDATE `id`=%s
                                """, (str(listid), user_id, backer_money, pay_time, taoba_entity.taoba_id, str(listid)))
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
            count = mysql_util.select_one("""
                SELECT COUNT(distinct(`supporter_id`)) FROM `order` WHERE `pro_id`=%s
            """, (taoba_entity.taoba_id, ))
            backer_count = count[0]
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
                """, (taoba_entity.taoba_id, flag.end_time, flag.start_time))

                # 目标人数为0，代表特殊类flag，只报人数
                if target == 0:
                    count_flag_test_msgs += '【%s】, 当前人数: %s ' % (flag.name, rst[0])
                else:
                    count_flag_test_msgs += '【%s】, 当前人数: %s, 目标人数: %s ' % (flag.name, rst[0], flag.target_flag_amount)

            my_logger.debug(count_flag_test_msgs)
            if len(count_flag_test_msgs) > 0:
                QQHandler.send_to_groups(['483548995'], count_flag_test_msgs)
                # msg += flag_test_msgs

            msg += '%s\n集资项目: %s\n集资方式: %s\n' % (project_info, pro_name, taoba_entity.link)
            # msg += jizi_pk_report

            my_logger.info(msg)
            if global_config.USING_COOLQ_PRO is True:
                my_logger.debug('使用酷Q PRO发送图片')
                msg += '\n[CQ:image,file={}]\n'.format(taoba_entity.qrcode)

            # if global_config.MODIAN_NEED_DISPLAY_PK:
            #     msg += self.pk_modian_activity()

            QQHandler.send_to_groups(taoba_entity.broadcast_groups, msg)
            if card_report:
                QQHandler.send_to_groups(taoba_entity.broadcast_groups, card_report)
                # QQHandler.send_to_groups(['483548995'], card_report)

            # 集五福
            # wufu_report = modian_wufu_handler.draw(user_id, nickname, backer_money, pay_time)
            # if wufu_report:
            #     QQHandler.send_to_groups(group_account_entity.broadcast_groups, wufu_report)

            self.order_queues[taoba_entity.taoba_id].add(listid)

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

    def decrypt(self, response):
        """
        对加密的response进行解密
        :return:
        """
        my_logger.info('对加密的response进行解密')
        my_logger.info('1. 分离出base64字符串')
        response_arr = response.split('$', 2)
        if len(response_arr) < 2:
            raise RuntimeError('response格式错误')
        base64_res = response_arr[1]
        my_logger.info('2. base64解码')
        base64_res = base64.b64decode(base64_res)
        my_logger.info('3. 对字符串进行进一步处理')
        res = self.process(base64_res)
        my_logger.info('4. 对处理结果进行zlib解压缩')
        res = zlib.decompress(res)
        return json.loads(str(res, encoding='utf-8'))

    def encrypt(self, request):
        """
        对request进行加密
        :param request:
        :return:
        """
        my_logger.info('对request进行加密')
        my_logger.info('1. 对字符串进行zlib压缩')
        res_str = json.dumps(request).strip()
        res = zlib.compress(bytes(res_str, encoding='utf-8'))
        my_logger.info('2. 对字符串进行处理')
        res = self.process(res)
        my_logger.info('3. base64编码')
        res = base64.b64encode(res)
        my_logger.info('4. 组装字符串')
        res = str(len(res_str)) + '$' + str(res, encoding='utf-8')
        return res

    def process(self, byte_str):
        """
        桃叭对字符串独有的处理函数
        :param byte_str:
        :return:
        """
        o = "%#54$^%&SDF^A*52#@7"
        n = bytes(o * 3, encoding='utf-8')
        t = b""
        i = 0
        for l in range(len(byte_str)):
            a = byte_str[l]
            if l % 2 == 0:
                index = i % len(o)
                a ^= n[index]
                i += 1
            t += a.to_bytes(length=1, signed=False, byteorder='big')
        return t

    def login(self, account, passwd):
        """
        登录，获取SIGNATURE
        :param account:
        :param passwd:
        :return:
        """
        url = 'https://www.tao-ba.club/signin/phone'
        data = {'account': account, 'pushid': '', 'loginpw': passwd,
                'device': {'platform': 'other', 'screen': '1680*1050', 'imei': 'XXX', 'uuid': 'YYY',
                           'version': 'v1.0.0', 'vendor': 'ZZZ'}, 'requestTime': int(time.time() * 1000), 'pf': 'h5'}
        header = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.122 Safari/537.36',
        }
        r = self.session.post(url, data=self.encrypt(data), headers=header)
        r = self.decrypt(r.text)
        if r['code'] == 0:
            my_logger.debug('登录成功')
            self.token = r['token']


if __name__ == "__main__":
    entity = TaoBaEntity('ssss', '400场', '1053')
    handler = TaoBaAccountHandler([], [entity])
    # handler.login('*', '*')
    # handler.init_order_queues()
    # print(handler.decrypt(
    #     '209$XZw+jnQOtzAoBKHiRoV2TEcI+KNB4NiCaJEKoTyhNcT8a/h5UFcGnxMY1pPvoSWUy9Q/q4QWw8HS4ipHmHxu/kndw+OCWOQYRVa7Rx+sAmh72KJhu3wGecT3vwLE0UAiMWsVLR8o/i2AK2tGTtsySN7xUl3k4ZUQmb/TB7giMg9Uo1xMvr7BK91AnkRbf4YEKFR5KtRFakpw8JQT2mYx1ztGaTy4'))
    # print(handler.decrypt(
    #     '111$XZxGyR4OtDA0BZ67iUaS76Z/37JrhtoaXeHENDGHKjW06ChdvVnBHFg/kQgZzcAnjjHkxTMIajjE9fEKpu1az26+8rmrIZWgXWpKqlCl/w/uyC6Z'))
    # print(handler.decrypt('1059$XZyWkApP9zA0xeHL6AG77aC/KExmJAY6cRAskw1q5jYujX1UYr8elwFAYCVgAXlOKU/ze1i/TtSvJgSJWyz6MWv5iYOcgXF6UpY9yEbcb7d1obEkc8DGQu8jDQX/Nwncyj3KcL4geyIf1PAJ93SzNBWRoAJxl6PsO1XyIupVE68Mfh1pyFY6WCo8NNTWKB/ej6lulR1D8w5m2IXtJQ+9YZHOI/p9mwB1+EmSTpcUk9+su1DRskm32cAd+auY2GaScK2pMgixhlrA1K/AP90Lzye9zs3fRN5XecFI8f/Cit/xUH+zRP7cLNGPGISfIFWJ24ijddXUXSxioeLt1+hiXrsFbAtYysMjuHhx2YFFQ22lo5mWsurOQMG0ROYz7XPhrjb+bNHT057Cb+5ftu9XIBbj'))
    #
    # print(handler.decrypt('61$XZyIVv/J+M0IUewyF9B3yhxLb05Dst/M49To0uHioJDv3BQlHEN2C0ATBgM/I1dDLUs4paQ0divhDBWlBAAHXDup'))
    print(handler.encrypt({'id': '1634', 'offset': 0, 'ismore': True, 'requestTime': int(time.time() * 1000), 'pf': 'h5'}))
    #
    rst = '4841$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'
    rst = handler.decrypt(rst)
    print(rst)
    # pk参数
    # {'pkgroup': '200624TVwh8e62', 'requestTime': 1593569363895, '_version_': 1, 'pf': 'h5'}
    # print(len(rst['list']))
