#!/usr/bin/make
# WARN: gmake syntax
########################################################
# Makefile for eapictl
#
# useful targets:
#	make sdist -- build python source distribution
#	make pep8 -- pep8 checks
#	make pyflakes -- pyflakes checks
#	make check -- manifest checks
#	make coverage -- run test coverage
#	make tests -- run all of the tests
#	make systest -- run system tests only
#	make unittest -- run unit tests only
#	make clean -- clean distutils
#
########################################################
# variable section

NAME = "eapictl"

PYTHON=python
COVERAGE=coverage
SITELIB = $(shell $(PYTHON) -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

VERSION := $(shell cat VERSION)

########################################################

all: clean pep8 pyflakes tests check

pep8:
	-pep8 -r --ignore=E501,E221,W291,W391,E302,E251,E203,W293,E231,E303,E201,E225,E261,E241 eapictl/ test/

pyflakes:
	pyflakes eapictl/ test/

check:
	check-manifest

clean:
	@echo "Cleaning up distutils stuff"
	rm -rf build
	rm -rf dist
	rm -rf MANIFEST
	rm -rf *.egg-info
	@echo "Cleaning up byte compiled python stuff"
	find . -type f -regex ".*\.py[co]$$" -delete

sdist: clean
	$(PYTHON) setup.py sdist

tests: unittest systest

unittest:
	$(PYTHON) -m unittest discover test/unit -v

systest:
	$(PYTHON) -m unittest discover test/sys -v

coverage:
	$(COVERAGE) run -m unittest discover test/unit -v
	$(COVERAGE) report -m

