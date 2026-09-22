# Learning Outcomes — From Model Builder to Production ML Engineer

The goal of this program is to move from *building models* to **engineering production AI
systems**: designing clean APIs around a model, containerising the service, automating
tests and CI/CD, and organising the codebase under Clean Architecture with proper
configuration management and static-analysis quality gates. CarDeal was built end-to-end to
demonstrate each of these competencies, not just a working model.

The table below maps every program objective to **how it was implemented** and **the
engineering skill it demonstrates**.

| Program objective | How it was implemented in CarDeal | Competency demonstrated |
|---|---|---|
| **Clean API around a model (FastAPI)** | `POST /v1/predict`, `GET /v1/comparables`, `GET /health`, `GET /ready`; a single response/error envelope carrying a `trace_id`; strict Pydantic request models with `extra="forbid"` and value ranges. | Designing a versioned, validated, observable HTTP contract that hides the model behind a stable interface — the API is the product, the model is an implementation detail. |
| **Containerisation (Docker)** | Multi-stage `Dockerfile` (build vs. runtime), non-root user, `/ready` healthcheck, a 418 MB image (≤ 500 MB), and `docker-compose.yml` running the app with PostgreSQL gated on `service_healthy`. | Packaging a service so it runs identically anywhere, with a lean, secure, health-aware runtime and a realistic multi-service topology. |
| **Automated testing & CI/CD (GitHub Actions)** | Pipeline `quality → docker → publish`: lint & type-check, tests with an 80% coverage gate, model training, real-model & golden tests, image build + smoke test, ≤ 500 MB size gate, then publish to GHCR — **main only**, tagged by **commit SHA**, never `:latest`. | Turning "it works on my machine" into an automated, reproducible release pipeline where every merge is proven before it ships. |
| **Clean Architecture & configuration management** | Four layers — `domain` (pure rules) / `service` (orchestration) / `adapters` (model, DB, settings) / `api`; the model sits behind a `Protocol` injected into the service; `import-linter` enforces the dependency direction; typed Pydantic `Settings` fail fast on misconfiguration. | Structuring code so business logic is independent of frameworks and infrastructure, and so the model can be swapped without touching the use case — maintainability by design. |
| **Code-quality tooling (review, linters, static analysis)** | `ruff` (lint), `mypy --strict` (types), `import-linter` (architecture), and `gitleaks` (secret scanning), all enforced as required checks on a protected `main` branch. | Treating quality as an automated, non-negotiable gate rather than a manual afterthought. |
| **Separation of ML from business logic** | The regression model only *estimates a price*; a separate deterministic policy classifies the deal (`GOOD_DEAL / REVIEW / POOR_DEAL`). Behavioural tests assert the policy's directionality and invariance. | Understanding that a model output is an input to a decision, not the decision itself — avoiding the circularity of training a classifier on a policy. |
| **Engineering honesty** | The model's known weaknesses (≈21k SAR MAE, non-monotonicity in mileage) are documented in `docs/model_limitations.md` and kept as an explicit `xfail`; benchmarks record only measured numbers; golden references are never silently regenerated. | Reporting real limitations and measured results instead of inflating them — the discipline that makes an engineer trustworthy.

## What this shifted in my practice

Before, "done" meant a notebook that produced a good metric. Through this project, "done"
now means a **service**: a clean API, a container, a green pipeline, enforced architecture,
scanned secrets, and honest documentation — everything a stranger engineer needs to run,
test, and trust the system in under ten minutes. The model is only one component inside a
production system, and the surrounding engineering is what makes it deployable and
maintainable. That shift — from *model builder* to *production ML engineer* — is exactly
what CarDeal was built to demonstrate.
