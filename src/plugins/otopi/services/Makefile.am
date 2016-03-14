#
# otopi -- plugable installer
#

include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

mydir=$(otopiplugindir)/otopi/services
dist_my_PYTHON = \
	__init__.py \
	openrc.py \
	rhel.py \
	systemd.py \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)

all-local: \
	python-syntax-check \
	$(NULL)
