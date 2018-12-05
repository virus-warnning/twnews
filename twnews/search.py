"""
新聞搜尋模組
"""

import re
import time
import os.path
import urllib.parse
from string import Template
from datetime import datetime

from bs4 import BeautifulSoup
from bs4.element import Tag

import twnews.common
from twnews.soup import NewsSoup

def visit_dict(dict_node, path):
    """
    用 CSS Selector 的形式拜訪 dict
    """
    keys = []
    if path != '':
        keys = path.split(' > ')
    visited = dict_node
    for key in keys:
        visited = visited[key]
    return visited

def filter_duplicated(results):
    """
    以連結為鍵值去重複化
    """
    filtered = []
    logger = twnews.common.get_logger()

    for (cidx, result) in enumerate(results):
        duplicated = False
        pidx = -1
        for pidx in range(cidx):
            previous = results[pidx]
            if result['link'] == previous['link']:
                duplicated = True

        if not duplicated:
            filtered.append(result)
        else:
            logger.warning('查詢結果的 %d, %d 筆重複，新聞網址 %s', cidx, pidx, result['link'])

    return filtered

class NewsSearchException(Exception):
    """
    新聞搜尋例外
    """
    pass

class NewsSearch:
    """
    新聞搜尋器
    """

    def __init__(self, channel, limit=25, beg_date=None, end_date=None):
        """
        配置新聞搜尋器
        """
        # 防止用中時搜尋
        if channel == 'chinatimes':
            msg = '頻道 {} 不支援搜尋功能'.format(channel)
            raise NewsSearchException(msg)

        # 防止開始日期和結束日期只設定了一個
        if beg_date is None or end_date is None:
            if end_date is not None:
                msg = '遺漏了開始日期'
                raise NewsSearchException(msg)
            if beg_date is not None:
                msg = '遺漏了結束日期'
                raise NewsSearchException(msg)

        # 防止開始日期和結束日期格式錯誤
        self.params = {
            'beg_date': None,
            'end_date': None,
            'channel': channel,
            'limit': limit
        }
        try:
            if beg_date is not None:
                self.params['beg_date'] = datetime.strptime(beg_date, '%Y-%m-%d')
            if end_date is not None:
                self.params['end_date'] = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            msg = '日期必須是 ISO 格式 (yyyy-mm-dd)'
            raise NewsSearchException(msg)

        # 防止開始日期大於結束日期
        if self.params['beg_date'] is not None:
            delta = self.params['end_date'] - self.params['beg_date']
            if delta.days < 0:
                msg = '開始日期必須小於或等於結束日期'
                raise NewsSearchException(msg)
            if delta.days > 90 and channel == 'ltn':
                msg = '頻道 {} 的日期條件必須在 90 天內'.format(channel)
                raise NewsSearchException(msg)

        self.conf = twnews.common.get_channel_conf(channel, 'search')
        self.context = None
        self.result = {
            'pages': 0,
            'elapsed': 0,
            'items': []
        }
        self.url_prefix = {
            'host': '',
            'base': ''
        }

    def by_keyword(self, keyword, title_only=False):
        """
        關鍵字搜尋
        """
        logger = twnews.common.get_logger()
        page = 1
        results = []
        no_more = False
        begin_time = time.time()

        # 如果蘋果和自由以外的媒體有設定日期範圍，先跳到合適的頁數
        # -   支援: 東森、聯合
        # - 不支援: 三立、中央社
        # TODO: 三立、中央社研擬假設 500 頁的二分翻頁法
        if self.params['beg_date'] is not None and self.params['channel'] in ['ettoday', 'udn']:
            # 東森、聯合採取二分翻頁法
            page = self.__flip_to_end_date(keyword)

        while not no_more and len(results) < self.params['limit']:
            self.__load_page(keyword, page)

            # 拆查詢結果
            result_nodes = self.__result_nodes()
            result_count = len(result_nodes)
            logger.info('第 %d 頁: 有 %d 筆搜尋結果', page, result_count)
            if result_count > 0:
                for node in result_nodes:
                    date_inst = self.__parse_date_node(node)
                    if self.params['beg_date'] is not None and \
                       self.params['channel'] not in ['appledaily', 'ltn']:
                        # 過濾開頭超過日期範圍的項目
                        if date_inst > self.params['end_date']:
                            continue
                        # 過濾結尾超過日期範圍的項目
                        if date_inst < self.params['beg_date']:
                            no_more = True
                            break

                    title = self.__parse_title_node(node)
                    link = self.__parse_link_node(node)
                    if (not title_only) or (keyword in title):
                        results.append({
                            "title": title,
                            "link": link,
                            'date': date_inst
                        })
                        if len(results) == self.params['limit']:
                            break
            else:
                no_more = True

            page += 1

        self.result = {
            'pages': page - 1,
            'elapsed': time.time() - begin_time,
            'items': filter_duplicated(results)
        }

        return self

    def to_dict_list(self):
        """
        回傳新聞查詢結果
        """
        return self.result['items']

    def to_soup_list(self):
        """
        回傳新聞查詢結果的分解器
        """
        soup_list = []
        for result in self.result['items']:
            nsoup = NewsSoup(result['link'])
            soup_list.append(nsoup)
        return soup_list

    def elapsed(self):
        """
        耗費時間
        """
        return self.result['elapsed']

    def pages(self):
        """
        頁數
        """
        return self.result['pages']

    def __flip_to_end_date(self, keyword):
        """
        回傳篩選時間範圍的開始頁數
        """

        page_range = {
            'lower': 1,
            'upper': 1000
        }

        date_range = {
            'lower': datetime.fromtimestamp(0),
            'upper': datetime.today()
        }

        # 取得最大頁數
        self.__load_page(keyword, 1)
        node = self.context.select(self.conf['last_page'])[0]
        if 'page_pattern' in self.conf:
            match = re.search(self.conf['page_pattern'], node.text)
            if match:
                page_range['upper'] = int(match.group(1))
            else:
                page_range['upper'] = -1
        else:
            try:
                page_range['upper'] = int(node.text)
            except ValueError:
                page_range['upper'] = -1

        if page_range['upper'] == -1:
            return 1

        # 取第一則搜尋結果的日期
        date_range['upper'] = self.__parse_date_node(self.__result_nodes()[0])
        if date_range['upper'] < self.params['end_date']:
            return 1

        # 取最後一頁最後一則搜尋結果的日期
        self.__load_page(keyword, page_range['upper'])
        date_range['lower'] = self.__parse_date_node(self.__result_nodes()[-1])
        if date_range['lower'] > self.params['end_date']:
            return -1

        # 起始狀態
        page_dist = page_range['upper'] - page_range['lower']
        prev_dist = page_range['upper'] - page_range['lower'] + 1
        logger = twnews.common.get_logger()
        logger.info(
            'page: %d ~ %d, date: %s ~ %s',
            page_range['lower'],
            page_range['upper'],
            date_range['upper'],
            date_range['lower']
        )

        # 取中間頁數，檢查是否能縮小範圍
        # 不能縮小範圍時，表示 page_range 的新聞都有 self.params['end_date'] 這一天的
        while page_dist < prev_dist:
            mid_page = (page_range['lower'] + page_range['upper']) // 2
            self.__load_page(keyword, mid_page)
            middle_udt = self.__parse_date_node(self.__result_nodes()[0])
            middle_ldt = self.__parse_date_node(self.__result_nodes()[-1])

            if middle_udt > self.params['end_date']:
                page_range['lower'] = mid_page
                date_range['upper'] = middle_udt

            if middle_ldt < self.params['end_date']:
                page_range['upper'] = mid_page
                date_range['lower'] = middle_ldt

            prev_dist = page_dist
            page_dist = page_range['upper'] - page_range['lower']
            logger.info(
                'page: %d ~ %d, date: %s ~ %s, mid=%d',
                page_range['lower'],
                page_range['upper'],
                date_range['upper'],
                date_range['lower'],
                mid_page
            )

        return page_range['lower']

    def __load_page(self, keyword, page):
        # 組查詢條件
        replacement = {
            'PAGE': page,
            'KEYWORD': urllib.parse.quote_plus(keyword)
        }
        url = Template(self.conf['url']).substitute(replacement)

        # 再加上日期範圍
        if self.params['beg_date'] is not None and self.params['channel'] in ['appledaily', 'ltn']:
            url += self.params['beg_date'].strftime(self.conf['begin_date_format'])
            url += self.params['end_date'].strftime(self.conf['end_date_format'])

        # 查詢
        session = twnews.common.get_session()
        logger = twnews.common.get_logger()
        logger.info('新聞搜尋 %s', url)
        resp = session.get(url, allow_redirects=False)
        if resp.status_code == 200:
            logger.debug('回應 200 OK')
            ctype = resp.headers['Content-Type']
            if 'text/html' in ctype:
                self.context = BeautifulSoup(resp.text, 'lxml')
            if 'application/json' in ctype:
                # TODO: 這裡有時會發生 decode error
                self.context = resp.json()
        elif resp.status_code == 404:
            logger.debug('回應 404 Not Found，視為沒有更多查詢結果')
            self.context = None
        else:
            logger.warning('回應碼: %s', resp.status_code)
            self.context = None

    def __result_nodes(self):
        """
        取查詢結果的 soup 或 dict
        """
        if self.context is not None:
            if isinstance(self.context, BeautifulSoup):
                return self.context.select(self.conf['result_node'])
            return visit_dict(self.context, self.conf['result_node'])
        return []

    def __parse_title_node(self, result_node):
        """
        單筆查詢結果範圍內取標題文字
        """

        if isinstance(result_node, Tag):
            title_node = result_node.select(self.conf['title_node'])[0]
            title = title_node.text.strip()
        else:
            title = visit_dict(result_node, self.conf['title_node'])
        return title

    def __parse_date_node(self, result_node):
        """
        單筆查詢結果範圍內取報導日期
        """

        if isinstance(result_node, Tag):
            date_node = result_node.select(self.conf['date_node'])[0]
            if 'date_pattern' in self.conf:
                # DOM node 除了日期還有其他文字
                match = re.search(self.conf['date_pattern'], date_node.text)
                date_text = match.group(0)
            else:
                # DOM node 只有日期
                date_text = date_node.text.strip()
        else:
            # API 的日期都很乾淨
            date_text = visit_dict(result_node, self.conf['date_node'])

        date_inst = datetime.strptime(date_text, self.conf['date_format'])
        return date_inst

    def __parse_link_node(self, result_node):
        """
        單筆查詢結果範圍內取新聞連結
        """
        if isinstance(result_node, Tag):
            link_node = result_node.select(self.conf['link_node'])[0]
            href = link_node['href']
        else:
            href = visit_dict(result_node, self.conf['link_node'])

        # 完整網址
        if href.startswith('https://'):
            return href

        # 絕對路徑
        if href.startswith('/'):
            if self.url_prefix['host'] == '':
                match = re.match(r'^https://([^/]+)/', self.conf['url'])
                self.url_prefix['host'] = match.group(1)
            return 'https://{}{}'.format(self.url_prefix['host'], href)

        # 相對路徑
        # 自由的 <head> 有設定 base_url
        if self.url_prefix['base'] == '':
            nodes = self.context.select('head > base')
            if len(nodes) == 1:
                self.url_prefix['base'] = nodes[0]['href']
            else:
                base_end = self.conf['url'].rfind('/')
                self.url_prefix['base'] = self.conf['url'][0:base_end+1]

        # 消除三立的 ../
        full_url = self.url_prefix['base'] + href
        spos = full_url.find('/', 10)
        reduced_url = full_url[0:spos] + os.path.realpath(full_url[spos:])

        return reduced_url
