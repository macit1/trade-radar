"""TradeRadar CLI - fetch OHLCV for the configured symbols into one or more sinks."""

import argparse

import requests

from traderadar.fetcher import fetch_prices
from traderadar.storage import SINKS
from traderadar.utils import DEFAULT_CONFIG_PATH, load_config, report, unique_list


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch daily OHLCV into one or more sinks (CSV, SQLite)."
    )
    parser.add_argument(
        "--output",
        nargs="+",
        choices=sorted(SINKS),
        metavar="SINK",
        help=(
            f"one or more sinks to write to ({', '.join(sorted(SINKS))}); "
            "default: the 'output' key in config.yaml"
        ),
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
    outputs = unique_list(args.output) if args.output else config["output"]
    interval = config["interval"]

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

        # Fetched once above; every sink writes that same frame.
        print()
        for name in outputs:
            target = SINKS[name](prices, symbol, interval, config)
            print(f"Wrote [{name}] -> {target}")
        print()

    print("=" * 60)
    summary = f"Done: {len(symbols) - len(failed)} ok, {len(failed)} failed"
    print(summary + (f" ({', '.join(failed)})" if failed else ""))


if __name__ == "__main__":
    main()
