# -*- coding:utf-8 -*-
"""
2018武侠特别活动
"""
from utils.mysql_util import mysql_util
import logging
try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)
from utils import util
import os
import itertools
import random

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 本地读取txt文件-list1
last_names = util.read_txt(os.path.join(BASE_DIR, 'data', 'last_name.txt'))
first_names = util.read_txt(os.path.join(BASE_DIR, 'data', 'first_name.txt'))
TOTAL_NAMES = set()
for x in itertools.product(last_names, first_names):
    TOTAL_NAMES.add(x[0] + x[1])


class Character:
    def __init__(self, modian_id, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.id = modian_id
        self.name = name
        self.prop1 = prop1
        self.prop2 = prop2
        self.prop3 = prop3
        self.prop4 = prop4
        self.prop5 = prop5


def created(modian_id):
    """
    是否创建人物，以摩点id判断
    :param modian_id: 摩点id
    :return:
    """
    my_logger.info('查询人物是否创建，modian_id: %s' % modian_id)
    rst = mysql_util.select_one("""
        SELECT * FROM `t_character` WHERE modian_id=%s
    """, (modian_id, ))
    my_logger.debug('rst: %s' % rst)
    if len(rst) > 0:
        return True, Character(modian_id, rst[0][1], rst[0][2], rst[0][3], rst[0][4], rst[0][5], rst[0][6])
    else:
        return False, None


def create_character(modian_id):
    """
    创建人物
    :return:
    """
    my_logger.info('创建人物, modian_id: %s' % modian_id)
    # 随机姓名
    random_name = TOTAL_NAMES.pop()
    my_logger.debug('随机姓名: %s' % random_name)
    # 随机生成属性
    prop1 = random.randint(1, 10)
    prop2 = random.randint(1, 10)
    prop3 = random.randint(1, 10)
    prop4 = random.randint(1, 10)
    prop5 = random.randint(1, 10)
    mysql_util.query("""
        INSERT INTO `t_character` (`modian_id`, `name`, `prop1`, `prop2`, `prop3`, `prop4`, `prop5`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (modian_id, random_name, prop1, prop2, prop3, prop4, prop5))
    report_str = '恭喜，人物创建成功！\n'
    report_str += '姓名: %s\n属性1: %s, 属性2: %s, 属性3: %s, 属性4: %s, 属性5: %s\n' % (random_name, prop1, prop2, prop3, prop4, prop5)
    return report_str


def donate(modian_id, pay_amount):
    rst = ''
    has_created, character = created(modian_id)
    if has_created:
        my_logger.info('已经创建了人物: %s' % modian_id)
        # 如果已经创建
        rst = '%s触发了随机事件（施工中）' % character.name
    else:
        my_logger.info('未创建人物, modian_id: %s' % modian_id)
        if pay_amount >= 1:
            rst = create_character(modian_id)
    return rst


def sync_names():
    """
    程序启动时，本地和db同步下已使用的姓名
    :return:
    """
    global TOTAL_NAMES
    # 从DB获取已使用的姓名
    rst = mysql_util.select_all("""
        SELECT `name` from `t_character`;
    """)
    my_logger.debug('names in db: %s' % rst)
    name_used = []
    if rst:
        for a in rst:
            name_used.append(a[0])
    # name_used = ['刘超', '李凡']
    # return list1 - list2
    total_copy = TOTAL_NAMES.copy()
    TOTAL_NAMES = list(total_copy.difference(set(name_used)))


sync_names()
if __name__ == '__main__':
    # sync_names()
    print(create_character('123456'))
