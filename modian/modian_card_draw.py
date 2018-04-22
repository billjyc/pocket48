# -*- coding: utf-8 -*-
import os
import json
from log.my_logger import modian_logger as logger
from utils import util
from utils.mysql_util import MySQLUtil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Card:
    def __init__(self, id, name, url, level):
        self.id = id
        self.name = name
        self.url = url
        self.level = level

    def __repr__(self):
        return "<Card {id: %s, name: %s, url: %s}>" % (self.id, self.name, self.url)

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(str(self.id) + self.name + self.url + str(self.level))


class CardDrawHandler:
    def __init__(self):
        self.mysql_util = MySQLUtil()
        # self.read_config()

    def read_config(self):
        config_path = os.path.join(BASE_DIR, 'data/card_draw.json')
        card_draw_json = json.load(open(config_path, encoding='utf8'))
        self.min_amount = card_draw_json['min_amount']
        self.base_cards = []
        self.cards = []
        self.weight = []
        for card_j in card_draw_json['cards']:
            card = Card(card_j['id'], card_j['name'], card_j['url'], card_j['level'])
            # 更新数据库中的卡牌信息
            self.mysql_util.query("""
                        INSERT INTO `card` (`id`, `name`, `url`, `level`) VALUES (%s,'%s','%s',%s)  ON DUPLICATE KEY
                                                UPDATE `name`='%s', `url`='%s', `level`=%s
                        """ % (card.id, card.name, card.url, card.level, card.name, card.url, card.level))
            self.cards.append(card)
            if card_j['level'] == 1:
                self.weight.append(card_j['weight'])
                self.base_cards.append(card)

    def draw(self, user_id, nickname, backer_money, pay_time):
        logger.info('抽卡: user_id: %s, nickname: %s, backer_money: %s, pay_time: %s',
                    user_id, nickname, backer_money, pay_time)
        # 计算抽卡张数
        card_num = util.compute_stick_num(self.min_amount, backer_money)

        if card_num == 0:
            logger.info('集资未达到标准，无法抽卡')
            return []

        logger.info('共抽卡%d张', card_num)
        rst = {}
        # 每次需要更新一下昵称
        self.mysql_util.query("""
                        INSERT INTO `supporter` (`id`, `name`) VALUES (%s, '%s')  ON DUPLICATE KEY
                            UPDATE `name`='%s'
                    """ % (user_id, nickname, nickname))

        insert_sql = 'INSERT INTO `draw_record` (`supporter_id`, `card_id`, `draw_time`) VALUES '
        for no in range(card_num):
            card_index = util.weight_choice(self.base_cards, self.weight)
            card = self.base_cards[card_index]
            insert_sql += '(%s, %s, \'%s\'),' % (user_id, card.id, pay_time)

            if card in rst:
                rst[card] += 1
            else:
                rst[card] = 1
        self.mysql_util.query(insert_sql[:-1])
        return rst


if __name__ == '__main__':
    handler = CardDrawHandler()
    rst = handler.draw('123', 'billjyc1', 2, '2018-03-24 12:54:00')
    print(rst)
