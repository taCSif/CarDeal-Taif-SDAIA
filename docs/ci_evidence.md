# CI evidence

Real evidence for the latest audited push, captured directly from the GitHub
Actions run and the GitHub API — not asserted from memory. Regenerate this
file after any push whose CI result should be the one of record.

## Latest run

- **Run:** https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35695153495
- **Commit SHA:** `d7ad4b07ade45f27fb56c56b550c90c59bd3ead8`
- **Trigger:** push to `main`
- **Result:** all 3 jobs `success` (confirmed via `gh api repos/taCSif/CarDeal-Taif-SDAIA/actions/runs/35695153495/jobs`)

| Job | Conclusion | Duration | Job ID |
|---|---|---|---|
| quality | success | 40s | 106640289574 |
| docker | success | 1m2s | 106640460576 |
| publish | success | 1m13s | 106640713188 |

## What each job actually did (from the run's own log lines)

- **quality**, `python -m pytest -m 'not real_model'`: `23 passed, 7 deselected, 2 warnings in 3.21s`; `Total coverage: 92.77%` (gate: ≥80%).
- **docker**, `python scripts/train.py`: `source_rows: 8035`, `MAE_SAR: 21154.3`, `R2: 0.6916` — matches `artifacts/metrics.json` and `BENCHMARKS.md`.
- **docker**, `python -m pytest -m real_model`: `6 passed, 23 deselected, 1 xfailed, 2 warnings in 1.99s` — this is the first CI run that reached `tests/test_behavioural_model.py`; the 1 xfail is the documented mileage non-monotonicity (`docs/model_limitations.md`), not a failure.
- **docker**, image-size gate (`test "$(cat image-size-bytes.txt)" -le 524288000`): passed. The exact byte count is written to a file, not echoed to the log, so it isn't quoted here; the equivalent image built and measured locally at the same commit's dataset/code state was 418,897,920 bytes (see `BENCHMARKS.md`).
- **publish**: built and pushed `ghcr.io/tacsif/cardeal-taif-sdaia:d7ad4b07ade45f27fb56c56b550c90c59bd3ead8` (lowercased per `ci: lowercase the GHCR image tag`).

## Published image

- **Package page (publicly reachable, verified `curl -o /dev/null` → `200`):** https://github.com/taCSif/CarDeal-Taif-SDAIA/pkgs/container/cardeal-taif-sdaia
- Tagged by commit SHA only; no `latest` tag is pushed (`.github/workflows/ci.yml`'s `publish` job).

## Prior runs this session (for context — do not treat as current)

| Run | Commit | Result | Cause (if failed) |
|---|---|---|---|
| [35662860371](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35662860371) | `4bc481b` | failure | Kaggle secrets missing (before the dataset was committed) |
| [35680655183](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35680655183) | `88659b4` | failure | gitleaks: shallow clone had no history to diff |
| [35680864113](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35680864113) | `d71deda` | failure | `real_model` pytest's coverage gate ran on a 3-test subset (structurally always <80%) |
| [35681278490](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35681278490) | `95170b9` | failure | GHCR tag rejected: repo name has uppercase letters |
| [35681522558](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35681522558) | `808bff1` | success | first fully green run |
| [35684411581](https://github.com/taCSif/CarDeal-Taif-SDAIA/actions/runs/35684411581) | `6356a28` | success | behavioural tests + comparables endpoint added |
| **35695153495** | **`d7ad4b0`** | **success** | **current — this audit's final state** |
