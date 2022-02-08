#
# otopi -- plugable installer
#


"""Minimalist dnf API interaction."""


from distutils.version import LooseVersion
import gettext
import logging
import os
import sys
import time
import traceback

# Users of minidnf should import it inside a try/except clause and handle
# failures gracefully. otopi deliberately does not require dnf to be installed.
# This applies also to python3-hawkey, which is a dependency of dnf.
import dnf
import dnf.callback
import dnf.logging
import dnf.subject
import dnf.yum.rpmtrans
import dnf.transaction_sr
from dnf.cli.cli import Cli
import hawkey

from . import packager


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


class MiniDNFSinkBase(object):
    """Sink base."""

    @property
    def failed(self):
        return self._failed

    def clearError(self):
        self._failed = False

    def verbose(self, msg):
        """verbose log.

        Keyword arguments:
        msg -- message to print

        """
        pass

    def info(self, msg):
        """info log.

        Keyword arguments:
        msg -- message to print

        """
        pass

    def error(self, msg):
        """error log.

        Keyword arguments:
        msg -- message to print

        """
        self._failed = True

    def keepAlive(self, msg):
        """keepAlive log.

        Keyword arguments:
        msg -- message to print

        """
        pass

    def askForGPGKeyImport(self, userid, hexkeyid):
        """Ask for GPG Key import.

        Keyword arguments:
        userid -- user
        hexkeyid - key id

        return True to accept.

        """
        return False

    def reexec(self):
        """Last chance before reexec."""
        pass


# Copied from dnf:dnf/cli/commands/history.py and edited a bit
# TODO: Revert to using an official API once available:
# https://bugzilla.redhat.com/2010209
def _revert_transaction(trans, base, skip_unavailable):
    action_map = {
        "Install": "Removed",
        "Removed": "Install",
        "Upgrade": "Downgraded",
        "Upgraded": "Downgrade",
        "Downgrade": "Upgraded",
        "Downgraded": "Upgrade",
        "Reinstalled": "Reinstall",
        "Reinstall": "Reinstalled",
        "Obsoleted": "Install",
        "Obsolete": "Obsoleted",
    }

    data = dnf.transaction_sr.serialize_transaction(trans)

    # revert actions in the serialized transaction data to perform
    # rollback/undo
    for content_type in ("rpms", "groups", "environments"):
        for ti in data.get(content_type, []):
            ti["action"] = action_map[ti["action"]]

            if ti["action"] == "Install" and ti.get("reason", None) == "clean":
                ti["reason"] = "dependency"

            if ti.get("repo_id") == hawkey.SYSTEM_REPO_NAME:
                # erase repo_id, because it's not possible to perform forward
                # actions from the @System repo
                ti["repo_id"] = None

    replay = dnf.transaction_sr.TransactionReplay(
        base,
        data=data,
        ignore_installed=True,
        ignore_extras=True,
        skip_unavailable=skip_unavailable
    )
    replay.run()
    return replay


