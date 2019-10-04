import os
import schedule
import signal
import sys
import threading
import time
from datetime import datetime, timedelta

sys.path.append(os.path.realpath('.'))

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
        pid_file = os.path.expanduser('~/.twnews/fin_schedule.pid')
        pid_base = os.path.dirname(pid_file)
        if not os.path.isdir(pid_base):
            os.makedirs(pid_base)
        with open(pid_file, 'w') as pid_stream:
            pid_stream.write('%s' % os.getpid())

    def pidfile_remove(self):
        # 移除 pid file
        os.remove(pid_file)

    def run(self):
        self.listen_sys_signals()
        self.stream_redirect()

        attrs = {}
        self.init_task(attrs)
        while not self.close_requested:
            self.loop_task(attrs)
            self.stream_flush()

            # Make the next waking near 0 second.
            t = time.time()
            delay = 1 - (t - int(t))
            time.sleep(delay)

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
            schedule.every().day.at(run_at).do(self.run_parallel, func, args)

    def loop_task(self, attrs):
        schedule.run_pending()

    def run_parallel(self, func, args):
        th = threading.Thread(target=func, args=args)
        th.start()

def taipei_time(timestr):
    hh_adjust = (time.altzone / -3600) - 8
    hh = (int(timestr[0:2]) + hh_adjust) % 24
    mm = int(timestr[3:5])
    return '%02d:%02d' % (hh, mm)

def main():
    ScheduleDaemon(
        schedule_table = {
            taipei_time('14:09'): { 'func': twse.sync_dataset, 'args': ('borrowed') },
            taipei_time('15:57'): { 'func': twse.sync_dataset, 'args': ('etfnet') },
            taipei_time('16:44'): { 'func': twse.sync_dataset, 'args': ('institution') },
            taipei_time('17:33'): { 'func': twse.sync_dataset, 'args': ('block') },
            taipei_time('20:41'): { 'func': twse.sync_dataset, 'args': ('margin') },
            taipei_time('20:42'): { 'func': twse.sync_dataset, 'args': ('selled') },
            taipei_time('16:49'): { 'func': tpex.sync_dataset, 'args': ('institution') },
            taipei_time('17:48'): { 'func': tpex.sync_dataset, 'args': ('block') },
            taipei_time('20:47'): { 'func': tpex.sync_dataset, 'args': ('margin') },
            taipei_time('07:01'): { 'func': tdcc.sync_dataset, 'args': () },
            # '17:53': { 'func': tpex.sync_dataset, 'args': ('institution') }
        },
        # background = False
    ).run()

if __name__ == '__main__':
    main()
