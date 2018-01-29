#
# otopi -- plugable installer
#


"""Change Env Type."""


from otopi import util


from . import change_env_type


@util.export
def createPlugins(context):
    change_env_type.Plugin(context=context)


# vim: expandtab tabstop=4 shiftwidth=4
