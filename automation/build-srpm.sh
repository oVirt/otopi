#!/bin/bash -xe
[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos

# stdci seems to ignore build-artifacts.packages
dnf install -y $(cat automation/build-artifacts.packages)
autopoint
autoreconf -ivf
./configure

SUFFIX=
. automation/config.sh
[ -n "${RELEASE_SUFFIX}" ] && SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

make dist

if [ -e /etc/fedora-release ]; then
	dnf builddep --spec otopi.spec
else
	yum-builddep otopi.spec
fi

rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    ${SUFFIX:+-D "release_suffix ${SUFFIX}"} \
    -ts otopi-*.tar.gz
