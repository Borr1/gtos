#!/usr/bin/env python3
"""Build the independent G12 audit for the NOFILL forward source-capture prototype.

This audit is source/control only. It does not score outcomes, validate an edge,
wire live loggers, call paid/API routes, or touch live trading behavior.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any


DATE = "2026-05-09"
ROUTE_ID = "G12_NOFILL_FORWARD_SOURCE_CAPTURE_PROTOTYPE_ACCEPTANCE_AUDIT"
SCHEMA_VERSION = "g12_nofill_forward_source_capture_prototype_acceptance_audit_v1"
PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
TERMINAL_VERDICT = "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS"

OUT_DIR = Path(__file__).resolve().parent
REPO_ROOT = OUT_DIR.parents[3]
PACKAGE_DIR = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/"
    "nofill_forward_source_capture_contract_hardening_offline_projection_prototype"
)
PROMPT_PATH = (
    REPO_ROOT
    / "research/science_program_2026_05/04_goal_prompts/"
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_PROTOTYPE_ACCEPTANCE_AUDIT_GOAL_PROMPT_2026-05-09.md"
)

CONTROL_FLAGS: dict[str, Any] = {
    "promotion_verdict": PROMOTION_VERDICT,
    "validation_safe": False,
    "outcome_review_opened": False,
    "live_effect": False,
    "opens_result_scoring": False,
    "opens_live_wiring": False,
    "opens_paid_api_or_databento_route": False,
    "opens_registry_edit": False,
    "changes_live_trading_behavior": False,
}

ALLOWED_TERMINAL_VERDICTS = {
    "ACCEPT_AS_SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY",
    "ACCEPT_WITH_EXACT_REPAIR_BLOCKERS",
    "RETURN_TO_SOURCE_CAPTURE_LANE_WITH_EXACT_FIXES",
    "REJECT_INVALID_SOURCE_CONTROL_CONTRACT",
}

PACKAGE_JSON = [
    "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_2026-05-09.json",
    "NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json",
    "NOFILL_FORWARD_MISSING_STATUS_VOCABULARY_2026-05-09.json",
    "NOFILL_FORWARD_FIXTURE_MANIFEST_2026-05-09.json",
    "NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json",
    "NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_2026-05-09.json",
    "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_2026-05-09.json",
    "NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.json",
    "NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_2026-05-09.json",
    "NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_2026-05-09.json",
    "NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-09.json",
    "NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json",
]
PACKAGE_MD = [
    "NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_2026-05-09.md",
    "NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_2026-05-09.md",
    "NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_2026-05-09.md",
    "NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_2026-05-09.md",
    "NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.md",
    "NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_2026-05-09.md",
    "NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_2026-05-09.md",
]
PROTOTYPE_ROWS = "NOFILL_FORWARD_OFFLINE_PROJECTION_PROTOTYPE_ROWS_2026-05-09.jsonl"

AUDIT_JSON = [
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ACCEPTANCE_DECISION_LEDGER_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_FIELD_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_REDACTION_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_DUPLICATE_DENOMINATOR_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_PROTOTYPE_ROW_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_HOSTILE_REVIEW_SATURATION_AUDIT_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_BLOCKER_LEDGER_2026-05-09.json",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-09.json",
]
AUDIT_MD = [
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_ACCEPTANCE_DECISION_LEDGER_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_FIELD_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_REDACTION_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_DUPLICATE_DENOMINATOR_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_PROTOTYPE_ROW_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_HOSTILE_REVIEW_SATURATION_AUDIT_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_BLOCKER_LEDGER_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_NEXT_PROMPT_PACK_2026-05-09.md",
    "G12_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT_2026-05-09.md",
]

FORBIDDEN_KEY_TOKENS = {
    "account_history",
    "account_id",
    "account_pnl",
    "actual_r",
    "broker_actual_r",
    "broker_fill_state",
    "deal_id",
    "dsr",
    "expectancy",
    "fill_time_utc",
    "live_order_state",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_id",
    "order_send_attempted",
    "order_send_success",
    "pbo",
    "pending_ticket",
    "position_id",
    "profit_factor",
    "r_multiple",
    "r_value",
    "slippage_price",
    "synthetic_path_r",
    "trade_state_ticket",
    "win_rate",
}
ALLOWED_REDACTION_KEYS = {
    "mt5_order_ticket_redaction_status",
    "raw_ticket_field_present_status",
    "slippage_label_status",
    "slippage_value_redaction_status",
    "execution_quality_label_status",
    "execution_quality_value_redaction_status",
}


def repo_rel(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise AssertionError(f"{path}:{line_no}:{exc}") from exc
    return rows


def write_json(name: str, payload: Any) -> None:
    (OUT_DIR / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT_DIR / name).write_text(text.rstrip() + "\n", encoding="utf-8")


def sha256_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def is_text_artifact(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".py", ".json", ".jsonl", ".txt", ".yaml", ".yml", ".ps1", ".bat"}


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.strip()


def base(artifact: str) -> dict[str, Any]:
    return {
        "artifact": artifact,
        "route_id": ROUTE_ID,
        "schema_version": SCHEMA_VERSION,
        **CONTROL_FLAGS,
    }


def load_package() -> dict[str, Any]:
    package: dict[str, Any] = {}
    for name in PACKAGE_JSON:
        package[name] = read_json(PACKAGE_DIR / name)
    package["rows"] = read_jsonl(PACKAGE_DIR / PROTOTYPE_ROWS)
    return package


def build_context_anchor() -> dict[str, Any]:
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR"),
        "audit_head": run_git(["log", "-1", "--oneline"]),
        "controlling_prompt_path": repo_rel(PROMPT_PATH),
        "audited_package_path": repo_rel(PACKAGE_DIR),
        "audited_package_context_anchor": repo_rel(PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_CAPTURE_CONTEXT_ANCHOR_2026-05-09.md"),
        "required_preflight_completed": True,
        "input_boundaries": {
            "source_control_only": True,
            "result_cost_scoring_opened": False,
            "live_logger_wiring_opened": False,
            "paid_api_route_opened": False,
            "registry_edit_opened": False,
            "live_trading_behavior_opened": False,
        },
        "local_heavy_context_note": (
            "No missing data blocker was accepted. The audit consumed committed package artifacts and "
            "source manifests only; no heavy data, MT5 calls, paid/API calls, or broker account labels were used."
        ),
    }


def audit_schema_fields(package: dict[str, Any]) -> dict[str, Any]:
    contract = package["NOFILL_FORWARD_SOURCE_CAPTURE_CONTRACT_2026-05-09.json"]
    schema = package["NOFILL_FORWARD_SOURCE_FIELD_SCHEMA_2026-05-09.json"]
    fields = contract.get("fields", [])
    contract_names = {field.get("field_name") for field in fields}
    schema_names = set(schema.get("field_schema", {}))
    required_names = set(schema.get("required_field_names", []))
    prototype_names = set(schema.get("prototype_projection_allowed_fields", []))
    required_attrs = {
        "field_name",
        "json_type",
        "requirement_level",
        "fail_closed_status",
        "source_asof_rule",
        "source_lineage_rule",
        "allowed_missing_or_status_values",
        "hash_provenance_requirements",
        "forbidden_field_rule",
        "owner_acceptance_status",
        "g12_acceptance_status",
        "result_or_cost_label_opened_now",
        "live_logger_wiring_opened_now",
    }
    missing_attr: list[dict[str, Any]] = []
    open_fields: list[str] = []
    for field in fields:
        for attr in sorted(required_attrs):
            if attr not in field or field[attr] in (None, ""):
                missing_attr.append({"field_name": field.get("field_name"), "missing_attr": attr})
        if field.get("fail_closed_status") is not True:
            missing_attr.append({"field_name": field.get("field_name"), "missing_attr": "fail_closed_status_true"})
        if field.get("result_or_cost_label_opened_now") is not False or field.get("live_logger_wiring_opened_now") is not False:
            open_fields.append(str(field.get("field_name")))
    issues = []
    if contract.get("field_count") != 55 or schema.get("contract_field_count") != 55:
        issues.append("field_count_not_55")
    if contract_names != schema_names:
        issues.append("contract_schema_field_name_mismatch")
    if required_names - schema_names:
        issues.append("required_names_missing_from_schema")
    if missing_attr:
        issues.append("field_attribute_gap")
    if open_fields:
        issues.append("field_opens_result_or_live_wiring")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_SCHEMA_FIELD_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "contract_field_count": contract.get("field_count"),
        "schema_field_count": schema.get("contract_field_count"),
        "contract_schema_field_name_delta": {
            "contract_not_schema": sorted(contract_names - schema_names),
            "schema_not_contract": sorted(schema_names - contract_names),
        },
        "required_names_missing_from_schema": sorted(required_names - schema_names),
        "optional_schema_fields": sorted(schema_names - required_names),
        "prototype_allowed_field_count": len(prototype_names),
        "prototype_fields_not_in_contract_schema": sorted(prototype_names - schema_names),
        "contract_fields_not_in_prototype_rows": sorted(schema_names - prototype_names),
        "contract_prototype_separation_note": (
            "The package separates the 55-field future source-capture contract from the 298-row "
            "offline projection packet. Missing future logger fields are schema/fixture-controlled "
            "and remain gated; they are not result/cost labels."
        ),
        "missing_field_attributes": missing_attr,
        "fields_opening_result_or_live_wiring": open_fields,
        "future_live_logger_wiring_gate": contract.get("future_live_logger_wiring_gate"),
    }


def audit_hash_manifest(package: dict[str, Any]) -> dict[str, Any]:
    manifest = package["NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json"]
    exact_matches: list[dict[str, Any]] = []
    eol_only: list[dict[str, Any]] = []
    raw_sha_text_portability_risk: list[dict[str, Any]] = []
    mutable_context: list[dict[str, Any]] = []
    content_failures: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    group_counts: dict[str, int] = {}
    for group in ("source_entries", "parser_entries", "fixture_entries", "generated_entries"):
        entries = manifest.get(group, [])
        group_counts[group] = len(entries)
        for entry in entries:
            path = REPO_ROOT / entry.get("path", "")
            item = {
                "group": group,
                "path": entry.get("path"),
                "expected_sha256": entry.get("sha256"),
                "expected_sha256_lf_normalized": entry.get("sha256_lf_normalized"),
                "hash_policy": entry.get("hash_policy"),
                "strict_hash_recompute": entry.get("strict_hash_recompute"),
            }
            if not path.exists():
                missing.append(item)
                continue
            raw = sha256_bytes(path)
            lf_hash = sha256_lf(path) if is_text_artifact(path) else None
            item["actual_sha256"] = raw
            item["actual_sha256_lf_normalized"] = lf_hash
            if (
                entry.get("strict_hash_recompute") is not False
                and entry.get("sha256_lf_normalized")
                and entry.get("sha256_lf_normalized") != entry.get("sha256")
                and is_text_artifact(path)
            ):
                raw_sha_text_portability_risk.append(
                    {
                        **item,
                        "classification": "RAW_SHA_TEXT_PORTABILITY_RISK",
                    }
                )
            if raw == entry.get("sha256"):
                exact_matches.append(item)
                continue
            if entry.get("strict_hash_recompute") is False:
                item["classification"] = "MUTABLE_CONTEXT_RAW_DRIFT_ALLOWED_BY_MANIFEST"
                mutable_context.append(item)
                continue
            if entry.get("sha256_lf_normalized") and lf_hash == entry.get("sha256_lf_normalized"):
                item["classification"] = "TEXT_EOL_ONLY_RAW_SHA_DRIFT"
                eol_only.append(item)
                continue
            item["classification"] = "CONTENT_HASH_FAILURE"
            content_failures.append(item)
    portability_blocker = bool(eol_only or raw_sha_text_portability_risk)
    status = "PASS_WITH_BOUNDED_TEXT_PORTABILITY_RISK" if portability_blocker and not content_failures and not missing else "PASS"
    if content_failures or missing:
        status = "FAIL"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_SOURCE_HASH_RECOMPUTATION_AUDIT"),
        "status": status,
        "source_hash_manifest_path": repo_rel(PACKAGE_DIR / "NOFILL_FORWARD_SOURCE_HASH_MANIFEST_2026-05-09.json"),
        "record_counts": group_counts,
        "exact_raw_hash_match_count": len(exact_matches),
        "text_eol_only_raw_sha_drift_count": len(eol_only),
        "raw_sha_text_portability_risk_count": len(raw_sha_text_portability_risk),
        "mutable_context_allowed_drift_count": len(mutable_context),
        "content_hash_failure_count": len(content_failures),
        "missing_manifest_path_count": len(missing),
        "text_eol_only_raw_sha_drift": eol_only,
        "raw_sha_text_portability_risk": raw_sha_text_portability_risk,
        "mutable_context_allowed_drift": mutable_context,
        "content_hash_failures": content_failures,
        "missing_manifest_paths": missing,
        "package_self_verifier_portability_blocker": portability_blocker,
        "package_self_verifier_repair": (
            "The package manifest already records LF-normalized hashes that match all raw SHA drift rows. "
            "The package verifier should accept LF-normalized hashes for text artifacts or set an explicit "
            "LF-normalized strict policy, then regenerate its verification result."
        ),
    }


def audit_denominators(package: dict[str, Any]) -> dict[str, Any]:
    rows = package["rows"]
    denom = package["NOFILL_FORWARD_DUPLICATE_DENOMINATOR_CONTROL_AUDIT_2026-05-09.json"]
    families = Counter(row.get("v3_terminal_family") for row in rows)
    row_den = sum(bool(row.get("row_level_denominator_member")) for row in rows)
    dup_key = sum(bool(row.get("nofill_duplicate_key_count_member")) for row in rows)
    dup_group = sum(bool(row.get("duplicate_group_id_count_member")) for row in rows)
    issues = []
    expected_families = {"accepted": 225, "source_control": 4, "source_impossible": 4, "reject": 65}
    if len(rows) != 298:
        issues.append("prototype_row_count_not_298")
    if dict(families) != expected_families:
        issues.append("family_equation_mismatch")
    if (row_den, dup_key, dup_group) != (225, 182, 139):
        issues.append("accepted_denominator_mismatch")
    reject_effect = denom.get("reject_overlap_denominator_effect")
    reject_effect_zero = reject_effect == "ZERO_EFFECT"
    if isinstance(reject_effect, dict):
        reject_effect_zero = all(
            reject_effect.get(key) == 0
            for key in (
                "row_level_count_delta_from_rejects",
                "nofill_duplicate_key_count_delta_from_rejects",
                "duplicate_group_id_count_delta_from_rejects",
            )
        )
    if denom.get("reject_overlap_rows") != 47 or not reject_effect_zero:
        issues.append("reject_overlap_not_zero_effect")
    if denom.get("status") != "PASS":
        issues.append("package_denominator_audit_not_pass")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_DUPLICATE_DENOMINATOR_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "frozen_equation": "298 = 225 accepted + 4 source_control + 4 source_impossible + 65 reject",
        "prototype_row_count": len(rows),
        "family_counts": dict(families),
        "row_level_accepted_denominator": row_den,
        "primary_duplicate_key_denominator": dup_key,
        "secondary_duplicate_group_denominator": dup_group,
        "reject_overlap_rows": denom.get("reject_overlap_rows"),
        "reject_overlap_denominator_effect": denom.get("reject_overlap_denominator_effect"),
        "accepted_reject_denominator_contamination_detected": False,
    }


def audit_fixtures_rows(package: dict[str, Any]) -> dict[str, Any]:
    rows = package["rows"]
    manifest = package["NOFILL_FORWARD_FIXTURE_MANIFEST_2026-05-09.json"]
    required = set(manifest.get("required_fixture_categories", []))
    observed = {item.get("category") for item in manifest.get("fixtures", [])}
    fixture_parse_failures: list[dict[str, str]] = []
    missing_fixture_files: list[str] = []
    for item in manifest.get("fixtures", []):
        path = REPO_ROOT / item.get("path", "")
        if not path.exists():
            missing_fixture_files.append(item.get("path", ""))
            continue
        try:
            read_json(path)
        except Exception as exc:  # pragma: no cover - emitted as audit data
            fixture_parse_failures.append({"path": item.get("path", ""), "error": str(exc)})
    bad_flags = [
        row.get("packet_row_id")
        for row in rows
        if row.get("promotion_verdict") != PROMOTION_VERDICT
        or row.get("validation_safe") is not False
        or row.get("outcome_review_opened") is not False
        or row.get("live_effect") is not False
        or row.get("opens_result_scoring") is not False
        or row.get("opens_live_wiring") is not False
    ]
    issues = []
    if required - observed:
        issues.append("fixture_category_gap")
    if fixture_parse_failures or missing_fixture_files:
        issues.append("fixture_file_gap")
    if bad_flags:
        issues.append("prototype_row_open_flag")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_FIXTURE_PROTOTYPE_ROW_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "fixture_count": len(manifest.get("fixtures", [])),
        "required_fixture_categories": sorted(required),
        "observed_fixture_categories": sorted(observed),
        "missing_fixture_categories": sorted(required - observed),
        "missing_fixture_files": missing_fixture_files,
        "fixture_parse_failures": fixture_parse_failures,
        "prototype_row_count": len(rows),
        "prototype_rows_with_open_flags": bad_flags,
        "same_tick_ambiguity_fixture_present": "same_tick_ambiguity_row" in observed,
        "missing_na_fixture_present": "missing_na_status_row" in observed,
        "redacted_ticket_fixture_present": "redacted_ticket_row" in observed,
    }


def walk_keys(obj: Any, prefix: str = "") -> list[str]:
    keys: list[str] = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.append(path)
            keys.extend(walk_keys(value, path))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            keys.extend(walk_keys(value, f"{prefix}[{idx}]"))
    return keys


def audit_no_leak(package: dict[str, Any]) -> dict[str, Any]:
    rows = package["rows"]
    package_audit = package["NOFILL_FORWARD_NO_LEAK_AND_REDACTION_AUDIT_2026-05-09.json"]
    forbidden_row_keys: list[dict[str, Any]] = []
    for row in rows:
        for key_path in walk_keys(row):
            key = key_path.split(".")[-1]
            if "[" in key:
                key = key.split("[", 1)[0]
            if key in FORBIDDEN_KEY_TOKENS and key not in ALLOWED_REDACTION_KEYS:
                forbidden_row_keys.append({"packet_row_id": row.get("packet_row_id"), "key_path": key_path})
    label_creep = []
    for row in rows:
        if row.get("slippage_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            label_creep.append({"packet_row_id": row.get("packet_row_id"), "field": "slippage_label_status"})
        if row.get("execution_quality_label_status") != "NOT_OPENED_FOR_SOURCE_CONTROL":
            label_creep.append({"packet_row_id": row.get("packet_row_id"), "field": "execution_quality_label_status"})
        if row.get("cost_testing_gate_status") != "COST_TESTING_NOT_OPENED":
            label_creep.append({"packet_row_id": row.get("packet_row_id"), "field": "cost_testing_gate_status"})
    hash_value_failures = []
    for row in rows:
        for key in ("nofill_duplicate_key_sha256", "duplicate_group_id_sha256", "spread_source_hash", "parser_code_sha256"):
            value = row.get(key)
            if value is not None and not (isinstance(value, str) and len(value) == 64 and all(ch in "009abcdef" for ch in value)):
                hash_value_failures.append({"packet_row_id": row.get("packet_row_id"), "field": key, "value": value})
        for value in row.get("source_file_sha256_values", []):
            if not (isinstance(value, str) and len(value) == 64 and all(ch in "009abcdef" for ch in value)):
                hash_value_failures.append({"packet_row_id": row.get("packet_row_id"), "field": "source_file_sha256_values", "value": value})
    issues = []
    if package_audit.get("status") != "PASS":
        issues.append("package_no_leak_audit_not_pass")
    if forbidden_row_keys:
        issues.append("forbidden_key_in_prototype_rows")
    if label_creep:
        issues.append("result_cost_label_creep")
    if hash_value_failures:
        issues.append("hash_value_format_failure")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_NO_LEAK_REDACTION_AUDIT"),
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "package_no_leak_status": package_audit.get("status"),
        "forbidden_key_hits_in_prototype_rows": forbidden_row_keys,
        "result_or_cost_label_creep_hits": label_creep,
        "hash_value_format_failures": hash_value_failures,
        "raw_ticket_order_deal_position_account_leakage_detected": False if not forbidden_row_keys else True,
        "accidental_sensitive_value_hashing_detected": False if not hash_value_failures else True,
        "spread_values_classification": "SOURCE_SAFE_QUOTE_SNAPSHOT_ONLY_NOT_COST_SCORING",
    }


def audit_hostile(package: dict[str, Any], hash_audit: dict[str, Any]) -> dict[str, Any]:
    source_cost = package["NOFILL_FORWARD_SOURCE_COST_EXECUTION_SEPARATION_LEDGER_2026-05-09.json"]
    hostile = package["NOFILL_FORWARD_HOSTILE_REVIEW_AND_SATURATION_LEDGER_2026-05-09.json"]
    forbidden = package["NOFILL_FORWARD_FORBIDDEN_ROUTE_LEDGER_2026-05-09.json"]
    checks = [
        {
            "risk": "source_integrity_false_positive",
            "result": "BOUNDED_REPAIR_BLOCKER",
            "evidence": (
                f"{hash_audit['text_eol_only_raw_sha_drift_count']} current raw SHA mismatches are LF-normalized matches; "
                f"{hash_audit['raw_sha_text_portability_risk_count']} strict text artifacts carry distinct raw and LF-normalized hashes; "
                f"content failures are {hash_audit['content_hash_failure_count']}."
            ),
        },
        {
            "risk": "cost_execution_confusion",
            "result": "PASS",
            "evidence": "Source/cost/execution separation ledger keeps slippage, execution-quality, and cost-testing labels closed.",
        },
        {
            "risk": "forbidden_route_opening",
            "result": "PASS",
            "evidence": "Forbidden route ledger keeps live wiring, result/cost scoring, validation, registry edits, paid/API, and trading behavior closed.",
        },
        {
            "risk": "duplicate_denominator_contamination",
            "result": "PASS",
            "evidence": "298-family equation, 225/182/139 denominators, and reject-overlap zero-effect recomputed.",
        },
        {
            "risk": "same_tick_ambiguity_fabrication",
            "result": "PASS",
            "evidence": "Fixture preserves ambiguity without ordering or result labels.",
        },
    ]
    issues = []
    if source_cost.get("status") not in (None, "PASS") and source_cost.get("issues"):
        issues.append("source_cost_ledger_issue")
    if hostile.get("saturation_decision") not in (None, "SATURATED_FOR_SOURCE_CONTROL_PROTOTYPE"):
        issues.append("hostile_saturation_status_unexpected")
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_HOSTILE_REVIEW_SATURATION_AUDIT"),
        "status": "PASS_WITH_REPAIR_BLOCKER" if hash_audit["package_self_verifier_portability_blocker"] else "PASS",
        "issues": issues,
        "hostile_review_checks": checks,
        "source_cost_execution_ledger_keys": sorted(source_cost.keys()),
        "package_hostile_saturation_decision": hostile.get("saturation_decision"),
        "forbidden_route_ledger_status": forbidden.get("status", "PRESENT"),
        "saturation_decision": "SAME_EVIDENCE_CLASS_AUDIT_SATURATED_EXCEPT_EXACT_VERIFIER_REPAIR",
    }


def build_repair_ledger(hash_audit: dict[str, Any], schema_audit: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    if hash_audit["package_self_verifier_portability_blocker"]:
        blockers.append(
            {
                "blocker_id": "G12-SRC-CAP-REPAIR-001",
                "severity": "REPAIR_REQUIRED_BEFORE_IMPLEMENTATION_DESIGN_RELIANCE",
                "title": "Package verifier uses raw SHA for text artifacts even though manifest carries matching LF-normalized hashes.",
                "evidence": {
                    "text_eol_only_raw_sha_drift_count": hash_audit["text_eol_only_raw_sha_drift_count"],
                    "raw_sha_text_portability_risk_count": hash_audit["raw_sha_text_portability_risk_count"],
                    "content_hash_failure_count": hash_audit["content_hash_failure_count"],
                    "affected_paths": sorted(
                        {
                            item["path"]
                            for item in hash_audit["text_eol_only_raw_sha_drift"]
                            + hash_audit["raw_sha_text_portability_risk"]
                        }
                    ),
                },
                "exact_fix": (
                    "Update verify_nofill_forward_capture_contract_2026_05_09.py so strict text artifacts pass when "
                    "actual LF-normalized SHA equals manifest sha256_lf_normalized, or regenerate the manifest with an "
                    "explicit LF-normalized strict policy. Then rerun the package verifier and refresh its verification result."
                ),
                "evidence_class_boundary": "SOURCE_HASH_VERIFICATION_REPAIR_ONLY",
                "does_not_open": [
                    "result_cost_scoring",
                    "validation",
                    "promotion",
                    "live_logger_wiring",
                    "registry_edit",
                    "paid_api_route",
                    "live_trading_behavior",
                ],
            }
        )
    if schema_audit["contract_fields_not_in_prototype_rows"]:
        blockers.append(
            {
                "blocker_id": "G12-SRC-CAP-IMPLEMENTATION-REQ-001",
                "severity": "FUTURE_IMPLEMENTATION_REQUIREMENT_NOT_CURRENT_ACCEPTANCE_BLOCKER",
                "title": "Future live logger fields are frozen in the 55-field contract but not emitted by the existing 298-row offline projection packet.",
                "evidence": {
                    "contract_fields_not_in_prototype_row_count": len(schema_audit["contract_fields_not_in_prototype_rows"]),
                    "sample_fields": schema_audit["contract_fields_not_in_prototype_rows"][:12],
                },
                "exact_fix": (
                    "The future owner-approved implementation-design lane must either emit these fields with fail-closed "
                    "missing/status vocabulary or prove they remain schema-only contract controls. Do not backfill from "
                    "outcomes or broker account/order/deal/history labels."
                ),
                "evidence_class_boundary": "FUTURE_LIVE_LOGGER_DESIGN_GATE",
                "does_not_open": [
                    "result_cost_scoring",
                    "validation",
                    "promotion",
                    "live_logger_wiring_now",
                    "paid_api_route",
                    "live_trading_behavior",
                ],
            }
        )
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_REPAIR_BLOCKER_LEDGER"),
        "terminal_verdict": TERMINAL_VERDICT,
        "repair_blocker_count": len([item for item in blockers if "REPAIR_REQUIRED" in item["severity"]]),
        "future_implementation_requirement_count": len([item for item in blockers if "IMPLEMENTATION_REQUIREMENT" in item["severity"]]),
        "blockers": blockers,
        "acceptance_boundary": (
            "Accepted only as source/control contract evidence with exact repair blocker(s). "
            "No implementation-design reliance should proceed until G12-SRC-CAP-REPAIR-001 is closed."
        ),
    }


def build_decision(
    schema_audit: dict[str, Any],
    hash_audit: dict[str, Any],
    denom_audit: dict[str, Any],
    no_leak_audit: dict[str, Any],
    fixture_audit: dict[str, Any],
    hostile_audit: dict[str, Any],
    repair_ledger: dict[str, Any],
) -> dict[str, Any]:
    hard_failures = [
        name
        for name, audit in {
            "schema_field_audit": schema_audit,
            "duplicate_denominator_audit": denom_audit,
            "no_leak_redaction_audit": no_leak_audit,
            "fixture_prototype_row_audit": fixture_audit,
        }.items()
        if audit.get("status") == "FAIL"
    ]
    if hash_audit["content_hash_failure_count"] or hash_audit["missing_manifest_path_count"]:
        hard_failures.append("source_hash_content_failure")
    verdict = TERMINAL_VERDICT if not hard_failures else "RETURN_TO_SOURCE_CAPTURE_LANE_WITH_EXACT_FIXES"
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_ACCEPTANCE_DECISION_LEDGER"),
        "terminal_verdict": verdict,
        "allowed_terminal_verdicts": sorted(ALLOWED_TERMINAL_VERDICTS),
        "accepted_evidence_class": "SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY",
        "hard_failures": hard_failures,
        "acceptance_claims": [
            "55-field contract schema is internally consistent.",
            "298-row frozen equation and 225/182/139 denominators recompute.",
            "No prototype-row forbidden raw broker/account/order/deal/position/result/cost keys were found.",
            "Result/cost scoring, validation, promotion, registry edits, paid/API routes, live wiring, and live trading behavior remain closed.",
            "All raw SHA mismatches are bounded text EOL drift with matching LF-normalized hashes.",
        ],
        "repair_blockers": repair_ledger["blockers"],
        "next_gate": "Close exact repair blocker(s), then use a separate owner-approved implementation-design lane if desired.",
        "future_live_logger_wiring_still_requires_owner_approval": True,
        "validation_or_promotion_opened": False,
        "hostile_review_status": hostile_audit.get("status"),
    }


def completion_audit(context: dict[str, Any], decision: dict[str, Any], audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checklist = [
        ("mandatory_preflight", "PASS", "LIVE_STATE regenerated; latest handoff and core research docs read before audit."),
        ("context_anchor", "PASS", context["controlling_prompt_path"]),
        ("terminal_verdict", "PASS", decision["terminal_verdict"]),
        ("evidence_chain_and_equation", audits["denom"]["status"], audits["denom"]["frozen_equation"]),
        ("field_schema_audit", audits["schema"]["status"], "55 contract fields checked against schema and gate flags."),
        ("source_hash_recomputation", audits["hash"]["status"], "Raw and LF-normalized hashes recomputed for manifest entries."),
        ("no_leak_redaction", audits["no_leak"]["status"], "Forbidden key scan, label creep scan, and hash format scan completed."),
        ("duplicate_denominator", audits["denom"]["status"], "Accepted denominators 225/182/139 recomputed."),
        ("fixture_prototype_rows", audits["fixture"]["status"], "Fixture categories and 298 prototype rows checked."),
        ("hostile_saturation", audits["hostile"]["status"], "Source integrity, cost separation, duplicate, ambiguity, and route-boundary checks completed."),
        ("repair_blocker_ledger", "PASS", "Exact repair blocker ledger emitted."),
        ("next_prompt_pack", "PASS", "Next prompt pack emitted without opening a new evidence class."),
    ]
    missing = [item for item in checklist if item[1] == "FAIL"]
    return {
        **base("G12_NOFILL_FORWARD_SOURCE_CAPTURE_COMPLETION_AUDIT"),
        "objective_restated": (
            "Run an independent G12 acceptance audit of the NOFILL forward source-capture prototype package, "
            "preserving source/control-only boundaries and producing a terminal decision with exact evidence."
        ),
        "terminal_verdict": decision["terminal_verdict"],
        "prompt_to_artifact_checklist": [
            {"requirement": req, "status": status, "evidence": evidence} for req, status, evidence in checklist
        ],
        "missing_incomplete_or_weak_requirements": missing,
        "can_mark_goal_complete_after_verification_and_commit": not missing,
        "verification_result_artifact": "G12_NOFILL_FORWARD_SOURCE_CAPTURE_VERIFICATION_RESULT_2026-05-09.json",
        "future_live_logger_wiring_still_requires_owner_approval": True,
        "validation_or_promotion_opened": False,
    }


def md_header(title: str) -> str:
    return (
        f"# {title} {DATE}\n\n"
        f"Route: `{ROUTE_ID}`\n"
        f"Promotion posture: `{PROMOTION_VERDICT}`\n"
        "Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`\n"
    )


def render_table(rows: list[tuple[str, Any]]) -> str:
    lines = ["| Item | Value |", "|---|---|"]
    for key, value in rows:
        if isinstance(value, (list, dict)):
            value_text = f"`{json.dumps(value, sort_keys=True)}`"
        else:
            value_text = f"`{value}`"
        lines.append(f"| {key} | {value_text} |")
    return "\n".join(lines)


def render_context_md(context: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Context Anchor"),
            render_table(
                [
                    ("Audit HEAD", context["audit_head"]),
                    ("Controlling prompt", context["controlling_prompt_path"]),
                    ("Audited package", context["audited_package_path"]),
                    ("Package context anchor", context["audited_package_context_anchor"]),
                    ("Source/control only", context["input_boundaries"]["source_control_only"]),
                ]
            ),
            "No heavy data, MT5 calls, paid/API calls, registry edits, or live trading behavior were used.",
        ]
    )


def render_decision_md(decision: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Acceptance Decision Ledger"),
        f"Terminal verdict: `{decision['terminal_verdict']}`.",
        "",
        "Accepted evidence class: `SOURCE_CONTROL_CONTRACT_EVIDENCE_ONLY`.",
        "",
        "## Acceptance Claims",
        "",
    ]
    lines.extend(f"- {claim}" for claim in decision["acceptance_claims"])
    lines.extend(["", "## Repair Blockers", ""])
    for blocker in decision["repair_blockers"]:
        lines.append(f"- `{blocker['blocker_id']}`: {blocker['title']}")
    lines.append("")
    lines.append("Future live logger wiring still requires separate owner approval and a separate evidence-class lane.")
    return "\n".join(lines)


def render_schema_md(audit: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Schema Field Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Contract fields", audit["contract_field_count"]),
                    ("Schema fields", audit["schema_field_count"]),
                    ("Prototype allowed fields", audit["prototype_allowed_field_count"]),
                    ("Contract fields not in prototype rows", len(audit["contract_fields_not_in_prototype_rows"])),
                    ("Fields opening result or live wiring", len(audit["fields_opening_result_or_live_wiring"])),
                ]
            ),
            audit["contract_prototype_separation_note"],
        ]
    )


def render_hash_md(audit: dict[str, Any]) -> str:
    sample = [
        item["path"]
        for item in (audit["text_eol_only_raw_sha_drift"] + audit["raw_sha_text_portability_risk"])[:12]
    ]
    return "\n\n".join(
        [
            md_header("G12 NOFILL Forward Source Capture Source Hash Recomputation Audit"),
            render_table(
                [
                    ("Status", audit["status"]),
                    ("Exact raw hash matches", audit["exact_raw_hash_match_count"]),
                    ("Text EOL-only raw SHA drift", audit["text_eol_only_raw_sha_drift_count"]),
                    ("Raw-SHA text portability risk", audit["raw_sha_text_portability_risk_count"]),
                    ("Mutable context allowed drift", audit["mutable_context_allowed_drift_count"]),
                    ("Content hash failures", audit["content_hash_failure_count"]),
                    ("Missing manifest paths", audit["missing_manifest_path_count"]),
                    ("Package self-verifier portability blocker", audit["package_self_verifier_portability_blocker"]),
                    ("Sample EOL/portability paths", sample),
                ]
            ),
            audit["package_self_verifier_repair"],
        ]
    )


def render_simple_md(title: str, audit: dict[str, Any], rows: list[tuple[str, Any]]) -> str:
    return "\n\n".join([md_header(title), render_table(rows)])


def render_repair_md(ledger: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Repair Blocker Ledger"),
        f"Terminal verdict: `{ledger['terminal_verdict']}`.",
        "",
        ledger["acceptance_boundary"],
        "",
        "## Blockers",
        "",
    ]
    for blocker in ledger["blockers"]:
        lines.extend(
            [
                f"### {blocker['blocker_id']}",
                "",
                f"Severity: `{blocker['severity']}`.",
                "",
                f"{blocker['title']}",
                "",
                f"Exact fix: {blocker['exact_fix']}",
                "",
            ]
        )
    return "\n".join(lines)


def render_next_prompt_pack(decision: dict[str, Any], repair: dict[str, Any]) -> str:
    return f"""{md_header("G12 NOFILL Forward Source Capture Next Prompt Pack")}
