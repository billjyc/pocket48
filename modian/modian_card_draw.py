# -*- coding: utf-8 -*-
import os
import json
from utils import util
import logging
from utils.mysql_util import mysql_util
from enum import Enum

try:
    from log.my_logger import modian_logger as logger
except:
    logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTIVITY_CARD_ID = [32, 33, 34, 35, 36]


class CardType(Enum):
    """
    卡片种类：日，月，星, 特殊
    """
    SUN = 1
    MOON = 2
    STAR = 3
    SPECIAL = 4


class CardLevel(Enum):
    SR = 1
    SSR = 2
    UR = 3


class Card:
    def __init__(self, id, name, type0, level, sub_id, url, is_valid=1):
        self.id = id
        self.name = name
        self.type0 = type0
        self.level = level
        self.sub_id = sub_id  # 组下的id
        self.url = url
        self.is_valid = is_valid

    def img_path(self):
        return os.path.join(BASE_DIR, 'imgs', self.id, '.jpg')

    def __repr__(self):
        return "<Card {id: %s, name: %s, type: %s, level: %s, sub_id: %s, is_valid: %s}>" % (self.id, self.name,
                                                                                             self.type0, self.level,
                                                                                             self.sub_id, self.is_valid)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(str(self.id) + self.name + str(self.level))


