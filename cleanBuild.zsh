#! /bin/zsh
#
# Copyright (c) 2024-2025 Tom Björkholm
# MIT License
#
set -eE
trap 'printf "\e[31m%s: %s\e[m\n" "Exiting due to error code from command" $?' ERR
if [ ! -z "${VIRTUAL_ENV}" ] ; then
  echo "Cannot delete virtual environment if already in virtual environment"
  echo "First do: deactivate "
  exit 1
fi
PYVER=''
if [ ${#} -gt 0 ] ; then
  for arg in ${@} ; do
    if echo ${arg} | grep 'python' > /dev/null
    then
      PYVER=${arg}
    fi
  done
fi
if [[ -z "${PYVER}" ]] ; then
  PYVER=`./bestInstalledPython.zsh`
  echo "Python version not found in arguments. Using default: ${PYVER}"
fi
./clean.zsh
./setup_build_environment.zsh ${PYVER}
./doBuild.zsh ${PYVER}
