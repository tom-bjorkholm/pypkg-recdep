#! /usr/local/bin/python3
# PYTHON_ARGCOMPLETE_OK
"""Handle command line parsing of pypkg_recdep."""

# Copyright (c) 2025 Tom Björkholm
# MIT License

from typing import Optional, TypeAlias
from copy import deepcopy
from socket import getfqdn
import sys
import os
import argparse
import argcomplete
from pypkg_recdep.list_ado_content import list_ado_content, UrlInfo
from pypkg_recdep.print_deps import print_rec_deps
from pypkg_recdep.exclude import ExcludeInfo
from pypkg_recdep.internal_server_listing import list_in_internal_server


SubParseAct: TypeAlias = 'argparse._SubParsersAction[argparse.ArgumentParser]'


def list_pypi_func(args: argparse.Namespace) -> int:
    """List content in internal PyPI server.

    @param args The namespace created by argparse.
    """
    list_in_internal_server(server_url=args.url[0],
                            pat_file=args.patfile[0],
                            output_file=args.output[0],
                            limit=args.limitnumber[0])
    return 0


def list_ado_func(args: argparse.Namespace) -> int:
    """List content in Azure Dev Ops (ADO) server.

    @param args The namespace created by argparse.
    """
    proj: Optional[str] = None
    if args.project is not None:
        if len(args.project) >= 1:
            proj = args.project[0]
            if proj == 'None':
                proj = None
    incs = args.include_types[0].split(',')
    url_info = UrlInfo(instance=args.instance[0],
                       collection=args.collection[0],
                       pat_file=args.patfile[0])
    return list_ado_content(file_name=args.output[0],
                            url_info=url_info,
                            project=proj, include_types=incs)


def print_deps_func(args: argparse.Namespace) -> int:
    """Print all recursive dependencies of a python package.

    Fetch the package and the information on packages it depends on.
    Then recursively follow each dependency to get the dependencies of the
    dependencies. (Conceptual recursion but implementation is not recursion.)
    @param args The namespace created by argparse.
    """
    exclude = ExcludeInfo(txt='no exclues', csv_filename=None)
    if args.excludecsv:
        exclude = ExcludeInfo(txt=args.excludetext[0],
                              csv_filename=args.excludecsv[0])
    return print_rec_deps(app_name=args.package[0],
                          metadata_max=args.metadatamax[0],
                          python_ver=args.pythonversion[0],
                          outfilename=args.output[0],
                          purls=args.listpurls[0],
                          exclude=exclude)


def get_def_domain() -> str:
    """Get default domain name (for internal servers).

    Make sure defalt internal domain is never .org, .net, .com.
    (This is used to guess names of internal servers, but should
    avoid guessing that the name of an internal server is pypi.org.)
    """
    dlist: list[str] = getfqdn().split('.')[1:]
    if len(dlist) >= 3:
        del dlist[0]
    if len(dlist) < 1:
        dlist = ['local']
    if len(dlist) < 2 and dlist[0] != 'local' and dlist[0] != 'localdomain':
        dlist.insert(0, 'local')
    return '.'.join(dlist)


def get_def_ado_inst() -> str:
    """Get default ado instance.

    Guess a name that might be resonable for internal Azure Dev Ops server.
    """
    return 'devops.' + get_def_domain()


def get_def_internal_pypi() -> str:
    """Get default internal PyPI server.

    Guess a name that might be resonalbe for internal PyPI server.
    (This is an internal server mirroring part of PyPI.org, not PyPI.org.)
    """
    return 'https://pypi.' + get_def_domain()


def get_defaultvals(env_var: str) -> tuple[Optional[str], str]:
    """Get default value and default value help text.

    Trying to be smart about default values and also for many of
    the command line arguments allow the use of environment variables
    to customize what the default varles should be.
    Returns tuple of default value and help text for default value.
    @param env_var Name of enviroment variable that has default value.
    """
    defval = os.getenv(env_var)
    defmap = {'ADO_COLLECTION': 'Python',
              'ADO_PROJECT': None,
              'ADO_TYPES': 'wheel',
              'PATFILE': None,
              'METADATAMAX': '2.2',
              'EXCLUDE_TEXT': 'already in local server',
              'EXCLUDE_CSV': None}
    if defval is None:
        if env_var == 'ADO_INSTANCE':
            defval = get_def_ado_inst()
        elif env_var == 'PYTHON_VER':
            defval = '.'.join([str(i) for i in sys.version_info[0:2]])
        elif env_var == 'INTERNAL_PYPI':
            defval = get_def_internal_pypi()
        else:
            defval = defmap[env_var]
    defvaltxt: str = ''
    if defval is None:
        defvaltxt = 'None'
    else:
        defvaltxt = f'"{defval}"'
    defhelp = f'(Default: {defvaltxt}. Set environment variable '
    defhelp += f'{env_var} to change default value.)'
    return (defval, defhelp)


