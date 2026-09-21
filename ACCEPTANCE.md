# Final Acceptance Matrix

Status legend: **PASS** (verified in this environment), **PARTIAL** (implemented and inspected, but not fully exercised here), **FAIL**, **NOT VERIFIED** (cannot be checked in this environment).

Verified on 2026-09-21 in a Linux container: Python 3.11.15, scikit-learn 1.9.1, pandas 2.3.3, real dataset (`UsedCarsSA_Clean_EN.csv`). Docker daemon and GitHub Actions are unavailable here, which is the only reason any row is not PASS.

| Requirement | Status | Evidence |
|---|---|---|
| 4-input UI | PASS | `src/api/static/index.html` exposes exactly Make&Model, Year, Mileage, Asking Price; `tests/test_api.py::test_ui_is_served` |
| UI → API integration | PASS | UI posts the four-field contract to `POST /v1/predict`; `tests/test_api.py::test_health_and_readiness_and_prediction` exercises that contract end-to-end |
| API validation | PASS | `src/api/schemas.py` (`extra="forbid"`, field validators); `test_api.py` unknown-field, single-token, negative-mileage cases |
| Clean Architecture | PASS | `src/{domain,service,adapters,api}`; import-linter contracts kept |
| Protocol + DI | PASS | `PriceModel`/`ComparableRepository`/`AuditRepository` Protocols in `service/predict.py`; `ServiceDependency` in `api/routes.py` |
| Model lifecycle | PASS | `create_app` lifespan loads+warms model, sets `ready`; `test_api.py::test_validation_and_not_ready_are_unified`, `test_predict_returns_503_when_not_ready` |
| Health/readiness | PASS | `GET /health` liveness, `GET /ready` gated on loaded+warmed model; API tests |
| Unit tests | PASS | `test_decisions.py` (all boundary cases), `test_service.py`, `test_behavior.py` |
| API tests | PASS | `test_api.py` (health, ready, predict, 503, validation, trace, UI) |
| Real-model behavior | PASS | `test_real_model_behavior.py` (directional policy + whitespace-normalization invariance on the trained artifact) |
| Golden tests | PASS | `test_golden.py` vs `tests/golden_predictions.json`, tolerance `rel=1e-6`; reproduced against a freshly trained model |
| Coverage ≥80% core | PASS | 92.57% branch coverage over domain/service/adapters/api |
| Docker | PARTIAL | `Dockerfile` multi-stage, python:3.11-slim, non-root uid 10001, `/ready` healthcheck, factory `CMD` — **not built here** (no Docker daemon) |
| Docker ≤500MB | NOT VERIFIED | No Docker daemon in this environment; CI enforces `test -le 524288000` |
| Compose | PARTIAL | `docker-compose.yml` with app + postgres, postgres healthcheck, `depends_on: condition: service_healthy` — **not run here** |
| PostgreSQL extension | PARTIAL | `PostgresAuditRepository` persists only trace_id/model_version/prices/decision/timestamp; wired via `DEAL_CHECKER_DATABASE_URL` — code inspected, not exercised at runtime |
| Structured logs | PASS | `middleware.py` `JsonFormatter` emits timestamp/level/message/trace_id; no vehicle payload logged |
| Trace ID | PASS | `TraceMiddleware` preserves `X-Trace-ID` or generates one; present in logs, response body, and response header; asserted in `test_api.py` |
| Config/secrets | PASS | `settings.py` typed `BaseSettings`, `extra="forbid"`, `.env` gitignored; no hardcoded secrets |
| Secret scan | PASS | gitleaks 8.18.4 over 8 commits of git history: no leaks (working-tree hits are all inside `.venv`, which is never committed) |
| Ruff | PASS | `ruff check src tests scripts` — all checks passed |
| mypy | PASS | `mypy src` (strict) — no issues in 16 files |
| import-linter | PASS | `lint-imports` — 2 contracts kept, 0 broken |
| CI/CD | PARTIAL | `.github/workflows/ci.yml` quality→docker→publish ordering corrected; **requires GitHub + Kaggle secrets to run** (external verification) |
| SHA image tagging | PASS (by inspection) | Workflow builds/pushes `ghcr.io/${repo}:${{ github.sha }}`; no `latest` tag; publish gated on push to `main` |
| README | PASS | Documents product, UX, architecture, dataset, model, training, API, validation, Docker, Compose, tests, CI/CD, limitations |
| BENCHMARKS | PASS | Measured numbers recorded; Docker/container rows marked `NOT MEASURED` with reason |
| DECISIONS | PASS | 10 decisions (≥5 required), including the four-input decision and rejected hidden defaults |
| Git history | PASS | 8 genuine incremental commits (`git log --oneline`); this review adds further incremental commits |
