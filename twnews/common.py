"""
twnews 共用項目
"""

import json
import os
import os.path
import logging
import logging.config

import requests

# pylint: disable=global-statement
__LOGGER = None
__ALLCONF = None
__SESSION = {
    'desktop': None,
    'mobile': None
}

VERSION = '0.2.2'

def get_package_dir():
    """
    取得套件根目錄，用來定位套件內資源
    """
    return os.path.dirname(__file__)

def get_logger():
    """
    取得 logger 如果已經存在就使用現有的
    """
    global __LOGGER

    if __LOGGER is None:
        logdir = os.path.expanduser('~/.twnews/log')
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

        logini = '{}/conf/logging.ini'.format(get_package_dir())
        if os.path.isfile(logini):
            logging.config.fileConfig(logini)
        __LOGGER = logging.getLogger()

    return __LOGGER

def get_session(mobile=True):
    """
    取得 requests session 如果已經存在就使用現有的

    桌面版和行動版的 session 必須分開使用，否則會發生行動版網址回應桌面版網頁的問題
    已知 setn 和 ettoday 的單元測試程式能發現此問題
    """
    global __SESSION

    device = 'mobile' if mobile else 'desktop'
    logger = get_logger()

    if __SESSION[device] is None:
        if mobile:
            user_agent = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) ' \
                + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36'
        else:
            user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) ' \
                + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'

        logger.debug('產生 session[%s]', device)
        __SESSION[device] = requests.Session()
        __SESSION[device].headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "User-Agent": user_agent
        })
    else:
        logger.debug('使用既有 session[%s]', device)

    return __SESSION[device]

def get_all_conf():
    """
    取得完整設定
    """
    global __ALLCONF

    if __ALLCONF is None:
        soup_cfg = '{}/conf/news-soup.json'.format(get_package_dir())
        with open(soup_cfg, 'r') as conf_file:
            __ALLCONF = json.load(conf_file)

    return __ALLCONF

def detect_channel(path):
    """
    偵測路徑對應的新聞頻道
    """
    all_conf = get_all_conf()
    for channel in all_conf:
        if channel in path:
            return channel
    return ''

def get_channel_conf(channel, action=None):
    """
    載入新聞台設定
    """
    all_conf = get_all_conf()

    if channel in all_conf:
        chconf = all_conf[channel]
        if action is None:
            return chconf
        if action in chconf:
            return chconf[action]

    return None
