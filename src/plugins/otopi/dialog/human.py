#
# otopi -- plugable installer
# Copyright (C) 2012 Red Hat, Inc.
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


"""Human dialog provider."""


import logging
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from otopi import constants
from otopi import util
from otopi import common
from otopi import plugin
from otopi import dialog


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

        if isinstance(text, list):
            for i in text:
                self.note(text=i)
            return

        if text is None:
            text = '\n'
        text = str(text)

        lines = text.splitlines()
        for line in lines[:-1]:
            printline(line)
        printline(lines[-1], newline=not prompt)
        self._flush()

    def queryString(
        self,
        name,
        note=None,
        validValues=None,
        mandatory=False,
        hidden=False,
        prompt=False,
    ):
        accepted = False
        while not accepted:
            if note is None:
                note = _("\nPlease specify '{name}' {values}: ").format(
                    name=name,
                    values=validValues,
                )
            self.dialog.note(text=note, prompt=prompt)
            value = self._readline(hidden=hidden)
            if validValues is not None and value not in validValues:
                self.logger.error(_('Invalid value'))
            elif mandatory and not value:
                self.logger.error(_('Please specify value'))
            else:
                accepted = True
        return value

    def queryMultiString(self, name, note=None):
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
        if note is None:
            note = _("\nPlease specify value for '{name}':").format(
                name=name
            )
        self.dialog.note(text=note)
        self.dialog.note(text=_("Format is type:value."))
        value = common.parseTypedValue(self._readline())
        return value

    def displayValue(self, name, value, note=None):
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
