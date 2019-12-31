#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author    : 奶权
# Action    : 微博监控
# Desc      : 微博监控主模块

import json
import requests
import logging

try:
    from log.my_logger import weibo_logger as my_logger
except Exception as e:
    my_logger = logging.getLogger(__name__)
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
                    whole_weibo_text = self.get_whole_weibo_content(i['mblog']['id'])
                    my_logger.debug('微博内容: {}'.format(
                        self.handle_weibo_text(whole_weibo_text)))
                    if 'pics' in i['mblog'].keys():
                        my_logger.debug('有图片')
                        for j in i['mblog']['pics']:
                            if 'large' in j.keys():
                                my_logger.debug('使用大图')
                                my_logger.debug(j['large']['url'])
                            else:
                                my_logger.debug(j['url'])
                    # 如果有视频
                    if 'page_info' in i['mblog'].keys():
                        page_info = i['mblog']['page_info']
                        if page_info['type'] == 'video':
                            my_logger.debug('有视频')
                            my_logger.debug('视频截图: {}'.format(page_info['page_pic']['url']))
                    # 如果是转发
                    if 'retweeted_status' in i['mblog'].keys():
                        retweeted_status = i['mblog']['retweeted_status']
                        retweeted_user = retweeted_status['user']
                        my_logger.debug(
                            '被转发人, id: {}, 微博名: {}'.format(retweeted_user['id'], retweeted_user['screen_name']))
                        my_logger.debug('转发微博内容: {}'.format(
                            self.handle_weibo_text(self.get_whole_weibo_content(retweeted_status['id']))))
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
                        whole_weibo_text = self.get_whole_weibo_content(i['mblog']['id'])
                        return_dict['text'] = self.handle_weibo_text(whole_weibo_text)
                        return_dict['source'] = i['mblog']['source']
                        return_dict['nickName'] = i['mblog']['user']['screen_name']
                        return_dict['scheme'] = i['scheme']
                        # return_dict['pics'] = i['pics']
                        my_logger.debug(i['mblog']['text'])
                        # if has photos
                        if 'pics' in i['mblog'].keys():
                            my_logger.debug('有图片')
                            return_dict['picUrls'] = []
                            for j in i['mblog']['pics']:
                                if 'large' in j.keys():
                                    my_logger.debug('使用大图')
                                    my_logger.debug(j['large']['url'])
                                    return_dict['picUrls'].append(j['large']['url'])
                                else:
                                    return_dict['picUrls'].append(j['url'])
                                    my_logger.debug(j['url'])
                        # 如果有视频
                        if 'page_info' in i['mblog'].keys():
                            my_logger.debug('有视频')
                            page_info = i['mblog']['page_info']
                            if page_info['type'] == 'video':
                                my_logger.debug('视频截图: {}'.format(page_info['page_pic']['url']))
                                return_dict['video_url'] = page_info['page_pic']['url']
                        # 如果是转发
                        if 'retweeted_status' in i['mblog'].keys():
                            return_dict['retweeted_status'] = {}
                            retweeted_status = i['mblog']['retweeted_status']
                            retweeted_user = retweeted_status['user']
                            my_logger.debug('被转发人, id: {}, 微博名: {}'.format(retweeted_user['id'],
                                                                           retweeted_user['screen_name']))
                            retweeted_text = self.handle_weibo_text(self.get_whole_weibo_content(retweeted_status['id']))
                            my_logger.debug('转发微博内容: {}'.format(retweeted_text))
                            return_dict['retweeted_status']['user'] = retweeted_user
                            return_dict['retweeted_status']['text'] = retweeted_text
                        return return_dict
            my_logger.info('微博队列共有 %d 条' % len(task.itemIds))
            # self.echoMsg('Info', '微博队列共有 %d 条' % len(self.itemIds))
        except Exception as e:
            my_logger.exception(e)
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
        weibo_text = '<div>' + weibo_text + '</div>'
        soup = BeautifulSoup(weibo_text.replace('<br />', '\n').replace('<br/>', '\n'), 'lxml')
        return soup.text

    def get_whole_weibo_content(self, weibo_id):
        """
        获取微博全文
        :param weibo_id:
        :return:
        """
        url = "https://m.weibo.cn/statuses/extend?id={}".format(weibo_id)
        try:
            r = self.session.get(url, headers=self.reqHeaders).json()
            if r['ok'] == 1:
                return r['data']['longTextContent']
        except Exception as e:
            my_logger.exception(e)
            return None


if __name__ == '__main__':
    weibo_text = """第六届<a  href="https://m.weibo.cn/search?containerid=231522type%3D1%26t%3D10%26q%3D%23SNH48%E5%B9%B4%E5%BA%A6%E9%87%91%E6%9B%B2%E5%A4%A7%E8%B5%8F%23" data-hide=""><span class="surl-text">#SNH48年度金曲大赏#</span></a> <br />Live音源（下）咪咕首发🎧<a data-url="http://t.cn/AiFUXBEG" href="http://c.migu.cn/003Jyu?ifrom=c8a1221dbcd2d3c4eeda2da0526d9b9e" data-hide=""><span class='url-icon'><img style='width: 1rem;height: 1rem' src='https://h5.sinaimg.cn/upload/2015/09/25/3/timeline_card_small_web_default.png'></span><span class="surl-text">网页链接</span></a> <br /><br />由最受年轻群体喜爱的哈尔滨啤酒冠名赞助呈现，独家战略音乐合作平台及独家互联网直播平台咪咕音乐全程支持的<a  href="https://m.weibo.cn/p/index?extparam=SNH48&containerid=1008086bd7cfe0bc1b396eede72d35bf433f4f" data-hide=""><span class='url-icon'><img style='width: 1rem;height: 1rem' src='https://n.sinaimg.cn/photo/5213b46e/20180926/timeline_card_small_super_default.png'></span><span class="surl-text">SNH48</span></a> GROUP第六届年度金曲大赏BEST50 REQUEST TIME歌曲总决选演唱会在广州体育馆圆满落幕，来自SNH48、<a href='/n/BEJ48'>@BEJ48</a>、<a href='/n/GNZ48'>@GNZ48</a> 三团成员共同献唱，为观众们呈现了一场精彩绝伦的音乐视听盛宴。年度队歌、年度荣耀队歌、炽曈组6首入围人气金曲及歌曲《浪漫圣诞夜》。SNH48 Team NII陆婷和冯薪朵《Hold Me Tight》荣获本届金曲大赏年度金曲；SNH48 Team NII《花之祭》荣膺本届年度荣耀队歌。帅气动感、活泼动人，精彩不断！"""
    # ret = weibo_text.find('<br />')
    handler = WeiboMonitor()
    print(handler.handle_weibo_text(weibo_text))
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
