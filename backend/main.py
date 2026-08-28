"""FastAPI backend - serves the SQLite store that the CLI fills.

Run with:  uvicorn backend.main:app --reload

Read-only, like the Streamlit dashboard: it never fetches from Yahoo. All
database access goes through traderadar.storage, so no connection logic or SQL
lives here.
"""

from functools import lru_cache

from fastapi import FastAPI, Query
from pydantic import BaseModel

from traderadar.storage import list_symbols, read_prices
from traderadar.utils import load_config

app = FastAPI(
    title="TradeRadar API",
    version="0.1.0",
    description="Daily OHLCV bars from the local TradeRadar store.",
)


class PriceBar(BaseModel):
    """One daily bar.

    `date` stays a 'YYYY-MM-DD' string rather than a datetime: that is how it is
    stored, and it is also what lightweight-charts expects for its `time` field,
    so the frontend needs no conversion.
    """

    symbol: str
    date: str
    open: float | None
    high: float | None
    low: float | None
    close: float | None
    volume: int | None


@lru_cache
def get_config():
    """config.yaml does not change while the server runs, so read it once."""
    return load_config()


def _to_records(frame):
    """DataFrame -> JSON-ready dicts: dates as strings, missing values as null."""
    frame = frame.assign(date=frame["date"].dt.strftime("%Y-%m-%d"))
    return frame.astype(object).where(frame.notna(), None).to_dict(orient="records")


@app.get("/symbols", response_model=list[str])
def get_symbols():
    """Every symbol in the store.

    An empty store returns [] rather than 404 - nothing stored yet is not a
    missing resource.
    """
    return list_symbols(get_config())


@app.get("/prices", response_model=list[PriceBar])
def get_prices(
    symbols: list[str] = Query(
        ...,
        description="Repeat per symbol: ?symbols=MSFT&symbols=NVDA",
        examples=["MSFT"],
    ),
):
    """Daily OHLCV bars for the given symbols, oldest first.

    One endpoint feeds both chart types: a line chart reads close, a candlestick
    chart reads open/high/low/close. Symbols that were never fetched are simply
    absent from the response.
    """
    frame = read_prices(symbols, get_config())
    return [] if frame.empty else _to_records(frame)
