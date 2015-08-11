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


"""yum packager provider."""


import gettext
import os
import time


from otopi import constants
from otopi import packager
from otopi import plugin
from otopi import transaction
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase, packager.PackagerBase):
    """yum packager provider.

    Confirms:
        Confirms.GPG_KEY -- confirm use of gpg key.

    """

    class YumTransaction(transaction.TransactionElement):
        """yum transaction element."""

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _("Yum Transaction")

        def prepare(self):
            self._parent.beginTransaction()

        def abort(self):
            self._parent.endTransaction(
                rollback=self._parent.environment[
                    constants.PackEnv.YUM_ROLLBACK
                ],
            )

        def commit(self):
            self._parent.endTransaction(rollback=False)

    def _getMiniYum(
        self,
        disabledPlugins=(),
        enabledPlugins=(),
    ):
        from otopi import miniyum

        class _MyMiniYumSink(miniyum.MiniYumSinkBase):
            """miniyum interaction."""

            def _touch(self):
                self._last = time.time()

            def __init__(self, parent):
                super(_MyMiniYumSink, self).__init__()
                self._parent = parent
                self._touch()

            def verbose(self, msg):
                super(_MyMiniYumSink, self).verbose(msg)
                self._parent.logger.debug('Yum %s' % msg)

            def info(self, msg):
                super(_MyMiniYumSink, self).info(msg)
                self._parent.logger.info('Yum %s' % msg)
                self._touch()

            def error(self, msg):
                super(_MyMiniYumSink, self).error(msg)
                self._parent.logger.error('Yum %s' % msg)
                self._touch()

            def keepAlive(self, msg):
                super(_MyMiniYumSink, self).keepAlive(msg)
                if time.time() - self._last >= self._parent.environment[
                    constants.PackEnv.KEEP_ALIVE_INTERVAL
                ]:
                    self.info(msg)

            def askForGPGKeyImport(self, userid, hexkeyid):
                return self._parent.dialog.confirm(
                    constants.Confirms.GPG_KEY,
                    _(
                        'Confirm use of GPG Key '
                        'userid={userid} hexkeyid={hexkeyid}'
                    ).format(
                        userid=userid,
                        hexkeyid=hexkeyid,
                    )
                )

            def reexec(self):
                super(_MyMiniYumSink, self).reexec()
                self._parent.context.notify(self._parent.context.NOTIFY_REEXEC)

        return miniyum.MiniYum(
            sink=_MyMiniYumSink(parent=self),
            blockStdHandles=False,
            disabledPlugins=disabledPlugins,
            enabledPlugins=enabledPlugins,
        )

    def _refreshMiniyum(self):
        #
        # @WORKAROUND-BEGIN
        # yum has long memory, especially
        # the exclude/include added to the suck
        # as we need to handle versionlock
        # manipulation we need to reconstruct.
        # I would have expected this information will be
        # re-read at every new transaction... but apparently not.
        if self._miniyum is not None:
            del self._miniyum
        self._miniyum = self._getMiniYum(
            disabledPlugins=self.environment[
                constants.PackEnv.YUM_DISABLED_PLUGINS
            ],
            enabledPlugins=self.environment[
                constants.PackEnv.YUM_ENABLED_PLUGINS
            ],
        )
        # @WORKAROUND-END

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._miniyum = None
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        priority=plugin.Stages.PRIORITY_LOW,
    )
    def _boot(self):
        self.environment.setdefault(
            constants.PackEnv.YUMPACKAGER_ENABLED,
            True
        )
        self.environment.setdefault(
            constants.PackEnv.YUM_DISABLED_PLUGINS,
            []
        )
        self.environment.setdefault(
            constants.PackEnv.YUM_ENABLED_PLUGINS,
            []
        )
        self.environment.setdefault(
            constants.PackEnv.KEEP_ALIVE_INTERVAL,
            constants.Defaults.PACKAGER_KEEP_ALIVE_INTERVAL
        )
        self.environment.setdefault(
            constants.PackEnv.YUMPACKAGER_EXPIRE_CACHE,
            True
        )
        self.environment.setdefault(
            constants.PackEnv.YUM_ROLLBACK,
            True
        )

        try:
            if self.environment[constants.PackEnv.YUMPACKAGER_ENABLED]:
                self._refreshMiniyum()

                # the following will trigger the NOTIFY_REEXEC
                # and then reexecute
                if os.geteuid() == 0:
                    self._miniyum.selinux_role()
                    self._enabled = True
        except Exception:
            self.logger.debug('Cannot initialize miniyum', exc_info=True)

    @plugin.event(
        name=constants.Stages.PACKAGERS_DETECTION,
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_HIGH,
        condition=lambda self: self._enabled,
    )
    def _init(self):
        if self.environment[constants.PackEnv.YUMPACKAGER_ENABLED]:
            self.logger.debug('Registering yum packager')
            self.context.registerPackager(packager=self)
        else:
            self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH-1,
        condition=lambda self: self._enabled,
    )
    def _setup_existence(self):
        self._enabled = self.packager == self

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
        condition=lambda self: self._enabled,
    )
    def _setup(self):
        if self.environment[constants.PackEnv.YUMPACKAGER_EXPIRE_CACHE]:
            with self._miniyum.transaction():
                self._miniyum.clean(['expire-cache'])
        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            self.YumTransaction(
                parent=self,
            )
        )
        self.environment[
            constants.CoreEnv.INTERNAL_PACKAGES_TRANSACTION
        ].append(
            self.YumTransaction(
                parent=self,
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
        self._refreshMiniyum()
        return self._miniyum.beginTransaction()

    def endTransaction(self, rollback=False):
        ret = self._miniyum.endTransaction(rollback=rollback)
        self._refreshMiniyum()
        return ret

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

    def installUpdate(self, packages, ignoreErrors=False):
        return self._miniyum.installUpdate(
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
