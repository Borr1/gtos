#!/usr/bin/env python3
"""Build the replay-free B7.5 source-window and no-config-delta contract."""

from __future__ import annotations

import argparse
import gc
import gzip
import json
import math
import shutil
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Iterator, Mapping

ROUTE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROUTE) not in sys.path:
    sys.path.insert(0, str(ROUTE))

import run_broad_live_as_if_replay_harness as harness  # noqa: E402
from run_selected_package_replay_bridge import norm_symbol  # noqa: E402

SCHEMA = (
    "gtos.final_moonshot.b7_5.extended_history_source_window_contract.v1"
)
OUTPUT_PATH = ROUTE / "B7_5_EXTENDED_HISTORY_SOURCE_WINDOW_CONTRACT.json"
MEMBER_AXIS_PATH = ROUTE / "SLEEVE_MEMBER_EXACT_JOIN_LEDGER.jsonl"
SELECTOR_PATH = (
    ROOT
    / "research/operations/"
    "final_moonshot_ultimate_convergence_hydrated_replay_lift_2026_06_19/"
    "HYDRATED_REPLAY_LIFT_SELECTOR_CANDIDATE_LEDGER.jsonl.gz"
)
V258_PREFIX = (
    "BROAD_LIVE_AS_IF_REPLAY_V258_B7_4_BROAD_JUNE_CACHE_SAFE_SOURCE_"
    "IDENTITY_20260601_20260619_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID"
)
WINDOWS = (
    {
        "window_id": "b7_5_2026_01",
        "start_day": "2026-01-01",
        "end_day": "2026-01-31",
    },
    {
        "window_id": "b7_5_2026_04",
        "start_day": "2026-04-01",
        "end_day": "2026-04-30",
    },
)
MINIMUM_POST_REPLAY_RESERVE_BYTES = 32 * 1024**3
SOURCE_BOUND_SIGNAL_SEMANTICS = {
    "evidence_class": (
        "source_member_axis_overlap_not_additive_exact_execution_r"
    ),
    "additive_allowed": False,
    "executable_r_percentage_allowed": False,
    "canonical_window_field": (
        "window_present_member_axis_combined_source_bound_signal_r_non_additive"
    ),
    "legacy_compatibility_alias": "window_available_source_bound_r",
    "legacy_alias_semantics": (
        "non_additive_member_axis_signal_sum_not_executable_r_denominator"
    ),
}

POSTRUN_PROOF_CONSUMER_CODE_PATHS = frozenset(
    {
        (
            "research/operations/final_moonshot_ultimate_system_"
            "denominator_to_deployment_execution_2026_06_20/"
            "build_source_bound_execution_parity.py"
        ),
        (
            "research/operations/final_moonshot_ultimate_system_"
            "denominator_to_deployment_execution_2026_06_20/"
            "verify_denominator_to_deployment_execution.py"
        ),
    }
)
BEHAVIORAL_EXECUTION_CONTRACT_FIELDS = (
    "schema",
    "code_authority",
    "missing_code_paths",
    "effective_profile_config_hashes",
    "effective_profile_config_hash_semantics",
    "config_file_hashes",
    "ultimate_package_runtime_input_contract",
    "active_replay_symbol_universe",
    "execution_options",
    "window_identity_excluded_from_shared_digest",
    "broker_live_final_authority",
)


def behavioral_execution_contract_projection(
    shared: Mapping[str, Any],
) -> dict[str, Any]:
    """Project only code and inputs that can alter replay behavior."""

    projection = {
        field: harness.json_safe(shared.get(field))
        for field in BEHAVIORAL_EXECUTION_CONTRACT_FIELDS
    }
    projection["code_authority"] = [
        harness.json_safe(row)
        for row in shared.get("code_authority") or ()
        if isinstance(row, Mapping)
        and str(row.get("path") or "") not in POSTRUN_PROOF_CONSUMER_CODE_PATHS
    ]
    projection["missing_code_paths"] = [
        str(path)
        for path in shared.get("missing_code_paths") or ()
        if str(path) not in POSTRUN_PROOF_CONSUMER_CODE_PATHS
    ]
    return projection


