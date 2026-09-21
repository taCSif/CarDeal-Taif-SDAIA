from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.domain.models import Vehicle

FEATURE_COLUMNS = ["Make_Model", "Year", "Mileage"]


class SklearnPriceModel:
    def __init__(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    @classmethod
    def load(cls, path: Path) -> "SklearnPriceModel":
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        return cls(joblib.load(path))

    def warm_up(self) -> None:
        self.predict(Vehicle("Toyota Camry", 2021, 80_000))

    def predict(self, vehicle: Vehicle) -> float:
        frame = pd.DataFrame([{
            "Make_Model": vehicle.make_model,
            "Year": vehicle.year,
            "Mileage": vehicle.mileage,
        }], columns=FEATURE_COLUMNS)
        value = float(self._pipeline.predict(frame)[0])
        if value <= 0:
            raise ValueError("model returned a non-positive price")
        return value
