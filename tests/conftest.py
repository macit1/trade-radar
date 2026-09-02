"""Shared fixtures and synthetic data builders.

Two frame shapes exist in this codebase and the tests need both:

    fetched  Date/Open/High/Low/Close/Volume  - what fetcher.py returns and the
             sinks in storage.py consume
    stored   symbol/date/open/.../volume      - what read_prices returns and the
             validation rules consume

The builders below produce a *clean* frame in each shape: real trading sessions,
a gentle price ramp, varying volume. Clean means no validation rule fires, which
`test_validation.py` asserts before anything else - a builder that quietly
tripped a rule would make every "broken" test meaningless.
"""

import pandas as pd
import pytest
import requests

from traderadar.validation import DEFAULTS, trading_days

CLEAN_END = "2026-08-28"


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch):
    """Fail any test that reaches the network instead of mocking it.

    Patched at the adapter, below `requests.get`, so a test that legitimately
    fakes `requests.get` never trips it while a forgotten mock does. This turns
    "no test hits live Yahoo" from a convention into something enforced.
    """

    def refuse(*args, **kwargs):
        raise RuntimeError(
            "live network access is disabled in tests - mock requests.get instead"
        )

    monkeypatch.setattr("requests.adapters.HTTPAdapter.send", refuse)


def sessions(count, end=CLEAN_END):
    """The last `count` US trading sessions ending on `end`."""
    end = pd.Timestamp(end)
    # Twice the calendar span plus a month comfortably covers weekends/holidays.
    start = end - pd.Timedelta(days=count * 2 + 30)
    return trading_days(start, end)[-count:]


def stored_frame(symbol="TEST", count=40, end=CLEAN_END, base=100.0):
    """A clean frame in the shape `read_prices` returns."""
    dates = sessions(count, end)
    # The ramp matters: identical consecutive bars would trip `repeated-bar`,
    # and a flat high/low would trip `flat-bar`.
    close = [base + index * 0.25 for index in range(len(dates))]
    return pd.DataFrame(
        {
            "symbol": symbol,
            "date": dates,
            "open": [value - 0.10 for value in close],
            "high": [value + 0.80 for value in close],
            "low": [value - 0.90 for value in close],
            "close": close,
            "volume": [1_000_000 + index * 1_000 for index in range(len(dates))],
        }
    )


def fetched_frame(count=40, end=CLEAN_END, base=100.0):
    """The same bars in the shape `fetch_prices` returns."""
    frame = stored_frame(count=count, end=end, base=base).drop(columns=["symbol"])
    return frame.rename(
        columns={
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )


@pytest.fixture
def settings():
    """Thresholds as the rules see them when config.yaml says nothing."""
    return dict(DEFAULTS)


@pytest.fixture
def config(tmp_path):
    """A config pointing every sink at a throwaway directory."""
    return {
        "symbols": ["TEST"],
        "interval": "1d",
        "range": "3y",
        "output": ["sql"],
        "db_path": str(tmp_path / "test.db"),
        "csv_path": str(tmp_path / "raw"),
        "validation": dict(DEFAULTS),
    }


@pytest.fixture
def yahoo_payload():
    """Factory for a Yahoo chart response body.

    Defaults to two complete daily bars; every piece is overridable so a test
    can describe exactly the malformed response it cares about.
    """

    def build(
        timestamps=(1756166400, 1756252800),  # 2026-08-26, 2026-08-27 UTC midnight
        opens=(100.0, 101.0),
        highs=(102.0, 103.0),
        lows=(99.0, 100.0),
        closes=(101.0, 102.0),
        volumes=(1_000_000, 1_100_000),
        timezone="America/New_York",
        error=None,
        result=True,
    ):
        if error is not None:
            return {"chart": {"result": None, "error": error}}
        if not result:
            return {"chart": {"result": [], "error": None}}
        return {
            "chart": {
                "error": None,
                "result": [
                    {
                        "meta": {"exchangeTimezoneName": timezone},
                        "timestamp": list(timestamps),
                        "indicators": {
                            "quote": [
                                {
                                    "open": list(opens),
                                    "high": list(highs),
                                    "low": list(lows),
                                    "close": list(closes),
                                    "volume": list(volumes),
                                }
                            ]
                        },
                    }
                ],
            }
        }

    return build


@pytest.fixture
def mock_yahoo(monkeypatch):
    """Point `requests.get` at a canned payload and capture the call."""
    calls = {}

    def install(payload, status_error=None):
        class Response:
            def raise_for_status(self):
                if status_error:
                    raise status_error

            def json(self):
                return payload

        def fake_get(url, params=None, headers=None, timeout=None):
            calls.update(url=url, params=params, headers=headers, timeout=timeout)
            return Response()

        monkeypatch.setattr(requests, "get", fake_get)
        return calls

    return install
