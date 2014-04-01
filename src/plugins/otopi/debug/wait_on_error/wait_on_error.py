#
# otopi -- plugable installer
#


""" Wait on error plugin."""


import gettext
import logging
import os

from otopi import constants
from otopi import util
from otopi import plugin


def _(m): gettext.dgettext(message=m, domain='ovirt-engine-setup')


class WOEHandler(logging.Handler):

    def __init__(self, plugin):
        logging.Handler.__init__(self)
        self._plugin = plugin

    def emit(self, record):
        if record.levelno == logging.ERROR:
            self._plugin.dialog.queryString(
                name='WAIT_ON_ERR_ANS',
                note="Press Enter to continue.",
                prompt=True,
                default='y'  # Allow enter without any value
            )


@util.export
class Plugin(plugin.PluginBase):
    """ Wait on error plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = os.environ.get(
            constants.SystemEnvironment.WAIT_ON_ERROR
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_LOW,
        condition=lambda self: self._enabled,
    )
    def _init(self):
        logger = logging.getLogger(constants.Log.LOGGER_BASE)
        logger.addHandler(WOEHandler(self))


# vim: expandtab tabstop=4 shiftwidth=4
