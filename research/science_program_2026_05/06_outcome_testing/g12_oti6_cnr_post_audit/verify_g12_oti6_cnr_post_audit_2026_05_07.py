#!/usr/bin/env python3
"""Verify G12 OTI6 CNR post-audit artifacts and stamp completion audit."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
COMPLETION_JSON = BASE / f"G12_OTI6_CNR_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"G12_OTI6_CNR_COMPLETION_AUDIT_{DATE}.md"
BUILDER = BASE / "build_g12_oti6_cnr_post_audit_2026_05_07.py"
VERIFIER = BASE / "verify_g12_oti6_cnr_post_audit_2026_05_07.py"
TEST = BASE / "test_g12_oti6_cnr_post_audit_2026_05_07.py"
OTI6_TEST = ROOT / "research/science_program_2026_05/06_outcome_testing/oti6_otr061_cnr_quarantined_results/test_oti6_otr061_cnr_quarantined_results_2026_05_07.py"
OTR061_TEST = ROOT / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/test_otr061_xau_tick_recovery_2026_05_07.py"
G12_OTI5_TEST = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/test_g12_oti5_otr061_post_audit_2026_05_07.py"
LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts", "run_agent.py", "start_all.bat"]


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(str(arg) for arg in args),
        "returncode": result.returncode,
        "status": "PASS" if result.returncode == 0 else "FAIL",
        "stderr_tail": result.stderr.strip()[-2000:],
        "stdout_tail": result.stdout.strip()[-2000:],
    }


def parse_generated_json() -> dict[str, Any]:
    files = sorted(BASE.glob(f"G12_OTI6_CNR_*{DATE}.json"))
    parsed = []
    for path in files:
        json.loads(path.read_text(encoding="utf-8"))
        parsed.append(rel(path))
    return {"status": "PASS", "parsed_count": len(parsed), "parsed_files": parsed}


def scan_no_promotion_verdict() -> dict[str, Any]:
    missing = []
    for path in sorted(BASE.glob(f"G12_OTI6_CNR_*{DATE}.*")):
        if path.suffix.lower() not in {".json", ".md"}:
            continue
        if PROMOTION_VERDICT not in path.read_text(encoding="utf-8", errors="replace"):
            missing.append(rel(path))
    return {"status": "PASS" if not missing else "FAIL", "missing_no_promotion_verdict_files": missing}


def scan_forbidden_flags_and_calls() -> dict[str, Any]:
    hits = []
    for path in sorted(BASE.glob(f"G12_OTI6_CNR_*{DATE}.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        stack = [("$", payload)]
        while stack:
            parent, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    dotted = f"{parent}.{key}"
                    if key in {"validation_safe", "outcome_review_opened", "live_effect"} and nested is True:
                        hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    if key in {"api_calls", "databento_calls", "paid_data_calls", "mt5_order_calls", "order_calls", "canary_calls"} and nested != 0:
                        hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    if key in {
                        "account_history_accessed",
                        "blocked_packet_outcome_source_read",
                        "broker_actual_r_accessed",
                        "live_order_state_accessed",
                        "live_trade_results_accessed",
                    } and nested is not False:
                        hits.append({"path": rel(path), "json_path": dotted, "value": nested})
                    stack.append((dotted, nested))
            elif isinstance(value, list):
                for idx, nested in enumerate(value):
                    stack.append((f"{parent}[{idx}]", nested))
    return {"status": "PASS" if not hits else "FAIL", "forbidden_flag_or_call_hits": hits}


def forbidden_live_surface_diff_scan() -> dict[str, Any]:
    result = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    changed = [line.strip().replace("\\", "/") for line in result["stdout_tail"].splitlines() if line.strip()]
    result.update({"changed_live_surface_files": changed, "status": "PASS" if result["returncode"] == 0 and not changed else "FAIL"})
    return result


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    all_pass = all(value.get("status") == "PASS" for value in results.values())
    checklist = completion.get("prompt_to_artifact_checklist", [])
    for row in checklist:
        if row["requirement"] == "forbidden_live_surface_diff_absent":
            row["status"] = results["forbidden_live_surface_diff_scan"]["status"]
            row["evidence"] = results["forbidden_live_surface_diff_scan"]
        elif row["requirement"] == "research_current_state_update":
            row["status"] = "PENDING_POST_ARTIFACT_COMMIT"
            row["evidence"] = "Update after artifact commit SHA is known."
    completion["prompt_to_artifact_checklist"] = checklist
    completion["verification_results_observed"] = results
    completion["verification_observed_at_utc"] = now_utc()
    completion["verification_status"] = "PASS" if all_pass else "FAIL"
    completion["can_mark_goal_complete"] = bool(all_pass and all(row["status"] in {"PASS", "PENDING_POST_ARTIFACT_COMMIT"} for row in checklist))
    completion["audit_verdict"] = "PASS_READY_FOR_ARTIFACT_COMMIT_AND_CONTEXT_REFRESH" if completion["can_mark_goal_complete"] else "FAIL_VERIFICATION_INCOMPLETE"
    COMPLETION_JSON.write_text(json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COMPLETION_MD.write_text(
        "\n".join(
            [
                f"# G12 OTI6 CNR Completion Audit - {DATE}",
                "",
                f"**Promotion verdict:** `{completion['promotion_verdict']}`  ",
                f"**Validation safe:** `{str(completion['validation_safe']).lower()}`  ",
                f"**Outcome review opened:** `{str(completion['outcome_review_opened']).lower()}`  ",
                f"**Live effect:** `{str(completion['live_effect']).lower()}`",
                "",
                f"**Terminal decision:** `{completion.get('terminal_g12_decision', 'see decision ledger')}`  ",
                f"**Verification status:** `{completion['verification_status']}`  ",
                f"**Can mark goal complete:** `{completion['can_mark_goal_complete']}`",
                "",
                "```json",
                json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return completion


def main() -> int:
    results = {
        "generated_json_parse": parse_generated_json(),
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(TEST)]),
        "focused_g12_oti6_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST), "-q"]),
        "focused_oti6_otr061_g12_control_pytest": run_command(
            [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(OTI6_TEST), str(OTR061_TEST), str(G12_OTI5_TEST), "-q"]
        ),
        "no_promotion_verdict_scan": scan_no_promotion_verdict(),
        "forbidden_flag_and_call_scan": scan_forbidden_flags_and_calls(),
        "forbidden_live_surface_diff_scan": forbidden_live_surface_diff_scan(),
        "final_live_state_regeneration": run_command([sys.executable, "scripts/generate_live_state.py"]),
    }
    completion = update_completion(results)
    print(json.dumps({"can_mark_goal_complete": completion["can_mark_goal_complete"], "verification_status": completion["verification_status"]}, sort_keys=True))
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
