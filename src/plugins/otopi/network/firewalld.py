#
# ovirt-engine-setup -- ovirt engine setup
# Copyright (C) 2013 Red Hat, Inc.
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


"""firewalld plugin."""

import os
import re
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-engine-setup')


from otopi import util
from otopi import plugin
from otopi import constants
from otopi import filetransaction


@util.export
class Plugin(plugin.PluginBase):
    """firewalld plugin.

    Environment:
        NetEnv.FIREWALLD_ENABLE -- enable firewalld update
        NetEnv.FIREWALLD_SERVICE_PREFIX -- services key=service value=content

    """

    FIREWALLD_SERVICES_DIR = '/etc/firewalld/services'
    _ZONE_RE = re.compile(r'^\w+$')
    _INTERFACE_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            \s+
            interfaces:
            \s+
            (?P<interfaces>[\w,]+)
        """
    )

    def _get_firewalld_cmd_version(self):
        if not self.services.exists('firewalld'):
            return 0

        should_stop = False
        if not self.services.status(name='firewalld'):
            should_stop = True
            self.services.state(
                name='firewalld',
                state=True,
            )
        rc, stdout, stderr = self.execute(
            (
                self.command.get('firewall-cmd'),
                '--version',
            ),
        )
        if should_stop:
            self.services.state(
                name='firewalld',
                state=False,
            )
        return int(
            '%02x%02x%02x' % tuple([
                int(x)
                for x in stdout[0].split('.')
            ]),
            16
        )

    def _get_active_zones(self):
        rc, stdout, stderr = self.execute(
            (
                self.command.get('firewall-cmd'),
                '--get-active-zones',
            ),
        )
        zones = {}
        if self._firewalld_version < 0x000303:
            for line in stdout:
                zone_name, devices = line.split(':')
                zones[zone_name] = devices.split()
        else:
            #0.3.3 has changed output
            zone_name = None
            for line in stdout:
                if self._ZONE_RE.match(line):
                    zone_name = line
                elif self._INTERFACE_RE.match(line):
                    devices = self._INTERFACE_RE.match(
                        line
                    ).group('interfaces')
                    zones[zone_name] = devices.split()

        return zones

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = True
        self._services = []
        self._firewalld_version = 0

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            constants.NetEnv.FIREWALLD_ENABLE,
            False
        )
        self.environment.setdefault(
            constants.NetEnv.FIREWALLD_AVAILABLE,
            False
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        condition=lambda self: self._enabled,
    )
    def _setup(self):
        self.command.detect(command='firewall-cmd')

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        condition=lambda self: self._enabled,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _customization(self):
        self._firewalld_version = self._get_firewalld_cmd_version()
        self._enabled = self.environment[
            constants.NetEnv.FIREWALLD_AVAILABLE
        ] = (
            self.services.exists('firewalld') and
            self._firewalld_version >= 0x000206
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self._enabled,
    )
    def _validation(self):
        self._enabled = self.environment[
            constants.NetEnv.FIREWALLD_ENABLE
        ]

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        for service, content in [
            (
                key[len(constants.NetEnv.FIREWALLD_SERVICE_PREFIX):],
                content,
            )
            for key, content in self.environment.items()
            if key.startswith(
                constants.NetEnv.FIREWALLD_SERVICE_PREFIX
            )
        ]:
            self._services.append(service)
            self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=os.path.join(
                        self.FIREWALLD_SERVICES_DIR,
                        '%s.xml' % service,
                    ),
                    content=content,
                    modifiedList=self.environment[
                        constants.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._enabled,
    )
    def _closeup(self):

        #
        # avoid conflicts, diable iptables
        #
        if self.services.exists(name='iptables'):
            self.services.startup(name='iptables', state=False)
            self.services.state(name='iptables', state=False)

        self.services.state(
            name='firewalld',
            state=True,
        )
        self.services.startup(name='firewalld', state=True)

        #
        # Ensure to load the newly written services if firewalld was already
        # running.
        #
        self.execute(
            (
                self.command.get('firewall-cmd'),
                '--reload'
            )
        )
        for zone in self._get_active_zones():
            for service in self._services:
                self.execute(
                    (
                        self.command.get('firewall-cmd'),
                        '--zone', zone,
                        '--permanent',
                        '--add-service', service,
                    ),
                )
        self.execute(
            (
                self.command.get('firewall-cmd'),
                '--reload'
            )
        )


# vim: expandtab tabstop=4 shiftwidth=4
