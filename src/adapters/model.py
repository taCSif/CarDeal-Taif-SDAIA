from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.domain.models import Vehicle

FEATURE_COLUMNS = [
    "Make", "Type", "Year", "Origin", "Color", "Options", "Engine_Size",
    "Fuel_Type", "Gear_Type", "Mileage", "Region",
]


class SklearnPriceModel:
    def __init__(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    @classmethod
    def load(cls, path: Path) -> "SklearnPriceModel":
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        return cls(joblib.load(path))

    def warm_up(self) -> None:
        sample = Vehicle("Toyota", "Camry", 2021, "Saudi", "White", "Full", 2.5, "Gas", "Automatic", 80000, "Riyadh")
        self.predict(sample)

    def predict(self, vehicle: Vehicle) -> float:
        frame = pd.DataFrame([{
            "Make": vehicle.make, "Type": vehicle.type, "Year": vehicle.year,
            "Origin": vehicle.origin, "Color": vehicle.color, "Options": vehicle.options,
            "Engine_Size": vehicle.engine_size, "Fuel_Type": vehicle.fuel_type,
            "Gear_Type": vehicle.gear_type, "Mileage": vehicle.mileage, "Region": vehicle.region,
        }], columns=FEATURE_COLUMNS)
        return float(self._pipeline.predict(frame)[0])
