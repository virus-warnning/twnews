#!/usr/bin/env python3
#
# 必要工具套件:
# * pylint
# * rstcheck
# * setuptools

import configparser
import os
import re
import subprocess
import sys

def get_wheel():
    """ 製作 wheel 檔案與取得檔名 """
    comp = subprocess.run(['python3', 'setup.py', 'bdist_wheel'], capture_output=True)
    if comp.returncode != 0:
        return False

    wheel = False
    stdout = comp.stdout.decode('utf-8').split('\n')
    for line in stdout:
        match = re.search('dist/twnews-.+\.whl', line)
        if match is not None:
            wheel = match.group(0)
            break

    return wheel

def get_latest_python():
    """ 選擇 pyenv 環境中 3.5 ~ 3.8 的最新版本 """
    detected_ver = {
        '3.5': -1,
        '3.6': -1,
        '3.7': -1,
        '3.8': -1
    }

    comp = subprocess.run(['pyenv', 'versions'], capture_output=True)
    stdout = comp.stdout.decode('utf-8').strip().split('\n')
    for line in stdout:
        match = re.match('  (\d\.\d)\.(\d+)', line)
        if match is not None:
            minor_ver = match.group(1)
            patch_ver = int(match.group(2))
            if minor_ver in detected_ver and \
                patch_ver > detected_ver[minor_ver]:
                detected_ver[minor_ver] = patch_ver

    latest_ver = []
    for minor_ver in detected_ver:
        if detected_ver[minor_ver] > -1:
            full_ver = '%s.%d' % (minor_ver, detected_ver[minor_ver])
            latest_ver.append(full_ver)

    return latest_ver

def test_in_virtualenv(pyver, wheel):
    """ 配置 virtualenv 並執行測試程式 """

    # 安裝 virtualenv
    src = os.path.expanduser('~/.pyenv/versions/%s/bin/python' % pyver)
    dst = 'sandbox/%s' % pyver
    comp = subprocess.run(['virtualenv', '-p', src, dst])
    if comp.returncode != 0:
        return False

    # 測試 wheel 包
    # 1. 安裝 wheel
    # 2. 安裝 green
    # 3. 執行測試程式
    os.chdir(dst)
    wheel = '../../' + wheel
    comp = subprocess.run(['bin/pip', 'install', wheel, 'green'])
    if comp.returncode == 0:
        comp = subprocess.run(['bin/green', '-vv', 'twnews'])
    os.chdir('../..')

    return (comp.returncode == 0)

def wheel_check():
    """ 檢查 wheel 是否能正常運作在各個 Python 版本環境上 """

    """
    print('檢查 logging.ini')
    config = configparser.ConfigParser()
    config.read('twnews/conf/logging.ini')
    if config['handler_stdout']['level'] != 'CRITICAL':
        print('handler_stdout 忘記切換成 CRITICAL level')
        exit(1)
    """

    print('檢查程式碼品質')
    ret = os.system('pylint -f colorized twnews')
    if ret != 0:
        print('檢查沒通過，停止封裝')
        exit(ret)

    print('檢查 README.rst')
    ret = os.system('rstcheck README.rst')
    if ret != 0:
        print('檢查沒通過，停止封裝')
        exit(ret)

    print('偵測可用的測試環境')
    os.system('rm -rf sandbox/*')
    wheel = get_wheel()
    latest_python = get_latest_python()
    if len(latest_python) == 0:
        print('沒有任何可用的測試環境')
        exit(1)

    for pyver in latest_python:
        print('測試 Python %s' % pyver)
        test_in_virtualenv(pyver, wheel)

def upload_to_pypi(test=False):
    """ 上傳 wheel 到 PyPi """

    # 檢查 ~/.pypirc 是否存在
    if not os.path.isfile(os.path.expanduser('~/.pypirc')):
        print('缺少 pypi 設定檔 ~/.pypirc')
        print('參考: https://gist.github.com/ibrahim12/c6a296c1e8f409dbed2f')

    # 重新產生 wheel 與上傳前確認
    wheel = get_wheel()
    prompt = '準備上傳的檔案是 %s, 確定上傳嗎 [y/n]? ' % wheel
    print(prompt, end='', flush=True)
    ans = sys.stdin.readline().strip()
    if ans != 'y':
        print('取消上傳')
        return

    # 上傳 wheel
    cmd = ['twine', 'upload']
    if test:
        cmd.append('--repository')
        cmd.append('testpypi')
    cmd.append('--verbose')
    cmd.append(wheel)
    comp = subprocess.run(cmd)
    if comp.returncode == 0:
        print('上傳成功')
    else:
        print('上傳失敗')

def main():
    # 確保不在 repo 目錄也能正常執行
    TWNEWS_HOME = os.path.realpath(os.path.dirname(__file__) + '/..')
    os.chdir(TWNEWS_HOME)

    action = 'wheel'
    if len(sys.argv) > 1:
        action = sys.argv[1]

    if action == 'release':
        upload_to_pypi()
    elif action == 'test':
        upload_to_pypi(True)
    elif action == 'wheel':
        wheel_check()
    else:
        print('Unknown action "%s".' % action)
        exit(1)

if __name__ == '__main__':
    main()
