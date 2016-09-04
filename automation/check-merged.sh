#!/bin/bash -e
autoreconf -ivf
./configure --enable-java-sdk COMMONS_LOGGING_JAR=$(build-classpath commons-logging) JUNIT_JAR=$((build-classpath junit4 || build-classpath junit) | sed '/^$/d')
make distcheck

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos
yum-builddep otopi.spec
rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    -ta otopi-*.tar.gz

yum install -y $(find "$PWD/tmp.repos" -iname \*noarch\*.rpm)
OTOPI_COVERAGE=1 COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" otopi
coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/
