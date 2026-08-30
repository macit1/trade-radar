"""Rule-by-rule tests for traderadar.validation.

Each rule gets a clean case and a broken one, and every rule with a threshold
also gets the two bars either side of it - a threshold nobody probed at its
boundary is a threshold nobody tested.

The rule functions are private by convention (`_check_*`) but they are the unit
under test here: calling them directly keeps a failure pointing at one rule
instead of at a whole report.
"""

import pandas as pd
import pytest

from tests.conftest import sessions, stored_frame
from traderadar import validation
from traderadar.validation import (
    ERROR,
    SYMBOL_RULES,
    WARNING,
    _check_calendar_drift,
    _check_coverage,
    _check_duplicate_dates,
    _check_extreme_moves,
    _check_flat_and_volume,
    _check_gaps,
    _check_missing_values,
    _check_ohlc_invariants,
    _check_price_domain,
    _check_repeated_bars,
    _check_session_dates,
    _check_staleness,
    last_trading_day,
    trading_days,
)


def rules(finding_list):
    return {finding.rule for finding in finding_list}


def severity_of(finding_list, rule):
    return next(f.severity for f in finding_list if f.rule == rule)


def run_all(frame, settings):
    return [f for rule in SYMBOL_RULES for f in rule(frame, settings)]


# --------------------------------------------------------------------------
# The builder itself. If this fails, every "broken" assertion below is noise.
# --------------------------------------------------------------------------


def test_clean_frame_trips_no_rule(settings):
    assert run_all(stored_frame(), settings) == []


def test_clean_frame_is_not_stale(settings):
    frame = stored_frame(end="2026-08-28")
    assert _check_staleness(frame, settings, pd.Timestamp("2026-08-28")) == []


# --------------------------------------------------------------------------
# Structural errors
# --------------------------------------------------------------------------


@pytest.mark.parametrize("column", ["open", "high", "low", "close", "volume"])
def test_null_in_any_ohlcv_field_is_an_error(settings, column):
    frame = stored_frame()
    frame.loc[3, column] = None

    findings = _check_missing_values(frame, settings)

    assert len(findings) == 1
    assert findings[0].severity == ERROR
    assert findings[0].rule == "missing-values"


def test_duplicate_dates_are_an_error(settings):
    frame = stored_frame(count=5)
    frame = pd.concat([frame, frame.iloc[[2]]], ignore_index=True)

    findings = _check_duplicate_dates(frame, settings)

    assert [f.severity for f in findings] == [ERROR]
    assert frame.loc[2, "date"].date().isoformat() in findings[0].samples


def test_unique_dates_pass(settings):
    assert _check_duplicate_dates(stored_frame(), settings) == []


@pytest.mark.parametrize("price", [0.0, -1.0])
def test_non_positive_price_is_an_error(settings, price):
    frame = stored_frame()
    frame.loc[2, "open"] = price

    findings = _check_price_domain(frame, settings)

    assert rules(findings) == {"non-positive-price"}
    assert findings[0].severity == ERROR


def test_negative_volume_is_an_error(settings):
    frame = stored_frame()
    frame.loc[4, "volume"] = -1

    findings = _check_price_domain(frame, settings)

    assert rules(findings) == {"negative-volume"}
    assert findings[0].severity == ERROR


def test_zero_volume_is_not_a_price_domain_error(settings):
    """Zero volume is a quiet session, not an impossible one."""
    frame = stored_frame()
    frame.loc[4, "volume"] = 0

    assert _check_price_domain(frame, settings) == []


@pytest.mark.parametrize(
    "column, value",
    [
        ("high", 1.0),  # high below open and close
        ("low", 10_000.0),  # low above open and close
    ],
)
def test_broken_ohlc_ordering_is_an_error(settings, column, value):
    frame = stored_frame()
    frame.loc[6, column] = value

    findings = _check_ohlc_invariants(frame, settings)

    assert [f.severity for f in findings] == [ERROR]


def test_high_below_low_is_an_error(settings):
    frame = stored_frame()
    frame.loc[6, ["open", "close"]] = 50.0
    frame.loc[6, "high"] = 40.0
    frame.loc[6, "low"] = 60.0

    assert [f.severity for f in _check_ohlc_invariants(frame, settings)] == [ERROR]


# --------------------------------------------------------------------------
# Session dates
# --------------------------------------------------------------------------


def test_weekend_bar_is_an_error(settings):
    frame = stored_frame()
    frame.loc[0, "date"] = pd.Timestamp("2026-08-29")  # a Saturday

    findings = _check_session_dates(frame, settings)

    assert rules(findings) == {"weekend-bar"}
    assert findings[0].severity == ERROR


def test_intraday_timestamp_is_an_error(settings):
    frame = stored_frame()
    frame.loc[0, "date"] = pd.Timestamp("2026-08-26 15:30:00")

    findings = _check_session_dates(frame, settings)

    assert rules(findings) == {"intraday-timestamp"}
    assert findings[0].severity == ERROR


