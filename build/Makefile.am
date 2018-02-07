#
# otopi -- plugable installer
#

include $(top_srcdir)/build/subst.inc

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)
CLEANFILES = \
	otopi-bundle \
	$(NULL)
EXTRA_DIST = \
	otopi-functions \
	$(NULL)

SUFFIXES = .in

pkgdata_SCRIPTS = \
	otopi-bundle \
	otopi-functions \
	$(NULL)

otopi-bundle: \
	$(top_srcdir)/configure.ac \
	$(NULL)
