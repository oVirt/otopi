#!/bin/bash -ex

group_start() {
	echo "::group::$@"
}

group_end() {
	echo "::endgroup::"
}

info() {
	echo "::notice:: INFO: $@"
}

err() {
	echo "::error:: ERROR: $@"
}

group_start Initialize

installer=dnf

${installer} install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)

LOGS=exported-artifacts/otopi_logs
mkdir -p "${LOGS}"

group_end

prepare_rpm_signing() {
	group_start prepare_rpm_signing
	export GNUPGHOME="${PWD}"/gpghome
	export GPGUSER="GPG User1"
	export GPGPUBKEY="${PWD}/RPM-GPG-key1"
	mkdir -p "${GNUPGHOME}"
	cat << __EOF__ > gpg-batch1
%no-protection
Key-Type: default
Subkey-Type: default
Name-Real: ${GPGUSER}
Name-Email: rn@example.com
Expire-Date: 0
__EOF__
	gpg --batch --gen-key gpg-batch1
	gpg --export -a "${GPGUSER}" > "${GPGPUBKEY}"
	export MY_RPM_HOME="${PWD}"
	cat << __EOF__ > "${MY_RPM_HOME}/.rpmmacros"
%_signature gpg
%_gpg_path ${GNUPGHOME}
%_gpg_name ${GPGUSER}
%_gpgbin /usr/bin/gpg
__EOF__
}

sign_rpms() {
	local repodir="$1"
	find "${repodir}" -name "*.rpm" -print0 | \
		HOME="${MY_RPM_HOME}" xargs -0 rpm --addsign
}

prepare_test_repo() {
	group_start prepare_test_repo
	pushd automation/testRPMs
	mkdir repos
	for p in testpackage*; do
		tar czf "${p}.tar.gz" "${p}"
		rpmbuild -D "_topdir $PWD/repos" -ta "${p}.tar.gz"
	done
	sign_rpms "$PWD/repos"
	createrepo_c repos
	for yumdnfconf in /etc/yum.conf /etc/dnf/dnf.conf; do
		if [ -f "${yumdnfconf}" ]; then
			cat << __EOF__ >> "${yumdnfconf}"
[testpackages]
name=packages for testing otopi
baseurl=file://${PWD}/repos
gpgcheck=1
enabled=1
gpgkey=file://${GPGPUBKEY}
__EOF__
		fi
	done
	popd
	group_end
}

prepare_test_updates_repo() {
	group_start prepare_test_updates_repo
	pushd automation/testRPMsUpdates
	mkdir repos_updates
	for p in testpackage*; do
		tar czf "${p}.tar.gz" "${p}"
		rpmbuild -D "_topdir $PWD/repos_updates" -ta "${p}.tar.gz"
	done
	sign_rpms "$PWD/repos_updates"
	createrepo_c repos_updates
	for yumdnfconf in /etc/yum.conf /etc/dnf/dnf.conf; do
		if [ -f "${yumdnfconf}" ]; then
			cat << __EOF__ >> "${yumdnfconf}"
[testpackagesupdates]
name=packages for testing otopi - updates
baseurl=file://${PWD}/repos_updates
gpgcheck=1
enabled=1
gpgkey=file://${GPGPUBKEY}
__EOF__
		fi
	done
	popd
	group_end
}

test_otopi() {
	group_start "test_otopi $2"
	local -r EXPECTED_RC="$1"
	local -r NAME="$2"
	shift 2
	info "Testing otopi: name [${NAME}] expected rc [${EXPECTED_RC}]"

	local -r LOG_DIR="${LOGS}/otopi-$(date +"%Y%m%d-%H%M%S")-${NAME}"
	mkdir -p "${LOG_DIR}"

	local -r OUTPUTFILE="${LOG_DIR}/otopi-output-${NAME}.log"

	local rc=0
	OTOPI_DEBUG=1 \
		OTOPI_COVERAGE=1 \
		COVERAGE_PROCESS_START="${PWD}/automation/coverage.rc" \
		COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX) \
		otopi \
			CORE/logFileNamePrefix="str:otopi-${NAME}" \
			CORE/logDir=str:"${LOG_DIR}" \
			"$@" \
			> "${OUTPUTFILE}" 2>&1 || rc=$?

	if [ "${rc}" -ne "${EXPECTED_RC}" ]; then
		err "otopi was supposed to have exit code ${EXPECTED_RC} but had instead ${rc}"
		tail -20 "${STDERRFILE}"
		exit 1
	else
		info "otopi exited with exit code ${rc} as expected"
	fi
	group_end
}

