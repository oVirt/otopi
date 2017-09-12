#
# otopi -- plugable installer
#


""" Test Command
"""


from otopi import util


from . import test_command


@util.export
def createPlugins(context):
    test_command.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
