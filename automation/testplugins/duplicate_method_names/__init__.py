#
# otopi -- plugable installer
#


"""Duplicate method names."""


from otopi import util


from . import duplicate_method_names


@util.export
def createPlugins(context):
    duplicate_method_names.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