def postrun_proof_consumer_contract_projection(
    shared: Mapping[str, Any],
) -> dict[str, Any]:
    """Project parity/verifier code that proves results but cannot alter replay."""

    code_authority = [
        harness.json_safe(row)
        for row in shared.get("code_authority") or ()
        if isinstance(row, Mapping)
        and str(row.get("path") or "") in POSTRUN_PROOF_CONSUMER_CODE_PATHS
    ]
    missing = [
        str(path)
        for path in shared.get("missing_code_paths") or ()
        if str(path) in POSTRUN_PROOF_CONSUMER_CODE_PATHS
    ]
    return {
        "schema": "gtos.final_moonshot.b7_5.postrun_proof_consumers.v1",
        "code_authority": code_authority,
        "missing_code_paths": missing,
    }


def execution_contract_authority_partition(
    shared: Mapping[str, Any],
) -> dict[str, Any]:
    """Separate immutable behavior identity from mutable post-run proof code."""

    behavioral = behavioral_execution_contract_projection(shared)
    proof = postrun_proof_consumer_contract_projection(shared)
    proof_paths = {
        str(row.get("path") or "")
        for row in proof["code_authority"]
        if isinstance(row, Mapping)
    }
    behavioral_digest = harness.stable_sha256(behavioral)
    proof_digest = harness.stable_sha256(proof)
    return {
        "schema": "gtos.final_moonshot.b7_5.execution_contract_partition.v1",
        "valid": bool(
            len(behavioral_digest) == 64
            and len(proof_digest) == 64
            and proof_paths == POSTRUN_PROOF_CONSUMER_CODE_PATHS
            and not proof["missing_code_paths"]
        ),
        "behavioral_execution_contract_digest_sha256": behavioral_digest,
        "behavioral_execution_contract_projection": behavioral,
        "postrun_proof_consumer_contract_digest_sha256": proof_digest,
        "postrun_proof_consumer_contract_projection": proof,
        "legacy_full_shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "legacy_full_digest_semantics": (
            "compatibility_only_includes_behavior_and_postrun_proof_consumers"
        ),
        "excluded_from_behavioral_digest": sorted(
            POSTRUN_PROOF_CONSUMER_CODE_PATHS
        ),
    }


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def iter_days(start_day: str, end_day: str) -> tuple[str, ...]:
    start = date.fromisoformat(start_day)
    end = date.fromisoformat(end_day)
    if end < start:
        raise ValueError(f"invalid_window:{start_day}:{end_day}")
    return tuple(
        (start + timedelta(days=offset)).isoformat()
        for offset in range((end - start).days + 1)
    )


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else Path.open
    if path.suffix == ".gz":
        handle = opener(path, "rt", encoding="utf-8")
    else:
        handle = opener(path, "r", encoding="utf-8")
    with handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"non_mapping_jsonl_row:{path}:{line_number}")
            yield row


def axis_key(row: Mapping[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("framework") or "unknown_framework"),
        str(row.get("origin_family") or "unknown_origin_family"),
        norm_symbol(
            row.get("normalized_symbol")
            or row.get("symbol")
            or row.get("instrument")
        ),
        str(row.get("session_bucket") or "unknown_session"),
        str(row.get("side") or "UNKNOWN").upper(),
    )


def load_member_axes(path: Path = MEMBER_AXIS_PATH) -> list[dict[str, Any]]:
    rows = list(iter_jsonl(path))
    stable_ids = [str(row.get("stable_member_axis_id") or "") for row in rows]
    axis_keys = [axis_key(row) for row in rows]
    if len(rows) != harness.ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS:
        raise ValueError(f"member_axis_row_count_invalid:{len(rows)}")
    if not all(stable_ids) or len(set(stable_ids)) != len(rows):
        raise ValueError("member_axis_stable_identity_invalid")
    if len(set(axis_keys)) != len(rows):
        raise ValueError("member_axis_key_duplicate")
    return rows


