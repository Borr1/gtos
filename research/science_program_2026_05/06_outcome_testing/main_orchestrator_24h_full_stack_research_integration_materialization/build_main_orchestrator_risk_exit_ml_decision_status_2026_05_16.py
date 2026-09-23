from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-16"
ROUTE_ID = "MAIN_ORCHESTRATOR_24H_FULL_STACK_RESEARCH_INTEGRATION_AND_RESULT_MATERIALIZATION"
SAFE_FLAGS = {
    "NO_PROMOTION_VERDICT": True,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}


def find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from {start}")


REPO_ROOT = find_repo_root(Path(__file__).resolve())
ROUTE_DIR = Path(__file__).resolve().parent


def rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT)).replace("/", "\\")


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8", errors="replace") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if isinstance(row, dict):
                row["_line_no"] = line_no
                rows.append(row)
    return rows


def artifact_record(label: str, path: Path) -> dict[str, Any]:
    return {
        "label": label,
        "path": rel(path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else None,
        "sha256": sha256(path),
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def latest_legacy_decisions(path: Path) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    for row in read_jsonl(path):
        family = str(row.get("family") or "")
        if family:
            decisions[family] = row
    return decisions


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(Counter(str(row.get(key) or "MISSING") for row in rows))


def contains(path: Path, needle: str) -> bool:
    if not path.exists():
        return False
    return needle in path.read_text(encoding="utf-8", errors="replace")


def main() -> None:
    generated_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    legacy_ledger_path = ROUTE_DIR / f"MAIN_ORCH24_LEGACY_IMPLEMENTATION_DECISION_LEDGER_{DATE}.jsonl"
    lto017_path = REPO_ROOT / "research/program_control/LTO017_S79_SIDE_AWARE_RISK_CONTEXT_2026-05-05.json"
    lto021_path = REPO_ROOT / "research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json"
    lto023_path = REPO_ROOT / "research/program_control/LTO023_K55_ML_SHADOW_2026-05-05.json"
    followup_path = REPO_ROOT / "research/program_control/LIVE_SHADOW_FOLLOWUP_COVERAGE_AUDIT_2026-05-04.json"
    queue_state_path = REPO_ROOT / "research/program_control/LIMITATIONS_TO_OPPORTUNITIES_QUEUE_STATE_2026-05-05.json"
    agent_config_path = REPO_ROOT / "config/agent_config.yaml"
    redacted_account_path = REPO_ROOT / "config/profiles/redacted_account.yaml"
    be_logger_path = REPO_ROOT / "src/components/be_shadow_logger.py"
    partial_logger_path = REPO_ROOT / "src/components/partial_close_shadow_logger.py"
    time_in_trade_logger_path = REPO_ROOT / "src/components/time_in_trade_shadow_logger.py"
    portfolio_risk_path = REPO_ROOT / "src/components/portfolio_risk.py"
    exit_status_path = REPO_ROOT / "shadow_logs/exit_management_shadow_status.jsonl"
    s79_status_path = REPO_ROOT / "shadow_logs/s79_side_aware_risk_context.jsonl"
    ml_shadow_path = REPO_ROOT / "shadow_logs/ml_shadow_predictions.jsonl"
    time_in_trade_path = REPO_ROOT / "shadow_logs/time_in_trade.jsonl"
    partial_event_path = REPO_ROOT / "shadow_logs/partial_close_shadow_log.jsonl"
    be_event_path = REPO_ROOT / "shadow_logs/be_shadow_log.jsonl"

    legacy_decisions = latest_legacy_decisions(legacy_ledger_path)
    lto017 = read_json(lto017_path)
    lto021 = read_json(lto021_path)
    lto023 = read_json(lto023_path)
    exit_rows = read_jsonl(exit_status_path)
    s79_rows = read_jsonl(s79_status_path)
    ml_rows = read_jsonl(ml_shadow_path)
    time_rows = read_jsonl(time_in_trade_path)
    partial_rows = read_jsonl(partial_event_path)
    be_rows = read_jsonl(be_event_path)

    common_inputs = {
        "legacy_decision_ledger": sha256(legacy_ledger_path),
        "lto017_report": sha256(lto017_path),
        "lto021_report": sha256(lto021_path),
        "lto023_report": sha256(lto023_path),
        "live_shadow_followup_audit": sha256(followup_path),
        "queue_state": sha256(queue_state_path),
        "agent_config": sha256(agent_config_path),
        "redacted_account_profile": sha256(redacted_account_path),
        "be_shadow_logger": sha256(be_logger_path),
        "partial_close_shadow_logger": sha256(partial_logger_path),
        "time_in_trade_shadow_logger": sha256(time_in_trade_logger_path),
        "portfolio_risk": sha256(portfolio_risk_path),
        "exit_management_shadow_status": sha256(exit_status_path),
        "s79_side_aware_risk_context": sha256(s79_status_path),
        "ml_shadow_predictions": sha256(ml_shadow_path),
        "time_in_trade": sha256(time_in_trade_path),
        "partial_close_shadow_log": sha256(partial_event_path),
        "be_shadow_log": sha256(be_event_path),
    }

    side_aware_config_present = contains(agent_config_path, "side_aware_sizing:")
    redacted_account_s79_present = contains(redacted_account_path, "S79 risk policy raise")
    partial_shadow_logger_present = contains(partial_logger_path, "Variant C Partial Close Shadow Logger")
    be_shadow_logger_present = contains(be_logger_path, "BE (Break-Even) Shadow Logger")
    time_in_trade_logger_present = time_in_trade_logger_path.exists()
    dedicated_trailing_logger_present = any(
        path.name.lower().startswith("trailing") for path in (REPO_ROOT / "src/components").glob("*logger.py")
    )
    portfolio_vol_managed_present = contains(portfolio_risk_path, "vol_managed") or contains(agent_config_path, "vol_managed")

    exit_rolling = lto021.get("rolling_status", {})
    s79_rolling = lto017.get("rolling_status", {})
    k55_rolling = lto023.get("rolling_status", {})

    ledger_rows: list[dict[str, Any]] = [
        {
            "row_id": "MAIN-ORCH24-RISK-EXIT-ML-001",
            "family": "S79_SIDE_AWARE",
            "legacy_decision": legacy_decisions.get("S79_SIDE_AWARE", {}).get("decision"),
            "materialized_decision": "KEEP_SHIPPED_S79_AND_SIDE_AWARE_AS_CONTEXT_AND_RISK_POLICY_ONLY",
            "decision_status": "IMPLEMENTED_CONTEXT_CAPTURE_PRESENT_NO_NEW_LIVE_CHANGE",
            "rows_computed": lto017.get("counts", {}).get("rows_computed"),
            "candidate_context_rows": lto017.get("counts", {}).get("candidate_context_rows"),
            "actual_r_claim_allowed_rows": lto017.get("counts", {}).get("actual_r_claim_allowed_rows"),
            "ml_label_eligibility_counts": s79_rolling.get("ml_label_eligibility_counts", {}),
            "symbol_counts": s79_rolling.get("symbol_counts", {}),
            "config_evidence": {
                "side_aware_sizing_present": side_aware_config_present,
                "redacted_account_s79_profile_note_present": redacted_account_s79_present,
            },
            "next_action": "PRESERVE_AS_K55_RISK_POLICY_CONTEXT_AND_SAMPLE_WEIGHT_METADATA",
            "input_hashes": common_inputs,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-RISK-EXIT-ML-002",
            "family": "K54_K55",
            "legacy_decision": legacy_decisions.get("K54_K55", {}).get("decision"),
            "materialized_decision": "KILL_K54_SAME_COHORT_ITERATION_PRESERVE_K55_FEATURE_BUNDLE",
            "decision_status": "K55_FEATURE_BUNDLE_READY_OR_PARTIAL_MODEL_ARTIFACT_PENDING_INFERENCE_DISABLED",
            "rows_computed": lto023.get("counts", {}).get("rows_computed"),
            "prediction_computed_rows": lto023.get("counts", {}).get("prediction_computed_rows"),
            "inference_enabled_rows": lto023.get("counts", {}).get("inference_enabled_rows"),
            "feature_count_avg": k55_rolling.get("feature_count_avg"),
            "feature_count_min": k55_rolling.get("feature_count_min"),
            "feature_count_max": k55_rolling.get("feature_count_max"),
            "status_counts": k55_rolling.get("status_counts", {}),
            "model_artifact": lto023.get("model_artifact", {}),
            "source_counts": lto023.get("source_counts", {}),
            "next_action": "DO_NOT_REUSE_STALE_K54_ARTIFACTS; BUILD_K55_MODEL_ONLY_AFTER_ACCOUNT_HISTORY_LABEL_BUNDLE_OR_APPROVED_SHADOW_MODEL_ARTIFACT",
            "input_hashes": common_inputs,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-RISK-EXIT-ML-003",
            "family": "TRAILING_STOP_EXIT_VARIANT",
            "legacy_decision": legacy_decisions.get("TRAILING_STOP_EXIT_VARIANT", {}).get("decision"),
            "materialized_decision": "QUEUE_DEFAULT_OFF_SHADOW_SPEC_ONLY_DO_NOT_IMPLEMENT_LIVE_OR_DEFAULT_ON",
            "decision_status": "NO_DEDICATED_TRAILING_LOGGER_PRESENT; EXISTING_EXIT_STATUS_SUPPORTS_BE_PARTIAL_TIME_IN_TRADE_NO_EVENT_BOUNDARY",
            "dedicated_trailing_logger_present": dedicated_trailing_logger_present,
            "exit_status_rows": lto021.get("counts", {}).get("candidate_rows_considered"),
            "exit_event_rows_present": lto021.get("counts", {}).get("event_rows_present"),
            "time_in_trade_event_rows": len(time_rows),
            "be_event_rows": len(be_rows),
            "partial_close_event_rows": len(partial_rows),
            "be_shadow_logger_present": be_shadow_logger_present,
            "partial_shadow_logger_present": partial_shadow_logger_present,
            "time_in_trade_logger_present": time_in_trade_logger_present,
            "required_before_code": [
                "exact trailing trigger rule",
                "source-safe path/price cadence for post-entry updates",
                "default_off_config_knob",
                "shadow-only verifier proving no order modification calls",
            ],
            "next_action": "PRESERVE_AS_DEFAULT_OFF_SHADOW_QUEUE_ITEM_NOT_A_LIVE_SWITCH",
            "input_hashes": common_inputs,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-RISK-EXIT-ML-004",
            "family": "PARTIAL_CLOSE_EXPANSION",
            "legacy_decision": legacy_decisions.get("PARTIAL_CLOSE_EXPANSION", {}).get("decision"),
            "materialized_decision": "KILL_NEW_PARTIAL_VARIANT_EXPANSION_KEEP_EXISTING_VARIANT_C_SHADOW_ONLY",
            "decision_status": "EXISTING_VARIANT_C_SHADOW_LOGGER_PRESENT_BUT_CURRENT_ROWS_SHOW_NO_PARTIAL_TRIGGER_EVENTS",
            "partial_shadow_logger_present": partial_shadow_logger_present,
            "partial_close_event_rows": len(partial_rows),
            "partial_close_status_counts": exit_rolling.get("partial_close_shadow_status_counts", {}),
            "documented_no_event_code_counts": exit_rolling.get("documented_no_event_code_counts", {}),
            "next_action": "KEEP_VARIANT_C_OBSERVATION_ONLY; DO_NOT_QUEUE_NEW_PARTIAL_VARIANTS_FROM_CURRENT_DISK_EVIDENCE",
            "input_hashes": common_inputs,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-RISK-EXIT-ML-005",
            "family": "PORTFOLIO_VOL_MANAGED_SIZING",
            "legacy_decision": legacy_decisions.get("PORTFOLIO_VOL_MANAGED_SIZING", {}).get("decision"),
            "materialized_decision": "KILL_PORTFOLIO_WIDE_VOL_MANAGED_SIZING_PRESERVE_NAS100_DEFAULT_OFF_SHADOW_ONLY",
            "decision_status": "NO_PORTFOLIO_VOL_MANAGED_IMPLEMENTATION_OR_LIVE_CONFIG_PRESENT",
            "portfolio_vol_managed_present": portfolio_vol_managed_present,
            "portfolio_risk_file_present": portfolio_risk_path.exists(),
            "next_action": "DO_NOT_CHANGE_RISK_OR_CONFIG; PRESERVE_ONLY_AS_FUTURE_DEFAULT_OFF_NAS100_SHADOW_CANDIDATE_IF_SPECIFIED",
            "input_hashes": common_inputs,
            "safe_flags": SAFE_FLAGS,
        },
        {
            "row_id": "MAIN-ORCH24-RISK-EXIT-ML-006",
            "family": "EXIT_MANAGEMENT_STATUS",
            "legacy_decision": "MATERIALIZE_CURRENT_EXIT_STATUS_COUNTS",
            "materialized_decision": "PRESERVE_EXIT_MANAGEMENT_STATUS_AS_EVIDENCE_BOUNDARY_FOR_EXIT_VARIANTS",
            "decision_status": lto021.get("status"),
            "exit_rows_loaded": len(exit_rows),
            "candidate_rows_considered": lto021.get("counts", {}).get("candidate_rows_considered"),
            "event_rows_present": lto021.get("counts", {}).get("event_rows_present"),
            "no_event_documented": lto021.get("counts", {}).get("no_event_documented"),
            "exit_management_status_counts": exit_rolling.get("exit_management_status_counts", {}),
            "fill_state_counts": exit_rolling.get("fill_state_counts", {}),
            "next_action": "USE_AS_CURRENT BOUNDARY FOR TRAILING/PARTIAL/BE DECISIONS; DO NOT SYNTHESIZE TRIGGER OUTCOMES WITHOUT EVENT ROWS",
            "input_hashes": common_inputs,
            "safe_flags": SAFE_FLAGS,
        },
    ]

    summary = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "plate": "risk_exit_ml_decision_status",
        "decision_rows": len(ledger_rows),
        "s79_rows_computed": lto017.get("counts", {}).get("rows_computed"),
        "s79_actual_r_claim_allowed_rows": lto017.get("counts", {}).get("actual_r_claim_allowed_rows"),
        "k55_rows_computed": lto023.get("counts", {}).get("rows_computed"),
        "k55_prediction_computed_rows": lto023.get("counts", {}).get("prediction_computed_rows"),
        "k55_model_artifact_status": lto023.get("model_artifact", {}).get("status"),
        "exit_candidate_rows_considered": lto021.get("counts", {}).get("candidate_rows_considered"),
        "exit_event_rows_present": lto021.get("counts", {}).get("event_rows_present"),
        "exit_no_event_documented": lto021.get("counts", {}).get("no_event_documented"),
        "time_in_trade_event_rows": len(time_rows),
        "partial_close_event_rows": len(partial_rows),
        "be_event_rows": len(be_rows),
        "dedicated_trailing_logger_present": dedicated_trailing_logger_present,
        "portfolio_vol_managed_present": portfolio_vol_managed_present,
        "decisions_by_family": {row["family"]: row["materialized_decision"] for row in ledger_rows},
        "safe_flags": SAFE_FLAGS,
    }

    ledger_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_LEDGER_{DATE}.jsonl"
    summary_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_SUMMARY_{DATE}.json"
    manifest_path = ROUTE_DIR / f"MAIN_ORCH24_RISK_EXIT_ML_DECISION_STATUS_OUTPUT_MANIFEST_{DATE}.json"

    write_jsonl(ledger_path, ledger_rows)
    write_json(summary_path, summary)

    manifest = {
        "route_id": ROUTE_ID,
        "generated_utc": generated_utc,
        "artifact_count": 2,
        "artifacts": [
            artifact_record("decision_status_ledger", ledger_path),
            artifact_record("summary", summary_path),
        ],
        "input_artifacts": [
            artifact_record("legacy_decision_ledger", legacy_ledger_path),
            artifact_record("lto017_s79_side_aware_report", lto017_path),
            artifact_record("lto021_exit_management_report", lto021_path),
            artifact_record("lto023_k55_report", lto023_path),
            artifact_record("live_shadow_followup_coverage_audit", followup_path),
            artifact_record("limitations_to_opportunities_queue_state", queue_state_path),
            artifact_record("agent_config", agent_config_path),
            artifact_record("redacted_account_profile", redacted_account_path),
            artifact_record("be_shadow_logger", be_logger_path),
            artifact_record("partial_close_shadow_logger", partial_logger_path),
            artifact_record("time_in_trade_shadow_logger", time_in_trade_logger_path),
            artifact_record("portfolio_risk", portfolio_risk_path),
            artifact_record("exit_management_shadow_status", exit_status_path),
            artifact_record("s79_side_aware_risk_context", s79_status_path),
            artifact_record("ml_shadow_predictions", ml_shadow_path),
            artifact_record("time_in_trade", time_in_trade_path),
            artifact_record("partial_close_shadow_log", partial_event_path),
            artifact_record("be_shadow_log", be_event_path),
        ],
        "safe_flags": SAFE_FLAGS,
    }
    write_json(manifest_path, manifest)

    print(json.dumps({"ok": True, "ledger_rows": len(ledger_rows), "manifest": rel(manifest_path)}, sort_keys=True))


if __name__ == "__main__":
    main()
