"""
聯合新聞網單元測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestUdn(unittest.TestCase):

    def setUp(self):
        self.url = 'https://udn.com/news/story/7320/3407294'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試聯合新聞網樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/udn.html.gz')
        self.assertEqual('udn', nsoup.channel)
        self.assertIn('澎湖重度殘障男子 陳屍馬公水仙宮旁空屋', nsoup.title())
        self.assertEqual('2018-02-28 14:31:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('馬公水仙宮旁的一處廢棄破屋內', nsoup.contents())

    def test_03_mobile(self):
        """
        測試聯合新聞網行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('udn', nsoup.channel)
        self.assertIn('清晨起床發現父親上吊天花板 嚇壞女兒急報案', nsoup.title())
        self.assertEqual('2018-10-06 15:45:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('陳宏睿', nsoup.author())
        self.assertIn('台中市北區水源街', nsoup.contents())
