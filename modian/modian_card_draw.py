# -*- coding: utf-8 -*-
import os
import json
from utils import util
import logging
from utils.mysql_util import mysql_util
try:
    from log.my_logger import modian_logger as logger
except:
    logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Card:
    def __init__(self, id, name, url, level):
        self.id = id
        self.name = name
        self.url = url
        self.level = level

    def __repr__(self):
        return "<Card {id: %s, name: %s, url: %s, level: %s}>" % (self.id, self.name, self.url, self.level)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(str(self.id) + self.name + self.url + str(self.level))


class CardDrawHandler:
    def __init__(self):
        pass
        # self.mysql_util = MySQLUtil()
        # self.read_config()

    def read_config(self):
        config_path = os.path.join(BASE_DIR, 'data/card_draw.json')
        card_draw_json = json.load(open(config_path, encoding='utf8'))
        self.min_amount = card_draw_json['min_amount']
        self.base_cards = []  # 基本卡
        self.cards = {}  # 所有卡
        self.weight = []
        for card_j in card_draw_json['cards']:
            card = Card(card_j['id'], card_j['name'], card_j['url'], card_j['level'])
            # 更新数据库中的卡牌信息
            mysql_util.query("""
                        INSERT INTO `card` (`id`, `name`, `url`, `level`) VALUES (%s, %s, %s, %s)  ON DUPLICATE KEY
                                                UPDATE `name`=%s, `url`=%s, `level`=%s
                        """, (card.id, card.name, card.url, card.level, card.name, card.url, card.level))
            if card.level not in self.cards.keys():
                self.cards[card.level] = []
            self.cards[card.level].append(card)
            if card_j['level'] == 1:
                self.weight.append(card_j['weight'])
                self.base_cards.append(card)

    def can_draw(self):
        """
        是否可以抽中卡, 概率1/5
        :return:
        """
        candidates = [i for i in range(5)]
        rst = util.choice(candidates)
        logger.debug('是否抽中卡: %s' % (rst[0] < 1))
        return rst[0] < 1

    def draw(self, user_id, nickname, backer_money, pay_time):
        logger.info('抽卡: user_id: %s, nickname: %s, backer_money: %s, pay_time: %s',
                    user_id, nickname, backer_money, pay_time)
        # 计算抽卡张数
        card_num = util.compute_stick_num(self.min_amount, backer_money)

        if card_num == 0:
            logger.info('集资未达到标准，无法抽卡')
            return None

        logger.info('共抽卡%d张', card_num)
        rst = {}
        # 每次需要更新一下昵称
        mysql_util.query("""
                        INSERT INTO `supporter` (`id`, `name`) VALUES (%s, %s)  ON DUPLICATE KEY
                            UPDATE `name`= %s
                    """, (user_id, nickname, nickname))

        insert_sql = 'INSERT INTO `draw_record` (`supporter_id`, `card_id`, `draw_time`) VALUES '
        flag = False
        for no in range(card_num):
            # 先判断能否抽中卡，如果抽不中，直接跳过
            draw_rst = self.can_draw()
            if not draw_rst:
                continue
            flag = True
            card_index = util.weight_choice(self.base_cards, self.weight)
            card = self.base_cards[card_index]
            insert_sql += '(%s, %s, \'%s\'),' % (user_id, card.id, pay_time)

            if card in rst:
                rst[card] += 1
            else:
                rst[card] = 1
        if flag:  # 如果一张都没有抽中，就不执行sql语句
            mysql_util.query(insert_sql[:-1])
        return rst

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
            """, (raw_material.id, ))
        # 从高1级的卡中获得一张
        new_card = util.choice(self.cards[raw_material_level+1])
        logger.debug('合成的新卡: %s' % new_card)
        mysql_util.query("""
            INSERT INTO `draw_record` (`supporter_id`, `card_id`, `draw_time`, `is_valid`) VALUES
                (%s, %s, %s, %s)
        """, (user_id, new_card.id, pay_time, 1))
        logger.info('合卡完成')


if __name__ == '__main__':
    handler = CardDrawHandler()
    handler.read_config()
    rst = handler.draw('123', 'billjyc1', 200, '2018-03-24 12:54:00')
    print(rst)
