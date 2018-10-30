"""
分解程式共用單元測試
"""

import os
import re
import unittest
from twnews.soup import NewsSoup

#@unittest.skip
class TestCommon(unittest.TestCase):

    def setUp(self):
        self.url = 'https://tw.news.appledaily.com/local/realtime/20181025/1453825'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_cache(self):
        """
        測試快取機制
        """

        # 清除快取
        for cache_file in os.listdir('cache'):
            if re.match(r'appledaily-mobile-.*\.html', cache_file):
                cache_path = 'cache/{}'.format(cache_file)
                os.unlink(cache_path)

        # 讀取新聞，計算快取檔案數
        count = 0
        nsoup = NewsSoup(self.url)
        for cache_file in os.listdir('cache'):
            if re.match(r'appledaily-mobile-.*\.html', cache_file):
                count += 1

        self.assertEqual(1, count)
