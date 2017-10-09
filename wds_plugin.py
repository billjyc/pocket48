# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
from config_reader import ConfigReader
import global_config
from qqhandler import QQHandler


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    pass


@qqbotsched(second='50', minute='*/3')
def monitor_wds(bot):
    """
    监控微打赏
    :param bot:
    :return:
    """
    pass