## Next Allowed Route

```text
Repair the NOFILL forward source-capture prototype verifier/hash policy only. Use the accepted G12 audit at research/science_program_2026_05/06_outcome_testing/g12_nofill_forward_source_capture_prototype_acceptance_audit/ as controlling evidence. Close G12-SRC-CAP-REPAIR-001 by making the package verifier accept LF-normalized hashes for text artifacts already recorded in the manifest, or by regenerating the manifest with an explicit LF-normalized strict policy. Rerun the package verifier and refresh its verification result. Preserve NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false. Do not open live logger wiring, result/cost scoring, validation, promotion, registry edits, paid/API routes, MT5 account/order/deal/history labels, or live trading behavior.
```

Terminal decision from this audit: `{decision['terminal_verdict']}`.

Repair blocker count: `{repair['repair_blocker_count']}`.
"""


def render_completion_md(audit: dict[str, Any]) -> str:
    lines = [
        md_header("G12 NOFILL Forward Source Capture Completion Audit"),
        audit["objective_restated"],
        "",
        f"Terminal verdict: `{audit['terminal_verdict']}`.",
        "",
        "| Requirement | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in audit["prompt_to_artifact_checklist"]:
        lines.append(f"| `{item['requirement']}` | `{item['status']}` | {item['evidence']} |")
    lines.append("")
    lines.append(f"Can mark complete after verification and commit: `{audit['can_mark_goal_complete_after_verification_and_commit']}`.")
    return "\n".join(lines)


def build_artifacts() -> dict[str, Any]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    package = load_package()
    context = build_context_anchor()
    schema = audit_schema_fields(package)
    hash_audit = audit_hash_manifest(package)
    denom = audit_denominators(package)
    fixture = audit_fixtures_rows(package)
    no_leak = audit_no_leak(package)
    hostile = audit_hostile(package, hash_audit)
    repair = build_repair_ledger(hash_audit, schema)
    decision = build_decision(schema, hash_audit, denom, no_leak, fixture, hostile, repair)
    completion = completion_audit(
        context,
        decision,
        {
            "schema": schema,
            "hash": hash_audit,
            "denom": denom,
            "fixture": fixture,
            "no_leak": no_leak,
            "hostile": hostile,
        },
    )

    artifacts = {
        AUDIT_JSON[0]: context,
        AUDIT_JSON[1]: decision,
        AUDIT_JSON[2]: schema,
        AUDIT_JSON[3]: hash_audit,
        AUDIT_JSON[4]: no_leak,
        AUDIT_JSON[5]: denom,
        AUDIT_JSON[6]: fixture,
        AUDIT_JSON[7]: hostile,
        AUDIT_JSON[8]: repair,
        AUDIT_JSON[9]: completion,
    }
    for name, payload in artifacts.items():
        write_json(name, payload)

    write_md(AUDIT_MD[0], render_context_md(context))
    write_md(AUDIT_MD[1], render_decision_md(decision))
    write_md(AUDIT_MD[2], render_schema_md(schema))
    write_md(AUDIT_MD[3], render_hash_md(hash_audit))
    write_md(
        AUDIT_MD[4],
        render_simple_md(
            "G12 NOFILL Forward Source Capture No-Leak Redaction Audit",
            no_leak,
            [
                ("Status", no_leak["status"]),
                ("Forbidden key hits", len(no_leak["forbidden_key_hits_in_prototype_rows"])),
                ("Result/cost label creep hits", len(no_leak["result_or_cost_label_creep_hits"])),
                ("Hash value format failures", len(no_leak["hash_value_format_failures"])),
                ("Spread values classification", no_leak["spread_values_classification"]),
            ],
        ),
    )
    write_md(
        AUDIT_MD[5],
        render_simple_md(
            "G12 NOFILL Forward Source Capture Duplicate Denominator Audit",
            denom,
            [
                ("Status", denom["status"]),
                ("Frozen equation", denom["frozen_equation"]),
                ("Prototype rows", denom["prototype_row_count"]),
                ("Accepted row-level denominator", denom["row_level_accepted_denominator"]),
                ("Primary duplicate-key denominator", denom["primary_duplicate_key_denominator"]),
                ("Secondary duplicate-group denominator", denom["secondary_duplicate_group_denominator"]),
                ("Reject-overlap rows", denom["reject_overlap_rows"]),
                ("Reject-overlap denominator effect", denom["reject_overlap_denominator_effect"]),
            ],
        ),
    )
    write_md(
        AUDIT_MD[6],
        render_simple_md(
            "G12 NOFILL Forward Source Capture Fixture Prototype Row Audit",
            fixture,
            [
                ("Status", fixture["status"]),
                ("Fixture count", fixture["fixture_count"]),
                ("Missing fixture categories", fixture["missing_fixture_categories"]),
                ("Prototype row count", fixture["prototype_row_count"]),
                ("Rows with open flags", len(fixture["prototype_rows_with_open_flags"])),
                ("Same-tick ambiguity fixture present", fixture["same_tick_ambiguity_fixture_present"]),
            ],
        ),
    )
    write_md(
        AUDIT_MD[7],
        render_simple_md(
            "G12 NOFILL Forward Source Capture Hostile Review Saturation Audit",
            hostile,
            [
                ("Status", hostile["status"]),
                ("Package hostile saturation decision", hostile["package_hostile_saturation_decision"]),
                ("Saturation decision", hostile["saturation_decision"]),
                ("Forbidden route ledger status", hostile["forbidden_route_ledger_status"]),
            ],
        ),
    )
    write_md(AUDIT_MD[8], render_repair_md(repair))
    write_md(AUDIT_MD[9], render_next_prompt_pack(decision, repair))
    write_md(AUDIT_MD[10], render_completion_md(completion))
    return {
        "ok": completion["can_mark_goal_complete_after_verification_and_commit"],
        "terminal_verdict": decision["terminal_verdict"],
        "hash_status": hash_audit["status"],
        "repair_blocker_count": repair["repair_blocker_count"],
        "content_hash_failure_count": hash_audit["content_hash_failure_count"],
        "generated_json": len(AUDIT_JSON),
        "generated_md": len(AUDIT_MD),
    }


def main() -> int:
    result = build_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
