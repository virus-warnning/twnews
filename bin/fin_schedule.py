import asyncio
import math
import os
import schedule
import signal
import time
from datetime import datetime

def job():
    print('  job() run at %s' % datetime.now().strftime('%H:%M:%S'))

def daemon():
    # kill process 時溫和結束
    close_requested = False
    def on_term(signum, frame):
        nonlocal close_requested
        close_requested = True
    signal.signal(signal.SIGTERM, on_term)

    # 非同步值行排程工作
    async def async_run_pending():
        schedule.run_pending()

    # 證交所
    schedule.every().day.at('00:30').do(job)
    schedule.every().day.at('08:00').do(job)
    schedule.every().day.at('08:47').do(job)
    schedule.every().day.at('09:37').do(job)
    schedule.every().day.at('12:44').do(job)
    schedule.every().day.at('12:45').do(job)

    # 櫃買中心
    schedule.every().day.at('08:52').do(job)
    schedule.every().day.at('09:42').do(job)
    schedule.every().day.at('12:49').do(job)

    while not close_requested:
        print(datetime.now().strftime('[%H:%M:%S.%f] Wake up.'))
        asyncio.run(async_run_pending())

        # 控制下次醒來的時，秒數小數部位趨近於 0
        t = time.time()
        delay = 1 - (t - int(t))
        time.sleep(delay)

    # TODO: Remove pid file
    print('daemon(): kill pid %d' % os.getpid())

def main():
    pid = os.fork()
    if pid == 0:
        daemon()
    else:
        print('PID of daemon is %d.' % pid)
        with open('b.pid', 'w') as fpid:
            fpid.write('%s' % pid)

if __name__ == '__main__':
    main()
