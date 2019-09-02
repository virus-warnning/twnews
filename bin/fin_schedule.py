import os
import schedule
import signal
import sys
import threading
import time
from datetime import datetime

sys.path.append(os.path.realpath('.'))

import busm
import twnews.finance.tpex as tpex

# @busm.through_telegram
def job(label):
    # tpex.sync_dataset('institution', '2019-09-02')
    print('shit')
    wkd = datetime.now().isoweekday()
    if wkd > 5:
        return
    timestr = datetime.now().strftime('%H:%M:%S.%f')
    print('[%s] job(%s)' % (timestr, label))

def daemon():
    # 觸發排程條件時，平行執行工作，避免超時導致下一個工作被忽略
    def run_threaded(job_func, *args):
        th = threading.Thread(target=job_func, args=args)
        th.start()

    def on_quit(signum, frame):
        nonlocal close_requested
        close_requested = True

    # 產生 pid file
    pid_file = os.path.expanduser('~/.twnews/fin_schedule.pid')
    pid_base = os.path.dirname(pid_file)
    if not os.path.isdir(pid_base):
        os.makedirs(pid_base)
    with open(pid_file, 'w') as pid_stream:
        pid_stream.write('%s' % os.getpid())

    # kill process 時溫和結束
    close_requested = False
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, on_quit)

    # schedule.every().day.at('16:52').do(job, 'Test')

    # 證交所
    schedule.every().day.at('00:30').do(job, '模擬證交所可借券')
    schedule.every().day.at('08:00').do(job, '模擬證交所ETF淨值')
    schedule.every().day.at('08:47').do(job, '模擬證交所三大法人')
    schedule.every().day.at('09:37').do(job, '模擬證交所鉅額交易')
    schedule.every().day.at('12:44').do(job, '模擬證交所信用交易')
    schedule.every().day.at('12:45').do(job, '模擬證交所借券賣出')

    # 櫃買中心
    schedule.every().day.at('18:04').do(run_threaded, tpex.sync_dataset, 'institution', '2019-09-02')
    schedule.every().day.at('09:58').do(job, '模擬櫃買鉅額交易')
    schedule.every().day.at('12:49').do(job, '模擬櫃買信用交易')

    # 集保中心
    schedule.every().day.at('23:00').do(job, '模擬集保股權分散')

    # 偵測與執行排程
    while not close_requested:
        schedule.run_pending()

        # 控制下次醒來的時，秒數小數部位趨近於 0
        t = time.time()
        delay = 1 - (t - int(t))
        time.sleep(delay)

    # 移除 pid file
    os.remove(pid_file)

if __name__ == '__main__':
    if os.fork() == 0:
        daemon()
