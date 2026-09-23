#!/usr/bin/env python3
"""Build runtime rows for Main Orch24 unified candidate path/proxy evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.gtos_vnext_runtime import resolve_vnext_symbol_family


DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME"
EVIDENCE_FAMILY = "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime"
SOURCE_NAME = "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime_wave"

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
UNIFIED_CANDIDATE_LEDGER = "MAIN_ORCH24_UNIFIED_CANDIDATE_LEDGER_2026-05-16.jsonl"
SPLIT_SUMMARY_LEDGER = "MAIN_ORCH24_SPLIT_SUMMARY_2026-05-16.jsonl"
OUTPUT_ROWS = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY = (
    ROUTE_DIR
    / f"GTOS_VNEXT_MAIN_ORCH24_UNIFIED_CANDIDATE_PATH_PROXY_RUNTIME_SUMMARY_{DATE}.json"
)

SOURCE_ARTIFACTS: tuple[tuple[str, str, str], ...] = (
    (
        "UNIT_009917",
        SPLIT_SUMMARY_LEDGER,
        "8d7b9b0256bb693b43664305db30fece6b32c69c",
    ),
    (
        "UNIT_009946",
        UNIFIED_CANDIDATE_LEDGER,
        "df156abfdb8df4f80e45f5e2957bd06b06130385",
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

ENTRY_VARIANTS = {
    "BODY_MID_RETEST_LIMIT_PROXY",
    "SWEEP_WICK_EXTREME_RETEST_PROXY",
    "NEXT_BAR_OPEN_MARKET_PROXY",
    "SIGNAL_CLOSE_MARKET_PROXY",
}
TARGET_TOKENS = ("TARGET_TOUCH_FIRST", "TARGET_FIRST", "TARGET_TOUCH_BEFORE_STOP")
STOP_TOKENS = ("STOP_TOUCH_FIRST", "STOP_FIRST", "STOP_TOUCH_BEFORE_TARGET")
NOFILL_TOKENS = ("NO_FILL", "NOFILL", "NOT_FILLED", "UNFILLED")
AMBIGUOUS_TOKENS = ("AMBIGUOUS", "UNRESOLVED", "INTERVAL_STRADDLES_ZERO")


def _path_text(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _norm(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"none", "nan", "null", "na", "n/a"}:
        return ""
    return text


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _metric(value: Any, source: str) -> dict[str, Any]:
    return {"value": value, "source": source}


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


@lru_cache(maxsize=None)
def _source_line(path_text: str, line_no: int) -> dict[str, Any]:
    if not path_text or line_no <= 0:
        return {}
    path = Path(path_text)
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", errors="ignore") as handle:
        for idx, line in enumerate(handle, start=1):
            if idx == line_no:
                if not line.strip():
                    return {}
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    return {}
    return {}


def _route_parts(*rows: dict[str, Any]) -> tuple[str, str, str, str]:
    for row in rows:
        route = _norm(row.get("route_candidate_id"))
        if route:
            parts = route.split("|")
            if len(parts) >= 4:
                return parts[0], parts[1], parts[2], parts[3]
    return "", "", "", ""


def _target_stop_class(row: dict[str, Any], detail: dict[str, Any]) -> str:
    for key in ("target_stop_contract_id", "target_stop_order_class"):
        value = _norm(detail.get(key)) or _norm(row.get(key))
        if value:
            return value
    horizon = _norm(row.get("horizon"))
    if horizon.startswith("OHLC-GTOS-PATH-TARGETSTOP-"):
        return horizon
    return ""


def _entry_variant(row: dict[str, Any], detail: dict[str, Any]) -> str:
    for key in ("entry_variant", "family"):
        value = _upper(detail.get(key)) or _upper(row.get(key))
        if value in ENTRY_VARIANTS:
            return value
    return ""


def _scope_from_payload(payload: dict[str, Any]) -> dict[str, str]:
    required = (
        _norm(payload.get("symbol")),
        _norm(payload.get("route_session")),
        _norm(payload.get("side")),
    )
    if not all(required):
        return {}
    return {
        key: _norm(payload.get(key))
        for key in (
            "symbol",
            "source_symbol",
            "market",
            "market_timeframe",
            "route_session",
            "route_family",
            "primitive",
            "side",
            "source_component",
            "entry_variant",
            "target_stop_order_class",
        )
        if _norm(payload.get(key))
    }


def _decision_from_tick(row: dict[str, Any]) -> dict[str, str]:
    family = _upper(row.get("family"))
    if family.endswith("_FOLLOW"):
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_unified_tick_m15_path_follow",
            "source_role": "main_orch24_unified_tick_m15_path_follow",
            "action_class": "main_orch24_unified_tick_m15_path_follow",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_TICK_M15_PATH_FOLLOW_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
            "system_surface": "execution_adjacent_unified_tick_m15_path_follow",
        }
    if family.endswith("_INVERSE"):
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_unified_tick_m15_path_inverse_avoid",
            "source_role": "main_orch24_unified_tick_m15_path_inverse_guard",
            "action_class": "main_orch24_unified_tick_m15_path_inverse_avoid",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_TICK_M15_PATH_INVERSE_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
            "system_surface": "execution_adjacent_unified_tick_m15_path_inverse_avoid",
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_unified_tick_m15_path_context",
        "source_role": "main_orch24_unified_tick_m15_path_context",
        "action_class": "main_orch24_unified_tick_m15_path_context",
        "r_evidence_class": "MAIN_ORCH24_UNIFIED_TICK_M15_PATH_CONTEXT",
        "proxy_r_class": "MIXED_PROXY_R",
        "system_surface": "execution_adjacent_unified_tick_m15_path_context",
    }


def _status_blob(row: dict[str, Any]) -> str:
    values: list[str] = []
    for key in (
        "m1_first_touch_status",
        "m1_replay_path_status",
        "target_stop_result",
        "branch_result_class",
        "branch_queue_status",
        "ambiguity_status",
        "fillability_bucket",
        "source_confidence_status",
        "exact_failure_cause",
        "exact_success_cause",
    ):
        values.append(_upper(row.get(key)))
    tags = row.get("system_implication_tags") or row.get("cause_tags") or []
    if isinstance(tags, list):
        values.extend(_upper(item) for item in tags)
    return " ".join(item for item in values if item)


def _decision_from_m1(row: dict[str, Any], detail: dict[str, Any]) -> dict[str, str]:
    if _upper(row.get("evidence_class")).endswith("FILL_REPLAY_ENTRY"):
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_unified_m1_entry_materialized_context",
            "source_role": "main_orch24_unified_m1_entry_materialized_context",
            "action_class": "main_orch24_unified_m1_entry_materialized_context",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_M1_ENTRY_MATERIALIZED_CONTEXT",
            "proxy_r_class": "MIXED_PROXY_R",
            "system_surface": "execution_adjacent_unified_m1_entry_materialized_context",
        }
    blob = _status_blob(detail) or _status_blob(row)
    if any(token in blob for token in TARGET_TOKENS) and "AMBIGUOUS" not in blob:
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_unified_m1_spread_fill_target_follow",
            "source_role": "main_orch24_unified_m1_spread_fill_target_follow",
            "action_class": "main_orch24_unified_m1_spread_fill_target_follow",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_M1_SPREAD_FILL_TARGET_FIRST_PROXY",
            "proxy_r_class": "POSITIVE_PROXY_R",
            "system_surface": "execution_adjacent_unified_m1_spread_fill_target_follow",
        }
    if any(token in blob for token in STOP_TOKENS) or any(token in blob for token in NOFILL_TOKENS):
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
            "source_role": "main_orch24_unified_m1_spread_fill_stop_or_nofill_guard",
            "action_class": "main_orch24_unified_m1_spread_fill_stop_or_nofill_avoid",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_M1_SPREAD_FILL_STOP_OR_NOFILL_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
            "system_surface": "execution_adjacent_unified_m1_spread_fill_stop_or_nofill_avoid",
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_unified_m1_fill_ordering_source_repair",
        "source_role": "main_orch24_unified_m1_fill_ordering_source_repair_guard",
        "action_class": "main_orch24_unified_m1_fill_ordering_source_repair",
        "r_evidence_class": "MAIN_ORCH24_UNIFIED_M1_FILL_ORDERING_SOURCE_REPAIR_REQUIRED",
        "proxy_r_class": "MIXED_PROXY_R",
        "system_surface": "execution_adjacent_unified_m1_fill_ordering_source_repair",
    }


def _decision_from_branch(detail: dict[str, Any]) -> dict[str, str]:
    blob = _status_blob(detail)
    target_first = _upper(detail.get("target_stop_result")) == "TARGET_FIRST_PROXY_DOMINANT"
    stop_first = _upper(detail.get("target_stop_result")) == "STOP_FIRST_PROXY_DOMINANT"
    positive = "POSITIVE_RSTYLE_PROXY_MIDPOINT" in blob or target_first
    negative = "NEGATIVE_RSTYLE_PROXY_MIDPOINT" in blob or stop_first
    ambiguous = any(token in blob for token in AMBIGUOUS_TOKENS)
    nofill = any(token in blob for token in NOFILL_TOKENS)
    if positive and not ambiguous:
        return {
            "review_action": "FOLLOW",
            "source_component": "main_orch24_unified_branch_proxy_follow",
            "source_role": "main_orch24_unified_branch_proxy_follow",
            "action_class": "main_orch24_unified_branch_proxy_follow",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_BRANCH_PROXY_POSITIVE",
            "proxy_r_class": "POSITIVE_PROXY_R",
            "system_surface": "execution_adjacent_unified_branch_proxy_follow",
        }
    if negative or nofill:
        return {
            "review_action": "AVOID",
            "source_component": "main_orch24_unified_branch_proxy_avoid",
            "source_role": "main_orch24_unified_branch_proxy_avoid_guard",
            "action_class": "main_orch24_unified_branch_proxy_avoid",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_BRANCH_PROXY_AVOID",
            "proxy_r_class": "NEGATIVE_PROXY_R",
            "system_surface": "execution_adjacent_unified_branch_proxy_avoid",
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_unified_branch_proxy_source_repair",
        "source_role": "main_orch24_unified_branch_proxy_source_repair_guard",
        "action_class": "main_orch24_unified_branch_proxy_source_repair",
        "r_evidence_class": "MAIN_ORCH24_UNIFIED_BRANCH_PROXY_SOURCE_REPAIR_REQUIRED",
        "proxy_r_class": "MIXED_PROXY_R",
        "system_surface": "execution_adjacent_unified_branch_proxy_source_repair",
    }


def _decision(row: dict[str, Any], detail: dict[str, Any]) -> dict[str, str]:
    evidence_class = _upper(row.get("evidence_class"))
    if evidence_class == "TICK_M15_ENTRY_PATH_GEOMETRY_PROXY":
        return _decision_from_tick(row)
    if "M1_SPREAD_ADJUSTED_FILL_REPLAY" in evidence_class:
        return _decision_from_m1(row, detail)
    if "BRANCH_RSTYLE_PROXY_OUTCOME_LAYER" in evidence_class or "COST_FILL_PATH_BRANCH_PROXY_SCORING" in evidence_class:
        return _decision_from_branch(detail)
    if evidence_class == "G12_READY8_R11_TRADE_GEOMETRY_SOURCE_CAPTURE_REPAIR_PACKET_AUDIT_ONLY":
        return {
            "review_action": "MIXED",
            "source_component": "main_orch24_unified_ready8_source_capture_repair_replay",
            "source_role": "main_orch24_unified_ready8_source_capture_repair_replay",
            "action_class": "main_orch24_unified_ready8_source_capture_repair_replay",
            "r_evidence_class": "MAIN_ORCH24_UNIFIED_READY8_R11_SOURCE_CAPTURE_REPLAY_ONLY",
            "proxy_r_class": "MIXED_PROXY_R",
            "system_surface": "replay_attribution_unified_ready8_source_capture_repair",
        }
    return {
        "review_action": "MIXED",
        "source_component": "main_orch24_unified_candidate_context",
        "source_role": "main_orch24_unified_candidate_context",
        "action_class": "main_orch24_unified_candidate_context",
        "r_evidence_class": "MAIN_ORCH24_UNIFIED_CANDIDATE_CONTEXT",
        "proxy_r_class": "MIXED_PROXY_R",
        "system_surface": "execution_adjacent_unified_candidate_context",
    }


def _r_metrics(decision: str, detail: dict[str, Any]) -> dict[str, dict[str, Any]]:
    metrics: dict[str, dict[str, Any]] = {"effective_n": _metric(1.0, "runtime_row")}
    rr = _num(detail.get("target_stop_reward_to_risk_ratio"))
    if decision == "FOLLOW":
        metrics["proxy_score"] = _metric(rr if rr is not None else 0.25, "path_proxy")
        metrics["stress_simulated_r"] = _metric(rr if rr is not None else 0.25, "path_proxy")
    elif decision == "AVOID":
        metrics["proxy_score"] = _metric(-1.0, "path_proxy")
        metrics["stress_simulated_r"] = _metric(-1.0, "path_proxy")
    else:
        midpoint = (
            (detail.get("expectancy_style_proxy") or {}).get("midpoint_mean")
            if isinstance(detail.get("expectancy_style_proxy"), dict)
            else None
        )
        if midpoint is not None:
            metrics["proxy_score"] = _metric(midpoint, "rstyle_proxy_midpoint")
        else:
            metrics["proxy_score"] = _metric(0.0, "mixed_or_source_repair_context")
    counts = detail.get("target_stop_result_counts")
    if isinstance(counts, dict):
        for key in (
            "target_first_rows",
            "stop_first_rows",
            "ambiguous_ordering_rows",
            "no_fill_or_unfilled_rows",
            "source_stress_rows",
        ):
            if key in counts:
                metrics[key] = _metric(counts[key], "target_stop_result_counts")
    return metrics


def _runtime_row(row: dict[str, Any], line_no: int) -> dict[str, Any]:
    source_file = _norm(row.get("source_file"))
    detail = _source_line(source_file, int(row.get("source_line_no") or 0))
    behavior = _decision(row, detail)
    route_symbol, route_session, primitive, horizon = _route_parts(detail, row)

    symbol = _norm(row.get("symbol")) or _norm(detail.get("symbol")) or route_symbol
    session = _norm(row.get("session")) or _norm(detail.get("route_session")) or route_session
    side = _norm(row.get("side")) or _norm(detail.get("side"))
    target_stop = _target_stop_class(row, detail)
    entry_variant = _entry_variant(row, detail)
    route_family = "main_orch24_unified_candidate_path_proxy"
    source_component = behavior["source_component"]
    action_class = behavior["action_class"]
    payload: dict[str, Any] = {
        "schema_version": "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime_row_v1",
        "runtime_row_id": f"MAIN_ORCH24_UNIFIED_PATH_PROXY_{line_no:05d}",
        "main_orch24_unified_candidate_path_proxy_runtime_row_id": (
            f"MAIN_ORCH24_UNIFIED_PATH_PROXY_{line_no:05d}"
        ),
        "batch_wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "source_artifact_path": _path_text(SOURCE_DIR / UNIFIED_CANDIDATE_LEDGER),
        "source_artifact_hash": "df156abfdb8df4f80e45f5e2957bd06b06130385",
        "source_artifact_hash_algorithm": "git_blob",
        "source_row_number": line_no,
        "source_file": source_file,
        "source_line_no": row.get("source_line_no"),
        "source_sha256": row.get("source_sha256"),
        "candidate_id": row.get("candidate_id"),
        "candidate_source": row.get("candidate_source"),
        "bucket": row.get("bucket"),
        "original_evidence_class": row.get("evidence_class"),
        "ready8_tagged": bool(row.get("ready8_tagged")),
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "market_timeframe": "M15" if symbol else "",
        "timeframe": "M15" if symbol else "",
        "route_session": session,
        "route_family": route_family,
        "primitive": primitive or _norm(row.get("family")),
        "horizon_id": _norm(row.get("horizon")) or horizon,
        "side": side,
        "entry_variant": entry_variant,
        "target_stop_order_class": target_stop,
        "source_component": source_component,
        "source_role": behavior["source_role"],
        "system_surface": behavior["system_surface"],
        "action_class": action_class,
        "review_action": behavior["review_action"],
        "decision": behavior["review_action"],
        "r_evidence_class": behavior["r_evidence_class"],
        "proxy_r_class": behavior["proxy_r_class"],
        "r_metrics": _r_metrics(behavior["review_action"], detail),
        "target_stop_result": _norm(detail.get("target_stop_result")),
        "m1_first_touch_status": _norm(detail.get("m1_first_touch_status")),
        "branch_result_class": _norm(detail.get("branch_result_class")),
        "ambiguity_status": _norm(detail.get("ambiguity_status")),
        "source_confidence_status": _norm(detail.get("source_confidence_status")),
        "claim_boundary": _norm(detail.get("claim_boundary")),
        "live_effect": False,
        "broker_effect": False,
        "candidate_use_allowed_now": behavior["review_action"] == "FOLLOW",
        "runtime_candidate_use_permitted": behavior["review_action"] == "FOLLOW",
    }
    scope = _scope_from_payload(payload)
    payload["event_scope"] = scope
    payload["source_bound"] = bool(scope)
    payload["source_complete"] = bool(scope) and behavior["review_action"] in {
        "FOLLOW",
        "AVOID",
    }
    if not scope:
        payload["candidate_use_allowed_now"] = False
        payload["runtime_candidate_use_permitted"] = False
    return {key: value for key, value in payload.items() if value not in ("", None)}


def _split_summary_runtime_row(row: dict[str, Any], line_no: int) -> dict[str, Any]:
    split_key = row.get("split_key") if isinstance(row.get("split_key"), dict) else {}
    symbol = _norm(split_key.get("symbol"))
    payload: dict[str, Any] = {
        "schema_version": "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime_row_v1",
        "runtime_row_id": f"MAIN_ORCH24_UNIFIED_SPLIT_SUMMARY_{line_no:05d}",
        "main_orch24_unified_candidate_path_proxy_runtime_row_id": (
            f"MAIN_ORCH24_UNIFIED_SPLIT_SUMMARY_{line_no:05d}"
        ),
        "batch_wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "source_name": SOURCE_NAME,
        "source_artifact_path": _path_text(SOURCE_DIR / SPLIT_SUMMARY_LEDGER),
        "source_artifact_hash": "8d7b9b0256bb693b43664305db30fece6b32c69c",
        "source_artifact_hash_algorithm": "git_blob",
        "source_row_number": line_no,
        "symbol": symbol,
        "source_symbol": symbol,
        "market": symbol,
        "symbol_family": resolve_vnext_symbol_family(symbol) if symbol else "",
        "route_family": "main_orch24_unified_candidate_path_proxy",
        "source_component": "main_orch24_unified_split_summary_replay_attribution",
        "source_role": "main_orch24_unified_split_summary_replay_attribution",
        "system_surface": "replay_attribution_unified_candidate_split_summary",
        "action_class": "main_orch24_unified_split_summary_replay_attribution",
        "review_action": "MIXED",
        "decision": "MIXED",
        "r_evidence_class": "MAIN_ORCH24_UNIFIED_SPLIT_SUMMARY_REPLAY_ATTRIBUTION_ONLY",
        "proxy_r_class": "MIXED_PROXY_R",
        "split_name": row.get("split_name"),
        "split_key": split_key,
        "source_row_count": row.get("row_count"),
        "exact_r_rows": row.get("exact_r_rows"),
        "proxy_r_rows": row.get("proxy_r_rows"),
        "result_status_counts": row.get("result_status_counts"),
        "proxy_r_summary": row.get("proxy_r_summary"),
        "r_metrics": {
            "effective_n": _metric(row.get("row_count") or 1, "split_summary_row_count"),
            "proxy_row_count": _metric(row.get("proxy_r_rows") or 0, "split_summary_proxy_rows"),
        },
        "event_scope": {},
        "source_bound": False,
        "source_complete": False,
        "live_effect": False,
        "broker_effect": False,
        "candidate_use_allowed_now": False,
        "runtime_candidate_use_permitted": False,
    }
    return {key: value for key, value in payload.items() if value not in ("", None)}


def build_runtime_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    unified_rows = _read_jsonl(SOURCE_DIR / UNIFIED_CANDIDATE_LEDGER)
    for line_no, row in enumerate(unified_rows, start=1):
        rows.append(_runtime_row(row, line_no))
    split_rows = _read_jsonl(SOURCE_DIR / SPLIT_SUMMARY_LEDGER)
    for line_no, row in enumerate(split_rows, start=1):
        rows.append(_split_summary_runtime_row(row, line_no))
    return rows


def _counter(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    return dict(
        sorted(
            Counter(_norm(row.get(field)) for row in rows if _norm(row.get(field))).items()
        )
    )


def _coverage(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    fields = {
        "symbols": "symbol",
        "markets": "market",
        "timeframes": "market_timeframe",
        "sessions": "route_session",
        "sides": "side",
        "entry_variants": "entry_variant",
        "target_stop_order_classes": "target_stop_order_class",
        "source_components": "source_component",
        "action_classes": "action_class",
        "r_evidence_classes": "r_evidence_class",
    }
    return {name: _counter(rows, field) for name, field in fields.items()}


def _blank_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    blanks: Counter[str] = Counter()
    for row in rows:
        for field in ANCHOR_FIELDS:
            if not _norm(row.get(field)):
                blanks[field] += 1
    return dict(sorted(blanks.items()))


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts: list[dict[str, Any]] = []
    for unit_id, name, digest in SOURCE_ARTIFACTS:
        path = SOURCE_DIR / name
        row_count = len(_read_jsonl(path)) if path.suffix == ".jsonl" else None
        source_artifacts.append(
            {
                "unit_id": unit_id,
                "name": name,
                "path": _path_text(path),
                "hash": digest,
                "hash_algorithm": "git_blob",
                "row_count": row_count,
                "runtime_rows_read": row_count,
            }
        )
    scope_rows = sum(1 for row in rows if row.get("event_scope"))
    return {
        "schema_version": "gtos_vnext_main_orch24_unified_candidate_path_proxy_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "evidence_family": EVIDENCE_FAMILY,
        "runtime_rows_path": _path_text(OUTPUT_ROWS),
        "runtime_summary_path": _path_text(OUTPUT_SUMMARY),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": len(rows),
        "selected_open_unit_count": len(SOURCE_ARTIFACTS),
        "row_count_unknown_unit_count": 0,
        "runtime_rows_with_event_scope": scope_rows,
        "runtime_rows_without_event_scope": len(rows) - scope_rows,
        "decision_counts": _counter(rows, "review_action"),
        "source_component_counts": _counter(rows, "source_component"),
        "action_class_counts": _counter(rows, "action_class"),
        "r_evidence_class_counts": _counter(rows, "r_evidence_class"),
        "proxy_r_class_counts": _counter(rows, "proxy_r_class"),
        "coverage_counts": _coverage(rows),
        "blank_anchor_counts": _blank_counts(rows),
        "source_artifacts": source_artifacts,
        "blank_anchor_policy": (
            "Rows without symbol/session/side event_scope are replay attribution only "
            "and cannot create broad route pressure."
        ),
    }


def write_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_ROWS.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    OUTPUT_SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def check_outputs(rows: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    if not OUTPUT_ROWS.exists() or not OUTPUT_SUMMARY.exists():
        raise SystemExit("runtime outputs are missing; run without --check first")
    expected_rows = "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n"
    actual_rows = OUTPUT_ROWS.read_text(encoding="utf-8")
    if actual_rows != expected_rows:
        raise SystemExit("runtime rows are stale")
    expected_summary = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    actual_summary = OUTPUT_SUMMARY.read_text(encoding="utf-8")
    if actual_summary != expected_summary:
        raise SystemExit("runtime summary is stale")
    print(
        json.dumps(
            {
                "status": "ok",
                "rows": len(rows),
                "rows_sha256": _sha256(OUTPUT_ROWS),
                "summary_sha256": _sha256(OUTPUT_SUMMARY),
            },
            sort_keys=True,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = build_runtime_rows()
    summary = build_summary(rows)
    if args.check:
        check_outputs(rows, summary)
    else:
        write_outputs(rows, summary)
        print(json.dumps({"status": "wrote", "rows": len(rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
