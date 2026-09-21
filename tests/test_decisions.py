import pytest
from src.domain.decisions import assess_deal
from src.domain.models import Decision


def test_boundaries():
    assert assess_deal(100_000, 105_000).decision == Decision.GOOD_DEAL
    assert assess_deal(100_000, 105_001).decision == Decision.REVIEW
    assert assess_deal(100_000, 115_000).decision == Decision.REVIEW
    assert assess_deal(100_000, 115_001).decision == Decision.POOR_DEAL
    assert assess_deal(100_000, 90_000).decision == Decision.GOOD_DEAL


def test_invalid_prices():
    with pytest.raises(ValueError): assess_deal(0, 10)
    with pytest.raises(ValueError): assess_deal(10, 0)
