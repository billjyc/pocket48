# -*- coding:utf-8 -*-
"""
2018武侠特别活动
"""
from utils.mysql_util import mysql_util
import logging
from utils import util


class Character:
    def __init__(self, modian_id, name, prop1, prop2, prop3, prop4, prop5):
        self.id = modian_id
        self.name = name
        self.prop1 = prop1
        self.prop2 = prop2
        self.prop3 = prop3
        self.prop4 = prop4
        self.prop5 = prop5



