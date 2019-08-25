#
# otopi -- plugable installer
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

    if isinstance(o, builtins.unicode):
        try:
            return o.encode('utf-8')
        except Exception:
            pass

    if hasattr(o, '__unicode__'):
        try:
            return toStr(o.__unicode__())
        except Exception:
            pass

    if hasattr(o, '__str__'):
        try:
            return o.__str__()
        except Exception:
            pass

    if hasattr(o, '__repr__'):
        try:
            return toStr(o.__repr__())
        except Exception:
            pass

    return o.__class__.__name__


@util.export
def toUStr(o):
    if isinstance(o, str):
        return o

    if isinstance(o, builtins.unicode):
        return o

    if hasattr(o, '__unicode__'):
        try:
            return toUStr(o.__unicode__())
        except Exception:
            pass

    if hasattr(o, '__str__'):
        try:
            return o.__str__()
        except Exception:
            pass

    if hasattr(o, '__repr__'):
        try:
            return toUStr(o.__repr__())
        except Exception:
            pass

    return o.__class__.__name__


# vim: expandtab tabstop=4 shiftwidth=4
