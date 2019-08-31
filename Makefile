PYXS = $(wildcard yarl/*.pyx)

all: test


.install-deps: $(shell find requirements -type f)
	@pip install -U -r requirements/dev.txt
	@touch .install-deps


.install-cython: requirements/cython.txt
	pip install -r requirements/cython.txt
	touch .install-cython


yarl/%.c: yarl/%.pyx
	cython -3 -o $@ $< -I yarl


.cythonize: .install-cython $(PYXS:.pyx=.c)


.develop: .install-deps $(shell find yarl -type f) .cythonize
	@pip install -e .
	@touch .develop


flake: .develop
	flake8 yarl tests setup.py
	if python -c "import sys; sys.exit(sys.version_info<(3,6))"; then \
		black --check yarl tests setup.py; \
		mypy yarl tests; \
	fi

fmt:
	black yarl tests setup.py


test: flake
	pytest ./tests ./yarl


vtest: flake
	pytest ./tests ./yarl -v


cov: flake
	pytest --cov yarl --cov-report html --cov-report term ./tests/ ./yarl/
	@echo "open file://`pwd`/htmlcov/index.html"


doc: doctest
	make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"


doctest: .develop
	make -C docs doctest


mypy:
	mypy yarl tests
