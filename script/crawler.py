#!/usr/bin/env python3
# -*- coding:utf-8 -*-
"""
crawler.py

Bing Image of The Day Crawler
Bing Homepage Images
必应首页背景图爬虫

@Author: MiaoTony
@CreateTime: 20201126
@UpdateTime: 20210118
"""

import os
import requests
import json
import time
import random
import datetime
import argparse
from PIL import Image
from io import BytesIO


class Crawler(object):
    """
    爬虫类
    """

    def __init__(self):
        self.host = r"https://www.bing.com"
        self.json_url = self.host + \
            r"/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=ZH-CN&pid=hp"
        self.json_en_url = self.host + \
            r"/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=ZH-CN&pid=hp&ensearch=1"
        self.json_en_au_url = self.host + \
            r"/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=EN-AU&pid=hp&ensearch=1"
        self.json_en_in_url = self.host + \
            r"/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=EN-IN&pid=hp&ensearch=1"
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
        self.img_push_name_list = ['UHD', '1080p', 'Mobile']
        self.data = {}

    def get_json(self, url: str):
        """
        Get the data with JSON format from the Bing API.
        :param url: {str} URL
        :return: JSON data
        """
        print(f'\033[32m[INFO] Getting JSON data... URL: {url}\033[0m')
        retry_cnt = 4
        while retry_cnt > 0:
            try:
                resp = requests.get(
                    url, headers=self.headers, timeout=self.timeout)
                resp.encoding = 'utf-8'
                data = resp.json()
                print(data)
                if data:
                    return data
            except Exception as e:
                print('\033[31m[ERROR]', e,
                      '\033[33mRetrying get_json:', retry_cnt, '\033[0m')
            retry_cnt -= 1
            time.sleep(random.uniform(0.5, 1))

    def get_info_cn(self):
        """
        Get and parse the JSON data in Chinese.
        """
        print('\033[32m[INFO] Getting and parsing info in Chinese...\033[0m')
        data_raw = self.get_json(self.json_url)
        image = data_raw.get('images')[0]
        # url = image.get('url')
        urlbase = image.get('urlbase')
        copyright_cn = image.get('copyright')
        copyrightlink = image.get('copyrightlink')
        name = urlbase.split('=')[1]
        print(urlbase, copyright_cn)
        self.name = name
        self.urlbase = self.host + urlbase
        self.data['name'] = name
        self.data['urlbase'] = urlbase
        self.data['copyright_cn'] = copyright_cn
        self.data['copyrightlink'] = copyrightlink

    def get_info_en(self):
        """
        Get the copyright and description info in English.
        """
        print('\033[32m[INFO] Getting and parsing info in English...\033[0m')
        data_raw = self.get_json(self.json_en_url)
        # TODO: 截取文件名进行比较
        image = data_raw.get('images')[0]
        desc = image.get('desc', '')
        copyright_en = image.get('copyright')
        print(copyright_en)
        print()
        self.data['desc'] = desc
        self.data['copyright'] = copyright_en
        print(self.data)

    def download_img(self):
        """
        Download the images to local, and return their urls.
        return: {list} url dict 
        """
        print('\033[32m[INFO] Downloading images...\033[0m')
        if not os.path.exists(f"../img/{self.date}/"):
            os.mkdir(f"../img/{self.date}/")

        data_url = {}
        for img_size in self.img_size_list:
            print(img_size)
            retry_cnt = 4
            while retry_cnt > 0:
                try:
                    url = self.urlbase + '_' + img_size + '.jpg'
                    resp = requests.get(
                        url, headers=self.headers, timeout=self.timeout)
                    if resp.status_code == 404:
                        # If not exist, pass.
                        break
                    if 200 <= resp.status_code < 300:
                        img_raw = resp.content
                        with open(f'../img/{self.date}/{self.name}_{img_size}.jpg', 'wb') as f:
                            f.write(img_raw)
                        data_url[img_size] = url

                        if img_size == 'UHD':
                            # get image raw size
                            img = Image.open(BytesIO(img_raw))
                            raw_size = f'{img.width}x{img.height}'
                            print(raw_size)
                            self.img_raw_size = raw_size
                            self.data['raw_size'] = raw_size
                            # Save the latest image to `UHD.jpg`
                            with open(f'../img/latest/UHD.jpg', 'wb') as f:
                                f.write(img_raw)

                        if img_size == '1920x1080':
                            # Save the latest image to `1080p.jpg`
                            with open(f'../img/latest/1080p.jpg', 'wb') as f:
                                f.write(img_raw)
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
        bot_token = os.environ.get('BOTTOKEN')
        channel_id_main = os.environ.get('CHANNELIDMAIN')
        channel_id_archive = os.environ.get('CHANNELIDARCHIVE')

        if not bot_token:
            from secret import bot_token, channel_id_main, channel_id_archive

        api_url_base = f'https://api.telegram.org/bot{bot_token}/'
        api_send_message = api_url_base + 'sendMessage'
        api_send_photo = api_url_base + 'sendPhoto'
        api_send_document = api_url_base + 'sendDocument'

        # push raw images to archive channel
        print('\033[33m[INFO] TG: Pushing raw images to archive channel...\033[0m')
        tg_archive = {}
        for photo_size in self.data['url']:
            print(photo_size)
            photo_url = self.data['url'].get(photo_size)
            if photo_size == 'UHD':
                caption = f'#{photo_size}\n{self.date}\n<b>{self.name}_{self.img_raw_size}</b>'
            else:
                caption = f'#{photo_size}\n{self.date}\n<b>{self.name}_{photo_size}</b>'
            payload = {'chat_id': channel_id_archive, 'document': photo_url,
                       'caption': caption, 'parse_mode': 'HTML'}
            # print(payload)
            resp = requests.post(api_send_document, data=payload,
                                 timeout=self.timeout)
            resp.encoding = 'utf-8'
            print(resp.json())
            result = resp.json().get('result')
            message_id = result.get('message_id')
            file_id = result.get('document').get('file_id')
            tg_archive[photo_size] = {
                'message_id': message_id, 'file_id': file_id}
            print('----------')
        print('\033[33m=============\033[0m')
        print()

        # push copyright and description
        print('\033[33m[INFO] TG: Pushing copyright and description...\033[0m')
        text = self.date + '\n<b>' + self.replace_entities(self.data['copyright']) + \
            '\n' + self.replace_entities(self.data['copyright_cn']) + \
            '</b>\n\n' + self.replace_entities(self.data['desc'])
        payload = {'chat_id': channel_id_archive,
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

        # push image to main channel with links of the archive channel
        print('\033[33m[INFO] TG: Pushing the image to main channel...\033[0m')
        if self.data['url'].get('UHD'):
            photo = self.data['url'].get('UHD')
        else:
            photo = self.data['url'].get('1920x1080')
        caption = '<b>' + self.replace_entities(self.data['copyright']) + '\n' + \
            self.replace_entities(self.data['copyright_cn']) + '</b>\n' + \
            f'<a href="https://t.me/BingImageArchive/{str(tg_story_message_id)}">Story</a>'

        for i, v in enumerate(self.img_push_size_list):
            if v in tg_archive.keys():
                message_id = tg_archive[v].get('message_id')
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
        self.data['telegram'] = {'archive': tg_archive, 'photo': tg_photo}

    def save_data(self):
        """
        Save all data to local.
        """
        print('\033[32m[INFO] Saving data...\033[0m')
        with open(f'../data/{self.date}.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False,
                      indent=2,  separators=(',', ': '))
        with open(f'../data/latest.json', 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False,
                      indent=2,  separators=(',', ': '))

    def run(self):
        """
        run job
        """
        print("\033[32m[INFO] Job start! \033[0m")
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")
        time_start = time.time()
        self.get_info_cn()
        print()
        self.get_info_en()
        print()
        self.download_img()
        print()
        self.telegram_push()
        print(self.data)
        print()
        self.save_data()
        print()
        print("\033[32m[INFO] Job finish! \033[0m")
        print(time.time()-time_start)

    def wait_for_run(self):
        """
        run at a specific time
        """
        print("\033[32m[INFO] Waiting for the specific execution time... \033[0m")
        time_d = datetime.datetime.now()
        hour = int(time_d.strftime("%H"))
        if hour > 20:
            time_d = time_d + datetime.timedelta(days=1)
        # Run at 00:00:30
        time_set = datetime.datetime.strptime(
            str(time_d.date()) + '00:00:30', '%Y-%m-%d%H:%M:%S')
        print('Set time:', time_set)
        while True:
            time_now = datetime.datetime.now()
            print(time_now)
            if time_now >= time_set:
                break
            time.sleep(30)
        self.run()


if __name__ == "__main__":
    if not os.path.exists("../data/"):
        os.mkdir("../data/")
    if not os.path.exists("../img/"):
        os.mkdir("../img/")
    if not os.path.exists("../img/latest/"):
        os.mkdir("../img/latest/")

    # Parse args
    parser = argparse.ArgumentParser()
    parser.description = "Bing Image of The Day Crawler"
    parser.add_argument(
        "-w", "--wait", help="Wait until the specific time to run.", action="store_true")
    args = parser.parse_args()

    crawler = Crawler()
    time_now = datetime.datetime.now()
    print("\033[32m[INFO] time_now: ", time_now, '\033[0m')
    if args.wait:
        crawler.wait_for_run()
    else:
        crawler.run()
