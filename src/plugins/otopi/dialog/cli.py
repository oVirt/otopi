#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""Command line interface.

Refer to README.dialog.

"""


from optparse import OptionParser, OptParseError   # python-2.6
import traceback
import shlex
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import common
from otopi import context
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """Command-line interface provider.

    Environment:
        DialogEnv.CUSTOMIZATION -- control customization.

    Queries:
        Queries.CUSTOMIZATION_COMMAND -- customization command.
        Queries.TERMINATION_COMMAND -- termination command.

    """
    def _command(command, description, stages=()):
        def decorator(f):
            f.decoration_command = {
                'method': f,
                'command': command,
                'description': description,
                'stages': stages
            }
            return f
        return decorator

    class _MyOptionParser(OptionParser):
        def __init__(self, prog, logger=None, *args, **kwargs):
            OptionParser.__init__(self, *args, add_help_option=False, **kwargs)
            self.prog = prog
            self.add_option(
                '-h', '--help',
                action="store_true", dest='help',
                help=_('This text')
            )
            self.logger = logger

        def exit(self, status=0, msg=None):
            for l in msg.splitlines():
                self.logger.error(l)
            raise OptParseError(msg)

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._commands = util.methodsByAttribute(
            self.__class__,
            'decoration_command'
        )

    def getCommand(self, stage):
        ret = {}
        for cmd in self._commands:
            if not cmd['stages'] or stage in cmd['stages']:
                ret[cmd['command']] = cmd
        return ret

    def _runCommandPrompt(self, stage, name, note):
        cont = True
        while cont:
            cmd = shlex.split(
                self.dialog.queryString(
                    name=name,
                    note=note,
                    prompt=True,
                )
            )

            if cmd:
                commands = self.getCommand(stage=stage)
                if cmd[0] in commands:
                    metadata = commands[cmd[0]]
                    try:
                        cont = metadata['method'].__get__(self)(cmd)
                    except OptParseError:
                        # ignore as we already logged
                        pass
                else:
                    self.logger.error(
                        _("Invalid command '{command}'").format(
                            command=cmd[0],
                        )
                    )

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            constants.DialogEnv.CLI_VERSION,
            1
        )
        self.environment.setdefault(
            constants.DialogEnv.CUSTOMIZATION,
            False
        )

    @plugin.event(
        name=constants.Stages.DIALOG_CLI_CUSTOMIZATION,
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        condition=(
            lambda self: self.environment[constants.DialogEnv.CUSTOMIZATION]
        ),
    )
    def _customize(self):
        self._runCommandPrompt(
            stage=plugin.Stages.STAGE_CUSTOMIZATION,
            name=constants.Queries.CUSTOMIZATION_COMMAND,
            note=_(
                "\nCustomization phase, use 'install' to proceed\nCOMMAND> "
            )
        )

    @plugin.event(
        name=constants.Stages.DIALOG_CLI_TERMINATION,
        stage=plugin.Stages.STAGE_PRE_TERMINATE,
        condition=(
            lambda self: self.environment[constants.DialogEnv.CUSTOMIZATION]
        ),
    )
    def _pre_terminate(self):
        self._runCommandPrompt(
            stage=plugin.Stages.STAGE_PRE_TERMINATE,
            name=constants.Queries.TERMINATION_COMMAND,
            note=_("\nProcessing ended, use 'quit' to quit\nCOMMAND> ")
        )

    def _header(self, title):
        for i in range(2):
            self.dialog.note()
        self.dialog.note(text=title)
        self.dialog.note()

    def _footer(self):
        for i in range(1):
            self.dialog.note()

    @_command(
        command='help',
        description=_('Display available commands'),
    )
    def _cmd_help(self, cmd):
        self._header(title=_('COMMAND HELP'))
        commands = self.getCommand(stage=self.context.currentStage)
        for cmd in sorted(commands):
            self.dialog.note(
                text=_("{command} - {description}").format(
                    command=cmd,
                    description=commands[cmd]['description']
                )
            )
        self.dialog.note()
        self.dialog.note(
            _('Use command --help to get command specific help.')
        )
        self._footer()
        return True

    @_command(
        command='noop',
        description=_('No operation'),
    )
    def _cmd_noop(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            pass
        return True

    @_command(
        command='abort',
        description=_('Abort process'),
        stages=(plugin.Stages.STAGE_CUSTOMIZATION,),
    )
    def _cmd_abort(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            raise context.Abort(_('Aborted by user'))
        return True

    @_command(
        command='install',
        description=_('Install software'),
        stages=(plugin.Stages.STAGE_CUSTOMIZATION,),
    )
    def _cmd_install(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            return False
        return True

    @_command(
        command='quit',
        description=_('Quit'),
        stages=(plugin.Stages.STAGE_PRE_TERMINATE,),
    )
    def _cmd_quit(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            return False
        return True

    @_command(
        command='env-show',
        description=_('Display environment'),
    )
    def _cmd_env_show(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            self._header(title=_('ENVIRONMENT'))
            for k in sorted(self.environment.keys()):
                v = self.environment[k]
                self.dialog.note(
                    text=_("'{key}'={type}:'{value}'").format(
                        key=k,
                        type=common.typeName(v),
                        value=v
                    )
                )
            self._footer()
        return True

    @_command(
        command='env-get',
        description=_('Get environment variable'),
    )
    def _cmd_env_get(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        parser.add_option(
            '-k', '--key',
            action="store", dest='key',
            help=_('Environment key')
        )
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args or options.key is None:
            self.logger.error(_("Syntax error"))
        else:
            if options.key in self.environment:
                value = self.environment[options.key]
                if isinstance(value, list) or isinstance(value, tuple):
                    self.dialog.displayMultiString(
                        name=options.key,
                        value=self.environment[options.key]
                    )
                else:
                    self.dialog.displayValue(
                        name=options.key,
                        value=self.environment[options.key]
                    )
            else:
                self.dialog.displayValue(
                    name=options.key,
                    value=None
                )
        return True

    @_command(
        command='env-set',
        description=_('Set environment variable'),
    )
    def _cmd_env_set(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        parser.add_option(
            '-k', '--key',
            action="store", dest='key',
            help=_('Environment key')
        )
        parser.add_option(
            '-t', '--type',
            action="store", dest='type', default='str',
            help=_("Variable type ('bool', 'int', 'str'), default 'str'")
        )
        parser.add_option(
            '-v', '--value',
            action="store", dest='value',
            help=_('Variable value')
        )
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif (
            args or
            options.key is None or
            options.value is None
        ):
            self.logger.error(_("Syntax error"))
        else:
            if options.type == 'bool':
                self.environment[options.key] = options.value not in (
                    0, 'f', 'F', 'false', 'False'
                )
            elif options.type == 'str':
                self.environment[options.key] = options.value
            elif options.type == 'int':
                try:
                    self.environment[options.key] = int(options.value)
                except ValueError:
                    self.logger.error(_("Syntax error"))
            else:
                self.logger.error(_("Invalid type"))
        return True

    @_command(
        command='env-query',
        description=_('Query environment variable'),
    )
    def _cmd_env_query(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        parser.add_option(
            '-k', '--key',
            action="store", dest='key',
            help=_('Environment key')
        )
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif (
            args or
            options.key is None
        ):
            self.logger.error(_("Syntax error"))
        else:
            self.environment[options.key] = self.dialog.queryValue(
                name=options.key
            )
        return True

    @_command(
        command='env-query-multi',
        description=_('Get multi string environment variable'),
    )
    def _cmd_env_query_multi(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        parser.add_option(
            '-k', '--key',
            action="store", dest='key',
            help=_('Environment key')
        )
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif (
            args or
            options.key is None
        ):
            self.logger.error(_("Syntax error"))
        else:
            self.environment[options.key] = self.dialog.queryMultiString(
                name=options.key
            )
        return True

    @_command(
        command='log',
        description=_('Retrieve log file'),
    )
    def _cmd_log(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            with open(
                self.resolveFile(
                    self.environment[constants.CoreEnv.LOG_FILE_NAME]
                ),
                'r'
            ) as f:
                log = [
                    l.replace(
                        self.environment[constants.DialogEnv.BOUNDARY],
                        '**BOUNDARY**'
                    ).rstrip('\n')
                    for l in f.readlines()
                ]
            self.dialog.displayMultiString(
                name='LOG',
                value=log,
            )
        return True

    @_command(
        command='exception-show',
        description=_('show exception information'),
    )
    def _cmd_exception_show(self, cmd):
        parser = self._MyOptionParser(cmd[0], logger=self.logger)
        (options, args) = parser.parse_args(args=cmd[1:])
        if options.help:
            self.dialog.note(text=parser.format_help())
        elif args:
            self.logger.error(_("Syntax error"))
        else:
            exceptionInfos = self.environment[constants.BaseEnv.EXCEPTION_INFO]
            if exceptionInfos is not None:
                for exceptionInfo in exceptionInfos:
                    self.dialog.note(
                        text=traceback.format_exception(*exceptionInfo)
                    )
        return True


# vim: expandtab tabstop=4 shiftwidth=4
