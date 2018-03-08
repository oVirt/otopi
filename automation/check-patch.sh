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

mkdir -p exported-artifacts/logs

cleanup() {
	cp -p /tmp/otopi-*.log exported-artifacts/logs
}

trap cleanup EXIT

cov_otopi() {
	otopi="$1"
	name="$2"
	shift 2
	OTOPI_DEBUG=1 OTOPI_COVERAGE=1 COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX) "${otopi}" CORE/logFileNamePrefix="str:${otopi}-${name}" "$@"
}

# Test packager
cov_otopi otopi packager ODEBUG/packagesAction=str:install ODEBUG/packages=str:zziplib,zsh

# Test command
PATH="${PWD}/automation/testbin:$PATH" OTOPI_TEST_COMMAND=1 cov_otopi otopi command

# Test machine dialog
cov_otopi otopi machine DIALOG/dialect=str:machine

cov_otopi otopi change_env_type "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:change_env_type"

# Test failures
cov_failing_otopi() {
	if cov_otopi "$@"; then
		echo otopi was supposed to fail but did not
		exit 1
	else
		echo otopi failed and this is ok
	fi
}

OTOPI_FORCE_FAIL_STAGE=STAGE_MISC cov_failing_otopi otopi force_fail
cov_failing_otopi otopi bad_before_after "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:bad_plugin1"

# Do some minimal testing for python3. This probably applies to no supported
# distros currently, because we only build python3-otopi for fedora (not for
# el7), and there the default "python" is already python-3, so already tested
# above by running 'otopi'. Still might be useful if/when we support otopi-3
# also on el7 one day.
if command -v otopi-3 >/dev/null 2>&1; then
	cov_otopi otopi-3 packager ODEBUG/packagesAction=str:install ODEBUG/packages=str:yelp-tools
fi

coverage combine
coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

