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


"""iptables handler plugin."""


import platform
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import filetransaction


@util.export
class Plugin(plugin.PluginBase):
    """iptables updater.

    Environment:
        NetEnv.IPTABLES_ENABLE -- enable iptables update
        NetEnv.IPTABLES_RULES -- iptables rules (multi-string)

    """
    REDHAT_IPTABLES = '/etc/sysconfig/iptables'

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._distribution = platform.linux_distribution(
            full_distribution_name=0
        )[0]
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(constants.NetEnv.IPTABLES_ENABLE, False)
        self.environment.setdefault(constants.NetEnv.IPTABLES_RULES, None)

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=(
            lambda self: self.environment[constants.NetEnv.IPTABLES_ENABLE]
        ),
    )
    def _validate(self):
        if not self._distribution in ('redhat', 'fedora'):
            self.logger.warning(
                _('Unsupported distribution for iptables plugin')
            )
        else:
            self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.install(('iptables',))

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _store_iptables(self):
        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=self.REDHAT_IPTABLES,
                owner='root',
                mode=0o600,
                enforcePermissions=True,
                content=self.environment[
                    constants.NetEnv.IPTABLES_RULES
                ],
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._enabled,
    )
    def _closeup(self):
        # We would like to avoid conflict
        if self.services.exists('firewalld'):
            self.services.startup('firewalld', False)
            self.services.state('firewalld', False)
        self.services.startup('iptables', True)
        self.services.state('iptables', False)
        self.services.state('iptables', True)
