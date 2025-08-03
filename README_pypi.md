# pypkg-recdep

## Background

Some organizations need to have python packages available in an internal network with no connection to internet. It is not enough to download and copy the python packages you know that you will use, you also have to include all dependencies. And the dependencies of the dependencies, recursively.

This python package is created to automate the collection of information needed to maintain python packages in such a setup with an internal network with no direct internet connection.

## Using it

If you want to use it install it using pip from [https://pypi.org/project/pypkg-recdep](https://pypi.org/project/pypkg-recdep). There is no need download anything from Bitbucket to use the application.

### Installing on mac and Linux

````sh
pip3 install --upgrade pypkg-recdep
````

### Installing on Microsoft Windows

````sh
pip install --upgrade pypkg-recdep
````

## What it does

* It creates a list of all dependencies of a package on PyPI and includes other information (like licences) that might be needed to evaluate if the use of package is OK in a specific context.
  * All dependencies includes not only the direct dependencies but also the indirect dependencies of the dependencies.
* It can also make a list of all packages available in an internal ADO server hosting the internal package repository.
* It can also make a list of all packages available in an internal server using PyPI protocols hosting the internal package repository.
* The lists of internally available packages can be used to as input when creating the list of all dependencies of a package on PyPI. Then the produced output differentiates between internally already available packages and packages that need to be processed to become available internally.

## How to use it

To be written.

## Test summary

* Test result: 10 passed in 3s
* No Flake8 warnings.
* No mypy errors found.
* 0.0.2 built and tested using python version: Python 3.13.5
