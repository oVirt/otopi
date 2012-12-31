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


"""Packager interface.

Packager is the component responsible for interacting with distribution
packager.

"""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from . import util


@util.export
class PackagerBase(object):
    """Base class for packagers.

    Common interface for all packager providers.

    """
    def beginTransaction(self):
        """Begin a transaction."""
        pass

    def endTransaction(self, rollback=False):
        """End transaction

        Keyword arguments:
        rollback -- if rollback should be done.

        Notes:
        Rollback support is optional, there should be no
        exception if not supported.

        """
        pass

    def installGroup(self, group, ignoreErrors=False):
        """Install a group.

        Keyword arguments:
        group -- group to install.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        raise NotImplementedError(_('Packager installGroup not implemented'))

    def updateGroup(self, group, ignoreErrors=False):
        """Update a group.

        Keyword arguments:
        group -- group to update.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        raise NotImplementedError(_('Packager updateGroup not implemented'))

    def removeGroup(self, group, ignoreErrors=False):
        """Remove a group.

        Keyword arguments:
        group -- group to remove.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        raise NotImplementedError(_('Packager removeGroup not implemented'))

    def install(self, packages, ignoreErrors=False):
        """Install packages.

        Keyword arguments:
        packages -- packages tuple to install.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        raise NotImplementedError(_('Packager install not implemented'))

    def update(self, packages, ignoreErrors=False):
        """Update packages.

        Keyword arguments:
        packages -- packages tuple to update.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        raise NotImplementedError(_('Packager update not implemented'))

    def installUpdate(self, packages, ignoreErrors=False):
        """Install and update packages.

        Keyword arguments:
        packages -- packages tuple to install and update.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        return (
            self.install(
                packages=packages,
                ignoreErrors=ignoreErrors,
            ) or
            self.update(
                packages=packages,
                ignoreErrors=ignoreErrors,
            )
        )

    def remove(self, packages, ignoreErrors=False):
        """Remove packages.

        Keyword arguments:
        packages -- packages tuple to remove.
        ignoreErrors -- Do not raise exception packaging exception.

        Returns:
        True -- success.

        """
        raise NotImplementedError(_('Packager remove not implemented'))

    def queryGroups(self):
        """Query groups.

        Returns:
            [
                {
                    'operation': install|update,
                    'name': name,
                    'uservisible': boolean,
                },
            ]

        """
        return []

    def queryPackages(self, patterns=None):
        """Query packages.

        Keyword arguments:
        patterns -- patterns to query.

        Returns:
            [
                {
                    'operation': available|installed|updates...,
                    'display_name':,
                    'name':,
                    'version':,
                    'release':,
                    'epoch':,
                    'arch':,
                },
            ]

        """
        return []

    def queryLocalCachePackages(self, patterns=None):
        """Query packages of local cache.

        Keyword arguments:
        patterns -- patterns to query.

        Returns:
        Same as queryPackages()

        """
        return []


# vim: expandtab tabstop=4 shiftwidth=4
