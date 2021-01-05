#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
crawler.py

Bing Image of The Day Crawler
Bing Homepage Images
必应首页背景图爬虫

@Author: MiaoTony
@CreateTime: 20201126
@UpdateTime: 20210105
"""

import os
import requests
import json
import time
import random
import datetime


class Crawler(object):
    """
    爬虫类
    """

    def __init__(self):
        self.host = r"https://www.bing.com"
        self.json_url = self.host + \
            r"/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US&pid=hp&ensearch=1"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36",
            "Accept": "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
        }
        self.timeout = 12  # seconds
        self.img_size_list = ['UHD', '1920x1080', '1024x768', '1366x768', '800x480',
                              # Mobile
                              '1080x1920', '480x800']
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.data = {}

    def get_json(self):
        """
        Get the data with JSON format from the Bing API.
        :return: JSON data
        """
        print('\033[32m[INFO] Getting JSON data...\033[0m')
        retry_cnt = 4
        while retry_cnt > 0:
            try:
                resp = requests.get(
                    self.json_url, headers=self.headers, timeout=self.timeout)
                resp.encoding = 'utf-8'
                data = resp.json()
                print(data)
                if data:
                    self.data_raw = data
                    break
            except Exception as e:
                print('\033[31m[ERROR]', e,
                      '\033[33mRetrying get_json:', retry_cnt, '\033[0m')
            retry_cnt -= 1
            time.sleep(random.uniform(0.5, 1))

    def parse_info(self):
        """
        Parse the JSON data.
        """
        print('\033[32m[INFO] Parsing JSON data...\033[0m')
        image = self.data_raw.get('images')[0]
        url = image.get('url')
        urlbase = image.get('urlbase')
        desc = image.get('desc', '')
        copyright = image.get('copyright')
        copyrightlink = image.get('copyrightlink')
        name = urlbase.split('=')[1]
        print(urlbase, copyright)
        print()
        self.name = name
        self.urlbase = self.host + urlbase

        self.data['name'] = name
        self.data['urlbase'] = urlbase
        self.data['desc'] = desc
        self.data['copyright'] = copyright
        self.data['copyrightlink'] = copyrightlink
        print(self.data)
        print()

    def download_img(self):
        """
        Download the images to local, and return their urls.
        return: {list} url dict 
        """
        print('\033[32m[INFO] Downloading images...\033[0m')
        if not os.path.exists(f"./img/{self.date}/"):
            os.mkdir(f"./img/{self.date}/")

        data_url = {}
        for img_size in self.img_size_list:
            print(img_size)
            retry_cnt = 4
            while retry_cnt > 0:
                try:
                    url = self.urlbase + '_' + img_size + '.jpg'
                    img_raw = requests.get(
                        url, headers=self.headers, timeout=self.timeout).content
                    with open(f'img/{self.date}/{self.name}_{img_size}.jpg', 'wb') as f:
                        f.write(img_raw)
                    data_url[img_size] = url
                    break
                except Exception as e:
                    print('\033[31m[ERROR]', e,
                          '\033[33mRetrying download_img:',  img_size, retry_cnt, '\033[0m')
                    retry_cnt -= 1
                    time.sleep(random.uniform(0.5, 1))
            print('=========================')
        self.data['url'] = data_url
        return data_url

    def telegram_push(self):
        """
        Push to Telegram channel using bot API.
        """
        print('\033[32m[INFO] Pushing to Telegram channel...\033[0m')
        bot_token = str(os.environ.get('BOTTOKEN'))
        channel_id = str(os.environ.get('CHANNELID'))
        print(bot_token[:3], channel_id[:3])  # debug
        # TODO return file ID.
        self.data['telegram'] = []
        return []

    def save_data(self):
        """
        Save all data to local.
        """
        print('\033[32m[INFO] Saving data...\033[0m')
        with open(f'data/{self.date}.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False,
                      indent=2,  separators=(',', ': '))

    def run(self):
        """
        run job
        """
        print("\033[32m[INFO] Job start! \033[0m")
        self.get_json()
        self.parse_info()
        self.download_img()
        self.telegram_push()
        print(self.data)
        self.save_data()
        print("\033[32m[INFO] Job finish! \033[0m")


if __name__ == "__main__":
    if not os.path.exists("./data/"):
        os.mkdir("./data/")
    if not os.path.exists("./img/"):
        os.mkdir("./img/")
    crawler = Crawler()
    time_start = time.time()
    time_now = datetime.datetime.now()
    print("\033[32m[INFO] time_now: ", time_now, '\033[0m')
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    crawler.run()
    print(time.time()-time_start)
