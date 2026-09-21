.PHONY: install test lint train image smoke
install:
	python -m pip install -e '.[dev]'
train:
	python scripts/train.py
test:
	pytest
lint:
	ruff check src tests scripts && mypy src && lint-imports
image:
	docker build -t saudi-used-car-deal-checker:$$(git rev-parse --short HEAD) .
smoke:
	python -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8000/ready').status)"
