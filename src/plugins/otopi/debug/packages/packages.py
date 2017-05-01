#
# otopi -- plugable installer
#


""" Packages debug plugin."""


import pprint

from otopi import constants
from otopi import util
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """Packages.

    Allow directly calling otopi's packager, useful mainly for debugging.

    Environment:
        DebugEnv.PACKAGES_ACTION -- Action to call
        DebugEnv.PACKAGES -- Comma-separated list of packages/patterns
    """

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self.environment.setdefault(
            constants.DebugEnv.PACKAGES,
            None
        )
        self.environment.setdefault(
            constants.DebugEnv.PACKAGES_ACTION,
            None
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self.environment[
            constants.DebugEnv.PACKAGES_ACTION
        ],
    )
    def _debug_packages(self):
        action = self.environment[constants.DebugEnv.PACKAGES_ACTION]
        if action == 'queryGroups':
            # No params
            self.dialog.note('\nCalling queryGroups:')
            res = self.packager.queryGroups()
            self.dialog.note('Result is: %s' % pprint.pformat(res))
        elif action in (
            'installGroup',
            'updateGroup',
            'removeGroup',
        ):
            # A single param
            for p in self.environment[constants.DebugEnv.PACKAGES].split(','):
                self.dialog.note(
                    '\nCalling {action} on {p}:'.format(
                        action=action,
                        p=p,
                    )
                )
                res = getattr(self.packager, action)(p)
                self.dialog.note('Result is: %s' % pprint.pformat(res))
        elif action in (
            'install',
            'update',
            'installUpdate',
            'remove',
            'queryPackages',
        ):
            # A single param that is a tuple (iterable).
            # In principle we can call action once, for now call per
            # item. In the future might extend to allow optionally call
            # for all.
            for p in self.environment[constants.DebugEnv.PACKAGES].split(','):
                self.dialog.note(
                    '\nCalling {action} on {p}:'.format(
                        action=action,
                        p=p,
                    )
                )
                res = getattr(self.packager, action)((p,))
                self.dialog.note('Result is: %s' % pprint.pformat(res))
        else:
            raise RuntimeError(
                'Unknown action passed to debug plugin packages'
            )


# vim: expandtab tabstop=4 shiftwidth=4
