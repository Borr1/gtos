from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-18"
ROUTE_ID = "MAIN_ORCH48_GATE_EVIDENCE_SURFACE_INVENTORY"
SCHEMA_VERSION = "main_orch48_gate_evidence_surface_inventory_v1"
ROUTE_DIR = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
CONFIG_PATH = REPO / "config/agent_config.yaml"
TOUCH_COUNT_LOG = REPO / "shadow_logs/touch_count_gate_decisions.jsonl"
SL_BEYOND_LOG = REPO / "shadow_logs/sl_beyond_ob_decisions.jsonl"
CANDIDATE_FEATURES_LOG = REPO / "shadow_logs/candidate_features_log.jsonl"
CONFIDENCE_QUARANTINE_SUMMARY = ROUTE_DIR / "MAIN_ORCH48_CONFIDENCE_FILTER_QUARANTINE_SUMMARY_2026-05-18.json"
PERMISSIONS_SOURCE = REPO / "src/components/permissions.py"
ORCHESTRATOR_SOURCE = REPO / "src/components/orchestrator.py"
TOUCH_LOGGER_SOURCE = REPO / "src/components/touch_count_gate_logger.py"
SL_LOGGER_SOURCE = REPO / "src/components/sl_beyond_ob_shadow_logger.py"
RUNTIME_HALT_FLAG = REPO / "pipeline_state/RESEARCH_RUNTIME_HALT.flag"
OUTPUT_LEDGER = ROUTE_DIR / f"{ROUTE_ID}_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"{ROUTE_ID}_SUMMARY_{DATE}.json"
OUTPUT_MANIFEST = ROUTE_DIR / f"{ROUTE_ID}_MANIFEST_{DATE}.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def run_git_in_repo(*args: str) -> dict[str, Any]:
    result = subprocess.run(["git", *args], cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def time_bounds(rows: list[dict[str, Any]], key: str = "timestamp_utc") -> dict[str, str]:
    values = sorted(str(row.get(key) or "") for row in rows if row.get(key))
    return {
        "first_timestamp_utc": values[0] if values else "",
        "latest_timestamp_utc": values[-1] if values else "",
    }


def source_contains(path: Path, text: str) -> bool:
    return text in path.read_text(encoding="utf-8", errors="replace")


def log_source_summary(path: Path) -> dict[str, Any]:
    return {
        "path": display_path(path),
        "exists": path.exists(),
        "lines": count_lines(path),
        "bytes": path.stat().st_size if path.exists() else 0,
        "sha256": sha256_path(path) if path.exists() else "",
    }


def touch_count_row(config: dict[str, Any]) -> dict[str, Any]:
    rows = read_jsonl_rows(TOUCH_COUNT_LOG)
    threshold = ((config.get("gate1") or {}).get("touch_count_reject_threshold"))
    return {
        "gate_surface_row_id": "MAIN-ORCH48-GATE-EVIDENCE-SURFACE-0001",
        "schema_version": SCHEMA_VERSION,
        "gate_surface": "touch_count_gate",
        "source_component": "src/components/permissions.py::_reject_if_touch_count_too_high",
        "decision_log": log_source_summary(TOUCH_COUNT_LOG),
        "source_wiring_present": source_contains(PERMISSIONS_SOURCE, "log_touch_count_gate_decision("),
        "logger_failure_isolated": source_contains(TOUCH_LOGGER_SOURCE, "except Exception as exc"),
        "config_threshold": threshold,
        "decision_rows": len(rows),
        "decision_counts": dict(sorted(Counter(str(row.get("gate_decision") or "") for row in rows).items())),
        "symbols": sorted({str(row.get("symbol") or "") for row in rows if row.get("symbol")}),
        **time_bounds(rows),
        "capture_status": "EVIDENCE_PRESENT_READY_FOR_REVIEW" if rows else "CAPTURE_EMPTY_NEEDS_RUNTIME_ROWS",
        "recommended_next_action": "USE_EXISTING_PASS_REJECT_ROWS_FOR_KEEP_CHANGE_REVIEW_AFTER_POST_HALT_FRESHNESS_CHECK",
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


def sl_beyond_row(config: dict[str, Any]) -> dict[str, Any]:
    rows = read_jsonl_rows(SL_BEYOND_LOG)
    enabled = bool(((config.get("shadow_loggers") or {}).get("sl_beyond_ob_decisions_logger") or {}).get("enabled"))
    return {
        "gate_surface_row_id": "MAIN-ORCH48-GATE-EVIDENCE-SURFACE-0002",
        "schema_version": SCHEMA_VERSION,
        "gate_surface": "sl_beyond_ob_l2",
        "source_component": "src/components/verification.py::_check_sl_beyond_ob",
        "decision_log": log_source_summary(SL_BEYOND_LOG),
        "source_wiring_present": source_contains(REPO / "src/components/verification.py", "log_sl_beyond_ob_decision("),
        "logger_failure_isolated": source_contains(SL_LOGGER_SOURCE, "except Exception as exc"),
        "config_shadow_logger_enabled": enabled,
        "decision_rows": len(rows),
        "decision_counts": dict(sorted(Counter(str(row.get("l2_decision") or "") for row in rows).items())),
        "symbols": sorted({str(row.get("symbol") or "") for row in rows if row.get("symbol")}),
        **time_bounds(rows),
        "capture_status": (
            "EVIDENCE_PRESENT_AND_CAPTURE_ENABLED_POST_HALT" if rows and enabled else "CAPTURE_NOT_READY"
        ),
        "recommended_next_action": "COLLECT_FRESH_POST_HALT_ROWS_THEN_REVIEW_KEEP_CHANGE_OR_NARROW",
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


def pre_ai_row(config: dict[str, Any]) -> dict[str, Any]:
    rows = read_jsonl_rows(CANDIDATE_FEATURES_LOG)
    skip_rows = [row for row in rows if bool(row.get("pre_ai_gate_skipped"))]
    enabled = bool(((config.get("pre_ai_gates") or {}).get("h1_poi_availability_enabled")))
    return {
        "gate_surface_row_id": "MAIN-ORCH48-GATE-EVIDENCE-SURFACE-0003",
        "schema_version": SCHEMA_VERSION,
        "gate_surface": "pre_ai_h1_poi_availability",
        "source_component": "src/components/pre_ai_gates.py + src/components/candidate_features_logger.py",
        "decision_log": log_source_summary(CANDIDATE_FEATURES_LOG),
        "source_wiring_present": source_contains(ORCHESTRATOR_SOURCE, "pre_ai_gate_skipped=True"),
        "config_enabled": enabled,
        "decision_rows": len(rows),
        "pre_ai_gate_skipped_rows": len(skip_rows),
        "pre_ai_gate_reason_counts": dict(
            sorted(Counter(str(row.get("pre_ai_gate_reason") or "") for row in skip_rows).items())
        ),
        "symbols": sorted({str(row.get("symbol") or "") for row in skip_rows if row.get("symbol")}),
        **time_bounds(rows),
        "capture_status": "SKIP_EVIDENCE_PRESENT_READY_FOR_REVIEW" if skip_rows else "SKIP_EVIDENCE_EMPTY",
        "recommended_next_action": "USE_EXISTING_SKIP_ROWS_FOR_API_COST_AND_FALSE_SKIP_REVIEW",
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


def confidence_row() -> dict[str, Any]:
    summary = read_json(CONFIDENCE_QUARANTINE_SUMMARY)
    return {
        "gate_surface_row_id": "MAIN-ORCH48-GATE-EVIDENCE-SURFACE-0004",
        "schema_version": SCHEMA_VERSION,
        "gate_surface": "confidence_filter",
        "source_component": "src/components/orchestrator.py confidence_filter_mode",
        "decision_log": log_source_summary(CONFIDENCE_QUARANTINE_SUMMARY),
        "confidence_filter_mode": summary.get("confidence_filter_mode"),
        "b12_confidence_trades_evaluated": summary.get("b12_confidence_trades_evaluated"),
        "b12_confidence_family_size": summary.get("b12_confidence_family_size"),
        "b12_confidence_predictive_strata": summary.get("b12_confidence_predictive_strata"),
        "confidence_filter_active_branch_present": summary.get("confidence_filter_active_branch_present"),
        "capture_status": "QUARANTINED_NO_ACTIVE_PROMOTION",
        "recommended_next_action": "KEEP_SHADOW_UNLESS_FRESH_SEPARATE_VALIDATION_FINDS_PREDICTIVE_STRATA",
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


def cross_instrument_row(config: dict[str, Any]) -> dict[str, Any]:
    risk_cfg = config.get("risk") or {}
    dedicated_log = REPO / "shadow_logs/cross_instrument_correlation_decisions.jsonl"
    enabled = bool(risk_cfg.get("cross_instrument_correlation_enabled"))
    return {
        "gate_surface_row_id": "MAIN-ORCH48-GATE-EVIDENCE-SURFACE-0005",
        "schema_version": SCHEMA_VERSION,
        "gate_surface": "cross_instrument_correlation_gate",
        "source_component": "src/components/cross_instrument_correlation_gate.py",
        "decision_log": log_source_summary(dedicated_log),
        "source_wiring_present": source_contains(PERMISSIONS_SOURCE, "_reject_if_cross_instrument_correlation_excess")
        and source_contains(ORCHESTRATOR_SOURCE, "_evaluate_cross_instrument_correlation("),
        "config_enabled": enabled,
        "config_threshold": risk_cfg.get("cross_instrument_correlation_threshold"),
        "config_min_positions": risk_cfg.get("cross_instrument_correlation_min_positions"),
        "capture_status": "CAPTURE_GAP_DEDICATED_DECISION_LOG_MISSING",
        "recommended_next_action": "ADD_OBSERVATION_ONLY_DECISION_LOG_BEFORE_THRESHOLD_OR_ACTION_REVIEW",
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


def runtime_halt_row() -> dict[str, Any]:
    return {
        "gate_surface_row_id": "MAIN-ORCH48-GATE-EVIDENCE-SURFACE-0006",
        "schema_version": SCHEMA_VERSION,
        "gate_surface": "session_57_runtime_halt_boundary",
        "source_component": "pipeline_state/RESEARCH_RUNTIME_HALT.flag",
        "decision_log": log_source_summary(RUNTIME_HALT_FLAG),
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "capture_status": "RUNTIME_HALT_ACTIVE_NO_LIVE_COLLECTION_NOW",
        "recommended_next_action": "DO_NOT_RESTART_RUNTIME_OR_FORCE_FRESH_ROWS_DURING_HALT",
        "runtime_decision_effect": False,
        "production_change_opened_now": False,
        "broker_operation": False,
        "paid_api_or_vendor_call": False,
    }


def build() -> dict[str, Any]:
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    rows = [
        touch_count_row(config),
        sl_beyond_row(config),
        pre_ai_row(config),
        confidence_row(),
        cross_instrument_row(config),
        runtime_halt_row(),
    ]
    write_jsonl(OUTPUT_LEDGER, rows)

    status_counts = Counter(str(row.get("capture_status") or "") for row in rows)
    summary = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": utc_now(),
        "main_repo_head_at_build": run_git_in_repo("rev-parse", "HEAD"),
        "rows": len(rows),
        "gate_surface_counts": dict(sorted(Counter(str(row.get("gate_surface") or "") for row in rows).items())),
        "capture_status_counts": dict(sorted(status_counts.items())),
        "gate_surfaces_with_decision_rows": sum(int(row.get("decision_rows") or 0) > 0 for row in rows),
        "capture_gap_rows": sum("CAPTURE_GAP" in str(row.get("capture_status") or "") for row in rows),
        "runtime_halt_active": RUNTIME_HALT_FLAG.exists(),
        "implementation_effect": {
            "gate_evidence_inventory_materialized": True,
            "runtime_decision_effect": False,
            "production_change_opened_now": False,
            "runtime_candidate_use_permitted": False,
            "broker_operation": False,
            "paid_api_or_vendor_call": False,
            "live_runtime_restart_now": False,
        },
        "can_continue_to_next_system_conversion_plate": True,
    }
    write_json(OUTPUT_SUMMARY, summary)

    outputs = [OUTPUT_LEDGER, OUTPUT_SUMMARY]
    manifest = {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_utc": summary["generated_utc"],
        "outputs": [
            {
                "path": display_path(path),
                "bytes": path.stat().st_size,
                "lines": count_lines(path),
                "sha256": sha256_path(path),
            }
            for path in outputs
        ],
    }
    write_json(OUTPUT_MANIFEST, manifest)
    return {
        "ok": True,
        "route_id": ROUTE_ID,
        "rows": len(rows),
        "capture_gap_rows": summary["capture_gap_rows"],
        "runtime_halt_active": summary["runtime_halt_active"],
    }


if __name__ == "__main__":
    print(json.dumps(build(), sort_keys=True))
