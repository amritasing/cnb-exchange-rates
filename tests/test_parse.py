"""
Tests for the parsing logic.

Run with:  pytest

These need no network, because parsing is separated from fetching. That is why
the split exists: you can test the logic that is most likely to break without
depending on a website being up.
"""

from datetime import date

import pytest

from src.parse import parse_rates

# A cut-down version of a real CNB file, including a currency quoted per 100
# so the normalisation gets tested.
SAMPLE = """14 Oct 2026 #198
Country|Currency|Amount|Code|Rate
Australia|dollar|1|AUD|15.248
Japan|yen|100|JPY|13.900
Indonesia|rupiah|1000|IDR|1.258
USA|dollar|1|USD|23.456
"""


def test_reads_the_date():
    rate_date, _ = parse_rates(SAMPLE)
    assert rate_date == date(2026, 10, 14)


def test_reads_every_currency():
    _, rates = parse_rates(SAMPLE)
    assert len(rates) == 4
    assert {r["code"] for r in rates} == {"AUD", "JPY", "IDR", "USD"}


def test_single_unit_currency_is_unchanged():
    _, rates = parse_rates(SAMPLE)
    usd = next(r for r in rates if r["code"] == "USD")
    assert usd["rate"] == 23.456
    assert usd["rate_per_unit"] == 23.456


def test_hundred_unit_currency_is_normalised():
    """The yen is quoted per 100, so one yen is the rate divided by 100."""
    _, rates = parse_rates(SAMPLE)
    jpy = next(r for r in rates if r["code"] == "JPY")
    assert jpy["rate"] == 13.900
    assert jpy["rate_per_unit"] == 0.139


def test_thousand_unit_currency_is_normalised():
    _, rates = parse_rates(SAMPLE)
    idr = next(r for r in rates if r["code"] == "IDR")
    assert idr["rate_per_unit"] == 0.001258


def test_rejects_a_changed_header():
    """If the CNB changes the file layout, we want to know, not guess."""
    broken = SAMPLE.replace("Country|Currency|Amount|Code|Rate", "Country|Currency|Code|Rate")
    with pytest.raises(ValueError, match="Header changed"):
        parse_rates(broken)


def test_rejects_a_truncated_file():
    with pytest.raises(ValueError, match="at least 3 lines"):
        parse_rates("14 Oct 2026 #198\nCountry|Currency|Amount|Code|Rate")


def test_rejects_a_row_with_missing_fields():
    broken = SAMPLE + "Nowhere|nothing|1|XXX\n"
    with pytest.raises(ValueError, match="Expected 5 fields"):
        parse_rates(broken)
