.PHONY: installdeps srpm git_config_pre

installdeps:
	dnf install -y $(shell cat automation/build-artifacts.packages)

git_config_pre:
	# From git 2.35.2 we need to mark temporary directory, where the project is cloned to, as safe, otherwise
	# git commands won't work
	$(eval REPO_DIR=$(shell pwd))
	git config --global --add safe.directory ${REPO_DIR}

prepare: installdeps git_config_pre
	# Calling 'eval' in 'srpm:' is done when parsing that target,
	# so we need to have this 'prepare' separate target for
	# preparing stuff so that the 'eval' call will work.
	autopoint
	autoreconf -ivf
	./configure

srpm: installdeps git_config_pre prepare
	$(eval SUFFIX=$(shell sh -c ' . automation/config.sh; [ -n "$${RELEASE_SUFFIX}" ] && echo ".$$(date -u +%Y%m%d%H%M%S).git$$(git rev-parse --short HEAD)"'))
	mkdir -p tmp.repos
	# changing the spec file as passing -D won't preserve the suffix when rebuilding in mock
	sed "s:%{?release_suffix}:${SUFFIX}:" -i otopi.spec.in
	make dist
	rpmbuild \
		-D "_topdir tmp.repos" \
		-ts ./*.tar.gz
	cp tmp.repos/SRPMS/*.src.rpm $(outdir)
