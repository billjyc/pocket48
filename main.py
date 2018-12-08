# -*- coding:utf-8 -*-

from utils import global_config
import json
from utils.config_reader import ConfigReader

from utils.scheduler import scheduler

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

import pocket48_plugin
import statistic_plugin
import weibo_plugin
import modian_plugin

scheduler.start()
