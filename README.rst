台灣新聞拆拆樂 (twnews) 用來分解台灣各大新聞網站，取出重要的純文字內容

功能特色
========
- 預設使用行動版網頁降低流量
- 首次載入後會存入快取，避免同一網頁重複下載
- 利用 BeautifulSoup 的 select() 方式搭配設定檔分解，利於跟進網站改版

安裝
==========
.. code:: bash

  pip3 install twnews

範例
==========
.. code:: python

  from twnews.soup import NewsSoup

  nsoup = NewsSoup('https://tw.news.appledaily.com/local/realtime/20181025/1453825')
  print('頻道: {}'.format(nsoup.channel))
  print('標題: {}'.format(nsoup.title()))
  print('日期: {}'.format(nsoup.date().isoformat()))
  print('記者: {}'.format(nsoup.author()))
  print('內文:')
  print(nsoup.contents())

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
----------------------

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
