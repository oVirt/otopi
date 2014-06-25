#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""Constants."""


from . import util


@util.export
class Defaults(object):
    LOG_FILE_PREFIX = 'otopi'
    CONFIG_FILE = '/etc/otopi.conf'
    COMMAND_SEARCH_PATH = ":".join(
        (
            '/usr/local/sbin',
            '/usr/local/bin',
            '/usr/sbin',
            '/usr/bin',
            '/sbin',
            '/bin',
        )
    )
    PACKAGER_KEEP_ALIVE_INTERVAL = 30


@util.export
class Stages(object):
    CORE_LOG_INIT = 'otopi.core.log.init'
    CORE_CONFIG_INIT = 'otopi.core.config.init'
    DIALOG_CLI_CUSTOMIZATION = 'otopi.dialog.cli.customization'
    DIALOG_CLI_TERMINATION = 'otopi.dialog.cli.termination'
    SYSTEM_COMMAND_DETECTION = 'otopi.system.command.detection'
    SYSTEM_COMMAND_REDETECTION = 'otopi.system.command.redetection'
    PACKAGERS_DETECTION = 'otopi.packagers.detection'
    FIREWALLD_VALIDATION = 'otopi.network.firewalld.validation'
    IPTABLES_VALIDATION = 'otopi.network.iptables.validation'


@util.export
class Log(object):
    LOGGER_BASE = 'otopi'


@util.export
@util.codegen
class Types(object):
    NONE = 'none'
    BOOLEAN = 'bool'
    INTEGER = 'int'
    STRING = 'str'
    MULTI_STRING = 'multi-str'
    OBJECT = 'object'


@util.export
@util.codegen
class Const(object):
    ENVIRONMENT_APPEND_PREFIX = 'APPEND:'
    ENVIRONMENT_PREPEND_PREFIX = 'PREPEND:'
    CONFIG_SECTION_DEFAULT = 'environment:default'
    CONFIG_SECTION_INIT = 'environment:init'
    CONFIG_SECTION_OVERRIDE = 'environment:override'
    CONFIG_SECTION_ENFORCE = 'environment:enforce'
    DIALOG_DIALECT_MACHINE = 'machine'
    DIALOG_DIALECT_HUMAN = 'human'


@util.export
@util.codegen
class SystemEnvironment(object):
    DEBUG = 'OTOPI_DEBUG'
    LOG_FILE = 'OTOPI_LOGFILE'
    LOG_DIR = 'OTOPI_LOGDIR'
    CONFIG = 'OTOPI_CONFIG'
    EXEC_DIR = 'OTOPI_EXECDIR'


@util.export
@util.codegen
class BaseEnv(object):
    ERROR = 'BASE/error'
    ABORTED = 'BASE/aborted'
    EXCEPTION_INFO = 'BASE/exceptionInfo'
    LOG = 'BASE/log'
    PLUGIN_PATH = 'BASE/pluginPath'
    PLUGIN_GROUPS = 'BASE/pluginGroups'
    DEBUG = 'BASE/debug'
    EXECUTION_DIRECTORY = 'BASE/executionDirectory'
    SUPPRESS_ENVIRONMENT_KEYS = 'BASE/suppressEnvironmentKeys'
    COMMAND_PREFIX = 'COMMAND/'
    RANDOMIZE_EVENTS = 'CORE/randomizeEvents'
    FAIL_ON_PRIO_OVERRIDE = 'CORE/failOnPrioOverride'


@util.export
@util.codegen
class CoreEnv(object):
    PACKAGE_NAME = 'INFO/PACKAGE_NAME'
    PACKAGE_VERSION = 'INFO/PACKAGE_VERSION'
    INTERNAL_PACKAGES_TRANSACTION = 'CORE/internalPackageTransaction'
    MAIN_TRANSACTION = 'CORE/mainTransaction'
    MODIFIED_FILES = 'CORE/modifiedFiles'
    LOG_FILE_NAME_PREFIX = 'CORE/logFileNamePrefix'
    LOG_DIR = 'CORE/logDir'
    LOG_FILE_NAME = 'CORE/logFileName'
    LOG_FILTER = 'CORE/logFilter'
    LOG_FILTER_KEYS = 'CORE/logFilterKeys'
    LOG_FILE_HANDLE = 'CORE/logFileHandle'
    LOG_REMOVE_AT_EXIT = 'CORE/logRemoveAtExit'
    CONFIG_FILE_NAME = 'CORE/configFileName'
    CONFIG_FILE_APPEND = 'CORE/configFileAppend'


@util.export
@util.codegen
class DialogEnv(object):
    DIALECT = 'DIALOG/dialect'
    CUSTOMIZATION = 'DIALOG/customization'
    BOUNDARY = 'DIALOG/boundary'
    CLI_VERSION = 'DIALOG/cliVersion'


@util.export
@util.codegen
class SysEnv(object):
    CLOCK_MAX_GAP = 'SYSTEM/clockMaxGap'
    CLOCK_SET = 'SYSTEM/clockSet'
    REBOOT = 'SYSTEM/reboot'
    REBOOT_ALLOW = 'SYSTEM/rebootAllow'
    REBOOT_DEFER_TIME = 'SYSTEM/rebootDeferTime'
    COMMAND_PATH = 'SYSTEM/commandPath'


@util.export
@util.codegen
class NetEnv(object):
    SSH_ENABLE = 'NETWORK/sshEnable'
    SSH_KEY = 'NETWORK/sshKey'
    SSH_USER = 'NETWORK/sshUser'
    IPTABLES_ENABLE = 'NETWORK/iptablesEnable'
    IPTABLES_RULES = 'NETWORK/iptablesRules'
    FIREWALLD_ENABLE = 'NETWORK/firewalldEnable'
    FIREWALLD_AVAILABLE = 'NETWORK/firewalldAvailable'
    FIREWALLD_SERVICE_PREFIX = 'NETWORK_FIREWALLD_SERVICE/'
    FIREWALLD_DISABLE_SERVICES = 'NETWORK/firewalldDisableServices'


@util.export
@util.codegen
class PackEnv(object):
    YUMPACKAGER_ENABLED = 'PACKAGER/yumpackagerEnabled'
    YUMPACKAGER_EXPIRE_CACHE = 'PACKAGER/yumExpireCache'
    KEEP_ALIVE_INTERVAL = 'PACKAGER/keepAliveInterval'
    YUM_DISABLED_PLUGINS = 'PACKAGER/yumDisabledPlugins'
    YUM_ENABLED_PLUGINS = 'PACKAGER/yumEnabledPlugins'
    YUM_ROLLBACK = 'PACKAGER/yumRollback'


@util.export
@util.codegen
class Queries(object):
    CUSTOMIZATION_COMMAND = 'CUSTOMIZATION_COMMAND'
    TERMINATION_COMMAND = 'TERMINATION_COMMAND'
    TIME = 'TIME'


@util.export
@util.codegen
class Confirms(object):
    GPG_KEY = 'GPG_KEY'


# vim: expandtab tabstop=4 shiftwidth=4
