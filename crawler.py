#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
crawler.py

Bing Image of The Day Crawler
Bing Homepage Images
必应首页背景图爬虫

@Author: MiaoTony
@CreateTime: 20201126
@UpdateTime: 20210109
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
        # images to be pushed and their names
        self.img_push_size_list = ['UHD', '1920x1080', '1080x1920']
        self.img_push_name_list = ['4K+', '1080p', 'Mobile']
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

    def replace_entities(self, string: str):
        """
        replace HTML entities `<`, `>`, `&` 
        """
        return string.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def telegram_push(self):
        """
        Push images to Telegram channel using bot API.
        """
        print('\033[32m[INFO] Pushing to Telegram channel...\033[0m')
        bot_token = str(os.environ.get('BOTTOKEN'))
        channel_id_main = str(os.environ.get('CHANNELIDMAIN'))
        channel_id_archieve = str(os.environ.get('CHANNELIDARCHIEVE'))

        # DEBUG
        # bot_token = ''
        # channel_id_main = '-1001214433840'
        # channel_id_archieve = '-1001373757531'

        api_url_base = f'https://api.telegram.org/bot{bot_token}/'
        api_send_message = api_url_base + 'sendMessage'
        api_send_photo = api_url_base + 'sendPhoto'
        api_send_document = api_url_base + 'sendDocument'

        # push raw images to archieve channel
        print('\033[33m[INFO] TG: Pushing raw images to archieve channel...\033[0m')
        tg_archieve = {}
        for photo_size in self.data['url']:
            print(photo_size)
            photo_url = self.data['url'].get(photo_size)
            if photo_size == 'UHD':
                # TODO: get photo raw size
                raw_size = photo_size
                caption = f'#{photo_size}\n<b>{self.name}_{raw_size}</b>'
            else:
                caption = f'#{photo_size}\n<b>{self.name}_{photo_size}</b>'
            payload = {'chat_id': channel_id_archieve, 'document': photo_url,
                       'caption': caption, 'parse_mode': 'HTML'}
            # print(payload)
            resp = requests.post(api_send_document, data=payload,
                                 timeout=self.timeout)
            resp.encoding = 'utf-8'
            print(resp.json())
            result = resp.json().get('result')
            message_id = result.get('message_id')
            file_id = result.get('document').get('file_id')
            tg_archieve[photo_size] = {
                'message_id': message_id, 'file_id': file_id}
            print('----------')
        print('\033[33m=============\033[0m')
        print()

        # push copyright and description
        print('\033[33m[INFO] TG: Pushing copyright and description...\033[0m')
        text = '<b>' + self.replace_entities(self.data['copyright']) + \
            '</b>\n\n' + self.replace_entities(self.data['desc'])
        payload = {'chat_id': channel_id_archieve,
                   'text': text, 'parse_mode': 'HTML'}
        # print(payload)
        resp = requests.post(api_send_message, data=payload,
                             timeout=self.timeout)
        resp.encoding = 'utf-8'
        print(resp.json())
        result = resp.json().get('result')
        tg_story_message_id = result.get('message_id')
        print('\033[33m=============\033[0m')
        print()

        # push image to main channel with links of the archieve channel
        print('\033[33m[INFO] TG: Pushing the image to main channel...\033[0m')
        if self.data['url'].get('UHD'):
            photo = self.data['url'].get('UHD')
        else:
            photo = self.data['url'].get('1920x1080')
        caption = '<b>' + \
            self.replace_entities(self.data['copyright']) + '</b>\n' + \
            f'<a href="https://t.me/BingImageArchive/{str(tg_story_message_id)}">Story</a>'

        for i, v in enumerate(self.img_push_size_list):
            if v in tg_archieve.keys():
                message_id = tg_archieve[v].get('message_id')
                display_name = self.img_push_name_list[i]
                caption += ' | '
                caption += f'<a href="https://t.me/BingImageArchive/{str(message_id)}">{display_name}</a>'
        payload = {'chat_id': channel_id_main, 'photo': photo, 'caption': caption,
                   'parse_mode': 'HTML', 'disable_web_page_preview': True}
        print(payload)
        resp = requests.post(api_send_photo, data=payload,
                             timeout=self.timeout)
        resp.encoding = 'utf-8'
        print(resp.json())
        result = resp.json().get('result')
        tg_photo = result.get('photo')
        print('\033[33m=============\033[0m')
        print()
        self.data['telegram'] = {'archieve': tg_archieve, 'photo': tg_photo}

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
        print()
        self.parse_info()
        print()
        self.download_img()
        print()
        self.telegram_push()
        print(self.data)
        print()
        self.save_data()
        print()
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
