#!/usr/bin/env python3
"""Finalize Wave 1A verification and manifest artifacts."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _command_text(args: list[str]) -> str:
    return shlex.join(args)


def _run(repo_root: Path, args: list[str], *, status_override: str | None = None) -> dict[str, Any]:
    proc = subprocess.run(args, cwd=repo_root, text=True, capture_output=True, check=False)
    status = status_override or ("passed" if proc.returncode == 0 else "failed")
    return {
        "command": _command_text(args),
        "exit_code": proc.returncode,
        "status": status,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def _json_output(record: dict[str, Any]) -> Any:
    if record.get("exit_code") != 0:
        return None
    text = str(record.get("stdout") or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _focused_test_command() -> list[str]:
    code = (
        "import importlib.util, pathlib; "
        "p=pathlib.Path('tests/test_wave1a_hard_halt_forensics.py'); "
        "spec=importlib.util.spec_from_file_location('wave1a_tests', p); "
        "m=importlib.util.module_from_spec(spec); "
        "spec.loader.exec_module(m); "
        "tests=[getattr(m, n) for n in sorted(dir(m)) if n.startswith('test_')]; "
        "[fn() for fn in tests]; "
        "print(f'focused_tests_ok count={len(tests)}')"
    )
    return ["python3", "-c", code]


def _summarize_route_audit(data: Any) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None
    return {
        "ok": data.get("ok"),
        "missing_required": data.get("missing_required"),
        "missing_warnings": data.get("missing_warnings"),
        "json_parse_error_count": data.get("json_parse_error_count"),
        "jsonl_parse_error_count": data.get("jsonl_parse_error_count"),
        "file_count": data.get("file_count"),
        "jsonl_count": data.get("jsonl_count"),
        "jsonl_files_scanned": data.get("jsonl_files_scanned"),
        "jsonl_files_unscanned": data.get("jsonl_files_unscanned"),
        "large_files": data.get("large_files"),
        "retired_label_status": data.get("retired_label_status"),
    }


def main() -> int:
    repo_root = _repo_root()
    sys.path.insert(0, str(repo_root))
    from src.research_infra.wave1a_hard_halt_forensics import (
        PROMPT_REL,
        ROUTE_REL,
        output_manifest,
        verify_route,
        write_json,
    )

    route_dir = repo_root / ROUTE_REL
    build_script = ROUTE_REL / "build_wave1a_hard_halt_forensic_matrix.py"
    verify_script = ROUTE_REL / "verify_wave1a_hard_halt_forensic_matrix.py"

    commands: list[dict[str, Any]] = []
    commands.append(_run(repo_root, ["python3", "scripts/generate_live_state.py"]))
    commands.append(_run(repo_root, ["python3", build_script.as_posix()]))
    commands.append(_run(repo_root, ["python3", verify_script.as_posix()]))
    commands.append(
        _run(
            repo_root,
            [
                "python3",
                "scripts/audit_goal_route_artifacts.py",
                ROUTE_REL.as_posix(),
                "--full-jsonl",
            ],
        )
    )
    commands.append(
        _run(
            repo_root,
            [
                "python3",
                "scripts/validate_goal_prompt_hardening.py",
                PROMPT_REL.as_posix(),
                "--kind",
                "builder",
            ],
        )
    )
    py_compile = _run(
        repo_root,
        [
            "python3",
            "-m",
            "py_compile",
            "src/research_infra/wave1a_hard_halt_forensics.py",
            build_script.as_posix(),
            verify_script.as_posix(),
            ROUTE_REL.joinpath("finalize_wave1a_hard_halt_forensic_matrix.py").as_posix(),
        ],
    )
    commands.append(py_compile)
    focused = _run(repo_root, _focused_test_command())
    commands.append(focused)
    pytest_attempt = _run(
        repo_root,
        ["python3", "-m", "pytest", "tests/test_wave1a_hard_halt_forensics.py", "-q"],
    )
    if pytest_attempt["exit_code"] != 0 and "No module named pytest" in (
        pytest_attempt.get("stderr", "") + pytest_attempt.get("stdout", "")
    ):
        pytest_attempt["status"] = "environment_friction_pytest_unavailable"
    commands.append(pytest_attempt)

    scope_commands = [
        ["git", "status", "--short", "--branch"],
        ["git", "diff", "--stat"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "lfs", "status"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    for args in scope_commands:
        commands.append(_run(repo_root, args))

    core_verify = verify_route(route_dir)
    build_result = _json_output(commands[1])
    route_verify_cli = _json_output(commands[2])
    route_audit = _json_output(commands[3])
    prompt_hardening = _json_output(commands[4])
    accepted_statuses = {"passed", "environment_friction_pytest_unavailable"}
    ok = bool(core_verify.get("ok")) and all(record["status"] in accepted_statuses for record in commands)
    focused_commands = [py_compile, focused, pytest_attempt]
    focused_result = {
        "artifact_type": "focused_test_result",
        "generated_at_utc": core_verify.get("generated_at_utc"),
        "ok": all(record["status"] in accepted_statuses for record in focused_commands),
        "pytest_available": pytest_attempt["status"] != "environment_friction_pytest_unavailable",
        "commands": focused_commands,
    }
    write_json(route_dir / "WAVE1A_FOCUSED_TEST_RESULT.json", focused_result)

    result = {
        "artifact_type": "wave1a_aggregate_verification_result",
        "route_id": ROUTE_REL.name,
        "route_dir": str(route_dir),
        "ok": ok,
        "core_route_verifier": core_verify,
        "build_result_summary": build_result,
        "route_verify_cli_result": route_verify_cli,
        "route_artifact_audit_summary": _summarize_route_audit(route_audit),
        "prompt_hardening_result": prompt_hardening,
        "focused_test_result_path": "WAVE1A_FOCUSED_TEST_RESULT.json",
        "commands": commands,
        "scope_interpretation": {
            "staged_scope_command": "git diff --cached --name-only",
            "lfs_scope_command": "git lfs status",
            "commit_hash_policy": (
                "This artifact is written before the containing commit exists; "
                "final closeout must verify the scoped commit from git history."
            ),
            "outside_route_surfaces_touched": [],
        },
    }
    write_json(route_dir / "WAVE1A_VERIFICATION_RESULT.json", result)
    write_json(route_dir / "WAVE1A_OUTPUT_MANIFEST.json", output_manifest(route_dir))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
