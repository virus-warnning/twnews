"""
蘋果日報單元測試
"""

import unittest
from twnews.soup import NewsSoup, pkgdir

#@unittest.skip
class TestAppleDaily(unittest.TestCase):

    def setUp(self):
        self.url = 'https://tw.news.appledaily.com/local/realtime/20181025/1453825'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup(pkgdir + '/samples/appledaily.html.gz', mobile=False)
        self.assertEqual('appledaily', nsoup.channel)
        self.assertIn('和男友口角鎖門吞藥　女墜樓不治', nsoup.title())
        self.assertEqual('2016-05-21 11:44:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('王煌忠', nsoup.author())
        self.assertIn('文心路的一棟住宅大樓', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('appledaily', nsoup.channel)
        self.assertIn('男子疑久病厭世　學校圍牆上吊輕生亡', nsoup.title())
        self.assertEqual('2018-10-25 12:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('江宏倫', nsoup.author())
        self.assertIn('台北市北投區西安街二段', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('appledaily', nsoup.channel)
        self.assertIn('男子疑久病厭世　學校圍牆上吊輕生亡', nsoup.title())
        self.assertEqual('2018-10-25 12:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('江宏倫', nsoup.author())
        self.assertIn('台北市北投區西安街二段', nsoup.contents())
