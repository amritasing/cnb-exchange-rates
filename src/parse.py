"""
Turn the raw text from the CNB into clean rows.

This is kept separate from fetching on purpose. Parsing needs no network, so it
can be tested with a saved sample - which is what tests/test_parse.py does.
"""

from datetime import datetime


def parse_rates(raw_text):
    """
    Take the raw CNB file and return (date, list of rate dictionaries).

    The file looks like this:

        14 Oct 2026 #198
        Country|Currency|Amount|Code|Rate
        Australia|dollar|1|AUD|15.248
        Japan|yen|100|JPY|9.876

    Line 1 is the date plus a publication number.
    Line 2 is the header.
    Everything after that is data, separated by pipes.
    """
    lines = [line.strip() for line in raw_text.strip().split("\n") if line.strip()]

    if len(lines) < 3:
        raise ValueError(f"File looks wrong - expected at least 3 lines, got {len(lines)}")

    # Line 1: "14 Oct 2026 #198" - we want the date, not the number after the #
    date_part = lines[0].split("#")[0].strip()
    rate_date = datetime.strptime(date_part, "%d %b %Y").date()

    # Line 2: check the header is what we expect. If the CNB ever changes the
    # file layout, we want to fail loudly here rather than load wrong data.
    expected_header = "Country|Currency|Amount|Code|Rate"
    if lines[1] != expected_header:
        raise ValueError(f"Header changed. Expected '{expected_header}', got '{lines[1]}'")

    rates = []
    for line in lines[2:]:
        fields = line.split("|")
        if len(fields) != 5:
            raise ValueError(f"Expected 5 fields, got {len(fields)} in line: {line}")

        country, currency, amount, code, rate = fields
        amount = int(amount)
        rate = float(rate)

        # THE IMPORTANT BIT.
        #
        # The CNB does not quote every currency per single unit. The yen is
        # quoted per 100, the Indonesian rupiah per 1000. So the raw rate
        # column is not comparable across currencies.
        #
        # If you ignore this, your yen rate is 100 times wrong and nobody
        # notices until someone converts a real amount of money.
        #
        # We keep the original values AND store a normalised per-unit rate,
        # so the raw data is still auditable but the clean number is usable.
        rate_per_unit = rate / amount

        rates.append({
            "rate_date": rate_date,
            "country": country,
            "currency": currency,
            "amount": amount,
            "code": code,
            "rate": rate,
            "rate_per_unit": round(rate_per_unit, 6),
        })

    return rate_date, rates
