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


"""Command interface.

Command is the component responsible of locating system commands.

"""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from . import constants
from . import util


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
