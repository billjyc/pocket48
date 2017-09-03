# -*- coding: utf-8 -*-

from qqbot import _bot as bot


class QQHandler:
    def __init__(self):
        pass

    def login(self, qq_number):
        bot.Login(['-u', qq_number])

    def list_group(self, group_number):
        return bot.List('group', group_number)

    @classmethod
    def send(cls, receiver, message):
        bot.SendTo(receiver, message)

if __name__ == '__main__':
    print bot.conf.qq
    # handler = QQHandler()
    #handler.login('421497163')
    #groups = handler.list_group('483548995')
    #if groups:
     #   group = groups[0]
     #   handler.send(group, 'test')
