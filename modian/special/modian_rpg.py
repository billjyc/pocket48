# -*- coding:utf-8 -*-
"""
款款的魔法世界特别活动
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
from enum import Enum


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class Point:
    """
    地图上的点
    """

    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y

    def __str__(self):
        return 'Point[{}, {}]'.format(self.x, self.y)


class Map:
    """
    地图实例
    """

    def __init__(self, row, col):
        self.row = row
        self.col = col


MAP_ROW = 50
MAP_COL = 50
GAME_MAP = Map(MAP_ROW, MAP_COL)


class Character:
    """
    人物（棋子）
    """

    def __init__(self, modian_id, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        self.map = map
        self.current_point = Point(0, 0)  # 初始起点
        self.id = modian_id
        self.name = name
        self.prop1 = prop1  # 精神
        self.prop2 = prop2  # 专注
        self.prop3 = prop3  # 智慧
        self.prop4 = prop4  # 运气
        self.prop5 = prop5  # 魅力
        self.num_of_fragment = 0  # 梦之碎片数量
        self.map = GAME_MAP

    def move(self, direction, dist):
        """
        在棋盘上移动
        :param direction: 方向
        :param dist: 移动距离
        :return:
        """
        my_logger.info('移动前坐标: {}'.format(self.current_point))
        my_logger.info('移动方向: {}, 距离: {}'.format(direction, dist))
        print('移动前坐标: {}'.format(self.current_point))
        print('移动方向: {}, 距离: {}'.format(direction, dist))
        if direction == Direction.UP:
            self.current_point.y = (self.current_point.y - dist) % GAME_MAP.row
        elif direction == Direction.DOWN:
            self.current_point.y = (self.current_point.y + dist) % GAME_MAP.row
        elif direction == Direction.LEFT:
            self.current_point.x = (self.current_point.x - dist) % GAME_MAP.col
        elif direction == Direction.RIGHT:
            self.current_point.x = (self.current_point.x + dist) % GAME_MAP.col
        my_logger.info('移动后坐标: {}'.format(self.current_point))
        print('移动后坐标: {}'.format(self.current_point))

    def __str__(self):
        return """Character[modian_id=%s, name=%s, 精神=%s, 专注=%s, 智慧=%s, 运气=%s, 魅力=%s],
                    当前位置: %s, 梦之碎片个数: %s""" % (self.id, self.name, self.prop1, self.prop2, self.prop3,
                                                      self.prop4,
                                                      self.prop5, self.current_point, self.num_of_fragment)

    def return_to_origin(self):
        """
        回到原点
        :return:
        """
        self.current_point = Point(0, 0)

    def random_move(self):
        """
        随机移动
        :return:
        """
        ds = [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]
        random_direction = util.choice(ds)[0]
        random_dist = random.randint(1, GAME_MAP.row)
        my_logger.info('随机移动')
        result = '移动方向: {}, 移动距离: {}, '.format(random_direction, random_dist)
        self.move(random_direction, random_dist)
        result += '当前位置: {}\n'.format(self.current_point)
        return result

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
        self.prop1 = prop1  # 精神
        self.prop2 = prop2  # 专注
        self.prop3 = prop3  # 智慧
        self.prop4 = prop4  # 运气
        self.prop5 = prop5  # 魅力

    def __str__(self):
        return 'Good[name=%s, 精神=%s, 专注=%s, 智慧=%s, 运气=%s, 魅力=%s]' % (self.name, self.prop1,
                                                                 self.prop2, self.prop3,
                                                                 self.prop4, self.prop5)

    def property_change(self):
        property_change_str = ''
        if self.prop1 != 0:
            property_change_str += '精神+%s, ' % self.prop1 if self.prop1 >= 0 else '精神%s, ' % self.prop1
        if self.prop2 != 0:
            property_change_str += '专注+%s, ' % self.prop2 if self.prop2 >= 0 else '专注%s, ' % self.prop2
        if self.prop3 != 0:
            property_change_str += '智慧+%s, ' % self.prop3 if self.prop3 >= 0 else '智慧%s, ' % self.prop3
        if self.prop4 != 0:
            property_change_str += '运气+%s, ' % self.prop4 if self.prop4 >= 0 else '运气%s, ' % self.prop4
        if self.prop5 != 0:
            property_change_str += '魅力+%s, ' % self.prop5 if self.prop5 >= 0 else '魅力%s, ' % self.prop5
        if len(property_change_str) > 0:
            return property_change_str[:-1]
        else:
            return property_change_str


class Equipment(Good):
    """
    装备类物品
    """

    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        super(Equipment, self).__init__(name, prop1, prop2, prop3, prop4, prop5)


class Item(Good):
    """
    消耗类物品
    """

    def __init__(self, name, prop1=0, prop2=0, prop3=0, prop4=0, prop5=0):
        super(Item, self).__init__(name, prop1, prop2, prop3, prop4, prop5)


class Skill(Good):
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
    if game_is_over(character.id):
        return '游戏结束'
    result = ''
    event_list_j = event_json[str(int(pay_amount))]
    event_list = []
    weight_list = []
    for event_j in event_list_j:
        event = Event(event_j['id'], event_j['name'], pay_amount, event_j['weight'])
        event_list.append(event)
        weight_list.append(event_j['weight'])
    # 按概率选出是哪个大类的事件
    idx = util.weight_choice(event_list, weight_list)
    choice = event_list[idx]
    my_logger.debug('触发事件前属性: %s' % character)
    my_logger.info('触发事件: %s' % choice.name)
    event_id = choice.id
    event_remark = ''

    if choice.id == 401:  # 个体-遇见NPC
        monsters = ['本院教师', '别院教师', '皮皮鬼', '托尼老师', '款款']
        weights = [30, 30, 30, 8, 2]
        hit_idx = util.weight_choice(monsters, weights)
        hit = monsters[hit_idx]
        event_remark = hit
        if hit == '款款':
            # 赠送梦的碎片
            result += '【{}】在身边发现款款！\n款款赠与了一块梦的碎片，并说了声再见。\n【{}】运气+10，魅力+5\n'.format(character.name,
                                                                                                 character.name,
                                                                                                 character.name)
            character.use_good(Good('款款', 0, 0, 0, 10, 5))
            character.num_of_fragment += 1
            event_id = 4011
        else:
            result += '{}突然出现在【{}】附近\n'.format(character.name, hit)
            rand_int = random.randint(1, 100)
            if rand_int <= 75:
                # 75%几率获胜
                result += '运气看来不错，{}并没有看到你。\n【{}】运气+5，专注+3\n'.format(hit, character.name, hit, character.name)
                character.use_good(Good('没有被NPC发现', 0, 3, 0, 5, 0))
                event_id = 4012
            else:
                result += '{}发现你啦，{}被遣送回学院\n运气-2，专注-5，返回出生点\n'.format(hit, character.name, character.name)
                character.use_good(Good('战斗胜利', 0, -5, 0, -2, 0))
                # 返回出生点
                character.return_to_origin()
                event_id = 4013
        result += character.random_move()
        save_character(character)
    elif choice.id == 402:  # 个体-物品
        idx = random.randint(0, 1)
        if idx == 0:  # 拾取
            rand_int = random.randint(1, 100)
            if rand_int <= 90:
                # 普通事件
                locations = ['门后', '台阶', '转角处', '草丛中', '路边']
                item = util.choice(item_list)[0]
                result += '【{}】在 {} 拾到 {}，\n{}\n'.format(character.name, util.choice(locations)[0], item.name,
                                                         item.property_change())
                character.use_good(item)
                event_id = 4021
                event_remark = item.name
            else:
                # 物品2类
                equipment = util.choice(equipment_list)[0]
                result += '{}在无意中发现了什么。去看看。这是什么？\n {}获得了{}精神+15，运气+15，魅力+10'.format(character.name, character.name,
                                                                                      equipment.name)
                # result += '【{}】在草丛中发现一把绝世好刀，动了动食指，点击一下，获得屠龙宝刀。\n【{}】攻击+15，运+15，魅力+10\n'.format(character.name,
                #                                                                                character.name)
                character.prop1 += 15
                character.prop4 += 15
                character.prop5 += 10
                event_id = 4022
                event_remark = equipment.name
        else:  # 交易
            locations = ['商店']
            location = util.choice(locations)[0]
            equipment = util.choice(equipment_list)[0]
            rand_int = random.randint(1, 100)
            if rand_int <= 100:
                # 普通事件
                result += '【{}】在 {} 处购得{}，{}\n'.format(character.name, location, equipment.name,
                                                   equipment.property_change())
                character.use_good(equipment)
                event_id = 4023
                event_remark = equipment.name
            # else:
            #     # 假货
            #     result += '【{}】在 {} 处购得{}，不料过了半日才发现竟是被奸商所骗，{}竟是赝品，运-8\n'.format(character.name, location, equipment.name,
            #                                                                 equipment.name)
            #     character.use_good(Good('奸商', 0, 0, 0, -8, 0))
            #     event_id = 4024
            #     event_remark = equipment.name
        result += character.random_move()
        save_character(character)
    elif choice.id == 403:  # 互动-相识
        all_character = get_all_character()
        rand_character = util.choice(all_character)[0]
        # locations = ['酒肆', '茶馆', '驿站']
        # location = util.choice(locations)[0]
        result += '【{}】在这看到了一个身影，原来也是偷跑出来的【{}】，认识一下吧。\n'.format(character.name, rand_character.name)
        result += character.random_move()
        save_character(character)
        event_remark = rand_character.name
    elif choice.id == 404:  # 互动-交恶
        all_character = get_all_character()
        rand_character = util.choice(all_character)[0]
        result += '【{}】发现，原来这里还有【{}】，不能让他就这么溜过去，让他暴露吧。\n'.format(character.name, rand_character.name)
        result += character.random_move()
        save_character(character)
        event_remark = rand_character.name
    elif choice.id == 405:  # 互动-PK
        all_character = get_all_character()
        rand_character = util.choice(all_character)[0]

        word_list = [
            '【{}】只顾低头行走，被【{}】一头撞上，两人发生争执，要分个高下才肯罢休。\n'.format(character.name, rand_character.name),
            '【{}】和【{}】在城堡里狭路相逢，既然躲不过，那么来较量一下吧。\n'.format(character.name, rand_character.name)
        ]

        event_remark = rand_character.name

        result += util.choice(word_list)[0]

        pk_rst = character.pk(rand_character)
        if pk_rst:
            result += '【{}】魔法略胜一筹，多年的勤学苦练终于派上用场。\n【{}】精神+6，专注+5，智慧+5，运气+3，魅力+8；\n【{}】精神-6，专注-5，智慧-5，运气-3，魅力-8\n'.format(
                character.name,
                character.name,
                rand_character.name)
            character.use_good(Good('PK胜利', 6, 5, 5, 3, 8))
            rand_character.use_good(Good('PK失败', -6, -5, -5, -3, -8))
            event_id = 4051
        else:
            result += '【{}】在较量中棋差一招，只怪自己学艺不精，道歉认输便得作罢。\n【{}】精神-6，专注-5，智慧-5，运气-3，魅力-8；\n【{}】精神+6，专注+5，智慧+5，运气+3，魅力+8\n'.format(
                character.name,
                character.name,
                rand_character.name)
            character.use_good(Good('PK失败', -6, -5, -5, -3, -8))
            rand_character.use_good(Good('PK胜利', 6, 5, 5, 3, 8))
            event_id = 4052
        result += character.random_move()
        save_character(character)
        save_character(rand_character)
    elif choice.id == 406:  # 互动-学院势力
        # TODO
        result += '学院压制'
        event_remark = '学院压制'
        result += character.random_move()
    elif choice.id == 301:  # 学艺-基础
        skill = util.choice(skill1_list)[0]
        character.use_good(skill)
        result += '【{}】刻苦修炼，终于习得【{}】，\n{}\n'.format(character.name, skill.name,
                                                    skill.property_change())
        event_remark = skill.name
        result += character.random_move()
        save_character(character)
    elif choice.id == 302:  # 学艺-进阶
        skill = util.choice(skill2_list)[0]
        character.use_good(skill)
        result += '【{}】刻苦修炼，终于习得【{}】，\n{}\n'.format(character.name, skill.name,
                                                    skill.property_change())
        event_remark = skill.name
        result += character.random_move()
        save_character(character)
    elif choice.id == 201:  # 门派
        mentor = util.choice(SCHOOLS)[0]
        result += '【{}】骨骼精奇天资聪慧，{}对他青睐有加，亲自传授本门武功。\n【{}】获得真传，攻+35，防+30，气+30，运+20，魅力+40\n'.format(character.name,
                                                                                                 mentor, character.name)
        character.prop1 += 35
        character.prop2 += 30
        character.prop3 += 30
        character.prop4 += 20
        character.prop5 += 40
        event_remark = mentor
        result += character.random_move()
        save_character(character)
    elif choice.id == 101:  # 其他-得子
        name = ['子', '女', '哪吒']
        choice_name = util.choice(name)[0]
        result += '行走江湖，总有意外，【{}】十月怀胎，诞下一{}。\n'.format(character.name, choice_name)
        event_remark = choice_name
        result += character.random_move()
        save_character(character)
    elif choice.id == 102:  # 其他-称号升级
        result += '【{}】武功日益精进，救死扶伤匡扶正义，昔日的【无名小侠】如今已【名震江湖】，魅力+88\n'.format(character.name, )
        character.prop5 += 88
        result += character.random_move()
        save_character(character)
        event_remark = '称号升级'
    my_logger.debug('触发事件后属性: %s' % character)
    save_event(character.id, event_id, event_remark)
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
        character = Character(modian_id, str(rst[1], encoding='utf-8'), rst[2], rst[3], rst[4], rst[5], rst[6])
        character.num_of_fragment = rst[7]
        character.current_point = Point(rst[8], rst[9])
        return True, character
    else:
        return False, None


def create_character(modian_id, modian_name):
    """
    创建人物
    :return:
    """
    my_logger.info('创建人物, modian_id: %s' % modian_id)

    # 随机生成属性
    prop1 = random.randint(40, 70)
    prop2 = random.randint(30, 60)
    prop3 = random.randint(5, 20)
    prop4 = random.randint(0, 50)
    prop5 = random.randint(30, 50)
    mysql_util.query("""
        INSERT INTO `t_character` (`modian_id`, `name`, `prop1`, `prop2`, `prop3`, `prop4`, `prop5`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (modian_id, modian_name, prop1, prop2, prop3, prop4, prop5))

    intro_words = [
        "樱桃树绽放出粉红的花朵，当微风吹过的时候，花瓣便在树枝上轻轻抖动，在这段沿盘山的小路上走来一位魔法师，胸前的徽章上似乎是一只小熊猫，那是【{}】。".format(modian_name),
        "一道高大的身影出现在城堡正门前，遮住了门外照进的阳光，他似乎抬头望向了“瘦夫人”的画像，“吾【{}】，请问此处可是“葛绿元少”？”".format(modian_name),
        "纯血即是正义！我是高贵！纯真！有抱负的【{}】，“丝来特别灵”是我的目标".format(modian_name),
        "“啊啊啊啊啊”伴随着一阵高昂的惨叫声，“啦闻唠嗑”的塔楼上方划过一道骑着扫帚的身影。那是！恐高症的【{}】".format(modian_name),
        "⑤	窗外，一阵急促的扑打翅膀的声音传来，一只猫头鹰停在了窗台前，它伸出了左爪将一封有着红色蜡封和盾牌纹章的羊皮信放在了窗台上。【{}】拿起了这封信。".format(modian_name)
    ]
    # 随机挑选一个出场方式
    intro = util.choice(intro_words)
    report_str = '%s\n' % intro[0]
    report_str += '%s的的魔法世界开启, 属性：\n攻: %s, 防: %s, 气: %s, 运: %s, 魅力: %s\n' % (
        modian_name, prop1, prop2, prop3, prop4, prop5)
    return report_str


