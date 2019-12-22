# -*- coding: utf-8 -*-

from log.my_logger import modian_logger as my_logger

from utils.config_reader import ConfigReader
from modian.modian_handler import ModianJiebangEntity, ModianFlagEntity, ModianCountFlagEntity
# from modian.modian_handler_bs4 import ModianHandlerBS4, ModianEntity
from modian.weixin_group_account_handler import GroupAccountEntity, WeixinGroupAccountHandler
from utils import global_config
# from qq.qqhandler import QQHandler
import uuid
import json
import time
from utils import util
from utils.mysql_util import mysql_util

from utils.scheduler import scheduler
from qq.qqhandler import QQHandler


# @scheduler.scheduled_job('cron', minute='*/15')
def update_modian_conf():
    global modian_handler
    time0 = time.time()
    my_logger.info('读取摩点配置')
    ConfigReader.read_conf()
    # modian_json = json.load(open("data/modian.json", encoding='utf8'))
    modian_json = json.load(open("data/weixin_group_account.json", encoding='utf8'))

    global_config.MODIAN_POSTSCRIPTS = modian_json['modian_postscripts']

    # 摩点集资PK链接数组初始化
    global_config.MODIAN_NEED_DISPLAY_PK = modian_json['modian_need_display_pk']

    for modian_pk_j in modian_json['modian_pk_activities']:
        global_config.MODIAN_PK_ARRAY.append(modian_pk_j)

    # 是否需要开启抽卡功能
    global_config.MODIAN_CARD_DRAW = modian_json['modian_need_card_draw']

    # global_config.MODIAN_300_ACTIVITY = modian_json['modian_300_activity']

    # 需要适应同时开多个链接的情况
    global_config.MODIAN_ARRAY = []

    for modian_j in modian_json['monitor_activities']:
        # if modian_j['modian_need_display_rank'] is False:
            # modian = ModianEntity(modian_j['modian_link'], modian_j['modian_title'], modian_j['modian_pro_id'], False,
            #                       modian_j['broadcast_groups'])
        modian = GroupAccountEntity(modian_j['modian_link'], modian_j['modian_title'], modian_j['modian_pro_id'],
                                    modian_j['broadcast_groups'], modian_j['qrcode'])
        # elif modian_j['wds_need_display_rank'] is True:
        #     modian = ModianEntity(modian_j['modian_link'], modian_j['modian_title'], modian_j['modian_pro_id'], True,
        #                           modian_j['broadcast_groups'])
        global_config.MODIAN_ARRAY.append(modian)

    modian_handler.group_account_project_array = global_config.MODIAN_ARRAY

    # modian_handler.init_order_queues()
    modian_handler.card_draw_handler.read_config()

    global_config.JIZI_NOTIFY_GROUPS = ConfigReader.get_property('qq_conf', 'jizi_notify_groups').split(';')
    modian_groups = global_config.JIZI_NOTIFY_GROUPS
    modian_handler.group_account_notify_groups = modian_groups

    my_logger.debug('JIZI_NOTIFY_GROUPS: %s, length: %d', ','.join(global_config.JIZI_NOTIFY_GROUPS),
                    len(modian_handler.group_account_notify_groups))

    my_logger.debug('读取正在进行中的flag活动')
    global_config.MODIAN_FLAG_ACTIVITIES = {}
    flag_json = json.load(open('data/modian_flag.json', encoding='utf8'))['activities']
    for modian in global_config.MODIAN_ARRAY:
        pro_id = modian.group_account_id
        global_config.MODIAN_FLAG_ACTIVITIES[pro_id] = []
    for activity in flag_json:
        pro_id = activity['pro_id']
        end_time = activity['end_time']
        if util.convert_timestr_to_timestamp(end_time) > time.time():
            flag = ModianFlagEntity(activity['flag_name'], activity['pro_id'], activity['target_flag_amount'],
                                    activity['end_time'], activity['remark'])
            global_config.MODIAN_FLAG_ACTIVITIES[int(pro_id)].append(flag)
    my_logger.debug('MODIAN_FLAG_ACTIVITIES: %s', global_config.MODIAN_FLAG_ACTIVITIES)

    my_logger.debug('读取正在进行的人头flag活动')
    global_config.MODIAN_COUNT_FLAG_ACTIVITIES = {}
    count_flag_json = json.load(open('data/modian_count_flag.json', encoding='utf8'))['activities']
    for modian in global_config.MODIAN_ARRAY:
        pro_id = modian.group_account_id
        global_config.MODIAN_COUNT_FLAG_ACTIVITIES[pro_id] = []
    for activity in count_flag_json:
        pro_id = activity['pro_id']
        start_time = activity['start_time']
        end_time = activity['end_time']
        if util.convert_timestr_to_timestamp(start_time) >= util.convert_timestr_to_timestamp(end_time):
            my_logger.error('人头类flag，起始时间大于结束时间！')
            raise RuntimeError('起始时间大于结束时间')
        time0 = time.time()
        if util.convert_timestr_to_timestamp(end_time) > time0 > util.convert_timestr_to_timestamp(start_time):
            flag = ModianCountFlagEntity(activity['flag_name'], activity['pro_id'], activity['target_flag_amount'],
                                    activity['start_time'], activity['end_time'], activity['remark'])
            global_config.MODIAN_COUNT_FLAG_ACTIVITIES[int(pro_id)].append(flag)
    my_logger.debug('MODIAN_COUNT_FLAG_ACTIVITIES: %s', global_config.MODIAN_COUNT_FLAG_ACTIVITIES)

    # 接棒活动更新，读取json文件中的内容，更新到数据库中
    my_logger.debug('接棒活动更新，读取json文件中的内容，更新到数据库中')
    jiebang_json = json.load(open('data/modian_jiebang.json', encoding='utf8'))['activities']
    # conn = sqlite3.connect('data/modian.db', check_same_thread=False)
    for activity in jiebang_json:
        end_time = activity['end_time']
        my_logger.debug('活动结束时间: {}; 当前时间：{}'.format(util.convert_timestr_to_timestamp(end_time),
                                                     time.time()))
        if util.convert_timestr_to_timestamp(end_time) < time.time():
            my_logger.debug('活动结束时间早于当前时间，跳过')
            continue
        name = activity['jiebang_name']
        try:
            # cursor = conn.cursor()
            # c = cursor.execute("""
            #     select * from jiebang WHERE name=?
            # """, (name, ))
            # rst = c.fetchall()
            rst = mysql_util.select_one("""
                select * from jiebang WHERE name=%s
            """, (name, ))
            my_logger.debug(rst)
            if rst is not None:
                my_logger.debug('DB中有相应的接棒活动')
            else:
                my_logger.debug('DB中没有对应的接棒活动，需要创建')
                mysql_util.query("""
                                    INSERT INTO jiebang (name, pro_id, current_stick_num, start_time, 
                                    end_time, target_stick_num, min_stick_amount, need_detail) VALUES
                                    (%s, %s, %s, %s, %s, %s, %s, %s)
                                """, (
                name, activity['pro_id'], 0,
                    activity['start_time'], activity['end_time'], activity['target_stick_num'],
                activity['min_stick_amount'], activity['need_detail']))
                # conn.commit()
            # else:
            #     raise RuntimeError('接棒活动名称错误！')
        except Exception as e:
            my_logger.error('读取mysql出现错误')
            my_logger.exception(e)
        # finally:
        #     cursor.close()

    # 读取正在进行中的接棒活动
    my_logger.debug('读取正在进行中的接棒活动')
    global_config.MODIAN_JIEBANG_ACTIVITIES = {}
    for modian in global_config.MODIAN_ARRAY:
        pro_id = modian.group_account_id
        global_config.MODIAN_JIEBANG_ACTIVITIES[pro_id] = []
        try:
            # cursor = conn.cursor()
            rst = mysql_util.select_all("""
                SELECT name, pro_id, current_stick_num, last_record_time, 
                    start_time, end_time, target_stick_num, min_stick_amount, need_detail
                FROM jiebang where pro_id=%s 
                    and end_time >= NOW() and current_stick_num < target_stick_num
            """, (pro_id, ))
            if rst:
                for jiebang in rst:
                    my_logger.debug('jiebang name: {}'.format(str(jiebang[0], encoding='utf-8')))
                    # 修正当前棒数
                    my_logger.info('修正接棒棒数')
                    real_stick_num = 0
                    rst0 = mysql_util.select_all("""
                                    SELECT backer_money FROM `order`
                                        WHERE pro_id = %s and backer_money >= %s and pay_time >= %s and pay_time <= %s
                                """, (pro_id, jiebang[7], jiebang[4], jiebang[5]))
                    my_logger.debug("""
                                    SELECT backer_money FROM `order`
                                        WHERE pro_id = %s and backer_money >= %s and pay_time >= %s and pay_time <= %s
                                """ % (pro_id, jiebang[7], jiebang[4], jiebang[5]))
                    my_logger.debug(rst0)
                    if rst0:
                        for order in rst0:
                            my_logger.debug('order: {}'.format(order[0]))
                            real_stick_num += int(order[0] // jiebang[7])

                    my_logger.info('记录棒数: {}, 实际棒数: {}'.format(jiebang[2], real_stick_num))
                    mysql_util.query("""
                        UPDATE jiebang SET current_stick_num = %s WHERE name = %s
                    """, (real_stick_num, jiebang[0]))

                    my_logger.debug('jiebang: %s, %s, %s, %s, %s, %s, %s, %s, %s',
                                    jiebang[0], jiebang[1], jiebang[2], jiebang[3], jiebang[4], jiebang[5],
                                                  jiebang[6], jiebang[7], jiebang[8])
                    jiebang_entity = ModianJiebangEntity(str(jiebang[0], encoding='utf-8'), jiebang[1], jiebang[2], jiebang[3], jiebang[4], jiebang[5],
                                                  jiebang[6], jiebang[7], jiebang[8])
                    jiebang_entity.current_stick_num = real_stick_num
                    my_logger.info('修正完成')
                    global_config.MODIAN_JIEBANG_ACTIVITIES[pro_id].append(jiebang_entity)

        except Exception as e:
            my_logger.error('读取正在进行中的接棒活动出现错误！')
            my_logger.exception(e)
        # finally:
        #     cursor.close()
    my_logger.debug(global_config.MODIAN_JIEBANG_ACTIVITIES)
    # conn.close()

    my_logger.debug('读取摩点配置耗时: %s秒', time.time() - time0)
    modian_handler.init_order_queues()


@scheduler.scheduled_job('cron', second='10,30,50')
def monitor_modian():
    """
    监控摩点
    :return:
    """
    global modian_handler
    my_logger.debug('监控摩点集资情况')
    for modian in global_config.MODIAN_ARRAY:
        time0 = time.time()
        r = modian_handler.query_project_orders(modian)
        modian_handler.parse_order_details(r, modian)
        my_logger.debug('查询摩点集资情况所消耗的时间为: %s秒', time.time() - time0)


# @scheduler.scheduled_job('cron', second='15,35,55')
# def update_ranking_list():
#     time0 = time.time()
#     global modian_handler
#     my_logger.debug('更新集资榜')
#     for modian in global_config.MODIAN_ARRAY:
#         modian_handler.jizi_rank_list = modian_handler.get_ranking_list(modian, type0=1)
#     time.sleep(5)
#     my_logger.debug('更新打卡榜')
#     for modian in global_config.MODIAN_ARRAY:
#         modian_handler.daka_rank_list = modian_handler.get_ranking_list(modian, type0=2)
#     my_logger.debug('更新排名榜单所用时间: %s', time.time() - time0)


# @scheduler.scheduled_job('cron', minute='*/30')
def sync_order():
    global modian_handler
    my_logger.info('同步订单')
    for modian in global_config.MODIAN_ARRAY:
        pro_id = modian.group_account_id
        orders = modian_handler.get_all_orders(modian)
        for order in orders:
            user_id = order['user_id']
            nickname = order['nickname']
            pay_time = order['pay_time']
            backer_money = order['backer_money']

            oid = uuid.uuid3(uuid.NAMESPACE_OID, str(user_id) + pay_time)
            # print('oid: %s', oid)

            rst = mysql_util.select_one("""
                    select * from `order` where id='%s'
                """, (str(oid),))
            if len(rst) == 0:
                my_logger.info('该订单不在数据库中')
                # 每次需要更新一下昵称
                mysql_util.query("""
                                        INSERT INTO `supporter` (`id`, `name`) VALUES (%s, '%s')  ON DUPLICATE KEY
                                            UPDATE `name`='%s'
                                        """ % (user_id, nickname, nickname))
                mysql_util.query("""
                        INSERT INTO `order` (`id`, `supporter_id`, `backer_money`, `pay_time`, `pro_id`) VALUES 
                            ('%s', %s, %s, '%s', %s);
                    """ % (oid, user_id, backer_money, pay_time, pro_id))
                msg = '【机器人补播报】感谢 %s 支持了%s元, %s\n' % (nickname, backer_money, util.random_str(global_config.MODIAN_POSTSCRIPTS))
                QQHandler.send_to_groups(['483548995'], msg)
                modian_handler.order_queues[modian.group_account_id].add(oid)


# @scheduler.scheduled_job('cron', minute='10,25,40,55', hour='8-22')
def notify_modian_pk():
    """
    播报摩点集资PK情况
    :return:
    """
    global modian_handler
    msg = modian_handler.pk_modian_activity()
    my_logger.info(msg)
    QQHandler.send_to_groups(modian_handler.modian_notify_groups, msg)


# modian_handler = ModianHandlerBS4([], [])
modian_handler = WeixinGroupAccountHandler([], [])
update_modian_conf()
# modian_handler.init_order_queues()
