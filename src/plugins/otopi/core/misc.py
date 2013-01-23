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


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import config


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
        self.environment[
            constants.CoreEnv.PACKAGE_NAME
        ] = config.PACKAGE_NAME
        self.environment[
            constants.CoreEnv.PACKAGE_VERSION
        ] = config.PACKAGE_VERSION

        self.context.dumpSequence()

        # as we want full dump and not delta
        # of something before log was active
        self.context.dumpEnvironment()

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _setup(self):
        self.dialog.note(
            text=_('Version: {package}-{version}').format(
                package=config.PACKAGE_NAME,
                version=config.PACKAGE_VERSION,
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _validation(self):
        # as we want full dump and not delta
        # of something before validation
        self.context.dumpEnvironment()


# vim: expandtab tabstop=4 shiftwidth=4
