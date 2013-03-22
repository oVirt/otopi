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


import os
import subprocess
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
        STAGE_CUSTOMIZATION,
        STAGE_VALIDATION,
        STAGE_TRANSACTION_BEGIN,
        STAGE_PACKAGES,
        STAGE_MISC,
        STAGE_TRANSACTION_END,
        STAGE_CLOSEUP,
        STAGE_CLEANUP,
        STAGE_PRE_TERMINATE,
        STAGE_TERMINATE,
        STAGE_REBOOT,
    ) = range(16)

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
            'description': _("Installation packages setup"),
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
    before=[],
    after=[],
    priority=Stages.PRIORITY_DEFAULT,
    condition=None,
):
    """Decoration to specify sequence event method.

    Keyword arguments:
    name -- name of stage.
    stage -- stage out of Stages.STAGE_*.
    before -- place before plugin.
    after -- place after plugin.
    priority -- priority out of Stages.PRIORITY_*.
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

    def executeRaw(
        self,
        args,
        executable=None,
        stdin=None,
        cwd=None,
        env=None,
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

        stdour, stderr binary blobs.
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

    def execute(self, args, raiseOnError=True, stdin=None, *eargs, **kwargs):
        """Execute system command.

        Keyword arguments:
        args -- a list of command arguments.
        raiseOnError -- raise exception if an error.
        stdin -- a list of lines.
        eargs -- extra args to subprocess.Popen.
        kwargs - extra kwargs to subprocess.Popen.

        Returns:
        (rc, stdout, stderr)

        stdour, stderr are list of lines.
        """
        if stdin is not None:
            self.logger.debug(
                'execute-input: %s stdin:\n%s\n',
                args,
                '\n'.join(stdin)
            )
        (rc, stdout, stderr) = self.executeRaw(
            args=args,
            stdin=(
                '\n'.join(stdin).encode(encoding='utf-8')
                if stdin is not None else None
            ),
            *eargs,
            **kwargs
        )
        stdout = stdout.decode(encoding='utf-8', errors='replace').splitlines()
        stderr = stderr.decode(encoding='utf-8', errors='replace').splitlines()
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
