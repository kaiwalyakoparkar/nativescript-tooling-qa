#!/usr/bin/env bash

# Run unit tests
python -m nose core_tests/unit

# Run pylint
python -m flake8 --max-line-length=120 core core_tests data products tests
python -m pylint --disable=locally-disabled --rcfile=.pylintrc core data products
find core_tests | grep .py | grep -v .pyc | xargs python -m pylint --disable=locally-disabled --rcfile=.pylintrc
find tests | grep .py | grep -v .pyc | xargs python -m pylint --disable=locally-disabled --min-similarity-lines=15 --rcfile=.pylintrc
