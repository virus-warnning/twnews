台灣新聞拆拆樂 (twnews) 用來分解台灣各大新聞網站，取出重要的純文字內容

功能特色
========

- 支援蘋果日報、中央社、東森新聞雲、自由時報、三立新聞網、聯合新聞網
- 使用行動版網頁與快取機制節省流量
- 利用 BeautifulSoup 的 CSS selector 功能搭配設定檔分解，利於跟進網站改版

安裝
==========

.. code:: bash

  pip3 install twnews # 安裝
  python3 -m twnews   # 試一下

範例
==========

.. code:: python

  from twnews.soup import NewsSoup

  nsoup = NewsSoup('https://tw.news.appledaily.com/local/realtime/20181025/1453825')
  print('頻道: {}'.format(nsoup.channel))
  print('標題: {}'.format(nsoup.title()))
  print('日期: {}'.format(nsoup.date()))
  print('記者: {}'.format(nsoup.author()))
  print('內文:')
  print(nsoup.contents())
  print('有效內容率: {:.2f}%'.format(nsoup.effective_text_rate() * 100))

.. code:: text

  頻道: appledaily
  標題: 男子疑久病厭世　學校圍牆上吊輕生亡│即時新聞│20181025│蘋果日報
  日期: 2018-10-25 12:03:00
  記者: 江宏倫
  內文:
  台北市北投區西安街二段，昨晚10時許，1名游姓男子（約80歲）坐在學校圍牆邊上吊輕生，路過民眾驚見嚇得趕緊報案，警消趕抵，時發現輕生男子已經沒有生命跡象，緊急送醫搶救仍宣告不治，警方初步調查排除外力介入，輕生原因仍有待釐清。

  警消表示，抵達現場時，發現游男坐在某國中圍牆邊上吊輕生，立即將他救下，但已無呼吸心跳，立即進行CPR並送醫搶救，家屬接獲通知趕抵醫院，同意放棄急救。警方調查，年約80多歲的游男，疑似因長期洗腎又患有心臟疾病、糖尿病才會想不開，現場並無打鬥痕跡，初步已排除外力介入，詳細輕生原因仍待調查釐清。（突發中心江宏倫／台北報導）《蘋果》關心你自殺解決不了問題，卻留給家人無比悲痛。請珍惜生命。再給自己一次機會自殺防治諮詢安心專線：0800-788995（24小時） 生命線協談專線：1995 張老師專線：1980出版時間02：07更新時間12：03


  >>加入蘋果日報粉絲團94即時94狂！
  有效內容率: 1.37%

卡關了
=========

如果新聞無法正確分解可能是網站改版了，利用 green 跑一下單元測試看看
假如單元測試失敗了，表示需要更新套件囉

.. code:: bash

  pip3 install green      # 安裝 green 套件
  green -vvv twnews.tests # 使用 green 套件跑單元測試
  pip3 install -U twnews  # 更新 twnews

參考手冊
=========

class twnews.soup.NewsSoup
--------------------------

NewsSoup.__init__(path, refresh=False, mobile=True)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
建立新聞分解器

path
  本機檔案路徑或是網址
refresh
  使用網址時，是否要重新整理而不使用既有快取
mobile
  是否使用行動版網頁

NewsSoup.title()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

取得新聞標題

NewsSoup.date()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

取得發佈日期

NewsSoup.author()
^^^^^^^^^^^^^^^^^^^^^^^

取得記者姓名

NewsSoup.contents()
^^^^^^^^^^^^^^^^^^^^^^^^^^^

取得新聞內文

NewsSoup.effective_text_rate()
^^^^^^^^^^^^^^^^^^^^^^^^^^^

取得有效內容率
