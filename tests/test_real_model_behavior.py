import pytest

from src.adapters.model import SklearnPriceModel
from src.api.schemas import PredictRequest
from src.domain.models import Decision, Vehicle
from src.service.predict import PredictService


@pytest.fixture(scope="session")
def real_model() -> SklearnPriceModel:
    return SklearnPriceModel.load(__import__("pathlib").Path("artifacts/price_model.joblib"))


@pytest.mark.real_model
def test_real_model_directional_policy(real_model: SklearnPriceModel) -> None:
    service = PredictService(real_model)
    vehicle = Vehicle("Toyota Camry", 2021, 80_000)
    prices = [90_000, 105_000, 110_000, 115_000, 120_000]
    order = {Decision.GOOD_DEAL: 0, Decision.REVIEW: 1, Decision.POOR_DEAL: 2}
    severities = [order[service.predict(vehicle, price).decision] for price in prices]
    assert severities == sorted(severities)


@pytest.mark.real_model
def test_real_model_normalized_input_is_stable(real_model: SklearnPriceModel) -> None:
    # Equivalent representations (outer + internal whitespace) must normalize to
    # the same request and therefore produce the same estimate from the real model.
    clean = PredictRequest(make_model="Toyota Camry", year=2021, mileage=80_000, asking_price=1)
    messy = PredictRequest(
        make_model="  Toyota   Camry  ", year=2021, mileage=80_000, asking_price=1
    )
    assert clean.make_model == messy.make_model == "Toyota Camry"
    clean_vehicle = Vehicle(clean.make_model, clean.year, clean.mileage)
    messy_vehicle = Vehicle(messy.make_model, messy.year, messy.mileage)
    assert real_model.predict(clean_vehicle) == real_model.predict(messy_vehicle)
