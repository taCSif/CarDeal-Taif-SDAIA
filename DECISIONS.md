# Engineering Decisions

## 1. Regression + deterministic policy
**Decision:** Predict expected listing price with regression and decide the deal separately.
**Context:** The dataset contains prices, not authoritative GOOD/REVIEW/POOR labels.
**Alternatives:** Derive classifier labels from the same price and thresholds; rule-only pricing.
**Why:** A classifier created from the same target-derived rule would learn the policy rather than market pricing. Separating ML estimation from policy keeps responsibilities testable and explainable.
**Trade-offs:** The model is optimized for price error, not directly for deal-classification accuracy.

## 2. Lightweight scikit-learn model
**Decision:** Use HistGradientBoostingRegressor behind a preprocessing Pipeline.
**Context:** The dataset is small enough for CPU training and inference.
**Alternatives:** Random Forest, XGBoost, neural networks.
**Why:** It avoids extra native dependencies and keeps the live demo operationally simple.
**Trade-offs:** Another model may produce different evaluation metrics; model choice must be based on the measured hold-out results, not assumptions.

## 3. Protocol-based model dependency
**Decision:** The service depends on a `PriceModel` Protocol.
**Context:** The model implementation should be replaceable.
**Alternatives:** Import sklearn directly in the service.
**Why:** The service remains framework/model independent and can be tested with a fake model.
**Trade-offs:** The adapter boundary adds a small amount of plumbing.

## 4. Startup loading + readiness
**Decision:** Load and warm the model during FastAPI lifespan; expose readiness separately from liveness.
**Context:** Import-time model loading makes failures harder to control and test.
**Alternatives:** Lazy first-request loading; module-level singleton.
**Why:** `/ready` accurately reflects whether the service can serve predictions.
**Trade-offs:** A missing/corrupt artifact leaves the application alive but not ready.

## 5. Data-quality filtering
**Decision:** Remove non-positive/low target prices, mileage above 700,000, invalid numeric rows, and impossible year/engine values.
**Context:** The published dataset uses `Price=0` for negotiable listings and contains extreme mileage values. Published analysis of this dataset also excluded prices below SAR 5,000 and mileage above 700,000.
**Alternatives:** Keep all rows; winsorize; impute invalid targets.
**Why:** A zero negotiated target is not a usable market-price target, while extreme invalid/out-of-scope records can distort regression.
**Trade-offs:** The resulting model should not be interpreted as covering listings outside the retained range.

## 6. PostgreSQL audit integration
**Decision:** Compose includes PostgreSQL and the app optionally writes a minimal prediction audit record when `DEAL_CHECKER_DATABASE_URL` is configured.
**Context:** The assignment requires a genuinely integrated supporting service.
**Alternatives:** Unused infrastructure; Redis; storing full requests.
**Why:** A small audit record demonstrates real persistence without storing vehicle free text or other unnecessary request data.
**Trade-offs:** Compose has one additional dependency and database startup cost.

## 7. Comparable Cars extension
**Decision:** Save the cleaned training listings as an artifact and expose up to five similar listings.
**Context:** A price estimate alone gives limited context.
**Alternatives:** No extension; external live market search.
**Why:** Local historical comparables are deterministic, offline, testable, and do not introduce another external API.
**Trade-offs:** Comparable listings are also historical 2021 data and are not live market listings.

## 8. Golden references are explicit
**Decision:** Golden predictions are generated only by a separate manual command and are never regenerated automatically by training or CI.
**Context:** Model changes can legitimately change predictions.
**Alternatives:** Auto-update golden values during training.
**Why:** Silent regeneration would allow behavioral regressions to become invisible.
**Trade-offs:** An intentional model release requires a human review of changed expected values.
