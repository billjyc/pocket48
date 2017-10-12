#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author    : 奶权
# Action    : 微博监控
# Desc      : 微博监控主模块

import requests, json, sys
from lxml import etree

from config_reader import ConfigReader
from qqbot.utf8logger import DEBUG, INFO, ERROR
import time


class WeiboMonitor:
    """
        @   Class self  :
    """

    def __init__(self, ):
        self.session = requests.session()
        self.reqHeaders = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://passport.weibo.cn/signin/login',
            'Connection': 'close',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3'
        }

    """
        @   Class self  :
        @   String userName  : The username of weibo.cn
        @   String passWord  : The password of weibo.cn
    """

    def login(self, userName, passWord):
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
                self.echoMsg('Info', 'Login successful! UserId:' + json.loads(r.text)['data']['uid'])
            else:
                self.echoMsg('Error', 'Logon failure!')
                # sys.exit()
        except Exception as e:
            self.echoMsg('Error', e)
            # sys.exit()

    """
        @   Class self  :
        @   String wbUserId  : The user you want to monitored
    """

    def getWBQueue(self, wbUserId):
        # get user weibo containerid
        userInfo = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s' % (wbUserId, wbUserId)
        try:
            r = self.session.get(userInfo, headers=self.reqHeaders)
            for i in r.json()['tabsInfo']['tabs']:
                if i['tab_type'] == 'weibo':
                    conId = i['containerid']
        except Exception as e:
            self.echoMsg('Error', e)
            sys.exit()
        # get user weibo index
        self.weiboInfo = 'https://m.weibo.cn/api/container/getIndex?uid=%s&type=uid&value=%s&containerid=%s' % (
        wbUserId, wbUserId, conId)
        try:
            r = self.session.get(self.weiboInfo, headers=self.reqHeaders)
            self.itemIds = []  # WBQueue
            for i in r.json()['cards']:
                if i['card_type'] == 9:
                    self.itemIds.append(i['mblog']['id'])
            self.echoMsg('Info', 'Got weibos')
            self.echoMsg('Info', 'Has %d id(s)' % len(self.itemIds))
        except Exception as e:
            self.echoMsg('Error', e)
            # sys.exit()

    """
        @   Class self  :
    """

    def startMonitor(self, ):
        returnDict = {}
        try:
            r = self.session.get(self.weiboInfo, headers=self.reqHeaders)
            for i in r.json()['cards']:
                # print i
                if i['card_type'] == 9:
                    if str(i['mblog']['id']) not in self.itemIds:
                        self.itemIds.append(i['mblog']['id'])
                        self.echoMsg('Info', 'Got a new weibo')
                        # @ return returnDict dict
                        returnDict['created_at'] = i['mblog']['created_at']
                        returnDict['text'] = i['mblog']['text']
                        returnDict['source'] = i['mblog']['source']
                        returnDict['nickName'] = i['mblog']['user']['screen_name']
                        DEBUG(i['mblog']['text'])
                        # if has photos
                        if i['mblog'].has_key('pics'):
                            returnDict['picUrls'] = []
                            for j in i['mblog']['pics']:
                                returnDict['picUrls'].append(j['url'])
                                DEBUG(j['url'])
                        return returnDict
            self.echoMsg('Info', '微博队列共有 %d 条' % len(self.itemIds))
        except Exception as e:
            self.echoMsg('Error', e)
            # sys.exit()

    """
        @   String level   : Info/Error
        @   String msg     : The message you want to show
    """

    def echoMsg(self, level, msg):
        if level == 'Info':
            INFO(msg)
        elif level == 'Error':
            DEBUG(msg)


if __name__ == '__main__':
    handler = WeiboMonitor()
    handler.login('hacker4043', 'jiaYICONG123')
    # uid = ConfigReader.get_property('weibo', 'fengxiaofei')
    uid = 1134206783
    handler.getWBQueue(uid)
    while 1:
        newWB = handler.startMonitor()
        if newWB is not None:
            print newWB
        time.sleep(3)
