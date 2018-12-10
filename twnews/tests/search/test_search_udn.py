"""
蘋果日報搜尋測試
"""

import unittest
from twnews.search import NewsSearch

#@unittest.skip
class TestUdn(unittest.TestCase):

    def setUp(self):
        self.keyword = '上吊'
        self.nsearch = NewsSearch('udn', limit=10)

    def test_01_filter_title(self):
        """
        測試聯合新聞網搜尋
        """
        results = self.nsearch.by_keyword(self.keyword, title_only=True).to_dict_list()
        for topic in results:
            if '上吊' not in topic['title']:
                self.fail('標題必須含有 "上吊"')

    def test_02_search_and_soup(self):
        """
        測試聯合新聞網搜尋+分解
        """
        nsoups = self.nsearch.by_keyword(self.keyword).to_soup_list()
        for nsoup in nsoups:
            if nsoup.title() is None:
                self.fail('標題不可為 None')
