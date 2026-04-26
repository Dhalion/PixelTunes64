.PHONY: help install install-system-deps install-python-deps install-matrix-python-deps install-matrix-runtime-permissions install-rpi-deps run test

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
VENV_PYTHON := .venv/bin/python

help:
	@printf '%s\n' \
		'Targets:' \
		'  make install               Install system tools and project deps' \
		'  make install-python-deps   Install the project in .venv' \
		'  make install-system-deps   Install build prerequisites for apt or dnf' \
		'  make install-rpi-deps      Alias for install' \
		'  make install-matrix-runtime-permissions  Allow matrix access without sudo' \
		'  make run                   Start PixelTunes64' \
		'  make test                  Run the test suite'

install: install-system-deps install-python-deps

install-system-deps:
	@set -e; \
	if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update; \
		sudo apt-get install -y build-essential git pkg-config python3-dev python3-venv libjpeg-dev libcap2-bin; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf install -y gcc gcc-c++ make git pkgconf python3-devel libjpeg-turbo-devel libcap; \
	else \
		printf '%s\n' "Unsupported package manager. Install build tools, git, pkg-config, Python headers, and JPEG headers manually." >&2; \
		exit 1; \
	fi

install-python-deps:
	@test -x .venv/bin/python || $(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e .

install-matrix-python-deps: install

install-matrix-runtime-permissions:
	@set -e; \
	if [ ! -x "$(VENV_PYTHON)" ]; then \
		printf '%s\n' "Missing .venv. Run 'make install' first." >&2; \
		exit 1; \
	fi; \
	python_bin="$$(readlink -f "$(VENV_PYTHON)")"; \
	sudo setcap 'cap_sys_nice=eip' "$$python_bin"; \
	printf '%s\n' "Granted cap_sys_nice to $$python_bin"; \
	command -v getcap >/dev/null 2>&1 && getcap "$$python_bin" || true

install-rpi-deps: install

run:
	$(VENV_PYTHON) -m pixeltunes64.cli

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
