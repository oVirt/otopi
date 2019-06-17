#
# otopi -- plugable installer
#


"""systemd services provider."""


import gettext


from otopi import constants
from otopi import plugin
from otopi import services
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase, services.ServicesBase):
    """systemd services provider."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('systemctl')

    @plugin.event(
        stage=plugin.Stages.STAGE_PROGRAMS,
        after=(
            constants.Stages.SYSTEM_COMMAND_DETECTION,
        ),
    )
    def _programs(self):
        systemctl = self.command.get('systemctl', optional=True)
        if systemctl is not None:
            (ret, stdout, stderr) = self.execute(
                (systemctl, 'show-environment'),
                raiseOnError=False,
            )
            if ret == 0:
                self.logger.debug('registering systemd provider')
                self.context.registerServices(services=self)

    #
    # ServicesBase
    #

    def _executeServiceCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (
                self.command.get('systemctl'),
            ) +
            (command if isinstance(command, tuple) else (command,)) +
            (
                '%s.service' % name,
            ),
            raiseOnError=raiseOnError
        )

    def _executeSocketCommand(self, name, command, raiseOnError=True):
        return self.execute(
            (
                self.command.get('systemctl'),
            ) +
            (command if isinstance(command, tuple) else (command,)) +
            (
                '%s.socket' % name,
            ),
            raiseOnError=raiseOnError
        )

    @property
    def supportsDependency(self):
        return True

    def exists(self, name):
        self.logger.debug('check if service %s exists', name)
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            (
                'show',
                '-p',
                'LoadState',
            ),
            raiseOnError=False,
        )
        return (
            rc == 0 and
            stdout and
            stdout[0].strip() == 'LoadState=loaded'
        )

    def status(self, name):
        self.logger.debug('check service %s status', name)
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            'status',
            raiseOnError=False,
        )
        return rc == 0

    def startup(self, name, state):
        self.logger.debug('set service %s startup to %s', name, state)

        # resolve service name
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            (
                'show',
                '-p',
                'Id',
            )
        )
        if len(stdout) == 1:
            name = stdout[0].split('=')[1].strip().replace('.service', '')

        rc, stdout, stderr = self._executeServiceCommand(
            name,
            'enable' if state else 'disable',
            raiseOnError=False,
        )
        if rc != 0:
            raise RuntimeError(
                _("Failed to {do} service '{service}'").format(
                    do=_('enable') if state else _('disable'),
                    service=name,
                )
            )

    def startupSocket(self, name, state):
        self.logger.debug('set socket %s startup to %s', name, state)

        # resolve service name
        rc, stdout, stderr = self._executeSocketCommand(
            name,
            (
                'show',
                '-p',
                'Id',
            )
        )
        if len(stdout) == 1:
            name = stdout[0].split('=')[1].strip().replace('.socket', '')

        rc, stdout, stderr = self._executeSocketCommand(
            name,
            'enable' if state else 'disable',
            raiseOnError=False,
        )
        if rc != 0:
            raise RuntimeError(
                _("Failed to {do} socket '{service}'").format(
                    do=_('enable') if state else _('disable'),
                    service=name,
                )
            )

    def state(self, name, state):
        self.logger.debug(
            '%s service %s',
            'starting' if state else 'stopping',
            name
        )
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            'start' if state else 'stop',
            raiseOnError=False,
        )
        if rc != 0:
            raise RuntimeError(
                _("Failed to {do} service '{service}'").format(
                    do=_('start') if state else _('stop'),
                    service=name,
                )
            )

    def restart(self, name):
        self.logger.debug(
            'restarting service %s',
            name
        )
        rc, stdout, stderr = self._executeServiceCommand(
            name,
            'restart',
            raiseOnError=False,
        )
        if rc != 0:
            raise RuntimeError(
                _("Failed to restart service '{service}'").format(
                    service=name,
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
