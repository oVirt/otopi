#
# otopi -- plugable installer
#

.in:
	if sed \
		-e 's#[@]otopiplugindir_POST@#$(otopiplugindir)#g' \
		-e 's#[@]otopilibdir_POST@#$(otopilibdir)#g' \
		-e 's#[@]localedir_POST@#$(localedir)#g' \
		-e 's#[@]sbindir_POST@#$(sbindir)#g' \
		$< > $@.tmp; then \
		mv "$@.tmp" "$@"; \
	else \
		rm -f "$@.tmp"; \
		false; \
	fi
