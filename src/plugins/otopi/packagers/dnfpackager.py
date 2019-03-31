#
# otopi -- plugable installer
#


"""dnf packager provider."""


import platform
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
    """dnf packager provider.

    Confirms:
        Confirms.GPG_KEY -- confirm use of gpg key.

    """

    class DNFTransaction(transaction.TransactionElement):
        """dnf transaction element."""

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _("DNF Transaction")

        def prepare(self):
            self._parent.beginTransaction()

        def abort(self):
            self._parent.endTransaction(
                rollback=self._parent.environment[
                    constants.PackEnv.DNF_ROLLBACK
                ],
            )

        def commit(self):
            self._parent.endTransaction(rollback=False)

    def _getMiniDNF(
        self,
        disabledPlugins=(),
    ):
        from otopi import minidnf

        class _MyMiniDNFSink(minidnf.MiniDNFSinkBase):
            """minidnf interaction."""

            def _touch(self):
                self._last = time.time()

            def __init__(self, parent):
                super(_MyMiniDNFSink, self).__init__()
                self._parent = parent
                self._touch()

            def verbose(self, msg):
                super(_MyMiniDNFSink, self).verbose(msg)
                self._parent.logger.debug('DNF %s' % msg)

            def info(self, msg):
                super(_MyMiniDNFSink, self).info(msg)
                self._parent.logger.info('DNF %s' % msg)
                self._touch()

            def error(self, msg):
                super(_MyMiniDNFSink, self).error(msg)
                self._parent.logger.error('DNF %s' % msg)
                self._touch()

            def keepAlive(self, msg):
                super(_MyMiniDNFSink, self).keepAlive(msg)
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
                super(_MyMiniDNFSink, self).reexec()
                self._parent.context.notify(self._parent.context.NOTIFY_REEXEC)

        return minidnf.MiniDNF(
            sink=_MyMiniDNFSink(parent=self),
            disabledPlugins=disabledPlugins,
        )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._minidnf = None
        self._enabled = False

    def _ok_to_use_dnf(self):
        plat_dist = platform.linux_distribution(full_distribution_name=0)
        distribution = plat_dist[0]
        version = plat_dist[1]
        return (
            distribution in (
                'fedora',
            ) or (
                distribution in (
                    'redhat',
                    'centos',
                    'ibm_powerkvm',
                ) and
                version >= '8.0'
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        before=(
            constants.Stages.YUM_PACKAGER_BOOT,
            # Run before yum, because if we have both, we want dnf to be used
            # and not yum.
        ),
        after=(
            constants.Stages.DIALOG_BOOT_DONE,
        ),
    )
    def _boot(self):
        self.environment.setdefault(
            constants.PackEnv.DNFPACKAGER_ENABLED,
            self._ok_to_use_dnf()
        )
        self.environment.setdefault(
            constants.PackEnv.DNF_DISABLED_PLUGINS,
            []
        )
        self.environment.setdefault(
            constants.PackEnv.KEEP_ALIVE_INTERVAL,
            constants.Defaults.PACKAGER_KEEP_ALIVE_INTERVAL
        )
        self.environment.setdefault(
            constants.PackEnv.DNFPACKAGER_EXPIRE_CACHE,
            True
        )
        self.environment.setdefault(
            constants.PackEnv.DNF_ROLLBACK,
            True
        )

        try:
            if self.environment[constants.PackEnv.DNFPACKAGER_ENABLED]:
                self._minidnf = self._getMiniDNF(
                    disabledPlugins=self.environment[
                        constants.PackEnv.DNF_DISABLED_PLUGINS
                    ],
                )

                # the following will trigger the NOTIFY_REEXEC
                # and then reexecute
                if os.geteuid() == 0:
                    self._minidnf.selinux_role()
                    self._enabled = True
                    self.environment[
                        constants.PackEnv.YUMPACKAGER_ENABLED
                    ] = False
        except Exception:
            # not calling with exc_info=True, because we always try to
            # load DNF support first, polluting the logs with misleading
            # tracebacks when running on yum-based operating systems
            self.logger.debug('Cannot initialize minidnf', exc_info=True)

    @plugin.event(
        before=(
            constants.Stages.PACKAGERS_DETECTION,
        ),
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_HIGH,
        condition=lambda self: self._enabled,
    )
    def _init(self):
        if self.environment[constants.PackEnv.DNFPACKAGER_ENABLED]:
            self.logger.debug('Registering dnf packager')
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
        if self.environment[constants.PackEnv.DNFPACKAGER_EXPIRE_CACHE]:
            with self._minidnf.transaction():
                self._minidnf.clean(['expire-cache'])
        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            self.DNFTransaction(
                parent=self,
            )
        )
        self.environment[
            constants.CoreEnv.INTERNAL_PACKAGES_TRANSACTION
        ].append(
            self.DNFTransaction(
                parent=self,
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
        priority=plugin.Stages.PRIORITY_LAST,
        condition=lambda self: self._enabled,
    )
    def _internal_packages_end(self):
        self.processTransaction()

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        priority=plugin.Stages.PRIORITY_LAST,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.processTransaction()

    # PackagerBase

    def beginTransaction(self):
        return self._minidnf.beginTransaction()

    def endTransaction(self, rollback=False):
        ret = self._minidnf.endTransaction(rollback=rollback)
        return ret

    def processTransaction(self):
        if self._minidnf.buildTransaction():
            self.logger.debug("Transaction Summary:")
            for p in self._minidnf.queryTransaction():
                self.logger.debug(
                    "    %s - %s",
                    p['operation'],
                    p['display_name'],
                )
            self._minidnf.processTransaction()

    def installGroup(self, group, ignoreErrors=False):
        return self._minidnf.installGroup(
            group=group,
            ignoreErrors=ignoreErrors,
        )

    def updateGroup(self, group, ignoreErrors=False):
        return self._minidnf.updateGroup(
            group=group,
            ignoreErrors=ignoreErrors,
        )

    def removeGroup(self, group, ignoreErrors=False):
        return self._minidnf.removeGroup(
            group=group,
            ignoreErrors=ignoreErrors,
        )

    def install(self, packages, ignoreErrors=False):
        return self._minidnf.install(
            packages=packages,
            ignoreErrors=ignoreErrors,
        )

    def update(self, packages, ignoreErrors=False):
        return self._minidnf.update(
            packages=packages,
            ignoreErrors=ignoreErrors,
        )

    def installUpdate(self, packages, ignoreErrors=False):
        return self._minidnf.installUpdate(
            packages=packages,
            ignoreErrors=ignoreErrors,
        )

    def remove(self, packages, ignoreErrors=False):
        return self._minidnf.remove(
            packages=packages,
            ignoreErrors=ignoreErrors,
        )

    def queryGroups(self):
        return self._minidnf.queryGroups()

    def queryPackages(self, patterns=None, listAll=False):
        return self._minidnf.queryPackages(
            patterns=patterns,
            showdups=listAll,
        )


# vim: expandtab tabstop=4 shiftwidth=4
