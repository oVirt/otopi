#
# otopi -- plugable installer
#


""" Test Note plugin."""


from otopi import constants
from otopi import util
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """ Test Note plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._note = self.environment.setdefault(constants.DebugEnv.NOTE, None)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        condition=lambda self: self._note is not None,
    )
    def _setup(self):
        self.dialog.note(f'Debug note:\n{self._note}')


# vim: expandtab tabstop=4 shiftwidth=4
