.develop: $(shell find yarl -type f)
	@pip install -e .
	@touch .develop

test: .develop
	pytest ./tests --flake8

vtest: .develop
	pytest ./tests --flake8 -v


cov: .develop
	pytest --cov yarl --cov-report html --cov-report term ./tests/ --flake8
	@echo "open file://`pwd`/htmlcov/index.html"


doc: doctest
	make -C docs html
	@echo "open file://`pwd`/docs/_build/html/index.html"


doctest: .develop
	make -C docs doctest
