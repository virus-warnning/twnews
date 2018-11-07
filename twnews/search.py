import sys
import time
import urllib.parse
from string import Template
from datetime import datetime

import twnews.common as common

import requests
from bs4 import BeautifulSoup

class NewsSearch:

    def __init__(self, channel, days_limit=30, records_limit=25):
        self.conf = common.get_channel_conf(channel, 'search')
        now_dti = datetime.now()
        beg_dti = datetime.fromtimestamp(now_dti.timestamp() - days_limit * 86400)
        self.now = now_dti.strftime(self.conf['date_query_format'])
        self.beg = beg_dti.strftime(self.conf['date_query_format'])
        self.records_limit = records_limit
        self.pages = 0
        self.elapsed = 0

    def by_keyword(self, keyword, title_only=False):
        logger = common.get_logger()
        page = 1
        results = []
        no_more = False
        begin_time = time.time()

        while not no_more and len(results) < self.records_limit:
            # 組查詢條件
            url = Template(self.conf['url']).substitute({
                'PAGE': page,
                'KEYWORD': urllib.parse.quote_plus(keyword),
                'DATE_BEG': urllib.parse.quote_plus(self.beg),
                'DATE_END': urllib.parse.quote_plus(self.now)
            })

            # 查詢
            session = common.get_session()
            logger.debug('新聞搜尋 ' + url)
            resp = session.get(url, allow_redirects=False)
            if resp.status_code == 200:
                logger.debug('回應 200 OK')
                for (k, v) in resp.headers.items():
                    logger.debug('{}: {}'.format(k, v))
                soup = BeautifulSoup(resp.text, 'lxml')
            else:
                logger.warning('回應碼: {}'.format(resp.status_code))
                break

            # 拆查詢結果
            result_nodes = soup.select(self.conf['result_node'])
            if len(result_nodes) > 0:
                for n in result_nodes:
                    title_node = n.select(self.conf['title_node'])[0]
                    date_node = n.select(self.conf['date_node'])[0]
                    title = title_node.text.strip()
                    link  = title_node['href']
                    date_inst = datetime.strptime(date_node.text.strip(), self.conf['date_format'])
                    if (not title_only) or (keyword in title):
                        results.append({
                            "title": title,
                            "link": link,
                            'date': date_inst
                        })
                        if len(results) == self.records_limit: break
            else:
                no_more = True

            page += 1

        self.pages = page - 1
        self.elapsed = time.time() - begin_time

        return results

def main():
    if len(sys.argv) > 1:
        keyword = sys.argv[1]
    else:
        keyword = '上吊'

    nsearch = NewsSearch('appledaily', 30, 10)
    results = nsearch.by_keyword(keyword, True)
    i = 0
    for r in results:
        i += 1
        print('{:03d}: {} ({})'.format(i, r['title'], r['date'].strftime('%Y-%m-%d')))
        print('     {}'.format(r['link']))

    print('-' * 75)
    print('耗時 {:.2f} 秒，分析 {} 頁查詢結果'.format(nsearch.elapsed, nsearch.pages))

if __name__ == '__main__':
    main()
