# -*- coding: UTF-8 -*-
import platform
import argparse
import csv
import time
from enum import Enum
from io import BytesIO
import sys
import os
import logging
import re

import requests
import pdfkit
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    UnexpectedAlertPresentException
)
from selenium.common.exceptions import TimeoutException
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_URL = 'http://www.tjmg.jus.br/portal-tjmg/'
URL_POST_CAPTCHA = 'http://2captcha.com/in.php'
URL_GET_CAPTCHA = 'http://2captcha.com/res.php'
KEY = 'c3b78102059c7d2009ea1591019068c6'
COUNT_NUMBERS = 0
CURRENT_NUMBERS = 0
logging.basicConfig(
    filename='scanning.log',
    filemode='w',
    format='%(name)s - %(levelname)s - %(message)s'
)

if platform.system() == "Windows":
    CHROME_DRIVER_PATH = os.path.join(BASE_DIR, "chrome", "windows", "chromedriver.exe")
elif platform.system() == "Linux":
    CHROME_DRIVER_PATH = os.path.join(BASE_DIR, "chrome", "linux", "chromedriver")
else:
    CHROME_DRIVER_PATH = os.path.join(BASE_DIR, "chrome", "mac", "chromedriver")


class TjmgAutomation(object):
    def __init__(self, download_folder, headless=False):
        self.headless = headless
        self.driver = self.session()
        self.download_folder = download_folder
        self.enable_download_in_headless_chrome()

    def enable_download_in_headless_chrome(self):
        # add missing support for chrome "send_command"  to selenium webdriver
        self.driver.command_executor._commands["send_command"] = ("POST", '/session/$sessionId/chromium/send_command')

        params = {'cmd': 'Page.setDownloadBehavior', 'params': {'behavior': 'allow', 'downloadPath': self.download_folder}}
        command_result = self.driver.execute("send_command", params)

    def session(self):
        chrome_options = webdriver.ChromeOptions()
        if self.headless is True:
            chrome_options.add_argument('-headless')
        # PROXY = "142.93.87.88:3128"
        # chrome_options.add_argument('--proxy-server=%s' % PROXY)
        self.driver = webdriver.Chrome(CHROME_DRIVER_PATH, chrome_options=chrome_options)

        self.driver.set_page_load_timeout(50)
        self.driver.set_window_size(1360, 900)

        return self.driver

    def rename(self, file_name, number, word):
        os.rename(self.download_folder + '/' + file_name,
                  self.download_folder + '/' + number + '_' + word + '.pdf')

    def search_process(self, number, search_word=None, work_folder='./'):
        try:
            self.driver.get(BASE_URL)
        except TimeoutException:
            logging.warning(
                    '{} - Timeout in loading website'.format(
                        number
                    )
                )
            return None

        try:
            self.driver.find_elements_by_xpath("//section[@class='tabs-of-process']"
                                               "//input[@id='txtProcesso']")[0].send_keys(number)
            self.driver.find_elements_by_xpath("//section[@class='tabs-of-process']"
                                               "//form[@class='first-instance-form']"
                                               "//button[@type='submit']")[0].click()
        except NoSuchElementException:
            logging.warning(
                '{} - Element not found.'.format(
                    number
                )
            )
            return None

        try:
            captcha_pass = False
            for i in range(3):
                if self.resolve_captcha() is True:
                    captcha_pass = True
                    break
        except UnexpectedAlertPresentException:
            logging.warning(
                '{} - Download do arquivo não permitido'.format(
                    number
                )
            )

            return None

        if not captcha_pass:
            logging.warning(
                '{} - Captcha failed.'.format(
                    number
                )
            )
            return None

        try:
            self.driver.find_elements_by_xpath("//*[contains(text(), ' Andamentos')]")[0].click()

        except:
            logging.warning(
                '{} - Element not found.'.format(
                    number
                )
            )
            return None

        all_tr_items = self.driver.find_elements_by_xpath("//table[@class='corpo']/tbody/tr[contains(@class, 'linha')]")

        try:
            for word in search_word:
                for tr in all_tr_items:
                    td_elems = tr.find_elements_by_xpath("td")
                    if word in td_elems[1].text.strip():
                        download_btn = td_elems[0].find_elements_by_xpath(".//a")[0]
                        download_btn.click()
                        doc_id = download_btn.get_attribute("href")
                        doc_id = re.search(r"javascript:mostrarOcultarPanel\((.*)?\)", doc_id).group(1)[1:][:-1]
                        download_btn = self.driver.find_elements_by_xpath("//table[@id='painelMov" + doc_id + "']//a")[0]
                        pdf_url_name = download_btn.text
                        download_btn.click()
                        time.sleep(5)
                        self.rename(pdf_url_name, number, td_elems[1].text.strip())
        except NoSuchElementException:
            logging.warning(
                '{} - Download failed.'.format(
                    number
                )
            )
            return None

        return True

    def resolve_captcha(self):
        try:
            self.driver.find_element_by_id('captcha_image')
        except NoSuchElementException:
            return True

        try:
            size_image = 1360, 900
            element = self.driver.find_element_by_id('captcha_image')
            location = element.location
            size = element.size
            png = self.driver.get_screenshot_as_png()
            im = Image.open(BytesIO(png))
            im.thumbnail(size_image, Image.ANTIALIAS)
            left = location['x']
            top = location['y']
            right = location['x'] + size['width']
            bottom = location['y'] + size['height']
            im = im.crop((left, top, right, bottom))
            im.save('screenshot.png')

            files = {'file': open('screenshot.png', 'rb')}
            data = {'key': KEY}
            response = requests.post(
                URL_POST_CAPTCHA,
                files=files,
                data=data,
                timeout=15
            )
            if response.ok:
                time.sleep(15)
                id_message = response.text.split('|')[-1]
                resolved_captcha = requests.get(
                    '{}?key={}&action=get&id={}'.format(
                        URL_GET_CAPTCHA,
                        KEY,
                        id_message
                    ),
                    timeout=15
                )
                message = resolved_captcha.text.split('|')[-1]
                self.driver.find_element_by_id('captcha_text').send_keys(message)
                return True
        except:
            return False

    def csv_parsing(self, csv_file, csv_words, work_folder='./'):
        global COUNT_NUMBERS

        with open(csv_file, newline='') as f1:
            reader1 = csv.DictReader(f1)
            COUNT_NUMBERS = len([_ for _ in reader1])

        with open(csv_file, newline='') as f2:
            reader2 = csv.DictReader(f2)
            for row in reader2:
                # try:
                    self.search_process(
                        number=row['processo'],
                        search_word=csv_words,
                        work_folder=work_folder
                    )

                    self.progress_bar()
                # except Exception as e:
                #     pass
                    # logging.warning(
                    #     '{} - Download do arquivo não permitido'.format(
                    #         row['processo']
                    #     )
                    # )

    @staticmethod
    def progress_bar():
        global COUNT_NUMBERS
        global CURRENT_NUMBERS

        CURRENT_NUMBERS += 1
        sys.stdout.write("\r" + str(
            'Progress Downloading Numbers: {}/{}'.format(
                CURRENT_NUMBERS,
                COUNT_NUMBERS
            )
        ))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='portal tjmg automation.')
    parser.add_argument(
        '-csv_numbers',
        dest='csv_numbers',
        type=str,
        help='Input CSV numbers'
    )
    parser.add_argument(
        '-csv_words',
        dest='csv_words',
        type=str,
        help='Input CSV words'
    )
    parser.add_argument(
        '-download_folder',
        dest='download_folder',
        type=str,
        help='Folder where will be stored pdf files',
        default='./'
    )
    parser.add_argument(
        '-number',
        dest='number',
        type=str,
        help='Number of search pdf',
        action='store',
        nargs='*',
    )
    args = parser.parse_args()

    ja = TjmgAutomation(args.download_folder, headless=True)
    search_words = []

    if args.download_folder:
        if not os.path.exists(args.download_folder):
            os.makedirs(args.download_folder)

    if args.csv_words:
        with open(args.csv_words, newline='') as f:
            search_words = [i.replace('\n', '') for i in f.readlines()]

    if args.csv_numbers and args.csv_words:
        ja.csv_parsing(
            args.csv_numbers,
            search_words,
            work_folder=args.download_folder
        )
        ja.driver.quit()
        sys.exit()

    elif args.number and args.csv_words:
        COUNT_NUMBERS = len(args.number)
        for num in args.number:
            ja.search_process(num, search_words, args.download_folder)
            ja.progress_bar()

    if args.download_folder:
        sys.stdout.write(
            "\nFiles stored in folder: {}\n".format(args.download_folder)
        )

    ja.driver.quit()
