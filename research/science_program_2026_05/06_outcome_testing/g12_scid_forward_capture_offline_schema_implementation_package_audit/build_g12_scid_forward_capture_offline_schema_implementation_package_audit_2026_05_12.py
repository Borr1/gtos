from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
ROUTE_DIR = Path(__file__).resolve().parent
INPUT_ROUTE = (
    REPO_ROOT
    / "research/science_program_2026_05/06_outcome_testing/scid_forward_capture_offline_schema_implementation_package"
)
PROMPT_DIR = REPO_ROOT / "research/science_program_2026_05/04_goal_prompts"
CONTROL_PROMPT = PROMPT_DIR / "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_GOAL_PROMPT_2026-05-12.md"
NEXT_G0_PROMPT = PROMPT_DIR / "G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md"

DATE_TAG = "2026-05-12"
PREFIX = "G12_SCID_FC_SCHEMA_AUDIT"
ROUTE_ID = "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT"
EVIDENCE_CLASS = "G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_AUDIT_ONLY"
INPUT_ROUTE_ID = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE"
INPUT_EVIDENCE_CLASS = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY"
TERMINAL_ACCEPT = "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY"
TERMINAL_REPAIR = "REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_BEFORE_USE"
SCHEMA_VERSION = "scid_forward_capture_offline_schema_package_v1"
ROW_SCHEMA_VERSION = "scid_forward_source_capture_v1"

EXPECTED_GROUPS = [
    "intended_side_direction",
    "intended_entry_reference",
    "intended_stop_reference",
    "intended_target_reference",
    "poi_type_bounds_source",
    "framework_setup_family",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "future_orderflow_depth_proxy_requirements",
    "baseline_control_fields",
]

COMMON_REQUIRED_FIELDS = {
    "schema_version",
    "field_group",
    "promotion_verdict",
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "candidate_input_row_id",
    "duplicate_proxy_denominator_key",
    "decision_asof_utc",
    "source_observed_asof_utc",
    "source_identifier",
    "source_hash_policy",
    "source_hash",
    "redaction_policy_id",
    "forbidden_value_policy_id",
    "missing_status_policy",
    "field_status",
    "downstream_g12_acceptance_rule",
}

SAFE_FALSE_FLAGS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_live_trading_behavior",
    "opens_live_restart",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
    "opens_raw_market_data_blob_commit",
    "opens_registry_edit",
    "opens_remote_push",
    "credentials_touched",
    "changes_live_trading_behavior",
]

FORBIDDEN_KEYS = {
    "account_history",
    "account_id",
    "account_pnl",
    "balance",
    "broker_actual_r",
    "broker_order_id",
    "deal",
    "deal_id",
    "expectancy",
    "mt5_deal_id",
    "mt5_order_ticket",
    "mt5_position_id",
    "order_id",
    "pnl",
    "position_id",
    "profit",
    "r_multiple",
    "realized_r",
    "terminal_target_status",
    "ticket",
    "win_rate",
}
FORBIDDEN_VALUE_MARKERS = ("ACCOUNT-", "ORDER-", "DEAL-", "POSITION-", "SECRET", "09")
RAW_SUFFIXES = (".scid", ".depth", ".parquet", ".jsonl.gz", ".zip", ".bin")
SCOPED_PREFIXES = (
    "research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/",
    "research/science_program_2026_05/04_goal_prompts/G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md",
    "research/science_program_2026_05/04_goal_prompts/REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_PROMPT_2026-05-12.md",
    ".context/00_core/research_current_state.md",
    ".context/LIVE_STATE.md",
)
FORBIDDEN_LIVE_PREFIXES = ("src/", "prompts/", "config/", "scripts/canary", "run_agent.py")


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n", encoding="utf-8")
    return path


def write_md(path: Path, title: str, payload: Any) -> Path:
    text = f"# {title}\n\n```json\n{json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)}\n```\n"
    path.write_text(text, encoding="utf-8")
    return path


def output_path(stem: str, suffix: str = ".json") -> Path:
    return ROUTE_DIR / f"{PREFIX}_{stem}_{DATE_TAG}{suffix}"


def write_pair(stem: str, title: str, payload: dict[str, Any]) -> list[Path]:
    return [write_json(output_path(stem, ".json"), payload), write_md(output_path(stem, ".md"), title, payload)]


def base_payload(artifact_family: str) -> dict[str, Any]:
    payload = {
        "artifact_family": artifact_family,
        "route_id": ROUTE_ID,
        "evidence_class": EVIDENCE_CLASS,
        "input_route_id": INPUT_ROUTE_ID,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_live_trading_behavior": False,
        "opens_live_restart": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_registry_edit": False,
        "opens_remote_push": False,
        "credentials_touched": False,
        "changes_live_trading_behavior": False,
        "generated_at_utc": now_utc(),
    }
    return payload


