#!/usr/bin/env python3
"""Analyze CME futures-to-MT5 CFD mapping from Databento DBN trades.

Research/tooling only. Reads ignored raw Databento DBN files plus existing
MT5 M1 CSVs, then writes a JSON report under `research/` by default.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.futures_cfd_mapping import (  # noqa: E402
    default_pairs,
    diagnose_pair,
    load_databento_trades,
    load_mt5_m1,
    parse_pair,
    aggregate_futures_m1,
    write_mapping_report,
)


DEFAULT_OUTPUT = (
    "research/databento_orderflow_capture_2026-05-02/"
    "FUTURES_CFD_MAPPING_INITIAL_REPORT_2026-05-02.json"
)


def parse_dbn_paths(values: list[str]) -> list[Path]:
    out: list[Path] = []
    for value in values:
        for part in value.split(","):
            stripped = part.strip()
            if stripped:
                out.append(Path(stripped))
    if not out:
        raise ValueError("at least one --dbn path is required")
    return out


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dbn", action="append", required=True, help="DBN path; repeatable or comma-separated")
    parser.add_argument("--mt5-dir", default="data/historical_2026")
    parser.add_argument("--pair", action="append", help="Pair FUTURES:MT5. Defaults GC/NQ/YM/ES mappings.")
    parser.add_argument("--start", help="UTC inclusive start filter")
    parser.add_argument("--end", help="UTC exclusive end filter")
    parser.add_argument(
        "--mt5-time-shift-minutes",
        type=int,
        default=0,
        help=(
            "Shift MT5 M1 timestamps before alignment. Use -180 when broker "
            "CSV times are UTC+3 and futures are UTC."
        ),
    )
    parser.add_argument("--max-lag-minutes", type=int, default=5)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    dbn_paths = parse_dbn_paths(args.dbn)
    pairs = [parse_pair(item) for item in args.pair] if args.pair else default_pairs()

    missing = [str(path) for path in dbn_paths if not path.exists()]
    if missing:
        parser.exit(2, f"missing DBN file(s): {missing}\n")

    trades = load_databento_trades(dbn_paths)
    futures_m1 = aggregate_futures_m1(trades)
    diagnostics = []
    mt5_cache = {}
    for pair in pairs:
        if pair.mt5_symbol not in mt5_cache:
            mt5_cache[pair.mt5_symbol] = load_mt5_m1(
                pair.mt5_symbol,
                data_dir=args.mt5_dir,
                start=args.start,
                end=args.end,
                time_shift_minutes=args.mt5_time_shift_minutes,
            )
        diagnostics.append(
            diagnose_pair(
                futures_m1,
                mt5_cache[pair.mt5_symbol],
                pair,
                max_lag_minutes=args.max_lag_minutes,
            )
        )

    payload = write_mapping_report(
        diagnostics,
        output_path=args.output,
        inputs={
            "dbn_paths": [str(path) for path in dbn_paths],
            "mt5_dir": args.mt5_dir,
            "pairs": [f"{pair.futures_symbol}:{pair.mt5_symbol}" for pair in pairs],
            "start": args.start,
            "end": args.end,
            "max_lag_minutes": args.max_lag_minutes,
            "mt5_time_shift_minutes": args.mt5_time_shift_minutes,
        },
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"wrote {args.output}")
        for row in payload["diagnostics"]:
            print(
                f"{row['futures_symbol']}->{row['mt5_symbol']}: "
                f"aligned={row['aligned_minutes']} "
                f"corr0={row['zero_lag_return_corr']} "
                f"best_lag={row['best_lag_minutes']} "
                f"best_corr={row['best_lag_corr']}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
