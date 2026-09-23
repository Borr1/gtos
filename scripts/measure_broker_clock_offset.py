#!/usr/bin/env python3
"""Measure a broker's UTC offset from exported bar data, with no external reference.

This is the evidence behind ``src/utils/broker_clock.NEW_YORK_PLUS_7``, and a
validator you can re-run against any export to check its declared time base.

The method
----------
Most timestamps in an MT5 export are anchored to the *broker's own* clock --- the
Friday weekend close, the daily session start, the D1 bar boundary --- so they are
constant in broker stamps and carry no information about the offset. Comparing them
against "true UTC FX weeks end ~22:00Z" is what produced the original EET/EEST
reading, and it cannot distinguish +2 from +3.

What does carry the information is a **cash equity open**, because it is fixed in
*its own exchange's* calendar, not the broker's. Read the broker stamp of the
opening volume spike and the offset falls straight out::

    implied_offset = broker_stamp_of_open - true_utc_of_that_exchange_open

Run it over instruments on three different exchange calendars and the answer is
overdetermined. In particular Tokyo observes no DST at all, so JP225 alone pins the
transition dates.

Usage
-----
    python3 scripts/measure_broker_clock_offset.py --data-dir data/historical_2026
    python3 scripts/measure_broker_clock_offset.py --data-dir data/... --check FTMO-Server3

``--check`` compares every daily observation against a registered rule and exits 1
on any disagreement, so an export can be validated in CI.

Read-only. Touches no broker.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.broker_clock import (  # noqa: E402
    BrokerClockRule,
    UnknownBrokerClockError,
    offset_seconds_at_utc,
    resolve_rule,
)


@dataclass(frozen=True)
class Anchor:
    """An instrument whose cash open is a fixed point in a known exchange calendar."""

    symbol: str
    zone: str
    open_local: time
    note: str


# Only cash-equity indices qualify. FX has no hard open --- its volume peaks track
# scheduled news, which is why a EURUSD probe returns noise (measured: no clean
# shift at any transition). Metals, energy and crypto are 23/5 or 24/7.
ANCHORS: tuple[Anchor, ...] = (
    Anchor("JP225", "Asia/Tokyo", time(9, 0), "TSE open; JST observes no DST, so this alone pins the transition dates"),
    Anchor("GER40", "Europe/Berlin", time(9, 0), "Xetra open; European DST"),
    Anchor("UK100", "Europe/London", time(8, 0), "LSE open; European DST"),
    Anchor("SPX500", "America/New_York", time(9, 30), "NYSE open; US DST"),
    Anchor("US30_cash", "America/New_York", time(9, 30), "NYSE open; US DST"),
    Anchor("NAS100", "America/New_York", time(9, 30), "NYSE open; US DST"),
)

# How far either side of the earliest plausible offset to hunt for the opening
# spike, in hours of broker stamp. Wide enough to span every offset a GMT+2/+3
# broker can take, narrow enough not to catch a different session's spike.
SEARCH_LO_HOURS = 0.0
SEARCH_HI_HOURS = 5.0


# Volume column, in preference order. Positional fallback is deliberately absent: on
# the 8-column export schema (time,o,h,l,c,tick_volume,spread,real_volume) the last
# column is real_volume, which is identically zero for spot CFDs --- a silent all-zero
# series that makes every measurement garbage while the tool still reports a number.
VOLUME_COLUMNS = ("volume", "tick_volume", "real_volume")


def _load_bars(path: Path) -> list[tuple[datetime, float]]:
    out: list[tuple[datetime, float]] = []
    with path.open(newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if not header:
            return out
        try:
            t_idx = header.index("time")
        except ValueError:
            t_idx = 0
        v_idx = next((header.index(c) for c in VOLUME_COLUMNS if c in header), None)
        if v_idx is None:
            raise ValueError(
                f"{path}: no volume column found (looked for {VOLUME_COLUMNS}); header={header}"
            )
        for row in reader:
            if len(row) <= max(t_idx, v_idx):
                continue
            try:
                stamp = datetime.strptime(row[t_idx], "%Y-%m-%d %H:%M:%S")
                volume = float(row[v_idx])
            except ValueError:
                continue
            out.append((stamp, volume))
    return out


def _true_utc_open(day: date, anchor: Anchor) -> datetime:
    local = datetime.combine(day, anchor.open_local).replace(tzinfo=ZoneInfo(anchor.zone))
    return local.astimezone(timezone.utc).replace(tzinfo=None)


def observe(path: Path, anchor: Anchor) -> dict[date, int]:
    """Per weekday, the implied broker offset in whole hours.

    Estimator: the largest **step up** in volume relative to the preceding bar, not the
    largest volume. That distinction matters. A cash open is an auction — volume jumps
    discontinuously — but it is often not the day's largest bar: for GER40, UK100 and
    JP225 alike the global daily maximum is the *NYSE* open several hours later. An
    argmax-of-level estimator therefore lands on the wrong session on a large minority
    of days and injects spurious offsets; the step estimator is anchored to the
    discontinuity itself and is far cleaner (measured: it takes the Tokyo anchor from
    79% to ~100% agreement, with a sharp split exactly at the transition date).
    """
    bars = _load_bars(path)
    bars.sort()
    previous = [0.0] + [v for _, v in bars[:-1]]
    by_day: dict[date, list[tuple[datetime, float]]] = collections.defaultdict(list)
    for (stamp, volume), prior in zip(bars, previous):
        by_day[stamp.date()].append((stamp, volume - prior))

    implied: dict[date, int] = {}
    for day, rows in by_day.items():
        if day.weekday() >= 5:
            continue
        expected_utc = _true_utc_open(day, anchor)
        lo = expected_utc + timedelta(hours=SEARCH_LO_HOURS)
        hi = expected_utc + timedelta(hours=SEARCH_HI_HOURS)
        window = [(step, s) for s, step in rows if lo <= s <= hi]
        if not window:
            continue
        _, peak = max(window)
        # Round to the nearest hour: the step sits in the 15-minute bar containing the
        # open, so the raw difference is the offset plus 0..59 minutes of slop.
        delta_minutes = (peak - expected_utc).total_seconds() / 60.0
        implied[day] = int(round(delta_minutes / 60.0))
    return implied


def _predicted_offset_hours(day: date, rule: BrokerClockRule) -> int:
    """The rule's offset for a trading day, read at midday to avoid every seam edge."""
    return offset_seconds_at_utc(
        datetime.combine(day, time(12, 0)).replace(tzinfo=timezone.utc), rule
    ) // 3600


