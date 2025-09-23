#
# otopi -- plugable installer
#


"""iptables handler plugin."""


import distro
import gettext


from otopi import constants
from otopi import filetransaction
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """iptables updater.

    Environment:
        NetEnv.IPTABLES_ENABLE -- enable iptables update
        NetEnv.IPTABLES_RULES -- iptables rules (multi-string)

    """
    REDHAT_IPTABLES = '/etc/sysconfig/iptables'

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._distribution = distro.id()
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(constants.NetEnv.IPTABLES_ENABLE, False)
        self.environment.setdefault(constants.NetEnv.IPTABLES_RULES, None)

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        name=constants.Stages.IPTABLES_VALIDATION,
        condition=(
            lambda self: self.environment[constants.NetEnv.IPTABLES_ENABLE]
        ),
    )
    def _validate(self):
        if self._distribution not in (
            'redhat',
            'fedora',
            'centos',
            'ibm_powerkvm',
            'rhel',
        ):
            self.logger.warning(
                _('Unsupported distribution for iptables plugin')
            )
        else:
            self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        if not self.packager.install(
            ('iptables-services',),
            ignoreErrors=True,
        ):
            self.packager.install(('iptables',))

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _store_iptables(self):
        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=self.REDHAT_IPTABLES,
                owner='root',
                mode=0o600,
                enforcePermissions=True,
                content=self.environment[
                    constants.NetEnv.IPTABLES_RULES
                ],
                modifiedList=self.environment[
                    constants.CoreEnv.MODIFIED_FILES
                ],
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._enabled,
    )
    def _closeup(self):
        # We would like to avoid conflict
        if self.services.exists('firewalld'):
            self.services.startup('firewalld', False)
            self.services.state('firewalld', False)
        self.services.startup('iptables', True)
        self.services.state('iptables', False)
        self.services.state('iptables', True)


# vim: expandtab tabstop=4 shiftwidth=4
