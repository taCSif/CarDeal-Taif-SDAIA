import pytest

from src.domain.decisions import assess_deal
from src.domain.models import Decision


def test_boundaries() -> None:
    # exactly 5% premium -> GOOD_DEAL (boundary is inclusive)
    assert assess_deal(100_000, 105_000).decision == Decision.GOOD_DEAL
    # slightly above 5% -> REVIEW
    assert assess_deal(100_000, 105_001).decision == Decision.REVIEW
    # exactly 15% premium -> REVIEW (boundary is inclusive)
    assert assess_deal(100_000, 115_000).decision == Decision.REVIEW
    # slightly above 15% -> POOR_DEAL
    assert assess_deal(100_000, 115_001).decision == Decision.POOR_DEAL
    # asking below estimate -> GOOD_DEAL
    assert assess_deal(100_000, 90_000).decision == Decision.GOOD_DEAL
    # asking equal to estimate -> GOOD_DEAL (0% premium)
    assert assess_deal(100_000, 100_000).decision == Decision.GOOD_DEAL


def test_invalid_prices() -> None:
    with pytest.raises(ValueError):
        assess_deal(0, 10)
    with pytest.raises(ValueError):
        assess_deal(10, 0)
