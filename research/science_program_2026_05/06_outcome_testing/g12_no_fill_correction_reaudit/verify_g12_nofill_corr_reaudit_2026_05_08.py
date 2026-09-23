#!/usr/bin/env python3
"""Verifier for G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_REAUDIT_V1."""

from __future__ import annotations

import importlib.util
import json
import py_compile
import subprocess
import sys
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
BUILDER_PATH = OUT_DIR / "build_g12_nofill_corr_reaudit_2026_05_08.py"
TEST_PATH = OUT_DIR / "test_g12_nofill_corr_reaudit_2026_05_08.py"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

REQUIRED_JSON = [
    "G12_NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.json",
    "G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.json",
    "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json",
    "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json",
    "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.json",
    "G12_NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.json",
    "G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json",
]

REQUIRED_MD = [
    "G12_NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.md",
    "G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.md",
    "G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.md",
    "G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.md",
    "G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.md",
    "G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.md",
    "G12_NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.md",
    "G12_NOFILL_CORR_NEXT_PROMPT_PACK_2026-05-08.md",
    "G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md",
]


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_nofill_corr_reaudit_builder", BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to import builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_builder()


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check_artifact_presence() -> dict[str, Any]:
    missing = [name for name in REQUIRED_JSON + REQUIRED_MD if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def check_json_parse() -> dict[str, Any]:
    parsed = []
    errors = []
    for name in REQUIRED_JSON:
        try:
            load_json(name)
            parsed.append(name)
        except Exception as exc:
            errors.append({"path": name, "error": str(exc)})
    return {"status": "PASS" if not errors else "FAIL", "parsed_count": len(parsed), "errors": errors}


def check_py_compile() -> dict[str, Any]:
    results = []
    for path in [BUILDER_PATH, Path(__file__).resolve(), TEST_PATH]:
        try:
            py_compile.compile(str(path), doraise=True)
            results.append({"path": builder.rel(path), "status": "PASS"})
        except Exception as exc:
            results.append({"path": builder.rel(path), "status": "FAIL", "error": str(exc)})
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL", "results": results}


def check_focused_pytest() -> dict[str, Any]:
    cmd = [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST_PATH), "-q"]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return {
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "command": " ".join(cmd),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def check_objective_requirements() -> dict[str, Any]:
    decision = load_json("G12_NOFILL_CORR_DECISION_LEDGER_2026-05-08.json")
    source = load_json("G12_NOFILL_CORR_SOURCE_REAUDIT_2026-05-08.json")
    row = load_json("G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json")
    noleak = load_json("G12_NOFILL_CORR_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    completion = load_json("G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json")
    issues = []
    if decision["decision"] != "ACCEPT_CORRECTED_SOURCE_PACKET_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE":
        issues.append("decision_not_accept")
    counts = source["packet_counts"]
    if counts["rows_jsonl_count"] != 298 or counts["closure_status_counts"].get("source_closed") != 298:
        issues.append("packet_count_mismatch")
    if counts["closure_status_counts"].get("source_blocked_exact", 0) != 0:
        issues.append("source_blocked_exact_not_zero")
    if row["source_sha256"] != builder.EXPECTED_OTR_SHA256:
        issues.append("row_0127_sha_mismatch")
    if row["recomputed_first_source_event"]["first_touch_utc"] != builder.EXPECTED_ROW_0127_TOUCH:
        issues.append("row_0127_first_touch_mismatch")
    if source["stale_blocker_status"]["status"] != "PASS":
        issues.append("stale_blocker_status_not_pass")
    if source["source_search_hardening"]["status"] != "PASS":
        issues.append("source_search_hardening_not_pass")
    if source["exclusion_status"]["status"] != "PASS":
        issues.append("exclusion_status_not_pass")
    if noleak["status"] != "PASS":
        issues.append("noleak_duplicate_samplefloor_not_pass")
    checklist_failures = [item for item in completion["prompt_to_artifact_checklist"] if item["status"] != "PASS"]
    if checklist_failures:
        issues.append({"checklist_failures": checklist_failures})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_recomputed_builder_payloads() -> dict[str, Any]:
    payloads = builder.build_payloads()
    issues = []
    if payloads["completion"]["completion_status"] != "PASS_ACCEPTED_CORRECTED_SOURCE_PACKET":
        issues.append("builder_completion_not_pass")
    if payloads["row_0127"]["source_sha256"] != load_json("G12_NOFILL_CORR_ROW_0127_AUDIT_2026-05-08.json")["source_sha256"]:
        issues.append("row_0127_hash_artifact_not_reproducible")
    if payloads["source_reaudit"]["packet_counts"]["rows_jsonl_count"] != 298:
        issues.append("recomputed_packet_count_not_298")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_flags() -> dict[str, Any]:
    issues = []
    for name in REQUIRED_JSON:
        payload = load_json(name)
        for key, expected in {
            "promotion_verdict": PROMOTION_VERDICT,
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        }.items():
            if payload.get(key) != expected:
                issues.append({"path": name, "key": key, "value": payload.get(key)})
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def check_live_surface_scope() -> dict[str, Any]:
    scope = builder.live_surface_status()
    return {"status": scope["status"], "scope": scope}


def update_artifacts(results: dict[str, Any]) -> None:
    verifier = load_json("G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.json")
    verifier["new_verifier_results"] = results
    verifier["status"] = "PASS" if all(value.get("status") == "PASS" for value in results.values()) else "FAIL"
    write_json("G12_NOFILL_CORR_VERIFIER_AND_SCOPE_AUDIT_2026-05-08.json", verifier)

    completion = load_json("G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json")
    completion["verification_results"] = results
    completion["can_mark_goal_complete"] = all(value.get("status") == "PASS" for value in results.values())
    completion["completion_status"] = "PASS_ACCEPTED_CORRECTED_SOURCE_PACKET" if completion["can_mark_goal_complete"] else "FAIL_VERIFIER"
    write_json("G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json", completion)

    md_lines = [
        "# G12 NOFILL Correction Completion Audit - 2026-05-08",
        "",
        f"Completion status: `{completion['completion_status']}`",
        f"Can mark goal complete: `{completion['can_mark_goal_complete']}`",
        f"Decision: `{completion['decision']}`",
        "",
        "## Prompt-To-Artifact Checklist",
    ]
    for item in completion["prompt_to_artifact_checklist"]:
        md_lines.append(f"- `{item['status']}` {item['requirement']} -> `{item['artifact']}`")
    md_lines.extend(["", "## Verifier Results"])
    for name, result in results.items():
        md_lines.append(f"- `{result.get('status')}` {name}")
    md_lines.append("")
    md_lines.append("All outputs remain source/control only with `NO_PROMOTION_VERDICT`, validation_safe=false, outcome_review_opened=false, and live_effect=false.")
    (OUT_DIR / "G12_NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")


def main() -> int:
    results = {
        "artifact_presence": check_artifact_presence(),
        "json_parse": check_json_parse(),
        "py_compile": check_py_compile(),
        "focused_pytest": check_focused_pytest(),
        "objective_requirements": check_objective_requirements(),
        "recomputed_builder_payloads": check_recomputed_builder_payloads(),
        "flags": check_flags(),
        "live_surface_scope": check_live_surface_scope(),
    }
    update_artifacts(results)
    status = "PASS" if all(value.get("status") == "PASS" for value in results.values()) else "FAIL"
    print(json.dumps({"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}, indent=2, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
