"""Verifier for the G0 READY8 discriminative result-opening gate."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
from pathlib import Path
from typing import Any

from build_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13 import (
    EVIDENCE_CLASS,
    EXPECTED_ROWSET_ROWS,
    EXPECTED_ROWSET_SHA256,
    EXPECTED_SOURCE_CANDIDATES,
    NEXT_PROMPT,
    NEXT_STARTER,
    PREFIX,
    READY_CARDS,
    ROOT,
    ROUTE_DIR,
    ROUTE_ID,
    SAFE_FLAGS,
    TERMINAL_OPEN,
    build_artifacts,
    git_status_snapshot,
    out,
    rel,
    sha256_file,
    write_json,
    write_output_manifest,
)


G12_VERIFIER = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "g12_scid_ready8_discriminative_card_rowset_repair_audit"
    / "verify_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py"
)

REQUIRED_JSON_STEMS = [
    "DECISION_LEDGER",
    "RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER",
    "DENOMINATOR_GATE_LEDGER",
    "NO_LEAK_AND_FORBIDDEN_SURFACE_GATE_LEDGER",
    "BLOCKER_AND_REPAIR_LEDGER",
    "COMPLETION_AUDIT",
    "OUTPUT_MANIFEST",
]
REQUIRED_MD_STEMS = ["ROUTE_DECISION_SYNTHESIS"]
REQUIRED_PY = [
    "build_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py",
    "verify_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py",
    "test_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def syntax_parse() -> dict[str, Any]:
    failures: list[str] = []
    for file_name in REQUIRED_PY:
        path = ROUTE_DIR / file_name
        if not path.exists():
            failures.append(f"missing python artifact: {rel(path)}")
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            failures.append(f"{rel(path)}: {exc}")
    return {"ok": not failures, "failures": failures, "method": "ast_parse_no_bytecode"}


def load_required(failures: list[str]) -> dict[str, Any]:
    loaded: dict[str, Any] = {}
    for stem in REQUIRED_JSON_STEMS:
        path = out(stem)
        if not path.exists():
            failures.append(f"missing json artifact: {rel(path)}")
            continue
        loaded[stem] = read_json(path)
    for stem in REQUIRED_MD_STEMS:
        path = out(stem, ".md")
        if not path.exists():
            failures.append(f"missing markdown artifact: {rel(path)}")
    for path in (NEXT_PROMPT, NEXT_STARTER):
        if not path.exists():
            failures.append(f"missing next prompt/starter: {rel(path)}")
    return loaded


def artifact_safe_flags_ok(stem: str, payload: dict[str, Any], failures: list[str]) -> None:
    if payload.get("route_id") != ROUTE_ID:
        failures.append(f"{stem}: route_id mismatch")
    if payload.get("evidence_class") != EVIDENCE_CLASS:
        failures.append(f"{stem}: evidence_class mismatch")
    for key, expected in SAFE_FLAGS.items():
        if payload.get(key) != expected:
            failures.append(f"{stem}: expected {key}={expected!r}, got {payload.get(key)!r}")


def rerun_g12_verifier_no_write() -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("g12_ready8_discriminative_verifier", G12_VERIFIER)
    if spec is None or spec.loader is None:
        return {"ok": False, "issues": [f"cannot load {rel(G12_VERIFIER)}"]}
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify(write_result=False)


def refresh_completion(result: dict[str, Any], mark_focused_tests_ok: bool) -> None:
    path = out("COMPLETION_AUDIT")
    completion = read_json(path)
    completion["standalone_verifier_ok"] = result["ok"]
    completion["standalone_verifier_failures"] = result["failures"]
    completion["focused_tests_ok"] = bool(mark_focused_tests_ok and result["ok"])
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "accepted G12 audit verifier rerun from disk":
            row["satisfied"] = result.get("accepted_g12_verifier_ok") is True
            row["evidence"] = rel(out("VERIFICATION_RESULT"))
        if row.get("requirement") == "new G0 verifier and focused tests pass":
            row["satisfied"] = bool(result["ok"] and mark_focused_tests_ok)
            row["evidence"] = rel(out("VERIFICATION_RESULT"))
    non_commit = [
        row
        for row in completion.get("prompt_to_artifact_checklist", [])
        if row.get("requirement") != "context refreshed and scoped commits made"
    ]
    completion["completion_standard_satisfied_before_commit"] = all(row.get("satisfied") is True for row in non_commit)
    completion["completion_standard_satisfied"] = all(
        row.get("satisfied") is True for row in completion.get("prompt_to_artifact_checklist", [])
    )
    completion["can_mark_goal_complete"] = completion["completion_standard_satisfied_before_commit"]
    write_json(path, completion)


def write_focused_test_result(result: dict[str, Any]) -> None:
    payload = {
        "route_id": ROUTE_ID,
        "schema_version": "g0_scid_ready8_discriminative_result_opening_gate_v1",
        "artifact_family": "focused_test_result",
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "focused_tests_ok": True,
        "standalone_verifier_ok": result["ok"],
        "focused_pytest_command": (
            "python -m pytest research/science_program_2026_05/06_outcome_testing/"
            "g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit/"
            "test_g0_scid_ready8_discriminative_result_opening_gate_after_g12_audit_2026_05_13.py -q"
        ),
    }
    write_json(out("FOCUSED_TEST_RESULT"), payload)


def refresh_output_manifest(result: dict[str, Any]) -> None:
    write_output_manifest()
    manifest_path = out("OUTPUT_MANIFEST")
    manifest = read_json(manifest_path)
    manifest["verification_result"] = {
        "path": rel(out("VERIFICATION_RESULT")),
        "ok": result["ok"],
        "failure_count": result["failure_count"],
        "can_mark_goal_complete": result["can_mark_goal_complete"],
    }
    manifest["artifacts"] = [
        {"path": row["path"], "sha256": sha256_file(ROOT / row["path"]), "bytes": (ROOT / row["path"]).stat().st_size}
        for row in manifest.get("artifacts", [])
        if (ROOT / row["path"]).exists()
    ]
    manifest["artifact_count"] = len(manifest["artifacts"])
    write_json(manifest_path, manifest)


def verify(write_result: bool = True, mark_focused_tests_ok: bool = False) -> dict[str, Any]:
    failures: list[str] = []
    syntax = syntax_parse()
    failures.extend(syntax["failures"])
    loaded = load_required(failures)
    recomputed = build_artifacts(write_outputs=False)
    g12_result = rerun_g12_verifier_no_write()
    if g12_result.get("ok") is not True:
        failures.append(f"accepted G12 verifier rerun failed: {g12_result.get('issues')}")

    for stem, payload in loaded.items():
        if isinstance(payload, dict):
            artifact_safe_flags_ok(stem, payload, failures)

    decision = loaded.get("DECISION_LEDGER", {})
    prereq = loaded.get("RESULT_OPENING_PREREQUISITE_FREEZE_LEDGER", {})
    denominator = loaded.get("DENOMINATOR_GATE_LEDGER", {})
    no_leak = loaded.get("NO_LEAK_AND_FORBIDDEN_SURFACE_GATE_LEDGER", {})
    blocker = loaded.get("BLOCKER_AND_REPAIR_LEDGER", {})
    completion = loaded.get("COMPLETION_AUDIT", {})
    manifest = loaded.get("OUTPUT_MANIFEST", {})

    if decision.get("terminal_decision") != TERMINAL_OPEN:
        failures.append("terminal decision did not open next discriminative result packet prompt")
    if decision.get("blockers"):
        failures.append(f"decision has blockers: {decision.get('blockers')}")
    if decision.get("result_scoring_opened_by_this_gate") is not False:
        failures.append("G0 gate opened result scoring")
    if recomputed["issues"]:
        failures.append(f"recomputed G0 evidence issues: {recomputed['issues']}")
    if recomputed["terminal_decision"] != decision.get("terminal_decision"):
        failures.append("recomputed terminal decision mismatch")

    bound = prereq.get("accepted_repaired_rowset", {})
    if bound.get("path") != (
        "research/science_program_2026_05/06_outcome_testing/"
        "scid_ready8_discriminative_card_rowset_repair_and_sealed_validation_design/"
        "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl"
    ):
        failures.append("prerequisite ledger does not bind repaired discriminative rowset path")
    if bound.get("sha256") != EXPECTED_ROWSET_SHA256:
        failures.append("prerequisite ledger rowset hash mismatch")
    if bound.get("candidate_universe_count") != EXPECTED_SOURCE_CANDIDATES:
        failures.append("candidate universe count mismatch")
    if bound.get("rowset_row_count") != EXPECTED_ROWSET_ROWS:
        failures.append("rowset row count mismatch")
    if prereq.get("target_family_horizon_freeze", {}).get("target_families") != [
        "neutral_close_to_close_return_m15_horizons_v1",
        "neutral_high_low_excursion_m15_horizons_v1",
    ]:
        failures.append("target families not frozen correctly")
    if prereq.get("target_family_horizon_freeze", {}).get("horizons_m15_bars") != [1, 4, 16, 32]:
        failures.append("target horizons not frozen correctly")
    if prereq.get("target_family_horizon_freeze", {}).get("previous_old_result_rows_reusable") is not False:
        failures.append("old target rows marked reusable")

    if denominator.get("status_counts", {}) != recomputed["rowset"]["status_counts"]:
        failures.append("denominator status counts do not match recomputed rowset")
    if denominator.get("role_counts", {}) != recomputed["rowset"]["role_counts"]:
        failures.append("denominator role counts do not match recomputed rowset")
    if denominator.get("denominator_integrity_checks", {}).get("fail_closed_as_pass_count") != 0:
        failures.append("fail-closed rows leak into pass role")
    if denominator.get("denominator_integrity_checks", {}).get("non_applicable_as_pass_count") != 0:
        failures.append("non-applicable rows leak into pass role")
    if "ADV-001" not in denominator.get("adversarial_control_cards", {}):
        failures.append("ADV-001 placebo-control rule missing")
    if "ADV-003" not in denominator.get("adversarial_control_cards", {}):
        failures.append("ADV-003 placebo-control rule missing")

    if no_leak.get("forbidden_field_scan_plan", {}).get("current_forbidden_row_field_hit_count") != 0:
        failures.append("forbidden row fields detected")
    if no_leak.get("asof_scan", {}).get("current_asof_violation_count") != 0:
        failures.append("as-of violations detected")
    if no_leak.get("safe_flags_preserved") is not True:
        failures.append("no-leak ledger does not preserve safe flags")

    if blocker.get("issues_found_count") != 0:
        failures.append("blocker ledger has unresolved issues")
    if blocker.get("no_same_g0_gate_intelligence_remaining") is not True:
        failures.append("blocker ledger does not assert same-G0 exhaustion")

    prompt = NEXT_PROMPT.read_text(encoding="utf-8") if NEXT_PROMPT.exists() else ""
    required_prompt_phrases = [
        "SCID_READY8_DISCRIMINATIVE_QUARANTINED_TARGET_RESULT_PACKET_ONLY",
        EXPECTED_ROWSET_SHA256,
        "SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_ROWS_2026-05-13.jsonl",
        "neutral_close_to_close_return_m15_horizons_v1",
        "neutral_high_low_excursion_m15_horizons_v1",
        "1`, `4`, `16`, and `32`",
        "ADV-001",
        "ADV-003",
        "NO_PROMOTION_VERDICT",
        "validation_safe=false",
        "live_effect=false",
        "must not be described as trading performance",
    ]
    for phrase in required_prompt_phrases:
        if phrase not in prompt:
            failures.append(f"next prompt missing phrase: {phrase}")
    for forbidden in [
        "SCID_NOAPI_READY8_ROWSET_ROWS_2026-05-12.jsonl",
        "7077a0f3fa3da2c854f2a0daab856d876992b927eb3228a161eb1cf02babb54d",
    ]:
        if forbidden in prompt:
            failures.append(f"next prompt still binds old redundant rowset artifact: {forbidden}")

    starter = NEXT_STARTER.read_text(encoding="utf-8").strip() if NEXT_STARTER.exists() else ""
    if "\n" in starter:
        failures.append("starter is not one physical line")
    if not starter.startswith("/goal Follow the full controlling prompt"):
        failures.append("starter missing /goal execution contract")
    for phrase in ["3014 source candidates", "24112 rowset rows", EXPECTED_ROWSET_SHA256, "NO_PROMOTION_VERDICT"]:
        if phrase not in starter:
            failures.append(f"starter missing phrase: {phrase}")

    checklist = completion.get("prompt_to_artifact_checklist", [])
    for row in checklist:
        if row.get("requirement") in {
            "accepted G12 audit verifier rerun from disk",
            "new G0 verifier and focused tests pass",
            "context refreshed and scoped commits made",
        }:
            continue
        if row.get("satisfied") is not True:
            failures.append(f"completion checklist unsatisfied: {row.get('requirement')}")
    if manifest.get("artifact_count", 0) < 10:
        failures.append("output manifest artifact count too low")

    git_status = git_status_snapshot()
    if git_status["forbidden_staged_paths"]:
        failures.append(f"forbidden staged paths: {git_status['forbidden_staged_paths']}")

    result = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        **SAFE_FLAGS,
        "terminal_decision": decision.get("terminal_decision"),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "can_mark_goal_complete": not failures and mark_focused_tests_ok,
        "focused_tests_ok": mark_focused_tests_ok,
        "accepted_g12_verifier_ok": g12_result.get("ok") is True,
        "accepted_g12_verifier_issues": g12_result.get("issues", []),
        "rowset_count_verified": recomputed["rowset"]["valid_json_rows"],
        "source_candidate_count_verified": recomputed["rowset"]["candidate_input_row_id_count"],
        "ready_card_ids_verified": recomputed["rowset"]["card_ids"],
        "rowset_hash_verified": recomputed["rowset"]["rowset_sha256"],
        "next_prompt_path": rel(NEXT_PROMPT),
        "next_starter_path": rel(NEXT_STARTER),
        "syntax_parse": syntax,
        "scoped_git_status": git_status,
    }
    if write_result:
        write_json(out("VERIFICATION_RESULT"), result)
        refresh_completion(result, mark_focused_tests_ok)
        if mark_focused_tests_ok and result["ok"]:
            write_focused_test_result(result)
        refresh_output_manifest(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mark-focused-tests-ok", action="store_true")
    args = parser.parse_args()
    result = verify(mark_focused_tests_ok=args.mark_focused_tests_ok)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
