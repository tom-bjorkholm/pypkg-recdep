# pypkg-recdep

> **👤 Looking to use this tool?**  
> This repository is for developers. If you want to install and use `pypkg-recdep`,
> please visit the **PyPI project page [https://pypi.org/project/pypkg-recdep](https://pypi.org/project/pypkg-recdep)**
> for installation instructions and user documentation.

## Background

Some organizations need to have python packages available in an internal network with no connection to internet. It is not enough to download and copy the python packages you know that you will use, you also have to include all dependencies. And the dependencies of the dependencies, recursively.

This python package is created to automate the collection of information needed to maintain python packages in such a setup with an internal network with no direct internet connection.

## What it does

- It creates a list of all dependencies of a package and includes other information (like licences) that might be needed to evaluate if the use of package is OK in a specific context.
- It can also make a list of all packages available in an internal ADO server hosting the internal package repository.
- It creates a list of all dependencies of a package excluding the packages that is already available in your own local collection of packages.

## For developers

### Needed environment

#### OS

For running the script and running the test suite you need a mac or a Linux computer. Even if the resulting application can be installed and used on Windows, the scripts for building and testing are only implemented for mac and Linux.

#### Python version

Please see README_pypi.md for information on needed python version. Main development is on newest Python version, and may be backported to older Python version on a branch.

#### Zsh

Some scripts are Python but there are also needed scripts in zsh. zsh is available by default on modern macs. zsh can easily be installed on Linux (on Ubuntu: `sudo apt install zsh`).

### Internal APIs not guaranteed

The internal APIs in this package are not guaranteed to be stable. They can change without warning between versions.

### Cloning

The mformat repo uses submodules. To clone it use the command:

````sh
git clone --recurse-submodules git@github.com:tom-bjorkholm/pypkg-recdep.git
````

If you forgot to include the `--recurse-submodules` in your `git clone` command
you can fix it later with the command:

````sh
git submodule update --init --recursive 
````

To update the version of thr submodule repo that you see in the main repo use the command:

````sh
git submodule update --remote --merge
````

### Building application

There are 3 main scripts (and 2 extra convinience scripts) for building the application:

- `run_setup_build_environment.py` Run this script first to get the
  environment set up for building.
- `run_build.py` Run this script to build an installation package (.whl) and
  to run the tests on it in a venv (virtual environment).
- `run_clean.py` Deletes all files that was produced by the build to start
  over from a clean state.
- `run_clean_build.py` Combines the use of `run_clean.py`,
  `run_setup_build_environment.py` and `run_build.py` into one script.
  Pylint discover some duplicate code warnings only on a clean build so this
  is useful.
- `run_pypi_build.py` Builds for PyPI upload and can do the upload too.

The "testing" includes pytest, pylint, flake8 and mypy.

After running `run_build.py` you can open `reports/index.html` to see all test
reports.

### More build system information

The file `./common_build_tools/README.md` (in git submodule - see above) contains more
information about the build system. This README can also be viewed at
[https://github.com/tom-bjorkholm/common_build_tools/blob/master/README.md](https://github.com/tom-bjorkholm/common_build_tools/blob/master/README.md)

### Integration tests towards PyPI.org

There are integration tests that query the real PyPI.org server. These tests are marked with `@pytest.mark.slow` and are not run in the automated build (because they require network access and are slow).

To run the integration tests manually:

```sh
source ./venv/bin/activate
pytest --slow test/test_pypkg_recdep/test_find_pypi_deps2.py -v -k "integration"
deactivate
```

These tests verify that the dependency resolution works correctly with real packages on PyPI.org and can help detect changes in PyPI's API or metadata formats.

After running `doBuild.zsh` you can do manual test of the built and installed application in the virtual environment `./venv`.

## Test summary

- Test result: 638 passed, 2 skipped in 18s
- No flake8 warnings.
- No mypy errors found.
- Python layout warnings.
- Built version(s): 0.6.1
- Build and test using Python 3.14.6