def test_ordinary_weekdays_pass(settings):
    assert _check_session_dates(stored_frame(), settings) == []


# --------------------------------------------------------------------------
# Gaps and coverage - both threshold rules, both probed at the boundary
# --------------------------------------------------------------------------


def drop_sessions(frame, count, at=10):
    """Remove `count` consecutive sessions, leaving a hole of exactly that size."""
    return frame.drop(index=range(at, at + count)).reset_index(drop=True)


def test_gap_at_the_threshold_passes(settings):
    """Exactly `gap_trading_days` missing is still inside the allowance."""
    frame = drop_sessions(stored_frame(count=60), settings["gap_trading_days"])

    assert _check_gaps(frame, settings) == []


def test_gap_one_session_over_the_threshold_warns(settings):
    frame = drop_sessions(stored_frame(count=60), settings["gap_trading_days"] + 1)

    findings = _check_gaps(frame, settings)

    assert [f.severity for f in findings] == [WARNING]
    assert findings[0].rule == "calendar-gap"


def test_long_weekend_is_not_a_gap(settings):
    """A holiday closure must never read as missing data."""
    # Independence Day 2025 fell on a Friday; the market was shut.
    frame = stored_frame(count=40, end="2025-07-31")

    assert _check_gaps(frame, settings) == []


def test_coverage_inside_tolerance_passes(settings):
    frame = stored_frame(count=100)
    # 4 of 100 sessions missing = 4%, under the 5% default.
    frame = frame.drop(index=[10, 30, 50, 70]).reset_index(drop=True)

    assert _check_coverage(frame, settings) == []


def test_coverage_outside_tolerance_warns(settings):
    frame = stored_frame(count=100)
    frame = frame.drop(index=range(10, 25)).reset_index(drop=True)  # 15%

    findings = _check_coverage(frame, settings)

    assert [f.severity for f in findings] == [WARNING]
    assert findings[0].rule == "thin-coverage"


# --------------------------------------------------------------------------
# Staleness - warn over 2 sessions behind, fail over 5
# --------------------------------------------------------------------------


def stale_by(count):
    """A frame whose newest bar is `count` sessions behind 2026-08-28."""
    available = sessions(count + 40)
    end = available[-1] if count == 0 else available[-(count + 1)]
    return stored_frame(count=30, end=end.date().isoformat())


@pytest.mark.parametrize("behind", [0, 1, 2])
def test_recent_data_is_not_stale(settings, behind):
    assert _check_staleness(stale_by(behind), settings, pd.Timestamp("2026-08-28")) == []


@pytest.mark.parametrize("behind", [3, 5])
def test_moderately_stale_data_warns(settings, behind):
    findings = _check_staleness(stale_by(behind), settings, pd.Timestamp("2026-08-28"))

    assert [f.severity for f in findings] == [WARNING]
    assert findings[0].rule == "stale-data"


@pytest.mark.parametrize("behind", [6, 20])
def test_badly_stale_data_is_an_error(settings, behind):
    findings = _check_staleness(stale_by(behind), settings, pd.Timestamp("2026-08-28"))

    assert [f.severity for f in findings] == [ERROR]


def test_staleness_is_measured_over_a_weekend_without_false_positives(settings):
    """Data current to Friday is not stale when checked on the Monday after."""
    frame = stored_frame(end="2026-08-28")  # Friday

    assert _check_staleness(frame, settings, pd.Timestamp("2026-08-31")) == []


# --------------------------------------------------------------------------
# Anomalies
# --------------------------------------------------------------------------


def test_move_under_the_threshold_passes(settings):
    frame = stored_frame()
    frame.loc[5, "close"] = frame.loc[4, "close"] * 1.20  # 20% < 25%

    assert _check_extreme_moves(frame, settings) == []


def test_move_over_the_threshold_warns(settings):
    frame = stored_frame()
    frame.loc[5, "close"] = frame.loc[4, "close"] * 1.30

    findings = _check_extreme_moves(frame, settings)

    assert [f.severity for f in findings] == [WARNING]
    assert findings[0].rule == "extreme-move"


def make_flat(frame, index, spread):
    """Collapse one bar's range to `spread` around a 100.00 close."""
    frame.loc[index, ["open", "close"]] = 100.0
    frame.loc[index, "high"] = 100.0 + spread / 2
    frame.loc[index, "low"] = 100.0 - spread / 2
    return frame


def test_bar_just_outside_the_flat_tolerance_passes(settings):
    # tolerance is 0.01% of ~100 = 0.01; 0.02 of range is comfortably wider.
    frame = make_flat(stored_frame(), 7, spread=0.02)

    assert _check_flat_and_volume(frame, settings) == []


def test_bar_just_inside_the_flat_tolerance_warns(settings):
    frame = make_flat(stored_frame(), 7, spread=0.005)

    findings = _check_flat_and_volume(frame, settings)

    assert rules(findings) == {"flat-bar"}
    assert findings[0].severity == WARNING


