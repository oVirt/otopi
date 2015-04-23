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


"""Plugin interface."""


import builtins
import datetime
import errno
import fcntl
import select
import signal
import os
import subprocess
import time
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from . import base
from . import util


@util.export
class Stages(object):
    """Stage holder."""

    PRIORITY_FIRST = 1000
    PRIORITY_HIGH = 2000
    PRIORITY_MEDIUM = 3000
    PRIORITY_DEFAULT = 5000
    PRIORITY_POST = 7000
    PRIORITY_LOW = 9000
    PRIORITY_LAST = 90000

    (
        STAGE_BOOT,
        STAGE_INIT,
        STAGE_SETUP,
        STAGE_INTERNAL_PACKAGES,
        STAGE_PROGRAMS,
        STAGE_LATE_SETUP,
        STAGE_CUSTOMIZATION,
        STAGE_VALIDATION,
        STAGE_TRANSACTION_BEGIN,
        STAGE_EARLY_MISC,
        STAGE_PACKAGES,
        STAGE_MISC,
        STAGE_TRANSACTION_END,
        STAGE_CLOSEUP,
        STAGE_CLEANUP,
        STAGE_PRE_TERMINATE,
        STAGE_TERMINATE,
        STAGE_REBOOT,
    ) = range(18)

    DATABASE = {
        STAGE_BOOT: {
            #
            # Use to setup boot environment.
            # Usually avoid.
            #
            'id': 'boot',
            'description': _("Booting"),
            'if-success': True,           # Enter always
        },
        STAGE_INIT: {
            #
            # Use this stage to initialize components.
            # Also initialize key environment.
            # Use only setdefault() to set environment.
            #
            'id': 'init',
            'description': _("Initializing"),
            'if-success': False,           # Enter always
        },
        STAGE_SETUP: {
            #
            # Use this stage to setup environment.
            # Use only setdefault() to set environment.
            #
            'id': 'setup',
            'description': _("Environment setup"),
            'if-success': True,            # Enter only if no error
        },
        STAGE_INTERNAL_PACKAGES: {
            #
            # Install local packages required for setup.
            # No rollback for these packages.
            #
            'id': 'internal_packages',
            'description': _("Environment packages setup"),
            'if-success': True,
        },
        STAGE_PROGRAMS: {
            #
            # Detect local programs.
            #
            'id': 'programs',
            'description': _("Programs detection"),
            'if-success': True,
        },
        STAGE_LATE_SETUP: {
            #
            # Late setup actions.
            #
            'id': 'late_setup',
            'description': _("Environment setup"),
            'if-success': True,
        },
        STAGE_CUSTOMIZATION: {
            #
            # Customization phase for dialog, avoid.
            #
            'id': 'customization',
            'description': _("Environment customization"),
            'if-success': True,
        },
        STAGE_VALIDATION: {
            #
            # Perform any process validations here.
            #
            'id': 'validation',
            'description': _("Setup validation"),
            'if-success': True,
        },
        STAGE_TRANSACTION_BEGIN: {
            #
            # Transaction begins here, you can add elements
            # before, at this point these will be prepared.
            #
            'id': 'transaction-prepare',
            'description': _("Transaction setup"),
            'if-success': True,
        },
        STAGE_EARLY_MISC: {
            #
            # Misc actions before package update.
            #
            'id': 'early_misc',
            'description': _("Misc configuration"),
            'if-success': True,
        },
        STAGE_PACKAGES: {
            #
            # Package installation.
            #
            'id': 'packages',
            'description': _("Package installation"),
            'if-success': True,
        },
        STAGE_MISC: {
            #
            # Misc actions go to here.
            #
            'id': 'misc',
            'description': _("Misc configuration"),
            'if-success': True,
        },
        STAGE_TRANSACTION_END: {
            #
            # Transaction commit.
            #
            'id': 'cleanup',
            'description': _("Transaction commit"),
            'if-success': True,
        },
        STAGE_CLOSEUP: {
            #
            # Non distructive actions.
            # Executed if no error.
            #
            'id': 'closeup',
            'description': _("Closing up"),
            'if-success': True,
        },
        STAGE_CLEANUP: {
            #
            # Clean up.
            # Executed always.
            #
            'id': 'cleanup',
            'description': _("Clean up"),
            'if-success': False,
        },
        STAGE_PRE_TERMINATE: {
            #
            # Termination dialog, avoid.
            #
            'id': 'pre-terminate',
            'description': _("Pre-termination"),
            'if-success': False,
        },
        STAGE_TERMINATE: {
            #
            # Termination, avoid.
            #
            'id': 'terminate',
            'description': _("Termination"),
            'if-success': False,
        },
        STAGE_REBOOT: {
            #
            # Reboot, avoid.
            #
            'id': 'reboot',
            'description': _("Reboot"),
            'if-success': True,
        },
    }

    @classmethod
    def stage_str(clz, stage):
        """Get stage string description."""
        return clz.DATABASE[stage]['description']

    @classmethod
    def stage_id(clz, stage):
        """Get stage string id."""
        return clz.DATABASE[stage]['id']


