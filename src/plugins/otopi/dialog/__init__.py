#
# otopi -- plugable installer
#


"""Dialog plugin."""


from otopi import util


from . import answer_file
from . import cli
from . import human
from . import machine
from . import misc


@util.export
def createPlugins(context):
    answer_file.Plugin(context=context)
    cli.Plugin(context=context)
    human.Plugin(context=context)
    machine.Plugin(context=context)
    misc.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
