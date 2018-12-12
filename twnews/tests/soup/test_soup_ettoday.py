"""
東森新聞雲分解測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

class TestEttoday(unittest.TestCase):

    def setUp(self):
        self.dtf = '%Y-%m-%d %H:%M:%S'

    def test_01_sample(self):
        """
        測試東森新聞雲樣本
        """
        pkgdir = twnews.common.get_package_dir()
        nsoup = NewsSoup(pkgdir + '/samples/ettoday.html.gz')
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('客運司機車禍致人於死　心情鬱悶陽台以狗鍊上吊', nsoup.title())
        self.assertEqual('2017-12-09 00:26:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('林悅', nsoup.author())
        self.assertIn('台南市永康區永安路住處後陽台上吊', nsoup.contents())

    def test_02_mobile(self):
        """
        測試東森新聞雲
        """
        url = 'https://www.ettoday.net/news/20181020/1285826.htm'
        nsoup = NewsSoup(url, refresh=True, proxy_first=True)
        self.assertEqual('ettoday', nsoup.channel)
        self.assertIn('快訊／整日沒出房門！三重無業男半夜住處2樓上吊　母開門才發現', nsoup.title())
        self.assertEqual('2018-10-20 04:11:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('趙永博', nsoup.author())
        self.assertIn('新北市三重區三和路三段101巷一處民宅2樓', nsoup.contents())

    def test_03_layouts(self):
        """
        測試東森新聞雲其他排版
        """
        layouts = [
            {
                'url': 'https://fashion.ettoday.net/news/1316942',
                'title': '漫長的冬日夜晚想閱讀　不妨參考誠品2018年度暢銷書單',
                'date': '2018-11-28 00:00:00',
                'author': '蔡惠如',
                'contents': '我輩中人：寫給中年人的情書'
            },
            {
                'url': 'https://game.ettoday.net/article/1315167.htm',
                'title': '網石與DC聯名合作　《蝙蝠俠》角色進駐《天堂2 革命》',
                'date': '2018-11-24 23:59:00',
                'author': None,
                'contents': '天堂2：革命'
            },
            {
                'url': 'https://health.ettoday.net/news/1317507',
                'title': '謝碧珠／沒有自費就醫資訊的健康存摺很空心',
                'date': '2018-11-28 12:50:00',
                'author': None,
                'contents': '全民健康保險法'
            },
            {
                'url': 'https://house.ettoday.net/news/1317619',
                'title': '台北、新北26.1％潛勢區　「市民生命安全」柯P、漢子準備好了嗎？',
                'date': '2018-11-28 11:16:00',
                'author': '陳韋帆',
                'contents': '其中「山腳斷層」更跨越了金山、三芝、淡水、五股、泰山、新莊及樹林等各區'
            },
            {
                'url': 'https://pets.ettoday.net/news/1307563',
                'title': '去睡覺囉！　傑克羅素㹴秒轉身「抱大狗娃娃」踏踏進房：晚安～',
                'date': '2018-11-16 14:50:00',
                'author': '陳靜',
                'contents': '每天晚上都一定要帶著它睡覺，有時候突然想到也會馬上衝進房間'
            },
            {
                'url': 'https://speed.ettoday.net/news/1316854',
                'title': '休旅車＆轎車誰安全？數據顯示這種車「死亡率低一半」',
                'date': '2018-11-27 00:00:00',
                'author': None,
                'contents': '發生各類車禍事故時，普通轎車乘客死亡率為39%，而SUV只有21%'
            },
            {
                'url': 'https://sports.ettoday.net/news/1317313',
                'title': '日職／丸佳浩MVP二連霸　山川穗高獲獎喊目標50轟',
                'date': '2018-11-27 21:10:00',
                'author': '楊舒帆',
                'contents': '今年繳出打擊率0.306、39轟、97分打點的成績'
            },
            {
                'url': 'https://star.ettoday.net/news/1308844',
                'title': 'KID半夜突襲女神房間！　驚見「浴衣脫落門外」他狂喜衝進去',
                'date': '2018-11-17 16:40:00',
                'author': '劉宜庭',
                'contents': 'KID親睹這一幕，更是興奮到整個人趴在地上'
            },
            {
                'url': 'https://travel.ettoday.net/article/1317664.htm',
                'title': '普羅旺斯花海、《鬼怪》蕎麥花！「全台5大花海」超醉心',
                'date': '2018-11-28 12:30:00',
                'author': None,
                'contents': '粉紅波斯菊、向日葵、百合、鼠尾草、貓尾花、麒麟菊、雞冠花、鳳仙花等陸續盛開'
            }
        ]
        for layout in layouts:
            nsoup = NewsSoup(layout['url'], refresh=True, proxy_first=True)
            self.assertEqual('ettoday', nsoup.channel)
            self.assertIn(layout['title'], nsoup.title())
            self.assertEqual(layout['date'], nsoup.date().strftime(self.dtf))
            self.assertEqual(layout['author'], nsoup.author())
            self.assertIn(layout['contents'], nsoup.contents())
