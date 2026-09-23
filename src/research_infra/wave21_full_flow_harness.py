"""Wave-21 raw-bar-to-economics research-timewarp harness.

This module is deliberately an adapter, not a trading implementation.  It runs
the existing :mod:`v4_timewarp_simulated_live_research_loop` reducer with
prepared-candidate consumption forbidden, observes calls to the production
broader-origin generator through :class:`V4DecisionCycleCore`, and projects the
native ledgers into compact, hash-bound comparison rows.

The graph proved here is the research timewarp graph.  It is not production
orchestrator parity and its risk units are the replay's abstract R/cash/
price-distance sizing units, not broker lots.
"""

from __future__ import annotations

import argparse
import bisect
import copy
import gzip
import hashlib
import importlib
import inspect
import io
import json
import math
import os
import re
import resource
import subprocess
import sys
import threading
import types
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.components import broader_origin_generators
from src.components.v4_live_replay_decision_core import V4DecisionCycleCore
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp
from src.research_infra.replay_compact_event_sink import ReplayCompactEventSink
from src.research_infra.wave21_full_flow_truth import (
    WAVE21_FULL_FLOW_TRUTH_MODE_KEY,
    wave21_full_flow_truth_mode_enabled,
)


HARNESS_REPO_ROOT = Path(__file__).resolve().parents[2]


def active_target_root() -> Path:
    source = inspect.getsourcefile(timewarp)
    if source is None:
        raise FullFlowHarnessError("target_timewarp_source_path_missing")
    return Path(source).resolve().parents[2]


SCHEMA = "gtos.wave21.research_timewarp_full_flow.v1"
STAGE_ROW_SCHEMA = f"{SCHEMA}.stage_row"
FINGERPRINT_SCHEMA = f"{SCHEMA}.comparator_fingerprint"
RECEIPT_SCHEMA = f"{SCHEMA}.run_receipt"
FIXTURE_SCHEMA = f"{SCHEMA}.deterministic_fixture"
SOURCE_AUTHORITY_SCHEMA = f"{SCHEMA}.source_authority"
CONSERVATION_SCHEMA = f"{SCHEMA}.decision_conservation"
STAGE_DAG_SCHEMA = f"{SCHEMA}.occurrence_stage_dag_audit"
COST_SCHEMA = f"{SCHEMA}.cost_completeness"
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

DEFAULT_LANE_HOLD_ROOT = Path(
    "/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/"
    ".hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1"
)
DEFAULT_P1_PACKET_ROOT = Path(
    "/Users/borr/GTOSActive/p1-upstream-source-packet-hold-20260802/"
    "p1-source-packet-sha256-"
    "e1dc1330f47d5a8778456f30f42cb9a1a908d4f8f1d3b744d154c77d6e028f6f"
)
P1_COMMITTED_MANIFEST = Path(
    "docs/audits/fable5-vision-audit-20260725/phase20/receipts/science/"
    "P1_UPSTREAM_SOURCE_PACKET_MANIFEST.json"
)
RAW_COMPARATOR_START = "2025-10-27"
RAW_COMPARATOR_END = "2025-11-09"
RAW_COMPARATOR_DAYS = tuple(
    (date.fromisoformat(RAW_COMPARATOR_START) + timedelta(days=offset)).isoformat()
    for offset in range(
        (date.fromisoformat(RAW_COMPARATOR_END) - date.fromisoformat(RAW_COMPARATOR_START)).days
        + 1
    )
)
TARGET_ROUTE_MODULE = (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "run_selected_package_replay_bridge.py"
)

GRAPH_BOUNDARY = {
    "graph": "research_timewarp",
    "production_parity": False,
    "sizing_authority": "abstract_R_cash_price_distance",
    "broker_lot_sizing_proved": False,
    "production_orchestrator_selector_scheduler_shared_decisions": False,
    "w7_compatibility_packets": "shims_not_shared_decisions",
    "live_correctness_claim_allowed": False,
    "broker_mutation_allowed": False,
    "result_use": "instrumentation_and_revision_comparison_only",
}

STAGE_ORDER = (
    "asof",
    "candidate",
    "scorecard",
    "order",
    "oracle",
    "trade",
    "exit",
    "account",
    "missed",
    "daily",
)

IDENTITY_FIELDS = (
    "campaign",
    "phase",
    "profile",
    "trading_day",
    "decision_time_utc",
    "decision_window_id",
    "candidate_decision_fingerprint_sha256",
    "selector_v4_verdict_hash_sha256",
    "emission_lineage_id",
    "emission_lineage_hash_sha256",
    "executable_instance_id",
    "executable_instance_hash_sha256",
    "canonical_replay_candidate_instance_key",
    "source_bound_replay_candidate_instance_key",
    "risk_finalizer_probe_instance_key",
    "candidate_id",
    "symbol",
    "side",
    "session",
    "route_session",
    "origin_family",
    "candidate_origin_family",
    "simulated_order_id",
    "simulated_trade_id",
    "event_time_utc",
    "wave21_truth_chain_occurrence_schema",
    WAVE21_TRUTH_CHAIN_ORDINAL_FIELD,
    WAVE21_TRUTH_CHAIN_KEY_FIELD,
    WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD,
    WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD,
)

OBSERVABLE_FIELDS = (
    "raw_data_status",
    "candidate_count",
    "candidate_generation_scope",
    "candidate_generation_raw_count",
    "candidate_generation_emitted_count",
    "candidate_generation_truncated_count",
    "candidate_generation_truncated",
    "selector_action",
    "selector_reason",
    "raw_selector_action",
    "raw_selector_reason",
    "effective_selector_action",
    "effective_selector_reason",
    "selected_action_class",
    "scheduler_action",
    "scheduler_reason",
    "scheduler_materialization_action_intent",
    "selected_candidate_id",
    "selected_candidate_ids",
    "risk_decision",
    "risk_decision_reason",
    "risk_pct",
    "final_risk_pct",
    "risk_cash",
    "position_size",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "order_status",
    "fill_status",
    "fill_time_utc",
    "terminal_outcome",
    "close_reason",
    "gross_r",
    "expected_cost_r",
    "spread_r",
    "expected_slippage_r",
    "swap_cost_r",
    "commission_r",
    "total_cost_r",
    "total_execution_cost_r",
    "broker_pretrade_cost_r",
    "total_cost_components",
    "spread_r_source",
    "expected_slippage_r_source",
    "swap_cost_r_source",
    "commission_r_source",
    "quote_authority",
    "quote_source",
    "close_side_all_in_cost_status",
    "net_cost_scope",
    "source_gap_cost_fallback_blocked",
    "candidate_cost_r_fallback_is_authority",
    "net_proxy_r",
    "net_r",
    "pnl_cash",
    "ending_balance",
    "ending_equity",
    "max_drawdown_pct",
    "miss_reason",
    "ordered_path_status",
    "path_source",
    "source_path",
    "source_sha256",
    "pretrade_cost_packet_status",
    "pretrade_cost_packet_model_version",
    "broker_pretrade_cost_source",
    "broker_pretrade_cost_executable",
    "broker_pretrade_cost_executable_block_reason",
    "cost_quote_source",
    "cost_source_gap_allowed_by_replay_profile",
    "cost_authority",
    "execution_cost_authority",
    "cost_source_gap_status",
    "candidate_probability",
    "candidate_ev_r",
    "candidate_expected_net_r",
    "fill_probability",
    "source_completeness",
    "package_replay_order_executable_transfer_status",
    "package_new_entry_authority_valid",
    "candidate_instance_identity_status",
    "candidate_instance_identity_collision",
    "candidate_identity_contract_status",
    "candidate_identity_contract_failures",
    "emission_lineage_schema",
    "emission_lineage_status",
    "emission_lineage_source_boundary",
    "emission_lineage_timeframe",
    "emission_lineage_source_anchor",
    "emission_lineage_source_authority",
    "emission_lineage_source_authority_root_sha256",
    "emission_lineage_cross_asset_source_authorities",
    "executable_instance_schema",
    "executable_instance_status",
    "executable_instance_source_boundary",
    "emission_source_timeframe",
    "emission_source_authority",
    "emission_source_authority_root_sha256",
    "emission_source_timestamp_timezone_status",
    "emission_cross_asset_source_authorities",
    "candidate_decision_fingerprint_schema",
    "candidate_decision_fingerprint_status",
    "candidate_decision_fingerprint_source_boundary",
    "candidate_decision_fingerprint_atoms",
    "candidate_decision_fingerprint_missing_atoms",
    "selector_v4_verdict_schema",
    "selector_v4_verdict_hash_sha256",
    "selector_v4_verdict_status",
    "selector_v4_verdict_source_boundary",
    "selector_v4_verdict_predecessor_candidate_decision_fingerprint_sha256",
    "selector_v4_verdict_atoms",
    "selector_v4_verdict_missing_atoms",
    "broad_entry_intent_policy_schema",
    "broad_entry_intent_policy_id",
    "broad_entry_intent_policy_status",
    "broad_entry_intent_policy_source_boundary",
    "broad_entry_intent_policy_authority_path",
    "broad_entry_intent_policy_authority_sha256",
    "broad_entry_intent_policy_content_sha256",
    "broad_entry_intent_policy_origin_family",
    "broad_entry_intent_policy_order_type",
    "broad_entry_intent_policy_time_in_force",
    "broad_entry_intent_policy_expiry_time_utc",
    "broad_entry_intent_policy_production_parity",
    "broad_entry_intent_policy_atoms",
    "broad_entry_intent_policy_hash_sha256",
    "broad_entry_intent_policy_failures",
    "broad_entry_intent_policy_predecessor_scheduler_candidate_option_identity_key",
    "broad_entry_intent_policy_predecessor_selected_risk_packet_sha256",
    "broad_entry_intent_policy_predecessor_stage_receipt_sha256",
    "broad_entry_intent_policy_quote_spread_asof_estate",
    "geometry_contract_hash_sha256",
    "candidate_geometry_hash_sha256",
    "risk_reward_ratio",
    "target_rr",
    "selector_packet_hash_sha256",
    "no_future_decision_rows",
    "dynamic_geometry_applied",
    "post_geometry_selector_recomputed_on_executable_geometry",
    "post_geometry_lifecycle_recomputed_on_executable_geometry",
    "post_geometry_cost_recomputed_on_executable_geometry",
    "post_geometry_scheduler_received_executable_geometry",
    WAVE21_TRUTH_CHAIN_KIND_FIELD,
    WAVE21_TRUTH_CHAIN_ATOMS_FIELD,
    WAVE21_TRUTH_STAGE_PACKET_FIELD,
)

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

AUTHORITATIVE_MODULES = (
    "src.components.broader_origin_generators",
    "src.components.v4_live_replay_decision_core",
    "src.components.selector_v4",
    "src.research.moonshot_scheduler_v4_best_trade_allocator",
    "src.components.same_symbol_lifecycle_v4",
    "src.components.execution_manager_v4",
    "src.components.dynamic_target_stop_geometry_v4",
    "src.components.exit_policy_v4",
    "src.components.broker_order_lifecycle_capture_v4",
    "src.research_infra.v4_timewarp_simulated_live_research_loop",
    "src.research_infra.replay_compact_event_sink",
    "src.research_infra.wave21_full_flow_truth",
    "src.research_infra.wave21_full_flow_harness",
)

_RUN_LOCK = threading.RLock()
_CONFIG_LOADER_AUTHORITY: dict[str, Any] = {}
_EXTERNAL_ADAPTER_AUTHORITY: list[dict[str, Any]] = []


class FullFlowHarnessError(RuntimeError):
    """Fail-closed harness contract violation."""


