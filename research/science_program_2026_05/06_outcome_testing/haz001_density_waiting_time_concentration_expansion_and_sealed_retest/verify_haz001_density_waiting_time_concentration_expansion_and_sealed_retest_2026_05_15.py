#!/usr/bin/env python3
"""Verifier for the HAZ-001 mechanism expansion route."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
OUT_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-15"
ROUTE_ID = "HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST"
EVIDENCE_CLASS = "READY8_HAZ001_MECHANISM_EXPANSION_AND_QUARANTINED_RETEST_ONLY"

SAFE_FALSE_KEYS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "changes_trading_risk_safety_prompt_decision_behavior",
    "credentials_touched",
    "opens_ai_api",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_paid_or_vendor_access",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_strategy_edge_claims",
]

ARTIFACTS = {
    "context": OUT_DIR / f"HAZ001_CONTEXT_ANCHOR_AND_INPUT_BINDING_LEDGER_{DATE_ID}.json",
    "source_inventory": OUT_DIR / f"HAZ001_SOURCE_ROWSET_BRANCH_INVENTORY_LEDGER_{DATE_ID}.jsonl",
    "pass_control": OUT_DIR / f"HAZ001_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_{DATE_ID}.jsonl",
    "deconcentration": OUT_DIR / f"HAZ001_CONCENTRATION_DECONCENTRATION_LEDGER_{DATE_ID}.jsonl",
    "horizon_target": OUT_DIR / f"HAZ001_HORIZON_TARGET_FAMILY_ANATOMY_LEDGER_{DATE_ID}.jsonl",
    "interaction": OUT_DIR / f"HAZ001_INTERACTION_LEDGER_{DATE_ID}.jsonl",
    "failure": OUT_DIR / f"HAZ001_FAILURE_INVERSE_NULL_ANATOMY_LEDGER_{DATE_ID}.jsonl",
    "fail_closed": OUT_DIR / f"HAZ001_FAIL_CLOSED_SOURCE_REPAIR_SENSITIVITY_LEDGER_{DATE_ID}.jsonl",
    "source_search": OUT_DIR / f"HAZ001_SOURCE_SEARCH_ACQUISITION_LEDGER_{DATE_ID}.json",
    "retest_design": OUT_DIR / f"HAZ001_DECONCENTRATED_RETEST_DESIGN_LEDGER_{DATE_ID}.json",
    "retest_packet": OUT_DIR / f"HAZ001_DECONCENTRATED_RETEST_INPUT_PACKET_SOURCE_CONTROL_ONLY_{DATE_ID}.jsonl",
    "questions": OUT_DIR / f"HAZ001_QUESTION_AMBIGUITY_LEDGER_{DATE_ID}.jsonl",
    "saturation": OUT_DIR / f"HAZ001_SATURATION_SELF_RED_TEAM_LEDGER_{DATE_ID}.json",
    "completion": OUT_DIR / f"HAZ001_COMPLETION_AUDIT_{DATE_ID}.json",
    "manifest": OUT_DIR / f"HAZ001_OUTPUT_MANIFEST_{DATE_ID}.json",
    "synthesis": OUT_DIR / f"HAZ001_SYNTHESIS_{DATE_ID}.md",
    "starter": OUT_DIR / f"G12_HAZ001_DENSITY_WAITING_TIME_AUDIT_STARTER_{DATE_ID}.txt",
    "next_prompt": ROOT / f"research/science_program_2026_05/04_goal_prompts/G12_HAZ001_DENSITY_WAITING_TIME_CONCENTRATION_EXPANSION_AND_SEALED_RETEST_AUDIT_GOAL_PROMPT_{DATE_ID}.md",
}
RESULT_PATH = OUT_DIR / f"HAZ001_VERIFICATION_RESULT_{DATE_ID}.json"


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def utc_now() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path))


def safe_flags_closed(obj: dict[str, Any]) -> bool:
    return obj.get("promotion_verdict") == "NO_PROMOTION_VERDICT" and all(obj.get(key) is False for key in SAFE_FALSE_KEYS)


def main() -> int:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    for name, path in ARTIFACTS.items():
        checks[f"{name}_exists"] = path.exists()
        if not path.exists():
            issues.append(f"missing artifact: {rel(path)}")

    if issues:
        result = {
            "ok": False,
            "can_mark_goal_complete": False,
            "generated_at_utc": utc_now(),
            "route_id": ROUTE_ID,
            "evidence_class": EVIDENCE_CLASS,
            "issues": issues,
            "checks": checks,
        }
        RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, sort_keys=True))
        return 1

    context = load_json(ARTIFACTS["context"])
    completion = load_json(ARTIFACTS["completion"])
    retest_design = load_json(ARTIFACTS["retest_design"])
    source_search = load_json(ARTIFACTS["source_search"])
    saturation = load_json(ARTIFACTS["saturation"])
    manifest = load_json(ARTIFACTS["manifest"])

    checks["context_safe_flags_closed"] = safe_flags_closed(context)
    checks["completion_safe_flags_closed"] = safe_flags_closed(completion)
    checks["retest_design_safe_flags_closed"] = safe_flags_closed(retest_design)
    checks["source_search_safe_flags_closed"] = safe_flags_closed(source_search)
    checks["saturation_safe_flags_closed"] = safe_flags_closed(saturation)
    checks["manifest_safe_flags_closed"] = safe_flags_closed(manifest)
    checks["rowset_hash_matches_expected"] = context["input_bindings"].get("rowset_sha256_matches") is True
    checks["haz001_target_row_count_exact"] = context["counts"].get("haz001_target_rows") == 24112
    checks["haz001_rowset_count_exact"] = context["counts"].get("haz001_rowset_rows") == 3014
    checks["haz001_unique_duplicate_count_exact"] = context["counts"].get("haz001_unique_duplicate_denominator_keys") == 3014
    checks["haz001_computable_count_exact"] = context["counts"]["status_counts"].get("COMPUTABLE") == 20292
    checks["haz001_fail_closed_count_exact"] = context["counts"]["status_counts"].get("FAIL_CLOSED_NOT_COMPUTABLE") == 3820

    expected_counts = completion["output_counts"]
    count_key_by_artifact = {
        "source_inventory": "source_inventory_rows",
        "pass_control": "pass_control_rows",
        "deconcentration": "deconcentration_rows",
        "horizon_target": "horizon_target_rows",
        "interaction": "interaction_rows",
        "failure": "failure_rows",
        "fail_closed": "fail_closed_rows",
        "retest_packet": "retest_packet_rows",
        "questions": "question_rows",
    }
    for name, key in count_key_by_artifact.items():
        count = count_jsonl(ARTIFACTS[name])
        checks[f"{key}_matches_completion"] = count == expected_counts[key]
        if count != expected_counts[key]:
            issues.append(f"{key} count mismatch: {count} != {expected_counts[key]}")

    dims = set()
    labels = set()
    for row in iter_jsonl(ARTIFACTS["deconcentration"]):
        dims.add(row.get("deconcentration_dimension"))
        labels.add(row.get("survival_label"))
    checks["deconcentration_all_required_dimensions"] = dims == {"symbol", "canonical_economic_group", "session", "source_segment_sha256", "source_date", "source_window"}
    checks["deconcentration_has_survival_and_kill_labels"] = {"SURVIVES_LEAVE_ONE_POSITIVE", "KILLED_OR_REVERSED_BY_LEAVE_ONE"}.issubset(labels)
    checks["deconcentration_marks_non_evaluable_dimensions"] = "DIMENSION_NOT_EVALUABLE_SINGLE_VALUE_FULL_REMOVAL" in labels

    classifications = set()
    for row in iter_jsonl(ARTIFACTS["pass_control"]):
        classifications.add(row.get("comparison_classification"))
    checks["pass_control_has_positive_inverse_underpowered_or_neutral"] = any(c and c.startswith("POSITIVE") for c in classifications) and any(c and ("INVERSE" in c or "UNDERPOWERED" in c or "NEUTRAL" in c or "NOT_COMPARABLE" in c) for c in classifications)

    forbidden_retest_fields = {
        "close_to_close_percent_return",
        "close_to_close_absolute_delta",
        "upside_excursion_percent",
        "downside_excursion_percent",
        "target_result_row_id",
        "target_result_row_hash",
        "horizon_close",
        "horizon_end_utc",
        "entry_close",
        "terminal_status",
    }
    packet_rows = 0
    forbidden_seen = set()
    for row in iter_jsonl(ARTIFACTS["retest_packet"]):
        packet_rows += 1
        forbidden_seen.update(forbidden_retest_fields.intersection(row))
        if not safe_flags_closed(row):
            issues.append("retest packet row has open safe flag")
            break
    checks["retest_packet_rows_exact"] = packet_rows == 3014
    checks["retest_packet_source_control_only_no_target_fields"] = not forbidden_seen
    if forbidden_seen:
        issues.append(f"retest packet contains forbidden target/outcome fields: {sorted(forbidden_seen)}")

    checklist = completion["prompt_to_artifact_checklist"]
    checks["completion_checklist_all_true"] = all(checklist.values())
    checks["retest_design_emits_candidates"] = retest_design.get("eligible_deconcentrated_branch_count", 0) > 0
    checks["source_search_sierra_and_absolute_roots_searched"] = any(s["root"].startswith("C:\\SierraChart") and s["status"] == "SEARCHED" for s in source_search["searches"]) and any(s["root"].startswith("C:\\Users\\MSI\\Documents\\ai-trading-agent") and s["status"] == "SEARCHED" for s in source_search["searches"])
    checks["saturation_stop_condition_present"] = bool(saturation.get("completion_stop_condition"))
    checks["manifest_includes_verifier_and_focused_paths"] = any("HAZ001_VERIFICATION_RESULT" in a["path"] for a in manifest["artifacts"]) and any("HAZ001_FOCUSED_TEST_RESULT" in a["path"] for a in manifest["artifacts"])

    for key, ok in checks.items():
        if not ok:
            issues.append(f"check failed: {key}")

    result = {
        "schema_version": "haz001_density_waiting_time_expansion_verifier_v1",
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "generated_at_utc": utc_now(),
        "ok": not issues,
        "can_mark_goal_complete": not issues,
        "issues": issues,
        "checks": checks,
        "safe_flags": {
            "promotion_verdict": "NO_PROMOTION_VERDICT",
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "issues": issues}, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
