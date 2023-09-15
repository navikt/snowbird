ifeq ($(OS),Windows_NT)
	BIN = Scripts
else
	BIN = bin
endif

VENV = .venv
PY =$(VENV)/$(BIN)/python -m 

install:
	python3.10 -m venv .venv && \
		${PY} pip install --upgrade pip && \
		poetry env use ./.venv/bin/python
		poetry install

build:
	rm -r dist
	poetry build
	poetry check
	twine check ./dist/*

test:
	poetry run pytest ./tests