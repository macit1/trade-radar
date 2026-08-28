"""Shared helpers: config loading and human-readable inspection output."""

from pathlib import Path

import yaml

DEFAULT_CONFIG_PATH = Path("config.yaml")


def unique_list(value):
    """Normalise a single value or a sequence into a de-duplicated list.

    Order is preserved: 'sql' -> ['sql'], ['csv', 'sql', 'csv'] -> ['csv', 'sql'].
    """
    values = [value] if isinstance(value, str) else list(value)
    return list(dict.fromkeys(values))


def load_config(path=DEFAULT_CONFIG_PATH):
    """Read the YAML config into a dict.

    'output' accepts either a single sink ('sql') or a list ([csv, sql]); it is
    normalised to a list here so callers never have to check which form it took.
    """
    with open(path, encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    config["output"] = unique_list(config["output"])
    return config


def report(symbol, interval, prices):
    """Print a sanity check of a freshly fetched frame."""
    print(f"Symbol:      {symbol}")
    print(f"Interval:    {interval}")
    print(f"Rows:        {len(prices)}")
    print(f"Date range:  {prices['Date'].min()} -> {prices['Date'].max()}")
    print(f"NaN counts:  {prices.isna().sum().sum()}")
    print(f"Duplicates:  {prices['Date'].duplicated().sum()}")
    print(f"\nLast 3 rows:\n{prices.tail(3).to_string(index=False)}")
