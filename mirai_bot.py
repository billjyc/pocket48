# -*- coding:utf-8 -*-

from graia.application import GraiaMiraiApplication
from graia.application.friend import Friend
from graia.application.group import Group, Member
from graia.application.message.chain import MessageChain
from graia.application.message.elements.internal import Plain, At

from log.my_logger import logger
from utils.bot import bcc, bot
from utils.config_reader import ConfigReader
from qq.ai_reply import QQAIBot
from utils import util
import os
import sqlite3
import datetime
from datetime import date
import traceback

AUTO_REPLY = {}
items = ConfigReader.get_section('auto_reply')
logger.debug('items: %s', items)
for k, v in items:
    logger.debug('k: %s, v: %s', k, v)
    AUTO_REPLY[k] = v
    logger.debug('k in global_config.AUTO_REPLY: %s', k in AUTO_REPLY)
    logger.debug(AUTO_REPLY)


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


@bcc.receiver("FriendMessage")
async def friend_message_listener(app: GraiaMiraiApplication, friend: Friend, message: MessageChain):
    content = message.asDisplay()
    logger.info(content)


@bcc.receiver("GroupMessage")
async def group_message_listener(app: GraiaMiraiApplication, group: Group, message: MessageChain, member: Member):
    content = message.asDisplay()
    logger.info(content)
    user_id = member.id
    group_id = group.id
    logger.info(group)
    if member.id != 421497163:
        if content in AUTO_REPLY:
            await app.sendGroupMessage(group, MessageChain.create([
                Plain(AUTO_REPLY[content])
            ]))
        elif content.startswith('%'):
            # AI智能回复
            logger.debug('AI智能回复')
            if len(content) > 1 and content.startswith('%'):
                content = content[1:]
                logger.debug('提问内容: %s' % content)
                reply = ai_bot.nlp_textchat(content, member.id)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain(reply)
                ]))
        elif content == '抽签':
            try:
                message = draw_lottery(user_id, group_id)
                await app.sendGroupMessage(group, MessageChain.create([
                    At(user_id), Plain(message)
                ]))
            except Exception as e:
                logger.exception(e)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain('抽签出现错误')
                ]))
        elif content == '解签':
            try:
                message = solve_lottery(user_id, group_id)
                await app.sendGroupMessage(group, MessageChain.create([
                    At(user_id), Plain(message)
                ]))
            except Exception as e:
                logger.exception(e)
                await app.sendGroupMessage(group, MessageChain.create([
                    Plain('解签出现错误')
                ]))


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
            return '你今天已经抽过签了，请明天再来！'
        # 抽签步骤：随机抽取，存进DB
        current_lot = util.choice(lottery_data)[0]
        logger.info('本次抽签: {}'.format(current_lot))
        cursor_2.execute("""
                INSERT OR REPLACE INTO `t_lot` 
                (`user_id`, `group_id`, `lot_date`, `lot_id`, `has_solve`) VALUES (?, ?, ?, ?, ?)
            """, (user_id, group_id, now_date.strftime('%Y-%m-%d'), current_lot['ID'], 0))
        lottery_db.commit()
        res_str = '您抽到了第{}签：{}'.format(current_lot['ID'], current_lot['抽签'])
        logger.info(res_str)
    except Exception as e:
        logger.exception(e)
    finally:
        cursor_2.close()
    return res_str


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
            return '你今天还没有抽过签，赶快去抽签吧！'
        else:
            last_lot_date = datetime.datetime.strptime(rst[0], "%Y-%m-%d").date()
            logger.info('上次抽签日期: {}, 今天日期为: {}'.format(last_lot_date, now_date))
            if last_lot_date < now_date:
                logger.info('你今天还没有抽过签，赶快去抽签吧！')
                return '你今天还没有抽过签，赶快去抽签吧！'
            has_solve = int(rst[1])
            if has_solve == 1:
                logger.info('你今天已经解过签了，请明天再来抽签吧~')
                return '你今天已经解过签了，请明天再来抽签吧~'
            else:
                lot_id = str(rst[2])
                current_lot = lottery_data_map[lot_id]
                cursor_2.execute("""
                    UPDATE `t_lot` SET `has_solve`=1 WHERE `user_id`=? and `group_id`=?
                """, (user_id, group_id))
                lottery_db.commit()
                res_str = '{}'.format(current_lot['解签'])
                logger.info(res_str)
    except Exception as e:
        logger.exception(e)
    finally:
        cursor_2.close()
    return res_str


if __name__ == '__main__':
    bot.launch_blocking()
