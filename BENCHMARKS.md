# Benchmarks

Measured in the current execution environment on 2026-09-21.

| Measurement | Result | Notes |
|---|---:|---|
| Full test suite | 3.829 s | `make test`, 11 passed, 1 skipped |
| Branch coverage | 90.48% | 80% gate passed |
| Docker image size | NOT MEASURED | Docker CLI is unavailable in this environment |
| Docker build time | NOT MEASURED | Docker CLI is unavailable in this environment |
| Model training time | NOT MEASURED | Source dataset file is not available inside the execution environment |
| Fast gate | NOT MEASURED | Lint/type/import-linter executables are not installed in this environment |

The CI workflow measures the Docker image size and blocks images above 500 MB. It also trains the model from the public Kaggle dataset before the Docker build.
