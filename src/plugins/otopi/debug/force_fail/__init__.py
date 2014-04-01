#
# otopi -- plugable installer
#


""" Force a failure
"""


from otopi import util


from . import force_fail


@util.export
def createPlugins(context):
    force_fail.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
