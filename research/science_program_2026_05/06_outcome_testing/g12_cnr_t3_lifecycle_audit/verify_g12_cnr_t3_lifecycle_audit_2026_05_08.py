#!/usr/bin/env python3
"""Verify G12 CNR T3 lifecycle audit artifacts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


DATE = "2026-05-08"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]
BUILDER = BASE / "build_g12_cnr_t3_lifecycle_audit_2026_05_08.py"
VERIFIER = BASE / "verify_g12_cnr_t3_lifecycle_audit_2026_05_08.py"
TEST_FILE = BASE / "test_g12_cnr_t3_lifecycle_audit_2026_05_08.py"
COMPLETION_JSON = BASE / f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.md"

REQUIRED_JSON = [
    f"G12_CNR_T3_CONTEXT_ANCHOR_{DATE}.json",
    f"G12_CNR_T3_DECISION_LEDGER_{DATE}.json",
    f"G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_{DATE}.json",
    f"G12_CNR_T3_LIFECYCLE_PACKET_AUDIT_{DATE}.json",
    f"G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_{DATE}.json",
    f"G12_CNR_T3_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json",
    f"G12_CNR_T3_FORENSICS_AND_LEARNING_{DATE}.json",
    f"G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}.json",
    f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.json",
]

REQUIRED_MD = [
    f"G12_CNR_T3_CONTEXT_ANCHOR_{DATE}.md",
    f"G12_CNR_T3_DECISION_LEDGER_{DATE}.md",
    f"G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_{DATE}.md",
    f"G12_CNR_T3_LIFECYCLE_PACKET_AUDIT_{DATE}.md",
    f"G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_{DATE}.md",
    f"G12_CNR_T3_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.md",
    f"G12_CNR_T3_FORENSICS_AND_LEARNING_{DATE}.md",
    f"G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}.md",
    f"G12_CNR_T3_NEXT_PROMPT_PACK_{DATE}.md",
    f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.md",
]

LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts/canary", "run_agent.py", "start_all.bat"]


def load_json(name: str) -> Any:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


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
    spec = importlib.util.spec_from_file_location("g12_cnr_t3_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_required_files() -> dict[str, Any]:
    failures = []
    parsed = []
    for name in REQUIRED_JSON:
        path = BASE / name
        if not path.exists():
            failures.append({"path": str(path), "error": "missing"})
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
            parsed.append(name)
        except Exception as exc:
            failures.append({"path": str(path), "error": str(exc)})
    for name in REQUIRED_MD:
        if not (BASE / name).exists():
            failures.append({"path": name, "error": "missing_md"})
    for path in (BUILDER, VERIFIER, TEST_FILE):
        if not path.exists():
            failures.append({"path": str(path), "error": "missing_script"})
    return {
        "parsed_json_count": len(parsed),
        "failures": failures,
        "status": "PASS" if not failures and len(parsed) == len(REQUIRED_JSON) else "FAIL",
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
        payload = load_json(name)
        for key, value in expected.items():
            if payload.get(key) != value:
                failures.append({"path": name, "key": key, "observed": payload.get(key), "expected": value})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def builder_recompute_scan() -> dict[str, Any]:
    builder = load_builder()
    t3 = builder.load_t3_artifacts()
    inventory = builder.inventory_coverage_audit(t3)
    lifecycle = builder.lifecycle_packet_audit(t3)
    source = builder.source_hash_and_noleak_audit(t3)
    duplicate = builder.duplicate_samplefloor_audit(t3)
    blockers = builder.blocker_and_route_ledger(t3, inventory)
    generated = {
        "inventory": load_json(f"G12_CNR_T3_INVENTORY_COVERAGE_AUDIT_{DATE}.json"),
        "lifecycle": load_json(f"G12_CNR_T3_LIFECYCLE_PACKET_AUDIT_{DATE}.json"),
        "source": load_json(f"G12_CNR_T3_SOURCE_HASH_AND_NOLEAK_AUDIT_{DATE}.json"),
        "duplicate": load_json(f"G12_CNR_T3_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json"),
        "blockers": load_json(f"G12_CNR_T3_BLOCKER_AND_NEXT_ROUTE_LEDGER_{DATE}.json"),
    }
    checks = {
        "inventory_count": inventory["recomputed_candidate_like_total"] == 304 == generated["inventory"]["recomputed_candidate_like_total"],
        "six_eligible": lifecycle["checks"]["packet_row_count_is_6"] and generated["lifecycle"]["checks"]["packet_row_count_is_6"],
        "all_stop_after_horizon": lifecycle["checks"]["all_packet_rows_stop_after_original_horizon"],
        "tick_recompute": lifecycle["checks"]["tick_path_recompute_matches_labels"],
        "source_hash": source["status"] == "PASS" == generated["source"]["status"],
        "duplicate_sample_floor": duplicate["status"] == "PASS" == generated["duplicate"]["status"],
        "blockers_298": blockers["blocker_count"] == 298 == generated["blockers"]["blocker_count"],
        "first_next_route": blockers["first_next_lane"]["route"] == "SEPARATE_NO_FILL_STILL_PENDING_LIFECYCLE_CONTRACT",
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def completion_checklist_scan() -> dict[str, Any]:
    completion = load_json(f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.json")
    failures = []
    required = {
        "mandatory_gtos_preflight",
        "context_anchor_before_decisions",
        "required_t3_inputs_read",
        "upstream_cnr_oti_artifacts_read",
        "local_heavy_data_roots_searched",
        "304_row_inventory_coverage",
        "six_eligible_rows",
        "298_exact_blockers",
        "frozen_contract_before_scan",
        "allowed_labels",
        "source_hashes",
        "no_leak_controls",
        "duplicate_sample_floor_controls",
        "94_blocked_row_exclusion",
        "what_six_stop_after_original_horizon_labels_prove",
        "what_six_stop_after_original_horizon_labels_do_not_prove",
        "next_route_guidance",
        "py_compile",
        "focused_pytest",
        "verifier_pass",
        "final_live_state_regeneration",
    }
    observed = {item["requirement"] for item in completion.get("prompt_to_artifact_checklist", [])}
    missing = sorted(required - observed)
    for item in completion.get("prompt_to_artifact_checklist", []):
        status = str(item.get("status", ""))
        if status.startswith("PENDING"):
            continue
        if not status.startswith("PASS"):
            failures.append(item)
    return {"missing": missing, "failures": failures, "status": "PASS" if not missing and not failures else "FAIL"}


def live_surface_diff_scan() -> dict[str, Any]:
    result = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    changed = [line.strip().replace("\\", "/") for line in result["stdout_tail"].splitlines() if line.strip()]
    result["changed_live_surface_files"] = changed
    result["status"] = "PASS" if result["returncode"] == 0 and not changed else "FAIL"
    return result


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = load_json(f"G12_CNR_T3_COMPLETION_AUDIT_{DATE}.json")
    all_pass = all(value.get("status") == "PASS" for value in results.values())
    for item in completion.get("prompt_to_artifact_checklist", []):
        if item["status"] == "PENDING_VERIFIER":
            item["status"] = "PASS_VERIFIED" if all_pass else "FAIL_VERIFIER"
        if item["requirement"] == "final_live_state_regeneration" and results.get("final_live_state_regeneration", {}).get("status") == "PASS":
            item["status"] = "PASS_VERIFIED"
    checklist_pass = all(str(item.get("status", "")).startswith("PASS") for item in completion.get("prompt_to_artifact_checklist", []))
    completion["verification_results_observed"] = results
    completion["verification_status"] = "PASS" if all_pass else "FAIL"
    completion["can_mark_goal_complete"] = bool(all_pass and checklist_pass)
    COMPLETION_JSON.write_text(json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    lines = [
        f"# G12 CNR T3 Completion Audit - {DATE}",
        "",
        f"Promotion verdict: `{completion['promotion_verdict']}`",
        f"Validation safe: `{str(completion['validation_safe']).lower()}`",
        f"Outcome review opened: `{str(completion['outcome_review_opened']).lower()}`",
        f"Live effect: `{str(completion['live_effect']).lower()}`",
        "",
        f"Verification status: `{completion['verification_status']}`",
        f"Can mark goal complete: `{str(completion['can_mark_goal_complete']).lower()}`",
        "",
        "```json",
        json.dumps(completion, indent=2, sort_keys=True, ensure_ascii=True),
        "```",
        "",
    ]
    COMPLETION_MD.write_text("\n".join(lines), encoding="utf-8")
    return completion


def main() -> int:
    results = {
        "generated_json_md_parse": parse_required_files(),
        "boundary_scan": boundary_scan(),
        "builder_recompute_scan": builder_recompute_scan(),
        "completion_checklist_scan": completion_checklist_scan(),
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(TEST_FILE)]),
        "focused_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST_FILE), "-q"]),
        "forbidden_live_surface_diff_scan": live_surface_diff_scan(),
        "final_live_state_regeneration": run_command([sys.executable, "scripts/generate_live_state.py"]),
    }
    # The verifier command itself reached this point successfully.
    results["verifier_self"] = {"status": "PASS", "issues": []}
    completion = update_completion(results)
    print(
        json.dumps(
            {
                "verification_status": completion["verification_status"],
                "can_mark_goal_complete": completion["can_mark_goal_complete"],
                "results": {key: value["status"] for key, value in results.items()},
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
