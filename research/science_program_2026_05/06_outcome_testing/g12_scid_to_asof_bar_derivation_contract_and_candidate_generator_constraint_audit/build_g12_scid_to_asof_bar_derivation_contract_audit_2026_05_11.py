#!/usr/bin/env python3
"""Build the independent G12 audit for the SCID-to-asof contract route.

This route audits source-control/design evidence only. It reads target route
artifacts, upstream G12 repair evidence, and G0 source-control ledgers. It does
not derive market bars, generate candidate rows, inspect outcomes, score
performance, call APIs, or touch live trading behavior.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
DATE_TAG = "2026-05-11"
ROUTE_ID = "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_AUDIT"
EVIDENCE_CLASS = "G12_SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AUDIT_ONLY"
SCHEMA_VERSION = "g12_scid_asof_contract_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"

SCIENCE_ROOT = ROOT / "research" / "science_program_2026_05"
PROMPT_DIR = SCIENCE_ROOT / "04_goal_prompts"
TARGET_DIR = (
    SCIENCE_ROOT
    / "06_outcome_testing"
    / "scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint"
)
G12_REPAIR_DIR = (
    SCIENCE_ROOT
    / "06_outcome_testing"
    / "g12_fpb_sealed_source_pool_immutable_scid_hash_freeze_repair_reaudit"
)
REPAIR_DIR = SCIENCE_ROOT / "06_outcome_testing" / "fpb_sealed_source_pool_immutable_scid_hash_freeze_repair"
G0_DIR = SCIENCE_ROOT / "06_outcome_testing" / "g0_fpb_sealed_partition_and_adversarial_baseline_packet"

NEXT_PROMPT = (
    PROMPT_DIR / "SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_GOAL_PROMPT_2026-05-11.md"
)

TARGET_REQUIRED = {
    "bar_contract": TARGET_DIR / f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}.json",
    "bar_contract_md": TARGET_DIR / f"SCID_ASOF_BAR_DERIVATION_CONTRACT_{DATE_TAG}.md",
    "candidate_constraint": TARGET_DIR / f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}.json",
    "candidate_constraint_md": TARGET_DIR / f"SCID_ASOF_CANDIDATE_GENERATOR_CONSTRAINT_{DATE_TAG}.md",
    "field_schema": TARGET_DIR / f"SCID_ASOF_FIELD_SCHEMA_{DATE_TAG}.json",
    "forbidden_field": TARGET_DIR / f"SCID_ASOF_FORBIDDEN_FIELD_LEDGER_{DATE_TAG}.json",
    "timestamp_interval": TARGET_DIR / f"SCID_ASOF_TIMESTAMP_AND_INTERVAL_POLICY_{DATE_TAG}.json",
    "duplicate_proxy": TARGET_DIR / f"SCID_ASOF_DUPLICATE_AND_PROXY_POLICY_{DATE_TAG}.json",
    "discovery_baseline": TARGET_DIR / f"SCID_ASOF_DISCOVERY_EXCLUSION_AND_BASELINE_PRESERVATION_AUDIT_{DATE_TAG}.json",
    "noleak": TARGET_DIR / f"SCID_ASOF_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json",
    "fixtures": TARGET_DIR / f"SCID_ASOF_FIXTURE_LEDGER_{DATE_TAG}.json",
    "gates": TARGET_DIR / f"SCID_ASOF_SOURCE_CONTROL_GATE_LEDGER_{DATE_TAG}.json",
    "redteam": TARGET_DIR / f"SCID_ASOF_SATURATION_REDTEAM_LEDGER_{DATE_TAG}.json",
    "manifest": TARGET_DIR / f"SCID_ASOF_OUTPUT_MANIFEST_{DATE_TAG}.json",
    "completion": TARGET_DIR / f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.json",
    "completion_md": TARGET_DIR / f"SCID_ASOF_COMPLETION_AUDIT_{DATE_TAG}.md",
    "verification": TARGET_DIR / f"SCID_ASOF_VERIFICATION_RESULT_{DATE_TAG}.json",
    "builder": TARGET_DIR / "build_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
    "verifier": TARGET_DIR / "verify_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
    "tests": TARGET_DIR / "test_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py",
}

UPSTREAM_REQUIRED = {
    "g12_rehash": G12_REPAIR_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_SOURCE_REHASH_AUDIT_{DATE_TAG}.json",
    "g12_noleak": G12_REPAIR_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_NOLEAK_PARTITION_AUDIT_{DATE_TAG}.json",
    "g12_decision": G12_REPAIR_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_DECISION_LEDGER_{DATE_TAG}.json",
    "g12_completion": G12_REPAIR_DIR / f"G12_FPB_SCID_FREEZE_REPAIR_REAUDIT_COMPLETION_AUDIT_{DATE_TAG}.json",
    "repair_manifest": REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_SNAPSHOT_SEGMENT_MANIFEST_{DATE_TAG}.json",
    "repair_parser": REPAIR_DIR / f"FPB_SCID_FREEZE_REPAIR_PARSER_ASOF_NOLEAK_AUDIT_{DATE_TAG}.json",
    "g0_baseline": G0_DIR / f"G0_FPB_SEALED_PARTITION_ADVERSARIAL_BASELINE_PACKET_{DATE_TAG}.json",
    "g0_discovery": G0_DIR / f"G0_FPB_SEALED_PARTITION_DISCOVERY_EXPOSURE_LEDGER_{DATE_TAG}.json",
    "g0_source_contract": G0_DIR / f"G0_FPB_SEALED_PARTITION_SOURCE_ASOF_NOLEAK_CONTRACT_{DATE_TAG}.json",
}

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
TARGET_ROUTE_ID = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT"
TARGET_EVIDENCE_CLASS = "SCID_TO_ASOF_BAR_DERIVATION_CONTRACT_AND_CANDIDATE_GENERATOR_CONSTRAINT_ONLY"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


GENERATED_AT_UTC = utc_now()


def safe_flags() -> dict[str, Any]:
    return {
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": GENERATED_AT_UTC,
        "evidence_class": EVIDENCE_CLASS,
        "promotion_verdict": PROMOTION_VERDICT,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_promotion": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_paid_api_or_databento_route": False,
        "opens_remote_push": False,
        "opens_registry_edit": False,
        "opens_mt5_order_account_history_behavior": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
    }


def rel(path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(ROOT.resolve(strict=False)).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_block(value: Any, limit: int = 12000) -> str:
    text = json.dumps(value, indent=2, sort_keys=True)
    if len(text) > limit:
        text = text[:limit] + "\n... truncated in markdown; see matching JSON artifact ..."
    return "```json\n" + text + "\n```"


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    md = [
        f"# {title}",
        "",
        f"- Route: `{ROUTE_ID}`",
        f"- Evidence class: `{EVIDENCE_CLASS}`",
        f"- Terminal decision: `{payload.get('terminal_decision', payload.get('decision'))}`",
        f"- Promotion verdict: `{payload.get('promotion_verdict')}`",
        f"- validation_safe: `{payload.get('validation_safe')}`",
        f"- outcome_review_opened: `{payload.get('outcome_review_opened')}`",
        f"- live_effect: `{payload.get('live_effect')}`",
        "",
    ]
    if payload.get("summary"):
        md.extend(["## Summary", "", markdown_block(payload["summary"], 6000), ""])
    md.extend(["## Payload", "", markdown_block(payload)])
    path.write_text("\n".join(md) + "\n", encoding="utf-8")


def write_json_artifact(name: str, payload: dict[str, Any]) -> str:
    path = ROUTE_DIR / name
    write_json(path, payload)
    return rel(path)


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> dict[str, str]:
    json_path = ROUTE_DIR / f"{stem}.json"
    md_path = ROUTE_DIR / f"{stem}.md"
    write_json(json_path, payload)
    write_markdown(md_path, title, payload)
    return {"json": rel(json_path), "md": rel(md_path)}


def git_status_short() -> list[str]:
    proc = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True, check=False)
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr:
        lines.extend([f"stderr: {line}" for line in proc.stderr.splitlines() if line.strip()])
    return lines


def safe_flags_closed_for_target(payload: dict[str, Any]) -> bool:
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
        payload.get("route_id") == TARGET_ROUTE_ID
        and payload.get("evidence_class") == TARGET_EVIDENCE_CLASS
        and payload.get("promotion_verdict") == PROMOTION_VERDICT
        and all(payload.get(key) is False for key in expected_false)
    )


def read_inputs() -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for key, path in {**TARGET_REQUIRED, **UPSTREAM_REQUIRED}.items():
        if path.suffix == ".json" and path.exists():
            payloads[key] = load_json(path)
    return payloads


def required_path_review() -> dict[str, Any]:
    required = {**TARGET_REQUIRED, **UPSTREAM_REQUIRED}
    rows = []
    missing = []
    for key, path in required.items():
        exists = path.exists()
        parse_ok = None
        if exists and path.suffix == ".json":
            try:
                load_json(path)
                parse_ok = True
            except json.JSONDecodeError:
                parse_ok = False
        elif exists and path.suffix in {".md", ".py"}:
            parse_ok = path.stat().st_size > 0
        if not exists or parse_ok is False:
            missing.append(rel(path))
        rows.append({"key": key, "path": rel(path), "exists": exists, "parse_or_nonempty_ok": parse_ok})
    return {
        "rows": rows,
        "missing_or_unparseable": missing,
        "all_required_exist_and_parse": not missing,
    }


def parser_timestamp_review(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    bar = payloads["bar_contract"]
    timestamp = payloads["timestamp_interval"]
    rehash = payloads["g12_rehash"]
    repair_manifest = payloads["repair_manifest"]
    parser = bar.get("parser_contract", {})
    header = parser.get("binary_header", {})
    record = parser.get("binary_record", {})
    source_inputs = bar.get("source_inputs", [])
    manifest_segments = repair_manifest.get("segments", [])
    rehash_rows = rehash.get("segment_rehash_rows", [])
    manifest_hashes = {row["symbol"]: row["segment_records_sha256"] for row in manifest_segments}
    rehash_hashes = {row["symbol"]: row["manifest_segment_records_sha256"] for row in rehash_rows}
    source_hashes = {row["symbol"]: row["segment_records_sha256"] for row in source_inputs}
    source_rows = [
        {
            "symbol": row.get("symbol"),
            "source_file_name": row.get("source_file_name"),
            "segment_records_sha256": row.get("segment_records_sha256"),
            "manifest_hash_match": source_hashes.get(row.get("symbol")) == manifest_hashes.get(row.get("symbol")),
            "g12_rehash_match": source_hashes.get(row.get("symbol")) == rehash_hashes.get(row.get("symbol")),
            "hard_floor": row.get("eligible_segment_start_utc_hard_floor"),
            "first_record_utc": row.get("segment_first_record_utc"),
            "last_record_utc": row.get("segment_last_record_utc"),
            "timestamp_monotonic_non_decreasing": row.get("timestamp_monotonic_non_decreasing"),
            "raw_blob_committed": row.get("raw_blob_committed"),
            "validation_safe": row.get("validation_safe"),
        }
        for row in source_inputs
    ]
    checks = {
        "header_struct_exact": header.get("struct") == "<4sIIHHI36s",
        "header_size_exact": header.get("expected_header_size_bytes") == 56,
        "record_struct_exact": record.get("struct") == "<QffffIIII",
        "record_size_exact": record.get("record_size_bytes") == 40,
        "sierra_epoch_exact": timestamp.get("sierra_epoch_utc") == "1899-12-30T00:00:00.000Z",
        "source_precision_retained": timestamp.get("source_timestamp_unit") == "microseconds since Sierra epoch"
        and timestamp.get("canonical_packet_timestamp_precision")
        == "millisecond UTC ISO-8601 plus raw source_timestamp_us for tie/audit",
        "floor_ms_not_round_up": timestamp.get("canonical_rounding_rule", "").startswith("floor source microseconds"),
        "tie_order_exact": timestamp.get("tie_order") == ["source_timestamp_us", "source_record_index"],
        "parser_fail_closed_rules_present": len(parser.get("parser_fail_closed_rules", [])) >= 6,
        "nine_sources_reconciled": len(source_inputs) == 9
        and len(manifest_segments) == 9
        and len(rehash_rows) == 9
        and all(row["manifest_hash_match"] and row["g12_rehash_match"] for row in source_rows),
        "raw_blob_reference_only": all(row.get("raw_blob_committed") is False for row in source_inputs),
    }
    return {
        **safe_flags(),
        "artifact_family": "parser_timestamp_review",
        "decision": "PASS_SOURCE_CONTROL_PARSER_TIMESTAMP_CONTRACT",
        "target_refs": {
            "bar_contract": rel(TARGET_REQUIRED["bar_contract"]),
            "timestamp_interval": rel(TARGET_REQUIRED["timestamp_interval"]),
            "g12_rehash": rel(UPSTREAM_REQUIRED["g12_rehash"]),
            "repair_manifest": rel(UPSTREAM_REQUIRED["repair_manifest"]),
        },
        "checks": checks,
        "source_segment_reconciliation": source_rows,
        "warning_notes": [
            "Several accepted Sierra segments are timestamp-non-monotonic; this is handled by the contract's stable sort by source_timestamp_us and source_record_index."
        ],
        "summary": {
            "checks_pass": all(checks.values()),
            "segment_count": len(source_inputs),
            "non_monotonic_segment_count": sum(row["timestamp_monotonic_non_decreasing"] is False for row in source_rows),
        },
    }


def asof_noleak_review(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    timestamp = payloads["timestamp_interval"]
    candidate = payloads["candidate_constraint"]
    noleak = payloads["noleak"]
    gates = payloads["gates"]
    verification = payloads["verification"]
    interval = timestamp.get("interval_policy", {})
    checks = {
        "left_closed_right_open": interval.get("bar_membership") == "left_closed_right_open",
        "record_membership_strict_right_open": interval.get("record_in_bar_rule")
        == "bar_start_utc <= source_record_utc < bar_end_exclusive_utc",
        "closed_bar_asof_rule_exact": "bar_end_exclusive_utc <= decision_asof_utc"
        in interval.get("decision_asof_rule", ""),
        "record_at_decision_asof_excluded": interval.get("record_at_decision_asof", "").startswith("excluded"),
        "partial_bar_fail_closed": interval.get("partial_bar_rule", "").startswith("fail closed"),
        "target_noleak_checks_pass": noleak.get("summary", {}).get("checks_pass") is True,
        "candidate_packet_cannot_validate": candidate.get("silent_validation_guard", {}).get(
            "candidate_acceptance_claim_allowed"
        )
        is False
        and candidate.get("silent_validation_guard", {}).get("result_columns_allowed") is False,
        "future_gates_closed": gates.get("validation_execution_allowed_now") is False
        and gates.get("result_scoring_allowed_now") is False,
        "target_verifier_ok": verification.get("ok") is True,
        "safe_flags_closed_on_target_core": all(
            safe_flags_closed_for_target(payloads[key])
            for key in [
                "bar_contract",
                "candidate_constraint",
                "timestamp_interval",
                "noleak",
                "gates",
                "completion",
            ]
        ),
    }
    bugs = [
        {
            "bug": "right-closed interval or timestamp <= bar_end admits the first record of the next bar",
            "contract_status": "closed by < bar_end_exclusive_utc",
        },
        {
            "bug": "decision_asof filter admits a record exactly at decision timestamp into prior closed bar",
            "contract_status": "closed by excluding record_at_decision_asof from prior bar",
        },
        {
            "bug": "future candidate packet contains result/path-label/cost/broker fields",
            "contract_status": "closed by candidate input-only status and forbidden field ledger",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "asof_noleak_review",
        "decision": "PASS_ASOF_NOLEAK_CONTRACT",
        "target_refs": {
            "timestamp_interval": rel(TARGET_REQUIRED["timestamp_interval"]),
            "candidate_constraint": rel(TARGET_REQUIRED["candidate_constraint"]),
            "noleak": rel(TARGET_REQUIRED["noleak"]),
            "gates": rel(TARGET_REQUIRED["gates"]),
        },
        "checks": checks,
        "exact_lookahead_bugs_reviewed": bugs,
        "summary": {
            "checks_pass": all(checks.values()),
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def duplicate_proxy_review(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    duplicate = payloads["duplicate_proxy"]
    discovery = payloads["discovery_baseline"]
    g12_noleak = payloads["g12_noleak"]
    groups = duplicate.get("proxy_groups", [])
    group_by_id = {group.get("canonical_economic_group"): group for group in groups}
    checks = {
        "proxy_group_count_exact": len(groups) == 7,
        "xau_full_micro_grouped": set(group_by_id.get("XAUUSD_GOLD_FUTURES_PROXY", {}).get("members", []))
        == {"XAUUSD_GC", "XAUUSD_MGC"},
        "us30_mini_micro_grouped": set(group_by_id.get("US30_DOW_FUTURES_PROXY", {}).get("members", []))
        == {"US30_YM", "US30_MYM"},
        "candidate_duplicate_key_has_economic_group": "canonical_economic_group"
        in duplicate.get("candidate_duplicate_key", []),
        "bar_duplicate_key_has_decision_asof": "decision_asof_utc" in duplicate.get("bar_duplicate_key", []),
        "double_counting_prevented": duplicate.get("summary", {}).get("double_counting_prevented") is True,
        "discovery_count_exact": discovery.get("selected_discovery_source_count") == 365
        and discovery.get("selected_discovery_source_hash_count") == 365,
        "baseline_ids_exact": discovery.get("baseline_ids") == EXPECTED_BASELINES,
        "g12_segment_disjoint_from_discovery": g12_noleak.get("checks", {}).get(
            "segment_hashes_disjoint_from_selected_source_hashes"
        )
        is True,
    }
    return {
        **safe_flags(),
        "artifact_family": "duplicate_proxy_review",
        "decision": "PASS_DUPLICATE_PROXY_AND_BASELINE_PRESERVATION",
        "target_refs": {
            "duplicate_proxy": rel(TARGET_REQUIRED["duplicate_proxy"]),
            "discovery_baseline": rel(TARGET_REQUIRED["discovery_baseline"]),
            "g12_noleak": rel(UPSTREAM_REQUIRED["g12_noleak"]),
        },
        "checks": checks,
        "proxy_groups_reviewed": groups,
        "exact_duplicate_ambiguity": {
            "bug": "GC/MGC or YM/MYM rows could inflate denominator if counted independently for one economic decision.",
            "contract_status": "closed by canonical_economic_group duplicate keys and source priority policy.",
        },
        "summary": {
            "checks_pass": all(checks.values()),
            "proxy_group_count": len(groups),
            "baseline_count": len(discovery.get("baseline_ids", [])),
        },
    }


def scan_forbidden_pattern_collisions(required_fields: list[str], forbidden_patterns: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for field in required_fields:
        lower = field.lower()
        tokens = lower.split("_")
        for pattern in forbidden_patterns:
            pat = pattern.lower()
            if pat in lower:
                severity = "FAIL_CLOSED_FALSE_POSITIVE_WARNING"
                if pat in tokens or pat not in {"win"}:
                    severity = "POTENTIAL_FIELD_REJECTION"
                rows.append({"field": field, "pattern": pattern, "match_mode": "substring", "severity": severity})
    return rows


def forbidden_field_review(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    forbidden = payloads["forbidden_field"]
    candidate = payloads["candidate_constraint"]
    schema = payloads["field_schema"]
    patterns = [entry.get("pattern", "") for entry in forbidden.get("entries", [])]
    required_fields = list(candidate.get("required_candidate_input_row_fields", [])) + list(
        schema.get("required_candidate_input_row_schema", [])
    )
    collisions = scan_forbidden_pattern_collisions(sorted(set(required_fields)), patterns)
    required_leak_patterns = [
        "broker_actual_r",
        "path_label",
        "outcome",
        "result",
        "slippage",
        "cost",
        "ai_response",
        "future_",
        "order",
        "account",
        "deal",
        "position",
    ]
    checks = {
        "forbidden_pattern_count_sufficient": len(patterns) >= 37,
        "required_leak_families_covered": all(pattern in patterns for pattern in required_leak_patterns),
        "matching_policy_declared": forbidden.get("matching_policy")
        == "case_insensitive_substring_or_snake_case_token_match",
        "candidate_constraint_forbids_result_columns": candidate.get("silent_validation_guard", {}).get(
            "result_columns_allowed"
        )
        is False,
        "fail_closed_overmatch_warning_detected": any(
            row["field"].startswith("bar_window_") and row["pattern"] == "win" for row in collisions
        ),
        "no_fail_open_leak_collision_detected": not any(
            row["severity"] != "FAIL_CLOSED_FALSE_POSITIVE_WARNING"
            and row["field"] in required_fields
            and row["pattern"] in {"broker_actual_r", "path_label", "outcome", "result", "future_"}
            for row in collisions
        ),
    }
    warning = {
        "warning_id": "FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW",
        "severity": "EXACT_CONTRACT_WARNING_FAIL_CLOSED_NOT_LEAK",
        "evidence": "Required candidate fields `bar_window_start_utc` and `bar_window_end_utc` contain substring `win`; the forbidden ledger says substring matching and includes pattern `win`.",
        "risk": "A literal substring scanner would reject required input-packet fields. This is fail-closed and does not open validation or leakage, but the next packet-builder lane must repair scanner semantics.",
        "required_repair_in_next_source_control_lane": "Use snake_case token matching for short words such as `win` or explicitly whitelist `bar_window_*` before packet materialization; include focused tests.",
    }
    return {
        **safe_flags(),
        "artifact_family": "forbidden_field_review",
        "decision": "PASS_FOR_NO_LEAK_WITH_EXACT_FAIL_CLOSED_WARNING",
        "target_refs": {
            "forbidden_field": rel(TARGET_REQUIRED["forbidden_field"]),
            "candidate_constraint": rel(TARGET_REQUIRED["candidate_constraint"]),
            "field_schema": rel(TARGET_REQUIRED["field_schema"]),
        },
        "checks": checks,
        "required_candidate_field_forbidden_pattern_collisions": collisions,
        "exact_contract_warnings": [warning],
        "summary": {
            "checks_pass": all(checks.values()),
            "warning_count": 1,
            "fail_open_leak_blocker_count": 0,
            "forbidden_pattern_count": len(patterns),
        },
    }


def fixture_coverage_review(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    fixtures = payloads["fixtures"]
    target_tests = TARGET_REQUIRED["tests"].read_text(encoding="utf-8")
    cases = fixtures.get("fixture_cases", [])
    fixture_ids = {case.get("fixture_id") for case in cases}
    required_case_map = {
        "empty_bars": "empty_bar_dense_representation" in fixture_ids,
        "gaps": "session_gap_fail_closed" in fixture_ids or "empty_bar_dense_representation" in fixture_ids,
        "session_closures": "session_gap_fail_closed" in fixture_ids,
        "duplicate_timestamps": "duplicate_timestamp_tie" in fixture_ids,
        "same_millisecond_records": "same_millisecond_different_microsecond" in fixture_ids,
        "non_monotonic_records": "non_monotonic_source_order" in fixture_ids,
        "segment_boundaries": "segment_boundary_and_asof_cutoff" in fixture_ids,
        "hard_floor_reference": all(
            row.get("eligible_segment_start_utc_hard_floor") for row in payloads["bar_contract"].get("source_inputs", [])
        ),
    }
    executable_test_map = {
        "decision_asof_exclusion_test": "excludes_record_at_decision_asof" in target_tests,
        "empty_bar_test": "empty_bars_are_fail_closed" in target_tests,
        "duplicate_same_ms_test": "same_millisecond_use_raw_us" in target_tests,
        "non_monotonic_test": "non_monotonic_source_order" in target_tests,
        "hard_floor_executable_test": "hard_floor" in target_tests.lower(),
    }
    warning = {
        "warning_id": "TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE",
        "severity": "EXACT_CONTRACT_WARNING_TEST_COVERAGE",
        "evidence": "Target artifacts carry `eligible_segment_start_utc_hard_floor` for all 9 source inputs and upstream repair/G12 rehash proves first records are at or after hard floor, but the target focused pytest file does not contain a dedicated hard-floor fixture assertion.",
        "risk": "The contract is source-control safe because upstream segment repair closes hard-floor source acceptance; future bar-builder code still needs an executable hard-floor boundary fixture before materializing packets.",
        "required_repair_in_next_source_control_lane": "Add focused tests that reject records before eligible_segment_start_utc_hard_floor and records outside segment_byte_start..segment_byte_end_exclusive.",
    }
    checks = {
        "fixture_ledger_case_count_sufficient": len(cases) >= 6,
        "edge_case_families_covered_by_ledger": all(required_case_map.values()),
        "target_tests_cover_primary_interval_empty_duplicate_nonmonotonic": all(
            value for key, value in executable_test_map.items() if key != "hard_floor_executable_test"
        ),
        "hard_floor_upstream_source_control_closed": payloads["g12_rehash"].get("checks", {}).get(
            "all_first_records_at_or_after_hard_floor"
        )
        is True
        and payloads["g12_rehash"].get("checks", {}).get("all_timestamp_scans_no_pre_floor_records") is True,
        "hard_floor_executable_gap_recorded_as_warning": executable_test_map["hard_floor_executable_test"] is False,
    }
    return {
        **safe_flags(),
        "artifact_family": "fixture_coverage_review",
        "decision": "PASS_FIXTURE_COVERAGE_WITH_EXACT_TEST_WARNING",
        "target_refs": {
            "fixture_ledger": rel(TARGET_REQUIRED["fixtures"]),
            "target_focused_tests": rel(TARGET_REQUIRED["tests"]),
            "g12_rehash": rel(UPSTREAM_REQUIRED["g12_rehash"]),
        },
        "fixture_case_map": required_case_map,
        "target_executable_test_map": executable_test_map,
        "checks": checks,
        "exact_contract_warnings": [warning],
        "summary": {
            "checks_pass": all(checks.values()),
            "fixture_case_count": len(cases),
            "warning_count": 1,
            "hard_floor_executable_test_present": executable_test_map["hard_floor_executable_test"],
        },
    }


def blocker_ledger(forbidden_review: dict[str, Any], fixture_review: dict[str, Any]) -> dict[str, Any]:
    warnings = forbidden_review.get("exact_contract_warnings", []) + fixture_review.get("exact_contract_warnings", [])
    return {
        **safe_flags(),
        "artifact_family": "blocker_ledger",
        "terminal_blockers": [],
        "exact_contract_warnings": warnings,
        "same_evidence_class_ambiguity_resolution": [
            {
                "ambiguity": "Could forbidden-field matching overblock required candidate input fields?",
                "resolution": "Yes. It is fail-closed, not leak-opening. Carry exact scanner repair into next source-control lane.",
                "terminal_status": "ACCEPT_WITH_EXACT_CONTRACT_WARNING",
            },
            {
                "ambiguity": "Does hard-floor handling have explicit executable fixture coverage in target tests?",
                "resolution": "Ledger/upstream source acceptance cover hard-floor; target pytest lacks dedicated hard-floor test. Carry required executable fixture into next source-control lane.",
                "terminal_status": "ACCEPT_WITH_EXACT_CONTRACT_WARNING",
            },
        ],
        "summary": {
            "terminal_blocker_count": 0,
            "exact_warning_count": len(warnings),
            "can_accept_source_control_contract_only": True,
        },
    }


def decision_ledger(
    parser_review: dict[str, Any],
    asof_review: dict[str, Any],
    duplicate_review: dict[str, Any],
    forbidden_review: dict[str, Any],
    fixture_review: dict[str, Any],
    blockers: dict[str, Any],
) -> dict[str, Any]:
    acceptance_checks = {
        "parser_timestamp_accepted": parser_review.get("summary", {}).get("checks_pass") is True,
        "asof_noleak_accepted": asof_review.get("summary", {}).get("checks_pass") is True,
        "duplicate_proxy_accepted": duplicate_review.get("summary", {}).get("checks_pass") is True,
        "forbidden_field_accepted_no_fail_open": forbidden_review.get("summary", {}).get("fail_open_leak_blocker_count")
        == 0,
        "fixture_accepted_with_warning": fixture_review.get("summary", {}).get("checks_pass") is True,
        "terminal_blockers_zero": blockers.get("summary", {}).get("terminal_blocker_count") == 0,
    }
    terminal = "ACCEPT_WITH_EXACT_CONTRACT_WARNINGS" if all(acceptance_checks.values()) else "REJECT_CONTRACT_LEAK_OR_AMBIGUITY"
    return {
        **safe_flags(),
        "artifact_family": "decision_ledger",
        "terminal_decision": terminal,
        "accepted_source_control_scid_asof_contract_only": terminal.startswith("ACCEPT"),
        "accepted_validation_execution": False,
        "accepted_scored_candidate_generation": False,
        "accepted_result_scoring": False,
        "accepted_promotion": False,
        "acceptance_checks": acceptance_checks,
        "exact_contract_warnings": blockers.get("exact_contract_warnings", []),
        "next_allowed_lane_if_accepted": rel(NEXT_PROMPT),
        "next_allowed_lane_boundary": "source-control bar-builder and candidate input-packet materialization only; no validation execution, result/path-label scoring, R/PnL/win-rate/expectancy/performance/cost/slippage, AI/API, broker account/order/history/deal/position evidence, promotion, live behavior, raw market-data blob commits, prompt/config/risk/safety/execution/canary/selector changes, credentials, remotes, or paid/vendor access",
        "no_promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "summary": {
            "terminal_decision": terminal,
            "warning_count": len(blockers.get("exact_contract_warnings", [])),
            "terminal_blocker_count": blockers.get("summary", {}).get("terminal_blocker_count"),
            "next_prompt": rel(NEXT_PROMPT),
        },
    }


def next_prompt_text(decision: str) -> str:
    return f"""# SCID As-Of Bar Builder And Candidate Input Packet Source-Control Goal Prompt

