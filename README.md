# Saudi Used Car Deal Checker

An ML engineering project for estimating a Saudi used-car market price from historical Syarah listings, then applying a deterministic business policy to classify an asking price as `GOOD_DEAL`, `REVIEW`, or `POOR_DEAL`.

## Dataset
The project uses the **Saudi Arabia Used Cars Dataset** from Kaggle, sourced from Syarah. It contains about 8,248 listings and was collected in 2021. The model therefore produces an **estimate based on historical training data**, not a guaranteed current Saudi market price.

Place the CSV at `data/raw/saudi_used_cars.csv`. The training script inspects the actual columns and fails if required fields are missing.

## ML approach
Regression: categorical features are one-hot encoded and numeric features are passed through to a `HistGradientBoostingRegressor`. A fixed 80/20 held-out test split with seed 42 is used. Metrics are MAE, RMSE and R². The API never trains at startup; it loads the saved artifact and performs a real warm-up.

Training cleaning removes invalid/missing rows, prices below SAR 5,000, mileage above 700,000, and invalid year/engine values. These thresholds are engineering/data-quality choices and are documented in `DECISIONS.md`.

## Decision policy
`premium = (asking_price - estimated_price) / estimated_price`
- `premium <= 5%` → `GOOD_DEAL`
- `5% < premium <= 15%` → `REVIEW`
- `premium > 15%` → `POOR_DEAL`

These thresholds are domain-policy constants, not claims about the Saudi market.

## Local setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
make train
make test
make lint
uvicorn src.api.routes:create_app --factory --host 0.0.0.0 --port 8000
```

## API
- `GET /health` liveness
- `GET /ready` readiness
- `POST /v1/predict` price estimate + deterministic deal decision

Example request:
```json
{"make":"Toyota","type":"Camry","year":2021,"origin":"Saudi","color":"White","options":"Full","engine_size":2.5,"fuel_type":"Gas","gear_type":"Automatic","mileage":80000,"region":"Riyadh","asking_price":72000}
```

## Architecture
`domain` contains pure business rules. `service` orchestrates the use case and depends on a `PriceModel` Protocol. `adapters` contain sklearn/config/I/O. `api` contains HTTP schemas, lifecycle, middleware and errors.

## Behavioral tests
The suite checks monotonic decision severity as asking price increases and a meaningful input-copy invariance. Golden-reference testing will be added after the first real model artifact is trained; expected values will never be auto-regenerated.

## Docker / Compose / CI
The repository includes a multi-stage Docker design, Compose health gating, and GitHub Actions scaffolding. Exact image size, test/build times and model metrics must be measured in the actual environment after the dataset is supplied; no numbers are fabricated.

## Limitations
- Historical 2021 source data.
- Predictions depend on available listing features and data quality.
- A predicted price is an estimate, not an appraisal or guaranteed current market value.
