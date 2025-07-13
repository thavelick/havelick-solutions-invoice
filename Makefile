# Sane defaults
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

# ---------------------- COMMANDS ---------------------------
generate: # Generate invoice HTML from template (usage: make generate CLIENT=acme-corp DATA=invoice-data-3-31)
	@echo "Generating invoice.."
	uv run python generate_invoice.py one-shot $(CLIENT).json $(DATA).txt
	@echo "Done."

update: # Update dependencies
	@echo "Updating dependencies.."
	uv sync -U

setup: # Setup project
	@echo "Installing dependencies.."
	uv sync
	@echo "Done."

lint: # Run linters (isort, black, pyright, pylint)
	@echo "Running isort import sorter.."
	uv run isort *.py tests/
	@echo "Running black formatter.."
	uv run black *.py tests/
	@echo "Running pyright type checker.."
	uv run pyright
	@echo "Running pylint.."
	uv run pylint --ignore-paths=tests/ --ignore=playwright.config.py *.py

add-dev-dependency: # Add development dependency (usage: make add-dev-dependency DEP=package-name)
	@echo "Adding development dependency: $(DEP)"
	uv add --dev $(DEP)

test-integration: # Run integration tests
	@echo "Running integration tests.."
	uv run pytest tests/integration/

test-unit: # Run unit tests
	@echo "Running unit tests.."
	uv run pytest tests/unit/

test: # Run all tests
	@echo "Running all tests.."
	uv run pytest tests/

test-with-coverage: # Run tests with coverage
	@echo "Running tests with coverage.."
	uv run pytest --cov=. --cov-report=html --cov-report=term tests/

# -----------------------------------------------------------
# CAUTION: If you have a file with the same name as make
# command, you need to add it to .PHONY below, otherwise it
# won't work. E.g. `make run` wouldn't work if you have
# `run` file in pwd.
.PHONY: help

# -----------------------------------------------------------
# -----       (Makefile helpers and decoration)      --------
# -----------------------------------------------------------

.DEFAULT_GOAL := help
# check https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
NC = \033[0m
ERR = \033[31;1m
TAB := '%-20s' # Increase if you have long commands

# tput colors
red := $(shell tput setaf 1)
green := $(shell tput setaf 2)
yellow := $(shell tput setaf 3)
blue := $(shell tput setaf 4)
cyan := $(shell tput setaf 6)
cyan80 := $(shell tput setaf 86)
grey500 := $(shell tput setaf 244)
grey300 := $(shell tput setaf 240)
bold := $(shell tput bold)
underline := $(shell tput smul)
reset := $(shell tput sgr0)

help:
	@printf '\n'
	@printf '    $(underline)Available make commands:$(reset)\n\n'
	@# Print commands with comments
	@grep -E '^([a-zA-Z0-9_-]+\.?)+:.+#.+$$' $(MAKEFILE_LIST) \
		| grep -v '^env-' \
		| grep -v '^arg-' \
		| sed 's/:.*#/: #/g' \
		| awk 'BEGIN {FS = "[: ]+#[ ]+"}; \
		{printf "    make $(bold)$(TAB)$(reset) # %s\n", \
			$$1, $$2}'
	@grep -E '^([a-zA-Z0-9_-]+\.?)+:( +\w+-\w+)*$$' $(MAKEFILE_LIST) \
		| grep -v help \
		| awk 'BEGIN {FS = ":"}; \
		{printf "    make $(bold)$(TAB)$(reset)\n", \
			$$1}' || true
	@echo -e ""