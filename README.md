# TradeRadar

Daily stock/crypto price tracker. Pulls OHLCV bars from Yahoo Finance and writes
them to one or more sinks you pick at run time: CSV files, a SQLite database, or
both from a single fetch.

No order execution, no brokerage integration. Not investment advice: this is a
learning project for the pipeline around market data, not for the data's
conclusions. Figures come from an unofficial source and carry no warranty.

## Setup

```bash
pip install -e .
```

`pyproject.toml` is the source of truth for dependencies. `requirements.txt`
is a thin mirror of it for plain `pip install -r` workflows.

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

## Validation

Every fetch is followed by a validation pass over the stored bars, so bad or
incomplete data surfaces immediately instead of sitting silently in SQLite.

```bash
python main.py --validate-only      # check what is stored, no fetching
python main.py --no-validate        # fetch without the check
python main.py --strict             # warnings fail the run too (for CI)
```

Findings carry a severity. An **error** is data that cannot be right - a broken
`high`/`low`, a duplicate key, a bar on a day the market was closed, a symbol
that is configured but missing. A **warning** is data a real market can produce
but a human should look at - a gap in the history, a 25% move, a zero-volume
session, bars that are stale by a couple of sessions.

The exit code is what a pipeline reads: `0` clean (warnings allowed), `1` when
any error fired, when a fetch failed, or when `--strict` is on and a warning
fired. Thresholds live under `validation:` in `config.yaml`.

Gaps and staleness are counted in trading sessions on the US equity calendar,
not calendar days, so a long weekend or a holiday is never mistaken for missing
data. Every configured symbol is assumed to trade on that calendar.

## API and dashboard

```bash
uvicorn backend.main:app --reload      # http://127.0.0.1:8000  (docs at /docs)
cd frontend && npm run dev             # http://localhost:3000
```

The API serves `GET /symbols` and `GET /prices?symbols=MSFT&symbols=NVDA`
straight from SQLite - no export step. The Next.js dashboard reads those two
endpoints and draws the charts with `lightweight-charts`. Copy
`frontend/.env.example` to `frontend/.env.local` to point the frontend at a
different API host.

Pick symbols in the top bar and a period above the chart to get KPI cards, a
price chart and a table of the latest bar per symbol. `/prices` returns full
history, so period, chart type and normalisation are all local recomputations -
switching them costs no request.

Two chart types:

- **Line** compares every selected symbol. "Normalise to %" rebases each series
  to 0% at the start of the period, so symbols at different price levels can be
  compared by shape rather than by level.
- **Candlestick** shows daily OHLC bars for one symbol, picked from a selector
  that lists whatever is currently selected above. Several symbols of candles on
  one axis would be unreadable, so this view stays single-symbol.

Run `python main.py --output sql` first; on an empty database the dashboard says
so instead of failing.

## Tests

```bash
pip install -e ".[dev]"
pytest
```

Unit tests over the validation rules, the storage sinks and read queries, the
Yahoo response parsing, and the two API endpoints. Every rule has a passing and
a failing case, and every threshold is probed on both sides of its boundary.

No test reaches the network: `requests` is blocked at the adapter for the whole
suite, so a forgotten mock fails the test instead of quietly calling Yahoo.

## Architecture

[`docs/architecture.html`](docs/architecture.html) is a standalone runtime map -
Yahoo Finance to the CLI, the SQLite store, the API and the dashboard, with the
primary data flow and the detail behind each component. Download it and open it
in a browser; it needs nothing else. `docs/architecture.json` is the spec it is
generated from, pinned to the commit it describes.

## Layout

```
main.py               CLI entry point and run loop
config.yaml           symbols, interval, range, sink paths
pyproject.toml        package metadata and dependencies (source of truth)
docs/
  architecture.html   runtime architecture diagram (open it in a browser)
  architecture.json   the spec it is generated from
tests/                pytest suite (see Tests above)
traderadar/
  __init__.py         package marker
  fetcher.py          Yahoo Finance chart endpoint -> DataFrame
  storage.py          database access: write sinks (csv, sql) + read queries
  utils.py            config loading, inspection report
  validation.py       post-fetch data checks, severities, exit codes
backend/
  __init__.py         package marker
  main.py             FastAPI app: /symbols and /prices, read-only
frontend/             Next.js + Tailwind + shadcn/ui dashboard (see above)
data/                 sqlite database and raw CSVs (gitignored)
```

`main.py` writes and `backend/main.py` reads; neither imports the other -
they only share `traderadar/storage.py` and `config.yaml`.

## Data

`https://query1.finance.yahoo.com/v8/finance/chart/{SYMBOL}` - an unofficial
endpoint. No API key, no published contract, no stability guarantee: it can
change or stop answering without notice, and the request sends a browser
`User-Agent` because a bare client is answered differently. If it breaks, that
is the first thing to check - the stored data is probably fine.

Interval limits: `1d` unlimited, `1h` ~2 years, `5m` 60 days, `1m` 8 days.
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

## Company logos

The symbol badges show company logos served by
[Brandfetch](https://brandfetch.com)'s Logo API, requested by ticker at display
time - no marks are copied into this repository. Where a logo is unavailable
the badge falls back to a two-letter abbreviation, so the interface never
depends on the request succeeding.

Company logos are shown for identification purposes only. There is no
affiliation with, sponsorship by, or endorsement from any of the companies
whose marks appear. All trademarks belong to their respective owners.

The API needs a free client ID in `frontend/.env.local` as
`NEXT_PUBLIC_BRANDFETCH_CLIENT_ID`; see `frontend/.env.example`. Leave it unset
and the badges simply stay lettered.

## License

MIT - see [LICENSE](LICENSE).
