# -*- coding: utf-8 -*-
import time

from log.my_logger import logger as my_logger
from utils.config_reader import ConfigReader
from pocket48.pocket48_handler import Pocket48Handler
from qq.qqhandler import QQHandler

from utils import global_config, util
from utils.scheduler import scheduler


def onQQMessage(bot, contact, member, content):
    # 当收到 QQ 消息时被调用
    # bot     : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # contact : QContact 对象，消息的发送者
    # member  : QContact 对象，仅当本消息为 群或讨论组 消息时有效，代表实际发消息的成员
    # content : str 对象，消息内容
    my_logger.debug('member: %s', str(getattr(member, 'uin')))
    # my_logger.debug('content: %s', content)
    # my_logger.debug('contact: %s', contact.ctype)

    if contact.ctype == 'group' and contact.qq in global_config.AUTO_REPLY_GROUPS:
        if '@ME' in content:  # 在群中@机器人
            bot.SendTo(contact, member.name + '，' + util.random_str(global_config.AT_AUTO_REPLY))
        elif content.startswith('-'):  # 以'-'开头才能触发自动回复
            if content == '-version':
                bot.SendTo(contact, 'QQbot-' + bot.conf.version)
            elif content == global_config.MEMBER_ATTR:  # 群消息输入成员缩写
                bot.SendTo(contact, util.random_str(global_config.I_LOVE))
            elif content in global_config.JIZI_KEYWORDS:  # 集资链接
                jizi_link = '\n'.join(global_config.JIZI_LINK)
                bot.SendTo(contact, '集资链接: %s' % jizi_link)
            elif content in global_config.WEIBO_KEYWORDS:  # 微博关键词
                weibo_link = global_config.WEIBO_LINK
                super_tag = global_config.SUPER_TAG
                bot.SendTo(contact, '微博: %s\n超级话题: %s' % (weibo_link, super_tag))
            elif content in global_config.GONGYAN_KEYWORDS:  # 公演关键词
                live_link = '\n'.join(global_config.LIVE_LINK)
                # strs = ConfigReader.get_property('profile', 'live_schedule').split(';')
                live_schedule = '\n'.join(global_config.LIVE_SCHEDULE)
                msg = '直播传送门: %s\n本周安排: %s' % (live_link, live_schedule)
                bot.SendTo(contact, msg)
            elif content in ['-统计']:
                histogram = ConfigReader.get_property('profile', 'histogram')
                msg = '公演统计链接: %s' % histogram
                bot.SendTo(contact, msg)
            else:  # 无法识别命令
                no_such_command = ConfigReader.get_property('profile', 'no_such_command')
                bot.SendTo(contact, no_such_command)


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

    auto_reply_groups = global_config.AUTO_REPLY_GROUPS
    member_room_msg_groups = global_config.MEMBER_ROOM_MSG_GROUPS
    member_room_comment_msg_groups = global_config.MEMBER_ROOM_COMMENT_GROUPS
    member_live_groups = global_config.MEMBER_LIVE_GROUPS
    member_room_msg_lite_groups = global_config.MEMBER_ROOM_MSG_LITE_GROUPS

    pocket48_handler.member_room_msg_groups = member_room_msg_groups
    pocket48_handler.member_room_comment_msg_groups = member_room_comment_msg_groups
    pocket48_handler.auto_reply_groups = auto_reply_groups
    pocket48_handler.member_live_groups = member_live_groups
    pocket48_handler.member_room_msg_lite_groups = member_room_msg_lite_groups

    # 初始化人数统计
    for group_number in global_config.MEMBER_ROOM_MSG_LITE_GROUPS:
        if group_number not in global_config.GROUP_MEMBER_NUM.keys():
            global_config.GROUP_MEMBER_NUM[group_number] = 0

    my_logger.debug('member_room_msg_groups: %s, length: %d', ','.join(global_config.MEMBER_ROOM_MSG_GROUPS), len(pocket48_handler.member_room_msg_groups))
    my_logger.debug('member_room_comment_groups: %s, length: %d', ','.join(global_config.MEMBER_ROOM_COMMENT_GROUPS), len(pocket48_handler.member_room_comment_msg_groups))
    my_logger.debug('auto_reply_groups: %s, length: %d', ','.join(global_config.AUTO_REPLY_GROUPS), len(pocket48_handler.auto_reply_groups))
    my_logger.debug('member_live_groups: %s, length: %d', ','.join(global_config.MEMBER_LIVE_GROUPS), len(member_live_groups))
    my_logger.debug('member_room_comment_lite_groups: %s, length: %d', ','.join(global_config.MEMBER_ROOM_MSG_LITE_GROUPS), len(pocket48_handler.member_room_msg_lite_groups))

    member_name = ConfigReader.get_property('root', 'member_name')
    if global_config.MEMBER_NAME == '' or member_name != global_config.MEMBER_NAME:
        my_logger.info('监控成员变更!')
        global_config.ROOM_ID = ConfigReader.get_member_room_number(member_name)
        if global_config.ROOM_ID == '':
            my_logger.error('该成员没有开通口袋房间！')
        global_config.MEMBER_ID = ConfigReader.get_property('live', member_name)
        pocket48_handler.init_msg_queues(global_config.ROOM_ID)
        global_config.MEMBER_NAME = member_name
    my_logger.debug('当前监控的成员是: %s, 房间ID: %s, member_id: %s', member_name, global_config.ROOM_ID, global_config.MEMBER_ID)

    global_config.JIZI_KEYWORDS = ConfigReader.get_property('profile', 'jizi_keywords').split(';')
    global_config.JIZI_LINK = ConfigReader.get_property('profile', 'jizi_link').split(';')

    global_config.WEIBO_KEYWORDS = ConfigReader.get_property('profile', 'weibo_keywords').split(';')
    global_config.GONGYAN_KEYWORDS = ConfigReader.get_property('profile', 'gongyan_keywords').split(';')
    global_config.LIVE_LINK=ConfigReader.get_property('profile', 'live_link').split(';')
    global_config.LIVE_SCHEDULE = ConfigReader.get_property('profile', 'live_schedule').split(';')

    global_config.WEIBO_LINK = ConfigReader.get_property('profile', 'weibo_link')
    global_config.SUPER_TAG = ConfigReader.get_property('profile', 'super_tag')

    global_config.MEMBER_ATTR = ConfigReader.get_property('profile', 'member_attr')
    global_config.I_LOVE = ConfigReader.get_property('profile', 'i_love').split(';')

    global_config.AT_AUTO_REPLY = ConfigReader.get_property('profile', 'at_auto_reply').split(';')
    global_config.ROOM_MSG_LITE_NOTIFY = ConfigReader.get_property('profile', 'room_msg_lite_notify').split(';')

    global_config.PERFORMANCE_NOTIFY = ConfigReader.get_property('profile', 'performance_notify')


