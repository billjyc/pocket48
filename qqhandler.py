# -*- coding: utf-8 -*-

from qqbot import _bot as bot

from qqbot.utf8logger import DEBUG, INFO, ERROR

import time


class QQHandler:
    def __init__(self):
        pass

    def login(self, qq_number):
        bot.Login(['-u', qq_number])

    def list_group(self, groups):
        """
        根据群号查询对应的QContact对象
        :param groups:
        :return: list of QContact
        """
        result = []
        for group_number in groups:
            if group_number:
                group = bot.List('group', group_number)
                if group:
                    result.append(group[0])
                else:
                    ERROR('没有搜索到对应的群号: %s', group_number)
        return result

    def update(self):
        bot.Update('buddy')
        bot.Update('group')

    def restart(self):
        DEBUG('RESTART')
        bot.Restart()

    def fresh_restart(self):
        bot.FreshRestart()

    def stop(self):
        bot.Stop()

    @classmethod
    def send(cls, receiver, message):
        bot.SendTo(receiver, message)

    @classmethod
    def send_to_groups(cls, groups, message):
        for group in groups:
            bot.SendTo(group, message)
            time.sleep(2)


if __name__ == '__main__':
    print bot.conf.qq
