#
# otopi -- plugable installer
#


"""Misc plugin."""


from otopi import constants
from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase):
    """Misc dialog settings.

    Environment:
        DialogEnv.DIALECT -- set default dialect.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _init(self):
        self.environment.setdefault(
            constants.DialogEnv.DIALECT,
            constants.Const.DIALOG_DIALECT_HUMAN,
        )


# vim: expandtab tabstop=4 shiftwidth=4
