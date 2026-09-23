from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = ROOT / "research/science_program_2026_05/06_outcome_testing/unc004_source_confidence_mechanism_disentanglement"
DATE = "2026-05-15"
RESULT_PATH = ROUTE_DIR / f"UNC004_VERIFICATION_RESULT_{DATE}.json"

SAFE_FLAGS = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
}
FORBIDDEN_SURFACE_FLAGS = {
    "changes_trading_risk_safety_prompt_decision_behavior": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
}

REQUIRED_FILES = {
    "context_anchor": ROUTE_DIR / f"UNC004_CONTEXT_ANCHOR_{DATE}.json",
    "accepted_evidence_binding": ROUTE_DIR / f"UNC004_ACCEPTED_EVIDENCE_BINDING_LEDGER_{DATE}.json",
    "rowset_inventory": ROUTE_DIR / f"UNC004_ROWSET_DESCRIPTOR_SOURCE_FIELD_INVENTORY_{DATE}.json",
    "tier_distribution": ROUTE_DIR / f"UNC004_COMPLETENESS_TIER_DISTRIBUTION_LEDGER_{DATE}.jsonl",
    "pass_control_recompute": ROUTE_DIR / f"UNC004_PASS_CONTROL_DESCRIPTOR_RECOMPUTATION_LEDGER_{DATE}.jsonl",
    "matched_control": ROUTE_DIR / f"UNC004_MATCHED_CONTROL_ATTEMPT_LEDGER_{DATE}.jsonl",
    "leave_one_stress": ROUTE_DIR / f"UNC004_LEAVE_ONE_STRESS_LEDGER_{DATE}.jsonl",
    "fail_closed_anatomy": ROUTE_DIR / f"UNC004_FAIL_CLOSED_NONAPPLICABLE_ANATOMY_LEDGER_{DATE}.json",
    "duplicate_concentration": ROUTE_DIR / f"UNC004_DUPLICATE_EFFECTIVE_N_CONCENTRATION_LEDGER_{DATE}.jsonl",
    "interaction": ROUTE_DIR / f"UNC004_INTERACTION_LEDGER_{DATE}.jsonl",
    "source_search": ROUTE_DIR / f"UNC004_SOURCE_SEARCH_ACQUISITION_LADDER_{DATE}.json",
    "negative_inverse_neutral": ROUTE_DIR / f"UNC004_NEGATIVE_INVERSE_NEUTRAL_LEDGER_{DATE}.jsonl",
    "downstream_design": ROUTE_DIR / f"UNC004_DOWNSTREAM_CAPTURE_RETEST_DESIGN_{DATE}.json",
    "saturation": ROUTE_DIR / f"UNC004_SATURATION_SELF_RED_TEAM_LEDGER_{DATE}.json",
    "instruction_coverage": ROUTE_DIR / f"UNC004_INSTRUCTION_COVERAGE_LEDGER_{DATE}.json",
    "decision_ledger": ROUTE_DIR / f"UNC004_DECISION_LEDGER_{DATE}.json",
    "completion_audit": ROUTE_DIR / f"UNC004_COMPLETION_AUDIT_{DATE}.json",
    "synthesis": ROUTE_DIR / f"UNC004_SYNTHESIS_{DATE}.md",
    "output_manifest": ROUTE_DIR / f"UNC004_OUTPUT_MANIFEST_{DATE}.json",
    "next_g12_starter": ROUTE_DIR / f"G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_STARTER_{DATE}.txt",
}
NEXT_G12_PROMPT = ROOT / "research/science_program_2026_05/04_goal_prompts/G12_UNC004_SOURCE_CONFIDENCE_DISENTANGLEMENT_AUDIT_GOAL_PROMPT_2026-05-15.md"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def flag_check(obj: dict[str, Any]) -> bool:
    return all(obj.get(k) == v for k, v in SAFE_FLAGS.items()) and all(
        obj.get(k) == v for k, v in FORBIDDEN_SURFACE_FLAGS.items()
    )


def count_jsonl(path: Path) -> tuple[int, Counter[str], Counter[str]]:
    group_families: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    count = 0
    for row in iter_jsonl(path):
        count += 1
        if not flag_check(row):
            classifications["SAFE_FLAG_OR_FORBIDDEN_SURFACE_FAILURE"] += 1
        if row.get("group_family"):
            group_families[row["group_family"]] += 1
        if row.get("comparison_family"):
            group_families[row["comparison_family"]] += 1
        if row.get("comparison_classification"):
            classifications[row["comparison_classification"]] += 1
    return count, group_families, classifications


