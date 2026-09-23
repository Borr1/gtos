"""Verifier for the G0 SCID anti-boxing child-route sequencing package."""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-13"
PREFIX = "G0_SCID_ANTI_BOXING"
EVIDENCE_CLASS = "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCING_ONLY"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
G12_ACCEPTANCE = "ACCEPT_AS_G12_SCID_ANTI_BOXING_ROUTE_INTAKE_CONTROL_EVIDENCE_ONLY"
TERMINAL_DECISION = "G0_SCID_ANTI_BOXING_CHILD_ROUTE_SEQUENCE_READY_NOT_LAUNCHED"

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "may_open_outcomes_or_results_in_this_route",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_trading_risk_safety_prompt_decision_behavior",
    "child_routes_launched",
]

REQUIRED_JSON_STEMS = [
    "CONTEXT_ANCHOR",
    "ROUTE_RANKING_LEDGER",
    "PARALLEL_WAVE_PLAN",
    "DEPENDENCY_LEDGER",
    "ADJACENT_ROUTE_FOLLOWUP_LEDGER",
    "ANTI_BOXING_SATURATION_LEDGER",
    "ONE_LINE_STARTERS_AND_COMMANDS",
    "NO_LEAK_FORBIDDEN_SURFACE_AUDIT",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]

REQUIRED_PY = [
    "build_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
    "verify_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
    "test_g0_scid_anti_boxing_child_route_sequencing_2026_05_13.py",
]

REQUIRED_CHILD_ROUTES = {
    "ADV-001",
    "MISS-001",
    "HAZ-001",
    "MICRO-001",
    "EXEC-002",
    "FAIL-001",
    "GEOM-TOPO-001",
    "ML-001",
    "BEH-001",
    "MACRO-004",
    "ADV-002",
    "ADV-004",
}

REQUIRED_DOMAINS = {
    "adversarial_baselines_placebos",
    "auction_microstructure_orderflow_liquidity",
    "behavioral_game_theory_session_participants",
    "execution_fillability_spread_slippage",
    "failure_anatomy_derived_hypotheses",
    "geometry_topology_path_shape",
    "macro_calendar_cross_asset",
    "ml_meta_labeling_uncertainty",
    "source_missingness_denominator_controls",
    "stochastic_tail_hazard",
}

FORBIDDEN_DIFF_PREFIXES = [
    "src/",
    "config/",
    "prompts/",
    "research/science_program_2026_05/04_goal_prompts/",
    "data/ticks/",
    "data/external/",
    "knowledge_base/trade_records/",
    "pipeline_state/",
    "shadow_logs/",
]

ALLOWED_DIFF_PREFIXES = [
    "research/science_program_2026_05/06_outcome_testing/g0_scid_anti_boxing_child_route_sequencing/",
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
]


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(stem: str) -> dict[str, Any]:
    path = ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def artifact_path(stem: str) -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}.json"


def check_safe_flags(payload: dict[str, Any], label: str, failures: list[str]) -> None:
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{label}: unexpected evidence_class={payload.get('evidence_class')}")
    if payload.get("promotion_verdict") != PROMOTION_VERDICT:
        failures.append(f"{label}: promotion_verdict not preserved")
    for flag in SAFE_FALSE_FLAGS:
        if payload.get(flag) is not False:
            failures.append(f"{label}: {flag} is not false")