def test_exactly_equal_prices_are_flat(settings):
    """The original definition still holds inside the tolerant one."""
    frame = make_flat(stored_frame(), 7, spread=0.0)

    assert rules(_check_flat_and_volume(frame, settings)) == {"flat-bar"}


def test_zero_volume_alone_warns(settings):
    frame = stored_frame()
    frame.loc[8, "volume"] = 0

    findings = _check_flat_and_volume(frame, settings)

    assert rules(findings) == {"zero-volume"}
    assert findings[0].severity == WARNING


def test_flat_and_zero_volume_together_is_an_error(settings):
    """Either alone is a quiet day; both together is a placeholder row."""
    frame = make_flat(stored_frame(), 9, spread=0.0)
    frame.loc[9, "volume"] = 0

    findings = _check_flat_and_volume(frame, settings)

    assert rules(findings) == {"flat-and-zero-volume"}
    assert severity_of(findings, "flat-and-zero-volume") == ERROR


def test_repeated_bar_warns(settings):
    frame = stored_frame()
    columns = ["open", "high", "low", "close", "volume"]
    frame.loc[11, columns] = frame.loc[10, columns].values

    findings = _check_repeated_bars(frame, settings)

    assert [f.severity for f in findings] == [WARNING]
    assert findings[0].rule == "repeated-bar"


# --------------------------------------------------------------------------
# Cross-symbol calendar drift
# --------------------------------------------------------------------------


def test_aligned_symbols_do_not_drift(settings):
    frames = {name: stored_frame(symbol=name) for name in ("AAA", "BBB", "CCC")}

    assert _check_calendar_drift(frames, settings) == []


def test_a_single_symbol_cannot_drift(settings):
    """With nothing to compare against, the rule has to stay quiet."""
    assert _check_calendar_drift({"AAA": stored_frame(symbol="AAA")}, settings) == []


def test_symbol_missing_a_session_the_others_have_is_an_error(settings):
    frames = {name: stored_frame(symbol=name) for name in ("AAA", "BBB", "CCC")}
    frames["CCC"] = frames["CCC"].drop(index=[15, 16]).reset_index(drop=True)

    findings = _check_calendar_drift(frames, settings)

    assert [f.severity for f in findings] == [ERROR]
    assert "CCC is missing 2 sessions" in findings[0].summary


def test_symbol_with_a_session_nobody_else_traded_is_an_error(settings):
    frames = {name: stored_frame(symbol=name, count=60) for name in ("AAA", "BBB", "CCC")}
    extra = frames["AAA"].iloc[[0]].copy()
    # 4 July 2026 is a Saturday, so the exchanges close on Friday the 3rd. A bar
    # on that day is one no other symbol can have.
    extra["date"] = pd.Timestamp("2026-07-03")
    frames["AAA"] = (
        pd.concat([frames["AAA"], extra]).sort_values("date").reset_index(drop=True)
    )

    findings = _check_calendar_drift(frames, settings)

    assert [f.severity for f in findings] == [ERROR]
    assert "no other symbol traded" in findings[0].summary


def test_shorter_history_is_not_drift(settings):
    """A newly added symbol has less history; that is not a missing session."""
    frames = {name: stored_frame(symbol=name, count=40) for name in ("AAA", "BBB")}
    frames["NEW"] = stored_frame(symbol="NEW", count=10)

    assert _check_calendar_drift(frames, settings) == []


# --------------------------------------------------------------------------
# Calendar helpers
# --------------------------------------------------------------------------


def test_weekends_are_not_trading_days():
    days = trading_days(pd.Timestamp("2026-08-24"), pd.Timestamp("2026-08-30"))

    assert list(days.dayofweek) == [0, 1, 2, 3, 4]


def test_good_friday_is_closed_although_it_is_not_a_federal_holiday():
    days = trading_days(pd.Timestamp("2026-04-03"), pd.Timestamp("2026-04-03"))

    assert len(days) == 0


def test_columbus_day_is_open_although_it_is_a_federal_holiday():
    days = trading_days(pd.Timestamp("2026-10-12"), pd.Timestamp("2026-10-12"))

    assert len(days) == 1


def test_last_trading_day_rolls_back_over_a_weekend():
    assert last_trading_day("2026-08-30") == pd.Timestamp("2026-08-28")


def test_last_trading_day_returns_the_day_itself_when_open():
    assert last_trading_day("2026-08-28") == pd.Timestamp("2026-08-28")


def test_trading_days_tolerates_missing_bounds():
    """The gap rule feeds this NaT when a date fails to parse; it must not raise."""
    assert len(validation.trading_days(pd.NaT, pd.Timestamp("2026-08-28"))) == 0
    assert len(validation.trading_days(pd.Timestamp("2026-08-28"), pd.NaT)) == 0
