from __future__ import annotations

import argparse
import json
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
EXPECTED_LANE02_ROWS = 289600
EXPECTED_FRIDAY_ROWS = 328


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def verify_route(route_dir: Path = ROUTE_DIR) -> dict:
    issues = []
    paths = {
        "timeline": route_dir / "LANE04_ROW_TIMELINE_LEDGER.jsonl",
        "strict": route_dir / "LANE04_STRICT_TICK_TIMELINE_LEDGER.jsonl",
        "source_gap": route_dir / "LANE04_SOURCE_GAP_LEDGER.jsonl",
        "anatomy": route_dir / "LANE04_ANATOMY_SPLIT_LEDGER.jsonl",
        "source_completeness": route_dir / "LANE04_SOURCE_COMPLETENESS_DECISION_LEDGER.jsonl",
        "dependency": route_dir / "LANE04_DEPENDENCY_STATE_LEDGER.jsonl",
        "decision": route_dir / "LANE04_IMPLEMENTATION_DECISION_LEDGER.jsonl",
        "summary": route_dir / "LANE04_EXPECTANCY_SUMMARY.json",
        "audit": route_dir / "LANE04_COMPLETION_AUDIT.json",
        "manifest": route_dir / "LANE04_OUTPUT_MANIFEST.json",
    }
    for name, path in paths.items():
        if not path.exists():
            issues.append(f"missing_output:{name}:{path.name}")
    if issues:
        return {"ok": False, "issue_count": len(issues), "issues": issues, "schema_version": "lane04_verification_result_v1"}

    timeline_rows = count_jsonl(paths["timeline"])
    expected_timeline = EXPECTED_LANE02_ROWS + EXPECTED_FRIDAY_ROWS
    if timeline_rows != expected_timeline:
        issues.append(f"timeline_row_count_expected_{expected_timeline}_actual_{timeline_rows}")
    strict_rows = count_jsonl(paths["strict"])
    if strict_rows <= 0:
        issues.append("strict_tick_timeline_missing_rows")
    if count_jsonl(paths["source_gap"]) <= 0:
        issues.append("source_gap_ledger_missing_rows")
    if count_jsonl(paths["anatomy"]) < 100:
        issues.append("anatomy_split_ledger_too_small")

    summary = read_json(paths["summary"])
    if summary.get("timeline_rows") != timeline_rows:
        issues.append("summary_timeline_rows_mismatch")
    if summary.get("lane02_rows") != EXPECTED_LANE02_ROWS:
        issues.append("summary_lane02_rows_mismatch")
    if summary.get("friday_rows") != EXPECTED_FRIDAY_ROWS:
        issues.append("summary_friday_rows_mismatch")
    strict_summary = summary.get("strict_tick") or {}
    if strict_summary.get("candidate_rows") != strict_rows:
        issues.append("strict_candidate_row_count_mismatch")
    if strict_summary.get("strict_tick_materialized_rows", 0) <= 0:
        issues.append("strict_tick_materialized_rows_missing")

    dep_rows = list(iter_jsonl(paths["dependency"]))
    required_absent = {
        "absolute_lane01_source_authority",
        "absolute_lane02_asof_contract",
        "absolute_lane03_candidate_reconstruction",
    }
    dep_names = {row.get("dependency_name") for row in dep_rows}
    missing_deps = sorted(required_absent - dep_names)
    if missing_deps:
        issues.append(f"missing_dependency_state_rows:{missing_deps}")

    decisions = list(iter_jsonl(paths["decision"]))
    if not any(row.get("decision") == "strict_tick_full_denominator_not_claimed" for row in decisions):
        issues.append("strict_tick_boundary_decision_missing")

    audit = read_json(paths["audit"])
    if audit.get("runtime_effect_boundary") != "offline_artifacts_only_no_broker_action_no_live_restart_no_config_change":
        issues.append("runtime_effect_boundary_missing_or_wrong")
    if audit.get("status") != "complete_for_current_approved_local_source_class_with_explicit_source_gaps":
        issues.append("audit_status_unexpected")

    return {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "timeline_rows": timeline_rows,
        "strict_tick_rows": strict_rows,
        "source_gap_rows": count_jsonl(paths["source_gap"]),
        "route_id": "vnext_moonshot_lane04_historical_microscope_engine_2026_06_01",
        "schema_version": "lane04_verification_result_v1",
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    result = verify_route()
    (ROUTE_DIR / "LANE04_VERIFICATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