def selector_window_dispositions(
    *,
    members: Iterable[Mapping[str, Any]],
    selector_path: Path = SELECTOR_PATH,
    windows: Iterable[Mapping[str, str]] = WINDOWS,
) -> dict[str, dict[str, Any]]:
    member_rows = [dict(row) for row in members]
    member_by_axis = {axis_key(row): row for row in member_rows}
    window_rows = [dict(window) for window in windows]
    stats: dict[str, defaultdict[str, dict[str, Any]]] = {
        str(window["window_id"]): defaultdict(
            lambda: {
                "candidate_rows": 0,
                "candidate_ids": set(),
                "min_decision_asof_utc": None,
                "max_decision_asof_utc": None,
            }
        )
        for window in window_rows
    }
    selector_rows_by_window: Counter[str] = Counter()
    unmatched_rows_by_window: Counter[str] = Counter()
    selector_total_rows_scanned = 0
    for row in iter_jsonl(selector_path):
        selector_total_rows_scanned += 1
        decision_time = str(row.get("decision_asof_utc") or "")
        trading_day = decision_time[:10]
        matched_window_id = None
        for window in window_rows:
            if window["start_day"] <= trading_day <= window["end_day"]:
                matched_window_id = str(window["window_id"])
                break
        if matched_window_id is None:
            continue
        selector_rows_by_window[matched_window_id] += 1
        member = member_by_axis.get(axis_key(row))
        if member is None:
            unmatched_rows_by_window[matched_window_id] += 1
            continue
        stable_id = str(member["stable_member_axis_id"])
        state = stats[matched_window_id][stable_id]
        state["candidate_rows"] += 1
        candidate_id = str(row.get("candidate_id") or "").strip()
        if candidate_id:
            state["candidate_ids"].add(candidate_id)
        if decision_time:
            prior_min = state["min_decision_asof_utc"]
            prior_max = state["max_decision_asof_utc"]
            state["min_decision_asof_utc"] = (
                decision_time
                if prior_min is None or decision_time < prior_min
                else prior_min
            )
            state["max_decision_asof_utc"] = (
                decision_time
                if prior_max is None or decision_time > prior_max
                else prior_max
            )

    result: dict[str, dict[str, Any]] = {}
    for window in window_rows:
        window_id = str(window["window_id"])
        dispositions = []
        non_additive_window_signal_r = 0.0
        for member in sorted(
            member_rows,
            key=lambda row: str(row.get("stable_member_axis_id") or ""),
        ):
            stable_id = str(member["stable_member_axis_id"])
            state = stats[window_id].get(stable_id)
            candidate_rows = int((state or {}).get("candidate_rows") or 0)
            candidate_ids = sorted((state or {}).get("candidate_ids") or ())
            available_r = float(
                member.get("combined_source_bound_signal_r") or 0.0
            )
            if candidate_rows:
                non_additive_window_signal_r += available_r
            dispositions.append(
                {
                    "stable_member_axis_id": stable_id,
                    "source_axis_row_index": member.get(
                        "source_axis_row_index"
                    ),
                    "sleeve_id": member.get("sleeve_id"),
                    "sleeve_type": member.get("sleeve_type"),
                    "framework": member.get("framework"),
                    "origin_family": member.get("origin_family"),
                    "symbol": norm_symbol(
                        member.get("normalized_symbol")
                        or member.get("symbol")
                    ),
                    "session_bucket": member.get("session_bucket"),
                    "side": str(member.get("side") or "UNKNOWN").upper(),
                    "disposition": (
                        "selector_axis_present_in_window"
                        if candidate_rows
                        else "selector_axis_absent_in_window"
                    ),
                    "selector_candidate_rows": candidate_rows,
                    "selector_unique_candidate_ids": len(candidate_ids),
                    "selector_candidate_id_samples": candidate_ids[:5],
                    "selector_min_decision_asof_utc": (
                        (state or {}).get("min_decision_asof_utc")
                    ),
                    "selector_max_decision_asof_utc": (
                        (state or {}).get("max_decision_asof_utc")
                    ),
                    "combined_source_bound_signal_r": round(available_r, 8),
                    "combined_source_bound_signal_r_evidence_class": (
                        SOURCE_BOUND_SIGNAL_SEMANTICS["evidence_class"]
                    ),
                    "combined_source_bound_signal_r_additive_allowed": False,
                    "window_present_member_axis_combined_source_bound_signal_r_non_additive": (
                        round(available_r, 8) if candidate_rows else 0.0
                    ),
                    "window_available_source_bound_r": (
                        round(available_r, 8) if candidate_rows else 0.0
                    ),
                    "window_available_source_bound_r_semantics": (
                        SOURCE_BOUND_SIGNAL_SEMANTICS["legacy_alias_semantics"]
                    ),
                }
            )
        present = sum(
            row["disposition"] == "selector_axis_present_in_window"
            for row in dispositions
        )
        summary = {
            "selector_source_path": display_path(selector_path),
            "selector_source_sha256": harness.file_sha256_cached(
                selector_path
            ),
            "selector_source_total_rows_scanned": selector_total_rows_scanned,
            "selector_rows_inside_window": selector_rows_by_window[window_id],
            "selector_rows_unmatched_to_package_axis": (
                unmatched_rows_by_window[window_id]
            ),
            "expected_member_axis_dispositions": len(member_rows),
            "member_axis_disposition_rows": len(dispositions),
            "member_axes_present": present,
            "member_axes_absent": len(dispositions) - present,
            "window_present_member_axis_combined_source_bound_signal_r_non_additive": round(
                non_additive_window_signal_r,
                8,
            ),
            "window_available_source_bound_r": round(
                non_additive_window_signal_r,
                8,
            ),
            "window_available_source_bound_r_semantics": (
                SOURCE_BOUND_SIGNAL_SEMANTICS["legacy_alias_semantics"]
            ),
            "source_bound_signal_evidence_class": (
                SOURCE_BOUND_SIGNAL_SEMANTICS["evidence_class"]
            ),
            "source_bound_r_additive_allowed": False,
            "executable_r_to_source_bound_r_percentage_allowed": False,
            "disposition_digest_sha256": harness.stable_sha256(dispositions),
        }
        result[window_id] = {
            "summary": summary,
            "dispositions": dispositions,
        }
    return result


