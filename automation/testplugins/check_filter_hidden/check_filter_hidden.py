#
# otopi -- plugable installer
#


"""check_filter_hidden."""


from otopi import constants
from otopi import plugin
from otopi import util

KEY = 'myTestKey'

@util.export
class Plugin(plugin.PluginBase):
    """check_filter_hidden."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
    )
    def _customization(self):
        self.environment[
            KEY
        ] = self.dialog.queryString(
            name='CHECK_FILTER_HIDDEN',
            note='Input some value(hidden):',
            prompt=True,
            hidden=True,
        )

# vim: expandtab tabstop=4 shiftwidth=4
