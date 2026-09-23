#!/usr/bin/env python3
"""Verify NOFILL forward addendum/projection-plan artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

REQUIRED_FILES = [
    "NOFILL_FORWARD_ADDENDUM_CONTEXT_ANCHOR_2026-05-09.md",
    "NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.md",
    "NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.json",
    "NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json",
    "NOFILL_FORWARD_PENDING_ORDER_REDACTION_PROOF_2026-05-09.md",
    "NOFILL_FORWARD_LATENCY_CLOCK_SKEW_CAPTURE_SPEC_2026-05-09.json",
    "NOFILL_FORWARD_SPREAD_SLIPPAGE_EXECUTION_QUALITY_STATUS_SPEC_2026-05-09.json",
    "NOFILL_FORWARD_OFFLINE_PROJECTION_BUILDER_PLAN_2026-05-09.md",
    "NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json",
    "NOFILL_FORWARD_BLOCKER_CLOSURE_DECISION_LEDGER_2026-05-09.md",
    "NOFILL_FORWARD_NEXT_PROMPT_PACK_2026-05-09.md",
    "NOFILL_FORWARD_ADDENDUM_COMPLETION_AUDIT_2026-05-09.md",
    "build_nofill_forward_contract_addendum_projection_plan_2026_05_09.py",
    "verify_nofill_forward_contract_addendum_projection_plan_2026_05_09.py",
    "test_nofill_forward_contract_addendum_projection_plan_2026_05_09.py",
]

JSON_FILES = [name for name in REQUIRED_FILES if name.endswith(".json")]
MD_FILES = [name for name in REQUIRED_FILES if name.endswith(".md")]

EXPECTED_BLOCKERS = {
    "G12-FWD-BLOCKER-001",
    "G12-FWD-BLOCKER-002",
    "G12-FWD-BLOCKER-003",
}

EXPECTED_FIELD_NAMES = {
    "capture_observed_at_utc",
    "capture_write_started_at_utc",
    "capture_write_completed_at_utc",
    "capture_latency_ms",
    "capture_clock_source_status",
    "capture_clock_skew_ms",
    "capture_clock_skew_status",
    "capture_timestamp_derivation_rule",
    "pending_order_mode_source_safe",
    "pending_order_mode_status",
    "broker_pending_order_created_status",
    "native_pending_order_type_source_safe",
    "native_pending_order_type_status",
    "raw_ticket_field_present_status",
    "mt5_order_ticket_redaction_status",
    "decision_spread_status",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_status",
    "entry_touch_spread_value_source_safe",
    "spread_source_hash",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
    "cost_testing_gate_status",
}

FORBIDDEN_LIVE_PREFIXES = (
    "src/components/",
    "src/safety/",
    "prompts/",
    "config/",
    "run_agent.py",
    "start_all.bat",
)

ALLOWED_DIR_PREFIX = (
    "research/science_program_2026_05/06_outcome_testing/nofill_forward_contract_addendum_projection_plan/",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)


def load_json(name: str) -> dict[str, Any]:
    return json.loads((OUT_DIR / name).read_text(encoding="utf-8"))


def flatten_json(value: Any) -> list[Any]:
    out: list[Any] = []
    if isinstance(value, dict):
        for nested in value.values():
            out.extend(flatten_json(nested))
    elif isinstance(value, list):
        for nested in value:
            out.extend(flatten_json(nested))
    else:
        out.append(value)
    return out


def git_changed_paths() -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    paths: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip() or line.startswith("warning:"):
            continue
        paths.append(line[3:].replace("\\", "/"))
    return paths


def main() -> int:
    failures: list[dict[str, Any]] = []
    missing = [name for name in REQUIRED_FILES if not (OUT_DIR / name).exists()]
    if missing:
        failures.append({"check": "required_files", "missing": missing})

    parsed: dict[str, dict[str, Any]] = {}
    for name in JSON_FILES:
        if not (OUT_DIR / name).exists():
            continue
        try:
            parsed[name] = load_json(name)
        except json.JSONDecodeError as exc:
            failures.append({"check": "json_parse", "file": name, "error": str(exc)})

    for name, data in parsed.items():
        if data.get("promotion_verdict") != PROMOTION_VERDICT:
            failures.append({"check": "promotion_verdict", "file": name, "value": data.get("promotion_verdict")})
        for flag in ("validation_safe", "outcome_review_opened", "live_effect"):
            if data.get(flag) is not False:
                failures.append({"check": "closed_flag", "file": name, "flag": flag, "value": data.get(flag)})
        for flag in (
            "opens_result_scoring",
            "opens_live_wiring",
            "opens_paid_api_or_databento_route",
            "opens_registry_edit",
            "changes_live_trading_behavior",
        ):
            if flag in data and data.get(flag) is not False:
                failures.append({"check": "closed_route", "file": name, "flag": flag, "value": data.get(flag)})
        if any(value is True for value in flatten_json(data) if isinstance(value, bool)):
            # True can be legitimate in source inventory exists flags. Closed control
            # flags are checked above, so this line is informational only.
            pass

    for name in MD_FILES:
        if not (OUT_DIR / name).exists():
            continue
        text = (OUT_DIR / name).read_text(encoding="utf-8", errors="replace")
        for token in (
            "NO_PROMOTION_VERDICT",
            "validation_safe",
            "outcome_review_opened",
            "live_effect",
        ):
            if token not in text:
                failures.append({"check": "md_control_token", "file": name, "missing": token})

    addendum = parsed.get("NOFILL_FORWARD_CONTRACT_ADDENDUM_2026-05-09.json", {})
    closures = addendum.get("blocker_closure_decisions", [])
    blockers = {item.get("blocker_id") for item in closures if isinstance(item, dict)}
    if blockers != EXPECTED_BLOCKERS:
        failures.append({"check": "blockers", "expected": sorted(EXPECTED_BLOCKERS), "actual": sorted(blockers)})

    schema = parsed.get("NOFILL_FORWARD_PROJECTION_FIELD_SCHEMA_2026-05-09.json", {})
    fields = schema.get("fields", [])
    field_names = {item.get("field_name") for item in fields if isinstance(item, dict)}
    missing_fields = sorted(EXPECTED_FIELD_NAMES - field_names)
    if missing_fields:
        failures.append({"check": "projection_field_names", "missing": missing_fields})
    if schema.get("field_count") != len(EXPECTED_FIELD_NAMES):
        failures.append({"check": "field_count", "expected": len(EXPECTED_FIELD_NAMES), "actual": schema.get("field_count")})

    audit = parsed.get("NOFILL_FORWARD_NO_LEAK_AND_FORBIDDEN_FIELD_AUDIT_2026-05-09.json", {})
    if audit.get("status") != "PASS":
        failures.append({"check": "no_leak_audit_status", "value": audit.get("status")})
    dry_run = audit.get("dry_run_projection_fixture", {})
    if dry_run.get("leak_issues"):
        failures.append({"check": "dry_run_redaction", "issues": dry_run.get("leak_issues")})
    projected = dry_run.get("projected_output", {})
    for key in ("slippage_label_status", "execution_quality_label_status"):
        if projected.get(key) != "NOT_OPENED_FOR_SOURCE_CONTROL":
            failures.append({"check": "closed_cost_status", "key": key, "value": projected.get(key)})

    changed_paths = git_changed_paths()
    forbidden_dirty = [
        path
        for path in changed_paths
        if path.startswith(FORBIDDEN_LIVE_PREFIXES)
    ]
    outside_scope = [
        path
        for path in changed_paths
        if not path.startswith(ALLOWED_DIR_PREFIX)
    ]
    if forbidden_dirty:
        failures.append({"check": "forbidden_live_surface_dirty", "paths": forbidden_dirty})
    if outside_scope:
        failures.append({"check": "outside_scope_dirty", "paths": outside_scope})

    result = {
        "ok": not failures,
        "can_mark_goal_complete": not failures,
        "route_id": "NOFILL_FORWARD_CONTRACT_ADDENDUM_PROJECTION_PLAN",
        "required_file_count": len(REQUIRED_FILES),
        "json_file_count": len(JSON_FILES),
        "projection_field_count": schema.get("field_count"),
        "blockers": sorted(blockers),
        "changed_paths_checked": changed_paths,
        "failures": failures,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
