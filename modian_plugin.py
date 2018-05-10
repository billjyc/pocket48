# -*- coding: utf-8 -*-

from log.my_logger import modian_logger as my_logger

from utils.config_reader import ConfigReader
from modian.modian_handler import ModianHandler, ModianEntity, ModianJiebangEntity, ModianFlagEntity, ModianCountFlagEntity
from utils import global_config
from qq.qqhandler import QQHandler
import sqlite3
import json
import time
from utils import util

from utils.scheduler import scheduler


@scheduler.scheduled_job('cron', minute='*/15')
def update_modian_conf():
    global modian_handler
    time0 = time.time()
    my_logger.info('读取摩点配置')
    ConfigReader.read_conf()
    modian_json = json.load(open("data/modian.json", encoding='utf8'))

    global_config.MODIAN_POSTSCRIPTS = modian_json['modian_postscripts']

    # 摩点集资PK链接数组初始化
    global_config.MODIAN_NEED_DISPLAY_PK = modian_json['modian_need_display_pk']

    for modian_pk_j in modian_json['modian_pk_activities']:
        global_config.MODIAN_PK_ARRAY.append(modian_pk_j)

    # 是否需要开启抽卡功能
    global_config.MODIAN_CARD_DRAW = modian_json['modian_need_card_draw']

    # 需要适应同时开多个链接的情况
    global_config.MODIAN_ARRAY = []

    for modian_j in modian_json['monitor_activities']:
        if modian_j['modian_need_display_rank'] is False:
            modian = ModianEntity(modian_j['modian_link'], modian_j['modian_title'], modian_j['modian_pro_id'], False)
        elif modian_j['wds_need_display_rank'] is True:
            modian = ModianEntity(modian_j['modian_link'], modian_j['modian_title'], modian_j['modian_pro_id'], True)
        global_config.MODIAN_ARRAY.append(modian)

    modian_handler.modian_project_array = global_config.MODIAN_ARRAY

    modian_handler.init_order_queues()
    modian_handler.card_draw_handler.read_config()

    global_config.JIZI_NOTIFY_GROUPS = ConfigReader.get_property('qq_conf', 'jizi_notify_groups').split(';')
    modian_groups = global_config.JIZI_NOTIFY_GROUPS
    modian_handler.modian_notify_groups = modian_groups

    my_logger.debug('JIZI_NOTIFY_GROUPS: %s, length: %d', ','.join(global_config.JIZI_NOTIFY_GROUPS),
                    len(modian_handler.modian_notify_groups))

    my_logger.debug('读取正在进行中的flag活动')
    global_config.MODIAN_FLAG_ACTIVITIES = {}
    flag_json = json.load(open('data/modian_flag.json', encoding='utf8'))['activities']
    for modian in global_config.MODIAN_ARRAY:
        pro_id = modian.pro_id
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
        pro_id = modian.pro_id
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
    conn = sqlite3.connect('data/modian.db', check_same_thread=False)
    for activity in jiebang_json:
        end_time = activity['end_time']
        if util.convert_timestr_to_timestamp(end_time) < time.time():
            continue
        name = activity['jiebang_name']
        try:
            cursor = conn.cursor()
            c = cursor.execute("""
                select * from jiebang WHERE name=?
            """, (name, ))
            rst = c.fetchall()
            if len(rst) == 1:
                my_logger.debug('len(rst)==1')

                # 修正当前接棒数
                # my_logger.debug('修正当前接棒数')
                # start_time = util.convert_timestr_to_timestamp(activity['start_time'])
                # current_stick_num = 0
                # cur_page = 1
                # entity = None
                # for modian_entity in global_config.MODIAN_ARRAY:
                #     pro_id = modian_entity.pro_id
                #     if str(pro_id) == str(activity['pro_id']):
                #         entity = modian_entity
                #         break
                # while True:
                #     finish_find = False
                #
                #     orders = modian_handler.query_project_orders(entity, cur_page)
                #     if len(orders) <= 0:
                #         break
                #
                #     for order in orders:
                #         order_time = util.convert_timestr_to_timestamp(order['pay_time'])
                #         if order_time < start_time:
                #             finish_find = True
                #             break
                #         current_stick_num += modian_handler.compute_stick_num(activity['min_stick_amount'], order['backer_money'])
                #     if finish_find is True:
                #         break
                #     cur_page += 1
                #
                # cursor.execute("""
                #     UPDATE jiebang SET name=?, pro_id=?, start_time=?, end_time=?,
                #     target_stick_num=?, min_stick_amount=?, current_stick_num=?
                #     WHERE name=?
                # """, (name, activity['pro_id'], activity['start_time'], activity['end_time'],
                #       activity['target_stick_num'], activity['min_stick_amount'], current_stick_num, name))
                # conn.commit()
                # my_logger.debug('%s接棒数修正完成，当前棒数:%s', activity['pro_id'], current_stick_num)
            elif len(rst) == 0:
                my_logger.debug('len(rst)==0')
                cursor.execute("""
                                    INSERT INTO jiebang (name, pro_id, current_stick_num, last_record_time, start_time, 
                                    end_time, target_stick_num, min_stick_amount, need_detail) VALUES
                                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """, (
                name, activity['pro_id'], 0, util.convert_timestamp_to_timestr(time.time()*1000),
                    activity['start_time'], activity['end_time'], activity['target_stick_num'],
                activity['min_stick_amount'], activity['need_detail']))
                conn.commit()
            else:
                raise RuntimeError('接棒活动名称错误！')
        except Exception as e:
            my_logger.error('读取modian.db出现错误')
            my_logger.error(e)
        finally:
            cursor.close()

    # 读取正在进行中的接棒活动
    my_logger.debug('读取正在进行中的接棒活动')
    global_config.MODIAN_JIEBANG_ACTIVITIES = {}
    for modian in global_config.MODIAN_ARRAY:
        pro_id = modian.pro_id
        global_config.MODIAN_JIEBANG_ACTIVITIES[pro_id] = []
        try:
            cursor = conn.cursor()
            c = cursor.execute("""
                SELECT name, pro_id, current_stick_num, last_record_time, 
                    start_time, end_time, target_stick_num, min_stick_amount, need_detail
                FROM jiebang where pro_id=? and start_time <= datetime('now', 'localtime') 
                    and end_time >= datetime('now', 'localtime') and current_stick_num < target_stick_num
            """, (pro_id, ))
            rst = c.fetchall()
            for jiebang in rst:
                my_logger.debug('jiebang: %s, %s, %s, %s, %s, %s, %s, %s, %s',
                                jiebang[0], jiebang[1], jiebang[2], jiebang[3], jiebang[4], jiebang[5],
                                              jiebang[6], jiebang[7], jiebang[8])
                jiebang_entity = ModianJiebangEntity(jiebang[0], jiebang[1], jiebang[2], jiebang[3], jiebang[4], jiebang[5],
                                              jiebang[6], jiebang[7], jiebang[8])
                global_config.MODIAN_JIEBANG_ACTIVITIES[pro_id].append(jiebang_entity)

        except Exception as e:
            my_logger.error('读取正在进行中的接棒活动出现错误！')
            my_logger.error(e)
        finally:
            cursor.close()
    my_logger.debug(global_config.MODIAN_JIEBANG_ACTIVITIES)
    conn.close()

    my_logger.debug('读取摩点配置耗时: %s秒', time.time() - time0)


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


@scheduler.scheduled_job('cron', minute='17', hour='*')
def notify_modian_pk():
    """
    播报摩点集资PK情况
    :return:
    """
    if global_config.MODIAN_NEED_DISPLAY_PK is False:
        return
    global modian_handler
    # wds_handler = WDSHandler([], [])
    my_logger.info('摩点集资PK播报')

    for modian_entity in global_config.MODIAN_PK_ARRAY:
        target, current, pro_name = modian_handler.get_current_and_target(modian_entity)

    msg = '当前集资PK战况播报:\n'
    sorted(global_config.MODIAN_PK_ARRAY, key=lambda x: x.current, reverse=True)

    for i in range(len(global_config.MODIAN_PK_ARRAY)):
        wds = global_config.MODIAN_PK_ARRAY[i]
        sub_msg = '%d. %s\t当前进度: %.2f元\n' % (i+1, wds.title, wds.current)
        msg += sub_msg

    my_logger.info(msg)
    QQHandler.send_to_groups(modian_handler.modian_notify_groups, msg)


modian_handler = ModianHandler([], [])
update_modian_conf()
