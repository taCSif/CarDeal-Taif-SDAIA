# Saudi Used Car Deal Checker

An ML engineering service that estimates an expected used-car price from historical Saudi listings, then applies a deterministic business policy to classify an asking price as `GOOD_DEAL`, `REVIEW`, or `POOR_DEAL`.

## Important data limitation
The source is the **Saudi Arabia Used Cars Dataset** from Kaggle/Syarah. The published dataset contains 8,248 listings and was collected in 2021. Predictions are therefore **estimates based on historical training data**, not guaranteed current Saudi market prices.

## Architecture

```text
API (FastAPI)
   ↓
Service (use-case orchestration)
   ↓
Domain (pure decision rules + models)

Adapters
├── sklearn model artifact
├── comparable-listings repository
├── PostgreSQL audit repository
└── typed settings
```

The domain does not import FastAPI, pandas, sklearn, or infrastructure. The service depends on a `PriceModel` Protocol, so the regression implementation can be replaced without changing the use case.

## ML approach

- Target: `Price`.
- Features: `Make`, `Type`, `Year`, `Origin`, `Color`, `Options`, `Engine_Size`, `Fuel_Type`, `Gear_Type`, `Mileage`, `Region`.
- Categorical features: one-hot encoding with unknown-category handling.
- Numeric features: passed through.
- Model: `HistGradientBoostingRegressor`.
- Split: 80/20 held-out test split, seed `42`.
- Metrics: MAE, RMSE, R².
- `Price=0` rows are excluded because the dataset uses zero to represent negotiable listings rather than a known price.
- Extreme/invalid records are removed according to the documented data-quality rules in `DECISIONS.md`.

Training is a separate command. The API never trains on startup.

## Deal policy

```text
premium = (asking_price - estimated_price) / estimated_price

premium <= 0.05          → GOOD_DEAL
0.05 < premium <= 0.15   → REVIEW
premium > 0.15            → POOR_DEAL
```

The thresholds are engineering/domain policy constants, **not claims about Saudi market pricing**.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Put the Kaggle CSV at:

```text
data/raw/saudi_used_cars.csv
```

Then:

```bash
make train
make test
make lint
```

`make train` creates:

```text
artifacts/price_model.joblib
artifacts/comparable_cars.csv
artifacts/metrics.json
artifacts/model_metadata.json
```

After an intentional model release, generate golden references explicitly:

```bash
python scripts/generate_golden.py
```

Review the file before committing it. Training and CI never regenerate it automatically.

## API

### `GET /health`
Liveness only.

### `GET /ready`
Returns `200` only after the model is loaded and warmed. Returns `503` when the service is not ready.

### `POST /v1/predict`

Example request:

```json
{
  "make": "Toyota",
  "type": "Camry",
  "year": 2021,
  "origin": "Saudi",
  "color": "White",
  "options": "Full",
  "engine_size": 2.5,
  "fuel_type": "Gas",
  "gear_type": "Automatic",
  "mileage": 80000,
  "region": "Riyadh",
  "asking_price": 72000
}
```

Response envelope:

```json
{
  "trace_id": "...",
  "data": {
    "estimated_price": 66000,
    "asking_price": 72000,
    "difference_amount": 6000,
    "difference_percentage": 9.09,
    "decision": "REVIEW",
    "comparable_cars": []
  }
}
```

Unknown fields, invalid mileage/year/price/engine values, and malformed requests are rejected with the same trace-aware envelope.

## Comparable Cars extension

The training pipeline saves the cleaned listings as a local artifact. The service can return up to five similar historical listings using make/type, transmission, year, mileage, engine size, and region similarity. This is an offline historical comparison, not a live marketplace search.

## PostgreSQL integration

Compose runs PostgreSQL as the supporting service. When `DEAL_CHECKER_DATABASE_URL` is configured, the app initializes a minimal `prediction_audit` table and records only trace ID, model version, price outputs, decision, and timestamp. It does not persist the full vehicle request.

## Tests

The suite covers:

- decision thresholds and exact boundaries
- invalid prices
- service/model orchestration
- model adapter load/warm-up/prediction
- API liveness/readiness/prediction
- validation and unknown fields
- trace ID propagation
- directional monotonicity as asking price increases
- meaningful metadata invariance
- input whitespace normalization
- comparable-car retrieval
- golden-reference behavior when an intentional golden artifact exists

Run:

```bash
make test
make fast-test
```

Coverage is enforced at 80% branch coverage across core source layers. The current environment's test suite passes with the local test artifact and reports coverage above the gate; real model evaluation still requires the dataset artifact.

## Docker

The image is multi-stage and runs as a non-root user. The container healthcheck targets `/ready`.

```bash
make train
make image
```

The image is intentionally blocked from building before a real model artifact exists; this prevents shipping a container that silently contains no trained model.

## Compose

```bash
docker compose up --build
```

The app waits for PostgreSQL to be healthy, then loads/warm-ups the model and becomes ready.

## CI/CD

GitHub Actions performs:

1. Ruff
2. mypy
3. import-linter
4. pytest + coverage gate
5. public Kaggle dataset download
6. real model training
7. Docker build
8. readiness smoke test
9. image-size gate (`<= 500 MB`)
10. GHCR publish only for pushes to `main`

Published images are tagged with the Git commit SHA. No `latest` tag is published.

## Benchmarks

`BENCHMARKS.md` is updated only with measured values. Model metrics, Docker size, build time, test time, and training time are never fabricated.

## Limitations

- The source data is historical 2021 listing data.
- The service estimates listing price; it is not a professional appraisal.
- Current market changes after collection are not represented.
- Rare vehicle configurations may have limited comparable historical listings.
- Comparable cars are historical records, not live marketplace results.
