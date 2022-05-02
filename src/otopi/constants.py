#
# otopi -- plugable installer
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
    YUM_PACKAGER_BOOT = 'otopi.packagers.yum.boot'
    DIALOG_MISC_BOOT = 'otopi.dialog.misc.boot'
    DIALOG_BOOT_DONE = 'otopi.dialog.boot.done'
    CORE_LOG_INIT = 'otopi.core.log.init'
    CORE_CONFIG_INIT = 'otopi.core.config.init'
    DIALOG_CLI_CUSTOMIZATION = 'otopi.dialog.cli.customization'
    DIALOG_CLI_TERMINATION = 'otopi.dialog.cli.termination'
    SYSTEM_COMMAND_DETECTION = 'otopi.system.command.detection'
    SYSTEM_COMMAND_REDETECTION = 'otopi.system.command.redetection'
    PACKAGERS_DETECTION = 'otopi.packagers.detection'
    FIREWALLD_VALIDATION = 'otopi.network.firewalld.validation'
    IPTABLES_VALIDATION = 'otopi.network.iptables.validation'
    TRANSACTIONS_INIT = 'otopi.core.transactions.init'
    ANSWER_FILE_GENERATED = 'otopi.core.answer.file.generated'


@util.export
class Log(object):
    LOGGER_BASE = 'otopi'


@util.export
class Types(object):
    NONE = 'none'
    BOOLEAN = 'bool'
    INTEGER = 'int'
    STRING = 'str'
    MULTI_STRING = 'multi-str'
    OBJECT = 'object'


@util.export
class Const(object):
    ENVIRONMENT_APPEND_PREFIX = 'APPEND:'
    ENVIRONMENT_PREPEND_PREFIX = 'PREPEND:'
    CONFIG_SECTION_DEFAULT = 'environment:default'
    CONFIG_SECTION_INIT = 'environment:init'
    CONFIG_SECTION_OVERRIDE = 'environment:override'
    CONFIG_SECTION_ENFORCE = 'environment:enforce'
    DIALOG_DIALECT_MACHINE = 'machine'
    DIALOG_DIALECT_HUMAN = 'human'
    EXIT_CODE_SUCCESS = 0
    EXIT_CODE_GENERAL_ERROR = 1
    EXIT_CODE_INITIALIZATION_ERROR = 2
    EXIT_CODE_DEBUG_PACKAGER_ROLLBACK_EXISTS = 101
    EXIT_CODE_DEBUG_PACKAGER_ROLLBACK_MISSING = 102


@util.export
class SystemEnvironment(object):
    DEBUG = 'OTOPI_DEBUG'
    LOG_FILE = 'OTOPI_LOGFILE'
    LOG_DIR = 'OTOPI_LOGDIR'
    CONFIG = 'OTOPI_CONFIG'
    EXEC_DIR = 'OTOPI_EXECDIR'
    WAIT_ON_ERROR = 'OTOPI_WAIT_ON_ERROR'
    FORCE_FAIL_STAGE = 'OTOPI_FORCE_FAIL_STAGE'
    FORCE_FAIL_PRIORITY = 'OTOPI_FORCE_FAIL_PRIORITY'
    TEST_COMMAND = 'OTOPI_TEST_COMMAND'
    ALLOW_PRIORITY_OVERRIDE = 'OTOPI_ALLOW_PRIORITY_OVERRIDE'
    COVERAGE = 'OTOPI_COVERAGE'
    SYS_PATH = 'PATH'
    DNF_ENABLE = 'OTOPI_DNF_ENABLE'


