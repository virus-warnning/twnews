"""
新聞湯
"""

import io
import re
import copy
import gzip
import hashlib
import os
import os.path
from datetime import datetime

import requests
import requests.exceptions
from bs4 import BeautifulSoup

import twnews.common

def get_cache_dir():
    """
    取得快取目錄
    """
    logger = twnews.common.get_logger()
    cache_dir = os.path.expanduser('~/.twnews/cache')
    if not os.path.isdir(cache_dir):
        logger.debug('建立快取目錄: %s', cache_dir)
        os.makedirs(cache_dir)
    logger.debug('使用快取目錄: %s', cache_dir)
    return cache_dir

def get_cache_filepath(channel, uri):
    """
    取得快取檔案路徑
    """
    cache_id = hashlib.md5(uri.encode('ascii')).hexdigest()
    path = '{}/{}-{}.html.gz'.format(get_cache_dir(), channel, cache_id)
    return path

def url_follow_redirection(url):
    """
    取得轉址後的 URL
    """
    logger = twnews.common.get_logger()
    session = twnews.common.get_session()
    old_url = url
    new_url = ''
    done = False

    while not done:
        try:
            resp = session.head(old_url)
            status = resp.status_code
            if status // 100 == 3:
                dest = resp.headers['Location']
                if dest.startswith('/'):
                    new_url = old_url[0:old_url.find('/', 10)] + dest
                else:
                    new_url = dest
                logger.debug('原始 URL: %s', old_url)
                logger.debug('變更 URL: %s', new_url)
                old_url = new_url
            elif status == 200:
                done = True
            else:
                logger.error('檢查轉址過程發生錯誤，回應碼: %d', status)
                done = True
        except requests.exceptions.ConnectionError as ex:
            logger.error('檢查轉址過程連線失敗: %s', ex)
            done = True

    return old_url

def url_force_https(url):
    """
    強制使用 https
    """
    logger = twnews.common.get_logger()
    if url.startswith('http://'):
        new_url = 'https://' + url[7:]
        logger.debug('原始 URL: %s', url)
        logger.debug('變更 URL: %s', new_url)
    else:
        new_url = url
    return new_url

def url_force_ltn_mobile(url):
    """
    強制使用自由時報行動版
    """
    logger = twnews.common.get_logger()
    new_url = url
    if url.startswith('https://news.ltn.com.tw'):
        new_url = 'https://m.ltn.com.tw' + url[len('https://news.ltn.com.tw'):]
        logger.debug('原始 URL: %s', url)
        logger.debug('變更 URL: %s', new_url)
    return new_url

def soup_from_website(url, channel, refresh):
    """
    網址轉換成 BeautifulSoup 4 物件
    """
    logger = twnews.common.get_logger()
    session = twnews.common.get_session()

    # 嘗試使用快取
    soup = None
    rawlen = 0
    uri = url[url.find('/', 10):]
    path = get_cache_filepath(channel, uri)
    if os.path.isfile(path) and not refresh:
        logger.debug('發現快取, URL: %s', url)
        logger.debug('載入快取, PATH: %s', path)
        (soup, rawlen) = soup_from_file(path)

    # 下載網頁
    if soup is None:
        logger.debug('GET URL: %s', url)
        try:
            resp = session.get(url, allow_redirects=False)
            if resp.status_code == 200:
                logger.debug('回應 200 OK')
                soup = BeautifulSoup(resp.text, 'lxml')
                rawlen = len(resp.text.encode('utf-8'))
                with gzip.open(path, 'wt') as cache_file:
                    logger.debug('寫入快取: %s', path)
                    cache_file.write(resp.text)
            else:
                logger.warning('回應碼: %d', resp.status_code)
        except requests.exceptions.ConnectionError as ex:
            logger.error('連線失敗: %s', ex)

    return (soup, rawlen)

def soup_from_file(file_path):
    """
    本地檔案轉換成 BeautifulSoup 4 物件
    """
    html = None
    soup = None
    clen = 0

    if file_path.endswith('.gz'):
        # 注意 gzip 預設 mode 是 rb
        with gzip.open(file_path, 'rt') as cache_file:
            html = cache_file.read()
    else:
        with open(file_path, 'r') as cache_file:
            html = cache_file.read()

    if html is not None:
        soup = BeautifulSoup(html, 'lxml')
        clen = len(html.encode('utf-8'))

    return (soup, clen)

def scan_author(article):
    """
    從新聞內文找出記者姓名
    """

    patterns = [
        r'\((.{2,5})／.+報導\)',
        r'（(.{2,5})／.+報導）',
        r'記者(.{2,5})／.+報導',
        r'中心(.{2,5})／.+報導',
        r'記者(.{2,3}).{2}[縣市]?\d{1,2}日電',
        r'（譯者：(.{2,5})/.+）'
    ]

    exclude_list = [
        '國際中心',
        '地方中心',
        '社會中心'
    ]

    for patt in patterns:
        pobj = re.compile(patt)
        match = pobj.search(article)
        if match is not None:
            if match.group(1) not in exclude_list:
                return match.group(1)

    return None

