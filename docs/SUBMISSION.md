# CarDeal — Saudi Used Car Deal Checker
### Capstone Submission Document (Track B) — Detailed

**Author:** Taif Al-Sufyani
**Repository:** https://github.com/taCSif/CarDeal-Taif-SDAIA
**CI status:** green on `main` — three jobs: `quality` → `docker` → `publish`
**Container image:** published to GitHub Container Registry (GHCR), tagged by commit SHA
**Slogan:** *Know the price. Spot the deal.*

This document is a complete, self-contained explanation of the project. It is written so that
an engineer who has never seen the repository can understand **what the system does, how every
part is engineered, why each decision was made, how it satisfies the program's objectives, how
to run it, what it measures, and where its honest limits are** — without a live walkthrough.

---

## 1. Problem, product, and the core design idea

### 1.1 The problem
Someone looking at a used-car listing in Saudi Arabia asks a simple question: **"Is this asking
price reasonable, or too high?"** Answering it requires two very different things: an estimate of
what the car is *worth*, and a *judgement* about the asking price relative to that estimate.

### 1.2 The product
CarDeal takes **four inputs** — Make & Model, Year, Mileage, and Asking Price — and returns an
estimated historical price, the difference from the asking price, and a **deal decision**:
`GOOD_DEAL`, `REVIEW`, or `POOR_DEAL`.

### 1.3 The core design idea — two separate responsibilities
The system is deliberately split into two independent parts:

```
  Vehicle details                      Asking price
 (Make&Model, Year, Mileage)                │
          │                                 │
          ▼                                 ▼
   ┌───────────────┐              ┌──────────────────────┐
   │   ML model    │ ─ estimate ─▶│ Deterministic policy │ ─▶ Decision
   │ (regression)  │              │  (fixed thresholds)  │   GOOD/REVIEW/POOR
   └───────────────┘              └──────────────────────┘
```

- The **ML model** only *estimates a price*. It has no idea what a "good deal" is.
- The **deterministic policy** takes that estimate and the asking price and *classifies the
  deal* using fixed, auditable rules.

**Why separate them?** If we instead trained a classifier to output GOOD/REVIEW/POOR directly,
we would have to invent those labels from the price first — so the classifier would just be
re-learning our own policy in a black box (circular reasoning). Keeping the regression and the
policy apart means the pricing model and the business rules can each be understood, tested, and
changed on their own. This is recorded as decision #1 in `DECISIONS.md`.

---

## 2. Track B — how the project satisfies the idea criteria

| Track B criterion | How CarDeal satisfies it |
|---|---|
| Instructor approved beforehand | The idea was approved by the instructor before building started. |
| A clear decision between 2–3 options | Exactly three outcomes: `GOOD_DEAL` / `REVIEW` / `POOR_DEAL` — not open-ended text generation. |
| Tabular or short-text data only | Tabular CSV (`Make, Type, Year, Mileage, Price, …`), 8,035 rows. |
| A lightweight model is enough | `HistGradientBoostingRegressor` from scikit-learn — no deep learning. |
| At least one deterministic behavioural test | e.g. "raising the asking price can never improve the decision" — asserted in `tests/test_behavior.py::test_directional_behavior`. |

---

## 3. How this project meets the program's objectives (in detail)

The program's stated goal is to move participants **from model builders to software engineers for
production AI systems** — designing clean APIs around models with FastAPI, containerising with
Docker, automating tests and CI/CD with GitHub Actions, organising code under Clean Architecture
with configuration management, and assessing code quality with reviews, linters, and static
analysis. Below, each objective is mapped to concrete implementation and the competency it proves.

### 3.1 A clean API around the model (FastAPI)
- Endpoints: `POST /v1/predict`, `GET /v1/comparables`, `GET /health`, `GET /ready`.
- Every response — success or error — uses **one envelope shape** carrying a `trace_id`, so
  clients and logs can correlate a single request end to end.
- Requests are validated by **Pydantic** models with `extra="forbid"` (unknown fields rejected)
  and explicit value ranges.
- **Competency:** the API is treated as the product and the stable contract; the model is an
  internal detail hidden behind it.

### 3.2 Containerisation (Docker)
- A **multi-stage** `Dockerfile`: a build stage installs dependencies, a slim runtime stage
  copies only what is needed.
