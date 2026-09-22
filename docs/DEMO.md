# CarDeal — Demo Walkthrough

> A 5-minute, self-contained walkthrough of the running service. Each step shows
> **what to look at** and **what it proves**, so the project can be understood
> without a live session.

**Repository:** https://github.com/taCSif/CarDeal-Taif-SDAIA
**Green CI:** see the badge on the README and `docs/ci_evidence.md`.

---

## What CarDeal does (30-second overview)

CarDeal estimates a used car's **historical Saudi listing price** from three inputs
(Make & Model, Year, Mileage) using a lightweight ML model, then a **separate
deterministic policy** compares that estimate with the seller's **asking price** and
classifies the deal as **GOOD_DEAL / REVIEW / POOR_DEAL**.

```
Vehicle details → ML model → Estimated price → Deterministic policy → Deal decision
```

The ML model only *estimates a price*. It never decides the deal — that keeps the two
concerns cleanly separated (see `DECISIONS.md` #1).

---

## Step 1 — Run the service with Docker Compose

```bash
docker compose up --build
```

![Compose up — app and postgres healthy](images/01-compose-up.png)

**What it proves:** the service runs as a **container** alongside a supporting
**PostgreSQL** service. The application only becomes *ready* after Postgres reports
healthy (`depends_on: condition: service_healthy`) and the model is loaded and warmed.

Verify liveness and readiness:

```bash
curl http://localhost:8000/health   # {"data":{"status":"ok"}}
curl http://localhost:8000/ready    # {"data":{"status":"ready"}}
```

![/health and /ready both 200](images/02-health-ready.png)

**What it proves:** `/health` (liveness) and `/ready` (real readiness) are **separate**.
`/ready` only returns 200 once the model artifact is loaded — never at import time.

---

## Step 2 — A valid prediction

Open `http://localhost:8000` and enter: **Toyota Camry / 2021 / 80000 / asking 85000**.

![Valid request — REVIEW decision](images/03-valid-request.png)

The API returns a unified envelope with a `trace_id`:

```json
{
  "trace_id": "…",
  "data": {
    "estimated_price": 75261.84,
    "asking_price": 85000,
    "difference_amount": 9738.16,
    "difference_percentage": 12.94,
    "decision": "REVIEW",
    "comparable_cars": [ … ]
  }
}
```

**What it proves:** the ML model produces the **estimate** (≈75,262 SAR), and the
deterministic policy computes the premium and classifies the deal. The policy:

```
premium = (asking − estimate) / estimate
premium ≤ 0.05 → GOOD_DEAL   |   ≤ 0.15 → REVIEW   |   > 0.15 → POOR_DEAL
```

Here premium ≈ +12.9% → **REVIEW**. Raising only the asking price never improves the
decision (GOOD → REVIEW → POOR), which a behavioural test enforces (Step 4).

---

## Step 3 — A malformed request is rejected

Send an unknown field, or an out-of-range year:

```bash
curl -X POST http://localhost:8000/v1/predict -H "Content-Type: application/json" \
  -d '{"make_model":"Toyota Camry","year":1800,"mileage":80000,"asking_price":72000}'
```

![Malformed request — 422 VALIDATION_ERROR](images/04-malformed-request.png)

```json
{ "trace_id": "…", "data": { "error": "VALIDATION_ERROR", "details": [ … ] } }
```

**What it proves:** validation lives in the **backend**, not just the browser. Pydantic
with `extra="forbid"` rejects unknown fields, enforces value ranges (year, mileage,
asking price), and every error still carries a `trace_id`.

---

## Step 4 — One behavioural test

Open `tests/test_behavior.py::test_directional_behavior`:

![Directional behavioural test passing](images/05-behavioural-test.png)

**What it proves:** for the same vehicle, as the asking price rises the decision can only
stay the same or get worse — never improve. The test asserts the decision severity is
non-decreasing across increasing prices. This is a **deterministic behavioural test**
against the real policy (the repo also has real-model directional, invariance, and golden
tests under the `real_model` marker).

---

## Step 5 — The CI/CD story

Open the **Actions** tab — all three jobs are green:

![GitHub Actions — quality, docker, publish all green](images/06-ci-green.png)

**Pipeline:** `quality` (ruff + mypy --strict + import-linter + tests & coverage gate)
→ `docker` (train the model, run real-model & golden tests, build the image, smoke test,
enforce the ≤500 MB size gate) → `publish` (push the image to GHCR, **main only**, tagged
by **commit SHA**, never `:latest`).

The published container image (public):

![GHCR published image](images/07-ghcr-image.png)

**What it proves:** every push to `main` is automatically checked, tested, built, and
published with no manual steps — the core of production ML engineering.

---

## Model metrics (honest numbers)

```bash
python scripts/train.py    # or: cat artifacts/metrics.json
```

![Training metrics](images/08-metrics.png)

| Metric | Value |
|---|---:|
| Rows after cleaning | 5,385 (from 8,035) |
| MAE | 21,154 SAR |
| RMSE | 39,622 SAR |
| R² | 0.69 |

**Honest limitation:** the model uses only three features, so its estimates carry a large
error band (MAE ≈ 21k SAR) and are not monotonic in mileage — both **documented** in
`docs/model_limitations.md`, not hidden. The engineering pipeline, not the model's
accuracy, is the focus of this project.

---

## Summary — what this demo shows

| Requirement | Shown in |
|---|---|
| Runs via Docker Compose with a supporting service | Step 1 |
| Liveness vs real readiness | Step 1 |
| Valid prediction with unified envelope + trace_id | Step 2 |
| Strict backend validation (malformed rejected) | Step 3 |
| A deterministic behavioural test | Step 4 |
| CI/CD pipeline green + image published to GHCR | Step 5 |
| Honest, documented model limitations | Metrics |
