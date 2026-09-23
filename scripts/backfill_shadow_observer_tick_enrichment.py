#!/usr/bin/env python3
"""Backfill MT5 tick summaries for no-AI shadow observer rows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.shadow_observer_tick_enrichment import (  # noqa: E402
    DEFAULT_OUTPUT,
    DEFAULT_SOURCE,
    run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--symbols", default="EURUSD")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    symbol_filter = {item.strip() for item in args.symbols.split(",") if item.strip()}
    summary = run(source_path=args.source, output_path=args.output, symbol_filter=symbol_filter)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
