#
# otopi -- plugable installer
#


""" Test Command
"""


from otopi import util


from . import test_note


@util.export
def createPlugins(context):
    test_note.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
