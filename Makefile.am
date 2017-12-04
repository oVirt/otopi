#
# otopi -- plugable installer
#

AUTOMAKE_OPTIONS = foreign 1.9
ACLOCAL_AMFLAGS = -I m4

MAINTAINERCLEANFILES = \
	config.log config.status \
	$(srcdir)/Makefile.in \
	$(srcdir)/configure \
	$(srcdir)/install-sh $(srcdir)/missing \
	$(srcdir)/depcomp $(srcdir)/py-compile \
	$(srcdir)/config.guess $(srcdir)/config.sub \
	$(srcdir)/config.rpath \
	$(srcdir)/ABOUT-NLS \
	$(srcdir)/aclocal.m4 \
	$(srcdir)/ln-sr \
	$(NULL)
CLEANFILES = \
	POTFILES.in.tmp \
	$(NULL)

EXTRA_DIST = \
	.gitignore \
	m4/.gitignore \
	po/.gitignore \
	$(NULL)

SUBDIRS = \
	build \
	po \
	src \
	$(NULL)

dist_noinst_DATA = \
	MAINTAINERS \
	README.API \
	README.config-query \
	README.debug-plugins \
	README.dialog \
	README.environment \
	README.localization \
	LICENSE \
	otopi.spec \
	$(NULL)

clean-local:
	rm -fr "$(TMPREPOS)"
	rm -fr target

maintainer-clean-local:
	sed '/^$$/d' "$(srcdir)/m4/.gitignore" | while read f; do \
		rm -f $(srcdir)/m4/$$f; \
	done
	sed '/^$$/d' "$(srcdir)/po/.gitignore" | while read f; do \
		rm -f $(srcdir)/po/$$f po/$$f; \
	done

POTFILES.in:
	( cd "$(srcdir)" && \
		find ./src -name '*.py' -or -name '*.py.in' ) | \
		sort | grep -v config.py > POTFILES.in.tmp && \
	cmp -s POTFILES.in.tmp "$(srcdir)/po/POTFILES.in" || \
		cp POTFILES.in.tmp "$(srcdir)/po/POTFILES.in"; \
	rm -f POTFILES.in.tmp

update-po: POTFILES.in
	$(MAKE) -C po update-po
