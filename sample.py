# -*- coding: utf-8 -*-

from qqbot.utf8logger import DEBUG

def onInit(bot):
    # 初始化时被调用
    # 注意 : 此时 bot 尚未启动，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    # 只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    DEBUG('%s.onInit', __name__)

def onQQMessage(bot, contact, member, content):
    # 当收到 QQ 消息时被调用
    # bot     : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # contact : QContact 对象，消息的发送者
    # member  : QContact 对象，仅当本消息为 群或讨论组 消息时有效，代表实际发消息的成员
    # content : str 对象，消息内容
    DEBUG('onMessage: %s', content)
    if content == '-hello':
        bot.SendTo(contact, '你好，我是QQ机器人')
    elif content == '-stop':
        bot.SendTo(contact, 'QQ机器人已关闭')
        bot.Stop()
    elif content == '--version':
        bot.SendTo(contact, 'QQbot-' + bot.conf.version)
