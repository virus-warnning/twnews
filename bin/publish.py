#!/usr/bin/env python3
#
# 必要工具套件:
# * pylint
# * rstcheck
# * setuptools

import os

'''
print('檢查程式碼品質')
ret = os.system('pylint -f colorized twnews')
if ret != 0:
    print('檢查沒通過，停止封裝\n')
    exit(ret)
'''

'''
print('檢查 README.rst')
ret = os.system('rstcheck README.rst')
if ret != 0:
    print('檢查沒通過，停止封裝\n')
    exit(ret)
'''

print('封裝')
ret = os.system('python3 setup.py -q bdist_wheel')
if ret != 0:
    print('封裝失敗')
    exit(ret)

print('測試')
for ver in ['35', '36', '37']:
    dest = 'sandbox/py' + ver
    if not os.path.isdir(dest):
        os.makedirs(dest)
