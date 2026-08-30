"""Parsing of the Yahoo chart response, against canned payloads only.

No test here touches the network: `mock_yahoo` swaps `requests.get`, and the
autouse lock in conftest fails anything that slips past it.
"""

import pandas as pd
import pytest
import requests

from traderadar.fetcher import COLUMNS, fetch_prices


def test_parses_a_complete_response(mock_yahoo, yahoo_payload):
    mock_yahoo(yahoo_payload())

    frame = fetch_prices("TEST", "3y", "1d")

    assert list(frame.columns) == COLUMNS
    assert len(frame) == 2
    assert frame["Close"].tolist() == [101.0, 102.0]


def test_sends_the_range_and_interval_it_was_given(mock_yahoo, yahoo_payload):
    calls = mock_yahoo(yahoo_payload())

    fetch_prices("MSFT", "1mo", "1d")

    assert calls["params"] == {"range": "1mo", "interval": "1d"}
    assert "MSFT" in calls["url"]


def test_sends_a_browser_user_agent(mock_yahoo, yahoo_payload):
    """Yahoo answers a bare client differently; the header is load-bearing."""
    calls = mock_yahoo(yahoo_payload())

    fetch_prices("TEST", "3y", "1d")

    assert "Mozilla" in calls["headers"]["User-Agent"]


def test_sets_a_timeout(mock_yahoo, yahoo_payload):
    calls = mock_yahoo(yahoo_payload())

    fetch_prices("TEST", "3y", "1d")

    assert calls["timeout"] > 0


def test_index_is_reset(mock_yahoo, yahoo_payload):
    """Dropping partial bars leaves holes; callers index by position."""
    mock_yahoo(
        yahoo_payload(
            timestamps=(1756166400, 1756252800, 1756339200),
            opens=(100.0, None, 102.0),
            highs=(102.0, None, 104.0),
            lows=(99.0, None, 101.0),
            closes=(101.0, None, 103.0),
            volumes=(1, 2, 3),
        )
    )

    frame = fetch_prices("TEST", "3y", "1d")

    assert frame.index.tolist() == [0, 1]


# --------------------------------------------------------------------------
# Timestamps
# --------------------------------------------------------------------------


def test_daily_bars_are_normalised_to_midnight(mock_yahoo, yahoo_payload):
    mock_yahoo(yahoo_payload())

    frame = fetch_prices("TEST", "3y", "1d")

    assert (frame["Date"].dt.normalize() == frame["Date"]).all()


def test_timestamps_are_converted_to_the_exchange_calendar(mock_yahoo, yahoo_payload):
    """A UTC epoch at 00:00 is still the previous evening in New York.

    Keeping UTC would file some bars under the wrong session, so the exchange
    timezone from the payload decides the date.
    """
    mock_yahoo(
        yahoo_payload(
            timestamps=(1756166400,),
            opens=(1.0,),
            highs=(2.0,),
            lows=(0.5,),
            closes=(1.5,),
            volumes=(10,),
        )
    )

    frame = fetch_prices("TEST", "3y", "1d")

    expected = (
        pd.to_datetime([1756166400], unit="s", utc=True)
        .tz_convert("America/New_York")
        .tz_localize(None)
        .normalize()[0]
    )
    assert frame["Date"].iloc[0] == expected


def test_dates_carry_no_timezone(mock_yahoo, yahoo_payload):
    """SQLite stores a string; a tz-aware timestamp would serialise differently."""
    mock_yahoo(yahoo_payload())

    assert fetch_prices("TEST", "3y", "1d")["Date"].dt.tz is None


def test_intraday_intervals_keep_their_time(mock_yahoo, yahoo_payload):
    mock_yahoo(
        yahoo_payload(
            timestamps=(1756215000,),
            opens=(1.0,),
            highs=(2.0,),
            lows=(0.5,),
            closes=(1.5,),
            volumes=(10,),
        )
    )

    frame = fetch_prices("TEST", "5d", "1h")

    assert frame["Date"].iloc[0] != frame["Date"].iloc[0].normalize()


# --------------------------------------------------------------------------
# Partial and malformed responses
# --------------------------------------------------------------------------


def test_the_running_session_bar_is_dropped(mock_yahoo, yahoo_payload):
    """Yahoo publishes today's bar before the close with OHLC still empty."""
    mock_yahoo(
        yahoo_payload(
            timestamps=(1756166400, 1756252800),
            opens=(100.0, None),
            highs=(102.0, None),
            lows=(99.0, None),
            closes=(101.0, None),
            volumes=(1_000_000, 0),
        )
    )

    frame = fetch_prices("TEST", "3y", "1d")

    assert len(frame) == 1


def test_a_response_of_only_partial_bars_raises(mock_yahoo, yahoo_payload):
    mock_yahoo(
        yahoo_payload(
            timestamps=(1756166400,),
            opens=(None,),
            highs=(None,),
            lows=(None,),
            closes=(None,),
            volumes=(None,),
        )
    )

    with pytest.raises(ValueError, match="Empty price series"):
        fetch_prices("TEST", "3y", "1d")


def test_a_yahoo_error_payload_raises_with_the_symbol(mock_yahoo, yahoo_payload):
    mock_yahoo(yahoo_payload(error={"code": "Not Found", "description": "No data"}))

    with pytest.raises(ValueError, match="BADTICK"):
        fetch_prices("BADTICK", "3y", "1d")


def test_an_empty_result_list_raises(mock_yahoo, yahoo_payload):
    mock_yahoo(yahoo_payload(result=False))

    with pytest.raises(ValueError, match="is the ticker valid"):
        fetch_prices("BADTICK", "3y", "1d")


def test_an_http_error_propagates(mock_yahoo, yahoo_payload):
    """A 404 is not a data problem to paper over; the CLI counts it as a failure."""
    mock_yahoo(yahoo_payload(), status_error=requests.HTTPError("404 Not Found"))

    with pytest.raises(requests.HTTPError):
        fetch_prices("TEST", "3y", "1d")


# --------------------------------------------------------------------------
# The network lock itself
# --------------------------------------------------------------------------


def test_live_requests_are_blocked_in_the_suite():
    """Proves the guard works, so 'no test hits Yahoo' is enforced, not assumed."""
    with pytest.raises(RuntimeError, match="live network access is disabled"):
        requests.get("https://query1.finance.yahoo.com/v8/finance/chart/AAPL", timeout=1)
