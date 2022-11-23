.PHONY: test help fmt install-editable lint install

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: $(VENV)/init ## run pytest
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO

lint: $(VENV)/init ## run flake8 to check the code
	. $(VENV)/bin/activate && flake8 pytest_arch tests

install-editable: $(VENV)/init
	. $(VENV)/bin/activate && $(PIP) install -e '.[dev]'

install: $(VENV)/init
	. $(VENV)/bin/activate && $(PIP) install '.[dev]'

fmt: $(VENV)/init ## run black to format the code
	. $(VENV)/bin/activate && black pytest_arch tests

fmt-check: $(VENV)/init ## run black to format the code
	. $(VENV)/bin/activate && black --check pytest_arch tests

$(VENV)/init: ## init the virtual environment
	python -m venv $(VENV)
	touch $@
