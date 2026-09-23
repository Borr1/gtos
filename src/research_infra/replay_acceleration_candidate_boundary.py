"""Outcome-blind instrumentation for the replay candidate sharing boundary.

This module never executes a policy arm.  It invokes the production closed-bar
candidate generator four times with structurally bound factorial projections,
records every configuration read, and proves the last shareable immutable
stage.  Factor binding and mutable portfolio stages are classified arm-local.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import resource
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterable, Iterator, Mapping

from src.components.broader_origin_generators import (
    generate_live_broader_origin_candidates,
)
from src.components.v4_live_replay_decision_core import V4DecisionCycleCore
from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


SCHEMA = "gtos.replay_acceleration.candidate_boundary_result.v1"
PROBE_SCHEMA = "gtos.replay_acceleration.candidate_boundary_probe.v1"
ARM_ORDER = ("S0R0", "S1R0", "S0R1", "S1R1")
FACTOR_PREFIX = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_RUNTIME_PREFIX
FACTOR_PATH_PREFIX = f"gtos_vnext_runtime.{FACTOR_PREFIX}"
SOURCE_RESULT_PATH = Path(
    "research/operations/replay_acceleration_bounded_slice_2026_07_19/"
    "BOUNDED_EQUIVALENCE_RESULT.json"
)
NORMALIZATION_RESULT_PATH = Path(
    "research/operations/replay_acceleration_normalized_slice_2026_07_19/"
    "NORMALIZATION_EQUIVALENCE_RESULT.json"
)
SOURCE_GATE = "BOUNDED_EQUIVALENCE_ACCEPTED_FOR_REPLAY_SLICE"
NORMALIZATION_GATE = "NORMALIZATION_EQUIVALENCE_ACCEPTED"


class CandidateBoundaryError(RuntimeError):
    """Stable fail-closed candidate-boundary rejection."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ReadTrackingDict(dict[str, Any]):
    """A real ``dict`` that records nested mapping reads without changing values."""

    def __init__(
        self,
        value: Mapping[str, Any],
        *,
        reads: set[str] | None = None,
        prefix: str = "",
    ) -> None:
        super().__init__()
        self._reads = reads if reads is not None else set()
        self._prefix = prefix
        for key, item in value.items():
            child_path = self._path(key)
            if isinstance(item, Mapping):
                item = ReadTrackingDict(item, reads=self._reads, prefix=child_path)
            dict.__setitem__(self, str(key), item)

    @property
    def reads(self) -> set[str]:
        return self._reads

    def _path(self, key: object) -> str:
        text = str(key)
        return f"{self._prefix}.{text}" if self._prefix else text

    def _mark(self, key: object) -> None:
        self._reads.add(self._path(key))

    def __getitem__(self, key: str) -> Any:
        self._mark(key)
        return dict.__getitem__(self, key)

    def get(self, key: str, default: Any = None) -> Any:
        self._mark(key)
        return dict.get(self, key, default)

    def __contains__(self, key: object) -> bool:
        self._mark(key)
        return dict.__contains__(self, key)

    def __iter__(self) -> Iterator[str]:
        self._reads.add(f"{self._prefix}.*" if self._prefix else "*")
        return dict.__iter__(self)

    def keys(self):  # type: ignore[no-untyped-def]
        self._reads.add(f"{self._prefix}.*" if self._prefix else "*")
        return dict.keys(self)

    def items(self):  # type: ignore[no-untyped-def]
        self._reads.add(f"{self._prefix}.*" if self._prefix else "*")
        return dict.items(self)

    def values(self):  # type: ignore[no-untyped-def]
        self._reads.add(f"{self._prefix}.*" if self._prefix else "*")
        return dict.values(self)


