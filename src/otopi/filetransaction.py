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


"""File transaction element."""


import os
import tempfile
import datetime
import shutil
import pwd
import grp
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='otopi')


from . import util
from . import transaction


@util.export
class FileTransaction(transaction.TransactionElement):
    """File transaction element."""

    @staticmethod
    def _defaultAtomicMove(source, destination):
        atomic = False

        # perform atomic move if on same device
        # (not mount -o bind)
        # if destination does not exist, check directory.
        # if destination exists, check file.
        if not os.path.exists(destination):
            if (
                os.stat(source).st_dev == os.stat(
                    os.path.dirname(destination)
                ).st_dev
            ):
                atomic = True
        elif os.stat(destination).st_dev == os.stat(source).st_dev:
            atomic = True

        if atomic:
            os.rename(source, destination)
        else:
            # pray!
            content = ''
            with open(source, 'r') as f:
                content = f.read()
            with open(destination, 'w') as f:
                f.write(content)
            os.unlink(source)

    def _createDirRecursive(self, d):
        if d and d != '/':
            self._createDirRecursive(os.path.dirname(d))
            if not os.path.exists(d):
                os.mkdir(d)
                os.chmod(d, self._dmode)
                os.chown(
                    d,
                    self._downer,
                    self._dgroup
                )

    _atomicMove = _defaultAtomicMove

    @property
    def name(self):
        return self._name

    @property
    def tmpname(self):
        return self._tmpname

    @classmethod
    def registerAtomicMove(clz, function):
        clz._atomicMove = function

    @classmethod
    def getAtomicMove(clz, function):
        return clz._atomicMove

    def __init__(
        self,
        name,
        content,
        mode=0o644,
        dmode=0o755,
        owner=None,
        group=None,
        downer=None,
        dgroup=None,
        enforcePermissions=False,
        modifiedList=[],
    ):
        """Constructor.

        Check if content differ, if not, does nothing.
        Backup current file.
        Create the new file as temporary name at same directory.
        Copy or assign new file attributes.
        When commit move temporary file to target file.

        Keyword arguments:
        name -- name of file.
        content -- content of file (string or list of lines).
        mode -- mode of file.
        dmode -- directory mode if directory is to be created.
        owner -- owner (name)
        group -- group (name)
        downer -- directory owner (name) if directory is to be created.
        dgroup -- directory group (name) if directory is to be created.
        enforcePermissions -- if True permissions are enforced also
            if previous file was exists.
        modifiedList -- a list to add file name if was changed.

        """
        super(FileTransaction, self).__init__()
        self._name = name

        if isinstance(content, list):
            self._content = '\n'.join(content)
        else:
            self._content = str(content)
        if not self._content.endswith('\n'):
            self._content += '\n'

        self._mode = mode
        self._dmode = dmode
        self._owner = -1
        self._group = -1
        self._downer = -1
        self._dgroup = -1
        self._enforcePermissions = enforcePermissions
        self._modifiedList = modifiedList
        if owner is not None:
            self._owner, self._group = pwd.getpwnam(owner)[2:4]
        if group is not None:
            self._group = grp.getgrnam(group)[2]
        if downer is not None:
            self._downer, self._group = pwd.getpwnam(downer)[2:4]
        if dgroup is not None:
            self._dgroup = grp.getgrnam(dgroup)[2]
        self._tmpname = None
        self._prepared = False

    def __str__(self):
        return _("File transaction for '{file}'").format(
            file=self._name
        )

    def prepare(self):
        doit = True
        if os.path.exists(self._name):
            self.logger.debug("file '%s' exists" % self._name)
            with open(self._name, 'r') as f:
                if f.read() == self._content:
                    self.logger.debug(
                        "file '%s' already has content" % self._name
                    )
                    doit = False
        else:
            self.logger.debug("file '%s' missing" % self._name)

        if doit:
            mydir = os.path.dirname(self._name)
            if os.path.exists(self._name):
                # check we can open file for write
                with open(self._name, 'a'):
                    pass

                # backup file
                newname = "%s.%s" % (
                    self._name,
                    datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                )
                self.logger.debug("backup '%s'->'%s'" % (self._name, newname))
                shutil.copyfile(self._name, newname)

                if not self._enforcePermissions:
                    # get current file stats
                    currentStat = os.stat(self._name)
                    self._mode = currentStat.st_mode
                    self._owner = currentStat.st_uid
                    self._group = currentStat.st_gid
            elif not os.path.exists(mydir):
                self._createDirRecursive(mydir)

            fd = -1
            try:
                fd, self._tmpname = tempfile.mkstemp(
                    suffix=".tmp",
                    prefix="%s." % os.path.basename(self._name),
                    dir=mydir,
                )

                os.chown(
                    self._tmpname,
                    self._owner,
                    self._group
                )

                # python does not support atomic umask
                # so leave file as-is
                if self._mode is not None:
                    os.chmod(
                        self._tmpname,
                        self._mode
                    )

                os.write(fd, self._content)
                os.fsync(fd)
                self._prepared = True
            finally:
                if fd != -1:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    fd = -1

    def abort(self):
        if self._tmpname is not None:
            try:
                os.unlink(self._tmpname)
            except OSError:
                pass

    def commit(self):
        if self._prepared:
            type(self)._atomicMove(self._tmpname, self._name)
            self._modifiedList.append(self._name)
