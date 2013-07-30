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


"""systemd services provider."""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import services


@util.export
class Plugin(plugin.PluginBase, services.ServicesBase):
    """systemd services provider."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('systemctl')

    @plugin.event(
        stage=plugin.Stages.STAGE_PROGRAMS,
        after=(
            constants.Stages.SYSTEM_COMMAND_DETECTION,
        ),
    )
    def _programs(self):
        systemctl = self.command.get('systemctl', optional=True)
        if systemctl is not None:
            (ret, stdout, stderr) = self.execute(
                (systemctl, 'show-environment'),
                raiseOnError=False,
            )
            if ret == 0:
                self.logger.debug('registering systemd provider')
                self.context.registerServices(services=self)

    #
    # ServicesBase
    #

    def _executeServiceCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (
                self.command.get('systemctl'),
            ) +
            (command if isinstance(command, tuple) else (command,)) +
            (
                '%s.service' % name,
            ),
            raiseOnError=raiseOnError
        )

    @property
    def supportsDependency(self):
        return True

    def exists(self, name):
        self.logger.debug('check if service %s exists', name)
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            (
                'show',
                '-p',
                'LoadState',
            ),
            raiseOnError=False,
        )
        return (
            rc == 0 and
            stdout and
            stdout[0].strip() == 'LoadState=loaded'
        )

    def status(self, name):
        self.logger.debug('check service %s status', name)
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            'status',
            raiseOnError=False,
        )
        return rc == 0

    def startup(self, name, state):
        self.logger.debug('set service %s startup to %s', name, state)

        # resolve service name
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            (
                'show',
                '-p',
                'Id',
            )
        )
        if len(stdout) == 1:
            name = stdout[0].split('=')[1].strip().replace('.service', '')

        self._executeServiceCommand(
            name,
            'enable' if state else 'disable'
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
