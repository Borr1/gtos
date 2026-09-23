#!/usr/bin/env python3
"""Verify the FPB immutable SCID segment-hash freeze repair artifacts."""

from __future__ import annotations

import importlib.util
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
PREFIX = "FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR"
FILE_PREFIX = "FPB_SCID_FREEZE_REPAIR"
VERIFY_PATH = ROUTE_DIR / f"{PREFIX}_VERIFICATION_RESULT_{DATE_TAG}.json"
BUILDER_PATH = ROUTE_DIR / "build_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"
TEST_PATH = ROUTE_DIR / "test_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_2026_05_11.py"

REQUIRED_JSON = {
    "packet": ROUTE_DIR / f"{FILE_PREFIX}_{DATE_TAG}.json",
    "source_freeze": ROUTE_DIR / f"{FILE_PREFIX}_SOURCE_FREEZE_LEDGER_{DATE_TAG}.json",
    "snapshot_segment": ROUTE_DIR / f"{FILE_PREFIX}_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}.json",
    "source_hash": ROUTE_DIR / f"{FILE_PREFIX}_SOURCE_HASH_MANIFEST_{DATE_TAG}.json",
    "duplicate": ROUTE_DIR / f"{FILE_PREFIX}_DUPLICATE_EXCLUSION_AUDIT_{DATE_TAG}.json",
    "parser": ROUTE_DIR / f"{FILE_PREFIX}_PARSER_ASOF_NOLEAK_AUDIT_{DATE_TAG}.json",
    "dirty": ROUTE_DIR / f"{FILE_PREFIX}_NOLEAK_DIRTY_AUDIT_{DATE_TAG}.json",
    "hardening": ROUTE_DIR / f"{FILE_PREFIX}_HARDENING_LEDGER_{DATE_TAG}.json",
    "saturation": ROUTE_DIR / f"{FILE_PREFIX}_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
    "completion": ROUTE_DIR / f"{FILE_PREFIX}_COMPLETION_AUDIT_{DATE_TAG}.json",
    "manifest": ROUTE_DIR / f"{FILE_PREFIX}_OUTPUT_MANIFEST_{DATE_TAG}.json",
}
NEXT_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_FPB_SEALED_SOURCE_POOL_IMMUTABLE_SCID_HASH_FREEZE_REPAIR_REAUDIT_GOAL_PROMPT_2026-05-11.md"
)
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
RAW_SOURCE_SUFFIXES = {".scid", ".dly", ".parquet", ".csv", ".bin", ".scidseg"}


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


