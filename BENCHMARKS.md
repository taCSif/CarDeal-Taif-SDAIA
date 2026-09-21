# Benchmarks

Measured values are recorded only after actually running the corresponding command. Values that cannot be produced in the current environment are marked `NOT MEASURED` with the reason, never fabricated.

Environment for the measured rows: Linux (Python 3.11.15), scikit-learn 1.9.1, pandas 2.3.3, real Saudi Arabia Used Cars dataset (`UsedCarsSA_Clean_EN.csv`, 8,035 rows), seed 42, on 2026-09-21.

| Measurement | Result | Notes |
|---|---:|---|
| Full test suite (incl. real-model), Linux | 3.01 s | 17 passed (earlier Linux run) |
| Non-real-model suite, Linux | 2.95 s | 14 passed, 3 deselected (earlier Linux run) |
| Branch coverage (core packages) | 92.59% | 80% gate passed; `--cov-branch` over domain/service/adapters/api |
| Model training time | 3.33 s | `python scripts/train.py` on the real dataset |
| Rows after cleaning | 5,385 | from 8,035 source rows |
| Model MAE / RMSE / R² | 21,154.30 / 39,622.45 / 0.6916 | held-out 20% test split |
| Ruff | PASS | `ruff check src tests scripts`, 0 errors (re-run 2026-09-22, ruff 0.16.8) |
| mypy --strict | PASS | `mypy src`, 0 errors, 16 files (re-run 2026-09-22, mypy 1.20.2) |
| import-linter | PASS | 2 contracts kept, 0 broken |
| Secret scan (git history) | PASS | gitleaks 8.30.1, full history after rewrite, no leaks (re-run 2026-09-22) |
| Docker image size (uncompressed layers) | 418.9 MB (399.5 MiB) | Sum of layer sizes from `docker history --human=false`; **passes** the 500 MB limit. Same figure a classic overlay-store daemon (GitHub-hosted runners) reports via `docker image inspect --format '{{.Size}}'` |
| Docker Desktop "disk usage" | 545.3 MB | `docker image inspect` on Docker Desktop 29.8.0 (containerd image store) adds the 126.4 MB compressed content blob to the 418.9 MB unpacked layers, so it double counts. Recorded for transparency; do not compare it against the CI gate |
| Docker image size (compressed) | 126.4 MB | `docker save` tar size |
| Docker build time | 392 s | `docker build` on Windows 10 / Docker Desktop, base image already pulled, pip downloads uncached, through a TLS-intercepting proxy (see note) |
| Compose `up --build -d` | 177 s | Layers cached; includes pulling `postgres:16-alpine` |
| Container smoke test | PASS | `/health` 200, `/ready` 200, `POST /v1/predict` (Toyota Camry, 2021, 80,000 km, asking 85,000) 200 with estimate 75,261.84 and decision `REVIEW`, invalid body 422 with `trace_id`; container reported `healthy` |
| Compose smoke test | PASS | postgres `healthy`, app `healthy`; same four requests as above; one row written to `prediction_audit` |
| Full test suite, Windows 10 / Python 3.11.4 | 58.9 s | 18 passed, 92.59% branch coverage, run on 2026-09-22 |

Docker-related notes:

- Before slimming, the layers summed to about 610 MB (the virtualenv layer alone was 466 MB; Docker Desktop reported 788 MB disk usage): scikit-learn, scipy, numpy and pandas ship large `tests/` directories and bytecode. The builder stage now installs with `--no-compile`, removes `tests`/`test` directories and `__pycache__`, and uninstalls `pip`/`setuptools` from the runtime virtualenv (466 MB to 275 MB). The API, real-model and Compose runs above were all done on the slimmed image.
- The build machine sits behind a TLS-intercepting proxy, so `pip` inside the container failed certificate verification. The measurements above were produced from a temporary copy of the `Dockerfile` that only adds `ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org"`. The `Dockerfile` in the repository is unchanged in that respect and builds normally on a network without interception.
- Host port 8000 was occupied by an unrelated container, so the runs used host port 18000 mapped to container port 8000.
- Test-suite timings differ between the Linux (3.01 s) and Windows (58.9 s) rows because they were measured on different machines; they are not comparable with each other.

CI is configured to reproduce the full release path on GitHub-hosted runners: download the dataset (with Kaggle secrets), train the model, run real-model behavior/golden tests, build the image, run readiness/API smoke tests, and enforce the 500 MB image-size limit. That workflow has not yet run on GitHub; it needs `KAGGLE_USERNAME` and `KAGGLE_KEY` repository secrets.
