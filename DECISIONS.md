# Engineering Decisions

## 1. Regression + deterministic deal policy
**Decision:** Predict expected listing price with regression and decide the deal separately.

**Why:** The dataset contains prices, not authoritative GOOD/REVIEW/POOR labels. Training a classifier from labels derived from the same price target would make the classifier learn the policy rather than market pricing.

**Trade-off:** The model is optimized for price error, not deal-classification accuracy.

## 2. Four-input public contract
**Decision:** The UI exposes only `Make & Model`, `Year`, `Mileage`, and `Asking Price`.

**Why:** A used-car deal check should be quick. Requiring twelve vehicle attributes creates unnecessary user friction. The first three inputs are model features; asking price is intentionally kept outside the regression target path and is used only by the deterministic policy.

**Trade-off:** A smaller feature set may reduce predictive performance versus a richer vehicle specification. The hold-out metrics in `artifacts/metrics.json` are the evidence for the chosen model, not assumptions.

## 3. Combined Make_Model feature
**Decision:** Derive one `Make_Model` categorical feature from the dataset's `Make` and `Type` columns.

**Why:** It lets the user provide one natural "Make & Model" field without inventing hidden defaults for engine, transmission, color, options, region, or origin.

**Trade-off:** The model intentionally does not condition on those omitted vehicle attributes.

## 4. Protocol-based model dependency
**Decision:** The service depends on a `PriceModel` Protocol.

**Why:** The service remains independent of sklearn and the trained artifact can be replaced without changing the use case.

**Trade-off:** The adapter boundary adds a small amount of plumbing.

## 5. Startup loading + readiness
**Decision:** Load and warm the model during FastAPI lifespan; expose readiness separately from liveness.

**Why:** Import-time loading makes failures harder to control. `/ready` accurately represents whether predictions can be served.

**Trade-off:** A missing/corrupt model leaves the application alive but unready.

## 6. Data-quality filtering
**Decision:** Remove non-positive/low target prices, mileage above 700,000, invalid numeric rows, and impossible years.

**Why:** The published data includes zero-price/negotiable rows and extreme records that are not suitable as ordinary regression targets.

**Trade-off:** The resulting model should not be interpreted as covering listings outside the retained range.

## 7. Minimal PostgreSQL audit
**Decision:** Compose includes PostgreSQL and the app optionally records trace ID, model version, output prices, decision, and timestamp.

**Why:** This demonstrates a real supporting service while avoiding unnecessary persistence of the full vehicle request.

**Trade-off:** Compose has an additional service and startup dependency.

## 8. Historical comparable extension
**Decision:** Save cleaned training listings and expose up to five similar historical records.

**Why:** It gives the estimate context without introducing an external marketplace API.

**Trade-off:** These are 2021 historical records, not live listings.

## 9. Golden references are explicit
**Decision:** Golden predictions are generated only by a separate command (`scripts/generate_golden.py`) and reviewed intentionally. The golden test compares against them with a tight relative tolerance (`rel=1e-6`) rather than bit-exact equality.

**Why:** Silent regeneration would make model regressions invisible. A genuine regression shifts predictions by far more than 1e-6, while cross-platform BLAS and scikit-learn patch differences can move only the final floating-point digits — bit-exact equality would produce false failures across environments without catching any real regression.

**Trade-off:** A deliberate model release requires reviewing updated expected values; the tolerance is deliberately far tighter than any change that would matter to a user.

## 10. Input normalization boundary
**Decision:** Pydantic strips outer whitespace and collapses internal whitespace runs in `make_model` (so `"Toyota   Camry"` → `"Toyota Camry"`), but preserves casing.

**Why:** Whitespace normalization gives equivalent inputs one canonical representation. Casing is preserved because the model's one-hot categories are the dataset's own mixed-case labels (e.g. `"Toyota Camry"`, `"C300"`); lower/upper-casing user input would fail to match those categories and degrade predictions. Unseen categories are handled by `OneHotEncoder(handle_unknown="ignore")` at inference.

**Trade-off:** A user typing a different case than the dataset uses will get the unknown-category path rather than an automatic case match; this is a deliberate accuracy-preserving choice, and the behavioral test asserts whitespace-variant inputs produce identical predictions.
