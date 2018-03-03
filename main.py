import pocket48_plugin
import statistic_plugin
import weibo_plugin
import modian_plugin
from utils import global_config
import json
from utils.config_reader import ConfigReader

from utils.scheduler import scheduler

# 读取口袋48的配置
global_config.MEMBER_JSON = json.load(open('data/member.json', encoding='utf8'))
global_config.POCKET48_VERSION = ConfigReader.get_property('root', 'version')
global_config.IMEI = ConfigReader.get_property('root', 'imei')

scheduler.start()
