"""
中時電子報單元測試
"""

import unittest
from twnews.soup import NewsSoup, pkgdir

#@unittest.skip
class TestChinatimes(unittest.TestCase):

    def setUp(self):
        self.url = 'https://www.chinatimes.com/realtimenews/20180916001767-260402'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup(pkgdir + '/samples/chinatimes.html.gz', mobile=False)
        self.assertEqual('chinatimes', nsoup.channel)
        self.assertIn('悲慟！北市士林年邁母子 住處上吊自殺身亡', nsoup.title())
        self.assertEqual('2018-09-16 15:31:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('謝明俊', nsoup.author())
        self.assertIn('北市士林區葫蘆街一處民宅', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('chinatimes', nsoup.channel)
        self.assertIn('悲慟！北市士林年邁母子 住處上吊自殺身亡', nsoup.title())
        self.assertEqual('2018-09-16 15:31:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('謝明俊', nsoup.author())
        self.assertIn('北市士林區葫蘆街一處民宅', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('chinatimes', nsoup.channel)
        self.assertIn('悲慟！北市士林年邁母子 住處上吊自殺身亡', nsoup.title())
        self.assertEqual('2018-09-16 15:31:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('謝明俊', nsoup.author())
        self.assertIn('北市士林區葫蘆街一處民宅', nsoup.contents())
