"""
蘋果日報分解測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestAppleDaily(unittest.TestCase):

    def setUp(self):
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試蘋果日報樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/appledaily.html.gz')
        self.assertEqual('appledaily', nsoup.channel)
        self.assertIn('和男友口角鎖門吞藥　女墜樓不治', nsoup.title())
        self.assertEqual('2016-05-21 11:44:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('王煌忠', nsoup.author())
        self.assertIn('文心路的一棟住宅大樓', nsoup.contents())

    def test_02_mobile(self):
        """
        測試蘋果日報行動版
        """
        url = 'https://tw.news.appledaily.com/local/realtime/20181025/1453825'
        nsoup = NewsSoup(url, refresh=True)
        self.assertEqual('appledaily', nsoup.channel)
        self.assertIn('男子疑久病厭世　學校圍牆上吊輕生亡', nsoup.title())
        self.assertEqual('2018-10-25 12:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('江宏倫', nsoup.author())
        self.assertIn('台北市北投區西安街二段', nsoup.contents())

    def test_03_layouts(self):
        """
        測試蘋果地產
        """
        layouts = [
            {
                'url': 'http://home.appledaily.com.tw/article/index/20190313/38279127',
                'title': '潮牌概念店撤離 東區房東陷定位危機',
                'date': '2019-03-13 00:00:00',
                'author': '唐家儀',
                'contents': '英國人氣潮牌Superdry（超級乾燥）位大安區忠孝東路四段的形象概念門市竟已歇業'
            }
        ]
        for layout in layouts:
            nsoup = NewsSoup(layout['url'], refresh=True, proxy_first=True)
            self.assertEqual('appledaily', nsoup.channel)
            self.assertIn(layout['title'], nsoup.title())
            if nsoup.date() is not None:
                self.assertEqual(layout['date'], nsoup.date().strftime(self.dtf))
            else:
                self.assertEqual(layout['date'], nsoup.date())
            self.assertEqual(layout['author'], nsoup.author())
            self.assertIn(layout['contents'], nsoup.contents())
