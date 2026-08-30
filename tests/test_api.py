"""The read-only FastAPI surface: /symbols and /prices.

The app reads config through a cached `get_config`, so each test points that at
a throwaway database rather than at the real config.yaml.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app, get_config
from tests.conftest import fetched_frame
from traderadar.storage import write_sqlite


@pytest.fixture
def client(monkeypatch, config):
    monkeypatch.setattr("backend.main.get_config", lambda: config)
    get_config.cache_clear()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded(config):
    """Two symbols sharing the same sessions."""
    frame = fetched_frame(count=5)
    write_sqlite(frame, "AAA", "1d", config)
    write_sqlite(frame, "BBB", "1d", config)
    return frame


# --------------------------------------------------------------------------
# /symbols
# --------------------------------------------------------------------------


def test_symbols_on_an_empty_store_is_an_empty_list(client):
    """Nothing stored yet is not a missing resource, so 200 and [], not 404."""
    response = client.get("/symbols")

    assert response.status_code == 200
    assert response.json() == []


def test_symbols_lists_what_is_stored(client, seeded):
    response = client.get("/symbols")

    assert response.status_code == 200
    assert response.json() == ["AAA", "BBB"]


# --------------------------------------------------------------------------
# /prices
# --------------------------------------------------------------------------


def test_prices_requires_a_symbol(client):
    assert client.get("/prices").status_code == 422


def test_prices_returns_bars_for_one_symbol(client, seeded):
    response = client.get("/prices", params={"symbols": "AAA"})

    assert response.status_code == 200
    assert len(response.json()) == 5


def test_prices_takes_a_repeated_parameter_not_a_joined_string(client, seeded):
    """?symbols=AAA&symbols=BBB - the frontend builds it this way."""
    response = client.get("/prices?symbols=AAA&symbols=BBB")

    assert response.status_code == 200
    assert {bar["symbol"] for bar in response.json()} == {"AAA", "BBB"}
    assert len(response.json()) == 10


def test_a_comma_joined_list_is_not_split(client, seeded):
    """Documenting the contract: one parameter is one symbol."""
    response = client.get("/prices", params={"symbols": "AAA,BBB"})

    assert response.status_code == 200
    assert response.json() == []


def test_unknown_symbols_are_absent_rather_than_an_error(client, seeded):
    response = client.get("/prices?symbols=AAA&symbols=NOPE")

    assert response.status_code == 200
    assert {bar["symbol"] for bar in response.json()} == {"AAA"}


def test_prices_on_an_empty_store_is_an_empty_list(client):
    response = client.get("/prices", params={"symbols": "AAA"})

    assert response.status_code == 200
    assert response.json() == []


# --------------------------------------------------------------------------
# Response shape - what the chart library depends on
# --------------------------------------------------------------------------


def test_a_bar_carries_exactly_the_documented_fields(client, seeded):
    bar = client.get("/prices", params={"symbols": "AAA"}).json()[0]

    assert set(bar) == {"symbol", "date", "open", "high", "low", "close", "volume"}


def test_date_is_a_plain_string(client, seeded):
    """lightweight-charts takes 'YYYY-MM-DD' as its time; no conversion allowed."""
    bar = client.get("/prices", params={"symbols": "AAA"}).json()[0]

    assert isinstance(bar["date"], str)
    assert len(bar["date"]) == len("YYYY-MM-DD")


def test_bars_come_back_oldest_first(client, seeded):
    dates = [bar["date"] for bar in client.get("/prices?symbols=AAA").json()]

    assert dates == sorted(dates)


def test_missing_values_serialise_as_null(client, config):
    """The frame holds NaN; JSON has to carry null, not the string 'NaN'."""
    frame = fetched_frame(count=3)
    frame.loc[1, "Volume"] = None
    write_sqlite(frame, "AAA", "1d", config)

    bars = client.get("/prices", params={"symbols": "AAA"}).json()

    assert bars[1]["volume"] is None
