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
import random
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Character:
    def __init__(self, modian_id, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.id = modian_id
        self.name = name
        self.prop1 = prop1  # 攻
        self.prop2 = prop2  # 防
        self.prop3 = prop3  # 气
        self.prop4 = prop4  # 运
        self.prop5 = prop5  # 魅力

    def __str__(self):
        return 'Character[modian_id=%s, name=%s, 攻=%s, 防=%s, 气=%s, 运=%s, 魅力=%s]' % (self.id, self.name, self.prop1,
                                                                                    self.prop2, self.prop3,
                                                                                    self.prop4, self.prop5)

    def use_good(self, good):
        """
        使用物品或学习技能
        :param good:
        :return:
        """
        my_logger.info('人物使用物品: %s' % good)
        self.prop1 += good.prop1
        self.prop2 += good.prop2
        self.prop3 += good.prop3
        self.prop4 += good.prop4
        self.prop5 += good.prop5

        self.prop1 = 0 if self.prop1 < 0 else self.prop1
        self.prop2 = 0 if self.prop2 < 0 else self.prop2
        self.prop3 = 0 if self.prop3 < 0 else self.prop3
        self.prop4 = 0 if self.prop4 < 0 else self.prop4
        self.prop5 = 0 if self.prop5 < 0 else self.prop5

    def pk(self, other):
        """
        和他人PK
        :param other:
        :return:
        """
        value1 = (self.prop1 * 1.5 + self.prop2 + self.prop3 * 1.2 + self.prop5 * 0.9) * (1 + self.prop4 / 100.0)
        value2 = (other.prop1 * 1.5 + other.prop2 + other.prop3 * 1.2 + other.prop5 * 0.9) * (1 + other.prop4 / 100.0)
        return value1 >= value2


class Good:
    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.name = name
        self.prop1 = prop1  # 攻
        self.prop2 = prop2  # 防
        self.prop3 = prop3  # 气
        self.prop4 = prop4  # 运
        self.prop5 = prop5  # 魅力

    def __str__(self):
        return 'Good[name=%s, 攻=%s, 防=%s, 气=%s, 运=%s, 魅力=%s]' % (self.name, self.prop1,
                                                                 self.prop2, self.prop3,
                                                                 self.prop4, self.prop5)

    def property_change(self):
        property_change_str = ''
        property_change_str += '攻+%s, ' % self.prop1 if self.prop1 > 0 else ''
        property_change_str += '防+%s, ' % self.prop2 if self.prop2 > 0 else ''
        property_change_str += '气+%s, ' % self.prop3 if self.prop3 > 0 else ''
        property_change_str += '运+%s, ' % self.prop4 if self.prop4 > 0 else ''
        property_change_str += '魅力+%s, ' % self.prop5 if self.prop5 > 0 else ''
        return property_change_str[:-1]


class Equipment(Good):
    """
    装备类物品
    """

    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        super(Equipment, self).__init__(name, prop1, prop2, prop3, prop4, prop5)


class Item:
    """
    消耗类物品
    """

    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        super(Item, self).__init__(name, prop1, prop2, prop3, prop4, prop5)


class Skill:
    """
    技能
    """

    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        super(Skill, self).__init__(name, prop1, prop2, prop3, prop4, prop5)


class Event:
    def __init__(self, id, name, amount, weight):
        self.id = id
        self.name = name
        self.amount = amount
        self.weight = weight


def handle_event(pay_amount, character):
    result = ''
    event_list_j = event_json[str(pay_amount)]
    event_list = []
    weight_list = []
    for event_j in event_list_j:
        event = Event(event_j['id'], event_j['name'], pay_amount, event_j['weight'])
        event_list.append(event)
        weight_list.append(event_j['weight'])
    # 按概率选出是哪个大类的事件
    choice = util.weight_choice(event_list, weight_list)
    my_logger.debug('触发事件前属性: %s' % character)
    my_logger.info('触发事件: %s' % choice.name)

    # TODO: 事件是否需要存进数据库，方便后期统计

    if choice.id == 401:  # 个体-遇怪
        pass
    elif choice.id == 402:  # 个体-物品
        idx = random.randint(0, 1)
        if idx == 0:  # 拾取
            rand_int = random.randint(1, 100)
            if rand_int <= 90:
                # 普通事件
                locations = ['路边', '树林', '衙门口', '肉铺', '荒井边']
                item = util.choice(item_list)
                result += '【{}】在 {} 拾到 {}，{}\n'.format(character.name, util.choice(locations), item.name,
                                                       item.property_change())
                character.use_good(item)
            else:
                # 屠龙宝刀
                result += '【{}】在草丛中发现一把绝世好刀，动了动食指，点击一下，获得屠龙宝刀。\n【{}】攻击+15，运+15，魅力+10\n'.format(character.name,
                                                                                               character.name)
                character.prop1 += 15
                character.prop4 += 15
                character.prop5 += 10
        else:  # 交易
            locations = ['店里', '小摊', '行脚商', '毛头小孩']
            location = util.choice(locations)
            equipment = util.choice(equipment_list)
            rand_int = random.randint(1, 100)
            if rand_int <= 90:
                # 普通事件
                result += '在 {} 处购得{}，{}\n'.format(character.name, location, equipment.name,
                                                   equipment.property_change())
                character.use_good(equipment_list)
            else:
                # 假货
                result += '在 {} 处购得{}，不料过了半日才发现竟是被奸商所骗，{}竟是赝品，运-8\n'.format(character.name, location, equipment.name,
                                                   equipment.name)
                character.prop4 -= 8
        save_character(character)
    elif choice.id == 403:  # 互动-相识
        all_character = get_all_character()
        rand_character = util.choice(all_character)
        result += '【{}】在 酒肆/茶馆/驿站 与一陌生公子交谈甚欢，问得其名为【{}】，两人因此相识。\n'.format(character.name, rand_character.name)
    elif choice.id == 404:  # 互动-交恶
        all_character = get_all_character()
        rand_character = util.choice(all_character)
        result += '{}正要拿起包子铺里的最后一个包子，却被{}抢了先，于是二人结仇。\n'.format(character.name, rand_character.name)
    elif choice.id == 405:  # 互动-PK
        all_character = get_all_character()
        rand_character = util.choice(all_character)

        word_list = [
            '【{}】在市集散步，突然被【{}】踩了脚，两人发生争执，兵刃相向。\n'.format(character.name, rand_character.name),
            '【{}】在雨天步行赶路，【{}】骑马奔驰溅了他一身泥水，两人发生争执，兵刃相向。\n'.format(character.name, rand_character.name)
        ]

        result += util.choice(word_list)

        pk_rst = character.pk(rand_character)
        if pk_rst:
            result += '【{}】武功略胜一筹，心想江湖恩怨也不过如此。【{}】攻+6，防+5，气+5，运+3，魅力+8；【{}】攻-6，防-5，气-5，运-3，魅力-8\n'.format(
                character.name,
                character.name,
                rand_character.name)
            character.use_good(Good('PK失败', 6, 5, 5, 3, 8))
            rand_character.use_good(Good('PK胜利', -6, -5, -5, -3, -8))
        else:
            result += '【{}】在打斗中身负重伤，恩怨情仇总不如命重要，道歉认输便得作罢。【{}】攻-6，防-5，气-5，运-3，魅力-8；【{}】攻+6，防+5，气+5，运+3，魅力+8\n'.format(
                character.name,
                character.name,
                rand_character.name)
            character.use_good(Good('PK失败', -6, -5, -5, -3, -8))
            rand_character.use_good(Good('PK胜利', 6, 5, 5, 3, 8))
    elif choice.id == 301:  # 学艺-基础
        skill = util.choice(skill1_list)
        character.use_good(skill)
        result += '【{}】刻苦修炼，终于习得【{}】，{}\n'.format(character.name, skill.name,
                                                  skill.property_change())
        save_character(character)
    elif choice.id == 302:  # 学艺-进阶
        skill = util.choice(skill2_list)
        character.use_good(skill)
        result += '【{}】刻苦修炼，终于习得【{}】，{}\n'.format(character.name, skill.name,
                                                  skill.property_change())
        save_character(character)
    elif choice.id == 201:  # 门派
        mentor = util.choice(SCHOOLS)
        result += '【{}】骨骼精奇天资聪慧，{}对他青睐有加，亲自传授本门武功。\n【{}】获得真传，攻+35，防+30，气+30，运+20，魅力+40\n'.format(character.name,
                                                                                                 mentor, character.name)
        character.prop1 += 35
        character.prop2 += 30
        character.prop3 += 30
        character.prop4 += 20
        character.prop5 += 40
        save_character(character)
    elif choice.id == 101:  # 其他-得子
        name = ['子', '女', '哪吒']
        result += '行走江湖，总有意外，【{}】十月怀胎，诞下一{}。\n'.format(character.name, util.choice(name))
    elif choice.id == 102:  # 其他-称号升级
        result += '【{}】武功日益精进，救死扶伤匡扶正义，昔日的【无名小侠】如今已【名震江湖】，魅力+88\n'.format(character.name, )
        character.prop5 += 88
        save_character(character)
    my_logger.debug('触发事件后属性: %s' % character)
    return result


def created(modian_id):
    """
    是否创建人物，以摩点id判断
    :param modian_id: 摩点id
    :return:
    """
    my_logger.info('查询人物是否创建，modian_id: %s' % modian_id)
    rst = mysql_util.select_one("""
        SELECT * FROM `t_character` WHERE modian_id=%s
    """, (modian_id,))
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
    report_str += '%s的武侠世界开启, 属性：\n攻: %s, 防: %s, 气: %s, 运: %s, 魅力: %s\n' % (
        random_name, prop1, prop2, prop3, prop4, prop5)
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


def save_character(character):
    """
    将更新后的任务保存到数据库
    :param character:
    :return:
    """
    my_logger.debug('将更新后的任务保存到数据库')
    mysql_util.query("""
        UPDATE `t_character` SET `name`=%s, `prop1`=%s, `prop2`=%s, `prop3`=%s, `prop4`=%s, `prop5`=%s
            WHERE `modian_id`=%s
    """, (character.name, character.prop1, character.prop2, character.prop3, character.prop4, character.prop5,
          character.id))


def get_all_character():
    """
    获取所有人物
    :return:
    """
    my_logger.info('获取所有人物')
    rst = mysql_util.select_all("""
            SELECT * from `t_character`;
        """)
    character_list = []
    if rst:
        for a in rst:
            character = Character(a[0], str(a[1], encoding='utf-8'), int(a[2]), int(a[3]),
                                  int(a[4]), int(a[5]), int(a[6]))
            character_list.append(character)
    return character_list


def read_skill_list():
    # 读取招式列表
    skill1_raw = util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'skill1.txt'))
    skill2_raw = util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'skill2.txt'))
    skill1_list = []
    skill2_list = []
    for line in skill1_raw:
        strs = line.split(',')
        skill = Skill(strs[0], int(strs[1]), int(strs[2]), int(strs[3]), int(strs[4]), int(strs[5]))
        skill1_list.append(skill)
    for line in skill2_raw:
        strs = line.split(',')
        skill = Skill(strs[0], int(strs[1]), int(strs[2]), int(strs[3]), int(strs[4]), int(strs[5]))
        skill2_list.append(skill)
    return skill1_list, skill2_list


def read_equipments_list():
    equipment_raw = util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'equipments.txt'))
    equipment_list = []
    for line in equipment_raw:
        strs = line.split(',')
        equipment = Equipment(strs[0], int(strs[1]), int(strs[2]), int(strs[3]), int(strs[4]), int(strs[5]))
        equipment_list.append(equipment)
    return equipment_list


def read_item_list():
    item_raw = util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'items.txt'))
    item_list = []
    for line in item_raw:
        strs = line.split(',')
        item = Item(strs[0], int(strs[1]), int(strs[2]), int(strs[3]), int(strs[4]), int(strs[5]))
        item_list.append(item)
    return item_list


TOTAL_NAMES = set(util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'names.txt')))
event_json = json.load(open(os.path.join(BASE_DIR, 'data', 'wuxia', 'event.json'), encoding='utf-8'))
SCHOOLS = util.read_txt(os.path.join(BASE_DIR, 'data', 'wuxia', 'school.txt'))
skill1_list, skill2_list = read_skill_list()
equipment_list = read_equipments_list()
item_list = read_item_list()
sync_names()

if __name__ == '__main__':
    # sync_names()
    print(create_character('123456'))
