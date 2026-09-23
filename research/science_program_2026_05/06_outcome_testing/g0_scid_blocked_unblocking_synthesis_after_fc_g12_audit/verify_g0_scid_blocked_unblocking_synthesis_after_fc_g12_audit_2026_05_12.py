from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path
from typing import Any


DATE = "2026-05-12"
PREFIX = "G0_SCID_BLOCKED_UNBLOCKING"
ROUTE_ID = "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT"
EVIDENCE_CLASS = "G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_AFTER_G12_FUTURE_CAPTURE_SOURCE_AUDIT_ONLY"
TERMINAL_DECISION = "ACCEPT_AS_G0_SCID_BLOCKED_CARD_UNBLOCKING_SYNTHESIS_WITH_RANKED_SOURCE_CONTROL_ROUTE_BUNDLE"

ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[4]
PROMPT_DIR = REPO_ROOT / "research" / "science_program_2026_05" / "04_goal_prompts"

JSON_STEMS = [
    "CONTEXT_ANCHOR",
    "DECISION_LEDGER",
    "ROUTE_RECONCILIATION_LEDGER",
    "RANKED_ROUTE_BUNDLE",
    "SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER",
    "DENOMINATOR_QUARANTINE_GATE_LEDGER",
    "SATURATION_SELF_RED_TEAM",
    "MANDATORY_INSTRUCTION_COVERAGE_AUDIT",
    "PARALLELIZATION_LEDGER",
    "NEXT_PROMPT_STARTER_LEDGER",
    "FOCUSED_TEST_RESULT",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
PYTHON_ARTIFACTS = [
    ROUTE_DIR / "build_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py",
    ROUTE_DIR / "verify_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py",
    ROUTE_DIR / "test_g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit_2026_05_12.py",
]
SAFE_FLAGS: dict[str, Any] = {
    "promotion_verdict": "NO_PROMOTION_VERDICT",
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_validation": False,
    "opens_result_scoring": False,
    "opens_strategy_edge_claims": False,
    "opens_ai_api": False,
    "opens_paid_or_vendor_access": False,
    "opens_broker_account_order_history_deal_position_evidence": False,
    "opens_live_restart": False,
    "opens_live_trading_behavior": False,
    "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
    "opens_raw_market_data_blob_commit": False,
    "opens_registry_edit": False,
    "opens_remote_push": False,
    "credentials_touched": False,
    "changes_trading_risk_safety_prompt_decision_behavior": False,
}
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g0_scid_blocked_unblocking_synthesis_after_fc_g12_audit/",
    "research/science_program_2026_05/04_goal_prompts/SCID_BLOCKED",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "run_agent.py")
RAW_SUFFIXES = {".scid", ".depth", ".parquet", ".zip", ".bin", ".dly"}


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}{suffix}"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: Any) -> None:
    path.write_text(
        f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n",
        encoding="utf-8",
    )


def syntax_parse(paths: list[Path]) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []
    for path in paths:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            failures.append({"issue": "syntax_error", "path": rel(path), "error": str(exc)})
    return failures


def git_status_check() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    rows = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        rows.append(
            {
                "raw": line,
                "path": path,
                "scoped": scoped,
                "forbidden_live_surface": path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "raw_market_blob": Path(path).suffix.lower() in RAW_SUFFIXES,
            }
        )
    return {
        "rows": rows,
        "unscoped_dirty_paths": [row["path"] for row in rows if not row["scoped"]],
        "forbidden_live_surface_paths": [row["path"] for row in rows if row["forbidden_live_surface"]],
        "raw_market_blob_paths": [row["path"] for row in rows if row["raw_market_blob"]],
    }


