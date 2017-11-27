#!/bin/bash -ex
[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

autoreconf -ivf
./configure --enable-java-sdk COMMONS_LOGGING_JAR=$(build-classpath commons-logging) JUNIT_JAR=$((build-classpath junit4 || build-classpath junit) | sed '/^$/d')
make distcheck

SUFFIX=
. automation/config.sh
[ -n "${RELEASE_SUFFIX}" ] && SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos
yum-builddep otopi.spec
rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    ${SUFFIX:+-D "release_suffix ${SUFFIX}"} \
    -ta otopi-*.tar.gz

mv *.tar.gz exported-artifacts

find \
    "$PWD/tmp.repos" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;

yum install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)

cov_otopi() {
	OTOPI_DEBUG=1 OTOPI_COVERAGE=1 COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX) otopi "$@"
}

# Test packager
cov_otopi ODEBUG/packagesAction=str:install ODEBUG/packages=str:zziplib,zsh

# Test command
PATH="${PWD}/automation/testbin:$PATH" OTOPI_TEST_COMMAND=1 cov_otopi

# Test machine dialog
cov_otopi DIALOG/dialect=str:machine

# Test failures
OTOPI_FORCE_FAIL_STAGE=STAGE_MISC cov_otopi || echo "Otopi was forced to fail, this is ok"

mkdir -p exported-artifacts/logs
cp -p /tmp/otopi-*.log exported-artifacts/logs

coverage combine
coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

