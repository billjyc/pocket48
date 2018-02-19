# -*- coding: utf-8 -*-

from log.my_logger import logger as my_logger

from utils.config_reader import ConfigReader
from statistic.statistic_handler import StatisticHandler
from utils import global_config
from qq.qqhandler import QQHandler
import json
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
    :param bot:
    :return:
    """
    global statistic_handler
    my_logger.debug('记录群人数数据')
    my_logger.debug('member name: %s', global_config.CUR_MEMBER['chinese_name'])
    statistic_handler.update_group_size(global_config.CUR_MEMBER['pinyin'])


statistic_handler = StatisticHandler('statistics.db')
update_wds_conf()
