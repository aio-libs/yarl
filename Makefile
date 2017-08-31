MD = $(shell python -c "import multidict; print(multidict.__path__[0])")

all: test


.develop: $(shell find yarl -type f)
	@pip install -e .
	@touch .develop

test: .develop mypy
	pytest ./tests --flake8

vtest: .develop mypy
	pytest ./tests --flake8 -v


cov: .develop mypy
	pytest --cov yarl --cov-report html --cov-report term ./tests/ --flake8
	@echo "open file://`pwd`/htmlcov/index.html"


doc: doctest
	make -C docs html SPHINXOPTS="-W -E"
	@echo "open file://`pwd`/docs/_build/html/index.html"


doctest: .develop
	make -C docs doctest


mypy:
	MYPYPATH=$(MD)/.. mypy yarl
	MYPYPATH=$(MD)/.. mypy --disallow-untyped-defs yarl/*.pyi