class NewsSoup:
    """
    新聞湯
    """

    def __init__(self, path, refresh=False):
        """
        建立新聞分解器
        """
        self.path = path
        self.refresh = refresh
        self.loaded = False
        self.soup = None
        self.rawlen = 0
        self.logger = twnews.common.get_logger()
        self.channel = twnews.common.detect_channel(path)
        self.cache = {
            'title': None,
            'date_raw': None,
            'date': None,
            'author': None,
            'contents': None,
            'tags': None
        }

        if self.channel == '':
            self.logger.error('不支援的新聞台，請檢查設定檔')
            return

        # URL 正規化
        if self.path.startswith('http'):
            self.path = url_follow_redirection(self.path)
            self.path = url_force_https(self.path)
            if self.channel == 'ltn':
                self.path = url_force_ltn_mobile(self.path)

        # Layout 偵測
        layout = 'mobile'
        layout_list = twnews.common.get_channel_conf(self.channel, 'layout_list')
        for item in layout_list:
            if path.startswith(item['prefix']):
                layout = item['layout']

        self.conf = twnews.common.get_channel_conf(self.channel, layout)

    def __get_soup(self):
        if not self.loaded:
            try:
                if self.path.startswith('http'):
                    self.logger.debug('從網路載入新聞')
                    (self.soup, self.rawlen) = soup_from_website(
                        self.path,
                        self.channel,
                        self.refresh
                    )
                else:
                    self.logger.debug('從檔案載入新聞')
                    (self.soup, self.rawlen) = soup_from_file(self.path)
            except requests.ConnectionError as ex:
                self.logger.error('因連線問題，無法載入新聞: %s', ex)
                self.logger.error(self.path)
            except FileNotFoundError as ex:
                self.logger.error('檔案不存在，無法載入新聞: %s', ex)
                self.logger.error(self.path)
            except TypeError as ex:
                self.logger.error('頻道不存在，無法載入新聞: %s', ex)
                self.logger.error(self.path)

            if self.soup is None:
                self.logger.error('無法轉換 BeautifulSoup，可能是網址或檔案路徑錯誤')

        return self.soup

    def title(self):
        """
        取得新聞標題
        """

        soup = self.__get_soup()
        if soup is None:
            return None

        if self.cache['title'] is None:
            nsel = self.conf['title_node']
            found = soup.select(nsel)
            if found:
                node = copy.copy(found[0])
                # 避免子元件干擾日期格式
                for child_node in node.select('*'):
                    child_node.extract()
                self.cache['title'] = node.text.strip()
                if len(found) > 1:
                    self.logger.warning('找到多組標題節點 (新聞台: %s)', self.channel)
            else:
                self.logger.error('找不到標題節點 (新聞台: %s)', self.channel)

        return self.cache['title']

    def date_raw(self):
        """
        取得原始時間字串
        """

        soup = self.__get_soup()
        if soup is None:
            return None

        if self.cache['date_raw'] is None:
            nsel = self.conf['date_node']
            found = soup.select(nsel)
            if found:
                node = copy.copy(found[0])
                # 避免子元件干擾日期格式
                for child_node in node.select('*'):
                    child_node.extract()
                self.cache['date_raw'] = node.text.strip()
                if len(found) > 1:
                    self.logger.warning('發現多組日期節點 (新聞台: %s)', self.channel)
            else:
                self.logger.error('找不到日期時間節點 (新聞台: %s)', self.channel)

        return self.cache['date_raw']

    def date(self):
        """
        取得 datetime.datetime 格式的時間
        """

        soup = self.__get_soup()
        if soup is None:
            return None

        if self.cache['date'] is None:
            dfmt = self.conf['date_format']
            try:
                self.cache['date'] = datetime.strptime(self.date_raw(), dfmt)
            except TypeError as ex:
                self.logger.error('日期格式分析失敗 %s (新聞台: %s)', ex, self.channel)
            except ValueError as ex:
                self.logger.error('日期格式分析失敗 %s (新聞台: %s)', ex, self.channel)
        return self.cache['date']

    def author(self):
        """
        取得新聞記者/社論作者
        """

        soup = self.__get_soup()
        if soup is None:
            return None

        if self.cache['author'] is None:
            nsel = self.conf['author_node']
            if nsel != '':
                found = soup.select(nsel)
                if found:
                    node = copy.copy(found[0])
                    for child_node in node.select('*'):
                        child_node.extract()
                    self.cache['author'] = node.text.strip()
                    if len(found) > 1:
                        self.logger.warning('找到多組記者姓名 (新聞台: %s)', self.channel)
                else:
                    self.logger.warning('找不到記者節點 (新聞台: %s)', self.channel)
            else:
                contents = self.contents()
                if contents is not None:
                    self.cache['author'] = scan_author(contents)
                    if self.cache['author'] is None:
                        self.logger.warning('內文中找不到記者姓名 (新聞台: %s)', self.channel)
                else:
                    self.logger.error('因為沒有內文所以無法比對記者姓名 (新聞台: %s)', self.channel)

        return self.cache['author']

    def contents(self, limit=0):
        """
        取得新聞內文
        """

        soup = self.__get_soup()
        if soup is None:
            return None

        if self.cache['contents'] is None:
            nsel = self.conf['article_node']
            found = soup.select(nsel)
            if found:
                contents = io.StringIO()
                for node in found:
                    contents.write(node.text.strip())
                self.cache['contents'] = contents.getvalue()
                contents.close()
            else:
                self.logger.error('找不到內文節點 (新聞台: %s)', self.channel)

        if isinstance(self.cache['contents'], str) and limit > 0:
            # https://github.com/PyCQA/pylint/issues/1498
            # pylint: disable=unsubscriptable-object
            return self.cache['contents'][0:limit]

        return self.cache['contents']

    def effective_text_rate(self):
        """
        計算有效內容率 (有效內容位元組數/全部位元組數)
        """

        soup = self.__get_soup()
        if soup is None or self.rawlen == 0:
            return 0

        data = [
            self.title(),
            self.author(),
            self.date_raw(),
            self.contents()
        ]

        useful_len = 0
        for datum in data:
            if datum is not None:
                useful_len += len(datum.encode('utf-8'))

        return useful_len / self.rawlen
