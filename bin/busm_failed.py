import os
import sys
import threading

sys.path.append(os.path.realpath('.'))

import twnews.common as cm

# 這一行搭配 logger.error() 可以讓程式在 Mac 環境爆掉
#   objc[70893]: +[__NSPlaceholderDate initialize] may have been in progress in another thread when fork() was called.
#   objc[70893]: +[__NSPlaceholderDate initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.
# 但目前找不到具體原因
import twnews.finance.twse as twse

def main():
    if os.fork() > 0:
        exit(0)

    logger = cm.get_logger('finance')
    logger.error('test')

if __name__ == '__main__':
    main()
