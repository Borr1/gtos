"""Bounded all-symbol persisted-byte equivalence for replay source CSV inputs.

The module extends the accepted immutable source-byte tracer without widening
its admission boundary.  It selects one day from source/session metadata,
seals every required CSV source behind a cross-symbol barrier, compares the
legacy loader with cache-issued leases, and emits source-stage measurements.
No policy reducer or replay arm is executed here.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import hashlib
import json
import math
import os
import resource
import re
import shutil
import stat
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence, TypeVar

from src.research_infra.replay_acceleration_source_batch import (
    FACTORIAL_ARMS,
    SOURCE_BYTES_STAGE,
    CacheAdmissionRegistry,
    ConfigReadGuard,
    ImmutableSourceBatchCache,
    SourceBatchBinding,
    SourceBatchRejected,
    implementation_root as accepted_cache_implementation_root,
)
from src.research_infra.v4_timewarp_simulated_live_research_loop import (
    load_csv_rows,
    parse_row_time,
)


SELECTION_SCHEMA = "gtos.replay_acceleration.slice_selection.v1"
BUNDLE_SCHEMA = "gtos.replay_acceleration.persisted_source_bundle.v1"
RUN_SCHEMA = "gtos.replay_acceleration.source_stage_run.v1"
ATTESTATION_SCHEMA = "gtos.replay_acceleration.bundle_source_attestation.v1"
CASE_SCHEMA = "gtos.replay_acceleration.failure_case.v1"
INJECTION_SCHEMA = "gtos.replay_acceleration.failure_injections.v1"
VERIFIER_ENVELOPE_SCHEMA = "gtos.replay_acceleration.verifier_envelope.v1"
RESULT_SCHEMA = "gtos.replay_acceleration.bounded_slice_result.v1"
SELECTION_RULE = (
    "lexicographically_earliest_january_day_with_all_expected_symbols_"
    "m1_m15_session_complete_non_diagnostic_path_enabled_and_current_files"
)
SOURCE_STAGE_LABEL = "bounded_all_symbol_source_stage_not_whole_replay"
ACCEPTED_BASE_COMMIT = "0d4faafc35f5d93ee8a54bc16d4e37b1c137394c"
DEFAULT_SOURCE_PLAN_DIGEST = (
    "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
)
EXPECTED_SYMBOLS = (
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
)
PHYSICAL_TIMEFRAMES = ("D1", "H4", "M15", "M1")
LOGICAL_TIMEFRAMES = ("D1", "H4", "H1", "M15", "M1")
FACTORIAL_ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
CSV_HEADER = ("time", "open", "high", "low", "close", "volume")
MAX_SCRATCH_BYTES = 1024**3
WARNING_FREE_BYTES = 34 * 1024**3
# Capacity is admitted from the measured workload projection and the bounded
# scratch quota.  A machine-wide static reserve made small source-only rebuilds
# fail even when their complete projected growth fit comfortably.
HARD_FLOOR_FREE_BYTES = 0
VERIFIER_PATH = Path(__file__).with_name("replay_acceleration_slice_verifier.py")

_T = TypeVar("_T")


class SliceRejected(RuntimeError):
    """Stable fail-closed slice rejection."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def canonical_json_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError):
        raise SliceRejected("noncanonical_value") from None
    return text.encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _valid_root(value: Any) -> bool:
    return type(value) is str and len(value) == 64 and all(
        character in "009abcdef" for character in value
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _atomic_write(path: Path, payload: bytes, *, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    descriptor = os.open(
        temporary,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        view = memoryview(payload)
        offset = 0
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise SliceRejected("atomic_write_failed")
            offset += written
        os.fsync(descriptor)
        os.fchmod(descriptor, mode)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    parent = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(parent)
    finally:
        os.close(parent)


def _write_canonical_json(
    path: Path, value: Mapping[str, Any], *, mode: int = 0o644
) -> None:
    _atomic_write(path, canonical_json_bytes(dict(value)) + b"\n", mode=mode)


def _load_canonical_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        raw = Path(path).read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise SliceRejected(code) from None
    if type(value) is not dict or raw != canonical_json_bytes(value) + b"\n":
        raise SliceRejected(code)
    return value


def _with_self_root(value: Mapping[str, Any], field: str) -> dict[str, Any]:
    core = {key: item for key, item in dict(value).items() if key != field}
    return {**core, field: sha256_bytes(canonical_json_bytes(core))}


def _verify_self_root(value: Mapping[str, Any], field: str, *, code: str) -> str:
    root = value.get(field)
    if not _valid_root(root):
        raise SliceRejected(code)
    core = {key: item for key, item in value.items() if key != field}
    if sha256_bytes(canonical_json_bytes(core)) != root:
        raise SliceRejected(code)
    return str(root)


def _stat_identity(path: Path) -> dict[str, int]:
    info = Path(path).stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise SliceRejected("source_file_not_regular")
    return {
        "device": int(info.st_dev),
        "inode": int(info.st_ino),
        "byte_count": int(info.st_size),
        "mtime_ns": int(info.st_mtime_ns),
        "ctime_ns": int(info.st_ctime_ns),
    }


_SOURCE_STAT_STABLE_FIELDS = (
    "device",
    "inode",
    "byte_count",
    "mtime_ns",
)


def _source_stat_stable_projection(
    identity: Mapping[str, Any],
) -> dict[str, int]:
    """Project content-relevant file identity, excluding volatile APFS ctime."""

    return {
        field: int(identity[field]) for field in _SOURCE_STAT_STABLE_FIELDS
    }


def _path_root(path: Path) -> str:
    return sha256_bytes(
        canonical_json_bytes({"source_path": os.path.abspath(os.fspath(path))})
    )


def _selection_source_signature(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("symbol"),
        row.get("timeframe"),
        row.get("source_path"),
        row.get("source_family"),
        row.get("source_role"),
        row.get("status"),
        row.get("requested_range_covered"),
        row.get("rows"),
        row.get("sha256"),
    )


def _selection_day_signature(row: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("symbol"),
        row.get("trading_day"),
        row.get("source_path"),
        row.get("source_family"),
        row.get("status"),
        row.get("source_session_status"),
        row.get("diagnostic_fallback_only"),
        row.get("path_replay_allowed"),
        row.get("terminal_lifecycle_close_allowed"),
        row.get("source_overlap_consistent"),
        tuple(row.get("source_gaps") or ()),
        row.get("rows"),
        row.get("m15_day_rows"),
        row.get("sha256"),
        row.get("source_day_authority_hash_sha256"),
    )


def _selection_command(command_argv: Sequence[str] | None) -> list[str]:
    return list(command_argv or ("python_api:create_selection_receipt",))


def _executed_command_receipt(argv: Sequence[str]) -> list[str]:
    original = getattr(sys, "orig_argv", None)
    if type(original) is list and original:
        return [str(item) for item in original]
    return [sys.executable, str(Path(__file__).resolve()), *map(str, argv)]


def create_selection_receipt(
    *,
    source_ledger: Path,
    output_path: Path,
    expected_symbols: Sequence[str] = EXPECTED_SYMBOLS,
    expected_source_plan_digest_sha256: str = DEFAULT_SOURCE_PLAN_DIGEST,
    month: str = "2026-01",
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Select and seal a day using source/session structure only."""

    ledger_path = Path(source_ledger)
    if not _valid_root(expected_source_plan_digest_sha256):
        raise SliceRejected("source_plan_digest_invalid")
    symbols = tuple(str(symbol) for symbol in expected_symbols)
    if not symbols or len(set(symbols)) != len(symbols):
        raise SliceRejected("expected_symbol_set_invalid")
    ledger_stat = _stat_identity(ledger_path)
    ledger_root = file_sha256(ledger_path)
    if _stat_identity(ledger_path) != ledger_stat:
        raise SliceRejected("source_ledger_changed_during_selection")
    static_rows: dict[tuple[str, str], tuple[Any, ...]] = {}
    static_values: dict[tuple[str, str], dict[str, Any]] = {}
    day_rows: dict[tuple[str, str], tuple[Any, ...]] = {}
    day_values: dict[tuple[str, str], dict[str, Any]] = {}
    tick_rows: dict[tuple[str, str], dict[str, Any]] = {}
    consumed_counts: dict[str, int] = defaultdict(int)
    try:
        handle = ledger_path.open("r", encoding="utf-8")
    except OSError:
        raise SliceRejected("source_ledger_unreadable") from None
    with handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                raise SliceRejected("source_ledger_unreadable") from None
            if type(row) is not dict:
                raise SliceRejected("source_ledger_row_invalid")
            row_type = row.get("row_type")
            if row_type == "source_selection":
                symbol = str(row.get("symbol") or "")
                timeframe = str(row.get("timeframe") or "")
                if symbol not in symbols or timeframe not in {"D1", "H4", "H1", "M15"}:
                    continue
                key = (symbol, timeframe)
                signature = _selection_source_signature(row)
                if key in static_rows and static_rows[key] != signature:
                    raise SliceRejected("source_metadata_conflict")
                static_rows[key] = signature
                static_values[key] = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "source_path": row.get("source_path"),
                    "source_family": row.get("source_family"),
                    "source_role": row.get("source_role"),
                    "status": row.get("status"),
                    "requested_range_covered": row.get("requested_range_covered"),
                    "ledger_source_root": row.get("sha256"),
                }
                consumed_counts[row_type] += 1
            elif row_type == "m1_symbol_day_source":
                symbol = str(row.get("symbol") or "")
                day = str(row.get("trading_day") or "")
                if symbol not in symbols or not day.startswith(f"{month}-"):
                    continue
                key = (day, symbol)
                signature = _selection_day_signature(row)
                if key in day_rows and day_rows[key] != signature:
                    raise SliceRejected("source_metadata_conflict")
                day_rows[key] = signature
                day_values[key] = {
                    "symbol": symbol,
                    "trading_day": day,
                    "source_path": row.get("source_path"),
                    "source_family": row.get("source_family"),
                    "status": row.get("status"),
                    "source_session_status": row.get("source_session_status"),
                    "diagnostic_fallback_only": row.get("diagnostic_fallback_only"),
                    "path_replay_allowed": row.get("path_replay_allowed"),
                    "terminal_lifecycle_close_allowed": row.get(
                        "terminal_lifecycle_close_allowed"
                    ),
                    "source_overlap_consistent": row.get("source_overlap_consistent"),
                    "source_gaps": list(row.get("source_gaps") or ()),
                    "record_count": row.get("rows"),
                    "m15_record_count": row.get("m15_day_rows"),
                    "ledger_source_root": row.get("sha256"),
                    "source_day_authority_root": row.get(
                        "source_day_authority_hash_sha256"
                    ),
                }
                consumed_counts[row_type] += 1
            elif row_type in {"tick_symbol_source", "tick_symbol_source_gap"}:
                symbol = str(row.get("symbol") or "")
                if symbol not in symbols:
                    continue
                key = (symbol, str(row.get("source_path") or row_type))
                tick_rows.setdefault(
                    key,
                    {
                        "symbol": symbol,
                        "status": row.get("status"),
                        "source_path": row.get("source_path"),
                        "declared_source_root": row.get("sha256")
                        or row.get("source_sha256"),
                        "declared_record_count": row.get("row_count")
                        or row.get("rows"),
                    },
                )
                consumed_counts[row_type] += 1

    expected_static = {
        (symbol, timeframe)
        for symbol in symbols
        for timeframe in ("D1", "H4", "H1", "M15")
    }
    if set(static_values) != expected_static:
        raise SliceRejected("static_source_coverage_incomplete")
    for row in static_values.values():
        if (
            type(row.get("source_path")) is not str
            or not str(row.get("status") or "").startswith("selected_source")
            or (
                row.get("timeframe") != "H1"
                and row.get("requested_range_covered") is not True
            )
        ):
            raise SliceRejected("static_source_not_admissible")
    for symbol in symbols:
        h1 = static_values[(symbol, "H1")]
        m15 = static_values[(symbol, "M15")]
        if (
            h1.get("source_path") != m15.get("source_path")
            or h1.get("source_role") != "source_bound_derived_h1_from_m15"
            or h1.get("status") != "selected_source_bound_derived_h1_from_m15"
        ):
            raise SliceRejected("derived_h1_source_alias_mismatch")

    days = sorted({day for day, _symbol in day_values})
    eligible_summaries: list[dict[str, Any]] = []
    eligible_days: list[str] = []
    for day in days:
        rows = [day_values.get((day, symbol)) for symbol in symbols]
        complete = [
            row
            for row in rows
            if row is not None
            and row.get("diagnostic_fallback_only") is False
            and row.get("path_replay_allowed") is True
            and row.get("terminal_lifecycle_close_allowed") is True
            and row.get("source_overlap_consistent") is True
            and not row.get("source_gaps")
            and type(row.get("record_count")) is int
            and int(row["record_count"]) > 0
            and type(row.get("m15_record_count")) is int
            and int(row["m15_record_count"]) > 0
            and str(row.get("source_session_status") or "")
            != "ftmo_verified_no_session_day"
        ]
        eligible = len(complete) == len(symbols)
        if eligible:
            eligible_days.append(day)
        eligible_summaries.append(
            {
                "day": day,
                "symbol_metadata_count": sum(row is not None for row in rows),
                "complete_symbol_count": len(complete),
                "eligible": eligible,
            }
        )
    if not eligible_days:
        raise SliceRejected("no_source_complete_day")
    selected_day = eligible_days[0]

    physical: list[dict[str, Any]] = []
    logical: list[dict[str, Any]] = []
    for symbol in sorted(symbols):
        for timeframe in PHYSICAL_TIMEFRAMES:
            metadata = (
                day_values[(selected_day, symbol)]
                if timeframe == "M1"
                else static_values[(symbol, timeframe)]
            )
            source_path = Path(str(metadata.get("source_path") or ""))
            try:
                identity_before = _stat_identity(source_path)
                physical_root = file_sha256(source_path)
                identity = _stat_identity(source_path)
            except OSError:
                raise SliceRejected("selected_source_missing") from None
            if _source_stat_stable_projection(
                identity_before
            ) != _source_stat_stable_projection(identity):
                raise SliceRejected("selected_source_changed_during_hash")
            if timeframe == "M1" and metadata.get("ledger_source_root") not in {
                None,
                "",
                physical_root,
            }:
                raise SliceRejected("selected_source_hash_mismatch")
            logical_timeframes = (
                ["H1", "M15"] if timeframe == "M15" else [timeframe]
            )
            partition_id = f"{symbol}:{timeframe}"
            partition_identity = {
                "schema": "gtos.replay_acceleration.source_partition.v1",
                "symbol": symbol,
                "selected_day": selected_day,
                "physical_timeframe": timeframe,
                "logical_timeframes": logical_timeframes,
                "source_plan_digest_sha256": expected_source_plan_digest_sha256,
            }
            source_identity = {
                "schema": "gtos.replay_acceleration.source_identity.v1",
                "source_plan_digest_sha256": expected_source_plan_digest_sha256,
                "source_ledger_sha256": ledger_root,
                "selected_day": selected_day,
                "symbol": symbol,
                "physical_timeframe": timeframe,
                "source_file_sha256": physical_root,
                "source_stat": identity,
            }
            physical.append(
                {
                    "index": len(physical),
                    "partition_id": partition_id,
                    "symbol": symbol,
                    "physical_timeframe": timeframe,
                    "logical_timeframes": logical_timeframes,
                    "source_path": os.path.abspath(os.fspath(source_path)),
                    "source_path_root": _path_root(source_path),
                    "source_file_sha256": physical_root,
                    "byte_count": identity["byte_count"],
                    "source_stat": identity,
                    "ledger_source_root": metadata.get("ledger_source_root"),
                    "source_day_authority_root": metadata.get(
                        "source_day_authority_root"
                    ),
                    "partition_identity": partition_identity,
                    "source_identity": source_identity,
                }
            )
        for timeframe in LOGICAL_TIMEFRAMES:
            physical_timeframe = "M15" if timeframe == "H1" else timeframe
            logical.append(
                {
                    "index": len(logical),
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "physical_partition_id": f"{symbol}:{physical_timeframe}",
                    "transform": (
                        "derived_h1_from_m15"
                        if timeframe == "H1"
                        else "direct_csv_normalization"
                    ),
                }
            )

    tick_available: list[dict[str, Any]] = []
    tick_gaps = 0
    tick_total_bytes = 0
    for row in sorted(tick_rows.values(), key=lambda item: (str(item["symbol"]), str(item["source_path"]))):
        raw_path = row.get("source_path")
        if type(raw_path) is str and raw_path:
            path = Path(raw_path)
            try:
                info = _stat_identity(path)
            except OSError:
                raise SliceRejected("declared_tick_source_missing") from None
            tick_total_bytes += info["byte_count"]
            tick_available.append(
                {
                    "symbol": row["symbol"],
                    "source_path_root": _path_root(path),
                    "byte_count": info["byte_count"],
                    "declared_source_root": row.get("declared_source_root"),
                }
            )
        else:
            tick_gaps += 1

    receipt_core = {
        "schema": SELECTION_SCHEMA,
        "status": "PROSPECTIVE_SOURCE_SELECTION_SEALED",
        "accepted_base_commit": ACCEPTED_BASE_COMMIT,
        "selection_rule": SELECTION_RULE,
        "selected_day": selected_day,
        "month": month,
        "expected_source_plan_digest_sha256": expected_source_plan_digest_sha256,
        "source_ledger": {
            "path": os.path.abspath(os.fspath(ledger_path)),
            "sha256": ledger_root,
            "byte_count": ledger_stat["byte_count"],
            "consumed_row_counts": dict(sorted(consumed_counts.items())),
            "consumed_surface": "source_and_session_structure_only",
        },
        "selection_command": _selection_command(command_argv),
        "source_stat_identity_contract": {
            "content_identity_fields": list(_SOURCE_STAT_STABLE_FIELDS),
            "observational_noncausal_fields": ["ctime_ns"],
            "content_sha256_required": True,
            "race_detection": (
                "stable_content_identity_before_and_after_read_plus_exact_sha256"
            ),
        },
        "eligible_day_summaries": eligible_summaries,
        "scope": {
            "symbols": sorted(symbols),
            "symbol_count": len(symbols),
            "physical_timeframes": list(PHYSICAL_TIMEFRAMES),
            "logical_timeframes": list(LOGICAL_TIMEFRAMES),
            "physical_partition_count": len(physical),
            "logical_partition_count": len(logical),
            "cross_symbol_barrier_required": True,
        },
        "physical_partitions": physical,
        "logical_partitions": logical,
        "postdecision_tick_inventory": {
            "classification": "outside_accepted_csv_source_byte_cache_boundary",
            "available_partition_count": len(tick_available),
            "gap_symbol_count": tick_gaps,
            "declared_full_source_bytes": tick_total_bytes,
            "full_source_hash_verification_performed": False,
            "partitions": tick_available,
        },
        "policy_execution_entered": False,
        "source_only": True,
    }
    receipt = _with_self_root(receipt_core, "selection_root_sha256")
    output = Path(output_path)
    if output.exists():
        existing = _load_canonical_json(output, code="selection_receipt_invalid")
        if existing != receipt:
            raise SliceRejected("selection_receipt_already_differs")
    else:
        _write_canonical_json(output, receipt, mode=0o444)
    return receipt


def verify_selection_receipt(path: Path) -> dict[str, Any]:
    receipt = _load_canonical_json(Path(path), code="selection_receipt_invalid")
    if receipt.get("schema") != SELECTION_SCHEMA:
        raise SliceRejected("selection_receipt_invalid")
    _verify_self_root(
        receipt,
        "selection_root_sha256",
        code="selection_receipt_invalid",
    )
    return receipt


def _read_stable_source(path: Path) -> tuple[bytes, dict[str, int]]:
    absolute = Path(os.path.abspath(os.fspath(path)))
    descriptor: int | None = None
    try:
        descriptor = os.open(
            absolute,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise SliceRejected("source_file_not_regular")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        payload = b"".join(chunks)
        after = os.fstat(descriptor)
    except OSError:
        raise SliceRejected("source_read_failed") from None
    finally:
        if descriptor is not None:
            os.close(descriptor)
    before_identity = {
        "device": int(before.st_dev),
        "inode": int(before.st_ino),
        "byte_count": int(before.st_size),
        "mtime_ns": int(before.st_mtime_ns),
        "ctime_ns": int(before.st_ctime_ns),
    }
    after_identity = {
        "device": int(after.st_dev),
        "inode": int(after.st_ino),
        "byte_count": int(after.st_size),
        "mtime_ns": int(after.st_mtime_ns),
        "ctime_ns": int(after.st_ctime_ns),
    }
    if (
        _source_stat_stable_projection(before_identity)
        != _source_stat_stable_projection(after_identity)
        or len(payload) != after.st_size
    ):
        raise SliceRejected("source_changed_during_read")
    return payload, after_identity


def _rows_root(rows: Iterable[Mapping[str, Any]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"gtos.replay_acceleration.canonical_rows.v1\n")
    for row in rows:
        digest.update(canonical_json_bytes(dict(row)))
        digest.update(b"\n")
    return digest.hexdigest()


def _selected_day_rows(
    rows: Iterable[Mapping[str, Any]], selected_day: str
) -> tuple[dict[str, Any], ...]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        timestamp = parse_row_time(row)
        if timestamp is not None and timestamp.astimezone(timezone.utc).date().isoformat() == selected_day:
            selected.append(dict(row))
    return tuple(selected)


def _safe_float(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0
    return result if math.isfinite(result) else 0.0


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


def _aggregate_h1(
    rows: Iterable[Mapping[str, Any]], *, symbol: str
) -> tuple[dict[str, Any], ...]:
    # Exact copy of the bounded legacy harness's H1-from-M15 semantics.  The
    # independent verifier carries its own implementation.
    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        timestamp = parse_row_time(row)
        if timestamp is None:
            continue
        bucket = timestamp.astimezone(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )
        buckets[bucket].append(row)
    output: list[dict[str, Any]] = []
    for bucket, items in sorted(buckets.items()):
        ordered = sorted(items, key=lambda item: parse_row_time(item) or bucket)
        output.append(
            {
                "time": _iso(bucket),
                "time_utc": _iso(bucket),
                "symbol": symbol,
                "open": _safe_float(ordered[0].get("open")),
                "high": max(_safe_float(row.get("high")) for row in ordered),
                "low": min(_safe_float(row.get("low")) for row in ordered),
                "close": _safe_float(ordered[-1].get("close")),
                "volume": sum(_safe_float(row.get("volume")) for row in ordered),
                "source_records": len(ordered),
            }
        )
    return tuple(output)


class _DarwinRusageV2(ctypes.Structure):
    _fields_ = [("uuid", ctypes.c_uint8 * 16)] + [
        (name, ctypes.c_uint64)
        for name in (
            "user_time",
            "system_time",
            "package_idle_wakeups",
            "interrupt_wakeups",
            "pageins",
            "wired_size",
            "resident_size",
            "physical_footprint",
            "process_start",
            "process_exit",
            "child_user_time",
            "child_system_time",
            "child_package_idle_wakeups",
            "child_interrupt_wakeups",
            "child_pageins",
            "child_elapsed",
            "diskio_bytes_read",
            "diskio_bytes_written",
        )
    ]


def _darwin_io_snapshot() -> tuple[int, int] | None:
    if sys.platform != "darwin":
        return None
    try:
        library = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
        library.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
        library.proc_pid_rusage.restype = ctypes.c_int
        value = _DarwinRusageV2()
        if library.proc_pid_rusage(os.getpid(), 2, ctypes.byref(value)) != 0:
            return None
        return int(value.diskio_bytes_read), int(value.diskio_bytes_written)
    except (AttributeError, OSError):
        return None


def _resource_snapshot() -> dict[str, Any]:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    io_value = _darwin_io_snapshot()
    return {
        "cpu_user_seconds": own.ru_utime + children.ru_utime,
        "cpu_system_seconds": own.ru_stime + children.ru_stime,
        "minor_page_faults": int(own.ru_minflt + children.ru_minflt),
        "major_page_faults": int(own.ru_majflt + children.ru_majflt),
        "block_input_operations": int(own.ru_inblock + children.ru_inblock),
        "block_output_operations": int(own.ru_oublock + children.ru_oublock),
        "peak_rss_bytes": (
            max(int(own.ru_maxrss), int(children.ru_maxrss))
            if sys.platform == "darwin"
            else max(int(own.ru_maxrss), int(children.ru_maxrss)) * 1024
        ),
        "bytes_read": io_value[0] if io_value is not None else None,
        "bytes_written": io_value[1] if io_value is not None else None,
    }


def _resource_delta(
    before: Mapping[str, Any], after: Mapping[str, Any], *, wall_seconds: float
) -> dict[str, Any]:
    delta: dict[str, Any] = {
        "wall_seconds": round(float(wall_seconds), 9),
        "peak_rss_bytes": int(after["peak_rss_bytes"]),
    }
    for field in ("cpu_user_seconds", "cpu_system_seconds"):
        delta[field] = round(float(after[field]) - float(before[field]), 9)
    for field in (
        "minor_page_faults",
        "major_page_faults",
        "block_input_operations",
        "block_output_operations",
    ):
        delta[field] = int(after[field]) - int(before[field])
    for field in ("bytes_read", "bytes_written"):
        if before[field] is None or after[field] is None:
            delta[field] = None
        else:
            delta[field] = max(0, int(after[field]) - int(before[field]))
    delta["byte_counters_available"] = (
        delta["bytes_read"] is not None and delta["bytes_written"] is not None
    )
    return delta


def _tree_usage(root: Path) -> dict[str, int]:
    logical = 0
    allocated = 0
    files = 0
    if not root.exists():
        return {"logical_bytes": 0, "allocated_bytes": 0, "file_count": 0}
    for base, _directories, names in os.walk(root):
        for name in names:
            path = Path(base) / name
            try:
                info = path.stat(follow_symlinks=False)
            except OSError:
                continue
            if stat.S_ISREG(info.st_mode):
                logical += int(info.st_size)
                allocated += int(getattr(info, "st_blocks", 0) * 512)
                files += 1
    return {"logical_bytes": logical, "allocated_bytes": allocated, "file_count": files}


def _swap_used_bytes() -> int | None:
    if sys.platform != "darwin":
        return None
    try:
        completed = subprocess.run(
            ["sysctl", "-n", "vm.swapusage"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"\bused\s*=\s*([0-9.]+)([KMG])\b", completed.stdout)
    if match is None:
        return None
    scale = {"K": 1024, "M": 1024**2, "G": 1024**3}[match.group(2)]
    return int(float(match.group(1)) * scale)


class _StageMeasurements:
    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self.stages: dict[str, dict[str, Any]] = {}
        self.peak_scratch = _tree_usage(self.workspace)

    @contextlib.contextmanager
    def stage(self, name: str) -> Iterator[None]:
        before_resource = _resource_snapshot()
        before_wall = time.perf_counter()
        try:
            yield
        finally:
            after_wall = time.perf_counter()
            after_resource = _resource_snapshot()
            scratch = _tree_usage(self.workspace)
            if scratch["logical_bytes"] > self.peak_scratch["logical_bytes"]:
                self.peak_scratch["logical_bytes"] = scratch["logical_bytes"]
            if scratch["allocated_bytes"] > self.peak_scratch["allocated_bytes"]:
                self.peak_scratch["allocated_bytes"] = scratch["allocated_bytes"]
            self.peak_scratch["file_count"] = max(
                self.peak_scratch["file_count"], scratch["file_count"]
            )
            row = self.stages.setdefault(
                name,
                {
                    "wall_seconds": 0.0,
                    "cpu_user_seconds": 0.0,
                    "cpu_system_seconds": 0.0,
                    "minor_page_faults": 0,
                    "major_page_faults": 0,
                    "block_input_operations": 0,
                    "block_output_operations": 0,
                    "bytes_read": 0,
                    "bytes_written": 0,
                    "byte_counters_available": True,
                    "peak_rss_bytes": 0,
                    "observations": 0,
                },
            )
            row["wall_seconds"] += after_wall - before_wall
            for field in ("cpu_user_seconds", "cpu_system_seconds"):
                row[field] += after_resource[field] - before_resource[field]
            for field in (
                "minor_page_faults",
                "major_page_faults",
                "block_input_operations",
                "block_output_operations",
            ):
                row[field] += after_resource[field] - before_resource[field]
            row["peak_rss_bytes"] = max(
                row["peak_rss_bytes"], after_resource["peak_rss_bytes"]
            )
            for field in ("bytes_read", "bytes_written"):
                if before_resource[field] is None or after_resource[field] is None:
                    row["byte_counters_available"] = False
                    row[field] = None
                elif row[field] is not None:
                    row[field] += max(0, after_resource[field] - before_resource[field])
            row["observations"] += 1

    def result(self) -> dict[str, Any]:
        stages: dict[str, dict[str, Any]] = {}
        for name, row in sorted(self.stages.items()):
            normalized = dict(row)
            for field in ("wall_seconds", "cpu_user_seconds", "cpu_system_seconds"):
                normalized[field] = round(float(normalized[field]), 9)
            stages[name] = normalized
        return {
            "label": SOURCE_STAGE_LABEL,
            "stages": stages,
            "compression": {"used": False, "wall_seconds": 0.0},
            "peak_scratch": dict(self.peak_scratch),
        }


def _enforce_capacity(
    *, workspace: Path, baseline_free: int, baseline_allocated: int
) -> dict[str, int]:
    usage = _tree_usage(workspace)
    growth = max(0, usage["allocated_bytes"] - baseline_allocated)
    free = shutil.disk_usage(workspace).free
    if growth > MAX_SCRATCH_BYTES:
        raise SliceRejected("scratch_quota_exceeded")
    if free < HARD_FLOOR_FREE_BYTES:
        raise SliceRejected("disk_hard_floor_reached")
    # Machine-wide free-space motion is not attributable to this workspace.
    # The bounded workspace allocation above is the causal scratch guard; a
    # concurrent process writing elsewhere must not reject an otherwise valid
    # source materialization.
    return {"free_bytes": int(free), "allocated_growth_bytes": int(growth)}


def _projected_capacity_sufficient(
    *, free_bytes: int, projected_growth_bytes: int
) -> bool:
    return (
        type(free_bytes) is int
        and type(projected_growth_bytes) is int
        and projected_growth_bytes >= 0
        and free_bytes >= projected_growth_bytes
    )


def _slice_code_identity() -> dict[str, Any]:
    writer_root = file_sha256(Path(__file__))
    verifier_root = file_sha256(VERIFIER_PATH)
    accepted_root = accepted_cache_implementation_root()
    core = {
        "writer_file_sha256": writer_root,
        "independent_verifier_file_sha256": verifier_root,
        "accepted_cache_implementation_root": accepted_root,
        "python_implementation": sys.implementation.name,
        "python_version": list(sys.version_info[:3]),
    }
    return {**core, "slice_code_identity_root": sha256_bytes(canonical_json_bytes(core))}


def _persist_legacy_copy(path: Path, payload: bytes, *, cold: bool) -> None:
    if path.exists():
        if cold or path.read_bytes() != payload:
            raise SliceRejected("legacy_persisted_bytes_mismatch")
        return
    if not cold:
        raise SliceRejected("warm_legacy_bytes_missing")
    _atomic_write(path, payload, mode=0o444)


def _empty_projection():
    return ConfigReadGuard(
        {}, known_keys=frozenset(), projection_keys=frozenset()
    ).seal_projection()


def _cache() -> CacheAdmissionRegistry:
    registry = CacheAdmissionRegistry()
    registry.admit(
        stage=SOURCE_BYTES_STAGE,
        implementation_identity_root=accepted_cache_implementation_root(),
        config_projection_keys=(),
    )
    return registry


def _attestation_expected(
    bundle: Mapping[str, Any], *, source_only_arm_id: str
) -> dict[str, Any]:
    roots = [
        [entry["partition_id"], entry["batch_root"], entry["payload_root"]]
        for entry in bundle["physical_partitions"]
    ]
    core = {
        "schema": ATTESTATION_SCHEMA,
        "source_only_arm_id": source_only_arm_id,
        "bundle_root_sha256": bundle["bundle_root_sha256"],
        "partition_roots": roots,
        "physical_partition_count": len(roots),
        "policy_execution_entered": False,
    }
    return {**core, "attestation_root_sha256": sha256_bytes(canonical_json_bytes(core))}


def _attest_bundle(bundle_dir: Path, source_only_arm_id: str) -> dict[str, Any]:
    if source_only_arm_id not in FACTORIAL_ARMS:
        raise SliceRejected("source_attestation_id_invalid")
    bundle = _load_canonical_json(bundle_dir / "bundle.json", code="bundle_invalid")
    root = _verify_self_root(bundle, "bundle_root_sha256", code="bundle_invalid")
    try:
        marker = (bundle_dir / "SEALED").read_bytes()
    except OSError:
        raise SliceRejected("bundle_unsealed") from None
    if marker != root.encode("ascii") + b"\n":
        raise SliceRejected("bundle_unsealed")
    cache = ImmutableSourceBatchCache(bundle_dir / "cache", registry=_cache())
    for entry in bundle.get("physical_partitions") or ():
        binding = SourceBatchBinding.from_dict(entry["binding"])
        manifest = cache._verify_batch(
            entry["batch_root"], expected_binding=binding
        )
        if (
            manifest.get("payload_root") != entry.get("payload_root")
            or manifest.get("record_count") != entry.get("record_count")
        ):
            raise SliceRejected("source_attestation_partition_mismatch")
    return _attestation_expected(bundle, source_only_arm_id=source_only_arm_id)


def _run_attestations(bundle_dir: Path) -> dict[str, Any]:
    roots: dict[str, str] = {}
    commands: list[list[str]] = []
    for source_only_arm_id in FACTORIAL_ARM_ORDER:
        command = [
            sys.executable,
            "-m",
            "src.research_infra.replay_acceleration_slice",
            "_attest",
            str(bundle_dir.resolve()),
            source_only_arm_id,
        ]
        commands.append(command)
        completed = subprocess.run(
            command,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=120,
        )
        if completed.returncode != 0:
            raise SliceRejected("source_attestation_process_failed")
        try:
            receipt = json.loads(completed.stdout)
        except json.JSONDecodeError:
            raise SliceRejected("source_attestation_process_failed") from None
        expected = _attestation_expected(
            _load_canonical_json(bundle_dir / "bundle.json", code="bundle_invalid"),
            source_only_arm_id=source_only_arm_id,
        )
        if receipt != expected:
            raise SliceRejected("source_attestation_process_mismatch")
        roots[source_only_arm_id] = receipt["attestation_root_sha256"]
    return {
        "count": len(roots),
        "roots": dict(sorted(roots.items())),
        "fresh_processes": True,
        "policy_execution_entered": False,
        "commands": commands,
    }


def materialize_slice(
    *,
    selection_path: Path,
    workspace: Path,
    run_label: str,
    expected_mode: str,
    run_attestations: bool = True,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    run_wall_started = time.perf_counter()
    run_resource_started = _resource_snapshot()
    selection = verify_selection_receipt(Path(selection_path))
    if expected_mode not in {"cold", "warm"}:
        raise SliceRejected("materialization_mode_invalid")
    root = Path(workspace)
    root.mkdir(parents=True, exist_ok=True)
    bundle_dir = root / "bundle"
    sealed_exists = (bundle_dir / "SEALED").exists()
    if expected_mode == "cold" and sealed_exists:
        raise SliceRejected("cold_workspace_not_empty")
    if expected_mode == "warm" and not sealed_exists:
        raise SliceRejected("warm_bundle_missing")
    baseline_free = shutil.disk_usage(root).free
    swap_before = _swap_used_bytes()
    baseline_usage = _tree_usage(root)
    source_bytes = sum(
        int(row.get("byte_count") or 0)
        for row in selection.get("physical_partitions") or ()
    )
    projected_growth = source_bytes * 2 + 64 * 1024 * 1024
    if projected_growth > MAX_SCRATCH_BYTES:
        raise SliceRejected("projected_scratch_quota_exceeded")
    if not _projected_capacity_sufficient(
        free_bytes=int(baseline_free),
        projected_growth_bytes=int(projected_growth),
    ):
        raise SliceRejected("projected_disk_capacity_insufficient")
    measurements = _StageMeasurements(root)
    code_identity = _slice_code_identity()
    cache = ImmutableSourceBatchCache(bundle_dir / "cache", registry=_cache())
    selected_day = str(selection["selected_day"])
    physical_output: list[dict[str, Any]] = []
    logical_summaries: dict[tuple[str, str], dict[str, Any]] = {}
    hits = 0
    misses = 0

    for partition in selection["physical_partitions"]:
        source_path = Path(partition["source_path"])
        with measurements.stage("legacy_direct_read"):
            direct_bytes, current_stat = _read_stable_source(source_path)
        if _source_stat_stable_projection(
            current_stat
        ) != _source_stat_stable_projection(partition["source_stat"]):
            raise SliceRejected("source_stat_identity_stale")
        with measurements.stage("physical_hashing"):
            direct_root = sha256_bytes(direct_bytes)
        if direct_root != partition["source_file_sha256"]:
            raise SliceRejected("source_file_identity_stale")
        legacy_name = (
            f"{int(partition['index']):03d}_"
            f"{partition['symbol']}_{partition['physical_timeframe']}.csv"
        )
        legacy_relative = f"legacy/{legacy_name}"
        with measurements.stage("legacy_persist"):
            _persist_legacy_copy(
                bundle_dir / legacy_relative,
                direct_bytes,
                cold=expected_mode == "cold",
            )

        binding = SourceBatchBinding.create(
            stage=SOURCE_BYTES_STAGE,
            source_identity=partition["source_identity"],
            source_path=source_path,
            partition_identity=partition["partition_identity"],
            config_projection=_empty_projection(),
        )
        with measurements.stage("content_address_seal"):
            sealed = cache.seal_source_file(source_path, binding=binding)
        if sealed.payload_root != direct_root or sealed.byte_count != len(direct_bytes):
            raise SliceRejected("legacy_content_persisted_bytes_mismatch")
        hits += int(sealed.cache_hit)
        misses += int(not sealed.cache_hit)
        with measurements.stage("legacy_parse_normalize"):
            legacy_rows = load_csv_rows(source_path, symbol=partition["symbol"])
        with measurements.stage("content_parse_normalize"):
            lease = cache.acquire_lease(
                sealed.batch_root, expected_binding=binding
            )
            content_rows = load_csv_rows(
                source_path,
                symbol=partition["symbol"],
                source_batch_lease=lease,
                source_partition=partition["partition_identity"],
            )
        if legacy_rows != content_rows:
            raise SliceRejected("legacy_content_normalization_mismatch")
        if len(legacy_rows) != sealed.record_count:
            raise SliceRejected("source_record_count_mismatch")
        with measurements.stage("canonical_rooting"):
            normalized_root = _rows_root(legacy_rows)
            selected_rows = _selected_day_rows(legacy_rows, selected_day)
            selected_root = _rows_root(selected_rows)
            direct_summary = {
                "normalized_root_sha256": normalized_root,
                "normalized_record_count": len(legacy_rows),
                "selected_day_root_sha256": selected_root,
                "selected_day_record_count": len(selected_rows),
            }
        logical_summaries[
            (partition["symbol"], partition["physical_timeframe"])
        ] = direct_summary
        if partition["physical_timeframe"] == "M15":
            h1_rows = _aggregate_h1(
                legacy_rows, symbol=partition["symbol"]
            )
            h1_selected = _selected_day_rows(h1_rows, selected_day)
            logical_summaries[(partition["symbol"], "H1")] = {
                "normalized_root_sha256": _rows_root(h1_rows),
                "normalized_record_count": len(h1_rows),
                "selected_day_root_sha256": _rows_root(h1_selected),
                "selected_day_record_count": len(h1_selected),
            }
        cache_manifest_relative = f"cache/{sealed.batch_root}/manifest.json"
        cache_payload_relative = f"cache/{sealed.batch_root}/payload.bin"
        physical_output.append(
            {
                "index": partition["index"],
                "partition_id": partition["partition_id"],
                "symbol": partition["symbol"],
                "physical_timeframe": partition["physical_timeframe"],
                "logical_timeframes": partition["logical_timeframes"],
                "source_path_root": partition["source_path_root"],
                "binding": binding.as_dict(),
                "batch_root": sealed.batch_root,
                "payload_root": sealed.payload_root,
                "byte_count": sealed.byte_count,
                "record_count": sealed.record_count,
                "legacy_path": legacy_relative,
                "manifest_path": cache_manifest_relative,
                "payload_path": cache_payload_relative,
                "csv_header": list(CSV_HEADER),
                "normalized_root_sha256": normalized_root,
                "normalized_record_count": len(legacy_rows),
                "selected_day_root_sha256": selected_root,
                "selected_day_record_count": len(selected_rows),
            }
        )
        del direct_bytes, legacy_rows, content_rows, selected_rows, lease
        if partition["physical_timeframe"] == "M15":
            del h1_rows, h1_selected
        _enforce_capacity(
            workspace=root,
            baseline_free=baseline_free,
            baseline_allocated=baseline_usage["allocated_bytes"],
        )

    logical_output: list[dict[str, Any]] = []
    for planned in selection["logical_partitions"]:
        summary = logical_summaries.get((planned["symbol"], planned["timeframe"]))
        if summary is None:
            raise SliceRejected("logical_partition_not_materialized")
        logical_output.append({**planned, **summary})

    symbols = sorted(selection["scope"]["symbols"])
    barrier = {
        "sealed": True,
        "policy_execution_entered": False,
        "symbol_count": len(symbols),
        "symbols": symbols,
        "physical_partition_count": len(physical_output),
        "logical_partition_count": len(logical_output),
    }
    config_identity_root = sha256_bytes(
        canonical_json_bytes(
            {
                "selected_day": selected_day,
                "source_plan_digest_sha256": selection[
                    "expected_source_plan_digest_sha256"
                ],
                "physical_timeframes": list(PHYSICAL_TIMEFRAMES),
                "logical_timeframes": list(LOGICAL_TIMEFRAMES),
                "policy_execution_entered": False,
            }
        )
    )
    cache_identity_root = sha256_bytes(
        canonical_json_bytes(
            {
                "selection_root_sha256": selection["selection_root_sha256"],
                "accepted_cache_implementation_root": code_identity[
                    "accepted_cache_implementation_root"
                ],
                "slice_code_identity_root": code_identity[
                    "slice_code_identity_root"
                ],
                "config_identity_root": config_identity_root,
            }
        )
    )
    bundle_core = {
        "schema": BUNDLE_SCHEMA,
        "status": "SEALED_SOURCE_EQUIVALENCE_BUNDLE",
        "selected_day": selected_day,
        "selection_root_sha256": selection["selection_root_sha256"],
        "expected_source_plan_digest_sha256": selection[
            "expected_source_plan_digest_sha256"
        ],
        "accepted_cache_implementation_root": code_identity[
            "accepted_cache_implementation_root"
        ],
        "slice_code_identity_root": code_identity["slice_code_identity_root"],
        "config_identity_root": config_identity_root,
        "cache_identity_root": cache_identity_root,
        "source_stage_label": SOURCE_STAGE_LABEL,
        "physical_partitions": physical_output,
        "logical_partitions": logical_output,
        "cross_symbol_barrier": barrier,
        "postdecision_tick_classification": selection[
            "postdecision_tick_inventory"
        ]["classification"],
        "policy_execution_entered": False,
    }
    bundle = _with_self_root(bundle_core, "bundle_root_sha256")
    with measurements.stage("bundle_serialization_and_seal"):
        bundle_path = bundle_dir / "bundle.json"
        if bundle_path.exists():
            existing = _load_canonical_json(bundle_path, code="bundle_invalid")
            if existing != bundle:
                raise SliceRejected("warm_bundle_determinism_mismatch")
        else:
            if expected_mode != "cold":
                raise SliceRejected("warm_bundle_missing")
            _write_canonical_json(bundle_path, bundle, mode=0o444)
            _atomic_write(
                bundle_dir / "SEALED",
                bundle["bundle_root_sha256"].encode("ascii") + b"\n",
                mode=0o444,
            )

    if run_attestations:
        with measurements.stage("four_process_source_attestation"):
            attestations = _run_attestations(bundle_dir)
    else:
        attestations = {
            "count": 0,
            "roots": {},
            "fresh_processes": False,
            "policy_execution_entered": False,
            "commands": [],
        }
    capacity = _enforce_capacity(
        workspace=root,
        baseline_free=baseline_free,
        baseline_allocated=baseline_usage["allocated_bytes"],
    )
    measurement_result = measurements.result()
    measurement_result["end_to_end"] = _resource_delta(
        run_resource_started,
        _resource_snapshot(),
        wall_seconds=time.perf_counter() - run_wall_started,
    )
    swap_after = _swap_used_bytes()
    run_core = {
        "schema": RUN_SCHEMA,
        "status": "SOURCE_STAGE_EQUIVALENT",
        "run_label": str(run_label),
        "expected_mode": expected_mode,
        "executed_at_utc": _utc_now(),
        "command": list(command_argv or ("python_api:materialize_slice",)),
        "cwd": os.path.abspath(os.getcwd()),
        "workspace": str(root.resolve()),
        "accepted_base_commit": ACCEPTED_BASE_COMMIT,
        "selection_root_sha256": selection["selection_root_sha256"],
        "bundle_root_sha256": bundle["bundle_root_sha256"],
        "slice_code_identity": code_identity,
        "cache_hits": {"hits": hits, "misses": misses},
        "counts": {
            "symbols": len(symbols),
            "physical_partitions": len(physical_output),
            "logical_partitions": len(logical_output),
            "physical_bytes": sum(row["byte_count"] for row in physical_output),
            "physical_records": sum(row["record_count"] for row in physical_output),
        },
        "cross_symbol_barrier": barrier,
        "source_attestations": attestations,
        "measurements": measurement_result,
        "disk": {
            "warning_free_bytes": WARNING_FREE_BYTES,
            "hard_floor_free_bytes": HARD_FLOOR_FREE_BYTES,
            "free_before_bytes": int(baseline_free),
            "free_after_bytes": capacity["free_bytes"],
        },
        "scratch": {
            "quota_bytes": MAX_SCRATCH_BYTES,
            "allocated_growth_bytes": capacity["allocated_growth_bytes"],
            "peak_observed": measurement_result["peak_scratch"],
        },
        "swap": {
            "available": swap_before is not None and swap_after is not None,
            "used_before_bytes": swap_before,
            "used_after_bytes": swap_after,
            "delta_bytes": (
                swap_after - swap_before
                if swap_before is not None and swap_after is not None
                else None
            ),
        },
        "source_stage_only": True,
        "whole_replay_claim": False,
        "policy_execution_entered": False,
    }
    run_receipt = _with_self_root(run_core, "run_root_sha256")
    _write_canonical_json(root / "runs" / f"{run_label}.json", run_receipt)
    return run_receipt


def _re_root_bundle(bundle: Mapping[str, Any]) -> dict[str, Any]:
    return _with_self_root(bundle, "bundle_root_sha256")


def build_failure_case(
    *, bundle_dir: Path, cases_root: Path, case_name: str
) -> Path:
    base = Path(bundle_dir).resolve()
    bundle = _load_canonical_json(base / "bundle.json", code="bundle_invalid")
    case_dir = Path(cases_root) / case_name
    if case_dir.exists():
        raise SliceRejected("failure_case_already_exists")
    case_dir.mkdir(parents=True)
    target = min(
        bundle["physical_partitions"],
        key=lambda row: (int(row["byte_count"]), str(row["partition_id"])),
    )
    overrides: dict[str, dict[str, str]] = {}
    bundle_override: str | None = None
    marker_root = bundle["bundle_root_sha256"]

    if case_name in {"bit_flip", "truncation", "append"}:
        payload = (base / target["payload_path"]).read_bytes()
        if not payload:
            raise SliceRejected("failure_case_target_empty")
        if case_name == "bit_flip":
            changed = bytearray(payload)
            changed[len(changed) // 2] ^= 0x01
            payload = bytes(changed)
        elif case_name == "truncation":
            payload = payload[:-1]
        else:
            payload = payload + b"2099-01-01 00:00:00,1,1,1,1,1\n"
        override_path = case_dir / "payload.override"
        _atomic_write(override_path, payload)
        overrides[target["partition_id"]] = {
            "payload_path": override_path.name
        }
    elif case_name in {
        "manifest_mismatch",
        "schema_mismatch",
        "source_mismatch",
        "config_mismatch",
        "code_mismatch",
    }:
        manifest = _load_canonical_json(
            base / target["manifest_path"], code="manifest_invalid"
        )
        if case_name == "manifest_mismatch":
            manifest["undeclared"] = True
        elif case_name == "schema_mismatch":
            manifest["schema"] = "wrong.schema"
        elif case_name == "source_mismatch":
            manifest["source_identity_root"] = "0" * 64
        elif case_name == "config_mismatch":
            manifest["config_projection_root"] = "0" * 64
        else:
            manifest["implementation_root"] = "0" * 64
        override_path = case_dir / "manifest.override.json"
        _write_canonical_json(override_path, manifest)
        overrides[target["partition_id"]] = {
            "manifest_path": override_path.name
        }
    elif case_name == "partition_reorder":
        changed = dict(bundle)
        entries = [dict(row) for row in bundle["physical_partitions"]]
        entries[0], entries[1] = entries[1], entries[0]
        changed["physical_partitions"] = entries
        changed = _re_root_bundle(changed)
        override_path = case_dir / "bundle.override.json"
        _write_canonical_json(override_path, changed)
        bundle_override = override_path.name
        marker_root = changed["bundle_root_sha256"]
    elif case_name == "stale_cache":
        changed = dict(bundle)
        changed["cache_identity_root"] = "0" * 64
        changed = _re_root_bundle(changed)
        override_path = case_dir / "bundle.override.json"
        _write_canonical_json(override_path, changed)
        bundle_override = override_path.name
        marker_root = changed["bundle_root_sha256"]
    elif case_name in {"interruption_before_seal", "interruption_after_seal"}:
        pass
    else:
        raise SliceRejected("failure_case_unknown")

    case = {
        "schema": CASE_SCHEMA,
        "case_name": case_name,
        "base_bundle_dir": str(base),
        "bundle_manifest_override": bundle_override,
        "partition_overrides": overrides,
    }
    _write_canonical_json(case_dir / "case.json", case)
    if case_name != "interruption_before_seal":
        _atomic_write(
            case_dir / "SEALED", marker_root.encode("ascii") + b"\n", mode=0o444
        )
    return case_dir


def _invoke_independent_verifier(command: list[str]) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=600,
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError:
        raise SliceRejected("independent_verifier_output_invalid") from None
    if type(value) is not dict:
        raise SliceRejected("independent_verifier_output_invalid")
    return completed.returncode, value


def run_independent_verifier(
    *,
    bundle_dir: Path,
    selection_path: Path,
    output_path: Path,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    measurements = _StageMeasurements(Path(bundle_dir).parent)
    verifier_output = Path(output_path).with_suffix(".verifier.json")
    command = [
        sys.executable,
        str(VERIFIER_PATH.resolve()),
        "verify",
        "--bundle-dir",
        str(Path(bundle_dir).resolve()),
        "--selection",
        str(Path(selection_path).resolve()),
        "--output",
        str(verifier_output.resolve()),
    ]
    with measurements.stage("independent_verification"):
        returncode, receipt = _invoke_independent_verifier(command)
    if returncode != 0 or receipt.get("status") != "VERIFIED":
        raise SliceRejected("independent_verification_failed")
    envelope_core = {
        "schema": VERIFIER_ENVELOPE_SCHEMA,
        "status": "VERIFIED",
        "executed_at_utc": _utc_now(),
        "command": command,
        "orchestrator_command": list(
            command_argv or ("python_api:run_independent_verifier",)
        ),
        "receipt": receipt,
        "receipt_file_sha256": file_sha256(verifier_output),
        "measurements": measurements.result(),
    }
    envelope = _with_self_root(envelope_core, "envelope_root_sha256")
    _write_canonical_json(Path(output_path), envelope)
    return envelope


def run_failure_injections(
    *,
    bundle_dir: Path,
    selection_path: Path,
    cases_root: Path,
    output_path: Path,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    rejection_cases = (
        "bit_flip",
        "truncation",
        "append",
        "partition_reorder",
        "manifest_mismatch",
        "schema_mismatch",
        "source_mismatch",
        "config_mismatch",
        "code_mismatch",
        "stale_cache",
        "interruption_before_seal",
    )
    accepted_cases = ("interruption_after_seal",)
    rows: list[dict[str, Any]] = []
    commands: list[list[str]] = []
    for case_name in (*rejection_cases, *accepted_cases):
        case_dir = build_failure_case(
            bundle_dir=bundle_dir,
            cases_root=cases_root,
            case_name=case_name,
        )
        command = [
            sys.executable,
            str(VERIFIER_PATH.resolve()),
            "verify-case",
            "--case-dir",
            str(case_dir.resolve()),
            "--selection",
            str(Path(selection_path).resolve()),
        ]
        commands.append(command)
        returncode, receipt = _invoke_independent_verifier(command)
        if case_name in rejection_cases:
            passed = returncode != 0 and receipt.get("status") == "REJECTED"
        else:
            passed = returncode == 0 and receipt.get("status") == "VERIFIED"
            repeat_code, repeat = _invoke_independent_verifier(command)
            passed = bool(
                passed
                and repeat_code == 0
                and repeat.get("bundle_root_sha256")
                == receipt.get("bundle_root_sha256")
            )
        if not passed:
            raise SliceRejected(f"failure_injection_not_rejected:{case_name}")
        rows.append(
            {
                "case": case_name,
                "verdict": "PASS",
                "observed_status": receipt.get("status"),
                "observed_code": receipt.get("code"),
                "fresh_process": True,
            }
        )
    scratch_usage = _tree_usage(Path(cases_root))
    if scratch_usage["allocated_bytes"] > MAX_SCRATCH_BYTES:
        raise SliceRejected("failure_case_scratch_quota_exceeded")
    if shutil.disk_usage(Path(cases_root)).free < HARD_FLOOR_FREE_BYTES:
        raise SliceRejected("disk_hard_floor_reached")
    core = {
        "schema": INJECTION_SCHEMA,
        "status": "ALL_REQUIRED_CASES_PASS",
        "executed_at_utc": _utc_now(),
        "command": list(command_argv or ("python_api:run_failure_injections",)),
        "verifier_commands": commands,
        "cases": rows,
        "case_count": len(rows),
        "scratch_usage": scratch_usage,
        "policy_execution_entered": False,
    }
    receipt = _with_self_root(core, "injection_root_sha256")
    _write_canonical_json(Path(output_path), receipt)
    return receipt


def _load_run(path: Path) -> dict[str, Any]:
    value = _load_canonical_json(path, code="run_receipt_invalid")
    if value.get("schema") != RUN_SCHEMA:
        raise SliceRejected("run_receipt_invalid")
    _verify_self_root(value, "run_root_sha256", code="run_receipt_invalid")
    return value


def finalize_result(
    *,
    selection_path: Path,
    cold_run_path: Path,
    cold_repeat_run_path: Path,
    warm_run_path: Path,
    warm_repeat_run_path: Path,
    verifier_paths: Sequence[Path],
    injection_path: Path,
    output_path: Path,
    command_argv: Sequence[str] | None = None,
) -> dict[str, Any]:
    selection = verify_selection_receipt(selection_path)
    runs = [
        _load_run(path)
        for path in (
            cold_run_path,
            cold_repeat_run_path,
            warm_run_path,
            warm_repeat_run_path,
        )
    ]
    bundle_roots = {run["bundle_root_sha256"] for run in runs}
    if len(bundle_roots) != 1:
        raise SliceRejected("run_determinism_mismatch")
    physical_count = int(selection["scope"]["physical_partition_count"])
    if any(
        run["cache_hits"] != {"hits": 0, "misses": physical_count}
        for run in runs[:2]
    ):
        raise SliceRejected("cold_cache_classification_mismatch")
    if any(
        run["cache_hits"] != {"hits": physical_count, "misses": 0}
        for run in runs[2:]
    ):
        raise SliceRejected("warm_cache_classification_mismatch")
    if any(
        run["source_attestations"].get("count") != 4
        or run["source_attestations"].get("policy_execution_entered") is not False
        for run in runs
    ):
        raise SliceRejected("source_attestation_incomplete")
    if len(
        {
            canonical_json_bytes(run["source_attestations"]["roots"])
            for run in runs
        }
    ) != 1:
        raise SliceRejected("source_attestation_determinism_mismatch")
    verifier_envelopes = [
        _load_canonical_json(path, code="verifier_envelope_invalid")
        for path in verifier_paths
    ]
    for envelope in verifier_envelopes:
        if envelope.get("schema") != VERIFIER_ENVELOPE_SCHEMA:
            raise SliceRejected("verifier_envelope_invalid")
        _verify_self_root(
            envelope, "envelope_root_sha256", code="verifier_envelope_invalid"
        )
        if envelope.get("receipt", {}).get("bundle_root_sha256") not in bundle_roots:
            raise SliceRejected("verifier_bundle_mismatch")
        if envelope.get("status") != "VERIFIED" or envelope.get("receipt", {}).get(
            "status"
        ) != "VERIFIED":
            raise SliceRejected("verifier_envelope_invalid")
    injections = _load_canonical_json(injection_path, code="injection_receipt_invalid")
    if injections.get("schema") != INJECTION_SCHEMA:
        raise SliceRejected("injection_receipt_invalid")
    _verify_self_root(
        injections, "injection_root_sha256", code="injection_receipt_invalid"
    )
    if injections.get("status") != "ALL_REQUIRED_CASES_PASS":
        raise SliceRejected("injection_receipt_invalid")

    stage_wall = []
    end_to_end_wall = []
    for run in runs:
        stage_wall.append(
            round(
                sum(
                    float(row.get("wall_seconds") or 0.0)
                    for row in run["measurements"]["stages"].values()
                ),
                9,
            )
        )
        end_to_end_wall.append(
            float(run["measurements"]["end_to_end"]["wall_seconds"])
        )
    ratio = (
        round(end_to_end_wall[0] / end_to_end_wall[2], 6)
        if end_to_end_wall[2]
        else None
    )
    retained_by_workspace = {
        str(run["workspace"]): _tree_usage(Path(run["workspace"])) for run in runs
    }
    failure_case_scratch = injections.get("scratch_usage")
    if (
        type(failure_case_scratch) is not dict
        or type(failure_case_scratch.get("allocated_bytes")) is not int
    ):
        raise SliceRejected("injection_receipt_invalid")
    combined_retained_allocated = sum(
        row["allocated_bytes"] for row in retained_by_workspace.values()
    ) + int(failure_case_scratch["allocated_bytes"])
    if combined_retained_allocated > MAX_SCRATCH_BYTES:
        raise SliceRejected("combined_scratch_quota_exceeded")
    commands = [selection["selection_command"]]
    commands.extend(run["command"] for run in runs)
    commands.extend(envelope["command"] for envelope in verifier_envelopes)
    commands.append(injections["command"])
    commands.append(list(command_argv or ("python_api:finalize_result",)))
    result_core = {
        "schema": RESULT_SCHEMA,
        "status": "ACCEPTED",
        "gate": "BOUNDED_EQUIVALENCE_ACCEPTED_FOR_REPLAY_SLICE",
        "accepted_base_commit": ACCEPTED_BASE_COMMIT,
        "selected_day": selection["selected_day"],
        "selection_rule": selection["selection_rule"],
        "selection_root_sha256": selection["selection_root_sha256"],
        "source_plan_digest_sha256": selection[
            "expected_source_plan_digest_sha256"
        ],
        "bundle_root_sha256": next(iter(bundle_roots)),
        "scope": selection["scope"],
        "structural_counts": runs[0]["counts"],
        "source_attestation_roots": [
            run["source_attestations"]["roots"] for run in runs
        ],
        "determinism": {
            "fresh_process_runs": 4,
            "cold_runs": 2,
            "warm_runs": 2,
            "bundle_roots_identical": True,
            "cold_cache_misses_per_run": physical_count,
            "warm_cache_hits_per_run": physical_count,
        },
        "source_stage_measurement": {
            "label": SOURCE_STAGE_LABEL,
            "stage_attributed_wall_seconds_by_run": stage_wall,
            "end_to_end_wall_seconds_by_run": end_to_end_wall,
            "cold_to_first_warm_ratio": ratio,
            "whole_replay_claim": False,
        },
        "resource_measurements": [run["measurements"] for run in runs],
        "disk": [run["disk"] for run in runs],
        "scratch": [run["scratch"] for run in runs],
        "combined_retained_scratch": {
            "quota_bytes": MAX_SCRATCH_BYTES,
            "allocated_bytes": combined_retained_allocated,
            "workspaces": retained_by_workspace,
            "failure_cases": failure_case_scratch,
        },
        "swap": [run["swap"] for run in runs],
        "independent_verification": [
            envelope["receipt"] for envelope in verifier_envelopes
        ],
        "failure_injections": injections["cases"],
        "postdecision_tick_inventory": selection["postdecision_tick_inventory"],
        "exact_command_receipts": commands,
        "outcome_blind_source_only": True,
        "policy_execution_entered": False,
        "successor_replay_launched": False,
        "broker_mutation_enabled": False,
    }
    result = _with_self_root(result_core, "result_root_sha256")
    forbidden = (
        "pnl",
        "win_rate",
        "win_count",
        "loss_count",
        "loss_total",
        "profit_total",
        "r_total",
        "r_multiple",
        "treatment_economics",
        "march_",
        "economic_outcome",
        "comparative_economic",
    )
    serialized = canonical_json_bytes(result).lower()
    if any(token.encode("ascii") in serialized for token in forbidden):
        raise SliceRejected("result_content_policy_failed")
    _write_canonical_json(Path(output_path), result)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    select = sub.add_parser("select")
    select.add_argument("--source-ledger", type=Path, required=True)
    select.add_argument("--output", type=Path, required=True)
    select.add_argument(
        "--expected-source-plan-digest-sha256",
        default=DEFAULT_SOURCE_PLAN_DIGEST,
    )
    select.add_argument("--month", default="2026-01")

    materialize = sub.add_parser("materialize")
    materialize.add_argument("--selection", type=Path, required=True)
    materialize.add_argument("--workspace", type=Path, required=True)
    materialize.add_argument("--run-label", required=True)
    materialize.add_argument("--mode", choices=("cold", "warm"), required=True)

    verify = sub.add_parser("verify-independent")
    verify.add_argument("--bundle-dir", type=Path, required=True)
    verify.add_argument("--selection", type=Path, required=True)
    verify.add_argument("--output", type=Path, required=True)

    inject = sub.add_parser("inject")
    inject.add_argument("--bundle-dir", type=Path, required=True)
    inject.add_argument("--selection", type=Path, required=True)
    inject.add_argument("--cases-root", type=Path, required=True)
    inject.add_argument("--output", type=Path, required=True)

    finalize = sub.add_parser("finalize")
    finalize.add_argument("--selection", type=Path, required=True)
    finalize.add_argument("--cold-run", type=Path, required=True)
    finalize.add_argument("--cold-repeat-run", type=Path, required=True)
    finalize.add_argument("--warm-run", type=Path, required=True)
    finalize.add_argument("--warm-repeat-run", type=Path, required=True)
    finalize.add_argument("--verifier", type=Path, action="append", required=True)
    finalize.add_argument("--injections", type=Path, required=True)
    finalize.add_argument("--output", type=Path, required=True)
    return parser


def _main(argv: list[str]) -> int:
    if argv and argv[0] == "_attest":
        if len(argv) != 3:
            return 2
        try:
            receipt = _attest_bundle(Path(argv[1]), argv[2])
        except (SliceRejected, SourceBatchRejected):
            return 2
        print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
        return 0
    args = _parser().parse_args(argv)
    command_receipt = _executed_command_receipt(argv)
    try:
        if args.command == "select":
            result = create_selection_receipt(
                source_ledger=args.source_ledger,
                output_path=args.output,
                expected_symbols=EXPECTED_SYMBOLS,
                expected_source_plan_digest_sha256=(
                    args.expected_source_plan_digest_sha256
                ),
                month=args.month,
                command_argv=command_receipt,
            )
        elif args.command == "materialize":
            result = materialize_slice(
                selection_path=args.selection,
                workspace=args.workspace,
                run_label=args.run_label,
                expected_mode=args.mode,
                command_argv=command_receipt,
            )
        elif args.command == "verify-independent":
            result = run_independent_verifier(
                bundle_dir=args.bundle_dir,
                selection_path=args.selection,
                output_path=args.output,
                command_argv=command_receipt,
            )
        elif args.command == "inject":
            result = run_failure_injections(
                bundle_dir=args.bundle_dir,
                selection_path=args.selection,
                cases_root=args.cases_root,
                output_path=args.output,
                command_argv=command_receipt,
            )
        else:
            result = finalize_result(
                selection_path=args.selection,
                cold_run_path=args.cold_run,
                cold_repeat_run_path=args.cold_repeat_run,
                warm_run_path=args.warm_run,
                warm_repeat_run_path=args.warm_repeat_run,
                verifier_paths=args.verifier,
                injection_path=args.injections,
                output_path=args.output,
                command_argv=command_receipt,
            )
    except (SliceRejected, SourceBatchRejected) as exc:
        code = exc.code if hasattr(exc, "code") else "source_batch_rejected"
        print(json.dumps({"status": "REJECTED", "code": code}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
