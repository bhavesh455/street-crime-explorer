PYTHON := $(shell [ -x .venv/bin/python ] && echo .venv/bin/python || echo python3)

all:
	$(PYTHON) src/extract.py
	$(PYTHON) src/transform.py
	$(PYTHON) src/build_dashboard.py

test:
	$(PYTHON) -m pytest tests/ -q
