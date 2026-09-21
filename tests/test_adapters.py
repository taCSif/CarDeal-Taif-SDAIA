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


FEATURES = [
    "Make", "Type", "Year", "Origin", "Color", "Options", "Engine_Size",
    "Fuel_Type", "Gear_Type", "Mileage", "Region",
]


def make_pipeline() -> Pipeline:
    x = pd.DataFrame([{
        "Make": "Toyota", "Type": "Camry", "Year": 2021, "Origin": "Saudi",
        "Color": "White", "Options": "Full", "Engine_Size": 2.5, "Fuel_Type": "Gas",
        "Gear_Type": "Automatic", "Mileage": 80_000, "Region": "Riyadh",
    }])
    model = Pipeline([
        (
            "preprocess",
            ColumnTransformer([
                ("cat", OneHotEncoder(handle_unknown="ignore"), [
                    "Make", "Type", "Origin", "Color", "Options", "Fuel_Type",
                    "Gear_Type", "Region",
                ]),
                ("num", "passthrough", ["Year", "Engine_Size", "Mileage"]),
            ]),
        ),
        ("model", DummyRegressor(strategy="constant", constant=100_000)),
    ])
    model.fit(x[FEATURES], [100_000])
    return model


def vehicle() -> Vehicle:
    return Vehicle(
        "Toyota", "Camry", 2021, "Saudi", "White", "Full", 2.5,
        "Gas", "Automatic", 80_000, "Riyadh",
    )


def test_sklearn_model_load_predict_and_warmup(tmp_path: Path) -> None:
    path = tmp_path / "model.joblib"
    joblib.dump(make_pipeline(), path)
    model = SklearnPriceModel.load(path)
    model.warm_up()
    assert model.predict(vehicle()) == 100_000


def test_comparable_repository_prefers_exact_make_type(tmp_path: Path) -> None:
    path = tmp_path / "comparables.csv"
    pd.DataFrame([
        {
            "Make": "Toyota", "Type": "Camry", "Year": 2021, "Origin": "Saudi",
            "Color": "White", "Options": "Full", "Engine_Size": 2.5, "Fuel_Type": "Gas",
            "Gear_Type": "Automatic", "Mileage": 80_000, "Region": "Riyadh", "Price": 70_000,
        },
        {
            "Make": "Toyota", "Type": "Camry", "Year": 2020, "Origin": "Saudi",
            "Color": "White", "Options": "Full", "Engine_Size": 2.5, "Fuel_Type": "Gas",
            "Gear_Type": "Automatic", "Mileage": 90_000, "Region": "Riyadh", "Price": 65_000,
        },
        {
            "Make": "Toyota", "Type": "Corolla", "Year": 2021, "Origin": "Saudi",
            "Color": "White", "Options": "Full", "Engine_Size": 2.0, "Fuel_Type": "Gas",
            "Gear_Type": "Automatic", "Mileage": 80_000, "Region": "Riyadh", "Price": 55_000,
        },
    ]).to_csv(path, index=False)
    results = ComparableCarsRepository(path).find_similar(vehicle(), limit=2)
    assert len(results) == 2
    assert all(result.type == "Camry" for result in results)
