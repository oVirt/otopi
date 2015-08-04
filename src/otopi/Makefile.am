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

include $(top_srcdir)/build/subst.inc
include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)
CLEANFILES = \
	config.py \
	$(NULL)

SUFFIXES = .in

SUBDIRS = \
	codegen \
	$(NULL)

dist_otopilib_PYTHON = \
	__init__.py \
	__main__.py \
	base.py \
	command.py \
	common.py \
	constants.py \
	context.py \
	dialog.py \
	filetransaction.py \
	main.py \
	minidnf.py \
	miniyum.py \
	packager.py \
	plugin.py \
	services.py \
	transaction.py \
	util.py \
	$(NULL)
otopilib_PYTHON = \
	config.py \
	$(NULL)

config.py: \
	$(top_srcdir)/configure.ac \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)

all-local: \
	$(DISTFILES) \
	python-syntax-check \
	$(NULL)
