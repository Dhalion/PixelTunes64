.PHONY: help install install-system-deps install-python-deps install-matrix-python-deps install-rpi-deps run test

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

help:
	@printf '%s\n' \
		'Targets:' \
		'  make install               Install system tools and project deps' \
		'  make install-python-deps   Install the project in .venv' \
		'  make install-system-deps   Install build prerequisites for apt or dnf' \
		'  make install-rpi-deps      Alias for install' \
		'  make run                   Start PixelTunes64' \
		'  make test                  Run the test suite'

install: install-system-deps install-python-deps

install-system-deps:
	@set -e; \
	if command -v apt-get >/dev/null 2>&1; then \
		sudo apt-get update; \
		sudo apt-get install -y build-essential git pkg-config python3-dev python3-venv libjpeg-dev; \
	elif command -v dnf >/dev/null 2>&1; then \
		sudo dnf install -y gcc gcc-c++ make git pkgconf python3-devel libjpeg-turbo-devel; \
	else \
		printf '%s\n' "Unsupported package manager. Install build tools, git, pkg-config, Python headers, and JPEG headers manually." >&2; \
		exit 1; \
	fi

install-python-deps:
	@test -x .venv/bin/python || $(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e .

install-matrix-python-deps: install

install-rpi-deps: install

run:
	.venv/bin/python -m pixeltunes64.cli

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v
