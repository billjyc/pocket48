# -*- coding:utf-8 -*-

import logging

from logging import config
import os

file_path = os.path.split(os.path.realpath(__file__))[0] + '/logging.conf'

config.fileConfig(file_path)

logger = logging.getLogger('root')

logger.debug('abcdefg')
