#!/usr/bin/env python3
"""Read-only MT5 tick export for V4U ordered-path replay hydration.

Writes ordered tick JSONL files under ``data/mt5_research_exports/<label>`` and
never places, modifies, or cancels orders.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
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
from scripts.inspect_mt5_tick_availability import ProbeWindow, parse_windows  # noqa: E402
from src.components.external_feeds import safe_slug, utc_now  # noqa: E402
from src.utils.broker_clock import (  # noqa: E402
    BrokerClockRule,
    UnknownBrokerClockError,
    broker_epoch_to_utc,
    resolve_rule,
    utc_to_broker_naive,
)

# F7: MT5 reports tick ``time``/``time_msc`` in the BROKER SERVER's wall clock. This
# script labelled them UTC. ``src/components/tick_capture.py`` already fixed the same
# defect on the live capture path (see its docstring, "Broker-offset convention,
# Issue #16") and this is the offline equivalent: keep the raw broker ``time_msc`` as
# the dedup/reconciliation key, correct ``ts_utc`` to genuine UTC, and translate the
# request window so the exported range is the range that was asked for.



def export_research_ticks(
    *,
    mt5_module: Any,
    specs: Iterable[SymbolSpec],
    windows: Iterable[ProbeWindow],
    output_dir: Path,
    copy_ticks_flag: int,
    chunk: timedelta | None = None,
    reuse_existing: bool = False,
    clock: BrokerClockRule | None = None,
) -> dict[str, Any]:
    """``windows`` are true UTC; ``clock`` translates them into broker time and back."""
    output_dir.mkdir(parents=True, exist_ok=True)
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
        for window in windows:
            key = f"{spec.file_symbol}_{safe_slug(window.label)}_TICK"
            tick_dir = output_dir / "ticks" / spec.file_symbol
            tick_path = tick_dir / f"{safe_slug(window.label)}_ticks.jsonl"
            if reuse_existing and tick_path.exists():
                stats = _read_existing_ticks_jsonl_stats(
                    tick_path,
                    start=window.start,
                    end=window.end,
                )
                request_stats = {
                    "chunks_requested": 0,
                    "chunks_with_rows": 0,
                    "empty_chunks": 0,
                    "raw_rows_returned": stats["rows"],
                    "last_empty_chunk_error": None,
                    "reused_existing_path": True,
                }
            else:
                ticks, request_stats = _copy_ticks_range_chunked(
                    mt5_module=mt5_module,
                    symbol=spec.mt5_symbol,
                    start=_tick_request_bound(window.start, clock),
                    end=_tick_request_bound(window.end, clock),
                    copy_ticks_flag=copy_ticks_flag,
                    chunk=chunk,
                )
                stats = _write_ticks_jsonl(
                    tick_path,
                    ticks,
                    start=window.start,
                    end=window.end,
                    clock=clock,
                )
            if stats["rows"] == 0:
                errors.append(
                    {
                        "file_symbol": spec.file_symbol,
                        "mt5_symbol": spec.mt5_symbol,
                        "window": window.label,
                        "error": f"no_ticks:{mt5_module.last_error()}",
                    }
                )
            stats.update(
                {
                    "file_symbol": spec.file_symbol,
                    "mt5_symbol": spec.mt5_symbol,
                    "timeframe": "TICK",
                    "window": window.label,
                    "request_start_utc": window.start.isoformat(),
                    "request_end_utc": window.end.isoformat(),
                    "path": str(tick_path),
                    **request_stats,
                }
            )
            files[key] = stats
    return {"files": files, "errors": errors}


def _read_existing_ticks_jsonl_stats(
    path: Path,
    *,
    start: datetime,
    end: datetime,
) -> dict[str, Any]:
    rows = 0
    first_time: str | None = None
    last_time: str | None = None
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            timestamp = row.get("ts_utc") or row.get("time")
            if not timestamp:
                continue
            try:
                parsed = _parse_utc(timestamp)
            except (TypeError, ValueError):
                continue
            if not (start <= parsed < end):
                continue
            rows += 1
            timestamp_text = parsed.isoformat()
            if first_time is None:
                first_time = timestamp_text
            last_time = timestamp_text
    return {
        "rows": rows,
        "first": first_time,
        "last": last_time,
    }


def enrich_tick_export_result_for_manifest(
    *,
    export_result: dict[str, Any],
    account: Any,
    provenance: dict[str, Any],
    manifest_path: Path,
) -> dict[str, Any]:
    files = export_result.get("files")
    if isinstance(files, dict):
        for file_payload in files.values():
            if not isinstance(file_payload, dict):
                continue
            source_path = Path(str(file_payload.get("path") or ""))
            rows = file_payload.get("rows")
            identity = account_identity_payload(account)
            file_payload.update(
                {
                    "row_count": rows,
                    "sha256": _file_sha256(source_path) if source_path.exists() else None,
                    "source_server_redacted": identity["server_redacted"],
                    "source_server_hash": identity["server_hash"],
                    "source_account_redacted": identity["login_redacted"],
                    "source_account_hash": identity["login_hash"],
                    "source_broker": provenance.get("source_broker"),
                    "source_role": provenance.get("source_role"),
                    "source_truth_scope": provenance.get("source_truth_scope"),
                    "replaces_missing_frozen_path_source": provenance.get(
                        "replaces_missing_frozen_path_source"
                    ),
                    "not_redacted_account_native": provenance.get("not_redacted_account_native"),
                    "broker_lifecycle_truth_satisfied": False,
                    "asof_decision_truth_satisfied": False,
                    "export_tool": "scripts/export_mt5_research_ticks.py",
                    "manifest_path": str(manifest_path),
                }
            )
    return export_result


def _copy_ticks_range_chunked(
    *,
    mt5_module: Any,
    symbol: str,
    start: datetime,
    end: datetime,
    copy_ticks_flag: int,
    chunk: timedelta | None,
) -> tuple[list[Any], dict[str, Any]]:
    windows = list(_iter_time_windows(start, end, chunk=chunk))
    rows: list[Any] = []
    chunks_with_rows = 0
    empty_chunks = 0
    last_error: Any = None
    for window_start, window_end in windows:
        ticks = mt5_module.copy_ticks_range(
            symbol,
            window_start,
            window_end,
            copy_ticks_flag,
        )
        if ticks is None or len(ticks) == 0:
            empty_chunks += 1
            last_error = mt5_module.last_error()
            continue
        chunks_with_rows += 1
        rows.extend(list(ticks))
    return rows, {
        "chunks_requested": len(windows),
        "chunks_with_rows": chunks_with_rows,
        "empty_chunks": empty_chunks,
        "raw_rows_returned": len(rows),
        "last_empty_chunk_error": str(last_error) if last_error is not None else None,
    }


def _iter_time_windows(
    start: datetime,
    end: datetime,
    *,
    chunk: timedelta | None,
) -> Iterable[tuple[datetime, datetime]]:
    if chunk is None:
        yield start, end
        return
    if chunk <= timedelta(0):
        raise ValueError("chunk must be positive")
    cursor = start
    while cursor < end:
        chunk_end = min(cursor + chunk, end)
        yield cursor, chunk_end
        cursor = chunk_end


def _tick_request_bound(instant: datetime, clock: BrokerClockRule | None) -> datetime:
    """True-UTC bound -> the broker wall clock ``copy_ticks_range`` compares against."""
    if clock is None:
        return instant
    return utc_to_broker_naive(instant, clock).replace(tzinfo=timezone.utc)


def _write_ticks_jsonl(
    path: Path,
    ticks: Iterable[Any],
    *,
    start: datetime,
    end: datetime,
    clock: BrokerClockRule | None = None,
) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [_tick_payload(tick, clock) for tick in ticks]
    rows = [
        row
        for row in rows
        if row.get("ts_utc") and start <= _parse_utc(row["ts_utc"]) < end
    ]
    rows.sort(key=lambda row: str(row.get("ts_utc") or ""))
    first_time = rows[0]["ts_utc"] if rows else None
    last_time = rows[-1]["ts_utc"] if rows else None
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "rows": len(rows),
        "first": first_time,
        "last": last_time,
        # ``time_msc`` stays the RAW broker millisecond epoch --- it is the dedup and
        # broker-reconciliation key, and tick_capture.py keeps it raw for the same
        # reason. Only ``ts_utc``/``time`` are corrected, so a reader must not assume
        # the two agree.
        "time_column_basis": "true_utc" if clock is not None else "broker_server_local",
        "time_msc_basis": "broker_server_local_raw",
        **(clock.provenance() if clock is not None else {
            "broker_clock_rule": "uncorrected_broker_local",
            "broker_clock_kind": "uncorrected",
            "broker_clock_evidence": "No correction applied; timestamps are broker wall clock.",
        }),
    }


def _tick_payload(tick: Any, clock: BrokerClockRule | None = None) -> dict[str, Any]:
    time_msc = _tick_field(tick, "time_msc")
    time_raw = _tick_field(tick, "time")
    timestamp = _tick_timestamp(time_msc=time_msc, time_raw=time_raw, clock=clock)
    return {
        "ts_utc": timestamp.isoformat() if timestamp else None,
        "time": timestamp.isoformat() if timestamp else None,
        "time_msc": _int_or_none(time_msc),
        "bid": _float_or_none(_tick_field(tick, "bid")),
        "ask": _float_or_none(_tick_field(tick, "ask")),
        "last": _float_or_none(_tick_field(tick, "last")),
        "volume": _float_or_none(_tick_field(tick, "volume")),
        "flags": _int_or_none(_tick_field(tick, "flags")),
        "volume_real": _float_or_none(_tick_field(tick, "volume_real")),
    }


def _tick_field(tick: Any, field: str) -> Any:
    if isinstance(tick, Mapping):
        return tick.get(field)
    names = getattr(getattr(tick, "dtype", None), "names", None) or ()
    if field not in names:
        return None
    try:
        return tick[field]
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _tick_timestamp(
    *, time_msc: Any, time_raw: Any, clock: BrokerClockRule | None = None
) -> datetime | None:
    """Broker tick epoch -> true UTC.

    ``clock=None`` reproduces the pre-2026-07-26 behaviour bit-exactly, which keeps
    every existing caller and test on its old contract; the exporter always passes one.
    """
    try:
        if time_msc not in (None, ""):
            epoch = int(time_msc) / 1000.0
        elif time_raw not in (None, ""):
            epoch = float(int(time_raw))
        else:
            return None
    except (TypeError, ValueError, OverflowError):
        return None
    try:
        if clock is None:
            return datetime.fromtimestamp(epoch, tz=timezone.utc)
        return broker_epoch_to_utc(epoch, clock)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _parse_utc(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        required=True,
        help="LABEL:START_UTC,END_UTC or LABEL:START_UTC:END_UTC. Repeatable.",
    )
    parser.add_argument("--terminal-path", help="Optional terminal64.exe path.")
    parser.add_argument("--label", default=None)
    parser.add_argument(
        "--output-root",
        default="data/mt5_research_exports",
        help="Root for ignored read-only tick export artifacts.",
    )
    parser.add_argument(
        "--chunk-minutes",
        type=float,
        help="Split copy_ticks_range calls into N-minute windows.",
    )
    parser.add_argument(
        "--reuse-existing",
        action="store_true",
        help=(
            "Reuse already-written tick JSONL files for matching symbol/window "
            "exports and include them in the manifest instead of re-copying."
        ),
    )
    parser.add_argument(
        "--yes-live-readonly",
        action="store_true",
        help="Allow read-only export from a live account. No orders are sent.",
    )
    clock_group = parser.add_argument_group(
        "broker clock (F7)",
        "MT5 reports tick epochs in the broker server's wall clock; the exported time "
        "base is declared in the manifest either way.",
    )
    clock_group.add_argument(
        "--broker-clock",
        default="auto",
        help="MT5 server name whose measured clock rule to apply (default: auto, from "
             "account_info().server). Unknown servers fail closed.",
    )
    clock_group.add_argument(
        "--no-broker-clock-correction",
        action="store_true",
        help="Emit broker-local tick stamps, the pre-2026-07-26 behaviour, declared as such.",
    )
    add_bridge_args(parser)
    add_source_provenance_args(parser)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    specs = parse_symbol_specs(args.symbol or default_symbol_specs_for_args(args))
    windows = parse_windows(args.window)
    label = safe_slug(args.label or "mt5_tick_export")
    output_dir = Path(args.output_root) / label
    chunk = (
        timedelta(minutes=args.chunk_minutes)
        if args.chunk_minutes is not None
        else None
    )
    if chunk is not None and chunk <= timedelta(0):
        raise ValueError("--chunk-minutes must be positive")
    provenance = source_provenance_from_args(args)

    mt5, mt5_client_kind = initialize_mt5_client(args)
    try:
        account = mt5.account_info()
        if account is None:
            raise RuntimeError("MT5 account_info returned None")
        live_account = getattr(account, "trade_mode", 0) != 0
        if live_account and not args.yes_live_readonly:
            raise RuntimeError(
                "connected account is live; re-run with --yes-live-readonly "
                "to confirm read-only export"
            )
        terminal = mt5.terminal_info()
        if args.no_broker_clock_correction:
            tick_clock = None
        else:
            server = args.broker_clock
            if server == "auto":
                # Fail closed, exactly as the OHLCV exporter does. Falling back to a
                # default server would silently apply FTMO's calendar to an
                # unidentified account --- a guess, which is the defect this repair
                # exists to remove.
                server = getattr(account, "server", None)
                if not server:
                    raise UnknownBrokerClockError(
                        "--broker-clock auto could not read account_info().server. Pass the "
                        "server name explicitly, or --no-broker-clock-correction to declare "
                        "an uncorrected export."
                    )
            tick_clock = resolve_rule(server)
        export_result = export_research_ticks(
            mt5_module=mt5,
            specs=specs,
            windows=windows,
            output_dir=output_dir,
            copy_ticks_flag=mt5.COPY_TICKS_ALL,
            chunk=chunk,
            reuse_existing=args.reuse_existing,
            clock=tick_clock,
        )
        manifest_path = output_dir / "manifest.json"
        export_result = enrich_tick_export_result_for_manifest(
            export_result=export_result,
            account=account,
            provenance=provenance,
            manifest_path=manifest_path,
        )
        manifest = {
            "schema_version": "mt5_research_tick_export_v1",
            "created_at_utc": utc_now().isoformat(),
            "read_only": True,
            "label": label,
            "chunk_minutes": args.chunk_minutes,
            "output_dir": str(output_dir),
            "manifest_path": str(manifest_path),
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
            "source_provenance": provenance,
            **export_result,
        }
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0 if not manifest["errors"] else 2
    finally:
        close_mt5_client(mt5, mt5_client_kind)


if __name__ == "__main__":
    raise SystemExit(main())
