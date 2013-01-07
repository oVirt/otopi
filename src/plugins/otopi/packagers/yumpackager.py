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


"""yum packager provider."""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import transaction
from otopi import plugin
from otopi import packager


@util.export
class Plugin(plugin.PluginBase, packager.PackagerBase):
    """yum packager provider.

    Confirms:
        Confirms.GPG_KEY -- confirm use of gpg key.

    """
    class YumTransaction(transaction.TransactionElement):
        """yum transaction element."""

        def __init__(self, miniyum):
            self._miniyum = miniyum

        def __str__(self):
            return _("Yum Transaction")

        def prepare(self):
            self._miniyum.beginTransaction()

        def abort(self):
            self._miniyum.endTransaction(rollback=True)

        def commit(self):
            self._miniyum.endTransaction(rollback=False)

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._miniyum = None
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        priority=plugin.Stages.PRIORITY_LOW,
    )
    def _boot(self):
        try:
            self.environment.setdefault(
                constants.PackEnv.KEEP_ALIVE_INTERVAL,
                constants.Defaults.PACKAGER_KEEP_ALIVE_INTERVAL
            )

            from . import miniyumlocal
            self._miniyum = miniyumlocal.getMiniYum(
                parent=self,
            )

            # the following will trigger the NOTIFY_REEXEC
            # and then reexecute
            self._miniyum.selinux_role()
            self._enabled = True
        except ImportError:
            self.logger.debug('Cannot import miniyumlocal', exc_info=True)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_HIGH,
        condition=lambda self: self._enabled,
    )
    def _init(self):
        if self.environment.setdefault(
            constants.PackEnv.YUMPACKAGER_ENABLED,
            True
        ):
            self.logger.debug('Registering yum packager')
            self.context.registerPackager(packager=self)
        else:
            self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
        condition=lambda self: self._enabled,
    )
    def _setup(self):
        with self._miniyum.transaction():
            self._miniyum.clean(['expire-cache'])
        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            self.YumTransaction(
                miniyum=self._miniyum
            )
        )
        self.environment[
            constants.CoreEnv.INTERNAL_PACKAGES_TRANSACTION
        ].append(
            self.YumTransaction(
                miniyum=self._miniyum
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
        priority=plugin.Stages.PRIORITY_LAST,
        condition=lambda self: self._enabled,
    )
    def _internal_packages_end(self):
        if self._miniyum.buildTransaction():
            self.logger.debug("Transaction Summary:")
            for p in self._miniyum.queryTransaction():
                self.logger.debug(
                    "    %s - %s",
                    p['operation'],
                    p['display_name'],
                )
            self._miniyum.processTransaction()

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        priority=plugin.Stages.PRIORITY_LAST,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        if self._miniyum.buildTransaction():
            self.logger.debug("Transaction Summary:")
            for p in self._miniyum.queryTransaction():
                self.logger.debug(
                    "    %s - %s",
                    p['operation'],
                    p['display_name'],
                )
            self._miniyum.processTransaction()

    # PackagerBase

    def beginTransaction(self):
        return self._miniyum.beginTransaction()

    def endTransaction(self, rollback=False):
        return self._miniyum.endTransaction(rollback=rollback)

    def installGroup(self, group, ignoreErrors=False):
        return self._miniyum.installGroup(
            group=group,
            ignoreErrors=ignoreErrors
        )

    def updateGroup(self, group, ignoreErrors=False):
        return self._miniyum.updateGroup(
            group=group,
            ignoreErrors=ignoreErrors
        )

    def removeGroup(self, group, ignoreErrors=False):
        return self._miniyum.removeGroup(
            group=group,
            ignoreErrors=ignoreErrors
        )

    def install(self, packages, ignoreErrors=False):
        return self._miniyum.install(
            packages=packages,
            ignoreErrors=ignoreErrors
        )

    def update(self, packages, ignoreErrors=False):
        return self._miniyum.update(
            packages=packages,
            ignoreErrors=ignoreErrors
        )

    def remove(self, packages, ignoreErrors=False):
        return self._miniyum.remove(
            packages=packages,
            ignoreErrors=ignoreErrors
        )

    def queryGroups(self):
        return self._miniyum.queryGroups()

    def queryPackages(self, patterns=None, listAll=False):
        return self._miniyum.queryPackages(
            patterns=patterns,
            showdups=listAll
        )


# vim: expandtab tabstop=4 shiftwidth=4
