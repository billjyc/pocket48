# -*- coding: utf-8 -*-

from log.my_logger import weibo_logger as my_logger

from weibo.weibo_handler import WeiboMonitor
from qq.qqhandler import QQHandler
from utils.config_reader import ConfigReader
from utils import global_config

from utils.scheduler import scheduler
import time


# @scheduler.scheduled_job('cron', second='35')
def update_weibo_conf():
    global weibo_monitor

    my_logger.debug('读取微博配置')
    global_config.MEMBER_WEIBO_GROUPS = ConfigReader.get_property('qq_conf', 'member_weibo_groups').split(';')

    for task in global_config.POCKET48_LISTEN_TASKS:
        uid = task.member.weibo_uid
        my_logger.debug('weibo uid: %s', uid)
        if uid != 0:
            weibo_monitor.getWBQueue(task)
        else:
            my_logger.error('微博UID填写错误，请检查')


@scheduler.scheduled_job('cron', minute='*', second='55')
def monitor_member_weibo():
    global weibo_monitor

    for task in global_config.POCKET48_LISTEN_TASKS:
        newWB = weibo_monitor.startMonitor(task)
        if newWB is not None:
            my_logger.debug(newWB)
            member_weibo_groups = global_config.MEMBER_WEIBO_GROUPS
            weibo_text = newWB['text']

            if task.member.member_id == 5973:
                message = 'SNH48发博啦:\n{}\n原文链接: {}\n'.format(weibo_text, newWB['scheme'])
                if newWB['created_at'] == '刚刚':
                    if '冯晓菲' in weibo_text or 'team x' in weibo_text.lower() or 'X队' in weibo_text.lower() or \
                            'teamx' in weibo_text.lower():
                        # QQHandler.send_to_groups(['483548995'], '包含关键词微博')
                        # QQHandler.send_to_groups(member_weibo_groups, message)
                        if 'video_url' in newWB.keys():
                            pass
                            # QQHandler.send_to_groups(member_weibo_groups, '[CQ:image,file={}]'.format(newWB['video_url']))
                        if 'picUrls' in newWB.keys():
                            # for pic in newWB['picUrls']:
                            # QQHandler.send_to_groups(member_weibo_groups, '[CQ:image,file={}]'.format(newWB['picUrls'][0]))
                            pass
                    else:
                        # QQHandler.send_to_groups(['483548995'], '不包含关键词微博')
                        if 'retweeted_status' in newWB.keys():
                            if '冯晓菲' in newWB['retweeted_status']['user']:
                                message = 'SNH48转发了微博:\n{}\n原文链接: {}\n'.format(weibo_text, newWB['scheme'])
                                text = message + '\n转发微博:\n@{}: {}'.format(newWB['retweeted_status']['user'],
                                                             newWB['retweeted_status']['text'])
                                # QQHandler.send_to_groups(member_weibo_groups, text)
                                if 'video_url' in newWB.keys():
                                    pass
                                    # QQHandler.send_to_groups(member_weibo_groups, '[CQ:image,file={}]'.format(newWB['video_url']))
                                if 'picUrls' in newWB.keys():
                                    # for pic in newWB['picUrls']:
                                    # QQHandler.send_to_groups(member_weibo_groups,
                                    #                          '[CQ:image,file={}]'.format(newWB['picUrls'][0]))
                                    pass
                            else:
                                text = message + '转发微博:\n@{}: {}'.format(newWB['retweeted_status']['user'],
                                                                        newWB['retweeted_status']['text'])
                                # QQHandler.send_to_groups(['483548995'], text)
                                if 'video_url' in newWB.keys():
                                    pass
                                    # QQHandler.send_to_groups(['483548995'], '[CQ:image,file={}]'.format(newWB['video_url']))
                                if 'picUrls' in newWB.keys():
                                    # for pic in newWB['picUrls']:
                                    # QQHandler.send_to_groups(['483548995'],
                                    #                          '[CQ:image,file={}]'.format(newWB['picUrls'][0]))
                                    pass
                        else:
                            # QQHandler.send_to_groups(['483548995'], message)
                            if 'video_url' in newWB.keys():
                                pass
                                # QQHandler.send_to_groups(['483548995'], '[CQ:image,file={}]'.format(newWB['video_url']))
                            if 'picUrls' in newWB.keys():
                                # for pic in newWB['picUrls']:
                                # QQHandler.send_to_groups(['483548995'],
                                #                          '[CQ:image,file={}]'.format(newWB['picUrls'][0]))
                                pass

            elif task.member.member_id == 6432:
                message = '{}发微博啦!\n{}\n{}'.format(task.member.name, weibo_text, newWB['scheme'])
                if newWB['created_at'] == '刚刚':
                    # QQHandler.send_to_groups(member_weibo_groups, message)
                    if 'video_url' in newWB.keys():
                        pass
                        # QQHandler.send_to_groups(member_weibo_groups, '[CQ:image,file={}]'.format(newWB['video_url']))
                    if 'picUrls' in newWB.keys():
                        # for pic in newWB['picUrls']:
                        # 发一张图就可以了
                        pass
                        # QQHandler.send_to_groups(member_weibo_groups, '[CQ:image,file={}]'.format(newWB['picUrls'][0]))
                    if 'retweeted_status' in newWB.keys():
                        text = '转发微博:\n@{}: {}'.format(newWB['retweeted_status']['user'],
                                                        newWB['retweeted_status']['text'])
                        pass
                        # QQHandler.send_to_groups(member_weibo_groups, text)


@scheduler.scheduled_job('cron', hour='10, 22', minute='17')
def kuan_time_broadcast():
    my_logger.info('款时播报')
    weibo_monitor.kuan_time_broadcast()


weibo_monitor = WeiboMonitor()
update_weibo_conf()

if __name__ == '__main__':
    global_config.MEMBER_WEIBO_GROUPS = ConfigReader.get_property('qq_conf', 'member_weibo_groups').split(';')
    # weibo_monitor.login('*', '*')
    # uid = ConfigReader.get_property('weibo', name)
    from pocket48.pocket48_handler import Pocket48ListenTask, Member
    uid = 1134206783
    task = Pocket48ListenTask(Member('SNH48', 0, 0, 2689280541, 'SNH48'))
    weibo_monitor.getWBQueue(task)
    while True:
        monitor_member_weibo()
        time.sleep(5)
