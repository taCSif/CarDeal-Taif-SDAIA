# CarDeal — Saudi Used Car Deal Checker

A production-style ML service that estimates a used car's historical Saudi listing price, then applies a deterministic policy to compare that estimate with the seller's asking price.

> **Know the price. Spot the deal.**

## User experience

The public UI intentionally asks for only four things:

1. **Make & Model**
2. **Year**
3. **Mileage**
4. **Asking Price**

The browser performs immediate validation, then sends the same contract to `POST /v1/predict`. The browser does **not** contain ML or deal-policy logic.

```text
CarDeal UI → FastAPI → PredictService → PriceModel + Deal Policy → response → UI
```

The model uses the first three inputs. Asking price is evaluated only after the ML estimate is produced.

## Data limitation

The source is the **Saudi Arabia Used Cars Dataset** from Kaggle/Syarah, collected in **2021**. The cleaned English listings file (`UsedCarsSA_Clean_EN.csv`) contains **8,035 rows**; after the data-quality filtering below, **5,385 rows** remain for training. Predictions are **estimated historical market prices based on the 2021 training data**, not guaranteed current-market valuations.

Dataset source: `https://www.kaggle.com/datasets/turkibintalib/saudi-arabia-used-cars-dataset`

The Kaggle download API requires authentication even for public datasets. To fetch it locally or in CI, set `KAGGLE_USERNAME` and `KAGGLE_KEY` (CI reads them from repository secrets) and run:

```bash
bash scripts/fetch_dataset.sh   # writes data/raw/saudi_used_cars.csv
```

## Architecture

```text
src/
├── domain/       pure vehicle + decision rules
├── service/      use-case orchestration + Protocols
├── adapters/     sklearn, repository, settings
└── api/          FastAPI, validation, middleware, UI
```

The domain does not import FastAPI, pandas, sklearn, or infrastructure. The service depends on a `PriceModel` Protocol, so the regression implementation can be replaced without changing the use case.

## ML approach

- Public inputs used by the model: `Make_Model`, `Year`, `Mileage`.
- Target: `Price`.
- `Make_Model` is derived from the dataset's `Make` + `Type` columns.
- Categorical encoding: one-hot with unknown-category handling.
- Numeric features: year and mileage.
- Model: `HistGradientBoostingRegressor`.
- Split: 80/20 held-out test split, seed `42`.
- Metrics: MAE, RMSE, R².
- `Price=0` rows are excluded because they do not represent a known target price.
- Out-of-scope/invalid rows are removed according to the documented data-quality rules.

The API never trains on startup.

### Held-out metrics (measured locally, 2026-09-21, seed 42, sklearn 1.9.1)

| Metric | Value |
|---|---:|
| Rows after cleaning | 5,385 |
| Train / test rows | 4,308 / 1,077 |
| MAE | 21,154.30 SAR |
| RMSE | 39,622.45 SAR |
| R² | 0.6916 |

These reflect a deliberately small three-feature contract (`Make_Model`, `Year`, `Mileage`). R² ≈ 0.69 and a five-figure MAE are honest for this feature set on a heterogeneous national listings dataset; richer vehicle attributes would improve accuracy but were excluded by the four-input product decision (see `DECISIONS.md`). Current values live in `artifacts/metrics.json` after training.

## Deal policy

```text
premium = (asking_price - estimated_price) / estimated_price

premium <= 0.05          → GOOD_DEAL
0.05 < premium <= 0.15   → REVIEW
premium > 0.15            → POOR_DEAL
```

These thresholds are application policy constants, not claims about Saudi market pricing.

## Validation and API contract

The backend is the authoritative validation boundary:

- Pydantic strict request model
- unknown fields rejected with `extra="forbid"`
- make/model must contain at least two tokens
- year: 1950–2026
- mileage: 0–2,000,000 km
- asking price: >0 and ≤10,000,000 SAR
- whitespace normalization
- unified trace-aware error envelopes

### `GET /health`
Liveness only.

### `GET /ready`
Returns `200` only after the model is loaded and warmed. Missing/corrupt artifacts leave the service alive but unready.

### `POST /v1/predict`

```json
{
  "make_model": "Toyota Camry",
  "year": 2021,
  "mileage": 80000,
  "asking_price": 85000
}
```

Successful responses use:

```json
{
  "trace_id": "...",
  "data": {
    "estimated_price": 78000,
    "asking_price": 85000,
    "difference_amount": 7000,
    "difference_percentage": 8.97,
    "decision": "REVIEW",
    "comparable_cars": []
  }
}
```

## Historical comparables

Training saves cleaned historical listings as `artifacts/comparable_cars.csv`. The API can return up to five nearby historical listings using make/model, year, and mileage similarity. These are **not live marketplace results**.

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
```

Place the public CSV at:

```text
data/raw/saudi_used_cars.csv
```

Then:

```bash
make train
make test
make lint
```

Training creates:

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

Review the changed values before committing. CI never regenerates golden references automatically.

## Docker / Compose

```bash
make train
make image
docker compose up --build
```

The image is multi-stage, runs as a non-root user, and uses `/ready` as its healthcheck. Compose gates the API on a healthy PostgreSQL service. PostgreSQL is used only for a minimal prediction audit record when configured; the full vehicle request is not persisted.

## Tests

The test pyramid includes:

- domain decision tests
- service tests
- API integration tests
- validation/trace tests
- UI route smoke test
- real-model behavioral tests
- intentional golden-reference test
- adapter/comparable repository tests

The real-model gate is marked `real_model` and requires a trained artifact. The behavioral suite checks policy directionality and model input stability. Golden values are never silently regenerated.

```bash
make test
make fast-test
python -m pytest -m real_model
```

## CI/CD

GitHub Actions follows:

```text
quality
  ├─ Ruff
  ├─ mypy --strict
  ├─ import-linter
  └─ tests excluding real-model gate
        ↓
train release model from public dataset
        ↓
real-model behavior + golden tests
        ↓
Docker build
        ↓
readiness + API smoke
        ↓
image-size gate <= 500 MB
        ↓
publish to GHCR on main only, tagged by commit SHA
```

No `latest` tag is published. The dataset-download steps require `KAGGLE_USERNAME` and `KAGGLE_KEY` repository secrets; without them the `docker` and `publish` jobs cannot fetch the dataset and will fail fast with a clear error.

## Security / configuration

Configuration is typed with Pydantic Settings and unknown environment variables fail fast. Secrets are not stored in source code. Logs are structured JSON and correlate requests with `X-Trace-ID`; they do not log the vehicle payload.

## Benchmarks

`BENCHMARKS.md` contains only measurements actually observed in the current environment or CI. Unmeasured Docker/model-release numbers are explicitly marked as such rather than fabricated.

## Engineering decisions

See `DECISIONS.md` for the five-plus key decisions covering the regression/policy split, four-input UX contract, model boundary, lifecycle, data quality, persistence, comparables, and golden references.