def _arm_config(arm_id: str) -> dict[str, Any]:
    if arm_id not in ARM_ORDER:
        raise CandidateBoundaryError("unknown_arm_projection")
    selection_factor, sizing_factor = timewarp.B7_5_SELECTION_SIZING_FACTORIAL_ARM_FACTORS[
        arm_id
    ]
    selection_mode = (
        "neutral_hash_hard_eligible"
        if selection_factor == "S0"
        else "quality_ranked_current"
    )
    sizing_mode = (
        "fixed_equal_account_risk" if sizing_factor == "R0" else "dynamic_runtime"
    )
    denominator = {
        "initial_equity_cash": (
            timewarp.B7_5_SELECTION_SIZING_FACTORIAL_INITIAL_EQUITY_CASH
        ),
        "fixed_account_risk_unit_pct": (
            timewarp.B7_5_SELECTION_SIZING_FACTORIAL_FIXED_ACCOUNT_RISK_UNIT_PCT
        ),
        "fixed_account_risk_unit_cash": (
            timewarp.B7_5_SELECTION_SIZING_FACTORIAL_FIXED_ACCOUNT_RISK_UNIT_CASH
        ),
        "fixed_denominator_portfolio_r_cash": (
            timewarp.B7_5_SELECTION_SIZING_FACTORIAL_FIXED_DENOMINATOR_PORTFOLIO_R_CASH
        ),
    }
    matched = dict(timewarp.B7_5_SELECTION_SIZING_FACTORIAL_MATCHED_RISK)
    protocol = {"denominator": denominator, "matched_risk": matched}
    protocol_digest = timewarp.stable_sha256(protocol)
    identity = {
        "decision_contract_sha256": hashlib.sha256(
            b"candidate-boundary-decision-contract"
        ).hexdigest(),
        "common_execution_input_digest_sha256": hashlib.sha256(
            b"candidate-boundary-common-input"
        ).hexdigest(),
        "arm_id": arm_id,
        "arm_fingerprint_sha256": hashlib.sha256(
            f"candidate-boundary:{arm_id}".encode("ascii")
        ).hexdigest(),
        "selection_factor": selection_factor,
        "sizing_factor": sizing_factor,
        "selection_mode": selection_mode,
        "sizing_mode": sizing_mode,
        "neutral_selection_seed_sha256": (
            timewarp.B7_5_SELECTION_SIZING_FACTORIAL_SEALED_NEUTRAL_SEED_SHA256
        ),
        "fixed_account_risk_unit_pct": denominator["fixed_account_risk_unit_pct"],
    }
    binding_payload = timewarp.b7_5_selection_sizing_factorial_binding_payload(
        **identity,
        protocol_economics=protocol,
        protocol_economics_digest_sha256=protocol_digest,
        denominator=denominator,
        matched_risk=matched,
        **{
            key: value
            for key, value in denominator.items()
            if key != "fixed_account_risk_unit_pct"
        },
        **matched,
    )
    prefix = FACTOR_PREFIX
    runtime: dict[str, Any] = {
        "prop_safe_selector_initial_balance": denominator["initial_equity_cash"],
        "prop_safe_selector_external_daily_loss_limit_pct": matched[
            "daily_accepted_risk_pct_cap"
        ],
        "scheduler_v4_best_trade_allocator_portfolio_ceiling_pct": matched[
            "peak_open_plus_pending_risk_pct_cap"
        ],
        "scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct": matched[
            "cluster_risk_pct_cap"
        ],
        "scheduler_v4_best_trade_allocator_dynamic_budget_"
        "opening_window_max_total_risk_pct": matched["opening_window_risk_pct_cap"],
        "scheduler_v4_best_trade_allocator_dynamic_budget_"
        "opening_window_reserve_enabled": True,
        f"{prefix}binding_valid": True,
        f"{prefix}binding_payload_sha256": timewarp.stable_sha256(binding_payload),
        f"{prefix}protocol_economics_digest_sha256": protocol_digest,
        f"{prefix}uses_outcome_fields": False,
        f"{prefix}live_broker_authority": False,
        f"{prefix}broker_mutation_enabled": False,
        f"{prefix}final_selection_claim": False,
    }
    runtime.update({f"{prefix}{key}": value for key, value in identity.items()})
    runtime.update({f"{prefix}{key}": value for key, value in denominator.items()})
    runtime.update({f"{prefix}{key}": value for key, value in matched.items()})
    return {
        "risk": {"risk_per_trade_pct": 0.50, "max_daily_loss_pct": 4.0, "min_rr": 1.5},
        "model_a": {"enabled_frameworks": []},
        "broad_live_as_if_replay_harness": {
            "live_broker_authority": False,
            "broker_mutation_enabled": False,
            "final_selection_claim": False,
        },
        "gtos_vnext_runtime": runtime,
    }


def _closed_bar_probe() -> tuple[dict[str, Any], datetime]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bars: list[dict[str, Any]] = []
    for index in range(80):
        base = 100.0 + index * 0.03 + ((index % 9) - 4) * 0.05
        if index == 78:
            base -= 1.5
        if index == 79:
            base += 0.8
        bars.append(
            {
                "time": (start + timedelta(minutes=15 * index)).isoformat(),
                "open": base,
                "high": base + 0.35,
                "low": base - 0.35,
                "close": base + 0.08,
                "volume": 100 + index,
            }
        )
    return (
        {"symbol": "XAUUSD", "candles": {"M15": bars}},
        start + timedelta(minutes=15 * len(bars)),
    )


