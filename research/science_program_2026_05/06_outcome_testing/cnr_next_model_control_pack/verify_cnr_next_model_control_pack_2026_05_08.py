#!/usr/bin/env python3
"""Verify CNR next-model control pack artifacts."""

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
BUILDER = BASE / "build_cnr_next_model_control_pack_2026_05_08.py"
VERIFIER = BASE / "verify_cnr_next_model_control_pack_2026_05_08.py"
TEST_FILE = BASE / "test_cnr_next_model_control_pack_2026_05_08.py"
COMPLETION_JSON = BASE / f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}.json"
COMPLETION_MD = BASE / f"CNR_NEXT_MODEL_COMPLETION_AUDIT_{DATE}.md"
LIVE_SURFACE_PATHS = ["src", "prompts", "config", "scripts/canary", "run_agent.py", "start_all.bat"]


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
    spec = importlib.util.spec_from_file_location("cnr_next_model_builder", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def parse_generated_machine_files() -> dict[str, Any]:
    json_files = sorted(path for path in BASE.glob(f"*_{DATE}.json") if path.name.startswith(("CNR_", "CNR061_")))
    parsed_json = []
    failures = []
    for path in json_files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
            parsed_json.append(rel(path))
        except Exception as exc:
            failures.append({"path": rel(path), "error": str(exc)})
    parsed_jsonl = []
    for path in sorted(BASE.glob(f"*_{DATE}_ROWS.jsonl")):
        count = 0
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        json.loads(line)
                        count += 1
            parsed_jsonl.append({"path": rel(path), "rows": count})
        except Exception as exc:
            failures.append({"path": rel(path), "error": str(exc)})
    return {
        "parsed_json_count": len(parsed_json),
        "parsed_json_files": parsed_json,
        "parsed_jsonl": parsed_jsonl,
        "failures": failures,
        "status": "PASS" if len(parsed_json) >= 9 and parsed_jsonl and not failures else "FAIL",
    }


def recompute_builder_invariants() -> dict[str, Any]:
    builder = load_builder()
    contract = builder.lifecycle_label_contract()
    packet, rows = builder.build_lifecycle_packet(contract)
    oti8_rows = builder.load_oti8_rows()
    no_terminal_hashes = {
        row["sidecar_row_sha256"]
        for row in oti8_rows
        if row.get("terminal_status") == "NO_TERMINAL_WITHIN_ORDERED_HORIZON"
    }
    packet_hashes = {row["sidecar_row_sha256"] for row in rows}
    labels_allowed = {row["lifecycle_label"] for row in rows}.issubset(set(contract["allowed_labels"]))
    no_r_keys = []
    for row in rows:
        stack = [("$", row)]
        while stack:
            prefix, value = stack.pop()
            if isinstance(value, dict):
                for key, nested in value.items():
                    dotted = f"{prefix}.{key}"
                    if key == "synthetic_r" or key.endswith("_r"):
                        no_r_keys.append({"packet_row_sha256": row["packet_row_sha256"], "json_path": dotted})
                    stack.append((dotted, nested))
            elif isinstance(value, list):
                for idx, nested in enumerate(value):
                    stack.append((f"{prefix}[{idx}]", nested))
    status = len(rows) == 6 and packet_hashes == no_terminal_hashes and labels_allowed and not no_r_keys
    return {
        "packet_status": packet["status"],
        "rows": len(rows),
        "packet_sidecar_hashes": sorted(packet_hashes),
        "oti8_no_terminal_hashes": sorted(no_terminal_hashes),
        "labels": sorted({row["lifecycle_label"] for row in rows}),
        "labels_allowed": labels_allowed,
        "r_key_hits": no_r_keys,
        "status": "PASS" if status else "FAIL",
    }


def scan_boundary_flags() -> dict[str, Any]:
    failures = []
    for path in sorted(BASE.glob(f"*_{DATE}.json")):
        if not path.name.startswith(("CNR_", "CNR061_")):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
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
        for key, expected_value in expected.items():
            if payload.get(key) != expected_value:
                failures.append({"path": rel(path), "key": key, "observed": payload.get(key), "expected": expected_value})
    return {"failures": failures, "status": "PASS" if not failures else "FAIL"}


def verify_no_leak_duplicate_samplefloor_artifact() -> dict[str, Any]:
    audit = json.loads((BASE / f"CNR_TIMING_TARGET_NOLEAK_DUPLICATE_SAMPLEFLOOR_AUDIT_{DATE}.json").read_text(encoding="utf-8"))
    checks = {
        "no_leak": audit["no_leak_scan"]["status"] == "PASS",
        "six_row_scope": audit["exact_six_row_scope_check"]["status"] == "PASS_EXACT_SIX",
        "blocked_94": audit["blocked_94_not_scored_proof"]["status"] == "PASS_94_BLOCKED_ROWS_NOT_SCORED",
        "sample_floor_false": audit["sample_floor"]["sample_floor_for_validation_met"] is False,
    }
    return {"checks": checks, "status": "PASS" if all(checks.values()) else "FAIL"}


def verify_source_hashes() -> dict[str, Any]:
    rows = []
    with (BASE / f"CNR061_NO_TERMINAL_TIMEBOX_LIFECYCLE_PACKET_{DATE}_ROWS.jsonl").open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    failures = []
    builder = load_builder()
    for row in rows:
        for source in row["lifecycle_observation"]["available_extended_source_files"]:
            path = Path(source["path"])
            observed = builder.file_sha256(path) if path.exists() else None
            if observed != source["sha256"]:
                failures.append({"path": source["path"], "observed": observed, "expected": source["sha256"]})
    return {"source_hash_failures": failures, "status": "PASS" if not failures else "FAIL"}


def scan_live_surface_diff() -> dict[str, Any]:
    result = run_command(["git", "diff", "--name-only", "--", *LIVE_SURFACE_PATHS])
    changed = [line.strip().replace("\\", "/") for line in result["stdout_tail"].splitlines() if line.strip()]
    result["changed_live_surface_files"] = changed
    result["status"] = "PASS" if result["returncode"] == 0 and not changed else "FAIL"
    return result


def update_completion(results: dict[str, Any]) -> dict[str, Any]:
    completion = json.loads(COMPLETION_JSON.read_text(encoding="utf-8"))
    all_results_pass = all(str(result.get("status", "")).startswith("PASS") for result in results.values())
    for item in completion.get("prompt_to_artifact_checklist", []):
        if item["status"] == "PENDING_VERIFIER":
            item["status"] = "PASS_VERIFIED" if all_results_pass else "FAIL_VERIFIER"
    checklist_pass = all(str(item.get("status", "")).startswith("PASS") for item in completion.get("prompt_to_artifact_checklist", []))
    completion["verification_observed_at_utc"] = now_utc()
    completion["verification_results_observed"] = results
    completion["verification_status"] = "PASS" if all_results_pass else "FAIL"
    completion["can_mark_goal_complete"] = bool(all_results_pass and checklist_pass)
    COMPLETION_JSON.write_text(json.dumps(completion, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        f"# CNR Next Model Completion Audit - {DATE}",
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
        "generated_json_jsonl_parse": parse_generated_machine_files(),
        "builder_invariant_recompute": recompute_builder_invariants(),
        "boundary_flag_scan": scan_boundary_flags(),
        "no_leak_duplicate_samplefloor": verify_no_leak_duplicate_samplefloor_artifact(),
        "source_path_hash_recompute": verify_source_hashes(),
        "py_compile": run_command([sys.executable, "-B", "-m", "py_compile", str(BUILDER), str(VERIFIER), str(TEST_FILE)]),
        "focused_pytest": run_command([sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(TEST_FILE), "-q"]),
        "forbidden_live_surface_diff_scan": scan_live_surface_diff(),
    }
    completion = update_completion(results)
    print(json.dumps({"verification_status": completion["verification_status"], "can_mark_goal_complete": completion["can_mark_goal_complete"]}, sort_keys=True))
    return 0 if completion["verification_status"] == "PASS" and completion["can_mark_goal_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
