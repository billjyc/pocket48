# -*- coding:utf-8 -*-
"""
摩点API文档地址：https://www.showdoc.cc/1702718?page_id=15700669
"""

import hashlib
import time
import urllib.parse
import uuid

import requests

from log.my_logger import modian_logger as my_logger
from modian.modian_card_draw import CardDrawHandler
from qq.qqhandler import QQHandler
from utils import global_config, util
from utils.mysql_util import mysql_util


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
                 min_stick_amount, need_detail):
        self.name = name
        self.pro_id = pro_id
        self.current_stick_num = current_stick_num
        self.last_record_time = last_record_time
        self.start_time = start_time
        self.end_time = end_time
        self.target_stick_num = target_stick_num
        self.min_stick_amount = min_stick_amount
        self.need_detail = need_detail


class ModianFlagEntity:
    def __init__(self, name, pro_id, target_flag_amount, end_time, remark):
        self.name = name
        self.pro_id = pro_id
        self.target_flag_amount = target_flag_amount
        self.end_time = end_time
        self.remark = remark


class ModianCountFlagEntity:
    def __init__(self, name, pro_id, target_flag_amount, start_time, end_time, remark):
        self.name = name
        self.pro_id = pro_id
        self.target_flag_amount = target_flag_amount
        self.start_time = start_time
        self.end_time = end_time
        self.remark = remark


