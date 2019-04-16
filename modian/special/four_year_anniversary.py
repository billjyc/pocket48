# -*- coding:utf-8 -*-
"""
出道4周年纪念活动
双方每10.17元集资记1积分，灰灰方41.7元为5分，款款则是101.7元为12分，最后积分多的一方获得本次pk的胜利
"""
from utils.mysql_util import mysql_util
import logging
from utils import util

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)
import time


HUIHUI_PRO_ID = 57083
KUANKUAN_PRO_ID = 57085

HUIHUI_AMOUNT = 41.7
KUANKUAN_AMOUNT = 101.7


def plus_huihui_points(amount, pro_id, user_id, order_id):
    """
    灰灰阵营加分, 灰灰方41.7元为5分
    :param amount:
    :param pro_id:
    :param user_id:
    :param order_id:
    :return:
    """
    my_logger.info('[四周年]灰灰阵营集资，id: {}, 金额：{}'.format(user_id, amount))
    if amount < 10.17:
        points = 0
    elif 10.17 <= amount < HUIHUI_AMOUNT:
        points = int(amount // 10.17)
    else:
        points = int(amount // HUIHUI_AMOUNT) * 5 + int(amount % HUIHUI_AMOUNT // 10.17)
    my_logger.info('[四周年]灰灰阵营加分: {}'.format(points))
    # 存入数据库
    mysql_util.query("""
                    insert into `point_detail` (`order_id`, `pro_id`, `point`) VALUES (%s, %s, %s)
                """, (order_id, pro_id, points))
    return points


def plus_kuankuan_points(amount, pro_id, user_id, order_id):
    """
    灰灰阵营加分, 灰灰方41.7元为5分
    :param amount:
    :param pro_id:
    :param user_id:
    :param order_id:
    :return:
    """
    my_logger.info('[四周年]款款阵营集资，id: {}, 金额：{}'.format(user_id, amount))
    if amount < 10.17:
        points = 0
    elif 10.17 <= amount < KUANKUAN_AMOUNT:
        points = int(amount // 10.17)
    else:
        points = int(amount // KUANKUAN_AMOUNT) * 12 + int(amount % KUANKUAN_AMOUNT // 10.17)
    my_logger.info('[四周年]款款阵营加分: {}'.format(points))
    # 存入数据库
    mysql_util.query("""
                    insert into `point_detail` (`order_id`, `pro_id`, `point`) VALUES (%s, %s, %s)
                """, (order_id, pro_id, points))
    return points


def compute_points(pro_id):
    my_logger.info('[四周年]计算总分, pro_id=%s' % pro_id)
    # 总分
    rst = mysql_util.select_one("""
                SELECT SUM(`point`) from `point_detail` WHERE `pro_id`=%s
            """, (pro_id,))
    point = rst[0] if rst[0] else 0
    my_logger.info('[四周年]总分: %s' % point)
    return point


def compute_total_points():
    """
    计算双方阵营总分
    :return:
    """
    my_logger.info('[四周年]计算总积分')
    kuankuan_point = compute_points(KUANKUAN_PRO_ID)
    huihui_point = compute_points(HUIHUI_PRO_ID)
    my_logger.info('[四周年]款款阵营积分：{}'.format(kuankuan_point))
    my_logger.info('[四周年]灰灰阵营积分：{}'.format(huihui_point))
    return kuankuan_point, huihui_point