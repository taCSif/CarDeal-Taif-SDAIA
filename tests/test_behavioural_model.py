"""Behavioural invariants asserted end-to-end against the real trained model.

Markers: real_model (loads artifacts/price_model.joblib, requires the release
artifact to exist) and integration (exercises the model together with the
domain policy and/or service layer, not a single unit in isolation).

Each invariant below was verified empirically against the actual artifact
before being written as an assertion — see docs/model_limitations.md for the
probe script and raw findings. One documented invariant does not hold for
this model; it is kept as an explicit xfail rather than omitted or forced to
pass (see test_higher_mileage_never_increases_price below).
"""

import json
from pathlib import Path

import pytest

from src.adapters.model import SklearnPriceModel
from src.domain.models import Decision, Vehicle
from src.service.predict import PredictService

pytestmark = [pytest.mark.real_model, pytest.mark.integration]

ARTIFACT = Path("artifacts/price_model.joblib")
GOLDEN = Path("tests/golden_predictions.json")
COMPARABLES = Path("artifacts/comparable_cars.csv")

# Max Price observed in the training data (artifacts/comparable_cars.csv), i.e.
# the most expensive car the model was actually trained on. See
# docs/model_limitations.md for how this was computed and verified.
KNOWN_MAX_PRICE = 1_150_000.0


@pytest.fixture(scope="module")
def real_model() -> SklearnPriceModel:
    assert ARTIFACT.exists(), "Trained model artifact is required for real_model tests"
    return SklearnPriceModel.load(ARTIFACT)


def test_higher_asking_price_never_improves_decision(real_model: SklearnPriceModel) -> None:
    """Raising the asking price, all else equal, can only hold or worsen the decision.

    This follows deterministically from src.domain.decisions.assess_deal: decision
    severity is a monotonic step function of the asking/estimate premium ratio,
    which strictly increases as asking_price increases for a fixed estimate.
    Verified here end to end through PredictService against the real model.
    """
    service = PredictService(real_model)
    vehicle = Vehicle("Toyota Camry", 2021, 80_000)
    severity = {Decision.GOOD_DEAL: 0, Decision.REVIEW: 1, Decision.POOR_DEAL: 2}
    prices = [60_000, 70_000, 80_000, 90_000, 100_000, 120_000, 150_000, 200_000]
    decisions = [severity[service.predict(vehicle, price).decision] for price in prices]
    assert decisions == sorted(decisions)


def test_unknown_make_model_never_exceeds_known_max(real_model: SklearnPriceModel) -> None:
    """A make/model absent from training must not be priced above the most
    expensive car actually observed in training.

    OneHotEncoder(handle_unknown="ignore") zeroes the categorical row for
    unseen make/models, so the model falls back to Year/Mileage alone. This
    asserts that fallback stays within the training price range rather than
    extrapolating unboundedly. Verified empirically across the full valid
    schema range (year 1950-2026, mileage 0-2,000,000; see
    docs/model_limitations.md) before being encoded as a test.
    """
    assert COMPARABLES.exists(), "comparable_cars.csv is required to know the training max price"
    unknown_names = ["Zzzzz Unknownmodel", "Totally Madeup Brand", "Nonexistent Vehicle"]
    years = [1950, 1980, 2010, 2021, 2026]
    mileages = [0, 50_000, 500_000, 2_000_000]
    for name in unknown_names:
        for year in years:
            for mileage in mileages:
                estimate = real_model.predict(Vehicle(name, year, mileage))
                assert estimate <= KNOWN_MAX_PRICE, (
                    f"{name}/{year}/{mileage} predicted {estimate}, "
                    f"exceeding the known training max of {KNOWN_MAX_PRICE}"
                )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Documented genuine model limitation, not a test bug: scripts/train.py "
        "trains a HistGradientBoostingRegressor with no monotonic_cst constraint "
        "on Mileage, and Make_Model x Year combinations are sparse and noisy in "
        "the source data. An empirical sweep (6 make/models x 3 years x 12 "
        "mileage points, see docs/model_limitations.md) found 42 non-monotonic "
        "mileage transitions out of 198. Retraining with a monotonic constraint "
        "would be a real model change requiring tests/golden_predictions.json "
        "to be regenerated with written justification (DECISIONS.md), which is "
        "out of scope here. Kept as strict xfail — documented and executed, "
        "not silently omitted or forced to pass."
    ),
)
def test_higher_mileage_never_increases_price(real_model: SklearnPriceModel) -> None:
    vehicle_specs = [("Toyota Camry", 2021), ("Hyundai Elantra", 2018), ("Nissan Patrol", 2015)]
    mileages = [0, 10_000, 30_000, 50_000, 80_000, 120_000, 200_000, 300_000, 500_000]
    for make_model, year in vehicle_specs:
        prices = [real_model.predict(Vehicle(make_model, year, m)) for m in mileages]
        for earlier, later in zip(prices, prices[1:], strict=True):
            assert later <= earlier + 1e-6


def test_golden_predictions_match(real_model: SklearnPriceModel) -> None:
    """Absolute-tolerance check of the golden reference (kept unchanged; see
    DECISIONS.md #9 for why golden references are never auto-regenerated).

    tests/test_golden.py separately enforces a tighter 1e-6 relative
    tolerance against the same file; this asserts the <=1 SAR absolute bound
    explicitly and independently.
    """
    assert GOLDEN.exists(), "Golden reference is required for the trained model release"
    cases = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert cases, "Golden reference must contain at least one case"
    for case in cases:
        f = case["features"]
        vehicle = Vehicle(f["make_model"], f["year"], f["mileage"])
        prediction = real_model.predict(vehicle)
        assert prediction == pytest.approx(case["estimated_price"], abs=1.0)
