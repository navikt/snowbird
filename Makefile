SHELL = /bin/bash
.DEFAULT_GOAL = install

PY = ./.venv/bin/python

.PHONY: install ## install requirements in virtual env
install:
	rm -rf .venv
	python3.11 -m venv .venv && \
		${PY} -m pip install --upgrade pip && \
		${PY} -m pip install -e .[dev]

.PHONY: docs ## generate documentation
docs:
	${PY} generate_doc.py

.PHONE: release ## publish new release
release:
	./release.sh
