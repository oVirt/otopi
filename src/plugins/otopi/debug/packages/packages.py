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

    def _add_exit_code(self, code, priority=plugin.Stages.PRIORITY_DEFAULT):
        self.environment[
            constants.BaseEnv.EXIT_CODE
        ].append(
            {
                'code': code,
                'priority': priority,
            }
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            constants.DebugEnv.PACKAGES_ACTION
        ],
    )
    def _debug_packages_validation(self):
        action = self.environment[constants.DebugEnv.PACKAGES_ACTION]
        if action in (
            'checkForSafeUpdate',
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
                if res['upgradeAvailable']:
                    if not res['missingRollback']:
                        self._add_exit_code(
                            constants.Const.
                            EXIT_CODE_DEBUG_PACKAGER_ROLLBACK_EXISTS
                        )
                    else:
                        self._add_exit_code(
                            constants.Const.
                            EXIT_CODE_DEBUG_PACKAGER_ROLLBACK_MISSING
                        )
                # else: Do nothing, default to exit code '0'

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
        elif action in (
            'queryPackages',
        ):
            # Same as above, but I want to pass another optional param
            for p in self.environment[constants.DebugEnv.PACKAGES].split(','):
                self.dialog.note(f'\nCalling queryPackages({p}, listAll=True)')
                res = self.packager.queryPackages((p,), listAll=True)
                self.dialog.note('Result is: %s' % pprint.pformat(res))
        elif action in (
            'checkForSafeUpdate',
        ):
            # Do nothing here, handled in validation above, outside of main
            # transaction.
            pass
        else:
            raise RuntimeError(
                'Unknown action passed to debug plugin packages'
            )


# vim: expandtab tabstop=4 shiftwidth=4
