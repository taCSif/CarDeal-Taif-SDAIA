from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.adapters.model import SklearnPriceModel
from src.adapters.repository import ComparableCarsRepository
from src.domain.models import Vehicle

FEATURES = ["Make_Model", "Year", "Mileage"]


def make_pipeline() -> Pipeline:
    x = pd.DataFrame([{"Make_Model": "Toyota Camry", "Year": 2021, "Mileage": 80_000}])
    model = Pipeline([
        ("preprocess", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["Make_Model"]),
            ("num", "passthrough", ["Year", "Mileage"]),
        ])),
        ("model", DummyRegressor(strategy="constant", constant=100_000)),
    ])
    model.fit(x[FEATURES], [100_000])
    return model


def vehicle() -> Vehicle:
    return Vehicle("Toyota Camry", 2021, 80_000)


def test_sklearn_model_load_predict_and_warmup(tmp_path: Path) -> None:
    path = tmp_path / "model.joblib"
    joblib.dump(make_pipeline(), path)
    model = SklearnPriceModel.load(path)
    model.warm_up()
    assert model.predict(vehicle()) == 100_000


def test_comparable_repository_prefers_exact_make_model(tmp_path: Path) -> None:
    path = tmp_path / "comparables.csv"
    pd.DataFrame([
        {"Make_Model": "Toyota Camry", "Year": 2021, "Mileage": 80_000, "Price": 70_000},
        {"Make_Model": "Toyota Camry", "Year": 2020, "Mileage": 90_000, "Price": 65_000},
        {"Make_Model": "Toyota Corolla", "Year": 2021, "Mileage": 80_000, "Price": 55_000},
    ]).to_csv(path, index=False)
    results = ComparableCarsRepository(path).find_similar(vehicle(), limit=2)
    assert len(results) == 2
    assert all(result.make_model == "Toyota Camry" for result in results)
