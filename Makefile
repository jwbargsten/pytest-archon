.PHONY: test help fmt install-editable lint install

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

test: $(VENV)/init ## run pytest
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO

cov: $(VENV)/init ## run pytest
	. $(VENV)/bin/activate && coverage run --source=pytest_archon --module pytest && coverage report

lint: $(VENV)/init ## run flake8 to check the code
	. $(VENV)/bin/activate && flake8 pytest_archon tests && mypy -m pytest_archon

install-editable: $(VENV)/init
	. $(VENV)/bin/activate && $(PIP) install -e '.[dev]'

install: $(VENV)/init
	. $(VENV)/bin/activate && $(PIP) install '.[dev]'

fmt: $(VENV)/init ## run black to format the code
	. $(VENV)/bin/activate && black pytest_archon tests

fmt-check: $(VENV)/init ## run black to format the code
	. $(VENV)/bin/activate && black --check pytest_archon tests

clean:
	rm -rf dist/ build/ *.egg-info

build: clean $(VENV)/init ## build the pkg
	$(PY) -m build

publish-test: build
	$(PY) -m twine upload --repository testpypi dist/*

publish: build
	. $(VENV)/bin/activate && check-manifest
	. $(VENV)/bin/activate && check-wheel-contents
	. $(VENV)/bin/activate && pyroma .
	$(PY) -m twine check dist/*
	$(PY) -m twine upload dist/*

test-install:
	$(PIP) install --index-url https://test.pypi.org/simple/ --no-deps pytest-archon-jwb

$(VENV)/init: pyproject.toml Makefile ## init the virtual environment
	python -m venv $(VENV)
	$(PIP) install --upgrade build twine
	touch $@
