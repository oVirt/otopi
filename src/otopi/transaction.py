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


"""Transaction handling."""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from . import base
from . import util


@util.export
class TransactionElement(base.Base):
    """Base for transaction element."""

    def __init__(self):
        """Constructor."""
        super(TransactionElement, self).__init__()

    def __del__(self):
        """Destructor."""
        self.abort()

    def __str__(self):
        """String representation."""
        return self.__name__

    def prepare(self):
        """Prepare phase.

        At this phase, perform any action that can fail.
        Best not to touch anything 'real' at this stage.

        """
        pass

    def abort(self):
        """Abort transaction.

        Cleanup/revert any artifact.

        """
        pass

    def commit(self):
        """Commit transaction element."""
        pass


@util.export
class Transaction(base.Base):

    def _prepare(self, element):
        if not self._failed:
            try:
                self._prepared.append(element)
                self.logger.debug("preparing '%s'", element)
                element.prepare()
            except Exception:
                self.logger.debug(
                    'exception during prepare phase',
                    exc_info=True
                )
                self._failed = True
                raise

    def __init__(self, elements=[]):
        """Constructor.

        Keyword arguments:
        elements -- transaction elements.

        """
        super(Transaction, self).__init__()
        self._failed = False
        self._postPrepare = False
        self._elements = []
        self._prepared = []
        for element in elements:
            self.append(element)

    def __str__(self):
        return 'transaction'

    def append(self, element):
        """Append transaction element.

        Keyword arguments:
        elements -- transaction elements.

        """
        if not isinstance(element, TransactionElement):
            raise TypeError(_('Invalid transaction element type'))

        self._elements.append(element)

        if self._postPrepare:
            self._prepare(element=element)

    def prepare(self):
        """Prepare transaction elements."""
        self._postPrepare = True
        for element in self._elements:
            self._prepare(element=element)

    def abort(self):
        """Abort transaction."""
        self._failed = True
        for element in self._prepared:
            try:
                self.logger.debug("aborting '%s'", element)
                element.abort()
            except:
                self.logger.debug(
                    "Unexpected exception from abort() of '%s'",
                    element,
                    exc_info=True
                )
        self._prepared = []

    def commit(self):
        """Commit transaction."""
        if not self._postPrepare:
            raise RuntimeError(
                _('Cannot commit transaction as transaction not prepared')
            )

        if self._failed:
            self.abort()
            raise RuntimeError(
                _('Cannot commit transaction as one of the elements failed')
            )

        for element in self._prepared:
            self.logger.debug("committing '%s'", element)
            element.commit()

    def __enter__(self):
        self.prepare()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.abort()


# vim: expandtab tabstop=4 shiftwidth=4
