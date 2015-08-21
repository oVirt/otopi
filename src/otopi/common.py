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


"""Common misc functions."""


import builtins
import gettext


from . import constants
from . import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
def parseTypedValue(value):
    """Parse type:value string into python object."""
    try:
        vtype, value = value.split(':', 1)
    except ValueError:
        raise ValueError(_("Missing variable type"))

    if vtype == constants.Types.NONE:
        value = None
    elif vtype == constants.Types.BOOLEAN:
        value = value not in (0, 'f', 'F', 'false', 'False')
    elif vtype == constants.Types.INTEGER:
        value = int(value)
    elif vtype == constants.Types.STRING:
        pass
    elif vtype == constants.Types.MULTI_STRING:
        value = value.splitlines()
    else:
        raise KeyError(
            _('Invalid variable type {type}').format(
                type=vtype
            )
        )
    return value


@util.export
def typeName(value):
    """Return type of value suitable for parsing"""
    if value is None:
        ret = constants.Types.NONE
    elif isinstance(value, bool):
        ret = constants.Types.BOOLEAN
    elif isinstance(value, int):
        ret = constants.Types.INTEGER
    elif isinstance(value, str) or isinstance(value, builtins.unicode):
        ret = constants.Types.STRING
    elif isinstance(value, list) or isinstance(value, tuple):
        ret = constants.Types.MULTI_STRING
    else:
        ret = constants.Types.OBJECT
    return ret


@util.export
def toStr(o):
    if isinstance(o, str):
        return o
    elif isinstance(o, builtins.unicode):
        return o.encode('utf-8')
    elif hasattr(o, '__repr__'):
        return toStr(o.__repr__())
    elif hasattr(o, '__unicode__'):
        return toStr(o.__unicode__())
    elif hasattr(o, '__str__'):
        return o.__str__()
    else:
        return o.__class__.__name__


# vim: expandtab tabstop=4 shiftwidth=4
