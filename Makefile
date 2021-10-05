sepblock=-------------------------------------------------------------------
newblock="$(sepblock)\n$(shell date -u) - $(shell git config user.name) <$(shell git config user.email)>\n\n-\n"

vc:
	@echo -e $(newblock) | cat - python3-azure-img-utils.changes > python3-azure-img-utils.changes.bak && mv python3-azure-img-utils.changes.bak python3-azure-img-utils.changes ||:
	@${VISUAL} +4 python3-azure-img-utils.changes ||:
	@echo "Changes file updated." ||:
