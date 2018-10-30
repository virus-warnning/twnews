"""
三立新聞網單元測試
"""

import time
import unittest
from twnews.soup import NewsSoup

#@unittest.skip
class TestSetn(unittest.TestCase):

    def setUp(self):
        self.url = 'http://www.setn.com/News.aspx?NewsID=350370'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup('samples/setn.html', mobile=False)
        self.assertEqual('setn', nsoup.channel)
        self.assertIn('與母爭吵疑失足墜樓　男子送醫搶救不治', nsoup.title())
        self.assertEqual('2018-02-21 18:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('', nsoup.author())
        self.assertIn('新北市新店區中正路今（21）日下午3時許發生墜樓案件', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('setn', nsoup.channel)
        self.assertIn('與母爭吵疑失足墜樓　男子送醫搶救不治', nsoup.title())
        self.assertEqual('2018-02-21 18:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('', nsoup.author())
        self.assertIn('新北市新店區中正路今（21）日下午3時許發生墜樓案件', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值

        02, 03 連續執行時，行動版會變成桌面版的結構
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('setn', nsoup.channel)
        self.assertIn('與母爭吵疑失足墜樓　男子送醫搶救不治', nsoup.title())
        self.assertEqual('2018-02-21 18:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('新北市新店區中正路今（21）日下午3時許發生墜樓案件', nsoup.contents())
