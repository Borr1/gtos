#!/usr/bin/env python3
"""Build MAIN_ORCH48 AI narrowing default-off runtime rows."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "main_orchestrator_24h_full_stack_research_integration_materialization"
)
PROGRAM_CONTROL_DIR = REPO_ROOT / "research" / "program_control"
OUTPUT_DIR = (
    REPO_ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "gtos_vnext_research_to_runtime_builder"
)

DATE = "2026-05-18"
WAVE_ID = "WAVE_MAIN_ORCH48_AI_NARROWING_DEFAULT_OFF_RUNTIME"
OUTPUT_ROWS_PATH = (
    OUTPUT_DIR / f"GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_ROWS_{DATE}.jsonl"
)
OUTPUT_SUMMARY_PATH = (
    OUTPUT_DIR / f"GTOS_VNEXT_AI_NARROWING_DEFAULT_OFF_RUNTIME_SUMMARY_{DATE}.json"
)

PREFIXES = (
    "MAIN_ORCH48_AI_NARROWING_EVENT_ADAPTER_SPEC",
    "MAIN_ORCH48_AI_NARROWING_EVENT_FIELD_AVAILABILITY",
    "MAIN_ORCH48_AI_NARROWING_FORWARD_CAPTURE_CONTRACT",
    "MAIN_ORCH48_AI_NARROWING_INTEGRITY_GUARD",
    "MAIN_ORCH48_AI_NARROWING_POLICY",
    "MAIN_ORCH48_AI_NARROWING_POLICY_REGISTRY_SELF_CHECK",
    "MAIN_ORCH48_AI_NARROWING_POLICY_SHADOW_EVALUATION",
    "MAIN_ORCH48_AI_NARROWING_RUNTIME_CONFIG_GUARD",
)
SCRIPT_STEMS = (
    "main_orch48_ai_narrowing_event_adapter_spec",
    "main_orch48_ai_narrowing_event_field_availability",
    "main_orch48_ai_narrowing_forward_capture_contract",
    "main_orch48_ai_narrowing_integrity_guard",
    "main_orch48_ai_narrowing_policy",
    "main_orch48_ai_narrowing_policy_registry_self_check",
    "main_orch48_ai_narrowing_policy_shadow_evaluation",
    "main_orch48_ai_narrowing_runtime_config_guard",
)

SOURCE_PATHS = tuple(
    SOURCE_DIR / f"{prefix}_LEDGER_{DATE}.jsonl"
    for prefix in PREFIXES
)
SUPPORT_PATHS = (
    *tuple(
        SOURCE_DIR / f"build_{stem}_2026_05_18.py"
        for stem in SCRIPT_STEMS
    ),
    *tuple(
        SOURCE_DIR / f"verify_{stem}_2026_05_18.py"
        for stem in SCRIPT_STEMS
    ),
    *tuple(
        path
        for prefix in PREFIXES
        for path in (
            SOURCE_DIR / f"{prefix}_LEDGER_{DATE}.jsonl",
            SOURCE_DIR / f"{prefix}_MANIFEST_{DATE}.json",
            SOURCE_DIR / f"{prefix}_SUMMARY_{DATE}.json",
            SOURCE_DIR / f"{prefix}_VERIFY_RESULT_{DATE}.json",
        )
    ),
    PROGRAM_CONTROL_DIR / f"AI_NARROWING_POLICY_SHADOW_EVALUATIONS_{DATE}.json",
    PROGRAM_CONTROL_DIR / f"AI_NARROWING_POLICY_SHADOW_EVALUATIONS_{DATE}.md",
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
            "source_shape": "ai_narrowing_default_off",
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


def _source_row_id(row: dict[str, Any], path: Path, line_no: int) -> str:
    for key in (
        "ai_narrowing_policy_row_id",
        "ai_narrowing_runtime_guard_decision_row_id",
        "ai_narrowing_registry_eval_row_id",
        "adapter_spec_row_id",
        "field_availability_row_id",
        "contract_row_id",
        "route_row_id",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return f"{path.name}:{line_no}"


def _status(row: dict[str, Any]) -> str:
    for key in (
        "ai_narrowing_policy_status",
        "ai_narrowing_runtime_guard_decision_status",
        "ai_narrowing_registry_eval_status",
        "adapter_resolution",
        "field_availability_status",
        "event_adapter_status",
        "health_status",
        "check",
    ):
        value = _normalized(row.get(key))
        if value:
            return value
    return ""


def _source_role(path: Path) -> str:
    name = path.name
    if "EVENT_ADAPTER_SPEC" in name:
        return "ai_narrowing_event_adapter_spec"
    if "EVENT_FIELD_AVAILABILITY" in name:
        return "ai_narrowing_event_contract_gap"
    if "FORWARD_CAPTURE_CONTRACT" in name:
        return "ai_narrowing_forward_capture_contract"
    if "INTEGRITY_GUARD" in name:
        return "ai_narrowing_integrity_guard"
    if "POLICY_REGISTRY_SELF_CHECK" in name:
        return "ai_narrowing_policy_registry_self_check"
    if "POLICY_SHADOW_EVALUATION" in name:
        return "ai_narrowing_shadow_evaluation"
    if "RUNTIME_CONFIG_GUARD" in name:
        return "ai_narrowing_runtime_config_guard"
    return "ai_narrowing_policy_scope"


def _source_component(row: dict[str, Any], source_role: str) -> str:
    component = _normalized(row.get("source_component"))
    if component:
        return component
    if source_role in {
        "ai_narrowing_event_adapter_spec",
        "ai_narrowing_event_contract_gap",
        "ai_narrowing_forward_capture_contract",
        "ai_narrowing_integrity_guard",
        "ai_narrowing_runtime_config_guard",
    }:
        return "shadow_source_guard"
    return "default_off_application"


def _event_rows_represented(row: dict[str, Any]) -> int:
    for key in (
        "event_rows",
        "event_source_rows",
        "source_rows_scanned",
        "candidate_rows",
        "matched_policy_rows",
    ):
        value = row.get(key)
        if isinstance(value, int) and value > 0:
            return value
    return 1


def _bool_count(row: dict[str, Any], key: str) -> int:
    return 1 if bool(row.get(key)) else 0


def _runtime_rows() -> list[dict[str, Any]]:
    output_rows: list[dict[str, Any]] = []
    source_shas = {path: _sha256(path) for path in SOURCE_PATHS}
    for path in SOURCE_PATHS:
        source_rows = _read_jsonl(path)
        for line_no, row in enumerate(source_rows, start=1):
            source_row_id = _source_row_id(row, path, line_no)
            row_hash = _hash_text(f"{path.name}|{line_no}|{source_row_id}")[:24]
            row_id = f"ai_narrowing_default_off:{row_hash}"
            source_role = _source_role(path)
            source_component = _source_component(row, source_role)
            symbol = _normalized(row.get("symbol") or row.get("source_symbol"))
            source_symbol = _normalized(row.get("source_symbol") or symbol)
            route_session = _normalized(row.get("route_session"))
            side = _normalized(row.get("selected_side") or row.get("side"))
            market_timeframe = _normalized(row.get("market_timeframe") or row.get("timeframe"))
            represented = _event_rows_represented(row)
            output_rows.append(
                {
                    "ai_narrowing_default_off_runtime_row_id": row_id,
                    "row_key": row_id,
                    "source_row_id": source_row_id,
                    "schema_version": "gtos_vnext_ai_narrowing_default_off_runtime_v1",
                    "evidence_family": "gtos_vnext_ai_narrowing_default_off_runtime",
                    "source_name": "gtos_vnext_ai_narrowing_default_off_wave",
                    "source_group": "ai_narrowing_default_off",
                    "source_role": source_role,
                    "system_surface": "pre_ai_ai_narrowing_default_off",
                    "source_component": source_component,
                    "source_path": _repo_path(path),
                    "source_artifact": _repo_path(path),
                    "source_artifact_sha256": source_shas[path],
                    "source_line_no": line_no,
                    "source_symbol": source_symbol,
                    "symbol": symbol,
                    "market": symbol,
                    "route_session": route_session,
                    "session": route_session,
                    "side": side,
                    "timeframe": market_timeframe,
                    "market_timeframe": market_timeframe,
                    "horizon_id": _normalized(row.get("horizon_id")),
                    "primitive": "",
                    "entry_variant": "",
                    "route_family": "mechanical_ai_selector",
                    "target_stop_order_class": "",
                    "decision": "MIXED",
                    "review_action": "MIXED",
                    "action_class": "ai_narrowing_default_off_guard",
                    "runtime_effect_now": "ai_narrowing_default_off_guard",
                    "runtime_score_allowed": False,
                    "runtime_candidate_use_permitted": False,
                    "candidate_use_allowed_now": bool(row.get("candidate_use_allowed_now")),
                    "live_effect": False,
                    "validation_safe": False,
                    "r_evidence_class": "AI_NARROWING_DEFAULT_OFF_GUARD",
                    "source_repair_required": False,
                    "source_acquisition_required": False,
                    "status": _status(row),
                    "runtime_guard_decision_status": _normalized(
                        row.get("ai_narrowing_runtime_guard_decision_status")
                    ),
                    "source_ai_narrowing_policy_status": _normalized(
                        row.get("ai_narrowing_policy_status")
                    ),
                    "source_ai_narrowing_registry_eval_status": _normalized(
                        row.get("ai_narrowing_registry_eval_status")
                    ),
                    "field_availability_status": _normalized(
                        row.get("field_availability_status")
                    ),
                    "adapter_resolution": _normalized(row.get("adapter_resolution")),
                    "adapter_action": _normalized(row.get("adapter_action")),
                    "required_event_field": _normalized(row.get("required_event_field")),
                    "required_event_fields": row.get("required_event_fields") or row.get("required_fields") or [],
                    "missing_required_field_counts": row.get("missing_required_field_counts") or {},
                    "runtime_enablement_gate_failures": row.get("runtime_enablement_gate_failures") or [],
                    "runtime_enablement_gate_failure_count": row.get(
                        "runtime_enablement_gate_failure_count"
                    ),
                    "capacity_blocklist_required_before_ai_narrowing": bool(
                        row.get("capacity_blocklist_required_before_ai_narrowing")
                    ),
                    "ai_call_skip_allowed_now": bool(row.get("ai_call_skip_allowed_now")),
                    "live_ai_runtime_change_now": bool(row.get("live_ai_runtime_change_now")),
                    "live_selector_change_now": bool(row.get("live_selector_change_now")),
                    "runtime_halt_active": bool(row.get("runtime_halt_active")),
                    "runtime_eligible_after_all_gates": bool(
                        row.get("runtime_eligible_after_all_gates")
                    ),
                    "ai_narrowing_review_ready": bool(row.get("ai_narrowing_review_ready")),
                    "source_rows_represented": represented,
                    "source_event_rows": represented,
                    "r_metrics": {
                        "effective_n": _metric(represented, source_field="source_rows_represented"),
                        "ai_narrowing_review_ready": _metric(
                            _bool_count(row, "ai_narrowing_review_ready"),
                            source_field="ai_narrowing_review_ready",
                        ),
                        "capacity_blocklist_required": _metric(
                            _bool_count(row, "capacity_blocklist_required_before_ai_narrowing"),
                            source_field="capacity_blocklist_required_before_ai_narrowing",
                        ),
                        "runtime_enablement_gate_failure_count": _metric(
                            row.get("runtime_enablement_gate_failure_count"),
                            source_field="runtime_enablement_gate_failure_count",
                        ),
                    },
                    "row_type": "AI_NARROWING_DEFAULT_OFF_RUNTIME_ROW",
                }
            )
    return output_rows


def _counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = Counter(_normalized(row.get(field)) for row in rows)
    counts.pop("", None)
    return dict(sorted(counts.items()))


def _list_field_counts(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        values = row.get(field)
        if isinstance(values, list):
            for value in values:
                text = _normalized(value)
                if text:
                    counts[text] += 1
        elif isinstance(values, dict):
            for key, value in values.items():
                text = _normalized(key)
                if text and isinstance(value, int):
                    counts[text] += value
        elif _normalized(values):
            counts[_normalized(values)] += 1
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
        "entry_variant",
        "primitive",
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
    for path in SUPPORT_PATHS:
        artifacts.append(
            {
                "path": _repo_path(path),
                "rows": _line_count(path),
                "runtime_rows_read": runtime_by_path.get(_repo_path(path), 0),
                "sha256_or_git_blob": _sha256(path) if path.exists() else "",
                "suffix": path.suffix,
            }
        )
    return artifacts


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    source_artifacts = _source_artifacts(rows)
    return {
        "schema_version": "gtos_vnext_ai_narrowing_default_off_runtime_summary_v1",
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
        "status_counts": _counts(rows, "status"),
        "runtime_guard_decision_status_counts": _counts(rows, "runtime_guard_decision_status"),
        "source_ai_narrowing_policy_status_counts": _counts(rows, "source_ai_narrowing_policy_status"),
        "source_ai_narrowing_registry_eval_status_counts": _counts(
            rows,
            "source_ai_narrowing_registry_eval_status",
        ),
        "adapter_resolution_counts": _counts(rows, "adapter_resolution"),
        "adapter_action_counts": _counts(rows, "adapter_action"),
        "required_event_field_counts": _counts(rows, "required_event_field"),
        "missing_required_field_counts": _list_field_counts(rows, "missing_required_field_counts"),
        "runtime_enablement_gate_failure_counts": _list_field_counts(
            rows,
            "runtime_enablement_gate_failures",
        ),
        "capacity_blocklist_required_rows": sum(
            1 for row in rows if row.get("capacity_blocklist_required_before_ai_narrowing")
        ),
        "ai_call_skip_allowed_now_rows": sum(
            1 for row in rows if row.get("ai_call_skip_allowed_now")
        ),
        "runtime_candidate_use_permitted_rows": sum(
            1 for row in rows if row.get("runtime_candidate_use_permitted")
        ),
        "runtime_halt_active_rows": sum(
            1 for row in rows if row.get("runtime_halt_active")
        ),
        "runtime_eligible_after_all_gates_rows": sum(
            1 for row in rows if row.get("runtime_eligible_after_all_gates")
        ),
        "coverage_counts": {
            "symbols": _counts(rows, "symbol"),
            "markets": _counts(rows, "market"),
            "source_symbols": _counts(rows, "source_symbol"),
            "sessions": _counts(rows, "route_session"),
            "sides": _counts(rows, "side"),
            "timeframes": _counts(rows, "timeframe"),
            "market_timeframes": _counts(rows, "market_timeframe"),
            "horizons": _counts(rows, "horizon_id"),
            "source_components": _counts(rows, "source_component"),
            "entry_variants": _counts(rows, "entry_variant"),
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
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
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
