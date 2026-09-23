#!/usr/bin/env python3
"""Verify G12 CNR next-model control audit artifacts."""

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
CONTROL = ROOT / "research" / "science_program_2026_05" / "06_outcome_testing" / "cnr_next_model_control_pack"
BUILDER = BASE / "build_g12_cnr_next_model_control_audit_2026_05_08.py"
VERIFIER = BASE / "verify_g12_cnr_next_model_control_audit_2026_05_08.py"
TEST_FILE = BASE / "test_g12_cnr_next_model_control_audit_2026_05_08.py"
COMPLETION_JSON = BASE / f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}.md"
LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts/canary", "run_agent.py", "start_all.bat"]

REQUIRED_JSON = [
    f"G12_CNR_NEXT_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_CNR_NEXT_DECISION_LEDGER_{DATE}.json",
    f"G12_CNR_TIMING_TARGET_PREREG_AUDIT_{DATE}.json",
    f"G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_{DATE}.json",
    f"G12_CNR061_LIFECYCLE_PACKET_AUDIT_{DATE}.json",
    f"G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_{DATE}.json",
    f"G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}.json",
    f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}.json",
]
REQUIRED_MD = [
    f"G12_CNR_NEXT_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_CNR_NEXT_DECISION_LEDGER_{DATE}.md",
    f"G12_CNR_TIMING_TARGET_PREREG_AUDIT_{DATE}.md",
    f"G12_CNR_SOURCE_NOLEAK_DUPLICATE_AUDIT_{DATE}.md",
    f"G12_CNR061_LIFECYCLE_PACKET_AUDIT_{DATE}.md",
    f"G12_CNR_XAGUSD_STOP_AFTER_HORIZON_FORENSICS_{DATE}.md",
    f"G12_CNR_NEXT_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}.md",
    f"G12_CNR_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_CNR_NEXT_COMPLETION_AUDIT_{DATE}.md",
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
        "stdout_tail": result.stdout.strip()[-4000:],
        "stderr_tail": result.stderr.strip()[-4000:],
    }


