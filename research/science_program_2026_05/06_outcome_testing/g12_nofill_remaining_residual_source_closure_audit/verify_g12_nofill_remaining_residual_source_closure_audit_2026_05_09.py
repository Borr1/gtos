from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
LANE_DIR = Path(__file__).resolve().parent
DATE = "2026-05-09"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ACCEPT_XAU = "ACCEPT_AS_SOURCE_CONTROL_INPUT_ONLY_EVIDENCE"
ACCEPT_USDJPY = "ACCEPT_AS_SOURCE_IMPOSSIBILITY_EVIDENCE_ONLY"
TARGET_ROWS = [
    "NOFILL-CAT-ROW-0241",
    "NOFILL-CAT-ROW-0130",
    "NOFILL-CAT-ROW-0143",
    "NOFILL-CAT-ROW-0165",
    "NOFILL-CAT-ROW-0178",
]
MAY3_ROWS = {"NOFILL-CAT-ROW-0049", "NOFILL-CAT-ROW-0050", "NOFILL-CAT-ROW-0051"}

REQUIRED_FILES = [
    f"G12_NOFILL_REMAINING_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.md",
    f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json",
    f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.md",
    f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json",
    f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.md",
    f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json",
    f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.md",
    f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.json",
    f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.md",
    f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.json",
    f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.md",
    f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.json",
    f"G12_NOFILL_REMAINING_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.md",
    f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json",
    "build_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py",
    "verify_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py",
    "test_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py",
]
ALLOWED_WORKSPACE_PREFIXES = {
    "research/science_program_2026_05/06_outcome_testing/g12_nofill_remaining_residual_source_closure_audit/",
}
ALLOWED_WORKSPACE_FILES = {
    ".context/LIVE_STATE.md",
    ".context/00_core/research_current_state.md",
}
FORBIDDEN_LIVE_PREFIXES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)


def read_json(name: str) -> Any:
    return json.loads((LANE_DIR / name).read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    (LANE_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines)


def write_completion_markdown(completion: dict[str, Any], verification: dict[str, Any], run_external: bool) -> None:
    md = f"""# G12 NOFILL Remaining Completion Audit - {DATE}

Generated: `{completion["generated_at_utc"]}`

Objective restatement: {completion["objective_restatement"]}

Can mark complete after verifier: `{completion["can_mark_goal_complete_after_verifier"]}`.

## Prompt-To-Artifact Checklist

{markdown_table(completion["prompt_to_artifact_checklist"], ["requirement", "artifact", "status", "evidence"])}

## Missing, Incomplete, Or Weak Requirements

```json
{json.dumps(completion["missing_incomplete_or_weak_requirements"], indent=2, sort_keys=True)}
```

## Verification Result

- Verifier ok: `{str(verification["ok"]).lower()}`
- Issues: `{len(verification["issues"])}`
- Source hash records: `{verification["source_hash_record_count"]}`
- External checks enabled: `{str(run_external).lower()}`
"""
    (LANE_DIR / f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.md").write_text(
        md.rstrip() + "\n", encoding="utf-8"
    )


def normalize_status_path(line: str) -> str | None:
    if not line or line.lower().startswith("warning:") or len(line) < 4:
        return None
    path = line[3:].strip()
    if " -> " in path:
        path = path.split(" -> ", 1)[1].strip()
    return path.replace("\\", "/")


def git_lines(args: list[str]) -> list[str]:
    try:
        output = subprocess.check_output(args, cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_UNAVAILABLE:{exc!r}"]
    return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip() and not line.startswith("warning:")]


def git_status_paths() -> list[str]:
    try:
        output = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True, stderr=subprocess.STDOUT)
    except Exception as exc:
        return [f"GIT_STATUS_UNAVAILABLE:{exc!r}"]
    paths = []
    for line in output.splitlines():
        path = normalize_status_path(line)
        if path:
            paths.append(path)
    return paths


def git_head_diff_paths() -> list[str]:
    return git_lines(["git", "show", "--pretty=", "--name-only", "--diff-filter=ACMRT", "HEAD"])


def allowed_workspace_path(path: str) -> bool:
    return path in ALLOWED_WORKSPACE_FILES or any(path.startswith(prefix) for prefix in ALLOWED_WORKSPACE_PREFIXES)


def command_result(args: list[str], *, timeout: int = 120) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            env=env,
        )
        output = proc.stdout or ""
        return {
            "args": args,
            "returncode": proc.returncode,
            "ok": proc.returncode == 0,
            "output_tail": output[-4000:],
        }
    except Exception as exc:
        return {"args": args, "returncode": None, "ok": False, "error": repr(exc)}


