#
# otopi -- plugable installer
#


"""Services interface.

Services is the component responsible of intraction with system services.

"""


from . import util


@util.export
class ServicesBase(object):
    """Base class for services.

    Base class for all services providers.

    """

    @property
    def supportsDependency(self):
        """True if provider supports service dependency."""
        return False

    def exists(self, name):
        """Checks if service exists"""
        return False

    def status(self, name):
        """Checks status of a service"""
        return False

    def startup(self, name, state):
        """Sets service state after reboot"""
        pass

    def state(self, name, state):
        """Sets service state"""
        pass


# vim: expandtab tabstop=4 shiftwidth=4
