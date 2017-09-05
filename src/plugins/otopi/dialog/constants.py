#
# otopi -- plugable installer
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

    QUERY_EXTRA_PREFIX = '**%'
    # Prefix for extra info for queries added by otopi 1.5.
    # Clients should ignore lines with this prefix if they can't parse them.
    QUERY_START = 'QStart:'
    QUERY_DEFAULT_VALUE = 'QDefault:'
    QUERY_VALID_VALUES = 'QValidValues:'
    QUERY_HIDDEN = 'QHidden:'
    QUERY_END = 'QEnd:'

    # Reusing QUERY_EXTRA_PREFIX for these too, even though they are unrelated
    # to queries. In practice QUERY_EXTRA_PREFIX is going to be used for all
    # new additions to the machine dialog protocol, at least until some future
    # version that can break compatibility with MachineDialogParser.java.

    # Events sequence stuff, used in the sequence dump we do in the beginning
    EVENTS_LIST_START = 'EventsListStart'
    EVENTS_LIST_ENTRY = 'EventsListEntry'
    EVENTS_LIST_END = 'EventsListEnd'

    # Actual events that run
    EVENT_START = 'EventStart'
    EVENT_CONDITION = 'EventCondition'  # bool, will use one of QUERY_HIDDEN*
    EVENT_END = 'EventEnd'

    QUERY_HIDDEN_TRUE = 'TRUE'
    QUERY_HIDDEN_FALSE = 'FALSE'

    DISPLAY_PREFIX = 'D:'
    DISPLAY_MULTI_STRING = DISPLAY_PREFIX + 'MULTI-STRING'
    DISPLAY_VALUE = DISPLAY_PREFIX + 'VALUE'

    CONFIRM = 'CONFIRM'
    CONFIRM_RESPONSE_VALUE = 'CONFIRM'
    CONFIRM_RESPONSE_ABORT = 'ABORT'

    TERMINATE = 'TERMINATE'


# vim: expandtab tabstop=4 shiftwidth=4
