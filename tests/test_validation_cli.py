"""Report assembly, exit codes, and the CLI wiring around validation."""

import sqlite3

import pandas as pd
import pytest

import main as cli
from tests.conftest import stored_frame
from traderadar.storage import write_sqlite
from traderadar.validation import ERROR, WARNING, Finding, format_report, validate_store


def seed(config, frame, symbol="TEST"):
    """Put a stored-shape frame into the configured database."""
    fetched = frame.drop(columns=["symbol"]).rename(
        columns={
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )
    write_sqlite(fetched, symbol, "1d", config)


# --------------------------------------------------------------------------
# Reading a store
# --------------------------------------------------------------------------


def test_clean_store_passes(config):
    seed(config, stored_frame())

    report = validate_store(config, asof="2026-08-28")

    assert report.status == "PASS"
    assert report.exit_code() == 0
    assert report.all_findings == []


def test_configured_symbol_absent_from_the_store_is_an_error(config):
    report = validate_store(config, asof="2026-08-28")

    assert report.status == "FAIL"
    assert [f.rule for f in report.all_findings] == ["no-data"]
    assert report.symbols[0].bars == 0


def test_symbols_argument_overrides_the_configured_list(config):
    seed(config, stored_frame(symbol="OTHER"), symbol="OTHER")

    report = validate_store(config, symbols=["OTHER"], asof="2026-08-28")

    assert report.status == "PASS"
    assert [s.symbol for s in report.symbols] == ["OTHER"]


def test_thresholds_come_from_the_config(config):
    """A tighter threshold in config.yaml has to change the outcome."""
    frame = stored_frame()
    # The whole bar moves, not just the close - lifting the close alone would
    # break high >= close and fail on an OHLC error instead of the threshold.
    frame.loc[5, ["open", "high", "low", "close"]] *= 1.10
    seed(config, frame)

    assert validate_store(config, asof="2026-08-28").status == "PASS"

    config["validation"] = {**config["validation"], "extreme_move_pct": 5.0}
    tightened = validate_store(config, asof="2026-08-28")

    assert tightened.status == "WARN"
    assert "extreme-move" in {f.rule for f in tightened.all_findings}


# --------------------------------------------------------------------------
# The NaT crash this module was fixed for
# --------------------------------------------------------------------------


def test_unparseable_date_is_reported_not_raised(config):
    """A store holding mixed date formats used to raise NaT deep in the gap check.

    It has to come back as a FAIL report - a validator that dies on bad data is
    the one thing a validator may not do.
    """
    seed(config, stored_frame())
    with sqlite3.connect(config["db_path"]) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO prices VALUES ('TEST','2026-08-27 15:30:00',1,2,0.5,1.5,10)"
        )

    report = validate_store(config, asof="2026-08-28")

    assert report.status == "FAIL"
    assert "unparseable-date" in {f.rule for f in report.all_findings}


def test_remaining_rows_are_still_checked_after_a_bad_date(config):
    """Reporting the bad row must not abandon the rest of the symbol."""
    frame = stored_frame()
    frame.loc[5, "high"] = 1.0  # a separate, ordinary error
    seed(config, frame)
    with sqlite3.connect(config["db_path"]) as connection:
        connection.execute(
            "INSERT OR REPLACE INTO prices VALUES ('TEST','2026-08-27 15:30:00',1,2,0.5,1.5,10)"
        )

    fired = {f.rule for f in validate_store(config, asof="2026-08-28").all_findings}

    assert {"unparseable-date", "ohlc-invariant"} <= fired


# --------------------------------------------------------------------------
# Exit codes - the contract CI will read
# --------------------------------------------------------------------------


def report_with(*findings):
    report = validate_store.__globals__["Report"](
        db_path="x", asof=pd.Timestamp("2026-08-28")
    )
    report.cross_findings = list(findings)
    return report


@pytest.mark.parametrize(
    "findings, strict, expected",
    [
        ((), False, 0),
        ((), True, 0),
        ((Finding("r", WARNING, "s"),), False, 0),
        ((Finding("r", WARNING, "s"),), True, 1),
        ((Finding("r", ERROR, "s"),), False, 1),
        ((Finding("r", ERROR, "s"),), True, 1),
    ],
)
def test_exit_code_matrix(findings, strict, expected):
    assert report_with(*findings).exit_code(strict=strict) == expected


