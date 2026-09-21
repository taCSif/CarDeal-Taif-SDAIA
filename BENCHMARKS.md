# Benchmarks

Measured values are recorded only after actually running the corresponding command. The current development environment does not have Docker, the public dataset, Ruff, mypy, or import-linter installed, so those measurements are intentionally not claimed.

| Measurement | Result | Notes |
|---|---:|---|
| Non-real-model test suite | 1.59 s | 12 passed locally on 2026-09-21 |
| Branch coverage | 91.05% | 80% gate passed for the non-real-model suite |
| Docker image size | NOT MEASURED | Docker CLI unavailable in this environment |
| Docker build time | NOT MEASURED | Docker CLI unavailable in this environment |
| Model training time | NOT MEASURED | Public dataset unavailable in this environment |
| Real-model behavior | NOT MEASURED | Requires trained artifact from the public dataset |
| Fast lint/type/import gate | NOT MEASURED | Ruff, mypy, and import-linter unavailable in this environment |

CI is configured to measure the release path: download the public dataset, train the model, run real-model behavior/golden tests, build the image, run readiness/API smoke tests, and enforce the 500 MB image-size limit.
