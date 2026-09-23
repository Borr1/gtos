#!/usr/bin/env python3
"""Read-only MT5 tick-history availability probe.

This script asks the connected MT5 terminal for tick counts over explicit time
windows. It does not export full tick data and never places/modifies/cancels
orders. Use it before any historical tick backfill attempt to identify broker
or terminal retention limits.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.export_mt5_research_ohlcv import (  # noqa: E402
    SymbolSpec,
    account_identity_payload,
    add_bridge_args,
    add_source_provenance_args,
    close_mt5_client,
    default_symbol_specs_for_args,
    initialize_mt5_client,
    parse_symbol_specs,
    source_provenance_from_args,
)
from src.components.external_feeds import safe_slug, utc_now  # noqa: E402


@dataclass(frozen=True)
class ProbeWindow:
    label: str
    start: datetime
    end: datetime


DEFAULT_WINDOWS = (
    "recent_ny:2026-04-30T13:00:00Z:2026-04-30T14:00:00Z",
    "current_week_ny:2026-04-27T13:00:00Z:2026-04-27T14:00:00Z",
    "m1_boundary_ny:2026-01-20T13:00:00Z:2026-01-20T14:00:00Z",
    "pre_m5_boundary_ny:2025-12-01T13:00:00Z:2025-12-01T14:00:00Z",
)


def inspect_tick_availability(
    *,
    mt5_module: Any,
    specs: Iterable[SymbolSpec],
    windows: Iterable[ProbeWindow],
    copy_ticks_flag: int,
) -> dict[str, Any]:
    """Return tick-count metadata for each symbol/window."""

    files: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    selected_windows = list(windows)
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
        for window in selected_windows:
            key = f"{spec.file_symbol}_{safe_slug(window.label)}"
            ticks = mt5_module.copy_ticks_range(
                spec.mt5_symbol,
                window.start,
                window.end,
                copy_ticks_flag,
            )
            if ticks is None:
                errors.append(
                    {
                        "file_symbol": spec.file_symbol,
                        "mt5_symbol": spec.mt5_symbol,
                        "window": window.label,
                        "error": f"copy_ticks_range_none:{mt5_module.last_error()}",
                    }
                )
                files[key] = _empty_window_payload(spec, window, mt5_module.last_error())
                continue
            files[key] = {
                "file_symbol": spec.file_symbol,
                "mt5_symbol": spec.mt5_symbol,
                "window": window.label,
                "start": window.start.isoformat(),
                "end": window.end.isoformat(),
                "rows": int(len(ticks)),
                "first_tick_utc": _tick_time_iso(ticks[0]) if len(ticks) else None,
                "last_tick_utc": _tick_time_iso(ticks[-1]) if len(ticks) else None,
                "has_ticks": bool(len(ticks)),
                "last_error": str(mt5_module.last_error()),
            }
    return {"files": files, "errors": errors}


def write_probe_artifact(
    *,
    output_root: str | Path,
    label: str,
    payload: dict[str, Any],
) -> Path:
    output_dir = Path(output_root) / "tick_availability"
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{safe_slug(label)}_{utc_now():%Y%m%dT%H%M%SZ}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--symbol",
        action="append",
        help="FILE_SYMBOL:MT5_SYMBOL mapping; repeatable. Defaults to Phase 3 symbols.",
    )
    parser.add_argument(
        "--window",
        action="append",
        help=(
            "LABEL:START_UTC:END_UTC. Repeatable. "
            "Defaults to recent/current-week/Jan-2026/Dec-2025 NY windows."
        ),
    )
    parser.add_argument("--terminal-path", help="Optional terminal64.exe path.")
    parser.add_argument("--label", default=None)
    parser.add_argument(
        "--output-root",
        default="data/mt5_research_exports",
        help="Root for ignored probe artifacts.",
    )
    parser.add_argument("--write-json", action="store_true")
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
    specs = parse_symbol_specs(args.symbol or default_symbol_specs_for_args(args))
    windows = parse_windows(args.window or DEFAULT_WINDOWS)
    label = safe_slug(args.label or "mt5_tick_availability_probe")

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
        terminal = mt5.terminal_info()
        result = inspect_tick_availability(
            mt5_module=mt5,
            specs=specs,
            windows=windows,
            copy_ticks_flag=mt5.COPY_TICKS_ALL,
        )
        payload = {
            "schema_version": "mt5_tick_availability_probe_v1",
            "created_at_utc": utc_now().isoformat(),
            "read_only": True,
            "label": label,
            "mt5_client_kind": mt5_client_kind,
            "account": account_identity_payload(account),
            "terminal": {
                "build": getattr(terminal, "build", None),
                "maxbars": getattr(terminal, "maxbars", None),
                "connected": getattr(terminal, "connected", None),
                "path": getattr(terminal, "path", None),
                "data_path": getattr(terminal, "data_path", None),
            },
            "symbols": [spec.__dict__ for spec in specs],
            "windows": [
                {
                    "label": window.label,
                    "start": window.start.isoformat(),
                    "end": window.end.isoformat(),
                }
                for window in windows
            ],
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


def parse_windows(items: Iterable[str]) -> list[ProbeWindow]:
    windows: list[ProbeWindow] = []
    for raw in items:
        parts = raw.split(":", 1)
        if len(parts) != 2:
            raise argparse.ArgumentTypeError(
                f"window must be LABEL:START_UTC:END_UTC, got {raw!r}"
            )
        label, rest = parts
        start_raw, end_raw = _split_window_times(rest, raw)
        start = _parse_utc(start_raw)
        end = _parse_utc(end_raw)
        if end <= start:
            raise argparse.ArgumentTypeError(f"window end must be after start: {raw!r}")
        windows.append(ProbeWindow(label=safe_slug(label), start=start, end=end))
    return windows


def _split_window_times(rest: str, raw: str) -> tuple[str, str]:
    marker = "Z:"
    if marker in rest:
        start_raw, end_raw = rest.split(marker, 1)
        return start_raw + "Z", end_raw
    parts = rest.split(",", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    raise argparse.ArgumentTypeError(
        f"window must be LABEL:START_UTC:END_UTC or LABEL:START_UTC,END_UTC, got {raw!r}"
    )


def _empty_window_payload(
    spec: SymbolSpec,
    window: ProbeWindow,
    last_error: Any,
) -> dict[str, Any]:
    return {
        "file_symbol": spec.file_symbol,
        "mt5_symbol": spec.mt5_symbol,
        "window": window.label,
        "start": window.start.isoformat(),
        "end": window.end.isoformat(),
        "rows": 0,
        "first_tick_utc": None,
        "last_tick_utc": None,
        "has_ticks": False,
        "last_error": str(last_error),
    }


def _parse_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _tick_time_iso(tick: Any) -> str | None:
    if isinstance(tick, Mapping):
        value = tick.get("time_msc")
        if value not in (None, ""):
            try:
                return datetime.fromtimestamp(int(value) / 1000.0, tz=timezone.utc).isoformat()
            except (TypeError, ValueError, OverflowError):
                return None
        value = tick.get("time")
        if value not in (None, ""):
            try:
                return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
            except (TypeError, ValueError, OverflowError):
                return None
        return None
    names = getattr(tick, "dtype", None)
    dtype_names = getattr(names, "names", None) or ()
    try:
        if "time_msc" in dtype_names:
            value = int(tick["time_msc"])
            return datetime.fromtimestamp(value / 1000.0, tz=timezone.utc).isoformat()
        value = int(tick["time"])
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    except (KeyError, TypeError, ValueError, IndexError, OverflowError):
        return None


if __name__ == "__main__":
    raise SystemExit(main())
