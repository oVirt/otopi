dnl
dnl otopi -- plugable installer
dnl

AC_PREREQ(2.60)

define([VERSION_MAJOR], [1])
define([VERSION_MINOR], [10])
define([VERSION_FIX], [4])
define([VERSION_NUMBER], VERSION_MAJOR[.]VERSION_MINOR[.]VERSION_FIX)
define([VERSION_SUFFIX], [_master])

AC_INIT([otopi], VERSION_NUMBER[]VERSION_SUFFIX)
PACKAGE_RPM_VERSION="VERSION_NUMBER"
PACKAGE_RPM_RELEASE="0.0.$(echo VERSION_SUFFIX | sed 's/^_//')"
RELEASE_SUFFIX="VERSION_SUFFIX"
AC_SUBST([PACKAGE_RPM_VERSION])
AC_SUBST([PACKAGE_RPM_RELEASE])
AC_SUBST([RELEASE_SUFFIX])

AC_CONFIG_AUX_DIR([.])
AC_CONFIG_SRCDIR([src/otopi/__init__.py])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE


AM_GNU_GETTEXT([external])
AM_GNU_GETTEXT_REQUIRE_VERSION([0.19.6])


AC_ARG_ENABLE(
	[python-syntax-check],
	[AS_HELP_STRING([--disable-python-syntax-check], [disable python syntax check @<:@default=enabled@:>@])],
	,
	[enable_python_syntax_check="yes"]
)

AC_ARG_WITH(
	[local-version],
	[AS_HELP_STRING([--with-local-version], [local version to use])],
	[LOCAL_VERSION="${withval}"],
	[LOCAL_VERSION=""]
)

AC_PROG_INSTALL
AC_PROG_SED
AC_PROG_MAKE_SET
AC_PROG_MKDIR_P
AC_PROG_LN_S
AX_LN_SR

AC_ARG_VAR([PYFLAKES], [path to pyflakes utility])
AC_CHECK_PROGS([PYFLAKES], [pyflakes])
AC_ARG_VAR([PEP8], [path to pep8 utility])
AC_CHECK_PROGS([PEP8], [pycodestyle-3 pep8])

AM_PATH_PYTHON([3.6],, [AC_MSG_ERROR([Cannot find python])])

otopilibdir="\$(pythondir)/otopi"
otopiplugindir="\$(pkgdatadir)/plugins"
AC_SUBST([otopilibdir])
AC_SUBST([otopiplugindir])
AC_SUBST([LOCAL_VERSION])
AM_CONDITIONAL([PYTHON_SYNTAX_CHECK], [test "${enable_python_syntax_check}" = "yes"])


AC_CONFIG_FILES([
	Makefile
	otopi.spec
	build/Makefile
	build/otopi-bundle.in
	po/Makefile.in
	src/Makefile
	src/bin/Makefile
	src/otopi/Makefile
	src/otopi/config.py.in
	src/plugins/Makefile
	src/plugins/otopi/Makefile
	src/plugins/otopi/core/Makefile
	src/plugins/otopi/dialog/Makefile
	src/plugins/otopi/system/Makefile
	src/plugins/otopi/network/Makefile
	src/plugins/otopi/services/Makefile
	src/plugins/otopi/packagers/Makefile
	src/plugins/otopi/debug/Makefile
	src/plugins/otopi/debug/debug_failure/Makefile
	src/plugins/otopi/debug/force_fail/Makefile
	src/plugins/otopi/debug/test_command/Makefile
	src/plugins/otopi/debug/test_note/Makefile
	src/plugins/otopi/debug/wait_on_error/Makefile
	src/plugins/otopi/debug/packages/Makefile
	automation/config.sh
	automation/testRPMs/testpackage1/testpackage1.spec
	automation/testRPMs/testpackage2/testpackage2.spec
	automation/testRPMsUpdates/testpackage1/testpackage1.spec
	automation/testRPMsUpdates/testpackage2/testpackage2.spec

])
AC_OUTPUT
