"""Shared V4 decision-cycle surface for production and replay.

The core owns side-effect-free decision-cycle stages that can be called by the
live orchestrator and by replay adapters. Broker mutation, account mutation,
and process lifecycle remain outside this module.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, MutableMapping
from typing import Any

from src.components.broader_origin_generators import (
    generate_live_broader_origin_candidates,
)


PRODUCTION_CORE_IMPORT_PATH = "src.components.v4_live_replay_decision_core.V4DecisionCycleCore"

_CANDIDATE_WINDOW_SUMMARY_FIELDS = (
    "candidate_id",
    "symbol",
    "broker_symbol",
    "side",
    "direction",
    "session",
    "kill_zone",
    "route_session",
    "session_bucket",
    "origin_family",
    "candidate_origin_family",
    "framework",
    "route_family",
    "candle_open_utc",
    "candle_close_utc",
    "timeframe",
    "market_timeframe",
    "source_window_complete",
    "source_path_feature_status",
    "live_generation_status",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "risk_reward_ratio",
    "requested_risk_pct",
    "selected_cell_risk_pct",
    "risk_pct",
    "candidate_probability",
    "probability",
    "candidate_ev_r",
    "ev_r",
    "EV",
    "expectancy_r",
    "broker_net_expectancy_r",
    "expected_cost_r",
    "cost_r",
    "candidate_expected_net_r",
    "expected_net_r",
    "stress_expectancy_r",
    "fill_probability",
    "heuristic_fill_probability",
    "predecision_limit_fillability",
    "confluence_score",
    "source_completeness",
    "source_completeness_status",
    "candidate_decision_quality_field_sources",
    "candidate_decision_quality_alias_status",
    "candidate_decision_quality_source_boundary",
    "no_leak_status",
    "utc_hour_bucket",
)


def summarize_decision_window_candidate(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Return the stable live/replay scheduler-window candidate summary."""

    summary = {
        field: candidate.get(field)
        for field in _CANDIDATE_WINDOW_SUMMARY_FIELDS
        if field in candidate
    }
    trade_parameters = candidate.get("trade_parameters")
    if isinstance(trade_parameters, Mapping):
        summary["trade_parameters"] = dict(trade_parameters)
    source_fields = candidate.get("source_fields")
    if isinstance(source_fields, Mapping):
        summary["source_fields"] = dict(source_fields)
    return summary


