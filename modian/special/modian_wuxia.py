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
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 本地读取txt文件-list1
# last_names = util.read_txt(os.path.join(BASE_DIR, 'data', 'last_name.txt'))
# first_names = util.read_txt(os.path.join(BASE_DIR, 'data', 'first_name.txt'))
TOTAL_NAMES = set(util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'names.txt')))
# for x in itertools.product(last_names, first_names):
#     TOTAL_NAMES.add(x[0] + x[1])
event_json = json.load(open(os.path.join(BASE_DIR, 'data', 'wuxia', 'event.json'), encoding='utf-8'))


class Character:
    def __init__(self, modian_id, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.id = modian_id
        self.name = name
        self.prop1 = prop1  # 攻
        self.prop2 = prop2  # 防
        self.prop3 = prop3  # 气
        self.prop4 = prop4  # 运
        self.prop5 = prop5  # 魅力


class Equipment:
    """
    装备类物品
    """
    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.name = name
        self.prop1 = prop1  # 攻
        self.prop2 = prop2  # 防
        self.prop3 = prop3  # 气
        self.prop4 = prop4  # 运
        self.prop5 = prop5  # 魅力


class Item:
    """
    消耗类物品
    """
    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.name = name
        self.prop1 = prop1  # 攻
        self.prop2 = prop2  # 防
        self.prop3 = prop3  # 气
        self.prop4 = prop4  # 运
        self.prop5 = prop5  # 魅力


class Skill:
    """
    技能
    """
    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.name = name
        self.prop1 = prop1  # 攻
        self.prop2 = prop2  # 防
        self.prop3 = prop3  # 气
        self.prop4 = prop4  # 运
        self.prop5 = prop5  # 魅力


class Event:
    def __init__(self, id, name, amount, weight):
        self.id = id
        self.name = name
        self.amount = amount
        self.weight = weight


def handle_event(pay_amount, character):
    event_list_j = event_json[str(pay_amount)]
    event_list = []
    weight_list = []
    for event_j in event_list_j:
        event = Event(event_j['id'], event_j['name'], pay_amount, event_j['weight'])
        event_list.append(event)
        weight_list.append(event_j['weight'])
    # 按概率选出是哪个大类的事件
    choice = util.weight_choice(event_list, weight_list)
    my_logger.info('触发事件: %s' % choice.name)

    if choice.id == 401:  # 个体-遇怪
        pass
    elif choice.id == 402:  # 个体-物品
        pass
    elif choice.id == 403:  # 互动-相识
        pass
    elif choice.id == 404:  # 互动-交恶
        pass
    elif choice.id == 405:  # 互动-PK
        pass
    elif choice.id == 301:  # 学艺-基础
        pass
    elif choice.id == 302:  # 学艺-PK
        pass
    elif choice.id == 201:  # 门派
        pass
    elif choice.id == 101:  # 其他-得子
        pass
    elif choice.id == 102:  # 其他-称号升级
        pass


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
    my_logger.debug(type(rst))
    my_logger.debug(rst)
    # my_logger.debug('rst: %s' % rst)
    if rst and len(rst) > 0:
        return True, Character(modian_id, str(rst[1], encoding='utf-8'), rst[2], rst[3], rst[4], rst[5], rst[6])
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
    prop1 = random.randint(40, 70)
    prop2 = random.randint(30, 60)
    prop3 = random.randint(5, 20)
    prop4 = random.randint(0, 50)
    prop5 = random.randint(30, 50)
    mysql_util.query("""
        INSERT INTO `t_character` (`modian_id`, `name`, `prop1`, `prop2`, `prop3`, `prop4`, `prop5`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (modian_id, random_name, prop1, prop2, prop3, prop4, prop5))

    intro_words = [
        "郁雷之声渐响，轰轰不绝。河海尚远，而耳中尽是浪涛之声。 似有一名字伴雷声入耳，仔细辨来，名为：【{}】。".format(random_name),
        "湖山深处,但见竹木阴森,苍翠重叠,不雨而润,不烟而晕, 晨雾朦胧处现一少年，“在下【{}】，请问此处可是星梦谷？”".format(random_name),
        "月照竹林风飞叶，竹影之下见刀光。小侠籍籍无名，仅有此片竹林识得其名为【{}】".format(random_name),
        "嗖的一声，一支羽箭从山坳后射了出来，呜呜声响，划过长空，【{}】松开弓弦，雁落平沙。".format(random_name),
        "灯宵月夕，雪际花时，市集喧闹却也听得句柔声细语：“这文书写有【{}】之名，可是你掉的？”".format(random_name)
    ]
    # 随机挑选一个出场方式
    intro = util.choice(intro_words)
    report_str = '%s\n' % intro[0]
    report_str += '%s的武侠世界开启, 属性：\n攻: %s, 防: %s, 气: %s, 运: %s, 魅力: %s\n' % (random_name, prop1, prop2, prop3, prop4, prop5)
    return report_str


def donate(modian_id, pay_amount):
    MIN_AMOUNT = 1
    rst = ''
    has_created, character = created(modian_id)
    if has_created:
        my_logger.info('已经创建了人物: %s' % modian_id)
        # 如果已经创建
        my_logger.debug('%s触发了随机事件（施工中）' % character.name)
        if pay_amount < MIN_AMOUNT:
            return ''
        tmp = pay_amount
        amounts = [200, 100, 50, 10]
        max_event = 3  # 最多触发3次事件
        idx = 0
        while max_event > 0:
            event_time = int(tmp / amounts[idx])
            event_time = max_event if event_time > max_event else event_time
            for i in range(event_time):
                handle_event(amounts[idx], character)
            max_event -= event_time
            tmp = tmp % amounts[idx]
            idx += 1
    else:
        my_logger.info('未创建人物, modian_id: %s' % modian_id)
        if pay_amount >= MIN_AMOUNT:
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
    my_logger.debug(type(rst))
    my_logger.debug(rst)
    # my_logger.debug('names in db: %s' % rst)
    name_used = []
    if rst:
        for a in rst:
            name_used.append(str(a[0], encoding='utf-8'))
    my_logger.debug('name_used: %s' % name_used)
    # name_used = ['刘超', '李凡']
    # return list1 - list2
    total_copy = TOTAL_NAMES.copy()
    TOTAL_NAMES = total_copy.difference(set(name_used))


sync_names()
if __name__ == '__main__':
    # sync_names()
    print(create_character('123456'))
