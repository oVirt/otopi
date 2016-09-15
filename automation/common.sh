[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

# On fedora 23 and up, we want to use python3, as by default dnf is python3 and we want to be able to use it.
distribution_name="$(python -c "import platform; print(platform.linux_distribution(full_distribution_name=0)[0])")"
distribution_version="$(python -c "import platform; print(platform.linux_distribution(full_distribution_name=0)[1])")"
if [ "${distribution_name}" == "fedora" -a "${distribution_version}" -ge 23 ]; then
	DEVPKG=python3-devel
	PEP8PKG=python3-pep8
	FLAKGESPKG=python3-pyflakes
	COVPKG=python3-coverage
	PEP8=/usr/bin/python3-pep8
	PYFLAKES=/usr/bin/python3-pyflakes
	COVERAGE=/usr/bin/python3-coverage
	PYTHON=/usr/bin/python3
else
	DEVPKG=python2-devel
	PEP8PKG=python-pep8
	FLAKGESPKG=pyflakes
	COVPKG=python-coverage
	PEP8=/usr/bin/pep8
	PYFLAKES=/usr/bin/pyflakes
	COVERAGE=/usr/bin/coverage
	PYTHON=/usr/bin/python
fi
export PEP8 PYFLAKES PYTHON
yum install -y $DEVPKG $PEP8PKG $FLAKGESPKG $COVPKG

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

sed "s;@WORKDIR@;$PWD;" < automation/coverage.rc.in > automation/coverage.rc

for f in /etc/yum.conf /etc/yum/yum.conf /etc/dnf/dnf.conf; do
	echo "**** Checking file $f ****"
	echo ls -l $f
	ls -l $f || true
	echo cat $f
	cat $f || true
	echo "**** Finished file $f ****"
done

echo "**** Clearing /etc/dnf/dnf.conf"
:>/etc/dnf/dnf.conf || true
echo "**** Cleared /etc/dnf/dnf.conf"

