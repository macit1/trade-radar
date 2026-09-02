"""Database access: output sinks for writing, queries for reading.

Every sink shares one signature so the CLI can pick at run time:
    sink(prices, symbol, interval, config) -> str describing where the data landed

Readers exist so consumers (the API) never open their own connection.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

import pandas as pd

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

PRICE_COLUMNS = ["symbol", "date", "open", "high", "low", "close", "volume"]


def _date_format(interval):
    return "%Y-%m-%d" if interval == "1d" else "%Y-%m-%d %H:%M:%S"


def _connect(config, create_parent=False):
    """Single place that knows where the database lives and how to open it."""
    target = Path(config["db_path"])
    if create_parent:
        target.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(target)


def write_csv(prices, symbol, interval, config):
    """One CSV per symbol, overwritten on each run."""
    target = Path(config["csv_path"]) / f"{symbol}_{interval}.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(target, index=False)
    return str(target)


def write_sqlite(prices, symbol, interval, config):
    """Upsert the frame into the shared prices table."""
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

    with closing(_connect(config, create_parent=True)) as connection:
        with connection:  # commits on success, rolls back on error
            connection.execute(SCHEMA)
            connection.executemany(UPSERT, rows)

    return f"{config['db_path']} (table: prices, {len(rows)} rows)"


# The CLI derives its --output choices from this registry, so adding a sink
# here is the only change needed to expose it.
SINKS = {
    "csv": write_csv,
    "sql": write_sqlite,
}


def list_symbols(config):
    """Symbols present in the database, alphabetically. Empty list if none yet."""
    if not Path(config["db_path"]).exists():
        return []

    with closing(_connect(config)) as connection:
        try:
            rows = connection.execute(
                "SELECT DISTINCT symbol FROM prices ORDER BY symbol"
            ).fetchall()
        except sqlite3.OperationalError:
            return []  # database file exists but the table was never created

    return [row[0] for row in rows]


def read_prices(symbols, config):
    """Stored bars for the given symbols, oldest first, as a DataFrame."""
    if not symbols or not Path(config["db_path"]).exists():
        return pd.DataFrame(columns=PRICE_COLUMNS)

    placeholders = ", ".join("?" * len(symbols))
    query = (
        f"SELECT {', '.join(PRICE_COLUMNS)} FROM prices "
        f"WHERE symbol IN ({placeholders}) ORDER BY date"
    )

    with closing(_connect(config)) as connection:
        return pd.read_sql_query(
            query, connection, params=list(symbols), parse_dates=["date"]
        )
