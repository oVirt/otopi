# coding: utf-8
#
# otopi -- plugable installer
#

from __future__ import print_function

import glob
import os
import sys

# this is a hack to run from source tree. should we keep it?
current_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.isdir(os.path.join(os.path.dirname(current_dir), 'otopi')):
    sys.path.insert(0, os.path.dirname(current_dir))


try:
    import configparser
except ImportError:
    import ConfigParser as configparser

from otopi import common, constants


class FileNotFound(RuntimeError):
    pass


def get_configparser(file):
    config = configparser.ConfigParser()
    config.optionxform = str
    files = []
    if os.path.isfile(file):
        files.append(file)
    files += sorted(
        glob.glob(
            os.path.join('%s.d' % file, '*.conf')
        )
    )
    if not config.read(files):
        raise FileNotFound('No configuration file found')
    return config


def do_query(args):
    '''
    Returns:
        - 0, on success, and prints the value found in the configuration file,
          with the type, if requested by user with --with-type.
    Raises:
        - configparser.NoOptionError, configparser.NoSectionError, if
          key/section does not exists in configuration file.
        - FileNotFound, if no configuration file is found.
    '''
    config = get_configparser(args.file)
    value = config.get(args.section, args.key)
    if args.with_type:
        print(value)
    else:
        print(common.parseTypedValue(value))
    return 0


def do_match(args):
    '''
    Returns:
        - 0, if user-provided value matches with value found in configuration
          file.
        - 1, if key exists in configuration file, but user-provided value does
          not matche with value found in configuration file.
        - 2, if requested key/section does not exists in configuration file, or
          if no configuration file was found.
    Raises:
        - ValueError, if user-provided value does not have an otopi-supported
          variable type, in the format <type>:<value>
        - KeyError, if user-provided value contains invalid variable type.
    '''
    rv = 0

    try:
        config = get_configparser(args.file)
        value = config.get(args.section, args.key)
    except (
        configparser.NoOptionError,
        configparser.NoSectionError,
        FileNotFound
    ):
        rv = 2
    else:
        value = common.parseTypedValue(value)
        user_value = common.parseTypedValue(args.value)
        if value != user_value:
            rv = 1

    return rv


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='otopi configuration query tool'
    )

    actions = parser.add_subparsers(title='actions')

    match = actions.add_parser(
        'match',
        help='Match configuration values in files'
    )
    match.add_argument(
        '-s',
        '--section',
        metavar='SECTION',
        default=constants.Const.CONFIG_SECTION_DEFAULT,
        help="Configuration section, defaults to '%s'" % (
            constants.Const.CONFIG_SECTION_DEFAULT,
        ),
    )
    match.add_argument(
        '-k',
        '--key',
        metavar='KEY',
        required=True,
        help='Configuration key',
    )
    match.add_argument(
        '-v',
        '--value',
        metavar='VALUE',
        required=True,
        help='Configuration value, in the format <type>:<value>',
    )
    match.add_argument(
        '-f',
        '--file',
        metavar='FILE',
        required=True,
        help=(
            'Configuration file. Will also look for *.conf files inside '
            '<FILE>.d directory, if exists'
        ),
    )
    match.set_defaults(callback=do_match)

    query = actions.add_parser(
        'query',
        help='Query configuration values in files'
    )
    query.add_argument(
        '-t',
        '--with-type',
        action='store_true',
        help='Return configuration value with type'
    )
    query.add_argument(
        '-s',
        '--section',
        metavar='SECTION',
        default=constants.Const.CONFIG_SECTION_DEFAULT,
        help="Configuration section, defaults to '%s'" % (
            constants.Const.CONFIG_SECTION_DEFAULT,
        ),
    )
    query.add_argument(
        '-k',
        '--key',
        metavar='KEY',
        required=True,
        help='Configuration key',
    )
    query.add_argument(
        '-f',
        '--file',
        metavar='FILE',
        required=True,
        help=(
            'Configuration file. Will also look for *.conf files inside '
            '<FILE>.d directory, if exists'
        ),
    )
    query.set_defaults(callback=do_query)

    args = parser.parse_args()

    rv = 0

    if hasattr(args, 'callback') and args.callback is not None:
        rv = args.callback(args)

    return rv


if __name__ == '__main__':
    sys.exit(main())
