#
# otopi -- plugable installer
#


"""Non-existent Before/After."""


from otopi import plugin
from otopi import util


@util.export
class Plugin(plugin.PluginBase):
    """Non-existent Before/After."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        after=(
            'non-existent-after',
        ),
        before=(
            'non-existent-before',
        ),
    )
    def _non_existent_before_after(self):
        pass


# vim: expandtab tabstop=4 shiftwidth=4
