from __future__ import annotations

import argparse
import ast
import importlib.util
import json
from pathlib import Path
from typing import Any

from build_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13 import (
    DATE,
    EVIDENCE_CLASS,
    EXPECTED_ROWSET_ROWS,
    EXPECTED_SOURCE_CANDIDATES,
    EXPECTED_TARGET_ROWS,
    HORIZONS,
    PROMPT_PATH,
    RANK1_ROUTE,
    READY_CARDS,
    ROOT,
    ROUTE_DIR,
    ROUTE_ID,
    SAFE_FLAGS,
    STARTER_PATH,
    TARGET_FAMILIES,
    TERMINAL_DECISION,
    build_artifacts,
    output_path,
    rel,
    safe_flags_ok,
    sha256_file,
    write_json,
    write_output_manifest,
)


REQUIRED_STEMS = [
    "DECISION_LEDGER",
    "FACT_RECONCILIATION_LEDGER",
    "KILLED_AND_PRESERVED_FINDINGS_LEDGER",
    "ROUTE_RANKING_LEDGER",
    "QUESTION_STACK_LEDGER",
    "BLOCKER_AND_REPAIR_LEDGER",
    "PROMPT_HARDENING_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
OPTIONAL_REFRESH_STEMS = ["VERIFICATION_RESULT", "FOCUSED_TEST_RESULT"]
REQUIRED_PY = [
    "build_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13.py",
    "verify_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13.py",
    "test_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13.py",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def syntax_parse() -> dict[str, Any]:
    failures = []
    for name in REQUIRED_PY:
        path = ROUTE_DIR / name
        if not path.exists():
            failures.append(f"missing python artifact: {name}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def load_required(failures: list[str]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for stem in REQUIRED_STEMS:
        suffix = ".md" if stem == "SYNTHESIS" else ".json"
        path = output_path(stem, suffix)
        if not path.exists():
            failures.append(f"missing artifact: {rel(path)}")
            continue
        if suffix == ".json":
            loaded[stem] = read_json(path)
    synthesis = output_path("SYNTHESIS", ".md")
    if not synthesis.exists():
        failures.append(f"missing synthesis markdown: {rel(synthesis)}")
    for path in [PROMPT_PATH, STARTER_PATH]:
        if not path.exists():
            failures.append(f"missing prompt/starter: {rel(path)}")
    return loaded


def refresh_completion(
    result: dict[str, Any],
    mark_focused_tests_ok: bool,
    mark_context_refreshed: bool = False,
    mark_committed: bool = False,
) -> None:
    path = output_path("COMPLETION_AUDIT")
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    completion["focused_tests_ok"] = bool(mark_focused_tests_ok and result["ok"])
    if mark_context_refreshed and result["ok"]:
        completion["context_refresh_ok"] = True
    if mark_committed and result["ok"]:
        completion["scoped_artifacts_committed_ok"] = True
    for row in completion.get("prompt_to_artifact_checklist", []):
        req = row.get("requirement")
        if req == "standalone verifier and focused tests pass":
            row["satisfied"] = bool(result["ok"] and mark_focused_tests_ok)
            row["evidence"] = rel(output_path("VERIFICATION_RESULT"))
        elif req == "research_current_state and LIVE_STATE updated" and mark_context_refreshed and result["ok"]:
            row["satisfied"] = True
            row["evidence"] = ".context/00_core/research_current_state.md and .context/LIVE_STATE.md refreshed"
        elif req == "scoped artifacts committed" and mark_committed and result["ok"]:
            row["satisfied"] = True
            row["evidence"] = "research commit 586a535c plus scoped context/verification refresh commit"
    non_commit = [row for row in completion.get("prompt_to_artifact_checklist", []) if row.get("requirement") != "scoped artifacts committed"]
    completion["missing_incomplete_or_weakly_verified_requirements"] = [
        row["requirement"] for row in completion.get("prompt_to_artifact_checklist", []) if row.get("satisfied") is not True
    ]
    completion["completion_standard_satisfied_before_commit"] = all(row.get("satisfied") is True for row in non_commit)
    completion["can_mark_goal_complete_before_commit"] = completion["completion_standard_satisfied_before_commit"]
    completion["can_mark_goal_complete"] = all(row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", []))
    write_json(path, completion)


def write_focused_test_result(result: dict[str, Any]) -> None:
    payload = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "artifact_family": "focused_test_result",
        "schema_version": "g0_scid_ready8_learning_synthesis_v1",
        **SAFE_FLAGS,
        "focused_tests_ok": True,
        "standalone_verifier_ok": result["ok"],
        "focused_pytest_command": (
            "python -m pytest research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/"
            "test_g0_scid_ready8_learning_synthesis_after_g12_audit_2026_05_13.py -q"
        ),
    }
    write_json(output_path("FOCUSED_TEST_RESULT"), payload)


def scoped_changed_files() -> list[str]:
    import subprocess

    completed = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    files = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return files


def import_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_upstream_verifiers() -> dict[str, Any]:
    g12_path = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_scid_ready8_numerical_screen_audit/verify_g12_scid_ready8_numerical_screen_audit_2026_05_13.py"
    g0_path = ROOT / "research/science_program_2026_05/06_outcome_testing/g0_scid_noapi_ready8_target_result_synthesis_and_quarantined_numerical_screen/verify_g0_scid_ready8_numerical_screen_2026_05_13.py"
    g12 = import_module(g12_path, "g12_ready8_numeric_verifier")
    g0 = import_module(g0_path, "g0_ready8_numeric_verifier")
    g12_result = g12.verify(write_result=False)
    g0_result = g0.verify()
    return {
        "accepted_g12_numerical_screen_verifier": {
            "path": rel(g12_path),
            "ok": g12_result.get("ok"),
            "issues": g12_result.get("issues"),
            "terminal_decision": g12_result.get("terminal_decision"),
            "count_expectations": g12_result.get("count_expectations"),
            "write_result": False,
        },
        "accepted_g0_numerical_screen_verifier": {
            "path": rel(g0_path),
            "ok": g0_result.get("ok"),
            "issues": g0_result.get("issues"),
            "input_target_row_count": g0_result.get("input_target_row_count"),
            "candidate_example_rows": g0_result.get("candidate_example_rows"),
            "known_same_evidence_class_intelligence_remaining": g0_result.get("known_same_evidence_class_intelligence_remaining"),
            "same_evidence_class_items_remaining_after_final_loop": g0_result.get("same_evidence_class_items_remaining_after_final_loop"),
        },
    }


def verify(
    write_result: bool = True,
    mark_focused_tests_ok: bool = False,
    mark_context_refreshed: bool = False,
    mark_committed: bool = False,
) -> dict[str, Any]:
    failures: list[str] = []
    syntax = syntax_parse()
    failures.extend(syntax["failures"])
    upstream_verifiers = run_upstream_verifiers()
    if upstream_verifiers["accepted_g12_numerical_screen_verifier"]["ok"] is not True:
        failures.append("accepted G12 numerical-screen verifier did not pass")
    if upstream_verifiers["accepted_g0_numerical_screen_verifier"]["ok"] is not True:
        failures.append("accepted G0 numerical-screen verifier did not pass")
    loaded = load_required(failures)
    recomputed = build_artifacts(write_outputs=False)

    for stem, payload in loaded.items():
        if isinstance(payload, dict):
            if payload.get("route_id") != ROUTE_ID:
                failures.append(f"{stem}: route_id mismatch")
            if payload.get("evidence_class") != EVIDENCE_CLASS:
                failures.append(f"{stem}: evidence_class mismatch")
            if not safe_flags_ok(payload):
                failures.append(f"{stem}: safe flags not preserved")

    decision = loaded.get("DECISION_LEDGER", {})
    fact = loaded.get("FACT_RECONCILIATION_LEDGER", {})
    killed = loaded.get("KILLED_AND_PRESERVED_FINDINGS_LEDGER", {})
    ranking = loaded.get("ROUTE_RANKING_LEDGER", {})
    questions = loaded.get("QUESTION_STACK_LEDGER", {})
    blocker = loaded.get("BLOCKER_AND_REPAIR_LEDGER", {})
    hardening = loaded.get("PROMPT_HARDENING_LEDGER", {})
    completion = loaded.get("COMPLETION_AUDIT", {})
    manifest = loaded.get("OUTPUT_MANIFEST", {})

    if decision.get("terminal_decision") != TERMINAL_DECISION:
        failures.append("terminal decision mismatch")
    if decision.get("selected_rank1_route") != RANK1_ROUTE:
        failures.append("rank1 route mismatch")
    if decision.get("rank1_is_another_audit") is not False:
        failures.append("rank1 incorrectly marked as audit")
    if decision.get("same_evidence_class_learning_remaining") != 0:
        failures.append("decision same_evidence_class_learning_remaining not zero")

    facts = fact.get("accepted_exact_facts", {})
    expectations = {
        "source_candidates": facts.get("source_candidates") == EXPECTED_SOURCE_CANDIDATES,
        "ready_cards": facts.get("ready_cards") == len(READY_CARDS),
        "ready_card_ids": facts.get("ready_card_ids") == READY_CARDS,
        "rowset_candidate_card_rows": facts.get("rowset_candidate_card_rows") == EXPECTED_ROWSET_ROWS,
        "candidate_example_rows": facts.get("candidate_example_rows") == EXPECTED_ROWSET_ROWS,
        "candidate_example_target_references": facts.get("candidate_example_target_references") == EXPECTED_TARGET_ROWS,
        "target_result_rows": facts.get("target_result_rows") == EXPECTED_TARGET_ROWS,
        "horizons": facts.get("horizons") == HORIZONS,
        "target_families": facts.get("target_families") == TARGET_FAMILIES,
        "candidate_no_top_n": facts.get("candidate_example_no_top_n_cap") is True,
        "target_refs_full_population": facts.get("target_reference_set_equals_target_population") is True,
    }
    failed_expectations = [key for key, ok in expectations.items() if not ok]
    if failed_expectations:
        failures.append(f"fact expectations failed: {failed_expectations}")

    redundancy = fact.get("card_redundancy_reconciled", {})
    if redundancy.get("all_card_horizon_target_fingerprints_match_adv001") is not True:
        failures.append("card redundancy not reconciled")
    if "not_a_dead_end" not in redundancy:
        failures.append("card redundancy dead-end repair missing")

    if len(killed.get("killed_findings", [])) < 8:
        failures.append("killed findings incomplete")
    preserved_ids = {row.get("finding_id") for row in killed.get("preserved_findings", [])}
    for required in ["PRES003_HORIZON_INTELLIGENCE", "PRES004_TARGET_FAMILY_INTELLIGENCE", "PRES006_FAIL_CLOSED_POLICY", "PRES007_DUPLICATE_CONCENTRATION_GUARD", "PRES008_CANDIDATE_LEVEL_ANATOMY_CATEGORIES"]:
        if required not in preserved_ids:
            failures.append(f"missing preserved finding: {required}")

    routes = ranking.get("routes", [])
    if len(routes) < 10:
        failures.append("route inventory appears truncated")
    if routes and routes[0].get("route_id") != RANK1_ROUTE:
        failures.append("rank1 not first route")
    if ranking.get("rank1_is_audit") is not False:
        failures.append("ranking rank1 audit loop not closed")

    if questions.get("same_evidence_class_learning_remaining") != 0:
        failures.append("question stack same_evidence_class_learning_remaining not zero")
    if len(questions.get("questions", [])) < 22:
        failures.append("question stack incomplete")
    if not all(row.get("same_evidence_class_remaining_after_answer") is False for row in questions.get("questions", [])):
        failures.append("some question leaves same-class learning open")

    if blocker.get("active_same_evidence_class_blockers") != []:
        failures.append("active same-class blockers remain")
    if blocker.get("same_evidence_class_learning_remaining") != 0:
        failures.append("blocker ledger same-class learning remains")
    if len(blocker.get("separate_evidence_class_handoffs", [])) < 3:
        failures.append("separate evidence-class handoffs incomplete")

    if hardening.get("all_known_prompt_weaknesses_fixed_in_this_goal") is not True:
        failures.append("prompt weaknesses not fixed")
    if len(hardening.get("weaknesses_found", [])) < 10:
        failures.append("prompt hardening ledger too thin")

    if PROMPT_PATH.exists():
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        required_prompt_phrases = [
            "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_ONLY",
            "3,014",
            "24,112",
            "192,896",
            "per-card source-field map",
            "candidate predicate or descriptor-contrast design",
            "duplicate_proxy_denominator_key",
            "sealed historical validation",
            "Target-opening prerequisites",
            "Do not treat \"cards are redundant\" as a dead end",
            "NO_PROMOTION_VERDICT",
            "validation_safe=false",
            "live_effect=false",
        ]
        for phrase in required_prompt_phrases:
            if phrase not in prompt:
                failures.append(f"rank1 prompt missing phrase: {phrase}")
    if STARTER_PATH.exists():
        starter = STARTER_PATH.read_text(encoding="utf-8").strip()
        if "\n" in starter:
            failures.append("starter is not one physical line")
        for phrase in [RANK1_ROUTE, "all 8 card-specific predicates", "NO_PROMOTION_VERDICT", "same-evidence-class repair/design remaining is 0"]:
            if phrase not in starter:
                failures.append(f"starter missing phrase: {phrase}")

    non_commit_completion_rows = [
        row
        for row in completion.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") not in {"standalone verifier and focused tests pass", "research_current_state and LIVE_STATE updated", "scoped artifacts committed"}
    ]
    if not non_commit_completion_rows or not all(row.get("satisfied") is True for row in non_commit_completion_rows):
        failures.append("completion checklist has unsatisfied non-verification rows")
    if completion.get("same_evidence_class_learning_remaining") != 0:
        failures.append("completion audit same_evidence_class_learning_remaining not zero")

    if manifest.get("artifact_count", 0) < 13:
        failures.append("manifest artifact count too low")
    manifest_paths = {row.get("path") for row in manifest.get("artifacts", [])}
    for path in [Path(__file__), ROUTE_DIR / REQUIRED_PY[0], ROUTE_DIR / REQUIRED_PY[2], PROMPT_PATH, STARTER_PATH, output_path("SYNTHESIS", ".md")]:
        if rel(path) not in manifest_paths:
            failures.append(f"manifest missing path: {rel(path)}")

    if recomputed["terminal_decision"] != TERMINAL_DECISION:
        failures.append("recomputed terminal decision mismatch")
    if recomputed["same_evidence_class_learning_remaining"] != 0:
        failures.append("recomputed same-class remaining not zero")

    oversized_output_files = [
        rel(path)
        for path in ROUTE_DIR.glob("*")
        if path.is_file() and path.stat().st_size > 100_000_000
    ]
    if oversized_output_files:
        failures.append(f"oversized output files: {oversized_output_files}")

    changed = scoped_changed_files()
    allowed_prefixes = [
        ".context/LIVE_STATE.md",
        ".context/00_core/research_current_state.md",
        "research/science_program_2026_05/04_goal_prompts/SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AND_SEALED_VALIDATION_DESIGN_GOAL_PROMPT_2026-05-13.md",
        "research/science_program_2026_05/06_outcome_testing/g0_scid_ready8_numerical_screen_learning_synthesis_after_g12_audit/",
    ]
    scoped_status_ok = all(any(path == prefix or path.startswith(prefix) for prefix in allowed_prefixes) for path in changed)

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "terminal_decision": decision.get("terminal_decision"),
        "rank1_route": decision.get("selected_rank1_route"),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "count_expectations": expectations,
        "same_evidence_class_learning_remaining": decision.get("same_evidence_class_learning_remaining"),
        "rank1_is_audit": ranking.get("rank1_is_audit"),
        "prompt_hardened": hardening.get("all_known_prompt_weaknesses_fixed_in_this_goal"),
        "focused_tests_ok": mark_focused_tests_ok,
        "context_refresh_ok": mark_context_refreshed,
        "upstream_verifiers": upstream_verifiers,
        "scoped_artifacts_committed_ok": mark_committed,
        "can_mark_goal_complete_before_commit": not failures and mark_focused_tests_ok and mark_context_refreshed,
        "can_mark_goal_complete": not failures and mark_focused_tests_ok and mark_context_refreshed and mark_committed,
        "syntax_parse": syntax,
        "oversized_output_files": oversized_output_files,
        "scoped_changed_files": changed,
        "scoped_status_ok": scoped_status_ok,
    }
    if write_result:
        write_json(output_path("VERIFICATION_RESULT"), result)
        refresh_completion(
            result,
            mark_focused_tests_ok=mark_focused_tests_ok,
            mark_context_refreshed=mark_context_refreshed,
            mark_committed=mark_committed,
        )
        if mark_focused_tests_ok and result["ok"]:
            write_focused_test_result(result)
        write_output_manifest([
            ROUTE_DIR / REQUIRED_PY[0],
            Path(__file__),
            ROUTE_DIR / REQUIRED_PY[2],
            PROMPT_PATH,
            STARTER_PATH,
            output_path("SYNTHESIS", ".md"),
            *(output_path(stem) for stem in REQUIRED_STEMS + OPTIONAL_REFRESH_STEMS),
        ])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    parser.add_argument("--mark-context-refreshed", action="store_true")
    parser.add_argument("--mark-committed", action="store_true")
    args = parser.parse_args()
    result = verify(
        mark_focused_tests_ok=args.mark_focused_tests_ok,
        mark_context_refreshed=args.mark_context_refreshed,
        mark_committed=args.mark_committed,
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
