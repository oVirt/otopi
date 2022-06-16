#!/bin/bash -xe
[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos

# stdci seems to ignore build-artifacts.packages
dnf install -y $(cat automation/build-artifacts.packages)
autopoint
autoreconf -ivf
./configure

SUFFIX=
. automation/config.sh
[ -n "${RELEASE_SUFFIX}" ] && SUFFIX=".$(build/get-suffix.sh)"

make dist

if [ -e /etc/fedora-release ]; then
	dnf builddep --spec otopi.spec
else
	yum-builddep otopi.spec
fi

rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    ${SUFFIX:+-D "release_suffix ${SUFFIX}"} \
    -ta otopi-*.tar.gz

mv *.tar.gz exported-artifacts
find \
    "$PWD/tmp.repos" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
