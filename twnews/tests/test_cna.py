"""
中央社單元測試
"""

import unittest
from twnews.soup import NewsSoup, pkgdir

#@unittest.skip
class TestCna(unittest.TestCase):

    def setUp(self):
        self.url = 'https://www.cna.com.tw/news/asoc/201810170077.aspx'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup(pkgdir + '/samples/cna.html', mobile=False)
        self.assertEqual('cna', nsoup.channel)
        self.assertIn('平鎮輪胎行惡火  疏散7人1女命喪', nsoup.title())
        self.assertEqual('2016-03-19 10:48:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('桃園市平鎮區一家輪胎行', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('cna', nsoup.channel)
        self.assertIn('前女友輕生  前男友到殯儀館砍現任還開槍', nsoup.title())
        self.assertEqual('2018-10-17 14:06:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('民主進步黨籍嘉義市議員王美惠上午到殯儀館參加公祭', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('cna', nsoup.channel)
        self.assertIn('前女友輕生  前男友到殯儀館砍現任還開槍', nsoup.title())
        self.assertEqual('2018-10-17 14:06:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('民主進步黨籍嘉義市議員王美惠上午到殯儀館參加公祭', nsoup.contents())