class CardDrawHandler:
    def __init__(self):
        pass
        # self.mysql_util = MySQLUtil()
        # self.read_config()

    def read_config(self):
        config_path = os.path.join(BASE_DIR, 'data/card_draw/cards.txt')
        weight_path = os.path.join(BASE_DIR, 'data/card_draw/weight.txt')
        card_datas = util.read_txt(config_path)
        weight_datas = util.read_txt(weight_path)[0]
        self.weights = []  # SR,SSR,UR卡的概率
        self.cards = {}  # 所有卡，按等级分，不包含已过期卡牌
        self.all_cards = {} # 所有卡，按等级分，包含已下架卡牌
        self.cards_single = {}  # 根据ID查询卡

        for line in card_datas:
            strs = line.split(',')
            card = Card(int(strs[0]), strs[3], CardType(int(strs[2])), CardLevel(int(strs[1])), int(strs[4]), strs[5])
            if card.level not in self.cards:
                self.cards[card.level] = []
            if card.level not in self.all_cards:
                self.all_cards[card.level] = []
            self.all_cards[card.level].append(card)
            self.cards_single[card.id] = card
            if int(strs[6]) == 0:  # 如果卡片无效，则跳过
                continue
            self.cards[card.level].append(card)

        logger.debug(self.cards)

        strs = weight_datas.split(',')
        for weight in strs:
            self.weights.append(float(weight))

        # card_draw_json = json.load(open(config_path, encoding='utf8'))
        # self.min_amount = card_draw_json['min_amount']
        # self.base_cards = []  # 基本卡
        # self.cards = {}  # 所有卡
        # self.weight = []
        # for card_j in card_draw_json['cards']:
        #     card = Card(card_j['id'], card_j['name'], card_j['url'], card_j['level'])
        #     # 更新数据库中的卡牌信息
        #     mysql_util.query("""
        #                 INSERT INTO `card` (`id`, `name`, `url`, `level`) VALUES (%s, %s, %s, %s)  ON DUPLICATE KEY
        #                                         UPDATE `name`=%s, `url`=%s, `level`=%s
        #                 """, (card.id, card.name, card.url, card.level, card.name, card.url, card.level))
        #     if card.level not in self.cards.keys():
        #         self.cards[card.level] = []
        #     self.cards[card.level].append(card)
        #     if card_j['level'] == 1:
        #         self.weight.append(card_j['weight'])
        #         self.base_cards.append(card)

    def compute_draw_nums(self, backer_money):
        """
        计算抽卡张数
        每集资10.17抽一张
        集资达到101.7抽11张
        :param backer_money:
        :return:
        """
        if backer_money < 10.17:
            return 0
        elif backer_money < 101.7:
            return int(backer_money // 10.17)
        else:
            tmp1 = int(backer_money // 101.7) * 11
            tmp2 = int((backer_money % 101.7) // 10.17)
            return tmp1 + tmp2

    def can_draw(self):
        """
        是否可以抽中卡, 概率1/3
        :return:
        """
        candidates = [i for i in range(3)]
        rst = util.choice(candidates)
        logger.debug('是否抽中卡: %s' % (rst[0] < 1))
        return rst[0] < 1

    def draw(self, user_id, nickname, backer_money, pay_time):
        logger.info('抽卡: user_id: %s, nickname: %s, backer_money: %s, pay_time: %s',
                    user_id, nickname, backer_money, pay_time)
        # 计算抽卡张数
        card_num = self.compute_draw_nums(backer_money)

        if card_num == 0:
            logger.info('集资未达到标准，无法抽卡')
            return ''

        logger.info('共抽卡%d张', card_num)
        rst = {}
        rst_type = {}
        rst_level = {}
        level_list = [CardLevel.SR, CardLevel.SSR, CardLevel.UR]
        type_dict = {
            CardType.STAR: '星组',
            CardType.MOON: '月组',
            CardType.SUN: '日组',
            CardType.SPECIAL: '活动限定'
        }

        # 获取此ID已抽中的全部卡牌
        rst_tmp = mysql_util.select_all("""
            SELECT distinct(`card_id`) from `draw_record` where supporter_id=%s
        """, (user_id,))
        card_has = set()
        if rst_tmp and len(rst_tmp) > 0:
            for tmp in rst_tmp:
                card_has.add(tmp[0])
        logger.debug('摩点ID: {}, 当前拥有的卡片: {}'.format(user_id, card_has))
        score_add = 0

        insert_sql = 'INSERT INTO `draw_record` (`supporter_id`, `card_id`, `draw_time`, `backer_money`) VALUES '
        flag = False
        for no in range(card_num):
            # 先判断能否抽中卡，如果抽不中，直接跳过
            # draw_rst = self.can_draw()
            # if not draw_rst:
            #     continue
            flag = True
            # 卡片类型
            idx = util.weight_choice(level_list, self.weights)
            card_type = level_list[idx]

            # 在对应卡片类型中，抽出一张卡
            card = util.choice(self.cards[card_type])[0]
            logger.debug('抽出的卡: %s' % card)

            if card.id in card_has:
                logger.debug('卡片{}已经拥有，积分+1')
                # 如果已经拥有该卡片，积分+1
                score_add += 1

            card_has.add(card.id)

            # card = self.base_cards[card_index]
            insert_sql += '(%s, %s, \'%s\', %s),' % (user_id, card.id, pay_time, backer_money)

            # 此种类型的卡如果已经达到了2张，则将该卡片从卡池中移除
            if card.id in ACTIVITY_CARD_ID:
                rst = mysql_util.select_one("""
                    SELECT count(*) from `draw_record` WHERE `card_id` = %s
                """, (card.id,))
                if rst[0] == 2:
                    if card in self.cards[card.level]:
                        self.cards[card.level].remove(card)

            if card in rst:
                rst[card] += 1
            else:
                rst[card] = 1

            if card.level not in rst_level:
                rst_level[card.level] = []
            if card not in rst_level[card.level]:
                rst_level[card.level].append(card)

            if card.type0 not in rst_type:
                rst_type[card.type0] = []
            if card not in rst_type[card.type0]:
                rst_type[card.type0].append(card)
        print(insert_sql[:-1])
        logger.debug(insert_sql[:-1])

        img_flag = True
        img_report = ''
        report = '恭喜抽中:\n'
        if CardLevel.UR in rst_level and len(rst_level[CardLevel.UR]) > 0:
            report += '【UR】: '
            for card in rst_level[CardLevel.UR]:
                report += '{}-{}*{}, '.format(type_dict[card.type0], card.name, rst[card])
            if img_flag:
                img = util.choice(rst_level[CardLevel.UR])[0]
                img_report = '[CQ:image,file={}]\n'.format(img.url)
                img_flag = False
            report += '\n'
        if CardLevel.SSR in rst_level and len(rst_level[CardLevel.SSR]) > 0:
            report += '【SSR】: '
            for card in rst_level[CardLevel.SSR]:
                report += '{}-{}*{}, '.format(type_dict[card.type0], card.name, rst[card])
            if img_flag:
                img = util.choice(rst_level[CardLevel.SSR])[0]
                img_report = '[CQ:image,file={}]\n'.format(img.url)
                img_flag = False
            report += '\n'
        if CardLevel.SR in rst_level and len(rst_level[CardLevel.SR]) > 0:
            report += '【SR】: '
            for card in rst_level[CardLevel.SR]:
                report += '{}{}*{}, '.format(type_dict[card.type0], card.sub_id, rst[card])
            if img_flag:
                img = util.choice(rst_level[CardLevel.SR])[0]
                img_report = '[CQ:image,file={}]\n'.format(img.url)
                img_flag = False
            report += '\n'

        report += img_report

        if flag:  # 如果一张都没有抽中，就不执行sql语句
            mysql_util.query(insert_sql[:-1])

        # 积分保存到数据库
        if score_add > 0:
            mysql_util.query("""
                INSERT INTO `t_card_score` (`modian_id`, `score`) VALUES 
                    (%s, %s)
            """, (user_id, score_add))
            report += '通过重复卡获取积分: {}\n'.format(score_add)
        report += '当前积分为: {}\n'.format(self.get_current_score(user_id))
        logger.debug(report)
        return report

    def get_cards(self, modian_id):
        """
        获取该人所有已抽中的卡
        :param modian_id:
        :return:
        """
        logger.info("查询已抽中的卡: {}".format(modian_id))
        rst = mysql_util.select_all("""
            select card_id, count(*) from `draw_record` where supporter_id=%s group by `card_id`;
        """, (modian_id,))
        rst_level = {}
        rst_level[CardLevel.UR] = []
        rst_level[CardLevel.SSR] = []
        rst_level[CardLevel.SR] = []
        rst_num = {}
        type_dict = {
            CardType.STAR: '星组',
            CardType.MOON: '月组',
            CardType.SUN: '日组',
            CardType.SPECIAL: '活动限定',
        }
        if rst and len(rst) > 0:
            logger.debug(rst)
            for tmp in rst:
                card = self.cards_single[int(tmp[0])]
                if card not in rst_level[card.level]:
                    rst_level[card.level].append(card)
        else:
            return '摩点ID: {}, 当前暂未抽中任何卡片 \n'.format(modian_id)
        logger.debug(rst_level)
        logger.debug(rst_num)
        report = '摩点ID: {}, 当前已抽中的卡片有: \n'.format(modian_id)
        if CardLevel.UR in rst_level and len(rst_level[CardLevel.UR]) > 0:
            report += '【UR】({}/{}): '.format(len(rst_level[CardLevel.UR]), len(self.all_cards[CardLevel.UR]))
            for card in rst_level[CardLevel.UR]:
                report += '{}-{}, '.format(type_dict[card.type0], card.name)
            report += '\n'
        logger.debug(report)
        if CardLevel.SSR in rst_level and len(rst_level[CardLevel.SSR]) > 0:
            report += '【SSR】({}/{}): '.format(len(rst_level[CardLevel.SSR]), len(self.all_cards[CardLevel.SSR]))
            for card in rst_level[CardLevel.SSR]:
                report += '{}-{}, '.format(type_dict[card.type0], card.name)
            report += '\n'
        logger.debug(report)
        if CardLevel.SR in rst_level and len(rst_level[CardLevel.SR]) > 0:
            report += '【SR】({}/{}): '.format(len(rst_level[CardLevel.SR]), len(self.all_cards[CardLevel.SR]))
            for card in rst_level[CardLevel.SR]:
                report += '{}{}, '.format(type_dict[card.type0], card.sub_id)
            report += '\n'
        current_score = self.get_current_score(modian_id)
        report += '当前积分为: {}\n'.format(current_score)
        logger.debug(report)
        return report

    def evolution(self, raw_list, user_id, pay_time):
        """
        进化（吞噬）
        :param raw_list: 原材料，只能为同等级的材料
        :return:
        """
        if (not raw_list) or len(raw_list) == 0:
            logger.exception('原材料为空！')
            raise RuntimeError('原材料列表为空')
        raw_material_level = raw_list[0].level
        if raw_material_level + 1 not in self.cards.keys():
            logger.info('已经是最高级的卡牌，不能合成')
            return None
        logger.info('删除原材料')
        # 删除原材料
        for raw_material in raw_list:
            mysql_util.query("""
                UPDATE `draw_record` SET is_valid=0 WHERE id=%s
            """, (raw_material.id,))
        # 从高1级的卡中获得一张
        new_card = util.choice(self.cards[raw_material_level + 1])
        logger.debug('合成的新卡: %s' % new_card)
        mysql_util.query("""
            INSERT INTO `draw_record` (`supporter_id`, `card_id`, `draw_time`, `is_valid`) VALUES
                (%s, %s, %s, %s)
        """, (user_id, new_card.id, pay_time, 1))
        logger.info('合卡完成')

    def get_current_score(self, modian_id):
        """
        获取当前积分
        :param modian_id:
        :return:
        """
        logger.debug('获取当前积分: {}'.format(modian_id))
        score = 0
        rst = mysql_util.select_one("""
            SELECT CONCAT(SUM(`score`)) FROM `t_card_score` WHERE `modian_id`=%s
        """, (modian_id,))
        if rst and len(rst) > 0:
            if rst[0] is not None:
                logger.debug('current score: {}'.format(rst[0]))
                score = str(rst[0], encoding='utf-8')
        print(score)
        return score

    def draw_missed_cards(self, modian_id, score=10):
        """
        补抽卡
        :param modian_id:
        :param score: 抽卡消耗的积分数量
        :return:
        """
        logger.info('积分抽卡，modian_id:{}, score:{}'.format(modian_id, score))
        import time
        if score < 15:
            return '消耗的积分必须要大于等于15！'
        if score % 15 != 0:
            return '消耗的积分必须是15的倍数！'
        current_score = int(self.get_current_score(modian_id))
        if current_score < score:
            return '摩点ID：{}的当前积分: {}，少于需要消耗的积分: {}，不能补抽！'.format(modian_id, current_score, score)
        else:
            result = '摩点ID：{}，积分抽卡，当前积分-{}\n'.format(modian_id, score)
            mysql_util.query("""
                            INSERT INTO `t_card_score` (`modian_id`, `score`) VALUES 
                                (%s, %s)
                        """, (modian_id, -1 * score))
            money = int(score // 10) * 10.17
            result += self.draw(modian_id, '补抽用户', money, util.convert_timestamp_to_timestr(int(time.time() * 1000)))
            return result


handler = CardDrawHandler()

if __name__ == '__main__':
    # handler = CardDrawHandler()
    # handler.read_config()
    # rst = handler.draw('1236666', 'billjyc1', 200, '2018-03-24 12:54:00')
    # print(rst)
    # handler.draw_missed_cards('1236666')
    # handler.get_current_score('1236666')
    pass
