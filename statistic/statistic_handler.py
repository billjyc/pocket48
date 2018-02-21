# -*- coding:utf-8 -*-

import sys
import os
import time
import sqlite3
import requests

from qq.qqhandler import QQHandler
from utils import util
from log.my_logger import logger as my_logger

from bs4 import BeautifulSoup

import datetime
# import matplotlib.pyplot as plt
# from pylab import mpl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# mpl.rcParams['font.sans-serif'] = ['FangSong']  # 指定默认字体
# mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


class StatisticHandler:
    def __init__(self, db_path):
        self.session = requests.session()
        db_path = os.path.join(BASE_DIR, db_path)
        my_logger.debug('db_path: %s', db_path)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS member (
                member_name  VARCHAR( 100 ),
                group_number INT,
                group_size   INT,
                date         DATE 
            );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS member ( 
            member_id    INT,
            member_name  VARCHAR,
            group_number INT,
            super_tag    VARCHAR( 500 ) 
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS super_tag ( 
            member_name VARCHAR( 100 ),
            link        VARCHAR( 500 ),
            size        INT,
            date        DATE 
        );
        """)
        cursor.close()
        my_logger.debug('读取数据库成功')

    def update_group_size(self, member_name):
        """
        获取群人数
        :param member_name:
        :return:
        """
        cursor = self.conn.cursor()
        my_logger.debug('更新群信息')
        # QQHandler.update()

        try:
            # 获取群号
            my_logger.debug('获取成员群号')
            c = cursor.execute("""
                select group_number from member WHERE member_name=?
            """, (member_name, ))
            group_number = c.fetchone()[0]
            my_logger.debug('群号: %s', group_number)
            number = QQHandler.get_group_number(str(group_number))
            my_logger.debug('群%s人数: %s', group_number, number)

            # number = 800
            cur_date = util.convert_timestamp_to_timestr(time.time() * 1000)
            my_logger.debug('记录时间: %s', cur_date)

            my_logger.debug('统计：成员: %s, 群号: %s, 人数: %s, 时间: %s', member_name, group_number, number, cur_date)
            cursor.execute("""
            INSERT INTO `group` (`member_name`, `group_number`, `group_size`, `date`) VALUES
            (?, ?, ?, ?)
            """, (member_name, group_number, number, cur_date))
            self.conn.commit()
        except Exception as e:
            my_logger.error(e)
        finally:
            cursor.close()

    def get_super_tag_size(self, member_name):
        """
        获取超话人数
        :param member_name:
        :return:
        """
        cursor = self.conn.cursor()

        try:
            # 获取超话链接
            c = cursor.execute("""
                        select super_tag from member WHERE member_name=?
                    """, (member_name,))
            super_tag = c.fetchone()[0]

            r = self.session.get(super_tag)
            soup = BeautifulSoup(r.content, 'lxml')

            tb_counter = soup.find_all(class_='tb_counter')[0]
            fans_number = tb_counter.find_all(class_='S_line1')[2].find_all('strong').contents[0]

            cur_date = util.convert_timestamp_to_timestr(time.time() * 1000)

            my_logger.debug('统计：成员: %s, 超话: %s, 人数: %d, 时间: %s', member_name, super_tag, fans_number, cur_date)
            cursor.execute("""
                    INSERT INTO `super_tag` (`member_name`, `link`, `size`, `date`) VALUES
                    (?, ?, ?, ?)
                    """, (member_name, super_tag, fans_number, cur_date))
            self.conn.commit()
        except Exception as e:
            my_logger.error(e)
        finally:
            cursor.close()

    # def draw_line_plot(self, x, y, title=''):
    #     """
    #     绘制折线图
    #     :param x: 时间
    #     :param y:
    #     :return:
    #     """
    #     plt.figure()
    #     plt.plot(x, y, marker='o', mec='r', mfc='w')
    #     for a, b in zip(x, y):
    #         plt.text(a, b+0.5, str(b))
    #     plt.xlabel("日期")
    #     plt.ylabel("人数")
    #     plt.title(title)
    #     plt.show()
    #     plt.savefig("line_%s.png" % time.time())


if __name__ == "__main__":
    statistic_handler = StatisticHandler('statistics.db')
    cursor = statistic_handler.conn.cursor()
    cursor.execute("""
        select `date`, `group_size` from `group` LIMIT 30
    """)
    list2 = cursor.fetchall()
    x = [datetime.date.strftime(datetime.datetime.strptime(i[0], '%Y-%m-%d %H:%M:%S').date(), '%Y-%m-%d') for i in list2]
    y = [i[1] for i in list2]
    # statistic_handler.draw_line_plot(x, y, title='fengxiaofei应援群人数变化')
    # statistic_handler.update_group_size('fengxiaofei')
    # statistic_handler.get_super_tag_size('fengxiaofei')
