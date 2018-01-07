# coding=utf-8
import threading
import requests
import time
import urllib
from asyncio import Queue
import os

from log.my_logger import logger as my_logger


class Download(threading.Thread):
    def __init__(self, que):
        threading.Thread.__init__(self)
        self.queue = que

    def Schedule(self, a, b, c):
        """
        :param a: 已经下载的数据块
        :param b: 数据块的大小
        :param c: 远程文件的大小
        :return:
        """
        per = 100.0 * a * b / c
        if per > 100:
            per = 100
        print('%.2f%%' % per)

    def run(self):
        while True:
            if not self.queue.empty():
                # DEBUG(self.name)
                # print self.name
                name = self.queue.get()
                live_url = self.queue.get()
                ext = live_url.split('.')[-1]
                file_name = name + '.' + ext
                my_logger.info('%s直播下载开始...', file_name)
                r = requests.get(live_url, verify=False)
                local_path = os.path.join('../', file_name)
                with open(local_path, 'wb') as code:
                    code.write(r.content)
                # urllib.urlretrieve(url, local_path, self.Schedule)
                my_logger.info('下载完成')
            else:
                my_logger.info('直播下载队列为空！')
            time.sleep(60)


if __name__ == '__main__':

    queue = Queue.Queue(20)

    d = Download(queue)
    d.setDaemon(True)
    d.start()

    url = 'https://mp4.48.cn/live/bbf8a902-2e5d-4fa1-9c09-5151145f7c90.mp4'
    url2 = 'http://2519.liveplay.myqcloud.com/live/2519_2996320.flv'
    url3 = 'http://www.sina.com.cn'
    d.setName('liuzengyan')
    queue.put(url)
    # queue.put(url2)
    # queue.put(url3)

    while True:
        print('main thread')
        time.sleep(30)
    # while True:
    #     print 'main thread'
    #     time.sleep(3)
