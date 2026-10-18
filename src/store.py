"""
Store the rates in a SQLite database.

SQLite needs no server and no setup - the database is just a file. That keeps
the first version simple. Swapping it for PostgreSQL later changes this file
and nothing else, which is the point of keeping storage separate.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "rates.db"

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS exchange_rates (
    rate_date     DATE NOT NULL,
    code          TEXT NOT NULL,
    country       TEXT NOT NULL,
    currency      TEXT NOT NULL,
    amount        INTEGER NOT NULL,
    rate          REAL NOT NULL,
    rate_per_unit REAL NOT NULL,
    loaded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- This is what makes the pipeline idempotent.
    --
    -- One date plus one currency can only appear once. Combined with
    -- INSERT OR REPLACE below, running the pipeline twice on the same day
    -- updates the row instead of creating a duplicate.
    --
    -- Without this, every re-run silently doubles your data, and you find
    -- out when someone's average is half what it should be.
    PRIMARY KEY (rate_date, code)
);
"""


def get_connection():
    """Open the database, creating the file and table if they do not exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(CREATE_TABLE)
    conn.commit()
    return conn


def save_rates(rates):
    """Write rates to the database. Returns how many rows were written."""
    conn = get_connection()

    rows = [
        (
            r["rate_date"],
            r["code"],
            r["country"],
            r["currency"],
            r["amount"],
            r["rate"],
            r["rate_per_unit"],
        )
        for r in rates
    ]

    conn.executemany(
        """
        INSERT OR REPLACE INTO exchange_rates
            (rate_date, code, country, currency, amount, rate, rate_per_unit)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()

    return len(rows)


def dates_already_loaded():
    """
    Which dates do we already have?

    This is the beginning of incremental loading. Rather than re-downloading
    everything every run, you ask the database what is missing and fetch only
    that.
    """
    conn = get_connection()
    result = conn.execute("SELECT DISTINCT rate_date FROM exchange_rates").fetchall()
    conn.close()
    return {row[0] for row in result}
