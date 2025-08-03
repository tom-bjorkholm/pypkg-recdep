#! /bin/zsh
#
# Copyright (c) 2024-2025 Tom Björkholm
# MIT License
#
bestnum=`find ${=PATH//:/ } -name 'python3.*' | egrep '.*python3.[0-9]+$' | \
  sed 's/.*python3.\([0-9]*\)/\1/g' | sort -n | tail -1`
echo python3.$bestnum
