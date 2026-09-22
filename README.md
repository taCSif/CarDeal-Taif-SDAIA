# CarDeal — Saudi Used Car Deal Checker

[![CI](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/workflows/ci.yml)

A production-style ML service that estimates a used car's historical Saudi listing price, then applies a deterministic policy to compare that estimate with the seller's asking price.

> **Know the price. Spot the deal.**

## Documentation

- [docs/SUBMISSION.md](docs/SUBMISSION.md) — Full detailed submission document
- [docs/DEMO_REPORT.html](docs/DEMO_REPORT.html) — Demo report (screenshots + explanations)
- [docs/LEARNING_OUTCOMES.md](docs/LEARNING_OUTCOMES.md) — How the project meets the program objectives

## How this project meets the program objectives

This project applies the program's goal of moving from *model building* to *production AI software engineering*:

| Program objective | Implementation |
|---|---|
| Clean API around the model (FastAPI) | `POST /v1/predict`, `GET /v1/comparables`, `/health`, `/ready`; unified response/error envelope with a `trace_id`; strict Pydantic validation (`extra="forbid"`, value ranges). |
| Containerisation (Docker) | Multi-stage Dockerfile, non-root user, `/ready` healthcheck, 418 MB image (≤500 MB), `docker-compose` with PostgreSQL gated on `service_healthy`. |
| Automated tests & CI/CD (GitHub Actions) | quality → tests + coverage gate → Docker build + smoke → publish to GHCR (main only, tagged by commit SHA, no `:latest`); branch protection on `main`. |
| Clean Architecture & config management | `domain/service/adapters/api` layers; model behind a `Protocol` with dependency injection; `import-linter` enforces the layering; typed Pydantic `Settings` that fail fast. |
| Code-quality tooling (review, linters, static analysis) | `ruff`, `mypy --strict`, `import-linter`, and `gitleaks` secret scanning, all gating merges via required CI checks. |
| Containerised model-serving project | End-to-end: training pipeline, FastAPI service, Docker image, CI/CD, and full documentation. |

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

The cleaned CSV is committed at `data/raw/saudi_used_cars.csv` (~660 KB, public data), so `python scripts/train.py` and CI both read it directly with no download step and no credentials. To refresh it from Kaggle instead — the Kaggle download API requires authentication even for public datasets — set `KAGGLE_USERNAME` and `KAGGLE_KEY` and run:

```bash
bash scripts/fetch_dataset.sh   # overwrites data/raw/saudi_used_cars.csv
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

### `GET /v1/comparables`

Training saves cleaned historical listings as `artifacts/comparable_cars.csv`. This reuses the same repository `POST /v1/predict` uses internally (its `comparable_cars` field is unchanged), exposed as its own endpoint for a caller that wants comparables without supplying an asking price. Same `make_model`/`year`/`mileage` validation as predict (`extra="forbid"`, same ranges, same whitespace normalization), passed as query parameters:

```bash
curl "http://localhost:8000/v1/comparables?make_model=Toyota%20Camry&year=2021&mileage=80000"
```

```json
{
  "trace_id": "...",
  "data": {
    "comparable_cars": [
      {"make_model": "Toyota Camry", "year": 2021, "mileage": 78000, "price": 76000}
    ]
  }
}
```

Returns up to five nearby historical listings by make/model, year, and mileage similarity — **not live marketplace results**. An unknown query parameter, an out-of-range value, or a request before the model is ready get the same `VALIDATION_ERROR` / `NOT_READY` envelopes as `POST /v1/predict`. See `DECISIONS.md` #11.

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
- real-model behavioral tests, including explicit invariance/directional checks (`tests/test_behavioural_model.py`)
- intentional golden-reference test
- adapter/comparable repository tests
- `GET /v1/comparables` unit (schema) and integration (TestClient) tests

The real-model gate is marked `real_model` and requires a trained artifact; `make fast-test` excludes it so the fast gate stays fast, `make test` and CI's `docker` job run it. The behavioral suite checks policy directionality, model input stability, and (`tests/test_behavioural_model.py`) that an unknown make/model never prices above the training max. One invariant — mileage monotonicity — does **not** hold for the real trained model; it is kept as a documented `xfail`, not hidden. See `docs/model_limitations.md`. Golden values are never silently regenerated.

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

No `latest` tag is published. The `docker` and `publish` jobs train from the committed `data/raw/saudi_used_cars.csv` and need no repository secrets to run.

Current CI evidence (run URL, commit SHA, GHCR image link, per-job status) is recorded in `docs/ci_evidence.md` after every audited push, rather than only claimed here.

### Branch protection

`main` is protected via `gh api repos/taCSif/CarDeal-Taif-SDAIA/branches/main/protection`:

- Required status checks before merge: `quality`, `docker`, `publish` (strict — must be up to date with `main`).
- Non-admin changes must go through a pull request (`required_pull_request_reviews` is set).
- Force pushes and branch deletion are disabled.

**`required_approving_review_count` is `0` and `enforce_admins` is off, deliberately.** This is a solo-maintainer repository with no second collaborator; GitHub does not count a PR author's own approval, so a "1 approving review" rule would be permanently unsatisfiable for this account and would only ever get bypassed by an admin — which is worse than an honestly-lower number. `enforce_admins: false` lets the owner still push directly (as this audit's own commits did) instead of silently disabling protection to work around it. Adding a second maintainer and setting `required_approving_review_count: 1` plus `enforce_admins: true` is the natural next step and is one `gh api -X PUT` call away; the exact JSON body used is in this repo's commit history (`git log -p -- scripts/verify_protection.sh` and the audit's commits).

Verify the current state at any time:

```bash
bash scripts/verify_protection.sh   # exits non-zero and prints the gap if protection is missing/weaker than expected
```

## Security / configuration

Configuration is typed with Pydantic Settings and unknown environment variables fail fast. Secrets are not stored in source code. Logs are structured JSON and correlate requests with `X-Trace-ID`; they do not log the vehicle payload.

## Benchmarks

`BENCHMARKS.md` contains only measurements actually observed in the current environment or CI, produced by `scripts/bench.sh` (image size, top Docker layers, `make fast-test` / `make test` timing). Unmeasured or environment-limited numbers are explicitly marked as such rather than fabricated.

## Engineering decisions

See `DECISIONS.md` for the 12 decisions covering the regression/policy split, four-input UX contract, model boundary, lifecycle, data quality, persistence, comparables (embedded and as `GET /v1/comparables`), golden references, and the documented model limitation.

## Acknowledgements

This project was completed as part of the SDA-AIE-113 — Software Engineering Practices for AI Systems training program at SDAIA Academy, under the supervision of Abdullah Khalid AlShahrani.

The portfolio demonstrates the practical application of software engineering practices for AI systems — building a production-style AI/ML service through clean architecture, a well-defined API contract, containerization, a layered automated testing suite, a CI/CD pipeline with branch protection, and safe configuration, secrets, and logging management.

Official SDAIA Academy GitHub: https://github.com/SDAIAAcademy
