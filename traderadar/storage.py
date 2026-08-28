"""Output sinks. Every sink shares one signature so the CLI can pick at run time.

sink(prices, symbol, interval, config) -> str describing where the data landed
"""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS prices (
    symbol TEXT,
    date   TEXT,
    open   REAL,
    high   REAL,
    low    REAL,
    close  REAL,
    volume INTEGER,
    PRIMARY KEY (symbol, date)
)
"""

# Re-running the same day must update, not duplicate - hence INSERT OR REPLACE.
UPSERT = "INSERT OR REPLACE INTO prices VALUES (?, ?, ?, ?, ?, ?, ?)"


def _date_format(interval):
    return "%Y-%m-%d" if interval == "1d" else "%Y-%m-%d %H:%M:%S"


def write_csv(prices, symbol, interval, config):
    """One CSV per symbol, overwritten on each run."""
    target = Path(config["csv_path"]) / f"{symbol}_{interval}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(target, index=False)
    return str(target)


def write_sqlite(prices, symbol, interval, config):
    """Upsert the frame into the shared prices table."""
    target = Path(config["db_path"])
    target.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        (
            symbol,
            row.Date.strftime(_date_format(interval)),
            row.Open,
            row.High,
            row.Low,
            row.Close,
            row.Volume,
        )
        for row in prices.itertuples(index=False)
    ]

    with sqlite3.connect(target) as connection:
        connection.execute(SCHEMA)
        connection.executemany(UPSERT, rows)

    return f"{target} (table: prices, {len(rows)} rows)"


# The CLI derives its --output choices from this registry, so adding a sink
# here is the only change needed to expose it.
SINKS = {
    "csv": write_csv,
    "sql": write_sqlite,
}
