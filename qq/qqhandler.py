# -*- coding: utf-8 -*-

"""
封装酷Q HTTP API
https://richardchien.github.io/coolq-http-api/3.3/#/API
"""
from log.my_logger import logger
from utils.bot import bot
from graia.application.group import Group, MemberPerm
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain, Image, At, AtAll, Voice, Face


class QQHandler:
    def __init__(self):
        pass

    # @classmethod
    # def get_login_info(cls):
    #     """
    #     获取登录号信息
    #     :return:
    #     """
    #     login_info = bot.get_login_info()
    #     logger.debug('login_info: %s', login_info)
    #     return login_info

    @classmethod
    def get_group_list(cls):
        group_list = bot.groupList()
        logger.debug('group list: %s', group_list)
        rst = []
        for group in group_list:
            rst.append(group.id)
        return group_list

    @classmethod
    def get_group_number(cls, group_number):
        """
        获取对应群的成员人数
        :param group_number:
        :return:
        """
        group_member_list = bot.memberList(group=int(group_number))
        return len(group_member_list)

    @classmethod
    def send_to_groups(cls, groups, message):
        for group in groups:
            try:
                logger.info(group)
                group = Group(id=int(group), name='群', accountPerm=MemberPerm.Member)
                bot.sendGroupMessage(group, message=MessageChain.create([Plain(message)]))
            except Exception as exp:
                logger.exception(exp)


if __name__ == '__main__':
    groups = ['483548995']
    group_list = QQHandler.get_group_list()
    QQHandler.send_to_groups(groups, '[CQ:image,file=1.jpg]')
    QQHandler.send_to_groups(groups, '[CQ:music,type=qq,id=212628607]')
    print('1')
