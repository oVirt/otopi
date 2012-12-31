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


"""Base class for project."""


import logging


from . import util


@util.export
class Base(object):
    """Base class for all objects."""

    @property
    def logger(self):
        """Logger."""
        return self._logger

    def __init__(self):
        """Contructor."""
        self._logger = logging.getLogger(self.__module__)


# vim: expandtab tabstop=4 shiftwidth=4
