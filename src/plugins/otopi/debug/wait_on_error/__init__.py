#
# otopi -- plugable installer
#


""" Wait on error
"""


from otopi import util


from . import wait_on_error


@util.export
def createPlugins(context):
    wait_on_error.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
