# -*- coding: utf-8 -*-

import pymysql
from log.my_logger import logger

from DBUtils.PooledDB import PooledDB
from utils import db_config as Config


class MySQLUtil:
    """
    MYSQL数据库对象，负责产生数据库连接 , 此类中的连接采用连接池实现
    获取连接对象：conn = self.get_conn()
    释放连接对象;conn.close()或del conn
    """

    def __init__(self):
        self._pool = PooledDB(creator=pymysql, mincached=Config.DB_MIN_CACHED, maxcached=Config.DB_MAX_CACHED,
                              host=Config.DB_HOST, port=Config.DB_PORT, user=Config.DB_USER, passwd=Config.DB_PASSWORD,
                              db=Config.DB_DBNAME, use_unicode=False, charset=Config.DB_CHARSET,
                              maxshared=Config.DB_MAX_SHARED, maxconnections=Config.DB_MAX_CONNECTIONS,
                              setsession=Config.DB_SET_SESSION)

    def get_conn(self):
        return self._pool.connection()

    # def getConn(self, host, port, user, passwd, db, charset="utf8"):
    #     logger.debug('获取数据库连接')
    #     try:
    #         conn = pymysql.connect(host=host, port=port, passwd=passwd, db=db, user=user, charset=charset)
    #         return conn
    #     except pymysql.Error as e:
    #         logger.error('连接mysql出现错误: %s', e)

    def execute_and_get_id(self, sql, param=None):
        """ 执行插入语句并获取自增id """
        conn = self.get_conn()
        cursor = conn.cursor()
        if param is None:
            cursor.execute(sql)
        else:
            cursor.execute(sql, param)
        row_id = cursor.lastrowid
        cursor.close()
        conn.close()
        return row_id

    def query(self, sql, param=None):
        """ 删除，更新，插入， 执行sql语句 """
        conn = self.get_conn()
        cursor = conn.cursor()
        if param is None:
            rowcount = cursor.execute(sql)
        else:
            rowcount = cursor.execute(sql, param)
        conn.commit()
        cursor.close()
        conn.close()

        return rowcount

    def select_one(self, sql, param=None):
        """ 获取一条信息 """
        conn = self.get_conn()
        cursor = conn.cursor()
        rowcount = cursor.execute(sql, param)
        if rowcount > 0:
            res = cursor.fetchone()
        else:
            res = None
        cursor.close()
        conn.close()

        return res

    def select_all(self, sql, param=None):
        """ 获取所有信息 """
        conn = self.get_conn()
        cursor = conn.cursor()
        rowcount = cursor.execute(sql, param)
        if rowcount > 0:
            res = cursor.fetchall()
        else:
            res = None
        cursor.close()
        conn.close()

        return res


if __name__ == '__main__':
    mysql_util = MySQLUtil()
    sql = """
    select supporter_id, sum(backer_money) as total 
    from `order` where pro_id=%s group by supporter_id order by total desc;
    """
    sql2 = """
        INSERT INTO `supporter` (`id`, `name`) VALUES (%s, %s) 
    """
    params = (13566, )
    params2 = (123, '熟练地')
    rst = mysql_util.query(sql2, params2)
    # print(rst)
    # print(type(rst))
    # print(rst[0][0])



