from fastapi.testclient import TestClient
from src.api.routes import create_app
from src.adapters.settings import Settings


def test_schema_rejects_unknown_field():
    # Startup is intentionally bypassed here; schema behavior is tested directly.
    from src.api.schemas import PredictRequest
    import pytest
    with pytest.raises(Exception):
        PredictRequest(make="Toyota", type="Camry", year=2021, origin="Saudi", color="White", options="Full", engine_size=2.5, fuel_type="Gas", gear_type="Automatic", mileage=1, region="Riyadh", asking_price=1, extra="x")
