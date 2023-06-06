include Makefile.in

SUBDIR :=

.PHONY: all clean test run build install upgrade help $(SUBDIR)

all: $(SUBDIR) 		# default action
	@[ -f .git/hooks/pre-commit ] || pre-commit install --install-hooks
	@git config commit.template .git-commit-template

clean: $(SUBDIR)	# clean-up environment
	@find . -name '*.sw[po]' -o -name '*.py[co]' -delete
	@find . -name '__pycache__' -delete
	@rm -rf dist/

test: $(VENV)		# run test
	$(POETRY) run pytest -v -n auto --cov=src/papyrus --no-cov-on-fail

run:				# run in the local environment
	$(POETRY) run papyrus

build: $(VENV)		# build the binary/library
	$(POETRY) build

install: $(VENV)		# install the binary tool into local env
	$(POETRY) install

upgrade:			# upgrade all the necessary packages
	pre-commit autoupdate

help:				# show this message
	@printf "Usage: make [OPTION]\n"
	@printf "\n"
	@perl -nle 'print $$& if m{^[\w-]+:.*?#.*$$}' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?#"} {printf "    %-18s %s\n", $$1, $$2}'

$(SUBDIR):
	$(MAKE) -C $@ $(MAKECMDGOALS)

$(VENV):
	$(PYTHON) -m venv $@
