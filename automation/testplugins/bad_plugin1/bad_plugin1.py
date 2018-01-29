#
# otopi -- plugable installer
#


"""Bad plugin 1."""


from otopi import constants
from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase):
    """Bad plugin 1."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        after=(
            constants.Stages.PACKAGERS_DETECTION
        ),
    )
    def _init(self):
        pass


# vim: expandtab tabstop=4 shiftwidth=4
