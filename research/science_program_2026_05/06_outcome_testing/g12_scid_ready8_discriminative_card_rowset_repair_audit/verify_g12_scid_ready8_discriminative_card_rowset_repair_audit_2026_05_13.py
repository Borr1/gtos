from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_AUDIT"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_READY8_DISCRIMINATIVE_CARD_ROWSET_REPAIR_CONTROL_EVIDENCE_ONLY"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"
BUILDER_PATH = ROUTE_DIR / "build_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py"

SPEC = importlib.util.spec_from_file_location("g12_ready8_discriminative_audit_builder", BUILDER_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def required_paths() -> dict[str, Path]:
    return {
        "decision": ROUTE_DIR / f"G12_SCID_READY8_DISCRIMINATIVE_AUDIT_DECISION_LEDGER_{DATE}.json",
        "recomputation": ROUTE_DIR / f"G12_SCID_READY8_DISCRIMINATIVE_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
        "repair": ROUTE_DIR / f"G12_SCID_READY8_DISCRIMINATIVE_AUDIT_REPAIR_LEDGER_{DATE}.json",
        "completion": ROUTE_DIR / f"G12_SCID_READY8_DISCRIMINATIVE_AUDIT_COMPLETION_AUDIT_{DATE}.json",
        "next_prompt": PROMPT_DIR
        / f"G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_G12_AUDIT_GOAL_PROMPT_{DATE}.md",
        "next_starter": ROUTE_DIR
        / f"G0_SCID_READY8_DISCRIMINATIVE_SEALED_VALIDATION_OPENING_GATE_AFTER_G12_AUDIT_STARTER_{DATE}.txt",
        "builder": BUILDER_PATH,
        "verifier": Path(__file__),
        "tests": ROUTE_DIR / "test_g12_scid_ready8_discriminative_card_rowset_repair_audit_2026_05_13.py",
    }


def verify(write_result: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    paths = required_paths()
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        issues.append(f"missing_required_paths::{missing}")

    payloads: dict[str, Any] = {}
    for name in ("decision", "recomputation", "repair", "completion"):
        path = paths[name]
        if path.exists():
            payloads[name] = read_json(path)

    for name, payload in payloads.items():
        if not builder.safe_flags_ok(payload):
            issues.append(f"safe_flags_not_preserved::{name}")

    decision = payloads.get("decision", {})
    recomputation = payloads.get("recomputation", {})
    repair = payloads.get("repair", {})
    completion = payloads.get("completion", {})
    checks = recomputation.get("checks", {})
    rowset = recomputation.get("rowset_recompute", {})
    source = recomputation.get("source_candidate_recompute", {})
    ledger = recomputation.get("ledger_audit", {})

    if decision.get("terminal_decision") != TERMINAL_DECISION:
        issues.append("terminal_decision_not_accept")
    if recomputation.get("ok") is not True:
        issues.append("recomputation_not_ok")
    if repair.get("issues_found_count") != 0:
        issues.append("repair_issues_not_zero")
    if completion.get("can_mark_goal_complete") is not True:
        issues.append("completion_can_mark_goal_complete_not_true")
    if checks and not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        issues.append(f"recomputation_checks_failed::{failed}")

    count_expectations = {
        "source_candidates": source.get("valid_json_rows") == builder.EXPECTED_SOURCE_CANDIDATES,
        "unique_source_candidate_ids": source.get("unique_candidate_input_row_ids") == builder.EXPECTED_SOURCE_CANDIDATES,
        "rowset_rows": rowset.get("valid_json_rows") == builder.EXPECTED_ROWSET_ROWS,
        "rowset_hash": rowset.get("sha256")
        == recomputation.get("source_rowset_manifest_sha256", rowset.get("sha256"))
        or checks.get("rowset_hash_matches_manifest") is True,
        "ready_cards": rowset.get("ready_cards_present") == builder.READY_CARDS,
        "rows_per_card": all(
            rowset.get("card_counts", {}).get(card) == builder.EXPECTED_ROWS_PER_CARD
            for card in builder.READY_CARDS
        ),
        "fail_closed": rowset.get("fail_closed_rows") == builder.EXPECTED_FAIL_CLOSED_ROWS,
        "non_applicable": rowset.get("non_applicable_rows") == builder.EXPECTED_NON_APPLICABLE_ROWS,
        "descriptor_counts": all(
            rowset.get("per_card", {}).get(card, {}).get("descriptor_contrast_key_count", 0) > 1
            for card in builder.READY_CARDS
        ),
        "duplicate_keys": rowset.get("duplicate_proxy_denominator_key_count") == builder.EXPECTED_SOURCE_CANDIDATES,
        "target_verifier": recomputation.get("target_verifier_rerun", {}).get("passed") is True,
        "target_focused_tests": recomputation.get("target_focused_tests_rerun", {}).get("passed") is True,
        "ledger_audit": ledger.get("ok") is True,
    }
    failed_counts = [name for name, passed in count_expectations.items() if not passed]
    if failed_counts:
        issues.append(f"count_or_ledger_expectations_failed::{failed_counts}")

    required_questions = completion.get("required_audit_question_answers", [])
    if len(required_questions) != 17 or not all(item.get("satisfied") for item in required_questions):
        issues.append("required_audit_questions_incomplete")

    forbidden = recomputation.get("forbidden_surface_scan", {})
    if forbidden.get("rowset_forbidden_field_hits") or forbidden.get("source_candidate_forbidden_field_hits"):
        issues.append("forbidden_field_hits_present")
    if forbidden.get("target_artifact_safe_flags_closed") is not True:
        issues.append("target_artifact_safe_flags_not_closed")

    oversized_outputs = [
        rel(path)
        for path in ROUTE_DIR.glob("*")
        if path.is_file() and path.stat().st_size > 100_000_000
    ]
    if oversized_outputs:
        issues.append(f"g12_output_dir_oversized_files::{oversized_outputs}")

    result = {
        **builder.safe_base("verification_result"),
        "ok": not issues,
        "terminal_decision": decision.get("terminal_decision"),
        "issues": issues,
        "required_paths": {name: rel(path) for name, path in paths.items()},
        "count_expectations": count_expectations,
        "all_recomputation_checks_passed": bool(checks) and all(checks.values()),
        "required_question_answers_count": len(required_questions),
        "safe_flags_checked": True,
        "no_oversized_g12_output_files": not oversized_outputs,
        "can_mark_goal_complete": not issues,
    }
    if write_result:
        write_json(ROUTE_DIR / f"G12_SCID_READY8_DISCRIMINATIVE_AUDIT_VERIFICATION_RESULT_{DATE}.json", result)
    return result


def main() -> None:
    result = verify(write_result=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
