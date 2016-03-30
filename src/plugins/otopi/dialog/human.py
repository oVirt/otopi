#
# otopi -- plugable installer
#


"""Human dialog provider."""


import gettext
import logging


from otopi import common
from otopi import constants
from otopi import dialog
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase, dialog.DialogBaseImpl):
    """Human dialog protocol provider.

    Environment:
        DialogEnv.DIALECT -- if human activate.
        DialogEnv.BOUNDARY -- set bundary to use.

    """
    BOUNDARY = '--=451b80dc-996f-432e-9e4f-2b29ef6d1141=--'

    class _MyFormatter(logging.Formatter):
        """Color formatter."""

        RED = "\033[0;31m"
        GREEN = "\033[92m"
        BLUE = "\033[94m"
        YELLOW = "\033[93m"
        NO_COLOR = "\033[0m"

        def __init__(self, parent):
            logging.Formatter.__init__(self, fmt='%(levelname)s %(message)s')
            self._parent = parent

        def format(self, record):
            prefix = ''
            suffix = ''
            if self._parent._output_isatty():
                if record.levelno == logging.INFO:
                    prefix = self.GREEN
                elif record.levelno == logging.WARNING:
                    prefix = self.YELLOW
                elif record.levelno == logging.ERROR:
                    prefix = self.RED
                if prefix:
                    suffix = self.NO_COLOR

            record.levelname = _('{prefix}[{level:^7}]{suffix}').format(
                prefix=prefix,
                suffix=suffix,
                level=record.levelname
            )

            return logging.Formatter.format(self, record).replace('\n', ' ')

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        dialog.DialogBaseImpl.__init__(self)    # python super is no good
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        priority=plugin.Stages.PRIORITY_MEDIUM,
        condition=(
            lambda self: self.environment[
                constants.DialogEnv.DIALECT
            ] == constants.Const.DIALOG_DIALECT_HUMAN
        ),
    )
    def _init(self):
        self.environment[constants.DialogEnv.BOUNDARY] = self.BOUNDARY
        self._open(logFormatter=self._MyFormatter(parent=self))
        self._enabled = True
        self.context.registerDialog(self)
        self.environment.setdefault(
            constants.DialogEnv.AUTO_ACCEPT_DEFAULT,
            False
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_TERMINATE,
        priority=plugin.Stages.PRIORITY_LAST + 10,
        condition=lambda self: self._enabled,
    )
    def _terminate(self):
        self.dialog.terminate()
        self._close()

    #
    # DialogBase
    #

    def note(self, text=None, prompt=False):

        def printline(line, newline=True):
            PREFIX = '         '
            self._write(
                text='%s%s%s' % (
                    PREFIX,
                    ' ' + line if line else '',
                    '\n' if newline else '',
                ),
                flush=False,
            )

        if isinstance(text, list) or isinstance(text, tuple):
            for i in text:
                self.note(text=i)
            return

        if text is None:
            text = '\n'
        text = common.toStr(text)

        lines = text.splitlines()
        if len(lines) > 0:
            for line in lines[:-1]:
                printline(line)
            printline(lines[-1], newline=not prompt)
            self._flush()

    def queryString(
        self,
        name,
        note=None,
        validValues=None,
        caseSensitive=True,
        hidden=False,
        prompt=False,
        default=None,
    ):
        self.logger.debug('query %s', name)
        if default is not None:
            default = common.toStr(default)
        if validValues is not None:
            validValues = [common.toStr(v) for v in validValues]
        note = self._queryStringNote(
            name=name,
            note=note,
            validValues=validValues,
            default=default,
        )

        if not caseSensitive and validValues is not None:
            validValues = [v.lower() for v in validValues]

        accepted = False

        if (
            self.environment[constants.DialogEnv.AUTO_ACCEPT_DEFAULT] and
            default is not None
        ):
            tempval = default if caseSensitive else default.lower()
            if (
                validValues is None or
                tempval in validValues
            ):
                self.dialog.note(text=note, prompt=False)
                value = tempval
                accepted = True

        while not accepted:
            self.dialog.note(text=note, prompt=prompt)
            value = self._readline(hidden=hidden)
            if not value and default is not None:
                value = default
            if not caseSensitive:
                value = value.lower()
            if validValues is not None and value not in validValues:
                self.logger.error(_('Invalid value'))
            elif not value and value != default:
                self.logger.error(_('Please specify value'))
            else:
                accepted = True
        return value

    def queryMultiString(self, name, note=None):
        self.logger.debug('query %s', name)
        if note is None:
            note = _("\nPlease specify multiple strings for '{name}':").format(
                name=name
            )
        self.dialog.note(text=note)
        self.dialog.note(
            text=_("type '{boundary}' in own line to mark end.").format(
                boundary=self.BOUNDARY,
            )
        )
        value = []
        while True:
            v = self._readline()
            if v == self.BOUNDARY:
                break
            value.append(v)
        return value

    def queryValue(self, name, note=None):
        self.logger.debug('query %s', name)
        if note is None:
            note = _("\nPlease specify value for '{name}':").format(
                name=name
            )
        self.dialog.note(text=note)
        self.dialog.note(text=_("Format is type:value."))
        value = common.parseTypedValue(self._readline())
        return value

    def displayValue(self, name, value, note=None):
        self.logger.debug('display %s', name)
        if note is not None:
            self.note(text=note)

        self._write(
            text='D:VALUE %s=%s:%s\n' % (
                name,
                common.typeName(value),
                value,
            )
        )

    def displayMultiString(self, name, value, note=None):
        self.logger.debug('display %s', name)
        if note is not None:
            self.note(text=note)

        self._write(
            text='D:MULTI-STRING %s %s\n%s\n%s\n' % (
                name,
                self.BOUNDARY,
                '\n'.join(value),
                self.BOUNDARY,
            )
        )

    def confirm(
        self,
        name,
        description,
        note=None,
        prompt=False,
    ):
        self.logger.debug('confirm %s', name)
        if note is None:
            note = _(
                "\nPlease confirm {description} [yes/no]: "
            ).format(
                description=description,
            )
        self.dialog.note(
            text=note,
            prompt=prompt,
        )
        value = self._readline()
        ret = value in ('yes', 'y', 'Y')
        return ret


# vim: expandtab tabstop=4 shiftwidth=4
