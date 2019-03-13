"""
蘋果日報搜尋測試
"""

import unittest
from twnews.search import NewsSearch

#@unittest.skip
class TestAppleDaily(unittest.TestCase):

    def setUp(self):
        self.keyword = '上吊'
        self.nsearch = NewsSearch('appledaily', limit=10)

    def test_01_filter_title(self):
        """
        測試蘋果日報搜尋
        """
        results = self.nsearch.by_keyword(self.keyword, title_only=True).to_dict_list()
        for topic in results:
            if '上吊' not in topic['title']:
                self.fail('標題必須含有 "上吊"')

    def test_02_search_and_soup(self):
        """
        測試蘋果日報搜尋+分解
        """
        nsoups = self.nsearch.by_keyword(self.keyword).to_soup_list()
        for nsoup in nsoups:
            if nsoup.contents() is None:
                # 因為 home.appledaily.com.tw 的 SSL 憑證有問題，忽略這個因素造成的錯誤
                if not nsoup.path.startswith('https://home.appledaily.com.tw'):
                    msg = '內文不可為 None, URL={}'.format(nsoup.path)
                    self.fail(msg)