def shared_replay_execution_contract() -> dict[str, Any]:
    args = SimpleNamespace(
        profiles=(harness.PROFILE_REPAIRED,),
        chunk_size=1,
        max_candidates_per_symbol_window=0,
        smoke_subset=False,
        skip_tick_source=False,
        use_native_h1=False,
        omit_candidate_ledger=True,
        omit_candidate_index_ledger=True,
        omit_packet_sidecar_ledger=True,
        compact_missed_ledger=True,
        compact_decision_ledger=True,
        compact_scorecard_ledger=True,
        candidate_ledger_packet_max_bytes=1024,
        scorecard_ledger_packet_max_bytes=4096,
        compact_scorecard_symbol_risk_config=True,
        scorecard_probe_row_limit=12,
        gc_between_chunks=True,
    )
    runtime_inputs = harness.ultimate_package_runtime_input_contract()
    return harness.broad_replay_shared_execution_contract(
        profiles=args.profiles,
        active_symbols=harness.GTOS_24_SYMBOL_SURFACE,
        execution_options=harness.broad_replay_execution_options_from_args(
            args
        ),
        runtime_input_contract=runtime_inputs,
    )


def source_authority_plans(
    *,
    windows: Iterable[Mapping[str, str]] = WINDOWS,
    resolver_factory: Any = harness.BroadSourceResolver,
) -> dict[str, dict[str, Any]]:
    plans: dict[str, dict[str, Any]] = {}
    resolver = resolver_factory(
        use_native_h1=False,
        skip_tick_source=False,
        verbose=False,
    )
    symbols = tuple(harness.GTOS_24_SYMBOL_SURFACE)
    for window_value in windows:
        window = dict(window_value)
        window_id = str(window["window_id"])
        days = iter_days(window["start_day"], window["end_day"])
        sources = resolver.build_sources_for_days(
            days,
            symbols=symbols,
            source_authority_days=days,
        )
        plan = harness.static_source_authority_plan(
            sources=sources,
            source_authority_days=days,
            requested_symbols=symbols,
        )
        source_rows = resolver.drain_source_rows()
        del sources
        cleanup = resolver.release_completed_chunk_caches(
            days,
            source_authority_days=days,
        )
        gc_collected_objects = gc.collect()
        cleanup_valid = bool(
            int(
                cleanup.get("completed_chunk_day_scoped_entries_remaining")
                or 0
            )
            == 0
            and int(
                cleanup.get(
                    "completed_source_authority_scoped_entries_remaining"
                )
                or 0
            )
            == 0
            and cleanup.get("completed_replay_source_caches_released") is True
        )
        plans[window_id] = {
            "window_id": window_id,
            "start_day": window["start_day"],
            "end_day": window["end_day"],
            "day_count": len(days),
            "source_authority_plan": plan,
            "source_resolution_row_count": len(source_rows),
            "source_resolution_rows_digest_sha256": harness.stable_sha256(
                source_rows
            ),
            "source_cache_cleanup_valid": cleanup_valid,
            "source_cache_cleanup": cleanup,
            "gc_collected_objects": gc_collected_objects,
        }
    return plans


