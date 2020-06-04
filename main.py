# -*- coding:utf-8 -*-

from utils import global_config
from utils import util
import json
from utils.config_reader import ConfigReader

from utils.scheduler import scheduler
from log.my_logger import logger
from pocket48.pocket48_handler import Pocket48ListenTask, Member

# 读取口袋48的配置
global_config.MEMBER_JSON = json.load(open('data/pocket48/member.json', encoding='utf8'))
global_config.POCKET48_JSON = json.load(open('data/pocket48/pocket48.json'), encoding='utf8')
global_config.POCKET48_VERSION = global_config.POCKET48_JSON['version']
global_config.IMEI = global_config.POCKET48_JSON['IMEI']

global_config.AUTO_REPLY_GROUPS = ConfigReader.get_property('qq_conf', 'auto_reply_groups').split(';')
global_config.TEST_GROUPS = ConfigReader.get_property('qq_conf', 'test_groups').split(';')
global_config.PERFORMANCE_NOTIFY = ConfigReader.get_property('profile', 'performance_notify')
global_config.LIVE_LINK = ConfigReader.get_property('auto_reply', '公演直播')

using_pro = ConfigReader.get_property('root', 'using_coolq_pro')
if using_pro == 'yes':
    global_config.USING_COOLQ_PRO = True

logger.debug('读取成员信息')
members_list = global_config.POCKET48_JSON['monitor_members']
for member in members_list:
    member_pinyin = member['name']
    if member_pinyin in global_config.MEMBER_JSON:
        # 如果成员名在数据文件中，创建监听任务
        member_json = global_config.MEMBER_JSON[member_pinyin]
        member_obj = Member(name=member_json['chinese_name'], member_id=member_json['member_id'],
                            room_id=member_json['room_id'], weibo_uid=member_json['weibo_uid'],
                            pinyin=member_pinyin)
        task = Pocket48ListenTask(member_obj)
        task.member_live_groups = member['broadcast_message_lite_groups']
        task.member_room_msg_groups = member['broadcast_message_detail_groups']
        task.member_room_msg_lite_groups = member['broadcast_message_lite_groups']
        task.room_comment_groups = member['broadcast_room_comment_groups']
        logger.debug('room_msg_lite_groups: {}'.format(task.member_room_msg_lite_groups))
        logger.debug('room_msg_groups: {}'.format(task.member_room_msg_groups))
        # task.lite_message = member['lite_message']
        # pocket48_handler.listen_tasks.append(task)
        global_config.POCKET48_LISTEN_TASKS.append(task)
        # pocket48_handler.init_msg_queues(task)
    else:
        logger.error('member_name: {}不在数据文件中，请重试！'.format(member_pinyin))

import pocket48_plugin
import statistic_plugin
import weibo_plugin
import modian_plugin

scheduler.start()
