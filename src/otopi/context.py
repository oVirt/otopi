#
# otopi -- plugable installer
#


"""Context management."""


import gettext
import glob
import operator
import os
import random
import sys
import traceback


from . import base
from . import command
from . import common
from . import config
from . import constants
from . import dialog
from . import packager
from . import plugin
from . import services
from . import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


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
            sys.stdout.flush()

    def _loadPlugins(self, base, path, groupname):
        if (
            os.path.isdir(path) and
            os.path.basename(path)[0] not in ('_', '.')
        ):
            if not glob.glob(os.path.join(path, '__init__.py*')):
                for d in glob.glob(os.path.join(path, '*')):
                    self._loadPlugins(base, d, groupname)
            else:
                self._earlyDebug(
                    'Loading plugin %s:%s (%s)' % (
                        groupname,
                        os.path.basename(path),
                        path,
                    )
                )

                def _synth(s):
                    r = ''
                    for c in s:
                        if c in '._' or c.isalnum():
                            r += c
                        else:
                            r += '_'
                    return r

                prefix = _synth(
                    os.path.relpath(
                        os.path.dirname(path),
                        base
                    ).replace('/', '.')
                ).lstrip('.')

                util.loadModule(
                    os.path.dirname(path),
                    'otopi.plugins.%s.%s%s' % (
                        _synth(groupname),
                        '%s.' % prefix if prefix else '',
                        os.path.basename(path),
                    ),
                ).createPlugins(self)

    def _loadPluginGroups(self, plugindir, needgroups, loadedgroups):

        for path in glob.glob(os.path.join(self.resolveFile(plugindir), '*')):
            if os.path.isdir(path):
                groupname = os.path.basename(path)
                if groupname in needgroups:
                    self._earlyDebug('Loading plugin group %s' % groupname)
                    loadedgroups.append(groupname)
                    self._loadPlugins(path, path, groupname)

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
            constants.BaseEnv.EXIT_CODE: [
                {
                    'priority': plugin.Stages.PRIORITY_LAST + 1,
                    'code': constants.Const.EXIT_CODE_SUCCESS,
                },
            ],
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
            constants.BaseEnv.FAIL_ON_PRIO_OVERRIDE: not os.environ.get(
                constants.SystemEnvironment.ALLOW_PRIORITY_OVERRIDE,
                False
            )
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

    def _castlingBuildSequence(self):
        # Enforce before/after by replacing locations of offending events
        # TODO Remove once the toposort version is considered stable and
        # all code using otopi is verified to work with it.

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

        prio_dep_reverses = []
        for stage, methods in sequence.items():
            for i, m in enumerate(methods[:-1]):
                if m['priority'] > methods[i + 1]['priority']:
                    prio_dep_reverses.append(
                        (
                            'Priorities were reversed during buildSequence: '
                            'method %s with priority %s appears after '
                            'method %s with priority %s'
                        ) % (
                            methods[i+1]['method'],
                            methods[i+1]['priority'],
                            m['method'],
                            m['priority'],
                        )
                    )
        if prio_dep_reverses:
            msg = '\n'.join(prio_dep_reverses)
            self._earlyDebug(msg)
            if self.environment[constants.BaseEnv.FAIL_ON_PRIO_OVERRIDE]:
                raise RuntimeError(msg)
        return sequence

    class ToposortCycleException(Exception):
        def __init__(self, leftovers):
            self.leftovers = leftovers

    # Based on https://pypi.python.org/pypi/toposort/1.0
    def _toposort(self, data):
        """Dependencies are expressed as a dictionary whose keys are items
        and whose values are a set of dependent items. Output is a list of
        sets in topological order. The first set consists of items with no
        dependences, each subsequent set consists of items that depend upon
        items in the preceeding sets.
        """

        # Special case empty input.
        if len(data) == 0:
            return

        # Copy the input so as to leave it unmodified.
        data = data.copy()

        # Ignore self dependencies.
        for k, v in data.items():
            v.discard(k)
        # Find all items that don't depend on anything.
        allvalues = set()
        for v in data.values():
            allvalues |= v
        extra_items_in_deps = allvalues - set(data.keys())
        # Add empty dependences where needed.
        # warning: python-2.6 does not have dict comprehension
        data.update({item: set() for item in extra_items_in_deps})
        while True:
            ordered = set(item for item, dep in data.items() if len(dep) == 0)
            if not ordered:
                break
            yield ordered
            data = {
                item: (dep - ordered)
                for item, dep in data.items()
                if item not in ordered
            }
        if len(data) != 0:
            raise Context.ToposortCycleException(data)

    def _toposortBuildSequence(self):
        # Build the sequence by doing a topological sort over the list of
        # events with the comparison being both on before/after and priority.
        # Stage is currently checked independently to ease debugging.

        #
        # bind functions to plugin
        #
        had_errors = False
        methods = []
        for p in self._plugins:
            for metadata in util.methodsByAttribute(
                p.__class__, 'decoration_event'
            ):
                metadata = metadata.copy()
                metadata['method'] = metadata['method'].__get__(p)
                metadata['condition'] = metadata['condition'].__get__(p)
                methods.append(metadata)

        method_by_name = {}
        self._earlyDebug('methods:')
        for index, method in enumerate(methods):
            self._earlyDebug(
                '  method %s %s %s' % (
                    index,
                    self._methodName(method),
                    method
                )
            )
            if method['name'] is not None:
                if method_by_name.get(method['name']):
                    self._earlyDebug(
                        '    error: duplicate name: %s %s %s' % (
                            method['name'],
                            self._methodName(method),
                            self._methodName(method_by_name[method['name']]),
                        )
                    )
                    had_errors = True
                method_by_name[method['name']] = method

        deps = {}
        self._earlyDebug('deps:')
        for index, method in enumerate(methods):
            # list of methods that method depends on, i.e. should be run
            # before it.
            before_after_method_deps = [
                i for i, m in enumerate(methods)
                if (
                    (
                        method['name'] is not None and
                        m['before'] is not None and
                        method['name'] in m['before']
                    ) or (
                        m['name'] is not None and
                        method['after'] is not None and
                        m['name'] in method['after']
                    )
                )
            ]
            if before_after_method_deps:
                self._earlyDebug(
                    (
                        '  deps due to before= or after= for {index} :'
                        '{methods}'
                    ).format(
                        index=index,
                        methods=before_after_method_deps,
                    )
                )
            for i in before_after_method_deps:
                if method['stage'] < methods[i]['stage']:
                    self._earlyDebug(
                        (
                            'error: method {m} is in a later stage '
                            'than method {method} although it depends on it'
                        ).format(
                            method=self._methodName(method),
                            m=self._methodName(methods[i]),
                        )
                    )
                    had_errors = True
                elif method['stage'] > methods[i]['stage']:
                    self._earlyDebug(
                        (
                            'warning: method {m} is in an earlier stage '
                            'than method {method} and also has before/after it'
                        ).format(
                            method=self._methodName(method),
                            m=self._methodName(methods[i]),
                        )
                    )
                if (
                    m['stage'] == method['stage'] and
                    method['priority'] < methods[i]['priority']
                ):
                    self._earlyDebug(
                        (
                            'error: method {method} has a higher priority '
                            'than method {m} '
                            'although dependencies require opposite order'
                        ).format(
                            method=self._methodName(method),
                            m=self._methodName(methods[i]),
                        )
                    )
                    had_errors = True
            method_deps = [
                j for j, m in enumerate(methods)
                if (
                    (
                        m['stage'] == method['stage'] and
                        m['priority'] < method['priority']
                    ) or
                    j in before_after_method_deps
                )
            ]
            if set(method_deps) != set(before_after_method_deps):
                self._earlyDebug(
                    (
                        '  deps added due to priority for {index} :'
                        '{methods}'
                    ).format(
                        index=index,
                        methods=list(
                            set(method_deps)-set(before_after_method_deps)
                        ),
                    )
                )
            deps[index] = set(method_deps)
        sortedmethods = []
        try:
            for s in self._toposort(deps):
                # toposort yields sets
                l = list(s)
                if self.environment[constants.BaseEnv.RANDOMIZE_EVENTS]:
                    random.shuffle(l)
                else:
                    l.sort(key=lambda i: self._methodName(methods[i]))
                self._earlyDebug('toposort group:')
                for i in l:
                    self._earlyDebug(
                        '  %s %s %s' % (
                            i,
                            self._methodName(methods[i]),
                            methods[i]['name']
                        )
                    )
                sortedmethods.extend([methods[i] for i in l])
        except Context.ToposortCycleException as e:
            leftovers = e.leftovers
            self._earlyDebug(
                (
                    'error: toposort failed due to a cycle: {leftovers}\n'
                    'More details:\n{details}'
                ).format(
                    leftovers=leftovers,
                    details='\n'.join(
                        (
                            '\n  method {i} {methodName} {name} needs to run '
                            'after:\n\n{deps}'
                        ).format(
                            i=i,
                            methodName=self._methodName(methods[i]),
                            name=methods[i]['name'],
                            deps='\n'.join(
                                '    method {di} {dmethodName} {dname}'.format(
                                    di=di,
                                    dmethodName=self._methodName(methods[di]),
                                    dname=methods[di]['name'],
                                )
                                for di in list(s)
                            )
                        )
                        for i, s in leftovers.items()
                    )
                )
            )
            raise RuntimeError(_('Cyclic dependencies found'))

        sequence = {}
        for m in sortedmethods:
            sequence.setdefault(m['stage'], []).append(m)

        prio_dep_reverses = []
        for stage, methods in sequence.items():
            for i, m in enumerate(methods[:-1]):
                if m['priority'] > methods[i + 1]['priority']:
                    prio_dep_reverses.append(
                        (
                            'Priorities were reversed during buildSequence: '
                            'method %s with priority %s appears after '
                            'method %s with priority %s'
                        ) % (
                            methods[i+1]['method'],
                            methods[i+1]['priority'],
                            m['method'],
                            m['priority'],
                        )
                    )
        if prio_dep_reverses:
            msg = '\n'.join(prio_dep_reverses)
            self._earlyDebug(msg)
            if self.environment[constants.BaseEnv.FAIL_ON_PRIO_OVERRIDE]:
                raise RuntimeError(msg)

        if had_errors:
            raise RuntimeError('Had errors during buildSequence, please fix')

        return sequence

    def buildSequence(self):
        """Build sequence.

        Should be called after plugins are loaded.

        """

        try:
            self._sequence = self._toposortBuildSequence()
        except Exception as e:
            self._earlyDebug("_toposortBuildSequence failed: %s" % e)
            if not os.environ.get(
                constants.SystemEnvironment.ALLOW_LEGACY_BUILDSEQ
            ):
                raise
            self._sequence = self._castlingBuildSequence()

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
                        oldEnvironment = dict(
                            (k, common.toStr(v))
                            for k, v in self.environment.items()
                        )
                        self._executeMethod(self._currentStage, methodinfo)
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
        diff = False
        for key in sorted(self.environment.keys()):
            value = common.toStr(self.environment[key])

            if (
                old is None or
                value != common.toStr(old.get(key))
            ):
                if not diff:
                    diff = True
                    self.logger.debug('ENVIRONMENT DUMP - BEGIN')

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

        if diff:
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

        loadedgroups = []
        for plugindir in mysplit(
            self.environment[constants.BaseEnv.PLUGIN_PATH]
        ):
            self._loadPluginGroups(plugindir, needgroups, loadedgroups)

        if set(needgroups) != set(loadedgroups):
            raise RuntimeError(
                _('Internal error, plugins {groups} are missing').format(
                    groups=needgroups
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
