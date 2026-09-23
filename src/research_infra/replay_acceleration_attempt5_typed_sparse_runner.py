#!/usr/bin/env python3
"""Execute the sealed attempt-5 typed/sparse S0R0 parity route.

This is the real simulated-live execution entrypoint. It requires immutable
typed source authority, a fresh output namespace, and the Jan 1-7 independent
parity interlock. Broker mutation and successor-arm authority remain closed.
"""

from __future__ import annotations

import argparse
from bisect import bisect_right
import copy
import csv
import ctypes
import errno
import gc
import gzip
import hashlib
import inspect
import json
import math
import os
import random
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Iterable as IterableABC
from collections import Counter, OrderedDict, defaultdict, deque
from concurrent.futures import ProcessPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[2]
CODE_ROUTE = ROOT / (
    "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20"
)
ROUTE = CODE_ROUTE
ATTEMPT5_TICK_SPARSE_CACHE_ROOT = ROOT / (
    "research/operations/replay_acceleration_real_s0r0_2026_07_19/"
    "attempt_5_tick_sparse_cache"
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROUTE) not in sys.path:
    sys.path.insert(0, str(ROUTE))

from src.components.workspace_paths import resolve_gtos_integration_repo  # noqa: E402

MAIN_REPO_ROOT = resolve_gtos_integration_repo(ROOT)

import run_selected_package_replay_bridge as selected_package_bridge  # noqa: E402
from run_selected_package_replay_bridge import (  # noqa: E402
    ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES,
    ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID,
    apply_ultimate_replay_loss_bucket_policy,
    reconstructed_proxy_package_selection_source_contract,
)
from src.research_infra import (  # noqa: E402
    v4_timewarp_simulated_live_research_loop as timewarp_loop,
)
from src.research_infra.replay_acceleration_integrated_source import (  # noqa: E402
    AcceptedPhysicalSourceReference,
    RealReplaySourceAccelerator,
    accepted_source_implementation_root,
)
from src.research_infra.replay_acceleration_immutable_evidence import (  # noqa: E402
    ImmutableEvidenceError,
    lexical_path,
    read_regular_nofollow,
)
from src.research_infra.replay_acceleration_real_gate import (  # noqa: E402
    FIXED_VERIFIER_MODULE,
    GateRejected,
    atomic_write_json as atomic_write_gate_json,
    build_gate_request,
    no_replay_contract_preflight,
    validate_prospective_golden_authority,
    wait_for_parity_receipt,
)
from src.research_infra.replay_acceleration_contract_split import (  # noqa: E402
    split_shared_execution_contract,
)
from src.research_infra.replay_acceleration_fixed_verifier_authority import (  # noqa: E402
    build_fixed_verifier_code_authority,
)
from src.research_infra.replay_acceleration_streaming_archive import (  # noqa: E402
    StreamingProofArchive,
)
from src.research_infra.replay_compact_event_sink import (  # noqa: E402
    ReplayCompactEventSink,
    ReplayCompactLedger,
)
from src.research_infra.replay_prepared_day_pack import (  # noqa: E402
    PreparedDayPackReader,
    build_campaign_prepared_day_pack,
)
from src.research_infra.replay_semantic_diagnostic import (  # noqa: E402
    write_semantic_source_manifest as seal_semantic_source_manifest,
)
from src.research_infra.v4_timewarp_simulated_live_research_loop import (  # noqa: E402
    CampaignExactCache,
    CampaignConfig,
    GTOS_24_SYMBOL_SURFACE,
    HTF_MIN_TOTAL_ROWS,
    M15_LIVE_LOOKBACK_MIN_TOTAL_ROWS,
    M1_EXPECTED_ROWS_PER_M15_BAR,
    M1_MIN_ROWS_PER_DAY,
    M1_MIN_SESSION_COVERAGE_RATIO,
    NO_BROKER_BOUNDARY,
    OUTCOME_EVIDENCE_CLASS,
    REPAIRED_PENDING_EXPIRY_MINUTES,
    SIM_EVIDENCE_CLASS,
    SOURCE_BOUND_EVIDENCE_CLASS,
    SOURCE_TRUTH_SCOPE,
    SIGNED_SOFT_TRANSFER_DISPLACEMENT_TRACE_KEYS,
    TERMINAL_ORDER_STATUSES,
    ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH,
    DEFAULT_LOOKBACKS,
    LazyTickRowsByDay,
    ResolvedSource,
    SimulatedBroker,
    SourceSpec,
    atomic_write_json,
    atomic_write_jsonl,
    b7_5_selection_sizing_factorial_binding_payload,
    candidate_decision_quality_envelope,
    candidate_poi_state_ledger_fields,
    canonical_replay_candidate_instance_fields,
    clear_replay_source_caches,
    file_sha256,
    file_sha256_cached,
    first_present,
    iso,
    json_safe,
    ledger_namespace_alias_fields,
    load_config,
    load_csv_rows,
    normalize_row,
    normalize_package_new_entry_authority_ledger_row,
    m1_symbol_day_source_authority,
    PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_PROJECTION_FIELDS,
    package_new_entry_authority_immutable_payload_failures,
    parse_row_time,
    parse_utc,
    replay_lifecycle_signed_package_authority_valid,
    replay_source_cache_counts,
    resolve_ftmo_tick_source,
    rows_by_day,
    run_campaign,
    scheduler_replay_truth_projection_fields,
    stable_sha256,
    summarize_campaign,
    utc_now,
)
from src.research.source_required_lifecycle_authority import (  # noqa: E402
    source_required_replay_override_applied,
    source_required_replay_override_reason_allowed_for_row,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (  # noqa: E402
    PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
    PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT,
    PACKAGE_NEW_ENTRY_AUTHORITY_VALID_STATUS,
)

PREFIX = "BROAD_LIVE_AS_IF_REPLAY"
ATTEMPT5_OUTPUT_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_SELECTION_SIZING_"
    "S0R0_SOURCE_REPAIRED_R3_CAP_R2"
)
ATTEMPT5_START_DAY = "2026-01-01"
ATTEMPT5_PARITY_DAY = "2026-01-07"
ATTEMPT5_CONTRACT_END_DAY = "2026-01-31"
# The bounded archive needs transient room for one measured dense-day shard;
# it does not need an unrelated multi-gigabyte reserve.  Keep the checkpoint
# tied to the actual write requirement so adequate disks cannot idle replay.
ATTEMPT5_STREAMING_HARD_FLOOR_BYTES = 0
ATTEMPT5_STREAMING_DAY_TRANSIENT_HEADROOM_BYTES = 768 * 1024**2
ATTEMPT5_STREAMING_BOUNDED_WARNING_FLOOR_BYTES = 0
B7_5_MANDATORY_POST_REPLAY_RESERVE_BYTES = 0
ATTEMPT5_NAMESPACE_ROOT = CODE_ROUTE / "attempt_5_typed_sparse"
ATTEMPT5_RUNTIME_EVIDENCE_ROOT = Path("/Users/borr/GTOSActive/repo").resolve()
ATTEMPT5_TICK_SOURCE_MANIFEST = Path(
    "/Users/borr/Documents/gtos/repo/ai-trading-agent/"
    "data/mt5_research_exports/bridge_ftmo_ticks_micro_2025_2026/manifest.json"
).resolve()
ATTEMPT5_TICK_SOURCE_MANIFEST_SHA256 = (
    "2362858a3b03ed7850352e2ebedf3a6408175b2096fd60f02b86e049f61da0ca"
)


def attempt5_finalizer_conflict_key_order(
    current: Iterable[str] | None = None,
) -> tuple[str, ...]:
    """Bind the accepted capped diagnostic order without changing source-cache code."""

    current_order = tuple(
        str(key)
        for key in (
            current
            if current is not None
            else timewarp_loop.FINALIZER_CANONICAL_AUTHORITY_KEYS
        )
    )
    sleeve_keys = (
        "ultimate_package_matched_sleeve_count",
        "ultimate_package_admission_sleeve_match_count",
    )
    required = (*sleeve_keys, "source_boundary")
    if (
        len(current_order) != len(set(current_order))
        or any(current_order.count(key) != 1 for key in required)
    ):
        raise ValueError("attempt5_finalizer_conflict_key_surface_invalid")
    without_sleeves = tuple(
        key for key in current_order if key not in sleeve_keys
    )
    source_index = without_sleeves.index("source_boundary")
    ordered = (
        *without_sleeves[:source_index],
        *sleeve_keys,
        *without_sleeves[source_index:],
    )
    if set(ordered) != set(current_order) or len(ordered) != len(current_order):
        raise ValueError("attempt5_finalizer_conflict_key_surface_invalid")
    return tuple(ordered)


def bind_attempt5_finalizer_conflict_key_order() -> tuple[str, ...]:
    """Install the golden-bound proof-only order for this opt-in replay route."""

    ordered = attempt5_finalizer_conflict_key_order()
    timewarp_loop.FINALIZER_CANONICAL_AUTHORITY_KEYS = ordered
    return ordered
ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256 = (
    "519d4d4f9054d5c19aae3575fa6018e09760e488d3b9274beeed36f48baf2bb4"
)
ATTEMPT5_PREDECESSOR_SOURCE_BUNDLE_ROOT_SHA256 = (
    "7b1ae5d4b614f64ca8c2632e058d28535793fa847efcdba0331ef3c9c34d3d25"
)
ATTEMPT5_SOURCE_REBIND_AUTHORITY_SHA256 = (
    "ff90833d6f1cf5a99cbc0f3277614e0904add3ce18a4f76df203410ba2286793"
)
ATTEMPT5_SOURCE_REBIND_AUTHORITY_ROOT_SHA256 = (
    "2cdacbe6aa6ba5be58635faf35df9f4c90145d89f3595cf59f0e4b58a260f574"
)
ATTEMPT5_SOURCE_SELECTION_SHA256 = (
    "0eb4828655cf2a1c8693c16b864271bd9c7561fb5ecd39387e386f1f8c36473a"
)
ATTEMPT5_SOURCE_SELECTION_ROOT_SHA256 = (
    "1a3a57413a3b8b42d31542198954e1e72bb9ab28fbb0e8b9cf24773400dea80a"
)
ATTEMPT5_SOURCE_BUNDLE_FILE_SHA256 = (
    "7d3465343311aa5d2783780bc4654e8888cb5c6587523df25d4ac93faa2965fd"
)
ATTEMPT5_SOURCE_IMPLEMENTATION_ROOT_SHA256 = (
    "160cc0e4955f6bc4d038379119787e16cb5c61b0d63926acceb7edcd3ba73b7a"
)
SOURCE_REBIND_AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.source_bundle_consumer_rebind_authority.v1"
)
BOUND_SOURCE_REBIND_AUTHORITY_SCHEMA = (
    "gtos.replay_acceleration.bound_source_bundle_consumer_rebind_authority.v1"
)
ATTEMPT5_TICK_DIAGNOSTIC_MANIFEST_BINDINGS = (
    (
        Path(
            "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/"
            "final_moonshot_v4_timewarp_simulated_live_research_loop_2026_06_07/"
            "ftmo_research_exports/timewarp_ftmo_selected_order_ticks_"
            "BTCUSD_20260607/manifest.json"
        ).resolve(),
        "a5319dd7c1788c978233b83dcfeb516183f16c83e210ea57de103595738681ba",
    ),
    (
        Path(
            "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/"
            "final_moonshot_v4_timewarp_simulated_live_research_loop_2026_06_07/"
            "ftmo_research_exports/timewarp_ftmo_selected_order_ticks_"
            "GBPUSD_20260607/manifest.json"
        ).resolve(),
        "9f3dab84af81ac9f359af1b1c3f0c445588e48f679cf171b7c7b81cd157e110a",
    ),
    (
        Path(
            "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/"
            "final_moonshot_v4_timewarp_simulated_live_research_loop_2026_06_07/"
            "ftmo_research_exports/timewarp_ftmo_selected_order_ticks_"
            "NAS100_20260607/manifest.json"
        ).resolve(),
        "e4984d6f17a02ba334ed6cf00ddcbc0a225815424fb86513897e000db0383882",
    ),
    (
        Path(
            "/Users/borr/Documents/gtos/repo/ai-trading-agent/research/operations/"
            "final_moonshot_v4_timewarp_simulated_live_research_loop_2026_06_07/"
            "ftmo_research_exports/timewarp_ftmo_selected_order_ticks_"
            "US30_cash_20260607/manifest.json"
        ).resolve(),
        "233ac4a7a20197dd3abee1835f8404e7d78656c80e45bf09fe8af7eeb219a47c",
    ),
)
RUNTIME_EVIDENCE_ROUTE = CODE_ROUTE
RUNTIME_EVIDENCE_ROUTE_IDENTITY = CODE_ROUTE.relative_to(ROOT)
BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA = (
    "gtos.final_moonshot.broad_live_as_if_replay_harness.summary.v2"
)
COMPACT_DECISION_PROJECTION_SCHEMA = (
    "gtos.final_moonshot.broad_replay.compact_decision_projection.v1"
)
COMPACT_SCORECARD_PROJECTION_SCHEMA = (
    "gtos.final_moonshot.broad_replay.compact_scorecard_projection.v1"
)
COMPACT_MISSED_OPPORTUNITY_SCHEMA = (
    "compact_broad_replay_missed_opportunity_v1"
)
CANDIDATE_RELATIONAL_MATERIALIZATION_SCHEMA = (
    "gtos.final_moonshot.broad_replay.candidate_relational_materialization.v2"
)
ULTIMATE_PACKAGE_RUNTIME_INPUT_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.broad_replay.ultimate_package_runtime_inputs.v1"
)


def configure_output_namespace(path: Path) -> Path:
    """Bind all replay outputs to one fresh attempt-5 namespace."""

    global ROUTE
    namespace = Path(path).resolve()
    expected_root = ATTEMPT5_NAMESPACE_ROOT.resolve()
    try:
        namespace.relative_to(expected_root)
    except ValueError:
        raise ValueError("attempt5_output_namespace_outside_sealed_root") from None
    if namespace == expected_root:
        raise ValueError("attempt5_output_namespace_identity_missing")
    if namespace.exists() or namespace.is_symlink():
        raise ValueError("attempt5_output_namespace_must_be_new")
    semantic_namespace = semantic_diagnostic_root(namespace)
    if semantic_namespace.exists() or semantic_namespace.is_symlink():
        raise ValueError("attempt5_semantic_namespace_must_be_new")
    namespace.mkdir(parents=True, exist_ok=False)
    ROUTE = namespace
    return namespace


def configure_runtime_evidence_root(root: Path) -> dict[str, Any]:
    """Bind read-only runtime evidence to one explicit repository root."""

    global RUNTIME_EVIDENCE_ROUTE
    global MAIN_REPO_ROOT
    global DATA_ROOTS
    global ULTIMATE_PACKAGE_REGISTRY_PATH
    global ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH

    evidence_root = Path(root).resolve()
    route = evidence_root / CODE_ROUTE.relative_to(ROOT)
    acceptance_route = evidence_root / (
        "research/operations/"
        "final_moonshot_ultimate_system_final_package_acceptance_compression_2026_06_19"
    )
    fillability_route = evidence_root / (
        "research/operations/"
        "final_moonshot_ultimate_system_wave_f_fillability_label_repair_2026_06_19"
    )
    inputs = {
        "member_axis": route / "SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl",
        "sleeve_registry": route
        / "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl",
        "reconstructed_selection": route
        / "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json",
        "source_materializer": route
        / "REPLAY_EXTENSION_OPTIMIZED_SOURCE_MATERIALIZER_LEDGER.jsonl",
        "pending_source_coverage": route
        / "REPLAY_EXTENSION_PENDING_CREATED_SOURCE_COVERAGE_LEDGER.jsonl",
        "accepted_member_ledger": acceptance_route
        / "FINAL_PACKAGE_SLEEVE_MEMBER_LEDGER.jsonl",
        "fillability_labels": fillability_route
        / "WAVE_F_ROW_BOUND_FILLABILITY_LABEL_REPAIR_LEDGER.jsonl",
    }
    required_inputs = frozenset(
        {
            "member_axis",
            "sleeve_registry",
            "reconstructed_selection",
            "accepted_member_ledger",
            "fillability_labels",
        }
    )
    contracts: dict[str, dict[str, Any]] = {}
    for name, path in inputs.items():
        try:
            stat_result = path.stat()
        except OSError:
            if name in required_inputs:
                raise ValueError(f"runtime_evidence_input_missing:{name}") from None
            contracts[name] = {
                "path": str(path),
                "present": False,
                "required_by_actual_replay_path": False,
            }
            continue
        if not path.is_file() or path.is_symlink() or stat_result.st_size <= 0:
            raise ValueError(f"runtime_evidence_input_invalid:{name}")
        contracts[name] = {
            "path": str(path),
            "present": True,
            "required_by_actual_replay_path": name in required_inputs,
            "bytes": int(stat_result.st_size),
            "sha256": file_sha256(path),
        }

    MAIN_REPO_ROOT = evidence_root
    DATA_ROOTS = (
        ROOT / "data/mt5_research_exports",
        evidence_root / "data/mt5_research_exports",
    )
    RUNTIME_EVIDENCE_ROUTE = route
    ULTIMATE_PACKAGE_REGISTRY_PATH = inputs["sleeve_registry"]
    ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH = inputs["member_axis"]
    timewarp_loop.ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH = inputs["member_axis"]
    selected_package_bridge.ULTIMATE_PACKAGE_REGISTRY_PATH = inputs[
        "sleeve_registry"
    ]
    selected_package_bridge.RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY_PATH = inputs[
        "reconstructed_selection"
    ]
    if inputs["source_materializer"].is_file():
        selected_package_bridge.MATERIALIZER_LEDGER = inputs["source_materializer"]
    if inputs["pending_source_coverage"].is_file():
        selected_package_bridge.PENDING_CREATED_SOURCE_COVERAGE_LEDGER = inputs[
            "pending_source_coverage"
        ]
    selected_package_bridge.MEMBER_LEDGER = inputs["accepted_member_ledger"]
    selected_package_bridge.LABEL_LEDGER = inputs["fillability_labels"]
    selected_package_bridge._cached_reconstructed_proxy_package_selection_source_contract.cache_clear()
    contract_core = {
        "schema": "gtos.replay_acceleration.runtime_evidence_root.v1",
        "root": str(evidence_root),
        "integration_repo_root": str(MAIN_REPO_ROOT),
        "data_roots": [str(path) for path in DATA_ROOTS],
        "inputs": contracts,
        "legacy_evidence_mutation_enabled": False,
        "read_only_existing_evidence": True,
    }
    return {
        **contract_core,
        "contract_root_sha256": stable_sha256(contract_core),
    }
CAPACITY_SAFE_CHUNK_EXECUTION_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.broad_replay.capacity_safe_chunk_execution.v2"
)
SOURCE_AUTHORITY_CHUNK_INVARIANCE_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.broad_replay.source_authority_chunk_invariance.v2"
)
BROAD_REPLAY_SHARED_EXECUTION_CONTRACT_SCHEMA = (
    "gtos.final_moonshot.broad_replay.shared_execution_contract.v1"
)
B7_5_SELECTION_SIZING_DECISION_CONTRACT_SCHEMA = (
    "gtos.b7_5.selection_sizing_decision_contract.v2"
)
B7_5_POST_ACCELERATION_DECISION_CONTRACT_SCHEMA = (
    "gtos.b7_5.post_acceleration_decision_contract.v1"
)
B7_5_POST_ACCELERATION_DECISION_CONTRACT_STATUS = (
    "SEALED_POST_ACCELERATION_REPLAY_FREE_DECISION_CONTRACT_VALID"
)
B7_5_POST_ACCELERATION_PREDECESSOR_FILE_SHA256 = (
    "614fe667024a844972cf5df02e9a923da6fe4b8087bf385769de0d69d32b741a"
)
B7_5_POST_ACCELERATION_PREDECESSOR_SELF_HASH_SHA256 = (
    "f15ddbe2c67ee803ca88260887dc694594f793f6cbb85e0fc719f4fe14f74222"
)
B7_5_POST_ACCELERATION_TASK9_ACCEPTANCE_FILE_SHA256 = (
    "afa44b4437e749bc369d5615f9aea8205084e50c3724532cc96b2b7e5df9acd5"
)
B7_5_POST_ACCELERATION_TASK9_ACCEPTANCE_ROOT_SHA256 = (
    "9cfbc5b7bbd2d0fc47e7b7b84437dc3163518087f99a483d16f847376487a5be"
)
B7_5_POST_ACCELERATION_TASK9_REBIND_FILE_SHA256 = (
    "4067480783d7d530b22c98850d97d2b3e8bd683ddb8e7849a47487a39f6565d6"
)
B7_5_POST_ACCELERATION_TASK9_REBIND_ROOT_SHA256 = (
    "a89bf1056df3e2d21850ca991178a824d3b2a937fb0fd77b5fa7e85cdf60adbe"
)
B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX = (
    "b7_5_selection_sizing_factorial_"
)
B7_5_SELECTION_SIZING_FACTORIAL_ARM_FACTORS = {
    "S0R0": ("S0", "R0"),
    "S1R0": ("S1", "R0"),
    "S0R1": ("S0", "R1"),
    "S1R1": ("S1", "R1"),
}
B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS = {
    "denominator": {
        "initial_equity_cash": 100000.0,
        "fixed_account_risk_unit_pct": 0.1,
        "fixed_account_risk_unit_cash": 100.0,
        "fixed_denominator_portfolio_r_cash": 100.0,
    },
    "matched_risk": {
        "same_ex_ante_rules_all_arms": True,
        "daily_accepted_risk_pct_cap": 4.0,
        "peak_open_plus_pending_risk_pct_cap": 4.0,
        "cluster_risk_pct_cap": 1.5,
        "opening_window_risk_pct_cap": 1.0,
        "pending_to_open_transfer_once": True,
        "expiry_or_close_release_once": True,
        "ex_post_rescaling_forbidden": True,
    },
}
BROAD_REPLAY_EFFECTIVE_CONFIG_DIAGNOSTIC_RUNTIME_FIELDS = (
    "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
    "selected_policy_expected_net_source_artifact_sha256",
    # These are storage locations only.  Their content and semantic digests
    # remain bound by the adjacent source authority and runtime-input contract.
    "broad_live_as_if_replay_owner_approved_reconstructed_proxy_"
    "selected_policy_expected_net_source_path",
    "ultimate_candidate_package_registry_path",
)
SOURCE_AUTHORITY_SCOPE_MODE = (
    "full_selected_split_window_independent_of_execution_chunk"
)
STATIC_SOURCE_AUTHORITY_TIMEFRAMES = ("D1", "H4", "H1", "M15")
ULTIMATE_PACKAGE_EXPECTED_REGISTRY_ROWS = 82
ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS = 1101
ULTIMATE_PACKAGE_REGISTRY_SCHEMA = (
    "gtos.final_moonshot.ultimate_candidate_package.sleeve_registry.v1"
)
ULTIMATE_PACKAGE_MEMBER_AXIS_SCHEMA = (
    "gtos.final_moonshot.denominator_to_deployment.sleeve_member_exact_join.v1"
)
CURRENT_SUMMARY_AUTHORITY_LEDGER_KEYS = (
    "candidate",
    "candidate_index",
    "scorecard",
    "order",
    "trade",
    "missed",
)
ULTIMATE_PACKAGE_REGISTRY_PATH = (
    ROOT
    / "research/operations/"
    "final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/"
    "ULTIMATE_CANDIDATE_PACKAGE_SLEEVE_REGISTRY_LEDGER.jsonl"
)


def _ultimate_package_runtime_jsonl_input_contract(
    path: Path,
    *,
    input_name: str,
    identity_field: str,
    expected_schema: str,
    expected_row_count: int,
) -> dict[str, Any]:
    """Inspect one replay-critical package input without accepting an empty surface."""

    target = Path(path)
    result: dict[str, Any] = {
        "input_name": input_name,
        "path": str(target),
        "identity_field": identity_field,
        "expected_schema": expected_schema,
        "expected_row_count": int(expected_row_count),
        "exists": target.is_file(),
        "bytes": 0,
        "sha256": None,
        "row_count": 0,
        "unique_identity_count": 0,
        "missing_identity_rows": 0,
        "duplicate_identity_rows": 0,
        "duplicate_identity_values": 0,
        "schema_mismatch_rows": 0,
        "invalid_json_rows": 0,
        "non_mapping_rows": 0,
        "issue_samples": [],
    }
    issues: list[str] = []
    if not result["exists"]:
        issues.append("file_missing")
    else:
        try:
            result["bytes"] = target.stat().st_size
            result["sha256"] = file_sha256(target)
            identity_counts: Counter[str] = Counter()
            with target.open("r", encoding="utf-8") as handle:
                for row_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    result["row_count"] += 1
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        result["invalid_json_rows"] += 1
                        if len(result["issue_samples"]) < 10:
                            result["issue_samples"].append(
                                f"invalid_json:{row_number}:{exc.msg}"
                            )
                        continue
                    if not isinstance(row, Mapping):
                        result["non_mapping_rows"] += 1
                        if len(result["issue_samples"]) < 10:
                            result["issue_samples"].append(
                                f"non_mapping_row:{row_number}"
                            )
                        continue
                    if row.get("schema") != expected_schema:
                        result["schema_mismatch_rows"] += 1
                        if len(result["issue_samples"]) < 10:
                            result["issue_samples"].append(
                                f"schema_mismatch:{row_number}:{row.get('schema')}"
                            )
                    identity = str(row.get(identity_field) or "").strip()
                    if not identity:
                        result["missing_identity_rows"] += 1
                        if len(result["issue_samples"]) < 10:
                            result["issue_samples"].append(
                                f"identity_missing:{row_number}:{identity_field}"
                            )
                    else:
                        identity_counts[identity] += 1
            duplicate_counts = [
                count for count in identity_counts.values() if count > 1
            ]
            result["unique_identity_count"] = len(identity_counts)
            result["duplicate_identity_values"] = len(duplicate_counts)
            result["duplicate_identity_rows"] = sum(
                count - 1 for count in duplicate_counts
            )
        except OSError as exc:
            issues.append(f"file_read_failed:{type(exc).__name__}")
            if len(result["issue_samples"]) < 10:
                result["issue_samples"].append(str(exc))

    if result["bytes"] <= 0:
        issues.append("file_empty")
    if result["row_count"] != int(expected_row_count):
        issues.append(
            f"row_count_mismatch:{result['row_count']}:{int(expected_row_count)}"
        )
    for field, issue in (
        ("invalid_json_rows", "invalid_json_rows_present"),
        ("non_mapping_rows", "non_mapping_rows_present"),
        ("schema_mismatch_rows", "schema_mismatch_rows_present"),
        ("missing_identity_rows", "missing_identity_rows_present"),
        ("duplicate_identity_rows", "duplicate_identity_rows_present"),
    ):
        if int(result[field] or 0):
            issues.append(issue)
    if not result["sha256"]:
        issues.append("sha256_missing")
    result["issues"] = issues
    result["valid"] = not issues
    result["status"] = (
        "runtime_input_valid" if result["valid"] else "runtime_input_invalid"
    )
    return result


def ultimate_package_runtime_input_contract(
    *,
    registry_path: Path | None = None,
    member_axis_path: Path | None = None,
    expected_registry_rows: int = ULTIMATE_PACKAGE_EXPECTED_REGISTRY_ROWS,
    expected_member_axis_rows: int = ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS,
) -> dict[str, Any]:
    """Bind every executable package replay to its complete runtime authority inputs."""

    registry_path = registry_path or ULTIMATE_PACKAGE_REGISTRY_PATH
    member_axis_path = member_axis_path or ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH

    inputs = {
        "sleeve_registry": _ultimate_package_runtime_jsonl_input_contract(
            registry_path,
            input_name="sleeve_registry",
            identity_field="sleeve_id",
            expected_schema=ULTIMATE_PACKAGE_REGISTRY_SCHEMA,
            expected_row_count=expected_registry_rows,
        ),
        "member_axis": _ultimate_package_runtime_jsonl_input_contract(
            member_axis_path,
            input_name="member_axis",
            identity_field="stable_member_axis_id",
            expected_schema=ULTIMATE_PACKAGE_MEMBER_AXIS_SCHEMA,
            expected_row_count=expected_member_axis_rows,
        ),
    }
    failures = [
        f"{input_name}:{issue}"
        for input_name, input_contract in inputs.items()
        for issue in input_contract["issues"]
    ]
    return {
        "schema": ULTIMATE_PACKAGE_RUNTIME_INPUT_CONTRACT_SCHEMA,
        "status": (
            "complete_runtime_authority_inputs_bound"
            if not failures
            else "runtime_authority_inputs_invalid_fail_closed"
        ),
        "valid": not failures,
        "expected_sleeve_count": int(expected_registry_rows),
        "expected_member_axis_count": int(expected_member_axis_rows),
        "full_82_sleeve_surface_required": True,
        "member_axis_execution_authority_required": True,
        "invalid_input_runtime_effect": "fail_before_run_campaign",
        "failure_reasons": failures,
        "inputs": inputs,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }


def require_ultimate_package_runtime_inputs(
    *,
    contract: Mapping[str, Any] | None = None,
    registry_path: Path | None = None,
    member_axis_path: Path | None = None,
    expected_registry_rows: int = ULTIMATE_PACKAGE_EXPECTED_REGISTRY_ROWS,
    expected_member_axis_rows: int = ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS,
) -> dict[str, Any]:
    registry_path = registry_path or ULTIMATE_PACKAGE_REGISTRY_PATH
    member_axis_path = member_axis_path or ULTIMATE_PACKAGE_MEMBER_AXIS_LEDGER_PATH
    checked = dict(
        contract
        or ultimate_package_runtime_input_contract(
            registry_path=registry_path,
            member_axis_path=member_axis_path,
            expected_registry_rows=expected_registry_rows,
            expected_member_axis_rows=expected_member_axis_rows,
        )
    )
    if checked.get("valid") is not True:
        failures = checked.get("failure_reasons") or ["unknown_runtime_input_failure"]
        raise ValueError(
            "ultimate_package_runtime_input_contract_failed:"
            + "|".join(str(failure) for failure in failures)
        )
    return checked


def _canonical_sha256_text(value: Any) -> str | None:
    text = str(value or "").strip().lower()
    if len(text) != 64 or any(character not in "009abcdef" for character in text):
        return None
    return text


def _selection_sizing_contract_self_hash(payload: Mapping[str, Any]) -> str:
    projection = copy.deepcopy(dict(payload))
    self_hash = projection.get("self_hash")
    if not isinstance(self_hash, dict):
        raise ValueError("selection_sizing_decision_contract_self_hash_missing")
    self_hash.pop("sha256", None)
    return stable_sha256(projection)


def selection_sizing_protocol_economics(
    contract: Mapping[str, Any],
) -> tuple[dict[str, Any], str]:
    """Validate and return the exact sealed denominator/risk economics."""

    denominator = contract.get("denominator")
    denominator = denominator if isinstance(denominator, Mapping) else {}
    matched_risk = contract.get("matched_risk")
    matched_risk = matched_risk if isinstance(matched_risk, Mapping) else {}
    projected = {
        "denominator": {
            field: denominator.get(field)
            for field in B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS["denominator"]
        },
        "matched_risk": {
            field: matched_risk.get(field)
            for field in B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS["matched_risk"]
        },
    }
    for section, expected_fields in B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS.items():
        for field, expected in expected_fields.items():
            actual = projected[section][field]
            if type(actual) is not type(expected) or actual != expected:
                raise ValueError(
                    "selection_sizing_decision_contract_economics_mismatch:"
                    f"{section}.{field}"
                )
    if projected != B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS:
        raise ValueError("selection_sizing_decision_contract_economics_mismatch")
    stored_projection = contract.get("protocol_economics")
    if (
        not isinstance(stored_projection, Mapping)
        or stable_sha256(stored_projection) != stable_sha256(projected)
    ):
        raise ValueError(
            "selection_sizing_decision_contract_economics_projection_mismatch"
        )
    digest = stable_sha256(projected)
    if contract.get("protocol_economics_digest_sha256") != digest:
        raise ValueError(
            "selection_sizing_decision_contract_economics_digest_mismatch"
        )
    return copy.deepcopy(projected), digest


def selection_sizing_core_binding_payload(
    *,
    decision_contract_sha256: Any,
    common_execution_input_digest_sha256: Any,
    arm_id: Any,
    arm_fingerprint_sha256: Any,
    selection_factor: Any,
    sizing_factor: Any,
    selection_mode: Any,
    sizing_mode: Any,
    neutral_selection_seed_sha256: Any,
    protocol_economics: Mapping[str, Any],
    protocol_economics_digest_sha256: Any,
) -> dict[str, Any]:
    """Call the core payload helper across its current/final economics API."""

    denominator = protocol_economics.get("denominator")
    denominator = denominator if isinstance(denominator, Mapping) else {}
    matched_risk = protocol_economics.get("matched_risk")
    matched_risk = matched_risk if isinstance(matched_risk, Mapping) else {}
    candidate_kwargs = {
        "decision_contract_sha256": decision_contract_sha256,
        "common_execution_input_digest_sha256": (
            common_execution_input_digest_sha256
        ),
        "arm_id": arm_id,
        "arm_fingerprint_sha256": arm_fingerprint_sha256,
        "selection_factor": selection_factor,
        "sizing_factor": sizing_factor,
        "selection_mode": selection_mode,
        "sizing_mode": sizing_mode,
        "neutral_selection_seed_sha256": neutral_selection_seed_sha256,
        "protocol_economics": copy.deepcopy(dict(protocol_economics)),
        "protocol_economics_digest_sha256": protocol_economics_digest_sha256,
        "denominator": copy.deepcopy(dict(denominator)),
        "matched_risk": copy.deepcopy(dict(matched_risk)),
        **dict(denominator),
        **dict(matched_risk),
    }
    parameters = inspect.signature(
        b7_5_selection_sizing_factorial_binding_payload
    ).parameters
    accepts_var_kwargs = any(
        parameter.kind is inspect.Parameter.VAR_KEYWORD
        for parameter in parameters.values()
    )
    missing_required = [
        name
        for name, parameter in parameters.items()
        if parameter.kind
        in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
        and parameter.default is inspect.Parameter.empty
        and name not in candidate_kwargs
    ]
    if missing_required:
        raise ValueError(
            "selection_sizing_core_binding_payload_api_unhandled:"
            + "|".join(sorted(missing_required))
        )
    kwargs = (
        candidate_kwargs
        if accepts_var_kwargs
        else {
            name: candidate_kwargs[name]
            for name in parameters
            if name in candidate_kwargs
        }
    )
    payload = b7_5_selection_sizing_factorial_binding_payload(**kwargs)
    if not isinstance(payload, Mapping):
        raise ValueError("selection_sizing_core_binding_payload_not_mapping")
    if payload.get("denominator") != dict(denominator):
        raise ValueError(
            "selection_sizing_core_binding_payload_denominator_mismatch"
        )
    if payload.get("matched_risk") != dict(matched_risk):
        raise ValueError(
            "selection_sizing_core_binding_payload_matched_risk_mismatch"
        )
    return copy.deepcopy(dict(payload))


def selection_sizing_factorial_binding_from_args(
    args: argparse.Namespace,
) -> dict[str, Any] | None:
    """Load and fail-close the sealed arm without accepting free factor flags."""

    raw_contract_path = str(getattr(args, "decision_contract", None) or "").strip()
    raw_arm_id = str(getattr(args, "arm_id", None) or "").strip()
    raw_expected_fingerprint = str(
        getattr(args, "expected_arm_fingerprint_sha256", None) or ""
    ).strip()
    requested = bool(
        raw_contract_path or raw_arm_id or raw_expected_fingerprint
    )
    if not requested:
        return None
    if not (raw_contract_path and raw_arm_id and raw_expected_fingerprint):
        raise ValueError("selection_sizing_factorial_binding_arguments_incomplete")
    arm_id = raw_arm_id.upper()
    expected_fingerprint = _canonical_sha256_text(raw_expected_fingerprint)
    if expected_fingerprint is None:
        raise ValueError("selection_sizing_factorial_expected_fingerprint_invalid")
    if arm_id not in B7_5_SELECTION_SIZING_FACTORIAL_ARM_FACTORS:
        raise ValueError("selection_sizing_factorial_arm_id_invalid")

    contract_path = Path(raw_contract_path).expanduser()
    if not contract_path.is_absolute():
        contract_path = ROOT / contract_path
    contract_path = contract_path.resolve()
    try:
        contract_relative_path = str(contract_path.relative_to(ROOT.resolve()))
    except ValueError as exc:
        raise ValueError("selection_sizing_decision_contract_outside_repo") from exc
    if not contract_path.is_file():
        raise ValueError("selection_sizing_decision_contract_missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if not isinstance(contract, Mapping):
        raise ValueError("selection_sizing_decision_contract_not_mapping")
    contract_schema = contract.get("schema")
    contract_status = contract.get("status")
    accepted_contract_identity = (
        (
            contract_schema == B7_5_SELECTION_SIZING_DECISION_CONTRACT_SCHEMA
            and contract_status == "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID"
        )
        or (
            contract_schema == B7_5_POST_ACCELERATION_DECISION_CONTRACT_SCHEMA
            and contract_status
            == B7_5_POST_ACCELERATION_DECISION_CONTRACT_STATUS
        )
    )
    if not accepted_contract_identity or contract.get("valid") is not True:
        raise ValueError("selection_sizing_decision_contract_invalid")
    if any(
        (
            contract.get("replay_free_builder") is not True,
            int(contract.get("run_campaign_call_count") or 0) != 0,
            int(contract.get("outcome_ledger_read_count") or 0) != 0,
            int(contract.get("outcome_artifact_read_count") or 0) != 0,
            contract.get("march_outcome_read") is not False,
        )
    ):
        raise ValueError("selection_sizing_decision_contract_outcome_boundary_invalid")
    self_hash = contract.get("self_hash")
    self_hash = self_hash if isinstance(self_hash, Mapping) else {}
    contract_sha256 = _canonical_sha256_text(self_hash.get("sha256"))
    if (
        contract_sha256 is None
        or contract_sha256 != _selection_sizing_contract_self_hash(contract)
    ):
        raise ValueError("selection_sizing_decision_contract_self_hash_mismatch")
    if contract_schema == B7_5_POST_ACCELERATION_DECISION_CONTRACT_SCHEMA:
        predecessor = contract.get("predecessor_contract_binding")
        acceleration = contract.get("acceleration_acceptance_binding")
        task9_acceptance = (
            acceleration.get("task9_acceptance")
            if isinstance(acceleration, Mapping)
            else None
        )
        task9_rebind = (
            acceleration.get("task9_review_rebind")
            if isinstance(acceleration, Mapping)
            else None
        )
        source_plan_authority = contract.get("source_plan_authority")
        execution_boundary = contract.get("execution_seal_boundary")
        if (
            not isinstance(predecessor, Mapping)
            or predecessor.get("file_sha256")
            != B7_5_POST_ACCELERATION_PREDECESSOR_FILE_SHA256
            or predecessor.get("self_hash_sha256")
            != B7_5_POST_ACCELERATION_PREDECESSOR_SELF_HASH_SHA256
            or predecessor.get("schema")
            != B7_5_SELECTION_SIZING_DECISION_CONTRACT_SCHEMA
            or predecessor.get("status")
            != "SEALED_REPLAY_FREE_DECISION_CONTRACT_VALID"
            or predecessor.get("preserved_immutable") is not True
            or predecessor.get("regeneration_forbidden") is not True
        ):
            raise ValueError(
                "selection_sizing_post_acceleration_predecessor_binding_invalid"
            )
        if (
            not isinstance(task9_acceptance, Mapping)
            or task9_acceptance.get("file_sha256")
            != B7_5_POST_ACCELERATION_TASK9_ACCEPTANCE_FILE_SHA256
            or task9_acceptance.get("receipt_root_sha256")
            != B7_5_POST_ACCELERATION_TASK9_ACCEPTANCE_ROOT_SHA256
            or task9_acceptance.get("mission_phase_b_complete") is not True
            or task9_acceptance.get("mission_phase_c_authorized") is not True
            or not isinstance(task9_rebind, Mapping)
            or task9_rebind.get("file_sha256")
            != B7_5_POST_ACCELERATION_TASK9_REBIND_FILE_SHA256
            or task9_rebind.get("receipt_root_sha256")
            != B7_5_POST_ACCELERATION_TASK9_REBIND_ROOT_SHA256
            or task9_rebind.get("exact_semantic_parity_all_trials") is not True
            or acceleration.get("performance_target_pass_claimed") is not False
            or acceleration.get("owner_adjusted_correctness_first_continuation")
            is not True
            or acceleration.get("broker_live_authority") is not False
            or acceleration.get("real_order_transmission_possible") is not False
        ):
            raise ValueError(
                "selection_sizing_post_acceleration_acceptance_binding_invalid"
            )
        if (
            not isinstance(source_plan_authority, Mapping)
            or source_plan_authority.get("engineering_june_04")
            != "2a5f9e2444a8aebb039f78a7865e70cbffd9797f6da81c7c3172d24108bea434"
            or source_plan_authority.get("development_january")
            != "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
            or source_plan_authority.get("old_source_cells_may_not_mix") is not True
            or not isinstance(execution_boundary, Mapping)
            or execution_boundary.get(
                "separate_artifact_required_before_policy_execution"
            )
            is not True
            or execution_boundary.get("source_bundle_and_shared_digests_not_freely_declared")
            is not True
        ):
            raise ValueError(
                "selection_sizing_post_acceleration_source_or_execution_boundary_invalid"
            )
    protocol_economics, protocol_economics_digest = (
        selection_sizing_protocol_economics(contract)
    )

    input_bindings = contract.get("input_bindings")
    input_bindings = input_bindings if isinstance(input_bindings, Mapping) else {}
    common_execution_input_digest = _canonical_sha256_text(
        input_bindings.get("common_execution_input_digest_sha256")
    )
    if common_execution_input_digest is None:
        raise ValueError(
            "selection_sizing_decision_contract_common_input_digest_invalid"
        )
    binding_roots = [ROOT.resolve()]
    runtime_evidence_root = getattr(args, "runtime_evidence_root", None)
    if runtime_evidence_root is not None:
        binding_roots.append(Path(runtime_evidence_root).expanduser().resolve())
    binding_roots.append(MAIN_REPO_ROOT.resolve())
    binding_roots = list(dict.fromkeys(binding_roots))

    def resolve_exact_bound_input(
        relative_path: str,
        expected_sha256: str,
    ) -> Path:
        relative = Path(relative_path)
        if relative.is_absolute() or any(
            part in ("", ".", "..") for part in relative.parts
        ):
            raise ValueError("selection_sizing_decision_contract_input_outside_repo")
        for binding_root in binding_roots:
            unresolved = binding_root / relative
            resolved = unresolved.resolve()
            try:
                resolved.relative_to(binding_root)
            except ValueError:
                continue
            if unresolved.is_symlink() or not resolved.is_file():
                continue
            if file_sha256_cached(resolved) == expected_sha256:
                return resolved
        raise ValueError(
            "selection_sizing_decision_contract_input_drift:"
            f"{relative_path}"
        )

    for binding_group in ("common_behavior_inputs", "package_authority_inputs"):
        rows = input_bindings.get(binding_group)
        if not isinstance(rows, list) or not rows:
            raise ValueError(
                f"selection_sizing_decision_contract_input_group_missing:{binding_group}"
            )
        for row in rows:
            if not isinstance(row, Mapping):
                raise ValueError("selection_sizing_decision_contract_input_row_invalid")
            relative_path = str(row.get("path") or "").strip()
            expected_sha256 = _canonical_sha256_text(row.get("sha256"))
            if not relative_path or expected_sha256 is None:
                raise ValueError("selection_sizing_decision_contract_input_binding_invalid")
            resolve_exact_bound_input(relative_path, expected_sha256)

    factorial = contract.get("factorial_contract")
    factorial = factorial if isinstance(factorial, Mapping) else {}
    arms = factorial.get("arms")
    arms = arms if isinstance(arms, list) else []
    arm = next(
        (
            row
            for row in arms
            if isinstance(row, Mapping)
            and str(row.get("arm_id") or "").strip().upper() == arm_id
        ),
        None,
    )
    if not isinstance(arm, Mapping):
        raise ValueError("selection_sizing_decision_contract_arm_missing")
    stored_fingerprint = _canonical_sha256_text(arm.get("arm_fingerprint_sha256"))
    fingerprint_projection = arm.get("arm_fingerprint_projection")
    declared_deltas = arm.get("declared_factor_deltas")
    declared_deltas = declared_deltas if isinstance(declared_deltas, Mapping) else {}
    selection_delta = declared_deltas.get("selection")
    selection_delta = selection_delta if isinstance(selection_delta, Mapping) else {}
    sizing_delta = declared_deltas.get("sizing")
    sizing_delta = sizing_delta if isinstance(sizing_delta, Mapping) else {}
    selection_factor = str(selection_delta.get("level") or "").strip().upper()
    sizing_factor = str(sizing_delta.get("level") or "").strip().upper()
    if (selection_factor, sizing_factor) != (
        B7_5_SELECTION_SIZING_FACTORIAL_ARM_FACTORS[arm_id]
    ):
        raise ValueError("selection_sizing_decision_contract_arm_factor_mismatch")
    expected_fingerprint_projection = {
        "common_execution_input_digest_sha256": common_execution_input_digest,
        "declared_factor_deltas": copy.deepcopy(dict(declared_deltas)),
        "protocol_economics": protocol_economics,
    }
    if (
        stored_fingerprint is None
        or not isinstance(fingerprint_projection, Mapping)
        or stable_sha256(fingerprint_projection)
        != stable_sha256(expected_fingerprint_projection)
        or stable_sha256(fingerprint_projection) != stored_fingerprint
        or expected_fingerprint != stored_fingerprint
    ):
        raise ValueError("selection_sizing_decision_contract_arm_fingerprint_mismatch")
    if arm.get("declared_factor_delta_digest_sha256") != stable_sha256(
        declared_deltas
    ):
        raise ValueError(
            "selection_sizing_decision_contract_factor_delta_digest_mismatch"
        )

    denominator = protocol_economics["denominator"]
    matched_risk = protocol_economics["matched_risk"]
    neutral_seed = _canonical_sha256_text(
        factorial.get("neutral_selection_seed_sha256")
    )
    if neutral_seed is None or factorial.get("neutral_selection_key") != (
        "sha256(seed|decision_window_id|candidate_instance_key)"
    ):
        raise ValueError("selection_sizing_decision_contract_neutral_seed_invalid")
    forbidden_inputs = tuple(factorial.get("neutral_selection_forbidden_inputs") or ())
    if forbidden_inputs != (
        "terminal_r",
        "cash_pnl",
        "pnl",
        "close_reason",
        "mfe",
        "mae",
        "future_bar",
        "future_tick",
        "postdecision_path",
    ):
        raise ValueError("selection_sizing_decision_contract_forbidden_inputs_drift")

    selection_mode = (
        "neutral_hash_hard_eligible"
        if selection_factor == "S0"
        else "quality_ranked_current"
    )
    sizing_mode = (
        "fixed_equal_account_risk" if sizing_factor == "R0" else "dynamic_runtime"
    )
    binding_payload = selection_sizing_core_binding_payload(
        decision_contract_sha256=contract_sha256,
        common_execution_input_digest_sha256=common_execution_input_digest,
        arm_id=arm_id,
        arm_fingerprint_sha256=stored_fingerprint,
        selection_factor=selection_factor,
        sizing_factor=sizing_factor,
        selection_mode=selection_mode,
        sizing_mode=sizing_mode,
        neutral_selection_seed_sha256=neutral_seed,
        protocol_economics=protocol_economics,
        protocol_economics_digest_sha256=protocol_economics_digest,
    )
    binding_payload_digest = stable_sha256(binding_payload)

    return {
        "valid": True,
        "status": "sealed_factorial_arm_bound_broker_live_closed",
        "decision_contract_path": contract_relative_path,
        "decision_contract_sha256": contract_sha256,
        "common_execution_input_digest_sha256": common_execution_input_digest,
        "binding_payload": binding_payload,
        "binding_payload_sha256": binding_payload_digest,
        "arm_id": arm_id,
        "arm_fingerprint_sha256": stored_fingerprint,
        "selection_factor": selection_factor,
        "sizing_factor": sizing_factor,
        "selection_mode": selection_mode,
        "sizing_mode": sizing_mode,
        "neutral_selection_seed_sha256": neutral_seed,
        "protocol_economics": protocol_economics,
        "protocol_economics_digest_sha256": protocol_economics_digest,
        "denominator": copy.deepcopy(denominator),
        "fixed_account_risk_unit_pct": denominator[
            "fixed_account_risk_unit_pct"
        ],
        "fixed_account_risk_unit_cash": denominator[
            "fixed_account_risk_unit_cash"
        ],
        "fixed_denominator_portfolio_r_cash": denominator[
            "fixed_denominator_portfolio_r_cash"
        ],
        "initial_equity_cash": denominator["initial_equity_cash"],
        "matched_risk": copy.deepcopy(dict(matched_risk)),
        "uses_outcome_fields": False,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
    }


def broad_replay_execution_options_from_args(
    args: argparse.Namespace,
    *,
    factorial_arm_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return only behavior/proof options that must not drift by window."""

    options = {
        "profiles": list(args.profiles),
        "chunk_size": int(args.chunk_size),
        "max_candidates_per_symbol_window": int(
            args.max_candidates_per_symbol_window
        ),
        "smoke_subset": bool(args.smoke_subset),
        "skip_tick_source": bool(getattr(args, "skip_tick_source", False)),
        "use_native_h1": bool(args.use_native_h1),
        "omit_candidate_ledger": bool(args.omit_candidate_ledger),
        "omit_candidate_index_ledger": bool(
            getattr(args, "omit_candidate_index_ledger", False)
        ),
        "omit_packet_sidecar_ledger": bool(args.omit_packet_sidecar_ledger),
        "compact_missed_ledger": bool(
            getattr(args, "compact_missed_ledger", False)
        ),
        "compact_decision_ledger": bool(
            getattr(args, "compact_decision_ledger", False)
        ),
        "compact_scorecard_ledger": bool(
            getattr(args, "compact_scorecard_ledger", False)
        ),
        "compact_event_sink_enabled": bool(
            getattr(args, "compact_event_sink", False)
        ),
        "compact_event_sink_roles": (
            ["decision", "missed"]
            if getattr(args, "compact_event_sink", False)
            else []
        ),
        "compact_event_sink_max_shard_bytes": int(
            getattr(args, "compact_event_max_shard_bytes", 128 * 1024 * 1024)
        ),
        "prepared_day_pack_enabled": bool(
            getattr(args, "prepared_day_pack_root", None)
            or getattr(args, "build_prepared_day_pack_root", None)
        ),
        "prepared_day_pack_build_enabled": bool(
            getattr(args, "build_prepared_day_pack_root", None)
        ),
        "candidate_ledger_packet_max_bytes": int(
            args.candidate_ledger_packet_max_bytes
        ),
        "scorecard_ledger_packet_max_bytes": int(
            args.scorecard_ledger_packet_max_bytes
        ),
        "compact_scorecard_symbol_risk_config": bool(
            args.compact_scorecard_symbol_risk_config
        ),
        "scorecard_probe_row_limit": int(args.scorecard_probe_row_limit),
        "gc_between_chunks": bool(getattr(args, "gc_between_chunks", True)),
        "parity_gate_after_day": getattr(args, "parity_gate_after_day", None),
        "parity_gate_requires_independent_receipt": bool(
            getattr(args, "parity_gate_after_day", None)
        ),
        "engineering_stop_after_day": getattr(
            args,
            "engineering_stop_after_day",
            None,
        ),
        "tick_sparse_cache_window_end_after_day": getattr(
            args,
            "tick_sparse_cache_window_end_after_day",
            None,
        ),
        "streaming_proof_archive_enabled": bool(
            getattr(args, "streaming_proof_archive_root", None)
        ),
        "streaming_proof_archive_hot_roles": (
            ["decision", "scorecard", "missed"]
            if getattr(args, "streaming_proof_archive_root", None)
            else []
        ),
        "max_streaming_proof_archive_bytes": int(
            getattr(args, "max_streaming_proof_archive_bytes", 1024 * 1024 * 1024)
        ),
    }
    if factorial_arm_binding is not None:
        options["b7_5_selection_sizing_factorial_arm"] = copy.deepcopy(
            dict(factorial_arm_binding)
        )
    source_acceleration_authority = getattr(
        args, "source_acceleration_authority", None
    )
    if isinstance(source_acceleration_authority, Mapping):
        options["source_acceleration"] = {
            key: copy.deepcopy(source_acceleration_authority.get(key))
            for key in (
                "schema",
                "source_bundle_root_sha256",
                "selection_root_sha256",
                "source_plan_digest_sha256",
                "config_projection_root_sha256",
                "normalizer_code_root_sha256",
                "partition_count",
                "symbol_count",
                "policy_execution_entered",
                "candidate_cache_enabled",
                "policy_state_cache_enabled",
                "source_bundle_consumer_rebind_authority",
            )
        }
        options["source_acceleration"]["prewarm_worker_count"] = int(
            getattr(args, "source_prewarm_workers", 1)
        )
    task2_semantic_checkpoint = str(
        getattr(args, "task2_semantic_checkpoint_after_day", None) or ""
    ).strip()
    if task2_semantic_checkpoint:
        options["task2_semantic_checkpoint_after_day"] = (
            task2_semantic_checkpoint
        )
    return options


def bound_source_acceleration_authority(
    args: argparse.Namespace,
    source_accelerator: RealReplaySourceAccelerator,
) -> dict[str, Any]:
    """Attach the verified consumer-successor receipt to source authority."""

    rebind = getattr(
        args,
        "bound_source_bundle_consumer_rebind_authority",
        None,
    )
    if not isinstance(rebind, Mapping):
        raise ValueError("attempt5_source_rebind_authority_not_bound")
    authority = source_accelerator.authority()
    if (
        authority.get("source_bundle_root_sha256")
        != rebind.get("verified_successor_bundle", {}).get(
            "bundle_root_sha256"
        )
        or authority.get("selection_root_sha256")
        != rebind.get("verified_successor_selection", {}).get(
            "selection_root_sha256"
        )
        or authority.get("source_plan_digest_sha256")
        != rebind.get("source_plan_digest_sha256")
    ):
        raise ValueError("attempt5_source_rebind_runtime_authority_mismatch")
    authority["source_bundle_consumer_rebind_authority"] = copy.deepcopy(
        dict(rebind)
    )
    return authority


def broad_replay_execution_semantic_config(
    config: Mapping[str, Any],
) -> dict[str, Any]:
    """Exclude audit-only provenance from the effective replay config identity."""

    projected = copy.deepcopy(json_safe(config))
    runtime = projected.get("gtos_vnext_runtime")
    if isinstance(runtime, dict):
        for field in BROAD_REPLAY_EFFECTIVE_CONFIG_DIAGNOSTIC_RUNTIME_FIELDS:
            runtime.pop(field, None)
    return projected


def broad_replay_shared_execution_contract(
    *,
    profiles: Iterable[str],
    active_symbols: Iterable[str],
    execution_options: Mapping[str, Any],
    runtime_input_contract: Mapping[str, Any] | None = None,
    factorial_arm_binding: Mapping[str, Any] | None = None,
    profile_configs: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Hash code, config, package inputs, and unchanged replay semantics."""

    code_authority_paths = (
        Path(__file__).resolve(),
        ROOT / "src/components/workspace_paths.py",
        ROOT / "src/research_infra/v4_timewarp_simulated_live_research_loop.py",
        CODE_ROUTE / "run_selected_package_replay_bridge.py",
        ROOT / "src/components/selector_v4.py",
        ROOT / "src/research/moonshot_scheduler_v4_best_trade_allocator.py",
        ROOT / "src/components/execution_manager_v4.py",
        ROOT / "src/components/broker_net_cost_engine.py",
        ROOT / "src/components/same_symbol_lifecycle_v4.py",
        ROOT / "src/components/pending_nofill_lifecycle_v4.py",
        ROOT / "src/components/exit_policy_v4.py",
        ROOT / "src/research_infra/replay_acceleration_source_batch.py",
        ROOT / "src/research_infra/replay_acceleration_integrated_source.py",
        ROOT
        / "src/research_infra/replay_acceleration_integrated_source_verifier.py",
        ROOT / "src/research_infra/replay_acceleration_real_gate.py",
        ROOT / "src/research_infra/replay_semantic_diagnostic.py",
        ROOT
        / "src/research_infra/replay_acceleration_real_parity_verifier.py",
        ROOT
        / "src/research_infra/replay_acceleration_streaming_archive.py",
        ROOT
        / "src/research_infra/replay_acceleration_streaming_archive_verifier.py",
        CODE_ROUTE / "build_source_bound_execution_parity.py",
        CODE_ROUTE / "verify_denominator_to_deployment_execution.py",
    )
    code_authority = []
    missing_code_paths = []
    for path in code_authority_paths:
        relative = str(path.relative_to(ROOT))
        if not path.is_file():
            missing_code_paths.append(relative)
            continue
        code_authority.append(
            {
                "path": relative,
                "sha256": file_sha256_cached(path),
            }
        )
    profile_names = tuple(str(profile) for profile in profiles)
    if profile_configs is None:
        effective_profile_configs = {
            profile: build_config(
                profile,
                factorial_arm_binding=factorial_arm_binding,
            )
            for profile in profile_names
        }
    else:
        if set(profile_configs) != set(profile_names):
            raise ValueError("shared_contract_profile_config_inventory_mismatch")
        effective_profile_configs = {
            profile: profile_configs[profile] for profile in profile_names
        }
    effective_config_hashes = {
        profile: stable_sha256(
            broad_replay_execution_semantic_config(
                effective_profile_configs[profile]
            )
        )
        for profile in profile_names
    }
    exact_profile_config_roots = {
        profile: stable_sha256(effective_profile_configs[profile])
        for profile in profile_names
    }
    exact_risk_profile_bindings: dict[str, dict[str, str]] = {}
    for profile in profile_names:
        risk_path, risk_sha256 = timewarp_loop._risk_profile_file_binding(
            effective_profile_configs[profile]
        )
        try:
            relative_risk_path = str(risk_path.relative_to(ROOT))
        except ValueError:
            raise ValueError(
                "shared_contract_risk_profile_outside_repo"
            ) from None
        exact_risk_profile_bindings[profile] = {
            "path": relative_risk_path,
            "sha256": risk_sha256,
        }
    package_inputs = dict(
        runtime_input_contract or ultimate_package_runtime_input_contract()
    )
    semantic_payload = {
        "schema": BROAD_REPLAY_SHARED_EXECUTION_CONTRACT_SCHEMA,
        "code_authority": code_authority,
        "missing_code_paths": missing_code_paths,
        "effective_profile_config_hashes": effective_config_hashes,
        "effective_profile_config_hash_semantics": {
            "projection": "execution_semantic_config_excludes_diagnostic_provenance",
            "excluded_runtime_fields": list(
                BROAD_REPLAY_EFFECTIVE_CONFIG_DIAGNOSTIC_RUNTIME_FIELDS
            ),
            "raw_artifact_sha256_retained_in_runtime_and_ledgers": True,
        },
        "config_file_hashes": {
            "config/agent_config.yaml": file_sha256_cached(
                ROOT / "config/agent_config.yaml"
            ),
            "config/profiles/operator_profile.yaml": (
                file_sha256_cached(
                    ROOT / "config/profiles/operator_profile.yaml"
                )
            ),
        },
        "ultimate_package_runtime_input_contract": package_inputs,
        "active_replay_symbol_universe": sorted(
            set(str(symbol) for symbol in active_symbols)
        ),
        "execution_options": dict(execution_options),
        "window_identity_excluded_from_shared_digest": True,
        "broker_live_final_authority": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
    }
    valid = bool(
        not missing_code_paths
        and package_inputs.get("valid") is True
        and profile_names
        and semantic_payload["active_replay_symbol_universe"]
    )
    return {
        **semantic_payload,
        # Bind the exact objects reused by the campaign cache without making
        # diagnostic-only raw provenance part of the semantic contract digest.
        # Runtime cache boundaries still fail closed on these full roots.
        "exact_profile_config_roots_sha256": exact_profile_config_roots,
        "exact_risk_profile_bindings": exact_risk_profile_bindings,
        "valid": valid,
        "status": (
            "shared_execution_contract_bound"
            if valid
            else "shared_execution_contract_invalid"
        ),
        "shared_execution_contract_digest_sha256": stable_sha256(
            semantic_payload
        ),
    }


def output_paths(prefix: str) -> dict[str, Path]:
    return {
        "source": ROUTE / f"{prefix}_SOURCE_UNIVERSE_LEDGER.jsonl",
        "decision": ROUTE / f"{prefix}_DECISION_LEDGER.jsonl",
        "candidate": ROUTE / f"{prefix}_CANDIDATE_LEDGER.jsonl",
        "candidate_index": ROUTE / f"{prefix}_CANDIDATE_INDEX_LEDGER.jsonl",
        "scorecard": ROUTE / f"{prefix}_SCORECARD_LEDGER.jsonl",
        "order": ROUTE / f"{prefix}_ORDER_LEDGER.jsonl",
        "trade": ROUTE / f"{prefix}_TRADE_LEDGER.jsonl",
        "oracle": ROUTE / f"{prefix}_ORDERED_PATH_ORACLE_LEDGER.jsonl",
        "missed": ROUTE / f"{prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl",
        "bucket": ROUTE / f"{prefix}_BUCKET_LEDGER.jsonl",
        "comparison": ROUTE / f"{prefix}_COMPARISON_LEDGER.jsonl",
        "packet_sidecar": ROUTE / f"{prefix}_PACKET_SIDECAR_LEDGER.jsonl",
        "summary": ROUTE / f"{prefix}_SUMMARY.json",
        "partial_summary": ROUTE / f"{prefix}_PARTIAL_SUMMARY.json",
    }


def semantic_diagnostic_root(route: Path | None = None) -> Path:
    exact_route = Path(route or ROUTE)
    return exact_route.parent / f"{exact_route.name}.semantic-diagnostic"


def semantic_output_paths(prefix: str) -> dict[str, Path]:
    root = semantic_diagnostic_root()
    return {
        "semantic_candidate": root / f"{prefix}_SEMANTIC_CANDIDATE_LEDGER.jsonl",
        "semantic_state_checkpoint": (
            root / f"{prefix}_SEMANTIC_STATE_CHECKPOINT_LEDGER.jsonl"
        ),
        "semantic_order_preimage": (
            root / f"{prefix}_SEMANTIC_ORDER_PREIMAGE_LEDGER.jsonl"
        ),
        "semantic_source_manifest": (
            root / f"{prefix}_SEMANTIC_SOURCE_MANIFEST.json"
        ),
    }


OUTPUTS = output_paths(PREFIX)


def _current_summary_verifier_module() -> Any:
    """Load the route verifier only when certifying completed outputs."""

    import verify_denominator_to_deployment_execution as verifier

    return verifier


def _current_summary_first_present(
    row: Mapping[str, Any],
    fields: Sequence[str],
) -> Any:
    for field in fields:
        value = row.get(field)
        if value not in (None, "", [], {}):
            return value
    return None


def _current_summary_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "allowed",
            "pass",
            "passed",
            "materialized",
        }
    return bool(value)


def _current_summary_positive_number(value: Any) -> bool:
    try:
        return float(value) > 0.0
    except (TypeError, ValueError):
        return False


def _current_summary_signed_authority_context(
    row: Mapping[str, Any],
    verifier: Any,
) -> tuple[bool, str, str, dict[str, Any]]:
    action_intent = verifier.canonical_scheduler_action_intent(
        _current_summary_first_present(
            row,
            (
                "selected_action_class",
                "risk_finalizer_selected_action_class",
                "post_risk_finalizer_selected_action_class",
                "effective_action_intent",
                "selected_scheduler_effective_action_intent",
                "pre_risk_finalizer_effective_action_intent",
                "risk_finalizer_effective_action_intent",
                "package_lifecycle_root_authority_action",
                "same_symbol_lifecycle_action",
                "gtos_vnext_same_symbol_lifecycle_action",
                "lifecycle_action",
                "scheduler_materialization_action_intent",
                "selected_scheduler_action_class",
                "scheduler_action_class",
                "action_intent",
            ),
        )
        or "new_position"
    )
    selector_action = verifier.canonical_selector_action(
        _current_summary_first_present(
            row,
            (
                "scheduler_materialization_selector_action",
                "selected_scheduler_selector_action",
                "pre_risk_finalizer_selector_action",
                "materialized_package_selector_action",
                "materialized_selector_action",
                "effective_selector_action_before_risk_expression",
                "scheduler_materialization_original_selector_action",
                "raw_selector_action",
                "effective_selector_action",
                "selector_action",
                "selector_action_origin",
            ),
        )
        or ""
    )
    signed_row = {
        **row,
        "selector_action": selector_action,
        "scheduler_materialization_action_intent": action_intent,
    }
    required, normalized_action = (
        verifier.signed_package_new_entry_authority_required(signed_row)
    )
    return required, normalized_action, selector_action, signed_row


def _current_summary_authority_claim_bearing(
    row: Mapping[str, Any],
    *,
    ledger_name: str,
    envelope_records: Sequence[Mapping[str, Any]],
) -> bool:
    if any(
        record.get("surface", {}).get("package_new_entry_authority_valid") is True
        for record in envelope_records
        if isinstance(record.get("surface"), Mapping)
    ):
        return True
    if any(
        _current_summary_truthy(row.get(field))
        for field in (
            "ledger_namespace_synthesized_executable_candidate_use_allowed",
            "package_replay_candidate_use_allowed",
            "package_replay_executable_candidate_use_allowed",
            "package_replay_order_executable_candidate_use_allowed",
            "replay_candidate_use_allowed_now",
            "ultimate_package_effective_executable_authority_allowed",
            "executable_finalized",
            "risk_finalizer_executable_finalized",
            "missed_row_executable_finalized",
        )
    ):
        return True
    # Candidate ledgers retain proposed/raw sizing for scoreability even when the
    # scheduler vetoes execution. Only finalized risk on a downstream execution
    # surface is an authority claim by itself.
    finalized_risk_claim = any(
        _current_summary_truthy(row.get(field))
        for field in (
            "executable_finalized",
            "risk_finalizer_executable_finalized",
            "package_replay_order_executable_candidate_use_allowed",
        )
    )
    if finalized_risk_claim and ledger_name in {"scorecard", "order", "trade"} and any(
        _current_summary_positive_number(row.get(field))
        for field in (
            "approved_risk_pct",
            "scheduler_approved_risk_pct",
            "selected_scheduler_approved_risk_pct",
            "risk_decision_approved_risk_pct",
        )
    ):
        return True
    if any(
        row.get(field) not in (None, "")
        for field in ("simulated_order_id", "simulated_trade_id")
    ):
        return True
    if ledger_name == "trade":
        return True
    return ledger_name == "order" and str(row.get("order_status") or "") in {
        "filled",
        "pending_accepted",
        "accepted_not_filled_pending_until_expiry",
    }


def current_summary_v2_contract_for_rows(
    rows: Iterable[tuple[str, Mapping[str, Any]]],
) -> dict[str, Any]:
    """Certify serialized ledger rows before declaring a current/full summary."""

    verifier = _current_summary_verifier_module()
    contract = {
        "schema": BROAD_REPLAY_CURRENT_SUMMARY_SCHEMA,
        "package_new_entry_authority_payload_contract": (
            PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
        ),
        "package_new_entry_authority_payload_required_for_signed_executable_rows": True,
    }
    summary_issues = [
        *verifier.broad_summary_full_verifier_schema_issues(contract),
        *verifier.broad_summary_package_new_entry_authority_payload_contract_issues(
            contract
        ),
    ]
    if summary_issues:
        raise ValueError(
            "current_summary_v2_contract_not_recognized_by_verifier:"
            + "|".join(summary_issues)
        )

    for ledger_name, source_row in rows:
        row = json_safe(dict(source_row))
        provisional_marker_paths = (
            verifier.provisional_package_new_entry_authority_marker_paths(row)
        )
        if provisional_marker_paths:
            candidate_id = (
                row.get("candidate_id")
                or row.get("selected_candidate_id")
                or "unknown_candidate"
            )
            raise ValueError(
                "current_summary_v2_provisional_authority_marker_leak:"
                f"{ledger_name}:{candidate_id}:"
                f"{'|'.join(provisional_marker_paths)}"
            )
        nonrequired_immutable_claim_reasons = (
            verifier.nonrequired_package_new_entry_authority_immutable_claim_reasons(
                row
            )
        )
        if nonrequired_immutable_claim_reasons:
            candidate_id = (
                row.get("candidate_id")
                or row.get("selected_candidate_id")
                or "unknown_candidate"
            )
            raise ValueError(
                "current_summary_v2_nonrequired_authority_payload_claim:"
                f"{ledger_name}:{candidate_id}:"
                f"{'|'.join(nonrequired_immutable_claim_reasons)}"
            )
        terminal_r_final_live_claim_reasons = (
            verifier.terminal_r_final_live_claim_reasons(row)
        )
        if terminal_r_final_live_claim_reasons:
            candidate_id = (
                row.get("candidate_id")
                or row.get("selected_candidate_id")
                or "unknown_candidate"
            )
            raise ValueError(
                "current_summary_v2_terminal_r_final_live_claim:"
                f"{ledger_name}:{candidate_id}:"
                f"{'|'.join(terminal_r_final_live_claim_reasons)}"
            )
        blocked_claim_reasons = verifier.blocked_status_executable_claim_reasons(row)
        if blocked_claim_reasons:
            candidate_id = (
                row.get("candidate_id")
                or row.get("selected_candidate_id")
                or "unknown_candidate"
            )
            raise ValueError(
                "current_summary_v2_blocked_executable_claim:"
                f"{ledger_name}:{candidate_id}:"
                f"{'|'.join(blocked_claim_reasons)}"
            )
        for namespace_record in (
            verifier.package_new_entry_authority_flat_namespace_contract_records(
                row
            )
        ):
            if not (
                namespace_record.get("claim_bearing")
                or namespace_record.get("integrity_bearing")
            ):
                continue
            if namespace_record.get("valid") is True:
                continue
            candidate_id = (
                namespace_record.get("surface", {}).get(
                    "package_new_entry_authority_candidate_id"
                )
                or row.get("candidate_id")
                or row.get("selected_candidate_id")
                or "unknown_candidate"
            )
            reasons = namespace_record.get("reasons") or [
                "flat_namespace_authority_invalid"
            ]
            raise ValueError(
                "current_summary_v2_namespaced_authority_certification_failed:"
                f"{ledger_name}:{candidate_id}:"
                f"{namespace_record.get('source')}:"
                f"{'|'.join(str(reason) for reason in reasons)}"
            )
        required, action_intent, selector_action, signed_row = (
            _current_summary_signed_authority_context(row, verifier)
        )
        envelope = verifier.package_new_entry_authority_envelope_selection(
            signed_row,
            action_intent=action_intent,
        )
        status = str(envelope.get("status") or "authority_envelope_missing")
        records = envelope.get("records") or []
        claim_bearing = _current_summary_authority_claim_bearing(
            signed_row,
            ledger_name=ledger_name.split(":", 1)[0],
            envelope_records=records,
        )
        conflicting = status == "conflicting_current_authority_envelopes"
        authority_claimed_valid = any(
            record.get("surface", {}).get("package_new_entry_authority_valid")
            is True
            for record in records
            if isinstance(record.get("surface"), Mapping)
        )
        must_validate = conflicting or authority_claimed_valid or (
            required and claim_bearing
        )
        if not must_validate:
            continue
        if (
            envelope.get("valid") is True
            and status == "single_current_schema_immutable_envelope"
        ):
            continue
        reasons = list(envelope.get("reasons") or [status])
        candidate_id = (
            row.get("candidate_id")
            or row.get("selected_candidate_id")
            or "unknown_candidate"
        )
        raise ValueError(
            "current_summary_v2_authority_certification_failed:"
            f"{ledger_name}:{candidate_id}:{selector_action}:{action_intent}:"
            f"{status}:{'|'.join(str(reason) for reason in reasons)}"
        )
    return contract


def current_summary_v2_contract_for_outputs(
    outputs: Mapping[str, Path],
) -> dict[str, Any]:
    def serialized_rows() -> Iterable[tuple[str, Mapping[str, Any]]]:
        for ledger_name in CURRENT_SUMMARY_AUTHORITY_LEDGER_KEYS:
            path = outputs.get(ledger_name)
            if path is None or not path.exists() or path.stat().st_size <= 0:
                continue
            with path.open("r", encoding="utf-8") as handle:
                for row_number, line in enumerate(handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError as exc:
                        raise ValueError(
                            "current_summary_v2_output_row_unreadable:"
                            f"{ledger_name}:{row_number}:{exc.msg}"
                        ) from exc
                    if not isinstance(row, Mapping):
                        raise ValueError(
                            "current_summary_v2_output_row_not_mapping:"
                            f"{ledger_name}:{row_number}"
                        )
                    yield f"{ledger_name}:{row_number}", row

    return current_summary_v2_contract_for_rows(serialized_rows())


def current_summary_v2_contract_for_streaming_archive(
    outputs: Mapping[str, Path],
    campaign_manifest_path: Path,
) -> dict[str, Any]:
    """Certify authority rows from exact archived hot bytes plus raw ledgers."""

    from src.research_infra.replay_acceleration_streaming_archive_verifier import (
        iter_campaign_roles_lines,
    )

    def decoded_rows(
        ledger_name: str,
        lines: Iterable[bytes | str],
    ) -> Iterable[tuple[str, Mapping[str, Any]]]:
        try:
            for row_number, line in enumerate(lines, start=1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        "current_summary_v2_output_row_unreadable:"
                        f"{ledger_name}:{row_number}"
                    ) from exc
                if not isinstance(row, Mapping):
                    raise ValueError(
                        "current_summary_v2_output_row_not_mapping:"
                        f"{ledger_name}:{row_number}"
                    )
                yield f"{ledger_name}:{row_number}", row
        finally:
            close = getattr(lines, "close", None)
            if callable(close):
                close()

    def direct_rows(
        ledger_names: Iterable[str],
    ) -> Iterable[tuple[str, Mapping[str, Any]]]:
        for ledger_name in ledger_names:
            path = outputs.get(ledger_name)
            if path is None or not path.exists() or path.stat().st_size <= 0:
                continue
            yield from decoded_rows(
                ledger_name,
                path.open("r", encoding="utf-8"),
            )

    def serialized_rows() -> Iterable[tuple[str, Mapping[str, Any]]]:
        yield from direct_rows(("candidate", "candidate_index"))
        archived = iter_campaign_roles_lines(
            campaign_manifest_path,
            ("scorecard", "missed"),
        )
        deferred_direct_emitted = False
        archived_row_numbers = {"scorecard": 0, "missed": 0}
        try:
            for ledger_name, line in archived:
                if ledger_name == "missed" and not deferred_direct_emitted:
                    yield from direct_rows(("order", "trade"))
                    deferred_direct_emitted = True
                if not line.strip():
                    continue
                archived_row_numbers[ledger_name] += 1
                row_number = archived_row_numbers[ledger_name]
                try:
                    row = json.loads(line)
                except (UnicodeError, json.JSONDecodeError) as exc:
                    raise ValueError(
                        "current_summary_v2_output_row_unreadable:"
                        f"{ledger_name}:{row_number}"
                    ) from exc
                if not isinstance(row, Mapping):
                    raise ValueError(
                        "current_summary_v2_output_row_not_mapping:"
                        f"{ledger_name}:{row_number}"
                    )
                yield f"{ledger_name}:{row_number}", row
        finally:
            archived.close()
        if not deferred_direct_emitted:
            yield from direct_rows(("order", "trade"))

    return current_summary_v2_contract_for_rows(serialized_rows())


def interrupted_summary_from_partial(prefix: str) -> dict[str, Any]:
    """Promote the latest partial checkpoint to an explicit interrupted summary."""
    outputs = output_paths(prefix)
    partial_path = outputs["partial_summary"]
    partial: dict[str, Any] = {}
    if partial_path.exists() and partial_path.read_text(encoding="utf-8").strip():
        with partial_path.open("r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            partial = loaded
    summary: dict[str, Any] = dict(partial)
    summary.update(
        {
            "schema": (
                "gtos.final_moonshot.broad_live_as_if_replay_harness."
                "interrupted_summary.v1"
            ),
            "generated_at_utc": utc_now(),
            "route_id": ROUTE.name,
            "output_prefix": prefix,
            "status": "interrupted_partial_not_final_proof",
            "interrupted_run": True,
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
            "package_new_entry_authority_payload_contract": (
                PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
            ),
            "package_new_entry_authority_payload_required_for_signed_executable_rows": True,
            "partial_summary_path": str(partial_path),
            "interrupted_summary_semantics": (
                "parseable tombstone generated from the last completed chunk; "
                "not a completed broad replay proof"
            ),
            "artifacts": {key: str(path) for key, path in outputs.items()},
            "ledger_file_bytes_at_interrupt": {
                key: (path.stat().st_size if path.exists() else None)
                for key, path in outputs.items()
                if key != "partial_summary"
            },
            "evidence_class": SIM_EVIDENCE_CLASS,
            "source_evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            "outcome_evidence_class": OUTCOME_EVIDENCE_CLASS,
        }
    )
    if "profiles_requested" in summary and "profiles" not in summary:
        summary["profiles"] = list(summary.get("profiles_requested") or [])
    if "comparison_rows" not in summary:
        summary["comparison_rows"] = []
    if "split_profile_stats" not in summary:
        summary["split_profile_stats"] = []
    atomic_write_json(outputs["summary"], json_safe(summary))
    if not partial_path.exists() or not partial_path.read_text(encoding="utf-8").strip():
        atomic_write_json(
            partial_path,
            json_safe(
                {
                    "schema": (
                        "gtos.final_moonshot.broad_live_as_if_replay_harness."
                        "partial_summary.interrupted_before_first_chunk.v1"
                    ),
                    "generated_at_utc": summary["generated_at_utc"],
                    "route_id": ROUTE.name,
                    "output_prefix": prefix,
                    "status": "interrupted_before_first_completed_chunk_not_final_proof",
                    "profiles_requested": summary.get("profiles_requested")
                    or summary.get("profiles")
                    or [],
                    "split_profile_stats": [],
                    "comparison_rows": [],
                    "live_broker_authority": False,
                    "broker_mutation_enabled": False,
                    "final_selection_claim": False,
                    "evidence_class": SIM_EVIDENCE_CLASS,
                }
            ),
        )
    return summary


def failed_summary_from_partial(
    prefix: str,
    *,
    failure_stage: str,
    failure: BaseException,
) -> dict[str, Any]:
    """Materialize an explicit non-final tombstone after a failed run."""

    summary = interrupted_summary_from_partial(prefix)
    outputs = output_paths(prefix)
    partial_counts = summary.get("ledger_write_row_counts_so_far")
    if isinstance(partial_counts, Mapping):
        count_projection = {
            "source_universe_rows": "source",
            "scorecard_rows": "scorecard",
            "order_rows": "order",
            "trade_rows": "trade",
            "oracle_rows": "oracle",
            "missed_opportunity_rows": "missed",
            "bucket_rows": "bucket",
            "packet_sidecar_rows": "packet_sidecar",
            "comparison_ledger_rows": "comparison",
        }
        for summary_key, count_key in count_projection.items():
            summary[summary_key] = int(partial_counts.get(count_key) or 0)

        candidate_count_key = (
            "candidate_index"
            if summary.get("candidate_ledger_omitted")
            else "candidate"
        )
        summary["candidate_rows"] = int(
            summary.get("candidate_rows_materialized_so_far")
            or partial_counts.get(candidate_count_key)
            or 0
        )
        summary["candidate_rows_written"] = int(
            partial_counts.get("candidate") or 0
        )
        summary["candidate_index_rows_written"] = int(
            partial_counts.get("candidate_index") or 0
        )

        terminal_execution_materialized = bool(
            int(partial_counts.get("order") or 0)
            or int(partial_counts.get("trade") or 0)
            or int(partial_counts.get("oracle") or 0)
        )
        summary["terminal_execution_materialized"] = (
            terminal_execution_materialized
        )
        summary["terminal_execution_materialization_status"] = (
            "partial_terminal_execution_ledgers_materialized"
            if terminal_execution_materialized
            else "partial_candidate_replay_no_terminal_execution_materialized"
        )
    summary.update(
        {
            "schema": (
                "gtos.final_moonshot.broad_live_as_if_replay_harness."
                "failed_summary.v1"
            ),
            "generated_at_utc": utc_now(),
            "status": "failed_partial_not_final_proof",
            "interrupted_run": False,
            "failed_run": True,
            "failure_stage": str(failure_stage),
            "failure_type": type(failure).__name__,
            "failure_message": str(failure),
            "failed_summary_semantics": (
                "parseable tombstone generated from the last completed chunk; "
                "not a completed replay proof"
            ),
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        }
    )
    atomic_write_json(outputs["summary"], json_safe(summary))
    return summary

M1_MONTH_PREFIX = "bridge_ftmo_m1_"
M1_SUPPLEMENTAL_ROOT_ORDER_BY_MONTH = {
    "202606": ("bridge_ftmo_b7_4_m1_20260601_20260620",),
}
DEFAULT_START = "2024-01-01"
DEFAULT_END = "2026-06-19"
REPAIR_SEED_START = "2026-05-03"
REPAIR_SEED_END = "2026-05-12"
SPLIT_RANGES = (
    ("train", "2024-01-01", "2025-06-30"),
    ("development", "2025-07-01", "2026-05-12"),
    ("holdout", "2026-05-13", DEFAULT_END),
)
PROFILE_RAW = "raw_package_live_as_if"
PROFILE_GUARDED = "guarded_causal_admission_repair_v2"
PROFILE_REPAIRED = "repaired_package_conversion_v3"
PROFILES = (PROFILE_RAW, PROFILE_GUARDED, PROFILE_REPAIRED)
PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS = frozenset(
    {
        "source_required_hold",
        "redesign_repair_hold",
        "avoid_feature_only_veto",
    }
)
PACKAGE_REDUCED_RISK_ROLE_DISPOSITIONS = frozenset(
    {
        "admission_with_avoid_feature_risk_control",
        "admission_with_redesign_context",
    }
)

DATA_ROOTS = (
    ROOT / "data/mt5_research_exports",
    MAIN_REPO_ROOT / "data/mt5_research_exports",
)
D1_ROOT_ORDER = (
    "deep_universe_h4d1_2014_2026",
    "cycle4_universe_d1",
    "bridge_ftmo_deep_d1_2022_2026",
    "bridge_ftmo_htf_20250601_20260610",
    "bridge_ftmo_b7_4_static_20250501_20260620",
)
H4_ROOT_ORDER = (
    "deep_universe_h4d1_2014_2026",
    "bridge_ftmo_deep_h4_backfill_2014_2026",
    "bridge_ftmo_deep_h4_2015_2022",
    "bridge_ftmo_deep_h4_2022_2026",
    "bridge_ftmo_htf_20250601_20260610",
    "bridge_ftmo_b7_4_static_20250501_20260620",
)
H1_ROOT_ORDER = (
    "gold_multitf_d1h1_2015_2026",
    "bridge_ftmo_metals_h1_backfill_2014_2025",
    "bridge_ftmo_energy_h1m15_backfill_2020_2026",
    "bridge_ftmo_crypto_h1m15_backfill_2024_2026",
    "bridge_ftmo_htf_20250601_20260610",
)
M15_ROOT_ORDER = (
    "bridge_ftmo_m15_20250601_20260610",
    "bridge_ftmo_b7_4_static_20250501_20260620",
    "deep_universe_m15_2014_2026",
    "deep_m15_metals_crypto_idx_2014_2026",
    "bridge_ftmo_fx_m15_backfill_2014_2025",
    "bridge_ftmo_idx_m15_backfill_2017_2025",
    "bridge_ftmo_energy_h1m15_backfill_2020_2026",
    "bridge_ftmo_crypto_h1m15_backfill_2024_2026",
    "gold_multitf_m15_2015_2026",
)

SYMBOL_ALIASES = {
    "GER40": ("GER40", "GER40_cash"),
    "JP225": ("JP225", "JP225_cash"),
    "NAS100": ("NAS100", "US100_cash"),
    "SPX500": ("SPX500", "US500_cash"),
    "UK100": ("UK100", "UK100_cash"),
    "US30_cash": ("US30_cash", "US30"),
    "USOIL_cash": ("USOIL_cash", "USOIL"),
    "UKOIL_cash": ("UKOIL_cash", "UKOIL"),
}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def quality_value_missing(value: Any) -> bool:
    return value in (None, "", [], {})


def first_quality_value(
    row: Mapping[str, Any], fields: Iterable[str]
) -> tuple[Any | None, str | None]:
    for field in fields:
        value = row.get(field)
        if not quality_value_missing(value):
            return value, field
    return None, None


PRE_RISK_FINALIZER_CANONICAL_QUALITY_FIELDS = (
    "expected_net_r",
    "probability",
    "source_completeness",
)


def canonical_quality_values_match(values: tuple[Any, ...]) -> bool:
    if any(quality_value_missing(value) for value in values):
        return False
    if any(isinstance(value, bool) for value in values):
        return False
    try:
        numeric_values = tuple(float(value) for value in values)
    except (TypeError, ValueError):
        return False
    return all(math.isfinite(value) for value in numeric_values) and all(
        value == values[0] for value in values[1:]
    )


def backfill_pre_risk_finalizer_quality_sources(row: dict[str, Any]) -> None:
    """Copy canonical zero-trade provenance only across matching quality surfaces."""

    target_field = (
        "pre_risk_finalizer_candidate_decision_quality_field_sources"
    )
    if (
        not quality_value_missing(row.get(target_field))
        or row.get("selected_action_class") != "zero_trade"
    ):
        return

    reported_sources = row.get(
        "scorecard_reported_candidate_decision_quality_field_sources"
    )
    probe_sources = row.get(
        "finalizer_primary_probe_candidate_decision_quality_field_sources"
    )
    if not isinstance(reported_sources, Mapping) or not reported_sources:
        return
    if not isinstance(probe_sources, Mapping) or not probe_sources:
        return
    if dict(reported_sources) != dict(probe_sources):
        return

    canonical_sources: dict[str, str] = {}
    for field in PRE_RISK_FINALIZER_CANONICAL_QUALITY_FIELDS:
        target_value = row.get(f"pre_risk_finalizer_{field}")
        reported_value = row.get(f"scorecard_reported_{field}")
        probe_value = row.get(f"finalizer_primary_probe_{field}")
        if not canonical_quality_values_match(
            (target_value, reported_value, probe_value)
        ):
            return
        if not quality_value_missing(
            row.get(f"finalizer_primary_probe_{field}_quality_fill_source")
        ):
            return

        reported_source = reported_sources.get(field)
        probe_source = probe_sources.get(field)
        if (
            not isinstance(reported_source, str)
            or not reported_source.strip()
            or reported_source != probe_source
        ):
            return
        canonical_sources[field] = reported_source

    row[target_field] = canonical_sources


def normalize_broker_cost_quality_fields(row: dict[str, Any]) -> None:
    """Expose broker-calibrated replay cost as quality data without making it authority."""

    broker_cost_fields = (
        "broker_calibrated_expected_cost_r",
        "broker_pretrade_cost_r",
        "total_execution_cost_r",
        "broker_pretrade_cost_non_executable_diagnostic_expected_cost_r",
    )
    for target in ("expected_cost_r", "cost_r"):
        if not quality_value_missing(row.get(target)):
            continue
        value, source = first_quality_value(row, broker_cost_fields)
        if source is None:
            continue
        row[target] = value
        row[f"{target}_quality_fill_source"] = source
        row["broker_calibrated_cost_quality_field_backfilled"] = True
        if source == "broker_pretrade_cost_non_executable_diagnostic_expected_cost_r":
            row["broker_cost_quality_fill_scope"] = (
                "non_executable_refused_broker_cost_diagnostic"
            )
            row["broker_cost_quality_fill_preserves_executable_false"] = True
        else:
            row.setdefault(
                "broker_cost_quality_fill_scope",
                "broker_calibrated_predecision_replay_cost",
            )


SCHEDULER_DECISION_INPUT_SURFACE_FIELDS = (
    "scheduler_candidate_decision_inputs",
    "selected_scheduler_decision_inputs",
    "pre_risk_finalizer_selected_scheduler_decision_inputs",
    "scheduler_option_candidate_decision_inputs",
    "scheduler_option_decision_inputs",
)

SCHEDULER_TRACE_SURFACE_FIELDS = (
    "selected_scheduler_option_trace",
    "scheduler_option_trace",
    "pre_risk_finalizer_scheduler_option_trace",
    "pre_risk_finalizer_selected_scheduler_option_trace",
    "post_risk_finalizer_scheduler_option_trace",
    "finalizer_primary_probe_scheduler_option_trace",
)


PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS = (
    "package_replay_order_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed_reason",
    "package_replay_order_executable_authority_source",
)


def scheduler_decision_input_surfaces(row: Mapping[str, Any]) -> list[tuple[str, Mapping[str, Any]]]:
    surfaces: list[tuple[str, Mapping[str, Any]]] = []
    for field in SCHEDULER_DECISION_INPUT_SURFACE_FIELDS:
        value = row.get(field)
        if isinstance(value, Mapping) and value:
            surfaces.append((field, value))
    for field in SCHEDULER_TRACE_SURFACE_FIELDS:
        trace = row.get(field)
        if not isinstance(trace, Mapping) or not trace:
            continue
        direct = trace.get("candidate_decision_inputs")
        if isinstance(direct, Mapping) and direct:
            surfaces.append((f"{field}.candidate_decision_inputs", direct))
        score_components = trace.get("score_components")
        if isinstance(score_components, Mapping):
            nested = score_components.get("candidate_decision_inputs")
            if isinstance(nested, Mapping) and nested:
                surfaces.append((f"{field}.score_components.candidate_decision_inputs", nested))
    return surfaces


PACKAGE_NEW_ENTRY_AUTHORITY_CLAIM_FIELDS = (
    "package_new_entry_authority_payload",
    "package_new_entry_authority_hash_sha256",
    "expected_package_new_entry_authority_hash_sha256",
    "package_new_entry_authority_required",
    "package_new_entry_authority_valid",
)
PACKAGE_NEW_ENTRY_AUTHORITY_ATOMIC_FLAT_FIELDS = tuple(
    dict.fromkeys(
        (
            *PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
            *(
                projection_field
                for projection_field, _payload_field in (
                    PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_PROJECTION_FIELDS
                )
            ),
        )
    )
)
PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_FIELDS = (
    "ultimate_candidate_package_open_reduced_risk_authority",
    "ultimate_candidate_package_reduce_risk_authority",
)
PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_METADATA_FIELDS = (
    "allowed",
    "applies",
    "authority_family",
    "authority_source",
    "selector_action",
    "selector_reason",
    "source_boundary",
    "uses_outcome_fields",
)
COMPACT_MISSED_EXECUTABLE_ALIAS_FIELDS = (
    "package_replay_candidate_use_allowed",
    "package_replay_executable_candidate_use_allowed",
    "package_replay_order_executable_candidate_use_allowed",
    "replay_candidate_use_allowed_now",
    "ultimate_package_effective_executable_authority_allowed",
    "missed_package_replay_order_executable_candidate_use_allowed",
    "ledger_namespace_synthesized_executable_candidate_use_allowed",
    "missed_opportunity_headline_execution_bound_eligible",
    "missed_cost_executable_headline_eligible",
)
COMPACT_MISSED_EXECUTABLE_REASON_FIELDS = (
    "package_replay_executable_candidate_use_allowed_reason",
    "package_replay_order_executable_candidate_use_allowed_reason",
    "replay_candidate_use_allowed_now_reason",
    "ultimate_package_effective_executable_authority_reason",
    "missed_package_replay_order_executable_candidate_use_allowed_reason",
)


def package_new_entry_authority_claim_present(surface: Mapping[str, Any]) -> bool:
    return any(
        not quality_value_missing(surface.get(field))
        for field in PACKAGE_NEW_ENTRY_AUTHORITY_CLAIM_FIELDS
    )


def compact_missed_authority_surface_candidates(
    row: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    """Return whole authority surfaces without merging fields between them."""

    candidates: list[tuple[str, Mapping[str, Any]]] = []

    def add_surface(name: str, surface: Any) -> None:
        if not isinstance(surface, Mapping) or not surface:
            return
        if package_new_entry_authority_claim_present(surface):
            candidates.append((name, surface))
        declared_field = str(
            surface.get("package_new_entry_authority_authority_field") or ""
        ).strip()
        nested_fields = list(PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_FIELDS)
        if declared_field and declared_field not in nested_fields:
            nested_fields.append(declared_field)
        for nested_field in nested_fields:
            nested = surface.get(nested_field)
            if (
                isinstance(nested, Mapping)
                and nested
                and package_new_entry_authority_claim_present(nested)
            ):
                candidates.append((f"{name}.{nested_field}", nested))

    add_surface("row", row)
    for source_name, surface in scheduler_decision_input_surfaces(row):
        add_surface(source_name, surface)
    return candidates


def compact_missed_authority_surface_failures(
    surface: Mapping[str, Any],
    *,
    current_identity: Mapping[str, str],
) -> list[str]:
    failures: list[str] = []
    if surface.get("package_new_entry_authority_required") is not True:
        failures.append("authority_not_required_true")
    if surface.get("package_new_entry_authority_valid") is not True:
        failures.append("authority_not_valid_true")
    if (
        str(surface.get("package_new_entry_authority_status") or "").strip()
        != PACKAGE_NEW_ENTRY_AUTHORITY_VALID_STATUS
    ):
        failures.append("authority_status_invalid")
    if surface.get("package_new_entry_authority_failures") not in (
        None,
        "",
        [],
        (),
        {},
    ):
        failures.append("authority_failures_present")
    failures.extend(
        package_new_entry_authority_immutable_payload_failures(
            surface,
            current_identity=current_identity,
        )
    )
    authority_field = str(
        surface.get("package_new_entry_authority_authority_field") or ""
    ).strip()
    if authority_field not in PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_FIELDS:
        failures.append("authority_field_missing_or_unexpected")
    payload = surface.get("package_new_entry_authority_payload")
    if isinstance(payload, Mapping):
        order_allowed = payload.get(
            "package_replay_order_executable_candidate_use_allowed"
        )
        if order_allowed not in (True, False):
            failures.append("authority_payload_order_permission_missing")
        if not str(
            payload.get(
                "package_replay_order_executable_candidate_use_allowed_reason"
            )
            or ""
        ).strip():
            failures.append("authority_payload_order_permission_reason_missing")
        if not str(
            payload.get("package_replay_order_executable_authority_source") or ""
        ).strip():
            failures.append("authority_payload_order_permission_source_missing")
    return list(dict.fromkeys(failures))


def clear_compact_missed_authority_envelope(row: dict[str, Any]) -> None:
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_ATOMIC_FLAT_FIELDS:
        row.pop(field, None)
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_FIELDS:
        row.pop(field, None)


def demote_compact_missed_executable_aliases(
    row: dict[str, Any],
    *,
    reason: str,
) -> None:
    for field in COMPACT_MISSED_EXECUTABLE_ALIAS_FIELDS:
        if field in row or field.startswith("package_replay_"):
            row[field] = False
    for field in COMPACT_MISSED_EXECUTABLE_REASON_FIELDS:
        row[field] = reason
    row["package_replay_order_executable_authority_source"] = (
        "compact_missed_atomic_authority_fail_closed"
    )
    row["ledger_namespace_executable_authority_source"] = (
        "compact_missed_atomic_authority_fail_closed"
    )
    row.pop("package_replay_order_executable_authority_flattened_from", None)


def compact_missed_authority_envelope_digest_material(
    row: Mapping[str, Any],
) -> dict[str, Any] | None:
    authority_field = str(
        row.get("package_new_entry_authority_authority_field") or ""
    ).strip()
    nested = row.get(authority_field) if authority_field else None
    if authority_field not in PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_FIELDS or not isinstance(
        nested,
        Mapping,
    ):
        return None
    flat = {
        field: copy.deepcopy(row.get(field))
        for field in PACKAGE_NEW_ENTRY_AUTHORITY_ATOMIC_FLAT_FIELDS
        if field in row
    }
    executable_aliases = {
        field: copy.deepcopy(row.get(field))
        for field in PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS
        if field in row
    }
    return {
        "authority_field": authority_field,
        "flat": flat,
        "nested": copy.deepcopy(dict(nested)),
        "executable_aliases": executable_aliases,
    }


def compact_missed_authority_envelope_digest_sha256(
    row: Mapping[str, Any],
) -> str | None:
    material = compact_missed_authority_envelope_digest_material(row)
    return stable_sha256(material) if material is not None else None


def materialize_compact_missed_atomic_authority_envelope(
    compact: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    """Preserve one signed envelope or clear every executable alias fail-closed."""

    effective_selector_action = str(
        source.get("effective_selector_action")
        or source.get("scheduler_materialization_selector_action")
        or source.get("selector_action")
        or ""
    ).strip()
    candidates = compact_missed_authority_surface_candidates(source)
    signed_reduced_context = effective_selector_action in {
        "reduce-risk",
        "open-reduced-risk",
    }
    if not candidates and not signed_reduced_context:
        compact["missed_opportunity_authority_envelope_status"] = "not_applicable"
        compact[
            "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
        ] = False
        return

    current_identity = canonical_replay_candidate_instance_fields(
        source,
        decision_time_utc=source.get("decision_time_utc"),
    )
    current_identity = {
        **current_identity,
        "candidate_id": str(source.get("candidate_id") or "").strip(),
        "decision_time_utc": str(source.get("decision_time_utc") or "").strip(),
    }
    valid_by_fingerprint: dict[
        str,
        list[tuple[str, Mapping[str, Any]]],
    ] = defaultdict(list)
    rejected: list[str] = []
    for source_name, surface in candidates:
        failures = compact_missed_authority_surface_failures(
            surface,
            current_identity=current_identity,
        )
        if failures:
            rejected.append(f"{source_name}:{'|'.join(failures)}")
            continue
        authority_field = str(
            surface.get("package_new_entry_authority_authority_field") or ""
        ).strip()
        authority_hash = str(
            surface.get("package_new_entry_authority_hash_sha256") or ""
        ).strip()
        fingerprint = stable_sha256(
            {
                "authority_field": authority_field,
                "authority_hash": authority_hash,
            }
        )
        valid_by_fingerprint[fingerprint].append((source_name, surface))

    if len(valid_by_fingerprint) != 1:
        reason = (
            "compact_missed_conflicting_complete_authority_envelopes"
            if len(valid_by_fingerprint) > 1
            else "compact_missed_complete_immutable_authority_envelope_missing"
        )
        clear_compact_missed_authority_envelope(compact)
        demote_compact_missed_executable_aliases(compact, reason=reason)
        compact["package_new_entry_authority_required"] = bool(
            signed_reduced_context or candidates
        )
        compact["package_new_entry_authority_valid"] = False
        compact["package_new_entry_authority_status"] = (
            "invalid_or_missing_signed_new_entry_authority"
        )
        compact["package_new_entry_authority_failures"] = [reason]
        compact["missed_opportunity_authority_envelope_status"] = "fail_closed"
        compact["missed_opportunity_authority_envelope_failure_reason"] = reason
        compact["missed_opportunity_authority_envelope_rejected_sources"] = rejected
        compact[
            "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
        ] = False
        compact["missed_opportunity_signed_authority_payload_preserved"] = False
        return

    equivalent_sources = next(iter(valid_by_fingerprint.values()))
    selected_source_name, selected_surface = equivalent_sources[0]
    authority_field = str(
        selected_surface.get("package_new_entry_authority_authority_field") or ""
    ).strip()
    payload = selected_surface.get("package_new_entry_authority_payload")
    if not isinstance(payload, Mapping):
        reason = "compact_missed_selected_authority_payload_missing"
        clear_compact_missed_authority_envelope(compact)
        demote_compact_missed_executable_aliases(compact, reason=reason)
        compact["package_new_entry_authority_required"] = True
        compact["package_new_entry_authority_valid"] = False
        compact["package_new_entry_authority_status"] = (
            "invalid_or_missing_signed_new_entry_authority"
        )
        compact["package_new_entry_authority_failures"] = [reason]
        compact["missed_opportunity_authority_envelope_status"] = "fail_closed"
        compact["missed_opportunity_authority_envelope_failure_reason"] = reason
        compact[
            "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
        ] = False
        compact["missed_opportunity_signed_authority_payload_preserved"] = False
        return

    clear_compact_missed_authority_envelope(compact)
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_ATOMIC_FLAT_FIELDS:
        if field in selected_surface:
            compact[field] = copy.deepcopy(selected_surface.get(field))

    nested_authority = {
        field: copy.deepcopy(selected_surface.get(field))
        for field in PACKAGE_NEW_ENTRY_AUTHORITY_ATOMIC_FLAT_FIELDS
        if field in selected_surface
    }
    for field in PACKAGE_NEW_ENTRY_AUTHORITY_NESTED_METADATA_FIELDS:
        if field in selected_surface:
            nested_authority[field] = copy.deepcopy(selected_surface.get(field))
    nested_authority.setdefault("allowed", payload.get("authority_allowed"))
    nested_authority.setdefault("applies", payload.get("authority_applies"))
    nested_authority.setdefault("authority_family", payload.get("authority_family"))
    nested_authority.setdefault("authority_source", payload.get("authority_source"))
    nested_authority.setdefault("selector_action", payload.get("selector_action"))
    nested_authority.setdefault("selector_reason", payload.get("selector_reason"))
    nested_authority.setdefault("source_boundary", payload.get("source_boundary"))
    nested_authority.setdefault("uses_outcome_fields", payload.get("uses_outcome_fields"))

    order_allowed = payload.get(
        "package_replay_order_executable_candidate_use_allowed"
    )
    order_reason = str(
        payload.get("package_replay_order_executable_candidate_use_allowed_reason")
        or ""
    ).strip()
    order_source = str(
        payload.get("package_replay_order_executable_authority_source") or ""
    ).strip()
    compact["package_replay_order_executable_candidate_use_allowed"] = order_allowed
    compact["package_replay_order_executable_candidate_use_allowed_reason"] = (
        order_reason
    )
    compact["package_replay_order_executable_authority_source"] = order_source
    nested_authority["package_replay_order_executable_candidate_use_allowed"] = (
        order_allowed
    )
    nested_authority[
        "package_replay_order_executable_candidate_use_allowed_reason"
    ] = order_reason
    nested_authority["package_replay_order_executable_authority_source"] = order_source
    compact[authority_field] = nested_authority

    outer_aliases = (
        "package_replay_candidate_use_allowed",
        "package_replay_executable_candidate_use_allowed",
        "replay_candidate_use_allowed_now",
        "ultimate_package_effective_executable_authority_allowed",
        "missed_package_replay_order_executable_candidate_use_allowed",
    )
    for field in outer_aliases:
        if field in source or field in compact:
            compact[field] = bool(order_allowed is True and source.get(field) is True)
    if order_allowed is not True:
        demote_compact_missed_executable_aliases(
            compact,
            reason=order_reason or "signed_order_permission_false",
        )

    materialization_failures = package_new_entry_authority_immutable_payload_failures(
        compact,
        current_identity=current_identity,
    )
    nested_failures = package_new_entry_authority_immutable_payload_failures(
        nested_authority,
        current_identity=current_identity,
    )
    if materialization_failures or nested_failures:
        reason = "compact_missed_atomic_authority_materialization_invalid"
        clear_compact_missed_authority_envelope(compact)
        demote_compact_missed_executable_aliases(compact, reason=reason)
        compact["package_new_entry_authority_required"] = True
        compact["package_new_entry_authority_valid"] = False
        compact["package_new_entry_authority_status"] = (
            "invalid_or_missing_signed_new_entry_authority"
        )
        compact["package_new_entry_authority_failures"] = list(
            dict.fromkeys([*materialization_failures, *nested_failures])
        )
        compact["missed_opportunity_authority_envelope_status"] = "fail_closed"
        compact["missed_opportunity_authority_envelope_failure_reason"] = reason
        compact[
            "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
        ] = False
        compact["missed_opportunity_signed_authority_payload_preserved"] = False
        return

    digest = compact_missed_authority_envelope_digest_sha256(compact)
    round_trip_digest = compact_missed_authority_envelope_digest_sha256(
        json_safe(compact)
    )
    if not digest or digest != round_trip_digest:
        reason = "compact_missed_authority_envelope_round_trip_digest_mismatch"
        clear_compact_missed_authority_envelope(compact)
        demote_compact_missed_executable_aliases(compact, reason=reason)
        compact["package_new_entry_authority_required"] = True
        compact["package_new_entry_authority_valid"] = False
        compact["package_new_entry_authority_status"] = (
            "invalid_or_missing_signed_new_entry_authority"
        )
        compact["package_new_entry_authority_failures"] = [reason]
        compact["missed_opportunity_authority_envelope_status"] = "fail_closed"
        compact["missed_opportunity_authority_envelope_failure_reason"] = reason
        compact[
            "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
        ] = False
        compact["missed_opportunity_signed_authority_payload_preserved"] = False
        return

    compact["missed_opportunity_authority_envelope_status"] = "atomic_complete"
    compact["missed_opportunity_authority_envelope_source"] = selected_source_name
    compact["missed_opportunity_authority_envelope_equivalent_source_count"] = len(
        equivalent_sources
    )
    compact["missed_opportunity_authority_envelope_digest_sha256"] = digest
    compact[
        "missed_opportunity_authority_envelope_round_trip_digest_sha256"
    ] = round_trip_digest
    compact["missed_opportunity_authority_envelope_round_trip_verified"] = True
    compact[
        "missed_opportunity_authority_envelope_mixed_reconstruction_allowed"
    ] = False
    compact["missed_opportunity_signed_authority_payload_preserved"] = True
    compact[f"{authority_field}_payload_omitted"] = False


def promote_package_order_executable_authority(row: dict[str, Any]) -> None:
    copied_from: str | None = None
    for source_name, inputs in scheduler_decision_input_surfaces(row):
        if not any(field in inputs for field in PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS):
            continue
        for field in PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS:
            if not quality_value_missing(row.get(field)):
                continue
            value = inputs.get(field)
            if quality_value_missing(value):
                continue
            row[field] = value
            copied_from = copied_from or source_name
        if copied_from:
            break
    if copied_from:
        row["package_replay_order_executable_authority_flattened_from"] = copied_from


def risk_expression_ladder_scalar_surfaces(
    row: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    surfaces: list[tuple[str, Mapping[str, Any]]] = []
    for key in (
        "risk_expression_ladder",
        "scorecard_reported_risk_expression_ladder",
        "finalizer_primary_probe_risk_expression_ladder",
        "risk_finalizer_best_package_probe_risk_expression_ladder",
    ):
        value = row.get(key)
        if isinstance(value, Mapping) and value:
            surfaces.append((key, value))
    for parent_key in (
        "risk_authority",
        "risk_finalizer_risk_authority",
        "risk_finalizer_probe_risk_authority",
        "finalizer_primary_probe",
        "risk_finalizer_best_package_probe",
    ):
        parent = row.get(parent_key)
        if not isinstance(parent, Mapping):
            continue
        value = parent.get("risk_expression_ladder")
        if isinstance(value, Mapping) and value:
            surfaces.append((f"{parent_key}.risk_expression_ladder", value))
    return surfaces


def risk_expression_ladder_scalar(
    row: Mapping[str, Any],
    fields: Iterable[str],
) -> Any:
    for source_name, ladder in risk_expression_ladder_scalar_surfaces(row):
        for field in fields:
            value = ladder.get(field)
            if quality_value_missing(value):
                continue
            return value
    return None


def promote_risk_authority_scalar(row: dict[str, Any]) -> None:
    risk_authority = row.get("risk_authority")
    risk_authority = risk_authority if isinstance(risk_authority, Mapping) else {}
    risk_pre = row.get("risk_authority_pre_scheduler")
    risk_pre = risk_pre if isinstance(risk_pre, Mapping) else {}
    finalizer_risk = row.get("risk_finalizer_risk_authority")
    finalizer_risk = finalizer_risk if isinstance(finalizer_risk, Mapping) else {}
    probe_risk = row.get("risk_finalizer_probe_risk_authority")
    probe_risk = probe_risk if isinstance(probe_risk, Mapping) else {}
    risk_surfaces = (
        ("risk_authority", risk_authority),
        ("risk_authority_pre_scheduler", risk_pre),
        ("risk_finalizer_risk_authority", finalizer_risk),
        ("risk_finalizer_probe_risk_authority", probe_risk),
    )
    for source_name, payload in risk_surfaces:
        if not payload:
            continue
        if quality_value_missing(row.get("risk_authority")):
            row["risk_authority"] = (
                payload.get("schema_version")
                or payload.get("risk_authority")
                or payload.get("authority")
            )
            if not quality_value_missing(row.get("risk_authority")):
                row["risk_authority_flattened_from"] = source_name
        if quality_value_missing(row.get("risk_authority_packet_hash_sha256")):
            row["risk_authority_packet_hash_sha256"] = payload.get("packet_hash_sha256")
        if quality_value_missing(row.get("risk_config_source")):
            row["risk_config_source"] = payload.get("risk_config_source")
        if quality_value_missing(row.get("risk_per_trade_pct")):
            row["risk_per_trade_pct"] = payload.get("risk_per_trade_pct")
        for key in (
            "risk_pct_basis",
            "risk_pct_basis_source",
            "risk_pct_final_source",
            "risk_pct_provenance",
            "risk_reduction_basis_pct",
            "risk_reduction_factor",
            "package_risk_expression_execution_fill_probability_full_risk_floor",
            "package_risk_expression_raw_execution_fillability_below_full_risk_floor",
            "package_risk_expression_fill_floor_route_resolved_for_full_risk",
            "package_risk_expression_route_resolution_full_risk_bypass_allowed",
            "package_risk_expression_fill_floor_resolved",
            "package_risk_expression_fill_floor_authority_allowed",
            "package_risk_expression_fill_floor_unresolved_failures",
        ):
            if quality_value_missing(row.get(key)) and not quality_value_missing(
                payload.get(key)
            ):
                row[key] = payload.get(key)
        if quality_value_missing(row.get("selected_cell_risk_pct")):
            row["selected_cell_risk_pct"] = (
                payload.get("selected_cell_risk_pct")
                if not quality_value_missing(payload.get("selected_cell_risk_pct"))
                else risk_expression_ladder_scalar(
                    row,
                    (
                        "selected_cell_risk_pct",
                        "package_risk_expression_selected_cell_risk_pct_before",
                        "requested_risk_pct",
                    ),
                )
            )
        if quality_value_missing(row.get("scheduler_approved_risk_pct")):
            row["scheduler_approved_risk_pct"] = (
                payload.get("approved_risk_pct")
                if payload.get("approved_risk_pct") is not None
                else payload.get("risk_delta_pct")
                if payload.get("risk_delta_pct") is not None
                else risk_expression_ladder_scalar(
                    row,
                    (
                        "approved_risk_pct",
                        "runtime_final_risk_pct",
                        "package_risk_expression_scheduler_approved_risk_pct_before",
                    ),
                )
            )
        if not quality_value_missing(row.get("risk_authority")):
            break


def promote_risk_class_and_sizing(row: dict[str, Any]) -> None:
    selector_action = str(
        row.get("effective_selector_action") or row.get("selector_action") or ""
    ).strip()
    risk_decision = str(row.get("risk_decision") or "").strip()
    if quality_value_missing(row.get("admission_risk_class")):
        row["admission_risk_class"] = selector_action or risk_decision or None
    selected_pct = safe_float(row.get("selected_cell_risk_pct"), 0.0)
    approved_pct = safe_float(
        row.get("scheduler_approved_risk_pct")
        if row.get("scheduler_approved_risk_pct") is not None
        else row.get("approved_risk_pct"),
        0.0,
    )
    if approved_pct <= 0.0:
        approved_pct = safe_float(row.get("risk_pct"), 0.0)
    if selected_pct > 0.0 and approved_pct > 0.0:
        haircut = approved_pct < selected_pct
        row.setdefault("final_approved_risk_pct", approved_pct)
        row.setdefault("risk_pct_basis", max(selected_pct, approved_pct))
        row.setdefault(
            "risk_pct_basis_source",
            "selected_cell_risk_pct_and_scheduler_approved_risk_pct",
        )
        row.setdefault("risk_pct_final_source", "scheduler_approved_risk_pct")
        row.setdefault(
            "risk_pct_provenance",
            {
                "selected_cell_risk_pct": selected_pct,
                "scheduler_approved_risk_pct": approved_pct,
                "final_approved_risk_pct": approved_pct,
                "source": "promote_risk_class_and_sizing",
            },
        )
        row["sizing_haircut_applied"] = haircut
        row["sizing_haircut_factor"] = round(approved_pct / selected_pct, 12)
        row["sizing_haircut_reason"] = (
            "approved_risk_pct_below_selected_cell_risk_pct"
            if haircut
            else "approved_risk_pct_matches_or_exceeds_selected_cell_risk_pct"
        )
    elif "sizing_haircut_applied" not in row:
        row["sizing_haircut_applied"] = None
        row["sizing_haircut_reason"] = "risk_pct_basis_missing"


def promote_scalar_authority_from_projection(
    compact: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    projection = dict(compact)
    source_risk_authority = source.get("risk_authority")
    if (
        not isinstance(source_risk_authority, Mapping)
        and source_risk_authority not in (None, "", [], {})
    ):
        projection["risk_authority"] = source_risk_authority
        projection.setdefault(
            "risk_authority_flattened_from",
            "risk_authority_scalar",
        )
    for key in (
        "scheduler_candidate_decision_inputs",
        "selected_scheduler_decision_inputs",
        "pre_risk_finalizer_selected_scheduler_decision_inputs",
        "scheduler_option_candidate_decision_inputs",
        "scheduler_option_decision_inputs",
        "selected_scheduler_option_trace",
        "scheduler_option_trace",
        "pre_risk_finalizer_scheduler_option_trace",
        "pre_risk_finalizer_selected_scheduler_option_trace",
        "post_risk_finalizer_scheduler_option_trace",
        "finalizer_primary_probe_scheduler_option_trace",
        "risk_expression_ladder",
        "scorecard_reported_risk_expression_ladder",
        "finalizer_primary_probe_risk_expression_ladder",
        "risk_finalizer_best_package_probe_risk_expression_ladder",
    ):
        value = source.get(key)
        if value not in (None, "", [], {}):
            projection[key] = value
    for source_key, projection_key in (
        ("risk_authority", "risk_authority_pre_scheduler"),
        ("risk_authority_pre_scheduler", "risk_authority_pre_scheduler"),
        ("risk_finalizer_risk_authority", "risk_finalizer_risk_authority"),
        ("risk_finalizer_probe_risk_authority", "risk_finalizer_probe_risk_authority"),
    ):
        value = source.get(source_key)
        if value not in (None, "", [], {}):
            projection[projection_key] = value
    promote_package_order_executable_authority(projection)
    promote_risk_authority_scalar(projection)
    promote_risk_class_and_sizing(projection)
    for key in (
        *PACKAGE_ORDER_EXECUTABLE_AUTHORITY_FIELDS,
        "package_replay_order_executable_authority_flattened_from",
        "risk_authority",
        "risk_authority_flattened_from",
        "risk_authority_packet_hash_sha256",
        "risk_config_source",
        "risk_per_trade_pct",
        "selected_cell_risk_pct",
        "scheduler_approved_risk_pct",
        "risk_pct_basis",
        "risk_pct_basis_source",
        "risk_pct_final_source",
        "risk_pct_provenance",
        "risk_reduction_basis_pct",
        "risk_reduction_factor",
        "admission_risk_class",
        "final_approved_risk_pct",
        "sizing_haircut_applied",
        "sizing_haircut_factor",
        "sizing_haircut_reason",
    ):
        value = projection.get(key)
        if value in (None, "", [], {}):
            continue
        compact[key] = value


def promote_scheduler_authority_and_selector(row: dict[str, Any]) -> None:
    """Flatten effective scheduler authority into compact replay ledgers."""

    promote_package_order_executable_authority(row)
    promote_risk_authority_scalar(row)

    copied_from: str | None = None
    authority_claim_present = any(
        not quality_value_missing(row.get(field))
        for field in (
            "package_new_entry_authority_payload",
            "package_new_entry_authority_hash_sha256",
            "expected_package_new_entry_authority_hash_sha256",
        )
    ) or any(
        row.get(field) is True
        for field in (
            "package_new_entry_authority_required",
            "package_new_entry_authority_valid",
        )
    )
    selected_authority_surface: Mapping[str, Any] | None = None
    if authority_claim_present and not (
        package_new_entry_authority_immutable_payload_failures(row)
    ):
        selected_authority_surface = dict(row)
        copied_from = "existing_row_exact_immutable_authority_envelope"
    else:
        for source_name, inputs in scheduler_decision_input_surfaces(row):
            source_claim_present = any(
                not quality_value_missing(inputs.get(field))
                for field in (
                    "package_new_entry_authority_payload",
                    "package_new_entry_authority_hash_sha256",
                    "expected_package_new_entry_authority_hash_sha256",
                )
            ) or any(
                inputs.get(field) is True
                for field in (
                    "package_new_entry_authority_required",
                    "package_new_entry_authority_valid",
                )
            )
            if not source_claim_present:
                continue
            source_failures = (
                package_new_entry_authority_immutable_payload_failures(inputs)
            )
            if source_failures:
                continue
            selected_authority_surface = inputs
            copied_from = source_name
            break
    if selected_authority_surface is not None:
        for field in PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS:
            row.pop(field, None)
        for field in PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS:
            value = selected_authority_surface.get(field)
            if quality_value_missing(value):
                continue
            row[field] = value
        row["package_new_entry_authority_flattened_from_scheduler_inputs"] = copied_from
    elif authority_claim_present:
        row["package_new_entry_authority_valid"] = False
        row["package_new_entry_authority_status"] = (
            "invalid_or_missing_signed_new_entry_authority"
        )
        row["package_new_entry_authority_projection_failures"] = (
            package_new_entry_authority_immutable_payload_failures(row)
        )

    materialized_selector_action = (
        row.get("scheduler_materialization_selector_action")
        or row.get("package_new_entry_authority_selector_action")
    )
    if not quality_value_missing(materialized_selector_action):
        original_action = row.get("selector_action")
        if not quality_value_missing(original_action) and original_action != materialized_selector_action:
            row.setdefault("selector_action_origin", original_action)
            row["selector_action_materialized_from_scheduler"] = True
        row["effective_selector_action"] = materialized_selector_action
    elif quality_value_missing(row.get("effective_selector_action")) and not quality_value_missing(
        row.get("selector_action")
    ):
        row["effective_selector_action"] = row.get("selector_action")

    materialized_selector_reason = (
        row.get("scheduler_materialization_selector_reason")
        or row.get("package_new_entry_authority_selector_reason")
    )
    if not quality_value_missing(materialized_selector_reason):
        original_reason = row.get("selector_reason")
        if not quality_value_missing(original_reason) and original_reason != materialized_selector_reason:
            row.setdefault("selector_reason_origin", original_reason)
        row["effective_selector_reason"] = materialized_selector_reason
    elif quality_value_missing(row.get("effective_selector_reason")) and not quality_value_missing(
        row.get("selector_reason")
    ):
        row["effective_selector_reason"] = row.get("selector_reason")
    promote_risk_class_and_sizing(row)


def normalize_scheduler_quality_aliases(row: dict[str, Any]) -> None:
    """Canonicalize scheduler quality aliases for replay ledgers."""

    promote_scheduler_authority_and_selector(row)
    scheduler_missing_status = (
        row.get("scheduler_quality_backfill_status")
        == "scheduler_option_missing_for_candidate"
    )
    if scheduler_missing_status:
        for field in ("selected_candidate_id", "selected_candidate_ids"):
            if quality_value_missing(row.get(field)):
                continue
            row[f"window_{field}"] = row.get(field)
            row[f"{field}_row_scope_removed_reason"] = (
                "selected_window_metadata_not_this_candidate_scheduler_option"
            )
            row[field] = None
        row.setdefault(
            "candidate_scheduler_quality_parity_status",
            "not_applicable_scheduler_option_missing",
        )
        row.setdefault("candidate_scheduler_quality_parity_mismatches", [])
        return

    scheduler_inputs = row.get("scheduler_candidate_decision_inputs")
    scheduler_inputs = scheduler_inputs if isinstance(scheduler_inputs, Mapping) else {}
    for field in (
        "selected_scheduler_decision_inputs",
        "pre_risk_finalizer_selected_scheduler_decision_inputs",
        "scheduler_option_candidate_decision_inputs",
        "scheduler_option_decision_inputs",
    ):
        value = row.get(field)
        if isinstance(value, Mapping) and value:
            scheduler_inputs = value
            row["scheduler_candidate_decision_inputs_quality_fill_source"] = field
            break
    if not scheduler_inputs:
        synthetic_inputs = {
            "expected_net_r": first_quality_value(
                row,
                (
                    "scheduler_expected_net_r",
                    "selected_scheduler_expected_net_r",
                    "pre_risk_finalizer_expected_net_r",
                    "finalizer_primary_probe_expected_net_r",
                    "candidate_expected_net_r",
                    "expected_net_r",
                ),
            )[0],
            "probability": first_quality_value(
                row,
                (
                    "scheduler_probability",
                    "selected_scheduler_probability",
                    "pre_risk_finalizer_probability",
                    "finalizer_primary_probe_probability",
                    "candidate_probability",
                    "probability",
                ),
            )[0],
            "fill_probability": first_quality_value(
                row,
                (
                    "scheduler_fill_probability",
                    "selected_scheduler_fill_probability",
                    "pre_risk_finalizer_fill_probability",
                    "finalizer_primary_probe_fill_probability",
                    "candidate_fill_probability",
                    "fill_probability",
                ),
            )[0],
            "source_completeness": first_quality_value(
                row,
                (
                    "scheduler_source_completeness",
                    "selected_scheduler_source_completeness",
                    "pre_risk_finalizer_source_completeness",
                    "finalizer_primary_probe_source_completeness",
                    "source_completeness",
                ),
            )[0],
        }
        synthetic_inputs = {
            key: value
            for key, value in synthetic_inputs.items()
            if not quality_value_missing(value)
        }
        if synthetic_inputs:
            scheduler_inputs = synthetic_inputs
            row["scheduler_candidate_decision_inputs_quality_fill_source"] = (
                "canonical_predecision_quality_fields"
            )
    if scheduler_inputs and quality_value_missing(
        row.get("scheduler_candidate_decision_inputs")
    ):
        row["scheduler_candidate_decision_inputs"] = dict(scheduler_inputs)

    direct_alias_map = {
        "selected_scheduler_score": (
            "scheduler_score",
            "scheduler_option_score",
            "score",
        ),
        "pre_risk_finalizer_expected_net_r": (
            "scheduler_expected_net_r",
            "selected_scheduler_expected_net_r",
            "candidate_expected_net_r",
            "expected_net_r",
        ),
        "pre_risk_finalizer_probability": (
            "scheduler_probability",
            "selected_scheduler_probability",
            "candidate_probability",
            "probability",
        ),
        "pre_risk_finalizer_fill_probability": (
            "scheduler_fill_probability",
            "selected_scheduler_fill_probability",
            "candidate_fill_probability",
            "fill_probability",
        ),
        "pre_risk_finalizer_source_completeness": (
            "scheduler_source_completeness",
            "selected_scheduler_source_completeness",
            "source_completeness",
        ),
        "finalizer_primary_probe_expected_net_r": (
            "pre_risk_finalizer_expected_net_r",
            "scheduler_expected_net_r",
            "selected_scheduler_expected_net_r",
            "candidate_expected_net_r",
            "expected_net_r",
        ),
        "finalizer_primary_probe_probability": (
            "pre_risk_finalizer_probability",
            "scheduler_probability",
            "selected_scheduler_probability",
            "candidate_probability",
            "probability",
        ),
        "finalizer_primary_probe_fill_probability": (
            "pre_risk_finalizer_fill_probability",
            "scheduler_fill_probability",
            "selected_scheduler_fill_probability",
            "candidate_fill_probability",
            "fill_probability",
        ),
        "finalizer_primary_probe_source_completeness": (
            "pre_risk_finalizer_source_completeness",
            "scheduler_source_completeness",
            "selected_scheduler_source_completeness",
            "source_completeness",
        ),
    }
    for target, aliases in direct_alias_map.items():
        if not quality_value_missing(row.get(target)):
            continue
        value, source = first_quality_value(row, aliases)
        if source is None:
            continue
        row[target] = value
        row[f"{target}_quality_fill_source"] = source

    alias_map = {
        "scheduler_expected_net_r": (
            "selected_scheduler_expected_net_r",
            "pre_risk_finalizer_expected_net_r",
            "finalizer_primary_probe_expected_net_r",
            "candidate_expected_net_r",
            "expected_net_r",
        ),
        "scheduler_probability": (
            "selected_scheduler_probability",
            "pre_risk_finalizer_probability",
            "finalizer_primary_probe_probability",
            "candidate_probability",
            "probability",
        ),
        "scheduler_confidence": (
            "selected_scheduler_confidence",
            "pre_risk_finalizer_confidence",
            "finalizer_primary_probe_scheduler_confidence",
            "finalizer_primary_probe_confidence",
            "candidate_confidence",
            "confidence",
        ),
        "scheduler_fill_probability": (
            "selected_scheduler_fill_probability",
            "pre_risk_finalizer_fill_probability",
            "finalizer_primary_probe_fill_probability",
            "candidate_fill_probability",
            "fill_probability",
        ),
        "scheduler_source_completeness": (
            "selected_scheduler_source_completeness",
            "pre_risk_finalizer_source_completeness",
            "finalizer_primary_probe_source_completeness",
            "source_completeness",
        ),
        "scheduler_source_completeness_status": (
            "selected_scheduler_source_completeness_status",
            "pre_risk_finalizer_source_completeness_status",
            "finalizer_primary_probe_source_completeness_status",
            "source_completeness_status",
        ),
    }
    for target, aliases in alias_map.items():
        if not quality_value_missing(row.get(target)):
            continue
        value, source = first_quality_value(row, aliases)
        if source is None:
            continue
        row[target] = value
        row[f"{target}_quality_fill_source"] = source

    scheduler_required = (
        "scheduler_candidate_decision_inputs",
        "scheduler_expected_net_r",
        "scheduler_probability",
        "scheduler_fill_probability",
        "scheduler_source_completeness",
    )
    if all(not quality_value_missing(row.get(field)) for field in scheduler_required):
        row["scheduler_quality_backfill_status"] = "materialized"
        row["candidate_scheduler_quality_parity_status"] = "pass"
        row["candidate_scheduler_quality_parity_mismatches"] = []


def normalize_replay_quality_fields(row: dict[str, Any], *, row_type: str) -> None:
    if row_type in {"candidate", "candidate_index", "scheduler_scorecard"}:
        normalize_broker_cost_quality_fields(row)
    if row_type in {
        "candidate",
        "candidate_index",
        "scheduler_scorecard",
        "simulated_order",
        "simulated_trade",
        "missed_opportunity",
        "ordered_path_oracle",
    }:
        if row_type == "scheduler_scorecard":
            backfill_pre_risk_finalizer_quality_sources(row)
        normalize_scheduler_quality_aliases(row)
        preserve_candidate_decision_quality_default_provenance(row)
        normalize_stop_hazard_guard_cap_truth(row)


RESULT_LEDGER_NORMALIZATION_ROW_TYPES: dict[str, str] = {
    "candidate": "candidate",
    "scorecard": "scheduler_scorecard",
    "order": "simulated_order",
    "trade": "simulated_trade",
    "missed": "missed_opportunity",
    "oracle": "ordered_path_oracle",
}


def normalize_replay_result_ledgers(result: Mapping[str, Any]) -> None:
    """Canonicalize chunk rows before summary, proof, and JSONL consumers split."""

    ledgers = result.get("ledgers")
    if not isinstance(ledgers, Mapping):
        return
    for ledger_name, row_type in RESULT_LEDGER_NORMALIZATION_ROW_TYPES.items():
        rows = ledgers.get(ledger_name, ()) or ()
        if isinstance(rows, ReplayCompactLedger):
            def normalize_materialized_row(
                row: dict[str, Any],
                *,
                bound_ledger_name: str = ledger_name,
                bound_row_type: str = row_type,
            ) -> None:
                if (
                    bound_ledger_name == "missed"
                    and row.get("missed_opportunity_compact_schema")
                    == COMPACT_MISSED_OPPORTUNITY_SCHEMA
                ):
                    return
                normalize_replay_quality_fields(row, row_type=bound_row_type)
                if bound_ledger_name in {"order", "trade"}:
                    normalize_package_new_entry_authority_ledger_row(row)

            rows.set_materialization_transform(normalize_materialized_row)
            continue
        for row in rows:
            if isinstance(row, dict):
                normalize_replay_quality_fields(row, row_type=row_type)
                if ledger_name in {"order", "trade"}:
                    normalize_package_new_entry_authority_ledger_row(row)


def preserve_candidate_decision_quality_default_provenance(row: dict[str, Any]) -> None:
    """Keep default-confidence provenance visible after compact ledger projection."""

    quality = candidate_decision_quality_envelope(row)
    if quality:
        row["candidate_decision_quality"] = quality
    field_sources = None
    if isinstance(quality, Mapping):
        field_sources = (
            quality.get("candidate_decision_quality_field_sources")
            or quality.get("field_sources")
        )
    if (
        isinstance(field_sources, Mapping)
        and field_sources
        and row.get("candidate_decision_quality_field_sources") in (None, "", [], {})
    ):
        row["candidate_decision_quality_field_sources"] = dict(field_sources)
    if isinstance(quality, Mapping):
        for target, aliases in {
            "candidate_decision_quality_source_boundary": (
                "source_boundary",
                "candidate_decision_quality_source_boundary",
            ),
            "candidate_decision_quality_alias_status": (
                "alias_status",
                "candidate_decision_quality_alias_status",
            ),
        }.items():
            if row.get(target) not in (None, "", [], {}):
                continue
            for alias in aliases:
                value = quality.get(alias)
                if value not in (None, "", [], {}):
                    row[target] = value
                    break
        warnings = (
            quality.get("candidate_decision_quality_optional_provenance_warnings")
            or quality.get("optional_provenance_warnings")
        )
        if (
            warnings not in (None, "", [], {})
            and row.get("candidate_decision_quality_optional_provenance_warnings")
            in (None, "", [], {})
        ):
            row["candidate_decision_quality_optional_provenance_warnings"] = list(
                warnings
                if isinstance(warnings, Sequence)
                and not isinstance(warnings, (str, bytes, bytearray))
                else [warnings]
            )
        if quality.get("confidence_missing_degraded_default_applied") is True:
            row["confidence_missing_degraded_default_applied"] = True


def normalize_stop_hazard_guard_cap_truth(row: dict[str, Any]) -> None:
    """Normalize stale compact stop-hazard cap fields without weakening verifier."""

    for prefix in ("", "selected_scheduler_", "scheduler_option_"):
        status_key = f"{prefix}predecision_stop_hazard_guard_status"
        reason_key = f"{prefix}predecision_stop_hazard_guard_reason"
        action_key = f"{prefix}predecision_stop_hazard_guard_action"
        applied_key = f"{prefix}predecision_stop_hazard_guard_risk_cap_applied"
        cap_key = f"{prefix}predecision_stop_hazard_guard_risk_cap_pct"
        guard_key = f"{prefix}predecision_stop_hazard_guard"
        guard = row.get(guard_key)
        guard_map = guard if isinstance(guard, Mapping) else {}
        status = str(row.get(status_key) or guard_map.get("status") or "").strip().lower()
        reason = str(row.get(reason_key) or guard_map.get("reason") or "").strip().lower()
        action = str(row.get(action_key) or guard_map.get("action") or "").strip().lower()
        cap_pct = row.get(cap_key)
        if quality_value_missing(cap_pct):
            cap_pct = guard_map.get("risk_cap_pct")
        cap_pct_present = not quality_value_missing(cap_pct)
        non_cap_status = status in {"pass", "passed", "clear", "allowed"}
        capped_truth = (
            status == "capped"
            or "risk_capped" in reason
            or (action in {"cap", "capped"} and cap_pct_present and not non_cap_status)
        )
        if not capped_truth:
            continue
        row[applied_key] = True
        if isinstance(guard, Mapping):
            guard_copy = dict(guard)
            guard_copy["risk_cap_applied"] = True
            if cap_pct_present and quality_value_missing(guard_copy.get("risk_cap_pct")):
                guard_copy["risk_cap_pct"] = cap_pct
            row[guard_key] = guard_copy


SELECTED_SCHEDULER_OPTION_MAP_FIELDS: tuple[str, ...] = (
    "selected_scheduler_options_by_candidate_id",
    "selected_scheduler_options_by_candidate_instance_key",
    "selected_scheduler_options_by_candidate_id_lookup_status",
)


def preserve_replay_truth_projection(
    compact: dict[str, Any],
    source: Mapping[str, Any],
    *,
    selected_scheduler_alias: bool,
) -> None:
    """Keep canonical replay context/replacement truth in compact ledgers."""

    projection = scheduler_replay_truth_projection_fields(
        source,
        compact,
        selected_scheduler_alias=selected_scheduler_alias,
    )
    for key, value in projection.items():
        if value not in (None, "", [], {}):
            compact[key] = value
    for key in SELECTED_SCHEDULER_OPTION_MAP_FIELDS:
        value = source.get(key)
        if value not in (None, "", [], {}):
            compact[key] = value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def selection_sizing_factorial_risk_lifecycle_audit(
    *,
    order_path: Path,
    trade_path: Path,
    factorial_arm_binding: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Reconstruct the sealed factorial risk lifecycle from serialized rows."""

    if factorial_arm_binding is None:
        return {
            "schema": "gtos.b7_5.selection_sizing.risk_lifecycle_audit.v1",
            "status": "not_applicable_factorial_arm_not_bound",
            "required": False,
            "valid": True,
        }
    matched_risk = factorial_arm_binding.get("matched_risk")
    matched_risk = matched_risk if isinstance(matched_risk, Mapping) else {}
    daily_cap = safe_float(matched_risk.get("daily_accepted_risk_pct_cap"), 0.0)
    portfolio_cap = safe_float(
        matched_risk.get("peak_open_plus_pending_risk_pct_cap"),
        0.0,
    )
    cluster_cap = safe_float(matched_risk.get("cluster_risk_pct_cap"), 0.0)
    opening_cap = safe_float(
        matched_risk.get("opening_window_risk_pct_cap"),
        0.0,
    )
    failures: list[dict[str, Any]] = []

    def fail(reason: str, **detail: Any) -> None:
        if len(failures) < 64:
            failures.append({"reason": reason, **detail})

    def event_time(value: Any, *, reason: str, order_id: str) -> datetime | None:
        text = str(value or "").strip()
        if not text:
            fail(reason, simulated_order_id=order_id)
            return None
        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(
                timezone.utc
            )
        except ValueError:
            fail(
                f"{reason}_invalid",
                simulated_order_id=order_id,
                value=text,
            )
            return None

    def lifecycle_scope(row: Mapping[str, Any]) -> tuple[str, str, str]:
        return (
            str(row.get("profile") or "default_profile").strip(),
            str(row.get("campaign") or "default_campaign").strip(),
            str(
                first_present(
                    row.get("account_id"),
                    row.get("broker_account_id"),
                    row.get("simulated_account_id"),
                    "simulated_account",
                )
                or "simulated_account"
            ).strip(),
        )

    def accepted_reservation_day(
        row: Mapping[str, Any],
        *,
        order_id: str,
    ) -> str:
        value = str(
            first_present(
                row.get("accepted_risk_reservation_day"),
                row.get("trading_day"),
            )
            or ""
        ).strip()
        try:
            date.fromisoformat(value)
        except ValueError:
            fail(
                "accepted_risk_reservation_day_missing_or_invalid",
                simulated_order_id=order_id,
                value=value or None,
            )
            return "invalid_reservation_day"
        return value

    Scope = tuple[str, str, str]
    ScopedOrder = tuple[Scope, str]
    events: list[
        tuple[datetime, int, Scope, str, str, dict[str, Any]]
    ] = []
    accepted_rows_by_order: dict[ScopedOrder, dict[str, Any]] = {}
    terminal_rows_by_order: dict[ScopedOrder, dict[str, Any]] = {}
    order_rows = read_jsonl(order_path)
    trade_rows = read_jsonl(trade_path)
    for row in order_rows:
        order_id = str(row.get("simulated_order_id") or "").strip()
        if not order_id:
            fail("order_id_missing")
            continue
        scope = lifecycle_scope(row)
        scoped_order = (scope, order_id)
        stage = str(row.get("order_event_stage") or "")
        if stage == "accepted_pending":
            if scoped_order in accepted_rows_by_order:
                fail("accepted_pending_duplicate", simulated_order_id=order_id)
                continue
            accepted_rows_by_order[scoped_order] = row
            when = event_time(
                first_present(
                    row.get("event_time_utc"),
                    row.get("created_time_utc"),
                    row.get("decision_time_utc"),
                ),
                reason="accepted_pending_time_missing",
                order_id=order_id,
            )
            if when is not None:
                events.append((when, 0, scope, order_id, "accept", row))
        elif row.get("is_terminal_order_event") is True:
            if scoped_order in terminal_rows_by_order:
                fail("terminal_order_duplicate", simulated_order_id=order_id)
                continue
            terminal_rows_by_order[scoped_order] = row
            terminal_filled = str(row.get("order_status") or "") == "filled"
            when = event_time(
                first_present(
                    row.get("event_time_utc"),
                    row.get("fill_time_utc") if terminal_filled else None,
                    row.get("expiry_utc"),
                ),
                reason="terminal_order_time_missing",
                order_id=order_id,
            )
            if when is not None:
                events.append(
                    (
                        when,
                        1 if terminal_filled else 2,
                        scope,
                        order_id,
                        "fill" if terminal_filled else "unfilled_release",
                        row,
                    )
                )
    trade_rows_by_order: dict[ScopedOrder, dict[str, Any]] = {}
    for row in trade_rows:
        order_id = str(row.get("simulated_order_id") or "").strip()
        if not order_id:
            fail("trade_order_id_missing")
            continue
        scope = lifecycle_scope(row)
        scoped_order = (scope, order_id)
        if scoped_order in trade_rows_by_order:
            fail("trade_row_duplicate", simulated_order_id=order_id)
            continue
        trade_rows_by_order[scoped_order] = row
        when = event_time(
            first_present(row.get("exit_time_utc"), row.get("close_time_utc")),
            reason="trade_close_time_missing",
            order_id=order_id,
        )
        if when is not None:
            events.append((when, 2, scope, order_id, "close_release", row))

    def causally_ordered_events() -> list[
        tuple[datetime, int, Scope, str, str, dict[str, Any]]
    ]:
        """Resolve equal timestamps from serialized counter/state evidence."""

        ordered: list[
            tuple[datetime, int, Scope, str, str, dict[str, Any]]
        ] = []
        shadow_active: dict[ScopedOrder, dict[str, Any]] = {}
        shadow_daily: dict[tuple[Scope, str], float] = defaultdict(float)
        by_time: dict[
            datetime,
            list[tuple[datetime, int, Scope, str, str, dict[str, Any]]],
        ] = defaultdict(list)
        for event in events:
            by_time[event[0]].append(event)

        def raw_reservation_day(row: Mapping[str, Any]) -> str:
            return str(
                first_present(
                    row.get("accepted_risk_reservation_day"),
                    row.get("trading_day"),
                )
                or "invalid_reservation_day"
            ).strip()

        def counter_matches(value: Any, expected: float) -> bool:
            observed = safe_float(value, math.nan)
            return not math.isfinite(observed) or abs(observed - expected) <= 1e-9

        for when in sorted(by_time):
            remaining = sorted(
                by_time[when],
                key=lambda event: (event[1], event[2], event[3], event[4]),
            )
            while remaining:
                ready: list[
                    tuple[
                        int,
                        int,
                        tuple[datetime, int, Scope, str, str, dict[str, Any]],
                    ]
                ] = []
                for index, event in enumerate(remaining):
                    _when, _priority, scope, order_id, kind, row = event
                    scoped_order = (scope, order_id)
                    state = shadow_active.get(scoped_order)
                    if kind == "accept":
                        reservation_day = raw_reservation_day(row)
                        daily_key = (scope, reservation_day)
                        if state is None and counter_matches(
                            row.get("daily_accepted_risk_pct_before"),
                            shadow_daily[daily_key],
                        ):
                            ready.append((2, index, event))
                    elif kind == "fill":
                        if state is not None and state.get("state") == "pending":
                            ready.append((1, index, event))
                    else:
                        required_state = (
                            "pending" if kind == "unfilled_release" else "open"
                        )
                        release = row.get("accepted_risk_reservation_release")
                        release = release if isinstance(release, Mapping) else {}
                        if state is not None and state.get("state") == required_state:
                            daily_key = (scope, str(state.get("reservation_day") or ""))
                            if counter_matches(
                                release.get(
                                    "day_accepted_risk_pct_before_release"
                                ),
                                shadow_daily[daily_key],
                            ):
                                ready.append((0, index, event))
                if ready:
                    _rank, chosen_index, chosen = min(
                        ready,
                        key=lambda item: (
                            item[0],
                            item[2][2],
                            item[2][3],
                            item[2][4],
                        ),
                    )
                else:
                    chosen_index = 0
                    chosen = remaining[0]
                remaining.pop(chosen_index)
                ordered.append(chosen)
                _when, _priority, scope, order_id, kind, row = chosen
                scoped_order = (scope, order_id)
                if kind == "accept":
                    reservation_day = raw_reservation_day(row)
                    risk_pct = max(
                        0.0,
                        safe_float(
                            first_present(
                                row.get("reserved_risk_pct"),
                                row.get("risk_pct"),
                            ),
                            0.0,
                        ),
                    )
                    shadow_active[scoped_order] = {
                        "state": "pending",
                        "risk_pct": risk_pct,
                        "reservation_day": reservation_day,
                    }
                    shadow_daily[(scope, reservation_day)] += risk_pct
                elif kind == "fill":
                    state = shadow_active.get(scoped_order)
                    if state is not None:
                        state["state"] = "open"
                else:
                    state = shadow_active.pop(scoped_order, None)
                    if state is not None:
                        shadow_daily[
                            (scope, str(state.get("reservation_day") or ""))
                        ] -= safe_float(state.get("risk_pct"), 0.0)
        return ordered

    lifecycle_events = causally_ordered_events()

    active: dict[ScopedOrder, dict[str, Any]] = {}
    daily_risk: dict[tuple[Scope, str], float] = defaultdict(float)
    pending_risk: dict[Scope, float] = defaultdict(float)
    open_risk: dict[Scope, float] = defaultdict(float)
    session_risk: dict[tuple[Scope, str, str], float] = defaultdict(float)
    cluster_risk: dict[tuple[Scope, str], float] = defaultdict(float)
    peak_daily_risk = 0.0
    peak_open_plus_pending_risk = 0.0
    peak_opening_window_risk = 0.0
    peak_cluster_risk: dict[str, float] = defaultdict(float)
    accepted_count = 0
    pending_to_open_transfer_count = 0
    close_or_expiry_event_count = 0
    close_or_expiry_release_count = 0
    physical_accepted_risk_pct_sum = 0.0
    timeline: list[dict[str, Any]] = []
    tolerance = 1e-9
    for when, _priority, scope, order_id, kind, row in lifecycle_events:
        scoped_order = (scope, order_id)
        if kind == "accept":
            if scoped_order in active:
                fail("accept_reuses_active_order", simulated_order_id=order_id)
                continue
            risk_authority = row.get("risk_authority")
            risk_authority = (
                risk_authority if isinstance(risk_authority, Mapping) else {}
            )
            risk_pct = max(
                0.0,
                safe_float(
                    first_present(row.get("reserved_risk_pct"), row.get("risk_pct")),
                    0.0,
                ),
            )
            cluster = str(
                first_present(
                    row.get("same_decision_cluster_side_risk_order_cluster"),
                    risk_authority.get(
                        "same_decision_cluster_side_risk_order_cluster"
                    ),
                )
                or ""
            ).strip()
            if not cluster:
                fail(
                    "accepted_risk_cluster_identity_missing",
                    simulated_order_id=order_id,
                )
            session = str(
                risk_authority.get("opening_window_session_counter_key") or ""
            ).strip()
            reservation_day = accepted_reservation_day(row, order_id=order_id)
            daily_key = (scope, reservation_day)
            session_key = (scope, reservation_day, session)
            cluster_key = (scope, cluster)
            allocator = risk_authority.get(
                "dynamic_daily_drawdown_budget_allocator"
            )
            allocator = allocator if isinstance(allocator, Mapping) else {}
            if allocator.get(
                "b7_5_selection_sizing_factorial_hard_cap_package_releases_suppressed"
            ) is not True:
                fail(
                    "factorial_package_hard_cap_release_suppression_missing",
                    simulated_order_id=order_id,
                )
            opening = allocator.get("opening_window_reserve")
            opening = opening if isinstance(opening, Mapping) else {}
            if opening.get("risk_cap_release_applied") is True:
                fail(
                    "factorial_opening_risk_cap_release_applied",
                    simulated_order_id=order_id,
                )
            opening_active = opening.get("active") is True
            opening_counter_scope = str(
                opening.get("counter_scope")
                or ("configured_session" if session else "utc_day")
            ).strip()
            serialized_before = safe_float(
                row.get("daily_accepted_risk_pct_before"),
                math.nan,
            )
            if not math.isfinite(serialized_before) or abs(
                serialized_before - daily_risk[daily_key]
            ) > tolerance:
                fail(
                    "daily_accepted_risk_before_serialized_mismatch",
                    simulated_order_id=order_id,
                    serialized=serialized_before,
                    reconstructed=round(daily_risk[daily_key], 12),
                )
            active[scoped_order] = {
                "risk_pct": risk_pct,
                "state": "pending",
                "cluster": cluster,
                "session": session,
                "reservation_day": reservation_day,
            }
            daily_risk[daily_key] += risk_pct
            pending_risk[scope] += risk_pct
            if cluster:
                cluster_risk[cluster_key] += risk_pct
            if session:
                session_risk[session_key] += risk_pct
            accepted_count += 1
            physical_accepted_risk_pct_sum += risk_pct
            serialized_after = safe_float(
                row.get("daily_accepted_risk_pct_after"),
                math.nan,
            )
            if not math.isfinite(serialized_after) or abs(
                serialized_after - daily_risk[daily_key]
            ) > tolerance:
                fail(
                    "daily_accepted_risk_after_serialized_mismatch",
                    simulated_order_id=order_id,
                    serialized=serialized_after,
                    reconstructed=round(daily_risk[daily_key], 12),
                )
            if daily_risk[daily_key] > daily_cap + tolerance:
                fail(
                    "daily_accepted_risk_cap_breached",
                    simulated_order_id=order_id,
                    actual=round(daily_risk[daily_key], 12),
                    cap=daily_cap,
                )
            if open_risk[scope] + pending_risk[scope] > portfolio_cap + tolerance:
                fail(
                    "peak_open_plus_pending_risk_cap_breached",
                    simulated_order_id=order_id,
                    actual=round(open_risk[scope] + pending_risk[scope], 12),
                    cap=portfolio_cap,
                )
            if cluster and cluster_risk[cluster_key] > cluster_cap + tolerance:
                fail(
                    "cluster_risk_cap_breached",
                    simulated_order_id=order_id,
                    cluster=cluster,
                    actual=round(cluster_risk[cluster_key], 12),
                    cap=cluster_cap,
                )
            if opening_active:
                if opening_counter_scope == "configured_session" and not session:
                    fail(
                        "opening_window_active_session_missing",
                        simulated_order_id=order_id,
                    )
                opening_risk = (
                    session_risk.get(session_key, 0.0)
                    if opening_counter_scope == "configured_session"
                    else daily_risk[daily_key]
                )
                if opening_risk > opening_cap + tolerance:
                    fail(
                        "opening_window_risk_cap_breached",
                        simulated_order_id=order_id,
                        counter_scope=opening_counter_scope,
                        session=session or None,
                        actual=round(opening_risk, 12),
                        cap=opening_cap,
                    )
                peak_opening_window_risk = max(
                    peak_opening_window_risk,
                    opening_risk,
                )
        elif kind == "fill":
            state = active.get(scoped_order)
            if state is None or state.get("state") != "pending":
                fail("fill_without_pending_reservation", simulated_order_id=order_id)
                continue
            if row.get("accepted_risk_reservation_released") is not False:
                fail("fill_releases_reservation", simulated_order_id=order_id)
            if str(row.get("accepted_risk_reservation_transition") or "") != (
                "pending_order_to_filled_position"
            ):
                fail("fill_transfer_transition_invalid", simulated_order_id=order_id)
            state["state"] = "open"
            pending_risk[scope] -= state["risk_pct"]
            open_risk[scope] += state["risk_pct"]
            pending_to_open_transfer_count += 1
        elif kind == "unfilled_release":
            state = active.pop(scoped_order, None)
            if state is None or state.get("state") != "pending":
                fail("unfilled_release_without_pending", simulated_order_id=order_id)
                continue
            release_proven = row.get("accepted_risk_reservation_released") is True
            if not release_proven:
                fail("unfilled_release_flag_missing", simulated_order_id=order_id)
            risk_pct = state["risk_pct"]
            release = row.get("accepted_risk_reservation_release")
            if not isinstance(release, Mapping):
                fail("unfilled_release_payload_missing", simulated_order_id=order_id)
                release = {}
                release_proven = False
            if release.get("accepted_risk_exact_release_required") is not True:
                release_proven = False
                fail(
                    "unfilled_release_not_exact",
                    simulated_order_id=order_id,
                )
            reservation_day = str(state.get("reservation_day") or "")
            release_day = str(
                release.get("accepted_risk_reservation_day") or ""
            )
            if release_day != reservation_day:
                release_proven = False
                fail(
                    "unfilled_release_reservation_day_mismatch",
                    simulated_order_id=order_id,
                    expected=reservation_day,
                    actual=release_day or None,
                )
            daily_key = (scope, reservation_day)
            session_key = (scope, reservation_day, str(state["session"]))
            cluster_key = (scope, str(state["cluster"]))
            released_risk_pct = safe_float(
                first_present(
                    row.get("released_risk_pct"),
                    release.get("released_risk_pct"),
                ),
                math.nan,
            )
            if not math.isfinite(released_risk_pct) or abs(
                released_risk_pct - risk_pct
            ) > tolerance:
                release_proven = False
                fail(
                    "unfilled_release_risk_mismatch",
                    simulated_order_id=order_id,
                    released=released_risk_pct,
                    reserved=risk_pct,
                )
            release_before = safe_float(
                release.get("day_accepted_risk_pct_before_release"),
                math.nan,
            )
            release_after = safe_float(
                release.get("day_accepted_risk_pct_after_release"),
                math.nan,
            )
            if not math.isfinite(release_before) or abs(
                release_before - daily_risk[daily_key]
            ) > tolerance:
                release_proven = False
                fail(
                    "unfilled_release_before_serialized_mismatch",
                    simulated_order_id=order_id,
                    serialized=release_before,
                    reconstructed=round(daily_risk[daily_key], 12),
                )
            daily_risk[daily_key] -= risk_pct
            pending_risk[scope] -= risk_pct
            if state["cluster"]:
                cluster_risk[cluster_key] -= risk_pct
            if state["session"]:
                session_risk[session_key] -= risk_pct
            if not math.isfinite(release_after) or abs(
                release_after - daily_risk[daily_key]
            ) > tolerance:
                release_proven = False
                fail(
                    "unfilled_release_after_serialized_mismatch",
                    simulated_order_id=order_id,
                    serialized=release_after,
                    reconstructed=round(daily_risk[daily_key], 12),
                )
            close_or_expiry_event_count += 1
            if release_proven:
                close_or_expiry_release_count += 1
        else:
            state = active.pop(scoped_order, None)
            if state is None or state.get("state") != "open":
                fail("close_release_without_open_position", simulated_order_id=order_id)
                continue
            release_proven = row.get("accepted_risk_reservation_released") is True
            if not release_proven:
                fail("trade_close_release_flag_missing", simulated_order_id=order_id)
            release = row.get("accepted_risk_reservation_release")
            if not isinstance(release, Mapping):
                fail("trade_close_release_payload_missing", simulated_order_id=order_id)
                release = {}
                release_proven = False
            if release.get("accepted_risk_exact_release_required") is not True:
                release_proven = False
                fail(
                    "trade_close_release_not_exact",
                    simulated_order_id=order_id,
                )
            reservation_day = str(state.get("reservation_day") or "")
            release_day = str(
                release.get("accepted_risk_reservation_day") or ""
            )
            if release_day != reservation_day:
                release_proven = False
                fail(
                    "trade_close_release_reservation_day_mismatch",
                    simulated_order_id=order_id,
                    expected=reservation_day,
                    actual=release_day or None,
                )
            daily_key = (scope, reservation_day)
            session_key = (scope, reservation_day, str(state["session"]))
            cluster_key = (scope, str(state["cluster"]))
            risk_pct = state["risk_pct"]
            released_risk_pct = safe_float(
                first_present(
                    row.get("accepted_risk_released_pct"),
                    release.get("released_risk_pct"),
                ),
                math.nan,
            )
            if not math.isfinite(released_risk_pct) or abs(
                released_risk_pct - risk_pct
            ) > tolerance:
                release_proven = False
                fail(
                    "trade_close_release_risk_mismatch",
                    simulated_order_id=order_id,
                    released=released_risk_pct,
                    reserved=risk_pct,
                )
            release_before = safe_float(
                release.get("day_accepted_risk_pct_before_release"),
                math.nan,
            )
            release_after = safe_float(
                release.get("day_accepted_risk_pct_after_release"),
                math.nan,
            )
            if not math.isfinite(release_before) or abs(
                release_before - daily_risk[daily_key]
            ) > tolerance:
                release_proven = False
                fail(
                    "trade_close_release_before_serialized_mismatch",
                    simulated_order_id=order_id,
                    serialized=release_before,
                    reconstructed=round(daily_risk[daily_key], 12),
                )
            daily_risk[daily_key] -= risk_pct
            open_risk[scope] -= risk_pct
            if state["cluster"]:
                cluster_risk[cluster_key] -= risk_pct
            if state["session"]:
                session_risk[session_key] -= risk_pct
            if not math.isfinite(release_after) or abs(
                release_after - daily_risk[daily_key]
            ) > tolerance:
                release_proven = False
                fail(
                    "trade_close_release_after_serialized_mismatch",
                    simulated_order_id=order_id,
                    serialized=release_after,
                    reconstructed=round(daily_risk[daily_key], 12),
                )
            close_or_expiry_event_count += 1
            if release_proven:
                close_or_expiry_release_count += 1
        for risk_map in (
            daily_risk,
            pending_risk,
            open_risk,
            session_risk,
            cluster_risk,
        ):
            for key in list(risk_map):
                if abs(risk_map[key]) <= tolerance:
                    risk_map[key] = 0.0
        current_daily_peak = max(daily_risk.values(), default=0.0)
        current_portfolio_peak = max(
            (
                open_risk[scope_key] + pending_risk[scope_key]
                for scope_key in set(open_risk) | set(pending_risk)
            ),
            default=0.0,
        )
        peak_daily_risk = max(peak_daily_risk, current_daily_peak)
        peak_open_plus_pending_risk = max(
            peak_open_plus_pending_risk,
            current_portfolio_peak,
        )
        for (_cluster_scope, cluster), value in cluster_risk.items():
            peak_cluster_risk[cluster] = max(peak_cluster_risk[cluster], value)
        if len(timeline) < 128:
            release = row.get("accepted_risk_reservation_release")
            release = release if isinstance(release, Mapping) else {}
            timeline_reservation_day = str(
                first_present(
                    row.get("accepted_risk_reservation_day"),
                    release.get("accepted_risk_reservation_day"),
                    row.get("trading_day"),
                )
                or "invalid_reservation_day"
            )
            timeline_daily_key = (scope, timeline_reservation_day)
            timeline.append(
                {
                    "event_time_utc": when.isoformat(),
                    "event_type": kind,
                    "simulated_order_id": order_id,
                    "profile": scope[0],
                    "campaign": scope[1],
                    "account_scope": scope[2],
                    "accepted_risk_reservation_day": timeline_reservation_day,
                    "processing_day": row.get("trading_day"),
                    "daily_accepted_risk_pct": round(
                        daily_risk[timeline_daily_key],
                        12,
                    ),
                    "pending_risk_pct": round(pending_risk[scope], 12),
                    "open_risk_pct": round(open_risk[scope], 12),
                    "open_plus_pending_risk_pct": round(
                        open_risk[scope] + pending_risk[scope],
                        12,
                    ),
                }
            )
    if set(accepted_rows_by_order) != set(terminal_rows_by_order):
        fail(
            "accepted_terminal_order_identity_mismatch",
            accepted_minus_terminal=sorted(
                set(accepted_rows_by_order) - set(terminal_rows_by_order)
            )[:20],
            terminal_minus_accepted=sorted(
                set(terminal_rows_by_order) - set(accepted_rows_by_order)
            )[:20],
        )
    filled_order_ids = {
        order_id
        for order_id, row in terminal_rows_by_order.items()
        if str(row.get("order_status") or "") == "filled"
    }
    if filled_order_ids != set(trade_rows_by_order):
        fail(
            "filled_trade_order_identity_mismatch",
            filled_minus_trade=sorted(filled_order_ids - set(trade_rows_by_order))[:20],
            trade_minus_filled=sorted(set(trade_rows_by_order) - filled_order_ids)[:20],
        )
    if active:
        fail("active_reservations_remain_after_terminal_events", order_ids=sorted(active)[:20])
    terminal_daily_risk = sum(daily_risk.values())
    terminal_pending_risk = sum(pending_risk.values())
    terminal_open_risk = sum(open_risk.values())
    if any(
        abs(value) > tolerance
        for value in (
            *daily_risk.values(),
            *pending_risk.values(),
            *open_risk.values(),
            *session_risk.values(),
            *cluster_risk.values(),
        )
    ):
        fail(
            "terminal_risk_not_zero",
            daily=round(terminal_daily_risk, 12),
            pending=round(terminal_pending_risk, 12),
            open=round(terminal_open_risk, 12),
        )
    valid = not failures
    return {
        "schema": "gtos.b7_5.selection_sizing.risk_lifecycle_audit.v1",
        "status": (
            "factorial_risk_lifecycle_contract_valid"
            if valid
            else "factorial_risk_lifecycle_contract_invalid"
        ),
        "required": True,
        "valid": valid,
        "arm_id": factorial_arm_binding.get("arm_id"),
        "matched_risk": dict(matched_risk),
        "accepted_order_count": accepted_count,
        "pending_to_open_transfer_count": pending_to_open_transfer_count,
        "close_or_expiry_event_count": close_or_expiry_event_count,
        "close_or_expiry_release_count": close_or_expiry_release_count,
        "physical_accepted_risk_pct_sum": round(physical_accepted_risk_pct_sum, 12),
        "peak_daily_accepted_risk_pct": round(peak_daily_risk, 12),
        "peak_open_plus_pending_risk_pct": round(
            peak_open_plus_pending_risk,
            12,
        ),
        "peak_opening_window_risk_pct": round(peak_opening_window_risk, 12),
        "peak_cluster_risk_pct": {
            key: round(value, 12)
            for key, value in sorted(peak_cluster_risk.items())
        },
        "risk_scope_count": len(
            {
                scope
                for scope, _reservation_day in daily_risk
            }
        ),
        "reservation_day_scope_count": len(daily_risk),
        "terminal_daily_accepted_risk_pct": round(terminal_daily_risk, 12),
        "terminal_pending_risk_pct": round(terminal_pending_risk, 12),
        "terminal_open_risk_pct": round(terminal_open_risk, 12),
        "failure_count": len(failures),
        "failures": failures,
        "timeline": timeline,
        "uses_outcome_fields": True,
        "outcome_fields_used_for_post_execution_audit_only": [
            "fill_time_utc",
            "exit_time_utc",
            "close_time_utc",
            "terminal_order_status",
        ],
        "uses_outcome_fields_for_selection_or_sizing": False,
        "broker_mutation_enabled": False,
        "live_broker_authority": False,
        "final_selection_claim": False,
    }


def append_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, default=str) + "\n")
            count += 1
    return count


def write_attempt5_semantic_source_manifest(
    *,
    outputs: Mapping[str, Path],
    campaign_days_by_profile: Mapping[str, Sequence[str]],
    archive_manifest_path: Path,
    archive_verification_receipt_path: Path,
    arm_id: str,
) -> dict[str, Any]:
    if len(campaign_days_by_profile) != 1:
        raise ValueError("semantic_source_exactly_one_profile_required")
    profile, campaign_days = next(iter(campaign_days_by_profile.items()))
    if type(profile) is not str or profile != profile.strip() or not profile:
        raise ValueError("semantic_source_profile_invalid")
    order_name = outputs["order"].name
    order_suffix = "_ORDER_LEDGER.jsonl"
    if not order_name.endswith(order_suffix):
        raise ValueError("semantic_source_output_prefix_invalid")
    output_prefix = order_name[: -len(order_suffix)]
    return seal_semantic_source_manifest(
        source_manifest_path=outputs["semantic_source_manifest"],
        evidence_paths={
            "candidate": outputs["semantic_candidate"],
            "order": outputs["order"],
            "trade": outputs["trade"],
            "oracle": outputs["oracle"],
            "state_checkpoint": outputs["semantic_state_checkpoint"],
            "order_preimage": outputs["semantic_order_preimage"],
        },
        archive_manifest_path=archive_manifest_path,
        archive_verification_receipt_path=(
            archive_verification_receipt_path
        ),
        campaign_id=f"{output_prefix.lower()}_{profile}",
        profile=profile,
        arm_id=arm_id,
        campaign_days=campaign_days,
    )


SEMANTIC_ORDER_OWNER_FIELDS = (
    "campaign",
    "decision_window_id",
    "canonical_replay_candidate_instance_key",
    "candidate_id",
    "simulated_order_id",
    "decision_time_utc",
)


def semantic_order_owner_matches(
    *,
    owner: Mapping[str, Any],
    order_row: Mapping[str, Any],
    execution_packet_sidecar_id: Any,
    require_profile: bool,
) -> bool:
    if any(
        owner.get(field) != order_row.get(field)
        for field in SEMANTIC_ORDER_OWNER_FIELDS
    ):
        return False
    if execution_packet_sidecar_id != order_row.get(
        "execution_packet_sidecar_id"
    ):
        return False
    order_profile = first_present(
        order_row.get("profile"),
        order_row.get("broad_replay_profile"),
    )
    if require_profile:
        return owner.get("profile") == order_profile
    return order_profile in (None, "") or owner.get("profile") == order_profile


def prebind_semantic_order_preimages_to_final_producer_rows(
    *,
    preimage_rows: Iterable[Mapping[str, Any]],
    producer_order_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Resolve capture hashes before runner normalization mutates order rows."""

    sources = list(preimage_rows)
    final_indexes_by_producer_hash: dict[str, list[int]] = defaultdict(list)
    for final_index, producer_order in enumerate(producer_order_rows):
        if not isinstance(producer_order, Mapping):
            raise ValueError(
                f"semantic_order_prebinding_producer_row_invalid:{final_index}"
            )
        final_indexes_by_producer_hash[stable_sha256(producer_order)].append(
            final_index
        )

    prebindings: list[dict[str, Any]] = []
    seen_capture_indexes: set[int] = set()
    seen_final_indexes: set[int] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise ValueError(f"semantic_order_prebinding_row_invalid:{index}")
        capture_index = source.get("producer_order_stream_index")
        if (
            type(capture_index) is not int
            or capture_index < 0
            or capture_index >= len(producer_order_rows)
            or capture_index in seen_capture_indexes
        ):
            raise ValueError(f"semantic_order_prebinding_index_invalid:{index}")
        owner = source.get("owner")
        producer_hash = source.get("producer_order_row_sha256")
        matching_final_indexes: list[int] = []
        if isinstance(owner, Mapping) and isinstance(producer_hash, str):
            for final_index in final_indexes_by_producer_hash.get(
                producer_hash, ()
            ):
                if semantic_order_owner_matches(
                    owner=owner,
                    order_row=producer_order_rows[final_index],
                    execution_packet_sidecar_id=source.get(
                        "execution_packet_sidecar_id"
                    ),
                    require_profile=False,
                ):
                    matching_final_indexes.append(final_index)
        if not matching_final_indexes:
            raise ValueError(f"semantic_order_prebinding_owner_mismatch:{index}")
        if len(matching_final_indexes) != 1:
            raise ValueError(
                f"semantic_order_prebinding_ambiguous_exact_preimage:{index}"
            )
        final_index = matching_final_indexes[0]
        if final_index in seen_final_indexes:
            raise ValueError(
                f"semantic_order_prebinding_resolved_index_reused:{index}"
            )
        seen_capture_indexes.add(capture_index)
        seen_final_indexes.add(final_index)
        expected_normalized_order = copy.deepcopy(
            dict(producer_order_rows[final_index])
        )
        normalize_replay_quality_fields(
            expected_normalized_order,
            row_type="simulated_order",
        )
        normalize_package_new_entry_authority_ledger_row(
            expected_normalized_order
        )
        prebindings.append(
            {
                "capture_row_index": index,
                "semantic_order_preimage_row_sha256": stable_sha256(source),
                "producer_order_stream_index": capture_index,
                "producer_order_row_sha256": producer_hash,
                "final_producer_order_stream_index": final_index,
                "pre_normalization_producer_order_row_sha256": stable_sha256(
                    producer_order_rows[final_index]
                ),
                "expected_post_normalization_producer_order_row_sha256": (
                    stable_sha256(expected_normalized_order)
                ),
            }
        )
    return prebindings


def bind_semantic_order_preimages_to_persisted_rows(
    *,
    preimage_rows: Iterable[Mapping[str, Any]],
    prebindings: Sequence[Mapping[str, Any]],
    producer_order_rows: Sequence[Mapping[str, Any]],
    persisted_order_rows: Sequence[Mapping[str, Any]],
    persisted_order_stream_offset: int,
) -> list[dict[str, Any]]:
    sources = list(preimage_rows)
    if len(producer_order_rows) != len(persisted_order_rows):
        raise ValueError("semantic_order_binding_inventory_mismatch")
    if len(sources) != len(prebindings):
        raise ValueError("semantic_order_prebinding_inventory_mismatch")
    if (
        type(persisted_order_stream_offset) is not int
        or persisted_order_stream_offset < 0
    ):
        raise ValueError("semantic_order_binding_stream_offset_invalid")

    bound: list[dict[str, Any]] = []
    seen_capture_indexes: set[int] = set()
    seen_final_indexes: set[int] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            raise ValueError(f"semantic_order_binding_row_invalid:{index}")
        row = dict(source)
        capture_index = row.get("producer_order_stream_index")
        if (
            type(capture_index) is not int
            or capture_index < 0
            or capture_index >= len(producer_order_rows)
            or capture_index in seen_capture_indexes
        ):
            raise ValueError(f"semantic_order_binding_index_invalid:{index}")
        prebinding = prebindings[index]
        if not isinstance(prebinding, Mapping):
            raise ValueError(f"semantic_order_prebinding_invalid:{index}")
        owner = row.get("owner")
        producer_hash = row.get("producer_order_row_sha256")
        if (
            prebinding.get("capture_row_index") != index
            or prebinding.get("semantic_order_preimage_row_sha256")
            != stable_sha256(source)
            or prebinding.get("producer_order_stream_index") != capture_index
            or prebinding.get("producer_order_row_sha256") != producer_hash
            or prebinding.get(
                "pre_normalization_producer_order_row_sha256"
            )
            != producer_hash
        ):
            raise ValueError(f"semantic_order_prebinding_mismatch:{index}")
        final_index = prebinding.get("final_producer_order_stream_index")
        if (
            type(final_index) is not int
            or final_index < 0
            or final_index >= len(producer_order_rows)
        ):
            raise ValueError(f"semantic_order_prebinding_index_invalid:{index}")
        if final_index in seen_final_indexes:
            raise ValueError(
                f"semantic_order_binding_resolved_index_reused:{index}"
            )
        producer_order = producer_order_rows[final_index]
        persisted_order = persisted_order_rows[final_index]
        if (
            not isinstance(owner, Mapping)
            or not isinstance(producer_order, Mapping)
            or not isinstance(persisted_order, Mapping)
            or not semantic_order_owner_matches(
                owner=owner,
                order_row=producer_order,
                execution_packet_sidecar_id=row.get(
                    "execution_packet_sidecar_id"
                ),
                require_profile=False,
            )
            or not semantic_order_owner_matches(
                owner=owner,
                order_row=persisted_order,
                execution_packet_sidecar_id=row.get(
                    "execution_packet_sidecar_id"
                ),
                require_profile=True,
            )
        ):
            raise ValueError(f"semantic_order_binding_owner_mismatch:{index}")
        final_producer_hash = stable_sha256(producer_order)
        if (
            final_producer_hash
            != prebinding.get(
                "expected_post_normalization_producer_order_row_sha256"
            )
        ):
            raise ValueError(
                "semantic_order_binding_unexpected_post_normalization_mutation:"
                f"{index}"
            )
        seen_capture_indexes.add(capture_index)
        seen_final_indexes.add(final_index)
        row["final_producer_order_stream_index"] = final_index
        row["pre_normalization_producer_order_row_sha256"] = producer_hash
        row["final_producer_order_row_sha256"] = final_producer_hash
        row["producer_order_row_sha256_matches_final_order"] = (
            producer_hash == final_producer_hash
        )
        row["producer_order_row_mutated_after_capture"] = (
            producer_hash != final_producer_hash
        )
        row["producer_order_stream_index_rebound_after_final_sort"] = (
            final_index != capture_index
        )
        row["persisted_order_stream_index"] = (
            persisted_order_stream_offset + final_index
        )
        row["persisted_order_row_sha256"] = stable_sha256(persisted_order)
        bound.append(row)
    return bound


def compact_asof_decision_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Keep one canonical current-FVG partition when producer audit aliases it."""

    compact_rows: list[dict[str, Any]] = []
    for source in rows:
        compact = dict(source)
        if (
            compact.get("compact_decision_projection_schema")
            == COMPACT_DECISION_PROJECTION_SCHEMA
        ):
            compact_rows.append(compact)
            continue
        partition = compact.get("current_fvg_poi_generation")
        generation_audit = compact.get("candidate_generation_audit")
        generation_audit_copy = (
            dict(generation_audit)
            if isinstance(generation_audit, Mapping)
            else None
        )
        producer_audit = (
            generation_audit_copy.get("producer_generation_audit")
            if generation_audit_copy is not None
            else None
        )
        producer_audit_copy = (
            dict(producer_audit)
            if isinstance(producer_audit, Mapping)
            else None
        )
        nested_partition = (
            producer_audit_copy.get("current_fvg_poi_generation")
            if producer_audit_copy is not None
            else None
        )
        if isinstance(partition, Mapping) and partition:
            status = "canonical_top_level_preserved_no_nested_alias"
            if nested_partition == partition:
                assert producer_audit_copy is not None
                assert generation_audit_copy is not None
                producer_audit_copy.pop("current_fvg_poi_generation", None)
                producer_audit_copy[
                    "current_fvg_poi_generation_projection_ref"
                ] = "top_level.current_fvg_poi_generation"
                generation_audit_copy["producer_generation_audit"] = (
                    producer_audit_copy
                )
                compact["candidate_generation_audit"] = generation_audit_copy
                status = (
                    "canonical_top_level_preserved_exact_nested_alias_omitted"
                )
            elif nested_partition not in (None, "", [], {}):
                status = "distinct_nested_partition_preserved_not_compacted"
            compact["compact_decision_projection_schema"] = (
                COMPACT_DECISION_PROJECTION_SCHEMA
            )
            compact["current_fvg_poi_generation_projection_status"] = status
            compact["current_fvg_poi_generation_projection_sha256"] = (
                stable_sha256(partition)
            )
        compact_rows.append(compact)
    return compact_rows


def compact_scorecard_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Serialize one canonical option trace and preserve distinct aliases."""

    compact_rows: list[dict[str, Any]] = []
    duplicate_alias_fields = (
        "pre_risk_finalizer_scheduler_option_trace",
        "post_risk_finalizer_scheduler_option_trace",
    )
    for source in rows:
        compact = dict(source)
        canonical_trace = compact.get("scheduler_option_trace")
        omitted_aliases: list[str] = []
        if isinstance(canonical_trace, list) and canonical_trace:
            for field in duplicate_alias_fields:
                if compact.get(field) == canonical_trace:
                    compact.pop(field, None)
                    omitted_aliases.append(field)
        if omitted_aliases:
            compact["compact_scorecard_projection_schema"] = (
                COMPACT_SCORECARD_PROJECTION_SCHEMA
            )
            compact["scheduler_option_trace_projection_status"] = (
                "canonical_trace_preserved_exact_duplicate_aliases_omitted"
            )
            compact["scheduler_option_trace_omitted_duplicate_aliases"] = (
                omitted_aliases
            )
            compact["scheduler_option_trace_projection_sha256"] = stable_sha256(
                canonical_trace
            )
        elif isinstance(canonical_trace, list) and canonical_trace:
            distinct_aliases = [
                field
                for field in duplicate_alias_fields
                if compact.get(field) not in (None, "", [], {})
            ]
            compact["compact_scorecard_projection_schema"] = (
                COMPACT_SCORECARD_PROJECTION_SCHEMA
            )
            compact["scheduler_option_trace_projection_status"] = (
                "canonical_trace_preserved_distinct_aliases_not_compacted"
                if distinct_aliases
                else "canonical_trace_preserved_no_aliases_present"
            )
            compact["scheduler_option_trace_omitted_duplicate_aliases"] = []
            compact["scheduler_option_trace_projection_sha256"] = stable_sha256(
                canonical_trace
            )
        compact_rows.append(compact)
    return compact_rows


def candidate_relational_materialization_audit(
    *,
    candidate_rows: Iterable[Mapping[str, Any]],
    missed_rows: Iterable[Mapping[str, Any]],
    order_rows: Iterable[Mapping[str, Any]],
    trade_rows: Iterable[Mapping[str, Any]],
    exit_rows: Iterable[Mapping[str, Any]],
    account_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Require one disjoint terminal disposition for every candidate occurrence."""

    audit, _identity_sets = _candidate_terminal_reconciliation(
        candidate_rows=candidate_rows,
        missed_rows=missed_rows,
        order_rows=order_rows,
        trade_rows=trade_rows,
        exit_rows=exit_rows,
        account_rows=account_rows,
    )
    return audit


def _candidate_terminal_reconciliation(
    *,
    candidate_rows: Iterable[Mapping[str, Any]],
    missed_rows: Iterable[Mapping[str, Any]],
    order_rows: Iterable[Mapping[str, Any]],
    trade_rows: Iterable[Mapping[str, Any]],
    exit_rows: Iterable[Mapping[str, Any]],
    account_rows: Iterable[Mapping[str, Any]],
) -> tuple[dict[str, Any], dict[str, set[str]]]:
    """Stream native ledgers and retain only the join rows needed for proof."""

    row_counts: Counter[str] = Counter()
    missing_keys: Counter[str] = Counter()

    def grouped(
        rows: Iterable[Mapping[str, Any]],
        role: str,
        projector: Any = None,
    ) -> dict[str, list[Any]]:
        out: dict[str, list[Any]] = defaultdict(list)
        for row in rows:
            row_counts[role] += 1
            key = (
                str(row.get("canonical_replay_candidate_instance_key") or "").strip()
                if isinstance(row, Mapping)
                else ""
            )
            if key:
                out[key].append(projector(row) if projector else row)
            else:
                missing_keys[role] += 1
        return out

    candidates = grouped(candidate_rows, "candidate")
    missed = grouped(
        missed_rows,
        "missed",
        lambda row: first_present(
            row.get("terminal_outcome"),
            row.get("opportunity_terminal_outcome"),
            row.get("close_reason"),
        ),
    )
    orders = grouped(order_rows, "order")
    trades = grouped(trade_rows, "trade")
    exits = grouped(exit_rows, "exit")
    candidate_keys = set(candidates)
    stage_groups = {"missed": missed, "order": orders, "trade": trades, "exit": exits}

    failures: Counter[str] = Counter()
    samples: dict[str, list[str]] = defaultdict(list)

    def fail(reason: str, identity: str, count: int = 1) -> None:
        failures[reason] += count
        if identity and identity not in samples[reason] and len(samples[reason]) < 8:
            samples[reason].append(identity)

    for role, count in missing_keys.items():
        if count:
            fail(f"{role}_candidate_instance_key_missing", role, count)
    orphan_keys = {
        role: set(rows) - candidate_keys for role, rows in stage_groups.items()
    }
    for role, keys in orphan_keys.items():
        for key in keys:
            fail(f"orphan_{role}_candidate_instance", key)

    order_owners: dict[str, set[str]] = defaultdict(set)
    trade_owners: dict[str, set[str]] = defaultdict(set)
    for key, rows in orders.items():
        for row in rows:
            order_id = str(row.get("simulated_order_id") or "").strip()
            if order_id:
                order_owners[order_id].add(key)
    for key, rows in trades.items():
        for row in rows:
            order_id = str(row.get("simulated_order_id") or "").strip()
            trade_id = str(row.get("simulated_trade_id") or "").strip()
            if order_id:
                order_owners[order_id].add(key)
            if trade_id:
                trade_owners[trade_id].add(key)
    for owners_by_id in (order_owners, trade_owners):
        for join_id, owners in owners_by_id.items():
            if len(owners) != 1:
                fail("ambiguous_execution_join_id", join_id)

    closed_accounts: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    orphan_account_rows = 0
    for row in account_rows:
        row_counts["account"] += 1
        if not isinstance(row, Mapping):
            orphan_account_rows += 1
            fail("account_row_not_mapping", "account")
            continue
        order_id = str(row.get("simulated_order_id") or "").strip()
        trade_id = str(row.get("simulated_trade_id") or "").strip()
        if not order_id and not trade_id:
            if row.get("event") == "simulated_trade_closed":
                orphan_account_rows += 1
                fail("closed_account_execution_identity_missing", "account")
            continue
        owners = set(order_owners.get(order_id, ())) | set(
            trade_owners.get(trade_id, ())
        )
        if len(owners) != 1:
            orphan_account_rows += 1
            fail("orphan_or_ambiguous_account_join", order_id or trade_id)
            continue
        if row.get("event") == "simulated_trade_closed":
            closed_accounts[next(iter(owners))].append(row)

    dispositions: dict[str, str] = {}
    for key in sorted(candidate_keys):
        crows, mrows = candidates[key], missed.get(key, [])
        orows, trows = orders.get(key, []), trades.get(key, [])
        xrows, arows = exits.get(key, []), closed_accounts.get(key, [])
        issues: set[str] = set()
        if len(crows) != 1:
            issues.add("duplicate_candidate_instance_rows")
        if len(mrows) > 1:
            issues.add("duplicate_missed_terminal_rows")
        terminal_orders = [
            row
            for row in orows
            if str(row.get("order_status") or "") in TERMINAL_ORDER_STATUSES
        ]
        if any(row.get("is_terminal_order_event") is not True for row in terminal_orders):
            issues.add("terminal_order_event_flag_missing")
        order_ids = {
            str(row.get("simulated_order_id") or "").strip() for row in orows
        }
        if "" in order_ids:
            issues.add("simulated_order_id_missing")
            order_ids.discard("")
        if len({
            (
                str(row.get("order_status") or ""),
                str(row.get("simulated_order_id") or ""),
                row.get("event_time_utc"),
            )
            for row in orows
        }) != len(orows):
            issues.add("duplicate_order_event_joins")

        disposition = ""
        if mrows:
            disposition = "missed"
            if orows or trows or xrows:
                issues.add("missed_terminal_overlaps_selected_flow")
            if not mrows[0]:
                issues.add("missed_terminal_outcome_missing")
        elif len(terminal_orders) != 1 or len(order_ids) != 1:
            issues.add("candidate_terminal_order_or_identity_count_not_one")
        else:
            terminal_order = terminal_orders[0]
            order_id = next(iter(order_ids))
            if str(terminal_order.get("simulated_order_id") or "") != order_id:
                issues.add("terminal_order_identity_mismatch")
            filled = terminal_order.get("order_status") == "filled"
            disposition = "trade" if filled else "terminal_unfilled"
            expected_counts = (1, 1, 1) if filled else (0, 1, 0)
            if (len(trows), len(xrows), len(arows)) != expected_counts:
                issues.add(
                    "filled_trade_exit_account_counts_invalid"
                    if filled
                    else "terminal_unfilled_trade_exit_account_counts_invalid"
                )
            trade_id = ""
            if len(trows) == 1:
                trade = trows[0]
                trade_id = str(trade.get("simulated_trade_id") or "").strip()
                if (
                    str(trade.get("simulated_order_id") or "") != order_id
                    or not trade_id
                    or not first_present(
                        trade.get("terminal_outcome"), trade.get("close_reason")
                    )
                ):
                    issues.add("filled_trade_identity_or_terminal_invalid")
            if len(xrows) == 1:
                exit_row = xrows[0]
                if (
                    str(exit_row.get("simulated_order_id") or "") != order_id
                    or not exit_row.get("terminal_outcome")
                    or not exit_row.get("close_reason")
                    or (
                        filled
                        and str(exit_row.get("simulated_trade_id") or "")
                        != trade_id
                    )
                ):
                    issues.add("exit_identity_or_terminal_invalid")
            if len(arows) == 1:
                account = arows[0]
                if (
                    str(account.get("simulated_order_id") or "") != order_id
                    or str(account.get("simulated_trade_id") or "") != trade_id
                ):
                    issues.add("filled_account_identity_invalid")
        if issues:
            for reason in issues:
                fail(reason, key)
        elif disposition:
            dispositions[key] = disposition

    if not candidate_keys:
        fail("candidate_population_empty", "candidate")
    terminal_keys = set(dispositions)
    candidate_minus_terminal = sorted(candidate_keys - terminal_keys)
    orphan_terminal_keys = set().union(*orphan_keys.values())
    disposition_counts = Counter(dispositions.values())
    exact = not failures and bool(candidate_keys) and candidate_keys == terminal_keys
    audit = {
        "schema": CANDIDATE_RELATIONAL_MATERIALIZATION_SCHEMA,
        "status": (
            "exact_candidate_equals_one_disjoint_terminal_disposition"
            if exact
            else "candidate_relational_materialization_mismatch"
        ),
        "exact": exact,
        "terminal_reconciliation_exact": exact,
        "graph": "research_timewarp",
        "production_parity": False,
        "pretrade_cost_role": "pretrade_expected_estimate_only",
        "post_lifecycle_cost_accounting_status": (
            "NOT_EVALUABLE_NOT_MATERIALIZED_BY_CURRENT_NATIVE_LEDGERS"
        ),
        "full_flow_economics_complete": False,
        "candidate_rows": int(row_counts["candidate"]),
        "candidate_unique_instance_keys": len(candidate_keys),
        "candidate_duplicate_instance_rows": sum(
            len(rows) - 1 for rows in candidates.values() if len(rows) > 1
        ),
        "missed_rows": int(row_counts["missed"]),
        "order_rows": int(row_counts["order"]),
        "trade_rows": int(row_counts["trade"]),
        "exit_rows": int(row_counts["exit"]),
        "account_rows": int(row_counts["account"]),
        "terminal_disposition_counts": {
            role: int(disposition_counts[role])
            for role in ("missed", "trade", "terminal_unfilled")
        },
        "terminal_disposition_unique_instance_keys": len(terminal_keys),
        "terminal_union_unique_instance_keys": len(terminal_keys),
        "missing_instance_key_counts": {
            role: int(missing_keys[role])
            for role in ("candidate", "missed", "order", "trade", "exit")
        },
        "orphan_candidate_instance_key_counts": {
            role: len(orphan_keys[role])
            for role in ("missed", "order", "trade", "exit")
        },
        "orphan_account_join_rows": orphan_account_rows,
        "candidate_minus_terminal_union_count": len(candidate_minus_terminal),
        "terminal_union_minus_candidate_count": len(orphan_terminal_keys),
        "candidate_minus_terminal_union_sample": candidate_minus_terminal[:8],
        "terminal_union_minus_candidate_sample": sorted(orphan_terminal_keys)[:8],
        "missed_order_overlap": len(set(missed) & set(orders)),
        "missed_trade_overlap": len(set(missed) & set(trades)),
        "order_trade_overlap": len(set(orders) & set(trades)),
        "failure_counts": dict(sorted(failures.items())),
        "failure_samples": {
            reason: sorted(identities)
            for reason, identities in sorted(samples.items())
        },
    }
    return audit, {"candidate": candidate_keys, "terminal": terminal_keys}


def materialized_candidate_rows_from_stats(
    stats: Iterable[Mapping[str, Any]],
) -> int:
    return sum(int(row.get("candidate_rows") or 0) for row in stats)


def compact_candidate_index_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Small candidate evidence rows for compact broad replay runs."""

    keep_fields = (
        "candidate_id",
        "decision_time_utc",
        "candle_close_utc",
        "source_candle_time_utc",
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
        "candidate_instance_identity_status",
        "decision_window_id",
        "candidate_set_id",
        "stable_decision_window_id",
        "symbol",
        "side",
        "direction",
        "framework",
        "current_framework",
        "route_family",
        "origin_family",
        "candidate_origin_family",
        "setup_family",
        "route_session",
        "session",
        "session_bucket",
        "authority_session",
        "trading_day",
        "utc_hour_bucket",
        "timeframe",
        "market_timeframe",
        "source_timeframe",
        "decision_timeframe",
        "selector_action",
        "selector_reason",
        "selector_action_origin",
        "selector_reason_origin",
        "effective_selector_action",
        "effective_selector_reason",
        "selector_action_materialized_from_scheduler",
        "entry_price",
        "current_price",
        "predecision_current_price",
        "predecision_current_price_source",
        "predecision_current_price_source_boundary",
        "predecision_current_price_source_time_utc",
        "stop_loss",
        "take_profit_1",
        "target_price",
        "dynamic_geometry_policy",
        "dynamic_execution_policy_id",
        "expected_net_r",
        "candidate_expected_net_r",
        "selected_policy_expected_net_r",
        "selected_policy_for_expected_net_r",
        "selected_policy_expected_net_calibration_status",
        "selected_policy_expected_net_r_calibration_status",
        "selected_policy_expected_net_calibrated",
        "selected_policy_expected_net_calibration_required",
        "selected_policy_expected_net_calibration_source",
        "selected_policy_expected_net_calibration_source_boundary",
        "selected_policy_expected_net_calibration_boundary",
        "selected_policy_expected_net_assumption_hash",
        "selected_policy_expected_net_r_assumption_hash",
        "selected_policy_expected_net_calibration_hash",
        "probability",
        "candidate_probability",
        "confidence",
        "candidate_confidence",
        "candidate_decision_quality",
        "candidate_decision_quality_field_sources",
        "candidate_decision_quality_source_boundary",
        "candidate_decision_quality_alias_status",
        "candidate_decision_quality_optional_provenance_warnings",
        "confidence_missing_degraded_default_applied",
        "scheduler_candidate_decision_quality_optional_provenance_warnings",
        "scheduler_confidence_missing_degraded_default_applied",
        "fill_probability",
        "candidate_fill_probability",
        "source_completeness",
        "source_completeness_status",
        "candidate_ev_r",
        "ev_r",
        "cost_r",
        "expected_cost_r",
        "broker_pretrade_cost_r",
        "broker_calibrated_expected_cost_r",
        "broker_pretrade_cost_non_executable_diagnostic_expected_cost_r",
        "total_execution_cost_r",
        "candidate_decision_quality",
        "candidate_decision_quality_alias_status",
        "candidate_decision_quality_field_sources",
        "candidate_decision_quality_source_boundary",
        "source_boundary",
        "pretrade_cost_packet_status",
        "pretrade_cost_status",
        "pretrade_cost_refusal_reasons",
        "cost_source_gap_status",
        "cost_authority",
        "execution_cost_authority",
        "candidate_cost_r_fallback_is_authority",
        "ultimate_candidate_package_open_reduced_risk_authority",
        "package_open_reduced_authority_allowed",
        "package_open_reduced_authority_family",
        "ultimate_package_open_reduced_authority_allowed",
        "ultimate_candidate_package_reduce_risk_authority",
        "package_reduce_risk_authority_allowed",
        "package_reduce_risk_authority_family",
        "package_new_entry_authority_required",
        "package_new_entry_authority_valid",
        "package_new_entry_authority_status",
        "package_new_entry_authority_failures",
        "package_new_entry_authority_hash_sha256",
        "expected_package_new_entry_authority_hash_sha256",
        "package_new_entry_authority_payload_schema",
        "package_new_entry_authority_scope",
        "package_new_entry_authority_target_action_intent",
        "package_new_entry_authority_authority_field",
        "package_new_entry_authority_authority_family",
        "package_new_entry_authority_source_boundary",
        "package_new_entry_authority_uses_outcome_fields",
        "package_new_entry_authority_selector_action",
        "package_new_entry_authority_selector_reason",
        *PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
        "predecision_stop_hazard_guard_status",
        "predecision_stop_hazard_guard_reason",
        "predecision_stop_hazard_guard_action",
        "predecision_stop_hazard_guard_risk_cap_applied",
        "predecision_stop_hazard_guard_risk_cap_pct",
        "predecision_stop_hazard_guard_score_penalty",
        "predecision_stop_hazard_guard_unit_risk_atr",
        "predecision_stop_hazard_guard_unit_risk",
        "predecision_stop_hazard_guard_atr14",
        "predecision_stop_hazard_guard_distance_to_limit_risk",
        "predecision_stop_hazard_guard_distance_to_limit_atr",
        "predecision_stop_hazard_guard_limit_fill_probability",
        "predecision_stop_hazard_guard_target_r",
        "predecision_stop_hazard_guard_target_r_source",
        "predecision_stop_hazard_guard_min_unit_risk_atr",
        "predecision_stop_hazard_guard_max_distance_to_limit_risk",
        "predecision_stop_hazard_guard_min_limit_fill_probability",
        "predecision_stop_hazard_guard_min_target_r",
        "predecision_stop_hazard_guard_pressure_enabled",
        "predecision_stop_hazard_guard_pressure_min_score",
        "predecision_stop_hazard_guard_pressure_score",
        "predecision_stop_hazard_guard_pressure_triggered",
        "predecision_stop_hazard_guard_pressure_components",
        "predecision_stop_hazard_guard_pressure_required_conditions",
        "predecision_stop_hazard_guard_pressure_triggered_conditions",
        "predecision_stop_hazard_guard_pressure_missing_fields",
        "predecision_stop_hazard_guard_require_all_thresholds",
        "predecision_stop_hazard_guard_triggered_conditions",
        "predecision_stop_hazard_guard_missing_fields",
        "predecision_stop_hazard_guard_source_boundary",
        "predecision_stop_hazard_guard_outcome_fields_used",
        "package_replay_candidate_use_allowed",
        "package_replay_executable_candidate_use_allowed",
        "package_replay_executable_candidate_use_allowed_reason",
        "replay_candidate_use_allowed_now",
        "replay_candidate_use_allowed_now_reason",
        "source_bound_package_candidate_use_allowed",
        "ultimate_package_source_bound_candidate_use_allowed",
        "ultimate_package_effective_source_bound_candidate_use_allowed",
        "ultimate_package_effective_source_bound_signal_r",
        "ultimate_package_effective_admission_count",
        "ultimate_package_effective_matched_count",
        "ultimate_package_admission_candidate_use_allowed",
        "ultimate_package_admission_sleeve_match_count",
        "ultimate_package_matched_sleeve_count",
        "ultimate_package_role_disposition",
        "scheduler_materialization_status",
        "scheduler_materialization_skip_reason",
        "scheduler_materialization_override_reason",
        "scheduler_materialization_lifecycle_action_resolution_required",
        "scheduler_materialization_replay_lifecycle_action_resolver_enabled",
        "scheduler_materialization_replay_lifecycle_action_resolver_applied",
        "scheduler_materialization_replay_lifecycle_action_resolver_reason",
        "scheduler_materialization_replay_lifecycle_action_resolver_failures",
        "scheduler_materialization_replay_lifecycle_action_resolver_original_action_intent",
        "scheduler_materialization_replay_lifecycle_action_resolver_resolved_action_intent",
        "scheduler_materialization_replay_lifecycle_action_resolver_authority_source",
        "same_symbol_replay_exposure_context",
        "same_symbol_replay_exposure_context_source",
        "same_symbol_replay_exposure_context_status",
        "same_symbol_replay_exposure_context_synthesized_empty",
        "canonical_replay_context_envelope",
        "canonical_replay_context_envelope_hash_sha256",
        "canonical_replay_context_envelope_shape_hash_sha256",
        "canonical_replay_context_source_boundary",
        "canonical_replay_context_projection_status",
        "same_symbol_lifecycle_exposure_risk_pct",
        "same_side_pending_ids",
        "same_side_pending_order_ids",
        "opposite_pending_ids",
        "opposite_pending_order_ids",
        "same_side_pending_risk_pct",
        "opposite_pending_risk_pct",
        "source_required_lifecycle_origin",
        "source_required_lifecycle_origin_reason",
        "scheduler_materialization_selector_action",
        "scheduler_materialization_selector_reason",
        "scheduler_materialization_action_intent",
        "selected_candidate_id",
        "selected_candidate_ids",
        "scheduler_quality_backfill_status",
        "scheduler_candidate_decision_inputs",
        "scheduler_expected_net_r",
        "scheduler_probability",
        "scheduler_confidence",
        "scheduler_fill_probability",
        "scheduler_source_completeness",
        "scheduler_source_completeness_status",
        "candidate_scheduler_quality_parity_status",
        "candidate_scheduler_quality_parity_mismatches",
        "scheduler_score",
        "scheduler_rank",
        "scheduler_option_status",
        "scheduler_option_reason",
        "scheduler_action_class",
        "replacement_reallocation_quality",
        "replacement_reallocation_quality_score",
        "replacement_reallocation_quality_eligible",
        "replacement_reallocation_quality_hard_gate_failures",
        "replacement_release_quality_score",
        "replacement_release_bonus",
        "replacement_reallocation_base_expected_transfer_score",
        "replacement_reallocation_stop_hazard_status",
        "replacement_reallocation_stop_hazard_quality_penalty",
        "replacement_reallocation_usable_release_candidate_count",
        "replacement_reallocation_selected_release_pending_id",
        "replacement_reallocation_selected_release_reason",
        "replacement_reallocation_used_pending_id_count",
        "replacement_reallocation_quality_source_boundary",
        "replacement_reallocation_quality_uses_outcome_fields",
        "replacement_reallocation_quality_projection_status",
        "pending_replacement_release_candidate_count",
        "selected_scheduler_replacement_reallocation_quality",
        "selected_scheduler_replacement_reallocation_quality_score",
        "selected_scheduler_replacement_reallocation_quality_eligible",
        "selected_scheduler_replacement_reallocation_quality_hard_gate_failures",
        "selected_scheduler_replacement_release_quality_score",
        "selected_scheduler_replacement_release_bonus",
        "selected_scheduler_replacement_reallocation_base_expected_transfer_score",
        "selected_scheduler_replacement_reallocation_stop_hazard_status",
        "selected_scheduler_replacement_reallocation_stop_hazard_quality_penalty",
        "selected_scheduler_replacement_reallocation_usable_release_candidate_count",
        "selected_scheduler_replacement_reallocation_selected_release_pending_id",
        "selected_scheduler_replacement_reallocation_selected_release_reason",
        "selected_scheduler_replacement_reallocation_used_pending_id_count",
        "selected_scheduler_replacement_reallocation_quality_source_boundary",
        "selected_scheduler_replacement_reallocation_quality_uses_outcome_fields",
        "selected_scheduler_replacement_reallocation_quality_projection_status",
        "selected_scheduler_pending_replacement_release_candidate_count",
        "selected_scheduler_options_by_candidate_id",
        "selected_scheduler_options_by_candidate_instance_key",
        "selected_scheduler_options_by_candidate_id_lookup_status",
        *SIGNED_SOFT_TRANSFER_DISPLACEMENT_TRACE_KEYS,
        "risk_authority",
        "risk_authority_status",
        "scheduler_approved_risk_pct",
        "risk_authority_packet_hash_sha256",
        "risk_config_source",
        "risk_per_trade_pct",
        "selected_cell_risk_pct",
        "packet_sidecar_id",
        "packet_sidecar_hash_sha256",
        "full_packet_sidecar_status",
        "evidence_class",
    )
    compact_rows: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        compact = {key: row.get(key) for key in keep_fields if key in row}
        risk_pre = row.get("risk_authority_pre_scheduler")
        risk_pre = risk_pre if isinstance(risk_pre, Mapping) else {}
        compact.update(
            canonical_replay_candidate_instance_fields(
                row,
                decision_time_utc=row.get("decision_time_utc"),
            )
        )
        alias_fields = ledger_namespace_alias_fields(
            row,
            decision_time_utc=row.get("decision_time_utc"),
        )
        for key, value in alias_fields.items():
            if compact.get(key) in (None, "", [], {}):
                compact[key] = value
        preserve_replay_truth_projection(
            compact,
            row,
            selected_scheduler_alias=bool(row.get("scheduler_final_selected")),
        )
        # The compact index is the authoritative candidate proof surface when
        # the full packet ledger is omitted. Keep the same atomic POI state and
        # lifecycle lineage that terminal compact rows already preserve.
        compact.update(candidate_poi_state_ledger_fields(row))
        stop_hazard_candidate_index_fields = (
            "predecision_stop_hazard_guard_status",
            "predecision_stop_hazard_guard_reason",
            "predecision_stop_hazard_guard_action",
            "predecision_stop_hazard_guard_risk_cap_applied",
            "predecision_stop_hazard_guard_risk_cap_pct",
            "predecision_stop_hazard_guard_score_penalty",
            "predecision_stop_hazard_guard_unit_risk_atr",
            "predecision_stop_hazard_guard_unit_risk",
            "predecision_stop_hazard_guard_atr14",
            "predecision_stop_hazard_guard_distance_to_limit_risk",
            "predecision_stop_hazard_guard_distance_to_limit_atr",
            "predecision_stop_hazard_guard_limit_fill_probability",
            "predecision_stop_hazard_guard_target_r",
            "predecision_stop_hazard_guard_target_r_source",
            "predecision_stop_hazard_guard_min_unit_risk_atr",
            "predecision_stop_hazard_guard_max_distance_to_limit_risk",
            "predecision_stop_hazard_guard_min_limit_fill_probability",
            "predecision_stop_hazard_guard_min_target_r",
            "predecision_stop_hazard_guard_pressure_enabled",
            "predecision_stop_hazard_guard_pressure_min_score",
            "predecision_stop_hazard_guard_pressure_score",
            "predecision_stop_hazard_guard_pressure_triggered",
            "predecision_stop_hazard_guard_pressure_components",
            "predecision_stop_hazard_guard_pressure_required_conditions",
            "predecision_stop_hazard_guard_pressure_triggered_conditions",
            "predecision_stop_hazard_guard_pressure_missing_fields",
            "predecision_stop_hazard_guard_require_all_thresholds",
            "predecision_stop_hazard_guard_triggered_conditions",
            "predecision_stop_hazard_guard_missing_fields",
            "predecision_stop_hazard_guard_source_boundary",
            "predecision_stop_hazard_guard_outcome_fields_used",
        )
        scheduler_inputs = row.get("scheduler_candidate_decision_inputs")
        scheduler_inputs = scheduler_inputs if isinstance(scheduler_inputs, Mapping) else {}
        selected_scheduler_inputs = row.get("selected_scheduler_decision_inputs")
        selected_scheduler_inputs = (
            selected_scheduler_inputs
            if isinstance(selected_scheduler_inputs, Mapping)
            else {}
        )
        for source in (scheduler_inputs, selected_scheduler_inputs):
            for key in stop_hazard_candidate_index_fields:
                if compact.get(key) in (None, "", [], {}) and source.get(key) not in (
                    None,
                    "",
                    [],
                    {},
                ):
                    compact[key] = source.get(key)
        ladder_selected_cell_risk_pct = risk_expression_ladder_scalar(
            compact,
            (
                "selected_cell_risk_pct",
                "package_risk_expression_selected_cell_risk_pct_before",
                "requested_risk_pct",
            ),
        )
        ladder_scheduler_approved_risk_pct = risk_expression_ladder_scalar(
            compact,
            (
                "approved_risk_pct",
                "runtime_final_risk_pct",
                "package_risk_expression_scheduler_approved_risk_pct_before",
            ),
        )
        selected_cell_risk_pct, _selected_cell_risk_pct_source = first_quality_value(
            compact,
            (
                "selected_cell_risk_pct",
                "risk_per_trade_pct",
                "requested_risk_pct",
                "runtime_final_risk_pct",
                "approved_risk_pct",
                "scheduler_approved_risk_pct",
            ),
        )
        if quality_value_missing(selected_cell_risk_pct):
            selected_cell_risk_pct, _selected_cell_risk_pct_source = (
                first_quality_value(
                    risk_pre,
                    (
                        "selected_cell_risk_pct",
                        "risk_per_trade_pct",
                        "requested_risk_pct",
                        "runtime_final_risk_pct",
                        "approved_risk_pct",
                        "scheduler_approved_risk_pct",
                    ),
                )
            )
        if quality_value_missing(selected_cell_risk_pct):
            selected_cell_risk_pct, _selected_cell_risk_pct_source = (
                first_quality_value(
                    row,
                    (
                        "selected_cell_risk_pct",
                        "risk_per_trade_pct",
                        "requested_risk_pct",
                        "runtime_final_risk_pct",
                        "approved_risk_pct",
                        "scheduler_approved_risk_pct",
                    ),
                )
            )
        if quality_value_missing(selected_cell_risk_pct):
            selected_cell_risk_pct = ladder_selected_cell_risk_pct
        scheduler_approved_risk_pct = (
            compact.get("scheduler_approved_risk_pct")
            if compact.get("scheduler_approved_risk_pct") is not None
            else row.get("approved_risk_pct")
            if row.get("approved_risk_pct") is not None
            else row.get("risk_delta_pct")
            if row.get("risk_delta_pct") is not None
            else ladder_scheduler_approved_risk_pct
            if ladder_scheduler_approved_risk_pct is not None
            else 0.0
        )
        risk_pct_basis = first_quality_value(
            compact,
            (
                "risk_pct_basis",
                "risk_reduction_basis_pct",
                "selected_cell_risk_pct",
                "scheduler_approved_risk_pct",
            ),
        )[0]
        if quality_value_missing(risk_pct_basis):
            basis_candidates = [
                safe_float(selected_cell_risk_pct, 0.0),
                safe_float(scheduler_approved_risk_pct, 0.0),
            ]
            risk_pct_basis = max(basis_candidates)
        risk_pct_provenance = compact.get("risk_pct_provenance")
        if quality_value_missing(risk_pct_provenance):
            risk_pct_provenance = {
                "selected_cell_risk_pct": selected_cell_risk_pct,
                "scheduler_approved_risk_pct": scheduler_approved_risk_pct,
                "runtime_final_risk_pct": compact.get("runtime_final_risk_pct"),
                "risk_reduction_basis_pct": compact.get("risk_reduction_basis_pct"),
                "source": "compact_broad_replay_candidate_index",
            }
        compact.update(
            {
                "candidate_index_schema": "compact_broad_replay_candidate_index_v1",
                "risk_authority": (
                    compact.get("risk_authority")
                    or risk_pre.get("schema_version")
                ),
                "risk_authority_status": (
                    compact.get("risk_authority_status")
                    or (
                        "pre_scheduler_risk_authority_materialized"
                        if risk_pre
                        else "pre_scheduler_risk_authority_missing"
                    )
                ),
                "risk_authority_packet_hash_sha256": (
                    compact.get("risk_authority_packet_hash_sha256")
                    or risk_pre.get("packet_hash_sha256")
                ),
                "risk_config_source": (
                    compact.get("risk_config_source")
                    or risk_pre.get("risk_config_source")
                ),
                "risk_per_trade_pct": (
                    compact.get("risk_per_trade_pct")
                    or risk_pre.get("risk_per_trade_pct")
                    or row.get("risk_per_trade_pct")
                    or selected_cell_risk_pct
                ),
                "selected_cell_risk_pct": selected_cell_risk_pct,
                "scheduler_approved_risk_pct": scheduler_approved_risk_pct,
                "risk_pct_basis": risk_pct_basis,
                "risk_pct_basis_source": compact.get("risk_pct_basis_source")
                or "compact_selected_scheduler_risk_pct",
                "risk_pct_final_source": compact.get("risk_pct_final_source")
                or "compact_scheduler_approved_risk_pct",
                "risk_pct_provenance": risk_pct_provenance,
                "candidate_packet_sidecar_payload_omitted": True,
                "candidate_index_lossless_candidate_payload": False,
            }
        )
        if compact.get("source_boundary") in (None, "", [], {}):
            compact["source_boundary"] = (
                row.get("source_boundary")
                or compact.get("candidate_decision_quality_source_boundary")
                or row.get("candidate_decision_quality_source_boundary")
            )
        if not isinstance(compact.get("candidate_decision_quality"), Mapping):
            compact_quality = candidate_decision_quality_envelope(compact)
            if compact_quality:
                compact["candidate_decision_quality"] = compact_quality
        if (
            compact.get("scheduler_quality_backfill_status")
            == "scheduler_option_missing_for_candidate"
            and compact.get("candidate_scheduler_quality_parity_status")
            in (None, "", [], {})
        ):
            compact["candidate_scheduler_quality_parity_status"] = (
                "not_applicable_scheduler_option_missing"
            )
            compact["candidate_scheduler_quality_parity_mismatches"] = []
        normalize_replay_quality_fields(compact, row_type="candidate_index")
        compact_rows.append(compact)
    return compact_rows


def compact_missed_opportunity_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Scoreable missed-opportunity rows without bulky candidate packet payloads."""

    keep_fields = (
        "candidate_id",
        "decision_time_utc",
        "candle_close_utc",
        "source_candle_time_utc",
        "canonical_replay_candidate_instance_key",
        "risk_finalizer_probe_instance_key",
        "source_bound_replay_candidate_instance_key",
        "candidate_instance_identity_status",
        "decision_window_id",
        "candidate_set_id",
        "stable_decision_window_id",
        "symbol",
        "side",
        "direction",
        "framework",
        "current_framework",
        "route_family",
        "origin_family",
        "candidate_origin_family",
        "setup_family",
        "route_session",
        "session",
        "session_bucket",
        "authority_session",
        "trading_day",
        "utc_hour_bucket",
        "decision_timeframe",
        "market_timeframe",
        "timeframe",
        "source_timeframe",
        "selector_action",
        "selector_reason",
        "selector_action_origin",
        "selector_reason_origin",
        "effective_selector_action",
        "effective_selector_reason",
        "risk_decision",
        "risk_decision_reason",
        "selected_action",
        "lifecycle_action",
        "same_symbol_lifecycle_action",
        "risk_lifecycle_action",
        "scheduler_lifecycle_action",
        "candidate_lifecycle_action",
        "risk_reconciled_lifecycle_action",
        "selected_candidate_id",
        "selected_candidate_ids",
        "scheduler_final_selected",
        "scheduler_pre_finalizer_selected",
        "scheduler_selection_disposition",
        "scheduler_rank",
        "scheduler_score",
        "scheduler_action_class",
        "scheduler_materialization_status",
        "scheduler_materialization_skip_reason",
        "scheduler_materialization_override_reason",
        "scheduler_materialization_action_intent",
        "scheduler_materialization_lifecycle_action_resolution_required",
        "scheduler_materialization_replay_lifecycle_action_resolver_enabled",
        "scheduler_materialization_replay_lifecycle_action_resolver_applied",
        "scheduler_materialization_replay_lifecycle_action_resolver_reason",
        "scheduler_materialization_replay_lifecycle_action_resolver_failures",
        "scheduler_materialization_replay_lifecycle_action_resolver_original_action_intent",
        "scheduler_materialization_replay_lifecycle_action_resolver_resolved_action_intent",
        "scheduler_materialization_replay_lifecycle_action_resolver_authority_source",
        "same_symbol_replay_exposure_context",
        "same_symbol_replay_exposure_context_source",
        "same_symbol_replay_exposure_context_status",
        "same_symbol_replay_exposure_context_synthesized_empty",
        "canonical_replay_context_envelope",
        "canonical_replay_context_envelope_hash_sha256",
        "canonical_replay_context_envelope_shape_hash_sha256",
        "canonical_replay_context_source_boundary",
        "canonical_replay_context_projection_status",
        "same_symbol_lifecycle_exposure_risk_pct",
        "same_side_pending_ids",
        "same_side_pending_order_ids",
        "opposite_pending_ids",
        "opposite_pending_order_ids",
        "same_side_pending_risk_pct",
        "opposite_pending_risk_pct",
        "scheduler_materialization_selector_action",
        "scheduler_materialization_selector_reason",
        "scheduler_option_status",
        "scheduler_option_reason",
        "scheduler_option_runtime_eligible",
        "scheduler_option_primary_runtime_ineligible_reason",
        "scheduler_option_primary_runtime_ineligible_family",
        "scheduler_option_vetoes",
        "scheduler_option_selector_reduce_risk_hard_block_reason",
        "scheduler_option_selector_reduce_risk_quality_failures",
        "scheduler_option_dynamic_budget_quality_failures",
        "risk_finalizer_selected",
        "risk_finalizer_decision",
        "risk_finalizer_reason",
        "risk_finalizer_rank",
        "risk_finalizer_scheduler_score",
        "risk_finalizer_dynamic_budget_status",
        "risk_finalizer_scheduler_option_status",
        "risk_finalizer_scheduler_option_runtime_eligible",
        "risk_finalizer_scheduler_option_primary_runtime_ineligible_reason",
        "risk_finalizer_scheduler_option_vetoes",
        "risk_finalizer_top_probe_reasons",
        "risk_finalizer_executable_finalized",
        "risk_finalizer_package_replay_executable_candidate_use_allowed",
        "risk_finalizer_package_replay_executable_candidate_use_allowed_reason",
        "scheduler_option_package_fill_floor_authority_allowed",
        "scheduler_option_package_fill_floor_authority_failures",
        "scheduler_option_package_fill_floor_authority_raw_failures",
        "scheduler_option_package_fill_floor_authority_resolved_failures",
        "scheduler_option_package_fill_floor_authority_unresolved_failures",
        "pre_risk_finalizer_scheduler_option_package_fill_floor_authority_allowed",
        "pre_risk_finalizer_scheduler_option_package_fill_floor_authority_failures",
        "pre_risk_finalizer_scheduler_option_package_fill_floor_authority_raw_failures",
        "pre_risk_finalizer_scheduler_option_package_fill_floor_authority_resolved_failures",
        "pre_risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_allowed",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_failures",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_raw_failures",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_resolved_failures",
        "risk_finalizer_scheduler_option_package_fill_floor_authority_unresolved_failures",
        "finalizer_primary_probe_scheduler_option_package_fill_floor_authority_allowed",
        "finalizer_primary_probe_scheduler_option_package_fill_floor_authority_failures",
        "finalizer_primary_probe_scheduler_option_package_fill_floor_authority_raw_failures",
        "finalizer_primary_probe_scheduler_option_package_fill_floor_authority_resolved_failures",
        "finalizer_primary_probe_scheduler_option_package_fill_floor_authority_unresolved_failures",
        *SIGNED_SOFT_TRANSFER_DISPLACEMENT_TRACE_KEYS,
        "risk_authority_status",
        "risk_authority_packet_hash_sha256",
        "risk_config_source",
        "risk_per_trade_pct",
        "selected_cell_risk_pct",
        "scheduler_approved_risk_pct",
        "scheduler_approved_risk_pct_status",
        "replacement_reallocation_quality",
        "replacement_reallocation_quality_score",
        "replacement_reallocation_quality_eligible",
        "replacement_reallocation_quality_hard_gate_failures",
        "replacement_release_quality_score",
        "replacement_release_bonus",
        "replacement_reallocation_base_expected_transfer_score",
        "replacement_reallocation_stop_hazard_status",
        "replacement_reallocation_stop_hazard_quality_penalty",
        "replacement_reallocation_usable_release_candidate_count",
        "replacement_reallocation_selected_release_pending_id",
        "replacement_reallocation_selected_release_reason",
        "replacement_reallocation_used_pending_id_count",
        "replacement_reallocation_quality_source_boundary",
        "replacement_reallocation_quality_uses_outcome_fields",
        "replacement_reallocation_quality_projection_status",
        "pending_replacement_release_candidate_count",
        "selected_scheduler_replacement_reallocation_quality",
        "selected_scheduler_replacement_reallocation_quality_score",
        "selected_scheduler_replacement_reallocation_quality_eligible",
        "selected_scheduler_replacement_reallocation_quality_hard_gate_failures",
        "selected_scheduler_replacement_release_quality_score",
        "selected_scheduler_replacement_release_bonus",
        "selected_scheduler_replacement_reallocation_base_expected_transfer_score",
        "selected_scheduler_replacement_reallocation_stop_hazard_status",
        "selected_scheduler_replacement_reallocation_stop_hazard_quality_penalty",
        "selected_scheduler_replacement_reallocation_usable_release_candidate_count",
        "selected_scheduler_replacement_reallocation_selected_release_pending_id",
        "selected_scheduler_replacement_reallocation_selected_release_reason",
        "selected_scheduler_replacement_reallocation_used_pending_id_count",
        "selected_scheduler_replacement_reallocation_quality_source_boundary",
        "selected_scheduler_replacement_reallocation_quality_uses_outcome_fields",
        "selected_scheduler_replacement_reallocation_quality_projection_status",
        "selected_scheduler_pending_replacement_release_candidate_count",
        "selected_scheduler_options_by_candidate_id",
        "selected_scheduler_options_by_candidate_instance_key",
        "selected_scheduler_options_by_candidate_id_lookup_status",
        "entry_price",
        "current_price",
        "predecision_current_price",
        "predecision_current_price_source",
        "predecision_current_price_source_boundary",
        "predecision_current_price_source_time_utc",
        "stop_loss",
        "take_profit_1",
        "target_price",
        "dynamic_geometry_policy",
        "dynamic_execution_policy_id",
        "expected_net_r",
        "candidate_expected_net_r",
        "selected_policy_expected_net_r",
        "selected_policy_for_expected_net_r",
        "selected_policy_expected_net_calibration_status",
        "selected_policy_expected_net_r_calibration_status",
        "selected_policy_expected_net_calibrated",
        "selected_policy_expected_net_calibration_required",
        "selected_policy_expected_net_calibration_source",
        "selected_policy_expected_net_calibration_source_boundary",
        "selected_policy_expected_net_calibration_boundary",
        "selected_policy_expected_net_assumption_hash",
        "selected_policy_expected_net_r_assumption_hash",
        "selected_policy_expected_net_calibration_hash",
        "selected_policy_exit_assumption_hash",
        "expected_net_r_exit_assumption_hash",
        "probability",
        "candidate_probability",
        "confidence",
        "candidate_confidence",
        "candidate_decision_quality",
        "candidate_decision_quality_field_sources",
        "candidate_decision_quality_source_boundary",
        "candidate_decision_quality_alias_status",
        "candidate_decision_quality_optional_provenance_warnings",
        "confidence_missing_degraded_default_applied",
        "scheduler_candidate_decision_quality_optional_provenance_warnings",
        "scheduler_confidence_missing_degraded_default_applied",
        "fill_probability",
        "candidate_fill_probability",
        "source_completeness",
        "source_completeness_status",
        "candidate_ev_r",
        "ev_r",
        "expectancy_r",
        "counterfactual_fill_probability",
        "counterfactual_source_completeness",
        "counterfactual_order_fill_status",
        "counterfactual_order_terminal_outcome",
        "counterfactual_order_close_mark_r",
        "counterfactual_order_close_mark_source",
        "counterfactual_order_close_time_utc",
        "order_status",
        "order_execution_path",
        "primary_order_type",
        "effective_order_type",
        "effective_order_type_status",
        "limit_first_fill_status",
        "limit_first_terminal_outcome",
        "limit_first_close_mark_r",
        "limit_first_close_mark_source",
        "guarded_market_fallback_status",
        "guarded_market_fallback_reason",
        "guarded_market_fallback_applied",
        "guarded_market_fallback_attempted",
        "guarded_market_fallback_configured",
        "guarded_market_fallback_extra_cost_r",
        "package_marketable_entry_guard_status",
        "package_marketable_entry_guard_reason",
        "package_marketable_entry_guard_original_reason",
        "limit_marketable_at_decision",
        "predecision_limit_fillability",
        "predecision_passive_limit_too_close_guard_status",
        "predecision_passive_limit_too_close_guard_reason",
        "predecision_passive_limit_too_close_guard_action",
        "predecision_passive_limit_too_close_guard_risk_cap_applied",
        "predecision_passive_limit_too_close_guard_risk_cap_pct",
        "predecision_passive_limit_too_close_guard_distance_to_limit_risk",
        "predecision_passive_limit_too_close_guard_distance_to_limit_atr",
        "predecision_passive_limit_too_close_guard_limit_fill_probability",
        "predecision_passive_limit_too_close_guard_min_distance_to_limit_risk",
        "predecision_passive_limit_too_close_guard_min_distance_to_limit_atr",
        "predecision_passive_limit_too_close_guard_max_limit_fill_probability",
        "predecision_passive_limit_too_close_guard_require_all_thresholds",
        "predecision_passive_limit_too_close_guard_triggered_conditions",
        "predecision_passive_limit_too_close_guard_missing_fields",
        "predecision_passive_limit_too_close_guard_source_boundary",
        "predecision_passive_limit_too_close_guard_outcome_fields_used",
        "predecision_stop_hazard_guard_status",
        "predecision_stop_hazard_guard_reason",
        "predecision_stop_hazard_guard_action",
        "predecision_stop_hazard_guard_risk_cap_applied",
        "predecision_stop_hazard_guard_risk_cap_pct",
        "predecision_stop_hazard_guard_score_penalty",
        "predecision_stop_hazard_guard_unit_risk_atr",
        "predecision_stop_hazard_guard_unit_risk",
        "predecision_stop_hazard_guard_atr14",
        "predecision_stop_hazard_guard_distance_to_limit_risk",
        "predecision_stop_hazard_guard_distance_to_limit_atr",
        "predecision_stop_hazard_guard_limit_fill_probability",
        "predecision_stop_hazard_guard_target_r",
        "predecision_stop_hazard_guard_min_unit_risk_atr",
        "predecision_stop_hazard_guard_max_distance_to_limit_risk",
        "predecision_stop_hazard_guard_min_limit_fill_probability",
        "predecision_stop_hazard_guard_require_all_thresholds",
        "predecision_stop_hazard_guard_triggered_conditions",
        "predecision_stop_hazard_guard_missing_fields",
        "predecision_stop_hazard_guard_source_boundary",
        "predecision_stop_hazard_guard_outcome_fields_used",
        "passive_limit_too_close_guard_status",
        "passive_limit_too_close_guard_reasons",
        "passive_limit_too_close_guard_required_conditions",
        "passive_limit_too_close_guard_missing_fields",
        "passive_limit_too_close_guard_require_all_thresholds",
        "passive_limit_too_close_guard_missing_fields_action",
        "passive_limit_queue_route_available",
        "passive_limit_queue_route_enabled",
        "passive_limit_fallback_envelope_required",
        "passive_limit_fallback_envelope_applies",
        "passive_limit_fallback_envelope_status",
        "passive_limit_fallback_envelope_reason",
        "passive_limit_fallback_envelope_reasons",
        "passive_limit_fallback_envelope_degraded_to_passive_queue",
        "passive_limit_fallback_envelope_passive_queue_release_reason",
        "passive_limit_fallback_envelope_degraded_rank_class",
        "passive_limit_fallback_envelope_degraded_extra_slot_candidate",
        "passive_limit_fallback_envelope_degraded_rank_penalty",
        "passive_limit_fallback_envelope_degraded_transfer_score",
        "passive_limit_fallback_envelope_min_degraded_transfer_score",
        "passive_limit_fallback_envelope_unusable_guarded_fallback_reasons",
        "passive_limit_fallback_envelope_used_only_predecision_fields",
        "passive_limit_fallback_envelope_guarded_market_route_available",
        "passive_limit_fallback_envelope_distance_to_limit_risk",
        "passive_limit_fallback_envelope_distance_to_limit_atr",
        "passive_limit_fallback_envelope_limit_fill_probability",
        "passive_limit_fallback_envelope_max_limit_fill_probability_for_fallback",
        "passive_limit_fallback_envelope_max_adverse_entry_drift_r",
        "passive_limit_fallback_envelope_expected_net_r",
        "passive_limit_fallback_envelope_expected_net_r_after_guarded_fallback_cost",
        "passive_limit_fallback_envelope_min_expected_net_r_after_guarded_fallback_cost",
        "passive_limit_fallback_envelope_source_completeness",
        "passive_limit_fallback_envelope_min_source_completeness",
        "passive_limit_fallback_envelope_candidate_probability",
        "passive_limit_fallback_envelope_min_candidate_probability",
        "passive_limit_fallback_envelope_fallback_time_utc",
        "passive_limit_fallback_envelope_expiry_utc",
        "passive_limit_fallback_envelope_source_boundary",
        "passive_limit_fallback_envelope_blocked",
        "passive_limit_fallback_envelope_block_reason",
        "passive_limit_fallback_envelope_block_reasons",
        "replay_order_fillability_policy_v1",
        "order_intent_materialized",
        "order_intent_materialization_status",
        "order_intent_materialization_reason",
        "pending_lifecycle_materialized",
        "accepted_risk_budget_materialized",
        "entry_fill_executable",
        "entry_fill_authority_status",
        "entry_fill_authority_reason",
        "entry_fill_authority_source_boundary",
        "terminal_r_scoreable",
        "terminal_r_scoreability_status",
        "terminal_r_scoreability_reason",
        "terminal_r_diagnostic_outcome",
        "terminal_r_diagnostic_gross_r",
        "terminal_r_diagnostic_close_reason",
        "terminal_r_diagnostic_target_r",
        "terminal_r_diagnostic_only",
        "accepted_risk_reservation_released",
        "accepted_risk_budget_consumed_by_fill",
        "accepted_risk_reservation_transition",
        "released_risk_pct",
        "fill_realism_class",
        "fill_realism_executable",
        "fill_realism_reason",
        "fill_realism_source_boundary",
        "fill_realism_queue_model",
        "fill_realism_diagnostic_fill_status",
        "fill_realism_diagnostic_fill_time_utc",
        "fill_realism_diagnostic_fill_price",
        "fill_realism_diagnostic_terminal_outcome",
        "entry_first_touch_utc",
        "passive_limit_queue_touch_count",
        "passive_limit_queue_max_penetration_price",
        "passive_limit_queue_max_penetration_r",
        "passive_limit_queue_penetrated_beyond_limit",
        "passive_limit_queue_realism_required",
        "passive_limit_queue_realism_min_penetration_r",
        "passive_limit_queue_realism_min_touch_count",
        "passive_limit_queue_realism_passed",
        "ambiguity_resolution",
        "fill_status",
        "terminal_outcome",
        "opportunity_close_reason",
        "raw_opportunity_close_reason",
        "opportunity_path_scored",
        "opportunity_gross_r",
        "opportunity_net_proxy_r",
        "raw_gross_r",
        "gross_r",
        "policy_gross_r",
        "raw_net_proxy_r",
        "net_proxy_r",
        "raw_target_r",
        "policy_target_r",
        "cost_r",
        "expected_cost_r",
        "broker_pretrade_cost_r",
        "broker_calibrated_expected_cost_r",
        "broker_pretrade_cost_non_executable_diagnostic_expected_cost_r",
        "total_execution_cost_r",
        "old_proxy_vs_broker_calibrated_delta_r",
        "commission_r",
        "spread_r",
        "swap_cost_r",
        "expected_slippage_r",
        "fallback_execution_surcharge_r",
        "pretrade_cost_packet_status",
        "missed_pretrade_cost_packet_status",
        "pretrade_cost_refusal_reasons",
        "broker_pretrade_cost_executable",
        "broker_pretrade_cost_executable_block_reason",
        "missed_cost_authority",
        "cost_authority",
        "execution_cost_authority",
        "cost_source_gap_status",
        "missed_cost_source_gap_status",
        "source_gap_cost_fallback_blocked",
        "missed_source_gap_cost_fallback_blocked",
        "candidate_cost_r_fallback_is_authority",
        "missed_candidate_cost_r_fallback_is_authority",
        "missed_cost_disposition",
        "missed_opportunity_accounting_scope",
        "missed_opportunity_r_scoreability_status",
        "missed_opportunity_headline_r_scoreable",
        "missed_opportunity_headline_execution_bound_eligible",
        "missed_cost_executable_opportunity_scoreable",
        "missed_cost_executable_headline_eligible",
        "missed_opportunity_counterfactual_scoreable",
        "missed_opportunity_non_executable_diagnostic_scoreable",
        "missed_opportunity_path_auditable",
        "missed_non_executable_diagnostic_reason",
        "miss_reason",
        "package_open_reduced_authority_allowed",
        "package_open_reduced_authority_family",
        "package_reduce_risk_authority_allowed",
        "package_reduce_risk_authority_family",
        "package_new_entry_authority_required",
        "package_new_entry_authority_valid",
        "package_new_entry_authority_status",
        "package_new_entry_authority_failures",
        "package_new_entry_authority_hash_sha256",
        "expected_package_new_entry_authority_hash_sha256",
        "package_new_entry_authority_payload_schema",
        "package_new_entry_authority_scope",
        "package_new_entry_authority_target_action_intent",
        "package_new_entry_authority_authority_field",
        "package_new_entry_authority_authority_family",
        "package_new_entry_authority_source_boundary",
        "package_new_entry_authority_uses_outcome_fields",
        "package_new_entry_authority_selector_action",
        "package_new_entry_authority_selector_reason",
        *PACKAGE_NEW_ENTRY_AUTHORITY_DECISION_INPUT_FIELDS,
        "package_replay_candidate_use_allowed",
        "package_replay_executable_candidate_use_allowed",
        "package_replay_executable_candidate_use_allowed_reason",
        "replay_candidate_use_allowed_now",
        "replay_candidate_use_allowed_now_reason",
        "source_bound_package_candidate_use_allowed",
        "ultimate_package_source_bound_candidate_use_allowed",
        "ultimate_package_effective_source_bound_candidate_use_allowed",
        "ultimate_package_effective_source_bound_signal_r",
        "source_bound_signal_r",
        "ultimate_package_combined_source_bound_signal_r_sum",
        "ultimate_package_admission_candidate_use_allowed",
        "ultimate_package_admission_sleeve_match_count",
        "ultimate_package_matched_sleeve_count",
        "ultimate_package_role_disposition",
        "selected_execution_policy_replay_status",
        "selected_execution_policy_replay_final_r",
        "selected_execution_policy_replay_final_r_authority_status",
        "selected_execution_policy_replay_source_boundary",
        "profit_harvest_mfe_capture_replay_exit_final_r_authority_status",
        "profit_harvest_replay_net_r",
        "profit_harvest_original_final_r",
        "profit_harvest_lost_target_net_r",
        "packet_sidecar_id",
        "packet_sidecar_hash_sha256",
        "full_packet_sidecar_status",
        "path_index_source_sha256",
        "path_index_rows_returned",
        "evidence_class",
        "live_broker_authority",
        "broker_mutation_enabled",
        "final_selection_claim",
        "package_execution_result_scope",
        "raw_baseline_diagnostic_only",
        "marketable_guard_profile",
        "broad_replay_profile",
        "split",
        "chunk_id",
        "phase",
        "campaign",
        "row_type",
    )
    compact_rows: list[dict[str, Any]] = []
    bulky_fields = (
        "candidate_decision_quality",
        "scheduler_candidate_decision_inputs",
        "risk_authority",
        "ultimate_candidate_package_open_reduced_risk_authority",
        "ultimate_candidate_package_reduce_risk_authority",
        "source_bound_fields",
        "source_gaps",
        "total_cost_components",
    )
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        if (
            row.get("missed_opportunity_compact_schema")
            == COMPACT_MISSED_OPPORTUNITY_SCHEMA
        ):
            compact_rows.append(dict(row))
            continue
        compact = {key: row.get(key) for key in keep_fields if key in row}
        compact.update(
            canonical_replay_candidate_instance_fields(
                row,
                decision_time_utc=row.get("decision_time_utc"),
            )
        )
        alias_fields = ledger_namespace_alias_fields(
            row,
            decision_time_utc=row.get("decision_time_utc"),
        )
        for key, value in alias_fields.items():
            if compact.get(key) in (None, "", [], {}):
                compact[key] = value
        preserve_replay_truth_projection(
            compact,
            row,
            selected_scheduler_alias=bool(row.get("scheduler_final_selected"))
            or bool(row.get("risk_finalizer_selected")),
        )
        # Compact terminal rows remain proof surfaces. Preserve the complete
        # candidate-instance POI atom even while bulky packet payloads are omitted.
        compact.update(candidate_poi_state_ledger_fields(row))
        promote_scalar_authority_from_projection(compact, row)
        for key in bulky_fields:
            value = row.get(key)
            if value in (None, "", [], {}):
                continue
            if key == "risk_authority" and not isinstance(value, Mapping):
                continue
            compact[f"{key}_payload_omitted"] = True
            compact[f"{key}_payload_type"] = type(value).__name__
            if isinstance(value, Mapping):
                compact[f"{key}_payload_key_count"] = len(value)
        compact.update(
            {
                "missed_opportunity_compact_schema": (
                    COMPACT_MISSED_OPPORTUNITY_SCHEMA
                ),
                "missed_opportunity_payload_omitted": True,
                "missed_opportunity_candidate_packet_payload_omitted": True,
                "missed_opportunity_signed_authority_payload_preserved": False,
                "missed_opportunity_lossless_payload": False,
            }
        )
        if compact.get("source_boundary") in (None, "", [], {}):
            compact["source_boundary"] = next(
                (
                    value
                    for value in (
                        row.get("source_boundary"),
                        row.get("candidate_decision_quality_source_boundary"),
                        row.get("package_new_entry_authority_source_boundary"),
                    )
                    if value not in (None, "", [], {})
                ),
                None,
            )
        normalize_replay_quality_fields(compact, row_type="missed_opportunity")
        materialize_compact_missed_atomic_authority_envelope(compact, row)
        compact_rows.append(compact)
    return compact_rows


def project_compact_missed_transport_row(
    row: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one append-only missed row before proof transport."""

    source = dict(row)
    normalize_replay_quality_fields(source, row_type="missed_opportunity")
    return compact_missed_opportunity_rows((source,))[0]


def iter_compact_asof_decision_rows(
    rows: Iterable[Mapping[str, Any]],
) -> Iterable[dict[str, Any]]:
    """Bounded exact equivalent of ``compact_asof_decision_rows``."""

    for row in rows:
        yield compact_asof_decision_rows((row,))[0]


def iter_compact_scorecard_rows(
    rows: Iterable[Mapping[str, Any]],
) -> Iterable[dict[str, Any]]:
    """Bounded exact equivalent of ``compact_scorecard_rows``."""

    for row in rows:
        yield compact_scorecard_rows((row,))[0]


def iter_compact_missed_opportunity_rows(
    rows: Iterable[Mapping[str, Any]],
) -> Iterable[dict[str, Any]]:
    """Bounded exact equivalent of ``compact_missed_opportunity_rows``."""

    for row in rows:
        if (
            row.get("missed_opportunity_compact_schema")
            == COMPACT_MISSED_OPPORTUNITY_SCHEMA
        ):
            yield dict(row)
        else:
            yield compact_missed_opportunity_rows((row,))[0]


def iter_compact_candidate_index_rows(
    rows: Iterable[Mapping[str, Any]],
) -> Iterable[dict[str, Any]]:
    """Bounded exact equivalent of ``compact_candidate_index_rows``."""

    for row in rows:
        yield compact_candidate_index_rows((row,))[0]


def iter_counted_compact_projection_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    role: str,
    counts: Counter[str],
) -> Iterable[Mapping[str, Any]]:
    """Count compact projection statuses without retaining a second row list."""

    if role == "decision":
        status_field = "current_fvg_poi_generation_projection_status"
    elif role == "scorecard":
        status_field = "scheduler_option_trace_projection_status"
    else:
        raise ValueError(f"compact_projection_role_unknown:{role}")
    for row in rows:
        counts[f"{role}_input_rows"] += 1
        counts[f"{role}_rows"] += 1
        projection_status = str(row.get(status_field) or "projection_missing")
        if projection_status != "projection_missing":
            counts[f"{role}_projection_eligible_rows"] += 1
        counts[f"{role}_status::{projection_status}"] += 1
        yield row


def reset_outputs(outputs: Mapping[str, Path] = OUTPUTS) -> None:
    for key, path in outputs.items():
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def iter_dates(start: str, end: str) -> list[str]:
    start_d = date.fromisoformat(start)
    end_d = date.fromisoformat(end)
    days: list[str] = []
    current = start_d
    while current <= end_d:
        days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def split_for_day(day: str) -> str | None:
    target = date.fromisoformat(day)
    for split, start, end in SPLIT_RANGES:
        if date.fromisoformat(start) <= target <= date.fromisoformat(end):
            return split
    return None


def is_repair_seed_day(day: str) -> bool:
    target = date.fromisoformat(day)
    return date.fromisoformat(REPAIR_SEED_START) <= target <= date.fromisoformat(
        REPAIR_SEED_END
    )


def month_key(day: str) -> str:
    return day[:7].replace("-", "")


def data_roots() -> tuple[Path, ...]:
    return tuple(path for path in DATA_ROOTS if path.exists())


def source_authority_scope(days: Iterable[str]) -> dict[str, Any]:
    day_key = tuple(sorted(set(str(day) for day in days if day)))
    payload = {
        "mode": SOURCE_AUTHORITY_SCOPE_MODE,
        "days": list(day_key),
        "start_day": day_key[0] if day_key else None,
        "end_day": day_key[-1] if day_key else None,
        "day_count": len(day_key),
    }
    return {
        **payload,
        "scope_id": stable_sha256(payload),
    }


def bound_tick_source_authority(
    *,
    manifest_path: Path,
    expected_manifest_sha256: str,
) -> tuple[dict[str, tuple[SourceSpec, ...]], dict[str, Any]]:
    """Load one exact tick manifest without scanning a retired repository."""

    path = Path(manifest_path).resolve()
    if not path.is_file() or path.is_symlink():
        raise ValueError("attempt5_bound_tick_manifest_invalid")
    actual_manifest_sha256 = file_sha256(path)
    if (
        len(str(expected_manifest_sha256 or "")) != 64
        or actual_manifest_sha256 != expected_manifest_sha256
    ):
        raise ValueError("attempt5_bound_tick_manifest_sha256_mismatch")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("attempt5_bound_tick_manifest_not_mapping")
    files = payload.get("files")
    if isinstance(files, Mapping):
        file_payloads = tuple(files.values())
    elif isinstance(files, list):
        file_payloads = tuple(files)
    else:
        raise ValueError("attempt5_bound_tick_manifest_files_invalid")
    manifest_data_root = next(
        (parent for parent in path.parents if parent.name == "data"),
        None,
    )
    if manifest_data_root is None:
        raise ValueError("attempt5_bound_tick_manifest_repo_root_unresolved")
    logical_repo_root = manifest_data_root.parent.resolve()
    provenance = payload.get("source_provenance")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    specs_by_symbol: dict[str, list[SourceSpec]] = defaultdict(list)
    contract_sources: list[dict[str, Any]] = []
    for file_payload in file_payloads:
        if not isinstance(file_payload, Mapping):
            raise ValueError("attempt5_bound_tick_manifest_file_invalid")
        timeframe = str(file_payload.get("timeframe") or "").upper()
        if timeframe != "TICK":
            continue
        symbol = str(
            file_payload.get("file_symbol") or file_payload.get("symbol") or ""
        )
        mapped_symbol = str(
            file_payload.get("mt5_symbol")
            or file_payload.get("mapped_symbol")
            or ""
        )
        source_broker = first_present(
            file_payload.get("source_broker"),
            provenance.get("source_broker"),
        )
        source_role = first_present(
            file_payload.get("source_role"),
            provenance.get("source_role"),
        )
        source_scope = first_present(
            file_payload.get("source_truth_scope"),
            provenance.get("source_truth_scope"),
        )
        not_redacted_account = first_present(
            file_payload.get("not_redacted_account_native"),
            provenance.get("not_redacted_account_native"),
        )
        if (
            symbol not in GTOS_24_SYMBOL_SURFACE
            or mapped_symbol != timewarp_loop.ftmo_symbol(symbol)
            or source_broker != "FTMO"
            or source_role not in timewarp_loop.FTMO_ALLOWED_SOURCE_ROLES
            or source_scope != SOURCE_TRUTH_SCOPE
            or not_redacted_account is not True
        ):
            raise ValueError("attempt5_bound_tick_manifest_authority_invalid")
        raw_path = Path(str(file_payload.get("path") or ""))
        if raw_path.is_absolute() or raw_path.parts[:2] != (
            "data",
            "mt5_research_exports",
        ):
            raise ValueError("attempt5_bound_tick_source_path_invalid")
        source_candidates = [logical_repo_root / raw_path]
        if raw_path.suffix != ".gz":
            source_candidates.append(Path(f"{source_candidates[0]}.gz"))
        source_path = next(
            (candidate for candidate in source_candidates if candidate.is_file()),
            None,
        )
        rows = int(
            timewarp_loop.safe_float(
                first_present(
                    file_payload.get("row_count"),
                    file_payload.get("rows"),
                ),
                0.0,
            )
        )
        source_sha256 = str(
            first_present(
                file_payload.get("sha256"),
                file_payload.get("source_sha256"),
            )
            or ""
        )
        server_hash = str(file_payload.get("source_server_hash") or "")
        account_hash = str(file_payload.get("source_account_hash") or "")
        if (
            source_path is None
            or source_path.is_symlink()
            or rows <= 0
            or not timewarp_loop.is_sha256(source_sha256)
            or not timewarp_loop.is_sha256(server_hash)
            or not timewarp_loop.is_sha256(account_hash)
        ):
            raise ValueError("attempt5_bound_tick_source_identity_invalid")
        start_utc = first_present(
            file_payload.get("first"),
            file_payload.get("start_utc"),
            file_payload.get("request_start_utc"),
        )
        end_utc = first_present(
            file_payload.get("last"),
            file_payload.get("end_utc"),
            file_payload.get("request_end_utc"),
        )
        if parse_utc(start_utc) is None or parse_utc(end_utc) is None:
            raise ValueError("attempt5_bound_tick_source_interval_invalid")
        spec = SourceSpec(
            symbol=symbol,
            mapped_symbol=mapped_symbol,
            timeframe="TICK",
            path=source_path,
            source_family="ftmo_mt5_research_export",
            source_broker="FTMO",
            source_role=str(source_role),
            start_utc=start_utc,
            end_utc=end_utc,
            row_count=rows,
            sha256=source_sha256,
            export_tool=str(
                file_payload.get("export_tool") or payload.get("export_tool") or ""
            ),
            manifest_path=str(path),
            source_server_redacted=file_payload.get("source_server_redacted"),
            source_server_hash=server_hash,
            source_account_redacted=file_payload.get("source_account_redacted"),
            source_account_hash=account_hash,
            source_truth_scope=SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=True,
            replaces_missing_frozen_path_source=bool(
                first_present(
                    file_payload.get("replaces_missing_frozen_path_source"),
                    provenance.get("replaces_missing_frozen_path_source"),
                    False,
                )
            ),
        )
        specs_by_symbol[symbol].append(spec)
        contract_sources.append(
            {
                "symbol": symbol,
                "source_path": str(source_path),
                "source_bytes": source_path.stat().st_size,
                "declared_row_count": rows,
                "declared_sha256": source_sha256,
                "start_utc": start_utc,
                "end_utc": end_utc,
            }
        )
    if not specs_by_symbol:
        raise ValueError("attempt5_bound_tick_manifest_has_no_tick_sources")
    normalized_specs = {
        symbol: tuple(
            sorted(
                specs,
                key=lambda spec: (
                    str(spec.start_utc or ""),
                    str(spec.end_utc or ""),
                    str(spec.sha256 or ""),
                    str(spec.path),
                ),
            )
        )
        for symbol, specs in sorted(specs_by_symbol.items())
    }
    contract_core = {
        "schema": "gtos.replay_acceleration.bound_tick_source_authority.v1",
        "status": "exact_manifest_bound_tick_source_authority",
        "manifest_path": str(path),
        "manifest_sha256": actual_manifest_sha256,
        "logical_repo_root": str(logical_repo_root),
        "source_count": len(contract_sources),
        "symbols": sorted(normalized_specs),
        "sources": sorted(contract_sources, key=lambda row: str(row["symbol"])),
        "broad_retired_repo_scan_enabled": False,
        "payload_hash_verification_stage": "canonical_source_authority_preflight",
    }
    return normalized_specs, {
        **contract_core,
        "contract_root_sha256": stable_sha256(contract_core),
    }


def bound_tick_source_authority_from_sealed_source_ledger(
    *,
    ledger_path: Path,
    expected_ledger_sha256: str,
) -> tuple[dict[str, tuple[SourceSpec, ...]], dict[str, Any]]:
    """Restore one sealed resolver-selected tick component set exactly.

    Historical source-plan digests bind the resolver's complete selected
    component set, including components outside the execution month.  This
    loader accepts only an exact, authenticated source-universe ledger and
    deliberately performs no repository discovery or interval pruning.
    Actual tick reads remain bounded by the lazy query and sparse-cache window.
    """

    path = Path(ledger_path)
    if (
        not path.is_absolute()
        or not path.is_file()
        or path.is_symlink()
        or _path_has_symlink_component(path)
    ):
        raise ValueError("sealed_tick_source_ledger_invalid")
    before = _regular_source_stat_identity(path)
    try:
        raw = path.read_bytes()
    except OSError:
        raise ValueError("sealed_tick_source_ledger_read_failed") from None
    after = _regular_source_stat_identity(path)
    if before != after:
        raise ValueError("sealed_tick_source_ledger_changed_during_read")
    actual_ledger_sha256 = hashlib.sha256(raw).hexdigest()
    if (
        not timewarp_loop.is_sha256(expected_ledger_sha256)
        or actual_ledger_sha256 != str(expected_ledger_sha256)
    ):
        raise ValueError("sealed_tick_source_ledger_sha256_mismatch")

    specs_by_symbol: dict[str, list[SourceSpec]] = defaultdict(list)
    source_identities: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    manifest_identities: dict[str, dict[str, Any]] = {}
    try:
        decoded_lines = raw.decode("utf-8").splitlines()
    except UnicodeError:
        raise ValueError("sealed_tick_source_ledger_utf8_invalid") from None
    for line_number, line in enumerate(decoded_lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            raise ValueError(
                f"sealed_tick_source_ledger_json_invalid:{line_number}"
            ) from None
        if not isinstance(row, Mapping):
            raise ValueError(
                f"sealed_tick_source_ledger_row_invalid:{line_number}"
            )
        if row.get("row_type") != "tick_symbol_source":
            continue

        symbol = str(row.get("symbol") or "")
        mapped_symbol = str(row.get("mapped_symbol") or "")
        source_path_value = str(row.get("source_path") or "")
        declared_path_value = str(row.get("path") or "")
        source_path = Path(source_path_value)
        manifest_path_value = str(row.get("manifest_path") or "")
        manifest_path = Path(manifest_path_value)
        source_sha256 = str(row.get("source_sha256") or "")
        row_sha256 = str(row.get("sha256") or "")
        rows = row.get("row_count")
        duplicate_rows = row.get("rows")
        start_utc = row.get("start_utc")
        end_utc = row.get("end_utc")
        source_role = str(row.get("source_role") or "")
        start = parse_utc(start_utc)
        end = parse_utc(end_utc)
        authority_valid = bool(
            symbol in GTOS_24_SYMBOL_SURFACE
            and mapped_symbol == timewarp_loop.ftmo_symbol(symbol)
            and row.get("timeframe") == "TICK"
            and source_path_value
            and declared_path_value == source_path_value
            and source_path.is_absolute()
            and source_path.is_file()
            and not source_path.is_symlink()
            and not _path_has_symlink_component(source_path)
            and manifest_path_value
            and manifest_path.is_absolute()
            and manifest_path.is_file()
            and not manifest_path.is_symlink()
            and not _path_has_symlink_component(manifest_path)
            and timewarp_loop.is_sha256(source_sha256)
            and row_sha256 == source_sha256
            and type(rows) is int
            and rows > 0
            and duplicate_rows == rows
            and start is not None
            and end is not None
            and end >= start
            and row.get("source_family") == "ftmo_mt5_research_export"
            and row.get("source_broker") == "FTMO"
            and source_role in timewarp_loop.FTMO_ALLOWED_SOURCE_ROLES
            and row.get("source_truth_scope") == SOURCE_TRUTH_SCOPE
            and row.get("not_redacted_account_native") is True
            and row.get("broker_lifecycle_truth_satisfied") is False
            and row.get("ordered_tick_truth_satisfied") is True
            and row.get("diagnostic_fallback_only") is False
            and row.get("selected_status")
            == "selected_priority_tick_source"
            and row.get("status") == "selected_priority_tick_source"
            and row.get("live_broker_authority") is False
            and row.get("broker_mutation_enabled") is False
            and row.get("evidence_class") == SOURCE_BOUND_EVIDENCE_CLASS
            and timewarp_loop.is_sha256(row.get("source_server_hash"))
            and timewarp_loop.is_sha256(row.get("source_account_hash"))
        )
        if not authority_valid:
            raise ValueError(
                f"sealed_tick_source_ledger_authority_invalid:{line_number}"
            )
        if source_path_value in seen_paths:
            raise ValueError(
                "sealed_tick_source_ledger_duplicate_source:"
                f"{source_path_value}"
            )
        seen_paths.add(source_path_value)

        source_stat = _regular_source_stat_identity(source_path)
        manifest_key = str(manifest_path)
        if manifest_key not in manifest_identities:
            manifest_before = _regular_source_stat_identity(manifest_path)
            manifest_sha256 = file_sha256(manifest_path)
            manifest_after = _regular_source_stat_identity(manifest_path)
            if manifest_before != manifest_after:
                raise ValueError(
                    "sealed_tick_source_manifest_changed_during_read:"
                    f"{manifest_path}"
                )
            manifest_identities[manifest_key] = {
                "path": manifest_key,
                "sha256": manifest_sha256,
            }

        spec = SourceSpec(
            symbol=symbol,
            mapped_symbol=mapped_symbol,
            timeframe="TICK",
            path=source_path,
            source_family=str(row["source_family"]),
            source_broker="FTMO",
            source_role=source_role,
            start_utc=start_utc,
            end_utc=end_utc,
            row_count=rows,
            sha256=source_sha256,
            export_tool=str(row.get("export_tool") or ""),
            manifest_path=manifest_path_value,
            source_server_redacted=row.get("source_server_redacted"),
            source_server_hash=str(row["source_server_hash"]),
            source_account_redacted=row.get("source_account_redacted"),
            source_account_hash=str(row["source_account_hash"]),
            source_truth_scope=SOURCE_TRUTH_SCOPE,
            not_redacted_account_native=True,
            broker_lifecycle_truth_satisfied=False,
            ordered_tick_truth_satisfied=True,
            replaces_missing_frozen_path_source=bool(
                row.get("replaces_missing_frozen_path_source")
            ),
        )
        specs_by_symbol[symbol].append(spec)
        source_identities.append(
            {
                "symbol": symbol,
                "source_path": source_path_value,
                "source_sha256": source_sha256,
                "row_count": rows,
                "start_utc": start_utc,
                "end_utc": end_utc,
                "manifest_path": manifest_path_value,
                "source_stat_identity": source_stat,
            }
        )

    if not specs_by_symbol:
        raise ValueError("sealed_tick_source_ledger_empty")
    normalized_specs = {
        symbol: tuple(
            sorted(
                specs,
                key=lambda spec: (
                    str(spec.start_utc or ""),
                    str(spec.end_utc or ""),
                    str(spec.sha256 or ""),
                    str(spec.path),
                ),
            )
        )
        for symbol, specs in sorted(specs_by_symbol.items())
    }
    ordered_sources = sorted(
        source_identities,
        key=lambda row: (
            str(row["symbol"]),
            str(row["source_path"]),
            str(row["source_sha256"]),
        ),
    )
    ordered_manifests = [
        manifest_identities[key] for key in sorted(manifest_identities)
    ]
    contract_core = {
        "schema": (
            "gtos.replay_acceleration."
            "sealed_source_ledger_tick_authority.v1"
        ),
        "status": "exact_sealed_source_ledger_full_component_set_bound",
        "ledger_path": str(path),
        "ledger_sha256": actual_ledger_sha256,
        "ledger_stat_identity": before,
        "source_count": len(ordered_sources),
        "symbol_count": len(normalized_specs),
        "symbols": sorted(normalized_specs),
        "source_identity_projection_root_sha256": stable_sha256(
            ordered_sources
        ),
        "manifest_count": len(ordered_manifests),
        "manifest_inventory": ordered_manifests,
        "manifest_inventory_root_sha256": stable_sha256(ordered_manifests),
        "full_component_set_preserved": True,
        "authority_window_component_pruning_enabled": False,
        "ambient_repository_scan_enabled": False,
        "raw_source_hash_verification_stage": (
            "sparse_tick_cache_prewarm_before_source_plan_acceptance"
        ),
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
    }
    return normalized_specs, {
        **contract_core,
        "contract_root_sha256": stable_sha256(contract_core),
    }


def bound_tick_diagnostic_authority(
    bindings: Sequence[tuple[Path, str]],
) -> tuple[dict[str, tuple[str, ...]], dict[str, Any]]:
    """Reproduce exact outside-window source gaps from named manifests only."""

    gaps_by_symbol: dict[str, list[str]] = defaultdict(list)
    manifests: list[dict[str, Any]] = []
    january_start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    january_end = datetime(2026, 2, 1, tzinfo=timezone.utc)
    for manifest_path, expected_sha256 in bindings:
        path = Path(manifest_path).resolve()
        if not path.is_file() or path.is_symlink():
            raise ValueError("attempt5_bound_tick_diagnostic_manifest_invalid")
        actual_sha256 = file_sha256(path)
        if actual_sha256 != str(expected_sha256 or ""):
            raise ValueError(
                "attempt5_bound_tick_diagnostic_manifest_sha256_mismatch"
            )
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = payload.get("files") if isinstance(payload, Mapping) else None
        if isinstance(files, Mapping):
            file_payloads = tuple(files.values())
        elif isinstance(files, list):
            file_payloads = tuple(files)
        else:
            raise ValueError("attempt5_bound_tick_diagnostic_files_invalid")
        first_payload = next(
            (item for item in file_payloads if isinstance(item, Mapping)),
            None,
        )
        declared_manifest = Path(
            str((first_payload or {}).get("manifest_path") or "")
        )
        if (
            declared_manifest.is_absolute()
            or not declared_manifest.parts
            or tuple(path.parts[-len(declared_manifest.parts) :])
            != declared_manifest.parts
        ):
            raise ValueError(
                "attempt5_bound_tick_diagnostic_repo_root_unresolved"
            )
        logical_repo_root = Path(
            *path.parts[: -len(declared_manifest.parts)]
        ).resolve()
        provenance = payload.get("source_provenance")
        provenance = provenance if isinstance(provenance, Mapping) else {}
        valid_outside_window_count = 0
        manifest_gap_count = 0
        manifest_symbols: set[str] = set()
        for file_payload in file_payloads:
            if not isinstance(file_payload, Mapping):
                raise ValueError(
                    "attempt5_bound_tick_diagnostic_file_invalid"
                )
            timeframe = str(file_payload.get("timeframe") or "").upper()
            if timeframe != "TICK":
                continue
            symbol = str(
                file_payload.get("file_symbol")
                or file_payload.get("symbol")
                or ""
            )
            mapped_symbol = str(
                file_payload.get("mt5_symbol")
                or file_payload.get("mapped_symbol")
                or ""
            )
            source_broker = first_present(
                file_payload.get("source_broker"),
                provenance.get("source_broker"),
            )
            source_role = first_present(
                file_payload.get("source_role"),
                provenance.get("source_role"),
            )
            source_scope = first_present(
                file_payload.get("source_truth_scope"),
                provenance.get("source_truth_scope"),
            )
            not_redacted_account = first_present(
                file_payload.get("not_redacted_account_native"),
                provenance.get("not_redacted_account_native"),
            )
            if (
                symbol not in GTOS_24_SYMBOL_SURFACE
                or mapped_symbol != timewarp_loop.ftmo_symbol(symbol)
                or source_broker != "FTMO"
                or source_role not in timewarp_loop.FTMO_ALLOWED_SOURCE_ROLES
                or source_scope != SOURCE_TRUTH_SCOPE
                or not_redacted_account is not True
            ):
                raise ValueError(
                    "attempt5_bound_tick_diagnostic_authority_invalid"
                )
            manifest_symbols.add(symbol)
            raw_path = Path(str(file_payload.get("path") or ""))
            if raw_path.is_absolute() or not raw_path.parts:
                raise ValueError(
                    "attempt5_bound_tick_diagnostic_source_path_invalid"
                )
            source_path = logical_repo_root / raw_path
            source_candidates = [source_path]
            if raw_path.suffix != ".gz":
                source_candidates.append(Path(f"{source_path}.gz"))
            existing_path = next(
                (candidate for candidate in source_candidates if candidate.is_file()),
                None,
            )
            if existing_path is None:
                gaps_by_symbol[symbol].append(
                    f"{path}:{symbol}_TICK:export_path_missing:{source_path}"
                )
                manifest_gap_count += 1
                continue
            rows = int(
                timewarp_loop.safe_float(
                    first_present(
                        file_payload.get("row_count"),
                        file_payload.get("rows"),
                    ),
                    0.0,
                )
            )
            if rows <= 0:
                gaps_by_symbol[symbol].append(
                    f"{path}:{symbol}_TICK:row_count_missing_or_zero"
                )
                manifest_gap_count += 1
                continue
            source_sha256 = first_present(
                file_payload.get("sha256"),
                file_payload.get("source_sha256"),
            )
            if not timewarp_loop.is_sha256(source_sha256):
                raise ValueError(
                    "attempt5_bound_tick_diagnostic_source_sha256_invalid"
                )
            start = parse_utc(
                first_present(
                    file_payload.get("first"),
                    file_payload.get("start_utc"),
                    file_payload.get("request_start_utc"),
                )
            )
            end = parse_utc(
                first_present(
                    file_payload.get("last"),
                    file_payload.get("end_utc"),
                    file_payload.get("request_end_utc"),
                )
            )
            if start is None or end is None or start >= january_end or end < january_start:
                if start is None or end is None:
                    raise ValueError(
                        "attempt5_bound_tick_diagnostic_interval_invalid"
                    )
                valid_outside_window_count += 1
                continue
            raise ValueError(
                "attempt5_unmaterialized_tick_source_overlaps_january_window"
            )
        manifests.append(
            {
                "path": str(path),
                "sha256": actual_sha256,
                "logical_repo_root": str(logical_repo_root),
                "symbols": sorted(manifest_symbols),
                "gap_count": manifest_gap_count,
                "valid_outside_window_source_count": valid_outside_window_count,
            }
        )
    normalized_gaps = {
        symbol: tuple(gaps)
        for symbol, gaps in sorted(gaps_by_symbol.items())
    }
    contract_core = {
        "schema": "gtos.replay_acceleration.bound_tick_diagnostic_authority.v1",
        "status": "exact_named_manifest_diagnostics_bound",
        "manifests": manifests,
        "manifest_count": len(manifests),
        "gap_count": sum(len(gaps) for gaps in normalized_gaps.values()),
        "symbols_with_gaps": sorted(normalized_gaps),
        "gaps_by_symbol": {
            symbol: list(gaps) for symbol, gaps in normalized_gaps.items()
        },
        "broad_retired_repo_scan_enabled": False,
        "january_overlap_allowed": False,
    }
    return normalized_gaps, {
        **contract_core,
        "contract_root_sha256": stable_sha256(contract_core),
    }


def bound_tick_authorities_from_replay_cache(
    *,
    authority_summary_path: Path,
    expected_authority_summary_sha256: str,
    source_ledger_path: Path,
    expected_source_ledger_sha256: str,
    manifest_path: Path,
    expected_manifest_sha256: str,
    expected_source_contract_root_sha256: str,
    diagnostic_manifest_bindings: Sequence[tuple[Path, str]],
    expected_diagnostic_contract_root_sha256: str,
) -> tuple[
    dict[str, tuple[SourceSpec, ...]],
    dict[str, Any],
    dict[str, tuple[str, ...]],
    dict[str, Any],
]:
    """Reuse exact source authority already persisted by an accepted replay.

    The source ledger contains the complete source-spec projection while the
    partial summary contains the independently rooted primary and diagnostic
    contracts.  Exact hashes bind both local cache inputs, so no raw manifest
    or tick payload is read on this route.
    """

    summary_path = Path(authority_summary_path).resolve()
    ledger_path = Path(source_ledger_path).resolve()
    resolved_manifest = Path(manifest_path).resolve()
    if (
        not summary_path.is_file()
        or summary_path.is_symlink()
        or not ledger_path.is_file()
        or ledger_path.is_symlink()
        or not resolved_manifest.is_file()
        or resolved_manifest.is_symlink()
        or file_sha256(summary_path)
        != str(expected_authority_summary_sha256 or "")
        or file_sha256(ledger_path) != str(expected_source_ledger_sha256 or "")
    ):
        raise ValueError("attempt5_tick_authority_replay_cache_input_invalid")
    try:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError(
            "attempt5_tick_authority_replay_cache_summary_invalid"
        ) from None
    if (
        not isinstance(summary, Mapping)
        or summary.get("status")
        not in {
            "partial_in_progress_not_final_proof",
            "runtime_input_and_source_acceleration_barrier_complete_"
            "run_campaign_not_entered",
        }
        or summary.get("broker_mutation_enabled") is not False
    ):
        raise ValueError("attempt5_tick_authority_replay_cache_summary_invalid")

    source_contract = summary.get("bound_tick_source_authority")
    diagnostic_contract = summary.get("bound_tick_diagnostic_authority")
    if not isinstance(source_contract, Mapping) or not isinstance(
        diagnostic_contract, Mapping
    ):
        raise ValueError("attempt5_tick_authority_replay_cache_contract_missing")
    source_contract = dict(source_contract)
    diagnostic_contract = dict(diagnostic_contract)
    source_core = dict(source_contract)
    source_root = str(source_core.pop("contract_root_sha256", ""))
    diagnostic_core = dict(diagnostic_contract)
    diagnostic_root = str(
        diagnostic_core.pop("contract_root_sha256", "")
    )
    expected_manifest = str(expected_manifest_sha256 or "")
    if (
        source_contract.get("schema")
        != "gtos.replay_acceleration.bound_tick_source_authority.v1"
        or source_contract.get("status")
        != "exact_manifest_bound_tick_source_authority"
        or source_contract.get("manifest_path") != str(resolved_manifest)
        or source_contract.get("manifest_sha256") != expected_manifest
        or source_contract.get("broad_retired_repo_scan_enabled") is not False
        or source_root != str(expected_source_contract_root_sha256 or "")
        or source_root != stable_sha256(source_core)
    ):
        raise ValueError("attempt5_tick_authority_replay_cache_source_invalid")
    if (
        diagnostic_contract.get("schema")
        != "gtos.replay_acceleration.bound_tick_diagnostic_authority.v1"
        or diagnostic_contract.get("status")
        != "exact_named_manifest_diagnostics_bound"
        or diagnostic_contract.get("broad_retired_repo_scan_enabled") is not False
        or diagnostic_contract.get("january_overlap_allowed") is not False
        or diagnostic_root
        != str(expected_diagnostic_contract_root_sha256 or "")
        or diagnostic_root != stable_sha256(diagnostic_core)
    ):
        raise ValueError(
            "attempt5_tick_authority_replay_cache_diagnostic_invalid"
        )
    expected_diagnostic_bindings = tuple(
        (str(Path(path).resolve()), str(sha256))
        for path, sha256 in diagnostic_manifest_bindings
    )
    cached_diagnostic_bindings = tuple(
        (str(row.get("path") or ""), str(row.get("sha256") or ""))
        for row in (diagnostic_contract.get("manifests") or ())
        if isinstance(row, Mapping)
    )
    if cached_diagnostic_bindings != expected_diagnostic_bindings:
        raise ValueError(
            "attempt5_tick_authority_replay_cache_diagnostic_binding_mismatch"
        )

    contract_sources = source_contract.get("sources")
    contract_symbols = source_contract.get("symbols")
    if not isinstance(contract_sources, list) or not isinstance(
        contract_symbols, list
    ):
        raise ValueError("attempt5_tick_authority_replay_cache_sources_invalid")
    source_contract_by_symbol: dict[str, dict[str, Any]] = {}
    for raw_source in contract_sources:
        if not isinstance(raw_source, Mapping):
            raise ValueError(
                "attempt5_tick_authority_replay_cache_sources_invalid"
            )
        row = dict(raw_source)
        symbol = str(row.get("symbol") or "")
        if not symbol or symbol in source_contract_by_symbol:
            raise ValueError(
                "attempt5_tick_authority_replay_cache_sources_invalid"
            )
        source_contract_by_symbol[symbol] = row

    source_rows: dict[str, dict[str, Any]] = {}
    try:
        with ledger_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw_row = json.loads(line)
                if not isinstance(raw_row, Mapping):
                    raise ValueError
                row = dict(raw_row)
                if row.get("row_type") != "tick_symbol_source":
                    continue
                symbol = str(row.get("symbol") or "")
                if symbol in source_rows:
                    raise ValueError
                source_rows[symbol] = row
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        raise ValueError(
            "attempt5_tick_authority_replay_cache_ledger_invalid"
        ) from None
    expected_symbols = tuple(sorted(str(value) for value in contract_symbols))
    if (
        tuple(sorted(source_rows)) != expected_symbols
        or tuple(sorted(source_contract_by_symbol)) != expected_symbols
        or int(source_contract.get("source_count") or -1)
        != len(expected_symbols)
    ):
        raise ValueError("attempt5_tick_authority_replay_cache_sources_invalid")

    specs_by_symbol: dict[str, tuple[SourceSpec, ...]] = {}
    recomputed_contract_sources: list[dict[str, Any]] = []
    for symbol in expected_symbols:
        row = source_rows[symbol]
        contract_source = source_contract_by_symbol[symbol]
        source_path = Path(str(row.get("source_path") or "")).resolve()
        row_count = int(row.get("row_count") or 0)
        source_sha256 = str(row.get("source_sha256") or "")
        if (
            row.get("selected_status") != "selected_priority_tick_source"
            or row.get("timeframe") != "TICK"
            or row.get("mapped_symbol") != timewarp_loop.ftmo_symbol(symbol)
            or row.get("source_broker") != "FTMO"
            or row.get("source_role")
            not in timewarp_loop.FTMO_ALLOWED_SOURCE_ROLES
            or row.get("source_truth_scope") != SOURCE_TRUTH_SCOPE
            or row.get("not_redacted_account_native") is not True
            or row.get("ordered_tick_truth_satisfied") is not True
            or row.get("broker_lifecycle_truth_satisfied") is not False
            or row.get("diagnostic_fallback_only") is not False
            or str(row.get("manifest_path") or "") != str(resolved_manifest)
            or str(row.get("path") or "") != str(source_path)
            or not source_path.is_file()
            or source_path.is_symlink()
            or row_count <= 0
            or not timewarp_loop.is_sha256(source_sha256)
            or not timewarp_loop.is_sha256(row.get("source_server_hash"))
            or not timewarp_loop.is_sha256(row.get("source_account_hash"))
            or parse_utc(row.get("start_utc")) is None
            or parse_utc(row.get("end_utc")) is None
        ):
            raise ValueError(
                "attempt5_tick_authority_replay_cache_source_row_invalid"
            )
        recomputed_contract_source = {
            "symbol": symbol,
            "source_path": str(source_path),
            "source_bytes": source_path.stat().st_size,
            "declared_row_count": row_count,
            "declared_sha256": source_sha256,
            "start_utc": row.get("start_utc"),
            "end_utc": row.get("end_utc"),
        }
        if recomputed_contract_source != contract_source:
            raise ValueError(
                "attempt5_tick_authority_replay_cache_source_contract_mismatch"
            )
        recomputed_contract_sources.append(recomputed_contract_source)
        specs_by_symbol[symbol] = (
            SourceSpec(
                symbol=symbol,
                mapped_symbol=str(row["mapped_symbol"]),
                timeframe="TICK",
                path=source_path,
                source_family=str(row.get("source_family") or ""),
                source_broker="FTMO",
                source_role=str(row["source_role"]),
                start_utc=str(row["start_utc"]),
                end_utc=str(row["end_utc"]),
                row_count=row_count,
                sha256=source_sha256,
                export_tool=str(row.get("export_tool") or ""),
                manifest_path=str(resolved_manifest),
                source_server_redacted=row.get("source_server_redacted"),
                source_server_hash=str(row["source_server_hash"]),
                source_account_redacted=row.get("source_account_redacted"),
                source_account_hash=str(row["source_account_hash"]),
                diagnostic_fallback_only=False,
                source_truth_scope=SOURCE_TRUTH_SCOPE,
                not_redacted_account_native=True,
                replaces_missing_frozen_path_source=bool(
                    row.get("replaces_missing_frozen_path_source")
                ),
                broker_lifecycle_truth_satisfied=False,
                ordered_tick_truth_satisfied=True,
            ),
        )
    if recomputed_contract_sources != contract_sources:
        raise ValueError(
            "attempt5_tick_authority_replay_cache_source_order_mismatch"
        )
    gaps = diagnostic_contract.get("gaps_by_symbol")
    if not isinstance(gaps, Mapping):
        raise ValueError(
            "attempt5_tick_authority_replay_cache_diagnostic_gaps_invalid"
        )
    normalized_gaps = {
        str(symbol): tuple(str(value) for value in values)
        for symbol, values in sorted(gaps.items())
        if isinstance(values, list)
    }
    if (
        sum(len(values) for values in normalized_gaps.values())
        != int(diagnostic_contract.get("gap_count") or 0)
        or sorted(normalized_gaps)
        != list(diagnostic_contract.get("symbols_with_gaps") or ())
    ):
        raise ValueError(
            "attempt5_tick_authority_replay_cache_diagnostic_gaps_invalid"
        )
    return (
        specs_by_symbol,
        source_contract,
        normalized_gaps,
        diagnostic_contract,
    )


def symbol_aliases(symbol: str) -> tuple[str, ...]:
    return SYMBOL_ALIASES.get(symbol, (symbol,))


def requested_replay_symbols(raw_symbols: Iterable[str] | None) -> tuple[str, ...] | None:
    if not raw_symbols:
        return None
    requested: list[str] = []
    canonical_by_upper = {symbol.upper(): symbol for symbol in GTOS_24_SYMBOL_SURFACE}
    for raw in raw_symbols:
        for item in str(raw or "").replace(",", " ").split():
            symbol_key = item.strip().upper()
            if not symbol_key:
                continue
            symbol = canonical_by_upper.get(symbol_key)
            if symbol is None:
                raise SystemExit(
                    f"Unsupported replay symbol {item.strip()!r}; expected one of "
                    f"{', '.join(GTOS_24_SYMBOL_SURFACE)}"
                )
            if symbol not in requested:
                requested.append(symbol)
    return tuple(requested) or None


def active_replay_symbol_universe(
    requested_symbols: Iterable[str] | None,
) -> tuple[str, ...]:
    return tuple(requested_symbols or GTOS_24_SYMBOL_SURFACE)


def first_existing_file(
    *,
    symbol: str,
    timeframe: str,
    root_order: Iterable[str],
) -> tuple[Path, str, str] | None:
    # Family priority is the authority contract. A lower-priority family in an
    # earlier data root must not displace a higher-priority family elsewhere.
    for family in root_order:
        for root in data_roots():
            for mapped_symbol in symbol_aliases(symbol):
                path = root / family / f"{mapped_symbol}_{timeframe}.csv"
                if path.exists():
                    return path, mapped_symbol, family
    return None


def row_time_bounds(rows: Iterable[Mapping[str, Any]]) -> tuple[str | None, str | None]:
    times = [parse_row_time(row) for row in rows]
    valid = [ts for ts in times if ts is not None]
    if not valid:
        return None, None
    return iso(min(valid)), iso(max(valid))


def source_covers_requested_range(
    rows: Iterable[Mapping[str, Any]],
    requested_days: Iterable[str] = (),
) -> tuple[bool, str | None, str | None]:
    start_utc, end_utc = row_time_bounds(rows)
    days = tuple(day for day in requested_days if day)
    if not days:
        return True, start_utc, end_utc
    start = parse_utc(start_utc)
    end = parse_utc(end_utc)
    if start is None or end is None:
        return False, start_utc, end_utc
    first_day = date.fromisoformat(days[0])
    last_day = date.fromisoformat(days[-1])
    return start.date() <= first_day and end.date() >= last_day, start_utc, end_utc


def source_spec_for_rows(
    *,
    symbol: str,
    mapped_symbol: str,
    timeframe: str,
    path: Path,
    source_family: str,
    rows: tuple[dict[str, Any], ...],
    sha256: str,
    source_role: str = "owner_authorized_research_hydration",
) -> SourceSpec:
    start_utc, end_utc = row_time_bounds(rows)
    return SourceSpec(
        symbol=symbol,
        mapped_symbol=mapped_symbol,
        timeframe=timeframe,
        path=path,
        source_family=source_family,
        source_broker="FTMO",
        source_role=source_role,
        start_utc=start_utc,
        end_utc=end_utc,
        row_count=len(rows),
        sha256=sha256,
        export_tool="local_historical_mt5_research_exports",
        manifest_path="source_resolved_by_broad_live_as_if_replay_harness",
        source_truth_scope=SOURCE_TRUTH_SCOPE,
        not_redacted_account_native=True,
        broker_lifecycle_truth_satisfied=False,
        ordered_tick_truth_satisfied=False,
    )


# BEGIN GTOS_SPARSE_TICK_CACHE_IMPLEMENTATION
SPARSE_TICK_CACHE_SCHEMA = "gtos.replay_acceleration.sparse_tick_window_cache.v1"
SPARSE_TICK_FILESYSTEM_STORAGE_SCHEMA = (
    "gtos.replay_acceleration.sparse_tick_filesystem_storage.v1"
)


def sparse_tick_cache_implementation_root() -> str:
    """Bind only the sparse-tick implementation, not unrelated runner edits."""

    source = Path(__file__).read_bytes()
    begin_marker = b"# BEGIN GTOS_SPARSE_TICK_CACHE_IMPLEMENTATION\n"
    end_marker = b"# " + b"END GTOS_SPARSE_TICK_CACHE_IMPLEMENTATION\n"
    try:
        begin = source.index(begin_marker) + len(begin_marker)
        end = source.index(end_marker, begin)
    except ValueError:
        raise RuntimeError("sparse_tick_cache_implementation_boundary_missing") from None
    return hashlib.sha256(source[begin:end]).hexdigest()


def _regular_source_stat_identity(path: Path) -> dict[str, int]:
    source = Path(path)
    try:
        info = os.lstat(source)
    except OSError:
        raise RuntimeError("sparse_tick_cache_source_stat_failed") from None
    if source.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise RuntimeError("sparse_tick_cache_source_not_regular")
    return {
        "device": int(info.st_dev),
        "inode": int(info.st_ino),
        "byte_count": int(info.st_size),
        "mtime_ns": int(info.st_mtime_ns),
        "ctime_ns": int(info.st_ctime_ns),
    }


def _allocated_file_bytes(path: Path) -> int:
    info = Path(path).stat()
    blocks = int(getattr(info, "st_blocks", 0) or 0)
    return blocks * 512 if blocks else int(info.st_size)


def compress_sparse_tick_partition_losslessly(
    path: Path,
    *,
    expected_sha256: str,
) -> dict[str, Any]:
    """Apply transparent APFS compression without changing logical bytes."""

    target = Path(path)
    logical_bytes = target.stat().st_size
    actual_sha256 = file_sha256(target)
    if actual_sha256 != str(expected_sha256):
        raise RuntimeError("sparse_tick_cache_precompression_sha256_mismatch")
    allocated_before = _allocated_file_bytes(target)
    ditto = shutil.which("ditto") if sys.platform == "darwin" else None
    if ditto is None:
        return {
            "schema": SPARSE_TICK_FILESYSTEM_STORAGE_SCHEMA,
            "status": "FILESYSTEM_COMPRESSION_UNAVAILABLE",
            "logical_bytes": logical_bytes,
            "allocated_bytes_before": allocated_before,
            "allocated_bytes_after": allocated_before,
            "sha256": actual_sha256,
        }

    temporary = target.with_name(f".{target.name}.{os.getpid()}.hfs-compressed")
    if temporary.exists() or temporary.is_symlink():
        raise RuntimeError("sparse_tick_cache_compression_temporary_exists")
    try:
        subprocess.run(
            [
                ditto,
                "--hfsCompression",
                "--zlibCompressionLevel",
                "9",
                str(target),
                str(temporary),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if (
            temporary.stat().st_size != logical_bytes
            or file_sha256(temporary) != actual_sha256
        ):
            raise RuntimeError("sparse_tick_cache_compression_byte_drift")
        allocated_after = _allocated_file_bytes(temporary)
        if allocated_after >= allocated_before:
            temporary.unlink()
            return {
                "schema": SPARSE_TICK_FILESYSTEM_STORAGE_SCHEMA,
                "status": "FILESYSTEM_COMPRESSION_UNAVAILABLE",
                "logical_bytes": logical_bytes,
                "allocated_bytes_before": allocated_before,
                "allocated_bytes_after": allocated_before,
                "sha256": actual_sha256,
            }
        os.replace(temporary, target)
    except BaseException:
        if temporary.exists() or temporary.is_symlink():
            temporary.unlink()
        raise
    return {
        "schema": SPARSE_TICK_FILESYSTEM_STORAGE_SCHEMA,
        "status": "APFS_TRANSPARENT_COMPRESSION_APPLIED",
        "logical_bytes": logical_bytes,
        "allocated_bytes_before": allocated_before,
        "allocated_bytes_after": allocated_after,
        "sha256": actual_sha256,
    }


def attempt5_tick_sparse_cache_window(
    start_day: str,
    end_day: str,
) -> tuple[datetime, datetime]:
    """Cover cost lookback and pending expiry around the sealed replay range."""

    start = datetime.fromisoformat(str(start_day)).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(str(end_day)).replace(tzinfo=timezone.utc)
    return start - timedelta(days=1), end + timedelta(days=2)


def attempt5_effective_tick_sparse_cache_window(
    args: argparse.Namespace,
) -> tuple[datetime, datetime]:
    """Hydrate ticks only through the final day this invocation can execute."""

    start_day = str(args.start)
    contract_end_day = str(args.end)
    effective_end_day = contract_end_day
    if bool(getattr(args, "stop_after_parity_gate", False)):
        parity_day = str(getattr(args, "parity_gate_after_day", "") or "")
        try:
            start_date = date.fromisoformat(start_day)
            contract_end_date = date.fromisoformat(contract_end_day)
            parity_date = date.fromisoformat(parity_day)
        except ValueError as exc:
            raise ValueError(
                "attempt5_tick_sparse_cache_parity_window_invalid"
            ) from exc
        if not start_date <= parity_date <= contract_end_date:
            raise ValueError("attempt5_tick_sparse_cache_parity_window_invalid")
        effective_end_day = parity_day
    for field in (
        "physical_reference_checkpoint_after_day",
        "task2_semantic_checkpoint_after_day",
    ):
        checkpoint_day = str(getattr(args, field, "") or "")
        if not checkpoint_day:
            continue
        try:
            start_date = date.fromisoformat(start_day)
            contract_end_date = date.fromisoformat(contract_end_day)
            checkpoint_date = date.fromisoformat(checkpoint_day)
            effective_end_date = date.fromisoformat(effective_end_day)
        except ValueError as exc:
            raise ValueError(
                "attempt5_tick_sparse_cache_checkpoint_window_invalid"
            ) from exc
        if not start_date <= checkpoint_date <= contract_end_date:
            raise ValueError("attempt5_tick_sparse_cache_checkpoint_window_invalid")
        if checkpoint_date < effective_end_date:
            effective_end_day = checkpoint_day
    return attempt5_tick_sparse_cache_window(start_day, effective_end_day)


def attempt5_streaming_warning_floor_bytes(
    args: argparse.Namespace,
    *,
    parity_gate_requested: bool,
) -> int:
    """Use the bounded reserve only for the exact Jan 1-7 stop gate."""

    bounded_parity_stop = (
        bool(parity_gate_requested)
        and bool(getattr(args, "stop_after_parity_gate", False))
        and str(getattr(args, "start", "")) == ATTEMPT5_START_DAY
        and str(getattr(args, "end", "")) == ATTEMPT5_CONTRACT_END_DAY
        and str(getattr(args, "parity_gate_after_day", ""))
        == ATTEMPT5_PARITY_DAY
    )
    if bounded_parity_stop:
        return ATTEMPT5_STREAMING_BOUNDED_WARNING_FLOOR_BYTES
    return B7_5_MANDATORY_POST_REPLAY_RESERVE_BYTES


class SparseTickWindowRowsByDay:
    """Immutable day shards that replace repeated full-gzip window scans."""

    lookup_mode = LazyTickRowsByDay.lookup_mode

    def __init__(
        self,
        *,
        symbol: str,
        spec: SourceSpec,
        cache_root: Path,
        window_start: datetime,
        window_end: datetime,
    ) -> None:
        if window_start.tzinfo is None or window_end.tzinfo is None:
            raise ValueError("sparse_tick_cache_window_timezone_missing")
        if window_end <= window_start:
            raise ValueError("sparse_tick_cache_window_invalid")
        self.symbol = str(symbol)
        self.spec = spec
        self.specs = (spec,)
        self.cache_root = Path(cache_root).resolve()
        self.window_start = window_start.astimezone(timezone.utc)
        self.window_end = window_end.astimezone(timezone.utc)
        self.last_validation_events: tuple[dict[str, Any], ...] = ()
        self.last_cache_validation_events: tuple[dict[str, Any], ...] = ()
        self._fallback = LazyTickRowsByDay(symbol=self.symbol, specs=self.specs)
        self._manifest: dict[str, Any] | None = None
        self._partition_by_day: dict[str, dict[str, Any]] = {}
        self._filesystem_storage_telemetry: tuple[dict[str, Any], ...] = ()
        self._raw_source_full_hash_performed = False
        self._sealed_cache_reused = False
        self._source_full_hash_validated = False
        self._day_cache: OrderedDict[
            str,
            tuple[tuple[dict[str, Any], ...], tuple[datetime, ...]],
        ] = OrderedDict()
        self._bind_identity(_regular_source_stat_identity(Path(spec.path)))

    def _publish_validation_event(self, event: Mapping[str, Any]) -> None:
        cache_event = dict(event)
        self.last_cache_validation_events = (cache_event,)
        legacy_event = {
            key: cache_event[key]
            for key in (
                "path",
                "manifest_sha256",
                "actual_sha256",
                "sha_validation_status",
                "sha_validation_error",
            )
            if key in cache_event
        }
        if cache_event.get("sha_validation_status") == (
            "sealed_full_hash_attestation_reused"
        ):
            legacy_event["actual_sha256"] = str(self.spec.sha256 or "")
            legacy_event["sha_validation_status"] = "validated_file_hash_match"
        self.last_validation_events = (legacy_event,)

    def _bind_identity(self, source_stat_identity: Mapping[str, int]) -> None:
        identity = {
            "schema": SPARSE_TICK_CACHE_SCHEMA,
            "source_path": str(Path(self.spec.path).resolve()),
            "source_sha256": str(self.spec.sha256 or ""),
            "source_stat_identity": dict(source_stat_identity),
            "declared_source_row_count": int(self.spec.row_count or 0),
            "symbol": self.symbol,
            "window_start_utc": iso(self.window_start),
            "window_end_utc": iso(self.window_end),
            "builder_path": str(Path(__file__).resolve()),
            "builder_implementation_root_sha256": (
                sparse_tick_cache_implementation_root()
            ),
            "row_semantics": (
                "original_json_payload_with_legacy_time_time_utc_symbol_normalization"
            ),
        }
        self.identity = identity
        self.identity_root_sha256 = stable_sha256(identity)
        self.entry = self.cache_root / self.identity_root_sha256

    def _validate_source(self) -> bool:
        event: dict[str, Any] = {
            "path": str(self.spec.path),
            "manifest_sha256": self.spec.sha256,
            "sha_validation_status": "not_checked",
        }
        try:
            current_stat = _regular_source_stat_identity(Path(self.spec.path))
        except RuntimeError as exc:
            event["sha_validation_status"] = "validation_failed"
            event["sha_validation_error"] = str(exc)
            self._publish_validation_event(event)
            return False
        if current_stat != self.identity.get("source_stat_identity"):
            self._manifest = None
            self._partition_by_day = {}
            self._bind_identity(current_stat)
        if self._manifest is not None:
            event.update(
                {
                    "status": (
                        "SEALED_CACHE_REUSED_AFTER_EXACT_SOURCE_STAT_AND_"
                        "PARTITION_VALIDATION"
                    ),
                    "sha_validation_status": "sealed_full_hash_attestation_reused",
                    "source_stat_identity": current_stat,
                    "raw_source_full_hash_performed": False,
                }
            )
            self._sealed_cache_reused = True
            self._publish_validation_event(event)
            return True
        if self.entry.exists() or self.entry.is_symlink():
            self._validate_entry()
            event.update(
                {
                    "status": (
                        "SEALED_CACHE_REUSED_AFTER_EXACT_SOURCE_STAT_AND_"
                        "PARTITION_VALIDATION"
                    ),
                    "sha_validation_status": "sealed_full_hash_attestation_reused",
                    "source_stat_identity": current_stat,
                    "raw_source_full_hash_performed": False,
                }
            )
            self._sealed_cache_reused = True
            self._publish_validation_event(event)
            return True
        event.update(
            {
                "status": "FULL_SOURCE_SHA256_DEFERRED_TO_SINGLE_PASS_BUILD",
                "sha_validation_status": "single_pass_build_pending",
                "source_stat_identity": current_stat,
                "raw_source_full_hash_performed": False,
            }
        )
        self._publish_validation_event(event)
        return True

    @staticmethod
    def _manifest_root(manifest: Mapping[str, Any]) -> str:
        projection = dict(manifest)
        projection.pop("manifest_root_sha256", None)
        return stable_sha256(projection)

    def _validate_entry(self) -> None:
        if not self.entry.is_dir() or self.entry.is_symlink():
            raise RuntimeError("sparse_tick_cache_entry_invalid")
        manifest_path = self.entry / "manifest.json"
        sealed_path = self.entry / "SEALED"
        if (
            not manifest_path.is_file()
            or manifest_path.is_symlink()
            or not sealed_path.is_file()
            or sealed_path.is_symlink()
        ):
            raise RuntimeError("sparse_tick_cache_seal_missing")
        manifest = json.loads(manifest_path.read_text(encoding="ascii"))
        if not isinstance(manifest, Mapping):
            raise RuntimeError("sparse_tick_cache_manifest_invalid")
        manifest = dict(manifest)
        manifest_root = str(manifest.get("manifest_root_sha256") or "")
        if (
            manifest.get("schema") != SPARSE_TICK_CACHE_SCHEMA
            or manifest.get("status") != "SEALED_IMMUTABLE_SPARSE_TICK_WINDOW"
            or manifest.get("identity") != self.identity
            or manifest.get("identity_root_sha256") != self.identity_root_sha256
            or manifest_root != self._manifest_root(manifest)
            or sealed_path.read_text(encoding="ascii").strip() != manifest_root
        ):
            raise RuntimeError("sparse_tick_cache_manifest_commitment_mismatch")
        source_validation = manifest.get("source_validation")
        if source_validation != {
            "status": "FULL_SOURCE_SHA256_VALIDATED_AT_BUILD",
            "source_sha256": str(self.spec.sha256 or ""),
            "source_stat_identity": self.identity["source_stat_identity"],
        }:
            raise RuntimeError("sparse_tick_cache_source_attestation_invalid")
        partition_by_day: dict[str, dict[str, Any]] = {}
        for raw_partition in manifest.get("partitions") or ():
            if not isinstance(raw_partition, Mapping):
                raise RuntimeError("sparse_tick_cache_partition_manifest_invalid")
            partition = dict(raw_partition)
            day = str(partition.get("day") or "")
            relative_path = Path(str(partition.get("path") or ""))
            unresolved_path = self.entry / relative_path
            path = unresolved_path.resolve()
            try:
                path.relative_to(self.entry.resolve())
            except ValueError:
                raise RuntimeError("sparse_tick_cache_partition_escape") from None
            if (
                not day
                or relative_path.parts[:1] != ("partitions",)
                or unresolved_path.is_symlink()
                or not path.is_file()
                or path.stat().st_size != int(partition.get("bytes") or -1)
            ):
                raise RuntimeError("sparse_tick_cache_partition_invalid")
            if file_sha256(path) != partition.get("sha256"):
                raise RuntimeError("sparse_tick_cache_partition_sha256_mismatch")
            partition_by_day[day] = partition
        if len(partition_by_day) != int(manifest.get("partition_count") or 0):
            raise RuntimeError("sparse_tick_cache_partition_count_mismatch")
        self._manifest = manifest
        self._partition_by_day = partition_by_day

    def _build_entry(self) -> None:
        source_path = Path(self.spec.path)
        source_digest = hashlib.sha256()
        source_stat_before = dict(self.identity["source_stat_identity"])
        self.cache_root.mkdir(parents=True, exist_ok=True)
        temporary = self.cache_root / (
            f".{self.identity_root_sha256}.{os.getpid()}.tmp"
        )
        if temporary.exists() or temporary.is_symlink():
            shutil.rmtree(temporary, ignore_errors=True)
        partition_root = temporary / "partitions"
        partition_root.mkdir(parents=True)
        handles: dict[str, Any] = {}
        digests: dict[str, Any] = {}
        row_counts: Counter[str] = Counter()
        byte_counts: Counter[str] = Counter()
        scanned_row_count = 0
        retained_row_count = 0
        previous_timestamp: datetime | None = None
        past_window_end = False
        try:
            source_handle = (
                gzip.open(source_path, "rb")
                if source_path.suffix == ".gz"
                else source_path.open("rb")
            )
            with source_handle:
                for raw_line in source_handle:
                    source_digest.update(raw_line)
                    if past_window_end:
                        continue
                    if not raw_line.strip():
                        continue
                    try:
                        payload = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(payload, dict):
                        continue
                    ts = parse_row_time(payload)
                    if ts is None:
                        continue
                    if previous_timestamp is not None and ts < previous_timestamp:
                        raise RuntimeError("sparse_tick_cache_source_not_time_ordered")
                    previous_timestamp = ts
                    scanned_row_count += 1
                    if ts > self.window_end:
                        past_window_end = True
                        continue
                    if ts < self.window_start:
                        continue
                    day = ts.date().isoformat()
                    handle = handles.get(day)
                    if handle is None:
                        handle = (partition_root / f"{day}.jsonl").open("wb")
                        handles[day] = handle
                        digests[day] = hashlib.sha256()
                    encoded = raw_line.rstrip(b"\r\n") + b"\n"
                    handle.write(encoded)
                    digests[day].update(encoded)
                    row_counts[day] += 1
                    byte_counts[day] += len(encoded)
                    retained_row_count += 1
            actual_sha256 = source_digest.hexdigest()
            source_stat_after = _regular_source_stat_identity(source_path)
            stable_fields = ("device", "inode", "byte_count", "mtime_ns")
            if any(
                source_stat_before[field] != source_stat_after[field]
                for field in stable_fields
            ):
                raise RuntimeError("sparse_tick_cache_source_changed_during_build")
            self._raw_source_full_hash_performed = True
            if self.spec.sha256 and actual_sha256 != self.spec.sha256:
                raise RuntimeError(
                    f"sparse_tick_cache_prewarm_source_validation_failed:{source_path}"
                )
            if source_stat_after != source_stat_before:
                self._bind_identity(source_stat_after)
            self._source_full_hash_validated = True
            self._publish_validation_event(
                {
                    "path": str(source_path),
                    "manifest_sha256": self.spec.sha256,
                    "actual_sha256": actual_sha256,
                    "status": "FULL_SOURCE_SHA256_VALIDATED_DURING_SINGLE_PASS_BUILD",
                    "sha_validation_status": "validated_file_hash_match",
                    "source_stat_identity": source_stat_after,
                    "raw_source_full_hash_performed": True,
                }
            )
            for handle in handles.values():
                handle.flush()
                os.fsync(handle.fileno())
                handle.close()
            handles.clear()
            storage_by_day = {
                day: compress_sparse_tick_partition_losslessly(
                    partition_root / f"{day}.jsonl",
                    expected_sha256=digests[day].hexdigest(),
                )
                for day in sorted(row_counts)
            }
            storage_telemetry = tuple(
                {"day": day, **storage_by_day[day]}
                for day in sorted(storage_by_day)
            )
            partitions = [
                {
                    "day": day,
                    "path": f"partitions/{day}.jsonl",
                    "rows": int(row_counts[day]),
                    "bytes": int(byte_counts[day]),
                    "sha256": digests[day].hexdigest(),
                }
                for day in sorted(row_counts)
            ]
            manifest_core = {
                "schema": SPARSE_TICK_CACHE_SCHEMA,
                "status": "SEALED_IMMUTABLE_SPARSE_TICK_WINDOW",
                "identity": self.identity,
                "identity_root_sha256": self.identity_root_sha256,
                "partition_count": len(partitions),
                "retained_row_count": retained_row_count,
                "source_rows_scanned_through_window_end": scanned_row_count,
                "source_validation": {
                    "status": "FULL_SOURCE_SHA256_VALIDATED_AT_BUILD",
                    "source_sha256": str(self.spec.sha256 or ""),
                    "source_stat_identity": self.identity["source_stat_identity"],
                },
                "partitions": partitions,
                "economic_values_exposed": False,
                "broker_live_authority": False,
            }
            manifest = {
                **manifest_core,
                "manifest_root_sha256": stable_sha256(manifest_core),
            }
            atomic_write_json(temporary / "manifest.json", manifest)
            with (temporary / "SEALED").open("w", encoding="ascii") as handle:
                handle.write(str(manifest["manifest_root_sha256"]) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            if self.entry.exists() or self.entry.is_symlink():
                shutil.rmtree(temporary)
            else:
                os.replace(temporary, self.entry)
                self._filesystem_storage_telemetry = storage_telemetry
        except BaseException:
            for handle in handles.values():
                try:
                    handle.close()
                except OSError:
                    pass
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    def _ensure_entry(self) -> None:
        if self._manifest is not None:
            return
        if not self.entry.exists() and not self.entry.is_symlink():
            self._build_entry()
        self._validate_entry()

    def _load_day(
        self,
        day: str,
    ) -> tuple[tuple[dict[str, Any], ...], tuple[datetime, ...]]:
        cached = self._day_cache.pop(day, None)
        if cached is not None:
            self._day_cache[day] = cached
            return cached
        partition = self._partition_by_day.get(day)
        if partition is None:
            return (), ()
        path = self.entry / str(partition["path"])
        if file_sha256(path) != partition.get("sha256"):
            raise RuntimeError("sparse_tick_cache_partition_sha256_mismatch")
        indexed_rows: list[tuple[datetime, dict[str, Any]]] = []
        with path.open("rb") as handle:
            for raw_line in handle:
                if not raw_line.strip():
                    continue
                try:
                    payload = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(payload, dict):
                    continue
                ts = parse_row_time(payload)
                if ts is None:
                    continue
                normalized = dict(payload)
                normalized["time"] = iso(ts)
                normalized["time_utc"] = iso(ts)
                normalized["symbol"] = self.symbol
                indexed_rows.append((ts, normalized))
        indexed_rows.sort(key=lambda item: item[0])
        if len(indexed_rows) != int(partition.get("rows") or 0):
            raise RuntimeError("sparse_tick_cache_partition_row_count_mismatch")
        result = (
            tuple(row for _timestamp, row in indexed_rows),
            tuple(timestamp for timestamp, _row in indexed_rows),
        )
        self._day_cache[day] = result
        while len(self._day_cache) > 2:
            self._day_cache.popitem(last=False)
        return result

    def query(
        self,
        *,
        after: datetime,
        until: datetime,
    ) -> tuple[tuple[dict[str, Any], ...], list[str]]:
        if after < self.window_start or until > self.window_end:
            result = self._fallback.query(after=after, until=until)
            self.last_validation_events = self._fallback.last_validation_events
            return result
        if not self._validate_source():
            return (), []
        self._ensure_entry()
        rows: list[dict[str, Any]] = []
        days: set[str] = set()
        seen: set[tuple[Any, Any, Any, Any, Any]] = set()
        cursor = after.date()
        end_day = until.date()
        while cursor <= end_day:
            day_rows, day_timestamps = self._load_day(cursor.isoformat())
            first = bisect_right(day_timestamps, after)
            last = bisect_right(day_timestamps, until)
            for row, ts in zip(
                day_rows[first:last],
                day_timestamps[first:last],
            ):
                key = (
                    row.get("time_utc") or row.get("time"),
                    row.get("bid"),
                    row.get("ask"),
                    row.get("last"),
                    row.get("volume"),
                )
                if key in seen:
                    continue
                seen.add(key)
                days.add(ts.date().isoformat())
                rows.append(dict(row))
            cursor += timedelta(days=1)
        rows.sort(key=lambda row: str(row.get("time_utc") or row.get("time")))
        return tuple(rows), sorted(days)

    def get(self, day: str, default: Any = None) -> Any:
        try:
            start = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        except ValueError:
            return default
        rows, _days = self.query(
            after=start - timedelta(microseconds=1),
            until=start + timedelta(days=1),
        )
        return rows or default

    def release_completed_days(self, days: Iterable[str]) -> int:
        released = 0
        for day in set(str(value) for value in days):
            indexed_rows = self._day_cache.pop(day, None)
            if indexed_rows is not None:
                released += len(indexed_rows[0])
        return released

    def release_all_loaded_days(self) -> int:
        released = sum(len(rows) for rows, _timestamps in self._day_cache.values())
        self._day_cache.clear()
        return released


def _prewarm_sparse_tick_entry(
    task: tuple[str, SourceSpec, str, str, str],
) -> dict[str, Any]:
    symbol, spec, cache_root, window_start_utc, window_end_utc = task
    window_start = parse_utc(window_start_utc)
    window_end = parse_utc(window_end_utc)
    if window_start is None or window_end is None:
        raise RuntimeError("sparse_tick_cache_prewarm_window_invalid")
    cache = SparseTickWindowRowsByDay(
        symbol=symbol,
        spec=spec,
        cache_root=Path(cache_root),
        window_start=window_start,
        window_end=window_end,
    )
    if not cache._validate_source():
        raise RuntimeError(
            f"sparse_tick_cache_prewarm_source_validation_failed:{spec.path}"
        )
    cache._ensure_entry()
    manifest = cache._manifest or {}
    return {
        "symbol": symbol,
        "source_path": str(spec.path),
        "source_sha256": str(spec.sha256 or ""),
        "identity_root_sha256": cache.identity_root_sha256,
        "manifest_root_sha256": manifest.get("manifest_root_sha256"),
        "partition_count": int(manifest.get("partition_count") or 0),
        "retained_row_count": int(manifest.get("retained_row_count") or 0),
        "source_validation": dict(
            (cache.last_cache_validation_events or ({},))[0]
        ),
        "raw_source_full_hash_performed": cache._raw_source_full_hash_performed,
        "sealed_cache_reused": cache._sealed_cache_reused,
        "non_authoritative_filesystem_storage": list(
            cache._filesystem_storage_telemetry
        ),
    }


def prewarm_sparse_tick_sources(
    *,
    specs_by_symbol: Mapping[str, Sequence[SourceSpec]],
    cache_root: Path,
    window_start: datetime,
    window_end: datetime,
    workers: int,
) -> dict[str, Any]:
    tasks = tuple(
        (
            str(symbol),
            spec,
            str(Path(cache_root).resolve()),
            str(iso(window_start)),
            str(iso(window_end)),
        )
        for symbol, specs in sorted(specs_by_symbol.items())
        for spec in specs
    )
    if not tasks:
        raise RuntimeError("sparse_tick_cache_prewarm_sources_missing")
    if workers <= 1 or len(tasks) == 1:
        entries = [_prewarm_sparse_tick_entry(task) for task in tasks]
    else:
        try:
            with ProcessPoolExecutor(
                max_workers=min(int(workers), len(tasks))
            ) as pool:
                entries = list(pool.map(_prewarm_sparse_tick_entry, tasks))
        except OSError as exc:
            if exc.errno != errno.EDEADLK:
                raise
            # macOS can return EDEADLK while several workers hydrate APFS
            # dataless/iCloud-backed sources concurrently.  The source bytes
            # and cache identities remain exact, so retry the same immutable
            # tasks serially instead of failing the replay.
            entries = [_prewarm_sparse_tick_entry(task) for task in tasks]
    entries.sort(
        key=lambda row: (
            str(row.get("symbol")),
            str(row.get("source_path")),
            str(row.get("source_sha256")),
        )
    )
    storage_entries = [
        {
            "symbol": str(entry.get("symbol")),
            "source_path": str(entry.get("source_path")),
            "source_sha256": str(entry.get("source_sha256")),
            "partitions": list(
                entry.pop("non_authoritative_filesystem_storage", ())
            ),
        }
        for entry in entries
    ]
    core = {
        "schema": "gtos.replay_acceleration.sparse_tick_cache_prewarm.v1",
        "status": "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE",
        "cache_schema": SPARSE_TICK_CACHE_SCHEMA,
        "cache_root": str(Path(cache_root).resolve()),
        "window_start_utc": iso(window_start),
        "window_end_utc": iso(window_end),
        "worker_count": min(max(1, int(workers)), len(tasks)),
        "entry_count": len(entries),
        "partition_count": sum(int(row["partition_count"]) for row in entries),
        "retained_row_count": sum(int(row["retained_row_count"]) for row in entries),
        "raw_source_full_hash_count": sum(
            int(row["raw_source_full_hash_performed"]) for row in entries
        ),
        "sealed_cache_reuse_count": sum(
            int(row["sealed_cache_reused"]) for row in entries
        ),
        "cache_precondition_measurement": (
            "entry_identity_binds_exact_source_stat_declared_sha_builder_and_window;"
            "reuse_recomputes_manifest_and_partition_hashes"
        ),
        "entries": entries,
        "economic_values_exposed": False,
        "broker_live_authority": False,
    }
    storage_receipt = {
        "schema": SPARSE_TICK_FILESYSTEM_STORAGE_SCHEMA,
        "status": "NON_AUTHORITATIVE_FILESYSTEM_STORAGE_TELEMETRY",
        "authoritative": False,
        "included_in_prewarm_root_sha256": False,
        "entries": storage_entries,
    }
    return {
        **core,
        "prewarm_root_sha256": stable_sha256(core),
        "non_authoritative_filesystem_storage_receipt": storage_receipt,
    }


# END GTOS_SPARSE_TICK_CACHE_IMPLEMENTATION


def attempt5_effective_execution_tick_sparse_cache_window(
    args: argparse.Namespace,
) -> tuple[datetime, datetime]:
    """Bound cache hydration to the final day this invocation can execute."""

    window_start, window_end = attempt5_effective_tick_sparse_cache_window(args)
    engineering_stop = str(
        getattr(args, "engineering_stop_after_day", "") or ""
    )
    cache_window_stop = str(
        getattr(args, "tick_sparse_cache_window_end_after_day", "") or ""
    )
    if not engineering_stop:
        if cache_window_stop:
            raise ValueError(
                "attempt5_tick_sparse_cache_window_override_without_engineering_stop"
            )
        return window_start, window_end
    try:
        start_date = date.fromisoformat(str(args.start))
        contract_end_date = date.fromisoformat(str(args.end))
        stop_date = date.fromisoformat(engineering_stop)
    except ValueError as exc:
        raise ValueError(
            "attempt5_tick_sparse_cache_engineering_stop_window_invalid"
        ) from exc
    if not start_date <= stop_date <= contract_end_date:
        raise ValueError(
            "attempt5_tick_sparse_cache_engineering_stop_window_invalid"
        )
    cache_stop_date = stop_date
    if cache_window_stop:
        try:
            cache_stop_date = date.fromisoformat(cache_window_stop)
        except ValueError as exc:
            raise ValueError(
                "attempt5_tick_sparse_cache_window_override_invalid"
            ) from exc
        if not stop_date <= cache_stop_date <= contract_end_date:
            raise ValueError(
                "attempt5_tick_sparse_cache_window_override_invalid"
            )
    bounded_start, bounded_end = attempt5_tick_sparse_cache_window(
        str(args.start), cache_stop_date.isoformat()
    )
    if bounded_start != window_start:
        raise RuntimeError("attempt5_tick_sparse_cache_window_start_drift")
    return bounded_start, min(window_end, bounded_end)


def sparse_tick_source_attestations(
    prewarm_receipt: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Return stat-bound source attestations from one exact prewarm barrier."""

    receipt = dict(prewarm_receipt)
    expected_root = str(receipt.pop("prewarm_root_sha256", ""))
    receipt.pop("non_authoritative_filesystem_storage_receipt", None)
    entries = receipt.get("entries")
    if (
        receipt.get("schema")
        != "gtos.replay_acceleration.sparse_tick_cache_prewarm.v1"
        or receipt.get("status")
        != "SEALED_SPARSE_TICK_CACHE_PREWARM_COMPLETE"
        or stable_sha256(receipt) != expected_root
        or not isinstance(entries, list)
        or len(entries) != int(receipt.get("entry_count") or -1)
    ):
        raise RuntimeError("sparse_tick_prewarm_attestation_root_invalid")
    attestations: dict[str, dict[str, Any]] = {}
    raw_hash_count = 0
    reuse_count = 0
    for raw_entry in entries:
        if not isinstance(raw_entry, Mapping):
            raise RuntimeError("sparse_tick_prewarm_attestation_entry_invalid")
        entry = dict(raw_entry)
        validation = entry.get("source_validation")
        validation = (
            dict(validation) if isinstance(validation, Mapping) else {}
        )
        source_path = Path(str(entry.get("source_path") or ""))
        source_sha256 = str(entry.get("source_sha256") or "")
        status = str(validation.get("status") or "")
        raw_hash_performed = entry.get("raw_source_full_hash_performed") is True
        sealed_reused = entry.get("sealed_cache_reused") is True
        build_valid = (
            status == "FULL_SOURCE_SHA256_VALIDATED_DURING_SINGLE_PASS_BUILD"
            and raw_hash_performed
            and not sealed_reused
        )
        reuse_valid = (
            status
            == "SEALED_CACHE_REUSED_AFTER_EXACT_SOURCE_STAT_AND_PARTITION_VALIDATION"
            and sealed_reused
            and not raw_hash_performed
        )
        try:
            current_stat = _regular_source_stat_identity(source_path)
        except RuntimeError:
            current_stat = {}
        if (
            not source_path.is_absolute()
            or len(source_sha256) != 64
            or any(char not in "009abcdef" for char in source_sha256)
            or str(validation.get("manifest_sha256") or "") != source_sha256
            or validation.get("source_stat_identity") != current_stat
            or not (build_valid or reuse_valid)
            or len(str(entry.get("identity_root_sha256") or "")) != 64
            or len(str(entry.get("manifest_root_sha256") or "")) != 64
        ):
            raise RuntimeError("sparse_tick_prewarm_attestation_entry_invalid")
        path_key = str(source_path.resolve())
        if path_key in attestations:
            raise RuntimeError("sparse_tick_prewarm_attestation_path_duplicate")
        attestations[path_key] = entry
        raw_hash_count += int(raw_hash_performed)
        reuse_count += int(sealed_reused)
    if (
        raw_hash_count != int(receipt.get("raw_source_full_hash_count") or 0)
        or reuse_count != int(receipt.get("sealed_cache_reuse_count") or 0)
    ):
        raise RuntimeError("sparse_tick_prewarm_attestation_count_invalid")
    return attestations


def _attested_tick_source_sha256(
    *,
    path: Path,
    expected_sha256: str,
    integrity_attestations: Mapping[str, Mapping[str, Any]],
) -> str | None:
    try:
        entry = integrity_attestations.get(str(path.resolve()))
        if not isinstance(entry, Mapping):
            return None
        validation = entry.get("source_validation")
        if not isinstance(validation, Mapping):
            return None
        if (
            str(entry.get("source_sha256") or "") != expected_sha256
            or str(validation.get("manifest_sha256") or "") != expected_sha256
            or validation.get("source_stat_identity")
            != _regular_source_stat_identity(path)
        ):
            return None
        return expected_sha256
    except (OSError, RuntimeError):
        return None


class ConflictCheckedLazyTickRowsByDay:
    """Merge lazy tick components and fail closed on cross-source quote drift."""

    lookup_mode = "lazy_tick_window_stream_cross_source_conflict_checked"

    def __init__(
        self,
        *,
        symbol: str,
        specs: Iterable[SourceSpec],
        sparse_cache_root: Path | None = None,
        sparse_window_start: datetime | None = None,
        sparse_window_end: datetime | None = None,
    ) -> None:
        self.symbol = symbol
        self.specs = tuple(specs)
        use_sparse_cache = (
            sparse_cache_root is not None
            and sparse_window_start is not None
            and sparse_window_end is not None
        )
        self._delegates = tuple(
            (
                spec,
                SparseTickWindowRowsByDay(
                    symbol=symbol,
                    spec=spec,
                    cache_root=Path(sparse_cache_root),
                    window_start=sparse_window_start,
                    window_end=sparse_window_end,
                )
                if use_sparse_cache
                else LazyTickRowsByDay(symbol=symbol, specs=(spec,)),
            )
            for spec in self.specs
        )
        self.last_validation_events: tuple[dict[str, Any], ...] = ()

    @staticmethod
    def _tick_value(value: Any) -> Any:
        if value in (None, ""):
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return str(value)
        return number if math.isfinite(number) else str(value)

    @classmethod
    def _quote_tuple(cls, row: Mapping[str, Any]) -> tuple[Any, Any, Any]:
        return (
            cls._tick_value(row.get("bid")),
            cls._tick_value(row.get("ask")),
            cls._tick_value(row.get("last")),
        )

    def query(
        self,
        *,
        after: datetime,
        until: datetime,
    ) -> tuple[tuple[dict[str, Any], ...], list[str]]:
        rows: list[dict[str, Any]] = []
        days: set[str] = set()
        validation_events: list[dict[str, Any]] = []
        seen_rows: set[tuple[Any, ...]] = set()
        prior_quotes_by_timestamp: dict[str, set[tuple[Any, Any, Any]]] = {}
        prior_paths_by_timestamp: dict[str, set[str]] = defaultdict(set)
        for spec, delegate in self._delegates:
            component_rows, component_days = delegate.query(
                after=after,
                until=until,
            )
            validation_events.extend(delegate.last_validation_events)
            days.update(component_days)
            local_quotes_by_timestamp: dict[
                str, set[tuple[Any, Any, Any]]
            ] = defaultdict(set)
            for row in component_rows:
                ts = parse_row_time(row)
                if ts is None:
                    continue
                timestamp = iso(ts) or str(
                    row.get("time_utc") or row.get("ts_utc") or row.get("time")
                )
                quote = self._quote_tuple(row)
                local_quotes_by_timestamp[timestamp].add(quote)
                row_key = (
                    timestamp,
                    *quote,
                    self._tick_value(row.get("volume")),
                )
                if row_key not in seen_rows:
                    seen_rows.add(row_key)
                    rows.append(dict(row))
            for timestamp, local_quotes in local_quotes_by_timestamp.items():
                prior_quotes = prior_quotes_by_timestamp.get(timestamp)
                if prior_quotes is not None and local_quotes != prior_quotes:
                    prior_paths = sorted(prior_paths_by_timestamp[timestamp])
                    self.last_validation_events = tuple(validation_events)
                    raise RuntimeError(
                        "conflicting_overlapping_tick_observations:"
                        f"{self.symbol}:{timestamp}:"
                        f"prior_paths={prior_paths}:current_path={spec.path}"
                    )
                prior_quotes_by_timestamp.setdefault(timestamp, set()).update(
                    local_quotes
                )
                prior_paths_by_timestamp[timestamp].add(str(spec.path))
        rows.sort(
            key=lambda row: str(
                row.get("time_utc") or row.get("ts_utc") or row.get("time")
            )
        )
        self.last_validation_events = tuple(validation_events)
        return tuple(rows), sorted(days)

    def get(self, day: str, default: Any = None) -> Any:
        try:
            start = datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        except ValueError:
            return default
        rows, _days = self.query(
            after=start - timedelta(microseconds=1),
            until=start + timedelta(days=1),
        )
        return rows or default

    def release_completed_days(self, days: Iterable[str]) -> int:
        return sum(
            int(delegate.release_completed_days(days))
            for _spec, delegate in self._delegates
            if hasattr(delegate, "release_completed_days")
        )

    def release_all_loaded_days(self) -> int:
        return sum(
            int(delegate.release_all_loaded_days())
            for _spec, delegate in self._delegates
            if hasattr(delegate, "release_all_loaded_days")
        )


class BroadSourceResolver:
    def __init__(
        self,
        *,
        use_native_h1: bool = False,
        skip_tick_source: bool = False,
        verbose: bool = False,
        source_accelerator: Any | None = None,
        physical_source_reference: Any | None = None,
        bound_tick_source_specs: Mapping[str, Sequence[SourceSpec]] | None = None,
        bound_tick_source_gaps: Mapping[str, Sequence[str]] | None = None,
        bound_tick_logical_repo_root: Path | None = None,
        sealed_tick_full_component_set: bool = False,
        tick_sparse_cache_root: Path | None = None,
        tick_sparse_window_start: datetime | None = None,
        tick_sparse_window_end: datetime | None = None,
    ) -> None:
        self._file_cache: dict[
            str, tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]
        ] = {}
        self._day_file_cache: dict[
            tuple[str, tuple[str, ...]],
            tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str],
        ] = {}
        self._htf_cache: dict[tuple[str, str, tuple[str, ...]], ResolvedSource] = {}
        self._tick_cache: dict[
            tuple[str, tuple[str, ...]], ResolvedSource | None
        ] = {}
        self.source_rows: list[dict[str, Any]] = []
        self.source_row_keys: set[tuple[str, str, str, str, str, str]] = set()
        self.use_native_h1 = use_native_h1
        self.skip_tick_source = skip_tick_source
        self.verbose = verbose
        self.source_accelerator = source_accelerator
        self.physical_source_reference = physical_source_reference
        if (
            self.source_accelerator is not None
            and self.physical_source_reference is not None
        ):
            raise ValueError("source_loader_modes_are_mutually_exclusive")
        self.bound_tick_source_specs = (
            {
                str(symbol): tuple(specs)
                for symbol, specs in bound_tick_source_specs.items()
            }
            if bound_tick_source_specs is not None
            else None
        )
        self.bound_tick_source_gaps = {
            str(symbol): tuple(str(gap) for gap in gaps)
            for symbol, gaps in (bound_tick_source_gaps or {}).items()
        }
        self.bound_tick_logical_repo_root = (
            Path(bound_tick_logical_repo_root).resolve()
            if bound_tick_logical_repo_root is not None
            else None
        )
        self.sealed_tick_full_component_set = bool(
            sealed_tick_full_component_set
        )
        if self.sealed_tick_full_component_set and self.bound_tick_source_specs is None:
            raise ValueError("sealed_tick_full_component_set_specs_missing")
        self.tick_sparse_cache_root = (
            Path(tick_sparse_cache_root).resolve()
            if tick_sparse_cache_root is not None
            else None
        )
        self.tick_sparse_window_start = tick_sparse_window_start
        self.tick_sparse_window_end = tick_sparse_window_end

    def load_file(
        self,
        path: Path,
        *,
        symbol: str,
    ) -> tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]:
        key = str(path)
        if key not in self._file_cache:
            source_loader = (
                self.source_accelerator or self.physical_source_reference
            )
            if source_loader is not None:
                self._file_cache[key] = source_loader.load_file(
                    path, symbol=symbol
                )
            else:
                rows = load_csv_rows(path, symbol=symbol)
                self._file_cache[key] = (rows, rows_by_day(rows), file_sha256(path))
        return self._file_cache[key]

    def load_file_days(
        self,
        path: Path,
        *,
        symbol: str,
        days: Iterable[str],
    ) -> tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str]:
        day_key = tuple(sorted(set(days)))
        key = (str(path), day_key)
        if key not in self._day_file_cache:
            source_loader = (
                self.source_accelerator or self.physical_source_reference
            )
            if source_loader is not None:
                self._day_file_cache[key] = source_loader.load_file_days(
                    path,
                    symbol=symbol,
                    days=day_key,
                )
                return self._day_file_cache[key]
            day_set = set(day_key)
            grouped: dict[str, list[dict[str, Any]]] = {day: [] for day in day_key}
            if path.exists() and day_set:
                max_day = day_key[-1]
                seen_target_day = False
                with path.open("r", newline="", encoding="utf-8") as handle:
                    for raw in csv.DictReader(handle):
                        row = normalize_row(raw, symbol=symbol)
                        if row is None:
                            continue
                        ts = parse_row_time(row)
                        if ts is None:
                            continue
                        day = ts.astimezone(timezone.utc).date().isoformat()
                        if day in day_set:
                            grouped[day].append(row)
                            seen_target_day = True
                            continue
                        if seen_target_day and day > max_day:
                            break
            sorted_grouped = {
                day: tuple(
                    sorted(
                        items,
                        key=lambda item: str(item.get("time_utc") or item.get("time") or ""),
                    )
                )
                for day, items in grouped.items()
            }
            rows = tuple(row for day in day_key for row in sorted_grouped.get(day, ()))
            self._day_file_cache[key] = (rows, sorted_grouped, file_sha256(path))
        return self._day_file_cache[key]

    def load_file_replay_lookback_window(
        self,
        path: Path,
        *,
        symbol: str,
        timeframe: str,
        days: Iterable[str],
        min_total_rows: int,
    ) -> tuple[tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str, dict[str, Any]]:
        day_key = tuple(sorted(set(days)))
        key = (str(path), timeframe, day_key)
        if key not in self._day_file_cache:
            source_loader = (
                self.source_accelerator or self.physical_source_reference
            )
            if source_loader is not None:
                self._day_file_cache[key] = (
                    source_loader.load_file_replay_lookback_window(
                        path,
                        symbol=symbol,
                        timeframe=timeframe,
                        days=day_key,
                        min_total_rows=min_total_rows,
                    )
                )
                return self._day_file_cache[key]
            if not day_key or not path.exists():
                metadata = {
                    "source_hash_scope": "missing_or_unbounded_source_file",
                    "bounded_replay_lookback_start_day": None,
                    "bounded_replay_lookback_end_day": None,
                    "bounded_replay_row_count": 0,
                }
                self._day_file_cache[key] = ((), {}, stable_sha256(metadata), metadata)
                return self._day_file_cache[key]
            minutes_per_row = {
                "D1": 24 * 60,
                "H4": 4 * 60,
                "H1": 60,
                "M15": 15,
            }.get(str(timeframe).upper(), 15)
            required_rows = max(
                int(min_total_rows),
                int(DEFAULT_LOOKBACKS.get(str(timeframe).upper(), min_total_rows) or 0),
            )
            lookback_days = max(
                1,
                math.ceil((max(required_rows, 1) * minutes_per_row) / (24 * 60)),
            )
            first_day = date.fromisoformat(day_key[0])
            last_day = date.fromisoformat(day_key[-1])
            start_day = first_day - timedelta(days=lookback_days + 2)
            # Include a small forward coverage buffer so weekend/no-session
            # tail days do not make a bounded source slice look absent. The
            # replay still filters decision inputs by as-of time.
            end_day = last_day + timedelta(days=3)
            pre_window_rows: deque[dict[str, Any]] = deque(
                maxlen=max(required_rows + 2, int(min_total_rows) + 2)
            )
            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            rows: list[dict[str, Any]] = []
            seen_window = False
            with path.open("r", newline="", encoding="utf-8") as handle:
                for raw in csv.DictReader(handle):
                    row = normalize_row(raw, symbol=symbol)
                    if row is None:
                        continue
                    ts = parse_row_time(row)
                    if ts is None:
                        continue
                    row_day = ts.astimezone(timezone.utc).date()
                    if row_day < first_day:
                        pre_window_rows.append(row)
                        continue
                    if row_day > end_day:
                        if seen_window:
                            break
                        continue
                    rows.append(row)
                    grouped[row_day.isoformat()].append(row)
                    seen_window = True
            rows = list(pre_window_rows) + rows
            for row in pre_window_rows:
                ts = parse_row_time(row)
                if ts is None:
                    continue
                grouped[ts.astimezone(timezone.utc).date().isoformat()].append(row)
            sorted_grouped = {
                day: tuple(
                    sorted(
                        items,
                        key=lambda item: str(item.get("time_utc") or item.get("time") or ""),
                    )
                )
                for day, items in grouped.items()
            }
            rows_tuple = tuple(
                sorted(rows, key=lambda item: str(item.get("time_utc") or item.get("time") or ""))
            )
            metadata = {
                "source_hash_scope": (
                    "bounded_replay_lookback_slice_not_full_historical_file_hash"
                ),
                "bounded_replay_lookback_start_day": start_day.isoformat(),
                "bounded_replay_lookback_end_day": end_day.isoformat(),
                "bounded_replay_requested_days": list(day_key),
                "bounded_replay_min_total_rows": int(min_total_rows),
                "bounded_replay_required_live_lookback_rows": required_rows,
                "bounded_replay_prewindow_selected_rows": len(pre_window_rows),
                "bounded_replay_source_selection_mode": (
                    "count_preserving_predecision_lookback_slice"
                ),
                "bounded_replay_row_count": len(rows_tuple),
                "bounded_replay_source_path": str(path),
            }
            sha256 = stable_sha256(
                {
                    **metadata,
                    "first_last": row_time_bounds(rows_tuple),
                    "rows": rows_tuple,
                }
            )
            self._day_file_cache[key] = (rows_tuple, sorted_grouped, sha256, metadata)
        cached = self._day_file_cache[key]
        if len(cached) == 3:
            rows, grouped, sha256 = cached
            return rows, grouped, sha256, {
                "source_hash_scope": "legacy_day_file_cache_full_file_hash"
            }
        return cached

    def emit_source_row(self, row: Mapping[str, Any]) -> None:
        key = (
            str(row.get("symbol")),
            str(row.get("timeframe")),
            str(row.get("source_path")),
            str(row.get("trading_day") or ""),
            str(row.get("row_type")),
            str(row.get("source_authority_scope_id") or ""),
        )
        if key in self.source_row_keys:
            return
        self.source_row_keys.add(key)
        self.source_rows.append(dict(row))

    def drain_source_rows(self) -> list[dict[str, Any]]:
        rows = list(self.source_rows)
        self.source_rows.clear()
        return rows

    def reset_source_row_emission(self) -> dict[str, Any]:
        """Discard preparation-only emission state before canonical proof."""

        discarded_rows = len(self.source_rows)
        discarded_keys = len(self.source_row_keys)
        self.source_rows.clear()
        self.source_row_keys.clear()
        return {
            "discarded_preparation_rows": discarded_rows,
            "discarded_preparation_keys": discarded_keys,
            "source_or_economic_payload_changed": False,
        }

    def cache_counts(self) -> dict[str, int]:
        return {
            "file": len(self._file_cache),
            "day_file": len(self._day_file_cache),
            "htf": len(self._htf_cache),
            "tick": len(self._tick_cache),
        }

    def release_completed_chunk_caches(
        self,
        days: Iterable[str],
        *,
        source_authority_days: Iterable[str] = (),
    ) -> dict[str, Any]:
        """Release hydrated execution and immutable-authority source slices."""

        day_key = tuple(sorted(set(str(day) for day in days)))
        authority_day_key = tuple(
            sorted(set(str(day) for day in source_authority_days))
        )
        releasable_day_keys = {day_key}
        if authority_day_key:
            releasable_day_keys.add(authority_day_key)
        before = self.cache_counts()
        replay_source_cache_before = replay_source_cache_counts()
        day_file_keys = [
            key
            for key in self._day_file_cache
            if isinstance(key, tuple) and key and key[-1] in releasable_day_keys
        ]
        htf_keys = [
            key
            for key in self._htf_cache
            if isinstance(key, tuple) and key and key[-1] in releasable_day_keys
        ]
        released_day_file_rows = 0
        for key in day_file_keys:
            cached = self._day_file_cache.pop(key)
            rows = cached[0] if cached else ()
            released_day_file_rows += len(rows)
        released_htf_rows = 0
        for key in htf_keys:
            source = self._htf_cache.pop(key)
            released_htf_rows += len(source.rows)
        for source in self._tick_cache.values():
            if source is None or not hasattr(
                source.rows_by_day, "release_completed_days"
            ):
                continue
            source.rows_by_day.release_completed_days(day_key)
        clear_replay_source_caches()
        replay_source_cache_after = replay_source_cache_counts()
        replay_source_cache_entries_remaining = sum(
            replay_source_cache_after.values()
        )
        after = self.cache_counts()
        return {
            "requested_days": list(day_key),
            "execution_chunk_days": list(day_key),
            "source_authority_days": list(authority_day_key),
            "before": before,
            "after": after,
            "released_day_file_entries": len(day_file_keys),
            "released_day_file_rows": released_day_file_rows,
            "released_htf_entries": len(htf_keys),
            "released_htf_rows": released_htf_rows,
            "persistent_tick_source_entries": after["tick"],
            "persistent_full_file_entries": after["file"],
            "replay_source_cache_before": replay_source_cache_before,
            "replay_source_cache_after": replay_source_cache_after,
            "completed_replay_source_cache_entries_remaining": (
                replay_source_cache_entries_remaining
            ),
            "completed_replay_source_caches_released": (
                replay_source_cache_entries_remaining == 0
            ),
            "completed_chunk_day_scoped_entries_remaining": sum(
                1
                for key in self._day_file_cache
                if isinstance(key, tuple)
                and key
                and key[-1] in releasable_day_keys
            )
            + sum(
                1
                for key in self._htf_cache
                if isinstance(key, tuple)
                and key
                and key[-1] in releasable_day_keys
            ),
            "completed_source_authority_scoped_entries_remaining": sum(
                1
                for key in self._day_file_cache
                if authority_day_key
                and isinstance(key, tuple)
                and key
                and key[-1] == authority_day_key
            )
            + sum(
                1
                for key in self._htf_cache
                if authority_day_key
                and isinstance(key, tuple)
                and key
                and key[-1] == authority_day_key
            ),
        }

    def release_all_loaded_tick_days(self) -> int:
        """Drop only parsed tick partitions, preserving bound source wrappers."""

        released = 0
        for source in self._tick_cache.values():
            if source is None or not hasattr(
                source.rows_by_day, "release_all_loaded_days"
            ):
                continue
            released += int(source.rows_by_day.release_all_loaded_days())
        return released

    def resolve_file_source(
        self,
        *,
        symbol: str,
        timeframe: str,
        root_order: Iterable[str],
        min_total_rows: int,
        requested_days: Iterable[str] = (),
    ) -> ResolvedSource | None:
        day_key = tuple(sorted(set(requested_days)))
        authority_scope = source_authority_scope(day_key)
        cache_key = (symbol, timeframe, day_key)
        if cache_key in self._htf_cache:
            return self._htf_cache[cache_key]
        family_order = tuple(root_order)
        source_selector = (
            self.source_accelerator or self.physical_source_reference
        )
        if source_selector is not None:
            source_candidates = tuple(
                (
                    candidate.source_family,
                    candidate.mapped_symbol,
                    candidate.source_path,
                )
                for candidate in source_selector.accepted_source_candidates(
                    symbol=symbol,
                    physical_timeframe=timeframe,
                    source_family_order=family_order,
                )
            )
        else:
            source_candidates = tuple(
                (family, mapped_symbol, path)
                for family in family_order
                for root in data_roots()
                for mapped_symbol in symbol_aliases(symbol)
                if (
                    path := root / family / f"{mapped_symbol}_{timeframe}.csv"
                ).exists()
            )
        saw_file = bool(source_candidates)
        # Search family-first so the declared source priority remains stable.
        # Under attempt-5 acceleration these are bundle-committed logical paths;
        # source bytes are opened only through the accepted cache lease.
        for family, mapped_symbol, path in source_candidates:
            if day_key:
                rows, grouped, sha256, source_slice_metadata = (
                    self.load_file_replay_lookback_window(
                        path,
                        symbol=symbol,
                        timeframe=timeframe,
                        days=day_key,
                        min_total_rows=min_total_rows,
                    )
                )
            else:
                rows, grouped, sha256 = self.load_file(path, symbol=symbol)
                source_slice_metadata = {
                    "source_hash_scope": "full_historical_file_hash"
                }
            covers_requested_range, start_utc, end_utc = source_covers_requested_range(
                rows,
                day_key,
            )
            status = "selected_source_meets_floor"
            if len(rows) < min_total_rows:
                status = "selected_source_below_floor"
            elif not covers_requested_range:
                status = "selected_source_missing_requested_replay_range"
            self.emit_source_row(
                {
                    "row_type": "source_selection",
                    "symbol": symbol,
                    "mapped_symbol": mapped_symbol,
                    "timeframe": timeframe,
                    "source_path": str(path),
                    "source_family": family,
                    "source_broker": "FTMO",
                    "source_role": "owner_authorized_research_hydration",
                    "rows": len(rows),
                    "min_required_rows": min_total_rows,
                    "requested_replay_days": list(day_key),
                    "requested_start_day": day_key[0] if day_key else None,
                    "requested_end_day": day_key[-1] if day_key else None,
                    "source_authority_scope_mode": authority_scope["mode"],
                    "source_authority_scope_id": authority_scope["scope_id"],
                    "source_authority_start_day": authority_scope["start_day"],
                    "source_authority_end_day": authority_scope["end_day"],
                    "source_authority_day_count": authority_scope["day_count"],
                    "source_start_utc": start_utc,
                    "source_end_utc": end_utc,
                    "requested_range_covered": covers_requested_range,
                    "sha256": sha256,
                    **source_slice_metadata,
                    "status": status,
                    "derived": False,
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "live_broker_authority": False,
                    "broker_mutation_enabled": False,
                    "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                }
            )
            if len(rows) < min_total_rows or not covers_requested_range:
                continue
            source = ResolvedSource(
                spec=source_spec_for_rows(
                    symbol=symbol,
                    mapped_symbol=mapped_symbol,
                    timeframe=timeframe,
                    path=path,
                    source_family=family,
                    rows=rows,
                    sha256=sha256,
                ),
                rows=rows,
                rows_by_day=grouped,
                sha256=sha256,
                day_counts={day: len(items) for day, items in grouped.items()},
                selected_status=status,
                min_required_rows_per_day=min_total_rows,
                source_gaps=(),
                component_source_labels=(
                    {
                        "symbol": symbol,
                        "mapped_symbol": mapped_symbol,
                        "timeframe": timeframe,
                        "source_path": str(path),
                        "source_family": family,
                        "row_count": len(rows),
                        "rows": len(rows),
                        "sha256": sha256,
                        **source_slice_metadata,
                        "selected_status": status,
                        "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    },
                ),
            )
            self._htf_cache[cache_key] = source
            return source
        self.emit_source_row(
            {
                "row_type": "source_gap",
                "symbol": symbol,
                "timeframe": timeframe,
                "status": "missing_source_file" if not saw_file else "no_source_covers_requested_replay_range",
                "requested_replay_days": list(day_key),
                "requested_start_day": day_key[0] if day_key else None,
                "requested_end_day": day_key[-1] if day_key else None,
                "source_authority_scope_mode": authority_scope["mode"],
                "source_authority_scope_id": authority_scope["scope_id"],
                "source_authority_start_day": authority_scope["start_day"],
                "source_authority_end_day": authority_scope["end_day"],
                "source_authority_day_count": authority_scope["day_count"],
                "searched_roots": [str(path) for path in data_roots()],
                "searched_families": list(root_order),
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
        return None

    def resolve_m15(
        self,
        symbol: str,
        *,
        requested_days: Iterable[str] = (),
    ) -> ResolvedSource | None:
        return self.resolve_file_source(
            symbol=symbol,
            timeframe="M15",
            root_order=M15_ROOT_ORDER,
            min_total_rows=M15_LIVE_LOOKBACK_MIN_TOTAL_ROWS,
            requested_days=requested_days,
        )

    def resolve_h1(
        self,
        symbol: str,
        m15_source: ResolvedSource,
        *,
        requested_days: Iterable[str] = (),
    ) -> ResolvedSource:
        authority_scope = source_authority_scope(requested_days)
        authority_days = tuple(authority_scope["days"])
        if self.use_native_h1:
            native = self.resolve_file_source(
                symbol=symbol,
                timeframe="H1",
                root_order=H1_ROOT_ORDER,
                min_total_rows=HTF_MIN_TOTAL_ROWS["H1"],
                requested_days=authority_days,
            )
            if native is not None:
                return native
        rows = aggregate_h1_from_m15(m15_source.rows, symbol=symbol)
        grouped = rows_by_day(rows)
        sha256 = stable_sha256(
            {
                "derivation": "h1_from_m15_hourly_ohlcv",
                "component_sha256": m15_source.sha256,
                "component_path": str(m15_source.spec.path),
                "row_count": len(rows),
                "first_last": row_time_bounds(rows),
            }
        )
        spec = source_spec_for_rows(
            symbol=symbol,
            mapped_symbol=m15_source.spec.mapped_symbol,
            timeframe="H1",
            path=m15_source.spec.path,
            source_family=f"derived_h1_from_{m15_source.spec.source_family}",
            rows=rows,
            sha256=sha256,
            source_role="source_bound_derived_h1_from_m15",
        )
        component_label = {
            "symbol": symbol,
            "mapped_symbol": m15_source.spec.mapped_symbol,
            "timeframe": "H1",
            "component_timeframe": "M15",
            "component_source_path": str(m15_source.spec.path),
            "component_sha256": m15_source.sha256,
            "derivation": "hourly_ohlcv_aggregation_from_source_bound_m15",
            "source_truth_scope": SOURCE_TRUTH_SCOPE,
        }
        self.emit_source_row(
            {
                "row_type": "source_selection",
                "symbol": symbol,
                "mapped_symbol": m15_source.spec.mapped_symbol,
                "timeframe": "H1",
                "source_path": str(m15_source.spec.path),
                "source_family": spec.source_family,
                "source_broker": "FTMO",
                "source_role": spec.source_role,
                "rows": len(rows),
                "min_required_rows": HTF_MIN_TOTAL_ROWS["H1"],
                "sha256": sha256,
                "status": "selected_source_bound_derived_h1_from_m15",
                "derived": True,
                "component_source_path": str(m15_source.spec.path),
                "component_sha256": m15_source.sha256,
                "requested_replay_days": list(authority_days),
                "requested_start_day": authority_scope["start_day"],
                "requested_end_day": authority_scope["end_day"],
                "source_authority_scope_mode": authority_scope["mode"],
                "source_authority_scope_id": authority_scope["scope_id"],
                "source_authority_start_day": authority_scope["start_day"],
                "source_authority_end_day": authority_scope["end_day"],
                "source_authority_day_count": authority_scope["day_count"],
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
        return ResolvedSource(
            spec=spec,
            rows=rows,
            rows_by_day=grouped,
            sha256=sha256,
            day_counts={day: len(items) for day, items in grouped.items()},
            selected_status="selected_source_bound_derived_h1_from_m15",
            min_required_rows_per_day=HTF_MIN_TOTAL_ROWS["H1"],
            component_source_labels=(component_label,),
        )

    def resolve_static_sources(
        self,
        symbol: str,
        *,
        requested_days: Iterable[str] = (),
    ) -> dict[str, ResolvedSource] | None:
        m15 = self.resolve_m15(symbol, requested_days=requested_days)
        d1 = self.resolve_file_source(
            symbol=symbol,
            timeframe="D1",
            root_order=D1_ROOT_ORDER,
            min_total_rows=HTF_MIN_TOTAL_ROWS["D1"],
            requested_days=requested_days,
        )
        h4 = self.resolve_file_source(
            symbol=symbol,
            timeframe="H4",
            root_order=H4_ROOT_ORDER,
            min_total_rows=HTF_MIN_TOTAL_ROWS["H4"],
            requested_days=requested_days,
        )
        if m15 is None or d1 is None or h4 is None:
            return None
        h1 = self.resolve_h1(symbol, m15, requested_days=requested_days)
        return {"D1": d1, "H4": h4, "H1": h1, "M15": m15}

    def resolve_tick(
        self,
        symbol: str,
        *,
        source_authority_days: Iterable[str] = (),
    ) -> ResolvedSource | None:
        day_key = tuple(sorted(set(str(day) for day in source_authority_days)))
        cache_key = (symbol, day_key)
        if cache_key in self._tick_cache:
            return self._tick_cache[cache_key]
        authority_scope = source_authority_scope(day_key)
        window_start = (
            datetime.combine(
                date.fromisoformat(day_key[0]),
                datetime.min.time(),
                tzinfo=timezone.utc,
            )
            if day_key
            else None
        )
        window_end = (
            datetime.combine(
                date.fromisoformat(day_key[-1]),
                datetime.min.time(),
                tzinfo=timezone.utc,
            )
            + timedelta(days=1)
            if day_key
            else None
        )
        merged_gaps: list[str] = []
        candidates: list[tuple[int, SourceSpec]] = []
        if self.bound_tick_source_specs is None:
            repo_roots = tuple(dict.fromkeys((ROOT, MAIN_REPO_ROOT)))
            scanned_repo_roots = repo_roots
        elif self.sealed_tick_full_component_set:
            repo_roots = ()
            scanned_repo_roots = ()
        else:
            if self.bound_tick_logical_repo_root is None:
                raise ValueError("bound_tick_logical_repo_root_missing")
            repo_roots = tuple(
                dict.fromkeys(
                    (MAIN_REPO_ROOT, self.bound_tick_logical_repo_root)
                )
            )
            scanned_repo_roots = (MAIN_REPO_ROOT,)
        for root_index, repo_root in enumerate(scanned_repo_roots):
            tick, gaps = resolve_ftmo_tick_source(symbol, repo_root=repo_root)
            merged_gaps.extend(gaps)
            if tick is None:
                continue
            tick_specs = getattr(tick.rows_by_day, "specs", ())
            for spec in tick_specs:
                if not isinstance(spec, SourceSpec):
                    continue
                start = parse_utc(spec.start_utc)
                end = parse_utc(spec.end_utc)
                if day_key and (start is None or end is None):
                    merged_gaps.append(
                        f"{spec.path}:tick_declared_interval_missing_or_invalid"
                    )
                    continue
                if (
                    window_start is not None
                    and window_end is not None
                    and not (start < window_end and end >= window_start)
                ):
                    continue
                candidates.append((root_index, spec))
        merged_gaps.extend(self.bound_tick_source_gaps.get(symbol, ()))
        if self.bound_tick_source_specs is not None:
            bound_root_index = len(scanned_repo_roots)
            for spec in self.bound_tick_source_specs.get(symbol, ()):
                start = parse_utc(spec.start_utc)
                end = parse_utc(spec.end_utc)
                if day_key and (start is None or end is None):
                    raise ValueError(
                        f"bound_tick_declared_interval_invalid:{spec.path}"
                    )
                if (
                    not self.sealed_tick_full_component_set
                    and
                    window_start is not None
                    and window_end is not None
                    and not (start < window_end and end >= window_start)
                ):
                    continue
                candidates.append((bound_root_index, spec))
        candidates.sort(
            key=lambda item: (
                item[0],
                str(item[1].start_utc or ""),
                str(item[1].end_utc or ""),
                str(item[1].sha256 or ""),
                str(item[1].path),
            )
        )
        selected_by_sha: dict[str, SourceSpec] = {}
        for _root_index, spec in candidates:
            sha = str(spec.sha256 or "")
            if not sha:
                merged_gaps.append(f"{spec.path}:tick_sha256_missing")
                continue
            selected_by_sha.setdefault(sha, spec)
        selected_specs = tuple(
            sorted(
                selected_by_sha.values(),
                key=lambda spec: (
                    str(spec.start_utc or ""),
                    str(spec.end_utc or ""),
                    str(spec.sha256 or ""),
                    str(spec.path),
                ),
            )
        )
        if selected_specs:
            first_spec = selected_specs[0]
            start_values = [
                str(spec.start_utc) for spec in selected_specs if spec.start_utc
            ]
            end_values = [
                str(spec.end_utc) for spec in selected_specs if spec.end_utc
            ]
            total_rows = sum(int(spec.row_count or 0) for spec in selected_specs)
            combined_sha = stable_sha256(
                {
                    "symbol": symbol,
                    "timeframe": "TICK",
                    "components": [
                        {
                            "path": str(spec.path),
                            "sha256": spec.sha256,
                            "rows": spec.row_count,
                        }
                        for spec in selected_specs
                    ],
                }
            )
            day_counts: dict[str, int] = defaultdict(int)
            for spec in selected_specs:
                start = parse_utc(spec.start_utc)
                if start is not None:
                    day_counts[start.date().isoformat()] += int(
                        spec.row_count or 0
                    )
            labels = tuple(
                {
                    **spec.__dict__,
                    "path": str(spec.path),
                    "rows": spec.row_count,
                    "row_count": spec.row_count,
                    "sha256": spec.sha256,
                    "source_sha256": spec.sha256,
                    "ordered_tick_truth_satisfied": True,
                    "broker_lifecycle_truth_satisfied": False,
                    "selected_status": "selected_priority_tick_source",
                    "tick_window_label": Path(spec.path).stem,
                    "sha_validation_status": "deferred_until_lazy_window_load",
                }
                for spec in selected_specs
            )
            tick = ResolvedSource(
                spec=SourceSpec(
                    symbol=symbol,
                    mapped_symbol=first_spec.mapped_symbol,
                    timeframe="TICK",
                    path=Path(f"combined_ftmo_tick_sources/{symbol}_TICK"),
                    source_family="ftmo_mt5_priority_tick_exports",
                    source_broker="FTMO",
                    source_role=first_spec.source_role,
                    start_utc=min(start_values) if start_values else None,
                    end_utc=max(end_values) if end_values else None,
                    row_count=total_rows,
                    sha256=combined_sha,
                    export_tool="scripts/export_mt5_research_ticks.py",
                    manifest_path="multiple_priority_tick_ftmo_manifests",
                    source_server_redacted=first_spec.source_server_redacted,
                    source_server_hash=first_spec.source_server_hash,
                    source_account_redacted=first_spec.source_account_redacted,
                    source_account_hash=first_spec.source_account_hash,
                    source_truth_scope=SOURCE_TRUTH_SCOPE,
                    not_redacted_account_native=True,
                    broker_lifecycle_truth_satisfied=False,
                    ordered_tick_truth_satisfied=True,
                ),
                rows=(),
                rows_by_day=ConflictCheckedLazyTickRowsByDay(
                    symbol=symbol,
                    specs=selected_specs,
                    sparse_cache_root=self.tick_sparse_cache_root,
                    sparse_window_start=self.tick_sparse_window_start,
                    sparse_window_end=self.tick_sparse_window_end,
                ),
                sha256=combined_sha,
                day_counts=dict(day_counts),
                selected_status="selected_priority_tick_sources_lazy_window_load",
                min_required_rows_per_day=1,
                # Rejected or missing components outside this authority window
                # are search diagnostics, not gaps in the selected source.
                source_gaps=(),
                component_source_labels=labels,
            )
            self._tick_cache[cache_key] = tick
            for label in labels:
                row = dict(label)
                row.update(
                    {
                        "row_type": "tick_symbol_source",
                        "symbol": symbol,
                        "timeframe": "TICK",
                        "status": row.get("selected_status")
                        or "selected_priority_tick_sources_lazy_window_load",
                        "source_path": str(row.get("path") or tick.spec.path),
                        "requested_replay_days": list(day_key),
                        "requested_start_day": authority_scope["start_day"],
                        "requested_end_day": authority_scope["end_day"],
                        "source_authority_scope_mode": authority_scope["mode"],
                        "source_authority_scope_id": authority_scope["scope_id"],
                        "source_authority_start_day": authority_scope["start_day"],
                        "source_authority_end_day": authority_scope["end_day"],
                        "source_authority_day_count": authority_scope["day_count"],
                        "live_broker_authority": False,
                        "broker_mutation_enabled": False,
                        "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                    }
                )
                self.emit_source_row(row)
            return tick
        self._tick_cache[cache_key] = None
        self.emit_source_row(
            {
                "row_type": "tick_symbol_source_gap",
                "symbol": symbol,
                "timeframe": "TICK",
                "status": (
                    "no_ftmo_tick_source_overlaps_requested_authority_window"
                    if day_key and candidates == []
                    else "missing_ftmo_tick_source"
                ),
                "searched_repo_roots": [str(root) for root in repo_roots],
                "requested_replay_days": list(day_key),
                "requested_start_day": authority_scope["start_day"],
                "requested_end_day": authority_scope["end_day"],
                "source_authority_scope_mode": authority_scope["mode"],
                "source_authority_scope_id": authority_scope["scope_id"],
                "source_authority_start_day": authority_scope["start_day"],
                "source_authority_end_day": authority_scope["end_day"],
                "source_authority_day_count": authority_scope["day_count"],
                "source_gaps": list(dict.fromkeys(merged_gaps)),
                "ordered_tick_truth_satisfied": False,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
        )
        return None

    def m1_source_candidates(
        self,
        *,
        symbol: str,
        month: str,
        days: Iterable[str],
    ) -> tuple[
        tuple[
            Path,
            str,
            str,
            tuple[dict[str, Any], ...],
            dict[str, tuple[dict[str, Any], ...]],
            str,
        ],
        ...,
    ]:
        month_days = tuple(day for day in days if month_key(day) == month)
        families = (
            f"{M1_MONTH_PREFIX}{month}",
            *M1_SUPPLEMENTAL_ROOT_ORDER_BY_MONTH.get(month, ()),
        )
        candidates: list[
            tuple[
                Path,
                str,
                str,
                tuple[dict[str, Any], ...],
                dict[str, tuple[dict[str, Any], ...]],
                str,
            ]
        ] = []
        seen_paths: set[str] = set()
        source_selector = (
            self.source_accelerator or self.physical_source_reference
        )
        if source_selector is not None:
            source_candidates = tuple(
                (
                    candidate.source_family,
                    candidate.mapped_symbol,
                    candidate.source_path,
                )
                for candidate in source_selector.accepted_source_candidates(
                    symbol=symbol,
                    physical_timeframe="M1",
                    source_family_order=families,
                )
            )
        else:
            source_candidates = tuple(
                (family, mapped_symbol, path)
                for family in families
                for root in data_roots()
                for mapped_symbol in symbol_aliases(symbol)
                if (path := root / family / f"{mapped_symbol}_M1.csv").exists()
            )
        for family, mapped_symbol, path in source_candidates:
            if str(path) in seen_paths:
                continue
            seen_paths.add(str(path))
            rows, grouped, sha256 = self.load_file_days(
                path,
                symbol=symbol,
                days=month_days,
            )
            candidates.append(
                (path, mapped_symbol, family, rows, grouped, sha256)
            )
        return tuple(candidates)

    def month_rows(
        self,
        *,
        symbol: str,
        month: str,
        days: Iterable[str],
    ) -> tuple[Path | None, tuple[dict[str, Any], ...], dict[str, tuple[dict[str, Any], ...]], str | None]:
        candidates = self.m1_source_candidates(
            symbol=symbol,
            month=month,
            days=days,
        )
        for path, _mapped_symbol, _family, rows, grouped, sha256 in candidates:
            if rows:
                return path, rows, grouped, sha256
        if candidates:
            path, _mapped_symbol, _family, rows, grouped, sha256 = candidates[0]
            return path, rows, grouped, sha256
        return None, (), {}, None

    def resolve_m1_for_days(
        self,
        *,
        symbol: str,
        days: tuple[str, ...],
        m15_source: ResolvedSource,
    ) -> ResolvedSource | None:
        merged_rows: list[dict[str, Any]] = []
        grouped_rows: dict[str, tuple[dict[str, Any], ...]] = {}
        day_counts: dict[str, int] = {}
        component_labels: list[dict[str, Any]] = []
        components_for_sha: list[dict[str, Any]] = []
        day_source_authority: dict[str, dict[str, Any]] = {}
        first_path: Path | None = None
        below_floor_days: list[str] = []
        below_floor_details: list[dict[str, Any]] = []
        candidates_by_month = {
            month: self.m1_source_candidates(
                symbol=symbol,
                month=month,
                days=days,
            )
            for month in sorted({month_key(day) for day in days})
        }
        for day in days:
            candidates = candidates_by_month.get(month_key(day), ())
            populated = [
                candidate
                for candidate in candidates
                if candidate[4].get(day, ())
            ]
            day_hashes = {
                stable_sha256(candidate[4].get(day, ())): candidate
                for candidate in populated
            }
            if len(day_hashes) > 1:
                conflict_paths = [str(candidate[0]) for candidate in populated]
                self.emit_source_row(
                    {
                        "row_type": "m1_source_overlap_validation",
                        "symbol": symbol,
                        "timeframe": "M1",
                        "trading_day": day,
                        "status": "m1_source_overlap_conflict",
                        "source_path": conflict_paths[0],
                        "candidate_source_paths": conflict_paths,
                        "candidate_day_sha256": sorted(day_hashes),
                        "source_truth_scope": SOURCE_TRUTH_SCOPE,
                        "live_broker_authority": False,
                        "broker_mutation_enabled": False,
                        "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                    }
                )
                raise ValueError(
                    "m1_source_overlap_conflict:"
                    f"{symbol}:{day}:{'|'.join(conflict_paths)}"
                )
            selected = populated[0] if populated else (candidates[0] if candidates else None)
            if selected is None:
                path = None
                mapped_symbol = symbol
                family = None
                rows_for_day: tuple[dict[str, Any], ...] = ()
                sha256 = None
            else:
                path, mapped_symbol, family, _rows, grouped, sha256 = selected
                rows_for_day = grouped.get(day, ())
            if path is not None and first_path is None:
                first_path = path
            if len(populated) > 1:
                self.emit_source_row(
                    {
                        "row_type": "m1_source_overlap_validation",
                        "symbol": symbol,
                        "timeframe": "M1",
                        "trading_day": day,
                        "status": "m1_source_overlap_consistent",
                        "source_path": str(path),
                        "source_family": family,
                        "candidate_source_paths": [
                            str(candidate[0]) for candidate in populated
                        ],
                        "candidate_day_sha256": next(iter(day_hashes), None),
                        "source_truth_scope": SOURCE_TRUTH_SCOPE,
                        "live_broker_authority": False,
                        "broker_mutation_enabled": False,
                        "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                    }
                )
            m15_day_rows = len(m15_source.rows_by_day.get(day, ()))
            authority = m1_symbol_day_source_authority(
                symbol=symbol,
                trading_day=day,
                m1_row_count=len(rows_for_day),
                m15_row_count=m15_day_rows,
                source_day_sha256=stable_sha256(rows_for_day),
                source_path=str(path) if path is not None else None,
                source_family=family,
                source_file_sha256=sha256,
            )
            status = str(authority["status"])
            no_session = status == "ftmo_verified_no_session_day"
            if authority["diagnostic_fallback_only"] is True:
                below_floor_days.append(day)
                below_floor_details.append({"trading_day": day, **authority})
            day_source_authority[day] = dict(authority)
            merged_rows.extend(rows_for_day)
            grouped_rows[day] = rows_for_day
            day_counts[day] = len(rows_for_day)
            label = {
                "symbol": symbol,
                "mapped_symbol": mapped_symbol,
                "timeframe": "M1",
                "trading_day": day,
                "path": str(path) if path is not None else None,
                "source_path": str(path) if path is not None else None,
                "source_family": family,
                "source_broker": "FTMO",
                "source_role": "owner_authorized_research_hydration",
                "row_count": len(rows_for_day),
                "rows": len(rows_for_day),
                "m15_day_rows": m15_day_rows,
                "sha256": sha256,
                "candidate_source_count": len(candidates),
                "populated_candidate_source_count": len(populated),
                "source_overlap_consistent": len(day_hashes) <= 1,
                "source_session_status": authority.get(
                    "source_session_status"
                ),
                "no_session_reference": (
                    "m1_and_m15_zero_rows_for_symbol_day" if no_session else None
                ),
                "diagnostic_fallback_only": authority.get(
                    "diagnostic_fallback_only"
                ),
                "source_gaps": list(authority.get("source_gaps") or ()),
                "absolute_min_rows": authority.get("absolute_min_rows"),
                "session_scaled_min_rows": authority.get(
                    "session_scaled_min_rows"
                ),
                "effective_min_rows": authority.get("effective_min_rows"),
                "expected_m1_rows_from_m15_session": authority.get(
                    "expected_m1_rows_from_m15_session"
                ),
                "m1_to_m15_expected_coverage_ratio": authority.get(
                    "m1_to_m15_expected_coverage_ratio"
                ),
                "session_scaled_floor_applied": authority.get(
                    "session_scaled_floor_applied"
                ),
                "source_day_authority_id": authority.get(
                    "source_day_authority_id"
                ),
                "source_day_authority_hash_sha256": authority.get(
                    "source_day_authority_hash_sha256"
                ),
                "path_replay_allowed": authority.get("path_replay_allowed"),
                "terminal_lifecycle_close_allowed": authority.get(
                    "terminal_lifecycle_close_allowed"
                ),
                "source_truth_scope": SOURCE_TRUTH_SCOPE,
                "not_redacted_account_native": True,
                "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            }
            component_labels.append(label)
            components_for_sha.append(
                {
                    "day": day,
                    "path": str(path) if path is not None else None,
                    "sha256": sha256,
                    "rows": len(rows_for_day),
                    "m15_rows": m15_day_rows,
                    "status": status,
                    "effective_min_rows": authority.get("effective_min_rows"),
                    "diagnostic_fallback_only": authority.get(
                        "diagnostic_fallback_only"
                    ),
                    "source_day_authority_hash_sha256": authority.get(
                        "source_day_authority_hash_sha256"
                    ),
                }
            )
            self.emit_source_row(
                {
                    "row_type": "m1_symbol_day_source",
                    "symbol": symbol,
                    "timeframe": "M1",
                    "trading_day": day,
                    "source_path": str(path) if path is not None else None,
                    "source_family": family,
                    "rows": len(rows_for_day),
                    "min_required_rows": authority.get("effective_min_rows"),
                    "m15_day_rows": m15_day_rows,
                    "sha256": sha256,
                    "candidate_source_count": len(candidates),
                    "populated_candidate_source_count": len(populated),
                    "source_overlap_consistent": len(day_hashes) <= 1,
                    "status": status,
                    "source_session_status": authority.get(
                        "source_session_status"
                    ),
                    "diagnostic_fallback_only": authority.get(
                        "diagnostic_fallback_only"
                    ),
                    "source_gaps": list(authority.get("source_gaps") or ()),
                    "absolute_min_rows": authority.get("absolute_min_rows"),
                    "session_scaled_min_rows": authority.get(
                        "session_scaled_min_rows"
                    ),
                    "effective_min_rows": authority.get("effective_min_rows"),
                    "expected_m1_rows_from_m15_session": authority.get(
                        "expected_m1_rows_from_m15_session"
                    ),
                    "m1_to_m15_expected_coverage_ratio": authority.get(
                        "m1_to_m15_expected_coverage_ratio"
                    ),
                    "session_scaled_floor_applied": authority.get(
                        "session_scaled_floor_applied"
                    ),
                    "source_day_authority_id": authority.get(
                        "source_day_authority_id"
                    ),
                    "source_day_authority_hash_sha256": authority.get(
                        "source_day_authority_hash_sha256"
                    ),
                    "path_replay_allowed": authority.get(
                        "path_replay_allowed"
                    ),
                    "terminal_lifecycle_close_allowed": authority.get(
                        "terminal_lifecycle_close_allowed"
                    ),
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "live_broker_authority": False,
                    "broker_mutation_enabled": False,
                    "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                }
            )
        source_gaps: list[str] = []
        selected_status = "selected_composite_m1_days_for_broad_live_as_if_replay"
        if below_floor_days:
            source_gaps.append(
                "m1_requested_symbol_days_below_session_scaled_floor"
            )
            session_days = [
                row
                for row in day_source_authority.values()
                if row.get("status") != "ftmo_verified_no_session_day"
            ]
            selected_status = (
                "selected_m1_all_session_days_diagnostic_path_proxy_required"
                if session_days
                and all(
                    row.get("diagnostic_fallback_only") is True
                    for row in session_days
                )
                else "selected_composite_m1_days_with_symbol_day_scoped_gaps"
            )
            self.emit_source_row(
                {
                    "row_type": "source_gap",
                    "symbol": symbol,
                    "timeframe": "M1",
                    "status": (
                        "m1_requested_symbol_days_below_session_scaled_floor"
                    ),
                    "requested_replay_days": list(days),
                    "below_floor_days": below_floor_days,
                    "below_floor_details": below_floor_details,
                    "absolute_min_rows": M1_MIN_ROWS_PER_DAY,
                    "session_scaled_floor_ratio": (
                        M1_MIN_SESSION_COVERAGE_RATIO
                    ),
                    "source_truth_scope": SOURCE_TRUTH_SCOPE,
                    "live_broker_authority": False,
                    "broker_mutation_enabled": False,
                    "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
                }
            )
        sha = stable_sha256(components_for_sha)
        spec_rows = tuple(merged_rows)
        spec = source_spec_for_rows(
            symbol=symbol,
            mapped_symbol=symbol,
            timeframe="M1",
            path=first_path or Path(f"missing_m1_for_{symbol}"),
            source_family="monthly_m1_bridge_ftmo_research_exports",
            rows=spec_rows,
            sha256=sha,
        )
        return ResolvedSource(
            spec=spec,
            rows=spec_rows,
            rows_by_day=grouped_rows,
            sha256=sha,
            day_counts=day_counts,
            selected_status=selected_status,
            min_required_rows_per_day=M1_MIN_ROWS_PER_DAY,
            # Symbol-day dispositions are authoritative. Aggregate gaps would
            # contaminate valid days in multi-day source objects.
            source_gaps=(),
            component_source_labels=tuple(component_labels),
            day_source_authority=day_source_authority,
        )

    def build_sources_for_days(
        self,
        days: tuple[str, ...],
        *,
        symbols: tuple[str, ...] | None = None,
        source_authority_days: tuple[str, ...] | None = None,
    ) -> dict[str, dict[str, ResolvedSource]]:
        execution_days = tuple(sorted(set(days)))
        authority_days = tuple(
            sorted(set(source_authority_days or execution_days))
        )
        if not execution_days:
            raise ValueError("execution_chunk_days_empty")
        if not set(execution_days).issubset(authority_days):
            raise ValueError(
                "execution_chunk_outside_source_authority_scope:"
                f"execution={execution_days}:authority={authority_days}"
            )
        sources: dict[str, dict[str, ResolvedSource]] = {}
        for symbol in (symbols or GTOS_24_SYMBOL_SURFACE):
            if self.verbose:
                print(
                    f"[source] execution={execution_days[0]}:{execution_days[-1]} "
                    f"authority={authority_days[0]}:{authority_days[-1]} {symbol}",
                    flush=True,
                )
            static = self.resolve_static_sources(
                symbol,
                requested_days=authority_days,
            )
            if static is None:
                continue
            m1 = self.resolve_m1_for_days(
                symbol=symbol,
                days=execution_days,
                m15_source=static["M15"],
            )
            tick = (
                None
                if self.skip_tick_source
                else self.resolve_tick(
                    symbol,
                    source_authority_days=authority_days,
                )
            )
            source_map = {**static, "M1": m1}
            if tick is not None:
                source_map["TICK"] = tick
            sources[symbol] = source_map
        return sources


def darwin_allocator_pressure_relief() -> int:
    """Return free malloc-zone pages to Darwin without touching live objects."""

    if sys.platform != "darwin":
        return 0
    try:
        pressure_relief = ctypes.CDLL(None).malloc_zone_pressure_relief
        pressure_relief.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
        pressure_relief.restype = ctypes.c_size_t
        return int(pressure_relief(None, 0))
    except (AttributeError, OSError, TypeError, ValueError):
        return 0


def reclaim_runtime_memory_pressure(
    resolver: BroadSourceResolver,
) -> dict[str, int]:
    """Release reloadable rows and allocator pages before capacity resampling."""

    released_loaded_tick_rows = resolver.release_all_loaded_tick_days()
    clear_replay_source_caches()
    replay_entries_remaining = sum(replay_source_cache_counts().values())
    gc_collected_objects = gc.collect()
    allocator_released_bytes = darwin_allocator_pressure_relief()
    return {
        "released_loaded_tick_rows": int(released_loaded_tick_rows),
        "replay_source_cache_entries_remaining": int(replay_entries_remaining),
        "gc_collected_objects": int(gc_collected_objects),
        "allocator_released_bytes": int(allocator_released_bytes),
    }


def tick_window_source_authority(
    *,
    symbol: str,
    source: ResolvedSource | None,
    source_authority_days: Iterable[str],
    integrity_attestations: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Bind tick components to the selected window with file integrity proof."""

    days = tuple(sorted(set(str(day) for day in source_authority_days)))
    components: list[dict[str, Any]] = []
    intervals: list[tuple[datetime, datetime]] = []
    integrity_failures: list[str] = []
    seen_paths: set[str] = set()
    labels = source.component_source_labels if source is not None else ()
    for label in labels:
        path = Path(str(label.get("path") or label.get("source_path") or ""))
        path_key = str(path)
        if not path_key or path_key in seen_paths:
            continue
        seen_paths.add(path_key)
        start = parse_utc(label.get("start_utc"))
        end = parse_utc(label.get("end_utc"))
        expected_sha = str(
            label.get("sha256") or label.get("source_sha256") or ""
        )
        actual_sha = (
            _attested_tick_source_sha256(
                path=path,
                expected_sha256=expected_sha,
                integrity_attestations=integrity_attestations,
            )
            if integrity_attestations is not None
            else file_sha256_cached(path) if path.is_file() else None
        )
        hash_matches = bool(actual_sha and expected_sha == actual_sha)
        manifest_path = Path(str(label.get("manifest_path") or ""))
        manifest_sha = (
            file_sha256_cached(manifest_path)
            if manifest_path.is_file()
            else None
        )
        if not hash_matches:
            integrity_failures.append(
                f"{path_key}:tick_file_hash_missing_or_mismatch"
            )
        if label.get("manifest_path") and manifest_sha is None:
            integrity_failures.append(
                f"{label.get('manifest_path')}:tick_manifest_missing"
            )
        if start is not None and end is not None and end >= start:
            intervals.append((start, end))
        components.append(
            {
                "source_path": path_key,
                "source_start_utc": iso(start),
                "source_end_utc": iso(end),
                "row_count": int(
                    label.get("row_count") or label.get("rows") or 0
                ),
                "expected_sha256": expected_sha or None,
                "actual_sha256": actual_sha,
                "sha256_matches_manifest": hash_matches,
                "manifest_path": str(label.get("manifest_path") or "")
                or None,
                "manifest_sha256": manifest_sha,
            }
        )
    components.sort(key=lambda row: str(row.get("source_path")))
    covered_days = []
    for day in days:
        day_start = datetime.combine(
            date.fromisoformat(day), datetime.min.time(), tzinfo=timezone.utc
        )
        day_end = day_start + timedelta(days=1)
        if any(start < day_end and end >= day_start for start, end in intervals):
            covered_days.append(day)
    status = (
        "covered"
        if days and len(covered_days) == len(days)
        else "partial"
        if covered_days
        else "none"
    )
    payload = {
        "symbol": symbol,
        "timeframe": "TICK",
        "window_start_day": days[0] if days else None,
        "window_end_day": days[-1] if days else None,
        "window_day_count": len(days),
        "status": status,
        "covered_day_count": len(covered_days),
        "covered_days": covered_days,
        "component_count": len(components),
        "components": components,
        "integrity_valid": not integrity_failures,
        "integrity_failures": integrity_failures,
        "ordered_tick_truth_scope": (
            "window_interval_and_file_integrity_bound_not_broker_lifecycle_truth"
        ),
    }
    return {
        **payload,
        "tick_window_authority_digest_sha256": stable_sha256(payload),
    }


def static_source_authority_plan(
    *,
    sources: Mapping[str, Mapping[str, ResolvedSource]],
    source_authority_days: Iterable[str],
    requested_symbols: Iterable[str],
    tick_integrity_attestations: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Hash static, M1 symbol-day, and tick-window source authority."""

    authority_scope = source_authority_scope(source_authority_days)
    symbols = tuple(sorted(set(str(symbol) for symbol in requested_symbols)))
    source_rows: list[dict[str, Any]] = []
    static_source_rows: list[dict[str, Any]] = []
    m1_symbol_day_authority_rows: list[dict[str, Any]] = []
    tick_window_authority_rows: list[dict[str, Any]] = []
    missing_symbols: list[str] = []
    incomplete_sources: list[str] = []
    for symbol in symbols:
        source_map = sources.get(symbol)
        if not isinstance(source_map, Mapping):
            missing_symbols.append(symbol)
            continue
        for timeframe in STATIC_SOURCE_AUTHORITY_TIMEFRAMES:
            source = source_map.get(timeframe)
            if source is None:
                incomplete_sources.append(f"{symbol}:{timeframe}")
                continue
            static_row = {
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "mapped_symbol": source.spec.mapped_symbol,
                    "source_path": str(source.spec.path),
                    "source_family": source.spec.source_family,
                    "source_role": source.spec.source_role,
                    "row_count": int(source.spec.row_count or len(source.rows)),
                    "source_start_utc": source.spec.start_utc,
                    "source_end_utc": source.spec.end_utc,
                    "sha256": source.sha256,
                    "selected_status": source.selected_status,
                    "source_gaps": list(source.source_gaps),
                }
            static_source_rows.append(static_row)
            source_rows.append(static_row)
        m1 = source_map.get("M1")
        if m1 is None:
            incomplete_sources.append(f"{symbol}:M1")
        else:
            source_rows.append(
                {
                    "symbol": symbol,
                    "timeframe": "M1",
                    "mapped_symbol": m1.spec.mapped_symbol,
                    "source_path": str(m1.spec.path),
                    "source_family": m1.spec.source_family,
                    "source_role": m1.spec.source_role,
                    "row_count": int(m1.spec.row_count or len(m1.rows)),
                    "source_start_utc": m1.spec.start_utc,
                    "source_end_utc": m1.spec.end_utc,
                    "sha256": m1.sha256,
                    "selected_status": m1.selected_status,
                    "source_gaps": [],
                    "day_source_authority_count": len(
                        m1.day_source_authority
                    ),
                }
            )
            for day in authority_scope["days"]:
                authority = m1.day_source_authority.get(day)
                if not isinstance(authority, Mapping):
                    incomplete_sources.append(f"{symbol}:M1:{day}")
                    continue
                m1_symbol_day_authority_rows.append(dict(authority))
        tick = source_map.get("TICK")
        tick_authority = tick_window_source_authority(
            symbol=symbol,
            source=tick,
            source_authority_days=authority_scope["days"],
            integrity_attestations=tick_integrity_attestations,
        )
        tick_window_authority_rows.append(tick_authority)
        if tick is not None:
            source_rows.append(
                {
                    "symbol": symbol,
                    "timeframe": "TICK",
                    "mapped_symbol": tick.spec.mapped_symbol,
                    "source_path": str(tick.spec.path),
                    "source_family": tick.spec.source_family,
                    "source_role": tick.spec.source_role,
                    "row_count": int(tick.spec.row_count or len(tick.rows)),
                    "source_start_utc": tick.spec.start_utc,
                    "source_end_utc": tick.spec.end_utc,
                    "sha256": tick.sha256,
                    "selected_status": tick.selected_status,
                    "source_gaps": list(tick.source_gaps),
                }
            )
    source_rows.sort(
        key=lambda row: (str(row.get("symbol")), str(row.get("timeframe")))
    )
    static_source_rows.sort(
        key=lambda row: (str(row.get("symbol")), str(row.get("timeframe")))
    )
    m1_symbol_day_authority_rows.sort(
        key=lambda row: (
            str(row.get("symbol")),
            str(row.get("trading_day")),
        )
    )
    tick_window_authority_rows.sort(key=lambda row: str(row.get("symbol")))
    m1_authority_ids = [
        str(row.get("source_day_authority_id") or "")
        for row in m1_symbol_day_authority_rows
    ]
    expected_static_rows = len(symbols) * len(STATIC_SOURCE_AUTHORITY_TIMEFRAMES)
    expected_m1_day_rows = len(symbols) * int(authority_scope["day_count"])
    unresolved_m1_day_rows = [
        {
            "symbol": row.get("symbol"),
            "trading_day": row.get("trading_day"),
            "status": row.get("status"),
            "source_gaps": row.get("source_gaps"),
        }
        for row in m1_symbol_day_authority_rows
        if row.get("diagnostic_fallback_only") is True
    ]
    tick_integrity_failures = [
        str(row.get("symbol"))
        for row in tick_window_authority_rows
        if row.get("integrity_valid") is not True
    ]
    static_source_digest = stable_sha256(static_source_rows)
    m1_day_plan_digest = stable_sha256(m1_symbol_day_authority_rows)
    tick_window_plan_digest = stable_sha256(tick_window_authority_rows)
    tick_component_source_digest = stable_sha256(
        [
            {
                "symbol": row.get("symbol"),
                "components": row.get("components"),
            }
            for row in tick_window_authority_rows
        ]
    )
    digest_payload = {
        "source_authority_scope": authority_scope,
        "requested_symbols": list(symbols),
        "missing_symbols": missing_symbols,
        "incomplete_sources": incomplete_sources,
        "static_source_digest_sha256": static_source_digest,
        "m1_day_plan_digest_sha256": m1_day_plan_digest,
        "tick_window_plan_digest_sha256": tick_window_plan_digest,
        "tick_component_source_digest_sha256": tick_component_source_digest,
    }
    valid = bool(
        authority_scope["days"]
        and len(sources) == len(symbols)
        and not missing_symbols
        and not incomplete_sources
        and len(static_source_rows) == expected_static_rows
        and len(m1_symbol_day_authority_rows) == expected_m1_day_rows
        and len(set(m1_authority_ids)) == expected_m1_day_rows
        and not unresolved_m1_day_rows
        and not tick_integrity_failures
    )
    return {
        "schema": "gtos.final_moonshot.broad_replay.source_authority_plan.v2",
        "status": (
            "valid_static_source_authority_plan"
            if valid
            else "invalid_static_source_authority_plan"
        ),
        "valid": valid,
        "source_authority_scope": authority_scope,
        "requested_symbols": list(symbols),
        "requested_symbol_count": len(symbols),
        "resolved_symbol_count": len(sources),
        "missing_symbols": missing_symbols,
        "incomplete_sources": incomplete_sources,
        "source_row_count": len(source_rows),
        "expected_static_source_row_count": expected_static_rows,
        "static_source_row_count": len(static_source_rows),
        "expected_m1_symbol_day_authority_row_count": expected_m1_day_rows,
        "m1_symbol_day_authority_row_count": len(
            m1_symbol_day_authority_rows
        ),
        "m1_symbol_day_authority_unique_id_count": len(set(m1_authority_ids)),
        "m1_unresolved_symbol_day_count": len(unresolved_m1_day_rows),
        "m1_unresolved_symbol_days": unresolved_m1_day_rows,
        "tick_window_authority_row_count": len(tick_window_authority_rows),
        "tick_window_integrity_failure_symbols": tick_integrity_failures,
        "static_source_digest_sha256": static_source_digest,
        "m1_day_plan_digest_sha256": m1_day_plan_digest,
        "tick_window_plan_digest_sha256": tick_window_plan_digest,
        "tick_component_source_digest_sha256": tick_component_source_digest,
        "plan_digest_sha256": stable_sha256(digest_payload),
        "source_rows": source_rows,
        "static_source_rows": static_source_rows,
        "m1_symbol_day_authority_rows": m1_symbol_day_authority_rows,
        "tick_window_authority_rows": tick_window_authority_rows,
    }


def source_authority_chunk_checkpoint(
    *,
    profile: str,
    split: str,
    execution_days: Iterable[str],
    source_plan: Mapping[str, Any],
    canonical_plan: Mapping[str, Any] | None,
) -> dict[str, Any]:
    canonical = canonical_plan or source_plan
    authority_scope = canonical.get("source_authority_scope")
    authority_scope = (
        authority_scope if isinstance(authority_scope, Mapping) else {}
    )
    execution_key = tuple(sorted(set(str(day) for day in execution_days)))
    authority_key = tuple(str(day) for day in authority_scope.get("days") or ())
    canonical_digest = str(canonical.get("plan_digest_sha256") or "")
    canonical_m1 = {
        (str(row.get("symbol")), str(row.get("trading_day"))): str(
            row.get("source_day_authority_hash_sha256") or ""
        )
        for row in canonical.get("m1_symbol_day_authority_rows") or ()
        if isinstance(row, Mapping)
        and str(row.get("trading_day")) in execution_key
    }
    chunk_m1 = {
        (str(row.get("symbol")), str(row.get("trading_day"))): str(
            row.get("source_day_authority_hash_sha256") or ""
        )
        for row in source_plan.get("m1_symbol_day_authority_rows") or ()
        if isinstance(row, Mapping)
    }
    expected_m1_subset_digest = stable_sha256(
        sorted(canonical_m1.items())
    )
    actual_m1_subset_digest = stable_sha256(sorted(chunk_m1.items()))
    static_sources_match = bool(
        source_plan.get("static_source_digest_sha256")
        and source_plan.get("static_source_digest_sha256")
        == canonical.get("static_source_digest_sha256")
    )
    tick_sources_match = bool(
        source_plan.get("tick_component_source_digest_sha256")
        and source_plan.get("tick_component_source_digest_sha256")
        == canonical.get("tick_component_source_digest_sha256")
    )
    m1_subset_matches = bool(canonical_m1 and canonical_m1 == chunk_m1)
    plan_matches = bool(
        static_sources_match and tick_sources_match and m1_subset_matches
    )
    return {
        "profile": profile,
        "split": split,
        "execution_days": list(execution_key),
        "source_authority_scope_mode": authority_scope.get("mode"),
        "source_authority_scope_id": authority_scope.get("scope_id"),
        "source_authority_days": list(authority_key),
        "source_authority_start_day": authority_scope.get("start_day"),
        "source_authority_end_day": authority_scope.get("end_day"),
        "source_authority_day_count": authority_scope.get("day_count"),
        "execution_days_subset_of_source_authority": set(execution_key).issubset(
            authority_key
        ),
        "source_plan_valid": source_plan.get("valid") is True,
        # This field is acceptance authority, not a digest of the transient
        # execution-day projection.  Every checkpoint therefore carries the
        # same full-window source-plan digest bound by the sealed contract.
        "source_plan_digest_sha256": canonical_digest,
        "canonical_source_plan_digest_sha256": canonical_digest,
        "source_plan_matches_canonical": plan_matches,
        "static_sources_match_canonical": static_sources_match,
        "tick_component_sources_match_canonical": tick_sources_match,
        "m1_execution_day_authority_matches_canonical": m1_subset_matches,
        "expected_m1_execution_day_authority_digest_sha256": (
            expected_m1_subset_digest
        ),
        "actual_m1_execution_day_authority_digest_sha256": (
            actual_m1_subset_digest
        ),
        "expected_m1_execution_day_authority_row_count": len(canonical_m1),
        "actual_m1_execution_day_authority_row_count": len(chunk_m1),
        "source_plan_source_row_count": int(source_plan.get("source_row_count") or 0),
        "source_plan_resolved_symbol_count": int(
            source_plan.get("resolved_symbol_count") or 0
        ),
        "source_plan_missing_symbols": list(source_plan.get("missing_symbols") or ()),
    }


def source_covers_broad_range(source: ResolvedSource) -> bool:
    start = parse_utc(source.spec.start_utc)
    end = parse_utc(source.spec.end_utc)
    if start is None or end is None:
        return False
    return start.date() <= date.fromisoformat(DEFAULT_START) and end.date() >= date.fromisoformat(
        DEFAULT_END
    )


def aggregate_h1_from_m15(
    rows: Iterable[Mapping[str, Any]],
    *,
    symbol: str,
) -> tuple[dict[str, Any], ...]:
    buckets: dict[datetime, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        ts = parse_row_time(row)
        if ts is None:
            continue
        bucket = ts.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        buckets[bucket].append(row)
    h1_rows: list[dict[str, Any]] = []
    for bucket, items in sorted(buckets.items()):
        ordered = sorted(items, key=lambda item: parse_row_time(item) or bucket)
        h1_rows.append(
            {
                "time": iso(bucket),
                "time_utc": iso(bucket),
                "symbol": symbol,
                "open": safe_float(ordered[0].get("open")),
                "high": max(safe_float(row.get("high")) for row in ordered),
                "low": min(safe_float(row.get("low")) for row in ordered),
                "close": safe_float(ordered[-1].get("close")),
                "volume": sum(safe_float(row.get("volume")) for row in ordered),
                "source_records": len(ordered),
            }
        )
    return tuple(h1_rows)


def merge_broker_profile_cost_specs(
    base: Mapping[str, Any],
    profile_cfg: Mapping[str, Any],
) -> dict[str, Any]:
    """Merge FTMO broker specs into replay config without replacing route runtime gates."""

    output = copy.deepcopy(base)
    for key in ("profile_name", "runtime", "broker_profile", "dual_broker"):
        if key not in output and key in profile_cfg:
            output[key] = copy.deepcopy(profile_cfg[key])
    merged_instruments = copy.deepcopy(profile_cfg.get("instruments") or {})
    base_instruments = base.get("instruments") if isinstance(base.get("instruments"), Mapping) else {}
    for symbol, base_row in base_instruments.items():
        if not isinstance(base_row, Mapping):
            continue
        merged_row = merged_instruments.setdefault(str(symbol), {})
        if not isinstance(merged_row, dict):
            merged_row = {}
            merged_instruments[str(symbol)] = merged_row
        for key, value in base_row.items():
            if key == "market" and isinstance(value, Mapping):
                market = copy.deepcopy(merged_row.get("market") or {})
                # The profile is the broker/account authority.  The base route
                # still carries generic cross-broker aliases (for example
                # GER40 -> GER30 and UKOIL_cash -> UKOUSD); overwriting the
                # FTMO profile's exact mt5_symbol with those aliases makes the
                # FTMO commission lookup query the redacted_account instrument and
                # fail closed.  Retain useful route-only fields, but never let
                # them replace an exact profile market/spec field.
                for market_key, market_value in value.items():
                    market.setdefault(market_key, copy.deepcopy(market_value))
                merged_row["market"] = market
            elif key == "risk" and isinstance(value, Mapping):
                risk = copy.deepcopy(merged_row.get("risk") or {})
                for risk_key, risk_value in value.items():
                    risk.setdefault(risk_key, copy.deepcopy(risk_value))
                merged_row["risk"] = risk
            elif key not in merged_row:
                merged_row[key] = copy.deepcopy(value)
    if merged_instruments:
        output["instruments"] = merged_instruments
    output["broad_live_as_if_broker_cost_profile"] = {
        "profile_path": "config/profiles/operator_profile.yaml",
        "profile_name": profile_cfg.get("profile_name"),
        "instrument_count": len(merged_instruments),
        "runtime_gate_source": "config/agent_config.yaml",
        "broker_symbol_spec_source": "config/profiles/operator_profile.yaml",
    }
    return output


def build_config(
    profile: str,
    *,
    factorial_arm_binding: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    base = load_config(ROOT / "config/agent_config.yaml")
    broker_profile = load_config(ROOT / "config/profiles/operator_profile.yaml")
    output = merge_broker_profile_cost_specs(base, broker_profile)
    runtime = output.setdefault("gtos_vnext_runtime", {})
    if not isinstance(runtime, dict):
        runtime = {}
        output["gtos_vnext_runtime"] = runtime
    market_state = output.setdefault("market_state", {})
    if not isinstance(market_state, dict):
        market_state = {}
        output["market_state"] = market_state
    market_state["side_effect_writes_enabled"] = False
    market_state["structure_shadow_log_enabled"] = False
    market_state["replay_side_effect_boundary"] = (
        "broad_live_as_if_replay_no_production_pipeline_state_or_shadow_log_writes"
    )
    runtime["scheduler_v4_best_trade_allocator_live_activation_allowed"] = False
    runtime["scheduler_v4_best_trade_allocator_apply_to_execution"] = True
    runtime["scheduler_v4_best_trade_allocator_risk_admitted_finalizer_enabled"] = True
    runtime["broad_live_as_if_replay_enforce_broker_cost_packet_status"] = True
    runtime["broad_live_as_if_replay_pretrade_swap_cost_time_stop_bars"] = 32
    runtime["selected_cell_swap_cost_time_stop_bars"] = 32
    runtime["selected_cell_swap_cost_minutes_per_bar"] = 15
    runtime.setdefault("scheduler_v4_best_trade_allocator_calendar_no_session_breadth_guard_enabled", True)
    runtime.setdefault("scheduler_v4_best_trade_allocator_calendar_no_session_breadth_guard_min_symbols", 8)
    runtime["ultimate_candidate_package_enabled"] = True
    runtime["ultimate_candidate_package_shadow_enabled"] = True
    runtime["ultimate_candidate_package_apply_to_execution"] = True
    runtime["ultimate_candidate_package_live_activation_allowed"] = False
    runtime["ultimate_candidate_package_final_package_selected"] = False
    runtime["ultimate_candidate_package_registry_path"] = str(ULTIMATE_PACKAGE_REGISTRY_PATH)
    runtime["ultimate_candidate_package_require_shadow_match_for_selector_v4"] = True
    runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_enabled"] = False
    runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_require_admission"] = True
    runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_score_weight"] = 0.0
    runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_source_r_weight"] = 0.0
    runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_admission_weight"] = 0.0
    runtime["scheduler_v4_best_trade_allocator_ultimate_package_rank_max_boost"] = 0.0
    runtime[
        "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_demotion_reason"
    ] = (
        "disabled_until_final_package_selected_false_replay_lane_promotes_only_causal_predecision_rank_inputs"
    )
    if profile in {PROFILE_GUARDED, PROFILE_REPAIRED}:
        output = apply_ultimate_replay_loss_bucket_policy(output)
    else:
        runtime = output.setdefault("gtos_vnext_runtime", {})
        runtime["scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_enabled"] = False
        runtime["scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_policy_id"] = "disabled"
        runtime["scheduler_v4_best_trade_allocator_replay_loss_bucket_guard_rules"] = []
        runtime["profit_harvest_mfe_capture_v4_enabled"] = False
        output["ultimate_replay_loss_bucket_policy"] = {
            "policy_id": "disabled",
            "enabled": False,
            "live_broker_authority": False,
            "order_calls": 0,
        }
    runtime = output.setdefault("gtos_vnext_runtime", {})
    repaired_profile = profile == PROFILE_REPAIRED
    raw_diagnostic_profile = profile == PROFILE_RAW
    marketable_guard_profile = profile in {PROFILE_GUARDED, PROFILE_REPAIRED}
    package_execution_result_scope = (
        "raw_baseline_diagnostic_only"
        if raw_diagnostic_profile
        else "guarded_executable_package_replay"
        if profile == PROFILE_GUARDED
        else "repaired_executable_package_replay"
    )
    runtime["broad_live_as_if_replay_package_execution_result_scope"] = (
        package_execution_result_scope
    )
    selected_package_bridge_replay_materialization_enabled = bool(repaired_profile)
    runtime[
        "scheduler_v4_best_trade_allocator_selected_package_bridge_replay_materialization_enabled"
    ] = selected_package_bridge_replay_materialization_enabled
    runtime[
        "selected_package_bridge_replay_materialization_enabled"
    ] = selected_package_bridge_replay_materialization_enabled
    runtime[
        "selected_package_bridge_replay_materialization_live_broker_authority"
    ] = False
    runtime[
        "selected_package_bridge_replay_materialization_source_boundary"
    ] = (
        "local_repaired_replay_only_strict_signed_predecision_bridge_"
        "broker_live_final_closed_no_order_mutation"
        if repaired_profile
        else "closed_for_raw_guarded_comparator_profiles"
    )
    runtime[
        "selected_package_bridge_replay_materialization_status"
    ] = (
        "enabled_for_repaired_profile_after_strict_bridge_contract: producer "
        "requires source-bound executable admission, broker-calibrated PASSED cost, "
        "complete predecision quality sources, selected-policy expected-net "
        "calibration, fill/source floors, and signed package new-entry authority; "
        "raw and guarded profiles remain comparator-closed; broker/live/final false"
        if repaired_profile
        else (
            "closed_for_raw_guarded_comparator_profiles_after_bridge_proxy_"
            "open_reduced_over_admission_leak; source-bound/package bridge rows "
            "remain scoreable missed opportunities outside repaired replay"
        )
    )
    if marketable_guard_profile:
        runtime[
            "scheduler_v4_best_trade_allocator_selected_policy_expected_net_calibration_required_for_new_risk"
        ] = True
        calibration_source_path = (
            RUNTIME_EVIDENCE_ROUTE
            / "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json"
        )
        calibration_source_identity_path = (
            RUNTIME_EVIDENCE_ROUTE_IDENTITY
            / "RECONSTRUCTED_PROXY_PACKAGE_SELECTION_SUMMARY.json"
        )
        calibration_source_contract = (
            reconstructed_proxy_package_selection_source_contract(
                calibration_source_path
            )
        )
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_enabled"
        ] = calibration_source_contract.get("valid") is True
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_boundary"
        ] = (
            "local_replay_package_selection_only_final_live_closed_"
            "no_broker_order_mutation"
        )
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_path"
        ] = calibration_source_identity_path.as_posix()
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_sha256"
        ] = calibration_source_contract.get("source_semantic_sha256")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_semantic_sha256"
        ] = calibration_source_contract.get("source_semantic_sha256")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_artifact_sha256"
        ] = calibration_source_contract.get("source_artifact_sha256")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_digest_semantics"
        ] = calibration_source_contract.get("semantic_digest_boundary")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_contract_valid"
        ] = calibration_source_contract.get("valid") is True
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_contract_status"
        ] = calibration_source_contract.get("status")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_contract_failure_reasons"
        ] = list(calibration_source_contract.get("failure_reasons") or ())
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_summary_schema"
        ] = calibration_source_contract.get("source_summary_schema")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_summary_status"
        ] = calibration_source_contract.get("source_summary_status")
        runtime[
            "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_source_semantic_digest_excluded_keys"
        ] = list(
            calibration_source_contract.get("semantic_digest_excluded_keys") or ()
        )
        runtime[
            "selector_v4_router_refusal_expected_net_policy_calibration_required"
        ] = True
        runtime[
            "selector_v4_numeric_disagreement_expected_net_policy_calibration_required"
        ] = True
        runtime["selected_policy_expected_net_calibration_execution_policy"] = (
            "guarded_and_repaired_executable_profiles_require_real_selected_policy_"
            "exit_expected_net_calibration; candidate_expected_net_r_bridge_proxy_"
            "is diagnostic_missed_only"
        )
    runtime[
        "scheduler_v4_best_trade_allocator_dynamic_budget_subtract_accepted_risk_spend"
    ] = not bool(repaired_profile)
    runtime[
        "scheduler_v4_best_trade_allocator_dynamic_budget_accepted_risk_spend_policy"
    ] = (
        "repaired_no_broker_package_replay_uses_current_open_pending_risk_and_prop_"
        "headroom; cumulative accepted order spend is ledger provenance, not an "
        "additional drawdown authority debit"
        if repaired_profile
        else "raw_baseline_keeps_legacy_cumulative_accepted_spend_debit"
    )
    runtime.setdefault(
        "broad_live_as_if_replay_owner_approved_reconstructed_proxy_selected_policy_expected_net_enabled",
        False,
    )
    runtime[
        "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_zero_trade_conversion"
    ] = False
    runtime[
        "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation"
    ] = False
    if repaired_profile:
        runtime["selected_cell_pretrade_max_spread_r"] = 0.35
        runtime["selected_cell_pretrade_max_total_cost_r"] = 0.45
        runtime["selected_cell_pretrade_cost_gate_policy_reason"] = (
            "Owner-approved offline repaired replay: retain the physical spread, "
            "slippage, swap, and commission deductions, but replace the blunt "
            "0.10R/0.15R rejection ceiling with the existing measured JPY-trial "
            "0.35R/0.45R ceiling. Selector expected-net and probability gates still "
            "decide quality; live and broker authority remain false."
        )
        runtime[
            "ultimate_candidate_package_owner_approved_family_root_admission"
        ] = {
            "policy_id": "owner_xau_displacement_short_family_root_v1",
            "symbol": "XAUUSD",
            "side": "SHORT",
            "origin_family": "displacement_continuation",
            "required_sleeve_id": (
                "fpsc_scheduler_lifecycle_merge_sleeve__broader_origin__"
                "displacement_continuation__short"
            ),
            "required_registry_row_sha256": (
                "3dbe5a25b5ca98140881dd204b5189d0c032ba565c6ea9690ee3715fc7b99005"
            ),
            "required_package_role": "scheduler_lifecycle_core",
            "research_only": True,
            "live_broker_authority": False,
            "uses_outcome_fields": False,
        }
        runtime[
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_enabled"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_min_expected_net_r"
        ] = 1.00
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_numeric_disagreement_min_probability"
        ] = 0.85
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_cross_asset_lead_lag_soft_authority_enabled"
        ] = False
        runtime[
            "ultimate_candidate_package_numeric_disagreement_open_reduced_risk_demotion_reason"
        ] = (
            "BROAD_LIVE_AS_IF_REPLAY_IMMEDIATE_MARKET_COST_CEILING_SMOKE strict "
            "numeric-disagreement subset remained net negative under broker-cost, "
            "source-complete, high-probability, high-fill floors; keep numeric "
            "disagreement explicit default-off while allowing signed cross-asset "
            "router-refusal package rows through repaired replay quality, cost, "
            "and fillability gates."
        )
        runtime["selector_v4_dynamic_router_refusal_action"] = "reject"
        runtime["ultimate_candidate_package_soften_dynamic_router_refusal_enabled"] = True
        runtime[
            "ultimate_candidate_package_soften_dynamic_router_refusal_requires_broker_cost_pass"
        ] = True
        runtime[
            "ultimate_candidate_package_dynamic_router_refusal_softening_allowed_origin_families"
        ] = [
            "structural_distance_extreme",
            "session_open_range_break",
            "fvg_fill",
            "breaker_re_entry",
        ]
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_router_refusal_origin_family_gate_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_router_refusal_allowed_origin_families"
        ] = [
            "structural_distance_extreme",
            "session_open_range_break",
            "fvg_fill",
            "breaker_re_entry",
        ]
        runtime[
            "ultimate_candidate_package_dynamic_router_refusal_softening_origin_family_policy"
        ] = (
            "BROAD_LIVE_AS_IF_REPLAY_V111_SCHEDULER_FILLABILITY_TRUTH_REPAIR "
            "same-window transfer repair: keep router-refusal soft materialization "
            "on causal origin families that survived the V110B 19-day comparator "
            "or selected-bridge contract. V111 narrowed away session-open-range "
            "winners and replaced them with off-session fallback fills; restore "
            "session-open-range while leaving non-proven families scoreable/missed."
        )
        runtime["ultimate_candidate_package_replay_execution_allowed_sides"] = []
        runtime["ultimate_candidate_package_replay_execution_side_policy"] = (
            "demoted_after_BROAD_LIVE_AS_IF_REPLAY_LEDGER_TRUTH_REPAIR_SMOKE: "
            "global LONG-only replay side authority worsened completed broad "
            "headline behavior and blocked a mixed-side missed executable pool. "
            "Keep selector side-authority code available, but require a future "
            "causal symbol/session/origin/side authority before feeding a hard "
            "allowed-side list into repaired replay."
        )
        runtime["selector_v4_calibrated_admission_floor_failure_action"] = "reject"
        runtime[
            "ultimate_candidate_package_positive_predecision_router_refusal_full_trade_allowed"
        ] = True
        runtime[
            "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk_allowed"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_router_refusal_package_new_entry_authority_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_expected_net_r"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_fill_probability"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_router_refusal_replay_materialization_min_source_bound_signal_r"
        ] = 0.0
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_open_reduced_materialization_enabled"
        ] = True
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_reason"
        ] = (
            "enabled_for_repaired_profile_only_after_V20_source_bound_parity_showed_"
            "broker_cost_passed_source_complete_positive_router_refusal_rows "
            "remaining generic selector rejects. This lane materializes them as "
            "open-reduced-risk only under package admission, broker-calibrated "
            "cost pass, positive predecision edge, provenance-valid quality, "
            "and reduced-risk source-bound floors aligned to selected-policy "
            "execution fillability rather than stricter entry-fill optimism."
        )
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_expected_net_r"
        ] = 0.55
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_probability"
        ] = 0.70
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_fill_probability"
        ] = 0.55
        runtime[
            "ultimate_candidate_package_source_bound_router_refusal_materialization_min_source_completeness"
        ] = 0.95
        runtime[
            "ultimate_candidate_package_soften_selector_fill_floor_enabled"
        ] = False
        runtime[
            "ultimate_candidate_package_soften_selector_fill_floor_repair_reason"
        ] = (
            "disabled_for_V114C_B3_risk_expression_truth: selector-level "
            "fill-floor softening cannot create open-reduced package authority "
            "until scheduler/order fillability proves an executable signed route."
        )
        runtime[
            "ultimate_candidate_package_soften_selector_fill_floor_requires_broker_cost_pass"
        ] = True
        runtime[
            "ultimate_candidate_package_soften_selector_fill_floor_requires_positive_predecision_edge"
        ] = True
        runtime["selector_v4_package_session_token_authority_enabled"] = True
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_softening_enabled"
        ] = False
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_softening_repair_reason"
        ] = (
            "disabled_after_OFFSESSION_AUTHORITY_REPAIR_1D_SMOKE: configured "
            "off-session hard-blocks must dominate package softening until a "
            "causal predecision session authority proves transfer beyond the "
            "single-day BTCUSD winner without admitting the paired USDJPY/XAUUSD "
            "losses."
        )
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_min_expected_net_r"
        ] = 0.80
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_min_probability"
        ] = 0.75
        runtime[
            "ultimate_candidate_package_positive_predecision_off_session_min_fill_probability"
        ] = 0.70
        runtime["selector_v4_admission_quality_exact_block_rules_mode"] = "diagnostic"
        runtime["selector_v4_admission_quality_exact_block_rules_mode_source"] = (
            "BROAD_LIVE_AS_IF_REPLAY_PACKAGE_REGISTRY_PATH_REPAIR_SMOKE showed "
            "package-matched, broker-cost-passed, source-complete UTC/session "
            "exact-block rows still contained executable winners; demote stale "
            "historical loss/hour blocks to diagnostics inside repaired replay "
            "while broker cost, package match, scheduler, risk, and lifecycle "
            "remain authoritative."
        )
        runtime["selector_v4_repaired_profile_soft_fail_status"] = (
            "dynamic_router_refusal_softens_to_reduced_risk_for_package_admitted_broker_cost_passed_rows"
        )
        runtime[
            "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_enabled"
        ] = False
        runtime[
            "ultimate_candidate_package_broker_net_gradient_open_reduced_risk_demotion_reason"
        ] = (
            "default-off for V114C_B3: below-full-trade broker-net EV is a "
            "reduced-risk expression unless a future signed risk ladder "
            "explicitly promotes it to open-reduced replay authority."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_reserve_release_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_micro_allocation_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_micro_allocation_min_risk_pct"
        ] = 0.02
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_max_risk_pct"
        ] = 0.25
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_risk_cap_release_reason"
        ] = (
            "Release only the opening-window total-risk cap for signed, "
            "broker-cost-passed, source-bound package candidates when overall "
            "dynamic-budget headroom still exists before the opportunity reserve. "
            "This is local replay package-conversion authority, not broker/live "
            "risk authority."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_min_expected_net_r"
        ] = 0.60
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_min_probability"
        ] = 0.58
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_order_cap_release_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_order_cap_release_reason"
        ] = (
            "BROAD_LIVE_AS_IF_REPLAY_NUMERIC_PRECEDENCE_ROOT_REPAIR_SMOKE showed "
            "package-qualified, broker-cost-passed candidates still blocked by "
            "opening-window order caps after selector parity repair. Release only "
            "the opening-window order cap when the dynamic package conversion "
            "reserve packet is eligible; daily and decision-time order-cap release "
            "remain explicit flags, and portfolio, broker-cost, lifecycle, "
            "cooldown, and quality floors stay authoritative."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_expected_net_r"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_pending_collision_min_edge_delta"
        ] = 0.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_pending_collision_min_fill_probability"
        ] = 0.25
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_expected_net_r"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_lifecycle_reconcile_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_expected_net_r"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_fill_probability"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_package_opposite_side_close_reverse_router_refusal_lifecycle_reconcile_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_expected_net_r"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_package_pending_replacement_lifecycle_reconcile_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_risk_cap_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_release_max_risk_pct"
        ] = 0.25
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_zero_trade_conversion"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_zero_trade_conversion_policy_reason"
        ] = (
            "Enable local replay-only zero-trade conversion after selector/field "
            "parity repairs exposed that many package-ranked, broker-cost-passed "
            "candidates were suppressed by a zero-trade competitor. The finalizer "
            "still requires ranked scheduler eligibility, risk-bearing selector "
            "action, broker-cost pass, source-complete package quality, score "
            "floors, dynamic-budget admission, and min allocatable risk."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_allow_reallocation"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_risk_finalizer_open_reduced_reallocation_allowed"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_risk_finalizer_open_reduced_conversion_allowed"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_risk_finalizer_open_reduced_reallocation_policy_reason"
        ] = (
            "Allow local replay-only risk-finalizer reallocation into signed "
            "open-reduced package candidates after broker-cost, selector, "
            "scheduler, source-bound, and signed authority checks pass. This "
            "does not grant full-risk conversion, broker/live authority, or "
            "final-selection authority."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_package_composite_reallocation_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_package_composite_reallocation_transfer_ratio_floor"
        ] = 0.90
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_package_composite_reallocation_min_source_bound_signal_r"
        ] = 0.0
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_transfer_dominates_original_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_same_window_executable_comparator_hard_dominance_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_same_window_executable_comparator_hard_dominance_min_delta"
        ] = 0.000000001
        runtime[
            "scheduler_v4_best_trade_allocator_same_window_executable_comparator_hard_dominance_policy_reason"
        ] = (
            "V220 local replay repair: rank hard-clean, broker-cost-passed, "
            "source-complete, order-executable candidates by causal hazard-adjusted "
            "transfer value before preserving the original scheduler choice. Soft "
            "risk caps remain reduced-risk rank penalties; hard authority failures "
            "remain non-executable."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_transfer_dominates_original_ratio_floor"
        ] = 1.10
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_transfer_dominates_original_min_expected_transfer_delta"
        ] = 0.05
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_burst_guard_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_burst_guard_max_same_direction_new_positions_per_cluster"
        ] = 1
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_max_same_direction_risk_bearing_orders_per_cluster"
        ] = 2
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_max_total_risk_pct"
        ] = 0.25
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_min_expected_transfer_score"
        ] = 0.02
        runtime[
            "scheduler_v4_best_trade_allocator_same_decision_cluster_package_extra_slot_policy_reason"
        ] = (
            "Allow a second same-decision cluster/side package row only in local "
            "broker-closed replay after the row is risk-admitted, source-bound, "
            "broker-cost passed, package executable, and the combined cluster-side "
            "risk remains capped. This repairs the V83 cap-locking-winners leak "
            "without disabling the burst guard for ordinary candidates."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_risk_admitted_finalizer_reallocation_policy_reason"
        ] = (
            "Enable local replay-only reallocation after current smoke showed 96 "
            "pre-finalizer new-position windows but only 27 final entries. If an "
            "original selected candidate fails risk authority, reallocate only to "
            "the next ranked candidate that independently passes scheduler "
            "eligibility, broker-cost authority, runtime risk, lifecycle, and "
            "dynamic-budget checks."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_allow_window_headroom_reduced_new_entries"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_window_headroom_reduced_new_entry_policy_reason"
        ] = (
            "Owner-approved sizing rule: a candidate that passes selection and "
            "risk authority is sized to the remaining portfolio/cluster headroom "
            "when that headroom is above the minimum allocatable risk. The ceiling "
            "still limits correlated exposure; lack of the full requested size no "
            "longer discards an otherwise valid trade."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_quality_floor_release_enabled"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_immediate_marketable_opening_quality_floor_release_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_opening_quality_floor_release_demotion_reason"
        ] = (
            "BROAD_LIVE_AS_IF_REPLAY_OPENING_QUALITY_RELEASE_REPAIR_SMOKE "
            "regressed repaired profile from +1.94357966R to -1.96558832R; "
            "keep code diagnostic/default-off until broader causal proof."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_immediate_marketable_limit_replay_authority_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_demotion_reason"
        ] = (
            "Post selector/geometry repair, repaired profile was positive only "
            "by suppressing all marketable package entries. Enable the existing "
            "no-broker replay route under broker-cost-passed, package-policy, "
            "and strict predecision quality floors so marketable limit entries "
            "are executable in replay instead of hidden by the guard. Source-bound "
            "router-refusal immediate-marketability is released only through the "
            "signed predecision package authority and never grants broker/live "
            "or final-selection authority."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_scheduler_score"
        ] = 3.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_expected_net_r"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_expected_net_r"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_source_completeness"
        ] = 0.95
        runtime["scheduler_v4_best_trade_allocator_package_cooldown_release_enabled"] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_package_quality"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_fill_floor_authority"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_router_refusal_authority"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_allow_same_symbol_daily_loss_lockout_for_signed_executable_package_authority"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_same_symbol_daily_loss_lockout_demotion_reason"
        ] = (
            "BROAD_LIVE_AS_IF_REPLAY_SAME_SYMBOL_RELEASE_REPAIR_HOLDOUT_SWEEP "
            "showed broad same-symbol daily-loss lockout release losing on holdout. "
            "Ordinary cooldown release remains possible, broad daily-loss and "
            "package-quality daily-loss release stay closed, and only the narrow "
            "fill-floor and signed router-refusal authority paths are executable "
            "in repaired no-broker replay after strict predecision package/cost/"
            "fillability/source floors pass."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_same_symbol_daily_loss_lockout_min_abs_prior_loss_r"
        ] = 0.25
        runtime[
            "scheduler_v4_best_trade_allocator_same_symbol_daily_loss_lockout_material_loss_reason"
        ] = (
            "Do not create a same-symbol daily loss lockout from de-minimis "
            "local replay noise or tiny cost/slippage/time-stop losses. The "
            "lockout still applies after material same-symbol losses of at "
            "least 0.25R; broad release remains closed unless the existing "
            "narrow fill-floor authority release passes."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_adaptive_replay_memory_guard_allow_origin_side_axis"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_adaptive_replay_memory_guard_allow_session_origin_side_axis"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_adaptive_replay_memory_guard_axis_scope_reason"
        ] = (
            "Repaired package replay keeps adaptive memory causal, but removes "
            "the broad session_origin_side and origin_side fallback axes because "
            "they overgeneralize losses across symbols/sessions and blocked later "
            "signed package winners. Narrow symbol/session/origin axes remain active."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_scheduler_score"
        ] = 3.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_expected_net_r"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_scheduler_score"
        ] = 2.50
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_expected_net_r"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_fill_floor_authority_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_router_refusal_authority_min_scheduler_score"
        ] = 2.50
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_router_refusal_authority_min_expected_net_r"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_router_refusal_authority_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_router_refusal_authority_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_router_refusal_authority_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_signed_executable_authority_min_scheduler_score"
        ] = 2.50
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_signed_executable_authority_min_expected_net_r"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_signed_executable_authority_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_signed_executable_authority_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_cooldown_release_signed_executable_authority_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_selector_trade_only"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_scheduler_score"
        ] = 0.0
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_expected_net_r"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_min_source_completeness"
        ] = 0.65
        runtime[
            "scheduler_v4_best_trade_allocator_replay_lifecycle_action_resolver_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_reason"
        ] = (
            "Enable replay-only package authority for source_required_fail_closed "
            "scheduler lifecycle rows after the selector/source-authority smoke "
            "showed the implemented override was disabled by profile config. "
            "Broker-cost pass, source-bound package admission, expected-net, "
            "probability, fillability, and source-completeness floors remain "
            "required. The same-side scale-in floor is aligned to the repaired "
            "package reduce/open-reduced admission floor so admitted package "
            "continuation rows do not strand between selector admission and "
            "source-required lifecycle reconciliation. source_required_hold and "
            "no-same-side new-position conversion remain disabled until source "
            "repair because the May13 no-context smoke displaced stronger "
            "same-side winners."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_expected_net_r"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_fill_probability"
        ] = 0.12
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_fail_closed_package_replay_override_allow_new_position_without_same_side_context_enabled"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_enabled"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_expected_net_r"
        ] = 0.60
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_probability"
        ] = 0.72
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_fill_probability"
        ] = 0.90
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_selector_hold_package_replay_override_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_expected_net_r"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_fill_probability"
        ] = 0.12
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_same_geometry_guard_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_duplicate_scale_in_same_geometry_price_precision"
        ] = 5
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_scheduler_score"
        ] = 2.50
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_expected_net_r"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_fill_probability"
        ] = 0.12
        runtime[
            "scheduler_v4_best_trade_allocator_source_required_package_risk_lifecycle_reconcile_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_scheduler_score"
        ] = 0.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_expected_net_r"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_fill_probability"
        ] = 0.12
        runtime[
            "scheduler_v4_best_trade_allocator_package_same_direction_scale_in_lifecycle_reconcile_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_require_admission"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_score_weight"
        ] = 0.65
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_source_r_weight"
        ] = 0.35
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_admission_weight"
        ] = 0.20
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_max_boost"
        ] = 2.50
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_status"
        ] = (
            "enabled_for_local_replay_authority_repaired_profile_requires_package_"
            "admission_and_broker_cost_pass"
        )
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_source_boundary"
        ] = (
            "predecision_package_membership_selector_shadow_source_r_and_broker_cost_"
            "authority_no_outcome_fields_no_live_broker_authority"
        )
        runtime[
            "scheduler_v4_best_trade_allocator_ultimate_package_rank_boost_repair_reason"
        ] = (
            "BROAD_REPLAY_FINALIZER_RANK_5D showed repaired profile disabled the "
            "package rank boost that guarded replay used to transfer source-bound "
            "edge. Repaired replay must preserve package-rank parity while adding "
            "finalizer/reallocation repairs; broker-cost pass, source completeness, "
            "package admission, and final/live=false boundaries remain required."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_displacement_quality_gate_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_displacement_min_edge_delta"
        ] = 0.05
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_displacement_no_primary_min_edge_score"
        ] = 0.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_displacement_require_primary_comparator"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_displacement_allow_no_primary_comparator_authority"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_replay_executable_authority_overrides_router_refusal_floors"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_soft_authority_displacement_no_primary_comparator_reason"
        ] = (
            "Allow repaired local replay to materialize package soft-authority rows "
            "when no primary comparator exists only after the displacement gate "
            "verifies signed package new-entry authority and executable broker-"
            "calibrated cost. Broker/live/final remain closed."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_opportunity_cost_gate_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_min_edge_delta"
        ] = 0.05
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allow_no_new_position_comparator_authority"
        ] = bool(repaired_profile)
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_expected_net_r"
        ] = 1.00
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_probability"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_fill_probability"
        ] = 0.25
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_no_comparator_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_comparator_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_transfer_ratio_floor"
        ] = 0.90
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_allocation_comparator_policy_reason"
        ] = (
            "Lifecycle-derived package scale-ins must also clear a same-decision "
            "cluster/side allocation-quality comparator when an executable "
            "independent new-position candidate is available. This protects scarce "
            "cluster headroom from package-rank scale-ins without using outcome "
            "fields or disabling full package replay authority."
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_lifecycle_scale_in_opportunity_cost_gate_reason"
        ] = (
            "Lifecycle-derived package scale-ins are valid replay authority when "
            "they beat the best executable independent new-position candidate by "
            "a causal predecision edge margin. No-comparator scale-ins are allowed "
            "only in repaired local replay after signed package authority, broker "
            "cost pass, source-bound admission, and lifecycle no-comparator quality "
            "floors; broker/live/final remain closed."
        )
        runtime["ultimate_candidate_package_strong_fill_floor_bypass_enabled"] = True
        runtime[
            "ultimate_candidate_package_strong_fill_floor_bypass_min_expected_net_r"
        ] = 0.70
        runtime[
            "ultimate_candidate_package_strong_fill_floor_bypass_min_probability"
        ] = 0.70
        runtime[
            "ultimate_candidate_package_strong_fill_floor_bypass_min_fill_probability"
        ] = 0.20
        runtime[
            "ultimate_candidate_package_strong_fill_floor_bypass_min_execution_fill_probability"
        ] = 0.35
        runtime[
            "ultimate_candidate_package_strong_fill_floor_bypass_full_trade_allowed"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_namespace_status"
        ] = (
            "authoritative_namespace_only_legacy_dynamic_budget_package_fill_floor_bypass_removed"
        )
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_selector_trade_only"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_expected_net_r"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_fill_probability"
        ] = 0.20
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_execution_fill_probability"
        ] = 0.35
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_bypass_min_source_completeness"
        ] = 0.65
        runtime[
            "scheduler_v4_best_trade_allocator_dynamic_budget_package_fill_floor_authority_bypass_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_authority_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_expected_net_r"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_fill_probability"
        ] = 0.45
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_min_source_completeness"
        ] = 0.65
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_penalty_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_execution_fill_shortfall_score_penalty_weight"
        ] = 2.50
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_gap_weight"
        ] = 1.20
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_cost_weight"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_selector_reduce_risk_package_fill_floor_execution_drag_max_penalty"
        ] = 0.75
        runtime[
            "scheduler_v4_best_trade_allocator_package_replay_executable_authority_dominates_fill_floor"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_expected_net_r"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_fill_probability"
        ] = 0.05
        runtime[
            "scheduler_v4_best_trade_allocator_source_bound_fill_floor_replay_materialization_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_replay_executable_authority_dominates_fill_floor_status"
        ] = (
            "enabled_for_repaired_profile_only_source_bound_broker_cost_passed_"
            "package_replay_executable_authority_can_select_without_fill_floor_"
            "dominating_nonoverridable_session_origin_cost_blocks"
        )
        runtime["scheduler_v4_best_trade_allocator_fill_probability_score_weight"] = 0.90
        runtime["profit_harvest_mfe_capture_v4_enabled"] = True
        runtime["profit_harvest_mfe_capture_v4_composition_mode"] = (
            "selected_policy_only"
        )
        runtime[
            "profit_harvest_mfe_capture_v4_selected_policy_only_policy_names"
        ] = ["momentum_exhaustion"]
        runtime["profit_harvest_mfe_capture_v4_composition_mode_source"] = (
            "B7_2_EXECUTABLE_POLICY_AUTHORITY_AND_REALISM_CLOSURE preserves the "
            "causally selected momentum exit policy as terminal authority while "
            "retaining profit-harvest behavior as a scored counterfactual."
        )
        runtime["profit_harvest_mfe_capture_v4_enabled_source"] = (
            "live_like_profit_preservation_reenabled_after_fullgrid_mfe_giveback_leak"
        )
        runtime["profit_harvest_mfe_capture_v4_repair_reason"] = (
            "BROAD_LIVE_AS_IF_REPLAY_ROOT_LEAK_REPAIR_FULLGRID_SMOKE selected "
            "five repaired trades that all stopped out while four first reached "
            "+0.25R and three reached +0.5R, but "
            "BROAD_LIVE_AS_IF_REPLAY_MARKETABLE_ROUTE_REPAIR_TARGET_SMOKE showed "
            "the 0.25R rescue calibration cut valid oil winners by 0.86322644R "
            "versus raw. Keep the overlay replay-only, but require live-like "
            "target proximity before it can override the ordered path; "
            "target-touch ambiguity remains a source gap and broker/live "
            "authority remains closed."
        )
        runtime["profit_harvest_mfe_capture_v4_allow_m1_proxy_final_r_authority"] = True
        runtime[
            "profit_harvest_mfe_capture_v4_m1_proxy_final_r_authority_source"
        ] = (
            "owner_approved_reconstructed_proxy_replay_authority_m1_ordered_path_not_live"
        )
        package_stop_activation_mfe_r = 0.50
        package_min_hold_minutes_before_stop_raise = 0
        runtime["profit_harvest_mfe_capture_v4_min_mfe_r"] = 0.50
        runtime["profit_harvest_mfe_capture_v4_stop_activation_mfe_r"] = (
            package_stop_activation_mfe_r
        )
        runtime["profit_harvest_mfe_capture_v4_target_activation_fraction"] = 0.75
        runtime["profit_harvest_mfe_capture_v4_trail_gap_r"] = 0.35
        runtime["profit_harvest_mfe_capture_v4_protect_floor_r"] = 0.0
        runtime["profit_harvest_mfe_capture_v4_close_on_giveback_r"] = 0.50
        runtime["profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled"] = True
        runtime["profit_harvest_mfe_capture_v4_cost_aware_margin_r"] = 0.02
        runtime["profit_harvest_mfe_capture_v4_stale_minutes"] = 360
        runtime["profit_harvest_mfe_capture_v4_stale_min_mfe_r"] = 0.25
        runtime["profit_harvest_mfe_capture_v4_stale_close_below_r"] = 0.0
        runtime["profit_harvest_mfe_capture_v4_armed_stale_close_enabled"] = True
        runtime["profit_harvest_mfe_capture_v4_armed_stale_minutes"] = 30
        runtime["profit_harvest_mfe_capture_v4_armed_stale_min_mfe_r"] = 0.50
        runtime["profit_harvest_mfe_capture_v4_armed_stale_close_below_r"] = 0.0
        runtime["profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise"] = (
            package_min_hold_minutes_before_stop_raise
        )
        policy = output.get("ultimate_replay_loss_bucket_policy")
        if isinstance(policy, dict):
            overlay = policy.setdefault("profit_harvest_overlay", {})
            if isinstance(overlay, dict):
                overlay["enabled"] = True
                overlay["repair_status"] = (
                    "sub1r_protective_floor_replay_authority_enabled_after_mfe_giveback_leak"
                )
                overlay["min_mfe_r"] = 0.50
                overlay["stop_activation_mfe_r"] = package_stop_activation_mfe_r
                overlay["target_activation_fraction"] = 0.75
                overlay["trail_gap_r"] = 0.35
                overlay["min_hold_minutes_before_stop_raise"] = (
                    package_min_hold_minutes_before_stop_raise
                )
    if marketable_guard_profile:
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
        ] = True
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
        ] = True
        runtime.setdefault(
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled",
            False,
        )
        runtime.setdefault(
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_demotion_reason",
            (
                "Executable package replay profiles must route marketable-at-decision "
                "package limits through no-broker fillability authority instead of "
                "ordinary limit-first execution with the guard disabled."
            ),
        )
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_scheduler_score"
        ] = 3.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_expected_net_r"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_source_completeness"
        ] = 0.95
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score"
        ] = 1.0
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_expected_net_r"
        ] = 0.55
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_probability"
        ] = 0.70
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_fill_probability"
        ] = 0.80
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_source_completeness"
        ] = 0.95
    elif raw_diagnostic_profile:
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_enabled"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_allowed"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
        ] = False
        runtime[
            "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_router_refusal_derived_immediate_marketable_limit_replay_authority_enabled"
        ] = False
    runtime["replay_order_fillability_policy_v1_enabled"] = marketable_guard_profile
    runtime["replay_order_fillability_policy_v1_require_package_execution_policy"] = True
    runtime["replay_order_fillability_policy_v1_fallback_delay_minutes"] = 30.0
    runtime["replay_order_fillability_policy_v1_min_candidate_probability"] = 0.58
    runtime["replay_order_fillability_policy_v1_min_candidate_ev_r"] = 0.20
    runtime[
        "replay_order_fillability_policy_v1_min_candidate_expected_net_r_after_fallback"
    ] = 0.40
    runtime[
        "replay_order_fillability_policy_v1_min_drift_adjusted_candidate_expected_net_r_after_fallback"
    ] = 0.50 if repaired_profile else -999.0
    runtime[
        "replay_order_fillability_policy_v1_min_effective_target_r_after_fallback"
    ] = 1.0 if repaired_profile else 0.0
    runtime["replay_order_fillability_policy_v1_min_fill_probability"] = 0.60
    runtime["replay_order_fillability_policy_v1_package_min_fill_probability"] = 0.45
    runtime[
        "replay_order_fillability_policy_v1_min_order_fillability_probability_for_fallback"
    ] = 0.35 if repaired_profile else 0.0
    runtime[
        "replay_order_fillability_policy_v1_package_min_order_fillability_probability_for_fallback"
    ] = 0.35 if repaired_profile else 0.0
    runtime["replay_order_fillability_policy_v1_max_limit_fill_probability_for_fallback"] = 0.85
    runtime[
        "replay_order_fillability_policy_v1_allow_high_fill_probability_after_unfilled_probe"
    ] = False
    runtime[
        "replay_order_fillability_policy_v1_defer_predecision_distance_block_to_fallback_path"
    ] = bool(repaired_profile)
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_too_close_guard_enabled"
    ] = bool(repaired_profile)
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_too_close_require_all_thresholds"
    ] = True
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_too_close_missing_fields_action"
    ] = "no_block"
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_min_distance_to_limit_risk"
    ] = 1.25
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_min_distance_to_limit_atr"
    ] = 0.50
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_max_fill_probability"
    ] = 0.64
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_guard_enabled"
    ] = bool(repaired_profile)
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_guard_action"
    ] = "block"
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_require_all_thresholds"
    ] = True
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_min_distance_to_limit_risk"
    ] = 1.25
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_min_distance_to_limit_atr"
    ] = 0.50
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_max_limit_fill_probability"
    ] = 0.64
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_passive_limit_too_close_missing_fields_action"
    ] = "no_block"
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_enabled"
    ] = bool(repaired_profile)
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_guard_action"
    ] = "cap"
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_require_all_thresholds"
    ] = True
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_min_unit_risk_atr"
    ] = 0.35
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_max_distance_to_limit_risk"
    ] = 1.00
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_min_limit_fill_probability"
    ] = 0.50
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_min_target_r"
    ] = 1.50
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_enabled"
    ] = bool(repaired_profile)
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_min_score"
    ] = 0.75
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_distance_weight"
    ] = 0.40
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_fill_weight"
    ] = 0.35
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_target_weight"
    ] = 0.25
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_pressure_requires_base_fragility"
    ] = True
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_risk_cap_pct"
    ] = 0.10
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_score_penalty"
    ] = 1.25
    runtime[
        "scheduler_v4_best_trade_allocator_predecision_stop_hazard_missing_fields_action"
    ] = "no_block"
    runtime[
        "replay_order_fillability_policy_v1_allow_open_reduced_risk_guarded_market_fallback"
    ] = bool(repaired_profile)
    runtime[
        "replay_order_fillability_policy_v1_allow_passive_limit_queue_for_package_replay"
    ] = bool(repaired_profile)
    runtime[
        "replay_order_fillability_policy_v1_require_passive_limit_fallback_envelope"
    ] = bool(repaired_profile)
    runtime[
        "scheduler_v4_best_trade_allocator_replay_order_fillability_policy_v1_require_passive_limit_fallback_envelope"
    ] = bool(repaired_profile)
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_queue_min_fill_probability"
    ] = 0.20 if repaired_profile else 0.0
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_fallback_envelope_min_degraded_transfer_score"
    ] = 0.40 if repaired_profile else 0.0
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_queue_realism_enabled"
    ] = bool(repaired_profile)
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_queue_realism_min_penetration_r"
    ] = 0.02 if repaired_profile else 0.0
    runtime[
        "replay_order_fillability_policy_v1_passive_limit_queue_realism_min_touch_count"
    ] = 2 if repaired_profile else 1
    runtime[
        "replay_order_fillability_policy_v1_allow_off_configured_session_guarded_market_fallback"
    ] = False
    runtime[
        "replay_order_fillability_policy_v1_repaired_profile_guarded_market_fallback_route_reason"
    ] = (
        "off_configured_guarded_market_fallback_disabled_after_V111_19d_"
        "comparator: V111 converted passive-limit/off-session candidates into "
        "market fallback fills, adding 28 market fills for -3.77895463R and "
        "displacing the V110B +22.80442652R limit-fill set. Off-session rows "
        "remain scoreable missed opportunities unless a future signed route "
        "proves explicit off-session guarded-market authority."
        if repaired_profile
        else "disabled_outside_repaired_profile_to_preserve_raw_guarded_comparators"
    )
    runtime[
        "replay_order_fillability_policy_v1_require_open_reduced_soft_authority_explicit_execution_route"
    ] = marketable_guard_profile
    runtime[
        "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_enabled"
    ] = marketable_guard_profile
    runtime[
        "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_max_price_improvement_r"
    ] = 0.50
    runtime[
        "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_max_cost_rebase_multiplier"
    ] = 2.0
    runtime[
        "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_structure_tokens"
    ] = [
        "ob",
        "retest",
        "breaker",
        "fvg",
        "liquidity",
        "sweep",
        "displacement",
        "session_open_range_break",
        "open_range",
    ]
    runtime["replay_order_fillability_policy_v1_min_source_completeness"] = 0.75
    runtime["replay_order_fillability_policy_v1_max_expected_cost_r"] = 0.20
    runtime["replay_order_fillability_policy_v1_guarded_market_extra_cost_r"] = 0.05
    runtime["replay_order_fillability_policy_v1_max_adverse_entry_drift_r"] = 0.75
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_allowed"
    ] = marketable_guard_profile
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_scheduler_score"
    ] = 1.0 if marketable_guard_profile else runtime.get(
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_min_scheduler_score",
        3.0,
    )
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_max_expected_cost_r"
    ] = 0.10 if marketable_guard_profile else runtime.get(
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_replay_route_max_expected_cost_r",
    )
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_tick_floor_cost_ceiling_enabled"
    ] = marketable_guard_profile
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_tick_floor_cost_ceiling_multiplier"
    ] = 1.25
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_tick_floor_untradeable_r"
    ] = 0.20
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_entry_quality_enabled"
    ] = marketable_guard_profile
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_max_unit_risk_atr"
    ] = 2.50
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_displacement_close_position_side"
    ] = 0.60
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_reclaim_close_position_side"
    ] = 0.35
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_open_range_break_close_position_side"
    ] = 0.60
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_open_range_break_body_atr"
    ] = 0.05
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_open_range_break_extension_atr"
    ] = 0.02
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_min_open_range_break_width_atr"
    ] = 0.10
    runtime[
        "scheduler_v4_best_trade_allocator_package_marketable_entry_guard_immediate_marketable_limit_max_open_range_break_width_atr"
    ] = 3.00
    runtime[
        "scheduler_v4_best_trade_allocator_dynamic_budget_package_immediate_marketable_opening_quality_floor_release_enabled"
    ] = marketable_guard_profile
    if factorial_arm_binding is not None:
        factorial_arm_binding = copy.deepcopy(dict(factorial_arm_binding))
        if factorial_arm_binding.get("valid") is not True:
            raise ValueError("selection_sizing_factorial_arm_binding_invalid")
        protocol_economics = factorial_arm_binding.get("protocol_economics")
        if protocol_economics != B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS:
            raise ValueError(
                "selection_sizing_factorial_protocol_economics_invalid"
            )
        protocol_economics = copy.deepcopy(dict(protocol_economics))
        protocol_economics_digest = stable_sha256(protocol_economics)
        if factorial_arm_binding.get(
            "protocol_economics_digest_sha256"
        ) != protocol_economics_digest:
            raise ValueError(
                "selection_sizing_factorial_protocol_economics_digest_invalid"
            )
        denominator = protocol_economics["denominator"]
        matched_risk = protocol_economics["matched_risk"]
        if factorial_arm_binding.get("denominator") != denominator:
            raise ValueError(
                "selection_sizing_factorial_denominator_binding_mismatch"
            )
        for field, expected in denominator.items():
            if factorial_arm_binding.get(field) != expected:
                raise ValueError(
                    "selection_sizing_factorial_denominator_field_mismatch:"
                    f"{field}"
                )
        if factorial_arm_binding.get("matched_risk") != matched_risk:
            raise ValueError(
                "selection_sizing_factorial_matched_risk_binding_mismatch"
            )
        effective_daily_cap = min(
            safe_float(
                runtime.get("prop_safe_selector_external_daily_loss_limit_pct"),
                safe_float((output.get("risk") or {}).get("max_daily_loss_pct"), 4.0),
            ),
            safe_float(
                runtime.get("prop_safe_selector_internal_daily_overlay_pct"),
                4.0,
            )
            if runtime.get("prop_safe_selector_internal_daily_overlay_enabled")
            and runtime.get("prop_safe_selector_internal_overlay_applies_to_budget")
            else math.inf,
        )
        configured_matched_risk = {
            "daily_accepted_risk_pct_cap": effective_daily_cap,
            "peak_open_plus_pending_risk_pct_cap": safe_float(
                runtime.get(
                    "scheduler_v4_best_trade_allocator_portfolio_ceiling_pct"
                ),
                4.0,
            ),
            "cluster_risk_pct_cap": safe_float(
                runtime.get(
                    "scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct"
                ),
                1.5,
            ),
            "opening_window_risk_pct_cap": safe_float(
                runtime.get(
                    "scheduler_v4_best_trade_allocator_dynamic_budget_opening_window_max_total_risk_pct"
                ),
                1.0,
            ),
        }
        for field, configured_value in configured_matched_risk.items():
            if configured_value != safe_float(matched_risk.get(field), math.nan):
                raise ValueError(
                    "selection_sizing_factorial_matched_risk_config_mismatch:"
                    f"{field}"
                )
        if safe_float(
            runtime.get("prop_safe_selector_initial_balance"),
            math.nan,
        ) != denominator["initial_equity_cash"]:
            raise ValueError("selection_sizing_factorial_initial_equity_mismatch")

        prefix = B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
        runtime.update(
            {
                f"{prefix}requested": True,
                f"{prefix}binding_valid": True,
                f"{prefix}decision_contract_path": factorial_arm_binding.get(
                    "decision_contract_path"
                ),
                f"{prefix}decision_contract_sha256": factorial_arm_binding.get(
                    "decision_contract_sha256"
                ),
                f"{prefix}common_execution_input_digest_sha256": (
                    factorial_arm_binding.get(
                        "common_execution_input_digest_sha256"
                    )
                ),
                f"{prefix}arm_id": factorial_arm_binding.get("arm_id"),
                f"{prefix}arm_fingerprint_sha256": factorial_arm_binding.get(
                    "arm_fingerprint_sha256"
                ),
                f"{prefix}selection_factor": factorial_arm_binding.get(
                    "selection_factor"
                ),
                f"{prefix}sizing_factor": factorial_arm_binding.get(
                    "sizing_factor"
                ),
                f"{prefix}selection_mode": factorial_arm_binding.get(
                    "selection_mode"
                ),
                f"{prefix}sizing_mode": factorial_arm_binding.get("sizing_mode"),
                f"{prefix}neutral_selection_seed_sha256": (
                    factorial_arm_binding.get("neutral_selection_seed_sha256")
                ),
                f"{prefix}protocol_economics_digest_sha256": (
                    protocol_economics_digest
                ),
                f"{prefix}initial_equity_cash": denominator[
                    "initial_equity_cash"
                ],
                f"{prefix}fixed_account_risk_unit_pct": denominator[
                    "fixed_account_risk_unit_pct"
                ],
                f"{prefix}fixed_account_risk_unit_cash": denominator[
                    "fixed_account_risk_unit_cash"
                ],
                f"{prefix}fixed_denominator_portfolio_r_cash": denominator[
                    "fixed_denominator_portfolio_r_cash"
                ],
                f"{prefix}same_ex_ante_rules_all_arms": matched_risk[
                    "same_ex_ante_rules_all_arms"
                ],
                f"{prefix}daily_accepted_risk_pct_cap": matched_risk[
                    "daily_accepted_risk_pct_cap"
                ],
                f"{prefix}peak_open_plus_pending_risk_pct_cap": matched_risk[
                    "peak_open_plus_pending_risk_pct_cap"
                ],
                f"{prefix}cluster_risk_pct_cap": matched_risk[
                    "cluster_risk_pct_cap"
                ],
                f"{prefix}opening_window_risk_pct_cap": matched_risk[
                    "opening_window_risk_pct_cap"
                ],
                f"{prefix}pending_to_open_transfer_once": matched_risk[
                    "pending_to_open_transfer_once"
                ],
                f"{prefix}expiry_or_close_release_once": matched_risk[
                    "expiry_or_close_release_once"
                ],
                f"{prefix}ex_post_rescaling_forbidden": matched_risk[
                    "ex_post_rescaling_forbidden"
                ],
                f"{prefix}uses_outcome_fields": False,
                f"{prefix}live_broker_authority": False,
                f"{prefix}broker_mutation_enabled": False,
                f"{prefix}final_selection_claim": False,
            }
        )
        factorial_binding_payload = (
            selection_sizing_core_binding_payload(
                decision_contract_sha256=factorial_arm_binding.get(
                    "decision_contract_sha256"
                ),
                common_execution_input_digest_sha256=factorial_arm_binding.get(
                    "common_execution_input_digest_sha256"
                ),
                arm_id=factorial_arm_binding.get("arm_id"),
                arm_fingerprint_sha256=factorial_arm_binding.get(
                    "arm_fingerprint_sha256"
                ),
                selection_factor=factorial_arm_binding.get("selection_factor"),
                sizing_factor=factorial_arm_binding.get("sizing_factor"),
                selection_mode=factorial_arm_binding.get("selection_mode"),
                sizing_mode=factorial_arm_binding.get("sizing_mode"),
                neutral_selection_seed_sha256=factorial_arm_binding.get(
                    "neutral_selection_seed_sha256"
                ),
                protocol_economics=protocol_economics,
                protocol_economics_digest_sha256=(
                    protocol_economics_digest
                ),
            )
        )
        binding_payload_digest = stable_sha256(factorial_binding_payload)
        if factorial_arm_binding.get("binding_payload") != factorial_binding_payload:
            raise ValueError(
                "selection_sizing_factorial_binding_payload_mismatch"
            )
        if factorial_arm_binding.get(
            "binding_payload_sha256"
        ) != binding_payload_digest:
            raise ValueError(
                "selection_sizing_factorial_binding_payload_digest_mismatch"
            )
        runtime[f"{prefix}binding_payload_sha256"] = binding_payload_digest
        if factorial_arm_binding.get("sizing_factor") == "R0":
            fixed_risk_pct = safe_float(
                factorial_arm_binding.get("fixed_account_risk_unit_pct"),
                math.nan,
            )
            if not math.isfinite(fixed_risk_pct) or fixed_risk_pct <= 0.0:
                raise ValueError("selection_sizing_factorial_fixed_risk_invalid")
            runtime[
                "scheduler_v4_best_trade_allocator_dynamic_budget_quality_gate_enabled"
            ] = False
            runtime[
                "b7_5_selection_sizing_factorial_r0_dynamic_quality_gate_disabled"
            ] = True
    output["broad_live_as_if_replay_harness"] = {
        "profile": profile,
        "profile_family": (
            "strict_raw_baseline"
            if profile == PROFILE_RAW
            else "guarded_loss_bucket_only"
            if profile == PROFILE_GUARDED
            else "repaired_full_package_conversion"
        ),
        "repaired_profile": repaired_profile,
        "package_execution_result_scope": package_execution_result_scope,
        "raw_baseline_diagnostic_only": raw_diagnostic_profile,
        "marketable_guard_profile": marketable_guard_profile,
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "cost_authority": "broker_calibrated_replay_cost",
        "cost_authority_fallback_diagnostic": "timewarp_candidate_cost_r_proxy",
        "marketable_limit_structure_preservation_enabled": runtime.get(
            "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_enabled",
            False,
        ),
        "marketable_limit_structure_preservation_max_price_improvement_r": runtime.get(
            "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_max_price_improvement_r",
            0.50,
        ),
        "marketable_limit_structure_preservation_max_cost_rebase_multiplier": runtime.get(
            "replay_order_fillability_policy_v1_marketable_limit_structure_preservation_max_cost_rebase_multiplier",
            2.0,
        ),
        "passive_limit_queue_realism_enabled": runtime.get(
            "replay_order_fillability_policy_v1_passive_limit_queue_realism_enabled",
            False,
        ),
        "passive_limit_queue_realism_min_penetration_r": runtime.get(
            "replay_order_fillability_policy_v1_passive_limit_queue_realism_min_penetration_r",
            0.0,
        ),
        "passive_limit_queue_realism_min_touch_count": runtime.get(
            "replay_order_fillability_policy_v1_passive_limit_queue_realism_min_touch_count",
            1,
        ),
        **(
            {
                "b7_5_selection_sizing_factorial_arm_binding": copy.deepcopy(
                    dict(factorial_arm_binding)
                )
            }
            if factorial_arm_binding is not None
            else {}
        ),
    }
    return output


def selection_sizing_factorial_ledger_fields(
    factorial_arm_binding: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(factorial_arm_binding, Mapping):
        return {}
    if factorial_arm_binding.get("valid") is not True:
        raise ValueError(
            "selection_sizing_factorial_partial_ledger_binding_invalid"
        )
    for field in (
        "decision_contract_sha256",
        "common_execution_input_digest_sha256",
        "binding_payload_sha256",
        "protocol_economics_digest_sha256",
        "arm_fingerprint_sha256",
        "neutral_selection_seed_sha256",
    ):
        if _canonical_sha256_text(factorial_arm_binding.get(field)) is None:
            raise ValueError(
                "selection_sizing_factorial_partial_ledger_binding_missing:"
                f"{field}"
            )
    if factorial_arm_binding.get(
        "protocol_economics"
    ) != B7_5_SELECTION_SIZING_PROTOCOL_ECONOMICS:
        raise ValueError(
            "selection_sizing_factorial_partial_ledger_economics_invalid"
        )
    denominator = factorial_arm_binding.get("denominator")
    denominator = denominator if isinstance(denominator, Mapping) else {}
    matched_risk = factorial_arm_binding.get("matched_risk")
    matched_risk = matched_risk if isinstance(matched_risk, Mapping) else {}
    return {
        "b7_5_selection_sizing_factorial_decision_contract_sha256": (
            factorial_arm_binding.get("decision_contract_sha256")
        ),
        "b7_5_selection_sizing_factorial_common_execution_input_digest_sha256": (
            factorial_arm_binding.get(
                "common_execution_input_digest_sha256"
            )
        ),
        "b7_5_selection_sizing_factorial_binding_payload_sha256": (
            factorial_arm_binding.get("binding_payload_sha256")
        ),
        "b7_5_selection_sizing_factorial_protocol_economics_digest_sha256": (
            factorial_arm_binding.get("protocol_economics_digest_sha256")
        ),
        "b7_5_selection_sizing_factorial_arm_id": factorial_arm_binding.get(
            "arm_id"
        ),
        "b7_5_selection_sizing_factorial_arm_fingerprint_sha256": (
            factorial_arm_binding.get("arm_fingerprint_sha256")
        ),
        "b7_5_selection_sizing_factorial_selection_factor": (
            factorial_arm_binding.get("selection_factor")
        ),
        "b7_5_selection_sizing_factorial_sizing_factor": (
            factorial_arm_binding.get("sizing_factor")
        ),
        "b7_5_selection_sizing_factorial_selection_mode": (
            factorial_arm_binding.get("selection_mode")
        ),
        "b7_5_selection_sizing_factorial_sizing_mode": (
            factorial_arm_binding.get("sizing_mode")
        ),
        "b7_5_selection_sizing_factorial_neutral_selection_seed_sha256": (
            factorial_arm_binding.get("neutral_selection_seed_sha256")
        ),
        "b7_5_selection_sizing_factorial_initial_equity_cash": denominator.get(
            "initial_equity_cash"
        ),
        "b7_5_selection_sizing_factorial_fixed_account_risk_unit_pct": (
            denominator.get("fixed_account_risk_unit_pct")
        ),
        "b7_5_selection_sizing_factorial_fixed_account_risk_unit_cash": (
            denominator.get("fixed_account_risk_unit_cash")
        ),
        "b7_5_selection_sizing_factorial_fixed_denominator_portfolio_r_cash": (
            denominator.get("fixed_denominator_portfolio_r_cash")
        ),
        "b7_5_selection_sizing_factorial_daily_accepted_risk_pct_cap": (
            matched_risk.get("daily_accepted_risk_pct_cap")
        ),
        "b7_5_selection_sizing_factorial_peak_open_plus_pending_risk_pct_cap": (
            matched_risk.get("peak_open_plus_pending_risk_pct_cap")
        ),
        "b7_5_selection_sizing_factorial_cluster_risk_pct_cap": (
            matched_risk.get("cluster_risk_pct_cap")
        ),
        "b7_5_selection_sizing_factorial_opening_window_risk_pct_cap": (
            matched_risk.get("opening_window_risk_pct_cap")
        ),
        "b7_5_selection_sizing_factorial_pending_to_open_transfer_once": (
            matched_risk.get("pending_to_open_transfer_once")
        ),
        "b7_5_selection_sizing_factorial_expiry_or_close_release_once": (
            matched_risk.get("expiry_or_close_release_once")
        ),
        "b7_5_selection_sizing_factorial_ex_post_rescaling_forbidden": (
            matched_risk.get("ex_post_rescaling_forbidden")
        ),
        "b7_5_selection_sizing_factorial_uses_outcome_fields": False,
        "b7_5_selection_sizing_factorial_live_broker_authority": False,
        "b7_5_selection_sizing_factorial_broker_mutation_enabled": False,
    }


def annotate_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    profile: str,
    split: str,
    chunk_id: str,
    row_type: str,
    factorial_arm_binding: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    annotated: list[dict[str, Any]] = []
    package_execution_result_scope = (
        "raw_baseline_diagnostic_only"
        if profile == PROFILE_RAW
        else "guarded_executable_package_replay"
        if profile == PROFILE_GUARDED
        else "repaired_executable_package_replay"
    )
    chunk_parts = str(chunk_id or "").split(":")
    chunk_start_day = chunk_parts[-2] if len(chunk_parts) >= 4 else None
    chunk_end_day = chunk_parts[-1] if len(chunk_parts) >= 4 else None
    chunk_day_count = None
    try:
        if chunk_start_day and chunk_end_day:
            chunk_day_count = (
                date.fromisoformat(chunk_end_day)
                - date.fromisoformat(chunk_start_day)
            ).days + 1
    except ValueError:
        chunk_day_count = None
    for row in rows:
        day = str(row.get("trading_day") or "")
        annotated_row = dict(row)
        row_package_execution_result_scope = package_execution_result_scope
        source_row_type = annotated_row.get("row_type")
        normalize_replay_quality_fields(annotated_row, row_type=row_type)
        if row_type == "candidate" and annotated_row.get("source_completeness_status") in (
            None,
            "",
        ):
            annotated_row["source_completeness_status"] = (
                "source_completeness_present"
                if annotated_row.get("source_completeness") not in (None, "")
                else "source_completeness_not_reported"
            )
            annotated_row["source_completeness_status_defaulted_by_harness"] = True
        if row_type == "simulated_trade":
            if annotated_row.get("source_completeness_status") in (None, ""):
                annotated_row["source_completeness_status"] = (
                    "source_completeness_present"
                    if annotated_row.get("source_completeness") not in (None, "")
                    else "source_completeness_not_reported"
                )
                annotated_row["source_completeness_status_defaulted_by_harness"] = True
            if annotated_row.get("net_cost_scope") in (None, ""):
                annotated_row["net_cost_scope"] = (
                    "broker_pretrade_plus_optional_fallback_surcharge_not_close_side_all_in"
                    if annotated_row.get("expected_cost_r") not in (None, "")
                    else "cost_scope_not_reported"
                )
            if annotated_row.get("close_side_all_in_cost_status") in (None, ""):
                annotated_row["close_side_all_in_cost_status"] = (
                    "not_joined_in_replay_net_proxy_r"
                )
            source_required_replay_headline_authorized = (
                source_required_lifecycle_replay_headline_authorized(annotated_row)
            )
            strict_reduced_authority_allowed = (
                strict_full_package_reduced_action_authority_allowed(annotated_row)
            )
            annotated_row[
                "strict_full_package_reduced_action_authority_allowed"
            ] = strict_reduced_authority_allowed
            annotated_row[
                "strict_full_package_reduced_action_authority_status"
            ] = (
                "signed_predecision_package_reduced_action_authority_valid"
                if strict_reduced_authority_allowed
                else "not_signed_predecision_package_reduced_action_authority"
            )
            exclusion_reason = headline_result_exclusion_reason(annotated_row)
            strict_exclusion_reason = strict_full_package_parity_result_exclusion_reason(
                annotated_row
            )
            annotated_row["headline_result_eligible"] = exclusion_reason is None
            annotated_row["headline_result_exclusion_reason"] = (
                exclusion_reason or "headline_result_eligible"
            )
            annotated_row["replay_repair_result_eligible"] = exclusion_reason is None
            annotated_row["strict_full_package_parity_result_eligible"] = (
                strict_exclusion_reason is None
            )
            annotated_row["strict_full_package_exclusion_reason"] = (
                strict_exclusion_reason
                or "strict_full_package_parity_result_eligible"
            )
            profit_harvest_m1_proxy_scope = profit_harvest_m1_proxy_replay_scope(
                annotated_row
            )
            annotated_row["profit_harvest_m1_proxy_replay_scope"] = (
                profit_harvest_m1_proxy_scope
            )
            annotated_row[
                "profit_harvest_m1_proxy_diagnostic_overlay_base_headline_allowed"
            ] = profit_harvest_m1_proxy_diagnostic_overlay_base_headline_allowed(
                annotated_row
            )
            annotated_row["profit_harvest_m1_proxy_replay_headline_eligible"] = (
                profit_harvest_m1_proxy_scope is not None
                and exclusion_reason is None
            )
            annotated_row["source_required_lifecycle_gap_diagnostic_only"] = (
                exclusion_reason
                == "source_required_fail_closed_lifecycle_source_gap_diagnostic_only"
            )
            annotated_row[
                "source_required_lifecycle_replay_headline_authorized"
            ] = source_required_replay_headline_authorized
            annotated_row[
                "source_required_lifecycle_replay_headline_authority_reason"
            ] = (
                "signed_package_authority_reconciled_local_replay"
                if source_required_replay_headline_authorized
                else "not_signed_reconciled_local_replay"
            )
            terminal_r_unscoreable = bool(
                annotated_row.get("entry_fill_executable") is True
                and annotated_row.get("terminal_r_scoreable") is False
            )
            annotated_row["result_scope"] = (
                "executed_entry_terminal_r_unscoreable"
                if terminal_r_unscoreable
                else "diagnostic_source_required_lifecycle_gap_not_headline"
                if exclusion_reason
                == "source_required_fail_closed_lifecycle_source_gap_diagnostic_only"
                else "diagnostic_profit_harvest_m1_proxy_not_headline"
                if exclusion_reason
                == "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"
                else "diagnostic_terminal_result_not_headline_authority"
                if str(exclusion_reason or "").startswith(
                    "terminal_result_not_headline_authority:"
                )
                else "diagnostic_replay_result_not_headline"
                if exclusion_reason is not None
                else "headline_replay_signed_source_required_lifecycle_result"
                if source_required_replay_headline_authorized
                else "headline_replay_result"
            )
            if terminal_r_unscoreable:
                row_package_execution_result_scope = str(
                    annotated_row.get("package_execution_result_scope")
                    or "entry_fill_executable_terminal_r_unscoreable"
                )
        output_row = {
            **annotated_row,
            "row_type": row_type,
            "source_row_type": source_row_type,
            "bucket_source_family": source_row_type if row_type == "bucket" else None,
            "profile": profile,
            "broad_replay_profile": profile,
            "phase": annotated_row.get("phase") or f"{profile}_{split}",
            "package_execution_result_scope": row_package_execution_result_scope,
            "raw_baseline_diagnostic_only": profile == PROFILE_RAW,
            "marketable_guard_profile": profile in {PROFILE_GUARDED, PROFILE_REPAIRED},
            "split": split,
            "chunk_id": chunk_id,
            "chunk_start_day": chunk_start_day,
            "chunk_end_day": chunk_end_day,
            "chunk_day_count": chunk_day_count,
            "row_provenance_schema": "broad_live_as_if_replay_row_provenance_v1",
            "repair_seed_window": is_repair_seed_day(day) if day else False,
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
            "no_broker_boundary": NO_BROKER_BOUNDARY,
            **selection_sizing_factorial_ledger_fields(factorial_arm_binding),
        }
        if row_type in {
            "candidate",
            "candidate_index",
            "scheduler_scorecard",
            "simulated_order",
            "simulated_trade",
            "ordered_path_oracle",
            "missed_opportunity",
        }:
            normalize_package_new_entry_authority_ledger_row(output_row)
            if row_type == "scheduler_scorecard":
                backfill_pre_risk_finalizer_quality_sources(output_row)
        annotated.append(output_row)
    return annotated


def iter_annotated_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    profile: str,
    split: str,
    chunk_id: str,
    row_type: str,
    factorial_arm_binding: Mapping[str, Any] | None = None,
) -> Iterable[dict[str, Any]]:
    """Yield the exact legacy annotation one row at a time."""

    for row in rows:
        yield annotate_rows(
            (row,),
            profile=profile,
            split=split,
            chunk_id=chunk_id,
            row_type=row_type,
            factorial_arm_binding=factorial_arm_binding,
        )[0]


def counter_add(target: Counter[str], value: Any) -> None:
    text = str(value or "")
    if text:
        target[text] += 1


def boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def package_role_disposition_executable(row: Mapping[str, Any]) -> bool:
    explicit = row.get("role_disposition_executable")
    if explicit is None:
        explicit = row.get("ultimate_package_role_disposition_executable")
    if explicit is not None and not boolish(explicit):
        return False
    role = str(
        row.get("ultimate_package_role_disposition")
        or row.get("role_disposition")
        or ""
    ).strip().lower().replace("-", "_").replace(" ", "_")
    return role not in PACKAGE_NON_EXECUTABLE_ROLE_DISPOSITIONS


REPLAY_REPAIR_ONLY_SELECTOR_ACTIONS = {"reduce-risk", "open-reduced-risk"}
STRICT_FULL_PACKAGE_REDUCED_ACTION_AUTHORITY_FAMILIES = {
    "router_refusal_softening",
    "explicit_package_executable_replay_materialization",
    "source_bound_fill_floor_replay_materialization",
    "fill_floor_softening",
    "fill_floor_bypass",
    "off_session_softening",
    "broker_net_admission_gradient",
    "numeric_disagreement_softening",
}
STRICT_FULL_PACKAGE_SIGNED_AUTHORITY_VALID_STATUSES = {
    "valid",
    "signed_reduced_package_new_entry_authority_valid",
    "signed_package_new_entry_authority_valid",
}
M1_PROFIT_HARVEST_PROXY_DIAGNOSTIC_STATUSES = {
    "m1_ordered_path_proxy_final_r_diagnostic_not_authority",
    "m1_ordered_path_proxy_final_r_authority_not_live",
    "m1_ordered_path_proxy_target_after_exit_diagnostic_not_authority",
}
M1_PROFIT_HARVEST_PROXY_STRICT_EXCLUSION_STATUSES = {
    *M1_PROFIT_HARVEST_PROXY_DIAGNOSTIC_STATUSES,
}


def profit_harvest_m1_proxy_replay_scope(row: Mapping[str, Any]) -> str | None:
    status = str(
        row.get("profit_harvest_mfe_capture_replay_exit_final_r_authority_status")
        or ""
    ).strip()
    if status not in M1_PROFIT_HARVEST_PROXY_STRICT_EXCLUSION_STATUSES:
        return None
    return "m1_proxy_diagnostic_overlay_not_terminal_r_authority"


def profit_harvest_m1_proxy_diagnostic_overlay_base_headline_allowed(
    row: Mapping[str, Any],
) -> bool:
    """Allow the base terminal replay result when profit-harvest is diagnostic.

    The M1 profit-harvest overlay must not become headline terminal authority
    unless the replay exit itself is authoritative. When the engine explicitly
    marks that overlay diagnostic-only and leaves the original terminal result
    in place, excluding the whole trade creates asymmetric accounting: target
    winners disappear while stop losses remain headline.
    """

    status = str(
        row.get("profit_harvest_mfe_capture_replay_exit_final_r_authority_status")
        or ""
    ).strip()
    if status not in M1_PROFIT_HARVEST_PROXY_STRICT_EXCLUSION_STATUSES:
        return False
    if not boolish(row.get("profit_harvest_mfe_capture_replay_exit_diagnostic_only")):
        return False
    if boolish(row.get("profit_harvest_mfe_capture_replay_bound")):
        return False
    final_r = safe_float(row.get("final_r"), math.nan)
    if not math.isfinite(final_r):
        return False
    close_reason = str(
        row.get("close_reason")
        or row.get("terminal_outcome")
        or row.get("raw_close_reason")
        or ""
    ).strip()
    return bool(close_reason)


def profit_harvest_m1_proxy_result_exclusion_reason(
    row: Mapping[str, Any],
) -> str | None:
    status = str(
        row.get("profit_harvest_mfe_capture_replay_exit_final_r_authority_status")
        or ""
    ).strip()
    if status not in M1_PROFIT_HARVEST_PROXY_STRICT_EXCLUSION_STATUSES:
        return None
    if profit_harvest_m1_proxy_diagnostic_overlay_base_headline_allowed(row):
        return None
    return "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"


def profit_harvest_m1_proxy_strict_result_exclusion_reason(
    row: Mapping[str, Any],
) -> str | None:
    status = str(
        row.get("profit_harvest_mfe_capture_replay_exit_final_r_authority_status")
        or ""
    ).strip()
    if status not in M1_PROFIT_HARVEST_PROXY_STRICT_EXCLUSION_STATUSES:
        return None
    if profit_harvest_m1_proxy_diagnostic_overlay_base_headline_allowed(row):
        return None
    return "profit_harvest_m1_proxy_final_r_diagnostic_not_headline_authority"


def missed_opportunity_execution_bound_cost_passed_scope(
    row: Mapping[str, Any],
) -> bool:
    """Cost-passed missed opportunity R is executable only with terminal path proof."""

    order_status = str(row.get("order_status") or "").strip()
    finalizer_execution_bound = any(
        boolish(row.get(field))
        for field in (
            "executable_finalized",
            "risk_finalizer_executable_finalized",
            "missed_row_executable_finalized",
        )
    )
    package_execution_bound = any(
        boolish(row.get(field))
        for field in (
            "package_replay_executable_candidate_use_allowed",
            "replay_candidate_use_allowed_now",
        )
    )
    order_execution_bound = any(
        boolish(row.get(field))
        for field in (
            "package_replay_order_executable_candidate_use_allowed",
            "missed_package_replay_order_executable_candidate_use_allowed",
        )
    )
    source_required_gap = source_required_lifecycle_gap_exclusion_reason(row) is not None
    return bool(
        row.get("missed_cost_executable_opportunity_scoreable") is True
        and row.get("missed_opportunity_execution_bound_cost_passed") is True
        and finalizer_execution_bound
        and package_execution_bound
        and order_execution_bound
        and package_role_disposition_executable(row)
        and order_status
        and order_status != "not_sent_missed_opportunity"
        and not source_required_gap
    )


def strict_full_package_reduced_action_authority_allowed(
    row: Mapping[str, Any],
) -> bool:
    if boolish(row.get("strict_full_package_reduced_action_authority_allowed")):
        return True
    selector_action = str(row.get("selector_action") or "").strip().lower()
    if selector_action == "reduce-risk":
        authority = row.get("ultimate_candidate_package_reduce_risk_authority")
        allowed_field_names = (
            "package_reduce_risk_authority_allowed",
            "ultimate_package_reduce_risk_authority_allowed",
        )
        family_field_names = (
            "package_reduce_risk_authority_family",
            "ultimate_package_reduce_risk_authority_family",
        )
    else:
        authority = row.get("ultimate_candidate_package_open_reduced_risk_authority")
        allowed_field_names = (
            "package_open_reduced_authority_allowed",
            "ultimate_package_open_reduced_authority_allowed",
        )
        family_field_names = (
            "package_open_reduced_authority_family",
            "ultimate_package_open_reduced_authority_family",
        )
    authority = authority if isinstance(authority, Mapping) else {}
    family = str(
        next(
            (
                row.get(field_name)
                for field_name in family_field_names
                if row.get(field_name) not in (None, "")
            ),
            None,
        )
        or row.get("package_new_entry_authority_authority_family")
        or authority.get("authority_family")
        or authority.get("package_new_entry_authority_authority_family")
        or ""
    ).strip()
    if family not in STRICT_FULL_PACKAGE_REDUCED_ACTION_AUTHORITY_FAMILIES:
        return False
    authority_allowed = any(
        boolish(row.get(field_name)) for field_name in allowed_field_names
    )
    authority_allowed = authority_allowed or boolish(authority.get("allowed"))
    if not authority_allowed:
        return False
    current_config_allowed = (
        boolish(authority.get("current_config_allowed"))
        or boolish(row.get("package_new_entry_authority_valid"))
    )
    if not current_config_allowed:
        return False
    if boolish(row.get("package_new_entry_authority_uses_outcome_fields")) or boolish(
        authority.get("package_new_entry_authority_uses_outcome_fields")
    ):
        return False
    status = str(
        row.get("package_new_entry_authority_status")
        or authority.get("package_new_entry_authority_status")
        or ""
    ).strip()
    signed_valid = boolish(row.get("package_new_entry_authority_valid")) or (
        status in STRICT_FULL_PACKAGE_SIGNED_AUTHORITY_VALID_STATUSES
    )
    authority_hash = (
        row.get("package_new_entry_authority_hash_sha256")
        or row.get("expected_package_new_entry_authority_hash_sha256")
        or authority.get("package_new_entry_authority_hash_sha256")
        or authority.get("expected_package_new_entry_authority_hash_sha256")
    )
    if not signed_valid or not authority_hash:
        return False
    source_boundary = str(
        row.get("package_new_entry_authority_source_boundary")
        or authority.get("package_new_entry_authority_source_boundary")
        or authority.get("source_boundary")
        or row.get("source_boundary")
        or ""
    ).strip()
    source_boundary_lower = source_boundary.lower()
    if not source_boundary or (
        "outcome" in source_boundary_lower
        and "no_outcome" not in source_boundary_lower
    ):
        return False
    quality_status = str(
        row.get("package_new_entry_authority_candidate_decision_quality_alias_status")
        or authority.get("package_new_entry_authority_candidate_decision_quality_alias_status")
        or row.get("candidate_decision_quality_alias_status")
        or ""
    ).strip()
    quality_contract = authority.get("quality_contract")
    quality_valid = bool(
        quality_status in {"materialized", "exact_materialized"}
        or (
            isinstance(quality_contract, Mapping)
            and boolish(quality_contract.get("valid"))
        )
    )
    if not quality_valid:
        return False
    return True


def source_required_lifecycle_replay_headline_authorized(
    row: Mapping[str, Any],
) -> bool:
    """Allow source-required lifecycle rows into local replay headline only.

    This does not satisfy broker-real lifecycle truth. It only prevents the
    broad no-broker replay harness from demoting rows that the simulator already
    executed with signed package authority, scheduler/risk reconciliation, and
    package/cost executability.
    """

    if boolish(row.get("broker_order_lifecycle_truth_satisfied")):
        return True
    if not source_required_replay_override_applied(row):
        return False
    if not source_required_replay_override_reason_allowed_for_row(row):
        return False
    if not replay_lifecycle_signed_package_authority_valid(row):
        return False
    if row.get("broker_pretrade_cost_executable") is False:
        return False
    if boolish(row.get("source_gap_cost_fallback_blocked")):
        return False
    if not boolish(row.get("package_replay_executable_candidate_use_allowed")):
        reason = str(
            row.get("package_replay_executable_candidate_use_allowed_reason") or ""
        )
        if "broker_cost_and_scheduler_action_executable" not in reason:
            return False
    replay_reconciled = any(
        boolish(row.get(field))
        for field in (
            "same_symbol_lifecycle_permission_reconcile_applied",
            "same_symbol_lifecycle_action_reconciled_from_scheduler",
            "risk_lifecycle_action_reconciled_from_scheduler",
            "source_required_package_risk_lifecycle_reconcile_applied",
            "execution_manager_source_required_package_risk_lifecycle_reconcile_applied",
            "execution_manager_same_symbol_lifecycle_permission_reconcile_applied",
            "package_same_direction_scale_in_lifecycle_reconcile_applied",
            "execution_manager_package_same_direction_scale_in_lifecycle_reconcile_applied",
            "package_opposite_side_close_reverse_lifecycle_reconcile_applied",
            "execution_manager_package_opposite_side_close_reverse_lifecycle_reconcile_applied",
            "package_pending_replacement_lifecycle_reconcile_applied",
            "execution_manager_package_pending_replacement_lifecycle_reconcile_applied",
        )
    )
    context_present = boolish(
        row.get("scheduler_materialization_source_required_fail_closed_lifecycle_context_present")
    )
    context_source = str(
        row.get(
            "scheduler_materialization_source_required_fail_closed_lifecycle_context_source"
        )
        or ""
    ).strip()
    return bool(
        replay_reconciled
        or (
            context_present
            and context_source in {"open_position", "pending_order", "simulated_account"}
        )
    )


def source_required_lifecycle_gap_exclusion_reason(
    row: Mapping[str, Any],
) -> str | None:
    """Keep true source gaps diagnostic while honoring signed local replay."""

    blocker_reasons = row.get("execution_manager_live_promotion_blocker_reasons")
    if isinstance(blocker_reasons, str):
        blocker_text = blocker_reasons
    elif isinstance(blocker_reasons, IterableABC):
        blocker_text = " ".join(str(item) for item in blocker_reasons)
    else:
        blocker_text = ""
    lifecycle_action_text = " ".join(
        str(row.get(field) or "")
        for field in (
            "same_symbol_lifecycle_action",
            "lifecycle_action",
            "candidate_lifecycle_action",
            "risk_lifecycle_action",
            "scheduler_lifecycle_action",
            "scheduler_materialization_action_intent",
        )
    )
    source_required_present = (
        boolish(row.get("source_required_lifecycle_origin"))
        or "source_required_fail_closed" in blocker_text
        or "source_required_fail_closed" in lifecycle_action_text
        or boolish(row.get("source_required_fail_closed_raw_lifecycle_action"))
        or source_required_replay_override_applied(row)
    )
    if not source_required_present:
        return None
    if boolish(row.get("broker_order_lifecycle_truth_satisfied")):
        return None
    if source_required_lifecycle_replay_headline_authorized(row):
        return None
    return "source_required_fail_closed_lifecycle_source_gap_diagnostic_only"


def headline_result_exclusion_reason(row: Mapping[str, Any]) -> str | None:
    if row.get("terminal_r_scoreable") is False:
        status = str(
            row.get("terminal_r_scoreability_status")
            or "entry_fill_executable_terminal_r_unscoreable"
        ).strip()
        return f"terminal_r_unscoreable:{status}"
    source_gap_reason = source_required_lifecycle_gap_exclusion_reason(row)
    if source_gap_reason:
        return source_gap_reason
    if row.get("headline_result_authority") is False:
        authority_status = str(
            row.get("headline_result_authority_status")
            or "terminal_result_not_headline_authority"
        ).strip()
        return f"terminal_result_not_headline_authority:{authority_status}"
    profit_harvest_reason = profit_harvest_m1_proxy_result_exclusion_reason(row)
    if profit_harvest_reason:
        return profit_harvest_reason
    fill_realism_class = str(row.get("fill_realism_class") or "").strip().lower()
    if row.get("diagnostic_fill_only") is True:
        return "fill_realism_diagnostic_not_headline_authority"
    if row.get("fill_realism_executable") is False:
        return "fill_realism_not_executable"
    if fill_realism_class in {
        "m15_proxy",
        "first_touch_optimistic",
        "ordered_tick_required_source_gap",
        "guarded_market_fallback_elapsed_path",
        "source_gap",
    }:
        return f"fill_realism_class_not_headline:{fill_realism_class}"
    return None


def _bucket_value(row: Mapping[str, Any], key: str) -> str:
    if key == "session":
        return str(
            row.get("route_session")
            or row.get("session")
            or row.get("session_bucket")
            or row.get("authority_session")
            or ""
        )
    if key == "framework":
        return str(row.get("framework") or row.get("current_framework") or "")
    if key == "policy":
        return str(
            row.get("policy")
            or row.get("dynamic_geometry_policy")
            or row.get("gtos_vnext_dynamic_policy_selected")
            or ""
        )
    if key == "risk_reason":
        return str(row.get("risk_decision_reason") or row.get("risk_reason") or "")
    return str(row.get(key) or "")


def _trade_matches_bucket(trade: Mapping[str, Any], bucket: Mapping[str, Any]) -> bool:
    for key in (
        "trading_day",
        "symbol",
        "side",
        "direction",
        "session",
        "framework",
        "policy",
        "risk_reason",
    ):
        bucket_value = bucket.get(key)
        if bucket_value in (None, "", "all"):
            continue
        if _bucket_value(trade, key) != str(bucket_value):
            return False
    return True


def _headline_trade_bucket_totals(
    trades: IterableABC[Mapping[str, Any]],
    bucket: Mapping[str, Any],
) -> dict[str, Any]:
    totals = {
        "headline_filled_trade_count": 0,
        "headline_winner_count": 0,
        "headline_loser_count": 0,
        "headline_flat_count": 0,
        "headline_net_proxy_r": 0.0,
        "headline_total_r": 0.0,
        "headline_gross_r": 0.0,
        "headline_final_r": 0.0,
        "headline_expected_cost_r": 0.0,
        "headline_cash_pnl": 0.0,
        "headline_risk_cash": 0.0,
        "headline_risk_cash_sum": 0.0,
        "headline_risk_pct_sum": 0.0,
        "diagnostic_only_trade_count": 0,
        "diagnostic_only_net_proxy_r": 0.0,
    }
    for trade in trades:
        if not _trade_matches_bucket(trade, bucket):
            continue
        net = safe_float(trade.get("net_proxy_r"), safe_float(trade.get("net_r")))
        if headline_result_exclusion_reason(trade):
            totals["diagnostic_only_trade_count"] += 1
            totals["diagnostic_only_net_proxy_r"] = round(
                totals["diagnostic_only_net_proxy_r"] + net,
                8,
            )
            continue
        totals["headline_filled_trade_count"] += 1
        totals["headline_net_proxy_r"] = round(totals["headline_net_proxy_r"] + net, 8)
        totals["headline_total_r"] = totals["headline_net_proxy_r"]
        totals["headline_gross_r"] = round(
            totals["headline_gross_r"] + safe_float(trade.get("gross_r")),
            8,
        )
        totals["headline_final_r"] = round(
            totals["headline_final_r"]
            + safe_float(trade.get("final_r"), safe_float(trade.get("gross_r"))),
            8,
        )
        totals["headline_expected_cost_r"] = round(
            totals["headline_expected_cost_r"]
            + safe_float(trade.get("expected_cost_r")),
            8,
        )
        totals["headline_cash_pnl"] = round(
            totals["headline_cash_pnl"] + safe_float(trade.get("pnl_cash")),
            8,
        )
        totals["headline_risk_cash"] = round(
            totals["headline_risk_cash"] + safe_float(trade.get("risk_cash")),
            8,
        )
        totals["headline_risk_cash_sum"] = totals["headline_risk_cash"]
        totals["headline_risk_pct_sum"] = round(
            totals["headline_risk_pct_sum"] + safe_float(trade.get("risk_pct")),
            8,
        )
        if net > 0:
            totals["headline_winner_count"] += 1
        elif net < 0:
            totals["headline_loser_count"] += 1
        else:
            totals["headline_flat_count"] += 1
    return totals


def headline_authority_bucket_rows(
    bucket_rows: IterableABC[Mapping[str, Any]],
    trade_rows: IterableABC[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    trades = [dict(row) for row in trade_rows]
    output: list[dict[str, Any]] = []
    authority_fields = (
        "net_proxy_r",
        "total_r",
        "gross_r",
        "expected_cost_r",
        "cash_pnl",
        "pnl_cash",
        "risk_cash",
        "risk_cash_sum",
        "risk_pct_sum",
        "filled_trades",
        "filled_trade_count",
        "winner_count",
        "loser_count",
    )
    for raw in bucket_rows:
        row = dict(raw)
        has_trade_totals = any(field in row for field in authority_fields)
        if not has_trade_totals or not trades:
            output.append(row)
            continue
        totals = _headline_trade_bucket_totals(trades, row)
        for field in authority_fields:
            if field in row:
                row[f"all_trade_{field}"] = row.get(field)
        row.update(totals)
        row["bucket_result_authority"] = (
            "headline_result_eligible_trade_rows_with_all_trade_diagnostic_fields"
        )
        row["bucket_result_authority_previous_fields_preserved_as"] = "all_trade_*"
        if "net_proxy_r" in row:
            row["net_proxy_r"] = totals["headline_net_proxy_r"]
        if "total_r" in row:
            row["total_r"] = totals["headline_total_r"]
        if "gross_r" in row:
            row["gross_r"] = totals["headline_gross_r"]
        if "expected_cost_r" in row:
            row["expected_cost_r"] = totals["headline_expected_cost_r"]
        if "cash_pnl" in row:
            row["cash_pnl"] = totals["headline_cash_pnl"]
        if "pnl_cash" in row:
            row["pnl_cash"] = totals["headline_cash_pnl"]
        if "risk_cash" in row:
            row["risk_cash"] = totals["headline_risk_cash"]
        if "risk_cash_sum" in row:
            row["risk_cash_sum"] = totals["headline_risk_cash_sum"]
        if "risk_pct_sum" in row:
            row["risk_pct_sum"] = totals["headline_risk_pct_sum"]
        if "filled_trades" in row:
            row["filled_trades"] = totals["headline_filled_trade_count"]
        if "filled_trade_count" in row:
            row["filled_trade_count"] = totals["headline_filled_trade_count"]
        if "winner_count" in row:
            row["winner_count"] = totals["headline_winner_count"]
        if "loser_count" in row:
            row["loser_count"] = totals["headline_loser_count"]
        output.append(row)
    return output


def strict_full_package_parity_result_exclusion_reason(
    row: Mapping[str, Any],
) -> str | None:
    """Strict/full-package claim metrics exclude replay-repair-only action rows."""

    headline_reason = headline_result_exclusion_reason(row)
    if headline_reason:
        return headline_reason
    selector_action = str(row.get("selector_action") or "").strip().lower()
    if (
        selector_action in REPLAY_REPAIR_ONLY_SELECTOR_ACTIONS
        and not strict_full_package_reduced_action_authority_allowed(row)
    ):
        return "selector_reduced_replay_repair_only_not_strict_full_package_parity"
    return None


class SummaryAccumulator:
    def __init__(self) -> None:
        self.stats: dict[tuple[str, str], dict[str, Any]] = {}
        self.trade_returns: dict[tuple[str, str], list[float]] = defaultdict(list)
        self.physical_trade_returns: dict[tuple[str, str], list[float]] = defaultdict(list)
        self.strict_trade_returns: dict[tuple[str, str], list[float]] = defaultdict(list)
        self.profile_days: dict[tuple[str, str], set[str]] = defaultdict(set)

    def ensure(self, profile: str, split: str) -> dict[str, Any]:
        key = (profile, split)
        if key not in self.stats:
            self.stats[key] = {
                "profile": profile,
                "split": split,
                "decision_rows": 0,
                "scorecard_rows": 0,
                "candidate_rows": 0,
                "candidate_rows_generated_from_decisions": 0,
                "candidate_generating_decision_rows": 0,
                "order_rows": 0,
                "order_event_rows": 0,
                "accepted_pending_order_rows": 0,
                "materialized_order_intent_rows": 0,
                "terminal_order_rows": 0,
                "oracle_rows": 0,
                "missed_opportunity_rows": 0,
                "trade_rows": 0,
                "physical_scoreable_trade_rows": 0,
                "physical_unscoreable_trade_rows": 0,
                "entry_fill_executable_terminal_r_unscoreable_trade_rows": 0,
                "physical_win_count": 0,
                "physical_loss_count": 0,
                "physical_flat_count": 0,
                "physical_gross_r": 0.0,
                "physical_final_r": 0.0,
                "physical_expected_cost_r": 0.0,
                "physical_total_execution_cost_r": 0.0,
                "physical_scoreable_expected_cost_r": 0.0,
                "physical_unscoreable_expected_cost_r": 0.0,
                "physical_scoreable_total_execution_cost_r": 0.0,
                "physical_unscoreable_total_execution_cost_r": 0.0,
                "physical_fallback_execution_surcharge_r": 0.0,
                "physical_net_r": 0.0,
                "physical_cash_pnl": 0.0,
                "physical_risk_cash": 0.0,
                "physical_risk_pct": 0.0,
                "physical_risk_ladder_tier_counts": Counter(),
                "filled_trade_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "flat_count": 0,
                "gross_r": 0.0,
                "final_r": 0.0,
                "expected_cost_r": 0.0,
                "total_execution_cost_r": 0.0,
                "fallback_execution_surcharge_r": 0.0,
                "net_r": 0.0,
                "cash_pnl": 0.0,
                "risk_cash": 0.0,
                "risk_pct": 0.0,
                "missed_positive_net_r": 0.0,
                "missed_negative_net_r": 0.0,
                "missed_total_scoreable_net_r": 0.0,
                "missed_executable_scoreable_net_r": 0.0,
                "missed_diagnostic_opportunity_net_r": 0.0,
                "missed_counterfactual_scoreable_rows": 0,
                "missed_executable_counterfactual_scoreable_rows": 0,
                "missed_diagnostic_counterfactual_scoreable_rows": 0,
                "missed_diagnostic_counterfactual_positive_rows": 0,
                "missed_diagnostic_counterfactual_negative_rows": 0,
                "missed_diagnostic_counterfactual_flat_rows": 0,
                "missed_diagnostic_positive_net_r": 0.0,
                "missed_diagnostic_negative_net_r": 0.0,
                "missed_counterfactual_positive_rows": 0,
                "missed_counterfactual_negative_rows": 0,
                "missed_counterfactual_flat_rows": 0,
                "missed_headline_scoreable_rows": 0,
                "missed_headline_total_net_r": 0.0,
                "missed_executable_cost_passed_rows": 0,
                "missed_executable_cost_passed_total_net_r": 0.0,
                "missed_opportunity_diagnostic_rows": 0,
                "missed_opportunity_diagnostic_total_net_r": 0.0,
                "missed_non_executable_diagnostic_rows": 0,
                "missed_non_executable_diagnostic_total_net_r": 0.0,
                "all_executed_trade_rows": 0,
                "all_executed_net_r": 0.0,
                "headline_trade_rows": 0,
                "headline_filled_trade_count": 0,
                "headline_win_count": 0,
                "headline_loss_count": 0,
                "headline_flat_count": 0,
                "headline_gross_r": 0.0,
                "headline_final_r": 0.0,
                "headline_expected_cost_r": 0.0,
                "headline_total_execution_cost_r": 0.0,
                "headline_net_r": 0.0,
                "strict_full_package_trade_rows": 0,
                "strict_full_package_filled_trade_count": 0,
                "strict_full_package_win_count": 0,
                "strict_full_package_loss_count": 0,
                "strict_full_package_flat_count": 0,
                "strict_full_package_gross_r": 0.0,
                "strict_full_package_final_r": 0.0,
                "strict_full_package_expected_cost_r": 0.0,
                "strict_full_package_total_execution_cost_r": 0.0,
                "strict_full_package_net_r": 0.0,
                "diagnostic_only_trade_rows": 0,
                "diagnostic_only_missing_r_rows": 0,
                "diagnostic_only_net_r": 0.0,
                "source_required_lifecycle_gap_trade_rows": 0,
                "source_required_lifecycle_gap_net_r": 0.0,
                "selected_action_counts": Counter(),
                "selector_action_counts": Counter(),
                "selector_reason_counts": Counter(),
                "selector_source_required_reason_counts": Counter(),
                "selector_source_required_field_counts": Counter(),
                "order_status_counts": Counter(),
                "risk_decision_counts": Counter(),
                "close_reason_counts": Counter(),
                "symbol_counts": Counter(),
                "side_counts": Counter(),
                "session_counts": Counter(),
                "framework_counts": Counter(),
                "current_framework_counts": Counter(),
                "origin_family_counts": Counter(),
                "candidate_origin_family_counts": Counter(),
                "route_family_counts": Counter(),
                "setup_family_counts": Counter(),
                "source_status_counts": Counter(),
                "candidate_generation_by_symbol": Counter(),
                "candidate_generating_decision_rows_by_symbol": Counter(),
                "raw_data_status_by_symbol": defaultdict(Counter),
                "source_required_exception_by_symbol": defaultdict(Counter),
                "policy_counts": Counter(),
                "replay_loss_bucket_guard_status_counts": Counter(),
                "guarded_market_fallback_status_counts": Counter(),
                "guarded_market_fallback_reason_counts": Counter(),
                "guarded_market_fallback_non_eligible_reason_counts": Counter(),
                "guarded_market_fallback_price_source_counts": Counter(),
                "guarded_market_fallback_geometry_mode_counts": Counter(),
                "order_fill_realism_class_counts": Counter(),
                "trade_fill_realism_class_counts": Counter(),
                "missed_fill_realism_class_counts": Counter(),
                "fill_realism_executable_counts": Counter(),
                "fill_realism_reason_counts": Counter(),
                "scheduler_selected_action_before_finalizer_counts": Counter(),
                "risk_finalizer_status_counts": Counter(),
                "risk_finalizer_probe_risk_reason_counts": Counter(),
                "risk_finalizer_probe_dynamic_budget_status_counts": Counter(),
                "risk_finalizer_reallocation_terminal_disposition_counts": Counter(),
                "risk_finalizer_reallocation_terminal_probe_row_count": 0,
                "risk_finalizer_reallocation_terminal_probe_missing_instance_key_count": 0,
                "risk_finalizer_reallocation_terminal_probe_instance_keys": [],
                "headline_result_exclusion_reason_counts": Counter(),
                "strict_full_package_exclusion_reason_counts": Counter(),
                "missed_opportunity_accounting_scope_counts": Counter(),
                "missed_opportunity_r_scoreability_status_counts": Counter(),
                "missed_cost_disposition_counts": Counter(),
                "missed_non_executable_diagnostic_reason_counts": Counter(),
                "risk_finalizer_reallocated_true_rows": 0,
                "risk_finalizer_from_zero_trade_rows": 0,
                "risk_finalizer_original_zero_trade_final_entry_rows": 0,
                "risk_finalizer_reallocation_candidate_probe_count": 0,
                "risk_finalizer_reallocation_admitted_candidate_probe_count": 0,
                "risk_finalizer_reallocation_policy_blocked_probe_count": 0,
                "risk_finalizer_reallocation_quality_blocked_probe_count": 0,
                "risk_finalizer_reallocation_selected_probe_count": 0,
                "risk_finalizer_zero_trade_conversion_candidate_probe_count": 0,
                "risk_finalizer_zero_trade_conversion_policy_blocked_probe_count": 0,
                "risk_finalizer_zero_trade_conversion_selected_probe_count": 0,
                "guarded_market_fallback_applied_count": 0,
                "guarded_market_fallback_applied_order_trade_count": 0,
                "guarded_market_fallback_original_sl_tp_preserved_count": 0,
                "guarded_market_fallback_reanchored_geometry_count": 0,
                "guarded_market_fallback_contract_unmet_count": 0,
                "selected_contract_unmet_rows": 0,
                "selected_contract_unmet_expected_net_r": 0.0,
                "selected_contract_unmet_reason_counts": Counter(),
                "selected_contract_unmet_instance_keys": [],
                "model_prior_only_not_executable_count": 0,
                "cancel_replace_event_count": 0,
                "cancel_replace_terminal_rows": 0,
                "cancel_replace_event_rows": 0,
                "cancel_replace_unique_order_ids": 0,
                "pending_replacement_applied_terminal_rows": 0,
                "delay_or_hold_count": 0,
                "skip_count": 0,
                "reduce_risk_count": 0,
            }
        return self.stats[key]

    def add_result(
        self,
        *,
        profile: str,
        split: str,
        days: tuple[str, ...],
        result: Mapping[str, Any],
    ) -> None:
        normalize_replay_result_ledgers(result)
        stat = self.ensure(profile, split)
        self.profile_days[(profile, split)].update(days)
        ledgers = result["ledgers"]
        stat["decision_rows"] += len(ledgers.get("asof", []))
        stat["scorecard_rows"] += len(ledgers.get("scorecard", []))
        stat["candidate_rows"] += len(ledgers.get("candidate", []))
        order_rows = list(ledgers.get("order", []))
        stat["order_event_rows"] += len(order_rows)
        materialized_intent_rows = [
            row
            for row in order_rows
            if row.get("order_intent_materialized") is True
            and row.get("is_terminal_order_event") is not True
            and str(row.get("order_status") or "") not in TERMINAL_ORDER_STATUSES
        ]
        stat["accepted_pending_order_rows"] += len(materialized_intent_rows)
        stat["materialized_order_intent_rows"] += len(materialized_intent_rows)
        terminal_order_by_id: dict[str, Mapping[str, Any]] = {}
        for row in order_rows:
            order_id = str(row.get("simulated_order_id") or "")
            status = str(row.get("order_status") or "")
            if not order_id or status not in TERMINAL_ORDER_STATUSES:
                continue
            terminal_order_by_id[order_id] = row
        terminal_order_rows = list(terminal_order_by_id.values())
        stat["terminal_order_rows"] += len(terminal_order_rows)
        stat["order_rows"] += len(terminal_order_rows)
        stat["oracle_rows"] += len(ledgers.get("oracle", []))
        stat["missed_opportunity_rows"] += len(ledgers.get("missed", []))
        for row in ledgers.get("asof", []):
            symbol = str(row.get("symbol") or "UNKNOWN")
            raw_status = str(row.get("raw_data_status") or "UNKNOWN")
            candidate_count = int(row.get("candidate_count") or 0)
            counter_add(stat["source_status_counts"], raw_status)
            stat["raw_data_status_by_symbol"][symbol][raw_status] += 1
            exception_type = row.get("source_required_exception_type")
            if exception_type:
                stat["source_required_exception_by_symbol"][symbol][
                    str(exception_type)
                ] += 1
            stat["candidate_rows_generated_from_decisions"] += candidate_count
            if candidate_count > 0:
                stat["candidate_generating_decision_rows"] += 1
                stat["candidate_generation_by_symbol"][symbol] += candidate_count
                stat["candidate_generating_decision_rows_by_symbol"][symbol] += 1
        for row in ledgers.get("scorecard", []):
            before_action = str(
                row.get("scheduler_selected_action_class_before_risk_finalizer") or ""
            )
            after_action = str(row.get("selected_action_class") or "")
            counter_add(stat["selected_action_counts"], after_action)
            counter_add(
                stat["scheduler_selected_action_before_finalizer_counts"],
                before_action,
            )
            finalizer = row.get("risk_admitted_scheduler_finalizer")
            finalizer = finalizer if isinstance(finalizer, Mapping) else {}
            counter_add(stat["risk_finalizer_status_counts"], finalizer.get("status"))
            if finalizer.get("reallocated") is True:
                stat["risk_finalizer_reallocated_true_rows"] += 1
            stat["risk_finalizer_reallocation_candidate_probe_count"] += int(
                finalizer.get("reallocation_candidate_probe_count") or 0
            )
            stat["risk_finalizer_reallocation_admitted_candidate_probe_count"] += int(
                finalizer.get("reallocation_admitted_candidate_probe_count") or 0
            )
            stat["risk_finalizer_reallocation_policy_blocked_probe_count"] += int(
                finalizer.get("reallocation_policy_blocked_probe_count") or 0
            )
            stat["risk_finalizer_reallocation_quality_blocked_probe_count"] += int(
                finalizer.get("reallocation_quality_blocked_probe_count") or 0
            )
            stat["risk_finalizer_reallocation_selected_probe_count"] += int(
                finalizer.get("reallocation_selected_probe_count") or 0
            )
            reallocation_terminal_probe_rows = finalizer.get(
                "reallocation_terminal_probe_rows"
            )
            reallocation_terminal_probe_rows = (
                reallocation_terminal_probe_rows
                if isinstance(reallocation_terminal_probe_rows, list)
                else []
            )
            stat[
                "risk_finalizer_reallocation_terminal_probe_row_count"
            ] += len(reallocation_terminal_probe_rows)
            for terminal_probe in reallocation_terminal_probe_rows:
                if not isinstance(terminal_probe, Mapping):
                    continue
                counter_add(
                    stat[
                        "risk_finalizer_reallocation_terminal_disposition_counts"
                    ],
                    terminal_probe.get("reallocation_terminal_disposition"),
                )
                instance_key = str(
                    terminal_probe.get("canonical_replay_candidate_instance_key")
                    or terminal_probe.get(
                        "source_bound_replay_candidate_instance_key"
                    )
                    or terminal_probe.get("risk_finalizer_probe_instance_key")
                    or ""
                ).strip()
                if instance_key:
                    stat[
                        "risk_finalizer_reallocation_terminal_probe_instance_keys"
                    ].append(instance_key)
                else:
                    stat[
                        "risk_finalizer_reallocation_terminal_probe_missing_instance_key_count"
                    ] += 1
            stat["risk_finalizer_zero_trade_conversion_candidate_probe_count"] += int(
                finalizer.get("zero_trade_conversion_candidate_probe_count") or 0
            )
            stat[
                "risk_finalizer_zero_trade_conversion_policy_blocked_probe_count"
            ] += int(
                finalizer.get("zero_trade_conversion_policy_blocked_probe_count") or 0
            )
            stat["risk_finalizer_zero_trade_conversion_selected_probe_count"] += int(
                finalizer.get("zero_trade_conversion_selected_probe_count") or 0
            )
            if (
                finalizer.get("status")
                == "risk_admitted_selection_materialized_from_zero_trade"
            ):
                stat["risk_finalizer_from_zero_trade_rows"] += 1
            if before_action == "zero_trade" and after_action in {
                "new_position",
                "same_direction_scale_in",
                "close_and_reverse",
            }:
                stat["risk_finalizer_original_zero_trade_final_entry_rows"] += 1
            for probe in finalizer.get("probe_rows") or []:
                if not isinstance(probe, Mapping):
                    continue
                counter_add(
                    stat["risk_finalizer_probe_risk_reason_counts"],
                    probe.get("risk_decision_reason") or probe.get("status"),
                )
                counter_add(
                    stat["risk_finalizer_probe_dynamic_budget_status_counts"],
                    probe.get("dynamic_daily_drawdown_budget_status"),
                )
        for row in ledgers.get("candidate", []):
            counter_add(stat["selector_action_counts"], row.get("selector_action"))
            counter_add(
                stat["selector_reason_counts"],
                row.get("selector_reason") or row.get("selector_decision_reason"),
            )
            action = str(row.get("selector_action") or "")
            if action == "source-required":
                counter_add(
                    stat["selector_source_required_reason_counts"],
                    row.get("selector_reason") or row.get("selector_decision_reason"),
                )
                source_required_fields = row.get("source_required_fields")
                if isinstance(source_required_fields, str):
                    for field in source_required_fields.split(","):
                        counter_add(
                            stat["selector_source_required_field_counts"],
                            field.strip(),
                        )
                elif isinstance(source_required_fields, IterableABC):
                    for field in source_required_fields:
                        counter_add(
                            stat["selector_source_required_field_counts"],
                            field,
                        )
            if action in {"skip", "reject", "blocked"}:
                stat["skip_count"] += 1
            if action in {"delay", "hold"}:
                stat["delay_or_hold_count"] += 1
        cancel_replace_unique_order_ids: set[str] = set()
        def record_guarded_market_fallback_row(row: Mapping[str, Any]) -> None:
            status = row.get("guarded_market_fallback_status")
            counter_add(stat["guarded_market_fallback_status_counts"], status)
            reasons = row.get("guarded_market_fallback_reasons")
            if isinstance(reasons, str):
                reason_values = [reasons]
            elif isinstance(reasons, IterableABC):
                reason_values = list(reasons)
            else:
                reason_values = []
            single_reason = row.get("guarded_market_fallback_reason")
            if single_reason not in (None, "", [], {}):
                reason_values.append(single_reason)
            for reason in reason_values:
                counter_add(stat["guarded_market_fallback_reason_counts"], reason)
                if status == "not_eligible":
                    counter_add(
                        stat["guarded_market_fallback_non_eligible_reason_counts"],
                        reason,
                    )
            counter_add(
                stat["guarded_market_fallback_price_source_counts"],
                row.get("fallback_fill_price_source")
                or row.get("guarded_market_fallback_fill_price_source"),
            )
            counter_add(
                stat["guarded_market_fallback_geometry_mode_counts"],
                row.get("fallback_geometry_mode"),
            )
            if row.get("fallback_geometry_original_sl_tp_preserved") is True:
                stat["guarded_market_fallback_original_sl_tp_preserved_count"] += 1
            if row.get("fallback_geometry_reanchored") is True:
                stat["guarded_market_fallback_reanchored_geometry_count"] += 1
            if row.get("package_marketable_guarded_fallback_contract_unmet") is True:
                stat["guarded_market_fallback_contract_unmet_count"] += 1
            if row.get("guarded_market_fallback_applied") is True:
                stat["guarded_market_fallback_applied_order_trade_count"] += 1
            if (
                row.get("fill_probability_authority_class")
                == "predecision_model_prior_not_fill_execution_authority"
                and row.get("package_replay_executable_candidate_use_allowed") is False
            ):
                stat["model_prior_only_not_executable_count"] += 1

        for row in terminal_order_rows:
            counter_add(stat["order_status_counts"], row.get("order_status"))
            counter_add(stat["risk_decision_counts"], row.get("risk_decision"))
            if (
                row.get("order_status") == "guarded_market_fallback_contract_unmet"
                or row.get("package_marketable_guarded_fallback_contract_unmet") is True
            ):
                stat["selected_contract_unmet_rows"] += 1
                stat["selected_contract_unmet_expected_net_r"] = round(
                    stat["selected_contract_unmet_expected_net_r"]
                    + safe_float(row.get("expected_net_r")),
                    8,
                )
                counter_add(
                    stat["selected_contract_unmet_reason_counts"],
                    row.get("package_marketable_guarded_fallback_contract_unmet_reason")
                    or row.get("guarded_market_fallback_reason")
                    or row.get("fill_status")
                    or row.get("order_status"),
                )
                instance_key = (
                    row.get("canonical_replay_candidate_instance_key")
                    or (
                        f"{row.get('candidate_id')}@@{row.get('decision_time_utc')}"
                        if row.get("candidate_id") and row.get("decision_time_utc")
                        else row.get("simulated_order_id")
                    )
                )
                if instance_key:
                    stat["selected_contract_unmet_instance_keys"].append(str(instance_key))
            counter_add(
                stat["replay_loss_bucket_guard_status_counts"],
                row.get("replay_loss_bucket_guard_status")
                or (
                    row.get("risk_authority", {}).get("replay_loss_bucket_guard_status")
                    if isinstance(row.get("risk_authority"), Mapping)
                    else None
                ),
            )
            if "reduce" in str(row.get("risk_decision") or "").lower():
                stat["reduce_risk_count"] += 1
            if row.get("pending_replacement_applied") is True:
                stat["pending_replacement_applied_terminal_rows"] += 1
            if row.get("order_status") == "cancelled_replaced_by_scheduler_v4":
                stat["cancel_replace_terminal_rows"] += 1
                order_id = str(row.get("simulated_order_id") or "")
                if order_id:
                    cancel_replace_unique_order_ids.add(order_id)
            counter_add(
                stat["order_fill_realism_class_counts"],
                row.get("fill_realism_class"),
            )
            counter_add(
                stat["fill_realism_executable_counts"],
                row.get("fill_realism_executable"),
            )
            counter_add(
                stat["fill_realism_reason_counts"],
                row.get("fill_realism_reason"),
            )
            record_guarded_market_fallback_row(row)
            if row.get("guarded_market_fallback_applied") is True:
                stat["guarded_market_fallback_applied_count"] += 1
        for row in ledgers.get("trade", []):
            record_guarded_market_fallback_row(row)
        for row in ledgers.get("event", []):
            if "cancel" in json.dumps(row, sort_keys=True, default=str).lower():
                stat["cancel_replace_event_rows"] += 1
                order_id = str(row.get("simulated_order_id") or "")
                if order_id:
                    cancel_replace_unique_order_ids.add(order_id)
        stat["cancel_replace_unique_order_ids"] = len(cancel_replace_unique_order_ids)
        stat["cancel_replace_event_count"] = (
            stat["cancel_replace_terminal_rows"] + stat["cancel_replace_event_rows"]
        )
        for row in ledgers.get("missed", []):
            counter_add(
                stat["missed_opportunity_accounting_scope_counts"],
                row.get("missed_opportunity_accounting_scope"),
            )
            counter_add(
                stat["missed_opportunity_r_scoreability_status_counts"],
                row.get("missed_opportunity_r_scoreability_status"),
            )
            counter_add(
                stat["missed_cost_disposition_counts"],
                row.get("missed_cost_disposition"),
            )
            counter_add(
                stat["missed_non_executable_diagnostic_reason_counts"],
                row.get("missed_non_executable_diagnostic_reason"),
            )
            counter_add(
                stat["missed_fill_realism_class_counts"],
                row.get("fill_realism_class"),
            )
            accounting_scope = str(row.get("missed_opportunity_accounting_scope") or "")
            headline_scope = bool(
                row.get("missed_opportunity_headline_r_scoreable") is True
                and row.get("missed_opportunity_headline_execution_bound_eligible")
                is True
                and row.get("executable_finalized") is True
                and row.get("order_status") != "not_sent_missed_opportunity"
            )
            cost_passed_opportunity_scope = (
                missed_opportunity_execution_bound_cost_passed_scope(row)
            )
            diagnostic_scope = str(
                row.get("missed_opportunity_accounting_scope") or ""
            ).startswith("non_executable_")
            executable_net = row.get("net_proxy_r")
            opportunity_net = row.get("opportunity_net_proxy_r")
            scoreability_status = str(
                row.get("missed_opportunity_r_scoreability_status") or ""
            )
            counterfactual_scoreable = bool(
                row.get("missed_opportunity_counterfactual_scoreable") is True
                or scoreability_status
                in {
                    "headline_r_scoreable",
                    "diagnostic_opportunity_r_scoreable",
                }
            )
            scoreable_net = (
                executable_net
                if headline_scope and executable_net is not None
                else opportunity_net
            )
            executable_counterfactual_scoreable = bool(
                counterfactual_scoreable
                and scoreable_net is not None
                and not diagnostic_scope
                and (
                    headline_scope
                    or cost_passed_opportunity_scope
                    or scoreability_status == "headline_r_scoreable"
                )
            )
            diagnostic_counterfactual_scoreable = bool(
                counterfactual_scoreable
                and scoreable_net is not None
                and not executable_counterfactual_scoreable
            )
            if counterfactual_scoreable and scoreable_net is not None:
                net_f = safe_float(scoreable_net)
                stat["missed_counterfactual_scoreable_rows"] += 1
                if executable_counterfactual_scoreable:
                    stat["missed_executable_counterfactual_scoreable_rows"] += 1
                    stat["missed_executable_scoreable_net_r"] = round(
                        stat["missed_executable_scoreable_net_r"] + net_f,
                        8,
                    )
                    stat["missed_total_scoreable_net_r"] = round(
                        stat["missed_total_scoreable_net_r"] + net_f, 8
                    )
                    if net_f > 0:
                        stat["missed_counterfactual_positive_rows"] += 1
                        stat["missed_positive_net_r"] = round(
                            stat["missed_positive_net_r"] + net_f,
                            8,
                        )
                    elif net_f < 0:
                        stat["missed_counterfactual_negative_rows"] += 1
                        stat["missed_negative_net_r"] = round(
                            stat["missed_negative_net_r"] + net_f,
                            8,
                        )
                    else:
                        stat["missed_counterfactual_flat_rows"] += 1
                elif diagnostic_counterfactual_scoreable:
                    stat["missed_diagnostic_counterfactual_scoreable_rows"] += 1
                    stat["missed_diagnostic_opportunity_net_r"] = round(
                        stat["missed_diagnostic_opportunity_net_r"] + net_f,
                        8,
                    )
                    if net_f > 0:
                        stat["missed_diagnostic_counterfactual_positive_rows"] += 1
                        stat["missed_diagnostic_positive_net_r"] = round(
                            stat["missed_diagnostic_positive_net_r"] + net_f,
                            8,
                        )
                    elif net_f < 0:
                        stat["missed_diagnostic_counterfactual_negative_rows"] += 1
                        stat["missed_diagnostic_negative_net_r"] = round(
                            stat["missed_diagnostic_negative_net_r"] + net_f,
                            8,
                        )
                    else:
                        stat["missed_diagnostic_counterfactual_flat_rows"] += 1
            if headline_scope and executable_net is not None:
                net_f = safe_float(executable_net)
                stat["missed_headline_scoreable_rows"] += 1
                stat["missed_headline_total_net_r"] = round(
                    stat["missed_headline_total_net_r"] + net_f,
                    8,
                )
            if cost_passed_opportunity_scope and opportunity_net is not None:
                net_f = safe_float(opportunity_net)
                stat["missed_executable_cost_passed_rows"] += 1
                stat["missed_executable_cost_passed_total_net_r"] = round(
                    stat["missed_executable_cost_passed_total_net_r"] + net_f,
                    8,
                )
                stat["missed_opportunity_diagnostic_rows"] += 1
                stat["missed_opportunity_diagnostic_total_net_r"] = round(
                    stat["missed_opportunity_diagnostic_total_net_r"] + net_f,
                    8,
                )
            if diagnostic_scope and opportunity_net is not None:
                net_f = safe_float(opportunity_net)
                stat["missed_non_executable_diagnostic_rows"] += 1
                stat["missed_non_executable_diagnostic_total_net_r"] = round(
                    stat["missed_non_executable_diagnostic_total_net_r"]
                    + net_f,
                    8,
                )
                stat["missed_opportunity_diagnostic_rows"] += 1
                stat["missed_opportunity_diagnostic_total_net_r"] = round(
                    stat["missed_opportunity_diagnostic_total_net_r"] + net_f,
                    8,
                )
        for row in ledgers.get("trade", []):
            stat["trade_rows"] += 1
            stat["physical_risk_cash"] += safe_float(row.get("risk_cash"))
            stat["physical_risk_pct"] += safe_float(row.get("risk_pct"))
            physical_expected_cost_r = safe_float(row.get("expected_cost_r"))
            physical_total_execution_cost_r = safe_float(
                row.get("total_execution_cost_r"),
                row.get("expected_cost_r"),
            )
            stat["physical_expected_cost_r"] += physical_expected_cost_r
            stat[
                "physical_total_execution_cost_r"
            ] += physical_total_execution_cost_r
            stat["physical_fallback_execution_surcharge_r"] += safe_float(
                row.get("fallback_execution_surcharge_r")
            )
            physical_ladder = row.get("risk_expression_ladder")
            physical_ladder = (
                physical_ladder if isinstance(physical_ladder, Mapping) else {}
            )
            physical_risk_tier = str(
                row.get("risk_expression_ladder_tier")
                or physical_ladder.get("ladder_tier")
                or row.get("risk_decision")
                or "unknown"
            ).strip() or "unknown"
            if physical_risk_tier in {"trade", "open-full-risk", "full-risk"}:
                physical_risk_tier = "full"
            elif physical_risk_tier in {
                "reduce-risk",
                "open-reduced-risk",
                "reduced-risk",
            }:
                physical_risk_tier = "reduced"
            counter_add(
                stat["physical_risk_ladder_tier_counts"],
                physical_risk_tier,
            )
            counter_add(
                stat["trade_fill_realism_class_counts"],
                row.get("fill_realism_class"),
            )
            counter_add(
                stat["fill_realism_executable_counts"],
                row.get("fill_realism_executable"),
            )
            counter_add(
                stat["fill_realism_reason_counts"],
                row.get("fill_realism_reason"),
            )
            exclusion_reason = headline_result_exclusion_reason(row)
            exclusion_key = exclusion_reason or "headline_result_eligible"
            counter_add(stat["headline_result_exclusion_reason_counts"], exclusion_key)
            strict_exclusion_reason = strict_full_package_parity_result_exclusion_reason(row)
            strict_exclusion_key = (
                strict_exclusion_reason
                or "strict_full_package_parity_result_eligible"
            )
            counter_add(
                stat["strict_full_package_exclusion_reason_counts"],
                strict_exclusion_key,
            )
            if row.get("net_proxy_r") is None:
                stat["physical_unscoreable_trade_rows"] += 1
                stat[
                    "physical_unscoreable_expected_cost_r"
                ] += physical_expected_cost_r
                stat[
                    "physical_unscoreable_total_execution_cost_r"
                ] += physical_total_execution_cost_r
                if (
                    row.get("entry_fill_executable") is True
                    and row.get("terminal_r_scoreable") is False
                ):
                    stat[
                        "entry_fill_executable_terminal_r_unscoreable_trade_rows"
                    ] += 1
                if exclusion_reason:
                    stat["diagnostic_only_trade_rows"] += 1
                    stat["diagnostic_only_missing_r_rows"] += 1
                continue
            stat["physical_scoreable_trade_rows"] += 1
            stat[
                "physical_scoreable_expected_cost_r"
            ] += physical_expected_cost_r
            stat[
                "physical_scoreable_total_execution_cost_r"
            ] += physical_total_execution_cost_r
            net = safe_float(row.get("net_proxy_r"))
            gross = safe_float(row.get("gross_r"))
            final_r = safe_float(row.get("final_r"), gross)
            stat["physical_gross_r"] += gross
            stat["physical_final_r"] += final_r
            stat["physical_net_r"] += net
            stat["physical_cash_pnl"] += safe_float(row.get("pnl_cash"))
            self.physical_trade_returns[(profile, split)].append(net)
            if net > 0:
                stat["physical_win_count"] += 1
            elif net < 0:
                stat["physical_loss_count"] += 1
            else:
                stat["physical_flat_count"] += 1
            if exclusion_reason:
                stat["diagnostic_only_trade_rows"] += 1
                stat["diagnostic_only_net_r"] = round(
                    stat["diagnostic_only_net_r"] + net, 8
                )
                if (
                    exclusion_reason
                    == "source_required_fail_closed_lifecycle_source_gap_diagnostic_only"
                ):
                    stat["source_required_lifecycle_gap_trade_rows"] += 1
                    stat["source_required_lifecycle_gap_net_r"] = round(
                        stat["source_required_lifecycle_gap_net_r"] + net, 8
                    )
                continue
            stat["filled_trade_count"] += 1
            stat["all_executed_trade_rows"] += 1
            stat["all_executed_net_r"] = round(
                stat["all_executed_net_r"] + net, 8
            )
            stat["gross_r"] = round(stat["gross_r"] + gross, 8)
            stat["final_r"] = round(stat["final_r"] + final_r, 8)
            stat["expected_cost_r"] = round(
                stat["expected_cost_r"] + safe_float(row.get("expected_cost_r")), 8
            )
            stat["total_execution_cost_r"] = round(
                stat["total_execution_cost_r"]
                + safe_float(row.get("total_execution_cost_r"), row.get("expected_cost_r")),
                8,
            )
            stat["fallback_execution_surcharge_r"] = round(
                stat["fallback_execution_surcharge_r"]
                + safe_float(row.get("fallback_execution_surcharge_r")),
                8,
            )
            stat["net_r"] = round(stat["net_r"] + net, 8)
            stat["cash_pnl"] = round(stat["cash_pnl"] + safe_float(row.get("pnl_cash")), 8)
            stat["risk_cash"] = round(stat["risk_cash"] + safe_float(row.get("risk_cash")), 8)
            stat["risk_pct"] = round(stat["risk_pct"] + safe_float(row.get("risk_pct")), 8)
            stat["headline_trade_rows"] += 1
            stat["headline_filled_trade_count"] += 1
            stat["headline_gross_r"] = round(stat["headline_gross_r"] + gross, 8)
            stat["headline_final_r"] = round(stat["headline_final_r"] + final_r, 8)
            stat["headline_expected_cost_r"] = round(
                stat["headline_expected_cost_r"]
                + safe_float(row.get("expected_cost_r")),
                8,
            )
            stat["headline_total_execution_cost_r"] = round(
                stat["headline_total_execution_cost_r"]
                + safe_float(row.get("total_execution_cost_r"), row.get("expected_cost_r")),
                8,
            )
            stat["headline_net_r"] = round(stat["headline_net_r"] + net, 8)
            self.trade_returns[(profile, split)].append(net)
            if strict_exclusion_reason is None:
                stat["strict_full_package_trade_rows"] += 1
                stat["strict_full_package_filled_trade_count"] += 1
                stat["strict_full_package_gross_r"] = round(
                    stat["strict_full_package_gross_r"] + gross,
                    8,
                )
                stat["strict_full_package_final_r"] = round(
                    stat["strict_full_package_final_r"] + final_r,
                    8,
                )
                stat["strict_full_package_expected_cost_r"] = round(
                    stat["strict_full_package_expected_cost_r"]
                    + safe_float(row.get("expected_cost_r")),
                    8,
                )
                stat["strict_full_package_total_execution_cost_r"] = round(
                    stat["strict_full_package_total_execution_cost_r"]
                    + safe_float(
                        row.get("total_execution_cost_r"),
                        row.get("expected_cost_r"),
                    ),
                    8,
                )
                stat["strict_full_package_net_r"] = round(
                    stat["strict_full_package_net_r"] + net,
                    8,
                )
                self.strict_trade_returns[(profile, split)].append(net)
            if net > 0:
                stat["win_count"] += 1
                stat["headline_win_count"] += 1
                if strict_exclusion_reason is None:
                    stat["strict_full_package_win_count"] += 1
            elif net < 0:
                stat["loss_count"] += 1
                stat["headline_loss_count"] += 1
                if strict_exclusion_reason is None:
                    stat["strict_full_package_loss_count"] += 1
            else:
                stat["flat_count"] += 1
                stat["headline_flat_count"] += 1
                if strict_exclusion_reason is None:
                    stat["strict_full_package_flat_count"] += 1
            counter_add(stat["close_reason_counts"], row.get("close_reason"))
            counter_add(stat["symbol_counts"], row.get("symbol"))
            counter_add(stat["side_counts"], row.get("side"))
            counter_add(stat["session_counts"], row.get("route_session") or row.get("session"))
            counter_add(stat["framework_counts"], row.get("framework"))
            counter_add(stat["current_framework_counts"], row.get("current_framework"))
            counter_add(stat["origin_family_counts"], row.get("origin_family"))
            counter_add(
                stat["candidate_origin_family_counts"],
                row.get("candidate_origin_family"),
            )
            counter_add(stat["route_family_counts"], row.get("route_family"))
            counter_add(stat["setup_family_counts"], row.get("setup_family"))
            counter_add(
                stat["policy_counts"],
                row.get("dynamic_geometry_policy")
                or row.get("gtos_vnext_dynamic_policy_selected"),
            )

    def serializable_stats(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for key in sorted(self.stats):
            row = dict(self.stats[key])
            profile, split = key
            row["trading_days"] = len(self.profile_days[key])
            row["trade_frequency_per_day"] = (
                round(row["filled_trade_count"] / len(self.profile_days[key]), 8)
                if self.profile_days[key]
                else 0.0
            )
            row["win_rate"] = (
                round(row["win_count"] / row["filled_trade_count"], 8)
                if row["filled_trade_count"]
                else None
            )
            for counter_key in (
                "selected_action_counts",
                "selector_action_counts",
                "selector_reason_counts",
                "physical_risk_ladder_tier_counts",
                "selector_source_required_reason_counts",
                "selector_source_required_field_counts",
                "order_status_counts",
                "risk_decision_counts",
                "close_reason_counts",
                "symbol_counts",
                "side_counts",
                "session_counts",
                "framework_counts",
                "current_framework_counts",
                "origin_family_counts",
                "candidate_origin_family_counts",
                "route_family_counts",
                "setup_family_counts",
                "source_status_counts",
                "candidate_generation_by_symbol",
                "candidate_generating_decision_rows_by_symbol",
                "policy_counts",
                "replay_loss_bucket_guard_status_counts",
                "guarded_market_fallback_status_counts",
                "guarded_market_fallback_reason_counts",
                "guarded_market_fallback_non_eligible_reason_counts",
                "guarded_market_fallback_price_source_counts",
                "guarded_market_fallback_geometry_mode_counts",
                "order_fill_realism_class_counts",
                "trade_fill_realism_class_counts",
                "missed_fill_realism_class_counts",
                "fill_realism_executable_counts",
                "fill_realism_reason_counts",
                "selected_contract_unmet_reason_counts",
                "scheduler_selected_action_before_finalizer_counts",
                "risk_finalizer_status_counts",
                "risk_finalizer_probe_risk_reason_counts",
                "risk_finalizer_probe_dynamic_budget_status_counts",
                "risk_finalizer_reallocation_terminal_disposition_counts",
                "headline_result_exclusion_reason_counts",
                "strict_full_package_exclusion_reason_counts",
                "missed_opportunity_accounting_scope_counts",
                "missed_opportunity_r_scoreability_status_counts",
                "missed_cost_disposition_counts",
                "missed_non_executable_diagnostic_reason_counts",
            ):
                row[counter_key] = dict(row[counter_key])
            for nested_counter_key in (
                "raw_data_status_by_symbol",
                "source_required_exception_by_symbol",
            ):
                row[nested_counter_key] = {
                    key: dict(value)
                    for key, value in sorted(row[nested_counter_key].items())
                }
            for physical_metric in (
                "physical_gross_r",
                "physical_final_r",
                "physical_expected_cost_r",
                "physical_total_execution_cost_r",
                "physical_scoreable_expected_cost_r",
                "physical_unscoreable_expected_cost_r",
                "physical_scoreable_total_execution_cost_r",
                "physical_unscoreable_total_execution_cost_r",
                "physical_fallback_execution_surcharge_r",
                "physical_net_r",
                "physical_cash_pnl",
                "physical_risk_cash",
                "physical_risk_pct",
            ):
                row[physical_metric] = round(float(row[physical_metric]), 8)
            row["physical_trade_frequency_per_day"] = (
                round(row["trade_rows"] / len(self.profile_days[key]), 8)
                if self.profile_days[key]
                else 0.0
            )
            row["physical_scoreable_trade_frequency_per_day"] = (
                round(
                    row["physical_scoreable_trade_rows"]
                    / len(self.profile_days[key]),
                    8,
                )
                if self.profile_days[key]
                else 0.0
            )
            row["physical_win_rate"] = (
                round(
                    row["physical_win_count"]
                    / row["physical_scoreable_trade_rows"],
                    8,
                )
                if row["physical_scoreable_trade_rows"]
                else None
            )
            row["physical_full_risk_trade_rows"] = row[
                "physical_risk_ladder_tier_counts"
            ].get("full", 0)
            row["physical_reduced_risk_trade_rows"] = row[
                "physical_risk_ladder_tier_counts"
            ].get("reduced", 0)
            row["headline_trade_frequency_per_day"] = (
                round(row["headline_filled_trade_count"] / len(self.profile_days[key]), 8)
                if self.profile_days[key]
                else 0.0
            )
            row["strict_full_package_trade_frequency_per_day"] = (
                round(
                    row["strict_full_package_filled_trade_count"]
                    / len(self.profile_days[key]),
                    8,
                )
                if self.profile_days[key]
                else 0.0
            )
            row["strict_full_package_win_rate"] = (
                round(
                    row["strict_full_package_win_count"]
                    / row["strict_full_package_filled_trade_count"],
                    8,
                )
                if row["strict_full_package_filled_trade_count"]
                else None
            )
            row["stress"] = stress_summary(self.trade_returns[key])
            row["monte_carlo"] = monte_carlo_summary(self.trade_returns[key])
            row["physical_stress"] = stress_summary(
                self.physical_trade_returns[key]
            )
            row["physical_monte_carlo"] = monte_carlo_summary(
                self.physical_trade_returns[key]
            )
            row["strict_full_package_stress"] = stress_summary(
                self.strict_trade_returns[key]
            )
            row["strict_full_package_monte_carlo"] = monte_carlo_summary(
                self.strict_trade_returns[key]
            )
            row["selected_contract_unmet_instance_keys"] = sorted(
                set(row["selected_contract_unmet_instance_keys"])
            )
            reallocation_instance_keys = list(
                row[
                    "risk_finalizer_reallocation_terminal_probe_instance_keys"
                ]
            )
            reallocation_instance_counts = Counter(reallocation_instance_keys)
            row[
                "risk_finalizer_reallocation_terminal_probe_instance_keys"
            ] = sorted(reallocation_instance_counts)
            row[
                "risk_finalizer_reallocation_terminal_probe_duplicate_instance_keys"
            ] = sorted(
                key
                for key, count in reallocation_instance_counts.items()
                if count > 1
            )
            row[
                "risk_finalizer_reallocation_terminal_probe_unique_instance_count"
            ] = len(reallocation_instance_counts)
            row[
                "risk_finalizer_reallocation_terminal_probe_reconciled"
            ] = bool(
                row[
                    "risk_finalizer_reallocation_terminal_probe_row_count"
                ]
                == row["risk_finalizer_reallocation_candidate_probe_count"]
                and row[
                    "risk_finalizer_reallocation_terminal_probe_missing_instance_key_count"
                ]
                == 0
                and not row[
                    "risk_finalizer_reallocation_terminal_probe_duplicate_instance_keys"
                ]
                and len(reallocation_instance_keys)
                == len(reallocation_instance_counts)
            )
            rows.append(row)
        return rows


PHYSICAL_TRADE_SUMMARY_RECONCILIATION_FIELDS: tuple[str, ...] = (
    "trade_rows",
    "physical_scoreable_trade_rows",
    "physical_unscoreable_trade_rows",
    "entry_fill_executable_terminal_r_unscoreable_trade_rows",
    "physical_win_count",
    "physical_loss_count",
    "physical_flat_count",
    "physical_gross_r",
    "physical_final_r",
    "physical_expected_cost_r",
    "physical_total_execution_cost_r",
    "physical_scoreable_expected_cost_r",
    "physical_unscoreable_expected_cost_r",
    "physical_scoreable_total_execution_cost_r",
    "physical_unscoreable_total_execution_cost_r",
    "physical_fallback_execution_surcharge_r",
    "physical_net_r",
    "physical_cash_pnl",
    "physical_risk_cash",
    "physical_risk_pct",
    "physical_risk_ladder_tier_counts",
    "physical_trade_frequency_per_day",
    "physical_scoreable_trade_frequency_per_day",
    "physical_win_rate",
    "physical_full_risk_trade_rows",
    "physical_reduced_risk_trade_rows",
    "physical_stress",
    "physical_monte_carlo",
)


def reconcile_physical_summary_stats_from_trade_ledger(
    stats: list[dict[str, Any]],
    trade_path: Path,
) -> list[dict[str, Any]]:
    """Rebuild physical metrics from the canonical serialized trade surface."""

    if not trade_path.exists() or trade_path.stat().st_size <= 0:
        return stats
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    days_by_key: dict[tuple[str, str], set[str]] = defaultdict(set)
    with trade_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("serialized_trade_summary_reconciliation_row_not_mapping")
            key = (str(row.get("profile") or ""), str(row.get("split") or ""))
            if not all(key):
                raise ValueError("serialized_trade_summary_reconciliation_scope_missing")
            rows_by_key[key].append(row)
            trading_day = str(row.get("trading_day") or "")
            if trading_day:
                days_by_key[key].add(trading_day)

    rebuilt = SummaryAccumulator()
    for (profile, split), rows in rows_by_key.items():
        rebuilt.add_result(
            profile=profile,
            split=split,
            days=tuple(sorted(days_by_key[(profile, split)])),
            result={"ledgers": {"trade": rows}},
        )
    rebuilt_by_key = {
        (str(row.get("profile") or ""), str(row.get("split") or "")): row
        for row in rebuilt.serializable_stats()
    }
    for stat in stats:
        key = (str(stat.get("profile") or ""), str(stat.get("split") or ""))
        projection = rebuilt_by_key.get(key)
        if projection is None:
            continue
        for field in PHYSICAL_TRADE_SUMMARY_RECONCILIATION_FIELDS:
            stat[field] = projection.get(field)
    return stats


def physical_trade_summary_serialized_ledger_parity_contract() -> dict[str, Any]:
    return {
        "schema": "gtos.broad_replay.physical_trade_summary_parity.v1",
        "canonical_result_ledger_normalization_before_summary": True,
        "scoreable_unscoreable_cost_partition_required": True,
        "serialized_trade_ledger_is_physical_summary_authority": True,
    }


def stress_summary(returns: list[float]) -> dict[str, Any]:
    if not returns:
        return {
            "trade_count": 0,
            "raw_net_r": 0.0,
            "guarded_stress_rows": [],
        }
    rows = []
    for extra_cost in (0.05, 0.10, 0.20):
        stressed = [value - extra_cost for value in returns]
        rows.append(
            {
                "stress_id": f"extra_cost_{extra_cost:.2f}r_per_trade",
                "net_r": round(sum(stressed), 8),
                "min_trade_r": round(min(stressed), 8),
                "loss_count": len([value for value in stressed if value < 0]),
            }
        )
    return {
        "trade_count": len(returns),
        "raw_net_r": round(sum(returns), 8),
        "guarded_stress_rows": rows,
    }


def max_drawdown(sequence: list[float]) -> float:
    equity = 0.0
    peak = 0.0
    drawdown = 0.0
    for value in sequence:
        equity += value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity - peak)
    return round(drawdown, 8)


def monte_carlo_summary(returns: list[float], *, iterations: int = 200) -> dict[str, Any]:
    if not returns:
        return {"iterations": iterations, "trade_count": 0, "max_drawdown_r_p05": None}
    drawdowns: list[float] = []
    for index in range(iterations):
        shuffled = list(returns)
        random.Random(99173 + index).shuffle(shuffled)
        drawdowns.append(max_drawdown(shuffled))
    drawdowns.sort()
    p05_index = max(0, min(len(drawdowns) - 1, int(len(drawdowns) * 0.05)))
    p50_index = max(0, min(len(drawdowns) - 1, int(len(drawdowns) * 0.50)))
    return {
        "iterations": iterations,
        "trade_count": len(returns),
        "total_net_r": round(sum(returns), 8),
        "max_drawdown_r_p05": drawdowns[p05_index],
        "max_drawdown_r_p50": drawdowns[p50_index],
        "max_drawdown_r_worst": min(drawdowns),
        "deterministic_seed_base": 99173,
    }


def comparison_rows(stats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["profile"], row["split"]): row for row in stats}
    rows: list[dict[str, Any]] = []
    for split, _start, _end in SPLIT_RANGES:
        for package_profile, baseline_profile, comparison_id in (
            (PROFILE_GUARDED, PROFILE_RAW, "guarded_vs_raw"),
            (PROFILE_REPAIRED, PROFILE_RAW, "repaired_vs_raw"),
            (PROFILE_REPAIRED, PROFILE_GUARDED, "repaired_vs_guarded"),
        ):
            package = by_key.get((package_profile, split))
            baseline = by_key.get((baseline_profile, split))
            if package is None or baseline is None:
                continue
            row = {
                "row_type": "package_vs_baseline_profile_delta",
                "comparison_id": comparison_id,
                "split": split,
                "package_profile": package_profile,
                "baseline_profile": baseline_profile,
                "package_net_r": package["net_r"],
                "baseline_net_r": baseline["net_r"],
                "delta_net_r": round(package["net_r"] - baseline["net_r"], 8),
                "package_all_executed_net_r": package.get("all_executed_net_r"),
                "baseline_all_executed_net_r": baseline.get("all_executed_net_r"),
                "delta_all_executed_net_r": round(
                    safe_float(package.get("all_executed_net_r"))
                    - safe_float(baseline.get("all_executed_net_r")),
                    8,
                ),
                "package_headline_filled_trades": package.get(
                    "headline_filled_trade_count"
                ),
                "baseline_headline_filled_trades": baseline.get(
                    "headline_filled_trade_count"
                ),
                "package_strict_full_package_net_r": package.get(
                    "strict_full_package_net_r"
                ),
                "baseline_strict_full_package_net_r": baseline.get(
                    "strict_full_package_net_r"
                ),
                "delta_strict_full_package_net_r": round(
                    safe_float(package.get("strict_full_package_net_r"))
                    - safe_float(baseline.get("strict_full_package_net_r")),
                    8,
                ),
                "package_strict_full_package_filled_trades": package.get(
                    "strict_full_package_filled_trade_count"
                ),
                "baseline_strict_full_package_filled_trades": baseline.get(
                    "strict_full_package_filled_trade_count"
                ),
                "package_diagnostic_only_trade_rows": package.get(
                    "diagnostic_only_trade_rows"
                ),
                "baseline_diagnostic_only_trade_rows": baseline.get(
                    "diagnostic_only_trade_rows"
                ),
                "package_source_required_lifecycle_gap_net_r": package.get(
                    "source_required_lifecycle_gap_net_r"
                ),
                "baseline_source_required_lifecycle_gap_net_r": baseline.get(
                    "source_required_lifecycle_gap_net_r"
                ),
                "package_filled_trades": package["filled_trade_count"],
                "baseline_filled_trades": baseline["filled_trade_count"],
                "delta_filled_trades": (
                    package["filled_trade_count"] - baseline["filled_trade_count"]
                ),
                "package_loss_count": package["loss_count"],
                "baseline_loss_count": baseline["loss_count"],
                "delta_loss_count": package["loss_count"] - baseline["loss_count"],
                "live_broker_authority": False,
                "final_selection_claim": False,
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
            if comparison_id == "guarded_vs_raw":
                row.update(
                    {
                        "guarded_net_r": package["net_r"],
                        "raw_net_r": baseline["net_r"],
                        "guarded_filled_trades": package["filled_trade_count"],
                        "raw_filled_trades": baseline["filled_trade_count"],
                        "guarded_loss_count": package["loss_count"],
                        "raw_loss_count": baseline["loss_count"],
                    }
                )
            rows.append(row)
    for profile in PROFILES:
        development = by_key.get((profile, "development"))
        holdout = by_key.get((profile, "holdout"))
        if development is None or holdout is None:
            continue
        rows.append(
            {
                "row_type": "in_sample_repair_vs_holdout_profile_delta",
                "profile": profile,
                "development_includes_repair_seed_window": True,
                "repair_seed_start": REPAIR_SEED_START,
                "repair_seed_end": REPAIR_SEED_END,
                "development_net_r": development["net_r"],
                "holdout_net_r": holdout["net_r"],
                "delta_holdout_minus_development_net_r": round(
                    holdout["net_r"] - development["net_r"], 8
                ),
                "development_filled_trades": development["filled_trade_count"],
                "holdout_filled_trades": holdout["filled_trade_count"],
                "live_broker_authority": False,
                "final_selection_claim": False,
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
        )
    return rows


def risk_finalizer_evidence(stats: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    total_scorecard_rows = 0
    total_finalizer_rows = 0
    total_reallocated = 0
    total_reallocation_candidates = 0
    total_reallocation_admitted = 0
    total_reallocation_policy_blocked = 0
    total_reallocation_quality_blocked = 0
    total_reallocation_selected = 0
    total_reallocation_terminal_probe_rows = 0
    total_reallocation_terminal_probe_missing_instance_keys = 0
    total_reallocation_terminal_dispositions: Counter[str] = Counter()
    total_reallocation_terminal_probe_reconciled = True
    total_zero_trade_conversion_candidates = 0
    total_zero_trade_conversion_policy_blocked = 0
    total_zero_trade_conversion_selected = 0
    repaired_rows = 0
    repaired_finalizer_rows = 0
    repaired_reallocated = 0
    repaired_reallocation_candidates = 0
    repaired_reallocation_selected = 0
    for stat in stats:
        status_counts = stat.get("risk_finalizer_status_counts")
        status_counts = status_counts if isinstance(status_counts, Mapping) else {}
        finalizer_rows = sum(int(value or 0) for value in status_counts.values())
        reallocated = int(stat.get("risk_finalizer_reallocated_true_rows") or 0)
        from_zero_trade = int(stat.get("risk_finalizer_from_zero_trade_rows") or 0)
        zero_trade_to_entry = int(
            stat.get("risk_finalizer_original_zero_trade_final_entry_rows") or 0
        )
        reallocation_candidates = int(
            stat.get("risk_finalizer_reallocation_candidate_probe_count") or 0
        )
        reallocation_admitted = int(
            stat.get("risk_finalizer_reallocation_admitted_candidate_probe_count") or 0
        )
        reallocation_policy_blocked = int(
            stat.get("risk_finalizer_reallocation_policy_blocked_probe_count") or 0
        )
        reallocation_quality_blocked = int(
            stat.get("risk_finalizer_reallocation_quality_blocked_probe_count") or 0
        )
        reallocation_selected = int(
            stat.get("risk_finalizer_reallocation_selected_probe_count") or 0
        )
        reallocation_terminal_probe_rows = int(
            stat.get(
                "risk_finalizer_reallocation_terminal_probe_row_count"
            )
            or 0
        )
        reallocation_terminal_probe_missing_instance_keys = int(
            stat.get(
                "risk_finalizer_reallocation_terminal_probe_missing_instance_key_count"
            )
            or 0
        )
        reallocation_terminal_dispositions = stat.get(
            "risk_finalizer_reallocation_terminal_disposition_counts"
        )
        reallocation_terminal_dispositions = (
            reallocation_terminal_dispositions
            if isinstance(reallocation_terminal_dispositions, Mapping)
            else {}
        )
        zero_trade_candidates = int(
            stat.get("risk_finalizer_zero_trade_conversion_candidate_probe_count") or 0
        )
        zero_trade_policy_blocked = int(
            stat.get(
                "risk_finalizer_zero_trade_conversion_policy_blocked_probe_count"
            )
            or 0
        )
        zero_trade_selected = int(
            stat.get("risk_finalizer_zero_trade_conversion_selected_probe_count") or 0
        )
        scorecard_rows = int(stat.get("scorecard_rows") or 0)
        total_scorecard_rows += scorecard_rows
        total_finalizer_rows += finalizer_rows
        total_reallocated += reallocated
        total_reallocation_candidates += reallocation_candidates
        total_reallocation_admitted += reallocation_admitted
        total_reallocation_policy_blocked += reallocation_policy_blocked
        total_reallocation_quality_blocked += reallocation_quality_blocked
        total_reallocation_selected += reallocation_selected
        total_reallocation_terminal_probe_rows += reallocation_terminal_probe_rows
        total_reallocation_terminal_probe_missing_instance_keys += (
            reallocation_terminal_probe_missing_instance_keys
        )
        total_reallocation_terminal_dispositions.update(
            {
                str(key): int(value or 0)
                for key, value in reallocation_terminal_dispositions.items()
            }
        )
        total_reallocation_terminal_probe_reconciled = bool(
            total_reallocation_terminal_probe_reconciled
            and stat.get(
                "risk_finalizer_reallocation_terminal_probe_reconciled"
            )
            is True
        )
        total_zero_trade_conversion_candidates += zero_trade_candidates
        total_zero_trade_conversion_policy_blocked += zero_trade_policy_blocked
        total_zero_trade_conversion_selected += zero_trade_selected
        profile = str(stat.get("profile") or "")
        if profile == PROFILE_REPAIRED:
            repaired_rows += scorecard_rows
            repaired_finalizer_rows += finalizer_rows
            repaired_reallocated += reallocated
            repaired_reallocation_candidates += reallocation_candidates
            repaired_reallocation_selected += reallocation_selected
        rows.append(
            {
                "profile": profile,
                "split": stat.get("split"),
                "scorecard_rows": scorecard_rows,
                "finalizer_rows": finalizer_rows,
                "reallocated_rows": reallocated,
                "reallocation_candidate_probe_count": reallocation_candidates,
                "reallocation_admitted_candidate_probe_count": reallocation_admitted,
                "reallocation_policy_blocked_probe_count": reallocation_policy_blocked,
                "reallocation_quality_blocked_probe_count": reallocation_quality_blocked,
                "reallocation_selected_probe_count": reallocation_selected,
                "reallocation_terminal_probe_row_count": (
                    reallocation_terminal_probe_rows
                ),
                "reallocation_terminal_probe_missing_instance_key_count": (
                    reallocation_terminal_probe_missing_instance_keys
                ),
                "reallocation_terminal_disposition_counts": dict(
                    reallocation_terminal_dispositions
                ),
                "reallocation_terminal_probe_reconciled": stat.get(
                    "risk_finalizer_reallocation_terminal_probe_reconciled"
                ),
                "from_zero_trade_rows": from_zero_trade,
                "original_zero_trade_final_entry_rows": zero_trade_to_entry,
                "zero_trade_conversion_candidate_probe_count": zero_trade_candidates,
                "zero_trade_conversion_policy_blocked_probe_count": (
                    zero_trade_policy_blocked
                ),
                "zero_trade_conversion_selected_probe_count": zero_trade_selected,
                "risk_finalizer_status_counts": dict(status_counts),
            }
        )
    return {
        "enabled_in_runtime_config": True,
        "scorecard_rows": total_scorecard_rows,
        "finalizer_rows": total_finalizer_rows,
        "reallocated_rows": total_reallocated,
        "reallocation_candidate_probe_count": total_reallocation_candidates,
        "reallocation_admitted_candidate_probe_count": total_reallocation_admitted,
        "reallocation_policy_blocked_probe_count": total_reallocation_policy_blocked,
        "reallocation_quality_blocked_probe_count": total_reallocation_quality_blocked,
        "reallocation_selected_probe_count": total_reallocation_selected,
        "reallocation_terminal_probe_row_count": (
            total_reallocation_terminal_probe_rows
        ),
        "reallocation_terminal_probe_missing_instance_key_count": (
            total_reallocation_terminal_probe_missing_instance_keys
        ),
        "reallocation_terminal_disposition_counts": dict(
            total_reallocation_terminal_dispositions
        ),
        "reallocation_terminal_probe_reconciled": bool(
            total_reallocation_terminal_probe_reconciled
            and total_reallocation_terminal_probe_rows
            == total_reallocation_candidates
            and total_reallocation_terminal_probe_missing_instance_keys == 0
        ),
        "zero_trade_conversion_candidate_probe_count": (
            total_zero_trade_conversion_candidates
        ),
        "zero_trade_conversion_policy_blocked_probe_count": (
            total_zero_trade_conversion_policy_blocked
        ),
        "zero_trade_conversion_selected_probe_count": (
            total_zero_trade_conversion_selected
        ),
        "repaired_profile_scorecard_rows": repaired_rows,
        "repaired_profile_finalizer_rows": repaired_finalizer_rows,
        "repaired_profile_reallocated_rows": repaired_reallocated,
        "repaired_profile_reallocation_candidate_probe_count": (
            repaired_reallocation_candidates
        ),
        "repaired_profile_reallocation_selected_probe_count": (
            repaired_reallocation_selected
        ),
        "repaired_profile_finalizer_evidenced": repaired_finalizer_rows > 0,
        "rows": rows,
    }


def profile_chunks(days_by_split: Mapping[str, tuple[str, ...]], chunk_size: int) -> Iterable[tuple[str, tuple[str, ...]]]:
    for split, days in days_by_split.items():
        for index in range(0, len(days), chunk_size):
            yield split, days[index : index + chunk_size]


def source_authority_chunk_invariance_contract(
    *,
    planned_chunk_count: int,
    completed_chunk_count: int,
    checkpoints: Sequence[Mapping[str, Any]],
    canonical_plans: Mapping[str, Mapping[str, Any]],
    current_chunk_pending: bool = False,
) -> dict[str, Any]:
    checkpoint_valid = bool(
        completed_chunk_count == len(checkpoints)
        and all(
            row.get("source_plan_valid") is True
            and row.get("source_plan_matches_canonical") is True
            and row.get("execution_days_subset_of_source_authority") is True
            and row.get("source_authority_scope_mode")
            == SOURCE_AUTHORITY_SCOPE_MODE
            for row in checkpoints
        )
    )
    canonical_plans_valid = bool(
        canonical_plans
        and all(
            plan.get("valid") is True
            and (
                plan.get("source_authority_scope")
                if isinstance(plan.get("source_authority_scope"), Mapping)
                else {}
            ).get("mode")
            == SOURCE_AUTHORITY_SCOPE_MODE
            and len(str(plan.get("plan_digest_sha256") or "")) == 64
            for plan in canonical_plans.values()
        )
    )
    complete = bool(
        checkpoint_valid
        and canonical_plans_valid
        and not current_chunk_pending
        and completed_chunk_count == planned_chunk_count
    )
    return {
        "schema": SOURCE_AUTHORITY_CHUNK_INVARIANCE_CONTRACT_SCHEMA,
        "status": (
            "complete_source_authority_chunk_invariance"
            if complete
            else (
                "source_authority_chunk_pending"
                if current_chunk_pending
                else "source_authority_chunk_invariance_incomplete"
            )
        ),
        "valid": complete,
        "source_authority_scope_mode": SOURCE_AUTHORITY_SCOPE_MODE,
        "planned_chunk_count": int(planned_chunk_count),
        "completed_chunk_count": int(completed_chunk_count),
        "checkpoint_count": len(checkpoints),
        "canonical_plan_count": len(canonical_plans),
        "current_chunk_pending": current_chunk_pending,
        "all_execution_days_inside_authority_scope": all(
            row.get("execution_days_subset_of_source_authority") is True
            for row in checkpoints
        ),
        "all_source_plans_valid": all(
            row.get("source_plan_valid") is True for row in checkpoints
        ),
        "all_chunk_source_plans_match_canonical": all(
            row.get("source_plan_matches_canonical") is True
            for row in checkpoints
        ),
        "canonical_plans": {
            key: dict(value) for key, value in sorted(canonical_plans.items())
        },
        "checkpoints": [dict(row) for row in checkpoints],
    }


def capacity_safe_chunk_execution_contract(
    *,
    configured_chunk_size: int,
    planned_chunk_count: int,
    completed_chunk_count: int,
    gc_between_chunks: bool,
    checkpoints: Sequence[Mapping[str, Any]],
    current_chunk_cleanup_pending: bool = False,
) -> dict[str, Any]:
    explicit_gc_requirement_satisfied = bool(
        gc_between_chunks or planned_chunk_count <= 1
    )
    cleanup_complete = bool(
        completed_chunk_count == len(checkpoints)
        and all(
            row.get("cleanup_status") == "completed"
            and row.get("broker_object_continuity") is True
            and row.get("account_object_continuity") is True
            and row.get("selected_order_sequence_monotonic") is True
            and int(
                (
                    row.get("source_cache_release")
                    if isinstance(row.get("source_cache_release"), Mapping)
                    else {}
                ).get("completed_chunk_day_scoped_entries_remaining")
                or 0
            )
            == 0
            and int(
                (
                    row.get("source_cache_release")
                    if isinstance(row.get("source_cache_release"), Mapping)
                    else {}
                ).get("completed_source_authority_scoped_entries_remaining")
                or 0
            )
            == 0
            and (
                row.get("source_cache_release")
                if isinstance(row.get("source_cache_release"), Mapping)
                else {}
            ).get("completed_replay_source_caches_released")
            is True
            and int(
                (
                    row.get("source_cache_release")
                    if isinstance(row.get("source_cache_release"), Mapping)
                    else {}
                ).get("completed_replay_source_cache_entries_remaining")
                or 0
            )
            == 0
            and (
                row.get("explicit_gc_completed") is True
                if gc_between_chunks
                else row.get("explicit_gc_completed") is False
            )
            for row in checkpoints
        )
    )
    complete = bool(
        cleanup_complete
        and explicit_gc_requirement_satisfied
        and not current_chunk_cleanup_pending
        and completed_chunk_count == planned_chunk_count
    )
    return {
        "schema": CAPACITY_SAFE_CHUNK_EXECUTION_CONTRACT_SCHEMA,
        "status": (
            "complete_capacity_safe_chunk_execution"
            if complete
            else (
                "chunk_ledgers_flushed_cleanup_pending"
                if current_chunk_cleanup_pending
                else "capacity_safe_chunk_execution_in_progress"
            )
        ),
        "valid": complete,
        "configured_chunk_size": int(configured_chunk_size),
        "planned_chunk_count": int(planned_chunk_count),
        "completed_chunk_count": int(completed_chunk_count),
        "cleanup_checkpoint_count": len(checkpoints),
        "current_chunk_cleanup_pending": current_chunk_cleanup_pending,
        "same_simulated_broker_reused_across_chunks": all(
            row.get("broker_object_continuity") is True for row in checkpoints
        ),
        "same_account_state_reused_across_chunks": all(
            row.get("account_object_continuity") is True for row in checkpoints
        ),
        "selected_order_sequence_monotonic_across_chunks": all(
            row.get("selected_order_sequence_monotonic") is True
            for row in checkpoints
        ),
        "completed_chunk_day_scoped_source_caches_released": all(
            int(
                (
                    row.get("source_cache_release")
                    if isinstance(row.get("source_cache_release"), Mapping)
                    else {}
                ).get("completed_chunk_day_scoped_entries_remaining")
                or 0
            )
            == 0
            for row in checkpoints
        ),
        "completed_source_authority_scoped_caches_released": all(
            int(
                (
                    row.get("source_cache_release")
                    if isinstance(row.get("source_cache_release"), Mapping)
                    else {}
                ).get("completed_source_authority_scoped_entries_remaining")
                or 0
            )
            == 0
            for row in checkpoints
        ),
        "completed_replay_source_caches_released": all(
            (
                row.get("source_cache_release")
                if isinstance(row.get("source_cache_release"), Mapping)
                else {}
            ).get("completed_replay_source_caches_released")
            is True
            and int(
                (
                    row.get("source_cache_release")
                    if isinstance(row.get("source_cache_release"), Mapping)
                    else {}
                ).get("completed_replay_source_cache_entries_remaining")
                or 0
            )
            == 0
            for row in checkpoints
        ),
        "explicit_gc_after_result_release_enabled": gc_between_chunks,
        "explicit_gc_requirement_satisfied": (
            explicit_gc_requirement_satisfied
        ),
        "automatic_gc_disabled_during_replay_chunks": True,
        "automatic_gc_reenabled_between_chunks": False,
        "caller_automatic_gc_state_restored_after_harness": True,
        "cleanup_complete_for_all_completed_chunks": cleanup_complete,
        "checkpoints": [dict(row) for row in checkpoints],
    }


def build_days_by_split(start: str, end: str, *, max_days: int | None) -> dict[str, tuple[str, ...]]:
    out: dict[str, list[str]] = {split: [] for split, _start, _end in SPLIT_RANGES}
    for day in iter_dates(start, end):
        split = split_for_day(day)
        if split is None:
            continue
        out[split].append(day)
    if max_days is not None:
        remaining = max_days
        limited: dict[str, tuple[str, ...]] = {}
        for split, days in out.items():
            selected = days[: max(0, remaining)]
            limited[split] = tuple(selected)
            remaining -= len(selected)
            if remaining <= 0:
                for rest_split in out:
                    limited.setdefault(rest_split, ())
                break
        return limited
    return {split: tuple(days) for split, days in out.items()}


def _resolved_argument_path(value: Any) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def _lexical_argument_path(value: Any) -> Path:
    path = Path(value)
    anchored = path if path.is_absolute() else ROOT / path
    return Path(os.path.abspath(os.fspath(anchored)))


def _path_has_symlink_component(path: Path) -> bool:
    lexical = _lexical_argument_path(path)
    current = Path(lexical.anchor)
    for component in lexical.parts[1:]:
        current /= component
        if current.is_symlink():
            return True
    return False


def _require_path_within(value: Any, root: Path, *, code: str) -> Path:
    path = _resolved_argument_path(value)
    try:
        path.relative_to(root.resolve())
    except ValueError:
        raise ValueError(code) from None
    return path


def _read_json_mapping_nofollow(
    path: Path,
    *,
    code: str,
) -> tuple[bytes, dict[str, Any]]:
    try:
        raw, _identity = read_regular_nofollow(path, code=code)
        payload = json.loads(raw)
    except (
        ImmutableEvidenceError,
        UnicodeError,
        json.JSONDecodeError,
    ):
        raise ValueError(code) from None
    if type(payload) is not dict:
        raise ValueError(code)
    return raw, payload


def source_bundle_consumer_rebind_authority_from_args(
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Bind the reviewed byte-exact source-bundle successor fail closed."""

    required = {
        "authority_path": getattr(
            args,
            "source_bundle_consumer_rebind_authority",
            None,
        ),
        "authority_sha256": getattr(
            args,
            "expected_source_bundle_consumer_rebind_authority_sha256",
            None,
        ),
        "authority_root_sha256": getattr(
            args,
            "expected_source_bundle_consumer_rebind_authority_root_sha256",
            None,
        ),
        "bundle_dir": getattr(args, "source_acceleration_bundle_dir", None),
        "selection_path": getattr(
            args,
            "source_acceleration_selection",
            None,
        ),
        "expected_bundle_root_sha256": getattr(
            args,
            "expected_source_bundle_root_sha256",
            None,
        ),
        "expected_source_plan_digest_sha256": getattr(
            args,
            "expected_source_plan_digest_sha256",
            None,
        ),
    }
    if any(value is None or not str(value).strip() for value in required.values()):
        raise ValueError("attempt5_source_rebind_authority_args_incomplete")
    if (
        str(required["authority_sha256"])
        != ATTEMPT5_SOURCE_REBIND_AUTHORITY_SHA256
        or str(required["authority_root_sha256"])
        != ATTEMPT5_SOURCE_REBIND_AUTHORITY_ROOT_SHA256
        or str(required["expected_bundle_root_sha256"])
        != ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256
    ):
        raise ValueError("attempt5_source_rebind_authority_identity_mismatch")

    authority_path = _lexical_argument_path(required["authority_path"])
    bundle_dir = _lexical_argument_path(required["bundle_dir"])
    selection_path = _lexical_argument_path(required["selection_path"])
    bundle_path = bundle_dir / "bundle.json"
    seal_path = bundle_dir / "SEALED"
    if any(
        _path_has_symlink_component(path)
        for path in (
            authority_path,
            bundle_dir,
            bundle_path,
            seal_path,
            selection_path,
        )
    ):
        raise ValueError("attempt5_source_rebind_authority_symlink_forbidden")

    authority_raw, authority = _read_json_mapping_nofollow(
        authority_path,
        code="attempt5_source_rebind_authority_invalid",
    )
    bundle_raw, bundle = _read_json_mapping_nofollow(
        bundle_path,
        code="attempt5_source_rebind_bundle_invalid",
    )
    selection_raw, selection = _read_json_mapping_nofollow(
        selection_path,
        code="attempt5_source_rebind_selection_invalid",
    )
    try:
        seal_raw, _seal_identity = read_regular_nofollow(
            seal_path,
            code="attempt5_source_rebind_bundle_invalid",
        )
    except ImmutableEvidenceError:
        raise ValueError("attempt5_source_rebind_bundle_invalid") from None

    authority_projection = dict(authority)
    authority_root = authority_projection.pop("authority_root_sha256", None)
    bundle_projection = dict(bundle)
    bundle_root = bundle_projection.pop("bundle_root_sha256", None)
    selection_projection = dict(selection)
    selection_root = selection_projection.pop("selection_root_sha256", None)
    authority_file_sha256 = hashlib.sha256(authority_raw).hexdigest()
    bundle_file_sha256 = hashlib.sha256(bundle_raw).hexdigest()
    selection_file_sha256 = hashlib.sha256(selection_raw).hexdigest()
    current_implementation_root = accepted_source_implementation_root()
    successor_bundle = authority.get("successor_bundle")
    successor_selection = authority.get("successor_selection")
    predecessor_bundle = authority.get("predecessor_bundle")
    selection_transformation = authority.get("selection_transformation")
    expected_authority_keys = {
        "authority_root_sha256",
        "broker_live_authority",
        "bundle_transformation",
        "continuation_authorized",
        "economic_values_exposed",
        "fresh_cold_runs",
        "independent_verifiers",
        "policy_execution_entered",
        "predecessor_bundle",
        "predecessor_selection",
        "reason",
        "schema",
        "selection_transformation",
        "status",
        "successor_bundle",
        "successor_selection",
    }
    if (
        set(authority) != expected_authority_keys
        or authority.get("schema") != SOURCE_REBIND_AUTHORITY_SCHEMA
        or authority.get("status")
        != "ACCEPTED_SOURCE_BYTES_IDENTICAL_IMPLEMENTATION_SUCCESSOR"
        or authority.get("continuation_authorized") is not False
        or authority.get("policy_execution_entered") is not False
        or authority.get("economic_values_exposed") is not False
        or authority.get("broker_live_authority") is not False
        or authority_file_sha256 != str(required["authority_sha256"])
        or authority_root != str(required["authority_root_sha256"])
        or authority_root != stable_sha256(authority_projection)
        or type(successor_bundle) is not dict
        or type(successor_selection) is not dict
        or type(predecessor_bundle) is not dict
        or type(selection_transformation) is not dict
    ):
        raise ValueError("attempt5_source_rebind_authority_invalid")
    if (
        bundle.get("schema")
        != "gtos.replay_acceleration.persisted_source_bundle.v1"
        or selection.get("schema")
        != "gtos.replay_acceleration.slice_selection.v1"
        or bundle_root != stable_sha256(bundle_projection)
        or selection_root != stable_sha256(selection_projection)
        or seal_raw != str(bundle_root or "").encode("ascii") + b"\n"
        or bundle_file_sha256 != ATTEMPT5_SOURCE_BUNDLE_FILE_SHA256
        or selection_file_sha256 != ATTEMPT5_SOURCE_SELECTION_SHA256
        or bundle_root != ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256
        or selection_root != ATTEMPT5_SOURCE_SELECTION_ROOT_SHA256
        or bundle.get("selection_root_sha256") != selection_root
        or bundle.get("accepted_cache_implementation_root")
        != ATTEMPT5_SOURCE_IMPLEMENTATION_ROOT_SHA256
        or current_implementation_root
        != ATTEMPT5_SOURCE_IMPLEMENTATION_ROOT_SHA256
        or bundle.get("expected_source_plan_digest_sha256")
        != str(required["expected_source_plan_digest_sha256"])
        or selection.get("expected_source_plan_digest_sha256")
        != str(required["expected_source_plan_digest_sha256"])
    ):
        raise ValueError("attempt5_source_rebind_successor_artifact_mismatch")
    if (
        lexical_path(Path(str(successor_bundle.get("path") or "")))
        != bundle_path
        or successor_bundle.get("sha256") != bundle_file_sha256
        or successor_bundle.get("bundle_root_sha256") != bundle_root
        or successor_bundle.get("implementation_root_sha256")
        != current_implementation_root
        or lexical_path(Path(str(successor_selection.get("path") or "")))
        != selection_path
        or successor_selection.get("sha256") != selection_file_sha256
        or successor_selection.get("selection_root_sha256") != selection_root
        or predecessor_bundle.get("bundle_root_sha256")
        != ATTEMPT5_PREDECESSOR_SOURCE_BUNDLE_ROOT_SHA256
        or selection_transformation.get("source_plan_digest_sha256")
        != str(required["expected_source_plan_digest_sha256"])
    ):
        raise ValueError("attempt5_source_rebind_authority_successor_mismatch")

    binding_core = {
        "schema": BOUND_SOURCE_REBIND_AUTHORITY_SCHEMA,
        "authority_path": str(authority_path),
        "authority_file_sha256": authority_file_sha256,
        "authority_root_sha256": authority_root,
        "authority": copy.deepcopy(authority),
        "verified_successor_bundle": {
            "path": str(bundle_path),
            "file_sha256": bundle_file_sha256,
            "bundle_root_sha256": bundle_root,
            "implementation_root_sha256": current_implementation_root,
        },
        "verified_successor_selection": {
            "path": str(selection_path),
            "file_sha256": selection_file_sha256,
            "selection_root_sha256": selection_root,
        },
        "source_plan_digest_sha256": str(
            required["expected_source_plan_digest_sha256"]
        ),
        "policy_execution_entered": False,
        "continuation_authorized": False,
        "broker_live_authority": False,
        "economic_values_exposed": False,
    }
    return {
        **binding_core,
        "binding_root_sha256": stable_sha256(binding_core),
    }


def prospective_golden_authority_from_args(
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Validate the immutable golden, amendment, and fixed-verifier identity."""

    required_values = {
        "golden_manifest": getattr(args, "golden_manifest", None),
        "expected_golden_manifest_sha256": getattr(
            args,
            "expected_golden_manifest_sha256",
            None,
        ),
        "expected_golden_manifest_self_root_sha256": getattr(
            args,
            "expected_golden_manifest_self_root_sha256",
            None,
        ),
        "expected_golden_root_sha256": getattr(
            args,
            "expected_golden_root_sha256",
            None,
        ),
        "expected_opaque_result_surface_root_sha256": getattr(
            args,
            "expected_opaque_result_surface_root_sha256",
            None,
        ),
        "golden_amendment": getattr(args, "golden_amendment", None),
        "expected_golden_amendment_sha256": getattr(
            args,
            "expected_golden_amendment_sha256",
            None,
        ),
        "expected_golden_amendment_self_root_sha256": getattr(
            args,
            "expected_golden_amendment_self_root_sha256",
            None,
        ),
        "expected_fixed_parity_verifier_sha256": getattr(
            args,
            "expected_fixed_parity_verifier_sha256",
            None,
        ),
    }
    successor_values = {
        "golden_successor_authority": getattr(
            args, "golden_successor_authority", None
        ),
        "expected_golden_successor_authority_sha256": getattr(
            args,
            "expected_golden_successor_authority_sha256",
            None,
        ),
        "expected_golden_successor_authority_root_sha256": getattr(
            args,
            "expected_golden_successor_authority_root_sha256",
            None,
        ),
        "expected_golden_successor_authority_verification_root_sha256": getattr(
            args,
            "expected_golden_successor_authority_verification_root_sha256",
            None,
        ),
        "expected_economic_execution_contract_sha256": getattr(
            args,
            "expected_economic_execution_contract_sha256",
            None,
        ),
        "expected_fixed_verifier_code_authority_root_sha256": getattr(
            args,
            "expected_fixed_verifier_code_authority_root_sha256",
            None,
        ),
    }
    successor_requested = any(
        value is not None and str(value).strip()
        for value in successor_values.values()
    )
    if any(
        value is None or not str(value).strip()
        for value in required_values.values()
    ):
        raise ValueError(
            "attempt5_prospective_golden_authority_args_incomplete"
        )
    if successor_requested and any(
        value is None or not str(value).strip()
        for value in successor_values.values()
    ):
        raise ValueError(
            "attempt5_successor_golden_authority_args_incomplete"
        )
    manifest_path = _lexical_argument_path(required_values["golden_manifest"])
    amendment_path = _lexical_argument_path(required_values["golden_amendment"])
    verifier_path = _lexical_argument_path(
        Path(__file__).with_name(
            "replay_acceleration_real_parity_verifier.py"
        )
    )
    if any(
        _path_has_symlink_component(path)
        for path in (manifest_path, amendment_path, verifier_path)
    ):
        raise ValueError(
            "attempt5_prospective_golden_authority_symlink_forbidden"
        )
    authority = {
        "golden_manifest_path": str(manifest_path),
        "golden_manifest_file_sha256": str(
            required_values["expected_golden_manifest_sha256"]
        ).strip(),
        "golden_manifest_self_root_sha256": str(
            required_values[
                "expected_golden_manifest_self_root_sha256"
            ]
        ).strip(),
        "golden_root_sha256": str(
            required_values["expected_golden_root_sha256"]
        ).strip(),
        "opaque_result_surface_root_sha256": str(
            required_values[
                "expected_opaque_result_surface_root_sha256"
            ]
        ).strip(),
        "golden_amendment_path": str(amendment_path),
        "golden_amendment_file_sha256": str(
            required_values["expected_golden_amendment_sha256"]
        ).strip(),
        "golden_amendment_self_root_sha256": str(
            required_values[
                "expected_golden_amendment_self_root_sha256"
            ]
        ).strip(),
        "fixed_verifier_module": FIXED_VERIFIER_MODULE,
        "fixed_verifier_path": str(verifier_path),
        "fixed_verifier_file_sha256": str(
            required_values["expected_fixed_parity_verifier_sha256"]
        ).strip(),
    }
    if successor_requested:
        successor_path = _lexical_argument_path(
            successor_values["golden_successor_authority"]
        )
        if _path_has_symlink_component(successor_path):
            raise ValueError(
                "attempt5_prospective_golden_authority_symlink_forbidden"
            )
        fixed_code_authority, _identities = (
            build_fixed_verifier_code_authority(Path(__file__).parent)
        )
        authority.update(
            {
                "successor_authority_path": str(successor_path),
                "successor_authority_file_sha256": str(
                    successor_values[
                        "expected_golden_successor_authority_sha256"
                    ]
                ).strip(),
                "successor_authority_root_sha256": str(
                    successor_values[
                        "expected_golden_successor_authority_root_sha256"
                    ]
                ).strip(),
                "successor_authority_verification_root_sha256": str(
                    successor_values[
                        "expected_golden_successor_authority_verification_root_sha256"
                    ]
                ).strip(),
                "economic_execution_contract_digest_sha256": str(
                    successor_values[
                        "expected_economic_execution_contract_sha256"
                    ]
                ).strip(),
                "fixed_verifier_code_authority": fixed_code_authority,
                "fixed_verifier_code_authority_root_sha256": str(
                    successor_values[
                        "expected_fixed_verifier_code_authority_root_sha256"
                    ]
                ).strip(),
            }
        )
    try:
        return validate_prospective_golden_authority(authority)
    except GateRejected as exc:
        raise ValueError(
            "attempt5_prospective_golden_authority_invalid:"
            f"{exc.code}"
        ) from None


def require_attempt5_execution_authority(args: argparse.Namespace) -> None:
    """Reject every route except the fresh S0R0 Jan 1-7 parity run."""

    required_true = {
        "omit_candidate_ledger": args.omit_candidate_ledger,
        "omit_candidate_index_ledger": args.omit_candidate_index_ledger,
        "omit_packet_sidecar_ledger": args.omit_packet_sidecar_ledger,
        "compact_missed_ledger": args.compact_missed_ledger,
        "compact_decision_ledger": args.compact_decision_ledger,
        "compact_scorecard_ledger": args.compact_scorecard_ledger,
        "gc_between_chunks": args.gc_between_chunks,
        "stop_after_parity_gate": args.stop_after_parity_gate,
    }
    if not all(value is True for value in required_true.values()):
        raise ValueError("attempt5_required_compact_or_stop_authority_missing")
    if any(
        (
            args.finalize_existing_prefix,
            args.max_days is not None,
            args.smoke_subset,
            args.symbols is not None,
            args.skip_tick_source,
            args.use_native_h1,
            int(args.max_candidates_per_symbol_window) != 0,
        )
    ):
        raise ValueError("attempt5_legacy_or_bounded_route_option_forbidden")
    if (
        str(args.start) != ATTEMPT5_START_DAY
        or str(args.end) != ATTEMPT5_CONTRACT_END_DAY
        or int(args.chunk_size) != 1
        or str(args.output_prefix) != ATTEMPT5_OUTPUT_PREFIX
        or list(args.profiles) != [PROFILE_REPAIRED]
        or str(args.parity_gate_after_day) != ATTEMPT5_PARITY_DAY
        or str(args.arm_id) != "S0R0"
        or int(args.source_prewarm_workers) != 4
        or int(args.max_streaming_proof_archive_bytes) != 1024 * 1024 * 1024
    ):
        raise ValueError("attempt5_sealed_scope_or_identity_mismatch")
    expected_roots = {
        "expected_source_bundle_root_sha256": (
            ATTEMPT5_SOURCE_BUNDLE_ROOT_SHA256
        ),
        "expected_source_plan_digest_sha256": (
            "85663876fababc9b69c1bd7041c2bd043b286b456c2e635b2a6fc2289192d4e5"
        ),
        "expected_arm_fingerprint_sha256": (
            "2ece240b5fc9434a7ec20919e95cdf549bcd46f1c0311f130458fd4804c6d447"
        ),
    }
    for field, expected in expected_roots.items():
        if str(getattr(args, field, None) or "") != expected:
            raise ValueError(f"attempt5_{field}_mismatch")
    args.bound_source_bundle_consumer_rebind_authority = (
        source_bundle_consumer_rebind_authority_from_args(args)
    )
    shared_digest = str(args.expected_shared_execution_contract_sha256 or "")
    if len(shared_digest) != 64:
        raise ValueError("attempt5_shared_execution_contract_digest_missing")
    if (
        _resolved_argument_path(args.runtime_evidence_root)
        != ATTEMPT5_RUNTIME_EVIDENCE_ROOT
    ):
        raise ValueError("attempt5_runtime_evidence_root_mismatch")
    if (
        _resolved_argument_path(args.tick_source_manifest)
        != ATTEMPT5_TICK_SOURCE_MANIFEST
        or str(args.expected_tick_source_manifest_sha256 or "")
        != ATTEMPT5_TICK_SOURCE_MANIFEST_SHA256
    ):
        raise ValueError("attempt5_tick_source_manifest_authority_mismatch")
    requested_tick_sparse_cache_root = Path(args.tick_sparse_cache_root)
    if (
        requested_tick_sparse_cache_root.resolve()
        != ATTEMPT5_TICK_SPARSE_CACHE_ROOT.resolve()
        or requested_tick_sparse_cache_root.is_symlink()
    ):
        raise ValueError("attempt5_tick_sparse_cache_root_mismatch")
    requested_diagnostic_paths = tuple(
        _resolved_argument_path(path)
        for path in (args.tick_diagnostic_manifests or ())
    )
    requested_diagnostic_hashes = tuple(
        str(value)
        for value in (
            args.expected_tick_diagnostic_manifest_sha256s or ()
        )
    )
    if len(requested_diagnostic_paths) != len(requested_diagnostic_hashes):
        raise ValueError("attempt5_tick_diagnostic_manifest_pairing_mismatch")
    requested_diagnostic_bindings = tuple(
        zip(requested_diagnostic_paths, requested_diagnostic_hashes)
    )
    if requested_diagnostic_bindings != ATTEMPT5_TICK_DIAGNOSTIC_MANIFEST_BINDINGS:
        raise ValueError(
            "attempt5_tick_diagnostic_manifest_authority_mismatch"
        )
    prospective_golden_authority = prospective_golden_authority_from_args(args)
    if "successor_authority_path" not in prospective_golden_authority:
        raise ValueError("attempt5_successor_golden_authority_required")
    if (
        str(args.expected_economic_execution_contract_sha256 or "")
        != prospective_golden_authority[
            "economic_execution_contract_digest_sha256"
        ]
    ):
        raise ValueError("attempt5_economic_execution_contract_mismatch")
    args.prospective_golden_authority = prospective_golden_authority
    if shutil.which("zstd") is None:
        raise ValueError("attempt5_zstd_unavailable")

    namespace = _require_path_within(
        args.output_dir,
        ATTEMPT5_NAMESPACE_ROOT,
        code="attempt5_output_namespace_outside_sealed_root",
    )
    if namespace == ATTEMPT5_NAMESPACE_ROOT.resolve():
        raise ValueError("attempt5_output_namespace_identity_missing")
    if namespace.exists() or namespace.is_symlink():
        raise ValueError("attempt5_output_namespace_must_be_new")
    selected_namespace_paths: dict[str, Path] = {}
    for field in (
        "source_acceleration_cache_root",
        "streaming_proof_archive_root",
        "parity_gate_request",
        "parity_report",
        "parity_receipt",
    ):
        path = _require_path_within(
            getattr(args, field),
            namespace,
            code=f"attempt5_{field}_outside_identity_namespace",
        )
        if path.exists() or path.is_symlink():
            raise ValueError(f"attempt5_{field}_must_be_new")
        selected_namespace_paths[field] = path
    reserved_paths = {
        **selected_namespace_paths,
        "source_bundle_consumer_rebind_authority": _lexical_argument_path(
            args.source_bundle_consumer_rebind_authority
        ),
        "source_acceleration_bundle_manifest": (
            _lexical_argument_path(args.source_acceleration_bundle_dir)
            / "bundle.json"
        ),
        "source_acceleration_bundle_seal": (
            _lexical_argument_path(args.source_acceleration_bundle_dir)
            / "SEALED"
        ),
        "source_acceleration_selection": _lexical_argument_path(
            args.source_acceleration_selection
        ),
        "golden_manifest": Path(
            prospective_golden_authority["golden_manifest_path"]
        ),
        "golden_amendment": Path(
            prospective_golden_authority["golden_amendment_path"]
        ),
        "fixed_parity_verifier": Path(
            prospective_golden_authority["fixed_verifier_path"]
        ),
        "partial_summary_snapshot": selected_namespace_paths[
            "parity_gate_request"
        ].with_name("ACCELERATED_COMPARED_PARTIAL_SUMMARY.json"),
        "execution_identity": (
            namespace / "ATTEMPT5_TYPED_SPARSE_EXECUTION_IDENTITY.json"
        ).resolve(),
        **{
            f"replay_output:{name}": (namespace / path.name).resolve()
            for name, path in output_paths(str(args.output_prefix)).items()
        },
    }
    if "successor_authority_path" in prospective_golden_authority:
        reserved_paths["golden_successor_authority"] = Path(
            prospective_golden_authority["successor_authority_path"]
        )
    fixed_code_authority = prospective_golden_authority.get(
        "fixed_verifier_code_authority"
    )
    if isinstance(fixed_code_authority, Mapping):
        for index, row in enumerate(fixed_code_authority.get("files") or ()):
            if isinstance(row, Mapping) and isinstance(row.get("path"), str):
                dependency_path = Path(row["path"])
                if dependency_path != reserved_paths["fixed_parity_verifier"]:
                    reserved_paths[
                        f"fixed_verifier_dependency:{index}"
                    ] = dependency_path
    reserved_items = list(reserved_paths.items())
    for index, (left_name, left_path) in enumerate(reserved_items):
        for right_name, right_path in reserved_items[index + 1 :]:
            if (
                left_path == right_path
                or left_path in right_path.parents
                or right_path in left_path.parents
            ):
                raise ValueError(
                    "attempt5_evidence_path_collision:"
                    f"{left_name}:{right_name}"
                )

    required_inputs = (
        args.source_acceleration_bundle_dir,
        args.source_acceleration_selection,
        args.source_bundle_consumer_rebind_authority,
        args.expected_source_bundle_consumer_rebind_authority_sha256,
        args.expected_source_bundle_consumer_rebind_authority_root_sha256,
        args.decision_contract,
        args.tick_source_manifest,
        *(args.tick_diagnostic_manifests or ()),
    )
    if any(value is None for value in required_inputs):
        raise ValueError("attempt5_sealed_input_missing")
    bundle = _lexical_argument_path(args.source_acceleration_bundle_dir)
    if (
        not bundle.is_dir()
        or _path_has_symlink_component(bundle)
    ):
        raise ValueError("attempt5_source_acceleration_bundle_invalid")
    for value in (
        args.source_acceleration_selection,
        args.decision_contract,
    ):
        path = _lexical_argument_path(value)
        if not path.is_file() or _path_has_symlink_component(path):
            raise ValueError("attempt5_sealed_input_invalid")


def expected_prepared_day_pack_roots_from_args(
    args: argparse.Namespace,
) -> dict[tuple[str, str, str], str]:
    """Parse immutable per-chunk pack roots before any reducer can consume."""

    raw = getattr(args, "expected_prepared_day_pack_roots", None)
    if raw is None:
        return {}
    items = raw.items() if isinstance(raw, Mapping) else (
        str(value).split("=", 1) for value in raw
    )
    parsed: dict[tuple[str, str, str], str] = {}
    try:
        for raw_key, raw_root in items:
            if isinstance(raw_key, tuple):
                key = tuple(str(part) for part in raw_key)
            else:
                key = tuple(str(raw_key).split(":"))
            root = str(raw_root)
            if (
                len(key) != 3
                or any(not part for part in key)
                or not timewarp_loop.is_sha256(root)
                or key in parsed
            ):
                raise ValueError
            parsed[(key[0], key[1], key[2])] = root
    except (TypeError, ValueError):
        raise ValueError("expected_prepared_day_pack_roots_invalid") from None
    return parsed


def _seal_compact_event_sink_after_economic_hot_path(
    *,
    result: dict[str, Any],
    compact_event_sink: ReplayCompactEventSink,
) -> None:
    """Seal deferred proof output fail-closed after the economic timer stops."""

    try:
        authority = compact_event_sink.seal()
    except BaseException:
        compact_event_sink.abort()
        raise
    result["compact_event_sink_authority"] = authority


def _run_typed_sparse_attempt5(args: argparse.Namespace) -> dict[str, Any]:
    output_prefix = str(args.output_prefix or PREFIX).strip() or PREFIX
    attempt5_execution_identity = getattr(
        args,
        "attempt5_execution_identity",
        None,
    )
    runtime_evidence_contract = None
    runtime_evidence_root = getattr(args, "runtime_evidence_root", None)
    if runtime_evidence_root is not None:
        runtime_evidence_contract = configure_runtime_evidence_root(
            Path(runtime_evidence_root)
        )
    tick_manifest_path = getattr(args, "tick_source_manifest", None)
    expected_tick_manifest_sha256 = str(
        getattr(args, "expected_tick_source_manifest_sha256", None) or ""
    ).strip()
    bound_tick_source_specs = None
    bound_tick_source_contract = None
    bound_tick_source_gaps: dict[str, tuple[str, ...]] = {}
    bound_tick_diagnostic_contract = None
    sealed_tick_ledger_path_value = getattr(
        args, "sealed_tick_source_ledger", None
    )
    sealed_tick_ledger_sha256 = str(
        getattr(
            args,
            "expected_sealed_tick_source_ledger_sha256",
            None,
        )
        or ""
    ).strip()
    sealed_tick_full_component_set = bool(
        getattr(args, "sealed_tick_full_component_set", False)
    )
    diagnostic_manifest_paths = tuple(
        Path(value)
        for value in (getattr(args, "tick_diagnostic_manifests", None) or ())
    )
    diagnostic_manifest_hashes = tuple(
        str(value)
        for value in (
            getattr(
                args,
                "expected_tick_diagnostic_manifest_sha256s",
                None,
            )
            or ()
        )
    )
    if len(diagnostic_manifest_paths) != len(diagnostic_manifest_hashes):
        raise ValueError(
            "attempt5_bound_tick_diagnostic_authority_args_incomplete"
        )
    sealed_ledger_requested = bool(
        sealed_tick_ledger_path_value
        or sealed_tick_ledger_sha256
        or sealed_tick_full_component_set
    )
    if sealed_ledger_requested:
        if (
            sealed_tick_ledger_path_value is None
            or not sealed_tick_ledger_sha256
            or not sealed_tick_full_component_set
            or tick_manifest_path is not None
            or expected_tick_manifest_sha256
            or diagnostic_manifest_paths
            or diagnostic_manifest_hashes
        ):
            raise ValueError(
                "sealed_tick_source_ledger_authority_args_incomplete"
            )
        (
            bound_tick_source_specs,
            bound_tick_source_contract,
        ) = bound_tick_source_authority_from_sealed_source_ledger(
            ledger_path=Path(sealed_tick_ledger_path_value),
            expected_ledger_sha256=sealed_tick_ledger_sha256,
        )
        bound_tick_source_gaps = {}
        diagnostic_core = {
            "schema": (
                "gtos.replay_acceleration."
                "bound_tick_diagnostic_authority.v1"
            ),
            "status": "sealed_source_ledger_requires_no_gap_diagnostics",
            "manifests": [],
            "manifest_count": 0,
            "gap_count": 0,
            "symbols_with_gaps": [],
            "gaps_by_symbol": {},
            "broad_retired_repo_scan_enabled": False,
            "january_overlap_allowed": False,
        }
        bound_tick_diagnostic_contract = {
            **diagnostic_core,
            "contract_root_sha256": stable_sha256(diagnostic_core),
        }
    elif tick_manifest_path is not None or expected_tick_manifest_sha256:
        if tick_manifest_path is None or not expected_tick_manifest_sha256:
            raise ValueError("attempt5_bound_tick_authority_args_incomplete")
        cache_values = {
            "authority_summary_path": getattr(
                args, "tick_authority_cache_summary", None
            ),
            "expected_authority_summary_sha256": getattr(
                args, "expected_tick_authority_cache_summary_sha256", None
            ),
            "source_ledger_path": getattr(
                args, "tick_authority_cache_source_ledger", None
            ),
            "expected_source_ledger_sha256": getattr(
                args,
                "expected_tick_authority_cache_source_ledger_sha256",
                None,
            ),
            "expected_source_contract_root_sha256": getattr(
                args,
                "expected_tick_source_contract_root_sha256",
                None,
            ),
            "expected_diagnostic_contract_root_sha256": getattr(
                args,
                "expected_tick_diagnostic_contract_root_sha256",
                None,
            ),
        }
        cache_requested = any(value is not None for value in cache_values.values())
        if cache_requested:
            if not all(value is not None for value in cache_values.values()):
                raise ValueError(
                    "attempt5_tick_authority_replay_cache_args_incomplete"
                )
            (
                bound_tick_source_specs,
                bound_tick_source_contract,
                bound_tick_source_gaps,
                bound_tick_diagnostic_contract,
            ) = bound_tick_authorities_from_replay_cache(
                authority_summary_path=Path(
                    cache_values["authority_summary_path"]
                ),
                expected_authority_summary_sha256=str(
                    cache_values["expected_authority_summary_sha256"]
                ),
                source_ledger_path=Path(cache_values["source_ledger_path"]),
                expected_source_ledger_sha256=str(
                    cache_values["expected_source_ledger_sha256"]
                ),
                manifest_path=Path(tick_manifest_path),
                expected_manifest_sha256=expected_tick_manifest_sha256,
                expected_source_contract_root_sha256=str(
                    cache_values["expected_source_contract_root_sha256"]
                ),
                diagnostic_manifest_bindings=tuple(
                    zip(diagnostic_manifest_paths, diagnostic_manifest_hashes)
                ),
                expected_diagnostic_contract_root_sha256=str(
                    cache_values[
                        "expected_diagnostic_contract_root_sha256"
                    ]
                ),
            )
        else:
            bound_tick_source_specs, bound_tick_source_contract = (
                bound_tick_source_authority(
                    manifest_path=Path(tick_manifest_path),
                    expected_manifest_sha256=expected_tick_manifest_sha256,
                )
            )
            bound_tick_source_gaps, bound_tick_diagnostic_contract = (
                bound_tick_diagnostic_authority(
                    tuple(
                        zip(
                            diagnostic_manifest_paths,
                            diagnostic_manifest_hashes,
                        )
                    )
                )
            )
    expected_source_plan_digest = str(
        getattr(args, "expected_source_plan_digest_sha256", None) or ""
    ).strip()
    source_authority_values = {
        "source_bundle_dir": getattr(args, "source_acceleration_bundle_dir", None),
        "selection_path": getattr(args, "source_acceleration_selection", None),
        "expected_bundle_root": getattr(
            args, "expected_source_bundle_root_sha256", None
        ),
    }
    source_authority_requested = any(
        value is not None for value in source_authority_values.values()
    )
    typed_cache_root = getattr(args, "source_acceleration_cache_root", None)
    physical_reference_requested = bool(
        getattr(args, "accepted_physical_reference", False)
    )
    if source_authority_requested and (
        not all(value is not None for value in source_authority_values.values())
        or not expected_source_plan_digest
    ):
        raise ValueError("source_acceleration_authority_args_incomplete")
    if physical_reference_requested:
        if not source_authority_requested or typed_cache_root is not None:
            raise ValueError("physical_reference_source_authority_invalid")
    elif source_authority_requested != (typed_cache_root is not None):
        raise ValueError("source_acceleration_authority_args_incomplete")
    source_accelerator = None
    physical_source_reference = None
    if physical_reference_requested:
        physical_source_reference = (
            AcceptedPhysicalSourceReference.from_accepted_bundle(
                source_bundle_dir=Path(
                    source_authority_values["source_bundle_dir"]
                ),
                selection_path=Path(
                    source_authority_values["selection_path"]
                ),
                expected_bundle_root=str(
                    source_authority_values["expected_bundle_root"]
                ),
                expected_source_plan_digest=expected_source_plan_digest,
            )
        )
    elif source_authority_requested:
        source_accelerator = RealReplaySourceAccelerator.from_accepted_bundle(
            source_bundle_dir=Path(source_authority_values["source_bundle_dir"]),
            selection_path=Path(source_authority_values["selection_path"]),
            typed_cache_root=Path(typed_cache_root),
            expected_bundle_root=str(
                source_authority_values["expected_bundle_root"]
            ),
            expected_source_plan_digest=expected_source_plan_digest,
        )
        args.source_acceleration_authority = bound_source_acceleration_authority(
            args,
            source_accelerator,
        )
    factorial_arm_binding = selection_sizing_factorial_binding_from_args(args)
    parity_gate_day = str(
        getattr(args, "parity_gate_after_day", None) or ""
    ).strip()
    parity_request_path = getattr(args, "parity_gate_request", None)
    parity_report_path = getattr(args, "parity_report", None)
    parity_receipt_path = getattr(args, "parity_receipt", None)
    parity_gate_requested = bool(
        parity_gate_day
        or parity_request_path
        or parity_report_path
        or parity_receipt_path
    )
    physical_reference_checkpoint_day = str(
        getattr(args, "physical_reference_checkpoint_after_day", None) or ""
    ).strip()
    task2_semantic_checkpoint_day = str(
        getattr(args, "task2_semantic_checkpoint_after_day", None) or ""
    ).strip()
    if physical_reference_requested:
        if (
            physical_reference_checkpoint_day != ATTEMPT5_PARITY_DAY
            or parity_gate_requested
            or bool(getattr(args, "stop_after_parity_gate", False))
        ):
            raise ValueError("physical_reference_checkpoint_scope_invalid")
    elif physical_reference_checkpoint_day:
        raise ValueError("physical_reference_checkpoint_requires_physical_loader")
    if task2_semantic_checkpoint_day:
        if (
            task2_semantic_checkpoint_day != "2026-01-02"
            or physical_reference_requested
            or parity_gate_requested
            or args.start != ATTEMPT5_START_DAY
            or args.end != ATTEMPT5_CONTRACT_END_DAY
            or args.max_days is not None
            or int(args.chunk_size) != 1
            or list(args.profiles) != [PROFILE_REPAIRED]
            or not isinstance(factorial_arm_binding, Mapping)
            or factorial_arm_binding.get("arm_id") != "S0R0"
            or source_accelerator is None
            or runtime_evidence_contract is None
            or getattr(args, "streaming_proof_archive_root", None) is not None
        ):
            raise ValueError("task2_semantic_checkpoint_scope_invalid")
    if parity_gate_requested:
        if not all(
            (
                parity_gate_day,
                parity_request_path,
                parity_report_path,
                parity_receipt_path,
            )
        ):
            raise ValueError("real_parity_gate_args_incomplete")
        if (
            parity_gate_day != "2026-01-07"
            or args.start != "2026-01-01"
            or args.end != "2026-01-31"
            or args.max_days is not None
            or int(args.chunk_size) != 1
            or list(args.profiles) != [PROFILE_REPAIRED]
            or not isinstance(factorial_arm_binding, Mapping)
            or factorial_arm_binding.get("arm_id") != "S0R0"
            or source_accelerator is None
            or runtime_evidence_contract is None
        ):
            raise ValueError("real_parity_gate_scope_not_authorized")
        timeout_seconds = int(
            getattr(args, "parity_wait_timeout_seconds", 0) or 0
        )
        if timeout_seconds < 1 or timeout_seconds > 604800:
            raise ValueError("real_parity_gate_timeout_invalid")
        for path in (
            Path(parity_request_path),
            Path(parity_report_path),
            Path(parity_receipt_path),
        ):
            if path.exists() or path.is_symlink():
                raise ValueError("real_parity_gate_artifact_must_be_new")
    elif bool(getattr(args, "stop_after_parity_gate", False)):
        raise ValueError("stop_after_parity_gate_requires_gate")
    streaming_archive_root = getattr(args, "streaming_proof_archive_root", None)
    streaming_archive_max_bytes = int(
        getattr(args, "max_streaming_proof_archive_bytes", 0) or 0
    )
    if parity_gate_requested and not bool(
        getattr(args, "stop_after_parity_gate", False)
    ):
        if streaming_archive_root is None:
            raise ValueError("parity_continuation_requires_streaming_proof_archive")
    if streaming_archive_root is not None:
        if not parity_gate_requested:
            raise ValueError("streaming_proof_archive_requires_parity_gate")
        if (
            streaming_archive_max_bytes < 1
            or streaming_archive_max_bytes > 1024 * 1024 * 1024
        ):
            raise ValueError("streaming_proof_archive_quota_invalid")
        archive_path = Path(streaming_archive_root)
        if archive_path.exists() or archive_path.is_symlink():
            raise ValueError("streaming_proof_archive_root_must_be_new")
    skip_tick_source = getattr(args, "skip_tick_source", False)
    requested_symbols_arg = getattr(args, "symbols", None)
    compact_missed_ledger = bool(getattr(args, "compact_missed_ledger", False))
    compact_decision_ledger = bool(
        getattr(args, "compact_decision_ledger", False)
    )
    compact_scorecard_ledger = bool(
        getattr(args, "compact_scorecard_ledger", False)
    )
    compact_event_sink_enabled = bool(
        getattr(args, "compact_event_sink", False)
    )
    compact_event_max_shard_bytes = int(
        getattr(args, "compact_event_max_shard_bytes", 128 * 1024 * 1024)
    )
    if not (1_024 <= compact_event_max_shard_bytes <= 128 * 1024 * 1024):
        raise ValueError("compact_event_max_shard_bytes_out_of_bounds")
    prepared_day_pack_root_value = getattr(args, "prepared_day_pack_root", None)
    prepared_day_pack_root = (
        Path(prepared_day_pack_root_value)
        if prepared_day_pack_root_value is not None
        else None
    )
    if prepared_day_pack_root is not None and (
        not prepared_day_pack_root.is_dir()
        or prepared_day_pack_root.is_symlink()
    ):
        raise ValueError("prepared_day_pack_root_invalid")
    expected_prepared_day_pack_roots = (
        expected_prepared_day_pack_roots_from_args(args)
    )
    prepared_day_pack_build_root_value = getattr(
        args,
        "build_prepared_day_pack_root",
        None,
    )
    prepared_day_pack_build_root = (
        Path(prepared_day_pack_build_root_value)
        if prepared_day_pack_build_root_value is not None
        else None
    )
    prepared_day_pack_build_only = bool(
        getattr(args, "prepared_day_pack_build_only", False)
    )
    if prepared_day_pack_build_root is not None:
        if prepared_day_pack_build_root.exists() or prepared_day_pack_build_root.is_symlink():
            raise ValueError("prepared_day_pack_build_root_must_be_new")
        if prepared_day_pack_root is not None:
            raise ValueError(
                "prepared_day_pack_build_and_existing_roots_mutually_exclusive"
            )
    if prepared_day_pack_build_only and prepared_day_pack_build_root is None:
        raise ValueError("prepared_day_pack_build_only_requires_build_root")
    prepared_pack_target_raw_shard_bytes = int(
        getattr(args, "prepared_pack_target_raw_shard_bytes", 32 * 1024 * 1024)
    )
    if not 1 <= prepared_pack_target_raw_shard_bytes <= 128 * 1024 * 1024:
        raise ValueError("prepared_pack_target_raw_shard_bytes_out_of_bounds")
    omit_candidate_index_ledger = bool(
        getattr(args, "omit_candidate_index_ledger", False)
    )
    candidate_relational_mode = bool(
        args.omit_candidate_ledger and omit_candidate_index_ledger
    )
    outputs = output_paths(output_prefix)
    semantic_outputs = semantic_output_paths(output_prefix)
    source_outputs = {**outputs, **semantic_outputs}
    streaming_archive = (
        StreamingProofArchive(
            root=Path(streaming_archive_root),
            output_prefix=output_prefix,
            hot_outputs={
                role: outputs[role]
                for role in ("decision", "scorecard", "missed")
            },
            max_archive_bytes=streaming_archive_max_bytes,
            hard_floor_free_bytes=ATTEMPT5_STREAMING_HARD_FLOOR_BYTES,
            warning_floor_free_bytes=attempt5_streaming_warning_floor_bytes(
                args,
                parity_gate_requested=parity_gate_requested,
            ),
        )
        if streaming_archive_root is not None
        else None
    )
    runtime_input_contract = ultimate_package_runtime_input_contract()
    requested_symbols = requested_replay_symbols(requested_symbols_arg)
    profile_configs = {
        str(profile): build_config(
            str(profile),
            factorial_arm_binding=factorial_arm_binding,
        )
        for profile in args.profiles
    }
    shared_execution_contract = broad_replay_shared_execution_contract(
        profiles=args.profiles,
        active_symbols=active_replay_symbol_universe(requested_symbols),
        execution_options=broad_replay_execution_options_from_args(
            args,
            factorial_arm_binding=factorial_arm_binding,
        ),
        runtime_input_contract=runtime_input_contract,
        factorial_arm_binding=factorial_arm_binding,
        profile_configs=profile_configs,
    )
    expected_shared_execution_digest = str(
        getattr(args, "expected_shared_execution_contract_sha256", None) or ""
    ).strip()
    contract_split = None
    if parity_gate_requested:
        contract_split = split_shared_execution_contract(
            shared_execution_contract
        )
        expected_economic_execution_digest = str(
            getattr(
                args,
                "expected_economic_execution_contract_sha256",
                None,
            )
            or ""
        ).strip()
        if (
            expected_economic_execution_digest
            != contract_split["economic_execution_contract_digest_sha256"]
        ):
            raise ValueError("economic_execution_contract_digest_mismatch")
        no_replay_preflight = no_replay_contract_preflight(
            prospective_golden_authority=args.prospective_golden_authority,
            current_shared_execution_contract=shared_execution_contract,
            source_bundle_consumer_rebind_authority=(
                args.bound_source_bundle_consumer_rebind_authority
            ),
        )
        no_replay_preflight_path = (
            Path(args.output_dir)
            / "TASK2_NO_REPLAY_CONTRACT_PREFLIGHT_RECEIPT.json"
        )
        atomic_write_gate_json(no_replay_preflight_path, no_replay_preflight)
    else:
        no_replay_preflight = None
        no_replay_preflight_path = None
    reset_outputs(outputs)
    b7_5_contract_binding_required = "_B7_5_" in output_prefix.upper()
    runtime_preflight_payload = {
                "schema": (
                    "gtos.final_moonshot.broad_live_as_if_replay_harness."
                    "partial_summary.runtime_input_preflight.v1"
                ),
                "generated_at_utc": utc_now(),
                "route_id": ROUTE.name,
                "output_prefix": output_prefix,
                "status": "runtime_input_preflight_not_final_proof",
                "profiles_requested": list(args.profiles),
                "candidate_ledger_omitted": args.omit_candidate_ledger,
                "candidate_index_ledger_omitted": omit_candidate_index_ledger,
                "missed_ledger_compacted": compact_missed_ledger,
                "decision_ledger_compacted": compact_decision_ledger,
                "scorecard_ledger_compacted": compact_scorecard_ledger,
                "compact_event_sink_enabled": compact_event_sink_enabled,
                "compact_event_sink_roles": (
                    ["decision", "missed"] if compact_event_sink_enabled else []
                ),
                "packet_sidecar_ledger_omitted": args.omit_packet_sidecar_ledger,
                "ultimate_package_runtime_input_contract": runtime_input_contract,
                "runtime_evidence_contract": runtime_evidence_contract,
                "bound_tick_source_authority": bound_tick_source_contract,
                "bound_tick_diagnostic_authority": (
                    bound_tick_diagnostic_contract
                ),
                "source_acceleration_authority": (
                    bound_source_acceleration_authority(
                        args,
                        source_accelerator,
                    )
                    if source_accelerator is not None
                    else None
                ),
                "streaming_proof_archive": (
                    streaming_archive.authority()
                    if streaming_archive is not None
                    else None
                ),
                "shared_execution_contract": shared_execution_contract,
                "attempt5_execution_identity": (
                    dict(attempt5_execution_identity)
                    if isinstance(attempt5_execution_identity, Mapping)
                    else None
                ),
                **(
                    {
                        "b7_5_selection_sizing_factorial_arm_binding": (
                            factorial_arm_binding
                        )
                    }
                    if factorial_arm_binding is not None
                    else {}
                ),
                "b7_5_contract_binding": {
                    "required": b7_5_contract_binding_required,
                    "expected_shared_execution_contract_digest_sha256": (
                        expected_shared_execution_digest or None
                    ),
                    "expected_source_plan_digest_sha256": (
                        expected_source_plan_digest or None
                    ),
                },
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
                "partial_summary_semantics": (
                    "runtime_input_preflight_only_run_campaign_not_entered"
                ),
                "evidence_class": SIM_EVIDENCE_CLASS,
            }
    atomic_write_json(
        outputs["partial_summary"],
        json_safe(runtime_preflight_payload),
    )
    require_ultimate_package_runtime_inputs(contract=runtime_input_contract)
    if shared_execution_contract.get("valid") is not True:
        raise ValueError(
            "broad_replay_shared_execution_contract_invalid:"
            f"{json.dumps(shared_execution_contract, sort_keys=True)}"
        )
    if b7_5_contract_binding_required and not (
        expected_shared_execution_digest and expected_source_plan_digest
    ):
        raise ValueError("b7_5_expected_contract_binding_missing")
    if (
        expected_shared_execution_digest
        and expected_shared_execution_digest
        != shared_execution_contract.get(
            "shared_execution_contract_digest_sha256"
        )
    ):
        raise ValueError("broad_replay_shared_execution_contract_digest_mismatch")
    if source_accelerator is not None:
        source_accelerator.prewarm_all(
            workers=int(getattr(args, "source_prewarm_workers", 1))
        )
        runtime_preflight_payload["source_acceleration_authority"] = (
            bound_source_acceleration_authority(
                args,
                source_accelerator,
            )
        )
        runtime_preflight_payload["status"] = (
            "runtime_input_and_source_acceleration_barrier_complete_"
            "run_campaign_not_entered"
        )
        atomic_write_json(
            outputs["partial_summary"],
            json_safe(runtime_preflight_payload),
        )
    tick_sparse_window_start, tick_sparse_window_end = (
        attempt5_effective_execution_tick_sparse_cache_window(args)
    )
    tick_sparse_integrity_attestations: dict[str, dict[str, Any]] | None = None
    if bound_tick_source_specs and getattr(
        args, "tick_sparse_cache_root", None
    ) is not None:
        tick_sparse_prewarm = prewarm_sparse_tick_sources(
            specs_by_symbol=bound_tick_source_specs,
            cache_root=Path(args.tick_sparse_cache_root),
            window_start=tick_sparse_window_start,
            window_end=tick_sparse_window_end,
            workers=int(getattr(args, "source_prewarm_workers", 1)),
        )
        tick_sparse_integrity_attestations = sparse_tick_source_attestations(
            tick_sparse_prewarm
        )
        atomic_write_json(
            Path(args.output_dir)
            / "ATTEMPT5_TICK_SPARSE_CACHE_PREWARM_RECEIPT.json",
            tick_sparse_prewarm,
        )
    resolver_kwargs = {
        "use_native_h1": args.use_native_h1,
        "skip_tick_source": skip_tick_source,
        "verbose": args.verbose,
        "source_accelerator": source_accelerator,
        "physical_source_reference": physical_source_reference,
        "bound_tick_source_specs": bound_tick_source_specs,
        "bound_tick_source_gaps": bound_tick_source_gaps,
        "bound_tick_logical_repo_root": (
            Path(str(bound_tick_source_contract["logical_repo_root"]))
            if (
                bound_tick_source_contract is not None
                and bound_tick_source_contract.get("logical_repo_root")
            )
            else None
        ),
        "sealed_tick_full_component_set": sealed_tick_full_component_set,
        "tick_sparse_cache_root": (
            Path(args.tick_sparse_cache_root)
            if getattr(args, "tick_sparse_cache_root", None) is not None
            else None
        ),
        "tick_sparse_window_start": tick_sparse_window_start,
        "tick_sparse_window_end": tick_sparse_window_end,
    }
    resolver = BroadSourceResolver(**resolver_kwargs)
    preparation_resolver = (
        BroadSourceResolver(**resolver_kwargs)
        if prepared_day_pack_build_root is not None
        else None
    )
    def resolve_sources_for_scope(
        execution_days: tuple[str, ...],
        source_authority_days: tuple[str, ...],
        *,
        resolver_instance: BroadSourceResolver | None = None,
    ) -> dict[str, dict[str, ResolvedSource]]:
        active_resolver = resolver_instance or resolver
        try:
            return active_resolver.build_sources_for_days(
                execution_days,
                symbols=requested_symbols,
                source_authority_days=source_authority_days,
            )
        except TypeError as exc:
            if requested_symbols or "unexpected keyword argument" not in str(exc):
                raise
            return active_resolver.build_sources_for_days(execution_days)

    days_by_split = build_days_by_split(args.start, args.end, max_days=args.max_days)
    chunk_plan = tuple(profile_chunks(days_by_split, args.chunk_size))
    engineering_stop_after_day = str(
        getattr(args, "engineering_stop_after_day", None) or ""
    ).strip()
    if engineering_stop_after_day:
        selected_days = {
            day for days in days_by_split.values() for day in days
        }
        if engineering_stop_after_day not in selected_days:
            raise ValueError("engineering_stop_after_day_not_selected")
        bounded_chunks: list[tuple[str, tuple[str, ...]]] = []
        stop_reached = False
        for split, chunk_days in chunk_plan:
            kept: list[str] = []
            for day in chunk_days:
                kept.append(day)
                if day == engineering_stop_after_day:
                    stop_reached = True
                    break
            if kept:
                bounded_chunks.append((split, tuple(kept)))
            if stop_reached:
                break
        if not stop_reached:
            raise ValueError("engineering_stop_after_day_order_invalid")
        chunk_plan = tuple(bounded_chunks)
    prepared_day_pack_build_receipts: list[dict[str, Any]] = []
    preparation_source_emission_reset: dict[str, Any] | None = None
    if prepared_day_pack_build_root is not None:
        preparation_config = profile_configs[str(args.profiles[0])]
        for split, chunk_days in chunk_plan:
            if not chunk_days:
                continue
            source_authority_days = tuple(days_by_split.get(split, ()))
            prepared_sources = resolve_sources_for_scope(
                tuple(chunk_days),
                source_authority_days,
                resolver_instance=preparation_resolver,
            )
            prepared_campaign = CampaignConfig(
                name="arm_neutral_prepared_day_pack",
                phase=f"arm_neutral_{split}",
                days=tuple(chunk_days),
                pending_expiry_minutes=REPAIRED_PENDING_EXPIRY_MINUTES,
                use_repaired_pending_expiry=True,
                profile="ARM_NEUTRAL",
                partial_be_runner=True,
                max_candidates_per_symbol_window=(
                    args.max_candidates_per_symbol_window
                ),
                run_smoke_subset=args.smoke_subset,
                materialize_packet_sidecars=False,
                materialize_semantic_diagnostics=True,
                candidate_ledger_packet_max_bytes=(
                    args.candidate_ledger_packet_max_bytes
                ),
                scorecard_ledger_packet_max_bytes=(
                    args.scorecard_ledger_packet_max_bytes
                ),
                compact_scorecard_symbol_risk_config=(
                    args.compact_scorecard_symbol_risk_config
                ),
                scorecard_probe_row_limit=args.scorecard_probe_row_limit,
            )
            prepared_pack_path = (
                prepared_day_pack_build_root
                / str(split)
                / f"{chunk_days[0]}_{chunk_days[-1]}"
            )
            build_receipt = build_campaign_prepared_day_pack(
                output_dir=prepared_pack_path,
                campaign=prepared_campaign,
                config=preparation_config,
                sources=prepared_sources,
                encoding_worker_count=int(
                    getattr(args, "prepared_pack_encoding_workers", 1)
                ),
                target_raw_shard_bytes=prepared_pack_target_raw_shard_bytes,
                borrow_campaign_cache_owner=True,
            )
            prepared_day_pack_build_receipts.append(
                {
                    **build_receipt,
                    "split": str(split),
                    "days": list(chunk_days),
                    "path": str(prepared_pack_path),
                }
            )
        prepared_day_pack_root = prepared_day_pack_build_root
        if preparation_resolver is None:
            raise ValueError("prepared_day_pack_preparation_resolver_missing")
        preparation_source_emission_reset = (
            preparation_resolver.reset_source_row_emission()
        )
        expected_prepared_day_pack_roots = {
            (
                str(row["split"]),
                str(row["days"][0]),
                str(row["days"][-1]),
            ): str(row["pack_root_sha256"])
            for row in prepared_day_pack_build_receipts
        }
    expected_prepared_pack_keys = {
        (str(split), str(days[0]), str(days[-1]))
        for split, days in chunk_plan
        if days
    }
    if prepared_day_pack_root is not None and (
        set(expected_prepared_day_pack_roots) != expected_prepared_pack_keys
    ):
        raise ValueError("expected_prepared_day_pack_roots_incomplete")
    if prepared_day_pack_root is None and expected_prepared_day_pack_roots:
        raise ValueError("expected_prepared_day_pack_roots_without_pack")
    planned_chunk_count = len(chunk_plan) * len(args.profiles)
    full_available_days_by_split = build_days_by_split(DEFAULT_START, DEFAULT_END, max_days=None)
    selected_day_count = sum(len(days) for days in days_by_split.values())
    full_available_day_count = sum(len(days) for days in full_available_days_by_split.values())
    coverage_status = (
        "full_configured_available_date_range"
        if (
            args.start == DEFAULT_START
            and args.end == DEFAULT_END
            and args.max_days is None
            and not args.smoke_subset
            and not engineering_stop_after_day
        )
        else "bounded_replay_materialization_not_full_available_universe"
    )
    bounded_smoke = coverage_status != "full_configured_available_date_range"
    bounded_symbol_scope_smoke = bool(requested_symbols)
    split_rows = [
        {
            "row_type": "split_definition",
            "split": split,
            "start": start,
            "end": end,
            "selected_days": len(days_by_split.get(split, ())),
            "repair_seed_overlap": split == "development",
            "repair_seed_start": REPAIR_SEED_START if split == "development" else None,
            "repair_seed_end": REPAIR_SEED_END if split == "development" else None,
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
            "evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
            **selection_sizing_factorial_ledger_fields(factorial_arm_binding),
        }
        for split, start, end in SPLIT_RANGES
    ]
    ledger_write_row_counts: Counter[str] = Counter()
    semantic_ledger_write_row_counts: Counter[str] = Counter()
    ledger_write_row_counts["source"] += append_jsonl(outputs["source"], split_rows)
    compact_projection_counts: Counter[str] = Counter()
    compact_event_sink_checkpoints: list[dict[str, Any]] = []
    prepared_day_pack_checkpoints: list[dict[str, Any]] = []
    candidate_relational_chunk_audits: list[dict[str, Any]] = []
    candidate_relational_candidate_keys: set[str] = set()
    candidate_relational_terminal_keys: set[str] = set()
    candidate_relational_candidate_rows = 0
    candidate_relational_missing_keys: Counter[str] = Counter()
    candidate_relational_disposition_counts: Counter[str] = Counter()

    def candidate_relational_summary() -> dict[str, Any]:
        duplicate_candidate_rows = (
            candidate_relational_candidate_rows
            - len(candidate_relational_candidate_keys)
            - candidate_relational_missing_keys["candidate"]
        )
        candidate_minus_terminal = (
            candidate_relational_candidate_keys
            - candidate_relational_terminal_keys
        )
        terminal_minus_candidate = (
            candidate_relational_terminal_keys
            - candidate_relational_candidate_keys
        )
        exact = bool(candidate_relational_mode) and not any(
            (
                not candidate_relational_chunk_audits,
                not candidate_relational_candidate_rows,
                duplicate_candidate_rows,
                sum(candidate_relational_missing_keys.values()),
                len(candidate_minus_terminal),
                len(terminal_minus_candidate),
            )
        )
        return {
            "schema": CANDIDATE_RELATIONAL_MATERIALIZATION_SCHEMA,
            "enabled": candidate_relational_mode,
            "status": (
                "exact_candidate_equals_one_disjoint_terminal_disposition"
                if exact
                else (
                    "not_requested_dedicated_candidate_ledger_materialized"
                    if not candidate_relational_mode
                    else "candidate_relational_materialization_mismatch"
                )
            ),
            "exact": exact,
            "terminal_reconciliation_exact": exact,
            "graph": "research_timewarp",
            "production_parity": False,
            "pretrade_cost_role": "pretrade_expected_estimate_only",
            "post_lifecycle_cost_accounting_status": (
                "NOT_EVALUABLE_NOT_MATERIALIZED_BY_CURRENT_NATIVE_LEDGERS"
            ),
            "full_flow_economics_complete": False,
            "chunk_audit_count": len(candidate_relational_chunk_audits),
            "candidate_rows": candidate_relational_candidate_rows,
            "candidate_unique_profile_scoped_instance_keys": len(
                candidate_relational_candidate_keys
            ),
            "candidate_duplicate_profile_scoped_instance_rows": (
                duplicate_candidate_rows
            ),
            "terminal_union_unique_profile_scoped_instance_keys": len(
                candidate_relational_terminal_keys
            ),
            "terminal_disposition_counts": {
                role: int(candidate_relational_disposition_counts[role])
                for role in ("missed", "trade", "terminal_unfilled")
            },
            "missing_instance_key_counts": dict(
                sorted(candidate_relational_missing_keys.items())
            ),
            "candidate_minus_terminal_union_count": len(
                candidate_minus_terminal
            ),
            "terminal_union_minus_candidate_count": len(
                terminal_minus_candidate
            ),
            "candidate_minus_terminal_union_sample": sorted(
                candidate_minus_terminal
            )[:8],
            "terminal_union_minus_candidate_sample": sorted(
                terminal_minus_candidate
            )[:8],
        }

    accumulator = SummaryAccumulator()
    progress_rows: list[dict[str, Any]] = []
    chunk_capacity_checkpoints: list[dict[str, Any]] = []
    source_authority_checkpoints: list[dict[str, Any]] = []
    canonical_source_authority_plans: dict[str, dict[str, Any]] = {}
    source_authority_preflight_checkpoints: list[dict[str, Any]] = []
    accepted_real_parity_gate: dict[str, Any] | None = None
    last_streaming_current_summary_contract: dict[str, Any] | None = None
    streaming_archive_shards: list[dict[str, Any]] = []
    streaming_capacity_checks: list[dict[str, Any]] = []
    completed_semantic_days_by_profile: dict[str, list[str]] = {
        str(profile): [] for profile in args.profiles
    }
    campaign_exact_cache_profiles: list[dict[str, Any]] = []
    source_plan_symbols = active_replay_symbol_universe(requested_symbols)
    def build_exact_source_authority_plan(
        *,
        sources: Mapping[str, Mapping[str, ResolvedSource]],
        source_authority_days: Iterable[str],
    ) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "sources": sources,
            "source_authority_days": source_authority_days,
            "requested_symbols": source_plan_symbols,
        }
        if tick_sparse_integrity_attestations is not None:
            kwargs["tick_integrity_attestations"] = (
                tick_sparse_integrity_attestations
            )
        return static_source_authority_plan(**kwargs)

    gc_between_chunks = bool(
        getattr(args, "gc_between_chunks", True)
        or os.environ.get("GTOS_BROAD_REPLAY_GC_BETWEEN_CHUNKS") == "1"
    )

    # Canonical authority is built from each complete split before any replay
    # chunk starts. Chunk-local M1 hydration is then checked as an exact subset
    # of this immutable full-window plan.
    for split, authority_days_value in days_by_split.items():
        source_authority_days = tuple(authority_days_value)
        if not source_authority_days:
            continue
        canonical_sources = resolve_sources_for_scope(
            source_authority_days,
            source_authority_days,
        )
        canonical_source_plan = build_exact_source_authority_plan(
            sources=canonical_sources,
            source_authority_days=source_authority_days,
        )
        source_scope = canonical_source_plan.get("source_authority_scope")
        source_scope = (
            source_scope if isinstance(source_scope, Mapping) else {}
        )
        source_plan_key = f"{split}:{source_scope.get('scope_id') or ''}"
        if canonical_source_plan.get("valid") is not True:
            raise ValueError(
                "canonical_source_authority_preflight_failed:"
                f"{source_plan_key}:"
                f"{json.dumps(canonical_source_plan, sort_keys=True)}"
            )
        if source_plan_key in canonical_source_authority_plans:
            raise ValueError(
                "duplicate_canonical_source_authority_scope:"
                f"{source_plan_key}"
            )
        canonical_source_authority_plans[source_plan_key] = dict(
            canonical_source_plan
        )
        ledger_write_row_counts["source"] += append_jsonl(
            outputs["source"],
            [
                {
                    **dict(row),
                    **selection_sizing_factorial_ledger_fields(
                        factorial_arm_binding
                    ),
                }
                for row in resolver.drain_source_rows()
            ],
        )
        del canonical_sources
        source_cache_release = resolver.release_completed_chunk_caches(
            source_authority_days,
            source_authority_days=source_authority_days,
        )
        gc_collected_objects = gc.collect() if gc_between_chunks else None
        if gc_between_chunks:
            darwin_allocator_pressure_relief()
        cleanup_valid = bool(
            int(
                source_cache_release.get(
                    "completed_chunk_day_scoped_entries_remaining"
                )
                or 0
            )
            == 0
            and int(
                source_cache_release.get(
                    "completed_source_authority_scoped_entries_remaining"
                )
                or 0
            )
            == 0
            and source_cache_release.get(
                "completed_replay_source_caches_released"
            )
            is True
        )
        preflight_checkpoint = {
            "split": split,
            "source_plan_key": source_plan_key,
            "source_authority_days": list(source_authority_days),
            "source_authority_day_count": len(source_authority_days),
            "canonical_source_plan_digest_sha256": (
                canonical_source_plan.get("plan_digest_sha256")
            ),
            "canonical_source_plan_valid": True,
            "cleanup_valid": cleanup_valid,
            "source_cache_release": source_cache_release,
            "explicit_gc_requested": gc_between_chunks,
            "gc_collected_objects": gc_collected_objects,
        }
        if not cleanup_valid:
            raise ValueError(
                "canonical_source_authority_preflight_cleanup_failed:"
                f"{source_plan_key}:"
                f"{json.dumps(preflight_checkpoint, sort_keys=True)}"
            )
        source_authority_preflight_checkpoints.append(preflight_checkpoint)

    canonical_source_plan_digests = sorted(
        str(plan.get("plan_digest_sha256") or "")
        for plan in canonical_source_authority_plans.values()
    )
    if expected_source_plan_digest and (
        len(canonical_source_plan_digests) != 1
        or canonical_source_plan_digests[0] != expected_source_plan_digest
    ):
        raise ValueError(
            "broad_replay_source_plan_digest_mismatch:"
            f"expected={expected_source_plan_digest}:"
            f"actual={canonical_source_plan_digests}"
        )
    b7_5_contract_binding = {
        "required": b7_5_contract_binding_required,
        "status": (
            "b7_5_source_and_execution_contracts_bound"
            if b7_5_contract_binding_required
            else "optional_contract_binding_not_required"
        ),
        "valid": bool(
            not b7_5_contract_binding_required
            or (
                expected_shared_execution_digest
                == shared_execution_contract.get(
                    "shared_execution_contract_digest_sha256"
                )
                and len(canonical_source_plan_digests) == 1
                and canonical_source_plan_digests[0]
                == expected_source_plan_digest
            )
        ),
        "expected_shared_execution_contract_digest_sha256": (
            expected_shared_execution_digest or None
        ),
        "actual_shared_execution_contract_digest_sha256": (
            shared_execution_contract.get(
                "shared_execution_contract_digest_sha256"
            )
        ),
        "expected_source_plan_digest_sha256": (
            expected_source_plan_digest or None
        ),
        "actual_source_plan_digests_sha256": canonical_source_plan_digests,
        "selection_sizing_factorial_arm_binding": factorial_arm_binding,
    }
    streaming_checkpoint_authority = None
    if streaming_archive is not None:
        if not isinstance(attempt5_execution_identity, Mapping):
            raise ValueError("attempt5_streaming_checkpoint_identity_missing")
        identity_projection = dict(attempt5_execution_identity)
        identity_root_sha256 = identity_projection.pop(
            "identity_root_sha256",
            None,
        )
        if (
            identity_root_sha256 != stable_sha256(identity_projection)
            or attempt5_execution_identity.get("output_prefix") != output_prefix
            or len(canonical_source_plan_digests) != 1
            or not isinstance(factorial_arm_binding, Mapping)
        ):
            raise ValueError("attempt5_streaming_checkpoint_authority_invalid")
        streaming_checkpoint_authority = {
            "schema": (
                "gtos.replay_acceleration.streaming_checkpoint_authority.v1"
            ),
            "output_prefix": output_prefix,
            "run_identity_root_sha256": identity_root_sha256,
            "source_plan_digest_sha256": canonical_source_plan_digests[0],
            "arm_fingerprint_sha256": str(
                factorial_arm_binding["arm_fingerprint_sha256"]
            ),
            "shared_execution_contract_sha256": str(
                shared_execution_contract[
                    "shared_execution_contract_digest_sha256"
                ]
            ),
            "accelerated_code_config_authority_root_sha256": stable_sha256(
                {
                    "code_authority": shared_execution_contract[
                        "code_authority"
                    ],
                    "config_file_hashes": shared_execution_contract[
                        "config_file_hashes"
                    ],
                }
            ),
        }

    atomic_write_json(
        outputs["partial_summary"],
        json_safe(
            {
                **runtime_preflight_payload,
                "generated_at_utc": utc_now(),
                "status": "source_authority_preflight_complete_replay_not_entered",
                "canonical_source_authority_plans": (
                    canonical_source_authority_plans
                ),
                "source_authority_preflight_checkpoints": (
                    source_authority_preflight_checkpoints
                ),
                "b7_5_contract_binding": b7_5_contract_binding,
                "partial_summary_semantics": (
                    "runtime_and_source_authority_preflight_only_"
                    "run_campaign_not_entered"
                ),
            }
        ),
    )

    if prepared_day_pack_build_only:
        core = {
            "schema": (
                "gtos.replay_acceleration.prepared_day_pack_build_only.v1"
            ),
            "status": "PREPARED_DAY_PACK_BUILD_ONLY_COMPLETE",
            "prepared_day_pack_enabled": True,
            "prepared_day_pack_build_only": True,
            "prepared_day_pack_build_receipts": (
                prepared_day_pack_build_receipts
            ),
            "preparation_source_emission_reset": (
                preparation_source_emission_reset
            ),
            "canonical_source_authority_plans": (
                canonical_source_authority_plans
            ),
            "source_authority_preflight_checkpoints": (
                source_authority_preflight_checkpoints
            ),
            "canonical_source_ledger": {
                "path": str(outputs["source"]),
                "rows": int(ledger_write_row_counts["source"]),
                "bytes": outputs["source"].stat().st_size,
                "sha256": file_sha256(outputs["source"]),
            },
            "chunk_plan": [
                {"split": split, "days": list(chunk_days)}
                for split, chunk_days in chunk_plan
            ],
            "shared_execution_contract": shared_execution_contract,
            "source_acceleration_authority": (
                bound_source_acceleration_authority(
                    args,
                    source_accelerator,
                )
                if source_accelerator is not None
                else None
            ),
            "bound_tick_source_authority": bound_tick_source_contract,
            "bound_tick_diagnostic_authority": (
                bound_tick_diagnostic_contract
            ),
            "factorial_arm_binding_used_only_to_construct_full_reducer_config": (
                factorial_arm_binding is not None
            ),
            "policy_execution_entered": False,
            "broker_live_authority": False,
            "broker_mutation_enabled": False,
            "economic_values_exposed": False,
        }
        receipt = {
            **core,
            "receipt_root_sha256": stable_sha256(core),
        }
        receipt_path = (
            Path(args.output_dir)
            / "PREPARED_DAY_PACK_BUILD_ONLY_RECEIPT.json"
        )
        atomic_write_json(receipt_path, receipt)
        return receipt

    for profile in args.profiles:
        config = profile_configs[str(profile)]
        risk_profile_binding = shared_execution_contract[
            "exact_risk_profile_bindings"
        ][str(profile)]
        profile_exact_cache = CampaignExactCache.from_config(
            config,
            expected_risk_profile_sha256=risk_profile_binding["sha256"],
        )
        broker = SimulatedBroker()
        profile_broker = broker
        profile_account = broker.account
        order_sequence = 0
        for split, chunk_days in chunk_plan:
            if not chunk_days:
                continue
            if streaming_archive is not None:
                capacity = streaming_archive.require_day_capacity(
                    min_transient_headroom_bytes=ATTEMPT5_STREAMING_DAY_TRANSIENT_HEADROOM_BYTES,
                    settle_timeout_seconds=300,
                    settle_poll_seconds=5,
                    on_advisory_miss=lambda: reclaim_runtime_memory_pressure(
                        resolver
                    ),
                )
                streaming_capacity_checks.append(
                    {
                        **capacity,
                        "phase": "before_policy_day",
                        "day": chunk_days[0],
                    }
                )
            chunk_id = f"{profile}:{split}:{chunk_days[0]}:{chunk_days[-1]}"
            starting_order_sequence = order_sequence
            source_authority_days = tuple(days_by_split.get(split, ()))
            sources = resolve_sources_for_scope(
                tuple(chunk_days),
                source_authority_days,
            )
            source_plan = build_exact_source_authority_plan(
                sources=sources,
                source_authority_days=tuple(chunk_days),
            )
            canonical_scope = source_authority_scope(source_authority_days)
            source_plan_key = (
                f"{split}:{canonical_scope.get('scope_id') or ''}"
            )
            canonical_source_plan = canonical_source_authority_plans.get(
                source_plan_key
            )
            if canonical_source_plan is None:
                raise ValueError(
                    "canonical_source_authority_plan_missing_for_chunk:"
                    f"{chunk_id}:{source_plan_key}"
                )
            source_authority_checkpoint = source_authority_chunk_checkpoint(
                profile=profile,
                split=split,
                execution_days=chunk_days,
                source_plan=source_plan,
                canonical_plan=canonical_source_plan,
            )
            if not all(
                (
                    source_authority_checkpoint.get("source_plan_valid") is True,
                    source_authority_checkpoint.get(
                        "execution_days_subset_of_source_authority"
                    )
                    is True,
                    source_authority_checkpoint.get(
                        "source_plan_matches_canonical"
                    )
                    is True,
                )
            ):
                raise ValueError(
                    "source_authority_chunk_invariance_failed:"
                    f"{chunk_id}:{json.dumps(source_authority_checkpoint, sort_keys=True)}"
                )
            source_authority_checkpoints.append(source_authority_checkpoint)
            ledger_write_row_counts["source"] += append_jsonl(
                outputs["source"],
                [
                    {
                        **dict(row),
                        **selection_sizing_factorial_ledger_fields(
                            factorial_arm_binding
                        ),
                    }
                    for row in resolver.drain_source_rows()
                ],
            )
            campaign = CampaignConfig(
                name=f"{output_prefix.lower()}_{profile}",
                phase=f"{profile}_{split}",
                days=tuple(chunk_days),
                pending_expiry_minutes=REPAIRED_PENDING_EXPIRY_MINUTES,
                use_repaired_pending_expiry=True,
                profile=profile,
                partial_be_runner=True,
                max_candidates_per_symbol_window=args.max_candidates_per_symbol_window,
                run_smoke_subset=args.smoke_subset,
                materialize_packet_sidecars=not args.omit_packet_sidecar_ledger,
                materialize_semantic_diagnostics=True,
                candidate_ledger_packet_max_bytes=args.candidate_ledger_packet_max_bytes,
                scorecard_ledger_packet_max_bytes=args.scorecard_ledger_packet_max_bytes,
                compact_scorecard_symbol_risk_config=args.compact_scorecard_symbol_risk_config,
                scorecard_probe_row_limit=args.scorecard_probe_row_limit,
            )
            prepared_day_pack = None
            if prepared_day_pack_root is not None:
                prepared_pack_path = (
                    prepared_day_pack_root
                    / str(split)
                    / f"{chunk_days[0]}_{chunk_days[-1]}"
                )
                expected_pack_root = expected_prepared_day_pack_roots[
                    (
                        str(split),
                        str(chunk_days[0]),
                        str(chunk_days[-1]),
                    )
                ]
                prepared_day_pack = PreparedDayPackReader(
                    prepared_pack_path,
                    expected_pack_root_sha256=expected_pack_root,
                )
                prepared_day_pack_checkpoints.append(
                    {
                        "profile": str(profile),
                        "split": str(split),
                        "days": list(chunk_days),
                        "path": str(prepared_pack_path),
                        "pack_root_sha256": (
                            prepared_day_pack.pack_root_sha256
                        ),
                        "expected_pack_root_sha256": expected_pack_root,
                        "external_root_authenticated": (
                            prepared_day_pack.external_root_authenticated
                        ),
                        "status": "authenticated_before_chronological_reducer",
                        "broker_mutation_enabled": False,
                        "live_authority_touched": False,
                    }
                )
            compact_event_sink = (
                ReplayCompactEventSink(
                    root=(
                        Path(args.output_dir)
                        / "compact-event-shards"
                        / str(profile)
                        / str(split)
                        / f"{chunk_days[0]}_{chunk_days[-1]}"
                    ),
                    max_shard_bytes=compact_event_max_shard_bytes,
                    defer_seal_to_caller=True,
                    row_projectors={
                        **(
                            {
                                "decision": lambda row: (
                                    compact_asof_decision_rows((row,))[0]
                                )
                            }
                            if compact_decision_ledger
                            else {}
                        ),
                        **(
                            {
                                "missed": (
                                    project_compact_missed_transport_row
                                )
                            }
                            if compact_missed_ledger
                            else {}
                        ),
                    },
                    retained_row_projectors=(
                        {
                            "candidate": (
                                timewarp_loop.post_window_candidate_retention_row
                            )
                        }
                        if candidate_relational_mode
                        else None
                    ),
                )
                if compact_event_sink_enabled
                else None
            )
            if gc.isenabled():
                gc.disable()
            economic_hot_path_started = time.perf_counter()
            try:
                result = run_campaign(
                    campaign=campaign,
                    config=config,
                    sources=sources,
                    broker=broker,
                    starting_order_sequence=order_sequence,
                    campaign_exact_cache=profile_exact_cache,
                    compact_event_sink=compact_event_sink,
                    prepared_day_pack=prepared_day_pack,
                    stage_profiler=getattr(args, "replay_stage_profiler", None),
                )
            except BaseException:
                if compact_event_sink is not None:
                    compact_event_sink.abort()
                raise
            economic_hot_path_seconds = round(
                time.perf_counter() - economic_hot_path_started,
                9,
            )
            proof_finalization_started = time.perf_counter()
            with timewarp_loop._replay_profile_stage(
                getattr(args, "replay_stage_profiler", None),
                "archive_seal",
            ):
                if compact_event_sink is not None:
                    _seal_compact_event_sink_after_economic_hot_path(
                        result=result,
                        compact_event_sink=compact_event_sink,
                    )
            semantic_order_prebindings = (
                prebind_semantic_order_preimages_to_final_producer_rows(
                    preimage_rows=result["ledgers"].get(
                        "semantic_order_preimage", ()
                    ),
                    producer_order_rows=result["ledgers"].get("order", ()),
                )
            )
            order_sequence = int(result.get("selected_order_sequence") or order_sequence)
            broker_object_continuity = bool(
                broker is profile_broker and result.get("broker") is profile_broker
            )
            account_object_continuity = bool(
                broker.account is profile_account
                and getattr(result.get("broker"), "account", None)
                is profile_account
            )
            selected_order_sequence_monotonic = (
                order_sequence >= starting_order_sequence
            )
            accumulator.add_result(
                profile=profile,
                split=split,
                days=tuple(chunk_days),
                result=result,
            )
            summary = summarize_campaign(result, phase=campaign.phase)
            progress_row = {
                "row_type": "chunk_progress",
                "profile": profile,
                "split": split,
                "chunk_id": chunk_id,
                "start_day": chunk_days[0],
                "end_day": chunk_days[-1],
                "day_count": len(chunk_days),
                "summary": summary,
                "selected_order_sequence": order_sequence,
                "broker_boundary": result["broker"].mutation_boundary(),
                "symbols_with_sources": sorted(sources),
                "source_authority": source_authority_checkpoint,
                "live_broker_authority": False,
                "broker_mutation_enabled": False,
                "final_selection_claim": False,
                "evidence_class": SIM_EVIDENCE_CLASS,
                "campaign_exact_cache": profile_exact_cache.audit(config),
                "economic_hot_path_seconds": economic_hot_path_seconds,
            }
            progress_rows.append(progress_row)
            ledgers = result["ledgers"]
            if candidate_relational_mode:
                relational_audit, relational_identity_sets = (
                    _candidate_terminal_reconciliation(
                        candidate_rows=ledgers.get("candidate", ()),
                        missed_rows=ledgers.get("missed", ()),
                        order_rows=ledgers.get("order", ()),
                        trade_rows=ledgers.get("trade", ()),
                        exit_rows=ledgers.get("exit", ()),
                        account_rows=ledgers.get("account", ()),
                    )
                )
                relational_audit.update(
                    {
                        "profile": profile,
                        "split": split,
                        "chunk_id": chunk_id,
                    }
                )
                candidate_relational_chunk_audits.append(relational_audit)
                progress_row["candidate_relational_materialization"] = (
                    relational_audit
                )
                if relational_audit.get("exact") is not True:
                    raise ValueError(
                        "candidate_relational_materialization_mismatch:"
                        f"{chunk_id}:{json.dumps(relational_audit, sort_keys=True)}"
                    )
                candidate_relational_candidate_rows += int(
                    relational_audit.get("candidate_rows") or 0
                )
                candidate_keys = relational_identity_sets["candidate"]
                terminal_keys = relational_identity_sets["terminal"]
                missing_counts = relational_audit.get("missing_instance_key_counts")
                missing_counts = (
                    missing_counts if isinstance(missing_counts, Mapping) else {}
                )
                candidate_relational_candidate_keys.update(
                    f"{profile}@@{key}" for key in candidate_keys
                )
                candidate_relational_terminal_keys.update(
                    f"{profile}@@{key}" for key in terminal_keys
                )
                candidate_relational_missing_keys.update(
                    {
                        role: int(missing_counts.get(role) or 0)
                        for role in ("candidate", "missed", "order", "trade", "exit")
                    }
                )
                disposition_counts = relational_audit.get(
                    "terminal_disposition_counts"
                )
                if isinstance(disposition_counts, Mapping):
                    candidate_relational_disposition_counts.update(
                        {
                            role: int(disposition_counts.get(role) or 0)
                            for role in ("missed", "trade", "terminal_unfilled")
                        }
                    )
                del candidate_keys
                del terminal_keys
            decision_rows_to_write: Iterable[Mapping[str, Any]] = (
                iter_compact_asof_decision_rows(ledgers.get("asof", ()))
                if compact_decision_ledger
                else ledgers.get("asof", ())
            )
            scorecard_rows_to_write: Iterable[Mapping[str, Any]] = (
                iter_compact_scorecard_rows(ledgers.get("scorecard", ()))
                if compact_scorecard_ledger
                else ledgers.get("scorecard", ())
            )
            if compact_decision_ledger:
                decision_rows_to_write = iter_counted_compact_projection_rows(
                    decision_rows_to_write,
                    role="decision",
                    counts=compact_projection_counts,
                )
            if compact_scorecard_ledger:
                scorecard_rows_to_write = iter_counted_compact_projection_rows(
                    scorecard_rows_to_write,
                    role="scorecard",
                    counts=compact_projection_counts,
                )
            ledger_write_row_counts["decision"] += append_jsonl(
                outputs["decision"],
                iter_annotated_rows(
                    decision_rows_to_write,
                    profile=profile,
                    split=split,
                    chunk_id=chunk_id,
                    row_type="asof_decision",
                    factorial_arm_binding=factorial_arm_binding,
                ),
            )
            if not args.omit_candidate_ledger:
                ledger_write_row_counts["candidate"] += append_jsonl(
                    outputs["candidate"],
                    annotate_rows(
                        ledgers.get("candidate", ()),
                        profile=profile,
                        split=split,
                        chunk_id=chunk_id,
                    row_type="candidate",
                    factorial_arm_binding=factorial_arm_binding,
                    ),
                )
            elif not omit_candidate_index_ledger:
                ledger_write_row_counts["candidate_index"] += append_jsonl(
                    outputs["candidate_index"],
                    iter_annotated_rows(
                        iter_compact_candidate_index_rows(
                            ledgers.get("candidate", ())
                        ),
                        profile=profile,
                        split=split,
                        chunk_id=chunk_id,
                    row_type="candidate_index",
                    factorial_arm_binding=factorial_arm_binding,
                    ),
                )
            producer_order_rows = list(ledgers.get("order", ()))
            order_rows_to_write = annotate_rows(
                producer_order_rows,
                profile=profile,
                split=split,
                chunk_id=chunk_id,
                row_type="simulated_order",
                factorial_arm_binding=factorial_arm_binding,
            )
            semantic_order_preimage_rows_to_write = (
                bind_semantic_order_preimages_to_persisted_rows(
                    preimage_rows=ledgers.get("semantic_order_preimage", ()),
                    prebindings=semantic_order_prebindings,
                    producer_order_rows=producer_order_rows,
                    persisted_order_rows=order_rows_to_write,
                    persisted_order_stream_offset=ledger_write_row_counts["order"],
                )
            )
            semantic_ledger_write_row_counts[
                "semantic_candidate"
            ] += append_jsonl(
                semantic_outputs["semantic_candidate"],
                ledgers.get("semantic_candidate", ()),
            )
            semantic_ledger_write_row_counts[
                "semantic_state_checkpoint"
            ] += append_jsonl(
                semantic_outputs["semantic_state_checkpoint"],
                ledgers.get("semantic_state_checkpoint", ()),
            )
            semantic_ledger_write_row_counts[
                "semantic_order_preimage"
            ] += append_jsonl(
                semantic_outputs["semantic_order_preimage"],
                semantic_order_preimage_rows_to_write,
            )
            ledger_write_row_counts["scorecard"] += append_jsonl(
                outputs["scorecard"],
                iter_annotated_rows(
                    scorecard_rows_to_write,
                    profile=profile,
                    split=split,
                    chunk_id=chunk_id,
                    row_type="scheduler_scorecard",
                    factorial_arm_binding=factorial_arm_binding,
                ),
            )
            ledger_write_row_counts["order"] += append_jsonl(
                outputs["order"],
                order_rows_to_write,
            )
            ledger_write_row_counts["trade"] += append_jsonl(
                outputs["trade"],
                annotate_rows(
                    ledgers.get("trade", ()),
                    profile=profile,
                    split=split,
                    chunk_id=chunk_id,
                    row_type="simulated_trade",
                    factorial_arm_binding=factorial_arm_binding,
                ),
            )
            ledger_write_row_counts["oracle"] += append_jsonl(
                outputs["oracle"],
                annotate_rows(
                    ledgers.get("oracle", ()),
                    profile=profile,
                    split=split,
                    chunk_id=chunk_id,
                    row_type="ordered_path_oracle",
                    factorial_arm_binding=factorial_arm_binding,
                ),
            )
            ledger_write_row_counts["missed"] += append_jsonl(
                outputs["missed"],
                iter_annotated_rows(
                    (
                        iter_compact_missed_opportunity_rows(
                            ledgers.get("missed", ())
                        )
                        if compact_missed_ledger
                        else ledgers.get("missed", ())
                    ),
                    profile=profile,
                    split=split,
                    chunk_id=chunk_id,
                    row_type="missed_opportunity",
                    factorial_arm_binding=factorial_arm_binding,
                ),
            )
            if not args.omit_packet_sidecar_ledger:
                ledger_write_row_counts["packet_sidecar"] += append_jsonl(
                    outputs["packet_sidecar"],
                    annotate_rows(
                        ledgers.get("packet_sidecar", ()),
                        profile=profile,
                        split=split,
                        chunk_id=chunk_id,
                    row_type="packet_sidecar",
                    factorial_arm_binding=factorial_arm_binding,
                    ),
                )
            ledger_write_row_counts["bucket"] += append_jsonl(
                outputs["bucket"],
                annotate_rows(
                    headline_authority_bucket_rows(
                        [
                            *ledgers.get("daily", ()),
                            *ledgers.get("rollup", ()),
                        ],
                        ledgers.get("trade", ()),
                    ),
                    profile=profile,
                    split=split,
                    chunk_id=chunk_id,
                    row_type="bucket",
                    factorial_arm_binding=factorial_arm_binding,
                ),
            )
            proof_finalization_seconds = round(
                time.perf_counter() - proof_finalization_started,
                9,
            )
            compact_event_authority = result.get("compact_event_sink_authority")
            compact_event_checkpoint = {
                "enabled": compact_event_sink is not None,
                "profile": profile,
                "split": split,
                "chunk_id": chunk_id,
                "economic_hot_path_seconds": economic_hot_path_seconds,
                "proof_finalization_seconds": proof_finalization_seconds,
                "authority": (
                    {
                        **dict(compact_event_authority),
                        "root": str(compact_event_sink.root),
                    }
                    if compact_event_sink is not None
                    and isinstance(compact_event_authority, Mapping)
                    else None
                ),
            }
            compact_event_sink_checkpoints.append(compact_event_checkpoint)
            progress_row["proof_finalization_seconds"] = proof_finalization_seconds
            progress_row["compact_event_sink"] = compact_event_checkpoint
            completed_profile_days = completed_semantic_days_by_profile[
                str(profile)
            ]
            if (
                completed_profile_days
                and chunk_days[0] <= completed_profile_days[-1]
            ) or any(day in completed_profile_days for day in chunk_days):
                raise ValueError(
                    "semantic_source_completed_day_sequence_invalid"
                )
            completed_profile_days.extend(chunk_days)
            partial_stats = accumulator.serializable_stats()
            partial_comparisons = comparison_rows(partial_stats)
            partial_payload = {
                        "schema": (
                            "gtos.final_moonshot.broad_live_as_if_replay_harness."
                            "partial_summary.v1"
                        ),
                        "generated_at_utc": utc_now(),
                        "route_id": ROUTE.name,
                        "output_prefix": output_prefix,
                        "status": "partial_in_progress_not_final_proof",
                        "last_completed_chunk_id": chunk_id,
                        "last_completed_profile": profile,
                        "last_completed_split": split,
                        "last_completed_start_day": chunk_days[0],
                        "last_completed_end_day": chunk_days[-1],
                        "profiles_requested": list(args.profiles),
                        "candidate_ledger_omitted": args.omit_candidate_ledger,
                        "candidate_index_ledger_omitted": (
                            omit_candidate_index_ledger
                        ),
                        "missed_ledger_compacted": compact_missed_ledger,
                        "decision_ledger_compacted": compact_decision_ledger,
                        "scorecard_ledger_compacted": compact_scorecard_ledger,
                        "compact_event_sink_enabled": bool(
                            compact_event_sink_enabled
                        ),
                        "compact_event_sink_checkpoints": list(
                            compact_event_sink_checkpoints
                        ),
                        "packet_sidecar_ledger_omitted": (
                            args.omit_packet_sidecar_ledger
                        ),
                        "progress_rows": progress_rows,
                        "ledger_write_row_counts_so_far": dict(
                            sorted(ledger_write_row_counts.items())
                        ),
                        "split_profile_stats": partial_stats,
                        "comparison_rows": partial_comparisons,
                        "candidate_rows_materialized_so_far": (
                            materialized_candidate_rows_from_stats(partial_stats)
                        ),
                        "candidate_relational_materialization": (
                            candidate_relational_summary()
                        ),
                        "capacity_safe_chunk_execution_required": True,
                        "capacity_safe_chunk_execution_contract": (
                            capacity_safe_chunk_execution_contract(
                                configured_chunk_size=args.chunk_size,
                                planned_chunk_count=planned_chunk_count,
                                completed_chunk_count=(
                                    len(chunk_capacity_checkpoints) + 1
                                ),
                                gc_between_chunks=gc_between_chunks,
                                checkpoints=chunk_capacity_checkpoints,
                                current_chunk_cleanup_pending=True,
                            )
                        ),
                        "source_authority_chunk_invariance_required": True,
                        "source_authority_preflight_checkpoints": (
                            source_authority_preflight_checkpoints
                        ),
                        "source_authority_chunk_invariance_contract": (
                            source_authority_chunk_invariance_contract(
                                planned_chunk_count=planned_chunk_count,
                                completed_chunk_count=len(
                                    source_authority_checkpoints
                                ),
                                checkpoints=source_authority_checkpoints,
                                canonical_plans=canonical_source_authority_plans,
                            )
                        ),
                        "gc_between_chunks": gc_between_chunks,
                        "automatic_gc_disabled_during_replay_chunks": True,
                        "automatic_gc_reenabled_between_chunks": False,
                        "explicit_gc_collection_after_result_release": (
                            gc_between_chunks
                        ),
                        "caller_automatic_gc_state_restored_after_harness": True,
                        "ultimate_package_runtime_input_contract": (
                            runtime_input_contract
                        ),
                        "runtime_evidence_contract": runtime_evidence_contract,
                        "source_acceleration_authority": (
                            bound_source_acceleration_authority(
                                args,
                                source_accelerator,
                            )
                            if source_accelerator is not None
                            else None
                        ),
                        "real_s0r0_parity_gate": accepted_real_parity_gate,
                        "streaming_proof_archive": (
                            streaming_archive.authority()
                            if streaming_archive is not None
                            else None
                        ),
                        "streaming_capacity_checks": list(
                            streaming_capacity_checks
                        ),
                        "shared_execution_contract": (
                            shared_execution_contract
                        ),
                        "attempt5_execution_identity": (
                            dict(attempt5_execution_identity)
                            if isinstance(
                                attempt5_execution_identity,
                                Mapping,
                            )
                            else None
                        ),
                        "b7_5_contract_binding": b7_5_contract_binding,
                        **(
                            {
                                "b7_5_selection_sizing_factorial_arm_binding": (
                                    factorial_arm_binding
                                )
                            }
                            if factorial_arm_binding is not None
                            else {}
                        ),
                        "compact_projection_counts_so_far": dict(
                            sorted(compact_projection_counts.items())
                        ),
                        "source_universe_rows_indexed_so_far": (
                            ledger_write_row_counts["source"]
                        ),
                        "ledger_file_bytes_flushed_before_partial_summary": {
                            key: (
                                path.stat().st_size
                                if path.exists()
                                else None
                            )
                            for key, path in outputs.items()
                            if key != "partial_summary"
                        },
                        "live_broker_authority": False,
                        "broker_mutation_enabled": False,
                        "final_selection_claim": False,
                        "package_new_entry_authority_payload_contract": (
                            PACKAGE_NEW_ENTRY_AUTHORITY_IMMUTABLE_PAYLOAD_CONTRACT
                        ),
                        "package_new_entry_authority_payload_required_for_signed_executable_rows": True,
                        "partial_summary_semantics": (
                            "salvage_checkpoint_only_final_summary_required_for_completed_run"
                        ),
                        "evidence_class": SIM_EVIDENCE_CLASS,
                    }
            atomic_write_json(
                outputs["partial_summary"],
                json_safe(partial_payload),
            )
            del decision_rows_to_write
            del scorecard_rows_to_write
            del producer_order_rows
            del order_rows_to_write
            del semantic_order_preimage_rows_to_write
            del semantic_order_prebindings
            del ledgers
            del result
            del sources
            source_cache_release = resolver.release_completed_chunk_caches(
                chunk_days,
                source_authority_days=source_authority_days,
            )
            automatic_gc_enabled_before_explicit_collection = gc.isenabled()
            gc_collected_objects = gc.collect() if gc_between_chunks else None
            if gc_between_chunks:
                darwin_allocator_pressure_relief()
            automatic_gc_enabled_after_explicit_collection = gc.isenabled()
            chunk_capacity_checkpoints.append(
                {
                    "chunk_id": chunk_id,
                    "profile": profile,
                    "split": split,
                    "start_day": chunk_days[0],
                    "end_day": chunk_days[-1],
                    "day_count": len(chunk_days),
                    "cleanup_status": "completed",
                    "broker_object_continuity": broker_object_continuity,
                    "account_object_continuity": account_object_continuity,
                    "starting_order_sequence": starting_order_sequence,
                    "ending_order_sequence": order_sequence,
                    "selected_order_sequence_monotonic": (
                        selected_order_sequence_monotonic
                    ),
                    "source_cache_release": source_cache_release,
                    "source_authority": source_authority_checkpoint,
                    "explicit_gc_requested": gc_between_chunks,
                    "explicit_gc_completed": gc_between_chunks,
                    "gc_collected_objects": gc_collected_objects,
                    "automatic_gc_enabled_before_explicit_collection": (
                        automatic_gc_enabled_before_explicit_collection
                    ),
                    "automatic_gc_enabled_after_explicit_collection": (
                        automatic_gc_enabled_after_explicit_collection
                    ),
                }
            )
            partial_payload["generated_at_utc"] = utc_now()
            partial_payload["capacity_safe_chunk_execution_contract"] = (
                capacity_safe_chunk_execution_contract(
                    configured_chunk_size=args.chunk_size,
                    planned_chunk_count=planned_chunk_count,
                    completed_chunk_count=len(chunk_capacity_checkpoints),
                    gc_between_chunks=gc_between_chunks,
                    checkpoints=chunk_capacity_checkpoints,
                )
            )
            partial_payload["source_authority_chunk_invariance_contract"] = (
                source_authority_chunk_invariance_contract(
                    planned_chunk_count=planned_chunk_count,
                    completed_chunk_count=len(source_authority_checkpoints),
                    checkpoints=source_authority_checkpoints,
                    canonical_plans=canonical_source_authority_plans,
                )
            )
            partial_payload["partial_summary_semantics"] = (
                "salvage_checkpoint_with_completed_capacity_cleanup_only_"
                "final_summary_required_for_completed_run"
            )
            atomic_write_json(
                outputs["partial_summary"],
                json_safe(partial_payload),
            )
            if (
                physical_reference_requested
                and chunk_days[-1] == physical_reference_checkpoint_day
            ):
                if (
                    streaming_archive is not None
                    or source_accelerator is not None
                    or physical_source_reference is None
                    or len(chunk_capacity_checkpoints) != len(
                        completed_semantic_days_by_profile[str(profile)]
                    )
                    or len(chunk_capacity_checkpoints) != 7
                    or len(source_authority_checkpoints) != 7
                ):
                    raise ValueError(
                        "physical_reference_post_cleanup_checkpoint_invalid"
                    )
                args.physical_source_reference_authority = (
                    physical_source_reference.authority()
                )
                return partial_payload
            if (
                task2_semantic_checkpoint_day
                and chunk_days[-1] == task2_semantic_checkpoint_day
            ):
                completed_days = completed_semantic_days_by_profile.get(
                    str(profile), []
                )
                if (
                    streaming_archive is not None
                    or physical_source_reference is not None
                    or source_accelerator is None
                    or len(chunk_capacity_checkpoints) != 2
                    or len(source_authority_checkpoints) != 2
                    or completed_days != ["2026-01-01", "2026-01-02"]
                    or len(progress_rows) != 2
                    or canonical_source_plan_digests
                    != [str(expected_source_plan_digest)]
                ):
                    raise ValueError(
                        "task2_semantic_post_cleanup_checkpoint_invalid"
                    )
                checkpoint_authority = {
                    "schema": (
                        "gtos.replay_acceleration."
                        "task2_semantic_checkpoint.v1"
                    ),
                    "status": "JAN1_2_POST_CLEANUP_CHECKPOINT_COMPLETE",
                    "acceptance_authorized": False,
                    "start_day": "2026-01-01",
                    "end_day": "2026-01-02",
                    "completed_day_count": 2,
                    "canonical_source_authority_start_day": (
                        ATTEMPT5_START_DAY
                    ),
                    "canonical_source_authority_end_day": (
                        ATTEMPT5_CONTRACT_END_DAY
                    ),
                    "canonical_source_plan_digest_sha256": (
                        canonical_source_plan_digests[0]
                    ),
                    "capacity_checkpoint_count": len(
                        chunk_capacity_checkpoints
                    ),
                    "source_checkpoint_count": len(
                        source_authority_checkpoints
                    ),
                    "broker_live_authority": False,
                    "broker_mutation_enabled": False,
                }
                checkpoint_authority["checkpoint_root_sha256"] = (
                    stable_sha256(checkpoint_authority)
                )
                partial_payload["task2_semantic_checkpoint"] = (
                    checkpoint_authority
                )
                partial_payload["generated_at_utc"] = utc_now()
                atomic_write_json(
                    outputs["partial_summary"],
                    json_safe(partial_payload),
                )
                args.task2_semantic_checkpoint_authority = (
                    checkpoint_authority
                )
                return partial_payload
            if streaming_archive is not None:
                if streaming_checkpoint_authority is None:
                    raise ValueError(
                        "attempt5_streaming_checkpoint_authority_missing"
                    )
                archive_shard = streaming_archive.seal_and_reclaim(
                    start_day=chunk_days[0],
                    end_day=chunk_days[-1],
                    pre_archive_partial_summary_path=outputs[
                        "partial_summary"
                    ],
                    checkpoint_authority=streaming_checkpoint_authority,
                    settle_timeout_seconds=300,
                    settle_poll_seconds=5,
                    on_advisory_miss=lambda: reclaim_runtime_memory_pressure(
                        resolver
                    ),
                )
                streaming_archive_shards.append(
                    {
                        "segment_id": archive_shard["segment_id"],
                        "start_day": archive_shard["start_day"],
                        "end_day": archive_shard["end_day"],
                        "manifest_root_sha256": archive_shard[
                            "manifest_root_sha256"
                        ],
                        "receipt_root_sha256": archive_shard[
                            "receipt_root_sha256"
                        ],
                        "verified_before_reclaim": True,
                        "raw_derivatives_reclaimed": True,
                    }
                )
                post_archive_capacity = streaming_archive.require_day_capacity(
                    min_transient_headroom_bytes=0,
                    settle_timeout_seconds=300,
                    settle_poll_seconds=5,
                    on_advisory_miss=lambda: reclaim_runtime_memory_pressure(
                        resolver
                    ),
                )
                streaming_capacity_checks.append(
                    {
                        **post_archive_capacity,
                        "phase": "after_verified_reclaim",
                        "day": chunk_days[-1],
                    }
                )
                partial_payload["streaming_proof_archive"] = (
                    streaming_archive.authority()
                )
                partial_payload["streaming_proof_archive_shards"] = list(
                    streaming_archive_shards
                )
                partial_payload["streaming_capacity_checks"] = list(
                    streaming_capacity_checks
                )
                partial_payload["generated_at_utc"] = utc_now()
                atomic_write_json(
                    outputs["partial_summary"],
                    json_safe(partial_payload),
                )
            if (
                parity_gate_requested
                and accepted_real_parity_gate is None
                and chunk_days[-1] == parity_gate_day
            ):
                request_path = Path(parity_request_path)
                report_path = Path(parity_report_path)
                receipt_path = Path(parity_receipt_path)
                snapshot_path = request_path.with_name(
                    "ACCELERATED_COMPARED_PARTIAL_SUMMARY.json"
                )
                if streaming_archive is None:
                    raise ValueError(
                        "semantic_source_requires_verified_streaming_archive"
                    )
                parity_archive_verification_receipt = (
                    Path(streaming_archive_root)
                    / "PARITY_CAMPAIGN_VERIFY_RECEIPT.json"
                )
                streaming_archive.independent_verify_campaign(
                    parity_archive_verification_receipt
                )
                write_attempt5_semantic_source_manifest(
                    outputs=source_outputs,
                    campaign_days_by_profile={
                        requested_profile: tuple(completed_days)
                        for requested_profile, completed_days in (
                            completed_semantic_days_by_profile.items()
                        )
                        if completed_days
                    },
                    archive_manifest_path=(
                        streaming_archive.campaign_manifest_path
                    ),
                    archive_verification_receipt_path=(
                        parity_archive_verification_receipt
                    ),
                    arm_id=str(factorial_arm_binding["arm_id"]),
                )
                if contract_split is None:
                    raise ValueError("real_parity_contract_split_missing")
                gate_request = build_gate_request(
                    output_prefix=output_prefix,
                    outputs=outputs,
                    ledger_row_counts=ledger_write_row_counts,
                    completed_through_day=chunk_days[-1],
                    source_plan_digest_sha256=canonical_source_plan_digests[0],
                    shared_execution_contract_sha256=str(
                        shared_execution_contract[
                            "shared_execution_contract_digest_sha256"
                        ]
                    ),
                    economic_execution_contract_sha256=str(
                        contract_split[
                            "economic_execution_contract_digest_sha256"
                        ]
                    ),
                    accelerator_implementation_authority_root_sha256=str(
                        contract_split[
                            "accelerator_implementation_authority_root_sha256"
                        ]
                    ),
                    arm_id=str(factorial_arm_binding["arm_id"]),
                    arm_fingerprint_sha256=str(
                        factorial_arm_binding["arm_fingerprint_sha256"]
                    ),
                    prospective_golden_authority=(
                        args.prospective_golden_authority
                    ),
                    partial_summary_snapshot=snapshot_path,
                    archived_result_surfaces=(
                        streaming_archive.gate_surface_contracts()
                        if streaming_archive is not None
                        else None
                    ),
                )
                atomic_write_gate_json(request_path, gate_request)
                parity_receipt = wait_for_parity_receipt(
                    receipt_path=receipt_path,
                    report_path=report_path,
                    gate_request=gate_request,
                    timeout_seconds=int(args.parity_wait_timeout_seconds),
                )
                accepted_real_parity_gate = {
                    "schema": (
                        "gtos.replay_acceleration.real_s0r0_"
                        "accepted_parity_gate.v1"
                    ),
                    "status": "EXACT_FULL_RESULT_PARITY_ACCEPTED",
                    "completed_through_day": chunk_days[-1],
                    "gate_request_root_sha256": gate_request[
                        "gate_request_root_sha256"
                    ],
                    "receipt_root_sha256": parity_receipt[
                        "receipt_root_sha256"
                    ],
                    "parity_report_root_sha256": parity_receipt[
                        "parity_report_root_sha256"
                    ],
                    "same_process_state_preserved": True,
                    "continuation_authorized": bool(
                        parity_receipt.get(
                            "same_state_continuation_through_2026_01_31_authorized"
                        )
                    ),
                    "other_arms_launched": False,
                    "broker_live_authority": False,
                    "economic_values_exposed": False,
                }
                partial_payload["real_s0r0_parity_gate"] = (
                    accepted_real_parity_gate
                )
                partial_payload["generated_at_utc"] = utc_now()
                if bool(getattr(args, "stop_after_parity_gate", False)):
                    partial_payload["status"] = (
                        "bounded_accelerated_s0r0_parity_gate_accepted"
                    )
                    partial_payload["selected_day_count"] = 7
                    partial_payload["profiles"] = list(args.profiles)
                    partial_payload["artifacts"] = {
                        key: str(path) for key, path in outputs.items()
                    }
                    partial_payload["same_state_continuation_entered"] = False
                    partial_payload["bounded_measurement_only"] = True
                    partial_payload["campaign_exact_cache_profiles"] = [
                        {
                            "profile": str(profile),
                            **profile_exact_cache.audit(config),
                        }
                    ]
                    atomic_write_json(
                        outputs["partial_summary"],
                        json_safe(partial_payload),
                    )
                    profile_exact_cache.close()
                    return partial_payload
                if accepted_real_parity_gate["continuation_authorized"] is not True:
                    raise ValueError(
                        "real_parity_receipt_continuation_not_authorized"
                    )
                partial_payload["same_state_continuation_entered"] = True
                atomic_write_json(
                    outputs["partial_summary"],
                    json_safe(partial_payload),
                )
        campaign_exact_cache_profiles.append(
            {
                "profile": str(profile),
                **profile_exact_cache.audit(config),
            }
        )
        profile_exact_cache.close()
    ledger_write_row_counts["source"] += append_jsonl(
        outputs["source"],
        [
            {
                **dict(row),
                **selection_sizing_factorial_ledger_fields(
                    factorial_arm_binding
                ),
            }
            for row in resolver.drain_source_rows()
        ],
    )
    stats = accumulator.serializable_stats()
    comparisons = comparison_rows(stats)
    finalizer_evidence = risk_finalizer_evidence(stats)
    candidate_rows_materialized = materialized_candidate_rows_from_stats(stats)
    candidate_relational_contract = candidate_relational_summary()
    capacity_safe_contract = capacity_safe_chunk_execution_contract(
        configured_chunk_size=args.chunk_size,
        planned_chunk_count=planned_chunk_count,
        completed_chunk_count=len(chunk_capacity_checkpoints),
        gc_between_chunks=gc_between_chunks,
        checkpoints=chunk_capacity_checkpoints,
    )
    source_authority_contract = source_authority_chunk_invariance_contract(
        planned_chunk_count=planned_chunk_count,
        completed_chunk_count=len(source_authority_checkpoints),
        checkpoints=source_authority_checkpoints,
        canonical_plans=canonical_source_authority_plans,
    )
    if capacity_safe_contract.get("valid") is not True:
        raise ValueError(
            "capacity_safe_chunk_execution_contract_failed:"
            f"{json.dumps(capacity_safe_contract, sort_keys=True)}"
        )
    if source_authority_contract.get("valid") is not True:
        raise ValueError(
            "source_authority_chunk_invariance_contract_failed:"
            f"{json.dumps(source_authority_contract, sort_keys=True)}"
        )
    if candidate_relational_mode:
        if candidate_relational_contract.get("exact") is not True:
            raise ValueError(
                "candidate_relational_materialization_final_mismatch:"
                f"{json.dumps(candidate_relational_contract, sort_keys=True)}"
            )
        if (
            int(candidate_relational_contract.get("candidate_rows") or 0)
            != candidate_rows_materialized
        ):
            raise ValueError(
                "candidate_relational_materialized_summary_count_mismatch:"
                f"relational={candidate_relational_contract.get('candidate_rows')}:"
                f"stats={candidate_rows_materialized}"
            )
    ledger_write_row_counts["comparison"] += append_jsonl(
        outputs["comparison"],
        [
            {
                **dict(row),
                **selection_sizing_factorial_ledger_fields(
                    factorial_arm_binding
                ),
            }
            for row in comparisons
        ],
    )
    streaming_campaign_verification: dict[str, Any] | None = None
    if streaming_archive is not None:
        if (
            accepted_real_parity_gate is None
            or len(streaming_archive_shards) != 31
            or streaming_archive_shards[0]["start_day"] != "2026-01-01"
            or streaming_archive_shards[0]["end_day"] != "2026-01-01"
            or streaming_archive_shards[-1]["end_day"] != "2026-01-31"
        ):
            raise ValueError("streaming_proof_archive_campaign_incomplete")
        final_archive_verification_receipt = (
            Path(streaming_archive_root)
            / "FINAL_CAMPAIGN_VERIFY_RECEIPT.json"
        )
        streaming_campaign_verification = (
            streaming_archive.independent_verify_campaign(
                final_archive_verification_receipt
            )
        )
        last_streaming_current_summary_contract = (
            current_summary_v2_contract_for_streaming_archive(
                outputs,
                streaming_archive.campaign_manifest_path,
            )
        )
        write_attempt5_semantic_source_manifest(
            outputs=source_outputs,
            campaign_days_by_profile={
                profile: tuple(completed_days)
                for profile, completed_days in (
                    completed_semantic_days_by_profile.items()
                )
                if completed_days
            },
            archive_manifest_path=streaming_archive.campaign_manifest_path,
            archive_verification_receipt_path=(
                final_archive_verification_receipt
            ),
            arm_id=str(factorial_arm_binding["arm_id"]),
        )
    artifact_paths: dict[str, str | None] = {
        key: str(path) for key, path in outputs.items()
    }
    artifact_materialization_status = {
        key: "materialized" for key in outputs
    }
    if streaming_archive is not None:
        for role in ("decision", "scorecard", "missed"):
            artifact_paths[role] = str(streaming_archive.campaign_manifest_path)
            artifact_materialization_status[role] = (
                "materialized_reconstructable_verified_zstd_day_shards"
            )
    if args.omit_candidate_ledger:
        artifact_paths["candidate"] = None
        artifact_materialization_status["candidate"] = (
            "omitted_by_compact_broad_replay_request"
        )
        if omit_candidate_index_ledger:
            artifact_paths["candidate_index"] = None
            artifact_materialization_status["candidate_index"] = (
                "omitted_by_exact_relational_missed_order_trade_materialization"
            )
        else:
            artifact_materialization_status["candidate_index"] = (
                "materialized_compact_candidate_index_for_omitted_candidate_ledger"
            )
    else:
        artifact_paths["candidate_index"] = None
        artifact_materialization_status["candidate_index"] = (
            "not_requested_full_candidate_ledger_materialized"
        )
    if args.omit_packet_sidecar_ledger:
        artifact_paths["packet_sidecar"] = None
        artifact_materialization_status["packet_sidecar"] = (
            "omitted_by_compact_broad_replay_request"
        )
    if compact_missed_ledger:
        artifact_materialization_status["missed"] = (
            "materialized_compact_missed_opportunity_ledger"
        )
    terminal_execution_materialized = bool(
        ledger_write_row_counts["order"]
        or ledger_write_row_counts["trade"]
        or ledger_write_row_counts["oracle"]
    )
    candidate_rows_written = (
        ledger_write_row_counts["candidate_index"]
        if args.omit_candidate_ledger
        else ledger_write_row_counts["candidate"]
    )
    if terminal_execution_materialized:
        summary_status = "broad_live_as_if_replay_materialized_broker_live_closed"
    elif candidate_rows_materialized == 0:
        summary_status = "broad_live_as_if_replay_zero_candidates_no_terminal_execution_broker_live_closed"
    else:
        summary_status = "broad_live_as_if_replay_candidate_replay_no_terminal_execution_broker_live_closed"
    active_symbols = active_replay_symbol_universe(requested_symbols)
    current_summary_contract = (
        last_streaming_current_summary_contract
        if streaming_archive is not None
        else current_summary_v2_contract_for_outputs(outputs)
    )
    factorial_risk_lifecycle = selection_sizing_factorial_risk_lifecycle_audit(
        order_path=outputs["order"],
        trade_path=outputs["trade"],
        factorial_arm_binding=factorial_arm_binding,
    )
    if (
        factorial_arm_binding is not None
        and factorial_risk_lifecycle.get("valid") is not True
    ):
        raise ValueError(
            "selection_sizing_factorial_risk_lifecycle_invalid:"
            + "|".join(
                str(row.get("reason") or "unknown")
                for row in factorial_risk_lifecycle.get("failures", [])[:12]
                if isinstance(row, Mapping)
            )
        )
    summary = {
        **current_summary_contract,
        "physical_trade_summary_serialized_ledger_parity_contract": (
            physical_trade_summary_serialized_ledger_parity_contract()
        ),
        "generated_at_utc": utc_now(),
        "route_id": ROUTE.name,
        "output_prefix": output_prefix,
        "status": summary_status,
        "coverage_status": coverage_status,
        "bounded_smoke": bounded_smoke,
        "bounded_symbol_scope_smoke": bounded_symbol_scope_smoke,
        "bounded_replay_interpretation": (
            "targeted_repair_proof_slice_not_full_reservoir_conversion_claim"
            if bounded_smoke
            else "full_configured_available_date_range"
        ),
        "run_mode": "smoke_decision_subset" if args.smoke_subset else "full_decision_grid",
        "symbol_universe_mode": (
            "targeted_symbol_subset" if requested_symbols else "full_24_symbol_surface"
        ),
        "requested_symbols": list(active_symbols),
        "requested_symbol_count": len(active_symbols),
        "active_replay_symbol_universe": list(active_symbols),
        "active_replay_symbol_count": len(active_symbols),
        "configured_symbol_universe": list(GTOS_24_SYMBOL_SURFACE),
        "configured_symbol_count": len(GTOS_24_SYMBOL_SURFACE),
        "symbol_universe_semantics": (
            "legacy_symbol_universe_fields_report_configured_24_symbol_surface; "
            "active_replay_symbol_universe reports the requested replay denominator"
        ),
        "tick_source_mode": "skipped_by_explicit_repair_smoke_flag"
        if skip_tick_source
        else "resolved_when_available",
        "profile_count": len(args.profiles),
        "profiles": list(args.profiles),
        "campaign_exact_cache_profiles": campaign_exact_cache_profiles,
        "max_candidates_per_symbol_window": int(
            args.max_candidates_per_symbol_window or 0
        ),
        "candidate_generation_authority": (
            "uncapped_full_authority"
            if int(args.max_candidates_per_symbol_window or 0) <= 0
            else "score_ranked_cap_explicitly_audited"
        ),
        "symbol_universe": list(GTOS_24_SYMBOL_SURFACE),
        "symbol_count": len(GTOS_24_SYMBOL_SURFACE),
        "date_start": args.start,
        "date_end": args.end,
        "engineering_stop_after_day": engineering_stop_after_day or None,
        "engineering_stop_is_acceptance_gate": False,
        "split_ranges": [
            {"split": split, "start": start, "end": end}
            for split, start, end in SPLIT_RANGES
        ],
        "days_by_split": {split: list(days) for split, days in days_by_split.items()},
        "selected_day_count": selected_day_count,
        "full_available_configured_day_count": full_available_day_count,
        "full_available_days_by_split": {
            split: {"day_count": len(days), "start": days[0] if days else None, "end": days[-1] if days else None}
            for split, days in full_available_days_by_split.items()
        },
        "repair_seed_window": {
            "start": REPAIR_SEED_START,
            "end": REPAIR_SEED_END,
            "interpretation": "in_sample_loss_bucket_repair_seed_not_final_system_proof",
        },
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "order_send_attempts": {
            profile: 0 for profile in args.profiles
        },
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_formula_authority": False,
        "candidate_cost_r_formula_use": "fallback_diagnostic_only",
        "cost_authority_sources": {
            "pretrade_cost_engine": "src/components/broker_net_cost_engine.py",
            "broker_symbol_specs": "config/profiles/operator_profile.yaml",
            "measured_tick_spread_floors": "src/components/ultimate_book/admission.py",
            "selected_cell_cost_gate_status": "commission_included_in_selected_cell_risk",
            "fallback_diagnostic": "timewarp_candidate_cost_r_proxy",
        },
        "guarded_policy": {
            "policy_id": ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID,
            "rule_count": len(ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES),
            "live_broker_authority": False,
        },
        "packet_sidecar_ledger_omitted": args.omit_packet_sidecar_ledger,
        "candidate_ledger_omitted": args.omit_candidate_ledger,
        "candidate_index_ledger_omitted": omit_candidate_index_ledger,
        "missed_ledger_compacted": compact_missed_ledger,
        "decision_ledger_compacted": compact_decision_ledger,
        "scorecard_ledger_compacted": compact_scorecard_ledger,
        "compact_event_sink_enabled": compact_event_sink_enabled,
        "compact_event_sink_checkpoints": compact_event_sink_checkpoints,
        "prepared_day_pack_enabled": prepared_day_pack_root is not None,
        "prepared_day_pack_build_receipts": prepared_day_pack_build_receipts,
        "prepared_day_pack_checkpoints": prepared_day_pack_checkpoints,
        "ultimate_package_runtime_input_contract": runtime_input_contract,
        "runtime_evidence_contract": runtime_evidence_contract,
        "source_acceleration_authority": (
            bound_source_acceleration_authority(
                args,
                source_accelerator,
            )
            if source_accelerator is not None
            else None
        ),
        "real_s0r0_parity_gate": accepted_real_parity_gate,
        "streaming_proof_archive": (
            streaming_archive.authority()
            if streaming_archive is not None
            else None
        ),
        "streaming_proof_archive_shards": streaming_archive_shards,
        "streaming_capacity_checks": streaming_capacity_checks,
        "streaming_proof_archive_campaign_verification": (
            streaming_campaign_verification
        ),
        "shared_execution_contract": shared_execution_contract,
        "b7_5_contract_binding": b7_5_contract_binding,
        "b7_5_selection_sizing_factorial_risk_lifecycle": (
            factorial_risk_lifecycle
        ),
        **(
            {
                "b7_5_selection_sizing_factorial_arm_binding": (
                    factorial_arm_binding
                )
            }
            if factorial_arm_binding is not None
            else {}
        ),
        "capacity_safe_chunk_execution_required": True,
        "capacity_safe_chunk_execution_contract": capacity_safe_contract,
        "source_authority_chunk_invariance_required": True,
        "source_authority_preflight_checkpoints": (
            source_authority_preflight_checkpoints
        ),
        "source_authority_chunk_invariance_contract": (
            source_authority_contract
        ),
        "broad_replay_compact_ledgers": {
            "candidate_ledger_packet_max_bytes": args.candidate_ledger_packet_max_bytes,
            "scorecard_ledger_packet_max_bytes": args.scorecard_ledger_packet_max_bytes,
            "compact_scorecard_symbol_risk_config": args.compact_scorecard_symbol_risk_config,
            "scorecard_probe_row_limit": args.scorecard_probe_row_limit,
            "packet_sidecars_materialized_in_run_campaign": not args.omit_packet_sidecar_ledger,
            "candidate_rows_materialized_in_summary_stats": True,
            "candidate_rows_written_to_jsonl": not args.omit_candidate_ledger,
            "candidate_index_rows_written_to_jsonl": (
                args.omit_candidate_ledger
                and not omit_candidate_index_ledger
            ),
            "candidate_index_rows_omitted_from_jsonl": (
                args.omit_candidate_ledger
                and omit_candidate_index_ledger
            ),
            "candidate_relational_materialization": (
                candidate_relational_contract
            ),
            "decision_rows_compacted_in_jsonl": compact_decision_ledger,
            "decision_projection_schema": (
                COMPACT_DECISION_PROJECTION_SCHEMA
                if compact_decision_ledger
                else None
            ),
            "scorecard_rows_compacted_in_jsonl": compact_scorecard_ledger,
            "scorecard_projection_schema": (
                COMPACT_SCORECARD_PROJECTION_SCHEMA
                if compact_scorecard_ledger
                else None
            ),
            "compact_projection_counts": dict(
                sorted(compact_projection_counts.items())
            ),
            "missed_opportunity_rows_materialized_in_summary_stats": True,
            "missed_opportunity_rows_compacted_in_jsonl": compact_missed_ledger,
            "compact_event_sink_roles": (
                ["decision", "missed"] if compact_event_sink_enabled else []
            ),
            "compact_event_sink_max_shard_bytes": int(
                compact_event_max_shard_bytes
            ),
            "compact_event_sink_checkpoints": compact_event_sink_checkpoints,
            "prepared_day_pack_enabled": prepared_day_pack_root is not None,
            "prepared_day_pack_build_receipts": (
                prepared_day_pack_build_receipts
            ),
            "prepared_day_pack_checkpoints": prepared_day_pack_checkpoints,
        },
        "gc_between_chunks": gc_between_chunks,
        "automatic_gc_disabled_during_replay_chunks": True,
        "automatic_gc_reenabled_between_chunks": False,
        "explicit_gc_collection_after_result_release": gc_between_chunks,
        "caller_automatic_gc_state_restored_after_harness": True,
        "source_universe_rows": int(ledger_write_row_counts["source"]),
        "candidate_rows": int(candidate_rows_materialized),
        "candidate_rows_written": int(ledger_write_row_counts["candidate"]),
        "candidate_index_rows_written": int(
            ledger_write_row_counts["candidate_index"]
        ),
        "candidate_rows_serialized_in_dedicated_candidate_ledger": int(
            candidate_rows_written
        ),
        "candidate_relational_materialization": candidate_relational_contract,
        "scorecard_rows": int(ledger_write_row_counts["scorecard"]),
        "order_rows": int(ledger_write_row_counts["order"]),
        "trade_rows": int(ledger_write_row_counts["trade"]),
        "oracle_rows": int(ledger_write_row_counts["oracle"]),
        "missed_opportunity_rows": int(ledger_write_row_counts["missed"]),
        "bucket_rows": int(ledger_write_row_counts["bucket"]),
        "packet_sidecar_rows": int(ledger_write_row_counts["packet_sidecar"]),
        "comparison_ledger_rows": int(ledger_write_row_counts["comparison"]),
        "terminal_execution_materialized": terminal_execution_materialized,
        "terminal_execution_materialization_status": (
            "terminal_execution_ledgers_materialized"
            if terminal_execution_materialized
            else "candidate_replay_no_terminal_execution_materialized"
        ),
        "ledger_write_row_counts": dict(sorted(ledger_write_row_counts.items())),
        "progress_rows": progress_rows,
        "split_profile_stats": stats,
        "comparison_rows": comparisons,
        "risk_admitted_scheduler_finalizer_evidence": finalizer_evidence,
        "artifacts": artifact_paths,
        "artifact_materialization_status": artifact_materialization_status,
        "evidence_class": SIM_EVIDENCE_CLASS,
        "source_evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
        "outcome_evidence_class": OUTCOME_EVIDENCE_CLASS,
    }
    atomic_write_json(outputs["summary"], json_safe(summary))
    return summary


def run_replay_engine(args: argparse.Namespace) -> dict[str, Any]:
    """Execute the canonical replay engine with caller GC state preserved."""

    gc_enabled_on_entry = gc.isenabled()
    try:
        with timewarp_loop.own_campaign_exact_caches():
            return _run_typed_sparse_attempt5(args)
    finally:
        if gc_enabled_on_entry and not gc.isenabled():
            gc.enable()
        elif not gc_enabled_on_entry and gc.isenabled():
            gc.disable()


def run_typed_sparse_attempt5(args: argparse.Namespace) -> dict[str, Any]:
    """Bind and execute the strict attempt-5 typed/sparse route."""

    require_attempt5_execution_authority(args)
    bind_attempt5_finalizer_conflict_key_order()
    namespace = configure_output_namespace(Path(args.output_dir))
    tick_sparse_window_start, tick_sparse_window_end = (
        attempt5_effective_execution_tick_sparse_cache_window(args)
    )
    identity_core = {
        "schema": "gtos.replay_acceleration.attempt5_typed_sparse_identity.v1",
        "status": "ATTEMPT5_TYPED_SPARSE_S0R0_JAN1_7_BOUND",
        "runner_path": str(Path(__file__).resolve()),
        "runner_sha256": file_sha256(Path(__file__).resolve()),
        "output_namespace": str(namespace),
        "output_prefix": str(args.output_prefix),
        "start_day": str(args.start),
        "parity_day": str(args.parity_gate_after_day),
        "contract_end_day": str(args.end),
        "arm_id": str(args.arm_id),
        "expected_arm_fingerprint_sha256": str(
            args.expected_arm_fingerprint_sha256
        ),
        "expected_source_bundle_root_sha256": str(
            args.expected_source_bundle_root_sha256
        ),
        "source_bundle_consumer_rebind_authority": copy.deepcopy(
            dict(args.bound_source_bundle_consumer_rebind_authority)
        ),
        "expected_source_plan_digest_sha256": str(
            args.expected_source_plan_digest_sha256
        ),
        "expected_shared_execution_contract_sha256": str(
            args.expected_shared_execution_contract_sha256
        ),
        "prospective_golden_authority": dict(
            args.prospective_golden_authority
        ),
        "tick_source_manifest": str(
            _resolved_argument_path(args.tick_source_manifest)
        ),
        "expected_tick_source_manifest_sha256": str(
            args.expected_tick_source_manifest_sha256
        ),
        "tick_sparse_cache": {
            "schema": SPARSE_TICK_CACHE_SCHEMA,
            "root": str(Path(args.tick_sparse_cache_root).resolve()),
            "window_start_utc": iso(tick_sparse_window_start),
            "window_end_utc": iso(tick_sparse_window_end),
            "source_plan_or_replay_semantics_changed": False,
        },
        "tick_diagnostic_manifest_bindings": [
            {
                "path": str(_resolved_argument_path(path)),
                "sha256": str(expected_sha256),
            }
            for path, expected_sha256 in zip(
                args.tick_diagnostic_manifests or (),
                args.expected_tick_diagnostic_manifest_sha256s or (),
            )
        ],
        "source_prewarm_workers": int(args.source_prewarm_workers),
        "legacy_replay_route_invoked": False,
        "policy_execution_entered": False,
        "other_arms_launched": False,
        "broker_live_authority": False,
        "broker_mutation_enabled": False,
        "economic_values_exposed": False,
    }
    identity = {
        **identity_core,
        "identity_root_sha256": stable_sha256(identity_core),
    }
    args.attempt5_execution_identity = identity
    atomic_write_json(
        namespace / "ATTEMPT5_TYPED_SPARSE_EXECUTION_IDENTITY.json",
        identity,
    )

    return run_replay_engine(args)


def completed_partial_checkpoint_declares_finalizable_cleanup(
    partial: Mapping[str, Any],
) -> bool:
    """Return whether a checkpoint proves every planned chunk finished cleanup."""

    capacity = partial.get("capacity_safe_chunk_execution_contract")
    source = partial.get("source_authority_chunk_invariance_contract")
    if not isinstance(capacity, Mapping) or not isinstance(source, Mapping):
        return False
    progress_count = len(partial.get("progress_rows") or [])
    capacity_planned = int(capacity.get("planned_chunk_count") or 0)
    capacity_completed = int(capacity.get("completed_chunk_count") or 0)
    source_planned = int(source.get("planned_chunk_count") or 0)
    source_completed = int(source.get("completed_chunk_count") or 0)
    return bool(
        partial.get("status") == "partial_in_progress_not_final_proof"
        and partial.get("partial_summary_semantics")
        == (
            "salvage_checkpoint_with_completed_capacity_cleanup_only_"
            "final_summary_required_for_completed_run"
        )
        and capacity.get("valid") is True
        and capacity.get("status") == "complete_capacity_safe_chunk_execution"
        and source.get("valid") is True
        and source.get("status") == "complete_source_authority_chunk_invariance"
        and source.get("current_chunk_pending") is False
        and capacity_planned > 0
        and capacity_planned == capacity_completed == progress_count
        and source_planned == source_completed == progress_count
    )


def completed_run_flushed_ledger_integrity_contract(
    outputs: Mapping[str, Path],
    partial: Mapping[str, Any],
) -> dict[str, Any]:
    """Certify flushed JSONL bytes, rows, hashes, and parseable boundaries."""

    ledger_keys = (
        "source",
        "decision",
        "candidate",
        "candidate_index",
        "scorecard",
        "order",
        "trade",
        "oracle",
        "missed",
        "bucket",
        "packet_sidecar",
    )
    fully_parse_keys = {
        "source",
        "decision",
        "oracle",
        "bucket",
    }
    expected_counts = partial.get("ledger_write_row_counts_so_far")
    expected_counts = expected_counts if isinstance(expected_counts, Mapping) else {}
    expected_bytes = partial.get("ledger_file_bytes_flushed_before_partial_summary")
    expected_bytes = expected_bytes if isinstance(expected_bytes, Mapping) else {}
    failures: list[str] = []
    rows: list[dict[str, Any]] = []

    for key in ledger_keys:
        path = outputs.get(key)
        expected_row_count = int(expected_counts.get(key) or 0)
        expected_size_raw = expected_bytes.get(key)
        expected_size = (
            int(expected_size_raw) if expected_size_raw is not None else None
        )
        row: dict[str, Any] = {
            "ledger": key,
            "path": str(path) if path is not None else None,
            "expected_rows": expected_row_count,
            "expected_bytes": expected_size,
            "full_json_parse_required_here": key in fully_parse_keys,
        }
        if path is None:
            row.update({"status": "path_missing", "valid": False})
            failures.append(f"{key}:path_missing")
            rows.append(row)
            continue
        if expected_size is None:
            unexpected_size = path.stat().st_size if path.exists() else 0
            valid = expected_row_count == 0 and unexpected_size == 0
            row.update(
                {
                    "actual_rows": 0,
                    "actual_bytes": unexpected_size,
                    "sha256": None,
                    "status": (
                        "intentionally_not_materialized"
                        if valid
                        else "unexpected_materialization"
                    ),
                    "valid": valid,
                }
            )
            if not valid:
                failures.append(
                    f"{key}:unexpected_materialization:"
                    f"rows={expected_row_count}:bytes={unexpected_size}"
                )
            rows.append(row)
            continue
        if not path.exists():
            row.update({"status": "file_missing", "valid": False})
            failures.append(f"{key}:file_missing")
            rows.append(row)
            continue

        digest = hashlib.sha256()
        actual_rows = 0
        actual_bytes = 0
        blank_rows = 0
        unterminated_rows = 0
        invalid_json_rows = 0
        non_mapping_rows = 0
        first_raw: bytes | None = None
        last_raw: bytes | None = None
        with path.open("rb") as handle:
            for actual_rows, raw_line in enumerate(handle, start=1):
                digest.update(raw_line)
                actual_bytes += len(raw_line)
                if first_raw is None:
                    first_raw = raw_line
                last_raw = raw_line
                if not raw_line.strip():
                    blank_rows += 1
                if not raw_line.endswith(b"\n"):
                    unterminated_rows += 1
                if key in fully_parse_keys:
                    try:
                        parsed = json.loads(raw_line)
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        invalid_json_rows += 1
                    else:
                        if not isinstance(parsed, Mapping):
                            non_mapping_rows += 1

        boundary_invalid_json_rows = 0
        boundary_non_mapping_rows = 0
        if key not in fully_parse_keys:
            boundary_lines = [first_raw]
            if last_raw is not None and last_raw is not first_raw:
                boundary_lines.append(last_raw)
            for raw_line in boundary_lines:
                if raw_line is None:
                    continue
                try:
                    parsed = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    boundary_invalid_json_rows += 1
                else:
                    if not isinstance(parsed, Mapping):
                        boundary_non_mapping_rows += 1

        actual_size = path.stat().st_size
        valid = bool(
            actual_rows == expected_row_count
            and actual_bytes == actual_size == expected_size
            and blank_rows == 0
            and unterminated_rows == 0
            and invalid_json_rows == 0
            and non_mapping_rows == 0
            and boundary_invalid_json_rows == 0
            and boundary_non_mapping_rows == 0
        )
        row.update(
            {
                "actual_rows": actual_rows,
                "actual_bytes": actual_bytes,
                "sha256": digest.hexdigest(),
                "blank_rows": blank_rows,
                "unterminated_rows": unterminated_rows,
                "invalid_json_rows": invalid_json_rows,
                "non_mapping_rows": non_mapping_rows,
                "boundary_invalid_json_rows": boundary_invalid_json_rows,
                "boundary_non_mapping_rows": boundary_non_mapping_rows,
                "status": "exact_flushed_jsonl" if valid else "integrity_mismatch",
                "valid": valid,
            }
        )
        if not valid:
            failures.append(
                f"{key}:integrity_mismatch:expected_rows={expected_row_count}:"
                f"actual_rows={actual_rows}:expected_bytes={expected_size}:"
                f"actual_bytes={actual_size}:blank={blank_rows}:"
                f"unterminated={unterminated_rows}:invalid_json={invalid_json_rows}:"
                f"non_mapping={non_mapping_rows}:"
                f"boundary_invalid_json={boundary_invalid_json_rows}:"
                f"boundary_non_mapping={boundary_non_mapping_rows}"
            )
        rows.append(row)

    valid = not failures
    return {
        "schema": "gtos.final_moonshot.broad_replay.completed_run_ledger_integrity.v1",
        "status": (
            "exact_flushed_ledgers_certified"
            if valid
            else "flushed_ledger_integrity_failed"
        ),
        "valid": valid,
        "failures": failures,
        "ledger_count": len(rows),
        "ledgers": rows,
    }


def existing_completed_run_recovery_source(
    outputs: Mapping[str, Path],
    partial: Mapping[str, Any],
) -> tuple[dict[str, Any], Path | None]:
    """Load a recoverable tombstone or certify a summary-less interruption."""

    summary_path = outputs["summary"]
    if not summary_path.exists() or not summary_path.read_text(encoding="utf-8").strip():
        if not completed_partial_checkpoint_declares_finalizable_cleanup(partial):
            raise ValueError(
                "existing_run_summary_missing_without_completed_cleanup_checkpoint"
            )
        return (
            {
                "status": "summary_missing_after_external_interruption",
                "failure_stage": "post_chunk_final_aggregation_interrupted",
                "failure_message": (
                    "all planned chunks and cleanup checkpoints completed, but the "
                    "process ended before the final summary was materialized"
                ),
            },
            None,
        )

    loaded = json.loads(summary_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("existing_run_recovery_source_summary_not_mapping")
    status = loaded.get("status")
    failure_stage = loaded.get("failure_stage")
    if status == "failed_partial_not_final_proof" and failure_stage in {
        "final_current_summary_v2_certification",
        "final_existing_completed_run_certification",
    }:
        backup = ROUTE / f"{partial['output_prefix']}_FAILED_CERTIFICATION_SUMMARY.json"
        return loaded, backup
    if status == "interrupted_partial_not_final_proof":
        if not completed_partial_checkpoint_declares_finalizable_cleanup(partial):
            raise ValueError(
                "existing_run_interrupted_summary_without_completed_cleanup_checkpoint"
            )
        backup = ROUTE / f"{partial['output_prefix']}_INTERRUPTED_SUMMARY.json"
        return loaded, backup
    if status in {
        "broad_live_as_if_replay_materialized_broker_live_closed",
        "broad_live_as_if_replay_candidate_replay_no_terminal_execution_broker_live_closed",
        "broad_live_as_if_replay_zero_candidates_no_terminal_execution_broker_live_closed",
    }:
        if not completed_partial_checkpoint_declares_finalizable_cleanup(partial):
            raise ValueError(
                "existing_run_completed_summary_without_completed_cleanup_checkpoint"
            )
        backup = ROUTE / (
            f"{partial['output_prefix']}_PRE_PHYSICAL_SUMMARY_PARITY_"
            "RECONCILIATION_SUMMARY.json"
        )
        return loaded, backup
    raise ValueError("existing_run_not_recoverable_final_certification_failure")


def certify_existing_run_contract_binding(
    partial: Mapping[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Bind recovery to the exact execution and source plans used by the run."""

    binding = partial.get("b7_5_contract_binding")
    binding = binding if isinstance(binding, Mapping) else {}
    shared = partial.get("shared_execution_contract")
    shared = shared if isinstance(shared, Mapping) else {}
    actual_shared = shared.get("shared_execution_contract_digest_sha256") or binding.get(
        "actual_shared_execution_contract_digest_sha256"
    )
    actual_source = list(binding.get("actual_source_plan_digests_sha256") or [])
    expected_shared = getattr(
        args, "expected_shared_execution_contract_sha256", None
    )
    expected_source = getattr(args, "expected_source_plan_digest_sha256", None)
    failures: list[str] = []
    if binding.get("required") is True and binding.get("valid") is not True:
        failures.append("stored_b7_5_contract_binding_invalid")
    if expected_shared and actual_shared != expected_shared:
        failures.append(
            "shared_execution_contract_digest_mismatch:"
            f"expected={expected_shared}:actual={actual_shared}"
        )
    if expected_source and actual_source != [expected_source]:
        failures.append(
            "source_plan_digest_mismatch:"
            f"expected={expected_source}:actual={'|'.join(actual_source)}"
        )
    valid = not failures
    contract = {
        "schema": "gtos.final_moonshot.broad_replay.completed_run_recovery_binding.v1",
        "status": "recovery_binding_certified" if valid else "recovery_binding_failed",
        "valid": valid,
        "failures": failures,
        "actual_shared_execution_contract_digest_sha256": actual_shared,
        "actual_source_plan_digests_sha256": actual_source,
        "expected_shared_execution_contract_digest_sha256": expected_shared,
        "expected_source_plan_digest_sha256": expected_source,
    }
    if not valid:
        raise ValueError(
            "existing_run_contract_binding_failed:"
            f"{json.dumps(contract, sort_keys=True)}"
        )
    return contract


def finalize_existing_completed_run(args: argparse.Namespace) -> dict[str, Any]:
    """Certify flushed rows or reconcile a completed summary from those rows."""

    output_prefix = str(args.output_prefix or PREFIX).strip() or PREFIX
    requested_factorial_binding = selection_sizing_factorial_binding_from_args(args)
    outputs = output_paths(output_prefix)
    partial = json.loads(outputs["partial_summary"].read_text(encoding="utf-8"))
    stored_factorial_binding = partial.get(
        "b7_5_selection_sizing_factorial_arm_binding"
    )
    if requested_factorial_binding != stored_factorial_binding:
        raise ValueError(
            "existing_run_selection_sizing_factorial_arm_binding_mismatch"
        )
    recovery_source, recovery_backup = existing_completed_run_recovery_source(
        outputs, partial
    )
    if partial.get("status") != "partial_in_progress_not_final_proof":
        raise ValueError("existing_run_partial_checkpoint_status_invalid")
    if partial.get("output_prefix") != output_prefix:
        raise ValueError("existing_run_partial_checkpoint_prefix_mismatch")

    profiles = tuple(getattr(args, "profiles", ()) or ())
    if list(profiles) != list(partial.get("profiles_requested") or []):
        raise ValueError("existing_run_profile_request_mismatch")
    days_by_split = build_days_by_split(
        args.start,
        args.end,
        max_days=getattr(args, "max_days", None),
    )
    expected_days = {
        (profile, split): set(days)
        for profile in profiles
        for split, days in days_by_split.items()
        if days
    }
    completed_days: dict[tuple[str, str], set[str]] = defaultdict(set)
    for progress in partial.get("progress_rows") or []:
        profile = str(progress.get("profile") or "")
        split = str(progress.get("split") or "")
        start_day = str(progress.get("start_day") or "")
        end_day = str(progress.get("end_day") or "")
        if profile and split and start_day and end_day:
            completed_days[(profile, split)].update(iter_dates(start_day, end_day))
    if completed_days != expected_days:
        raise ValueError("existing_run_completed_chunk_coverage_mismatch")
    capacity_contract = partial.get("capacity_safe_chunk_execution_contract")
    if partial.get("capacity_safe_chunk_execution_required") is True:
        if not isinstance(capacity_contract, Mapping):
            raise ValueError(
                "existing_run_capacity_safe_chunk_execution_contract_missing"
            )
        if capacity_contract.get("valid") is not True:
            raise ValueError(
                "existing_run_capacity_safe_chunk_execution_contract_invalid"
            )
    source_authority_contract = partial.get(
        "source_authority_chunk_invariance_contract"
    )
    if partial.get("source_authority_chunk_invariance_required") is True:
        if not isinstance(source_authority_contract, Mapping):
            raise ValueError(
                "existing_run_source_authority_chunk_invariance_contract_missing"
            )
        if source_authority_contract.get("valid") is not True:
            raise ValueError(
                "existing_run_source_authority_chunk_invariance_contract_invalid"
            )

    recovery_binding = certify_existing_run_contract_binding(partial, args)
    ledger_integrity = completed_run_flushed_ledger_integrity_contract(
        outputs, partial
    )
    if ledger_integrity.get("valid") is not True:
        raise ValueError(
            "existing_run_flushed_ledger_integrity_failed:"
            f"{json.dumps(ledger_integrity, sort_keys=True)}"
        )

    current_summary_contract = current_summary_v2_contract_for_outputs(outputs)
    counts = Counter(
        {
            str(key): int(value or 0)
            for key, value in (
                partial.get("ledger_write_row_counts_so_far") or {}
            ).items()
        }
    )
    stats = reconcile_physical_summary_stats_from_trade_ledger(
        list(partial.get("split_profile_stats") or []),
        outputs["trade"],
    )
    comparisons = comparison_rows(stats)
    if comparisons != list(partial.get("comparison_rows") or []):
        raise ValueError("existing_run_comparison_projection_mismatch")
    finalizer_evidence = risk_finalizer_evidence(stats)
    terminal_execution_materialized = bool(
        counts["order"] or counts["trade"] or counts["oracle"]
    )
    candidate_count_key = (
        "candidate_index" if partial.get("candidate_ledger_omitted") else "candidate"
    )
    candidate_rows = int(
        partial.get("candidate_rows_materialized_so_far")
        or counts[candidate_count_key]
        or 0
    )
    if terminal_execution_materialized:
        status = "broad_live_as_if_replay_materialized_broker_live_closed"
    elif candidate_rows:
        status = (
            "broad_live_as_if_replay_candidate_replay_no_terminal_execution_"
            "broker_live_closed"
        )
    else:
        status = (
            "broad_live_as_if_replay_zero_candidates_no_terminal_execution_"
            "broker_live_closed"
        )

    requested_symbols = requested_replay_symbols(getattr(args, "symbols", None))
    active_symbols = active_replay_symbol_universe(requested_symbols)
    full_available_days_by_split = build_days_by_split(
        DEFAULT_START,
        DEFAULT_END,
        max_days=None,
    )
    selected_day_count = sum(len(days) for days in days_by_split.values())
    full_available_day_count = sum(
        len(days) for days in full_available_days_by_split.values()
    )
    coverage_status = (
        "full_configured_available_date_range"
        if (
            args.start == DEFAULT_START
            and args.end == DEFAULT_END
            and getattr(args, "max_days", None) is None
            and not getattr(args, "smoke_subset", False)
        )
        else "bounded_replay_materialization_not_full_available_universe"
    )
    bounded_smoke = coverage_status != "full_configured_available_date_range"
    artifact_paths = {key: str(path) for key, path in outputs.items()}
    artifact_materialization_status = {key: "materialized" for key in outputs}
    if partial.get("candidate_ledger_omitted"):
        artifact_paths["candidate"] = None
        artifact_materialization_status["candidate"] = (
            "omitted_by_compact_broad_replay_request"
        )
        if partial.get("candidate_index_ledger_omitted"):
            artifact_paths["candidate_index"] = None
            artifact_materialization_status["candidate_index"] = (
                "omitted_by_exact_relational_missed_order_trade_materialization"
            )
    else:
        artifact_paths["candidate_index"] = None
        artifact_materialization_status["candidate_index"] = (
            "not_requested_full_candidate_ledger_materialized"
        )
    if partial.get("packet_sidecar_ledger_omitted"):
        artifact_paths["packet_sidecar"] = None
        artifact_materialization_status["packet_sidecar"] = (
            "omitted_by_compact_broad_replay_request"
        )
    if partial.get("missed_ledger_compacted"):
        artifact_materialization_status["missed"] = (
            "materialized_compact_missed_opportunity_ledger"
        )

    if recovery_backup is not None and not recovery_backup.exists():
        atomic_write_json(recovery_backup, recovery_source)
    comparison_rows_written = atomic_write_jsonl(outputs["comparison"], comparisons)
    if comparison_rows_written != len(comparisons):
        raise ValueError(
            "existing_run_comparison_ledger_write_mismatch:"
            f"expected={len(comparisons)}:actual={comparison_rows_written}"
        )
    ledger_counts = dict(sorted(counts.items()))
    ledger_counts["comparison"] = comparison_rows_written
    factorial_risk_lifecycle = selection_sizing_factorial_risk_lifecycle_audit(
        order_path=outputs["order"],
        trade_path=outputs["trade"],
        factorial_arm_binding=requested_factorial_binding,
    )
    if (
        requested_factorial_binding is not None
        and factorial_risk_lifecycle.get("valid") is not True
    ):
        raise ValueError(
            "existing_run_selection_sizing_factorial_risk_lifecycle_invalid:"
            + "|".join(
                str(row.get("reason") or "unknown")
                for row in factorial_risk_lifecycle.get("failures", [])[:12]
                if isinstance(row, Mapping)
            )
        )
    summary = {
        **partial,
        **current_summary_contract,
        "physical_trade_summary_serialized_ledger_parity_contract": (
            physical_trade_summary_serialized_ledger_parity_contract()
        ),
        "generated_at_utc": utc_now(),
        "status": status,
        "coverage_status": coverage_status,
        "bounded_smoke": bounded_smoke,
        "bounded_symbol_scope_smoke": bool(requested_symbols),
        "bounded_replay_interpretation": (
            "targeted_repair_proof_slice_not_full_reservoir_conversion_claim"
            if bounded_smoke
            else "full_configured_available_date_range"
        ),
        "run_mode": (
            "smoke_decision_subset"
            if getattr(args, "smoke_subset", False)
            else "full_decision_grid"
        ),
        "symbol_universe_mode": (
            "targeted_symbol_subset" if requested_symbols else "full_24_symbol_surface"
        ),
        "requested_symbols": list(active_symbols),
        "requested_symbol_count": len(active_symbols),
        "active_replay_symbol_universe": list(active_symbols),
        "active_replay_symbol_count": len(active_symbols),
        "configured_symbol_universe": list(GTOS_24_SYMBOL_SURFACE),
        "configured_symbol_count": len(GTOS_24_SYMBOL_SURFACE),
        "symbol_universe": list(GTOS_24_SYMBOL_SURFACE),
        "symbol_count": len(GTOS_24_SYMBOL_SURFACE),
        "symbol_universe_semantics": (
            "legacy_symbol_universe_fields_report_configured_24_symbol_surface; "
            "active_replay_symbol_universe reports the requested replay denominator"
        ),
        "tick_source_mode": (
            "skipped_by_explicit_repair_smoke_flag"
            if getattr(args, "skip_tick_source", False)
            else "resolved_when_available"
        ),
        "profile_count": len(profiles),
        "profiles": list(profiles),
        "max_candidates_per_symbol_window": int(
            getattr(args, "max_candidates_per_symbol_window", 0) or 0
        ),
        "candidate_generation_authority": (
            "uncapped_full_authority"
            if int(getattr(args, "max_candidates_per_symbol_window", 0) or 0) <= 0
            else "score_ranked_cap_explicitly_audited"
        ),
        "date_start": args.start,
        "date_end": args.end,
        "split_ranges": [
            {"split": split, "start": start, "end": end}
            for split, start, end in SPLIT_RANGES
        ],
        "days_by_split": {key: list(value) for key, value in days_by_split.items()},
        "selected_day_count": selected_day_count,
        "full_available_configured_day_count": full_available_day_count,
        "full_available_days_by_split": {
            split: {
                "day_count": len(days),
                "start": days[0] if days else None,
                "end": days[-1] if days else None,
            }
            for split, days in full_available_days_by_split.items()
        },
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "order_send_attempts": {profile: 0 for profile in profiles},
        "repair_seed_window": {
            "start": REPAIR_SEED_START,
            "end": REPAIR_SEED_END,
            "interpretation": "in_sample_loss_bucket_repair_seed_not_final_system_proof",
        },
        "cost_authority": "broker_calibrated_replay_cost",
        "candidate_cost_r_formula_authority": False,
        "candidate_cost_r_formula_use": "fallback_diagnostic_only",
        "cost_authority_sources": {
            "pretrade_cost_engine": "src/components/broker_net_cost_engine.py",
            "broker_symbol_specs": "config/profiles/operator_profile.yaml",
            "measured_tick_spread_floors": "src/components/ultimate_book/admission.py",
            "selected_cell_cost_gate_status": "commission_included_in_selected_cell_risk",
            "fallback_diagnostic": "timewarp_candidate_cost_r_proxy",
        },
        "b7_5_selection_sizing_factorial_risk_lifecycle": (
            factorial_risk_lifecycle
        ),
        "guarded_policy": {
            "policy_id": ULTIMATE_REPLAY_LOSS_BUCKET_POLICY_ID,
            "rule_count": len(ULTIMATE_REPLAY_LOSS_BUCKET_GUARD_RULES),
            "live_broker_authority": False,
        },
        "gc_between_chunks": bool(
            partial.get(
                "gc_between_chunks",
                getattr(args, "gc_between_chunks", False),
            )
        ),
        "automatic_gc_disabled_during_replay_chunks": True,
        "automatic_gc_reenabled_between_chunks": bool(
            partial.get("automatic_gc_reenabled_between_chunks", False)
        ),
        "explicit_gc_collection_after_result_release": bool(
            (
                capacity_contract
                if isinstance(capacity_contract, Mapping)
                else {}
            ).get("explicit_gc_after_result_release_enabled")
        ),
        "caller_automatic_gc_state_restored_after_harness": True,
        "capacity_safe_chunk_execution_required": bool(
            partial.get("capacity_safe_chunk_execution_required")
        ),
        "capacity_safe_chunk_execution_contract": capacity_contract,
        "source_authority_chunk_invariance_required": bool(
            partial.get("source_authority_chunk_invariance_required")
        ),
        "source_authority_chunk_invariance_contract": (
            source_authority_contract
        ),
        "candidate_ledger_omitted": bool(
            partial.get("candidate_ledger_omitted")
        ),
        "candidate_index_ledger_omitted": bool(
            partial.get("candidate_index_ledger_omitted")
        ),
        "missed_ledger_compacted": bool(partial.get("missed_ledger_compacted")),
        "decision_ledger_compacted": bool(
            partial.get("decision_ledger_compacted")
        ),
        "scorecard_ledger_compacted": bool(
            partial.get("scorecard_ledger_compacted")
        ),
        "ultimate_package_runtime_input_contract": partial.get(
            "ultimate_package_runtime_input_contract"
        ),
        "packet_sidecar_ledger_omitted": bool(
            partial.get("packet_sidecar_ledger_omitted")
        ),
        "broad_replay_compact_ledgers": {
            "candidate_rows_materialized_in_summary_stats": True,
            "candidate_rows_written_to_jsonl": not bool(
                partial.get("candidate_ledger_omitted")
            ),
            "candidate_index_rows_written_to_jsonl": bool(
                partial.get("candidate_ledger_omitted")
            )
            and not bool(partial.get("candidate_index_ledger_omitted")),
            "candidate_index_rows_omitted_from_jsonl": bool(
                partial.get("candidate_ledger_omitted")
            )
            and bool(partial.get("candidate_index_ledger_omitted")),
            "candidate_relational_materialization": partial.get(
                "candidate_relational_materialization"
            ),
            "decision_rows_compacted_in_jsonl": bool(
                partial.get("decision_ledger_compacted")
            ),
            "decision_projection_schema": (
                COMPACT_DECISION_PROJECTION_SCHEMA
                if partial.get("decision_ledger_compacted")
                else None
            ),
            "scorecard_rows_compacted_in_jsonl": bool(
                partial.get("scorecard_ledger_compacted")
            ),
            "scorecard_projection_schema": (
                COMPACT_SCORECARD_PROJECTION_SCHEMA
                if partial.get("scorecard_ledger_compacted")
                else None
            ),
            "compact_projection_counts": dict(
                partial.get("compact_projection_counts_so_far") or {}
            ),
            "missed_opportunity_rows_materialized_in_summary_stats": True,
            "missed_opportunity_rows_compacted_in_jsonl": bool(
                partial.get("missed_ledger_compacted")
            ),
        },
        "source_universe_rows": counts["source"],
        "candidate_rows": candidate_rows,
        "candidate_rows_written": counts["candidate"],
        "candidate_index_rows_written": counts["candidate_index"],
        "candidate_rows_serialized_in_dedicated_candidate_ledger": counts[
            candidate_count_key
        ],
        "candidate_relational_materialization": partial.get(
            "candidate_relational_materialization"
        ),
        "scorecard_rows": counts["scorecard"],
        "order_rows": counts["order"],
        "trade_rows": counts["trade"],
        "oracle_rows": counts["oracle"],
        "missed_opportunity_rows": counts["missed"],
        "bucket_rows": counts["bucket"],
        "packet_sidecar_rows": counts["packet_sidecar"],
        "comparison_ledger_rows": comparison_rows_written,
        "terminal_execution_materialized": terminal_execution_materialized,
        "terminal_execution_materialization_status": (
            "terminal_execution_ledgers_materialized"
            if terminal_execution_materialized
            else "candidate_replay_no_terminal_execution_materialized"
        ),
        "ledger_write_row_counts": ledger_counts,
        "split_profile_stats": stats,
        "comparison_rows": comparisons,
        "risk_admitted_scheduler_finalizer_evidence": finalizer_evidence,
        "artifacts": artifact_paths,
        "artifact_materialization_status": artifact_materialization_status,
        "completed_run_flushed_ledger_integrity": ledger_integrity,
        "completed_run_recovery_binding": recovery_binding,
        "recovered_completed_run": True,
        "recovery_source_status": recovery_source.get("status"),
        "recovery_source_failure_stage": recovery_source.get("failure_stage"),
        "recovery_source_failure_message": recovery_source.get("failure_message"),
        "recovery_source_summary_present": recovery_backup is not None,
        "recovery_source_summary_backup_path": (
            str(recovery_backup) if recovery_backup is not None else None
        ),
        "recovery_contract": (
            "fully_flushed_chunk_coverage_cleanup_source_invariance_bytes_rows_"
            "hashes_json_boundaries_contract_binding_and_current_summary_v2_"
            "ledger_certification"
        ),
        "evidence_class": SIM_EVIDENCE_CLASS,
        "source_evidence_class": SOURCE_BOUND_EVIDENCE_CLASS,
        "outcome_evidence_class": OUTCOME_EVIDENCE_CLASS,
    }
    atomic_write_json(outputs["summary"], json_safe(summary))
    return summary


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default=DEFAULT_START)
    parser.add_argument("--end", default=DEFAULT_END)
    parser.add_argument("--max-days", type=int, default=None)
    parser.add_argument("--chunk-size", type=int, default=5)
    parser.add_argument(
        "--output-prefix",
        default=PREFIX,
        help="Artifact prefix. Use a distinct value for targeted repair reruns.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Fresh identity-bound namespace below the sealed attempt-5 root.",
    )
    parser.add_argument(
        "--profiles",
        nargs="+",
        choices=PROFILES,
        default=list(PROFILES),
    )
    parser.add_argument("--max-candidates-per-symbol-window", type=int, default=0)
    parser.add_argument("--smoke-subset", action="store_true")
    parser.add_argument(
        "--engineering-stop-after-day",
        default=None,
        help=(
            "Bound an acceleration engineering run after this selected day. "
            "This is not an acceptance or economic-selection checkpoint."
        ),
    )
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=None,
        help=(
            "Optional targeted symbol subset for bounded repair smokes. "
            "Default preserves the full 24-symbol source surface."
        ),
    )
    parser.add_argument(
        "--skip-tick-source",
        action="store_true",
        help=(
            "Skip optional tick-source lookup for targeted repair smokes. "
            "Default broad replay still resolves tick sources when available."
        ),
    )
    parser.add_argument("--use-native-h1", action="store_true")
    parser.add_argument("--omit-candidate-ledger", action="store_true")
    parser.add_argument(
        "--omit-candidate-index-ledger",
        action="store_true",
        help=(
            "When --omit-candidate-ledger is set, also skip the compact "
            "candidate index JSONL. Summary candidate counts and the exact "
            "candidate-instance surface remain materialized through a verified "
            "missed/order/trade relational union for long-window proof mode."
        ),
    )
    parser.add_argument("--omit-packet-sidecar-ledger", action="store_true")
    parser.add_argument("--compact-missed-ledger", action="store_true")
    parser.add_argument(
        "--compact-decision-ledger",
        action="store_true",
        help=(
            "Omit an exact duplicate current-FVG partition from the nested "
            "producer audit while preserving the canonical top-level partition."
        ),
    )
    parser.add_argument(
        "--compact-scorecard-ledger",
        action="store_true",
        help=(
            "Preserve one canonical scheduler option trace and omit only exact "
            "duplicate pre/post-finalizer trace aliases."
        ),
    )
    parser.add_argument(
        "--compact-event-sink",
        action=argparse.BooleanOptionalAction,
        default=False,
        help=(
            "Spool append-only decision and missed producer rows into bounded "
            "authenticated zstd frames during replay, then reconstruct the "
            "legacy proof rows after the economic reducer completes."
        ),
    )
    parser.add_argument(
        "--compact-event-max-shard-bytes",
        type=int,
        default=128 * 1024 * 1024,
    )
    parser.add_argument(
        "--prepared-day-pack-root",
        default=None,
        help=(
            "Read sealed arm-neutral prepared packs from "
            "ROOT/<split>/<first-day>_<last-day> and keep all account, broker, "
            "selection, sizing, and lifecycle state private to this reducer."
        ),
    )
    parser.add_argument(
        "--expected-prepared-day-pack-root",
        dest="expected_prepared_day_pack_roots",
        action="append",
        default=None,
        metavar="SPLIT:FIRST_DAY:LAST_DAY=SHA256",
        help=(
            "Bind one already sealed prepared pack root for each consumed replay "
            "chunk. Required with --prepared-day-pack-root; build-and-consume "
            "routes derive the same binding from their in-process seal receipt."
        ),
    )
    parser.add_argument(
        "--build-prepared-day-pack-root",
        default=None,
        help=(
            "Build one arm-neutral sealed pack per replay chunk before reducers "
            "start, then consume those exact packs in this execution."
        ),
    )
    parser.add_argument(
        "--prepared-pack-encoding-workers",
        type=int,
        choices=(1, 2, 3, 4),
        default=1,
    )
    parser.add_argument(
        "--prepared-pack-target-raw-shard-bytes",
        type=int,
        default=32 * 1024 * 1024,
    )
    parser.add_argument("--candidate-ledger-packet-max-bytes", type=int, default=1024)
    parser.add_argument("--scorecard-ledger-packet-max-bytes", type=int, default=4096)
    parser.add_argument(
        "--compact-scorecard-symbol-risk-config",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--scorecard-probe-row-limit", type=int, default=12)
    parser.add_argument(
        "--gc-between-chunks",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Collect only after each completed chunk's ledgers are flushed, heavy "
            "result references are released, and day-scoped source caches are "
            "evicted. Enabled by default for capacity-safe multi-chunk replay."
        ),
    )
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument(
        "--finalize-existing-prefix",
        action="store_true",
        help=(
            "Certify fully flushed artifacts after final-summary interruption or "
            "reconcile a completed summary from its serialized trade truth."
        ),
    )
    parser.add_argument(
        "--expected-shared-execution-contract-sha256",
        default=None,
        help=(
            "Fail before replay when code/config/runtime/package authority "
            "differs from the replay-free source-window contract."
        ),
    )
    parser.add_argument(
        "--expected-source-plan-digest-sha256",
        default=None,
        help=(
            "Fail before replay when the sole selected split's full-window "
            "source authority differs from the replay-free contract."
        ),
    )
    parser.add_argument(
        "--runtime-evidence-root",
        type=Path,
        default=None,
        help=(
            "Read exact immutable package/runtime evidence from this explicit "
            "repository root without copying or hydrating LFS paths."
        ),
    )
    parser.add_argument(
        "--tick-source-manifest",
        type=Path,
        default=None,
        help=(
            "Exact structural tick-source manifest; attempt 5 binds the accepted "
            "January microstructure authority without scanning a retired repo."
        ),
    )
    parser.add_argument(
        "--expected-tick-source-manifest-sha256",
        default=None,
        help="Fail before replay unless the bound tick manifest is byte-exact.",
    )
    parser.add_argument(
        "--tick-diagnostic-manifest",
        dest="tick_diagnostic_manifests",
        type=Path,
        action="append",
        default=None,
        help=(
            "Exact named outside-window tick manifest used only to preserve "
            "source-gap diagnostics without a retired-repository scan."
        ),
    )
    parser.add_argument(
        "--expected-tick-diagnostic-manifest-sha256",
        dest="expected_tick_diagnostic_manifest_sha256s",
        action="append",
        default=None,
        help="Byte commitment paired with --tick-diagnostic-manifest.",
    )
    parser.add_argument(
        "--source-acceleration-bundle-dir",
        type=Path,
        default=None,
        help="Independently accepted immutable source-bundle directory.",
    )
    parser.add_argument(
        "--source-acceleration-selection",
        type=Path,
        default=None,
        help="Prospective structural source-selection receipt for that bundle.",
    )
    parser.add_argument(
        "--source-bundle-consumer-rebind-authority",
        type=Path,
        default=None,
        help=(
            "Reviewed outcome-unread authority proving the accepted source "
            "bundle is the byte-exact current-consumer successor."
        ),
    )
    parser.add_argument(
        "--expected-source-bundle-consumer-rebind-authority-sha256",
        default=None,
        help="Exact file SHA-256 of the source consumer-rebind authority.",
    )
    parser.add_argument(
        "--expected-source-bundle-consumer-rebind-authority-root-sha256",
        default=None,
        help="Exact self-root of the source consumer-rebind authority.",
    )
    parser.add_argument(
        "--source-acceleration-cache-root",
        type=Path,
        default=None,
        help="Quota-controlled typed normalized partition cache root.",
    )
    parser.add_argument(
        "--tick-sparse-cache-root",
        type=Path,
        default=ATTEMPT5_TICK_SPARSE_CACHE_ROOT,
        help=(
            "Content-addressed immutable day shards for bound tick sources; "
            "queries retain legacy row and lookup semantics."
        ),
    )
    parser.add_argument(
        "--expected-source-bundle-root-sha256",
        default=None,
        help="Fail before replay unless the accepted persisted bundle root matches.",
    )
    parser.add_argument(
        "--source-prewarm-workers",
        type=int,
        choices=tuple(range(1, 9)),
        default=1,
        help=(
            "Legal immutable-preprocessing workers; all complete before the "
            "cross-symbol policy barrier."
        ),
    )
    parser.add_argument(
        "--golden-manifest",
        type=Path,
        required=True,
        help="Prospectively designated exact Jan 1-7 partial-golden manifest.",
    )
    parser.add_argument(
        "--expected-golden-manifest-sha256",
        required=True,
        help="Exact file SHA-256 of the designated partial-golden manifest.",
    )
    parser.add_argument(
        "--expected-golden-manifest-self-root-sha256",
        required=True,
        help="Expected self-root declared by the designated golden manifest.",
    )
    parser.add_argument(
        "--expected-golden-root-sha256",
        required=True,
        help="Expected sealed golden namespace root.",
    )
    parser.add_argument(
        "--expected-opaque-result-surface-root-sha256",
        required=True,
        help="Expected opaque persisted-result surface root from the manifest.",
    )
    parser.add_argument(
        "--golden-amendment",
        type=Path,
        required=True,
        help="Prospective amendment binding the designated partial golden.",
    )
    parser.add_argument(
        "--expected-golden-amendment-sha256",
        required=True,
        help="Exact file SHA-256 of the prospective golden amendment.",
    )
    parser.add_argument(
        "--expected-golden-amendment-self-root-sha256",
        required=True,
        help="Expected self-root declared by the prospective amendment.",
    )
    parser.add_argument(
        "--expected-fixed-parity-verifier-sha256",
        required=True,
        help="Exact file SHA-256 of the fixed independent parity verifier.",
    )
    parser.add_argument(
        "--golden-successor-authority",
        type=Path,
        default=None,
        help="Recursive v2 authority proving descent from the predecessor golden.",
    )
    parser.add_argument(
        "--expected-golden-successor-authority-sha256",
        default=None,
    )
    parser.add_argument(
        "--expected-golden-successor-authority-root-sha256",
        default=None,
    )
    parser.add_argument(
        "--expected-golden-successor-authority-verification-root-sha256",
        default=None,
    )
    parser.add_argument(
        "--expected-economic-execution-contract-sha256",
        default=None,
        help="Golden-bound economic semantics digest, separate from proof code.",
    )
    parser.add_argument(
        "--expected-fixed-verifier-code-authority-root-sha256",
        default=None,
        help="Complete fixed-verifier import-closure authority root.",
    )
    parser.add_argument(
        "--parity-gate-after-day",
        default=None,
        help=(
            "Pause the same in-process S0R0 state after this sealed daily chunk; "
            "the bounded authority currently permits only 2026-01-07."
        ),
    )
    parser.add_argument(
        "--parity-gate-request",
        type=Path,
        default=None,
        help="New structural request artifact written at the Jan 1-7 barrier.",
    )
    parser.add_argument(
        "--parity-report",
        type=Path,
        default=None,
        help="Independent exact-parity report consumed with its bound receipt.",
    )
    parser.add_argument(
        "--parity-receipt",
        type=Path,
        default=None,
        help="Independent opaque-equality receipt consumed before continuation.",
    )
    parser.add_argument(
        "--parity-wait-timeout-seconds",
        type=int,
        default=86400,
    )
    parser.add_argument(
        "--stop-after-parity-gate",
        action="store_true",
        help=(
            "For a bounded cold measurement, exit cleanly after an accepted "
            "Jan 1-7 receipt instead of continuing the preserved in-process state."
        ),
    )
    parser.add_argument(
        "--streaming-proof-archive-root",
        type=Path,
        default=None,
        help=(
            "New quota-controlled archive for independently verified exact "
            "decision/scorecard/missed day shards sealed before the parity gate "
            "and throughout an authorized continuation."
        ),
    )
    parser.add_argument(
        "--max-streaming-proof-archive-bytes",
        type=int,
        default=1024 * 1024 * 1024,
        help="Hard retained archive quota; values above 1 GiB are rejected.",
    )
    parser.add_argument(
        "--decision-contract",
        default=None,
        help=(
            "Sealed replay-free B7.5 selection/sizing decision contract. "
            "Required together with --arm-id and its expected fingerprint."
        ),
    )
    parser.add_argument(
        "--arm-id",
        choices=tuple(B7_5_SELECTION_SIZING_FACTORIAL_ARM_FACTORS),
        default=None,
        help="Contract-declared factorial arm; no free factor flags are accepted.",
    )
    parser.add_argument(
        "--expected-arm-fingerprint-sha256",
        default=None,
        help=(
            "Fail before source resolution or replay if the selected arm does "
            "not match the sealed post-change input fingerprint."
        ),
    )
    return parser.parse_args(argv)


def main() -> int:
    args = parse_args()
    try:
        summary = run_typed_sparse_attempt5(args)
        exit_code = 0
    except KeyboardInterrupt:
        summary = interrupted_summary_from_partial(str(args.output_prefix))
        exit_code = 130
    except Exception as exc:
        if str(exc).startswith("current_summary_v2_"):
            failure_stage = "final_current_summary_v2_certification"
        elif str(exc).startswith("ultimate_package_runtime_input_contract_failed:"):
            failure_stage = "ultimate_package_runtime_input_preflight"
        else:
            failure_stage = "run_typed_sparse_attempt5"
        if ROUTE == CODE_ROUTE:
            summary = {
                "status": "attempt5_pre_namespace_rejected",
                "failure_stage": failure_stage,
                "failure_type": type(exc).__name__,
                "failure_message": str(exc),
                "artifacts": {},
            }
        else:
            summary = failed_summary_from_partial(
                str(args.output_prefix),
                failure_stage=failure_stage,
                failure=exc,
            )
        print(
            json.dumps(
                {
                    "status": summary["status"],
                    "failure_stage": summary["failure_stage"],
                    "failure_type": summary["failure_type"],
                    "failure_message": summary["failure_message"],
                    "artifacts": summary.get("artifacts", {}),
                },
                indent=2,
                sort_keys=True,
            )
        )
        raise
    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_day_count": summary.get("selected_day_count"),
                "profiles": summary.get("profiles")
                or summary.get("profiles_requested")
                or [],
                "artifacts": summary.get("artifacts", {}),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
