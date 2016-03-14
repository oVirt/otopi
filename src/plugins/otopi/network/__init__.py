#
# otopi -- plugable installer
#


"""Network plugin."""


from otopi import util


from . import firewalld
from . import hostname
from . import iptables
from . import ssh


@util.export
def createPlugins(context):
    firewalld.Plugin(context=context)
    hostname.Plugin(context=context)
    iptables.Plugin(context=context)
    ssh.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
