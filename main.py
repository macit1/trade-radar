"""TradeRadar CLI - fetch OHLCV for the configured symbols into one or more sinks."""

import argparse
import sys

import requests

from traderadar.fetcher import fetch_prices
from traderadar.storage import SINKS
from traderadar.utils import DEFAULT_CONFIG_PATH, load_config, report, unique_list
from traderadar.validation import format_report, validate_store


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
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="validate what is already stored and exit, without fetching",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="skip the validation pass that normally follows a fetch",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat validation warnings as failures (exit 1) - for CI",
    )
    return parser.parse_args()


def run_validation(config, symbols, strict):
    """Validate the store and return the exit code the run should carry."""
    print()
    validation = validate_store(config, symbols)
    print(format_report(validation, strict=strict))
    return validation.exit_code(strict=strict)


def main():
    args = parse_args()
    config = load_config(args.config)

    symbols = args.symbols or config["symbols"]
    outputs = unique_list(args.output) if args.output else config["output"]
    interval = config["interval"]

    # Validation reads the store, so on its own it needs neither a network call
    # nor a sink. Nothing below this point runs.
    if args.validate_only:
        return run_validation(config, symbols, args.strict)

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

    # A fetch that dropped symbols is a failed run even if what landed is clean,
    # so the worse of the two outcomes wins.
    exit_code = 1 if failed else 0
    if not args.no_validate:
        exit_code = max(exit_code, run_validation(config, symbols, args.strict))

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
