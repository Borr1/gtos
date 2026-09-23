#!/usr/bin/env python3
"""Declare the time base of an MT5 tick export, after measuring it.

Why this exists, and why it is separate from ``declare_research_timebase.py``
----------------------------------------------------------------------------
``declare_research_timebase.py`` declares **bar** exports and verifies them with an
exchange-anchor probe: a cash open is a fixed point in its own exchange's calendar, so
the broker stamp of that open reads the broker offset directly. Ticks have no such
anchor — there is no "open bar" to look at — so that verification cannot run, and a tool
that silently skipped its own check would be worse than a separate one.

The tick-appropriate measurement is the **FX week boundary**. The FX week closes at 17:00
New York on Friday and reopens 17:00 New York on Sunday. That is a fixed point in the
*New York* calendar, so the stamped time of the last tick before the weekend reads the
broker offset directly, the same way a cash open does for bars.

Finding F7, restated for ticks
------------------------------
MT5 returns tick timestamps in the **broker server's wall clock**. Decoding them with
``datetime.fromtimestamp(t, tz=utc)`` produces a value that *claims* UTC and is not. The
2026-07-26 VPS export shipped fields literally named ``first_tick_utc`` / ``last_tick_utc``
that were broker time — the round-1 manifest asserted UTC in its own field names. A ``Z``
suffix or a ``_utc`` name is a *stronger* claim than a bare column, so a reader has every
reason to trust it. This writes the sidecar that makes the claim true or false explicitly.

Usage
-----
    python3 scripts/declare_tick_export_timebase.py --data-dir DIR --server FTMO-Server3
    python3 scripts/declare_tick_export_timebase.py --data-dir DIR --server FTMO-Server3 --apply

Dry-run is the default: it measures, prints the per-symbol offsets, and writes nothing.
``--apply`` writes one ``<file>.timebase.json`` beside each tick file.

Refuses to declare a rule the data contradicts. That refusal is the point — a declaration
nothing checked is an assumption wearing a receipt.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.broker_clock import (  # noqa: E402
    UnknownBrokerClockError,
    offset_seconds_at_utc,
    resolve_rule,
)

SIDECAR_SUFFIX = ".timebase.json"
SCHEMA = "gtos_timebase_sidecar_v1"

# Which instruments the boundary probe is VALID for.
#
# The offset is a property of the SERVER, not of the instrument — every symbol on one MT5
# server shares one clock. So the probe does not need to work on every file; it needs to
# work on enough files to establish the server's offset, and it must not run where its own
# anchor is invalid.
#
# The anchor is "the FX week closes 17:00 New York on Friday". That holds for spot FX and
# for nothing else, which the first run of this script demonstrated empirically: the 14 FX
# pairs measured +2.84..+2.92 h while index CFDs read +1.79, metals and oils −0.53..−1.02,
# and Tokyo-anchored JP225 −1.04. Those are not clock disagreements — they are each
# instrument's own session end, which is not 17:00 New York. Measuring there and declaring
# the difference a clock error would have been exactly the mistake F7 already made once.
CURRENCIES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
    "SEK", "NOK", "DKK", "SGD", "HKD", "MXN", "ZAR", "PLN", "CZK", "HUF", "TRY", "CNH",
}


def _is_spot_fx(symbol: str) -> bool:
    """True only for a six-letter pair of two known currency codes (e.g. EURUSD, GBPJPY).

    Deliberately excludes metals (XAUUSD/XAGUSD look like pairs but are not: gold has its
    own session end), index and energy CFDs, and crypto.
    """
    core = symbol.upper().split("_")[-1] if symbol.upper().startswith(("FTMO", "redacted_account")) else symbol.upper()
    core = core.replace(".", "").replace("_", "")
    if len(core) != 6:
        return False
    return core[:3] in CURRENCIES and core[3:] in CURRENCIES


def _weekend_gap_offset(path: Path, *, stride: int = 50) -> float | None:
    """Implied broker offset in hours from the FX week boundary, or None if unmeasurable.

    Reads every ``stride``-th tick (the boundary is a gap of >36 h, so sampling cannot
    move it) and finds the largest gap. The true-UTC close is Friday 17:00 New York; the
    stamped close minus that instant is the offset.
    """
    stamps: list[int] = []
    opener = gzip.open if path.suffix == ".gz" else open
    try:
        with opener(path, "rt", newline="") as handle:
            for index, row in enumerate(csv.DictReader(handle)):
                if index % stride:
                    continue
                raw = row.get("time")
                if raw:
                    stamps.append(int(float(raw)))
    except (OSError, ValueError, KeyError):
        return None
    if len(stamps) < 100:
        return None
    stamps.sort()
    gaps = [(b - a, a) for a, b in zip(stamps, stamps[1:]) if b - a > 36 * 3600]
    if not gaps:
        return None
    _, last_before = max(gaps)
    stamped = datetime.fromtimestamp(last_before, timezone.utc)
    # New York is on EDT (UTC-4) or EST (UTC-5); 17:00 NY is 21:00 or 22:00 UTC.
    ny_close_utc_hour = 21 if 3 <= stamped.month <= 10 else 22
    true_close = stamped.replace(hour=ny_close_utc_hour, minute=0, second=0, microsecond=0)
    return round((stamped - true_close).total_seconds() / 3600.0, 2)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--server", required=True, help="MT5 account_info().server string")
    parser.add_argument("--pattern", default="*ticks*.csv.gz")
    parser.add_argument("--apply", action="store_true", help="write sidecars (default: dry run)")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--tolerance-hours", type=float, default=0.25,
                        help="max |measured - rule| per symbol before the run refuses")
    parser.add_argument("--min-measured", type=int, default=3,
                        help="minimum symbols that must yield a boundary measurement")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    files = sorted(data_dir.rglob(args.pattern))
    if not files:
        print(f"no files matching {args.pattern!r} under {data_dir}", file=sys.stderr)
        return 2

    try:
        rule = resolve_rule(args.server)
    except UnknownBrokerClockError as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    print(f"{len(files)} files | server {args.server} -> rule {rule.name}\n")
    measured: list[tuple[str, float, float, float]] = []
    skipped: list[str] = []
    for path in files:
        symbol = path.name.split("_ticks")[0]
        if not _is_spot_fx(symbol):
            # Not a probe failure: the FX-close anchor is simply not valid here. The server
            # clock is established from the FX pairs and applies to every symbol on it.
            skipped.append(f"{symbol} (not spot FX; declared from the server measurement)")
            continue
        got = _weekend_gap_offset(path)
        if got is None:
            skipped.append(f"{symbol} (no weekend gap found)")
            continue
        # The rule's offset at that same instant, for comparison.
        expected = offset_seconds_at_utc(datetime.now(timezone.utc), rule) / 3600.0
        measured.append((symbol, got, expected, abs(got - expected)))

    for symbol, got, expected, delta in measured:
        flag = "" if delta <= args.tolerance_hours else "   <-- OUT OF TOLERANCE"
        print(f"  {symbol:18s} measured +{got:5.2f} h | rule +{expected:.2f} h | delta {delta:.2f}{flag}")
    for note in skipped:
        print(f"  {note}")

    if len(measured) < args.min_measured:
        print(f"\nREFUSED: only {len(measured)} symbols yielded a boundary measurement "
              f"(need {args.min_measured}). Declaring on this little evidence is a guess.",
              file=sys.stderr)
        return 2

    worst = max(d for _, _, _, d in measured)
    median = statistics.median(g for _, g, _, _ in measured)
    print(f"\nmedian measured offset +{median:.2f} h | worst per-symbol delta {worst:.2f} h "
          f"| tolerance {args.tolerance_hours} h")
    if worst > args.tolerance_hours:
        print("REFUSED: the data contradicts the rule. Do not declare.", file=sys.stderr)
        return 2
    print("MEASUREMENT AGREES WITH THE RULE.")

    if not args.apply:
        print("\nDry run: no sidecars written. Re-run with --apply.")
        return 0

    payload_base = dict(rule.provenance())
    payload_base.update({
        "schema_version": SCHEMA,
        "declared_by": "scripts/declare_tick_export_timebase.py",
        "broker_clock_server": args.server,
        "time_column": "time",
        "time_column_basis": "broker_server_local",
        "time_msc_column": "time_msc",
        "verification": (
            f"FX week boundary measured on {len(measured)} symbols in this directory; "
            f"median +{median:.2f} h, worst per-symbol delta {worst:.2f} h against the rule."
        ),
        "WARNING": (
            "The `time` and `time_msc` columns are BROKER SERVER WALL CLOCK, not UTC. Decoding "
            "them with fromtimestamp(t, tz=utc) yields a value that claims UTC and is not "
            "(finding F7). Convert with src.utils.broker_clock.broker_epoch_to_utc."
        ),
    })

    written = 0
    for path in files:
        sidecar = path.with_name(path.name + SIDECAR_SUFFIX)
        if sidecar.exists() and not args.overwrite:
            continue
        payload = dict(payload_base)
        payload["declares"] = path.name
        sidecar.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written += 1
    print(f"\nwrote {written} sidecars ({len(files) - written} already present)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
