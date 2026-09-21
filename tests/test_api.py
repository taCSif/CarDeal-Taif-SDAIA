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
from src.api.schemas import PredictRequest

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
