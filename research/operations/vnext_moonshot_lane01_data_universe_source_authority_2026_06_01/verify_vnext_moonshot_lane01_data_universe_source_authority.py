from __future__ import annotations

import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from build_vnext_moonshot_lane01_data_universe_source_authority import (
    ACTIVE_SYMBOLS,
    BROKER_FIELD_GROUPS,
    REQUIRED_TIMEFRAMES,
    ROUTE_DIR,
    ROUTE_ID,
    rel_path,
    refresh_manifest,
    utc_now,
)


REQUIRED_ARTIFACTS = [
    "DATA_SOURCE_INVENTORY.jsonl",
    "PARSER_CHECK_RESULTS.jsonl",
    "SOURCE_ACQUISITION_ATTEMPT_LEDGER.jsonl",
    "SOURCE_AUTHORITY_MAP.json",
    "SOURCE_GAP_LEDGER.jsonl",
    "SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
    "DEPENDENCY_STATE_LEDGER.jsonl",
    "LOCAL_REPO_VS_MT5_CACHE_COMPARISON.json",
    "DOWNSTREAM_SOURCE_CONTRACTS.json",
    "PARSER_CHECKER_REGISTRY.json",
    "RESULT_USE_STATUS.json",
    "BRANCH_DECISION_LEDGER.jsonl",
    "ROUTE_CONTEXT_ANCHOR.json",
    "COMPLETION_AUDIT.json",
    "OUTPUT_MANIFEST.json",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def git_dirty_summary() -> dict[str, Any]:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROUTE_DIR.parents[2], text=True, encoding="utf-8")
    except Exception as exc:
        return {"status_error": str(exc), "dirty_paths": []}
    dirty = [line for line in output.splitlines() if line.strip()]
    route_prefix = rel_path(ROUTE_DIR).replace("/", "\\")
    route_dirty = [line for line in dirty if line.replace("/", "\\").endswith(route_prefix) or route_prefix in line.replace("/", "\\")]
    return {
        "dirty_count": len(dirty),
        "route_dirty_count": len(route_dirty),
        "unrelated_dirty_count": len(dirty) - len(route_dirty),
        "note": "unrelated dirty worktree is informational only; verifier scopes assertions to route artifacts",
    }


