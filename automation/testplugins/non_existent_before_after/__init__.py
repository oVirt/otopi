#
# otopi -- plugable installer
#


"""Non-existent Before/After."""


from otopi import util


from . import non_existent_before_after


@util.export
def createPlugins(context):
    non_existent_before_after.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
