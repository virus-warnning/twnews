"""
分解程式共用單元測試
"""

import os
import re
import tempfile
import unittest
from twnews.soup import NewsSoup, get_cache_dir

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
        cache_dir = get_cache_dir()
        for cache_file in os.listdir(cache_dir):
            if re.search(r'\.html\.gz$', cache_file):
                cache_path = '{}/{}'.format(cache_dir, cache_file)
                os.unlink(cache_path)

        # 讀取新聞，計算快取檔案數
        count = 0
        nsoup = NewsSoup(self.url)
        for cache_file in os.listdir(cache_dir):
            if re.search(r'\.html\.gz$', cache_file):
                count += 1
                news_cache = '{}/{}'.format(cache_dir, cache_file)
                news_mtime = os.path.getmtime(news_cache)
        self.assertEqual(1, count)

        # 再次讀取新聞，確認快取檔的 mtime 沒變
        if count == 1:
            nsoup = NewsSoup(self.url)
            news_mtime_new = os.path.getmtime(news_cache)
            self.assertEqual(news_mtime, news_mtime_new)
