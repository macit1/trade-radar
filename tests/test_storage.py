"""Sinks and read queries in traderadar.storage, against a throwaway database."""

import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from tests.conftest import fetched_frame
from traderadar.storage import (
    SINKS,
    list_symbols,
    read_prices,
    write_csv,
    write_sqlite,
)


def row_count(config):
    with sqlite3.connect(config["db_path"]) as connection:
        return connection.execute("SELECT COUNT(*) FROM prices").fetchone()[0]


# --------------------------------------------------------------------------
# The sink registry the CLI builds its --output choices from
# --------------------------------------------------------------------------


def test_sink_registry_exposes_both_sinks():
    assert set(SINKS) == {"csv", "sql"}


def test_every_sink_shares_one_signature(config, tmp_path):
    """The CLI calls them interchangeably, so they have to stay interchangeable."""
    frame = fetched_frame(count=5)

    for name, sink in SINKS.items():
        target = sink(frame, "TEST", "1d", config)
        assert isinstance(target, str) and target, name


# --------------------------------------------------------------------------
# SQLite sink
# --------------------------------------------------------------------------


def test_write_sqlite_creates_the_database_and_its_parent(config):
    write_sqlite(fetched_frame(count=5), "TEST", "1d", config)

    assert Path(config["db_path"]).exists()
    assert row_count(config) == 5


def test_rerunning_updates_instead_of_duplicating(config):
    """INSERT OR REPLACE on (symbol, date): a second run must not grow the table."""
    frame = fetched_frame(count=5)
    write_sqlite(frame, "TEST", "1d", config)

    corrected = frame.copy()
    corrected["Close"] = corrected["Close"] + 10
    write_sqlite(corrected, "TEST", "1d", config)

    assert row_count(config) == 5

    stored = read_prices(["TEST"], config)
    assert stored["close"].tolist() == pytest.approx(corrected["Close"].tolist())


def test_symbols_do_not_overwrite_each_other(config):
    """The key is (symbol, date) - the same dates for two symbols coexist."""
    frame = fetched_frame(count=5)
    write_sqlite(frame, "AAA", "1d", config)
    write_sqlite(frame, "BBB", "1d", config)

    assert row_count(config) == 10
    assert list_symbols(config) == ["AAA", "BBB"]


def test_daily_bars_are_stored_as_plain_dates(config):
    write_sqlite(fetched_frame(count=3), "TEST", "1d", config)

    with sqlite3.connect(config["db_path"]) as connection:
        stored = [row[0] for row in connection.execute("SELECT date FROM prices")]

    assert all(len(value) == len("YYYY-MM-DD") for value in stored)


def test_intraday_bars_keep_their_time(config):
    """A non-daily interval has to stay distinguishable inside the same key."""
    frame = fetched_frame(count=3)
    frame["Date"] = frame["Date"] + pd.Timedelta(hours=15, minutes=30)

    write_sqlite(frame, "TEST", "1h", config)

    with sqlite3.connect(config["db_path"]) as connection:
        stored = [row[0] for row in connection.execute("SELECT date FROM prices")]

    assert all(value.endswith("15:30:00") for value in stored)


# --------------------------------------------------------------------------
# CSV sink
# --------------------------------------------------------------------------


def test_write_csv_names_the_file_after_symbol_and_interval(config):
    target = write_csv(fetched_frame(count=4), "TEST", "1d", config)

    assert Path(target).name == "TEST_1d.csv"
    assert Path(target).exists()


def test_write_csv_round_trips_the_frame(config):
    frame = fetched_frame(count=4)

    target = write_csv(frame, "TEST", "1d", config)
    reloaded = pd.read_csv(target, parse_dates=["Date"])

    assert list(reloaded.columns) == list(frame.columns)
    assert reloaded["Close"].tolist() == pytest.approx(frame["Close"].tolist())


def test_write_csv_overwrites_rather_than_appending(config):
    write_csv(fetched_frame(count=4), "TEST", "1d", config)
    target = write_csv(fetched_frame(count=2), "TEST", "1d", config)

    assert len(pd.read_csv(target)) == 2


# --------------------------------------------------------------------------
# Read queries - the API's only door to the store
# --------------------------------------------------------------------------


def test_list_symbols_on_a_missing_database_is_empty(config):
    assert list_symbols(config) == []


def test_list_symbols_on_a_database_without_the_table_is_empty(config):
    """The file can exist before the CLI has ever written a bar."""
    sqlite3.connect(config["db_path"]).close()

    assert list_symbols(config) == []


def test_list_symbols_is_sorted(config):
    for symbol in ("MSFT", "AAPL", "NVDA"):
        write_sqlite(fetched_frame(count=2), symbol, "1d", config)

    assert list_symbols(config) == ["AAPL", "MSFT", "NVDA"]


def test_read_prices_returns_an_empty_frame_with_columns_when_nothing_is_stored(config):
    frame = read_prices(["TEST"], config)

    assert frame.empty
    assert list(frame.columns) == [
        "symbol",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]


def test_read_prices_with_no_symbols_is_empty(config):
    write_sqlite(fetched_frame(count=3), "TEST", "1d", config)

    assert read_prices([], config).empty


def test_read_prices_filters_to_the_requested_symbols(config):
    write_sqlite(fetched_frame(count=3), "AAA", "1d", config)
    write_sqlite(fetched_frame(count=3), "BBB", "1d", config)

    frame = read_prices(["AAA"], config)

    assert set(frame["symbol"]) == {"AAA"}


def test_read_prices_returns_oldest_first(config):
    write_sqlite(fetched_frame(count=10), "TEST", "1d", config)

    dates = read_prices(["TEST"], config)["date"]

    assert dates.is_monotonic_increasing


def test_read_prices_parses_dates(config):
    write_sqlite(fetched_frame(count=3), "TEST", "1d", config)

    frame = read_prices(["TEST"], config)

    assert pd.api.types.is_datetime64_any_dtype(frame["date"])


def test_unknown_symbols_are_simply_absent(config):
    write_sqlite(fetched_frame(count=3), "AAA", "1d", config)

    frame = read_prices(["AAA", "NOPE"], config)

    assert set(frame["symbol"]) == {"AAA"}