def load_builder():
    spec = importlib.util.spec_from_file_location("fpb_scid_freeze_builder_verify", BUILDER_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("could not load builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify() -> dict[str, Any]:
    failures: list[str] = []
    payloads: dict[str, dict[str, Any]] = {}
    for name, path in REQUIRED_JSON.items():
        if not path.exists():
            failures.append(f"missing {name}: {rel(path)}")
            continue
        payloads[name] = load(path)

    for payload_name, payload in payloads.items():
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{payload_name} promotion_verdict mismatch")
        for flag in ["validation_safe", "outcome_review_opened", "live_effect"]:
            if payload.get(flag) is not False:
                failures.append(f"{payload_name} {flag} is not false")
        for flag in [
            "opens_validation",
            "opens_result_scoring",
            "opens_promotion",
            "opens_live_trading_behavior",
            "opens_paid_api_or_databento_route",
            "opens_mt5_order_account_history_behavior",
        ]:
            if payload.get(flag) is not False:
                failures.append(f"{payload_name} {flag} is not false")

    packet = payloads.get("packet", {})
    source_freeze = payloads.get("source_freeze", {})
    snapshot_segment = payloads.get("snapshot_segment", {})
    source_hash = payloads.get("source_hash", {})
    duplicate = payloads.get("duplicate", {})
    parser = payloads.get("parser", {})
    dirty = payloads.get("dirty", {})
    hardening = payloads.get("hardening", {})
    saturation = payloads.get("saturation", {})
    completion = payloads.get("completion", {})
    manifest = payloads.get("manifest", {})

    if source_freeze.get("candidate_count") != 9:
        failures.append("source freeze candidate_count is not 9")
    if source_freeze.get("repaired_source_count") != 9:
        failures.append("not all 9 sources repaired")
    if source_freeze.get("source_access_blocker_count") != 0:
        failures.append("source access blockers remain")
    if not source_freeze.get("all_9_sources_repaired"):
        failures.append("all_9_sources_repaired is not true")
    if snapshot_segment.get("segment_count") != 9:
        failures.append("segment manifest count is not 9")
    if snapshot_segment.get("raw_snapshot_files_committed") != 0:
        failures.append("raw snapshot files committed count is nonzero")
    if not source_hash.get("all_accepted_hashes_present"):
        failures.append("not all accepted segment hashes are present")
    if duplicate.get("selected_source_rows_preserved") != 365:
        failures.append("selected source rows preserved is not 365")
    if duplicate.get("selected_segment_hash_overlap"):
        failures.append("segment hash overlaps selected discovery hashes")
    if duplicate.get("duplicate_segment_hashes"):
        failures.append("duplicate segment hashes found")
    if duplicate.get("baseline_controls_present") != EXPECTED_BASELINES:
        failures.append("four baseline controls not preserved exactly")
    if not all(duplicate.get("checks", {}).values()):
        failures.append("duplicate/discovery checks did not all pass")
    if not all(parser.get("checks", {}).values()):
        failures.append("parser/as-of/no-leak checks did not all pass")
    if not all(dirty.get("checks", {}).values()):
        failures.append("dirty-state scoped checks did not all pass")
    if not hardening.get("all_hardening_controls_covered"):
        failures.append("hardening coverage incomplete")
    if not saturation.get("same_evidence_class_gaps_closed"):
        failures.append("saturation gaps remain")
    if packet.get("validation_execution_prompt_emitted") is not False:
        failures.append("validation execution prompt emitted")
    if "SCID_TO_ASOF_BAR" not in packet.get("scid_to_asof_bar_derivation_contract_gate", ""):
        failures.append("SCID-to-asof gate missing")
    if not NEXT_PROMPT.exists():
        failures.append("next G12 repair reaudit prompt missing")
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion standard not satisfied")
    if not manifest.get("artifacts"):
        failures.append("output manifest has no artifacts")

    raw_blob_paths = [
        rel(path)
        for path in ROUTE_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in RAW_SOURCE_SUFFIXES
    ]
    if raw_blob_paths:
        failures.append(f"raw source blob files found in route: {raw_blob_paths}")

    builder = load_builder()
    segment_rehash = builder.verify_segments_from_manifest()
    if not segment_rehash["ok"]:
        failures.append("segment rehash from manifest failed")

    with tempfile.TemporaryDirectory(prefix=".tmp_pytest_fpb_scid_freeze_", dir=ROOT) as basetemp:
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
    pycache_root = ROOT / "_codex_pycache"
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
    if not focused_tests["ok"]:
        failures.append("focused pytest failed")
    if not py_compile["ok"]:
        failures.append("py_compile failed")

    result = {
        "ok": not failures,
        "can_mark_goal_complete_after_commit_and_context_refresh": not failures,
        "failures": failures,
        "segment_rehash": segment_rehash,
        "focused_tests": focused_tests,
        "py_compile": py_compile,
        "terminal_decision": packet.get("terminal_decision"),
        "repaired_source_count": source_freeze.get("repaired_source_count"),
        "selected_source_rows_preserved": duplicate.get("selected_source_rows_preserved"),
        "baseline_controls_present": duplicate.get("baseline_controls_present"),
        "completion_standard_satisfied": completion.get("completion_standard_satisfied"),
        "promotion_verdict": packet.get("promotion_verdict"),
        "validation_safe": packet.get("validation_safe"),
        "outcome_review_opened": packet.get("outcome_review_opened"),
        "live_effect": packet.get("live_effect"),
    }
    VERIFY_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
