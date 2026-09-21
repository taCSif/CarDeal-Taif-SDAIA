# Engineering Decisions

## 1. Regression + deterministic policy
**Decision:** Predict price with regression and decide the deal separately.
**Context:** The dataset has listing prices, not authoritative GOOD/REVIEW/POOR labels.
**Alternatives:** Create labels from price thresholds and train a classifier; direct rule-only system.
**Why:** A classifier derived from the same price would learn the policy rather than learn market pricing. Separating ML estimation from policy keeps responsibilities clear.
**Trade-off:** The model is not directly optimized for deal classification.

## 2. Lightweight sklearn model
**Decision:** Use HistGradientBoostingRegressor with a preprocessing pipeline.
**Context:** The dataset is small enough for a CPU-friendly model.
**Alternatives:** Random Forest, XGBoost, neural networks.
**Why:** Low operational complexity and fast training/inference.
**Trade-off:** More sophisticated boosting libraries may improve accuracy but add dependencies/complexity.

## 3. Protocol-based model dependency
**Decision:** Service depends on `PriceModel` Protocol.
**Context:** Model implementation should be replaceable.
**Alternatives:** Import sklearn directly in service.
**Why:** Preserves clean architecture and simplifies testing with a fake model.
**Trade-off:** A small adapter layer is required.

## 4. Startup model loading
**Decision:** Load and warm the model during FastAPI lifespan.
**Context:** Model artifacts should not load during Python module import.
**Alternatives:** Lazy loading on first request; module-level singleton.
**Why:** Readiness accurately reflects whether the service can serve predictions.
**Trade-off:** Startup fails if the artifact is missing or corrupt.

## 5. Data-quality filtering
**Decision:** Remove prices below SAR 5,000 and mileage above 700,000, plus invalid numeric rows.
**Context:** The published dataset contains extreme/zero price and mileage values.
**Alternatives:** Winsorization; retain all values; impute.
**Why:** These records are unsuitable for a used-car price regression target and were also treated as extreme values in published analysis of this dataset.
**Trade-off:** The model does not cover listings outside the retained range.
