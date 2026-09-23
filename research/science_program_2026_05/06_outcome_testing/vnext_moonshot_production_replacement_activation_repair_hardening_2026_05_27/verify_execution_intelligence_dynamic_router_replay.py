from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-27"
ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
STAGE04_SUMMARY = ROUTE_DIR / f"VNEXT_ACTIVATION_REPAIR_STAGE04_CANONICAL_FREQUENCY_TRADE_R_SUMMARY_{DATE}.json"
SUMMARY = ROUTE_DIR / "ei15r" / "final_dynamic_router_replay_summary.json"
BUILDER = ROUTE_DIR / "build_execution_intelligence_dynamic_router_replay.py"
VERIFIER = ROUTE_DIR / "verify_execution_intelligence_dynamic_router_replay.py"
LIVE_POLICIES = {
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
    "time_stop",
}
COMPARISON_FIELDS = {
    "fixed_1_5r": "comparison_fixed_1_5r_r",
    "be_after_trigger": "comparison_be_after_trigger_r",
    "partial_be_runner": "comparison_partial_be_runner_r",
    "trailing_runner": "comparison_trailing_runner_r",
    "momentum_exhaustion": "comparison_momentum_exhaustion_r",
    "time_stop": "comparison_time_stop_r",
}
EXECUTION_POLICY_IDS = {
    "be_after_trigger": "vnext_exec_be_after_trigger_1r_to_15r",
    "partial_be_runner": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
    "trailing_runner": "vnext_exec_trailing_1r_gap_05r_cap_3r",
    "momentum_exhaustion": "vnext_exec_momentum_1r_pullback_04r_cap_2r",
    "time_stop": "vnext_exec_time_stop_m15_bars",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        for line_no, line in enumerate(handle, 1):
            if line.strip():
                yield line_no, json.loads(line)


def check_plain_jsonl(path: Path, issues: list[str]) -> None:
    if path.suffix != ".jsonl":
        issues.append(f"not_jsonl:{path}")
    if path.name.endswith(".jsonl.gz") or path.suffixes[-2:] == [".jsonl", ".gz"]:
        issues.append(f"compressed_jsonl_forbidden:{path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        first = handle.readline()
    if first.strip():
        json.loads(first)


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


def add_metric(bucket: dict[str, Any], value: float) -> None:
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


def close_enough(left: Any, right: Any, tolerance: float = 0.00001) -> bool:
    if left is None or right is None:
        return left is right
    try:
        return abs(float(left) - float(right)) <= tolerance
    except (TypeError, ValueError):
        return left == right


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    issues: list[str] = []
    for path in (STAGE04_SUMMARY, SUMMARY, BUILDER, VERIFIER):
        if not path.exists():
            issues.append(f"missing_required_file:{path.name}")
    if issues:
        print(json.dumps({"status": "failed", "issue_count": len(issues), "issues": issues}, sort_keys=True))
        return 1

    stage04 = read_json(STAGE04_SUMMARY)
    summary = read_json(SUMMARY)
    expected_rows = int(stage04["selector_counts"]["combined_selected_rows"])
    if expected_rows != 289600:
        issues.append(f"unexpected_stage04_selected_rows:{expected_rows}")
    if summary.get("selected_rows_processed") != expected_rows:
        issues.append("summary_selected_rows_mismatch")
    if summary.get("full_denominator_rows") != expected_rows:
        issues.append("summary_full_denominator_mismatch")
    if summary.get("ledger_output_format") != "uncompressed_plain_jsonl_shards_with_manifest":
        issues.append("summary_not_plain_uncompressed_jsonl")
    if summary.get("condition_router_projection_gap_carried_forward_rows") != 0:
        issues.append("condition_router_projection_gap_carried_forward")
    if summary.get("prior_condition_router_projection_dependency") is not False:
        issues.append("summary_depends_on_prior_condition_router_projection")
    if summary.get("fixed_1_5r_role") != "baseline_comparator_and_fail_closed_fallback_only_not_live_default":
        issues.append("fixed_15r_reintroduced_as_default")
    if summary.get("global_momentum_role") != "diagnostic_global_counterfactual_not_launch_rule":
        issues.append("global_momentum_not_marked_diagnostic")
    if summary.get("live_dynamic_router_selection_mode") != "condition_asof_displacement_v1":
        issues.append("wrong_live_dynamic_router_mode")

    output_meta = (summary.get("outputs") or {}).get("final_dynamic_router_replay_ledger")
    if not output_meta:
        issues.append("missing_final_dynamic_router_output_meta")
        print(json.dumps({"status": "failed", "issue_count": len(issues), "issues": issues}, sort_keys=True))
        return 1
    if output_meta.get("plain_jsonl_shards") is not True or output_meta.get("compressed") is not False:
        issues.append("final_dynamic_router_output_not_plain_jsonl")
    manifest = REPO_ROOT / output_meta.get("manifest_path", "")
    if not manifest.exists():
        issues.append(f"missing_manifest:{output_meta.get('manifest_path')}")
        print(json.dumps({"status": "failed", "issue_count": len(issues), "issues": issues}, sort_keys=True))
        return 1
    check_plain_jsonl(manifest, issues)
    entries = [row for _, row in read_jsonl(manifest)]
    manifest_total = sum(int(entry.get("row_count", -1)) for entry in entries)
    if manifest_total != expected_rows:
        issues.append(f"manifest_row_count:{manifest_total}!={expected_rows}")
    if output_meta.get("row_count") != expected_rows:
        issues.append(f"output_meta_row_count:{output_meta.get('row_count')}!={expected_rows}")

    seen_ids: set[str] = set()
    policy_counts: Counter[str] = Counter()
    raw_policy_counts: Counter[str] = Counter()
    execution_policy_counts: Counter[str] = Counter()
    replay_class_counts: Counter[str] = Counter()
    m1_counts: Counter[str] = Counter()
    tick_counts: Counter[str] = Counter()
    non_replayable_count = 0
    router_refused_count = 0
    metric_count = 0
    router_metric = metric_bucket()
    comparison_metrics = {policy: metric_bucket() for policy in COMPARISON_FIELDS}
    regret_total = 0.0
    regret_rows = 0

    for entry in entries:
        shard = REPO_ROOT / entry.get("path", "")
        if not shard.exists():
            issues.append(f"missing_shard:{entry.get('path')}")
            continue
        check_plain_jsonl(shard, issues)
        shard_count = 0
        for _, row in read_jsonl(shard):
            shard_count += 1
            rid = row.get("selected_row_id")
            if not rid:
                issues.append("blank_selected_row_id")
            elif rid in seen_ids:
                issues.append(f"duplicate_selected_row_id:{rid}")
            else:
                seen_ids.add(str(rid))
            policy = row.get("chosen_policy")
            policy_counts[str(policy)] += 1
            if policy not in LIVE_POLICIES:
                issues.append(f"chosen_policy_not_live_supported:{rid}:{policy}")
            if policy == "fixed_1_5r":
                issues.append(f"fixed_15r_chosen_as_live_policy:{rid}")
            expected_policy_id = EXECUTION_POLICY_IDS.get(str(policy))
            if not row.get("execution_policy_id") or row.get("execution_policy_id") != expected_policy_id:
                issues.append(f"execution_policy_id_mismatch:{rid}:{policy}:{row.get('execution_policy_id')}")
            execution_policy_counts[str(row.get("execution_policy_id") or "missing")] += 1
            raw_policy_counts[str(row.get("raw_asof_selected_policy") or policy)] += 1
            if not isinstance(row.get("router_inputs"), dict) or not row["router_inputs"]:
                issues.append(f"missing_router_inputs:{rid}")
            else:
                for field in (
                    "framework",
                    "session_bucket",
                    "current_bar_displacement_atr14",
                    "liquidity_sweep_proxy_state",
                    "condition_challenger_enabled",
                ):
                    if field not in row["router_inputs"]:
                        issues.append(f"router_input_missing_{field}:{rid}")
            if row.get("router_candidate_use_allowed_now") is not True:
                router_refused_count += 1
                if not row.get("router_refusal_reasons"):
                    issues.append(f"router_refused_without_reasons:{rid}")
            if not row.get("fallback_conversion_reason"):
                issues.append(f"missing_fallback_conversion_reason:{rid}")
            if row.get("m1_availability_status") in (None, ""):
                issues.append(f"missing_m1_availability:{rid}")
            if row.get("tick_availability_status") in (None, ""):
                issues.append(f"missing_tick_availability:{rid}")
            m1_counts[str(row.get("m1_availability_status"))] += 1
            tick_counts[str(row.get("tick_availability_status"))] += 1
            replay_class = str(row.get("replay_source_class") or "")
            replay_class_counts[replay_class] += 1
            final_r = row.get("final_r")
            if final_r is None:
                non_replayable_count += 1
                if not row.get("non_replayable_reason"):
                    issues.append(f"non_replayable_without_reason:{rid}")
            else:
                metric_count += 1
                add_metric(router_metric, float(final_r))
            if not isinstance(row.get("missing_field_notes"), list) or not row["missing_field_notes"]:
                issues.append(f"missing_field_notes_not_row_level:{rid}")
            if not isinstance(row.get("cost_notes"), list) or not row["cost_notes"]:
                issues.append(f"missing_cost_notes:{rid}")
            for policy_name, field in COMPARISON_FIELDS.items():
                if field not in row:
                    issues.append(f"missing_comparison_field:{rid}:{field}")
                    continue
                value = row.get(field)
                if value is not None:
                    add_metric(comparison_metrics[policy_name], float(value))
            if row.get("hindsight_best_policy") in (None, "") and final_r is not None:
                issues.append(f"missing_hindsight_best_policy:{rid}")
            if row.get("hindsight_regret_r") is not None:
                regret_rows += 1
                regret_total += float(row["hindsight_regret_r"])
        if shard_count != int(entry.get("row_count", -1)):
            issues.append(f"shard_row_count:{entry.get('path')}:{shard_count}!={entry.get('row_count')}")

    if len(seen_ids) != expected_rows:
        issues.append(f"unique_selected_id_count:{len(seen_ids)}!={expected_rows}")
    if sum(policy_counts.values()) != expected_rows:
        issues.append(f"policy_distribution_total:{sum(policy_counts.values())}!={expected_rows}")
    if set(policy_counts) - LIVE_POLICIES:
        issues.append(f"unknown_chosen_policy_distribution:{dict(policy_counts)}")
    if router_refused_count != summary.get("router_refused_rows"):
        issues.append("router_refused_summary_mismatch")
    if router_refused_count != 0:
        issues.append(f"router_refused_rows_present:{router_refused_count}")
    if non_replayable_count != summary.get("non_replayable_rows"):
        issues.append("non_replayable_summary_mismatch")
    if metric_count != summary.get("replayable_metric_rows"):
        issues.append("metric_row_summary_mismatch")
    if policy_counts != Counter(summary.get("policy_distribution") or {}):
        issues.append("policy_distribution_summary_mismatch")
    if raw_policy_counts != Counter(summary.get("raw_asof_policy_distribution") or {}):
        issues.append("raw_policy_distribution_summary_mismatch")
    if execution_policy_counts != Counter(summary.get("execution_policy_id_distribution") or {}):
        issues.append("execution_policy_distribution_summary_mismatch")
    if m1_counts != Counter(summary.get("m1_availability_status_counts") or {}):
        issues.append("m1_availability_summary_mismatch")
    if tick_counts != Counter(summary.get("tick_availability_status_counts") or {}):
        issues.append("tick_availability_summary_mismatch")
    if replay_class_counts != Counter(summary.get("replay_source_class_counts") or {}):
        issues.append("replay_class_summary_mismatch")

    final_metrics = summary.get("final_dynamic_router_metrics") or {}
    if final_metrics.get("rows") != metric_count:
        issues.append("final_metrics_rows_mismatch")
    if not close_enough(final_metrics.get("total_r"), router_metric["total_r"]):
        issues.append(f"final_metrics_total_r_mismatch:{final_metrics.get('total_r')}!={router_metric['total_r']}")
    if final_metrics.get("wins") != router_metric["wins"]:
        issues.append("final_metrics_wins_mismatch")
    if final_metrics.get("losses") != router_metric["losses"]:
        issues.append("final_metrics_losses_mismatch")
    if final_metrics.get("breakevens") != router_metric["breakevens"]:
        issues.append("final_metrics_breakevens_mismatch")
    comparison_summary = summary.get("global_policy_comparison_metrics") or {}
    for policy, metrics in comparison_metrics.items():
        if policy not in comparison_summary:
            issues.append(f"missing_global_policy_comparison:{policy}")
            continue
        if not close_enough(comparison_summary[policy].get("total_r"), metrics["total_r"]):
            issues.append(f"comparison_total_r_mismatch:{policy}")
        if comparison_summary[policy].get("rows") != metrics["rows"]:
            issues.append(f"comparison_rows_mismatch:{policy}")
    regret = summary.get("hindsight_best_regret") or {}
    if regret.get("rows") != regret_rows:
        issues.append("hindsight_regret_rows_mismatch")
    if not close_enough(regret.get("total_regret_r"), regret_total):
        issues.append("hindsight_regret_total_mismatch")
    if not summary.get("distributions", {}).get("frequency_by_day"):
        issues.append("missing_frequency_by_day")
    if not summary.get("distributions", {}).get("frequency_by_week"):
        issues.append("missing_frequency_by_week")
    if not summary.get("distributions", {}).get("frequency_by_month"):
        issues.append("missing_frequency_by_month")
    for name in ("symbol", "session", "framework", "origin_family", "chosen_policy"):
        if not summary.get("distributions", {}).get(name):
            issues.append(f"missing_distribution:{name}")

    result = {
        "mode": "check" if args.check else "verify",
        "status": "passed" if not issues else "failed",
        "issue_count": len(issues),
        "issues": issues[:200],
        "selected_rows": expected_rows,
        "ledger_rows": len(seen_ids),
        "router_metric_rows": metric_count,
        "non_replayable_rows": non_replayable_count,
        "policy_distribution": dict(sorted(policy_counts.items())),
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
