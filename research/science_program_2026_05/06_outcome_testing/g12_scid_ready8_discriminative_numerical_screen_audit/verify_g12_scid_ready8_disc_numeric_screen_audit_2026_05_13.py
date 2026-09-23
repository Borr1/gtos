from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import build_g12_scid_ready8_disc_numeric_screen_audit_2026_05_13 as builder


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    with open(builder.io_path(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    with open(builder.io_path(path), "w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=True)
        handle.write("\n")


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    for key, expected in builder.SAFE_FLAGS.items():
        if payload.get(key) != expected:
            return False
    return True


def main() -> int:
    paths = builder.artifact_paths()
    required_keys = [
        "builder",
        "verifier",
        "tests",
        "decision",
        "recomputation",
        "repair",
        "completion",
        "focused",
        "next_prompt",
        "next_starter",
    ]
    missing = [key for key in required_keys if not builder.file_exists(paths[key])]

    decision = read_json(paths["decision"]) if builder.file_exists(paths["decision"]) else {}
    recomputation = read_json(paths["recomputation"]) if builder.file_exists(paths["recomputation"]) else {}
    repair = read_json(paths["repair"]) if builder.file_exists(paths["repair"]) else {}
    completion = read_json(paths["completion"]) if builder.file_exists(paths["completion"]) else {}
    focused = read_json(paths["focused"]) if builder.file_exists(paths["focused"]) else {}

    accepted_checks = recomputation.get("accepted_upstream_facts_recomputed", {})
    safe_checks = recomputation.get("safe_flag_recomputation", {})
    no_shortcut = recomputation.get("no_shortcut_recompute", {})
    g0_ledgers = recomputation.get("g0_large_ledger_recompute", {})

    checks = {
        "required_files_exist": not missing,
        "decision_terminal_accept": decision.get("terminal_decision") == builder.TERMINAL_DECISION,
        "recomputation_ok": recomputation.get("ok") is True,
        "all_accepted_fact_checks_pass": bool(accepted_checks) and all(accepted_checks.values()),
        "all_safe_checks_pass": bool(safe_checks) and all(safe_checks.values()),
        "rowset_hash_exact": accepted_checks.get("rowset_hash_exact") is True,
        "target_rows_exact": accepted_checks.get("target_rows_192896") is True,
        "computable_rows_exact": accepted_checks.get("computable_rows_162336") is True,
        "fail_closed_rows_exact": accepted_checks.get("fail_closed_rows_30560") is True,
        "candidate_level_full_population": accepted_checks.get("candidate_level_full_population") is True,
        "candidate_target_cells_full_population": accepted_checks.get("candidate_level_target_cells_full_population") is True,
        "explanation_backing_complete": accepted_checks.get("explanations_have_data_backing") is True,
        "data_backing_no_extra_ids": accepted_checks.get("data_backing_has_no_unowned_ids") is True,
        "no_explanation_performance_conversion": accepted_checks.get("no_explanation_performance_conversion") is True,
        "ambiguity_remaining_zero": accepted_checks.get("ambiguity_repairable_remaining_zero") is True,
        "no_shortcut_not_top_n": no_shortcut.get("top_n_or_compact_substitute_detected") is False,
        "large_ledger_line_counts_present": g0_ledgers.get("line_counts")
        == {
            "aggregate": 4561,
            "ambiguity": 8691,
            "candidate": 24112,
            "contrast": 3400,
            "data_backing": 17380,
            "explanation": 8689,
            "failure": 2161,
            "partition": 192,
        },
        "same_g12_remaining_zero": repair.get("same_g12_repairable_items_remaining") == 0,
        "same_g12_unanswered_zero": repair.get("same_g12_unanswered_audit_questions_remaining") == 0,
        "completion_all_requirements_satisfied": completion.get("all_prompt_requirements_satisfied") is True,
        "focused_tests_recorded_passed": focused.get("status") == "passed" and focused.get("returncode") == 0,
        "safe_flags_closed_in_outputs": all(
            safe_flags_closed(payload) for payload in [decision, recomputation, repair, completion, focused] if payload
        ),
        "next_g0_prompt_exists": builder.file_exists(paths["next_prompt"]),
        "next_g0_starter_exists": builder.file_exists(paths["next_starter"]),
    }

    issues = [name for name, ok in checks.items() if not ok]
    payload = {
        **builder.safe_base("verification_result"),
        "generated_at_utc": now_utc(),
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "missing_required_files": missing,
        "terminal_decision": decision.get("terminal_decision"),
        "can_mark_goal_complete": not issues,
        "same_g12_repairable_items_remaining": repair.get("same_g12_repairable_items_remaining"),
        "same_g12_unanswered_audit_questions_remaining": repair.get(
            "same_g12_unanswered_audit_questions_remaining"
        ),
        "required_paths": {key: builder.repo_path(path) for key, path in paths.items()},
    }
    write_json(paths["verification"], payload)
    builder.build_manifest()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
