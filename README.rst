用來分解台灣各大新聞網站，取出重要的純文字內容

功能特色
========
- 預設使用行動版網頁降低流量
- 首次載入後會存入快取，避免同一網頁重複下載
- 利用 BeautifulSoup 的 select() 方式搭配設定檔分解，利於跟進網站改版

安裝
==========
.. code:: bash

  pip3 install twnews

參考手冊
=========

class NewsSoup
----------------------

WorkerDispatcher.__init__(worker_count=0, use_core=0, time_limit=0)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a dispatcher instace.

worker_count
  How many threads would be created, 0 means to create (use_core * 2) threads.
use_core
  How many cores would be use, 0 means all cores.
time_limit
  Stop workers after given seconds. Running functions still run at that moment.
  Queued functions would be cancled.

WorkerDispatcher.dispatch(func, args)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Dispatch a function to one of workers randomly.

func
  Function to call.
args
  Argument list of this function.

WorkerDispatcher.sleep(seconds)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sleep dispatcher for given seconds.

seconds
  Seconds to sleep. Dispatcher would not sleep given seconds actually.
  It sleep many times during given seconds, so that system signal (e.g. Ctrl+C) can be handled.

WorkerDispatcher.join()
^^^^^^^^^^^^^^^^^^^^^^^

Wait until all workers stopped.

WorkerDispatcher.is_alive()
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Check if the dispatcher is alive.
