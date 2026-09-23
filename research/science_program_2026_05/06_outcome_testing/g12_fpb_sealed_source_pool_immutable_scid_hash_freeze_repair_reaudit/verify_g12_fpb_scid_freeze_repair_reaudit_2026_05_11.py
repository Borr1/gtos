#!/usr/bin/env python3
"""Verify the G12 FPB SCID freeze-repair reaudit artifacts."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
DATE_TAG = "2026-05-11"
FILE_PREFIX = "G12_FPB_SCID_FREEZE_REPAIR_REAUDIT"
VERIFY_PATH = ROUTE_DIR / f"{FILE_PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
BUILDER_PATH = ROUTE_DIR / "build_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py"
TEST_PATH = ROUTE_DIR / "test_g12_fpb_scid_freeze_repair_reaudit_2026_05_11.py"

TARGET_DIR = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "06_outcome_testing"
    / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
)
TARGET_VERIFIER = TARGET_DIR / "verify_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"
TARGET_TEST = TARGET_DIR / "test_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"
NEXT_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_GOAL_PROMPT_2026-05-11.md"
)

REQUIRED_JSON = {
    "decision": ROUTE_DIR / f"{FILE_PREFIX}_DECISION_LEDGER_{DATE_TAG}.json",
    "rehash": ROUTE_DIR / f"{FILE_PREFIX}_SOURCE_REHASH_AUDIT_{DATE_TAG}.json",
    "noleak": ROUTE_DIR / f"{FILE_PREFIX}_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json",
    "dirty": ROUTE_DIR / f"{FILE_PREFIX}_DIRTY_PATH_AUDIT_{DATE_TAG}.json",
    "blockers": ROUTE_DIR / f"{FILE_PREFIX}_BLOCKER_LEDGER_{DATE_TAG}.json",
    "completion": ROUTE_DIR / f"{FILE_PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    "manifest": ROUTE_DIR / f"{FILE_PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
}
EXPECTED_ACCEPT_DECISIONS = {
    "ACCEPT_AS_SOURCE_CONTROL_IMMUTABLE_SCID_SEGMENT_REPAIR_EVIDENCE_ONLY",
    "ACCEPT_WITH_EXACT_SOURCE_CONTROL_WARNINGS",
}
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
RAW_SOURCE_SUFFIXES = {".scid", ".dly", ".parquet", ".csv", ".bin", ".scidseg"}
SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_promotion",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_paid_api_or_databento_route",
    "opens_remote_push",
    "opens_registry_edit",
    "opens_mt5_order_account_history_behavior",
    "credentials_touched",
    "changes_live_trading_behavior",
]


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_cmd(args: list[str], env_extra: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False, env=env)
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


def raw_blob_paths_under(path: Path) -> list[str]:
    if not path.exists():
        return []
    return sorted(
        rel(child)
        for child in path.rglob("*")
        if child.is_file() and child.suffix.lower() in RAW_SOURCE_SUFFIXES
    )


def verify() -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in REQUIRED_JSON.items():
        if not path.exists():
            failures.append(f"missing required JSON {name}: {rel(path)}")
            continue
        payloads[name] = load(path)

    for payload_name, payload in payloads.items():
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{payload_name} promotion_verdict mismatch")
        for flag in SAFE_FALSE_FLAGS:
            if payload.get(flag) is not False:
                failures.append(f"{payload_name} {flag} is not false")

    decision = payloads.get("decision", {})
    rehash = payloads.get("rehash", {})
    noleak = payloads.get("noleak", {})
    dirty = payloads.get("dirty", {})
    blockers = payloads.get("blockers", {})
    completion = payloads.get("completion", {})
    manifest = payloads.get("manifest", {})

    terminal = decision.get("terminal_decision")
    if terminal not in EXPECTED_ACCEPT_DECISIONS:
        failures.append(f"terminal decision not accepted source-control evidence: {terminal}")
    if decision.get("accepted_validation_execution") is not False:
        failures.append("decision accepted validation execution")
    if decision.get("accepted_result_scoring") is not False:
        failures.append("decision accepted result scoring")
    if decision.get("accepted_promotion") is not False:
        failures.append("decision accepted promotion")

    if rehash.get("summary", {}).get("segment_count") != 9:
        failures.append("rehash segment count is not 9")
    for check_name, ok in rehash.get("checks", {}).items():
        if ok is not True:
            failures.append(f"rehash check failed: {check_name}")
    for row in rehash.get("segment_rehash_rows", []):
        if row.get("raw_byte_rehash_sha256_first_pass") != row.get("manifest_segment_records_sha256"):
            failures.append(f"raw-byte rehash mismatch for {row.get('source')}")
        if row.get("raw_byte_rehash_sha256_first_pass") != row.get("raw_byte_rehash_sha256_second_pass"):
            failures.append(f"raw-byte deterministic rehash mismatch for {row.get('source')}")
        if row.get("timestamp_scan", {}).get("records_below_eligible_floor") != 0:
            failures.append(f"pre-floor timestamp leaked into segment for {row.get('source')}")

    for check_name, ok in noleak.get("checks", {}).items():
        if ok is not True:
            failures.append(f"noleak/partition check failed: {check_name}")
    if noleak.get("baseline_controls_present") != EXPECTED_BASELINES:
        failures.append("baseline controls are not exact")
    if noleak.get("segment_selected_source_hash_overlap"):
        failures.append("segment hash overlaps selected discovery source hash")

    if blockers.get("blocker_count") != 0:
        failures.append("accepted G12 reaudit has nonzero blockers")
    if dirty.get("summary", {}).get("raw_blob_path_count") != 0:
        failures.append("raw market-data blob path found in scoped/target route")
    if dirty.get("summary", {}).get("forbidden_live_surface_dirty_path_count") != 0:
        failures.append("forbidden live-surface dirty path detected")
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion standard is not satisfied")
    if completion.get("can_mark_goal_complete_after_verifier_tests_commit_and_context_refresh") is not True:
        failures.append("completion closeout gate is not true")
    if not manifest.get("artifacts"):
        failures.append("output manifest has no artifacts")
    if not NEXT_PROMPT.exists():
        failures.append("accepted next source-control prompt is missing")

    route_raw_blobs = raw_blob_paths_under(ROUTE_DIR)
    if route_raw_blobs:
        failures.append(f"raw blobs found under G12 route: {route_raw_blobs}")

    target_verifier = run_cmd([sys.executable, rel(TARGET_VERIFIER)])
    if not target_verifier["ok"]:
        failures.append("target repair verifier failed")
    with tempfile.TemporaryDirectory(prefix=".tmp_pytest_g12_fpb_scid_reaudit_", dir=ROOT) as basetemp:
        target_tests = run_cmd(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                rel(TARGET_TEST),
                "-p",
                "no:cacheprovider",
                "--basetemp",
                basetemp,
            ]
        )
        target_tests = stable_pytest_result(target_tests, basetemp)
    if not target_tests["ok"]:
        failures.append("target focused pytest failed")

    with tempfile.TemporaryDirectory(prefix=".tmp_pytest_g12_fpb_scid_reaudit_self_", dir=ROOT) as basetemp:
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
    if not focused_tests["ok"]:
        failures.append("G12 focused pytest failed")

    pycache_root = ROOT / "_codex_pycache" / "g12_scid_reaudit"
    pycache_root.mkdir(parents=True, exist_ok=True)
    compile_snippet = (
        "import pathlib, py_compile, sys; "
        "out=pathlib.Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True); "
        "[py_compile.compile(path, cfile=str(out / (str(i) + '.pyc')), doraise=True) "
        "for i, path in enumerate(sys.argv[2:])]"
    )
    py_compile = run_cmd(
        [
            sys.executable,
            "-c",
            compile_snippet,
            str(pycache_root),
            rel(BUILDER_PATH),
            rel(Path(__file__)),
            rel(TEST_PATH),
        ]
    )
    if not py_compile["ok"]:
        failures.append("py_compile failed")

    result = {
        "ok": not failures,
        "can_mark_goal_complete_after_commit_and_context_refresh": not failures,
        "failures": failures,
        "terminal_decision": terminal,
        "segment_count": rehash.get("summary", {}).get("segment_count"),
        "selected_source_count_declared": noleak.get("selected_source_count_declared"),
        "g0_selected_source_count": noleak.get("g0_selected_source_count"),
        "baseline_controls_present": noleak.get("baseline_controls_present"),
        "target_repair_verifier": target_verifier,
        "target_focused_tests": target_tests,
        "focused_tests": focused_tests,
        "py_compile": py_compile,
        "promotion_verdict": decision.get("promotion_verdict"),
        "validation_safe": decision.get("validation_safe"),
        "outcome_review_opened": decision.get("outcome_review_opened"),
        "live_effect": decision.get("live_effect"),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
