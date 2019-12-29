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
from bs4 import BeautifulSoup


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
                        return_dict['text'] = self.handle_weibo_text(i['mblog']['text'])
                        return_dict['source'] = i['mblog']['source']
                        return_dict['nickName'] = i['mblog']['user']['screen_name']
                        return_dict['scheme'] = i['scheme']
                        return_dict['pics'] = i['pics']
                        my_logger.debug(i['mblog']['text'])
                        # if has photos
                        if 'pics' in i['mblog']:
                            return_dict['picUrls'] = []
                            for j in i['mblog']['pics']:
                                return_dict['picUrls'].append(j['url'])
                                my_logger.debug(j['url'])
                        # 如果有视频
                        if 'page_info' in i['mblog']:
                            page_info = i['mblog']
                            if page_info['type'] == 'video':
                                return_dict['video_url'] = page_info['media_info']['h5_url']
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

    def handle_weibo_text(self, weibo_text):
        """
        处理微博文字，去除html标签
        :param weibo_text:
        :return:
        """
        soup = BeautifulSoup(weibo_text.replace('<br />', '\n').replace('<br/>', '\n'), 'lxml')
        return soup.text


if __name__ == '__main__':
    weibo_text = """<a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23SNH48%E5%B9%B4%E5%BA%A6%E9%87%91%E6%9B%B2%E5%A4%A7%E8%B5%8F%23&luicode=10000011&lfid=1076032689280541" data-hide=""><span class="surl-text">#SNH48年度金曲大赏#</span></a> 精彩回顾<br /><a  href="https://m.weibo.cn/p/index?containerid=1008086bd7cfe0bc1b396eede72d35bf433f4f&extparam=SNH48&luicode=10000011&lfid=1076032689280541" data-hide=""><span class='url-icon'><img style='width: 1rem;height: 1rem' src='http://n.sinaimg.cn/photo/5213b46e/20181127/timeline_card_small_super_default.png'></span><span class="surl-text">SNH48超话</span></a>《Who I Am》<br /><a href='/n/SNH48-莫寒'>@SNH48-莫寒</a> <a href='/n/SNH48-戴萌'>@SNH48-戴萌</a>  <br />现场的证据是我故意<br />特别为你而设下的局<br /><a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E6%88%91%E7%9A%84%E5%B9%B4%E5%BA%A6%E9%87%91%E6%9B%B2%23&isnewpage=1&luicode=10000011&lfid=1076032689280541" data-hide=""><span class="surl-text">#我的年度金曲#</span></a><a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23%E6%97%A9%E5%AE%89SNH48%23&luicode=10000011&lfid=1076032689280541" data-hide=""><span class="surl-text">#早安SNH48#</span></a> <br /><a data-url="http://t.cn/AiFXwfzI" href="https://m.weibo.cn/p/index?containerid=2304444454806354591746&url_type=39&object_type=video&pos=1&luicode=10000011&lfid=1076032689280541" data-hide=""><span class='url-icon'><img style='width: 1rem;height: 1rem' src='https://h5.sinaimg.cn/upload/2015/09/25/3/timeline_card_small_video_default.png'></span><span class="surl-text">SNH48的微博视频</span></a> """
    ret = weibo_text.find('<br />')
    handler = WeiboMonitor()
    handler.handle_weibo_text(weibo_text)
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
