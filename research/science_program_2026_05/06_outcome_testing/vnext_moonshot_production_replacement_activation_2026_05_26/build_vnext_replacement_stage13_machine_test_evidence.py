from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

OUTPUT = ROUTE_DIR / f"VNEXT_REPLACEMENT_STAGE13_MACHINE_TEST_EVIDENCE_{DATE}.json"
FOCUSED_STAGE12_TEST = ROUTE_DIR / "test_vnext_replacement_stage12_semantic_verifier.py"
STAGE12_SEMANTIC_VERIFIER = ROUTE_DIR / "verify_vnext_replacement_stage12_semantic_red_team.py"
OUTPUT_MANIFEST_VERIFIER = ROUTE_DIR / "verify_vnext_replacement_output_manifest.py"
ROUTE_STATE_VERIFIER = ROUTE_DIR / "verify_vnext_replacement_route_state_integrity.py"

VALIDATED_INPUTS = [
    "config/agent_config.yaml",
    "src/components/gtos_vnext_runtime.py",
    "src/components/orchestrator.py",
    "src/components/execution.py",
    "tests/test_gtos_vnext_runtime.py",
    "tests/test_j46_j49_policy.py",
    "tests/test_limit_order_flow.py",
    f"research/science_program_2026_05/06_outcome_testing/{ROUTE_ID}/test_vnext_replacement_stage12_semantic_verifier.py",
    f"research/science_program_2026_05/06_outcome_testing/{ROUTE_ID}/verify_vnext_replacement_stage12_semantic_red_team.py",
    f"research/science_program_2026_05/06_outcome_testing/{ROUTE_ID}/verify_vnext_replacement_output_manifest.py",
    f"research/science_program_2026_05/06_outcome_testing/{ROUTE_ID}/verify_vnext_replacement_route_state_integrity.py",
    f"research/science_program_2026_05/06_outcome_testing/{ROUTE_ID}/VNEXT_REPLACEMENT_FINAL_SEMANTIC_VERIFICATION_RESULT_{DATE}.json",
]


def _git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _run(command: list[str], command_id: str) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    started_monotonic = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    ended = datetime.now(timezone.utc)
    return {
        "command": " ".join(command),
        "duration_seconds": round(time.monotonic() - started_monotonic, 3),
        "ended_at_utc": ended.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "exit_code": completed.returncode,
        "id": command_id,
        "started_at_utc": started.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "status": "passed" if completed.returncode == 0 else "failed",
        "stderr_tail": completed.stderr[-4000:],
        "stdout_tail": completed.stdout[-4000:],
    }


def main() -> int:
    commands = [
        (
            [
                sys.executable,
                str(STAGE12_SEMANTIC_VERIFIER),
                "--check",
            ],
            "stage12_semantic_verifier_check_mode",
        ),
        (
            [
                sys.executable,
                str(OUTPUT_MANIFEST_VERIFIER),
                "--check",
            ],
            "output_manifest_verifier_check_mode",
        ),
        (
            [
                sys.executable,
                str(ROUTE_STATE_VERIFIER),
                "--check",
            ],
            "route_state_integrity_verifier_check_mode",
        ),
        (
            [
                sys.executable,
                "-m",
                "pytest",
                str(FOCUSED_STAGE12_TEST),
                "-q",
                "--basetemp=.pytest-tmp-vnext-stage13-machine-evidence",
                "-o",
                "cache_dir=.pytest-tmp-vnext-stage13-machine-cache",
            ],
            "stage12_semantic_pytest",
        ),
    ]
    results = [_run(command, command_id) for command, command_id in commands]
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    input_hashes = {
        path: _sha256(REPO_ROOT / path)
        for path in VALIDATED_INPUTS
    }
    payload = {
        "commands": results,
        "current_head": _git(["log", "-1", "--oneline"]),
        "generated_at_utc": generated_at,
        "input_hashes": input_hashes,
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_stage13_machine_test_evidence_v1",
        "status": "passed" if all(row["exit_code"] == 0 for row in results) else "failed",
        "validated_inputs": VALIDATED_INPUTS,
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": _rel(OUTPUT), "status": payload["status"]}, sort_keys=True))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
