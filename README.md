# TradeRadar

Daily stock/crypto price tracker. Pulls OHLCV bars from Yahoo Finance and writes
them to a sink you pick at run time: CSV files or a SQLite database.

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
python main.py --output sql --symbols MSFT NVDA
python main.py --config other.yaml      # different config file
```

Symbols, interval, range and paths all live in `config.yaml`. The CLI only
overrides them.

## Layout

```
main.py               CLI entry point and run loop
config.yaml           symbols, interval, range, sink paths
traderadar/
  fetcher.py          Yahoo Finance chart endpoint -> DataFrame
  storage.py          output sinks (csv, sql) behind one shared signature
  utils.py            config loading, inspection report
```

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
