#!/bin/bash -ex
autoreconf -ivf
./configure --enable-java-sdk COMMONS_LOGGING_JAR=$(build-classpath commons-logging) JUNIT_JAR=$((build-classpath junit4 || build-classpath junit) | sed '/^$/d')
make distcheck

automation/build-artifacts.sh

DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
installer=""
if [[ "${DISTVER}" == "el" ]]; then
    installer=yum
else
    installer=dnf
fi
${installer} install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)

cov_otopi() {
	OTOPI_DEBUG=1 OTOPI_COVERAGE=1 COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX) otopi "$@"
}

# Test packager
# In otopi 1.7, fedora/dnf is broken, do not run there for now.
[[ "${DISTVER}" == "el" ]] && cov_otopi ODEBUG/packagesAction=str:install ODEBUG/packages=str:zziplib,zsh

# Test command
PATH="${PWD}/automation/testbin:$PATH" OTOPI_TEST_COMMAND=1 cov_otopi

# Test machine dialog
cov_otopi DIALOG/dialect=str:machine

cov_otopi "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:change_env_type"

# Test failures
cov_failing_otopi() {
	if cov_otopi "$@"; then
		echo otopi was supposed to fail but did not
		exit 1
	else
		echo otopi failed and this is ok
	fi
}

OTOPI_FORCE_FAIL_STAGE=STAGE_MISC cov_failing_otopi
cov_failing_otopi "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:bad_plugin1"

mkdir -p exported-artifacts/logs
cp -p /tmp/otopi-*.log exported-artifacts/logs

coverage combine
coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

