"""Validation layer - checks the stored bars every time new data lands.

Not a one-off audit: `validate_store` is called by the CLI after every write and
can be run on its own against whatever is already in the database, so a bad
fetch surfaces immediately instead of sitting silently in SQLite.

Findings carry a severity. The split is deliberate:

    ERROR    the data is definitely wrong - broken OHLC, duplicate keys, a bar
             on a day the market was shut. Nothing legitimate produces these.
    WARNING  the data is suspicious but a real market can produce it - a 30%
             move, a zero-volume session, a thin stretch of history.

A normal run reports warnings and still exits 0; `--strict` promotes them, which
is the knob CI will want later.

Exchange assumption: every configured symbol is expected to trade on the US
equity calendar. That holds for the current list and is what makes the weekend
and cross-symbol checks safe. A 24/7 instrument (crypto) would trip both, so
adding one means giving symbols a calendar of their own - start here.
"""

from dataclasses import dataclass, field

import pandas as pd
from pandas.tseries.holiday import (
    AbstractHolidayCalendar,
    GoodFriday,
    Holiday,
    USLaborDay,
    USMartinLutherKingJr,
    USMemorialDay,
    USPresidentsDay,
    USThanksgivingDay,
    nearest_workday,
)
from pandas.tseries.offsets import CustomBusinessDay

from traderadar.storage import read_prices

ERROR = "error"
WARNING = "warning"

OHLC = ["open", "high", "low", "close"]
OHLCV = OHLC + ["volume"]

# Every threshold is overridable from config.yaml under `validation:`; these are
# the fallbacks so a config written before this module still validates.
DEFAULTS = {
    # Trading days that may be missing between two stored bars before it counts
    # as a hole. One-off closures (a state funeral, a hurricane) land here.
    "gap_trading_days": 3,
    # How far behind the last trading day the newest bar may fall.
    "stale_warn_days": 2,
    "stale_fail_days": 5,
    # Share of the expected trading days that may be missing across the whole
    # stored window before the history counts as thin.
    "coverage_tolerance": 0.05,
    # Close-to-close move that is worth a human look. Splits land here too:
    # Yahoo's chart endpoint is not split-adjusted retroactively in every case.
    "extreme_move_pct": 25.0,
    # A bar is flat when its four prices agree to within this percentage.
    # Exact equality misses the real thing: a thin day prints 100.00/100.01.
    "flat_bar_tolerance_pct": 0.01,
    # Sample dates printed per finding before the rest are counted.
    "max_samples": 5,
}


