#! /bin/zsh
#
# Copyright (c) 2024 - 2025 Tom Björkholm
# MIT License
#
set -eE
DO_TWINE_UPLOAD=0
PYVER=''
if [ ${#} -gt 0 ] ; then
  for arg in ${@} ; do
    if echo ${arg} | grep 'python' > /dev/null
    then
      PYVER=${arg}
    fi
    if [ ${arg} = 'twine' ] ; then
      DO_TWINE_UPLOAD=1
    fi
  done
fi
if [[ -z "${PYVER}" ]] ; then
  PYVER=`./bestInstalledPython.zsh`
  echo "Python version not found in arguments. Using default."
fi
echo "Using Python version: ${PYVER}"
./cleanBuild.zsh ${PYVER}
./cleanBuild.zsh ${PYVER}
if [ ${DO_TWINE_UPLOAD} -eq 1 ] ; then
  twine upload dist/*
else
  echo "Twine upload not done as it was not requested."
  echo "To upload to PyPI, run: ./doPypiBuild.zsh twine"
fi
