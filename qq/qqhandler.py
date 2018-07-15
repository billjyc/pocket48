# -*- coding: utf-8 -*-

"""
封装酷Q HTTP API
https://richardchien.github.io/coolq-http-api/3.3/#/API
"""
from log.my_logger import logger
from utils.bot import bot


class QQHandler:
    def __init__(self):
        pass

    @classmethod
    def get_login_info(cls):
        """
        获取登录号信息
        :return:
        """
        login_info = bot.get_login_info()
        logger.debug('login_info: %s', login_info)
        return login_info

    @classmethod
    def get_group_list(cls):
        group_list = bot.get_group_list()
        logger.debug('group list: %s', group_list)
        return group_list

    @classmethod
    def get_group_number(cls, group_number):
        """
        获取对应群的成员人数
        :param group_number:
        :return:
        """
        group_member_list = bot.get_group_member_list(group_id=group_number)
        return len(group_member_list)

    @classmethod
    def send_to_groups(cls, groups, message):
        for group in groups:
            bot.send_group_msg(group_id=group, message=message)


if __name__ == '__main__':
    groups = ['483548995']
    group_list = QQHandler.get_group_list()
    QQHandler.send_to_groups(groups, '[CQ:image,file=1.jpg]')
    QQHandler.send_to_groups(groups, '[CQ:music,type=qq,id=212628607]')
    print('1')
