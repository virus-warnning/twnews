"""
聯合新聞網單元測試
"""

import unittest
from twnews.soup import NewsSoup

#@unittest.skip
class TestUdn(unittest.TestCase):

    def setUp(self):
        self.url = 'https://udn.com/news/story/7320/3407294'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試本地樣本解構
        * 如果測試 02 失敗，需要用 bin/getnews.sh 重新製作本地樣本
        """
        nsoup = NewsSoup('samples/udn.html', mobile=False)
        self.assertEqual('udn', nsoup.channel)
        self.assertIn('澎湖重度殘障男子 陳屍馬公水仙宮旁空屋', nsoup.title())
        self.assertEqual('2018-02-28 14:31:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('馬公水仙宮旁的一處廢棄破屋內', nsoup.contents())

    def test_02_desktop(self):
        """
        測試桌面版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=False)
        self.assertEqual('udn', nsoup.channel)
        self.assertIn('清晨起床發現父親上吊天花板 嚇壞女兒急報案', nsoup.title())
        self.assertEqual('2018-10-06 15:45:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('陳宏睿', nsoup.author())
        self.assertIn('台中市北區水源街', nsoup.contents())

    def test_03_mobile(self):
        """
        測試行動版網頁解構
        * 務必開啟強制更新，確保解構程式能跟進網站最新版本
        * 實際新聞內容有可能更新，需要同步單元測試的預期值
        """
        nsoup = NewsSoup(self.url, refresh=True, mobile=True)
        self.assertEqual('udn', nsoup.channel)
        self.assertIn('清晨起床發現父親上吊天花板 嚇壞女兒急報案', nsoup.title())
        self.assertEqual('2018-10-06 15:45:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('陳宏睿', nsoup.author())
        self.assertIn('台中市北區水源街', nsoup.contents())