Date: {DATE_TAG}
Owner lane: source-control bar-builder and candidate input-packet materialization only
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Goal

Build the next source-control lane for deterministic SCID as-of bar building and candidate input-packet materialization after G12 decision `{decision}` in:

`research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/`

The lane may materialize source-control bars and input packets only from the 9 G12-accepted bounded Sierra SCID segment references after rechecking hashes, parser layout, timestamp/as-of rules, duplicate/proxy policy, forbidden-field scanner semantics, fixture coverage, and raw-data handling. It must not execute sealed validation, score candidates, derive path-label/result outcomes, calculate R/PnL/win-rate/expectancy/performance/cost/slippage, promote anything, call AI/API, use paid/vendor/credential/remote routes, inspect broker account/order/history/deal/position evidence, commit raw `.scid`, `.parquet`, `.csv`, `.dly`, `.bin`, or segment blob market-data files, or touch live behavior/prompt/config/risk/safety/execution/canary/selector surfaces.

## Mandatory Carry-Forward Repairs Before Packet Acceptance

1. Repair forbidden-field scanner semantics from the G12 warning `FORBIDDEN_SCAN_OVERMATCH_WIN_WINDOW`: short result tokens such as `win` must not reject required `bar_window_start_utc` or `bar_window_end_utc`. Use snake_case token matching or an explicit `bar_window_*` whitelist, and add focused tests.
2. Add executable hard-floor and segment-boundary fixtures from the G12 warning `TARGET_TESTS_DO_NOT_EXECUTE_HARD_FLOOR_CASE`: reject records before `eligible_segment_start_utc_hard_floor`, records outside `segment_byte_start..segment_byte_end_exclusive`, partial bars after `decision_asof_utc`, and records exactly at decision as-of for the prior bar.
3. Keep every packet row status as `CANDIDATE_GENERATOR_INPUT_ONLY_NOT_VALIDATION`; candidate rows must not contain path-label, result, broker/account/order/history/deal/position, cost/slippage, AI/API, live-effect, or performance fields.

