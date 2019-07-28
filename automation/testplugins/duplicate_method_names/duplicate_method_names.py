#
# otopi -- plugable installer
#


"""Duplicate method names."""


from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase):
    """Duplicate method names."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        name='duplicate_name1',
    )
    def _duplicate_name1_1(self):
        pass

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        name='duplicate_name1',
    )
    def _duplicate_name1_2(self):
        pass


# vim: expandtab tabstop=4 shiftwidth=4
