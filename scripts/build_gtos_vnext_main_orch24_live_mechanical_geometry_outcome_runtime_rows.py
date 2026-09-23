#!/usr/bin/env python3
"""Build runtime rows for Main Orch24 live-mechanical geometry/outcome evidence."""

from __future__ import annotations

import os
import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime_wave"

ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_OUTCOME_RUNTIME_SUMMARY_{DATE}.json"
)

GEOMETRY_BINDING_LEDGER = "MAIN_ORCH24_GEOMETRY_BINDING_LEDGER_2026-05-16.jsonl"
NONCOMPUTABLE_PROOF_LEDGER = (
    "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_NONCOMPUTABLE_PROOF_LEDGER_2026-05-16.jsonl"
)
OVERALL_RECONCILIATION_LEDGER = (
    "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_RECONCILIATION_LEDGER_2026-05-16.jsonl"
)
SCORER_REFRESH_DELTA_LEDGER = (
    "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DELTA_LEDGER_2026-05-16.jsonl"
)
SCORER_REFRESH_DRY_RUN_LEDGER = (
    "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_DRY_RUN_LEDGER_2026-05-16.jsonl"
)
OPPORTUNITY_PROJECTION_ROWS = (
    "MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_ROWS_2026-05-17.jsonl"
)
SPLIT_SUMMARY = "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_SPLIT_SUMMARY_2026-05-16.jsonl"

SOURCE_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    (
        "UNIT_009394",
        "build_main_orchestrator_live_mechanical_latest_overall_reconciliation_2026_05_16.py",
        "1a10e1d41965be86070740d8b7dc864fd5632247",
    ),
    (
        "UNIT_009395",
        "build_main_orchestrator_live_mechanical_latest_scorer_refresh_2026_05_16.py",
        "38d61653d12fcda99894bceb82ef9b4ca65592d9",
    ),
    (
        "UNIT_009396",
        "build_main_orchestrator_live_mechanical_opportunity_preservation_projection_2026_05_17.py",
        "cae65de9becfb7adf246707d53cc73d48654023b",
    ),
    (
        "UNIT_009469",
        "build_main_orchestrator_replayable_geometry_materialization_2026_05_16.py",
        "8be28ea2965c8614925a2b7fe12bb6bec2ff7430",
    ),
    ("UNIT_009697", GEOMETRY_BINDING_LEDGER, "a5449ed3f60e9c5ede53916156ba9fea19281102"),
    ("UNIT_009722", NONCOMPUTABLE_PROOF_LEDGER, "f98d5af9d2f5ce3a4d728b8694ffc3d32d8bd34e"),
    (
        "UNIT_009723",
        "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_OUTPUT_MANIFEST_2026-05-16.json",
        "0691bbdbb8755835e65d6f11350f0b246d3dd094",
    ),
    ("UNIT_009724", OVERALL_RECONCILIATION_LEDGER, "3f14941f7b8ce14e272d698b5258cdc8c1df97e7"),
    ("UNIT_009725", SPLIT_SUMMARY, "a1776420a8f14bba2d0123ebbf7a7ced2626a1ac"),
    (
        "UNIT_009726",
        "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_SUMMARY_2026-05-16.json",
        "7bf26f28d844d10537c575730fd8bdbb6afe69b0",
    ),
    (
        "UNIT_009727",
        "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_OVERALL_VERIFICATION_RESULT_2026-05-16.json",
        "ce2fd6ed53ff795877843ae5f32ae54104b1d6ed",
    ),
    ("UNIT_009728", SCORER_REFRESH_DELTA_LEDGER, "e9f67c889e0be268b8c1afd31fbe205ec03dbd55"),
    ("UNIT_009729", SCORER_REFRESH_DRY_RUN_LEDGER, "0802bc7c029784b7daed04a401e1300e44ec529d"),
    (
        "UNIT_009730",
        "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_OUTPUT_MANIFEST_2026-05-16.json",
        "7c15e2842e3cbfb22440e19c1604a7e86637dbcc",
    ),
    (
        "UNIT_009731",
        "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_SUMMARY_2026-05-16.json",
        "388b9fe4d51d0c52b6df95270860cf0b3b49e7dc",
    ),
    (
        "UNIT_009732",
        "MAIN_ORCH24_LIVE_MECHANICAL_LATEST_SCORER_REFRESH_VERIFICATION_RESULT_2026-05-16.json",
        "446340dbdd2ce980b2f42283fcdf88385fb7c363",
    ),
    (
        "UNIT_009733",
        "MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_MANIFEST_2026-05-17.json",
        "99139621f96c635585106a58387d2d7ebf9a92d2",
    ),
    ("UNIT_009734", OPPORTUNITY_PROJECTION_ROWS, "64c42d23be1e6e8b83d990df5a3720f8894a504b"),
    (
        "UNIT_009735",
        "MAIN_ORCH24_LIVE_MECHANICAL_OPPORTUNITY_PRESERVATION_PROJECTION_SUMMARY_2026-05-17.json",
        "2e6caeb59c87a4e4e84f7ca4246074c6adcce27d",
    ),
    (
        "UNIT_009867",
        "MAIN_ORCH24_REPLAYABLE_GEOMETRY_MATERIALIZATION_SUMMARY_2026-05-16.md",
        "9ce410ef1c0f31a29d223dbf6d6b77c1eaa44403",
    ),
    (
        "UNIT_010320",
        "verify_main_orchestrator_live_mechanical_latest_overall_reconciliation_2026_05_16.py",
        "0d386fa079182693edacbe81982deb67a14db363",
    ),
    (
        "UNIT_010321",
        "verify_main_orchestrator_live_mechanical_latest_scorer_refresh_2026_05_16.py",
        "c5a4f6af5ae1189158c5d40937bb0749e4e11bf6",
    ),
    (
        "UNIT_010322",
        "verify_main_orchestrator_live_mechanical_opportunity_preservation_projection_2026_05_17.py",
        "71c57097f94d166683b4f3de66ef6c555f821683",
    ),
    (
        "UNIT_010395",
        "verify_main_orchestrator_replayable_geometry_materialization_2026_05_16.py",
        "875912d0d3ac3836b6db10b039cb51e8ca84d7e7",
    ),
)

