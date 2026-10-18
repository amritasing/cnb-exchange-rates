# Czech National Bank Exchange Rate Pipeline

A small, tested data pipeline that collects the Czech National Bank's daily
exchange rate fixing, normalises it, and stores it in a local database.

Built as a first step toward a larger incremental pipeline. The design priority
is correctness and failing loudly rather than feature count.

---

## The problem

The CNB publishes exchange rates every working day as a plain text file. It
looks simple, and it contains one trap that makes naive loading wrong.

```
14 Oct 2026 #198
Country|Currency|Amount|Code|Rate
Australia|dollar|1|AUD|15.248
Japan|yen|100|JPY|13.900
Indonesia|rupiah|1000|IDR|1.258
```

**Rates are not quoted per single unit.** The Australian dollar is quoted per 1,
the Japanese yen per 100, the Indonesian rupiah per 1000. A pipeline that loads
the `Rate` column and treats it as a per-unit price has a yen rate that is 100
times too large, and nobody notices until someone converts real money.

This pipeline keeps the original `amount` and `rate` columns so the source data
stays auditable, and adds a normalised `rate_per_unit` column that is safe to
compare across currencies.

---

## How it works

```
   CNB website                src/fetch.py      HTTP request, timeout, error check
        │
        ▼
   raw text                   src/parse.py      date, header check, field check,
        │                                       unit normalisation
        ▼
   list of rates              src/store.py      SQLite, primary key on
        │                                       (rate_date, code)
        ▼
   exchange_rates table
```

Fetching, parsing and storing are separate modules on purpose:

- **Parsing is testable without a network.** The logic most likely to break is
  the parsing, and it can be tested against a saved sample rather than
  depending on a website being up.
- **Storage can be swapped.** Moving from SQLite to PostgreSQL changes one file.

---

## Design decisions

**The pipeline is idempotent.** The table has a primary key on
`(rate_date, code)` and writes use `INSERT OR REPLACE`. Running it twice on the
same day updates the rows rather than duplicating them. Without this, every
re-run would silently double the data.

**It fails loudly instead of degrading quietly.** The header is checked against
the expected layout, every row is checked for the right number of fields, and
the run stops if fewer than 20 currencies arrive when roughly 30 are expected.
A pipeline that catches errors and carries on reports success having loaded
nothing, which is worse than crashing.

**Requests have a timeout.** Without one, a hanging server hangs the pipeline
indefinitely instead of failing so it can be retried.

**It uses logging, not print.** Logs carry timestamps and severity levels, which
matters as soon as something runs on a schedule and fails at 3am.

**It exits with a non-zero code on failure**, which is how a scheduler knows the
job did not succeed.

---

## Running it

```bash
# install dependencies
pip install -r requirements.txt

# run the pipeline
python -m src.pipeline

# run the tests
pytest
```

The database is written to `data/rates.db` and is excluded from version control.

---

## Testing

The test suite covers the parsing logic, including:

- the date is read correctly from the header line
- every currency in the file is captured
- single-unit currencies are unchanged
- currencies quoted per 100 and per 1000 are correctly normalised
- a changed header is rejected rather than silently misread
- a truncated file is rejected
- a row with missing fields is rejected

```bash
pytest -v
```

---

## What this does not do yet

Stated deliberately, because knowing the limits of your own work matters more
than pretending there are none.

- **No incremental backfill.** `store.dates_already_loaded()` exists as the
  foundation for it, but the pipeline currently fetches one day at a time.
- **No scheduling.** It runs when invoked. Orchestration with Airflow is the
  next step.
- **No handling of non-publication days.** The CNB does not publish on weekends
  or Czech public holidays, and the pipeline does not yet distinguish "no data
  published" from "fetch failed."
- **No alerting.** Failures are logged and the exit code is set, but nothing
  notifies anyone.

---

## Next steps

1. Incremental backfill: find missing dates and fetch only those
2. Handle weekends and public holidays explicitly
3. Orchestrate with Airflow, with retries and failure alerts
4. Move storage to PostgreSQL
5. Add a transformation layer in dbt with tests on the output
6. Containerise with Docker

---

## Source

Czech National Bank, central bank exchange rate fixing. Published daily on
working days, no API key required.

https://www.cnb.cz/en/financial-markets/foreign-exchange-market/central-bank-exchange-rate-fixing/central-bank-exchange-rate-fixing/
