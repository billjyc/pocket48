# -*- coding:utf-8 -*-
"""
用于两个集资链接互相PK用
"""
from utils.mysql_util import mysql_util
import logging
from utils import util
try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)
import time


LOLLIPOP_AMOUNT = 10.17
LOLLIPOP_POINTS = 1
LOLLIPOP_IMG = 'https://raw.githubusercontent.com/billjyc/girls_django/master/modian/static/birthdaywish/imgs/%E6%A3%92%E6%A3%92%E7%B3%96.jpg'
SUGAR_BOWL_AMOUNT = 48
SUGAR_BOWL_POINTS = 5
SUGAR_BOWL_IMG = 'https://raw.githubusercontent.com/billjyc/girls_django/master/modian/static/birthdaywish/imgs/%E7%B3%96%E6%9E%9C%E7%BD%90.jpg'
FOX_DOLL_AMOUNT = 101.7
FOX_DOLL_POINTS = 10
FOX_DOLL_IMG = 'https://raw.githubusercontent.com/billjyc/girls_django/master/modian/static/birthdaywish/imgs/%E7%8B%90%E7%8B%B8%E7%8E%A9%E5%81%B6.jpg'

HUMMER_AMOUNT = 10.17
HUMMER_POINTS = -1
HUMMER_IMG = 'https://raw.githubusercontent.com/billjyc/girls_django/master/modian/static/birthdaywish/imgs/%E9%94%A4%E5%AD%90.jpg'
PUMPKIN_GRIMACE_AMOUNT = 101.7
PUMPKIN_GRIMACE_POINTS = -10
PUMPKIN_GRIMACE_IMG = 'https://raw.githubusercontent.com/billjyc/girls_django/master/modian/static/birthdaywish/imgs/%E5%8D%97%E7%93%9C%E9%AC%BC%E8%84%B8.jpg'
TREAT_AMOUNT = 111.1
TREAT_POINTS = -12
TREAT_IMG = 'https://raw.githubusercontent.com/billjyc/girls_django/master/modian/static/birthdaywish/imgs/%E6%8D%A3%E8%9B%8B.jpg'

OUTDATED_LOLLIPOP_POINTS = -1
FXF_KISS_POINTS = 3

TREAT_FAIL = 1
TREAT_SUCCESS = -3

SWEET_PRO_ID = 37152
TREAT_PRO_ID = 37154

TOTAL_POINTS = 0