def donate(modian_id, pay_amount, modian_name):
    MIN_AMOUNT = 10
    times = random.randint(10, 200)
    pay_amount = pay_amount * times
    rst = ''
    has_created, character = created(modian_id)
    if has_created:
        my_logger.info('已经创建了人物: %s' % modian_id)
        # 如果已经创建
        my_logger.debug('%s触发了随机事件（施工中）' % character.name)
        if pay_amount < MIN_AMOUNT:
            return ''
        tmp = pay_amount
        amounts = [200, 100, 50, 20, 10]
        # amounts = [i / 10 for i in amounts]
        max_event = 3  # 最多触发3次事件
        idx = 0
        while max_event > 0 and idx < len(amounts):
            event_time = int(tmp / amounts[idx])
            event_time = max_event if event_time > max_event else event_time
            for i in range(event_time):
                try:
                    sub_event_str = handle_event(amounts[idx], character)
                except Exception as e:
                    my_logger.exception(e)
                rst += sub_event_str
                my_logger.debug(sub_event_str)
                # rst += '----------------------------\n'
            max_event -= event_time
            tmp = tmp % amounts[idx]
            idx += 1
        rst += '【{}】当前属性：\n攻：{}, 防: {}, 气: {}, 运：{}, 魅力: {}\n'.format(character.name, character.prop1,
                                                                         character.prop2, character.prop3,
                                                                         character.prop4, character.prop5)
    else:
        my_logger.info('未创建人物, modian_id: %s' % modian_id)
        if pay_amount >= MIN_AMOUNT:
            rst = create_character(modian_id, modian_name)
    return rst


