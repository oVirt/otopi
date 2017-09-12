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
otopi ODEBUG/packagesAction=str:install ODEBUG/packages=str:zziplib,zsh
OTOPI_DEBUG=1 otopi DIALOG/dialect=str:machine
OTOPI_DEBUG=1 OTOPI_COVERAGE=1 COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" otopi
mkdir -p exported-artifacts/logs
cp -p /tmp/otopi-*.log exported-artifacts/logs

coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

