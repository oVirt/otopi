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


"""otopi main class."""


import gettext
import logging
import os
import signal
import sys


from otopi import common
from otopi import constants
from otopi import context
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class PluginLoadException(Exception):
    pass


@util.export
class Otopi(object):
    """otopi bootstrap.

    Methods of execution:
    - Locally installed.
    - Bundled and executed from temporary directory.
    - Development tree execution.

    """
    @property
    def context(self):
        """Context."""
        return self._context

    @staticmethod
    def _signal(signum, frame):
        raise RuntimeError("SIG%s" % signum)

    def _setupLogger(self):
        class NullHandler(logging.Handler):
            """Simple NullHandler.

            Avoid python-2.7 warning:

            'No handlers could be found for logger'

            Needed as NullHandler is does not exit in python-2.6.

            Resolved at python-3.0.

            """
            def __init__(self):
                # python2-6 has not real object
                # super(NullHandler, self).__init__()
                logging.Handler.__init__(self)

            def emit(self, record):
                pass

        logger = logging.getLogger(constants.Log.LOGGER_BASE)
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
        logger.addHandler(NullHandler())

    def _setupGettext(self):
        """Setup gettext domains within bundled package."""
        if self._bundledir:
            domains = []

            for (__, __, files) in os.walk(
                top=os.path.join(
                    self._bundledir,
                    'locale'
                )
            ):
                domains.extend([
                    f.replace('.mo', '')
                    for f in files
                    if f.endswith('.mo')
                ])

            for domain in set(domains):
                gettext.bindtextdomain(
                    domain=domain,
                    localedir=os.path.join(
                        self._bundledir,
                        'locale'
                    )
                )

    @property
    def environment(self):
        """Environment."""
        return self.context.environment

    def __init__(self):
        for i in (
            signal.SIGABRT,
            signal.SIGHUP,
            signal.SIGINT,
            signal.SIGPIPE,
            signal.SIGQUIT,
            signal.SIGTERM,
            signal.SIGIO,
        ):
            try:
                signal.signal(i, self._signal)
            except:
                pass

        self._debug = int(
            os.environ.get(
                constants.SystemEnvironment.DEBUG,
                0
            )
        )
        self._bundledir = os.environ.get(
            'OTOPI_BUNDLED',
            ''
        )
        self._insource = '0' != os.environ.get(
            'OTOPI_INSOURCETREE',
            '0'
        )
        self._setupLogger()
        self._setupGettext()
        self._context = context.Context()

    def execute(self):
        try:
            self.context.loadPlugins()
        except Exception as e:
            util.raiseExceptionInformation(
                info=(
                    PluginLoadException,
                    PluginLoadException(common.toStr(e)),
                    sys.exc_info()[2],
                )
            )
        self.context.buildSequence()
        self.context.runSequence()


# vim: expandtab tabstop=4 shiftwidth=4
