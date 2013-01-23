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


"""Misc plugin."""


from otopi import constants
from otopi import util
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """Misc dialog settings.

    Environment:
        DialogEnv.DIALECT -- set default dialect.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _init(self):
        self.environment.setdefault(
            constants.DialogEnv.DIALECT,
            constants.Const.DIALOG_DIALECT_HUMAN,
        )


# vim: expandtab tabstop=4 shiftwidth=4
