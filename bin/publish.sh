#!/bin/bash

rm -f dist/*
python3 setup.py bdist_wheel

if [ $? -eq 0 ]; then
  WHEEL=`find dist/* | tail -n 1`

  if [ "$1" == "test" ]; then
    twine upload --repository testpypi ${WHEEL}
  else
    twine upload ${WHEEL}
  fi
else
  echo "======================================================================"
  echo "Cannot build wheel."
fi
