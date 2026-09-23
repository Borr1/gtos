#!/usr/bin/env python3
"""Declare the time base of an existing research export directory. Rewrites no data.

This is the view layer's other half. :mod:`src.utils.research_timebase` can *read* an
export in true UTC; this writes the ``<file>.timebase.json`` sidecar that tells it how,
so the archive becomes self-describing without a single data byte changing.

Why declare rather than re-export
---------------------------------
1. The offset is deterministic --- measured, over 2022-2026, on three exchange
   calendars --- so a view is exact rather than approximate.
2. Re-export depends on re-materialising iCloud-evicted files (53 of the 96 the April
   bundle binds) and on a live MT5 bridge. Declaring works today, offline.
3. The sealed campaign must keep reading the bytes it was sealed against. Re-exporting
   would produce a *second* dataset beside the sealed one and would not remove the need
   to read the old one correctly --- so it is strictly more work for strictly less
   coverage.

Every declaration is **measured, not assumed**: before writing sidecars this re-runs the
exchange-anchor probe against the directory's own bars and refuses to declare a rule the
data contradicts. That is the difference between a declaration and a guess, and a guess
is what produced F7.

Usage
-----
    python3 scripts/declare_research_timebase.py --data-dir data/historical_2026 --server FTMO-Server3
    python3 scripts/declare_research_timebase.py --data-dir data/... --server FTMO-Server3 --apply

Dry-run by default. Read-only with respect to the data; touches no broker.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.broker_clock import UnknownBrokerClockError, resolve_rule  # noqa: E402
from src.utils.research_timebase import (  # noqa: E402
    BROKER_LOCAL,
    TRUE_UTC,
    sidecar_path,
    write_sidecar,
)

# Import by path rather than relying on scripts/ being sys.path[0], which only holds
# when this file is executed directly --- so the tool can also be imported and tested.
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location(
    "_measure_broker_clock_offset", Path(__file__).resolve().parent / "measure_broker_clock_offset.py"
)
probe = _ilu.module_from_spec(_spec)
sys.modules[_spec.name] = probe
_spec.loader.exec_module(probe)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", required=True, help="Directory of <SYMBOL>_<TF>.csv exports.")
    parser.add_argument("--server", required=True, help="MT5 server that produced the data, e.g. FTMO-Server3.")
    parser.add_argument(
        "--basis",
        choices=[BROKER_LOCAL, TRUE_UTC],
        default=BROKER_LOCAL,
        help="What the time column already is (default: broker_server_local --- the pre-repair exports).",
    )
    parser.add_argument("--apply", action="store_true", help="Write the sidecars. Without this, dry-run.")
    parser.add_argument("--overwrite", action="store_true", help="Replace sidecars that already exist.")
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Declare without re-measuring. Use only where the directory has no exchange-anchored "
             "instrument; the declaration is then an assertion, not a measurement, and says so.",
    )
    parser.add_argument("--min-agreement", type=float, default=0.90)
    args = parser.parse_args(argv)

    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"ERROR: no such directory: {data_dir}", file=sys.stderr)
        return 2
    try:
        rule = resolve_rule(args.server)
    except UnknownBrokerClockError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    verification = "skipped by --skip-verification (declaration is asserted, not measured)"
    if not args.skip_verification and args.basis == BROKER_LOCAL:
        rc = probe.main(["--data-dir", str(data_dir), "--check", args.server,
                         "--min-agreement", str(args.min_agreement)])
        if rc == 2:
            print(
                "\nNo exchange-anchored instrument in this directory, so the rule cannot be "
                "verified from its own bars. Re-run with --skip-verification if you are "
                "declaring it from external provenance, and expect the sidecar to say so.",
                file=sys.stderr,
            )
            return 2
        if rc != 0:
            print("\nREFUSING to declare: the data contradicts the rule (see mismatches above).",
                  file=sys.stderr)
            return 1
        verification = (
            f"Verified against this directory by scripts/measure_broker_clock_offset.py "
            f"--data-dir {data_dir} --check {args.server} (>= {args.min_agreement:.0%} of days agree)."
        )

    csvs = sorted(p for p in data_dir.rglob("*.csv"))
    written = skipped = 0
    for path in csvs:
        target = sidecar_path(path)
        if target.exists() and not args.overwrite:
            skipped += 1
            continue
        if args.apply:
            write_sidecar(
                path,
                basis=args.basis,
                rule=rule if args.basis == BROKER_LOCAL else None,
                evidence=f"{rule.evidence} {verification}",
                server=args.server if args.basis == BROKER_LOCAL else None,
                extra={"declared_by": "scripts/declare_research_timebase.py"},
            )
        written += 1

    verb = "wrote" if args.apply else "would write"
    print(f"\n{verb} {written} sidecar(s) under {data_dir}; {skipped} already present (use --overwrite).")
    if not args.apply:
        print("Dry run --- re-run with --apply to write them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
