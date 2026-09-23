#!/usr/bin/env python3
"""Out-of-band Sierra depth feature enrichment for live candidate rows.

This script is shadow-only. It reads already-written live candidate rows,
parses the exact Sierra ``.depth`` file recorded on each candidate, and appends
pre-decision ladder-depth features to a separate JSONL lane. It never calls AI,
Databento, canary, MT5 order APIs, or live trading code.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.extract_sierra_depth_features import (  # noqa: E402
    FEATURE_FIELDS,
    extract_event_features,
    extract_events_features_batch,
)
from src.research_infra.forward_capture import (  # noqa: E402
    SIERRA_PROXY_BY_SYMBOL,
    SIERRA_SOURCE_STATUS_BY_SYMBOL,
    append_jsonl,
)


SCHEMA_VERSION = "sierra_depth_feature_snapshot_v1"
DEPTH_FEATURE_VERSION = "sierra_depth_predecision_eob_top10_v2"
DEFAULT_SOURCE = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/sierra_depth_feature_snapshots.jsonl")
DEFAULT_CHECKPOINT = Path("pipeline_state/sierra_depth_enrichment_checkpoint.json")
DEFAULT_MAX_FILE_SIZE_MB = 128.0
NO_LEAK_STATUS = "PASS_PRE_DECISION_WINDOWS_ONLY"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_state(depth_path: Path | None) -> dict[str, Any]:
    if depth_path is None:
        return {"depth_file_exists": False, "depth_file_size_bytes": None, "depth_file_mtime_utc": None}
    try:
        stat = depth_path.stat()
    except OSError:
        return {"depth_file_exists": False, "depth_file_size_bytes": None, "depth_file_mtime_utc": None}
    return {
        "depth_file_exists": True,
        "depth_file_size_bytes": int(stat.st_size),
        "depth_file_mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
    }


def update_checkpoint(
    checkpoint_path: Path | None,
    *,
    row: dict[str, Any],
    run_started_at_utc: str,
    max_file_size_mb: float | None,
    max_per_symbol: int | None,
) -> None:
    if checkpoint_path is None:
        return
    payload = read_json(checkpoint_path)
    candidates = payload.get("candidates") if isinstance(payload.get("candidates"), dict) else {}
    cid = str(row.get("candidate_id") or "")
    if cid:
        candidates[cid] = {
            "candidate_id": cid,
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "last_attempt_utc": row.get("created_at_utc"),
            "last_feature_status": row.get("feature_status"),
            "features_present": row.get("features_present"),
            "depth_path": row.get("depth_path"),
            "depth_file_size_bytes": row.get("depth_file_size_bytes"),
            "row_key": row.get("row_key"),
        }
    payload.update(
        {
            "schema_version": "sierra_depth_enrichment_checkpoint_v1",
            "updated_at_utc": utc_now_iso(),
            "last_run_started_at_utc": run_started_at_utc,
            "depth_feature_version": DEPTH_FEATURE_VERSION,
            "max_file_size_mb": max_file_size_mb,
            "max_per_symbol": max_per_symbol,
            "candidates": candidates,
        }
    )
    write_json(checkpoint_path, payload)


def latest_candidates(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in rows:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = latest.get(cid)
        if current is None or str(row.get("created_at_utc") or "") >= str(current.get("created_at_utc") or ""):
            latest[cid] = row
    return sorted(latest.values(), key=lambda item: str(item.get("decision_time_utc") or ""), reverse=True)


def existing_state(path: Path) -> tuple[set[str], set[str]]:
    row_keys: set[str] = set()
    successful_candidate_ids: set[str] = set()
    for row in read_jsonl(path):
        key = row.get("row_key")
        if key:
            row_keys.add(str(key))
        if (
            row.get("features_present") is True
            and row.get("feature_status") == "FEATURES_EXTRACTED"
            and row.get("source_status")
            and row.get("parity_status")
            and row.get("interpretation_status")
        ):
            cid = row.get("candidate_id")
            if cid:
                successful_candidate_ids.add(str(cid))
    return row_keys, successful_candidate_ids


def latest_feature_rows(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current = latest.get(cid)
        if current is None or str(row.get("created_at_utc") or "") >= str(current.get("created_at_utc") or ""):
            latest[cid] = row
    return latest


def _sierra_object(candidate: dict[str, Any]) -> dict[str, Any]:
    external = candidate.get("external_confluence")
    if not isinstance(external, dict):
        return {}
    sierra = external.get("sierra")
    return sierra if isinstance(sierra, dict) else {}


def _row_key(
    *,
    candidate_id: str,
    source_symbol: Any,
    feature_status: str,
    depth_path: Path | None,
) -> str:
    file_state = "no_file"
    if depth_path is not None and depth_path.exists():
        try:
            stat = depth_path.stat()
            file_state = f"{stat.st_size}:{int(stat.st_mtime)}"
        except OSError:
            file_state = "stat_failed"
    return "|".join([SCHEMA_VERSION, candidate_id, str(source_symbol or "none"), feature_status, file_state])


def _base_row(
    candidate: dict[str, Any],
    *,
    sierra: dict[str, Any],
    feature_status: str,
    depth_path: Path | None,
) -> dict[str, Any]:
    candidate_id = str(candidate.get("candidate_id") or "")
    symbol = str(candidate.get("symbol") or "")
    depth_file_state = file_state(depth_path)
    sierra_status = sierra.get("status")
    if depth_file_state.get("depth_file_exists") is True and sierra_status == "LOCAL_DEPTH_FILE_MISSING":
        sierra_status = "LOCAL_DEPTH_FILE_PRESENT_AFTER_INITIAL_MISSING_STATUS"
    source_boundary = SIERRA_SOURCE_STATUS_BY_SYMBOL.get(
        symbol,
        {
            "source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
            "parity_status": "SOURCE_BLOCKED",
            "interpretation_status": "BLOCKED_NO_PROXY",
        },
    )
    source_status = sierra.get("source_status") or source_boundary.get("source_status")
    parity_status = sierra.get("parity_status") or source_boundary.get("parity_status")
    interpretation_status = sierra.get("interpretation_status") or source_boundary.get("interpretation_status")
    proxy_class = sierra.get("proxy_class") or source_boundary.get("proxy_class")
    allowed_use = sierra.get("allowed_use") or source_boundary.get("allowed_use")
    claim_boundary = sierra.get("claim_boundary") or source_boundary.get("claim_boundary")
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "row_key": _row_key(
            candidate_id=candidate_id,
            source_symbol=sierra.get("source_symbol"),
            feature_status=feature_status,
            depth_path=depth_path,
        ),
        "candidate_id": candidate_id,
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "asof_cutoff_utc": candidate.get("decision_time_utc"),
        "side": candidate.get("side"),
        "framework": candidate.get("framework"),
        "source_system": "sierra_depth",
        "depth_path": str(depth_path) if depth_path else sierra.get("depth_path"),
        "depth_feature_version": DEPTH_FEATURE_VERSION,
        **depth_file_state,
        "sierra_status": sierra_status,
        "source_status": source_status,
        "parity_status": parity_status,
        "interpretation_status": interpretation_status,
        "proxy_class": proxy_class,
        "allowed_use": allowed_use,
        "claim_boundary": claim_boundary,
        "depth_interpretation_allowed": sierra.get("depth_interpretation_allowed")
        if sierra.get("depth_interpretation_allowed") is not None
        else source_boundary.get("depth_interpretation_allowed"),
        "scid_interpretation_allowed": sierra.get("scid_interpretation_allowed")
        if sierra.get("scid_interpretation_allowed") is not None
        else source_boundary.get("scid_interpretation_allowed"),
        "control_only": sierra.get("control_only")
        if sierra.get("control_only") is not None
        else source_boundary.get("control_only"),
        "sierra_source_symbol": sierra.get("source_symbol"),
        "sierra_futures_symbol": sierra.get("futures_symbol"),
        "feature_status": feature_status,
        "feature_extraction_mode": "out_of_band_full",
        "feature_extraction_policy": (
            "Live candidate rows capture Sierra source path/mtime/size immediately; "
            "this lane enriches full depth features out of band so large .depth scans "
            "cannot delay or drop candidate logging."
        ),
        "features_present": False,
        "features": {},
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "no_leak_status": NO_LEAK_STATUS,
    }


def _source_boundary(candidate: dict[str, Any], sierra: dict[str, Any]) -> dict[str, Any]:
    symbol = str(candidate.get("symbol") or "")
    fallback = SIERRA_SOURCE_STATUS_BY_SYMBOL.get(
        symbol,
        {
            "source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
            "parity_status": "SOURCE_BLOCKED",
            "interpretation_status": "BLOCKED_NO_PROXY",
        },
    )
    return {
        "source_status": sierra.get("source_status") or fallback.get("source_status"),
        "parity_status": sierra.get("parity_status") or fallback.get("parity_status"),
        "interpretation_status": sierra.get("interpretation_status") or fallback.get("interpretation_status"),
        "proxy_class": sierra.get("proxy_class") or fallback.get("proxy_class"),
        "allowed_use": sierra.get("allowed_use") or fallback.get("allowed_use"),
        "claim_boundary": sierra.get("claim_boundary") or fallback.get("claim_boundary"),
        "depth_interpretation_allowed": sierra.get("depth_interpretation_allowed")
        if sierra.get("depth_interpretation_allowed") is not None
        else fallback.get("depth_interpretation_allowed"),
        "scid_interpretation_allowed": sierra.get("scid_interpretation_allowed")
        if sierra.get("scid_interpretation_allowed") is not None
        else fallback.get("scid_interpretation_allowed"),
        "control_only": sierra.get("control_only")
        if sierra.get("control_only") is not None
        else fallback.get("control_only"),
    }


def is_no_registered_sierra_proxy(candidate: dict[str, Any], sierra: dict[str, Any]) -> bool:
    boundary = _source_boundary(candidate, sierra)
    return (
        str(sierra.get("status") or "") == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
        or str(boundary.get("source_status") or "") == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
    )


def build_no_registered_proxy_row(candidate: dict[str, Any], *, sierra: dict[str, Any]) -> dict[str, Any]:
    row = _base_row(
        candidate,
        sierra=sierra,
        feature_status="NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
        depth_path=None,
    )
    row["row_key"] = "|".join(
        [
            SCHEMA_VERSION,
            str(candidate.get("candidate_id") or ""),
            "none",
            "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
            DEPTH_FEATURE_VERSION,
            "registry_boundary_v2",
        ]
    )
    row["usable_as_databento_equivalent"] = False
    return row


def repair_existing_feature_row(candidate: dict[str, Any], existing: dict[str, Any]) -> dict[str, Any] | None:
    if existing.get("features_present") is not True or existing.get("feature_status") != "FEATURES_EXTRACTED":
        return None
    if (
        existing.get("source_status")
        and existing.get("parity_status")
        and existing.get("interpretation_status")
        and existing.get("proxy_class")
        and existing.get("allowed_use")
        and existing.get("claim_boundary")
    ):
        return None
    sierra = _sierra_object(candidate)
    boundary = _source_boundary(candidate, sierra)
    row = dict(existing)
    row.update(boundary)
    row["created_at_utc"] = utc_now_iso()
    row["row_key"] = "|".join(
        [
            SCHEMA_VERSION,
            str(candidate.get("candidate_id") or ""),
            str(row.get("sierra_source_symbol") or sierra.get("source_symbol") or "none"),
            "FEATURES_EXTRACTED_SOURCE_STATUS_REPAIR",
            str(existing.get("row_key") or "unknown_source_row"),
        ]
    )
    row["sierra_status"] = row.get("sierra_status") or sierra.get("status")
    row["usable_as_databento_equivalent"] = not str(row.get("interpretation_status") or "").startswith("BLOCKED")
    row["source_status_repair"] = True
    return row


def build_pending_row(candidate: dict[str, Any], *, reason: str) -> dict[str, Any]:
    sierra = _sierra_object(candidate)
    depth_raw = sierra.get("depth_path")
    depth_path = Path(str(depth_raw)) if depth_raw else None
    feature_status = "FEATURE_EXTRACTION_PENDING_HEAVY_DEPTH_SCAN"
    if depth_path is None:
        boundary = _source_boundary(candidate, sierra)
        feature_status = (
            "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
            if boundary.get("source_status") == "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL"
            else "MISSING_DEPTH_PATH"
        )
    row = _base_row(
        candidate,
        sierra=sierra,
        feature_status=feature_status,
        depth_path=depth_path,
    )
    row["row_key"] = "|".join(
        [
            SCHEMA_VERSION,
            str(candidate.get("candidate_id") or ""),
            str(row.get("sierra_source_symbol") or "none"),
            feature_status,
            "status_only_v1",
        ]
    )
    row["pending_reason"] = reason
    row["usable_as_databento_equivalent"] = not str(row.get("interpretation_status") or "").startswith("BLOCKED")
    return row


def build_file_size_guard_row(
    candidate: dict[str, Any],
    *,
    sierra: dict[str, Any],
    depth_path: Path,
    max_file_size_mb: float,
) -> dict[str, Any]:
    row = _base_row(
        candidate,
        sierra=sierra,
        feature_status="FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD",
        depth_path=depth_path,
    )
    max_bytes = int(max_file_size_mb * 1024 * 1024)
    row.update(
        {
            "features_present": False,
            "features": {},
            "file_size_guard": {
                "status": "DEFERRED_REQUIRES_EXPLICIT_HIGHER_CAP",
                "max_file_size_mb": max_file_size_mb,
                "max_file_size_bytes": max_bytes,
                "depth_file_size_bytes": row.get("depth_file_size_bytes"),
            },
            "guard_reason": (
                "Sierra depth file exceeds the configured unattended enrichment file-size cap. "
                "Run with a higher --max-file-size-mb during a dedicated backfill window if needed."
            ),
            "usable_as_databento_equivalent": not str(row.get("interpretation_status") or "").startswith("BLOCKED"),
        }
    )
    row["row_key"] = "|".join(
        [
            SCHEMA_VERSION,
            str(candidate.get("candidate_id") or ""),
            str(sierra.get("source_symbol") or "none"),
            "FEATURE_EXTRACTION_DEFERRED_FILE_SIZE_GUARD",
            str(max_bytes),
            str(row.get("depth_file_size_bytes") or "missing"),
        ]
    )
    return row


def build_feature_snapshot_row_from_extracted(
    candidate: dict[str, Any],
    *,
    sierra: dict[str, Any],
    depth_path: Path,
    extracted: dict[str, Any],
) -> dict[str, Any]:
    feature = extracted.get("feature_row") or {}
    data_status = feature.get("data_status")
    feature_status = "FEATURES_EXTRACTED" if data_status == "ok" else "FEATURES_ATTEMPTED_NO_SAMPLES"
    row = _base_row(candidate, sierra=sierra, feature_status=feature_status, depth_path=depth_path)
    row.update(
        {
            "features_present": data_status == "ok",
            "features": {field: feature.get(field) for field in FEATURE_FIELDS},
            "data_status": data_status,
            "sample_method": feature.get("sample_method"),
            "depth_header": extracted.get("header") or {},
            "usable_as_databento_equivalent": not str(row.get("interpretation_status") or "").startswith("BLOCKED"),
        }
    )
    row["row_key"] = _row_key(
        candidate_id=str(candidate.get("candidate_id") or ""),
        source_symbol=sierra.get("source_symbol"),
        feature_status=feature_status,
        depth_path=depth_path,
    )
    return row


def build_feature_row(candidate: dict[str, Any], *, max_file_size_mb: float | None = DEFAULT_MAX_FILE_SIZE_MB) -> dict[str, Any]:
    sierra = _sierra_object(candidate)
    depth_raw = sierra.get("depth_path")
    depth_path = Path(str(depth_raw)) if depth_raw else None
    if not sierra:
        return _base_row(candidate, sierra={}, feature_status="MISSING_SIERRA_CONFLUENCE_OBJECT", depth_path=None)
    if depth_path is None:
        if is_no_registered_sierra_proxy(candidate, sierra):
            return build_no_registered_proxy_row(candidate, sierra=sierra)
        return _base_row(candidate, sierra=sierra, feature_status="MISSING_DEPTH_PATH", depth_path=None)
    if not depth_path.exists():
        return _base_row(candidate, sierra=sierra, feature_status="LOCAL_DEPTH_FILE_MISSING", depth_path=depth_path)
    if max_file_size_mb is not None:
        size_bytes = file_state(depth_path).get("depth_file_size_bytes")
        if size_bytes is not None and int(size_bytes) > int(max_file_size_mb * 1024 * 1024):
            return build_file_size_guard_row(
                candidate,
                sierra=sierra,
                depth_path=depth_path,
                max_file_size_mb=max_file_size_mb,
            )
    decision_time = parse_utc(candidate.get("decision_time_utc"))
    if decision_time is None:
        return _base_row(candidate, sierra=sierra, feature_status="MISSING_DECISION_TIME", depth_path=depth_path)
    symbol = str(candidate.get("symbol") or "")
    proxy = SIERRA_PROXY_BY_SYMBOL.get(symbol) or {}
    tick_size = proxy.get("tick_size")
    if tick_size is None:
        return _base_row(candidate, sierra=sierra, feature_status="MISSING_REGISTERED_TICK_SIZE", depth_path=depth_path)

    try:
        extracted = extract_event_features(
            depth_path=depth_path,
            event={
                "event_id": candidate.get("candidate_id"),
                "symbol": symbol,
                "event_class": "LIVE_CANDIDATE_SHADOW",
                "decision": candidate.get("analysis_decision"),
                "framework": candidate.get("framework"),
                "direction": candidate.get("side"),
                "canonical_m15_close_utc": decision_time.isoformat(),
                "window_start_utc": (decision_time - timedelta(minutes=60)).isoformat(),
                "window_end_utc": decision_time.isoformat(),
            },
            source_symbol=str(sierra.get("source_symbol") or proxy.get("root")),
            futures_symbol=str(sierra.get("futures_symbol") or proxy.get("futures_symbol")),
            tick_size=float(tick_size),
        )
    except Exception as exc:  # noqa: BLE001
        row = _base_row(candidate, sierra=sierra, feature_status="FEATURE_EXTRACTION_FAILED", depth_path=depth_path)
        row["error"] = f"{type(exc).__name__}: {exc}"
        return row

    return build_feature_snapshot_row_from_extracted(
        candidate,
        sierra=sierra,
        depth_path=depth_path,
        extracted=extracted,
    )


def _batch_candidate_spec(
    candidate: dict[str, Any],
    *,
    max_file_size_mb: float | None,
) -> tuple[tuple[str, str, str, float], dict[str, Any], Path] | dict[str, Any]:
    sierra = _sierra_object(candidate)
    depth_raw = sierra.get("depth_path")
    depth_path = Path(str(depth_raw)) if depth_raw else None
    if not sierra:
        return _base_row(candidate, sierra={}, feature_status="MISSING_SIERRA_CONFLUENCE_OBJECT", depth_path=None)
    if depth_path is None:
        if is_no_registered_sierra_proxy(candidate, sierra):
            return build_no_registered_proxy_row(candidate, sierra=sierra)
        return _base_row(candidate, sierra=sierra, feature_status="MISSING_DEPTH_PATH", depth_path=None)
    if not depth_path.exists():
        return _base_row(candidate, sierra=sierra, feature_status="LOCAL_DEPTH_FILE_MISSING", depth_path=depth_path)
    if max_file_size_mb is not None:
        size_bytes = file_state(depth_path).get("depth_file_size_bytes")
        if size_bytes is not None and int(size_bytes) > int(max_file_size_mb * 1024 * 1024):
            return build_file_size_guard_row(
                candidate,
                sierra=sierra,
                depth_path=depth_path,
                max_file_size_mb=max_file_size_mb,
            )
    decision_time = parse_utc(candidate.get("decision_time_utc"))
    if decision_time is None:
        return _base_row(candidate, sierra=sierra, feature_status="MISSING_DECISION_TIME", depth_path=depth_path)
    symbol = str(candidate.get("symbol") or "")
    proxy = SIERRA_PROXY_BY_SYMBOL.get(symbol) or {}
    tick_size = proxy.get("tick_size")
    if tick_size is None:
        return _base_row(candidate, sierra=sierra, feature_status="MISSING_REGISTERED_TICK_SIZE", depth_path=depth_path)
    source_symbol = str(sierra.get("source_symbol") or proxy.get("root"))
    futures_symbol = str(sierra.get("futures_symbol") or proxy.get("futures_symbol"))
    return ((str(depth_path), source_symbol, futures_symbol, float(tick_size)), sierra, depth_path)


def build_feature_rows_batch(
    candidates: list[dict[str, Any]],
    *,
    max_file_size_mb: float | None = DEFAULT_MAX_FILE_SIZE_MB,
) -> dict[str, dict[str, Any]]:
    """Build feature rows for many candidates, scanning each depth file once."""
    rows_by_candidate: dict[str, dict[str, Any]] = {}
    grouped: dict[tuple[str, str, str, float], list[tuple[dict[str, Any], dict[str, Any], Path]]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id:
            continue
        spec = _batch_candidate_spec(candidate, max_file_size_mb=max_file_size_mb)
        if isinstance(spec, dict):
            rows_by_candidate[candidate_id] = spec
            continue
        group_key, sierra, depth_path = spec
        grouped.setdefault(group_key, []).append((candidate, sierra, depth_path))

    for (depth_path_raw, source_symbol, futures_symbol, tick_size), group in grouped.items():
        depth_path = Path(depth_path_raw)
        events = []
        for candidate, _sierra, _depth_path in group:
            decision_time = parse_utc(candidate.get("decision_time_utc"))
            if decision_time is None:
                continue
            events.append(
                {
                    "event_id": candidate.get("candidate_id"),
                    "symbol": candidate.get("symbol"),
                    "event_class": "LIVE_CANDIDATE_SHADOW",
                    "decision": candidate.get("analysis_decision"),
                    "framework": candidate.get("framework"),
                    "direction": candidate.get("side"),
                    "canonical_m15_close_utc": decision_time.isoformat(),
                    "window_start_utc": (decision_time - timedelta(minutes=60)).isoformat(),
                    "window_end_utc": decision_time.isoformat(),
                }
            )
        try:
            extracted_by_event_id = extract_events_features_batch(
                depth_path=depth_path,
                events=events,
                source_symbol=source_symbol,
                futures_symbol=futures_symbol,
                tick_size=tick_size,
            )
        except Exception as exc:  # noqa: BLE001
            for candidate, sierra, path in group:
                row = _base_row(candidate, sierra=sierra, feature_status="FEATURE_EXTRACTION_FAILED", depth_path=path)
                row["error"] = f"{type(exc).__name__}: {exc}"
                rows_by_candidate[str(candidate.get("candidate_id") or "")] = row
            continue
        for candidate, sierra, path in group:
            candidate_id = str(candidate.get("candidate_id") or "")
            extracted = extracted_by_event_id.get(candidate_id)
            if extracted is None:
                row = _base_row(candidate, sierra=sierra, feature_status="FEATURE_EXTRACTION_FAILED", depth_path=path)
                row["error"] = "batch extractor did not return event_id"
            else:
                row = build_feature_snapshot_row_from_extracted(
                    candidate,
                    sierra=sierra,
                    depth_path=path,
                    extracted=extracted,
                )
                row["batch_depth_file_extraction"] = True
            rows_by_candidate[candidate_id] = row
    return rows_by_candidate


def run(
    *,
    source: Path = DEFAULT_SOURCE,
    output: Path = DEFAULT_OUTPUT,
    max_hours: float = 12.0,
    limit: int | None = None,
    pending_status_only: bool = False,
    max_file_size_mb: float | None = DEFAULT_MAX_FILE_SIZE_MB,
    max_per_symbol: int | None = None,
    checkpoint: Path | None = DEFAULT_CHECKPOINT,
    symbols: set[str] | None = None,
    candidate_ids: set[str] | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    run_started = now.isoformat()
    candidates = latest_candidates(read_jsonl(source))
    existing_keys, successful_candidate_ids = existing_state(output)
    latest_features = latest_feature_rows(output)
    rows_written = 0
    rows_written_by_symbol: dict[str, int] = {}
    skipped: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for candidate in candidates:
        cid = str(candidate.get("candidate_id") or "")
        symbol = str(candidate.get("symbol") or "")
        if candidate_ids is not None and cid not in candidate_ids:
            skipped["candidate_id_filter"] = skipped.get("candidate_id_filter", 0) + 1
            continue
        if symbols is not None and symbol not in symbols:
            skipped["symbol_filter"] = skipped.get("symbol_filter", 0) + 1
            continue
        if max_per_symbol is not None and rows_written_by_symbol.get(symbol, 0) >= max_per_symbol:
            skipped["per_symbol_throttle"] = skipped.get("per_symbol_throttle", 0) + 1
            continue
        decision_time = parse_utc(candidate.get("decision_time_utc"))
        if decision_time is None:
            skipped["missing_decision_time"] = skipped.get("missing_decision_time", 0) + 1
            continue
        if now - decision_time > timedelta(hours=max_hours):
            skipped["outside_max_hours"] = skipped.get("outside_max_hours", 0) + 1
            continue
        repaired = repair_existing_feature_row(candidate, latest_features.get(cid) or {})
        if not repaired and cid in successful_candidate_ids:
            skipped["already_extracted"] = skipped.get("already_extracted", 0) + 1
            continue
        if repaired:
            row = repaired
        elif pending_status_only:
            row = build_pending_row(candidate, reason="full_depth_feature_extraction_runs_out_of_band")
        else:
            row = build_feature_row(candidate, max_file_size_mb=max_file_size_mb)
        key = str(row.get("row_key") or "")
        if key in existing_keys:
            skipped["duplicate_file_state"] = skipped.get("duplicate_file_state", 0) + 1
            continue
        append_jsonl(output, row)
        update_checkpoint(
            checkpoint,
            row=row,
            run_started_at_utc=run_started,
            max_file_size_mb=max_file_size_mb,
            max_per_symbol=max_per_symbol,
        )
        existing_keys.add(key)
        rows_written += 1
        rows_written_by_symbol[symbol] = rows_written_by_symbol.get(symbol, 0) + 1
        status = str(row.get("feature_status") or "UNKNOWN")
        status_counts[status] = status_counts.get(status, 0) + 1
        if row.get("features_present") is True:
            successful_candidate_ids.add(cid)
        if limit is not None and rows_written >= limit:
            skipped["limit_reached"] = skipped.get("limit_reached", 0) + 1
            break
    return {
        "schema_version": "sierra_live_candidate_depth_enrichment_summary_v1",
        "created_at_utc": utc_now_iso(),
        "source": str(source),
        "output": str(output),
        "candidates_seen": len(candidates),
        "rows_written": rows_written,
        "rows_written_by_symbol": dict(sorted(rows_written_by_symbol.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "skipped": dict(sorted(skipped.items())),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "pending_status_only": pending_status_only,
        "max_file_size_mb": max_file_size_mb,
        "max_per_symbol": max_per_symbol,
        "symbols": sorted(symbols) if symbols is not None else None,
        "candidate_ids": sorted(candidate_ids) if candidate_ids is not None else None,
        "checkpoint": str(checkpoint) if checkpoint else None,
        "depth_feature_version": DEPTH_FEATURE_VERSION,
    }


def expand_csv_args(values: list[str] | None) -> set[str] | None:
    if not values:
        return None
    expanded = {
        item.strip()
        for value in values
        for item in str(value).split(",")
        if item.strip()
    }
    return expanded or None


def expand_symbol_args(values: list[str] | None) -> set[str] | None:
    return expand_csv_args(values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--max-hours", type=float, default=12.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--pending-status-only", action="store_true")
    parser.add_argument("--max-file-size-mb", type=float, default=DEFAULT_MAX_FILE_SIZE_MB)
    parser.add_argument("--max-per-symbol", type=int)
    parser.add_argument("--symbol", action="append", help="Optional GTOS symbol filter; repeatable or comma-separated.")
    parser.add_argument(
        "--candidate-id",
        action="append",
        help="Optional candidate_id filter for targeted source repair; repeatable or comma-separated.",
    )
    parser.add_argument("--checkpoint", default=str(DEFAULT_CHECKPOINT))
    parser.add_argument("--no-checkpoint", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = run(
        source=Path(args.source),
        output=Path(args.output),
        max_hours=args.max_hours,
        limit=args.limit,
        pending_status_only=args.pending_status_only,
        max_file_size_mb=args.max_file_size_mb,
        max_per_symbol=args.max_per_symbol,
        symbols=expand_symbol_args(args.symbol),
        candidate_ids=expand_csv_args(args.candidate_id),
        checkpoint=None if args.no_checkpoint else Path(args.checkpoint),
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