def test_status_reflects_the_worst_finding():
    assert report_with().status == "PASS"
    assert report_with(Finding("r", WARNING, "s")).status == "WARN"
    assert (
        report_with(Finding("r", WARNING, "s"), Finding("r", ERROR, "s")).status == "FAIL"
    )


def test_report_renders_findings_and_the_summary(config):
    frame = stored_frame()
    frame.loc[5, "volume"] = 0
    seed(config, frame)

    text = format_report(validate_store(config, asof="2026-08-28"))

    assert "zero-volume" in text
    assert "Result: WARN" in text
    assert "1 symbols: 0 pass, 1 warning, 0 failed" in text


def test_strict_is_explained_in_the_report(config):
    frame = stored_frame()
    frame.loc[5, "volume"] = 0
    seed(config, frame)

    text = format_report(validate_store(config, asof="2026-08-28"), strict=True)

    assert "--strict" in text


# --------------------------------------------------------------------------
# CLI wiring
# --------------------------------------------------------------------------


@pytest.fixture
def cli_config(monkeypatch, config):
    """Make `main.py` load our throwaway config instead of config.yaml."""
    monkeypatch.setattr(cli, "load_config", lambda path: config)
    return config


def run_cli(monkeypatch, *args):
    monkeypatch.setattr("sys.argv", ["main.py", *args])
    return cli.main()


def test_validate_only_returns_zero_on_clean_data(monkeypatch, cli_config):
    seed(cli_config, stored_frame())

    assert run_cli(monkeypatch, "--validate-only") == 0


def test_validate_only_returns_one_on_broken_data(monkeypatch, cli_config):
    frame = stored_frame()
    frame.loc[5, "high"] = 1.0
    seed(cli_config, frame)

    assert run_cli(monkeypatch, "--validate-only") == 1


def test_validate_only_never_fetches(monkeypatch, cli_config):
    """The point of the flag: it reads the store and nothing else."""
    seed(cli_config, stored_frame())

    def explode(*args, **kwargs):
        raise AssertionError("--validate-only must not fetch")

    monkeypatch.setattr(cli, "fetch_prices", explode)

    assert run_cli(monkeypatch, "--validate-only") == 0


def test_strict_turns_warnings_into_a_failure(monkeypatch, cli_config):
    frame = stored_frame()
    frame.loc[5, "volume"] = 0  # a warning, not an error
    seed(cli_config, frame)

    assert run_cli(monkeypatch, "--validate-only") == 0
    assert run_cli(monkeypatch, "--validate-only", "--strict") == 1


def test_a_failed_fetch_fails_the_run(monkeypatch, cli_config):
    """A run that dropped a symbol must not report success to a pipeline."""

    def refuse(symbol, price_range, interval):
        raise ValueError(f"no data for {symbol}")

    monkeypatch.setattr(cli, "fetch_prices", refuse)

    assert run_cli(monkeypatch, "--output", "sql", "--no-validate") == 1


def test_no_validate_skips_the_check(monkeypatch, cli_config):
    """Even with a broken store, skipping validation leaves the run green."""
    frame = stored_frame()
    frame.loc[5, "high"] = 1.0
    seed(cli_config, frame)

    def fake_fetch(symbol, price_range, interval):
        return (
            stored_frame()
            .drop(columns=["symbol"])
            .rename(
                columns={
                    "date": "Date",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                }
            )
        )

    monkeypatch.setattr(cli, "fetch_prices", fake_fetch)
    called = []
    monkeypatch.setattr(cli, "run_validation", lambda *a: called.append(a) or 0)

    assert run_cli(monkeypatch, "--output", "sql", "--no-validate") == 0
    assert called == []


def test_unknown_flag_exits_two(monkeypatch, cli_config):
    """argparse owns exit code 2; CI treats it as a usage error, not a data one."""
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "--not-a-flag")

    assert exit_info.value.code == 2


def test_unknown_sink_exits_two(monkeypatch, cli_config):
    with pytest.raises(SystemExit) as exit_info:
        run_cli(monkeypatch, "--output", "parquet")

    assert exit_info.value.code == 2
