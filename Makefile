test:
	py.test ./tests --flake8

vtest:
	py.test ./tests --flake8 -v


cov:
	py.test --cov yarl --cov-report html ./tests/ --flake8
	@echo "open file://`pwd`/htmlcov/index.html"
