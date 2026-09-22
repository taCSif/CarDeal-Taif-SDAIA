from pathlib import Path

import joblib
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.adapters.settings import Settings
from src.api.routes import create_app
from src.api.schemas import ComparablesQuery, PredictRequest

FEATURES = ["Make_Model", "Year", "Mileage"]


def build_test_artifact(path: Path) -> None:
    model = Pipeline([
        ("preprocess", ColumnTransformer([
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["Make_Model"]),
            ("num", "passthrough", ["Year", "Mileage"]),
        ])),
        ("model", DummyRegressor(strategy="constant", constant=100_000)),
    ])
    x = pd.DataFrame([{"Make_Model": "Toyota Camry", "Year": 2021, "Mileage": 80_000}])
    model.fit(x[FEATURES], [100_000])
    joblib.dump(model, path)


def valid_payload() -> dict[str, object]:
    return {"make_model": "Toyota Camry", "year": 2021, "mileage": 80_000, "asking_price": 105_000}


def build_test_comparables_csv(path: Path) -> None:
    # 6 exact Camry matches (>= the repository's limit of 5) plus 2 Corolla rows,
    # so the "prefer exact make_model" branch in ComparableCarsRepository is
    # actually exercised: the closest 5 returned should all be Camrys.
    rows = [
        {"Make_Model": "Toyota Camry", "Year": year, "Mileage": mileage, "Price": price}
        for year, mileage, price in [
            (2021, 80_000, 75_000),
            (2020, 90_000, 70_000),
            (2021, 60_000, 78_000),
            (2019, 100_000, 65_000),
            (2020, 70_000, 72_000),
            (2018, 110_000, 60_000),
        ]
    ]
    rows += [
        {"Make_Model": "Toyota Corolla", "Year": 2021, "Mileage": 80_000, "Price": 55_000},
        {"Make_Model": "Toyota Corolla", "Year": 2020, "Mileage": 85_000, "Price": 52_000},
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def test_schema_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        PredictRequest(**valid_payload(), extra="x")


def test_schema_rejects_single_token_make_model() -> None:
    with pytest.raises(ValidationError):
        PredictRequest(**{**valid_payload(), "make_model": "Toyota"})


def test_custom_validator_error_returns_422_not_500(tmp_path: Path) -> None:
    # Regression: a custom field-validator failure (single-token make_model) must
    # produce a serializable 422 envelope, not crash the error handler into a 500.
    artifact = tmp_path / "model.joblib"
    build_test_artifact(artifact)
    app = create_app(Settings(model_path=artifact, comparables_path=tmp_path / "none.csv"))
    with TestClient(app) as client:
        response = client.post("/v1/predict", json={**valid_payload(), "make_model": "Toyota"})
        assert response.status_code == 422
        assert response.json()["data"]["error"] == "VALIDATION_ERROR"
        assert response.json()["data"]["details"][0]["loc"] == ["body", "make_model"]


def test_predict_returns_503_when_not_ready(tmp_path: Path) -> None:
    app = create_app(Settings(model_path=tmp_path / "missing.joblib"))
    with TestClient(app) as client:
        response = client.post("/v1/predict", json=valid_payload())
        assert response.status_code == 503
        assert response.json()["data"]["error"] == "NOT_READY"


def test_health_and_readiness_and_prediction(tmp_path: Path) -> None:
    artifact = tmp_path / "model.joblib"
    build_test_artifact(artifact)
    app = create_app(Settings(model_path=artifact, comparables_path=tmp_path / "none.csv"))
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.headers["X-Trace-ID"] == health.json()["trace_id"]
        ready = client.get("/ready")
        assert ready.status_code == 200
        response = client.post(
            "/v1/predict", json=valid_payload(), headers={"X-Trace-ID": "fixed-trace"}
        )
        assert response.status_code == 200
        assert response.json()["trace_id"] == "fixed-trace"
        assert response.json()["data"]["estimated_price"] == 100_000.0
        assert response.json()["data"]["decision"] == "GOOD_DEAL"


def test_ui_is_served() -> None:
    from src.api.routes import create_app
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Know the price" in response.text


def test_validation_and_not_ready_are_unified(tmp_path: Path) -> None:
    app = create_app(Settings(model_path=tmp_path / "missing.joblib"))
    with TestClient(app) as client:
        assert client.get("/ready").status_code == 503

    artifact = tmp_path / "model.joblib"
    build_test_artifact(artifact)
    ready_app = create_app(Settings(model_path=artifact, comparables_path=tmp_path / "none.csv"))
    with TestClient(ready_app) as client:
        bad = client.post("/v1/predict", json={**valid_payload(), "mileage": -1})
        assert bad.status_code == 422
        assert bad.json()["data"]["error"] == "VALIDATION_ERROR"


# --- GET /v1/comparables (unit: schema only, no app/model involved) ---------


def test_comparables_query_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        ComparablesQuery(make_model="Toyota Camry", year=2021, mileage=80_000, extra="x")


def test_comparables_query_rejects_single_token_make_model() -> None:
    with pytest.raises(ValidationError):
        ComparablesQuery(make_model="Toyota", year=2021, mileage=80_000)


def test_comparables_query_rejects_out_of_range_year() -> None:
    with pytest.raises(ValidationError):
        ComparablesQuery(make_model="Toyota Camry", year=1800, mileage=80_000)


def test_comparables_query_normalizes_whitespace() -> None:
    query = ComparablesQuery(make_model="  Toyota   Camry  ", year=2021, mileage=80_000)
    assert query.make_model == "Toyota Camry"


# --- GET /v1/comparables (integration: real app + TestClient) --------------


def test_comparables_endpoint_returns_similar_cars(tmp_path: Path) -> None:
    artifact = tmp_path / "model.joblib"
    build_test_artifact(artifact)
    comparables_path = tmp_path / "comparables.csv"
    build_test_comparables_csv(comparables_path)
    app = create_app(Settings(model_path=artifact, comparables_path=comparables_path))
    with TestClient(app) as client:
        response = client.get(
            "/v1/comparables", params={"make_model": "Toyota Camry", "year": 2021, "mileage": 80_000}
        )
        assert response.status_code == 200
        assert response.headers["X-Trace-ID"] == response.json()["trace_id"]
        cars = response.json()["data"]["comparable_cars"]
        assert len(cars) == 5  # the closest 5, per ComparableRepository.find_similar's default
        assert all(car["make_model"] == "Toyota Camry" for car in cars)


def test_comparables_endpoint_rejects_unknown_query_param(tmp_path: Path) -> None:
    artifact = tmp_path / "model.joblib"
    build_test_artifact(artifact)
    app = create_app(Settings(model_path=artifact, comparables_path=tmp_path / "none.csv"))
    with TestClient(app) as client:
        response = client.get(
            "/v1/comparables",
            params={"make_model": "Toyota Camry", "year": 2021, "mileage": 80_000, "bogus": "x"},
        )
        assert response.status_code == 422
        assert response.json()["data"]["error"] == "VALIDATION_ERROR"


def test_comparables_endpoint_rejects_out_of_range_mileage(tmp_path: Path) -> None:
    artifact = tmp_path / "model.joblib"
    build_test_artifact(artifact)
    app = create_app(Settings(model_path=artifact, comparables_path=tmp_path / "none.csv"))
    with TestClient(app) as client:
        response = client.get(
            "/v1/comparables", params={"make_model": "Toyota Camry", "year": 2021, "mileage": -1}
        )
        assert response.status_code == 422
        assert response.json()["data"]["error"] == "VALIDATION_ERROR"


def test_comparables_endpoint_returns_503_when_not_ready(tmp_path: Path) -> None:
    app = create_app(Settings(model_path=tmp_path / "missing.joblib"))
    with TestClient(app) as client:
        response = client.get(
            "/v1/comparables", params={"make_model": "Toyota Camry", "year": 2021, "mileage": 80_000}
        )
        assert response.status_code == 503
        assert response.json()["data"]["error"] == "NOT_READY"