def load_builder():
    spec = importlib.util.spec_from_file_location("g12_cnr_next_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_required_files() -> dict[str, Any]:
    failures = []
    parsed_json = []
    for name in REQUIRED_JSON:
        path = BASE / name
        if not path.exists():
            failures.append({"path": rel(path), "error": "missing"})
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            parsed_json.append(rel(path))
        except Exception as exc:
            failures.append({"path": rel(path), "error": str(exc)})
    missing_md = [rel(BASE / name) for name in REQUIRED_MD if not (BASE / name).exists()]
    for path in missing_md:
        failures.append({"path": path, "error": "missing_md"})
    return {
        "parsed_json_count": len(parsed_json),
        "parsed_json_files": parsed_json,
        "missing_md": missing_md,
        "failures": failures,
        "status": "PASS" if not failures and len(parsed_json) == len(REQUIRED_JSON) else "FAIL",
    }


def boundary_scan() -> dict[str, Any]:
    failures = []
    expected = {
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "broker_actual_r_accessed": False,
        "account_history_accessed": False,
        "live_trade_results_accessed": False,
        "live_order_state_accessed": False,
        "blocked_packet_outcome_source_read": False,
        "api_calls": 0,
        "databento_calls": 0,
        "paid_data_calls": 0,
        "mt5_order_calls": 0,
        "mt5_account_calls": 0,
        "order_calls": 0,
        "canary_calls": 0,
    }
    for name in REQUIRED_JSON:
        payload = json.loads((BASE / name).read_text(encoding="utf-8"))
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                failures.append({"path": name, "key": key, "observed": payload.get(key), "expected": expected_value})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def builder_invariant_recompute() -> dict[str, Any]:
    builder = load_builder()
    control = builder.load_control_pack()
    upstream = builder.load_upstream()
    lifecycle = builder.lifecycle_recompute(control, upstream)
    source = builder.source_noleak_duplicate_audit(control, upstream, lifecycle)
    timing = builder.timing_target_prereg_audit(control)
    checks = {
        "lifecycle_status_pass": lifecycle["status"] == "PASS",
        "all_six_stop_after_original_horizon": lifecycle["label_counts"] == {"stop_after_original_horizon": 6},
        "no_source_hash_failures": not lifecycle["source_hash_failures"],
        "no_forbidden_lifecycle_keys": not lifecycle["forbidden_lifecycle_key_hits"],
        "blocked_94_excluded": source["blocked_94_exclusion"]["status"] == "PASS",
        "boundary_flags_pass": source["boundary_flag_scan"]["status"] == "PASS",
        "timing_family_check_pass": timing["timing_family_set_check"]["status"] == "PASS",
        "target_family_check_pass": timing["target_family_set_check"]["status"] == "PASS",
    }
    return {
        "checks": checks,
        "lifecycle_label_counts": lifecycle["label_counts"],
        "lifecycle_rows": lifecycle["row_count"],
        "source_hash_failures": lifecycle["source_hash_failures"],
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def completion_checklist_scan() -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    failures = []
    for item in completion.get("prompt_to_artifact_checklist", []):
        status = str(item.get("status", ""))
        if status in {"PENDING_VERIFIER", "PENDING_FINAL_PREFLIGHT"}:
            continue
        if not status.startswith("PASS"):
            failures.append(item)
    required = {
        "mandatory_gtos_preflight",
        "context_anchor_before_decisions",
        "required_control_inputs_read",
        "upstream_artifacts_read",
        "local_heavy_data_search",
        "E2_E3_E4_timing_preregistration",
        "T1_T2_T3_target_preregistration",
        "source_contracts",
        "no_leak_controls",
        "duplicate_sample_floor_controls",
        "exact_six_lifecycle_rows",
        "all_six_stop_after_original_horizon",
        "source_hash_recompute",
        "94_blocked_rows_excluded",
        "xagusd_residual_forensics",
        "next_lane_prompt_guidance",
    }
    observed = {item["requirement"] for item in completion.get("prompt_to_artifact_checklist", [])}
    missing = sorted(required - observed)
    return {"failures": failures, "missing": missing, "status": "PASS" if not failures and not missing else "FAIL"}


def live_surface_diff_scan() -> dict[str, Any]:
    result = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    changed = [line.strip().replace("\\", "/") for line in result["stdout_tail"].splitlines() if line.strip()]
    result["changed_live_surface_files"] = changed
    result["status"] = "PASS" if result["returncode"] == 0 and not changed else "FAIL"
    return result


def control_pack_focused_tests() -> dict[str, Any]:
    return run_command(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(CONTROL / "test_cnr_next_model_control_pack_2026_05_08.py"),
            "-q",
        ]
    )


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    all_results_pass = all(str(result.get("status", "")).startswith("PASS") for result in results.values())
    for item in completion.get("prompt_to_artifact_checklist", []):
        if item["status"] == "PENDING_VERIFIER":
            item["status"] = "PASS_VERIFIED" if all_results_pass else "FAIL_VERIFIER"
    checklist_pass = all(
        str(item.get("status", "")).startswith("PASS") or item.get("status") == "PENDING_FINAL_PREFLIGHT"
        for item in completion.get("prompt_to_artifact_checklist", [])
    )
    completion["verification_observed_at_utc"] = now_utc()
    completion["verification_results_observed"] = results
    completion["verification_status"] = "PASS" if all_results_pass else "FAIL"
    completion["can_mark_goal_complete"] = bool(all_results_pass and checklist_pass)
    COMPLETION_JSON.write_text(json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# G12 CNR Next Completion Audit - {DATE}",
        "",
        f"**Promotion verdict:** `{completion['promotion_verdict']}`  ",
        f"**Validation safe:** `{str(completion['validation_safe']).lower()}`  ",
        f"**Outcome review opened:** `{str(completion['outcome_review_opened']).lower()}`  ",
        f"**Live effect:** `{str(completion['live_effect']).lower()}`",
        "",
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
    results = {
        "generated_json_md_parse": parse_required_files(),
        "boundary_scan": boundary_scan(),
        "builder_invariant_recompute": builder_invariant_recompute(),
        "completion_checklist_scan": completion_checklist_scan(),
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(TEST_FILE)]),
        "focused_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST_FILE), "-q"]),
        "control_pack_focused_pytest": control_pack_focused_tests(),
        "forbidden_live_surface_diff_scan": live_surface_diff_scan(),
    }
    completion = update_completion(results)
    print(json.dumps({"verification_status": completion["verification_status"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
