"""
自由時報單元分解測試
"""

import unittest
import twnews.common
from twnews.soup import NewsSoup

#@unittest.skip
class TestLtn(unittest.TestCase):

    def setUp(self):
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

    def test_02_mobile(self):
        """
        測試自由時報行動版
        """
        url = 'http://news.ltn.com.tw/news/society/breakingnews/2581807'
        nsoup = NewsSoup(url, refresh=True)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('疑因病厭世 男子國小圖書館上吊身亡', nsoup.title())
        self.assertEqual('2018-10-15 23:51:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('台北市萬華區的老松國小今（15）日早上驚傳上吊輕生事件', nsoup.contents())

    def test_03_layouts(self):
        """
        測試自由時報其他排版
        """
        layouts = [
            # TODO: 改善作者精準度
            {
                'url': 'http://3c.ltn.com.tw/m/news/35179',
                'title': 'iPhone XR 開箱體驗（三）！相機對比 iPhone XS、Google Pixel 3',
                'date': '2018-11-28 14:08:00',
                'author': '黃敬淳',
                'contents': '曝光控制也是 XR 相比 iPhone 8 Plus 的主要升級點'
            },
            # TODO: 改善日期精準度
            {
                'url': 'http://auto.ltn.com.tw/m/news/11334/3',
                'title': '瞄準 Toyota Auris，大改款 Mazda 3 洛杉磯車展正式亮相！（內有相片集）',
                'date': None,
                'author': '徐煜展',
                'contents': '其中新造型的 LED 尾燈組也與先前公佈的 Kai Concept 概念車相仿'
            },
            {
                'url': 'http://ec.ltn.com.tw/m/article/breakingnews/2626720',
                'title': '童子賢：不要幻想東南亞是下1個中國 中國模式難複製到其他國',
                'date': '2018-11-28 12:40:03',
                'author': '卓怡君',
                'contents': '過去20年中國在台商和全球外商打造出製造業的基礎建設'
            },
            {
                'url': 'http://ent.ltn.com.tw/m/news/breakingnews/2626753',
                'title': '藍文青獨賠近5千萬 自稱 「韓國瑜鑾生兄弟」',
                'date': '2018-11-28 13:05:00',
                'author': '蕭宇涵',
                'contents': '但吳易展以旗下公司美仕特牛排公司才剛起步'
            },
            {
                'url': 'http://estate.ltn.com.tw/article/6493',
                'title': '台南新吉工業區地上權招租 提供優惠方案',
                'date': '2018-11-26 18:27:00',
                'author': '林耀文',
                'contents': '台南市新吉工業區位於臺南市安南區、安定區交界處招商也頗為亮麗'
            },
            {
                'url': 'http://food.ltn.com.tw/m/article/8263',
                'title': '菠菜影響鈣吸收？吃多了會結石？別再相信謠言了！',
                'date': '2018-11-28 00:00:00',
                'author': None,
                'contents': '坊間常有說法認為菠菜中大量的「草酸」會阻礙鈣質吸收、影響幼兒生長'
            },
            # TODO: 改善日期精準度
            {
                'url': 'http://istyle.ltn.com.tw/m/article/9168',
                'title': '明星瘋這咖》張鈞甯、陳庭妮私下都揹小包！「小叮噹大袋」暫退...',
                'date': None,
                'author': '余崇慧',
                'contents': '一頭復古味十足的劉海，帶著六、七零年代阿哥哥風格'
            },
            {
                'url': 'http://market.ltn.com.tw/m/article/5159',
                'title': '2018台北國際旅展  推動原住民族文化',
                'date': '2018-11-27 11:31:00',
                'author': None,
                'contents': '台北國際旅展設置形象館，推出全台36個部落的精彩遊程'
            },
            {
                'url': 'http://playing.ltn.com.tw/m/article/11191',
                'title': '北高韓粉吃雞排囉！3千份雞排賀韓國瑜當選，今起發送到週末',
                'date': '2018-11-28 00:00:00',
                'author': None,
                'contents': '網友打趣地解釋，原先說是900份。後來加碼至1000份'
            },
            {
                'url': 'http://sports.ltn.com.tw/m/news/breakingnews/2626821',
                'title': 'MLB》王牌陣解體在即？印地安人傳更想出售鮑爾',
                'date': '2018-11-28 14:21:00',
                'author': None,
                'contents': '鮑爾目前只剩兩年控制權，而他今年有望靠著優異表現在薪資上大幅躍進'
            },
            {
                'url': 'http://talk.ltn.com.tw/article/breakingnews/2625348',
                'title': '胡，怎麼說》正負8％造成政治雪崩效應',
                'date': '2018-11-27 09:43:00',
                'author': '胡文輝',
                'contents': '2016年總統及立委選舉，民進黨才連下兩城，總統選舉得票率以56.12%狂勝國民黨的31.04%'
            }
        ]
        for layout in layouts:
            nsoup = NewsSoup(layout['url'], refresh=True, proxy_first=True)
            self.assertEqual('ltn', nsoup.channel)
            self.assertIn(layout['title'], nsoup.title())
            if nsoup.date() is not None:
                self.assertEqual(layout['date'], nsoup.date().strftime(self.dtf))
            else:
                self.assertEqual(layout['date'], nsoup.date())
            self.assertEqual(layout['author'], nsoup.author())
            self.assertIn(layout['contents'], nsoup.contents())

    def test_04_switch_mobile(self):
        """
        測試自動切換行動版
        """
        url = 'http://sports.ltn.com.tw/news/breakingnews/2626821'
        nsoup = NewsSoup(url, refresh=True)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('MLB》王牌陣解體在即？印地安人傳更想出售鮑爾', nsoup.title())
        self.assertEqual('2018-11-28 14:21:00', nsoup.date().strftime(self.dtf))
        self.assertEqual(None, nsoup.author())
        self.assertIn('鮑爾目前只剩兩年控制權，而他今年有望靠著優異表現在薪資上大幅躍進', nsoup.contents())

    def test_05_multiple_date_format(self):
        """
        測試多重日期格式
        """
        url = 'https://m.ltn.com.tw/news/politics/paper/1249335'
        nsoup = NewsSoup(url, refresh=True)
        self.assertEqual('ltn', nsoup.channel)
        self.assertIn('狂拿15席 吳總教頭首戰告捷', nsoup.title())
        self.assertEqual('2018-11-25 00:00:00', nsoup.date().strftime(self.dtf))
        self.assertEqual('施曉光', nsoup.author())
        self.assertIn('由黨魁吳敦義扮演「總教頭」並宣稱要擊出二十二支全壘打的國民黨', nsoup.contents())