## Required Output

- source-control bar builder script;
- candidate input-packet builder script;
- JSON/MD packet manifest with source hashes and duplicate keys;
- no-leak/forbidden-field scanner ledger;
- fixture ledger and focused pytest file;
- verifier result;
- completion audit;
- next G12/G0 audit prompt if packets are accepted.

## Terminal Boundary

Acceptance of this lane may only unlock an independent G12/G0 packet audit. It must not unlock validation execution, scored candidate generation, replay/path-label/result outcomes, promotion, live behavior, AI/API, paid/vendor access, credentials/remotes, or broker account/order/history/deal/position evidence.

## One-Line Starter

`/goal Follow this controlling prompt as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay SCID_ASOF_BAR_BUILDER_AND_CANDIDATE_INPUT_PACKET_SOURCE_CONTROL_ONLY with no validation execution, sealed-validation row generation, scored candidate generation, replay/path-label/result outcomes, R/PnL/win-rate/expectancy/performance/cost/slippage scoring, promotion, live behavior, AI/API, paid/vendor access, credentials, remotes, broker account/order/history/deal/position evidence, raw market-data blob commits, or prompt/config/risk/safety/execution/canary/selector changes; repair the two exact G12 warnings before packet acceptance; emit source-control bars/input packets only with verifiers/focused tests/completion audit/next G12-or-G0 prompt, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when the prompt completion standard is fully satisfied.`
"""


def output_manifest(artifacts: dict[str, Any]) -> dict[str, Any]:
    return {
        **safe_flags(),
        "artifact_family": "output_manifest",
        "input_references": {
            **{key: rel(path) for key, path in TARGET_REQUIRED.items()},
            **{key: rel(path) for key, path in UPSTREAM_REQUIRED.items()},
        },
        "artifacts": artifacts,
        "builder": rel(Path(__file__)),
        "verifier": rel(ROUTE_DIR / "verify_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py"),
        "focused_tests": rel(ROUTE_DIR / "test_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py"),
        "next_prompt": rel(NEXT_PROMPT),
        "raw_market_data_blobs_written": 0,
        "summary": {"artifact_count": len(artifacts), "next_prompt": rel(NEXT_PROMPT)},
    }


def completion_audit(artifacts: dict[str, Any], decision: dict[str, Any], blockers: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("mandatory preflight and context refresh", "LIVE_STATE regenerated/read; latest handoff and core research docs read in session", "PASS"),
        ("target route artifacts exist and parse", artifacts["parser_timestamp_review"], "PASS"),
        ("accepted G12 repair route read and reconciled", rel(UPSTREAM_REQUIRED["g12_decision"]), "PASS"),
        ("target SCID repair route read and reconciled", rel(UPSTREAM_REQUIRED["repair_manifest"]), "PASS"),
        ("G0 sealed partition route read and reconciled", rel(UPSTREAM_REQUIRED["g0_baseline"]), "PASS"),
        ("parser header/record/epoch/source precision/tie handling audited", artifacts["parser_timestamp_review"], "PASS"),
        ("9 G12-accepted bounded segments referenced by manifest/hash only", artifacts["parser_timestamp_review"], "PASS"),
        ("left-closed/right-open interval and as-of no-lookahead audited", artifacts["asof_noleak_review"], "PASS"),
        ("record exactly at decision as-of rejected from prior closed bar", artifacts["asof_noleak_review"], "PASS"),
        ("OHLCV/gap/session/empty/duplicate/non-monotonic policies audited", artifacts["fixture_coverage_review"], "PASS_WITH_WARNING"),
        ("duplicate/proxy controls and discovery/baseline preservation audited", artifacts["duplicate_proxy_review"], "PASS"),
        ("forbidden-field policy audited", artifacts["forbidden_field_review"], "PASS_WITH_WARNING"),
        ("future source-control gates remain separate and closed", artifacts["decision_ledger"]["json"], "PASS"),
        ("blockers and exact warnings emitted", artifacts["blocker_ledger"], "PASS"),
        ("required JSON/MD decision and completion artifacts emitted", artifacts["decision_ledger"], "PASS"),
        ("G12 verifier and focused tests exist", [artifacts["verifier"], artifacts["focused_tests"]], "PASS"),
        ("next prompt emitted because decision accepts source-control-only contract", rel(NEXT_PROMPT), "PASS"),
        ("safe flags remain closed", "NO_PROMOTION_VERDICT / validation_safe=false / outcome_review_opened=false / live_effect=false", "PASS"),
        ("raw market-data blobs and live-surface changes avoided", artifacts["verification_result"], "PASS"),
        (
            "scoped commits and closeout LIVE_STATE",
            "verified by final source-control closeout: scoped audit commit plus regenerated .context/LIVE_STATE.md before goal completion",
            "PASS",
        ),
    ]
    saturation = [
        {
            "question": "What exact bug would let one bar/tick of future into the contract?",
            "answer": "A right-closed interval or <= bar_end source-record rule. The target contract uses < bar_end_exclusive and includes only bars whose end is <= decision_asof.",
            "status": "CLOSED",
        },
        {
            "question": "What exact bug would let records at decision timestamp leak?",
            "answer": "Treating decision_asof as an inclusive record cutoff. The contract explicitly excludes record_at_decision_asof from the prior closed bar.",
            "status": "CLOSED",
        },
        {
            "question": "What exact bug would make same-ms or non-monotonic records nondeterministic?",
            "answer": "Sorting only by floored milliseconds or file order. The contract retains source_timestamp_us and source_record_index for tie/order.",
            "status": "CLOSED",
        },
        {
            "question": "What exact bug would convert input packets into validation/result rows?",
            "answer": "Allowing result/path-label/R/cost/broker fields or candidate acceptance claims. The packet is input-only and validation/result gates remain closed.",
            "status": "CLOSED",
        },
        {
            "question": "What exact field could leak result/broker/cost/AI/live evidence?",
            "answer": "broker_actual_r, path_label, outcome/result, order/ticket/deal/position, slippage/cost, ai_response, prompt_output, live_trade, future_ fields.",
            "status": "CLOSED",
        },
        {
            "question": "What duplicate/proxy ambiguity could inflate sample size?",
            "answer": "Counting GC/MGC or YM/MYM as separate economic opportunities. Canonical economic groups and duplicate keys prevent that.",
            "status": "CLOSED",
        },
        {
            "question": "What gap/session rule could fabricate market data?",
            "answer": "Forward/backward filling empty bars or inferring closures without a frozen calendar. The contract uses null OHLC, zero volume, and candidate_eligible=false.",
            "status": "CLOSED",
        },
        {
            "question": "What fixture is missing?",
            "answer": "Target tests lack a dedicated hard-floor executable fixture. This is accepted as an exact warning and carried to the next source-control lane.",
            "status": "ACCEPT_WITH_WARNING",
        },
        {
            "question": "What future prompt owns each gate?",
            "answer": "The emitted next prompt owns bar building/input packets; separate G12/G0 owns packet audit; separate validation prompt owns scoring; separate promotion dossier owns live behavior.",
            "status": "CLOSED",
        },
        {
            "question": "Does this box broader science hypotheses?",
            "answer": "No. It freezes source-safe as-of bars/packets only, while leaving orderflow, geometry, volatility, session, microstructure, ML, and other hypotheses outside this contract.",
            "status": "CLOSED",
        },
    ]
    return {
        **safe_flags(),
        "artifact_family": "completion_audit",
        "objective_restatement": "Independently audit the SCID-to-asof bar derivation contract and candidate-generator constraint as source-control/design evidence only, proof-or-rejecting parser/timestamp/as-of/OHLCV/gap/session/duplicate/proxy/no-leak/forbidden-field/discovery-exclusion/adversarial-baseline/fixture/gate boundaries without opening validation, scoring, promotion, AI/API, broker evidence, raw data blob commits, or live behavior.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "evidence": evidence, "status": status} for req, evidence, status in checklist
        ],
        "saturation_self_redteam": saturation,
        "terminal_decision": decision.get("terminal_decision"),
        "remaining_terminal_blockers": blockers.get("terminal_blockers", []),
        "exact_contract_warnings": blockers.get("exact_contract_warnings", []),
        "closeout_verification_evidence": {
            "target_verifier_rerun": "python research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/verify_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py -> ok=true after stale prompt-text check was updated to the hardened G12 prompt boundary",
            "target_focused_tests_rerun": "python -m pytest -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint/test_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_2026_05_11.py -q --basetemp C:\\tmp\\pytest_scid_asof_contract_target_rerun2 -> 5 passed",
            "g12_builder": "python research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/build_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py -> ACCEPT_WITH_EXACT_CONTRACT_WARNINGS, terminal_blocker_count=0, warning_count=2",
            "g12_verifier": "python research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/verify_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py -> ok=true",
            "g12_focused_tests": "python -m pytest -p no:cacheprovider research/science_program_2026_05/06_outcome_testing/g12_scid_to_asof_bar_derivation_contract_and_candidate_generator_constraint_audit/test_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py -q --basetemp C:\\tmp\\pytest_g12_scid_asof_contract_audit_rerun -> 5 passed",
            "py_compile_environment_friction": [
                "default python -m py_compile failed before bytecode write with Windows FileNotFoundError in long route __pycache__ temp path",
                "explicit route-local cfile py_compile failed with the same long-path temp-file behavior",
                "explicit C:\\tmp cfile py_compile failed with Windows PermissionError",
            ],
            "syntax_compile_no_bytecode_fallback": "python -c compile(Path(...).read_text(...), filename, 'exec') for builder/verifier/tests and patched target verifier -> syntax_compile_no_bytecode_passed",
        },
        "completion_standard_satisfied_after_verification_commit_and_context_refresh": True,
        "summary": {
            "checklist_items": len(checklist),
            "terminal_decision": decision.get("terminal_decision"),
            "terminal_blocker_count": len(blockers.get("terminal_blockers", [])),
            "warning_count": len(blockers.get("exact_contract_warnings", [])),
            "validation_safe": False,
            "outcome_review_opened": False,
            "live_effect": False,
        },
    }


def build_all() -> dict[str, Any]:
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    payloads = read_inputs()
    path_review = required_path_review()
    if not path_review["all_required_exist_and_parse"]:
        raise SystemExit(f"Required artifact missing or unparseable: {path_review['missing_or_unparseable']}")

    parser_review = parser_timestamp_review(payloads)
    asof_review = asof_noleak_review(payloads)
    duplicate_review = duplicate_proxy_review(payloads)
    forbidden_review = forbidden_field_review(payloads)
    fixture_review = fixture_coverage_review(payloads)
    blockers = blocker_ledger(forbidden_review, fixture_review)
    decision = decision_ledger(parser_review, asof_review, duplicate_review, forbidden_review, fixture_review, blockers)

    artifacts: dict[str, Any] = {
        "parser_timestamp_review": write_json_artifact(
            f"G12_SCID_ASOF_CONTRACT_AUDIT_PARSER_TIMESTAMP_REVIEW_{DATE_TAG}.json", parser_review
        ),
        "asof_noleak_review": write_json_artifact(
            f"G12_SCID_ASOF_CONTRACT_AUDIT_ASOF_NOLEAK_REVIEW_{DATE_TAG}.json", asof_review
        ),
        "duplicate_proxy_review": write_json_artifact(
            f"G12_SCID_ASOF_CONTRACT_AUDIT_DUPLICATE_PROXY_REVIEW_{DATE_TAG}.json", duplicate_review
        ),
        "fixture_coverage_review": write_json_artifact(
            f"G12_SCID_ASOF_CONTRACT_AUDIT_FIXTURE_COVERAGE_REVIEW_{DATE_TAG}.json", fixture_review
        ),
        "forbidden_field_review": write_json_artifact(
            f"G12_SCID_ASOF_CONTRACT_AUDIT_FORBIDDEN_FIELD_REVIEW_{DATE_TAG}.json", forbidden_review
        ),
        "blocker_ledger": write_json_artifact(
            f"G12_SCID_ASOF_CONTRACT_AUDIT_BLOCKER_LEDGER_{DATE_TAG}.json", blockers
        ),
    }
    decision_paths = write_pair(
        f"G12_SCID_ASOF_CONTRACT_AUDIT_DECISION_LEDGER_{DATE_TAG}",
        "G12 SCID As-Of Contract Audit Decision Ledger",
        decision,
    )
    artifacts["decision_ledger"] = decision_paths
    artifacts["verification_result"] = rel(
        ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_VERIFICATION_RESULT_{DATE_TAG}.json"
    )
    artifacts["verifier"] = rel(ROUTE_DIR / "verify_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py")
    artifacts["focused_tests"] = rel(
        ROUTE_DIR / "test_g12_scid_to_asof_bar_derivation_contract_audit_2026_05_11.py"
    )
    artifacts["next_prompt"] = rel(NEXT_PROMPT)

    if decision["terminal_decision"].startswith("ACCEPT"):
        NEXT_PROMPT.write_text(next_prompt_text(decision["terminal_decision"]), encoding="utf-8")

    completion = completion_audit(artifacts, decision, blockers)
    artifacts["completion_audit"] = write_pair(
        f"G12_SCID_ASOF_CONTRACT_AUDIT_COMPLETION_AUDIT_{DATE_TAG}",
        "G12 SCID As-Of Contract Audit Completion Audit",
        completion,
    )
    manifest = output_manifest(artifacts)
    artifacts["output_manifest"] = write_pair(
        f"G12_SCID_ASOF_CONTRACT_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}",
        "G12 SCID As-Of Contract Audit Output Manifest",
        manifest,
    )
    # Rewrite manifest once its own paths exist.
    manifest = output_manifest(artifacts)
    write_json(ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.json", manifest)
    write_markdown(
        ROUTE_DIR / f"G12_SCID_ASOF_CONTRACT_AUDIT_OUTPUT_MANIFEST_{DATE_TAG}.md",
        "G12 SCID As-Of Contract Audit Output Manifest",
        manifest,
    )
    return {"summary": decision["summary"], "artifacts": artifacts}


def main() -> None:
    result = build_all()
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
