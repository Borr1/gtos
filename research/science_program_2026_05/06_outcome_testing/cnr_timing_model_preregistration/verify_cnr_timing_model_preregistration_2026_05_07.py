#!/usr/bin/env python3
"""Verify the CNR timing model preregistration package."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATE = "2026-05-07"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
BASE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
FORBIDDEN_TRUE_KEYS = {"validation_safe", "outcome_review_opened", "live_effect"}
REQUIRED_STEMS = [
    "CNR_TIMING_MODEL_PREREGISTRATION",
    "CNR_TIMING_MODEL_SOURCE_FIELD_CONTRACT",
    "CNR_TIMING_MODEL_LATENCY_CAPTURE_SPEC",
    "CNR_TIMING_MODEL_NOLEAK_DUPLICATE_LABEL_POLICY",
    "CNR_TIMING_MODEL_MULTITIMEFRAME_EVIDENCE_MAP",
    "CNR_TIMING_MODEL_BLOCKER_AND_SAMPLE_FLOOR_LEDGER",
    "CNR_TIMING_MODEL_DATA_EXPANSION_PLAN",
    "CNR_TIMING_MODEL_NEXT_PACKET_PLAN",
    "CNR_TIMING_MODEL_CORRECT_DIRECTION_FAILURE_ANATOMY",
    "CNR_TIMING_MODEL_RECURSIVE_AMBIGUITY_LEDGER",
    "CNR_TIMING_MODEL_ANTI_BOXING_REVIEW",
    "CNR_TIMING_MODEL_CONTEXT_ANCHOR",
    "CNR_TIMING_MODEL_COMPLETION_AUDIT",
]
FORBIDDEN_LIVE_SURFACES = (
    "src/",
    "prompts/",
    "config/",
    "scripts/canary",
    "scripts/canary_fixtures/",
    "run_agent.py",
    "start_all.bat",
)


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        return f"ERROR[{result.returncode}]: {result.stderr.strip()}"
    return result.stdout.strip()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def walk(value: Any, path: str = ""):
    if isinstance(value, dict):
        for key, nested in value.items():
            new_path = f"{path}.{key}" if path else key
            yield new_path, key, nested
            yield from walk(nested, new_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from walk(item, f"{path}[{index}]")


def run_command(args: list[str]) -> dict[str, Any]:
    result = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "args": args,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-4000:],
        "stderr_tail": result.stderr[-4000:],
        "status": "PASS" if result.returncode == 0 else "FAIL",
    }


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title} - {DATE}",
        "",
        f"**Promotion verdict:** `{PROMOTION_VERDICT}`  ",
        "**Validation safe:** `false`  ",
        "**Outcome review opened:** `false`  ",
        "**Live effect:** `false`",
        "",
        "```json",
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True, default=str),
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def verify() -> dict[str, Any]:
    issues: list[str] = []
    json_payloads: dict[str, Any] = {}
    missing_files: list[str] = []

    for stem in REQUIRED_STEMS:
        json_path = BASE / f"{stem}_{DATE}.json"
        md_path = BASE / f"{stem}_{DATE}.md"
        if not json_path.exists():
            missing_files.append(rel(json_path))
            continue
        if not md_path.exists():
            missing_files.append(rel(md_path))
            continue
        payload = load_json(json_path)
        json_payloads[stem] = payload
        if payload.get("promotion_verdict") != PROMOTION_VERDICT:
            issues.append(f"{json_path.name}: promotion_verdict not preserved")
        for key in FORBIDDEN_TRUE_KEYS:
            if payload.get(key) is not False:
                issues.append(f"{json_path.name}: top-level {key} is not false")
        md_text = md_path.read_text(encoding="utf-8")
        if PROMOTION_VERDICT not in md_text:
            issues.append(f"{md_path.name}: missing NO_PROMOTION_VERDICT")

    forbidden_true_hits: list[str] = []
    for stem, payload in json_payloads.items():
        for path, key, value in walk(payload):
            if key in FORBIDDEN_TRUE_KEYS and value is True:
                forbidden_true_hits.append(f"{stem}:{path}=true")
    if forbidden_true_hits:
        issues.extend(forbidden_true_hits)

    anti = json_payloads.get("CNR_TIMING_MODEL_ANTI_BOXING_REVIEW", {})
    covered_classes = {row.get("class") for row in anti.get("limitation_classes", [])}
    expected_classes = {
        "timeframe",
        "data_location",
        "data_modality",
        "instrument_symbol",
        "science_domain",
        "model_class",
        "code_artifact_history",
        "access_path",
        "question_scope",
    }
    missing_anti = sorted(expected_classes - covered_classes)
    if missing_anti:
        issues.append(f"anti-boxing review missing classes: {missing_anti}")

    expansion = json_payloads.get("CNR_TIMING_MODEL_DATA_EXPANSION_PLAN", {})
    manifest = expansion.get("next_extraction_manifest", {})
    if not manifest.get("fields") or not manifest.get("forbidden_fields") or not manifest.get("source_priority"):
        issues.append("data expansion plan missing exact extraction fields/forbidden/source priority")

    context = json_payloads.get("CNR_TIMING_MODEL_CONTEXT_ANCHOR", {})
    for key in ["controlling_prompt_path", "control_inputs_read", "searched_roots", "route_decisions", "remaining_blockers_or_approvals"]:
        if not context.get(key):
            issues.append(f"context anchor missing {key}")

    completion = json_payloads.get("CNR_TIMING_MODEL_COMPLETION_AUDIT", {})
    checklist = completion.get("prompt_to_artifact_checklist", [])
    if len(checklist) < 20:
        issues.append("completion audit checklist too short")
    bad_checklist = [row for row in checklist if row.get("status") not in {"satisfied", "not_applicable_with_reason", "blocked_with_exact_next_requirement"}]
    if bad_checklist:
        issues.append(f"completion checklist has invalid statuses: {bad_checklist[:3]}")

    diff_names = git(["diff", "--name-only"])
    diff_files = [line.strip().replace("\\", "/") for line in diff_names.splitlines() if line.strip()]
    forbidden_diff_files = [path for path in diff_files if path.startswith(FORBIDDEN_LIVE_SURFACES)]
    if forbidden_diff_files:
        issues.append(f"forbidden live-surface diff files: {forbidden_diff_files}")

    output_dirs = [path for path in BASE.iterdir() if path.is_dir()]
    forbidden_output_dirs = [path.name for path in output_dirs if "outcome" in path.name.lower() or "quarantine" in path.name.lower()]
    if forbidden_output_dirs:
        issues.append(f"forbidden result/quarantine output dirs: {forbidden_output_dirs}")

    scripts = [
        BASE / "build_cnr_timing_model_preregistration_2026_05_07.py",
        BASE / "verify_cnr_timing_model_preregistration_2026_05_07.py",
        BASE / "test_cnr_timing_model_preregistration_2026_05_07.py",
    ]
    py_compile = run_command(["python", "-m", "py_compile", *[str(path) for path in scripts]])
    if py_compile["returncode"] != 0:
        issues.append("py_compile failed")
    pytest = run_command(["python", "-m", "pytest", str(BASE / "test_cnr_timing_model_preregistration_2026_05_07.py"), "-q", "-p", "no:cacheprovider"])
    if pytest["returncode"] != 0:
        issues.append("focused pytest failed")

    result = {
        "artifact_family": "CNR_TIMING_MODEL_VERIFICATION_RESULTS",
        "date_stamp": DATE,
        "forbidden_diff_files": forbidden_diff_files,
        "forbidden_output_dirs": forbidden_output_dirs,
        "forbidden_true_hits": forbidden_true_hits,
        "generated_at_utc": now_utc(),
        "git_branch_at_verify": git(["branch", "--show-current"]),
        "git_head_at_verify": git(["log", "-1", "--oneline"]),
        "issues": issues,
        "live_effect": False,
        "missing_files": missing_files,
        "outcome_review_opened": False,
        "promotion_verdict": PROMOTION_VERDICT,
        "py_compile": py_compile,
        "pytest": pytest,
        "required_json_count": len(json_payloads),
        "status": "PASS" if not issues and not missing_files else "FAIL",
        "validation_safe": False,
    }

    results_json = BASE / f"CNR_TIMING_MODEL_VERIFICATION_RESULTS_{DATE}.json"
    results_md = BASE / f"CNR_TIMING_MODEL_VERIFICATION_RESULTS_{DATE}.md"
    write_json(results_json, result)
    write_md(results_md, "CNR Timing Model Verification Results", result)

    completion_path = BASE / f"CNR_TIMING_MODEL_COMPLETION_AUDIT_{DATE}.json"
    if completion_path.exists():
        completion_payload = load_json(completion_path)
        completion_payload["verification_evidence"] = {
            "forbidden_true_scan": "PASS" if not forbidden_true_hits else "FAIL",
            "focused_pytest": pytest,
            "json_parse_count": len(json_payloads),
            "missing_files": missing_files,
            "no_forbidden_live_surface_diff": not forbidden_diff_files,
            "no_result_or_quarantine_output_dir": not forbidden_output_dirs,
            "py_compile": py_compile,
            "status": result["status"],
            "verification_results_artifact": rel(results_json),
        }
        completion_payload["completion_verdict"] = "VERIFICATION_PASS_READY_FOR_COMMIT" if result["status"] == "PASS" else "VERIFICATION_FAIL_NOT_COMPLETE"
        write_json(completion_path, completion_payload)
        write_md(BASE / f"CNR_TIMING_MODEL_COMPLETION_AUDIT_{DATE}.md", "CNR Timing Model Completion Audit", completion_payload)

    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True, default=str))
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
