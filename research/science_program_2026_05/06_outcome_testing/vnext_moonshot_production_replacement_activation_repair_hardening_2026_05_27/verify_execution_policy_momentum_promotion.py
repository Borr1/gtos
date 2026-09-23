from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
OUT_DIR = ROUTE_DIR / "ei15r"
SUMMARY = OUT_DIR / "momentum_policy_promotion_summary.json"
PROMOTION_MANIFEST = OUT_DIR / "momentum_policy_promotion.manifest.jsonl"
EXCEPTION_LEDGER = OUT_DIR / "momentum_exception_decision_ledger.jsonl"
RISK_PROOF = OUT_DIR / "selected_policy_risk_proof_summary.json"
LIFECYCLE_PROOF = OUT_DIR / "momentum_policy_lifecycle_propagation_proof.json"
VERIFIER_RESULT = OUT_DIR / f"momentum_policy_promotion_verifier_result_{DATE}.json"
COMPLETION_EVIDENCE = (
    ROUTE_DIR / f"MOMENTUM_POLICY_PROMOTION_COMPLETION_EVIDENCE_{DATE}.json"
)
BUILDER = ROUTE_DIR / "build_execution_policy_momentum_promotion.py"
VERIFIER = ROUTE_DIR / "verify_execution_policy_momentum_promotion.py"
EXPECTED_ROWS = 289_600
EXPECTED_REPLAYABLE_ROWS = 289_599
EXPECTED_PROMOTED_TOTAL_R = 286_221.353599
EXPECTED_POLICY_COUNTS = {
    "momentum_exhaustion": 121_112,
    "partial_be_runner": 168_487,
    "non_replayable_no_policy": 1,
}
EXPECTED_EXCEPTION_FAMILIES = {
    "cross_asset_lead_lag",
    "displacement_continuation",
    "liquidity_sweep_reclaim",
    "regime_transition_break",
    "session_open_range_break",
    "volatility_compression_expansion",
}
FORBIDDEN_PROMOTED_POLICIES = {
    "fixed_1_5r",
    "j46_j49",
    "be_after_trigger",
    "trailing_runner",
    "time_stop",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                yield line_no, json.loads(line)


def rel_to_path(path_text: str) -> Path:
    return REPO_ROOT / path_text


def close_enough(left: Any, right: Any, tolerance: float = 0.00001) -> bool:
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return left == right


def check_plain_jsonl(path: Path, issues: list[str]) -> None:
    if path.suffix != ".jsonl":
        issues.append(f"not_jsonl:{path}")
    if path.name.endswith(".jsonl.gz") or path.suffixes[-2:] == [".jsonl", ".gz"]:
        issues.append(f"compressed_jsonl_forbidden:{path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        first = handle.readline()
    if first.strip():
        json.loads(first)


def add_metric(bucket: dict[str, Any], value: float | None) -> None:
    if value is None:
        return
    bucket["rows"] += 1
    bucket["total_r"] += value
    if value > 0:
        bucket["wins"] += 1
        bucket["gross_profit_r"] += value
    elif value < 0:
        bucket["losses"] += 1
        bucket["gross_loss_r"] += value
    else:
        bucket["breakevens"] += 1


def metric_bucket() -> dict[str, Any]:
    return {
        "rows": 0,
        "total_r": 0.0,
        "wins": 0,
        "losses": 0,
        "breakevens": 0,
        "gross_profit_r": 0.0,
        "gross_loss_r": 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    for path in (
        SUMMARY,
        PROMOTION_MANIFEST,
        EXCEPTION_LEDGER,
        RISK_PROOF,
        LIFECYCLE_PROOF,
        BUILDER,
        VERIFIER,
    ):
        if not path.exists():
            issues.append(f"missing_required_file:{path.name}")
    if issues:
        print(json.dumps({"status": "failed", "issues": issues}, sort_keys=True))
        return 1

    config = yaml.safe_load((REPO_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8")) or {}
    gtos_cfg = config.get("gtos_vnext_runtime") or {}
    summary = read_json(SUMMARY)
    risk = read_json(RISK_PROOF)
    lifecycle = read_json(LIFECYCLE_PROOF)

    if summary.get("full_denominator_rows") != EXPECTED_ROWS:
        issues.append(f"full_denominator_rows:{summary.get('full_denominator_rows')}")
    if summary.get("selected_rows_processed") != EXPECTED_ROWS:
        issues.append("selected_rows_processed_mismatch")
    if summary.get("replayable_rows") != EXPECTED_REPLAYABLE_ROWS:
        issues.append(f"replayable_rows:{summary.get('replayable_rows')}")
    if summary.get("non_replayable_rows") != 1:
        issues.append(f"non_replayable_rows:{summary.get('non_replayable_rows')}")
    if summary.get("ledger_output_format") != "uncompressed_plain_jsonl_shards_with_manifest":
        issues.append("promotion_ledger_not_plain_uncompressed_jsonl")

    decision = summary.get("promotion_decision") or {}
    if decision.get("primary_policy") != "momentum_exhaustion":
        issues.append("primary_policy_not_momentum_exhaustion")
    if decision.get("exception_policy") != "partial_be_runner":
        issues.append("exception_policy_not_partial_be_runner")
    if set(decision.get("exception_origin_families") or []) != EXPECTED_EXCEPTION_FAMILIES:
        issues.append("exception_origin_families_mismatch")
    if decision.get("fixed_1_5r_role") != "comparator_and_fail_closed_refusal_only_not_default":
        issues.append("fixed_1_5r_not_marked_comparator_only")
    if decision.get("be_after_trigger_role") != "supported_legacy_policy_not_primary_not_exception":
        issues.append("be_after_trigger_still_primary_or_exception")

    expected_config = summary.get("runtime_config_expected") or {}
    for key, expected in expected_config.items():
        actual = gtos_cfg.get(key)
        if key.endswith("_to_partial_be_runner"):
            if set(actual or []) != set(expected or []):
                issues.append(f"config_mismatch:{key}")
        elif actual != expected:
            issues.append(f"config_mismatch:{key}:{actual}!={expected}")

    metrics = summary.get("metrics") or {}
    promoted = metrics.get("promoted_dynamic_router") or {}
    if promoted.get("rows") != EXPECTED_REPLAYABLE_ROWS:
        issues.append("promoted_metric_row_count_mismatch")
    if not close_enough(promoted.get("total_r"), EXPECTED_PROMOTED_TOTAL_R):
        issues.append(f"promoted_total_r:{promoted.get('total_r')}")
    if not close_enough(promoted.get("expectancy_r"), 0.988336816):
        issues.append(f"promoted_expectancy:{promoted.get('expectancy_r')}")
    if not close_enough(promoted.get("profit_factor"), 8.823648469):
        issues.append(f"promoted_profit_factor:{promoted.get('profit_factor')}")
    if not close_enough(promoted.get("win_rate"), 0.689070059):
        issues.append(f"promoted_win_rate:{promoted.get('win_rate')}")
    if summary.get("policy_distribution") != EXPECTED_POLICY_COUNTS:
        issues.append(f"policy_distribution_mismatch:{summary.get('policy_distribution')}")
    deltas = summary.get("deltas") or {}
    source_state = summary.get("source_dynamic_router_state")
    if source_state == "post_promotion_router_already_current":
        if not close_enough(deltas.get("promoted_minus_old_condition_router_r"), 0.0):
            issues.append("post_promotion_source_router_not_equal_promoted_router")
        old_metric = (summary.get("metrics") or {}).get("old_condition_router") or {}
        if not close_enough(old_metric.get("total_r"), EXPECTED_PROMOTED_TOTAL_R):
            issues.append("post_promotion_source_router_total_r_mismatch")
    elif deltas.get("promoted_minus_old_condition_router_r", 0) <= 128_000:
        issues.append("promoted_delta_vs_old_router_too_low")
    if deltas.get("promoted_minus_global_momentum_r", 0) <= 33_000:
        issues.append("promoted_delta_vs_global_momentum_too_low")

    output_meta = (summary.get("outputs") or {}).get("promotion_ledger") or {}
    if output_meta.get("row_count") != EXPECTED_ROWS:
        issues.append("promotion_output_row_count_mismatch")
    if output_meta.get("plain_jsonl_shards") is not True or output_meta.get("compressed") is not False:
        issues.append("promotion_output_not_plain_jsonl")
    check_plain_jsonl(PROMOTION_MANIFEST, issues)

    entries = [row for _, row in read_jsonl(PROMOTION_MANIFEST)]
    manifest_count = sum(int(row.get("row_count", -1)) for row in entries)
    if manifest_count != EXPECTED_ROWS:
        issues.append(f"manifest_row_count:{manifest_count}")

    seen: set[str] = set()
    policy_counts: Counter[str] = Counter()
    metric = metric_bucket()
    row_count = 0
    missing_exit_reason = 0
    missing_cost_notes = 0
    missing_risk_identity = 0
    non_exception_partial = 0
    momentum_exception_family = 0
    forbidden_promoted_policy_rows = 0
    non_replayable_rows = 0
    for entry in entries:
        shard = rel_to_path(entry.get("path", ""))
        if not shard.exists():
            issues.append(f"missing_promotion_shard:{entry.get('path')}")
            continue
        check_plain_jsonl(shard, issues)
        shard_rows = 0
        for _, row in read_jsonl(shard):
            row_count += 1
            shard_rows += 1
            rid = row.get("selected_row_id")
            if not rid:
                issues.append("missing_selected_row_id")
            elif rid in seen:
                issues.append(f"duplicate_selected_row_id:{rid}")
            else:
                seen.add(rid)
            policy = row.get("promoted_policy") or "non_replayable_no_policy"
            policy_counts[policy] += 1
            if policy in FORBIDDEN_PROMOTED_POLICIES:
                forbidden_promoted_policy_rows += 1
            if row.get("non_replayable_reason"):
                non_replayable_rows += 1
                if policy != "non_replayable_no_policy":
                    issues.append(f"non_replayable_has_policy:{rid}")
                continue
            value = row.get("promoted_final_r")
            if value is None:
                issues.append(f"replayable_missing_promoted_final_r:{rid}")
            else:
                add_metric(metric, float(value))
            if not row.get("promoted_exit_reason"):
                missing_exit_reason += 1
            if not row.get("cost_notes"):
                missing_cost_notes += 1
            risk_cell = row.get("risk_cell") or {}
            if not risk_cell.get("selected_cell_risk_cell_id"):
                missing_risk_identity += 1
            family = row.get("origin_family")
            if policy == "partial_be_runner" and family not in EXPECTED_EXCEPTION_FAMILIES:
                non_exception_partial += 1
            if policy == "momentum_exhaustion" and family in EXPECTED_EXCEPTION_FAMILIES:
                momentum_exception_family += 1
            if row.get("fixed_1_5r_final_r") is None:
                issues.append(f"missing_fixed_comparator:{rid}")
            if row.get("delta_promoted_vs_old_router_r") is None:
                issues.append(f"missing_promoted_delta:{rid}")
        if shard_rows != entry.get("row_count"):
            issues.append(f"shard_row_count_mismatch:{entry.get('path')}")

    if row_count != EXPECTED_ROWS:
        issues.append(f"promotion_row_count:{row_count}")
    if policy_counts != EXPECTED_POLICY_COUNTS:
        issues.append(f"ledger_policy_counts:{dict(policy_counts)}")
    if forbidden_promoted_policy_rows:
        issues.append(f"forbidden_promoted_policy_rows:{forbidden_promoted_policy_rows}")
    if non_replayable_rows != 1:
        issues.append(f"ledger_non_replayable_rows:{non_replayable_rows}")
    if missing_exit_reason:
        issues.append(f"missing_promoted_exit_reason:{missing_exit_reason}")
    if missing_cost_notes:
        issues.append(f"missing_cost_notes:{missing_cost_notes}")
    if missing_risk_identity:
        issues.append(f"missing_risk_identity:{missing_risk_identity}")
    if non_exception_partial:
        issues.append(f"partial_rows_outside_exception_families:{non_exception_partial}")
    if momentum_exception_family:
        issues.append(f"momentum_rows_inside_exception_families:{momentum_exception_family}")
    if not close_enough(metric["total_r"], EXPECTED_PROMOTED_TOTAL_R):
        issues.append(f"ledger_promoted_total_r:{metric['total_r']}")

    check_plain_jsonl(EXCEPTION_LEDGER, issues)
    exception_rows = [row for _, row in read_jsonl(EXCEPTION_LEDGER)]
    accepted = {
        row.get("segment_value")
        for row in exception_rows
        if row.get("dimension") == "origin_family"
        and row.get("decision") == "promote_partial_be_runner_exception"
    }
    if accepted != EXPECTED_EXCEPTION_FAMILIES:
        issues.append(f"accepted_exception_families:{sorted(accepted)}")
    rejected_current_breaker = [
        row
        for row in exception_rows
        if row.get("dimension") == "origin_family"
        and row.get("segment_value") == "current_breaker_re_entry"
        and row.get("decision") == "reject_exception_keep_momentum_primary"
    ]
    if not rejected_current_breaker:
        issues.append("missing_rejected_current_breaker_re_entry_exception_evidence")
    for row in exception_rows:
        if row.get("decision") == "promote_partial_be_runner_exception":
            stability = row.get("stability") or {}
            if not stability.get("stable_positive_all_years"):
                issues.append(f"accepted_exception_not_year_stable:{row.get('segment_value')}")
            if not stability.get("stable_positive_all_sessions"):
                issues.append(f"accepted_exception_not_session_stable:{row.get('segment_value')}")

    if risk.get("policy_identity_status_required_in_live_runtime") is not True:
        issues.append("selected_policy_risk_identity_not_required")
    if risk.get("be_keyed_risk_rows_allowed_only_with_policy_invariant_broker_geometry") is not True:
        issues.append("be_keyed_risk_not_policy_invariant_only")
    if risk.get("config_policy_invariant_geometry_flag") is not True:
        issues.append("policy_invariant_geometry_config_flag_not_true")
    runtime_paths = "\n".join(risk.get("runtime_enforcement_paths") or [])
    if "_resolve_vnext_production_risk_pct" not in runtime_paths:
        issues.append("risk_runtime_execution_enforcement_path_missing")

    if lifecycle.get("production_policy") != "momentum_exhaustion":
        issues.append("lifecycle_proof_production_policy_not_momentum")
    if lifecycle.get("fixed_1_5r_role") != "comparator_and_fail_closed_refusal_only_not_default":
        issues.append("lifecycle_fixed_15r_reactivation_risk")
    required_fields = set(lifecycle.get("required_runtime_fields") or [])
    for field in (
        "gtos_vnext_dynamic_policy_selected",
        "gtos_vnext_execution_policy_id",
        "gtos_vnext_dynamic_momentum_pullback_r",
        "gtos_vnext_selected_cell_risk_policy_identity_status",
    ):
        if field not in required_fields:
            issues.append(f"lifecycle_required_field_missing:{field}")

    code_checks = {
        "router_primary_constant": (
            REPO_ROOT / "src" / "research" / "moonshot_default_off_policy_router.py",
            "DEFAULT_POLICY = MOMENTUM_EXHAUSTION_POLICY",
        ),
        "execution_risk_identity_status": (
            REPO_ROOT / "src" / "components" / "execution.py",
            "gtos_vnext_selected_cell_risk_policy_identity_status",
        ),
        "runtime_policy_invariant_geometry": (
            REPO_ROOT / "src" / "components" / "gtos_vnext_runtime.py",
            "policy_invariant_broker_geometry_for_selected_execution_policy",
        ),
        "future_leakage_test": (
            REPO_ROOT / "tests" / "test_moonshot_default_off_policy_router.py",
            "future_outcome_fields_present_but_ignored_by_live_router",
        ),
    }
    for name, (path, token) in code_checks.items():
        if token not in path.read_text(encoding="utf-8"):
            issues.append(f"code_check_missing:{name}")

    result = {
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues[:50],
        "checked_rows": row_count,
        "policy_counts": dict(policy_counts),
        "promoted_total_r": round(metric["total_r"], 6),
    }
    if not args.check:
        write_json(VERIFIER_RESULT, result)
        write_json(
            COMPLETION_EVIDENCE,
            {
                "schema_version": "vnext_execution_policy_momentum_promotion_completion_v1",
                "generated_at_utc": utc_now(),
                "status": "verified" if not issues else "verification_failed",
                "summary_path": rel(SUMMARY),
                "promotion_ledger_manifest": rel(PROMOTION_MANIFEST),
                "exception_decision_ledger": rel(EXCEPTION_LEDGER),
                "selected_policy_risk_proof_summary": rel(RISK_PROOF),
                "lifecycle_propagation_proof": rel(LIFECYCLE_PROOF),
                "verifier_path": rel(VERIFIER),
                "verifier_result_path": rel(VERIFIER_RESULT),
                "checked_rows": row_count,
                "policy_counts": dict(policy_counts),
                "promoted_total_r": round(metric["total_r"], 6),
                "issue_count": len(issues),
            },
        )
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