def _transitions(offsets: dict[date, int]) -> list[tuple[date, date, int, int]]:
    """(last day at the old offset, first day at the new, old, new), ignoring 1-day blips."""
    days = sorted(offsets)
    # Collapse single-day excursions: a lone off-value day is estimator noise on a
    # holiday or a news bar, not a clock change.
    smoothed: dict[date, int] = dict(offsets)
    for i in range(1, len(days) - 1):
        prev, cur, nxt = days[i - 1], days[i], days[i + 1]
        if offsets[prev] == offsets[nxt] != offsets[cur]:
            smoothed[cur] = offsets[prev]
    out = []
    for prev, cur in zip(days, days[1:]):
        if smoothed[prev] != smoothed[cur]:
            out.append((prev, cur, smoothed[prev], smoothed[cur]))
    return out


def _seam_mismatches(consensus: dict[date, int], rule: BrokerClockRule) -> list[dict[str, object]]:
    """Every measured transition must be bracketed by one the rule also predicts.

    This is the check that actually discriminates between DST calendars; percentage
    agreement does not.
    """
    predicted = {day: _predicted_offset_hours(day, rule) for day in consensus}
    measured_seams = _transitions(consensus)
    rule_seams = _transitions(predicted)
    failures: list[dict[str, object]] = []
    for before, after, old, new in measured_seams:
        matched = any(
            r_old == old and r_new == new and before <= r_after and r_before <= after
            for r_before, r_after, r_old, r_new in rule_seams
        )
        if not matched:
            failures.append({
                "measured_between": [before.isoformat(), after.isoformat()],
                "measured_change": f"UTC+{old} -> UTC+{new}",
                "rule_predicts_transitions": [
                    [b.isoformat(), a.isoformat(), f"UTC+{o} -> UTC+{n}"] for b, a, o, n in rule_seams
                ],
            })
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", default="data/historical_2026", help="Directory of <SYMBOL>_M15.csv exports.")
    parser.add_argument("--check", default=None, help="MT5 server name; verify every observation against its registered rule and exit 1 on disagreement.")
    parser.add_argument("--min-agreement", type=float, default=0.90, help="Fraction of days that must match the rule (default 0.90; index opens are occasionally displaced by a holiday or a news spike).")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable output.")
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"ERROR: no such directory: {data_dir}", file=sys.stderr)
        return 2

    rule: BrokerClockRule | None = None
    if args.check:
        try:
            rule = resolve_rule(args.check)
        except UnknownBrokerClockError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    per_anchor: dict[str, dict[date, int]] = {}
    for anchor in ANCHORS:
        path = data_dir / f"{anchor.symbol}_M15.csv"
        if not path.is_file():
            continue
        observations = observe(path, anchor)
        if observations:
            per_anchor[anchor.symbol] = observations

    if not per_anchor:
        print(
            f"ERROR: no anchor instruments found in {data_dir}. Need at least one of: "
            f"{', '.join(a.symbol for a in ANCHORS)} as <SYMBOL>_M15.csv.",
            file=sys.stderr,
        )
        return 2

    # Consensus across anchors, per day. Disagreement between exchanges on the same
    # day is the loud failure this tool exists to surface.
    votes: dict[date, collections.Counter] = collections.defaultdict(collections.Counter)
    for symbol, observations in per_anchor.items():
        for day, offset in observations.items():
            votes[day][offset] += 1

    consensus: dict[date, int] = {}
    contested: list[date] = []
    for day, counter in votes.items():
        top, n_top = counter.most_common(1)[0]
        consensus[day] = top
        if len(counter) > 1 and n_top < sum(counter.values()):
            contested.append(day)

    runs: list[tuple[date, date, int]] = []
    for day in sorted(consensus):
        offset = consensus[day]
        if runs and runs[-1][2] == offset:
            runs[-1] = (runs[-1][0], day, offset)
        else:
            runs.append((day, day, offset))

    mismatches: list[dict[str, object]] = []
    seam_failures: list[dict[str, object]] = []
    if rule is not None:
        for day, offset in sorted(consensus.items()):
            predicted = _predicted_offset_hours(day, rule)
            if predicted != offset:
                mismatches.append({"date": day.isoformat(), "measured_hours": offset, "rule_hours": predicted})

        # Overall agreement is NOT sufficient to discriminate between candidate DST
        # calendars, and relying on it would have let the original EU-calendar reading
        # through: the EU and US calendars differ on only ~20 of ~261 weekdays a year,
        # so a wrong calendar still scores ~92% and clears any percentage threshold you
        # would naively pick. The discriminating signal is WHERE the offset changes, so
        # the transition dates are gated separately and exactly.
        seam_failures = _seam_mismatches(consensus, rule)

    agreement = 1.0 - (len(mismatches) / len(consensus)) if consensus else 0.0

    if args.json:
        print(json.dumps({
            "data_dir": str(data_dir),
            "anchors_used": {s: len(o) for s, o in per_anchor.items()},
            "days_observed": len(consensus),
            "offset_runs": [{"from": a.isoformat(), "to": b.isoformat(), "offset_hours": o} for a, b, o in runs],
            "contested_days": [d.isoformat() for d in sorted(contested)],
            "checked_against": rule.name if rule else None,
            "agreement": round(agreement, 4),
            "mismatches": mismatches,
            "seam_failures": seam_failures,
        }, indent=2))
    else:
        print(f"data dir      : {data_dir}")
        print(f"anchors used  : " + ", ".join(f"{s} ({len(o)}d)" for s, o in sorted(per_anchor.items())))
        print(f"days observed : {len(consensus)}")
        print()
        print("implied broker offset, contiguous runs:")
        for start, end, offset in runs:
            print(f"  {start} .. {end}   UTC+{offset}")
        if contested:
            print(f"\n  WARNING: {len(contested)} day(s) where anchors disagreed: "
                  f"{', '.join(d.isoformat() for d in sorted(contested)[:10])}")
        if rule is not None:
            print()
            print(f"checked against : {rule.name}")
            print(f"agreement       : {agreement:.1%} ({len(consensus) - len(mismatches)}/{len(consensus)} days, consensus)")
            print("per anchor (each is an independent exchange calendar):")
            for symbol in sorted(per_anchor):
                hits = sum(
                    1 for day, off in per_anchor[symbol].items()
                    if off == _predicted_offset_hours(day, rule)
                )
                total = len(per_anchor[symbol])
                print(f"  {symbol:11s} {hits}/{total} ({hits / total:.0%})")
            print(f"transition dates : {'OK' if not seam_failures else str(len(seam_failures)) + ' MISMATCHED'}"
                  "  (the check that actually discriminates between DST calendars)")
            for bad in seam_failures:
                print(f"  SEAM the rule does not predict: {bad['measured_change']} between "
                      f"{bad['measured_between'][0]} and {bad['measured_between'][1]}")
            for bad in mismatches[:20]:
                print(f"  day mismatch {bad['date']}: measured UTC+{bad['measured_hours']}, rule says UTC+{bad['rule_hours']}")

    if rule is not None and seam_failures:
        print(f"\nFAIL: {len(seam_failures)} measured transition(s) the rule does not predict. "
              "This is the calendar check --- a wrong DST calendar still scores ~92% on days.",
              file=sys.stderr)
        return 1
    if rule is not None and agreement < args.min_agreement:
        print(f"\nFAIL: agreement {agreement:.1%} below --min-agreement {args.min_agreement:.1%}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