class MiniDNF():

    class _MyHandler(logging.Handler):
        def __init__(self, sink):
            logging.Handler.__init__(self)
            self._sink = sink

        def emit(self, record):
            if record.getMessage():
                if record.levelno > logging.WARNING:
                    self._sink.error(record.getMessage())
                elif record.levelno > logging.DEBUG:
                    self._sink.info(record.getMessage())
                else:
                    self._sink.verbose(record.getMessage())
            if record.exc_info:
                self._sink.verbose(
                    ''.join(traceback.format_exception(*record.exc_info))
                )

    class _MyDownloadProgress(dnf.callback.DownloadProgress):

        _STATUS_2_STR = {
            dnf.callback.STATUS_FAILED: _('FAILED'),
            dnf.callback.STATUS_ALREADY_EXISTS: _('SKIPPED'),
            dnf.callback.STATUS_MIRROR: _('MIRROR'),
            dnf.callback.STATUS_DRPM: _('DRPM'),
        }

        def __init__(self, sink):
            super(MiniDNF._MyDownloadProgress, self).__init__()
            self._sink = sink

        def start(self, total_files, total_size):
            super(MiniDNF._MyDownloadProgress, self).start(
                total_files,
                total_size,
            )
            self._sink.info(
                _('Downloading {files} files, {size:.2f}KB').format(
                    files=total_files,
                    size=total_size / 1024,
                )
            )

        def progress(self, payload, done):
            super(MiniDNF._MyDownloadProgress, self).progress(payload, done)
            msg = _('Downloading {payload} {done:.2f}/{total:.2f}KB').format(
                payload=payload,
                done=done / 1024,
                total=payload.download_size / 1024,
            )
            self._sink.verbose(msg)
            self._sink.keepAlive(msg)

        def end(self, payload, status, msg):
            super(MiniDNF._MyDownloadProgress, self).end(payload, status, msg)
            self._sink.info(
                _('Downloaded {payload}{status}{message}').format(
                    payload=payload,
                    status=(
                        (' ' + self._STATUS_2_STR.get(status, _('Unknown')))
                        if status else ''
                    ),
                    message=(' ' + msg) if msg else '',
                )
            )

    class _MyTransactionDisplay(dnf.yum.rpmtrans.TransactionDisplay):

        _ACTION_TRANSLATION = {
            dnf.callback.PKG_CLEANUP: _('Cleanup'),
            dnf.callback.PKG_DOWNGRADE: _(
                'Downgrading'
            ),
            dnf.callback.PKG_REMOVE: _('Removing'),
            dnf.callback.PKG_INSTALL: _('Installing'),
            dnf.callback.PKG_OBSOLETE: _('Obsoleting'),
            dnf.callback.PKG_REINSTALL: _(
                'Reinstalling'
            ),
            dnf.callback.PKG_UPGRADE: _('Upgrading'),
            dnf.callback.TRANS_POST: _(
                'Post transaction'
            ),
        }

        _FILEACTION_TRANSLATION = {
            dnf.callback.PKG_CLEANUP: _('Cleanup'),
            dnf.callback.PKG_DOWNGRADE: _('Downgraded'),
            dnf.callback.PKG_REMOVE: _('Removed'),
            dnf.callback.PKG_INSTALL: _('Installed'),
            dnf.callback.PKG_OBSOLETE: _('Obsoleted'),
            dnf.callback.PKG_REINSTALL: _(
                'Reinstalled'
            ),
            dnf.callback.PKG_UPGRADE:  _('Upgraded'),
            dnf.callback.TRANS_POST: _(
                'Post transaction'
            ),
        }

        def __init__(self, sink):
            super(MiniDNF._MyTransactionDisplay, self).__init__()
            self._sink = sink
            self._lastaction = None
            self._lastpackage = None

        def event(
            self,
            package,
            action,
            te_current,
            te_total,
            ts_current,
            ts_total,
        ):
            super(MiniDNF._MyTransactionDisplay, self).event(
                package,
                action,
                te_current,
                te_total,
                ts_current,
                ts_total,
            )
            if self._lastaction != action or package != self._lastpackage:
                self._lastaction = action
                self._lastpackage = package

                if package:
                    self._sink.info(
                        _('{action}: {count}/{total}: {package}').format(
                            action=self._ACTION_TRANSLATION.get(
                                action,
                                _('Unknown'),
                            ),
                            count=ts_current,
                            total=ts_total,
                            package=package,
                        )
                    )
                else:
                    self._sink.info(
                        _('{action}').format(
                            action=self._ACTION_TRANSLATION.get(
                                action,
                                _('Unknown'),
                            ),
                        )
                    )

        def scriptout(self, msgs):
            super(MiniDNF._MyTransactionDisplay, self).scriptout(
                msgs,
            )
            if msgs:
                self._sink.verbose(
                    _('Script out: {messages}').format(
                        messages=msgs,
                    )
                )

        def errorlog(self, msg):
            super(MiniDNF._MyTransactionDisplay, self).errorlog(
                msg,
            )
            self._sink.error(msg)

        def filelog(self, package, action):
            super(MiniDNF._MyTransactionDisplay, self).filelog(package, action)
            self._sink.info(
                _('{action}: {package}').format(
                    action=self._FILEACTION_TRANSLATION.get(action, 'Unknown'),
                    package=package,
                )
            )

        def verify_tsi_package(self, pkg, count, total):
            super(MiniDNF._MyTransactionDisplay, self).verify_tsi_package(
                pkg,
                count,
                total,
            )
            self._sink.info(
                _('Verify: {package} {count}/{total}').format(
                    package=pkg,
                    count=count,
                    total=total,
                )
            )

    class _MyTransaction(object):
        def __init__(self, managed, rollback=True):
            self._managed = managed
            self._rollback = rollback

        def __enter__(self):
            self._managed.beginTransaction()

        def __exit__(self, exc_type, exc_value, traceback):
            self._managed.endTransaction(
                rollback=(
                    self._rollback and
                    exc_type is not None
                ),
            )

    class _VoidSink(MiniDNFSinkBase):
        def __init__(self):
            super(MiniDNF._VoidSink, self).__init__()

    @classmethod
    def _getPackageName(clz, po):
        return f'{po.name}-{po.version}-{po.release}.{po.arch}'

    @classmethod
    def _getPackageInfo(clz, po):
        info = {}
        info['display_name'] = clz._getPackageName(po)
        for f in (
            'name',
            'version',
            'release',
            'epoch',
            'arch',
        ):
            info[f] = getattr(po, f)
        return info

    def _createBase(self, offline=False):
        base = dnf.Base()

        # This avoid DNF trying to remove packages that were not touched by
        # its own transaction when doing a rollback.
        base.conf.clean_requirements_on_remove = False

        # This causes DNF to either use the highest available version or fail.
        # When it fails, it should show the reasons. Without this, it will
        # simply ignore the unsatisfied dependencies of the highest version,
        # and either install an older version or do nothing.
        base.conf.best = True

        base.conf.read(priority=dnf.conf.PRIO_MAINCONFIG)
        base.conf.substitutions.update_from_etc(
            base.conf.installroot,
            varsdir=base.conf.varsdir,
        )

        # dnf seems to behave differently depending on whether cli is passed
        # or not (defaults to None). With None, filtering out disabled plugins
        # does not work well. Not sure whether that's by design or a bug.
        # See also: https://bugzilla.redhat.com/show_bug.cgi?id=1919803
        cli = Cli(base)
        base.init_plugins(disabled_glob=self._disabledPlugins, cli=cli)

        base.pre_configure_plugins()
        base.read_all_repos()
        base.configure_plugins()
        base.repos.all().set_progress_bar(self._MyDownloadProgress(self._sink))

        # dnf does not keep packages for offline usage
        # if offline:
        #     base.repos.all().md_only_cached = True

        base.fill_sack()
        base.read_comps()

        return base

    def _destroyBase(self, base):
        if base is not None:
            self._sink.verbose(_('Calling _plugins._unload'))
            base._plugins._unload()
            base.close()

    def _queuePackages(
        self,
        action,
        call,
        packages,
        ignoreErrors=False,
    ):
        ret = True

        for package in packages:
            try:
                self._sink.verbose(
                    _('Queue package {package} for {action}').format(
                        package=package,
                        action=action,
                    )
                )
                call(package)
            except dnf.exceptions.Error as e:
                ret = False
                msg = _("Cannot queue package '{package}': {error}").format(
                    package=package,
                    error=e,
                )
                if ignoreErrors:
                    self._sink.verbose(msg)
                else:
                    self._sink.error(msg)
                    raise
            except Exception as e:
                self._sink.error(
                    _("Cannot queue package '{package}': {error}").format(
                        package=package,
                        error=e,
                    )
                )
                raise

        return ret

    def _queueGroup(
        self,
        action,
        call,
        group,
        ignoreErrors=False,
    ):
        try:
            self._sink.verbose(
                _('Queue group {group} for {action}').format(
                    group=group,
                    action=action,
                )
            )
            groups = [g for g in self._base.comps.groups if g.id == group]
            if not groups:
                raise dnf.exceptions.Error(
                    _('Group {group} cannot be resolved').format(
                        group=group,
                    )
                )
            call(groups[0].id)
            return True
        except dnf.exceptions.Error as e:
            msg = _("Cannot queue group '{group}': {error}").format(
                group=group,
                error=e,
            )
            if ignoreErrors:
                self._sink.verbose(msg)
                return False
            else:
                self._sink.error(msg)
                raise
        except Exception as e:
            self._sink.error(
                _("Cannot queue group '{group}': {error}").format(
                    group=group,
                    error=e,
                )
            )
            raise

    def __init__(
        self,
        sink=None,
        disabledPlugins=None,
    ):
        self._base = None
        self._baseTransaction = None

        if not packager.ok_to_use_dnf():
            raise RuntimeError('minidnf is disabled')

        if LooseVersion(dnf.__version__) < LooseVersion('4.7'):
            # Recent changes are incompatible with older dnf 4.
            # See e.g. recent reports on the list about a missing
            # _get_key_for_package function in dnf 4.2.23.
            raise RuntimeError(_('Incompatible DNF, use 4.7 or later'))

        self._sink = sink if sink else self._VoidSink()
        self._disabledPlugins = disabledPlugins if disabledPlugins else []

        self._handler = self._MyHandler(self._sink)

    def __del__(self):
        if self._base is not None:
            self.endTransaction(rollback=True)

    def selinux_role(self):
        """Setup proper selinux role.

        this must be called at beginning of process
        to adjust proper roles for selinux.
        it will re-execute the process with same arguments.

        This has similar effect of:
        # chcon -t rpm_exec_t executable.py

        We must do this dynamic as this class is to be
        used at bootstrap stage, so we cannot put any
        persistent selinux policy changes, and have no clue
        if filesystem where we put scripts supports extended
        attributes, or if we have proper role for chcon.

        """

        try:
            import selinux
        except ImportError:
            package_name = None
            if sys.version_info.major == 2:
                package_name = 'libselinux-python'
            elif sys.version_info.major == 3:
                package_name = 'libselinux-python3'
            else:
                # Unknown python version, do nothing for now
                pass
            if package_name is not None:
                package_installed = False
                with self.transaction():
                    self.install([package_name])
                    if self.buildTransaction():
                        self.processTransaction()
                        package_installed = True
                #
                # on fedora-18 for example
                # the selinux core is updated
                # so we fail resolving symbols
                # solution is re-execute the process
                # after installation.
                #
                if package_installed:
                    self._sink.reexec()
                    os.execv(sys.executable, [sys.executable] + sys.argv)
                    os._exit(1)

        if selinux.is_selinux_enabled():
            rc, ctx = selinux.getcon()
            if rc != 0:
                raise Exception(_('Cannot get selinux context'))
            ctx1 = selinux.context_new(ctx)
            if not ctx1:
                raise Exception(_('Cannot create selinux context'))
            if selinux.context_role_get(ctx1) != 'system_r':
                if selinux.context_role_set(ctx1, 'system_r') != 0:
                    raise Exception(
                        _('Cannot set role within selinux context')
                    )
                if selinux.setexeccon(selinux.context_str(ctx1)) != 0:
                    raise Exception(
                        _('Cannot set selinux exec context')
                    )
                self._sink.reexec()
                os.execv(sys.executable, [sys.executable] + sys.argv)
                os._exit(1)

    def transaction(self, rollback=True):
        """Manage transaction.

        Usage:
            with mini.transaction():
                do anything
        """
        return self._MyTransaction(self, rollback=rollback)

    def clean(self, what):
        try:
            self._sink.verbose(
                _('Cleaning cache: {what}').format(
                    what=what,
                )
            )
            if 'expire-cache' in what or 'all' in what:
                for repo in self._base.repos.iter_enabled():
                    repo.metadata_expire = 0
        except Exception as e:
            self._sink.error(e)
            raise

    def beginTransaction(self):
        try:
            logging.getLogger('dnf').addHandler(self._handler)
            self._sink.verbose(_('Creating transaction'))
            self._base = self._createBase()
            lastTrans = self._base.history.last()
            self._baseTransaction = lastTrans.tid if lastTrans else 0
        except Exception as e:
            if self._base is not None:
                self._base.close()
                self._base = None
            self._sink.error(e)
            raise

    def endTransaction(self, rollback=False):
        try:
            if self._base is None or self._baseTransaction is None:
                raise RuntimeError(_('Illegal transaction state'))

            self._sink.verbose(
                _('Closing transaction with {op}').format(
                    op=_('rollback') if rollback else _('commit'),
                )
            )

            currTrans = self._base.history.last(
                complete_transactions_only=False,
            )
            currentTransaction = currTrans.tid if currTrans else 0

            self._destroyBase(self._base)
            self._base = None

            if rollback:
                self._sink.info(_('Performing DNF transaction rollback'))
                base = self._createBase(offline=True)
                try:
                    if self._baseTransaction < currentTransaction:
                        for id_ in range(
                            self._baseTransaction + 1,
                            currentTransaction + 1,
                        ):
                            self._sink.verbose(f'Reverting transaction {id_}')
                            _revert_transaction(
                                trans=base.history.old([id_])[0],
                                base=base,
                                skip_unavailable=True,
                            )
                        base.resolve(allow_erasing=True)
                        self._processTransaction(base=base)
                finally:
                    self._destroyBase(base)
                    base = None
        except Exception as e:
            self._sink.error(e)
            raise
        finally:
            if self._base is not None:
                self._destroyBase(self._base)
                self._base = None
            self._baseTransaction = None
            handlers = logging.getLogger('dnf').handlers
            while self._handler in handlers:
                handlers.remove(self._handler)

    def buildTransaction(self):
        try:
            self._sink.verbose(_('Building transaction'))
            ret = self._base.resolve(allow_erasing=True)
            self._sink.verbose(_('Transaction built'))
            if not ret:
                self._sink.verbose(_('Empty transaction'))
            else:
                self._sink.verbose('Transaction Summary:')
                for op, c in (
                    (_('install'), self._base.transaction.install_set),
                    (_('remove'), self._base.transaction.remove_set),
                ):
                    for p in c:
                        self._sink.verbose(
                            _('    {op:10}: {package}').format(
                                op=op,
                                package=p,
                            )
                        )
            return ret
        except Exception as e:
            self._sink.error(e)
            raise

    def _processTransaction(self, base=None):
        try:
            base.download_packages(
                base.transaction.install_set,
                progress=self._MyDownloadProgress(self._sink),
            )
            for po in base.transaction.install_set:
                result, errmsg = base.package_signature_check(po)
                if result == 0:
                    pass
                elif result == 1:
                    def _askGPG(d):
                        return self._sink.askForGPGKeyImport(
                            d['userid'],
                            d['hexkeyid'],
                        )
                    base.package_import_key(po, fullaskcb=_askGPG)
                else:
                    raise RuntimeError(errmsg)

            base.do_transaction(display=self._MyTransactionDisplay(self._sink))
        except Exception as e:
            self._sink.error(e)
            raise

    def processTransaction(self):
        self._processTransaction(base=self._base)

    def queryTransaction(self):
        ret = []
        for op, set_ in (
            ('install', self._base.transaction.install_set),
            ('erase', self._base.transaction.remove_set),
        ):
            for po in set_:
                ret.append(
                    dict(
                        self._getPackageInfo(po),
                        operation=op,
                    )
                )
        self._sink.verbose(f'queryTransaction ret: {ret}')
        return ret

    def installGroup(self, group, **kwargs):
        return self._queueGroup(
            _('install'),
            lambda group: self._base.group_install(
                group,
                pkg_types=('mandatory', 'default'),
            ),
            group,
            **kwargs
        )

    def removeGroup(self, group, **kwargs):
        return self._queueGroup(
            _('remove'),
            self._base.group_remove,
            group,
            **kwargs
        )

    def updateGroup(self, group, **kwargs):
        return self._queueGroup(
            _('update'),
            self._base.group_upgrade,
            group,
            **kwargs
        )

    def install(self, packages, **kwargs):
        return self._queuePackages(
            _('install'),
            self._base.install,
            packages,
            **kwargs
        )

    def installUpdate(self, packages, **kwargs):
        def _installUpdate(p):
            self._base.install(p)
            try:
                self._base.upgrade(p)
            except dnf.exceptions.MarkingError:
                # package is just now being queued for install
                pass

        return self._queuePackages(
            _('install/update'),
            _installUpdate,
            packages,
            **kwargs
        )

    def remove(self, packages, **kwargs):
        return self._queuePackages(
            _('erase'),
            self._base.remove,
            packages,
            **kwargs
        )

    def update(self, packages, **kwargs):
        return self._queuePackages(
            _('update'),
            self._base.upgrade,
            packages,
            **kwargs
        )

    def queryPackages(self, patterns=None, showdups=False):
        try:
            ret = []

            installed = []
            available = []
            reinstall_available = []

            if self._base is None:
                base = _base = self._createBase()
            else:
                base = self._base
                _base = None

            try:
                for pattern in patterns:
                    q = dnf.subject.Subject(pattern).get_best_query(
                        base.sack,
                        with_provides=True,
                    )

                    # more or less copy from dnf
                    dinst = {}
                    ndinst = {}  # Newest versions by name.arch
                    for po in q.installed():
                        dinst[po.pkgtup] = po
                        if showdups:
                            continue
                        key = (po.name, po.arch)
                        if key not in ndinst or po > ndinst[key]:
                            ndinst[key] = po
                    installed = dinst.values()

                    for pkg in (q if showdups else q.latest()):
                        available.append(pkg)

                    for pkg in (q.available() if showdups else q.latest()):
                        reinstall_available.append(pkg)
            finally:
                if _base is not None:
                    self._destroyBase(_base)

            for op, l in (
                ('available', available),
                ('installed', installed),
                ('reinstall_available', reinstall_available),
            ):
                for entry in l:
                    info = self._getPackageInfo(entry)
                    info['operation'] = op
                    ret.append(info)

            self._sink.verbose(
                f'queryPackages: showdups: {showdups}\n'
                f'queryPackages: patterns: {patterns}\n'
                f'queryPackages: result: {ret}'
            )
            return ret
        except Exception as e:
            self._sink.error(e)
            raise

    def queryGroups(self):
        if self._base is None:
            base = _base = self._createBase()
        else:
            base = self._base
            _base = None

        try:
            return [
                {
                    'operation': 'installed'
                    if base.history.group.get(group.id) is not None
                    else 'available',
                    'name': group.id,
                    'description': group.name,
                    'uservisible': group.visible
                }
                for group in base.comps.groups_iter()
            ]
        except Exception as e:
            self._sink.error(e)
            raise
        finally:
            if _base is not None:
                self._destroyBase(_base)

    def getConf(self):
        we_created_base = False
        if self._base is None:
            base = self._createBase()
            we_created_base = True
        else:
            base = self._base

        try:
            return 'DNF Conf dump:\n{conf}\n{repos}'.format(
                conf=base.conf.dump(),
                repos=''.join(
                    f'DNF Repo dump: {repo.repofile}\n{repo.dump()}\n'
                    for repo in base.repos.values()
                )
            )
        except Exception as e:
            self._sink.error(e)
            raise
        finally:
            if we_created_base and base is not None:
                self._destroyBase(base)

    def checkForSafeUpdate(self, packages):
        missingRollback = []
        upgradeAvailable = False
        plist = []

        with self.transaction():
            self.installUpdate(packages)

            if self.buildTransaction():
                upgradeAvailable = True

                for p in self.queryTransaction():
                    plist.append(p.copy())

                # Verify all installed packages available in repos
                for package in self.queryTransaction():
                    installed = False
                    reinstall_available = False
                    for query in self.queryPackages(
                        patterns=(package['display_name'],),
                        showdups=True,
                    ):
                        self._sink.verbose(
                            'dupes: operation [%s] package %s' % (
                                query['operation'],
                                query['display_name'],
                            )
                        )
                        if query['operation'] == 'installed':
                            installed = True
                        if query['operation'] == 'reinstall_available':
                            reinstall_available = True
                    if installed and not reinstall_available:
                        missingRollback.append(package['display_name'])
        return {
            'upgradeAvailable': upgradeAvailable,
            'missingRollback': set(missingRollback),
            'packageOperations': plist,
        }


