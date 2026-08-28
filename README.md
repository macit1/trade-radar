# TradeRadar

Daily stock/crypto price tracker. Pulls OHLCV bars from Yahoo Finance and writes
them to one or more sinks you pick at run time: CSV files, a SQLite database, or
both from a single fetch.

No order execution, no brokerage integration.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py                          # uses config.yaml defaults
python main.py --output sql             # write to SQLite
python main.py --output csv             # write one CSV per symbol
python main.py --output csv sql         # both, from a single fetch per symbol
python main.py --output csv sql --symbols MSFT NVDA
python main.py --config other.yaml      # different config file
```

Symbols, interval, range and paths all live in `config.yaml`. The CLI only
overrides them. `output` takes a single sink (`output: sql`) or a list
(`output: [csv, sql]`); repeats are ignored, order is kept.

Each symbol is fetched from Yahoo exactly once no matter how many sinks are
selected.

## Dashboard

```bash
streamlit run dashboard.py
```

Reads the SQLite store directly - no export step. Pick symbols and a period in
the sidebar to get KPI cards, a price chart and a table of the latest bar.

Two chart types:

- **Line** compares every selected symbol. "Normalise to %" rebases each series
  to 0% at the start of the period, so symbols at different price levels can be
  compared by shape rather than by level.
- **Candlestick** shows daily OHLC bars for one symbol, picked from a selector
  that lists whatever is currently selected above. Several symbols of candles on
  one axis would be unreadable, so this view stays single-symbol.

Run `python main.py --output sql` first; on an empty database the dashboard says
so instead of failing.

## Layout

```
main.py               CLI entry point and run loop
dashboard.py          Streamlit dashboard, separate entry point (read-only)
config.yaml           symbols, interval, range, sink paths
traderadar/
  fetcher.py          Yahoo Finance chart endpoint -> DataFrame
  storage.py          database access: write sinks (csv, sql) + read queries
  utils.py            config loading, inspection report
```

`main.py` writes, `dashboard.py` reads, and neither imports the other - they
only share `traderadar/storage.py` and `config.yaml`.

## Data

`https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}` - unofficial, no API
key. Interval limits: `1d` unlimited, `1h` ~2 years, `5m` 60 days, `1m` 8 days.
Never pass `range=max` - it silently ignores `interval` and returns monthly bars.

SQLite schema:

```sql
CREATE TABLE prices (
    symbol TEXT, date TEXT,
    open REAL, high REAL, low REAL, close REAL, volume INTEGER,
    PRIMARY KEY (symbol, date)
);
```

Re-running is safe: rows are upserted on `(symbol, date)`, never duplicated.
