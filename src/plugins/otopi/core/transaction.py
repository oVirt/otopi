#
# otopi -- plugable installer
# Copyright (C) 2012 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""Transaction plugin."""


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import transaction


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
        except:
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
        except:
            self._mainTransaction.abort()
            raise
        finally:
            self._mainTransaction = None
