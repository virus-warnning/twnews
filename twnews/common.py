import json
import os
import os.path
import logging
import logging.config

import requests

__logger = None
__allconf = None
__session = {
    'desktop': None,
    'mobile': None
}

VERSION = '0.2.2'

def get_logger():
    """
    取得 logger 如果已經存在就使用現有的
    """
    global __logger

    if __logger is None:
        logdir = os.path.expanduser('~/.twnews/log')
        if not os.path.isdir(logdir):
            os.makedirs(logdir)

        pkgdir = os.path.dirname(__file__)
        logini = '{}/conf/logging.ini'.format(pkgdir)

        if os.path.isfile(logini):
            logging.config.fileConfig(logini)
        __logger = logging.getLogger()

    return __logger

def get_session(mobile=True):
    """
    取得 requests session 如果已經存在就使用現有的

    桌面版和行動版的 session 必須分開使用，否則會發生行動版網址回應桌面版網頁的問題
    已知 setn 和 ettoday 的單元測試程式能發現此問題
    """
    global __session

    device = 'mobile' if mobile else 'desktop'
    logger = get_logger()

    if __session[device] is None:
        if mobile:
            ua = 'Mozilla/5.0 (Linux; Android 4.0.4; Galaxy Nexus Build/IMM76B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.76 Mobile Safari/537.36'
        else:
            ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'

        logger.debug('產生 session[{}]'.format(device))
        __session[device] = requests.Session()
        __session[device].headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "User-Agent": ua
        })
    else:
        logger.debug('使用既有 session[{}]'.format(device))

    return __session[device]

def get_channel_conf(channel, action):
    """
    載入新聞台設定
    """
    global __allconf

    if __allconf is None:
        pkgdir = os.path.dirname(__file__)
        soup_cfg = '{}/conf/news-soup.json'.format(pkgdir)
        with open(soup_cfg, 'r') as conf_file:
            __allconf = json.load(conf_file)

    if channel in __allconf:
        chconf = __allconf[channel]
        if action in chconf:
            return chconf[action]

    return None
