#
# otopi -- plugable installer
#


"""Core plugin."""


from otopi import util


from . import config
from . import log
from . import misc
from . import transaction


@util.export
def createPlugins(context):
    config.Plugin(context=context)
    log.Plugin(context=context)
    misc.Plugin(context=context)
    transaction.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
