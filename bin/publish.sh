#!/bin/bash

# 封裝前檢查 logging.ini，確認 root logger 使用 INFO level
echo -n '檢查 root logger 是否設定成 INFO 等級 ... '
head -n 6 twnews/conf/logging.ini | grep 'INFO' > /dev/null
if [ $? -ne 0 ]; then
  echo 'Root logger 沒使用 INFO level，停止封裝'
  exit 1
fi
echo 'OK'

# 封裝前跑一次單元測試，確認程式邏輯正確
echo -n '檢查 README.rst 語法 ... '
MSG=`rstcheck README.rst 2>&1`
if [ $? -ne 0 ]; then
  echo 'README.rst 語法錯誤，停止封裝'
  echo $MSG
  exit 2
fi
echo 'OK'

# 封裝前跑一次單元測試，確認程式邏輯正確
echo -n '發佈前測試 ... '
python3 -m unittest discover -f twnews.tests 2> /dev/null
if [ $? -ne 0 ]; then
  echo '發佈前測試失敗，停止封裝'
  exit 3
fi
echo 'OK'

# 封裝
echo -n '封裝 ... '
python3 setup.py -q bdist_wheel
RET=$?
rm -rf build twnews.egg-info
if [ $RET -ne 0 ]; then
  echo '封裝失敗'
  exit 3
fi
echo 'OK'

# 佈署
WHEEL=`ls -t1 dist/ | head -n 1`
if [ "$1" == 'release' ]; then
  # 佈署到 pypi.org
  twine upload dist/$WHEEL
elif [ "$1" == 'test' ]; then
  # 佈署到 test.pypi.org
  twine upload --repository testpypi --verbose dist/$WHEEL
else
  # 在乾淨環境跑一次單元測試，確認沒有缺少相依套件

  # 在 sandbox 目錄建立 virtualenv 然後安裝 wheel 包
  echo -n '在 virtualenv 環境進行本地佈署 ... '
  if [ -d 'sandbox' ]; then
    rm -rf sandbox
  fi
  virtualenv -q sandbox
  sandbox/bin/pip -q install dist/$WHEEL
  echo 'OK'

  # 在 sandbox 跑一次單元測試
  echo -n '發佈後測試 ... '
  cd sandbox
  bin/python -m unittest discover -f twnews.tests 2> /dev/null
  if [ $? -ne 0 ]; then
    echo '發佈後測試失敗，進入 sandbox 目錄查一下環境問題吧'
    exit 4
  fi
  echo 'OK'

  # 成功後顯示下一步提示
  echo '-----------------------------------------------------'
  echo '發佈後測試成功，接下來發佈到 PyPi 看看:'
  echo ''
  echo '發佈到 https://test.pypi.org'
  echo ''
  echo '    bin/publish.sh test'
  echo ''
  echo '發佈到 https://pypi.org'
  echo ''
  echo '    bin/publish.sh release'
  echo ''
  cd ..
  rm -rf sandbox
fi

exit 0