class USMarketCalendar(AbstractHolidayCalendar):
    """NYSE/Nasdaq closures - not the US federal calendar.

    The exchanges trade on Columbus Day and Veterans Day, which the federal
    calendar closes, and close on Good Friday, which it does not. One-off
    closures are not modelled; they surface as a gap warning instead.
    """

    rules = [
        Holiday("New Year's Day", month=1, day=1, observance=nearest_workday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday(
            "Juneteenth",
            month=6,
            day=19,
            start_date="2021-06-18",
            observance=nearest_workday,
        ),
        Holiday("Independence Day", month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday("Christmas Day", month=12, day=25, observance=nearest_workday),
    ]


MARKET_DAY = CustomBusinessDay(calendar=USMarketCalendar())


def trading_days(start, end):
    """Sessions the US equity market was open, inclusive of both ends."""
    if pd.isna(start) or pd.isna(end) or start > end:
        return pd.DatetimeIndex([])
    return pd.bdate_range(start, end, freq=MARKET_DAY)


def last_trading_day(asof):
    """The most recent session on or before `asof`."""
    asof = pd.Timestamp(asof).normalize()
    return asof if len(trading_days(asof, asof)) else asof - MARKET_DAY


@dataclass
class Finding:
    """One rule firing on one symbol (or on the set, for cross-symbol rules)."""

    rule: str
    severity: str
    summary: str
    samples: list = field(default_factory=list)


@dataclass
class SymbolReport:
    symbol: str
    bars: int
    first: object = None
    last: object = None
    findings: list = field(default_factory=list)

    @property
    def status(self):
        severities = {finding.severity for finding in self.findings}
        if ERROR in severities:
            return "FAIL"
        return "WARN" if WARNING in severities else "PASS"


@dataclass
class Report:
    db_path: str
    asof: object
    symbols: list = field(default_factory=list)
    cross_findings: list = field(default_factory=list)

    @property
    def all_findings(self):
        return [
            f for report in self.symbols for f in report.findings
        ] + self.cross_findings

    def count(self, severity):
        return sum(1 for finding in self.all_findings if finding.severity == severity)

    def exit_code(self, strict=False):
        """0 clean, 1 when the run should fail a pipeline."""
        if self.count(ERROR):
            return 1
        return 1 if strict and self.count(WARNING) else 0

    @property
    def status(self):
        if self.count(ERROR):
            return "FAIL"
        return "WARN" if self.count(WARNING) else "PASS"


def _settings(config):
    """Thresholds from config.yaml, falling back to DEFAULTS key by key."""
    return {**DEFAULTS, **(config.get("validation") or {})}


def _dates(frame):
    return pd.DatetimeIndex(frame["date"])


def _samples(dates, limit):
    """Human-readable date list, truncated with a count of the remainder."""
    shown = [pd.Timestamp(date).date().isoformat() for date in list(dates)[:limit]]
    remaining = len(dates) - len(shown)
    if remaining > 0:
        shown.append(f"(+{remaining} more)")
    return shown


# --------------------------------------------------------------------------
# Per-symbol rules. Each takes the symbol's sorted frame plus settings and
# returns findings, so adding a rule means writing one function and listing it.
# --------------------------------------------------------------------------


def _check_missing_values(frame, settings):
    missing = frame[frame[OHLCV].isna().any(axis=1)]
    if missing.empty:
        return []
    return [
        Finding(
            "missing-values",
            ERROR,
            f"{len(missing)} bars have a null in open/high/low/close/volume",
            _samples(_dates(missing), settings["max_samples"]),
        )
    ]


def _check_duplicate_dates(frame, settings):
    duplicated = frame[frame["date"].duplicated(keep=False)]
    if duplicated.empty:
        return []
    return [
        Finding(
            "duplicate-dates",
            ERROR,
            f"{duplicated['date'].nunique()} dates appear more than once",
            _samples(_dates(duplicated).unique(), settings["max_samples"]),
        )
    ]


def _check_price_domain(frame, settings):
    findings = []

    non_positive = frame[(frame[OHLC] <= 0).any(axis=1)]
    if not non_positive.empty:
        findings.append(
            Finding(
                "non-positive-price",
                ERROR,
                f"{len(non_positive)} bars price at or below zero",
                _samples(_dates(non_positive), settings["max_samples"]),
            )
        )

    negative_volume = frame[frame["volume"] < 0]
    if not negative_volume.empty:
        findings.append(
            Finding(
                "negative-volume",
                ERROR,
                f"{len(negative_volume)} bars report negative volume",
                _samples(_dates(negative_volume), settings["max_samples"]),
            )
        )

    return findings


def _check_ohlc_invariants(frame, settings):
    """high has to top open and close; low has to sit under both."""
    body_high = frame[["open", "close"]].max(axis=1)
    body_low = frame[["open", "close"]].min(axis=1)
    broken = frame[
        (frame["high"] < body_high)
        | (frame["low"] > body_low)
        | (frame["high"] < frame["low"])
    ]
    if broken.empty:
        return []
    return [
        Finding(
            "ohlc-invariant",
            ERROR,
            f"{len(broken)} bars break high >= open/close >= low",
            _samples(_dates(broken), settings["max_samples"]),
        )
    ]


def _check_session_dates(frame, settings):
    """A daily series may only hold midnight-stamped weekday sessions.

    Weekends and stray timestamps are unambiguous corruption. Holidays are left
    to the gap and drift rules, which do not depend on this module's holiday
    table being perfect for every year.
    """
    findings = []
    dates = _dates(frame)

    weekend = frame[dates.dayofweek >= 5]
    if not weekend.empty:
        findings.append(
            Finding(
                "weekend-bar",
                ERROR,
                f"{len(weekend)} bars fall on a Saturday or Sunday",
                _samples(_dates(weekend), settings["max_samples"]),
            )
        )

    intraday = frame[dates.normalize() != dates]
    if not intraday.empty:
        findings.append(
            Finding(
                "intraday-timestamp",
                ERROR,
                f"{len(intraday)} bars carry a time of day in a daily series",
                _samples(_dates(intraday), settings["max_samples"]),
            )
        )

    return findings


def _check_gaps(frame, settings):
    """Holes inside the stored window, measured in sessions rather than days.

    Calendar days would flag every long weekend; the stored data already shows
    four-day calendar gaps that are simply holidays.
    """
    dates = _dates(frame)
    holes = []
    for previous, current in zip(dates, dates[1:]):
        missing = len(trading_days(previous + MARKET_DAY, current - MARKET_DAY))
        if missing > settings["gap_trading_days"]:
            holes.append((previous, current, missing))

    if not holes:
        return []

    samples = [
        f"{previous.date()} -> {current.date()} ({missing} sessions)"
        for previous, current, missing in holes[: settings["max_samples"]]
    ]
    if len(holes) > len(samples):
        samples.append(f"(+{len(holes) - len(samples)} more)")

    return [
        Finding(
            "calendar-gap", WARNING, f"{len(holes)} gaps in the stored history", samples
        )
    ]


def _check_coverage(frame, settings):
    """Thin history: sessions missing across the window as a whole."""
    dates = _dates(frame)
    expected = len(trading_days(dates.min(), dates.max()))
    if not expected:
        return []

    missing = expected - dates.nunique()
    if missing <= 0 or missing / expected <= settings["coverage_tolerance"]:
        return []

    return [
        Finding(
            "thin-coverage",
            WARNING,
            f"{missing} of {expected} sessions missing "
            f"({missing / expected:.1%} > {settings['coverage_tolerance']:.0%} tolerance)",
        )
    ]


def _check_staleness(frame, settings, asof):
    """How far behind the market the newest bar is, counted in sessions."""
    latest = _dates(frame).max()
    reference = last_trading_day(asof)
    if latest >= reference:
        return []

    behind = len(trading_days(latest + MARKET_DAY, reference))
    if behind > settings["stale_fail_days"]:
        severity = ERROR
    elif behind > settings["stale_warn_days"]:
        severity = WARNING
    else:
        return []

    return [
        Finding(
            "stale-data",
            severity,
            f"newest bar {latest.date()} is {behind} sessions behind "
            f"the last trading day ({reference.date()})",
        )
    ]


def _check_extreme_moves(frame, settings):
    move = frame["close"].pct_change().abs() * 100
    extreme = frame[move > settings["extreme_move_pct"]]
    if extreme.empty:
        return []

    samples = [
        f"{pd.Timestamp(row.date).date()} {move.loc[row.Index]:.1f}%"
        for row in extreme.head(settings["max_samples"]).itertuples()
    ]
    if len(extreme) > len(samples):
        samples.append(f"(+{len(extreme) - len(samples)} more)")

    return [
        Finding(
            "extreme-move",
            WARNING,
            f"{len(extreme)} close-to-close moves over {settings['extreme_move_pct']:.0f}% "
            "(a split or a real event - needs a human)",
            samples,
        )
    ]


def _check_flat_and_volume(frame, settings):
    """Flat bars, zero-volume sessions, and the pair that means real trouble.

    Either alone happens on a genuinely quiet day. Together they describe a
    session where nothing traded and no price moved, which is a placeholder row
    rather than a bar.
    """
    findings = []
    tolerance = settings["flat_bar_tolerance_pct"] / 100

    span = frame["high"] - frame["low"]
    # Relative to the bar's own level, so a $500 stock is not held to a $5 one's
    # standard. A zero or missing close falls back to an absolute comparison.
    reference = frame["close"].abs().where(frame["close"].abs() > 0, 1.0)
    flat = span <= reference * tolerance
    no_volume = frame["volume"] == 0

    dead = frame[flat & no_volume]
    if not dead.empty:
        findings.append(
            Finding(
                "flat-and-zero-volume",
                ERROR,
                f"{len(dead)} bars are flat and traded nothing - placeholder rows",
                _samples(_dates(dead), settings["max_samples"]),
            )
        )

    flat_only = frame[flat & ~no_volume]
    if not flat_only.empty:
        findings.append(
            Finding(
                "flat-bar",
                WARNING,
                f"{len(flat_only)} bars move less than "
                f"{settings['flat_bar_tolerance_pct']}% between high and low",
                _samples(_dates(flat_only), settings["max_samples"]),
            )
        )

    zero_only = frame[no_volume & ~flat]
    if not zero_only.empty:
        findings.append(
            Finding(
                "zero-volume",
                WARNING,
                f"{len(zero_only)} sessions report zero volume",
                _samples(_dates(zero_only), settings["max_samples"]),
            )
        )

    return findings


def _check_repeated_bars(frame, settings):
    """Consecutive bars identical in all five fields - a stuck feed repeating."""
    same = (frame[OHLCV] == frame[OHLCV].shift()).all(axis=1)
    repeated = frame[same]
    if repeated.empty:
        return []
    return [
        Finding(
            "repeated-bar",
            WARNING,
            f"{len(repeated)} bars repeat the previous bar exactly",
            _samples(_dates(repeated), settings["max_samples"]),
        )
    ]


SYMBOL_RULES = [
    _check_missing_values,
    _check_duplicate_dates,
    _check_price_domain,
    _check_ohlc_invariants,
    _check_session_dates,
    _check_gaps,
    _check_coverage,
    _check_extreme_moves,
    _check_flat_and_volume,
    _check_repeated_bars,
]


def _check_calendar_drift(frames, settings):
    """Sessions one symbol has and the rest do not, or the other way round.

    Every configured symbol trades on the same exchange calendar, so a date the
    majority agrees on is a session. A symbol that disagrees inside its own
    window is missing data, not a different market - hence an error.
    """
    if len(frames) < 2:
        return []

    counts = pd.Series(
        [date for frame in frames.values() for date in _dates(frame).unique()]
    ).value_counts()
    consensus = set(counts[counts > len(frames) / 2].index)

    findings = []
    for symbol, frame in sorted(frames.items()):
        dates = _dates(frame)
        own = set(dates.unique())
        window = {date for date in consensus if dates.min() <= date <= dates.max()}

        absent = sorted(window - own)
        if absent:
            findings.append(
                Finding(
                    "calendar-drift",
                    ERROR,
                    f"{symbol} is missing {len(absent)} sessions the other symbols have",
                    _samples(absent, settings["max_samples"]),
                )
            )

        extra = sorted(own - consensus)
        if extra:
            findings.append(
                Finding(
                    "calendar-drift",
                    ERROR,
                    f"{symbol} has {len(extra)} sessions no other symbol traded",
                    _samples(extra, settings["max_samples"]),
                )
            )

    return findings


def validate_store(config, symbols=None, asof=None):
    """Run every rule over the stored bars and return a Report.

    `symbols` defaults to the configured list. Reading goes through
    traderadar.storage, so this module never opens a connection of its own.
    """
    settings = _settings(config)
    asof = pd.Timestamp(asof or pd.Timestamp.today()).normalize()
    wanted = list(symbols if symbols is not None else config["symbols"])

    stored = read_prices(wanted, config)
    report = Report(db_path=str(config["db_path"]), asof=asof)
    frames = {}

    for symbol in wanted:
        frame = (
            stored[stored["symbol"] == symbol].sort_values("date").reset_index(drop=True)
        )

        # A row whose date did not parse is corruption in the key itself, and it
        # would turn every date calculation below into NaT. Report it, then work
        # with what is left rather than failing the whole run - the point of a
        # validator is to describe bad data, not to fall over on it.
        unparseable = frame[frame["date"].isna()]
        prefix = []
        if not unparseable.empty:
            prefix.append(
                Finding(
                    "unparseable-date",
                    ERROR,
                    f"{len(unparseable)} rows carry a date the reader could not parse",
                )
            )
            frame = frame.dropna(subset=["date"]).reset_index(drop=True)

        if frame.empty:
            report.symbols.append(
                SymbolReport(
                    symbol=symbol,
                    bars=0,
                    findings=prefix
                    + [Finding("no-data", ERROR, "configured but absent from the store")],
                )
            )
            continue

        frames[symbol] = frame
        dates = _dates(frame)
        findings = prefix + [f for rule in SYMBOL_RULES for f in rule(frame, settings)]
        findings += _check_staleness(frame, settings, asof)

        report.symbols.append(
            SymbolReport(
                symbol=symbol,
                bars=len(frame),
                first=dates.min(),
                last=dates.max(),
                findings=findings,
            )
        )

    report.cross_findings = _check_calendar_drift(frames, settings)
    return report


def format_report(report, strict=False):
    """The console rendering. One line per symbol, detail only where it fired."""
    width = 60
    lines = [
        "=" * width,
        f"Validation - {report.db_path}",
        f"US equity calendar, as of {report.asof.date()} "
        f"(last session {last_trading_day(report.asof).date()})",
        "",
    ]

    for symbol_report in report.symbols:
        span = (
            f"{symbol_report.first.date()} -> {symbol_report.last.date()}"
            if symbol_report.bars
            else "no bars"
        )
        lines.append(
            f"{symbol_report.symbol:<7}{symbol_report.status:<6}"
            f"{symbol_report.bars:>5} bars  {span}"
        )
        lines += _format_findings(symbol_report.findings)

    if report.cross_findings:
        lines.append("")
        lines.append("Cross-symbol")
        lines += _format_findings(report.cross_findings)

    passed = sum(1 for s in report.symbols if s.status == "PASS")
    warned = sum(1 for s in report.symbols if s.status == "WARN")
    failed = sum(1 for s in report.symbols if s.status == "FAIL")

    lines += [
        "",
        "-" * width,
        f"{len(report.symbols)} symbols: {passed} pass, {warned} warning, {failed} failed",
        f"Result: {report.status} "
        f"({report.count(ERROR)} errors, {report.count(WARNING)} warnings)",
    ]

    if strict and report.count(WARNING) and not report.count(ERROR):
        lines.append("--strict is on, so warnings fail the run.")

    return "\n".join(lines)


def _format_findings(findings):
    lines = []
    for finding in findings:
        lines.append(f"  [{finding.severity}] {finding.rule}: {finding.summary}")
        if finding.samples:
            lines.append(f"    {', '.join(finding.samples)}")
    return lines
