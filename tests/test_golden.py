import json
from pathlib import Path

import pytest

from src.adapters.model import SklearnPriceModel
from src.domain.models import Vehicle


@pytest.mark.real_model
def test_golden_reference() -> None:
    path = Path("tests/golden_predictions.json")
    assert path.exists(), "Golden reference is required for the trained model release"
    assert Path("artifacts/price_model.joblib").exists(), "Trained model artifact is required"
    model = SklearnPriceModel.load(Path("artifacts/price_model.joblib"))
    cases = json.loads(path.read_text(encoding="utf-8"))
    for case in cases:
        f = case["features"]
        vehicle = Vehicle(f["make_model"], f["year"], f["mileage"])
        assert model.predict(vehicle) == case["estimated_price"]
