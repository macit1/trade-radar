"""Shared helpers: config loading and human-readable inspection output."""

from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path=DEFAULT_CONFIG_PATH):
    """Read the YAML config into a dict."""
    with open(path, encoding="utf-8") as config_file:
        return yaml.safe_load(config_file)


def report(symbol, interval, prices):
    """Print a sanity check of a freshly fetched frame."""
    print(f"Symbol:      {symbol}")
    print(f"Interval:    {interval}")
    print(f"Rows:        {len(prices)}")
    print(f"Date range:  {prices['Date'].min()} -> {prices['Date'].max()}")
    print(f"NaN counts:  {prices.isna().sum().sum()}")
    print(f"Duplicates:  {prices['Date'].duplicated().sum()}")
    print(f"\nLast 3 rows:\n{prices.tail(3).to_string(index=False)}")
