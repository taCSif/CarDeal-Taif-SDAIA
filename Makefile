.PHONY: install train test fast-test lint image smoke benchmark
install:
	python -m pip install -e '.[dev]'
train:
	python scripts/train.py

test:
	python -m pytest
fast-test:
	python -m pytest -m 'not slow' --cov=src/domain --cov=src/service --cov=src/adapters --cov=src/api --cov-branch --cov-report=term-missing --cov-fail-under=80
lint:
	ruff check src tests scripts && mypy src && lint-imports
image:
	@test -f artifacts/price_model.joblib || (echo 'Train the model first: make train' && exit 1)
	docker build -t saudi-used-car-deal-checker:$$(git rev-parse --short HEAD) .
smoke:
	python scripts/smoke.py
benchmark:
	python scripts/benchmark.py
