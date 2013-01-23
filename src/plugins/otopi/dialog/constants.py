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


"""Machine dialog provider's constants

Refer to README.dialog.

"""


from otopi import util


@util.codegen
class DialogMachineConst(object):
    NOTE_PREFIX = '#'
    REQUEST_PREFIX = '***'

    LOG_PREFIX = 'L:'
    LOG_INFO = LOG_PREFIX + 'INFO'
    LOG_WARNING = LOG_PREFIX + 'WARNING'
    LOG_ERROR = LOG_PREFIX + 'ERROR'
    LOG_CRITICAL = LOG_PREFIX + 'CRITICAL'
    LOG_FATAL = LOG_PREFIX + 'FATAL'

    QUERY_PREFIX = 'Q:'
    QUERY_STRING = QUERY_PREFIX + 'STRING'
    QUERY_MULTI_STRING = QUERY_PREFIX + 'MULTI-STRING'
    QUERY_VALUE = QUERY_PREFIX + 'VALUE'
    QUERY_VALUE_RESPONSE_ABORT = 'ABORT'
    QUERY_VALUE_RESPONSE_VALUE = 'VALUE'

    DISPLAY_PREFIX = 'D:'
    DISPLAY_MULTI_STRING = DISPLAY_PREFIX + 'MULTI-STRING'
    DISPLAY_VALUE = DISPLAY_PREFIX + 'VALUE'

    CONFIRM = 'CONFIRM'
    CONFIRM_RESPONSE_VALUE = 'CONFIRM'
    CONFIRM_RESPONSE_ABORT = 'ABORT'

    TERMINATE = 'TERMINATE'


# vim: expandtab tabstop=4 shiftwidth=4
