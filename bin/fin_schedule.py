import os
import schedule
import signal
import sys
import threading
import time
from datetime import datetime, timedelta

sys.path.append(os.path.realpath('.'))

import busm
import twnews.finance.twse as twse
import twnews.finance.tpex as tpex
import twnews.finance.tdcc as tdcc

def run_threaded(task):
    # 觸發排程條件時，平行執行工作，避免超時導致下一個工作被忽略
    print('Run task %s' % task)
    trading_date = datetime.now().strftime('%Y-%m-%d')
    (inst, action) = task.split(':')

    if inst == 'twse':
        func = twse.sync_dataset
        args = (action, trading_date)
    elif inst == 'tpex':
        func = tpex.sync_dataset
        args = (action, trading_date)
    elif inst == 'tdcc':
        func = tdcc.sync_dataset
        args = ()
    else:
        func = None
        args = ()

    if func is not None:
        th = threading.Thread(target=func, args=args)
        th.start()

def daemon():
    # 產生 pid file
    pid_file = os.path.expanduser('~/.twnews/fin_schedule.pid')
    pid_base = os.path.dirname(pid_file)
    if not os.path.isdir(pid_base):
        os.makedirs(pid_base)
    with open(pid_file, 'w') as pid_stream:
        pid_stream.write('%s' % os.getpid())

    # kill process 時安全結束
    close_requested = False

    def on_quit(signum, frame):
        nonlocal close_requested
        close_requested = True

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, on_quit)

    dt = datetime.now() + timedelta(minutes=1)
    sch_time = dt.strftime('%H:%M')

    # 證交所 - OK!
    # schedule.every().day.at(sch_time).do(run_threaded, 'twse:borrowed')
    # schedule.every().day.at(sch_time).do(run_threaded, 'twse:etfnet')
    # schedule.every().day.at(sch_time).do(run_threaded, 'twse:institution')
    # schedule.every().day.at(sch_time).do(run_threaded, 'twse:block')
    # schedule.every().day.at(sch_time).do(run_threaded, 'twse:margin')
    # schedule.every().day.at(sch_time).do(run_threaded, 'twse:selled')

    # 櫃買中心 - OK!
    # schedule.every().day.at(sch_time).do(run_threaded, 'tpex:institution')
    # schedule.every().day.at(sch_time).do(run_threaded, 'tpex:block')
    # schedule.every().day.at(sch_time).do(run_threaded, 'tpex:margin')

    # 集保中心
    schedule.every().day.at(sch_time).do(run_threaded, 'tdcc:')

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
    # if os.fork() == 0:
    daemon()
