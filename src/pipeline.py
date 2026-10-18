"""
Run the whole pipeline: fetch, parse, store.

Run it with:  python -m src.pipeline
"""

import logging
import sys

from src.fetch import fetch_rates
from src.parse import parse_rates
from src.store import save_rates, dates_already_loaded

# Logging rather than print(). The difference matters once something runs on a
# schedule: logs carry timestamps and severity, and can be sent somewhere you
# will actually look when a 3am run fails.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run(date=None):
    """Fetch one day of rates and store them. Returns the number of rows."""
    log.info("Fetching rates from the CNB%s", f" for {date}" if date else " (latest)")

    try:
        raw = fetch_rates(date)
    except Exception as e:
        # Fail loudly and stop. The alternative - catching the error and
        # carrying on - means the pipeline reports success having loaded
        # nothing, which is worse than crashing.
        log.error("Could not fetch rates: %s", e)
        raise

    rate_date, rates = parse_rates(raw)
    log.info("Parsed %d currencies for %s", len(rates), rate_date)

    # A simple data quality check. The CNB publishes somewhere around 30
    # currencies. If we suddenly get 3, something is wrong upstream and we
    # should not quietly load it.
    if len(rates) < 20:
        raise ValueError(f"Only {len(rates)} currencies - expected around 30. Stopping.")

    rows = save_rates(rates)
    log.info("Stored %d rows for %s", rows, rate_date)

    return rows


if __name__ == "__main__":
    try:
        run()
        loaded = dates_already_loaded()
        log.info("Database now holds %d distinct dates", len(loaded))
    except Exception as e:
        log.error("Pipeline failed: %s", e)
        # A non-zero exit code is how a scheduler knows the job failed.
        sys.exit(1)
