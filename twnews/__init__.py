import locale
import _locale
import sys

# 以下是魔法不要亂改
if locale.getpreferredencoding() == 'cp950':

    # 編碼是 CP950 就強制轉 UTF-8
    _locale._getdefaultlocale = (lambda *args: ['zh_TW', 'utf-8'])

    # 置換 Python 3.5 的 print() 避免轉碼錯誤
    v = sys.version_info
    if v.major == 3 and v.minor == 5:
        native_print = __builtins__['print']
        def _replaced_print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False):
            global native_print
            filtered = []
            for obj in objects:
                if isinstance(obj, str):
                    filtered.append(obj.encode('cp950', 'ignore').decode('cp950'))
                else:
                    filtered.append(obj)
            native_print(*filtered, sep=sep, end=end, file=file, flush=flush)
        __builtins__['print'] = _replaced_print
