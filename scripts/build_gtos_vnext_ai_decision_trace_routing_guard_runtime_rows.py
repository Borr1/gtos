#!/usr/bin/env python3
"""Build AI decision trace routing-guard runtime rows."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ROUTE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)
MAIN_ORCH48_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
PROGRAM_CONTROL_DIR = REPO_ROOT / "research" / "program_control"
GOAL_PROMPTS_DIR = (
    REPO_ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
)
DATE = "2026-05-18"
WAVE_ID = "WAVE_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME"
OUTPUT_ROWS_PATH = (
    ROUTE_DIR / f"GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY_PATH = (
    ROUTE_DIR / f"GTOS_VNEXT_AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_SUMMARY_{DATE}.json"
)

ARCHITECTURE_LEDGER = ROUTE_DIR / f"GTOS_VNEXT_AI_DECISION_ARCHITECTURE_LEDGER_{DATE}.jsonl"
ARCHITECTURE_AUDIT_LEDGER = (
    MAIN_ORCH48_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_LEDGER_{DATE}.jsonl"
)
TRACE_INTEGRITY_LEDGER = (
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_INTEGRITY_GUARD_LEDGER_{DATE}.jsonl"
)
TRACE_PROVENANCE_LEDGER = (
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE_LEDGER_{DATE}.jsonl"
)
TRACE_BACKFILL_LEDGER = (
    MAIN_ORCH48_DIR / f"MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_LEDGER_{DATE}.jsonl"
)
READINESS_JSON = PROGRAM_CONTROL_DIR / "AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.json"

SOURCE_PATHS = (
    ARCHITECTURE_LEDGER,
    ARCHITECTURE_AUDIT_LEDGER,
    TRACE_INTEGRITY_LEDGER,
    TRACE_PROVENANCE_LEDGER,
    TRACE_BACKFILL_LEDGER,
    READINESS_JSON,
)
SUPPORT_PATHS = (
    REPO_ROOT / "research" / "academic_pipeline" / "phase1_llm_financial_reasoning_q9_1_v1.md",
    REPO_ROOT / "research" / "academic_pipeline" / "phase1_llm_vs_statistical_model_v1.md",
    REPO_ROOT / "research" / "ml_program" / "literature" / "_specs" / "20_rl_llms_in_trading.md",
    READINESS_JSON,
    PROGRAM_CONTROL_DIR / "AI_DECISION_LAYER_SHADOW_READINESS_2026-05-04.md",
    GOAL_PROMPTS_DIR
    / "MAIN_ORCHESTRATOR_48H_RESEARCH_TO_SYSTEM_COMPILER_AND_AI_DECISION_ARCHITECTURE_GOAL_PROMPT_2026-05-18.md",
    GOAL_PROMPTS_DIR
    / "MAIN_ORCHESTRATOR_48H_RESEARCH_TO_SYSTEM_COMPILER_AND_AI_DECISION_ARCHITECTURE_STARTER_2026-05-18.txt",
    ARCHITECTURE_LEDGER,
    MAIN_ORCH48_DIR / "build_main_orch48_ai_decision_architecture_audit_2026_05_18.py",
    MAIN_ORCH48_DIR / "build_main_orch48_ai_decision_trace_integrity_guard_2026_05_18.py",
    MAIN_ORCH48_DIR / "build_main_orch48_ai_decision_trace_provenance_2026_05_18.py",
    MAIN_ORCH48_DIR / "build_main_orch48_ai_trace_trade_record_backfill_2026_05_18.py",
    ARCHITECTURE_AUDIT_LEDGER,
    MAIN_ORCH48_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_MANIFEST_{DATE}.json",
    MAIN_ORCH48_DIR / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_SUMMARY_{DATE}.json",
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_ARCHITECTURE_AUDIT_VERIFY_RESULT_{DATE}.json",
    TRACE_INTEGRITY_LEDGER,
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_INTEGRITY_GUARD_MANIFEST_{DATE}.json",
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_INTEGRITY_GUARD_SUMMARY_{DATE}.json",
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_INTEGRITY_GUARD_VERIFY_RESULT_{DATE}.json",
    TRACE_PROVENANCE_LEDGER,
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE_MANIFEST_{DATE}.json",
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE_SUMMARY_{DATE}.json",
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_DECISION_TRACE_PROVENANCE_VERIFY_RESULT_{DATE}.json",
    TRACE_BACKFILL_LEDGER,
    MAIN_ORCH48_DIR / f"MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_MANIFEST_{DATE}.json",
    MAIN_ORCH48_DIR / f"MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_SUMMARY_{DATE}.json",
    MAIN_ORCH48_DIR
    / f"MAIN_ORCH48_AI_TRACE_TRADE_RECORD_BACKFILL_VERIFY_RESULT_{DATE}.json",
    MAIN_ORCH48_DIR / "verify_main_orch48_ai_decision_architecture_audit_2026_05_18.py",
    MAIN_ORCH48_DIR
    / "verify_main_orch48_ai_decision_trace_integrity_guard_2026_05_18.py",
    MAIN_ORCH48_DIR / "verify_main_orch48_ai_decision_trace_provenance_2026_05_18.py",
    MAIN_ORCH48_DIR / "verify_main_orch48_ai_trace_trade_record_backfill_2026_05_18.py",
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8", errors="replace") as fh:
        return sum(1 for _ in fh)


def _repo_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _normalized(value: Any) -> str:
    if value in (None, "None"):
        return ""
    return str(value).strip()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _metric(value: float | int | None, *, source_field: str) -> dict[str, Any]:
    if isinstance(value, (int, float)):
        return {
            "count": 1,
            "max": float(value),
            "mean": float(value),
            "min": float(value),
            "negative_rows": 0,
            "positive_rows": 1 if value > 0 else 0,
            "source_field": source_field,
            "source_shape": "ai_decision_trace_routing_guard",
            "sum": float(value),
            "zero_rows": 1 if value == 0 else 0,
        }
    return {
        "count": 0,
        "max": None,
        "mean": None,
        "min": None,
        "negative_rows": 0,
        "positive_rows": 0,
        "source_field": source_field,
        "source_shape": "missing",
        "sum": None,
        "zero_rows": 0,
    }


def _bool_metric(row: dict[str, Any], key: str) -> dict[str, Any]:
    return _metric(1 if bool(row.get(key)) else 0, source_field=key)


def _canonical_session(raw: str) -> str:
    text = _normalized(raw).casefold()
    return {
        "london": "london_core",
        "ldn": "london_core",
        "london_core": "london_core",
        "ny": "ny_core",
        "new_york": "ny_core",
        "ny_core": "ny_core",
        "tokyo": "tokyo_kz",
        "asia": "tokyo_kz",
        "tokyo_kz": "tokyo_kz",
        "off_core_session": "off_core_session",
        "all_sessions": "ALL_SESSIONS",
        "ALL_SESSIONS": "ALL_SESSIONS",
    }.get(text, raw)


def _derive_session(row: dict[str, Any]) -> str:
    for key in ("route_session", "session"):
        if value := _normalized(row.get(key)):
            return _canonical_session(value)
    for key in ("trade_id", "source_path"):
        value = _normalized(row.get(key))
        if not value:
            continue
        match = re.search(r"_(london|ny|tokyo)_", value.casefold())
        if match:
            return _canonical_session(match.group(1))
    return ""


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for key in (
        "vnext_matrix_row_id",
        "ai_architecture_audit_row_id",
        "ai_decision_trace_integrity_guard_row_id",
        "ai_decision_trace_provenance_row_id",
        "row_key",
        "trade_id",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return f"{path.name}:{line_no}"


def _source_role(path: Path) -> str:
    name = path.name
    if name == ARCHITECTURE_LEDGER.name:
        return "ai_decision_architecture_policy"
    if name == ARCHITECTURE_AUDIT_LEDGER.name:
        return "ai_decision_architecture_audit"
    if name == TRACE_INTEGRITY_LEDGER.name:
        return "ai_decision_trace_integrity_guard"
    if name == TRACE_PROVENANCE_LEDGER.name:
        return "ai_decision_trace_provenance"
    if name == TRACE_BACKFILL_LEDGER.name:
        return "ai_trace_trade_record_backfill"
    if name == READINESS_JSON.name:
        return "ai_decision_layer_shadow_readiness"
    return "ai_decision_trace_support"


def _source_component(row: dict[str, Any], source_role: str) -> str:
    if component := _normalized(row.get("source_component")):
        return component
    return {
        "ai_decision_architecture_policy": "shadow_source_guard",
        "ai_decision_architecture_audit": "ai_architecture_audit",
        "ai_decision_trace_integrity_guard": "ai_trace_integrity_guard",
        "ai_decision_trace_provenance": "ai_trace_provenance",
        "ai_trace_trade_record_backfill": "ai_trace_trade_record_backfill",
        "ai_decision_layer_shadow_readiness": "ai_shadow_readiness",
    }.get(source_role, "ai_decision_trace_support")


def _framework_route_family(framework: str) -> str:
    if not framework:
        return "mechanical_ai_selector"
    return {
        "ob_retest": "ob_retest",
        "breaker_re_entry": "breaker_re_entry",
        "fvg_fill": "fvg_fill",
    }.get(framework, framework)


def _source_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".jsonl":
        return _read_jsonl(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [payload if isinstance(payload, dict) else {"payload": payload}]


def _runtime_row(path: Path, row: dict[str, Any], line_no: int) -> dict[str, Any]:
    source_role = _source_role(path)
    source_component = _source_component(row, source_role)
    source_row_id = _source_row_id(row, path, line_no)
    row_hash = _hash_text(f"{path.name}|{line_no}|{source_row_id}")[:24]
    row_id = f"ai_decision_trace_routing_guard:{row_hash}"
    symbol = _normalized(row.get("symbol") or row.get("source_symbol"))
    source_symbol = _normalized(row.get("source_symbol") or symbol)
    side = _normalized(row.get("side") or row.get("ai_direction"))
    route_session = _derive_session(row)
    framework = _normalized(row.get("framework") or row.get("ai_framework"))
    market_timeframe = _normalized(row.get("market_timeframe") or row.get("timeframe"))
    if source_role == "ai_trace_trade_record_backfill" and not market_timeframe:
        market_timeframe = "M15"
    horizon_id = _normalized(row.get("horizon_id"))
    source_action = _normalized(
        row.get("implementation_action")
        or row.get("ai_architecture_action")
        or row.get("action_class")
        or row.get("ai_decision")
        or row.get("status")
    )
    boundary = row.get("research_boundary") if isinstance(row.get("research_boundary"), dict) else {}
    controls = (
        row.get("research_boundary_controls")
        if isinstance(row.get("research_boundary_controls"), dict)
        else {}
    )
    prompt_fingerprint = (
        row.get("prompt_fingerprint")
        if isinstance(row.get("prompt_fingerprint"), dict)
        else {}
    )
    represented = int(row.get("source_rows_represented") or row.get("row_count") or 1)
    output = {
        "ai_decision_trace_routing_guard_runtime_row_id": row_id,
        "row_key": row_id,
        "source_row_id": source_row_id,
        "schema_version": "gtos_vnext_ai_decision_trace_routing_guard_runtime_v1",
        "evidence_family": "gtos_vnext_ai_decision_trace_routing_guard",
        "source_name": "gtos_vnext_ai_decision_trace_routing_guard_wave",
        "source_group": "ai_decision_trace_routing_guard",
        "source_role": source_role,
        "system_surface": "pre_ai_post_l2_ai_trace_routing_guard",
        "source_component": source_component,
        "source_path": _repo_path(path),
        "source_artifact": _repo_path(path),
        "source_artifact_sha256": _sha256(path),
        "source_line_no": line_no,
        "source_symbol": source_symbol,
        "symbol": symbol,
        "market": symbol,
        "route_session": route_session,
        "session": route_session,
        "side": side,
        "timeframe": market_timeframe,
        "market_timeframe": market_timeframe,
        "horizon_id": horizon_id,
        "framework": framework,
        "route_family": _normalized(row.get("route_family")) or _framework_route_family(framework),
        "target_stop_order_class": _normalized(row.get("target_stop_order_class")),
        "decision": "MIXED",
        "review_action": "MIXED",
        "action_class": "ai_decision_trace_routing_guard",
        "implementation_action": "AI_DECISION_TRACE_ROUTING_GUARD_DEFAULT_OFF_CONTEXT",
        "runtime_effect_now": "ai_trace_routing_guard_shadow_context",
        "runtime_score_allowed": False,
        "runtime_candidate_use_permitted": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "validation_safe": False,
        "r_evidence_class": "AI_DECISION_TRACE_ROUTING_GUARD",
        "source_repair_required": False,
        "source_acquisition_required": False,
        "source_ai_action": source_action,
        "activation_state": _normalized(row.get("activation_state")),
        "ai_decision": _normalized(row.get("ai_decision")),
        "ai_grade": _normalized(row.get("ai_grade")),
        "ai_confidence": row.get("ai_confidence"),
        "ai_response_length": row.get("ai_response_length"),
        "ai_response_sha256": _normalized(row.get("ai_response_sha256")),
        "model_used": _normalized(row.get("model_used")),
        "capture_status": _normalized(row.get("capture_status")),
        "final_outcome": _normalized(row.get("final_outcome")),
        "trade_id": _normalized(row.get("trade_id")),
        "trade_record_source_path": _normalized(row.get("source_path")) if source_role == "ai_trace_trade_record_backfill" else "",
        "prompt_bundle_sha256": _normalized(prompt_fingerprint.get("prompt_bundle_sha256")),
        "system_prompt_sha256": _normalized(prompt_fingerprint.get("system_prompt_sha256")),
        "user_message_sha256": _normalized(prompt_fingerprint.get("user_message_sha256")),
        "stores_full_prompt_or_response_text": bool(
            row.get("stores_full_prompt_or_response_text")
            or boundary.get("stores_full_prompt_or_response_text")
            or controls.get("stores_full_prompt_or_response_text")
        ),
        "broker_operation": bool(
            row.get("broker_operation")
            or boundary.get("broker_operation")
            or controls.get("broker_operation")
        ),
        "paid_api_or_vendor_call": bool(
            row.get("paid_api_or_vendor_call")
            or boundary.get("paid_api_or_vendor_call")
            or controls.get("paid_api_or_vendor_call")
        ),
        "runtime_trading_or_live_broker_effect": bool(
            boundary.get("runtime_trading_or_live_broker_effect")
            or controls.get("runtime_trading_or_live_broker_effect")
        ),
        "runtime_observability_effect_if_runtime_reenabled": bool(
            boundary.get("runtime_observability_effect_if_runtime_reenabled")
        ),
        "config_enabled": row.get("config_enabled"),
        "primary_analyzer_records_trace": row.get("primary_analyzer_records_trace"),
        "hash_only_schema_present": row.get("hash_only_schema_present"),
        "hash_only_self_check_passed": row.get("hash_only_self_check_passed"),
        "expected_response_status_present_rows": row.get(
            "expected_response_status_present_rows"
        ),
        "required_shadow_labels": row.get("required_shadow_labels") or [],
        "readiness_status": _normalized(row.get("status")),
        "promotion_verdict": _normalized(row.get("promotion_verdict")),
        "blocker_trigger": _normalized(row.get("blocker_trigger")),
        "source_rows_represented": represented,
        "source_event_rows": represented,
        "r_metrics": {
            "effective_n": _metric(represented, source_field="source_rows_represented"),
            "hash_only_trace_present": _bool_metric(row, "hash_only_schema_present"),
            "primary_analyzer_trace_wired": _bool_metric(
                row,
                "primary_analyzer_records_trace",
            ),
            "stores_full_text_violation": _metric(
                1 if bool(row.get("stores_full_prompt_or_response_text")) else 0,
                source_field="stores_full_prompt_or_response_text",
            ),
        },
        "row_type": "AI_DECISION_TRACE_ROUTING_GUARD_RUNTIME_ROW",
    }
    return output


def _runtime_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in SOURCE_PATHS:
        for line_no, row in enumerate(_source_rows(path), start=1):
            rows.append(_runtime_row(path, row, line_no))
    return rows


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_normalized(row.get(field)) for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _list_field_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(field)
        if isinstance(value, list):
            for item in value:
                text = _normalized(item)
                if text:
                    counts[text] += 1
        elif isinstance(value, dict):
            for key, item in value.items():
                numeric = item if isinstance(item, int) else 1
                text = _normalized(key)
                if text:
                    counts[text] += numeric
        elif _normalized(value):
            counts[_normalized(value)] += 1
    return dict(sorted(counts.items()))


def _blank_anchor_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    anchors = (
        "symbol",
        "source_symbol",
        "market",
        "route_session",
        "side",
        "timeframe",
        "market_timeframe",
        "horizon_id",
        "framework",
        "target_stop_order_class",
    )
    return {
        field: sum(1 for row in rows if _normalized(row.get(field)) == "")
        for field in anchors
        if sum(1 for row in rows if _normalized(row.get(field)) == "")
    }


def _source_artifacts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    runtime_by_path = Counter(row["source_path"] for row in rows)
    artifacts = []
    seen: set[str] = set()
    for path in SUPPORT_PATHS:
        rel = _repo_path(path)
        if rel in seen:
            continue
        seen.add(rel)
        artifacts.append(
            {
                "path": rel,
                "rows": _line_count(path),
                "runtime_rows_read": runtime_by_path.get(rel, 0),
                "sha256_or_git_blob": _sha256(path) if path.exists() else "",
                "suffix": path.suffix,
            }
        )
    return artifacts


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    return {
        "schema_version": "gtos_vnext_ai_decision_trace_routing_guard_runtime_summary_v1",
        "wave_id": WAVE_ID,
        "output_rows": _repo_path(OUTPUT_ROWS_PATH),
        "runtime_row_count": len(rows),
        "runtime_source_rows_represented": sum(
            int(row.get("source_rows_represented") or 0) for row in rows
        ),
        "wave_source_artifact_count": len(source_artifacts),
        "wave_source_rows_counted": sum(item["rows"] for item in source_artifacts),
        "decision_counts": _counts(rows, "decision"),
        "source_role_counts": _counts(rows, "source_role"),
        "source_component_counts": _counts(rows, "source_component"),
        "source_ai_action_counts": _counts(rows, "source_ai_action"),
        "activation_state_counts": _counts(rows, "activation_state"),
        "capture_status_counts": _counts(rows, "capture_status"),
        "final_outcome_counts": _counts(rows, "final_outcome"),
        "model_used_counts": _counts(rows, "model_used"),
        "stores_full_prompt_or_response_text_rows": sum(
            1 for row in rows if row.get("stores_full_prompt_or_response_text")
        ),
        "broker_operation_rows": sum(1 for row in rows if row.get("broker_operation")),
        "paid_api_or_vendor_call_rows": sum(
            1 for row in rows if row.get("paid_api_or_vendor_call")
        ),
        "runtime_trading_or_live_broker_effect_rows": sum(
            1 for row in rows if row.get("runtime_trading_or_live_broker_effect")
        ),
        "runtime_observability_effect_if_runtime_reenabled_rows": sum(
            1 for row in rows if row.get("runtime_observability_effect_if_runtime_reenabled")
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "candidate_use_allowed_now_rows": sum(
            1 for row in rows if row.get("candidate_use_allowed_now")
        ),
        "required_shadow_label_counts": _list_field_counts(rows, "required_shadow_labels"),
        "coverage_counts": {
            "symbols": _counts(rows, "symbol"),
            "markets": _counts(rows, "market"),
            "source_symbols": _counts(rows, "source_symbol"),
            "sessions": _counts(rows, "route_session"),
            "sides": _counts(rows, "side"),
            "timeframes": _counts(rows, "timeframe"),
            "market_timeframes": _counts(rows, "market_timeframe"),
            "horizons": _counts(rows, "horizon_id"),
            "frameworks": _counts(rows, "framework"),
            "source_components": _counts(rows, "source_component"),
            "target_stop_order_classes": _counts(rows, "target_stop_order_class"),
        },
        "blank_anchor_counts": _blank_anchor_counts(rows),
        "source_artifacts": source_artifacts,
    }


def build(*, check: bool = False) -> dict[str, Any]:
    rows = _runtime_rows()
    summary = _summary(rows)
    row_text = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    summary_text = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    if check:
        if not OUTPUT_ROWS_PATH.exists():
            raise SystemExit(f"missing output rows: {OUTPUT_ROWS_PATH}")
        if not OUTPUT_SUMMARY_PATH.exists():
            raise SystemExit(f"missing output summary: {OUTPUT_SUMMARY_PATH}")
        if OUTPUT_ROWS_PATH.read_text(encoding="utf-8") != row_text:
            raise SystemExit(f"stale output rows: {OUTPUT_ROWS_PATH}")
        if OUTPUT_SUMMARY_PATH.read_text(encoding="utf-8") != summary_text:
            raise SystemExit(f"stale output summary: {OUTPUT_SUMMARY_PATH}")
    else:
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_ROWS_PATH.write_text(row_text, encoding="utf-8")
        OUTPUT_SUMMARY_PATH.write_text(summary_text, encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(check=args.check), sort_keys=True))


if __name__ == "__main__":
    main()
