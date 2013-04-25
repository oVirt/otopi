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


"""OpenRC services provider"""


import os
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import services


@util.export
class Plugin(plugin.PluginBase, services.ServicesBase):
    """OpenRC services provider"""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('rc')
        self.command.detect('rc-update')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        after=[
            constants.Stages.SYSTEM_COMMAND_DETECTION,
        ],
    )
    def _programs(self):
        rc = self.command.get('rc', optional=True)
        if rc is not None:
            (ret, stdout, stderr) = self.execute(
                (rc, '--version'),
                raiseOnError=False,
            )
            if ret == 0 and len(stdout) == 1 and 'OpenRC' in stdout[0]:
                self.logger.debug('registering OpenRC provider')
                self.context.registerServices(services=self)

    #
    # ServicesBase
    #

    def _getServiceScript(self, name):
        return os.path.join('/etc/init.d', name)

    def _executeServiceCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (self._getServiceScript(name), '-q', command),
            raiseOnError=raiseOnError
        )

    @property
    def setSupportsDependency(self):
        return True

    def exists(self, name):
        self.logger.debug('check if service %s exists', name)
        return os.path.exists(self._getServiceScript(name))

    def status(self, name):
        self.logger.debug('check service %s status', name)
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            'status',
            raiseOnError=False
        )
        return rc == 0

    def startup(self, name, state):
        self.logger.debug('set service %s startup to %s', name, state)
        self.execute(
            (
                self.command.get('rc-update'),
                'add' if state else 'del',
                name
            ),
            raiseOnError=False,
        )

    def state(self, name, state):
        self.logger.debug(
            '%s service %s',
            'starting' if state else 'stopping',
            name
        )
        self._executeServiceCommand(
            name,
            'start' if state else 'stop'
        )


# vim: expandtab tabstop=4 shiftwidth=4
