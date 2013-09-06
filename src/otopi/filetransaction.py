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
    def _defaultAtomicMove(source, destination, binary=False):
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
            with open(source, 'r' + ('b' if binary else '')) as f:
                content = f.read()
            with open(destination, 'w' + ('b' if binary else '')) as f:
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
        if self._originalDiffer:
            return self._tmpname
        else:
            return self._name

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
        binary=False,
        mode=0o644,
        dmode=0o755,
        owner=None,
        group=None,
        downer=None,
        dgroup=None,
        enforcePermissions=False,
        visibleButUnsafe=False,
        modifiedList=None,
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
        binary -- treat content as binary.
        mode -- mode of file.
        dmode -- directory mode if directory is to be created.
        owner -- owner (name)
        group -- group (name)
        downer -- directory owner (name) if directory is to be created.
        dgroup -- directory group (name) if directory is to be created.
        enforcePermissions -- if True permissions are enforced also
            if previous file was exists.
        visibleButUnsafe -- if True during transaction new content is visible.
        modifiedList -- a list to add file name if was changed.

        """
        super(FileTransaction, self).__init__()
        self._name = name
        self._binary = binary

        if self._binary:
            self._content = content
        else:
            if isinstance(content, list) or isinstance(content, tuple):
                self._content = '\n'.join(content)
                if content:
                    self._content += '\n'
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
        self._visibleButUnsafe = visibleButUnsafe
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
        self._backup = None
        self._originalFileWasMissing = not os.path.exists(self._name)
        self._prepared = False
        self._originalDiffer = True

    def __str__(self):
        return _("File transaction for '{file}'").format(
            file=self._name
        )

    def prepare(self):
        if self._originalFileWasMissing:
            self.logger.debug("file '%s' missing" % self._name)
        else:
            self.logger.debug("file '%s' exists" % self._name)
            with open(self._name, 'r' + ('b' if self._binary else '')) as f:
                if f.read() == self._content:
                    self.logger.debug(
                        "file '%s' already has content" % self._name
                    )
                    self._originalDiffer = False

        if self._originalDiffer:
            mydir = os.path.dirname(self._name)
            if self._originalFileWasMissing:
                if not os.path.exists(mydir):
                    self._createDirRecursive(mydir)
            else:
                # check we can open file for write
                with open(self._name, 'a'):
                    pass

                currentStat = os.stat(self._name)
                if not self._enforcePermissions:
                    self._mode = currentStat.st_mode
                    self._owner = currentStat.st_uid
                    self._group = currentStat.st_gid

                #
                # backup the file
                #
                self._backup = "%s.%s" % (
                    self._name,
                    datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                )
                self.logger.debug(
                    "backup '%s'->'%s'" % (
                        self._name,
                        self._backup
                    )
                )
                shutil.copyfile(self._name, self._backup)
                shutil.copystat(self._name, self._backup)
                os.chown(
                    self._backup,
                    currentStat.st_uid,
                    currentStat.st_gid
                )

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

                if self._visibleButUnsafe:
                    type(self)._atomicMove(
                        source=self._tmpname,
                        destination=self._name,
                        binary=self._binary,
                    )

                self._prepared = True
            finally:
                if fd != -1:
                    try:
                        os.close(fd)
                    except OSError:
                        pass
                    fd = -1

    def abort(self):
        try:
            if self._visibleButUnsafe:
                if self._originalFileWasMissing:
                    if os.path.exists(self._name):
                        os.unlink(self._name)
                elif (
                    self._backup is not None and
                    os.path.exists(self._backup)
                ):
                    type(self)._atomicMove(
                        source=self._backup,
                        destination=self._name,
                        binary=self._binary,
                    )
            else:
                if (
                    self._tmpname is not None and
                    os.path.exists(self._tmpname)
                ):
                    os.unlink(self._tmpname)
        except OSError:
            self.logger.debug('Exception during abort', exc_info=True)
            pass

    def commit(self):
        if self._prepared:
            if not self._visibleButUnsafe:
                type(self)._atomicMove(
                    source=self._tmpname,
                    destination=self._name,
                    binary=self._binary,
                )
            if self._modifiedList is not None:
                self._modifiedList.append(self._name)


# vim: expandtab tabstop=4 shiftwidth=4
