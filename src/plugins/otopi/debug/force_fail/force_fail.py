#
# otopi -- plugable installer
#


""" Force fail plugin."""


import gettext
import os

from otopi import constants
from otopi import util
from otopi import plugin


def _(m): gettext.dgettext(message=m, domain='ovirt-engine-setup')


_stage = None
_prio = plugin.Stages.PRIORITY_DEFAULT
_enabled = False
# TODO add before/after


def _init_plugin():
    global _stage, _prio, _enabled
    _stage = os.environ.get(
        constants.SystemEnvironment.FORCE_FAIL_STAGE,
    )
    _prio = os.environ.get(
        constants.SystemEnvironment.FORCE_FAIL_PRIORITY,
    )
    if _stage is None:
        _stage = plugin.Stages.STAGE_INIT
    else:
        _enabled = True
        if _stage is not None and hasattr(plugin.Stages, _stage):
            _stage = getattr(plugin.Stages, _stage)
        if _prio is not None and hasattr(plugin.Stages, _prio):
            _prio = getattr(plugin.Stages, _prio)
        if _prio is None:
            _prio = plugin.Stages.PRIORITY_DEFAULT

# Need to be called before the Plugin class definition, because
# the globals need to have their values for the annotation to work.
# That's also why we can't allow setting this in the answer file -
# the answer files are processed only after plugins are loaded, by
# the core/config.py plugin.
_init_plugin()


@util.export
class Plugin(plugin.PluginBase):
    """ Force failure plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=_stage,
        priority=_prio,
        condition=lambda self: _enabled,
    )
    def _force_fail_do(self):
        raise RuntimeError(
            "Force Fail: stage %s priority %s" %
            (
                _stage,
                _prio,
            )
        )


# vim: expandtab tabstop=4 shiftwidth=4
