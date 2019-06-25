#
# otopi -- plugable installer
#


"""Packager interface.

Packager is the component responsible for interacting with distribution
packager.

"""


import gettext
import os
import platform


from . import constants
from . import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


def ok_to_use_dnf():
    if os.environ.get(constants.SystemEnvironment.DNF_ENABLE):
        return True

    plat_dist = platform.linux_distribution(full_distribution_name=0)
    distribution = plat_dist[0]
    version = plat_dist[1]
    return (
        distribution in (
            'fedora',
        ) or (
            distribution in (
                'redhat',
                'centos',
                'ibm_powerkvm',
            ) and
            version >= '8.0'
        )
    )


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

    def processTransaction(self):
        """Process transaction."""
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
        # legacy note, this should not have been implemented
        # however, offline packages expect it to be implemented.
        # logic is incorrect, and packagers should reimplement it
        # properly.
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

    def queryPackages(self, patterns=None, listAll=False):
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


# vim: expandtab tabstop=4 shiftwidth=4
