"""Verifier for G12_NOFILL_LIFECYCLE_CLOSURE_SOURCE_PACKET_AUDIT_V1."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import build_g12_nofill_close_audit_2026_05_08 as builder


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]

REQUIRED_JSON = [
    "G12_NOFILL_CLOSE_CONTEXT_ANCHOR_2026-05-08.json",
    "G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json",
    "G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json",
    "G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.json",
    "G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json",
    "G12_NOFILL_CLOSE_LABEL_FAMILY_AUDIT_2026-05-08.json",
    "G12_NOFILL_CLOSE_BLOCKER_AND_REQUEST_AUDIT_2026-05-08.json",
    "G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json",
    "G12_NOFILL_CLOSE_FORENSICS_AND_LEARNING_2026-05-08.json",
    "G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json",
]

REQUIRED_MD = [name.replace(".json", ".md") for name in REQUIRED_JSON] + [
    "G12_NOFILL_CLOSE_NEXT_PROMPT_PACK_2026-05-08.md",
]


def load_json(name: str) -> Any:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def py_compile_check() -> dict[str, Any]:
    scripts = [
        OUT_DIR / "build_g12_nofill_close_audit_2026_05_08.py",
        OUT_DIR / "verify_g12_nofill_close_audit_2026_05_08.py",
        OUT_DIR / "test_g12_nofill_close_audit_2026_05_08.py",
    ]
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "py_compile", *[str(path) for path in scripts]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {"command": "python -B -m py_compile ...", "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def live_surface_diff_check() -> dict[str, Any]:
    paths = [
        "src",
        "prompts",
        "config",
        "scripts/canary_fixtures",
        "scripts/canary_test.py",
        "run_agent.py",
        "start_all.bat",
        "requirements.txt",
        ".env",
    ]
    safe_dir = REPO_ROOT.as_posix()
    committed_cmd = ["git", "-c", f"safe.directory={safe_dir}", "diff", "--name-only", "HEAD^1", "HEAD", "--", *paths]
    committed_proc = subprocess.run(committed_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    committed_names = [line.strip() for line in committed_proc.stdout.splitlines() if line.strip()]

    workspace_cmd = ["git", "-c", f"safe.directory={safe_dir}", "diff", "--name-only", "--", *paths]
    workspace_proc = subprocess.run(workspace_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    workspace_names = [line.strip() for line in workspace_proc.stdout.splitlines() if line.strip()]

    scope_cmd = ["git", "-c", f"safe.directory={safe_dir}", "diff", "--name-only", "HEAD^1", "HEAD"]
    scope_proc = subprocess.run(scope_cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    committed_scope = [line.strip().replace("\\", "/") for line in scope_proc.stdout.splitlines() if line.strip()]
    audit_committed_scope = any(
        path.startswith("research/science_program_2026_05/06_outcome_testing/g12_no_fill_closure_audit/")
        for path in committed_scope
    )
    names = committed_names if audit_committed_scope else workspace_names
    return {
        "command": "git -c safe.directory=... diff --name-only HEAD^1 HEAD -- live-surface paths"
        if audit_committed_scope
        else "git -c safe.directory=... diff --name-only -- live-surface paths",
        "returncode": committed_proc.returncode if audit_committed_scope else workspace_proc.returncode,
        "checked_scope": "committed_diff_HEAD_parent" if audit_committed_scope else "workspace_status",
        "changed_live_surface_paths": names,
        "workspace_changed_live_surface_paths_observed": workspace_names,
        "status": "PASS" if (committed_proc.returncode if audit_committed_scope else workspace_proc.returncode) == 0 and not names else "FAIL",
        "stderr_tail": (committed_proc.stderr if audit_committed_scope else workspace_proc.stderr)[-1000:],
    }


def focused_pytest_check() -> dict[str, Any]:
    test_path = OUT_DIR / "test_g12_nofill_close_audit_2026_05_08.py"
    proc = subprocess.run(
        [sys.executable, "-B", "-m", "pytest", "-p", "no:cacheprovider", str(test_path), "-q"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": "python -B -m pytest -p no:cacheprovider research/.../test_g12_nofill_close_audit_2026_05_08.py -q",
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def upstream_source_packet_checks() -> dict[str, Any]:
    source_dir = REPO_ROOT / "research/science_program_2026_05/06_outcome_testing/no_fill_lifecycle_closure_source_packet"
    scripts = [
        source_dir / "build_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        source_dir / "verify_nofill_lifecycle_closure_source_packet_2026_05_08.py",
        source_dir / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py",
    ]
    py_compile = subprocess.run(
        [sys.executable, "-B", "-m", "py_compile", *[str(path) for path in scripts]],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    pytest = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            str(source_dir / "test_nofill_lifecycle_closure_source_packet_2026_05_08.py"),
            "-q",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "py_compile": {
            "command": "python -B -m py_compile upstream NOFILL close builder/verifier/test",
            "returncode": py_compile.returncode,
            "stdout_tail": py_compile.stdout[-1000:],
            "stderr_tail": py_compile.stderr[-1000:],
        },
        "focused_pytest": {
            "command": "python -B -m pytest -p no:cacheprovider upstream NOFILL close test -q",
            "returncode": pytest.returncode,
            "stdout_tail": pytest.stdout[-2000:],
            "stderr_tail": pytest.stderr[-2000:],
        },
    }


def verify() -> dict[str, Any]:
    missing = [name for name in REQUIRED_JSON + REQUIRED_MD if not (OUT_DIR / name).exists()]
    parsed = {}
    parse_errors = []
    for name in REQUIRED_JSON:
        try:
            parsed[name] = load_json(name)
        except Exception as exc:  # pragma: no cover - defensive verifier output
            parse_errors.append({"path": name, "error": f"{type(exc).__name__}: {exc}"})

    decision = parsed.get("G12_NOFILL_CLOSE_DECISION_LEDGER_2026-05-08.json", {})
    universe = parsed.get("G12_NOFILL_CLOSE_UNIVERSE_AND_EXCLUSION_AUDIT_2026-05-08.json", {})
    closure = parsed.get("G12_NOFILL_CLOSE_SOURCE_CLOSURE_AUDIT_2026-05-08.json", {})
    hash_noleak = parsed.get("G12_NOFILL_CLOSE_SOURCE_HASH_AND_NOLEAK_AUDIT_2026-05-08.json", {})
    duplicate = parsed.get("G12_NOFILL_CLOSE_DUPLICATE_SAMPLEFLOOR_AUDIT_2026-05-08.json", {})
    label = parsed.get("G12_NOFILL_CLOSE_LABEL_FAMILY_AUDIT_2026-05-08.json", {})

    checks = {
        "required_artifacts_present": not missing,
        "json_parse": not parse_errors,
        "terminal_verdict_valid": decision.get("terminal_verdict") == "ACCEPT_AS_INPUT_ONLY_SOURCE_CLOSURE_EVIDENCE",
        "packet_298_rows": universe.get("packet_rows") == 298,
        "universe_matches_nofill": universe.get("closure_matches_accepted_nofill_universe") is True,
        "six_t3_rows_excluded": (universe.get("six_t3_rows_excluded") or {}).get("status") == "PASS",
        "blocked_94_cnr061_excluded": (universe.get("blocked_94_cnr061_excluded") or {}).get("status") == "PASS",
        "upstream_297_1_verified": (closure.get("upstream_closure_status_counts") or {}).get("source_closed") == 297
        and (closure.get("upstream_closure_status_counts") or {}).get("source_blocked_exact") == 1,
        "g12_corrected_298_0_verified": (closure.get("g12_corrected_closure_status_counts") or {}).get("source_closed") == 298
        and (closure.get("g12_corrected_closure_status_counts") or {}).get("source_blocked_exact") == 0,
        "row_0127_source_closed": (closure.get("row_0127_resolution") or {}).get("g12_closure_status") == "source_closed",
        "source_hashes_match": (hash_noleak.get("g12_recomputed_hashes") or {}).get("strict_source_mismatch_count") == 0
        and (hash_noleak.get("g12_recomputed_hashes") or {}).get("missing_count") == 0,
        "no_leak": hash_noleak.get("no_leak_status") == "PASS",
        "freeze_order": (hash_noleak.get("asof_and_freeze_order") or {}).get("status") == "PASS",
        "duplicate_samplefloor": duplicate.get("g12_status") == "PASS_DUPLICATE_AND_SAMPLE_FLOOR_CONTROLS_BLOCK_VALIDATION",
        "label_family": label.get("status") == "PASS_LABEL_FAMILY_SEPARATION_PRESERVED",
    }

    py_compile = py_compile_check()
    focused_pytest = focused_pytest_check()
    upstream_checks = upstream_source_packet_checks()
    live_surface = live_surface_diff_check()
    live_state = builder.run_live_state_regeneration()

    checks["py_compile"] = py_compile["returncode"] == 0
    checks["focused_pytest"] = focused_pytest["returncode"] == 0
    checks["upstream_source_packet_py_compile"] = upstream_checks["py_compile"]["returncode"] == 0
    checks["upstream_source_packet_focused_pytest"] = upstream_checks["focused_pytest"]["returncode"] == 0
    checks["live_surface_diff"] = live_surface["status"] == "PASS"
    checks["live_state_regenerated_at_closeout"] = live_state["returncode"] == 0

    status = "PASS" if all(checks.values()) else "FAIL"
    result = {
        "verification_status": status,
        "can_mark_goal_complete": status == "PASS",
        "checks": checks,
        "missing_artifacts": missing,
        "parse_errors": parse_errors,
        "py_compile": py_compile,
        "focused_pytest": focused_pytest,
        "upstream_source_packet_checks": upstream_checks,
        "live_surface_diff": live_surface,
        "live_state_closeout": live_state,
    }

    completion_path = OUT_DIR / "G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json"
    completion = load_json("G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json")
    completion["completion_status"] = "PASS_VERIFIED_WITH_G12_ROW_0127_SOURCE_CORRECTION" if status == "PASS" else "FAIL_VERIFIER"
    completion["can_mark_goal_complete"] = status == "PASS"
    completion["verification_results"] = result
    builder.write_json(completion_path, completion)
    builder.write_companion_md("G12_NOFILL_CLOSE_COMPLETION_AUDIT_2026-05-08.json", completion)
    return result


def main() -> None:
    result = verify()
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["verification_status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
