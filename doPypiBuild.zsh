#! /bin/zsh
#
# Copyright (c) 2024 - 2025 Tom Björkholm
# MIT License
#

./clean.zsh
./setup_build_environment.zsh
./doBuild.zsh
./clean.zsh
./setup_build_environment.zsh
./doBuild.zsh
twine upload dist/*
