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


"""Context management."""


import sys
import os
import glob
import traceback
import operator
import random
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from . import config
from . import constants
from . import base
from . import util
from . import plugin
from . import dialog
from . import services
from . import packager
from . import command


@util.export
class Abort(Exception):
    """Abort exception."""
    def __init__(self, message):
        super(Abort, self).__init__(self, message)


@util.export
class Context(base.Base):
    """Context.

    The context is responsible for the entire workflow.
    It loads the plugins and execute the stages within the
    plugins.

    Environment:
        BaseEnv.DEBUG -- debug level
        BaseEnv.LOG -- logging enabled
        BaseEnv.ERROR -- error condition
        BaseEnv.EXCEPTION_INFO -- exception information
        BaseEnv.PLUGIN_PATH -- plugin search path
        BaseEnv.PLUGIN_GROUPS -- plugin groups to load

    """
    def _earlyDebug(self, msg):
        if self.environment[constants.BaseEnv.DEBUG] > 0:
            print(msg)

    def _loadPlugins(self, plugindir, needgroups):
        def _fulldir(d):
            return [os.path.join(d, f) for f in os.listdir(d)]

        def _candidate(f):
            b = os.path.basename(f)
            return (
                not b.startswith('_') and
                not b.startswith('.') and
                os.path.isdir(f)
            )

        plugindir = self.resolveFile(plugindir)

        for group in _fulldir(plugindir):
            if _candidate(group):
                groupname = os.path.basename(group)
                self._earlyDebug('Loading plugin group %s' % groupname)
                if groupname in needgroups:
                    needgroups.remove(groupname)
                    for p in _fulldir(group):
                        if (
                            _candidate(p) and
                            glob.glob(os.path.join(p, '__init__.py*'))
                        ):
                            self._earlyDebug(
                                'Loading plugin %s' %
                                os.path.basename(p)
                            )
                            util.loadModule(
                                group,
                                'otopi.plugins.%s.%s' % (
                                    groupname.replace('-', '_'),
                                    os.path.basename(p),
                                ),
                            ).createPlugins(self)

    def _methodName(self, methodinfo):
        method = methodinfo['method']
        return "%s.%s.%s" % (
            method.__self__.__class__.__module__,
            method.__self__.__class__.__name__,
            method.__name__
        )

    def _executeMethod(self, stage, method):
        if self.environment[constants.BaseEnv.LOG]:
            self.logger.debug(
                'Stage %s METHOD %s',
                plugin.Stages.stage_id(stage),
                self._methodName(method),
            )
        try:
            if method['condition']():
                method['method']()
            else:
                self.logger.debug('condition False')
        except Exception as e:
            self.environment[constants.BaseEnv.ERROR] = True
            self.environment[constants.BaseEnv.EXCEPTION_INFO].append(
                sys.exc_info()
            )
            self.logger.debug(
                'method exception',
                exc_info=True
            )
            if isinstance(e, Abort):
                self.environment[constants.BaseEnv.ABORTED] = True
                self.logger.warning(_('Aborted'))
            else:
                self.logger.error(
                    _("Failed to execute stage '{stage}': {exception}").format(
                        stage=plugin.Stages.stage_str(stage),
                        exception=e,
                    )
                )
            self.notify(event=self.NOTIFY_ERROR)

    (
        NOTIFY_ERROR,   # error occurred.
        NOTIFY_REEXEC,  # about to re-execute process.
    ) = range(2)

    @property
    def environment(self):
        """Environment."""
        return self._environment

    @property
    def dialog(self):
        """Dialog provider."""
        return self._dialog

    @property
    def services(self):
        """Services provider."""
        return self._services

    @property
    def packager(self):
        """Packager provider."""
        return self._packager

    @property
    def command(self):
        """Command provider."""
        return self._command

    @property
    def currentStage(self):
        """Current stage."""
        return self._currentStage

    def __init__(self):
        """Constructor."""
        super(Context, self).__init__()
        self._sequence = {}
        self._plugins = []
        self._notifications = []
        self._environment = {
            constants.BaseEnv.ERROR: False,
            constants.BaseEnv.ABORTED: False,
            constants.BaseEnv.EXCEPTION_INFO: [],
            constants.BaseEnv.EXECUTION_DIRECTORY: '.',
            constants.BaseEnv.SUPPRESS_ENVIRONMENT_KEYS: [],
            constants.BaseEnv.LOG: False,
            constants.BaseEnv.PLUGIN_PATH: config.otopiplugindir,
            constants.BaseEnv.PLUGIN_GROUPS: 'otopi',
            constants.BaseEnv.DEBUG: int(
                os.environ.get(
                    constants.SystemEnvironment.DEBUG,
                    '0'
                )
            ),
            constants.BaseEnv.RANDOMIZE_EVENTS: False,
        }
        self.registerDialog(dialog.DialogBase())
        self.registerServices(services.ServicesBase())
        self.registerPackager(packager.PackagerBase())
        self.registerCommand(command.CommandBase())

    def notify(self, event):
        """Notify plugins.

        Keyword arguments:
        event -- event to send.

        """
        for n in self._notifications:
            try:
                n(event=event)
            except:
                self.environment[constants.BaseEnv.ERROR] = True
                self.logger.debug(
                    'Unexpected exception from notification',
                    exc_info=True
                )
                self.logger.error(_('Unexepcted exception'))
                raise

    def registerNotification(self, notification):
        """Register notification method."""
        self._notifications.append(notification)

    def registerPlugin(self, p):
        """Register plugin.

        A plugin is calling this method when loaded.

        """
        self._plugins.append(p)

    def registerDialog(self, dialog):
        """Register dialog provider."""
        self._dialog = dialog

    def registerServices(self, services):
        """Register services provider."""
        self._services = services

    def registerPackager(self, packager):
        """Register packager provider."""
        self._packager = packager

    def registerCommand(self, command):
        """Register command provider."""
        self._command = command

    def buildSequence(self):
        """Build sequence.

        Should be called after plugins are loaded.

        """
        #
        # bind functions to plugin
        #
        tmplist = []
        for p in self._plugins:
            for metadata in util.methodsByAttribute(
                p.__class__, 'decoration_event'
            ):
                metadata = metadata.copy()
                metadata['method'] = metadata['method'].__get__(p)
                metadata['condition'] = metadata['condition'].__get__(p)
                tmplist.append(metadata)

        #
        # Set some stable order or randomize
        #
        if self.environment[constants.BaseEnv.RANDOMIZE_EVENTS]:
            random.shuffle(tmplist)
        else:
            tmplist.sort(key=self._methodName)

        #
        # sort based on priority
        #
        tmplist.sort(key=operator.itemgetter('priority'))

        #
        # Handle before and after
        # KISS mode
        #
        def _doit(l, what, compare, aggregate, offset):
            def _indexOfName(names):
                try:
                    return aggregate(
                        i for i, data in enumerate(l)
                        if data['name'] in names
                    )
                except ValueError:
                    return None

            everModified = False
            for limit in range(400):    # boundary
                modified = False
                for index, metadata in enumerate(l):
                    candidateindex = _indexOfName(metadata[what])
                    if (
                        candidateindex is not None and
                        compare(candidateindex, index)
                    ):
                        self._earlyDebug(
                            'modifying location: candidateindex %s index %s '
                            'what %s metadata[what] %s method %s' % (
                                candidateindex,
                                index,
                                what,
                                metadata[what],
                                metadata['method'],
                            )
                        )
                        l.insert(candidateindex + offset, metadata)
                        if candidateindex < index:
                            del l[index + 1]
                        else:
                            del l[index]
                        modified = True
                        everModified = True
                        break
                if not modified:
                    break
            if modified:
                raise RuntimeError(_('Sequence build loop detected'))
            return everModified

        for x in range(400):
            modified = False
            modified = modified or _doit(
                tmplist,
                'before',
                operator.lt,
                min,
                0
            )
            modified = modified or _doit(
                tmplist,
                'after',
                operator.gt,
                max,
                1
            )
            if not modified:
                break
        if modified:
            raise RuntimeError(_('Sequence build loop detected'))

        sequence = {}
        for m in tmplist:
            sequence.setdefault(m['stage'], []).append(m)

        self._sequence = sequence

    def runSequence(self):
        """Run sequence."""
        for self._currentStage in sorted(self._sequence.keys()):
            if_no_error = plugin.Stages.DATABASE[
                self._currentStage
            ]['if-success']

            if (
                not if_no_error or
                not self.environment[constants.BaseEnv.ERROR]
            ):
                self.logger.info(
                    _("Stage: {stage}").format(
                        stage=plugin.Stages.stage_str(self._currentStage),
                    )
                )
                self.logger.debug(
                    "STAGE %s" % plugin.Stages.stage_id(self._currentStage)
                )
                for methodinfo in self._sequence[self._currentStage]:
                    if (
                        not if_no_error or
                        not self.environment[constants.BaseEnv.ERROR]
                    ):
                        oldEnvironment = self.environment.copy()
                        self._executeMethod(self._currentStage, methodinfo)
                        if oldEnvironment != self.environment:
                            self.dumpEnvironment(old=oldEnvironment)

        if self.environment[constants.BaseEnv.ERROR]:
            infos = self.environment[
                constants.BaseEnv.EXCEPTION_INFO
            ]
            for exception_info in infos:
                self.logger.debug(
                    'Exception: %s' % (
                        traceback.format_tb(exception_info[2])
                    )
                )

            if infos:
                util.raiseExceptionInformation(infos[0])
            else:
                raise RuntimeError(_('Error during sequence'))

    def resolveFile(self, file):
        """Resolve file based on installer execution directory"""
        if file is None:
            return None
        elif os.path.isabs(file):
            return file
        else:
            return os.path.join(
                self.environment[
                    constants.BaseEnv.EXECUTION_DIRECTORY
                ],
                file
            )

    def dumpSequence(self):
        """Dump sequence."""
        self.logger.debug('SEQUENCE DUMP - BEGIN')
        for stage, methodinfos in self._sequence.items():
            self.logger.debug('STAGE %s', plugin.Stages.stage_id(stage))
            for methodinfo in methodinfos:
                self.logger.debug(
                    '    METHOD %s (%s)',
                    self._methodName(methodinfo),
                    methodinfo['name'],
                )
        self.logger.debug('SEQUENCE DUMP - END')

    def dumpEnvironment(self, old=None):
        """Dump environment."""
        self.logger.debug('ENVIRONMENT DUMP - BEGIN')
        for key in sorted(self.environment.keys()):
            if (
                old is None or
                self.environment[key] != old.get(key)
            ):
                value = self.environment[key]
                if key in self.environment[
                    constants.BaseEnv.SUPPRESS_ENVIRONMENT_KEYS
                ]:
                    value = '***'
                self.logger.debug(
                    "ENV %s=%s:'%s'",
                    key,
                    type(self.environment[key]).__name__,
                    value,
                )
        self.logger.debug('ENVIRONMENT DUMP - END')

    def loadPlugins(self):
        """Load plugins.

        Load plugins groups based on:
        constants.BaseEnv.PLUGIN_GROUPS

        Search plugins at:
        constants.BaseEnv.PLUGIN_PATH

        """
        def mysplit(l):
            return [i for i in l.split(':') if i]

        needgroups = set(mysplit(
            self.environment[constants.BaseEnv.PLUGIN_GROUPS]
        ))
        needgroups.add('otopi')   # always load us

        for plugindir in mysplit(
            self.environment[constants.BaseEnv.PLUGIN_PATH]
        ):
            self._loadPlugins(plugindir, needgroups)

        if needgroups:
            raise RuntimeError(
                _('Internal error, plugins {groups} are missing').format(
                    groups=needgroups
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