def capacity_projection(
    *,
    windows: Iterable[Mapping[str, str]] = WINDOWS,
    free_bytes: int | None = None,
) -> dict[str, Any]:
    retained_files = sorted(
        path
        for path in ROUTE.glob(f"{V258_PREFIX}*")
        if path.is_file()
    )
    retained_rows = [
        {
            "path": display_path(path),
            "bytes": path.stat().st_size,
        }
        for path in retained_files
    ]
    retained_bytes = sum(row["bytes"] for row in retained_rows)
    benchmark_day_count = 19
    bytes_per_day = math.ceil(retained_bytes / benchmark_day_count)
    window_rows = []
    for window in windows:
        day_count = len(iter_days(window["start_day"], window["end_day"]))
        window_rows.append(
            {
                "window_id": window["window_id"],
                "day_count": day_count,
                "planned_chunk_size_days": 1,
                "planned_chunk_count": day_count,
                "projected_retained_bytes": bytes_per_day * day_count,
            }
        )
    projected_bytes = sum(
        row["projected_retained_bytes"] for row in window_rows
    )
    available = (
        int(free_bytes)
        if free_bytes is not None
        else int(shutil.disk_usage(ROOT).free)
    )
    required = projected_bytes + MINIMUM_POST_REPLAY_RESERVE_BYTES
    valid = bool(retained_rows and retained_bytes > 0 and available >= required)
    return {
        "status": (
            "capacity_projection_passed"
            if valid
            else "capacity_projection_failed"
        ),
        "valid": valid,
        "v258_benchmark_prefix": V258_PREFIX,
        "v258_retained_file_count": len(retained_rows),
        "v258_retained_bytes": retained_bytes,
        "v258_benchmark_day_count": benchmark_day_count,
        "v258_bytes_per_day_ceiling": bytes_per_day,
        "v258_size_manifest_sha256": harness.stable_sha256(retained_rows),
        "projection_formula": (
            "ceil(v258_retained_bytes/19)*window_calendar_day_count"
        ),
        "windows": window_rows,
        "planned_chunk_count_total": sum(
            row["planned_chunk_count"] for row in window_rows
        ),
        "projected_retained_bytes_total": projected_bytes,
        "minimum_post_replay_reserve_bytes": (
            MINIMUM_POST_REPLAY_RESERVE_BYTES
        ),
        "required_free_bytes_before_both_windows": required,
        "observed_free_bytes": available,
        "projected_free_bytes_after_both_windows": available - projected_bytes,
    }


