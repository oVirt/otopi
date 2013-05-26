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


"""miniyum interaction."""


import time
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util


from . import miniyum


class _MyMiniYumSink(miniyum.MiniYumSinkBase):
    """miniyum interaction."""

    def _touch(self):
        self._last = time.time()

    def __init__(self, parent):
        super(_MyMiniYumSink, self).__init__()
        self._parent = parent
        self._touch()

    def verbose(self, msg):
        super(_MyMiniYumSink, self).verbose(msg)
        self._parent.logger.debug('Yum %s' % msg)

    def info(self, msg):
        super(_MyMiniYumSink, self).info(msg)
        self._parent.logger.info('Yum %s' % msg)
        self._touch()

    def error(self, msg):
        super(_MyMiniYumSink, self).error(msg)
        self._parent.logger.error('Yum %s' % msg)
        self._touch()

    def keepAlive(self, msg):
        super(_MyMiniYumSink, self).keepAlive(msg)
        if time.time() - self._last >= self._parent.environment[
            constants.PackEnv.KEEP_ALIVE_INTERVAL
        ]:
            self.info(msg)

    def askForGPGKeyImport(self, userid, hexkeyid):
        return self._parent.dialog.confirm(
            constants.Confirms.GPG_KEY,
            _(
                'Confirm use of GPG Key '
                'userid={userid} hexkeyid={hexkeyid}'
            ).format(
                userid=userid,
                hexkeyid=hexkeyid,
            )
        )

    def reexec(self):
        super(_MyMiniYumSink, self).reexec()
        self._parent.context.notify(self._parent.context.NOTIFY_REEXEC)


@util.export
def getMiniYum(
    parent,
    disabledPlugins=[],
    enabledPlugins=[]
):
    """Get miniyum objects at separate source to ease making it optional."""
    return miniyum.MiniYum(
        sink=_MyMiniYumSink(parent=parent),
        blockStdHandles=False,
        disabledPlugins=disabledPlugins,
        enabledPlugins=enabledPlugins,
    )


# vim: expandtab tabstop=4 shiftwidth=4
