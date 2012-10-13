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


"""rhel services provider."""


import os
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import util
from otopi import plugin
from otopi import services


@util.export
class Plugin(plugin.PluginBase, services.ServicesBase):
    """rhel services provider."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('service')
        self.command.detect('chkconfig')
        self.command.detect('systemctl')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _validation(self):
        haveSystemd = False
        systemctl = self.command.get('systemctl', optional=True)
        if systemctl is not None:
            (ret, stdout, stderr) = self.execute(
                (systemctl, 'show-environment'),
                raiseOnError=False,
            )
            if ret == 0:
                haveSystemd = True

        if (
            not haveSystemd and
            self.command.get('service', optional=True) is not None
        ):
            self.logger.debug('registering rhel provider')
            self.context.registerServices(services=self)

    #
    # ServicesBase
    #

    def _executeServiceCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (
                self.command.get('service'),
                name,
                command
            ),
            raiseOnError=raiseOnError
        )

    def exists(self, name):
        self.logger.debug('check if service %s exists', name)
        return os.path.exists(os.path.join('/etc/rc.d/init.d', name))

    def status(self, name):
        self.logger.debug('check service %s status', name)
        (rc, stdout, stderr) = self._executeServiceCommand(
            name,
            'status',
            raiseOnError=False
        )
        return rc == 0

    def startup(self, name, state):
        self.logger.debug('set service %s startup to %s', name, state)
        return self.execute(
            (
                self.command.get('chkconfig'),
                name,
                'on' if state else 'off',
            ),
        )

    def state(self, name, state):
        self.logger.debug('starting service %s', name)
        self._executeServiceCommand(
            name,
            'start' if state else 'stop'
        )
