"""Pull OHLCV bars from the public Yahoo Finance chart endpoint."""

import pandas as pd
import requests

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)
REQUEST_TIMEOUT = 15

COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
OHLC = ["Open", "High", "Low", "Close"]


def fetch_prices(symbol, price_range, interval):
    """Fetch OHLCV as a DataFrame. Raises if the response is not usable."""
    response = requests.get(
        CHART_URL.format(symbol=symbol),
        params={"range": price_range, "interval": interval},
        headers={"User-Agent": USER_AGENT},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    chart = response.json()["chart"]

    if chart.get("error"):
        raise ValueError(f"Yahoo returned an error for '{symbol}': {chart['error']}")
    if not chart.get("result"):
        raise ValueError(f"No data returned for '{symbol}' - is the ticker valid?")

    result = chart["result"][0]
    quote = result["indicators"]["quote"][0]

    # Yahoo returns UTC epochs; bars belong to the exchange's local calendar.
    timestamps = (
        pd.to_datetime(result["timestamp"], unit="s", utc=True)
        .tz_convert(result["meta"]["exchangeTimezoneName"])
        .tz_localize(None)
    )
    if interval == "1d":
        timestamps = timestamps.normalize()

    prices = pd.DataFrame(
        {
            "Date": timestamps,
            "Open": quote["open"],
            "High": quote["high"],
            "Low": quote["low"],
            "Close": quote["close"],
            "Volume": quote["volume"],
        }
    )

    # Yahoo publishes the current session's bar before the close, with some of
    # its OHLC still empty. A partial bar is not a daily bar: drop it so the
    # store always ends on the last completed session.
    prices = prices.dropna(subset=OHLC)

    if prices.empty:
        raise ValueError(f"Empty price series for '{symbol}'")

    return prices[COLUMNS].reset_index(drop=True)
