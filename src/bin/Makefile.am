#
# otopi -- plugable installer
#

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)
CLEANFILES = \
	config.py \
	$(NULL)

EXTRA_DIST = \
	.source \
	$(NULL)

dist_sbin_SCRIPTS = \
	otopi \
	$(NULL)

dist_bin_SCRIPTS = \
	otopi-config-query \
	$(NULL)

mydir=$(pkgdatadir)/scripts
dist_my_PYTHON = \
	otopi-config-query.py \
	$(NULL)