def run_external_checks(enabled: bool) -> dict[str, Any]:
    if not enabled:
        return {"enabled": False, "py_compile": {"ok": None}, "focused_pytest": {"ok": None}, "ok": True}
    scripts = [
        str(LANE_DIR / "build_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py"),
        str(LANE_DIR / "verify_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py"),
        str(LANE_DIR / "test_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py"),
    ]
    py_compile = command_result([sys.executable, "-B", "-m", "py_compile", *scripts])
    pytest = command_result(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            str(LANE_DIR / "test_g12_nofill_remaining_residual_source_closure_audit_2026_05_09.py"),
            "--basetemp",
            str(ROOT / ".pytest_tmp_g12_nofill_remaining"),
        ],
        timeout=180,
    )
    return {
        "enabled": True,
        "py_compile": py_compile,
        "focused_pytest": pytest,
        "ok": bool(py_compile["ok"] and pytest["ok"]),
    }


def verify(*, run_external: bool = True, update_completion: bool = True) -> dict[str, Any]:
    issues: list[str] = []
    missing_files = [name for name in REQUIRED_FILES if not (LANE_DIR / name).exists()]
    if missing_files:
        issues.append(f"missing required files: {missing_files}")

    decision = read_json(f"G12_NOFILL_REMAINING_DECISION_LEDGER_{DATE}.json")
    xau = read_json(f"G12_NOFILL_REMAINING_XAUUSD_SOURCE_CONTROL_AUDIT_{DATE}.json")
    usdjpy = read_json(f"G12_NOFILL_REMAINING_USDJPY_IMPOSSIBILITY_AUDIT_{DATE}.json")
    source_hash = read_json(f"G12_NOFILL_REMAINING_SOURCE_HASH_RAW_CAPTURE_AUDIT_{DATE}.json")
    noleak = read_json(f"G12_NOFILL_REMAINING_NOLEAK_DUPLICATE_DENOMINATOR_LABEL_AUDIT_{DATE}.json")
    residual_verifier = read_json(f"G12_NOFILL_REMAINING_RESIDUAL_VERIFIER_AUDIT_{DATE}.json")
    completion = read_json(f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json")

    if decision["target_row_ids"] != TARGET_ROWS or decision["targeted_row_count"] != 5:
        issues.append("target rows/count mismatch")
    if set(decision["target_row_ids"]) & MAY3_ROWS or decision["may3_rows_reopened"]:
        issues.append("May 3 rows reopened")
    if decision["terminal_decision_counts"] != {ACCEPT_XAU: 1, ACCEPT_USDJPY: 4}:
        issues.append("terminal decision counts mismatch")
    if decision["upstream_status_counts"] != {
        "SOURCE_CONTROL_CLEARED_INPUT_ONLY": 1,
        "SOURCE_IMPOSSIBLE_FROM_APPROVED_ROUTES": 4,
    }:
        issues.append("upstream status counts mismatch")
    if not all(row["all_identity_fields_match_prior_blocker_lane"] for row in decision["row_decisions"]):
        issues.append("row identity mismatch against prior blocker lane")
    if any(row["validation_safe"] or row["outcome_review_opened"] or row["live_effect"] for row in decision["row_decisions"]):
        issues.append("unsafe true row flag found")
    if any(row["categorical_lifecycle_label"] is not None or row["cleared_into_accepted_denominator"] for row in decision["row_decisions"]):
        issues.append("row label or denominator moved")

    recovered = xau["g12_direct_recheck"]["recovered_may6_gap"]
    may5 = xau["g12_direct_recheck"]["may5_active_window"]
    if xau["g12_terminal_decision"] != ACCEPT_XAU:
        issues.append("XAU terminal decision mismatch")
    if recovered["window_rows"] != 549 or recovered["short_entry_touch_bid_ge_entry"]:
        issues.append("XAU recovered gap row count/touch mismatch")
    if recovered["max_bid"] >= recovered["entry_price"] or may5["max_bid"] >= may5["entry_price"]:
        issues.append("XAU max bid reached entry")
    if xau["upstream_packet_claim"]["mt5_read_only_capture"]["account_order_deal_position_history_calls"] != 0:
        issues.append("XAU capture reports forbidden account/order/history calls")
    if xau["upstream_packet_claim"]["mt5_read_only_capture"]["order_send_calls"] != 0:
        issues.append("XAU capture reports order_send calls")
    if xau["upstream_packet_claim"]["mt5_read_only_capture"]["paid_api_or_databento_calls"] != 0:
        issues.append("XAU capture reports paid/API/Databento calls")

    if usdjpy["g12_terminal_decision"] != ACCEPT_USDJPY or len(usdjpy["row_audits"]) != 4:
        issues.append("USDJPY terminal decision/count mismatch")
    if not all(row["same_tick_impossibility_holds"] for row in usdjpy["row_audits"]):
        issues.append("USDJPY same-tick impossibility row failed")
    for row in usdjpy["row_audits"]:
        exact = row["g12_source_recheck"]
        if exact["exact_timestamp_row_count"] != 1:
            issues.append(f"{row['packet_row_id']} exact row count != 1")
        exact_row = exact["exact_rows"][0]
        if not (exact_row["entry_touch"] and exact_row["protective_level"] and not exact_row["terminal_area"]):
            issues.append(f"{row['packet_row_id']} predicate truth mismatch")

    doc_checks = source_hash["official_mql5_raw_capture_audit"]["contract_checks"]
    required_doc_checks = [
        "mqltick_has_time_msc",
        "mqltick_has_flags",
        "mqltick_has_bid_ask",
        "copyticksrange_orders_rows_past_to_present",
        "copyticksrange_flags_describe_changed_fields",
        "python_returns_named_time_bid_ask_last_flags",
    ]
    if not all(doc_checks.get(key) for key in required_doc_checks):
        issues.append("official MQL5 doc contract checks incomplete")
    if doc_checks.get("sub_row_sequence_field_found"):
        issues.append("official MQL5 doc audit found an unexpected sequence field")
    if source_hash["g12_hash_manifest_audit"]["record_count"] != 35:
        issues.append("source hash manifest record count mismatch")
    if source_hash["g12_hash_manifest_audit"]["strict_hash_failures"]:
        issues.append("strict source hash failures present")

    if noleak["target_rows"] != TARGET_ROWS:
        issues.append("noleak target rows mismatch")
    if noleak["may3_rows_reopened"]:
        issues.append("noleak May 3 reopened rows non-empty")
    if noleak["reject_total_preserved_outside_labels_denominators"] != 65:
        issues.append("reject count mismatch")
    if noleak["rows_moved_to_accepted_denominator"] != 0:
        issues.append("denominator moved")
    if noleak["lifecycle_labels_assigned"] != 0 or noleak["result_or_performance_labels_assigned"] != 0:
        issues.append("label assigned")
    if noleak["boundary_scan"]["status"] != "PASS":
        issues.append("noleak boundary scan failed")

    if not all(residual_verifier["code_checks"].values()):
        issues.append("residual verifier code checks failed")

    workspace_paths = git_status_paths()
    disallowed_workspace = [path for path in workspace_paths if not allowed_workspace_path(path)]
    head_diff_paths = git_head_diff_paths()
    forbidden_head_diff = [path for path in head_diff_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    forbidden_workspace = [path for path in workspace_paths if path.startswith(FORBIDDEN_LIVE_PREFIXES)]
    if forbidden_head_diff:
        issues.append(f"forbidden live-surface HEAD diff paths: {forbidden_head_diff}")

    if update_completion:
        for item in completion["prompt_to_artifact_checklist"]:
            if item["requirement"] == "verifier/tests/py_compile/focused pytest":
                item["status"] = "PENDING_VERIFIER_RUN"
                item["evidence"] = "Verifier is about to run py_compile plus focused pytest."
        write_json(f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json", completion)

    external = run_external_checks(run_external)
    if not external["ok"]:
        issues.append("external py_compile/focused pytest check failed")

    ok = not issues
    verification = {
        "artifact_family": "G12_NOFILL_REMAINING_VERIFICATION",
        "ok": ok,
        "issues": issues,
        "missing_files": missing_files,
        "targeted_row_count": decision["targeted_row_count"],
        "terminal_decision_counts": decision["terminal_decision_counts"],
        "source_hash_record_count": source_hash["g12_hash_manifest_audit"]["record_count"],
        "xau_recovered_gap_rows": recovered["window_rows"],
        "usdjpy_rows_checked": len(usdjpy["row_audits"]),
        "workspace_paths_informational_only": workspace_paths,
        "disallowed_workspace_paths_informational_only": disallowed_workspace,
        "head_diff_paths": head_diff_paths,
        "forbidden_head_diff_paths": forbidden_head_diff,
        "forbidden_workspace_paths_informational_only": forbidden_workspace,
        "external_checks": external,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "can_mark_goal_complete": ok,
    }
    if update_completion:
        completion["verification"] = verification
        completion["can_mark_goal_complete_after_verifier"] = ok
        for item in completion["prompt_to_artifact_checklist"]:
            if item["requirement"] == "verifier/tests/py_compile/focused pytest":
                item["status"] = "PASS" if ok else "FAIL"
                item["evidence"] = "Verifier rechecked artifacts and ran py_compile plus focused pytest." if run_external else "Verifier rechecked artifacts without external checks."
        completion["missing_incomplete_or_weak_requirements"] = [] if ok else issues
        write_json(f"G12_NOFILL_REMAINING_COMPLETION_AUDIT_{DATE}.json", completion)
        write_completion_markdown(completion, verification, run_external)
    return verification


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-external", action="store_true", help="Skip py_compile and focused pytest subprocess checks.")
    parser.add_argument("--no-update", action="store_true", help="Do not update completion audit with verification results.")
    args = parser.parse_args()
    result = verify(run_external=not args.no_external, update_completion=not args.no_update)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
