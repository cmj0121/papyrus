SUBDIR :=

.PHONY: all clean test run build release install upgrade help

all: $(SUBDIR) 		# default action
	@[ -f .git/hooks/pre-commit ] || pre-commit install --install-hooks
	@git config commit.template .git-commit-template

clean: $(SUBDIR)	# clean-up environment
	@find . -name '*.sw[po]' -delete
	cargo clean

test: $(VENV)		# run test
	cargo test

run:				# run in the local environment
	cargo run

build: 				# build the binary/library
	cargo build --all-features --all-targets

release: 			# build the release binary/library
	cargo build --release --all-features --all-targets

install: 			# install the binary tool into local env
	cargo install

upgrade:			# upgrade all the necessary packages
	pre-commit autoupdate

help:			# show this message
	@printf "Usage: make [OPTION]\n"
	@printf "\n"
	@perl -nle 'print $$& if m{^[\w-]+:.*?#.*$$}' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?#"} {printf "    %-18s %s\n", $$1, $$2}'
