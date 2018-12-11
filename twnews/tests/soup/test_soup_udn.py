"""
聯合新聞網分解測試
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

    def test_02_mobile(self):
        """
        測試聯合新聞網行動版
        """
        nsoup = NewsSoup(self.url, refresh=True)
        self.assertEqual('udn', nsoup.channel)
        self.assertIn('清晨起床發現父親上吊天花板 嚇壞女兒急報案', nsoup.title())
        self.assertEqual('2018-10-06 15:45:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('陳宏睿', nsoup.author())
        self.assertIn('台中市北區水源街', nsoup.contents())

    def test_03_layouts(self):
        """
        測試聯合新聞網的其他排版
        """
        layouts = [
            {
                'url': 'https://autos.udn.com/autos/story/7826/3506163',
                'title': '2018洛杉磯車展／更洗鍊有型！全新第四代Mazda3發表前廠照先曝光',
                'date': '2018-11-28 11:35:11',
                'author': '張振群',
                'contents': 'Mazda汽車今年壓軸重頭戲全新第四代Mazda3，在正式發表前外觀定裝照率先曝光。'
            },
            {
                'url': 'https://game.udn.com/game/story/10449/3489517',
                'title': '《轉校生》新手生存指南 對戰？先活下來再說吧！',
                'date': '2018-11-19 17:14:00',
                'author': '老宅',
                'contents': '遊戲中兩大生產建設在教室下方的紙杯跟爐架，在這邊可以生產飲料跟食物'
            },
            {
                'url': 'https://global.udn.com/global_vision/story/8663/3502209',
                'title': '「二次公投」好不好？凌遲式的英國脫歐單行道',
                'date': '2018-11-26 00:00:00',
                'author': None,
                'contents': '廢除脫歐決定、舉行二次脫歐公投的聲量也越來越強'
            },
            {
                'url': 'https://health.udn.com/health/story/6037/3504950',
                'title': '喝奶茶不如單喝紅茶 日本紅茶協會：加牛奶會失去兩大功效',
                'date': '2018-11-28 00:41:00',
                'author': '廖思涵',
                'contents': '茶葉含有咖啡鹼、茶鹼、鞣酸、可可鹼、葉酸、維生素B群、C、P及少量的礦物質'
            },
            {
                'url': 'https://house.udn.com/house/story/5887/3506297',
                'title': '一戶19萬也沒人要！ 神才賣得掉的217戶又流標了',
                'date': '2018-11-28 12:26:17',
                'author': '游智文',
                'contents': '北海岸喜凱亞渡假村法拍屋，今（28）日進行第17次拍賣'
            },
            {
                'url': 'https://nba.udn.com/nba/story/6780/3506854',
                'title': '「鳥人」現身丹佛主場 期盼能重返NBA',
                'date': '2018-11-28 16:24:00',
                'author': '蔡佳霖',
                'contents': '今天現身丹佛主場，在中場時間擊鼓助威，和球迷進行互動'
            },
            {
                'url': 'https://opinion.udn.com/opinion/story/12067/3506294',
                'title': '從太陽花到韓流：未挑戰政經核心，只會出現鬼打牆的鐘擺效應',
                'date': None,
                'author': '陳柏謙',
                'contents': '九合一大選結果全面潰敗，縣市首長從選前13席崩盤到僅守住6席'
            },
            {
                'url': 'https://stars.udn.com/star/story/10090/3507027',
                'title': '自嘲和李進良「大餅跟鳥」 小禎妙答李婉鈺田欣誰戰力強',
                'date': '2018-11-28 17:11:00',
                'author': '梅衍儂',
                'contents': '很心疼小禎，願意把生活裡的體驗用演技來給大家看'
            },
            {
                'url': 'https://style.udn.com/style/story/8065/3500832',
                'title': '《我身後的陶斯》林世美長髮時浪漫感十足 但短髮的她更有看頭',
                'date': '2018-11-25 10:02:00',
                'author': '魏家娸',
                'contents': '第二女主角林世美在戲中深情愛著蘇志燮的情感也令人為之動容'
            }
        ]
        for layout in layouts:
            nsoup = NewsSoup(layout['url'], refresh=True, proxy_first=True)
            self.assertEqual('udn', nsoup.channel)
            self.assertIn(layout['title'], nsoup.title())
            if layout['date'] is not None:
                self.assertEqual(layout['date'], nsoup.date().strftime(self.dtf))
            else:
                self.assertEqual(layout['date'], None)
            self.assertEqual(layout['author'], nsoup.author())
            self.assertIn(layout['contents'], nsoup.contents())
