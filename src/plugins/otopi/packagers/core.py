#
# otopi -- plugable installer
#


"""core."""


from otopi import constants
from otopi import packager
from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase, packager.PackagerBase):
    """core"""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        name=constants.Stages.PACKAGERS_DETECTION,
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _init(self):
        # This is just a marker for when packagers where detected
        pass


# vim: expandtab tabstop=4 shiftwidth=4
