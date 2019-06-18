# -*- coding: utf-8 -*-
import time

from log.my_logger import pocket48_logger as my_logger
from pocket48.pocket48_handler import pocket48_handler
from utils import global_config
from utils.config_reader import ConfigReader
from utils.scheduler import scheduler


# @scheduler.scheduled_job('cron', minute='*')
def update_conf():
    """
    每隔1分钟读取配置文件
    :return:
    """
    my_logger.debug('读取配置文件：conf.ini')
    ConfigReader.read_conf()

    auto_reply_groups = global_config.AUTO_REPLY_GROUPS
    test_groups = global_config.TEST_GROUPS

    pocket48_handler.auto_reply_groups = auto_reply_groups
    pocket48_handler.test_groups = test_groups

    my_logger.debug('auto_reply_groups: %s, length: %d', ','.join(global_config.AUTO_REPLY_GROUPS),
                    len(pocket48_handler.auto_reply_groups))

    for task in global_config.POCKET48_LISTEN_TASKS:
        pocket48_handler.listen_tasks.append(task)
        pocket48_handler.init_msg_queues(task)


@scheduler.scheduled_job('cron', minute='*', second=10)
def get_room_msgs():
    for task in pocket48_handler.listen_tasks:
        start_t = time.time()
        r1 = pocket48_handler.get_member_room_msg(task)
        pocket48_handler.parse_room_msg(r1, task)
        r2 = pocket48_handler.get_member_room_comment(task)
        pocket48_handler.parse_room_comment(r2, task)

        end_t = time.time()
        my_logger.debug('获取{}房间消息 执行时间: {}'.format(task.member.name, end_t - start_t))


# @scheduler.scheduled_job('cron', minute='*', second=40)
# def get_member_lives():
#     """
#     获取直播信息
#     :return:
#     """
#     r = pocket48_handler.get_member_live_msg()
#     for task in pocket48_handler.listen_tasks:
#         pocket48_handler.parse_member_live(r, task)

@scheduler.scheduled_job('cron', hour='*/2')
def login_timely():
    my_logger.info('定时登录，刷新token')
    pocket48_handler.is_login = False
    pocket48_handler.login(username, password)


@scheduler.scheduled_job('cron', second=30, minute='20,50', hour='13,18,19', day_of_week='2-6')
def notify_performance():
    my_logger.info('检查公演日程')
    pocket48_handler.notify_performance()


username = global_config.POCKET48_JSON["username"]
password = global_config.POCKET48_JSON["password"]
pocket48_handler.login(username, password)
# 先更新配置
update_conf()
