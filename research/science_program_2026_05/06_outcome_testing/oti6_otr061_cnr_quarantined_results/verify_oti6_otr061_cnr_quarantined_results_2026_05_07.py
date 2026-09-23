#!/usr/bin/env python3
"""Verify OTI6 CNR artifacts and stamp observed verification into completion audit."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
ROOT = Path(__file__).resolve().parents[4]
BASE = Path(__file__).resolve().parent
COMPLETION_JSON = BASE / f"OTI6_CNR_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"OTI6_CNR_COMPLETION_AUDIT_{DATE}.md"
LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts", "run_agent.py", "start_all.bat"]
OTI6_TEST = BASE / "test_oti6_otr061_cnr_quarantined_results_2026_05_07.py"
BUILDER = BASE / "build_oti6_otr061_cnr_quarantined_results_2026_05_07.py"
VERIFIER = BASE / "verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py"
OTR061_TEST = ROOT / "research/science_program_2026_05/06_outcome_testing/otr061_xau_tick_recovery/test_otr061_xau_tick_recovery_2026_05_07.py"
G12_TEST = ROOT / "research/science_program_2026_05/06_outcome_testing/g12_oti5_otr061_post_audit/test_g12_oti5_otr061_post_audit_2026_05_07.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "command": " ".join(args),
        "returncode": result.returncode,
        "stdout_tail": result.stdout.strip()[-2000:],
        "stderr_tail": result.stderr.strip()[-2000:],
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }


def parse_generated_json() -> dict[str, Any]:
    files = sorted(BASE.glob(f"OTI6_CNR_*{DATE}.json"))
    parsed = []
    for path in files:
        json.loads(path.read_text(encoding="utf-8"))
        parsed.append(rel(path))
    return {"status": "PASS", "parsed_count": len(parsed), "parsed_files": parsed}


def scan_promotion_verdict() -> dict[str, Any]:
    files = sorted(BASE.glob(f"OTI6_CNR_*{DATE}.*"))
    missing = []
    for path in files:
        if path.suffix.lower() not in {".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if PROMOTION_VERDICT not in text:
            missing.append(rel(path))
    return {"status": "PASS" if not missing else "FAIL", "missing_no_promotion_verdict_files": missing}


def scan_forbidden_true_flags() -> dict[str, Any]:
    hits = []
    for path in sorted(BASE.glob(f"OTI6_CNR_*{DATE}.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        stack = [("$", payload)]
        while stack:
            parent, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    dotted = f"{parent}.{key}"
                    if key in {"validation_safe", "outcome_review_opened", "live_effect"} and nested is True:
                        hits.append({"path": rel(path), "json_path": dotted})
                    stack.append((dotted, nested))
            elif isinstance(value, list):
                for idx, nested in enumerate(value):
                    stack.append((f"{parent}[{idx}]", nested))
    return {"status": "PASS" if not hits else "FAIL", "forbidden_true_flag_hits": hits}


def scan_forbidden_live_surface_diff() -> dict[str, Any]:
    result = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    changed = [line.strip().replace("\\", "/") for line in result["stdout_tail"].splitlines() if line.strip()]
    result.update({"changed_live_surface_files": changed, "status": "PASS" if result["returncode"] == 0 and not changed else "FAIL"})
    return result


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    all_pass = all(row.get("status") == "PASS" for row in results.values())
    checklist_pass = all(row.get("status") == "PASS" for row in completion.get("prompt_to_artifact_checklist", []))
    completion["verification_status"] = "PASS" if all_pass else "FAIL"
    completion["verification_observed_at_utc"] = now_utc()
    completion["verification_results_observed"] = results
    completion["can_mark_goal_complete"] = bool(all_pass and checklist_pass and completion.get("terminal_status"))
    completion["required_artifacts_written"] = sorted(
        set(
            completion.get("required_artifacts_written", [])
            + [
                "verify_oti6_otr061_cnr_quarantined_results_2026_05_07.py",
            ]
        )
    )
    COMPLETION_JSON.write_text(json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    COMPLETION_MD.write_text(
        "\n".join(
            [
                f"# OTI6 CNR Completion Audit - {DATE}",
                "",
                f"**Promotion verdict:** `{completion['promotion_verdict']}`  ",
                f"**Validation safe:** `{str(completion['validation_safe']).lower()}`  ",
                f"**Outcome review opened:** `{str(completion['outcome_review_opened']).lower()}`  ",
                f"**Live effect:** `{str(completion['live_effect']).lower()}`",
                "",
                f"**Terminal status:** `{completion['terminal_status']}`  ",
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
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(OTI6_TEST)]),
        "focused_oti6_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(OTI6_TEST), "-q"]),
        "focused_otr061_g12_pytest": run_command(
            [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(OTR061_TEST), str(G12_TEST), "-q"]
        ),
        "no_promotion_verdict_scan": scan_promotion_verdict(),
        "forbidden_true_flag_scan": scan_forbidden_true_flags(),
        "forbidden_live_surface_diff_scan": scan_forbidden_live_surface_diff(),
    }
    completion = update_completion(results)
    print(json.dumps({"verification_status": completion["verification_status"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
