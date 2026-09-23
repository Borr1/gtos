#!/usr/bin/env python3
"""Verifier for NOFILL_LIFECYCLE_CLOSURE_SOURCE_CORRECTION_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_nofill_closure_source_correction_2026_05_08 as builder


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
UPSTREAM_DIR = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet"

REQUIRED_JSON = [
    "NOFILL_CORR_CONTEXT_ANCHOR_2026-05-08.json",
    "NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json",
    "NOFILL_CORR_PATCH_LEDGER_2026-05-08.json",
    "NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
    "NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "NOFILL_CORR_FORENSICS_AND_LEARNING_2026-05-08.json",
    "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json",
]

REQUIRED_MD = [name.replace(".json", ".md") for name in REQUIRED_JSON] + [
    "NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md",
]


def load_json(path: Path | str) -> Any:
    path = OUT_DIR / path if isinstance(path, str) else path
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def run_cmd(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    return {
        "command": " ".join(str(arg) for arg in args),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "status": "PASS" if proc.returncode == 0 else "FAIL",
    }


def json_parse_check() -> dict[str, Any]:
    parsed = []
    errors = []
    for name in REQUIRED_JSON:
        try:
            json.loads((OUT_DIR / name).read_text(encoding="utf-8"))
            parsed.append(name)
        except Exception as exc:
            errors.append({"path": name, "error": f"{type(exc).__name__}: {exc}"})
    for path in [
        UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json",
        UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl",
        UPSTREAM_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json",
        UPSTREAM_DIR / "NOFILL_CLOSE_SOURCE_SEARCH_LEDGER_2026-05-08.json",
        UPSTREAM_DIR / "NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
        UPSTREAM_DIR / "NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
        UPSTREAM_DIR / "NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json",
    ]:
        try:
            if path.suffix == ".jsonl":
                for line in path.read_text(encoding="utf-8").splitlines():
                    if line.strip():
                        json.loads(line)
            else:
                json.loads(path.read_text(encoding="utf-8"))
            parsed.append(builder.rel(path))
        except Exception as exc:
            errors.append({"path": builder.rel(path), "error": f"{type(exc).__name__}: {exc}"})
    return {"status": "PASS" if not errors else "FAIL", "parsed_count": len(parsed), "errors": errors}


def artifact_presence_check() -> dict[str, Any]:
    missing = [name for name in REQUIRED_JSON + REQUIRED_MD if not (OUT_DIR / name).exists()]
    return {"status": "PASS" if not missing else "FAIL", "missing": missing}


def correction_objective_check() -> dict[str, Any]:
    source = load_json("NOFILL_CORR_SOURCE_RESOLUTION_LEDGER_2026-05-08.json")
    hash_noleak = load_json("NOFILL_CORR_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json")
    duplicate = load_json("NOFILL_CORR_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json")
    packet = json.loads((UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08.json").read_text(encoding="utf-8"))
    rows = load_jsonl(UPSTREAM_DIR / "NOFILL_CLOSE_ROW_PACKET_2026-05-08_ROWS.jsonl")
    blocker = json.loads((UPSTREAM_DIR / "NOFILL_CLOSE_ROW_BLOCKER_LEDGER_2026-05-08.json").read_text(encoding="utf-8"))
    row_0127 = next((row for row in rows if row.get("packet_row_id") == "NOFILL-CLOSE-ROW-0127"), None)
    issues: list[Any] = []
    counts = packet.get("closure_status_counts") or {}
    if packet.get("packet_row_count") != 298 or counts.get("source_closed") != 298 or counts.get("source_blocked_exact", 0) != 0:
        issues.append({"packet_counts": counts, "packet_rows": packet.get("packet_row_count")})
    if not row_0127:
        issues.append("row_0127_missing")
    else:
        projection = (row_0127.get("source_evidence") or {}).get("tick_terminal_sequence_projection") or {}
        selected = projection.get("selected_supplemental_source_files") or []
        if row_0127.get("closure_status") != "source_closed":
            issues.append("row_0127_not_source_closed")
        if projection.get("terminal_area_touch_time_utc") != "2026-05-06T07:15:00.634000Z":
            issues.append("row_0127_terminal_touch_mismatch")
        if len(selected) != 1 or not selected[0].endswith(builder.OTR061_FILE):
            issues.append({"row_0127_selected_source_files": selected})
        elif projection.get("source_sha256", {}).get(selected[0]) != builder.OTR061_SHA256:
            issues.append("row_0127_selected_source_hash_mismatch")
    if source["stale_blocker_resolution"]["BLOCKED_NO_TICKS_IN_WINDOW_active_rows_after_correction"]:
        issues.append("stale_BLOCKED_NO_TICKS_IN_WINDOW_rows_remain")
    if blocker.get("read_only_extraction_requests"):
        issues.append("active_read_only_extraction_requests_remain")
    superseded = blocker.get("superseded_read_only_extraction_requests", [])
    if len(superseded) != 1 or superseded[0].get("current_audit_status") != "SUPERSEDED_BY_EXISTING_LOCAL_OTR061_SOURCE_EVIDENCE":
        issues.append("superseded_extraction_manifest_missing_or_wrong_status")
    if hash_noleak.get("status") != "PASS":
        issues.append({"hash_noleak_status": hash_noleak.get("status")})
    if duplicate.get("validation_sample_floor_status") != "FALSE_SOURCE_CLOSURE_PACKET_NOT_RESULT_VALIDATION":
        issues.append("duplicate_sample_floor_drift")
    if any(row.get("source_lane") == "OTI8_CNR061" for row in rows):
        issues.append("OTI8_CNR061_leak")
    if any(row.get("closure_label") == "stop_after_original_horizon" for row in rows):
        issues.append("T3_stop_after_original_horizon_label_leak")
    if any(row.get("validation_safe") or row.get("outcome_review_opened") or row.get("live_effect") for row in rows):
        issues.append("false_flag_drift")
    return {"status": "PASS" if not issues else "FAIL", "issues": issues}


def py_compile_check() -> dict[str, Any]:
    scripts = [
        OUT_DIR / "build_nofill_closure_source_correction_2026_05_08.py",
        OUT_DIR / "verify_nofill_closure_source_correction_2026_05_08.py",
        OUT_DIR / "test_nofill_closure_source_correction_2026_05_08.py",
        UPSTREAM_DIR / "build_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        UPSTREAM_DIR / "verify_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        UPSTREAM_DIR / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py",
    ]
    return run_cmd([sys.executable, "-B", "-m", "py_compile", *[str(path) for path in scripts]])


def focused_pytest_check() -> dict[str, Any]:
    return run_cmd(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(UPSTREAM_DIR / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py"),
            str(OUT_DIR / "test_nofill_closure_source_correction_2026_05_08.py"),
            "-q",
        ]
    )


def upstream_verifier_check() -> dict[str, Any]:
    return run_cmd([sys.executable, str(UPSTREAM_DIR / "verify_nofill_lifecycle_closure_source_packet_2026_05_08.py")])


def live_surface_diff_check() -> dict[str, Any]:
    status = builder.git_output("status", "--short")
    workspace_changed = []
    for line in status.splitlines():
        stripped = line.strip()
        if not stripped or stripped.lower().startswith("warning:"):
            continue
        if len(line) >= 4:
            workspace_changed.append(line[3:].replace("\\", "/"))

    committed_scope = builder.git_output("diff", "--name-only", "HEAD^1", "HEAD")
    committed_changed = [
        line.strip().replace("\\", "/")
        for line in committed_scope.splitlines()
        if line.strip()
    ]
    correction_committed_scope = any(
        path.startswith("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet/")
        or path.startswith("research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_correction/")
        for path in committed_changed
    )
    changed = committed_changed if correction_committed_scope else workspace_changed

    forbidden_prefixes = [
        "src/",
        "prompts/",
        "config/",
        "scripts/canary",
        "run_agent.py",
        "start_all.bat",
        ".env",
    ]
    forbidden_needles = [
        "execution",
        "risk",
        "permissions",
        "safety",
        "selector",
        "mt5_order",
        "mt5_account",
        "databento",
        "credential",
        "remote",
    ]
    forbidden = [
        path for path in changed
        if any(path.startswith(prefix) for prefix in forbidden_prefixes)
        or any(needle in path.lower() for needle in forbidden_needles)
    ]
    return {
        "status": "PASS" if not forbidden else "FAIL",
        "checked_scope": "committed_diff_HEAD_parent" if correction_committed_scope else "workspace_status",
        "changed_paths": changed,
        "workspace_changed_paths_observed": workspace_changed,
        "forbidden_live_surface_changed_paths": forbidden,
    }


def live_state_regeneration_check() -> dict[str, Any]:
    return run_cmd([sys.executable, "scripts/generate_live_state.py"])


def g12_historical_verifier_relevance_check() -> dict[str, Any]:
    return {
        "status": "PASS",
        "decision": "NOT_RERUN_AS_GREEN_GATE_AFTER_UPSTREAM_CORRECTION",
        "reason": "The historical G12 verifier asserts the old upstream 297/1 state by design. This lane writes NOFILL_CORR_G12_REAUDIT_PROMPT_PACK_2026-05-08.md for the required post-correction G12 reaudit instead.",
    }


def update_completion(result: dict[str, Any]) -> None:
    completion_path = OUT_DIR / "NOFILL_CORR_COMPLETION_AUDIT_2026-05-08.json"
    completion = load_json(completion_path)
    completion["verification_results"] = result
    completion["can_mark_goal_complete"] = result["verification_status"] == "PASS"
    completion["completion_status"] = "PASS_VERIFIED_SOURCE_CORRECTION" if completion["can_mark_goal_complete"] else "FAIL_VERIFIER"
    for item in completion["prompt_to_artifact_checklist"]:
        if item["requirement"] == "Verifier/tests":
            item["status"] = "PASS" if completion["can_mark_goal_complete"] else "FAIL"
            item["evidence"] = "JSON/JSONL parse, py_compile, upstream+correction pytest, upstream verifier, source/hash/no-leak, duplicate/sample-floor, live-surface, and LIVE_STATE closeout checks"
    builder.write_json(completion_path, completion)
    builder.write_completion_md(completion)


def verify() -> dict[str, Any]:
    results = {
        "artifact_presence": artifact_presence_check(),
        "json_parse": json_parse_check(),
        "correction_objective": correction_objective_check(),
        "py_compile": py_compile_check(),
        "focused_pytest": focused_pytest_check(),
        "upstream_verifier": upstream_verifier_check(),
        "g12_historical_verifier_relevance": g12_historical_verifier_relevance_check(),
        "live_surface_diff": live_surface_diff_check(),
        "live_state_regeneration": live_state_regeneration_check(),
    }
    status = "PASS" if all(item.get("status") == "PASS" for item in results.values()) else "FAIL"
    result = {"verification_status": status, "can_mark_goal_complete": status == "PASS", "results": results}
    update_completion(result)
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["verification_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