- Runs as a **non-root** user (uid 10001) for security.
- A container **healthcheck** targets `/ready`, so the orchestrator knows when the service can
  actually serve predictions, not just when the process is alive.
- Final image size **418 MB** — under the 500 MB target.
- **Competency:** shipping a lean, secure, health-aware artifact that behaves identically on any
  machine.

### 3.3 Automated testing & CI/CD (GitHub Actions)
- The pipeline runs on every push and pull request: **quality → docker → publish**.
- It lints, type-checks, checks architecture, scans for secrets, runs the tests with an **80%
  coverage gate**, trains the model, runs the real-model and golden tests, builds the image,
  smoke-tests a running container, enforces the **≤ 500 MB** size gate, and finally publishes the
  image to GHCR — **only on `main`**, tagged by **commit SHA** (never `:latest`).
- **Competency:** replacing "it works on my machine" with an automated, reproducible release
  pipeline where nothing merges or ships unproven.

### 3.4 Clean Architecture & configuration management
- Four layers — `domain`, `service`, `adapters`, `api` — with dependencies pointing **inward**.
- The model is accessed through a **`Protocol`** (an interface) and injected into the service
  (dependency injection), so the concrete sklearn model can be replaced without touching the
  use case.
- **`import-linter`** enforces the layering automatically as a CI check.
- Configuration is a typed Pydantic **`Settings`** object with `extra="forbid"` that **fails fast**
  on any unknown or malformed setting.
- **Competency:** business logic that is independent of frameworks and infrastructure, and
  therefore maintainable and testable.

### 3.5 Code quality (review, linters, static analysis)
- **`ruff`** (linting), **`mypy --strict`** (type checking), **`import-linter`** (architecture),
  and **`gitleaks`** (secret scanning) all run in CI and **gate merges** on a protected `main`.
- **Competency:** quality enforced automatically, not left to manual discipline.

### 3.6 The transformation, in one line
"Done" no longer means a notebook with a good metric — it means a **service**: a clean API, a
container, a green pipeline, enforced architecture, scanned secrets, and honest documentation.
Full write-up: [`docs/LEARNING_OUTCOMES.md`](LEARNING_OUTCOMES.md).

---

## 4. Architecture in detail (Clean Architecture)

```
src/
├── domain/          PURE business rules — no framework, no I/O
│   ├── models.py    Vehicle, Decision (enum), DealAssessment
│   ├── rules.py     premium_ratio(), the 0.05 / 0.15 thresholds
│   └── decisions.py assess_deal(): estimate + asking → DealAssessment
├── service/
│   └── predict.py   PredictService + the PriceModel / repository Protocols (DI)
├── adapters/
│   ├── model.py     SklearnPriceModel: loads the .joblib, predicts, warms up
│   ├── repository.py comparable-cars lookup + minimal PostgreSQL audit
│   └── settings.py  typed Pydantic Settings (fail-fast configuration)
└── api/
    ├── routes.py    FastAPI app factory, lifespan, endpoints, DI wiring
    ├── schemas.py   Pydantic request/response models (extra="forbid", ranges)
    ├── middleware.py trace-id middleware + structured JSON logging
    ├── errors.py    unified error envelopes
    └── static/index.html  the four-input web UI
```

**The dependency rule:** inner layers never import outer layers. The `domain` package imports no
FastAPI, no pandas, no sklearn — nothing but standard Python. The `service` depends only on
abstractions (`Protocol`s), not on the concrete model. Two `import-linter` contracts enforce this
on every CI run:
- *Domain has no outer-layer dependencies* — KEPT.
- *Service stays independent of adapters and API* — KEPT.

**Why it matters:** the pricing model is a plug-in. Swapping `HistGradientBoostingRegressor` for
XGBoost, or even a rule-based estimator, requires changing only `adapters/model.py` — the domain,
service, and API are untouched.

---

## 5. The dataset

- Source: the **Saudi Arabia Used Cars Dataset** (Kaggle / Syarah), collected in **2021**.
- The cleaned English file (`UsedCarsSA_Clean_EN.csv`) has **8,035 rows** with columns including
  `Make, Type, Year, Origin, Color, Options, Engine_Size, Fuel_Type, Gear_Type, Mileage, Region,
  Price, Negotiable`.
- It is committed at `data/raw/saudi_used_cars.csv` (~660 KB, public data) so training and CI need
  no download and no credentials. A `scripts/fetch_dataset.sh` helper can refresh it from Kaggle
  (which requires `KAGGLE_USERNAME` / `KAGGLE_KEY`).
