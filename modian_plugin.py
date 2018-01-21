# -*- coding: utf-8 -*-

from qqbot.utf8logger import DEBUG, INFO
from qqbot import qqbotsched
from utils.config_reader import ConfigReader
from wds.modian_handler import ModianHandler, ModianEntity
from utils import global_config
from qq.qqhandler import QQHandler
import json


modian_handler = ModianHandler([], [])


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    global modian_handler
    update_modian_conf(bot)


@qqbotsched(minute='*/15')
def update_modian_conf(bot):
    global modian_handler
    INFO('读取摩点配置')
    ConfigReader.read_conf()
    modian_json = json.load(open("data/modian.json"))

    global_config.MODIAN_POSTSCRIPTS = modian_json['modian_postscripts']

    # 摩点集资PK链接数组初始化
    global_config.MODIAN_NEED_DISPLAY_PK = modian_json['modian_need_display_pk']

    for modian_pk_j in modian_json['modian_pk_activities']:
        global_config.MODIAN_PK_ARRAY.append(modian_pk_j)

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

    global_config.JIZI_NOTIFY_GROUPS = ConfigReader.get_property('qq_conf', 'jizi_notify_groups').split(';')
    modian_groups = global_config.JIZI_NOTIFY_GROUPS
    modian_handler.modian_notify_groups = modian_groups

    DEBUG('JIZI_NOTIFY_GROUPS: %s, length: %d', ','.join(global_config.JIZI_NOTIFY_GROUPS),
                    len(modian_handler.modian_notify_groups))


@qqbotsched(minute='*', second='50')
def monitor_modian(bot):
    """
    监控微打赏
    :return:
    """
    global modian_handler
    DEBUG('监控摩点集资情况')
    for modian in global_config.MODIAN_ARRAY:
        r = modian_handler.query_project_orders(modian)
        modian_handler.parse_order_details(r, modian)


@qqbotsched(minute='17', hour='*')
def notify_wds_pk(bot):
    """
    播报微打赏集资PK情况
    :return:
    """
    if global_config.WDS_NEED_DISPLAY_PK is False:
        return
    global modian_handler
    # wds_handler = WDSHandler([], [])
    INFO('摩点集资PK播报')

    for modian_entity in global_config.WDS_PK_ARRAY:
        target, current, pro_name = modian_handler.get_current_and_target(modian_entity)

    msg = '当前集资PK战况播报:\n'
    sorted(global_config.WDS_PK_ARRAY, key=lambda x: x.current, reverse=True)

    for i in range(len(global_config.WDS_PK_ARRAY)):
        wds = global_config.WDS_PK_ARRAY[i]
        sub_msg = '%d. %s\t当前进度: %.2f元\n' % (i+1, wds.title, wds.current)
        msg += sub_msg

    INFO(msg)
    QQHandler.send_to_groups(modian_handler.modian_notify_groups, msg)

