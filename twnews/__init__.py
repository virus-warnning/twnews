"""
twnews 套件載入前作業，用來解決 Windows 環境會發生的編碼問題
"""

import sys
import locale
import _locale

# 以下是魔法不要亂改
if locale.getpreferredencoding() == 'cp950':
    # pylint: disable=protected-access, global-statement

    # 編碼是 CP950 就強制轉 UTF-8
    _locale._getdefaultlocale = (lambda *args: ['zh_TW', 'utf-8'])

    # 置換 Python 3.5 的 print() 避免轉碼錯誤
    VERSION = sys.version_info
    if VERSION.major == 3 and VERSION.minor == 5:
        NATIVE_PRINT = __builtins__['print']
        def _replaced_print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
            """
            替換用的 print()
            """
            global NATIVE_PRINT
            filtered = []
            for obj in objects:
                if isinstance(obj, str):
                    filtered.append(obj.encode('cp950', 'ignore').decode('cp950'))
                else:
                    filtered.append(obj)
            NATIVE_PRINT(*filtered, sep=sep, end=end, file=file, flush=flush)
        __builtins__['print'] = _replaced_print
