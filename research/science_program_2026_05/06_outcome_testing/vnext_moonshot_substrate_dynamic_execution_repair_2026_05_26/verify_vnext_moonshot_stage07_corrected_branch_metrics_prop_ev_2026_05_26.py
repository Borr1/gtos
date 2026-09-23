from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
DATE_ID = "2026-05-26"

BRANCH_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_METRICS_LEDGER_{DATE_ID}.jsonl"
PROP_LEDGER = ROUTE_DIR / f"VNEXT_MOONSHOT_PROP_EV_ATTEMPT_LEDGER_{DATE_ID}.jsonl"
SUMMARY = ROUTE_DIR / f"VNEXT_MOONSHOT_CORRECTED_BRANCH_SUMMARY_{DATE_ID}.json"
REPORT = ROUTE_DIR / f"VNEXT_MOONSHOT_PROP_EV_OPPORTUNITY_COST_REPORT_{DATE_ID}.md"
STATE = ROUTE_DIR / f"VNEXT_MOONSHOT_SUBSTRATE_SESSION_STATE_{DATE_ID}.json"
VERIFY_RESULT = ROUTE_DIR / f"VNEXT_MOONSHOT_STAGE07_VERIFICATION_RESULT_{DATE_ID}.json"

REQUIRED_BRANCHES = {
    "raw_repaired_all_replayable",
    "source_complete_only",
    "missing_source_excluded_asof_computed",
    "high_quality_asof_kz",
    "aggressive_research_asof_all_sessions",
    "context_recovery_off_kz_side_aligned",
    "ml_candidate_feature_complete",
    "ai_required_context_rich",
    "no_paid_mechanical_diagnostic",
    "prop_ev_optimized_side_aligned_kz",
    "origin_current_ob_retest",
    "origin_current_fvg_fill",
    "origin_current_breaker_re_entry",
}

REQUIRED_PROP_POLICIES = {
    "ALLOW_FULL_RISK_SEGMENTED",
    "REDUCE_RISK_TO_BUDGET",
    "MICRO_RISK_NEAR_BUDGET",
    "HIGH_QUALITY_ONLY",
    "DEFER_UNTIL_RESET",
    "ACCOUNT_ABANDON_OR_RESTART",
    "BLOCK_ALL_NEAR_LIMIT",
    "EV_OPTIMIZED_REDUCE_OR_DEFER",
}

REQUIRED_DYNAMIC_POLICIES = {
    "legacy_fixed_1.5r",
    "ai_target",
    "live_current_j46_j49",
    "partial_be_runner",
    "be_after_trigger",
    "trailing_runner",
    "time_stop_only",
    "early_cut_if_no_progress",
    "path_aware_runner",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> None:
    failures: list[str] = []
    summary = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}
    state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
    branch_rows = load_jsonl(BRANCH_LEDGER) if BRANCH_LEDGER.exists() else []
    prop_rows = load_jsonl(PROP_LEDGER) if PROP_LEDGER.exists() else []

    branch_ids = {row.get("branch_id") for row in branch_rows}
    branch_policy_pairs = {
        (row.get("branch_id"), row.get("policy_name"))
        for row in branch_rows
        if row.get("policy_name")
    }
    prop_policies = {row.get("prop_policy") for row in prop_rows}
    dynamic_policies_in_prop = {row.get("policy_name") for row in prop_rows}
    selection_classes = Counter(row.get("selection_class") for row in branch_rows)

    missing_branches = sorted(REQUIRED_BRANCHES - branch_ids)
    if missing_branches:
        failures.append(f"missing required branch rows: {missing_branches}")
    missing_raw_policies = sorted(
        policy for policy in REQUIRED_DYNAMIC_POLICIES if ("raw_repaired_all_replayable", policy) not in branch_policy_pairs
    )
    if missing_raw_policies:
        failures.append(f"raw repaired branch missing dynamic policies: {missing_raw_policies}")
    missing_prop_policies = sorted(REQUIRED_PROP_POLICIES - prop_policies)
    if missing_prop_policies:
        failures.append(f"missing prop policies: {missing_prop_policies}")
    missing_dynamic_prop = sorted(REQUIRED_DYNAMIC_POLICIES - dynamic_policies_in_prop)
    if missing_dynamic_prop:
        failures.append(f"prop EV missing dynamic policies: {missing_dynamic_prop}")
    if summary.get("events_replayed") != 214536:
        failures.append(f"events_replayed mismatch: {summary.get('events_replayed')}")
    if summary.get("corrected_branch_metric_rows") != len(branch_rows):
        failures.append("summary branch row count mismatch")
    if summary.get("prop_ev_attempt_rows") != len(prop_rows):
        failures.append("summary prop row count mismatch")
    if not summary.get("legacy_fixed_1_5r_rejected_as_activation_truth"):
        failures.append("legacy fixed 1.5R was not explicitly rejected as activation truth")
    if not summary.get("segmented_prop_attempts_not_continuous_account"):
        failures.append("prop simulation did not assert segmented attempts")
    if any(not row.get("segmented_account_attempts_modelled") for row in prop_rows):
        failures.append("one or more prop rows did not model segmented account attempts")
    if not any(row.get("prop_policy") == "EV_OPTIMIZED_REDUCE_OR_DEFER" for row in prop_rows):
        failures.append("EV optimized prop policy missing")
    if "candidate_origin_registry_only" not in selection_classes:
        failures.append("registry-only candidate-origin rows missing")
    if summary.get("forbidden_boundaries_crossed"):
        failures.append("forbidden boundary crossed")
    if state.get("first_incomplete_invariant") != "STAGE_08_AI_ROLE_AND_BUDGET_DESIGN":
        failures.append("route state did not advance to Stage08")
    if not REPORT.exists() or REPORT.stat().st_size < 500:
        failures.append("opportunity cost report missing or too small")

    result = {
        "checked_at_utc": utc_now(),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "branch_metric_rows": len(branch_rows),
        "prop_ev_attempt_rows": len(prop_rows),
        "branch_selection_class_counts": dict(sorted(selection_classes.items())),
        "prop_policies": sorted(prop_policies),
        "dynamic_policies_in_prop": sorted(dynamic_policies_in_prop),
        "first_incomplete_invariant": state.get("first_incomplete_invariant"),
    }
    VERIFY_RESULT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