def canonical_bytes(value: Any) -> bytes:
    normalized = strict_json_primitive(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def strict_json_primitive(value: Any, *, path: str = "$") -> Any:
    """Normalize only explicitly supported values to strict JSON primitives.

    Unlike ``json.dumps(..., default=str)``, this cannot silently turn an
    arbitrary strategy or authority object into hash-moving text.  Aware
    datetimes and paths have deliberate representations; naive datetimes and
    every other unsupported object fail closed.
    """

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise FullFlowHarnessError(f"nonfinite_json_number:{path}")
        return value
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise FullFlowHarnessError(f"naive_datetime_forbidden:{path}")
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise FullFlowHarnessError(
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
    raise FullFlowHarnessError(
        f"unsupported_json_object:{path}:{type(value).__module__}."
        f"{type(value).__qualname__}"
    )


def _json_safe(value: Any) -> Any:
    return strict_json_primitive(value)


def _explicit_utc_datetime(value: Any, *, field: str) -> datetime:
    """Parse an explicitly zoned UTC value without assuming a timezone."""

    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str) and value.strip():
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise FullFlowHarnessError(f"invalid_utc_timestamp:{field}") from exc
    else:
        raise FullFlowHarnessError(f"utc_timestamp_missing_or_unsupported:{field}")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise FullFlowHarnessError(f"naive_timestamp_forbidden:{field}")
    if parsed.utcoffset() != timedelta(0):
        raise FullFlowHarnessError(f"non_utc_timestamp_for_true_utc_source:{field}")
    return parsed.astimezone(timezone.utc)


def _row_open_utc(row: Mapping[str, Any], *, field: str) -> datetime:
    for key in ("time_utc", "timestamp_utc", "time", "timestamp", "datetime"):
        if row.get(key) not in (None, ""):
            return _explicit_utc_datetime(row[key], field=f"{field}.{key}")
    raise FullFlowHarnessError(f"source_row_timestamp_missing:{field}")


def _row_scheduled_close_utc(
    row: Mapping[str, Any],
    *,
    timeframe: str,
    field: str,
    require_explicit: bool,
) -> tuple[datetime, str]:
    if require_explicit:
        # Truth chronology is a loader boundary, not something this observer
        # may infer or bless after candidate generation.  Until the byte-
        # reopening loader receipt API is integrated, no row-carried close
        # field is sufficient authority.
        raise FullFlowHarnessError(
            f"truth_completed_bar_prefilter_dependency_not_integrated:{field}"
        )
    explicit = [
        _explicit_utc_datetime(row[key], field=f"{field}.{key}")
        for key in (
            "scheduled_close_utc",
            "candle_close_utc",
            "close_time_utc",
        )
        if row.get(key) not in (None, "")
    ]
    if explicit:
        if len(set(explicit)) != 1:
            raise FullFlowHarnessError(
                f"source_row_scheduled_close_conflict:{field}"
            )
        return explicit[0], "row_carried_close_diagnostic_unverified"
    minutes = timewarp.TIMEFRAME_MINUTES.get(timeframe)
    if not isinstance(minutes, int) or minutes <= 0:
        raise FullFlowHarnessError(f"generator_candle_timeframe_unknown:{timeframe}")
    opened = _row_open_utc(row, field=field)
    return opened + timedelta(minutes=minutes), "engineering_nominal_timeframe_only"


def completed_bar_chronology_violations(
    candles: Mapping[str, Any],
    *,
    decision_time_utc: datetime,
    require_explicit_scheduled_close: bool = False,
) -> list[dict[str, Any]]:
    """Engineering-only post-call chronology diagnostic.

    Truth mode is intentionally refused here: completed-bar selection must be
    performed by the byte-reopening loader before the generator sees a row.
    """

    asof = _explicit_utc_datetime(
        decision_time_utc, field="generator.decision_time_utc"
    )
    violations: list[dict[str, Any]] = []
    for timeframe, rows in candles.items():
        if not isinstance(rows, Sequence) or isinstance(
            rows, (str, bytes, bytearray)
        ):
            raise FullFlowHarnessError(
                f"generator_candles_not_sequence:{timeframe}"
            )
        normalized_timeframe = str(timeframe).upper()
        for ordinal, row in enumerate(rows):
            if not isinstance(row, Mapping):
                raise FullFlowHarnessError(
                    f"generator_candle_row_not_mapping:{timeframe}:{ordinal}"
                )
            opened = _row_open_utc(
                row, field=f"generator.candles.{normalized_timeframe}[{ordinal}]"
            )
            scheduled_close, close_authority = _row_scheduled_close_utc(
                row,
                timeframe=normalized_timeframe,
                field=f"generator.candles.{normalized_timeframe}[{ordinal}]",
                require_explicit=require_explicit_scheduled_close,
            )
            if scheduled_close <= opened:
                raise FullFlowHarnessError(
                    "source_row_scheduled_close_not_after_open:"
                    f"{normalized_timeframe}:{ordinal}"
                )
            if scheduled_close > asof:
                violations.append(
                    {
                        "timeframe": normalized_timeframe,
                        "row_ordinal": ordinal,
                        "open_utc": opened.isoformat(),
                        "scheduled_close_utc": scheduled_close.isoformat(),
                        "scheduled_close_authority": close_authority,
                        "decision_time_utc": asof.isoformat(),
                    }
                )
    return violations


def _first(row: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return None


def composite_identity(row: Mapping[str, Any]) -> dict[str, Any]:
    """Project the non-lossy join identity available on a native ledger row."""

    identity = {
        key: row.get(key)
        for key in IDENTITY_FIELDS
        if row.get(key) not in (None, "")
    }
    decision_time = _first(
        row,
        "decision_time_utc",
        "scheduler_asof_utc",
        "candidate_instance_time_utc",
        "asof_utc",
        "candle_close_utc",
    )
    if decision_time is not None:
        identity.setdefault("decision_time_utc", decision_time)
    side = _first(row, "side", "direction")
    if side is not None:
        identity.setdefault("side", side)
    if not any(
        key in identity
        for key in (
            "candidate_id",
            "decision_window_id",
            "simulated_order_id",
            "simulated_trade_id",
            "trading_day",
        )
    ):
        identity["identity_status"] = "stage_aggregate_without_candidate_identity"
    else:
        identity["identity_status"] = "composite_identity_projected"
    return identity


def project_stage_rows(
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    """Emit every native row as a compact projection plus its complete row hash."""

    projected: list[dict[str, Any]] = []
    known = list(STAGE_ORDER)
    known.extend(sorted(set(ledgers) - set(known)))
    for stage in known:
        rows = ledgers.get(stage, ())
        for ordinal, source_row in enumerate(rows):
            row = dict(source_row)
            comparison = _comparison_projection(
                stage=stage, ordinal=ordinal, row=row
            )
            projected.append(
                {
                    **comparison,
                    "comparison_row_root_sha256": stable_sha256(comparison),
                    "native_row_root_sha256_supplemental": stable_sha256(row),
                }
            )
    return projected


def _project_ledgers_bounded(
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]],
    *,
    collect_rows: bool,
    stage_ledger_path: Path | None = None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Project ledgers one row at a time and hash the serialized semantics."""

    collected: list[dict[str, Any]] = []
    known = list(STAGE_ORDER)
    known.extend(sorted(set(ledgers) - set(known)))
    raw_handle = None
    gzip_handle = None
    text_handle = None
    temporary = None
    if stage_ledger_path is not None:
        stage_ledger_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = stage_ledger_path.with_name(f".{stage_ledger_path.name}.tmp")
        raw_handle = temporary.open("xb")
        gzip_handle = gzip.GzipFile(
            filename="", mode="wb", fileobj=raw_handle, mtime=0, compresslevel=6
        )
        text_handle = io.TextIOWrapper(gzip_handle, encoding="utf-8", newline="\n")
    stages: dict[str, dict[str, Any]] = {}
    try:
        for stage in known:
            comparison_hasher = hashlib.sha256()
            serialized_hasher = hashlib.sha256()
            native_hasher = hashlib.sha256()
            identity_hasher = hashlib.sha256()
            dispositions = {field: Counter() for field in DISPOSITION_FIELDS}
            count = 0
            for ordinal, source_row in enumerate(ledgers.get(stage, ())):
                row = dict(source_row)
                comparison = _comparison_projection(
                    stage=stage, ordinal=ordinal, row=row
                )
                projected = {
                    **comparison,
                    "comparison_row_root_sha256": stable_sha256(comparison),
                    "native_row_root_sha256_supplemental": stable_sha256(row),
                }
                comparison_hasher.update(canonical_bytes(comparison) + b"\n")
                serialized_hasher.update(canonical_bytes(projected) + b"\n")
                native_hasher.update(canonical_bytes(row) + b"\n")
                identity_hasher.update(canonical_bytes(comparison["identity"]) + b"\n")
                for field, counter in dispositions.items():
                    value = row.get(field)
                    if value not in (None, "", [], {}):
                        counter[str(value)] += 1
                if collect_rows:
                    collected.append(projected)
                if text_handle is not None:
                    text_handle.write(
                        json.dumps(
                            strict_json_primitive(projected),
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                            allow_nan=False,
                        )
                        + "\n"
                    )
                count += 1
            stages[stage] = {
                "row_count": count,
                "comparison_jsonl_stream_sha256": comparison_hasher.hexdigest(),
                "serialized_projection_jsonl_stream_sha256": serialized_hasher.hexdigest(),
                "native_jsonl_stream_sha256_supplemental": native_hasher.hexdigest(),
                "identity_jsonl_stream_sha256": identity_hasher.hexdigest(),
                "dispositions": {
                    field: dict(sorted(counter.items()))
                    for field, counter in dispositions.items()
                    if counter
                },
            }
        if text_handle is not None:
            text_handle.flush()
            text_handle.detach()
            gzip_handle.close()
            raw_handle.flush()
            os.fsync(raw_handle.fileno())
            raw_handle.close()
            stage_ledger_path.parent.mkdir(parents=True, exist_ok=True)
            temporary.replace(stage_ledger_path)
            text_handle = gzip_handle = raw_handle = None
    finally:
        if text_handle is not None:
            text_handle.close()
        elif gzip_handle is not None:
            gzip_handle.close()
        if raw_handle is not None and not raw_handle.closed:
            raw_handle.close()
    return collected, stages


def _exact_comparison_ledgers(
    result: Mapping[str, Any],
    compact_sink: ReplayCompactEventSink | None,
) -> dict[str, Iterable[Mapping[str, Any]]]:
    """Return fresh exact-spool iterators for compacted roles, never projections."""

    ledgers = dict(result["ledgers"])
    if compact_sink is None:
        return ledgers
    authority = result.get("compact_event_sink_authority")
    row_counts = (
        authority.get("row_counts") if isinstance(authority, Mapping) else {}
    )
    row_counts = row_counts if isinstance(row_counts, Mapping) else {}
    for stage, role in {
        "asof": "decision",
        "candidate": "candidate",
        "order": "order",
        "trade": "trade",
        "missed": "missed",
    }.items():
        if int(row_counts.get(role) or 0) > 0:
            ledgers[stage] = compact_sink.iter_rows(role)
    return ledgers


def _counter(rows: Sequence[Mapping[str, Any]], field: str) -> dict[str, int]:
    values = Counter(
        str(row[field])
        for row in rows
        if row.get(field) not in (None, "", [], {})
    )
    return dict(sorted(values.items()))


def _comparison_projection(
    *, stage: str, ordinal: int, row: Mapping[str, Any]
) -> dict[str, Any]:
    identity = composite_identity(row)
    observables = {
        key: _json_safe(row[key])
        for key in OBSERVABLE_FIELDS
        if key in row and row[key] is not None
    }
    if stage == "candidate":
        observables["legacy_identity_fallback_tokens"] = [
            f"{field}={value}"
            for field, value in row.items()
            if "identity" in str(field).lower()
            and "fallback" in str(value).lower()
        ]
    for source_field, output_field in (
        ("geometry_contract", "geometry_contract_hash_sha256"),
        ("selector_packet", "selector_packet_hash_sha256"),
    ):
        value = row.get(source_field)
        if isinstance(value, Mapping):
            observables[output_field] = stable_sha256(value)
        elif row.get(output_field):
            observables[output_field] = row[output_field]
    return {
        "schema": STAGE_ROW_SCHEMA,
        "stage": stage,
        "stage_row_ordinal": ordinal,
        "identity": identity,
        "observables": observables,
    }


def _harness_candidate_retention_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Keep only post-window state plus hashes needed by the harness oracle."""

    retained = timewarp.post_window_candidate_retention_row(row)
    for source_field, output_field in (
        ("geometry_contract", "geometry_contract_hash_sha256"),
        ("selector_packet", "selector_packet_hash_sha256"),
    ):
        value = row.get(source_field)
        if isinstance(value, Mapping):
            retained[output_field] = stable_sha256(value)
    return retained


def _decision_conservation(
    *,
    result: Mapping[str, Any],
    campaign: timewarp.CampaignConfig,
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
    generation_trace: Mapping[str, Any],
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    ledger_map = result["ledgers"] if ledgers is None else ledgers
    clock = timewarp.ReplayClock(campaign.days, sources)
    expected_by_day: dict[str, int] = {}
    decision_windows_by_day: dict[str, int] = {}
    calendar_rows: list[dict[str, Any]] = []
    for day in campaign.days:
        windows = clock.decision_times_for_day(day, smoke_subset=False)
        decision_windows_by_day[day] = len(windows)
        expected_by_day[day] = len(windows) * len(sources)
        calendar_rows.append(
            {
                "trading_day": day,
                "weekday": date.fromisoformat(day).strftime("%A"),
                "decision_window_count": len(windows),
                "status": (
                    "market_calendar_no_decision_bars"
                    if not windows
                    else "decision_bars_present"
                ),
            }
        )
    expected_slots = sum(expected_by_day.values())
    slot_keys: set[tuple[str, str]] = set()
    observed_asof_count = 0
    duplicate_slots = 0
    raw_counts = 0
    emitted_counts = 0
    truncated_counts = 0
    eligible_calls = 0
    disposition: Counter[str] = Counter()
    for source_row in ledger_map.get("asof", ()):
        row = dict(source_row)
        observed_asof_count += 1
        slot_key = (
            str(row.get("symbol") or ""),
            str(row.get("decision_time_utc") or ""),
        )
        if slot_key in slot_keys:
            duplicate_slots += 1
        slot_keys.add(slot_key)
        raw_counts += int(row.get("candidate_generation_raw_count") or 0)
        emitted_counts += int(row.get("candidate_generation_emitted_count") or 0)
        truncated_counts += int(row.get("candidate_generation_truncated_count") or 0)
        eligible_calls += row.get("raw_data_status") == (
            "live_equivalent_raw_data_built_and_mso_computed"
        )
        disposition[str(row.get("raw_data_status") or "MISSING")] += 1
    family_universe = tuple(broader_origin_generators.PRODUCTION_ORIGIN_FAMILIES) + tuple(
        broader_origin_generators.CURRENT_FRAMEWORK_ORIGIN_FAMILY.values()
    )
    coverage_counts: Counter[tuple[str, str, str]] = Counter()
    candidate_row_count = 0
    for source_row in ledger_map.get("candidate", ()):
        row = dict(source_row)
        candidate_row_count += 1
        coverage_counts[
            (
                str(row.get("symbol") or ""),
                str(
                    row.get("origin_family")
                    or row.get("candidate_origin_family")
                    or "UNKNOWN"
                ),
                str(
                    row.get("side") or row.get("direction") or "UNKNOWN"
                ).upper(),
            )
        ] += 1
    coverage_cells = [
        {
            "symbol": symbol,
            "origin_family": family,
            "side": side,
            "candidate_count": int(coverage_counts[(symbol, family, side)]),
        }
        for symbol in sorted(sources)
        for family in family_universe
        for side in ("BUY", "SELL")
    ]
    violations: list[str] = []
    if observed_asof_count != expected_slots:
        violations.append("decision_slot_count_mismatch")
    if duplicate_slots:
        violations.append("duplicate_decision_slot_rows")
    if int(generation_trace["generator_call_count"]) != eligible_calls:
        violations.append("generator_call_conservation_mismatch")
    if int(generation_trace["raw_generated_candidate_count"]) != raw_counts:
        violations.append("raw_candidate_count_conservation_mismatch")
    if emitted_counts != candidate_row_count:
        violations.append("emitted_candidate_ledger_conservation_mismatch")
    if truncated_counts or campaign.max_candidates_per_symbol_window != 0:
        violations.append("candidate_population_truncated")
    if int(generation_trace.get("generator_future_or_forming_bar_violation_count") or 0):
        violations.append("generator_future_or_forming_bar_consumed")
    body = {
        "schema": CONSERVATION_SCHEMA,
        "expected_decision_slot_count": expected_slots,
        "observed_asof_row_count": observed_asof_count,
        "silent_continue_or_missing_slot_count": expected_slots - observed_asof_count,
        "duplicate_decision_slot_count": duplicate_slots,
        "decision_windows_by_day": decision_windows_by_day,
        "expected_slots_by_day": expected_by_day,
        "market_calendar_rows": calendar_rows,
        "generator_eligible_slot_count": eligible_calls,
        "generator_refusal_or_source_disposition_counts": dict(sorted(disposition.items())),
        "generator_call_count": int(generation_trace["generator_call_count"]),
        "raw_generated_candidate_count": raw_counts,
        "emitted_candidate_count": emitted_counts,
        "candidate_ledger_row_count": candidate_row_count,
        "truncated_candidate_count": truncated_counts,
        "coverage_cells": coverage_cells,
        "coverage_cell_count": len(coverage_cells),
        "violations": violations,
        "status": "PASS" if not violations else "FAIL",
    }
    return {**body, "conservation_root_sha256": stable_sha256(body)}


def _is_sha256(value: Any) -> bool:
    return bool(_SHA256_RE.fullmatch(str(value or "").strip().lower()))


def _candidate_fingerprint_forbidden_atom_paths(
    value: Any, *, path: str = "candidate_decision_fingerprint_atoms"
) -> list[str]:
    """Find order/executable semantics forbidden before Selector/Scheduler."""

    failures: list[str] = []
    forbidden_key_fragments = (
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
            key_text = str(key).lower()
            child = f"{path}.{key}"
            if any(fragment in key_text for fragment in forbidden_key_fragments):
                failures.append(child)
            failures.extend(
                _candidate_fingerprint_forbidden_atom_paths(item, path=child)
            )
    elif isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for ordinal, item in enumerate(value):
            failures.extend(
                _candidate_fingerprint_forbidden_atom_paths(
                    item, path=f"{path}[{ordinal}]"
                )
            )
    return failures


def _truth_stage_packet_failures(packet: Mapping[str, Any]) -> list[str]:
    failures: list[str] = []
    receipt = packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD)
    if not isinstance(receipt, Mapping):
        return ["stage_receipt_missing"]
    if receipt.get("schema") != WAVE21_TRUTH_STAGE_RECEIPT_SCHEMA:
        failures.append("stage_receipt_schema_invalid")
    payload_with_identity = {
        key: value
        for key, value in packet.items()
        if key != WAVE21_TRUTH_STAGE_RECEIPT_FIELD
    }
    stage_payload = {
        key: value
        for key, value in payload_with_identity.items()
        if key != WAVE21_TRUTH_IDENTITY_ROOT_FIELD
    }
    try:
        payload_sha256 = stable_sha256(payload_with_identity)
        receipt_body = {
            key: value for key, value in receipt.items() if key != "receipt_sha256"
        }
        receipt_sha256 = stable_sha256(receipt_body)
    except FullFlowHarnessError:
        return ["stage_packet_not_strict_json"]
    if receipt.get("payload_sha256") != payload_sha256:
        failures.append("stage_payload_hash_mismatch")
    if receipt.get("receipt_sha256") != receipt_sha256:
        failures.append("stage_receipt_hash_mismatch")
    identity_root = packet.get(WAVE21_TRUTH_IDENTITY_ROOT_FIELD)
    if not _is_sha256(identity_root):
        failures.append("stage_identity_root_invalid")
    if receipt.get("identity_root_sha256") != identity_root:
        failures.append("stage_receipt_identity_root_mismatch")
    stage_id = str(receipt.get("stage_id") or "")
    fixed_point_pass = receipt.get("fixed_point_pass")
    if (
        isinstance(fixed_point_pass, bool)
        or not isinstance(fixed_point_pass, int)
        or fixed_point_pass < 0
    ):
        failures.append("fixed_point_pass_invalid")
    else:
        expected_identity_root = stable_sha256(
            {
                "schema": WAVE21_TRUTH_IDENTITY_ROOT_SCHEMA,
                "stage_id": stage_id,
                "fixed_point_pass": fixed_point_pass,
                "predecessor_identity_root_sha256": receipt.get(
                    "predecessor_identity_root_sha256"
                ),
                "stage_payload_sha256": stable_sha256(stage_payload),
            }
        )
        # The producer receipt binds the predecessor receipt hash, while the
        # identity root binds the predecessor *identity* root.  The latter is
        # not repeated in the receipt, so callers replace this provisional
        # value with the actual predecessor before comparing below.
        if receipt.get("stage_ordinal") == 0 and identity_root != expected_identity_root:
            failures.append("stage_identity_root_recompute_mismatch")
    stage_ordinal = receipt.get("stage_ordinal")
    if (
        isinstance(stage_ordinal, bool)
        or not isinstance(stage_ordinal, int)
        or stage_ordinal < 0
    ):
        failures.append("stage_ordinal_invalid")
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
    return failures


def _occurrence_stage_dag_audit(
    result: Mapping[str, Any],
    *,
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    """Independently validate the pass-indexed Wave-21 window DAG.

    Ledger occurrence ordinals are global *stage-row* ordinals.  Candidate
    chains are keyed separately by source slot plus candidate occurrence, and
    may repeat Selector/Scheduler/risk/order/cost/fillability across up to
    three fixed-point passes before any executable instance exists.
    """

    ledger_map = result["ledgers"] if ledgers is None else ledgers
    failures: list[dict[str, Any]] = []

    def fail(reason: str, **context: Any) -> None:
        if len(failures) < 300:
            failures.append({"reason": reason, **_json_safe(context)})

    candidate_rows = [dict(row) for row in ledger_map.get("candidate", ())]
    candidate_ordinals: list[int] = []
    candidate_instance_keys: list[str] = []
    candidate_key_truth_ordinal: dict[str, int | None] = {}
    candidate_rows_missing_truth_ordinal = 0
    candidate_pre_scheduler_contract_failure_count = 0
    for row_index, row in enumerate(candidate_rows):
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
        elif isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 0:
            row_failures.append("candidate_occurrence_ordinal_missing_or_invalid")
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
        if status is not None and row.get("candidate_instance_identity_collision") is True:
            row_failures.append("candidate_occurrence_identity_collision")
        fingerprint_atoms = row.get("candidate_decision_fingerprint_atoms")
        if isinstance(fingerprint_atoms, Mapping):
            if _candidate_fingerprint_forbidden_atom_paths(fingerprint_atoms):
                row_failures.append(
                    "candidate_fingerprint_contains_order_or_exec_atoms"
                )
        cross = row.get("emission_cross_asset_source_authorities")
        if cross not in (None, []):
            if not isinstance(cross, list):
                row_failures.append("cross_asset_source_authorities_not_list")
            else:
                seen_dependencies: set[tuple[str, int]] = set()
                for dependency_index, dependency in enumerate(cross):
                    if not isinstance(dependency, Mapping):
                        row_failures.append(
                            f"cross_asset_dependency_{dependency_index}_not_mapping"
                        )
                        continue
                    leader = str(dependency.get("leader_symbol") or "").strip()
                    probe = dependency.get("probe_ordinal")
                    if not leader or isinstance(probe, bool) or not isinstance(probe, int):
                        row_failures.append(
                            f"cross_asset_dependency_{dependency_index}_identity_invalid"
                        )
                    elif (leader, probe) in seen_dependencies:
                        row_failures.append(
                            f"cross_asset_dependency_{dependency_index}_duplicate"
                        )
                    else:
                        seen_dependencies.add((leader, probe))
                    if not _is_sha256(
                        dependency.get("source_authority_root_sha256")
                    ):
                        row_failures.append(
                            f"cross_asset_dependency_{dependency_index}_authority_root_invalid"
                        )
        fallback_tokens = [
            str(value)
            for key, value in row.items()
            if "identity" in str(key).lower()
            and "fallback" in str(value).lower()
        ]
        if fallback_tokens:
            row_failures.append("legacy_or_fallback_identity_detected")
        if row_failures:
            candidate_pre_scheduler_contract_failure_count += 1
            fail(
                "candidate_pre_scheduler_contract_invalid",
                candidate_row_index=row_index,
                identity=composite_identity(row),
                failures=row_failures,
            )
    if candidate_ordinals:
        expected_candidate_ordinals = list(range(len(candidate_ordinals)))
        if candidate_ordinals != expected_candidate_ordinals:
            fail(
                "candidate_occurrence_ordinals_not_global_contiguous",
                observed=candidate_ordinals[:20],
                expected=expected_candidate_ordinals[:20],
            )

    asof_rows = [dict(row) for row in ledger_map.get("asof", ())]
    zero_candidate_slot_keys: list[str] = []
    for row in asof_rows:
        if int(row.get("candidate_generation_emitted_count") or 0) != 0:
            continue
        decision_time = str(row.get("decision_time_utc") or "").strip()
        symbol = str(row.get("symbol") or "").strip().upper()
        if decision_time and symbol:
            zero_candidate_slot_keys.append(f"{decision_time}@@{symbol}")
        else:
            fail("zero_candidate_asof_slot_identity_missing")

    raw_stage_rows = [
        dict(row) for row in ledger_map.get(WAVE21_TRUTH_STAGE_LEDGER, ())
    ]
    groups: dict[tuple[str, str, int | None], list[Mapping[str, Any]]] = {}
    group_order: list[tuple[str, str, int | None]] = []
    closed_groups: set[tuple[str, str, int | None]] = set()
    prior_group: tuple[str, str, int | None] | None = None
    observed_row_keys: set[str] = set()
    for row_index, row in enumerate(raw_stage_rows):
        ordinal = row.get(WAVE21_TRUTH_CHAIN_ORDINAL_FIELD)
        if ordinal != row_index:
            fail(
                "truth_stage_occurrence_ordinal_not_contiguous",
                row_index=row_index,
                observed=ordinal,
            )
        kind = str(row.get(WAVE21_TRUTH_CHAIN_KIND_FIELD) or "")
        source_slot_key = str(
            row.get(WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD) or ""
        ).strip()
        candidate_ordinal = row.get(WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD)
        if kind == "source_terminal":
            candidate_ordinal = None
        group = (kind, source_slot_key, candidate_ordinal)
        if prior_group is not None and group != prior_group:
            closed_groups.add(prior_group)
        if group in closed_groups:
            fail(
                "truth_candidate_chain_rows_not_contiguous",
                row_index=row_index,
                group=list(group),
            )
        if group not in groups:
            groups[group] = []
            group_order.append(group)
        prior_group = group

        expected_atoms = {
            WAVE21_TRUTH_CHAIN_ORDINAL_FIELD: ordinal,
            WAVE21_TRUTH_CHAIN_KIND_FIELD: kind,
            WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD: source_slot_key,
            WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD: candidate_ordinal,
        }
        if row.get("wave21_truth_chain_occurrence_schema") != (
            WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA
        ):
            fail("truth_chain_occurrence_schema_invalid", row_index=row_index)
        if row.get(WAVE21_TRUTH_CHAIN_ATOMS_FIELD) != expected_atoms:
            fail("truth_chain_occurrence_atoms_mismatch", row_index=row_index)
        expected_key = "wave21chain:" + stable_sha256(
            {"schema": WAVE21_TRUTH_CHAIN_OCCURRENCE_SCHEMA, **expected_atoms}
        )
        row_key = str(row.get(WAVE21_TRUTH_CHAIN_KEY_FIELD) or "")
        if row_key != expected_key:
            fail("truth_chain_occurrence_key_mismatch", row_index=row_index)
        if row_key in observed_row_keys:
            fail("truth_chain_occurrence_key_duplicate", row_index=row_index)
        observed_row_keys.add(row_key)
        if kind not in {"candidate", "source_terminal"}:
            fail("truth_chain_kind_invalid", row_index=row_index, kind=kind)
        if not source_slot_key:
            fail("truth_source_slot_key_missing", row_index=row_index)
        if kind == "candidate" and (
            isinstance(candidate_ordinal, bool)
            or not isinstance(candidate_ordinal, int)
            or candidate_ordinal < 0
        ):
            fail("truth_candidate_occurrence_ordinal_invalid", row_index=row_index)

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
    terminal_not_evaluable_chain_count = 0
    terminal_evaluable_nontrade_chain_count = 0
    complete_accounted_chain_count = 0
    candidate_chain_ordinals: list[int] = []
    source_terminal_slot_keys: list[str] = []
    window_pass_selector: dict[tuple[str, int], set[int]] = defaultdict(set)
    window_pass_scheduler: dict[tuple[str, int], set[int]] = defaultdict(set)
    window_pass_convergence: dict[tuple[str, int], set[int]] = defaultdict(set)
    convergence_packets: dict[tuple[str, int], list[Mapping[str, Any]]] = defaultdict(list)

    def window_key(source_slot_key: str) -> str:
        return source_slot_key.rsplit("@@", 1)[0]

    def terminal_at_end(
        packets: Sequence[Mapping[str, Any]],
        *,
        index: int,
        allow_evaluable: bool,
        group: tuple[str, str, int | None],
    ) -> str | None:
        if index >= len(packets):
            return None
        receipt = packets[index].get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD)
        receipt = receipt if isinstance(receipt, Mapping) else {}
        if receipt.get("stage_id") != "terminal_disposition":
            return None
        if index != len(packets) - 1:
            fail("truth_stage_after_terminal", group=list(group))
        disposition = str(receipt.get("disposition") or "")
        if disposition == "TERMINAL_EVALUABLE_NONTRADE" and not allow_evaluable:
            fail("premature_evaluable_nontrade_terminal", group=list(group))
        return disposition

    for group in group_order:
        kind, source_slot_key, candidate_ordinal = group
        packets = groups[group]
        receipts = [
            packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD)
            if isinstance(packet.get(WAVE21_TRUTH_STAGE_RECEIPT_FIELD), Mapping)
            else {}
            for packet in packets
        ]
        for stage_index, (packet, receipt) in enumerate(zip(packets, receipts)):
            stage_id = str(receipt.get("stage_id") or "")
            stage_counts[stage_id] += 1
            stage_status_counts[
                f"{stage_id}:{packet.get('wave21_truth_stage_status')}"
            ] += 1
            if receipt.get("stage_ordinal") != stage_index:
                fail(
                    "truth_stage_ordinal_not_contiguous",
                    group=list(group),
                    stage_index=stage_index,
                )
            predecessor = receipts[stage_index - 1] if stage_index else None
            if predecessor is None:
                if receipt.get("predecessor_stage_id") is not None or receipt.get(
                    "predecessor_stage_receipt_sha256"
                ) is not None:
                    fail("truth_initial_stage_has_predecessor", group=list(group))
                predecessor_identity_root = None
            else:
                if receipt.get("predecessor_stage_id") != predecessor.get("stage_id"):
                    fail("truth_stage_predecessor_id_mismatch", group=list(group))
                if receipt.get("predecessor_stage_receipt_sha256") != predecessor.get(
                    "receipt_sha256"
                ):
                    fail("truth_stage_predecessor_hash_mismatch", group=list(group))
                predecessor_identity_root = packets[stage_index - 1].get(
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
            expected_identity_root = stable_sha256(
                {
                    "schema": WAVE21_TRUTH_IDENTITY_ROOT_SCHEMA,
                    "stage_id": stage_id,
                    "fixed_point_pass": receipt.get("fixed_point_pass"),
                    "predecessor_identity_root_sha256": predecessor_identity_root,
                    "stage_payload_sha256": stable_sha256(stage_payload),
                }
            )
            if packet.get(WAVE21_TRUTH_IDENTITY_ROOT_FIELD) != expected_identity_root:
                fail("truth_stage_identity_root_mismatch", group=list(group), stage=stage_id)

        if not packets:
            fail("truth_stage_chain_empty", group=list(group))
            continue
        stage_ids = [str(receipt.get("stage_id") or "") for receipt in receipts]
        final_disposition = str(receipts[-1].get("disposition") or "")
        if final_disposition == "TERMINAL_NOT_EVALUABLE":
            terminal_not_evaluable_chain_count += 1
        elif final_disposition == "TERMINAL_EVALUABLE_NONTRADE":
            terminal_evaluable_nontrade_chain_count += 1

        if kind == "source_terminal":
            source_terminal_slot_keys.append(source_slot_key)
            if stage_ids != ["source_lineage", "terminal_disposition"]:
                fail("source_terminal_stage_sequence_invalid", group=list(group), stages=stage_ids)
            continue
        if kind != "candidate" or not isinstance(candidate_ordinal, int):
            continue
        candidate_chain_ordinals.append(candidate_ordinal)

        index = 0

        def require_stage(stage_id: str, fixed_pass: int) -> bool:
            nonlocal index
            if index >= len(receipts) or receipts[index].get("stage_id") != stage_id:
                fail(
                    "candidate_stage_sequence_invalid",
                    group=list(group),
                    expected_stage=stage_id,
                    observed_stage=(
                        receipts[index].get("stage_id") if index < len(receipts) else None
                    ),
                    stages=stage_ids,
                )
                return False
            if receipts[index].get("fixed_point_pass") != fixed_pass:
                fail(
                    "candidate_stage_fixed_point_pass_mismatch",
                    group=list(group),
                    stage=stage_id,
                    expected_pass=fixed_pass,
                    observed_pass=receipts[index].get("fixed_point_pass"),
                )
            index += 1
            return True

        if not require_stage("source_lineage", 0):
            continue
        if terminal_at_end(packets, index=index, allow_evaluable=False, group=group):
            continue
        if not require_stage("candidate_decision_fingerprint", 0):
            continue
        fingerprint_packet = packets[index - 1]
        if not _is_sha256(
            fingerprint_packet.get("candidate_decision_fingerprint_sha256")
        ):
            fail("stage_candidate_fingerprint_invalid", group=list(group))
        fingerprint_atoms = fingerprint_packet.get(
            "candidate_decision_fingerprint_atoms"
        )
        if not isinstance(fingerprint_atoms, Mapping) or (
            _candidate_fingerprint_forbidden_atom_paths(fingerprint_atoms)
        ):
            fail("stage_candidate_fingerprint_atoms_invalid", group=list(group))
        if terminal_at_end(packets, index=index, allow_evaluable=False, group=group):
            continue

        fixed_pass = 0
        committed = False
        while index < len(packets):
            if fixed_pass >= 3:
                fail("fixed_point_pass_limit_exceeded", group=list(group))
                break
            if not require_stage("selector_verdict", fixed_pass):
                break
            selector_packet = packets[index - 1]
            selector_hash = selector_packet.get("selector_v4_verdict_hash_sha256")
            fingerprint_hash = fingerprint_packet.get(
                "candidate_decision_fingerprint_sha256"
            )
            if not _is_sha256(selector_hash):
                fail("stage_selector_verdict_hash_invalid", group=list(group))
            if selector_packet.get(
                "selector_v4_verdict_predecessor_candidate_decision_fingerprint_sha256"
            ) != fingerprint_hash:
                fail("stage_selector_fingerprint_predecessor_mismatch", group=list(group))
            window_pass_selector[(window_key(source_slot_key), fixed_pass)].add(
                candidate_ordinal
            )
            if terminal_at_end(packets, index=index, allow_evaluable=False, group=group):
                break
            if not require_stage("scheduler_option", fixed_pass):
                break
            scheduler_packet = packets[index - 1]
            window_pass_scheduler[(window_key(source_slot_key), fixed_pass)].add(
                candidate_ordinal
            )
            if scheduler_packet.get("candidate_occurrence_ordinal") != candidate_ordinal:
                fail("scheduler_option_candidate_ordinal_mismatch", group=list(group))
            disposition = scheduler_packet.get(
                "scheduler_candidate_option_disposition"
            )
            selected = scheduler_packet.get("scheduler_candidate_option_selected")
            if disposition not in {
                "RISK_BEARING_EVALUATED",
                "TERMINAL_EVALUABLE_NONTRADE",
                "TERMINAL_NOT_EVALUABLE",
            }:
                fail("scheduler_option_disposition_invalid", group=list(group))
            if not isinstance(selected, bool):
                fail("scheduler_option_selected_not_boolean", group=list(group))
                selected = False
            if selected and disposition != "RISK_BEARING_EVALUATED":
                fail("scheduler_selected_terminal_option", group=list(group))
            if scheduler_packet.get("scheduler_option_is_final_order_authority") is True:
                fail("scheduler_claims_final_order_authority", group=list(group))
            if scheduler_packet.get("scheduler_option_is_executable_instance_authority") is True:
                fail("scheduler_claims_executable_authority", group=list(group))
            if terminal_at_end(packets, index=index, allow_evaluable=False, group=group):
                break
            if selected:
                order_stages_complete = True
                for stage_id in (
                    "continuous_risk_sizing",
                    "final_order",
                    "pretrade_expected_cost",
                    "order_fillability",
                ):
                    if not require_stage(stage_id, fixed_pass):
                        order_stages_complete = False
                        break
                    if terminal_at_end(
                        packets, index=index, allow_evaluable=False, group=group
                    ):
                        order_stages_complete = False
                        break
                if not order_stages_complete:
                    break
            if not require_stage("fixed_point_convergence", fixed_pass):
                break
            convergence = packets[index - 1]
            window_pass_convergence[(window_key(source_slot_key), fixed_pass)].add(
                candidate_ordinal
            )
            convergence_packets[(window_key(source_slot_key), fixed_pass)].append(
                convergence
            )
            if convergence.get("order_policy_fixed_point_pass") != fixed_pass:
                fail("fixed_point_payload_pass_mismatch", group=list(group))
            stable = convergence.get("order_policy_fixed_point_adjacent_stable")
            if not isinstance(stable, bool):
                fail("fixed_point_stability_not_boolean", group=list(group))
                stable = False
            if terminal_at_end(
                packets,
                index=index,
                allow_evaluable=not selected and stable,
                group=group,
            ):
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
                if not require_stage(stage_id, fixed_pass):
                    downstream_complete = False
                    break
                stage_status = packets[index - 1].get("wave21_truth_stage_status")
                if terminal_at_end(
                    packets,
                    index=index,
                    allow_evaluable=stage_status == "EVALUABLE_NONTRADE",
                    group=group,
                ):
                    downstream_complete = False
                    break
            if downstream_complete and index == len(packets):
                complete_accounted_chain_count += 1
            break
        if index < len(packets) and receipts[index].get("stage_id") != "terminal_disposition":
            fail(
                "candidate_chain_unconsumed_stage_suffix",
                group=list(group),
                suffix=stage_ids[index:],
            )
        if committed and fixed_pass == 0:
            fail("fixed_point_committed_without_adjacent_pass", group=list(group))

    truth_chain_model_active = bool(raw_stage_rows)
    if truth_chain_model_active:
        if candidate_rows_missing_truth_ordinal:
            fail(
                "candidate_occurrence_ordinal_missing_under_truth_chain_model",
                missing_count=candidate_rows_missing_truth_ordinal,
            )
        candidate_chain_ordinals_sorted = sorted(candidate_chain_ordinals)
        if candidate_chain_ordinals_sorted != candidate_ordinals:
            fail(
                "candidate_occurrence_chain_conservation_mismatch",
                ledger_ordinals=candidate_ordinals[:20],
                chain_ordinals=candidate_chain_ordinals_sorted[:20],
            )
        if sorted(source_terminal_slot_keys) != sorted(zero_candidate_slot_keys):
            fail(
                "zero_candidate_source_terminal_conservation_mismatch",
                expected_count=len(zero_candidate_slot_keys),
                observed_count=len(source_terminal_slot_keys),
            )

    # ------------------------------------------------------------------
    # Occurrence-union DAG: every candidate occurrence must end in exactly
    # one disjoint terminal disposition -- missed | trade | terminal_unfilled
    # -- unless a truth-chain covers it (chains carry their own terminal
    # stage).  This is the graph the raw comparator actually emits.
    # ------------------------------------------------------------------
    def _occurrence_key(row: Mapping[str, Any]) -> str:
        return str(
            row.get("canonical_replay_candidate_instance_key") or ""
        ).strip()

    candidate_key_set = set(candidate_instance_keys)
    chain_covered_keys = {
        key
        for key, key_ordinal in candidate_key_truth_ordinal.items()
        if key_ordinal is not None and key_ordinal in set(candidate_chain_ordinals)
    }
    missed_keys: set[str] = set()
    for row_index, row in enumerate(ledger_map.get("missed", ())):
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
    for row_index, row in enumerate(ledger_map.get("order", ())):
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
    for row_index, row in enumerate(ledger_map.get("trade", ())):
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
        if any(status == "filled" for status in order_statuses_by_key[key]):
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
    for key, selector_ordinals in sorted(window_pass_selector.items()):
        scheduler_ordinals = window_pass_scheduler.get(key, set())
        if scheduler_ordinals and scheduler_ordinals != selector_ordinals:
            fail(
                "scheduler_window_option_conservation_mismatch",
                window_pass=list(key),
                selector_ordinals=sorted(selector_ordinals),
                scheduler_ordinals=sorted(scheduler_ordinals),
            )
        convergence_ordinals = window_pass_convergence.get(key, set())
        if convergence_ordinals and convergence_ordinals != scheduler_ordinals:
            fail(
                "fixed_point_window_candidate_conservation_mismatch",
                window_pass=list(key),
                scheduler_ordinals=sorted(scheduler_ordinals),
                convergence_ordinals=sorted(convergence_ordinals),
            )
    for key, packets in sorted(convergence_packets.items()):
        roots = {
            stable_sha256(packet.get("order_policy_fixed_point_atoms"))
            for packet in packets
        }
        keys = {
            packet.get("order_policy_fixed_point_key_sha256") for packet in packets
        }
        if len(roots) != 1 or len(keys) != 1:
            fail(
                "fixed_point_window_atoms_not_identical",
                window_pass=list(key),
            )
            continue
        atoms = packets[0].get("order_policy_fixed_point_atoms")
        atoms = atoms if isinstance(atoms, Mapping) else {}
        expected_key = stable_sha256(
            {"schema": "gtos.wave21.order_policy_window_fixed_point.v1", **dict(atoms)}
        )
        if next(iter(keys)) != expected_key:
            fail("fixed_point_window_key_mismatch", window_pass=list(key))
        raw_option_atoms = atoms.get("candidate_option_atoms")
        option_ordinals = {
            row.get("candidate_occurrence_ordinal")
            for row in raw_option_atoms
        } if isinstance(raw_option_atoms, list) else set()
        if option_ordinals != window_pass_scheduler.get(key, set()):
            fail(
                "fixed_point_candidate_option_atoms_conservation_mismatch",
                window_pass=list(key),
            )

    stage_count_map = dict(sorted(stage_counts.items()))
    mandatory_result_stage_counts = {
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
        "asof_source_slot_count": len(asof_rows),
        "zero_candidate_source_slot_count": len(zero_candidate_slot_keys),
        "candidate_occurrence_count": len(candidate_rows),
        "candidate_pre_scheduler_contract_failure_count": (
            candidate_pre_scheduler_contract_failure_count
        ),
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
        "expected_chain_count": len(candidate_rows) + len(zero_candidate_slot_keys),
        "observed_chain_count": len(groups),
        "truth_stage_row_count": len(raw_stage_rows),
        "candidate_chain_count": len(candidate_chain_ordinals),
        "source_terminal_chain_count": len(source_terminal_slot_keys),
        "terminal_not_evaluable_chain_count": terminal_not_evaluable_chain_count,
        "terminal_evaluable_nontrade_chain_count": (
            terminal_evaluable_nontrade_chain_count
        ),
        "complete_accounted_chain_count": complete_accounted_chain_count,
        "stage_counts": stage_count_map,
        "stage_status_counts": dict(sorted(stage_status_counts.items())),
        "mandatory_result_stage_counts": mandatory_result_stage_counts,
        "fixed_point_window_pass_count": len(window_pass_selector),
        "scheduler_is_order_or_exec_authority": False,
        "legacy_candidate_to_order_geometry_audit_used": False,
        "failure_count": len(failures),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }
    return {**body, "stage_dag_audit_root_sha256": stable_sha256(body)}


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
    except FullFlowHarnessError:
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
    except FullFlowHarnessError:
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


def _economic_chain_key(row: Mapping[str, Any]) -> str:
    return stable_sha256(
        {
            "chain_kind": row.get(WAVE21_TRUTH_CHAIN_KIND_FIELD),
            "source_slot_key": row.get(WAVE21_TRUTH_SOURCE_SLOT_KEY_FIELD),
            "candidate_occurrence_ordinal": row.get(
                WAVE21_TRUTH_CANDIDATE_ORDINAL_FIELD
            ),
        }
    )


def _economic_projection(
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
                        "identity": composite_identity(row),
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
                        "identity": composite_identity(row),
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
        sorted(timewarp.GTOS_24_SYMBOL_SURFACE)
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
                set(timewarp.GTOS_24_SYMBOL_SURFACE) - set(TICK_COVERED_SYMBOLS)
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


def build_comparator_fingerprint(
    result: Mapping[str, Any],
    *,
    stage_summaries: Mapping[str, Mapping[str, Any]],
    input_manifest: Mapping[str, Any],
    generation_trace: Mapping[str, Any],
    result_scope: str,
    ledgers: Mapping[str, Iterable[Mapping[str, Any]]] | None = None,
) -> dict[str, Any]:
    stages = {
        str(stage): _json_safe(summary)
        for stage, summary in stage_summaries.items()
    }
    economics = _economic_projection(
        result,
        result_scope=result_scope,
        denominator_symbols=tuple(
            sorted(
                {
                    str(row.get("symbol") or "")
                    for row in input_manifest.get("source_manifest", {}).get(
                        "sources", ()
                    )
                    if isinstance(row, Mapping) and row.get("symbol")
                }
            )
        ),
        ledgers=ledgers,
    )
    body = {
        "schema": FINGERPRINT_SCHEMA,
        **GRAPH_BOUNDARY,
        "input_manifest_root_sha256": stable_sha256(input_manifest),
        "generation_trace_root_sha256": stable_sha256(generation_trace),
        "stage_order": list(stages),
        "stages": stages,
        "economics": economics,
    }
    return {**body, "fingerprint_root_sha256": stable_sha256(body)}


def source_manifest(
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for symbol, by_timeframe in sorted(sources.items()):
        for timeframe, source in sorted(by_timeframe.items()):
            computed_rows_root = stable_sha256(source.rows)
            rows.append(
                {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "path": str(source.spec.path),
                    "row_count": len(source.rows),
                    "canonical_normalized_rows_root_sha256": computed_rows_root,
                    "resolved_source_identity_sha256": source.sha256,
                    "source_spec_declared_sha256": source.spec.sha256,
                    "source_spec_hash_domain": (
                        "composite_or_bounded_source_identity"
                        if len(source.component_source_labels) > 1
                        else "declared_physical_file_or_packet_identity"
                    ),
                    "hash_domains_distinct": True,
                    "days": dict(sorted(source.day_counts.items())),
                    "source_family": source.spec.source_family,
                    "source_broker": source.spec.source_broker,
                    "source_role": source.spec.source_role,
                    "source_truth_scope": source.spec.source_truth_scope,
                    "diagnostic_fallback_only": source.spec.diagnostic_fallback_only,
                    "ordered_tick_truth_satisfied": (
                        source.spec.ordered_tick_truth_satisfied
                    ),
                }
            )
    body = {"sources": rows}
    return {**body, "source_root_sha256": stable_sha256(body)}


def _loader_owned_raw_source_authority_fields_by_symbol(
    *,
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
    source_authority: Mapping[str, Any] | None,
    days: Sequence[str],
) -> dict[str, dict[str, Any]]:
    """Consume only producer-attached v2 receipts; post-hoc projection is forbidden."""

    if not source_authority:
        return {}
    raise FullFlowHarnessError(
        "loader_owned_source_authority_receipt_v2_dependency_not_integrated"
    )


def code_manifest() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for module_name in AUTHORITATIVE_MODULES:
        module = importlib.import_module(module_name)
        source_path = inspect.getsourcefile(module)
        if source_path is None:
            raise FullFlowHarnessError(f"module_source_path_missing:{module_name}")
        path = Path(source_path).resolve()
        rows.append(
            {
                "module": module_name,
                "path": str(path),
                "sha256": file_sha256(path),
                "byte_count": path.stat().st_size,
            }
        )
    body = {"modules": rows}
    return {**body, "code_root_sha256": stable_sha256(body)}


@dataclass
class _GenerationTrace:
    calls: list[dict[str, Any]]
    violations: list[str]

    def payload(self) -> dict[str, Any]:
        raw_count = sum(int(row["generated_candidate_count"]) for row in self.calls)
        future_violations = sum(
            int(row.get("generator_future_or_forming_bar_violation_count") or 0)
            for row in self.calls
        )
        refused = Counter()
        source_authority_supported = 0
        source_authority_candidates = 0
        source_authority_failures = 0
        for row in self.calls:
            source_authority_supported += int(
                row.get("candidate_source_authority_supported_count") or 0
            )
            source_authority_candidates += int(
                row.get("generated_candidate_count") or 0
            )
            source_authority_failures += int(
                row.get("candidate_source_authority_contract_failure_count") or 0
            )
            for timeframe, count in (
                row.get("source_future_or_forming_rows_refused_by_timeframe") or {}
            ).items():
                refused[str(timeframe)] += int(count)
        return {
            "raw_generation_executed": (
                bool(self.calls) and not self.violations and future_violations == 0
            ),
            "generator_call_count": len(self.calls),
            "raw_generated_candidate_count": raw_count,
            "generator": (
                "src.components.broader_origin_generators."
                "generate_live_broader_origin_candidates"
            ),
            "decision_core": (
                "src.components.v4_live_replay_decision_core."
                "V4DecisionCycleCore"
            ),
            "prepared_day_pack_argument": None,
            "prepared_candidate_payload_consumed": False,
            "generation_audit_transport_workaround_applied": False,
            "completed_bar_only_chronology_enabled": True,
            "scheduled_close_authorities": dict(
                sorted(
                    Counter(
                        str(row.get("scheduled_close_authority") or "MISSING")
                        for row in self.calls
                    ).items()
                )
            ),
            "generator_future_or_forming_bar_violation_count": future_violations,
            "source_authority_injected_call_count": sum(
                row.get("source_authority_injected") is True for row in self.calls
            ),
            "candidate_source_authority_supported_count": source_authority_supported,
            "candidate_source_authority_denominator_count": source_authority_candidates,
            "candidate_source_authority_contract_failure_count": (
                source_authority_failures
            ),
            "source_future_or_forming_rows_refused_by_timeframe": dict(
                sorted(refused.items())
            ),
            "calls": self.calls,
            "violations": self.violations,
        }


@contextmanager
def _trace_real_generator_calls(
    *,
    source_authority_fields_by_symbol: Mapping[str, Mapping[str, Any]],
    truth_mode: bool,
) -> Iterable[_GenerationTrace]:
    trace = _GenerationTrace(calls=[], violations=[])
    original = V4DecisionCycleCore.generate_candidates
    production_generator = (
        broader_origin_generators.generate_live_broader_origin_candidates
    )
    close_index_cache: dict[tuple[int, str, bool], tuple[datetime, ...]] = {}

    def with_source_authority(raw_data: Any, *, symbol: str) -> dict[str, Any]:
        if not isinstance(raw_data, Mapping):
            raise FullFlowHarnessError(f"generator_raw_data_not_mapping:{symbol}")
        output = dict(raw_data)
        fields = source_authority_fields_by_symbol.get(symbol)
        if fields:
            output.update(fields)
        elif truth_mode:
            raise FullFlowHarnessError(
                f"truth_generator_source_authority_missing:{symbol}"
            )
        return output

    def cross_asset_with_source_authority(value: Any) -> Any:
        if not isinstance(value, Mapping):
            return value
        output = dict(value)
        for container_key in ("raw_data_by_symbol", "by_symbol", "symbols"):
            nested = output.get(container_key)
            if not isinstance(nested, Mapping):
                continue
            output[container_key] = {
                str(symbol): with_source_authority(raw, symbol=str(symbol))
                for symbol, raw in nested.items()
            }
        return output

    def source_refusals(
        core: V4DecisionCycleCore,
        *,
        symbol: str,
        asof: datetime,
    ) -> dict[str, int]:
        source_map = (core.sources or {}).get(symbol, {})
        output: dict[str, int] = {}
        for timeframe in timewarp.PRIMARY_DECISION_TIMEFRAMES:
            source = source_map.get(timeframe)
            rows = getattr(source, "rows", ())
            key = (id(rows), timeframe, truth_mode)
            close_times = close_index_cache.get(key)
            if close_times is None:
                close_times = tuple(
                    sorted(
                        _row_scheduled_close_utc(
                            row,
                            timeframe=timeframe,
                            field=(
                                f"source.{symbol}.{timeframe}[{ordinal}]"
                            ),
                            require_explicit=truth_mode,
                        )[0]
                        for ordinal, row in enumerate(rows)
                    )
                )
                close_index_cache[key] = close_times
            eligible = bisect.bisect_right(close_times, asof)
            output[timeframe] = len(close_times) - eligible
        return output

    def observed(self: V4DecisionCycleCore, **kwargs: Any) -> list[dict[str, Any]]:
        bound = getattr(self, "_candidate_generator", None)
        if bound is not production_generator:
            trace.violations.append("nonproduction_candidate_generator_bound")
        if truth_mode:
            # Never run the generator and audit chronology afterwards.  The
            # loader-owned receipt integration must first pass only completed
            # rows (including independently reopenable successor witnesses)
            # into this call.
            raise FullFlowHarnessError(
                "truth_completed_bar_prefilter_dependency_not_integrated"
            )
        symbol = str(kwargs.get("symbol") or "")
        strategy_raw_root = stable_sha256(kwargs.get("raw_data"))
        call_kwargs = dict(kwargs)
        call_kwargs["raw_data"] = with_source_authority(
            kwargs.get("raw_data"), symbol=symbol
        )
        call_kwargs["cross_asset_raw_data"] = cross_asset_with_source_authority(
            kwargs.get("cross_asset_raw_data")
        )
        generated = original(self, **call_kwargs)
        candidate_root = stable_sha256(generated)
        audit_before = self.last_candidate_generation_audit
        # This deepcopy is a deliberate assertion of the producer's public
        # audit transport contract.  The harness never normalizes or repairs it.
        copy.deepcopy(audit_before)
        raw_data = call_kwargs.get("raw_data")
        raw_data = raw_data if isinstance(raw_data, Mapping) else {}
        candles = raw_data.get("candles")
        candles = candles if isinstance(candles, Mapping) else {}
        asof = kwargs.get("now_utc")
        if not isinstance(asof, datetime):
            raise FullFlowHarnessError("generator_decision_time_not_datetime")
        violations = completed_bar_chronology_violations(
            candles,
            decision_time_utc=asof,
            require_explicit_scheduled_close=truth_mode,
        )
        if violations:
            trace.violations.append("generator_received_future_or_forming_bar")
        refused = source_refusals(
            self,
            symbol=symbol,
            asof=asof,
        )
        expected_fields = source_authority_fields_by_symbol.get(symbol) or {}
        expected_by_timeframe = expected_fields.get(
            "wave21_raw_source_authority_by_timeframe"
        )
        expected_by_timeframe = (
            expected_by_timeframe
            if isinstance(expected_by_timeframe, Mapping)
            else {}
        )
        expected_root = expected_fields.get(
            "wave21_raw_source_authority_root_sha256"
        )
        supported_count = sum(
            "emission_source_authority_root_sha256" in row for row in generated
        )
        authority_failures: list[dict[str, Any]] = []
        if generated and supported_count not in (0, len(generated)):
            authority_failures.append(
                {"reason": "candidate_source_authority_partial_support"}
            )
        if truth_mode and supported_count != len(generated):
            authority_failures.append(
                {"reason": "truth_candidate_source_authority_not_stamped"}
            )
        if supported_count:
            for ordinal, candidate in enumerate(generated):
                timeframe = str(
                    candidate.get("emission_source_timeframe") or ""
                ).upper()
                expected = expected_by_timeframe.get(timeframe)
                failures: list[str] = []
                if not isinstance(expected, Mapping):
                    failures.append("candidate_emission_timeframe_not_bound")
                if candidate.get("emission_source_authority") != expected:
                    failures.append("candidate_source_authority_mismatch")
                if (
                    candidate.get("emission_source_authority_root_sha256")
                    != expected_root
                ):
                    failures.append("candidate_source_authority_root_mismatch")
                if (
                    candidate.get("emission_source_timestamp_timezone_status")
                    != "timezone_aware"
                ):
                    failures.append("candidate_source_timestamp_not_timezone_aware")
                if (
                    candidate.get("emission_lineage_source_authority_root_sha256")
                    != expected_root
                ):
                    failures.append("lineage_source_authority_root_mismatch")
                if truth_mode and candidate.get("emission_lineage_status") != "materialized":
                    failures.append("truth_emission_lineage_not_materialized")
                if truth_mode and candidate.get("candidate_identity_contract_status") != (
                    "valid_emission_v2_candidate_decision_v1_exec_not_final"
                ):
                    failures.append("truth_candidate_identity_contract_invalid")
                cross = candidate.get("emission_cross_asset_source_authorities")
                if isinstance(cross, Sequence) and not isinstance(
                    cross, (str, bytes, bytearray)
                ):
                    seen_leaders: set[str] = set()
                    seen_probe_ordinals: set[int] = set()
                    for dependency in cross:
                        if not isinstance(dependency, Mapping):
                            failures.append("cross_asset_source_authority_not_mapping")
                            continue
                        leader_symbol = str(
                            dependency.get("leader_symbol") or ""
                        )
                        probe_ordinal = dependency.get("probe_ordinal")
                        if not leader_symbol:
                            failures.append("cross_asset_source_authority_symbol_missing")
                            continue
                        if (
                            leader_symbol in seen_leaders
                            or isinstance(probe_ordinal, bool)
                            or not isinstance(probe_ordinal, int)
                            or probe_ordinal in seen_probe_ordinals
                        ):
                            failures.append("cross_asset_source_authority_identity_collision")
                            continue
                        seen_leaders.add(leader_symbol)
                        seen_probe_ordinals.add(probe_ordinal)
                        leader_fields = source_authority_fields_by_symbol.get(
                            str(leader_symbol)
                        )
                        if not isinstance(leader_fields, Mapping) or not isinstance(
                            dependency, Mapping
                        ):
                            failures.append("cross_asset_source_authority_unbound")
                            continue
                        if dependency.get("source_authority_root_sha256") != (
                            leader_fields.get(
                                "wave21_raw_source_authority_root_sha256"
                            )
                        ):
                            failures.append(
                                "cross_asset_source_authority_root_mismatch"
                            )
                elif cross not in (None, [], ()):
                    failures.append("cross_asset_source_authority_not_ordered_list")
                if failures:
                    authority_failures.append(
                        {
                            "candidate_ordinal": ordinal,
                            "candidate_id": candidate.get("candidate_id"),
                            "failures": failures,
                        }
                    )
        if authority_failures:
            trace.violations.append("candidate_source_authority_contract_failed")
        trace.calls.append(
            {
                "call_ordinal": len(trace.calls),
                "symbol": symbol,
                "decision_time_utc": str(kwargs.get("now_utc") or ""),
                "pre_authority_strategy_raw_data_root_sha256": strategy_raw_root,
                "raw_data_root_sha256": stable_sha256(raw_data),
                "source_authority_injected": bool(expected_fields),
                "source_authority_root_sha256": expected_root,
                "candidate_source_authority_supported_count": supported_count,
                "candidate_source_authority_contract_failure_count": len(
                    authority_failures
                ),
                "candidate_source_authority_contract_failures": authority_failures[:8],
                "generated_candidate_count": len(generated),
                "generated_candidates_root_sha256": candidate_root,
                "generated_candidate_identities_root_sha256": stable_sha256(
                    [
                        {
                            "candidate_id": row.get("candidate_id"),
                            "symbol": row.get("symbol"),
                            "side": row.get("side"),
                            "origin_family": row.get("origin_family"),
                            "candle_close_utc": row.get("candle_close_utc"),
                        }
                        for row in generated
                    ]
                ),
                "producer_generation_audit_root_sha256": stable_sha256(
                    self.last_candidate_generation_audit
                ),
                "generation_audit_transport_normalization": "none",
                "generation_audit_transport_workaround_applied": False,
                "completed_bar_only_chronology_enabled": True,
                "scheduled_close_authority": (
                    "loader_owned_completed_bar_prefilter_required"
                    if truth_mode
                    else "engineering_nominal_timeframe_fallback_allowed"
                ),
                "generator_future_or_forming_bar_violation_count": len(
                    violations
                ),
                "generator_future_or_forming_bar_violation_sample": violations[:8],
                "source_future_or_forming_rows_refused_by_timeframe": refused,
                "production_generator_identity_exact": bound is production_generator,
            }
        )
        return generated

    with patch.object(V4DecisionCycleCore, "generate_candidates", observed):
        yield trace


@contextmanager
def _scoped_replay_symbols(symbols: Sequence[str]) -> Iterable[None]:
    if not symbols or len(set(symbols)) != len(symbols):
        raise FullFlowHarnessError("fixture_symbol_scope_invalid")
    previous = timewarp.INCLUDED_SYMBOLS
    timewarp.INCLUDED_SYMBOLS = tuple(symbols)
    try:
        yield
    finally:
        timewarp.INCLUDED_SYMBOLS = previous


def _safety_bound_config(
    config: Mapping[str, Any], *, truth_mode: bool
) -> dict[str, Any]:
    if not isinstance(truth_mode, bool):
        raise FullFlowHarnessError("truth_mode_must_be_exact_boolean")
    output = copy.deepcopy(dict(config))
    market_state = output.setdefault("market_state", {})
    if not isinstance(market_state, dict):
        raise FullFlowHarnessError("market_state_config_not_mapping")
    market_state["side_effect_writes_enabled"] = False
    market_state["structure_shadow_log_enabled"] = False
    harness = output.setdefault("broad_live_as_if_replay_harness", {})
    if not isinstance(harness, dict):
        raise FullFlowHarnessError("replay_harness_config_not_mapping")
    harness.update(
        {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
            "completed_bar_only_chronology": True,
            "future_bar_rejection_mandatory": True,
            "arm_dimensions": {
                "continuous_session_treatment": "baseline_unchanged",
                "adr006_breaker_buffer_treatment": "baseline_unchanged",
                "forming_bar_treatment": "corrected_completed_bar_only",
            },
        }
    )
    runtime = output.setdefault("gtos_vnext_runtime", {})
    if not isinstance(runtime, dict):
        raise FullFlowHarnessError("gtos_vnext_runtime_config_not_mapping")
    runtime[WAVE21_FULL_FLOW_TRUTH_MODE_KEY] = bool(truth_mode)
    if wave21_full_flow_truth_mode_enabled(output) is not bool(truth_mode):
        raise FullFlowHarnessError("central_truth_mode_resolver_disagrees")
    return output


def execute_full_flow(
    *,
    campaign: timewarp.CampaignConfig,
    config: Mapping[str, Any],
    sources: Mapping[str, Mapping[str, timewarp.ResolvedSource]],
    result_scope: str = "deterministic_smoke",
    truth_mode: bool = False,
    compact_sink_root: Path | None = None,
    source_authority: Mapping[str, Any] | None = None,
    compact_oracle: Mapping[str, Any] | None = None,
    stage_ledger_path: Path | None = None,
) -> dict[str, Any]:
    """Execute the real direct raw-generator research-timewarp flow.

    ``prepared_day_pack`` is intentionally not accepted by this adapter.  The
    underlying call passes ``None`` explicitly and the run fails closed unless
    at least one invocation reaches the exact production generator.
    """

    if not isinstance(truth_mode, bool):
        raise FullFlowHarnessError("truth_mode_must_be_exact_boolean")
    if campaign.max_candidates_per_symbol_window != 0:
        raise FullFlowHarnessError("candidate_population_truncation_forbidden")
    if not campaign.days:
        raise FullFlowHarnessError("campaign_days_required")
    if campaign.run_smoke_subset:
        raise FullFlowHarnessError("smoke_hour_filter_forbidden")
    symbols = tuple(sources)
    redacted_account_leaks = [
        f"{symbol}:{timeframe}"
        for symbol, by_timeframe in sources.items()
        for timeframe, source in by_timeframe.items()
        if (
            "redacted_account" in str(source.spec.source_broker or "").upper()
            or source.spec.not_redacted_account_native is not True
        )
    ]
    if truth_mode:
        if tuple(sorted(symbols)) != tuple(sorted(timewarp.GTOS_24_SYMBOL_SURFACE)):
            raise FullFlowHarnessError("truth_mode_requires_complete_24_symbol_surface")
        if len(campaign.days) < 14:
            raise FullFlowHarnessError("truth_mode_requires_at_least_14_consecutive_days")
        parsed_days = tuple(date.fromisoformat(day) for day in campaign.days)
        if any(
            parsed_days[index] + timedelta(days=1) != parsed_days[index + 1]
            for index in range(len(parsed_days) - 1)
        ):
            raise FullFlowHarnessError("truth_mode_days_not_consecutive")
        if not (
            parsed_days[0] <= date(2025, 11, 2) <= parsed_days[-1]
        ):
            raise FullFlowHarnessError("truth_mode_us_dst_transition_not_spanned")
        if compact_sink_root is None:
            raise FullFlowHarnessError("truth_mode_requires_stateful_compact_sink")
        if (
            not isinstance(compact_oracle, Mapping)
            or compact_oracle.get("status") != "PASS"
            or compact_oracle.get("full_vs_compact_exact") is not True
        ):
            raise FullFlowHarnessError("truth_mode_compact_oracle_not_proved")
        if redacted_account_leaks:
            raise FullFlowHarnessError(
                f"ftmo_source_mapping_leaked_to_redacted_account:{redacted_account_leaks[:8]}"
            )
    effective_config = _safety_bound_config(config, truth_mode=truth_mode)
    raw_source_authority_fields = _loader_owned_raw_source_authority_fields_by_symbol(
        sources=sources,
        source_authority=source_authority,
        days=campaign.days,
    )
    if truth_mode and set(raw_source_authority_fields) != set(symbols):
        raise FullFlowHarnessError(
            "truth_mode_raw_source_authority_symbol_surface_incomplete"
        )
    inputs = {
        "schema": f"{SCHEMA}.input_manifest",
        **GRAPH_BOUNDARY,
        "campaign": _json_safe(campaign.__dict__),
        "effective_config_payload": _json_safe(effective_config),
        "config_root_sha256": stable_sha256(effective_config),
        "source_manifest": source_manifest(sources),
        "source_authority": _json_safe(source_authority or {}),
        "raw_source_authority_fields_by_symbol_root_sha256": stable_sha256(
            raw_source_authority_fields
        ),
        "raw_source_authority_injection_symbol_count": len(
            raw_source_authority_fields
        ),
        "code_manifest": code_manifest(),
        "prepared_day_pack": None,
        "candidate_population_projection": "full_native_population_no_top_n",
        "result_scope": result_scope,
        "truth_mode": truth_mode,
        "truth_mode_config_key": (
            f"gtos_vnext_runtime.{WAVE21_FULL_FLOW_TRUTH_MODE_KEY}"
        ),
        "truth_mode_config_value": bool(truth_mode),
        "completed_bar_only_chronology": True,
        "ftmo_mapping_leak_to_redacted_account": bool(redacted_account_leaks),
        "ftmo_mapping_leak_cells": redacted_account_leaks,
        "arm_dimensions": effective_config["broad_live_as_if_replay_harness"][
            "arm_dimensions"
        ],
    }
    compact_sink = (
        ReplayCompactEventSink(
            root=compact_sink_root,
            retained_row_projectors={"candidate": _harness_candidate_retention_row},
        )
        if compact_sink_root is not None
        else None
    )
    with (
        _RUN_LOCK,
        _scoped_replay_symbols(symbols),
        _trace_real_generator_calls(
            source_authority_fields_by_symbol=raw_source_authority_fields,
            truth_mode=truth_mode,
        ) as trace,
    ):
        broker = timewarp.SimulatedBroker()
        try:
            result = timewarp.run_campaign(
                campaign=campaign,
                config=effective_config,
                sources=sources,
                broker=broker,
                compact_event_sink=compact_sink,
                prepared_day_pack=None,
            )
        except Exception:
            if compact_sink is not None:
                compact_sink.abort()
            raise
    generation = trace.payload()
    if not generation["raw_generation_executed"]:
        raise FullFlowHarnessError(
            "raw_generation_not_executed:direct_run_campaign_required"
        )
    if generation["prepared_candidate_payload_consumed"]:
        raise FullFlowHarnessError("prepared_candidate_payload_consumed")
    if generation["generation_audit_transport_workaround_applied"]:
        raise FullFlowHarnessError("generation_audit_workaround_forbidden")
    if broker.order_send_attempts != 0:
        raise FullFlowHarnessError("broker_order_send_attempted")
    projected, stage_summaries = _project_ledgers_bounded(
        _exact_comparison_ledgers(result, compact_sink),
        collect_rows=stage_ledger_path is None,
        stage_ledger_path=stage_ledger_path,
    )
    conservation = _decision_conservation(
        result=result,
        campaign=campaign,
        sources=sources,
        generation_trace=generation,
        ledgers=_exact_comparison_ledgers(result, compact_sink),
    )
    stage_dag = _occurrence_stage_dag_audit(
        result,
        ledgers=_exact_comparison_ledgers(result, compact_sink),
    )
    fingerprint = build_comparator_fingerprint(
        result,
        stage_summaries=stage_summaries,
        input_manifest=inputs,
        generation_trace=generation,
        result_scope=result_scope,
        ledgers=_exact_comparison_ledgers(result, compact_sink),
    )
    fingerprint["decision_conservation"] = conservation
    fingerprint["occurrence_stage_dag_audit"] = stage_dag
    fingerprint_without_root = dict(fingerprint)
    fingerprint_without_root.pop("fingerprint_root_sha256", None)
    fingerprint["fingerprint_root_sha256"] = stable_sha256(
        fingerprint_without_root
    )
    hard_truth_failures = []
    if conservation["status"] != "PASS":
        hard_truth_failures.append("decision_conservation_failed")
    if truth_mode and stage_dag["status"] != "PASS":
        hard_truth_failures.append("occurrence_stage_dag_failed")
    mandatory_stage_counts = stage_dag.get("mandatory_result_stage_counts")
    mandatory_stage_counts = (
        dict(mandatory_stage_counts)
        if isinstance(mandatory_stage_counts, Mapping)
        else {}
    )
    mandatory_stage_zero_counts = sorted(
        stage_id
        for stage_id, count in mandatory_stage_counts.items()
        if int(count or 0) <= 0
    )
    full_flow_stage_coverage_complete = bool(mandatory_stage_counts) and not (
        mandatory_stage_zero_counts
    )
    if truth_mode and not full_flow_stage_coverage_complete:
        hard_truth_failures.append("mandatory_full_flow_stage_coverage_incomplete")
    if truth_mode and int(stage_dag.get("candidate_occurrence_count") or 0) <= 0:
        hard_truth_failures.append("truth_candidate_population_empty")
    if truth_mode and int(stage_dag.get("complete_accounted_chain_count") or 0) <= 0:
        hard_truth_failures.append("truth_complete_accounted_chain_absent")
    if truth_mode and fingerprint["economics"].get(
        "economics_complete_for_all_materialized_lifecycles"
    ) is not True:
        hard_truth_failures.append("post_lifecycle_economics_not_complete")
    economics_status = fingerprint["economics"][
        "aggregate_economic_headline_status"
    ]
    if truth_mode:
        receipt_status = (
            "RAW_GENERATION_RESEARCH_TIMEWARP_HARD_TRUTH_STOP"
            if hard_truth_failures
            else "RAW_GENERATION_RESEARCH_TIMEWARP_TRUTH_FULL_FLOW_EXECUTED"
        )
    elif result_scope == "deterministic_smoke":
        receipt_status = "RAW_GENERATION_ENGINEERING_SMOKE_EXECUTED"
    else:
        receipt_status = "RAW_GENERATION_ENGINEERING_COMPARATOR_EXECUTED"
    receipt_body = {
        "schema": RECEIPT_SCHEMA,
        **GRAPH_BOUNDARY,
        "status": receipt_status,
        "raw_generation_executed": True,
        "prepared_candidate_payload_consumed": False,
        "candidate_population_truncated": False,
        "truth_mode": truth_mode,
        "truth_mode_hard_failures": hard_truth_failures,
        "engineering_only": not truth_mode,
        "result_bearing_truth_run": bool(truth_mode and not hard_truth_failures),
        "full_flow_stage_coverage_complete": full_flow_stage_coverage_complete,
        "mandatory_stage_zero_counts": mandatory_stage_zero_counts,
        "complete_accounted_chain_count": int(
            stage_dag.get("complete_accounted_chain_count") or 0
        ),
        "result_scope": result_scope,
        "economics_headline_status": economics_status,
        "broker_true_economics_claimed": False,
        "ftmo_mapping_leak_to_redacted_account": bool(redacted_account_leaks),
        "compact_mode": compact_sink is not None,
        "compact_event_sink_authority": result.get("compact_event_sink_authority"),
        "decision_conservation": conservation,
        "occurrence_stage_dag_audit": stage_dag,
        "inputs": inputs,
        "generation_trace": generation,
        "broker_boundary": broker.mutation_boundary(),
        "terminal_execution_truth_reconciliation": result.get(
            "terminal_execution_truth_reconciliation"
        ),
        "comparator_fingerprint": fingerprint,
    }
    receipt = {
        **receipt_body,
        "receipt_root_sha256": stable_sha256(receipt_body),
    }
    return {
        "result": result,
        "stage_rows": projected,
        "stage_ledger_path": str(stage_ledger_path) if stage_ledger_path else None,
        "fingerprint": fingerprint,
        "receipt": receipt,
        "decision_conservation": conservation,
        "occurrence_stage_dag_audit": stage_dag,
    }


def _bar_rows(
    *,
    symbol: str,
    latest_open: datetime,
    minutes: int,
    count: int,
    price: float = 100.0,
    width: float = 1.0,
) -> list[dict[str, Any]]:
    start = latest_open - timedelta(minutes=minutes * (count - 1))
    return [
        {
            "time": (start + timedelta(minutes=minutes * index)).isoformat(),
            "time_utc": (start + timedelta(minutes=minutes * index)).isoformat(),
            "symbol": symbol,
            "open": price,
            "high": price + width / 2.0,
            "low": price - width / 2.0,
            "close": price,
            "volume": 100.0 + index,
        }
        for index in range(count)
    ]


def _resolved_fixture_source(
    *,
    symbol: str,
    timeframe: str,
    rows: Sequence[Mapping[str, Any]],
    day_source_authority: Mapping[str, Mapping[str, Any]] | None = None,
) -> timewarp.ResolvedSource:
    row_tuple = tuple(dict(row) for row in rows)
    digest = stable_sha256(row_tuple)
    by_day = timewarp.rows_by_day(row_tuple)
    return timewarp.ResolvedSource(
        spec=timewarp.SourceSpec(
            symbol=symbol,
            mapped_symbol=symbol,
            timeframe=timeframe,
            path=Path(f"wave21_deterministic_fixture/{symbol}_{timeframe}.json"),
            source_family="wave21_deterministic_raw_bar_smoke_fixture",
            source_broker="SYNTHETIC_FIXTURE_NOT_BROKER_EVIDENCE",
            source_role="deterministic_behavioral_smoke_only",
            row_count=len(row_tuple),
            sha256=digest,
            diagnostic_fallback_only=False,
            source_truth_scope=timewarp.SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=False,
        ),
        rows=row_tuple,
        rows_by_day=by_day,
        sha256=digest,
        day_counts={day: len(values) for day, values in by_day.items()},
        selected_status="deterministic_fixture_source_complete",
        min_required_rows_per_day=1,
        day_source_authority=day_source_authority or {},
    )


def build_deterministic_smoke_sources(
    *, symbol: str = "XAUUSD"
) -> tuple[dict[str, dict[str, timewarp.ResolvedSource]], dict[str, Any]]:
    """Build one raw decision bar plus complete production lookbacks and M1 path."""

    day = "2026-05-26"
    decision_time = datetime(2026, 5, 26, 8, 0, tzinfo=timezone.utc)
    rows_by_tf = {
        "D1": _bar_rows(
            symbol=symbol,
            latest_open=datetime(2026, 5, 25, tzinfo=timezone.utc),
            minutes=1440,
            count=30,
            width=4.0,
        ),
        "H4": _bar_rows(
            symbol=symbol,
            latest_open=datetime(2026, 5, 26, 8, 0, tzinfo=timezone.utc),
            minutes=240,
            count=80,
            width=2.0,
        ),
        "H1": _bar_rows(
            symbol=symbol,
            latest_open=datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc),
            minutes=60,
            count=168,
            width=1.5,
        ),
    }
    # Keep 668 bars before the smoke day.  Four real London-session bars give
    # the production session-open-range generator its native three-bar opening
    # range and breakout decision without manufacturing a candidate packet.
    m15 = _bar_rows(
        symbol=symbol,
        latest_open=datetime(2026, 5, 25, 23, 45, tzinfo=timezone.utc),
        minutes=15,
        count=668,
        width=1.0,
    )
    m15.extend(
        [
        {
            "time": "2026-05-26T07:00:00+00:00",
            "time_utc": "2026-05-26T07:00:00+00:00",
            "symbol": symbol,
            "open": 100.0,
            "high": 100.5,
            "low": 96.0,
            "close": 100.0,
            "volume": 996.0,
        },
        {
            "time": "2026-05-26T07:15:00+00:00",
            "time_utc": "2026-05-26T07:15:00+00:00",
            "symbol": symbol,
            "open": 100.0,
            "high": 100.4,
            "low": 96.2,
            "close": 100.0,
            "volume": 997.0,
        },
        {
            "time": "2026-05-26T07:30:00+00:00",
            "time_utc": "2026-05-26T07:30:00+00:00",
            "symbol": symbol,
            "open": 100.0,
            "high": 100.3,
            "low": 96.5,
            "close": 100.0,
            "volume": 998.0,
        },
        {
            "time": "2026-05-26T07:45:00+00:00",
            "time_utc": "2026-05-26T07:45:00+00:00",
            "symbol": symbol,
            "open": 100.1,
            "high": 101.3,
            "low": 99.9,
            "close": 101.0,
            "volume": 999.0,
        },
        ]
    )
    rows_by_tf["M15"] = m15
    m1: list[dict[str, Any]] = []
    m1_start = datetime(2026, 5, 26, 7, 15, tzinfo=timezone.utc)
    for index in range(181):
        opened = m1_start + timedelta(minutes=index)
        minutes_after_breakout = max(0, int((opened - decision_time).total_seconds() / 60))
        close = 100.0 if opened < decision_time else min(
            104.0, 101.0 + 0.04 * minutes_after_breakout
        )
        m1.append(
            {
                "time": opened.isoformat(),
                "time_utc": opened.isoformat(),
                "symbol": symbol,
                "open": close + 0.02,
                "high": close + 0.08,
                "low": close - 0.08,
                "close": close,
                "bid": close - 0.01,
                "ask": close + 0.01,
                "spread": 0.02,
                "volume": 25.0,
            }
        )
    rows_by_tf["M1"] = m1
    sources = {
        symbol: {
            timeframe: _resolved_fixture_source(
                symbol=symbol,
                timeframe=timeframe,
                rows=rows,
            )
            for timeframe, rows in rows_by_tf.items()
        }
    }
    m1_authority = timewarp.m1_symbol_day_source_authority(
        symbol=symbol,
        trading_day=day,
        m1_row_count=len(m1),
        m15_row_count=4,
        source_day_sha256=stable_sha256(m1),
        source_path=str(sources[symbol]["M1"].spec.path),
        source_family=sources[symbol]["M1"].spec.source_family,
        source_file_sha256=sources[symbol]["M1"].sha256,
    )
    sources[symbol]["M1"] = _resolved_fixture_source(
        symbol=symbol,
        timeframe="M1",
        rows=m1,
        day_source_authority={day: m1_authority},
    )
    fixture = {
        "schema": FIXTURE_SCHEMA,
        **GRAPH_BOUNDARY,
        "symbol": symbol,
        "trading_day": day,
        "decision_time_utc": decision_time.isoformat(),
        "purpose": "deterministic_behavioral_smoke_not_strategy_economics",
        "candidate_trigger": (
            "production session_open_range_break London raw M15 pattern"
        ),
        "source_manifest": source_manifest(sources),
        "no_threshold_relaxation": True,
        "no_candidate_population_truncation": True,
        "prepared_candidate_payload": False,
    }
    return sources, {**fixture, "fixture_root_sha256": stable_sha256(fixture)}


def _git_output(target_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(target_root), *args],
            text=True,
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise FullFlowHarnessError(
            f"target_git_command_failed:{':'.join(args)}:{exc.stderr.strip()}"
        ) from exc


def _install_target_local_route_module(target_root: Path) -> dict[str, Any]:
    """Load the target HEAD's sparse route blob without integration fallback."""

    target_root = target_root.resolve()
    virtual_path = target_root / TARGET_ROUTE_MODULE
    blob = subprocess.check_output(
        ["git", "-C", str(target_root), "show", f"HEAD:{TARGET_ROUTE_MODULE}"],
        stderr=subprocess.PIPE,
    )
    blob_sha = hashlib.sha256(blob).hexdigest()
    expected_git_blob = _git_output(
        target_root, "rev-parse", f"HEAD:{TARGET_ROUTE_MODULE}"
    )
    module_name = "run_selected_package_replay_bridge"
    existing = sys.modules.get(module_name)
    if existing is not None:
        existing_file = Path(str(getattr(existing, "__file__", ""))).resolve()
        if existing_file != virtual_path:
            raise FullFlowHarnessError(
                f"integration_route_module_already_imported:{existing_file}"
            )
        return {
            "adapter": "target_head_git_blob_virtual_module",
            "target_root": str(target_root),
            "route_path": TARGET_ROUTE_MODULE,
            "route_file_bytes_sha256": blob_sha,
            "route_git_blob_sha1": expected_git_blob,
            "reused": True,
        }
    module = types.ModuleType(module_name)
    module.__file__ = str(virtual_path)
    module.__package__ = ""
    sys.modules[module_name] = module
    try:
        exec(compile(blob, str(virtual_path), "exec"), module.__dict__)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return {
        "adapter": "target_head_git_blob_virtual_module",
        "target_root": str(target_root),
        "route_path": TARGET_ROUTE_MODULE,
        "route_file_bytes_sha256": blob_sha,
        "route_git_blob_sha1": expected_git_blob,
        "reused": False,
        "economic_semantics_changed": False,
    }


def load_repaired_replay_config(
    *, target_root: Path | None = None
) -> dict[str, Any]:
    """Call the target tree's accepted builder with no integration imports."""

    global _CONFIG_LOADER_AUTHORITY
    worktree_root = (
        active_target_root()
        if target_root is None
        else Path(target_root).resolve()
    )
    if Path(sys.path[0]).resolve() != worktree_root:
        sys.path.insert(0, str(worktree_root))
    route_authority = _install_target_local_route_module(worktree_root)
    from src.components import workspace_paths

    runner_name = "src.research_infra.replay_acceleration_attempt5_typed_sparse_runner"
    prior_runner = sys.modules.get(runner_name)
    if prior_runner is not None and (
        Path(prior_runner.MAIN_REPO_ROOT).resolve() != worktree_root
        or Path(prior_runner.ROOT).resolve() != worktree_root
    ):
        # A long test session (or caller) already imported the runner WITHOUT
        # the patched resolver, so its module-level roots bind the integration
        # repository's H1 fallback. That cached module is exactly the
        # contamination this loader exists to refuse -- but refusing a cache is
        # not neutralizing it: import a fresh copy under the patch for OUR use
        # and restore the cached one afterward so the rest of the session keeps
        # its object identity. The root checks below still fail closed if even
        # a fresh import cannot bind the target tree.
        sys.modules.pop(runner_name, None)
    try:
        with patch.object(
            workspace_paths,
            "resolve_gtos_integration_repo",
            lambda _active_root, **_kwargs: worktree_root,
        ):
            runner = importlib.import_module(runner_name)
    finally:
        if (
            prior_runner is not None
            and sys.modules.get(runner_name) is not prior_runner
        ):
            sys.modules[runner_name] = prior_runner
    if Path(runner.ROOT).resolve() != worktree_root:
        raise FullFlowHarnessError(
            f"target_runner_root_mismatch:{runner.ROOT}:{worktree_root}"
        )
    if Path(runner.MAIN_REPO_ROOT).resolve() != worktree_root:
        raise FullFlowHarnessError("integration_repository_import_detected")
    config = runner.build_config(runner.PROFILE_REPAIRED)
    if not isinstance(config, dict):
        raise FullFlowHarnessError("accepted_repaired_profile_config_invalid")
    _CONFIG_LOADER_AUTHORITY = {
        **route_authority,
        "target_head": _git_output(worktree_root, "rev-parse", "HEAD"),
        "target_tree": _git_output(worktree_root, "rev-parse", "HEAD^{tree}"),
        "target_status_porcelain_sha256": stable_sha256(
            _git_output(worktree_root, "status", "--porcelain=v1")
        ),
        "runner_path": str(Path(inspect.getsourcefile(runner) or "").resolve()),
        "runner_sha256": file_sha256(Path(inspect.getsourcefile(runner) or "")),
        "profile": runner.PROFILE_REPAIRED,
        "config_root_sha256": stable_sha256(config),
        "integration_module_imported": False,
        "external_json_safe_api_adapters": list(_EXTERNAL_ADAPTER_AUTHORITY),
    }
    return config


def _manifest_root(payload: Mapping[str, Any], field: str) -> str:
    core = dict(payload)
    core.pop(field, None)
    return stable_sha256(core)


def _logical_repo_root(lane_root: Path, manifest: Mapping[str, Any]) -> Path:
    relative = Path(str(manifest.get("lane_root_repo_relpath") or ""))
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise FullFlowHarnessError("lane_manifest_logical_root_binding_invalid")
    candidate = lane_root.resolve()
    for _part in relative.parts:
        candidate = candidate.parent
    if (candidate / relative).resolve() != lane_root.resolve():
        raise FullFlowHarnessError("lane_manifest_logical_root_binding_mismatch")
    return candidate


def _bound_regular_file(root: Path, relative: str) -> Path:
    raw = Path(relative)
    if raw.is_absolute() or not raw.parts or ".." in raw.parts:
        raise FullFlowHarnessError(f"source_relative_path_invalid:{relative}")
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise FullFlowHarnessError(f"source_path_escape:{relative}") from exc
    if path.is_symlink() or not path.is_file():
        raise FullFlowHarnessError(f"source_file_missing_or_symlink:{relative}")
    return path


def _scan_ordered_bid_ask_tick_component(
    *,
    path: Path,
    symbol: str,
    window_id: str,
    file_bytes_sha256: str,
    broker_clock_rule: str,
    raw_broker_epoch_preserved: bool,
) -> dict[str, Any]:
    """Prove exact paired BID/ASK chronology over the preregistered interval."""

    interval_start = datetime.fromisoformat(
        f"{RAW_COMPARATOR_START}T00:00:00+00:00"
    )
    interval_end = datetime.fromisoformat(
        f"{RAW_COMPARATOR_END}T23:59:59.999999+00:00"
    )
    physical_rows = 0
    selected_rows = 0
    invalid_pair_rows = 0
    utc_string_projection_mismatches = 0
    raw_broker_epoch_rule_mismatches = 0
    chronology_regressions = 0
    prior: datetime | None = None
    selected_first: datetime | None = None
    selected_last: datetime | None = None
    with path.open("rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            physical_rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FullFlowHarnessError(
                    f"tick_json_invalid:{symbol}:{window_id}:{line_number}"
                ) from exc
            if not isinstance(row, Mapping):
                raise FullFlowHarnessError(
                    f"tick_row_not_mapping:{symbol}:{window_id}:{line_number}"
                )
            stamp = _explicit_utc_datetime(
                row.get("ts_utc"),
                field=f"tick[{symbol}:{window_id}:{line_number}].ts_utc",
            )
            if prior is not None and stamp < prior:
                chronology_regressions += 1
            prior = stamp
            time_value = _explicit_utc_datetime(
                row.get("time"),
                field=f"tick[{symbol}:{window_id}:{line_number}].time",
            )
            utc_epoch_msc = int(stamp.timestamp()) * 1000 + stamp.microsecond // 1000
            if time_value != stamp:
                utc_string_projection_mismatches += 1
            if broker_clock_rule != "new_york_plus_7" or not raw_broker_epoch_preserved:
                raw_broker_epoch_rule_mismatches += 1
            else:
                ny_offset = stamp.astimezone(
                    ZoneInfo("America/New_York")
                ).utcoffset()
                if ny_offset is None:
                    raw_broker_epoch_rule_mismatches += 1
                else:
                    server_offset_msc = int(
                        (ny_offset + timedelta(hours=7)).total_seconds() * 1000
                    )
                    if row.get("time_msc") != utc_epoch_msc + server_offset_msc:
                        raw_broker_epoch_rule_mismatches += 1
            if not interval_start <= stamp <= interval_end:
                continue
            selected_rows += 1
            selected_first = stamp if selected_first is None else selected_first
            selected_last = stamp
            bid = row.get("bid")
            ask = row.get("ask")
            if (
                isinstance(bid, bool)
                or isinstance(ask, bool)
                or not isinstance(bid, (int, float))
                or not isinstance(ask, (int, float))
                or not math.isfinite(float(bid))
                or not math.isfinite(float(ask))
                or float(bid) <= 0.0
                or float(ask) < float(bid)
            ):
                invalid_pair_rows += 1
    if (
        selected_rows == 0
        or invalid_pair_rows
        or utc_string_projection_mismatches
        or raw_broker_epoch_rule_mismatches
        or chronology_regressions
    ):
        raise FullFlowHarnessError(
            "ordered_bid_ask_tick_component_invalid:"
            f"{symbol}:{window_id}:selected={selected_rows}:pairs={invalid_pair_rows}:"
            f"utc_strings={utc_string_projection_mismatches}:"
            f"broker_epoch={raw_broker_epoch_rule_mismatches}:"
            f"chronology={chronology_regressions}"
        )
    body = {
        "schema": f"{SOURCE_AUTHORITY_SCHEMA}.ordered_bid_ask_component.v1",
        "symbol": symbol,
        "window_id": window_id,
        "path": str(path),
        "file_bytes_sha256": file_bytes_sha256,
        "physical_row_count": physical_rows,
        "selected_interval": [RAW_COMPARATOR_START, RAW_COMPARATOR_END],
        "selected_ordered_bid_ask_row_count": selected_rows,
        "selected_first_utc": selected_first.isoformat() if selected_first else None,
        "selected_last_utc": selected_last.isoformat() if selected_last else None,
        "paired_bid_ask_invalid_row_count": invalid_pair_rows,
        "time_equals_ts_utc_mismatch_count": utc_string_projection_mismatches,
        "time_msc_basis": "raw_broker_wall_clock_epoch_preserved",
        "broker_clock_rule": broker_clock_rule,
        "raw_broker_epoch_preserved": raw_broker_epoch_preserved,
        "raw_broker_time_msc_rule_mismatch_count": raw_broker_epoch_rule_mismatches,
        "chronology_regression_count": chronology_regressions,
        "intrabar_order_event_coverage": "NOT_AVAILABLE",
        "broker_order_lifecycle_truth_satisfied": False,
    }
    return {**body, "component_root_sha256": stable_sha256(body)}


def verify_real_source_estates(
    *,
    repo_root: Path | None = None,
    lane_root: Path = DEFAULT_LANE_HOLD_ROOT,
    packet_root: Path = DEFAULT_P1_PACKET_ROOT,
    verify_payload_bytes: bool = True,
) -> dict[str, Any]:
    """Bind the two declared source estates without reading semantic sidecars."""

    repo_root = HARNESS_REPO_ROOT if repo_root is None else repo_root
    lane_root = lane_root.resolve()
    packet_root = packet_root.resolve()
    registry_path = lane_root / "LANE_INPUT_REGISTRY.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    if registry.get("registry_root_sha256") != _manifest_root(
        registry, "registry_root_sha256"
    ):
        raise FullFlowHarnessError("lane_registry_root_mismatch")
    registry_windows = registry.get("windows")
    if not isinstance(registry_windows, Mapping):
        raise FullFlowHarnessError("lane_registry_windows_missing")
    manifests: dict[str, dict[str, Any]] = {}
    manifest_bindings: list[dict[str, Any]] = []
    file_bindings: list[dict[str, Any]] = []
    tick_component_checks: list[dict[str, Any]] = []
    logical_root: Path | None = None
    for window_id in ("october_2025", "november_2025"):
        entry = registry_windows.get(window_id)
        if not isinstance(entry, Mapping):
            raise FullFlowHarnessError(f"lane_registry_window_missing:{window_id}")
        manifest_path = _bound_regular_file(lane_root, str(entry["source_manifest"]))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (
            manifest.get("manifest_root_sha256")
            != entry.get("source_manifest_root_sha256")
            or manifest.get("manifest_root_sha256")
            != _manifest_root(manifest, "manifest_root_sha256")
            or manifest.get("window_id") != window_id
            or manifest.get("campaign_sealed") is not False
            or manifest.get("economic_outcomes_read") is not False
        ):
            raise FullFlowHarnessError(f"lane_manifest_binding_invalid:{window_id}")
        current_logical = _logical_repo_root(lane_root, manifest)
        if logical_root is None:
            logical_root = current_logical
        elif logical_root != current_logical:
            raise FullFlowHarnessError("lane_logical_root_changed_between_manifests")
        manifest_file_bytes_sha256 = file_sha256(manifest_path)
        bars = [dict(row) for row in manifest.get("bar_sources") or ()]
        expected_cells = {
            (symbol, timeframe)
            for symbol in timewarp.GTOS_24_SYMBOL_SURFACE
            for timeframe in ("D1", "H4", "M15", "M1")
        }
        actual_cells = {
            (str(row.get("symbol")), str(row.get("timeframe"))) for row in bars
        }
        if actual_cells != expected_cells or len(bars) != 96:
            raise FullFlowHarnessError(f"lane_bar_surface_incomplete:{window_id}")
        for row in [*bars, *[dict(item) for item in manifest.get("tick_sources") or ()]]:
            actual = _bound_regular_file(current_logical, str(row["repo_relpath"]))
            actual_sha = file_sha256(actual) if verify_payload_bytes else None
            if verify_payload_bytes and actual_sha != row.get("sha256"):
                raise FullFlowHarnessError(
                    f"lane_payload_sha256_mismatch:{window_id}:{row['repo_relpath']}"
                )
            if verify_payload_bytes and row.get("timeframe") in (None, "TICK"):
                tick_check = _scan_ordered_bid_ask_tick_component(
                    path=actual,
                    symbol=str(row.get("symbol") or ""),
                    window_id=window_id,
                    file_bytes_sha256=str(actual_sha),
                    broker_clock_rule=str(row.get("broker_clock_rule") or ""),
                    raw_broker_epoch_preserved=(
                        row.get("raw_broker_epoch_preserved") is True
                    ),
                )
                if tick_check["physical_row_count"] != int(
                    row.get("row_count") or -1
                ):
                    raise FullFlowHarnessError(
                        f"tick_physical_row_count_mismatch:{window_id}:"
                        f"{row.get('symbol')}"
                    )
                tick_component_checks.append(tick_check)
            file_bindings.append(
                {
                    "estate": f"lane_{window_id}",
                    "window_id": window_id,
                    "symbol": row.get("symbol"),
                    "timeframe": row.get("timeframe", "TICK"),
                    "path": str(actual),
                    "reader": (
                        "tick_jsonl_v1"
                        if row.get("timeframe") in (None, "TICK")
                        else "ohlcv_csv_v1"
                    ),
                    "manifest_kind": "lane_self_hash_v1",
                    "manifest_path": str(manifest_path),
                    "manifest_file_bytes_sha256": manifest_file_bytes_sha256,
                    "manifest_semantic_root_sha256": manifest[
                        "manifest_root_sha256"
                    ],
                    "manifest_member_logical_path": row.get("repo_relpath"),
                    "declared_file_bytes_sha256": row.get("sha256"),
                    "verified_file_bytes_sha256": actual_sha,
                    "declared_row_count": row.get("row_count"),
                    "first_utc": row.get("first_utc"),
                    "last_utc": row.get("last_utc"),
                    "source_family": row.get("source_family"),
                    "time_column_basis": row.get("time_column_basis"),
                    "broker_clock_rule": row.get("broker_clock_rule"),
                }
            )
        manifests[window_id] = manifest
        manifest_bindings.append(
            {
                "window_id": window_id,
                "path": str(manifest_path),
                "file_bytes_sha256": manifest_file_bytes_sha256,
                "manifest_root_sha256": manifest["manifest_root_sha256"],
                "registered_source_plan_digest_sha256": entry.get(
                    "canonical_source_plan_digest_sha256"
                ),
                "window": manifest["window"],
                "bar_source_count": len(bars),
                "tick_symbols": sorted(
                    str(row["symbol"]) for row in manifest.get("tick_sources") or ()
                ),
                "tick_gap_symbols": sorted(
                    str(row["symbol"]) for row in manifest.get("tick_gaps") or ()
                ),
            }
        )
    committed_path = (repo_root / P1_COMMITTED_MANIFEST).resolve()
    committed = json.loads(committed_path.read_text(encoding="utf-8"))
    packet_manifest_path = packet_root / "PACKET_MANIFEST.json"
    packet_manifest = json.loads(packet_manifest_path.read_text(encoding="utf-8"))
    packet_manifest_file_bytes_sha256 = file_sha256(packet_manifest_path)
    if (
        packet_manifest_file_bytes_sha256
        != committed["external_packet_manifest"]["sha256"]
        or packet_manifest.get("packet_payload_root_sha256")
        != committed.get("packet_payload_root_sha256")
        or packet_manifest.get("status") != "FROZEN"
    ):
        raise FullFlowHarnessError("p1_packet_manifest_binding_invalid")
    payload_descriptors = [dict(row) for row in packet_manifest.get("payload_files") or ()]
    payload_root = stable_sha256(
        {
            "schema": "gtos.p1-upstream-packet-payload.v1",
            "files": payload_descriptors,
        }
    )
    if payload_root != packet_manifest["packet_payload_root_sha256"]:
        raise FullFlowHarnessError("p1_packet_payload_root_mismatch")
    verified_payloads: list[dict[str, Any]] = []
    for descriptor in payload_descriptors:
        path = _bound_regular_file(packet_root, str(descriptor["path"]))
        actual_sha = file_sha256(path) if verify_payload_bytes else None
        if verify_payload_bytes and (
            actual_sha != descriptor.get("sha256")
            or path.stat().st_size != int(descriptor.get("bytes") or -1)
        ):
            raise FullFlowHarnessError(
                f"p1_payload_binding_mismatch:{descriptor['path']}"
            )
        verified_payloads.append(
            {
                "path": str(path),
                "relative_path": descriptor["path"],
                "reader": (
                    "ohlcv_jsonl_gzip_v1"
                    if str(descriptor["path"]).startswith("series/")
                    else None
                ),
                "manifest_kind": "p1_packet_payload_v1",
                "manifest_path": str(packet_manifest_path),
                "manifest_file_bytes_sha256": packet_manifest_file_bytes_sha256,
                "manifest_semantic_root_sha256": packet_manifest[
                    "packet_payload_root_sha256"
                ],
                "manifest_member_logical_path": descriptor["path"],
                "declared_file_bytes_sha256": descriptor["sha256"],
                "verified_file_bytes_sha256": actual_sha,
                "bytes": descriptor["bytes"],
                "semantic_use": (
                    "raw_H1_or_M15_only"
                    if str(descriptor["path"]).startswith("series/")
                    else "hash_binding_only_never_loaded_as_decision_authority"
                ),
            }
        )
    series = packet_manifest.get("series")
    if not isinstance(series, Mapping) or set(series) != set(timewarp.GTOS_24_SYMBOL_SURFACE):
        raise FullFlowHarnessError("p1_series_symbol_surface_incomplete")
    for symbol, timeframes in series.items():
        if set(timeframes) != {"H1", "M15"}:
            raise FullFlowHarnessError(f"p1_series_timeframe_surface_incomplete:{symbol}")
        for timeframe in ("H1", "M15"):
            descriptor = timeframes[timeframe]
            if not (
                str(descriptor.get("first_utc")) <= f"{RAW_COMPARATOR_START}T00:00:00"
                and str(descriptor.get("last_utc")) >= f"{RAW_COMPARATOR_END}T00:00:00"
            ):
                raise FullFlowHarnessError(
                    f"p1_series_interval_not_covered:{symbol}:{timeframe}"
                )
    missing_ticks = sorted(set(timewarp.GTOS_24_SYMBOL_SURFACE) - set(TICK_COVERED_SYMBOLS))
    tick_interval_by_symbol = {
        symbol: {
            "component_count": len(
                [row for row in tick_component_checks if row["symbol"] == symbol]
            ),
            "selected_ordered_bid_ask_row_count": sum(
                int(row["selected_ordered_bid_ask_row_count"])
                for row in tick_component_checks
                if row["symbol"] == symbol
            ),
            "component_roots_sha256": [
                row["component_root_sha256"]
                for row in tick_component_checks
                if row["symbol"] == symbol
            ],
            "intrabar_order_event_coverage": "NOT_AVAILABLE",
            "broker_order_lifecycle_truth_satisfied": False,
        }
        for symbol in TICK_COVERED_SYMBOLS
    }
    if verify_payload_bytes and (
        set(row["symbol"] for row in tick_component_checks)
        != set(TICK_COVERED_SYMBOLS)
        or any(
            row["component_count"] != 2
            or row["selected_ordered_bid_ask_row_count"] <= 0
            for row in tick_interval_by_symbol.values()
        )
    ):
        raise FullFlowHarnessError("ordered_bid_ask_tick_interval_coverage_incomplete")
    body = {
        "schema": SOURCE_AUTHORITY_SCHEMA,
        "status": "PASS",
        "requested_interval": [RAW_COMPARATOR_START, RAW_COMPARATOR_END],
        "requested_day_count": len(RAW_COMPARATOR_DAYS),
        "us_dst_transition_spanned": "2025-11-02",
        "lane_registry": {
            "path": str(registry_path),
            "file_bytes_sha256": file_sha256(registry_path),
            "registry_root_sha256": registry["registry_root_sha256"],
            "projection_window_ids": ["october_2025", "november_2025"],
            "march_manifest_opened": False,
            "march_source_rows_accessed": 0,
        },
        "lane_manifest_bindings": manifest_bindings,
        "lane_payload_file_bindings": file_bindings,
        "p1_committed_manifest": {
            "path": str(committed_path),
            "file_bytes_sha256": file_sha256(committed_path),
        },
        "p1_packet_manifest": {
            "path": str(packet_manifest_path),
            "file_bytes_sha256": packet_manifest_file_bytes_sha256,
            "packet_payload_root_sha256": payload_root,
            "payload_file_count": len(payload_descriptors),
            "timebase_authority": packet_manifest.get("timebase_authority"),
        },
        "p1_payload_bindings": verified_payloads,
        "semantic_source_estate_map": {
            "D1": "lane_october_and_november_registered_manifests",
            "H4": "lane_october_and_november_registered_manifests",
            "M15": "p1_raw_series_cross_checked_against_lane_registered_M15",
            "H1": "p1_raw_series_packet_verifier_derived_from_bound_M15",
            "M1": "lane_october_and_november_registered_manifests",
            "TICK": "lane_registered_only_for_four_symbols",
        },
        "expected_denominator_symbols": list(timewarp.GTOS_24_SYMBOL_SURFACE),
        "registered_bar_denominator_symbols": list(
            timewarp.GTOS_24_SYMBOL_SURFACE
        ),
        "registered_bar_denominator_exact_gtos_24": True,
        "all_24_bar_surface_complete": True,
        "all_24_bar_surface_claim_scope": (
            "registered_source_cell_inventory_only_not_completed_bar_truth"
        ),
        "loader_owned_source_receipts_attached": False,
        "independent_byte_reparse_and_completion_witness_validation": False,
        "result_bearing_chronology_coverage_complete": False,
        "result_use_scope": (
            "SOURCE_ESTATE_PREFLIGHT_ONLY_NOT_CANDIDATE_OR_ECONOMIC_AUTHORITY"
        ),
        "ordered_bid_ask_tick_covered_symbols": list(TICK_COVERED_SYMBOLS),
        "ordered_bid_ask_tick_missing_symbols": missing_ticks,
        "ordered_bid_ask_tick_coverage_count": len(TICK_COVERED_SYMBOLS),
        "ordered_bid_ask_tick_gap_count": len(missing_ticks),
        "ordered_bid_ask_tick_component_checks": tick_component_checks,
        "ordered_bid_ask_tick_interval_coverage_by_symbol": tick_interval_by_symbol,
        "ordered_bid_ask_tick_interval_schema_verified": verify_payload_bytes,
        "all_24_lifecycle_economics_class": "M1_MODELLED_NOT_BROKER_TRUE",
        "tick_subset_transfer_to_other_20_allowed": False,
        "exact_source_acquisition_requirement": {
            "symbols": missing_ticks,
            "interval": [RAW_COMPARATOR_START, RAW_COMPARATOR_END],
            "required": (
                "ordered true-UTC bid/ask ticks plus hash-bound broker symbol specs "
                "for every decision-to-terminal lifecycle interval"
            ),
        },
        "forbidden_semantic_payloads": [
            "identity_to_slice.jsonl.gz",
            "states/predecision_market_state.jsonl.gz",
        ],
        "forbidden_semantic_payloads_loaded": False,
        "prepared_or_stored_candidate_payload_consumed": False,
        "payload_bytes_verified": verify_payload_bytes,
    }
    return {**body, "source_authority_root_sha256": stable_sha256(body)}


def _merge_sources(
    first: timewarp.ResolvedSource,
    second: timewarp.ResolvedSource,
    *,
    source_family: str,
) -> timewarp.ResolvedSource:
    unique: dict[str, dict[str, Any]] = {}
    multiplicity: Counter[str] = Counter()
    exact_duplicate_count = 0
    for component_ordinal, source in enumerate((first, second)):
        for row_ordinal, raw_row in enumerate(source.rows):
            row = dict(raw_row)
            timestamp = _row_open_utc(
                row,
                field=(
                    f"merge_source[{component_ordinal}].rows[{row_ordinal}]"
                ),
            ).isoformat()
            multiplicity[timestamp] += 1
            previous = unique.get(timestamp)
            if previous is None:
                unique[timestamp] = row
                continue
            if strict_json_primitive(previous) != strict_json_primitive(row):
                raise FullFlowHarnessError(
                    "source_merge_conflicting_same_timestamp:"
                    f"{first.spec.symbol}:{first.spec.timeframe}:{timestamp}"
                )
            exact_duplicate_count += 1
    rows = tuple(
        row for _timestamp, row in sorted(unique.items())
    )
    grouped = timewarp.rows_by_day(rows)
    multiplicity_receipt_body = {
        "schema": f"{SOURCE_AUTHORITY_SCHEMA}.merge_multiplicity.v1",
        "symbol": first.spec.symbol,
        "timeframe": first.spec.timeframe,
        "component_resolved_source_identity_sha256s": [
            first.sha256,
            second.sha256,
        ],
        "input_occurrence_count": len(first.rows) + len(second.rows),
        "unique_timestamp_count": len(rows),
        "exact_duplicate_occurrence_count": exact_duplicate_count,
        "conflicting_same_timestamp_count": 0,
        "multiplicity_histogram": {
            str(count): occurrences
            for count, occurrences in sorted(
                Counter(multiplicity.values()).items()
            )
        },
        "ordered_timestamp_multiplicity_root_sha256": stable_sha256(
            [
                {"timestamp_utc": timestamp, "occurrence_count": count}
                for timestamp, count in sorted(multiplicity.items())
            ]
        ),
    }
    multiplicity_receipt = {
        **multiplicity_receipt_body,
        "receipt_root_sha256": stable_sha256(multiplicity_receipt_body),
    }
    identity = stable_sha256(
        {
            "components": [first.sha256, second.sha256],
            "canonical_rows_root_sha256": stable_sha256(rows),
            "merge_multiplicity_receipt_root_sha256": multiplicity_receipt[
                "receipt_root_sha256"
            ],
        }
    )
    spec = replace(
        first.spec,
        source_family=source_family,
        row_count=len(rows),
        sha256=identity,
        start_utc=str(rows[0].get("time_utc")) if rows else None,
        end_utc=str(rows[-1].get("time_utc")) if rows else None,
    )
    authorities: dict[str, dict[str, Any]] = {}
    for source in (first, second):
        for raw_day, raw_authority in source.day_source_authority.items():
            day = str(raw_day)
            authority = dict(raw_authority)
            previous = authorities.get(day)
            if previous is not None and strict_json_primitive(previous) != (
                strict_json_primitive(authority)
            ):
                raise FullFlowHarnessError(
                    "source_merge_day_authority_conflict:"
                    f"{first.spec.symbol}:{first.spec.timeframe}:{day}"
                )
            authorities[day] = authority
    return timewarp.ResolvedSource(
        spec=spec,
        rows=rows,
        rows_by_day=grouped,
        sha256=identity,
        day_counts={day: len(values) for day, values in grouped.items()},
        selected_status="selected_hash_bound_cross_manifest_interval_source",
        min_required_rows_per_day=max(
            int(first.min_required_rows_per_day or 0),
            int(second.min_required_rows_per_day or 0),
        ),
        source_gaps=tuple((*first.source_gaps, *second.source_gaps)),
        component_source_labels=tuple(
            (
                *first.component_source_labels,
                *second.component_source_labels,
                {"merge_multiplicity_receipt": multiplicity_receipt},
            )
        ),
        day_source_authority=authorities,
    )


def _load_p1_series(
    *,
    packet_root: Path,
    packet_manifest: Mapping[str, Any],
    symbol: str,
    timeframe: str,
    days: Sequence[str],
) -> timewarp.ResolvedSource:
    from src.research_infra import replay_acceleration_integrated_source as integrated

    descriptor = packet_manifest["series"][symbol][timeframe]
    path = _bound_regular_file(packet_root, str(descriptor["path"]))
    if file_sha256(path) != descriptor["sha256"]:
        raise FullFlowHarnessError(f"p1_series_sha256_mismatch:{symbol}:{timeframe}")
    normalized: list[dict[str, Any]] = []
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise FullFlowHarnessError(
                    f"p1_series_json_invalid:{symbol}:{timeframe}:{line_number}"
                ) from exc
            canonical = timewarp.normalize_row(row, symbol=symbol)
            if canonical is None:
                raise FullFlowHarnessError(
                    f"p1_series_time_invalid:{symbol}:{timeframe}:{line_number}"
                )
            normalized.append(canonical)
    minimum = (
        timewarp.M15_LIVE_LOOKBACK_MIN_TOTAL_ROWS
        if timeframe == "M15"
        else timewarp.HTF_MIN_TOTAL_ROWS["H1"]
    )
    selected, grouped, metadata = integrated.select_replay_lookback_window(
        normalized,
        timeframe=timeframe,
        days=days,
        min_total_rows=minimum,
    )
    if len(selected) < minimum:
        raise FullFlowHarnessError(f"p1_series_lookback_incomplete:{symbol}:{timeframe}")
    identity = stable_sha256(
        {
            "packet_payload_root_sha256": packet_manifest["packet_payload_root_sha256"],
            "file_bytes_sha256": descriptor["sha256"],
            "bounded_rows_root_sha256": stable_sha256(selected),
            "selection_metadata": metadata,
        }
    )
    spec = timewarp.SourceSpec(
        symbol=symbol,
        mapped_symbol=symbol,
        timeframe=timeframe,
        path=path,
        source_family=f"p1_packet_raw_{timeframe.lower()}_series",
        source_broker="FTMO",
        source_role="hash_bound_source_only_no_outcome_read",
        start_utc=str(selected[0]["time_utc"]),
        end_utc=str(selected[-1]["time_utc"]),
        row_count=len(selected),
        sha256=str(descriptor["sha256"]),
        export_tool="src.research_infra.p1_upstream_reconstruction",
        manifest_path="PACKET_MANIFEST.json",
        source_truth_scope=timewarp.SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        broker_lifecycle_truth_satisfied=False,
        ordered_tick_truth_satisfied=False,
    )
    return timewarp.ResolvedSource(
        spec=spec,
        rows=selected,
        rows_by_day=grouped,
        sha256=identity,
        day_counts={day: len(rows) for day, rows in grouped.items()},
        selected_status="selected_hash_bound_p1_raw_series_bounded_lookback",
        min_required_rows_per_day=minimum,
        component_source_labels=(
            {
                "packet_payload_root_sha256": packet_manifest[
                    "packet_payload_root_sha256"
                ],
                "file_bytes_sha256": descriptor["sha256"],
                "bounded_selection_metadata": metadata,
            },
        ),
    )


def load_real_source_bound_inputs(
    *,
    days: Sequence[str] = RAW_COMPARATOR_DAYS,
    lane_root: Path = DEFAULT_LANE_HOLD_ROOT,
    packet_root: Path = DEFAULT_P1_PACKET_ROOT,
    source_authority: Mapping[str, Any] | None = None,
) -> tuple[dict[str, dict[str, timewarp.ResolvedSource]], dict[str, Any]]:
    """Load the actual 24-symbol source interval; never load stored decisions."""

    if (
        not days
        or any(day not in RAW_COMPARATOR_DAYS for day in days)
        or tuple(days) != tuple(sorted(set(days)))
        or any(
            date.fromisoformat(days[index]) + timedelta(days=1)
            != date.fromisoformat(days[index + 1])
            for index in range(len(days) - 1)
        )
    ):
        raise FullFlowHarnessError("real_source_loader_interval_not_preregistered")
    authority = dict(
        source_authority
        or verify_real_source_estates(
            lane_root=lane_root, packet_root=packet_root, verify_payload_bytes=True
        )
    )
    load_repaired_replay_config()
    from src.research_infra import lane_rematerialization as lane

    registry = json.loads((lane_root / "LANE_INPUT_REGISTRY.json").read_text())
    manifests = {
        window_id: json.loads(
            (lane_root / registry["windows"][window_id]["source_manifest"]).read_text()
        )
        for window_id in ("october_2025", "november_2025")
    }
    logical_root = _logical_repo_root(lane_root, manifests["october_2025"])

    def resolver(window_id: str, *, skip_tick: bool) -> Any:
        manifest_path = lane_root / registry["windows"][window_id]["source_manifest"]
        manifest = manifests[window_id]
        specs, _tick_contract = lane._tick_authority(
            repo_root=logical_root,
            manifest=manifest,
            manifest_path=manifest_path,
        )
        return lane.LaneBroadSourceResolver(
            use_native_h1=False,
            skip_tick_source=skip_tick,
            verbose=False,
            source_accelerator=lane.LaneReplaySourceAccelerator(
                repo_root=logical_root,
                manifest_path=manifest_path,
                source_plan_digest_sha256=registry["windows"][window_id].get(
                    "canonical_source_plan_digest_sha256"
                ),
            ),
            bound_tick_source_specs=specs,
            bound_tick_source_gaps=lane._tick_gaps(manifest),
            bound_tick_logical_repo_root=logical_root,
            sealed_tick_full_component_set=True,
            tick_sparse_cache_root=None,
        )

    october_days = tuple(day for day in days if day <= "2025-10-31")
    november_days = tuple(day for day in days if day >= "2025-11-01")
    oct_sources = (
        resolver("october_2025", skip_tick=True).build_sources_for_days(
            october_days, symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE)
        )
        if october_days
        else {}
    )
    nov_sources = (
        resolver("november_2025", skip_tick=True).build_sources_for_days(
            november_days, symbols=tuple(timewarp.GTOS_24_SYMBOL_SURFACE)
        )
        if november_days
        else {}
    )
    if any(
        sources and set(sources) != set(timewarp.GTOS_24_SYMBOL_SURFACE)
        for sources in (oct_sources, nov_sources)
    ):
        raise FullFlowHarnessError("lane_resolver_24_symbol_surface_incomplete")
    packet_manifest = json.loads((packet_root / "PACKET_MANIFEST.json").read_text())
    merged: dict[str, dict[str, timewarp.ResolvedSource]] = {}
    m15_cross_checks: list[dict[str, Any]] = []
    weekend_calendar_validation: list[dict[str, Any]] = []
    for symbol in timewarp.GTOS_24_SYMBOL_SURFACE:
        source_map: dict[str, timewarp.ResolvedSource] = {}
        for timeframe in ("D1", "H4", "M1"):
            if oct_sources and nov_sources:
                source_map[timeframe] = _merge_sources(
                    oct_sources[symbol][timeframe],
                    nov_sources[symbol][timeframe],
                    source_family=(
                        "lane_registered_october_november_m1"
                        if timeframe == "M1"
                        else f"lane_registered_october_november_{timeframe.lower()}"
                    ),
                )
            else:
                only = oct_sources or nov_sources
                source_map[timeframe] = only[symbol][timeframe]
        packet_m15 = _load_p1_series(
            packet_root=packet_root,
            packet_manifest=packet_manifest,
            symbol=symbol,
            timeframe="M15",
            days=days,
        )
        lane_m15 = (
            _merge_sources(
                oct_sources[symbol]["M15"],
                nov_sources[symbol]["M15"],
                source_family="lane_registered_october_november_m15_crosscheck",
            )
            if oct_sources and nov_sources
            else (oct_sources or nov_sources)[symbol]["M15"]
        )
        lane_by_time = {
            str(row.get("time_utc")): row for row in lane_m15.rows
        }
        overlap = [
            row for row in packet_m15.rows if str(row.get("time_utc")) in lane_by_time
        ]
        mismatches = [
            str(row.get("time_utc"))
            for row in overlap
            if any(
                float(row.get(field) or 0.0)
                != float(lane_by_time[str(row.get("time_utc"))].get(field) or 0.0)
                for field in ("open", "high", "low", "close", "volume")
            )
        ]
        if not overlap or mismatches:
            raise FullFlowHarnessError(f"p1_lane_m15_semantic_mismatch:{symbol}")
        m15_cross_checks.append(
            {
                "symbol": symbol,
                "overlap_row_count": len(overlap),
                "mismatch_count": len(mismatches),
                "status": "exact_normalized_ohlcv_match",
            }
        )
        weekend_rows = [
            (stamp, row)
            for row in packet_m15.rows
            if (stamp := timewarp.parse_row_time(row)) is not None
            and date(2025, 10, 31) <= stamp.date() <= date(2025, 11, 3)
        ]
        gaps = [
            (right[0] - left[0], left[0], right[0])
            for left, right in zip(weekend_rows, weekend_rows[1:])
        ]
        maximum = max(gaps, default=(timedelta(0), None, None), key=lambda row: row[0])
        scheduled_weekend = bool(
            maximum[1] is not None
            and maximum[1].weekday() == 4
            and maximum[2].weekday() in {6, 0}
        )
        weekend_calendar_validation.append(
            {
                "symbol": symbol,
                "maximum_gap_seconds": int(maximum[0].total_seconds()),
                "gap_start_utc": maximum[1].isoformat() if maximum[1] else None,
                "gap_end_utc": maximum[2].isoformat() if maximum[2] else None,
                "status": (
                    "market_calendar_weekend_closure"
                    if scheduled_weekend
                    else "continuous_or_instrument_session_calendar"
                ),
                "treated_as_missing_source": False,
            }
        )
        source_map["M15"] = packet_m15
        source_map["H1"] = _load_p1_series(
            packet_root=packet_root,
            packet_manifest=packet_manifest,
            symbol=symbol,
            timeframe="H1",
            days=days,
        )
        merged[symbol] = source_map

    combined_tick_specs: dict[str, tuple[timewarp.SourceSpec, ...]] = defaultdict(tuple)
    combined_gaps: dict[str, tuple[str, ...]] = {}
    for window_id in ("october_2025", "november_2025"):
        manifest_path = lane_root / registry["windows"][window_id]["source_manifest"]
        specs, _contract = lane._tick_authority(
            repo_root=logical_root,
            manifest=manifests[window_id],
            manifest_path=manifest_path,
        )
        for symbol, rows in specs.items():
            combined_tick_specs[symbol] = (*combined_tick_specs[symbol], *rows)
        combined_gaps.update(lane._tick_gaps(manifests[window_id]))
    tick_resolver = lane.LaneBroadSourceResolver(
        use_native_h1=False,
        skip_tick_source=False,
        verbose=False,
        source_accelerator=lane.LaneReplaySourceAccelerator(
            repo_root=logical_root,
            manifest_path=(lane_root / registry["windows"]["october_2025"]["source_manifest"]),
        ),
        bound_tick_source_specs=dict(combined_tick_specs),
        bound_tick_source_gaps=combined_gaps,
        bound_tick_logical_repo_root=logical_root,
        sealed_tick_full_component_set=True,
        tick_sparse_cache_root=None,
    )
    for symbol in TICK_COVERED_SYMBOLS:
        tick = tick_resolver.resolve_tick(symbol, source_authority_days=tuple(days))
        if tick is None:
            raise FullFlowHarnessError(f"combined_tick_source_missing:{symbol}")
        merged[symbol]["TICK"] = tick
    merge_multiplicity_receipts = [
        {
            "symbol": symbol,
            "timeframe": timeframe,
            **dict(label["merge_multiplicity_receipt"]),
        }
        for symbol, source_map in sorted(merged.items())
        for timeframe, source in sorted(source_map.items())
        for label in source.component_source_labels
        if isinstance(label, Mapping)
        and isinstance(label.get("merge_multiplicity_receipt"), Mapping)
    ]
    load_body = {
        "schema": f"{SOURCE_AUTHORITY_SCHEMA}.loaded_projection",
        "status": "PASS",
        "source_authority_root_sha256": authority[
            "source_authority_root_sha256"
        ],
        "days": list(days),
        "symbols": list(timewarp.GTOS_24_SYMBOL_SURFACE),
        "m15_cross_checks": m15_cross_checks,
        "source_merge_multiplicity_receipts": merge_multiplicity_receipts,
        "weekend_calendar_validation": weekend_calendar_validation,
        "weekend_gap_treated_as_missing_source": False,
        "source_estate_semantic_map": authority["semantic_source_estate_map"],
        "prepared_day_pack": None,
        "stored_candidates_or_outcomes_loaded": False,
        "future_rows_consumed": 0,
        "march_manifest_opened": False,
        "march_source_rows_accessed": 0,
        "config_loader_authority": _CONFIG_LOADER_AUTHORITY,
    }
    return merged, {**load_body, "loaded_projection_root_sha256": stable_sha256(load_body)}


def run_deterministic_smoke() -> dict[str, Any]:
    sources, fixture = build_deterministic_smoke_sources()
    campaign = timewarp.CampaignConfig(
        name="wave21_full_flow_raw_generation_smoke",
        phase="wave21_full_flow_engineering_smoke",
        profile="repaired_package_conversion_v3",
        days=(fixture["trading_day"],),
        pending_expiry_minutes=timewarp.REPAIRED_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=True,
        partial_be_runner=True,
        max_candidates_per_symbol_window=0,
        run_smoke_subset=False,
        materialize_packet_sidecars=False,
        materialize_semantic_diagnostics=False,
    )
    executed = execute_full_flow(
        campaign=campaign,
        config=load_repaired_replay_config(),
        sources=sources,
        result_scope="deterministic_smoke",
    )
    return {**executed, "fixture": fixture}


def _atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(f".{path.name}.tmp")
    temp.write_text(
        json.dumps(
            strict_json_primitive(payload),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def _atomic_write_jsonl_gz(
    path: Path, rows: Iterable[Mapping[str, Any]]
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp")
    with temp.open("xb") as raw:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6
        ) as compressed:
            with io.TextIOWrapper(compressed, encoding="utf-8", newline="\n") as handle:
                for row in rows:
                    handle.write(
                        json.dumps(
                            strict_json_primitive(row),
                            sort_keys=True,
                            separators=(",", ":"),
                            ensure_ascii=False,
                            allow_nan=False,
                        )
                        + "\n"
                    )
        raw.flush()
        os.fsync(raw.fileno())
    temp.replace(path)


def write_smoke_artifacts(output_dir: Path, payload: Mapping[str, Any]) -> None:
    _atomic_write_json(output_dir / "harness_smoke_fixture.json", payload["fixture"])
    _atomic_write_jsonl_gz(
        output_dir / "harness_smoke_stage_ledger.jsonl.gz", payload["stage_rows"]
    )
    _atomic_write_json(
        output_dir / "harness_smoke_comparator_fingerprint.json",
        payload["fingerprint"],
    )
    _atomic_write_json(output_dir / "harness_smoke_run_receipt.json", payload["receipt"])


def verify_written_artifacts(output_dir: Path) -> dict[str, Any]:
    paths = {
        "fixture": output_dir / "harness_smoke_fixture.json",
        "stage_ledger": output_dir / "harness_smoke_stage_ledger.jsonl.gz",
        "fingerprint": output_dir / "harness_smoke_comparator_fingerprint.json",
        "receipt": output_dir / "harness_smoke_run_receipt.json",
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FullFlowHarnessError(f"written_artifacts_missing:{','.join(missing)}")
    receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
    stored_receipt_root = receipt.pop("receipt_root_sha256", None)
    if stored_receipt_root != stable_sha256(receipt):
        raise FullFlowHarnessError("written_receipt_root_mismatch")
    fingerprint = json.loads(paths["fingerprint"].read_text(encoding="utf-8"))
    stored_fingerprint_root = fingerprint.pop("fingerprint_root_sha256", None)
    if stored_fingerprint_root != stable_sha256(fingerprint):
        raise FullFlowHarnessError("written_fingerprint_root_mismatch")
    with gzip.open(paths["stage_ledger"], "rt", encoding="utf-8") as handle:
        stage_rows = [json.loads(line) for line in handle if line.strip()]
    expected_count = sum(
        int(stage["row_count"])
        for stage in receipt["comparator_fingerprint"]["stages"].values()
    )
    if len(stage_rows) != expected_count:
        raise FullFlowHarnessError("written_stage_ledger_row_count_mismatch")
    return {
        "schema": f"{SCHEMA}.artifact_verification",
        "status": "PASS",
        "artifact_sha256": {
            name: file_sha256(path) for name, path in sorted(paths.items())
        },
        "stage_row_count": len(stage_rows),
        "receipt_root_sha256": stored_receipt_root,
        "fingerprint_root_sha256": stored_fingerprint_root,
    }


def _safe_label(label: str) -> str:
    normalized = str(label or "").strip()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,80}", normalized):
        raise FullFlowHarnessError(f"artifact_label_invalid:{label}")
    return normalized


def write_run_artifacts(
    output_dir: Path,
    *,
    label: str,
    payload: Mapping[str, Any],
    source_authority: Mapping[str, Any] | None = None,
    loaded_projection: Mapping[str, Any] | None = None,
    resource_measurement: Mapping[str, Any] | None = None,
) -> dict[str, Path]:
    label = _safe_label(label)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "stage_ledger": output_dir / f"harness_{label}_stage_ledger.jsonl.gz",
        "fingerprint": output_dir / f"harness_{label}_comparator_fingerprint.json",
        "receipt": output_dir / f"harness_{label}_run_receipt.json",
        "source_authority": output_dir / f"harness_{label}_source_authority.json",
        "loaded_projection": output_dir / f"harness_{label}_loaded_projection.json",
        "resource": output_dir / f"harness_{label}_resource_measurement.json",
    }
    existing_stage = payload.get("stage_ledger_path")
    if existing_stage:
        if Path(str(existing_stage)).resolve() != paths["stage_ledger"].resolve():
            raise FullFlowHarnessError("prewritten_stage_ledger_path_mismatch")
    else:
        _atomic_write_jsonl_gz(paths["stage_ledger"], payload.get("stage_rows", ()))
    _atomic_write_json(paths["fingerprint"], payload["fingerprint"])
    _atomic_write_json(paths["receipt"], payload["receipt"])
    _atomic_write_json(paths["source_authority"], source_authority or {})
    _atomic_write_json(paths["loaded_projection"], loaded_projection or {})
    _atomic_write_json(paths["resource"], resource_measurement or {})
    return paths


def _inclusive_days(start: str, end: str) -> tuple[str, ...]:
    first = date.fromisoformat(start)
    last = date.fromisoformat(end)
    if first > last:
        raise FullFlowHarnessError("source_run_interval_reversed")
    return tuple(
        (first + timedelta(days=offset)).isoformat()
        for offset in range((last - first).days + 1)
    )


def _raw_campaign(days: Sequence[str], *, truth_mode: bool) -> timewarp.CampaignConfig:
    return timewarp.CampaignConfig(
        name=(
            "wave21_full_flow_raw_source_dst_truth_population"
            if truth_mode
            else "wave21_full_flow_raw_source_engineering_comparator"
        ),
        phase=(
            "wave21_full_flow_truth"
            if truth_mode
            else "wave21_full_flow_engineering_comparator"
        ),
        profile="repaired_package_conversion_v3",
        days=tuple(days),
        pending_expiry_minutes=timewarp.REPAIRED_PENDING_EXPIRY_MINUTES,
        use_repaired_pending_expiry=True,
        partial_be_runner=True,
        max_candidates_per_symbol_window=0,
        run_smoke_subset=False,
        materialize_packet_sidecars=False,
        materialize_semantic_diagnostics=False,
    )


def _deep_size(value: Any, seen: set[int] | None = None) -> int:
    seen = set() if seen is None else seen
    identifier = id(value)
    if identifier in seen:
        return 0
    seen.add(identifier)
    size = sys.getsizeof(value)
    if isinstance(value, Mapping):
        return size + sum(
            _deep_size(key, seen) + _deep_size(item, seen)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple, set, frozenset)):
        return size + sum(_deep_size(item, seen) for item in value)
    return size


def _resource_measurement(
    *, result: Mapping[str, Any], output_paths: Sequence[Path]
) -> dict[str, Any]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    max_rss_bytes = int(usage.ru_maxrss)
    # Darwin reports bytes; Linux reports KiB.
    if sys.platform != "darwin":
        max_rss_bytes *= 1024
    disk_bytes = sum(path.stat().st_size for path in output_paths if path.is_file())
    stat = os.statvfs(active_target_root())
    available_memory_bytes = None
    physical_memory_bytes = None
    try:
        physical_memory_bytes = int(
            subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True).strip()
        )
        vm_text = subprocess.check_output(["vm_stat"], text=True)
        page_match = re.search(r"page size of (\d+) bytes", vm_text)
        page_size = int(page_match.group(1)) if page_match else 4096
        pages = {}
        for line in vm_text.splitlines():
            match = re.match(r"([^:]+):\s+([0-9]+)\.", line)
            if match:
                pages[match.group(1)] = int(match.group(2))
        available_memory_bytes = page_size * sum(
            pages.get(key, 0)
            for key in ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable")
        )
    except (OSError, subprocess.CalledProcessError, ValueError):
        pass
    return {
        "schema": f"{SCHEMA}.resource_measurement",
        "process_max_rss_bytes": max_rss_bytes,
        "resident_result_deep_size_bytes": _deep_size(result.get("ledgers", {})),
        "written_artifact_bytes": disk_bytes,
        "filesystem_free_bytes": int(stat.f_bavail * stat.f_frsize),
        "host_physical_memory_bytes": physical_memory_bytes,
        "host_available_memory_bytes": available_memory_bytes,
        "compact_state_views": {
            "streamed_exact": ["asof", "missed"],
            "identity_observed": ["candidate", "order", "trade"],
            "completed_prefix_retained_projection": ["candidate"],
            "resident_for_stateful_terminal_reconciliation": [
                "candidate_scalar_identity_index",
                "order",
                "trade",
                "scorecard",
                "oracle",
                "exit",
                "account",
                "event",
                "daily",
            ],
            "campaign_split_or_state_reset": False,
        },
    }


def run_source_bound_worker(
    *,
    output_dir: Path,
    label: str,
    days: Sequence[str],
    compact: bool,
    truth_mode: bool,
    compact_oracle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    authority = verify_real_source_estates(verify_payload_bytes=True)
    sources, loaded = load_real_source_bound_inputs(
        days=days, source_authority=authority
    )
    label = _safe_label(label)
    stage_path = output_dir / f"harness_{label}_stage_ledger.jsonl.gz"
    sink_root = output_dir / f"harness_{label}_compact_events" if compact else None
    result_scope = (
        "fourteen_day_source_bound_dst_truth_population"
        if truth_mode
        else "source_bound_engineering_comparator"
    )
    payload = execute_full_flow(
        campaign=_raw_campaign(days, truth_mode=truth_mode),
        config=load_repaired_replay_config(),
        sources=sources,
        result_scope=result_scope,
        truth_mode=truth_mode,
        compact_sink_root=sink_root,
        source_authority={**authority, "loaded_projection": loaded},
        compact_oracle=compact_oracle,
        stage_ledger_path=stage_path,
    )
    initial_paths = write_run_artifacts(
        output_dir,
        label=label,
        payload=payload,
        source_authority=authority,
        loaded_projection=loaded,
    )
    measurement = _resource_measurement(
        result=payload["result"], output_paths=list(initial_paths.values())
    )
    _atomic_write_json(initial_paths["resource"], measurement)
    from src.research_infra.wave21_full_flow_verifier import verify as independent_verify

    verification = independent_verify(
        stage_ledger=initial_paths["stage_ledger"],
        fingerprint_path=initial_paths["fingerprint"],
        receipt_path=initial_paths["receipt"],
    )
    verification_path = (
        output_dir / f"harness_{label}_independent_verification.json"
    )
    _atomic_write_json(verification_path, verification)
    initial_paths["independent_verification"] = verification_path
    return {
        "label": label,
        "paths": {key: str(value) for key, value in initial_paths.items()},
        "fingerprint": payload["fingerprint"],
        "receipt": payload["receipt"],
        "resource_measurement": measurement,
        "independent_verification": verification,
    }


def _target_worker_command(
    *,
    target_root: Path,
    harness_path: Path,
    arguments: Sequence[str],
) -> list[str]:
    target_root = target_root.resolve()
    harness_path = harness_path.resolve()
    adapter_specs = _external_target_adapter_specs(
        target_root=target_root, harness_path=harness_path
    )
    bootstrap = "import importlib.util,runpy,sys;"
    bootstrap += f"sys.path.insert(0,{str(target_root)!r});"
    for module_name, adapter_path in adapter_specs:
        bootstrap += (
            f"s=importlib.util.spec_from_file_location({module_name!r},"
            f"{str(adapter_path)!r});"
            "m=importlib.util.module_from_spec(s);"
            f"sys.modules[{module_name!r}]=m;"
            "s.loader.exec_module(m);"
        )
    bootstrap += f"runpy.run_path({str(harness_path)!r},run_name='__main__')"
    return [sys.executable, "-I", "-c", bootstrap, *arguments]


def _external_target_adapter_specs(
    *, target_root: Path, harness_path: Path
) -> list[tuple[str, Path]]:
    """Declare content-hashed non-economic helpers absent from an old tree."""

    helper_names = (
        "wave21_full_flow_truth.py",
        "wave21_full_flow_source_authority.py",
    )
    specs: list[tuple[str, Path]] = []
    for filename in helper_names:
        target_path = target_root / "src" / "research_infra" / filename
        adapter_path = harness_path.parent / filename
        if target_path.is_file():
            continue
        if not adapter_path.is_file():
            if filename == "wave21_full_flow_source_authority.py":
                continue
            raise FullFlowHarnessError(
                f"external_adapter_helper_missing:{adapter_path}"
            )
        specs.append(
            (f"src.research_infra.{Path(filename).stem}", adapter_path.resolve())
        )
    return specs


def _run_isolated_target_worker(
    *,
    target_root: Path,
    output_dir: Path,
    label: str,
    days: Sequence[str],
    compact: bool,
) -> dict[str, Any]:
    harness_path = Path(__file__).resolve()
    args = [
        "source-worker",
        "--output-dir",
        str(output_dir),
        "--label",
        label,
        "--start",
        days[0],
        "--end",
        days[-1],
        "--mode",
        "compact" if compact else "full",
    ]
    for module_name, adapter_path in _external_target_adapter_specs(
        target_root=target_root.resolve(), harness_path=harness_path
    ):
        args.extend(
            ["--external-adapter", f"{module_name}={adapter_path}"]
        )
    completed = subprocess.run(
        _target_worker_command(
            target_root=target_root,
            harness_path=harness_path,
            arguments=args,
        ),
        cwd=target_root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise FullFlowHarnessError(
            f"isolated_target_worker_failed:{label}:{completed.returncode}:"
            f"{completed.stderr[-4000:]}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FullFlowHarnessError(
            f"isolated_target_worker_non_json_output:{label}"
        ) from exc
    return payload


def build_compact_oracle(
    *, output_dir: Path, target_root: Path | None = None
) -> dict[str, Any]:
    target_root = (
        active_target_root()
        if target_root is None
        else target_root.resolve()
    )
    days = ("2025-10-27", "2025-10-28")
    full = _run_isolated_target_worker(
        target_root=target_root,
        output_dir=output_dir,
        label="source_2d_full_native",
        days=days,
        compact=False,
    )
    compact = _run_isolated_target_worker(
        target_root=target_root,
        output_dir=output_dir,
        label="source_2d_compact",
        days=days,
        compact=True,
    )
    full_fp = full["fingerprint"]
    compact_fp = compact["fingerprint"]
    stage_fields = (
        "row_count",
        "comparison_jsonl_stream_sha256",
        "identity_jsonl_stream_sha256",
        "dispositions",
    )
    stage_comparison = {
        stage: {
            field: {
                "full": full_fp["stages"][stage].get(field),
                "compact": compact_fp["stages"][stage].get(field),
                "exact": full_fp["stages"][stage].get(field)
                == compact_fp["stages"][stage].get(field),
            }
            for field in stage_fields
        }
        for stage in sorted(set(full_fp["stages"]) | set(compact_fp["stages"]))
    }
    stage_exact = all(
        field["exact"]
        for stage in stage_comparison.values()
        for field in stage.values()
    )
    economics_exact = stable_sha256(full_fp["economics"]) == stable_sha256(
        compact_fp["economics"]
    )
    conservation_exact = stable_sha256(full_fp["decision_conservation"]) == stable_sha256(
        compact_fp["decision_conservation"]
    )
    stage_dag_exact = stable_sha256(full_fp["occurrence_stage_dag_audit"]) == stable_sha256(
        compact_fp["occurrence_stage_dag_audit"]
    )
    terminal_exact = stable_sha256(
        full["receipt"].get("terminal_execution_truth_reconciliation")
    ) == stable_sha256(
        compact["receipt"].get("terminal_execution_truth_reconciliation")
    )
    exact = all(
        (stage_exact, economics_exact, conservation_exact, stage_dag_exact, terminal_exact)
    )
    truth_semantics_ready = (
        compact_fp["decision_conservation"].get("status") == "PASS"
        and compact_fp["occurrence_stage_dag_audit"].get("status") == "PASS"
        and compact["receipt"].get("truth_mode_hard_failures") in (None, [])
    )
    compact_resource = compact["resource_measurement"]
    retained = int(compact_resource["resident_result_deep_size_bytes"])
    measured_peak = int(compact_resource["process_max_rss_bytes"])
    projected_peak = measured_peak + retained * 6
    projected_disk = int(compact_resource["written_artifact_bytes"]) * 7
    free_disk = int(compact_resource["filesystem_free_bytes"])
    physical_memory = compact_resource.get("host_physical_memory_bytes")
    available_memory = compact_resource.get("host_available_memory_bytes")
    memory_safe = bool(
        isinstance(physical_memory, int)
        and isinstance(available_memory, int)
        and projected_peak < int(physical_memory * 0.85)
        and retained * 6 < available_memory
    )
    disk_safe = projected_disk + 8 * 1024**3 < free_disk
    resource_safe = memory_safe and disk_safe
    body = {
        "schema": f"{SCHEMA}.compact_oracle",
        "status": "PASS" if exact and resource_safe and truth_semantics_ready else "STOP",
        "full_vs_compact_exact": exact,
        "truth_semantics_ready": truth_semantics_ready,
        "truth_semantics_stop_reasons": (
            []
            if truth_semantics_ready
            else [
                "two_day_source_oracle_exposes_stage_dag_or_conservation_stop"
            ]
        ),
        "stage_comparison": stage_comparison,
        "economics_exact": economics_exact,
        "decision_conservation_exact": conservation_exact,
        "occurrence_stage_dag_exact": stage_dag_exact,
        "terminal_reconciliation_exact": terminal_exact,
        "resource_gate": {
            "status": "PASS" if resource_safe else "STOP",
            "measured_two_day_compact_peak_rss_bytes": measured_peak,
            "measured_two_day_retained_result_bytes": retained,
            "fourteen_day_peak_rss_upper_estimate_bytes": projected_peak,
            "estimator": "2d_peak_plus_six_additional_2d_retained_state_increments",
            "measured_two_day_artifact_bytes": compact_resource[
                "written_artifact_bytes"
            ],
            "fourteen_day_artifact_upper_estimate_bytes": projected_disk,
            "filesystem_free_bytes": free_disk,
            "host_physical_memory_bytes": physical_memory,
            "host_available_memory_bytes": available_memory,
            "memory_safe": memory_safe,
            "disk_safe": disk_safe,
            "mandatory_post_run_reserve_bytes": 8 * 1024**3,
        },
        "full_worker": full,
        "compact_worker": compact,
        "target": {
            "root": str(target_root),
            "head": _git_output(target_root, "rev-parse", "HEAD"),
            "tree": _git_output(target_root, "rev-parse", "HEAD^{tree}"),
        },
    }
    oracle = {**body, "oracle_root_sha256": stable_sha256(body)}
    _atomic_write_json(output_dir / "harness_source_2d_compact_oracle.json", oracle)
    return oracle


def _target_revision_manifest(target_root: Path) -> dict[str, Any]:
    target_root = target_root.resolve()
    tracked_status = _git_output(
        target_root, "status", "--porcelain=v1", "--untracked-files=no"
    )
    return {
        "root": str(target_root),
        "head": _git_output(target_root, "rev-parse", "HEAD"),
        "tree": _git_output(target_root, "rev-parse", "HEAD^{tree}"),
        "tracked_status": tracked_status,
        "tracked_tree_clean": not tracked_status,
    }


def build_revision_comparison(
    *,
    output_dir: Path,
    targets: Sequence[tuple[str, Path]],
    compact: bool,
) -> dict[str, Any]:
    """Run one external JSON-only worker per target and bind causal ancestry."""

    if len(targets) < 2:
        raise FullFlowHarnessError("revision_comparison_requires_multiple_targets")
    manifests: dict[str, dict[str, Any]] = {}
    results: dict[str, dict[str, Any]] = {}
    for label, target_root in targets:
        label = _safe_label(label)
        if label in manifests:
            raise FullFlowHarnessError(f"duplicate_target_label:{label}")
        manifest = _target_revision_manifest(target_root)
        if not manifest["tracked_tree_clean"]:
            raise FullFlowHarnessError(f"target_tracked_tree_dirty:{label}")
        manifests[label] = manifest
        results[label] = _run_isolated_target_worker(
            target_root=target_root,
            output_dir=output_dir / label,
            label=f"{label}_source_2d_{'compact' if compact else 'full'}",
            days=("2025-10-27", "2025-10-28"),
            compact=compact,
        )
    causal_edges: list[dict[str, Any]] = []
    labels = list(manifests)
    common_git_dir = _git_output(Path(manifests[labels[0]]["root"]), "rev-parse", "--git-common-dir")
    for left_index, left in enumerate(labels):
        for right in labels[left_index + 1 :]:
            left_head = manifests[left]["head"]
            right_head = manifests[right]["head"]
            root = Path(manifests[left]["root"])
            merge_base = _git_output(root, "merge-base", left_head, right_head)
            left_is_ancestor = subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", left_head, right_head],
                check=False,
            ).returncode == 0
            right_is_ancestor = subprocess.run(
                ["git", "-C", str(root), "merge-base", "--is-ancestor", right_head, left_head],
                check=False,
            ).returncode == 0
            causal_edges.append(
                {
                    "left": left,
                    "right": right,
                    "merge_base": merge_base,
                    "left_is_ancestor_of_right": left_is_ancestor,
                    "right_is_ancestor_of_left": right_is_ancestor,
                    "left_only_commit_count": int(
                        _git_output(root, "rev-list", "--count", f"{right_head}..{left_head}")
                    ),
                    "right_only_commit_count": int(
                        _git_output(root, "rev-list", "--count", f"{left_head}..{right_head}")
                    ),
                }
            )
    fingerprints = {
        label: result["fingerprint"]["fingerprint_root_sha256"]
        for label, result in results.items()
    }
    body = {
        "schema": f"{SCHEMA}.revision_comparison",
        "status": "EXECUTED",
        "worker_transport": "isolated_python_target_sys_path_first_json_only",
        "harness_copied_or_cherry_picked_into_targets": False,
        "integration_repository_import_allowed": False,
        "external_adapter": {
            "path": str(Path(__file__).resolve()),
            "file_bytes_sha256": file_sha256(Path(__file__).resolve()),
            "economic_semantics_changed": False,
            "role": "source_and_projection_orchestrator_only",
        },
        "git_common_dir": common_git_dir,
        "targets": manifests,
        "causal_edges": causal_edges,
        "fingerprint_roots": fingerprints,
        "results": results,
    }
    comparison = {**body, "comparison_root_sha256": stable_sha256(body)}
    _atomic_write_json(
        output_dir / "harness_revision_comparison_manifest.json", comparison
    )
    return comparison


def main(argv: Sequence[str] | None = None) -> int:
    global _EXTERNAL_ADAPTER_AUTHORITY

    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    common_default = Path(
        "docs/audits/fable5-vision-audit-20260725/phase21/full_flow_truth"
    )
    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--output-dir", type=Path, default=common_default)
    preflight = subparsers.add_parser("source-preflight")
    preflight.add_argument("--output-dir", type=Path, default=common_default)
    preflight.add_argument("--skip-payload-byte-hashes", action="store_true")
    worker = subparsers.add_parser("source-worker")
    worker.add_argument("--output-dir", type=Path, required=True)
    worker.add_argument("--label", required=True)
    worker.add_argument("--start", required=True)
    worker.add_argument("--end", required=True)
    worker.add_argument("--mode", choices=("full", "compact"), required=True)
    worker.add_argument("--external-adapter", action="append", default=[])
    oracle_parser = subparsers.add_parser("compact-oracle")
    oracle_parser.add_argument("--output-dir", type=Path, default=common_default)
    truth = subparsers.add_parser("truth-run")
    truth.add_argument("--output-dir", type=Path, default=common_default)
    truth.add_argument(
        "--oracle",
        type=Path,
        default=common_default / "harness_source_2d_compact_oracle.json",
    )
    comparison_parser = subparsers.add_parser("compare")
    comparison_parser.add_argument("--output-dir", type=Path, default=common_default)
    comparison_parser.add_argument(
        "--target",
        action="append",
        required=True,
        help="label=/absolute/target/worktree (repeat for each revision)",
    )
    comparison_parser.add_argument(
        "--mode", choices=("full", "compact"), default="compact"
    )
    args = parser.parse_args(argv)
    command = args.command or "smoke"
    if command == "smoke":
        output_dir = getattr(args, "output_dir", common_default)
        payload = run_deterministic_smoke()
        write_smoke_artifacts(output_dir, payload)
        output = verify_written_artifacts(output_dir)
        _atomic_write_json(
            output_dir / "harness_smoke_verification.json", output
        )
    elif command == "source-preflight":
        output = verify_real_source_estates(
            verify_payload_bytes=not args.skip_payload_byte_hashes
        )
        _atomic_write_json(
            args.output_dir / "harness_source_authority_preflight.json", output
        )
    elif command == "source-worker":
        adapters: list[dict[str, Any]] = []
        for raw_adapter in args.external_adapter:
            module_name, separator, raw_path = str(raw_adapter).partition("=")
            path = Path(raw_path)
            if (
                not separator
                or not module_name.startswith("src.research_infra.wave21_full_flow_")
                or not path.is_absolute()
                or not path.is_file()
            ):
                raise FullFlowHarnessError(
                    f"external_adapter_argument_invalid:{raw_adapter}"
                )
            adapters.append(
                {
                    "module": module_name,
                    "path": str(path.resolve()),
                    "file_bytes_sha256": file_sha256(path),
                    "transport": "preloaded_external_json_safe_helper",
                    "economic_semantics_changed": False,
                }
            )
        _EXTERNAL_ADAPTER_AUTHORITY = adapters
        with redirect_stdout(sys.stderr):
            output = run_source_bound_worker(
                output_dir=args.output_dir,
                label=args.label,
                days=_inclusive_days(args.start, args.end),
                compact=args.mode == "compact",
                truth_mode=False,
            )
    elif command == "compact-oracle":
        output = build_compact_oracle(output_dir=args.output_dir)
    elif command == "truth-run":
        oracle = json.loads(args.oracle.read_text(encoding="utf-8"))
        output = run_source_bound_worker(
            output_dir=args.output_dir,
            label="source_14d_dst_truth",
            days=RAW_COMPARATOR_DAYS,
            compact=True,
            truth_mode=True,
            compact_oracle=oracle,
        )
    elif command == "compare":
        parsed_targets: list[tuple[str, Path]] = []
        for raw in args.target:
            label, separator, raw_path = str(raw).partition("=")
            if not separator or not Path(raw_path).is_absolute():
                raise FullFlowHarnessError(f"target_argument_invalid:{raw}")
            parsed_targets.append((_safe_label(label), Path(raw_path)))
        output = build_revision_comparison(
            output_dir=args.output_dir,
            targets=parsed_targets,
            compact=args.mode == "compact",
        )
    else:
        raise FullFlowHarnessError(f"unknown_command:{command}")
    print(
        json.dumps(
            strict_json_primitive(output),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