@scheduler.scheduled_job('cron', minute='*', second=10)
def get_room_msgs():
    start_t = time.time()
    global pocket48_handler

    r1 = pocket48_handler.get_member_room_msg(global_config.ROOM_ID)
    pocket48_handler.parse_room_msg(r1)
    r2 = pocket48_handler.get_member_room_comment(global_config.ROOM_ID)
    pocket48_handler.parse_room_comment(r2)

    # my_logger.debug('last_msg_time: %s', pocket48_handler.last_msg_time)

    end_t = time.time()
    my_logger.debug('获取房间消息 执行时间: %s', end_t-start_t)


@scheduler.scheduled_job('cron', minute='*', second=40)
def get_member_lives():
    global pocket48_handler

    r = pocket48_handler.get_member_live_msg()
    pocket48_handler.parse_member_live(r, global_config.MEMBER_ID)


@scheduler.scheduled_job('cron', second=30, minute='20,50', hour='13,18,19', day_of_week='2-6')
def notify_performance():
    my_logger.info('检查公演日程')
    global pocket48_handler
    pocket48_handler.notify_performance()


@scheduler.scheduled_job('cron', minute='*', second=35)
def notify_group_number():
    my_logger.info('检查群内人数')
    for g_number in global_config.MEMBER_ROOM_MSG_LITE_GROUPS:
        number = QQHandler.get_group_number(g_number)
        my_logger.debug('群%s: %d人', g_number, number)
        my_logger.debug('global_config.GROUP_MEMBER_NUM: %d', global_config.GROUP_MEMBER_NUM[g_number])
        if 0 < global_config.GROUP_MEMBER_NUM[g_number] < number:
            my_logger.info('有新人入群啦~')

            g_obj = [g_number]
            QQHandler.send_to_groups(g_obj, '机器人自动欢迎~')
        global_config.GROUP_MEMBER_NUM[g_number] = number


pocket48_handler = Pocket48Handler([], [], [], [], [])

username = ConfigReader.get_property('user', 'username')
password = ConfigReader.get_property('user', 'password')
pocket48_handler.login(username, password)

# 先更新配置
update_conf()
