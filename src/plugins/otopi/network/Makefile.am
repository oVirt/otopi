#
# otopi -- plugable installer
#

include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

mydir=$(otopiplugindir)/otopi/network
dist_my_PYTHON = \
	__init__.py \
	firewalld.py \
	hostname.py \
	iptables.py \
	ssh.py \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)

all-local: \
	python-syntax-check \
	$(NULL)
