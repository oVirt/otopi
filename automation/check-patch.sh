#!/bin/bash -e
[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

autoreconf -ivf
./configure --enable-java-sdk COMMONS_LOGGING_JAR=$(build-classpath commons-logging) JUNIT_JAR=$((build-classpath junit4 || build-classpath junit) | sed '/^$/d')
make distcheck

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos
yum-builddep otopi.spec
rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    -D "release_suffix ${SUFFIX}" \
    -ta otopi-*.tar.gz

mv *.tar.gz exported-artifacts

find \
    "$PWD/tmp.repos" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;

yum install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)
OTOPI_DEBUG=1 otopi
