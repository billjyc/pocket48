#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author    : 奶权
# Action    : 微博监控
# Desc      : 微博监控主模块

import json
import requests
import time
from utils import util
from log.my_logger import weibo_logger as my_logger


class WeiboListenTask:
    def __init__(self, weibo_uid):
        self.weibo_uid = weibo_uid
        self.weibo_info = ''
        self.itemIds = []  # WB Queue


class WeiboMonitor:
    def __init__(self, ):
        self.session = requests.session()
        self.reqHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://passport.weibo.cn/signin/login',
            'Connection': 'close',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }

    def login(self, userName, passWord):
        """
        登录微博
        :param userName:
        :param passWord:
        :return:
        """
        loginApi = 'https://passport.weibo.cn/sso/login'
        loginPostData = {
            'username': userName,
            'password': passWord,
            'savestate': 1,
            'r': '',
            'ec': '0',
            'pagerefer': '',
            'entry': 'mweibo',
            'wentry': '',
            'loginfrom': '',
            'client_id': '',
            'code': '',
            'qq': '',
            'mainpageflag': 1,
            'hff': '',
            'hfp': ''
        }
        # get user session
        try:
            r = self.session.post(loginApi, data=loginPostData, headers=self.reqHeaders)
            if r.status_code == 200 and json.loads(r.text)['retcode'] == 20000000:
                self.echoMsg('Info', 'weibo Login successful! UserId:' + json.loads(r.text)['data']['uid'])
            else:
                self.echoMsg('Error', 'weibo Login failure!')
                # sys.exit()
        except Exception as e:
            self.echoMsg('Error', e)
            # sys.exit()

    def getWBQueue(self, task):
        """
        拿到用户的微博队列
        :param task:
        :return:
        """
        # get user weibo containerid
        user_info = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s' % (
        task.member.weibo_uid, task.member.weibo_uid)
        try:
            r = self.session.get(user_info, headers=self.reqHeaders)
            for i in r.json()['data']['tabsInfo']['tabs']:
                if i['tab_type'] == 'weibo':
                    con_id = i['containerid']
                    # TODO: 拿不到con_id
        except Exception as e:
            self.echoMsg('Error', e)
            print(e)
            # sys.exit()

        # get user weibo index
        task.weibo_info = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s&containerid=%s' % (
            task.member.weibo_uid, task.member.weibo_uid, con_id)
        try:
            r = self.session.get(task.weibo_info, headers=self.reqHeaders)
            task.itemIds = []  # WBQueue
            for i in r.json()['data']['cards']:
                if i['card_type'] == 9:
                    task.itemIds.append(i['mblog']['id'])
            self.echoMsg('Info', 'Got weibos')
            self.echoMsg('Info', 'Has %d weibo id(s)' % len(task.itemIds))
        except Exception as e:
            self.echoMsg('Error', e)
            print(e)
            # sys.exit()

    def startMonitor(self, task):
        """
        开始监控
        :param task:
        :return:
        """
        my_logger.debug('weibo handler: start monitor')
        return_dict = {}
        try:
            r = self.session.get(task.weibo_info, headers=self.reqHeaders)
            for i in r.json()['data']['cards']:
                # print i
                if i['card_type'] == 9:
                    if str(i['mblog']['id']) not in task.itemIds:
                        task.itemIds.append(i['mblog']['id'])
                        self.echoMsg('Info', 'Got a new weibo')
                        # @ return returnDict dict
                        return_dict['created_at'] = i['mblog']['created_at']
                        return_dict['text'] = util.filter_tags(i['mblog']['text'])
                        return_dict['source'] = i['mblog']['source']
                        return_dict['nickName'] = i['mblog']['user']['screen_name']
                        return_dict['scheme'] = i['scheme']
                        my_logger.debug(i['mblog']['text'])
                        # if has photos
                        if 'pics' in i['mblog']:
                            return_dict['picUrls'] = []
                            for j in i['mblog']['pics']:
                                return_dict['picUrls'].append(j['url'])
                                my_logger.debug(j['url'])

                        return return_dict
            my_logger.info('微博队列共有 %d 条' % len(task.itemIds))
            # self.echoMsg('Info', '微博队列共有 %d 条' % len(self.itemIds))
        except Exception as e:
            my_logger.error(e)
            # print(e)
            # sys.exit()

    """
        @   String level   : Info/Error
        @   String msg     : The message you want to show
    """

    def echoMsg(self, level, msg):
        if level == 'Info':
            my_logger.info(msg)
        elif level == 'Error':
            my_logger.debug(msg)


if __name__ == '__main__':
    # handler = WeiboMonitor()
    # handler.login('***', '****')
    # uid = ConfigReader.get_property('weibo', 'fengxiaofei')
    # uid = 1134206783
    # handler.getWBQueue(uid)
    # while 1:
    #     newWB = handler.startMonitor()
    #     if newWB is not None:
    #         print(newWB['text'])
    #     time.sleep(3)
    pass