- **Honesty note:** because the data is from 2021, every prediction is an **estimated historical
  price**, not a live-market valuation — stated in the UI and the README.

---

## 6. The model — training pipeline, step by step

`scripts/train.py` performs the full pipeline:

**Step 1 — Load.** Read the CSV (8,035 rows) and verify the required columns exist.

**Step 2 — Clean (data-quality rules).**
- Convert `Year`, `Mileage`, `Price` to numbers; drop rows where any required field is missing.
- Keep only `Price ≥ 5,000` (a `Price = 0` "negotiable" row is not a valid regression target).
- Keep only `Mileage ≤ 700,000` (remove impossible/extreme records).
- Keep a documented `Year` range; require non-empty `Make` and `Type`.
- Build the single categorical feature `Make_Model = Make + " " + Type` (e.g. "Hyundai Elantra").
- Result: **5,385 clean rows**.

**Step 3 — Split.** 80% train (4,308) / 20% held-out test (1,077), with a fixed random seed
`42` so the split — and therefore the metrics and the model — are **reproducible**.

**Step 4 — Train.** A scikit-learn `Pipeline`:
- `OneHotEncoder(handle_unknown="ignore")` on `Make_Model` (an unseen model degrades gracefully
  instead of crashing).
- `Year` and `Mileage` passed through as numeric features.
- A **`HistGradientBoostingRegressor`** predicts `Price`.

**How the model works (plain explanation):** gradient boosting builds many small decision trees
**one after another**; each new tree is trained to correct the *error left by the previous trees*.
The final prediction is the sum of all their corrections, so accuracy improves gradually. The
"Hist" variant bins continuous values into histograms for speed on larger datasets. It is a
lightweight model — exactly what the brief allows — and needs **no deep learning**.

**Step 5 — Evaluate & save.** Predict on the held-out test set, compute the metrics, and save:
`price_model.joblib` (the trained model), `metrics.json`, `model_metadata.json`, and
`comparable_cars.csv` (the cleaned listings used by the comparables feature).

### 6.1 Measured metrics (seed 42)

| Metric | Value | Meaning |
|---|---:|---|
| Source rows | 8,035 | raw dataset |
| Rows after cleaning | 5,385 | valid regression rows |
| Train / test rows | 4,308 / 1,077 | 80 / 20 split |
| **MAE** | **21,154 SAR** | average absolute error of the estimate |
| **RMSE** | **39,622 SAR** | error that penalises large misses more |
| **R²** | **0.69** | the model explains ~69% of price variance |