def replay_command(
    *,
    window: Mapping[str, Any],
    shared_digest: str,
    source_plan_digest: str,
) -> str:
    compact_id = str(window["window_id"]).upper()
    prefix = (
        f"BROAD_LIVE_AS_IF_REPLAY_{compact_id}_EXTENDED_HISTORY_"
        "REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID"
    )
    script = str(
        (ROUTE / "run_broad_live_as_if_replay_harness.py").relative_to(ROOT)
    )
    return " ".join(
        (
            "python3",
            script,
            "--start",
            str(window["start_day"]),
            "--end",
            str(window["end_day"]),
            "--chunk-size 1",
            f"--output-prefix {prefix}",
            f"--profiles {harness.PROFILE_REPAIRED}",
            "--max-candidates-per-symbol-window 0",
            "--omit-candidate-ledger",
            "--omit-candidate-index-ledger",
            "--omit-packet-sidecar-ledger",
            "--compact-missed-ledger",
            "--compact-decision-ledger",
            "--compact-scorecard-ledger",
            "--candidate-ledger-packet-max-bytes 1024",
            "--scorecard-ledger-packet-max-bytes 4096",
            "--compact-scorecard-symbol-risk-config",
            "--scorecard-probe-row-limit 12",
            "--gc-between-chunks",
            f"--expected-shared-execution-contract-sha256 {shared_digest}",
            f"--expected-source-plan-digest-sha256 {source_plan_digest}",
        )
    )


