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

## Version history

| Version | Date        | Python version  | Description                         |
|---------|-------------|-----------------|-------------------------------------|
| 0.1     | 15 Aug 2025 | 3.12 or newer   | First released version              |
| 0.2.1   | 14 Dec 2025 | 3.12 or newer   | Bug fix release                     |

## How to use it

### Use help

On mac and Linux:

```` text
% python3 -m pypkg_recdep --help
% python3 -m pypkg_recdep printdeps --help
% python3 -m pypkg_recdep listinternal --help
% python3 -m pypkg_recdep listado --help
````

On Microsoft Windows:

```` text
% python -m pypkg_recdep --help
% python -m pypkg_recdep printdeps --help
% python -m pypkg_recdep listinternal --help
% python -m pypkg_recdep listado --help
````

### Get information on first packages

So you have set up a service to store python packages in your isolated network. The first thing you need to do is to get information from PyPI.org about a few packages that are candidates to have on you internal network. However, you are using the old Python 3.12 in the internal network so all packages should run on that version. Also the sercie to store python packages have a bug for metadata version greater than 2.3, so you need to select package versions based on this. You also want a list of PURLs [https://github.com/package-url/purl-spec#purl](https://github.com/package-url/purl-spec#purl) to feed into some script you have.

On a computer with internet access run on mac or Linux:

```` text
% python3 -m pypkg_recdep printdeps --package setuptools --pythonversion 3.12 --metadatamax 2.3 --listpurls purls.txt --output setuptools.md
% python3 -m pypkg_recdep printdeps --package selenium --pythonversion 3.12 --metadatamax 2.3 --listpurls purls.txt --output selenium.md
File purls.txt exists. Appending to it.
````

or using the short version of the command line flags on mac and Linux:

```` text
% python3 -m pypkg_recdep printdeps -p setuptools -y 3.12 -m 2.3 -l purls.txt -o setuptools.md
% python3 -m pypkg_recdep printdeps -p selenium -y 3.12 -m 2.3 -l purls.txt -o selenium.md
File purls.txt exists. Appending to it.
````

On a computer with internet access run on Microsoft Windows:

```` text
% python -m pypkg_recdep printdeps --package setuptools --pythonversion 3.12 --metadatamax 2.3 --listpurls purls.txt --output setuptools.md
% python -m pypkg_recdep printdeps --package selenium --pythonversion 3.12 --metadatamax 2.3 --listpurls purls.txt --output selenium.md
File purls.txt exists. Appending to it.
````

or using the short version of the command line flags on Microsoft Windows:

```` text
% python -m pypkg_recdep printdeps -p setuptools -y 3.12 -m 2.3 -l purls.txt -o setuptools.md
% python -m pypkg_recdep printdeps -p selenium -y 3.12 -m 2.3 -l purls.txt -o selenium.md
File purls.txt exists. Appending to it.
````

As you notice you will need to let the program create a separate markdown file with infomration for each top-level package you want information on. This markdown file contains information on that package and on all packages it depends on, and on all packages the dependencies depend on, and so on.
However, you can use the same file name of the list of PURLs for several top level packages.

### Knowing what is on your server

Once you have downloaded a number of packages and uploaded them to you local server on your local isolated network, you want to know what you already have locally. You want to avoid analyzing and downloading versions of packages that you already have.
To solve this pypkg_recdep can list what you have on you local server.

#### Using PyPI REST API to list your local server

On a Linux or mac computer on you local network run:

```` text
 % python3 -m pypkg_recdep listinternal --url https://pypi.local --output internal.csv
````

or if you need to use a personal access token, run:

```` text
% python3 -m pypkg_recdep listinternal --url https://pypi.org --output internal.csv --patfile my_pat_file
````

Of course this can also be done on using the short versions of the command line flags (with or without the personal access token):

```` text
% python3 -m pypkg_recdep listinternal -u https://pypi.org -o internal.csv
````

or if you need to use a personal access token, run:

```` text
% python3 -m pypkg_recdep listinternal -u https://pypi.org -o internal.csv -a my_pat_file
````

To run these on a computer running Microsoft Windows just type "python" instead of "python3".

#### Listing python packages on Azure Devops Server

```` text
% python3 -m pypkg_recdep listado --help  usage: pypkg_recdep listado [-h] [-o OUTPUT] [-s INSTANCE] [-c COLLECTION]
                            [-p PROJECT] [-i INCLUDE_TYPES] [-a PATFILE]

List python packages in Azure Dev Ops (ADO) server matching types.

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Name of output CSV file (default: ado.csv).
  -s, --instance INSTANCE
                        Instance or server name. (Default: "devops.local.net".
                        Set environment variable ADO_INSTANCE to change
                        default value.)
  -c, --collection COLLECTION
                        Collection. (Default: "Python". Set environment
                        variable ADO_COLLECTION to change default value.)
  -p, --project PROJECT
                        Project.(Default: None. Set environment variable
                        ADO_PROJECT to change default value.)
  -i, --include-types INCLUDE_TYPES
                        Comma separated list of package types to include.
                        (Default: "wheel". Set environment variable ADO_TYPES
                        to change default value.)
  -a, --patfile PATFILE
                        File name of file with personal access token.
                        (Default: None. Set environment variable PATFILE to
                        change default value.)

Useful when having internal ADO server mirroring part of PyPI.org.
````

### Get information on additional packages

The CSV file of the packages on your local server (created in the text above) can be used as an exclude file for what dependent packages to exclude (i.e. not download this time) when getting information on additional packages from PyPI.org.

On a computer with internet access run on mac or Linux:

```` text
% python3 -m pypkg_recdep printdeps --package excel-list-transform --pythonversion 3.12 --metadatamax 2.3 --listpurls purls.txt --output excel-list-transform.md --excludecsv internal.csv --excludetext 'already on internal server'
````

Of course this can also be done on using the short versions of the command line flags

```` text
% python3 -m pypkg_recdep printdeps -p excel-list-transform -y 3.12 -m 2.3 -l purls.txt --o excel-list-transform.md -e internal.csv -t 'already on internal server' 
````

To run these on a computer running Microsoft Windows just type "python" instead of "python3".

## Source code

Source code and tests are available at [https://bitbucket.org/tom-bjorkholm/pypkg-recdep](https://bitbucket.org/tom-bjorkholm/pypkg-recdep).

## Test summary

* Test result: 205 passed in 3s
* No Flake8 warnings.
* No mypy errors found.
* 0.2.1 built and tested using python version: Python 3.14.0
