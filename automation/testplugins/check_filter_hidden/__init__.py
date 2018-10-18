#
# otopi -- plugable installer
#


"""check_filter_hidden."""


from otopi import util


from . import check_filter_hidden


@util.export
def createPlugins(context):
    check_filter_hidden.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
