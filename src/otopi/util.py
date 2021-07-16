#
# otopi -- plugable installer
#


"""Utilities and tools."""


import gettext
import sys
import os
_use_importlib = False
try:
    from importlib import util as importlibutil
    _use_importlib = True
except ImportError:
    import imp

__all__ = ['export']


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


def export(o):
    """Decoration to export module symbol.

    Usage:
        import util
        @util.export
        def x():
            pass

    """
    sys.modules[o.__module__].__dict__.setdefault(
        '__all__', []
    ).append(o.__name__)
    return o


@export
def codegen(o):
    """A no-op decoration left for backwards-compatibility.

    Original doc string follows:

    Decoration to code generate class symbols.

    Usage:
        import util
        @util.codegen
        class x():
            CONSTANT = 'value'

    """
    return o


@export
def methodsByAttribute(clz, attribute):
    """Query metadata information for specific method attribute.

    Keyword arguments:
    clz -- class to check.
    attribute -- attribute to find within methods.

    Returns:
        [attribute]


    Usable for class members decoration query.
    """
    ret = []
    for m in clz.__dict__.values():
        if hasattr(m, attribute):
            ret.append(getattr(m, attribute))
    return ret


@export
def raiseExceptionInformation(info):
    """Python-2/Python-3 raise exception based on exception information."""
    if hasattr(info[1], 'with_traceback'):
        raise info[1].with_traceback(info[2])
    else:
        exec('raise info[1], None, info[2]')


@export
def loadModule(path, name):
    """Dynamic load module.

    Keyword arguments:
    path -- path to load from.
    name -- name of module.

    Returns:
    Loaded module.

    """
    if _use_importlib:
        module_name = name.split('.')[-1]
        spec = importlibutil.spec_from_file_location(
            name,
            os.path.join(path, module_name, '__init__.py')
        )
        module = importlibutil.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    else:
        mod_fobj, mod_absp, mod_desc = imp.find_module(
            name.split('.')[-1],
            [path]
        )
        try:
            return imp.load_module(
                name,
                mod_fobj,
                mod_absp,
                mod_desc
            )
        finally:
            if mod_fobj is not None:
                mod_fobj.close()


# vim: expandtab tabstop=4 shiftwidth=4
