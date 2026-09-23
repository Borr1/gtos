from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
OUT_DIR = ROUTE_DIR / "ei15r"
SUMMARY = OUT_DIR / "summary.json"
BUILDER = ROUTE_DIR / "build_execution_intelligence_static_15r_ceiling_repair.py"
VERIFIER = ROUTE_DIR / "verify_execution_intelligence_static_15r_ceiling_repair.py"
TEST_FILE = ROUTE_DIR / "test_execution_intelligence_static_15r_ceiling_repair.py"
FINAL_ROUTER_BUILDER = ROUTE_DIR / "build_execution_intelligence_dynamic_router_replay.py"
FINAL_ROUTER_VERIFIER = ROUTE_DIR / "verify_execution_intelligence_dynamic_router_replay.py"
FINAL_ROUTER_SUMMARY = OUT_DIR / "final_dynamic_router_replay_summary.json"

POLICIES = (
    "fixed_1_5r",
    "be_after_trigger",
    "trailing_runner",
    "partial_be_runner",
    "hold_to_structure",
    "early_cut_if_no_progress",
    "volatility_session_expansion",
    "momentum_exhaustion",
    "liquidity_sweep_exit",
    "m1_tick_path_exit",
    "time_stop",
    "condition_router",
)
IMPLEMENTED_LIVE_POLICIES = (
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
    "time_stop",
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            yield line_no, json.loads(line)


def check_plain_jsonl(path: Path, issues: list[str]) -> None:
    if path.suffix != ".jsonl":
        issues.append(f"not_jsonl:{path}")
    if path.suffixes[-2:] == [".jsonl", ".gz"] or path.name.endswith(".jsonl.gz"):
        issues.append(f"compressed_jsonl_forbidden:{path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        first = handle.readline()
    if first:
        json.loads(first)


def manifest_entries(manifest: Path, issues: list[str]) -> list[dict[str, Any]]:
    check_plain_jsonl(manifest, issues)
    entries = [row for _, row in read_jsonl(manifest)]
    if not entries:
        issues.append(f"empty_manifest:{manifest.name}")
    for entry in entries:
        shard = REPO_ROOT / entry.get("path", "")
        if not shard.exists():
            issues.append(f"missing_shard:{entry.get('path')}")
            continue
        check_plain_jsonl(shard, issues)
        if entry.get("compressed") is not False or entry.get("format") != "plain_jsonl":
            issues.append(f"manifest_not_plain_uncompressed:{entry.get('path')}")
    return entries


def verify_ledger(
    *,
    name: str,
    manifest: Path,
    expected_rows: int,
    issues: list[str],
    row_check: Callable[[dict[str, Any], int], None] | None = None,
) -> int:
    entries = manifest_entries(manifest, issues)
    manifest_total = sum(int(entry.get("row_count", -1)) for entry in entries)
    if manifest_total != expected_rows:
        issues.append(f"{name}_manifest_row_count:{manifest_total}!={expected_rows}")

    actual = 0
    for entry in entries:
        shard = REPO_ROOT / entry["path"]
        if not shard.exists():
            continue
        shard_count = 0
        for _, row in read_jsonl(shard):
            actual += 1
            shard_count += 1
            if row_check:
                row_check(row, actual)
        if shard_count != int(entry.get("row_count", -1)):
            issues.append(f"{name}_shard_row_count:{entry['path']}:{shard_count}!={entry.get('row_count')}")
    if actual != expected_rows:
        issues.append(f"{name}_actual_row_count:{actual}!={expected_rows}")
    return actual


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    for path in (
        BUILDER,
        VERIFIER,
        TEST_FILE,
        FINAL_ROUTER_BUILDER,
        FINAL_ROUTER_VERIFIER,
        STAGE04_SUMMARY,
        SUMMARY,
        FINAL_ROUTER_SUMMARY,
    ):
        if not path.exists():
            issues.append(f"missing_required_file:{path.name}")
    if issues:
        print(json.dumps({"status": "failed", "issue_count": len(issues), "issues": issues}, sort_keys=True))
        return 1

    stage04 = read_json(STAGE04_SUMMARY)
    summary = read_json(SUMMARY)
    expected_selected = int(stage04["selector_counts"]["combined_selected_rows"])
    expected_winners = int(stage04["canonical_metrics"]["wins"])
    expected_losers = int(stage04["canonical_metrics"]["losses"])
    expected_bes = int(stage04["canonical_metrics"]["breakevens"])
    expected_dynamic = expected_selected * len(POLICIES)
    outputs = summary.get("outputs") or {}

    if expected_selected != 289600:
        issues.append(f"unexpected_stage04_denominator:{expected_selected}")
    if summary.get("ledger_output_format") != "uncompressed_plain_jsonl_shards_with_manifest":
        issues.append("summary_missing_plain_jsonl_shard_format")
    if summary.get("static_ceiling_not_terminal") is not True:
        issues.append("static_ceiling_terminal_or_missing")
    if summary.get("selected_rows_processed") != expected_selected:
        issues.append("summary_selected_rows_mismatch")
    if summary.get("dynamic_policy_rows") != expected_dynamic:
        issues.append("summary_dynamic_policy_rows_mismatch")

    required_ledgers = {
        "denominator_reconciliation_ledger": expected_selected,
        "winner_leftover_move_ledger": expected_winners,
        "loser_mitigation_ledger": expected_losers,
        "be_classification_ledger": expected_bes,
        "dynamic_exit_counterfactual_ledger": expected_dynamic,
        "runtime_surface_gap_ledger": expected_dynamic,
        "replay_scoring_upgrade_ledger": expected_selected,
    }
    for ledger_name in required_ledgers:
        if ledger_name not in outputs:
            issues.append(f"missing_output_meta:{ledger_name}")
        elif not outputs[ledger_name].get("plain_jsonl_shards"):
            issues.append(f"output_not_marked_plain_jsonl:{ledger_name}")

    selected_ids: set[str] = set()

    def denom_check(row: dict[str, Any], _idx: int) -> None:
        rid = row.get("selected_row_id")
        if not rid:
            issues.append("denom_blank_selected_row_id")
            return
        if rid in selected_ids:
            issues.append(f"denom_duplicate_selected_row_id:{rid}")
        selected_ids.add(rid)
        if not row.get("replay_class"):
            issues.append(f"denom_blank_replay_class:{rid}")
        if str(row.get("replay_class")).startswith("non_replayable") and not row.get("non_replayable_reason"):
            issues.append(f"denom_missing_non_replayable_reason:{rid}")
        if not row.get("m1_availability_status"):
            issues.append(f"denom_missing_m1_availability_status:{rid}")
        if not row.get("tick_availability_status"):
            issues.append(f"denom_missing_tick_availability_status:{rid}")
        if row.get("m1_availability_status") == "local_m1_bar_available_for_entry_minute":
            if not row.get("m1_source_path") or not row.get("m1_source_sha256"):
                issues.append(f"denom_m1_available_without_path_hash:{rid}")
        if row.get("tick_availability_status") == "local_tick_parquet_available_for_entry_date":
            if not row.get("tick_source_path") or not row.get("tick_source_sha256"):
                issues.append(f"denom_tick_available_without_path_hash:{rid}")

    verify_ledger(
        name="denominator_reconciliation_ledger",
        manifest=REPO_ROOT / outputs["denominator_reconciliation_ledger"]["manifest_path"],
        expected_rows=expected_selected,
        issues=issues,
        row_check=denom_check,
    )
    if len(selected_ids) != expected_selected:
        issues.append(f"selected_id_unique_count:{len(selected_ids)}!={expected_selected}")

    def primary_row_check(row: dict[str, Any], _idx: int) -> None:
        if not row.get("selected_row_id"):
            issues.append("primary_ledger_blank_selected_row_id")
        if not row.get("replay_class"):
            issues.append("primary_ledger_blank_replay_class")

    verify_ledger(
        name="winner_leftover_move_ledger",
        manifest=REPO_ROOT / outputs["winner_leftover_move_ledger"]["manifest_path"],
        expected_rows=expected_winners,
        issues=issues,
        row_check=primary_row_check,
    )
    verify_ledger(
        name="loser_mitigation_ledger",
        manifest=REPO_ROOT / outputs["loser_mitigation_ledger"]["manifest_path"],
        expected_rows=expected_losers,
        issues=issues,
        row_check=primary_row_check,
    )
    verify_ledger(
        name="be_classification_ledger",
        manifest=REPO_ROOT / outputs["be_classification_ledger"]["manifest_path"],
        expected_rows=expected_bes,
        issues=issues,
        row_check=primary_row_check,
    )

    policy_counts: Counter[str] = Counter()

    def dynamic_check(row: dict[str, Any], _idx: int) -> None:
        policy = row.get("policy_name")
        policy_counts[str(policy)] += 1
        if policy not in POLICIES:
            issues.append(f"dynamic_unknown_policy:{policy}")
        if row.get("forbidden_future_features_used") not in ([], None):
            issues.append(f"dynamic_forbidden_future_features:{row.get('selected_row_id')}:{policy}")
        if not row.get("simulation_status"):
            issues.append(f"dynamic_blank_simulation_status:{row.get('selected_row_id')}:{policy}")
        if not isinstance(row.get("runtime_supported_now"), bool):
            issues.append(f"dynamic_runtime_supported_not_bool:{row.get('selected_row_id')}:{policy}")
        if row.get("cost_status") == "missing_historical_live_cost_lifecycle_fields" and row.get("net_r") is not None:
            issues.append(f"dynamic_net_r_silently_filled_without_cost:{row.get('selected_row_id')}:{policy}")
        if str(row.get("simulation_status")).startswith(("not_", "not_applicable")) and not row.get("source_blocker"):
            issues.append(f"dynamic_missing_source_blocker:{row.get('selected_row_id')}:{policy}")
        if policy == "m1_tick_path_exit" and (
            row.get("m1_exact_entry_minute_present") or row.get("tick_source_path")
        ):
            if row.get("simulation_status") == "not_replayable_missing_ordered_m1_tick_source":
                issues.append(f"dynamic_m1_tick_path_ignored_available_ltf_source:{row.get('selected_row_id')}")

    verify_ledger(
        name="dynamic_exit_counterfactual_ledger",
        manifest=REPO_ROOT / outputs["dynamic_exit_counterfactual_ledger"]["manifest_path"],
        expected_rows=expected_dynamic,
        issues=issues,
        row_check=dynamic_check,
    )
    for policy in POLICIES:
        if policy_counts[policy] != expected_selected:
            issues.append(f"dynamic_policy_count:{policy}:{policy_counts[policy]}!={expected_selected}")

    runtime_policy_counts: Counter[str] = Counter()
    implemented_runtime_rows = Counter()

    def runtime_check(row: dict[str, Any], _idx: int) -> None:
        policy = row.get("policy_name")
        runtime_policy_counts[str(policy)] += 1
        if policy not in POLICIES:
            issues.append(f"runtime_unknown_policy:{policy}")
        if row.get("runtime_supported_now"):
            implemented_runtime_rows[str(policy)] += 1
            if not row.get("test_evidence"):
                issues.append(f"runtime_supported_without_test:{policy}")
        else:
            if not row.get("missing_code_path") or not row.get("required_test"):
                issues.append(f"runtime_unsupported_missing_path_or_test:{policy}")
            if not row.get("activation_blocker"):
                issues.append(f"runtime_unsupported_missing_blocker:{policy}")

    verify_ledger(
        name="runtime_surface_gap_ledger",
        manifest=REPO_ROOT / outputs["runtime_surface_gap_ledger"]["manifest_path"],
        expected_rows=expected_dynamic,
        issues=issues,
        row_check=runtime_check,
    )
    for policy in POLICIES:
        if runtime_policy_counts[policy] != expected_selected:
            issues.append(f"runtime_policy_count:{policy}:{runtime_policy_counts[policy]}!={expected_selected}")
    for policy in IMPLEMENTED_LIVE_POLICIES:
        if implemented_runtime_rows[policy] != expected_selected:
            issues.append(f"runtime_policy_not_implemented_all_rows:{policy}:{implemented_runtime_rows[policy]}")

    def upgrade_check(row: dict[str, Any], _idx: int) -> None:
        missing = row.get("missing_fields_after_source_search")
        if not isinstance(missing, list) or not missing:
            issues.append(f"upgrade_missing_exact_fields:{row.get('selected_row_id')}")
        ltf_available = bool(row.get("m1_exact_entry_minute_present") or row.get("tick_source_path"))
        if ltf_available and (
            "m1_or_tick_source_path" in missing or "m1_or_tick_source_sha256" in missing
        ):
            issues.append(f"upgrade_available_ltf_source_still_marked_missing:{row.get('selected_row_id')}")
        if not ltf_available:
            if not row.get("m1_source_absence_proof") and not row.get("tick_source_absence_proof"):
                issues.append(f"upgrade_missing_ltf_absence_proof:{row.get('selected_row_id')}")

    verify_ledger(
        name="replay_scoring_upgrade_ledger",
        manifest=REPO_ROOT / outputs["replay_scoring_upgrade_ledger"]["manifest_path"],
        expected_rows=expected_selected,
        issues=issues,
        row_check=upgrade_check,
    )

    metrics = summary.get("policy_metrics") or {}
    verdict = summary.get("dynamic_layer_verdict") or {}
    for policy in ("fixed_1_5r", *IMPLEMENTED_LIVE_POLICIES):
        if policy not in metrics:
            issues.append(f"missing_policy_metric:{policy}")
    if not verdict.get("baseline_policy") == "fixed_1_5r":
        issues.append("dynamic_verdict_missing_fixed_baseline")
    if verdict.get("fixed_1_5r_role") != "baseline_comparator_and_fail_closed_fallback_only_not_live_default":
        issues.append("dynamic_verdict_reintroduced_fixed_15r_default")
    if verdict.get("production_policy_selection_mode") != "condition_asof_displacement_v1_dynamic_router":
        issues.append("dynamic_verdict_missing_live_router_selection_mode")
    if verdict.get("production_policy_is_single_global_style") is not False:
        issues.append("dynamic_verdict_collapsed_to_single_global_policy")
    if set(IMPLEMENTED_LIVE_POLICIES) - set(verdict.get("implemented_live_policy_set") or []):
        issues.append("dynamic_verdict_missing_implemented_live_policy_set")
    if verdict.get("best_implemented_policy") not in set(IMPLEMENTED_LIVE_POLICIES):
        issues.append("dynamic_verdict_missing_implemented_policy_result")
    if not summary.get("m1_availability_status_counts"):
        issues.append("summary_missing_m1_availability_counts")
    if not summary.get("tick_availability_status_counts"):
        issues.append("summary_missing_tick_availability_counts")

    final_router = read_json(FINAL_ROUTER_SUMMARY)
    if final_router.get("selected_rows_processed") != expected_selected:
        issues.append("final_router_selected_rows_mismatch")
    if final_router.get("condition_router_projection_gap_carried_forward_rows") != 0:
        issues.append("final_router_condition_projection_gap_carried_forward")
    if final_router.get("prior_condition_router_projection_dependency") is not False:
        issues.append("final_router_depends_on_prior_projection")
    if final_router.get("router_refused_rows") != 0:
        issues.append(f"final_router_refused_rows:{final_router.get('router_refused_rows')}")
    if final_router.get("non_replayable_rows_excluded_from_launch_metrics") != final_router.get("non_replayable_rows"):
        issues.append("final_router_non_replayable_exclusion_not_explicit")
    if final_router.get("fixed_1_5r_role") != "baseline_comparator_and_fail_closed_fallback_only_not_live_default":
        issues.append("final_router_fixed_15r_default_reintroduced")
    if final_router.get("global_momentum_role") != "diagnostic_global_counterfactual_not_launch_rule":
        issues.append("final_router_global_momentum_not_diagnostic")
    final_policy_distribution = Counter(final_router.get("policy_distribution") or {})
    if sum(final_policy_distribution.values()) != expected_selected:
        issues.append("final_router_policy_distribution_not_full_denominator")
    if "fixed_1_5r" in final_policy_distribution:
        issues.append("final_router_chose_fixed_15r")
    required_final_policies = {"partial_be_runner", "momentum_exhaustion"}
    if required_final_policies - set(final_policy_distribution):
        issues.append("final_router_missing_required_live_policy_choice")
    forbidden_final_policies = {"fixed_1_5r", "be_after_trigger", "trailing_runner", "time_stop"}
    if forbidden_final_policies & set(final_policy_distribution):
        issues.append("final_router_contains_non_launch_policy_choice")
    final_metrics = final_router.get("final_dynamic_router_metrics") or {}
    for key in ("total_r", "expectancy_r", "profit_factor", "win_rate", "wins", "losses", "breakevens"):
        if key not in final_metrics:
            issues.append(f"final_router_metric_missing:{key}")
    comparisons = final_router.get("global_policy_comparison_metrics") or {}
    for policy in ("fixed_1_5r", "be_after_trigger", "partial_be_runner", "trailing_runner", "momentum_exhaustion", "time_stop"):
        if policy not in comparisons:
            issues.append(f"final_router_missing_global_comparison:{policy}")
    regret = final_router.get("hindsight_best_regret") or {}
    if "total_regret_r" not in regret or "hindsight_best_total_r" not in regret:
        issues.append("final_router_missing_hindsight_regret")
    final_output = (final_router.get("outputs") or {}).get("final_dynamic_router_replay_ledger") or {}
    if final_output.get("plain_jsonl_shards") is not True or final_output.get("compressed") is not False:
        issues.append("final_router_output_not_plain_jsonl")
    final_manifest_path = final_output.get("manifest_path")
    if not final_manifest_path:
        issues.append("final_router_missing_manifest_path")
    else:
        final_entries = manifest_entries(REPO_ROOT / final_manifest_path, issues)
        final_manifest_total = sum(int(entry.get("row_count", -1)) for entry in final_entries)
        if final_manifest_total != expected_selected:
            issues.append(f"final_router_manifest_rows:{final_manifest_total}!={expected_selected}")
    final_distributions = final_router.get("distributions") or {}
    for name in ("symbol", "session", "framework", "origin_family", "chosen_policy", "frequency_by_day", "frequency_by_week", "frequency_by_month"):
        if not final_distributions.get(name):
            issues.append(f"final_router_missing_distribution:{name}")

    missing_shards = [
        issue.removeprefix("missing_shard:")
        for issue in issues
        if issue.startswith("missing_shard:")
    ]
    status = "blocked" if missing_shards else ("passed" if not issues else "failed")
    result = {
        "mode": "check" if args.check else "verify",
        "status": status,
        "issue_count": len(issues),
        "issues": issues[:200],
        "missing_shards": missing_shards,
        "selected_rows": expected_selected,
        "dynamic_policy_rows": expected_dynamic,
        "policy_count_counted": dict(sorted(policy_counts.items())),
        "runtime_policy_count_counted": dict(sorted(runtime_policy_counts.items())),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