class Example():

    class MyDNFSink(MiniDNFSinkBase):

        KEEPALIVE_INTERVAL = 60

        def _touch(self):
            self._last = time.time()

        def verbose(self, msg):
            super(Example.MyDNFSink, self).verbose(msg)
            print('VERB: -->%s<--' % msg)

        def info(self, msg):
            super(Example.MyDNFSink, self).info(msg)
            self._touch()
            print('OK:   -->%s<--' % msg)

        def error(self, msg):
            super(Example.MyDNFSink, self).error(msg)
            self._touch()
            print('FAIL: -->%s<--' % msg)

        def keepAlive(self, msg):
            super(Example.MyDNFSink, self).keepAlive(msg)
            if time.time() - self._last >= \
                    self.KEEPALIVE_INTERVAL:
                self.info(msg)

        def askForGPGKeyImport(self, userid, hexkeyid):
            print('APPROVE-GPG: -->%s-%s<--' % (userid, hexkeyid))
            return True

    @staticmethod
    def main():
        logging.getLogger('dnf').setLevel(dnf.logging.SUBDEBUG)

        # BEGIN: PROCESS-INITIALIZATION
        minidnf = MiniDNF(sink=Example.MyDNFSink())
        minidnf.selinux_role()
        # END: PROCESS-INITIALIZATION

        with minidnf.transaction():
            print(minidnf.queryPackages(patterns=('ccid',)))
            print(minidnf.queryPackages(patterns=('sudo',), showdups=True))
            print(minidnf.queryGroups())
            minidnf.installGroup('robotics-suite')
            if minidnf.buildTransaction():
                for p in minidnf.queryTransaction():
                    print(
                        '    %s - %s' % (
                            p['operation'],
                            p['display_name']
                        )
                    )

        with minidnf.transaction():
            minidnf.clean(('expire-cache',))

        with minidnf.transaction():
            minidnf.install(packages=('ccid',))
            if minidnf.buildTransaction():
                for p in minidnf.queryTransaction():
                    print(
                        '    %s - %s' % (
                            p['operation'],
                            p['display_name']
                        )
                    )
                minidnf.processTransaction()

        with minidnf.transaction():
            minidnf.remove(packages=('pcsc-lite*',))
            if minidnf.buildTransaction():
                for p in minidnf.queryTransaction():
                    print(
                        '    %s - %s' % (
                            p['operation'],
                            p['display_name']
                        )
                    )
                minidnf.processTransaction()

        class IgnoreMe(Exception):
            pass
        try:
            with minidnf.transaction():
                minidnf.update(packages=('sudo',))
                minidnf.install(packages=('ccid',))
                if minidnf.buildTransaction():
                    minidnf.processTransaction()
                    pass
                raise IgnoreMe()
        except IgnoreMe:
            pass


if __name__ == '__main__':
    Example.main()


__all__ = ['MiniDNF', 'MiniDNFSinkBase']


# vim: expandtab tabstop=4 shiftwidth=4
