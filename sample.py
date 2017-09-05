# -*- coding: utf-8 -*-
from qqbot import qqbotsched
from qqbot.utf8logger import DEBUG, INFO, ERROR
import json
import time
import random

from config_reader import ConfigReader
from pocket48_handler import Pocket48Handler
from qqhandler import QQHandler

pocket48_handler = None
qq_handler = None
roomId = 0
group_number = '0'
test_group_number = '0'
big_group_number = '0'

def onInit(bot):
    # 初始化时被调用
    # 注意 : 此时 bot 尚未启动，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    #       只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    DEBUG('%s.onInit', __name__)


def onQrcode(bot, pngPath, pngContent):
    # 获取到二维码时被调用
    # 注意 : 此时 bot 尚未启动，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    #       只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    # pngPath : 二维码图片路径
    # pngContent : 二维码图片内容
    DEBUG('%s.onQrcode: %s (%d bytes)', __name__, pngPath, len(pngContent))


def onQQMessage(bot, contact, member, content):
    # 当收到 QQ 消息时被调用
    # bot     : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # contact : QContact 对象，消息的发送者
    # member  : QContact 对象，仅当本消息为 群或讨论组 消息时有效，代表实际发消息的成员
    # content : str 对象，消息内容
    DEBUG('member: %s', str(getattr(member, 'uin')))
    # DEBUG('content: %s', content)
    # DEBUG('contact: %s', contact.ctype)
    global group_number, test_group_number, big_group_number
    if contact.ctype == 'group' and contact.qq in [group_number, big_group_number, test_group_number]:
        if content.startswith('-'):
            if '@ME' in content:
                bot.SendTo(contact, member.name + '，艾特我干嘛呢？')
            elif content == '-version':
                bot.SendTo(contact, 'QQbot-' + bot.conf.version)
            elif content == '-fxf':
                strs = ConfigReader.get_property('profile', 'i_love_fxf').split(';')
                bot.SendTo(contact, random_str(strs))
            elif content in ['-生日', '-生诞', '-集资', '-我有钱']:
                jizi_link = ConfigReader.get_property('profile', 'jizi_link')
                bot.SendTo(contact, '集资链接: %s' % jizi_link)
            elif content in ['-微博', '-超话']:
                weibo_link = ConfigReader.get_property('profile', 'weibo_link')
                super_tag = ConfigReader.get_property('profile', 'super_tag')
                bot.SendTo(contact, '微博: %s\n超级话题: %s' % (weibo_link, super_tag))
            elif content in ['-公演']:
                live_link = ConfigReader.get_property('profile', 'live_link')
                strs = ConfigReader.get_property('profile', 'live_schedule').split(';')
                live_schedule = '\n'.join(strs)
                msg = '直播传送门: %s\n本周安排: %s' % (live_link, live_schedule)
                bot.SendTo(contact, msg)
            else:
                no_such_command = ConfigReader.get_property('profile', 'no_such_command')
                bot.SendTo(contact, no_such_command)


def onInterval(bot):
    # 每隔 5 分钟被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    DEBUG('%s.onInterval', __name__)


def onStartupComplete(bot):
    # 启动完成时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    DEBUG('%s.onStartupComplete', __name__)
    global qq_handler, pocket48_handler, roomId, group_number, test_group_number, big_group_number
    group_number = ConfigReader.get_group_number()
    test_group_number = ConfigReader.get_test_group_number()
    big_group_number = ConfigReader.get_property('qq_conf', 'big_group_number')
    roomId = ConfigReader.get_member_room_number('fengxiaofei')
    qq_number = ConfigReader.get_qq_number('qq')
    qq_handler = QQHandler()
    qq_handler.update()
    groups = qq_handler.list_group(group_number)
    test_groups = qq_handler.list_group(test_group_number)

    if groups or test_groups:
        if test_groups:
            test_group = test_groups[0]
        if groups:
            group = groups[0]
        else:
            group = test_groups[0]

        # INFO('Group: ' + group)
        # INFO('Test Group: ' + test_group)
        pocket48_handler = Pocket48Handler(group, test_group)
    else:
        ERROR('群号输入不正确！')


def onUpdate(bot, tinfo):
    # 某个联系人列表更新时被调用
    # bot : QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # tinfo : 联系人列表的代号，详见文档中关于 bot.List 的第一个参数的含义解释
    DEBUG('%s.onUpdate: %s', __name__, tinfo)


def onPlug(bot):
    # 本插件被加载时被调用，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    # 提醒：如果本插件设置为启动时自动加载，则本函数将延迟到登录完成后被调用
    # bot ： QQBot 对象
    DEBUG('%s.onPlug', __name__)


def onUnplug(bot):
    # 本插件被卸载时被调用
    # bot ： QQBot 对象，提供 List/SendTo/GroupXXX/Stop/Restart 等接口，详见文档第五节
    DEBUG('%s.onUnplug', __name__)


def onExit(bot, code, reason, error):
    # MainLoop（主循环）终止时被调用， Mainloop 是一个无限循环，QQBot 登录成功后便开始运
    # 行，当且仅当以下事件发生时 Mainloop 终止：
    #     1） 调用了 bot.Stop() ，此时：
    #         code = 0, reason = 'stop', error = None
    #     2） 调用了 bot.Restart() ，此时：
    #         code = 201, reason = 'restart', error = None
    #     3） 调用了 bot.FreshRestart() ，此时：
    #         code = 202, reason = 'fresh-restart', error = None
    #     4） 调用了 sys.exit(x) （ x 不等于 0,201,202,203 ），此时：
    #         code = x, reason = 'system-exit', error = None
    #     5） 登录的 cookie 已过期，此时：
    #         code = 203, reason = 'login-expire', error = None
    #     6） 发生未知错误 e （暂未出现过，出现则表明 qqbot 程序内部可能存在错误），此时：
    #         code = 1, reason = 'unknown-error', error = e
    #
    # 一般情况下：
    #     发生 1/2/3/4 时，可以安全的调用 bot.List/SendTo/GroupXXX 等接口
    #     发生 5/6 时，调用 bot.List/SendTo/GroupXXX 等接口将出错
    #
    # 一般情况下，用户插件内的代码和运行错误会被捕捉并忽略，不会引起 MainLoop 的退出
    #
    # 本函数被调用后，会执行 sys.exit(code) 退出本次进程并返回到父进程，父进程会根据
    # “ code 的数值” 以及 “是否配置为自动重启模式” 来决定是否重启 QQBot 。
    #

    DEBUG('%s.onExit: %r %r %r', __name__, code, reason, error)


def onExpire(bot):
    # 登录过期时被调用
    # 注意 : 此时登录已过期，因此请勿在本函数中调用 bot.List/SendTo/GroupXXX/Stop/Restart 等接口
    #       只可以访问配置信息 bot.conf
    # bot : QQBot 对象
    DEBUG('ON-EXPIRE')


def random_str(strs):
    return random.choice(strs)


@qqbotsched(hour='10')
def restart_sche(bot):
    DEBUG('RESTART scheduled')
    bot.FreshRestart()


@qqbotsched(second='*/30')
def get_room_msgs(bot):
    global qq_handler, pocket48_handler, roomId

    r1 = pocket48_handler.get_member_room_msg(roomId)
    pocket48_handler.parse_room_msg(r1)
    r2 = pocket48_handler.get_member_room_comment(roomId)
    pocket48_handler.parse_room_msg(r2)
    pocket48_handler.last_monitor_time = int(time.time())

