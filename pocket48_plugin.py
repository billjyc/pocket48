# -*- coding: utf-8 -*-
import time

from log.my_logger import pocket48_logger as my_logger
from utils.config_reader import ConfigReader
from pocket48.pocket48_handler import Pocket48Handler
from qq.qqhandler import QQHandler

from utils import global_config, util
from utils.scheduler import scheduler
import json


@scheduler.scheduled_job('cron', minute='*')
def update_conf():
    """
    每隔1分钟读取配置文件
    :param bot:
    :return:
    """
    global pocket48_handler
    my_logger.debug('读取配置文件')

    ConfigReader.read_conf()
    global_config.AUTO_REPLY_GROUPS = ConfigReader.get_property('qq_conf', 'auto_reply_groups').split(';')
    global_config.MEMBER_ROOM_MSG_GROUPS = ConfigReader.get_property('qq_conf', 'member_room_msg_groups').split(';')
    global_config.MEMBER_ROOM_COMMENT_GROUPS = ConfigReader.\
        get_property('qq_conf', 'member_room_comment_groups').split(';')
    global_config.MEMBER_LIVE_GROUPS = ConfigReader.get_property('qq_conf', 'member_live_groups').split(';')
    global_config.MEMBER_ROOM_MSG_LITE_GROUPS = ConfigReader.get_property('qq_conf', 'member_room_comment_lite_groups').split(';')
    global_config.TEST_GROUPS = ConfigReader.get_property('qq_conf', 'test_groups').split(';')

    auto_reply_groups = global_config.AUTO_REPLY_GROUPS
    member_room_msg_groups = global_config.MEMBER_ROOM_MSG_GROUPS
    member_room_comment_msg_groups = global_config.MEMBER_ROOM_COMMENT_GROUPS
    member_live_groups = global_config.MEMBER_LIVE_GROUPS
    member_room_msg_lite_groups = global_config.MEMBER_ROOM_MSG_LITE_GROUPS
    test_groups = global_config.TEST_GROUPS

    pocket48_handler.member_room_msg_groups = member_room_msg_groups
    pocket48_handler.member_room_comment_msg_groups = member_room_comment_msg_groups
    pocket48_handler.auto_reply_groups = auto_reply_groups
    pocket48_handler.member_live_groups = member_live_groups
    pocket48_handler.member_room_msg_lite_groups = member_room_msg_lite_groups
    pocket48_handler.test_groups = test_groups

    my_logger.debug('member_room_msg_groups: %s, length: %d', ','.join(global_config.MEMBER_ROOM_MSG_GROUPS), len(pocket48_handler.member_room_msg_groups))
    my_logger.debug('member_room_comment_groups: %s, length: %d', ','.join(global_config.MEMBER_ROOM_COMMENT_GROUPS), len(pocket48_handler.member_room_comment_msg_groups))
    my_logger.debug('auto_reply_groups: %s, length: %d', ','.join(global_config.AUTO_REPLY_GROUPS), len(pocket48_handler.auto_reply_groups))
    my_logger.debug('member_live_groups: %s, length: %d', ','.join(global_config.MEMBER_LIVE_GROUPS), len(member_live_groups))
    my_logger.debug('member_room_comment_lite_groups: %s, length: %d', ','.join(global_config.MEMBER_ROOM_MSG_LITE_GROUPS), len(pocket48_handler.member_room_msg_lite_groups))

    my_logger.debug('读取成员信息')

    member_name = ConfigReader.get_property('root', 'member_name')
    if global_config.CUR_MEMBER is None or member_name != global_config.CUR_MEMBER['pinyin']:
        my_logger.info('监控成员变更!')
        global_config.CUR_MEMBER = global_config.MEMBER_JSON[member_name]
        pocket48_handler.init_msg_queues(global_config.CUR_MEMBER['room_id'])
    my_logger.debug('当前监控的成员是: %s', global_config.CUR_MEMBER)

    global_config.ROOM_MSG_LITE_NOTIFY = ConfigReader.get_property('profile', 'room_msg_lite_notify').split(';')

    global_config.PERFORMANCE_NOTIFY = ConfigReader.get_property('profile', 'performance_notify')

    # global_config.LIVE_LINK = ConfigReader.get_property('auto_reply', '公演直播').split(';')


@scheduler.scheduled_job('cron', minute='*', second=10)
def get_room_msgs():
    start_t = time.time()
    global pocket48_handler

    r1 = pocket48_handler.get_member_room_msg(global_config.CUR_MEMBER['room_id'])
    pocket48_handler.parse_room_msg(r1)
    r2 = pocket48_handler.get_member_room_comment(global_config.CUR_MEMBER['room_id'])
    pocket48_handler.parse_room_comment(r2)

    end_t = time.time()
    my_logger.debug('获取房间消息 执行时间: %s', end_t-start_t)


@scheduler.scheduled_job('cron', minute='*', second=40)
def get_member_lives():
    global pocket48_handler

    r = pocket48_handler.get_member_live_msg()
    pocket48_handler.parse_member_live(r, global_config.CUR_MEMBER['member_id'])


@scheduler.scheduled_job('cron', second=30, minute='20,50', hour='13,18,19', day_of_week='2-6')
def notify_performance():
    my_logger.info('检查公演日程')
    global pocket48_handler
    pocket48_handler.notify_performance()


pocket48_handler = Pocket48Handler([], [], [], [], [], [])

username = ConfigReader.get_property('user', 'username')
password = ConfigReader.get_property('user', 'password')
pocket48_handler.login(username, password)

# 先更新配置

update_conf()
