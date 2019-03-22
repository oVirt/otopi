#!/bin/bash -ex
DISTVER="$(rpm --eval "%dist"|cut -c2-4)"
installer=""
if [[ "${DISTVER}" == "el7" ]]; then
    installer=yum
else
    installer=dnf
fi

autoreconf -ivf
./configure --enable-java-sdk COMMONS_LOGGING_JAR=$(build-classpath commons-logging) JUNIT_JAR=$((build-classpath junit4 || build-classpath junit) | sed '/^$/d')
make distcheck

automation/build-artifacts.sh

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
cov_otopi otopi packager ODEBUG/packagesAction=str:remove ODEBUG/packages=str:zsh
cov_otopi otopi packager ODEBUG/packagesAction=str:queryGroups

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
cov_failing_otopi otopi cyclic_dep "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:event_cyclic_dep"
cov_failing_otopi otopi non_existent_before_after "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:non_existent_before_after CORE/ignoreMissingBeforeAfter=bool:False"
cov_failing_otopi otopi duplicate_method_names "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:duplicate_method_names"

# Do some minimal testing for python3, even if we default to python2 in the
# rest of the tests. Test if python3 is "supported" simply by running otopi
# with python3 and see if this works. Disable the packagers so that problems
# in them will be revealed in the actual test (and also so that it runs very
# fast).
if OTOPI_PYTHON=python3 otopi PACKAGER/dnfpackagerEnabled=bool:False PACKAGER/yumpackagerEnabled=bool:False > /dev/null 2>&1; then
	OTOPI_PYTHON=python3 cov_otopi otopi packager-python3 ODEBUG/packagesAction=str:install ODEBUG/packages=str:yelp-tools
fi

coverage combine --rcfile="${PWD}/automation/coverage.rc"
coverage html -d exported-artifacts/coverage_html_report --rcfile="${PWD}/automation/coverage.rc"
cp automation/index.html exported-artifacts/

# Validate a bundle on a system without otopi installed
bundle_exec="/usr/share/otopi/otopi-bundle"
bundle_dir="$(mktemp -d)"
selfinst="$(mktemp /tmp/otopi-installer-XXXXX.sh)"

if [ -x ${bundle_exec} ]; then
    ${bundle_exec} --target="${bundle_dir}"
    makeself --follow "${bundle_dir}" "${selfinst}" "Test ${name}" ./otopi packager ODEBUG/packagesAction=str:install ODEBUG/packages=str:zziplib,zsh
fi

${installer} remove "*otopi*" zsh
${selfinst}

cp ${selfinst} exported-artifacts/
