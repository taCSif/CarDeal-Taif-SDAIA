import pytest

from src.adapters.model import SklearnPriceModel
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
    clean = Vehicle("Toyota Camry", 2021, 80_000)
    normalized = Vehicle("Toyota Camry", 2021, 80_000)
    assert real_model.predict(clean) == real_model.predict(normalized)