def update_completion(ok: bool, mark_focused_tests_ok: bool) -> None:
    verification_path = artifact_path("VERIFICATION_RESULT")
    focused_path = artifact_path("FOCUSED_TEST_RESULT")
    completion_path = artifact_path("COMPLETION_AUDIT")

    if focused_path.exists() and mark_focused_tests_ok:
        focused = read_json(focused_path)
        focused["focused_tests_ok"] = True
        focused["status"] = "PASSED_BY_PYTEST_AND_MARKED_BY_VERIFIER"
        write_json(focused_path, focused)
        write_md(focused_path.with_suffix(".md"), "Focused Test Result", focused)

    if completion_path.exists():
        completion = read_json(completion_path)
        for item in completion.get("prompt_to_artifact_checklist", []):
            if item["requirement"] == "standalone verifier passed":
                item["satisfied"] = ok
                item["evidence"] = rel(verification_path)
            if item["requirement"] == "focused tests passed" and mark_focused_tests_ok:
                item["satisfied"] = True
                item["evidence"] = rel(focused_path)
        completion["standalone_verifier_ok"] = ok
        if mark_focused_tests_ok:
            completion["focused_tests_ok"] = True
        missing = [item["requirement"] for item in completion.get("prompt_to_artifact_checklist", []) if not item["satisfied"]]
        completion["missing_incomplete_or_weakly_verified_requirements"] = missing
        completion["completion_standard_satisfied"] = not missing
        completion["can_mark_goal_complete"] = not missing
        write_json(completion_path, completion)
        write_md(completion_path.with_suffix(".md"), "Completion Audit", completion)


