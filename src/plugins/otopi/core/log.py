#
# otopi -- plugable installer
#


"""Log plugin."""


from datetime import datetime
import gettext
import logging
import os
import random
import re
import string
import tempfile
import time


from otopi import common
from otopi import constants
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


def _get_tz_from_os():
    import subprocess

    p = subprocess.Popen(
        args=(
            '/bin/date',
            '+%z',
        ),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
    )
    stdout, stderr = p.communicate()
    stdout = stdout.decode('utf-8', 'replace').splitlines()
    stderr = stderr.decode('utf-8', 'replace').splitlines()
    if p.returncode != 0:
        tz = 'UnknownTZ'
    else:
        tz = stdout[0].rstrip('\n')
    return tz


@util.export
class Plugin(plugin.PluginBase):
    """Log provier.

    Log is based on standard python logging.

    Environment:
        CoreEnv.LOG_FILE_HANDLE -- opened handle.
        CoreEnv.LOG_DIR -- log directory.
        CoreEnv.LOG_FILE_NAME_REFIX -- file name prefix.
        CoreEnv.LOG_FILE_NAME -- file name.
        CoreEnv.LOG_FILTER -- list of strings to flter out.
        CoreEnv.LOG_REMOVE_AT_EXIT -- True if to remove log.

    OS Environment:
        SystemEnvironment.LOG_FILE -- log file name, default self genmerate.
        SystemEnvironment.LOG_DIR -- log directory, default is tempdir.

    """
    class _MyLoggerFilter(object):
        """List wrapper to not expose content by str()"""

        def __init__(self):
            self._list = []

        def append(self, string):
            self._list.append(string)

        def __str__(self):
            return 'filter'

    class _MyFormatter(logging.Formatter):
        """Filter strings from log entries."""

        @property
        def environment(self):
            return self._environment

        def _filter(self, content, tokens, regexps):
            """
            Filter overlapping tokens within content.
            regexps is a list of regexp objects, each having a group named
            'filter'. The content of this group will be filtered.

            Examples:
            content=abcabca, tokens=('abca')
            content=aaabbbccc, tokens=('bbb', 'abbba')
            content=aaaababbbb, tokens=('aaab', 'aaa', 'bbb')
            content=a BS some secret ES b, regexps=('BS (?P<filter>.*) ES')
            """

            def _insertFilter(content, begin, end):
                return content[:begin] + '**FILTERED**' + content[end:]

            tofilter = []

            for token in tokens:
                if token not in (None, ''):
                    index = -1
                    while True:
                        index = content.find(token, index+1)
                        if index == -1:
                            break
                        tofilter.append((index, index + len(token)))

            for reobj in regexps:
                if reobj is not None:
                    index = -1
                    while True:
                        matchobj = reobj.search(content, index)
                        if matchobj is None:
                            break
                        index = matchobj.start('filter')
                        tofilter.append((index, matchobj.end('filter')))

            tofilter = sorted(tofilter, key=lambda e: e[1], reverse=True)
            begin = None
            end = None
            for entry in tofilter:
                if begin is None or entry[1] < begin:
                    if begin is not None:
                        content = _insertFilter(content, begin, end)
                    begin = entry[0]
                    end = entry[1]
                elif entry[0] < begin:
                    begin = entry[0]
            else:
                if begin is not None:
                    content = _insertFilter(content, begin, end)

            return content

        def __init__(
            self,
            fmt=None,
            datefmt=None,
            environment=None,
        ):
            logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)
            self._environment = environment

        def converter(self, timestamp):
            return datetime.fromtimestamp(
                timestamp,
                self._tzlocal
            )

        def _formatTime_dateutil(self, record, datefmt=None):
            ct = self.converter(record.created)
            if datefmt:
                s = ct.strftime(datefmt, ct)
            else:
                s = "%s,%03d%s" % (
                    ct.strftime('%Y-%m-%d %H:%M:%S'),
                    record.msecs,
                    ct.strftime('%z')
                )
            return s

        def _formatTimeOS(self, record, datefmt=None):
            # Ignore datefmt if we do not have dateutil
            ct = datetime.fromtimestamp(record.created)
            return "%s,%03d%s" % (
                ct.strftime('%Y-%m-%d %H:%M:%S'),
                record.msecs,
                self._os_tz
            )

        try:
            from dateutil import tz
            _tzlocal = tz.tzlocal()
            formatTime = _formatTime_dateutil
        except ImportError:
            _os_tz = _get_tz_from_os()
            formatTime = _formatTimeOS

        def format(self, record):
            return self._filter(
                content=logging.Formatter.format(self, record),
                tokens=(
                    self.environment[constants.CoreEnv.LOG_FILTER]._list +
                    [
                        self.environment.get(k, None) for k in
                        self.environment[constants.CoreEnv.LOG_FILTER_KEYS]
                    ]
                ),
                regexps=self.environment[constants.CoreEnv.LOG_FILTER_RE],
            )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._handler = None
        self._logerror = None
        self.environment[constants.CoreEnv.LOG_FILTER_KEYS] = []

    def _setupLogging(self):
        self.environment[constants.CoreEnv.LOG_FILE_HANDLE] = None
        self.environment[constants.CoreEnv.LOG_FILTER] = self._MyLoggerFilter()
        self.environment[constants.CoreEnv.LOG_FILTER_RE] = []
        self.environment[
            constants.CoreEnv.LOG_FILTER_RE
        ].append(
            re.compile(
                flags=re.VERBOSE | re.DOTALL,
                pattern=r"""
                    BEGIN\ PRIVATE\ KEY
                    (?P<filter>.*)
                    END\ PRIVATE\ KEY
                """,
            )
        )
        self.environment.setdefault(
            constants.CoreEnv.LOG_FILE_NAME_PREFIX,
            constants.Defaults.LOG_FILE_PREFIX
        )

        #
        # Allow system environment to override both
        # the log dir and the log file
        #
        self.environment[constants.CoreEnv.LOG_DIR] = os.environ.get(
            constants.SystemEnvironment.LOG_DIR,
            self.environment.get(
                constants.CoreEnv.LOG_DIR,
                tempfile.gettempdir(),
            ),
        )

        logFileName = self.environment[
            constants.CoreEnv.LOG_FILE_NAME
        ] = os.environ.get(
            constants.SystemEnvironment.LOG_FILE,
            self.environment.get(
                constants.CoreEnv.LOG_FILE_NAME,
                os.path.join(
                    self.environment[constants.CoreEnv.LOG_DIR],
                    "%s-%s-%s.log" % (
                        self.environment[
                            constants.CoreEnv.LOG_FILE_NAME_PREFIX
                        ],
                        time.strftime("%Y%m%d%H%M%S"),
                        ''.join(
                            [
                                random.choice(
                                    string.ascii_lowercase +
                                    string.digits
                                ) for i in range(6)
                            ]
                        )
                    )
                )
            ),
        )

        logFileName = self.resolveFile(logFileName)

        # put in our environment
        # so when re-exec we use same log
        os.environ[constants.SystemEnvironment.LOG_FILE] = logFileName

        try:
            self.environment[constants.CoreEnv.LOG_FILE_HANDLE] = open(
                logFileName,
                mode='a',
                buffering=1,
            )
        except IOError as e:
            self._logerror = common.toStr(e)
            self.environment[constants.CoreEnv.LOG_FILE_HANDLE] = open(
                os.devnull,
                mode='a',
                buffering=1,
            )

        self._handler = logging.StreamHandler(
            self.environment[constants.CoreEnv.LOG_FILE_HANDLE]
        )
        self._handler.setLevel(logging.DEBUG)
        self._handler.setFormatter(
            self._MyFormatter(
                fmt=(
                    '%(asctime)s %(levelname)s %(name)s '
                    '%(module)s.%(funcName)s:%(lineno)d '
                    '%(message)s'
                ),
                environment=self.environment,
            )
        )
        l = logging.getLogger("otopi")
        l.addHandler(self._handler)

    def _closeLogging(self):
        if self._handler is not None:
            l = logging.getLogger("otopi")
            l.removeHandler(self._handler)
            self._handler.close()
            self._handler = None

        if (
            self.environment.setdefault(
                constants.CoreEnv.LOG_FILE_HANDLE,
                None
            ) is not None
        ):
            self.environment[constants.CoreEnv.LOG_FILE_HANDLE].close()
            self.environment[constants.CoreEnv.LOG_FILE_HANDLE] = None

        if (
            self.environment.setdefault(
                constants.CoreEnv.LOG_REMOVE_AT_EXIT,
                False
            ) and
            self.environment.setdefault(
                constants.CoreEnv.LOG_FILE_NAME,
                None
            ) is not None
        ):
            try:
                os.unlink(self.environment[constants.CoreEnv.LOG_FILE_NAME])
            except OSError:
                pass

    def _notification(self, event):
        if event == self.context.NOTIFY_REEXEC:
            self._closeLogging()

    @plugin.event(
        name=constants.Stages.CORE_LOG_INIT,
        stage=plugin.Stages.STAGE_BOOT,
    )
    def _init(self):
        self._setupLogging()
        self.environment[constants.BaseEnv.LOG] = True
        self.environment.setdefault(
            constants.CoreEnv.LOG_REMOVE_AT_EXIT,
            False
        )

        self.context.registerNotification(self._notification)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _setup(self):
        if self._logerror:
            self.logger.warning(
                _("Cannot open log file '{logFileName}': {error}").format(
                    logFileName=self.environment[
                        constants.CoreEnv.LOG_FILE_NAME
                    ],
                    error=self._logerror,
                )
            )
        else:
            self.dialog.note(
                _('Log file: {logFileName}').format(
                    logFileName=self.environment[
                        constants.CoreEnv.LOG_FILE_NAME
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_TERMINATE,
        priority=plugin.Stages.PRIORITY_LAST + 1000
    )
    def _terminate(self):
        self._closeLogging()


# vim: expandtab tabstop=4 shiftwidth=4
