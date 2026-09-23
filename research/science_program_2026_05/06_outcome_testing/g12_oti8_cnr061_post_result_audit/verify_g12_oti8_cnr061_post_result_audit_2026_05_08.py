#!/usr/bin/env python3
"""Verify G12 OTI8 CNR061 post-result audit artifacts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
BUILDER = BASE / "build_g12_oti8_cnr061_post_result_audit_2026_05_08.py"
VERIFIER = BASE / "verify_g12_oti8_cnr061_post_result_audit_2026_05_08.py"
TEST_FILE = BASE / "test_g12_oti8_cnr061_post_result_audit_2026_05_08.py"
COMPLETION_JSON = BASE / f"G12_OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"G12_OTI8_CNR061_COMPLETION_AUDIT_{DATE}.md"

OTI8 = ROOT / "research/science_program_2026_05/06_outcome_testing/oti8_cnr061_quarantined_results"
OTI8_VERIFIER = OTI8 / "verify_oti8_cnr061_quarantined_results_2026_05_08.py"
OTI8_COMPLETION = OTI8 / f"OTI8_CNR061_COMPLETION_AUDIT_{DATE}.json"
OTI8_ROWS = OTI8 / f"OTI8_CNR061_RESULT_LEDGER_{DATE}_ROWS.jsonl"

LIVE_SURFACE_PATHS = [
    "src",
    "prompts",
    "config",
    "scripts/canary",
    "scripts/canary_fixtures",
    "run_agent.py",
    "start_all.bat",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "stderr_tail": result.stderr.strip()[-4000:],
        "stdout_tail": result.stdout.strip()[-4000:],
    }


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_oti8_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_json_jsonl() -> dict[str, Any]:
    parsed_json = []
    for path in sorted(BASE.glob(f"G12_OTI8_CNR061_*_{DATE}.json")):
        json.loads(path.read_text(encoding="utf-8"))
        parsed_json.append(rel(path))
    oti8_row_count = 0
    with OTI8_ROWS.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                json.loads(line)
                oti8_row_count += 1
    return {
        "g12_json_files": parsed_json,
        "g12_json_count": len(parsed_json),
        "oti8_jsonl_rows_parsed": oti8_row_count,
        "status": "PASS" if len(parsed_json) >= 7 and oti8_row_count == 8 else "FAIL",
    }


def run_oti8_verifier_then_rebuild_g12() -> dict[str, Any]:
    oti8_result = run_command([sys.executable, str(OTI8_VERIFIER)])
    build_result = run_command([sys.executable, str(BUILDER)])
    completion = json.loads(OTI8_COMPLETION.read_text(encoding="utf-8"))
    status = (
        oti8_result["returncode"] == 0
        and build_result["returncode"] == 0
        and completion.get("verification_status") == "PASS"
        and completion.get("can_mark_goal_complete") is True
    )
    return {
        "g12_builder": build_result,
        "oti8_completion_can_mark_goal_complete": completion.get("can_mark_goal_complete"),
        "oti8_completion_verification_status": completion.get("verification_status"),
        "oti8_verifier": oti8_result,
        "status": "PASS" if status else "FAIL",
    }


def scan_generated_flags() -> dict[str, Any]:
    true_flag_hits = []
    wrong_promotion = []
    for path in sorted(BASE.glob(f"G12_OTI8_CNR061_*_{DATE}.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            wrong_promotion.append(rel(path))
        stack = [("$", payload)]
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    dotted = f"{prefix}.{key}"
                    if key in {"validation_safe", "outcome_review_opened", "live_effect"} and nested is True:
                        true_flag_hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    if key.endswith("_accessed") and nested is True:
                        true_flag_hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    if key.endswith("_calls") and nested not in {0, None}:
                        true_flag_hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    if key in {"order_calls", "paid_data_calls"} and nested not in {0, None}:
                        true_flag_hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    stack.append((dotted, nested))
            elif isinstance(value, list):
                for index, nested in enumerate(value):
                    stack.append((f"{prefix}[{index}]", nested))
    return {
        "forbidden_true_flag_hits": true_flag_hits,
        "missing_or_wrong_promotion_verdict": wrong_promotion,
        "status": "PASS" if not true_flag_hits and not wrong_promotion else "FAIL",
    }


def check_core_audits() -> dict[str, Any]:
    source = json.loads((BASE / f"G12_OTI8_CNR061_SOURCE_HASH_NOLEAK_AUDIT_{DATE}.json").read_text(encoding="utf-8"))
    duplicate = json.loads((BASE / f"G12_OTI8_CNR061_DUPLICATE_LABEL_METHODOLOGY_AUDIT_{DATE}.json").read_text(encoding="utf-8"))
    integrity = json.loads((BASE / f"G12_OTI8_CNR061_RESULT_INTEGRITY_AUDIT_{DATE}.json").read_text(encoding="utf-8"))
    decision = json.loads((BASE / f"G12_OTI8_CNR061_POST_RESULT_DECISION_LEDGER_{DATE}.json").read_text(encoding="utf-8"))

    checks = {
        "decision_accepts_quarantined_evidence": decision.get("decision") == "ACCEPT_AS_QUARANTINED_DISCOVERY_EVIDENCE",
        "exact_8_94_scope": duplicate.get("blocked_row_exclusion", {}).get("accepted_rows") == 8
        and duplicate.get("blocked_row_exclusion", {}).get("blocked_rows") == 94,
        "hash_recompute": source.get("hash_recompute_status") == "PASS",
        "noleak": source.get("forbidden_label_and_flag_scan", {}).get("status") == "PASS",
        "zero_countable_overlap": duplicate.get("blocked_row_exclusion", {}).get("countable_blocked_overlap")
        == {
            "duplicate_denominator_key_overlap": [],
            "duplicate_group_id_overlap": [],
            "record_id_overlap": [],
            "source_row_hash_overlap": [],
        },
        "methodology_not_computable": duplicate.get("methodology_noncomputability", {}).get("status")
        == "PASS_NOT_COMPUTABLE_AND_NOT_VALIDATION",
        "terminal_integrity": integrity.get("integrity_status") == "PASS_TERMINAL_SCORING_INTERNALLY_CONSISTENT",
    }
    return {
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def scan_live_surface_diff() -> dict[str, Any]:
    diff = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    status = run_command(["git", "status", "--short", "--", *LIVE_SURFACE_PATHS])
    changed_diff = [line.strip().replace("\\", "/") for line in diff["stdout_tail"].splitlines() if line.strip()]
    changed_status = [line.strip().replace("\\", "/") for line in status["stdout_tail"].splitlines() if line.strip()]
    diff["changed_live_surface_files"] = changed_diff
    diff["changed_live_surface_status_entries"] = changed_status
    diff["git_status_command"] = status
    diff["status"] = "PASS" if diff["returncode"] == 0 and status["returncode"] == 0 and not changed_diff and not changed_status else "FAIL"
    return diff


def scan_credentials_and_remotes() -> dict[str, Any]:
    status = run_command(["git", "status", "--short"])
    remote = run_command(["git", "remote", "-v"])
    suspicious = []
    for line in status["stdout_tail"].splitlines():
        normalized = line.lower().replace("\\", "/")
        if any(fragment in normalized for fragment in [".env", "credential", "secret", "token", "remote", ".git/config"]):
            suspicious.append(line)
    return {
        "git_remote_v_observed": remote,
        "status": "PASS" if status["returncode"] == 0 and remote["returncode"] == 0 and not suspicious else "FAIL",
        "suspicious_credential_remote_status_entries": suspicious,
    }


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    all_results_pass = all(str(result.get("status", "")).startswith("PASS") for result in results.values())
    for row in completion.get("prompt_to_artifact_checklist", []):
        if row.get("requirement") == "builder_verifier_tests":
            row["evidence"] = "py_compile, focused pytest, G12 builder, and OTI8 verifier recorded in verification_results_observed"
            row["status"] = "PASS" if all(
                results[key]["status"] == "PASS"
                for key in ["oti8_verifier_and_g12_builder", "py_compile", "focused_pytest"]
            ) else "FAIL"
        if row.get("requirement") == "forbidden_live_surface_diff_status":
            row["evidence"] = "forbidden_live_surface_diff_scan and credentials/remotes scan"
            row["status"] = "PASS" if results["forbidden_live_surface_diff_scan"]["status"] == "PASS" and results["credential_remote_scan"]["status"] == "PASS" else "FAIL"
    checklist_pass = all(str(row.get("status", "")).startswith("PASS") for row in completion.get("prompt_to_artifact_checklist", []))
    completion["verification_observed_at_utc"] = now_utc()
    completion["verification_results_observed"] = results
    completion["verification_status"] = "PASS" if all_results_pass else "FAIL"
    completion["can_mark_goal_complete"] = bool(all_results_pass and checklist_pass)
    COMPLETION_JSON.write_text(json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# G12 OTI8 CNR061 Completion Audit - {DATE}",
        "",
        f"**Promotion verdict:** `{completion['promotion_verdict']}`  ",
        f"**Validation safe:** `{str(completion['validation_safe']).lower()}`  ",
        f"**Outcome review opened:** `{str(completion['outcome_review_opened']).lower()}`  ",
        f"**Live effect:** `{str(completion['live_effect']).lower()}`",
        "",
        f"**Decision:** `{completion['decision']}`  ",
        f"**Verification status:** `{completion['verification_status']}`  ",
        f"**Can mark goal complete:** `{str(completion['can_mark_goal_complete']).lower()}`",
        "",
        "```json",
        json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
    ]
    COMPLETION_MD.write_text("\n".join(lines), encoding="utf-8")
    return completion


def main() -> int:
    # The OTI8 verifier mutates OTI8's completion audit; run it first, then
    # rebuild G12 artifacts against the observed OTI8 verification state.
    precheck = run_oti8_verifier_then_rebuild_g12()
    results = {
        "oti8_verifier_and_g12_builder": precheck,
        "json_jsonl_parse": parse_json_jsonl(),
        "core_audit_invariants": check_core_audits(),
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(TEST_FILE)]),
        "focused_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST_FILE), "-q"]),
        "generated_quarantine_flag_scan": scan_generated_flags(),
        "forbidden_live_surface_diff_scan": scan_live_surface_diff(),
        "credential_remote_scan": scan_credentials_and_remotes(),
    }
    completion = update_completion(results)
    print(json.dumps({"verification_status": completion["verification_status"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
