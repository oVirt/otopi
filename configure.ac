dnl
dnl otopi -- plugable installer
dnl

AC_PREREQ(2.60)

define([VERSION_MAJOR], [1])
define([VERSION_MINOR], [6])
define([VERSION_FIX], [2])
define([VERSION_NUMBER], VERSION_MAJOR[.]VERSION_MINOR[.]VERSION_FIX)
define([VERSION_SUFFIX], [_master])

AC_INIT([otopi], VERSION_NUMBER[]VERSION_SUFFIX)
PACKAGE_RPM_VERSION="VERSION_NUMBER"
PACKAGE_RPM_RELEASE="0.0.$(echo VERSION_SUFFIX | sed 's/^_//')"
PACKAGE_MAVEN_VERSION="VERSION_MAJOR.VERSION_MINOR.0$(echo VERSION_SUFFIX | sed 's/^_/-/')"
RELEASE_SUFFIX="VERSION_SUFFIX"
AC_SUBST([PACKAGE_RPM_VERSION])
AC_SUBST([PACKAGE_RPM_RELEASE])
AC_SUBST([PACKAGE_MAVEN_VERSION])
AC_SUBST([RELEASE_SUFFIX])

AC_CONFIG_AUX_DIR([.])
AC_CONFIG_SRCDIR([src/otopi/__init__.py])
AC_CONFIG_MACRO_DIR([m4])
AM_INIT_AUTOMAKE

dnl Fallback definition for gettext.m4 older than 0.19.6.
m4_ifndef([AM_GNU_GETTEXT_REQUIRE_VERSION], [m4_define([AM_GNU_GETTEXT_REQUIRE_VERSION])], [])
dnl Prefer the latest infrastructure, given it is newer than 0.18.2.
AM_GNU_GETTEXT_REQUIRE_VERSION([0.18.2])

dnl This will be ignored if the installed autopoint supports
dnl AM_GNU_GETTEXT_REQUIRE_VERSION.
AM_GNU_GETTEXT_VERSION([0.18.2])
AM_PO_SUBDIRS

AC_ARG_ENABLE(
	[python-syntax-check],
	[AS_HELP_STRING([--disable-python-syntax-check], [disable python syntax check @<:@default=enabled@:>@])],
	,
	[enable_python_syntax_check="yes"]
)

AC_ARG_ENABLE(
	[java-sdk],
	[AS_HELP_STRING([--enable-java-sdk], [enable java-sdk @<:@default=disabled@:>@])],
	,
	[enable_java_sdk="no"]
)

AC_ARG_ENABLE(
	[java-sdk-compile],
	[AS_HELP_STRING([--disable-java-sdk-compile], [disable java-sdk compile @<:@default=enabled@:>@])],
	,
	[enable_java_sdk_compile="yes"]
)

AC_ARG_WITH(
	[local-version],
	[AS_HELP_STRING([--with-local-version], [local version to use])],
	[LOCAL_VERSION="${withval}"],
	[LOCAL_VERSION=""]
)

AC_ARG_WITH(
	[maven],
	[AS_HELP_STRING([--with-maven], [use maven to build java-sdk @<:@default=no@:>@])],
	,
	[with_maven="no"]
)

AC_ARG_WITH(
	[maven-version-snapshot],
	[AS_HELP_STRING([--with-maven-version-snapshot], [maven version snapshot @<:@default=no@:>@])],
	,
	[with_maven_version_snapshot="no"]
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
AC_CHECK_PROGS([PEP8], [pep8])
AC_ARG_VAR([MVN], [path to mvn utility])
AC_CHECK_PROGS([MVN], [mvn])
AC_ARG_VAR([JAVAC], [path to java compiler])
AC_CHECK_PROGS([JAVAC], [javac])
AC_ARG_VAR([JAR], [path to jar utility])
AC_CHECK_PROGS([JAR], [jar])

AC_ARG_VAR([COMMONS_LOGGING_JAR], [path to commons-logging jar])
AC_ARG_VAR([JUNIT_JAR], [path to junit jar])

if test "${enable_java_sdk}" = "yes" -a "${enable_java_sdk_compile}" = "yes"; then
	if test "${with_maven}" = "yes"; then
		test -z "${MVN}" && \
			AC_MSG_ERROR([maven is required but not found])
	else
		test -z "${JAVAC}" && \
			AC_MSG_ERROR([javac is required but not found])
		test -z "${JAR}" && \
			AC_MSG_ERROR([jar is required but not found])
	fi
fi

if test "${with_maven_version_snapshot}" = "no"; then
	MAVEN_VERSION_SNAPSHOT=""
else
	MAVEN_VERSION_SNAPSHOT="-SNAPSHOT"
fi
AC_SUBST([MAVEN_VERSION_SNAPSHOT])

AM_PATH_PYTHON([2.6],, [AC_MSG_ERROR([Cannot find python])])

otopilibdir="\$(pythondir)/otopi"
otopiplugindir="\$(pkgdatadir)/plugins"
AC_SUBST([otopilibdir])
AC_SUBST([otopiplugindir])
AC_SUBST([LOCAL_VERSION])
AM_CONDITIONAL([PYTHON_SYNTAX_CHECK], [test "${enable_python_syntax_check}" = "yes"])
AM_CONDITIONAL([JAVA_SDK], [test "${enable_java_sdk}" = "yes"])
AM_CONDITIONAL([JAVA_SDK_COMPILE], [test "${enable_java_sdk_compile}" = "yes"])
AM_CONDITIONAL([WITH_MAVEN], [test "${with_maven}" = "yes"])

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
	src/otopi/codegen/Makefile
	src/plugins/Makefile
	src/plugins/otopi/Makefile
	src/plugins/otopi/core/Makefile
	src/plugins/otopi/dialog/Makefile
	src/plugins/otopi/system/Makefile
	src/plugins/otopi/network/Makefile
	src/plugins/otopi/services/Makefile
	src/plugins/otopi/packagers/Makefile
	src/plugins/otopi/debug/Makefile
	src/plugins/otopi/debug/force_fail/Makefile
	src/plugins/otopi/debug/wait_on_error/Makefile
	src/java/Makefile
	src/java/pom.xml
	automation/config.sh
])
AC_OUTPUT
