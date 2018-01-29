#
# otopi -- plugable installer
#


"""Change Env Type."""


from otopi import constants
from otopi import plugin
from otopi import util

KEY = 'myTestKey'

@util.export
class Plugin(plugin.PluginBase):
    """Change Env Type."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(KEY, None)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.environment[KEY] = '1234'

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
    )
    def _customization(self):
        self.environment[KEY] = 1234

# vim: expandtab tabstop=4 shiftwidth=4