def add_print_deps_flags(parser: argparse.ArgumentParser) -> None:
    """Add flags for printing recursive dependencies.

    Add flags (and command line arguments) to the command line parser
    for handling the case of printing recursive dependencies on
    (external) pypi.org.
    @parser  The parser of argparse to add the flags to.
    """
    parser.add_argument('-p', '--package', type=str, nargs=1,
                        required=True,
                        help='Package or application to list dependencies ' +
                        'for recursively.')
    defmeta, defmetatxt = get_defaultvals('METADATAMAX')
    parser.add_argument('-m', '--metadatamax',
                        type=str, nargs=1, default=[defmeta],
                        help='Highest allowed metadata version' + defmetatxt)
    defpyt, defpyttxt = get_defaultvals('PYTHON_VER')
    parser.add_argument('-y', '--pythonversion', type=str, nargs=1,
                        default=[defpyt],
                        help='Works on python version. ' + defpyttxt)
    defext, defexttxt = get_defaultvals('EXCLUDE_CSV')
    parser.add_argument('-e', '--excludecsv', type=str, nargs=1,
                        default=defext,
                        help='File name of CSV file with packages and ' +
                        'versions to exclude. Needs to have column ' +
                        'names "Name" and "Version". ' + defexttxt)
    defcsv, defcsvtxt = get_defaultvals('EXCLUDE_TEXT')
    parser.add_argument('-t', '--excludetext', type=str, nargs=1,
                        default=[defcsv],
                        help='Text to include in report with reason for ' +
                        'excluding packages with ---excludecsv. ' +
                        defcsvtxt)


def add_print_deps_subcmd(subparsers: SubParseAct) -> None:
    """Sub-command to print dependencies of a package in PyPI.org.

    Add sub-command and flags (and command line arguments) to the command
    line parser for handling the case of printing information on (recursive)
    dependencies of a package in PyPi.org.
    @subparsers  The subparsers object of argparse to add the sub-command to.
    """
    desc = 'Print all recursive dependencies of a python package.'
    epi = 'Useful to figure out which packages to copy.'
    parser = subparsers.add_parser('printdeps', help=desc,
                                   epilog=epi,
                                   description=desc)
    parser.add_argument('-o', '--output', nargs=1,
                        default=['dependencies.md'],
                        type=str, help='Name of output markdown file. ' +
                        '(Default: dependencies.md).')
    parser.add_argument('-l', '--listpurls', nargs=1,
                        default=[None],
                        type=str, help='Name of file with list of packages ' +
                        'to download in purl format ' +
                        'https://github.com/package-url/purl-spec#purl ' +
                        '(Default: None).')
    add_print_deps_flags(parser=parser)
    parser.set_defaults(func=print_deps_func)


def add_patfile_flags(parser: argparse.ArgumentParser) -> None:
    """Add flag for PAT file.

    Add the command line argument and flag for specifying a file with
    a personal access token.
    @parser  The parser of argparse to add the flag to.
    """
    defpat, defpattxt = get_defaultvals('PATFILE')
    parser.add_argument('-a', '--patfile', nargs=1, type=str,
                        default=[defpat],
                        help='File name of file with personal access token. ' +
                        defpattxt)


