#
# otopi -- plugable installer
#


"""otopi module."""


import sys


def _pythonModulesCompat():
    """Rename modules to match python3 names."""
    if sys.version_info[0] >= 3:
        import builtins
        setattr(builtins, 'unicode', str)
    else:
        import ConfigParser
        sys.modules['configparser'] = ConfigParser
        import __builtin__
        sys.modules['builtins'] = __builtin__

        class COMPAT_BlockingIOError(OSError):
            pass

        setattr(__builtin__, 'BlockingIOError', COMPAT_BlockingIOError)


_pythonModulesCompat()


__all__ = []


# vim: expandtab tabstop=4 shiftwidth=4
