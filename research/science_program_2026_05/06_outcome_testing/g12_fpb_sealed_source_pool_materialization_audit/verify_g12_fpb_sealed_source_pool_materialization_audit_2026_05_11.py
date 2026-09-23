#!/usr/bin/env python3
"""Verify the G12 FPB sealed source pool materialization audit artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
DATE_TAG = "2026-05-11"
PREFIX = "G12_FPB_SEALED_SOURCE_POOL_MATERIALIZATION_AUDIT"
VERIFY_PATH = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
BUILDER_PATH = ROUTE_DIR / "build_g12_fpb_sealed_source_pool_materialization_audit_2026_05_11.py"
TEST_PATH = ROUTE_DIR / "test_g12_fpb_sealed_source_pool_materialization_audit_2026_05_11.py"

REQUIRED_JSON = {
    "audit": ROUTE_DIR / f"{PREFIX}_{DATE_TAG}.json",
    "completion": ROUTE_DIR / f"{PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    "scid": ROUTE_DIR / f"{PREFIX}_SCID_SOURCE_HASH_COVERAGE_AUDIT_{DATE_TAG}.json",
    "discovery": ROUTE_DIR / f"{PREFIX}_DISCOVERY_EXCLUSION_AUDIT_{DATE_TAG}.json",
    "csv": ROUTE_DIR / f"{PREFIX}_CSV_ZERO_CANDIDATE_AUDIT_{DATE_TAG}.json",
    "baseline": ROUTE_DIR / f"{PREFIX}_ADVERSARIAL_BASELINE_AUDIT_{DATE_TAG}.json",
    "gates": ROUTE_DIR / f"{PREFIX}_SCID_ASOF_GENERATOR_GATE_AUDIT_{DATE_TAG}.json",
    "blockers": ROUTE_DIR / f"{PREFIX}_REPAIR_BLOCKER_LEDGER_{DATE_TAG}.json",
    "next_prompt": ROUTE_DIR / f"{PREFIX}_NEXT_PROMPT_PACK_{DATE_TAG}.json",
    "manifest": ROUTE_DIR / f"{PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
}

EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def run_cmd(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)
    return {
        "args": args,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "ok": proc.returncode == 0,
    }


def stable_pytest_result(result: dict[str, Any], basetemp: str) -> dict[str, Any]:
    stable = dict(result)
    stable["args"] = ["<workspace_temp_dir>" if arg == basetemp else arg for arg in result["args"]]
    stable["stdout"] = "\n".join(
        line.split(" in ")[0].strip()
        for line in result["stdout"].splitlines()
        if " passed" in line or " failed" in line or " error" in line
    )
    if stable["stdout"]:
        stable["stdout"] += "\n"
    return stable


def verify() -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in REQUIRED_JSON.items():
        if not path.exists():
            failures.append(f"missing {name}: {path.as_posix()}")
            continue
        payloads[name] = load(path)

    audit = payloads.get("audit", {})
    completion = payloads.get("completion", {})
    scid = payloads.get("scid", {})
    discovery = payloads.get("discovery", {})
    csv = payloads.get("csv", {})
    baseline = payloads.get("baseline", {})
    gates = payloads.get("gates", {})
    blockers = payloads.get("blockers", {})
    next_prompt = payloads.get("next_prompt", {})
    manifest = payloads.get("manifest", {})

    allowed_decisions = {
        "ACCEPT_SOURCE_POOL_SOURCE_CONTROL_ONLY_NEXT_SCID_ASOF_CONTRACT_REQUIRED",
        "REPAIR_BLOCKED_SOURCE_POOL_PACKET",
    }
    if audit.get("audit_decision") not in allowed_decisions:
        failures.append("audit decision is neither accepted nor repair-blocked")
    for payload_name, payload in payloads.items():
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{payload_name} promotion_verdict mismatch")
        for flag in ["validation_safe", "outcome_review_opened", "live_effect"]:
            if payload.get(flag) is not False:
                failures.append(f"{payload_name} {flag} is not false")

    if scid.get("candidate_count") != 9:
        failures.append("SCID candidate count is not 9")
    if not all(row.get("recomputed_sha256") for row in scid.get("audit_rows", [])):
        failures.append("not all SCID candidates were independently rehashed")

    if discovery.get("selected_source_rows_in_source_selection") != 365:
        failures.append("selected source row count is not 365")
    if discovery.get("selected_hash_count") != 365:
        failures.append("selected hash count is not 365")
    if discovery.get("selected_candidate_hash_overlap"):
        failures.append("selected/candidate hash overlap is non-empty")
    if discovery.get("accepted_fpb_path_label_rows_excluded") != 12_852_758:
        failures.append("accepted FPB path-label exclusion count mismatch")
    if not all(discovery.get("checks", {}).values()):
        failures.append("discovery exclusion checks did not all pass")

    if csv.get("accepted_csv_candidate_count") != 0:
        failures.append("CSV accepted candidate count is not zero")
    if not all(csv.get("checks", {}).values()):
        failures.append("CSV zero-candidate checks did not all pass")

    if baseline.get("expected_baselines") != EXPECTED_BASELINES:
        failures.append("expected baseline list mismatch")
    if not all(baseline.get("checks", {}).values()):
        failures.append("baseline checks did not all pass")

    if not all(gates.get("checks", {}).values()):
        failures.append("SCID as-of/generator gate checks did not all pass")

    if audit.get("audit_decision") == "ACCEPT_SOURCE_POOL_SOURCE_CONTROL_ONLY_NEXT_SCID_ASOF_CONTRACT_REQUIRED":
        if blockers.get("repair_blocker_count") != 0:
            failures.append("accepted audit has nonzero repair blockers")
        if next_prompt.get("next_route_id") != "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT":
            failures.append("accepted next prompt route mismatch")
    if audit.get("audit_decision") == "REPAIR_BLOCKED_SOURCE_POOL_PACKET":
        if blockers.get("repair_blocker_count", 0) <= 0:
            failures.append("repair-blocked audit has no repair blockers")
        if blockers.get("repair_blockers_exact_and_actionable") is not True:
            failures.append("repair blockers are not exact/actionable")
        if next_prompt.get("next_route_id") != "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR":
            failures.append("repair-blocked next prompt route mismatch")
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion standard is not satisfied")
    if completion.get("can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh") is not True:
        failures.append("completion gate is not true")
    if not manifest.get("artifacts"):
        failures.append("manifest has no artifacts")

    with tempfile.TemporaryDirectory(prefix=".tmp_pytest_g12_fpb_source_audit_verify_", dir=ROOT) as basetemp:
        focused_tests = run_cmd(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                rel(TEST_PATH),
                "-p",
                "no:cacheprovider",
                "--basetemp",
                basetemp,
            ]
        )
        focused_tests = stable_pytest_result(focused_tests, basetemp)
    py_compile = run_cmd([sys.executable, "-m", "py_compile", rel(BUILDER_PATH), rel(Path(__file__)), rel(TEST_PATH)])
    if not focused_tests["ok"]:
        failures.append("focused pytest failed")
    if not py_compile["ok"]:
        failures.append("py_compile failed")

    result = {
        "ok": not failures,
        "can_mark_goal_complete_after_commit_and_context_refresh": not failures,
        "failures": failures,
        "focused_tests": focused_tests,
        "py_compile": py_compile,
        "audit_decision": audit.get("audit_decision"),
        "promotion_verdict": audit.get("promotion_verdict"),
        "validation_safe": audit.get("validation_safe"),
        "outcome_review_opened": audit.get("outcome_review_opened"),
        "live_effect": audit.get("live_effect"),
        "accepted_scid_after_audit": scid.get("accepted_candidate_count_after_audit"),
        "selected_hash_count": discovery.get("selected_hash_count"),
        "accepted_csv_candidate_count": csv.get("accepted_csv_candidate_count"),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
