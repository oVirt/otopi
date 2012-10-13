#
# otopi -- plugable installer
# Copyright (C) 2012 Red Hat, Inc.
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


"""System information plugin."""


import sys
import platform
import socket
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import util
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """Misc plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        priority=plugin.Stages.PRIORITY_LOW,
    )
    def _init(self):
        self.logger.debug('SYSTEM INFORMATION - BEGIN')
        self.logger.debug('executable %s', sys.executable)
        self.logger.debug('python %s', sys.executable)
        self.logger.debug('platform %s', sys.platform)
        self.logger.debug('distribution %s', platform.linux_distribution())
        self.logger.debug("host '%s'", socket.gethostname())
        self.logger.debug('SYSTEM INFORMATION - END')
