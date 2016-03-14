#
# otopi -- plugable installer
#


"""services plugin."""


from otopi import util


from . import openrc
from . import rhel
from . import systemd


@util.export
def createPlugins(context):
    openrc.Plugin(context=context)
    rhel.Plugin(context=context)
    systemd.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
