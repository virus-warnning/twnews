"""
中央社單元測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestCna(unittest.TestCase):

    def setUp(self):
        self.url = 'https://www.cna.com.tw/news/asoc/201810170077.aspx'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試中央社樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/cna.html.gz')
        self.assertEqual('cna', nsoup.channel)
        self.assertIn('平鎮輪胎行惡火  疏散7人1女命喪', nsoup.title())
        self.assertEqual('2016-03-19 10:48:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('邱俊欽', nsoup.author())
        self.assertIn('桃園市平鎮區一家輪胎行', nsoup.contents())

    def test_03_mobile(self):
        """
        測試中央社行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('cna', nsoup.channel)
        self.assertIn('前女友輕生  前男友到殯儀館砍現任還開槍', nsoup.title())
        self.assertEqual('2018-10-17 14:06:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('黃國芳', nsoup.author())
        self.assertIn('民主進步黨籍嘉義市議員王美惠上午到殯儀館參加公祭', nsoup.contents())