def _factor_reads(reads: Iterable[str]) -> list[str]:
    return sorted(path for path in reads if FACTOR_PATH_PREFIX in path)


def _safe_binding_projection(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "arm_id": binding.get("arm_id"),
        "selection_factor": binding.get("selection_factor"),
        "sizing_factor": binding.get("sizing_factor"),
        "selection_mode": binding.get("selection_mode"),
        "sizing_mode": binding.get("sizing_mode"),
        "enabled": binding.get("enabled"),
        "valid": binding.get("valid"),
    }


def enforce_candidate_base_shareability(
    *,
    cross_symbol_barrier_required: bool,
    candidate_roots_equal: bool,
    candidate_read_sets_equal: bool,
    candidate_factor_reads: Iterable[str],
    mutable_state_read: bool,
) -> None:
    if not cross_symbol_barrier_required:
        raise CandidateBoundaryError("cross_symbol_barrier_missing")
    if not candidate_roots_equal:
        raise CandidateBoundaryError("candidate_base_root_mismatch")
    if not candidate_read_sets_equal:
        raise CandidateBoundaryError("candidate_base_read_set_mismatch")
    if list(candidate_factor_reads):
        raise CandidateBoundaryError("candidate_factor_read_detected")
    if mutable_state_read:
        raise CandidateBoundaryError("candidate_mutable_state_read_detected")


def run_candidate_boundary_failure_injections() -> list[dict[str, str]]:
    cases: tuple[tuple[str, dict[str, Any], str], ...] = (
        (
            "cross_symbol_barrier_removed",
            {"cross_symbol_barrier_required": False},
            "cross_symbol_barrier_missing",
        ),
        (
            "candidate_payload_changed",
            {"candidate_roots_equal": False},
            "candidate_base_root_mismatch",
        ),
        (
            "candidate_read_set_changed",
            {"candidate_read_sets_equal": False},
            "candidate_base_read_set_mismatch",
        ),
        (
            "factor_read_added",
            {"candidate_factor_reads": ["factor.path"]},
            "candidate_factor_read_detected",
        ),
        (
            "mutable_state_read_added",
            {"mutable_state_read": True},
            "candidate_mutable_state_read_detected",
        ),
    )
    verdicts: list[dict[str, str]] = []
    for name, mutation, expected in cases:
        facts: dict[str, Any] = {
            "cross_symbol_barrier_required": True,
            "candidate_roots_equal": True,
            "candidate_read_sets_equal": True,
            "candidate_factor_reads": [],
            "mutable_state_read": False,
        }
        facts.update(mutation)
        try:
            enforce_candidate_base_shareability(**facts)
        except CandidateBoundaryError as exc:
            if str(exc) != expected:
                raise CandidateBoundaryError("failure_injection_wrong_rejection") from exc
            verdicts.append({"case": name, "status": "REJECTED_AS_REQUIRED", "code": expected})
        else:
            raise CandidateBoundaryError("failure_injection_not_rejected")
    return verdicts


def _static_boundary_evidence() -> dict[str, Any]:
    generator_signature = inspect.signature(generate_live_broader_origin_candidates)
    generator_source = inspect.getsource(generate_live_broader_origin_candidates)
    core_source = inspect.getsource(V4DecisionCycleCore.generate_candidates)
    scheduler_source = inspect.getsource(timewarp.materialize_scheduler_window)
    campaign_source = inspect.getsource(timewarp.run_campaign)
    generator_parameters = set(generator_signature.parameters)
    mutable_names = {"account", "open_positions", "pending_orders", "reservations"}
    generator_mutable_parameters = sorted(generator_parameters & mutable_names)
    raw_barrier = campaign_source.find(
        'cross_asset_raw_data = {"raw_data_by_symbol": raw_by_symbol}'
    )
    symbol_loop_marker = "for symbol in INCLUDED_SYMBOLS:"
    first_symbol_loop = campaign_source.rfind(symbol_loop_marker, 0, raw_barrier)
    second_symbol_loop = campaign_source.find(symbol_loop_marker, raw_barrier)
    cross_symbol_barrier_proven = (
        first_symbol_loop >= 0
        and raw_barrier > first_symbol_loop
        and second_symbol_loop > raw_barrier
    )
    if generator_mutable_parameters:
        raise CandidateBoundaryError("generator_mutable_state_signature_detected")
    if not cross_symbol_barrier_proven:
        raise CandidateBoundaryError("run_campaign_cross_symbol_barrier_not_proven")
    if "b7_5_selection_sizing_factorial_runtime_binding" not in scheduler_source:
        raise CandidateBoundaryError("scheduler_factor_binding_call_missing")
    if 'factorial_binding.get("sizing_factor") == "R0"' not in scheduler_source:
        raise CandidateBoundaryError("scheduler_r0_eligibility_branch_missing")
    return {
        "generator_source_sha256": hashlib.sha256(
            generator_source.encode("utf-8")
        ).hexdigest(),
        "decision_core_generation_source_sha256": hashlib.sha256(
            core_source.encode("utf-8")
        ).hexdigest(),
        "scheduler_source_sha256": hashlib.sha256(
            scheduler_source.encode("utf-8")
        ).hexdigest(),
        "campaign_source_sha256": hashlib.sha256(
            campaign_source.encode("utf-8")
        ).hexdigest(),
        "generator_mutable_state_parameters": generator_mutable_parameters,
        "cross_symbol_barrier_proven": cross_symbol_barrier_proven,
        "scheduler_factor_binding_call_proven": True,
        "scheduler_r0_eligibility_branch_proven": True,
    }


