"""
Get the exchange rate file from the Czech National Bank.

The CNB publishes a plain text file every working day. There is no API key and
no registration.
"""

import requests

BASE_URL = (
    "https://www.cnb.cz/en/financial-markets/foreign-exchange-market/"
    "central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/daily.txt"
)


def fetch_rates(date=None):
    """
    Download the rate file. With no date, you get the latest published rates.
    With a date, you get that day's rates.

    Returns the raw text. Parsing happens elsewhere.
    """
    params = {}
    if date is not None:
        # The CNB expects DD.MM.YYYY in the query string
        params["date"] = date.strftime("%d.%m.%Y")

    # timeout matters. Without it, a hanging server hangs your pipeline
    # forever instead of failing so you can retry.
    response = requests.get(BASE_URL, params=params, timeout=30)

    # Turns an HTTP error into a Python exception, so the pipeline stops
    # instead of trying to parse an error page as if it were data.
    response.raise_for_status()

    if not response.text.strip():
        raise ValueError("The CNB returned an empty file")

    return response.text
