"""
東森新聞雲單元測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

@unittest.skip
class TestEttoday(unittest.TestCase):

    def setUp(self):
        self.url = 'https://www.ettoday.net/news/20181020/1285826.htm'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試東森新聞雲樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/ettoday.html.gz')
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('客運司機車禍致人於死　心情鬱悶陽台以狗鍊上吊', nsoup.title())
        self.assertEqual('2017-12-09 00:26:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('林悅', nsoup.author())
        self.assertIn('台南市永康區永安路住處後陽台上吊', nsoup.contents())

    def test_03_mobile(self):
        """
        測試東森新聞雲行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('快訊／整日沒出房門！三重無業男半夜住處2樓上吊　母開門才發現', nsoup.title())
        self.assertEqual('2018-10-20 04:11:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('趙永博', nsoup.author())
        self.assertIn('新北市三重區三和路三段101巷一處民宅2樓', nsoup.contents())
