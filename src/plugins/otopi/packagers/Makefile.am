#
# otopi -- plugable installer
#

include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

mydir=$(otopiplugindir)/otopi/packagers
dist_my_PYTHON = \
	__init__.py \
	dnfpackager.py \
	yumpackager.py \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)

all-local: \
	python-syntax-check \
	$(NULL)
