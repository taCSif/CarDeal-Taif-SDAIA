"""Create golden references after an intentional model release.

This script is never called by training or CI automatically. Review the resulting
file before committing it; changing expected predictions is an explicit decision.
"""

import json
from pathlib import Path

import joblib
import pandas as pd

CASES = [
    {
        "make": "Toyota", "type": "Camry", "year": 2021, "origin": "Saudi",
        "color": "White", "options": "Full", "engine_size": 2.5, "fuel_type": "Gas",
        "gear_type": "Automatic", "mileage": 80_000, "region": "Riyadh",
    },
    {
        "make": "Hyundai", "type": "Elantra", "year": 2019, "origin": "Saudi",
        "color": "Silver", "options": "Standard", "engine_size": 1.6, "fuel_type": "Gas",
        "gear_type": "Automatic", "mileage": 100_000, "region": "Riyadh",
    },
    {
        "make": "Nissan", "type": "Patrol", "year": 2016, "origin": "Saudi",
        "color": "White", "options": "Full", "engine_size": 4.8, "fuel_type": "Gas",
        "gear_type": "Automatic", "mileage": 90_000, "region": "Riyadh",
    },
]


def main() -> None:
    model = joblib.load(Path("artifacts/price_model.joblib"))
    rows = []
    for features in CASES:
        estimate = float(model.predict(pd.DataFrame([features]))[0])
        rows.append({"features": features, "estimated_price": round(estimate, 2)})
    Path("tests/golden_predictions.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8"
    )
    print("Wrote tests/golden_predictions.json. Review and commit intentionally.")


if __name__ == "__main__":
    main()
