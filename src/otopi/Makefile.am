#
# otopi -- plugable installer
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
