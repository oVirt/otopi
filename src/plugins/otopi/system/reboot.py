#
# otopi -- plugable installer
#


"""Reboot plugin."""


import gettext
import os
import time


from otopi import constants
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """Reboot provider.

    Environment:
        SysEnv.REBOOT -- should we reboot.
        SysEnv.REBOOT_ALLOW -- do we allow reboot.
        SysEnv.REBOOT_DEFER_TIME -- how much time to wait in background.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    def _simpleDaemon(self, main, args=(), kwargs={}):
        # Default maximum for the number of available file descriptors.
        MAXFD = 1024

        import resource  # Resource usage information.
        maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
        if (maxfd == resource.RLIM_INFINITY):
            maxfd = MAXFD

        pid = os.fork()
        if pid == 0:
            try:
                os.chdir('/')
                os.setsid()
                for fd in range(0, maxfd):
                    try:
                        os.close(fd)
                    except OSError:
                        # ERROR, fd wasn't open to begin with (ignored)
                        pass

                os.open(os.devnull, os.O_RDWR)  # standard input (0)
                os.dup2(0, 1)  # standard output (1)
                os.dup2(0, 2)  # standard error (2)

                if os.fork() != 0:
                    os._exit(0)

                try:
                    main(*args, **kwargs)
                except:
                    import traceback
                    traceback.print_exc()
            finally:
                os._exit(1)

        pid, status = os.waitpid(pid, 0)

        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            raise RuntimeError(_('Daemon not exited properly'))

    def _delayedReboot(self, reboot, sleepTime):
        time.sleep(sleepTime)
        os.execl(reboot, reboot)

    def _doReboot(self):
        return (
            self.environment[constants.SysEnv.REBOOT] and
            self.environment[constants.SysEnv.REBOOT_ALLOW]
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(constants.SysEnv.REBOOT, False)
        self.environment.setdefault(constants.SysEnv.REBOOT_ALLOW, True)
        self.environment.setdefault(constants.SysEnv.REBOOT_DEFER_TIME, 10)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('reboot')

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        priority=plugin.Stages.PRIORITY_LAST,
        condition=_doReboot,
    )
    def _closeup(self):
        self.command.get('reboot')  # exception...
        self.logger.info(_('Reboot scheduled'))

    @plugin.event(
        stage=plugin.Stages.STAGE_REBOOT,
        condition=_doReboot,
    )
    def _reboot(self):
        self.logger.debug("scheduling reboot")
        self._simpleDaemon(
            self._delayedReboot,
            (
                self.command.get('reboot'),
                self.environment[constants.SysEnv.REBOOT_DEFER_TIME],
            )
        )
        self.logger.debug("Reboot scheduled")


# vim: expandtab tabstop=4 shiftwidth=4
