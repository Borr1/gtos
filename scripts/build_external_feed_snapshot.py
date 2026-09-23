#!/usr/bin/env python3
"""Build a shadow external-feed feature snapshot from the local cache.

This utility reads ``data/external/normalized`` and optionally writes a feature
snapshot under ``data/external/features``. It does not import or mutate live
trading components.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    SOURCE_REGISTRY,
    ExternalFeedStore,
    build_feature_snapshot,
    ensure_utc,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external)",
    )
    parser.add_argument("--symbol", required=True, help="GTOS symbol, e.g. XAUUSD")
    parser.add_argument(
        "--candle-close",
        required=True,
        help="Candle close timestamp, ISO-8601 UTC preferred",
    )
    parser.add_argument(
        "--source",
        action="append",
        choices=sorted(SOURCE_REGISTRY),
        help="Source to include; repeatable. Default includes all registered sources.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write the snapshot under data/external/features/{SYMBOL}/",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = ExternalFeedStore(args.root)
    sources = args.source or sorted(SOURCE_REGISTRY)
    source_rows = {
        source: store.read_latest_normalized_rows(source)
        for source in sources
    }
    missing = [source for source, rows in source_rows.items() if not rows]
    snapshot = build_feature_snapshot(
        symbol=args.symbol,
        candle_close_utc=args.candle_close,
        source_rows=source_rows,
    )
    if args.write:
        path = store.write_feature_snapshot(
            args.symbol,
            ensure_utc(args.candle_close),
            snapshot,
        )
        print(f"wrote {path}", file=sys.stderr)
    if missing:
        print(f"missing cached rows: {', '.join(missing)}", file=sys.stderr)
    print(json.dumps(snapshot, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