def probe_candidate_boundary() -> dict[str, Any]:
    raw_data, now_utc = _closed_bar_probe()
    arms: dict[str, dict[str, Any]] = {}
    candidate_roots: list[str] = []
    candidate_read_sets: list[tuple[str, ...]] = []
    candidate_counts: list[int] = []
    candidate_factor_reads: set[str] = set()
    for arm_id in ARM_ORDER:
        plain_config = _arm_config(arm_id)
        candidate_config = ReadTrackingDict(plain_config)
        core = V4DecisionCycleCore(config=candidate_config)
        generated = core.generate_candidates(
            raw_data=raw_data,
            mso=SimpleNamespace(timeframes={}),
            symbol="XAUUSD",
            kill_zone="london",
            now_utc=now_utc,
        )
        candidate_root = stable_sha256(generated)
        candidate_read_set = tuple(sorted(candidate_config.reads))
        factor_reads = _factor_reads(candidate_read_set)
        candidate_factor_reads.update(factor_reads)

        scheduler_config = ReadTrackingDict(plain_config)
        binding = timewarp.b7_5_selection_sizing_factorial_runtime_binding(
            scheduler_config,
            fail_on_invalid=True,
        )
        scheduler_factor_reads = _factor_reads(scheduler_config.reads)
        if not scheduler_factor_reads:
            raise CandidateBoundaryError("scheduler_factor_read_set_empty")
        projection = _safe_binding_projection(binding)
        arms[arm_id] = {
            "candidate_base_root_sha256": candidate_root,
            "candidate_base_count": len(generated),
            "candidate_base_config_read_set": list(candidate_read_set),
            "candidate_base_factor_read_set": factor_reads,
            "factor_binding_valid": bool(binding.get("valid")),
            "scheduler_factor_read_set": scheduler_factor_reads,
            "scheduler_factor_projection_sha256": stable_sha256(projection),
        }
        candidate_roots.append(candidate_root)
        candidate_read_sets.append(candidate_read_set)
        candidate_counts.append(len(generated))

    roots_equal = len(set(candidate_roots)) == 1
    read_sets_equal = len(set(candidate_read_sets)) == 1
    counts_equal = len(set(candidate_counts)) == 1
    count = candidate_counts[0] if counts_equal else -1
    if count <= 0:
        raise CandidateBoundaryError("candidate_probe_empty")
    enforce_candidate_base_shareability(
        cross_symbol_barrier_required=True,
        candidate_roots_equal=roots_equal,
        candidate_read_sets_equal=read_sets_equal,
        candidate_factor_reads=candidate_factor_reads,
        mutable_state_read=False,
    )
    static_evidence = _static_boundary_evidence()
    return {
        "schema": PROBE_SCHEMA,
        "arm_order": list(ARM_ORDER),
        "arms": arms,
        "candidate_base_count": count,
        "candidate_base_roots_equal": roots_equal,
        "candidate_base_read_sets_equal": read_sets_equal,
        "candidate_base_factor_read_intersection": sorted(candidate_factor_reads),
        "shared_boundary_stage": "candidate_base_materialized",
        "cross_symbol_barrier_required": True,
        "stage_classification": {
            "normalized_source": "shared_immutable",
            "closed_bar_snapshot": "shared_before_cross_symbol_barrier",
            "candidate_origin_generation": "shared_after_read_set_and_root_equality",
            "candidate_base_materialization": "shared_after_read_set_and_root_equality",
            "candidate_evaluation": "arm_local",
            "scheduler_eligibility": "arm_local",
            "risk_and_order_materialization": "arm_local",
            "portfolio_lifecycle": "arm_local",
        },
        "mutable_state_surfaces": [
            "account",
            "open_positions",
            "pending_orders",
            "reservations",
        ],
        "static_boundary_evidence": static_evidence,
        "successor_arm_execution_launched": False,
        "policy_output_persisted": False,
    }