def add_list_ado_flags(parser: argparse.ArgumentParser) -> None:
    """Add flags for getting available packages in ADO server.

    Add the command line arguments and flags for getting a list of all
    packages available on an internal Azure Dev Ops server.
    @parser  The parser of argparse to add the flag to.
    """
    definst, definsttxt = get_defaultvals('ADO_INSTANCE')
    parser.add_argument('-s', '--instance', type=str, nargs=1,
                        default=[definst],
                        help='Instance or server name. ' +
                        definsttxt)
    defcoll, defcolltxt = get_defaultvals('ADO_COLLECTION')
    parser.add_argument('-c', '--collection', type=str, nargs=1,
                        default=[defcoll],
                        help='Collection. ' + defcolltxt)
    defproj, defprojtxt = get_defaultvals('ADO_PROJECT')
    parser.add_argument('-p', '--project', default=[defproj], nargs=1,
                        help='Project.' + defprojtxt)
    deftypes, deftypestxt = get_defaultvals('ADO_TYPES')
    parser.add_argument('-i', '--include-types', type=str, nargs=1,
                        default=[deftypes],
                        help='Comma separated list of package types to ' +
                        'include. ' + deftypestxt)
    add_patfile_flags(parser=parser)


def add_list_ado_subcmd(subparsers: SubParseAct) -> None:
    """Sub-command to list python packages in ADO.

    The sub-command that lists python packages in Azure Dev Ops (ADO)
    server.
    @param subparsers The sub-parsers object of argparse.
    """
    desc = 'List python packages in Azure Dev Ops (ADO) server matching'
    desc += ' types.'
    epi = 'Useful when having internal ADO server mirroring '
    epi += 'part of PyPI.org.'
    parser = subparsers.add_parser('listado', help=desc,
                                   epilog=epi,
                                   description=desc)
    parser.add_argument('-o', '--output', nargs=1, default=['ado.csv'],
                        type=str, help='Name of output CSV file ' +
                        '(default: ado.csv).')
    add_list_ado_flags(parser=parser)
    parser.set_defaults(func=list_ado_func)


def add_list_pypi_subcmd(subparsers: SubParseAct) -> None:
    """Sub-ommand to list python packages in internal PyPI.

    The sub-command that lists python packages available in internal PyPi
    server.
    @param subparsers The sub-parsers object of argparse.
    """
    desc = 'List python packages in internal PyPI server.'
    epi = 'Useful when having internal PyPI server mirroring '
    epi += 'part of PyPI.org. Never run this towards pypi.org.'
    parser = subparsers.add_parser('listinternal', help=desc,
                                   epilog=epi,
                                   description=desc)
    defurl, defurltxt = get_defaultvals('INTERNAL_PYPI')
    parser.add_argument('-u', '--url', default=[defurl], nargs=1, type=str,
                        help='Base URL to internal PyPI server. ' + defurltxt)
    parser.add_argument('-o', '--output', nargs=1, default=['internal.csv'],
                        type=str, help='Name of output CSV file ' +
                        '(default: internal.csv).')
    parser.add_argument('-n', '--limitnumber', nargs=1, default=[None],
                        type=int,
                        help='Limit output to this number of packages ' +
                        '(default: None).')
    add_patfile_flags(parser=parser)
    parser.set_defaults(func=list_pypi_func)


def pypkg_recdep_cmd(arguments: Optional[list[str]] = None) -> int:
    """Command pypkg_recdep.

    Create the command line parsing and help texts for the pypkg_recdep
    command.
    @param arguments As optional list of strings that form the command line.
    """
    if arguments is None:  # pragma: no cover
        arguments = sys.argv
    fixed_args = deepcopy(arguments)
    if len(fixed_args) > 2 and 'python' in fixed_args[0]:
        del fixed_args[0]
    if len(fixed_args) > 2 and '-m' == fixed_args[0]:
        del fixed_args[0]
    while len(fixed_args) >= 1 and fixed_args[0][-3:] == '.py':
        del fixed_args[0]
    descr = 'List recursive dependencies of package.'
    epi = 'More detailed help is available for each sub-command.'
    parser = argparse.ArgumentParser(prog='pypkg_recdep', description=descr,
                                     epilog=epi)
    subparsers = parser.add_subparsers(dest='subparser_name', required=True)
    add_list_ado_subcmd(subparsers=subparsers)
    add_print_deps_subcmd(subparsers=subparsers)
    add_list_pypi_subcmd(subparsers=subparsers)
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args=fixed_args)
    ret = args.func(args)
    assert isinstance(ret, int)
    return ret


if __name__ == "__main__":  # pragma: no cover
    pypkg_recdep_cmd()