def save_character(character):
    """
    将更新后的任务保存到数据库
    :param character:
    :return:
    """
    my_logger.debug('将更新后的任务保存到数据库')
    mysql_util.query("""
        UPDATE `t_character` SET `name`=%s, `prop1`=%s, `prop2`=%s, `prop3`=%s, `prop4`=%s, `prop5`=%s, 
        `num_of_fragment`=%s, `loc_x`=%s, `loc_y`=%s
            WHERE `modian_id`=%s
    """, (character.name, character.prop1, character.prop2, character.prop3, character.prop4, character.prop5, character.num_of_fragment,
          character.current_point.x, character.current_point.y, character.id))


def save_event(modian_id, event_id, event_remark):
    """
    保存事件到数据库
    :param modian_id
    :param event_id
    :param event_remark
    :return:
    """
    my_logger.debug('保存事件到数据库')
    mysql_util.query("""
        INSERT INTO `t_event` (`modian_id`, `event_id`, `event_remark`) VALUES 
            (%s, %s, %s)
    """, (modian_id, event_id, event_remark))


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


def game_is_over(modian_id=None):
    """
    游戏是否结束
    :param modian_id: 当前id
    :return:
    """
    # 20个人拥有梦之碎片
    rst = mysql_util.select_one("""
           SELECT count(*) FROM `t_character` WHERE `num_of_fragment`>%s
       """, (0,))
    if rst[0] >= 20:
        return True
    # 该用户拥有7个梦之碎片
    if modian_id:
        rst = mysql_util.select_one("""
                   SELECT `num_of_fragment` FROM `t_character` WHERE `modian_id`=%s
               """, (modian_id,))
        if rst:
            if rst[0] >= 7:
                return True
    return False


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
    equipment_raw = util.read_txt(os.path.join(BASE_DIR, 'data', 'magic', 'equipments.txt'))
    equipment_list = []
    for line in equipment_raw:
        strs = line.split(',')
        equipment = Equipment(strs[0], int(strs[1]), int(strs[2]), int(strs[3]), int(strs[4]), int(strs[5]))
        equipment_list.append(equipment)
    return equipment_list


