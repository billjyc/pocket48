# -*- coding: utf-8 -*-

from qqbot import _bot as bot

from qqbot.utf8logger import DEBUG, INFO, ERROR

import time
from utils.config_reader import ConfigReader


class QQHandler:
    def __init__(self):
        pass

    @classmethod
    def login(self, qq_number):
        bot.Login(['-u', qq_number])

    @classmethod
    def list_group(cls, groups):
        """
        根据群号查询对应的QContact对象
        :param groups:
        :return: list of QContact
        """
        result = []
        for group_number in groups:
            if group_number:
                group_name = ConfigReader.get_group_name(group_number)
                DEBUG('group number: %s, group_name: %s', group_number, group_name)
                group = bot.List('group', group_name)
                DEBUG(group)
                if group:
                    result.append(group[0])
                else:
                    ERROR('没有搜索到对应的群号: %s', group_number)
                    raise Exception('没有group number对应的群号')
        return result

    @classmethod
    def get_group_number(cls, group_number):
        """
        获取对应群的成员人数
        :param group_number:
        :return:
        """
        number = 0
        if group_number:
            group_name = ConfigReader.get_group_name(group_number)
            DEBUG('group number: %s, group_name: %s', group_number, group_name)
            group = bot.List('group', group_name)
            if group:
                g = group[0]
                member_list = bot.List(g)
                # DEBUG(member_list)
                number = len(member_list)
            else:
                ERROR('没有搜索到对应的群号: %s', group_number)
                raise Exception('没有group number对应的群号')
        return number

    @classmethod
    def update(cls):
        bot.Update('buddy')
        bot.Update('group')

    @classmethod
    def restart(cls):
        DEBUG('RESTART')
        bot.Restart()

    @classmethod
    def fresh_restart(cls):
        bot.FreshRestart()

    @classmethod
    def stop(self):
        bot.Stop()

    @classmethod
    def send(cls, receiver, message):
        bot.SendTo(receiver, message)

    @classmethod
    def send_to_groups(cls, groups, message):
        DEBUG('send to groups: %s', groups)
        for group in groups:
            bot.SendTo(group, message)
            time.sleep(2)


if __name__ == '__main__':
    print bot.conf.qq
