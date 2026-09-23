#!/usr/bin/env python3
"""Report Phase 3 external-feed credential and cache status.

Read-only utility. It does not fetch data and does not touch live trading state.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

try:  # pragma: no cover - exercised by operator environment, not unit tests
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env", override=False)
    load_dotenv(PROJECT_ROOT / ".env.local", override=True)
except ImportError:  # pragma: no cover
    pass

from src.components.external_feeds import (  # noqa: E402
    DEFAULT_EXTERNAL_DATA_ROOT,
    ExternalFeedStore,
    external_feed_env_status,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show external free-feed cache + credential readiness."
    )
    parser.add_argument(
        "--root",
        default=str(DEFAULT_EXTERNAL_DATA_ROOT),
        help="External feed cache root (default: data/external)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON.",
    )
    parser.add_argument(
        "--source",
        help="Optional source filter, e.g. fred, wgc, flashalpha_gex.",
    )
    parser.add_argument(
        "--include-legacy-source-status",
        action="store_true",
        help="Also show old source-level status files when keyed statuses exist.",
    )
    args = parser.parse_args()

    store = ExternalFeedStore(args.root)
    statuses = store.list_statuses(source=args.source)
    if not args.include_legacy_source_status:
        keyed_sources = {status.source for status in statuses if status.status_key}
        statuses = [
            status
            for status in statuses
            if status.status_key or status.source not in keyed_sources
        ]
    payload = {
        "root": str(Path(args.root)),
        "credentials_present": external_feed_env_status(),
        "statuses": [status.to_dict() for status in statuses],
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"External feed root: {payload['root']}")
    print("\nCredentials:")
    for source, vars_present in payload["credentials_present"].items():
        if not vars_present:
            print(f"  {source}: no credentials required")
            continue
        rendered = ", ".join(
            f"{name}={'present' if present else 'missing'}"
            for name, present in vars_present.items()
        )
        print(f"  {source}: {rendered}")

    print("\nCached source statuses:")
    if not payload["statuses"]:
        print("  none")
    for status in payload["statuses"]:
        print(
            f"  {status['status_id']}: {status['status']} "
            f"rows={status['row_count']} fetched={status['fetched_at_utc']} "
            f"message={status['message']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