def _accepted_artifact_identity(path: Path, expected_gate: str) -> dict[str, Any]:
    payload = json.loads(path.read_bytes())
    if payload.get("gate") != expected_gate or payload.get("status") != "ACCEPTED":
        raise CandidateBoundaryError("accepted_predecessor_gate_missing")
    root = str(payload.get("result_root_sha256") or "")
    if len(root) != 64:
        raise CandidateBoundaryError("accepted_predecessor_root_invalid")
    return {
        "path": path.as_posix(),
        "file_sha256": file_sha256(path),
        "result_root_sha256": root,
        "gate": expected_gate,
    }


def _resource_snapshot() -> dict[str, int]:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "user_ns": int(usage.ru_utime * 1_000_000_000),
        "system_ns": int(usage.ru_stime * 1_000_000_000),
        "max_rss_native": int(usage.ru_maxrss),
        "minor_page_faults": int(usage.ru_minflt),
        "major_page_faults": int(usage.ru_majflt),
        "blocks_read": int(usage.ru_inblock),
        "blocks_written": int(usage.ru_oublock),
    }


def _resource_delta(before: Mapping[str, int], after: Mapping[str, int]) -> dict[str, Any]:
    return {
        "user_ns": after["user_ns"] - before["user_ns"],
        "system_ns": after["system_ns"] - before["system_ns"],
        "peak_rss_native": after["max_rss_native"],
        "peak_rss_unit": "bytes_on_darwin_kib_elsewhere",
        "minor_page_faults": after["minor_page_faults"] - before["minor_page_faults"],
        "major_page_faults": after["major_page_faults"] - before["major_page_faults"],
        "blocks_read": after["blocks_read"] - before["blocks_read"],
        "blocks_written": after["blocks_written"] - before["blocks_written"],
    }


def build_candidate_boundary_result(
    *, command_receipt: list[str] | None = None
) -> dict[str, Any]:
    before = _resource_snapshot()
    wall_start = time.perf_counter_ns()
    source_identity = _accepted_artifact_identity(SOURCE_RESULT_PATH, SOURCE_GATE)
    normalization_identity = _accepted_artifact_identity(
        NORMALIZATION_RESULT_PATH, NORMALIZATION_GATE
    )
    probe = probe_candidate_boundary()
    wall_ns = time.perf_counter_ns() - wall_start
    after = _resource_snapshot()
    writer_path = Path(__file__).resolve()
    verifier_path = writer_path.with_name(
        "replay_acceleration_candidate_boundary_verifier.py"
    )
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "status": "ACCEPTED",
        "gate": "CANDIDATE_BASE_BOUNDARY_ACCEPTED",
        "accepted_predecessors": {
            "source": source_identity,
            "normalization": normalization_identity,
        },
        "candidate_probe": probe,
        "failure_injections": run_candidate_boundary_failure_injections(),
        "code_identity": {
            "writer_path": writer_path.relative_to(Path.cwd()).as_posix(),
            "writer_sha256": file_sha256(writer_path),
            "independent_verifier_path": verifier_path.relative_to(Path.cwd()).as_posix(),
            "independent_verifier_sha256": file_sha256(verifier_path),
        },
        "measurement": {
            "scope": "candidate_boundary_instrumentation_only",
            "wall_ns": wall_ns,
            **_resource_delta(before, after),
            "scratch_bytes": 0,
            "whole_replay_speed_claim": False,
        },
        "exact_command_receipt": command_receipt or [sys.executable, *sys.argv],
        "outcome_blind_structural_only": True,
        "policy_execution_entered": False,
        "successor_arm_execution_launched": False,
    }
    payload["result_root_sha256"] = stable_sha256(payload)
    return payload


def write_candidate_boundary_result(
    path: Path, *, command_receipt: list[str] | None = None
) -> dict[str, Any]:
    result = build_candidate_boundary_result(command_receipt=command_receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_bytes(canonical_bytes(result) + b"\n")
    os.replace(temporary, path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    receipt = [sys.executable, "-m", __name__, "--output", args.output.as_posix()]
    result = write_candidate_boundary_result(args.output, command_receipt=receipt)
    print(
        json.dumps(
            {
                "gate": result["gate"],
                "result_root_sha256": result["result_root_sha256"],
                "output": args.output.as_posix(),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