def syntax_parse() -> dict[str, Any]:
    failures: list[str] = []
    for name in REQUIRED_PY:
        path = ROUTE_DIR / name
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{name}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def scoped_git_status() -> dict[str, Any]:
    proc = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    entries = []
    forbidden = []
    unscoped = []
    for raw_line in proc.stdout.splitlines():
        if not raw_line.strip():
            continue
        status = raw_line[:2].strip()
        path = raw_line[3:].replace("\\", "/") if len(raw_line) > 3 else raw_line.strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        is_forbidden = any(path.startswith(prefix) for prefix in FORBIDDEN_DIFF_PREFIXES)
        is_allowed = any(path.startswith(prefix) or path == prefix for prefix in ALLOWED_DIFF_PREFIXES)
        entry = {"status": status, "path": path, "allowed_scoped": is_allowed, "forbidden_surface": is_forbidden}
        entries.append(entry)
        if is_forbidden:
            forbidden.append(entry)
        if not is_allowed:
            unscoped.append(entry)
    return {
        "returncode": proc.returncode,
        "entries": entries,
        "forbidden_entries": forbidden,
        "unscoped_entries": unscoped,
        "stderr": proc.stderr.splitlines(),
    }


def verify(mark_focused_tests_ok: bool = False, write_result: bool = False) -> dict[str, Any]:
    failures: list[str] = []

    for stem in REQUIRED_JSON_STEMS:
        if not artifact_path(stem).exists():
            failures.append(f"missing json artifact {stem}")
    for name in REQUIRED_PY:
        if not (ROUTE_DIR / name).exists():
            failures.append(f"missing script/test {name}")
    md_path = ROUTE_DIR / f"{PREFIX}_SATURATION_SELF_RED_TEAM_{DATE_TAG}.md"
    if not md_path.exists():
        failures.append("missing saturation self-red-team markdown")
    if failures:
        result = {
            "artifact_family": "verification_result",
            "evidence_class": EVIDENCE_CLASS,
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
            "ok": False,
            "failures": failures,
            "can_mark_goal_complete": False,
        }
        if write_result:
            artifact_path("VERIFICATION_RESULT").write_text(
                json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        return result

    artifacts = {stem: load_json(stem) for stem in REQUIRED_JSON_STEMS}
    for stem, payload in artifacts.items():
        check_safe_flags(payload, stem, failures)

    context = artifacts["CONTEXT_ANCHOR"]
    ranking = artifacts["ROUTE_RANKING_LEDGER"]
    wave_plan = artifacts["PARALLEL_WAVE_PLAN"]
    dependency = artifacts["DEPENDENCY_LEDGER"]
    adjacent = artifacts["ADJACENT_ROUTE_FOLLOWUP_LEDGER"]
    saturation = artifacts["ANTI_BOXING_SATURATION_LEDGER"]
    starters = artifacts["ONE_LINE_STARTERS_AND_COMMANDS"]
    no_leak = artifacts["NO_LEAK_FORBIDDEN_SURFACE_AUDIT"]
    completion = artifacts["COMPLETION_AUDIT"]

    if context.get("accepted_g12_decision") != G12_ACCEPTANCE:
        failures.append("G12 terminal decision was not recomputed as accepted")
    if context.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("unexpected terminal decision")

    child_rows = ranking.get("ranked_child_routes", [])
    if len(child_rows) != 12:
        failures.append(f"ranked child route count is {len(child_rows)}, expected 12")
    route_ids = {row.get("route_family_id") for row in child_rows}
    if route_ids != REQUIRED_CHILD_ROUTES:
        failures.append(f"child route ids mismatch: {sorted(route_ids)}")
    ranks = sorted(row.get("sequence_rank") for row in child_rows)
    if ranks != list(range(1, 13)):
        failures.append(f"sequence ranks not 1..12: {ranks}")
    domains = {row.get("science_domain") for row in child_rows}
    if domains != REQUIRED_DOMAINS:
        failures.append(f"child route domains mismatch: {sorted(domains)}")
    if not ranking.get("ranking_is_broad_not_ob_boxed"):
        failures.append("ranking did not assert broad anti-boxing posture")

    if wave_plan.get("wave_count") != 4:
        failures.append("wave count not 4")
    wave_route_count = sum(wave.get("route_count", 0) for wave in wave_plan.get("waves", []))
    if wave_route_count != 12:
        failures.append(f"wave route count {wave_route_count} != 12")
    if dependency.get("same_class_sequencing_blockers_open") != []:
        failures.append("same-class sequencing blockers remain open")

    adjacent_rows = adjacent.get("adjacent_followup_rows", [])
    if adjacent.get("adjacent_followup_count") != 28:
        failures.append(f"adjacent followup count {adjacent.get('adjacent_followup_count')} != 28")
    if any(row.get("quarantine_status") != "QUARANTINED_ADJACENT_FOLLOWUP_NOT_IN_12_CHILD_PROMPT_PACKS" for row in adjacent_rows):
        failures.append("one or more adjacent rows not quarantined")

    if saturation.get("saturation_verdict") != "PASS_BROAD_SEQUENCE_NOT_BOXED_NOT_LAUNCHED":
        failures.append("anti-boxing saturation verdict did not pass")
    if not saturation.get("accepted_12_are_first_wave_not_horizon"):
        failures.append("accepted 12 not marked as first wave")

    if not starters.get("all_starters_one_physical_line"):
        failures.append("not all starters are one physical line")
    if not starters.get("all_starters_bind_controlling_prompt"):
        failures.append("not all starters bind controlling prompt")
    for wave in starters.get("wave_commands", []):
        for route in wave.get("routes", []):
            line = route.get("one_line_starter", "")
            if not line.startswith("/goal Follow the full controlling prompt in "):
                failures.append(f"starter for {route.get('route_family_id')} is malformed")
            if "\n" in line:
                failures.append(f"starter for {route.get('route_family_id')} contains newline")
            if "NO_PROMOTION_VERDICT" not in line:
                failures.append(f"starter for {route.get('route_family_id')} lacks safe flags")

    child_dir_checks = no_leak.get("child_route_dirs_absent_or_not_launched", [])
    existing_child_dirs = [row for row in child_dir_checks if row.get("exists")]
    if existing_child_dirs:
        failures.append(f"child route dirs already exist or were launched: {existing_child_dirs}")
    if not no_leak.get("forbidden_surfaces_closed"):
        failures.append("forbidden surfaces not closed")
    if not no_leak.get("all_route_rows_safe"):
        failures.append("not all child rows safe")
    if not no_leak.get("all_adjacent_rows_safe"):
        failures.append("not all adjacent rows safe")

    if not completion.get("all_checklist_items_satisfied_by_artifacts"):
        failures.append("completion audit checklist not satisfied")
    if completion.get("ranked_child_route_count") != 12:
        failures.append("completion audit child route count mismatch")
    if completion.get("adjacent_followup_count") != 28:
        failures.append("completion audit adjacent followup count mismatch")

    syntax = syntax_parse()
    failures.extend(syntax["failures"])

    git_status = scoped_git_status()
    if git_status["forbidden_entries"]:
        failures.append(f"forbidden scoped git entries: {git_status['forbidden_entries']}")
    if git_status["unscoped_entries"]:
        failures.append(f"unscoped git entries: {git_status['unscoped_entries']}")

    ok_without_tests = not failures
    can_mark_goal_complete = ok_without_tests and mark_focused_tests_ok
    result: dict[str, Any] = {
        "artifact_family": "verification_result",
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "may_open_outcomes_or_results_in_this_route": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_trading_risk_safety_prompt_decision_behavior": False,
        "child_routes_launched": False,
        "ok": ok_without_tests,
        "focused_tests_ok": mark_focused_tests_ok,
        "can_mark_goal_complete": can_mark_goal_complete,
        "failures": failures,
        "ranked_child_route_count_verified": len(child_rows),
        "adjacent_followup_count_verified": len(adjacent_rows),
        "domain_count_verified": len(domains),
        "wave_count_verified": wave_plan.get("wave_count"),
        "terminal_decision": TERMINAL_DECISION,
        "g12_terminal_decision_verified": context.get("accepted_g12_decision"),
        "same_class_sequencing_blockers_open": dependency.get("same_class_sequencing_blockers_open"),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }

    if write_result:
        artifact_path("VERIFICATION_RESULT").write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok, write_result=args.write_result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
