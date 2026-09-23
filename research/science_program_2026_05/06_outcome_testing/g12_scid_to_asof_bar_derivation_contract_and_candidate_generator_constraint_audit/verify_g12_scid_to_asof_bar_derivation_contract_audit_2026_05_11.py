#!/usr/bin/env python3
"""Verify the independent G12 SCID-to-asof contract audit route.

This verifier checks the audit artifacts and source-control boundaries only.
It does not derive bars, generate candidates, inspect outcomes, or score
anything.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
ROUTE_ID = "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT"
EVIDENCE_CLASS = "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AUDIT_ONLY"
RESULT_PATH = ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_VERIFICATION_RESULT_{DATE_TAG}.json"
NEXT_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md"
)
FORBIDDEN_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "config/",
    "prompts/",
    "scripts/canary",
    "scripts/canary_",
)

REQUIRED_FILES = [
    f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{DATE_TAG}.md",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_PARSER_TIMESTAMP_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_ASOF_NOLEAK_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_DUPLICATE_PROXY_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_FIXTURE_COVERAGE_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_FORBIDDEN_FIELD_REVIEW_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_BLOCKER_LEDGER_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.md",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.json",
    f"G12_SCID_ASOF_CONTRACT_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.md",
    "build_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py",
    "verify_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py",
    "test_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py",
]


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    false_keys = [
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
    return (
        payload.get("route_id") == ROUTE_ID
        and payload.get("evidence_class") == EVIDENCE_CLASS
        and payload.get("promotion_verdict") == "NO_PROMOTION_VERDICT"
        and all(payload.get(key) is False for key in false_keys)
    )


def main() -> None:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    paths = [ROUTE_DIR / name for name in REQUIRED_FILES]
    checks["required_files_exist"] = all(path.exists() for path in paths) and NEXT_PROMPT.exists()
    if not checks["required_files_exist"]:
        missing = [rel(path) for path in paths if not path.exists()]
        if not NEXT_PROMPT.exists():
            missing.append(rel(NEXT_PROMPT))
        issues.append(f"missing required files: {missing}")

    parsed: dict[str, dict[str, Any]] = {}
    for path in paths:
        if path.suffix == ".json" and path.exists():
            try:
                parsed[path.name] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(f"json parse failed for {rel(path)}: {exc}")
    checks["json_parse_ok"] = not any("json parse failed" in issue for issue in issues)

    decision = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{DATE_TAG}.json", {})
    parser = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_PARSER_TIMESTAMP_REVIEW_{DATE_TAG}.json", {})
    asof = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_ASOF_NOLEAK_REVIEW_{DATE_TAG}.json", {})
    duplicate = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_DUPLICATE_PROXY_REVIEW_{DATE_TAG}.json", {})
    fixture = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_FIXTURE_COVERAGE_REVIEW_{DATE_TAG}.json", {})
    forbidden = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_FORBIDDEN_FIELD_REVIEW_{DATE_TAG}.json", {})
    blockers = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_BLOCKER_LEDGER_{DATE_TAG}.json", {})
    completion = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_COMPLETION_AUDIT_{DATE_TAG}.json", {})
    manifest = parsed.get(f"G12_SCID_ASOF_CONTRACT_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.json", {})

    payloads = [decision, parser, asof, duplicate, fixture, forbidden, blockers, completion, manifest]
    checks["safe_flags_closed"] = all(safe_flags_closed(payload) for payload in payloads)
    checks["terminal_decision_allowed"] = decision.get("terminal_decision") in {
        "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CONTRACT_ONLY",
        "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS",
        "REJECT_CONTRACT_LEAK_OR_AMBIGUITY",
        "BLOCKED_EXACT_SOURCE_OR_ENVIRONMENT_REASON",
    }
    checks["accepted_source_control_only"] = (
        decision.get("terminal_decision") == "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS"
        and decision.get("accepted_source_control_scid_asof_contract_only") is True
        and decision.get("accepted_validation_execution") is False
        and decision.get("accepted_result_scoring") is False
    )
    checks["parser_timestamp_passed"] = parser.get("summary", {}).get("checks_pass") is True
    checks["nine_segments_reconciled"] = parser.get("summary", {}).get("segment_count") == 9
    checks["asof_noleak_passed"] = asof.get("summary", {}).get("checks_pass") is True
    checks["duplicate_proxy_passed"] = duplicate.get("summary", {}).get("checks_pass") is True
    checks["forbidden_warning_not_blocker"] = (
        forbidden.get("summary", {}).get("fail_open_leak_blocker_count") == 0
        and forbidden.get("summary", {}).get("warning_count") == 1
        and forbidden.get("checks", {}).get("fail_closed_overmatch_warning_detected") is True
    )
    checks["fixture_warning_not_blocker"] = (
        fixture.get("summary", {}).get("warning_count") == 1
        and fixture.get("checks", {}).get("hard_floor_upstream_source_control_closed") is True
        and fixture.get("checks", {}).get("hard_floor_executable_gap_recorded_as_warning") is True
    )
    checks["blockers_zero_warnings_exact"] = (
        blockers.get("summary", {}).get("terminal_blocker_count") == 0
        and blockers.get("summary", {}).get("exact_warning_count") == 2
    )
    checks["completion_maps_prompt"] = (
        len(completion.get("prompt_to_artifact_checklist", [])) >= 20
        and len(completion.get("saturation_self_redteam", [])) >= 10
        and completion.get("summary", {}).get("terminal_blocker_count") == 0
    )
    prompt_text = NEXT_PROMPT.read_text(encoding="utf-8") if NEXT_PROMPT.exists() else ""
    checks["next_prompt_source_control_only"] = (
        "source-control bar-builder and candidate input-packet materialization only" in prompt_text
        and "must not execute sealed validation" in prompt_text
        and "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW" in prompt_text
        and "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE" in prompt_text
        and "NO_PROMOTION_VERDICT" in prompt_text
    )

    route_files = [path for path in ROUTE_DIR.rglob("*") if path.is_file()]
    checks["no_raw_market_data_blobs"] = not any(path.suffix.lower() in FORBIDDEN_EXTENSIONS for path in route_files)
    artifact_paths = []
    for artifact in manifest.get("artifacts", {}).values():
        if isinstance(artifact, dict):
            artifact_paths.extend(str(value) for value in artifact.values() if isinstance(value, str))
        elif isinstance(artifact, str):
            artifact_paths.append(artifact)
    artifact_paths.extend([manifest.get("builder", ""), manifest.get("verifier", ""), manifest.get("focused_tests", "")])
    checks["scoped_artifacts_avoid_live_surface"] = not any(
        path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES) for path in artifact_paths
    )

    for key, value in checks.items():
        if not value:
            issues.append(f"check failed: {key}")

    output = {
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "ok": not issues,
        "checks": checks,
        "issues": issues,
        "git_status_short_informational": git_status_short(),
        "can_mark_goal_complete_after_commit_and_context_refresh": not issues,
    }
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": output["ok"], "issues": issues}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