@util.export
class BaseEnv(object):
    ERROR = 'BASE/error'
    ABORTED = 'BASE/aborted'
    EXCEPTION_INFO = 'BASE/exceptionInfo'
    EXIT_CODE = 'BASE/exitCode'
    LOG = 'BASE/log'
    PLUGIN_PATH = 'BASE/pluginPath'
    PLUGIN_GROUPS = 'BASE/pluginGroups'
    DEBUG = 'BASE/debug'
    EXECUTION_DIRECTORY = 'BASE/executionDirectory'
    SUPPRESS_ENVIRONMENT_KEYS = 'BASE/suppressEnvironmentKeys'
    COMMAND_PREFIX = 'COMMAND/'
    RANDOMIZE_EVENTS = 'CORE/randomizeEvents'
    FAIL_ON_PRIO_OVERRIDE = 'CORE/failOnPrioOverride'
    IGNORE_MISSING_BEFORE_AFTER = 'CORE/ignoreMissingBeforeAfter'


@util.export
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
    LOG_FILTER_RE = 'CORE/logFilterRe'
    LOG_FILTER_KEYS = 'CORE/logFilterKeys'
    LOG_FILTER_QUESTIONS = 'CORE/logFilterQuestions'
    LOG_FILTER_QUESTIONS_KEYS = 'CORE/logFilterQuestionsKeys'
    LOG_FILE_HANDLE = 'CORE/logFileHandle'
    LOG_REMOVE_AT_EXIT = 'CORE/logRemoveAtExit'
    CONFIG_FILE_NAME = 'CORE/configFileName'
    CONFIG_FILE_APPEND = 'CORE/configFileAppend'
    VALIDATE_KEYS_FILTERED_EARLY = 'CORE/validateKeysFilteredEarly'
    QUESTION_PREFIX = 'QUESTION/'


@util.export
class DialogEnv(object):
    DIALECT = 'DIALOG/dialect'
    CUSTOMIZATION = 'DIALOG/customization'
    BOUNDARY = 'DIALOG/boundary'
    CLI_VERSION = 'DIALOG/cliVersion'
    AUTO_ACCEPT_DEFAULT = 'DIALOG/autoAcceptDefault'
    ANSWER_FILE = 'DIALOG/answerFile'
    ANSWER_FILE_CONTENT = 'DIALOG/answerFileContent'


@util.export
class SysEnv(object):
    CLOCK_MAX_GAP = 'SYSTEM/clockMaxGap'
    CLOCK_SET = 'SYSTEM/clockSet'
    REBOOT = 'SYSTEM/reboot'
    REBOOT_ALLOW = 'SYSTEM/rebootAllow'
    REBOOT_DEFER_TIME = 'SYSTEM/rebootDeferTime'
    COMMAND_PATH = 'SYSTEM/commandPath'


@util.export
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
class PackEnv(object):
    KEEP_ALIVE_INTERVAL = 'PACKAGER/keepAliveInterval'
    YUMPACKAGER_ENABLED = 'PACKAGER/yumpackagerEnabled'
    YUMPACKAGER_EXPIRE_CACHE = 'PACKAGER/yumExpireCache'
    YUM_DISABLED_PLUGINS = 'PACKAGER/yumDisabledPlugins'
    YUM_ENABLED_PLUGINS = 'PACKAGER/yumEnabledPlugins'
    YUM_ROLLBACK = 'PACKAGER/yumRollback'
    DNFPACKAGER_ENABLED = 'PACKAGER/dnfpackagerEnabled'
    DNFPACKAGER_EXPIRE_CACHE = 'PACKAGER/dnfExpireCache'
    DNF_DISABLED_PLUGINS = 'PACKAGER/dnfDisabledPlugins'
    DNF_ROLLBACK = 'PACKAGER/dnfRollback'


@util.export
class Queries(object):
    CUSTOMIZATION_COMMAND = 'CUSTOMIZATION_COMMAND'
    TERMINATION_COMMAND = 'TERMINATION_COMMAND'
    TIME = 'TIME'


@util.export
class Confirms(object):
    GPG_KEY = 'GPG_KEY'


@util.export
class DebugEnv(object):
    WAIT_ON_ERROR = 'ODEBUG/WaitOnError'
    PACKAGES_ACTION = 'ODEBUG/packagesAction'
    PACKAGES = 'ODEBUG/packages'
    NOTE = 'ODEBUG/note'


# vim: expandtab tabstop=4 shiftwidth=4
