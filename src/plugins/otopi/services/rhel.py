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


"""rhel services provider."""


import os
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
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
        self.command.detect('initctl')

    @plugin.event(
        stage=plugin.Stages.STAGE_PROGRAMS,
        after=[
            constants.Stages.SYSTEM_COMMAND_DETECTION,
        ],
    )
    def _programs(self):
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

    def _executeInitctlCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (
                self.command.get('initctl'),
                command,
                name,
            ),
            raiseOnError=raiseOnError
        )

    def _executeServiceCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (
                self.command.get('service'),
                name,
                command
            ),
            raiseOnError=raiseOnError
        )

    def _isUpstart(self, name):
        exists = False
        status = False

        if self.command.get('initctl') is not None:
            #
            # status always returns rc 0 no mater
            # what state it is
            #
            rc, stdout, stderr = self._executeInitctlCommand(
                name,
                'status',
                raiseOnError=False,
            )
            if rc == 0 and len(stdout) == 1:
                exists = True
                if 'start/' in stdout[0]:
                    status = True
        return (exists, status)

    def exists(self, name):
        ret = False
        self.logger.debug('check if service %s exists', name)
        (upstart, status) = self._isUpstart(name)
        if upstart:
            ret = True
        else:
            ret = os.path.exists(
                os.path.join('/etc/rc.d/init.d', name)
            )
        self.logger.debug(
            'service %s exists %s upstart=%s',
            name,
            ret,
            upstart
        )
        return ret

    def status(self, name):
        self.logger.debug('check service %s status', name)
        (upstart, status) = self._isUpstart(name)
        if not upstart:
            (rc, stdout, stderr) = self._executeServiceCommand(
                name,
                'status',
                raiseOnError=False
            )
            status = rc == 0
        self.logger.debug('service %s status %s', name, status)
        return status

    def startup(self, name, state):
        self.logger.debug('set service %s startup to %s', name, state)
        (upstart, status) = self._isUpstart(name)
        if upstart:
            #
            # upstart does not have the nature of
            # startup configuration?
            #
            pass
        else:
            self.execute(
                (
                    self.command.get('chkconfig'),
                    name,
                    'on' if state else 'off',
                ),
            )

    def state(self, name, state):
        self.logger.debug('starting service %s', name)
        (upstart, status) = self._isUpstart(name)
        if upstart:
            #
            # upstart fails when multiple
            # start/stop commands.
            #
            if state != status:
                self._executeInitctlCommand(
                    name,
                    'start' if state else 'stop'
                )
        else:
            self._executeServiceCommand(
                name,
                'start' if state else 'stop'
            )


# vim: expandtab tabstop=4 shiftwidth=4
