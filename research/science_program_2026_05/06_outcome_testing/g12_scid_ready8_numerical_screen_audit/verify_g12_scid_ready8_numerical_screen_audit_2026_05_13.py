from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


DATE = "2026-05-13"
ROUTE_ID = "G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT"
TERMINAL_DECISION = "ACCEPT_AS_G12_SCID_READY8_NUMERICAL_SCREEN_CONTROL_EVIDENCE_ONLY"

ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
PROMPT_DIR = ROOT / "research/science_program_2026_05/04_goal_prompts"
BUILDER_PATH = ROUTE_DIR / "build_g12_scid_ready8_numerical_screen_audit_2026_05_13.py"

SPEC = importlib.util.spec_from_file_location("g12_ready8_numeric_audit_builder", BUILDER_PATH)
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
        "decision": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_DECISION_LEDGER_{DATE}.json",
        "recomputation": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_RECOMPUTATION_LEDGER_{DATE}.json",
        "repair": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_REPAIR_LEDGER_{DATE}.json",
        "completion": ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_COMPLETION_AUDIT_{DATE}.json",
        "next_prompt": PROMPT_DIR / f"G0_SCID_READY8_NUMERICAL_SCREEN_LEARNING_SYNTHESIS_AFTER_G12_AUDIT_GOAL_PROMPT_{DATE}.md",
        "builder": BUILDER_PATH,
        "verifier": Path(__file__),
        "tests": ROUTE_DIR / "test_g12_scid_ready8_numerical_screen_audit_2026_05_13.py",
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

    if payloads.get("decision", {}).get("terminal_decision") != TERMINAL_DECISION:
        issues.append("terminal_decision_not_accept")
    if payloads.get("recomputation", {}).get("ok") is not True:
        issues.append("recomputation_not_ok")
    if payloads.get("repair", {}).get("issues_found_count") != 0:
        issues.append("repair_issues_not_zero")
    if payloads.get("completion", {}).get("can_mark_goal_complete") is not True:
        issues.append("completion_can_mark_goal_complete_not_true")

    target = payloads.get("recomputation", {}).get("target_population_recompute", {})
    candidate = payloads.get("recomputation", {}).get("candidate_example_recompute", {})
    ledger = payloads.get("recomputation", {}).get("g0_ledger_recompute_or_lossless_proof", {})
    checks = ledger.get("ledger_checks", {})
    count_expectations = {
        "source_candidates": target.get("unique_duplicate_proxy_denominator_key_count") == builder.EXPECTED_SOURCE_CANDIDATES,
        "ready_cards": len(builder.READY_CARDS) == builder.EXPECTED_READY_CARDS,
        "rowset_rows": target.get("unique_rowset_row_id_count") == builder.EXPECTED_ROWSET_ROWS,
        "candidate_rows": candidate.get("candidate_example_rows") == builder.EXPECTED_ROWSET_ROWS,
        "target_rows": target.get("target_result_row_count") == builder.EXPECTED_TARGET_ROWS,
        "horizons": sorted(int(item) for item in target.get("horizon_counts", {}).keys()) == builder.HORIZONS,
        "target_families": sorted(target.get("target_family_counts", {}).keys()) == sorted(builder.TARGET_FAMILIES),
    }
    failed_counts = [key for key, ok in count_expectations.items() if not ok]
    if failed_counts:
        issues.append(f"count_reconciliation_failed::{failed_counts}")

    if checks and not all(checks.values()):
        failed = [key for key, ok in checks.items() if not ok]
        issues.append(f"ledger_checks_failed::{failed}")

    if candidate.get("target_reference_set_equals_target_population") is not True:
        issues.append("candidate_target_reference_set_not_full_population")
    if candidate.get("top_n_or_sampling_rule_detected") is not False:
        issues.append("top_n_or_sampling_detected")

    storage = payloads.get("recomputation", {}).get("lfs_pointer_and_materialization_audit", {})
    if storage.get("oversized_normal_git_blob_count") != 0 or storage.get("large_jsonl_without_lfs_count") != 0:
        issues.append("large_blob_storage_check_failed")

    required_questions = payloads.get("completion", {}).get("required_audit_question_answers", [])
    if len(required_questions) != 15 or not all(item.get("satisfied") for item in required_questions):
        issues.append("required_question_answers_incomplete")

    output_dir_oversized = [
        rel(path)
        for path in ROUTE_DIR.glob("*")
        if path.is_file() and path.stat().st_size > 100_000_000
    ]
    if output_dir_oversized:
        issues.append(f"g12_output_dir_oversized_files::{output_dir_oversized}")

    result = {
        **builder.safe_base("verification_result"),
        "ok": not issues,
        "terminal_decision": payloads.get("decision", {}).get("terminal_decision"),
        "issues": issues,
        "required_paths": {name: rel(path) for name, path in paths.items()},
        "count_expectations": count_expectations,
        "ledger_checks_all_passed": bool(checks) and all(checks.values()),
        "required_question_answers_count": len(required_questions),
        "safe_flags_checked": True,
        "no_oversized_g12_output_files": not output_dir_oversized,
        "can_mark_goal_complete": not issues,
    }
    if write_result:
        write_json(ROUTE_DIR / f"G12_SCID_READY8_NUMERICAL_SCREEN_AUDIT_VERIFICATION_RESULT_{DATE}.json", result)
    return result


def main() -> None:
    result = verify(write_result=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
