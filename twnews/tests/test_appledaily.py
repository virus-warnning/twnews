"""
蘋果日報單元測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestAppleDaily(unittest.TestCase):

    def setUp(self):
        self.url = 'https://tw.news.appledaily.com/local/realtime/20181025/1453825'
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

    def test_03_mobile(self):
        """
        測試蘋果日報行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('appledaily', nsoup.channel)
        self.assertIn('男子疑久病厭世　學校圍牆上吊輕生亡', nsoup.title())
        self.assertEqual('2018-10-25 12:03:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('江宏倫', nsoup.author())
        self.assertIn('台北市北投區西安街二段', nsoup.contents())