class ModianHandler:
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'instance'):
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, modian_notify_groups, modian_project_array):
        self.session = requests.session()
        self.modian_notify_groups = modian_notify_groups
        self.modian_project_array = modian_project_array

        # self.jizi_rank_list = []
        # self.daka_rank_list = []

        self.card_draw_handler = CardDrawHandler()
        self.order_queues = {}

        # self.mysql_util = MySQLUtil()

        # self.init_order_queues()

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
                # self.order_queues[modian_entity.pro_id] = set()
                my_logger.debug('项目%s队列长度: %s', modian_entity.pro_id, len(self.order_queues[modian_entity.pro_id]))
                orders = self.query_project_orders(modian_entity)
                # retry_time = 0
                # while retry_time < 5:
                #     retry_time += 1
                #     if len(orders) == 0:
                #         my_logger.debug('请求订单失败，第%s次重试', retry_time)
                #         orders = self.query_project_orders(modian_entity)
                #     else:
                #         break

                for order in orders:
                    user_id = order['user_id']
                    pay_time = order['pay_time']

                    oid = uuid.uuid3(uuid.NAMESPACE_OID, str(user_id) + pay_time)
                    self.order_queues[modian_entity.pro_id].add(oid)
            except Exception as e:
                my_logger.error('初始化订单队列失败！')
                my_logger.exception(e)

        # self.current_available_seats = modian_300_performance_handler.get_current_available_seats()
        # # self.current_standing_seats_num = modian_300_performance_handler.get_current_standing_num()
        # self.current_wanneng_num = modian_300_performance_handler.get_current_wanneng_num()
        # self.current_available_standings = modian_300_performance_handler.get_current_available_standings()

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
        jiebang_activities = global_config.MODIAN_JIEBANG_ACTIVITIES[modian_entity.pro_id]
        flag_activities = global_config.MODIAN_FLAG_ACTIVITIES[modian_entity.pro_id]
        count_flag_activities = global_config.MODIAN_COUNT_FLAG_ACTIVITIES[modian_entity.pro_id]

        # 查询集资情况
        target, current, pro_name = self.get_current_and_target(modian_entity)
        project_info = '当前进度: %s元, 目标金额: %s元' % (current, target)

        modian_entity.current = current
        modian_entity.title = pro_name
        modian_entity.target = target
        # modian_entity.support_num = len(self.jizi_rank_list)
        my_logger.debug('size of order %s queue: %s', modian_entity.pro_id,
                        len(self.order_queues[modian_entity.pro_id]))

        for order in orders:
            user_id = order['user_id']
            nickname = order['nickname']
            pay_time = order['pay_time']
            backer_money = order['backer_money']

            oid = uuid.uuid3(uuid.NAMESPACE_OID, str(user_id) + pay_time)
            my_logger.debug('oid: %s', oid)

            if oid in self.order_queues[modian_entity.pro_id]:
                continue
            my_logger.debug('项目%s队列长度: %s', modian_entity.pro_id, len(self.order_queues[modian_entity.pro_id]))
            # 每次需要更新一下昵称
            mysql_util.query("""
                    INSERT INTO `supporter` (`id`, `name`) VALUES (%s, %s)  ON DUPLICATE KEY
                        UPDATE `name`=%s
                    """, (user_id, nickname, nickname))

            mysql_util.query("""
                INSERT INTO `order` (`id`,`supporter_id`,`backer_money`,`pay_time`, `pro_id`) 
                VALUES (%s, %s, %s, %s, %s) ON DUPLICATE KEY
                        UPDATE `id`=%s
            """, (str(oid), user_id, backer_money, pay_time, modian_entity.pro_id, str(oid)))

            # if modian_entity.pro_id == modian_pk_20180601_handler.WJL_PRO_ID:
            #     msg = '感谢 %s 支持了%s元\n' % (nickname, backer_money)
            # else:
            msg = '感谢 %s 支持了%s元, %s\n' % (nickname, backer_money, util.random_str(global_config.MODIAN_POSTSCRIPTS))
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
            rst = mysql_util.select_one("""
                                select count(distinct(`supporter_id`)) from `order` 
                                where `pro_id` = %s
                            """, (modian_entity.pro_id, ))
            if rst is not None:
                msg += '当前集资人数: %s\n' % rst[0]

            '''接棒相关'''
            my_logger.debug('接棒情况更新')
            for jiebang in jiebang_activities:
                my_logger.debug('接棒活动详情: 【%s】', jiebang.name)
                my_logger.debug('集资金额: %s, 接棒最小金额: %s', backer_money, jiebang.min_stick_amount)
                if backer_money >= jiebang.min_stick_amount:
                    stick_num = util.compute_stick_num(jiebang.min_stick_amount, backer_money)
                    jiebang.current_stick_num += stick_num
                    
                    # jiebang.last_record_time = util.convert_timestamp_to_timestr(time.time()*1000)
                    jiebang.last_record_time = int(time.time())
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
                    my_logger.debug(test_msg)
                    if len(test_msg) > 0:
                        # msg += test_msg
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

            # 抽卡播报
            cards_msg = ''
            if global_config.MODIAN_CARD_DRAW:
                cards = self.card_draw_handler.draw(user_id, nickname, backer_money, pay_time)
                if cards:
                    cards_msg += '恭喜抽中'
                    for k, v in cards.items():
                        cards_msg += '\"%s\"*%d,' % (k.name, v)
                    my_logger.debug(cards_msg)
                    cards_msg = cards_msg[:-1] + '，连词成句 试图中奖，start！\n'
                    # 加上图片
                    # if global_config.USING_COOLQ_PRO is True:
                    #     for k, v in cards.items():
                    #         cards_msg += '[CQ:image,file=%s]' % k.url
                else:
                    cards_msg += '没有抽中任何字，就送您一个“谢谢惠顾”吧'
                if cards_msg:
                    msg += '\n%s' % cards_msg
                # if cards_msg:
                #     QQHandler.send_to_groups(['483548995'], cards_msg)

            msg += '%s\n集资项目: %s\n链接: %s\n' % (project_info, pro_name, modian_entity.link)
            # msg += jizi_pk_report

            my_logger.info(msg)
            if global_config.USING_COOLQ_PRO is True:
                my_logger.debug('使用酷Q PRO发送图片')
                msg += '\n[CQ:image,file=http://wx1.sinaimg.cn/large/439a9f3fgy1fpllweknr6j201i01g0lz.jpg]'

            # if modian_entity.pro_id == modian_pk_handler.WJL_PRO_ID:
            #     QQHandler.send_to_groups(global_config.TEST_GROUPS, msg)
            # else:
            QQHandler.send_to_groups(self.modian_notify_groups, msg)
            self.order_queues[modian_entity.pro_id].add(oid)

        # 更新接棒的数据库
        # conn = sqlite3.connect('data/modian.db', check_same_thread=False)
        # cursor = conn.cursor()
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
        # finally:
        #     conn.commit()
        #     cursor.close()
        #     conn.close()

    def jizi_operation(self):
        pass

    def get_today_jizi_ranking_list(self, pro_id):
        """
        获取当日集资排名
        :param pro_id:
        :return: 排名tuple 格式（supporter_id, supporter_name, total_amount, rank)
        """
        # 总额
        rst2 = mysql_util.select_one("""
                    select SUM(`order`.backer_money) as total 
                    from `order`
                    where `order`.pro_id = %s
                        and CURDATE()=DATE(`order`.pay_time);
                """, (pro_id,))
        total = rst2[0]

        # 集资排名
        rst = mysql_util.select_all("""
            select `supporter`.id, `supporter`.name, SUM(`order`.backer_money) as total 
            from `order`, `supporter` 
            where `supporter`.id=`order`.supporter_id 
                and `order`.pro_id = %s
                and CURDATE()=DATE(`order`.pay_time) 
            group by `order`.supporter_id 
            order by total desc;
        """, (pro_id, ))
        cur_rank = 0
        row_tmp = 0
        last_val = -1
        new_rst = []
        for rank in rst:
            row_tmp += 1
            if rank[2] != last_val:
                cur_rank = row_tmp
            last_val = rank[2]
            rank_tmp = rank + (cur_rank, )
            new_rst.append(rank_tmp)
        my_logger.debug(new_rst)
        return new_rst, total

    def get_jizi_ranking_list(self, pro_id):
        """
        获取集资排名列表，从本地获取
        :param pro_id: 项目id
        :return:
        """
        rst = mysql_util.select_all("""
            select supporter_id, sum(backer_money) as total from `order` where pro_id=%s group by supporter_id order by total desc;
        """, (pro_id, ))
        return rst

    # def get_ranking_list(self, modian_entity, type0=1):
    #     """
    #     获取排名所有的列表
    #     :param modian_entity:
    #     :param type0: 1为集资，2为打卡
    #     :return:
    #     """
    #     ranking_list = []
    #     page = 1
    #     while True:
    #         rank_page = self.get_modian_rankings(modian_entity, type0, page)
    #         if len(rank_page) > 0:
    #             ranking_list.extend(rank_page)
    #             page += 1
    #         else:
    #             return ranking_list

    def get_modian_rankings(self, modian_entity, type0=1, page=1):
        """
        查询项目集资榜和打卡榜
        :param type0: 排名类型，1代表集资榜，2代表打卡榜
        :param modian_entity:
        :param page: 页号，每页默认返回20条
        :return:
        """
        if type0 == 1:
            my_logger.info('查询项目集资榜, page=%s', page)
        elif type0 == 2:
            my_logger.info('查询项目打卡榜, page=%s', page)
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
            # my_logger.info('查询项目排名: %s', rankings)
            return rankings
        elif int(r['status'] == 2):
            return []
        else:
            raise RuntimeError('获取项目排名失败, type=%d', type0)

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
                    from `order` where pro_id=13566 group by supporter_id order by c desc;
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
        """, (pro_id, ))
        cur_rank = 0
        for temp_id, days in ranking_list:
            cur_rank += 1
            if temp_id == user_id:
                return cur_rank, days
        return -1, -1

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

    def get_all_orders(self, modian_entity):
        """
        获取全部订单
        :return:
        """
        orders = []
        page = 1
        while True:
            sub_orders = self.query_project_orders(modian_entity, page)
            if len(sub_orders) > 0:
                orders.extend(sub_orders)
                page += 1
            else:
                break
        return orders


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