def build_contract(
    *,
    output_path: Path = OUTPUT_PATH,
    member_path: Path = MEMBER_AXIS_PATH,
    selector_path: Path = SELECTOR_PATH,
    windows: Iterable[Mapping[str, str]] = WINDOWS,
    resolver_factory: Any = harness.BroadSourceResolver,
    free_bytes: int | None = None,
) -> dict[str, Any]:
    window_rows = [dict(window) for window in windows]
    members = load_member_axes(member_path)
    selector = selector_window_dispositions(
        members=members,
        selector_path=selector_path,
        windows=window_rows,
    )
    shared = shared_replay_execution_contract()
    execution_contract_partition = execution_contract_authority_partition(shared)
    source_plans = source_authority_plans(
        windows=window_rows,
        resolver_factory=resolver_factory,
    )
    capacity = capacity_projection(
        windows=window_rows,
        free_bytes=free_bytes,
    )
    runtime_input_contract = shared.get(
        "ultimate_package_runtime_input_contract"
    )
    runtime_input_contract = (
        runtime_input_contract
        if isinstance(runtime_input_contract, Mapping)
        else {}
    )
    contract_windows = []
    source_plan_valid = True
    selector_valid = True
    for window in window_rows:
        window_id = str(window["window_id"])
        source = source_plans[window_id]
        selector_row = selector[window_id]
        plan = source["source_authority_plan"]
        source_valid = bool(
            plan.get("valid") is True
            and source.get("source_cache_cleanup_valid") is True
        )
        disposition_summary = selector_row["summary"]
        disposition_valid = bool(
            disposition_summary["member_axis_disposition_rows"]
            == harness.ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS
            and disposition_summary["selector_rows_unmatched_to_package_axis"]
            == 0
            and disposition_summary["member_axes_present"]
            + disposition_summary["member_axes_absent"]
            == harness.ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS
        )
        source_plan_valid = source_plan_valid and source_valid
        selector_valid = selector_valid and disposition_valid
        contract_windows.append(
            {
                **window,
                "day_count": source["day_count"],
                "source_plan_valid": source_valid,
                "source_authority_plan": plan,
                "source_resolution_row_count": source[
                    "source_resolution_row_count"
                ],
                "source_resolution_rows_digest_sha256": source[
                    "source_resolution_rows_digest_sha256"
                ],
                "source_cache_cleanup_valid": source[
                    "source_cache_cleanup_valid"
                ],
                "selector_disposition_valid": disposition_valid,
                "selector_disposition_summary": disposition_summary,
                "selector_axis_dispositions": selector_row["dispositions"],
                "replay_command": replay_command(
                    window=window,
                    shared_digest=str(
                        shared[
                            "shared_execution_contract_digest_sha256"
                        ]
                    ),
                    source_plan_digest=str(plan["plan_digest_sha256"]),
                ),
            }
        )
    unexpected_config_delta_paths: list[str] = []
    pair_payload = {
        "window_ids": [row["window_id"] for row in contract_windows],
        "shared_execution_contract_digest_sha256": shared.get(
            "shared_execution_contract_digest_sha256"
        ),
        "behavioral_execution_contract_digest_sha256": (
            execution_contract_partition.get(
                "behavioral_execution_contract_digest_sha256"
            )
        ),
        "postrun_proof_consumer_contract_digest_sha256": (
            execution_contract_partition.get(
                "postrun_proof_consumer_contract_digest_sha256"
            )
        ),
        "source_plan_digests_sha256": {
            row["window_id"]: row["source_authority_plan"].get(
                "plan_digest_sha256"
            )
            for row in contract_windows
        },
        "selector_disposition_digests_sha256": {
            row["window_id"]: row["selector_disposition_summary"].get(
                "disposition_digest_sha256"
            )
            for row in contract_windows
        },
        "source_bound_signal_semantics_sha256": harness.stable_sha256(
            SOURCE_BOUND_SIGNAL_SEMANTICS
        ),
        "unexpected_config_delta_paths": unexpected_config_delta_paths,
    }
    source_window_contract_valid = bool(
        len(contract_windows) == 2
        and contract_windows[0]["end_day"]
        < contract_windows[1]["start_day"]
        and shared.get("valid") is True
        and execution_contract_partition.get("valid") is True
        and runtime_input_contract.get("valid") is True
        and source_plan_valid
        and selector_valid
        and not unexpected_config_delta_paths
    )
    new_replay_capacity_ready = bool(
        source_window_contract_valid and capacity.get("valid") is True
    )
    payload = {
        "schema": SCHEMA,
        "status": (
            "b7_5_extended_history_source_window_contract_valid_replay_closed"
            if source_window_contract_valid
            else "b7_5_extended_history_source_window_contract_invalid"
        ),
        "valid": source_window_contract_valid,
        "new_replay_capacity_ready": new_replay_capacity_ready,
        "replay_launch_claim": False,
        "capacity_gate_disposition": (
            "new_replay_capacity_ready"
            if new_replay_capacity_ready
            else "source_contract_valid_new_replay_requires_storage_checkpoint"
        ),
        "replay_free_builder": True,
        "run_campaign_call_count": 0,
        "window_count": len(contract_windows),
        "non_adjacent_windows_required": True,
        "shared_execution_contract": shared,
        "execution_contract_authority_partition": execution_contract_partition,
        "unexpected_config_delta_paths": unexpected_config_delta_paths,
        "capacity_projection": capacity,
        "windows": contract_windows,
        "pair_binding_sha256": harness.stable_sha256(pair_payload),
        "pair_binding_payload": pair_payload,
        "source_bound_signal_semantics": SOURCE_BOUND_SIGNAL_SEMANTICS,
        "full_82_sleeve_surface_preserved": True,
        "expected_sleeve_count": harness.ULTIMATE_PACKAGE_EXPECTED_REGISTRY_ROWS,
        "expected_member_axis_count": (
            harness.ULTIMATE_PACKAGE_EXPECTED_MEMBER_AXIS_ROWS
        ),
        "live_broker_authority": False,
        "broker_mutation_enabled": False,
        "final_selection_claim": False,
        "contract_scope": (
            "source_window_and_unchanged_execution_authority_preflight_"
            "not_behavioral_or_live_proof"
        ),
    }
    payload["contract_digest_sha256"] = harness.stable_sha256(payload)
    harness.atomic_write_json(output_path, harness.json_safe(payload))
    return payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = build_contract(output_path=args.output)
    print(
        json.dumps(
            {
                "status": result["status"],
                "valid": result["valid"],
                "new_replay_capacity_ready": result[
                    "new_replay_capacity_ready"
                ],
                "contract_digest_sha256": result["contract_digest_sha256"],
                "output": str(args.output),
                "windows": [
                    {
                        "window_id": row["window_id"],
                        "source_plan_digest_sha256": row[
                            "source_authority_plan"
                        ]["plan_digest_sha256"],
                        "member_axes_present": row[
                            "selector_disposition_summary"
                        ]["member_axes_present"],
                        "window_present_member_axis_combined_source_bound_signal_r_non_additive": row[
                            "selector_disposition_summary"
                        ][
                            "window_present_member_axis_combined_source_bound_signal_r_non_additive"
                        ],
                    }
                    for row in result["windows"]
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
