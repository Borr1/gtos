"""Verify the Blocked17 orderflow/proxy G12 audit artifacts."""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
BUILD_PATH = ROUTE_DIR / "build_g12_scid_blocked17_orderflow_proxy_contract_audit_2026_05_13.py"
spec = importlib.util.spec_from_file_location("g12_proxy_build", BUILD_PATH)
build = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(build)


PREFIX = build.PREFIX
DATE = build.DATE


def artifact_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE}{suffix}"


def read_json(stem: str) -> Any:
    return json.loads(artifact_path(stem).read_text(encoding="utf-8"))


def git_status_short() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=build.REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        return [line for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def verify(write_result: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    required = [
        "CONTEXT_ANCHOR",
        "DENOMINATOR_AUDIT",
        "ARTIFACT_HASH_AUDIT",
        "SOURCE_FAMILY_CONTRACT_AUDIT",
        "EQUIVALENCE_NON_EQUIVALENCE_AUDIT",
        "BLOCKER_EXACTNESS_AUDIT",
        "NOLEAK_SAFE_FLAG_AUDIT",
        "DECISION_LEDGER",
        "COMPLETION_AUDIT",
    ]
    payloads: dict[str, Any] = {}
    for stem in required:
        path = artifact_path(stem)
        if not path.exists():
            failures.append(f"missing artifact {path.name}")
            continue
        payloads[stem] = read_json(stem)

    for stem, payload in payloads.items():
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            failures.append(f"{stem} promotion verdict changed")
        for key in build.SAFE_FALSE_KEYS:
            if payload.get(key) is not False:
                failures.append(f"{stem} {key} not false")

    for stem in [
        "DENOMINATOR_AUDIT",
        "ARTIFACT_HASH_AUDIT",
        "SOURCE_FAMILY_CONTRACT_AUDIT",
        "EQUIVALENCE_NON_EQUIVALENCE_AUDIT",
        "BLOCKER_EXACTNESS_AUDIT",
        "NOLEAK_SAFE_FLAG_AUDIT",
    ]:
        if payloads.get(stem, {}).get("ok") is not True:
            failures.append(f"{stem} ok is not true")

    artifact_hash = payloads.get("ARTIFACT_HASH_AUDIT", {})
    if artifact_hash.get("strict_failure_count") != 0:
        failures.append("artifact hash audit has strict failures")
    if len(artifact_hash.get("same_g12_repairs_closed", [])) != 1:
        failures.append("prompt manifest repair was not closed exactly once")
    if artifact_hash.get("text_eol_equivalent_row_count") != 5:
        failures.append("expected five text EOL-equivalent rows")

    decision = payloads.get("DECISION_LEDGER", {})
    if not str(decision.get("terminal_decision", "")).startswith("ACCEPT_AS_G12"):
        failures.append("terminal decision is not ACCEPT")
    if decision.get("broker_native_cfd_truth_claims") != 0:
        failures.append("broker native CFD truth claims not zero")

    completion = payloads.get("COMPLETION_AUDIT", {})
    if completion.get("completion_standard_satisfied") is not True:
        failures.append("completion standard not satisfied")
    if completion.get("missing_incomplete_or_weak_requirements"):
        failures.append("completion audit has missing requirements")

    next_prompt = ROUTE_DIR / f"{PREFIX}_NEXT_G0_PROMPT_{DATE}.md"
    next_starter = ROUTE_DIR / f"{PREFIX}_NEXT_G0_STARTER_{DATE}.txt"
    if not next_prompt.exists() or not next_starter.exists():
        failures.append("next G0 prompt/starter missing")

    focused = artifact_path("FOCUSED_TEST_RESULT")
    focused_ok = None
    if focused.exists():
        focused_payload = read_json("FOCUSED_TEST_RESULT")
        focused_ok = focused_payload.get("ok")
        if focused_ok is not True:
            failures.append("focused test result not ok")

    status_lines = git_status_short()
    forbidden_changed = [
        line
        for line in status_lines
        if any(token in line for token in ["src/", "src\\", "prompts/", "config/agent_config.yaml"])
    ]
    if forbidden_changed:
        failures.append(f"forbidden live-surface/status paths changed: {forbidden_changed}")

    result = {
        **build.base_payload("VERIFICATION_RESULT"),
        "ok": not failures,
        "failure_count": len(failures),
        "failures": failures,
        "terminal_decision": decision.get("terminal_decision"),
        "completion_standard_satisfied": completion.get("completion_standard_satisfied"),
        "focused_test_result_ok": focused_ok,
        "changed_or_untracked_paths": status_lines,
        "forbidden_live_surface_changed_paths": forbidden_changed,
    }
    if write_result:
        build.write_artifact("VERIFICATION_RESULT", "Verification Result", result)
        build.write_output_manifest()
    return result


def main() -> None:
    result = verify(write_result=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
