Module burncpu is a worker dispatcher with multiprocessing and multithreading.

Features
========
- All CPU cores can be used.
- Workers can be stopped gracefully by system signals.
- Pure python code.

Quickstart
==========
Use the following command to run the sample module.

.. code:: bash

  python3 -m burncpu.sample

Then monitor CPU status, some changes take place at these time.

====  =================================================
Time                        Events
====  =================================================
  0s   All CPU cores are IDLE.
 10s   Workers begin to call one_second_task many times.
 60s   Workers begin to terminate.
====  =================================================

Pressing Ctrl+C or sending system signal can also terminate the sample.

Finally copy and modify the `source code <https://github.com/virus-warnning/burncpu/blob/master/burncpu/sample.py>`_ to make your own.

Reference
=========

To import
---------

.. code:: python

  from burncpu.dispatcher import WorkerDispatcher

class WorkerDispatcher
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
