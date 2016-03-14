#
# otopi -- plugable installer
#

include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

mydir=$(otopiplugindir)/otopi/core
dist_my_PYTHON = \
	__init__.py \
	config.py \
	log.py \
	misc.py \
	transaction.py \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)

all-local: \
	python-syntax-check \
	$(NULL)
