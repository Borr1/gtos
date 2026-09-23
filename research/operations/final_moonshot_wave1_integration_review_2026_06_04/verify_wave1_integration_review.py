#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[2]

REQUIRED_FILES = [
    "WAVE1_INTEGRATION_COMPLETION_AUDIT.md",
    "WAVE1_INTEGRATION_DECISION_LEDGER.jsonl",
    "WAVE1_INTEGRATION_REVIEW_AND_MERGE_LEDGER.md",
    "WAVE1_INTEGRATION_VERIFICATION_RESULT.json",
    "WAVE1_INTEGRATION_FOCUSED_TEST_RESULT.json",
    "WAVE1_INTEGRATION_OUTPUT_MANIFEST.json",
    "WAVE1_INTEGRATION_BLOCKER_AND_REPAIR_LEDGER.jsonl",
    "WAVE1_INTEGRATION_SATURATION_SELF_RED_TEAM.md",
    "WAVE2_NEXT_OWNER_STARTER_2026-06-04.txt",
    "WAVE2_PROMPT_HARDENING_RESULT.json",
]


def _read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_no} is not a JSON object")
            rows.append(payload)
    return rows


def main() -> int:
    issues: list[str] = []
    for name in REQUIRED_FILES:
        if not (ROUTE_DIR / name).exists():
            issues.append(f"missing_required:{name}")

    if not issues:
        verification = _read_json(ROUTE_DIR / "WAVE1_INTEGRATION_VERIFICATION_RESULT.json")
        focused = _read_json(ROUTE_DIR / "WAVE1_INTEGRATION_FOCUSED_TEST_RESULT.json")
        prompt_hardening = _read_json(ROUTE_DIR / "WAVE2_PROMPT_HARDENING_RESULT.json")
        decisions = _read_jsonl(ROUTE_DIR / "WAVE1_INTEGRATION_DECISION_LEDGER.jsonl")
        repairs = _read_jsonl(ROUTE_DIR / "WAVE1_INTEGRATION_BLOCKER_AND_REPAIR_LEDGER.jsonl")

        if verification.get("ok") is not True:
            issues.append("verification_result_not_ok")
        if focused.get("ok") is not True:
            issues.append("focused_test_result_not_ok")
        if prompt_hardening.get("status") != "complete_verified":
            issues.append("prompt_hardening_result_not_complete_verified")
        for key in ("canonical_prompt", "canonical_starter", "route_local_starter"):
            if prompt_hardening.get(key, {}).get("overall_ok") is not True:
                issues.append(f"prompt_hardening_{key}_not_ok")
        if len(decisions) < 7:
            issues.append("decision_ledger_missing_rows")
        if not any(row.get("decision_id") == "integration_test_fix" for row in decisions):
            issues.append("decision_ledger_missing_integration_test_fix")
        if not repairs:
            issues.append("blocker_or_repair_ledger_empty")

    result = {
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
        "route_dir": str(ROUTE_DIR.relative_to(REPO_ROOT)),
        "required_file_count": len(REQUIRED_FILES),
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
