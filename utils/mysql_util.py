# -*- coding: utf-8 -*-

import pymysql
from log.my_logger import logger


class MySQLUtil:
    def __init__(self, host, port, user, passwd, db):
        self.conn = self.getConn(host, port, user, passwd, db)

    def getConn(self, host, port, user, passwd, db, charset="utf8"):
        logger.debug('获取数据库连接')
        try:
            conn = pymysql.connect(host=host, port=port, passwd=passwd, db=db, user=user, charset=charset)
            return conn
        except pymysql.Error as e:
            logger.error('连接mysql出现错误: %s', e)

    def select(self, sql):
        logger.info('查询: %s', sql)
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
        except pymysql.Error as e:
            logger.error('数据库select出现错误: %s', e)
        finally:
            cursor.close()
        return data

    def query(self, sql):
        """
        插入，删除，更新操作
        :param sql:
        :return:
        """
        logger.info('mysql语句: %s', sql)
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
            self.conn.commit()
        except pymysql.Error as e:
            logger.error('数据库操作出现错误: %s', e)
            self.conn.rollback()
        finally:
            cursor.close()

    def close(self):
        self.conn.close()


if __name__ == '__main__':
    mysql_util = MySQLUtil('localhost', 3306, 'root', 'root', 'card_draw')
    rst = mysql_util.select('select count(distinct(supporter_id)) from `order`')
    print(rst[0][0])



