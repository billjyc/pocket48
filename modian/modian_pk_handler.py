# -*- coding:utf-8 -*-
from utils.mysql_util import mysql_util
from log.my_logger import modian_logger as my_logger
import time

MINUS_AMOUNT = 99.9
FXF_PRO_ID = 18966
WJL_PRO_ID = 18954

FXF_MAKE_TROUBLE_POINTS = 9
WJL_MAKE_TROUBLE_POINTS = 5


def minus_points(pro_id, pay_amount):
    """
    扣分
    :param pro_id: 项目id
    :param pay_amount: 金额
    :return:
    """
    my_logger.info('减分, pro_id: %s, pay_amount: %s' % (pro_id, pay_amount))
    point = 0
    if pay_amount == MINUS_AMOUNT:
        if pro_id == FXF_PRO_ID:
            point = FXF_MAKE_TROUBLE_POINTS
            my_logger.info('冯晓菲 扣 汪佳翎%s分' % point)
        elif pro_id == WJL_PRO_ID:
            point = WJL_MAKE_TROUBLE_POINTS
            my_logger.info('汪佳翎 扣 冯晓菲%s分' % point)
    else:
        my_logger.info('不进行扣分计算')
    return point


def plus_points(pro_id, pay_amount):
    """
    加分
    :param pro_id:
    :param pay_amount:
    :return:
    """
    my_logger.info('加分, pro_id: %s, pay_amount: %s' % (pro_id, pay_amount))
    point = 0
    if pro_id == FXF_PRO_ID:
        if pay_amount < 10.17:
            return 0
        elif pay_amount < 50:
            point = 1
        elif pay_amount < 101.7:
            point = 5
        else:
            extra = int((pay_amount - 100) // 10)
            point = 10 + extra
        my_logger.info('冯晓菲 加分%s' % point)

    elif pro_id == WJL_PRO_ID:
        if pay_amount < 7.13:
            return 0
        elif pay_amount < 50:
            point = 1
        elif pay_amount < 71.3:
            point = 7
        else:
            extra = int((pay_amount - 70) // 7)
            point = 10 + extra
        my_logger.info('汪佳翎 加分%s' % point)
    else:
        my_logger.info('不进行加分计算')
    return point


def get_make_trouble_time(pro_id):
    """
    获取捣乱次数
    :param pro_id:
    :return:
    """
    my_logger.info('获取捣乱次数: %s' % pro_id)
    if pro_id == FXF_PRO_ID:
        rst = mysql_util.select_one("""
            SELECT count(*) FROM `order` WHERE `pro_id`=%s and `backer_money`= %s
        """, (FXF_PRO_ID, MINUS_AMOUNT))
        my_logger.info('冯晓菲 捣乱次数: %s' % rst[0])
    elif pro_id == WJL_PRO_ID:
        rst = mysql_util.select_one("""
                    SELECT count(*) FROM `order` WHERE `pro_id`=%s and `backer_money`= %s
                """, (WJL_PRO_ID, MINUS_AMOUNT))
        my_logger.info('汪佳翎 捣乱次数: %s' % rst[0])
    else:
        return 0
    return rst[0]


def get_plus_10_times(pro_id):
    """
    获取给本方加10分操作的次数
    :param pro_id:
    :return:
    """
    # fxf: 集资101.7以上
    # wjl: 集资71.3以上
    # 每5次捣乱 +10分
    my_logger.info('获取给本方加10分的次数，pro_id: %s' % pro_id)
    if pro_id == FXF_PRO_ID:
        rst = mysql_util.select_one("""
            SELECT count(*) FROM `order` WHERE `pro_id`=%s and `backer_money`>= %s
        """, (FXF_PRO_ID, 101.7))
    elif pro_id == WJL_PRO_ID:
        rst = mysql_util.select_one("""
                    SELECT count(*) FROM `order` WHERE `pro_id`=%s and `backer_money`>= %s
                """, (WJL_PRO_ID, 71.3))
    else:
        return 0
    # 本方捣乱次数
    rst2 = get_make_trouble_time(pro_id)
    return rst[0] + int(rst2 // 5)


def get_current_supporter_num(pro_id):
    """
    获取当前集资人数
    :param pro_id:
    :return:
    """
    rst = mysql_util.select_one("""
        SELECT COUNT(DISTINCT(`supporter_id`)) FROM `order` WHERE `pro_id`=%s
    """, (pro_id, ))
    my_logger.info('%s当前集资人数: %s' % (pro_id, rst[0]))
    return rst[0]


def get_current_points(pro_id):
    if pro_id not in[FXF_PRO_ID, WJL_PRO_ID]:
        return 0
    time0 = time.time()
    # 当前集资人数
    fxf_supporter_num = get_current_supporter_num(FXF_PRO_ID)
    wjl_supporter_num = get_current_supporter_num(WJL_PRO_ID)
    supporter_num_points = 0
    rst = mysql_util.select_all("""
        select * from `order` where pro_id=%s
    """, (pro_id, ))
    points = 0
    for order in rst:
        """
        (order_id, supporter_id, backer_money, pay_time, pro_id)
        """
        add = plus_points(pro_id, order[2])
        points += add
    if pro_id == FXF_PRO_ID:
        make_trouble_time_other = get_make_trouble_time(WJL_PRO_ID)
        make_trouble_time_self = get_make_trouble_time(FXF_PRO_ID)
        bonus_minus_time = get_plus_10_times(WJL_PRO_ID)
        # 对方通过捣乱给己方扣除的分数
        make_trouble_points = make_trouble_time_other * WJL_MAKE_TROUBLE_POINTS
        # 通过累计+10分的记录为对方扣除的分数（每5次扣除10分）
        bonus_minus_points = int(bonus_minus_time // 5) * 10
        my_logger.debug('汪佳翎共给冯晓菲捣乱%s次，共扣除%s分' % (make_trouble_time_other, make_trouble_points))
        my_logger.debug('冯晓菲共有%s次+10分的记录，为汪佳翎扣除%s分' % (bonus_minus_time, bonus_minus_points))
        if fxf_supporter_num > wjl_supporter_num:
            supporter_num_points = 61

    elif pro_id == WJL_PRO_ID:
        make_trouble_time_self = get_make_trouble_time(WJL_PRO_ID)
        make_trouble_time_other = get_make_trouble_time(FXF_PRO_ID)
        bonus_minus_time = get_plus_10_times(FXF_PRO_ID)

        # 对方通过捣乱给己方扣除的分数
        make_trouble_points = make_trouble_time_other * FXF_MAKE_TROUBLE_POINTS
        # 通过累计+10分的记录为对方扣除的分数（每5次扣除10分）
        bonus_minus_points = int(bonus_minus_time // 5) * 10
        my_logger.debug('冯晓菲共给汪佳翎捣乱%s次，共扣除%s分' % (make_trouble_time_other, make_trouble_points))
        my_logger.debug('冯晓菲共有%s次+10分的记录，为汪佳翎扣除%s分' % (bonus_minus_time, bonus_minus_points))
        if fxf_supporter_num < wjl_supporter_num:
            supporter_num_points = 61
    else:
        return 0
    my_logger.info('%s人头数得分为:%s' % (pro_id, supporter_num_points))
    # 己方捣乱加成分数
    my_logger.info('%s捣乱次数为: %s' % (pro_id, make_trouble_time_self))
    make_trouble_bonus_points = 10 * int(make_trouble_time_self // 5)
    my_logger.info('%s捣乱共加分: %s' % (pro_id, make_trouble_bonus_points))
    # 分数计算方法: 基本得分 - 对方捣乱分数 + 己方捣乱分数(每5次捣乱+10分） - 额外分数（每有5次+10分项目 为对方-10分）+ 人头得分
    points = points - make_trouble_points + make_trouble_bonus_points - bonus_minus_points + supporter_num_points
    my_logger.info('当前%s的总得分为: %s' % (pro_id, points))
    my_logger.debug('该函数共消耗时间: %s' % (time.time() - time0))
    return points


if __name__ == '__main__':
    # plus_points(15972, 101.7)
    # plus_points(15980, 71.3)
    # plus_points(15972, 10.19)
    # plus_points(15980, 78.3)
    # plus_points(15972, 10)
    # plus_points(15980, 7)
    # print(get_plus_10_times(FXF_PRO_ID))
    # print(get_plus_10_times(WJL_PRO_ID))
    get_current_points(15972)
    get_current_points(15980)

