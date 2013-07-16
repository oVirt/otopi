#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
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


"""SSH key installer plugin."""


import os
import getpass
import re
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import plugin
from otopi import filetransaction


@util.export
class Plugin(plugin.PluginBase):
    """SSH key installer.

    Environment:
        NetEnv.SSH_ENABLE -- enable key install.
        NetEnv.SSH_KEY -- ssh public key.
        NetEnv.SSH_USER -- user to install into.

    Try as much as possible not to alter file.

    Remove duplicate public keys of ours' key.

    Remove different alias of ours' key.

    If we create the file, we should also restore SELinux
    properties (if available).

    """
    _RE_SSHPUB = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            \s*
            ssh-(?P<algo>rsa|dss)
            \s+
            (?P<public>[A-Za-z0-9+/]+={0,2})
            (?P<alias>\s+[^\s]+)?
            \s*
            $
        """
    )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False

    def _mergeAuthKeysFile(self, authkeys, sshKey):
        found = False
        content = []

        with open(authkeys, 'r') as f:
            current = f.read().splitlines()

        keymatch = self._RE_SSHPUB.match(sshKey)
        for line in current:
            linematch = self._RE_SSHPUB.match(line)
            append = True
            if linematch is not None:

                # find matching public key
                # remove duplicates
                # accept only our key name
                if (
                    (
                        linematch.group('algo'),
                        linematch.group('public'),
                    ) == (
                        keymatch.group('algo'),
                        keymatch.group('public'),
                    )
                ):
                    if linematch.group('alias') != keymatch.group('alias'):
                        append = False
                    elif found:
                        append = False
                    else:
                        found = True

                # find matching key name
                # remove if found
                else:
                    if (
                        keymatch.group('alias') is not None and
                        keymatch.group('alias') == linematch.group('alias')
                    ):
                        append = False
            if append:
                content.append(line)

        return found, content

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(constants.NetEnv.SSH_ENABLE, False)
        self.environment.setdefault(constants.NetEnv.SSH_KEY, None)
        self.environment.setdefault(constants.NetEnv.SSH_USER, '')
        self._needSelinuxFixup = None

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('restorecon')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[constants.NetEnv.SSH_ENABLE],
    )
    def _validation(self):
        if self.environment[constants.NetEnv.SSH_KEY] is not None:
            if self._RE_SSHPUB.match(
                self.environment[constants.NetEnv.SSH_KEY]
            ) is None:
                raise RuntimeError(_('SSH public key is invalid'))
            self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _append_key(self):
        sshKey = self.environment[constants.NetEnv.SSH_KEY]
        sshUser = self.environment[constants.NetEnv.SSH_USER]
        authkeysdir = os.path.expanduser('~%s/.ssh' % sshUser)
        authkeys = os.path.join(authkeysdir, 'authorized_keys')

        content = []
        found = False
        if (
            not os.path.exists(authkeysdir) and
            self.command.get('restorecon', optional=True) is not None
        ):
            self._needSelinuxFixup = authkeysdir
        else:
            if os.path.exists(authkeys):
                found, content = self._mergeAuthKeysFile(authkeys, sshKey)

        if not found:
            content.append(sshKey)

        self.environment[constants.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=authkeys,
                content=content,
                owner=sshUser if sshUser else getpass.getuser(),
                downer=sshUser if sshUser else getpass.getuser(),
                mode=0o600,
                dmode=0o700,
                enforcePermissions=True,
                modifiedList=self.environment[
                    constants.CoreEnv.MODIFIED_FILES
                ],
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._needSelinuxFixup,
    )
    def _cleanup(self):
        rc, stdout, stderr = self.execute(
            (
                self.command.get('restorecon'),
                '-r',
                self._needSelinuxFixup
            ),
            raiseOnError=False,
        )

        if rc != 0:
            self.logger.warning(
                _('Cannot set SELinux properties on SSH directory')
            )


# vim: expandtab tabstop=4 shiftwidth=4
