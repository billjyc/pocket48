# -*- coding: utf-8 -*-
from cqhttp import CQHttp, Error
from log.my_logger import logger
from utils.config_reader import ConfigReader
from utils import global_config
from modian_plugin import modian_handler

bot = CQHttp(api_root='http://127.0.0.1:5700', access_token='aslkfdjie32df', secret='abc')
AUTO_REPLY = {}
items = ConfigReader.get_section('auto_reply')
logger.debug('items: %s', items)
for k, v in items:
    logger.debug('k: %s, v: %s', k, v)
    AUTO_REPLY[k] = v
    logger.debug('k in global_config.AUTO_REPLY: %s', k in AUTO_REPLY)
    logger.debug(AUTO_REPLY)


@bot.on_message()
def handle_msg(context):
    # 下面这句等价于 bot.send_private_msg(user_id=context['user_id'], message='你好呀，下面一条是你刚刚发的：')
    try:
        message = context['message']
        group_id = context['group_id']
        user_id = context['user_id']
        logger.info('收到一条消息: 群: %s, 发送人: %s, %s', group_id, user_id, message)
        if user_id == context['self_id']:
            logger.debug('不处理自己发送的消息')
            return

        logger.info(AUTO_REPLY)

        for k, v in AUTO_REPLY.items():
            if k in message.lower():
                logger.info('命中关键词: %s', k)
                bot.send(context, v)
                break
        # bot.send(context, '你好呀，下面一条是你刚刚发的：')

        if message == '-今日榜单':
            if int(group_id) in global_config.JIZI_NOTIFY_GROUPS:
                if len(global_config.MODIAN_ARRAY) > 0:
                    for modian in global_config.MODIAN_ARRAY:
                        rankings, total = modian_handler.get_today_jizi_ranking_list(modian.pro_id)
                        reply = '今日榜单: %s\n' % modian.title
                        for rank in rankings:
                            sub_message = '%s.%s: %s元\n' % (rank[3], rank[1], rank[2])
                            reply += sub_message
                        reply += '总金额: %s\n'
                        bot.send(context, reply)
                else:
                    bot.send(context, '目前并没有正在进行的集资项目T_T')
    except Error:
        pass
    # return {'reply': context['message'],
    #         'at_sender': False}  # 返回给 HTTP API 插件，走快速回复途径


@bot.on_event('group_increase')
def handle_group_increase(context):
    info = bot.get_group_member_info(group_id=context['group_id'],
                                     user_id=context['user_id'])
    nickname = info['nickname']
    name = nickname if nickname else '新人'
    # bot.send(context, message='最快的机器人欢迎@{}～'.format(name))
    bot.send(context, message='最快的机器人欢迎[CQ:at,qq={}]'.format(context['user_id']))
#     if context['group_id'] == int('101724227'):
#         bot.send(context, message="""
# 欢迎加入SNH48-冯晓菲应援会，今天的机长是灰灰
# 为了更好的了解灰灰，给灰灰应援～
# 冯晓菲剧场应援群：499121036
# B站补档推荐up主：冯晓菲的后置摄像头，冯晓菲甜甜的wink
# 网易云电台：冯晓菲的地上波
# 欢迎关注微博：@SNH48-冯晓菲应援会
# @冯晓菲的萝卜养护中心
#         """)


@bot.on_event('group_decrease')
def handle_group_decrease(context):
    user_id = context['user_id']
    logger.info('有人退群，QQ号: %s', user_id)


@bot.on_request('group')
def handle_group_request(context):
    if context['message'] != 'some-secret':
        # 验证信息不符，拒绝
        return {'approve': False, 'reason': '你填写的验证信息有误'}
    return {'approve': True}


if __name__ == '__main__':
    bot.run(host='127.0.0.1', port=8200)
