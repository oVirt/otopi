#
# otopi -- plugable installer
#


"""Bad plugin 1."""


from otopi import util


from . import bad_plugin1


@util.export
def createPlugins(context):
    bad_plugin1.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
