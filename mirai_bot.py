# -*- coding:utf-8 -*-

from graia.application import GraiaMiraiApplication
from graia.application.friend import Friend
from graia.application.group import Group
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain

from log.my_logger import logger
from utils.bot import bcc, bot
from utils.config_reader import ConfigReader

AUTO_REPLY = {}
items = ConfigReader.get_section('auto_reply')
logger.debug('items: %s', items)
for k, v in items:
    logger.debug('k: %s, v: %s', k, v)
    AUTO_REPLY[k] = v
    logger.debug('k in global_config.AUTO_REPLY: %s', k in AUTO_REPLY)
    logger.debug(AUTO_REPLY)


@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    word_list = message.get(Plain)
    print(word_list)
    for word in word_list:
        if word.text in AUTO_REPLY:
            await app.sendFriendMessage(friend, MessageChain.create([
                Plain(AUTO_REPLY[word.text])
            ]))


@bcc.receiver("GroupMessage")
async def group_message_listener(app: GraiaMiraiApplication, group: Group, message: MessageChain):
    # await app.sendGroupMessage(group, MessageChain.create([
    #     Plain("我还活着")
    # ]))
    print(message.asDisplay())


if __name__ == '__main__':
    bot.launch_blocking()
