# -*- coding: utf-8 -*-

from log.my_logger import logger as my_logger

from weibo.weibo_handler import WeiboMonitor
from qq.qqhandler import QQHandler
from utils.config_reader import ConfigReader
from utils import global_config

from utils.scheduler import scheduler


@scheduler.scheduled_job('cron', second='35')
def update_weibo_conf():
    global weibo_monitor

    my_logger.debug('读取微博配置')
    global_config.MEMBER_WEIBO_GROUPS = ConfigReader.get_property('qq_conf', 'member_weibo_groups').split(';')

    member_name = ConfigReader.get_property('root', 'member_name')
    if global_config.CUR_MEMBER is None or member_name != global_config.CUR_MEMBER['pinyin']:
        my_logger.debug('微博监控成员变更')
        # global_config.MEMBER_NAME = member_name
        global_config.CUR_MEMBER = global_config.MEMBER_JSON[member_name]
        # uid = ConfigReader.get_property('weibo', member_name)
        uid = global_config.CUR_MEMBER['weibo_uid']
        my_logger.debug('weibo uid: %s', uid)
        if uid != 0:
            weibo_monitor.getWBQueue(uid)
        else:
            my_logger.error('微博UID填写错误，请检查')


@scheduler.scheduled_job('cron', minute='*', second='55')
def monitor_member_weibo():
    global weibo_monitor

    newWB = weibo_monitor.startMonitor()
    if newWB is not None:
        my_logger.debug(newWB)
        member_weibo_groups = global_config.MEMBER_WEIBO_GROUPS
        message = '你的小宝贝儿发微博啦: %s\n发送时间: %s' % (newWB['scheme'], newWB['created_at'])
        if newWB['created_at'] == '刚刚':
            QQHandler.send_to_groups(member_weibo_groups, message)


weibo_monitor = WeiboMonitor()
update_weibo_conf()


if __name__ == '__main__':
    # global_config.MEMBER_WEIBO_GROUPS = ConfigReader.get_property('qq_conf', 'member_weibo_groups').split(';')
    # weibo_monitor.login('***', '***')
    # name = ConfigReader.get_property('root', 'member_name')
    # uid = ConfigReader.get_property('weibo', name)
    # # uid = 1134206783
    # weibo_monitor.getWBQueue(uid)
    pass
