#
# otopi -- plugable installer
#


"""Command provider."""


import os


from otopi import command
from otopi import constants
from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase, command.CommandBase):
    """Command provider.

    Environment:
        SysEnv.COMMAND_PATH -- search path.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    def _search_one_cmd(self, cmd, searchPath=None):
        if searchPath is None:
            searchPath = self.environment[
                constants.SysEnv.COMMAND_PATH
            ].split(':')
        if self.command.get(command=cmd, optional=True) is None:
            for path in searchPath:
                cmdPath = os.path.join(path, cmd)
                if os.path.exists(cmdPath):
                    self.command.set(command=cmd, path=cmdPath)
                    break

    def _search(self):
        searchPath = self.environment[
            constants.SysEnv.COMMAND_PATH
        ].split(':')
        for cmd in self.command.enum():
            self._search_one_cmd(cmd, searchPath)

    def get(self, command, optional=False):
        res = super(Plugin, self).get(command, optional=True)
        if not res and not optional:
            # Try harder.
            self.logger.debug(
                'command %s not detected yet, searching',
                command
            )
            self._search_one_cmd(command)
            res = super(Plugin, self).get(command, optional)
        return res

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _init(self):
        self.environment.setdefault(
            constants.SysEnv.COMMAND_PATH,
            (
                os.environ.get(constants.SystemEnvironment.SYS_PATH) or
                constants.Defaults.COMMAND_SEARCH_PATH
            )
        )
        self.context.registerCommand(command=self)

    @plugin.event(
        name=constants.Stages.SYSTEM_COMMAND_DETECTION,
        stage=plugin.Stages.STAGE_PROGRAMS,
    )
    def _programs(self):
        self._search()

    @plugin.event(
        name=constants.Stages.SYSTEM_COMMAND_REDETECTION,
        stage=plugin.Stages.STAGE_MISC,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _misc(self):
        self._search()


# vim: expandtab tabstop=4 shiftwidth=4
