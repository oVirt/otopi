#
# otopi -- plugable installer
#


"""Command interface.

Command is the component responsible of locating system commands.

"""


import gettext


from . import constants
from . import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class CommandBase(object):
    """Base class for command.

    Base class for all command providers.

    """
    def _commandKey(self, command):
        return "%s%s" % (constants.BaseEnv.COMMAND_PREFIX, command)

    def detect(self, command):
        """Request command detection.

        Keyword arguments:
        command -- command to detect.

        """
        self.environment.setdefault(
            self._commandKey(command=command),
            None
        )

    def set(self, command, path):
        """Set command.

        Keyword arguments:
        command -- command to detect.
        path -- path of command.

        """
        self.environment[self._commandKey(command=command)] = path

    def get(self, command, optional=False):
        """Get command.

        Keyword arguments:
        command -- command to get.
        required -- raise exception if not found.

        Returns:
        Command path or None.

        """
        path = self.environment.setdefault(
            self._commandKey(command=command),
            None
        )
        if path is None and not optional:
            raise RuntimeError(
                _("Command '{command}' is required but missing").format(
                    command=command
                )
            )
        return path

    def enum(self):
        """Enumerate commands.

        Returns:
        List of commands.

        """
        return [
            cmd.replace(constants.BaseEnv.COMMAND_PREFIX, '', 1)
            for cmd in self.environment
            if cmd.startswith(constants.BaseEnv.COMMAND_PREFIX)
        ]


# vim: expandtab tabstop=4 shiftwidth=4