prepare_rpm_signing
prepare_test_repo
# Verify rpm signing verification.
# Try to install without importing the key
# We do not have in otopi a "run unattended" option,
# to make sure it will fail when prompting for a confirmation.
# "Simulate" this by running without an stdin.
:|test_otopi 1 packager-install-testpackage1-no-gpgkey-import ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage1
# Try again, but confirm
test_otopi 0 packager-install-testpackage1-gpgkey-import QUESTION/1/DIALOG_CONFIRM/GPG_KEY=str:yes ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage1
# All later installations will be verified.
# TODO: Is there value in removing the key and seeing that an installation fails?
test_otopi 0 packager-install-testpackage2 ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage2
test_otopi 0 packager-query-testpackages ODEBUG/packagesAction=str:queryPackages ODEBUG/packages=str:testpackage\*
test_otopi 0 packager-checksafeupdate ODEBUG/packagesAction=str:checkForSafeUpdate ODEBUG/packages=str:testpackage1,testpackage2
test_otopi 0 packager-remove-testpackage1 ODEBUG/packagesAction=str:remove ODEBUG/packages=str:testpackage1
test_otopi 0 packager-queryGroups ODEBUG/packagesAction=str:queryGroups

# Group install/remove. TODO: Create our own group in automation/testRPMs and use that, instead of 'ftp-server'.
test_otopi 0 packager-install-group-ftp-server ODEBUG/packagesAction=str:installGroup ODEBUG/packages=str:ftp-server
test_otopi 0 packager-remove-group-ftp-server ODEBUG/packagesAction=str:removeGroup ODEBUG/packages=str:ftp-server

# Test command
PATH="${PWD}/automation/testbin:$PATH" OTOPI_TEST_COMMAND=1 test_otopi 0 command

# Test machine dialog
test_otopi 0 machine DIALOG/dialect=str:machine

test_otopi 0 change_env_type "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:change_env_type"

# Test failures

OTOPI_FORCE_FAIL_STAGE=STAGE_MISC test_otopi 1 force_fail
test_otopi 1 bad_before_after "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:bad_plugin1"
test_otopi 1 cyclic_dep "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:event_cyclic_dep"
test_otopi 1 non_existent_before_after "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:non_existent_before_after CORE/ignoreMissingBeforeAfter=bool:False"
test_otopi 1 duplicate_method_names "APPEND:BASE/pluginPath=str:${PWD}/automation/testplugins" "APPEND:BASE/pluginGroups=str:duplicate_method_names"

# Test packager rollback. testpackage1 should not be installed at this point, because we remove it earlier
if rpm -q testpackage1 2>&1; then
	err "Packager rollback: testpackage1 found before testing, failing"
	exit 1
fi
OTOPI_FORCE_FAIL_STAGE=STAGE_MISC test_otopi 1 packager-install-testpackage1-undo ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage1
# force_fail should fail it, so using 'test_otopi 1', but we also want to verify that testpackage1's installation was reverted
if rpm -q testpackage1 2>&1; then
	err "Packager rollback: testpackage1 found after testing, failing"
	exit 1
fi

test_otopi 0 packager-install-testpackage1 ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage1
prepare_test_updates_repo
# 101 is EXIT_CODE_DEBUG_PACKAGER_ROLLBACK_EXISTS - there is an update, and if we fail to update, we can rollback
test_otopi 101 packager-checksafeupdate-with-update ODEBUG/packagesAction=str:checkForSafeUpdate ODEBUG/packages=str:testpackage1,testpackage2
dnf config-manager --disable testpackages
# 102 is EXIT_CODE_DEBUG_PACKAGER_ROLLBACK_MISSING - there is an update, but if we fail to update, can't rollback, because existing installed package can't be found in current repos
test_otopi 102 packager-checksafeupdate-with-disabled-current ODEBUG/packagesAction=str:checkForSafeUpdate ODEBUG/packages=str:testpackage1,testpackage2
dnf config-manager --enable testpackages
test_otopi 101 packager-checksafeupdate-with-update ODEBUG/packagesAction=str:checkForSafeUpdate ODEBUG/packages=str:testpackage1,testpackage2
# Try again to update, but force failing - to test that rollback to current version works
OTOPI_FORCE_FAIL_STAGE=STAGE_MISC test_otopi 1 packager-install-update-testpackage1-undo ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage1
test_otopi 101 packager-checksafeupdate-with-update ODEBUG/packagesAction=str:checkForSafeUpdate ODEBUG/packages=str:testpackage1,testpackage2
test_otopi 0 packager-install-update-testpackage1-do ODEBUG/packagesAction=str:install ODEBUG/packages=str:testpackage1
if ! rpm -q testpackage1 2>&1 | grep 'testpackage1-1.0.1'; then
	err "testpackage1-1.0.1 not found, update failed"
	exit 1
fi

coverage-3 combine --rcfile="${PWD}/automation/coverage.rc"
coverage-3 html -d exported-artifacts/coverage_html_report --rcfile="${PWD}/automation/coverage.rc"
cp automation/index.html exported-artifacts/

