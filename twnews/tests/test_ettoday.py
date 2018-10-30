"""
東森新聞雲單元測試
"""

import unittest
from twnews.soup import NewsSoup, pkgdir

#@unittest.skip
class TestEttoday(unittest.TestCase):

    def setUp(self):
        self.url = 'https://www.ettoday.net/news/20181020/1285826.htm'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup(pkgdir + '/samples/ettoday.html', mobile=False)
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('客運司機車禍致人於死　心情鬱悶陽台以狗鍊上吊', nsoup.title())
        self.assertEqual('2017-12-09 00:26:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('林悅', nsoup.author())
        self.assertIn('台南市永康區永安路住處後陽台上吊', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('快訊／整日沒出房門！三重無業男半夜住處2樓上吊　母開門才發現', nsoup.title())
        self.assertEqual('2018-10-20 04:11:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('趙永博', nsoup.author())
        self.assertIn('新北市三重區三和路三段101巷一處民宅2樓', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('快訊／整日沒出房門！三重無業男半夜住處2樓上吊　母開門才發現', nsoup.title())
        self.assertEqual('2018-10-20 04:11:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('趙永博', nsoup.author())
        self.assertIn('新北市三重區三和路三段101巷一處民宅2樓', nsoup.contents())
