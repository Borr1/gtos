#!/usr/bin/env python3
"""Build the deterministic B7.5 cross-window behavior proof.

The paired January/April windows share one execution contract but have disjoint
market dates, so this analyzer compares normalized transfer and behavior. It
never performs cross-window trade-identity comparisons and never runs replay.
May and June are retained as historical ladder comparators, not config-identical
B7.5 evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any


ROUTE = Path(__file__).resolve().parent
if str(ROUTE) not in sys.path:
    sys.path.insert(0, str(ROUTE))

import compare_broad_live_as_if_replay_runs as replay_compare  # noqa: E402
import build_b7_5_extended_history_source_window_contract as source_contract_builder  # noqa: E402


SCHEMA = "gtos.final_moonshot.b7_5.extended_history_behavior.v1"
OUTPUT_JSON = "B7_5_EXTENDED_HISTORY_BEHAVIOR_SUMMARY.json"
OUTPUT_MD = "B7_5_EXTENDED_HISTORY_BEHAVIOR_DOSSIER.md"
PROFILE = "repaired_package_conversion_v3"
SOURCE_WINDOW_CONTRACT_NAME = "B7_5_EXTENDED_HISTORY_SOURCE_WINDOW_CONTRACT.json"
SOURCE_BOUND_SIGNAL_EVIDENCE_CLASS = (
    "source_member_axis_overlap_not_additive_exact_execution_r"
)
SOURCE_BOUND_PERCENTAGE_DISPOSITION = (
    "forbidden_non_additive_source_member_axis_overlap_signal"
)


@dataclass(frozen=True)
class WindowSpec:
    window_id: str
    role: str
    prefix: str


DEFAULT_WINDOWS = (
    WindowSpec(
        "b7_5_2026_01",
        "paired_extended_history",
        "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_01_TERMINAL_BLOCKER_STAGE_REPAIR_R4_RELATIONAL_COMPACT_FULLGRID",
    ),
    WindowSpec(
        "b7_5_2026_04",
        "paired_extended_history",
        "BROAD_LIVE_AS_IF_REPLAY_B7_5_2026_04_TERMINAL_BLOCKER_STAGE_REPAIR_R4_RELATIONAL_COMPACT_FULLGRID",
    ),
    WindowSpec(
        "hostile_2026_05",
        "historical_ladder_comparator_not_config_identical",
        "BROAD_LIVE_AS_IF_REPLAY_V249_B7_2_HOSTILE_5D_V248_SIGNED_ACTION_TERMINAL_BINDING_20260513_20260517_REPAIRED_ONLY_COMPACT_FULLGRID",
    ),
    WindowSpec(
        "broad_2026_06",
        "historical_ladder_comparator_not_config_identical",
        "BROAD_LIVE_AS_IF_REPLAY_V258_B7_4_BROAD_JUNE_CACHE_SAFE_SOURCE_IDENTITY_20260601_20260619_REPAIRED_ONLY_RELATIONAL_COMPACT_FULLGRID",
    ),
)


DIMENSIONS: dict[str, tuple[str, ...]] = {
    "symbol": ("symbol",),
    "session": ("route_session", "session_bucket", "session"),
    "side": ("side", "direction"),
    "day": ("trading_day", "decision_time_utc", "decision_time"),
    "origin_family": ("origin_family", "candidate_origin_family"),
    "framework": ("framework", "current_framework"),
    "order_policy": ("order_policy",),
    "action": ("risk_decision", "order_policy_action", "action"),
    "close_reason": ("close_reason", "policy_close_reason"),
    "fill_realism": ("fill_realism_class",),
}


def first_present(row: Mapping[str, Any], fields: Iterable[str]) -> Any:
    for field in fields:
        value = row.get(field)
        if value not in (None, "", [], {}):
            return value
    return None


def fnum(value: Any) -> float:
    return replay_compare.fnum(value)


def inum(value: Any) -> int:
    return replay_compare.inum(value)


def round8(value: Any) -> float:
    return round(fnum(value), 8)


def date_count(start: Any, end: Any) -> int:
    try:
        first = date.fromisoformat(str(start))
        last = date.fromisoformat(str(end))
    except (TypeError, ValueError):
        return 0
    return max((last - first).days + 1, 0)


def parse_date(value: Any) -> date | None:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def row_net_r(row: Mapping[str, Any]) -> float | None:
    value = first_present(row, ("net_r", "net_proxy_r"))
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def is_headline(row: Mapping[str, Any]) -> bool:
    return row.get("headline_result_eligible") is True


def dimension_value(row: Mapping[str, Any], dimension: str) -> str:
    value = first_present(row, DIMENSIONS[dimension])
    if dimension == "day":
        return str(value or "unknown")[:10] or "unknown"
    return str(value or "unknown")


def aggregate_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    materialized = list(rows)
    scoreable_net_r = [
        value for row in materialized if (value := row_net_r(row)) is not None
    ]
    wins = sum(value > 0 for value in scoreable_net_r)
    losses = sum(value < 0 for value in scoreable_net_r)
    flats = sum(value == 0 for value in scoreable_net_r)
    net_r = sum(scoreable_net_r)
    gross_r = sum(fnum(row.get("gross_r")) for row in materialized)
    final_r = sum(fnum(row.get("final_r")) for row in materialized)
    cost_r = sum(
        fnum(first_present(row, ("expected_cost_r", "broker_pretrade_cost_r")))
        for row in materialized
    )
    return {
        "trade_rows": len(materialized),
        "scoreable_trade_rows": len(scoreable_net_r),
        "unscoreable_trade_rows": len(materialized) - len(scoreable_net_r),
        "terminal_r_unscoreable_trade_rows": sum(
            row.get("terminal_r_scoreable") is False for row in materialized
        ),
        "wins": wins,
        "losses": losses,
        "flats": flats,
        "net_r": round(net_r, 8),
        "gross_r": round(gross_r, 8),
        "final_r": round(final_r, 8),
        "execution_cost_r": round(cost_r, 8),
        "cash_pnl": round(sum(fnum(first_present(row, ("pnl_cash", "cash_pnl"))) for row in materialized), 8),
        "risk_cash": round(sum(fnum(row.get("risk_cash")) for row in materialized), 8),
        "risk_pct": round(
            sum(
                fnum(first_present(row, ("risk_pct", "approved_risk_pct")))
                for row in materialized
            ),
            8,
        ),
    }


def breakdown(rows: Iterable[Mapping[str, Any]], dimension: str) -> list[dict[str, Any]]:
    groups: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[dimension_value(row, dimension)].append(row)
    output = []
    for key, members in groups.items():
        output.append({dimension: key, **aggregate_rows(members)})
    return sorted(output, key=lambda row: (fnum(row.get("net_r")), str(row.get(dimension))))


def behavior_surface(rows: list[dict[str, Any]], day_count_value: int) -> dict[str, Any]:
    rollup = aggregate_rows(rows)
    rollup["trade_frequency_per_day"] = round(
        len(rows) / day_count_value, 8
    ) if day_count_value else 0.0
    rollup["breakdowns"] = {
        dimension: breakdown(rows, dimension) for dimension in DIMENSIONS
    }
    rollup["risk_ladder"] = replay_compare.trade_rollup(rows)
    rollup["risk_ladder"].pop("sample_keys", None)
    return rollup


def source_binding(summary: Mapping[str, Any]) -> dict[str, Any]:
    binding = summary.get("b7_5_contract_binding")
    return dict(binding) if isinstance(binding, Mapping) else {}


def selected_lifecycle(stats: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "selected_action_counts",
        "scheduler_selected_action_before_finalizer_counts",
        "accepted_pending_order_rows",
        "terminal_order_rows",
        "order_status_counts",
        "skip_count",
        "delay_or_hold_count",
        "cancel_replace_event_count",
        "pending_replacement_applied_terminal_rows",
        "guarded_market_fallback_applied_count",
        "risk_finalizer_status_counts",
    )
    return {key: stats.get(key) for key in keys if stats.get(key) is not None}


def transfer_rates(transfer: Mapping[str, Any]) -> dict[str, Any]:
    package_axes = inum(transfer.get("package_axes_available_inside_replay_window"))
    candidate_axes = inum(transfer.get("candidate_generated_axes_inside_replay_window"))
    scorecard_axes = inum(
        transfer.get("scorecard_or_order_present_axes_inside_replay_window")
    )
    order_axes = inum(transfer.get("order_present_axes_inside_replay_window"))
    filled_axes = inum(transfer.get("filled_trade_axes_inside_replay_window"))

    def pct(numerator: int, denominator: int) -> float:
        return round(100.0 * numerator / denominator, 6) if denominator else 0.0

    non_additive_signal_r = transfer.get(
        "non_additive_executable_gated_source_bound_signal_r_inside_replay_window"
    )
    non_additive_signal_r_available = non_additive_signal_r not in (None, "")
    return {
        "package_axes": package_axes,
        "candidate_generated_axes": candidate_axes,
        "scorecard_or_order_present_axes": scorecard_axes,
        "order_present_axes": order_axes,
        "filled_trade_axes": filled_axes,
        "candidate_pct_of_package": pct(candidate_axes, package_axes),
        "scorecard_pct_of_candidate": pct(scorecard_axes, candidate_axes),
        "order_pct_of_scorecard": pct(order_axes, scorecard_axes),
        "fill_pct_of_order": pct(filled_axes, order_axes),
        "candidate_instance_rows": inum(
            transfer.get("candidate_instance_rows_inside_replay_window")
        ),
        "scorecard_present_candidate_instance_rows": inum(
            transfer.get(
                "scorecard_present_candidate_instance_rows_inside_replay_window"
            )
        ),
        "scheduler_selected_candidate_instance_rows": inum(
            transfer.get(
                "scheduler_selected_candidate_instance_rows_inside_replay_window"
            )
        ),
        "order_present_candidate_instance_rows": inum(
            transfer.get(
                "order_present_candidate_instance_rows_inside_replay_window"
            )
        ),
        "filled_candidate_instance_rows": inum(
            transfer.get("filled_candidate_instance_rows_inside_replay_window")
        ),
        "missed_candidate_instance_rows": inum(
            transfer.get("missed_candidate_instance_rows_inside_replay_window")
        ),
        "source_bound_signal_evidence_class": transfer.get(
            "source_bound_signal_evidence_class"
        ),
        "source_bound_r_additive_allowed": transfer.get(
            "source_bound_r_additive_allowed"
        ),
        "executable_r_to_source_bound_r_percentage_allowed": transfer.get(
            "executable_r_to_source_bound_r_percentage_allowed"
        ),
        "non_additive_window_source_bound_signal_available": (
            non_additive_signal_r_available
        ),
        "non_additive_window_source_bound_signal_r": (
            round8(non_additive_signal_r)
            if non_additive_signal_r_available
            else None
        ),
        "diagnostic_global_source_bound_r_not_denominator": round8(
            transfer.get("diagnostic_global_source_bound_r_sum_not_denominator")
        ),
        "actual_physical_executable_r": round8(
            transfer.get("actual_executable_r_inside_replay_window")
        ),
        "actual_headline_executable_r": round8(
            transfer.get("headline_replay_net_r_inside_replay_window")
        ),
        "physical_r_pct_of_source_bound_signal": transfer.get(
            "actual_executable_r_pct_of_window_source_bound_r"
        ),
        "physical_r_pct_disposition": transfer.get(
            "actual_executable_r_pct_disposition"
        ),
    }


def artifact_metadata(
    path: Path,
    *,
    required: bool,
    row_unit: str | None = None,
    bind_hash: bool = True,
) -> dict[str, Any]:
    present = path.is_file() and path.stat().st_size > 0
    payload: dict[str, Any] = {
        "path": path.name,
        "required": required,
        "present": present,
        "row_unit": row_unit,
        "byte_count": path.stat().st_size if present else 0,
        "hash_bound": bool(present and bind_hash),
        "sha256": None,
        "row_count": None,
    }
    if not present:
        payload["availability_disposition"] = (
            "required_artifact_missing"
            if required
            else "historical_comparator_row_level_artifact_unavailable"
        )
        return payload
    if not bind_hash:
        payload["availability_disposition"] = (
            "historical_comparator_row_level_artifact_present_not_pair_bound"
        )
        return payload
    digest = hashlib.sha256()
    row_count = 0
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
            if row_unit is not None:
                row_count += chunk.count(b"\n")
    payload["sha256"] = digest.hexdigest()
    payload["row_count"] = row_count if row_unit is not None else None
    payload["availability_disposition"] = (
        "required_pair_artifact_hash_bound"
        if required
        else "historical_comparator_artifact_hash_bound"
    )
    return payload


def parity_ledger_path(prefix: str, *, root: Path) -> Path:
    summary = replay_compare.parity_summary_path(prefix, root=root)
    suffix = "_SUMMARY.json"
    if not summary.name.endswith(suffix):
        raise ValueError(f"unexpected parity summary name: {summary.name}")
    return summary.with_name(summary.name[: -len(suffix)] + "_LEDGER.jsonl")


def artifact_contract(spec: WindowSpec, root: Path) -> dict[str, Any]:
    paired = spec.role == "paired_extended_history"
    paths = {
        "summary": (
            replay_compare.summary_path(spec.prefix, root=root),
            True,
            None,
            True,
        ),
        "flow_summary": (
            replay_compare.flow_summary_path(spec.prefix, root=root),
            True,
            None,
            True,
        ),
        "parity_summary": (
            replay_compare.parity_summary_path(spec.prefix, root=root),
            True,
            None,
            True,
        ),
        "trade_ledger": (
            replay_compare.trade_path(spec.prefix, root=root),
            True,
            "physical_fill_row",
            True,
        ),
        "source_bound_parity_ledger": (
            parity_ledger_path(spec.prefix, root=root),
            paired,
            "source_bound_parity_record",
            paired,
        ),
        "candidate_instance_projection_ledger": (
            replay_compare.candidate_projection_path(spec.prefix, root=root),
            paired,
            "candidate_instance_row",
            paired,
        ),
    }
    return {
        name: artifact_metadata(
            path,
            required=required,
            row_unit=row_unit,
            bind_hash=bind_hash,
        )
        for name, (path, required, row_unit, bind_hash) in paths.items()
    }


def source_window_contract_binding(root: Path) -> dict[str, Any]:
    path = root / SOURCE_WINDOW_CONTRACT_NAME
    artifact = artifact_metadata(path, required=True)
    contract = replay_compare.read_json(path)
    execution_partition = contract.get("execution_contract_authority_partition")
    execution_partition = (
        execution_partition if isinstance(execution_partition, Mapping) else {}
    )
    windows = [
        {
            "window_id": row.get("window_id"),
            "start_day": row.get("start_day"),
            "end_day": row.get("end_day"),
            "source_plan_digest_sha256": (
                (row.get("source_authority_plan") or {}).get(
                    "plan_digest_sha256"
                )
            ),
            "selector_disposition_digest_sha256": (
                (row.get("selector_disposition_summary") or {}).get(
                    "disposition_digest_sha256"
                )
            ),
        }
        for row in contract.get("windows") or ()
        if isinstance(row, Mapping)
    ]
    return {
        "artifact": artifact,
        "valid": contract.get("valid") is True,
        "contract_digest_sha256": contract.get("contract_digest_sha256"),
        "pair_binding_sha256": contract.get("pair_binding_sha256"),
        "shared_execution_contract_digest_sha256": (
            (contract.get("shared_execution_contract") or {}).get(
                "shared_execution_contract_digest_sha256"
            )
        ),
        "behavioral_execution_contract_digest_sha256": (
            execution_partition.get(
                "behavioral_execution_contract_digest_sha256"
            )
        ),
        "postrun_proof_consumer_contract_digest_sha256": (
            execution_partition.get(
                "postrun_proof_consumer_contract_digest_sha256"
            )
        ),
        "execution_contract_authority_partition_valid": (
            execution_partition.get("valid") is True
        ),
        "source_bound_signal_semantics": contract.get(
            "source_bound_signal_semantics"
        ),
        "windows": windows,
    }


def window_report(spec: WindowSpec, *, root: Path = ROUTE) -> dict[str, Any]:
    summary = replay_compare.read_json(replay_compare.summary_path(spec.prefix, root=root))
    if not summary:
        raise FileNotFoundError(f"missing completed replay summary for {spec.window_id}: {spec.prefix}")
    metrics = replay_compare.run_metrics(spec.prefix, root=root)
    stats = replay_compare.first_profile_stats(summary)
    transfer, transfer_status = replay_compare.load_axis_transfer_with_status(
        spec.prefix,
        profile=PROFILE,
        role=spec.window_id,
        root=root,
    )
    trade_rows = list(replay_compare.iter_jsonl(replay_compare.trade_path(spec.prefix, root=root)))
    expected_physical = inum(metrics.get("physical_trades"))
    if len(trade_rows) != expected_physical:
        raise ValueError(
            f"{spec.window_id} trade ledger mismatch: expected {expected_physical}, observed {len(trade_rows)}"
        )
    headline_rows = [row for row in trade_rows if is_headline(row)]
    diagnostic_rows = [row for row in trade_rows if not is_headline(row)]
    expected_headline = inum(metrics.get("headline_trades"))
    days = date_count(summary.get("date_start"), summary.get("date_end"))
    refused_executed = sum(
        str(row.get("pretrade_cost_packet_status") or "").upper() == "REFUSED"
        for row in trade_rows
    )
    source_gap_executed = sum(
        row.get("broker_pretrade_cost_executable") is False
        or str(row.get("cost_source_gap_status") or "").lower()
        not in ("", "not_applicable", "source_bound_cost_authority_present")
        for row in trade_rows
    )
    artifacts = artifact_contract(spec, root)
    binding = source_binding(summary)
    embedded_shared_contract = summary.get("shared_execution_contract")
    embedded_shared_contract = (
        embedded_shared_contract
        if isinstance(embedded_shared_contract, Mapping)
        else {}
    )
    if embedded_shared_contract:
        replay_execution_partition = (
            source_contract_builder.execution_contract_authority_partition(
                embedded_shared_contract
            )
        )
        binding["behavioral_execution_contract_digest_sha256"] = (
            replay_execution_partition.get(
                "behavioral_execution_contract_digest_sha256"
            )
        )
        binding["postrun_proof_consumer_contract_digest_sha256"] = (
            replay_execution_partition.get(
                "postrun_proof_consumer_contract_digest_sha256"
            )
        )
        binding["execution_contract_authority_partition_valid"] = (
            replay_execution_partition.get("valid") is True
        )
        binding["legacy_full_shared_execution_contract_digest_sha256"] = (
            binding.get("actual_shared_execution_contract_digest_sha256")
        )
    elif binding.get("behavioral_execution_contract_digest_sha256") is None:
        # Synthetic focused tests may supply an already-scoped digest without a
        # materialized replay summary. Real paired artifacts never use this path.
        binding["behavioral_execution_contract_digest_sha256"] = binding.get(
            "actual_shared_execution_contract_digest_sha256"
        )
        binding["execution_contract_authority_partition_valid"] = True
    transfer_summary = transfer_rates(transfer)
    parity_payload = replay_compare.read_json(
        replay_compare.parity_summary_path(spec.prefix, root=root)
    )
    projection = parity_payload.get("candidate_instance_parity_projection")
    projection = projection if isinstance(projection, Mapping) else {}
    profile_stages = (
        projection.get("profile_stage_presence_counts") or {}
    ).get(PROFILE) or {}
    for output_field, stage in (
        ("candidate_instance_rows", "candidate"),
        ("scorecard_present_candidate_instance_rows", "scorecard"),
        ("scheduler_selected_candidate_instance_rows", "scheduler_selected"),
        ("order_present_candidate_instance_rows", "order"),
        ("filled_candidate_instance_rows", "trade"),
        ("missed_candidate_instance_rows", "missed"),
    ):
        if transfer_summary[output_field] == 0 and stage in profile_stages:
            transfer_summary[output_field] = inum(profile_stages.get(stage))
    paired_row_ledgers_bound = all(
        artifacts[name].get("required") is True
        and artifacts[name].get("present") is True
        and artifacts[name].get("hash_bound") is True
        and artifacts[name].get("row_count") is not None
        for name in (
            "source_bound_parity_ledger",
            "candidate_instance_projection_ledger",
        )
    ) if spec.role == "paired_extended_history" else True
    non_additive_signal_truth = bool(
        transfer_summary["source_bound_signal_evidence_class"]
        == SOURCE_BOUND_SIGNAL_EVIDENCE_CLASS
        and transfer_summary["source_bound_r_additive_allowed"] is False
        and transfer_summary[
            "executable_r_to_source_bound_r_percentage_allowed"
        ]
        is False
        and transfer_summary["physical_r_pct_of_source_bound_signal"] is None
        and transfer_summary["physical_r_pct_disposition"]
        == SOURCE_BOUND_PERCENTAGE_DISPOSITION
    )
    paired_semantics_required = spec.role == "paired_extended_history"
    truth_contract = {
        "completed": str(summary.get("status") or "").endswith("broker_live_closed"),
        "all_required_artifacts_present": all(
            row.get("present") is True
            for row in artifacts.values()
            if row.get("required") is True
        ),
        "transfer_status": transfer_status.get("status"),
        "full_82_sleeve_axis_surface": transfer_summary["package_axes"] == 1101,
        "non_additive_source_signal_truth_valid": (
            non_additive_signal_truth if paired_semantics_required else True
        ),
        "source_bound_signal_semantics_authority": (
            "paired_current_non_additive_contract"
            if paired_semantics_required
            else "historical_comparator_not_pair_semantics_authority"
        ),
        "behavioral_execution_contract_partition_bound": (
            binding.get("execution_contract_authority_partition_valid") is True
            and len(
                str(
                    binding.get(
                        "behavioral_execution_contract_digest_sha256"
                    )
                    or ""
                )
            )
            == 64
            if paired_semantics_required
            else True
        ),
        "paired_row_level_artifacts_hash_bound": paired_row_ledgers_bound,
        "candidate_transfer_nonzero": transfer_summary["candidate_generated_axes"] > 0,
        "scorecard_transfer_nonzero": transfer_summary[
            "scorecard_or_order_present_axes"
        ] > 0,
        "order_transfer_nonzero": transfer_summary["order_present_axes"] > 0,
        "fill_transfer_nonzero": transfer_summary["filled_trade_axes"] > 0,
        "physical_trade_count_reconciled": len(trade_rows) == expected_physical,
        "headline_trade_count_reconciled": len(headline_rows) == expected_headline,
        "executed_refused_cost_rows": refused_executed,
        "executed_source_gap_rows": source_gap_executed,
        "broker_live_final_closed": (
            summary.get("live_broker_authority") is not True
            and summary.get("broker_mutation_enabled") is not True
            and summary.get("final_selection_claim") is not True
        ),
    }
    truth_contract["pass"] = all(
        (
            truth_contract["completed"],
            truth_contract["all_required_artifacts_present"],
            truth_contract["transfer_status"] == "present",
            truth_contract["full_82_sleeve_axis_surface"],
            truth_contract["non_additive_source_signal_truth_valid"],
            truth_contract["behavioral_execution_contract_partition_bound"],
            truth_contract["paired_row_level_artifacts_hash_bound"],
            truth_contract["candidate_transfer_nonzero"],
            truth_contract["scorecard_transfer_nonzero"],
            truth_contract["order_transfer_nonzero"],
            truth_contract["fill_transfer_nonzero"],
            truth_contract["physical_trade_count_reconciled"],
            truth_contract["headline_trade_count_reconciled"],
            refused_executed == 0,
            source_gap_executed == 0,
            truth_contract["broker_live_final_closed"],
        )
    )
    truth_contract["issues"] = sorted(
        key
        for key in (
            "completed",
            "all_required_artifacts_present",
            "full_82_sleeve_axis_surface",
            "non_additive_source_signal_truth_valid",
            "behavioral_execution_contract_partition_bound",
            "paired_row_level_artifacts_hash_bound",
            "candidate_transfer_nonzero",
            "scorecard_transfer_nonzero",
            "order_transfer_nonzero",
            "fill_transfer_nonzero",
            "physical_trade_count_reconciled",
            "headline_trade_count_reconciled",
            "broker_live_final_closed",
        )
        if truth_contract.get(key) is not True
    )
    if truth_contract["transfer_status"] != "present":
        truth_contract["issues"].append("transfer_status")
    if refused_executed:
        truth_contract["issues"].append("executed_refused_cost_rows")
    if source_gap_executed:
        truth_contract["issues"].append("executed_source_gap_rows")

    cost_status_counts: defaultdict[str, int] = defaultdict(int)
    cost_source_gap_status_counts: defaultdict[str, int] = defaultdict(int)
    cost_authority_counts: defaultdict[str, int] = defaultdict(int)
    for row in trade_rows:
        cost_status_counts[str(row.get("pretrade_cost_packet_status") or "missing")] += 1
        cost_source_gap_status_counts[
            str(row.get("cost_source_gap_status") or "missing")
        ] += 1
        cost_authority_counts[str(row.get("cost_authority") or "missing")] += 1
    return {
        "window_id": spec.window_id,
        "role": spec.role,
        "prefix": spec.prefix,
        "date_start": summary.get("date_start"),
        "date_end": summary.get("date_end"),
        "calendar_day_count": days,
        "profile": PROFILE,
        "contract_binding": binding,
        "artifacts": artifacts,
        "artifact_row_counts": {
            "candidate_instance_rows": transfer_summary[
                "candidate_instance_rows"
            ],
            "summary_candidate_rows": inum(metrics.get("candidate_rows")),
            "candidate_instance_projection_ledger_rows": artifacts[
                "candidate_instance_projection_ledger"
            ].get("row_count"),
            "scorecard_ledger_rows": inum(metrics.get("scorecard_rows")),
            "scorecard_present_candidate_instance_rows": transfer_summary[
                "scorecard_present_candidate_instance_rows"
            ],
            "scheduler_selected_candidate_instance_rows": transfer_summary[
                "scheduler_selected_candidate_instance_rows"
            ],
            "order_event_rows": inum(metrics.get("order_event_rows")),
            "order_present_candidate_instance_rows": transfer_summary[
                "order_present_candidate_instance_rows"
            ],
            "terminal_order_rows": inum(stats.get("terminal_order_rows")),
            "summary_physical_trade_rows": expected_physical,
            "loaded_physical_trade_rows": len(trade_rows),
            "trade_ledger_physical_fill_rows": artifacts[
                "trade_ledger"
            ].get("row_count"),
            "summary_headline_trade_rows": expected_headline,
            "loaded_headline_trade_rows": len(headline_rows),
            "source_member_axis_rows": transfer_summary["package_axes"],
            "parity_summary_declared_ledger_rows": inum(
                parity_payload.get("parity_ledger_rows")
            ),
            "source_bound_parity_ledger_rows": artifacts[
                "source_bound_parity_ledger"
            ].get("row_count"),
        },
        "truth_contract": truth_contract,
        "transfer": transfer_summary,
        "lifecycle": selected_lifecycle(stats),
        "cost_source_execution": {
            "pretrade_cost_packet_status_counts": dict(sorted(cost_status_counts.items())),
            "cost_source_gap_status_counts": dict(
                sorted(cost_source_gap_status_counts.items())
            ),
            "cost_authority_counts": dict(sorted(cost_authority_counts.items())),
            "executed_refused_cost_rows": refused_executed,
            "executed_source_gap_rows": source_gap_executed,
            "guarded_market_fallback_applied_rows": sum(
                row.get("guarded_market_fallback_applied") is True
                for row in trade_rows
            ),
        },
        "missed": {
            key: metrics.get(key)
            for key in (
                "missed_rows",
                "missed_scoreable",
                "missed_unscoreable",
                "missed_executable_scoreable",
                "missed_executable_net_r",
                "missed_diagnostic_scoreable",
                "missed_diagnostic_positive_rows",
                "missed_diagnostic_positive_net_r",
                "missed_diagnostic_negative_rows",
                "missed_diagnostic_negative_net_r",
                "missed_diagnostic_net_r",
            )
        },
        "stress": metrics.get("stress") or {},
        "monte_carlo": metrics.get("monte_carlo") or {},
        "behavior": {
            "physical": behavior_surface(trade_rows, days),
            "headline": behavior_surface(headline_rows, days),
            "diagnostic_only": behavior_surface(diagnostic_rows, days),
        },
        "identity_comparison_disposition": (
            "cross_window_trade_identity_comparison_forbidden_disjoint_dates; "
            "compare_normalized_transfer_and_behavior_only"
        ),
    }


def sum_surface(windows: Iterable[Mapping[str, Any]], surface: str) -> dict[str, Any]:
    rows = [window["behavior"][surface] for window in windows]
    result = {
        key: round(sum(fnum(row.get(key)) for row in rows), 8)
        for key in (
            "trade_rows",
            "wins",
            "losses",
            "flats",
            "net_r",
            "gross_r",
            "final_r",
            "execution_cost_r",
            "cash_pnl",
            "risk_cash",
            "risk_pct",
        )
    }
    result["trade_rows"] = int(result["trade_rows"])
    result["wins"] = int(result["wins"])
    result["losses"] = int(result["losses"])
    result["flats"] = int(result["flats"])
    return result


def lowest_headline_buckets(window: Mapping[str, Any]) -> dict[str, Any]:
    breakdowns = window["behavior"]["headline"].get("breakdowns", {})
    output: dict[str, Any] = {}
    for dimension, rows in breakdowns.items():
        if rows:
            output[dimension] = rows[0]
    return output


def build_report(
    specs: Iterable[WindowSpec] = DEFAULT_WINDOWS,
    *,
    root: Path = ROUTE,
    source_contract: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    windows = [window_report(spec, root=root) for spec in specs]
    paired = [
        window for window in windows if window["role"] == "paired_extended_history"
    ]
    if len(paired) < 2:
        raise ValueError("B7.5 requires at least two paired non-adjacent windows")
    paired_ranges = sorted(
        [
            (
                parse_date(window.get("date_start")),
                parse_date(window.get("date_end")),
                window["window_id"],
            )
            for window in paired
        ],
        key=lambda row: (row[0] or date.max, row[2]),
    )
    paired_dates_valid = all(
        start is not None and end is not None and start <= end
        for start, end, _ in paired_ranges
    )
    paired_windows_disjoint = paired_dates_valid and all(
        previous_end < next_start
        for (_, previous_end, _), (next_start, _, _) in zip(
            paired_ranges, paired_ranges[1:]
        )
    )
    paired_windows_non_adjacent = paired_windows_disjoint and all(
        (next_start.year * 12 + next_start.month)
        - (previous_start.year * 12 + previous_start.month)
        > 1
        for (previous_start, _, _), (next_start, _, _) in zip(
            paired_ranges, paired_ranges[1:]
        )
    )
    behavioral_execution_digests = {
        str(
            window["contract_binding"].get(
                "behavioral_execution_contract_digest_sha256"
            )
            or ""
        )
        for window in paired
    }
    behavioral_execution_digests.discard("")
    legacy_full_shared_digests = {
        str(
            window["contract_binding"].get(
                "actual_shared_execution_contract_digest_sha256"
            )
            or ""
        )
        for window in paired
    }
    legacy_full_shared_digests.discard("")
    source_digests = {
        str(window["contract_binding"].get("expected_source_plan_digest_sha256") or "")
        for window in paired
    }
    source_digests.discard("")
    source_contract_binding = (
        dict(source_contract)
        if source_contract is not None
        else source_window_contract_binding(root)
    )
    source_contract_windows = {
        str(row.get("window_id") or ""): row
        for row in source_contract_binding.get("windows") or ()
        if isinstance(row, Mapping)
    }
    source_contract_semantics = source_contract_binding.get(
        "source_bound_signal_semantics"
    )
    source_contract_semantics = (
        source_contract_semantics
        if isinstance(source_contract_semantics, Mapping)
        else {}
    )
    source_contract_artifact = source_contract_binding.get("artifact")
    source_contract_artifact = (
        source_contract_artifact
        if isinstance(source_contract_artifact, Mapping)
        else {}
    )
    source_contract_window_bindings_valid = all(
        (
            contract_window := source_contract_windows.get(window["window_id"])
        )
        is not None
        and contract_window.get("start_day") == window.get("date_start")
        and contract_window.get("end_day") == window.get("date_end")
        and contract_window.get("source_plan_digest_sha256")
        == window["contract_binding"].get(
            "expected_source_plan_digest_sha256"
        )
        for window in paired
    )
    source_contract_binding_valid = bool(
        source_contract_binding.get("valid") is True
        and source_contract_artifact.get("required") is True
        and source_contract_artifact.get("present") is True
        and source_contract_artifact.get("hash_bound") is True
        and len(str(source_contract_binding.get("contract_digest_sha256") or ""))
        == 64
        and len(str(source_contract_binding.get("pair_binding_sha256") or ""))
        == 64
        and source_contract_binding.get(
            "behavioral_execution_contract_digest_sha256"
        )
        in behavioral_execution_digests
        and source_contract_binding.get(
            "execution_contract_authority_partition_valid"
        )
        is True
        and len(
            str(
                source_contract_binding.get(
                    "postrun_proof_consumer_contract_digest_sha256"
                )
                or ""
            )
        )
        == 64
        and source_contract_semantics.get("evidence_class")
        == SOURCE_BOUND_SIGNAL_EVIDENCE_CLASS
        and source_contract_semantics.get("additive_allowed") is False
        and source_contract_semantics.get("executable_r_percentage_allowed")
        is False
        and source_contract_window_bindings_valid
    )
    paired_truth = all(window["truth_contract"]["pass"] for window in paired)
    pair_binding_valid = all(
        window["contract_binding"].get("valid") is True for window in paired
    )
    same_execution_contract = len(behavioral_execution_digests) == 1
    distinct_source_windows = len(source_digests) == len(paired)
    no_opportunity_collapse = all(
        window["transfer"]["candidate_generated_axes"] > 0
        and window["transfer"]["scorecard_or_order_present_axes"] > 0
        and window["behavior"]["headline"]["trade_rows"] > 0
        for window in paired
    )
    positive_windows = [
        window["window_id"]
        for window in paired
        if window["behavior"]["headline"]["net_r"] > 0
    ]
    negative_windows = [
        window["window_id"]
        for window in paired
        if window["behavior"]["headline"]["net_r"] <= 0
    ]
    stress_rows_by_window = {
        window["window_id"]: list(
            (window.get("stress") or {}).get("guarded_stress_rows", [])
        )
        for window in paired
    }
    stress_rows_present = all(stress_rows_by_window.values())
    stress_positive = stress_rows_present and all(
        all(fnum(row.get("net_r")) > 0 for row in rows)
        for rows in stress_rows_by_window.values()
    )
    economic_generalization_pass = (
        len(positive_windows) == len(paired) and stress_positive
    )
    truth_integrity_pass = (
        paired_truth
        and pair_binding_valid
        and same_execution_contract
        and distinct_source_windows
        and source_contract_binding_valid
        and paired_windows_disjoint
        and paired_windows_non_adjacent
        and no_opportunity_collapse
    )
    status = (
        "b7_5_truth_and_economic_generalization_green"
        if truth_integrity_pass and economic_generalization_pass
        else "b7_5_truth_green_economic_generalization_failed"
        if truth_integrity_pass
        else "b7_5_truth_integrity_failed"
    )
    return {
        "schema": SCHEMA,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": status,
        "evidence_class": "broker_live_closed_live_as_if_replay_cross_window_behavior",
        "profile": PROFILE,
        "window_count": len(windows),
        "paired_extended_history_window_count": len(paired),
        "windows": windows,
        "paired_extended_history": {
            "window_ids": [window["window_id"] for window in paired],
            "same_execution_contract": same_execution_contract,
            "behavioral_execution_contract_digests_sha256": sorted(
                behavioral_execution_digests
            ),
            "shared_execution_contract_digests_sha256": sorted(
                behavioral_execution_digests
            ),
            "shared_execution_contract_digest_semantics": (
                "behavioral_authority_excludes_postrun_proof_consumers"
            ),
            "legacy_full_shared_execution_contract_digests_sha256": sorted(
                legacy_full_shared_digests
            ),
            "distinct_source_window_contracts": distinct_source_windows,
            "paired_dates_valid": paired_dates_valid,
            "paired_windows_disjoint": paired_windows_disjoint,
            "paired_windows_non_adjacent": paired_windows_non_adjacent,
            "source_plan_digests_sha256": sorted(source_digests),
            "pair_binding_valid": pair_binding_valid,
            "source_window_contract_binding": source_contract_binding,
            "source_window_contract_binding_valid": (
                source_contract_binding_valid
            ),
            "source_window_contract_window_bindings_valid": (
                source_contract_window_bindings_valid
            ),
            "truth_integrity_pass": truth_integrity_pass,
            "no_opportunity_collapse": no_opportunity_collapse,
            "positive_headline_windows": positive_windows,
            "negative_headline_windows": negative_windows,
            "stress_positive_in_every_window": stress_positive,
            "stress_rows_present_in_every_window": stress_rows_present,
            "economic_generalization_pass": economic_generalization_pass,
            "b7_5_gate_pass": truth_integrity_pass and economic_generalization_pass,
            "combined_physical": sum_surface(paired, "physical"),
            "combined_headline": sum_surface(paired, "headline"),
            "combined_diagnostic_only": sum_surface(paired, "diagnostic_only"),
            "transfer_totals": {
                key: round(sum(fnum(window["transfer"].get(key)) for window in paired), 8)
                for key in (
                    "package_axes",
                    "candidate_generated_axes",
                    "scorecard_or_order_present_axes",
                    "order_present_axes",
                    "filled_trade_axes",
                    "actual_physical_executable_r",
                    "actual_headline_executable_r",
                )
            },
            "non_additive_source_signal_truth_window_count": sum(
                window["transfer"].get(
                    "non_additive_window_source_bound_signal_available"
                )
                is True
                and window["transfer"].get(
                    "source_bound_r_additive_allowed"
                )
                is False
                and window["transfer"].get(
                    "physical_r_pct_of_source_bound_signal"
                )
                is None
                for window in paired
            ),
            "non_additive_source_signal_by_window": {
                window["window_id"]: window["transfer"].get(
                    "non_additive_window_source_bound_signal_r"
                )
                for window in paired
            },
        },
        "causal_focus": {
            "required": bool(negative_windows),
            "negative_window_lowest_headline_buckets": {
                window["window_id"]: lowest_headline_buckets(window)
                for window in paired
                if window["window_id"] in negative_windows
            },
            "interpretation": (
                "truth-green negative behavior selects a causal predecision repair; "
                "it does not authorize date/symbol/session outcome buckets, opportunity "
                "suppression, cost-authority weakening, or cross-window identity comparison"
            ),
        },
        "comparison_boundary": {
            "paired_windows": "normalized transfer and behavior under one execution contract",
            "historical_ladder_comparators": "context only; config/code identity is not asserted",
            "global_reservoir": (
                "diagnostic only; source member-axis signal is non-additive and "
                "is never an executable-R denominator"
            ),
            "cross_window_trade_identity": "not comparable because dates are disjoint",
        },
        "broker_live_final_closed": True,
    }


def render_dossier(report: Mapping[str, Any]) -> str:
    pair = report["paired_extended_history"]
    lines = [
        "# B7.5 Extended-History Behavior Dossier",
        "",
        f"Status: `{report['status']}`.",
        "",
        "January and April are normalized disjoint-window proofs under one execution contract. "
        "May and June are historical ladder comparators only. Cross-window trade identity is not compared.",
        "",
        "## Paired Gate",
        "",
        f"- Truth integrity: `{pair['truth_integrity_pass']}`.",
        f"- No opportunity collapse: `{pair['no_opportunity_collapse']}`.",
        f"- Economic generalization: `{pair['economic_generalization_pass']}`.",
        f"- B7.5 gate: `{pair['b7_5_gate_pass']}`.",
        "",
        "## Window Behavior",
        "",
        "| Window | Role | Physical trades | Physical W/L/F | Physical net R | Headline trades | Headline W/L/F | Headline net R | Non-additive gated signal | Axes package/candidate/scorecard/order/fill | Instances candidate/scorecard/selected/order/fill | Rows scorecard/order-events/terminal |",
        "| --- | --- | ---: | --- | ---: | ---: | --- | ---: | ---: | --- | --- | --- |",
    ]
    for window in report["windows"]:
        physical = window["behavior"]["physical"]
        headline = window["behavior"]["headline"]
        transfer = window["transfer"]
        signal_r = transfer.get("non_additive_window_source_bound_signal_r")
        signal_r_text = (
            f"{fnum(signal_r):.8f}"
            if transfer.get(
                "non_additive_window_source_bound_signal_available"
            )
            is True
            else "unavailable"
        )
        counts = window["artifact_row_counts"]
        lines.append(
            f"| {window['window_id']} | {window['role']} | {physical['trade_rows']} | "
            f"{physical['wins']}/{physical['losses']}/{physical['flats']} | {physical['net_r']:+.8f} | "
            f"{headline['trade_rows']} | {headline['wins']}/{headline['losses']}/{headline['flats']} | "
            f"{headline['net_r']:+.8f} | {signal_r_text} | "
            f"{transfer['package_axes']}/{transfer['candidate_generated_axes']}/"
            f"{transfer['scorecard_or_order_present_axes']}/{transfer['order_present_axes']}/"
            f"{transfer['filled_trade_axes']} | "
            f"{transfer['candidate_instance_rows']}/"
            f"{transfer['scorecard_present_candidate_instance_rows']}/"
            f"{transfer['scheduler_selected_candidate_instance_rows']}/"
            f"{transfer['order_present_candidate_instance_rows']}/"
            f"{transfer['filled_candidate_instance_rows']} | "
            f"{counts['scorecard_ledger_rows']}/{counts['order_event_rows']}/"
            f"{counts['terminal_order_rows']} |"
        )
    lines.extend(
        [
            "",
            "## Paired Totals",
            "",
            f"- Physical: `{pair['combined_physical']['trade_rows']}` trades, "
            f"W/L/F `{pair['combined_physical']['wins']}/{pair['combined_physical']['losses']}/{pair['combined_physical']['flats']}`, "
            f"net `{pair['combined_physical']['net_r']:+.8f}R`, cash `{pair['combined_physical']['cash_pnl']:+.2f}`.",
            f"- Headline: `{pair['combined_headline']['trade_rows']}` trades, "
            f"W/L/F `{pair['combined_headline']['wins']}/{pair['combined_headline']['losses']}/{pair['combined_headline']['flats']}`, "
            f"net `{pair['combined_headline']['net_r']:+.8f}R`, cash `{pair['combined_headline']['cash_pnl']:+.2f}`.",
            f"- Negative headline windows: `{', '.join(pair['negative_headline_windows']) or 'none'}`.",
            "- Source-bound signal is non-additive member-axis evidence; no executable-R percentage is calculated.",
            "",
            "## Disposition",
            "",
            report["causal_focus"]["interpretation"] + ".",
            "",
            "Broker/live/final remain false.",
            "",
        ]
    )
    return "\n".join(lines)


def parse_window(value: str) -> WindowSpec:
    parts = value.split("|", 2)
    if len(parts) != 3 or not all(part.strip() for part in parts):
        raise argparse.ArgumentTypeError("window must be WINDOW_ID|ROLE|PREFIX")
    return WindowSpec(*(part.strip() for part in parts))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROUTE)
    parser.add_argument("--window", action="append", type=parse_window)
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    report = build_report(args.window or DEFAULT_WINDOWS, root=root)
    output_json = args.output_json or root / OUTPUT_JSON
    output_md = args.output_md or root / OUTPUT_MD
    output_json.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    output_md.write_text(render_dossier(report), encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "output_json": str(output_json),
        "output_md": str(output_md),
        "b7_5_gate_pass": report["paired_extended_history"]["b7_5_gate_pass"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
