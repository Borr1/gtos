"""Synthetic-only runtime-facing harness for the accepted SCID capture schema.

This module intentionally stays route-local. It imports no production GTOS
runtime code, opens no broker/API surfaces, and validates only synthetic rows
against the accepted offline schema package artifacts.
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROUTE_ID = "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY"
EVIDENCE_CLASS = "SCID_CAPTURE_SCHEMA_TO_RUNTIME_TEST_HARNESS_SYNTHETIC_ONLY_ONLY"
ARTIFACT_PREFIX = "SCID_CAPTURE_RUNTIME_HARNESS_SYNTHETIC_ONLY"

SCHEMA_VERSION = "scid_forward_source_capture_v1"
SCHEMA_ROW_ROUTE_ID = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE"
SCHEMA_ROW_EVIDENCE_CLASS = "SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_ONLY"

REPO_ROOT = Path(__file__).resolve().parents[4]
SCIENCE_ROOT = REPO_ROOT / "research" / "science_program_2026_05"
OUTCOME_ROOT = SCIENCE_ROOT / "06_outcome_testing"
ACCEPTED_SCHEMA_ROUTE = OUTCOME_ROOT / "scid_forward_capture_offline_schema_implementation_package"
ACCEPTED_SCHEMA_DIR = ACCEPTED_SCHEMA_ROUTE / "schemas"
G12_AUDIT_ROUTE = OUTCOME_ROOT / "g12_scid_forward_capture_offline_schema_implementation_package_audit"
ROUTE_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = ROUTE_DIR / "fixtures"

CAPTURE_GROUPS = [
    "baseline_control_fields",
    "framework_setup_family",
    "future_orderflow_depth_proxy_requirements",
    "intended_entry_reference",
    "intended_side_direction",
    "intended_stop_reference",
    "intended_target_reference",
    "lifecycle_fill_cancel_expiry_source_status",
    "lower_timeframe_asof_path_availability",
    "poi_type_bounds_source",
]

MARKET_CONTEXT_UNAVAILABLE_GROUPS = {
    "future_orderflow_depth_proxy_requirements",
    "lower_timeframe_asof_path_availability",
}

SAFE_FLAG_FIELDS = [
    "validation_safe",
    "outcome_review_opened",
    "live_effect",
    "opens_validation",
    "opens_result_scoring",
    "opens_strategy_edge_claims",
    "opens_broker_account_order_history_deal_position_evidence",
    "opens_ai_api",
    "opens_paid_or_vendor_access",
    "opens_live_restart",
    "opens_live_trading_behavior",
    "opens_raw_market_data_blob_commit",
    "opens_prompt_config_risk_safety_execution_canary_selector_edit",
]

FORBIDDEN_KEY_EXACT = {
    "account_id",
    "account_history",
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

FORBIDDEN_KEY_FRAGMENTS = {
    "account_id",
    "broker_order",
    "deal_id",
    "mt5_deal",
    "mt5_order",
    "mt5_position",
    "order_ticket",
    "position_id",
    "realized_r",
    "terminal_target",
    "win_rate",
}

FORBIDDEN_VALUE_MARKERS = [
    "ACCOUNT-",
    "DEAL-",
    "ORDER-",
    "POSITION-",
    "SECRET",
    "WIN_RATE",
]

FIXED_DECISION_ASOF = "2026-05-12T00:00:00Z"
FIXED_SOURCE_ASOF = "2026-05-11T23:59:00Z"
FIXED_STALE_SOURCE_ASOF = "2026-05-12T00:01:00Z"


@dataclass(frozen=True)
class FixtureCase:
    fixture_id: str
    category: str
    field_group: str | None
    expected_valid: bool
    rows: list[dict[str, Any]]
    manifest_payload: dict[str, Any] | None = None
    fail_closed_semantics: bool = False
    inapplicable_reason: str | None = None

    def to_manifest_row(self, relative_path: str) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "category": self.category,
            "field_group": self.field_group,
            "expected_valid": self.expected_valid,
            "row_count": len(self.rows),
            "fixture_path": relative_path,
            "fail_closed_semantics": self.fail_closed_semantics,
            "inapplicable_reason": self.inapplicable_reason,
        }


@dataclass(frozen=True)
class FixtureOutcome:
    fixture_id: str
    category: str
    field_group: str | None
    expected_valid: bool
    observed_valid: bool
    pass_status: bool
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "category": self.category,
            "field_group": self.field_group,
            "expected_valid": self.expected_valid,
            "observed_valid": self.observed_valid,
            "pass_status": self.pass_status,
            "errors": self.errors,
        }


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def parse_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_accepted_schemas() -> dict[str, dict[str, Any]]:
    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(ACCEPTED_SCHEMA_DIR.glob("scid_forward_source_capture_v1_*.schema.json")):
        if path.name.endswith("_master.schema.json"):
            schemas["__master__"] = read_json(path)
            continue
        schema = read_json(path)
        field_group = schema.get("x_scid_contract", {}).get("field_group")
        if not field_group:
            raise ValueError(f"schema missing x_scid_contract.field_group: {path}")
        schemas[field_group] = schema
    return schemas


def group_schema(schemas: dict[str, dict[str, Any]], field_group: str) -> dict[str, Any]:
    if field_group not in schemas:
        raise KeyError(f"unknown field group: {field_group}")
    return schemas[field_group]


def row_common(field_group: str, variant: str) -> dict[str, Any]:
    candidate_id = f"SYNTHETIC::{field_group}::{variant}"
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": SCHEMA_ROW_ROUTE_ID,
        "evidence_class": SCHEMA_ROW_EVIDENCE_CLASS,
        "promotion_verdict": "NO_PROMOTION_VERDICT",
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
        "opens_validation": False,
        "opens_result_scoring": False,
        "opens_strategy_edge_claims": False,
        "opens_broker_account_order_history_deal_position_evidence": False,
        "opens_ai_api": False,
        "opens_paid_or_vendor_access": False,
        "opens_live_restart": False,
        "opens_live_trading_behavior": False,
        "opens_raw_market_data_blob_commit": False,
        "opens_prompt_config_risk_safety_execution_canary_selector_edit": False,
        "candidate_input_row_id": candidate_id,
        "duplicate_proxy_denominator_key": sha256_text(candidate_id)[:32],
        "field_group": field_group,
        "decision_asof_utc": FIXED_DECISION_ASOF,
        "source_observed_asof_utc": FIXED_SOURCE_ASOF,
        "source_identifier": f"synthetic://runtime-harness/{field_group}/{variant}",
        "source_hash": sha256_text(f"{field_group}:{variant}:source"),
        "source_hash_policy": "STRICT_SHA256_REQUIRED",
        "redaction_policy_id": "SCID_FORWARD_CAPTURE_NO_BROKER_ACCOUNT_ORDER_DEAL_POSITION_IDS_V1",
        "forbidden_value_policy_id": "SCID_FORWARD_CAPTURE_FORBIDDEN_SURFACE_FAIL_CLOSED_V1",
        "missing_status_policy": "FAIL_CLOSED_MISSING_SOURCE_FIELD",
        "field_status": "CAPTURED_SOURCE_SAFE",
        "downstream_g12_acceptance_rule": "G12_ACCEPTED_OFFLINE_SCHEMA_PACKAGE_WITH_MANIFEST_BINDING_REPAIR_ONLY",
    }


def group_values(field_group: str, variant: str) -> dict[str, Any]:
    is_alt = variant.endswith("variant")
    if field_group == "intended_side_direction":
        return {
            "strategy_side_enum_LONG_SHORT_NEUTRAL_NO_STRATEGY": "SHORT" if is_alt else "LONG",
            "side_source_component": "synthetic_decision_packet_logger",
            "side_source_rule_or_model_hash": sha256_text(f"{variant}:side-rule"),
            "side_emission_reason_code": "synthetic_pre_decision_side_emitted",
        }
    if field_group == "intended_entry_reference":
        return {
            "entry_reference_type_market_limit_zone_midpoint_other": "limit" if is_alt else "market",
            "entry_reference_price": 2345.25 if is_alt else 2344.50,
            "entry_reference_time_utc": FIXED_SOURCE_ASOF,
            "entry_source_timeframe": "M15",
            "entry_source_bar_hash_or_mso_snapshot_hash": sha256_text(f"{variant}:entry-snapshot"),
        }
    if field_group == "intended_stop_reference":
        return {
            "stop_reference_price": 2338.75 if is_alt else 2339.10,
            "stop_reference_type": "synthetic_structure_low" if is_alt else "synthetic_order_block_bound",
            "stop_buffer_rule_id": "synthetic_stop_buffer_rule_v1",
            "stop_source_structure_id": f"synthetic_stop_structure_{variant}",
            "stop_source_snapshot_hash": sha256_text(f"{variant}:stop-snapshot"),
        }
    if field_group == "intended_target_reference":
        return {
            "target_reference_price": 2360.25 if is_alt else 2358.40,
            "target_reference_type": "synthetic_rr_projection" if is_alt else "synthetic_liquidity_reference",
            "target_rule_id": "synthetic_target_rule_v1",
            "risk_reward_reference": 1.75 if is_alt else 1.50,
            "target_source_snapshot_hash": sha256_text(f"{variant}:target-snapshot"),
        }
    if field_group == "poi_type_bounds_source":
        return {
            "poi_type_enum_ob_fvg_breaker_swing_other_none": "fvg" if is_alt else "ob",
            "poi_lower_bound": 2341.10 if is_alt else 2340.25,
            "poi_upper_bound": 2343.00 if is_alt else 2342.50,
            "poi_source_timeframe": "H1",
            "poi_source_bar_ids": [f"synthetic_bar_{variant}_1", f"synthetic_bar_{variant}_2"],
            "mso_snapshot_hash": sha256_text(f"{variant}:mso"),
            "poi_detection_rule_version": "synthetic_poi_rule_v1",
        }
    if field_group == "framework_setup_family":
        return {
            "frameworks_evaluated": ["ob_retest", "fvg_fill", "breaker_re_entry"]
            if is_alt
            else ["ob_retest", "breaker_re_entry"],
            "framework_qualified_flags": {
                "ob_retest": not is_alt,
                "fvg_fill": bool(is_alt),
                "breaker_re_entry": False,
            },
            "selected_framework_or_none": "fvg_fill" if is_alt else "ob_retest",
            "setup_family": "synthetic_multi_framework_variant" if is_alt else "synthetic_ob_retest",
            "framework_tiebreak_rule_id": "synthetic_framework_tiebreak_v1",
            "framework_source_snapshot_hash": sha256_text(f"{variant}:framework-snapshot"),
        }
    if field_group == "lifecycle_fill_cancel_expiry_source_status":
        return {
            "pending_intent_id": f"synthetic_intent_{variant}",
            "source_event_type_created_updated_expired_cancelled_replaced_no_order": "no_order" if is_alt else "created",
            "source_event_utc": FIXED_SOURCE_ASOF,
            "source_event_clock_basis": "synthetic_decision_clock",
            "intent_state_before": None if is_alt else "synthetic_empty",
            "intent_state_after": "synthetic_no_order" if is_alt else "synthetic_pending_created",
            "redacted_order_bridge_hash_optional": None,
        }
    if field_group == "lower_timeframe_asof_path_availability":
        return {
            "ltf_timeframes_available": ["M1", "M5"] if is_alt else ["M5"],
            "ltf_source_file_pointer_or_cache_id": f"synthetic_ltf_cache_{variant}",
            "ltf_source_hash": sha256_text(f"{variant}:ltf-source"),
            "decision_minus_window_start_utc": "2026-05-11T23:45:00Z",
            "bars_present_by_timeframe": {"M1": 15, "M5": 3} if is_alt else {"M5": 3},
            "asof_path_descriptor_version": "synthetic_ltf_asof_descriptor_v1",
            "ltf_availability_status": "AVAILABLE",
        }
    if field_group == "future_orderflow_depth_proxy_requirements":
        return {
            "proxy_instrument": "SYNTH_DEPTH_PROXY" if is_alt else "SYNTH_SCID_PROXY",
            "proxy_contract_month": "2026-06" if is_alt else None,
            "source_family_scid_depth_mbo_mbp_other": "depth" if is_alt else "scid",
            "source_file_pointer_or_vendor_cache_id": f"synthetic_orderflow_cache_{variant}",
            "proxy_mapping_version": "synthetic_proxy_map_v1",
            "publication_or_capture_asof_utc": FIXED_SOURCE_ASOF,
            "derived_feature_schema_version": "synthetic_orderflow_features_v1",
            "orderflow_proxy_availability_status": "AVAILABLE",
        }
    if field_group == "baseline_control_fields":
        return {
            "partition_assignment": "synthetic_holdout" if is_alt else "synthetic_train_partition",
            "symbol": "SYNTH_XAUUSD" if is_alt else "SYNTH_USDJPY",
            "session_bucket": "synthetic_ny" if is_alt else "synthetic_london",
            "time_of_day_bucket": "synthetic_1300_1315" if is_alt else "synthetic_0700_0715",
            "baseline_family_session_only_volatility_only_random_proxy_matched": "volatility_only" if is_alt else "session_only",
            "baseline_assignment_seed": "synthetic_seed_alt" if is_alt else "synthetic_seed_base",
            "baseline_duplicate_policy_id": "synthetic_duplicate_policy_v1",
        }
    raise KeyError(field_group)


def positive_row(field_group: str, variant: str = "base") -> dict[str, Any]:
    row = row_common(field_group, variant)
    row.update(group_values(field_group, variant))
    return row


def unavailable_row(field_group: str, variant: str = "unavailable") -> dict[str, Any]:
    row = positive_row(field_group, variant="base")
    row["candidate_input_row_id"] = f"SYNTHETIC::{field_group}::{variant}"
    row["duplicate_proxy_denominator_key"] = sha256_text(row["candidate_input_row_id"])[:32]
    row["source_identifier"] = f"synthetic://runtime-harness/{field_group}/{variant}"
    row["source_hash"] = None
    row["source_hash_policy"] = "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED"
    row["missing_status_policy"] = "PROSPECTIVE_CAPTURE_REQUIRED"
    row["field_status"] = "SOURCE_UNAVAILABLE_FAIL_CLOSED"
    if field_group == "lower_timeframe_asof_path_availability":
        row["ltf_source_file_pointer_or_cache_id"] = None
        row["ltf_source_hash"] = None
        row["ltf_timeframes_available"] = []
        row["bars_present_by_timeframe"] = {}
        row["ltf_availability_status"] = "UNAVAILABLE_FAIL_CLOSED"
    if field_group == "future_orderflow_depth_proxy_requirements":
        row["proxy_instrument"] = None
        row["proxy_contract_month"] = None
        row["source_family_scid_depth_mbo_mbp_other"] = "unavailable"
        row["source_file_pointer_or_vendor_cache_id"] = None
        row["proxy_mapping_version"] = None
        row["derived_feature_schema_version"] = None
        row["orderflow_proxy_availability_status"] = "UNAVAILABLE_FAIL_CLOSED"
    return row


def first_group_specific_required(schema: dict[str, Any]) -> str:
    common = set(row_common(schema["x_scid_contract"]["field_group"], "tmp"))
    for key in schema.get("required", []):
        if key not in common:
            return key
    raise ValueError(f"no group-specific required field in {schema['title']}")


def first_enum_field(schema: dict[str, Any]) -> str | None:
    common_keys = set(row_common(schema["x_scid_contract"]["field_group"], "tmp"))
    for key, spec in schema.get("properties", {}).items():
        if key in common_keys:
            continue
        if "enum" in spec:
            return key
    return None


def clone_mutated(row: dict[str, Any], **updates: Any) -> dict[str, Any]:
    mutated = copy.deepcopy(row)
    mutated.update(updates)
    return mutated


def build_manifest_repair_payload(valid: bool) -> dict[str, Any]:
    policy = {
        "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash": True,
        "output_manifest_self_hash_drift_is_nonblocking": True,
        "all_other_source_and_input_hash_mismatches_are_strict_blockers": True,
        "safe_flags_preserved": True,
    }
    if not valid:
        policy["all_other_source_and_input_hash_mismatches_are_strict_blockers"] = False
    return {
        "route_id": ROUTE_ID,
        "fixture_id": "manifest_repair_valid" if valid else "manifest_repair_invalid",
        "safe_flags": {flag: False for flag in SAFE_FLAG_FIELDS},
        "accepted_repair_scope": policy,
        "accepted_g12_terminal_decision": "ACCEPT_AS_G12_SCID_FORWARD_CAPTURE_OFFLINE_SCHEMA_IMPLEMENTATION_PACKAGE_CONTROL_EVIDENCE_ONLY",
        "candidate_rows_verified": 3014,
        "capture_group_count_verified": 10,
    }


def manifest_repair_valid(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if payload.get("route_id") != ROUTE_ID:
        errors.append("manifest_repair_route_id_mismatch")
    safe_flags = payload.get("safe_flags", {})
    for flag in SAFE_FLAG_FIELDS:
        if safe_flags.get(flag) is not False:
            errors.append(f"manifest_repair_unsafe_flag:{flag}")
    policy = payload.get("accepted_repair_scope", {})
    required_policy = {
        "current_g12_prompt_hash_supersedes_stale_pre_hardening_hash",
        "output_manifest_self_hash_drift_is_nonblocking",
        "all_other_source_and_input_hash_mismatches_are_strict_blockers",
        "safe_flags_preserved",
    }
    for key in sorted(required_policy):
        if policy.get(key) is not True:
            errors.append(f"manifest_repair_policy_not_true:{key}")
    if payload.get("candidate_rows_verified") != 3014:
        errors.append("manifest_repair_candidate_boundary_not_3014")
    if payload.get("capture_group_count_verified") != 10:
        errors.append("manifest_repair_group_count_not_10")
    return not errors, errors


def build_fixture_cases() -> list[FixtureCase]:
    schemas = load_accepted_schemas()
    cases: list[FixtureCase] = []

    for group in CAPTURE_GROUPS:
        cases.append(
            FixtureCase(
                fixture_id=f"positive_base__{group}",
                category="positive_base",
                field_group=group,
                expected_valid=True,
                rows=[positive_row(group, "base")],
            )
        )
        cases.append(
            FixtureCase(
                fixture_id=f"positive_variant__{group}",
                category="positive_variant",
                field_group=group,
                expected_valid=True,
                rows=[positive_row(group, "variant")],
            )
        )

        schema = group_schema(schemas, group)
        missing_key = first_group_specific_required(schema)
        missing = positive_row(group, "missing_required")
        missing.pop(missing_key)
        cases.append(
            FixtureCase(
                fixture_id=f"negative_missing_required__{group}",
                category="missing_required",
                field_group=group,
                expected_valid=False,
                rows=[missing],
            )
        )

        cases.append(
            FixtureCase(
                fixture_id=f"negative_stale_asof__{group}",
                category="stale_asof",
                field_group=group,
                expected_valid=False,
                rows=[clone_mutated(positive_row(group, "stale_asof"), source_observed_asof_utc=FIXED_STALE_SOURCE_ASOF)],
            )
        )

        forbidden = positive_row(group, "forbidden_identifier")
        forbidden["nested_forbidden_surface"] = {
            "mt5_order_ticket": "ORDER-SYNTHETIC-FORBIDDEN",
        }
        cases.append(
            FixtureCase(
                fixture_id=f"negative_forbidden_identifier__{group}",
                category="forbidden_identifier",
                field_group=group,
                expected_valid=False,
                rows=[forbidden],
            )
        )

        cases.append(
            FixtureCase(
                fixture_id=f"negative_unsafe_flag__{group}",
                category="unsafe_flag",
                field_group=group,
                expected_valid=False,
                rows=[clone_mutated(positive_row(group, "unsafe_flag"), opens_validation=True)],
            )
        )

        cases.append(
            FixtureCase(
                fixture_id=f"negative_schema_version__{group}",
                category="schema_version_mismatch",
                field_group=group,
                expected_valid=False,
                rows=[clone_mutated(positive_row(group, "schema_version"), schema_version="scid_forward_source_capture_v999")],
            )
        )

        extra = positive_row(group, "unexpected_field")
        extra["unexpected_runtime_field"] = "synthetic_extra"
        cases.append(
            FixtureCase(
                fixture_id=f"negative_unexpected_field__{group}",
                category="unexpected_field",
                field_group=group,
                expected_valid=False,
                rows=[extra],
            )
        )

        duplicate_a = positive_row(group, "duplicate_key_a")
        duplicate_b = positive_row(group, "duplicate_key_b")
        duplicate_b["candidate_input_row_id"] = duplicate_a["candidate_input_row_id"]
        duplicate_b["duplicate_proxy_denominator_key"] = "different_duplicate_key_for_same_candidate"
        cases.append(
            FixtureCase(
                fixture_id=f"negative_duplicate_key_drift__{group}",
                category="duplicate_key_drift",
                field_group=group,
                expected_valid=False,
                rows=[duplicate_a, duplicate_b],
            )
        )

        unavailable = unavailable_row(group)
        expected_unavailable_valid = group in MARKET_CONTEXT_UNAVAILABLE_GROUPS
        cases.append(
            FixtureCase(
                fixture_id=f"{'positive' if expected_unavailable_valid else 'negative'}_unavailable_source__{group}",
                category="unavailable_source",
                field_group=group,
                expected_valid=expected_unavailable_valid,
                rows=[unavailable],
                fail_closed_semantics=expected_unavailable_valid,
                inapplicable_reason=None
                if expected_unavailable_valid
                else "SOURCE_UNAVAILABLE_FAIL_CLOSED is accepted only for LTF/orderflow market-context recoverability groups; historical strategy-intent groups must fail closed until prospectively captured.",
            )
        )

        enum_field = first_enum_field(schema)
        if enum_field:
            bad_enum = positive_row(group, "bad_enum")
            bad_enum[enum_field] = "SYNTHETIC_ENUM_VALUE_NOT_ALLOWED"
            cases.append(
                FixtureCase(
                    fixture_id=f"negative_bad_enum__{group}",
                    category="bad_enum",
                    field_group=group,
                    expected_valid=False,
                    rows=[bad_enum],
                )
            )

    cases.append(
        FixtureCase(
            fixture_id="positive_manifest_binding_repair_continuity",
            category="manifest_repair_valid",
            field_group=None,
            expected_valid=True,
            rows=[],
            manifest_payload=build_manifest_repair_payload(valid=True),
        )
    )
    cases.append(
        FixtureCase(
            fixture_id="negative_manifest_binding_repair_strict_hash_policy_disabled",
            category="manifest_repair_invalid",
            field_group=None,
            expected_valid=False,
            rows=[],
            manifest_payload=build_manifest_repair_payload(valid=False),
        )
    )
    return cases


def recursive_forbidden_hits(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lower_key = str(key).lower()
            if lower_key in FORBIDDEN_KEY_EXACT:
                hits.append(f"forbidden_key_exact:{path}.{key}")
            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                if fragment in lower_key:
                    hits.append(f"forbidden_key_fragment:{path}.{key}:{fragment}")
            hits.extend(recursive_forbidden_hits(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            hits.extend(recursive_forbidden_hits(child, f"{path}[{idx}]"))
    elif isinstance(value, str):
        upper = value.upper()
        for marker in FORBIDDEN_VALUE_MARKERS:
            if marker in upper:
                hits.append(f"forbidden_value_marker:{path}:{marker}")
    return hits


def validate_type(key: str, value: Any, spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if "const" in spec and value != spec["const"]:
        errors.append(f"const_violation:{key}")
    if "enum" in spec and value not in spec["enum"]:
        errors.append(f"enum_violation:{key}")

    expected_types = spec.get("type")
    if expected_types is None:
        return errors
    if isinstance(expected_types, str):
        expected_types = [expected_types]
    if value is None:
        if "null" not in expected_types:
            errors.append(f"type_violation:{key}:null")
        return errors

    type_ok = False
    for expected_type in expected_types:
        if expected_type == "string" and isinstance(value, str):
            type_ok = True
        elif expected_type == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            type_ok = True
        elif expected_type == "integer" and isinstance(value, int) and not isinstance(value, bool):
            type_ok = True
        elif expected_type == "boolean" and isinstance(value, bool):
            type_ok = True
        elif expected_type == "object" and isinstance(value, dict):
            type_ok = True
        elif expected_type == "array" and isinstance(value, list):
            type_ok = True
    if not type_ok:
        errors.append(f"type_violation:{key}:{type(value).__name__}")
        return errors

    if isinstance(value, str):
        if spec.get("minLength") is not None and len(value) < int(spec["minLength"]):
            errors.append(f"min_length_violation:{key}")
        if spec.get("format") == "date-time":
            try:
                parse_datetime(value)
            except ValueError:
                errors.append(f"datetime_parse_violation:{key}")
    if isinstance(value, list):
        item_spec = spec.get("items")
        if item_spec:
            for idx, item in enumerate(value):
                errors.extend(validate_type(f"{key}[{idx}]", item, item_spec))
    return errors


def validate_row(row: dict[str, Any], schemas: dict[str, dict[str, Any]] | None = None) -> list[str]:
    schemas = schemas or load_accepted_schemas()
    field_group = row.get("field_group")
    if field_group not in CAPTURE_GROUPS:
        return [f"unknown_field_group:{field_group}"]
    schema = group_schema(schemas, field_group)
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    errors: list[str] = []
    for key in required:
        if key not in row:
            errors.append(f"missing_required:{key}")
    unexpected = sorted(set(row) - set(properties))
    if unexpected:
        errors.append(f"unexpected_keys:{','.join(unexpected)}")

    errors.extend(recursive_forbidden_hits(row))

    for key, value in row.items():
        if key in properties:
            errors.extend(validate_type(key, value, properties[key]))

    for flag in SAFE_FLAG_FIELDS:
        if row.get(flag) is not False:
            errors.append(f"unsafe_flag:{flag}")

    try:
        if parse_datetime(row["source_observed_asof_utc"]) > parse_datetime(row["decision_asof_utc"]):
            errors.append("asof_violation:source_observed_after_decision")
    except (KeyError, TypeError, ValueError):
        pass

    if row.get("field_status") == "CAPTURED_SOURCE_SAFE" and row.get("source_hash") is None:
        errors.append("missing_source_hash_for_captured_row")
    if row.get("source_hash") is None and row.get("source_hash_policy") != "HASH_DEFERRED_SOURCE_UNAVAILABLE_FAIL_CLOSED":
        errors.append("null_source_hash_without_deferral_policy")
    if (
        row.get("field_status") == "SOURCE_UNAVAILABLE_FAIL_CLOSED"
        and field_group not in MARKET_CONTEXT_UNAVAILABLE_GROUPS
    ):
        errors.append("unavailable_status_only_allowed_for_market_context_groups")
    return errors


def validate_dataset(rows: Iterable[dict[str, Any]], schemas: dict[str, dict[str, Any]] | None = None) -> list[str]:
    schemas = schemas or load_accepted_schemas()
    errors: list[str] = []
    duplicate_keys: dict[str, str] = {}
    for idx, row in enumerate(rows):
        for error in validate_row(row, schemas):
            errors.append(f"row_{idx}:{error}")
        candidate_id = row.get("candidate_input_row_id")
        duplicate_key = row.get("duplicate_proxy_denominator_key")
        if isinstance(candidate_id, str) and isinstance(duplicate_key, str):
            if candidate_id in duplicate_keys and duplicate_keys[candidate_id] != duplicate_key:
                errors.append(f"duplicate_key_drift:{candidate_id}")
            duplicate_keys.setdefault(candidate_id, duplicate_key)
    return errors


def validate_fixture_case(case: FixtureCase, schemas: dict[str, dict[str, Any]] | None = None) -> FixtureOutcome:
    if case.manifest_payload is not None:
        observed_valid, errors = manifest_repair_valid(case.manifest_payload)
    else:
        errors = validate_dataset(case.rows, schemas)
        observed_valid = not errors
        if case.fail_closed_semantics and observed_valid:
            for row in case.rows:
                if row.get("field_status") != "SOURCE_UNAVAILABLE_FAIL_CLOSED":
                    errors.append("fail_closed_semantics_missing_field_status")
                if case.field_group == "lower_timeframe_asof_path_availability" and row.get("ltf_availability_status") != "UNAVAILABLE_FAIL_CLOSED":
                    errors.append("fail_closed_semantics_missing_ltf_unavailable")
                if case.field_group == "future_orderflow_depth_proxy_requirements" and row.get("orderflow_proxy_availability_status") != "UNAVAILABLE_FAIL_CLOSED":
                    errors.append("fail_closed_semantics_missing_orderflow_unavailable")
            observed_valid = not errors
    return FixtureOutcome(
        fixture_id=case.fixture_id,
        category=case.category,
        field_group=case.field_group,
        expected_valid=case.expected_valid,
        observed_valid=observed_valid,
        pass_status=observed_valid == case.expected_valid,
        errors=errors,
    )


def validate_fixture_cases(cases: Iterable[FixtureCase]) -> list[FixtureOutcome]:
    schemas = load_accepted_schemas()
    return [validate_fixture_case(case, schemas) for case in cases]


def leak_redaction_audit(cases: Iterable[FixtureCase]) -> dict[str, Any]:
    positive_hits: list[dict[str, Any]] = []
    accepted_fail_closed_hits: list[dict[str, Any]] = []
    deliberate_negative_hits: list[dict[str, Any]] = []
    schemas = load_accepted_schemas()
    for case in cases:
        rows_or_payloads: list[Any] = [case.manifest_payload] if case.manifest_payload is not None else case.rows
        hits: list[str] = []
        for payload in rows_or_payloads:
            hits.extend(recursive_forbidden_hits(payload))
        if not hits:
            continue
        outcome = validate_fixture_case(case, schemas)
        record = {
            "fixture_id": case.fixture_id,
            "category": case.category,
            "field_group": case.field_group,
            "hits": hits,
            "validator_errors": outcome.errors,
        }
        if case.expected_valid:
            accepted_fail_closed_hits.append(record)
        elif case.category == "forbidden_identifier" and not outcome.observed_valid:
            deliberate_negative_hits.append(record)
        else:
            positive_hits.append(record)
    return {
        "positive_or_expected_valid_forbidden_hits": positive_hits + accepted_fail_closed_hits,
        "deliberate_negative_forbidden_hits_caught": deliberate_negative_hits,
        "accepted_rows_clean": not (positive_hits or accepted_fail_closed_hits),
        "deliberate_negative_hit_count": len(deliberate_negative_hits),
    }


def category_matrix(cases: Iterable[FixtureCase]) -> dict[str, Any]:
    matrix: dict[str, Any] = {}
    for case in cases:
        bucket = matrix.setdefault(
            case.category,
            {
                "case_count": 0,
                "field_groups": [],
                "expected_valid_count": 0,
                "expected_invalid_count": 0,
                "inapplicable_proofs": [],
            },
        )
        bucket["case_count"] += 1
        if case.field_group and case.field_group not in bucket["field_groups"]:
            bucket["field_groups"].append(case.field_group)
        if case.expected_valid:
            bucket["expected_valid_count"] += 1
        else:
            bucket["expected_invalid_count"] += 1
        if case.inapplicable_reason:
            bucket["inapplicable_proofs"].append(
                {"field_group": case.field_group, "reason": case.inapplicable_reason}
            )
    for bucket in matrix.values():
        bucket["field_groups"] = sorted(bucket["field_groups"])
    return matrix


def saturation_summary(cases: Iterable[FixtureCase], outcomes: Iterable[FixtureOutcome]) -> dict[str, Any]:
    case_list = list(cases)
    outcome_list = list(outcomes)
    categories = category_matrix(case_list)
    per_group: dict[str, dict[str, int]] = {group: {"positive": 0, "negative_or_fail_closed": 0} for group in CAPTURE_GROUPS}
    for case in case_list:
        if not case.field_group:
            continue
        if case.expected_valid and not case.fail_closed_semantics and case.category.startswith("positive"):
            per_group[case.field_group]["positive"] += 1
        else:
            per_group[case.field_group]["negative_or_fail_closed"] += 1
    return {
        "fixture_case_count": len(case_list),
        "row_fixture_count": sum(len(case.rows) for case in case_list),
        "category_count": len(categories),
        "categories": categories,
        "per_group_coverage": per_group,
        "all_outcomes_pass_expected_validity": all(outcome.pass_status for outcome in outcome_list),
        "not_shallow_thresholds": {
            "minimum_positive_cases_required": 20,
            "minimum_fixture_cases_required": 90,
            "positive_cases_observed": sum(1 for case in case_list if case.expected_valid and case.category.startswith("positive")),
            "fixture_cases_observed": len(case_list),
        },
    }
