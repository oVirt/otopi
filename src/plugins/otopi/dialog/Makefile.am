#
# otopi -- plugable installer
#

include $(top_srcdir)/build/python.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

mydir=$(otopiplugindir)/otopi/dialog
dist_my_PYTHON = \
	__init__.py \
	answer_file.py \
	cli.py \
	constants.py \
	human.py \
	machine.py \
	misc.py \
	$(NULL)

clean-local: \
	python-clean \
	$(NULL)

all-local: \
	python-syntax-check \
	$(NULL)
