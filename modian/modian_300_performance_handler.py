# -*- coding:utf-8 -*-
"""
公演300场特别企划
①每集资10元即可抽票一次，1/3的几率抽中，100以上都算10次。抽票结果的座位号为1到10排，1号到30号，不包括10排17
②抽到的结果不重复，每个位置只能抽出1次，结果可在后台记录查看。机器人播报时显示场次日期、座位号，这两个都是变量，不同的座位号对应不同的日期，之后我会整理出表格发你。播报文案：您参与的FXF48公演抽选成功！公演日期：xxx 座位号：x排x号 或 抱歉，本次抽选未中。一次集资包含多次抽选的话，每一条播报前面加个序号
③抽到几个指定的座位后，在播报后会有其他文案，例如：恭喜抽中七夕特别座位，您将与x排xx号一同欢度七夕，祝福。大概有10多个触发奖品的座位号和对应的文案，之后也会整理一下发你
④299个座位都抽完后，抽中的票都叫加站001等等。抽中几率升为1/2.5
"""

from utils.mysql_util import mysql_util
import logging
try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)
# import time
from utils import util
import xlrd
import os
from utils import global_config


class Seat:
    def __init__(self, row, col):
        self._row = row
        self._col = col
        self._year = 0
        self._month = 0
        self._day = 0

    @property
    def row(self):
        return self._row

    @property
    def col(self):
        return self._col

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @property
    def day(self):
        return self._day

    @year.setter
    def year(self, year):
        self._year = year

    @month.setter
    def month(self, month):
        self._month = month

    @day.setter
    def day(self, day):
        self._day = day

    def __str__(self):
        return 'Seat[row=%s, col=%s, year=%s, month=%s, day=%s]' % (self.row, self.col, self.year, self.month, self.day)


class Standing:
    def __init__(self, number):
        self._number = number

    @property
    def number(self):
        return self._number

    def __str__(self):
        return 'Standing[number=%s]' % self.number


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
excel_path = os.path.join(base_dir, 'data', '300场活动.xlsx')
workbook = xlrd.open_workbook(excel_path)
sheet = workbook.sheet_by_name('场次对应')
nrows = sheet.nrows
ncols = sheet.ncols
# 前2行是标题
seat_number_to_date_dict = {}
for i in range(2, nrows):
    row = sheet.row_values(i)
    if row:
        seat = Seat(int(row[5]), int(row[6]))
        seat.year = int(row[1])
        seat.month = int(row[2])
        seat.day = int(row[3])
        seat_number = int(row[0])
        seat_number_to_date_dict[seat_number] = seat


special_seats_wording = {
    227: '恭喜8排17与7排7共同欢度七夕，二位将各获得一份「女生收到都感动得哭了」或「男生收到都感动得哭了」小礼物 以及应援会微博祝福及群内自定义CP头衔',
    187: '恭喜8排17与7排7共同欢度七夕，二位将各获得一份「女生收到都感动得哭了」或「男生收到都感动得哭了」小礼物 以及应援会微博祝福及群内自定义CP头衔',
    107: '2015年4月17日是我们灰的首演日期，抽到座位4排17即可获得【李子园一箱】',
    174: '2016年6月24日是我们灰100场达成的日期，抽到座位6排24即可获得【自定义群关键词回复】机会',
    175: '2017年6月25日是我们灰200场达成的日期，抽到座位6排25即可获得【自定义群关键词回复】机会',
    141: '2017年5月21日是我们灰正式宣布兼任SII的日期，抽到座位5排21即可获得【自定义群关键词回复】机会',
    293: '2015年10月23日是我们灰的第一次生诞祭日期，抽到座位10排23即可获得【FXF48徽章周边】一个',
    299: '2016年10月29日是我们灰的第二次生诞祭日期，抽到座位10排29即可获得【春季周边“学识渊博”款应援服一件（fxf同款，限量4件）】',
    241: '9排1号对应2017年11月4日 我们灰的第三次生诞祭日期，抽到座位9排1即可获得【款款日记周边】一套'

}


def get_current_available_seats():
    """
    获取当前可用座区号码
    :return:
    """
    my_logger.info('获取当前可用座区号码')
    rst = [i for i in range(1, 301)]
    used_seats = mysql_util.select_all("""
        SELECT seats_number FROM `seats_record` where seats_type = 1
    """)
    for seat in used_seats:
        rst.remove(seat[0])
    my_logger.debug('当前剩余的座区号码: %s' % rst)
    return rst


def get_draw_tickets_num(support_num):
    if not global_config.MODIAN_300_ACTIVITY:
        support_num = support_num * 10
    if support_num <= 10:
        return 0
    elif support_num <= 100:
        return int(support_num / 10)
    else:
        return 10


def can_draw_tickets(is_seats=True):
    """
    抽选概率1/3（坐区），1/2.5(站区）
    :return: 是否能够抽中
    """
    if is_seats:
        candidates = [i for i in range(3)]
        rst = util.choice(candidates)
        my_logger.debug('是否抽中坐区: %s' % (rst[0] < 1))
        return rst[0] < 1
    else:
        candidates = [i for i in range(5)]
        rst = util.choice(candidates)
        my_logger.debug('是否抽中站区: %s' % (rst[0] < 2))
        return rst[0] < 2


def get_current_standing_num():
    """
    获取当前已售出的站票总数
    :return:
    """
    rst = mysql_util.select_one("""
        SELECT COUNT(*) FROM `seats_record` WHERE seats_type=2
    """)
    return rst[0]


def draw_standing_tickets():
    """
    抽站票
    :return:
    """
    can_draw = can_draw_tickets(is_seats=False)
    if not can_draw:
        return -1
    rst = get_current_standing_num() + 1
    my_logger.info('抽中的站区号码: %s' % rst)
    return rst


def draw_tickets(tickets_array):
    """
    抽坐票
    :param tickets_array: 坐区可用座位号
    :return: 座位号，坐区从1-300
    """
    can_draw = can_draw_tickets(is_seats=True)
    if not can_draw:
        return -1
    rst = util.choice(tickets_array)[0]
    my_logger.info('抽中的座位号: %s' % rst)
    return rst


def convert_number_to_seats(number):
    """
    将号码转化为座位号
    :param number:
    :return:
    """
    if number > 300 or number <= 0:
        raise ValueError("座位号必须小于等于300！")
    row = int((number - 1) / 30) + 1
    col = (number - 1) % 30 + 1
    my_logger.info('座位号: %s' % Seat(row, col))
    return Seat(row, col)


if __name__ == '__main__':
    get_current_standing_num()
