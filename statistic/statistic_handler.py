# -*- coding:utf-8 -*-

import sys
import os
import time
import sqlite3
import requests
import json
import datetime

from qq.qqhandler import QQHandler
from utils import util
from log.my_logger import statistic_logger as my_logger

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
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS 'group' (
                    member_name  VARCHAR( 100 ),
                    group_number INT,
                    group_size   INT,
                    date         DATE 
                );""")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS 'member' ( 
                    member_id    INT,
                    member_name  VARCHAR,
                    group_number INT,
                    super_tag    VARCHAR( 500 ) 
                );""")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS 'super_tag' ( 
                member_name VARCHAR( 100 ),
                link        VARCHAR( 500 ),
                size        INT,
                date        DATE 
            );""")
        except Exception as e:
            my_logger.error(e)
        finally:
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

        try:
            # 获取群号
            my_logger.debug('获取成员群号')
            c = cursor.execute("""
                select group_number from member WHERE member_name=?
            """, (member_name,))
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

            r = self.session.get(super_tag).json()
            if r['ok'] == 1:
                desc_more = r['data']['pageInfo']['desc_more'][0]
                desc_arr = desc_more.strip().split('\u3000')
                fans_number = int(desc_arr[2][2:])
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

    def get_bilibili_stat(self):
        """
        获取b站数据
        :return:
        """
        cursor = self.conn.cursor()
        try:
            bilibili_path = os.path.join(os.path.dirname(BASE_DIR), 'data', 'bilibili.json')
            member_json = json.load(open(bilibili_path, encoding='utf8'))['stats']
            for member in member_json:
                bilibili_id = member['bid']
                member_name = member['name']
                my_logger.info(member_name)

                url1 = 'https://api.bilibili.com/x/relation/stat?vmid={}&jsonp=jsonp'.format(bilibili_id)
                header = {
                    'Referer': 'https://space.bilibili.com/{}'.format(bilibili_id),
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'
                }
                rsp = self.session.get(url1, headers=header).text
                rsp_json = json.loads(rsp[6: -1])
                fan_number = rsp_json['data']['follower']

                try:

                    url2 = 'https://api.bilibili.com/x/space/upstat?mid={}&jsonp=jsonp'.format(bilibili_id)
                    rsp = self.session.get(url2, headers=header,
                                           cookies={'SESSDATA': 'db49e46a%2C1614611003%2C81dfe*91'}).text

                    rsp_json = json.loads(rsp[6: -1])
                    view = rsp_json['data']['archive']['view']
                    print(rsp_json)
                except Exception as e:
                    my_logger.exception(e)
                    view = 0

                url3 = 'https://api.bilibili.com/x/space/acc/info?mid={}&jsonp=jsonp'.format(bilibili_id)
                rsp = self.session.get(url3, headers=header).json()
                bilibili_name = rsp['data']['name']

                cur_date = util.convert_timestamp_to_timestr(time.time() * 1000)

                cursor.execute("""
                    INSERT INTO `bilibili` (`member_name`, `bilibili_id`, `bilibili_name`, `fans_num`, `video_view`, `update_time`)
                    VALUES
                    (?, ?, ?, ?, ?, ?)
                """, (member_name, bilibili_id, bilibili_name, fan_number, view, cur_date))
                self.conn.commit()
                time.sleep(2)
        except Exception as e:
            my_logger.exception(e)
        finally:
            cursor.close()

    def pocket_msgs(self):
        from pocket48 import others
        cursor = self.conn.cursor()
        today = datetime.date.today().strftime('%Y-%m-%d %H:%M:%S')
        today_timestamp = int(util.convert_timestr_to_timestamp(today)) * 1000
        yesterday_timestamp = today_timestamp - 60*24*60*1000
        room_list = others.get_room_list()

        try:
            for room in room_list:
                others.member_messages = {'id': room['id'], 'name': room['name'], 'room_id': room['room_id'], '100': 0,
                                   '101': 0, '102': 0, '103': 0, '104': 0, '105': 0, '106': 0, '200': 0, '201': 0,
                                   '202': 0, '203': 0}
                my_logger.debug(room['name'])
                if room['id'] in [63, 327683, 327682, 5973]:
                    continue

                others.get_room_history_msg(room['id'], room['room_id'], today_timestamp - 1, yesterday_timestamp)

                my_logger.debug(others.member_messages)
                cur_date = util.convert_timestamp_to_timestr(time.time() * 1000)

                sum = others.member_messages['100'] + others.member_messages['101'] + others.member_messages['102'] + others.member_messages[
                    '103'] + others.member_messages['104'] + others.member_messages['105'] + others.member_messages['106'] + others.member_messages[
                          '201'] + others.member_messages['202'] + others.member_messages['203']
                cursor.execute("""
                    INSERT INTO `pocket_message` (`member_id`, `room_id`, `member_name`, `text`, `reply`, `live`, `vote`,
                    `idol_flip`, `red_packet`, `pic`, `voice`, `video`, `total_num`, `update_time`) VALUES 
                    (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    others.member_messages['id'], others.member_messages['room_id'], others.member_messages['name'], others.member_messages['100'],
                    others.member_messages['101'], others.member_messages['102'], others.member_messages['104'], others.member_messages['105'],
                    others.member_messages['106'], others.member_messages['200'], others.member_messages['201'], others.member_messages['202'],
                    sum, cur_date))
            self.conn.commit()
        except Exception as e:
            my_logger.exception(e)
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
    # cursor = statistic_handler.conn.cursor()
    # cursor.execute("""
    #     select `date`, `group_size` from `group` LIMIT 30
    # """)
    # list2 = cursor.fetchall()
    # x = [datetime.date.strftime(datetime.datetime.strptime(i[0], '%Y-%m-%d %H:%M:%S').date(), '%Y-%m-%d') for i in list2]
    # y = [i[1] for i in list2]
    # statistic_handler.draw_line_plot(x, y, title='fengxiaofei应援群人数变化')
    # statistic_handler.update_group_size('fengxiaofei')
    # statistic_handler.get_super_tag_size('fengxiaofei')
    # statistic_handler.get_super_tag_size('zhangxin')
    statistic_handler.get_bilibili_stat()
    # from utils import global_config
    # global_config.POCKET48_TOKEN = '8kqaSdMzuM56NTZLhzqQgUEasxvfa1WpuvuBoNY+AHdVBG2qew4+9l8rh5FOa9Vwrk3PPJEhz+s='
    # statistic_handler.pocket_msgs()
