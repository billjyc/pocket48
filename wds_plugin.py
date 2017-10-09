# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
from config_reader import ConfigReader
from wds.wds_handler import WDSHandler
import global_config
from qqhandler import QQHandler


wds_handler = None
qq_handler = None


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    global wds_handler, qq_handler
    wds_handler = WDSHandler([])
    qq_handler = QQHandler()
    update_wds_conf(bot)


@qqbotsched(minute='*', second="45")
def update_wds_conf(bot):
    global wds_handler, qq_handler

    DEBUG('读取微打赏配置')
    ConfigReader.read_conf()

    wds_link = ConfigReader.get_property('wds', 'wds_link')

    if global_config.WDS_LINK == '' or wds_link != global_config.WDS_LINK:
        global_config.WDS_LINK = wds_link
        global_config.WDS_TITLE = ConfigReader.get_property('wds', 'wds_title')
        global_config.WDS_MOXI_ID = ConfigReader.get_property('wds', 'wds_moxi_id')
        global_config.WDS_PRO_ID = ConfigReader.get_property('wds', 'wds_pro_id')
        wds_handler.init_comment_queues()

    DEBUG('wds link: %s', global_config.WDS_LINK)
    DEBUG('wds title: %s', global_config.WDS_TITLE)
    DEBUG('wds moxi id: %s', global_config.WDS_MOXI_ID)
    DEBUG('wds pro id: %s', global_config.WDS_PRO_ID)

    global_config.JIZI_NOTIFY_GROUPS = ConfigReader.get_property('qq_conf', 'jizi_notify_groups').split(';')
    wds_groups = qq_handler.list_group(global_config.JIZI_NOTIFY_GROUPS)
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
    r = wds_handler.monitor_wds_comment()
    wds_handler.parse_wds_comment(r)
