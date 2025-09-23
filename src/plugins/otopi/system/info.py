#
# otopi -- plugable installer
#


"""System information plugin."""


import distro
import gettext
import os
import socket
import sys


from otopi import constants
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """Misc plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        after=(
            constants.Stages.CORE_LOG_INIT,
        ),
    )
    def _init(self):
        self.logger.debug('SYSTEM INFORMATION - BEGIN')
        self.logger.debug('executable %s', sys.executable)
        self.logger.debug('python version %s', sys.version)
        self.logger.debug('python %s', sys.executable)
        self.logger.debug('platform %s', sys.platform)
        self.logger.debug(
            'distribution id=%s name=%s version=%s like=%s',
            distro.id(),
            distro.name(pretty=False),
            distro.version(),
            distro.like(),
        )
        self.logger.debug("host '%s'", socket.gethostname())
        self.logger.debug(
            'uid %s euid %s gid %s egid %s',
            os.getuid(),
            os.geteuid(),
            os.getgid(),
            os.getegid(),
        )
        self.logger.debug('SYSTEM INFORMATION - END')


# vim: expandtab tabstop=4 shiftwidth=4
