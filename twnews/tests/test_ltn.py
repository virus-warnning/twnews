"""
自由時報單元測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestLtn(unittest.TestCase):

    def setUp(self):
        self.url = 'http://news.ltn.com.tw/news/society/breakingnews/2581807'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試自由時報樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/ltn.html.gz')
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('10年前父親掐死兒後自縊... 凶宅下月拍開價425萬', nsoup.title())
        self.assertEqual('2018-07-31 08:19:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('台北市萬華區萬大路一帶公寓的蘇姓男子', nsoup.contents())

    def test_03_mobile(self):
        """
        測試自由時報行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('疑因病厭世 男子國小圖書館上吊身亡', nsoup.title())
        self.assertEqual('2018-10-15 23:51:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('台北市萬華區的老松國小今（15）日早上驚傳上吊輕生事件', nsoup.contents())