def verify() -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    for name in REQUIRED_ARTIFACTS:
        path = ROUTE_DIR / name
        if not path.exists():
            issues.append({"severity": "error", "check": "required_artifact_exists", "path": name})

    if issues:
        return {"ok": False, "issue_count": len(issues), "issues": issues}

    inventory = load_jsonl(ROUTE_DIR / "DATA_SOURCE_INVENTORY.jsonl")
    parser_results = load_jsonl(ROUTE_DIR / "PARSER_CHECK_RESULTS.jsonl")
    gaps = load_jsonl(ROUTE_DIR / "SOURCE_GAP_LEDGER.jsonl")
    dependencies = load_jsonl(ROUTE_DIR / "DEPENDENCY_STATE_LEDGER.jsonl")
    authority = load_json(ROUTE_DIR / "SOURCE_AUTHORITY_MAP.json")
    contracts = load_json(ROUTE_DIR / "DOWNSTREAM_SOURCE_CONTRACTS.json")
    parser_registry = load_json(ROUTE_DIR / "PARSER_CHECKER_REGISTRY.json")
    result_use = load_json(ROUTE_DIR / "RESULT_USE_STATUS.json")
    comparison = load_json(ROUTE_DIR / "LOCAL_REPO_VS_MT5_CACHE_COMPARISON.json")

    if len(inventory) == 0:
        issues.append({"severity": "error", "check": "inventory_nonempty"})
    if len(parser_results) != len(inventory):
        issues.append(
            {
                "severity": "error",
                "check": "parser_result_count_matches_inventory",
                "inventory_rows": len(inventory),
                "parser_rows": len(parser_results),
            }
        )

    required_roots = {
        "repo_data",
        "shadow_logs",
        "pipeline_state",
        "knowledge_base",
        "mt5_local_cache_preservation_route",
        "vps_data_preservation_route",
        "friday_microscope_route",
        "live_companion_route",
        "absolute_master_route",
        "lane02_broad_selected",
        "lane04_selected_cell_risk",
        "lane06_broker_truth",
        "lane08_execution_policy",
        "activation_repair_hardening_route",
        "external_mt5_archive",
    }
    roots_present = {row.get("root_id") for row in inventory}
    missing_roots = sorted(required_roots - roots_present)
    if missing_roots:
        issues.append({"severity": "error", "check": "required_roots_in_inventory", "missing_roots": missing_roots})

    required_authorities = {
        "broker_real_truth",
        "mt5_market_history",
        "local_mt5_cache",
        "selected_denominator",
        "runtime_shadow_log",
        "replay_projection",
        "route_summary",
    }
    authority_present = {row.get("authority_level") for row in inventory}
    missing_authorities = sorted(required_authorities - authority_present)
    if missing_authorities:
        issues.append({"severity": "error", "check": "required_authority_classes_present", "missing": missing_authorities})

    market_gap_keys = {
        (row.get("symbol"), row.get("timeframe"))
        for row in gaps
        if row.get("gap_family") == "market_history_timeframe_coverage"
    }
    missing_market_gap_rows = [
        {"symbol": symbol, "timeframe": tf}
        for symbol in ACTIVE_SYMBOLS
        for tf in REQUIRED_TIMEFRAMES
        if (symbol, tf) not in market_gap_keys
    ]
    if missing_market_gap_rows:
        issues.append(
            {
                "severity": "error",
                "check": "all_symbol_timeframe_gap_rows_present",
                "missing_rows": missing_market_gap_rows[:20],
                "missing_count": len(missing_market_gap_rows),
            }
        )

    gap_families = {row.get("gap_family") for row in gaps}
    for family in BROKER_FIELD_GROUPS:
        if family not in gap_families:
            issues.append({"severity": "error", "check": "broker_gap_family_present", "missing_family": family})

    if "selected_denominator_tick_availability_status" not in gap_families:
        issues.append({"severity": "error", "check": "selected_tick_availability_gap_preserved"})
    if "selected_denominator_m1_availability_status" not in gap_families:
        issues.append({"severity": "error", "check": "selected_m1_availability_gap_preserved"})

    dependency_by_id = {row.get("dependency_id"): row for row in dependencies}
    master_row = dependency_by_id.get("absolute_master_route")
    if not master_row:
        issues.append({"severity": "error", "check": "absolute_master_dependency_state_recorded"})
    elif master_row.get("exists") is True:
        if master_row.get("dependency_state") != "present_consumed":
            issues.append(
                {
                    "severity": "error",
                    "check": "absolute_master_present_consumed",
                    "dependency_state": master_row.get("dependency_state"),
                }
            )
    elif master_row.get("dependency_state") != "absent_recorded_not_stop_condition":
        issues.append(
            {
                "severity": "error",
                "check": "absolute_master_absent_dependency_state",
                "dependency_state": master_row.get("dependency_state"),
            }
        )
    if not dependency_by_id.get("lane02_selected_denominator_counts", {}).get("selected_surface_rows"):
        issues.append({"severity": "error", "check": "lane02_counts_consumed"})

    contract_keys = set((contracts.get("contracts") or {}).keys())
    required_contracts = {
        "historical_microscope",
        "feature_store_v1",
        "label_store_v1",
        "broker_truth_cost_calibration",
        "digital_twin_replay_engine",
        "meta_selector_v2",
        "portfolio_scheduler_v2",
        "execution_policy_engine_v2",
        "ml_dataset_baseline_lab",
        "daily_learning_repair_companion",
        "command_center_production_dossier",
    }
    missing_contracts = sorted(required_contracts - contract_keys)
    if missing_contracts:
        issues.append({"severity": "error", "check": "downstream_contracts_complete", "missing": missing_contracts})

    parser_ids = {parser.get("parser_id") for parser in parser_registry.get("parsers", [])}
    required_parser_ids = {
        "csv_ohlc_time_series_v1",
        "parquet_tick_bid_ask_v1",
        "jsonl_runtime_route_ledger_v1",
        "json_summary_contract_v1",
        "mt5_native_cache_inventory_v1",
    }
    missing_parsers = sorted(required_parser_ids - parser_ids)
    if missing_parsers:
        issues.append({"severity": "error", "check": "parser_registry_required_ids", "missing": missing_parsers})

    parser_status_counts = Counter(row.get("parser_status") for row in parser_results)
    parser_error_rows = [
        {"path": row.get("path"), "parser_issue": row.get("parser_issue")}
        for row in parser_results
        if row.get("parser_status") == "error"
    ]
    if parser_error_rows:
        issues.append(
            {
                "severity": "error",
                "check": "parser_checks_no_errors",
                "error_count": len(parser_error_rows),
                "examples": parser_error_rows[:10],
            }
        )

    if result_use.get("lane01_owns_r_scoring") is not False:
        issues.append({"severity": "error", "check": "lane01_result_boundary"})
    if not result_use.get("expectancy_fields_consumed", {}).get("lane02_accepted_expectancy_r"):
        issues.append({"severity": "error", "check": "expectancy_metadata_consumed"})
    if not comparison.get("mt5_archive_manifest", {}).get("archive_sha256"):
        issues.append({"severity": "error", "check": "mt5_archive_manifest_consumed"})

    if authority.get("global_counts", {}).get("file_count") != len(inventory):
        issues.append({"severity": "error", "check": "authority_file_count_matches_inventory"})

    completion = load_json(ROUTE_DIR / "COMPLETION_AUDIT.json")
    ok = not any(issue["severity"] == "error" for issue in issues)
    completion["verification_ok"] = ok
    completion["can_mark_goal_complete"] = ok
    completion["verification_issue_count"] = len(issues)
    completion["verification_result_path"] = rel_path(ROUTE_DIR / "VERIFICATION_RESULT.json")
    if ok:
        completion["scoped_commit_status"] = "ready_for_scoped_commit_after_verification"
    with (ROUTE_DIR / "COMPLETION_AUDIT.json").open("w", encoding="utf-8", newline="\n") as f:
        json.dump(completion, f, indent=2, sort_keys=True)
        f.write("\n")

    result = {
        "schema_version": "lane01_verification_result_v1",
        "route_id": ROUTE_ID,
        "generated_at_utc": utc_now(),
        "ok": ok,
        "issue_count": len(issues),
        "issues": issues,
        "artifact_counts": {
            "inventory_rows": len(inventory),
            "parser_check_rows": len(parser_results),
            "gap_rows": len(gaps),
            "dependency_rows": len(dependencies),
            "contract_count": len(contract_keys),
        },
        "parser_status_counts": dict(parser_status_counts),
        "git_dirty_summary": git_dirty_summary(),
        "runtime_effect_boundary": "route-local source-authority verification only; no live broker operation or production activation",
    }
    with (ROUTE_DIR / "VERIFICATION_RESULT.json").open("w", encoding="utf-8", newline="\n") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    refresh_manifest()
    return result


def main() -> None:
    result = verify()
    print(json.dumps({"ok": result["ok"], "issue_count": result["issue_count"], "route_id": ROUTE_ID}, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
