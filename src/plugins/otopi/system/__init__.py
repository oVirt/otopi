#
# otopi -- plugable installer
#


"""System plugin."""


from otopi import util


from . import clock
from . import command
from . import info
from . import reboot


@util.export
def createPlugins(context):
    clock.Plugin(context=context)
    command.Plugin(context=context)
    info.Plugin(context=context)
    reboot.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
