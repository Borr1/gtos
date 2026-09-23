#!/usr/bin/env python3
"""Read-only MT5 OHLCV export for research substrates.

Writes versioned CSVs under ``data/mt5_research_exports/<label>`` and never
places, modifies, or cancels orders. This exists because the older historical
exporter overwrites ``data/historical_2026`` and has stale broker aliases for
the current redacted_account terminal.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.components.external_feeds import safe_slug, utc_now  # noqa: E402
from src.utils.broker_clock import (  # noqa: E402
    BrokerClockRule,
    UnknownBrokerClockError,
    broker_epoch_to_utc,
    fixed_offset_rule,
    offset_seconds_at_utc,
    resolve_rule,
    utc_to_broker_naive,
)


# ---------------------------------------------------------------------------
# Time base (F7)
# ---------------------------------------------------------------------------
#
# MT5 hands back bar epochs in the BROKER SERVER's wall clock. Decoding them with
# ``fromtimestamp(ts, tz=timezone.utc)`` --- which is what this script did until
# 2026-07-26 --- labels broker time as UTC and shifts every stamp by 2-3 hours.
# Two places have to change together, and missing either one is silent:
#
#   1. the request window sent to ``copy_rates_range``, whose bounds are compared
#      against those same broker-localized epochs, and
#   2. the timestamps written to the CSV.
#
# Correcting only (2) yields correct stamps over a window shifted by the offset.


class UncorrectedClock:
    """Explicitly declared *absence* of correction --- broker local time, labelled so.

    Kept because reproducing a historical export bit-for-bit is sometimes the point.
    It is not the default and it is never silent: the manifest and the per-file
    sidecar both record ``uncorrected_broker_local``, so no consumer can mistake the
    output for UTC.
    """

    name = "uncorrected_broker_local"
    kind = "uncorrected"
    evidence = (
        "No correction applied. Timestamps are the broker server's wall clock. "
        "This is finding F7's original defect, retained deliberately and declared."
    )

    def __init__(self, server: str | None = None) -> None:
        # The server is recorded even though no correction was applied, so
        # research_timebase.read_bars can still correct the file on read. Without it
        # the sidecar declares "broker-local" with no resolvable rule and our own
        # reader raises --- an export nothing can consume.
        self.server = server

    def provenance(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "broker_clock_rule": self.name,
            "broker_clock_kind": self.kind,
            "broker_clock_evidence": self.evidence,
            "time_column_basis": "broker_server_local",
        }
        if self.server:
            payload["broker_clock_server"] = self.server
        return payload


ExportClock = BrokerClockRule | UncorrectedClock


def _is_uncorrected(clock: ExportClock) -> bool:
    """Duck-typed on the declared kind, not on class identity.

    ``isinstance`` is wrong here: this module is loaded by path in tests and by
    ``__main__`` in production, so the same class can exist as two distinct objects
    and identity checks silently take the wrong branch.
    """
    return getattr(clock, "kind", None) == "uncorrected"


def _to_true_utc(broker_epoch: float, clock: ExportClock) -> datetime:
    """Decode one MT5 bar epoch under the declared time base."""
    if _is_uncorrected(clock):
        return datetime.fromtimestamp(broker_epoch, tz=timezone.utc)
    return broker_epoch_to_utc(broker_epoch, clock)


def _request_bound(instant: datetime, clock: ExportClock) -> datetime:
    """Translate a true-UTC window bound into what ``copy_rates_range`` expects.

    MT5 compares the bound against broker-localized bar epochs, so a true-UTC bound
    has to be expressed as broker wall clock first.
    """
    if _is_uncorrected(clock):
        return instant
    return utc_to_broker_naive(instant, clock).replace(tzinfo=timezone.utc)


def resolve_export_clock(args: argparse.Namespace, account: Any) -> ExportClock:
    """Decide the time base for this export, failing closed on anything unknown."""
    if getattr(args, "no_broker_clock_correction", False):
        declared = getattr(args, "broker_clock", None)
        if not declared or declared == "auto":
            declared = _account_get(account, "server")
        return UncorrectedClock(server=declared or None)
    if getattr(args, "broker_clock_offset_hours", None) is not None:
        return fixed_offset_rule(
            float(args.broker_clock_offset_hours),
            evidence=f"operator override via --broker-clock-offset-hours at export time",
        )
    server = getattr(args, "broker_clock", None) or "auto"
    if server == "auto":
        server = _account_get(account, "server")
        if not server:
            raise UnknownBrokerClockError(
                "--broker-clock auto could not read account_info().server. Pass the "
                "server name explicitly, or --broker-clock-offset-hours, or "
                "--no-broker-clock-correction to declare an uncorrected export."
            )
    return resolve_rule(server)


DEFAULT_SYMBOL_SPECS = (
    "XAUUSD:XAUUSD",
    "XAGUSD:XAGUSD",
    "GBPJPY:GBPJPY",
    "USDJPY:USDJPY",
    "GBPUSD:GBPUSD",
    "NAS100:NDX100",
    "US30_cash:US30",
)
FTMO_DEFAULT_SYMBOL_SPECS = (
    "AUDJPY:AUDJPY",
    "AUDUSD:AUDUSD",
    "BTCUSD:BTCUSD",
    "CHFJPY:CHFJPY",
    "ETHUSD:ETHUSD",
    "EURGBP:EURGBP",
    "EURJPY:EURJPY",
    "EURUSD:EURUSD",
    "GBPJPY:GBPJPY",
    "GBPUSD:GBPUSD",
    "GER40:GER40.cash",
    "JP225:JP225.cash",
    "NAS100:US100.cash",
    "NZDUSD:NZDUSD",
    "SPX500:US500.cash",
    "UK100:UK100.cash",
    "UKOIL_cash:UKOIL.cash",
    "US30_cash:US30.cash",
    "USDCAD:USDCAD",
    "USDCHF:USDCHF",
    "USDJPY:USDJPY",
    "USOIL_cash:USOIL.cash",
    "XAGUSD:XAGUSD",
    "XAUUSD:XAUUSD",
)
DEFAULT_TIMEFRAMES = ("M15",)
TIMEFRAME_ATTRS = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "M30": "TIMEFRAME_M30",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}
TIMEFRAME_DELTAS = {
    "M1": timedelta(minutes=1),
    "M5": timedelta(minutes=5),
    "M15": timedelta(minutes=15),
    "M30": timedelta(minutes=30),
    "H1": timedelta(hours=1),
    "H4": timedelta(hours=4),
    "D1": timedelta(days=1),
}

ORDERED_PATH_OVERRIDE_SCOPE = (
    "ordered_price_path_only_not_broker_order_lifecycle_truth"
)


@dataclass(frozen=True)
class SymbolSpec:
    """Mapping from output file symbol to broker terminal symbol."""

    file_symbol: str
    mt5_symbol: str


def parse_symbol_specs(items: Iterable[str]) -> list[SymbolSpec]:
    specs: list[SymbolSpec] = []
    for raw in items:
        item = raw.strip()
        if not item:
            continue
        if ":" in item:
            file_symbol, mt5_symbol = item.split(":", 1)
        else:
            file_symbol = mt5_symbol = item
        file_symbol = file_symbol.strip()
        mt5_symbol = mt5_symbol.strip()
        if not file_symbol or not mt5_symbol:
            raise argparse.ArgumentTypeError(
                f"symbol spec must be FILE_SYMBOL:MT5_SYMBOL, got {raw!r}"
            )
        specs.append(SymbolSpec(file_symbol=file_symbol, mt5_symbol=mt5_symbol))
    return specs


def default_symbol_specs_for_args(args: argparse.Namespace) -> tuple[str, ...]:
    source_broker = str(getattr(args, "source_broker", "") or "").strip().upper()
    if source_broker == "FTMO":
        return FTMO_DEFAULT_SYMBOL_SPECS
    return DEFAULT_SYMBOL_SPECS


def parse_timeframe_names(value: str | Iterable[str]) -> list[str]:
    raw_items = value.split(",") if isinstance(value, str) else list(value)
    names = [item.strip().upper() for item in raw_items if item.strip()]
    unsupported = [name for name in names if name not in TIMEFRAME_ATTRS]
    if unsupported:
        raise argparse.ArgumentTypeError(f"unsupported timeframe(s): {unsupported}")
    return names


def add_source_provenance_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--source-broker",
        help="Broker namespace for this read-only source export, e.g. FTMO.",
    )
    parser.add_argument(
        "--source-role",
        help="Source role label, e.g. owner_authorized_path_override.",
    )
    parser.add_argument(
        "--replaces-missing-frozen-path-source",
        action="store_true",
        help="Mark this source as replacing missing frozen replay path source only.",
    )
    parser.add_argument(
        "--not-redacted_account-native",
        action="store_true",
        help="Mark this source as not redacted_account-native truth.",
    )
    parser.add_argument(
        "--source-truth-scope",
        default=None,
        help="Exact truth scope for the exported data.",
    )
    parser.add_argument("--handoff-run-id", help="V4U handoff run id.")
    parser.add_argument("--handoff-requirement-id", help="V4U requirement id.")
    parser.add_argument(
        "--require-owner-authorized-path-override",
        action="store_true",
        help=(
            "Fail unless source provenance is the owner-authorized path override "
            "contract used by V4U LTF hydration."
        ),
    )


def source_provenance_from_args(args: argparse.Namespace) -> dict[str, Any]:
    provenance = {
        "source_broker": args.source_broker,
        "source_role": args.source_role,
        "replaces_missing_frozen_path_source": bool(
            args.replaces_missing_frozen_path_source
        ),
        "not_redacted_account_native": bool(args.not_redacted_account_native),
        "source_truth_scope": args.source_truth_scope,
        "handoff_run_id": args.handoff_run_id,
        "handoff_requirement_id": args.handoff_requirement_id,
        "broker_lifecycle_truth_satisfied": False,
        "asof_decision_truth_satisfied": False,
    }
    if args.require_owner_authorized_path_override:
        missing = [
            field
            for field in (
                "source_broker",
                "source_role",
                "source_truth_scope",
            )
            if not provenance.get(field)
        ]
        if provenance.get("source_broker") != "FTMO":
            missing.append("source_broker=FTMO")
        if provenance.get("source_role") != "owner_authorized_path_override":
            missing.append("source_role=owner_authorized_path_override")
        if provenance.get("source_truth_scope") != ORDERED_PATH_OVERRIDE_SCOPE:
            missing.append(f"source_truth_scope={ORDERED_PATH_OVERRIDE_SCOPE}")
        if not provenance["replaces_missing_frozen_path_source"]:
            missing.append("replaces_missing_frozen_path_source=true")
        if not provenance["not_redacted_account_native"]:
            missing.append("not_redacted_account_native=true")
        if missing:
            raise RuntimeError(
                "owner-authorized path override provenance missing: "
                + ", ".join(sorted(set(missing)))
            )
    return provenance


def _identifier_hash(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _identifier_redacted(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    if len(text) <= 4:
        return "redacted"
    return f"redacted:{text[:2]}...{text[-2:]}"


def _account_get(account: Any, key: str) -> Any:
    if isinstance(account, dict):
        return account.get(key)
    return getattr(account, key, None)


def account_identity_payload(account: Any) -> dict[str, Any]:
    server = _account_get(account, "server")
    login = _account_get(account, "login")
    trade_mode = _account_get(account, "trade_mode")
    return {
        "server_redacted": _identifier_redacted(server),
        "server_hash": _identifier_hash(server),
        "login_redacted": _identifier_redacted(login),
        "login_hash": _identifier_hash(login),
        "trade_mode": trade_mode,
        "live_account": trade_mode != 0,
    }


def add_bridge_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--bridge-host",
        help="Use siliconmetatrader5 localhost bridge host instead of local MetaTrader5 import.",
    )
    parser.add_argument("--bridge-port", type=int, default=8001)
    parser.add_argument(
        "--prefer-silicon-bridge",
        action="store_true",
        help="Prefer siliconmetatrader5 bridge when available.",
    )


def initialize_mt5_client(args: argparse.Namespace) -> tuple[Any, str]:
    if args.bridge_host or args.prefer_silicon_bridge:
        from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415

        client = MetaTrader5(
            host=args.bridge_host or "localhost",
            port=args.bridge_port,
            keepalive=True,
        )
        if not client.initialize():
            raise RuntimeError(f"MT5 bridge initialize failed: {client.last_error()}")
        return client, "siliconmetatrader5_bridge"

    try:
        import MetaTrader5 as mt5  # noqa: PLC0415
    except ModuleNotFoundError:
        from siliconmetatrader5 import MetaTrader5  # noqa: PLC0415

        client = MetaTrader5(host="localhost", port=args.bridge_port, keepalive=True)
        if not client.initialize():
            raise RuntimeError(f"MT5 bridge initialize failed: {client.last_error()}")
        return client, "siliconmetatrader5_bridge"

    init_kwargs = {"path": args.terminal_path} if args.terminal_path else {}
    if not mt5.initialize(**init_kwargs):
        raise RuntimeError(f"MT5 initialize failed: {mt5.last_error()}")
    return mt5, "MetaTrader5_python"


def close_mt5_client(mt5_client: Any, client_kind: str) -> None:
    if client_kind == "siliconmetatrader5_bridge":
        close = getattr(mt5_client, "close", None)
        if callable(close):
            close()
        return
    mt5_client.shutdown()


def export_research_ohlcv(
    *,
    mt5_module: Any,
    specs: Iterable[SymbolSpec],
    timeframe_names: Iterable[str],
    start: datetime,
    end: datetime,
    output_dir: Path,
    clock: ExportClock,
    chunk: timedelta | None = None,
    history_refresh_retries: int = 0,
    history_refresh_delay_seconds: float = 0.0,
) -> dict[str, Any]:
    """Copy MT5 rates to CSV files and return a manifest payload.

    ``start``/``end`` are true UTC. They are translated into the broker's wall clock
    for the request and the corrected stamps are filtered against them afterwards,
    so the exported range means what the caller asked for.
    """

    output_dir.mkdir(parents=True, exist_ok=True)
    # No widening. The UTC -> broker mapping is exact and strictly monotonic (New York
    # wall clock is monotonic in UTC), so a contiguous true-UTC window maps to a
    # contiguous broker-time window with no gap, including across a DST seam. Widening
    # would only inflate the chunk count and re-trim to the same rows.
    request_start = _request_bound(start, clock)
    request_end = _request_bound(end, clock)
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
            rates, request_stats = _copy_rates_range_chunked(
                mt5_module=mt5_module,
                symbol=spec.mt5_symbol,
                timeframe=timeframe_const,
                start=request_start,
                end=request_end,
                chunk=chunk,
                history_refresh_retries=history_refresh_retries,
                history_refresh_delay_seconds=history_refresh_delay_seconds,
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
                continue
            csv_path = output_dir / f"{spec.file_symbol}_{timeframe_name}.csv"
            stats = _write_rates_csv(
                csv_path,
                rates,
                start=start,
                end=end,
                timeframe_name=timeframe_name,
                clock=clock,
            )
            stats.update(
                {
                    "file_symbol": spec.file_symbol,
                    "mt5_symbol": spec.mt5_symbol,
                    "timeframe": timeframe_name,
                    "path": str(csv_path),
                    **request_stats,
                }
            )
            files[key] = stats
    return {"files": files, "errors": errors}


def enrich_export_result_for_manifest(
    *,
    export_result: dict[str, Any],
    account: Any,
    provenance: dict[str, Any],
    start: datetime,
    end: datetime,
    manifest_path: Path,
    clock: ExportClock,
) -> dict[str, Any]:
    """Add durable source-capture fields required by V4U import validation.

    Also stamps each file with its time base. An export whose offset is undeclared
    is the same defect wearing a correction, so this is not optional decoration:
    every file gets the rule, the evidence, and the offsets actually applied, in the
    manifest and in a sidecar beside the CSV so a file that travels alone stays
    self-describing.
    """

    clock_provenance = clock.provenance()
    files = export_result.get("files")
    if isinstance(files, dict):
        for file_payload in files.values():
            if not isinstance(file_payload, dict):
                continue
            source_path = Path(str(file_payload.get("path") or ""))
            rows = file_payload.get("rows")
            identity = account_identity_payload(account)
            file_payload.setdefault("time_column_basis", "true_utc")
            for key, value in clock_provenance.items():
                file_payload.setdefault(key, value)
            file_payload.update(
                {
                    "row_count": rows,
                    "sha256": _file_sha256(source_path) if source_path.exists() else None,
                    "request_start_utc": start.isoformat(),
                    "request_end_utc": end.isoformat(),
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
                    "export_tool": "scripts/export_mt5_research_ohlcv.py",
                    "manifest_path": str(manifest_path),
                }
            )
            if source_path.name:
                _write_timebase_sidecar(source_path, file_payload)
    return export_result


def _write_timebase_sidecar(csv_path: Path, file_payload: dict[str, Any]) -> None:
    """Write ``<file>.timebase.json`` next to an exported CSV.

    The CSV header stays ``time,open,high,low,close,volume`` --- renaming the column
    would break every existing reader --- so the declaration lives beside it. Any
    consumer that cannot find a sidecar for a file is reading data of unknown time
    base and should say so rather than assume UTC.
    """
    sidecar = csv_path.with_suffix(csv_path.suffix + ".timebase.json")
    keys = (
        "broker_clock_rule",
        "broker_clock_kind",
        "broker_clock_evidence",
        "broker_clock_anchor_zone",
        "broker_clock_anchor_offset_hours",
        "broker_clock_fixed_offset_hours",
        "broker_clock_server",
        "broker_offset_seconds_applied",
        "time_column_basis",
        "source_server_hash",
        "source_broker",
        "export_tool",
        "manifest_path",
        "first",
        "last",
        "row_count",
    )
    payload = {key: file_payload[key] for key in keys if key in file_payload}
    payload["time_column"] = "time"
    payload["schema_version"] = "gtos_timebase_sidecar_v1"
    sidecar.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copy_rates_range_chunked(
    *,
    mt5_module: Any,
    symbol: str,
    timeframe: int,
    start: datetime,
    end: datetime,
    chunk: timedelta | None,
    history_refresh_retries: int = 0,
    history_refresh_delay_seconds: float = 0.0,
) -> tuple[list[Any] | None, dict[str, Any]]:
    """Read MT5 rates in one or more windows and preserve request metadata."""

    windows = list(_iter_time_windows(start, end, chunk=chunk))
    by_time: dict[int, Any] = {}
    raw_rows = 0
    chunks_with_rows = 0
    empty_chunks = 0
    last_error: Any = None
    refresh_attempts = 0
    refresh_improvements = 0
    for window_start, window_end in windows:
        best_rates: Any = None
        best_key = (-1, -1)
        retry_count = history_refresh_retries if window_end == end else 0
        for attempt in range(retry_count + 1):
            if attempt and history_refresh_delay_seconds > 0:
                time.sleep(history_refresh_delay_seconds)
            rates = mt5_module.copy_rates_range(
                symbol,
                timeframe,
                window_start,
                window_end,
            )
            if attempt:
                refresh_attempts += 1
            if rates is None or len(rates) == 0:
                continue
            timestamps = [
                timestamp
                for timestamp in (_rate_timestamp(rec) for rec in rates)
                if timestamp is not None
            ]
            response_key = (max(timestamps, default=-1), len(rates))
            if response_key > best_key:
                if best_rates is not None:
                    refresh_improvements += 1
                best_rates = rates
                best_key = response_key
        rates = best_rates
        if rates is None or len(rates) == 0:
            empty_chunks += 1
            last_error = mt5_module.last_error()
            continue
        chunks_with_rows += 1
        for rec in rates:
            raw_rows += 1
            timestamp = _rate_timestamp(rec)
            if timestamp is None:
                continue
            by_time[timestamp] = rec
    stats = {
        "chunks_requested": len(windows),
        "chunks_with_rows": chunks_with_rows,
        "empty_chunks": empty_chunks,
        "raw_rows_returned": raw_rows,
        "duplicate_rows_dropped": max(raw_rows - len(by_time), 0),
        "last_empty_chunk_error": str(last_error) if last_error is not None else None,
        "history_refresh_retries_configured": int(history_refresh_retries),
        "history_refresh_delay_seconds": float(history_refresh_delay_seconds),
        "history_refresh_attempts": refresh_attempts,
        "history_refresh_improvements": refresh_improvements,
    }
    if not by_time:
        return None, stats
    return [by_time[key] for key in sorted(by_time)], stats


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


def _write_rates_csv(
    path: Path,
    rates: Any,
    *,
    start: datetime,
    end: datetime,
    timeframe_name: str,
    clock: ExportClock,
) -> dict[str, Any]:
    first_time: str | None = None
    last_time: str | None = None
    count = 0
    previous_ts: datetime | None = None
    gap_count = 0
    max_gap_seconds = 0.0
    offsets_seen: set[int] = set()
    expected_delta = TIMEFRAME_DELTAS[timeframe_name.upper()]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["time", "open", "high", "low", "close", "volume"])
        for rec in rates:
            timestamp_raw = _rate_timestamp(rec)
            if timestamp_raw is None:
                continue
            timestamp = _to_true_utc(timestamp_raw, clock)
            # The window filter runs on the corrected stamp, so --start/--end keep
            # meaning true UTC exactly as their help text says.
            if timestamp < start or timestamp >= end:
                continue
            offsets_seen.add(
                int(round((datetime.fromtimestamp(timestamp_raw, tz=timezone.utc) - timestamp).total_seconds()))
            )
            if previous_ts is not None:
                gap = timestamp - previous_ts
                if gap > expected_delta:
                    gap_count += 1
                    max_gap_seconds = max(max_gap_seconds, gap.total_seconds())
            previous_ts = timestamp
            rendered_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            volume = _rate_field(rec, "tick_volume", default=0)
            writer.writerow(
                [
                    rendered_time,
                    _rate_field(rec, "open"),
                    _rate_field(rec, "high"),
                    _rate_field(rec, "low"),
                    _rate_field(rec, "close"),
                    volume,
                ]
            )
            first_time = first_time or rendered_time
            last_time = rendered_time
            count += 1
    return {
        "rows": count,
        "first": first_time,
        "last": last_time,
        "gap_count": gap_count,
        "max_gap_seconds": max_gap_seconds if gap_count else 0.0,
        "expected_delta_seconds": expected_delta.total_seconds(),
        # Which offsets this particular file actually spans. A file crossing a DST
        # seam legitimately carries two; more than two means the rule is wrong for
        # this server and the file should not be trusted.
        "broker_offset_seconds_applied": sorted(offsets_seen),
        # Stamped here, where the clock is actually applied, so the declaration
        # travels with the data even for callers that never build a manifest.
        "time_column_basis": "broker_server_local" if _is_uncorrected(clock) else "true_utc",
        **clock.provenance(),
    }


def _rate_timestamp(rec: Any) -> int | None:
    try:
        return int(rec["time"])
    except (KeyError, TypeError, ValueError, IndexError):
        return None


def _rate_field(rec: Any, field: str, default: Any = None) -> Any:
    try:
        return rec[field]
    except (KeyError, TypeError, ValueError, IndexError):
        return default


def _parse_utc(value: str) -> datetime:
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="UTC start timestamp/date, inclusive.")
    parser.add_argument("--end", required=True, help="UTC end timestamp/date, exclusive.")
    parser.add_argument(
        "--output-root",
        default="data/mt5_research_exports",
        help="Root for versioned research exports.",
    )
    parser.add_argument("--label", default=None, help="Output folder label.")
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
    parser.add_argument(
        "--chunk-days",
        type=float,
        help=(
            "Split each MT5 copy_rates_range call into N-day windows. "
            "Use this for large M1/M5/M15 ranges that can fail as one request."
        ),
    )
    parser.add_argument(
        "--history-refresh-retries",
        type=int,
        default=2,
        help=(
            "Repeat the final historical window to let MT5 finish hydrating "
            "recent bars; the newest and most complete response wins."
        ),
    )
    parser.add_argument(
        "--history-refresh-delay-seconds",
        type=float,
        default=0.5,
        help="Delay between bounded final-window history refresh attempts.",
    )
    parser.add_argument(
        "--yes-live-readonly",
        action="store_true",
        help="Allow read-only export from a live account. No orders are sent.",
    )
    clock_group = parser.add_argument_group(
        "broker clock (F7)",
        "MT5 reports bar epochs in the broker server's wall clock. Exactly one of "
        "these decides the exported time base; all three are recorded in the manifest.",
    )
    clock_group.add_argument(
        "--broker-clock",
        default="auto",
        help=(
            "MT5 server name whose measured clock rule to apply (default: auto, read "
            "from account_info().server). Unknown servers fail closed --- measure one "
            "with scripts/measure_broker_clock_offset.py and register it in "
            "src/utils/broker_clock.py."
        ),
    )
    clock_group.add_argument(
        "--broker-clock-offset-hours",
        type=float,
        default=None,
        help="Operator override: constant offset in hours, no DST. Overrides --broker-clock.",
    )
    clock_group.add_argument(
        "--no-broker-clock-correction",
        action="store_true",
        help=(
            "Emit broker-local timestamps, the pre-2026-07-26 behaviour. Declared as "
            "uncorrected_broker_local in the manifest and every sidecar, never silent."
        ),
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
    chunk = timedelta(days=args.chunk_days) if args.chunk_days is not None else None
    if chunk is not None and chunk <= timedelta(0):
        raise ValueError("--chunk-days must be positive")
    if args.history_refresh_retries < 0:
        raise ValueError("--history-refresh-retries must be non-negative")
    if args.history_refresh_delay_seconds < 0:
        raise ValueError("--history-refresh-delay-seconds must be non-negative")
    specs = parse_symbol_specs(args.symbol or default_symbol_specs_for_args(args))
    timeframe_names = parse_timeframe_names(args.timeframes)
    label = safe_slug(args.label or f"mt5_ohlcv_{start:%Y%m%d}_{end:%Y%m%d}")
    output_dir = Path(args.output_root) / label

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
        clock = resolve_export_clock(args, account)
        export_result = export_research_ohlcv(
            mt5_module=mt5,
            specs=specs,
            timeframe_names=timeframe_names,
            start=start,
            end=end,
            output_dir=output_dir,
            clock=clock,
            chunk=chunk,
            history_refresh_retries=args.history_refresh_retries,
            history_refresh_delay_seconds=args.history_refresh_delay_seconds,
        )
        manifest_path = output_dir / "manifest.json"
        provenance = source_provenance_from_args(args)
        export_result = enrich_export_result_for_manifest(
            export_result=export_result,
            account=account,
            provenance=provenance,
            start=start,
            end=end,
            manifest_path=manifest_path,
            clock=clock,
        )
        manifest = {
            "schema_version": "mt5_research_ohlcv_export_v1",
            **clock.provenance(),
            # offset_seconds_at_utc, not the broker-time form: start/end are true-UTC
            # instants and a UTC instant has exactly one offset, whereas the broker
            # wall clock is ambiguous in the repeated autumn hour.
            "broker_clock_offset_seconds_at_start": (
                0 if _is_uncorrected(clock) else offset_seconds_at_utc(start, clock)
            ),
            "broker_clock_offset_seconds_at_end": (
                0 if _is_uncorrected(clock) else offset_seconds_at_utc(end, clock)
            ),
            "created_at_utc": utc_now().isoformat(),
            "read_only": True,
            "label": label,
            "start_utc": start.isoformat(),
            "end_utc": end.isoformat(),
            "chunk_days": args.chunk_days,
            "output_dir": str(output_dir),
            "mt5_client_kind": mt5_client_kind,
            "account": account_identity_payload(account),
            "symbols": [spec.__dict__ for spec in specs],
            "timeframes": timeframe_names,
            "source_provenance": provenance,
            "manifest_path": str(manifest_path),
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
