#!/bin/bash -xe

. automation/common.sh

yum install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)
OTOPI_DEBUG=1 OTOPI_COVERAGE=1 COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" otopi
$COVERAGE html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

