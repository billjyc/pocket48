# -*- coding: utf-8 -*-

from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
from weibo.weibo_handler import WeiboMonitor
from qqhandler import QQHandler
from config_reader import ConfigReader
import global_config

weibo_monitor = None
qq_handler = None


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    global weibo_monitor, qq_handler
    qq_handler = QQHandler()

    global_config.MEMBER_WEIBO_GROUPS = ConfigReader.get_property('qq_conf', 'member_weibo_groups').split(';')
    weibo_monitor = WeiboMonitor()
    weibo_monitor.login('hacker4043', 'jiaYICONG123')
    uid = ConfigReader.get_property('weibo', 'fengxiaofei')
    # uid = 1134206783
    weibo_monitor.getWBQueue(uid)


@qqbotsched(second='*/10')
def monitor_member_weibo(bot):
    global weibo_monitor, qq_handler

    newWB = weibo_monitor.startMonitor()
    if newWB is not None:
        DEBUG(newWB)
        member_weibo_groups = qq_handler.list_group(global_config.MEMBER_WEIBO_GROUPS)
        message = '你的小宝贝儿发微博啦: %s\n发送时间: %s' % (newWB['text'], newWB['created_at'])
        QQHandler.send_to_groups(member_weibo_groups, message)