These are honest numbers for a deliberately small three-feature model on a heterogeneous national
dataset. Richer features would improve accuracy but were excluded by the four-input product
decision (`DECISIONS.md` #2).

---

## 7. The deal policy (deterministic)

Given the model's `estimated_price` and the user's `asking_price`:

```
premium = (asking_price − estimated_price) / estimated_price

premium ≤ 0.05           → GOOD_DEAL
0.05 < premium ≤ 0.15    → REVIEW
premium > 0.15           → POOR_DEAL
```

- A **negative** premium means the asking price is *below* the estimate → a good deal.
- The boundaries are inclusive on the lower band and tested precisely: exactly 5%, just above 5%,
  exactly 15%, just above 15%, asking below estimate, and asking equal to estimate.
- The thresholds are **application policy constants**, not claims about the real market.

**Worked example.** Toyota Camry, 2021, 80,000 km, asking 85,000 SAR:
- estimate ≈ 75,262 SAR
- difference = 85,000 − 75,262 = +9,738 SAR
- premium = 9,738 / 75,262 = +12.9% → within (0.05, 0.15] → **REVIEW**.

---

## 8. Service interface & lifecycle (in detail)

### 8.1 Endpoints
- **`POST /v1/predict`** — accepts the four inputs, returns the estimate, difference, decision,
  and comparables inside the envelope.
- **`GET /v1/comparables`** — the extension; returns up to five similar historical listings for a
  vehicle (same validation as predict), without needing an asking price.
- **`GET /health`** — liveness only: is the process up?
- **`GET /ready`** — real readiness: returns 200 **only after** the model artifact is loaded and
  warmed. A missing or corrupt artifact leaves the app alive but *not ready*.

### 8.2 Request / response contract

Request:
```json
{ "make_model": "Toyota Camry", "year": 2021, "mileage": 80000, "asking_price": 85000 }
```

Success response (unified envelope):
```json
{
  "trace_id": "…",
  "data": {
    "estimated_price": 75261.84,
    "asking_price": 85000,
    "difference_amount": 9738.16,
    "difference_percentage": 12.94,
    "decision": "REVIEW",
    "comparable_cars": [ … up to five … ]
  }
}
```

Error response (same shape):
```json
{ "trace_id": "…", "data": { "error": "VALIDATION_ERROR", "details": [ … ] } }
```

### 8.3 Lifecycle
Model loading happens **once, at application startup** via FastAPI's `lifespan` — **never** at
import time and **never** on the first request. The sequence is: startup → load model → warm it up
(one throwaway prediction) → initialise dependencies → mark `ready = true`. If startup fails,
`ready` stays `false` and the service honestly reports that it cannot serve predictions.

### 8.4 Validation (authoritative in the backend)
The browser validates for convenience, but the backend is the real boundary:
- Unknown fields → rejected (`extra="forbid"`).
- `make_model` must contain at least two tokens (make + model); internal whitespace is collapsed.
- `year`: 1950–2026 · `mileage`: 0–2,000,000 km · `asking_price`: > 0 and ≤ 10,000,000 SAR.
- Wrong types, missing fields, and out-of-range values are all rejected with a `422` and a
  `VALIDATION_ERROR` envelope that still carries the `trace_id`.

### 8.5 Trace ID
Every request gets a trace id: if the client sends `X-Trace-ID` it is preserved, otherwise one is
generated. It appears in the **response body**, the **`X-Trace-ID` response header**, and the
**logs** — so one request can be followed everywhere.

---

## 9. Containerisation (in detail)

- **Multi-stage build:** a builder stage creates a virtual environment and installs the package;
  the runtime stage (`python:3.11-slim`) copies only that environment plus the source and the
  trained artifacts.
- **Non-root:** a dedicated `appuser` (uid 10001) owns and runs the app.
- **Healthcheck:** the image's `HEALTHCHECK` polls `/ready`.
- **Size:** **418 MB** uncompressed layers — under the 500 MB target (the number is real, measured
  with `docker history`; the container store's larger figure double-counts the compressed blob).
- **Compose:** `docker-compose.yml` runs the app together with **PostgreSQL**; the app's startup
  `depends_on` Postgres reporting **`service_healthy`**. On shutdown the container stops cleanly and
  the app resets its readiness state.
- **PostgreSQL audit:** when a database URL is configured, each prediction writes a **minimal**
  audit row — `trace_id`, `model_version`, `estimated_price`, `asking_price`, `decision`,
  `timestamp` — never the full vehicle request.

---

## 10. CI/CD & branch protection (in detail)

**Pipeline (`.github/workflows/ci.yml`):**
```
quality
  ├─ ruff check            (lint)
  ├─ mypy --strict         (type check)
  ├─ import-linter         (architecture contracts)
  ├─ gitleaks              (secret scan)
  └─ pytest (not real_model) + 80% coverage gate
        ↓
docker
  ├─ train the model from the committed dataset
  ├─ run real-model + golden tests
  ├─ build the Docker image
  ├─ start a container and smoke-test /health, /ready, /v1/predict
  └─ enforce the image ≤ 500 MB size gate
        ↓
publish   (only on push to main)
  └─ push the image to GHCR, tagged by commit SHA (never :latest)
```

- **Publish only on `main`, tagged by commit SHA** — every published image is traceable to an exact
  commit, and there is no ambiguous `:latest`.
- **Branch protection on `main`:** required status checks (`quality`, `docker`, `publish`, strict),
  pull request required, force-push and deletion disabled. Because this is a **solo-maintainer**
  account, `required_approving_review_count` is `0` (GitHub does not count a PR author's own
  approval, so a "1 review" rule would be permanently unsatisfiable) — this is documented, not
  silently weakened, and adding a second reviewer is one API call away.
- **Evidence:** `docs/ci_evidence.md` records the latest run URL, commit SHA, GHCR image link, and
  per-job status; a badge in the README shows live status.

---

## 11. Testing — the pyramid (in detail)

- **Unit tests** — the pure domain: `assess_deal` boundaries (5% / 15% edges, equal, below), and
  service orchestration with a fake model.
- **Integration tests** — the API through FastAPI's `TestClient`: `/health`, `/ready`, a valid
  prediction, unknown-field rejection, out-of-range rejection, the trace-id round-trip, the unified
  envelope, and the served UI route.
- **Behavioural tests against the real trained model** (marked `real_model`):
  - **Directional:** raising only the asking price never improves the decision.
  - **Invariance:** whitespace-equivalent inputs produce the same result; an unknown make/model
    never prices above the training maximum.
  - **Golden reference:** the real model's predictions for reviewed example cars match committed
    golden values within a tight tolerance — and the golden file is **never** silently regenerated.
- **Coverage:** **92%+ branch coverage** on the core layers, enforced by an 80% gate.
- **Fast gate:** the non-real-model suite finishes in seconds in CI, so quick feedback stays quick;
  `make test` and CI's `docker` job run the full suite including the real-model gate.

---

## 12. Configuration, secrets & logging (in detail)

- **Configuration:** a typed Pydantic `Settings` class with `env_prefix="DEAL_CHECKER_"` and
  `extra="forbid"`. Unknown environment variables or bad types fail fast and clearly at startup.
- **Secrets:** none are stored in code or git history — verified by running **`gitleaks`** over the
  full commit history (no leaks). All configuration is centralised in `adapters/settings.py`.
- **Logging:** structured **JSON** logs (timestamp, level, message, `trace_id`). Only request
  metadata (path, status, duration) is logged — the vehicle payload is **never** written to logs,
  avoiding unnecessary data retention.

---

## 13. The extension — `GET /v1/comparables`

Training saves cleaned historical listings to `artifacts/comparable_cars.csv`. The comparables
capability already exists *inside* `/v1/predict`; the extension promotes it to its **own endpoint**
so a caller can fetch similar historical cars **without** supplying an asking price. It reuses the
same repository and the same validation (`extra="forbid"`, ranges, whitespace normalisation), passed
as query parameters, and returns up to five nearest listings by make/model, year, and mileage
similarity. These are historical records, **not live marketplace results**. It has its own unit and
integration tests. See `DECISIONS.md` #11.

---

## 14. Honest limitations & future work

**Limitations (documented in `docs/model_limitations.md`, not hidden):**
1. **Only three features** → a large error band (MAE ≈ 21k SAR); the model can overestimate models
   with few examples (e.g. some Elantra configurations) due to overfitting on sparse categories.
2. **Not monotonic in mileage** → occasionally a higher mileage yields a higher estimate, which is
   unrealistic. This is kept as an explicit `xfail` test so it is visible and cannot be silently
   "fixed" without review.
3. **2021 historical data** → estimates are historical, not current-market valuations.

**Future work:**
- Add features (engine size, options, region) and stronger regularisation to reduce the error and
  the overfitting.
- Retrain with a monotonic constraint on mileage (`monotonic_cst`) and regenerate the golden
  references with written justification, turning the documented `xfail` into a passing invariant.
- Add a "suspiciously low price" risk signal for prices far below the estimate — an extra
  deterministic flag beyond the three deal bands.
- Replace the 2021 dataset with a live market feed for up-to-date valuations.
- Add a second maintainer and require one approving review on `main`.

---

## 15. Deliverables checklist

| Deliverable | Status | Where |
|---|---|---|
| GitHub repository, clean history (5+ commits) | ✅ | repo `git log` |
| Green CI on `main` + image on GHCR | ✅ | Actions tab, GHCR |
| README runbook (a stranger can run it in 10 min) | ✅ | `README.md` |
| BENCHMARKS with real measurements | ✅ | `BENCHMARKS.md` |
| DECISIONS (12 documented decisions) | ✅ | `DECISIONS.md` |
| At least one extension, working and tested | ✅ | `GET /v1/comparables` |
| Demo walkthrough | ✅ | `docs/DEMO.md` |
| Learning-outcomes mapping | ✅ | `docs/LEARNING_OUTCOMES.md` |
| Model limitations documented | ✅ | `docs/model_limitations.md` |
| Acceptance matrix | ✅ | `ACCEPTANCE.md` |

**Key links:**
- Repository: https://github.com/taCSif/CarDeal-Taif-SDAIA
- CI runs: https://github.com/taCSif/CarDeal-Taif-SDAIA/actions
- Published image: https://github.com/taCSif/CarDeal-Taif-SDAIA/pkgs/container/cardeal-taif-sdaia
