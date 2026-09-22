# Known model limitation: mileage is not strictly monotonic

`scripts/train.py` fits a `HistGradientBoostingRegressor` with no
`monotonic_cst` constraint. Before writing
`tests/test_behavioural_model.py::test_higher_mileage_never_increases_price`,
the invariant it asserts ("more mileage never raises the estimate, all else
equal") was checked empirically against the real trained artifact
(`artifacts/price_model.joblib`) rather than assumed. It does not hold.

## Probe

```python
import joblib, pandas as pd
pipe = joblib.load("artifacts/price_model.joblib")
FEATURES = ["Make_Model", "Year", "Mileage"]

def predict(make_model, year, mileage):
    df = pd.DataFrame([{"Make_Model": make_model, "Year": year, "Mileage": mileage}], columns=FEATURES)
    return float(pipe.predict(df)[0])

makes = ["Toyota Camry", "Hyundai Elantra", "Nissan Patrol", "Toyota Corolla", "Ford Explorer", "Chevrolet Malibu"]
years = [2015, 2018, 2021]
mileages = [0, 10_000, 30_000, 50_000, 80_000, 120_000, 200_000, 300_000, 500_000, 700_000, 1_000_000, 2_000_000]

violations = [
    (mk, yr, mileages[i - 1], mileages[i])
    for mk in makes for yr in years
    for prices in [[predict(mk, yr, m) for m in mileages]]
    for i in range(1, len(prices)) if prices[i] > prices[i - 1] + 1e-6
]
```

## Result (run on the release artifact, 2026-09-22)

**42 non-monotonic transitions out of 198** (18 mileage steps x 6 makes x 3
years... 11 steps x 6 x 3 = 198 adjacent pairs). Examples:

| Make_Model | Year | Mileage A → B | Price A → B |
|---|---|---|---|
| Toyota Camry | 2015 | 0 → 10,000 | 44,842.33 → 51,091.08 |
| Toyota Camry | 2018 | 50,000 → 80,000 | 72,944.58 → 83,214.52 |
| Hyundai Elantra | 2018 | 0 → 10,000 | 22,256.80 → 55,267.05 |
| Nissan Patrol | 2015 | 0 → 10,000 | 86,077.59 → 101,688.94 |

## Why

- No monotonic constraint was requested at training time.
- `Make_Model x Year` combinations are sparse in the 5,385-row cleaned
  dataset (see `artifacts/metrics.json`); many low-mileage points for a given
  make/model/year are extrapolated from very few real rows, so the tree
  ensemble's boosted residual corrections are not smooth in mileage there.
- Near `Mileage=0` in particular, almost no cars in the source data are
  reported with zero kilometers, so predictions there lean on the boosting
  residuals rather than dense local evidence.

## What was checked and does hold

The same kind of probe for **unknown make/model never exceeds the training
max price** (`KNOWN_MAX_PRICE = 1,150,000`, the max `Price` in
`artifacts/comparable_cars.csv`) found **zero violations** across 3 unknown
names x 5 years x 4 mileages, and a wider check across 3 names x 8 years x 8
mileages spanning the full schema range (year 1950-2026, mileage
0-2,000,000). That invariant is encoded as a normal (non-xfail) test.

## Decision

Do not retrain to add a monotonic constraint here. Per `DECISIONS.md` #9,
`tests/golden_predictions.json` is only ever regenerated deliberately with
written justification, and retraining with `monotonic_cst` would change
every prediction, forcing exactly that regeneration — a materially larger
and riskier change than the scope of this audit. Instead,
`test_higher_mileage_never_increases_price` is kept in the suite, marked
`@pytest.mark.xfail(strict=True, reason=...)`: it runs on every CI build
against the real artifact, documents the limitation in the test output, and
would fail loudly (`XPASS`) if a future retrain accidentally fixed it
without updating this document.
