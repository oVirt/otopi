#
# otopi -- plugable installer
#


""" Test Command plugin."""


import os

from otopi import constants
from otopi import util
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """ Test Command plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = os.environ.get(
            constants.SystemEnvironment.TEST_COMMAND
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        condition=lambda self: self._enabled,
    )
    def _init_detect_get_ls(self):
        # Detect and get early
        self.logger.debug('test_command: detect ls')
        self.command.detect('ls')
        self.logger.debug('test_command: get ls')
        ls = self.command.get('ls')
        self.logger.debug('test_command: get ls result: %s', ls)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        condition=lambda self: self._enabled,
    )
    def _init_detect_du(self):
        # Detect early, get later
        self.logger.debug('test_command: detect du')
        self.command.detect('du')

    @plugin.event(
        stage=plugin.Stages.STAGE_LATE_SETUP,
        condition=lambda self: self._enabled,
    )
    def _late_setup_get_du(self):
        # Get earlier detected
        self.logger.debug('test_command: get du')
        du = self.command.get('du')
        self.logger.debug('test_command: get du result: %s', du)

    @plugin.event(
        stage=plugin.Stages.STAGE_LATE_SETUP,
        condition=lambda self: self._enabled,
    )
    def _late_setup_detect_get_mv(self):
        # Detect and get late
        self.logger.debug('test_command: detect mv')
        self.command.detect('mv')
        self.logger.debug('test_command: get mv')
        mv = self.command.get('mv')
        self.logger.debug('test_command: get mv result: %s', mv)


# vim: expandtab tabstop=4 shiftwidth=4
