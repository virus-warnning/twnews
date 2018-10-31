import io
import re
import os
import json
import hashlib
import logging
import logging.config
import os.path
from datetime import datetime

import requests
from bs4 import BeautifulSoup

pkgdir = os.path.dirname(__file__)
logini = '{}/conf/logging.ini'.format(pkgdir)

if os.path.isfile(logini):
    logging.config.fileConfig(logini)
logger = logging.getLogger()

__allconf = None
__session = {
    'desktop': None,
    'mobile': None
}

def get_session(mobile=True):
    """
    取得 requests session 如果已經存在就使用現有的

    桌面版和行動版的 session 必須分開使用，否則會發生行動版網址回應桌面版網頁的問題
    已知 setn 和 ettoday 的單元測試程式能發現此問題
    """
    global __session

    device = 'mobile' if mobile else 'desktop'
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

def soup_from_website(url, channel, refresh, mobile):
    """
    網址轉換成 BeautifulSoup 4 物件
    """

    # 強制使用 https
    if url.startswith('http://'):
        url = 'https://' + url[7:]
        logger.debug('變更 URL 為: {}'.format(url))

    # 處理非 RWD 設計的網址轉換 (自由、三立)
    suffix = url[url.find('/', 10):]
    (_, conf) = load_soup_conf(channel)
    if not conf['rwd']:
        if mobile:
            prefix_exp = conf['mobile']['prefix']
            prefix_uex = conf['desktop']['prefix']
        else:
            prefix_exp = conf['desktop']['prefix']
            prefix_uex = conf['mobile']['prefix']
        if not url.startswith(prefix_exp):
            suffix = url[len(prefix_uex):]
            url = prefix_exp + suffix
            logger.debug('prefix: {}'.format(prefix_exp))
            logger.debug('suffix: {}'.format(suffix))
            logger.debug('變更 URL 為: {}'.format(url))

    # 嘗試使用快取
    soup = None
    device = 'mobile' if mobile else 'desktop'
    hash = hashlib.md5(suffix.encode('ascii')).hexdigest()
    path = 'cache/{}-{}-{}.html'.format(channel, device, hash)
    if os.path.isfile(path) and not refresh:
        logger.debug('發現 URL 快取: {}'.format(url))
        logger.debug('載入快取檔案: {}'.format(path))
        soup = soup_from_file(path)

    # 下載網頁
    if soup is None:
        logger.debug('從網路讀取 URL: {}'.format(url))
        session = get_session(mobile)
        resp = session.get(url, allow_redirects=False)
        if resp.status_code == 200:
            logger.debug('回應 200 OK')
            for (k,v) in resp.headers.items():
                logger.debug('{}: {}'.format(k, v))
            soup = BeautifulSoup(resp.text, 'lxml')

            if not os.path.isdir('cache'):
                os.mkdir('cache')

            with open(path, 'w') as cache_file:
                logger.debug('寫入快取: {}'.format(path))
                cache_file.write(resp.text)
        else:
            logger.warning('回應碼: {}'.format(resp.status_code))

    return soup

def soup_from_file(file_path):
    """
    本地檔案轉換成 BeautifulSoup 4 物件
    """
    soup = None
    with open(file_path, 'r') as cache_file:
        html = cache_file.read()
        soup = BeautifulSoup(html, 'lxml')
    return soup

def scan_author(article):
    """
    從新聞內文找出記者姓名
    """
    patterns = [
        '（(.{2,5})／.+報導）',
        '記者(.{2,5})／.+報導',
        '中心(.{2,5})／.+報導'
    ]
    for p in patterns:
        po = re.compile(p)
        m = po.search(article)
        if m is not None:
            return m[1]

def load_soup_conf(path):
    """
    載入新聞解構設定
    """
    global __allconf

    if __allconf is None:
        soup_cfg = '{}/conf/news-soup.json'.format(pkgdir)
        with open(soup_cfg, 'r') as conf_file:
            __allconf = json.load(conf_file)

    for (channel, conf) in __allconf.items():
        if channel in path:
            if channel in path:
                return (channel, conf)

    return (None, None)

class NewsSoup:

    def __init__(self, path, refresh=False, mobile=True):
        self.soup = None
        self.device = 'mobile' if mobile else 'desktop'
        self.cache = {
            'title': None,
            'date': None,
            'author': None,
            'contents': None,
            'tags': None
        }

        (self.channel, self.conf) = load_soup_conf(path)

        if self.channel is not None:
            try:
                if path.startswith('http'):
                    self.soup = soup_from_website(path, self.channel, refresh, mobile)
                else:
                    logger.debug('從檔案載入新聞')
                    self.soup = soup_from_file(path)
            except Exception as ex:
                logger.error('無法載入新聞, {}'.format(ex))

            if self.soup is None:
                logger.error('無法轉換 BeautifulSoup，可能是網址或檔案路徑錯誤')
        else:
            logger.error('不支援的新聞台，請檢查設定檔')

    def title(self):
        if self.cache['title'] is None:
            nsel = self.conf[self.device]['title_node']
            attr = self.conf[self.device]['title_attr']
            found = self.soup.select(nsel)
            if len(found) > 0:
                node = found[0]
                if attr != '':
                    self.cache['title'] = node[attr]
                else:
                    self.cache['title'] = node.text.strip()
                if len(found) > 1:
                    logger.warning('找到多組標題節點 (新聞台: {})'.format(self.channel))
            else:
                logger.error('找不到標題節點 (新聞台: {})'.format(self.channel))

        return self.cache['title']

    def date(self):
        if self.cache['date'] is None:
            nsel = self.conf[self.device]['date_node']
            dfmt = self.conf[self.device]['date_format']
            found = self.soup.select(nsel)
            if len(found) > 0:
                node = found[0]
                # ettoday 的日期有換行字元，要先過濾再跑 strptime
                # TODO: 處理 parsing 例外
                self.cache['date'] = datetime.strptime(node.text.strip(), dfmt)
                if len(found) > 1:
                    logger.warning('發現多組日期節點 (新聞台: {})'.format(self.channel))
            else:
                logger.error('找不到日期時間節點 (新聞台: {})'.format(self.channel))

        return self.cache['date']

    def author(self):
        if self.cache['author'] is None:
            nsel = self.conf[self.device]['author_node']
            if nsel != '':
                found = self.soup.select(nsel)
                if len(found) > 0:
                    node = found[0]
                    self.cache['author'] = node.text
                    if len(found) > 1:
                        logger.warning('找到多組記者姓名 (新聞台: {})'.format(self.channel))
                else:
                    logger.error('找不到記者節點 (新聞台: {})'.format(self.channel))
            else:
                contents = self.contents()
                if contents is not None:
                    self.cache['author'] = scan_author(contents)
                    if self.cache['author'] is None:
                        logger.warning('內文中找不到記者姓名 (新聞台: {})'.format(self.channel))
                else:
                    logger.error('因為沒有內文所以無法比對記者姓名 (新聞台: {})'.format(self.channel))

        return self.cache['author']

    def contents(self):
        if self.cache['contents'] is None:
            nsel = self.conf[self.device]['article_node']
            found = self.soup.select(nsel)
            if len(found) > 0:
                contents = io.StringIO()
                for node in found:
                    contents.write(node.text.strip())
                self.cache['contents'] = contents.getvalue()
                contents.close()
            else:
                logger.error('找不到內文節點 (新聞台: {})'.format(self.channel))

        return self.cache['contents']
