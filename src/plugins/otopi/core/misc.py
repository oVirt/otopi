#
# otopi -- plugable installer
#


"""Misc plugin."""


import gettext


from otopi import config
from otopi import constants
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """Misc plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        after=(
            constants.Stages.CORE_LOG_INIT,
        ),
    )
    def _init(self):
        self.environment[
            constants.CoreEnv.PACKAGE_NAME
        ] = config.PACKAGE_NAME
        self.environment[
            constants.CoreEnv.PACKAGE_VERSION
        ] = config.PACKAGE_VERSION

        self.context.dumpSequence()

        # as we want full dump and not delta
        # of something before log was active
        self.context.dumpEnvironment()

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _setup(self):
        self.dialog.note(
            text=_('Version: {package}-{version} ({local_version})').format(
                package=config.PACKAGE_NAME,
                version=config.PACKAGE_VERSION,
                local_version=config.LOCAL_VERSION,
            )
        )
        self.context.checkSequence()

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _validation(self):
        # as we want full dump and not delta
        # of something before validation
        self.context.dumpEnvironment()

    @plugin.event(
        stage=plugin.Stages.STAGE_PRE_TERMINATE,
    )
    def _preTerminate(self):
        # as we want full dump and not delta
        # of something before termination
        self.context.dumpEnvironment()


# vim: expandtab tabstop=4 shiftwidth=4
