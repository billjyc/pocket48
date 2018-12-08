# -*- coding: utf-8 -*-

from log.my_logger import statistic_logger as my_logger
from statistic.statistic_handler import StatisticHandler
from utils import global_config
from utils.config_reader import ConfigReader
from utils.scheduler import scheduler


@scheduler.scheduled_job('cron', minute='45', hour=2)
def update_wds_conf():
    global statistic_handler

    my_logger.debug('读取数据配置-statistic_plugin')
    ConfigReader.read_conf()


@scheduler.scheduled_job('cron', hour=3)
def record_data():
    """
    记录数据
    :return:
    """
    global statistic_handler
    my_logger.debug('记录群人数数据')
    for task in global_config.POCKET48_LISTEN_TASKS:
        my_logger.debug('member name: %s', task.member.name)
        statistic_handler.update_group_size(task.member.pinyin)


statistic_handler = StatisticHandler('statistics.db')
update_wds_conf()
