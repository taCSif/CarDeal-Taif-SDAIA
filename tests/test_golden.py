import json
from pathlib import Path

import pytest

from src.adapters.model import SklearnPriceModel
from src.domain.models import Vehicle

# Golden values are compared with a tight relative tolerance rather than bit-exact
# equality. A meaningful model regression shifts predictions by far more than this,
# while cross-platform BLAS / sklearn patch differences can move the last few
# floating-point digits. Regenerate deliberately with scripts/generate_golden.py.
GOLDEN_REL_TOLERANCE = 1e-6


@pytest.mark.real_model
def test_golden_reference() -> None:
    path = Path("tests/golden_predictions.json")
    assert path.exists(), "Golden reference is required for the trained model release"
    assert Path("artifacts/price_model.joblib").exists(), "Trained model artifact is required"
    model = SklearnPriceModel.load(Path("artifacts/price_model.joblib"))
    cases = json.loads(path.read_text(encoding="utf-8"))
    assert cases, "Golden reference must contain at least one case"
    for case in cases:
        f = case["features"]
        vehicle = Vehicle(f["make_model"], f["year"], f["mileage"])
        prediction = model.predict(vehicle)
        assert prediction == pytest.approx(case["estimated_price"], rel=GOLDEN_REL_TOLERANCE)
