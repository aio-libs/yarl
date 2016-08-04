flake:
	flake8 yarl tests


test: flake
	py.test ./tests


cov: flake
	py.test --cov yarl --cov-report html ./tests/
	@echo "open file://`pwd`/htmlcov/index.html"
