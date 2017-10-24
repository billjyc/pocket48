# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
from config_reader import ConfigReader
from wds.wds_handler import WDSHandler, WDS
import global_config
from qqhandler import QQHandler


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

    # wds_link = ConfigReader.get_property('wds', 'wds_link')
    #
    # if global_config.WDS_LINK == '' or wds_link != global_config.WDS_LINK:
    #     global_config.WDS_LINK = wds_link
    #     global_config.WDS_TITLE = ConfigReader.get_property('wds', 'wds_title')
    #     global_config.WDS_MOXI_ID = ConfigReader.get_property('wds', 'wds_moxi_id')
    #     global_config.WDS_PRO_ID = ConfigReader.get_property('wds', 'wds_pro_id')
    #     wds_handler.init_comment_queues()
    #
    # DEBUG('wds link: %s', global_config.WDS_LINK)
    # DEBUG('wds title: %s', global_config.WDS_TITLE)
    # DEBUG('wds moxi id: %s', global_config.WDS_MOXI_ID)
    # DEBUG('wds pro id: %s', global_config.WDS_PRO_ID)

    # 微打赏集资PK链接数组初始化
    wds_need_display_pk = ConfigReader.get_property('wds', 'wds_need_display_pk')
    if wds_need_display_pk.lower() == 'false':
        global_config.WDS_NEED_DISPLAY_PK = False
    elif wds_need_display_pk.lower() == 'true':
        global_config.WDS_NEED_DISPLAY_PK = True
    wds_pk_links = ConfigReader.get_property('wds', 'wds_pk_links').split(';')
    wds_pk_titles = ConfigReader.get_property('wds', 'wds_pk_titles').split(';')

    for i in range(len(wds_pk_links)):
        wds = WDS(wds_pk_links[i], wds_pk_titles[i], '', '', False)
        global_config.WDS_PK_ARRAY.append(wds)

    # 需要适应同时开多个链接的情况
    global_config.WDS_ARRAY = []

    wds_links = ConfigReader.get_property('wds', 'wds_link').split(';')
    wds_titles = ConfigReader.get_property('wds', 'wds_title').split(';')
    wds_moxi_ids = ConfigReader.get_property('wds', 'wds_moxi_id').split(';')
    wds_pro_ids = ConfigReader.get_property('wds', 'wds_pro_id').split(';')
    wds_need_display_rank = ConfigReader.get_property('wds', 'wds_need_display_rank').split(';')

    wds_len = len(wds_links)

    for i in range(wds_len):
        if wds_need_display_rank[i].lower() == 'false':
            wds = WDS(wds_links[i], wds_titles[i], wds_moxi_ids[i], wds_pro_ids[i], False)
        elif wds_need_display_rank[i].lower() == 'true':
            wds = WDS(wds_links[i], wds_titles[i], wds_moxi_ids[i], wds_pro_ids[i], True)
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


@qqbotsched(hour='*')
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


def wds_pk_sort(wds1, wds2):
    if wds1.current < wds2.current:
        return 1
    elif wds1.current > wds2.current:
        return -1
    else:
        return 0


if __name__ == '__main__':
    wds1 = WDS('https://wds.modian.com/show_weidashang_pro/8538', 'fxf', '', '')
    wds2 = WDS('https://wds.modian.com/show_weidashang_pro/8536', 'yby', '', '')
    global_config.WDS_PK_ARRAY = [wds1, wds2]
    notify_wds_pk(None)
