"""Verifier for the G0 SCID neutral target control synthesis route."""

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
PREFIX = "G0_SCID_NEUTRAL_TARGET_SYNTHESIS"
ROUTE_ID = "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS"
EVIDENCE_CLASS = "G0_SCID_NEUTRAL_TARGET_CONTROL_SYNTHESIS_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_NEUTRAL_TARGET_SYNTHESIS_WITH_RANKED_NEXT_ROUTE"
NEXT_PROMPT = PROMPT_DIR / "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md"
VERIFICATION_RESULT = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
COMPLETION_AUDIT = ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json"

REQUIRED_STEMS = [
    "CONTEXT_ANCHOR",
    "DECISION_LEDGER",
    "ACCEPTED_EVIDENCE_RECONCILIATION",
    "NEUTRAL_BEHAVIOR_SYNTHESIS",
    "ANTI_BOXING_MECHANISM_REVIEW",
    "CONCENTRATION_DENOMINATOR_RISK_REVIEW",
    "NOT_COMPUTABLE_FAILURE_ANATOMY_SYNTHESIS",
    "FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER",
    "ROUTE_RANKING_LEDGER",
    "SATURATION_SELF_REDTEAM_PASS",
    "OUTPUT_MANIFEST",
    "COMPLETION_AUDIT",
]
REQUIRED_PY = [
    "build_g0_scid_neutral_target_control_synthesis_2026_05_12.py",
    "verify_g0_scid_neutral_target_control_synthesis_2026_05_12.py",
    "test_g0_scid_neutral_target_control_synthesis_2026_05_12.py",
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
        "research/science_program_2026_05/06_outcome_testing/g0_scid_neutral_target_control_synthesis/",
        "research/science_program_2026_05/04_goal_prompts/SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_GOAL_PROMPT_2026-05-12.md",
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
    if not NEXT_PROMPT.exists():
        failures.append(f"missing rank-1 next prompt: {repo_path(NEXT_PROMPT)}")

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

    if "ACCEPTED_EVIDENCE_RECONCILIATION" in payloads:
        checks = {
            row["check_id"]: row
            for row in payloads["ACCEPTED_EVIDENCE_RECONCILIATION"]["exact_reconciliation_checks"]
        }
        expected = {
            "g12_terminal_decision": "ACCEPT_AS_G12_SOURCE_SAFE_NEUTRAL_TARGET_EXECUTION_PACKET_CONTROL_EVIDENCE_ONLY",
            "candidate_rows": 3014,
            "sealed_rows": 2432,
            "stress_rows": 582,
            "terminal_statuses": 24112,
            "computable_rows": 20292,
            "fail_closed_not_computable_rows": 3820,
            "bounded_scid_segments_rehashed": 9,
            "target_row_hash_mismatches": 0,
            "target_value_mismatches": 0,
            "terminal_grid_recomputed_unique_keys": 24112,
            "terminal_grid_duplicate_keys": 0,
            "denominator_groups": 7,
        }
        for check_id, value in expected.items():
            row = checks.get(check_id)
            if row is None:
                failures.append(f"missing exact reconciliation check: {check_id}")
            elif row.get("actual") != value or row.get("expected") != value or row.get("status") != "PASS":
                failures.append(f"{check_id}: expected and actual did not pass as {value}")

    if "NEUTRAL_BEHAVIOR_SYNTHESIS" in payloads:
        neutral = payloads["NEUTRAL_BEHAVIOR_SYNTHESIS"]
        if len(neutral.get("availability_by_target_family_and_horizon", [])) != 8:
            failures.append("neutral behavior: expected 8 availability rows")
        excerpts = neutral.get("matrix_excerpts", {})
        for key in ["by_symbol", "by_session_bucket", "by_utc_hour", "by_denominator_group", "by_source_file"]:
            if not excerpts.get(key):
                failures.append(f"neutral behavior: missing matrix excerpt {key}")
        boundary = neutral.get("interpretation_boundary", "")
        for phrase in ["not R", "not PnL", "not win-rate", "not validation", "not strategy-edge"]:
            if phrase not in boundary:
                failures.append(f"neutral behavior boundary missing phrase: {phrase}")

    if "FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER" in payloads:
        field_ledger = payloads["FUTURE_SOURCE_FIELD_REQUIREMENT_LEDGER"]
        fields = {row["field_group"] for row in field_ledger.get("required_fields", [])}
        required_fields = {
            "direction_and_side",
            "entry_stop_target_references",
            "poi_type_bounds_and_setup_family",
            "lifecycle_fill_cancel_expiry_source_state",
            "orderflow_depth_proxy_context",
            "adversarial_baseline_assignment",
        }
        if not required_fields.issubset(fields):
            failures.append(f"source-field ledger missing required fields: {sorted(required_fields - fields)}")

    if "ROUTE_RANKING_LEDGER" in payloads:
        ranking = payloads["ROUTE_RANKING_LEDGER"]
        if ranking.get("rank_1_route") != "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET":
            failures.append("route ranking: rank_1_route mismatch")
        if ranking.get("rank_1_prompt_path") != repo_path(NEXT_PROMPT):
            failures.append("route ranking: rank_1_prompt_path mismatch")
        routes = ranking.get("routes", [])
        if len(routes) < 7:
            failures.append("route ranking: expected at least 7 ranked routes")
        if routes and routes[0].get("decision") != "ACTIVE_NEXT_ROUTE":
            failures.append("route ranking: rank 1 is not active next route")

    if "COMPLETION_AUDIT" in payloads:
        completion = payloads["COMPLETION_AUDIT"]
        if completion.get("terminal_decision") != TERMINAL_DECISION:
            failures.append("completion audit: terminal_decision mismatch")
        if completion.get("can_mark_goal_complete") is not True:
            failures.append("completion audit: can_mark_goal_complete not true")
        checklist = completion.get("prompt_to_artifact_checklist", [])
        if len(checklist) < 8 or any(row.get("status") != "PASS" for row in checklist):
            failures.append("completion audit: prompt-to-artifact checklist incomplete")

    if NEXT_PROMPT.exists():
        prompt_text = NEXT_PROMPT.read_text(encoding="utf-8")
        required_prompt_phrases = [
            "SCID_STRATEGY_FIELD_SOURCE_EXPANSION_PACKET_ONLY",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "outcome_review_opened=false",
            "live_effect=false",
            "Every `3,014` candidate row",
            "CLOSED_FROM_SOURCE",
            "FAIL_CLOSED_MISSING_SOURCE_FIELD",
            "PROSPECTIVE_CAPTURE_REQUIRED",
            "FORBIDDEN_IN_THIS_EVIDENCE_CLASS",
            "broker account/order/history/deal/position evidence",
            "no validation/strategy-edge/R/PnL/win-rate/expectancy/performance",
        ]
        for phrase in required_prompt_phrases:
            if phrase not in prompt_text:
                failures.append(f"rank-1 prompt missing required phrase: {phrase}")

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
        "terminal_decision": TERMINAL_DECISION if not failures else "REPAIR_G0_SYNTHESIS_REQUIRED",
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    write_verification(result)
    return result


if __name__ == "__main__":
    print(json.dumps(verify(), indent=2, sort_keys=True))
