# Benchmarks

Measured values are recorded only after actually running the corresponding command. Values that cannot be produced in the current environment are marked `NOT MEASURED` with the reason, never fabricated.

Environment for the measured rows: Linux (Python 3.11.15), scikit-learn 1.9.1, pandas 2.3.3, real Saudi Arabia Used Cars dataset (`UsedCarsSA_Clean_EN.csv`, 8,035 rows), seed 42, on 2026-09-21.

| Measurement | Result | Notes |
|---|---:|---|
| Full test suite (incl. real-model) | 3.01 s | 17 passed |
| Non-real-model suite | 2.95 s | 14 passed, 3 deselected |
| Branch coverage (core packages) | 92.57% | 80% gate passed; `--cov-branch` over domain/service/adapters/api |
| Model training time | 3.33 s | `python scripts/train.py` on the real dataset |
| Rows after cleaning | 5,385 | from 8,035 source rows |
| Model MAE / RMSE / R² | 21,154.30 / 39,622.45 / 0.6916 | held-out 20% test split |
| Ruff | PASS | `ruff check src tests scripts`, 0 errors |
| mypy --strict | PASS | `mypy src`, 0 errors, 16 files |
| import-linter | PASS | 2 contracts kept, 0 broken |
| Secret scan (git history) | PASS | gitleaks 8.18.4, 8 commits, no leaks |
| Docker image size | NOT MEASURED | Docker daemon unavailable in this environment |
| Docker build time | NOT MEASURED | Docker daemon unavailable in this environment |
| Container smoke test | NOT MEASURED | Requires building/running the image |

CI is configured to reproduce the full release path on GitHub-hosted runners: download the dataset (with Kaggle secrets), train the model, run real-model behavior/golden tests, build the image, run readiness/API smoke tests, and enforce the 500 MB image-size limit. The Docker rows above can only be produced there or on a machine with Docker.
