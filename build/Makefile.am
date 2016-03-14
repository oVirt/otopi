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

SUFFIXES = .in

pkgdata_SCRIPTS = \
	otopi-bundle \
	$(NULL)

otopi-bundle: \
	$(top_srcdir)/configure.ac \
	$(NULL)
