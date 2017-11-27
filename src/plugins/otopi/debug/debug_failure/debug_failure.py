#
# otopi -- plugable installer
#


""" Debug Failures plugin."""


import gettext


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import transaction


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """Debug Failure.
    """

    class DebugFailureTransaction(transaction.TransactionElement):
        """
        Debug Failures transaction element
        """

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _("Debug Failures Transaction")

        def prepare(self):
            pass

        def abort(self):
            self._parent.execute(
                args=(
                    self._parent.command.get('ss'),
                    '--all',
                    '--numeric',
                    '--processes',
                ),
            )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        after=(
            constants.Stages.TRANSACTIONS_INIT,
        ),
    )
    def _debug_failure_init(self):
        # We add ourselves at STAGE_INIT, hopefully as first,
        # because otopi (currently) calls the 'abort' methods in the same
        # order that the elements were added, and we hope to be first, as
        # close as possible to the failure.
        self.environment[
            constants.CoreEnv.MAIN_TRANSACTION
        ].append(
            self.DebugFailureTransaction(
                parent=self,
            )
        )
        self.command.detect('ss')


# vim: expandtab tabstop=4 shiftwidth=4
