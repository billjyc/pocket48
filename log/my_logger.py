# -*- coding:utf-8 -*-

import logging

from logging import config
import os

file_path = os.path.split(os.path.realpath(__file__))[0] + '/logging.conf'

config.fileConfig(file_path)

logger = logging.getLogger('root')
weibo_logger = logging.getLogger('weibo')
pocket48_logger = logging.getLogger('pocket48')
modian_logger = logging.getLogger('modian')
statistic_logger = logging.getLogger('statistic')

logger.debug('abcdefg')
