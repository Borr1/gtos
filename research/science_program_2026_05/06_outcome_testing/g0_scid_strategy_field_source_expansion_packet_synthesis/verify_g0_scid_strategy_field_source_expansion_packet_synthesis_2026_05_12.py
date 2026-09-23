"""Verifier for the G0 SCID strategy-field packet synthesis route."""

from __future__ import annotations

import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"
DATE_TAG = "2026-05-12"
PREFIX = "G0_SCID_STRATEGY_FIELD_PACKET_SYNTHESIS"
ROUTE_ID = "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS"
EVIDENCE_CLASS = "G0_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_SYNTHESIS_CONTROL_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_STRATEGY_FIELD_PACKET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "ACCEPTED_G12_AUDIT_RECONCILIATION",
    "SOURCE_FIELD_READINESS_SYNTHESIS",
    "ROUTE_OPTION_RANKING_LEDGER",
    "ANTI_BOXING_ROUTE_DISCOVERY_LEDGER",
    "CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION",
    "CONSTRUCTIVE_LEARNING_ROUTE_EXPANSION_LEDGER",
    "FORBIDDEN_SURFACE_NO_LEAK_CONTINUITY_AUDIT",
    "DECISION_LEDGER",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
    "CLOSEOUT_VERIFICATION",
]
REQUIRED_PY = [
    "build_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py",
    "verify_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py",
    "test_g0_scid_strategy_field_source_expansion_packet_synthesis_2026_05_12.py",
]
PROMPT_FILES = [
    "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-12.md",
    "SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_ROUTE_GOAL_PROMPT_2026-05-12.md",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_ROUTE_GOAL_PROMPT_2026-05-12.md",
]
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "credentials_touched",
    "changes_live_trading_behavior",
]
REQUIRED_ROUTE_IDS = {
    "SCID_STRATEGY_SOURCE_FIELD_FORWARD_CAPTURE_IMPLEMENTATION_CONTRACT",
    "SCID_STRATEGY_FIELD_BROADER_HISTORICAL_SOURCE_SEARCH",
    "SCID_DIRECTION_AWARE_RESULT_DESIGN",
    "SCID_LTF_AND_ORDERFLOW_PROXY_SOURCE_EXPANSION",
    "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE",
}


