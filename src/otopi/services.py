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


"""Services interface.

Services is the component responsible of intraction with system services.

"""


from . import util


@util.export
class ServicesBase(object):
    """Base class for services.

    Base class for all services providers.

    """

    @property
    def supportsDependency(self):
        """True if provider supports service dependency."""
        return False

    def exists(self, name):
        """Checks if service exists"""
        return False

    def status(self, name):
        """Checks status of a service"""
        return False

    def startup(self, name, state):
        """Sets service state after reboot"""
        pass

    def state(self, name, state):
        """Sets service state"""
        pass


# vim: expandtab tabstop=4 shiftwidth=4
