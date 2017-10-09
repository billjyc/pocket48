# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
from config_reader import ConfigReader
from wds.wds_handler import WDSHandler
import global_config
from qqhandler import QQHandler


wds_handler = None


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    global wds_handler
    update_wds_conf(bot)
    wds_handler = WDSHandler(global_config.JIZI_NOTIFY_GROUPS)


@qqbotsched(minute='*', second="45")
def update_wds_conf(bot):
    global wds_handler

    DEBUG('读取微打赏配置')
    ConfigReader.read_conf()
    global_config.WDS_LINK = ConfigReader.get_property('wds', 'wds_link')
    global_config.WDS_TITLE = ConfigReader.get_property('wds', 'wds_title')
    global_config.WDS_MOXI_ID = ConfigReader.get_property('wds', 'wds_moxi_id')
    global_config.WDS_PRO_ID = ConfigReader.get_property('wds', 'wds_pro_id')

    global_config.JIZI_NOTIFY_GROUPS = ConfigReader.get_property('qq_conf', 'jizi_notify_groups')
    wds_handler.wds_notify_groups = global_config.JIZI_NOTIFY_GROUPS


@qqbotsched(second='50', minute='*/3')
def monitor_wds(bot):
    """
    监控微打赏
    :param bot:
    :return:
    """
    global wds_handler
    r = wds_handler.monitor_wds_comment()
    wds_handler.parse_wds_comment(r)



