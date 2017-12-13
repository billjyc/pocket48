# -*- coding:utf-8 -*-

import sys
import os
import time
import sqlite3
import requests

from qq.qqhandler import QQHandler
from qqbot.utf8logger import DEBUG, INFO, ERROR
from utils import util

from bs4 import BeautifulSoup


reload(sys)
sys.setdefaultencoding('utf8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class StatisticHandler:
    def __init__(self, db_path):
        self.session = requests.session()
        db_path = os.path.join(BASE_DIR, db_path)
        DEBUG('db_path: %s', db_path)
        self.conn = sqlite3.connect(db_path)
        DEBUG('读取数据库成功')

    def update_group_size(self, member_name):
        """
        获取群人数
        :param member_name:
        :return:
        """
        cursor = self.conn.cursor()
        DEBUG('更新群信息')
        # QQHandler.update()

        try:
            # 获取群号
            DEBUG('获取成员群号')
            c = cursor.execute("""
                select group_number from member WHERE member_name=?
            """, (member_name, ))
            group_number = c.fetchone()[0]
            DEBUG('群号: %s', group_number)
            number = QQHandler.get_group_number(group_number)
            DEBUG('群%s人数: %s', group_number, number)

            # number = 800
            cur_date = util.convert_timestamp_to_timestr(time.time() * 1000)
            DEBUG('记录时间: %s', cur_date)

            DEBUG('统计：成员: %s, 群号: %s, 人数: %s, 时间: %s', member_name, group_number, number, cur_date)
            cursor.execute("""
            INSERT INTO `group` (`member_name`, `group_number`, `group_size`, `date`) VALUES
            (?, ?, ?, ?)
            """, (member_name, group_number, number, cur_date))
            self.conn.commit()
        except Exception as e:
            ERROR(e)
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
            # 获取群号
            c = cursor.execute("""
                        select super_tag from member WHERE member_name=?
                    """, (member_name,))
            super_tag = c.fetchone()[0]

            r = self.session.get(super_tag)
            soup = BeautifulSoup(r.content, 'lxml')

            tb_counter = soup.find_all(class_='tb_counter')[0]
            fans_number = tb_counter.find_all(class_='S_line1')[2].find_all('strong').contents[0]

            cur_date = util.convert_timestamp_to_timestr(time.time() * 1000)

            DEBUG('统计：成员: %s, 超话: %s, 人数: %d, 时间: %s', member_name, super_tag, number, cur_date)
            cursor.execute("""
                    INSERT INTO `super_tag` (`member_name`, `link`, `size`, `date`) VALUES
                    (?, ?, ?, ?)
                    """, (member_name, super_tag, number, cur_date))
            self.conn.commit()
        except Exception as e:
            ERROR(e)
        finally:
            cursor.close()


if __name__ == "__main__":
    statistic_handler = StatisticHandler('statistics.db')
    statistic_handler.update_group_size('fengxiaofei')
    # statistic_handler.get_super_tag_size('fengxiaofei')
