# -*- coding:utf-8 -*-
"""
2018武侠特别活动
"""
from utils.mysql_util import mysql_util
import logging

try:
    from log.my_logger import modian_logger as my_logger
except:
    my_logger = logging.getLogger(__name__)
from utils import util
import os
import random
import json
from enum import Enum


class Direction(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class Point:
    """
    地图上的点
    """
    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    @property
    def x(self):
        return self.__x

    @x.setter
    def x(self, x):
        self.__x = x

    @property
    def y(self):
        return self.__y

    @y.setter
    def y(self, y):
        self.__y = y

    def __str__(self):
        return 'Point[{}, {}]'.format(self.x, self.y)


class Map:
    """
    地图实例
    """
    def __init__(self, row, col):
        self.row = row
        self.col = col


class Character:
    """
    人物（棋子）
    """
    def __init__(self, map):
        self.map = map
        self.current_point = Point(0, 0)  # 初始起点

    def move(self, direction, dist):
        """
        在棋盘上移动
        :param direction: 方向
        :param dist: 移动距离
        :return:
        """
        my_logger.info('移动前坐标: {}'.format(self.current_point))
        my_logger.info('移动方向: {}, 距离: {}'.format(direction, dist))
        print('移动前坐标: {}'.format(self.current_point))
        print('移动方向: {}, 距离: {}'.format(direction, dist))
        if direction == Direction.UP:
            self.current_point.y = (self.current_point.y - dist) % self.map.row
        elif direction == Direction.DOWN:
            self.current_point.y = (self.current_point.y + dist) % self.map.row
        elif direction == Direction.LEFT:
            self.current_point.x = (self.current_point.x - dist) % self.map.col
        elif direction == Direction.RIGHT:
            self.current_point.x = (self.current_point.x + dist) % self.map.col
        my_logger.info('移动后坐标: {}'.format(self.current_point))
        print('移动后坐标: {}'.format(self.current_point))


if __name__ == '__main__':
    game_map = Map(4, 4)
    c = Character(game_map)
    c.move(Direction.UP, 1)
    c.move(Direction.RIGHT, 3)
    c.move(Direction.LEFT, 4)
    c.move(Direction.DOWN, 2)
