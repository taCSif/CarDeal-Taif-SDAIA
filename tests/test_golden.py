import json
from pathlib import Path

import pytest

from src.adapters.model import SklearnPriceModel
from src.domain.models import Vehicle


def test_golden_reference() -> None:
    path = Path("tests/golden_predictions.json")
    if not path.exists() or not Path("artifacts/price_model.joblib").exists():
        pytest.skip("Golden reference requires an intentionally generated model artifact")
    model = SklearnPriceModel.load(Path("artifacts/price_model.joblib"))
    cases = json.loads(path.read_text(encoding="utf-8"))
    for case in cases:
        f = case["features"]
        vehicle = Vehicle(
            f["make"], f["type"], f["year"], f["origin"], f["color"], f["options"],
            f["engine_size"], f["fuel_type"], f["gear_type"], f["mileage"], f["region"],
        )
        assert model.predict(vehicle) == case["estimated_price"]
