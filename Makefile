.PHONY: venv build build-test build-monte-carlo build-interactive build-rl build-all lint test run run-auto run-monte-carlo run-interactive train-rl pbt-train-rl evaluate-rl clean docker-build docker-run docker-clean
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

build-rl: build
	pip install -e .[rl]

build-all: build build-test build-monte-carlo build-interactive build-rl

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
	python main.py play --mode automatic

run-monte-carlo:
	python main.py monte-carlo -r 1000 --mode automatic

run-interactive:
	python main.py play --mode interactive

train-rl:
	python main.py train

pbt-train-rl:
	python main.py pbt-train

evaluate-rl:
	python main.py evaluate -n 1000 --checkpoint model/pbt_checkpoints/best_agent.pt

clean:
	rm -rf .venv
	rm -rf __pycache__
	rm -rf */__pycache__
	rm -rf .pytest_cache
	rm -rf *.egg-info

docker-build:
	docker build -t doppelt-so-clever-pbt .

docker-run:
	docker run -e ITERATIONS=$(or $(ITERATIONS),5) -e NUM_WORKERS=$(or $(NUM_WORKERS),0) -v $(PWD)/model/pbt_checkpoints:/app/model/pbt_checkpoints -v $(PWD)/runs:/app/runs doppelt-so-clever-pbt

docker-clean:
	docker rmi doppelt-so-clever-pbt
