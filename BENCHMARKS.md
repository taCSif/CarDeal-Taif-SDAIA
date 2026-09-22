# Benchmarks

Measured values are recorded only after actually running the corresponding command. Values that cannot be produced in the current environment are marked `NOT MEASURED` with the reason, never fabricated.

## Track B targets (re-measured 2026-09-22 with `scripts/bench.sh`, commit `244581f`)

| Metric | Value | Target | Status |
|---|---:|---|---|
| Docker image size (uncompressed layers) | 418,897,920 bytes (418.9 MB) | ≤ 500 MB | PASS |
| `make fast-test`, GitHub Actions (`quality` job, `-m 'not real_model'`) | 3.24 s | ≤ 60 s | PASS — see `docs/ci_evidence.md` |
| `make fast-test`, this Windows dev machine | 115 s wall (pytest self-reported: 50.97 s) | ≤ 60 s | **FAIL on this machine** — see note below; the CI number is what actually gates merges |
| `make test` (full suite incl. real-model), this Windows dev machine | 80 s wall (pytest self-reported: 68.38 s) | n/a (not a gated target) | measured for reference |
| Branch coverage (core packages) | 92.77% | ≥ 80% | PASS |

**Why the local fast-test number misses the target:** this development machine has 8 GB total RAM and was observed with as little as ~21 MB free physical memory while `docker` (including an unrelated project's containers) and other applications were running concurrently (`wmic OS get FreePhysicalMemory,TotalVisibleMemorySize`). Two consecutive runs measured 151.76 s and 87.83 s for the same command before this table's 115 s; pytest's own reported CPU time (50.97 s) is far more stable than the wall-clock time, which is dominated by OS-level paging under memory pressure. This is a real, reproducible measurement on this machine, reported honestly rather than discarded — but the number that actually governs the pipeline is the one GitHub Actions' `quality` job produces on its own hosted runner (3.24 s, well under target; see `docs/ci_evidence.md` for the run this came from). `Makefile`'s `fast-test` was also fixed in this pass to exclude `real_model` tests (it previously only excluded `slow`, which no test uses, so it silently ran the full real-model suite — see commit `fix(test): exclude real_model tests from the fast gate`).

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
| Secret scan (git history) | PASS | gitleaks 8.30.1, no leaks; re-run 2026-09-22 over 25 commits (787.06 KB scanned) after this audit's commits |
| Docker image size (uncompressed layers) | 418.9 MB (399.5 MiB) | Sum of layer sizes from `docker history --human=false`; **passes** the 500 MB limit. Same figure a classic overlay-store daemon (GitHub-hosted runners) reports via `docker image inspect --format '{{.Size}}'`. Re-measured 2026-09-22 at commit `244581f` (after adding `GET /v1/comparables`): 418,897,920 bytes, unchanged to within rounding |
| Docker Desktop "disk usage" | 545.3 MB (545,270,346 bytes at `244581f`) | `docker image inspect` on Docker Desktop 29.8.0 (containerd image store) adds the compressed content blob to the unpacked layers, so it double counts. Recorded for transparency; do not compare it against the CI gate |
| Docker image size (compressed) | 126.4 MB | `docker save` tar size |
| Docker build time | 392 s (289 s on the 2026-09-22 re-run, base layers cached) | `docker build` on Windows 10 / Docker Desktop, through a TLS-intercepting proxy (see note) |
| Compose `up --build -d` | 177 s | Layers cached; includes pulling `postgres:16-alpine` |
| Container smoke test | PASS | `/health` 200, `/ready` 200, `POST /v1/predict` (Toyota Camry, 2021, 80,000 km, asking 85,000) 200 with estimate 75,261.84 and decision `REVIEW`, invalid body 422 with `trace_id`; `GET /v1/comparables` 200 with the closest 5, an unknown query param 422, an out-of-range value 422; `python scripts/smoke.py` PASS; container reported `healthy` (re-run 2026-09-22 at commit `244581f`, including the new endpoint) |
| Compose smoke test | PASS | postgres `healthy`, app `healthy`; same requests as above; one row written to `prediction_audit` |
| Full test suite, Windows 10 / Python 3.11.4 | 58.9 s (earlier run); 68.4 s / 80 s wall on 2026-09-22 under memory pressure (see Track B table above) | 29 passed, 1 xfailed (documented model limitation, see `docs/model_limitations.md`), 92.77% branch coverage |

Docker-related notes:

- Before slimming, the layers summed to about 610 MB (the virtualenv layer alone was 466 MB; Docker Desktop reported 788 MB disk usage): scikit-learn, scipy, numpy and pandas ship large `tests/` directories and bytecode. The builder stage now installs with `--no-compile`, removes `tests`/`test` directories and `__pycache__`, and uninstalls `pip`/`setuptools` from the runtime virtualenv (466 MB to 275 MB). The API, real-model and Compose runs above were all done on the slimmed image.
- The build machine sits behind a TLS-intercepting proxy, so `pip` inside the container failed certificate verification. The measurements above were produced from a temporary copy of the `Dockerfile` that only adds `ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org"`. The `Dockerfile` in the repository is unchanged in that respect and builds normally on a network without interception.
- Host port 8000 was occupied by an unrelated container, so the runs used host port 18000 mapped to container port 8000.
- Test-suite timings differ between the Linux (3.01 s) and Windows (58.9 s / 68.4 s) rows because they were measured on different machines under different load; they are not comparable with each other.
- `scripts/bench.sh` reproduces the Track B table above (`make fast-test` / `make test` timing, `docker image inspect` size, `docker history` top layers). Run `bash scripts/bench.sh --skip-docker` to skip the Docker portion where Docker isn't available.

CI is configured to reproduce the full release path on GitHub-hosted runners: train the model from the committed dataset, run real-model behavior/golden tests, build the image, run readiness/API smoke tests, and enforce the 500 MB image-size limit. No repository secrets are required.
