#
# otopi -- plugable installer
#


""" Debug Failures plugin."""


import gettext
import os
import re
import glob


from otopi import util
from otopi import plugin


def _(m):
    return gettext.dgettext(message=m, domain='otopi')


PROC_NET_TCP = "/proc/net/tcp"
SOCKET_STATES = {
    '01': 'ESTABLISHED',
    '02': 'SYN_SENT',
    '03': 'SYN_RECV',
    '04': 'FIN_WAIT1',
    '05': 'FIN_WAIT2',
    '06': 'TIME_WAIT',
    '07': 'CLOSE',
    '08': 'CLOSE_WAIT',
    '09': 'LAST_ACK',
    '0A': 'LISTEN',
    '0B': 'CLOSING',
}


@util.export
class Plugin(plugin.PluginBase):
    """Debug Failure.
    """

    def _load_proc(self):
        with open(PROC_NET_TCP, 'r') as f:
            content = f.read().splitlines()
            content.pop(0)  # Remove header
        return content

    def _hex2dec(self, s):
        return str(int(s, 16))

    def _hex_ip_to_decimal(self, s):
        return '.'.join([self._hex2dec(s[i:i+2]) for i in (6, 4, 2, 0)])

    def _hex_ip_port_to_str(self, s):
        ip, port = s.split(':')
        return ':'.join((self._hex_ip_to_decimal(ip), self._hex2dec(port)))

    def _get_inode_pids(self):
        res = {}
        target_re = re.compile(r'socket:\[(\d*)\]')
        try:
            for pidpath in glob.glob('/proc/[0-9]*'):
                pid = os.path.basename(pidpath)
                try:
                    for fdpath in glob.glob('%s/fd/[0-9]*' % pidpath):
                        target = os.readlink(fdpath)
                        match = target_re.match(target)
                        if match:
                            res[match.group(1)] = pid
                except Exception:
                    pass  # Skip if can't read, but continue with others
        except Exception:
            pass
        return res

    def _get_connections(self):
        inodes_pids = self._get_inode_pids()
        res = ['id uid local foreign state pid exe']
        for line in self._load_proc():
            line = line.split()
            id = line[0]
            local = self._hex_ip_port_to_str(line[1])
            foreign = self._hex_ip_port_to_str(line[2])
            state = SOCKET_STATES[line[3]]
            uid = line[7]
            pid = inodes_pids.get(line[9], 'UnknownPID')
            try:
                exe = os.readlink('/proc/%s/exe' % pid)
            except Exception:
                exe = 'UnknownEXE'
            res.append(' '.join((id, uid, local, foreign, state, pid, exe)))
        return res

    def _notification(self, event):
        if event == self.context.NOTIFY_ERROR:
            self.logger.debug(
                'tcp connections:\n%s',
                '\n'.join(self._get_connections())
            )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
    )
    def _debug_failure_init(self):
        self.context.registerNotification(self._notification)


# vim: expandtab tabstop=4 shiftwidth=4
