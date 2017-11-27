#
# otopi -- plugable installer
#


""" Debug Failure
"""


from otopi import util


from . import debug_failure


@util.export
def createPlugins(context):
    debug_failure.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
