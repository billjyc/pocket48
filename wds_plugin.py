# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO
from utils.config_reader import ConfigReader
from wds.wds_handler import WDSHandler, WDS
from utils import global_config
from qq.qqhandler import QQHandler
import json


wds_handler = None


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    global wds_handler
    wds_handler = WDSHandler([], [])
    update_wds_conf(bot)


@qqbotsched(hour='3', minute="15")
def update_wds_conf(bot):
    global wds_handler

    DEBUG('读取微打赏配置')
    ConfigReader.read_conf()
    wds_json = json.load(open("data/wds.json"))

    global_config.WDS_POSTSCRIPTS = wds_json['wds_postscripts']

    # 微打赏集资PK链接数组初始化
    global_config.WDS_NEED_DISPLAY_PK = wds_json['wds_need_display_pk']

    for wds_pk_j in wds_json['wds_pk_activities']:
        wds = WDS(wds_pk_j['wds_pk_link'], wds_pk_j['wds_pk_title'], '', '', False)
        global_config.WDS_PK_ARRAY.append(wds)

    # 需要适应同时开多个链接的情况
    global_config.WDS_ARRAY = []

    for wds_j in wds_json['monitor_activities']:
        if wds_j['wds_need_display_rank'] is False:
            wds = WDS(wds_j['wds_link'], wds_j['wds_title'], wds_j['wds_moxi_id'], wds_j['wds_pro_id'],
                      False)
        elif wds_j['wds_need_display_rank'] is True:
            wds = WDS(wds_j['wds_link'], wds_j['wds_title'], wds_j['wds_moxi_id'], wds_j['wds_pro_id'],
                      True)
        global_config.WDS_ARRAY.append(wds)

    wds_handler.wds_array = global_config.WDS_ARRAY

    wds_handler.init_comment_queues()

    global_config.JIZI_NOTIFY_GROUPS = ConfigReader.get_property('qq_conf', 'jizi_notify_groups').split(';')
    wds_groups = QQHandler.list_group(global_config.JIZI_NOTIFY_GROUPS)
    wds_handler.wds_notify_groups = wds_groups

    DEBUG('JIZI_NOTIFY_GROUPS: %s, length: %d', ','.join(global_config.JIZI_NOTIFY_GROUPS),
          len(wds_handler.wds_notify_groups))


@qqbotsched(second='50', minute='*')
def monitor_wds(bot):
    """
    监控微打赏
    :param bot:
    :return:
    """
    global wds_handler
    DEBUG('监控微打赏')
    for wds in global_config.WDS_ARRAY:
        r = wds_handler.monitor_wds_comment(wds)
        wds_handler.parse_wds_comment2(r, wds)


@qqbotsched(hour='*', minute='17')
def notify_wds_pk(bot):
    """
    播报微打赏集资PK情况
    :param bot:
    :return:
    """
    if global_config.WDS_NEED_DISPLAY_PK is False:
        return
    global wds_handler
    # wds_handler = WDSHandler([], [])
    INFO('微打赏集资PK播报')

    for wds in global_config.WDS_PK_ARRAY:
        support_num, current, target = wds_handler.get_current_and_target(wds)

    msg = '当前集资PK战况播报:\n'
    sorted(global_config.WDS_PK_ARRAY, wds_pk_sort)

    for i in range(len(global_config.WDS_PK_ARRAY)):
        wds = global_config.WDS_PK_ARRAY[i]
        sub_msg = '%d. %s\t当前进度: %.2f元\n' % (i+1, wds.title, wds.current)
        msg += sub_msg

    INFO(msg)
    QQHandler.send_to_groups(wds_handler.wds_notify_groups, msg)


def wds_pk_sort(wds1, wds2):
    if wds1.current < wds2.current:
        return 1
    elif wds1.current > wds2.current:
        return -1
    else:
        return 0


if __name__ == '__main__':
    update_wds_conf(None)
    # wds1 = WDS('https://wds.modian.com/show_weidashang_pro/8538', 'fxf', '', '')
    # wds2 = WDS('https://wds.modian.com/show_weidashang_pro/8536', 'yby', '', '')
    # global_config.WDS_PK_ARRAY = [wds1, wds2]
    # notify_wds_pk(None)
