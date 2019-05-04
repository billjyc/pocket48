# -*- coding: utf-8 -*-
import json

from cqhttp import Error

from log.my_logger import logger
from utils.bot import bot
from utils.config_reader import ConfigReader
# from utils import global_config
# from modian_plugin import modian_handler
from qq.ai_reply import QQAIBot
from utils import util
import os
import sqlite3
import datetime
from datetime import date

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 抽签数据读取
try:
    lottery_data = util.read_csv(os.path.join(BASE_DIR, 'data', 'lottery', 'data.csv'))
    logger.info(lottery_data)
    lottery_data_map = {}
    for lottery in lottery_data:
        lottery_id = lottery['ID']
        lottery_data_map[lottery_id] = lottery

    lottery_db = sqlite3.connect(os.path.join(BASE_DIR, 'data', 'lottery', 'lottery.db'), check_same_thread=False)
    cursor = lottery_db.cursor()
    cursor.execute("""
                    CREATE TABLE IF NOT EXISTS 't_lot' (
                        user_id  VARCHAR( 100 ),
                        group_id VARCHAR( 100 ),
                        lot_date         DATE,
                        lot_id       INTEGER,
                        has_solve INTEGER DEFAULT ( 0 ),
                        UNIQUE ( user_id, group_id ) 
                    );""")
except Exception as e:
    logger.exception(e)
finally:
    cursor.close()

try:
    from utils.mysql_util import mysql_util
except Exception as e:
    logger.exception('导入mysql出现错误', e)


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

        if str(group_id) in test_groups:
            # AI智能回复
            logger.debug('AI智能回复')
            if len(message) > 1 and message.startswith('%'):
                content = message[1:]
                logger.debug('提问内容: %s' % content)
                reply = ai_bot.nlp_textchat(content, user_id)
                bot.send(context, reply)
            elif message == '-express':
                express_message = '[CQ:image,file=%s]' % (
                     'lt_020.png')
                express_message2 = '[CQ:image,file=%s]' % (
                     'tsj_013.gif')
                express_message3 = '[CQ:image,file=%s]' % (
                    'xxy_040.png')
                logger.debug(express_message)
                logger.debug(express_message2)
                logger.debug(express_message3)
                bot.send(context, express_message)
                bot.send(context, express_message2)
                bot.send(context, express_message3)
            elif message == '-audio':
                import random
                files = ['1.aac', '2.aac', '3.aac', '4.aac', '5.aac']
                express_message = '[CQ:record,file=%s]'.format(random.choice(files))
                bot.send(context, express_message)
            # elif message == '抽签':
            #     try:
            #         message = draw_lottery(user_id, group_id)
            #         bot.send(context, message)
            #     except Error as err:
            #         logger.exception(err)
            #     except Exception as e:
            #         logger.exception(e)
            #         bot.send(context, '抽签出现错误！')
            # elif message == '解签':
            #     try:
            #         message = solve_lottery(user_id, group_id)
            #         bot.send(context, message)
            #     except Error as err:
            #         logger.exception(err)
            #     except Exception as e:
            #         logger.exception(e)
            #         bot.send(context, '解签出现错误！')

        # 查询集资
        if str(group_id) in groups:
            if len(modian_array) > 0:
                if message == '-today':
                    get_jizi_ranking_list_by_date(context, 0)
                elif message == '-yesterday':
                    get_jizi_ranking_list_by_date(context, 1)
                elif message == '-战况':
                    message = get_modian_pk()
                    bot.send(context, message)
                # elif message == '-排行榜':
                #     get_huitui_rank(context)
                elif message == '-help':
                    help_msg = """
                        查询当前集卡情况: 【-查询 摩点ID】，
                        积分抽卡（积分数量必须是15的倍数）: 【-积分抽 摩点ID 积分数量】，
                        补抽卡: 【-补抽 摩点ID 补抽金额】
                    """
                    bot.send(context, help_msg)
                elif message.startswith('-查询'):
                    strs = message.split(' ')
                    if len(strs) == 2:
                        search_card(context, strs[1])
                    else:
                        bot.send(context, '格式为【-查询 摩点ID】的形式，请重试~')
                elif message.startswith('-积分抽'):
                    from utils import util
                    admins = util.read_txt(os.path.join(BASE_DIR, 'data', 'card_draw', 'admin.txt'))
                    if str(user_id) not in admins:
                        logger.info('QQ：{} 无权限操作积分抽卡！')
                        return
                    strs = message.split(' ')
                    if len(strs) == 3:
                        draw_card_using_score(context, strs[1], strs[2])
                    else:
                        bot.send(context, '格式为【-积分抽 摩点ID 积分数量】的形式，请重试~')
                elif message.startswith('-补抽'):
                    from utils import util
                    admins = util.read_txt(os.path.join(BASE_DIR, 'data', 'card_draw', 'admin.txt'))
                    if str(user_id) not in admins:
                        logger.info('QQ：{} 无权限操作补抽卡！')
                        return
                    strs = message.split(' ')
                    if len(strs) == 3:
                        draw_missed_card(context, strs[1], strs[2])
                    else:
                        bot.send(context, '格式为【-补抽 摩点ID 补抽金额】的形式，请重试~')
                # elif message.upper() == '-PK':
                #     try:
                #         from modian_plugin import modian_handler
                #         message = modian_handler.pk_modian_activity()
                #         bot.send(context, message)
                #     except Error as e:
                #         logger.exception(e)
                #     except Exception as e:
                #         logger.exception(e)
                #         bot.send(context, '查询PK出现错误！')
            else:
                bot.send(context, '目前并没有正在进行的集资项目T_T')
    except Error:
        pass
    # return {'reply': context['message'],
    #         'at_sender': False}  # 返回给 HTTP API 插件，走快速回复途径


