# pypkg-recdep

> **👤 Looking to use this tool?**  
> This repository is for developers. If you want to install and use `pypkg-recdep`,
> please visit the **PyPI project page [https://pypi.org/project/pypkg-recdep](https://pypi.org/project/pypkg-recdep)**
> for installation instructions and user documentation.

## Background

Some organizations need to have python packages available in an internal network with no connection to internet. It is not enough to download and copy the python packages you know that you will use, you also have to include all dependencies. And the dependencies of the dependencies, recursively.

This python package is created to automate the collection of information needed to maintain python packages in such a setup with an internal network with no direct internet connection.

## What it does

* It creates a list of all dependencies of a package and includes other information (like licences) that might be needed to evaluate if the use of package is OK in a specific context.
* It can also make a list of all packages available in an internal ADO server hosting the internal package repository.
* It creates a list of all dependencies of a package excluding the packages that is already available in your own local collection of packages.

## For developers

### Needed environment

#### OS

For running the script and running the test suite you need a mac or a Linux computer. Even if the resulting application can be installed and used on Windows, the scripts for building and testing are only implemented for mac and Linux.

#### Python version

Please see README_pypi.md for information on needed python version. Main development is on newest Python version, and may be backported to older Python version on a branch.

#### Zsh

The scripts are all zsh. zsh is available by default on modern macs. zsh can easily be installed on Linux (on Ubuntu: `sudo apt install zsh`).

### Internal APIs not guaranteed

The internal APIs in this package are not guaranteed to be stable. They can change without warning between versions.

### Quick start

1. Clone this repository
2. Run `./setup_build_environment.zsh` to set up the build environment
3. Run `./doBuild.zsh` to build and test the package

### Building application

There are 3 scripts for building the application:

* `setup_build_environment.zsh` Run this script first to get the environment set up for building
* `doBuild.zsh` Run this script to build an installation package (.whl) and to run the tests on it in a venv (virtual environment).
* `clean.zsh` Deletes all files that was produced by the build to start over from a clean state.

The "testing" includes pytest, pylint, flake8 and mypy.

After running `doBuild.zsh` you can open `reports/index.htm` to see all test reports.

After running `doBuild.zsh` you can do manual test of the built and installed application in the virtual environment `./venv`.

## Test summary

* Test result: 438 passed in 5s
* No Flake8 warnings.
* No mypy errors found.
* 0.3 built and tested using python version: Python 3.14.2
