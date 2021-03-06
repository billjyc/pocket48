# -*- coding:utf-8 -*-
"""
2018水灰PK特别活动
"""
from utils.mysql_util import mysql_util
import logging
from utils import util

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)
import time


# fxf, yby四天的链接列表，用于计算总积分
FXF_PRO_IDS = [37793, 37912, 37920, 37916]
YBY_PRO_IDS = [37826, 37959, 38095, 38202]
# 水灰链接
SHUIHUI_PRO_ID = 37740

# fxf, yby当日链接，用于计算当日积分
FXF_CURRENT_PRO_ID = 37916
YBY_CURRENT_PRO_ID = 38202

TEN = 10
ONE_HUNDRED = 100


def plus_fxf_yby_points(amount, pro_id, order_id, user_id):
    """
    FXF和YBY链接的每次集资得分计算方式
    10元=1积分，100元=11积分
    :param amount:
    :param pro_id
    :param order_id:
    :param user_id:
    :return:
    """
    my_logger.info('[水灰PK]pro_id: %s, 集资金额: %s, order_id: %s, user_id: %s' % (pro_id, amount, order_id, user_id))
    points = 0
    if amount < TEN:
        points = 0
    elif amount < ONE_HUNDRED:
        points = int(amount // TEN)
    else:
        points = int(amount // ONE_HUNDRED) * 11 + int(amount % ONE_HUNDRED // TEN)
    my_logger.info('[水灰PK]加分数量: %s' % points)
    # 存入数据库
    mysql_util.query("""
                insert into `point_detail` (`order_id`, `pro_id`, `point`) VALUES (%s, %s, %s)
            """, (order_id, pro_id, points))
    return points


def plus_shuihui_points(amount, pro_id, order_id, user_id):
    """
    水灰应援会链接的得分计算方式
    10元=2.5积分，100元=26积分
    :param amount:
    :param pro_id
    :param order_id:
    :param user_id:
    :return:
    """
    my_logger.info('[水灰PK]pro_id: %s, 集资金额: %s, order_id: %s, user_id: %s' % (pro_id, amount, order_id, user_id))
    points = 0
    if amount < TEN:
        points = 0
    elif amount < ONE_HUNDRED:
        points = int(amount // TEN) * 2.5
    else:
        points = int(amount // ONE_HUNDRED) * 26 + int(amount % ONE_HUNDRED // TEN) * 2.5
    my_logger.info('[水灰PK]加分数量: %s' % points)
    # 存入数据库
    mysql_util.query("""
                insert into `point_detail` (`order_id`, `pro_id`, `point`) VALUES (%s, %s, %s)
            """, (order_id, pro_id, points))
    return points


def get_current_supporter_num(pro_id):
    """
    获取当前集资人数
    :param pro_id:
    :return:
    """
    rst = mysql_util.select_one("""
        SELECT COUNT(DISTINCT(`supporter_id`)) FROM `order` WHERE `pro_id`= %s
    """, (pro_id,))
    my_logger.info('[水灰PK]%s当前集资人数: %s' % (pro_id, rst[0] if rst[0] else 0))
    return rst[0] if rst[0] else 0


def compute_shuihui_total_points():
    """
    计算水灰应援会的总分=日常积分+人头数*25
    :return:
    """
    my_logger.info('[水灰PK]计算水灰应援会总分')
    # 人头数
    supporter_num = get_current_supporter_num(SHUIHUI_PRO_ID)
    # 总分
    rst = mysql_util.select_one("""
        SELECT SUM(`point`) from `point_detail` WHERE `pro_id`=%s
    """, (SHUIHUI_PRO_ID, ))
    point = supporter_num * 25 + rst[0] if rst[0] else 0
    my_logger.info('[水灰PK]水灰应援会总分: %s' % point)
    return point


def compute_fxf_yby_single_points(pro_id):
    """
    计算fxf，yby单日积分
    :param pro_id:
    :return:
    """
    my_logger.info('[水灰PK]计算应援会总分, pro_id=%s' % pro_id)
    # 总分
    rst = mysql_util.select_one("""
            SELECT SUM(`point`) from `point_detail` WHERE `pro_id`=%s
        """, (pro_id,))
    point = rst[0] if rst[0] else 0
    my_logger.info('[水灰PK]应援会总分: %s' % point)
    return point


def compute_fxf_yby_total_points():
    """
    计算fxf，yby阵营总积分
    :return:
    """
    my_logger.info('[水灰PK]计算fxf,yby阵营总积分')
    yby_point = 0
    fxf_point = 0
    for pro_id in FXF_PRO_IDS:
        if pro_id == 37920:
            fxf_point += compute_fxf_yby_single_points(pro_id) * 1.5
        elif pro_id == 37916:
            fxf_point += compute_fxf_yby_single_points(pro_id) * 2
        else:
            fxf_point += compute_fxf_yby_single_points(pro_id)
    my_logger.info('[水灰PK]FXF阵营总积分: %s' % fxf_point)
    for pro_id in YBY_PRO_IDS:
        yby_point += compute_fxf_yby_single_points(pro_id)
    my_logger.info('[水灰PK]YBY阵营总积分: %s' % yby_point)
    return fxf_point, yby_point


# 水灰金曲PK活动相关
#             current_report = ''
#             if int(modian_entity.pro_id) == modian_shuihui_pk.FXF_CURRENT_PRO_ID:
#                 plus_point = modian_shuihui_pk.plus_fxf_yby_points(backer_money, modian_entity.pro_id, str(oid),
#                                                                    user_id)
#                 self.fxf_current_point += plus_point
#                 self.fxf_total_point += plus_point
#                 current_report += '本次加分: %s\n' % plus_point
#             elif int(modian_entity.pro_id) == modian_shuihui_pk.YBY_CURRENT_PRO_ID:
#                 plus_point = modian_shuihui_pk.plus_fxf_yby_points(backer_money, modian_entity.pro_id, str(oid),
#                                                                    user_id)
#                 self.yby_current_point += plus_point
#                 self.yby_total_point += plus_point
#                 current_report += '本次加分: %s\n' % plus_point
#             elif int(modian_entity.pro_id) == modian_shuihui_pk.SHUIHUI_PRO_ID:
#                 plus_point = modian_shuihui_pk.plus_shuihui_points(backer_money, modian_entity.pro_id, str(oid),
#                                                                    user_id)
#                 self.shuihui_total_point = modian_shuihui_pk.compute_shuihui_total_points()
#                 current_report += '本次加分: %s\n' % plus_point
#
#             fxf_data = {
#                 "name": "冯晓菲应援会",
#                 "current": self.fxf_current_point,
#                 "total": self.fxf_total_point
#             }
#             yby_data = {
#                 "name": "杨冰怡应援会",
#                 "current": self.yby_current_point,
#                 "total": self.yby_total_point,
#             }
#             shuihui_data = {
#                 "name": "水灰应援会",
#                 "total": self.shuihui_total_point,
#             }
#             current_data = [fxf_data, yby_data]
#             total_data = [fxf_data, yby_data, shuihui_data]
#             current_data.sort(key=lambda k: (k.get('current', 0)), reverse=True)
#             total_data.sort(key=lambda k: (k.get('total', 0)), reverse=True)
#             my_logger.debug('[水灰PK]排序后的current_data: %s' % current_data)
#             my_logger.debug('[水灰PK]排序后的total_data: %s' % total_data)
#             current_report += '今日战况: \n'
#             for i in range(len(current_data)):
#                 sub_msg = '%d. %s: %.1f分\n' % (i + 1, current_data[i]['name'], current_data[i]['current'])
#                 current_report += sub_msg
#             total_report = '总积分排行: \n'
#             for i in range(len(total_data)):
#                 sub_msg = '%d. %s: %.1f分\n' % (i + 1, total_data[i]['name'], total_data[i]['total'])
#                 total_report += sub_msg

            # QQHandler.send_to_groups(['483548995'], current_report + total_report)