def repo_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def route_json(stem: str) -> dict[str, Any]:
    return load_json(ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json")


def syntax_parse(paths: list[Path]) -> dict[str, Any]:
    failures = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{repo_path(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed_prefixes = (
        "research/science_program_2026_05/06_outcome_testing/g0_scid_strategy_field_source_expansion_packet_synthesis/",
        "research/science_program_2026_05/04_goal_prompts/SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_LTF_ORDERFLOW_PROXY_SOURCE_EXPANSION_ROUTE_GOAL_PROMPT_2026-05-12.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_DIRECTION_AWARE_RESULT_DESIGN_PREREGISTRATION_ROUTE_GOAL_PROMPT_2026-05-12.md",
        ".context/00_core/research_current_state.md",
        ".context/LIVE_STATE.md",
    )
    forbidden_live_prefixes = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")
    raw_blob_suffixes = (".scid", ".depth", ".parquet", ".csv", ".dly", ".bin", ".jsonl.gz")
    entries = []
    for line in proc.stdout.strip().splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in allowed_prefixes)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "forbidden_live_surface_path": scoped and path.startswith(forbidden_live_prefixes),
                "raw_market_blob_path": scoped and path.endswith(raw_blob_suffixes),
            }
        )
    scoped = [entry for entry in entries if entry["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "entries": entries,
        "scoped_entries": scoped,
        "no_forbidden_live_surface_in_scoped_entries": not any(row["forbidden_live_surface_path"] for row in scoped),
        "no_raw_market_blob_in_scoped_entries": not any(row["raw_market_blob_path"] for row in scoped),
    }


def write_verification(result: dict[str, Any]) -> None:
    VERIFICATION_RESULT.write_text(
        json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    if COMPLETION_AUDIT.exists():
        completion = load_json(COMPLETION_AUDIT)
        completion["standalone_verifier_ok"] = result["ok"]
        completion["standalone_verifier_failures"] = result["failures"]
        completion["can_mark_goal_complete"] = result["ok"]
        completion["completion_standard_satisfied"] = result["ok"]
        COMPLETION_AUDIT.write_text(
            json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )


def verify() -> dict[str, Any]:
    failures: list[str] = []

    for stem in REQUIRED_STEMS:
        json_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        md_path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.md"
        if not json_path.exists():
            failures.append(f"missing required json artifact: {repo_path(json_path)}")
        if not md_path.exists():
            failures.append(f"missing required markdown artifact: {repo_path(md_path)}")
    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing required python artifact: {name}")
    for name in PROMPT_FILES:
        if not (PROMPT_DIR / name).exists():
            failures.append(f"missing prompt bundle file: {repo_path(PROMPT_DIR / name)}")

    payloads: dict[str, dict[str, Any]] = {}
    for stem in REQUIRED_STEMS:
        path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
        if path.exists():
            payloads[stem] = load_json(path)

    for stem, payload in payloads.items():
        if payload.get("route_id") != ROUTE_ID:
            failures.append(f"{stem}: route_id mismatch")
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append(f"{stem}: evidence_class mismatch")
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem}: promotion_verdict not closed")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{stem}: {flag} is not false")

    if "ACCEPTED_G12_AUDIT_RECONCILIATION" in payloads:
        reconciliation = payloads["ACCEPTED_G12_AUDIT_RECONCILIATION"]
        checks = {row["check_id"]: row for row in reconciliation.get("exact_reconciliation_checks", [])}
        expected = {
            "g12_terminal_decision": "ACCEPT_AS_G12_SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_CONTROL_EVIDENCE_ONLY",
            "candidate_rows": 3014,
            "closure_rows": 3014,
            "closed_field_families": 3,
            "fail_closed_field_families": 7,
            "prospective_capture_field_families": 2,
            "forbidden_field_families": 1,
            "forbidden_result_key_hits": 0,
            "forbidden_broker_key_hits": 0,
        }
        for check_id, expected_value in expected.items():
            row = checks.get(check_id)
            if row is None:
                failures.append(f"missing reconciliation check: {check_id}")
            elif row.get("actual") != expected_value or row.get("expected") != expected_value or row.get("status") != "PASS":
                failures.append(f"reconciliation check failed: {check_id}")

    if "SOURCE_FIELD_READINESS_SYNTHESIS" in payloads:
        readiness = payloads["SOURCE_FIELD_READINESS_SYNTHESIS"]
        if readiness.get("accepted_packet_row_count") != 3014:
            failures.append("readiness: accepted row count mismatch")
        if readiness.get("result_design_ready") is not False:
            failures.append("readiness: result design should remain blocked")
        if len(readiness.get("closed_field_families", [])) != 3:
            failures.append("readiness: expected 3 closed families")
        if len(readiness.get("fail_closed_field_families", [])) != 7:
            failures.append("readiness: expected 7 fail-closed families")
        if len(readiness.get("prospective_capture_field_families", [])) != 2:
            failures.append("readiness: expected 2 prospective families")
        if readiness.get("representative_closure_row_count") != 3014:
            failures.append("readiness: representative closure row count mismatch")

    if "ROUTE_OPTION_RANKING_LEDGER" in payloads:
        ranking = payloads["ROUTE_OPTION_RANKING_LEDGER"]
        route_ids = {row["route_id"] for row in ranking.get("routes", [])}
        missing_routes = REQUIRED_ROUTE_IDS - route_ids
        if missing_routes:
            failures.append(f"ranking: missing required route ids {sorted(missing_routes)}")
        if ranking.get("rank_1_route") != "SCID_COMBINED_SOURCE_SEARCH_AND_FORWARD_CAPTURE_ROUTE":
            failures.append("ranking: rank_1_route mismatch")
        if len(ranking.get("routes", [])) < 10:
            failures.append("ranking: expected at least 10 route families")
        totals = [row["weighted_total_score"] for row in ranking.get("routes", [])]
        if totals != sorted(totals, reverse=True):
            failures.append("ranking: routes are not sorted by score descending")
        if len(ranking.get("selected_route_bundle", [])) != 3:
            failures.append("ranking: expected a three-prompt route bundle")

    if "ANTI_BOXING_ROUTE_DISCOVERY_LEDGER" in payloads:
        anti = payloads["ANTI_BOXING_ROUTE_DISCOVERY_LEDGER"]
        families = anti.get("outside_current_edge_route_families_considered", [])
        if len(families) < 12:
            failures.append("anti-boxing: expected at least 12 outside-current-edge route families")
        for phrase in ["current GTOS OB/FVG/breaker frameworks", "M15-only path view", "single source modality"]:
            if phrase not in anti.get("not_treated_as_limits", []):
                failures.append(f"anti-boxing: missing non-limit {phrase}")

    if "CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION" in payloads:
        capture = payloads["CAPTURE_ONLY_IMPLEMENTATION_ROUTE_SPECIFICATION"]
        groups = {row["field_group"] for row in capture.get("required_capture_field_groups", [])}
        required_groups = {
            "intended_side_direction",
            "intended_entry_reference",
            "intended_stop_reference",
            "intended_target_reference",
            "poi_type_bounds_source",
            "framework_setup_family",
            "lifecycle_fill_cancel_expiry_source_status",
            "lower_timeframe_asof_path_availability",
            "future_orderflow_depth_proxy_requirements",
            "adversarial_baseline_assignment",
        }
        if not required_groups.issubset(groups):
            failures.append(f"capture: missing groups {sorted(required_groups - groups)}")

    if "DECISION_LEDGER" in payloads:
        decision = payloads["DECISION_LEDGER"]
        if decision.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("decision: terminal decision mismatch")
        if decision.get("result_design_ready") is not False:
            failures.append("decision: result design should remain not ready")
        if decision.get("repair_g12_audit_required") is not False:
            failures.append("decision: repair g12 audit should not be required")

    if "COMPLETION_AUDIT" in payloads:
        completion = payloads["COMPLETION_AUDIT"]
        if completion.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("completion: terminal decision mismatch")
        if completion.get("can_mark_goal_complete") is not True:
            failures.append("completion: can_mark_goal_complete should be true before verifier update")
        checklist = completion.get("prompt_to_artifact_checklist", [])
        if len(checklist) < 12 or any(row.get("status") != "PASS" for row in checklist):
            failures.append("completion: prompt-to-artifact checklist incomplete")

    for name in PROMPT_FILES:
        path = PROMPT_DIR / name
        if path.exists():
            text = path.read_text(encoding="utf-8")
            required_phrases = [
                "NO_PROMOTION_VERDICT",
                "validation_safe=false",
                "outcome_review_opened=false",
                "live_effect=false",
                "Mandatory Preflight",
                "Required Saturation And Self-Red-Team",
                "Do not open validation execution",
                "broker account/order/history/deal/position evidence",
                "prompt/config/risk/safety/execution/canary/selector changes",
            ]
            for phrase in required_phrases:
                if phrase not in text:
                    failures.append(f"{name}: missing required phrase {phrase}")

    syntax = syntax_parse([ROUTE_DIR / name for name in REQUIRED_PY if (ROUTE_DIR / name).exists()])
    if not syntax["ok"]:
        failures.extend(syntax["failures"])

    git_status = scoped_git_status()
    if not git_status["no_forbidden_live_surface_in_scoped_entries"]:
        failures.append("scoped git status includes forbidden live-surface path")
    if not git_status["no_raw_market_blob_in_scoped_entries"]:
        failures.append("scoped git status includes raw market blob path")

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "failures": failures,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "terminal_decision": TERMINAL_DECISION if not failures else "REPAIR_G0_STRATEGY_FIELD_PACKET_SYNTHESIS_REQUIRED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "required_route_options_verified": sorted(REQUIRED_ROUTE_IDS),
        "prompt_bundle_verified": [repo_path(PROMPT_DIR / name) for name in PROMPT_FILES],
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    write_verification(result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
