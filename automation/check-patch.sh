#!/bin/bash -ex
DISTVER="$(rpm --eval "%dist"|cut -c2-4)"
installer=dnf

# stdci seems to ignore check-patch.packages
${installer} install -y $(cat automation/check-patch.packages)

autopoint
autoreconf -ivf
./configure
make distcheck

automation/build-artifacts.sh
automation/run-checks.sh
