#
# otopi -- plugable installer
#


"""Clock plugin."""


import datetime
import gettext


from otopi import constants
from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


@util.export
class Plugin(plugin.PluginBase):
    """Clock synchronize.

    Environment:
        SysEnv.CLOCK_SET -- enable clock set.
        SysEnv.CLOCK_MAX_GAP -- allowed gap per request/response.

    Queries:
        Queries.TIME -- current time.

    If ntpd is installed and sync, skip.

    Otherwise ask manager for current time.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(constants.SysEnv.CLOCK_MAX_GAP, 5)
        self.environment.setdefault(constants.SysEnv.CLOCK_SET, False)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('ntpq')
        self.command.detect('chronyc')
        self.command.detect('date')
        self.command.detect('hwclock')

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self.environment[constants.SysEnv.CLOCK_SET],
    )
    def _set_clock(self):
        needClockSync = True
        ntpq = self.command.get('ntpq', optional=True)
        if ntpq is not None:
            # ntpq returns success also if fails...
            rc, stdout, stderr = self.execute(
                (ntpq, '-c', 'rv'),
                raiseOnError=False,
            )
            if (
                rc == 0 and
                not stderr and
                stdout and
                'clock_sync' in stdout[0]
            ):
                self.logger.debug('clock is synchronized')
                needClockSync = False
        chronyc = self.command.get('chronyc', optional=True)
        if chronyc is not None:
            rc, stdout, stderr = self.execute(
                (chronyc, 'waitsync', '1'),
                raiseOnError=False,
            )
            if rc == 0:
                self.logger.debug('clock is synchronized')
                needClockSync = False
        if needClockSync:
            got = False
            skip = False
            while not got and not skip:
                mark1 = datetime.datetime.now()

                currentTime = self.dialog.queryValue(
                    name=constants.Queries.TIME,
                    note=_(
                        '\nPlease specify current time ({format}), '
                        'empty to skip:'
                    ).format(
                        format="YYYYmmddHHMMSS+0000"
                    )
                )

                mark2 = datetime.datetime.now()

                if not currentTime:
                    self.logger.debug('skipping')
                    skip = True
                else:
                    td = mark2 - mark1
                    # since python 2.7
                    total_seconds = (
                        td.microseconds + (
                            td.seconds + td.days * 24 * 3600
                        ) * 10 ** 6
                    ) / 10 ** 6

                    if (
                        total_seconds < self.environment[
                            constants.SysEnv.CLOCK_MAX_GAP
                        ]
                    ):
                        got = True
                    else:
                        self.logger.debug(
                            'query took too long (%s)',
                            total_seconds
                        )

            if not skip:
                now = datetime.datetime.utcnow().strptime(
                    currentTime,
                    "%Y%m%d%H%M%S+0000"
                )

                try:
                    (rc, stdout, stderr) = self.execute(
                        (
                            self.command.get('date'),
                            '--utc',
                            now.strftime("%m%d%H%M%Y.%S")
                        ),
                    )
                    (rc, stdout, stderr) = self.execute(
                        (
                            self.command.get('hwclock'),
                            '--systohc'
                        ),
                    )
                except:
                    self.logger.warning(
                        _('Cannot set clock'),
                        exc_info=True
                    )


# vim: expandtab tabstop=4 shiftwidth=4
