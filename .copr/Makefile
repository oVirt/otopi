.PHONY: installdeps srpm git_config_pre

installdeps:
	dnf -y install git autoconf automake make gettext-devel gcc

git_config_pre:
	# From git 2.35.2 we need to mark temporary directory, where the project is cloned to, as safe, otherwise
	# git commands won't work
	$(eval REPO_DIR=$(shell pwd))
	git config --global --add safe.directory ${REPO_DIR}

srpm: installdeps git_config_pre
	mkdir -p tmp.repos
	autopoint
	autoreconf -ivf
	./configure
	$(eval SUFFIX=$(shell sh -c " . automation/config.sh; [ -n "$${RELEASE_SUFFIX}" ] && echo '.$$(date -u +%Y%m%d%H%M%S).git$$(git rev-parse --short HEAD)'"))
	# changing the spec file as passing -D won't preserve the suffix when rebuilding in mock
	sed "s:%{?release_suffix}:${SUFFIX}:" -i otopi.spec.in
	make dist
	rpmbuild \
		-D "_topdir tmp.repos" \
		-ts ./*.tar.gz
	cp tmp.repos/SRPMS/*.src.rpm $(outdir)
