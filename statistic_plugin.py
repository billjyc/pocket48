# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG
from utils.config_reader import ConfigReader
from statistic.statistic_handler import StatisticHandler
from utils import global_config
from qq.qqhandler import QQHandler
import json


statistic_handler = None


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    global statistic_handler
    statistic_handler = StatisticHandler('statistics.db')
    update_wds_conf(bot)


@qqbotsched(hour='2', minute="45")
def update_wds_conf(bot):
    global statistic_handler

    DEBUG('读取数据配置')
    ConfigReader.read_conf()


@qqbotsched(hour='3')
def record_data(bot):
    """
    记录数据
    :param bot:
    :return:
    """
    global statistic_handler
    DEBUG('记录群人数数据')
    DEBUG('member name: %s', global_config.MEMBER_NAME)
    statistic_handler.update_group_size(global_config.MEMBER_NAME)


if __name__ == '__main__':
    pass