ANCHOR_FIELDS = (
    "symbol",
    "source_symbol",
    "market",
    "timeframe",
    "market_timeframe",
    "route_session",
    "route_family",
    "primitive",
    "side",
    "source_component",
    "entry_variant",
    "target_stop_order_class",
)

TARGET_FIRST_STATUSES = {
    "ENTRY_TOUCHED_THEN_TP1",
    "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
}
STOP_FIRST_STATUSES = {
    "ENTRY_TOUCHED_THEN_SL",
    "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
}
NOFILL_AVOID_STATUSES = {
    "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH",
    "NO_FILL_CANCELLED_TARGET_REACHED_WITHOUT_ENTRY_TOUCH",
    "NO_FILL_CANCELLED_WRONG_SIDE",
    "NO_FILL_AT_SHIFT",
}
PENDING_STATUSES = {
    "NO_FILL_STILL_PENDING",
    "BROKER_FILLED_AWAITING_EXIT_R",
    "ENTRY_TOUCHED_UNRESOLVED",
}


def _long_path(path: Path) -> str:
    text = str(path.resolve())
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _path_text(path: Path) -> str:
    try:
        if path.is_relative_to(REPO_ROOT):
            return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        pass
    return str(path).replace("\\", "/")


def _source_path(name: str) -> Path:
    return SOURCE_DIR / name


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    return "" if text.casefold() in {"none", "null", "nan"} else text


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@lru_cache(maxsize=None)
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(_long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        for line in handle:
            if not line.strip():
                continue
            payload = json.loads(line)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _read_json(path: Path) -> Any:
    with open(_long_path(path), "r", encoding="utf-8-sig", newline="") as handle:
        return json.load(handle)


def _source_row_count(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() == ".jsonl":
        with open(_long_path(path), "rb") as handle:
            return sum(1 for line in handle if line.strip())
    if path.suffix.lower() == ".json":
        try:
            payload = _read_json(path)
        except json.JSONDecodeError:
            return None
        if isinstance(payload, list):
            return len(payload)
        if isinstance(payload, dict):
            for key in (
                "total_rows",
                "total_projection_rows",
                "projection_rows",
                "row_count",
                "rows",
                "input_rows",
                "source_row_count",
                "total_runtime_rows",
                "total_rows_represented",
            ):
                value = payload.get(key)
                if isinstance(value, int):
                    return value
                if isinstance(value, list):
                    return len(value)
    return None


def _session_for(symbol: str, timestamp: str) -> str:
    if not timestamp:
        return ""
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return ""
    minutes = dt.hour * 60 + dt.minute
    symbol_key = symbol.upper()
    if symbol_key in {"XAUUSD", "XAGUSD"}:
        windows = ((7 * 60, 10 * 60 + 30, "london_core"), (13 * 60, 17 * 60, "ny_core"))
    elif symbol_key in {"US30", "US30_CASH", "US30_CASH"}:
        windows = ((8 * 60, 10 * 60 + 30, "london_core"), (13 * 60 + 30, 16 * 60, "ny_core"))
    elif symbol_key == "NAS100":
        windows = ((13 * 60, 17 * 60, "ny_core"),)
    elif symbol_key in {"USDJPY", "GBPJPY"}:
        windows = (
            (0, 3 * 60, "tokyo_kz"),
            (7 * 60, 9 * 60 + 30, "london_core"),
            (13 * 60, 15 * 60 + 30, "ny_core"),
        )
    elif symbol_key == "GBPUSD":
        windows = ((7 * 60, 12 * 60, "london_core"), (13 * 60, 15 * 60 + 30, "ny_core"))
    else:
        windows = ()
    for start, end, session in windows:
        if start <= minutes < end:
            return session
    return "off_core_session"


def _market_for_symbol(symbol: str) -> str:
    return symbol


def _proxy_class(value: float | None) -> str:
    if value is None:
        return ""
    if value >= 1.0:
        return "STRONG_POSITIVE_PROXY_R"
    if value > 0:
        return "POSITIVE_PROXY_R"
    if value <= -1.0:
        return "STRONG_NEGATIVE_PROXY_R"
    if value < 0:
        return "NEGATIVE_PROXY_R"
    return "FLAT_PROXY_R"


def _metric_from_scalar(value: float | None, source_field: str) -> dict[str, Any]:
    if value is None:
        return {}
    return {
        "sum": value,
        "count": 1,
        "mean": value,
        "positive_rows": 1 if value > 0 else 0,
        "negative_rows": 1 if value < 0 else 0,
        "zero_rows": 1 if value == 0 else 0,
        "source_field": source_field,
        "source_shape": "scalar_proxy",
    }


def _event_scope(row: dict[str, Any]) -> dict[str, str]:
    return {
        field: _norm(row.get(field))
        for field in ANCHOR_FIELDS
        if _norm(row.get(field))
    }


def _base_runtime_row(
    *,
    source_row: dict[str, Any],
    source_artifact: Path,
    source_row_id: str,
    decision: str,
    source_component: str,
    source_role: str,
    r_evidence_class: str,
    action_class: str,
    implementation_action: str,
    runtime_effect: str,
    symbol: str = "",
    side: str = "",
    framework: str = "",
    route_family: str = "",
    primitive: str = "",
    route_session: str = "",
    target_stop_order_class: str = "",
    proxy_r: float | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_hash = _sha256_file(source_artifact)
    source_symbol = symbol
    market = _market_for_symbol(symbol) if symbol else ""
    row: dict[str, Any] = {
        "schema_version": "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime_v1",
        "wave_id": WAVE_ID,
        "source_name": SOURCE_NAME,
        "evidence_family": EVIDENCE_FAMILY,
        "source_group": "main_orch24_live_mechanical_geometry_outcome",
        "source_role": source_role,
        "system_surface": "main_orch24_live_mechanical_geometry_outcome_runtime",
        "source_component": source_component,
        "decision": decision,
        "action_class": action_class,
        "implementation_action": implementation_action,
        "runtime_effect_now": runtime_effect,
        "r_evidence_class": r_evidence_class,
        "source_row_id": source_row_id,
        "row_key": source_row_id,
        "source_artifact": _path_text(source_artifact),
        "source_artifact_sha256": source_hash,
        "source_path": _path_text(source_artifact),
        "drill_through_path": _path_text(source_artifact),
        "symbol": symbol,
        "source_symbol": source_symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market": market,
        "timeframe": "M15" if symbol else "",
        "market_timeframe": "M15" if symbol else "",
        "framework": framework,
        "route_family": route_family,
        "route_session": route_session,
        "horizon_id": "forward_shadow_24h",
        "primitive": primitive or "main_orch24_live_mechanical_geometry_outcome",
        "side": side,
        "source_bound": bool(source_component and (symbol or source_artifact)),
        "source_complete": decision in {"FOLLOW", "AVOID"} and bool(symbol and side),
        "target_stop_order_class": target_stop_order_class,
        "proxy_r_class": _proxy_class(proxy_r),
        "source_candidate_id": source_row.get("candidate_id"),
        "source_strategy_id": source_row.get("strategy_id"),
        "source_strategy_family": source_row.get("strategy_family"),
        "source_outcome_status": (
            source_row.get("outcome_status")
            or source_row.get("after_outcome_status")
            or source_row.get("binding_status")
            or source_row.get("score_status")
        ),
        "source_score_status": source_row.get("score_status")
        or source_row.get("after_score_status"),
        "source_status_reason": source_row.get("status_reason"),
        "row_count": 1,
    }
    metrics: dict[str, Any] = {}
    proxy_metric = _metric_from_scalar(proxy_r, "main_orch24_live_mechanical_proxy_r")
    if proxy_metric:
        metrics["proxy_score"] = proxy_metric
    metrics["effective_n"] = {
        "sum": 1,
        "count": 1,
        "mean": 1,
        "positive_rows": 1,
        "negative_rows": 0,
        "zero_rows": 0,
        "source_field": "runtime_row",
        "source_shape": "row_count",
    }
    row["r_metrics"] = metrics
    if extra:
        row.update(extra)
    row["event_scope"] = _event_scope(row)
    row["runtime_row_id"] = (
        f"main-orch24-live-mech:{_sha256_payload({k: row.get(k) for k in ('source_row_id', 'source_artifact', 'source_component', 'decision')})[:24]}"
    )
    return row


def _decision_from_status(
    status: str,
    action_class: str = "",
) -> tuple[str, str, str, str, str, float | None]:
    status = _upper(status)
    action_class = _upper(action_class)
    if status in TARGET_FIRST_STATUSES:
        return (
            "FOLLOW",
            "main_orch24_live_mechanical_forward_follow",
            "main_orch24_live_mechanical_forward_follow_scorer",
            "MAIN_ORCH24_LIVE_MECHANICAL_FORWARD_TP1_FOLLOW",
            "live_mechanical_forward_follow_pressure",
            1.5,
        )
    if status in STOP_FIRST_STATUSES:
        return (
            "AVOID",
            "main_orch24_live_mechanical_stop_or_nofill_avoid",
            "main_orch24_live_mechanical_stop_first_avoid_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_STOP_FIRST_AVOID_FILTER",
            "live_mechanical_stop_first_avoid_filter",
            -1.0,
        )
    if status in NOFILL_AVOID_STATUSES:
        return (
            "AVOID",
            "main_orch24_live_mechanical_stop_or_nofill_avoid",
            "main_orch24_live_mechanical_nofill_avoid_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_NOFILL_AVOID_FILTER",
            "live_mechanical_nofill_avoid_filter",
            -0.5,
        )
    if "AMBIGUOUS" in status:
        return (
            "MIXED",
            "main_orch24_live_mechanical_ambiguous_path_guard",
            "main_orch24_live_mechanical_ambiguous_path_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_AMBIGUOUS_M15_SOURCE_REQUIRED",
            "live_mechanical_ambiguous_path_source_guard",
            0.0,
        )
    if status in PENDING_STATUSES or "PENDING" in status or "AWAITING" in status:
        return (
            "MIXED",
            "main_orch24_live_mechanical_pending_lifecycle_guard",
            "main_orch24_live_mechanical_pending_lifecycle_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_PENDING_LIFECYCLE_SOURCE_REQUIRED",
            "live_mechanical_pending_lifecycle_guard",
            0.0,
        )
    if action_class == "SOURCE_REPAIR":
        return (
            "MIXED",
            "main_orch24_live_mechanical_source_acquisition",
            "main_orch24_live_mechanical_source_acquisition_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_SOURCE_ACQUISITION_REQUIRED",
            "live_mechanical_source_acquisition_guard",
            0.0,
        )
    if action_class == "KILL":
        return (
            "AVOID",
            "main_orch24_live_mechanical_kill_guard",
            "main_orch24_live_mechanical_kill_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_KILL_AVOID_FILTER",
            "live_mechanical_kill_avoid_filter",
            -0.25,
        )
    if action_class == "REDESIGN":
        return (
            "AVOID",
            "main_orch24_live_mechanical_redesign_guard",
            "main_orch24_live_mechanical_redesign_guard",
            "MAIN_ORCH24_LIVE_MECHANICAL_REDESIGN_AVOID_FILTER",
            "live_mechanical_redesign_avoid_filter",
            -0.25,
        )
    return (
        "MIXED",
        "main_orch24_live_mechanical_context",
        "main_orch24_live_mechanical_context_guard",
        "MAIN_ORCH24_LIVE_MECHANICAL_CONTEXT_ONLY",
        "live_mechanical_context_only",
        0.0,
    )


def _context_only_decision() -> tuple[str, str, str, str, str, float | None]:
    return (
        "MIXED",
        "main_orch24_live_mechanical_context",
        "main_orch24_live_mechanical_context_guard",
        "MAIN_ORCH24_LIVE_MECHANICAL_CONTEXT_ONLY",
        "live_mechanical_context_only",
        0.0,
    )


def _target_stop_class(status: str) -> str:
    status = _upper(status)
    if status in TARGET_FIRST_STATUSES:
        return "TARGET_FIRST_PROXY_DOMINANT"
    if status in STOP_FIRST_STATUSES:
        return "STOP_FIRST_PROXY_DOMINANT"
    if status in NOFILL_AVOID_STATUSES or status in PENDING_STATUSES:
        return "NO_FILL_OR_UNFILLED_DOMINANT"
    if "AMBIGUOUS" in status or "UNRESOLVED" in status:
        return "TARGET_STOP_AMBIGUOUS_OR_MIXED"
    return ""


def _build_projection_rows() -> list[dict[str, Any]]:
    projection_path = _source_path(OPPORTUNITY_PROJECTION_ROWS)
    delta_rows = _read_jsonl(_source_path(SCORER_REFRESH_DELTA_LEDGER))
    delta_by_key = {
        (_norm(row.get("candidate_id")), _norm(row.get("strategy_id"))): row
        for row in delta_rows
    }
    runtime_rows: list[dict[str, Any]] = []
    for row in _read_jsonl(projection_path):
        candidate_id = _norm(row.get("candidate_id"))
        strategy_id = _norm(row.get("strategy_id"))
        delta = delta_by_key.get((candidate_id, strategy_id), {})
        symbol = _norm(row.get("broker_symbol") or row.get("symbol"))
        side = _upper(row.get("side"))
        status = _upper(row.get("outcome_status"))
        action_class = _upper(delta.get("action_class"))
        decision, component, role, r_class, effect, default_proxy = _decision_from_status(
            status,
            action_class,
        )
        source_score_status = _upper(row.get("score_status") or delta.get("after_score_status"))
        route_family = _norm(row.get("strategy_family") or strategy_id)
        if source_score_status == "NOT_AN_ENTRY_STRATEGY":
            decision, component, role, r_class, effect, default_proxy = _context_only_decision()
        proxy_r = _float(row.get("strategy_proxy_r"))
        if proxy_r is None:
            proxy_r = _float(delta.get("after_proxy_r"))
        if proxy_r is None:
            proxy_r = default_proxy
        if decision == "AVOID" and proxy_r is not None and proxy_r > 0:
            proxy_r = -abs(default_proxy or 0.25)
        runtime_rows.append(
            _base_runtime_row(
                source_row=row,
                source_artifact=projection_path,
                source_row_id=_norm(row.get("row_id"))
                or f"{candidate_id}:{strategy_id}",
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=effect,
                implementation_action=effect,
                runtime_effect=effect,
                symbol=symbol,
                side=side,
                framework=_norm(row.get("framework")),
                route_family=route_family,
                primitive=_norm(row.get("strategy_family")) or "live_mechanical_candidate_path",
                route_session=_session_for(symbol, _norm(row.get("decision_time_utc"))),
                target_stop_order_class=_target_stop_class(status),
                proxy_r=proxy_r,
                extra={
                    "source_action_class": action_class,
                    "source_proxy_delta_class": delta.get("proxy_r_delta_class"),
                    "entry_touch_distance_status": row.get("entry_touch_distance_status"),
                    "entry_retest_redesign_bucket": row.get("entry_retest_redesign_bucket"),
                    "ltf_path_order_label": row.get("ltf_path_order_label"),
                    "m15_path_provenance_status": row.get("m15_path_provenance_status"),
                },
            )
        )
    return runtime_rows


def _build_noncomputable_rows() -> list[dict[str, Any]]:
    source_path = _source_path(NONCOMPUTABLE_PROOF_LEDGER)
    runtime_rows: list[dict[str, Any]] = []
    for row in _read_jsonl(source_path):
        score_status = _upper(row.get("score_status"))
        if score_status in {
            "COMPUTED_FROM_CANDIDATE_PATH",
            "CONTEXT_ATTACHED",
            "NOT_AN_ENTRY_STRATEGY",
        }:
            component = "main_orch24_live_mechanical_context"
            role = "main_orch24_live_mechanical_context_guard"
            r_class = "MAIN_ORCH24_LIVE_MECHANICAL_CONTEXT_ONLY"
            action_class = "live_mechanical_context_only"
            decision = "MIXED"
        else:
            component = "main_orch24_live_mechanical_source_acquisition"
            role = "main_orch24_live_mechanical_source_acquisition_guard"
            r_class = "MAIN_ORCH24_LIVE_MECHANICAL_SOURCE_ACQUISITION_REQUIRED"
            action_class = "live_mechanical_source_acquisition_guard"
            decision = "MIXED"
        runtime_rows.append(
            _base_runtime_row(
                source_row=row,
                source_artifact=source_path,
                source_row_id=_norm(row.get("row_id"))
                or f"{row.get('candidate_id')}:{row.get('strategy_id')}",
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=action_class,
                implementation_action=action_class,
                runtime_effect=action_class,
                route_family=_norm(row.get("strategy_id") or row.get("strategy_status")),
                primitive="live_mechanical_noncomputable_proof",
                proxy_r=0.0,
                extra={
                    "missing_fields": row.get("missing_fields"),
                    "why_no_weaker_proxy_r": row.get("why_no_weaker_proxy_r"),
                    "safe_flags": row.get("safe_flags"),
                },
            )
        )
    return runtime_rows


def _build_geometry_rows() -> list[dict[str, Any]]:
    source_path = _source_path(GEOMETRY_BINDING_LEDGER)
    runtime_rows: list[dict[str, Any]] = []
    for row in _read_jsonl(source_path):
        status = _upper(row.get("binding_status"))
        proxy_available = bool(row.get("proxy_r_available"))
        exact_available = bool(row.get("exact_r_available"))
        if exact_available:
            decision = "FOLLOW"
            component = "main_orch24_live_mechanical_geometry_proxy_follow"
            role = "main_orch24_live_mechanical_geometry_proxy_follow"
            r_class = "MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_PROXY_BOUND"
            action_class = "live_mechanical_geometry_proxy_follow"
            proxy_r = 0.25
        elif proxy_available and not status.startswith("NONCOMPUTABLE"):
            decision = "MIXED"
            component = "main_orch24_live_mechanical_geometry_proxy_context"
            role = "main_orch24_live_mechanical_geometry_proxy_context"
            r_class = "MAIN_ORCH24_LIVE_MECHANICAL_GEOMETRY_PROXY_BOUND"
            action_class = "live_mechanical_geometry_proxy_context"
            proxy_r = 0.0
        else:
            decision = "MIXED"
            component = "main_orch24_live_mechanical_source_acquisition"
            role = "main_orch24_live_mechanical_source_acquisition_guard"
            r_class = "MAIN_ORCH24_LIVE_MECHANICAL_SOURCE_ACQUISITION_REQUIRED"
            action_class = "live_mechanical_source_acquisition_guard"
            proxy_r = 0.0
        runtime_rows.append(
            _base_runtime_row(
                source_row=row,
                source_artifact=source_path,
                source_row_id=_norm(row.get("binding_id"))
                or f"{row.get('candidate_id')}:{row.get('result_id')}",
                decision=decision,
                source_component=component,
                source_role=role,
                r_evidence_class=r_class,
                action_class=action_class,
                implementation_action=action_class,
                runtime_effect=action_class,
                route_family="geometry_binding",
                primitive="live_mechanical_geometry_binding",
                proxy_r=proxy_r,
                extra={
                    "binding_status": row.get("binding_status"),
                    "exact_r_available": exact_available,
                    "proxy_r_available": proxy_available,
                    "fields_present": row.get("fields_present"),
                    "missing_fields_for_exact_r": row.get("missing_fields_for_exact_r")
                    or row.get("missing_fields"),
                    "source_geometry_file": row.get("source_file"),
                    "source_geometry_sha256": row.get("source_sha256"),
                },
            )
        )
    return runtime_rows


def _source_artifacts_summary(runtime_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows_by_source = Counter(row["source_artifact"] for row in runtime_rows)
    artifacts: list[dict[str, Any]] = []
    for unit_id, name, git_hash in SOURCE_ARTIFACTS:
        path = _source_path(name)
        path_text = _path_text(path)
        artifacts.append(
            {
                "unit_id": unit_id,
                "path": path_text,
                "name": name,
                "hash": git_hash,
                "hash_algorithm": "git_blob",
                "row_count": _source_row_count(path),
                "runtime_rows_read": rows_by_source.get(path_text, 0),
            }
        )
    return artifacts


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        field: sum(1 for row in rows if not _norm(row.get(field)))
        for field in ANCHOR_FIELDS
    }


def build_runtime_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = [
        *_build_projection_rows(),
        *_build_noncomputable_rows(),
        *_build_geometry_rows(),
    ]
    rows.sort(key=lambda row: (row["source_component"], row["source_row_id"]))
    coverage = {
        "symbols": dict(sorted(Counter(row.get("symbol") for row in rows if row.get("symbol")).items())),
        "source_symbols": dict(sorted(Counter(row.get("source_symbol") for row in rows if row.get("source_symbol")).items())),
        "markets": dict(sorted(Counter(row.get("market") for row in rows if row.get("market")).items())),
        "timeframes": dict(sorted(Counter(row.get("timeframe") for row in rows if row.get("timeframe")).items())),
        "sessions": dict(sorted(Counter(row.get("route_session") for row in rows if row.get("route_session")).items())),
        "sides": dict(sorted(Counter(row.get("side") for row in rows if row.get("side")).items())),
        "frameworks": dict(sorted(Counter(row.get("framework") for row in rows if row.get("framework")).items())),
        "route_families": dict(sorted(Counter(row.get("route_family") for row in rows if row.get("route_family")).items())),
        "entry_variants": dict(sorted(Counter(row.get("entry_variant") for row in rows if row.get("entry_variant")).items())),
        "target_stop_order_classes": dict(sorted(Counter(row.get("target_stop_order_class") for row in rows if row.get("target_stop_order_class")).items())),
    }
    source_artifacts = _source_artifacts_summary(rows)
    known_counts = [item["row_count"] for item in source_artifacts if item["row_count"] is not None]
    summary = {
        "schema_version": "gtos_vnext_main_orch24_live_mechanical_geometry_outcome_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": len(rows),
        "wave_source_rows_counted": sum(known_counts),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": sum(1 for item in source_artifacts if item["row_count"] is None),
        "projection_runtime_rows": sum(1 for row in rows if row["source_artifact"].endswith(OPPORTUNITY_PROJECTION_ROWS)),
        "noncomputable_proof_runtime_rows": sum(1 for row in rows if row["source_artifact"].endswith(NONCOMPUTABLE_PROOF_LEDGER)),
        "geometry_binding_runtime_rows": sum(1 for row in rows if row["source_artifact"].endswith(GEOMETRY_BINDING_LEDGER)),
        "decision_counts": dict(sorted(Counter(row["decision"] for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(row["source_component"] for row in rows).items())),
        "source_role_counts": dict(sorted(Counter(row["source_role"] for row in rows).items())),
        "r_evidence_class_counts": dict(sorted(Counter(row["r_evidence_class"] for row in rows).items())),
        "action_class_counts": dict(sorted(Counter(row["action_class"] for row in rows).items())),
        "proxy_r_class_counts": dict(sorted(Counter(row.get("proxy_r_class") for row in rows if row.get("proxy_r_class")).items())),
        "source_acquisition_required_rows": sum(
            1
            for row in rows
            if row["source_component"] == "main_orch24_live_mechanical_source_acquisition"
        ),
        "positive_proxy_rows": sum(1 for row in rows if row["decision"] == "FOLLOW"),
        "avoid_or_redesign_rows": sum(1 for row in rows if row["decision"] == "AVOID"),
        "coverage_counts": coverage,
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }
    return rows, summary


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")
    OUTPUT_SUMMARY.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _outputs_match(rows: list[dict[str, Any]], summary: dict[str, Any]) -> bool:
    if not OUTPUT_ROWS.exists() or not OUTPUT_SUMMARY.exists():
        return False
    expected_rows = [
        json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows
    ]
    actual_rows = OUTPUT_ROWS.read_text(encoding="utf-8").splitlines()
    if actual_rows != expected_rows:
        return False
    try:
        actual_summary = json.loads(OUTPUT_SUMMARY.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return actual_summary == summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows, summary = build_runtime_rows()
    if args.check:
        if not _outputs_match(rows, summary):
            print("Generated Main Orch24 live-mechanical geometry/outcome runtime outputs are stale.")
            return 1
        print(
            "Main Orch24 live-mechanical geometry/outcome runtime outputs are current: "
            f"{summary['runtime_row_count']} rows"
        )
        return 0
    write_outputs(rows, summary)
    print(
        "Wrote Main Orch24 live-mechanical geometry/outcome runtime outputs: "
        f"{OUTPUT_ROWS} ({summary['runtime_row_count']} rows)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
