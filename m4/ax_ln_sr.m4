dnl
dnl otopi -- plugable installer
dnl
dnl rhel, fedora does not support ln -r
dnl
AC_DEFUN([AX_LN_SR], [
	AC_MSG_CHECKING([if 'ln -sr' supported])
	ln -sr test conftest 2> /dev/null
	result=$?
	rm -f conftest
	if test "${result}" = 0; then
		AC_MSG_RESULT([yes])
		LN_SR="ln -sr"
		HAVE_LN_SR="1"
	else
		AC_MSG_RESULT([no])
		LN_SR="${ac_abs_confdir}/ln-sr"
		HAVE_LN_SR="0"
		cat > "${ac_abs_confdir}/ln-sr" << __EOF__
#!/bin/sh
src="\[$]1"
dst="\[$]2"
relative="\$(perl -MFile::Spec -e 'print File::Spec->abs2rel("'\${src}'","'\$(dirname "\${dst}")'")' 2> /dev/null)"
if test "\$?" = 0; then
	exec ln -s "\${relative}" "\${dst}"
else
	echo "WARNING: Cannot create relative path"
	exec ln -s "\$(echo "\${src}" | sed "s#^\${DESTDIR}##")" "\${dst}"
fi
__EOF__
		chmod a+x "${ac_abs_confdir}/ln-sr"
	fi
	AC_SUBST([LN_SR])
	AC_SUBST([HAVE_LN_SR])
])
