#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


ROUTE = Path(__file__).resolve().parent
VERIFIED_SUPERVISION_STATUS = "verified_post_generation_route_verifier_and_tests_green"


def read_json(name: str) -> dict:
    return json.loads((ROUTE / name).read_text(encoding="utf-8-sig"))


def read_json_path(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                row["_line_no"] = line_no
                rows.append(row)
    return rows


def latest(pattern: str) -> Path | None:
    matches = sorted(ROUTE.glob(pattern), key=lambda path: path.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def active_supervision_completion_issues(supervision_completion: dict, supervision_reload: dict) -> list[str]:
    issues: list[str] = []
    if not supervision_completion:
        return issues
    if supervision_completion.get("broker_mutation_status") != "none":
        issues.append("active_supervision_unexpected_broker_mutation")
    if supervision_completion.get("runtime_effect_boundary") not in {
        "read_only_supervision_artifact_refresh_no_reload_no_broker_mutation",
        "controlled_book_worker_reload_no_broker_mutation",
    }:
        issues.append("active_supervision_unexpected_runtime_effect_boundary")
    if supervision_completion.get("runtime_effect_boundary") == "controlled_book_worker_reload_no_broker_mutation":
        if not supervision_reload or supervision_reload.get("ok") is not True:
            issues.append("active_supervision_reload_proof_missing_or_not_ok")
    if supervision_completion.get("instruction_coverage", {}).get("controlling_prompt_read") is not True:
        issues.append("active_supervision_instruction_coverage_missing_prompt")
    if len(supervision_completion.get("self_red_team") or []) < 5:
        issues.append("active_supervision_self_red_team_incomplete")
    if supervision_completion.get("ok") is not True:
        issues.append("active_supervision_completion_not_ok")
    if supervision_completion.get("verification_status") != VERIFIED_SUPERVISION_STATUS:
        issues.append("active_supervision_completion_verification_status_not_green")
    if supervision_completion.get("verification_status") == VERIFIED_SUPERVISION_STATUS:
        if not supervision_completion.get("verified_at_utc"):
            issues.append("active_supervision_completion_verified_at_missing")
        if not supervision_completion.get("verification_results"):
            issues.append("active_supervision_completion_verification_results_missing")
    return issues


def active_supervision_broker_snapshot_issues(supervision_broker: dict) -> list[str]:
    issues: list[str] = []
    for namespace, profile in (supervision_broker.get("profiles") or {}).items():
        query = profile.get("recent_deals_query") or {}
        if query.get("broker_offset_error"):
            issues.append(f"active_supervision_recent_deals_broker_offset_error:{namespace}")
        if query and query.get("offset_source") != "src.components.mt5_daemon_runtime.detect_broker_offset_seconds":
            issues.append(f"active_supervision_recent_deals_offset_source_unexpected:{namespace}")
        if query and "broker_offset_seconds" not in query:
            issues.append(f"active_supervision_recent_deals_offset_seconds_missing:{namespace}")
    return issues


def active_supervision_packet_chronology_issues(supervision_packet: dict) -> list[str]:
    issues: list[str] = []
    packet_log = supervision_packet.get("packet_log") or {}
    same_namespace_regressions = packet_log.get("same_namespace_append_order_regression_count")
    if same_namespace_regressions not in (None, 0):
        issues.append("active_supervision_same_namespace_append_order_regressions")
    append_regressions = int(packet_log.get("append_order_regression_count") or 0)
    class_counts = packet_log.get("append_order_regression_class_counts") or {}
    if append_regressions and sum(int(value or 0) for value in class_counts.values()) != append_regressions:
        issues.append("active_supervision_append_order_classification_count_mismatch")
    return issues


def main() -> int:
    issues: list[str] = []
    completion = read_json("COMPLETION_AUDIT.json")
    focused = read_json("FOCUSED_TEST_RESULT.json")
    manifest = read_json("OUTPUT_MANIFEST.json")
    slippage_focus = read_json("SLIPPAGE_RUNTIME_MERGE_FOCUSED_TEST_RESULT.json")
    slippage_cost = read_json("SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.json")
    broker_r = read_json("BROKER_R_RUNTIME_MERGE_COVERAGE.json")
    live_follow = read_json("LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.json")
    broker_detail = read_json("VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.json")
    broker_detail_focus = read_json("BROKER_PROFILE_MARKET_DETAIL_FOCUSED_TEST_RESULT.json")
    supervision_completion_path = ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json"
    supervision_completion = read_json_path(supervision_completion_path) if supervision_completion_path.exists() else {}
    supervision_broker = read_json_path(latest("VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_*.json")) if latest("VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_*.json") else {}
    supervision_packet = read_json_path(latest("VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_*.json")) if latest("VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_*.json") else {}
    supervision_profile = read_json_path(latest("VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_*.json")) if latest("VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_*.json") else {}
    supervision_reload_path = latest("VPS_ACTIVE_SUPERVISION_REPAIR_RELOAD_PROOF_*.json")
    supervision_reload = read_json_path(supervision_reload_path) if supervision_reload_path else {}

    if completion.get("repair_status") != "implemented_verified_reloaded":
        issues.append("repair_status_not_implemented_verified_reloaded")
    if completion.get("broker_runtime_mutation_status") != "no_order_deal_position_mutation_book_worker_reload_only":
        issues.append("unexpected_broker_runtime_mutation_status")
    if completion.get("config_hash_before") != completion.get("config_hash_after"):
        issues.append("config_hash_changed")
    if len(completion.get("closed_record_repairs") or []) != 2:
        issues.append("closed_record_repairs_count_not_2")
    if focused.get("all_passed") is not True:
        issues.append("focused_tests_not_all_passed")
    if manifest.get("ok") is not True:
        issues.append("manifest_not_ok")
    if slippage_focus.get("ok") is not True:
        issues.append("slippage_runtime_merge_focused_tests_not_ok")
    slippage_cost_rows = (slippage_cost.get("coverage") or {}).get("slippage_rows")
    broker_r_rows = (broker_r.get("coverage") or {}).get("slippage_rows")
    latest_slippage_rows = ((supervision_packet.get("slippage_stream") or {}).get("merged_row_count"))
    if latest_slippage_rows is not None:
        if slippage_cost_rows != latest_slippage_rows:
            issues.append("slippage_cost_runtime_merge_row_count_not_current")
        if broker_r_rows != latest_slippage_rows:
            issues.append("broker_r_runtime_merge_row_count_not_current")
    else:
        if not isinstance(slippage_cost_rows, int) or slippage_cost_rows < 7:
            issues.append("slippage_cost_runtime_merge_row_count_below_seed_7")
        if not isinstance(broker_r_rows, int) or broker_r_rows < 7:
            issues.append("broker_r_runtime_merge_row_count_below_seed_7")
    if broker_detail.get("ok") is not True:
        issues.append("broker_profile_market_detail_audit_not_ok")
    if broker_detail.get("issue_count") != 0:
        issues.append("broker_profile_market_detail_issue_count_not_0")
    profiles = broker_detail.get("profiles") or {}
    ftmo_summary = (profiles.get("operator_profile") or {}).get("summary") or {}
    funded_summary = (profiles.get("redacted_account") or {}).get("summary") or {}
    if ftmo_summary.get("supported_symbol_count") != 46:
        issues.append("broker_profile_market_detail_ftmo_supported_not_46")
    if funded_summary.get("supported_symbol_count") != 36:
        issues.append("broker_profile_market_detail_redacted_account_supported_not_36")
    if funded_summary.get("unexpected_unsupported_symbols") != []:
        issues.append("broker_profile_market_detail_redacted_account_unexpected_unsupported_not_empty")
    if broker_detail_focus.get("ok") is not True:
        issues.append("broker_profile_market_detail_focused_test_not_ok")
    follow_012 = next((row for row in live_follow.get("rows", []) if row.get("id") == "LIVE-FOLLOW-012"), None)
    if not follow_012:
        issues.append("missing_live_follow_012")
    else:
        files = follow_012.get("files") or []
        slippage_file = files[0] if files else {}
        follow_line_count = slippage_file.get("line_count")
        if latest_slippage_rows is not None:
            if follow_line_count != latest_slippage_rows:
                issues.append("live_follow_012_slippage_line_count_not_current")
        elif not isinstance(follow_line_count, int) or follow_line_count < 7:
            issues.append("live_follow_012_slippage_line_count_below_seed_7")
        if slippage_file.get("error") is not None:
            issues.append("live_follow_012_slippage_error_not_null")

    required_supervision_static = [
        "build_vps_active_supervision_repair_artifacts.py",
        "VPS_ACTIVE_SUPERVISION_REPAIR_CONTEXT_ANCHOR.md",
        "VPS_ACTIVE_SUPERVISION_REPAIR_CYCLE_LEDGER.jsonl",
        "VPS_ACTIVE_SUPERVISION_REPAIR_ISSUE_LEDGER.jsonl",
        "VPS_ACTIVE_SUPERVISION_REPAIR_ACTION_LEDGER.jsonl",
        "VPS_ACTIVE_SUPERVISION_REPAIR_SUBAGENT_LEDGER.jsonl",
        "VPS_ACTIVE_SUPERVISION_REPAIR_COMPLETION_OR_HANDOFF_AUDIT.json",
    ]
    for required in required_supervision_static:
        if not (ROUTE / required).exists():
            issues.append(f"missing_{required}")
    required_supervision_globs = [
        "VPS_ACTIVE_SUPERVISION_REPAIR_BROKER_SNAPSHOT_*.json",
        "VPS_ACTIVE_SUPERVISION_REPAIR_PACKET_CHRONOLOGY_AUDIT_*.json",
        "VPS_ACTIVE_SUPERVISION_REPAIR_PROFILE_DETAIL_AUDIT_*.json",
        "VPS_ACTIVE_SUPERVISION_REPAIR_LIMITATIONS_AND_OPPORTUNITIES_*.md",
    ]
    for pattern in required_supervision_globs:
        if latest(pattern) is None:
            issues.append(f"missing_{pattern}")
    issues.extend(active_supervision_completion_issues(supervision_completion, supervision_reload))
    if supervision_broker:
        if supervision_broker.get("broker_mutation_status") != "none":
            issues.append("active_supervision_broker_snapshot_mutation_status_not_none")
        if supervision_broker.get("ok") is not True:
            issues.append("active_supervision_broker_snapshot_not_ok")
        issues.extend(active_supervision_broker_snapshot_issues(supervision_broker))
    if supervision_packet:
        if supervision_packet.get("ok") is not True:
            issues.append("active_supervision_packet_audit_not_ok")
        packet_log = supervision_packet.get("packet_log") or {}
        if packet_log.get("validation_issue_count") != 0:
            issues.append("active_supervision_packet_validation_issues")
        issues.extend(active_supervision_packet_chronology_issues(supervision_packet))
        slippage_stream = supervision_packet.get("slippage_stream") or {}
        if slippage_stream.get("source_json_row_count") != slippage_stream.get("merged_row_count"):
            issues.append("active_supervision_slippage_source_count_mismatch")
        if slippage_stream.get("source_non_json_line_count", 0) > 0 and not any(
            row.get("non_json_lines_sampled") for row in slippage_stream.get("source_files") or []
        ):
            issues.append("active_supervision_slippage_non_json_not_sampled")
        consistency = ((supervision_packet.get("trade_records") or {}).get("active_consistency") or {})
        if any((consistency.get("broker_open_without_local_record") or {}).values()):
            issues.append("active_supervision_broker_open_without_local_record")
        if any((consistency.get("local_nonclosed_absent_from_broker") or {}).values()):
            issues.append("active_supervision_local_open_absent_from_broker")
        placement_ledger = supervision_packet.get("placement_ledger") or {}
        if placement_ledger.get("parse_error_count") not in (None, 0):
            issues.append("active_supervision_placement_ledger_parse_errors")
        if placement_ledger.get("incomplete_ticket_row_count") not in (None, 0):
            issues.append("active_supervision_placement_ledger_incomplete_ticket_rows")
        if placement_ledger and placement_ledger.get("ok") is not True:
            issues.append("active_supervision_placement_ledger_not_ok")
    if supervision_profile:
        if supervision_profile.get("ok") is not True:
            issues.append("active_supervision_profile_detail_not_ok")
        if supervision_profile.get("issue_count") != 0:
            issues.append("active_supervision_profile_detail_issues")
    subagent_path = ROUTE / "VPS_ACTIVE_SUPERVISION_REPAIR_SUBAGENT_LEDGER.jsonl"
    if subagent_path.exists():
        subagent_rows = read_jsonl(subagent_path)
        completed = [row for row in subagent_rows if row.get("status") == "completed"]
        if len(completed) < 5:
            issues.append("active_supervision_subagent_completed_rows_below_5")

    for required in [
        "VPS_ACTIVE_MONITORING_REPAIR_EVIDENCE.md",
        "COMPLETION_AUDIT.json",
        "DECISION_LEDGER.jsonl",
        "FOCUSED_TEST_RESULT.json",
        "OUTPUT_MANIFEST.json",
        "SATURATION_SELF_RED_TEAM_AUDIT.json",
        "NEXT_PROMPT.md",
        "VERIFICATION_RESULT.json",
        "SLIPPAGE_RUNTIME_MERGE_FOCUSED_TEST_RESULT.json",
        "SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.json",
        "SLIPPAGE_COST_RUNTIME_MERGE_COVERAGE.md",
        "BROKER_R_RUNTIME_MERGE_COVERAGE.json",
        "BROKER_R_RUNTIME_MERGE_COVERAGE.md",
        "LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.json",
        "LIVE_SHADOW_FOLLOWUP_RUNTIME_MERGE_COVERAGE.md",
        "VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.json",
        "VPS_BROKER_PROFILE_MARKET_DETAIL_AUDIT_2026_06_19.md",
        "BROKER_PROFILE_MARKET_DETAIL_FOCUSED_TEST_RESULT.json",
        "VPS_TO_MAC_RESEARCH_HANDOFF_2026_06_19.md",
        "MAC_RESEARCH_STARTER_2026_06_19.md",
    ]:
        if not (ROUTE / required).exists():
            issues.append(f"missing_{required}")

    result = {
        "schema": "gtos.vps_runtime_active_monitoring_repair.route_verifier_result.v1",
        "route": str(ROUTE),
        "issue_count": len(issues),
        "issues": issues,
        "ok": not issues,
    }
    (ROUTE / "VERIFICATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
