#
# otopi -- plugable installer
#


"""Event Cyclic Dependency."""


from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase):
    """Event Cyclic Dependency."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        name='cycdep1',
        after=(
            'cycdep2',
        ),
    )
    def _cycdep1(self):
        pass

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        name='cycdep2',
        after=(
            'cycdep1',
        ),
    )
    def _cycdep2(self):
        pass


# vim: expandtab tabstop=4 shiftwidth=4