def verify(write: bool = True, mark_focused_tests_ok: bool = False, allow_focused_pending: bool = False) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    loaded: dict[str, Any] = {}

    for stem in JSON_STEMS:
        path = artifact_path(stem)
        md_path = artifact_path(stem, ".md")
        if not path.exists():
            failures.append({"issue": "missing_json_artifact", "path": rel(path)})
            continue
        loaded[stem] = read_json(path)
        if not md_path.exists():
            failures.append({"issue": "missing_markdown_artifact", "path": rel(md_path)})
        payload = loaded[stem]
        if payload.get("route_id") != ROUTE_ID:
            failures.append({"artifact": stem, "issue": "route_id_mismatch", "observed": payload.get("route_id")})
        if payload.get("evidence_class") != EVIDENCE_CLASS:
            failures.append({"artifact": stem, "issue": "evidence_class_mismatch", "observed": payload.get("evidence_class")})
        for flag, expected in SAFE_FLAGS.items():
            if payload.get(flag) != expected:
                failures.append(
                    {
                        "artifact": stem,
                        "issue": "safe_flag_mismatch",
                        "flag": flag,
                        "observed": payload.get(flag),
                        "expected": expected,
                    }
                )

    for path in PYTHON_ARTIFACTS:
        if not path.exists():
            failures.append({"issue": "missing_python_artifact", "path": rel(path)})
    failures.extend(syntax_parse([path for path in PYTHON_ARTIFACTS if path.exists()]))

    context = loaded.get("CONTEXT_ANCHOR", {})
    input_hashes = context.get("input_hashes", [])
    if len(input_hashes) < 10 or not all(row.get("exists") and row.get("sha256") for row in input_hashes):
        failures.append({"artifact": "CONTEXT_ANCHOR", "issue": "required_inputs_not_all_hashed"})
    if not all(row.get("read_this_session") for row in context.get("mandatory_context_reads_after_preflight", [])):
        failures.append({"artifact": "CONTEXT_ANCHOR", "issue": "mandatory_context_not_marked_read"})

    reconciliation = loaded.get("ROUTE_RECONCILIATION_LEDGER", {})
    if reconciliation.get("blocked32_card_count") != 32:
        failures.append({"artifact": "ROUTE_RECONCILIATION_LEDGER", "issue": "blocked32_count_not_32"})
    if reconciliation.get("blocked15_card_count") != 15:
        failures.append({"artifact": "ROUTE_RECONCILIATION_LEDGER", "issue": "blocked15_count_not_15"})
    if reconciliation.get("blocked17_card_count") != 17:
        failures.append({"artifact": "ROUTE_RECONCILIATION_LEDGER", "issue": "blocked17_count_not_17"})
    if reconciliation.get("capture_group_count") != 10:
        failures.append({"artifact": "ROUTE_RECONCILIATION_LEDGER", "issue": "capture_group_count_not_10"})
    if reconciliation.get("recovered_source_state_rows") != 1213:
        failures.append({"artifact": "ROUTE_RECONCILIATION_LEDGER", "issue": "recovered_rows_not_1213"})
    if len(reconciliation.get("card_route_rows", [])) != 32:
        failures.append({"artifact": "ROUTE_RECONCILIATION_LEDGER", "issue": "card_route_rows_not_32"})

    blocker = loaded.get("SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER", {})
    if blocker.get("unresolved_vague_blockers"):
        failures.append({"artifact": "SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER", "issue": "unresolved_vague_blockers_present"})
    if blocker.get("every_item_has_exact_next_requirement") is not True:
        failures.append({"artifact": "SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER", "issue": "not_every_item_has_exact_requirement"})
    if len(blocker.get("capture_group_rows", [])) != 10:
        failures.append({"artifact": "SAME_EVIDENCE_BLOCKER_PURSUIT_LEDGER", "issue": "capture_group_rows_not_10"})

    denominator = loaded.get("DENOMINATOR_QUARANTINE_GATE_LEDGER", {})
    if denominator.get("accepted_40_denominator_count") != 40:
        failures.append({"artifact": "DENOMINATOR_QUARANTINE_GATE_LEDGER", "issue": "accepted_40_count_not_40"})
    if denominator.get("accepted_40_result_denominator_unblocked_by_recovered_rows") is not False:
        failures.append({"artifact": "DENOMINATOR_QUARANTINE_GATE_LEDGER", "issue": "recovered_rows_unblock_denominator"})
    if denominator.get("blocked_cards_may_score_results_now") is not False:
        failures.append({"artifact": "DENOMINATOR_QUARANTINE_GATE_LEDGER", "issue": "blocked_cards_may_score_results"})

    ranked = loaded.get("RANKED_ROUTE_BUNDLE", {})
    routes = ranked.get("routes", [])
    if ranked.get("route_count", 0) < 8 or len(routes) < 8:
        failures.append({"artifact": "RANKED_ROUTE_BUNDLE", "issue": "route_count_less_than_8"})
    all_domains = {domain for route in routes for domain in route.get("domain_breadth", [])}
    required_domains = {"source-state", "lifecycle", "LTF", "orderflow/proxy", "baseline-control", "failure-anatomy", "non-OB", "cross-domain"}
    missing_domains = sorted(required_domains - all_domains)
    if missing_domains:
        failures.append({"artifact": "RANKED_ROUTE_BUNDLE", "issue": "missing_required_domain_breadth", "missing": missing_domains})
    if ranked.get("non_ob_cross_domain_routes_present") is not True:
        failures.append({"artifact": "RANKED_ROUTE_BUNDLE", "issue": "non_ob_cross_domain_flag_false"})

    prompts = loaded.get("NEXT_PROMPT_STARTER_LEDGER", {})
    prompt_pack = prompts.get("prompt_pack", [])
    if prompts.get("prompt_count") != len(routes) or prompts.get("starter_count") != len(routes):
        failures.append({"artifact": "NEXT_PROMPT_STARTER_LEDGER", "issue": "prompt_starter_count_mismatch"})
    if not all((REPO_ROOT / row["prompt_path"]).exists() and (REPO_ROOT / row["starter_path"]).exists() for row in prompt_pack):
        failures.append({"artifact": "NEXT_PROMPT_STARTER_LEDGER", "issue": "prompt_or_starter_missing"})
    if prompts.get("all_starters_one_physical_line") is not True:
        failures.append({"artifact": "NEXT_PROMPT_STARTER_LEDGER", "issue": "starter_not_one_line"})

    coverage = loaded.get("MANDATORY_INSTRUCTION_COVERAGE_AUDIT", {})
    for key in [
        "goal_session_research_discipline_read_after_preflight",
        "research_operating_doctrine_read_after_preflight",
        "research_current_state_read_after_preflight",
        "local_heavy_data_inventory_read_after_preflight",
        "ai_in_loop_cost_control_read_after_preflight",
        "forbidden_surfaces_preserved",
    ]:
        if coverage.get(key) is not True:
            failures.append({"artifact": "MANDATORY_INSTRUCTION_COVERAGE_AUDIT", "issue": f"{key}_not_true"})

    parallel = loaded.get("PARALLELIZATION_LEDGER", {})
    if len(parallel.get("can_run_in_parallel_after_current_g0_acceptance", [])) < 5:
        failures.append({"artifact": "PARALLELIZATION_LEDGER", "issue": "parallel_child_count_too_low"})

    saturation = loaded.get("SATURATION_SELF_RED_TEAM", {})
    if saturation.get("no_unresolved_tbd_unknown_maybe_later_placeholders") is not True:
        failures.append({"artifact": "SATURATION_SELF_RED_TEAM", "issue": "placeholder_flag_false"})
    if len(saturation.get("anti_boxing_questions_answered", [])) < 5:
        failures.append({"artifact": "SATURATION_SELF_RED_TEAM", "issue": "too_few_anti_boxing_questions"})

    decision = loaded.get("DECISION_LEDGER", {})
    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append({"artifact": "DECISION_LEDGER", "issue": "terminal_decision_mismatch"})
    if decision.get("terminal_blockers"):
        failures.append({"artifact": "DECISION_LEDGER", "issue": "terminal_blockers_present"})
    if not all(decision.get("check_map", {}).values()):
        failures.append({"artifact": "DECISION_LEDGER", "issue": "decision_check_map_not_all_true", "check_map": decision.get("check_map")})

    focused = loaded.get("FOCUSED_TEST_RESULT", {})
    if focused.get("focused_tests_ok") is not True and not (allow_focused_pending or mark_focused_tests_ok):
        failures.append({"artifact": "FOCUSED_TEST_RESULT", "issue": "focused_tests_not_marked_ok"})

    status = git_status_check()
    if status["unscoped_dirty_paths"]:
        failures.append({"issue": "unscoped_dirty_paths_present", "paths": status["unscoped_dirty_paths"]})
    if status["forbidden_live_surface_paths"]:
        failures.append({"issue": "forbidden_live_surface_dirty_paths", "paths": status["forbidden_live_surface_paths"]})
    if status["raw_market_blob_paths"]:
        failures.append({"issue": "raw_market_blob_dirty_paths", "paths": status["raw_market_blob_paths"]})

    ok = not failures
    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "ok": ok,
        "failure_count": len(failures),
        "failures": failures,
        "checked_json_artifact_count": len(JSON_STEMS),
        "checked_python_artifact_count": len(PYTHON_ARTIFACTS),
        "terminal_decision": TERMINAL_DECISION,
        "focused_tests_marked_ok": mark_focused_tests_ok,
        "git_status_check": status,
    }
    result.update(SAFE_FLAGS)

    if write:
        write_json(artifact_path("VERIFICATION_RESULT"), result)
        write_md(artifact_path("VERIFICATION_RESULT", ".md"), "Verification Result", result)
        update_completion(ok, mark_focused_tests_ok)
        if mark_focused_tests_ok and artifact_path("COMPLETION_AUDIT").exists():
            completion = read_json(artifact_path("COMPLETION_AUDIT"))
            result["completion_can_mark_goal_complete"] = completion.get("can_mark_goal_complete")
            write_json(artifact_path("VERIFICATION_RESULT"), result)
            write_md(artifact_path("VERIFICATION_RESULT", ".md"), "Verification Result", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--allow-focused-pending", action="store_true")
    args = parser.parse_args()
    result = verify(
        write=not args.no_write,
        mark_focused_tests_ok=args.mark_focused_tests_ok,
        allow_focused_pending=args.allow_focused_pending,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
