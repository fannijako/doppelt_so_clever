.PHONY: venv build build-test build-monte-carlo build-interactive build-all lint test run run-auto run-monte-carlo run-interactive clean
PYFILES = $(shell git ls-files '*.py')

venv:
	python -m venv .venv

build:
	pip install --upgrade pip
	pip install setuptools
	pip install -e .[build]

build-test: build
	pip install -e .[test]

build-monte-carlo: build
	pip install -e .[monte-carlo]

build-interactive: build
	pip install -e .[interactive]

build-all: build build-test build-monte-carlo build-interactive

lint:
	pylint $(PYFILES) --disable=R0801,W0511,R0401
	flake8 $(PYFILES) --count --exit-zero --select=E9,F63,F7,F82 --show-source --statistics --exclude=.venv
	flake8 $(PYFILES) --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics --exclude=.venv

test:
	python -m pytest
	python -m pytest --cov=src --cov-report=term-missing

run:
	python main.py

run-auto:
	python main.py --mode automatic

run-monte-carlo:
	python monte_carlo.py -r 1000 --mode automatic

run-interactive:
	python main.py --mode interactive

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info
