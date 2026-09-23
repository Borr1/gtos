#!/usr/bin/env python3
"""Verify Wave3 LiveDecisionPacketV4 route artifacts and code hooks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.live_decision_packet_v4 import (
    FORBIDDEN_SURFACE_BOUNDARY,
    REQUIRED_FIELD_GROUPS,
    SEMANTIC_OWNERSHIP_REQUIREMENTS,
)

ROUTE_DIR = Path(
    "research/operations/"
    "wave3_data_capture_source_repair_final_and_livedecisionpacket_v4_2026_06_04"
)

REQUIRED_ARTIFACTS = (
    "WAVE3_DATA_CAPTURE_SOURCE_REPAIR_CONTEXT_ANCHOR.json",
    "WAVE3_LIVE_DECISION_PACKET_V4_SCHEMA_CONTRACT.json",
    "WAVE3_SOURCE_GAP_AND_CAPTURE_REQUIREMENT_LEDGER.jsonl",
    "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl",
    "WAVE3_SEMANTIC_OWNERSHIP_COVERAGE_LEDGER.jsonl",
    "WAVE3_SEARCHED_ROOT_LEDGER.jsonl",
    "WAVE3_SATURATION_SELF_RED_TEAM.md",
    "WAVE3_OUTPUT_MANIFEST.json",
    "WAVE3_COMPLETION_AUDIT.md",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{idx}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{idx}: JSONL row is not an object")
        rows.append(row)
    return rows


def _record(issue_list: list[dict[str, Any]], code: str, **details: Any) -> None:
    issue_list.append({"code": code, **details})


def verify(route_dir: Path = ROUTE_DIR) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    parsed_json: dict[str, Any] = {}
    parsed_jsonl_counts: dict[str, int] = {}

    if not route_dir.exists():
        _record(issues, "route_dir_missing", route_dir=str(route_dir))
        return {"status": "fail", "issues": issues}

    for name in REQUIRED_ARTIFACTS:
        if not (route_dir / name).exists():
            _record(issues, "required_artifact_missing", artifact=name)

    for path in sorted(route_dir.glob("*.json")):
        if path.name == "WAVE3_VERIFICATION_RESULT.json":
            continue
        try:
            parsed_json[path.name] = _load_json(path)
        except Exception as exc:  # noqa: BLE001 - verifier reports path-specific issue.
            _record(issues, "json_parse_failed", path=str(path), error=str(exc))

    for path in sorted(route_dir.glob("*.jsonl")):
        try:
            rows = _load_jsonl(path)
            parsed_jsonl_counts[path.name] = len(rows)
        except Exception as exc:  # noqa: BLE001
            _record(issues, "jsonl_parse_failed", path=str(path), error=str(exc))

    manifest = parsed_json.get("WAVE3_OUTPUT_MANIFEST.json") or {}
    if manifest.get("validation_result_status") is not False:
        _record(issues, "validation_result_status_not_false")
    if manifest.get("outcome_result_rows_status") is not False:
        _record(issues, "outcome_result_rows_status_not_false")
    if manifest.get("broker_runtime_change_status") is not False:
        _record(issues, "broker_runtime_change_status_not_false")
    forbidden = manifest.get("forbidden_surface_boundary")
    if forbidden != FORBIDDEN_SURFACE_BOUNDARY:
        _record(issues, "forbidden_surface_boundary_mismatch", value=forbidden)

    schema = parsed_json.get("WAVE3_LIVE_DECISION_PACKET_V4_SCHEMA_CONTRACT.json") or {}
    if schema.get("schema_name") != "LiveDecisionPacketV4":
        _record(issues, "schema_name_missing")
    if tuple(schema.get("required_field_groups") or ()) != REQUIRED_FIELD_GROUPS:
        _record(issues, "required_field_groups_mismatch")
    if schema.get("no_leak_status") != "PASS_PRE_DECISION_SOURCE_HASH_EXCLUDES_POST_DECISION_FIELDS":
        _record(issues, "no_leak_status_invalid", value=schema.get("no_leak_status"))
    if schema.get("forbidden_surface_boundary") != FORBIDDEN_SURFACE_BOUNDARY:
        _record(issues, "schema_forbidden_surface_boundary_mismatch")
    runtime_contract = schema.get("runtime_evidence_contract")
    required_runtime_contract_keys = {
        "source_completeness_policy",
        "no_leak_asof_policy",
        "duplicate_policy",
        "partition_holdout_requirements",
        "cost_slippage_stress_requirements",
        "rollback_path",
        "semantic_ownership_handoff",
    }
    if not isinstance(runtime_contract, dict):
        _record(issues, "runtime_evidence_contract_missing")
    else:
        missing = sorted(required_runtime_contract_keys - set(runtime_contract))
        if missing:
            _record(
                issues,
                "runtime_evidence_contract_keys_missing",
                missing=missing,
            )

    semantic_rows = _load_jsonl(route_dir / "WAVE3_SEMANTIC_OWNERSHIP_COVERAGE_LEDGER.jsonl")
    covered = {row.get("semantic_key") for row in semantic_rows}
    for key in SEMANTIC_OWNERSHIP_REQUIREMENTS:
        if key not in covered:
            _record(issues, "semantic_ownership_key_missing", key=key)
    for row in semantic_rows:
        if row.get("status") not in {
            "implemented_capture_or_explicit_source_gap",
            "handoff_contract_explicit",
        }:
            _record(issues, "semantic_row_status_invalid", row=row)

    gap_rows = _load_jsonl(route_dir / "WAVE3_SOURCE_GAP_AND_CAPTURE_REQUIREMENT_LEDGER.jsonl")
    for row in gap_rows:
        if not row.get("owner_lane"):
            _record(issues, "source_gap_owner_missing", row=row)
        if not row.get("exact_capture_requirement"):
            _record(issues, "source_gap_exact_requirement_missing", row=row)
        if row.get("status") not in {
            "implemented_capture",
            "prospective_capture_required",
            "source_gap_exactly_bounded",
        }:
            _record(issues, "source_gap_status_invalid", row=row)

    disposition_rows = _load_jsonl(route_dir / "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl")
    dispositions = {row.get("component"): row.get("production_code_disposition") for row in disposition_rows}
    if dispositions.get("src/components/live_decision_packet_v4.py") != "active_capture_only":
        _record(issues, "live_decision_packet_component_not_active_capture_only")
    if dispositions.get("src/components/orchestrator.py") != "active_capture_only_hook":
        _record(issues, "orchestrator_hook_disposition_missing")

    code_checks = {
        "src/components/orchestrator.py": "attach_live_decision_packet_v4",
        "config/agent_config.yaml": "live_decision_packet_v4_log_path",
        "tests/test_vnext_broader_origin_orchestrator.py": (
            "test_broader_origin_record_attaches_live_decision_packet_v4_and_jsonl"
        ),
    }
    for path_text, needle in code_checks.items():
        text = Path(path_text).read_text(encoding="utf-8-sig")
        if needle not in text:
            _record(issues, "code_hook_missing", path=path_text, needle=needle)

    prompt = Path(
        "research/science_program_2026_05/04_goal_prompts/"
        "wave3_final_moonshot_after_hard_halt_2026_06_04/"
        "WAVE3_02_DATA_CAPTURE_SOURCE_REPAIR_FINAL_AND_LIVEDECISIONPACKET_V4_GOAL_PROMPT_2026-06-04.md"
    ).read_text(encoding="utf-8-sig")
    for required in (
        "LiveDecisionPacketV4 schema and logger code",
        "source-hash and no-leak field contract",
        "semantic field capture tests",
        "route verifier proving packet completeness gates",
    ):
        if required not in prompt:
            _record(issues, "prompt_required_output_missing", required=required)

    status = "pass" if not issues else "fail"
    return {
        "status": status,
        "route_dir": str(route_dir),
        "json_artifact_count": len(parsed_json),
        "jsonl_artifact_counts": parsed_jsonl_counts,
        "required_field_group_count": len(REQUIRED_FIELD_GROUPS),
        "semantic_ownership_key_count": len(SEMANTIC_OWNERSHIP_REQUIREMENTS),
        "source_gap_row_count": len(gap_rows) if "gap_rows" in locals() else 0,
        "forbidden_surface_boundary": FORBIDDEN_SURFACE_BOUNDARY,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("route_dir", nargs="?", default=str(ROUTE_DIR))
    parser.add_argument("--write-result", action="store_true")
    args = parser.parse_args()

    route_dir = Path(args.route_dir)
    result = verify(route_dir)
    payload = json.dumps(result, indent=2, sort_keys=True)
    print(payload)
    if args.write_result:
        (route_dir / "WAVE3_VERIFICATION_RESULT.json").write_text(
            payload + "\n",
            encoding="utf-8",
        )
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
