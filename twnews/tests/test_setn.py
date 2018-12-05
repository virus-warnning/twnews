"""
三立新聞網單元測試
"""

import time
import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestSetn(unittest.TestCase):

    def setUp(self):
        self.url = 'http://www.setn.com/News.aspx?NewsID=350370'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試三立新聞網樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/setn.html.gz')
        self.assertEqual('setn', nsoup.channel)
        self.assertIn('與母爭吵疑失足墜樓　男子送醫搶救不治', nsoup.title())
        self.assertEqual('2018-02-21 18:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('新北市新店區中正路今（21）日下午3時許發生墜樓案件', nsoup.contents())

    def test_03_mobile(self):
        """
        測試三立新聞網行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('setn', nsoup.channel)
        self.assertIn('與母爭吵疑失足墜樓　男子送醫搶救不治', nsoup.title())
        self.assertEqual('2018-02-21 18:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('新北市新店區中正路今（21）日下午3時許發生墜樓案件', nsoup.contents())
