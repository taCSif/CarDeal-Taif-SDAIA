from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.domain.models import Vehicle

FEATURE_COLUMNS = ["Make_Model", "Year", "Mileage"]


class SklearnPriceModel:
    """Adapter that implements service.predict.PriceModel over a trained
    scikit-learn pipeline (see scripts/train.py). This is the only module
    that imports the trained artifact's shape; the rest of the codebase only
    knows about the PriceModel Protocol.
    """

    def __init__(self, pipeline: Any) -> None:
        self._pipeline = pipeline

    @classmethod
    def load(cls, path: Path) -> "SklearnPriceModel":
        # Fail loudly and specifically (not a generic joblib error) when the
        # artifact is simply missing, e.g. before `make train` has been run.
        if not path.exists():
            raise FileNotFoundError(f"Model artifact not found: {path}")
        return cls(joblib.load(path))

    def warm_up(self) -> None:
        # Runs one real prediction during startup (see api.routes lifespan)
        # so that the first user-facing request does not pay the cost of
        # lazily initializing the sklearn pipeline's internals.
        self.predict(Vehicle("Toyota Camry", 2021, 80_000))

    def predict(self, vehicle: Vehicle) -> float:
        # Column order and names must match training exactly (see
        # scripts/train.py FEATURES); passing `columns=` here pins that
        # order regardless of the dict's insertion order.
        frame = pd.DataFrame([{
            "Make_Model": vehicle.make_model,
            "Year": vehicle.year,
            "Mileage": vehicle.mileage,
        }], columns=FEATURE_COLUMNS)
        value = float(self._pipeline.predict(frame)[0])
        # A non-positive price is not a valid market estimate; treat it as a
        # model/data error rather than passing it on to the deal policy.
        if value <= 0:
            raise ValueError("model returned a non-positive price")
        return value
