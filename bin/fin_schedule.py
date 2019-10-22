import logging
import os
import schedule
import signal
import sys
import threading
import time
from datetime import datetime, timedelta

sys.path.append(os.path.realpath('.'))

import twnews.common as cm
import twnews.finance.twse as twse
import twnews.finance.tpex as tpex
import twnews.finance.tdcc as tdcc

class JustDaemon:
    """
    定型化 Daemon
    TODO: 分割成獨立套件
    """

    def __init__(self, init_task=None, loop_task=None, stdout='/dev/null', stderr='/dev/null', background=True):
        if background and os.fork() > 0:
            exit(0)

        self.init_task = init_task if init_task is not None else self.do_nothing
        self.loop_task = loop_task if loop_task is not None else self.do_nothing
        self.stdout = stdout
        self.stderr = stderr
        self.background = background
        self.close_requested = False

    def do_nothing(self):
        pass

    def on_quit(self, signum, frame):
        self.close_requested = True

    def listen_sys_signals(self):
        ACCEPTED_SIGNALS = [
            signal.SIGHUP,  # 1
            signal.SIGINT,  # 2
            signal.SIGQUIT, # 3
            signal.SIGABRT, # 6
            signal.SIGTERM  # 15
        ]
        for sig in ACCEPTED_SIGNALS:
            signal.signal(sig, self.on_quit)

    def stream_redirect(self):
        if self.background:
            outpath = os.path.expanduser(self.stdout)
            sys.stdout = open(outpath, 'w')
            errpath = os.path.expanduser(self.stderr)
            sys.stderr = open(errpath, 'w')

    def stream_flush(self):
        if self.background:
            sys.stdout.flush()
            sys.stderr.flush()

    def stream_close(self):
        if self.background:
            sys.stdout.close()
            sys.stderr.close()

    def pidfile_create(self):
        # 產生 pid file
        self.pid_file = os.path.expanduser('~/.twnews/fin_schedule.pid')
        pid_base = os.path.dirname(self.pid_file)
        if not os.path.isdir(pid_base):
            os.makedirs(pid_base)
        with open(self.pid_file, 'w') as pid_stream:
            pid_stream.write('%s' % os.getpid())

    def pidfile_remove(self):
        # 移除 pid file
        os.remove(self.pid_file)

    def run(self):
        self.listen_sys_signals()
        self.stream_redirect()
        self.pidfile_create()

        attrs = {}
        self.init_task(attrs)
        while not self.close_requested:
            self.loop_task(attrs)
            self.stream_flush()

            # Make the next waking near 0 second.
            t = time.time()
            delay = 1 - (t - int(t))
            time.sleep(delay)

        self.pidfile_remove()
        self.stream_close()

class ScheduleDaemon(JustDaemon):
    """
    排程型 Daemon
    TODO: 分割成獨立套件
    """

    def __init__(self, schedule_table, stdout='/dev/null', stderr='/dev/null', background=True):
        self.schedule_table = schedule_table
        super().__init__(
            init_task = self.init_task,
            loop_task = self.loop_task,
            stdout = stdout,
            stderr = stderr,
            background = background
        )

    def init_task(self, attrs):
        for run_at in self.schedule_table:
            func = self.schedule_table[run_at]['func']
            args = self.schedule_table[run_at]['args']
            weekend = True
            if 'weekend' in self.schedule_table[run_at]:
                weekend = self.schedule_table[run_at]['weekend']

            if weekend:
                schedule.every().day.at(run_at).do(self.run_parallel, func, args)
            else:
                schedule.every().monday.at(run_at).do(self.run_parallel, func, args)
                schedule.every().tuesday.at(run_at).do(self.run_parallel, func, args)
                schedule.every().wednesday.at(run_at).do(self.run_parallel, func, args)
                schedule.every().thursday.at(run_at).do(self.run_parallel, func, args)
                schedule.every().friday.at(run_at).do(self.run_parallel, func, args)

    def loop_task(self, attrs):
        schedule.run_pending()

    def run_parallel(self, func, args):
        th = threading.Thread(target=func, args=args)
        th.start()

def im_fine():
    logger = cm.get_logger('finance')
    logger.info('I\'m fine. (%s)', __file__)

def tpe_at(timestr):
    hh_adjust = (time.altzone / -3600) - 8
    hh = (int(timestr[0:2]) + hh_adjust) % 24
    mm = int(timestr[3:5])
    return '%02d:%02d' % (hh, mm)

def main():
    # 注意!! args 要用 list 不可以用 tuple，否則傳遞一個字串時，會把每個字元當成一個參數傳遞
    ScheduleDaemon(
        schedule_table = {
            # 每日健康回報
            tpe_at('09:30'): { 'func': im_fine, 'args': [] },
            tpe_at('14:00'): { 'func': im_fine, 'args': [] },
            # 證交所
            tpe_at('14:09'): { 'func': twse.sync_dataset, 'args': ['borrowed'], 'weekend': False },
            tpe_at('15:57'): { 'func': twse.sync_dataset, 'args': ['etfnet'], 'weekend': False },
            tpe_at('16:44'): { 'func': twse.sync_dataset, 'args': ['institution'], 'weekend': False },
            tpe_at('17:33'): { 'func': twse.sync_dataset, 'args': ['block'], 'weekend': False },
            tpe_at('21:41'): { 'func': twse.sync_dataset, 'args': ['margin'], 'weekend': False },
            tpe_at('21:42'): { 'func': twse.sync_dataset, 'args': ['selled'], 'weekend': False },
            # 櫃買中心
            tpe_at('16:49'): { 'func': tpex.sync_dataset, 'args': ['institution'], 'weekend': False },
            tpe_at('17:48'): { 'func': tpex.sync_dataset, 'args': ['block'], 'weekend': False },
            tpe_at('21:47'): { 'func': tpex.sync_dataset, 'args': ['margin'], 'weekend': False },
            tpe_at('21:48'): { 'func': tpex.sync_dataset, 'args': ['selled'], 'weekend': False },
            # 集保中心
            tpe_at('07:01'): { 'func': tdcc.sync_dataset, 'args': [] },
        },
        background = False
    ).run()

if __name__ == '__main__':
    main()
