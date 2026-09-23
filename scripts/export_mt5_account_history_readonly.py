#!/usr/bin/env python3
"""Read-only MT5 account/deal-history exporter.

Default mode is a dry-run query plan. Use ``--execute`` to import
MetaTrader5, initialize the terminal, read historical deals, and write JSONL.
The script never sends/modifies/cancels orders.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "mt5_account_history_deal_export_v1"


def parse_day(value: str, *, end: bool = False) -> datetime:
    day = datetime.fromisoformat(value).date()
    clock = time(23, 59, 59) if end else time(0, 0, 0)
    return datetime.combine(day, clock, tzinfo=timezone.utc)


def normalize_deal(deal: Any) -> dict[str, Any]:
    if hasattr(deal, "_asdict"):
        raw = dict(deal._asdict())
    elif isinstance(deal, dict):
        raw = dict(deal)
    else:
        raw = {name: getattr(deal, name) for name in dir(deal) if not name.startswith("_")}
    allowed_fields = (
        "ticket",
        "order",
        "position_id",
        "entry",
        "time",
        "time_msc",
        "type",
        "volume",
        "price",
        "profit",
        "commission",
        "swap",
        "fee",
        "magic",
        "reason",
        "symbol",
        "comment",
    )
    raw = {key: raw.get(key) for key in allowed_fields if key in raw}
    if raw.get("time") is not None:
        try:
            raw["time_utc"] = datetime.fromtimestamp(int(raw["time"]), tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            raw["time_utc"] = None
    raw["schema_version"] = SCHEMA_VERSION
    raw["source"] = "MT5.history_deals_get"
    raw["read_only_export"] = True
    return raw


def build_query_plan(
    *,
    start: datetime,
    end: datetime,
    symbol: str | None,
    position_id: int | None,
    output: Path,
) -> dict[str, Any]:
    return {
        "schema_version": "mt5_account_history_readonly_query_plan_v1",
        "start_utc": start.isoformat(),
        "end_utc": end.isoformat(),
        "symbol_filter": symbol,
        "position_id_filter": position_id,
        "output": str(output),
        "read_only": True,
        "calls": ["MetaTrader5.initialize", "MetaTrader5.history_deals_get", "MetaTrader5.shutdown"],
        "no_order_calls": True,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def execute_export(
    *,
    start: datetime,
    end: datetime,
    symbol: str | None,
    position_id: int | None,
    output: Path,
) -> int:
    import MetaTrader5 as mt5  # type: ignore[import-not-found]

    if not mt5.initialize():
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    try:
        deals = mt5.history_deals_get(start, end)
        rows = [normalize_deal(deal) for deal in (deals or [])]
        if symbol:
            rows = [row for row in rows if str(row.get("symbol") or "") == symbol]
        if position_id is not None:
            rows = [row for row in rows if row.get("position_id") == position_id]
        write_jsonl(output, rows)
        print(json.dumps({"deals_exported": len(rows), "output": str(output)}, sort_keys=True))
        return 0
    finally:
        mt5.shutdown()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="UTC start date, YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="UTC end date, YYYY-MM-DD")
    parser.add_argument("--symbol", default=None, help="Optional exact MT5 symbol filter")
    parser.add_argument("--position-id", type=int, default=None, help="Optional exact MT5 position_id filter")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true", help="Actually query MT5; otherwise print a dry-run plan")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    start = parse_day(args.start)
    end = parse_day(args.end, end=True)
    if end < start:
        raise SystemExit("--end must be >= --start")
    if not args.execute:
        print(
            json.dumps(
                build_query_plan(
                    start=start,
                    end=end,
                    symbol=args.symbol,
                    position_id=args.position_id,
                    output=args.output,
                ),
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    return execute_export(
        start=start,
        end=end,
        symbol=args.symbol,
        position_id=args.position_id,
        output=args.output,
    )


if __name__ == "__main__":
    raise SystemExit(main())
