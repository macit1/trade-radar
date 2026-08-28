"""Streamlit dashboard - reads the SQLite store directly, no export step.

Run with:  streamlit run dashboard.py

Separate entry point from main.py: this module never fetches, it only reads
what the CLI has already stored.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from traderadar import storage
from traderadar.utils import load_config

CACHE_TTL = 300  # seconds; the store only changes when the CLI runs

# Trailing window sizes in calendar days. None means "everything stored".
PERIODS = {"1M": 30, "6M": 182, "1Y": 365, "All": None}


@st.cache_data(ttl=CACHE_TTL)
def get_config():
    return load_config()


@st.cache_data(ttl=CACHE_TTL)
def get_symbols():
    return storage.list_symbols(get_config())


@st.cache_data(ttl=CACHE_TTL)
def get_prices(symbols):
    """symbols is a tuple so Streamlit can use it as a cache key."""
    return storage.read_prices(list(symbols), get_config())


def apply_period(prices, period):
    """Keep only bars inside the trailing window, measured from the latest bar."""
    days = PERIODS[period]
    if days is None or prices.empty:
        return prices

    cutoff = prices["date"].max() - pd.Timedelta(days=days)
    return prices[prices["date"] >= cutoff]


def close_by_symbol(prices):
    """Long table -> one column of closes per symbol, indexed by date."""
    return prices.pivot(index="date", columns="symbol", values="close")


def to_percent_change(closes):
    """Rebase every series to 0% at its own first available bar.

    Symbols trade at very different price levels, so an absolute chart shows the
    gap between them rather than how each one moved. Rebasing makes the shapes
    comparable.
    """
    return closes.apply(lambda column: column / column.dropna().iloc[0] * 100 - 100)


def candlestick_figure(prices, symbol):
    """OHLC bars for a single symbol. Several symbols at once would overlap."""
    bars = prices[prices["symbol"] == symbol].sort_values("date")

    figure = go.Figure(
        go.Candlestick(
            x=bars["date"],
            open=bars["open"],
            high=bars["high"],
            low=bars["low"],
            close=bars["close"],
            name=symbol,
        )
    )
    figure.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        height=420,
        # The period radio already controls the time window; a second one confuses.
        xaxis_rangeslider_visible=False,
    )
    return figure


def summarise(prices):
    """One row per symbol: last close, change against the previous bar, volume."""
    rows = []
    for symbol, group in prices.groupby("symbol"):
        group = group.sort_values("date")
        last = group.iloc[-1]
        previous_close = group["close"].iloc[-2] if len(group) > 1 else None

        change = None if previous_close is None else last["close"] - previous_close
        change_pct = None if not previous_close else change / previous_close * 100

        rows.append(
            {
                "Symbol": symbol,
                "Date": last["date"].date(),
                "Close": last["close"],
                "Change": change,
                "Change %": change_pct,
                "Volume": last["volume"],
                "Bars": len(group),
            }
        )

    return pd.DataFrame(rows).set_index("Symbol")


def render_kpis(summary):
    """A st.metric card per symbol, wrapped four to a row."""
    symbols = list(summary.index)
    for start in range(0, len(symbols), 4):
        for column, symbol in zip(st.columns(4), symbols[start : start + 4]):
            row = summary.loc[symbol]
            delta = (
                None
                if pd.isna(row["Change"])
                else f"{row['Change']:+.2f} ({row['Change %']:+.2f}%)"
            )
            column.metric(label=symbol, value=f"{row['Close']:,.2f}", delta=delta)
            column.caption(f"Vol {row['Volume']:,}")


def main():
    st.set_page_config(page_title="TradeRadar", page_icon=":chart_with_upwards_trend:")
    st.title("TradeRadar")

    available = get_symbols()
    if not available:
        st.info("The database is empty. Run `python main.py --output sql` first.")
        st.stop()

    with st.sidebar:
        st.header("Filters")
        symbols = st.multiselect("Symbols", available, default=available[:2])
        period = st.radio("Period", list(PERIODS), index=len(PERIODS) - 1, horizontal=True)
        chart_type = st.radio("Chart", ["Line", "Candlestick"], horizontal=True)

        # Each chart type has one control of its own; showing the other type's
        # control greyed out or inert would only be noise.
        candle_symbol = None
        normalise = False
        if chart_type == "Candlestick":
            candle_symbol = st.selectbox("Candlestick symbol", symbols) if symbols else None
        else:
            normalise = st.checkbox(
                "Normalise to %",
                help="Rebase each series to 0% at the start of the period so the "
                "trends can be compared regardless of price level.",
            )
        if st.button("Reload from database"):
            st.cache_data.clear()
            st.rerun()

    if not symbols:
        st.warning("Pick at least one symbol.")
        st.stop()

    prices = apply_period(get_prices(tuple(symbols)), period)
    if prices.empty:
        st.warning("No stored bars fall inside this period.")
        st.stop()

    summary = summarise(prices)
    render_kpis(summary)

    st.subheader("Price trend")
    if chart_type == "Candlestick":
        st.plotly_chart(candlestick_figure(prices, candle_symbol), width="stretch")
        st.caption(f"Daily OHLC bars for {candle_symbol}.")
    else:
        closes = close_by_symbol(prices)
        st.line_chart(to_percent_change(closes) if normalise else closes)
        if normalise:
            st.caption("Percent change since the first bar of the selected period.")

    st.subheader("Latest bar")
    st.dataframe(
        summary.style.format(
            {
                "Close": "{:,.2f}",
                "Change": "{:+,.2f}",
                "Change %": "{:+.2f}%",
                "Volume": "{:,.0f}",
            }
        ),
        width="stretch",
    )


# Streamlit runs this file as __main__, so the guard still fires under
# `streamlit run` while keeping the module importable for tests.
if __name__ == "__main__":
    main()
