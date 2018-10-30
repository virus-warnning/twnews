#!/bin/bash

rm -rf dist build twnews.egg-info
python3 setup.py bdist_wheel

if [ $? -eq 0 ]; then
  WHEEL=`find dist/* | tail -n 1`

  if [ "$1" == "release" ]; then
    twine upload ${WHEEL}
  elif [ "$1" == "test" ]; then
    twine upload --repository testpypi --verbose ${WHEEL}
  else
    pip3 uninstall -y twnews
    pip3 install ${WHEEL}
  fi
else
  echo "======================================================================"
  echo "Cannot build wheel."
fi
