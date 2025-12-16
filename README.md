# Python repository template

[![Coverage Status](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/fannijako/repo_template)

## Project Overview

Repository template for my Python projects

## Dependencies

- python package 1
- python package 2

## Installation

1. Create a virtual environment:
```bash
make venv
```

2. Install the package with build dependencies:
```bash
make build
```

3. Install test dependencies:
```bash
make build-test
```

4. Run tests:
```bash
make test
```

5. Run linter:
```bash
make lint
```

## Usage

Create a .env file with the following variables:

```bash
KEY_NAME=key_value
```

```bash
make venv
source .venv/bin/activate
make build
make run
```
