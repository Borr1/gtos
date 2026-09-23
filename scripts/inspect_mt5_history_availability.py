#!/usr/bin/env python3
"""Read-only MT5 history availability probe.

This script asks the connected MT5 terminal what OHLCV history is available for
the requested symbols/timeframes/date range, but does not export full candles.
It is intended as a cheap first pass before large research exports.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_mt5_research_ohlcv import (  # noqa: E402
    DEFAULT_SYMBOL_SPECS,
    TIMEFRAME_ATTRS,
    SymbolSpec,
    account_identity_payload,
    add_bridge_args,
    add_source_provenance_args,
    close_mt5_client,
    initialize_mt5_client,
    parse_symbol_specs,
    parse_timeframe_names,
    source_provenance_from_args,
)
from src.components.external_feeds import safe_slug, utc_now  # noqa: E402


DEFAULT_TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
TIMEFRAME_DELTAS = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "M30": timedelta(minutes=30),
    "H1": timedelta(hours=1),
    "H4": timedelta(hours=4),
    "D1": timedelta(days=1),
}


def inspect_history_availability(
    *,
    mt5_module: Any,
    specs: Iterable[SymbolSpec],
    timeframe_names: Iterable[str],
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    """Return availability metadata for each symbol/timeframe."""

    files: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for spec in specs:
        selected = bool(mt5_module.symbol_select(spec.mt5_symbol, True))
        if not selected:
            errors.append(
                {
                    "file_symbol": spec.file_symbol,
                    "mt5_symbol": spec.mt5_symbol,
                    "error": f"symbol_select_failed:{mt5_module.last_error()}",
                }
            )
            continue
        for timeframe_name in timeframe_names:
            timeframe_const = getattr(mt5_module, TIMEFRAME_ATTRS[timeframe_name])
            rates = mt5_module.copy_rates_range(
                spec.mt5_symbol,
                timeframe_const,
                start,
                end,
            )
            key = f"{spec.file_symbol}_{timeframe_name}"
            if rates is None or len(rates) == 0:
                errors.append(
                    {
                        "file_symbol": spec.file_symbol,
                        "mt5_symbol": spec.mt5_symbol,
                        "timeframe": timeframe_name,
                        "error": f"no_rates:{mt5_module.last_error()}",
                    }
                )
                files[key] = {
                    "file_symbol": spec.file_symbol,
                    "mt5_symbol": spec.mt5_symbol,
                    "timeframe": timeframe_name,
                    "rows": 0,
                    "first": None,
                    "last": None,
                    "covers_requested_start": False,
                    "reaches_requested_end": False,
                }
                continue
            first = _rate_time(rates[0])
            last = _rate_time(rates[-1])
            files[key] = {
                "file_symbol": spec.file_symbol,
                "mt5_symbol": spec.mt5_symbol,
                "timeframe": timeframe_name,
                "rows": int(len(rates)),
                "first": first.isoformat(),
                "last": last.isoformat(),
                "has_rows_in_requested_range": first < end and last >= start,
                "covers_requested_start": first <= start <= last,
                "reaches_requested_end": _reaches_requested_end(
                    first,
                    last,
                    end,
                    timeframe_name,
                ),
            }
    return {"files": files, "errors": errors}


def write_probe_artifact(
    *,
    output_root: str | Path,
    label: str,
    payload: dict[str, Any],
) -> Path:
    output_dir = Path(output_root) / "history_availability"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_slug(label)}_{utc_now():%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="UTC start timestamp/date, inclusive.")
    parser.add_argument("--end", required=True, help="UTC end timestamp/date, exclusive.")
    parser.add_argument(
        "--symbol",
        action="append",
        help="FILE_SYMBOL:MT5_SYMBOL mapping; repeatable. Defaults to Phase 3 symbols.",
    )
    parser.add_argument(
        "--timeframes",
        default=",".join(DEFAULT_TIMEFRAMES),
        help="Comma-separated MT5 timeframes.",
    )
    parser.add_argument("--terminal-path", help="Optional terminal64.exe path.")
    parser.add_argument("--label", default=None)
    parser.add_argument(
        "--output-root",
        default="data/mt5_research_exports",
        help="Root for ignored probe artifacts.",
    )
    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write the probe payload under data/mt5_research_exports/history_availability.",
    )
    parser.add_argument(
        "--yes-live-readonly",
        action="store_true",
        help="Allow read-only probe from a live account. No orders are sent.",
    )
    add_bridge_args(parser)
    add_source_provenance_args(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    start = _parse_utc(args.start)
    end = _parse_utc(args.end)
    if end <= start:
        raise ValueError("--end must be after --start")

    specs = parse_symbol_specs(args.symbol or DEFAULT_SYMBOL_SPECS)
    timeframe_names = parse_timeframe_names(args.timeframes)
    label = safe_slug(args.label or f"mt5_history_probe_{start:%Y%m%d}_{end:%Y%m%d}")

    mt5, mt5_client_kind = initialize_mt5_client(args)
    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError("MT5 account_info returned None")
        live_account = getattr(account, "trade_mode", 0) != 0
        if live_account and not args.yes_live_readonly:
            raise RuntimeError(
                "connected account is live; re-run with --yes-live-readonly "
                "to confirm read-only probe"
            )
        result = inspect_history_availability(
            mt5_module=mt5,
            specs=specs,
            timeframe_names=timeframe_names,
            start=start,
            end=end,
        )
        payload = {
            "schema_version": "mt5_history_availability_probe_v1",
            "created_at_utc": utc_now().isoformat(),
            "read_only": True,
            "label": label,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
            "mt5_client_kind": mt5_client_kind,
            "account": account_identity_payload(account),
            "symbols": [spec.__dict__ for spec in specs],
            "timeframes": timeframe_names,
            "source_provenance": source_provenance_from_args(args),
            **result,
        }
        if args.write_json:
            payload["artifact_path"] = str(
                write_probe_artifact(
                    output_root=args.output_root,
                    label=label,
                    payload=payload,
                )
            )
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if not payload["errors"] else 2
    finally:
        close_mt5_client(mt5, mt5_client_kind)


def _parse_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _rate_time(rate: Any) -> datetime:
    return datetime.fromtimestamp(int(rate["time"]), tz=timezone.utc)


def _reaches_requested_end(
    first: datetime,
    last: datetime,
    end: datetime,
    timeframe_name: str,
) -> bool:
    if first >= end:
        return False
    delta = TIMEFRAME_DELTAS.get(timeframe_name.upper(), timedelta())
    return last >= end - delta


if __name__ == "__main__":
    raise SystemExit(main())
