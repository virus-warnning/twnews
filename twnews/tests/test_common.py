"""
分解程式共用單元測試

為了節省爬蟲開發時間，原則上 NewsSoup 盡量不丟例外，有問題以 logging 機制為主
"""

import os
import re
import unittest
from twnews.soup import *

class TestCommon(unittest.TestCase):

    def setUp(self):
        self.url = 'https://tw.appledaily.com/headline/daily/20181201/38194705/'
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_cache(self):
        """
        測試快取機制
        """

        # 清除快取
        cache_dir = get_cache_dir()
        cache_path = '{}/appledaily-ed33e11740a7c95cb0852827b91cd37d.html.gz'.format(cache_dir)
        if os.path.isfile(cache_path):
            os.unlink(cache_path)

        # 讀取新聞，計算快取檔案數
        NewsSoup(self.url).title()
        has_cache = os.path.isfile(cache_path)
        self.assertTrue(has_cache)

        # 再次讀取新聞，確認快取檔的 mtime 沒變
        if has_cache:
            news_mtime_old = os.path.getmtime(cache_path)
            NewsSoup(self.url).title()
            news_mtime_new = os.path.getmtime(cache_path)
            self.assertEqual(news_mtime_old, news_mtime_new)

    def test_02_soup_from_website(self):
        '''
        測試 NewSoup(URL) 輸入不理想網址
        '''

        # channel 不存在
        try:
            nsoup = NewsSoup('https://localhost.xxx')
            self.assertIsNone(nsoup.title(), 'channel 錯誤時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), 'channel 錯誤時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), 'channel 錯誤時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), 'channel 錯誤時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), 'channel 錯誤時，effective_text_rate() 應該回傳 0')
        except Exception:
            self.fail('channel 錯誤時，__init__() 不應該發生例外')

        # channel 正確但 host 漏字
        try:
            nsoup = NewsSoup('https://appledaily.co')
            self.assertIsNone(nsoup.title(), 'host 錯誤時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), 'host 錯誤時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), 'host 錯誤時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), 'host 錯誤時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), 'host 錯誤時，effective_text_rate() 應該回傳 0')
        except Exception:
            self.fail('host 錯誤時，__init__() 不應該發生例外')

        # host 正確但 url 漏字
        try:
            url = 'https://tw.news.appledaily.com/local/realtime/WRONG/NEWS_ID'
            nsoup = NewsSoup(url)
            self.assertIsNone(nsoup.title(), 'url 錯誤時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), 'url 錯誤時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), 'url 錯誤時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), 'url 錯誤時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), '頻道錯誤時，effective_text_rate() 應該回傳 0')
        except Exception:
            self.fail('url 錯誤時，__init__() 不應該發生例外')

    def test_03_soup_from_file(self):
        '''
        測試 NewsSoup(FILE) 輸入不理想檔案
        '''

        # channel 不存在
        try:
            nsoup = NewsSoup('/tmp/badchannel.html')
            self.assertIsNone(nsoup.title(), 'channel 錯誤時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), 'channel 錯誤時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), 'channel 錯誤時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), 'channel 錯誤時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), 'channel 錯誤時，effective_text_rate() 應該回傳 0')
        except Exception:
            self.fail('channel 錯誤時，__init__() 不應該發生例外')

        # 檔案不存在
        try:
            nsoup = NewsSoup('/tmp/appledaily-notexisted.html')
            self.assertIsNone(nsoup.title(), '檔案不存在時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), '檔案不存在時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), '檔案不存在時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), '檔案不存在時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), '檔案不存在時，effective_text_rate() 應該回傳 0')
        except Exception:
            self.fail('檔案不存在時，__init__() 不應該發生例外')

        # 空白檔案
        try:
            open('appledaily-empty.html', 'a').close()
            nsoup = NewsSoup('appledaily-empty.html')
            self.assertIsNone(nsoup.title(), '空白檔案時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), '空白檔案時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), '空白檔案時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), '空白檔案時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), '檔案不存在時，effective_text_rate() 應該回傳 0')
            os.unlink('appledaily-empty.html')
        except Exception:
            self.fail('空白檔案時，__init__() 不應該發生例外')

        # 空白 gz 檔案
        try:
            open('appledaily-empty.html.gz', 'a').close()
            nsoup = NewsSoup('appledaily-empty.html')
            self.assertIsNone(nsoup.soup)
            self.assertIsNone(nsoup.title(), '空白檔案時，title() 應該回傳 None')
            self.assertIsNone(nsoup.date(), '空白檔案時，date() 應該回傳 None')
            self.assertIsNone(nsoup.author(), '空白檔案時，author() 應該回傳 None')
            self.assertIsNone(nsoup.contents(), '空白檔案時，contents() 應該回傳 None')
            self.assertEqual(0, nsoup.effective_text_rate(), '檔案不存在時，effective_text_rate() 應該回傳 0')
            os.unlink('appledaily-empty.html.gz')
        except Exception:
            self.fail('空白檔案時，__init__() 不應該發生例外')

    def test_04_author_in_contents(self):
        """
        測試無記者欄的記者姓名分析 (蘋果、中央社、東森、自由、三立)
        """

        good_samples = [
            # 蘋果
            '(王覺一／台北報導)',
            '（林文彬／綜合外電報導）',
            # 中央社
            '（中央社記者吳睿騏桃園5日電）',
            '（中央社記者黃國芳嘉義縣17日電）',
            '（中央社東京5日綜合外電報導）日本軟銀（譯者：何宏儒/核稿：劉學源）',
            # 東森
            '記者吳奕靖／高雄報導',
            # 自由
            '〔記者梁偉銘／台北報導〕',
            '［記者江志雄／宜蘭報導］',
            # 三立
            '記者於慶璇／台中報導'
        ]

        bad_samples = [
            # 蘋果
            '（國際中心／綜合外電報導）',
            # 中央社
            '（中央社伊斯坦堡/日內瓦5日綜合外電報導）',
            # 東森
            '地方中心／嘉義報導',
            # 自由
            '〔即時新聞／綜合報導〕',
            # 三立
            '社會中心／綜合報導',
            # 腦補
            '（地方中心／綜合報導）',
            '（社會中心／綜合報導）',
            '〔地方中心／綜合報導〕',
            '〔社會中心／綜合報導〕',
        ]

        for text in good_samples:
            author = scan_author(text)
            msg = '"{}" 應該分析出記者姓名'.format(text)
            self.assertIsNotNone(author, msg)

        for text in bad_samples:
            author = scan_author(text)
            msg = '"{}" 不應分析出記者姓名'.format(text)
            self.assertIsNone(author, msg)

    def test_05_author_in_node(self):
        """
        測試有記者欄的記者姓名分析 (中時、聯合)
        """

        # 中時找不到異常案例，暫不測試
        bad_samples = [
          # 中央社 高雄6日電 (無連結)
          'https://udn.com/news/story/10958/3465283',
          # 聯合新聞網 綜合報導 (無連結)
          'https://udn.com/news/story/10958/3465161'
        ]

        for url in bad_samples:
            nsoup = NewsSoup(url)
            author = nsoup.author()
            msg = '"{}" 不應分析出記者姓名'.format(url)
            self.assertIsNone(author, msg)
