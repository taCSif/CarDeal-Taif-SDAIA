import json
from pathlib import Path

from src.adapters.model import SklearnPriceModel
from src.domain.models import Vehicle

CASES = [
    {"make_model": "Toyota Camry", "year": 2021, "mileage": 80_000},
    {"make_model": "Hyundai Elantra", "year": 2019, "mileage": 100_000},
    {"make_model": "Nissan Patrol", "year": 2016, "mileage": 90_000},
]

model = SklearnPriceModel.load(Path("artifacts/price_model.joblib"))
output = []
for features in CASES:
    estimate = model.predict(Vehicle(**features))
    output.append({"features": features, "estimated_price": estimate})
Path("tests/golden_predictions.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
print(json.dumps(output, indent=2))