def draw_lottery(user_id, group_id):
    """
    抽签
    :param user_id:
    :param group_id:
    :return:
    """
    logger.info('抽签，QQ={}, group_id={}'.format(user_id, group_id))
    cursor_2 = lottery_db.cursor()
    res_str = ''
    try:
        # 是否有抽签记录
        c = cursor_2.execute("""
            SELECT `lot_date` FROM `t_lot` WHERE user_id=? and group_id=?
        """, (user_id, group_id))
        rst = c.fetchone()
        can_lot = True
        # 是否可以抽签
        now_date = date.today()
        if rst:
            last_lot_date = datetime.datetime.strptime(rst[0], "%Y-%m-%d").date()
            logger.info('上次抽签日期: {}, 今天日期为: {}'.format(last_lot_date, now_date))
            if last_lot_date >= now_date:
                can_lot = False
        if not can_lot:
            return '[CQ:at,qq={}] 你今天已经抽过签了，请明天再来！'.format(user_id)
        # 抽签步骤：随机抽取，存进DB
        current_lot = util.choice(lottery_data)[0]
        logger.info('本次抽签: {}'.format(current_lot))
        cursor_2.execute("""
                INSERT OR REPLACE INTO `t_lot` 
                (`user_id`, `group_id`, `lot_date`, `lot_id`, `has_solve`) VALUES (?, ?, ?, ?, ?)
            """, (user_id, group_id, now_date.strftime('%Y-%m-%d'), current_lot['ID'], 0))
        lottery_db.commit()
        res_str = '[CQ:at,qq={}] 您抽到了第{}签：{}'.format(user_id, current_lot['ID'], current_lot['抽签'])
        logger.info(res_str)
    except Exception as e:
        logger.exception(e)
    finally:
        cursor_2.close()
    return res_str


def get_modian_pk():
    """
    获取当前PK战况
    :return:
    """
    from modian_plugin import modian_handler
    rst = modian_handler.pk_modian_activity()
    return rst


def solve_lottery(user_id, group_id):
    """
    解签
    :param user_id:
    :param group_id:
    :return:
    """
    logger.info('解签，QQ={}, group_id={}'.format(user_id, group_id))
    res_str = ''
    cursor_2 = lottery_db.cursor()
    try:
        # 是否有抽签记录
        c = cursor_2.execute("""
                    SELECT `lot_date`, `has_solve`, `lot_id` FROM `t_lot` WHERE user_id=? and group_id=?
                """, (user_id, group_id))
        rst = c.fetchone()
        now_date = date.today()
        if not rst:
            logger.info('你今天还没有抽过签，赶快去抽签吧！')
            return '[CQ:at,qq={}] 你今天还没有抽过签，赶快去抽签吧！'.format(user_id)
        else:
            last_lot_date = datetime.datetime.strptime(rst[0], "%Y-%m-%d").date()
            logger.info('上次抽签日期: {}, 今天日期为: {}'.format(last_lot_date, now_date))
            if last_lot_date < now_date:
                logger.info('你今天还没有抽过签，赶快去抽签吧！')
                return '[CQ:at,qq={}] 你今天还没有抽过签，赶快去抽签吧！'.format(user_id)
            has_solve = int(rst[1])
            if has_solve == 1:
                logger.info('你今天已经解过签了，请明天再来抽签吧~')
                return '[CQ:at,qq={}] 你今天已经解过签了，请明天再来抽签吧~'.format(user_id)
            else:
                lot_id = str(rst[2])
                current_lot = lottery_data_map[lot_id]
                cursor_2.execute("""
                    UPDATE `t_lot` SET `has_solve`=1 WHERE `user_id`=? and `group_id`=?
                """, (user_id, group_id))
                lottery_db.commit()
                res_str = '[CQ:at,qq={}] {}'.format(user_id, current_lot['解签'])
                logger.info(res_str)
    except Exception as e:
        logger.exception(e)
    finally:
        cursor_2.close()
    return res_str


