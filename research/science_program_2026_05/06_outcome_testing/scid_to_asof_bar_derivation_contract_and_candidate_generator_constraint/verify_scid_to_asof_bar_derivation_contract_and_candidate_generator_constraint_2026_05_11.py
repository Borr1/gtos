#!/usr/bin/env python3
"""Verify the SCID as-of contract route artifacts.

The verifier checks contract completeness and source-control boundaries only.
It does not derive real bars, generate candidates, inspect outcomes, or score
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
RESULT_PATH = ROUTE_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json"
NEXT_G12_PROMPT = (
    ROOT
    / "research"
    / "science_program_2026_05"
    / "04_goal_prompts"
    / "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT_GOAL_PROMPT_2026-05-11.md"
)
ROUTE_ID = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
EVIDENCE_CLASS = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY"
EXPECTED_BASELINES = [
    "baseline_random_session_control",
    "baseline_shifted_entry_control",
    "baseline_momentum_continuation",
    "baseline_mean_reversion",
]
FORBIDDEN_EXTENSIONS = {".scid", ".parquet", ".csv", ".dly", ".bin"}
FORBIDDEN_LIVE_SURFACE_PREFIXES = (
    "src/",
    "config/",
    "prompts/",
    "scripts/canary",
    "scripts/canary_",
)

REQUIRED_FILES = [
    f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}.json",
    f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}.md",
    f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}.json",
    f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}.md",
    f"SCID_ASOF_FIELD_SCHEMA_{DATE_TAG}.json",
    f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}.json",
    f"SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_{DATE_TAG}.json",
    f"SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_{DATE_TAG}.json",
    f"SCID_ASOF_DISCOVERY_EXCLUSION_AND_BASELINE_PRESERVATION_AUDIT_{DATE_TAG}.json",
    f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json",
    f"SCID_ASOF_FIXTURE_LEDGER_{DATE_TAG}.json",
    f"SCID_ASOF_SOURCE_CONTROL_GATE_LEDGER_{DATE_TAG}.json",
    f"SCID_ASOF_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
    f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}.json",
    f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.json",
    f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.md",
]


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(name: str) -> dict[str, Any]:
    return json.loads((ROUTE_DIR / name).read_text(encoding="utf-8"))


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def safe_flags_closed(payload: dict[str, Any]) -> bool:
    expected_false = [
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
        and all(payload.get(key) is False for key in expected_false)
    )


def main() -> None:
    issues: list[str] = []
    checks: dict[str, bool] = {}

    required_paths = [ROUTE_DIR / name for name in REQUIRED_FILES]
    checks["required_files_exist"] = all(path.exists() for path in required_paths) and NEXT_G12_PROMPT.exists()
    if not checks["required_files_exist"]:
        missing = [rel(path) for path in required_paths if not path.exists()]
        if not NEXT_G12_PROMPT.exists():
            missing.append(rel(NEXT_G12_PROMPT))
        issues.append(f"missing required files: {missing}")

    parsed: dict[str, dict[str, Any]] = {}
    for path in required_paths:
        if path.suffix == ".json" and path.exists():
            try:
                parsed[path.name] = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                issues.append(f"json parse failed for {rel(path)}: {exc}")
    checks["json_parse_ok"] = not any("json parse failed" in issue for issue in issues)

    bar = parsed.get(f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}.json", {})
    candidate = parsed.get(f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}.json", {})
    schema = parsed.get(f"SCID_ASOF_FIELD_SCHEMA_{DATE_TAG}.json", {})
    forbidden = parsed.get(f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}.json", {})
    timestamp = parsed.get(f"SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_{DATE_TAG}.json", {})
    duplicate = parsed.get(f"SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_{DATE_TAG}.json", {})
    discovery = parsed.get(f"SCID_ASOF_DISCOVERY_EXCLUSION_AND_BASELINE_PRESERVATION_AUDIT_{DATE_TAG}.json", {})
    noleak = parsed.get(f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json", {})
    fixtures = parsed.get(f"SCID_ASOF_FIXTURE_LEDGER_{DATE_TAG}.json", {})
    gates = parsed.get(f"SCID_ASOF_SOURCE_CONTROL_GATE_LEDGER_{DATE_TAG}.json", {})
    redteam = parsed.get(f"SCID_ASOF_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json", {})
    manifest = parsed.get(f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}.json", {})
    completion = parsed.get(f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.json", {})

    payloads_to_check = [
        bar,
        candidate,
        schema,
        forbidden,
        timestamp,
        duplicate,
        discovery,
        noleak,
        fixtures,
        gates,
        redteam,
        manifest,
        completion,
    ]
    checks["safe_flags_closed"] = all(safe_flags_closed(payload) for payload in payloads_to_check)

    parser = bar.get("parser_contract", {})
    checks["parser_contract_exact"] = (
        parser.get("binary_header", {}).get("struct") == "<4sIIHHI36s"
        and parser.get("binary_header", {}).get("expected_header_size_bytes") == 56
        and parser.get("binary_record", {}).get("struct") == "<QffffIIII"
        and parser.get("binary_record", {}).get("record_size_bytes") == 40
    )

    source_inputs = bar.get("source_inputs", [])
    checks["nine_segments_referenced"] = (
        len(source_inputs) == 9
        and all(row.get("source_manifest_ref") for row in source_inputs)
        and all(row.get("segment_records_sha256") for row in source_inputs)
        and all(row.get("raw_blob_committed") is False for row in source_inputs)
    )
    checks["all_rehashes_match"] = all(row.get("rehash_matches") is True for row in source_inputs)

    checks["timestamp_policy_no_lookahead"] = (
        timestamp.get("interval_policy", {}).get("bar_membership") == "left_closed_right_open"
        and "bar_end_exclusive_utc <= decision_asof_utc"
        in timestamp.get("interval_policy", {}).get("decision_asof_rule", "")
        and timestamp.get("interval_policy", {}).get("record_at_decision_asof", "").startswith("excluded")
    )

    checks["candidate_generator_cannot_validate"] = (
        candidate.get("silent_validation_guard", {}).get("result_columns_allowed") is False
        and candidate.get("silent_validation_guard", {}).get("path_label_columns_allowed") is False
        and candidate.get("silent_validation_guard", {}).get("candidate_acceptance_claim_allowed") is False
        and candidate.get("summary", {}).get("validation_execution_allowed") is False
    )

    checks["forbidden_fields_cover_required_families"] = all(
        any(required in entry.get("pattern", "") for entry in forbidden.get("entries", []))
        for required in ["broker", "order", "path_label", "outcome", "slippage", "ai_response", "future_"]
    )

    checks["field_schema_has_scid_and_bar_fields"] = (
        len(schema.get("allowed_scid_record_fields", [])) == 9
        and any(field.get("name") == "bar_end_exclusive_utc" for field in schema.get("allowed_derived_bar_fields", []))
        and "forbidden_field_ledger_ref" in schema
    )

    checks["discovery_and_baselines_preserved"] = (
        discovery.get("selected_discovery_source_count") == 365
        and discovery.get("selected_discovery_source_hash_count") == 365
        and discovery.get("baseline_ids") == EXPECTED_BASELINES
        and discovery.get("summary", {}).get("checks_pass") is True
    )

    checks["noleak_partition_closed"] = noleak.get("summary", {}).get("checks_pass") is True
    checks["fixtures_cover_edge_cases"] = (
        fixtures.get("summary", {}).get("fixture_case_count", 0) >= 6
        and fixtures.get("expected_fixture_result_summary", {}).get("empty_bar_count", 0) >= 1
        and fixtures.get("expected_fixture_result_summary", {}).get("same_timestamp_group_count", 0) >= 1
    )
    checks["duplicate_proxy_policy_frozen"] = (
        len(duplicate.get("proxy_groups", [])) >= 7
        and "canonical_economic_group" in duplicate.get("candidate_duplicate_key", [])
        and duplicate.get("summary", {}).get("double_counting_prevented") is True
    )
    checks["future_gates_closed"] = (
        gates.get("validation_execution_allowed_now") is False
        and gates.get("candidate_generation_allowed_now") is False
        and gates.get("result_scoring_allowed_now") is False
        and gates.get("summary", {}).get("all_future_result_gates_closed") is True
    )
    checks["saturation_closed"] = (
        redteam.get("summary", {}).get("redteam_question_count", 0) >= 10
        and redteam.get("summary", {}).get("all_closed_or_gated") is True
        and redteam.get("remaining_same_evidence_class_gaps") == []
    )

    route_files = [path for path in ROUTE_DIR.rglob("*") if path.is_file()]
    checks["no_raw_market_blobs_in_route"] = not any(path.suffix.lower() in FORBIDDEN_EXTENSIONS for path in route_files)

    artifact_paths = []
    for artifact in manifest.get("artifacts", {}).values():
        if isinstance(artifact, dict):
            artifact_paths.extend(str(value) for value in artifact.values() if isinstance(value, str))
    artifact_paths.extend([manifest.get("builder", ""), manifest.get("verifier", ""), manifest.get("focused_tests", "")])
    checks["scoped_artifacts_avoid_live_surface"] = not any(
        path.startswith(FORBIDDEN_LIVE_SURFACE_PREFIXES) for path in artifact_paths
    )

    prompt_text = NEXT_G12_PROMPT.read_text(encoding="utf-8") if NEXT_G12_PROMPT.exists() else ""
    checks["next_g12_prompt_contract_only"] = (
        "validation execution" in prompt_text
        and "NO_PROMOTION_VERDICT" in prompt_text
        and "ACCEPT_AS_SOURCE_CONTROL_SCID_ASOF_CONTRACT_ONLY" in prompt_text
        and "Acceptance may only unlock a future source-control bar-builder/input-packet lane" in prompt_text
        and "must not unlock validation execution" in prompt_text
    )

    checks["completion_audit_maps_requirements"] = (
        len(completion.get("prompt_to_artifact_checklist", [])) >= 15
        and completion.get("summary", {}).get("remaining_blocker_count") == 0
    )

    for key, value in checks.items():
        if not value:
            issues.append(f"check failed: {key}")

    status_lines = git_status_short()
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
        "git_status_short_informational": status_lines,
        "can_mark_goal_complete_after_commit_and_context_refresh": not issues,
    }
    RESULT_PATH.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": output["ok"], "issues": issues}, indent=2, sort_keys=True))
    if issues:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
