otopi-config-query -- configuration query tool
==============================================

ABOUT
-----

The otopi-config-query script is a helper tool to make it easier to handle
otopi-generated configuration files from shell scripts.

It allows users to match values with the content of configuration files and
to query values from configuration files. More actions can be added in the
future.


COMMAND LINE
------------

otopi-config-query implements two actions:

  - match
  - query


Action: match
~~~~~~~~~~~~~

This action will try to match an user-provided value with the value found in
configuration files for a given key.

The tool will return the following return codes:

  - 0, if user-provided value matches with value found in configuration
    file.
  - 1, if key exists in configuration file, but user-provided value does
    not match with value found in configuration file.
  - 2, if requested key/section does not exists in configuration file, or
    if no configuration file was found.

The tool will also raise a Python exception warning the user, if the value
provided is malformed:

  - ValueError, if user-provided value does not have an otopi-supported
    variable type, in the format <type>:<value>
  - KeyError, if user-provided value contains invalid variable type.


Usage: otopi-config-query match [-h] [-s SECTION] -k KEY -v VALUE -f FILE

Options:
  -h, --help                     show this help message and exit
  -s SECTION, --section SECTION  Configuration section, defaults to
                                 'environment:default'
  -k KEY, --key KEY              Configuration key
  -v VALUE, --value VALUE        Configuration value, in the format
                                 <type>:<value>
  -f FILE, --file FILE           Configuration file. Will also look for
                                 *.conf files inside <FILE>.d directory, if
                                 exists


Examples:

Check if ovirt-engine is enabled for a host:

    $ otopi-config-query match \
          --key OVESETUP_ENGINE_CORE/enable \
          --value bool:True \
          --file /etc/ovirt-engine-setup.conf
    $ echo $?
    0

Check if ovirt-engine is using firewalld as the firewall manager:

    $ otopi-config-query match \
          --key OVESETUP_CONFIG/firewallManager \
          --value str:firewalld \
          --file /etc/ovirt-engine-setup.conf
    $ echo $?
    0

Check for invalid key:

    $ otopi-config-query match \
          --key OVESETUP_CONFIG/firewallManager2 \
          --value str:firewalld \
          --file /etc/ovirt-engine-setup.conf
    $ echo $?
    2

Check for non-existing configuration file:

    $ otopi-config-query match \
          --key OVESETUP_CONFIG/firewallManager \
          --value str:firewalld \
          --file /etc/ovirt-engine-setup2.conf
    $ echo $?
    2

Check for invalid variable type:

    $ otopi-config-query match \
          --key OVESETUP_CONFIG/firewallManager \
          --value st:firewalld \
          --file /etc/ovirt-engine-setup.conf
    Traceback (most recent call last):
      File "/usr/bin/otopi-config-query", line 197, in <module>
        sys.exit(main())
      File "/usr/bin/otopi-config-query", line 191, in main
        rv = args.callback(args)
      File "/usr/bin/otopi-config-query", line 93, in do_match
        user_value = common.parseTypedValue(args.value)
      File "/usr/lib/python2.7/site-packages/otopi/common.py", line 42, in parseTypedValue
        type=vtype
    KeyError: 'Invalid variable type st'

Check for variable without type:

    $ otopi-config-query match \
          --key OVESETUP_CONFIG/firewallManager \
          --value firewalld \
          --file /etc/ovirt-engine-setup.conf
    Traceback (most recent call last):
      File "/usr/bin/otopi-config-query", line 197, in <module>
        sys.exit(main())
      File "/usr/bin/otopi-config-query", line 191, in main
        rv = args.callback(args)
      File "/usr/bin/otopi-config-query", line 93, in do_match
        user_value = common.parseTypedValue(args.value)
      File "/usr/lib/python2.7/site-packages/otopi/common.py", line 27, in parseTypedValue
        raise ValueError(_("Missing variable type"))
    ValueError: Missing variable type


Action: query
~~~~~~~~~~~~~

This action will look for a given key in the configuration files, and print
it, if found.

The tool will return the following return codes:

  - 0, on success, and prints the value found in the configuration file,
    with the type, if requested by user with --with-type.

The tool will also raise a Python exception, if something wrong happens:

  - configparser.NoOptionError, configparser.NoSectionError, if
    key/section does not exists in configuration file.
  - FileNotFound, if no configuration file is found.


Usage: otopi-config-query query [-h] [-t] [-s SECTION] -k KEY -f FILE

Options:
  -h, --help                     show this help message and exit
  -t, --with-type                Return configuration value with type
  -s SECTION, --section SECTION  Configuration section, defaults to
                                 'environment:default'
  -k KEY, --key KEY              Configuration key
  -f FILE, --file FILE           Configuration file. Will also look for
                                 *.conf files inside <FILE>.d directory, if
                                 exists


Examples:

Get ovirt-engine-setup version used to install ovirt-engine (with variable type):

    $ otopi-config-query query \
          --key OVESETUP_CORE/generatedByVersion \
          --file /etc/ovirt-engine-setup.conf \
          --with-type
    str:4.0.0_master

Get ISO NFS domain storage directory:

    $ otopi-config-query query \
          --key OVESETUP_CONFIG/isoDomainStorageDir \
          --file /etc/ovirt-engine-setup.conf
    /var/lib/exports/iso/b991c2df-eafe-431e-956c-3537efb81407/images/11111111-1111-1111-1111-111111111111

Get value of invalid key:

    $ otopi-config-query query \
          --key OVESETUP_CONFIG/isoDomainStorageDir2 \
          --file /etc/ovirt-engine-setup.conf
    Traceback (most recent call last):
      File "/usr/bin/otopi-config-query", line 197, in <module>
        sys.exit(main())
      File "/usr/bin/otopi-config-query", line 191, in main
        rv = args.callback(args)
      File "/usr/bin/otopi-config-query", line 58, in do_query
        value = config.get(args.section, args.key)
      File "/usr/lib64/python2.7/ConfigParser.py", line 618, in get
        raise NoOptionError(option, section)
    ConfigParser.NoOptionError: No option 'OVESETUP_CONFIG/isoDomainStorageDir2' in section: 'environment:default'

Get value from non-existing configuration file:

    $ otopi-config-query query \
          --key OVESETUP_CONFIG/isoDomainStorageDir \
          --file /etc/ovirt-engine-setup2.conf
    Traceback (most recent call last):
      File "/usr/bin/otopi-config-query", line 197, in <module>
        sys.exit(main())
      File "/usr/bin/otopi-config-query", line 191, in main
        rv = args.callback(args)
      File "/usr/bin/otopi-config-query", line 57, in do_query
        config = get_configparser(args.file)
      File "/usr/bin/otopi-config-query", line 43, in get_configparser
        raise FileNotFound('No configuration file found')
    __main__.FileNotFound: No configuration file found


FILE LOADER BEHAVIOR
--------------------

The tool uses a custom file loader, that reads the file asked by user,
and also looks for a directory named as <FILE>.d, and loads all .conf
files found in such directory, after loading the "main" file itself.
The files in the directory are loaded in alphabetical order.
