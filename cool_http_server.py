# -*- coding: utf-8 -*-
import json

from cqhttp import Error

from log.my_logger import logger
from utils.bot import bot
from utils.config_reader import ConfigReader
# from utils import global_config
# from modian_plugin import modian_handler
from utils.mysql_util import mysql_util
from qq.ai_reply import QQAIBot

AUTO_REPLY = {}
items = ConfigReader.get_section('auto_reply')
logger.debug('items: %s', items)
for k, v in items:
    logger.debug('k: %s, v: %s', k, v)
    AUTO_REPLY[k] = v
    logger.debug('k in global_config.AUTO_REPLY: %s', k in AUTO_REPLY)
    logger.debug(AUTO_REPLY)

# groups = [483548995]
groups = ConfigReader.get_property('qq_conf', 'jizi_notify_groups').split(';')
test_groups = ConfigReader.get_property('qq_conf', 'auto_reply_groups').split(';')
print(groups)
logger.debug('test groups: %s' % test_groups)
modian_json = json.load(open("data/modian.json", encoding='utf8'))

modian_array = []
for modian_j in modian_json['monitor_activities']:
    modian_array.append(modian_j)

# AI智能闲聊机器人
ai_app_key = ConfigReader.get_property('AIBot', 'appkey')
ai_app_id = ConfigReader.get_property('AIBot', 'appid')
ai_bot = QQAIBot(ai_app_key, ai_app_id)


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

        # 关键词自动回复
        for k, v in AUTO_REPLY.items():
            if k in message.lower():
                logger.info('命中关键词: %s', k)
                bot.send(context, v)
                break
        # AI智能回复
        if str(group_id) in test_groups:
            logger.debug('AI智能回复')
            if len(message) > 1 and message.startswith('%'):
                content = message[1:]
                logger.debug('提问内容: %s' % content)
                reply = ai_bot.nlp_textchat(content, user_id)
                bot.send(context, reply)

        # 查询集资
        if str(group_id) in groups:
            if len(modian_array) > 0:
                if message == '-today':
                    get_jizi_ranking_list_by_date(context, 0)
                elif message == '-yesterday':
                    get_jizi_ranking_list_by_date(context, 1)
                elif message == '-排行榜':
                    get_huitui_rank(context)
                elif message.startswith('-查询'):
                    strs = message.split(' ')
                    if len(strs) == 2:
                        try:
                            modian_id = int(strs[1])
                            search_card(context, modian_id)
                        except:
                            bot.send(context, '摩点ID不符合规定~')
            else:
                bot.send(context, '目前并没有正在进行的集资项目T_T')
    except Error:
        pass
    # return {'reply': context['message'],
    #         'at_sender': False}  # 返回给 HTTP API 插件，走快速回复途径


def search_card(context, modian_id):
    """
    查询当前已经获得的卡片
    :param context:
    :param modian_id:
    :return:
    """
    try:
        from modian.modian_card_draw import CardDrawHandler
        handler = CardDrawHandler()
        handler.read_config()
        report = handler.get_cards(modian_id)
        bot.send(context, report)
    except Error as e:
        logger.error(e)
        bot.send(context, '查询出现错误！\n{}'.format(e))
    except Exception as exp:
        logger.error(exp)
        bot.send(context, '查询出现异常！\n{}'.format(exp))


def get_huitui_rank(context):
    """
    获取排行榜
    :return:
    """
    logger.debug('获取排行榜')
    rst = mysql_util.select_all("""
    select s.`name`, tc.`name`, CONVERT((tc.prop1 * 1.5 + tc.prop2 + tc.prop3 * 1.2 + tc.prop5 * 0.9) * (1 + tc.prop4 / 100), SIGNED) as ce
from `t_character` tc, `supporter` s where tc.`modian_id` = s.`id`
order by ce desc limit 10;
            """)
    rank = 1
    result_str = '灰推群侠传排行榜: \n'
    logger.debug(rst)
    for name, c_name, ce in rst:
        result_str += '{}.{}({}): {}\n'.format(rank, str(name, encoding='utf-8'),
                                               str(c_name, encoding='utf-8'), ce)
        rank += 1
    logger.debug(result_str)
    bot.send(context, result_str)


def get_jizi_ranking_list_by_date(context, day_diff):
    """
    根据日期获取集资榜单
    :param context:
    :param day_diff: 与今天相差的天数
    :return:
    """
    for modian in modian_array:
        rankings, total = __get_jizi_ranking_list_by_date_diff(modian['modian_pro_id'], day_diff)
        reply = '榜单: %s\n' % modian['modian_title']
        for rank in rankings:
            sub_message = '%s.%s: %s元\n' % (rank[3], str(rank[1], encoding='utf8'), rank[2])
            reply += sub_message
        reply += '总金额: %s元\n' % total
        bot.send(context, reply)


def __get_jizi_ranking_list_by_date_diff(pro_id, day_diff=0):
    """
    获取当日集资排名
    :param pro_id:
    :param day_diff:与今天相差的天数
    :return: 排名tuple 格式（supporter_id, supporter_name, total_amount, rank)
    """
    # 总额
    rst2 = mysql_util.select_one("""
                    select SUM(`order`.backer_money) as total 
                    from `order`
                    where `order`.pro_id = %s
                        and CURDATE()-%s=DATE(`order`.pay_time);
                """, (pro_id, day_diff))
    total = rst2[0]

    # 集资排名
    rst = mysql_util.select_all("""
            select `supporter`.id, `supporter`.name, SUM(`order`.backer_money) as total 
            from `order`, `supporter` 
            where `supporter`.id=`order`.supporter_id 
                and `order`.pro_id = %s
                and CURDATE()-%s=DATE(`order`.pay_time) 
            group by `order`.supporter_id 
            order by total desc;
        """, (pro_id, day_diff))
    cur_rank = 0
    row_tmp = 0
    last_val = -1
    new_rst = []
    for rank in rst:
        row_tmp += 1
        if rank[2] != last_val:
            cur_rank = row_tmp
        last_val = rank[2]
        rank_tmp = rank + (cur_rank, )
        new_rst.append(rank_tmp)
    logger.debug(new_rst)
    return new_rst, total


@bot.on_notice('group_increase')
def handle_group_increase(context):
    info = bot.get_group_member_info(group_id=context['group_id'],
                                     user_id=context['user_id'])
    nickname = info['nickname']
    logger.info('有人进群: qq: %s' % context['user_id'])
    name = nickname if nickname else '新人'
    # bot.send(context, message='最快的机器人欢迎@{}～'.format(name))
    bot.send(context, message='最快的机器人欢迎[CQ:at,qq={}]'.format(context['user_id']))
    logger.info('有人进群, QQ号: %s' % context['user_id'])
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


@bot.on_notice('group_decrease')
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