def main() -> int:
    issues: list[str] = []
    for name, path in REQUIRED_FILES.items():
        if not path.exists():
            issues.append(f"missing_required_file:{name}:{path}")
    if not NEXT_G12_PROMPT.exists():
        issues.append(f"missing_next_g12_prompt:{NEXT_G12_PROMPT}")
    if issues:
        result = {"ok": False, "issues": issues}
        RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 1

    context = read_json(REQUIRED_FILES["context_anchor"])
    accepted = read_json(REQUIRED_FILES["accepted_evidence_binding"])
    inventory = read_json(REQUIRED_FILES["rowset_inventory"])
    fail_anatomy = read_json(REQUIRED_FILES["fail_closed_anatomy"])
    source_search = read_json(REQUIRED_FILES["source_search"])
    saturation = read_json(REQUIRED_FILES["saturation"])
    instruction = read_json(REQUIRED_FILES["instruction_coverage"])
    decision = read_json(REQUIRED_FILES["decision_ledger"])
    completion = read_json(REQUIRED_FILES["completion_audit"])
    manifest = read_json(REQUIRED_FILES["output_manifest"])

    for name, obj in {
        "context_anchor": context,
        "accepted_evidence_binding": accepted,
        "rowset_inventory": inventory,
        "fail_closed_anatomy": fail_anatomy,
        "source_search": source_search,
        "saturation": saturation,
        "instruction_coverage": instruction,
        "decision_ledger": decision,
        "completion_audit": completion,
        "output_manifest": manifest,
    }.items():
        if not flag_check(obj):
            issues.append(f"safe_flags_or_forbidden_surface_failed:{name}")

    if inventory.get("unc004_rowset_rows") != 3014:
        issues.append("unc004_rowset_rows_not_3014")
    if inventory.get("unc004_target_rows") != 24112:
        issues.append("unc004_target_rows_not_24112")
    if fail_anatomy.get("rowset_non_applicable_rows") != 0:
        issues.append("unc004_unexpected_rowset_non_applicable_rows")
    if fail_anatomy.get("rowset_fail_closed_rows") != 0:
        issues.append("unc004_unexpected_rowset_fail_closed_rows")
    if completion.get("same_evidence_class_remaining_repairable_blockers") != 0:
        issues.append("same_evidence_class_blockers_remaining")
    if completion.get("same_evidence_class_remaining_actionable_ambiguities") != 0:
        issues.append("same_evidence_class_ambiguities_remaining")
    if completion.get("same_evidence_class_remaining_source_search_paths") != 0:
        issues.append("same_evidence_class_source_paths_remaining")
    if completion.get("no_arbitrary_top_n_used") is not True:
        issues.append("completion_top_n_flag_not_true")

    jsonl_counts = {}
    family_counters: dict[str, Counter[str]] = {}
    classification_counters: dict[str, Counter[str]] = {}
    for key in (
        "tier_distribution",
        "pass_control_recompute",
        "matched_control",
        "leave_one_stress",
        "duplicate_concentration",
        "interaction",
        "negative_inverse_neutral",
    ):
        count, families, classifications = count_jsonl(REQUIRED_FILES[key])
        jsonl_counts[key] = count
        family_counters[key] = families
        classification_counters[key] = classifications
        if count <= 0:
            issues.append(f"empty_jsonl:{key}")
        if classifications.get("SAFE_FLAG_OR_FORBIDDEN_SURFACE_FAILURE"):
            issues.append(f"jsonl_safe_flag_failure:{key}")

    required_distribution_families = {
        "tier_by_symbol",
        "tier_by_economic_group",
        "tier_by_session",
        "tier_by_source_segment",
        "tier_by_partition",
        "tier_by_horizon",
        "tier_by_target_family",
        "tier_by_duplicate_key",
        "tier_by_target_status",
    }
    missing_dist = required_distribution_families - set(family_counters["tier_distribution"])
    if missing_dist:
        issues.append(f"missing_distribution_families:{sorted(missing_dist)}")

    required_interactions = {
        "source_confidence_tier_x_haz001_density",
        "source_confidence_tier_x_beh001_session_open",
        "source_confidence_tier_x_haz005_transition_clock",
        "source_confidence_tier_x_mac001_calendar",
        "source_confidence_tier_x_mac004_fix_window",
    }
    missing_interactions = required_interactions - set(family_counters["interaction"])
    if missing_interactions:
        issues.append(f"missing_interaction_families:{sorted(missing_interactions)}")

    if not any(k.startswith("matched_by_symbol_session_source_segment") for k in family_counters["matched_control"]):
        issues.append("missing_source_segment_matched_controls")
    if not any(k.startswith("leave_one_source_segment") for k in family_counters["leave_one_stress"]):
        issues.append("missing_leave_one_source_segment")
    if not source_search.get("approved_roots"):
        issues.append("source_search_roots_missing")
    if decision.get("use_as_live_filter_now") is not False:
        issues.append("decision_improper_live_filter")
    if decision.get("terminal_decision") not in {
        "PRESERVE_AS_SOURCE_BIAS_AWARE_RETEST_CANDIDATE_NOT_FILTER",
        "ROUTE_TO_SOURCE_CAPTURE_OR_KILL_IF_MATCHED_CONTROLS_REMAIN_NOT_FEASIBLE",
    }:
        issues.append("unexpected_terminal_decision")
    if not all(item.get("passed") for item in instruction.get("coverage_items", [])):
        issues.append("instruction_coverage_not_all_passed")
    if manifest.get("artifact_count", 0) < 15:
        issues.append("manifest_too_small")
    if accepted.get("accepted_g12_terminal_decision") != "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_RESULT_AUDIT_NO_PROMOTION":
        issues.append("accepted_g12_decision_not_bound")

    result = {
        "ok": not issues,
        "issues": issues,
        "jsonl_counts": jsonl_counts,
        "classification_counts": {key: dict(value) for key, value in classification_counters.items()},
        "required_distribution_families_present": sorted(required_distribution_families),
        "required_interactions_present": sorted(required_interactions),
        "safe_flags": SAFE_FLAGS,
        "forbidden_surfaces": FORBIDDEN_SURFACE_FLAGS,
        "can_mark_goal_complete": not issues,
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
