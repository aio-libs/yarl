all: test


.install-deps: $(shell find requirements -type f)
	@pip install -U -r requirements/dev.txt
	@touch .install-deps


.develop: .install-deps $(shell find yarl -type f)
	@pip install -e .
	@touch .develop


flake: .develop
	flake8 yarl tests setup.py


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
