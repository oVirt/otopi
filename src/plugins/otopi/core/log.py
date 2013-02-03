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


"""Log plugin."""


import os
import time
import tempfile
import logging
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import plugin


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

        def __init__(
            self,
            fmt=None,
            datefmt=None,
            filter=None,
        ):
            logging.Formatter.__init__(self, fmt=fmt, datefmt=datefmt)
            self._filter = filter

        def format(self, record):
            msg = logging.Formatter.format(self, record)

            if self._filter is not None:
                for f in self._filter._list:
                    msg = msg.replace(f, '**FILTERED**')

            return msg

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._handler = None

    def _setupLogging(self):
        self.environment[constants.CoreEnv.LOG_FILE_HANDLE] = None
        self.environment[constants.CoreEnv.LOG_FILTER] = self._MyLoggerFilter()
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
                    "%s-%s.log" % (
                        self.environment[
                            constants.CoreEnv.LOG_FILE_NAME_PREFIX
                        ],
                        time.strftime("%Y%m%d%H%M%S"),
                    )
                )
            ),
        )

        # put in our environment
        # so when re-exec we use same log
        os.environ[constants.SystemEnvironment.LOG_FILE] = logFileName

        self.environment[constants.CoreEnv.LOG_FILE_HANDLE] = open(
            self.resolveFile(logFileName),
            mode='a',
            buffering=1
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
                datefmt='%Y-%m-%d %H:%M:%S',
                filter=self.environment[constants.CoreEnv.LOG_FILTER],
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
        priority=plugin.Stages.PRIORITY_HIGH,
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
        self.dialog.note(
            _('Log file: {logFileName}').format(
                logFileName=self.environment[constants.CoreEnv.LOG_FILE_NAME]
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_TERMINATE,
        priority=plugin.Stages.PRIORITY_LAST + 1000
    )
    def _terminate(self):
        self._closeLogging()


# vim: expandtab tabstop=4 shiftwidth=4