@util.export
def event(
    name=None,
    stage=None,
    before=(),
    after=(),
    priority=Stages.PRIORITY_DEFAULT,
    condition=None,
):
    """Decoration to specify sequence event method.

    Keyword arguments:
    name -- give this event a name. Used with before and after.
    stage -- stage to place this even in. One of Stages.STAGE_*.
    before=EVENTNAMESLIST -- place this event before the events with
        names EVENTNAMESLIST.
    after -- place this event after the events with names EVENTNAMESLIST.
    priority -- priority to place this event in. One of Stages.PRIORITY_*.
    condition -- optional condition function.

    """
    def decorator(f):
        f.decoration_event = {
            'method': f,
            'name': name,
            'stage': stage,
            'before': before,
            'after': after,
            'priority': priority,
            'condition': (
                condition if condition is not None
                else lambda self: True
            ),
        }
        return f
    return decorator


@util.export
class PluginBase(base.Base):
    """Base class for plugin.

    Base class for all plugins.

    Plugin is the component that interact with the context.

    """

    @property
    def context(self):
        """Context."""
        return self._context

    @property
    def environment(self):
        """Environment."""
        return self.context.environment

    @property
    def dialog(self):
        """Dialog provider."""
        return self.context.dialog

    @property
    def services(self):
        """Services provider."""
        return self.context.services

    @property
    def packager(self):
        """Packager provider."""
        return self.context.packager

    @property
    def command(self):
        """Command provider."""
        return self.context.command

    @property
    def currentStage(self):
        """Current stage."""
        return self.context.currentStage

    def __init__(self, context):
        """Constructor.

        Keyword arguments:
        context -- context to use.

        """
        super(PluginBase, self).__init__()
        self._context = context
        context.registerPlugin(self)

    def resolveFile(self, file):
        return self.context.resolveFile(file)

    def executePipeRaw(
        self,
        popenArgs,
        stdin=None,
        stdout=None,
        envAppend=None,
        timeout=None,
        callback=None,
        callback_interval=30,
    ):
        """Execute a list of processes in a pipeline.

        Keyword arguments:
        popenArgs - a list of dictionaries, each a **kwarg for Popen
        stdin - input of first process, passed as-is to Popen
        stdout - output of last process, passed as-is to Popen
        envAppend - a dict to append to the environment of all processes
        timeout - max timeout in seconds
        callback - callable object state argument
        callback_interval - interval to call callback

        Returns a dict d:
        d['stdout'] - output of last process, blob or file
        d['result'] - a list of dicts, one per process:
        d['result'][n]['rc'] - return code of process n
        d['result'][n]['stderr'] - stderr of process n, blob or file

        For each dict in popenArgs:
        'stdin' and 'stdout' are set as needed.
        'env' is appended to from envAppend if it's not None.
        rest of data is passed as-is to Popen.

        Callback state:
        state[n]['args'] - arguments of entry.
        state[n]['popen'] - popen object.
        state[n]['streams']['buffer'] - buffer.
        state[n]['streams']['buffer_index'] - index within buffer.
        """

        CHUNK_SIZE = 4096

        class _Timeout(RuntimeError):
            def __init__(self):
                super(_Timeout, self).__init__('Command timeout')

        def _callCallback():
            now = datetime.datetime.now()
            if (
                (
                    _callCallback.next +
                    datetime.timedelta(seconds=callback_interval)
                ) < now
            ):
                _callCallback.next = datetime.datetime.now()
                if callback:
                    callback(state=popens)

        _callCallback.next = datetime.datetime.now()

        end_time = datetime.datetime.now()
        if timeout is None:
            end_time += datetime.timedelta(days=3650)
        else:
            end_time += datetime.timedelta(seconds=timeout)

        popens = []
        fds = {}
        try:
            stdindata = None
            if (
                stdin is None or
                isinstance(stdin, bytes) or
                isinstance(stdin, str) or
                isinstance(stdin, builtins.unicode)
            ):
                stdindata = stdin
                stdin = None

            for i, kw in enumerate(popenArgs):
                kw = kw.copy()

                pipestdin = False
                pipestdout = False
                pipestderr = False

                if envAppend is not None:
                    if 'env' not in kw:
                        kw['env'] = os.environ
                    kw['env'] = kw['env'].copy()
                    kw['env'].update(envAppend)

                if 'preexec_fn' not in kw:

                    def _enableSignals():
                        signal.signal(signal.SIGHUP, signal.SIG_DFL)
                        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

                    kw['preexec_fn'] = _enableSignals

                if 'close_fds' not in kw:
                    kw['close_fds'] = True

                if 'stderr' not in kw:
                    kw['stderr'] = subprocess.PIPE
                    pipestderr = True

                if len(popens) < len(popenArgs) - 1:
                    kw['stdout'] = subprocess.PIPE
                else:
                    if stdout is not None:
                        kw['stdout'] = stdout
                    else:
                        kw['stdout'] = subprocess.PIPE
                        pipestdout = True

                if popens:
                    kw['stdin'] = popens[-1]['popen'].stdout
                else:
                    if stdindata is None:
                        kw['stdin'] = stdin
                    else:
                        kw['stdin'] = subprocess.PIPE
                        pipestdin = True

                self.logger.debug('executePipeRaw: [%s] popen kw=%s' % (i, kw))
                popen = subprocess.Popen(**kw)
                self.logger.debug(
                    'executePipeRaw: [%s] pid pid=%s' % (
                        i,
                        popen.pid
                    )
                )

                if popens:
                    popens[-1]['popen'].stdout.close()

                popens.append({
                    'args': kw,
                    'popen': popen,
                    'streams': {
                        'stdin': {
                            'pipe': pipestdin,
                            'stream': popen.stdin,
                            'buffer': stdindata,
                            'events': select.POLLOUT,
                        },
                        'stdout': {
                            'pipe': pipestdout,
                            'stream': popen.stdout,
                            'buffer': b'',
                            'events': select.POLLIN,
                        },
                        'stderr': {
                            'pipe': pipestderr,
                            'stream': popen.stderr,
                            'buffer':  b'',
                            'events': select.POLLIN,
                        },
                    },
                })

            poll = select.poll()
            for popen in popens:
                for stream in popen['streams'].values():
                    if stream is not None and stream['pipe']:
                        stream['fd'] = stream['stream'].fileno()
                        stream['buffer_index'] = 0
                        fcntl.fcntl(
                            stream['fd'],
                            fcntl.F_SETFL,
                            fcntl.fcntl(
                                stream['fd'],
                                fcntl.F_GETFL
                            ) | os.O_NONBLOCK,
                        )
                        fds[stream['fd']] = stream
                        poll.register(stream['fd'], stream['events'])

            while (
                set(
                    [fd['stream'].closed for fd in fds.values()]
                ) != set([True])
            ):
                _callCallback()
                if (datetime.datetime.now() > end_time):
                    raise _Timeout()

                for fd, events in poll.poll(callback_interval * 1000):
                    entry = fds[fd]
                    should_close = False

                    if (events & select.POLLOUT) != 0:
                        try:
                            while entry['buffer_index'] < len(entry['buffer']):
                                entry['buffer_index'] += os.write(
                                    entry['fd'],
                                    entry['buffer'][
                                        entry['buffer_index']:
                                        entry['buffer_index'] + CHUNK_SIZE
                                    ],
                                )
                            should_close = True
                        except builtins.BlockingIOError:
                            pass
                        except OSError as e:
                            if e.errno != errno.EWOULDBLOCK:
                                self.logger.debug('OSError', exc_info=True)
                                should_close = True

                    if (events & select.POLLIN) != 0:
                        try:
                            while True:
                                buf = os.read(entry['fd'], CHUNK_SIZE)
                                if len(buf) == 0:
                                    break
                                entry['buffer'] += buf
                            should_close = True
                        except builtins.BlockingIOError:
                            pass
                        except OSError as e:
                            if e.errno != errno.EWOULDBLOCK:
                                self.logger.debug('OSError', exc_info=True)
                                should_close = True

                    if ((events & (select.POLLERR | select.POLLHUP)) != 0):
                        should_close = True

                    if should_close:
                        poll.unregister(entry['fd'])
                        entry['stream'].close()

            while (
                None in [
                    p['popen'].poll() for p in popens
                ]
            ):
                _callCallback()
                if (datetime.datetime.now() > end_time):
                    raise _Timeout()
                time.sleep(1)

            for i, p in enumerate(popens):
                self.logger.debug(
                    'executePipe-result: [%s] %s, rc=%s',
                    i,
                    p['args']['args'],
                    p['popen'].returncode,
                )

            return {
                'stdout': (
                    popens[-1]['streams']['stdout']['buffer']
                    if popens[-1]['streams']['stdout']['pipe']
                    else popens[-1]['streams']['stdout']
                ),
                'result': [
                    {
                        'rc': p['popen'].returncode,
                        'stderr': (
                            p['streams']['stderr']['buffer']
                            if p['streams']['stderr']['pipe']
                            else p['streams']['stderr']
                        ),
                    }
                    for p in popens
                ],
            }

        except Exception as e:
            for p in popens:
                if 'streams' in p:
                    for s in p['streams'].values():
                        if 'buffer' in s and s['buffer']:
                            s['buffer'] = 'Deleted'
            self.logger.debug(
                'executePipeRaw exception: kw:%s\npopens:%s\nfds:%s',
                popenArgs,
                popens,
                fds,
                exc_info=True
            )

            for popen in popens:
                if popen['popen'].poll() is None:
                    popen['popen'].kill()
                for stream in popen['streams'].values():
                    if (
                        stream['stream'] is not None and
                        not stream['stream'].closed
                    ):
                        stream['stream'].close()

            raise RuntimeError(
                _("Command '{command}' failed to execute: {error}").format(
                    command=(
                        ' | '.join([
                            ' '.join(kw['args'])
                            for kw in popenArgs
                        ])
                    ),
                    error=e,
                )
            )

    def executePipe(
        self,
        popenArgs,
        raiseOnError=True,
        logStreams=True,
        stdin=None,
        **kwargs
    ):
        """Execute a list of system commands in a pipeline.

        Keyword arguments:
        popenArgs - a list of dictionaries, each a **kwarg for Popen
        raiseOnError -- raise exception if the return code of one of the
                commands is not zero.
        logStreams -- log streams' content.
        stdin -- a list of lines.
        kwargs - extra kwargs to executePipeRaw.

        Returns a dict d:
        d['stdout'] - output of last process, list of lines
        d['result'] - a list of dicts, one per process:
        d['result'][n]['rc'] - return code of process n
        d['result'][n]['stderr'] - stderr of process n, list of lines

        For each dict in popenArgs:
        'stdin' and 'stdout' are set as needed.
        'env' is appended to from envAppend if it's not None.
        rest of data is passed as-is to Popen.
        """
        if stdin is not None:
            if isinstance(stdin, tuple) or isinstance(stdin, list):
                stdin = '%s%s' % (
                    '\n'.join(stdin),
                    '\n' if stdin else '',
                )

            if logStreams:
                self.logger.debug(
                    'executePipe-input: %s stdin:\n%s\n',
                    popenArgs[0]['args'],
                    stdin
                )

            if isinstance(stdin, str):
                stdin = stdin.encode('utf-8')

        res = self.executePipeRaw(
            popenArgs=popenArgs,
            stdin=stdin,
            **kwargs
        )

        def _splitStream(s):
            ret = None
            if s is not None:
                if (
                    not isinstance(s, bytes) and
                    not isinstance(s, str) and
                    not isinstance(s, builtins.unicode)
                ):
                    s = s.read()
                if isinstance(s, bytes):
                    # warning: python-2.6 does not have kwargs for decode
                    s = s.decode('utf-8', 'replace')
                ret = s.splitlines()
            return ret

        def _listToString(l):
            return '' if l is None else '\n'.join(l)

        res['stdout'] = _splitStream(res['stdout'])
        for r in res['result']:
            r['stderr'] = _splitStream(r['stderr'])

        if logStreams:
            self.logger.debug(
                'executePipe-output: %s stdout:\n%s\n',
                popenArgs[-1]['args'],
                _listToString(res['stdout']),
            )
            for i, r, kw in [
                (i, r, popenArgs[i])
                for i, r in enumerate(res['result'])
            ]:
                self.logger.debug(
                    'executePipe-output: [%s] %s stderr:\n%s\n',
                    i,
                    kw['args'],
                    _listToString(r['stderr']),
                )

        if (
            raiseOnError and
            set([0]) != set([r['rc'] for r in res['result']])
        ):
            raise RuntimeError(
                _("Command '{command}' failed to execute").format(
                    command=(
                        ' | '.join([
                            ' '.join(kw['args'])
                            for kw in popenArgs
                        ])
                    ),
                )
            )

        return res

    def executeRaw(
        self,
        args,
        executable=None,
        stdin=None,
        cwd=None,
        env=None,
        preexec_fn=None,
        envAppend=None,
    ):
        """Execute a process.

        Keyword arguments:
        args -- a list of command arguments.
        executable -- executable name.
        stdin -- binary blob.
        cwd -- working directory.
        env -- environment dictionary.
        envAppend -- append environment.

        Returns:
        (rc, stdout, stderr)

        stdout, stderr binary blobs.
        """
        try:
            if envAppend is not None:
                if env is None:
                    env = os.environ
                env = env.copy()
                env.update(envAppend)

            self.logger.debug(
                "execute: %s, executable='%s', cwd='%s', env=%s",
                args,
                executable,
                cwd,
                env,
            )
            p = subprocess.Popen(
                args,
                executable=executable,
                stdin=subprocess.PIPE if stdin is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                cwd=cwd,
                env=env,
                preexec_fn=preexec_fn,
            )
            stdout, stderr = p.communicate(input=stdin)
            rc = p.returncode
            self.logger.debug(
                'execute-result: %s, rc=%s',
                args,
                rc,
            )
        except:
            self.logger.debug(
                'execute-result: %s, exception',
                args,
                exc_info=True
            )
            raise

        return (rc, stdout, stderr)

    def execute(
        self,
        args,
        raiseOnError=True,
        logStreams=True,
        stdin=None,
        *eargs,
        **kwargs
    ):
        """Execute system command.

        Keyword arguments:
        args -- a list of command arguments.
        raiseOnError -- raise exception if an error.
        logStreams -- log streams' content.
        stdin -- a list of lines.
        eargs -- extra args to subprocess.Popen.
        kwargs - extra kwargs to subprocess.Popen.

        Returns:
        (rc, stdout, stderr)

        stdout, stderr are list of lines.
        """
        if logStreams and stdin is not None:
            self.logger.debug(
                'execute-input: %s stdin:\n%s\n',
                args,
                '\n'.join(stdin)
            )
        (rc, stdout, stderr) = self.executeRaw(
            args=args,
            stdin=(
                '\n'.join(stdin).encode('utf-8')
                if stdin is not None else None
            ),
            *eargs,
            **kwargs
        )
        # warning: python-2.6 does not have kwargs for decode
        stdout = stdout.decode('utf-8', 'replace').splitlines()
        stderr = stderr.decode('utf-8', 'replace').splitlines()
        if logStreams:
            self.logger.debug(
                'execute-output: %s stdout:\n%s\n',
                args,
                '\n'.join(stdout)
            )
            self.logger.debug(
                'execute-output: %s stderr:\n%s\n',
                args,
                '\n'.join(stderr)
            )
        if rc != 0 and raiseOnError:
            raise RuntimeError(
                _("Command '{command}' failed to execute").format(
                    command=args[0],
                )
            )
        return (rc, stdout, stderr)


# vim: expandtab tabstop=4 shiftwidth=4
