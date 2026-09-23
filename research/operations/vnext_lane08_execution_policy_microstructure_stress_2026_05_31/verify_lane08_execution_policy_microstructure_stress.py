from __future__ import annotations

import argparse
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
POLICIES = {
    "fixed_1_5r",
    "be_after_trigger",
    "partial_be_runner",
    "momentum_exhaustion",
    "time_stop",
    "trailing_runner",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def count_jsonl(path: Path) -> int:
    return sum(1 for _ in iter_jsonl(path)) if path.exists() else 0


def verify_route(route_dir: Path = ROUTE_DIR) -> dict:
    issues = []
    paths = {
        "row": route_dir / "LANE08_POLICY_ROW_LEDGER.jsonl",
        "summary": route_dir / "LANE08_POLICY_SUMMARY_LEDGER.jsonl",
        "split": route_dir / "LANE08_POLICY_SPLIT_STRESS_LEDGER.jsonl",
        "micro": route_dir / "LANE08_MICROSTRUCTURE_STRESS_LEDGER.jsonl",
        "broker": route_dir / "LANE08_BROKER_CONSTRAINT_LEDGER.jsonl",
        "strict": route_dir / "LANE08_STRICT_TICK_POLICY_LEDGER.jsonl",
        "source": route_dir / "LANE08_SOURCE_COMPLETENESS_LEDGER.jsonl",
        "decision": route_dir / "LANE08_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "expectancy": route_dir / "LANE08_EXPECTANCY_SUMMARY.json",
        "audit": route_dir / "LANE08_COMPLETION_AUDIT.json",
        "manifest": route_dir / "LANE08_OUTPUT_MANIFEST.json",
    }
    for name, path in paths.items():
        if not path.exists():
            issues.append(f"missing_output:{name}:{path.name}")
    if issues:
        return {
            "ok": False,
            "issue_count": len(issues),
            "issues": issues,
            "schema_version": "lane08_verification_result_v1",
        }

    row_count = count_jsonl(paths["row"])
    if row_count != 289600:
        issues.append(f"policy_row_count_expected_289600_actual_{row_count}")

    summary_rows = list(iter_jsonl(paths["summary"]))
    summary_keys = {(row.get("denominator"), row.get("policy")) for row in summary_rows}
    for denominator in ("selected", "portfolio_ready"):
        for policy in POLICIES:
            if (denominator, policy) not in summary_keys:
                issues.append(f"missing_policy_summary:{denominator}:{policy}")

    expectancy = read_json(paths["expectancy"])
    if expectancy.get("input_rows") != row_count:
        issues.append("expectancy_input_rows_mismatch")
    expected_portfolio_ready = (
        ((expectancy.get("lane02_summary") or {}).get("stats") or {}).get("accepted_rows")
        or expectancy.get("portfolio_ready_rows")
    )
    if expectancy.get("portfolio_ready_rows") != expected_portfolio_ready:
        issues.append(
            f"portfolio_ready_rows_expected_{expected_portfolio_ready}_actual_{expectancy.get('portfolio_ready_rows')}"
        )
    micro_counts = expectancy.get("microstructure_realism_counts") or {}
    if "strict_tick_path_available_cost_lifecycle_missing" not in micro_counts:
        issues.append("strict_tick_microstructure_class_missing")
    if "m1_ordered_path_proxy_cost_lifecycle_missing" not in micro_counts:
        issues.append("m1_proxy_microstructure_class_missing")
    tick_counts = expectancy.get("tick_availability_counts") or {}
    tick_available = int(tick_counts.get("local_tick_parquet_available_for_entry_date") or 0)
    strict_count = count_jsonl(paths["strict"])
    strict_summary = expectancy.get("strict_tick_replay_summary") or {}
    if tick_available <= 0:
        issues.append("no_local_tick_available_rows_recorded")
    if strict_count != tick_available:
        issues.append(f"strict_tick_row_count_expected_{tick_available}_actual_{strict_count}")
    if strict_summary.get("candidate_rows") != tick_available:
        issues.append("strict_tick_candidate_count_mismatch")
    if strict_summary.get("geometry_joined_rows") != tick_available:
        issues.append("strict_tick_geometry_join_incomplete")
    if not strict_summary.get("strict_tick_replayed_rows"):
        issues.append("strict_tick_replayed_rows_missing")
    strict_policy_keys = {
        (row.get("denominator"), row.get("policy"))
        for row in strict_summary.get("policy_summary_by_denominator") or []
    }
    if ("selected", "momentum_exhaustion") not in strict_policy_keys:
        issues.append("strict_tick_selected_momentum_summary_missing")

    decisions = list(iter_jsonl(paths["decision"]))
    if not any(row.get("decision") == "patch_runtime_dynamic_sl_modify_failure_visibility" for row in decisions):
        issues.append("missing_dynamic_sl_modify_patch_decision")
    if not any(row.get("decision") == "strict_tick_full_denominator_not_claimed" for row in decisions):
        issues.append("missing_strict_tick_gap_decision")

    audit = read_json(paths["audit"])
    if audit.get("runtime_effect_boundary") != "local_code_and_offline_artifacts_only_no_broker_action_no_live_reload_no_config_change":
        issues.append("runtime_effect_boundary_missing_or_wrong")
    if not audit.get("open_source_gaps_not_hidden"):
        issues.append("source_gaps_not_recorded")

    if count_jsonl(paths["micro"]) < 100:
        issues.append("microstructure_stress_rows_too_small")
    if count_jsonl(paths["broker"]) < 24:
        issues.append("broker_constraint_rows_expected_24_or_more")
    if count_jsonl(paths["split"]) < 100:
        issues.append("split_stress_rows_too_small")

    result = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "input_rows": row_count,
        "portfolio_ready_rows": expectancy.get("portfolio_ready_rows"),
        "route_id": "vnext_lane08_execution_policy_microstructure_stress_2026_05_31",
        "schema_version": "lane08_verification_result_v1",
    }
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    result = verify_route()
    (ROUTE_DIR / "LANE08_VERIFICATION_RESULT.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
