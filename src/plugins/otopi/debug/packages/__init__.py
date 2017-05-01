#
# otopi -- plugable installer
#


""" Packages
"""


from otopi import util


from . import packages


@util.export
def createPlugins(context):
    packages.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
