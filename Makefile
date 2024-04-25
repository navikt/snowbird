ifeq ($(OS),Windows_NT)
	BIN = Scripts
else
	BIN = bin
endif

VENV = .venv
PY =$(VENV)/$(BIN)/python -m

.PHONY: install ## install requirements in virtual env
install:
	rm -rf .venv
	python3.11 -m venv .venv && \
		${PY} pip install --upgrade pip && \
		${PY} pip install .[dev]
