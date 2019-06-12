台灣新聞拆拆樂 (twnews) 用來分解台灣各大新聞網站，取出重要的純文字內容

功能
====

- 支援蘋果日報、中時電子報、中央社、東森新聞雲、自由時報、三立新聞網、聯合新聞網
- 使用行動版網頁與快取機制節省流量
- 盡可能找出記者姓名
- 利用 BeautifulSoup 的 CSS selector 功能搭配設定檔分解，容易同步網站改版
- 解決 Python for Windows CP950 編碼問題，節省處理鳥事的時間
- 每週執行自動化測試檢查分解程式的時效性

0.3.2 新功能

- 更新東森新聞爬蟲設定
- 解決自由地產、自由時尚因 lxml 版本太舊而拆失敗的問題
- 新增證交所資料蒐集程式 (三大法人、信用交易、借券賣出、鉅額交易、ETF淨值溢價率)
- 改善集保中心資料蒐集程式 (股權分散表)

0.3.1 新功能

- 跟進中時電子報的排版變更
- 支援蘋果地產
- 股權分散表資料表結構改善
- 股權分散表資料表日期改為 ISO 格式

0.3.0 新功能

- 股權分散表 CSV 檔蒐集程式
- 修正自由時報娛樂新聞分解問題 `#50 <https://github.com/virus-warnning/twnews/issues/50>`_ (回報者: `CpOuyang <https://github.com/CpOuyang>`_)

0.2.4 新功能

- 改善記者姓名辨識能力
- 自由時報分類新聞自動切換手機版
- 修正自由時報部分新聞無法取得日期問題
- 修正中國時報部分新聞無法取得記者問題
- 修正蘋果日報搜尋功能自動翻頁問題
- 增加測試項目

安裝
====

.. code:: bash

  pip3 install twnews

工具程式
========

.. code:: bash

  # 拆新聞
  python3 -m twnews soup https://tw.news.appledaily.com/local/realtime/20181025/1453825

  # 搜尋
  python3 -m twnews search 韓國瑜 udn

  # 搜尋 + 拆
  python3 -m twnews snsp 酒駕

  # 統計關鍵字出現在標題的次數
  python3 -m twnews cpkw 柯文哲

  # 查看用法
  python3 -m twnews help

範例 - 分解新聞
===============

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

  警消表示，抵達現場時，發現游男坐在某國中圍牆邊上吊輕生，立即將他救下，但已無呼吸心跳，立即進行CPR並送醫搶救，家屬接獲通知趕抵醫院，同意放棄急救。警方調查，年約80多歲的游男，疑似因長期洗腎又患有心臟疾病、糖尿病才會想不開，現場並無打鬥痕跡，初步已排除外力介入，詳細輕生原因仍待調查釐清。（突發中心江宏倫／台北報導）《蘋果》關心你自殺解決不了問題，卻留給家人無比悲痛。請珍惜生命。再給自己一次機會自殺防治諮詢安心專線：0800-788995（24小時） 生命線協談專線：1995 張老師專線：1980出版時間02：07更新時間12：03


  >>加入蘋果日報粉絲團94即時94狂！
  有效內容率: 1.37%

範例 - 關鍵字搜尋 + 分解新聞
============================

.. code:: python

  from twnews.search import NewsSearch

  nsearch = NewsSearch(
    'ltn',
    limit=10,
    beg_date='2018-08-03', # 自由時報的日期範圍只能在 90 天以內
    end_date='2018-11-01'
  )
  nsoups = nsearch.by_keyword('上吊', title_only=True).to_soup_list()

  for (i, nsoup) in enumerate(nsoups):
      print('{:03d}: {}'.format(i, nsoup.path))
      if nsoup.title() is not None:
          print('     記者: {} / 日期: {}'.format(nsoup.author(), nsoup.date()))
          print('     標題: {}'.format(nsoup.title()))
          print('     {} ...'.format(nsoup.contents()[0:30]))
      else:
          print('     新聞分解失敗，無法識別 DOM 結構')

.. code:: text

  000: http://m.ltn.com.tw/news/society/breakingnews/2581807
       記者: None / 日期: 2018-10-15 23:51:00
       標題: 疑因病厭世 男子國小圖書館上吊身亡
       〔即時新聞／綜合報導〕台北市萬華區的老松國小今（15）日早上 ...
  001: http://m.ltn.com.tw/news/society/breakingnews/2579780
       記者: None / 日期: 2018-10-13 16:52:00
       標題: 汐止五指山驚傳男子上吊 水管繞頸陳屍樹林
       〔記者林嘉東、吳昇儒／新北報導〕台北市郭姓男子今天午後被發現 ...
  002: http://m.ltn.com.tw/news/entertainment/breakingnews/2579590
       新聞分解失敗，無法識別 DOM 結構
  003: http://m.ltn.com.tw/news/society/breakingnews/2577987
       記者: 謝武雄 / 日期: 2018-10-11 18:10:00
       標題: 議員尿急樹林解放赫見白骨 男子上吊這天正好滿七...
       ［記者謝武雄／桃園報導］桃園市大園選區市議員游吾和昨天在臉書 ...
  004: http://m.ltn.com.tw/news/entertainment/breakingnews/2577596
       新聞分解失敗，無法識別 DOM 結構
  005: http://m.ltn.com.tw/news/society/breakingnews/2570595
       記者: 吳仁捷 / 日期: 2018-10-04 13:40:00
       標題: 疑借貸千萬翻身失敗 公墓上吊嚇壞爬山男
       〔記者吳仁捷／新北報導〕章姓男子今天上午到新北市樹林大同山區 ...
  006: http://m.ltn.com.tw/news/entertainment/breakingnews/2567740
       新聞分解失敗，無法識別 DOM 結構
  007: http://m.ltn.com.tw/news/life/breakingnews/2567637
       記者: None / 日期: 2018-10-01 23:35:00
       標題: 「肉粽」難送！ 員林三合院連5人在「同條樑」上吊
       〔即時新聞／綜合報導〕在彰化沿海一帶，為上吊身亡者「送肉棕」 ...
  008: http://m.ltn.com.tw/news/society/breakingnews/2561962
       記者: None / 日期: 2018-09-26 11:08:00
       標題: 男子北美館樹林上吊亡 警到場調查
       〔即時新聞／綜合報導〕今天上午10時許，台北市立美術館停車場 ...
  009: http://m.ltn.com.tw/news/society/breakingnews/2561566
       記者: 黃良傑 / 日期: 2018-09-25 18:05:00
       標題: 美籍女師上吊租屋處身亡 美籍男友：房內發現遺書
       〔記者黃良傑／高雄報導〕一名美籍女老師今午被男友發現陳屍租屋 ...
