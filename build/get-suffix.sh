#!/bin/sh

# GitHub's actions/checkout by default merges the PR into the target branch.
# In this case, we want to return the hash of the PR, not of the merge.

is_github_merge() {
	# If the reference looks like refs/pull/23/merge , and
	# the committer email is github, and the subject starts with 'Merge',
	# it's a github merge.
	echo "${GITHUB_REF}" | grep -q '/merge$' &&
		git log --max-count=1 --pretty=%ce | grep -q '^noreply@github.com$' &&
		git log --max-count=1 --pretty=%s | grep -q '^Merge '
}

ref() {
	if is_github_merge; then
		# HEAD~ should get us the commit we merged into, hopefully
		target_branch_head=$(git log --max-count=1 --pretty=%h HEAD~)
		# %P gives us all parents. Filter out the target branch, to get the PR commit.
		# Sadly, I failed to find any direct way to get it from GITHUB* variables.
		git log --max-count=1 --pretty=%P | tr ' ' '\n' | grep -v "${target_branch_head}"
	else
		echo HEAD
	fi
}

echo $(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short $(ref))
