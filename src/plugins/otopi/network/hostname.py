#
# otopi -- plugable installer
#


"""Host name validation plugin."""


import gettext
import re
import socket


from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """Host name validation.

    Check if reverse lookup of local name resolves
    to one of the interfaces address except of loopback.

    """
    _ADDRESS_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^\s*inet\s+(?P<ipv4>[0-9.]+)/.*
            |
            ^\s*inet6\s+(?P<ipv6>[0-9a-f:]+)/.*
        """
    )

    MSG_PREFIX = _('Cannot validate host name settings, reason: {reason}')

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('ip')

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
    )
    def _internal_packages(self):
        self.packager.install(packages=('iproute',))

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
    )
    def _validation(self):
        myname = socket.gethostname()
        self.logger.debug('my name: %s', myname)
        try:
            myaddresses = [
                address[0] for __, __, __, __, address in
                socket.getaddrinfo(
                    myname,
                    None
                )
            ]

            (rc, stdout, stderr) = self.execute(
                (
                    self.command.get('ip'),
                    'addr',
                    'show'
                ),
                raiseOnError=False,
            )
            if rc != 0:
                self.logger.warning(
                    self.MSG_PREFIX.format(
                        reason=_('cannot enumerate interface addresses')
                    )
                )
            else:
                addresses = []
                for l in stdout:
                    m = self._ADDRESS_RE.match(l)
                    if m is not None:
                        for g in ('ipv4', 'ipv6'):
                            if m.group(g) is not None:
                                addresses.append(m.group(g))
                addresses = [
                    address for address in addresses
                    if not address.startswith('127.') and not address == '::1'
                ]

                self.logger.debug('my addresses: %s', myaddresses)
                self.logger.debug('local addresses: %s', addresses)
                if not set(addresses) & set(myaddresses):
                    self.logger.warning(
                        self.MSG_PREFIX.format(
                            reason=_(
                                'resolved host does not match any of the '
                                'local addresses'
                            )
                        )
                    )

        except socket.error:
            self.logger.debug('exception during resolve', exc_info=True)
            self.logger.warning(
                self.MSG_PREFIX.format(
                    reason=_("cannot resolve own name '{name}'").format(
                        name=myname
                    )
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
