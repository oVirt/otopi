#
# otopi -- plugable installer
#


"""Transaction plugin."""


from otopi import constants
from otopi import plugin
from otopi import transaction
from otopi import util


@util.export
class Plugin(plugin.PluginBase):
    """Transaction provider.

    Prepare transaction at STAGE_TRANSACTION_END.

    Commit transaction at STAGE_TRANSACTION_END.

    Listen for error notification and rollback transaction in this case.

    Environment:
        CoreEnv.INTERNAL_PACKAGES_TRANSACTION -- transaction object.
        CoreEnv.MAIN_TRANSACTION -- transaction object.

    Users of this module can acquire transaction object
    out of the environment at CoreEnv.MAIN_TRANSACTION.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    def _notify(self, event):
        if event == self.context.NOTIFY_ERROR:
            if self._internalPackageTransaction is not None:
                self._internalPackageTransaction.abort()
                self._internalPackageTransaction = None
            if self._mainTransaction is not None:
                self._mainTransaction.abort()
                self._mainTransaction = None

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        name=constants.Stages.TRANSACTIONS_INIT,
    )
    def _init(self):
        self._internalPackageTransaction = transaction.Transaction()
        self._mainTransaction = transaction.Transaction()
        self.environment[
            constants.CoreEnv.INTERNAL_PACKAGES_TRANSACTION
        ] = self._internalPackageTransaction
        self.environment[
            constants.CoreEnv.MAIN_TRANSACTION
        ] = self._mainTransaction
        self.environment[
            constants.CoreEnv.MODIFIED_FILES
        ] = []
        self.context.registerNotification(self._notify)

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _pre_prepare(self):
        self._internalPackageTransaction.prepare()

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
        priority=plugin.Stages.PRIORITY_LAST + 10,
    )
    def _pre_end(self):
        try:
            self._internalPackageTransaction.commit()
        except Exception:
            self._internalPackageTransaction.abort()
            raise
        finally:
            self._internalPackageTransaction = None

    @plugin.event(
        stage=plugin.Stages.STAGE_TRANSACTION_BEGIN,
    )
    def _main_prepare(self):
        self._mainTransaction.prepare()

    @plugin.event(
        stage=plugin.Stages.STAGE_TRANSACTION_END,
    )
    def _main_end(self):
        try:
            self._mainTransaction.commit()
        except Exception:
            self._mainTransaction.abort()
            raise
        finally:
            self._mainTransaction = None


# vim: expandtab tabstop=4 shiftwidth=4
