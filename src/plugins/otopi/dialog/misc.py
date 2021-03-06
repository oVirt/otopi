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
        name=constants.Stages.DIALOG_MISC_BOOT,
        after=(
            constants.Stages.CORE_LOG_INIT,
        ),
    )
    def _init(self):
        self.environment.setdefault(
            constants.DialogEnv.DIALECT,
            constants.Const.DIALOG_DIALECT_HUMAN,
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        name=constants.Stages.DIALOG_BOOT_DONE,
    )
    def _boot_misc_done(self):
        pass


# vim: expandtab tabstop=4 shiftwidth=4