class V4DecisionCycleCore:
    """Production-owned V4 decision-cycle core called by live and replay paths."""

    core_id = "V4DecisionCycleCore"
    production_import_path = PRODUCTION_CORE_IMPORT_PATH
    surface_contract = {
        "decision_cycle_core": PRODUCTION_CORE_IMPORT_PATH,
        "candidate_generation": (
            "src.components.broader_origin_generators."
            "generate_live_broader_origin_candidates"
        ),
        "decision_window_summary": (
            "src.components.v4_live_replay_decision_core."
            "summarize_decision_window_candidate"
        ),
        "production_call_stage": (
            "src.components.orchestrator.SessionOrchestrator."
            "_process_vnext_broader_origin_candidates"
        ),
        "replay_call_stage": (
            "src.research_infra.v4_timewarp_simulated_live_research_loop.run_campaign"
        ),
        "broker_mutation": False,
        "paid_api": False,
        "remote_push": False,
    }

    def __init__(
        self,
        *,
        config: Mapping[str, Any],
        sources: Mapping[str, Mapping[str, Any]] | None = None,
        candidate_evaluator: Callable[..., Mapping[str, Any]] | None = None,
        scheduler_allocator: Callable[..., Mapping[str, Any]] | None = None,
        candidate_generator: Callable[..., Iterable[Mapping[str, Any]]] = (
            generate_live_broader_origin_candidates
        ),
    ):
        self.config = config
        self.sources = sources
        self._candidate_evaluator = candidate_evaluator
        self._scheduler_allocator = scheduler_allocator
        self._candidate_generator = candidate_generator
        self.last_candidate_generation_audit: dict[str, Any] = {}

    def generate_candidates(
        self,
        *,
        raw_data: Mapping[str, Any],
        mso: Any,
        symbol: str,
        kill_zone: str,
        cross_asset_raw_data: Mapping[str, Any] | None = None,
        now_utc: Any = None,
        candidate_generator: Callable[..., Iterable[Mapping[str, Any]]] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate production broader-origin candidates through the shared core."""

        generation_audit: dict[str, Any] = {}
        generator = candidate_generator or self._candidate_generator
        kwargs = {
            "raw_data": dict(raw_data),
            "mso": mso,
            "config": self.config,
            "symbol": symbol,
            "kill_zone": kill_zone,
            "cross_asset_raw_data": cross_asset_raw_data,
            "now_utc": now_utc,
        }
        if generator is generate_live_broader_origin_candidates:
            kwargs["generation_audit"] = generation_audit
        generated = generator(**kwargs)
        self.last_candidate_generation_audit = generation_audit
        return [dict(candidate) for candidate in generated]

    def decision_window_candidate_summaries(
        self,
        candidates: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return [summarize_decision_window_candidate(candidate) for candidate in candidates]

    def evaluate_candidate(
        self,
        *,
        candidate: Mapping[str, Any],
        symbol: str,
        risk_pct: float,
        asof_utc: str,
        mso: Any,
        open_positions: Iterable[Mapping[str, Any]] = (),
        pending_orders: Iterable[Mapping[str, Any]] = (),
        defer_proof_hash: bool = False,
    ) -> dict[str, Any]:
        """Evaluate one candidate through the replay-bound V4 evaluator."""

        if self._candidate_evaluator is None:
            raise RuntimeError("V4DecisionCycleCore candidate evaluator is not bound")
        if self.sources is None:
            raise RuntimeError("V4DecisionCycleCore sources are not bound")
        kwargs = {
            "candidate": candidate,
            "config": self.config,
            "source": self.sources[symbol]["M15"],
            "path_sources": self.sources[symbol],
            "risk_pct": risk_pct,
            "asof_utc": asof_utc,
            "mso": mso,
            "open_positions": open_positions,
            "pending_orders": pending_orders,
        }
        if defer_proof_hash:
            kwargs["defer_live_packet_hash"] = True
        return dict(self._candidate_evaluator(**kwargs))

    def schedule_window(
        self,
        *,
        asof_utc: str,
        candidates: list[dict[str, Any]],
        v4_packets: Mapping[str, Mapping[str, Any]],
        open_positions: Iterable[Mapping[str, Any]] = (),
        pending_orders: Iterable[Mapping[str, Any]] = (),
        _pristine_scheduler_sidecar_sink: MutableMapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Allocate a replay decision window through the bound scheduler surface."""

        if self._scheduler_allocator is None:
            raise RuntimeError("V4DecisionCycleCore scheduler allocator is not bound")
        kwargs = {
            "asof_utc": asof_utc,
            "candidates": candidates,
            "v4_packets": v4_packets,
            "config": self.config,
            "open_positions": open_positions,
            "pending_orders": pending_orders,
        }
        if _pristine_scheduler_sidecar_sink is not None:
            kwargs["_pristine_scheduler_sidecar_sink"] = (
                _pristine_scheduler_sidecar_sink
            )
        return dict(self._scheduler_allocator(**kwargs))

    @classmethod
    def proof_contract(cls) -> dict[str, Any]:
        return {
            "decision_cycle_core": cls.core_id,
            "production_import_path": cls.production_import_path,
            "surface_contract": dict(cls.surface_contract),
            "broker_mutation_enabled": False,
            "direct_session_orchestrator_boot_required": False,
            "core_operations": [
                "generate_candidates",
                "decision_window_candidate_summaries",
                "evaluate_candidate",
                "schedule_window",
                "simulate_order_lifecycle_via_simulated_broker",
            ],
        }
