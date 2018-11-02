"""
自由時報單元測試
"""

import unittest
from twnews.soup import NewsSoup, pkgdir

#@unittest.skip
class TestLtn(unittest.TestCase):

    def setUp(self):
        self.url = 'http://news.ltn.com.tw/news/society/breakingnews/2581807'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup(pkgdir + '/samples/ltn.html.gz', mobile=False)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('10年前父親掐死兒後自縊... 凶宅下月拍開價425萬', nsoup.title())
        self.assertEqual('2018-07-31 08:19:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('台北市萬華區萬大路一帶公寓的蘇姓男子', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('疑因病厭世 男子國小圖書館上吊身亡', nsoup.title())
        self.assertEqual('2018-10-15 23:51:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('台北市萬華區的老松國小今（15）日早上驚傳上吊輕生事件', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('疑因病厭世 男子國小圖書館上吊身亡', nsoup.title())
        self.assertEqual('2018-10-15 23:51:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('台北市萬華區的老松國小今（15）日早上驚傳上吊輕生事件', nsoup.contents())