def read_item_list():
    item_raw = util.read_txt(os.path.join(BASE_DIR, 'data', 'magic', 'items.txt'))
    item_list = []
    for line in item_raw:
        strs = line.split(',')
        item = Item(strs[0], int(strs[1]), int(strs[2]), int(strs[3]), int(strs[4]), int(strs[5]))
        item_list.append(item)
    return item_list


event_json = json.load(open(os.path.join(BASE_DIR, 'data', 'magic', 'event.json'), encoding='utf-8'))
SCHOOLS = util.read_txt(os.path.join(BASE_DIR, 'data', 'magic', 'school.txt'))
skill1_list, skill2_list = read_skill_list()
equipment_list = read_equipments_list()
item_list = read_item_list()


if __name__ == '__main__':
    # game_map = Map(4, 4)
    # c = Character(game_map)
    # c.move(Direction.UP, 1)
    # c.move(Direction.RIGHT, 3)
    # c.move(Direction.LEFT, 4)
    # c.move(Direction.DOWN, 2)
    #
    # rst = mysql_util.select_all("""
    # select s.`name`, tc.`name`, CONVERT((tc.prop1 * 1.5 + tc.prop2 + tc.prop3 * 1.2 + tc.prop5 * 0.9) * (1 + tc.prop4 / 100), SIGNED) as ce
    # from `t_character` tc, `supporter` s where tc.`modian_id` = s.`id`
    # order by ce desc limit 10;
    #         """)
    # print(rst)
    # result_str = ''
    # rank = 1
    # for name, c_name, ce in rst:
    #     result_str += '{}.{}({}): {}\n'.format(rank, str(name, encoding='utf-8'),
    #                                            str(c_name, encoding='utf-8'), ce)
    #     rank += 1
    # print(result_str)
    # sync_names()
    for i in range(10):
        print(donate('123', 10, 'abc123'))
        print(donate('456', 100, 'abc456'))
        print(donate('789', 200, 'abc789'))

