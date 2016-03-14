#
# ovirt-engine-setup -- ovirt engine setup
#


"""firewalld plugin."""


import gettext
import os
import re


from otopi import constants
from otopi import filetransaction
from otopi import plugin
from otopi import transaction
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """firewalld plugin.

    Environment:
        NetEnv.FIREWALLD_ENABLE -- enable firewalld update
        NetEnv.FIREWALLD_SERVICE_PREFIX -- services key=service value=content
        NetEnv.FIREWALLD_DISABLE_SERVICES -- list of services to be disabled

    """

    class FirewalldTransaction(transaction.TransactionElement):
        """firewalld transaction element."""

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _('Firewalld Transaction')

        def prepare(self):
            pass

        def abort(self):
            for (
                zone,
                services,
            ) in self._parent._disabled_zones_services.items():
                for service in services:
                    rc, stdout, stderr = self._parent.execute(
                        args=(
                            self._parent.command.get('firewall-cmd'),
                            '--zone', zone,
                            '--permanent',
                            '--add-service', service,
                        ),
                        raiseOnError=False,
                    )
                    if rc != 0:
                        self._parent.logger.debug(
                            'Error during firewalld restore',
                        )

        def commit(self):
            pass

    FIREWALLD_SERVICES_DIR = '/etc/firewalld/services'
    _ZONE_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            (?P<zone>\w+)
        """
    )
    _INTERFACE_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            \s+
            interfaces:
            \s+
            (?P<interfaces>[\w,]+)
        """
    )
    _SERVICE_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            \s+
            services:
            \s+
            (?P<services>.+)
        """
    )

    def _get_firewalld_cmd_version(self):
        version = 0

        if self.services.exists('firewalld'):
            try:
                from firewall import client

                self.logger.debug('firewalld version: %s', client.VERSION)
                version = int(
                    '%02x%02x%02x' % tuple([
                        int(x)
                        for x in client.VERSION.split('.')[:3]
                    ]),
                    16
                )
            except ImportError:
                self.logger.debug('No firewalld python module')
            except:
                self.logger.debug(
                    'Exception during firewalld dection',
                    exc_info=True,
                )

        return version

    def _get_active_zones(self):
        rc, stdout, stderr = self.execute(
            (
                self.command.get('firewall-cmd'),
                '--get-active-zones',
            ),
        )
        zones = {}
        if self._firewalld_version < 0x000303:
            for line in stdout:
                zone_name, devices = line.split(':')
                zones[zone_name] = devices.split()
        else:
            # 0.3.3 has changed output
            zone_name = None
            for line in stdout:
                zoneMatch = self._ZONE_RE.match(line)
                if zoneMatch is not None:
                    zone_name = zoneMatch.group('zone')
                else:
                    interfacesMatch = self._INTERFACE_RE.match(line)
                    if interfacesMatch is not None:
                        zones[zone_name] = interfacesMatch.group(
                            'interfaces'
                        ).split()

        return zones

    def _get_zones(self):
        rc, stdout, stderr = self.execute(
            (
                self.command.get('firewall-cmd'),
                '--get-zones',
            ),
        )
        return ' '.join(stdout).split()

    def _get_zones_services(self):
        rc, stdout, stderr = self.execute(
            (
                self.command.get('firewall-cmd'),
                '--list-all-zones',
            ),
        )
        zones = {}
        zone_name = None
        for line in stdout:
            zoneMatch = self._ZONE_RE.match(line)
            if zoneMatch is not None:
                zone_name = zoneMatch.group('zone')
            else:
                servicesMatch = self._SERVICE_RE.match(line)
                if servicesMatch is not None:
                    zones[zone_name] = servicesMatch.group(
                        'services'
                    ).split()

        return zones

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = os.geteuid() == 0
        self._enabled_services = []
        self._disabled_zones_services = {}
        self._firewalld_version = 0

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            constants.NetEnv.FIREWALLD_ENABLE,
            False
        )
        self.environment.setdefault(
            constants.NetEnv.FIREWALLD_AVAILABLE,
            False
        )
        self.environment.setdefault(
            constants.NetEnv.FIREWALLD_DISABLE_SERVICES,
            []
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        condition=lambda self: self._enabled,
    )
    def _setup(self):
        self.command.detect(command='firewall-cmd')

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        condition=lambda self: self._enabled,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _customization(self):
        self._firewalld_version = self._get_firewalld_cmd_version()
        self._enabled = self.environment[
            constants.NetEnv.FIREWALLD_AVAILABLE
        ] = self._firewalld_version >= 0x000206

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        name=constants.Stages.FIREWALLD_VALIDATION,
        condition=lambda self: self._enabled,
    )
    def _validation(self):
        self._enabled = self.environment[
            constants.NetEnv.FIREWALLD_ENABLE
        ]

    @plugin.event(
        stage=plugin.Stages.STAGE_EARLY_MISC,
        condition=lambda self: self._enabled,
    )
    def _early_misc(self):
        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            self.FirewalldTransaction(
                parent=self,
            )
        )

        #
        # avoid conflicts, disable iptables
        #
        if self.services.exists(name='iptables'):
            self.services.startup(name='iptables', state=False)
            self.services.state(name='iptables', state=False)

        self.services.state(
            name='firewalld',
            state=True,
        )
        self.services.startup(name='firewalld', state=True)

        #
        # Disabling existing services before configuration reload
        # because the service file may be emptied or removed in misc stage by
        # the plugins requesting this action and in this case reload will fail
        #
        zones_services = self._get_zones_services()
        self.logger.debug('zones_services = %s', zones_services)
        for zone in zones_services:
            for service in self.environment[
                constants.NetEnv.FIREWALLD_DISABLE_SERVICES
            ]:
                if service in zones_services[zone]:
                    self._disabled_zones_services.setdefault(
                        zone,
                        []
                    ).append(service)
                    self.execute(
                        (
                            self.command.get('firewall-cmd'),
                            '--zone', zone,
                            '--permanent',
                            '--remove-service', service,
                        ),
                    )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        for service, content in [
            (
                key[len(constants.NetEnv.FIREWALLD_SERVICE_PREFIX):],
                content,
            )
            for key, content in self.environment.items()
            if key.startswith(
                constants.NetEnv.FIREWALLD_SERVICE_PREFIX
            )
        ]:
            self._enabled_services.append(service)
            self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=os.path.join(
                        self.FIREWALLD_SERVICES_DIR,
                        '%s.xml' % service,
                    ),
                    content=content,
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
        #
        # Ensure to load the newly written services if firewalld was already
        # running.
        #
        self.execute(
            (
                self.command.get('firewall-cmd'),
                '--reload'
            )
        )
        for zone in self._get_active_zones():
            for service in self._enabled_services:
                self.execute(
                    (
                        self.command.get('firewall-cmd'),
                        '--zone', zone,
                        '--permanent',
                        '--add-service', service,
                    ),
                )
        self.execute(
            (
                self.command.get('firewall-cmd'),
                '--reload'
            )
        )


# vim: expandtab tabstop=4 shiftwidth=4