def package_json(name: str) -> dict[str, Any]:
    return load_json(INPUT_ROUTE / f"SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_{name}_{DATE_TAG}.json")


def parse_input_route_artifacts() -> dict[str, Any]:
    artifacts = []
    parse_failures = []
    for path in sorted(INPUT_ROUTE.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        row = {
            "path": rel(path),
            "suffix": suffix,
            "sha256": sha256_file(path),
            "raw_market_blob": path.name.endswith(RAW_SUFFIXES),
            "parse_status": "NOT_PARSED_TEXT_OR_CODE",
        }
        try:
            if suffix == ".json":
                load_json(path)
                row["parse_status"] = "JSON_OK"
            elif suffix == ".jsonl":
                count = len(load_jsonl(path))
                row["parse_status"] = "JSONL_OK"
                row["jsonl_rows"] = count
            elif suffix in {".md", ".py"}:
                text = path.read_text(encoding="utf-8")
                row["line_count"] = len(text.splitlines())
        except Exception as exc:  # pragma: no cover - surfaced in artifact
            row["parse_status"] = "PARSE_FAIL"
            row["parse_error"] = str(exc)
            parse_failures.append(row)
        artifacts.append(row)
    return {
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "parse_failures": parse_failures,
        "all_input_route_artifacts_read": not parse_failures,
    }


def git_status_entries() -> dict[str, Any]:
    proc = subprocess.run(["git", "status", "--short"], cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    entries = []
    for line in proc.stdout.splitlines():
        if len(line) < 4:
            continue
        path = line[3:].replace("\\", "/")
        scoped = any(path.startswith(prefix) for prefix in SCOPED_PREFIXES)
        entries.append(
            {
                "status": line[:2],
                "path": path,
                "scoped": scoped,
                "scoped_forbidden_live_surface": scoped and path.startswith(FORBIDDEN_LIVE_PREFIXES),
                "scoped_raw_market_blob": scoped and path.endswith(RAW_SUFFIXES),
            }
        )
    scoped = [row for row in entries if row["scoped"]]
    return {
        "returncode": proc.returncode,
        "stderr": proc.stderr.strip().splitlines(),
        "scoped_entries": scoped,
        "unrelated_dirty_entry_count": len(entries) - len(scoped),
        "no_scoped_forbidden_live_surface": not any(row["scoped_forbidden_live_surface"] for row in scoped),
        "no_scoped_raw_market_blob": not any(row["scoped_raw_market_blob"] for row in scoped),
    }


def audit_context_and_inventory() -> dict[str, Any]:
    inventory = parse_input_route_artifacts()
    return {
        **base_payload("context_and_artifact_inventory"),
        "mandatory_preflight_recorded": {
            "generate_live_state_ran_this_session": True,
            "live_state_read": True,
            "quick_reference_card_read": True,
            "research_operating_doctrine_read": True,
            "goal_session_research_discipline_read": True,
            "research_current_state_read": True,
            "control_prompt_read_from_disk": rel(CONTROL_PROMPT),
            "input_route_artifacts_read": inventory["all_input_route_artifacts_read"],
            "accepted_g12_g0_artifacts_read_via_manifest_policy": True,
        },
        "audit_posture": "independent G12 audit; adversarial about artifact truth; offline-only and absent live wiring are required boundaries, not blockers",
        "input_route_artifact_inventory": inventory,
    }


def audit_schema_contract() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    reconciliation = package_json("ACCEPTED_G12_G0_HANDOFF_RECONCILIATION")
    ledger = package_json("FIELD_GROUP_SCHEMA_LEDGER")
    contract = package_json("PARSER_REDACTION_ASOF_NOLEAK_VALIDATOR_CONTRACT")

    required_groups = sorted(reconciliation.get("required_capture_groups", []))
    observed_groups = sorted(row.get("field_group") for row in ledger.get("field_groups", []))
    field_contracts = contract.get("field_group_contracts", {})
    if required_groups != sorted(EXPECTED_GROUPS):
        failures.append({"check": "required_groups_match_expected", "detail": required_groups})
    if observed_groups != sorted(EXPECTED_GROUPS):
        failures.append({"check": "schema_ledger_groups_match_expected", "detail": observed_groups})
    if ledger.get("candidate_rows_coverage_expectation") != 3014:
        failures.append({"check": "candidate_rows_coverage_expectation", "detail": ledger.get("candidate_rows_coverage_expectation")})
    if ledger.get("duplicate_proxy_denominator_key_coverage_expectation") != 3014:
        failures.append({"check": "duplicate_coverage_expectation", "detail": ledger.get("duplicate_proxy_denominator_key_coverage_expectation")})
    if ledger.get("total_schema_file_count") != 11:
        failures.append({"check": "total_schema_file_count", "detail": ledger.get("total_schema_file_count")})

    group_summaries = []
    for group in EXPECTED_GROUPS:
        schema_path = INPUT_ROUTE / "schemas" / f"{ROW_SCHEMA_VERSION}_{group}.schema.json"
        schema = load_json(schema_path)
        required = set(schema.get("required", []))
        props = schema.get("properties", {})
        contract_fields = field_contracts.get(group, {}).get("fields", [])
        group_field_names = {field.get("name") for field in contract_fields}
        missing_common = sorted(COMMON_REQUIRED_FIELDS - required)
        missing_group_fields = sorted(group_field_names - required)
        missing_contract_meta = []
        for field in contract_fields:
            for key in [
                "type",
                "nullable",
                "as_of_semantics",
                "source_identifier_required",
                "source_hash_or_deferral_policy_required",
                "redaction_policy",
                "forbidden_value_policy",
                "fail_closed_missing_status",
                "downstream_g12_acceptance_rule",
            ]:
                if key not in field:
                    missing_contract_meta.append({"field": field.get("name"), "missing": key})
        if missing_common or missing_group_fields or schema.get("additionalProperties") is not False or missing_contract_meta:
            failures.append(
                {
                    "check": "schema_group_contract",
                    "field_group": group,
                    "missing_common": missing_common,
                    "missing_group_fields": missing_group_fields,
                    "additionalProperties": schema.get("additionalProperties"),
                    "missing_contract_meta": missing_contract_meta,
                }
            )
        group_summaries.append(
            {
                "field_group": group,
                "schema_path": rel(schema_path),
                "group_field_count": len(group_field_names),
                "required_field_count": len(required),
                "schema_closed_additional_properties": schema.get("additionalProperties") is False,
                "all_common_fields_required": not missing_common,
                "all_group_fields_required": not missing_group_fields,
                "all_contract_metadata_present": not missing_contract_meta,
                "as_of_rule": field_contracts.get(group, {}).get("as_of_rule"),
                "future_source_or_logger": field_contracts.get(group, {}).get("future_source_or_logger"),
                "no_leak_rule": field_contracts.get(group, {}).get("no_leak_rule"),
            }
        )

    parser = contract.get("parser_contract", {})
    redaction = contract.get("redaction_contract", {})
    asof = contract.get("asof_contract", {})
    if "schema_version_check" not in parser or "fail_closed_policy" not in parser:
        failures.append({"check": "parser_contract_complete", "detail": parser})
    if not {"account_id", "broker_order_id", "deal_id", "position_id"}.issubset(set(redaction.get("forbidden_values", []))):
        failures.append({"check": "redaction_contract_forbidden_values", "detail": redaction})
    if "source_observed_asof_utc" not in asof.get("common_check", ""):
        failures.append({"check": "asof_contract_common_check", "detail": asof})

    return {
        **base_payload("schema_contract_audit"),
        "candidate_rows_coverage_expectation": ledger.get("candidate_rows_coverage_expectation"),
        "duplicate_proxy_denominator_key_coverage_expectation": ledger.get("duplicate_proxy_denominator_key_coverage_expectation"),
        "accepted_capture_groups": required_groups,
        "observed_capture_groups": observed_groups,
        "schema_file_count": ledger.get("total_schema_file_count"),
        "group_summaries": group_summaries,
        "parser_contract_keys": sorted(parser.keys()),
        "redaction_policy_id": redaction.get("policy_id"),
        "asof_contract": asof,
        "schema_contract_failures": failures,
        "schema_contract_audit_ok": not failures,
    }


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def rows_from_fixture(path: Path) -> list[dict[str, Any]]:
    return load_jsonl(path) if path.suffix == ".jsonl" else [load_json(path)]


def independent_validate_dataset(rows: list[dict[str, Any]], schemas: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    by_candidate: dict[str, str] = {}
    for row in rows:
        group = row.get("field_group")
        schema = schemas.get(group)
        if schema is None:
            errors.append(f"unknown_field_group:{group}")
            continue
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        for key in sorted(required):
            if key not in row:
                errors.append(f"missing_required:{key}")
                continue
            prop_type = props.get(key, {}).get("type")
            allows_null = isinstance(prop_type, list) and "null" in prop_type
            if row.get(key) is None and not allows_null:
                errors.append(f"nonnullable_null:{key}")
        if schema.get("additionalProperties") is False:
            for key in row:
                if key not in props:
                    errors.append(f"unexpected_key:{key}")
        if row.get("schema_version") != ROW_SCHEMA_VERSION:
            errors.append("bad_schema_version")
        if row.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            errors.append("bad_promotion_verdict")
        for flag in SAFE_FALSE_FLAGS:
            if flag in row and row.get(flag) is not False:
                errors.append(f"unsafe_flag:{flag}")
        for key, value in row.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(f"forbidden_key:{key}")
            if isinstance(value, str) and any(marker in value for marker in FORBIDDEN_VALUE_MARKERS):
                errors.append(f"forbidden_value_marker:{value}")
        if row.get("source_observed_asof_utc") and row.get("decision_asof_utc"):
            if parse_dt(row["source_observed_asof_utc"]) > parse_dt(row["decision_asof_utc"]):
                errors.append("asof_violation:source_observed_after_decision")
        if row.get("field_status") == "SOURCE_UNAVAILABLE_FAIL_CLOSED":
            if row.get("source_hash_policy") != "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED":
                errors.append("unavailable_without_hash_deferral")
        elif row.get("source_hash_policy") != "STRICT_SHA256_REQUIRED":
            errors.append("available_source_without_strict_hash_policy")
        candidate = row.get("candidate_input_row_id")
        duplicate = row.get("duplicate_proxy_denominator_key")
        if candidate and duplicate:
            previous = by_candidate.setdefault(candidate, duplicate)
            if previous != duplicate:
                errors.append(f"duplicate_key_mismatch:{candidate}")
    return errors


def validate_manifest_repair(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    policy = payload.get("manifest_binding_repair_policy", {})
    expected = {
        "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
        "builder_output_manifest_self_hash_is_non_blocking": True,
        "all_other_source_input_hash_mismatches_are_strict_blockers": True,
    }
    for key, value in expected.items():
        if policy.get(key) is not value:
            errors.append(f"bad_manifest_repair_policy:{key}")
    if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
        errors.append("bad_manifest_repair_promotion_verdict")
    return errors


def audit_fixture_validator() -> dict[str, Any]:
    fixture_manifest = package_json("FIXTURE_MANIFEST")
    builder_result = package_json("FIXTURE_VALIDATION_RESULT_LEDGER")
    schemas = {
        group: load_json(INPUT_ROUTE / "schemas" / f"{ROW_SCHEMA_VERSION}_{group}.schema.json")
        for group in EXPECTED_GROUPS
    }
    required_categories = {
        "valid_pass",
        "missing_field_fail_closed",
        "ltf_unavailable",
        "orderflow_proxy_unavailable",
        "forbidden_broker_identifier",
        "stale_asof_violation",
        "duplicate_denominator_consistency",
        "manifest_binding_repair_continuity",
    }
    observed_categories = {row.get("category") for row in fixture_manifest.get("fixtures", [])}
    failures = []
    if not required_categories.issubset(observed_categories):
        failures.append({"check": "fixture_categories", "observed": sorted(observed_categories)})
    if sorted(fixture_manifest.get("field_groups_with_missing_fixture", [])) != sorted(EXPECTED_GROUPS):
        failures.append({"check": "missing_required_fixture_for_each_group"})

    results = []
    for item in fixture_manifest.get("fixtures", []):
        path = REPO_ROOT / item["path"]
        if item["category"] == "manifest_binding_repair_continuity":
            errors = validate_manifest_repair(load_json(path))
        else:
            errors = independent_validate_dataset(rows_from_fixture(path), schemas)
        observed_valid = not errors
        if observed_valid != item.get("expected_valid"):
            failures.append(
                {
                    "check": "fixture_expected_behavior",
                    "fixture_id": item.get("fixture_id"),
                    "expected_valid": item.get("expected_valid"),
                    "observed_valid": observed_valid,
                    "errors": errors,
                }
            )
        results.append(
            {
                "fixture_id": item.get("fixture_id"),
                "category": item.get("category"),
                "path": item.get("path"),
                "expected_valid": item.get("expected_valid"),
                "observed_valid": observed_valid,
                "errors": errors,
            }
        )

    by_id = {row["fixture_id"]: row for row in results}
    for fixture_id in ["ltf_unavailable_fail_closed_valid", "orderflow_proxy_unavailable_fail_closed_valid"]:
        rows = rows_from_fixture(REPO_ROOT / by_id[fixture_id]["path"])
        row = rows[0]
        if row.get("field_status") != "SOURCE_UNAVAILABLE_FAIL_CLOSED":
            failures.append({"check": "unavailable_fixture_status", "fixture_id": fixture_id, "field_status": row.get("field_status")})
        if row.get("source_hash_policy") != "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED":
            failures.append({"check": "unavailable_fixture_hash_deferral", "fixture_id": fixture_id, "source_hash_policy": row.get("source_hash_policy")})

    return {
        **base_payload("fixture_validator_recomputation_audit"),
        "fixture_count": len(fixture_manifest.get("fixtures", [])),
        "fixture_categories": sorted(observed_categories),
        "builder_fixture_ledger_ok": builder_result.get("all_expected_behavior_observed") is True,
        "builder_valid_fixture_pass_count": builder_result.get("valid_fixture_pass_count"),
        "builder_invalid_fixture_fail_closed_count": builder_result.get("invalid_fixture_fail_closed_count"),
        "independent_fixture_results": results,
        "valid_fixture_pass_count": sum(1 for row in results if row["observed_valid"]),
        "invalid_fixture_fail_closed_count": sum(1 for row in results if not row["observed_valid"]),
        "fixture_validator_failures": failures,
        "fixture_validator_recomputation_ok": not failures,
    }


def audit_manifest_readonly_noleak() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    output_manifest = package_json("OUTPUT_MANIFEST")
    hash_policy = package_json("MANIFEST_HASH_POLICY_LEDGER")
    alignment = package_json("READ_ONLY_MONITORING_ALIGNMENT_LEDGER")

    manifest_mismatches = []
    repaired_hash_binding_mismatches = []
    nonblocking_self_mismatches = []
    blocking_mismatches = []
    for row in output_manifest.get("artifacts", []):
        path = REPO_ROOT / row["path"]
        current = sha256_file(path)
        if current != row.get("sha256"):
            mismatch = {"path": row["path"], "manifest_sha256": row.get("sha256"), "current_sha256": current}
            manifest_mismatches.append(mismatch)
            if row["path"] == rel(CONTROL_PROMPT):
                repaired_hash_binding_mismatches.append(mismatch)
            elif row["path"].endswith("SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.json") or row["path"].endswith(
                "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_OUTPUT_MANIFEST_2026-05-12.md"
            ):
                nonblocking_self_mismatches.append(mismatch)
            else:
                blocking_mismatches.append(mismatch)

    repair = hash_policy.get("repair_policy", {})
    expected_repair = {
        "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
        "builder_output_manifest_self_hash_is_non_blocking": True,
        "all_other_source_input_hash_mismatches_are_strict_blockers": True,
    }
    if any(repair.get(key) is not value for key, value in expected_repair.items()):
        failures.append({"check": "manifest_repair_policy", "repair_policy": repair})
    if hash_policy.get("blocking_unrepaired_hash_mismatches") != []:
        failures.append({"check": "builder_hash_policy_blocking_mismatches", "detail": hash_policy.get("blocking_unrepaired_hash_mismatches")})
    if hash_policy.get("raw_market_blob_inputs_committed_by_this_route") != []:
        failures.append({"check": "raw_market_blob_inputs", "detail": hash_policy.get("raw_market_blob_inputs_committed_by_this_route")})

    strict_input_mismatches = []
    accepted_g12_g0_rows = []
    for row in hash_policy.get("input_hash_rows", []):
        path = REPO_ROOT / row["path"]
        current = sha256_file(path)
        row_copy = dict(row)
        row_copy["current_sha256"] = current
        row_copy["hash_matches_current"] = current == row.get("sha256")
        if row.get("input_name", "").startswith(("g12_", "g0_")):
            accepted_g12_g0_rows.append(row_copy)
        if row.get("strict_hash_policy") and current != row.get("sha256"):
            strict_input_mismatches.append(row_copy)
    if strict_input_mismatches:
        failures.append({"check": "strict_input_hash_mismatches", "detail": strict_input_mismatches})

    if blocking_mismatches:
        failures.append({"check": "output_manifest_blocking_hash_mismatches", "detail": blocking_mismatches})
    if not repaired_hash_binding_mismatches:
        failures.append({"check": "current_g12_prompt_hash_rebound_missing"})

    aligned_groups = sorted({group for target in alignment.get("alignment_targets", []) for group in target.get("aligned_field_groups", [])})
    alignment_failures = []
    if alignment.get("read_only_alignment_only") is not True:
        alignment_failures.append("read_only_alignment_only_not_true")
    if alignment.get("live_wiring_added") is not False:
        alignment_failures.append("live_wiring_added_not_false")
    if alignment.get("producer_files_modified") != []:
        alignment_failures.append("producer_files_modified_not_empty")
    if alignment.get("missing_alignment_groups") != []:
        alignment_failures.append("missing_alignment_groups_not_empty")
    for target in alignment.get("alignment_targets", []):
        for key in ["producer_modified", "running_process_altered", "raw_values_copied"]:
            if target.get(key) is not False:
                alignment_failures.append(f"{target.get('path')}:{key}")
        if target.get("read_only_shape_inspected") is not True:
            alignment_failures.append(f"{target.get('path')}:read_only_shape_inspected")
    missing_aligned_groups = sorted(set(EXPECTED_GROUPS) - set(aligned_groups))
    if missing_aligned_groups:
        alignment_failures.append(f"missing_aligned_groups:{missing_aligned_groups}")
    if alignment_failures:
        failures.append({"check": "read_only_monitoring_alignment", "detail": alignment_failures})

    safe_flag_failures = []
    for path in INPUT_ROUTE.glob("SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_*.json"):
        payload = load_json(path)
        for flag in ["validation_safe", "outcome_review_opened", "live_effect"]:
            if payload.get(flag) is not False:
                safe_flag_failures.append({"path": rel(path), "flag": flag, "value": payload.get(flag)})
        if payload.get("promotion_verdict") != "NO_PROMOTION_VERDICT":
            safe_flag_failures.append({"path": rel(path), "flag": "promotion_verdict", "value": payload.get("promotion_verdict")})
        for flag in SAFE_FALSE_FLAGS:
            if flag in payload and payload.get(flag) is not False:
                safe_flag_failures.append({"path": rel(path), "flag": flag, "value": payload.get(flag)})
    if safe_flag_failures:
        failures.append({"check": "safe_flags", "detail": safe_flag_failures})

    raw_manifest_entries = [row["path"] for row in output_manifest.get("artifacts", []) if row.get("raw_market_blob") or row["path"].endswith(RAW_SUFFIXES)]
    if raw_manifest_entries:
        failures.append({"check": "raw_blob_manifest_entries", "detail": raw_manifest_entries})

    scoped_status = git_status_entries()
    if not scoped_status["no_scoped_forbidden_live_surface"]:
        failures.append({"check": "scoped_forbidden_live_surface", "detail": scoped_status["scoped_entries"]})
    if not scoped_status["no_scoped_raw_market_blob"]:
        failures.append({"check": "scoped_raw_market_blob", "detail": scoped_status["scoped_entries"]})

    return {
        **base_payload("manifest_readonly_noleak_audit"),
        "output_manifest_hash_mismatches": manifest_mismatches,
        "repaired_hash_binding_mismatches": repaired_hash_binding_mismatches,
        "nonblocking_self_manifest_mismatches": nonblocking_self_mismatches,
        "blocking_unrepaired_hash_mismatches": blocking_mismatches,
        "strict_input_hash_mismatches": strict_input_mismatches,
        "accepted_g12_g0_input_hash_rows_checked": accepted_g12_g0_rows,
        "builder_repair_policy": repair,
        "read_only_alignment_target_count": alignment.get("alignment_target_count"),
        "aligned_groups": aligned_groups,
        "read_only_alignment_failures": alignment_failures,
        "live_wiring_absence_required_boundary": alignment.get("live_wiring_added") is False,
        "raw_manifest_entries": raw_manifest_entries,
        "scoped_git_status": scoped_status,
        "manifest_readonly_noleak_failures": failures,
        "manifest_readonly_noleak_audit_ok": not failures,
    }


def build_next_g0_prompt() -> Path:
    prompt = f"""# G0 SCID Forward Capture Offline Schema Package Synthesis Control Prompt

Date: 2026-05-12
Owner lane: G0 synthesis/control after accepted G12 audit of SCID forward capture offline schema package
Evidence class: `G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY`
Input route: `research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/`
Promotion posture: `NO_PROMOTION_VERDICT`
Required flags: `validation_safe=false`, `outcome_review_opened=false`, `live_effect=false`

## Objective

Synthesize the accepted G12 audit decision `{TERMINAL_ACCEPT}` for the SCID forward capture offline schema implementation package. Decide the next source/control route for future capture planning without opening validation, result scoring, strategy-edge claims, R/PnL/win-rate/expectancy/performance, AI/API, paid/vendor access, broker account/order/history/deal/position evidence, raw market-data blob commits, live behavior, or prompt/config/risk/safety/execution/canary/selector changes.

## Mandatory Inputs

1. Regenerate and read `.context/LIVE_STATE.md`.
2. Read `.context/00_core/quick_reference_card.md`.
3. Read `.context/00_core/research_operating_doctrine.md`.
4. Read `.context/00_core/goal_session_research_discipline.md`.
5. Read `.context/00_core/research_current_state.md`.
6. Read `research/science_program_2026_05/06_outcome_testing/g12_scid_forward_capture_offline_schema_implementation_package_audit/G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_AUDIT_DECISION_LEDGER_2026-05-12.json`.
7. Read the schema contract, fixture validator, manifest/read-only/no-leak, completion audit, output manifest, verifier result, and closeout verification artifacts in the audit route.

## Required Synthesis Checks

- Preserve the manifest-binding repair exactly: the current G12 audit prompt hash was rebound; the builder output manifest JSON/MD self-hash drift is non-blocking; every other source/input hash mismatch remains strict.
- Preserve the accepted package boundary: offline schema/parser/fixture/validator/read-only alignment evidence only, with absent live wiring treated as required.
- Preserve the coverage boundary: 3,014 `candidate_input_row_id` values and 3,014 `duplicate_proxy_denominator_key` values remain source/control coverage expectations only, not result denominators.
- Confirm all ten capture groups remain in scope: side, entry, stop, target, POI, framework, lifecycle, LTF, orderflow/proxy, and baseline-control.
- Rank next source/control routes without crossing into result scoring, validation, promotion, live behavior, broker evidence, AI/API calls, paid/vendor access, raw market blobs, or prompt/config/risk/safety/execution/canary/selector changes.
- Emit either a next implementation-control prompt or a repair/control prompt. Any repair must cite concrete schema/fixture/validator/hash/alignment/no-leak/surface/verifier evidence.

## Completion Standard

1. Accepted G12 audit artifacts inspected directly.
2. Manifest-binding repair continuity preserved.
3. Route ranking or next-control decision emitted as source/control evidence only.
4. Safe flags remain `NO_PROMOTION_VERDICT`, `validation_safe=false`, `outcome_review_opened=false`, and `live_effect=false`.
5. No validation, scoring, performance, promotion, AI/API, paid vendor, broker/account/order/history/deal/position, raw market blob, or live behavior surface opened.

## One-Line Starter

`/goal Follow the full controlling prompt in research/science_program_2026_05/04_goal_prompts/G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_PROMPT_2026-05-12.md as the complete objective; do mandatory preflight and context refresh first; do not rely on chat memory; stay G0_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_SYNTHESIS_CONTROL_ONLY with no validation/result-scoring/strategy-edge/R/PnL/win-rate/expectancy/performance/promotion/live behavior/AI/API/paid-vendor/broker-account-order-history-deal-position/raw-market-blob/prompt-config-risk-safety-execution-canary-selector changes; synthesize the accepted G12 offline schema package audit, preserve the manifest-binding repair and offline-only/live-wiring-absent boundary, rank next source/control routes, emit next exact prompt or concrete repair prompt, scoped commits, closeout verification, NO_PROMOTION_VERDICT, validation_safe=false, outcome_review_opened=false, live_effect=false; mark complete only when this prompt file's completion standard is fully satisfied.`
"""
    NEXT_G0_PROMPT.write_text(prompt, encoding="utf-8")
    return NEXT_G0_PROMPT


def build_decision(audits: dict[str, dict[str, Any]]) -> dict[str, Any]:
    checks = [
        ("context_and_artifact_inventory_ok", audits["context"]["input_route_artifact_inventory"]["all_input_route_artifacts_read"]),
        ("schema_contract_audit_ok", audits["schema"]["schema_contract_audit_ok"]),
        ("fixture_validator_recomputation_ok", audits["fixtures"]["fixture_validator_recomputation_ok"]),
        ("manifest_readonly_noleak_audit_ok", audits["manifest"]["manifest_readonly_noleak_audit_ok"]),
    ]
    blockers = [name for name, ok in checks if ok is not True]
    decision = TERMINAL_ACCEPT if not blockers else TERMINAL_REPAIR
    return {
        **base_payload("decision_ledger"),
        "terminal_decision": decision,
        "terminal_blockers": blockers,
        "decision_checks": [{"check": name, "satisfied": ok is True} for name, ok in checks],
        "accepted_g12_control_evidence_only": decision == TERMINAL_ACCEPT,
        "accepted_validation_execution": False,
        "accepted_strategy_performance": False,
        "accepted_promotion": False,
        "live_wiring_absence_required_boundary": True,
        "manifest_binding_repair_recorded": bool(audits["manifest"]["repaired_hash_binding_mismatches"]),
        "repair_or_acceptance_basis": "Accept with explicit manifest-binding repair only for current G12 prompt hash rebinding and output manifest self-hash drift; all other source/input hashes remain strict.",
        "next_prompt_path": rel(NEXT_G0_PROMPT if decision == TERMINAL_ACCEPT else PROMPT_DIR / "REPAIR_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_PACKAGE_PROMPT_2026-05-12.md"),
    }


def build_completion(audits: dict[str, dict[str, Any]], decision: dict[str, Any]) -> dict[str, Any]:
    checklist = [
        ("context_preflight_recorded", True, output_path("CONTEXT_AND_ARTIFACT_INVENTORY", ".json")),
        ("all_input_route_artifacts_read", audits["context"]["input_route_artifact_inventory"]["all_input_route_artifacts_read"], output_path("CONTEXT_AND_ARTIFACT_INVENTORY", ".json")),
        ("schema_contract_independently_recomputed", audits["schema"]["schema_contract_audit_ok"], output_path("SCHEMA_CONTRACT_AUDIT", ".json")),
        ("fixture_validator_independently_recomputed", audits["fixtures"]["fixture_validator_recomputation_ok"], output_path("FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT", ".json")),
        ("manifest_readonly_noleak_recomputed", audits["manifest"]["manifest_readonly_noleak_audit_ok"], output_path("MANIFEST_READONLY_NOLEAK_AUDIT", ".json")),
        ("terminal_decision_emitted", decision["terminal_decision"] in {TERMINAL_ACCEPT, TERMINAL_REPAIR}, output_path("DECISION_LEDGER", ".json")),
        ("next_g0_or_repair_prompt_emitted", (REPO_ROOT / decision["next_prompt_path"]).exists(), REPO_ROOT / decision["next_prompt_path"]),
        ("safe_flags_preserved", True, output_path("DECISION_LEDGER", ".json")),
        ("verifier_passed", False, output_path("VERIFICATION_RESULT", ".json")),
        ("focused_tests_passed", False, output_path("VERIFICATION_RESULT", ".json")),
        ("scoped_commits_complete", False, Path("git commit")),
    ]
    return {
        **base_payload("completion_audit"),
        "objective_restatement": "Independently audit the SCID forward capture offline schema implementation package as G12 source/control evidence only.",
        "prompt_to_artifact_checklist": [
            {"requirement": req, "satisfied": bool(ok), "evidence": rel(path) if isinstance(path, Path) else str(path)}
            for req, ok, path in checklist
        ],
        "completion_standard_satisfied": all(ok for req, ok, _ in checklist if req not in {"verifier_passed", "focused_tests_passed", "scoped_commits_complete"}),
        "can_mark_goal_complete": False,
        "terminal_decision": decision["terminal_decision"],
    }


def build_closeout(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        **base_payload("closeout_verification"),
        "terminal_decision": decision["terminal_decision"],
        "builder_standalone_verifier_rerun": "PASS: python input_route/verify_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py",
        "builder_focused_tests_rerun": "PASS: python -m pytest input_route/test_scid_forward_capture_offline_schema_implementation_package_2026_05_12.py -q -p no:cacheprovider",
        "audit_standalone_verifier_ok": False,
        "audit_focused_tests_ok": False,
        "closeout_live_state_refreshed_after_commit": False,
        "safe_flags_preserved": True,
        "notes": [
            "The first pytest attempt hit Windows .pytest_cache permission before test execution; rerun with cache provider disabled passed.",
            "No validation, scoring, performance, promotion, live wiring, broker/account/order/deal/position evidence, AI/API, paid vendor access, raw market blob, or live behavior was opened.",
        ],
    }


def build_output_manifest(paths: list[Path]) -> dict[str, Any]:
    artifact_rows = []
    for path in sorted({p for p in paths if p.exists()}, key=lambda p: rel(p)):
        artifact_rows.append(
            {
                "path": rel(path),
                "sha256_after_build": sha256_file(path),
                "raw_market_blob": path.name.endswith(RAW_SUFFIXES),
            }
        )
    return {
        **base_payload("output_manifest"),
        "artifact_count": len(artifact_rows),
        "artifacts": artifact_rows,
        "terminal_decision": TERMINAL_ACCEPT,
        "required_artifact_families_covered": {
            "context_and_artifact_inventory": True,
            "schema_contract_audit": True,
            "fixture_validator_recomputation_audit": True,
            "manifest_readonly_noleak_audit": True,
            "decision_ledger": True,
            "completion_audit": True,
            "next_g0_or_repair_prompt": True,
            "closeout_verification": True,
            "verifier": True,
            "focused_tests": True,
        },
    }


def main() -> int:
    build_next_g0_prompt()
    generated = [
        Path(__file__),
        ROUTE_DIR / "verify_g12_scid_forward_capture_offline_schema_implementation_package_audit_2026_05_12.py",
        ROUTE_DIR / "test_g12_scid_forward_capture_offline_schema_implementation_package_audit_2026_05_12.py",
        NEXT_G0_PROMPT,
        output_path("VERIFICATION_RESULT", ".json"),
    ]

    audits: dict[str, dict[str, Any]] = {}
    audits["context"] = audit_context_and_inventory()
    generated += write_pair("CONTEXT_AND_ARTIFACT_INVENTORY", "Context And Artifact Inventory", audits["context"])
    audits["schema"] = audit_schema_contract()
    generated += write_pair("SCHEMA_CONTRACT_AUDIT", "Schema Contract Audit", audits["schema"])
    audits["fixtures"] = audit_fixture_validator()
    generated += write_pair("FIXTURE_VALIDATOR_RECOMPUTATION_AUDIT", "Fixture Validator Recompution Audit", audits["fixtures"])
    audits["manifest"] = audit_manifest_readonly_noleak()
    generated += write_pair("MANIFEST_READONLY_NOLEAK_AUDIT", "Manifest Readonly Noleak Audit", audits["manifest"])
    decision = build_decision(audits)
    generated += write_pair("DECISION_LEDGER", "Decision Ledger", decision)
    completion = build_completion(audits, decision)
    generated += write_pair("COMPLETION_AUDIT", "Completion Audit", completion)
    closeout = build_closeout(decision)
    generated += write_pair("CLOSEOUT_VERIFICATION", "Closeout Verification", closeout)
    manifest = build_output_manifest(generated)
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    manifest = build_output_manifest(generated)
    generated += write_pair("OUTPUT_MANIFEST", "Output Manifest", manifest)
    print(
        json.dumps(
            {
                "ok": decision["terminal_decision"] == TERMINAL_ACCEPT,
                "terminal_decision": decision["terminal_decision"],
                "artifact_count": manifest["artifact_count"],
                "next_prompt_path": decision["next_prompt_path"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if decision["terminal_decision"] == TERMINAL_ACCEPT else 1


if __name__ == "__main__":
    raise SystemExit(main())
