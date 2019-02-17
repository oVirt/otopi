#
# otopi -- plugable installer
#


"""Event Cyclic Dependency."""


from otopi import util


from . import event_cyclic_dep


@util.export
def createPlugins(context):
    event_cyclic_dep.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
