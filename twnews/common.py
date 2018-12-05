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
__SESSION = None

VERSION = '0.2.3'

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

def get_session():
    """
    取得 requests session 如果已經存在就使用現有的
    """
    global __SESSION
    logger = get_logger()

    if __SESSION is None:
        logger.debug('建立新的 session')
        user_agent = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) ' \
            + 'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36'
        __SESSION = requests.Session()
        __SESSION.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "User-Agent": user_agent
        })
    else:
        logger.debug('使用現有 session')

    return __SESSION

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
