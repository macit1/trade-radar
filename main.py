"""TradeRadar CLI - fetch OHLCV for the configured symbols into a chosen sink."""

import argparse

import requests

from traderadar.fetcher import fetch_prices
from traderadar.storage import SINKS
from traderadar.utils import DEFAULT_CONFIG_PATH, load_config, report


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch daily OHLCV into CSV or SQLite.")
    parser.add_argument(
        "--output",
        choices=sorted(SINKS),
        help="where to write the data (default: the 'output' key in config.yaml)",
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        metavar="TICKER",
        help="override the symbol list from config.yaml",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"path to the config file (default: {DEFAULT_CONFIG_PATH})",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config(args.config)

    symbols = args.symbols or config["symbols"]
    output = args.output or config["output"]
    interval = config["interval"]
    sink = SINKS[output]

    failed = []
    for symbol in symbols:
        print("=" * 60)
        try:
            prices = fetch_prices(symbol, config["range"], interval)
        except (requests.RequestException, ValueError, KeyError) as error:
            # One bad ticker must not abort the rest of the run.
            print(f"{symbol}: FAILED - {error}")
            failed.append(symbol)
            continue

        report(symbol, interval, prices)
        print(f"\nWrote [{output}] -> {sink(prices, symbol, interval, config)}\n")

    print("=" * 60)
    summary = f"Done: {len(symbols) - len(failed)} ok, {len(failed)} failed"
    print(summary + (f" ({', '.join(failed)})" if failed else ""))


if __name__ == "__main__":
    main()
