#
# otopi -- plugable installer
#


"""Packager provider."""


from otopi import util


from . import dnfpackager
from . import yumpackager


@util.export
def createPlugins(context):
    dnfpackager.Plugin(context=context)
    yumpackager.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
