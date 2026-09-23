"""Independent verifier for Wave-21 serialized full-flow projections.

This module intentionally does not import the producer harness, timewarp, or
any producer summary helper.  Its only economic inputs are the serialized
stage rows and the hash-bound receipt/fingerprint files.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = "gtos.wave21.research_timewarp_full_flow.v1"
VERIFIER_SCHEMA = f"{SCHEMA}.independent_verifier"
DISPOSITION_FIELDS = (
    "raw_data_status",
    "selector_action",
    "selector_reason",
    "effective_selector_action",
    "scheduler_action",
    "scheduler_reason",
    "scheduler_materialization_action_intent",
    "risk_decision",
    "risk_decision_reason",
    "order_status",
    "fill_status",
    "terminal_outcome",
    "close_reason",
    "miss_reason",
)
COST_COMPONENT_FIELDS = (
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
)
POST_LIFECYCLE_COMPONENT_COST_SCHEMA = (
    "gtos.costs.post_lifecycle_component_cost.v1"
)
POST_LIFECYCLE_COST_STAGE_SCHEMA = (
    "gtos.wave21.post_lifecycle_component_cost_stage.v1"
)
POST_LIFECYCLE_ACCOUNTING_SCHEMA = (
    "gtos.wave21.post_lifecycle_accounting.v1"
)
POST_LIFECYCLE_COMPONENT_SOURCE_ROLES = {
    "spread_r": "observed_quote_spread_attributed_in_fill_anchored_gross",
    "expected_slippage_r": (
        "source_bound_expected_slippage_not_broker_realized"
    ),
    "swap_cost_r": "actual_elapsed_broker_rollover_component",
    "commission_r": "broker_schedule_component",
}
POST_LIFECYCLE_COVERAGE_STRENGTH = {
    "MEASURED": 0,
    "TRANSFERRED": 1,
    "MODELLED": 2,
}
TICK_COVERED_SYMBOLS = ("EURUSD", "USDJPY", "XAGUSD", "XAUUSD")
GTOS_24_SYMBOL_SURFACE = (
    "AUDJPY",
    "AUDUSD",
    "BTCUSD",
    "CHFJPY",
    "ETHUSD",
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "GER40",
    "JP225",
    "NAS100",
    "NZDUSD",
    "SPX500",
    "UK100",
    "UKOIL_cash",
    "US30_cash",
    "USDCAD",
    "USDCHF",
    "USDJPY",
    "USOIL_cash",
    "XAGUSD",
    "XAUUSD",
)
GTOS_BROAD_ORIGIN_FAMILIES = (
    "microstructure_absorption_reversal",
    "microstructure_vdelta_divergence",
    "range_extreme_reversion",
    "liquidity_sweep_reclaim",
    "structural_distance_extreme",
    "cross_asset_lead_lag",
    "displacement_continuation",
    "session_open_range_break",
    "regime_transition_break",
    "volatility_compression_expansion",
    "current_fvg_fill",
    "current_ob_retest",
    "current_breaker_re_entry",
)
STAGE_DAG_SCHEMA = f"{SCHEMA}.occurrence_stage_dag_audit"
WAVE21_TRUTH_STAGE_LEDGER = "wave21_truth_stage"
WAVE21_TRUTH_STAGE_RECEIPT_SCHEMA = "gtos.wave21.truth_stage_receipt.v1"
WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA = "gtos.wave21.truth_chain_occurrence.v1"
WAVE21_TRUTH_IDENTITY_ROOT_SCHEMA = "gtos.wave21.truth_identity_root.v1"
WAVE21_TRUTH_STAGE_RECEIPT_FIELD = "wave21_truth_stage_receipt"
WAVE21_TRUTH_IDENTITY_ROOT_FIELD = "wave21_truth_identity_root_sha256"
WAVE21_TRUTH_STAGE_PACKET_FIELD = "wave21_truth_stage_packet"
WAVE21_TRUTH_CHAIN_ORDINAL_FIELD = "wave21_truth_chain_occurrence_ordinal"
WAVE21_TRUTH_CHAIN_KEY_FIELD = "wave21_truth_chain_occurrence_key"
WAVE21_TRUTH_CHAIN_KIND_FIELD = "wave21_truth_chain_kind"
WAVE21_TRUTH_CHAIN_ATOMS_FIELD = "wave21_truth_chain_occurrence_atoms"
WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD = "wave21_truth_candidate_occurrence_ordinal"
WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD = "wave21_truth_source_slot_key"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class VerificationError(RuntimeError):
    """Serialized evidence failed an independent check."""


def canonical_bytes(value: Any) -> bytes:
    normalized = strict_json_primitive(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def strict_json_primitive(value: Any, *, path: str = "$") -> Any:
    """Fail closed instead of stringifying unsupported hash inputs."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise VerificationError(f"nonfinite_json_number:{path}")
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise VerificationError(f"naive_datetime_forbidden:{path}")
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise VerificationError(
                    f"non_string_json_key:{path}:{type(key).__name__}"
                )
            output[key] = strict_json_primitive(item, path=f"{path}.{key}")
        return output
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        return [
            strict_json_primitive(item, path=f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    raise VerificationError(
        f"unsupported_json_object:{path}:{type(value).__module__}."
        f"{type(value).__qualname__}"
    )


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_rooted_json(path: Path, root_field: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise VerificationError(f"json_root_not_object:{path}")
    stored = payload.pop(root_field, None)
    if stored != stable_sha256(payload):
        raise VerificationError(f"json_root_hash_mismatch:{path.name}")
    payload[root_field] = stored
    return payload


def _identity(row: Mapping[str, Any]) -> dict[str, Any]:
    identity = row.get("identity")
    if not isinstance(identity, Mapping):
        raise VerificationError("stage_identity_not_mapping")
    return dict(identity)


def _comparison(row: Mapping[str, Any]) -> dict[str, Any]:
    required = (
        "schema",
        "stage",
        "stage_row_ordinal",
        "identity",
        "observables",
    )
    if any(field not in row for field in required):
        raise VerificationError("stage_comparison_fields_missing")
    return {field: row[field] for field in required}


def _explicit_utc_datetime(value: Any, *, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise VerificationError(f"invalid_utc_timestamp:{field}") from exc
    else:
        raise VerificationError(f"utc_timestamp_missing_or_unsupported:{field}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise VerificationError(f"naive_timestamp_forbidden:{field}")
    if parsed.utcoffset().total_seconds() != 0:
        raise VerificationError(f"non_utc_timestamp_for_true_utc_source:{field}")
    return parsed.astimezone(timezone.utc)


def _finite_nonnegative_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) and number >= 0.0 else None


def _post_lifecycle_component_cost_assessment(
    packet: Any,
) -> dict[str, Any]:
    """Mirror the shared cost contract from serialized primitives only."""

    if not isinstance(packet, Mapping):
        return {
            "status": "NOT_EVALUABLE",
            "complete": False,
            "component_values": {},
            "component_sum_r": None,
            "failures": ["post_lifecycle_packet_missing"],
        }
    failures: list[str] = []
    if packet.get("schema") != POST_LIFECYCLE_COMPONENT_COST_SCHEMA:
        failures.append("wrong_post_lifecycle_schema")
    if packet.get("cost_role") != "post_lifecycle_component_cost":
        failures.append("wrong_cost_role_not_post_lifecycle")
    if packet.get("status") != "COMPLETE":
        failures.append("post_lifecycle_status_not_complete")
    if packet.get("broker_realized_status") != (
        "NOT_EVALUABLE_NO_BROKER_DEAL_COMPONENTS"
    ):
        failures.append("broker_realized_claim_scope_invalid")

    predecessor = packet.get("predecessor")
    if not isinstance(predecessor, Mapping):
        failures.append("predecessor_missing")
    else:
        if predecessor.get("cost_role") != "pretrade_expected_cost":
            failures.append("predecessor_role_invalid")
        if predecessor.get("components_reused") != []:
            failures.append("pretrade_components_reused")

    lifecycle = packet.get("lifecycle")
    if not isinstance(lifecycle, Mapping):
        lifecycle = {}
        failures.append("lifecycle_missing")
    try:
        entry = _explicit_utc_datetime(
            lifecycle.get("entry_utc"), field="post_cost.lifecycle.entry_utc"
        )
        exit_ = _explicit_utc_datetime(
            lifecycle.get("exit_utc"), field="post_cost.lifecycle.exit_utc"
        )
    except VerificationError:
        entry = exit_ = None
        failures.append("actual_entry_exit_invalid")
    elapsed = _finite_nonnegative_number(
        lifecycle.get("elapsed_holding_hours")
    )
    if entry is not None and exit_ is not None:
        if exit_ < entry:
            failures.append("actual_entry_exit_invalid")
        elif elapsed != (exit_ - entry).total_seconds() / 3600.0:
            failures.append("actual_elapsed_holding_mismatch")
    if lifecycle.get("holding_source_status") != (
        "actual_simulated_entry_exit_elapsed"
    ):
        failures.append("holding_source_is_not_actual_lifecycle")
    if lifecycle.get("source_status") != "actual_simulated_lifecycle":
        failures.append("lifecycle_source_status_invalid")
    provenance = lifecycle.get("provenance")
    if not isinstance(provenance, str) or not provenance.strip():
        failures.append("lifecycle_provenance_missing")
    for field in ("entry_price", "exit_price", "sl_distance_price"):
        value = _finite_nonnegative_number(lifecycle.get(field))
        if value is None or value <= 0.0:
            failures.append(f"invalid_lifecycle_geometry:{field}")
    geometry = lifecycle.get("quote_geometry")
    if not isinstance(geometry, Mapping):
        failures.append("quote_geometry_missing")
    else:
        if geometry.get("gross_basis") != "fill_anchored_quote_geometry":
            failures.append("quote_geometry_gross_basis_invalid")
        if geometry.get("gross_includes_spread") is not True:
            failures.append("quote_geometry_spread_inclusion_missing")
        if not _is_sha256(geometry.get("source_sha256")):
            failures.append("quote_geometry_source_hash_invalid")
        if geometry.get("trade_id") != packet.get("trade_id"):
            failures.append("quote_geometry_trade_mismatch")
    integrity_keys = (
        "entry_utc",
        "exit_utc",
        "symbol",
        "account",
        "side",
        "elapsed_holding_hours",
        "entry_price",
        "exit_price",
        "sl_distance_price",
        "holding_source_status",
        "source_status",
        "provenance",
    )
    lifecycle_integrity = {
        key: lifecycle.get(key) for key in integrity_keys
    }
    lifecycle_integrity["quote_geometry"] = geometry
    try:
        expected_lifecycle_sha = hashlib.sha256(
            json.dumps(
                strict_json_primitive(lifecycle_integrity),
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()
    except VerificationError:
        expected_lifecycle_sha = None
    if lifecycle.get("record_sha256") != expected_lifecycle_sha:
        failures.append("lifecycle_record_hash_mismatch")

    authority = packet.get("cost_input_authority")
    manifest_sha: str | None = None
    broker_truth_sha: str | None = None
    if not isinstance(authority, Mapping):
        failures.append("cost_input_authority_missing")
    else:
        if authority.get("root_kind") != "git_versioned_manifest_bytes":
            failures.append("cost_input_authority_root_invalid")
        manifest_sha = (
            str(authority.get("manifest_sha256"))
            if _is_sha256(authority.get("manifest_sha256"))
            else None
        )
        if manifest_sha is None:
            failures.append("cost_input_manifest_hash_invalid")
        if not isinstance(authority.get("manifest_path"), str):
            failures.append("cost_input_manifest_path_missing")
        broker_truth_sha = (
            str(authority.get("broker_true_costs_artifact_sha256"))
            if _is_sha256(
                authority.get("broker_true_costs_artifact_sha256")
            )
            else None
        )
        if broker_truth_sha is None:
            failures.append("broker_true_costs_artifact_hash_invalid")

    components = packet.get("components")
    if not isinstance(components, Mapping):
        components = {}
        failures.append("post_lifecycle_components_missing")
    values: dict[str, float] = {}
    coverages: list[str] = []
    for field in COST_COMPONENT_FIELDS:
        component = components.get(field)
        if not isinstance(component, Mapping):
            failures.append(f"missing_post_lifecycle_component:{field}")
            continue
        value = _finite_nonnegative_number(component.get("value"))
        if value is None:
            failures.append(f"invalid_post_lifecycle_component:{field}")
        else:
            values[field] = value
        coverage = str(component.get("coverage") or "")
        if coverage not in POST_LIFECYCLE_COVERAGE_STRENGTH:
            failures.append(f"invalid_component_coverage:{field}")
        else:
            coverages.append(coverage)
        component_provenance = component.get("provenance")
        if (
            not isinstance(component_provenance, str)
            or not component_provenance.strip()
        ):
            failures.append(f"component_provenance_missing:{field}")
        if component.get("source_role") != (
            POST_LIFECYCLE_COMPONENT_SOURCE_ROLES[field]
        ):
            failures.append(f"component_source_role_invalid:{field}")
        if field in {"swap_cost_r", "commission_r"} and component.get(
            "broker_true_costs_artifact_sha256"
        ) != broker_truth_sha:
            failures.append(f"broker_truth_authority_mismatch:{field}")
    slippage = components.get("expected_slippage_r")
    if isinstance(slippage, Mapping) and slippage.get(
        "cost_inputs_manifest_sha256"
    ) != manifest_sha:
        failures.append("slippage_manifest_authority_mismatch")
    spread = components.get("spread_r")
    if isinstance(spread, Mapping):
        if spread.get("accounting") != (
            "included_in_fill_anchored_gross_no_additional_deduction"
        ):
            failures.append("spread_accounting_not_exactly_once")
        if _finite_nonnegative_number(
            spread.get("attributed_physical_spread_r")
        ) is None:
            failures.append("attributed_physical_spread_missing")

    component_sum: float | None = None
    if len(values) == len(COST_COMPONENT_FIELDS):
        component_sum = (
            values["spread_r"]
            + values["expected_slippage_r"]
            + values["swap_cost_r"]
            + values["commission_r"]
        )
    total = _finite_nonnegative_number(packet.get("total_cost_r"))
    if total is None:
        failures.append("post_lifecycle_total_invalid")
    elif component_sum is None or total != component_sum:
        failures.append("post_lifecycle_component_identity_mismatch")
    if packet.get("component_sum_order") != list(COST_COMPONENT_FIELDS):
        failures.append("component_sum_order_invalid")
    if coverages:
        weakest = max(
            coverages,
            key=lambda value: POST_LIFECYCLE_COVERAGE_STRENGTH[value],
        )
        if (
            len(coverages) != len(COST_COMPONENT_FIELDS)
            or packet.get("coverage") != weakest
        ):
            failures.append("post_lifecycle_weakest_coverage_mismatch")
    failures = list(dict.fromkeys(failures))
    complete = not failures
    return {
        "status": "COMPLETE" if complete else "NOT_EVALUABLE",
        "complete": complete,
        "component_values": values,
        "component_sum_r": component_sum if complete else None,
        "failures": failures,
    }


def _post_lifecycle_cost_stage_assessment(
    stage_payload: Mapping[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    if stage_payload.get("post_lifecycle_component_cost_stage_schema") != (
        POST_LIFECYCLE_COST_STAGE_SCHEMA
    ):
        failures.append("post_lifecycle_cost_stage_schema_invalid")
    nested = stage_payload.get("post_lifecycle_component_cost")
    assessment = _post_lifecycle_component_cost_assessment(nested)
    nested_sha = stable_sha256(nested) if isinstance(nested, Mapping) else None
    if stage_payload.get("post_lifecycle_component_cost_sha256") != nested_sha:
        failures.append("post_lifecycle_component_cost_hash_mismatch")
    if stage_payload.get("post_lifecycle_component_cost_assessment") != assessment:
        failures.append("post_lifecycle_component_cost_assessment_mismatch")
    expected_status = "MATERIALIZED" if assessment["complete"] else "NOT_EVALUABLE"
    if stage_payload.get("status") != expected_status:
        failures.append("post_lifecycle_component_cost_stage_status_mismatch")
    expected_failures = [] if assessment["complete"] else assessment["failures"]
    if stage_payload.get("failures") != expected_failures:
        failures.append("post_lifecycle_component_cost_stage_failures_mismatch")
    for forbidden_field in (
        "component_sum_r",
        "components",
        "cost_r",
        "expected_cost_r",
        "total_cost_components",
        "total_cost_r",
    ):
        if forbidden_field in stage_payload:
            failures.append(
                f"post_lifecycle_cost_packet_must_remain_nested:{forbidden_field}"
            )
    return {
        "complete": assessment["complete"] and not failures,
        "nested": dict(nested) if isinstance(nested, Mapping) else None,
        "nested_sha256": nested_sha,
        "assessment": assessment,
        "failures": list(dict.fromkeys(failures)),
    }


def _verify_input_manifest(
    *, input_manifest: Mapping[str, Any], fingerprint: Mapping[str, Any]
) -> dict[str, Any]:
    """Recompute serialized config/source/code authority without producer imports."""

    if stable_sha256(input_manifest) != fingerprint.get(
        "input_manifest_root_sha256"
    ):
        raise VerificationError("input_manifest_root_mismatch")

    config = input_manifest.get("effective_config_payload")
    if not isinstance(config, Mapping):
        raise VerificationError("effective_config_payload_missing")
    if stable_sha256(config) != input_manifest.get("config_root_sha256"):
        raise VerificationError("effective_config_root_mismatch")
    runtime = config.get("gtos_vnext_runtime")
    if not isinstance(runtime, Mapping):
        raise VerificationError("effective_config_runtime_missing")
    truth_value = runtime.get("wave21_full_flow_truth_mode_enabled")
    if type(truth_value) is not bool:
        raise VerificationError("truth_mode_config_value_not_boolean")
    if truth_value is not bool(input_manifest.get("truth_mode")):
        raise VerificationError("truth_mode_config_receipt_mismatch")
    harness_config = config.get("broad_live_as_if_replay_harness")
    if not isinstance(harness_config, Mapping):
        raise VerificationError("effective_harness_config_missing")
    required_harness_values = {
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "completed_bar_only_chronology": True,
        "future_bar_rejection_mandatory": True,
    }
    for key, expected in required_harness_values.items():
        if harness_config.get(key) is not expected:
            raise VerificationError(f"effective_harness_config_invalid:{key}")
    if input_manifest.get("prepared_day_pack") is not None:
        raise VerificationError("prepared_day_pack_not_none")
    campaign = input_manifest.get("campaign")
    if not isinstance(campaign, Mapping):
        raise VerificationError("campaign_manifest_missing")
    if campaign.get("max_candidates_per_symbol_window") != 0:
        raise VerificationError("candidate_population_cap_not_zero")
    if campaign.get("run_smoke_subset") is not False:
        raise VerificationError("smoke_subset_filter_not_false")

    source_manifest = input_manifest.get("source_manifest")
    if not isinstance(source_manifest, Mapping):
        raise VerificationError("source_manifest_missing")
    source_rows = source_manifest.get("sources")
    if not isinstance(source_rows, Sequence):
        raise VerificationError("source_manifest_rows_missing")
    source_body = {"sources": list(source_rows)}
    if source_manifest.get("source_root_sha256") != stable_sha256(source_body):
        raise VerificationError("source_manifest_root_mismatch")
    source_symbols = sorted(
        {
            str(row.get("symbol") or "")
            for row in source_rows
            if isinstance(row, Mapping) and row.get("symbol")
        }
    )
    if truth_value and tuple(source_symbols) != tuple(sorted(GTOS_24_SYMBOL_SURFACE)):
        raise VerificationError("truth_source_denominator_not_exact_24")
    source_authority = input_manifest.get("source_authority")
    if source_authority is not None and not isinstance(source_authority, Mapping):
        raise VerificationError("input_source_authority_not_mapping")
    if truth_value:
        if not isinstance(source_authority, Mapping) or not source_authority:
            raise VerificationError("truth_loader_owned_source_authority_missing")
        # A hash over a producer-projected object is not independent source
        # proof.  This gate is replaced only by the committed loader validator
        # that reopens manifest/component bytes, reparses/reselects rows, and
        # recomputes completion witnesses.  Until then truth verification must
        # stop here rather than accept the estate preflight as row authority.
        raise VerificationError(
            "truth_source_authority_independent_reopen_validator_dependency_not_integrated"
        )

    code_manifest = input_manifest.get("code_manifest")
    if not isinstance(code_manifest, Mapping):
        raise VerificationError("code_manifest_missing")
    module_rows = code_manifest.get("modules")
    if not isinstance(module_rows, Sequence):
        raise VerificationError("code_manifest_module_rows_missing")
    code_body = {"modules": list(module_rows)}
    if code_manifest.get("code_root_sha256") != stable_sha256(code_body):
        raise VerificationError("code_manifest_root_mismatch")
    code_checks: list[dict[str, Any]] = []
    seen_modules: set[str] = set()
    for ordinal, raw_row in enumerate(module_rows):
        if not isinstance(raw_row, Mapping):
            raise VerificationError(f"code_manifest_row_not_mapping:{ordinal}")
        module_name = str(raw_row.get("module") or "")
        if not module_name or module_name in seen_modules:
            raise VerificationError(f"code_manifest_module_duplicate_or_missing:{ordinal}")
        seen_modules.add(module_name)
        path_value = raw_row.get("path")
        if not isinstance(path_value, str) or not Path(path_value).is_absolute():
            raise VerificationError(f"code_manifest_path_not_absolute:{module_name}")
        path = Path(path_value)
        if not path.is_file():
            raise VerificationError(f"code_manifest_file_missing:{module_name}")
        actual_sha = file_sha256(path)
        actual_bytes = path.stat().st_size
        if raw_row.get("sha256") != actual_sha:
            raise VerificationError(f"code_manifest_file_hash_mismatch:{module_name}")
        if raw_row.get("byte_count") != actual_bytes:
            raise VerificationError(f"code_manifest_file_size_mismatch:{module_name}")
        code_checks.append(
            {
                "module": module_name,
                "path": str(path),
                "sha256": actual_sha,
                "byte_count": actual_bytes,
            }
        )

    return {
        "input_manifest_root_valid": True,
        "effective_config_root_valid": True,
        "truth_mode_config_value": truth_value,
        "source_manifest_root_valid": True,
        "source_symbol_denominator": source_symbols,
        "source_authority_boundary": (
            "engineering_inventory_only_not_independently_reopened"
            if isinstance(source_authority, Mapping) and source_authority
            else "not_supplied"
        ),
        "code_manifest_root_valid": True,
        "code_files_reopened_count": len(code_checks),
        "code_file_checks": code_checks,
    }


def _is_sha256(value: Any) -> bool:
    return bool(_SHA256_RE.fullmatch(str(value or "").strip().lower()))


def _forbidden_candidate_atom_paths(
    value: Any, *, path: str = "candidate_decision_fingerprint_atoms"
) -> list[str]:
    failures: list[str] = []
    forbidden = (
        "order_type",
        "order_hint",
        "time_in_force",
        "tif",
        "expiry",
        "executable",
        "final_order",
    )
    if isinstance(value, Mapping):
        for key, item in value.items():
            child = f"{path}.{key}"
            if any(token in str(key).lower() for token in forbidden):
                failures.append(child)
            failures.extend(_forbidden_candidate_atom_paths(item, path=child))
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for ordinal, item in enumerate(value):
            failures.extend(
                _forbidden_candidate_atom_paths(item, path=f"{path}[{ordinal}]")
            )
    return failures


def _truth_stage_packet_failures(packet: Mapping[str, Any]) -> list[str]:
    receipt = packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD)
    if not isinstance(receipt, Mapping):
        return ["stage_receipt_missing"]
    failures: list[str] = []
    if receipt.get("schema") != WAVE21_TRUTH_STAGE_RECEIPT_SCHEMA:
        failures.append("stage_receipt_schema_invalid")
    payload = {
        key: value
        for key, value in packet.items()
        if key != WAVE21_TRUTH_STAGE_RECEIPT_FIELD
    }
    stage_payload = {
        key: value
        for key, value in payload.items()
        if key != WAVE21_TRUTH_IDENTITY_ROOT_FIELD
    }
    receipt_body = {
        key: value for key, value in receipt.items() if key != "receipt_sha256"
    }
    if receipt.get("payload_sha256") != stable_sha256(payload):
        failures.append("stage_payload_hash_mismatch")
    if receipt.get("receipt_sha256") != stable_sha256(receipt_body):
        failures.append("stage_receipt_hash_mismatch")
    identity_root = packet.get(WAVE21_TRUTH_IDENTITY_ROOT_FIELD)
    if not _is_sha256(identity_root):
        failures.append("stage_identity_root_invalid")
    if receipt.get("identity_root_sha256") != identity_root:
        failures.append("stage_receipt_identity_root_mismatch")
    fixed_point_pass = receipt.get("fixed_point_pass")
    if (
        isinstance(fixed_point_pass, bool)
        or not isinstance(fixed_point_pass, int)
        or fixed_point_pass < 0
    ):
        failures.append("fixed_point_pass_invalid")
    stage_ordinal = receipt.get("stage_ordinal")
    if (
        isinstance(stage_ordinal, bool)
        or not isinstance(stage_ordinal, int)
        or stage_ordinal < 0
    ):
        failures.append("stage_ordinal_invalid")
    stage_id = str(receipt.get("stage_id") or "")
    if not stage_id:
        failures.append("stage_id_missing")
    if receipt.get("disposition") not in {
        "MATERIALIZED",
        "TERMINAL_EVALUABLE_NONTRADE",
        "TERMINAL_NOT_EVALUABLE",
    }:
        failures.append("stage_disposition_invalid")
    disposition = receipt.get("disposition")
    if stage_id == "terminal_disposition":
        if disposition not in {
            "TERMINAL_EVALUABLE_NONTRADE",
            "TERMINAL_NOT_EVALUABLE",
        }:
            failures.append("terminal_stage_disposition_invalid")
    elif disposition != "MATERIALIZED":
        failures.append("nonterminal_stage_has_terminal_disposition")
    if packet.get("wave21_truth_stage_id") != stage_id:
        failures.append("stage_payload_id_receipt_mismatch")
    status = str(packet.get("wave21_truth_stage_status") or "")
    if status not in {"MATERIALIZED", "EVALUABLE_NONTRADE", "NOT_EVALUABLE"}:
        failures.append("stage_payload_status_invalid")
    if stage_id == "terminal_disposition":
        expected_status = (
            "EVALUABLE_NONTRADE"
            if disposition == "TERMINAL_EVALUABLE_NONTRADE"
            else "NOT_EVALUABLE"
        )
        if status != expected_status:
            failures.append("terminal_payload_status_disposition_mismatch")
    if not stage_payload:
        failures.append("stage_payload_missing")
    return failures


class _OccurrenceStageDagVerifier:
    """Collect serialized rows and independently rebuild the window DAG."""

    def __init__(self) -> None:
        self.asof_rows: list[dict[str, Any]] = []
        self.candidate_rows: list[dict[str, Any]] = []
        self.stage_rows: list[dict[str, Any]] = []
        self.missed_rows: list[dict[str, Any]] = []
        self.order_rows: list[dict[str, Any]] = []
        self.trade_rows: list[dict[str, Any]] = []

    def observe_asof(
        self, identity: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        self.asof_rows.append({**dict(identity), **dict(values)})

    def observe_candidate(
        self, identity: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        self.candidate_rows.append({**dict(identity), **dict(values)})

    def observe_truth_stage(
        self, identity: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        self.stage_rows.append({**dict(identity), **dict(values)})

    def observe_missed(
        self, identity: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        self.missed_rows.append({**dict(identity), **dict(values)})

    def observe_order(
        self, identity: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        self.order_rows.append({**dict(identity), **dict(values)})

    def observe_trade(
        self, identity: Mapping[str, Any], values: Mapping[str, Any]
    ) -> None:
        self.trade_rows.append({**dict(identity), **dict(values)})

    def finish(self) -> dict[str, Any]:
        failures: list[dict[str, Any]] = []

        def fail(reason: str, **context: Any) -> None:
            if len(failures) < 300:
                failures.append(
                    {"reason": reason, **strict_json_primitive(context)}
                )

        candidate_ordinals: list[int] = []
        candidate_instance_keys: list[str] = []
        candidate_key_truth_ordinal: dict[str, int | None] = {}
        candidate_rows_missing_truth_ordinal = 0
        candidate_failure_count = 0
        for row_index, row in enumerate(self.candidate_rows):
            row_failures: list[str] = []
            instance_key = str(
                row.get("canonical_replay_candidate_instance_key") or ""
            ).strip()
            if not instance_key:
                row_failures.append("candidate_occurrence_instance_key_missing")
            elif instance_key in candidate_key_truth_ordinal:
                row_failures.append("candidate_occurrence_instance_key_duplicate")
            else:
                candidate_instance_keys.append(instance_key)
                candidate_key_truth_ordinal[instance_key] = None
            ordinal = row.get(WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD)
            if ordinal is None:
                # Occurrence-model row: terminal disposition is carried by the
                # missed/order/trade union, not by a truth-chain ordinal.
                candidate_rows_missing_truth_ordinal += 1
            elif (
                isinstance(ordinal, bool)
                or not isinstance(ordinal, int)
                or ordinal < 0
            ):
                row_failures.append(
                    "candidate_occurrence_ordinal_missing_or_invalid"
                )
            else:
                candidate_ordinals.append(ordinal)
                if instance_key:
                    candidate_key_truth_ordinal[instance_key] = ordinal
            status = row.get("candidate_identity_contract_status")
            if status not in (
                None,
                "valid_emission_v2_candidate_decision_v1_exec_not_final",
            ):
                row_failures.append("candidate_identity_contract_not_v2")
            if row.get("candidate_instance_identity_collision") is True:
                row_failures.append("candidate_occurrence_identity_collision")
            atoms = row.get("candidate_decision_fingerprint_atoms")
            if isinstance(atoms, Mapping) and _forbidden_candidate_atom_paths(atoms):
                row_failures.append(
                    "candidate_fingerprint_contains_order_or_exec_atoms"
                )
            cross = row.get("emission_cross_asset_source_authorities")
            if cross not in (None, []):
                if not isinstance(cross, list):
                    row_failures.append("cross_asset_source_authorities_not_list")
                else:
                    seen: set[tuple[str, int]] = set()
                    for dependency_index, dependency in enumerate(cross):
                        if not isinstance(dependency, Mapping):
                            row_failures.append(
                                f"cross_asset_dependency_{dependency_index}_not_mapping"
                            )
                            continue
                        leader = str(
                            dependency.get("leader_symbol") or ""
                        ).strip()
                        probe = dependency.get("probe_ordinal")
                        if (
                            not leader
                            or isinstance(probe, bool)
                            or not isinstance(probe, int)
                        ):
                            row_failures.append(
                                f"cross_asset_dependency_{dependency_index}_identity_invalid"
                            )
                        elif (leader, probe) in seen:
                            row_failures.append(
                                f"cross_asset_dependency_{dependency_index}_duplicate"
                            )
                        else:
                            seen.add((leader, probe))
                        if not _is_sha256(
                            dependency.get("source_authority_root_sha256")
                        ):
                            row_failures.append(
                                f"cross_asset_dependency_{dependency_index}_authority_root_invalid"
                            )
            if row_failures:
                candidate_failure_count += 1
                fail(
                    "candidate_pre_scheduler_contract_invalid",
                    candidate_row_index=row_index,
                    failures=row_failures,
                )
        if candidate_ordinals and candidate_ordinals != list(
            range(len(candidate_ordinals))
        ):
            fail("candidate_occurrence_ordinals_not_global_contiguous")

        zero_slot_keys: list[str] = []
        for row in self.asof_rows:
            if int(row.get("candidate_generation_emitted_count") or 0) != 0:
                continue
            decision_time = str(row.get("decision_time_utc") or "").strip()
            symbol = str(row.get("symbol") or "").strip().upper()
            if decision_time and symbol:
                zero_slot_keys.append(f"{decision_time}@@{symbol}")
            else:
                fail("zero_candidate_asof_slot_identity_missing")

        groups: dict[
            tuple[str, str, int | None], list[Mapping[str, Any]]
        ] = {}
        group_order: list[tuple[str, str, int | None]] = []
        closed: set[tuple[str, str, int | None]] = set()
        prior_group: tuple[str, str, int | None] | None = None
        row_keys: set[str] = set()
        for row_index, row in enumerate(self.stage_rows):
            ordinal = row.get(WAVE21_TRUTH_CHAIN_ORDINAL_FIELD)
            if ordinal != row_index:
                fail(
                    "truth_stage_occurrence_ordinal_not_contiguous",
                    row_index=row_index,
                    observed=ordinal,
                )
            kind = str(row.get(WAVE21_TRUTH_CHAIN_KIND_FIELD) or "")
            slot = str(row.get(WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD) or "").strip()
            candidate_ordinal = row.get(WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD)
            if kind == "source_terminal":
                candidate_ordinal = None
            group = (kind, slot, candidate_ordinal)
            if prior_group is not None and group != prior_group:
                closed.add(prior_group)
            if group in closed:
                fail("truth_candidate_chain_rows_not_contiguous", row_index=row_index)
            if group not in groups:
                groups[group] = []
                group_order.append(group)
            prior_group = group
            atoms = {
                WAVE21_TRUTH_CHAIN_ORDINAL_FIELD: ordinal,
                WAVE21_TRUTH_CHAIN_KIND_FIELD: kind,
                WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD: slot,
                WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD: candidate_ordinal,
            }
            if row.get("wave21_truth_chain_occurrence_schema") != (
                WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA
            ):
                fail("truth_chain_occurrence_schema_invalid", row_index=row_index)
            if row.get(WAVE21_TRUTH_CHAIN_ATOMS_FIELD) != atoms:
                fail("truth_chain_occurrence_atoms_mismatch", row_index=row_index)
            expected_key = "wave21chain:" + stable_sha256(
                {"schema": WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA, **atoms}
            )
            row_key = str(row.get(WAVE21_TRUTH_CHAIN_KEY_FIELD) or "")
            if row_key != expected_key:
                fail("truth_chain_occurrence_key_mismatch", row_index=row_index)
            if row_key in row_keys:
                fail("truth_chain_occurrence_key_duplicate", row_index=row_index)
            row_keys.add(row_key)
            packet = row.get(WAVE21_TRUTH_STAGE_PACKET_FIELD)
            if not isinstance(packet, Mapping):
                fail("truth_stage_packet_missing", row_index=row_index)
                groups[group].append({})
                continue
            packet_failures = _truth_stage_packet_failures(packet)
            if packet_failures:
                fail(
                    "truth_stage_packet_invalid",
                    row_index=row_index,
                    failures=packet_failures,
                )
            groups[group].append(dict(packet))

        stage_counts: Counter[str] = Counter()
        stage_status_counts: Counter[str] = Counter()
        terminal_ne = 0
        terminal_nontrade = 0
        complete_accounted = 0
        candidate_chain_ordinals: list[int] = []
        source_terminal_slots: list[str] = []
        selector_by_pass: dict[tuple[str, int], set[int]] = defaultdict(set)
        scheduler_by_pass: dict[tuple[str, int], set[int]] = defaultdict(set)
        convergence_by_pass: dict[tuple[str, int], set[int]] = defaultdict(set)
        convergence_packets: dict[
            tuple[str, int], list[Mapping[str, Any]]
        ] = defaultdict(list)

        def window_key(slot: str) -> str:
            return slot.rsplit("@@", 1)[0]

        for group in group_order:
            kind, slot, candidate_ordinal = group
            packets = groups[group]
            receipts = [
                packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD)
                if isinstance(
                    packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD), Mapping
                )
                else {}
                for packet in packets
            ]
            for stage_index, (packet, receipt) in enumerate(
                zip(packets, receipts)
            ):
                stage_id = str(receipt.get("stage_id") or "")
                stage_counts[stage_id] += 1
                stage_status_counts[
                    f"{stage_id}:{packet.get('wave21_truth_stage_status')}"
                ] += 1
                if receipt.get("stage_ordinal") != stage_index:
                    fail("truth_stage_ordinal_not_contiguous", group=list(group))
                predecessor = receipts[stage_index - 1] if stage_index else None
                predecessor_identity = None
                if predecessor is None:
                    if receipt.get("predecessor_stage_id") is not None or receipt.get(
                        "predecessor_stage_receipt_sha256"
                    ) is not None:
                        fail("truth_initial_stage_has_predecessor", group=list(group))
                else:
                    if receipt.get("predecessor_stage_id") != predecessor.get(
                        "stage_id"
                    ):
                        fail("truth_stage_predecessor_id_mismatch", group=list(group))
                    if receipt.get(
                        "predecessor_stage_receipt_sha256"
                    ) != predecessor.get("receipt_sha256"):
                        fail("truth_stage_predecessor_hash_mismatch", group=list(group))
                    predecessor_identity = packets[stage_index - 1].get(
                        WAVE21_TRUTH_IDENTITY_ROOT_FIELD
                    )
                stage_payload = {
                    key: value
                    for key, value in packet.items()
                    if key
                    not in {
                        WAVE21_TRUTH_STAGE_RECEIPT_FIELD,
                        WAVE21_TRUTH_IDENTITY_ROOT_FIELD,
                    }
                }
                expected_identity = stable_sha256(
                    {
                        "schema": WAVE21_TRUTH_IDENTITY_ROOT_SCHEMA,
                        "stage_id": stage_id,
                        "fixed_point_pass": receipt.get("fixed_point_pass"),
                        "predecessor_identity_root_sha256": predecessor_identity,
                        "stage_payload_sha256": stable_sha256(stage_payload),
                    }
                )
                if packet.get(WAVE21_TRUTH_IDENTITY_ROOT_FIELD) != expected_identity:
                    fail("truth_stage_identity_root_mismatch", group=list(group))
            if not receipts:
                fail("truth_stage_chain_empty", group=list(group))
                continue
            stage_ids = [str(row.get("stage_id") or "") for row in receipts]
            final_disposition = receipts[-1].get("disposition")
            if final_disposition == "TERMINAL_NOT_EVALUABLE":
                terminal_ne += 1
            elif final_disposition == "TERMINAL_EVALUABLE_NONTRADE":
                terminal_nontrade += 1
            if kind == "source_terminal":
                source_terminal_slots.append(slot)
                if stage_ids != ["source_lineage", "terminal_disposition"]:
                    fail("source_terminal_stage_sequence_invalid", group=list(group))
                continue
            if kind != "candidate" or not isinstance(candidate_ordinal, int):
                continue
            candidate_chain_ordinals.append(candidate_ordinal)
            index = 0

            def require(stage_id: str, fixed_pass: int) -> bool:
                nonlocal index
                if index >= len(receipts) or receipts[index].get("stage_id") != stage_id:
                    fail(
                        "candidate_stage_sequence_invalid",
                        group=list(group),
                        expected_stage=stage_id,
                        stages=stage_ids,
                    )
                    return False
                if receipts[index].get("fixed_point_pass") != fixed_pass:
                    fail(
                        "candidate_stage_fixed_point_pass_mismatch",
                        group=list(group),
                        stage=stage_id,
                    )
                index += 1
                return True

            def terminal(allow_evaluable: bool) -> bool:
                nonlocal index
                if index >= len(receipts) or receipts[index].get("stage_id") != (
                    "terminal_disposition"
                ):
                    return False
                if index != len(receipts) - 1:
                    fail("truth_stage_after_terminal", group=list(group))
                if (
                    receipts[index].get("disposition")
                    == "TERMINAL_EVALUABLE_NONTRADE"
                    and not allow_evaluable
                ):
                    fail("premature_evaluable_nontrade_terminal", group=list(group))
                index += 1
                return True

            if not require("source_lineage", 0):
                continue
            if terminal(False):
                continue
            if not require("candidate_decision_fingerprint", 0):
                continue
            fingerprint_packet = packets[index - 1]
            if not _is_sha256(
                fingerprint_packet.get("candidate_decision_fingerprint_sha256")
            ):
                fail("stage_candidate_fingerprint_invalid", group=list(group))
            atoms = fingerprint_packet.get("candidate_decision_fingerprint_atoms")
            if not isinstance(atoms, Mapping) or _forbidden_candidate_atom_paths(atoms):
                fail("stage_candidate_fingerprint_atoms_invalid", group=list(group))
            if terminal(False):
                continue
            fixed_pass = 0
            committed = False
            while index < len(packets):
                if fixed_pass >= 3:
                    fail("fixed_point_pass_limit_exceeded", group=list(group))
                    break
                if not require("selector_verdict", fixed_pass):
                    break
                selector_packet = packets[index - 1]
                if not _is_sha256(
                    selector_packet.get("selector_v4_verdict_hash_sha256")
                ):
                    fail("stage_selector_verdict_hash_invalid", group=list(group))
                if selector_packet.get(
                    "selector_v4_verdict_predecessor_candidate_decision_fingerprint_sha256"
                ) != fingerprint_packet.get("candidate_decision_fingerprint_sha256"):
                    fail("stage_selector_fingerprint_predecessor_mismatch", group=list(group))
                selector_by_pass[(window_key(slot), fixed_pass)].add(
                    candidate_ordinal
                )
                if terminal(False):
                    break
                if not require("scheduler_option", fixed_pass):
                    break
                scheduler = packets[index - 1]
                scheduler_by_pass[(window_key(slot), fixed_pass)].add(
                    candidate_ordinal
                )
                selected = scheduler.get("scheduler_candidate_option_selected")
                disposition = scheduler.get(
                    "scheduler_candidate_option_disposition"
                )
                if not isinstance(selected, bool):
                    fail("scheduler_option_selected_not_boolean", group=list(group))
                    selected = False
                if disposition not in {
                    "RISK_BEARING_EVALUATED",
                    "TERMINAL_EVALUABLE_NONTRADE",
                    "TERMINAL_NOT_EVALUABLE",
                }:
                    fail("scheduler_option_disposition_invalid", group=list(group))
                if selected and disposition != "RISK_BEARING_EVALUATED":
                    fail("scheduler_selected_terminal_option", group=list(group))
                if scheduler.get("scheduler_option_is_final_order_authority") is True:
                    fail("scheduler_claims_final_order_authority", group=list(group))
                if scheduler.get(
                    "scheduler_option_is_executable_instance_authority"
                ) is True:
                    fail("scheduler_claims_executable_authority", group=list(group))
                if terminal(False):
                    break
                if selected:
                    complete = True
                    for stage_id in (
                        "continuous_risk_sizing",
                        "final_order",
                        "pretrade_expected_cost",
                        "order_fillability",
                    ):
                        if not require(stage_id, fixed_pass):
                            complete = False
                            break
                        if terminal(False):
                            complete = False
                            break
                    if not complete:
                        break
                if not require("fixed_point_convergence", fixed_pass):
                    break
                convergence = packets[index - 1]
                convergence_by_pass[(window_key(slot), fixed_pass)].add(
                    candidate_ordinal
                )
                convergence_packets[(window_key(slot), fixed_pass)].append(
                    convergence
                )
                stable = convergence.get(
                    "order_policy_fixed_point_adjacent_stable"
                )
                if not isinstance(stable, bool):
                    fail("fixed_point_stability_not_boolean", group=list(group))
                    stable = False
                if terminal(not selected and stable):
                    break
                if not stable:
                    fixed_pass += 1
                    continue
                committed = True
                if not selected:
                    fail("stable_nonselected_chain_missing_terminal", group=list(group))
                    break
                downstream_complete = True
                for stage_id in (
                    "executable_instance",
                    "fill",
                    "exit",
                    "post_lifecycle_component_cost",
                    "accounting",
                ):
                    if not require(stage_id, fixed_pass):
                        downstream_complete = False
                        break
                    stage_status = packets[index - 1].get(
                        "wave21_truth_stage_status"
                    )
                    if terminal(stage_status == "EVALUABLE_NONTRADE"):
                        downstream_complete = False
                        break
                if downstream_complete and index == len(packets):
                    complete_accounted += 1
                break
            if index < len(packets):
                fail(
                    "candidate_chain_unconsumed_stage_suffix",
                    group=list(group),
                    suffix=stage_ids[index:],
                )
            if committed and fixed_pass == 0:
                fail("fixed_point_committed_without_adjacent_pass", group=list(group))

        truth_chain_model_active = bool(self.stage_rows)
        if truth_chain_model_active:
            if candidate_rows_missing_truth_ordinal:
                fail(
                    "candidate_occurrence_ordinal_missing_under_truth_chain_model",
                    missing_count=candidate_rows_missing_truth_ordinal,
                )
            if sorted(candidate_chain_ordinals) != candidate_ordinals:
                fail("candidate_occurrence_chain_conservation_mismatch")
            if sorted(source_terminal_slots) != sorted(zero_slot_keys):
                fail("zero_candidate_source_terminal_conservation_mismatch")

        # Occurrence-union DAG: every candidate occurrence must end in exactly
        # one disjoint terminal disposition -- missed | trade |
        # terminal_unfilled -- unless a truth-chain covers it.
        def _occurrence_key(row: Mapping[str, Any]) -> str:
            return str(
                row.get("canonical_replay_candidate_instance_key") or ""
            ).strip()

        candidate_key_set = set(candidate_instance_keys)
        chain_covered_keys = {
            key
            for key, key_ordinal in candidate_key_truth_ordinal.items()
            if key_ordinal is not None
            and key_ordinal in set(candidate_chain_ordinals)
        }
        missed_keys: set[str] = set()
        for row_index, row in enumerate(self.missed_rows):
            key = _occurrence_key(row)
            if not key:
                fail("missed_row_instance_key_missing", missed_row_index=row_index)
                continue
            if key not in candidate_key_set:
                fail(
                    "missed_row_without_candidate_occurrence",
                    occurrence_key=key,
                )
                continue
            missed_keys.add(key)
        order_statuses_by_key: dict[str, list[str]] = {}
        for row_index, row in enumerate(self.order_rows):
            key = _occurrence_key(row)
            if not key:
                fail("order_row_instance_key_missing", order_row_index=row_index)
                continue
            if key not in candidate_key_set:
                fail(
                    "order_row_without_candidate_occurrence",
                    occurrence_key=key,
                )
                continue
            order_statuses_by_key.setdefault(key, []).append(
                str(row.get("order_status") or "")
            )
        trade_keys: set[str] = set()
        for row_index, row in enumerate(self.trade_rows):
            key = _occurrence_key(row)
            if not key:
                fail("trade_row_instance_key_missing", trade_row_index=row_index)
                continue
            if key not in candidate_key_set:
                fail(
                    "trade_row_without_candidate_occurrence",
                    occurrence_key=key,
                )
                continue
            if key not in order_statuses_by_key:
                fail("trade_without_order", occurrence_key=key)
                continue
            trade_keys.add(key)
        order_key_set = set(order_statuses_by_key)
        for key in sorted(missed_keys & order_key_set):
            fail("occurrence_both_missed_and_ordered", occurrence_key=key)
        terminal_unfilled_keys: set[str] = set()
        for key in sorted(order_key_set - trade_keys):
            if any(
                status == "filled" for status in order_statuses_by_key[key]
            ):
                fail("filled_order_without_trade", occurrence_key=key)
                continue
            terminal_unfilled_keys.add(key)
        undisposed = sorted(
            candidate_key_set
            - missed_keys
            - order_key_set
            - chain_covered_keys
        )
        for key in undisposed[:50]:
            fail(
                "candidate_occurrence_without_terminal_disposition",
                occurrence_key=key,
            )
        disposition_conservation_exact = (
            not undisposed
            and not (missed_keys & order_key_set)
            and len(missed_keys) + len(trade_keys) + len(terminal_unfilled_keys)
            == len(candidate_key_set - chain_covered_keys)
        )
        if not disposition_conservation_exact:
            fail(
                "occurrence_disposition_conservation_inexact",
                candidate_occurrence_count=len(candidate_key_set),
                chain_covered_count=len(chain_covered_keys),
                missed_count=len(missed_keys),
                trade_count=len(trade_keys),
                terminal_unfilled_count=len(terminal_unfilled_keys),
                undisposed_count=len(undisposed),
            )
        for key, selector_ordinals in sorted(selector_by_pass.items()):
            scheduler_ordinals = scheduler_by_pass.get(key, set())
            if scheduler_ordinals and scheduler_ordinals != selector_ordinals:
                fail("scheduler_window_option_conservation_mismatch", window_pass=list(key))
            convergence_ordinals = convergence_by_pass.get(key, set())
            if convergence_ordinals and convergence_ordinals != scheduler_ordinals:
                fail("fixed_point_window_candidate_conservation_mismatch", window_pass=list(key))
        for key, packets in sorted(convergence_packets.items()):
            atom_roots = {
                stable_sha256(packet.get("order_policy_fixed_point_atoms"))
                for packet in packets
            }
            fixed_keys = {
                packet.get("order_policy_fixed_point_key_sha256")
                for packet in packets
            }
            if len(atom_roots) != 1 or len(fixed_keys) != 1:
                fail("fixed_point_window_atoms_not_identical", window_pass=list(key))
                continue
            atoms = packets[0].get("order_policy_fixed_point_atoms")
            atoms = atoms if isinstance(atoms, Mapping) else {}
            expected_fixed_key = stable_sha256(
                {
                    "schema": "gtos.wave21.order_policy_window_fixed_point.v1",
                    **dict(atoms),
                }
            )
            if next(iter(fixed_keys)) != expected_fixed_key:
                fail("fixed_point_window_key_mismatch", window_pass=list(key))
            option_atoms = atoms.get("candidate_option_atoms")
            option_ordinals = {
                row.get("candidate_occurrence_ordinal")
                for row in option_atoms
            } if isinstance(option_atoms, list) else set()
            if option_ordinals != scheduler_by_pass.get(key, set()):
                fail(
                    "fixed_point_candidate_option_atoms_conservation_mismatch",
                    window_pass=list(key),
                )

        mandatory_counts = {
            stage_id: stage_counts.get(stage_id, 0)
            for stage_id in (
                "source_lineage",
                "candidate_decision_fingerprint",
                "selector_verdict",
                "scheduler_option",
                "continuous_risk_sizing",
                "final_order",
                "pretrade_expected_cost",
                "order_fillability",
                "fixed_point_convergence",
                "executable_instance",
                "fill",
                "exit",
                "post_lifecycle_component_cost",
                "accounting",
            )
        }
        body = {
            "schema": STAGE_DAG_SCHEMA,
            "dag_model": "candidate_occurrence_disjoint_terminal_v1",
            "asof_source_slot_count": len(self.asof_rows),
            "zero_candidate_source_slot_count": len(zero_slot_keys),
            "candidate_occurrence_count": len(self.candidate_rows),
            "candidate_pre_scheduler_contract_failure_count": candidate_failure_count,
            "occurrence_disposition_counts": {
                "missed": len(missed_keys),
                "trade": len(trade_keys),
                "terminal_unfilled": len(terminal_unfilled_keys),
                "truth_chain_covered": len(chain_covered_keys),
            },
            "order_occurrence_count": len(order_key_set),
            "occurrence_disposition_conservation_exact": (
                disposition_conservation_exact
            ),
            "truth_chain_model_active": truth_chain_model_active,
            "expected_chain_count": len(self.candidate_rows) + len(zero_slot_keys),
            "observed_chain_count": len(groups),
            "truth_stage_row_count": len(self.stage_rows),
            "candidate_chain_count": len(candidate_chain_ordinals),
            "source_terminal_chain_count": len(source_terminal_slots),
            "terminal_not_evaluable_chain_count": terminal_ne,
            "terminal_evaluable_nontrade_chain_count": terminal_nontrade,
            "complete_accounted_chain_count": complete_accounted,
            "stage_counts": dict(sorted(stage_counts.items())),
            "stage_status_counts": dict(sorted(stage_status_counts.items())),
            "mandatory_result_stage_counts": mandatory_counts,
            "fixed_point_window_pass_count": len(selector_by_pass),
            "scheduler_is_order_or_exec_authority": False,
            "legacy_candidate_to_order_geometry_audit_used": False,
            "failure_count": len(failures),
            "failures": failures,
            "status": "PASS" if not failures else "FAIL",
        }
        return {**body, "stage_dag_audit_root_sha256": stable_sha256(body)}


def _verify_decision_conservation(
    *,
    stored: Mapping[str, Any],
    receipt: Mapping[str, Any],
    source_symbols: Sequence[str],
    campaign_days: Sequence[str],
    asof_count: int,
    asof_keys: set[tuple[str, str]],
    asof_day_counts: Counter[str],
    raw_candidate_count: int,
    emitted_candidate_count: int,
    truncated_candidate_count: int,
    generator_eligible_count: int,
    source_dispositions: Counter[str],
    candidate_count: int,
    candidate_coverage: Counter[tuple[str, str, str]],
) -> dict[str, Any]:
    stored_body = dict(stored)
    stored_root = stored_body.pop("conservation_root_sha256", None)
    if stored_root != stable_sha256(stored_body):
        raise VerificationError("decision_conservation_root_mismatch")
    if stored.get("status") != "PASS" or stored.get("violations") not in ([], ()): 
        raise VerificationError("producer_decision_conservation_not_pass")
    if receipt.get("decision_conservation") != stored:
        raise VerificationError("receipt_decision_conservation_binding_mismatch")

    generation = receipt.get("generation_trace")
    if not isinstance(generation, Mapping):
        raise VerificationError("receipt_generation_trace_missing")
    fingerprint = receipt.get("comparator_fingerprint")
    if not isinstance(fingerprint, Mapping):
        raise VerificationError("receipt_comparator_fingerprint_missing")
    if stable_sha256(generation) != fingerprint.get("generation_trace_root_sha256"):
        raise VerificationError("generation_trace_root_mismatch")
    if generation.get("raw_generation_executed") is not True:
        raise VerificationError("generation_trace_raw_generation_not_executed")
    if generation.get("prepared_candidate_payload_consumed") is not False:
        raise VerificationError("generation_trace_prepared_payload_not_false")
    if generation.get("candidate_population_truncated") is not False:
        raise VerificationError("generation_trace_candidate_population_truncated")
    if generation.get("generation_audit_transport_workaround_applied") is not False:
        raise VerificationError("generation_trace_workaround_applied")
    if int(generation.get("generator_future_or_forming_bar_violation_count") or 0):
        raise VerificationError("generation_trace_future_bar_violation")

    symbol_count = len(set(source_symbols))
    if symbol_count == 0:
        raise VerificationError("decision_conservation_source_symbols_empty")
    if len(asof_keys) != asof_count:
        raise VerificationError("decision_conservation_duplicate_source_slots")
    expected_by_day = {
        day: int(asof_day_counts.get(day, 0)) for day in campaign_days
    }
    decision_windows_by_day: dict[str, int] = {}
    for day, count in expected_by_day.items():
        if count % symbol_count:
            raise VerificationError(
                f"decision_conservation_partial_symbol_window:{day}:{count}"
            )
        decision_windows_by_day[day] = count // symbol_count
    if stored.get("expected_decision_slot_count") != asof_count:
        raise VerificationError("decision_conservation_expected_slot_mismatch")
    if stored.get("observed_asof_row_count") != asof_count:
        raise VerificationError("decision_conservation_observed_asof_mismatch")
    if stored.get("silent_continue_or_missing_slot_count") != 0:
        raise VerificationError("decision_conservation_silent_slot_gap")
    if stored.get("duplicate_decision_slot_count") != 0:
        raise VerificationError("decision_conservation_duplicate_slot_receipt")
    if stored.get("expected_slots_by_day") != expected_by_day:
        raise VerificationError("decision_conservation_day_slot_counts_mismatch")
    if stored.get("decision_windows_by_day") != decision_windows_by_day:
        raise VerificationError("decision_conservation_day_window_counts_mismatch")
    if stored.get("generator_eligible_slot_count") != generator_eligible_count:
        raise VerificationError("decision_conservation_generator_eligible_mismatch")
    if stored.get("generator_call_count") != generation.get("generator_call_count"):
        raise VerificationError("decision_conservation_generator_call_mismatch")
    if generation.get("generator_call_count") != generator_eligible_count:
        raise VerificationError("decision_conservation_generator_call_eligible_mismatch")
    if stored.get("raw_generated_candidate_count") != raw_candidate_count:
        raise VerificationError("decision_conservation_raw_candidate_mismatch")
    if generation.get("raw_generated_candidate_count") != raw_candidate_count:
        raise VerificationError("generation_trace_raw_candidate_mismatch")
    if stored.get("emitted_candidate_count") != emitted_candidate_count:
        raise VerificationError("decision_conservation_emitted_candidate_mismatch")
    if emitted_candidate_count != candidate_count:
        raise VerificationError("decision_conservation_candidate_ledger_mismatch")
    if stored.get("candidate_ledger_row_count") != candidate_count:
        raise VerificationError("decision_conservation_candidate_count_mismatch")
    if truncated_candidate_count != 0 or stored.get("truncated_candidate_count") != 0:
        raise VerificationError("decision_conservation_truncation_nonzero")
    if stored.get("generator_refusal_or_source_disposition_counts") != dict(
        sorted(source_dispositions.items())
    ):
        raise VerificationError("decision_conservation_source_dispositions_mismatch")

    coverage_rows = stored.get("coverage_cells")
    if not isinstance(coverage_rows, Sequence):
        raise VerificationError("decision_conservation_coverage_cells_missing")
    expected_coverage_count = (
        len(set(source_symbols)) * len(GTOS_BROAD_ORIGIN_FAMILIES) * 2
    )
    if len(coverage_rows) != expected_coverage_count:
        raise VerificationError("decision_conservation_coverage_denominator_incomplete")
    seen_cells: set[tuple[str, str, str]] = set()
    for raw in coverage_rows:
        if not isinstance(raw, Mapping):
            raise VerificationError("decision_conservation_coverage_row_invalid")
        cell = (
            str(raw.get("symbol") or ""),
            str(raw.get("origin_family") or ""),
            str(raw.get("side") or ""),
        )
        if cell in seen_cells:
            raise VerificationError("decision_conservation_coverage_cell_duplicate")
        seen_cells.add(cell)
        if int(raw.get("candidate_count") or 0) != int(candidate_coverage[cell]):
            raise VerificationError("decision_conservation_coverage_cell_count_mismatch")
    expected_cells = {
        (symbol, family, side)
        for symbol in sorted(set(source_symbols))
        for family in GTOS_BROAD_ORIGIN_FAMILIES
        for side in ("BUY", "SELL")
    }
    if seen_cells != expected_cells:
        raise VerificationError("decision_conservation_coverage_cells_not_exact_product")

    return {
        "status": "PASS",
        "observed_asof_row_count": asof_count,
        "unique_source_slot_count": len(asof_keys),
        "decision_windows_by_day": decision_windows_by_day,
        "raw_generated_candidate_count": raw_candidate_count,
        "emitted_candidate_count": emitted_candidate_count,
        "candidate_ledger_row_count": candidate_count,
        "truncated_candidate_count": truncated_candidate_count,
        "coverage_cell_count": len(seen_cells),
        "conservation_root_sha256": stored_root,
    }


def _economic_chain_key(row: Mapping[str, Any]) -> str:
    explicit = row.get("__economic_chain_key")
    if _is_sha256(explicit):
        return str(explicit)
    identity = row.get("__identity")
    identity = identity if isinstance(identity, Mapping) else row
    return stable_sha256(
        {
            "chain_kind": identity.get(WAVE21_TRUTH_CHAIN_KIND_FIELD),
            "source_slot_key": identity.get(WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD),
            "candidate_occurrence_ordinal": identity.get(
                WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD
            ),
        }
    )


def _recompute_serialized_economic_projection(
    result: Mapping[str, Any],
    *,
    result_scope: str,
    denominator_symbols: Sequence[str],
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Project only serialized post-lifecycle cost and accounting truth stages."""

    ledger_map = result["ledgers"] if ledgers is None else ledgers
    pretrade_by_chain: dict[str, Mapping[str, Any]] = {}
    post_cost_by_chain: dict[str, tuple[dict[str, Any], Mapping[str, Any]]] = {}
    accounting_by_chain: dict[str, tuple[dict[str, Any], Mapping[str, Any]]] = {}
    structural_failures: list[dict[str, Any]] = []
    pretrade_stage_row_count = 0
    for row_ordinal, native in enumerate(
        ledger_map.get(WAVE21_TRUTH_STAGE_LEDGER, ())
    ):
        row = dict(native)
        chain_key = _economic_chain_key(row)
        packet = row.get(WAVE21_TRUTH_STAGE_PACKET_FIELD)
        if not chain_key or not isinstance(packet, Mapping):
            continue
        receipt = packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD)
        stage_id = str(
            receipt.get("stage_id")
            if isinstance(receipt, Mapping)
            else packet.get("wave21_truth_stage_id") or ""
        )
        if stage_id == "pretrade_expected_cost":
            pretrade_stage_row_count += 1
            pretrade_by_chain[chain_key] = dict(packet)
        elif stage_id == "post_lifecycle_component_cost":
            if chain_key in post_cost_by_chain:
                structural_failures.append(
                    {
                        "reason": "duplicate_post_lifecycle_cost_stage_for_chain",
                        "chain_key": chain_key,
                        "stage_row_ordinal": row_ordinal,
                    }
                )
            post_cost_by_chain[chain_key] = (row, dict(packet))
        elif stage_id == "accounting":
            if chain_key in accounting_by_chain:
                structural_failures.append(
                    {
                        "reason": "duplicate_accounting_stage_for_chain",
                        "chain_key": chain_key,
                        "stage_row_ordinal": row_ordinal,
                    }
                )
            accounting_by_chain[chain_key] = (row, dict(packet))

    component_sums = {field: 0.0 for field in COST_COMPONENT_FIELDS}
    component_counts = {field: 0 for field in COST_COMPONENT_FIELDS}
    cost_coverage: Counter[str] = Counter()
    cost_failures: list[dict[str, Any]] = list(structural_failures)
    complete_cost_chain_count = 0
    lifecycle_symbols: set[str] = set()
    tick_subset_cost_chain_count = 0
    for chain_key, (row, payload) in post_cost_by_chain.items():
        stage_assessment = _post_lifecycle_cost_stage_assessment(payload)
        nested = stage_assessment["nested"]
        assessment = stage_assessment["assessment"]
        if isinstance(nested, Mapping):
            lifecycle = nested.get("lifecycle")
            lifecycle = lifecycle if isinstance(lifecycle, Mapping) else {}
            symbol = str(lifecycle.get("symbol") or row.get("symbol") or "")
            if symbol:
                lifecycle_symbols.add(symbol)
            cost_coverage[str(nested.get("coverage") or "MISSING")] += 1
        else:
            symbol = str(row.get("symbol") or "")
            cost_coverage["MISSING"] += 1
        if not stage_assessment["complete"]:
            if len(cost_failures) < 100:
                cost_failures.append(
                    {
                        "reason": "post_lifecycle_component_cost_not_complete",
                        "chain_key": chain_key,
                        "identity": dict(row.get("__identity") or {}),
                        "failures": stage_assessment["failures"]
                        + list(assessment["failures"]),
                    }
                )
            continue
        complete_cost_chain_count += 1
        if symbol in TICK_COVERED_SYMBOLS:
            tick_subset_cost_chain_count += 1
        for field, value in assessment["component_values"].items():
            component_sums[field] += float(value)
            component_counts[field] += 1

    accounting_sums = {
        "gross_result_r": 0.0,
        "post_lifecycle_total_cost_r": 0.0,
        "net_result_r": 0.0,
    }
    accounting_counts = {field: 0 for field in accounting_sums}
    accounting_failures: list[dict[str, Any]] = []
    tick_subset_accounting_count = 0
    tick_subset_net_result_r = 0.0

    def finite_number(value: Any) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        number = float(value)
        return number if math.isfinite(number) else None

    for chain_key, (row, payload) in accounting_by_chain.items():
        failures: list[str] = []
        cost_pair = post_cost_by_chain.get(chain_key)
        if cost_pair is None:
            failures.append("accounting_post_lifecycle_cost_stage_missing")
            stage_assessment = None
            nested = None
        else:
            stage_assessment = _post_lifecycle_cost_stage_assessment(cost_pair[1])
            nested = stage_assessment["nested"]
            if not stage_assessment["complete"]:
                failures.append("accounting_post_lifecycle_cost_not_complete")
        if payload.get("post_lifecycle_accounting_schema") != (
            POST_LIFECYCLE_ACCOUNTING_SCHEMA
        ):
            failures.append("post_lifecycle_accounting_schema_invalid")
        if payload.get("status") != "MATERIALIZED":
            failures.append("post_lifecycle_accounting_status_not_materialized")
        if payload.get("failures") != []:
            failures.append("post_lifecycle_accounting_failures_not_empty")
        gross = finite_number(payload.get("gross_result_r"))
        total = finite_number(payload.get("post_lifecycle_total_cost_r"))
        net = finite_number(payload.get("net_result_r"))
        if gross is None:
            failures.append("accounting_gross_result_r_not_finite")
        expected_total = (
            stage_assessment["assessment"]["component_sum_r"]
            if stage_assessment is not None and stage_assessment["complete"]
            else None
        )
        if total is None or total != expected_total:
            failures.append("accounting_post_lifecycle_total_cost_mismatch")
        if gross is None or total is None or net != gross - total:
            failures.append("accounting_net_result_identity_mismatch")
        provenance = payload.get("gross_result_provenance")
        if not isinstance(provenance, str) or not provenance.strip():
            failures.append("accounting_gross_result_provenance_missing")
        if not _is_sha256(
            payload.get("gross_result_source_stage_receipt_sha256")
        ):
            failures.append("accounting_gross_result_source_receipt_invalid")
        expected_cost_sha = (
            stage_assessment["nested_sha256"]
            if stage_assessment is not None
            else None
        )
        if payload.get("post_lifecycle_component_cost_sha256") != (
            expected_cost_sha
        ):
            failures.append("accounting_post_lifecycle_cost_hash_mismatch")
        if isinstance(nested, Mapping):
            if payload.get("post_lifecycle_cost_coverage") != nested.get(
                "coverage"
            ):
                failures.append("accounting_cost_coverage_mismatch")
            if payload.get("broker_realized_status") != nested.get(
                "broker_realized_status"
            ):
                failures.append("accounting_broker_realized_status_mismatch")
        if payload.get("result_use_scope") != (
            "SIMULATED_POST_LIFECYCLE_ECONOMICS_NOT_BROKER_REALIZED"
        ):
            failures.append("accounting_result_use_scope_invalid")
        atoms = payload.get("post_lifecycle_accounting_atoms")
        if not isinstance(atoms, Mapping):
            failures.append("post_lifecycle_accounting_atoms_missing")
        else:
            if any(payload.get(key) != value for key, value in atoms.items()):
                failures.append("post_lifecycle_accounting_atoms_mismatch")
            if payload.get("post_lifecycle_accounting_packet_sha256") != (
                stable_sha256(
                    {
                        "schema": POST_LIFECYCLE_ACCOUNTING_SCHEMA,
                        "atoms": atoms,
                    }
                )
            ):
                failures.append("post_lifecycle_accounting_hash_mismatch")
        failures = list(dict.fromkeys(failures))
        if failures:
            if len(accounting_failures) < 100:
                accounting_failures.append(
                    {
                        "chain_key": chain_key,
                        "identity": dict(row.get("__identity") or {}),
                        "failures": failures,
                    }
                )
            continue
        assert gross is not None and total is not None and net is not None
        accounting_sums["gross_result_r"] += gross
        accounting_sums["post_lifecycle_total_cost_r"] += total
        accounting_sums["net_result_r"] += net
        for field in accounting_counts:
            accounting_counts[field] += 1
        symbol = ""
        if isinstance(nested, Mapping):
            lifecycle = nested.get("lifecycle")
            if isinstance(lifecycle, Mapping):
                symbol = str(lifecycle.get("symbol") or "")
        if not symbol:
            symbol = str(row.get("symbol") or "")
        if symbol in TICK_COVERED_SYMBOLS:
            tick_subset_accounting_count += 1
            tick_subset_net_result_r += net

    missing_accounting_chains = sorted(
        set(post_cost_by_chain) - set(accounting_by_chain)
    )
    if missing_accounting_chains:
        accounting_failures.extend(
            {
                "chain_key": chain_key,
                "failures": ["post_lifecycle_cost_chain_missing_accounting"],
            }
            for chain_key in missing_accounting_chains[:100]
        )
    exact_denominator = tuple(
        sorted(set(str(symbol) for symbol in denominator_symbols))
    )
    all24_denominator_exact = exact_denominator == tuple(
        sorted(GTOS_24_SYMBOL_SURFACE)
    )
    all24_ordered_tick_complete = all24_denominator_exact and set(
        exact_denominator
    ).issubset(TICK_COVERED_SYMBOLS)
    complete_economics = bool(post_cost_by_chain) and (
        len(cost_failures) == 0
        and len(accounting_failures) == 0
        and len(accounting_by_chain) == len(post_cost_by_chain)
    )
    aggregate_status = (
        "NOT_EVALUABLE_POST_LIFECYCLE_COST_STAGE_ABSENT"
        if not post_cost_by_chain
        else "NOT_EVALUABLE_POST_LIFECYCLE_COMPONENT_OR_ACCOUNTING_GAPS"
        if not complete_economics
        else "NOT_EVALUABLE_ALL24_ORDERED_BID_ASK_COVERAGE_INCOMPLETE"
        if not all24_ordered_tick_complete and result_scope != "deterministic_smoke"
        else "SIMULATED_POST_LIFECYCLE_ECONOMICS_NOT_BROKER_REALIZED"
    )
    return {
        "legacy_candidate_or_trade_expected_cost_consumed": False,
        "pretrade_expected_cost_projection": {
            "status": "FORECAST_ESTIMATE_ONLY_NOT_FINAL_ECONOMICS",
            "stage": "pretrade_expected_cost",
            "stage_row_count": pretrade_stage_row_count,
            "candidate_chain_count": len(pretrade_by_chain),
            "component_values_summed": False,
            "forecast_substituted_for_post_lifecycle_cost": False,
        },
        "post_lifecycle_component_cost_projection": {
            "schema": POST_LIFECYCLE_COMPONENT_COST_SCHEMA,
            "denominator_chain_count": len(post_cost_by_chain),
            "complete_chain_count": complete_cost_chain_count,
            "not_evaluable_chain_count": (
                len(post_cost_by_chain) - complete_cost_chain_count
            ),
            "component_field_sums": {
                key: round(value, 12) for key, value in component_sums.items()
            },
            "component_field_counts": component_counts,
            "coverage_counts": dict(sorted(cost_coverage.items())),
            "failure_count": len(cost_failures),
            "failures": cost_failures[:100],
            "forecast_components_reused": False,
            "broker_realized": False,
        },
        "post_lifecycle_accounting_projection": {
            "schema": POST_LIFECYCLE_ACCOUNTING_SCHEMA,
            "denominator_chain_count": len(accounting_by_chain),
            "complete_chain_count": accounting_counts["net_result_r"],
            "field_sums": {
                key: round(value, 12) for key, value in accounting_sums.items()
            },
            "field_counts": accounting_counts,
            "missing_accounting_chain_count": len(missing_accounting_chains),
            "failure_count": len(accounting_failures),
            "failures": accounting_failures[:100],
            "gross_minus_cost_equals_net": not accounting_failures,
            "broker_realized": False,
        },
        "economics_complete_for_all_materialized_lifecycles": complete_economics,
        "aggregate_economic_headline_status": aggregate_status,
        "all_24_output": {
            "scope": "generator_selector_scheduler_plus_m1_modelled_lifecycle",
            "denominator_symbols": list(exact_denominator),
            "denominator_is_exact_gtos_24": all24_denominator_exact,
            "post_lifecycle_symbols": sorted(lifecycle_symbols),
            "ordered_bid_ask_complete": all24_ordered_tick_complete,
            "broker_true": False,
            "headline_allowed": False,
            "missing_ordered_bid_ask_symbols": sorted(
                set(GTOS_24_SYMBOL_SURFACE) - set(TICK_COVERED_SYMBOLS)
            ),
        },
        "ordered_tick_subset_output": {
            "symbols": list(TICK_COVERED_SYMBOLS),
            "post_lifecycle_cost_chain_count": tick_subset_cost_chain_count,
            "accounting_chain_count": tick_subset_accounting_count,
            "net_result_r_sum": round(tick_subset_net_result_r, 12),
            "transfer_to_other_20_allowed": False,
            "broker_true": False,
            "result_use_scope": (
                "SIMULATED_POST_LIFECYCLE_ECONOMICS_NOT_BROKER_REALIZED"
            ),
        },
        "result_scope": result_scope,
    }


def verify(
    *,
    stage_ledger: Path,
    fingerprint_path: Path,
    receipt_path: Path,
) -> dict[str, Any]:
    fingerprint = _load_rooted_json(fingerprint_path, "fingerprint_root_sha256")
    receipt = _load_rooted_json(receipt_path, "receipt_root_sha256")
    if (
        receipt.get("comparator_fingerprint", {}).get("fingerprint_root_sha256")
        != fingerprint["fingerprint_root_sha256"]
    ):
        raise VerificationError("receipt_fingerprint_binding_mismatch")
    input_manifest = receipt.get("inputs")
    if not isinstance(input_manifest, Mapping):
        raise VerificationError("receipt_input_manifest_missing")
    input_checks = _verify_input_manifest(
        input_manifest=input_manifest, fingerprint=fingerprint
    )
    if receipt.get("raw_generation_executed") is not True:
        raise VerificationError("receipt_raw_generation_not_executed")
    if receipt.get("prepared_candidate_payload_consumed") is not False:
        raise VerificationError("receipt_prepared_candidate_payload_not_false")
    if receipt.get("candidate_population_truncated") is not False:
        raise VerificationError("receipt_candidate_population_truncated")
    receipt_status = str(receipt.get("status") or "")
    if receipt_status == "RAW_GENERATION_RESEARCH_TIMEWARP_FULL_FLOW_EXECUTED":
        raise VerificationError("obsolete_unscoped_full_flow_status_forbidden")
    required_boundary = {
        "graph": "research_timewarp",
        "production_parity": False,
        "sizing_authority": "abstract_R_cash_price_distance",
        "broker_lot_sizing_proved": False,
        "production_orchestrator_selector_scheduler_shared_decisions": False,
        "w7_compatibility_packets": "shims_not_shared_decisions",
        "live_correctness_claim_allowed": False,
        "broker_mutation_allowed": False,
    }
    for key, expected in required_boundary.items():
        if receipt.get(key) != expected or fingerprint.get(key) != expected:
            raise VerificationError(f"research_graph_boundary_mismatch:{key}")
    if receipt.get("broker_true_economics_claimed") is not False:
        raise VerificationError("broker_true_economics_claimed")
    broker_boundary = receipt.get("broker_boundary")
    if not isinstance(broker_boundary, Mapping):
        raise VerificationError("broker_mutation_boundary_missing")
    if broker_boundary.get("broker_mutation_enabled") is not False:
        raise VerificationError("broker_mutation_boundary_enabled")
    if int(broker_boundary.get("order_send_attempts") or 0) != 0:
        raise VerificationError("broker_order_send_attempted")

    stage_hashers: dict[str, dict[str, Any]] = {}
    stage_counts: Counter[str] = Counter()
    stage_dispositions: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: {field: Counter() for field in DISPOSITION_FIELDS}
    )
    expected_ordinal: Counter[str] = Counter()
    pretrade_stage_row_count = 0
    pretrade_chains: set[str] = set()
    post_cost_by_chain: dict[
        str, tuple[dict[str, Any], dict[str, Any]]
    ] = {}
    accounting_by_chain: dict[
        str, tuple[dict[str, Any], dict[str, Any]]
    ] = {}
    economic_structural_failures: list[dict[str, Any]] = []
    stage_dag_verifier = _OccurrenceStageDagVerifier()
    asof_keys: set[tuple[str, str]] = set()
    asof_day_counts: Counter[str] = Counter()
    asof_count = 0
    raw_candidate_count = 0
    emitted_candidate_count = 0
    truncated_candidate_count = 0
    generator_eligible_count = 0
    source_dispositions: Counter[str] = Counter()
    candidate_count = 0
    candidate_coverage: Counter[tuple[str, str, str]] = Counter()

    with gzip.open(stage_ledger, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise VerificationError(f"stage_json_invalid:{line_number}") from exc
            if not isinstance(row, dict):
                raise VerificationError(f"stage_row_not_object:{line_number}")
            stage = str(row.get("stage") or "")
            if stage not in fingerprint["stages"]:
                raise VerificationError(f"stage_not_in_fingerprint:{stage}")
            ordinal = row.get("stage_row_ordinal")
            if ordinal != expected_ordinal[stage]:
                raise VerificationError(
                    f"stage_ordinal_mismatch:{stage}:{ordinal}:{expected_ordinal[stage]}"
                )
            expected_ordinal[stage] += 1
            comparison = _comparison(row)
            if row.get("comparison_row_root_sha256") != stable_sha256(comparison):
                raise VerificationError(f"comparison_row_root_mismatch:{stage}:{ordinal}")
            state = stage_hashers.setdefault(
                stage,
                {
                    "comparison": hashlib.sha256(),
                    "serialized": hashlib.sha256(),
                    "identity": hashlib.sha256(),
                },
            )
            state["comparison"].update(canonical_bytes(comparison) + b"\n")
            state["serialized"].update(canonical_bytes(row) + b"\n")
            identity = _identity(row)
            state["identity"].update(canonical_bytes(identity) + b"\n")
            stage_counts[stage] += 1
            observables = row.get("observables")
            if not isinstance(observables, Mapping):
                raise VerificationError(f"observables_not_mapping:{stage}:{ordinal}")
            values = dict(observables)
            if stage == "asof":
                stage_dag_verifier.observe_asof(identity, values)
                asof_count += 1
                symbol = str(identity.get("symbol") or "")
                decision_time = str(identity.get("decision_time_utc") or "")
                asof_keys.add((symbol, decision_time))
                trading_day = str(identity.get("trading_day") or "")
                if trading_day:
                    asof_day_counts[trading_day] += 1
                raw_candidate_count += int(
                    values.get("candidate_generation_raw_count") or 0
                )
                emitted_candidate_count += int(
                    values.get("candidate_generation_emitted_count") or 0
                )
                truncated_candidate_count += int(
                    values.get("candidate_generation_truncated_count") or 0
                )
                raw_status = str(values.get("raw_data_status") or "MISSING")
                source_dispositions[raw_status] += 1
                if raw_status == "live_equivalent_raw_data_built_and_mso_computed":
                    generator_eligible_count += 1
            elif stage == "candidate":
                stage_dag_verifier.observe_candidate(identity, values)
                candidate_count += 1
                candidate_coverage[
                    (
                        str(identity.get("symbol") or ""),
                        str(
                            identity.get("origin_family")
                            or identity.get("candidate_origin_family")
                            or "UNKNOWN"
                        ),
                        str(identity.get("side") or "UNKNOWN").upper(),
                    )
                ] += 1
            elif stage == "missed":
                stage_dag_verifier.observe_missed(identity, values)
            elif stage == "order":
                stage_dag_verifier.observe_order(identity, values)
            elif stage == "trade":
                stage_dag_verifier.observe_trade(identity, values)
            elif stage == WAVE21_TRUTH_STAGE_LEDGER:
                stage_dag_verifier.observe_truth_stage(identity, values)
                chain_key = _economic_chain_key({"__identity": identity})
                stage_packet = values.get(WAVE21_TRUTH_STAGE_PACKET_FIELD)
                if chain_key and isinstance(stage_packet, Mapping):
                    stage_receipt = stage_packet.get(
                        WAVE21_TRUTH_STAGE_RECEIPT_FIELD
                    )
                    stage_id = str(
                        stage_receipt.get("stage_id")
                        if isinstance(stage_receipt, Mapping)
                        else stage_packet.get("wave21_truth_stage_id") or ""
                    )
                    economic_row = {
                        "__identity": dict(identity),
                        WAVE21_TRUTH_CHAIN_KEY_FIELD: chain_key,
                        WAVE21_TRUTH_STAGE_PACKET_FIELD: dict(stage_packet),
                    }
                    if stage_id == "pretrade_expected_cost":
                        pretrade_stage_row_count += 1
                        pretrade_chains.add(chain_key)
                    elif stage_id == "post_lifecycle_component_cost":
                        if chain_key in post_cost_by_chain:
                            economic_structural_failures.append(
                                {
                                    "reason": (
                                        "duplicate_post_lifecycle_cost_stage_for_chain"
                                    ),
                                    "chain_key": chain_key,
                                    "stage_row_ordinal": ordinal,
                                }
                            )
                        post_cost_by_chain[chain_key] = (
                            economic_row,
                            dict(stage_packet),
                        )
                    elif stage_id == "accounting":
                        if chain_key in accounting_by_chain:
                            economic_structural_failures.append(
                                {
                                    "reason": (
                                        "duplicate_accounting_stage_for_chain"
                                    ),
                                    "chain_key": chain_key,
                                    "stage_row_ordinal": ordinal,
                                }
                            )
                        accounting_by_chain[chain_key] = (
                            economic_row,
                            dict(stage_packet),
                        )
            for field in DISPOSITION_FIELDS:
                value = values.get(field)
                if value not in (None, "", [], {}):
                    stage_dispositions[stage][field][str(value)] += 1

    stage_checks: dict[str, Any] = {}
    for stage, expected in fingerprint["stages"].items():
        state = stage_hashers.get(
            stage,
            {
                "comparison": hashlib.sha256(),
                "serialized": hashlib.sha256(),
                "identity": hashlib.sha256(),
            },
        )
        actual = {
            "row_count": int(stage_counts[stage]),
            "comparison_jsonl_stream_sha256": state["comparison"].hexdigest(),
            "serialized_projection_jsonl_stream_sha256": state["serialized"].hexdigest(),
            "identity_jsonl_stream_sha256": state["identity"].hexdigest(),
            "dispositions": {
                field: dict(sorted(counter.items()))
                for field, counter in stage_dispositions[stage].items()
                if counter
            },
        }
        comparison_fields = tuple(actual)
        exact = all(actual[field] == expected.get(field) for field in comparison_fields)
        stage_checks[stage] = {"exact": exact, "actual": actual}
        if not exact:
            raise VerificationError(f"stage_fingerprint_mismatch:{stage}")

    recomputed_stage_dag = stage_dag_verifier.finish()
    expected_stage_dag = fingerprint.get("occurrence_stage_dag_audit")
    if not isinstance(expected_stage_dag, Mapping):
        raise VerificationError("fingerprint_occurrence_stage_dag_missing")
    if stable_sha256(recomputed_stage_dag) != stable_sha256(expected_stage_dag):
        raise VerificationError("independent_occurrence_stage_dag_mismatch")
    if receipt.get("occurrence_stage_dag_audit") != expected_stage_dag:
        raise VerificationError("receipt_occurrence_stage_dag_binding_mismatch")

    stored_conservation = fingerprint.get("decision_conservation")
    if not isinstance(stored_conservation, Mapping):
        raise VerificationError("fingerprint_decision_conservation_missing")
    campaign = input_manifest.get("campaign")
    campaign_days = campaign.get("days") if isinstance(campaign, Mapping) else None
    if not isinstance(campaign_days, Sequence):
        raise VerificationError("campaign_days_missing_for_conservation")
    recomputed_conservation = _verify_decision_conservation(
        stored=stored_conservation,
        receipt=receipt,
        source_symbols=input_checks["source_symbol_denominator"],
        campaign_days=[str(day) for day in campaign_days],
        asof_count=asof_count,
        asof_keys=asof_keys,
        asof_day_counts=asof_day_counts,
        raw_candidate_count=raw_candidate_count,
        emitted_candidate_count=emitted_candidate_count,
        truncated_candidate_count=truncated_candidate_count,
        generator_eligible_count=generator_eligible_count,
        source_dispositions=source_dispositions,
        candidate_count=candidate_count,
        candidate_coverage=candidate_coverage,
    )

    result_scope = str(fingerprint["economics"].get("result_scope") or "")
    source_manifest = input_manifest.get("source_manifest")
    if not isinstance(source_manifest, Mapping):
        raise VerificationError("receipt_source_manifest_missing")
    source_rows = source_manifest.get("sources")
    if not isinstance(source_rows, Sequence):
        raise VerificationError("receipt_source_manifest_rows_missing")
    denominator_symbols = tuple(
        sorted(
            {
                str(row.get("symbol") or "")
                for row in source_rows
                if isinstance(row, Mapping) and row.get("symbol")
            }
        )
    )
    economic_rows: list[dict[str, Any]] = []
    ordered_pretrade_chains = sorted(pretrade_chains)
    for chain_key in ordered_pretrade_chains:
        economic_rows.append(
            {
                WAVE21_TRUTH_CHAIN_KEY_FIELD: chain_key,
                "__economic_chain_key": chain_key,
                WAVE21_TRUTH_STAGE_PACKET_FIELD: {
                    WAVE21_TRUTH_STAGE_RECEIPT_FIELD: {
                        "stage_id": "pretrade_expected_cost"
                    }
                },
                "__identity": {},
            }
        )
    if pretrade_stage_row_count > len(ordered_pretrade_chains):
        if not ordered_pretrade_chains:
            raise VerificationError(
                "pretrade_stage_rows_without_chain_identity"
            )
        economic_rows.extend(
            {
                WAVE21_TRUTH_CHAIN_KEY_FIELD: ordered_pretrade_chains[0],
                "__economic_chain_key": ordered_pretrade_chains[0],
                WAVE21_TRUTH_STAGE_PACKET_FIELD: {
                    WAVE21_TRUTH_STAGE_RECEIPT_FIELD: {
                        "stage_id": "pretrade_expected_cost"
                    }
                },
                "__identity": {},
            }
            for _ in range(
                pretrade_stage_row_count - len(ordered_pretrade_chains)
            )
        )
    economic_rows.extend(
        row for row, _payload in post_cost_by_chain.values()
    )
    economic_rows.extend(
        row for row, _payload in accounting_by_chain.values()
    )
    recomputed_economics = _recompute_serialized_economic_projection(
        {"ledgers": {WAVE21_TRUTH_STAGE_LEDGER: economic_rows}},
        result_scope=result_scope,
        denominator_symbols=denominator_symbols,
    )
    if economic_structural_failures:
        projection = recomputed_economics[
            "post_lifecycle_component_cost_projection"
        ]
        projection["failure_count"] += len(economic_structural_failures)
        projection["failures"] = (
            economic_structural_failures + projection["failures"]
        )[:100]
        recomputed_economics[
            "economics_complete_for_all_materialized_lifecycles"
        ] = False
        recomputed_economics["aggregate_economic_headline_status"] = (
            "NOT_EVALUABLE_POST_LIFECYCLE_COMPONENT_OR_ACCOUNTING_GAPS"
        )
    truth_mode = input_manifest.get("truth_mode")
    if not isinstance(truth_mode, bool):
        raise VerificationError("input_truth_mode_not_exact_boolean")
    mandatory_counts = recomputed_stage_dag.get("mandatory_result_stage_counts")
    mandatory_counts = (
        dict(mandatory_counts) if isinstance(mandatory_counts, Mapping) else {}
    )
    mandatory_zero = sorted(
        stage_id
        for stage_id, count in mandatory_counts.items()
        if int(count or 0) <= 0
    )
    stage_coverage_complete = bool(mandatory_counts) and not mandatory_zero
    expected_hard_failures: list[str] = []
    if truth_mode and recomputed_stage_dag.get("status") != "PASS":
        expected_hard_failures.append("occurrence_stage_dag_failed")
    if truth_mode and not stage_coverage_complete:
        expected_hard_failures.append(
            "mandatory_full_flow_stage_coverage_incomplete"
        )
    if truth_mode and int(
        recomputed_stage_dag.get("candidate_occurrence_count") or 0
    ) <= 0:
        expected_hard_failures.append("truth_candidate_population_empty")
    if truth_mode and int(
        recomputed_stage_dag.get("complete_accounted_chain_count") or 0
    ) <= 0:
        expected_hard_failures.append("truth_complete_accounted_chain_absent")
    if truth_mode and recomputed_economics.get(
        "economics_complete_for_all_materialized_lifecycles"
    ) is not True:
        expected_hard_failures.append("post_lifecycle_economics_not_complete")
    receipt_hard_failures = receipt.get("truth_mode_hard_failures")
    if receipt_hard_failures not in (None, expected_hard_failures):
        raise VerificationError("receipt_truth_hard_failure_set_mismatch")
    if receipt.get("full_flow_stage_coverage_complete") not in (
        None,
        stage_coverage_complete,
    ):
        raise VerificationError("receipt_full_flow_stage_coverage_mismatch")
    if receipt.get("mandatory_stage_zero_counts") not in (None, mandatory_zero):
        raise VerificationError("receipt_mandatory_stage_zero_counts_mismatch")
    result_scope_from_receipt = str(receipt.get("result_scope") or "")
    if truth_mode:
        expected_status = (
            "RAW_GENERATION_RESEARCH_TIMEWARP_HARD_TRUTH_STOP"
            if expected_hard_failures
            else "RAW_GENERATION_RESEARCH_TIMEWARP_TRUTH_FULL_FLOW_EXECUTED"
        )
        if receipt.get("engineering_only") not in (None, False):
            raise VerificationError("truth_receipt_marked_engineering_only")
        if receipt.get("result_bearing_truth_run") not in (
            None,
            not expected_hard_failures,
        ):
            raise VerificationError("truth_result_bearing_flag_mismatch")
    else:
        expected_status = (
            "RAW_GENERATION_ENGINEERING_SMOKE_EXECUTED"
            if result_scope_from_receipt in ("", "deterministic_smoke")
            else "RAW_GENERATION_ENGINEERING_COMPARATOR_EXECUTED"
        )
        if receipt.get("engineering_only") not in (None, True):
            raise VerificationError("engineering_receipt_scope_flag_mismatch")
        if receipt.get("result_bearing_truth_run") not in (None, False):
            raise VerificationError("engineering_receipt_claims_truth_result")
    if receipt_status != expected_status:
        raise VerificationError(
            f"receipt_status_scope_mismatch:{receipt_status}:{expected_status}"
        )

    if stable_sha256(recomputed_economics) != stable_sha256(fingerprint["economics"]):
        raise VerificationError("independent_economics_mismatch")
    body = {
        "schema": VERIFIER_SCHEMA,
        "status": "PASS",
        "producer_summary_imported": False,
        "input_authority_checks": input_checks,
        "recomputed_occurrence_stage_dag_audit": recomputed_stage_dag,
        "recomputed_decision_conservation": recomputed_conservation,
        "stage_checks": stage_checks,
        "recomputed_economics": recomputed_economics,
        "stage_ledger_sha256": file_sha256(stage_ledger),
        "fingerprint_sha256": file_sha256(fingerprint_path),
        "receipt_sha256": file_sha256(receipt_path),
        "fingerprint_root_sha256": fingerprint["fingerprint_root_sha256"],
        "receipt_root_sha256": receipt["receipt_root_sha256"],
        "verifier_code_sha256": file_sha256(Path(__file__).resolve()),
    }
    return {**body, "verification_root_sha256": stable_sha256(body)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-ledger", type=Path, required=True)
    parser.add_argument("--fingerprint", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = verify(
        stage_ledger=args.stage_ledger,
        fingerprint_path=args.fingerprint,
        receipt_path=args.receipt,
    )
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