def plus_points(amount, order_id, pro_id):
    """
    发糖组加分
    10.17得到棒棒糖 积分+1
    48   得到糖罐   积分+5
    101.7得到狐狸玩偶 积分+10
    过期的棒棒糖   积分-1  概率20%（暂定）
    Fxf的啵啵      积分+3   概率10%（暂定）
    :param amount:
    :return:
    """
    my_logger.info('发糖组加分，金额: %s元' % amount)
    num_of_fox_doll = 0
    num_of_sugar_bowl = 0
    num_of_lollipop = 0
    if amount < LOLLIPOP_AMOUNT:
        points = 0
        return points, ''
    elif LOLLIPOP_AMOUNT <= amount < SUGAR_BOWL_AMOUNT:
        num_of_lollipop = int(amount // LOLLIPOP_AMOUNT)
        points = num_of_lollipop * LOLLIPOP_POINTS
    elif SUGAR_BOWL_AMOUNT <= amount < FOX_DOLL_AMOUNT:
        num_of_sugar_bowl = int(amount // SUGAR_BOWL_AMOUNT)
        num_of_lollipop = int((amount % SUGAR_BOWL_AMOUNT) // LOLLIPOP_AMOUNT)
        points = num_of_sugar_bowl * SUGAR_BOWL_POINTS +  num_of_lollipop * LOLLIPOP_POINTS
    else:
        num_of_fox_doll = int(amount // FOX_DOLL_AMOUNT)
        num_of_sugar_bowl = int((amount % FOX_DOLL_AMOUNT) // SUGAR_BOWL_AMOUNT)
        num_of_lollipop = int((amount % FOX_DOLL_AMOUNT % SUGAR_BOWL_AMOUNT) // LOLLIPOP_AMOUNT)
        points = num_of_fox_doll * FOX_DOLL_POINTS + num_of_sugar_bowl * SUGAR_BOWL_POINTS + num_of_lollipop * LOLLIPOP_POINTS
    my_logger.info('加分数量: %s' % points)

    report = '获得'
    report += '【棒棒糖】*%s, ' % num_of_lollipop if num_of_lollipop > 0 else ''
    report += '【糖罐】*%s, ' % num_of_sugar_bowl if num_of_sugar_bowl > 0 else ''
    report += '【狐狸玩偶】*%s, ' % num_of_fox_doll if num_of_fox_doll > 0 else ''
    if num_of_lollipop > 0:
        report += '[CQ:image,file=%s]' % LOLLIPOP_IMG
    if num_of_sugar_bowl > 0:
        report += '[CQ:image,file=%s]' % SUGAR_BOWL_IMG
    if num_of_fox_doll > 0:
        report += '[CQ:image,file=%s]' % FOX_DOLL_IMG
    report += '\n'

    candidate = ['过期的棒棒糖', 'FXF的啵啵', '无']
    weight = [10, 20, 70]
    weight2 = [10, 15, 75]
    if 10.17 <= amount < 101.7:
        idx = util.weight_choice(candidate, weight2)
    elif amount >= 101.7:
        idx = util.weight_choice(candidate, weight)
    else:
        idx = -1
    bonus_report = ''
    if idx == 0:  # 过期的棒棒糖
        if 10.17 <= amount < 101.7:  # 10.17-101.7, 积分清零
            points = 0
            bonus_report += '很不幸，你获得了【过期的棒棒糖】，本次获取的积分清零T_T'
        elif amount >= 101.7:  # 多于101.7，积分减半
            points = int(points // 2)
            bonus_report += '很不幸，你获得了【过期的棒棒糖】，本次获取的积分减半T_T'
    elif idx == 1:  # FXF的啵啵，本次积分翻倍
        points *= 2
        bonus_report += '恭喜，你获得了【FXF的啵啵】，本次获取的积分加倍'
    else:
        pass
    if bonus_report:
        report += bonus_report
    report += '本次加分：%s\n' % points
    # 存入数据库
    mysql_util.query("""
        insert into `point_detail` (`order_id`, `pro_id`, `point`) VALUES (%s, %s, %s)
    """, (order_id, pro_id, points))
    return points, report


def minus_points(amount, order_id, pro_id):
    """
    捣蛋组扣分
    10.17得到小锤子  积分-1
    101.7得到南瓜鬼脸 积分-10
    111.1  捣蛋一次    积分-12

    捣蛋失败 积分+1      概率20%（暂定）
    捣蛋大成功 积分额外-3 概率10%（暂定）
    :param amount:
    :return:
    """
    my_logger.info('捣蛋组扣分, 金额: %s' % amount)
    num_of_hummer = 0
    num_of_pumpkin_grimace = 0
    num_of_treat = 0
    if amount < HUMMER_AMOUNT:
        points = 0
        return points, ''
    elif HUMMER_AMOUNT <= amount < PUMPKIN_GRIMACE_AMOUNT:
        num_of_hummer = int(amount // HUMMER_AMOUNT)
        points = num_of_hummer * HUMMER_POINTS
    elif PUMPKIN_GRIMACE_AMOUNT <= amount < TREAT_AMOUNT:
        num_of_pumpkin_grimace = int(amount // PUMPKIN_GRIMACE_AMOUNT)
        num_of_hummer = int((amount % PUMPKIN_GRIMACE_AMOUNT) // HUMMER_AMOUNT)
        points = num_of_pumpkin_grimace * PUMPKIN_GRIMACE_POINTS + num_of_hummer * HUMMER_POINTS
    else:
        num_of_treat = int(amount // TREAT_AMOUNT)
        num_of_pumpkin_grimace = int((amount % TREAT_AMOUNT) // PUMPKIN_GRIMACE_AMOUNT)
        num_of_hummer = int((amount % TREAT_AMOUNT % PUMPKIN_GRIMACE_AMOUNT) // HUMMER_AMOUNT)
        points = num_of_treat * TREAT_POINTS \
                 + num_of_pumpkin_grimace * PUMPKIN_GRIMACE_POINTS \
                 + num_of_hummer * HUMMER_POINTS
    my_logger.info('扣分数量: %s' % points)

    report = '获得'
    report += '【小锤子】*%s, ' % num_of_hummer if num_of_hummer > 0 else ''
    report += '【南瓜鬼脸】*%s, ' % num_of_pumpkin_grimace if num_of_pumpkin_grimace > 0 else ''
    report += '【捣蛋】*%s, ' % num_of_treat if num_of_treat > 0 else ''
    report += '\n'
    if num_of_hummer > 0:
        report += '[CQ:image,file=%s]' % HUMMER_IMG
    if num_of_pumpkin_grimace > 0:
        report += '[CQ:image,file=%s]' % PUMPKIN_GRIMACE_IMG
    if num_of_treat > 0:
        report += '[CQ:image,file=%s]' % TREAT_IMG

    candidate = ['捣蛋失败', '捣蛋大成功', '无']
    weight = [10, 20, 70]
    weight2 = [10, 15, 75]
    if 10.17 <= amount < 101.7:
        idx = util.weight_choice(candidate, weight)
    elif amount >= 101.7:
        idx = util.weight_choice(candidate, weight2)
    else:
        idx = -1
    bonus_report = ''
    if idx == 0:  # 捣蛋失败
        if 10.17 <= amount < 101.7:  # 10.17-101.7, 积分清零
            points = 0
            bonus_report += '很不幸，捣蛋失败，本次获取的积分清零T_T'
        elif amount >= 101.7:  # 多于101.7，积分减半
            points = int(points // 2)
            bonus_report += '很不幸，捣蛋失败，本次获取的积分减半T_T'
    elif idx == 1:  # 捣蛋大成功，本次积分翻倍
        points *= 2
        bonus_report += '恭喜，捣蛋大成功，本次获取的积分加倍'
    else:
        pass
    if len(bonus_report) > 0:
        report += bonus_report
    report += '本次减分：%s\n' % -points
    # 存入数据库
    mysql_util.query("""
            insert into `point_detail` (`order_id`, `pro_id`, `point`) VALUES (%s, %s, %s)
        """, (order_id, pro_id, points))
    return points, report


def get_current_supporter_num(pro_id):
    """
    获取当前集资人数
    :param pro_id:
    :return:
    """
    rst = mysql_util.select_one("""
        SELECT COUNT(DISTINCT(`supporter_id`)) FROM `order` WHERE `pro_id`= %s
    """, (pro_id,))
    my_logger.info('%s当前集资人数: %s' % (pro_id, rst[0]))
    return rst[0]


def get_current_points(pro_id):
    if pro_id not in [SWEET_PRO_ID, TREAT_PRO_ID]:
        return 0
    time0 = time.time()
    points = 0

    rst = mysql_util.select_all("""
        SELECT `point` from `point_detail` WHERE `pro_id` = %s
    """, (pro_id, ))
    if not rst:
        return points
    for a in rst:
        points += a[0]

    my_logger.info('当前累计分数: %s' % points)
    my_logger.debug('该函数共消耗时间: %s' % (time.time() - time0))
    return points


if __name__ == '__main__':
    # get_current_supporter_num(33035)
    # get_current_points(33035)
    print(minus_points(10.17, '1', '33035'))
    # print(minus_points(101.7))
    # print(minus_points(60))
    # print(minus_points(500))

    # print(plus_points(10.17))
    # print(plus_points(101.7))
    print(plus_points(60, '2', '33035'))
    # print(plus_points(500))