def search_card(context, modian_id):
    """
    查询当前已经获得的卡片
    :param context:
    :param modian_id:
    :return:
    """
    try:
        from modian.modian_card_draw import CardDrawHandler
        card_draw_handler = CardDrawHandler()
        card_draw_handler.read_config()
        from utils import util
        is_digit = util.is_positive_integer(modian_id)
        if not is_digit:
            bot.send('摩点ID为纯数字，请重试~')
            return
        report = card_draw_handler.get_cards(int(modian_id))
        bot.send(context, report)
    except Error as e:
        logger.error(e)
        # bot.send(context, '查询出现错误！\n{}'.format(traceback.print_exc()))
    except Exception as exp:
        logger.error(exp)
        # bot.send(context, '查询出现异常！\n{}'.format(traceback.print_exc()))


def draw_card_using_score(context, modian_id, score):
    """
    消耗积分抽卡
    :param context:
    :param modian_id:
    :return:
    """
    from utils import util
    from modian.modian_card_draw import CardDrawHandler
    card_draw_handler = CardDrawHandler()
    card_draw_handler.read_config()
    score_is_digit = util.is_positive_integer(score)
    modian_id_is_digit = util.is_positive_integer(modian_id)
    if not modian_id_is_digit:
        bot.send(context, '输入的摩点ID不符合规范，请重试~')
        return
    if not score_is_digit:
        bot.send(context, '输入的积分数不符合规范，请重试~')
    try:
        report = card_draw_handler.draw_missed_cards(int(modian_id), int(score))
        bot.send(context, report)
    except:
        logger.error('积分抽卡出现错误！')


def draw_missed_card(context, modian_id, backer_money):
    """
    补抽卡
    :param context:
    :param modian_id:
    :param backer_money:
    :return:
    """
    from utils import util
    from modian.modian_card_draw import CardDrawHandler
    import time
    card_draw_handler = CardDrawHandler()
    card_draw_handler.read_config()
    money_is_digit = util.is_digit(backer_money)
    modian_id_is_digit = util.is_positive_integer(modian_id)
    if not modian_id_is_digit:
        bot.send(context, '输入的摩点ID不符合规范，请重试~')
        return
    if not money_is_digit:
        bot.send(context, '输入的金额不符合规范，请重试~')
    try:
        report = card_draw_handler.draw(modian_id, '补抽用户', float(backer_money),
                                        util.convert_timestamp_to_timestr(int(time.time() * 1000)))
        bot.send(context, report)
    except:
        logger.error('补抽卡出现错误！')


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
        rank_tmp = rank + (cur_rank,)
        new_rst.append(rank_tmp)
    logger.debug(new_rst)
    return new_rst, total


@bot.on_notice('group_increase')
def handle_group_increase(context):
    info = bot.get_group_member_info(group_id=context['group_id'],
                                     user_id=context['user_id'])
    nickname = info['nickname']
    logger.info('有人进群: qq: %s' % context['user_id'])
#     name = nickname if nickname else '新人'
#     # bot.send(context, message='最快的机器人欢迎@{}～'.format(name))
#     bot.send(context, message='最快的机器人欢迎[CQ:at,qq={}]'.format(context['user_id']))
#     logger.info('有人进群, QQ号: %s' % context['user_id'])
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
    # draw_lottery('793746995', '483548995')
    # solve_lottery('793746995', '483548995')
    bot.run(host='127.0.0.1', port=8200)
