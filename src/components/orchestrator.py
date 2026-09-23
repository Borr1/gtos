"""Component 8 — Session Orchestrator.

Main entry point for live trading. Manages the M15 candle loop,
configurable kill zone windows, session memory, and trade lifecycle.
PID-locked per symbol via knowledge_base/meta/.orchestrator_{symbol}.lock.
"""

from __future__ import annotations

import asyncio
import datetime as _datetime_module
import hashlib
import json
import logging
import math
import os
import re
import signal
import time
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Optional

import yaml

from src.mt5 import create_mt5, MT5Interface
from src.components.confidence_scorer import resolve_confidence_filter_mode, score_confidence
from src.components.broader_origin_generators import (
    LEAD_LAG_PAIRS,
    PRODUCTION_ORIGIN_FAMILIES,
    SOURCE_QUALITY_KEY,
    SOURCE_QUALITY_OK,
    evaluate_m15_ohlc_source_quality,
    generate_live_broader_origin_candidates,
)
from src.components.data_ingestion import (
    DataIncompleteError,
    TF_MAP,
    ingest_live_data,
    repair_malformed_ohlc_from_ticks,
)
from src.components.execution import (
    ExecutionEngine,
    clear_all_pending_intent_files,
)
from src.components.dual_broker_intent_bus import (
    MARKET_ENTRY as DUAL_BROKER_MARKET_ENTRY,
    PENDING_LIMIT as DUAL_BROKER_PENDING_LIMIT,
    build_intent_from_execution_inputs as _build_dual_broker_intent,
    publish_intent_if_enabled as _publish_dual_broker_intent,
)
from src.components.live_decision_packet_v4 import attach_live_decision_packet_v4
from src.components.poi_state_contract import POI_STATE_ATOMIC_FIELDS
from src.components.prop_firm_headroom_v4 import (
    build_prop_firm_headroom_snapshot_v4_from_account_state,
)
from src.components.verification import verify_candidate
from src.notifications import (
    notify_limit_placed, notify_limit_filled, notify_trade_closed,
    notify_limit_expired, notify_candidate, notify_daily_summary,
    notify_alert, build_vnext_notification_context,
)
from src.components.m5_refinement import refine_entry_m5, apply_m5_overrides
from src.components.market_state import compute_market_state
from src.components.permissions import check_permissions
from src.components.portfolio_risk import check_correlation_risk
from src.components.cross_instrument_correlation_gate import (
    apply_risk_multiplier as _apply_cross_instrument_risk_multiplier,
    evaluate_for_candidate as _evaluate_cross_instrument_correlation,
)
from src.components.pre_ai_gates import (
    framework_poi_availability,
    h1_poi_availability,
    poi_proximity_availability,
)
from src.components.structural_c_gate import (
    StructuralCGateDecision,
    evaluate_structural_c_gate,
)
from src.components.ai_call_policy import (
    attach_ai_call_policy_to_record,
    evaluate_ai_call_policy,
    record_ai_call_policy_decision,
)
from src.components.ai_supervisor import (
    apply_ai_supervisor_runtime_overrides,
    evaluate_ai_supervisor,
    record_ai_supervisor_decision,
)
from src.components.autocorrelation_risk import (
    attach_autocorrelation_risk_to_record,
    evaluate_autocorrelation_risk,
)
from src.components.walk_forward import check_walk_forward_lock
from src.components.trade_capture import (
    create_trade_record,
    update_verification,
    update_gate_results,
    update_execution,
    update_exit,
    update_m5_refinement,
    save_trade_record,
    load_trade_record,
    build_gate3_result,
    build_gate1_result,
    index_pending_record,
    lookup_pending_record,
    remove_pending_record,
)
from src.prompts.primary_analyzer_prompt import format_cross_instrument_context
from src.utils.cross_instrument import get_xauusd_d1_direction, get_asian_range_pct
from src.utils.config import (
    apply_instrument_overrides,
    apply_profile_overrides,
    resolve_profile,
)
from src.utils.broker_profile import (
    assert_mt5_account_matches_profile,
    broker_account_namespace,
    namespaced_file_path,
    resolve_mt5_terminal_path,
)
from src.utils.economic_calendar import load_calendar, should_block_trading
from src.components.news_calendar import NewsCalendar
from src.utils.file_io import atomic_write
from src.components.devils_advocate import DevilsAdvocate
from src.components.be_shadow_logger import BEShadowTracker, write_be_shadow_log
from src.components.partial_close_shadow_logger import PartialCloseShadowTracker, write_partial_close_shadow_log
from src.components.trailing_stop_shadow_logger import TrailingStopShadowTracker, write_trailing_stop_shadow_log
from src.components.proximity_shadow_logger import compute_trade_proximity, write_proximity_shadow_log, update_proximity_outcome
from src.components.time_in_trade_shadow_logger import (
    compute_time_in_trade_hypotheticals,
    write_time_in_trade_shadow_log,
)
from src.components.slippage_shadow_logger import record_close_slippage
from src.components.candidate_features_logger import log_candidate_features
from src.components.d1_bias_lag_logger import log_if_d1_bias_lag
from src.components import direction_emission_logger as _direction_emission
from src.components import dumb_baseline_shadow_logger as _dumb_baseline
from src.components import regime_shadow_logger as _regime_shadow
from src.components.drawdown_manager import DrawdownManager
from src.components.evaluation_logger import EvaluationLogger
from src.components import side_aware_sizing as _side_aware
from src.components.side_aware_sprt_watcher import SideAwareSprtWatcher
from src.components.sprt_class_halt_runtime import SprtClassHaltRuntime
from src.safety.heartbeat_monitor import (
    write_heartbeat as _write_heartbeat,
    per_symbol_heartbeat_path as _per_symbol_heartbeat_path,
)
from src.safety import dormant_state as _dormant_state
from src.safety.equity_guard import EquityFilter, safe_read_equity
from src.safety.runtime_halt import RuntimeHaltError, enforce_runtime_not_halted
from src.research_infra.forward_capture import (
    build_live_candidate_identity,
    record_live_candidate_forward_shadow,
    record_live_mso_forward_shadow,
)
from src.components.expired_poi_watch import (
    INTERESTING_REVALIDATION_STATUSES as _EXPIRED_POI_INTERESTING_STATUSES,
    archive_expired_pending_intent,
    evaluate_and_log_active_watches as _evaluate_expired_poi_watches,
)
from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.components.gtos_vnext_runtime import (
    attach_vnext_ai_policy_to_record,
    attach_vnext_confidence_override_to_record,
    attach_vnext_decision_to_record,
    attach_vnext_ltf_path_execution_to_record,
    attach_vnext_moonshot_dynamic_execution_to_record,
    attach_vnext_pending_policy_to_record,
    attach_vnext_pre_ai_to_record,
    attach_vnext_prop_safe_selector_to_record,
    attach_vnext_replacement_monitoring_to_record,
    attach_vnext_risk_adjustment_to_record,
    apply_vnext_risk_adjustment,
    build_vnext_replacement_monitoring_snapshot,
    evaluate_candidate_vnext,
    evaluate_pre_ai_vnext,
    evaluate_vnext_ai_policy,
    evaluate_vnext_confidence_override,
    evaluate_vnext_ltf_path_execution,
    evaluate_vnext_moonshot_dynamic_execution,
    evaluate_vnext_pending_policy,
    evaluate_vnext_prop_safe_selector,
    format_vnext_ai_policy_context_for_prompt,
    format_vnext_ai_role_context_for_prompt,
    GTOSVNextRuntimeDecision,
    is_vnext_ai_enforceable_route_family,
    record_vnext_replacement_monitoring_snapshot,
    record_vnext_runtime_decision,
    resolve_vnext_effective_framework,
    resolve_vnext_route_family,
    vnext_execution_block_reason,
)
from src.components.probability_debate_v4 import (
    attach_probability_debate_v4_to_record,
    build_probability_debate_context_from_runtime,
    evaluate_probability_debate_team_v4,
    probability_debate_v4_execution_block_reason,
    record_probability_debate_v4_decision,
)
from src.research.moonshot_default_off_policy_router import (
    DEFAULT_POLICY as MOONSHOT_DEFAULT_EXECUTION_POLICY,
    EXECUTION_POLICY_IDS as MOONSHOT_EXECUTION_POLICY_IDS,
    select_asof_displacement_policy as _select_moonshot_asof_policy,
)
from src.research.moonshot_v3_runtime_packages import (
    build_execution_policy_v3_packet,
    build_scheduler_v3_packet,
    build_selector_v3_packet,
    load_v3_runtime_package_set,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    build_scheduler_v4_runtime_capture_packet,
)
from src.components.v4_live_replay_decision_core import V4DecisionCycleCore

logger = logging.getLogger(__name__)


_VNEXT_PROP_PRE_DYNAMIC_HARD_BOUNDARY_REASONS = {
    "prop_safe_selector_missing_account_state",
    "prop_safe_selector_current_overall_max_loss_breach",
    "prop_safe_selector_current_daily_loss_window_breach",
    "prop_safe_selector_current_daily_and_overall_budget_breach",
}

_VNEXT_POSITION_RISK_FIELDS = (
    "gtos_vnext_prop_safe_selector_after_risk_pct",
    "gtos_vnext_selected_cell_risk_pct",
    "risk_pct",
)

_VNEXT_POSITION_TICKET_FIELDS = (
    "trade_state_ticket",
    "mt5_position_ticket",
    "mt5_entry_order_ticket",
    "mt5_order_ticket",
    "pending_ticket",
)


def _compose_effective_risk_with_selected_cell(
    effective_risk_pct,
    selected_cell_risk_pct,
) -> tuple[float, dict]:
    """Apply selected-cell risk as a source-backed cap, not an override."""
    try:
        current = float(effective_risk_pct)
    except (TypeError, ValueError):
        current = 0.0
    try:
        selected = float(selected_cell_risk_pct)
    except (TypeError, ValueError):
        return current, {
            "status": "selected_cell_risk_absent",
            "authority": "runtime_account_prop_correlation_risk",
            "pre_selected_runtime_risk_pct": current,
            "selected_cell_source_risk_pct": None,
            "effective_risk_pct": current,
        }
    if selected <= 0:
        return current, {
            "status": "selected_cell_risk_nonpositive",
            "authority": "runtime_account_prop_correlation_risk",
            "pre_selected_runtime_risk_pct": current,
            "selected_cell_source_risk_pct": selected,
            "effective_risk_pct": current,
        }
    if current <= 0:
        return current, {
            "status": "preserved_nonpositive_runtime_risk",
            "authority": "runtime_account_prop_correlation_risk",
            "pre_selected_runtime_risk_pct": current,
            "selected_cell_source_risk_pct": selected,
            "effective_risk_pct": current,
        }

    final = min(current, selected)
    return final, {
        "status": (
            "selected_cell_capped_runtime_risk"
            if selected < current
            else "runtime_risk_below_or_equal_selected_cell"
        ),
        "authority": "min_runtime_account_prop_correlation_and_selected_cell",
        "pre_selected_runtime_risk_pct": current,
        "selected_cell_source_risk_pct": selected,
        "effective_risk_pct": final,
    }


def _permission_denial_runtime_outcome(denial) -> dict:
    """Map a permissions denial to the orchestrator terminal runtime outcome."""
    gate = getattr(denial, "gate", "")
    reason = getattr(denial, "reason", "")
    details = getattr(denial, "details", {}) or {}
    if gate == "gate0_deployment_phase" and reason == "deployment_phase_2_log_only":
        return {
            "final_outcome": "LOG_ONLY_DEPLOYMENT_PHASE",
            "candle_decision": "LOG_ONLY_DEPLOYMENT_PHASE",
            "candle_detail": f"{gate}: {reason}",
            "execution_action": "LOG_ONLY_NO_ORDER",
            "deployment_phase": details.get("phase"),
        }
    return {
        "final_outcome": f"REJECTED_{str(gate).upper()}",
        "candle_decision": "REJECTED",
        "candle_detail": f"{gate}: {reason}",
        "execution_action": "REJECT_ORDER",
        "deployment_phase": details.get("phase"),
    }


def _attach_permission_denial_outcome_to_record(record: dict, denial, outcome: dict) -> None:
    """Attach the permission-denial execution action to a trade record."""
    pipeline = record.setdefault("decision_pipeline", {})
    pipeline["final_outcome"] = outcome["final_outcome"]
    pipeline["permission_gate"] = getattr(denial, "gate", "")
    pipeline["permission_reason"] = getattr(denial, "reason", "")
    pipeline["permission_execution_action"] = outcome["execution_action"]
    if outcome.get("deployment_phase") is not None:
        pipeline["deployment_phase"] = outcome["deployment_phase"]


VNEXT_BROADER_ORIGIN_BROKER_ALIASES = {
    "AUDJPY": "AUDJPY",
    "AUDUSD": "AUDUSD",
    "BTCUSD": "BTCUSD",
    "CHFJPY": "CHFJPY",
    "ETHUSD": "ETHUSD",
    "EURGBP": "EURGBP",
    "EURJPY": "EURJPY",
    "EURUSD": "EURUSD",
    "GBPJPY": "GBPJPY",
    "GBPUSD": "GBPUSD",
    "JP225": "JP225",
    "NAS100": "NDX100",
    "NZDUSD": "NZDUSD",
    "SPX500": "SPX500",
    "UK100": "UK100",
    "US30": "US30",
    "US30_CASH": "US30",
    "USDCAD": "USDCAD",
    "USDCHF": "USDCHF",
    "USDJPY": "USDJPY",
    "XAGUSD": "XAGUSD",
    "XAUUSD": "XAUUSD",
}


def _plain_dict(value):
    if isinstance(value, SimpleNamespace):
        return {key: _plain_dict(item) for key, item in vars(value).items()}
    if isinstance(value, dict):
        return {key: _plain_dict(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain_dict(item) for item in value]
    return value


class _SyntheticMoonshotAnalysis(SimpleNamespace):
    def model_dump(self, mode: str = "json") -> dict:  # noqa: ARG002 - pydantic-compatible shim
        return _plain_dict(self)


def _make_synthetic_moonshot_analysis(candidate: dict) -> _SyntheticMoonshotAnalysis:
    trade_parameters = candidate.get("trade_parameters") if isinstance(candidate, dict) else {}
    trade_parameters = dict(trade_parameters or {})
    trade_parameters.setdefault("candidate_id", candidate.get("candidate_id"))
    trade_parameters.setdefault("gtos_vnext_candidate_id", candidate.get("candidate_id"))
    trade_parameters.setdefault("direction", candidate.get("direction") or candidate.get("side"))
    trade_parameters.setdefault("entry_price", candidate.get("entry_price"))
    trade_parameters.setdefault("stop_loss", candidate.get("stop_loss"))
    trade_parameters.setdefault("take_profit_1", candidate.get("take_profit_1"))
    trade_parameters.setdefault("take_profit_2", candidate.get("take_profit_2"))
    trade_parameters.setdefault("take_profit_3", candidate.get("take_profit_3"))
    trade_parameters.setdefault("risk_reward_ratio", candidate.get("risk_reward_ratio", 1.5))
    source_fields = candidate.get("source_fields") if isinstance(candidate, dict) else {}
    source_fields = source_fields if isinstance(source_fields, dict) else {}
    for key in (
        "decision_window_candidates",
        "runtime_candidate_window",
        "gtos_vnext_decision_window_candidates",
        "gtos_vnext_probability_debate_v4_packet",
        "gtos_vnext_numeric_confluence_v4_packet",
        "gtos_vnext_follow_avoid_mixed_numeric_confluence_v4_packet",
        "origin_family",
        "candidate_origin_family",
        "current_framework",
        "framework",
        "poi_state",
        "poi_state_hash_sha256",
        "poi_state_contract_status",
        "poi_state_contract_failures",
        "poi_state_contract_valid",
        "poi_state_execution_allowed",
        *POI_STATE_ATOMIC_FIELDS,
    ):
        value = candidate.get(key)
        if value in (None, "", [], {}):
            value = source_fields.get(key)
        if value not in (None, "", [], {}) and key not in trade_parameters:
            trade_parameters[key] = value
    if source_fields:
        trade_parameters.setdefault("source_fields", dict(source_fields))
    return _SyntheticMoonshotAnalysis(
        decision="CANDIDATE",
        framework=candidate.get("framework") or candidate.get("origin_family"),
        confidence_score=100,
        no_trade_reason=None,
        wait_reason=None,
        trade_parameters=SimpleNamespace(**trade_parameters),
        reasoning=SimpleNamespace(
            setup_grade="A+",
            daily_bias=SimpleNamespace(direction="ranging"),
            h1_setup=SimpleNamespace(
                poi_type=candidate.get("origin_family"),
                fib_retracement_pct=None,
                causing_event_type=candidate.get("origin_family"),
                zone=None,
            ),
            liquidity_sweep=SimpleNamespace(
                detected=bool(source_fields.get("sweep_direction")),
                pool_type=source_fields.get("sweep_direction"),
            ),
            m15_confirmation=SimpleNamespace(
                displacement_quality="moonshot_broader_origin_live_asof",
                displacement_candle_body_vs_avg_ratio=source_fields.get("body_atr14"),
            ),
            overall_reasoning=(
                "Live vNext broader-origin candidate generated from closed M15 "
                f"source bars: {candidate.get('origin_family')}"
            ),
        ),
    )

# Default kill zone windows (UTC) - overridden by config
LONDON_START = (7, 0)   # 07:00
LONDON_END = (10, 30)   # 10:30 (extended from 09:30)
LONDON_CORE_END = (9, 30)  # Core window ends at 09:30; 09:30-10:30 is extended
NY_START = (13, 0)      # 13:00
NY_END = (15, 30)       # 15:30

TIMEOUT_TRAIL_MINUTES = 120  # 2 hours after session/fill anchor

LOCK_DIR = "knowledge_base/meta"
PENDING_LIMIT_LIFECYCLE_LOG_PATH: str = "shadow_logs/pending_limit_lifecycle.jsonl"
SLIPPAGE_LOG_PATH: str = "shadow_logs/slippage.jsonl"
LANE06_BROKER_LIFECYCLE_LOG_PATH: str = (
    "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31/"
    "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
)

# Per-symbol session-state persistence directory (Thursday 2026-04-23 audit —
# bug 2). Before this fix, ``session_state["date"]`` was initialized to None
# in __init__ and the first tick in _main_loop compared it to today's UTC
# date, triggering ``_new_day`` on every bootstrap and cancelling pending
# limits even mid-day. Persisting the date across restarts lets us detect a
# true new-day transition vs. a mid-day restart. Only the ``date`` field is
# round-tripped — per-KZ counters and MT5-derived balances are re-seeded in
# ``_new_day`` unconditionally when the UTC date actually rolls.
SESSION_STATE_DIR = Path("pipeline_state")


def _session_state_path(symbol: str) -> Path:
    """Per-symbol persisted session-state file. Isolated so simultaneous
    symbol processes never stomp each other's state."""
    safe = "".join(c for c in symbol if c.isalnum() or c in ("-", "_", ".")) or "unknown"
    return SESSION_STATE_DIR / f"session_state_{safe}.json"


def _load_persisted_session_date(symbol: str) -> Optional[str]:
    """Read the last-persisted UTC date for this symbol. Returns None on
    missing/unreadable/malformed file (caller treats as 'first-ever boot')."""
    path = _session_state_path(symbol)
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        date_val = data.get("date")
        if isinstance(date_val, str) and len(date_val) == 10:
            return date_val
        return None
    except (OSError, ValueError, json.JSONDecodeError) as e:
        logger.warning("session_state_%s.json unreadable, treating as absent: %s",
                       symbol, e)
        return None


def _persist_session_date(symbol: str, date_str: str) -> None:
    """Atomically persist the session date. Failure is logged but never
    crashes the pipeline — on next boot the absent/bad file falls back to
    'first-ever boot' which triggers _new_day (safe default)."""
    try:
        path = _session_state_path(symbol)
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, {"date": date_str, "symbol": symbol})
    except Exception as e:  # noqa: BLE001 — persistence failure must not crash
        logger.warning("Failed to persist session_state for %s: %s", symbol, e)

# ── Instrument-specific domain expertise blocks ──────────────────────────────
# Injected into additional_context so the AI has structural market knowledge
# when evaluating setups.  NO performance statistics — only factual knowledge
# about how the market works.

_XAUUSD_EXPERTISE = """## Gold Market Expertise

SESSION DYNAMICS:
- London KZ captures the LBMA AM Fix (09:30 UTC during BST, 10:30 UTC during GMT). \
Fix-related institutional flow concentrates 30-60 minutes before the fix. \
Structural breaks during this window carry higher conviction.
- NY KZ overlaps with COMEX futures open (~12:20-13:00 UTC). The heaviest COMEX \
volume occurs in the first 2-3 hours. The collision between European closing flows \
and American opening flows in the first 15 minutes can create false initial moves.
- Asian session (00:00-07:00 UTC) produces ranges. Asian high/low become visible \
reference levels on institutional screens. XAUUSD Asian range sweeps are \
continuation events, NOT reversals.

DISPLACEMENT MECHANICS:
- Stop-loss orders cluster at visible structural levels (below swing lows, above \
swing highs). When triggered, the cascade creates one-directional flow surge.
- The OB zone represents the last equilibrium BEFORE the cascade. Retest means \
price returning to pre-cascade fair value.
- Stronger cascades (fewer candles, larger body-to-range ratio) create stronger \
zones. A single-candle impulse means concentrated flow. A 4+ candle gradual \
move means distributed flow — weaker zone.
- Three-candle gaps (FVG) in the impulse signal exceptionally strong cascades \
with higher continuation rates.

GOLD-SPECIFIC:
- Central bank buying (~850+ tonnes/year) creates a structural demand floor. \
In bull regimes, bullish OB retests have fundamental support.
- DXY-gold inverse correlation is stable. Strong USD = gold headwind. \
When evaluating bearish gold setups, consider whether USD strength is a driver.
- Gold trades on a CFD derived from COMEX futures. Exact-pip precision is less \
reliable than structural zone identification."""


def apply_runtime_namespace_to_config(
    config: dict,
    runtime_namespace: str | None = None,
) -> str:
    """Resolve and stamp the runtime namespace into the active config.

    ExecutionEngine resolves persistence paths from config/env. Stamping the
    CLI-resolved namespace here prevents a direct run_agent launch from using
    namespaced locks/intent-bus metadata while falling back to legacy pending
    intent/checkpoint files.
    """
    resolved = broker_account_namespace(config, runtime_namespace)
    if resolved:
        runtime_cfg = config.get("runtime")
        if not isinstance(runtime_cfg, dict):
            runtime_cfg = {}
            config["runtime"] = runtime_cfg
        runtime_cfg["broker_account_namespace"] = resolved
    return resolved


class SessionOrchestrator:
    """Main loop that drives the live trading pipeline."""

    def __init__(self, mode: str = "demo", config_path: str = "config/agent_config.yaml",
                 symbol: str | None = None, profile: str | None = None,
                 terminal_path: str | None = None,
                 runtime_namespace: str | None = None):
        self.mode = mode
        self.config = self._load_config(config_path, symbol, profile)
        self._runtime_namespace = apply_runtime_namespace_to_config(
            self.config,
            runtime_namespace,
        )
        self._terminal_path = resolve_mt5_terminal_path(self.config, terminal_path)
        self.mt5: Optional[MT5Interface] = None
        self.execution: Optional[ExecutionEngine] = None
        self.analyzer = None  # PrimaryAnalyzer — lazy init
        self.running = False

        self._symbol = self.config.get("market", {}).get("symbol", "XAUUSD")
        self._mt5_symbol = self.config.get("market", {}).get("mt5_symbol", self._symbol)
        self._profile_name = (
            self.config.get("profile_name")
            or self.config.get("broker_profile", {}).get("broker")
            or profile
        )

        # Per-symbol PID lock path
        namespace_prefix = f"{self._runtime_namespace}_" if self._runtime_namespace else ""
        self._lock_path = str(
            Path(LOCK_DIR) / f".orchestrator_{namespace_prefix}{self._symbol}.lock"
        )

        # Load ALL KZ windows from config into a unified structure
        # Each entry: {name: {start_min, end_min, core_end_min, crosses_midnight}}
        kz_cfg = self.config.get("market", {}).get("kill_zones", {})
        self._kz_windows: dict[str, dict] = {}
        for kz_name, kz_data in kz_cfg.items():
            if kz_name == "missing_session":
                continue
            if kz_name == "off_configured_session" and self._symbol not in {"BTCUSD", "ETHUSD"}:
                continue
            start = self._parse_time(kz_data.get("start_utc", "00:00"))
            end = self._parse_time(kz_data.get("end_utc", "00:00"))
            core_end = self._parse_time(kz_data.get("core_end_utc",
                                                      kz_data.get("end_utc", "00:00")))
            start_min = start[0] * 60 + start[1]
            end_min = end[0] * 60 + end[1]
            core_end_min = core_end[0] * 60 + core_end[1]
            self._kz_windows[kz_name] = {
                "start_min": start_min,
                "end_min": end_min,
                "core_end_min": core_end_min,
                "crosses_midnight": end_min <= start_min,
            }
        self._install_vnext_moonshot_hour_kill_zones()

        # Backward-compat aliases for existing code referencing london/ny directly
        london = self._kz_windows.get("london", {})
        ny = self._kz_windows.get("ny", {})
        self._london_start = self._min_to_tuple(london.get("start_min", 7 * 60))
        self._london_end = self._min_to_tuple(london.get("end_min", 10 * 60 + 30))
        self._london_core_end = self._min_to_tuple(london.get("core_end_min", 9 * 60 + 30))
        self._ny_start = self._min_to_tuple(ny.get("start_min", 13 * 60))
        self._ny_end = self._min_to_tuple(ny.get("end_min", 15 * 60 + 30))
        self._ny_core_end = self._min_to_tuple(ny.get("core_end_min", 15 * 60 + 30))

        # Session state — dynamic per-KZ trade counters
        self.session_state = {
            "date": None,
            "trades_today": 0,
            "daily_pnl_pct": 0.0,
            "losses_today": 0,
            "current_kill_zone": None,
        }
        # Initialize per-KZ trade counters
        for kz_name in self._kz_windows:
            self.session_state[f"trades_{kz_name}"] = 0

        # Session memory: sliding window of last 6 candle evaluations per KZ
        self.session_memory: list[dict] = []

        # Cross-instrument context (computed once per session day)
        self._ci_context_text: str = ""
        # Raw XAU D1 direction value cached for downstream observability
        # (e.g. ``direction_emission_logger``). Stored separately from
        # ``_ci_context_text`` because the latter is the formatted prompt
        # block — analysts need the underlying label, not the rendered
        # paragraph. Values: "bullish" / "bearish" / "unavailable" /
        # "disabled" (set when the symbol is in
        # ``cross_instrument_context_disabled_for``). Reset to default on
        # ``_new_day``.
        self._xau_d1_direction_value: str = "unavailable"

        # Candle evaluations log for session manifest
        self.candle_log: list[dict] = []

        # Active trade record for exit updates
        self._active_trade_record: Optional[dict] = None
        self._active_trade_record_path: Optional[str] = None
        # Path to the record saved at LIMIT_PLACED time, promoted to
        # _active_trade_record_path on fill.  In-memory only; reconstructed
        # from disk at startup when pending_intent is restored (see
        # _recover_pending_record_path).
        self._pending_trade_record_path: Optional[str] = None

        # Economic calendar
        self._calendar = self._load_economic_calendar()

        # News calendar (FTMO-grade tight filter — replaces economic_calendar when enabled)
        self._news_calendar = NewsCalendar(self.config)

        # Shadow data collection (WF-1)
        self.devils_advocate = DevilsAdvocate(self.config)
        self.eval_logger = EvaluationLogger()

        # H29: Drawdown-based position size reduction
        self._drawdown_mgr = DrawdownManager(self.config)
        self._sprt_class_halt_runtime = SprtClassHaltRuntime(self.config)

        # Exit tracking state (MFE/MAE, R computation)
        self._trade_entry_price: Optional[float] = None
        self._trade_direction: Optional[str] = None
        self._trade_sl_distance: Optional[float] = None
        self._trade_entry_time: Optional[datetime] = None
        self._mfe_price: Optional[float] = None
        self._mae_price: Optional[float] = None
        self._last_tick_price: Optional[float] = None
        self._be_shadow_tracker: Optional[BEShadowTracker] = None
        self._partial_close_shadow_tracker: Optional[PartialCloseShadowTracker] = None
        self._trailing_stop_shadow_tracker: Optional[TrailingStopShadowTracker] = None
        self._last_mso = None  # Cache latest MSO for session summary
        # MT5 can stay "connected" after a brief network outage while
        # copy_rates_from_pos/account_info returns empty/zero inside the old
        # process. Retry through a fresh MT5 session, then let the watchdog
        # respawn us if the feed remains broken for multiple candles.
        self._data_incomplete_streak = 0
        self._data_incomplete_restart_threshold = 3
        self._abnormal_shutdown_reason: Optional[str] = None
        self._v3_runtime_package_cache = None
        self._v4_decision_cycle_core = V4DecisionCycleCore(config=self.config)

        # Bug #25 fix: per-symbol rolling-median equity filter. Protects
        # ``_update_daily_pnl`` from MT5 transient ``account_info()=None``
        # reads (which silently surface as ``equity=0.0`` via the
        # ``mt5_real`` wrapper) — those would compute ``daily_pnl_pct=-100%``
        # and trip the daily-loss-stop dormant marker on a healthy account.
        # Median-of-5 absorbs single transient outliers; recovery is
        # automatic once normal reads resume.
        self._equity_filter = EquityFilter(symbol=self._symbol)

    def _emit_dual_broker_intent(
        self,
        *,
        intent_type: str,
        trade_params: dict,
        source_trade_id: str,
        candidate_id: str | None = None,
        effective_risk_pct: float | None = None,
        kill_zone: str | None = None,
        trigger: str | None = None,
        telemetry_context: dict | None = None,
        primary_order: dict | None = None,
    ) -> dict:
        """Publish a canonical dual-broker intent when the bus is enabled.

        This is deliberately fail-open. Secondary-account replication must
        never block or slow the primary live order path.
        """
        try:
            source_profile = (
                getattr(self, "_profile_name", None)
                or self.config.get("profile_name")
                or self.config.get("broker_profile", {}).get("broker")
            )
            intent = _build_dual_broker_intent(
                intent_type=intent_type,
                source_profile=source_profile,
                source_runtime_namespace=getattr(self, "_runtime_namespace", None),
                source_symbol=self._symbol,
                source_mt5_symbol=self._mt5_symbol,
                trade_params=trade_params,
                source_trade_id=source_trade_id,
                candidate_id=candidate_id,
                effective_risk_pct=effective_risk_pct,
                kill_zone=kill_zone,
                trigger=trigger,
                telemetry_context=telemetry_context,
                primary_order=primary_order,
            )
            result = _publish_dual_broker_intent(self.config, intent)
            if result.get("status") in {"appended", "duplicate"}:
                logger.info(
                    "Dual-broker intent %s: type=%s id=%s source_trade=%s path=%s",
                    result.get("status"),
                    intent_type,
                    result.get("intent_id"),
                    source_trade_id,
                    result.get("path"),
                )
            return result
        except Exception as exc:  # noqa: BLE001
            logger.warning("Dual-broker intent build/publish failed open: %s", exc)
            return {"status": "error", "error": str(exc)}

    def _install_vnext_moonshot_hour_kill_zones(self) -> None:
        """Add proof-backed moonshot hour windows after normal KZ windows.

        Normal configured sessions keep precedence through insertion order. The
        moonshot windows make outside-session allowlist rows schedulable without
        turning generic ``off_configured_session`` into a production session.
        """
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        if not bool(cfg.get("moonshot_broader_origin_extended_session_enabled", False)):
            return
        if self._vnext_canonical_symbol_key(self._symbol) in {"BTCUSD", "ETHUSD"}:
            return
        eligible = {
            self._vnext_canonical_symbol_key(item)
            for item in cfg.get("moonshot_dynamic_execution_router_broker_native_eligible_symbols", [])
        }
        if eligible and self._vnext_canonical_symbol_key(self._symbol) not in eligible:
            return
        market_cfg = self.config.setdefault("market", {})
        kill_zones = market_cfg.setdefault("kill_zones", {})
        for hour in range(24):
            name = f"moonshot_h{hour:02d}_{(hour + 1) % 24:02d}"
            if name in self._kz_windows:
                continue
            start_min = hour * 60
            end_min = ((hour + 1) % 24) * 60
            schedule = {
                "start_utc": f"{hour:02d}:00",
                "end_utc": f"{(hour + 1) % 24:02d}:00",
                "core_end_utc": f"{(hour + 1) % 24:02d}:00",
                "source": "stage13_outside_session_hour_bucket_expansion",
            }
            kill_zones.setdefault(name, schedule)
            self._kz_windows[name] = {
                "start_min": start_min,
                "end_min": end_min,
                "core_end_min": end_min,
                "crosses_midnight": end_min <= start_min,
            }

    def run(self):
        """Main entry point. Call this to start the trading session."""
        try:
            self._bootstrap()
            self._main_loop()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt - shutting down")
        except RuntimeHaltError as e:
            logger.warning("Runtime halt active - orchestrator stopped before bootstrap: %s", e)
        except Exception as e:
            logger.error(f"Orchestrator error: {e}", exc_info=True)
            self._handle_crash(e)
        finally:
            self._shutdown()

    # === BOOTSTRAP ===

    def _bootstrap(self):
        """Startup: lock, connect, reconcile, validate."""
        logger.info(f"Bootstrapping orchestrator (mode={self.mode})")

        if self.mode in {"demo", "live"}:
            enforce_runtime_not_halted(
                action="orchestrator_bootstrap",
                config=self.config,
                context={
                    "mode": self.mode,
                    "symbol": self._symbol,
                    "mt5_symbol": self._mt5_symbol,
                    "profile": self._profile_name,
                    "runtime_namespace": self._runtime_namespace,
                },
            )

        self._acquire_lock()

        # API key safety check
        billing_mode = self.config.get("ai", {}).get("billing_mode", "api")
        if billing_mode == "subscription":
            if os.environ.get("ANTHROPIC_API_KEY"):
                raise RuntimeError(
                    "ANTHROPIC_API_KEY is set but billing_mode=subscription. "
                    "Remove the API key env var to prevent accidental API billing."
                )

        # Connect to MT5
        mt5_kwargs = {"terminal_path": self._terminal_path} if self._terminal_path else {}
        self.mt5 = create_mt5(mode=self.mode, **mt5_kwargs)
        if not self.mt5.connect():
            raise RuntimeError("Failed to connect to MT5")
        logger.info(f"MT5 connected (mode={self.mode})")
        account_assertion = assert_mt5_account_matches_profile(self.mt5, self.config)
        if account_assertion.get("checked"):
            logger.info(
                "MT5 account/profile assertion passed: fields=%s",
                account_assertion.get("fields_checked"),
            )
        logger.info(f"Account margin mode: {self.mt5.get_margin_mode()}")

        # Initialize components
        self.execution = ExecutionEngine(self.mt5, self.config)
        self._init_analyzer()

        # Cross-instrument context strip — startup confirmation for ops visibility
        ci_disabled_for = self.config.get("cross_instrument_context_disabled_for", []) or []
        if self._symbol in ci_disabled_for:
            logger.info(
                f"{self._symbol} cross-instrument context: DISABLED (XAUUSD strip)"
            )

        # pending_intent is persisted but _pending_trade_record_path is in-memory
        # only, so after a restart we need to reattach the saved record to the
        # live intent before it fills.
        self._recover_pending_record_path()

        # Walk-forward lock check (warning only — not a hard block)
        check_walk_forward_lock()

        # Crash recovery
        recovery_actions = self.execution.reconcile_on_startup()
        if recovery_actions:
            logger.warning(f"Recovery actions: {recovery_actions}")
            self._reconnect_trade_record()

        balance = self.mt5.get_account_balance()
        logger.info(f"Account balance: ${balance:,.2f}")

        # Bug 2 (Thursday 2026-04-23 audit): seed session_state["date"] from
        # the per-symbol persisted state BEFORE entering _main_loop so a
        # mid-day restart doesn't treat today as a "new day" and cancel all
        # pending limits. ``_new_day`` still fires when the persisted date is
        # stale (actual UTC date rollover) or when no file exists (first-ever
        # boot — safe default, matches pre-persistence behavior).
        try:
            persisted_date = _load_persisted_session_date(self._symbol)
            if persisted_date:
                self.session_state["date"] = persisted_date
                logger.info(
                    "Restored session date from disk: %s (mid-day restart — "
                    "pending limits preserved)",
                    persisted_date,
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("Session-state restore failed (safe fallback): %s", e)

        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Clear any stale graceful-shutdown marker for this symbol — we're
        # alive again, so the marker (which would tell the watchdog to skip
        # respawning us) is no longer relevant. Without this cleanup, a
        # manually-restarted orch leaves the marker behind; if the orch
        # later dies legitimately, the still-valid marker would suppress
        # the watchdog's respawn until the marker expires at next dead-zone
        # exit. We're booting → marker should not persist.
        try:
            stale_marker = Path("pipeline_state") / f".orch_shutdown_{self._symbol}.json"
            if stale_marker.exists():
                stale_marker.unlink()
                logger.info("Cleared stale graceful-shutdown marker on boot: %s", stale_marker.name)
        except OSError as e:
            logger.warning("Stale shutdown marker cleanup failed (non-fatal): %s", e)

        self.running = True
        logger.info("Bootstrap complete - ready to trade")

    def _init_analyzer(self):
        """Initialize PrimaryAnalyzer with KB and LLM backend."""
        from src.components.primary_analyzer import PrimaryAnalyzer
        from src.components.knowledge_base import KnowledgeBase
        from src.components.sprt_monitor import SPRTMonitor
        from src.llm_backend import LLMBackend

        billing_mode = self.config.get("ai", {}).get("billing_mode", "api")
        kb = KnowledgeBase(config=self.config)  # Uses default "knowledge_base/" path
        backend = LLMBackend(mode=billing_mode)
        self.llm_backend = backend  # Retained for M5 refinement calls
        self.kb = kb  # Retained for write_no_trade() logging
        self._sprt_monitor = SPRTMonitor(config=self.config)
        self.analyzer = PrimaryAnalyzer(self.config, kb=kb, llm_backend=backend)

    def _evaluate_gtos_vnext_runtime(self, *, analysis, raw_data: dict,
                                     kill_zone: str, record: dict | None):
        """Run the vNext runtime decision surface for one AI CANDIDATE."""
        decision = evaluate_candidate_vnext(
            analysis=analysis,
            raw_data=raw_data,
            kill_zone=kill_zone,
            config=self.config,
            symbol=self._symbol,
            source_symbol=self._mt5_symbol,
        )
        if record is not None:
            attach_vnext_decision_to_record(record, decision)

        candle_time = self._vnext_effective_candle_time(raw_data)
        record_vnext_runtime_decision(
            decision=decision,
            config=self.config,
            phase="post_l2_candidate",
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=str(candle_time) if candle_time else None,
        )
        evidence = decision.evidence or {}
        metrics = evidence.get("metrics", {}) if isinstance(evidence, dict) else {}
        cost_r = (metrics.get("cost_adjusted_simulated_r") or {}).get("sum")
        proxy = (metrics.get("proxy_score") or {}).get("sum")
        stress_r = (metrics.get("stress_simulated_r") or {}).get("sum")
        effective_n = (metrics.get("effective_n") or {}).get("sum")
        logger.info(
            "GTOS_VNEXT_RUNTIME decision=%s matched=%s apply_to_execution=%s "
            "cost_r=%s proxy=%s stress_r=%s effective_n=%s event=%s",
            decision.decision,
            decision.matched,
            decision.apply_to_execution,
            cost_r,
            proxy,
            stress_r,
            effective_n,
            decision.event,
        )
        return decision

    def _evaluate_probability_debate_team_v4(
        self,
        *,
        analysis,
        raw_data: dict,
        kill_zone: str,
        record: dict | None,
        vnext_decision,
        confidence_metrics=None,
    ):
        """Run the V4 numeric probability/debate packet for one candidate.

        The engine is production-code packaged but default-off for execution in
        config. Logging/attachment is diagnostic and must never break runtime.
        """
        try:
            context = build_probability_debate_context_from_runtime(
                analysis=analysis,
                raw_data=raw_data,
                vnext_decision=vnext_decision,
                symbol=self._symbol,
                source_symbol=self._mt5_symbol,
                kill_zone=kill_zone,
                record=record,
                confidence_metrics=confidence_metrics,
            )
            decision = evaluate_probability_debate_team_v4(context, self.config)
            if record is not None:
                attach_probability_debate_v4_to_record(record, decision)
            candle_time = self._vnext_effective_candle_time(raw_data)
            record_probability_debate_v4_decision(
                decision=decision,
                config=self.config,
                phase="post_l2_candidate",
                symbol=self._symbol,
                kill_zone=kill_zone,
                candle_time_utc=str(candle_time) if candle_time else None,
            )
            logger.info(
                "PROBABILITY_DEBATE_V4 action=%s probability=%.3f ev=%.3f "
                "apply_to_execution=%s reason=%s",
                decision.selected_action,
                decision.selected_thesis.probability,
                decision.selected_thesis.ev_r,
                decision.apply_to_execution,
                decision.reason,
            )
            return decision
        except Exception as exc:  # noqa: BLE001 - diagnostics cannot break runtime
            logger.warning("Probability debate V4 evaluation failed: %s", exc, exc_info=True)
            return None

    def _evaluate_gtos_vnext_moonshot_dynamic_execution(
        self,
        *,
        vnext_decision,
        raw_data: dict,
        kill_zone: str,
        record: dict | None,
        candidate_context: dict | None = None,
    ):
        """Run the production moonshot dynamic execution router."""
        decision = evaluate_vnext_moonshot_dynamic_execution(
            decision=vnext_decision,
            config=self.config,
            candidate_context=candidate_context,
        )
        if record is not None:
            attach_vnext_moonshot_dynamic_execution_to_record(record, decision)

        candle_time = self._vnext_effective_candle_time(raw_data)
        record_vnext_runtime_decision(
            decision=decision,
            config=self.config,
            phase="moonshot_dynamic_execution",
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=str(candle_time) if candle_time else None,
        )
        logger.info(
            "GTOS_VNEXT_MOONSHOT_DYNAMIC policy=%s execution_policy_id=%s applied=%s status=%s "
            "candidate_action=%s replaces=%s source_action=%s",
            decision.selected_policy,
            getattr(decision, "execution_policy_id", None),
            decision.applied,
            decision.decision_status,
            decision.candidate_action,
            decision.replaced_policy,
            decision.source_quality_action,
        )
        return decision

    def _record_gtos_vnext_replacement_monitoring(
        self,
        *,
        phase: str,
        raw_data: dict,
        kill_zone: str,
        record: dict | None,
        vnext_pre_ai=None,
        vnext_ai_policy=None,
        vnext_decision=None,
        vnext_risk_adjustment=None,
        vnext_pending_policy=None,
        vnext_ltf_path_execution=None,
        vnext_prop_safe_selector=None,
        vnext_moonshot_dynamic_execution=None,
        source_capture_state: dict | None = None,
    ):
        """Record the Stage10 vNext replacement monitoring snapshot."""
        candle_time = self._vnext_effective_candle_time(raw_data)
        ai_supervisor = raw_data.get("ai_supervisor_decision") if isinstance(raw_data, dict) else None
        snapshot = build_vnext_replacement_monitoring_snapshot(
            config=self.config,
            phase=phase,
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=str(candle_time) if candle_time else None,
            vnext_pre_ai=vnext_pre_ai,
            vnext_ai_policy=vnext_ai_policy,
            vnext_decision=vnext_decision,
            vnext_risk_adjustment=vnext_risk_adjustment,
            vnext_pending_policy=vnext_pending_policy,
            vnext_ltf_path_execution=vnext_ltf_path_execution,
            vnext_prop_safe_selector=vnext_prop_safe_selector,
            vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
            ai_supervisor_decision=ai_supervisor,
            source_capture_state=source_capture_state,
        )
        if record is not None:
            attach_vnext_replacement_monitoring_to_record(record, snapshot)
        record_vnext_replacement_monitoring_snapshot(
            snapshot=snapshot,
            config=self.config,
        )
        logger.info(
            "GTOS_VNEXT_REPLACEMENT_MONITOR phase=%s dynamic_policy=%s "
            "source_window_complete=%s old_live_leakage=%s warnings=%s",
            snapshot.phase,
            snapshot.dynamic_exit_transition.get("selected_policy"),
            snapshot.source_capture_completeness.get("source_window_complete"),
            snapshot.old_live_fallback_leakage.get("leakage_detected"),
            list(snapshot.warnings),
        )
        return snapshot

    def _process_vnext_broader_origin_candidates(
        self,
        *,
        raw_data: dict,
        mso,
        kill_zone: str,
    ) -> bool:
        """Run live broader-origin vNext candidates before the AI/L2 path."""
        cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
        production_replacement_active = (
            str(cfg.get("mode") or "").strip().lower()
            == "production_replacement_vnext_moonshot"
        )
        if not bool(cfg.get("enabled", False)) or not bool(cfg.get("apply_to_execution", False)):
            if production_replacement_active:
                self._record_vnext_broader_origin_no_candidate(
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    final_outcome="NO_TRADE_GTOS_VNEXT_REPLACEMENT_RUNTIME_DISABLED",
                    reason=(
                        "production_replacement_vnext_runtime_disabled_no_old_primary_"
                        "analyzer_l2_fallback"
                    ),
                    decision_path=(
                        "production_replacement_vnext_runtime_disabled_consumed_before_old_primary_"
                        "analyzer_and_l2"
                    ),
                    control_flags={
                        "enabled": bool(cfg.get("enabled", False)),
                        "apply_to_execution": bool(cfg.get("apply_to_execution", False)),
                    },
                )
                self._log_candle(
                    "NO_TRADE_GTOS_VNEXT_REPLACEMENT_RUNTIME_DISABLED",
                    "production_replacement_vnext_runtime_disabled_no_old_primary_analyzer_l2_fallback",
                    kill_zone,
                )
                return True
            return False
        control_flags_ready = (
            bool(cfg.get("moonshot_broader_origin_live_generation_enabled", False))
            and bool(cfg.get("moonshot_broader_origin_execute_pre_ai_pre_l2", False))
            and bool(cfg.get("moonshot_dynamic_execution_router_enabled", False))
            and bool(cfg.get("moonshot_dynamic_execution_router_apply_to_execution", False))
        )
        if not control_flags_ready:
            if production_replacement_active:
                self._record_vnext_broader_origin_no_candidate(
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    final_outcome="NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_CONTROL_FLAG_DISABLED",
                    reason="production_replacement_control_flags_disabled_no_old_primary_analyzer_l2_fallback",
                    decision_path=(
                        "vnext_broader_origin_control_flags_disabled_consumed_before_old_primary_"
                        "analyzer_and_l2"
                    ),
                    control_flags={
                        "moonshot_broader_origin_live_generation_enabled": bool(
                            cfg.get("moonshot_broader_origin_live_generation_enabled", False)
                        ),
                        "moonshot_broader_origin_execute_pre_ai_pre_l2": bool(
                            cfg.get("moonshot_broader_origin_execute_pre_ai_pre_l2", False)
                        ),
                        "moonshot_dynamic_execution_router_enabled": bool(
                            cfg.get("moonshot_dynamic_execution_router_enabled", False)
                        ),
                        "moonshot_dynamic_execution_router_apply_to_execution": bool(
                            cfg.get("moonshot_dynamic_execution_router_apply_to_execution", False)
                        ),
                    },
                )
                self._log_candle(
                    "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_CONTROL_FLAG_DISABLED",
                    "production_replacement_control_flags_disabled_no_old_primary_analyzer_l2_fallback",
                    kill_zone,
                )
                return True
            return False

        try:
            cross_asset_raw_data = self._vnext_broader_origin_cross_asset_raw_data()
            decision_core = getattr(self, "_v4_decision_cycle_core", None)
            if not isinstance(decision_core, V4DecisionCycleCore):
                decision_core = V4DecisionCycleCore(config=self.config)
                self._v4_decision_cycle_core = decision_core
            candidates = decision_core.generate_candidates(
                raw_data=raw_data,
                mso=mso,
                symbol=self._symbol,
                kill_zone=kill_zone,
                cross_asset_raw_data=cross_asset_raw_data,
                now_utc=raw_data.get("candle_close_utc") if isinstance(raw_data, dict) else None,
                candidate_generator=generate_live_broader_origin_candidates,
            )
        except Exception as exc:  # noqa: BLE001 - generator failure must fail closed.
            logger.warning("GTOS_VNEXT_BROADER_ORIGIN generation failed: %s", exc)
            self._record_vnext_broader_origin_no_candidate(
                raw_data=raw_data,
                kill_zone=kill_zone,
                final_outcome="NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_GENERATOR_FAILED",
                reason="live_broader_origin_generator_failed_fail_closed_before_old_primary_analyzer_l2",
                decision_path=(
                    "vnext_broader_origin_generator_failed_consumed_before_old_primary_"
                    "analyzer_and_l2"
                ),
                error=str(exc),
            )
            self._log_candle(
                "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_GENERATOR_FAILED",
                "live_broader_origin_generator_failed_fail_closed_before_old_primary_analyzer_l2",
                kill_zone,
            )
            return True

        if not candidates:
            source_quality = (
                raw_data.get(SOURCE_QUALITY_KEY)
                if isinstance(raw_data, dict) and isinstance(raw_data.get(SOURCE_QUALITY_KEY), dict)
                else {}
            )
            source_quality_failed = source_quality.get("status") not in (None, SOURCE_QUALITY_OK)
            no_candidate_reason = (
                str(source_quality.get("reason"))
                if source_quality_failed and source_quality.get("reason")
                else "no_live_broader_origin_candidate_from_closed_m15_source_contract"
            )
            final_outcome = (
                "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_MALFORMED_SOURCE"
                if source_quality_failed
                else "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_NO_CANDIDATE"
            )
            decision_path = (
                "vnext_broader_origin_malformed_source_consumed_before_old_primary_analyzer_and_l2"
                if source_quality_failed
                else (
                    "vnext_broader_origin_no_candidate_consumed_before_old_primary_"
                    "analyzer_and_l2"
                )
            )
            self._record_vnext_broader_origin_no_candidate(
                raw_data=raw_data,
                kill_zone=kill_zone,
                final_outcome=final_outcome,
                reason=no_candidate_reason,
                decision_path=decision_path,
                candidate_count=0,
            )
            self._log_candle(
                final_outcome,
                no_candidate_reason,
                kill_zone,
            )
            return True

        safety_gate_outcome = self._vnext_broader_origin_safety_gate(
            raw_data=raw_data,
            mso=mso,
            kill_zone=kill_zone,
            candidates=candidates,
        )
        if safety_gate_outcome is not None:
            return True

        consumed = False
        decision_window_candidates = (
            self._v4_decision_cycle_core.decision_window_candidate_summaries(
                candidate for candidate in candidates if isinstance(candidate, dict)
            )
        )
        for candidate in candidates:
            if isinstance(candidate, dict):
                candidate.setdefault(
                    "decision_window_candidates",
                    decision_window_candidates,
                )
            outcome = self._execute_vnext_broader_origin_candidate(
                candidate=candidate,
                raw_data=raw_data,
                mso=mso,
                kill_zone=kill_zone,
            )
            consumed = True
            if outcome in {
                "EXECUTED_GTOS_VNEXT_BROADER_ORIGIN_MARKET",
                "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN",
            }:
                return True
        return consumed

    def _record_vnext_broader_origin_no_candidate(
        self,
        *,
        raw_data: dict,
        kill_zone: str,
        final_outcome: str,
        reason: str,
        decision_path: str,
        candidate_count: int = 0,
        control_flags: dict | None = None,
        error: str | None = None,
    ) -> dict:
        """Persist native vNext no-candidate/refusal evidence before old paths."""
        candle_time = self._vnext_effective_candle_time(raw_data)
        source_packet = self._vnext_no_candidate_source_packet(raw_data=raw_data, kill_zone=kill_zone)
        evidence = {
            "schema_version": "gtos_vnext_no_candidate_packet_v1",
            "capture_mode": "native_live_no_candidate_writer",
            "capture_reason": "live_process_no_candidate_packet_writer",
            "symbol": self._symbol,
            "broker_symbol": self._mt5_symbol,
            "kill_zone": kill_zone,
            "route_session": kill_zone,
            "candle_close_utc": candle_time,
            "candle_time_source": self._vnext_candle_time_source(raw_data, candle_time),
            "decision_path": decision_path,
            "final_outcome": final_outcome,
            "reason": reason,
            "candidate_count": int(candidate_count or 0),
            "old_primary_analyzer_called": False,
            "old_l2_required": False,
            "source_packet": source_packet,
            "null_zero_reasons": source_packet.get("null_zero_reasons", {}),
        }
        if control_flags is not None:
            evidence["control_flags"] = dict(control_flags)
        if error:
            evidence["error"] = str(error)
        self._last_vnext_broader_origin_no_candidate = evidence

        cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
        decision = GTOSVNextRuntimeDecision(
            decision="AVOID",
            event={
                "symbol": self._symbol,
                "source_symbol": self._mt5_symbol,
                "route_session": kill_zone,
                "phase": "broader_origin_no_candidate",
                "decision_path": decision_path,
            },
            enabled=bool(cfg.get("enabled", False)),
            apply_to_execution=bool(cfg.get("apply_to_execution", False)),
            matched=False,
            reason=reason,
            evidence=evidence,
        )
        try:
            record_vnext_runtime_decision(
                decision=decision,
                config=self.config,
                phase="broader_origin_no_candidate",
                symbol=self._symbol,
                kill_zone=kill_zone,
                candle_time_utc=str(candle_time) if candle_time else None,
            )
            self._record_gtos_vnext_replacement_monitoring(
                phase="broader_origin_no_candidate",
                raw_data=raw_data,
                kill_zone=kill_zone,
                record=None,
                vnext_decision=decision,
                source_capture_state={
                    "source_complete": source_packet.get("source_window_complete"),
                    "source_window_complete": source_packet.get("source_window_complete"),
                    "source_mode": source_packet.get("source_mode"),
                    "source_path_feature_status": source_packet.get(
                        "source_path_feature_status"
                    ),
                    "null_zero_reasons": source_packet.get("null_zero_reasons", {}),
                    "m1": source_packet.get("m1", {}),
                    "m15": source_packet.get("m15", {}),
                    "tick": source_packet.get("tick", {}),
                    "no_candidate_reason": reason,
                    "candidate_count": int(candidate_count or 0),
                },
            )
        except Exception as exc:  # noqa: BLE001 - evidence logging must not break runtime.
            logger.warning("GTOS_VNEXT_BROADER_ORIGIN no-candidate evidence failed: %s", exc)
        return evidence

    def _vnext_no_candidate_source_packet(self, *, raw_data: dict, kill_zone: str) -> dict:
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        candles = raw_data.get("candles") if isinstance(raw_data.get("candles"), dict) else {}
        m1_candles = list(candles.get("M1") or [])
        m15_candles = list(candles.get("M15") or [])
        m1_capture_state = self._vnext_m1_capture_state_snapshot()
        tick = None
        if self.mt5 is not None:
            try:
                tick = self.mt5.get_tick(self._mt5_symbol)
            except Exception:  # noqa: BLE001 - snapshot only.
                tick = None
        tick_bid = self._float_or_none(getattr(tick, "bid", None)) if tick is not None else None
        tick_ask = self._float_or_none(getattr(tick, "ask", None)) if tick is not None else None
        spread = self._float_or_none(getattr(tick, "spread_cents", None)) if tick is not None else None
        null_zero_reasons = {}
        m1_latest = self._latest_candle_time_from_rows(m1_candles)
        if not m1_latest and m1_capture_state:
            m1_latest = m1_capture_state.get("last_closed_candle_time_utc") or m1_capture_state.get(
                "last_time_utc"
            )
        if not m1_latest:
            null_zero_reasons["m1_candles"] = (
                "no_m1_candles_in_raw_data_or_capture_state_for_no_candidate_packet"
            )
        if not m15_candles:
            null_zero_reasons["m15_candles"] = "no_m15_candles_in_raw_data_for_no_candidate_packet"
        if tick is None:
            null_zero_reasons["tick_snapshot"] = "mt5_tick_snapshot_unavailable_for_no_candidate_packet"
        source_quality = (
            raw_data.get(SOURCE_QUALITY_KEY)
            if isinstance(raw_data.get(SOURCE_QUALITY_KEY), dict)
            else None
        )
        return {
            "source_mode": "LIVE_RAW_M15",
            "source_window_complete": bool(raw_data.get("source_window_complete", bool(m15_candles))),
            "source_path_feature_status": raw_data.get(
                "source_path_feature_status",
                "raw_data_m15_asof_complete" if m15_candles else "raw_data_m15_missing_or_not_attached",
            ),
            "live_generation_status": "no_broader_origin_candidate_generated_live_asof",
            "kill_zone": kill_zone,
            "source_quality": source_quality,
            "m1": {
                "available": bool(m1_latest),
                "count": len(m1_candles),
                "latest_time_utc": m1_latest,
                "raw_data_count": len(m1_candles),
                "capture_state": m1_capture_state,
                "source": "raw_data_candles" if m1_candles else "pipeline_state_m1_capture_state",
            },
            "m15": {
                "available": bool(m15_candles),
                "count": len(m15_candles),
                "latest_time_utc": self._latest_candle_time_from_rows(m15_candles),
            },
            "tick": {
                "available": tick is not None,
                "bid": tick_bid,
                "ask": tick_ask,
                "spread_cents": spread,
            },
            "null_zero_reasons": null_zero_reasons,
        }

    def _vnext_m1_capture_state_snapshot(self) -> dict | None:
        base_path = Path("pipeline_state") / "m1_capture_state.json"
        runtime_namespace = getattr(self, "_runtime_namespace", "") or ""
        path = (
            namespaced_file_path(base_path, runtime_namespace)
            if runtime_namespace
            else base_path
        )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        symbols = payload.get("symbols") if isinstance(payload, dict) else None
        state = symbols.get(self._symbol) if isinstance(symbols, dict) else None
        if not isinstance(state, dict):
            return None
        return {
            "path": str(path),
            "runtime_namespace": runtime_namespace or None,
            "updated_at_utc": payload.get("updated_at_utc"),
            "broker_symbol": state.get("broker_symbol"),
            "last_closed_candle_time_utc": state.get("last_closed_candle_time_utc"),
            "last_closed_candle_age_seconds": state.get("last_closed_candle_age_seconds"),
            "last_cycle_status": state.get("last_cycle_status"),
            "last_fetch_bars_requested": state.get("last_fetch_bars_requested"),
            "last_rows_written": state.get("last_rows_written"),
            "last_no_new_row_reason": state.get("last_no_new_row_reason"),
            "last_seen_at_utc": state.get("last_seen_at_utc"),
            "top_level_last_error_count": payload.get("last_error_count"),
        }

    @staticmethod
    def _latest_candle_time_from_rows(rows: list) -> str | None:
        if not rows:
            return None
        latest = rows[-1]
        if isinstance(latest, dict):
            return latest.get("time") or latest.get("timestamp") or latest.get("time_utc")
        return str(getattr(latest, "time", "") or "") or None

    def _vnext_effective_candle_time(self, raw_data: dict | None) -> str | None:
        """Prefer the newest closed M15 candle over stale top-level metadata."""
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        top_level = raw_data.get("candle_close_utc") or raw_data.get("candle_time_utc")
        candles = raw_data.get("candles") if isinstance(raw_data.get("candles"), dict) else {}
        m15_latest = self._latest_candle_time_from_rows(list(candles.get("M15") or []))
        top_dt = self._parse_utc_datetime(top_level)
        m15_dt = self._parse_utc_datetime(m15_latest)
        if m15_dt is not None and (top_dt is None or m15_dt > top_dt):
            return str(m15_latest)
        return str(top_level) if top_level not in (None, "") else None

    def _vnext_candle_time_source(
        self,
        raw_data: dict | None,
        effective_candle_time: str | None,
    ) -> dict:
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        top_level = raw_data.get("candle_close_utc") or raw_data.get("candle_time_utc")
        candles = raw_data.get("candles") if isinstance(raw_data.get("candles"), dict) else {}
        m15_latest = self._latest_candle_time_from_rows(list(candles.get("M15") or []))
        corrected = bool(
            effective_candle_time
            and m15_latest
            and str(effective_candle_time) == str(m15_latest)
            and str(top_level or "") != str(m15_latest)
        )
        return {
            "top_level_candle_time_utc": top_level,
            "m15_latest_closed_time_utc": m15_latest,
            "effective_candle_time_utc": effective_candle_time,
            "status": (
                "corrected_from_latest_closed_m15"
                if corrected
                else "top_level_candle_time_current_or_m15_absent"
            ),
        }

    @staticmethod
    def _vnext_candidate_safety_gate_summary(candidate: dict) -> dict:
        summary_fields = (
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
            "probability",
            "ev_r",
            "EV",
            "broker_net_expectancy_r",
            "stress_expectancy_r",
            "confluence_score",
            "source_completeness",
            "source_completeness_status",
            "no_leak_status",
            "utc_hour_bucket",
        )
        summary = {field: candidate.get(field) for field in summary_fields if field in candidate}
        trade_parameters = candidate.get("trade_parameters")
        if isinstance(trade_parameters, dict):
            summary["trade_parameters"] = dict(trade_parameters)
        source_fields = candidate.get("source_fields")
        if isinstance(source_fields, dict):
            summary["source_fields"] = dict(source_fields)
        return summary

    def _record_vnext_broader_origin_safety_gate_block(
        self,
        *,
        raw_data: dict,
        kill_zone: str,
        candidates: list[dict] | None,
        final_outcome: str,
        reason: str,
        decision_path: str,
    ) -> dict:
        """Persist vNext broader-origin candidate blocks before old paths.

        This covers candles where live broader-origin candidates exist but a
        native vNext safety gate blocks them before per-candidate execution.
        Without this packet, replacement monitoring can look silent even though
        a source-backed candidate was evaluated and refused.
        """
        candidate_rows = [
            self._vnext_candidate_safety_gate_summary(candidate)
            for candidate in (candidates or [])
            if isinstance(candidate, dict)
        ]
        candle_time = self._vnext_effective_candle_time(raw_data)
        source_packet = self._vnext_no_candidate_source_packet(raw_data=raw_data, kill_zone=kill_zone)
        evidence = {
            "schema_version": "gtos_vnext_candidate_safety_gate_block_packet_v1",
            "capture_mode": "native_live_candidate_safety_gate_writer",
            "capture_reason": "live_process_candidate_safety_gate_packet_writer",
            "symbol": self._symbol,
            "broker_symbol": self._mt5_symbol,
            "kill_zone": kill_zone,
            "route_session": kill_zone,
            "candle_close_utc": candle_time,
            "candle_time_source": self._vnext_candle_time_source(raw_data, candle_time),
            "decision_path": decision_path,
            "final_outcome": final_outcome,
            "reason": reason,
            "candidate_count": len(candidate_rows),
            "candidates": candidate_rows,
            "old_primary_analyzer_called": False,
            "old_l2_required": False,
            "source_packet": source_packet,
            "null_zero_reasons": source_packet.get("null_zero_reasons", {}),
        }
        self._last_vnext_broader_origin_safety_gate_block = evidence

        cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
        decision = GTOSVNextRuntimeDecision(
            decision="AVOID",
            event={
                "symbol": self._symbol,
                "source_symbol": self._mt5_symbol,
                "route_session": kill_zone,
                "phase": "broader_origin_safety_gate_blocked",
                "decision_path": decision_path,
                "final_outcome": final_outcome,
                "candidate_count": len(candidate_rows),
            },
            enabled=bool(cfg.get("enabled", False)),
            apply_to_execution=bool(cfg.get("apply_to_execution", False)),
            matched=True,
            reason=reason,
            evidence=evidence,
        )
        try:
            record_vnext_runtime_decision(
                decision=decision,
                config=self.config,
                phase="broader_origin_safety_gate_blocked",
                symbol=self._symbol,
                kill_zone=kill_zone,
                candle_time_utc=str(candle_time) if candle_time else None,
            )
            self._record_gtos_vnext_replacement_monitoring(
                phase="broader_origin_safety_gate_blocked",
                raw_data=raw_data,
                kill_zone=kill_zone,
                record=None,
                vnext_decision=decision,
                source_capture_state={
                    "source_complete": source_packet.get("source_window_complete"),
                    "source_window_complete": source_packet.get("source_window_complete"),
                    "source_mode": source_packet.get("source_mode"),
                    "source_path_feature_status": source_packet.get(
                        "source_path_feature_status"
                    ),
                    "null_zero_reasons": source_packet.get("null_zero_reasons", {}),
                    "m1": source_packet.get("m1", {}),
                    "m15": source_packet.get("m15", {}),
                    "tick": source_packet.get("tick", {}),
                    "candidate_count": len(candidate_rows),
                    "candidate_summaries": [
                        self._vnext_candidate_safety_gate_summary(candidate)
                        for candidate in candidate_rows
                    ],
                    "safety_gate_outcome": final_outcome,
                    "safety_gate_reason": reason,
                },
            )
        except Exception as exc:  # noqa: BLE001 - evidence logging must not break runtime.
            logger.warning("GTOS_VNEXT_BROADER_ORIGIN safety-gate evidence failed: %s", exc)
        return evidence

    def _vnext_broader_origin_safety_gate(
        self,
        *,
        raw_data: dict,
        mso,
        kill_zone: str,
        candidates: list[dict] | None = None,
    ) -> str | None:
        """Apply vNext-native pre-execution safety controls to broader origins."""
        passed, reason = prescreen_mso(mso)
        if not passed:
            self._record_vnext_broader_origin_safety_gate_block(
                raw_data=raw_data,
                kill_zone=kill_zone,
                candidates=candidates,
                final_outcome="NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_PRESCREEN_BLOCKED",
                reason=f"vnext_broader_origin_prescreen:{reason}",
                decision_path=(
                    "vnext_broader_origin_prescreen_blocked_consumed_before_old_primary_"
                    "analyzer_and_l2"
                ),
            )
            self._record_forward_capture_evaluation_shadow(
                mso=mso,
                raw_data=raw_data,
                evaluation_stage="GTOS_VNEXT_BROADER_ORIGIN_PRESCREEN_BLOCKED",
                prescreen_status="FAILED",
                reason=reason,
                kill_zone=kill_zone,
            )
            self._log_candle(
                "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_PRESCREEN_BLOCKED",
                f"vnext_broader_origin_prescreen:{reason}",
                kill_zone,
            )
            return "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_PRESCREEN_BLOCKED"

        candle_time_utc = self._parse_utc_datetime(
            raw_data.get("candle_close_utc") if isinstance(raw_data, dict) else None
        ) or datetime.now(timezone.utc)
        news_calendar = getattr(self, "_news_calendar", None)
        if news_calendar is not None and getattr(news_calendar, "enabled", False):
            blocked, cal_reason = news_calendar.should_skip(self._symbol, candle_time_utc)
            if blocked:
                self._record_vnext_broader_origin_safety_gate_block(
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    candidates=candidates,
                    final_outcome="SKIP_GTOS_VNEXT_BROADER_ORIGIN_NEWS_BLOCKED",
                    reason=f"vnext_broader_origin_news:{cal_reason}",
                    decision_path=(
                        "vnext_broader_origin_news_blocked_consumed_before_old_primary_"
                        "analyzer_and_l2"
                    ),
                )
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="GTOS_VNEXT_BROADER_ORIGIN_NEWS_BLOCKED",
                    prescreen_status="PASSED",
                    reason=cal_reason,
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "SKIP_GTOS_VNEXT_BROADER_ORIGIN_NEWS_BLOCKED",
                    f"vnext_broader_origin_news:{cal_reason}",
                    kill_zone,
                )
                return "SKIP_GTOS_VNEXT_BROADER_ORIGIN_NEWS_BLOCKED"

        if news_calendar is None or not getattr(news_calendar, "enabled", False):
            blocked, cal_reason = should_block_trading(
                getattr(self, "_calendar", None),
                candle_time_utc,
                self._symbol,
                self.config,
            )
            if blocked:
                self._record_vnext_broader_origin_safety_gate_block(
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    candidates=candidates,
                    final_outcome="BLOCKED_GTOS_VNEXT_BROADER_ORIGIN_CALENDAR",
                    reason=f"vnext_broader_origin_calendar:{cal_reason}",
                    decision_path=(
                        "vnext_broader_origin_calendar_blocked_consumed_before_old_primary_"
                        "analyzer_and_l2"
                    ),
                )
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="GTOS_VNEXT_BROADER_ORIGIN_ECONOMIC_CALENDAR_BLOCKED",
                    prescreen_status="PASSED",
                    reason=cal_reason,
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "BLOCKED_GTOS_VNEXT_BROADER_ORIGIN_CALENDAR",
                    f"vnext_broader_origin_calendar:{cal_reason}",
                    kill_zone,
                )
                return "BLOCKED_GTOS_VNEXT_BROADER_ORIGIN_CALENDAR"
        return None

    def _vnext_broader_origin_cross_asset_raw_data(self) -> dict | None:
        cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
        if not bool(cfg.get("moonshot_broader_origin_cross_asset_fetch_enabled", True)):
            return None
        current = self._vnext_canonical_symbol_key(self._symbol)
        leaders = sorted(
            {
                leader
                for leader, lag in LEAD_LAG_PAIRS
                if self._vnext_canonical_symbol_key(lag) == current
            }
        )
        if not leaders or self.mt5 is None:
            return None
        count = int(cfg.get("moonshot_broader_origin_cross_asset_fetch_bars", 80) or 80)
        timeframe = TF_MAP.get("M15", 15)
        raw_by_symbol: dict[str, dict] = {}
        for leader in leaders:
            broker_symbol = VNEXT_BROADER_ORIGIN_BROKER_ALIASES.get(
                self._vnext_canonical_symbol_key(leader),
                leader,
            )
            try:
                candles = self.mt5.get_candles(broker_symbol, timeframe, count) or []
            except Exception as exc:  # noqa: BLE001 - one leader must not break others.
                logger.debug(
                    "GTOS_VNEXT_BROADER_ORIGIN cross-asset fetch failed %s/%s: %s",
                    leader,
                    broker_symbol,
                    exc,
                )
                continue
            if len(candles) >= 51:
                raw_by_symbol[leader] = {
                    "symbol": leader,
                    "candles": {"M15": candles},
                }
        return {"raw_data_by_symbol": raw_by_symbol} if raw_by_symbol else None

    @staticmethod
    def _vnext_canonical_symbol_key(value) -> str:
        return str(value or "").strip().upper().replace(".", "_")

    def _execute_vnext_broader_origin_candidate(
        self,
        *,
        candidate: dict,
        raw_data: dict,
        mso,
        kill_zone: str,
    ) -> str:
        analysis = _make_synthetic_moonshot_analysis(candidate)
        record = self._create_vnext_broader_origin_record(
            candidate=candidate,
            analysis=analysis,
            raw_data=raw_data,
            mso=mso,
            kill_zone=kill_zone,
        )
        vnext_decision = self._vnext_broader_origin_runtime_decision(candidate)
        if record is not None:
            attach_vnext_decision_to_record(record, vnext_decision)
        record_vnext_runtime_decision(
            decision=vnext_decision,
            config=self.config,
            phase="broader_origin_pre_ai_candidate",
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=str(
                candidate.get("candle_close_utc")
                or self._vnext_effective_candle_time(raw_data)
                or ""
            ),
        )

        self.session_state["current_kill_zone"] = kill_zone
        self.session_state["deterministic_bias"] = "no_bias"
        tc_cfg = self.config.get("trade_capture", {})
        vnext_block_reason = vnext_execution_block_reason(vnext_decision, self.config)
        if vnext_block_reason:
            # Broader-origin live candidates must not be terminally blocked by
            # pre-dynamic vNext risk/source summaries. Selected-cell risk,
            # LTF path, tick/broker snapshots, and executable geometry are
            # resolved below; terminal refusal belongs to that source-backed
            # dynamic path.
            if record is not None:
                record.setdefault("decision_pipeline", {})[
                    "gtos_vnext_pre_dynamic_execution_block_projection"
                ] = {
                    "would_block": True,
                    "reason": vnext_block_reason,
                    "terminal_authority": (
                        "deferred_until_moonshot_dynamic_execution_and_"
                        "geometry_repair"
                    ),
                }
                record.setdefault("instrumentation", {})[
                    "gtos_vnext_pre_dynamic_execution_block_deferred"
                ] = True

        pre_geometry_denial = check_permissions(
            analysis,
            mso,
            self.session_state,
            self.mt5,
            config=self.config,
            symbol=self._mt5_symbol,
            skip_gate1_safety=True,
        )
        pre_geometry_advisory_denial = None
        if (
            pre_geometry_denial is not None
            and getattr(pre_geometry_denial, "gate", None) == "gate3_circuit_breaker"
            and getattr(pre_geometry_denial, "reason", None)
            in {"spread_too_wide", "concurrent_cap_reached"}
        ):
            pre_geometry_advisory_denial = pre_geometry_denial
            pre_geometry_denial = None
        if record is not None:
            try:
                pre_geometry_gate3 = build_gate3_result(
                    pre_geometry_advisory_denial or pre_geometry_denial,
                    self.session_state,
                    self.mt5,
                    symbol=self._mt5_symbol,
                )
                if pre_geometry_advisory_denial is not None:
                    advisory_reason = getattr(pre_geometry_advisory_denial, "reason", None)
                    pre_geometry_gate3["passed"] = True
                    pre_geometry_gate3.setdefault("checks_run", []).append(
                        f"{advisory_reason}_terminal_check_deferred_until_after_vnext_dynamic_geometry"
                    )
                    deferred_detail = {
                        "deferred": True,
                        "reason": advisory_reason,
                        "details": pre_geometry_advisory_denial.details,
                        "terminal_authority": (
                            "final_gate3_after_dynamic_router_selected_cell_risk_"
                            "geometry_repair_and_prop_governor"
                        ),
                    }
                    pre_geometry_gate3.setdefault("details", {})[
                        f"pre_geometry_{advisory_reason}_advisory"
                    ] = deferred_detail
                    if advisory_reason == "concurrent_cap_reached":
                        pre_geometry_gate3.setdefault("details", {}).setdefault(
                            "concurrent_cap", {}
                        ).update(
                            {
                                "status": (
                                    "deferred_until_selected_cell_account_risk_"
                                    "governed_final_gate3"
                                ),
                                "runtime_authority": "permissions.check_permissions",
                            }
                        )
                    else:
                        pre_geometry_gate3.setdefault("details", {})[
                            "pre_geometry_spread_advisory"
                        ] = deferred_detail
                    advisory_key = (
                        "pre_geometry_spread_advisory"
                        if advisory_reason == "spread_too_wide"
                        else f"pre_geometry_{advisory_reason}_advisory"
                    )
                    record.setdefault("decision_pipeline", {})[advisory_key] = deferred_detail
                update_gate_results(
                    record,
                    pre_geometry_gate3,
                    {
                        "passed": True,
                        "checks_run": ["deferred_until_vnext_executable_geometry_repair"],
                        "details": {
                            "gate1_deferred_for_vnext_broader_origin": True,
                            "reason": (
                                "raw broader-origin geometry must be repaired with "
                                "dynamic policy, LTF path, selected-cell risk, "
                                "broker spec, and prop governor before terminal "
                                "Gate1 rejection"
                            ),
                        },
                    },
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Trade capture: failed to update broader-origin pre-geometry gate results: %s", exc)
        if pre_geometry_denial:
            outcome = _permission_denial_runtime_outcome(pre_geometry_denial)
            if record is not None and tc_cfg.get("save_rejected", True):
                _attach_permission_denial_outcome_to_record(record, pre_geometry_denial, outcome)
                self._refresh_vnext_candidate_intelligence_packet(
                    record,
                    candidate=candidate,
                    raw_data=raw_data,
                    mso=mso,
                    analysis=analysis,
                    final_order_decision={
                        "final_outcome": outcome["final_outcome"],
                        "reached_order_path": False,
                        "order_path": "permission_rejected_before_geometry_repair",
                        "reason": outcome["candle_detail"],
                    },
                    repair_not_entered_reason="permission_denial_before_geometry_repair",
                )
                save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
            self._log_candle(
                outcome["candle_decision"],
                f"vnext_broader_origin:{outcome['candle_detail']}",
                kill_zone,
                produced_candidate=True,
            )
            return outcome["final_outcome"]

        equity = self.mt5.get_account_equity()
        base_risk_pct = self._drawdown_mgr.get_risk_pct(equity)
        autocorr_risk = self._apply_autocorrelation_risk_sizing(
            current_risk_pct=base_risk_pct,
            raw_data=raw_data,
            record=record,
        )
        base_risk_pct = autocorr_risk.after_risk_pct
        open_positions = self._get_open_positions_for_correlation()
        corr_adj = check_correlation_risk(
            symbol=self._symbol,
            base_risk_pct=base_risk_pct,
            open_positions=open_positions,
            config=self.config,
        )
        effective_risk_pct = corr_adj.final_risk_pct
        cross_corr_adj = _evaluate_cross_instrument_correlation(
            candidate_symbol=self._symbol,
            candidate_direction=analysis.trade_parameters.direction,
            mt5=self.mt5,
            config=self.config,
            evaluation_context="orchestrator_broader_origin_sizing_risk_adjustment",
        )
        if cross_corr_adj.action == "RISK_REDUCE_HALF":
            effective_risk_pct = _apply_cross_instrument_risk_multiplier(
                effective_risk_pct,
                cross_corr_adj,
            )
        vnext_risk_adjustment = self._apply_gtos_vnext_risk_adjustment(
            current_risk_pct=effective_risk_pct,
            vnext_decision=vnext_decision,
            record=record,
        )
        if vnext_risk_adjustment.applied:
            effective_risk_pct = vnext_risk_adjustment.after_risk_pct
        if effective_risk_pct <= 0:
            if record is not None:
                record.setdefault("decision_pipeline", {})[
                    "gtos_vnext_pre_dynamic_effective_risk_projection"
                ] = {
                    "effective_risk_pct": effective_risk_pct,
                    "reason": "effective_risk_pct_zero_or_negative",
                    "terminal_authority": (
                        "deferred_until_selected_cell_risk_and_geometry_repair"
                    ),
                }
                record.setdefault("instrumentation", {})[
                    "gtos_vnext_pre_dynamic_zero_risk_deferred"
                ] = True

        vnext_pending_policy = evaluate_vnext_pending_policy(
            decision=vnext_decision,
            config=self.config,
        )
        if record is not None:
            attach_vnext_pending_policy_to_record(record, vnext_pending_policy)
        tp = analysis.trade_parameters
        ltf_path_state = self._build_gtos_vnext_ltf_path_state(
            trade_params=tp,
            raw_data=raw_data,
            kill_zone=kill_zone,
        )
        vnext_ltf_path_execution = evaluate_vnext_ltf_path_execution(
            decision=vnext_decision,
            config=self.config,
            trade_params={
                "direction": tp.direction,
                "entry_price": tp.entry_price,
                "stop_loss": tp.stop_loss,
                "take_profit_1": tp.take_profit_1,
            },
            path_state=ltf_path_state,
        )
        if record is not None:
            attach_vnext_ltf_path_execution_to_record(record, vnext_ltf_path_execution)

        balance = self.mt5.get_account_balance()
        pending_intent = getattr(self.execution, "pending_intent", None)
        risk_base_amount = balance or equity
        open_position_exposure = self._open_position_risk_exposure_summary(
            open_positions,
            risk_base_amount,
        )
        pending_order_risk_pct = float(getattr(pending_intent, "risk_pct", 0.0) or 0.0)
        pending_order_risk_amount = (
            float(risk_base_amount or 0.0) * pending_order_risk_pct / 100.0
        )
        correlated_buffer_pct = sum(
            float(position.get("risk_pct", 0.0) or 0.0)
            for position in getattr(cross_corr_adj, "correlated_positions", []) or []
        )
        session_trade_count = int(self.session_state.get(f"trades_{kill_zone}", 0) or 0)
        runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        risk_cfg = self.config.get("risk", {}) or {}
        account_namespace = (
            broker_account_namespace(self.config)
            or runtime_cfg.get("prop_firm_headroom_required_account_namespace")
            or "gtos_runtime_account"
        )
        initial_balance = runtime_cfg.get(
            "prop_safe_selector_initial_balance",
            100000.0,
        )
        prop_account_state = {
            "schema_version": "prop_firm_headroom_account_state_v4",
            "account_namespace": account_namespace,
            "account_id": account_namespace,
            "initial_balance": initial_balance,
            "initial_equity_or_balance_baseline": initial_balance,
            "current_balance": balance,
            "current_equity": equity,
            "risk_base_amount": risk_base_amount,
            "day_start_equity_or_balance_baseline": (
                self.session_state.get("start_equity")
                or self.session_state.get("start_balance")
                or equity
            ),
            "daily_loss_limit_pct": runtime_cfg.get(
                "prop_safe_selector_external_daily_loss_limit_pct",
                risk_cfg.get("max_daily_loss_pct"),
            ),
            "overall_loss_limit_pct": runtime_cfg.get(
                "prop_safe_selector_external_overall_max_loss_pct",
                risk_cfg.get("max_portfolio_drawdown_pct"),
            ),
            "daily_reset_window_id": (
                f"{self.session_state.get('date') or datetime.now(timezone.utc).date().isoformat()}"
                f"/{account_namespace}"
            ),
            "open_position_risk_pct": open_position_exposure["open_position_risk_pct"],
            "open_position_risk_amount": open_position_exposure[
                "open_position_risk_amount"
            ],
            "open_position_count": open_position_exposure["open_position_count"],
            "open_position_risk_valued_count": open_position_exposure[
                "open_position_risk_valued_count"
            ],
            "open_position_risk_pct_fallback_count": open_position_exposure[
                "open_position_risk_pct_fallback_count"
            ],
            "open_position_risk_missing_count": open_position_exposure[
                "open_position_risk_missing_count"
            ],
            "open_position_risk_details": open_position_exposure[
                "open_position_risk_details"
            ],
            "open_position_risk_missing_positions": open_position_exposure[
                "open_position_risk_missing_positions"
            ],
            "pending_order_risk_pct": pending_order_risk_pct,
            "pending_order_risk_amount": pending_order_risk_amount,
            "new_trade_sl_risk_pct": effective_risk_pct,
            "correlated_exposure_buffer_pct": correlated_buffer_pct,
            "day_trade_count": int(self.session_state.get("trades_today", 0) or 0),
            "session_trade_count": session_trade_count,
            "symbol_day_trade_count": int(self.session_state.get("trades_today", 0) or 0),
            "symbol_session_trade_count": session_trade_count,
            "simultaneous_candidate_count": 1,
            "symbol": self._symbol,
            "route_session": kill_zone,
        }
        prop_context = {"symbol": self._symbol, "route_session": kill_zone}
        vnext_prop_safe_selector = evaluate_vnext_prop_safe_selector(
            decision=vnext_decision,
            config=self.config,
            current_risk_pct=effective_risk_pct,
            current_time_utc=datetime.now(timezone.utc),
            account_state=prop_account_state,
            candidate_context=prop_context,
        )
        pre_dynamic_prop_projection = vnext_prop_safe_selector
        if (
            vnext_prop_safe_selector.applied
            and vnext_prop_safe_selector.reason not in _VNEXT_PROP_PRE_DYNAMIC_HARD_BOUNDARY_REASONS
        ):
            # Before the dynamic router selects a current vNext risk cell, new-trade
            # budget actions are only projections. Terminal budget authority runs
            # again after selected-cell risk and executable geometry are known.
            vnext_prop_safe_selector = replace(
                vnext_prop_safe_selector,
                action="ALLOW",
                applied=False,
                after_risk_pct=round(float(effective_risk_pct), 12),
                reason=(
                    "pre_dynamic_projection_only_"
                    f"{pre_dynamic_prop_projection.reason}"
                ),
            )
        if record is not None:
            attach_vnext_prop_safe_selector_to_record(record, vnext_prop_safe_selector)
            if pre_dynamic_prop_projection is not vnext_prop_safe_selector:
                record.setdefault("decision_pipeline", {})[
                    "gtos_vnext_prop_safe_selector_pre_dynamic_projection"
                ] = pre_dynamic_prop_projection.to_record()
                record.setdefault("instrumentation", {})[
                    "gtos_vnext_prop_safe_selector_pre_dynamic_projection_only"
                ] = True
        if vnext_prop_safe_selector.applied:
            if vnext_prop_safe_selector.action == "REDUCE_RISK":
                effective_risk_pct = vnext_prop_safe_selector.after_risk_pct
            elif vnext_prop_safe_selector.action in {"DEFER_UNTIL_RESET", "BLOCK"}:
                final_outcome = (
                    "DEFERRED_GTOS_VNEXT_PROP_RESET"
                    if vnext_prop_safe_selector.action == "DEFER_UNTIL_RESET"
                    else "SKIPPED_GTOS_VNEXT_PROP_BUDGET"
                )
                if record is not None and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = final_outcome
                    self._refresh_vnext_candidate_intelligence_packet(
                        record,
                        candidate=candidate,
                        raw_data=raw_data,
                        mso=mso,
                        analysis=analysis,
                        final_order_decision={
                            "final_outcome": final_outcome,
                            "reached_order_path": False,
                            "order_path": "prop_budget_rejected_before_geometry_repair",
                            "reason": vnext_prop_safe_selector.reason,
                        },
                        repair_not_entered_reason="prop_budget_rejected_before_geometry_repair",
                    )
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._log_candle(final_outcome, vnext_prop_safe_selector.reason, kill_zone, produced_candidate=True)
                return final_outcome

        moonshot_context = self._vnext_broader_origin_moonshot_context(
            candidate=candidate,
            kill_zone=kill_zone,
            prop_selector=vnext_prop_safe_selector,
            analysis=analysis,
            mso=mso,
        )
        vnext_moonshot_dynamic_execution = self._evaluate_gtos_vnext_moonshot_dynamic_execution(
            vnext_decision=vnext_decision,
            raw_data=raw_data,
            kill_zone=kill_zone,
            record=record,
            candidate_context=moonshot_context,
        )
        self._record_gtos_vnext_replacement_monitoring(
            phase="broader_origin_pre_ai_candidate",
            raw_data=raw_data,
            kill_zone=kill_zone,
            record=record,
            vnext_decision=vnext_decision,
            vnext_risk_adjustment=vnext_risk_adjustment,
            vnext_pending_policy=vnext_pending_policy,
            vnext_ltf_path_execution=vnext_ltf_path_execution,
            vnext_prop_safe_selector=vnext_prop_safe_selector,
            vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
            source_capture_state={
                "source_complete": candidate.get("source_window_complete"),
                "source_window_complete": candidate.get("source_window_complete"),
                "same_bar_ambiguous": moonshot_context.get("same_bar_ambiguous"),
                "source_mode": moonshot_context.get("source_mode"),
                "source_path_feature_status": moonshot_context.get(
                    "source_path_feature_status"
                ),
                "ordered_path_status": moonshot_context.get("ordered_path_status"),
                "selected_policy_ordered_path_status": moonshot_context.get(
                    "selected_policy_ordered_path_status"
                ),
                "selected_policy_same_bar_ambiguous": moonshot_context.get(
                    "selected_policy_same_bar_ambiguous"
                ),
                "candidate_id": candidate.get("candidate_id"),
                "broker_symbol": self._mt5_symbol,
                "raw_geometry": moonshot_context.get("raw_geometry"),
                "trade_parameters": moonshot_context.get("trade_parameters"),
                "m15_source_fields": moonshot_context.get("m15_source_fields"),
                "mso_context": moonshot_context.get("mso_context"),
                "tick_snapshot": moonshot_context.get("tick_snapshot"),
                "broker_snapshot": moonshot_context.get("broker_snapshot"),
                "m15": {
                    "available": bool(moonshot_context.get("m15_source_fields")),
                    "latest_time_utc": candidate.get("candle_close_utc"),
                    "source_fields": moonshot_context.get("m15_source_fields"),
                },
                "tick": moonshot_context.get("tick_snapshot"),
            },
        )
        if not vnext_moonshot_dynamic_execution.applied:
            final_outcome = "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC"
            if record is not None and tc_cfg.get("save_rejected", True):
                record["decision_pipeline"]["final_outcome"] = final_outcome
                record["decision_pipeline"]["gtos_vnext_moonshot_dynamic_refusal_reasons"] = list(
                    vnext_moonshot_dynamic_execution.refusal_reasons
                )
                self._refresh_vnext_candidate_intelligence_packet(
                    record,
                    candidate=candidate,
                    raw_data=raw_data,
                    mso=mso,
                    analysis=analysis,
                    final_order_decision={
                        "final_outcome": final_outcome,
                        "reached_order_path": False,
                        "order_path": "dynamic_execution_refused_before_geometry_repair",
                        "reason": list(vnext_moonshot_dynamic_execution.refusal_reasons),
                    },
                    repair_not_entered_reason="dynamic_execution_not_applied_before_geometry_repair",
                )
                save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
            self._log_candle(
                final_outcome,
                str(list(vnext_moonshot_dynamic_execution.refusal_reasons)),
                kill_zone,
                produced_candidate=True,
            )
            return final_outcome

        dynamic_trade_context = self._vnext_dynamic_trade_context(
            vnext_moonshot_dynamic_execution
        )
        try:
            selected_cell_risk_pct = float(
                dynamic_trade_context.get("gtos_vnext_selected_cell_risk_pct")
            )
        except (TypeError, ValueError):
            selected_cell_risk_pct = None
        if selected_cell_risk_pct and selected_cell_risk_pct > 0:
            effective_risk_pct, selected_cell_risk_composition = (
                _compose_effective_risk_with_selected_cell(
                    effective_risk_pct,
                    selected_cell_risk_pct,
                )
            )
            if record is not None:
                record.setdefault("decision_pipeline", {})[
                    "gtos_vnext_selected_cell_risk_composition"
                ] = selected_cell_risk_composition
                record.setdefault("decision_pipeline", {})[
                    "effective_risk_pct"
                ] = effective_risk_pct
        execution_entry_price = tp.entry_price
        if (
            vnext_ltf_path_execution.applied
            and vnext_ltf_path_execution.action == "ADJUST_LIMIT_ENTRY"
            and vnext_ltf_path_execution.adjusted_entry_price is not None
        ):
            execution_entry_price = vnext_ltf_path_execution.adjusted_entry_price
        geometry_repair = self._repair_vnext_broader_origin_executable_geometry(
            candidate=candidate,
            analysis=analysis,
            mso=mso,
            entry_price=execution_entry_price,
            dynamic_trade_context=dynamic_trade_context,
            vnext_ltf_path_execution=vnext_ltf_path_execution,
            vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
            risk_pct=effective_risk_pct,
            account_balance=balance,
        )
        if record is not None:
            record.setdefault("decision_pipeline", {})[
                "gtos_vnext_executable_geometry_repair"
            ] = geometry_repair
            record.setdefault("instrumentation", {})[
                "gtos_vnext_executable_geometry_repair_status"
            ] = geometry_repair.get("status")
            self._refresh_vnext_candidate_intelligence_packet(
                record,
                candidate=candidate,
                raw_data=raw_data,
                mso=mso,
                analysis=analysis,
                final_order_decision={
                    "stage": "geometry_repair_completed",
                    "reached_order_path": False,
                    "order_path": "not_reached_yet",
                },
            )

        # Re-run the prop governor after selected-cell risk and repaired
        # executable geometry are known. Pre-dynamic projection cannot
        # terminally reject new-trade budget because it does not yet know the
        # selected-cell risk contract; this is the terminal live/replay parity
        # gate before final Gate1 and broker placement.
        prop_account_state["new_trade_sl_risk_pct"] = effective_risk_pct
        vnext_prop_safe_selector = evaluate_vnext_prop_safe_selector(
            decision=vnext_decision,
            config=self.config,
            current_risk_pct=effective_risk_pct,
            current_time_utc=datetime.now(timezone.utc),
            account_state=prop_account_state,
            candidate_context=prop_context,
        )
        if record is not None:
            attach_vnext_prop_safe_selector_to_record(record, vnext_prop_safe_selector)
            record.setdefault("decision_pipeline", {})[
                "gtos_vnext_prop_safe_selector_after_geometry_repair"
            ] = vnext_prop_safe_selector.to_record()
        if vnext_prop_safe_selector.applied:
            if vnext_prop_safe_selector.action == "REDUCE_RISK":
                effective_risk_pct = vnext_prop_safe_selector.after_risk_pct
            elif vnext_prop_safe_selector.action in {"DEFER_UNTIL_RESET", "BLOCK"}:
                final_outcome = (
                    "DEFERRED_GTOS_VNEXT_PROP_RESET"
                    if vnext_prop_safe_selector.action == "DEFER_UNTIL_RESET"
                    else "SKIPPED_GTOS_VNEXT_PROP_BUDGET"
                )
                if record is not None and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = final_outcome
                    self._refresh_vnext_candidate_intelligence_packet(
                        record,
                        candidate=candidate,
                        raw_data=raw_data,
                        mso=mso,
                        analysis=analysis,
                        final_order_decision={
                            "final_outcome": final_outcome,
                            "reached_order_path": False,
                            "order_path": "prop_budget_rejected_after_geometry_repair",
                            "reason": vnext_prop_safe_selector.reason,
                        },
                    )
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._log_candle(final_outcome, vnext_prop_safe_selector.reason, kill_zone, produced_candidate=True)
                return final_outcome

        if effective_risk_pct <= 0:
            final_outcome = "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_ZERO_RISK"
            if record is not None and tc_cfg.get("save_rejected", True):
                record["decision_pipeline"]["final_outcome"] = final_outcome
                record["decision_pipeline"]["effective_risk_pct"] = effective_risk_pct
                self._refresh_vnext_candidate_intelligence_packet(
                    record,
                    candidate=candidate,
                    raw_data=raw_data,
                    mso=mso,
                    analysis=analysis,
                    final_order_decision={
                        "final_outcome": final_outcome,
                        "reached_order_path": False,
                        "order_path": "zero_risk_after_dynamic_geometry_repair",
                        "reason": "effective_risk_pct_zero_or_negative_after_dynamic_geometry_repair",
                    },
                    repair_not_entered_reason=(
                        "zero_risk_after_dynamic_geometry_repair"
                    ),
                )
                save_trade_record(
                    record,
                    tc_cfg.get("base_path", "knowledge_base/trade_records"),
                )
            self._log_candle(
                final_outcome,
                "vnext_broader_origin_effective_risk_pct_zero_or_negative_after_dynamic_geometry_repair",
                kill_zone,
                produced_candidate=True,
            )
            return final_outcome

        prop_firm_headroom_snapshot = (
            build_prop_firm_headroom_snapshot_v4_from_account_state(
                prop_account_state,
                config=self.config,
                now_utc=datetime.now(timezone.utc),
            )
        )
        prop_account_state["gtos_vnext_prop_firm_headroom_snapshot_v4"] = (
            prop_firm_headroom_snapshot
        )
        setattr(
            tp,
            "gtos_vnext_prop_firm_headroom_snapshot_v4",
            prop_firm_headroom_snapshot,
        )

        final_vnext_trade_telemetry = self._gtos_vnext_pending_telemetry(
            vnext_pre_ai=None,
            vnext_decision=vnext_decision,
            vnext_risk_adjustment=vnext_risk_adjustment,
            vnext_pending_policy=vnext_pending_policy,
            vnext_ltf_path_execution=vnext_ltf_path_execution,
            vnext_prop_safe_selector=vnext_prop_safe_selector,
            vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
        )
        for key, value in final_vnext_trade_telemetry.items():
            if value not in (None, "", [], {}):
                setattr(tp, key, value)

        final_denial = check_permissions(
            analysis,
            mso,
            self.session_state,
            self.mt5,
            config=self.config,
            symbol=self._mt5_symbol,
        )
        if record is not None:
            try:
                update_gate_results(
                    record,
                    build_gate3_result(final_denial, self.session_state, self.mt5, symbol=self._mt5_symbol),
                    build_gate1_result(final_denial, analysis, mso),
                )
            except Exception as exc:  # noqa: BLE001
                logger.error("Trade capture: failed to update broader-origin final gate results: %s", exc)
        if final_denial:
            outcome = _permission_denial_runtime_outcome(final_denial)
            if record is not None and tc_cfg.get("save_rejected", True):
                _attach_permission_denial_outcome_to_record(record, final_denial, outcome)
                self._refresh_vnext_candidate_intelligence_packet(
                    record,
                    candidate=candidate,
                    raw_data=raw_data,
                    mso=mso,
                    analysis=analysis,
                    final_order_decision={
                        "final_outcome": outcome["final_outcome"],
                        "reached_order_path": False,
                        "order_path": "permission_rejected_after_repaired_geometry",
                        "reason": outcome["candle_detail"],
                    },
                )
                save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
            self._log_candle(
                outcome["candle_decision"],
                f"vnext_broader_origin:{outcome['candle_detail']}",
                kill_zone,
                produced_candidate=True,
            )
            return outcome["final_outcome"]

        risk_was_adjusted = (
            corr_adj.adjusted
            or cross_corr_adj.action == "RISK_REDUCE_HALF"
            or vnext_risk_adjustment.applied
            or autocorr_risk.applied
            or vnext_prop_safe_selector.applied
            or (selected_cell_risk_pct is not None and selected_cell_risk_pct > 0)
        )
        execution_entry_price = tp.entry_price
        market_entry_now = (
            vnext_pending_policy.applied
            and vnext_pending_policy.action == "MARKET_ENTRY_NOW"
        ) or (
            vnext_ltf_path_execution.applied
            and vnext_ltf_path_execution.action == "MARKET_ENTRY_NOW"
        )
        trade_params = {
            "direction": tp.direction,
            "entry_price": execution_entry_price,
            "stop_loss": tp.stop_loss,
            "take_profit_1": tp.take_profit_1,
            "take_profit_2": getattr(tp, "take_profit_2", None),
            "take_profit_3": getattr(tp, "take_profit_3", None),
            "risk_reward_ratio": tp.risk_reward_ratio,
            "gtos_vnext_prop_firm_headroom_account_state_v4": prop_account_state,
            "gtos_vnext_prop_firm_headroom_snapshot_v4": (
                prop_firm_headroom_snapshot
            ),
            **dynamic_trade_context,
            **final_vnext_trade_telemetry,
        }
        for key in (
            "candidate_id",
            "gtos_vnext_candidate_id",
            "gtos_vnext_decision_window_candidates",
            "decision_window_candidates",
            "gtos_vnext_same_symbol_lifecycle_v4_packet",
            "gtos_vnext_same_symbol_lifecycle_action",
            "gtos_vnext_same_symbol_lifecycle_reason",
            "gtos_vnext_scheduler_v4_packet",
            "gtos_vnext_scheduler_v4_packet_hash",
            "gtos_vnext_scheduler_v4_current_candidate_id",
            "gtos_vnext_scheduler_v4_selected_candidate_id",
            "gtos_vnext_scheduler_v4_selected_action_class",
            "gtos_vnext_scheduler_v4_decision_window_id",
            "gtos_vnext_selector_v4_action",
            "gtos_vnext_selector_v4_reason",
            "gtos_vnext_selector_v4_packet",
            "gtos_vnext_selector_v4_packet_hash",
            "gtos_vnext_probability_debate_v4_packet",
            "gtos_vnext_numeric_confluence_v4_packet",
            "gtos_vnext_follow_avoid_mixed_numeric_confluence_v4_packet",
            "gtos_vnext_pretrade_cost_model",
            "origin_family",
            "candidate_origin_family",
            "current_framework",
            "framework",
            "source_fields",
            "poi_state",
            "poi_state_hash_sha256",
            "poi_state_contract_status",
            "poi_state_contract_failures",
            "poi_state_contract_valid",
            "poi_state_execution_allowed",
            *POI_STATE_ATOMIC_FIELDS,
        ):
            value = getattr(tp, key, None)
            if value not in (None, "", [], {}):
                trade_params[key] = value
        if market_entry_now:
            trade_state = self.execution.open_trade(
                trade_params=trade_params,
                account_balance=balance,
                risk_pct_override=effective_risk_pct if risk_was_adjusted else None,
                kill_zone=kill_zone,
                trigger="gtos_vnext_broader_origin_market_entry",
            )
            if not trade_state:
                return self._finalize_vnext_broader_origin_failed_record(
                    record=record,
                    tc_cfg=tc_cfg,
                    final_outcome="GTOS_VNEXT_BROADER_ORIGIN_MARKET_ENTRY_FAILED",
                    kill_zone=kill_zone,
                    reason="open_trade returned None",
                )
            self._emit_dual_broker_intent(
                intent_type=DUAL_BROKER_MARKET_ENTRY,
                trade_params=trade_params,
                source_trade_id=trade_state.trade_id,
                candidate_id=candidate.get("candidate_id"),
                effective_risk_pct=effective_risk_pct,
                kill_zone=kill_zone,
                trigger="gtos_vnext_broader_origin_market_entry",
                telemetry_context={
                    "candidate_id": candidate.get("candidate_id"),
                    "origin_family": candidate.get("origin_family"),
                    "route_session": candidate.get("route_session") or kill_zone,
                    "utc_hour_bucket": candidate.get("utc_hour_bucket"),
                    **dynamic_trade_context,
                },
                primary_order={
                    "ticket": trade_state.ticket,
                    "entry_price": trade_state.entry_price,
                    "initial_volume": trade_state.initial_volume,
                    "entry_order_ticket": trade_state.entry_order_ticket,
                    "entry_deal_ticket": trade_state.entry_deal_ticket,
                    "entry_order_retcode": trade_state.entry_order_retcode,
                },
            )
            self._save_vnext_broader_origin_market_record(
                record=record,
                tc_cfg=tc_cfg,
                trade_state=trade_state,
                effective_risk_pct=effective_risk_pct,
                vnext_pending_policy=vnext_pending_policy,
                vnext_ltf_path_execution=vnext_ltf_path_execution,
                vnext_prop_safe_selector=vnext_prop_safe_selector,
                vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
            )
            try:
                self._init_trade_tracking(trade_state)
            except Exception as exc:  # noqa: BLE001
                logger.error("Exit tracking init failed on broader-origin market entry: %s", exc)
            self._log_candle("EXECUTED", trade_state.trade_id, kill_zone, produced_candidate=True)
            return "EXECUTED_GTOS_VNEXT_BROADER_ORIGIN_MARKET"

        pending_telemetry_context = {
            "source_branch": "gtos_vnext_broader_origin_pre_ai",
            "candidate_id": candidate.get("candidate_id"),
            "origin_family": candidate.get("origin_family"),
            "source_symbol": self._mt5_symbol,
            "kill_zone": kill_zone,
            "route_session": candidate.get("route_session") or kill_zone,
            "utc_hour_bucket": candidate.get("utc_hour_bucket"),
            "source_window_complete": candidate.get("source_window_complete"),
            "source_path_feature_status": candidate.get("source_path_feature_status"),
            "live_generation_status": candidate.get("live_generation_status"),
            **dynamic_trade_context,
            "gtos_vnext_moonshot_dynamic_execution": (
                vnext_moonshot_dynamic_execution.to_record()
            ),
        }
        pending_telemetry_context.update(
            self._gtos_vnext_pending_telemetry(
                vnext_pre_ai=None,
                vnext_decision=vnext_decision,
                vnext_risk_adjustment=vnext_risk_adjustment,
                vnext_pending_policy=vnext_pending_policy,
                vnext_ltf_path_execution=vnext_ltf_path_execution,
                vnext_prop_safe_selector=vnext_prop_safe_selector,
                vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
            )
        )
        pending = self.execution.set_limit_intent(
            trade_params=trade_params,
            account_balance=balance,
            risk_pct_override=effective_risk_pct if risk_was_adjusted else None,
            telemetry_context=pending_telemetry_context,
        )
        if not pending:
            return self._finalize_vnext_broader_origin_failed_record(
                record=record,
                tc_cfg=tc_cfg,
                final_outcome="GTOS_VNEXT_BROADER_ORIGIN_LIMIT_INTENT_FAILED",
                kill_zone=kill_zone,
                reason="set_limit_intent returned None",
            )
        self._emit_dual_broker_intent(
            intent_type=DUAL_BROKER_PENDING_LIMIT,
            trade_params=trade_params,
            source_trade_id=pending.trade_id,
            candidate_id=candidate.get("candidate_id"),
            effective_risk_pct=effective_risk_pct,
            kill_zone=kill_zone,
            trigger="gtos_vnext_broader_origin_pending_limit",
            telemetry_context=pending_telemetry_context,
            primary_order={
                "pending_order_mode": pending.pending_order_mode,
                "broker_pending_order_created": pending.broker_pending_order_created,
                "mt5_order_ticket": pending.mt5_order_ticket,
                "native_pending_order_type": pending.native_pending_order_type,
            },
        )
        pending_final_target_r = getattr(pending, "gtos_vnext_dynamic_final_target_r", None)
        notify_limit_placed(
            symbol=self._symbol,
            direction=pending.direction,
            entry=pending.limit_price,
            sl=pending.stop_loss,
            tp=pending.take_profit_1,
            rr=float(
                pending_final_target_r
                if pending_final_target_r not in (None, "")
                else trade_params.get("risk_reward_ratio", 1.5) or 1.5
            ),
            kill_zone=kill_zone,
            trade_id=pending.trade_id,
            dynamic_policy=getattr(pending, "gtos_vnext_dynamic_policy_selected", None),
            risk_pct=getattr(pending, "risk_pct", None),
            origin_family=getattr(pending, "gtos_vnext_origin_family", None),
            selector_ref=(
                getattr(pending, "gtos_vnext_selector_row_id", None)
                or getattr(pending, "gtos_vnext_selector_proof_hash", None)
                or getattr(pending, "gtos_vnext_source_event_hash", None)
            ),
            vnext_context=build_vnext_notification_context(
                pending,
                lifecycle_event="limit_placed",
            ),
        )
        self._save_vnext_broader_origin_pending_record(
            record=record,
            tc_cfg=tc_cfg,
            pending=pending,
            vnext_pending_policy=vnext_pending_policy,
            vnext_ltf_path_execution=vnext_ltf_path_execution,
            vnext_prop_safe_selector=vnext_prop_safe_selector,
            vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
        )
        self._log_candle(
            "LIMIT_PLACED",
            pending.trade_id,
            kill_zone,
            extended_kz=False,
            kz_sub_window=kill_zone,
            produced_candidate=True,
        )
        return "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"

    def _create_vnext_broader_origin_record(
        self,
        *,
        candidate: dict,
        analysis,
        raw_data: dict,
        mso,
        kill_zone: str,
    ) -> dict | None:
        tc_cfg = self.config.get("trade_capture", {})
        if not tc_cfg.get("enabled", True):
            return None
        try:
            record = create_trade_record(
                symbol=self._symbol,
                kill_zone=kill_zone,
                candle_time=candidate.get("candle_close_utc") or raw_data.get("candle_close_utc"),
                mso=mso,
                prompt_system="GTOS vNext broader-origin live generator",
                prompt_user="No paid AI call; candidate generated from closed source bars.",
                ai_response=analysis.model_dump(mode="json"),
                cross_instrument_context=getattr(self, "_ci_context_text", ""),
                session_memory="",
                config=self.config,
            )
            record.setdefault("metadata", {})["candle_close_utc"] = (
                candidate.get("candle_close_utc") or raw_data.get("candle_close_utc")
            )
            candidate_id = str(candidate.get("candidate_id") or "").strip()
            if candidate_id:
                metadata = record.setdefault("metadata", {})
                metadata["candidate_id"] = candidate_id
                metadata["broader_origin_candidate_id"] = candidate_id
                metadata["parent_candle_trade_id"] = metadata.get("trade_id")
                metadata["trade_id"] = f"{metadata.get('trade_id')}_{candidate_id}"
            pipeline = record.setdefault("decision_pipeline", {})
            pipeline["candidate_source"] = "gtos_vnext_broader_origin_live_generator"
            pipeline["old_primary_analyzer_called"] = False
            pipeline["old_l2_required"] = False
            pipeline["level2_verification"] = {
                "passed": None,
                "checks": [],
                "blocked_by": None,
                "not_run_reason": "broader_origin_pre_ai_path_uses_vnext_runtime_contract",
            }
            record["moonshot_broader_origin_candidate"] = dict(candidate)
            self._refresh_vnext_candidate_intelligence_packet(
                record,
                candidate=candidate,
                raw_data=raw_data,
                mso=mso,
                analysis=analysis,
                final_order_decision={
                    "stage": "candidate_record_created",
                    "reached_order_path": False,
                    "order_path": "not_reached_yet",
                },
            )
            return record
        except Exception as exc:  # noqa: BLE001
            logger.error("Trade capture: failed to create broader-origin record: %s", exc)
            return None

    @staticmethod
    def _jsonable_vnext_snapshot(value, *, max_depth: int = 5, max_items: int = 80):
        if max_depth < 0:
            return str(value)
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            out = {}
            for idx, (key, item) in enumerate(value.items()):
                if idx >= max_items:
                    out["_truncated"] = True
                    break
                if str(key).startswith("_"):
                    continue
                out[str(key)] = SessionOrchestrator._jsonable_vnext_snapshot(
                    item,
                    max_depth=max_depth - 1,
                    max_items=max_items,
                )
            return out
        if isinstance(value, (list, tuple, set)):
            values = list(value)
            out = [
                SessionOrchestrator._jsonable_vnext_snapshot(
                    item,
                    max_depth=max_depth - 1,
                    max_items=max_items,
                )
                for item in values[:max_items]
            ]
            if len(values) > max_items:
                out.append({"_truncated": True, "total_items": len(values)})
            return out
        if hasattr(value, "model_dump"):
            try:
                return SessionOrchestrator._jsonable_vnext_snapshot(
                    value.model_dump(mode="json"),
                    max_depth=max_depth - 1,
                    max_items=max_items,
                )
            except Exception:  # noqa: BLE001
                pass
        if hasattr(value, "__dict__"):
            return SessionOrchestrator._jsonable_vnext_snapshot(
                {
                    key: item
                    for key, item in vars(value).items()
                    if not str(key).startswith("_")
                },
                max_depth=max_depth - 1,
                max_items=max_items,
            )
        return str(value)

    def _vnext_mso_timeframe_packet(self, mso) -> dict:
        mso_snapshot = self._jsonable_vnext_snapshot(mso, max_depth=6)
        timeframes = {}
        if isinstance(mso_snapshot, dict):
            raw_timeframes = mso_snapshot.get("timeframes")
            if isinstance(raw_timeframes, dict):
                timeframes = raw_timeframes
        packet: dict[str, dict] = {}
        for timeframe in ("D1", "H4", "H1", "M15"):
            context = timeframes.get(timeframe)
            if context is None:
                packet[timeframe] = {
                    "available": False,
                    "missing_reason": "timeframe_absent_from_mso_snapshot",
                }
            else:
                packet[timeframe] = {
                    "available": True,
                    "context": context,
                }
        if isinstance(mso_snapshot, dict):
            packet["_mso_timestamp_utc"] = mso_snapshot.get("timestamp_utc")
            packet["_data_quality"] = mso_snapshot.get("data_quality")
        return packet

    def _vnext_tick_spread_packet(self) -> dict:
        if self.mt5 is None:
            return {"available": False, "missing_reason": "mt5_interface_unavailable"}
        try:
            tick = self.mt5.get_tick(self._mt5_symbol)
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "missing_reason": f"tick_fetch_exception:{exc}"}
        if tick is None:
            return {"available": False, "missing_reason": "mt5_tick_unavailable"}
        return {
            "available": True,
            "symbol": self._symbol,
            "broker_symbol": self._mt5_symbol,
            "bid": self._float_or_none(getattr(tick, "bid", None)),
            "ask": self._float_or_none(getattr(tick, "ask", None)),
            "last": self._float_or_none(getattr(tick, "last", None)),
            "spread": self._float_or_none(getattr(tick, "spread", None)),
            "spread_cents": self._float_or_none(getattr(tick, "spread_cents", None)),
            "time": getattr(tick, "time", None),
            "time_msc": getattr(tick, "time_msc", None),
        }

    def _vnext_dynamic_policy_intent_packet(
        self,
        *,
        candidate: dict,
        runtime_event: dict,
    ) -> dict:
        """Return the current production policy intent without marking routing as run."""

        runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        event = dict(runtime_event) if isinstance(runtime_event, dict) else {}
        event.setdefault("framework", candidate.get("framework") or candidate.get("origin_family"))
        event.setdefault("route_family", candidate.get("origin_family"))
        event.setdefault("candidate_origin_family", candidate.get("candidate_origin_family"))
        event.setdefault("side", candidate.get("side") or candidate.get("direction"))
        event.setdefault("route_session", candidate.get("route_session") or candidate.get("session"))
        event.setdefault("session_bucket", candidate.get("session_bucket"))
        event.setdefault("utc_hour_bucket", candidate.get("utc_hour_bucket"))
        event.setdefault(
            "primary_policy",
            runtime_cfg.get("moonshot_dynamic_execution_router_policy")
            or MOONSHOT_DEFAULT_EXECUTION_POLICY,
        )
        event.setdefault(
            "partial_exception_origin_families",
            runtime_cfg.get(
                "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
            ),
        )
        event.setdefault(
            "partial_exception_policy",
            runtime_cfg.get("moonshot_dynamic_execution_router_momentum_exception_policy"),
        )
        try:
            selected_policy, displacement_bucket = _select_moonshot_asof_policy(event)
        except Exception as exc:  # noqa: BLE001 - proof packet must not break capture.
            selected_policy = (
                str(
                    runtime_cfg.get("moonshot_dynamic_execution_router_policy")
                    or MOONSHOT_DEFAULT_EXECUTION_POLICY
                )
                .strip()
                .lower()
            )
            displacement_bucket = "policy_intent_exception"
            return {
                "status": "policy_intent_fallback_after_exception",
                "exception": str(exc),
                "selected_policy": selected_policy,
                "execution_policy_id": MOONSHOT_EXECUTION_POLICY_IDS.get(selected_policy),
                "displacement_bucket": displacement_bucket,
                "source": "runtime_config_fallback",
            }
        return {
            "status": "current_production_policy_intent",
            "selected_policy": selected_policy,
            "execution_policy_id": MOONSHOT_EXECUTION_POLICY_IDS.get(selected_policy),
            "displacement_bucket": displacement_bucket,
            "source": "moonshot_default_off_policy_router_configured_intent",
        }

    @staticmethod
    def _vnext_dynamic_not_run_reason(repair_not_entered_reason: str | None) -> str:
        if not repair_not_entered_reason:
            return "dynamic_router_not_reached_yet"
        if repair_not_entered_reason == "permission_denial_before_geometry_repair":
            return "permission_denial_before_dynamic_router"
        if repair_not_entered_reason.endswith("_before_geometry_repair"):
            return repair_not_entered_reason.replace(
                "_before_geometry_repair",
                "_before_dynamic_router",
            )
        return repair_not_entered_reason

    @staticmethod
    def _vnext_selected_cell_risk_packet(
        dynamic_record: dict,
        *,
        policy_intent: dict | None = None,
        not_run_reason: str | None = None,
    ) -> dict:
        router_record = dynamic_record.get("router_record") if isinstance(dynamic_record, dict) else {}
        if not isinstance(router_record, dict):
            router_record = {}
        route_dimensions = router_record.get("route_dimensions")
        if not isinstance(route_dimensions, dict):
            route_dimensions = {}
        source_event = dynamic_record.get("source_event") if isinstance(dynamic_record, dict) else {}
        if not isinstance(source_event, dict):
            source_event = {}
        def source_get(key, default=None):
            marker = object()
            value = route_dimensions.get(key, marker)
            if value is not marker and value not in (None, "", [], {}):
                return value
            fallback = source_event.get(key, marker)
            if fallback is not marker:
                return fallback
            if value is not marker:
                return value
            return default

        if not dynamic_record:
            reason = not_run_reason or "dynamic_router_not_reached_yet"
            policy_intent = policy_intent if isinstance(policy_intent, dict) else {}
            return {
                "ran": False,
                "not_run_reason": reason,
                "allowed": None,
                "risk_pct": None,
                "risk_pct_missing_reason": reason,
                "cell_id": None,
                "match_reason": "selected_cell_risk_not_applicable_before_dynamic_router",
                "required": None,
                "selected_policy": policy_intent.get("selected_policy"),
                "execution_policy_id": policy_intent.get("execution_policy_id"),
                "proof_reference": None,
                "status": "not_applicable_dynamic_router_not_reached",
            }
        allowed = source_get("selected_cell_risk_allowed")
        risk_pct = source_get("selected_cell_risk_pct")
        refusal_cause = source_get("selected_cell_risk_refusal_cause")
        match_reason = source_get("selected_cell_risk_match_reason")
        selected_policy = (
            source_get("selected_cell_risk_selected_policy")
            or dynamic_record.get("selected_policy")
        )
        source_policy = source_get("selected_cell_risk_source_policy")
        policy_identity_status = source_get("selected_cell_risk_policy_identity_status")
        if selected_policy and not policy_identity_status:
            policy_identity_status = (
                "selected_policy_inherited_from_dynamic_router_record"
            )
        risk_pct_missing_reason = None
        if risk_pct in (None, "", 0, 0.0):
            if refusal_cause:
                risk_pct_missing_reason = str(refusal_cause)
            elif match_reason:
                risk_pct_missing_reason = str(match_reason)
            elif allowed is False:
                risk_pct_missing_reason = "selected_cell_risk_not_allowed"
            else:
                risk_pct_missing_reason = "selected_cell_risk_pct_not_reported"
        return {
            "ran": True,
            "allowed": allowed,
            "risk_pct": risk_pct,
            "risk_pct_missing_reason": risk_pct_missing_reason,
            "cell_id": source_get("selected_cell_risk_cell_id"),
            "source_ledger_path": source_get("selected_cell_risk_source_ledger_path"),
            "source_row_identity": source_get("selected_cell_risk_source_row_identity"),
            "capture_contract": source_get("selected_cell_risk_capture_contract"),
            "decision_basis": source_get("selected_cell_risk_decision_basis"),
            "match_reason": match_reason,
            "required": source_get("selected_cell_risk_required"),
            "selected_policy": selected_policy,
            "source_policy": source_policy,
            "source_policy_missing_reason": (
                None if source_policy else "selected_cell_risk_source_policy_not_reported"
            ),
            "execution_policy_id": (
                source_get("selected_cell_risk_execution_policy_id")
                or dynamic_record.get("execution_policy_id")
            ),
            "policy_identity_status": policy_identity_status,
            "proof_reference": (
                source_get("selected_cell_risk_cell_id")
                or source_event.get("source_row_id")
                or source_event.get("row_id")
            ),
            "refusal_cause": refusal_cause,
            "failed_dimensions": source_get("selected_cell_risk_failed_dimensions") or [],
            "nearest_candidate": source_get("selected_cell_risk_nearest_candidate"),
            "unresolved_reasons": (
                source_get("selected_cell_risk_unresolved_reasons")
                or source_get("selected_cell_risk_execution_critical_unresolved_reasons")
                or []
            ),
            "status": (
                "verified_positive"
                if allowed is True and risk_pct not in (None, "", 0, 0.0)
                else "not_verified_or_zero"
            ),
        }

    def _vnext_v3_live_authority_packet(
        self,
        *,
        candidate: dict,
        runtime_event: dict,
        selected_cell_risk_packet: dict,
        selected_dynamic_policy: str | None,
        selected_execution_policy_id: str | None,
        broker_snapshot: dict,
        final_risk_authority: dict,
        source_context: dict | None = None,
    ) -> dict:
        """Attach V3 package authority proof without changing live execution."""

        runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        source_context = source_context if isinstance(source_context, dict) else {}

        def cfg_bool(key: str, default: bool = False) -> bool:
            value = runtime_cfg.get(key, default)
            if isinstance(value, bool):
                return value
            return str(value or "").strip().lower() in {"1", "true", "yes", "y"}

        package_config_paths = {
            "selector_v3": runtime_cfg.get("selector_v3_default_off_package_path"),
            "selector_v3_packet_schema": runtime_cfg.get(
                "selector_v3_runtime_packet_schema_path"
            ),
            "scheduler_v3": runtime_cfg.get("scheduler_v3_default_off_package_path"),
            "execution_policy_v3": runtime_cfg.get(
                "execution_policy_v3_default_off_package_path"
            ),
        }
        try:
            if self._v3_runtime_package_cache is None:
                repo_root = Path(__file__).resolve().parents[2]
                self._v3_runtime_package_cache = load_v3_runtime_package_set(repo_root)
            packages = self._v3_runtime_package_cache
        except Exception as exc:  # noqa: BLE001 - proof packet must fail closed.
            return {
                "schema_version": "gtos_vnext_v3_live_authority_packet_v1",
                "capture_mode": "native_live_writer_capture_only",
                "status": "v3_package_load_failed_capture_only",
                "exception": str(exc),
                "config_package_paths": package_config_paths,
                "runtime_effect_now": False,
                "broker_operation": False,
                "order_calls": 0,
                "paid_api_or_vendor_call": False,
                "runtime_effect_boundary": (
                    "v3_authority_capture_failed_closed_no_live_broker_effect"
                ),
            }

        source_window_complete = source_context.get("source_window_complete")
        if source_window_complete is True:
            source_completeness_state = "complete"
        elif source_window_complete is False:
            source_completeness_state = "incomplete"
        else:
            source_completeness_state = (
                source_context.get("source_path_feature_status")
                or source_context.get("source_completeness_state")
                or "unknown"
            )
        selector_event = dict(runtime_event) if isinstance(runtime_event, dict) else {}
        selector_event.update(
            {
                "symbol": (
                    selector_event.get("symbol")
                    or candidate.get("symbol")
                    or self._symbol
                ),
                "broker_symbol": self._mt5_symbol,
                "framework": (
                    selector_event.get("framework")
                    or candidate.get("framework")
                    or candidate.get("origin_family")
                ),
                "origin_family": (
                    selector_event.get("candidate_origin_family")
                    or selector_event.get("origin_family")
                    or candidate.get("candidate_origin_family")
                    or candidate.get("origin_family")
                ),
                "candidate_origin_family": (
                    selector_event.get("candidate_origin_family")
                    or candidate.get("candidate_origin_family")
                ),
                "side": (
                    selector_event.get("side")
                    or candidate.get("side")
                    or candidate.get("direction")
                ),
                "route_session": (
                    selector_event.get("route_session")
                    or candidate.get("route_session")
                    or candidate.get("session")
                ),
                "session_bucket": (
                    selector_event.get("session_bucket")
                    or candidate.get("session_bucket")
                ),
                "utc_hour_bucket": (
                    selector_event.get("utc_hour_bucket")
                    or candidate.get("utc_hour_bucket")
                ),
                "spread_r_bucket": (
                    selector_event.get("spread_r_bucket")
                    or source_context.get("spread_r_bucket")
                ),
                "source_completeness_state": source_completeness_state,
            }
        )
        risk_cfg = self.config.get("risk", {}) or {}
        account_state = {
            "account_balance": self.session_state.get("account_balance"),
            "account_equity": self.session_state.get("account_equity"),
            "day_start_baseline": self.session_state.get("day_start_baseline"),
            "realized_broker_or_proxy_pnl": self.session_state.get("daily_pnl_pct"),
            "open_worst_case_sl_risk_pct": None,
            "pending_worst_case_sl_risk_pct": None,
            "new_trade_worst_case_risk_pct": (
                final_risk_authority.get("final_order_effective_risk_pct")
                if isinstance(final_risk_authority, dict)
                else None
            )
            or (
                final_risk_authority.get("effective_risk_pct")
                if isinstance(final_risk_authority, dict)
                else None
            ),
            "approved_trade_risk_pct": (
                final_risk_authority.get("effective_risk_pct")
                if isinstance(final_risk_authority, dict)
                else None
            ),
            "selected_cell_risk_pct": selected_cell_risk_packet.get("risk_pct"),
            "portfolio_ceiling_pct": (
                self._float_or_none(risk_cfg.get("max_portfolio_drawdown_pct"))
                or self._float_or_none(risk_cfg.get("max_daily_loss_pct"))
            ),
            "correlation_cluster_ceiling_pct": None,
            "daily_overlay_limit_pct": risk_cfg.get("max_daily_loss_pct"),
            "external_daily_loss_limit_pct": runtime_cfg.get(
                "prop_safe_selector_external_daily_loss_limit_pct"
            ),
            "external_total_loss_limit_pct": runtime_cfg.get(
                "prop_safe_selector_external_overall_max_loss_pct"
            ),
            "same_symbol_risk_pct_before": None,
            "correlated_cluster_risk_pct_before": None,
            "actual_sl_distance_status": (
                "broker_symbol_info_available"
                if broker_snapshot.get("symbol_info_available")
                else "broker_symbol_info_missing"
            ),
            "lot_contract_geometry_status": (
                "broker_contract_size_available"
                if broker_snapshot.get("trade_contract_size") not in (None, "")
                else "broker_contract_size_missing"
            ),
            "drawdown_compression_state": None,
        }
        execution_context = {
            "selected_policy": selected_dynamic_policy,
            "current_policy": selected_dynamic_policy,
            "execution_policy_id": selected_execution_policy_id,
            "broker_lifecycle_source_complete": False,
            "ticket_bound_lifecycle_source_complete": False,
        }
        selector_packet = build_selector_v3_packet(
            selector_event,
            packages["selector_v3"],
            enabled=cfg_bool("selector_v3_enabled"),
            apply_to_execution=cfg_bool("selector_v3_apply_to_execution"),
        )
        scheduler_packet = build_scheduler_v3_packet(
            account_state,
            packages["scheduler_v3"],
            enabled=cfg_bool("scheduler_v3_enabled"),
            apply_to_execution=cfg_bool("scheduler_v3_apply_to_execution"),
        )
        execution_packet = build_execution_policy_v3_packet(
            execution_context,
            packages["execution_policy_v3"],
            enabled=cfg_bool("execution_policy_v3_enabled"),
            apply_to_execution=cfg_bool("execution_policy_v3_apply_to_execution"),
        )

        def disposition(packet: dict, enabled_key: str, apply_key: str) -> str:
            provenance = packet.get("package_provenance") or {}
            if not cfg_bool(enabled_key):
                return "package_present_config_disabled_default_off"
            if not cfg_bool(apply_key):
                return "package_present_observe_only_apply_disabled"
            if not provenance.get("live_activation_allowed_by_package"):
                return "package_present_package_forbids_live_activation"
            if packet.get("runtime_effect_now"):
                return "runtime_effect_enabled_by_config_and_package"
            return "package_present_no_runtime_effect"

        component_dispositions = {
            "selector_v3": {
                "enabled": cfg_bool("selector_v3_enabled"),
                "apply_to_execution": cfg_bool("selector_v3_apply_to_execution"),
                "runtime_disposition": disposition(
                    selector_packet,
                    "selector_v3_enabled",
                    "selector_v3_apply_to_execution",
                ),
            },
            "scheduler_v3": {
                "enabled": cfg_bool("scheduler_v3_enabled"),
                "apply_to_execution": cfg_bool("scheduler_v3_apply_to_execution"),
                "runtime_disposition": disposition(
                    scheduler_packet,
                    "scheduler_v3_enabled",
                    "scheduler_v3_apply_to_execution",
                ),
            },
            "execution_policy_v3": {
                "enabled": cfg_bool("execution_policy_v3_enabled"),
                "apply_to_execution": cfg_bool("execution_policy_v3_apply_to_execution"),
                "runtime_disposition": disposition(
                    execution_packet,
                    "execution_policy_v3_enabled",
                    "execution_policy_v3_apply_to_execution",
                ),
            },
        }
        runtime_effect_now = any(
            bool(packet.get("runtime_effect_now"))
            for packet in (selector_packet, scheduler_packet, execution_packet)
        )
        return {
            "schema_version": "gtos_vnext_v3_live_authority_packet_v1",
            "capture_mode": "native_live_writer_capture_only",
            "status": "v3_package_authority_captured_default_off",
            "config_package_paths": package_config_paths,
            "selector_event": selector_event,
            "scheduler_account_state": account_state,
            "execution_context": execution_context,
            "selector_v3": selector_packet,
            "scheduler_v3": scheduler_packet,
            "execution_policy_v3": execution_packet,
            "component_dispositions": component_dispositions,
            "runtime_effect_now": runtime_effect_now,
            "broker_operation": False,
            "order_calls": 0,
            "paid_api_or_vendor_call": False,
            "runtime_effect_boundary": (
                "v3_authority_packet_capture_only_no_live_broker_effect"
            ),
        }

    def _vnext_scheduler_v4_best_trade_allocator_packet(
        self,
        *,
        candidate: dict,
        runtime_event: dict,
        selected_cell_risk_packet: dict,
        final_risk_authority: dict,
        source_context: dict | None = None,
    ) -> dict:
        """Attach Scheduler V4 decision-window allocator proof without live effect."""

        runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        source_context = source_context if isinstance(source_context, dict) else {}

        def cfg_bool(key: str, default: bool = False) -> bool:
            value = runtime_cfg.get(key, default)
            if isinstance(value, bool):
                return value
            return str(value or "").strip().lower() in {"1", "true", "yes", "y"}

        def cfg_float(key: str, default: float) -> float:
            try:
                value = runtime_cfg.get(key, default)
                return float(value if value not in (None, "") else default)
            except (TypeError, ValueError):
                return default

        def cfg_list(key: str, default: list[str]) -> list[str]:
            value = runtime_cfg.get(key, default)
            if isinstance(value, str):
                return [part.strip() for part in value.split(",") if part.strip()]
            if isinstance(value, (list, tuple)):
                return [str(part).strip() for part in value if str(part).strip()]
            return list(default)

        config = {
            "enabled": cfg_bool("scheduler_v4_best_trade_allocator_enabled"),
            "apply_to_execution": cfg_bool(
                "scheduler_v4_best_trade_allocator_apply_to_execution"
            ),
            "live_activation_allowed": cfg_bool(
                "scheduler_v4_best_trade_allocator_live_activation_allowed"
            ),
            "portfolio_ceiling_pct": cfg_float(
                "scheduler_v4_best_trade_allocator_portfolio_ceiling_pct",
                4.0,
            ),
            "correlation_cluster_ceiling_pct": cfg_float(
                "scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct",
                1.5,
            ),
            "min_reduced_risk_pct": cfg_float(
                "scheduler_v4_best_trade_allocator_min_reduced_risk_pct",
                0.10,
            ),
            "min_trade_score": cfg_float(
                "scheduler_v4_best_trade_allocator_min_trade_score",
                0.35,
            ),
            "zero_trade_score": cfg_float(
                "scheduler_v4_best_trade_allocator_zero_trade_score",
                0.20,
            ),
            "allow_multiple_new_positions_per_window": cfg_bool(
                "scheduler_v4_best_trade_allocator_allow_multiple_new_positions_per_window"
            ),
            "pending_replacement_enabled": cfg_bool(
                "scheduler_v4_best_trade_allocator_pending_replacement_enabled",
                True,
            ),
            "pending_replacement_min_candidate_ev_r": cfg_float(
                "scheduler_v4_best_trade_allocator_pending_replacement_min_candidate_ev_r",
                0.65,
            ),
            "pending_replacement_min_candidate_probability": cfg_float(
                "scheduler_v4_best_trade_allocator_pending_replacement_min_candidate_probability",
                0.68,
            ),
            "pending_replacement_min_edge_delta": cfg_float(
                "scheduler_v4_best_trade_allocator_pending_replacement_min_edge_delta",
                0.20,
            ),
            "pending_replacement_min_pending_age_minutes": cfg_float(
                "scheduler_v4_best_trade_allocator_pending_replacement_min_pending_age_minutes",
                0.0,
            ),
            "require_full_window_source": cfg_bool(
                "scheduler_v4_best_trade_allocator_require_full_window_source"
            ),
            "critical_missing_source_tokens": cfg_list(
                "scheduler_v4_best_trade_allocator_critical_missing_source_tokens",
                [],
            ),
        }
        try:
            packet = build_scheduler_v4_runtime_capture_packet(
                candidate=candidate,
                runtime_event=runtime_event,
                selected_cell_risk_packet=selected_cell_risk_packet,
                final_risk_authority=final_risk_authority,
                source_context=source_context,
                config=config,
            )
        except Exception as exc:  # noqa: BLE001 - capture packet must fail closed.
            return {
                "schema_version": "scheduler_v4_best_trade_allocator_packet_v1",
                "component": "scheduler_v4_best_trade_allocator",
                "status": "scheduler_v4_packet_failed_closed_capture_only",
                "exception": str(exc),
                "config": config,
                "runtime_effect_now": False,
                "broker_operation": False,
                "order_calls": 0,
                "paid_api_or_vendor_call": False,
                "vps_process_change": False,
                "remote_push": False,
                "runtime_effect_boundary": (
                    "scheduler_v4_capture_failed_closed_no_live_broker_effect"
                ),
            }
        packet["component_disposition"] = (
            "staged_default_off_config_disabled"
            if not config["enabled"]
            else "staged_default_off_apply_disabled"
            if not config["apply_to_execution"]
            else "staged_default_off_live_activation_not_allowed"
            if not config["live_activation_allowed"]
            else "enabled_by_config_but_runtime_effect_still_packet_gated"
        )
        return packet

    def _refresh_vnext_candidate_intelligence_packet(
        self,
        record: dict | None,
        *,
        candidate: dict | None = None,
        raw_data: dict | None = None,
        mso=None,
        analysis=None,
        final_order_decision: dict | None = None,
        repair_not_entered_reason: str | None = None,
    ) -> dict | None:
        """Attach the row-level vNext proof packet required for replay parity."""
        if record is None:
            return None
        candidate = candidate if isinstance(candidate, dict) else (
            record.get("moonshot_broader_origin_candidate") or {}
        )
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        pipeline = record.setdefault("decision_pipeline", {})
        prior_packet = pipeline.get("gtos_vnext_candidate_intelligence_packet")
        if not isinstance(prior_packet, dict):
            prior_packet = {}
        metadata = record.setdefault("metadata", {})
        dynamic_record = pipeline.get("gtos_vnext_moonshot_dynamic_execution") or {}
        pending_policy = pipeline.get("gtos_vnext_pending_policy") or {}
        ltf_path = pipeline.get("gtos_vnext_ltf_path_execution") or {}
        repair = pipeline.get("gtos_vnext_executable_geometry_repair") or {}
        prop_before = pipeline.get("gtos_vnext_prop_safe_selector") or {}
        prop_after = pipeline.get("gtos_vnext_prop_safe_selector_after_geometry_repair")
        runtime = pipeline.get("gtos_vnext_runtime") or {}
        runtime_event = runtime.get("event") if isinstance(runtime, dict) else {}
        if not isinstance(runtime_event, dict):
            runtime_event = {}
        policy_intent = self._vnext_dynamic_policy_intent_packet(
            candidate=candidate,
            runtime_event=runtime_event,
        )
        dynamic_not_run_reason = self._vnext_dynamic_not_run_reason(
            repair_not_entered_reason
        )
        router_record = dynamic_record.get("router_record") if isinstance(dynamic_record, dict) else {}
        if not isinstance(router_record, dict):
            router_record = {}
        route_dimensions = router_record.get("route_dimensions")
        if not isinstance(route_dimensions, dict):
            route_dimensions = {}
        source_event = dynamic_record.get("source_event") if isinstance(dynamic_record, dict) else {}
        if not isinstance(source_event, dict):
            source_event = {}

        def dynamic_source_get(key, default=None):
            marker = object()
            value = route_dimensions.get(key, marker)
            if value is not marker and value not in (None, "", [], {}):
                return value
            fallback = source_event.get(key, marker)
            if fallback is not marker:
                return fallback
            if value is not marker:
                return value
            return default

        raw_trade_params = candidate.get("trade_parameters")
        if not isinstance(raw_trade_params, dict):
            raw_trade_params = {}
        else:
            raw_trade_params = dict(raw_trade_params)
        if analysis is not None:
            tp = getattr(analysis, "trade_parameters", None)
            if tp is not None:
                analysis_trade_params = {
                    "direction": getattr(tp, "direction", None),
                    "entry_price": self._float_or_none(getattr(tp, "entry_price", None)),
                    "stop_loss": self._float_or_none(getattr(tp, "stop_loss", None)),
                    "take_profit_1": self._float_or_none(getattr(tp, "take_profit_1", None)),
                    "risk_reward_ratio": self._float_or_none(
                        getattr(tp, "risk_reward_ratio", None)
                    ),
                }
                if hasattr(tp, "__dict__"):
                    for key, value in vars(tp).items():
                        if value not in (None, "", [], {}):
                            analysis_trade_params.setdefault(key, value)
                raw_trade_params.update(
                    {
                        key: value
                        for key, value in analysis_trade_params.items()
                        if value not in (None, "", [], {})
                    }
                )

        broker_snapshot = self._broker_geometry_snapshot()
        broker_snapshot = {
            key: value for key, value in broker_snapshot.items() if key != "_symbol_info"
        }
        if not broker_snapshot.get("symbol_info_available"):
            broker_snapshot.setdefault(
                "missing_reason",
                "broker_symbol_info_unavailable_or_not_exposed",
            )

        if repair:
            repair_path = {
                "entered": True,
                "status": repair.get("status"),
                "actions": repair.get("actions", []),
            }
            repaired_geometry = {
                "status": repair.get("status"),
                "geometry": repair.get("repaired"),
            }
            lot_recompute = repair.get("lot_recompute") or {
                "status": "not_available",
                "not_run_reason": "repair_lot_recompute_missing",
            }
        else:
            reason = repair_not_entered_reason
            if reason is None and dynamic_record and dynamic_record.get("applied") is False:
                reason = "dynamic_execution_not_applied_before_geometry_repair"
            if reason is None:
                reason = "geometry_repair_not_reached_yet"
            repair_path = {
                "entered": False,
                "status": "not_entered",
                "not_entered_reason": reason,
            }
            repaired_geometry = {
                "status": "not_run",
                "not_run_reason": reason,
                "geometry": None,
            }
            lot_recompute = {
                "status": "not_run",
                "not_run_reason": reason,
            }

        gate1 = pipeline.get("gate1_result")
        gate3 = pipeline.get("gate3_result")
        final_gate1_after_repair = {
            "ran_after_repair": bool(repair) and isinstance(gate1, dict)
            and "deferred_until_vnext_executable_geometry_repair"
            not in set(gate1.get("checks_run") or []),
            "output": gate1,
        }
        if not final_gate1_after_repair["ran_after_repair"]:
            final_gate1_after_repair["not_run_reason"] = (
                "geometry_repair_not_entered"
                if not repair
                else "gate1_output_missing_or_still_deferred"
            )

        final_outcome = (
            (final_order_decision or {}).get("final_outcome")
            or pipeline.get("final_outcome")
            or record.get("final_outcome")
        )
        if final_order_decision is None:
            reached_order_path = bool(record.get("limit_intent") or record.get("execution"))
            final_order_decision = {
                "final_outcome": final_outcome,
                "reached_order_path": reached_order_path,
                "order_path": (
                    "pending_limit"
                    if record.get("limit_intent")
                    else "market_order"
                    if record.get("execution")
                    else "not_reached"
                ),
            }
        else:
            final_order_decision = dict(final_order_decision)
            final_order_decision.setdefault("final_outcome", final_outcome)

        runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        selected_dynamic_policy = (
            dynamic_record.get("selected_policy")
            if isinstance(dynamic_record, dict)
            else None
        ) or policy_intent.get("selected_policy")
        selected_execution_policy_id = (
            dynamic_record.get("execution_policy_id")
            if isinstance(dynamic_record, dict)
            else None
        ) or policy_intent.get("execution_policy_id")
        dynamic_trigger_final_pullback = {
            "selected_policy": selected_dynamic_policy,
            "be_trigger_r": (
                runtime_cfg.get("moonshot_dynamic_execution_router_be_trigger_r")
                if selected_dynamic_policy == "be_after_trigger"
                else None
            ),
            "be_trigger_missing_reason": (
                None
                if selected_dynamic_policy == "be_after_trigger"
                else "selected_policy_not_be_after_trigger"
            ),
            "partial_trigger_r": (
                runtime_cfg.get("moonshot_dynamic_execution_router_partial_trigger_r")
                if selected_dynamic_policy == "partial_be_runner"
                else None
            ),
            "partial_final_target_r": (
                runtime_cfg.get("moonshot_dynamic_execution_router_partial_final_target_r")
                if selected_dynamic_policy == "partial_be_runner"
                else None
            ),
            "partial_close_ratio": (
                runtime_cfg.get("moonshot_dynamic_execution_router_partial_close_ratio")
                if selected_dynamic_policy == "partial_be_runner"
                else None
            ),
            "partial_fields_missing_reason": (
                None
                if selected_dynamic_policy == "partial_be_runner"
                else "selected_policy_not_partial_be_runner"
            ),
            "momentum_trigger_r": (
                runtime_cfg.get("moonshot_dynamic_execution_router_momentum_trigger_r")
                if selected_dynamic_policy == "momentum_exhaustion"
                else None
            ),
            "momentum_final_target_r": (
                runtime_cfg.get("moonshot_dynamic_execution_router_momentum_final_target_r")
                if selected_dynamic_policy == "momentum_exhaustion"
                else None
            ),
            "momentum_pullback_r": (
                runtime_cfg.get("moonshot_dynamic_execution_router_momentum_pullback_r")
                if selected_dynamic_policy == "momentum_exhaustion"
                else None
            ),
            "momentum_fields_missing_reason": (
                None
                if selected_dynamic_policy == "momentum_exhaustion"
                else "selected_policy_not_momentum_exhaustion"
            ),
            "repaired_dynamic_final_target_r": (
                (repair.get("dynamic_target") or {}).get("final_target_r")
                if repair
                else None
            ),
            "repaired_dynamic_final_target_price": (
                (repair.get("dynamic_target") or {}).get("final_target_price")
                if repair
                else None
            ),
            "repaired_target_missing_reason": (
                None if repair else "geometry_repair_not_entered"
            ),
        }
        selected_cell_risk_packet = self._vnext_selected_cell_risk_packet(
            dynamic_record if isinstance(dynamic_record, dict) else {},
            policy_intent=policy_intent,
            not_run_reason=dynamic_not_run_reason,
        )
        pipeline_effective_risk_pct = pipeline.get("effective_risk_pct")
        pre_geometry_effective_risk_pct = None
        if isinstance(prop_before, dict):
            pre_geometry_effective_risk_pct = (
                prop_before.get("after_risk_pct")
                if prop_before.get("after_risk_pct") is not None
                else prop_before.get("before_risk_pct")
            )
        post_geometry_effective_risk_pct = (
            prop_after.get("after_risk_pct")
            if isinstance(prop_after, dict)
            else None
        )
        selected_cell_effective_risk_pct = selected_cell_risk_packet.get("risk_pct")
        reached_order_path_for_risk = bool(final_order_decision.get("reached_order_path"))
        final_order_effective_risk_pct = (
            pipeline_effective_risk_pct
            if reached_order_path_for_risk and pipeline_effective_risk_pct is not None
            else selected_cell_effective_risk_pct
            if reached_order_path_for_risk and selected_cell_effective_risk_pct is not None
            else post_geometry_effective_risk_pct
            if reached_order_path_for_risk and post_geometry_effective_risk_pct is not None
            else None
        )
        effective_risk_pct_value = (
            pipeline_effective_risk_pct
            if pipeline_effective_risk_pct is not None
            else post_geometry_effective_risk_pct
            if post_geometry_effective_risk_pct is not None
            else pre_geometry_effective_risk_pct
        )
        final_risk_authority = {
            "authority": (
                "final_order_path_effective_risk"
                if final_order_effective_risk_pct is not None
                else "post_geometry_prop_safe_selector"
                if post_geometry_effective_risk_pct is not None
                else "selected_cell_source_risk_without_order_path"
                if selected_cell_effective_risk_pct is not None
                else "pre_geometry_prop_safe_selector"
                if pre_geometry_effective_risk_pct is not None
                else "pipeline_effective_risk_pct"
                if pipeline_effective_risk_pct is not None
                else "risk_not_reached_or_not_recorded"
            ),
            "pre_geometry_effective_risk_pct": pre_geometry_effective_risk_pct,
            "post_geometry_effective_risk_pct": post_geometry_effective_risk_pct,
            "selected_cell_effective_risk_pct": selected_cell_effective_risk_pct,
            "final_order_effective_risk_pct": final_order_effective_risk_pct,
            "effective_risk_pct": effective_risk_pct_value,
            "effective_risk_pct_role": (
                "final_order_risk"
                if final_order_effective_risk_pct is not None
                else "pre_order_projection"
            ),
            "legacy_authority": (
                "post_geometry_prop_safe_selector"
                if isinstance(prop_after, dict) and prop_after.get("after_risk_pct") is not None
                else "pre_geometry_prop_safe_selector"
                if isinstance(prop_before, dict)
                and (
                    prop_before.get("after_risk_pct") is not None
                    or prop_before.get("before_risk_pct") is not None
                )
                else "pipeline_effective_risk_pct"
                if pipeline.get("effective_risk_pct") is not None
                else "risk_not_reached_or_not_recorded"
            ),
            "selected_cell_risk_pct": selected_cell_risk_packet.get("risk_pct"),
            "selected_cell_risk_cell_id": selected_cell_risk_packet.get("cell_id"),
            "selected_cell_risk_status": selected_cell_risk_packet.get("status"),
            "selected_policy": selected_dynamic_policy,
            "execution_policy_id": selected_execution_policy_id,
            "prop_safe_before_geometry": prop_before or None,
            "prop_safe_after_geometry": prop_after if isinstance(prop_after, dict) else None,
        }
        tick_spread_packet = self._vnext_tick_spread_packet()
        candidate_quality_selector = dynamic_source_get("candidate_quality_selector")
        if not isinstance(candidate_quality_selector, dict):
            candidate_quality_selector = {
                "enabled": bool(
                    runtime_cfg.get("moonshot_candidate_quality_selector_enabled")
                ),
                "apply_to_execution": bool(
                    runtime_cfg.get(
                        "moonshot_candidate_quality_selector_apply_to_execution"
                    )
                ),
                "classification": "not_run_before_dynamic_router"
                if not dynamic_record
                else "not_reported_by_dynamic_router",
                "refusal_reason": dynamic_not_run_reason if not dynamic_record else None,
                "evidence_path": runtime_cfg.get(
                    "moonshot_candidate_quality_selector_evidence_path"
                ),
            }
        selector_bridge_proof = {
            "schema_version": "gtos_vnext_selector_bridge_proof_v1",
            "dynamic_router_ran": bool(dynamic_record),
            "dynamic_not_run_reason": None if dynamic_record else dynamic_not_run_reason,
            "current_policy_set": {
                "primary_policy": runtime_cfg.get(
                    "moonshot_dynamic_execution_router_policy"
                )
                or MOONSHOT_DEFAULT_EXECUTION_POLICY,
                "selected_policy": selected_dynamic_policy,
                "execution_policy_id": selected_execution_policy_id,
                "partial_exception_policy": runtime_cfg.get(
                    "moonshot_dynamic_execution_router_momentum_exception_policy"
                ),
                "partial_exception_origin_families": runtime_cfg.get(
                    "moonshot_dynamic_execution_router_momentum_exception_origin_families_to_partial_be_runner"
                ),
            },
            "policy_intent": policy_intent,
            "broader_origin_allowed": dynamic_source_get("broader_origin_allowed"),
            "broader_origin_match_reason": dynamic_source_get(
                "broader_origin_match_reason"
            ),
            "broader_origin_source_row_identity": dynamic_source_get(
                "broader_origin_source_row_identity"
            ),
            "broader_origin_capture_contract": dynamic_source_get(
                "broader_origin_capture_contract"
            ),
            "selected_cell_risk_source_row_identity": selected_cell_risk_packet.get(
                "source_row_identity"
            ),
            "selected_cell_risk_capture_contract": selected_cell_risk_packet.get(
                "capture_contract"
            ),
            "candidate_quality_selector": candidate_quality_selector,
            "spread_r_at_candidate": dynamic_source_get("spread_r_at_candidate"),
            "repaired_branch_allowed": (
                dynamic_record.get("candidate_use_allowed_now")
                if isinstance(dynamic_record, dict)
                else None
            ),
            "candidate_action": (
                dynamic_record.get("candidate_action")
                if isinstance(dynamic_record, dict)
                else None
            ),
        }
        v3_source_context = {
            "source_mode": dynamic_source_get(
                "source_mode",
                candidate.get("source_mode") or raw_data.get("source_mode"),
            ),
            "source_path_feature_status": dynamic_source_get(
                "source_path_feature_status",
                candidate.get("source_path_feature_status"),
            ),
            "source_window_complete": dynamic_source_get(
                "source_window_complete",
                candidate.get("source_window_complete"),
            ),
            "source_completeness_state": dynamic_source_get(
                "source_completeness_state"
            ),
            "spread_r_bucket": dynamic_source_get("spread_r_bucket"),
        }
        scheduler_source_context = dict(v3_source_context)
        decision_window_candidates = (
            candidate.get("decision_window_candidates")
            or raw_data.get("decision_window_candidates")
            or runtime_event.get("decision_window_candidates")
            or prior_packet.get("scheduler_decision_window_candidates")
        )
        if isinstance(decision_window_candidates, list):
            scheduler_source_context["decision_window_candidates"] = [
                row for row in decision_window_candidates if isinstance(row, dict)
            ]
        open_position_snapshot = None
        if self.mt5 is not None:
            try:
                positions = self.mt5.get_positions(self._mt5_symbol)
                if positions is not None:
                    open_position_snapshot = [
                        {
                            "exposure_id": getattr(position, "ticket", None),
                            "ticket": getattr(position, "ticket", None),
                            "symbol": getattr(position, "symbol", None),
                            "side": (
                                "LONG"
                                if getattr(position, "type", None) == 0
                                else "SHORT"
                                if getattr(position, "type", None) == 1
                                else None
                            ),
                            "risk_pct": getattr(position, "gtos_vnext_selected_cell_risk_pct", None),
                            "probability_at_entry": getattr(
                                position,
                                "gtos_vnext_probability_at_entry",
                                None,
                            ),
                            "ev_r_at_entry": getattr(
                                position,
                                "gtos_vnext_ev_r_at_entry",
                                None,
                            ),
                            "thesis_id": getattr(position, "gtos_vnext_thesis_id", None),
                            "lifecycle_phase": getattr(
                                position,
                                "gtos_vnext_lifecycle_phase",
                                None,
                            ),
                            "source_status": "broker_position_snapshot_read_only",
                        }
                        for position in positions
                    ]
            except Exception as exc:  # noqa: BLE001 - packet source gap only.
                scheduler_source_context["open_position_snapshot_error"] = str(exc)
        if open_position_snapshot is not None:
            scheduler_source_context["open_position_snapshot"] = open_position_snapshot
        pending_intent = getattr(getattr(self, "execution", None), "pending_intent", None)
        scheduler_source_context["pending_order_snapshot"] = (
            [
                {
                    "pending_id": getattr(pending_intent, "trade_id", None),
                    "symbol": getattr(pending_intent, "symbol", None),
                    "side": getattr(pending_intent, "direction", None),
                    "risk_pct": getattr(pending_intent, "risk_pct", None),
                    "limit_price": getattr(pending_intent, "limit_price", None),
                    "stop_loss": getattr(pending_intent, "stop_loss", None),
                    "mt5_order_ticket": getattr(pending_intent, "mt5_order_ticket", None),
                    "source_status": "execution_pending_intent_snapshot_read_only",
                }
            ]
            if pending_intent is not None
            else []
        )
        same_symbol_packet = (
            raw_trade_params.get("gtos_vnext_same_symbol_lifecycle_v4_packet")
            or candidate.get("gtos_vnext_same_symbol_lifecycle_v4_packet")
            or pipeline.get("same_symbol_lifecycle_v4")
        )
        if isinstance(same_symbol_packet, dict):
            scheduler_source_context["same_symbol_lifecycle_packet"] = same_symbol_packet
        probability_packet = pipeline.get("probability_debate_team_engine_v4")
        if isinstance(probability_packet, dict):
            scheduler_source_context["probability_debate_packet"] = probability_packet
        confluence_packet = (
            pipeline.get("follow_avoid_mixed_numeric_confluence")
            or pipeline.get("numeric_confluence")
        )
        if isinstance(confluence_packet, dict):
            scheduler_source_context["numeric_follow_avoid_mixed_packet"] = (
                confluence_packet
            )
        selector_packet = (
            raw_trade_params.get("gtos_vnext_selector_v4_packet")
            or candidate.get("gtos_vnext_selector_v4_packet")
            or pipeline.get("selector_v4")
            or pipeline.get("selector_v4_packet")
        )
        if isinstance(selector_packet, dict):
            scheduler_source_context["selector_v4_packet"] = selector_packet
        if isinstance(selected_cell_risk_packet, dict) and selected_cell_risk_packet:
            scheduler_source_context["selected_cell_risk_proof"] = (
                selected_cell_risk_packet
            )
        pretrade_cost_model = (
            raw_trade_params.get("gtos_vnext_pretrade_cost_model")
            or raw_trade_params.get("pretrade_cost_model")
            or candidate.get("gtos_vnext_pretrade_cost_model")
            or candidate.get("pretrade_cost_model")
            or pipeline.get("pretrade_cost_model")
            or pipeline.get("cost_model")
        )
        if isinstance(pretrade_cost_model, dict):
            scheduler_source_context["pretrade_cost_model"] = pretrade_cost_model
        source_event_hash = (
            raw_trade_params.get("gtos_vnext_source_event_hash")
            or raw_trade_params.get("source_event_hash")
            or raw_trade_params.get("source_event_hash_sha256")
            or candidate.get("gtos_vnext_source_event_hash")
            or candidate.get("source_event_hash")
            or candidate.get("source_event_hash_sha256")
            or runtime_event.get("source_event_hash")
            or runtime_event.get("source_event_hash_sha256")
            or selected_cell_risk_packet.get("source_event_hash")
            or selected_cell_risk_packet.get("source_event_hash_sha256")
            or selected_cell_risk_packet.get("source_hash")
        )
        if source_event_hash:
            scheduler_source_context["source_event_hash"] = str(source_event_hash)
        scheduler_source_context["zero_trade_value_calibration"] = {
            "status": "configured_zero_trade_score",
            "zero_trade_score": runtime_cfg.get(
                "scheduler_v4_best_trade_allocator_zero_trade_score"
            ),
        }
        v3_live_authority = self._vnext_v3_live_authority_packet(
            candidate=candidate,
            runtime_event=runtime_event,
            selected_cell_risk_packet=selected_cell_risk_packet,
            selected_dynamic_policy=selected_dynamic_policy,
            selected_execution_policy_id=selected_execution_policy_id,
            broker_snapshot=broker_snapshot,
            final_risk_authority=final_risk_authority,
            source_context=v3_source_context,
        )
        scheduler_v4_best_trade_allocator = (
            self._vnext_scheduler_v4_best_trade_allocator_packet(
                candidate=candidate,
                runtime_event=runtime_event,
                selected_cell_risk_packet=selected_cell_risk_packet,
                final_risk_authority=final_risk_authority,
                source_context=scheduler_source_context,
            )
        )

        packet = {
            "schema_version": "gtos_vnext_candidate_intelligence_packet_v1",
            "capture_mode": "native_live_writer",
            "capture_reason": "live_process_candidate_packet_writer",
            "old_primary_analyzer_called": bool(
                pipeline.get("old_primary_analyzer_called", False)
            ),
            "old_l2_required": bool(pipeline.get("old_l2_required", False)),
            "candidate_identity": {
                "candidate_id": candidate.get("candidate_id"),
                "trade_id": metadata.get("trade_id"),
                "symbol": metadata.get("symbol") or candidate.get("symbol") or self._symbol,
                "broker_symbol": self._mt5_symbol,
                "origin_family": candidate.get("origin_family") or runtime_event.get("route_family"),
                "candidate_origin_family": (
                    candidate.get("candidate_origin_family")
                    or runtime_event.get("candidate_origin_family")
                ),
                "framework": candidate.get("framework") or runtime_event.get("framework"),
                "side": candidate.get("side") or candidate.get("direction") or runtime_event.get("side"),
                "session": candidate.get("session") or metadata.get("kill_zone"),
                "kill_zone": metadata.get("kill_zone") or candidate.get("kill_zone"),
                "route_session": candidate.get("route_session") or runtime_event.get("route_session"),
                "utc_hour_bucket": candidate.get("utc_hour_bucket") or runtime_event.get("utc_hour_bucket"),
                "candle_close_utc": (
                    candidate.get("candle_close_utc")
                    or metadata.get("candle_close_utc")
                    or raw_data.get("candle_close_utc")
                ),
            },
            "source_m15": {
                "candle_open_utc": candidate.get("candle_open_utc"),
                "candle_close_utc": candidate.get("candle_close_utc")
                or raw_data.get("candle_close_utc"),
                "timeframe": candidate.get("timeframe") or "M15",
                "market_timeframe": candidate.get("market_timeframe") or "M15",
                "source_path_feature_status": candidate.get("source_path_feature_status"),
                "source_window_complete": candidate.get("source_window_complete"),
                "source_fields": candidate.get("source_fields") or {},
            },
            "mso_context": (
                self._vnext_mso_timeframe_packet(mso)
                if mso is not None
                else prior_packet.get("mso_context")
                or self._vnext_mso_timeframe_packet(None)
            ),
            "m1_ltf_availability": {
                "ran": bool(ltf_path),
                "not_run_reason": None if ltf_path else "ltf_path_execution_not_reached_yet",
                "source_complete": (ltf_path.get("path_state") or {}).get("source_complete"),
                "source_timeframe": (ltf_path.get("path_state") or {}).get("source_timeframe"),
                "path_source_status": (ltf_path.get("path_state") or {}).get("path_source_status"),
                "path_state": ltf_path.get("path_state"),
            },
            "tick_spread_snapshot": tick_spread_packet,
            "broker_spec_snapshot": broker_snapshot,
            "geometry": {
                "raw": {
                    "direction": raw_trade_params.get("direction") or candidate.get("direction"),
                    "entry_price": self._float_or_none(
                        raw_trade_params.get("entry_price", candidate.get("entry_price"))
                    ),
                    "stop_loss": self._float_or_none(
                        raw_trade_params.get("stop_loss", candidate.get("stop_loss"))
                    ),
                    "take_profit_1": self._float_or_none(
                        raw_trade_params.get("take_profit_1", candidate.get("take_profit_1"))
                    ),
                    "risk_reward_ratio": self._float_or_none(
                        raw_trade_params.get(
                            "risk_reward_ratio",
                            candidate.get("risk_reward_ratio"),
                        )
                    ),
                },
                "repair_path": repair_path,
                "repaired": repaired_geometry,
                "repair_thresholds": repair.get("thresholds") if repair else None,
                "dynamic_target": repair.get("dynamic_target") if repair else None,
            },
            "gates": {
                "gate0_deployment_profile_trading": {
                    "ran": True,
                    "phase": (self.config.get("deployment", {}) or {}).get("phase"),
                    "trading_enabled": bool(self.config.get("trading_enabled", True)),
                    "profile": self.config.get("profile") or self.config.get("active_profile"),
                },
                "gate1_pre_geometry": {
                    "ran": isinstance(gate1, dict),
                    "deferred_for_repair": isinstance(gate1, dict)
                    and "deferred_until_vnext_executable_geometry_repair"
                    in set(gate1.get("checks_run") or []),
                    "output": gate1,
                },
                "gate1_final_after_repair": final_gate1_after_repair,
                "gate3": {
                    "ran": isinstance(gate3, dict),
                    "output": gate3,
                },
            },
            "dynamic_policy": {
                "ran": bool(dynamic_record),
                "not_run_reason": None if dynamic_record else dynamic_not_run_reason,
                "policy_intent": policy_intent,
                "selected_policy_source": (
                    "dynamic_router_result"
                    if dynamic_record
                    else "pre_dynamic_current_production_policy_intent"
                ),
                "applied": dynamic_record.get("applied") if isinstance(dynamic_record, dict) else None,
                "selected_policy": selected_dynamic_policy,
                "execution_policy_id": selected_execution_policy_id,
                "decision_status": (
                    dynamic_record.get("decision_status")
                    if isinstance(dynamic_record, dict)
                    else None
                ),
                "candidate_action": (
                    dynamic_record.get("candidate_action")
                    if isinstance(dynamic_record, dict)
                    else None
                ),
                "source_quality_action": (
                    dynamic_record.get("source_quality_action")
                    if isinstance(dynamic_record, dict)
                    else None
                ),
                "prop_action": (
                    dynamic_record.get("prop_action")
                    if isinstance(dynamic_record, dict)
                    else None
                ),
                "dynamic_trigger_final_pullback": dynamic_trigger_final_pullback,
                "refusal_reasons": (
                    dynamic_record.get("refusal_reasons")
                    if isinstance(dynamic_record, dict)
                    else []
                ),
            },
            "selector_bridge_proof": selector_bridge_proof,
            "v3_live_authority": v3_live_authority,
            "scheduler_v4_best_trade_allocator": scheduler_v4_best_trade_allocator,
            "selected_cell_risk_proof": selected_cell_risk_packet,
            "risk_lot_calculation": {
                "autocorrelation_risk_sizing": pipeline.get("autocorrelation_risk_sizing"),
                "vnext_risk_adjustment": pipeline.get("gtos_vnext_risk_adjustment"),
                "prop_safe_selector_before_geometry": prop_before or None,
                "effective_risk_pct": effective_risk_pct_value,
                "lot_recompute": lot_recompute,
            },
            "final_risk_authority": final_risk_authority,
            "prop_governor": {
                "before_geometry_repair": prop_before or {
                    "ran": False,
                    "not_run_reason": "prop_safe_selector_not_reached_yet",
                },
                "after_geometry_repair": prop_after or {
                    "ran": False,
                    "not_run_reason": (
                        "geometry_repair_not_entered"
                        if not repair
                        else "prop_recheck_after_geometry_missing"
                    ),
                },
            },
            "pending_policy": {
                "ran": bool(pending_policy),
                "not_run_reason": None if pending_policy else "pending_policy_not_reached_yet",
                "record": pending_policy or None,
            },
            "runtime_decision": runtime,
            "final_order_decision": final_order_decision,
            "order_readiness": {
                "reached_order_path": bool(final_order_decision.get("reached_order_path")),
                "order_path": final_order_decision.get("order_path"),
                "final_outcome": final_order_decision.get("final_outcome"),
                "not_ready_reason": (
                    None
                    if final_order_decision.get("reached_order_path")
                    else final_order_decision.get("order_path")
                    or dynamic_not_run_reason
                    or "order_path_not_reached"
                ),
                "geometry_repair_status": repaired_geometry.get("status"),
                "selected_cell_risk_status": selected_cell_risk_packet.get("status"),
                "dynamic_policy_selected": selected_dynamic_policy,
                "execution_policy_id": selected_execution_policy_id,
            },
            "source_completeness": {
                "source_mode": dynamic_source_get(
                    "source_mode",
                    candidate.get("source_mode") or raw_data.get("source_mode"),
                ),
                "source_path_feature_status": dynamic_source_get(
                    "source_path_feature_status",
                    candidate.get("source_path_feature_status"),
                ),
                "source_window_complete": dynamic_source_get(
                    "source_window_complete",
                    candidate.get("source_window_complete"),
                ),
                "live_generation": "native_live_writer",
                "m1_ltf_available": bool(ltf_path),
                "tick_spread_available": bool(tick_spread_packet.get("available")),
                "broker_spec_available": bool(broker_snapshot.get("symbol_info_available")),
                "selected_policy_ordered_path_status": dynamic_source_get(
                    "selected_policy_ordered_path_status"
                ),
                "ordered_path_status": dynamic_source_get("ordered_path_status"),
                "selected_cell_capture_contract": selected_cell_risk_packet.get(
                    "capture_contract"
                ),
                "broader_origin_capture_contract": selector_bridge_proof.get(
                    "broader_origin_capture_contract"
                ),
            },
            "old_system_absence_proof": {
                "old_primary_analyzer_called": bool(
                    pipeline.get("old_primary_analyzer_called", False)
                ),
                "old_l2_required": bool(pipeline.get("old_l2_required", False)),
                "absence_status": (
                    "explicit_absent"
                    if not bool(pipeline.get("old_primary_analyzer_called", False))
                    and not bool(pipeline.get("old_l2_required", False))
                    else "legacy_component_flag_present"
                ),
                "current_system": "gtos_vnext_moonshot_production_replacement",
            },
            "refusal_and_repair_reasons": {
                "dynamic_refusal_reasons": (
                    dynamic_record.get("refusal_reasons")
                    if isinstance(dynamic_record, dict)
                    else []
                ),
                "recorded_dynamic_refusal_reasons": pipeline.get(
                    "gtos_vnext_moonshot_dynamic_refusal_reasons",
                    [],
                ),
                "permission_reason": pipeline.get("permission_reason"),
                "permission_gate": pipeline.get("permission_gate"),
                "repair_actions": repair.get("actions", []) if repair else [],
                "repair_not_entered_reason": (
                    repair_path.get("not_entered_reason")
                    if not repair_path.get("entered")
                    else None
                ),
            },
        }
        pipeline["gtos_vnext_candidate_intelligence_packet"] = packet
        attach_live_decision_packet_v4(
            record,
            legacy_packet=packet,
            candidate=candidate,
            raw_data=raw_data,
            runtime_config=runtime_cfg,
        )
        return packet

    def _vnext_broader_origin_runtime_decision(self, candidate: dict):
        cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
        enabled = bool(cfg.get("enabled", False))
        apply_to_execution = bool(enabled and cfg.get("apply_to_execution", False))
        raw_geometry = self._vnext_candidate_raw_geometry(candidate)
        source_fields = (
            dict(candidate.get("source_fields"))
            if isinstance(candidate.get("source_fields"), dict)
            else {}
        )
        null_zero_reasons = {
            f"raw_geometry.{key}": "candidate_geometry_field_missing"
            for key, value in raw_geometry.items()
            if key != "direction" and value is None
        }
        event = {
            "symbol": self._symbol,
            "source_symbol": self._mt5_symbol,
            "broker_symbol": self._mt5_symbol,
            "candidate_id": candidate.get("candidate_id"),
            "side": candidate.get("side") or candidate.get("direction"),
            "framework": candidate.get("framework") or candidate.get("origin_family"),
            "effective_framework": candidate.get("framework") or candidate.get("origin_family"),
            "route_family": candidate.get("origin_family"),
            "candidate_origin_family": candidate.get("candidate_origin_family"),
            "route_session": candidate.get("route_session"),
            "kill_zone": candidate.get("kill_zone"),
            "session": candidate.get("session"),
            "timeframe": candidate.get("timeframe"),
            "market_timeframe": candidate.get("market_timeframe"),
            "candle_time_utc": candidate.get("candle_close_utc"),
            "utc_hour_bucket": candidate.get("utc_hour_bucket"),
            "source_window_complete": candidate.get("source_window_complete"),
            "source_path_feature_status": candidate.get("source_path_feature_status"),
            "live_generation_status": candidate.get("live_generation_status"),
            "raw_geometry": raw_geometry,
        }
        return GTOSVNextRuntimeDecision(
            decision="FOLLOW",
            event={key: value for key, value in event.items() if value not in (None, "")},
            enabled=enabled,
            apply_to_execution=apply_to_execution,
            matched=True,
            reason="broader_origin_candidate_contract_live_generated_pre_ai",
            evidence={
                "matched_rows": 0,
                "source_component_counts": {
                    f"broader_origin_live_{candidate.get('origin_family')}": 1,
                },
                "broader_origin_candidate_id": candidate.get("candidate_id"),
                "candidate_summary": self._vnext_candidate_safety_gate_summary(candidate),
                "raw_geometry": raw_geometry,
                "source_m15_snapshot": {
                    "source_window_complete": candidate.get("source_window_complete"),
                    "source_path_feature_status": candidate.get(
                        "source_path_feature_status"
                    ),
                    "live_generation_status": candidate.get("live_generation_status"),
                    "source_fields": source_fields,
                },
                "null_zero_reasons": null_zero_reasons,
            },
        )

    def _vnext_candidate_raw_geometry(self, candidate: dict, analysis=None) -> dict:
        trade_parameters = (
            dict(candidate.get("trade_parameters"))
            if isinstance(candidate.get("trade_parameters"), dict)
            else {}
        )
        if analysis is not None and not trade_parameters:
            tp = getattr(analysis, "trade_parameters", None)
            if tp is not None:
                trade_parameters = {
                    "direction": getattr(tp, "direction", None),
                    "entry_price": getattr(tp, "entry_price", None),
                    "stop_loss": getattr(tp, "stop_loss", None),
                    "take_profit_1": getattr(tp, "take_profit_1", None),
                    "risk_reward_ratio": getattr(tp, "risk_reward_ratio", None),
                }
        return {
            "direction": (
                trade_parameters.get("direction")
                or candidate.get("direction")
                or candidate.get("side")
            ),
            "entry_price": self._float_or_none(
                trade_parameters.get("entry_price", candidate.get("entry_price"))
            ),
            "stop_loss": self._float_or_none(
                trade_parameters.get("stop_loss", candidate.get("stop_loss"))
            ),
            "take_profit_1": self._float_or_none(
                trade_parameters.get("take_profit_1", candidate.get("take_profit_1"))
            ),
            "risk_reward_ratio": self._float_or_none(
                trade_parameters.get(
                    "risk_reward_ratio",
                    candidate.get("risk_reward_ratio"),
                )
            ),
        }

    def _vnext_broader_origin_moonshot_context(
        self,
        *,
        candidate: dict,
        kill_zone: str,
        prop_selector,
        analysis=None,
        mso=None,
    ) -> dict:
        fields = candidate.get("source_fields") if isinstance(candidate.get("source_fields"), dict) else {}
        raw_geometry = self._vnext_candidate_raw_geometry(candidate, analysis=analysis)
        raw_trade_parameters = (
            dict(candidate.get("trade_parameters"))
            if isinstance(candidate.get("trade_parameters"), dict)
            else raw_geometry
        )
        broker_snapshot = {
            key: value
            for key, value in self._broker_geometry_snapshot().items()
            if key != "_symbol_info"
        }
        source_mode = (
            "LIVE_CROSS_ASSET_RAW_M15"
            if candidate.get("source_path_feature_status") == "cross_asset_raw_data_asof_complete"
            else "LIVE_RAW_M15"
        )
        spread_r_at_candidate = None
        spread_r_missing_reason = None
        tp = getattr(analysis, "trade_parameters", None) if analysis is not None else None
        try:
            risk_distance = abs(float(tp.entry_price) - float(tp.stop_loss)) if tp is not None else None
        except (TypeError, ValueError):
            risk_distance = None
        tick = None
        if self.mt5 is not None:
            try:
                tick = self.mt5.get_tick(self._mt5_symbol)
            except Exception:  # noqa: BLE001 - quality context should not break routing.
                tick = None
        bid = self._float_or_none(getattr(tick, "bid", None)) if tick is not None else None
        ask = self._float_or_none(getattr(tick, "ask", None)) if tick is not None else None
        if bid is not None and ask is not None and risk_distance and risk_distance > 0:
            spread_r_at_candidate = abs(ask - bid) / risk_distance
        elif tick is None:
            spread_r_missing_reason = "mt5_tick_snapshot_unavailable_for_quality_selector"
        elif not risk_distance or risk_distance <= 0:
            spread_r_missing_reason = "candidate_risk_distance_unavailable_for_quality_selector"
        else:
            spread_r_missing_reason = "tick_bid_ask_unavailable_for_quality_selector"
        kill_zone_position = self._broader_origin_kill_zone_position(
            candidate=candidate,
            kill_zone=kill_zone,
        )
        context = {
            "symbol": self._symbol,
            "broker_symbol": self._mt5_symbol,
            "candidate_id": candidate.get("candidate_id"),
            "side": candidate.get("side") or candidate.get("direction"),
            "framework": candidate.get("framework") or candidate.get("origin_family"),
            "candidate_origin_family": candidate.get("candidate_origin_family"),
            "route_family": candidate.get("origin_family"),
            "route_session": candidate.get("route_session") or kill_zone,
            "kill_zone": kill_zone,
            "kill_zone_position": kill_zone_position,
            "candle_time_utc": candidate.get("candle_close_utc"),
            "utc_hour_bucket": candidate.get("utc_hour_bucket") or fields.get("utc_hour_bucket"),
            "branch_label": "FOLLOW",
            "branch_reason": "broader_origin_live_generated_pre_ai",
            "source_mode": source_mode,
            "source_path_feature_status": candidate.get("source_path_feature_status"),
            "live_generation_status": candidate.get("live_generation_status"),
            "source_complete": candidate.get("source_window_complete"),
            "source_window_complete": candidate.get("source_window_complete"),
            "same_bar_ambiguous": bool(candidate.get("same_bar_ambiguous", False)),
            "selected_policy_same_bar_ambiguous": bool(
                candidate.get("selected_policy_same_bar_ambiguous", candidate.get("same_bar_ambiguous", False))
            ),
            "ordered_path_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
            "selected_policy_ordered_path_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
            "current_bar_displacement_atr14": fields.get("range_atr14"),
            "liquidity_sweep_proxy_state": fields.get("sweep_direction") or "no_prior_20_sweep",
            "volatility_state_14_vs_50": (
                "compression_expansion"
                if candidate.get("origin_family") == "volatility_compression_expansion"
                else "normal_recent_vs_baseline"
            ),
            "trend_state_20": fields.get("trend_state_20") or "unknown_trend_state",
            "prop_governor_action": getattr(prop_selector, "action", None),
            "spread_r_at_candidate": spread_r_at_candidate,
            "spread_r_missing_reason": spread_r_missing_reason,
            "raw_geometry": raw_geometry,
            "trade_parameters": raw_trade_parameters,
            "m15_source_fields": dict(fields),
            "mso_context": self._vnext_mso_timeframe_packet(mso),
            "tick_snapshot": self._vnext_tick_spread_packet(),
            "broker_snapshot": broker_snapshot,
        }
        return {key: value for key, value in context.items() if value not in (None, "")}

    @staticmethod
    def _broader_origin_kill_zone_position(*, candidate: dict, kill_zone: str) -> str:
        expected = str(kill_zone or "").strip().lower()
        candidate_zone = (
            candidate.get("route_session")
            or candidate.get("kill_zone")
            or candidate.get("session")
            or candidate.get("session_bucket")
        )
        candidate_zone_text = str(candidate_zone or "").strip().lower()
        if not expected:
            return "off_configured_kill_zone_or_missing_schedule"
        if candidate_zone_text and candidate_zone_text != expected:
            return "off_configured_kill_zone_or_unconfigured_symbol"
        return f"in_{expected}_runtime_configured_kill_zone"

    def _vnext_dynamic_trade_context(self, vnext_moonshot_dynamic_execution) -> dict:
        source_event = getattr(vnext_moonshot_dynamic_execution, "source_event", None) or {}
        source_event_details = dict(source_event) if isinstance(source_event, dict) else {}
        source_event_hash = hashlib.sha256(
            json.dumps(
                source_event_details,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        selected_policy = vnext_moonshot_dynamic_execution.selected_policy
        applied = bool(vnext_moonshot_dynamic_execution.applied)
        unresolved_reasons = source_event.get("unresolved_reasons")
        if unresolved_reasons is None:
            unresolved_reasons = source_event.get("selected_cell_risk_unresolved_reasons")
        if isinstance(unresolved_reasons, str):
            unresolved_reasons = [unresolved_reasons] if unresolved_reasons.strip() else []
        elif isinstance(unresolved_reasons, (list, tuple, set)):
            unresolved_reasons = [str(item) for item in unresolved_reasons if str(item).strip()]
        else:
            unresolved_reasons = []
        execution_critical_unresolved = source_event.get(
            "selected_cell_risk_execution_critical_unresolved_reasons"
        )
        if isinstance(execution_critical_unresolved, str):
            execution_critical_unresolved = (
                [execution_critical_unresolved]
                if execution_critical_unresolved.strip()
                else []
            )
        elif isinstance(execution_critical_unresolved, (list, tuple, set)):
            execution_critical_unresolved = [
                str(item)
                for item in execution_critical_unresolved
                if str(item).strip()
            ]
        else:
            execution_critical_unresolved = []
        selected_cell_risk_allowed = source_event.get("selected_cell_risk_allowed")
        if selected_cell_risk_allowed is None:
            selected_cell_risk_allowed = source_event.get("risk_allowed")
        commission_model_status = (
            "SELECTED_CELL_RISK_LEDGER_VERIFIED_NO_EXECUTION_CRITICAL_COMMISSION_GAP"
            if selected_cell_risk_allowed is True and not execution_critical_unresolved
            else "SELECTED_CELL_RISK_LEDGER_HAS_UNRESOLVED_COST_OR_GEOMETRY_GAP"
        )
        context = {
            "gtos_vnext_production_execution_path": True,
            "gtos_vnext_dynamic_policy_selected": vnext_moonshot_dynamic_execution.selected_policy,
            "gtos_vnext_execution_policy_id": getattr(
                vnext_moonshot_dynamic_execution,
                "execution_policy_id",
                None,
            ),
            "gtos_vnext_target_stop_geometry_v4": dict(
                getattr(
                    vnext_moonshot_dynamic_execution,
                    "target_stop_geometry_v4",
                    {},
                )
                or {}
            ),
            "gtos_vnext_dynamic_policy_applied": vnext_moonshot_dynamic_execution.applied,
            "gtos_vnext_dynamic_policy_replaced_policy": vnext_moonshot_dynamic_execution.replaced_policy,
            "gtos_vnext_dynamic_policy_candidate_action": vnext_moonshot_dynamic_execution.candidate_action,
            "gtos_vnext_dynamic_policy_decision_status": vnext_moonshot_dynamic_execution.decision_status,
            "gtos_vnext_dynamic_policy_source_quality_action": vnext_moonshot_dynamic_execution.source_quality_action,
            "gtos_vnext_dynamic_policy_exit_management_action": vnext_moonshot_dynamic_execution.exit_management_action,
            "gtos_vnext_dynamic_policy_prop_action": vnext_moonshot_dynamic_execution.prop_action,
            "gtos_vnext_dynamic_policy_fixed_target_role": vnext_moonshot_dynamic_execution.fixed_target_role,
            "gtos_vnext_selected_cell_risk_pct": source_event.get("selected_cell_risk_pct"),
            "gtos_vnext_selected_cell_risk_cell_id": source_event.get("selected_cell_risk_cell_id"),
            "gtos_vnext_selected_cell_risk_decision_basis": source_event.get("selected_cell_risk_decision_basis"),
            "gtos_vnext_selected_cell_risk_unresolved_reasons": unresolved_reasons,
            "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons": (
                execution_critical_unresolved
            ),
            "gtos_vnext_selected_cell_risk_selected_policy": source_event.get(
                "selected_cell_risk_selected_policy"
            ),
            "gtos_vnext_selected_cell_risk_source_policy": source_event.get(
                "selected_cell_risk_source_policy"
            ),
            "gtos_vnext_selected_cell_risk_policy_identity_status": source_event.get(
                "selected_cell_risk_policy_identity_status"
            ),
            "gtos_vnext_commission_model_status": commission_model_status,
            "gtos_vnext_cost_model_source": "selected_cell_risk_ledger_and_current_quote_spread_pre_send",
            "gtos_vnext_source_event_hash": source_event_hash,
            "gtos_vnext_source_event_details": source_event_details,
            "gtos_vnext_activation_family": vnext_moonshot_dynamic_execution.candidate_action,
            "gtos_vnext_origin_family": (
                source_event.get("candidate_origin_family")
                or vnext_moonshot_dynamic_execution.selected_branch
            ),
            "gtos_vnext_selector_row_id": source_event.get("selected_cell_risk_cell_id"),
            "gtos_vnext_selector_proof_hash": source_event_hash,
        }
        if applied:
            cfg = self._gtos_vnext_runtime_cfg()
        if applied and str(selected_policy or "").strip().lower() == "be_after_trigger":
            context["gtos_vnext_dynamic_be_trigger_r"] = cfg.get(
                "moonshot_dynamic_execution_router_be_trigger_r",
                1.0,
            )
            context["gtos_vnext_dynamic_final_target_r"] = cfg.get(
                "moonshot_dynamic_execution_router_be_final_target_r",
                1.5,
            )
            context["gtos_vnext_dynamic_time_stop_bars"] = cfg.get(
                "moonshot_dynamic_execution_router_be_time_stop_bars"
            )
        elif applied and str(selected_policy or "").strip().lower() == "partial_be_runner":
            context["gtos_vnext_dynamic_be_trigger_r"] = cfg.get(
                "moonshot_dynamic_execution_router_partial_trigger_r",
                1.0,
            )
            context["gtos_vnext_dynamic_final_target_r"] = cfg.get(
                "moonshot_dynamic_execution_router_partial_final_target_r",
                3.0,
            )
            context["gtos_vnext_dynamic_partial_close_ratio"] = cfg.get(
                "moonshot_dynamic_execution_router_partial_close_ratio",
                0.5,
            )
            context["gtos_vnext_dynamic_time_stop_bars"] = cfg.get(
                "moonshot_dynamic_execution_router_partial_time_stop_bars"
            )
        elif applied and str(selected_policy or "").strip().lower() == "trailing_runner":
            context["gtos_vnext_dynamic_be_trigger_r"] = cfg.get(
                "moonshot_dynamic_execution_router_trailing_trigger_r",
                1.0,
            )
            context["gtos_vnext_dynamic_final_target_r"] = cfg.get(
                "moonshot_dynamic_execution_router_trailing_final_target_r",
                3.0,
            )
            context["gtos_vnext_dynamic_trail_gap_r"] = cfg.get(
                "moonshot_dynamic_execution_router_trailing_gap_r",
                0.5,
            )
            context["gtos_vnext_dynamic_time_stop_bars"] = cfg.get(
                "moonshot_dynamic_execution_router_trailing_time_stop_bars"
            )
        elif applied and str(selected_policy or "").strip().lower() == "momentum_exhaustion":
            context["gtos_vnext_dynamic_be_trigger_r"] = cfg.get(
                "moonshot_dynamic_execution_router_momentum_trigger_r",
                1.0,
            )
            context["gtos_vnext_dynamic_final_target_r"] = cfg.get(
                "moonshot_dynamic_execution_router_momentum_final_target_r",
                2.0,
            )
            context["gtos_vnext_dynamic_momentum_pullback_r"] = cfg.get(
                "moonshot_dynamic_execution_router_momentum_pullback_r",
                0.4,
            )
            context["gtos_vnext_dynamic_time_stop_bars"] = cfg.get(
                "moonshot_dynamic_execution_router_momentum_time_stop_bars"
            )
        elif applied and str(selected_policy or "").strip().lower() == "time_stop":
            context["gtos_vnext_dynamic_be_trigger_r"] = cfg.get(
                "moonshot_dynamic_execution_router_time_stop_target_r",
                1.5,
            )
            context["gtos_vnext_dynamic_final_target_r"] = cfg.get(
                "moonshot_dynamic_execution_router_time_stop_target_r",
                1.5,
            )
            context["gtos_vnext_dynamic_time_stop_bars"] = cfg.get(
                "moonshot_dynamic_execution_router_time_stop_bars",
                32,
            )
        return context

    @staticmethod
    def _float_or_none(value) -> float | None:
        try:
            if value in (None, ""):
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _market_config_float(market: dict, *keys: str) -> float | None:
        for key in keys:
            value = SessionOrchestrator._float_or_none(market.get(key))
            if value is not None and value > 0:
                return value
        return None

    def _position_symbol_config(self, broker_symbol: str) -> dict:
        try:
            return apply_instrument_overrides(self.config, broker_symbol)
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "vNext open-position symbol config fallback for %s: %s",
                broker_symbol,
                exc,
            )
            return self.config

    def _position_profit_at_price_with_source(
        self,
        position,
        target_price: float,
        *,
        allow_tick_metadata_fallback: bool = True,
    ) -> tuple[float | None, str]:
        broker_symbol = str(getattr(position, "symbol", "") or "")
        volume = self._float_or_none(getattr(position, "volume", None))
        price_open = self._float_or_none(getattr(position, "price_open", None))
        position_type_raw = self._float_or_none(getattr(position, "type", 0))
        if not broker_symbol or volume is None or volume <= 0 or price_open is None:
            return None, "position_geometry_unresolved"
        position_type = int(position_type_raw or 0)
        mt5_module = getattr(self.mt5, "_mt5", None)
        order_calc_profit = getattr(mt5_module, "order_calc_profit", None)
        if callable(order_calc_profit):
            try:
                calculated = order_calc_profit(
                    position_type,
                    broker_symbol,
                    volume,
                    price_open,
                    target_price,
                )
            except Exception as exc:  # noqa: BLE001
                logger.debug(
                    "vNext open-position order_calc_profit failed for %s: %s",
                    broker_symbol,
                    exc,
                )
            else:
                value = self._float_or_none(calculated)
                if value is not None:
                    return value, "broker_order_calc_profit"

        if not allow_tick_metadata_fallback:
            return None, "broker_order_calc_profit_required_unavailable"

        symbol_config = self._position_symbol_config(broker_symbol)
        market = symbol_config.get("market", {}) if isinstance(symbol_config, dict) else {}
        tick_size = self._market_config_float(
            market,
            "trade_tick_size",
            "tick_size",
            "point",
        )
        tick_value = self._market_config_float(
            market,
            "trade_tick_value_loss",
            "trade_tick_value",
            "tick_value",
        )
        if tick_size is None or tick_value is None:
            return None, "symbol_tick_metadata_unresolved"
        price_delta = (
            target_price - price_open
            if position_type == 0
            else price_open - target_price
        )
        return (price_delta / tick_size) * tick_value * volume, "symbol_tick_metadata_fallback"

    def _position_profit_at_price(self, position, target_price: float) -> float | None:
        value, _source = self._position_profit_at_price_with_source(
            position,
            target_price,
        )
        return value

    def _open_position_stop_loss_risk_amount(self, position) -> dict:
        broker_symbol = str(getattr(position, "symbol", "") or "")
        ticket = getattr(position, "ticket", None)
        sl = self._float_or_none(getattr(position, "sl", None))
        if sl is None or sl <= 0:
            return {
                "risk_amount": None,
                "risk_amount_source": "missing_position_stop_loss",
                "risk_amount_missing_reason": "position_stop_loss_missing",
                "ticket": ticket,
                "symbol": broker_symbol,
            }
        current_profit = self._float_or_none(getattr(position, "profit", 0.0)) or 0.0
        profit_at_stop, profit_model = self._position_profit_at_price_with_source(
            position,
            sl,
            allow_tick_metadata_fallback=False,
        )
        if profit_at_stop is None:
            return {
                "risk_amount": None,
                "risk_amount_source": "unverified_stop_loss_profit_model",
                "risk_amount_missing_reason": f"position_profit_at_stop_{profit_model}",
                "ticket": ticket,
                "symbol": broker_symbol,
                "stop_loss": sl,
                "current_profit": current_profit,
                "profit_model": profit_model,
            }
        risk_amount = max(0.0, current_profit - profit_at_stop)
        return {
            "risk_amount": risk_amount,
            "risk_amount_source": "current_position_profit_to_stop_loss_broker_order_calc_profit",
            "risk_amount_missing_reason": None,
            "ticket": ticket,
            "symbol": broker_symbol,
            "stop_loss": sl,
            "current_profit": current_profit,
            "profit_at_stop_loss": profit_at_stop,
            "profit_model": profit_model,
        }

    def _open_position_risk_exposure_summary(
        self,
        open_positions: list[dict],
        risk_base_amount: float | None,
    ) -> dict:
        base = float(risk_base_amount or 0.0)
        open_risk_pct = 0.0
        open_risk_amount = 0.0
        valued_count = 0
        pct_fallback_count = 0
        missing: list[dict] = []
        details: list[dict] = []
        for position in open_positions:
            risk_pct = self._float_or_none(position.get("risk_pct")) or 0.0
            open_risk_pct += risk_pct
            risk_amount = self._float_or_none(position.get("risk_amount"))
            detail = {
                "symbol": position.get("symbol"),
                "ticket": position.get("ticket"),
                "risk_pct": risk_pct,
                "risk_pct_source": position.get("risk_pct_source"),
                "risk_amount": risk_amount,
                "risk_amount_source": position.get("risk_amount_source"),
            }
            if risk_amount is not None:
                open_risk_amount += max(0.0, risk_amount)
                valued_count += 1
                details.append(detail)
                continue
            missing_detail = {
                "symbol": position.get("symbol"),
                "ticket": position.get("ticket"),
                "risk_pct_missing_reason": position.get("risk_pct_missing_reason"),
                "risk_amount_missing_reason": position.get("risk_amount_missing_reason"),
            }
            missing.append(missing_detail)
            details.append({**detail, **missing_detail})
        return {
            "open_position_risk_pct": open_risk_pct,
            "open_position_risk_amount": open_risk_amount,
            "open_position_count": len(open_positions),
            "open_position_risk_valued_count": valued_count,
            "open_position_risk_pct_fallback_count": pct_fallback_count,
            "open_position_risk_missing_count": len(missing),
            "open_position_risk_missing_positions": missing,
            "open_position_risk_details": details,
        }

    @staticmethod
    def _round_price_to_increment(
        value: float,
        increment: float | None,
        *,
        mode: str = "nearest",
        digits: int | None = None,
    ) -> float:
        if not increment or increment <= 0:
            return round(float(value), digits) if digits is not None else float(value)
        scaled = float(value) / float(increment)
        if mode == "floor":
            rounded = math.floor(scaled) * float(increment)
        elif mode == "ceil":
            rounded = math.ceil(scaled) * float(increment)
        else:
            rounded = round(scaled) * float(increment)
        return round(rounded, digits) if digits is not None else rounded

    def _broker_geometry_snapshot(self) -> dict:
        sym_info = None
        try:
            if hasattr(self.execution, "_mt5_symbol_info"):
                sym_info = self.execution._mt5_symbol_info()
        except Exception as exc:  # noqa: BLE001
            logger.debug("vNext broker geometry snapshot unavailable: %s", exc)
        if sym_info is None:
            try:
                mt5_module = getattr(self.mt5, "_mt5", None)
                if mt5_module is not None and hasattr(mt5_module, "symbol_info"):
                    sym_info = mt5_module.symbol_info(self._mt5_symbol)
            except Exception as exc:  # noqa: BLE001
                logger.debug("vNext direct broker geometry snapshot unavailable: %s", exc)
        risk_cfg = self.config.get("risk", {}) or {}
        point = self._float_or_none(getattr(sym_info, "point", None))
        if point is None:
            point = self._float_or_none(risk_cfg.get("tick_size"))
        digits = getattr(sym_info, "digits", None)
        try:
            digits = int(digits) if digits is not None else None
        except (TypeError, ValueError):
            digits = None
        stops_level = self._float_or_none(getattr(sym_info, "trade_stops_level", None)) or 0.0
        freeze_level = self._float_or_none(getattr(sym_info, "trade_freeze_level", None)) or 0.0
        min_distance = max(stops_level, freeze_level) * point if point else 0.0
        return {
            "symbol": self._symbol,
            "broker_symbol": self._mt5_symbol,
            "symbol_info_available": sym_info is not None,
            "point": point,
            "digits": digits,
            "trade_stops_level": stops_level,
            "trade_freeze_level": freeze_level,
            "broker_min_stop_distance": min_distance,
            "volume_min": self._float_or_none(getattr(sym_info, "volume_min", None)),
            "volume_max": self._float_or_none(getattr(sym_info, "volume_max", None)),
            "volume_step": self._float_or_none(getattr(sym_info, "volume_step", None)),
            "trade_contract_size": self._float_or_none(
                getattr(sym_info, "trade_contract_size", None)
            ),
            "_symbol_info": sym_info,
        }

    def _repair_vnext_broader_origin_executable_geometry(
        self,
        *,
        candidate: dict,
        analysis,
        mso,
        entry_price: float,
        dynamic_trade_context: dict,
        vnext_ltf_path_execution,
        vnext_moonshot_dynamic_execution,
        risk_pct: float,
        account_balance: float,
    ) -> dict:
        """Repair raw broader-origin geometry into broker-placement geometry."""
        tp = getattr(analysis, "trade_parameters", None)
        if tp is None:
            return {
                "schema_version": "gtos_vnext_executable_geometry_repair_v1",
                "status": "failed_no_trade_parameters",
                "applied": False,
                "actions": [],
            }

        risk_cfg = self.config.get("risk", {}) or {}
        source_fields = (
            candidate.get("source_fields")
            if isinstance(candidate.get("source_fields"), dict)
            else {}
        )
        m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
        mso_atr = self._float_or_none(getattr(m15_tf, "atr_14", None)) if m15_tf else None
        source_atr = self._float_or_none(source_fields.get("atr14"))
        broker = self._broker_geometry_snapshot()
        increment = broker.get("point")
        digits = broker.get("digits")
        original = {
            "direction": getattr(tp, "direction", None),
            "entry_price": self._float_or_none(getattr(tp, "entry_price", None)),
            "stop_loss": self._float_or_none(getattr(tp, "stop_loss", None)),
            "take_profit_1": self._float_or_none(getattr(tp, "take_profit_1", None)),
            "risk_reward_ratio": self._float_or_none(
                getattr(tp, "risk_reward_ratio", None)
            ),
        }
        direction = str(original["direction"] or "").upper()
        actions: list[str] = []

        repaired_entry = self._float_or_none(entry_price)
        if repaired_entry is None:
            repaired_entry = original["entry_price"]
        if repaired_entry is not None and increment:
            repaired_entry = self._round_price_to_increment(
                repaired_entry,
                increment,
                mode="nearest",
                digits=digits,
            )
        if repaired_entry is not None and repaired_entry != original["entry_price"]:
            actions.append("m1_or_broker_increment_entry_adjustment")
            tp.entry_price = repaired_entry

        selected_policy = str(
            getattr(vnext_moonshot_dynamic_execution, "selected_policy", "") or ""
        ).strip().lower()
        final_target_r = self._float_or_none(
            dynamic_trade_context.get("gtos_vnext_dynamic_final_target_r")
        )
        if final_target_r is None or final_target_r <= 0:
            final_target_r = max(
                self._float_or_none(getattr(tp, "risk_reward_ratio", None)) or 0.0,
                self._float_or_none(risk_cfg.get("min_rr")) or 1.5,
            )
        trigger_r = self._float_or_none(
            dynamic_trade_context.get("gtos_vnext_dynamic_be_trigger_r")
        )

        sl_floor = self._float_or_none(risk_cfg.get("sl_absolute_min")) or 0.0
        atr_for_gate = mso_atr if mso_atr is not None and mso_atr > 0 else source_atr
        atr_floor = 1.5 * atr_for_gate if atr_for_gate and atr_for_gate > 0 else 0.0
        broker_floor = self._float_or_none(broker.get("broker_min_stop_distance")) or 0.0
        required_sl_distance = max(sl_floor, atr_floor, broker_floor)

        entry = self._float_or_none(getattr(tp, "entry_price", None))
        stop = self._float_or_none(getattr(tp, "stop_loss", None))
        current_sl_distance = abs(entry - stop) if entry is not None and stop is not None else 0.0
        if (
            direction in {"LONG", "SHORT"}
            and entry is not None
            and required_sl_distance > 0
            and current_sl_distance < required_sl_distance
        ):
            stop_mode = "floor" if direction == "LONG" else "ceil"
            raw_stop = (
                entry - required_sl_distance
                if direction == "LONG"
                else entry + required_sl_distance
            )
            repaired_stop = self._round_price_to_increment(
                raw_stop,
                increment,
                mode=stop_mode,
                digits=digits,
            )
            repaired_distance = abs(entry - repaired_stop)
            if repaired_distance < required_sl_distance and increment:
                repaired_stop = (
                    repaired_stop - increment
                    if direction == "LONG"
                    else repaired_stop + increment
                )
                repaired_stop = round(repaired_stop, digits) if digits is not None else repaired_stop
            tp.stop_loss = repaired_stop
            actions.append("structural_atr_broker_stop_expansion")

        entry = self._float_or_none(getattr(tp, "entry_price", None))
        stop = self._float_or_none(getattr(tp, "stop_loss", None))
        sl_distance = abs(entry - stop) if entry is not None and stop is not None else 0.0
        if direction in {"LONG", "SHORT"} and entry is not None and sl_distance > 0:
            raw_target = (
                entry + final_target_r * sl_distance
                if direction == "LONG"
                else entry - final_target_r * sl_distance
            )
            target_mode = "ceil" if direction == "LONG" else "floor"
            repaired_target = self._round_price_to_increment(
                raw_target,
                increment,
                mode=target_mode,
                digits=digits,
            )
            tp.take_profit_1 = repaired_target
            tp.risk_reward_ratio = final_target_r
            dynamic_trade_context["gtos_vnext_dynamic_final_target_price"] = repaired_target
            if trigger_r and trigger_r > 0:
                raw_trigger = (
                    entry + trigger_r * sl_distance
                    if direction == "LONG"
                    else entry - trigger_r * sl_distance
                )
                trigger_mode = "ceil" if direction == "LONG" else "floor"
                dynamic_trade_context["gtos_vnext_dynamic_be_trigger_price"] = (
                    self._round_price_to_increment(
                        raw_trigger,
                        increment,
                        mode=trigger_mode,
                        digits=digits,
                    )
                )
            actions.append("dynamic_target_recomputed_from_repaired_risk")

        if dynamic_trade_context.get("gtos_vnext_target_stop_geometry_v4") is not None:
            dynamic_trade_context["gtos_vnext_target_stop_geometry_v4"] = (
                build_target_stop_geometry_v4_contract(
                    config=self.config,
                    selected_policy=selected_policy,
                    execution_policy_id=dynamic_trade_context.get(
                        "gtos_vnext_execution_policy_id"
                    ),
                    source_event=getattr(
                        vnext_moonshot_dynamic_execution,
                        "source_event",
                        {},
                    )
                    or {},
                    trade_params=dynamic_trade_context,
                    prior_contract=dynamic_trade_context.get(
                        "gtos_vnext_target_stop_geometry_v4"
                    ),
                    entry_price=getattr(tp, "entry_price", None),
                    stop_loss=getattr(tp, "stop_loss", None),
                    direction=getattr(tp, "direction", None),
                    risk_distance=sl_distance,
                    trigger_r=trigger_r,
                    final_target_r=final_target_r,
                    trigger_price=dynamic_trade_context.get(
                        "gtos_vnext_dynamic_be_trigger_price"
                    ),
                    final_target_price=dynamic_trade_context.get(
                        "gtos_vnext_dynamic_final_target_price"
                    ),
                    stage="orchestrator_repaired_geometry",
                )
            )

        for key, value in dynamic_trade_context.items():
            setattr(tp, key, value)

        lot_recompute: dict = {
            "status": "not_available",
            "risk_pct": risk_pct,
            "account_balance": account_balance,
        }
        sym_info = broker.get("_symbol_info")
        if (
            hasattr(self.execution, "_calculate_lots")
            and hasattr(self.execution, "_normalize_volume")
            and sl_distance > 0
        ):
            try:
                risk_amount = float(account_balance or 0.0) * float(risk_pct or 0.0) / 100.0
                raw_lots = self.execution._calculate_lots(
                    sl_distance,
                    risk_amount,
                    sym_info=sym_info,
                    require_broker_geometry=True,
                    direction=direction,
                    entry_price=entry,
                    stop_loss=stop,
                )
                normalized_lots = (
                    self.execution._normalize_volume(
                        raw_lots,
                        sym_info,
                        require_broker_geometry=True,
                    )
                    if raw_lots is not None
                    else None
                )
                lot_recompute = {
                    "status": "computed" if normalized_lots is not None else "failed",
                    "risk_pct": risk_pct,
                    "risk_amount": risk_amount,
                    "raw_lots": raw_lots,
                    "normalized_lots": normalized_lots,
                    "lot_sizing_diagnostic": getattr(
                        self.execution,
                        "_last_lot_sizing_diagnostic",
                        None,
                    ),
                }
                actions.append("risk_lot_recomputed_for_repaired_geometry")
            except Exception as exc:  # noqa: BLE001
                lot_recompute = {
                    "status": "failed_exception",
                    "risk_pct": risk_pct,
                    "error": str(exc),
                }

        repaired = {
            "direction": getattr(tp, "direction", None),
            "entry_price": self._float_or_none(getattr(tp, "entry_price", None)),
            "stop_loss": self._float_or_none(getattr(tp, "stop_loss", None)),
            "take_profit_1": self._float_or_none(getattr(tp, "take_profit_1", None)),
            "risk_reward_ratio": self._float_or_none(getattr(tp, "risk_reward_ratio", None)),
            "sl_distance": sl_distance,
        }
        selected_cell = {
            "risk_pct": dynamic_trade_context.get("gtos_vnext_selected_cell_risk_pct"),
            "cell_id": dynamic_trade_context.get("gtos_vnext_selected_cell_risk_cell_id"),
            "selected_policy": dynamic_trade_context.get(
                "gtos_vnext_selected_cell_risk_selected_policy"
            ),
            "source_policy": dynamic_trade_context.get(
                "gtos_vnext_selected_cell_risk_source_policy"
            ),
            "policy_identity_status": dynamic_trade_context.get(
                "gtos_vnext_selected_cell_risk_policy_identity_status"
            ),
            "unresolved_reasons": dynamic_trade_context.get(
                "gtos_vnext_selected_cell_risk_unresolved_reasons"
            ),
        }
        broker_public = {key: value for key, value in broker.items() if key != "_symbol_info"}
        status = "repaired" if original != repaired or actions else "checked_no_change_required"
        return {
            "schema_version": "gtos_vnext_executable_geometry_repair_v1",
            "status": status,
            "applied": bool(actions),
            "actions": actions,
            "original": original,
            "repaired": repaired,
            "thresholds": {
                "sl_absolute_min": sl_floor,
                "m15_atr_source": "mso" if mso_atr is not None else "candidate_source_fields",
                "m15_atr": atr_for_gate,
                "atr_1_5_floor": atr_floor,
                "broker_min_stop_distance": broker_floor,
                "required_sl_distance": required_sl_distance,
            },
            "m1_ltf_entry_adjustment": {
                "action": getattr(vnext_ltf_path_execution, "action", None),
                "applied": getattr(vnext_ltf_path_execution, "applied", None),
                "adjusted_entry_price": getattr(
                    vnext_ltf_path_execution,
                    "adjusted_entry_price",
                    None,
                ),
                "monitor_timeframe": getattr(vnext_ltf_path_execution, "monitor_timeframe", None),
            },
            "dynamic_target": {
                "selected_policy": selected_policy,
                "final_target_r": final_target_r,
                "trigger_r": trigger_r,
                "final_target_price": dynamic_trade_context.get(
                    "gtos_vnext_dynamic_final_target_price"
                ),
                "trigger_price": dynamic_trade_context.get(
                    "gtos_vnext_dynamic_be_trigger_price"
                ),
            },
            "selected_cell_risk_check": selected_cell,
            "broker_spec_check": broker_public,
            "lot_recompute": lot_recompute,
            "terminal_gate1_policy": (
                "run_after_repair; legacy raw sl_floor/sl_atr/tp1_2r rejection "
                "does_not_have_pre_repair_authority_on_vnext_broader_origin"
            ),
        }

    def _finalize_vnext_broader_origin_failed_record(
        self,
        *,
        record: dict | None,
        tc_cfg: dict,
        final_outcome: str,
        kill_zone: str,
        reason: str,
    ) -> str:
        if record is not None:
            record["decision_pipeline"]["final_outcome"] = final_outcome
            self._refresh_vnext_candidate_intelligence_packet(
                record,
                final_order_decision={
                    "final_outcome": final_outcome,
                    "reached_order_path": False,
                    "order_path": "order_path_failed",
                    "reason": reason,
                },
            )
            save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
        self._log_candle(final_outcome, reason, kill_zone, produced_candidate=True)
        return final_outcome

    @staticmethod
    def _trade_state_execution_identity(trade_state) -> dict:
        ticket = getattr(trade_state, "ticket", None)
        entry_order_ticket = getattr(trade_state, "entry_order_ticket", None)
        entry_deal_ticket = getattr(trade_state, "entry_deal_ticket", None)
        if entry_deal_ticket in (None, "", 0, "0"):
            entry_deal_ticket = None
        entry_order_retcode = getattr(trade_state, "entry_order_retcode", None)
        join_keys = []
        for key_name, key_value in (
            ("trade_state_ticket", ticket),
            ("mt5_position_ticket", ticket),
            ("mt5_entry_order_ticket", entry_order_ticket),
            ("mt5_entry_deal_ticket", entry_deal_ticket),
        ):
            if key_value not in (None, "", 0, "0"):
                join_keys.append(f"{key_name}:{key_value}")
        join_keys = list(dict.fromkeys(join_keys))
        return {
            "position_ticket": ticket,
            "entry_order_ticket": entry_order_ticket,
            "entry_deal_ticket": entry_deal_ticket,
            "entry_deal_ticket_status": (
                "mt5_result_deal_ticket_present"
                if entry_deal_ticket is not None
                else "mt5_result_deal_ticket_absent_using_order_position_join_keys"
            ),
            "order_result_retcode": entry_order_retcode,
            "entry_order_retcode": entry_order_retcode,
            "filled_order_position_join_keys": join_keys,
            "exact_r_join_key_status": (
                "FILLED_ORDER_POSITION_KEYS_CAPTURED"
                if join_keys
                else "NO_FILLED_ORDER_POSITION_KEYS_FOR_CURRENT_STATE"
            ),
        }

    def _save_vnext_broader_origin_market_record(
        self,
        *,
        record: dict | None,
        tc_cfg: dict,
        trade_state,
        effective_risk_pct: float,
        vnext_pending_policy,
        vnext_ltf_path_execution,
        vnext_prop_safe_selector,
        vnext_moonshot_dynamic_execution,
    ) -> None:
        if record is None:
            return
        record["decision_pipeline"]["final_outcome"] = "EXECUTED_GTOS_VNEXT_BROADER_ORIGIN_MARKET"
        update_execution(
            record,
            {
                "execution_mode": "GTOS_VNEXT_BROADER_ORIGIN_MARKET_ENTRY",
                "trade_id": trade_state.trade_id,
                "ticket": trade_state.ticket,
                "direction": trade_state.direction,
                "entry_price": trade_state.entry_price,
                "stop_loss": trade_state.stop_loss,
                "take_profit_1": trade_state.take_profit_1,
                "risk_pct": effective_risk_pct,
                **self._trade_state_execution_identity(trade_state),
                "gtos_vnext_pending_policy": vnext_pending_policy.to_record(),
                "gtos_vnext_ltf_path_execution": vnext_ltf_path_execution.to_record(),
                "gtos_vnext_prop_safe_selector": vnext_prop_safe_selector.to_record(),
                "gtos_vnext_moonshot_dynamic_execution": vnext_moonshot_dynamic_execution.to_record(),
            },
        )
        self._refresh_vnext_candidate_intelligence_packet(
            record,
            final_order_decision={
                "final_outcome": "EXECUTED_GTOS_VNEXT_BROADER_ORIGIN_MARKET",
                "reached_order_path": True,
                "order_path": "market_order",
                "trade_id": trade_state.trade_id,
                "ticket": trade_state.ticket,
            },
        )
        base_path = tc_cfg.get("base_path", "knowledge_base/trade_records")
        self._active_trade_record_path = save_trade_record(record, base_path)
        self._active_trade_record = record

    def _save_vnext_broader_origin_pending_record(
        self,
        *,
        record: dict | None,
        tc_cfg: dict,
        pending,
        vnext_pending_policy,
        vnext_ltf_path_execution,
        vnext_prop_safe_selector,
        vnext_moonshot_dynamic_execution,
    ) -> None:
        if record is None:
            return
        record["decision_pipeline"]["final_outcome"] = "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN"
        record["limit_intent"] = {
            "trade_id": pending.trade_id,
            "limit_price": pending.limit_price,
            "stop_loss": pending.stop_loss,
            "take_profit_1": pending.take_profit_1,
            "expiry_candles": pending.expiry_candles,
            "pending_order_mode": pending.pending_order_mode,
            "broker_pending_order_created": pending.broker_pending_order_created,
            "mt5_order_ticket": pending.mt5_order_ticket,
            "native_pending_order_type": pending.native_pending_order_type,
            "gtos_vnext_pending_policy": vnext_pending_policy.to_record(),
            "gtos_vnext_ltf_path_execution": vnext_ltf_path_execution.to_record(),
            "gtos_vnext_prop_safe_selector": vnext_prop_safe_selector.to_record(),
            "gtos_vnext_moonshot_dynamic_execution": vnext_moonshot_dynamic_execution.to_record(),
        }
        self._refresh_vnext_candidate_intelligence_packet(
            record,
            final_order_decision={
                "final_outcome": "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN",
                "reached_order_path": True,
                "order_path": "pending_limit",
                "trade_id": pending.trade_id,
                "broker_pending_order_created": pending.broker_pending_order_created,
                "mt5_order_ticket": pending.mt5_order_ticket,
                "native_pending_order_type": pending.native_pending_order_type,
            },
        )
        base_path = tc_cfg.get("base_path", "knowledge_base/trade_records")
        self._pending_trade_record_path = save_trade_record(record, base_path)
        if self._pending_trade_record_path:
            index_pending_record(
                trade_id=pending.trade_id,
                record_path=self._pending_trade_record_path,
                symbol=self._symbol,
                base_path=base_path,
            )

    def _evaluate_ai_supervisor(self, *, raw_data: dict, kill_zone: str):
        """Run the bounded AI supervisor and store its effective config."""
        decision = evaluate_ai_supervisor(config=self.config)
        record_ai_supervisor_decision(
            decision=decision,
            config=self.config,
            phase="orchestrator_pre_ai",
            symbol=self._symbol,
            kill_zone=kill_zone,
        )
        self._ai_supervisor_effective_config = apply_ai_supervisor_runtime_overrides(
            self.config,
            decision,
        )
        if isinstance(raw_data, dict):
            raw_data["ai_supervisor_decision"] = decision.to_record()
        logger.info(
            "AI_SUPERVISOR action=%s severity=%s disable_ai_narrowing=%s reason=%s",
            decision.action,
            decision.severity,
            decision.disable_ai_narrowing,
            decision.reason,
        )
        return decision

    def _config_after_ai_supervisor(self) -> dict:
        return getattr(self, "_ai_supervisor_effective_config", None) or self.config

    def _evaluate_gtos_vnext_pre_ai(self, *, raw_data: dict, kill_zone: str,
                                    bias_result: dict):
        """Run vNext mechanical routing before spending an AI call."""
        self._evaluate_ai_supervisor(raw_data=raw_data, kill_zone=kill_zone)
        effective_config = self._config_after_ai_supervisor()
        decision = evaluate_pre_ai_vnext(
            symbol=self._symbol,
            source_symbol=self._mt5_symbol,
            kill_zone=kill_zone,
            config=effective_config,
            bias=bias_result.get("bias"),
            raw_data=raw_data,
        )
        candle_time = self._vnext_effective_candle_time(raw_data)
        record_vnext_runtime_decision(
            decision=decision,
            config=self.config,
            phase="pre_ai",
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=str(candle_time) if candle_time else None,
        )
        logger.info(
            "GTOS_VNEXT_PRE_AI action=%s decision=%s would_action=%s "
            "recommended_side=%s recommended_frameworks=%s recommended_route_families=%s "
            "blocked_sides=%s blocked_frameworks=%s blocked_route_families=%s apply_to_ai_call=%s "
            "reason=%s event=%s",
            decision.action,
            decision.decision,
            getattr(decision, "would_action", "ALLOW_AI"),
            getattr(decision, "recommended_side", None),
            list(getattr(decision, "recommended_frameworks", ())),
            list(getattr(decision, "recommended_route_families", ())),
            list(getattr(decision, "blocked_sides", ())),
            list(getattr(decision, "blocked_frameworks", ())),
            list(getattr(decision, "blocked_route_families", ())),
            decision.apply_to_ai_call,
            decision.reason,
            decision.event,
        )
        return decision

    def _evaluate_gtos_vnext_ai_policy(
        self,
        *,
        raw_data: dict,
        kill_zone: str,
        bias_result: dict,
        vnext_pre_ai,
    ):
        """Run Stage07 mechanical-first AI policy before PrimaryAnalyzer."""
        risk_tier = None
        if isinstance(raw_data, dict):
            risk_tier = raw_data.get("risk_tier") or raw_data.get("prop_risk_tier")
        decision = evaluate_vnext_ai_policy(
            pre_ai_decision=vnext_pre_ai,
            config=self._config_after_ai_supervisor(),
            raw_data=raw_data,
            risk_tier=risk_tier,
        )
        candle_time = self._vnext_effective_candle_time(raw_data)
        record_vnext_runtime_decision(
            decision=decision,
            config=self.config,
            phase="ai_policy_pre_call",
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=str(candle_time) if candle_time else None,
        )
        logger.info(
            "GTOS_VNEXT_AI_POLICY action=%s would_action=%s allowed=%s "
            "would_allow_ai_call=%s apply_to_ai_call=%s role=%s reason=%s bias=%s",
            decision.action,
            decision.would_action,
            decision.allowed,
            decision.would_allow_ai_call,
            decision.apply_to_ai_call,
            decision.ai_role,
            decision.reason,
            bias_result.get("bias") if isinstance(bias_result, dict) else None,
        )
        if isinstance(raw_data, dict):
            raw_data["gtos_vnext_ai_policy"] = decision.to_record()
        return decision

    def _evaluate_structural_c_gate_pre_ai(
        self,
        *,
        mso,
        raw_data: dict,
        kill_zone: str,
        bias_result: dict,
    ) -> StructuralCGateDecision:
        """Run the Session-13 structural C-gate before the AI call."""
        decision = evaluate_structural_c_gate(
            mso=mso,
            bias_result=bias_result,
            config=self.config,
        )
        if isinstance(raw_data, dict):
            raw_data["structural_c_gate_decision"] = decision.to_record()
        logger.info(
            "STRUCTURAL_C_GATE action=%s would_action=%s apply_to_ai_call=%s "
            "bias=%s side=%s h1=%s m15=%s reason=%s",
            decision.action,
            decision.would_action,
            decision.apply_to_ai_call,
            decision.bias,
            decision.side,
            decision.h1_direction,
            decision.m15_direction,
            decision.reason,
        )
        return decision

    @staticmethod
    def _apply_structural_c_gate_pre_ai_route(
        *,
        bias_result: dict,
        structural_c_gate: StructuralCGateDecision,
    ) -> dict:
        """Apply active structural C-gate side routing to deterministic bias.

        UNIT_000063: when D1 is stale and H4+H1 agree against it, the
        structural gate is allowed to replace the D1-bound pre-AI bias rather
        than only filling no-bias gaps. This converts the NAS100 W14 D1-lag
        failure mode into a runtime AI narrowing rule.
        """
        if (
            structural_c_gate.action != "NARROW_AI_TO_SIDE"
            or structural_c_gate.bias not in ("bullish", "bearish")
        ):
            return bias_result

        reason = structural_c_gate.reason
        should_apply = (
            bias_result.get("bias") == "no_bias"
            or reason == "structural_c_gate_d1_lag_h4_h1_consensus"
        )
        if not should_apply:
            return bias_result

        return {
            **bias_result,
            "bias": structural_c_gate.bias,
            "source": reason,
            "structural_c_gate_original_bias": bias_result.get("bias"),
            "structural_c_gate_original_source": bias_result.get("source"),
            "structural_c_gate": structural_c_gate.to_record(),
        }

    def _ai_call_policy_context(
        self,
        *,
        raw_data: dict,
        kill_zone: str,
        bias_result: dict,
        vnext_pre_ai,
        vnext_ai_policy=None,
    ) -> dict:
        """Build the compact context consumed by the AI cost-control policy."""
        raw_context = {}
        if isinstance(raw_data, dict) and isinstance(raw_data.get("ai_call_context"), dict):
            raw_context = dict(raw_data.get("ai_call_context") or {})
        context = {
            "purpose": "production_trade_decision",
            "runtime_context": "live_orchestrator",
            "symbol": self._symbol,
            "source_symbol": getattr(self, "_mt5_symbol", None),
            "kill_zone": kill_zone,
            "deterministic_bias": bias_result.get("bias"),
            "vnext_pre_ai_action": getattr(vnext_pre_ai, "action", None),
            "vnext_pre_ai_would_action": getattr(vnext_pre_ai, "would_action", None),
            "vnext_pre_ai_reason": getattr(vnext_pre_ai, "reason", None),
        }
        if vnext_ai_policy is not None:
            context["vnext_ai_policy_action"] = getattr(vnext_ai_policy, "action", None)
            context["vnext_ai_policy_would_action"] = getattr(
                vnext_ai_policy, "would_action", None
            )
            context["vnext_ai_policy_allowed"] = getattr(vnext_ai_policy, "allowed", None)
            context["vnext_ai_policy_would_allow_ai_call"] = getattr(
                vnext_ai_policy,
                "would_allow_ai_call",
                None,
            )
            context["vnext_ai_policy_role"] = getattr(vnext_ai_policy, "ai_role", None)
            context["vnext_ai_policy_reason"] = getattr(vnext_ai_policy, "reason", None)
            prompt_scope = getattr(vnext_ai_policy, "prompt_scope", {}) or {}
            if isinstance(prompt_scope, dict):
                context["vnext_ai_policy_source_bound"] = prompt_scope.get("source_bound")
                context["vnext_ai_policy_recommended_side"] = prompt_scope.get(
                    "recommended_side"
                )
                context["vnext_ai_policy_recommended_frameworks"] = prompt_scope.get(
                    "recommended_frameworks"
                )
        role_context = getattr(vnext_pre_ai, "ai_role_context", {}) or {}
        if isinstance(role_context, dict) and role_context:
            context["vnext_ai_role"] = role_context.get("ai_role")
            context["vnext_ai_role_source_artifact_path"] = role_context.get(
                "source_artifact_path"
            )
            context["vnext_ai_role_matched_rows"] = role_context.get("matched_rows")
            context["vnext_ai_role_selection_action"] = role_context.get("selection_action")
            context["vnext_ai_role_recommended_side"] = role_context.get("recommended_side")
            context["vnext_ai_role_recommended_frameworks"] = role_context.get(
                "recommended_frameworks"
            )
            context["vnext_ai_role_recommended_route_families"] = role_context.get(
                "recommended_route_families"
            )
        if isinstance(raw_data, dict):
            if raw_data.get("candle_close_utc"):
                context["candle_time_utc"] = raw_data.get("candle_close_utc")
            for key in (
                "run_mode",
                "evaluation_mode",
                "source_universe_kind",
                "claim_type",
                "historical_replay",
            ):
                if key in raw_data:
                    context[key] = raw_data.get(key)
        context.update(raw_context)
        return {key: value for key, value in context.items() if value not in (None, "")}

    def _evaluate_ai_call_policy(self, *, raw_data: dict, kill_zone: str,
                                 bias_result: dict, vnext_pre_ai, vnext_ai_policy=None):
        """Run the AI cost-control policy in the orchestrator pre-call path."""
        context = self._ai_call_policy_context(
            raw_data=raw_data,
            kill_zone=kill_zone,
            bias_result=bias_result,
            vnext_pre_ai=vnext_pre_ai,
            vnext_ai_policy=vnext_ai_policy,
        )
        decision = evaluate_ai_call_policy(
            config=self.config,
            context=context,
            symbol=self._symbol,
            kill_zone=kill_zone,
            candle_time_utc=context.get("candle_time_utc"),
            model=(self.config.get("ai", {}) or {}).get("primary_model"),
        )
        record_ai_call_policy_decision(
            decision=decision,
            config=self.config,
            phase="orchestrator_pre_primary_analyzer",
        )
        logger.info(
            "AI_CALL_POLICY action=%s allowed=%s apply_to_ai_call=%s reason=%s context=%s",
            decision.action,
            decision.allowed,
            decision.apply_to_ai_call,
            decision.reason,
            decision.context,
        )
        return decision

    def _format_gtos_vnext_ai_role_context(self, *, vnext_pre_ai, vnext_ai_policy=None) -> str:
        """Render vNext's specialized AI role context for PrimaryAnalyzer."""
        cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
        if not bool(cfg.get("pre_ai_ai_role_context_apply_to_prompt", True)):
            return ""
        role_text = format_vnext_ai_role_context_for_prompt(
            getattr(vnext_pre_ai, "ai_role_context", {}) or {}
        )
        policy_text = format_vnext_ai_policy_context_for_prompt(vnext_ai_policy)
        return "\n\n".join(part for part in (role_text, policy_text) if part)

    @staticmethod
    def _bias_from_vnext_side(side: str | None) -> str | None:
        if side == "LONG":
            return "bullish"
        if side == "SHORT":
            return "bearish"
        return None

    def _apply_gtos_vnext_pre_ai_route(self, *, bias_result: dict,
                                       vnext_pre_ai) -> dict:
        """Apply an active vNext pre-AI side route to the AI bias context."""
        action = getattr(vnext_pre_ai, "action", None)
        routed_bias = self._bias_from_vnext_side(
            getattr(vnext_pre_ai, "recommended_side", None)
        )
        if not routed_bias and action != "NARROW_AI_EXCLUDE_FRAMEWORKS":
            return bias_result
        routed = dict(bias_result)
        routed["gtos_vnext_original_bias"] = bias_result.get("bias")
        routed["gtos_vnext_original_source"] = bias_result.get("source")
        routed["gtos_vnext_route_reason"] = getattr(vnext_pre_ai, "reason", "")
        routed["gtos_vnext_route_decision"] = vnext_pre_ai.to_record()
        routed["gtos_vnext_recommended_frameworks"] = list(
            getattr(vnext_pre_ai, "recommended_frameworks", ())
        )
        routed["gtos_vnext_recommended_route_families"] = list(
            getattr(vnext_pre_ai, "recommended_route_families", ())
        )
        routed["gtos_vnext_blocked_frameworks"] = list(
            getattr(vnext_pre_ai, "blocked_frameworks", ())
        )
        routed["gtos_vnext_blocked_route_families"] = list(
            getattr(vnext_pre_ai, "blocked_route_families", ())
        )
        if routed_bias:
            routed["bias"] = routed_bias
        framework_route = "+".join(routed["gtos_vnext_recommended_frameworks"])
        route_family = "+".join(routed["gtos_vnext_recommended_route_families"])
        route_text = framework_route or route_family or "any_route"
        route_side = getattr(vnext_pre_ai, "recommended_side", None) or "frameworks"
        routed["source"] = (
            f"gtos_vnext_pre_ai:{route_side}:"
            f"{route_text}:"
            f"{bias_result.get('source', 'unknown')}"
        )
        logger.info(
            "GTOS_VNEXT_PRE_AI_ROUTE original_bias=%s routed_bias=%s "
            "recommended_side=%s recommended_frameworks=%s recommended_route_families=%s reason=%s",
            bias_result.get("bias"),
            routed_bias,
            getattr(vnext_pre_ai, "recommended_side", None),
            routed["gtos_vnext_recommended_frameworks"],
            routed["gtos_vnext_recommended_route_families"],
            getattr(vnext_pre_ai, "reason", ""),
        )
        return routed

    def _config_for_gtos_vnext_pre_ai_gate(self, *, vnext_pre_ai) -> dict:
        """Return config for pre-AI gates after active vNext framework routing."""
        frameworks = list(getattr(vnext_pre_ai, "recommended_frameworks", ()) or ())
        if (
            getattr(vnext_pre_ai, "action", None)
            not in {"NARROW_AI_TO_ROUTE", "NARROW_AI_EXCLUDE_FRAMEWORKS"}
            or not frameworks
        ):
            return self.config
        routed_config = dict(self.config)
        model_a = dict(routed_config.get("model_a", {}) or {})
        model_a["enabled_frameworks"] = frameworks
        routed_config["model_a"] = model_a
        return routed_config

    @staticmethod
    def _latest_raw_m15_close(raw_data: dict) -> float | None:
        try:
            candles = raw_data.get("candles", {}).get("M15", [])
            if not candles:
                return None
            return float(candles[-1]["close"])
        except (AttributeError, KeyError, TypeError, ValueError):
            return None

    def _evaluate_poi_proximity_pre_ai_gate(
        self,
        *,
        mso,
        raw_data: dict,
        bias_result: dict,
        poi_gate_config: dict,
    ) -> dict:
        """Run the framework-aware POI proximity gate before the AI call."""
        gate_cfg = poi_gate_config.get("pre_ai_gates", {}) if isinstance(poi_gate_config, dict) else {}
        enabled = bool(gate_cfg.get("poi_proximity_enabled", False))
        apply_to_ai_call = bool(gate_cfg.get("poi_proximity_apply_to_ai_call", False))
        current_price = self._latest_raw_m15_close(raw_data)
        record = {
            "enabled": enabled,
            "apply_to_ai_call": apply_to_ai_call,
            "skipped": False,
            "reason": "",
            "current_price": current_price,
            "bias": bias_result.get("bias"),
            "source_path": gate_cfg.get("poi_proximity_source_path"),
            "tolerance_pct": gate_cfg.get("poi_proximity_tolerance_pct", 0.01),
        }
        if not enabled or current_price is None:
            if enabled and current_price is None:
                record["reason"] = "missing_m15_close"
            if isinstance(raw_data, dict):
                raw_data["pre_ai_poi_proximity_gate"] = record
            return record

        should_skip, reason = poi_proximity_availability(
            mso,
            poi_gate_config,
            current_price=current_price,
            bias=bias_result.get("bias", ""),
        )
        record["skipped"] = bool(should_skip and apply_to_ai_call)
        record["would_skip"] = bool(should_skip)
        record["reason"] = reason
        if isinstance(raw_data, dict):
            raw_data["pre_ai_poi_proximity_gate"] = record
        logger.info(
            "POI_PROXIMITY_PRE_AI enabled=%s apply_to_ai_call=%s skipped=%s "
            "price=%s reason=%s",
            enabled,
            apply_to_ai_call,
            record["skipped"],
            current_price,
            reason,
        )
        return record

    @staticmethod
    def _frameworks_override_for_gtos_vnext_ai(*, vnext_pre_ai) -> list[str] | None:
        frameworks = list(getattr(vnext_pre_ai, "recommended_frameworks", ()) or ())
        if (
            getattr(vnext_pre_ai, "action", None)
            in {"NARROW_AI_TO_ROUTE", "NARROW_AI_EXCLUDE_FRAMEWORKS"}
            and frameworks
        ):
            return frameworks
        return None

    @staticmethod
    def _gtos_vnext_ai_route_mismatch(*, analysis, vnext_pre_ai) -> str | None:
        """Return a mismatch reason when AI output violates an active vNext route."""
        action = getattr(vnext_pre_ai, "action", None)
        if action not in {"NARROW_AI_TO_ROUTE", "NARROW_AI_EXCLUDE_FRAMEWORKS"}:
            return None
        if getattr(analysis, "decision", None) != "CANDIDATE":
            return None

        expected_side = getattr(vnext_pre_ai, "recommended_side", None)
        trade_params = getattr(analysis, "trade_parameters", None)
        actual_side = getattr(trade_params, "direction", None)
        if expected_side and actual_side and actual_side != expected_side:
            return f"side_mismatch_expected_{expected_side}_got_{actual_side}"

        expected_frameworks = set(getattr(vnext_pre_ai, "recommended_frameworks", ()) or ())
        blocked_frameworks = set(getattr(vnext_pre_ai, "blocked_frameworks", ()) or ())
        expected_route_families = {
            family
            for family in (getattr(vnext_pre_ai, "recommended_route_families", ()) or ())
            if is_vnext_ai_enforceable_route_family(family)
        }
        blocked_route_families = {
            family
            for family in (getattr(vnext_pre_ai, "blocked_route_families", ()) or ())
            if is_vnext_ai_enforceable_route_family(family)
        }
        actual_framework, _was_overridden, _routing_decision = resolve_vnext_effective_framework(
            analysis
        )
        actual_route_family = resolve_vnext_route_family(actual_framework)
        if actual_framework in blocked_frameworks:
            return f"framework_blocked_{actual_framework}"
        if actual_route_family in blocked_route_families:
            return f"route_family_blocked_{actual_route_family}"
        if expected_frameworks and actual_framework not in expected_frameworks:
            expected = "+".join(sorted(expected_frameworks))
            return f"framework_mismatch_expected_{expected}_got_{actual_framework}"
        if expected_route_families and actual_route_family not in expected_route_families:
            expected = "+".join(sorted(expected_route_families))
            return f"route_family_mismatch_expected_{expected}_got_{actual_route_family}"
        return None

    @staticmethod
    def _gtos_vnext_pending_telemetry(
        *,
        vnext_pre_ai,
        vnext_decision,
        vnext_risk_adjustment,
        vnext_pending_policy=None,
        vnext_ltf_path_execution=None,
        vnext_prop_safe_selector=None,
        vnext_moonshot_dynamic_execution=None,
    ) -> dict:
        evidence = getattr(vnext_decision, "evidence", {}) or {}
        metrics = evidence.get("metrics", {}) if isinstance(evidence, dict) else {}
        matched_rows = evidence.get("matched_rows") if isinstance(evidence, dict) else None
        selected_event = (
            getattr(vnext_moonshot_dynamic_execution, "source_event", None) or {}
        )
        if not isinstance(selected_event, dict):
            selected_event = {}
        broader_metrics = selected_event.get("broader_origin_metrics")
        if not isinstance(broader_metrics, dict):
            broader_metrics = {}
        matched_rows_status = None
        if matched_rows in (0, 0.0) and selected_event.get("broader_origin_allowed") is True:
            matched_rows_status = (
                "live_generated_broader_origin_pre_ai_decision_has_no_static_"
                "matched_rows_denominator; dynamic_selected_cell_and_broader_origin_"
                "metrics_are_recorded_separately"
            )

        def _metric_sum(name: str):
            payload = metrics.get(name) if isinstance(metrics, dict) else None
            return payload.get("sum") if isinstance(payload, dict) else None

        return {
            "gtos_vnext_pre_ai_action": getattr(vnext_pre_ai, "action", None),
            "gtos_vnext_pre_ai_recommended_side": getattr(vnext_pre_ai, "recommended_side", None),
            "gtos_vnext_pre_ai_recommended_frameworks": list(
                getattr(vnext_pre_ai, "recommended_frameworks", ()) or ()
            ),
            "gtos_vnext_pre_ai_recommended_route_families": list(
                getattr(vnext_pre_ai, "recommended_route_families", ()) or ()
            ),
            "gtos_vnext_pre_ai_blocked_sides": list(
                getattr(vnext_pre_ai, "blocked_sides", ()) or ()
            ),
            "gtos_vnext_pre_ai_blocked_frameworks": list(
                getattr(vnext_pre_ai, "blocked_frameworks", ()) or ()
            ),
            "gtos_vnext_pre_ai_blocked_route_families": list(
                getattr(vnext_pre_ai, "blocked_route_families", ()) or ()
            ),
            "gtos_vnext_pre_ai_risk_vetoed_sides": list(
                getattr(vnext_pre_ai, "risk_vetoed_sides", ()) or ()
            ),
            "gtos_vnext_pre_ai_side_risk_reasons": dict(
                getattr(vnext_pre_ai, "side_risk_reasons", {}) or {}
            ),
            "gtos_vnext_decision": getattr(vnext_decision, "decision", None),
            "gtos_vnext_reason": getattr(vnext_decision, "reason", None),
            "gtos_vnext_matched": getattr(vnext_decision, "matched", None),
            "gtos_vnext_matched_rows": matched_rows,
            "gtos_vnext_matched_rows_status": matched_rows_status,
            "gtos_vnext_broader_origin_selected_rows": broader_metrics.get("selected_count"),
            "gtos_vnext_broader_origin_performance_rows": broader_metrics.get("performance_rows"),
            "gtos_vnext_selected_cell_risk_pct": selected_event.get("selected_cell_risk_pct"),
            "gtos_vnext_selected_cell_risk_cell_id": selected_event.get(
                "selected_cell_risk_cell_id"
            ),
            "gtos_vnext_selected_cell_risk_status": (
                "positive_selected_cell_risk"
                if selected_event.get("selected_cell_risk_allowed") is True
                else selected_event.get("selected_cell_risk_status")
            ),
            "gtos_vnext_cost_adjusted_r_sum": _metric_sum("cost_adjusted_simulated_r"),
            "gtos_vnext_proxy_score_sum": _metric_sum("proxy_score"),
            "gtos_vnext_stress_r_sum": _metric_sum("stress_simulated_r"),
            "gtos_vnext_effective_n_sum": _metric_sum("effective_n"),
            "gtos_vnext_risk_multiplier": getattr(vnext_risk_adjustment, "multiplier", None),
            "gtos_vnext_risk_would_multiplier": getattr(
                vnext_risk_adjustment,
                "would_multiplier",
                None,
            ),
            "gtos_vnext_risk_reason": getattr(vnext_risk_adjustment, "reason", None),
            "gtos_vnext_pending_policy_action": getattr(
                vnext_pending_policy,
                "action",
                None,
            ),
            "gtos_vnext_pending_policy_would_action": getattr(
                vnext_pending_policy,
                "would_action",
                None,
            ),
            "gtos_vnext_pending_policy_applied": getattr(
                vnext_pending_policy,
                "applied",
                None,
            ),
            "gtos_vnext_pending_policy_reason": getattr(
                vnext_pending_policy,
                "reason",
                None,
            ),
            "gtos_vnext_ltf_path_action": getattr(
                vnext_ltf_path_execution,
                "action",
                None,
            ),
            "gtos_vnext_ltf_path_would_action": getattr(
                vnext_ltf_path_execution,
                "would_action",
                None,
            ),
            "gtos_vnext_ltf_path_applied": getattr(
                vnext_ltf_path_execution,
                "applied",
                None,
            ),
            "gtos_vnext_ltf_path_reason": getattr(
                vnext_ltf_path_execution,
                "reason",
                None,
            ),
            "gtos_vnext_ltf_path_monitor_timeframe": getattr(
                vnext_ltf_path_execution,
                "monitor_timeframe",
                None,
            ),
            "gtos_vnext_ltf_path_adjusted_entry_price": getattr(
                vnext_ltf_path_execution,
                "adjusted_entry_price",
                None,
            ),
            "gtos_vnext_prop_safe_selector_action": getattr(
                vnext_prop_safe_selector,
                "action",
                None,
            ),
            "gtos_vnext_prop_safe_selector_would_action": getattr(
                vnext_prop_safe_selector,
                "would_action",
                None,
            ),
            "gtos_vnext_prop_safe_selector_applied": getattr(
                vnext_prop_safe_selector,
                "applied",
                None,
            ),
            "gtos_vnext_prop_safe_selector_after_risk_pct": getattr(
                vnext_prop_safe_selector,
                "after_risk_pct",
                None,
            ),
            "gtos_vnext_prop_safe_selector_reason": getattr(
                vnext_prop_safe_selector,
                "reason",
                None,
            ),
            "gtos_vnext_dynamic_policy_selected": getattr(
                vnext_moonshot_dynamic_execution,
                "selected_policy",
                None,
            ),
            "gtos_vnext_execution_policy_id": getattr(
                vnext_moonshot_dynamic_execution,
                "execution_policy_id",
                None,
            ),
            "gtos_vnext_dynamic_policy_applied": getattr(
                vnext_moonshot_dynamic_execution,
                "applied",
                None,
            ),
            "gtos_vnext_dynamic_policy_replaced_policy": getattr(
                vnext_moonshot_dynamic_execution,
                "replaced_policy",
                None,
            ),
            "gtos_vnext_dynamic_policy_candidate_action": getattr(
                vnext_moonshot_dynamic_execution,
                "candidate_action",
                None,
            ),
            "gtos_vnext_dynamic_policy_decision_status": getattr(
                vnext_moonshot_dynamic_execution,
                "decision_status",
                None,
            ),
            "gtos_vnext_dynamic_policy_source_quality_action": getattr(
                vnext_moonshot_dynamic_execution,
                "source_quality_action",
                None,
            ),
            "gtos_vnext_dynamic_policy_exit_management_action": getattr(
                vnext_moonshot_dynamic_execution,
                "exit_management_action",
                None,
            ),
            "gtos_vnext_dynamic_policy_prop_action": getattr(
                vnext_moonshot_dynamic_execution,
                "prop_action",
                None,
            ),
            "gtos_vnext_dynamic_policy_fixed_target_role": getattr(
                vnext_moonshot_dynamic_execution,
                "fixed_target_role",
                None,
            ),
        }

    def _gtos_vnext_runtime_cfg(self) -> dict:
        if not isinstance(self.config, dict):
            return {}
        return self.config.get("gtos_vnext_runtime", {}) or {}

    @staticmethod
    def _ltf_timeframe_minutes(timeframe: str | None) -> int:
        tf = str(timeframe or "M1").upper()
        if tf.startswith("M") and tf[1:].isdigit():
            return max(1, int(tf[1:]))
        return 1

    def _latest_closed_ltf_candle(
        self,
        candles: list[dict],
        timeframe: str,
        now: Optional[datetime] = None,
    ) -> Optional[dict]:
        ref = now or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        else:
            ref = ref.astimezone(timezone.utc)
        minutes = self._ltf_timeframe_minutes(timeframe)
        for candle in reversed(candles):
            raw_time = candle.get("time")
            if not raw_time:
                continue
            try:
                opened = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            except ValueError:
                continue
            if opened.tzinfo is None:
                opened = opened.replace(tzinfo=timezone.utc)
            else:
                opened = opened.astimezone(timezone.utc)
            if opened + timedelta(minutes=minutes) <= ref + timedelta(seconds=2):
                return candle
        return None

    def _build_gtos_vnext_ltf_path_state(
        self,
        *,
        trade_params,
        raw_data: dict,
        kill_zone: str,
    ) -> dict:
        cfg = self._gtos_vnext_runtime_cfg()
        timeframe = str(cfg.get("ltf_path_monitor_timeframe", "M1") or "M1").upper()
        fetch_bars = int(cfg.get("ltf_path_monitor_fetch_bars", 4) or 4)
        candles = []
        if isinstance(raw_data, dict):
            candles = list((raw_data.get("candles", {}) or {}).get(timeframe, []) or [])
        source_system = "raw_data"
        if not candles and cfg.get("ltf_path_fetch_on_decision", True):
            try:
                from src.components.data_ingestion import TF_MAP

                tf_const = TF_MAP.get(timeframe) or {"M1": 1, "M5": 5}.get(timeframe)
                if tf_const is not None:
                    candles = list(self.mt5.get_candles(self._mt5_symbol, tf_const, fetch_bars) or [])
                    source_system = "mt5_readonly_fetch"
            except Exception as exc:  # noqa: BLE001
                return {
                    "source_complete": False,
                    "path_source_status": "ltf_fetch_failed",
                    "source_timeframe": timeframe,
                    "source_system": "mt5_readonly_fetch",
                    "route_session": kill_zone,
                    "error": str(exc),
                }
        candle = self._latest_closed_ltf_candle(candles, timeframe)
        if candle is None:
            return {
                "source_complete": False,
                "path_source_status": "no_closed_ltf_candle",
                "source_timeframe": timeframe,
                "source_system": source_system,
                "route_session": kill_zone,
            }
        direction = str(getattr(trade_params, "direction", "") or "").upper()
        entry = float(getattr(trade_params, "entry_price", 0.0) or 0.0)
        stop = float(getattr(trade_params, "stop_loss", 0.0) or 0.0)
        target = float(getattr(trade_params, "take_profit_1", 0.0) or 0.0)
        high = float(candle.get("high", 0.0) or 0.0)
        low = float(candle.get("low", 0.0) or 0.0)
        close = float(candle.get("close", 0.0) or 0.0)
        sl_distance = abs(entry - stop)
        if direction == "LONG":
            entry_touched = low <= entry if entry else False
            target_touched = high >= target if target else False
            protective_touched = low <= stop if stop else False
            signed_distance_to_entry = (close - entry) / sl_distance if sl_distance else None
        elif direction == "SHORT":
            entry_touched = high >= entry if entry else False
            target_touched = low <= target if target else False
            protective_touched = high >= stop if stop else False
            signed_distance_to_entry = (entry - close) / sl_distance if sl_distance else None
        else:
            entry_touched = False
            target_touched = False
            protective_touched = False
            signed_distance_to_entry = None
        near_threshold = float(cfg.get("ltf_path_near_entry_threshold_r", 0.25) or 0.25)
        distance_abs = abs(signed_distance_to_entry) if signed_distance_to_entry is not None else None
        if entry_touched:
            approach_state = "entry_touched"
        elif distance_abs is not None and distance_abs <= near_threshold:
            approach_state = "near_entry"
        else:
            approach_state = "monitoring"
        return {
            "source_complete": True,
            "path_source_status": "asof_ltf_candle_available",
            "source_timeframe": timeframe,
            "source_system": source_system,
            "route_session": kill_zone,
            "asof_cutoff_utc": candle.get("time"),
            "checked_candle_time_utc": candle.get("time"),
            "side": direction,
            "entry_touched": entry_touched,
            "target_touched_without_entry": bool(target_touched and not entry_touched),
            "protective_touched_before_entry": bool(protective_touched and not entry_touched),
            "same_bar_ambiguous": bool(entry_touched and (target_touched or protective_touched)),
            "distance_to_entry_r": signed_distance_to_entry,
            "approach_state": approach_state,
            "entry_price": entry,
            "stop_loss": stop,
            "take_profit_1": target,
        }

    def _apply_gtos_vnext_risk_adjustment(self, *, current_risk_pct: float,
                                          vnext_decision, record: dict | None):
        """Apply/record vNext evidence-backed sizing after existing risk gates."""
        adjustment = apply_vnext_risk_adjustment(
            current_risk_pct=current_risk_pct,
            decision=vnext_decision,
            config=self.config,
        )
        if record is not None:
            attach_vnext_risk_adjustment_to_record(record, adjustment)
        logger.info(
            "GTOS_VNEXT_RISK decision=%s applied=%s multiplier=%.3f "
            "would_multiplier=%.3f risk=%.3f%%->%.3f%% reason=%s",
            adjustment.decision,
            adjustment.applied,
            adjustment.multiplier,
            adjustment.would_multiplier,
            adjustment.before_risk_pct,
            adjustment.after_risk_pct,
            adjustment.reason,
        )
        return adjustment

    def _check_sprt_class_halt_gate(self, kill_zone: str) -> bool:
        """Block new evaluation when class-aware LONG-WR halt state is active."""
        try:
            runtime = getattr(self, "_sprt_class_halt_runtime", None)
            if runtime is None:
                runtime = SprtClassHaltRuntime(self.config)
                self._sprt_class_halt_runtime = runtime
            decision = runtime.evaluate_gate(self._symbol)
            if not decision.should_block:
                if decision.would_block:
                    logger.warning(
                        "SPRT_CLASS_HALT shadow would block %s: %s",
                        self._symbol,
                        decision.reason,
                    )
                return False

            intent_tid = ""
            if self.execution and self.execution.pending_intent:
                intent_tid = self.execution.pending_intent.trade_id
                self.execution.cancel_limit_intent("sprt_class_halt")
            if intent_tid:
                self._clear_pending_trade_record(intent_tid, reason="sprt_class_halt")
            self._log_candle(
                "SPRT_CLASS_HALT",
                f"{decision.reason}:{decision.verdict}",
                kill_zone,
            )
            logger.critical(
                "SPRT_CLASS_HALT blocked %s KZ=%s verdict=%s WR=%s n=%s",
                self._symbol,
                kill_zone,
                decision.verdict,
                decision.actual_wr,
                decision.n,
            )
            return True
        except Exception as exc:
            logger.warning("SPRT class halt gate failed open: %s", exc)
            return False

    def _apply_autocorrelation_risk_sizing(self, *, current_risk_pct: float,
                                           raw_data: dict, record: dict | None):
        """Apply/record H1 autocorrelation decay risk sizing."""
        decision = evaluate_autocorrelation_risk(
            current_risk_pct=current_risk_pct,
            raw_data=raw_data,
            config=self.config,
        )
        if record is not None:
            attach_autocorrelation_risk_to_record(record, decision)
        logger.info(
            "AUTOCORRELATION_RISK action=%s applied=%s %.3f%% -> %.3f%% "
            "autocorr=%s window=%s reason=%s",
            "REDUCE_RISK" if decision.applied else "NO_CHANGE",
            decision.applied,
            decision.before_risk_pct,
            decision.after_risk_pct,
            (
                None
                if decision.autocorrelation is None
                else round(decision.autocorrelation, 4)
            ),
            decision.window,
            decision.reason,
        )
        return decision

    @staticmethod
    def _first_present(*values):
        for value in values:
            if value not in (None, ""):
                return value
        return None

    @staticmethod
    def _parse_utc_datetime(value):
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            parsed = value
        elif isinstance(value, str):
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        else:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _extract_runtime_news_context(self, raw_data: dict) -> dict:
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        news_context = raw_data.get("news_context") if isinstance(raw_data.get("news_context"), dict) else {}
        event = self._first_present(
            raw_data.get("next_high_impact_event"),
            raw_data.get("high_impact_news"),
            news_context.get("next_event"),
            news_context.get("event"),
        )
        event = event if isinstance(event, dict) else {}
        current_time = self._parse_utc_datetime(
            self._first_present(
                raw_data.get("candle_close_utc"),
                raw_data.get("timestamp_utc"),
                raw_data.get("time_utc"),
            )
        ) or datetime.now(timezone.utc)

        if not event:
            news_calendar = getattr(self, "_news_calendar", None)
            if news_calendar is not None and getattr(news_calendar, "enabled", False):
                try:
                    event = news_calendar.get_next_event(
                        getattr(self, "_symbol", ""),
                        current_time,
                    ) or {}
                except Exception:
                    event = {}

        minutes = self._first_present(
            raw_data.get("news_minutes_to_event"),
            raw_data.get("high_impact_news_minutes_to_event"),
            news_context.get("minutes_to_event"),
            event.get("minutes_to_event"),
        )
        event_time = self._parse_utc_datetime(
            self._first_present(
                event.get("datetime_utc"),
                event.get("time_utc"),
                event.get("event_time_utc"),
                news_context.get("time_utc"),
            )
        )
        if minutes in (None, "") and event_time is not None:
            minutes = (event_time - current_time).total_seconds() / 60.0

        return {
            "news_minutes_to_event": minutes,
            "news_event_name": self._first_present(
                raw_data.get("news_event_name"),
                news_context.get("event_name"),
                event.get("event"),
                event.get("name"),
            ),
            "news_currency": self._first_present(
                raw_data.get("news_currency"),
                news_context.get("currency"),
                event.get("currency"),
            ),
            "news_impact": self._first_present(
                raw_data.get("news_impact"),
                news_context.get("impact"),
                event.get("impact"),
            ),
            "news_event_time_utc": (
                event_time.isoformat().replace("+00:00", "Z")
                if event_time is not None else None
            ),
            "news_source": self._first_present(
                raw_data.get("news_source"),
                news_context.get("source"),
                event.get("source"),
                "news_calendar" if event else None,
            ),
        }

    @staticmethod
    def _extract_runtime_volatility_context(raw_data: dict) -> dict:
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        volatility = raw_data.get("volatility_context")
        volatility = volatility if isinstance(volatility, dict) else {}
        macro = raw_data.get("macro_context")
        macro = macro if isinstance(macro, dict) else {}
        return {
            "volatility_gvz": SessionOrchestrator._first_present(
                raw_data.get("volatility_gvz"),
                raw_data.get("gvz"),
                raw_data.get("gvz_close"),
                raw_data.get("fred__GVZCLS__value"),
                raw_data.get("GVZCLS"),
                volatility.get("gvz"),
                volatility.get("gvz_close"),
                volatility.get("fred__GVZCLS__value"),
                macro.get("fred__GVZCLS__value"),
                macro.get("gvz"),
            ),
            "volatility_source": SessionOrchestrator._first_present(
                raw_data.get("volatility_source"),
                volatility.get("source"),
                macro.get("source"),
                "fred__GVZCLS" if SessionOrchestrator._first_present(
                    raw_data.get("fred__GVZCLS__value"),
                    volatility.get("fred__GVZCLS__value"),
                    macro.get("fred__GVZCLS__value"),
                ) not in (None, "") else None,
            ),
        }

    def _build_contextual_side_risk_context(
        self,
        *,
        analysis,
        raw_data: dict,
        kill_zone: str,
        vnext_decision,
        autocorr_risk,
    ) -> dict:
        """Build the compact runtime contract for contextual side-risk sizing."""
        raw_data = raw_data if isinstance(raw_data, dict) else {}
        event = getattr(vnext_decision, "event", {}) or {}
        if not isinstance(event, dict):
            event = {}
        evidence = getattr(vnext_decision, "evidence", {}) or {}
        if not isinstance(evidence, dict):
            evidence = {}
        framework = self._first_present(
            event.get("framework"),
            event.get("effective_framework"),
            getattr(analysis, "framework", None),
            raw_data.get("framework"),
            raw_data.get("selected_framework"),
        )
        route_family = self._first_present(
            event.get("route_family"),
            raw_data.get("route_family"),
            raw_data.get("mechanical_route_family"),
        )
        session = self._first_present(
            event.get("route_session"),
            raw_data.get("route_session"),
            raw_data.get("session"),
            kill_zone,
        )
        kz_window = getattr(self, "_kz_windows", {}).get(kill_zone, {})
        regime_decay = raw_data.get("regime_decay_asof") if isinstance(raw_data.get("regime_decay_asof"), dict) else {}
        ready8 = raw_data.get("ready8") if isinstance(raw_data.get("ready8"), dict) else {}
        news_context = self._extract_runtime_news_context(raw_data)
        volatility_context = self._extract_runtime_volatility_context(raw_data)
        return {
            "symbol": self._first_present(
                event.get("symbol"),
                event.get("source_symbol"),
                getattr(self, "_symbol", None),
            ),
            "source_symbol": self._first_present(
                event.get("source_symbol"),
                getattr(self, "_mt5_symbol", None),
                getattr(self, "_symbol", None),
            ),
            "symbol_family": self._first_present(
                event.get("symbol_family"),
                raw_data.get("symbol_family"),
            ),
            "side": self._first_present(
                event.get("side"),
                getattr(getattr(analysis, "trade_parameters", None), "direction", None),
            ),
            "session": session,
            "candle_time_utc": self._first_present(
                raw_data.get("candle_close_utc"),
                raw_data.get("timestamp_utc"),
                raw_data.get("time_utc"),
            ),
            "session_start_utc": self._format_min_utc(kz_window.get("start_min")),
            "session_end_utc": self._format_min_utc(kz_window.get("end_min")),
            "framework": framework,
            "route_family": route_family,
            "regime": self._first_present(
                raw_data.get("regime"),
                raw_data.get("market_regime"),
                regime_decay.get("regime"),
            ),
            "market_timeframe": self._first_present(
                event.get("market_timeframe"),
                raw_data.get("market_timeframe"),
                raw_data.get("timeframe"),
            ),
            "detector_version": self._first_present(
                raw_data.get("detector_version_at_eval"),
                raw_data.get("detector_version"),
                (self.config.get("market_state", {}) or {}).get("detector_version"),
            ),
            "timeframe": self._first_present(
                event.get("timeframe"),
                raw_data.get("timeframe"),
            ),
            "h1_autocorrelation": getattr(autocorr_risk, "autocorrelation", None),
            "h1_decay_risk_applied": getattr(autocorr_risk, "applied", False),
            "asian_range_info": dict(getattr(self, "_asian_range_info", {}) or {}),
            "asian_range_pct_of_adr": (
                (getattr(self, "_asian_range_info", {}) or {}).get("pct_of_adr")
            ),
            "asian_range_category": (
                (getattr(self, "_asian_range_info", {}) or {}).get("category")
            ),
            "ready8_card_id": self._first_present(
                raw_data.get("ready8_card_id"),
                ready8.get("card_id"),
            ),
            "ready8_horizon_m15_bars": self._first_present(
                raw_data.get("ready8_horizon_m15_bars"),
                ready8.get("horizon_m15_bars"),
            ),
            "ready8_target_family_id": self._first_present(
                raw_data.get("ready8_target_family_id"),
                ready8.get("target_family_id"),
            ),
            "ready8_partition_assignment": self._first_present(
                raw_data.get("ready8_partition_assignment"),
                ready8.get("partition_assignment"),
            ),
            "ready8_descriptor_name": self._first_present(
                raw_data.get("ready8_descriptor_name"),
                ready8.get("descriptor_name"),
            ),
            "ready8_descriptor_value": self._first_present(
                raw_data.get("ready8_descriptor_value"),
                ready8.get("descriptor_value"),
            ),
            "ready8_wait_gap_bucket": self._first_present(
                raw_data.get("ready8_wait_gap_bucket"),
                ready8.get("wait_gap_bucket"),
            ),
            "ready8_prior_24h_count_bucket": self._first_present(
                raw_data.get("ready8_prior_24h_count_bucket"),
                ready8.get("prior_24h_count_bucket"),
            ),
            "ready8_source_window": self._first_present(
                raw_data.get("ready8_source_window"),
                ready8.get("source_window"),
            ),
            "ready8_source_segment_sha256": self._first_present(
                raw_data.get("ready8_source_segment_sha256"),
                ready8.get("source_segment_sha256"),
            ),
            "ready8_canonical_economic_group": self._first_present(
                raw_data.get("ready8_canonical_economic_group"),
                ready8.get("canonical_economic_group"),
            ),
            "fvg_in_impulse": self._first_present(
                raw_data.get("fvg_in_impulse"),
                raw_data.get("has_fvg_in_impulse"),
            ),
            "creates_fvg": self._first_present(
                raw_data.get("creates_fvg"),
                raw_data.get("impulse_creates_fvg"),
            ),
            "sweep_before_ob": self._first_present(
                raw_data.get("sweep_before_ob"),
                raw_data.get("liquidity_sweep_before_ob"),
                raw_data.get("pre_ob_sweep_detected"),
                raw_data.get("ob_preceded_by_sweep"),
                raw_data.get("setup_has_sweep_before_ob"),
            ),
            "sweep_before_poi": self._first_present(
                raw_data.get("sweep_before_poi"),
                raw_data.get("liquidity_sweep_before_poi"),
            ),
            "m15_session_vol_ratio": self._first_present(
                raw_data.get("m15_session_vol_ratio"),
                raw_data.get("session_vol_ratio"),
                raw_data.get("mso_m15_session_vol_ratio"),
                raw_data.get("internal_session_vol_ratio"),
            ),
            "m15_clv_avg_5": self._first_present(
                raw_data.get("m15_clv_avg_5"),
                raw_data.get("clv_avg_5"),
                raw_data.get("mso_m15_clv_avg_5"),
            ),
            "m15_bvc_buy_fraction": self._first_present(
                raw_data.get("m15_bvc_buy_fraction"),
                raw_data.get("bvc_buy_fraction"),
                raw_data.get("mso_m15_bvc_buy_fraction"),
            ),
            "m15_net_flow_5": self._first_present(
                raw_data.get("m15_net_flow_5"),
                raw_data.get("net_flow_5"),
                raw_data.get("mso_m15_net_flow_5"),
            ),
            **news_context,
            **volatility_context,
            "vnext_decision": getattr(vnext_decision, "decision", None),
            "vnext_event": dict(event),
            "vnext_evidence": evidence,
        }

    def _apply_contextual_side_risk_sizing(
        self,
        *,
        current_risk_pct: float,
        analysis,
        raw_data: dict,
        kill_zone: str,
        vnext_decision,
        autocorr_risk,
        record: dict | None,
    ):
        """Apply/record contextual side-risk sizing in the runtime path."""
        context = self._build_contextual_side_risk_context(
            analysis=analysis,
            raw_data=raw_data,
            kill_zone=kill_zone,
            vnext_decision=vnext_decision,
            autocorr_risk=autocorr_risk,
        )
        direction = context.get("side") or getattr(
            getattr(analysis, "trade_parameters", None),
            "direction",
            "",
        )
        decision = _side_aware.evaluate_contextual_side_multiplier(
            base_risk_pct=current_risk_pct,
            direction=direction,
            config=self.config,
            context=context,
        )
        _side_aware.attach_contextual_side_risk_to_record(record, decision)
        logger.info(
            "CONTEXTUAL_SIDE_RISK mode=%s side=%s applied=%s multiplier=%.3f "
            "would_multiplier=%.3f score=%.3f risk=%.3f%%->%.3f%% "
            "symbol_family=%s session=%s framework=%s route_family=%s "
            "news_minutes=%s gvz=%s reason=%s",
            decision.mode,
            decision.direction,
            decision.applied,
            decision.multiplier,
            decision.would_multiplier,
            decision.score,
            decision.before_risk_pct,
            decision.after_risk_pct,
            context.get("symbol_family"),
            context.get("session"),
            context.get("framework"),
            context.get("route_family"),
            context.get("news_minutes_to_event"),
            context.get("volatility_gvz"),
            decision.reason,
        )
        return decision

    def _vnext_replaces_count_trade_caps(self) -> bool:
        cfg = self.config.get("gtos_vnext_runtime", {}) if isinstance(self.config, dict) else {}
        return bool(
            cfg.get("enabled", False)
            and cfg.get("apply_to_execution", False)
            and cfg.get("moonshot_dynamic_execution_router_enabled", False)
            and cfg.get("moonshot_dynamic_execution_router_apply_to_execution", False)
        )

    def _check_kill_zone_trade_cap(self, kill_zone: str) -> bool:
        """Return True only when a legacy kill-zone count cap blocks trading."""
        if self._vnext_replaces_count_trade_caps():
            logger.info(
                "vNext account-risk governance replaces kill-zone count cap; "
                "kill_zone=%s trades=%s cap=%s",
                kill_zone,
                self.session_state.get(f"trades_{kill_zone}", 0),
                (self.config.get("risk", {}) if isinstance(self.config, dict) else {}).get(
                    "max_trades_per_kill_zone",
                ),
            )
            return False
        risk_cfg = self.config.get("risk", {}) if isinstance(self.config, dict) else {}
        if not risk_cfg.get("max_trades_per_kill_zone_enabled", True):
            return False
        try:
            max_trades = int(risk_cfg.get("max_trades_per_kill_zone", 2))
        except (TypeError, ValueError):
            max_trades = 2
        if max_trades <= 0:
            return False
        kz_key = f"trades_{kill_zone}"
        try:
            trades_in_kz = int(self.session_state.get(kz_key, 0) or 0)
        except (TypeError, ValueError):
            trades_in_kz = 0
        if trades_in_kz < max_trades:
            return False

        if getattr(self, "execution", None) is not None:
            pending = getattr(self.execution, "pending_intent", None)
            if pending is not None:
                intent_tid = getattr(pending, "trade_id", "") or ""
                self.execution.cancel_limit_intent("kill_zone_trade_cap_stop")
                self._clear_pending_trade_record(
                    intent_tid,
                    reason="kz_trade_cap_stop",
                )
        self._log_candle(
            "EMERGENCY_STOP",
            f"kill_zone_trade_cap:{kill_zone} trades={trades_in_kz} >= {max_trades}",
            kill_zone,
        )
        return True

    def _cancel_local_pending_intent_for_dormant(self, *, reason: str) -> bool:
        """Cancel this process's in-memory pending intent under dormant state.

        The daily-loss dormant marker is portfolio-wide. Each symbol process
        owns its own in-memory software limit, so the triggering process cannot
        directly mutate every other process. This hook makes every process
        cancel its local intent the next time it observes the marker, before
        returning from the pre-AI dormant gate.
        """
        execution = getattr(self, "execution", None)
        pending = getattr(execution, "pending_intent", None) if execution else None
        if pending is None:
            return False
        trade_id = getattr(pending, "trade_id", "") or ""
        try:
            execution.cancel_limit_intent(reason)
        finally:
            try:
                self._clear_pending_trade_record(trade_id, reason=reason)
            except Exception as exc:  # noqa: BLE001 - cancellation wins
                logger.warning(
                    "daily_loss_stop: pending trade record clear failed: %s",
                    exc,
                )
        logger.warning(
            "daily_loss_stop: canceled local pending intent %s due to dormant state",
            trade_id or "<unknown>",
        )
        return True

    def _attach_gtos_vnext_block_risk_preview(self, *, vnext_decision,
                                              record: dict | None):
        """Attach vNext risk evidence when execution is blocked before sizing."""
        try:
            base_risk = float(
                (self.config.get("risk", {}) or {}).get("risk_per_trade_pct", 1.0)
                or 1.0
            )
        except (TypeError, ValueError):
            base_risk = 1.0
        return self._apply_gtos_vnext_risk_adjustment(
            current_risk_pct=base_risk,
            vnext_decision=vnext_decision,
            record=record,
        )

    # === MAIN LOOP ===

    def _main_loop(self):
        """Event-driven loop on M15 candle closes within kill zone windows."""
        while self.running:
            now = datetime.now(timezone.utc)

            # T1.1 heartbeat — best-effort, never blocks or crashes the loop.
            # Consumed by src.safety.heartbeat_monitor (watchdog-launched).
            # WARNING level (was debug) — failed write is the silent-degradation
            # tell that prior shared-file architecture suppressed.
            try:
                _write_heartbeat(extra={"symbol": self._symbol})
            except Exception as _hb_err:  # noqa: BLE001 — safety-critical best-effort
                logger.warning(
                    "heartbeat write raised (non-fatal) symbol=%s: %s",
                    self._symbol, _hb_err,
                )

            today = now.strftime("%Y-%m-%d")
            if self.session_state["date"] != today:
                self._new_day(today)

            kz = self._get_active_kill_zone(now)

            if kz:
                if self.session_state["current_kill_zone"] != kz:
                    # Save summary for the previous KZ if transitioning
                    prev_kz = self.session_state["current_kill_zone"]
                    if prev_kz:
                        self._save_session_summary(prev_kz)
                    self._enter_kill_zone(kz)

                next_candle = self._next_m15_close(now)
                wait_seconds = (next_candle - now).total_seconds()
                if wait_seconds > 0:
                    logger.debug(f"Waiting {wait_seconds:.0f}s for next M15 close at {next_candle}")
                    # Sleep in 60s chunks with trade monitoring between each
                    self._monitored_sleep(wait_seconds)

                if not self.running:
                    break

                self._process_candle(kz)

                self._check_trade_and_capture()

            elif self._is_between_kz(now):
                self._check_trade_and_capture()
                self._monitor_expired_poi_watches_from_mt5(
                    self.session_state.get("current_kill_zone") or "between_kz",
                )
                if self.execution.active_trade:
                    self._manage_timeout_trailing()
                elif self.execution.pending_intent:
                    self._check_pending_limit_outside_kz()

                # Sleep until the next KZ starts
                next_kz_start = self._next_kz_start_time(now)
                if next_kz_start:
                    wait = (next_kz_start - now).total_seconds()
                    self._interruptible_sleep(min(wait, 60))
                else:
                    self._interruptible_sleep(60)

            elif self._is_after_all_kz(now):
                self._check_trade_and_capture()
                self._monitor_expired_poi_watches_from_mt5(
                    self.session_state.get("current_kill_zone") or "after_all_kz",
                )
                if self.execution.active_trade:
                    self._manage_timeout_trailing()
                    self._monitored_sleep(60)
                elif self.execution.pending_intent:
                    self._check_pending_limit_outside_kz()
                    self._interruptible_sleep(60)
                else:
                    # BUG #26 fix (2026-04-28 GBPJPY cascade): before
                    # declaring "no active trade" and ending the session,
                    # reconcile against MT5 reality. ``mt5.get_positions``
                    # already filters by MAGIC_NUMBER (see
                    # ``src/mt5/mt5_interface.py:80-81`` + ``mt5_mock.py:75-76``
                    # / ``mt5_real.py``), so a non-empty result is OUR open
                    # position that the orchestrator's local state did not
                    # know about. Adopt it via reconcile_on_startup() and
                    # stay alive in monitoring-only mode (no new evals
                    # outside KZ; position-mgmt hooks still fire). The
                    # original failure: orchestrator emitted "All kill zones
                    # complete, no active trade. Ending session." while a
                    # +0.74R GBPJPY position was open, leading to a
                    # watchdog respawn that cascaded into BUG #27 + #28.
                    if self._reconcile_open_positions_or_continue():
                        # Adopted an orphan; treat as active trade and
                        # immediately enter monitoring on this iteration.
                        self._manage_timeout_trailing()
                        self._monitored_sleep(60)
                        continue

                    # Save summary for the last KZ
                    last_kz = self.session_state.get("current_kill_zone")
                    if last_kz:
                        self._save_session_summary(last_kz)
                    logger.info("All kill zones complete, no active trade. Ending session.")
                    self._end_session()
                    break
            else:
                # Before first KZ — also monitor any active trade or pending limit
                if self.execution.active_trade:
                    self._check_trade_and_capture()
                elif self.execution.pending_intent:
                    self._check_pending_limit_outside_kz()
                else:
                    self._monitor_expired_poi_watches_from_mt5("pre_kz")
                next_kz_start = self._next_kz_start_time(now)
                if next_kz_start:
                    # Wake 5 minutes before KZ
                    pre_kz = next_kz_start - timedelta(minutes=5)
                    if now < pre_kz:
                        wait = (pre_kz - now).total_seconds()
                        self._monitored_sleep(min(wait, 300))
                    else:
                        self._monitored_sleep(10)
                else:
                    self._monitored_sleep(60)

    def _process_candle(self, kill_zone: str):
        """Full pipeline: Data → MSO → Pre-screen → Analyze → Safety → Execute."""
        logger.info("Processing candle - %s KZ", kill_zone)

        # Update daily P&L and portfolio drawdown from MT5 before any evaluation
        self._update_daily_pnl()

        # Portfolio drawdown emergency stop
        drawdown_pct = self.session_state.get("portfolio_drawdown_pct", 0.0)
        max_drawdown = self.config.get("risk", {}).get("max_portfolio_drawdown_pct", 4.0)
        if drawdown_pct >= max_drawdown:
            intent_tid = (
                self.execution.pending_intent.trade_id
                if self.execution.pending_intent else ""
            )
            self.execution.cancel_limit_intent("portfolio_drawdown_stop")
            self._clear_pending_trade_record(intent_tid, reason="drawdown_stop")
            self._log_candle("EMERGENCY_STOP", f"portfolio_drawdown={drawdown_pct:.2f}% >= {max_drawdown}%", kill_zone)
            return

        # Consecutive loss emergency stop
        consec_losses = self.session_state.get("consecutive_losses", 0)
        max_consec = self.config.get("risk", {}).get("max_consecutive_losses", 5)
        if consec_losses >= max_consec:
            intent_tid = (
                self.execution.pending_intent.trade_id
                if self.execution.pending_intent else ""
            )
            self.execution.cancel_limit_intent("consecutive_losses_stop")
            self._clear_pending_trade_record(intent_tid, reason="consec_losses")
            self._log_candle("EMERGENCY_STOP", f"consecutive_losses={consec_losses} >= {max_consec}", kill_zone)
            return

        if self._check_kill_zone_trade_cap(kill_zone):
            return

        # T2.8 daily-loss stop — MTM daily P&L breach triggers dormant state.
        # Cancels pending limits + sends Telegram alert, then skips AI call.
        # Open positions close naturally via their own SL/TP (locked decision #5).
        if self._check_and_trigger_daily_loss_stop(kill_zone):
            return

        # T2.8 dormant gate — if the marker was set earlier today (possibly by
        # a prior process), short-circuit before making any AI call. Permissions
        # Gate 3 also enforces this; skipping here avoids spending a token budget
        # just to be rejected by Gate 3. The old one-trade KZ cap remains
        # removed; the quick-reference emergency stop above only blocks the
        # third trade in a single kill zone.
        if _dormant_state.is_dormant_today():
            self._cancel_local_pending_intent_for_dormant(
                reason="daily_loss_stop_dormant",
            )
            self._log_candle(
                "SKIP_DORMANT",
                "daily_loss_stop active — no AI call until 00:00 UTC",
                kill_zone,
            )
            return

        if self._check_sprt_class_halt_gate(kill_zone):
            return

        # Skip first NY candle (13:00 UTC) if configured — 0% WR on XAUUSD (n=7)
        if self._should_skip_first_ny_candle(kill_zone) and not self.execution.pending_intent:
            self._log_candle("SKIP_NY_OPEN_CANDLE",
                             "skip_first_ny_candle: 0% WR at 13:00 UTC", kill_zone)
            return

        try:
            # 1. Ingest live data
            raw_data = self._ingest_live_data_with_reconnect(kill_zone)
            self._data_incomplete_streak = 0
            source_quality = evaluate_m15_ohlc_source_quality(
                raw_data,
                config=self.config,
            )
            if source_quality.get("status") != SOURCE_QUALITY_OK:
                raw_data[SOURCE_QUALITY_KEY] = source_quality
                feature_status = source_quality.get("source_path_feature_status")
                if feature_status:
                    raw_data["source_path_feature_status"] = feature_status
                raw_data["source_window_complete"] = False
                reason = str(
                    source_quality.get("reason")
                    or "raw_data_m15_malformed_ohlc_price_scale"
                )
                self._record_vnext_broader_origin_no_candidate(
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    final_outcome="NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_MALFORMED_SOURCE",
                    reason=reason,
                    decision_path=(
                        "vnext_broader_origin_malformed_source_consumed_before_pending_"
                        "fill_old_primary_analyzer_and_l2"
                    ),
                    candidate_count=0,
                )
                self._log_candle(
                    "NO_TRADE_GTOS_VNEXT_BROADER_ORIGIN_MALFORMED_SOURCE",
                    reason,
                    kill_zone,
                )
                return
            self._monitor_expired_poi_watches(raw_data, kill_zone)

            # 1b. Pending limit fill check — runs every candle while intent is active.
            # Emergency stops above (drawdown, consec_losses) already fired.
            # No new setup evaluated while a limit intent is pending.
            if self.execution.pending_intent:
                m15_candles = raw_data.get("candles", {}).get("M15", [])
                if m15_candles:
                    candle = self._latest_closed_m15_candle(m15_candles)
                    if candle is None:
                        logger.warning(
                            "Pending limit check skipped: no closed M15 candle available "
                            "(symbol=%s, m15_count=%d)",
                            self._symbol,
                            len(m15_candles),
                        )
                        return
                    # Capture intent trade_id BEFORE check_limit_fill can clear it
                    pre_check_intent = self.execution.pending_intent
                    pre_fill_trade_id = pre_check_intent.trade_id
                    self._archive_if_pending_limit_clock_expired(pre_check_intent)
                    trade_state = self.execution.check_limit_fill(
                        candle,
                        telemetry_context={
                            "source_branch": "inside_kz_process_candle",
                            "check_context": "inside_kz",
                            "kill_zone": kill_zone,
                            "session": kill_zone,
                            "source_symbol": self._mt5_symbol,
                            "raw_data_m15_count": len(m15_candles),
                            "raw_data_latest_m15_time_utc": m15_candles[-1].get("time"),
                            "latest_m15_time_utc": candle.get("time"),
                            "asof_cutoff_utc": candle.get("time"),
                            "record_path": self._pending_trade_record_path,
                        },
                    )
                    if trade_state:
                        self.session_state["trades_today"] += 1
                        # T2.8 (dc4cec2) removed the ``kz_trades`` binding at the
                        # top of _process_candle when the per-KZ cap was deprecated
                        # but left this stale reference behind. Read the counter
                        # directly — it's observability only (no trading cap).
                        kz_key = f"trades_{kill_zone}"
                        self.session_state[kz_key] = self.session_state.get(kz_key, 0) + 1
                        self._log_candle("LIMIT_FILLED", trade_state.trade_id, kill_zone)
                        logger.info(
                            "LIMIT FILLED: %s at %.5f",
                            trade_state.trade_id, trade_state.entry_price,
                        )
                        notify_limit_filled(
                            symbol=self._symbol, direction=trade_state.direction,
                            entry=trade_state.entry_price, trade_id=trade_state.trade_id,
                            sl=trade_state.stop_loss, tp=trade_state.take_profit_1,
                            vnext_context=build_vnext_notification_context(
                                trade_state,
                                lifecycle_event="fill",
                            ),
                        )
                        self._promote_pending_record_on_fill()
                        try:
                            self._init_trade_tracking(trade_state)
                        except Exception as e:
                            logger.error("Exit tracking init failed on limit fill: %s", e)
                    elif self.execution.pending_intent is None:
                        # Intent cleared without a fill (expiry / wrong-side / SL-too-close).
                        self._clear_pending_trade_record(
                            pre_fill_trade_id, reason="inside_kz_no_fill",
                        )
                return  # whether filled or still pending — no new setup this candle

            # 2. Compute MSO
            mso = compute_market_state(raw_data, self.config)
            self._last_mso = mso
            canonical_candle_close_utc = raw_data.get("candle_close_utc")
            self._record_forward_capture_evaluation_shadow(
                mso=mso,
                raw_data=raw_data,
                evaluation_stage="MSO_COMPUTED_PRE_AI",
                kill_zone=kill_zone,
            )
            if self._process_vnext_broader_origin_candidates(
                raw_data=raw_data,
                mso=mso,
                kill_zone=kill_zone,
            ):
                return

            # 2a. D1-bias-lag shadow logger (T5.24) — observation-only.
            # Detects candles where D1 structure contradicts both H1 AND H4
            # (the pattern that produced 0 CANDIDATEs on NAS100 W14 during a
            # +4.20% rally). Never gates trades. Wrapped in try/except as
            # belt-and-suspenders — the logger already self-isolates.
            try:
                dbl_cfg = (self.config.get("shadow_loggers", {}) or {}).get(
                    "d1_bias_lag_logger", {}
                ) or {}
                if dbl_cfg.get("enabled", True):
                    dbl_threshold = int(dbl_cfg.get("alert_threshold_consecutive", 20))
                    dbl_ts = getattr(mso, "timestamp_utc", "") or datetime.now(timezone.utc).isoformat()
                    log_if_d1_bias_lag(
                        mso=mso,
                        symbol=self._symbol,
                        timestamp_utc=str(dbl_ts),
                        kill_zone=kill_zone,
                        alert_threshold_consecutive=dbl_threshold,
                    )
            except Exception as e:
                logger.warning("d1_bias_lag logger outer guard: %s", e)

            # 2b. Log OB retest events (edge decay monitoring — before AI eval)
            try:
                m15_close = raw_data["candles"]["M15"][-1]["close"]
                self._log_ob_retest_event(mso, m15_close)
            except (KeyError, IndexError, TypeError):
                pass  # non-critical — don't block the trade pipeline

            # 2c. Dumb-momentum-baseline shadow logger (A6 follow-up).
            # Per `research/dumb_momentum_baseline/REPORT.md`: A6 found same-window
            # AI Exp +0.35R vs dumb-baseline Exp +0.36R (n=11/13) — too small to
            # claim. This logger fires hypothetical 80%-retrace pullback trades
            # alongside live trades for empirical comparison after 50-100 fills.
            # Pure observation: never gates trades, never counts toward kz_trades
            # or concurrent_tracker. Outer try wraps inner fail-open.
            try:
                cfg_dumb = (self.config.get("shadow_loggers", {}) or {}).get(
                    "dumb_baseline_logger", {}
                ) or {}
                if cfg_dumb.get("enabled", True):
                    _dumb_baseline.process_candle(
                        symbol=self._symbol,
                        raw_data=raw_data,
                        kz=kill_zone,
                        timestamp_utc=getattr(mso, "timestamp_utc", None) or datetime.now(timezone.utc).isoformat(),
                        enable_debug=bool(cfg_dumb.get("debug_log_enabled", False)),
                        look_back_h1=int(cfg_dumb.get("look_back_h1_candles", 24)),
                    )
            except Exception as e:  # noqa: BLE001 — additive logger, must never break pipeline
                logger.warning("dumb_baseline logger outer guard: %s", e)

            # 2d. Regime classifier shadow logger (Wave 1 follow-up).
            # Per CEO brief 2026-04-25: ~70-75% of XAUUSD's April collapse was
            # AI-side, and the AI is currently regime-blind. Wave 1 (A5) found
            # structural quality alone doesn't predict outcome; regime/timing
            # matters more. V1 is a pragmatic Option-A H4-swing classifier
            # (trending_bull / trending_bear / chop / reversal_in_progress /
            # unclear). Pure observation: never gates trades, never feeds the
            # AI prompt. Promotion to live filter requires >=14d shadow data
            # + comparison to realized outcomes. See
            # ``src/components/regime_classifier.py`` for the full design
            # rationale.
            try:
                cfg_regime = (self.config.get("shadow_loggers", {}) or {}).get(
                    "regime_classifier_logger", {}
                ) or {}
                if cfg_regime.get("enabled", True):
                    _regime_shadow.log_classification(
                        mso,
                        symbol=self._symbol,
                        candle_time=getattr(mso, "timestamp_utc", None)
                        or datetime.now(timezone.utc).isoformat(),
                        lookback_h4_candles=int(
                            cfg_regime.get("lookback_h4_candles", 20)
                        ),
                    )
            except Exception as e:  # noqa: BLE001 — additive logger, must never break pipeline
                logger.warning("regime_classifier logger outer guard: %s", e)

            # 3. Pre-screen
            passed, reason = prescreen_mso(mso)
            if not passed:
                logger.info("Pre-screen FAILED: %s", reason)
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="PRESCREEN_FAILED_PRE_AI",
                    prescreen_status="FAILED",
                    reason=reason,
                    kill_zone=kill_zone,
                )
                self._log_candle("NO_TRADE", f"pre_screen: {reason}", kill_zone)
                return

            # 3b. News / economic calendar check (before API call — saves tokens)
            candle_time_utc = datetime.now(timezone.utc)
            if self._news_calendar.enabled:
                blocked, cal_reason = self._news_calendar.should_skip(
                    self._symbol, candle_time_utc
                )
                if blocked:
                    logger.info("News event skip: %s", cal_reason)
                    self._record_forward_capture_evaluation_shadow(
                        mso=mso,
                        raw_data=raw_data,
                        evaluation_stage="NEWS_CALENDAR_BLOCKED_PRE_AI",
                        prescreen_status="PASSED",
                        reason=cal_reason,
                        kill_zone=kill_zone,
                    )
                    self._log_candle("SKIP_NEWS_EVENT", cal_reason, kill_zone)
                    return
            else:
                blocked, cal_reason = should_block_trading(
                    self._calendar, candle_time_utc, self._symbol, self.config
                )
                if blocked:
                    logger.info("Calendar block: %s", cal_reason)
                    self._record_forward_capture_evaluation_shadow(
                        mso=mso,
                        raw_data=raw_data,
                        evaluation_stage="ECONOMIC_CALENDAR_BLOCKED_PRE_AI",
                        prescreen_status="PASSED",
                        reason=cal_reason,
                        kill_zone=kill_zone,
                    )
                    self._log_candle("BLOCKED_CALENDAR", cal_reason, kill_zone)
                    return

            # 3c. Deterministic bias check and GTOS vNext pre-AI mechanical router.
            # vNext runs before the no_bias skip so all-side evidence can route
            # or skip the AI path when pre_ai_apply_to_ai_call is flipped.
            bias_result = self._compute_deterministic_bias(mso)
            vnext_pre_ai = self._evaluate_gtos_vnext_pre_ai(
                raw_data=raw_data,
                kill_zone=kill_zone,
                bias_result=bias_result,
            )
            structural_c_gate = self._evaluate_structural_c_gate_pre_ai(
                mso=mso,
                raw_data=raw_data,
                kill_zone=kill_zone,
                bias_result=bias_result,
            )
            if structural_c_gate.action in (
                "SKIP_AI_NO_H1_BIAS",
                "SKIP_AI_M15_OPPOSES_H1",
            ):
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="STRUCTURAL_C_GATE_PRE_AI_SKIP",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    reason=structural_c_gate.reason,
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "NO_TRADE",
                    f"structural_c_gate:{structural_c_gate.reason}",
                    kill_zone,
                )
                return
            bias_result = self._apply_structural_c_gate_pre_ai_route(
                bias_result=bias_result,
                structural_c_gate=structural_c_gate,
            )
            vnext_ai_policy = self._evaluate_gtos_vnext_ai_policy(
                raw_data=raw_data,
                kill_zone=kill_zone,
                bias_result=bias_result,
                vnext_pre_ai=vnext_pre_ai,
            )
            if (
                bias_result["bias"] == "no_bias"
                and vnext_pre_ai.action == "ALLOW_AI"
            ):
                logger.info("Deterministic bias: no_bias (D1=%s, H4=%s, H1=%s) - skipping API call",
                            bias_result['d1'], bias_result['h4'], bias_result['h1'])
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="DETERMINISTIC_NO_BIAS_PRE_AI",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    reason=(
                        f"D1={bias_result['d1']}, H4={bias_result['h4']}, "
                        f"H1={bias_result['h1']}"
                    ),
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "NO_TRADE",
                    f"deterministic_no_bias: D1={bias_result['d1']}, "
                    f"H4={bias_result['h4']}, H1={bias_result['h1']}",
                    kill_zone,
                )
                return

            if vnext_pre_ai.action == "SKIP_AI_AVOID_ONLY":
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="GTOS_VNEXT_PRE_AI_AVOID_SKIP",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    reason=vnext_pre_ai.reason,
                    kill_zone=kill_zone,
                )
                try:
                    candle_ts = (getattr(mso, "timestamp_utc", "")
                                 or datetime.now(timezone.utc).isoformat())
                    log_candidate_features(
                        pa_output=None,
                        mso=mso,
                        symbol=self._symbol,
                        timestamp_utc=str(candle_ts),
                        candle_close_utc=(
                            str(canonical_candle_close_utc)
                            if canonical_candle_close_utc
                            else None
                        ),
                        session_state={"kill_zone": kill_zone},
                        pre_ai_gate_skipped=True,
                        pre_ai_gate_reason=f"gtos_vnext:{vnext_pre_ai.reason}",
                        ai_direction_evaluated=(
                            "LONG" if bias_result.get("bias") == "bullish"
                            else "SHORT" if bias_result.get("bias") == "bearish"
                            else "UNCLEAR"
                        ),
                        pre_ai_gate_bias=bias_result.get("bias"),
                        pre_ai_gate_enabled_frameworks=(
                            self.config.get("model_a", {}).get("enabled_frameworks")
                        ),
                        pre_ai_gate_framework_poi_availability=framework_poi_availability(
                            mso, self.config, bias=bias_result.get("bias", "")
                        ),
                    )
                except Exception as e:  # noqa: BLE001
                    logger.debug("Candidate features logger (vNext pre-AI) outer guard: %s", e)
                self._log_candle(
                    "NO_TRADE",
                    f"gtos_vnext_pre_ai:{vnext_pre_ai.reason}",
                    kill_zone,
                )
                return

            # 3d. Pre-AI H1 POI availability gate — skip AI call when MSO has zero
            # unmitigated H1 OBs + zero unretested H1 breakers (mirrors L2
            # h1_poi_exists; saves API cost, never blocks a trade that L2 would pass).
            if vnext_pre_ai.action in (
                "NARROW_AI_TO_SIDE",
                "NARROW_AI_TO_ROUTE",
                "NARROW_AI_EXCLUDE_FRAMEWORKS",
            ):
                bias_result = self._apply_gtos_vnext_pre_ai_route(
                    bias_result=bias_result,
                    vnext_pre_ai=vnext_pre_ai,
                )

            poi_gate_config = self._config_for_gtos_vnext_pre_ai_gate(vnext_pre_ai=vnext_pre_ai)
            if poi_gate_config.get("pre_ai_gates", {}).get("h1_poi_availability_enabled", False):
                should_skip, skip_reason = h1_poi_availability(
                    mso, poi_gate_config, bias=bias_result.get("bias", "")
                )
                if should_skip:
                    logger.info("Pre-AI gate skip: %s", skip_reason)
                    self._record_forward_capture_evaluation_shadow(
                        mso=mso,
                        raw_data=raw_data,
                        evaluation_stage="H1_POI_PRE_AI_SKIP",
                        prescreen_status="PASSED",
                        deterministic_bias=bias_result.get("bias"),
                        reason=skip_reason,
                        kill_zone=kill_zone,
                    )
                    # Bug 5 (Thursday 2026-04-23 audit): before this fix,
                    # log_candidate_features was called only AFTER analysis
                    # was produced, so gated candles were invisible to
                    # shadow_logs/candidate_features_log.jsonl (58 Thursday
                    # gated candles missing). Log MSO features here with
                    # pa_output=None and pre_ai_gate_skipped=True so the
                    # gated-candle distribution is auditable. The logger
                    # is failure-isolated, so this never crashes the
                    # pipeline.
                    try:
                        candle_ts = (getattr(mso, "timestamp_utc", "")
                                     or datetime.now(timezone.utc).isoformat())
                        log_candidate_features(
                            pa_output=None,
                            mso=mso,
                            symbol=self._symbol,
                            timestamp_utc=str(candle_ts),
                            candle_close_utc=(
                                str(canonical_candle_close_utc)
                                if canonical_candle_close_utc
                                else None
                            ),
                            session_state={"kill_zone": kill_zone},
                            pre_ai_gate_skipped=True,
                            pre_ai_gate_reason=skip_reason,
                            ai_direction_evaluated=(
                                "LONG" if bias_result.get("bias") == "bullish"
                                else "SHORT" if bias_result.get("bias") == "bearish"
                                else "UNCLEAR"
                            ),
                            pre_ai_gate_bias=bias_result.get("bias"),
                            pre_ai_gate_enabled_frameworks=(
                                poi_gate_config.get("model_a", {}).get("enabled_frameworks")
                            ),
                            pre_ai_gate_framework_poi_availability=framework_poi_availability(
                                mso, poi_gate_config, bias=bias_result.get("bias", "")
                            ),
                        )
                    except Exception as e:  # noqa: BLE001
                        logger.debug("Candidate features logger (gated) outer guard: %s", e)
                    self._log_candle("NO_TRADE", f"pre_ai_gate:{skip_reason}", kill_zone)
                    return

            poi_proximity_gate = self._evaluate_poi_proximity_pre_ai_gate(
                mso=mso,
                raw_data=raw_data,
                bias_result=bias_result,
                poi_gate_config=poi_gate_config,
            )
            if poi_proximity_gate.get("skipped"):
                skip_reason = str(poi_proximity_gate.get("reason") or "poi_proximity_skip")
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="POI_PROXIMITY_PRE_AI_SKIP",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    reason=skip_reason,
                    kill_zone=kill_zone,
                )
                try:
                    candle_ts = (getattr(mso, "timestamp_utc", "")
                                 or datetime.now(timezone.utc).isoformat())
                    log_candidate_features(
                        pa_output=None,
                        mso=mso,
                        symbol=self._symbol,
                        timestamp_utc=str(candle_ts),
                        candle_close_utc=(
                            str(canonical_candle_close_utc)
                            if canonical_candle_close_utc
                            else None
                        ),
                        session_state={"kill_zone": kill_zone},
                        pre_ai_gate_skipped=True,
                        pre_ai_gate_reason=f"poi_proximity:{skip_reason}",
                        ai_direction_evaluated=(
                            "LONG" if bias_result.get("bias") == "bullish"
                            else "SHORT" if bias_result.get("bias") == "bearish"
                            else "UNCLEAR"
                        ),
                        pre_ai_gate_bias=bias_result.get("bias"),
                        pre_ai_gate_enabled_frameworks=(
                            poi_gate_config.get("model_a", {}).get("enabled_frameworks")
                        ),
                        pre_ai_gate_framework_poi_availability=framework_poi_availability(
                            mso, poi_gate_config, bias=bias_result.get("bias", "")
                        ),
                    )
                except Exception as e:  # noqa: BLE001
                    logger.debug("Candidate features logger (POI proximity) outer guard: %s", e)
                self._log_candle("NO_TRADE", f"poi_proximity:{skip_reason}", kill_zone)
                return

            if not vnext_ai_policy.allowed:
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="GTOS_VNEXT_AI_POLICY_SKIP_PRE_AI",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    reason=vnext_ai_policy.reason,
                    kill_zone=kill_zone,
                )
                try:
                    candle_ts = (getattr(mso, "timestamp_utc", "")
                                 or datetime.now(timezone.utc).isoformat())
                    log_candidate_features(
                        pa_output=None,
                        mso=mso,
                        symbol=self._symbol,
                        timestamp_utc=str(candle_ts),
                        candle_close_utc=(
                            str(canonical_candle_close_utc)
                            if canonical_candle_close_utc
                            else None
                        ),
                        session_state={"kill_zone": kill_zone},
                        pre_ai_gate_skipped=True,
                        pre_ai_gate_reason=f"gtos_vnext_ai_policy:{vnext_ai_policy.reason}",
                        ai_direction_evaluated=(
                            "LONG" if bias_result.get("bias") == "bullish"
                            else "SHORT" if bias_result.get("bias") == "bearish"
                            else "UNCLEAR"
                        ),
                        pre_ai_gate_bias=bias_result.get("bias"),
                        pre_ai_gate_enabled_frameworks=(
                            poi_gate_config.get("model_a", {}).get("enabled_frameworks")
                        ),
                        pre_ai_gate_framework_poi_availability=framework_poi_availability(
                            mso, poi_gate_config, bias=bias_result.get("bias", "")
                        ),
                    )
                except Exception as e:  # noqa: BLE001
                    logger.debug("Candidate features logger (vNext AI policy) outer guard: %s", e)
                self._log_candle(
                    "NO_TRADE",
                    f"gtos_vnext_ai_policy:{vnext_ai_policy.reason}",
                    kill_zone,
                )
                return

            # 3e. AI call policy. Production trade decisions are allowed; broad
            # historical market-edge replay must stay no-API unless the current
            # context carries an explicit AI-layer purpose, manifest, budget,
            # approval, and cache identity.
            ai_call_policy = self._evaluate_ai_call_policy(
                raw_data=raw_data,
                kill_zone=kill_zone,
                bias_result=bias_result,
                vnext_pre_ai=vnext_pre_ai,
                vnext_ai_policy=vnext_ai_policy,
            )
            if not ai_call_policy.allowed:
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="AI_CALL_POLICY_SKIP_PRE_AI",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    reason=ai_call_policy.reason,
                    kill_zone=kill_zone,
                )
                try:
                    candle_ts = (getattr(mso, "timestamp_utc", "")
                                 or datetime.now(timezone.utc).isoformat())
                    log_candidate_features(
                        pa_output=None,
                        mso=mso,
                        symbol=self._symbol,
                        timestamp_utc=str(candle_ts),
                        candle_close_utc=(
                            str(canonical_candle_close_utc)
                            if canonical_candle_close_utc
                            else None
                        ),
                        session_state={"kill_zone": kill_zone},
                        pre_ai_gate_skipped=True,
                        pre_ai_gate_reason=f"ai_call_policy:{ai_call_policy.reason}",
                        ai_direction_evaluated=(
                            "LONG" if bias_result.get("bias") == "bullish"
                            else "SHORT" if bias_result.get("bias") == "bearish"
                            else "UNCLEAR"
                        ),
                        pre_ai_gate_bias=bias_result.get("bias"),
                        pre_ai_gate_enabled_frameworks=(
                            poi_gate_config.get("model_a", {}).get("enabled_frameworks")
                        ),
                        pre_ai_gate_framework_poi_availability=framework_poi_availability(
                            mso, poi_gate_config, bias=bias_result.get("bias", "")
                        ),
                    )
                except Exception as e:  # noqa: BLE001
                    logger.debug("Candidate features logger (AI call policy) outer guard: %s", e)
                self._log_candle(
                    "NO_TRADE",
                    f"ai_call_policy:{ai_call_policy.reason}",
                    kill_zone,
                )
                return

            # 4. Session memory context (disabled via config if session_memory_enabled=false)
            if self.config.get("session_memory_enabled", True):
                memory_block = self._format_session_memory()
            else:
                memory_block = ""

            # 4b. Compute timeframe alignment context + instrument expertise
            align_context = self._compute_align_context(mso, bias_result=bias_result)
            vnext_ai_role_context = self._format_gtos_vnext_ai_role_context(
                vnext_pre_ai=vnext_pre_ai,
                vnext_ai_policy=vnext_ai_policy,
            )
            if vnext_ai_role_context:
                align_context = "\n\n".join(
                    part for part in (align_context, vnext_ai_role_context) if part
                )
            logger.debug("additional_context [%d chars]: %.100s...",
                         len(align_context), align_context)

            # 5. Run Primary Analyzer (async)
            try:
                frameworks_override = self._frameworks_override_for_gtos_vnext_ai(
                    vnext_pre_ai=vnext_pre_ai
                )
                analysis = asyncio.get_event_loop().run_until_complete(
                    self.analyzer.analyze(
                        market_state=mso,
                        kill_zone=kill_zone,
                        session_memory=memory_block,
                        cross_instrument_context=self._ci_context_text,
                        additional_context=align_context,
                        frameworks_override=frameworks_override,
                        ai_call_context=ai_call_policy.context,
                    )
                )
            except Exception as e:
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="AI_ANALYZER_ERROR_AFTER_PRE_AI_ANCHOR",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    ai_status="ERROR_OR_EXCEPTION",
                    ai_dependency="PRE_AI_ROW_ALREADY_WRITTEN",
                    reason=str(e),
                    kill_zone=kill_zone,
                )
                raise

            # 5-shadow. Candidate features shadow logger (R2 meta-learning
            # training-set accumulator — observation-only, never gates trades).
            # Captures MSO features + AI output for every evaluation (CANDIDATE
            # AND NO_TRADE). Failure-isolated inside log_candidate_features.
            try:
                candle_ts = getattr(mso, "timestamp_utc", "") or datetime.now(timezone.utc).isoformat()
                log_candidate_features(
                    pa_output=analysis,
                    mso=mso,
                    symbol=self._symbol,
                    timestamp_utc=str(candle_ts),
                    candle_close_utc=(
                        str(canonical_candle_close_utc)
                        if canonical_candle_close_utc
                        else None
                    ),
                    session_state={"kill_zone": kill_zone},
                )
            except Exception as e:
                logger.debug("Candidate features logger outer guard: %s", e)

            route_mismatch = self._gtos_vnext_ai_route_mismatch(
                analysis=analysis,
                vnext_pre_ai=vnext_pre_ai,
            )
            if route_mismatch:
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage="GTOS_VNEXT_AI_ROUTE_MISMATCH",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    ai_status="COMPLETED_ROUTE_MISMATCH",
                    ai_dependency="GTOS_VNEXT_PRE_AI_ROUTE_ENFORCED",
                    reason=route_mismatch,
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "NO_TRADE",
                    f"gtos_vnext_route_mismatch:{route_mismatch}",
                    kill_zone,
                )
                return

            # 5b-shadow. A.2 direction-emission audit logger. Per-CANDIDATE
            # only (silent on NO_TRADE / WAIT) — captures the proposed
            # direction relative to XAUUSD's D1 directional bias and the
            # candidate instrument's static Pearson correlation to XAU.
            # Goal: 30+ days of live data to validate (or refute) the
            # per-class agent's class-bias finding (UK100 100% LONG, GER40
            # 95% LONG, XAGUSD 17% SHORT in BT). Pure observation: never
            # gates trades. ``log_direction_emission`` is failure-isolated
            # AND a no-op for non-CANDIDATE outputs, so the outer guard is
            # belt-and-suspenders only. Reads ``_xau_d1_direction_value``
            # cached by ``_compute_cross_instrument_context`` at KZ entry —
            # for symbols on ``cross_instrument_context_disabled_for`` (e.g.
            # GBPUSD), that cache holds ``"disabled"`` and the row records
            # the sentinel without crashing.
            try:
                cfg_dir = (self.config.get("shadow_loggers", {}) or {}).get(
                    "direction_emission_logger", {}
                ) or {}
                if cfg_dir.get("enabled", True):
                    candle_ts_dir = (
                        getattr(mso, "timestamp_utc", "")
                        or datetime.now(timezone.utc).isoformat()
                    )
                    _direction_emission.log_direction_emission(
                        analysis,
                        instrument=self._symbol,
                        xau_d1_direction=self._xau_d1_direction_value,
                        mso=mso,
                        session_state={"kill_zone": kill_zone},
                        candle_time_utc=str(candle_ts_dir),
                    )
            except Exception as e:  # noqa: BLE001 — additive logger, must never break pipeline
                logger.warning("direction_emission_logger outer guard: %s", e)

            # 6. Update session memory (skip if disabled — no point accumulating unused entries)
            if self.config.get("session_memory_enabled", True):
                self._update_session_memory(analysis, kill_zone)

            # 6-shadow. Structured evaluation logging (every candle, non-blocking)
            # HALLUC-2 (2026-04-27): forward analyzer token usage so the JSONL
            # carries a per-evaluation ``usage`` block. ``_last_usage`` is reset
            # at the start of each ``analyze()`` call and accumulates across
            # retries (primary_analyzer.py:279). Reading is failure-isolated:
            # missing attribute, subscription mode without real tokens, or any
            # serialisation issue degrades cleanly to the pre-HALLUC-2 schema.
            try:
                align_score_int = self._extract_align_score(align_context)
                current_spread = self._get_current_spread()
                candle_time_str = getattr(mso, "timestamp_utc", "") or ""
                analyzer_usage = getattr(self.analyzer, "_last_usage", None)
                self.eval_logger.log_evaluation(
                    symbol=self._symbol,
                    candle_time=str(candle_time_str),
                    kill_zone=kill_zone,
                    analysis_dict=analysis.model_dump(mode="json"),
                    session_memory_count=len(self.session_memory),
                    align_score=align_score_int,
                    spread=current_spread,
                    usage=analyzer_usage,
                )
            except Exception as e:
                logger.debug("Eval logger failed (non-blocking): %s", e)

            if analysis.decision != "CANDIDATE":
                detail = analysis.no_trade_reason or ""
                if analysis.decision == "WAIT":
                    detail = getattr(analysis, "wait_reason", "") or ""
                self._record_forward_capture_evaluation_shadow(
                    mso=mso,
                    raw_data=raw_data,
                    evaluation_stage=f"AI_COMPLETED_{analysis.decision}",
                    prescreen_status="PASSED",
                    deterministic_bias=bias_result.get("bias"),
                    ai_status="COMPLETED_NO_CANDIDATE",
                    ai_dependency="AI_STATUS_ONLY_ROW_PRE_AI_ANCHOR_EXISTS",
                    reason=detail,
                    kill_zone=kill_zone,
                )
                self._log_candle(analysis.decision, detail, kill_zone)
                candle_t = getattr(mso, "timestamp_utc", "") or ""
                self._write_no_trade_record(
                    reason=detail,
                    kill_zone=kill_zone,
                    candle_time=str(candle_t),
                    analysis_dict=analysis.model_dump(mode="json"),
                )
                return

            notify_candidate(
                symbol=self._symbol,
                direction=analysis.trade_parameters.direction if analysis.trade_parameters else "?",
                grade="CANDIDATE", kill_zone=kill_zone,
            )

            # --- TRADE CAPTURE: Create record for every CANDIDATE ---
            tc_cfg = self.config.get("trade_capture", {})
            tc_enabled = tc_cfg.get("enabled", True)
            record = None
            if tc_enabled:
                try:
                    candle_time = getattr(mso, "timestamp_utc", datetime.now(timezone.utc).isoformat())
                    record = create_trade_record(
                        symbol=self._symbol,
                        kill_zone=kill_zone,
                        candle_time=candle_time,
                        mso=mso,
                        prompt_system=self.analyzer.last_system_prompt,
                        prompt_user=self.analyzer.last_user_message,
                        ai_response=analysis.model_dump(mode="json"),
                        cross_instrument_context=self._ci_context_text,
                        session_memory=memory_block,
                        config=self.config,
                    )
                    if raw_data.get("candle_close_utc"):
                        record.setdefault("metadata", {})["candle_close_utc"] = raw_data.get(
                            "candle_close_utc"
                        )
                        record.setdefault("metadata", {})[
                            "wall_clock_timestamp_utc"
                        ] = getattr(mso, "timestamp_utc", None)
                    attach_vnext_pre_ai_to_record(record, vnext_pre_ai)
                    attach_vnext_ai_policy_to_record(record, vnext_ai_policy)
                    if raw_data.get("structural_c_gate_decision"):
                        record.setdefault("decision_pipeline", {})[
                            "structural_c_gate"
                        ] = raw_data.get("structural_c_gate_decision")
                    attach_ai_call_policy_to_record(record, ai_call_policy)
                except Exception as e:
                    logger.error("Trade capture: failed to create record: %s", e)

            # Enrich trade record with shadow data fields
            if record:
                try:
                    tp = analysis.trade_parameters
                    h1_setup = analysis.reasoning.h1_setup
                    record["shadow_data"] = {
                        "session_memory_count": len(self.session_memory),
                        "align_score": self._extract_align_score(align_context),
                        "spread_at_entry": self._get_current_spread(),
                        "candle_index_in_kz": self.eval_logger._candle_index_in_kz,
                        "h1_poi_type": h1_setup.poi_type if h1_setup else None,
                        "h1_fib_pct": h1_setup.fib_retracement_pct if h1_setup else None,
                        "h1_causing_event": h1_setup.causing_event_type if h1_setup else None,
                        "h1_zone": h1_setup.zone if h1_setup else None,
                        "sweep_detected": analysis.reasoning.liquidity_sweep.detected,
                        "sweep_type": analysis.reasoning.liquidity_sweep.pool_type,
                        "m15_displacement_quality": analysis.reasoning.m15_confirmation.displacement_quality,
                        "m15_displacement_ratio": analysis.reasoning.m15_confirmation.displacement_candle_body_vs_avg_ratio,
                    }
                except Exception as e:
                    logger.debug("Shadow data enrichment failed: %s", e)

            # 6-shadow-proximity. Zone proximity at evaluation time (non-blocking)
            try:
                mso_text = self.analyzer.last_user_message or ""
                trade_dir = analysis.trade_parameters.direction if analysis.trade_parameters else "LONG"
                prox_data = compute_trade_proximity(mso_text, trade_dir)
                if record:
                    record.setdefault("shadow", {})["proximity"] = prox_data
                candle_t = getattr(mso, "timestamp_utc", "") or ""
                write_proximity_shadow_log(
                    trade_id=record.get("trade_id", "unknown") if record else "unknown",
                    symbol=self._symbol,
                    kill_zone=kill_zone,
                    candle_time=str(candle_t),
                    trade_direction=trade_dir,
                    proximity_data=prox_data,
                )
            except Exception as e:
                logger.debug("Proximity shadow logging failed (non-blocking): %s", e)

            # 6-shadow-DA. Devil's Advocate risk assessment (truly non-blocking)
            import threading

            def _shadow_da_background(rec, da_inst, mso_text, reasoning, params):
                try:
                    result = da_inst.evaluate(
                        mso_text=mso_text,
                        pa_reasoning=reasoning,
                        trade_params=params,
                    )
                    if result and not result.get("error"):
                        logger.info("Shadow DA: max_risk=%s%%", result.get("max_risk_pct", "?"))
                    if rec is not None and result:
                        rec["shadow_da"] = result
                except Exception as e:
                    logger.warning("Shadow DA failed (background): %s", e)

            try:
                reasoning_dict = analysis.model_dump(mode="json").get("reasoning", {})
                da_thread = threading.Thread(
                    target=_shadow_da_background,
                    args=(
                        record,
                        self.devils_advocate,
                        self.analyzer.last_user_message[:8000] if self.analyzer.last_user_message else "",
                        reasoning_dict.get("overall_reasoning", ""),
                        analysis.model_dump(mode="json").get("trade_parameters") or {},
                    ),
                    daemon=True,
                )
                da_thread.start()
            except Exception as e:
                logger.warning("Shadow DA thread launch failed: %s", e)

            # 6a. Level 2 verification — check AI claims against MSO
            verification = verify_candidate(analysis, mso, self.config)
            if record:
                try:
                    update_verification(record, verification)
                except Exception as e:
                    logger.error("Trade capture: failed to update verification: %s", e)

            if not verification.passed:
                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = "REJECTED_L2"
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome="REJECTED_L2",
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "REJECTED_L2",
                    f"{verification.blocked_by}: "
                    + next(c.detail for c in verification.checks if c.status == "FAIL"),
                    kill_zone,
                    produced_candidate=True,
                )
                return

            # 6a.1. GTOS vNext runtime decision surface. This consumes the
            # verified vNext review/registry evidence from current event fields
            # and attaches FOLLOW/AVOID/MIXED/LEGACY evidence to the runtime
            # trade record. ``apply_to_execution=false`` keeps it non-blocking;
            # flipping that config makes AVOID/MIXED handling executable here.
            vnext_decision = self._evaluate_gtos_vnext_runtime(
                analysis=analysis,
                raw_data=raw_data,
                kill_zone=kill_zone,
                record=record,
            )
            probability_debate_v4 = self._evaluate_probability_debate_team_v4(
                analysis=analysis,
                raw_data=raw_data,
                kill_zone=kill_zone,
                record=record,
                vnext_decision=vnext_decision,
            )
            probability_debate_block_reason = (
                probability_debate_v4_execution_block_reason(
                    probability_debate_v4,
                    self.config,
                )
                if probability_debate_v4 is not None else None
            )
            if probability_debate_block_reason:
                final_outcome = "SKIPPED_PROBABILITY_DEBATE_V4"
                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = final_outcome
                    record["decision_pipeline"][
                        "probability_debate_v4_block_reason"
                    ] = probability_debate_block_reason
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome=final_outcome,
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    final_outcome,
                    probability_debate_block_reason,
                    kill_zone,
                    produced_candidate=True,
                )
                return
            vnext_block_reason = vnext_execution_block_reason(vnext_decision, self.config)
            if vnext_block_reason:
                self._record_gtos_vnext_replacement_monitoring(
                    phase="post_l2_replacement_block",
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    record=record,
                    vnext_pre_ai=vnext_pre_ai,
                    vnext_ai_policy=vnext_ai_policy,
                    vnext_decision=vnext_decision,
                )
                if vnext_block_reason.startswith("vnext_risk_"):
                    self._attach_gtos_vnext_block_risk_preview(
                        vnext_decision=vnext_decision,
                        record=record,
                    )
                outcome_label = (
                    "REJECTED_GTOS_VNEXT_RISK"
                    if vnext_block_reason.startswith("vnext_risk_")
                    else f"REJECTED_GTOS_VNEXT_{vnext_decision.decision}"
                )
                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = outcome_label
                    record["decision_pipeline"]["gtos_vnext_block_reason"] = vnext_block_reason
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome=outcome_label,
                    kill_zone=kill_zone,
                )
                evidence = vnext_decision.evidence or {}
                self._log_candle(
                    outcome_label,
                    (
                        f"vnext_decision={vnext_decision.decision} "
                        f"matched_rows={evidence.get('matched_rows', 0)} "
                        f"block_reason={vnext_block_reason} "
                        f"reason={vnext_decision.reason}"
                    ),
                    kill_zone,
                    produced_candidate=True,
                )
                return

            # 6b. Confidence scoring (shadow or active mode)
            conf_metrics = score_confidence(analysis.model_dump())
            conf_filter_mode = resolve_confidence_filter_mode(self.config)
            conf_mode = conf_filter_mode.effective_mode
            if conf_filter_mode.blocked_reason:
                logger.warning(
                    "Confidence filter mode %s blocked (%s); using %s",
                    conf_filter_mode.requested_mode,
                    conf_filter_mode.blocked_reason,
                    conf_mode,
                )
            logger.info(
                "Confidence: grade=%s price_levels=%d hesitation=%d multiplier=%.2f (mode=%s)",
                conf_metrics.confidence_grade,
                conf_metrics.price_level_count,
                conf_metrics.hesitation_score,
                conf_metrics.position_size_multiplier,
                conf_mode,
            )
            vnext_confidence_override = evaluate_vnext_confidence_override(
                decision=vnext_decision,
                confidence_grade=conf_metrics.confidence_grade,
                config=self.config,
            )
            if record:
                attach_vnext_confidence_override_to_record(record, vnext_confidence_override)
            logger.info(
                "GTOS_VNEXT_CONFIDENCE_OVERRIDE grade=%s decision=%s applied=%s "
                "would_apply=%s reason=%s",
                conf_metrics.confidence_grade,
                vnext_confidence_override.decision,
                vnext_confidence_override.applied,
                vnext_confidence_override.would_apply,
                vnext_confidence_override.reason,
            )
            if conf_mode == "active" and conf_metrics.confidence_grade == "LOW":
                if vnext_confidence_override.applied:
                    logger.info(
                        "GTOS_VNEXT_CONFIDENCE_OVERRIDE: active LOW confidence gate "
                        "bypassed by strong FOLLOW evidence"
                    )
                else:
                    if record:
                        record["decision_pipeline"]["final_outcome"] = "SKIPPED_LOW_CONFIDENCE"
                    self._record_forward_capture_candidate_shadow(
                        analysis=analysis,
                        mso=mso,
                        record=record,
                        verification=verification,
                        final_outcome="SKIPPED_LOW_CONFIDENCE",
                        kill_zone=kill_zone,
                    )
                    self._log_candle(
                        "SKIPPED_LOW_CONFIDENCE",
                        f"grade={conf_metrics.confidence_grade} "
                        f"prices={conf_metrics.price_level_count} "
                        f"hesitation={conf_metrics.hesitation_score} "
                        f"vnext_override={vnext_confidence_override.reason}",
                        kill_zone,
                        produced_candidate=True,
                    )
                    return

            # 6c. M5 Entry Refinement (before safety check)
            m5_cfg = self.config.get("m5_refinement", {})
            m5_cfg["_full_config"] = self.config  # pass full config for prompt parameterization
            if m5_cfg.get("enabled", False):
                m5_candles = self._pull_m5_candles()
                # Inject M15 ATR into trade_parameters for floor calculation
                m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
                if m15_tf and analysis.trade_parameters:
                    analysis.trade_parameters._m15_atr = getattr(m15_tf, "atr_14", 0) or 0
                m5_out = refine_entry_m5(analysis, m5_candles, m5_cfg, self.llm_backend, mso=mso)
                # A3: snapshot M5 outcome into trade record instrumentation block
                # (regardless of applied/skipped — Phase-2 queries need both).
                if record:
                    try:
                        update_m5_refinement(record, m5_out)
                    except Exception as e:
                        logger.error("Trade capture: failed to update m5 refinement: %s", e)
                if m5_out["applied"]:
                    apply_m5_overrides(analysis, m5_out["overrides"])
                    logger.info(
                        "M5 refined: quality=%s SL=$%.5f->$%.5f TP=$%.5f",
                        m5_out["overrides"].get("m5_quality"),
                        m5_out["overrides"].get("m5_raw_sl_dist", 0),
                        m5_out["overrides"]["sl_distance"],
                        m5_out["overrides"]["take_profit_1"],
                    )
                    # Re-verify L2 Check 6 (sl_beyond_ob) with M5-refined SL
                    re_verify = verify_candidate(analysis, mso, self.config)
                    sl_check = next((c for c in re_verify.checks if c.name == "sl_beyond_ob"), None)
                    if sl_check and sl_check.status == "FAIL":
                        if record and tc_cfg.get("save_rejected", True):
                            record["decision_pipeline"]["final_outcome"] = "REJECTED_L2_POST_M5"
                            save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                        self._record_forward_capture_candidate_shadow(
                            analysis=analysis,
                            mso=mso,
                            record=record,
                            verification=re_verify,
                            final_outcome="REJECTED_L2_POST_M5",
                            kill_zone=kill_zone,
                        )
                        self._log_candle("REJECTED_L2_POST_M5",
                                         f"M5 refined SL fails sl_beyond_ob: {sl_check.detail}",
                                         kill_zone,
                                         produced_candidate=True)
                        return
                else:
                    logger.info("M5: %s - using M15 SL/TP.",
                                m5_out["m5_result"].get("decision", "N/A"))
                # Persist M5 result
                m5_log_path = Path("pipeline_state/m5_refinement.json")
                m5_log_path.parent.mkdir(parents=True, exist_ok=True)
                atomic_write(m5_log_path, json.dumps(m5_out, indent=2, default=str))

            # 6d. Calendar safety net (event may have entered window during AI eval)
            if self._news_calendar.enabled:
                blocked, cal_reason = self._news_calendar.should_skip(
                    self._symbol, datetime.now(timezone.utc)
                )
                outcome_label = "SKIP_NEWS_EVENT"
            else:
                blocked, cal_reason = should_block_trading(
                    self._calendar, datetime.now(timezone.utc), self._symbol, self.config
                )
                outcome_label = "BLOCKED_CALENDAR"
            if blocked:
                if record:
                    record["decision_pipeline"]["final_outcome"] = outcome_label
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome=outcome_label,
                    kill_zone=kill_zone,
                )
                self._log_candle(outcome_label, f"safety_net: {cal_reason}", kill_zone,
                                 produced_candidate=True)
                return

            # 7. Permission check
            self.session_state["current_kill_zone"] = kill_zone
            self.session_state["deterministic_bias"] = bias_result.get("bias", "no_bias")
            denial = check_permissions(analysis, mso, self.session_state, self.mt5,
                                        config=self.config, symbol=self._mt5_symbol)

            # --- TRADE CAPTURE: Gate results ---
            if record:
                try:
                    g3 = build_gate3_result(denial, self.session_state, self.mt5,
                                            symbol=self._mt5_symbol)
                    g1 = build_gate1_result(denial, analysis, mso)
                    update_gate_results(record, g3, g1)
                except Exception as e:
                    logger.error("Trade capture: failed to update gate results: %s", e)

            if denial:
                denial_outcome = _permission_denial_runtime_outcome(denial)
                if record and tc_cfg.get("save_rejected", True):
                    _attach_permission_denial_outcome_to_record(
                        record,
                        denial,
                        denial_outcome,
                    )
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome=denial_outcome["final_outcome"],
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    denial_outcome["candle_decision"],
                    denial_outcome["candle_detail"],
                    kill_zone,
                    produced_candidate=True,
                )
                return

            # 7b. H29 drawdown-based risk reduction (before correlation sizing)
            equity = self.mt5.get_account_equity()
            base_risk_pct = self._drawdown_mgr.get_risk_pct(equity)
            dd_pct = self._drawdown_mgr.get_drawdown_pct(equity)
            if self._drawdown_mgr.is_reduced:
                logger.info("H29_DRAWDOWN_REDUCTION: risk=%.1f%% (equity=$%.2f, "
                            "peak=$%.2f, dd=%.2f%%)",
                            base_risk_pct, equity,
                            self._drawdown_mgr.equity_peak, dd_pct * 100)

            autocorr_risk = self._apply_autocorrelation_risk_sizing(
                current_risk_pct=base_risk_pct,
                raw_data=raw_data,
                record=record,
            )
            base_risk_pct = autocorr_risk.after_risk_pct

            # 7c. Correlation-aware position sizing
            open_positions = self._get_open_positions_for_correlation()
            corr_adj = check_correlation_risk(
                symbol=self._symbol,
                base_risk_pct=base_risk_pct,
                open_positions=open_positions,
                config=self.config,
            )
            effective_risk_pct = corr_adj.final_risk_pct
            if corr_adj.adjusted:
                if effective_risk_pct <= 0:
                    if record:
                        record["decision_pipeline"]["final_outcome"] = "SKIPPED_CORRELATION"
                        save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                    self._record_forward_capture_candidate_shadow(
                        analysis=analysis,
                        mso=mso,
                        record=record,
                        verification=verification,
                        final_outcome="SKIPPED_CORRELATION",
                        kill_zone=kill_zone,
                    )
                    self._log_candle("SKIPPED_CORRELATION", corr_adj.reason, kill_zone,
                                     produced_candidate=True)
                    return
                logger.info("RISK_REDUCED_CORRELATION: %s %.1f%% -> %.1f%% (%s)",
                            self._symbol, base_risk_pct, effective_risk_pct, corr_adj.reason)

            # 7d. Cross-instrument correlation cluster (additive sizing
            # reduction layered ON TOP of group-scoped check_correlation_risk).
            # The REJECT path is owned by Gate 3.5 in permissions.py — by the
            # time we get here, that path has already returned. This block is
            # ONLY responsible for the HALVE outcome.
            cross_corr_adj = _evaluate_cross_instrument_correlation(
                candidate_symbol=self._symbol,
                candidate_direction=analysis.trade_parameters.direction,
                mt5=self.mt5,
                config=self.config,
                evaluation_context="orchestrator_sizing_risk_adjustment",
            )
            if cross_corr_adj.action == "RISK_REDUCE_HALF":
                pre_halve = effective_risk_pct
                effective_risk_pct = _apply_cross_instrument_risk_multiplier(
                    effective_risk_pct, cross_corr_adj,
                )
                logger.warning(
                    "CROSS_INSTRUMENT_CORR_HALVE applied: %s %s %.3f%% -> %.3f%% "
                    "(cluster=%d positions, threshold=%.2f) %s",
                    self._symbol, analysis.trade_parameters.direction,
                    pre_halve, effective_risk_pct,
                    len(cross_corr_adj.correlated_positions),
                    cross_corr_adj.threshold,
                    [(p["symbol"], p["direction"], round(p["correlation"], 3))
                     for p in cross_corr_adj.correlated_positions],
                )

            # 7e. Contextual side-aware sizing. The old global LONG=0.5x /
            # SHORT=1.0x rule is now only the legacy fallback. In contextual
            # mode, both sides earn full risk only when the candidate's
            # symbol/session/framework/regime/H1/vNext/no-fill/path evidence
            # supports it. The SPRT watcher still auto-disables the path.
            side_aware_was_applied = False
            if _side_aware.is_enabled(self.config):
                try:
                    sprt_watcher = SideAwareSprtWatcher(self.config)
                    if not sprt_watcher.is_disabled():
                        side_decision = self._apply_contextual_side_risk_sizing(
                            current_risk_pct=effective_risk_pct,
                            analysis=analysis,
                            raw_data=raw_data,
                            kill_zone=kill_zone,
                            vnext_decision=vnext_decision,
                            autocorr_risk=autocorr_risk,
                            record=record,
                        )
                        effective_risk_pct = side_decision.after_risk_pct
                        side_aware_was_applied = side_decision.applied
                    else:
                        logger.warning(
                            "Side-aware sizing AUTO-DISABLED (SPRT WR<threshold); "
                            "using base %.2f%%",
                            effective_risk_pct,
                        )
                except Exception as e:
                    logger.warning(
                        "side_aware sizing path failed (non-blocking, base risk "
                        "preserved): %s",
                        e,
                    )

            # 7f. GTOS vNext evidence-backed sizing. This composes after the
            # established drawdown/correlation/side-aware adjustments and uses
            # the post-L2 vNext R/proxy/stress/effective-N evidence already
            # attached to the trade record. Current config keeps execution
            # effect off; flipping apply_to_execution activates the multiplier.
            vnext_risk_adjustment = self._apply_gtos_vnext_risk_adjustment(
                current_risk_pct=effective_risk_pct,
                vnext_decision=vnext_decision,
                record=record,
            )
            if vnext_risk_adjustment.applied:
                effective_risk_pct = vnext_risk_adjustment.after_risk_pct
                if effective_risk_pct <= 0:
                    if record and tc_cfg.get("save_rejected", True):
                        record["decision_pipeline"]["final_outcome"] = "SKIPPED_GTOS_VNEXT_RISK"
                        save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                    self._record_forward_capture_candidate_shadow(
                        analysis=analysis,
                        mso=mso,
                        record=record,
                        verification=verification,
                        final_outcome="SKIPPED_GTOS_VNEXT_RISK",
                        kill_zone=kill_zone,
                    )
                    self._log_candle(
                        "SKIPPED_GTOS_VNEXT_RISK",
                        vnext_risk_adjustment.reason,
                        kill_zone,
                        produced_candidate=True,
                    )
                    return

            # 7g. GTOS vNext no-fill/entry policy. This consumes matched
            # no-fill source-component evidence before creating a candle-polled
            # pending limit. Current config records the would-action only;
            # flipping apply_to_execution allows no-fill avoid evidence to skip
            # the pending limit or near-miss market-entry evidence to use the
            # immediate market order path.
            vnext_pending_policy = evaluate_vnext_pending_policy(
                decision=vnext_decision,
                config=self.config,
            )
            if record:
                attach_vnext_pending_policy_to_record(record, vnext_pending_policy)
            logger.info(
                "GTOS_VNEXT_PENDING_POLICY action=%s would_action=%s applied=%s reason=%s",
                vnext_pending_policy.action,
                vnext_pending_policy.would_action,
                vnext_pending_policy.applied,
                vnext_pending_policy.reason,
            )
            if (
                vnext_pending_policy.applied
                and vnext_pending_policy.action == "SKIP_PENDING_NOFILL_AVOID"
            ):
                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = "SKIPPED_GTOS_VNEXT_NOFILL"
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome="SKIPPED_GTOS_VNEXT_NOFILL",
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "SKIPPED_GTOS_VNEXT_NOFILL",
                    vnext_pending_policy.reason,
                    kill_zone,
                    produced_candidate=True,
                )
                return

            # 7h. Replay-backed LTF path execution engine. This is distinct
            # from the prop selector: it controls entry timing/placement and
            # pending monitoring from as-of M1/M5/tick-compatible state, while
            # remaining activation-gated by config.
            tp = analysis.trade_parameters
            ltf_path_state = self._build_gtos_vnext_ltf_path_state(
                trade_params=tp,
                raw_data=raw_data,
                kill_zone=kill_zone,
            )
            vnext_ltf_path_execution = evaluate_vnext_ltf_path_execution(
                decision=vnext_decision,
                config=self.config,
                trade_params={
                    "direction": tp.direction,
                    "entry_price": tp.entry_price,
                    "stop_loss": tp.stop_loss,
                    "take_profit_1": tp.take_profit_1,
                },
                path_state=ltf_path_state,
            )
            if record:
                attach_vnext_ltf_path_execution_to_record(record, vnext_ltf_path_execution)
            logger.info(
                "GTOS_VNEXT_LTF_PATH action=%s would_action=%s applied=%s "
                "tf=%s adjusted_entry=%s reason=%s",
                vnext_ltf_path_execution.action,
                vnext_ltf_path_execution.would_action,
                vnext_ltf_path_execution.applied,
                vnext_ltf_path_execution.monitor_timeframe,
                vnext_ltf_path_execution.adjusted_entry_price,
                vnext_ltf_path_execution.reason,
            )
            if (
                vnext_ltf_path_execution.applied
                and vnext_ltf_path_execution.action == "SKIP_LTF_NOFILL_AVOID"
            ):
                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = "SKIPPED_GTOS_VNEXT_LTF_PATH"
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome="SKIPPED_GTOS_VNEXT_LTF_PATH",
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "SKIPPED_GTOS_VNEXT_LTF_PATH",
                    vnext_ltf_path_execution.reason,
                    kill_zone,
                    produced_candidate=True,
                )
                return
            vnext_execution_entry_price = tp.entry_price
            if (
                vnext_ltf_path_execution.applied
                and vnext_ltf_path_execution.action == "ADJUST_LIMIT_ENTRY"
                and vnext_ltf_path_execution.adjusted_entry_price is not None
            ):
                vnext_execution_entry_price = vnext_ltf_path_execution.adjusted_entry_price

            # 7i. redacted_account-style prop-safe budget governance. This is not a
            # blanket trade suppressor: it projects current equity against the
            # reset-window daily floor and static initial-balance max-loss
            # floor, then allows full size, reduces size, defers to reset, or
            # blocks only when projected budget breach risk exists.
            balance = self.mt5.get_account_balance()
            pending_intent = getattr(self.execution, "pending_intent", None)
            risk_base_amount = balance or equity
            open_position_exposure = self._open_position_risk_exposure_summary(
                open_positions,
                risk_base_amount,
            )
            pending_order_risk_pct = float(getattr(pending_intent, "risk_pct", 0.0) or 0.0)
            pending_order_risk_amount = (
                float(risk_base_amount or 0.0) * pending_order_risk_pct / 100.0
            )
            correlated_buffer_pct = sum(
                float(position.get("risk_pct", 0.0) or 0.0)
                for position in getattr(cross_corr_adj, "correlated_positions", []) or []
            )
            session_trade_count = int(self.session_state.get(f"trades_{kill_zone}", 0) or 0)
            runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
            vnext_prop_account_state = {
                "schema_version": "prop_firm_headroom_account_state_v4",
                "account_namespace": runtime_cfg.get(
                    "prop_firm_headroom_required_account_namespace",
                    "gtos_runtime_account",
                ),
                "initial_balance": (
                    runtime_cfg.get("prop_safe_selector_initial_balance", 100000.0)
                ),
                "current_balance": balance,
                "current_equity": equity,
                "risk_base_amount": risk_base_amount,
                "day_start_equity_or_balance_baseline": (
                    self.session_state.get("start_equity")
                    or self.session_state.get("start_balance")
                    or equity
                ),
                "open_position_risk_pct": open_position_exposure[
                    "open_position_risk_pct"
                ],
                "open_position_risk_amount": open_position_exposure[
                    "open_position_risk_amount"
                ],
                "open_position_count": open_position_exposure["open_position_count"],
                "open_position_risk_valued_count": open_position_exposure[
                    "open_position_risk_valued_count"
                ],
                "open_position_risk_pct_fallback_count": open_position_exposure[
                    "open_position_risk_pct_fallback_count"
                ],
                "open_position_risk_missing_count": open_position_exposure[
                    "open_position_risk_missing_count"
                ],
                "open_position_risk_details": open_position_exposure[
                    "open_position_risk_details"
                ],
                "open_position_risk_missing_positions": open_position_exposure[
                    "open_position_risk_missing_positions"
                ],
                "pending_order_risk_pct": pending_order_risk_pct,
                "pending_order_risk_amount": pending_order_risk_amount,
                "new_trade_sl_risk_pct": effective_risk_pct,
                "correlated_exposure_buffer_pct": correlated_buffer_pct,
                "day_trade_count": int(self.session_state.get("trades_today", 0) or 0),
                "session_trade_count": session_trade_count,
                "symbol_day_trade_count": int(
                    self.session_state.get("trades_today", 0) or 0
                ),
                "symbol_session_trade_count": session_trade_count,
                "simultaneous_candidate_count": 1,
                "symbol": self._symbol,
                "route_session": kill_zone,
            }
            vnext_prop_candidate_context = {
                "symbol": self._symbol,
                "route_session": kill_zone,
            }
            vnext_prop_safe_selector = evaluate_vnext_prop_safe_selector(
                decision=vnext_decision,
                config=self.config,
                current_risk_pct=effective_risk_pct,
                current_time_utc=datetime.now(timezone.utc),
                account_state=vnext_prop_account_state,
                candidate_context=vnext_prop_candidate_context,
            )
            if record:
                attach_vnext_prop_safe_selector_to_record(record, vnext_prop_safe_selector)
            logger.info(
                "GTOS_VNEXT_PROP_SAFE_SELECTOR action=%s would_action=%s applied=%s "
                "risk=%.3f%%->%.3f%% external_daily_cushion=%.2f "
                "external_overall_cushion=%.2f internal_overlay_cushion=%s reason=%s",
                vnext_prop_safe_selector.action,
                vnext_prop_safe_selector.would_action,
                vnext_prop_safe_selector.applied,
                vnext_prop_safe_selector.before_risk_pct,
                vnext_prop_safe_selector.after_risk_pct,
                (
                    vnext_prop_safe_selector.external_rule_projection.get(
                        "remaining_daily_cushion", 0.0
                    )
                ),
                (
                    vnext_prop_safe_selector.external_rule_projection.get(
                        "remaining_overall_cushion", 0.0
                    )
                ),
                vnext_prop_safe_selector.internal_overlay_projection.get(
                    "remaining_daily_cushion"
                ),
                vnext_prop_safe_selector.reason,
            )
            moonshot_context = {
                **vnext_prop_candidate_context,
                "side": tp.direction,
                "framework": (vnext_decision.event or {}).get("effective_framework")
                or (vnext_decision.event or {}).get("framework"),
                "candidate_origin_family": (vnext_decision.event or {}).get(
                    "candidate_origin_family"
                ),
                "route_family": (vnext_decision.event or {}).get("route_family"),
                "kill_zone": kill_zone,
                "kill_zone_position": f"in_{str(kill_zone).strip().lower()}_runtime_configured_kill_zone",
                "branch_label": vnext_decision.decision,
                "branch_reason": vnext_decision.reason,
                "source_complete": ltf_path_state.get("source_complete"),
                "source_window_complete": ltf_path_state.get("source_complete"),
                "same_bar_ambiguous": ltf_path_state.get("same_bar_ambiguous"),
                "selected_policy_same_bar_ambiguous": ltf_path_state.get("same_bar_ambiguous"),
            }
            if isinstance(raw_data, dict):
                for key in (
                    "source_mode",
                    "source_path_feature_status",
                    "candidate_origin_family",
                    "candle_time_utc",
                    "time_utc",
                    "timestamp_utc",
                    "time",
                    "kill_zone_position",
                    "session_bucket",
                    "route_session",
                    "ordered_path_status",
                    "selected_policy_ordered_path_status",
                    "selected_policy_same_bar_ambiguous",
                    "current_bar_displacement_atr14",
                    "liquidity_sweep_proxy_state",
                    "volatility_state_14_vs_50",
                    "trend_state_20",
                    "policy_router_mode",
                    "remaining_daily_cushion_r",
                    "remaining_overall_cushion_r",
                    "phase_profit_remaining_r",
                    "account_recovery_expectancy_r",
                ):
                    if raw_data.get(key) not in (None, ""):
                        moonshot_context[key] = raw_data.get(key)
            vnext_moonshot_dynamic_execution = (
                self._evaluate_gtos_vnext_moonshot_dynamic_execution(
                    vnext_decision=vnext_decision,
                    raw_data=raw_data,
                    kill_zone=kill_zone,
                    record=record,
                    candidate_context=moonshot_context,
                )
            )
            self._record_gtos_vnext_replacement_monitoring(
                phase="post_l2_replacement_candidate",
                raw_data=raw_data,
                kill_zone=kill_zone,
                record=record,
                vnext_pre_ai=vnext_pre_ai,
                vnext_ai_policy=vnext_ai_policy,
                vnext_decision=vnext_decision,
                vnext_risk_adjustment=vnext_risk_adjustment,
                vnext_pending_policy=vnext_pending_policy,
                vnext_ltf_path_execution=vnext_ltf_path_execution,
                vnext_prop_safe_selector=vnext_prop_safe_selector,
                vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
                source_capture_state={
                    "source_complete": ltf_path_state.get("source_complete"),
                    "source_window_complete": ltf_path_state.get("source_complete"),
                    "same_bar_ambiguous": ltf_path_state.get("same_bar_ambiguous"),
                    "source_mode": moonshot_context.get("source_mode"),
                },
            )
            pre_prop_selected_cell_risk_pct = None
            try:
                pre_prop_selected_cell_risk_pct = float(
                    (vnext_moonshot_dynamic_execution.source_event or {}).get(
                        "selected_cell_risk_pct"
                    )
                )
            except (TypeError, ValueError):
                pre_prop_selected_cell_risk_pct = None
            if vnext_prop_safe_selector.applied:
                if vnext_prop_safe_selector.action == "REDUCE_RISK":
                    effective_risk_pct = vnext_prop_safe_selector.after_risk_pct
                elif vnext_prop_safe_selector.action in {"DEFER_UNTIL_RESET", "BLOCK"}:
                    if record:
                        record.setdefault("decision_pipeline", {})[
                            "gtos_vnext_prop_safe_selector_pre_selected_cell_projection_only"
                        ] = True
                        record.setdefault("decision_pipeline", {})[
                            "gtos_vnext_prop_safe_selector_pre_selected_cell_projection_reason"
                        ] = vnext_prop_safe_selector.reason
                        record.setdefault("instrumentation", {})[
                            "gtos_vnext_prop_safe_selector_terminal_deferred_until_selected_cell"
                        ] = True

            dynamic_cfg = (self.config.get("gtos_vnext_runtime", {}) or {})
            dynamic_apply_requested = bool(
                dynamic_cfg.get("moonshot_dynamic_execution_router_enabled", False)
                and dynamic_cfg.get(
                    "moonshot_dynamic_execution_router_apply_to_execution",
                    False,
                )
                and vnext_decision.apply_to_execution
            )
            if dynamic_apply_requested and not vnext_moonshot_dynamic_execution.applied:
                final_outcome = "SKIPPED_GTOS_VNEXT_MOONSHOT_DYNAMIC"
                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = final_outcome
                    record["decision_pipeline"]["gtos_vnext_moonshot_dynamic_block_reason"] = (
                        vnext_moonshot_dynamic_execution.decision_status
                    )
                    record["decision_pipeline"][
                        "gtos_vnext_moonshot_dynamic_refusal_reasons"
                    ] = list(vnext_moonshot_dynamic_execution.refusal_reasons)
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome=final_outcome,
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    final_outcome,
                    (
                        f"dynamic_status={vnext_moonshot_dynamic_execution.decision_status} "
                        f"action={vnext_moonshot_dynamic_execution.candidate_action} "
                        f"refusals={list(vnext_moonshot_dynamic_execution.refusal_reasons)}"
                    ),
                    kill_zone,
                    produced_candidate=True,
                )
                return

            selected_cell_risk_pct = None
            try:
                selected_cell_risk_pct = float(
                    (vnext_moonshot_dynamic_execution.source_event or {}).get(
                        "selected_cell_risk_pct"
                    )
                )
            except (TypeError, ValueError):
                selected_cell_risk_pct = None
            if vnext_moonshot_dynamic_execution.applied and selected_cell_risk_pct and selected_cell_risk_pct > 0:
                effective_risk_pct, selected_cell_risk_composition = (
                    _compose_effective_risk_with_selected_cell(
                        effective_risk_pct,
                        selected_cell_risk_pct,
                    )
                )
                vnext_prop_account_state["new_trade_sl_risk_pct"] = effective_risk_pct
                if record:
                    record.setdefault("decision_pipeline", {})[
                        "gtos_vnext_selected_cell_risk_composition"
                    ] = selected_cell_risk_composition
                    record.setdefault("decision_pipeline", {})[
                        "effective_risk_pct"
                    ] = effective_risk_pct
                vnext_prop_safe_selector = evaluate_vnext_prop_safe_selector(
                    decision=vnext_decision,
                    config=self.config,
                    current_risk_pct=effective_risk_pct,
                    current_time_utc=datetime.now(timezone.utc),
                    account_state=vnext_prop_account_state,
                    candidate_context={
                        **vnext_prop_candidate_context,
                        "risk_authority": "selected_cell_post_dynamic",
                    },
                )
                if record:
                    record.setdefault("decision_pipeline", {})[
                        "gtos_vnext_prop_safe_selector_post_selected_cell"
                    ] = vnext_prop_safe_selector.to_record()
                if vnext_prop_safe_selector.applied:
                    if vnext_prop_safe_selector.action == "REDUCE_RISK":
                        effective_risk_pct = min(
                            effective_risk_pct,
                            vnext_prop_safe_selector.after_risk_pct,
                        )
                        vnext_prop_account_state[
                            "new_trade_sl_risk_pct"
                        ] = effective_risk_pct
                        if record:
                            record.setdefault("decision_pipeline", {})[
                                "effective_risk_pct"
                            ] = effective_risk_pct
                    elif vnext_prop_safe_selector.action in {
                        "DEFER_UNTIL_RESET",
                        "BLOCK",
                    }:
                        final_outcome = (
                            "DEFERRED_GTOS_VNEXT_PROP_RESET"
                            if vnext_prop_safe_selector.action == "DEFER_UNTIL_RESET"
                            else "SKIPPED_GTOS_VNEXT_PROP_BUDGET"
                        )
                        if record and tc_cfg.get("save_rejected", True):
                            record["decision_pipeline"]["final_outcome"] = final_outcome
                            save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                        self._record_forward_capture_candidate_shadow(
                            analysis=analysis,
                            mso=mso,
                            record=record,
                            verification=verification,
                            final_outcome=final_outcome,
                            kill_zone=kill_zone,
                        )
                        self._log_candle(
                            final_outcome,
                            vnext_prop_safe_selector.reason,
                            kill_zone,
                            produced_candidate=True,
                        )
                        return

            vnext_dynamic_trade_context = self._vnext_dynamic_trade_context(
                vnext_moonshot_dynamic_execution
            )

            # Whether to send risk_pct_override depends on EITHER the
            # group-scoped corr_adj OR the cross-instrument HALVE having
            # actually changed the resolved risk.
            risk_was_adjusted = (
                corr_adj.adjusted
                or cross_corr_adj.action == "RISK_REDUCE_HALF"
                or side_aware_was_applied
                or vnext_risk_adjustment.applied
                or autocorr_risk.applied
                or vnext_prop_safe_selector.applied
                or (selected_cell_risk_pct is not None and selected_cell_risk_pct > 0)
            )

            vnext_ltf_holds_market_entry = (
                vnext_ltf_path_execution.applied
                and vnext_ltf_path_execution.action in {"MONITOR_LTF_PATH", "ADJUST_LIMIT_ENTRY"}
            )
            vnext_market_entry_now = (
                vnext_pending_policy.applied
                and vnext_pending_policy.action == "MARKET_ENTRY_NOW"
                and not vnext_ltf_holds_market_entry
            ) or (
                vnext_ltf_path_execution.applied
                and vnext_ltf_path_execution.action == "MARKET_ENTRY_NOW"
            )
            vnext_live_trade_params = {
                "direction": tp.direction,
                "entry_price": vnext_execution_entry_price,
                "stop_loss": tp.stop_loss,
                "take_profit_1": tp.take_profit_1,
                "take_profit_2": tp.take_profit_2,
                "take_profit_3": tp.take_profit_3,
                "risk_reward_ratio": tp.risk_reward_ratio,
                "gtos_vnext_prop_firm_headroom_account_state_v4": (
                    vnext_prop_account_state
                ),
                **vnext_dynamic_trade_context,
            }

            if vnext_market_entry_now:
                trade_state = self.execution.open_trade(
                    trade_params=vnext_live_trade_params,
                    account_balance=balance,
                    risk_pct_override=effective_risk_pct if risk_was_adjusted else None,
                    kill_zone=kill_zone,
                    trigger="gtos_vnext_market_entry",
                )
                if trade_state:
                    self._emit_dual_broker_intent(
                        intent_type=DUAL_BROKER_MARKET_ENTRY,
                        trade_params=vnext_live_trade_params,
                        source_trade_id=trade_state.trade_id,
                        candidate_id=record.get("candidate_id") if isinstance(record, dict) else None,
                        effective_risk_pct=effective_risk_pct,
                        kill_zone=kill_zone,
                        trigger="gtos_vnext_market_entry",
                        telemetry_context={
                            "candidate_id": record.get("candidate_id") if isinstance(record, dict) else None,
                            **vnext_dynamic_trade_context,
                        },
                        primary_order={
                            "ticket": trade_state.ticket,
                            "entry_price": trade_state.entry_price,
                            "initial_volume": trade_state.initial_volume,
                            "entry_order_ticket": trade_state.entry_order_ticket,
                            "entry_deal_ticket": trade_state.entry_deal_ticket,
                            "entry_order_retcode": trade_state.entry_order_retcode,
                        },
                    )
                    if record:
                        try:
                            record["decision_pipeline"]["final_outcome"] = "EXECUTED_GTOS_VNEXT_MARKET"
                            update_execution(
                                record,
                                {
                                    "execution_mode": "GTOS_VNEXT_MARKET_ENTRY",
                                    "trade_id": trade_state.trade_id,
                                    "ticket": trade_state.ticket,
                                    "direction": trade_state.direction,
                                    "entry_price": trade_state.entry_price,
                                    "stop_loss": trade_state.stop_loss,
                                    "take_profit_1": trade_state.take_profit_1,
                                    "risk_pct": effective_risk_pct,
                                    **self._trade_state_execution_identity(trade_state),
                                    "gtos_vnext_pending_policy": vnext_pending_policy.to_record(),
                                    "gtos_vnext_ltf_path_execution": (
                                        vnext_ltf_path_execution.to_record()
                                    ),
                                    "gtos_vnext_prop_safe_selector": (
                                        vnext_prop_safe_selector.to_record()
                                    ),
                                    "gtos_vnext_moonshot_dynamic_execution": (
                                        vnext_moonshot_dynamic_execution.to_record()
                                    ),
                                },
                            )
                            base_path = tc_cfg.get(
                                "base_path", "knowledge_base/trade_records",
                            )
                            self._active_trade_record_path = save_trade_record(record, base_path)
                            self._active_trade_record = record
                        except Exception as e:
                            logger.error("Trade capture: failed to save vNext market entry record: %s", e)
                    self._record_forward_capture_candidate_shadow(
                        analysis=analysis,
                        mso=mso,
                        record=record,
                        verification=verification,
                        final_outcome="EXECUTED_GTOS_VNEXT_MARKET",
                        kill_zone=kill_zone,
                        trade_id=trade_state.trade_id,
                    )
                    try:
                        self._init_trade_tracking(trade_state)
                    except Exception as e:
                        logger.error("Exit tracking init failed on vNext market entry: %s", e)
                    self._log_candle(
                        "EXECUTED",
                        trade_state.trade_id,
                        kill_zone,
                        produced_candidate=True,
                    )
                    return

                if record and tc_cfg.get("save_rejected", True):
                    record["decision_pipeline"]["final_outcome"] = "GTOS_VNEXT_MARKET_ENTRY_FAILED"
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome="GTOS_VNEXT_MARKET_ENTRY_FAILED",
                    kill_zone=kill_zone,
                )
                self._log_candle(
                    "GTOS_VNEXT_MARKET_ENTRY_FAILED",
                    vnext_pending_policy.reason,
                    kill_zone,
                    produced_candidate=True,
                )
                return

            # 8. PLACE LIMIT ORDER
            pending_telemetry_context = build_live_candidate_identity(
                symbol=self._symbol,
                broker_symbol=self._mt5_symbol,
                source_symbol=self._symbol,
                kill_zone=kill_zone,
                analysis=analysis,
                mso=mso,
                record=record,
                verification=verification,
                final_outcome="LIMIT_PLACED",
            )
            pending_telemetry_context.update(
                self._gtos_vnext_pending_telemetry(
                    vnext_pre_ai=vnext_pre_ai,
                    vnext_decision=vnext_decision,
                    vnext_risk_adjustment=vnext_risk_adjustment,
                    vnext_pending_policy=vnext_pending_policy,
                    vnext_ltf_path_execution=vnext_ltf_path_execution,
                    vnext_prop_safe_selector=vnext_prop_safe_selector,
                    vnext_moonshot_dynamic_execution=vnext_moonshot_dynamic_execution,
                )
            )
            pending = self.execution.set_limit_intent(
                trade_params=vnext_live_trade_params,
                account_balance=balance,
                risk_pct_override=effective_risk_pct if risk_was_adjusted else None,
                telemetry_context=pending_telemetry_context,
            )

            if pending:
                self._emit_dual_broker_intent(
                    intent_type=DUAL_BROKER_PENDING_LIMIT,
                    trade_params=vnext_live_trade_params,
                    source_trade_id=pending.trade_id,
                    candidate_id=record.get("candidate_id") if isinstance(record, dict) else None,
                    effective_risk_pct=effective_risk_pct,
                    kill_zone=kill_zone,
                    trigger="gtos_vnext_pending_limit",
                    telemetry_context=pending_telemetry_context,
                    primary_order={
                        "pending_order_mode": pending.pending_order_mode,
                        "broker_pending_order_created": pending.broker_pending_order_created,
                        "mt5_order_ticket": pending.mt5_order_ticket,
                        "native_pending_order_type": pending.native_pending_order_type,
                    },
                )
                self._log_candle(
                    "LIMIT_PLACED", pending.trade_id, kill_zone,
                    extended_kz=False, kz_sub_window=kill_zone,
                    produced_candidate=True,
                )
                logger.info(
                    "LIMIT PLACED: %s %s limit=%.5f sl=%.5f tp=%.5f",
                    pending.trade_id, pending.direction,
                    pending.limit_price, pending.stop_loss, pending.take_profit_1,
                )
                pending_final_target_r = getattr(
                    pending, "gtos_vnext_dynamic_final_target_r", None
                )
                pending_rr = (
                    pending_final_target_r
                    if pending_final_target_r not in (None, "")
                    else tp.risk_reward_ratio
                    if tp.risk_reward_ratio
                    else 1.5
                )
                notify_limit_placed(
                    symbol=self._symbol, direction=pending.direction,
                    entry=pending.limit_price, sl=pending.stop_loss,
                    tp=pending.take_profit_1, rr=float(pending_rr),
                    kill_zone=kill_zone, trade_id=pending.trade_id,
                    dynamic_policy=getattr(pending, "gtos_vnext_dynamic_policy_selected", None),
                    risk_pct=getattr(pending, "risk_pct", None),
                    origin_family=getattr(pending, "gtos_vnext_origin_family", None),
                    selector_ref=(
                        getattr(pending, "gtos_vnext_selector_row_id", None)
                        or getattr(pending, "gtos_vnext_selector_proof_hash", None)
                        or getattr(pending, "gtos_vnext_source_event_hash", None)
                    ),
                    vnext_context=build_vnext_notification_context(
                        pending,
                        lifecycle_event="limit_placed",
                    ),
                )
                if record:
                    try:
                        record["decision_pipeline"]["final_outcome"] = "LIMIT_PLACED"
                        record["limit_intent"] = {
                            "trade_id": pending.trade_id,
                            "limit_price": pending.limit_price,
                            "stop_loss": pending.stop_loss,
                            "take_profit_1": pending.take_profit_1,
                            "expiry_candles": pending.expiry_candles,
                            "pending_order_mode": pending.pending_order_mode,
                            "broker_pending_order_created": (
                                pending.broker_pending_order_created
                            ),
                            "mt5_order_ticket": pending.mt5_order_ticket,
                            "native_pending_order_type": pending.native_pending_order_type,
                            "gtos_vnext_pending_policy": vnext_pending_policy.to_record(),
                            "gtos_vnext_ltf_path_execution": (
                                vnext_ltf_path_execution.to_record()
                            ),
                            "gtos_vnext_prop_safe_selector": (
                                vnext_prop_safe_selector.to_record()
                            ),
                            "gtos_vnext_moonshot_dynamic_execution": (
                                vnext_moonshot_dynamic_execution.to_record()
                            ),
                        }
                        base_path = tc_cfg.get(
                            "base_path", "knowledge_base/trade_records",
                        )
                        self._pending_trade_record_path = save_trade_record(
                            record, base_path,
                        )
                        # T2.6: index under intent trade_id for race-free recovery
                        if self._pending_trade_record_path:
                            index_pending_record(
                                trade_id=pending.trade_id,
                                record_path=self._pending_trade_record_path,
                                symbol=self._symbol,
                                base_path=base_path,
                            )
                    except Exception as e:
                        logger.error("Trade capture: failed to save limit intent record: %s", e)
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome="LIMIT_PLACED",
                    kill_zone=kill_zone,
                    trade_id=pending.trade_id,
                )
            else:
                if record:
                    record["decision_pipeline"]["final_outcome"] = "LIMIT_INTENT_FAILED"
                    save_trade_record(record, tc_cfg.get("base_path", "knowledge_base/trade_records"))
                self._record_forward_capture_candidate_shadow(
                    analysis=analysis,
                    mso=mso,
                    record=record,
                    verification=verification,
                    final_outcome="LIMIT_INTENT_FAILED",
                    kill_zone=kill_zone,
                )
                self._log_candle("LIMIT_INTENT_FAILED", "set_limit_intent returned None", kill_zone,
                                 produced_candidate=True)

        except DataIncompleteError as e:
            self._data_incomplete_streak += 1
            logger.warning(f"Data incomplete: {e}")
            self._log_candle("NO_TRADE", f"data_incomplete: {e}", kill_zone)
            if self._data_incomplete_streak >= self._data_incomplete_restart_threshold:
                self._abnormal_shutdown_reason = (
                    f"data_incomplete_streak_{self._data_incomplete_streak}: {e}"
                )
                logger.error(
                    "Data incomplete for %d consecutive %s candles after MT5 "
                    "reconnect attempts. Exiting abnormally so watchdog can "
                    "respawn a fresh orchestrator.",
                    self._data_incomplete_streak,
                    kill_zone,
                )
                self.running = False
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            self._log_candle("ERROR", str(e), kill_zone)

    def _ingest_live_data_with_reconnect(self, kill_zone: str) -> dict:
        """Ingest live data, retrying once through a fresh MT5 session.

        A post-outage MT5 Python session can keep returning empty candles while
        a new Python process reads the same terminal correctly. Reconnecting
        here handles the recoverable case immediately; the caller counts
        consecutive failures and exits without a graceful marker if MT5 stays
        stale.
        """
        try:
            return ingest_live_data(self.mt5, self.config)
        except DataIncompleteError as first_error:
            logger.warning(
                "Data incomplete on first read for %s/%s: %s. Reconnecting MT5 "
                "and retrying once.",
                self._symbol,
                kill_zone,
                first_error,
            )
            self._reconnect_mt5_after_data_incomplete(first_error)
            return ingest_live_data(self.mt5, self.config)

    def _reconnect_mt5_after_data_incomplete(self, error: Exception) -> None:
        """Refresh the MT5 session after empty candle/account reads."""
        if self.mt5 is None:
            raise DataIncompleteError(f"MT5 unavailable after data_incomplete: {error}")
        try:
            self.mt5.disconnect()
        except Exception as exc:  # noqa: BLE001
            logger.warning("MT5 disconnect during data-incomplete recovery failed: %s", exc)
        try:
            if not self.mt5.connect():
                raise DataIncompleteError(
                    f"MT5 reconnect returned false after data_incomplete: {error}"
                )
            logger.warning(
                "MT5 reconnect succeeded after data-incomplete read for %s",
                self._symbol,
            )
        except DataIncompleteError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DataIncompleteError(
                f"MT5 reconnect raised after data_incomplete: {error}; reconnect_error={exc}"
            ) from exc

    # === SESSION MEMORY ===

    def _update_session_memory(self, analysis, kill_zone: str):
        now = datetime.now(timezone.utc)
        summary = self._compress_evaluation(analysis)
        entry = {
            "time": now.strftime("%H:%M UTC"),
            "kill_zone": kill_zone,
            "decision": analysis.decision,
            "summary": summary,
        }
        self.session_memory.append(entry)

        # Keep only last 6 entries per KZ
        kz_entries = [e for e in self.session_memory if e["kill_zone"] == kill_zone]
        if len(kz_entries) > 6:
            for i, e in enumerate(self.session_memory):
                if e["kill_zone"] == kill_zone:
                    self.session_memory.pop(i)
                    break

    def _compress_evaluation(self, analysis) -> str:
        decision = analysis.decision
        if decision == "NO_TRADE":
            reason = analysis.no_trade_reason or "unknown"
            return f"NO_TRADE — {reason[:100]}"
        elif decision == "WAIT":
            reason = getattr(analysis, "wait_reason", "unknown") or "unknown"
            return f"WAIT — {reason[:100]}"
        elif decision == "CANDIDATE":
            tp = analysis.trade_parameters
            if tp is None:
                return "CANDIDATE — null trade_parameters (demoted)"
            r = analysis.reasoning
            grade = r.setup_grade if r else "?"
            conf = analysis.confidence_score
            return (f"CANDIDATE ({grade}, conf={conf}) — "
                    f"{tp.direction} entry={tp.entry_price}, "
                    f"SL={tp.stop_loss}, TP1={tp.take_profit_1}")
        return f"{decision}"

    def _format_session_memory(self) -> str:
        if not self.session_memory:
            return ""
        lines = []
        for entry in self.session_memory[-6:]:
            lines.append(f"- {entry['time']}: {entry['summary']}")
        return "\n".join(lines)

    @staticmethod
    def _compute_deterministic_bias(mso) -> dict:
        """Compute directional bias deterministically from MSO structure.

        Implements the prompt's own U1/U2 rules in code:
        - If D1 is clearly bullish/bearish, use D1 as bias.
        - If D1 is unclear but H4+H1 both agree, use their consensus.
        - If D1 is unclear but H4 is clear, use H4 as primary reference.
        - Otherwise, no valid bias exists.

        Returns dict with keys: bias, source, d1, h4, h1, m15.
        """
        tfs = mso.timeframes if hasattr(mso, "timeframes") else {}

        def _dir(tf_name):
            tf = tfs.get(tf_name)
            if tf is None:
                return "unavailable"
            structure = getattr(tf, "structure", None)
            return structure.direction if structure else "unavailable"

        d1 = _dir("D1")
        h4 = _dir("H4")
        h1 = _dir("H1")
        m15 = _dir("M15")

        directional = ("bullish", "bearish")

        if d1 in directional:
            bias = d1
            source = "D1"
        elif h4 in directional and h4 == h1:
            bias = h4
            source = "H4+H1_consensus"
        elif h4 in directional:
            bias = h4
            source = "H4_primary"
        else:
            bias = "no_bias"
            source = "none"

        return {
            "bias": bias,
            "source": source,
            "d1": d1,
            "h4": h4,
            "h1": h1,
            "m15": m15,
        }

    def _compute_align_context(self, mso, bias_result: dict | None = None) -> str:
        """Compute timeframe alignment score and format as prompt context.

        Counts how many of D1/H4/H1/M15 share the same directional bias.
        The dominant direction and score are injected so the AI can weigh
        confluence strength.  This is NOT a hard gate — 24% of winning
        trades historically had align < 2.

        Also injects the deterministically computed directional bias as a
        binding fact so the AI does not re-derive it (fixing the U1
        inconsistency that blocked 77% of live evaluations in WF-1).

        Returns a formatted string block for prompt injection.
        """
        directions = {}
        for tf_name in ("D1", "H4", "H1", "M15"):
            tf_state = mso.timeframes.get(tf_name)
            if tf_state:
                directions[tf_name] = tf_state.structure.direction
            else:
                directions[tf_name] = "unavailable"

        bullish = sum(1 for d in directions.values() if d == "bullish")
        bearish = sum(1 for d in directions.values() if d == "bearish")
        dominant = "bullish" if bullish >= bearish else "bearish"
        score = max(bullish, bearish)

        detail = ", ".join(f"{tf}={d}" for tf, d in directions.items())
        lines = [
            "## Timeframe Alignment",
            f"Alignment score: {score}/4 ({dominant})",
            f"  {detail}",
            "  Historical edge: 3-4 aligned TFs show +7-9pp better continuation.",
            "  Score 0-1 means most timeframes disagree — higher bar for entry.",
        ]
        logger.info("Align score: %d/4 %s (%s)", score, dominant, detail)

        # Inject deterministic bias as binding fact
        if bias_result is None:
            bias_result = self._compute_deterministic_bias(mso)
        bias = bias_result["bias"]
        source = bias_result["source"]
        lines.append("")
        lines.append("## Directional Bias (COMPUTED — DO NOT OVERRIDE)")
        lines.append(f"Bias: {bias} (source: {source})")
        lines.append(
            f"  D1={bias_result['d1']}, H4={bias_result['h4']}, "
            f"H1={bias_result['h1']}, M15={bias_result['m15']}"
        )
        lines.append(
            "  This bias has been computed deterministically from market structure. "
            "Use it as given for U1. Do NOT re-derive directional bias."
        )
        if bias in ("bullish", "bearish"):
            lines.append(
                f"  Trade direction: {'LONG' if bias == 'bullish' else 'SHORT'} only."
            )
        logger.info("Deterministic bias: %s (source=%s)", bias, source)

        route_record = bias_result.get("gtos_vnext_route_decision") if isinstance(bias_result, dict) else None
        if isinstance(route_record, dict):
            frameworks = route_record.get("recommended_frameworks") or []
            route_families = route_record.get("recommended_route_families") or []
            blocked_frameworks = route_record.get("blocked_frameworks") or []
            blocked_route_families = route_record.get("blocked_route_families") or []
            lines.append("")
            lines.append("## GTOS vNext Mechanical Route")
            lines.append(
                f"Decision: {route_record.get('decision')} "
                f"(action: {route_record.get('action')}, reason: {route_record.get('reason')})"
            )
            if route_record.get("recommended_side"):
                lines.append(f"  Routed side: {route_record.get('recommended_side')}")
            if frameworks:
                lines.append(f"  Preferred framework route: {', '.join(str(item) for item in frameworks)}")
            if route_families:
                lines.append(
                    f"  Preferred mechanical route family: {', '.join(str(item) for item in route_families)}"
                )
            if blocked_frameworks:
                lines.append(f"  Avoid framework route: {', '.join(str(item) for item in blocked_frameworks)}")
            if blocked_route_families:
                lines.append(
                    f"  Avoid mechanical route family: {', '.join(str(item) for item in blocked_route_families)}"
                )
            lines.append("  Treat this as source-bound replay evidence attached before the AI call.")

        # Append instrument-specific domain expertise
        expertise = self._get_instrument_expertise(self._symbol)
        if expertise:
            lines.append("")
            lines.append(expertise)

        return "\n".join(lines)

    # === INSTRUMENT EXPERTISE ===

    @staticmethod
    def _get_instrument_expertise(symbol: str) -> str:
        """Return domain expertise block for a given instrument.

        This provides structural market knowledge (not performance statistics)
        that helps the AI assess setup quality more intelligently.  It is
        appended to ``additional_context`` alongside the alignment score.
        """
        if symbol == "XAUUSD":
            return _XAUUSD_EXPERTISE
        # Other instruments can be added here as knowledge is validated.
        return ""

    # === SHADOW DATA HELPERS ===

    @staticmethod
    def _extract_align_score(align_context: str) -> int | None:
        """Parse the alignment score integer from the align_context string."""
        import re
        m = re.search(r"Alignment score:\s*(\d)/4", align_context)
        return int(m.group(1)) if m else None

    def _get_current_spread(self) -> float | None:
        """Get current spread in price units. Returns None if MT5 unavailable."""
        try:
            if self.mt5:
                tick = self.mt5.get_tick(self._mt5_symbol)
                if tick:
                    return tick.spread_cents if hasattr(tick, "spread_cents") else None
        except Exception:
            pass
        return None

    # === CROSS-INSTRUMENT CONTEXT ===

    def _compute_cross_instrument_context(self):
        """Compute cross-instrument context for the current session.

        Pulls reference instrument D1 data and computes Asian range.
        Result is cached in ``self._ci_context_text`` — stable per day.
        """
        # Belt-and-suspenders: symbols in the strip list NEVER receive cross-
        # instrument context (currently XAUUSD D1 macro). Prevents the Apr 13
        # GBPUSD non-determinism where AI cited "XAUUSD D1 bearish macro" as
        # the deciding factor despite T7 C-gate forbidding macro reasoning.
        # See handoff 16 §54-59.
        disabled_for = self.config.get("cross_instrument_context_disabled_for", []) or []
        if self._symbol in disabled_for:
            self._ci_context_text = ""
            self._asian_range_info = None
            # Distinct sentinel — the symbol is on the strip list, so we
            # never compute an XAU view. The direction-emission audit
            # logger reads this and writes "disabled" so the analyst can
            # separate "no XAU data" from "policy says don't look at XAU".
            self._xau_d1_direction_value = "disabled"
            return

        ci_cfg = self.config.get("cross_instrument_context", {})
        if not ci_cfg.get("enabled"):
            self._ci_context_text = ""
            self._xau_d1_direction_value = "unavailable"
            self._asian_range_info = None
            return

        today = self.session_state.get("date", "")
        if not today:
            self._ci_context_text = ""
            self._xau_d1_direction_value = "unavailable"
            self._asian_range_info = None
            return

        try:
            ref_symbol = ci_cfg.get("reference_instrument", "XAUUSD")
            ref_tf = ci_cfg.get("reference_timeframe", "D1")

            # Pull reference D1 data from MT5
            from src.components.data_ingestion import TF_MAP
            tf_const = TF_MAP.get(ref_tf)
            if tf_const is None:
                logger.warning("Unknown timeframe %s for cross-instrument", ref_tf)
                self._ci_context_text = ""
                self._xau_d1_direction_value = "unavailable"
                return
            ref_d1 = self.mt5.get_candles(ref_symbol, tf_const, 30)
            if not ref_d1:
                logger.warning("No %s %s data for cross-instrument context", ref_symbol, ref_tf)
                self._ci_context_text = ""
                self._xau_d1_direction_value = "unavailable"
                return

            xau_dir = get_xauusd_d1_direction(today, ref_d1)
            # Persist raw XAU direction for downstream shadow loggers.
            # ``get_xauusd_d1_direction`` returns
            # ``"bullish"`` / ``"bearish"`` / ``"unavailable"``.
            self._xau_d1_direction_value = xau_dir or "unavailable"

            # Pull target instrument M15 + D1 for Asian range
            m15_data = self.mt5.get_candles(self._mt5_symbol, TF_MAP["M15"], 100)
            d1_data = self.mt5.get_candles(self._mt5_symbol, TF_MAP["D1"], 20)
            asian_info = get_asian_range_pct(today, m15_data or [], d1_data or [])
            self._asian_range_info = asian_info

            self._ci_context_text = format_cross_instrument_context(
                xau_dir, asian_info, self.config,
                candidate_symbol=self._mt5_symbol,
            )
            if self._ci_context_text:
                logger.info("Cross-instrument context: %s D1=%s, Asian=%s",
                            ref_symbol, xau_dir,
                            f"{asian_info['pct_of_adr']:.0f}% ({asian_info['category']})"
                            if asian_info else "unavailable")
        except Exception as e:
            logger.warning("Failed to compute cross-instrument context: %s", e)
            self._ci_context_text = ""
            self._xau_d1_direction_value = "unavailable"
            self._asian_range_info = None

    def _record_forward_capture_evaluation_shadow(
        self,
        *,
        mso,
        raw_data,
        evaluation_stage: str,
        kill_zone: str,
        prescreen_status: str | None = None,
        deterministic_bias: str | None = None,
        ai_status: str | None = None,
        ai_dependency: str | None = None,
        reason: str | None = None,
    ) -> None:
        """Emit research-only follow rows for a live MSO evaluation."""
        try:
            cfg = (
                (self.config.get("shadow_loggers", {}) or {})
                .get("forward_capture_evaluation_logger", {})
            ) or {}
            if cfg.get("enabled", True) is False:
                return
            record_live_mso_forward_shadow(
                symbol=self._symbol,
                broker_symbol=self._mt5_symbol,
                kill_zone=kill_zone,
                mso=mso,
                raw_data=raw_data,
                evaluation_stage=evaluation_stage,
                prescreen_status=prescreen_status,
                deterministic_bias=deterministic_bias,
                ai_status=ai_status,
                ai_dependency=ai_dependency,
                reason=reason,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("forward_capture_evaluation_logger failed (non-blocking): %s", e)

    def _record_forward_capture_candidate_shadow(
        self,
        *,
        analysis,
        mso,
        record,
        verification=None,
        final_outcome: str,
        kill_zone: str,
        trade_id: str | None = None,
    ) -> None:
        """Emit research-only follow rows for one live AI CANDIDATE."""
        try:
            cfg = (
                (self.config.get("shadow_loggers", {}) or {})
                .get("forward_capture_candidate_logger", {})
            ) or {}
            if cfg.get("enabled", True) is False:
                return
            record_live_candidate_forward_shadow(
                symbol=self._symbol,
                broker_symbol=self._mt5_symbol,
                source_symbol=self._symbol,
                kill_zone=kill_zone,
                analysis=analysis,
                mso=mso,
                record=record,
                verification=verification,
                final_outcome=final_outcome,
                trade_id=trade_id,
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("forward_capture_candidate_logger failed (non-blocking): %s", e)

    # === EXIT TRACKING ===

    def _latest_pending_lifecycle_row_for_trade_id(
        self, trade_id: str,
    ) -> dict | None:
        """Return the latest pending-limit lifecycle row for a trade id."""
        if not trade_id:
            return None
        path = Path(PENDING_LIMIT_LIFECYCLE_LOG_PATH)
        if not path.exists():
            return None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return None
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("symbol") or "") != str(self._symbol):
                continue
            if str(row.get("trade_id") or "") != str(trade_id):
                continue
            return row
        return None

    @staticmethod
    def _pending_limit_terminal_outcome(
        lifecycle_row: dict | None,
        fallback_reason: str,
    ) -> str:
        row = lifecycle_row or {}
        intent_state = str(row.get("intent_after_check") or "").lower()
        reason = str(row.get("reason") or fallback_reason or "").lower()
        if (
            row.get("sl_too_close_abort") is True
            or "sl_too_close" in intent_state
            or "sl_too_close" in reason
        ):
            return "LIMIT_CANCELLED_GTOS_VNEXT_LTF_SL_TOO_CLOSE"
        if row.get("wrong_side_abort") is True or "wrong_side" in intent_state:
            return "LIMIT_CANCELLED_GTOS_VNEXT_LTF_PRICE_BEYOND_SL"
        if "daily_loss" in reason:
            return "LIMIT_CANCELLED_GTOS_VNEXT_DAILY_LOSS_STOP"
        if "drawdown" in reason:
            return "LIMIT_CANCELLED_GTOS_VNEXT_DRAWDOWN_STOP"
        if "consecutive_losses" in reason:
            return "LIMIT_CANCELLED_GTOS_VNEXT_CONSECUTIVE_LOSSES_STOP"
        if "kill_zone" in reason or "kz_trade_cap" in reason:
            return "LIMIT_CANCELLED_GTOS_VNEXT_KILL_ZONE_CAP_STOP"
        return "LIMIT_CANCELLED_GTOS_VNEXT_PENDING_NO_FILL"

    def _mark_pending_trade_record_terminal_no_fill(
        self,
        record_path: str | None,
        trade_id: str,
        reason: str,
    ) -> None:
        """Persist the terminal no-fill/cancel state on the candidate record."""
        if not record_path or not Path(record_path).exists():
            return
        try:
            record = load_trade_record(record_path)
            if not isinstance(record, dict):
                return
            lifecycle_row = self._latest_pending_lifecycle_row_for_trade_id(trade_id)
            final_outcome = self._pending_limit_terminal_outcome(lifecycle_row, reason)
            lifecycle_reason = (
                (lifecycle_row or {}).get("reason")
                or reason
                or "pending_limit_cleared_without_fill"
            )
            lifecycle_state = (lifecycle_row or {}).get("intent_after_check")

            record.setdefault("decision_pipeline", {})[
                "final_outcome"
            ] = final_outcome
            limit_intent = record.setdefault("limit_intent", {})
            limit_intent.update({
                "terminal_state": lifecycle_state or "cleared_without_fill",
                "terminal_reason": lifecycle_reason,
                "terminal_outcome": final_outcome,
                "terminal_lifecycle_timestamp_utc": (lifecycle_row or {}).get(
                    "timestamp_utc"
                ),
                "broker_fill_state": (lifecycle_row or {}).get(
                    "broker_fill_state", "not_filled"
                ),
                "order_send_attempted": (lifecycle_row or {}).get(
                    "order_send_attempted"
                ),
                "order_send_success": (lifecycle_row or {}).get(
                    "order_send_success"
                ),
                "order_result_retcode": (lifecycle_row or {}).get(
                    "order_result_retcode"
                ),
            })
            record.setdefault("instrumentation", {}).update({
                "gtos_vnext_pending_limit_terminal_state": (
                    lifecycle_state or "cleared_without_fill"
                ),
                "gtos_vnext_pending_limit_terminal_reason": lifecycle_reason,
                "gtos_vnext_pending_limit_terminal_outcome": final_outcome,
                "gtos_vnext_pending_limit_terminal_record_source": (
                    "pending_limit_lifecycle"
                    if lifecycle_row
                    else "orchestrator_clear_pending_trade_record"
                ),
            })
            base_path = self.config.get("trade_capture", {}).get(
                "base_path", "knowledge_base/trade_records",
            )
            save_trade_record(record, base_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to mark pending record terminal no-fill (%s): %s",
                reason,
                exc,
            )

    def _clear_pending_trade_record(
        self, trade_id: str = "", *, reason: str = "",
    ) -> None:
        """Clear the in-memory pending record path AND drop the index entry.

        T2.6: abandonment paths (drawdown stop, consec losses, new-day, stale
        clear) must remove the trade_id from the pending index so a later
        restart does not attempt to recover a record for a cancelled intent.

        Args:
            trade_id: The intent's trade_id.  Pass explicitly when
                ``pending_intent`` has already been cleared (cancel_limit_intent
                or a failed fill cleared it).  If empty, falls back to reading
                the live ``pending_intent``, then to the in-memory record file.
            reason: Diagnostic string for logs on failure.

        Best-effort — never raises.
        """
        trade_id_for_index = trade_id or ""
        if not trade_id_for_index:
            intent = (
                getattr(self.execution, "pending_intent", None)
                if self.execution else None
            )
            if intent is not None:
                trade_id_for_index = intent.trade_id or ""
        # Last-resort: read the trade_id out of the record we're abandoning
        if not trade_id_for_index and self._pending_trade_record_path:
            try:
                rec = load_trade_record(self._pending_trade_record_path)
                trade_id_for_index = (rec.get("limit_intent") or {}).get(
                    "trade_id", "",
                ) if rec else ""
            except Exception:
                trade_id_for_index = ""

        self._mark_pending_trade_record_terminal_no_fill(
            self._pending_trade_record_path,
            trade_id_for_index,
            reason,
        )
        self._pending_trade_record_path = None
        if trade_id_for_index:
            try:
                base_path = self.config.get("trade_capture", {}).get(
                    "base_path", "knowledge_base/trade_records",
                )
                remove_pending_record(
                    trade_id_for_index, self._symbol, base_path,
                )
            except Exception as e:
                logger.warning(
                    "Failed to clear pending index entry (%s): %s", reason, e,
                )

    def _promote_pending_record_on_fill(self) -> None:
        """Load the record saved at LIMIT_PLACED and attach it as the active record.

        Without this, _finalize_exit() is never called for limit-filled trades
        because self._active_trade_record stays None — exit data, shadow logs,
        and the on-disk final_outcome all get stuck.
        """
        if not self._pending_trade_record_path:
            return
        # Capture trade_id BEFORE clearing state so we can drop the index entry
        # regardless of which branch we take below.
        intent = getattr(self.execution, "pending_intent", None) if self.execution else None
        trade_id_for_index = intent.trade_id if intent else ""
        try:
            record = load_trade_record(self._pending_trade_record_path)
            if not record:
                logger.warning(
                    "Pending record empty/missing on limit fill: %s",
                    self._pending_trade_record_path,
                )
                return
            self._active_trade_record = record
            self._active_trade_record_path = self._pending_trade_record_path
            try:
                self._attach_pending_fill_execution_to_record(record)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Failed to attach pending-fill execution capture: %s",
                    exc,
                )
            if not trade_id_for_index:
                trade_id_for_index = (record.get("limit_intent") or {}).get(
                    "trade_id", "",
                )
        except Exception as e:
            logger.warning("Failed to load trade record on limit fill: %s", e)
        finally:
            self._pending_trade_record_path = None
            # T2.6: drop the index entry now that the record is promoted
            if trade_id_for_index:
                base_path = self.config.get("trade_capture", {}).get(
                    "base_path", "knowledge_base/trade_records",
                )
                remove_pending_record(
                    trade_id_for_index, self._symbol, base_path,
                )

    def _attach_pending_fill_execution_to_record(self, record: dict) -> None:
        """Persist broker fill evidence on the trade record at limit-fill time."""
        if not isinstance(record, dict):
            return
        trade = getattr(self.execution, "active_trade", None) if self.execution else None
        if trade is None:
            record.setdefault("instrumentation", {})[
                "gtos_vnext_limit_fill_execution_capture_status"
            ] = "not_captured_no_active_trade_state_at_fill_promotion"
            return

        lifecycle_row = None
        try:
            lifecycle_row = self._latest_filled_lifecycle_row_for_active_trade()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Pending-fill lifecycle row lookup failed: %s", exc)
        if not isinstance(lifecycle_row, dict):
            lifecycle_row = {}

        def _row_or_attr(row_key: str, attr_name: str | None = None):
            value = lifecycle_row.get(row_key)
            if value not in (None, ""):
                return value
            if attr_name:
                return getattr(trade, attr_name, None)
            return None

        def _positive_ticket(value):
            if value in (None, "", 0, "0"):
                return None
            return value

        existing_execution = (
            record.get("execution")
            if isinstance(record.get("execution"), dict)
            else {}
        )

        def _execution_value(field: str, fallback):
            existing = existing_execution.get(field)
            if existing not in (None, ""):
                return existing
            return fallback

        def _execution_positive_value(field: str, fallback):
            existing = existing_execution.get(field)
            try:
                if existing not in (None, "") and float(existing) > 0:
                    return existing
            except (TypeError, ValueError):
                pass
            return fallback

        limit_intent = record.get("limit_intent") or {}
        entry_deal_ticket = _positive_ticket(
            _row_or_attr("mt5_entry_deal_ticket", "entry_deal_ticket")
        )
        lifecycle_join_keys = []
        for join_key in lifecycle_row.get("filled_order_position_join_keys") or []:
            text = str(join_key)
            if text.endswith(":0"):
                continue
            lifecycle_join_keys.append(join_key)
        execution_data = {
            "execution_mode": "GTOS_VNEXT_LIMIT_FILL_INTERNAL_MARKET_ORDER_ON_TOUCH",
            "trade_id": getattr(trade, "trade_id", None) or limit_intent.get("trade_id"),
            "ticket": getattr(trade, "ticket", None),
            "position_ticket": _row_or_attr("mt5_position_ticket", "ticket"),
            "entry_order_ticket": _row_or_attr("mt5_entry_order_ticket", "entry_order_ticket"),
            "entry_deal_ticket": entry_deal_ticket,
            "entry_deal_ticket_status": (
                "mt5_result_deal_ticket_present"
                if entry_deal_ticket is not None
                else "mt5_result_deal_ticket_absent_using_order_position_join_keys"
            ),
            "order_result_retcode": _row_or_attr("order_result_retcode", "entry_order_retcode"),
            "direction": getattr(trade, "direction", None),
            "entry_price": _execution_value("entry_price", getattr(trade, "entry_price", None)),
            "requested_limit_price": _execution_value(
                "requested_limit_price",
                lifecycle_row.get("entry_price") or limit_intent.get("limit_price"),
            ),
            "executed_entry_price": _execution_value(
                "executed_entry_price",
                lifecycle_row.get("executed_entry_price")
                or getattr(trade, "entry_price", None),
            ),
            "execution_price_delta_from_limit": lifecycle_row.get(
                "execution_price_delta_from_limit"
            ),
            "stop_loss": _execution_value("stop_loss", getattr(trade, "stop_loss", None)),
            "take_profit_1": _execution_value("take_profit_1", getattr(trade, "take_profit_1", None)),
            "take_profit_2": _execution_value("take_profit_2", getattr(trade, "take_profit_2", None)),
            "take_profit_3": _execution_value("take_profit_3", getattr(trade, "take_profit_3", None)),
            "active_stop_loss": _execution_value("active_stop_loss", getattr(trade, "stop_loss", None)),
            "broker_stop_loss": _execution_value("broker_stop_loss", getattr(trade, "stop_loss", None)),
            "active_take_profit": _execution_value(
                "active_take_profit",
                getattr(trade, "take_profit_2", None)
                or getattr(trade, "take_profit_1", None),
            ),
            "broker_take_profit": _execution_value(
                "broker_take_profit",
                getattr(trade, "take_profit_2", None)
                or getattr(trade, "take_profit_1", None),
            ),
            "initial_volume": _execution_positive_value("initial_volume", getattr(trade, "initial_volume", None)),
            "current_volume": getattr(trade, "current_volume", None),
            "sl_distance": _execution_positive_value("sl_distance", getattr(trade, "sl_distance", None)),
            "risk_pct": (
                _execution_value(
                    "risk_pct",
                    getattr(trade, "risk_pct_at_entry", None)
                    or lifecycle_row.get("gtos_vnext_prop_safe_selector_after_risk_pct"),
                )
            ),
            "cash_risk_amount": _execution_positive_value(
                "cash_risk_amount",
                getattr(trade, "cash_risk_amount", None),
            ),
            "cash_risk_amount_source": getattr(
                trade,
                "cash_risk_amount_source",
                None,
            ),
            "cash_risk_amount_status": getattr(
                trade,
                "cash_risk_amount_status",
                None,
            ),
            "broker_cash_risk_per_lot": getattr(
                trade,
                "broker_cash_risk_per_lot",
                None,
            ),
            "broker_lot_sizing_diagnostic": getattr(
                trade,
                "broker_lot_sizing_diagnostic",
                None,
            ),
            "broker_symbol": lifecycle_row.get("broker_symbol") or self._mt5_symbol,
            "broker_order_action": lifecycle_row.get("broker_order_action"),
            "broker_order_entry_mode": lifecycle_row.get("broker_order_entry_mode"),
            "broker_fill_state": lifecycle_row.get("broker_fill_state") or "filled",
            "fill_time_utc": _execution_value(
                "fill_time_utc",
                lifecycle_row.get("fill_time_utc"),
            ),
            "filled_order_position_join_keys": lifecycle_join_keys,
            "exact_r_join_key_status": lifecycle_row.get("exact_r_join_key_status"),
            "gtos_vnext_dynamic_policy_selected": getattr(
                trade,
                "gtos_vnext_dynamic_policy_selected",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_selected"),
            "gtos_vnext_execution_policy_id": getattr(
                trade,
                "gtos_vnext_execution_policy_id",
                None,
            )
            or lifecycle_row.get("gtos_vnext_execution_policy_id"),
            "gtos_vnext_dynamic_policy_applied": getattr(
                trade,
                "gtos_vnext_dynamic_policy_applied",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_applied"),
            "gtos_vnext_dynamic_policy_replaced_policy": getattr(
                trade,
                "gtos_vnext_dynamic_policy_replaced_policy",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_replaced_policy"),
            "gtos_vnext_dynamic_policy_candidate_action": getattr(
                trade,
                "gtos_vnext_dynamic_policy_candidate_action",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_candidate_action"),
            "gtos_vnext_dynamic_policy_decision_status": getattr(
                trade,
                "gtos_vnext_dynamic_policy_decision_status",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_decision_status"),
            "gtos_vnext_dynamic_policy_source_quality_action": getattr(
                trade,
                "gtos_vnext_dynamic_policy_source_quality_action",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_source_quality_action"),
            "gtos_vnext_dynamic_policy_exit_management_action": getattr(
                trade,
                "gtos_vnext_dynamic_policy_exit_management_action",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_exit_management_action"),
            "gtos_vnext_dynamic_policy_prop_action": getattr(
                trade,
                "gtos_vnext_dynamic_policy_prop_action",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_prop_action"),
            "gtos_vnext_dynamic_policy_fixed_target_role": getattr(
                trade,
                "gtos_vnext_dynamic_policy_fixed_target_role",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_policy_fixed_target_role"),
            "gtos_vnext_dynamic_be_trigger_r": getattr(
                trade,
                "gtos_vnext_dynamic_be_trigger_r",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_be_trigger_r"),
            "gtos_vnext_dynamic_final_target_r": getattr(
                trade,
                "gtos_vnext_dynamic_final_target_r",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_final_target_r"),
            "gtos_vnext_dynamic_be_trigger_price": getattr(
                trade,
                "gtos_vnext_dynamic_be_trigger_price",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_be_trigger_price"),
            "gtos_vnext_dynamic_final_target_price": getattr(
                trade,
                "gtos_vnext_dynamic_final_target_price",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_final_target_price"),
            "gtos_vnext_dynamic_time_stop_bars": getattr(
                trade,
                "gtos_vnext_dynamic_time_stop_bars",
                None,
            )
            or lifecycle_row.get("gtos_vnext_dynamic_time_stop_bars"),
            "gtos_vnext_selector_row_id": getattr(
                trade,
                "gtos_vnext_selector_row_id",
                None,
            )
            or lifecycle_row.get("gtos_vnext_selector_row_id"),
            "gtos_vnext_selected_cell_risk_pct": getattr(
                trade,
                "gtos_vnext_selected_cell_risk_pct",
                None,
            )
            or lifecycle_row.get("gtos_vnext_selected_cell_risk_pct")
            or lifecycle_row.get("gtos_vnext_prop_safe_selector_after_risk_pct"),
            "gtos_vnext_selected_cell_risk_cell_id": getattr(
                trade,
                "gtos_vnext_selected_cell_risk_cell_id",
                None,
            )
            or lifecycle_row.get("gtos_vnext_selected_cell_risk_cell_id")
            or lifecycle_row.get("gtos_vnext_selector_row_id"),
            "gtos_vnext_source_event_hash": getattr(
                trade,
                "gtos_vnext_source_event_hash",
                None,
            )
            or lifecycle_row.get("gtos_vnext_source_event_hash"),
            "lifecycle_source": {
                "source_log": str(PENDING_LIMIT_LIFECYCLE_LOG_PATH),
                "source_branch": lifecycle_row.get("source_branch"),
                "check_context": lifecycle_row.get("check_context"),
                "checked_candle_time_utc": lifecycle_row.get("checked_candle_time_utc"),
                "source_timeframe": lifecycle_row.get("source_timeframe"),
                "record_path": lifecycle_row.get("record_path"),
            },
        }
        update_execution(record, execution_data)
        record.setdefault("decision_pipeline", {})[
            "final_outcome"
        ] = "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN"
        self._refresh_vnext_candidate_intelligence_packet(
            record,
            final_order_decision={
                "final_outcome": "LIMIT_FILLED_GTOS_VNEXT_BROADER_ORIGIN",
                "reached_order_path": True,
                "order_path": "pending_limit_filled",
                "trade_id": execution_data.get("trade_id"),
                "ticket": execution_data.get("ticket"),
                "broker_fill_state": execution_data.get("broker_fill_state"),
                "fill_time_utc": execution_data.get("fill_time_utc"),
            },
        )
        record.setdefault("instrumentation", {})[
            "gtos_vnext_limit_fill_execution_capture_status"
        ] = (
            "captured_from_trade_state_and_pending_limit_lifecycle"
            if lifecycle_row
            else "captured_from_trade_state_without_lifecycle_row"
        )
        base_path = self.config.get("trade_capture", {}).get(
            "base_path", "knowledge_base/trade_records",
        )
        saved_path = save_trade_record(record, base_path)
        if saved_path:
            self._active_trade_record_path = saved_path

    def _init_trade_tracking(self, trade_state):
        """Initialize MFE/MAE and exit tracking after a trade opens."""
        self._trade_entry_price = trade_state.entry_price
        self._trade_direction = trade_state.direction
        self._trade_sl_distance = trade_state.sl_distance
        self._trade_entry_time = datetime.fromisoformat(trade_state.entry_time)
        self._mfe_price = trade_state.entry_price
        self._mae_price = trade_state.entry_price
        self._last_tick_price = trade_state.entry_price

        # BE shadow tracker (H2 — observation only, does not affect trades)
        self._be_shadow_tracker = BEShadowTracker(
            trade_id=trade_state.trade_id,
            entry_price=trade_state.entry_price,
            stop_loss=trade_state.stop_loss,
            direction=trade_state.direction,
            sl_distance=trade_state.sl_distance,
        )

        # Variant C partial close shadow tracker (observation only)
        pc_cfg = (
            (self.config.get("shadow_loggers", {}) or {}).get(
                "partial_close_shadow_logger", {},
            )
            or {}
        )
        if pc_cfg.get("enabled", True):
            partial_close_source_evidence = {
                "source_path": pc_cfg.get(
                    "source_path",
                    ".context/02_session_handoffs/14_apr13_t7_production_simulation_handoff.md",
                ),
                "source_line_no": pc_cfg.get("source_line_no", 270),
                "ftmo_pass_delta_pp": pc_cfg.get("ftmo_pass_delta_pp"),
                "status": pc_cfg.get("status", "shadow_observation"),
            }
            for evidence_key in (
                "q62_verdict",
                "q62_runtime_artifact_path",
                "q62_source_rows_represented",
                "q62_valid_universe_size",
                "q62_triggered_trade_count",
                "q62_variant_c_mean_delta_r",
                "q62_variant_c_wilcoxon_p",
                "q62_common_subset_c_mean_delta_r",
                "q62_variant_d_shadow_enabled",
                "active_policy_change_allowed_now",
                "live_triggered_events_required",
            ):
                if evidence_key in pc_cfg:
                    partial_close_source_evidence[evidence_key] = pc_cfg[evidence_key]
            self._partial_close_shadow_tracker = PartialCloseShadowTracker(
                trade_id=trade_state.trade_id,
                entry_price=trade_state.entry_price,
                stop_loss=trade_state.stop_loss,
                take_profit=getattr(trade_state, "take_profit", 0.0) or 0.0,
                direction=trade_state.direction,
                sl_distance=trade_state.sl_distance,
                partial_close_fraction=float(pc_cfg.get("partial_close_fraction", 0.33)),
                trigger_r=float(pc_cfg.get("trigger_r", 1.0)),
                source_evidence=partial_close_source_evidence,
            )
        else:
            self._partial_close_shadow_tracker = None

        trailing_cfg = (
            (self.config.get("shadow_loggers", {}) or {}).get(
                "trailing_stop_v1_shadow_logger", {},
            )
            or {}
        )
        if trailing_cfg.get("enabled", True):
            self._trailing_stop_shadow_tracker = TrailingStopShadowTracker(
                trade_id=trade_state.trade_id,
                entry_price=trade_state.entry_price,
                stop_loss=trade_state.stop_loss,
                take_profit=getattr(trade_state, "take_profit", 0.0) or 0.0,
                direction=trade_state.direction,
                sl_distance=trade_state.sl_distance,
                activation_r=float(trailing_cfg.get("activation_r", 0.5)),
                trail_distance_r=float(trailing_cfg.get("trail_distance_r", 0.5)),
                source_evidence={
                    "source_path": trailing_cfg.get(
                        "source_path",
                        "research/t2_1_trailing_stop_full_pop_rerun_2026-04-19/verdict.md",
                    ),
                    "source_rows_represented": trailing_cfg.get(
                        "source_rows_represented",
                    ),
                    "expected_delta_r_per_trade": trailing_cfg.get(
                        "expected_delta_r_per_trade",
                    ),
                    "triggered_pct": trailing_cfg.get("triggered_pct"),
                    "status": trailing_cfg.get("status", "shadow_observation"),
                },
            )
        else:
            self._trailing_stop_shadow_tracker = None

    def _update_mfe_mae(self, price: float):
        """Update MFE/MAE tracking with a new price observation."""
        if self._trade_direction is None:
            return
        if self._trade_direction == "LONG":
            if price > self._mfe_price:
                self._mfe_price = price
            if price < self._mae_price:
                self._mae_price = price
        elif self._trade_direction == "SHORT":
            if price < self._mfe_price:
                self._mfe_price = price
            if price > self._mae_price:
                self._mae_price = price

    def _update_mfe_mae_from_tick(self):
        """Get current tick and update MFE/MAE."""
        if self._trade_direction is None:
            return
        try:
            tick = self.mt5.get_tick(self._mt5_symbol)
            if tick:
                price = tick.bid if self._trade_direction == "LONG" else tick.ask
                self._last_tick_price = price
                self._update_mfe_mae(price)
                # BE shadow tracker update (non-blocking)
                if self._be_shadow_tracker:
                    self._be_shadow_tracker.update(price)
                # Variant C partial close shadow tracker update (non-blocking)
                if self._partial_close_shadow_tracker:
                    self._partial_close_shadow_tracker.update(price)
                # T2.1 trailing-stop V1 shadow tracker update (non-blocking)
                if self._trailing_stop_shadow_tracker:
                    self._trailing_stop_shadow_tracker.update(price)
        except Exception:
            pass

    def _compute_r(self, price: float) -> float:
        """Compute R-multiple for a given price relative to entry."""
        if not self._trade_sl_distance or self._trade_sl_distance == 0:
            return 0.0
        if self._trade_direction == "LONG":
            return (price - self._trade_entry_price) / self._trade_sl_distance
        else:
            return (self._trade_entry_price - price) / self._trade_sl_distance

    def _check_trade_and_capture(self):
        """Wrap check_and_manage_trade with MFE/MAE tracking and exit capture."""
        if not self.execution.active_trade:
            return

        self._update_mfe_mae_from_tick()

        trade_snapshot = self.execution.active_trade

        time_stop_result = None
        try:
            time_stop_result = self.execution.check_time_stop_and_close()
        except Exception as e:
            logger.warning("J46-J49 time stop check failed (non-blocking): %s", e)

        if time_stop_result is not None and self.execution.active_trade is None:
            if self._active_trade_record is not None:
                self._finalize_exit(trade_snapshot, time_stop_result)
            return

        result = self.execution.check_and_manage_trade({})

        if self.execution.active_trade is None and self._active_trade_record is not None:
            self._finalize_exit(trade_snapshot, result or "unknown")
        elif (
            result
            and str(result) != "monitoring"
            and self._active_trade_record is not None
        ):
            self._persist_active_trade_lifecycle_update(
                self.execution.active_trade,
                result,
            )

    def _persist_active_trade_lifecycle_update(self, trade, lifecycle_result: str) -> None:
        """Persist in-flight lifecycle truth without finalizing the trade record."""
        if not trade or not isinstance(self._active_trade_record, dict):
            return
        if not lifecycle_result:
            return

        broker_position = None
        try:
            positions = self.mt5.get_positions(self._mt5_symbol)
            for pos in positions or []:
                if getattr(pos, "ticket", None) == getattr(trade, "ticket", None):
                    broker_position = pos
                    break
        except Exception as exc:  # noqa: BLE001
            logger.warning("Active lifecycle broker sync failed (non-blocking): %s", exc)

        def _num(value):
            try:
                if value is None:
                    return None
                number = float(value)
            except (TypeError, ValueError):
                return None
            return number if math.isfinite(number) else None

        current_volume = _num(
            getattr(broker_position, "volume", None)
            if broker_position is not None
            else getattr(trade, "current_volume", None)
        )
        broker_stop_loss = _num(
            getattr(broker_position, "sl", None)
            if broker_position is not None
            else getattr(trade, "stop_loss", None)
        )
        broker_take_profit = _num(
            getattr(broker_position, "tp", None)
            if broker_position is not None
            else (
                getattr(trade, "take_profit_2", None)
                if getattr(trade, "tp1_hit", False)
                else getattr(trade, "take_profit_1", None)
            )
        )
        entry_price = _num(getattr(trade, "entry_price", None))
        direction = str(getattr(trade, "direction", "") or "").upper()
        residual_risk_released = bool(getattr(trade, "sl_at_breakeven", False))
        if entry_price is not None and broker_stop_loss is not None:
            if direction == "LONG" and broker_stop_loss >= entry_price:
                residual_risk_released = True
            elif direction == "SHORT" and broker_stop_loss <= entry_price:
                residual_risk_released = True

        partial_events = self._jsonable_vnext_snapshot(
            getattr(trade, "partial_close_events", []) or [],
            max_depth=8,
            max_items=200,
        )
        partial_closed = any(
            "PARTIAL" in str(event.get("type", "")).upper()
            for event in partial_events
            if isinstance(event, dict)
        )
        updated_at = datetime.now(timezone.utc).isoformat()

        execution = self._active_trade_record.setdefault("execution", {})
        execution.setdefault("original_position_ticket", execution.get("position_ticket"))
        execution["ticket"] = getattr(trade, "ticket", None)
        execution["position_ticket"] = getattr(trade, "ticket", None)
        execution["current_volume"] = current_volume
        execution["broker_stop_loss"] = broker_stop_loss
        execution["active_stop_loss"] = broker_stop_loss
        execution["broker_take_profit"] = broker_take_profit
        execution["active_take_profit"] = broker_take_profit
        execution["sl_at_breakeven"] = bool(getattr(trade, "sl_at_breakeven", False))
        execution["tp1_hit"] = bool(getattr(trade, "tp1_hit", False))
        execution["partial_close_events"] = partial_events
        execution["last_lifecycle_result"] = str(lifecycle_result)
        execution["last_lifecycle_update_utc"] = updated_at
        execution["active_lifecycle_capture_status"] = (
            "persisted_from_active_trade_state_and_readonly_broker_position"
            if broker_position is not None
            else "persisted_from_active_trade_state_without_broker_position"
        )
        execution["residual_worst_case_cash_risk_amount"] = (
            0.0 if residual_risk_released else None
        )
        execution["residual_worst_case_cash_risk_status"] = (
            "released_by_breakeven_or_better_sl"
            if residual_risk_released
            else "not_released_or_unverified"
        )

        lifecycle = self._active_trade_record.setdefault("lifecycle", {})
        lifecycle["active_trade_management_events"] = partial_events
        lifecycle["last_lifecycle_result"] = str(lifecycle_result)
        lifecycle["last_lifecycle_update_utc"] = updated_at
        lifecycle["residual_position_ticket"] = getattr(trade, "ticket", None)
        lifecycle["residual_volume"] = current_volume
        lifecycle["residual_broker_stop_loss"] = broker_stop_loss
        lifecycle["residual_broker_take_profit"] = broker_take_profit
        lifecycle["residual_risk_released"] = residual_risk_released

        instrumentation = self._active_trade_record.setdefault("instrumentation", {})
        instrumentation["gtos_vnext_active_lifecycle_truth_status"] = (
            "residual_open_lifecycle_update_persisted"
        )
        instrumentation["gtos_vnext_active_lifecycle_last_result"] = str(lifecycle_result)
        instrumentation["gtos_vnext_active_lifecycle_update_utc"] = updated_at
        instrumentation["gtos_vnext_recovered_partial_closed"] = partial_closed
        instrumentation["gtos_vnext_recovered_residual_open"] = True
        if partial_events:
            instrumentation["gtos_vnext_recovered_partial_close_events"] = partial_events

        try:
            saved_path = save_trade_record(
                self._active_trade_record,
                self.config.get("trade_capture", {}).get(
                    "base_path", "knowledge_base/trade_records",
                ),
            )
            if saved_path:
                self._active_trade_record_path = saved_path
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Active lifecycle trade-record update failed (non-blocking): %s",
                exc,
            )

    def _vnext_ltf_pending_monitor_enabled(self) -> bool:
        cfg = self._gtos_vnext_runtime_cfg()
        return bool(
            cfg.get("enabled", False)
            and cfg.get("apply_to_execution", False)
            and cfg.get("ltf_path_execution_enabled", True)
            and cfg.get("ltf_path_execution_apply_to_execution", False)
            and cfg.get("ltf_path_monitor_pending_intent_enabled", True)
        )

    def _check_pending_limit_ltf_path(self, *, check_context: str) -> bool:
        """Check an active pending limit on the configured LTF cadence.

        Returns True when an LTF check was attempted so callers can avoid doing
        a redundant M15 check in the same loop tick.
        """
        if not self.execution.pending_intent or not self._vnext_ltf_pending_monitor_enabled():
            return False
        cfg = self._gtos_vnext_runtime_cfg()
        timeframe = str(cfg.get("ltf_path_monitor_timeframe", "M1") or "M1").upper()
        try:
            tf_const = TF_MAP.get(timeframe) or {"M1": 1, "M5": 5}.get(timeframe)
            if tf_const is None:
                return False
            candles = self.mt5.get_candles(
                self._mt5_symbol,
                tf_const,
                int(cfg.get("ltf_path_monitor_fetch_bars", 4) or 4),
            )
            if not candles:
                return False
            tick_anchor_price = None
            try:
                anchor_tick = self.mt5.get_tick(self._mt5_symbol)
                tick_anchor_price = getattr(anchor_tick, "bid", None)
            except Exception:  # noqa: BLE001
                tick_anchor_price = None
            candles, ltf_ohlc_repair = repair_malformed_ohlc_from_ticks(
                candles,
                self._symbol,
                timeframe,
                self.config,
                anchor_price=tick_anchor_price,
            )
            candle = self._latest_closed_ltf_candle(candles, timeframe)
            if candle is None:
                return False
            candle_time = candle.get("time")
            repair_status = (
                (candle.get("ohlc_source_repair") or {}).get("status")
                if isinstance(candle, dict)
                else None
            )
            if str(repair_status or "").startswith("repair_failed"):
                self._last_ltf_limit_check_candle_time = candle_time
                logger.warning(
                    "Pending limit LTF check skipped: malformed %s candle repair failed "
                    "%s candle=%s report=%s",
                    timeframe,
                    self._symbol,
                    candle_time,
                    ltf_ohlc_repair,
                )
                return True
            if (
                candle_time
                and candle_time == getattr(self, "_last_ltf_limit_check_candle_time", None)
            ):
                return True
            self._last_ltf_limit_check_candle_time = candle_time
            pre_fill_trade_id = (
                self.execution.pending_intent.trade_id
                if self.execution.pending_intent else ""
            )
            pre_check_intent = self.execution.pending_intent
            self._archive_if_pending_limit_clock_expired(pre_check_intent)
            trade_state = self.execution.check_limit_fill(
                candle,
                telemetry_context={
                    "source_branch": "gtos_vnext_ltf_path_pending_monitor",
                    "check_context": check_context,
                    "kill_zone": self.session_state.get("current_kill_zone"),
                    "session": self.session_state.get("current_kill_zone"),
                    "source_symbol": self._mt5_symbol,
                    "source_timeframe": timeframe,
                    "latest_ltf_time_utc": candle_time,
                    "asof_cutoff_utc": candle_time,
                    "elapsed_candle_increment": 0,
                    "record_path": self._pending_trade_record_path,
                    "ltf_ohlc_repair": ltf_ohlc_repair,
                    "ltf_anchor_tick_bid": tick_anchor_price,
                },
            )
            if trade_state:
                self.session_state["trades_today"] += 1
                origin_kz = self.session_state.get("current_kill_zone")
                if origin_kz:
                    kz_key = f"trades_{origin_kz}"
                    self.session_state[kz_key] = self.session_state.get(kz_key, 0) + 1
                logger.info(
                    "LIMIT FILLED (vNext LTF path): %s at %.5f (origin_kz=%s)",
                    trade_state.trade_id,
                    trade_state.entry_price,
                    origin_kz or "unknown",
                )
                notify_limit_filled(
                    symbol=self._symbol,
                    direction=trade_state.direction,
                    entry=trade_state.entry_price,
                    trade_id=trade_state.trade_id,
                    sl=trade_state.stop_loss,
                    tp=trade_state.take_profit_1,
                    outside_kz=check_context != "inside_kz_ltf_sleep",
                    vnext_context=build_vnext_notification_context(
                        trade_state,
                        lifecycle_event="fill",
                    ),
                )
                self._promote_pending_record_on_fill()
                try:
                    self._init_trade_tracking(trade_state)
                except Exception as e:
                    logger.error("Exit tracking init failed on vNext LTF limit fill: %s", e)
            elif self.execution.pending_intent is None:
                self._clear_pending_trade_record(
                    pre_fill_trade_id,
                    reason="vnext_ltf_path_no_fill",
                )
            return True
        except Exception as e:
            logger.warning("vNext LTF pending monitor failed: %s", e)
            return False

    def _check_pending_limit_outside_kz(self):
        """Check pending limit fills outside kill zone hours.

        During KZs, _process_candle() handles limit checks. Between/after KZs,
        pending limits would otherwise go unchecked until the next KZ opens.
        Pulls the latest M15 candles from MT5 and selects the latest CLOSED
        candle. MT5 position 0 can be the currently-forming bar; checking and
        de-duping that bar early can miss a later high/low that touches a
        pending limit before the candle closes.
        """
        if not self.execution.pending_intent:
            return
        try:
            if self._check_pending_limit_ltf_path(check_context="outside_kz_ltf"):
                return
            candles = self.mt5.get_candles(self._mt5_symbol, TF_MAP["M15"], 3)
            if not candles:
                return
            tick_anchor_price = None
            try:
                anchor_tick = self.mt5.get_tick(self._mt5_symbol) if self.mt5 else None
                tick_anchor_price = getattr(anchor_tick, "bid", None)
            except Exception:  # noqa: BLE001
                tick_anchor_price = None
            candles, m15_ohlc_repair = repair_malformed_ohlc_from_ticks(
                candles,
                self._symbol,
                "M15",
                self.config,
                anchor_price=tick_anchor_price,
            )
            candle = self._latest_closed_m15_candle(candles)
            if candle is None:
                return

            # Avoid re-checking the same candle repeatedly
            candle_time = candle.get("time")
            repair_status = (
                (candle.get("ohlc_source_repair") or {}).get("status")
                if isinstance(candle, dict)
                else None
            )
            if str(repair_status or "").startswith("repair_failed"):
                self._last_limit_check_candle_time = candle_time
                logger.warning(
                    "Pending limit M15 check skipped: malformed candle repair failed "
                    "%s candle=%s report=%s",
                    self._symbol,
                    candle_time,
                    m15_ohlc_repair,
                )
                return
            if candle_time and candle_time == getattr(self, "_last_limit_check_candle_time", None):
                return
            self._last_limit_check_candle_time = candle_time

            # Capture intent trade_id BEFORE check_limit_fill can clear it
            pre_fill_trade_id = (
                self.execution.pending_intent.trade_id
                if self.execution.pending_intent else ""
            )
            pre_check_intent = self.execution.pending_intent
            self._archive_if_pending_limit_clock_expired(pre_check_intent)
            trade_state = self.execution.check_limit_fill(
                candle,
                telemetry_context={
                    "source_branch": "outside_kz_pending_check",
                    "check_context": "outside_kz",
                    "kill_zone": self.session_state.get("current_kill_zone"),
                    "session": self.session_state.get("current_kill_zone"),
                    "source_symbol": self._mt5_symbol,
                    "last_limit_check_candle_time_before": candle_time,
                    "latest_m15_time_utc": candle.get("time"),
                    "asof_cutoff_utc": candle.get("time"),
                    "record_path": self._pending_trade_record_path,
                    "m15_ohlc_repair": m15_ohlc_repair,
                    "m15_anchor_tick_bid": tick_anchor_price,
                },
            )
            if trade_state:
                self.session_state["trades_today"] += 1
                # Attribute trade to the KZ where the limit was originally placed
                origin_kz = self.session_state.get("current_kill_zone")
                if origin_kz:
                    kz_key = f"trades_{origin_kz}"
                    self.session_state[kz_key] = self.session_state.get(kz_key, 0) + 1
                logger.info(
                    "LIMIT FILLED (outside KZ): %s at %.5f (origin_kz=%s)",
                    trade_state.trade_id, trade_state.entry_price,
                    origin_kz or "unknown",
                )
                notify_limit_filled(
                    symbol=self._symbol, direction=trade_state.direction,
                    entry=trade_state.entry_price, trade_id=trade_state.trade_id,
                    sl=trade_state.stop_loss, tp=trade_state.take_profit_1,
                    outside_kz=True,
                    vnext_context=build_vnext_notification_context(
                        trade_state,
                        lifecycle_event="fill",
                    ),
                )
                self._promote_pending_record_on_fill()
                try:
                    self._init_trade_tracking(trade_state)
                except Exception as e:
                    logger.error("Exit tracking init failed on outside-KZ limit fill: %s", e)
            elif self.execution.pending_intent is None:
                # Intent cleared without a fill (expiry / wrong-side / SL-too-close).
                self._clear_pending_trade_record(
                    pre_fill_trade_id, reason="outside_kz_no_fill",
                )
        except Exception as e:
            logger.warning("Outside-KZ limit check failed: %s", e)

    def _archive_expired_poi_watch(self, intent, reason: str) -> None:
        """Archive an eligible cancelled pending limit as a structural POI watch.

        Observation-only. This never arms a new order; it only preserves the
        POI geometry so later candles can be revalidated in shadow logs.
        """
        cfg = self.config.get("expired_poi_watch", {}) if isinstance(self.config, dict) else {}
        if not cfg.get("enabled", False) or str(cfg.get("mode", "shadow")).lower() == "off":
            return
        try:
            record_path = self._pending_trade_record_path
            if not record_path and intent is not None:
                base_path = self.config.get("trade_capture", {}).get(
                    "base_path", "knowledge_base/trade_records",
                )
                record_path = lookup_pending_record(
                    getattr(intent, "trade_id", ""), self._symbol, base_path,
                )

            record = None
            if record_path and Path(record_path).exists():
                try:
                    record = load_trade_record(record_path)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "expired_poi_watch: failed to load source record %s: %s",
                        record_path, exc,
                    )

            watch = archive_expired_pending_intent(
                record=record,
                intent=intent,
                cancel_reason=reason,
                config=self.config,
                record_path=record_path,
            )
            if watch:
                logger.warning(
                    "EXPIRED_POI_WATCH_CREATED: %s %s %s entry=%.5f sl=%.5f "
                    "tp=%.5f reason=%s mode=%s",
                    watch.get("watch_id"),
                    watch.get("symbol"),
                    watch.get("side"),
                    float(watch.get("entry_price") or 0.0),
                    float(watch.get("stop_loss") or 0.0),
                    float(watch.get("take_profit_1") or 0.0),
                    reason,
                    watch.get("mode"),
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("expired_poi_watch archive failed (non-blocking): %s", exc)

    def _archive_if_pending_limit_clock_expired(self, intent) -> None:
        """Archive 48h-expiring executable intents before ExecutionEngine clears them."""
        if intent is None:
            return
        try:
            placed = datetime.fromisoformat(str(intent.placed_time).replace("Z", "+00:00"))
            if placed.tzinfo is None:
                placed = placed.replace(tzinfo=timezone.utc)
            else:
                placed = placed.astimezone(timezone.utc)
            if datetime.now(timezone.utc) - placed >= timedelta(hours=48):
                self._archive_expired_poi_watch(intent, "48h clock expiry")
        except Exception as exc:  # noqa: BLE001
            logger.warning("expired_poi_watch 48h pre-archive failed: %s", exc)

    def _monitor_expired_poi_watches(self, raw_data: dict, kill_zone: str) -> None:
        """Evaluate active expired-POI watches on the latest closed M15 candle."""
        cfg = self.config.get("expired_poi_watch", {}) if isinstance(self.config, dict) else {}
        if not cfg.get("enabled", False) or str(cfg.get("mode", "shadow")).lower() == "off":
            return
        try:
            m15_candles = (raw_data.get("candles", {}) or {}).get("M15", [])
            candle = self._latest_closed_m15_candle(m15_candles) if m15_candles else None
            tick = self.mt5.get_tick(self._mt5_symbol) if self.mt5 else None
            rows = _evaluate_expired_poi_watches(
                symbol=self._symbol,
                candle=candle,
                bid=getattr(tick, "bid", None) if tick else None,
                ask=getattr(tick, "ask", None) if tick else None,
                config=self.config,
                kill_zone=kill_zone,
                log_all=bool(cfg.get("log_all_revalidations", False)),
            )
            self._log_expired_poi_watch_rows(rows)
        except Exception as exc:  # noqa: BLE001
            logger.warning("expired_poi_watch monitor failed (non-blocking): %s", exc)

    def _monitor_expired_poi_watches_from_mt5(self, kill_zone: str) -> None:
        """Evaluate expired-POI watches outside normal candle processing."""
        cfg = self.config.get("expired_poi_watch", {}) if isinstance(self.config, dict) else {}
        if not cfg.get("enabled", False) or str(cfg.get("mode", "shadow")).lower() == "off":
            return
        try:
            from src.components.data_ingestion import TF_MAP

            candles = self.mt5.get_candles(self._mt5_symbol, TF_MAP["M15"], 3)
            candle = self._latest_closed_m15_candle(candles) if candles else None
            tick = self.mt5.get_tick(self._mt5_symbol) if self.mt5 else None
            rows = _evaluate_expired_poi_watches(
                symbol=self._symbol,
                candle=candle,
                bid=getattr(tick, "bid", None) if tick else None,
                ask=getattr(tick, "ask", None) if tick else None,
                config=self.config,
                kill_zone=kill_zone,
                log_all=bool(cfg.get("log_all_revalidations", False)),
            )
            self._log_expired_poi_watch_rows(rows)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "expired_poi_watch outside-KZ monitor failed (non-blocking): %s",
                exc,
            )

    def _log_expired_poi_watch_rows(self, rows: list[dict]) -> None:
        for row in rows:
            status = row.get("status")
            if status in _EXPIRED_POI_INTERESTING_STATUSES:
                logger.warning(
                    "EXPIRED_POI_WATCH_%s: %s %s entry=%.5f current=%.5f "
                    "rr_current=%s reason=%s",
                    status,
                    row.get("symbol"),
                    row.get("side"),
                    float(row.get("entry_price") or 0.0),
                    float(row.get("current_price") or 0.0),
                    row.get("risk_reward_at_current"),
                    row.get("reason"),
                )

    @staticmethod
    def _latest_closed_m15_candle(
        candles: list[dict],
        now: Optional[datetime] = None,
    ) -> Optional[dict]:
        """Return the newest M15 candle whose close time has passed."""
        ref = now or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        else:
            ref = ref.astimezone(timezone.utc)

        for candle in reversed(candles):
            raw_time = candle.get("time")
            if not raw_time:
                continue
            try:
                opened = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
            except ValueError:
                continue
            if opened.tzinfo is None:
                opened = opened.replace(tzinfo=timezone.utc)
            else:
                opened = opened.astimezone(timezone.utc)
            if opened + timedelta(minutes=15) <= ref + timedelta(seconds=2):
                return candle
        return None

    def _compute_mfe_mae_m5(
        self,
        entry_price: float | None,
        direction: str | None,
        entry_time: datetime | None,
        exit_time: datetime | None,
        sl_distance: float | None,
    ) -> dict | None:
        """Compute MFE/MAE from M5 bar data between entry and exit.

        Returns dict with mfe_r_m5, mae_r_m5, mfe_time_minutes, mae_time_minutes
        or None if data unavailable.
        """
        if not all([entry_price, direction, entry_time, exit_time, sl_distance]):
            return None
        if sl_distance <= 0:
            return None

        try:
            from src.components.data_ingestion import TF_M5
            rates = self.mt5.get_candles_range(
                self._mt5_symbol, TF_M5, entry_time, exit_time,
            )
            if not rates:
                return None

            max_fav = 0.0
            max_adv = 0.0
            mfe_ts = entry_time
            mae_ts = entry_time
            window_rates = self._m5_rates_inside_trade_window(
                rates, entry_time, exit_time,
            )
            if not window_rates:
                return None

            for bar, bar_time in window_rates:
                if direction == "LONG":
                    fav = (bar["high"] - entry_price) / sl_distance
                    adv = (entry_price - bar["low"]) / sl_distance
                else:
                    fav = (entry_price - bar["low"]) / sl_distance
                    adv = (bar["high"] - entry_price) / sl_distance

                if fav > max_fav:
                    max_fav = fav
                    mfe_ts = bar_time
                if adv > max_adv:
                    max_adv = adv
                    mae_ts = bar_time

            mfe_min = int((mfe_ts - entry_time).total_seconds() / 60)
            mae_min = int((mae_ts - entry_time).total_seconds() / 60)

            result = {
                "mfe_r_m5": round(max_fav, 3),
                "mae_r_m5": round(-max_adv, 3),
                "mfe_time_minutes": mfe_min,
                "mae_time_minutes": mae_min,
            }
            logger.info(
                "M5 MFE/MAE: MFE=+%.3fR @%dmin, MAE=%.3fR @%dmin (%d M5 bars)",
                max_fav, mfe_min, -max_adv, mae_min, len(window_rates),
            )
            return result
        except Exception as e:
            logger.warning("M5 MFE/MAE computation failed: %s", e)
            return None

    @staticmethod
    def _bar_time_utc(value) -> Optional[datetime]:
        if value is None:
            return None
        try:
            if isinstance(value, datetime):
                dt = value
            elif isinstance(value, str):
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            else:
                dt = datetime.fromtimestamp(float(value), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _m5_rates_inside_trade_window(
        self,
        rates,
        entry_time,
        exit_time,
    ) -> list[tuple[dict, datetime]]:
        entry_dt = self._parse_utc_datetime(entry_time)
        exit_dt = self._parse_utc_datetime(exit_time)
        if entry_dt is None or exit_dt is None or exit_dt < entry_dt:
            return []
        result: list[tuple[dict, datetime]] = []
        exit_tolerance = timedelta(seconds=2)
        for bar in rates or []:
            if not isinstance(bar, dict):
                continue
            bar_time = self._bar_time_utc(bar.get("time"))
            if bar_time is None:
                continue
            bar_close_time = bar_time + timedelta(minutes=5)
            if bar_time < entry_dt:
                continue
            if bar_close_time > exit_dt + exit_tolerance:
                continue
            result.append((bar, bar_time))
        return result

    @staticmethod
    def _parse_utc_datetime(value) -> Optional[datetime]:
        if not value:
            return None
        datetime_type = _datetime_module.datetime
        if isinstance(value, datetime_type):
            dt = value
        else:
            try:
                dt = datetime_type.fromisoformat(str(value).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _finite_float_or_none(value) -> float | None:
        try:
            if value in (None, ""):
                return None
            number = float(value)
        except (TypeError, ValueError):
            return None
        return number if math.isfinite(number) else None

    def _resolve_exit_sl_distance(self, trade_snapshot) -> tuple[float | None, str]:
        """Resolve immutable entry-risk distance for terminal exit R math.

        Mutable broker stops can be moved to breakeven while a trade is open.
        Exit/shadow accounting must keep using the original entry-to-stop
        distance, otherwise BE-managed positions can produce near-zero
        denominators and impossible R multiples.
        """
        record = self._active_trade_record if isinstance(self._active_trade_record, dict) else {}
        execution = record.get("execution") if isinstance(record, dict) else None
        limit_intent = record.get("limit_intent") if isinstance(record, dict) else None
        instrumentation = record.get("instrumentation") if isinstance(record, dict) else None

        candidates: list[tuple[str, float]] = []

        def _add(source: str, value) -> None:
            number = self._finite_float_or_none(value)
            if number is not None and number > 1e-9:
                candidates.append((source, number))

        if isinstance(instrumentation, dict):
            for event in instrumentation.get("gtos_vnext_recovered_partial_close_events") or []:
                if isinstance(event, dict):
                    _add(
                        "instrumentation.gtos_vnext_recovered_partial_close_events.sl_distance",
                        event.get("sl_distance"),
                    )

        if isinstance(execution, dict):
            for key in (
                "original_sl_distance",
                "entry_sl_distance",
                "initial_sl_distance",
                "sl_distance",
            ):
                _add(f"execution.{key}", execution.get(key))
            entry = self._finite_float_or_none(
                execution.get("entry_price") or execution.get("executed_entry_price")
            )
            stop = self._finite_float_or_none(execution.get("stop_loss"))
            if entry is not None and stop is not None and abs(entry - stop) > 1e-9:
                _add("execution.entry_stop_distance", abs(entry - stop))

        if isinstance(limit_intent, dict):
            entry = self._finite_float_or_none(
                limit_intent.get("limit_price") or limit_intent.get("entry_price")
            )
            stop = self._finite_float_or_none(limit_intent.get("stop_loss"))
            if entry is not None and stop is not None and abs(entry - stop) > 1e-9:
                _add("limit_intent.entry_stop_distance", abs(entry - stop))

        if candidates:
            # Within immutable sources, prefer the largest positive distance.
            # This protects recovered records whose current BE stop appears
            # alongside original geometry.
            source, value = max(candidates, key=lambda item: item[1])
            return value, source

        _add("trade_snapshot.sl_distance", getattr(trade_snapshot, "sl_distance", None))
        _add("orchestrator._trade_sl_distance", self._trade_sl_distance)
        if candidates:
            source, value = max(candidates, key=lambda item: item[1])
            return value, source
        return None, "missing_positive_exit_sl_distance"

    def _entry_time_for_exit(self, exit_time: datetime) -> tuple[Optional[datetime], str, str]:
        """Resolve a source-backed entry time for exit telemetry."""
        exit_time = self._parse_utc_datetime(exit_time) or datetime.now(timezone.utc)
        entry_time = self._parse_utc_datetime(self._trade_entry_time)
        if entry_time and entry_time <= exit_time:
            return entry_time, "trade_state_entry_time", "ENTRY_AND_CLOSE_TIME_CAPTURED"

        execution = {}
        if isinstance(self._active_trade_record, dict):
            execution = self._active_trade_record.get("execution", {}) or {}
        fill_time = self._parse_utc_datetime(execution.get("fill_time_utc"))
        if fill_time and fill_time <= exit_time:
            return (
                fill_time,
                "trade_record_execution_fill_time_utc",
                "ENTRY_TIME_FUTURE_REPAIRED_FROM_EXECUTION_FILL_TIME",
            )

        if entry_time:
            return (
                entry_time,
                "trade_state_entry_time",
                "ENTRY_TIME_AFTER_CLOSE_UNRESOLVED",
            )
        return None, "missing_entry_time", "ENTRY_TIME_SOURCE_MISSING"

    def _partial_close_event_candidates_for_exit(self, trade_snapshot) -> list[dict]:
        """Collect in-memory and recovered partial events for terminal exits."""
        candidates: list[dict] = []

        def _extend(events, source: str) -> None:
            if not isinstance(events, list):
                return
            for event in events:
                if not isinstance(event, dict):
                    continue
                copy = dict(event)
                copy.setdefault("terminal_exit_event_source", source)
                candidates.append(copy)

        _extend(
            getattr(trade_snapshot, "partial_close_events", None),
            "trade_snapshot.partial_close_events",
        )

        record = self._active_trade_record if isinstance(self._active_trade_record, dict) else {}
        execution = record.get("execution") if isinstance(record, dict) else None
        if isinstance(execution, dict):
            _extend(
                execution.get("partial_close_events"),
                "trade_record.execution.partial_close_events",
            )

        lifecycle = record.get("lifecycle") if isinstance(record, dict) else None
        if isinstance(lifecycle, dict):
            _extend(
                lifecycle.get("active_trade_management_events"),
                "trade_record.lifecycle.active_trade_management_events",
            )

        instrumentation = record.get("instrumentation") if isinstance(record, dict) else None
        if isinstance(instrumentation, dict):
            _extend(
                instrumentation.get("gtos_vnext_recovered_partial_close_events"),
                "trade_record.instrumentation.gtos_vnext_recovered_partial_close_events",
            )

        return candidates

    def _partial_close_records_for_exit(self, trade_snapshot) -> list[dict]:
        """Build canonical partial-close rows, including recovered lifecycle events."""
        initial_volume = self._finite_float_or_none(
            getattr(trade_snapshot, "initial_volume", None)
        )
        partial_close_records: list[dict] = []
        seen_keys: set[tuple] = set()

        for evt in self._partial_close_event_candidates_for_exit(trade_snapshot):
            evt_type = str(evt.get("type") or evt.get("close_event_type") or "")
            if "PARTIAL" not in evt_type.upper():
                continue
            price = self._finite_float_or_none(
                evt.get("price") if evt.get("price") is not None else evt.get("fill_price")
            )
            volume_closed = self._finite_float_or_none(
                evt.get("volume_closed")
                if evt.get("volume_closed") is not None
                else evt.get("lots_closed")
            )
            if price is None or volume_closed is None or volume_closed <= 0:
                continue
            event_initial_volume = self._finite_float_or_none(evt.get("initial_volume"))
            effective_initial_volume = initial_volume
            if (
                event_initial_volume is not None
                and event_initial_volume > 0
                and (
                    effective_initial_volume is None
                    or event_initial_volume > effective_initial_volume
                )
            ):
                effective_initial_volume = event_initial_volume
            if effective_initial_volume is None or effective_initial_volume <= 0:
                continue

            order_id = evt.get("mt5_order_id") or evt.get("order_ticket") or evt.get("order")
            deal_id = evt.get("mt5_deal_id") or evt.get("deal_ticket") or evt.get("deal")
            if deal_id:
                key = ("deal", deal_id)
            elif order_id:
                key = ("order", order_id, round(volume_closed, 8), round(price, 8))
            else:
                key = (
                    "event",
                    evt.get("time") or evt.get("close_time") or evt.get("ts"),
                    round(volume_closed, 8),
                    round(price, 8),
                )
            if key in seen_keys:
                continue
            seen_keys.add(key)

            pct = volume_closed / effective_initial_volume
            if not math.isfinite(pct) or pct <= 0:
                continue
            pct = min(pct, 1.0)
            lots_remaining = self._finite_float_or_none(
                evt.get("remaining_volume")
                if evt.get("remaining_volume") is not None
                else evt.get("lots_remaining")
            )
            if lots_remaining is None:
                lots_remaining = max(effective_initial_volume - volume_closed, 0.0)
            r_at_close = self._finite_float_or_none(evt.get("r_at_close"))
            computed_r_at_close = self._compute_r(price)
            if r_at_close is None or abs(r_at_close) > 100:
                r_at_close = computed_r_at_close
            partial_close_records.append({
                "type": evt_type or "TP1_PARTIAL",
                "price": price,
                "lots_closed": volume_closed,
                "lots_remaining": lots_remaining,
                "pct_closed": round(pct, 4),
                "r_at_close": round(r_at_close, 4),
                "time": evt.get("time") or evt.get("close_time") or evt.get("ts") or "",
                "close_reason": evt.get("close_reason"),
                "mt5_order_id": evt.get("mt5_order_id") or evt.get("order_ticket") or evt.get("order"),
                "mt5_deal_id": evt.get("mt5_deal_id") or evt.get("deal_ticket") or evt.get("deal"),
                "commission": evt.get("commission"),
                "swap": evt.get("swap"),
                "sl_at_breakeven": evt.get("sl_at_breakeven"),
                "time_in_trade_minutes": evt.get("time_in_trade_minutes"),
                "terminal_exit_event_source": evt.get("terminal_exit_event_source"),
            })

        return partial_close_records

    def _mark_active_trade_record_terminal_lifecycle_closed(
        self,
        *,
        trade_snapshot,
        exit_type: str,
        exit_time: datetime,
        partial_close_records: list[dict],
    ) -> None:
        """Clear residual-open lifecycle state after a confirmed terminal exit."""
        if not isinstance(self._active_trade_record, dict):
            return
        updated_at = exit_time.isoformat()
        terminal_result = f"terminal_exit_{exit_type}"

        execution = self._active_trade_record.setdefault("execution", {})
        if isinstance(execution, dict):
            execution["current_volume"] = 0.0
            execution["broker_stop_loss"] = None
            execution["active_stop_loss"] = None
            execution["broker_take_profit"] = None
            execution["active_take_profit"] = None
            execution["last_lifecycle_result"] = terminal_result
            execution["last_lifecycle_update_utc"] = updated_at
            execution["active_lifecycle_capture_status"] = (
                "terminal_exit_persisted_from_finalize_exit"
            )
            execution["terminal_exit_type"] = exit_type
            execution["terminal_exit_time_utc"] = updated_at
            execution["residual_worst_case_cash_risk_amount"] = 0.0
            execution["residual_worst_case_cash_risk_status"] = (
                "released_by_terminal_exit"
            )

        lifecycle = self._active_trade_record.setdefault("lifecycle", {})
        if isinstance(lifecycle, dict):
            previous_residual_state = {
                "residual_position_ticket": lifecycle.get("residual_position_ticket"),
                "residual_volume": lifecycle.get("residual_volume"),
                "residual_broker_stop_loss": lifecycle.get("residual_broker_stop_loss"),
                "residual_broker_take_profit": lifecycle.get("residual_broker_take_profit"),
                "residual_risk_released": lifecycle.get("residual_risk_released"),
                "broker_position_ticket": lifecycle.get("broker_position_ticket"),
                "broker_position_volume": lifecycle.get("broker_position_volume"),
                "broker_stop_loss": lifecycle.get("broker_stop_loss"),
                "broker_take_profit": lifecycle.get("broker_take_profit"),
                "broker_comment": lifecycle.get("broker_comment"),
                "open_worst_case_cash_risk_amount": lifecycle.get(
                    "open_worst_case_cash_risk_amount"
                ),
                "open_worst_case_cash_risk_status": lifecycle.get(
                    "open_worst_case_cash_risk_status"
                ),
                "last_lifecycle_result": lifecycle.get("last_lifecycle_result"),
                "last_lifecycle_update_utc": lifecycle.get("last_lifecycle_update_utc"),
            }
            if any(value is not None for value in previous_residual_state.values()):
                lifecycle.setdefault(
                    "previous_residual_open_state_before_terminal_exit",
                    previous_residual_state,
                )
            lifecycle["last_lifecycle_result"] = terminal_result
            lifecycle["last_lifecycle_update_utc"] = updated_at
            lifecycle["residual_position_ticket"] = getattr(trade_snapshot, "ticket", None)
            lifecycle["residual_volume"] = 0.0
            lifecycle["residual_broker_stop_loss"] = None
            lifecycle["residual_broker_take_profit"] = None
            lifecycle["residual_risk_released"] = True
            lifecycle["broker_position_ticket"] = getattr(trade_snapshot, "ticket", None)
            lifecycle["broker_position_volume"] = 0.0
            lifecycle["broker_stop_loss"] = None
            lifecycle["broker_take_profit"] = None
            lifecycle["broker_comment"] = None
            lifecycle["open_worst_case_cash_risk_amount"] = 0.0
            lifecycle["open_worst_case_cash_risk_status"] = (
                "released_by_terminal_exit"
            )
            lifecycle["terminal_exit_type"] = exit_type
            lifecycle["terminal_exit_time_utc"] = updated_at
            if partial_close_records:
                lifecycle["terminal_exit_partial_close_records"] = partial_close_records

        instrumentation = self._active_trade_record.setdefault("instrumentation", {})
        if isinstance(instrumentation, dict):
            instrumentation["gtos_vnext_active_lifecycle_truth_status"] = (
                "terminal_exit_lifecycle_update_persisted"
            )
            instrumentation["gtos_vnext_active_lifecycle_last_result"] = terminal_result
            instrumentation["gtos_vnext_active_lifecycle_update_utc"] = updated_at
            instrumentation["gtos_vnext_recovered_residual_open"] = False
            if partial_close_records:
                instrumentation["gtos_vnext_recovered_partial_closed"] = True

    def _finalize_exit(self, trade_snapshot, exit_type: str):
        """Build exit data from trade snapshot and save to the trade record."""
        try:
            resolved_sl_distance, resolved_sl_source = self._resolve_exit_sl_distance(
                trade_snapshot
            )
            if resolved_sl_distance is not None:
                self._trade_sl_distance = resolved_sl_distance
            exit_price = self._last_tick_price or self._trade_entry_price or 0
            exit_time_override: Optional[datetime] = None
            broker_deal_used = False
            broker_closing_deal: Optional[dict] = None
            broker_position_deals: list[dict] = []
            broker_position_profit: Optional[float] = None
            broker_position_commission: Optional[float] = None
            broker_position_swap: Optional[float] = None
            broker_position_net_profit: Optional[float] = None

            # Broker-closed reconciliation (2026-04-29):
            # When MT5 closes a position externally (TP/SL hit during dead-zone,
            # daemon-side force-close, manual close), the orchestrator's M15
            # detection runs LATER and previously used ``self._last_tick_price``
            # (current bid) as exit_price + ``datetime.now(UTC)`` as exit_time.
            # On 2026-04-28 that produced a -0.0365R record for a trade that
            # actually exited at +0.738R hours earlier — the wrong bid at the
            # wrong time. Fix: query MT5 for the actual closing deal (matched
            # by position_id, filtered to DEAL_ENTRY_OUT) and use its price +
            # time. Falls back to the old detection-time bid if MT5 returns
            # nothing (graceful — never blocks the close path).
            if exit_type == "broker_closed" and trade_snapshot.ticket:
                try:
                    from datetime import timedelta
                    now_utc = datetime.now(timezone.utc)
                    deals = self.mt5.get_history_deals(
                        now_utc - timedelta(days=30),
                        now_utc + timedelta(minutes=5),
                        self._mt5_symbol,
                    )
                    broker_position_deals = [
                        d for d in (deals or [])
                        if d.get("position_id") == trade_snapshot.ticket
                    ]
                    closing_deals = [
                        d for d in broker_position_deals
                        if d.get("position_id") == trade_snapshot.ticket
                        and d.get("entry") == 1  # DEAL_ENTRY_OUT
                    ]
                    if closing_deals:
                        # Most recent closing deal — handles partial-then-full closes.
                        closing = max(closing_deals, key=lambda d: d["time"])
                        broker_closing_deal = closing
                        exit_price = float(closing["price"])
                        exit_time_override = closing["time"]
                        broker_deal_used = True
                        broker_position_profit = round(sum(
                            float(d.get("profit") or 0.0)
                            for d in broker_position_deals
                        ), 8)
                        broker_position_commission = round(sum(
                            float(d.get("commission") or 0.0)
                            for d in broker_position_deals
                        ), 8)
                        broker_position_swap = round(sum(
                            float(d.get("swap") or 0.0)
                            for d in broker_position_deals
                        ), 8)
                        broker_position_net_profit = round(
                            broker_position_profit
                            + broker_position_commission
                            + broker_position_swap,
                            8,
                        )
                        logger.info(
                            "broker_closed: reconciled from MT5 deal — "
                            "ticket=%d exit=%.5f at %s (was bid %.5f at %s)",
                            trade_snapshot.ticket, exit_price,
                            exit_time_override.isoformat(),
                            self._last_tick_price or 0.0,
                            now_utc.isoformat(),
                        )
                    else:
                        logger.warning(
                            "broker_closed: no MT5 closing deal found for "
                            "ticket=%d in last 24h — falling back to "
                            "detection-time bid (record may be stale)",
                            trade_snapshot.ticket,
                        )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "broker_closed: MT5 deal query failed (%s) — "
                        "falling back to detection-time bid",
                        exc,
                    )

            partial_close_records = self._partial_close_records_for_exit(trade_snapshot)

            for evt in (getattr(trade_snapshot, "partial_close_events", None) or []):
                if not isinstance(evt, dict) or "price" not in evt or not evt.get("volume_closed"):
                    continue
                evt_type = evt.get("type", "")
                if "PARTIAL" in str(evt_type).upper():
                    continue
                # Full close event source from the live snapshot.
                exit_price = evt["price"]

            if partial_close_records:
                blended_r = 0.0
                total_partial_pct = sum(pc["pct_closed"] for pc in partial_close_records)
                for pc in partial_close_records:
                    blended_r += pc["r_at_close"] * pc["pct_closed"]
                final_pct = max(0.0, 1.0 - total_partial_pct)
                if final_pct > 0:
                    blended_r += self._compute_r(exit_price) * final_pct
                actual_r = blended_r
            else:
                actual_r = self._compute_r(exit_price)

            # Prefer the actual MT5 close time (set above for broker_closed via
            # deal reconciliation) over the orchestrator's detection time.
            exit_time = exit_time_override or datetime.now(timezone.utc)
            entry_time_for_exit, entry_time_source, hold_time_status = (
                self._entry_time_for_exit(exit_time)
            )
            hold_minutes: Optional[int] = None
            if entry_time_for_exit:
                hold_minutes = int(
                    (exit_time - entry_time_for_exit).total_seconds() / 60
                )
                if hold_minutes < 0:
                    hold_minutes = None
                    hold_time_status = "ENTRY_TIME_AFTER_CLOSE_UNRESOLVED"

            if broker_closing_deal:
                try:
                    record_close_slippage(
                        ticket=trade_snapshot.ticket,
                        symbol=self._symbol,
                        direction=self._trade_direction or trade_snapshot.direction,
                        requested_price=None,
                        fill_price=exit_price,
                        close_reason=exit_type,
                        close_event_type="BROKER_CLOSED_DEAL_RECONCILIATION",
                        volume_closed=broker_closing_deal.get("volume"),
                        initial_volume=getattr(trade_snapshot, "initial_volume", None),
                        remaining_volume=0.0,
                        entry_price=self._trade_entry_price or trade_snapshot.entry_price,
                        stop_loss=trade_snapshot.stop_loss,
                        sl_distance=self._trade_sl_distance or trade_snapshot.sl_distance,
                        entry_time=(
                            entry_time_for_exit.isoformat()
                            if entry_time_for_exit else trade_snapshot.entry_time
                        ),
                        sl_at_breakeven=getattr(trade_snapshot, "sl_at_breakeven", None),
                        partial_close=False,
                        mt5_order_id=broker_closing_deal.get("order"),
                        mt5_deal_id=broker_closing_deal.get("ticket"),
                        commission=broker_position_commission,
                        swap=broker_position_swap,
                        broker_profit=broker_position_profit,
                        close_comment=broker_closing_deal.get("comment"),
                        close_time=exit_time.isoformat(),
                        requested_price_status="SOURCE_NOT_CAPTURED_FOR_BROKER_CLOSED",
                        accounting_source="MT5_HISTORY_DEALS_READONLY",
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "broker_closed close-side telemetry failed (non-blocking): %s",
                        exc,
                    )

            # J46-J49 shadow logger (replays OLD policy on each closed trade).
            try:
                from src.components.j46_j49_shadow_logger import (
                    compute_j46_j49_shadow,
                    write_j46_j49_shadow_log,
                )
                from src.components.data_ingestion import TF_M1
                fill_id_for_shadow = (
                    self._active_trade_record.get("trade_id")
                    or self._active_trade_record.get("metadata", {}).get("trade_id", "")
                    or trade_snapshot.trade_id
                    or ""
                )

                def _fetch_m1(date_from, date_to):
                    try:
                        return self.mt5.get_candles_range(
                            self._mt5_symbol, TF_M1, date_from, date_to,
                        )
                    except Exception as fe:
                        logger.warning("j46_j49 M1 fetch failed: %s", fe)
                        return None

                shadow_entry_time = (
                    entry_time_for_exit
                    or self._parse_utc_datetime(getattr(trade_snapshot, "entry_time", ""))
                    or exit_time
                )
                shadow_row = compute_j46_j49_shadow(
                    fill_id=fill_id_for_shadow,
                    instrument=self._symbol,
                    direction=self._trade_direction or trade_snapshot.direction,
                    entry_time=shadow_entry_time,
                    exit_time=exit_time,
                    entry_price=self._trade_entry_price or trade_snapshot.entry_price,
                    original_sl=trade_snapshot.stop_loss,
                    original_ai_tp1=getattr(trade_snapshot, "original_ai_tp1", 0.0),
                    sl_distance=self._trade_sl_distance or trade_snapshot.sl_distance,
                    actual_exit_price=exit_price,
                    actual_exit_time=exit_time,
                    actual_r=actual_r,
                    actual_exit_reason=exit_type,
                    bar_fetcher=_fetch_m1,
                )
                write_j46_j49_shadow_log(shadow_row)
            except Exception as e:
                logger.warning("J46-J49 shadow logging failed (non-blocking): %s", e)

            exit_data = {
                "exit_type": exit_type,
                "exit_price": exit_price,
                "exit_time": exit_time.isoformat(),
                "actual_r": round(actual_r, 4),
                "r_denominator_source": resolved_sl_source,
                "r_sl_distance": (
                    round(float(resolved_sl_distance), 10)
                    if resolved_sl_distance is not None
                    else None
                ),
                "hold_time_minutes": hold_minutes,
                "hold_time_status": hold_time_status,
                "hold_time_entry_source": entry_time_source,
                "mfe_price": self._mfe_price,
                "mfe_r": round(self._compute_r(self._mfe_price), 4) if self._mfe_price else 0,
                "mae_price": self._mae_price,
                "mae_r": round(self._compute_r(self._mae_price), 4) if self._mae_price else 0,
                "partial_closes": partial_close_records,
                "close_reason": exit_type,
                "commission": broker_closing_deal.get("commission") if broker_closing_deal else None,
                "swap": broker_closing_deal.get("swap") if broker_closing_deal else None,
                "broker_profit": broker_closing_deal.get("profit") if broker_closing_deal else None,
                "broker_close_deal_profit": broker_closing_deal.get("profit") if broker_closing_deal else None,
                "broker_position_profit": broker_position_profit,
                "broker_position_commission": broker_position_commission,
                "broker_position_swap": broker_position_swap,
                "broker_position_net_profit": broker_position_net_profit,
                "broker_position_deal_count": len(broker_position_deals),
                "broker_close_deal_id": broker_closing_deal.get("ticket") if broker_closing_deal else None,
                "broker_close_order_id": broker_closing_deal.get("order") if broker_closing_deal else None,
                "broker_position_id": broker_closing_deal.get("position_id") if broker_closing_deal else None,
                "broker_close_reason": broker_closing_deal.get("reason") if broker_closing_deal else None,
                "broker_close_comment": broker_closing_deal.get("comment") if broker_closing_deal else None,
                # ``broker_deal_reconciled`` distinguishes records where
                # exit_price/exit_time came from MT5 deal history (true close)
                # vs detection-time bid (graceful fallback). Operators + audit
                # tools can filter by this flag.
                "broker_deal_reconciled": broker_deal_used,
            }

            update_exit(self._active_trade_record, exit_data)
            self._mark_active_trade_record_terminal_lifecycle_closed(
                trade_snapshot=trade_snapshot,
                exit_type=exit_type,
                exit_time=exit_time,
                partial_close_records=partial_close_records,
            )

            # Retroactive M5 MFE/MAE — fills gaps between tick polls
            m5_excursion = self._compute_mfe_mae_m5(
                entry_price=self._trade_entry_price,
                direction=self._trade_direction,
                entry_time=entry_time_for_exit,
                exit_time=exit_time,
                sl_distance=self._trade_sl_distance,
            )
            if m5_excursion:
                self._active_trade_record.setdefault("exit", {}).update(m5_excursion)

            # BE shadow log (H2 — observation only)
            try:
                if self._be_shadow_tracker and self._be_shadow_tracker.be_trigger_activated:
                    be_result = self._be_shadow_tracker.compute_hypothetical(
                        actual_exit_price=exit_price,
                        actual_r_multiple=actual_r,
                    )
                    if be_result:
                        write_be_shadow_log(be_result)
                        self._active_trade_record.setdefault("shadow", {})["be_shadow"] = be_result
            except Exception as e:
                logger.warning("BE shadow logging failed (non-blocking): %s", e)

            # Time-in-trade shadow log (T5.4 — observation only)
            try:
                from src.components.data_ingestion import TF_M15
                trade_id_for_log = (
                    self._active_trade_record.get("trade_id")
                    or self._active_trade_record.get("metadata", {}).get("trade_id", "")
                )

                def _fetch_m15(date_from, date_to):
                    try:
                        return self.mt5.get_candles_range(
                            self._mt5_symbol, TF_M15, date_from, date_to,
                        )
                    except Exception as fe:
                        logger.warning("time_in_trade bar fetch failed: %s", fe)
                        return None

                tit_result = compute_time_in_trade_hypotheticals(
                    trade_id=trade_id_for_log,
                    symbol=self._symbol,
                    direction=self._trade_direction,
                    entry_time=entry_time_for_exit,
                    close_time=exit_time,
                    entry_price=self._trade_entry_price,
                    sl_distance=self._trade_sl_distance,
                    actual_close_r=actual_r,
                    bar_fetcher=_fetch_m15,
                )
                if tit_result:
                    write_time_in_trade_shadow_log(tit_result)
                    self._active_trade_record.setdefault("shadow", {})["time_in_trade"] = tit_result
            except Exception as e:
                logger.warning("Time-in-trade shadow logging failed (non-blocking): %s", e)

            # Variant C partial close shadow log (observation only)
            try:
                if self._partial_close_shadow_tracker and self._partial_close_shadow_tracker.trigger_activated:
                    pc_result = self._partial_close_shadow_tracker.compute_hypothetical(
                        actual_exit_price=exit_price,
                        actual_r_multiple=actual_r,
                    )
                    if pc_result:
                        write_partial_close_shadow_log(pc_result)
                        self._active_trade_record.setdefault("shadow", {})["partial_close"] = pc_result
            except Exception as e:
                logger.warning("Partial close shadow logging failed (non-blocking): %s", e)

            # T2.1 trailing-stop V1 shadow log (observation only)
            try:
                if (
                    self._trailing_stop_shadow_tracker
                    and self._trailing_stop_shadow_tracker.trigger_activated
                ):
                    trailing_result = (
                        self._trailing_stop_shadow_tracker.compute_hypothetical(
                            actual_exit_price=exit_price,
                            actual_r_multiple=actual_r,
                        )
                    )
                    if trailing_result:
                        write_trailing_stop_shadow_log(trailing_result)
                        self._active_trade_record.setdefault("shadow", {})[
                            "trailing_stop_v1"
                        ] = trailing_result
            except Exception as e:
                logger.warning("Trailing-stop shadow logging failed (non-blocking): %s", e)

            # Proximity shadow outcome update (non-blocking)
            try:
                trade_id = self._active_trade_record.get("trade_id", "")
                outcome = "WIN" if actual_r > 0 else "LOSS"
                if trade_id:
                    update_proximity_outcome(trade_id, actual_r, outcome)
            except Exception as e:
                logger.warning("Proximity outcome update failed (non-blocking): %s", e)

            # Shadow exit fields (WF-1 data collection)
            try:
                sl_price = (self._trade_entry_price - self._trade_sl_distance
                            if self._trade_direction == "LONG"
                            else self._trade_entry_price + self._trade_sl_distance)
                shadow_exit = self._compute_shadow_exit_fields(
                    entry_price=self._trade_entry_price,
                    sl_price=sl_price,
                    direction=self._trade_direction,
                    entry_time=entry_time_for_exit,
                    exit_time=exit_time,
                )
                if shadow_exit:
                    self._active_trade_record.setdefault("shadow", {}).update(shadow_exit)
            except Exception as e:
                logger.warning("Shadow exit logging failed (non-blocking): %s", e)

            # Unit69: class-aware LONG-WR halt now updates from live exits before
            # the trade record is saved, so the outcome carries the gate evidence.
            try:
                if (self._trade_direction or "").upper() == "LONG":
                    sprt_class_decision = self._sprt_class_halt_runtime.record_long_outcome(
                        self._symbol,
                        was_win=(actual_r > 0),
                    )
                    self._active_trade_record.setdefault("decision_pipeline", {})[
                        "sprt_class_halt"
                    ] = sprt_class_decision.to_record()
                    self._active_trade_record.setdefault("instrumentation", {})[
                        "sprt_class_halt_verdict"
                    ] = sprt_class_decision.verdict
            except Exception as e:
                logger.warning("SPRT class halt update failed (non-blocking): %s", e)

            save_trade_record(
                self._active_trade_record,
                self.config.get("trade_capture", {}).get("base_path", "knowledge_base/trade_records"),
            )
            logger.info("Exit data captured: type=%s R=%.4f hold=%smin",
                        exit_type, actual_r, hold_minutes)
            telegram_lifecycle_event = (
                "broker/deal reconciliation" if broker_deal_used else exit_type
            )
            try:
                execution_obj = getattr(self, "execution", None)
                notification_trade = (
                    getattr(execution_obj, "active_trade", None)
                    if execution_obj is not None
                    else None
                ) or self._active_trade_record
                notify_trade_closed(
                    symbol=self._symbol, result=exit_type,
                    actual_r=actual_r, hold_minutes=hold_minutes,
                    trade_id=self._active_trade_record.get("metadata", {}).get("trade_id", ""),
                    entry_price=self._trade_entry_price or 0,
                    exit_price=exit_price,
                    broker_profit=broker_closing_deal.get("profit") if broker_closing_deal else None,
                    broker_net_profit=broker_position_net_profit,
                    broker_deal_reconciled=broker_deal_used,
                    broker_deal_id=broker_closing_deal.get("ticket") if broker_closing_deal else None,
                    broker_close_order_id=broker_closing_deal.get("order") if broker_closing_deal else None,
                    broker_commission=broker_position_commission,
                    broker_swap=broker_position_swap,
                    vnext_context=build_vnext_notification_context(
                        notification_trade,
                        lifecycle_event=telegram_lifecycle_event,
                    ),
                )
            except Exception as e:
                logger.warning("Trade closed notification failed (non-blocking): %s", e)

            # SPRT + CUSUM update (automatic per CEO decision Apr 11)
            try:
                won = actual_r > 0
                sprt_result, cusum_result = self._sprt_monitor.update_all(self._symbol, won)
                logger.info("SPRT update: %s status=%s Lambda=%.4f (%d/%d W/L)",
                            self._symbol, sprt_result.status,
                            sprt_result.cumulative_lambda,
                            sprt_result.wins, sprt_result.losses)
                if sprt_result.status == "KILL":
                    logger.critical("SPRT KILL boundary reached for %s - halt trading", self._symbol)
                if cusum_result.deterioration_signal:
                    logger.warning("CUSUM deterioration signal for %s (S+=%.2f)",
                                   self._symbol, cusum_result.s_plus)
            except Exception as e:
                logger.debug("SPRT update failed (non-blocking): %s", e)

            # Side-aware sizing SPRT update (LONG-only outcomes; portfolio
            # level). Auto-disables side-aware multiplier when rolling-20
            # LONG-WR drops below threshold. Wrapped in try/except so a
            # state-write failure can never kill the exit flow.
            try:
                if _side_aware.is_enabled(self.config):
                    if (self._trade_direction or "").upper() == "LONG":
                        sprt_watcher = SideAwareSprtWatcher(self.config)
                        sprt_watcher.record_long_outcome(
                            self._symbol, was_win=(actual_r > 0),
                        )
            except Exception as e:
                logger.warning(
                    "side_aware sprt update failed (non-blocking): %s", e,
                )

            # EdgeMonitor update (SR + CUSUM + BOCPD change-point detection)
            try:
                from src.components.edge_monitor import EdgeMonitor, make_gtos_monitor

                monitor_path = "knowledge_base/monitoring/edge_monitor_state.json"
                try:
                    edge_monitor = EdgeMonitor.load_state(monitor_path)
                except (FileNotFoundError, json.JSONDecodeError):
                    edge_monitor = make_gtos_monitor("primary")

                edge_result = edge_monitor.update(outcome=won)
                edge_monitor.save_state(monitor_path)

                logger.info(
                    "EdgeMonitor: SR=%.1f CUSUM=%.3f BOCPD_WR=%.3f "
                    "SR_alarm=%s trades=%d",
                    edge_result["sr_statistic"],
                    edge_result["cusum_statistic"],
                    edge_result["bocpd_posterior_wr"],
                    edge_result["sr_alarm"],
                    edge_result["n_trades"],
                )

                if edge_result["sr_alarm"] or edge_result["cusum_alarm"]:
                    logger.critical(
                        "EDGE DECAY ALARM: SR_alarm=%s CUSUM_alarm=%s "
                        "BOCPD_WR=%.1f%% — HUMAN REVIEW REQUIRED",
                        edge_result["sr_alarm"],
                        edge_result["cusum_alarm"],
                        edge_result["bocpd_posterior_wr"] * 100,
                    )
            except Exception as e:
                logger.error("EdgeMonitor update failed (non-blocking): %s", e)
        except Exception as e:
            logger.error("Failed to capture exit data: %s", e)
        finally:
            self._clear_trade_tracking()

    def _clear_trade_tracking(self):
        """Reset all active trade tracking state."""
        self._active_trade_record = None
        self._active_trade_record_path = None
        self._trade_entry_price = None
        self._trade_direction = None
        self._trade_sl_distance = None
        self._trade_entry_time = None
        self._mfe_price = None
        self._mae_price = None
        self._last_tick_price = None
        self._be_shadow_tracker = None
        self._partial_close_shadow_tracker = None
        self._trailing_stop_shadow_tracker = None

    # === SHADOW DATA COLLECTION (WF-1) ===

    def _compute_shadow_entry_fields(self, mso, trade_params) -> dict:
        """Compute shadow fields at trade entry time.

        Returns a dict of shadow_ prefixed fields. Never raises.
        """
        shadow = {}
        try:
            # ATR from MSO timeframes (already computed)
            h1_tf = mso.timeframes.get("H1") if hasattr(mso, "timeframes") else None
            m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None

            h1_atr_14 = getattr(h1_tf, "atr_14", 0) or 0 if h1_tf else 0
            m15_atr_14 = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0

            shadow["shadow_h1_atr_14"] = round(h1_atr_14, 4) if h1_atr_14 else None
            shadow["shadow_m15_atr_14"] = round(m15_atr_14, 4) if m15_atr_14 else None

            # H1 ATR(50) — compute from raw candles if available in MSO
            h1_atr_50 = None
            if hasattr(mso, "_raw_data"):
                h1_candles = mso._raw_data.get("candles", {}).get("H1", [])
                if len(h1_candles) > 50:
                    from src.components.market_state import calculate_atr
                    h1_atr_50 = calculate_atr(h1_candles, period=50)
            # Fallback: pull H1 candles from MT5 for ATR(50)
            if h1_atr_50 is None:
                try:
                    from src.components.data_ingestion import TF_H1
                    h1_candles = self.mt5.get_candles(self._mt5_symbol, TF_H1, 60)
                    if len(h1_candles) > 50:
                        from src.components.market_state import calculate_atr
                        h1_atr_50 = calculate_atr(h1_candles, period=50)
                except Exception:
                    pass
            shadow["shadow_h1_atr_50"] = round(h1_atr_50, 4) if h1_atr_50 else None

            # SL as ATR multiple
            sl_distance = abs(trade_params.get("entry_price", 0) - trade_params.get("stop_loss", 0))
            if h1_atr_14 and h1_atr_14 > 0 and sl_distance > 0:
                shadow["shadow_sl_as_h1_atr_multiple"] = round(sl_distance / h1_atr_14, 4)
            else:
                shadow["shadow_sl_as_h1_atr_multiple"] = None

            if m15_atr_14 and m15_atr_14 > 0 and sl_distance > 0:
                shadow["shadow_sl_as_m15_atr_multiple"] = round(sl_distance / m15_atr_14, 4)
            else:
                shadow["shadow_sl_as_m15_atr_multiple"] = None

        except Exception as e:
            shadow["shadow_entry_logging_error"] = str(e)

        return shadow

    def _compute_shadow_exit_fields(
        self,
        entry_price: float,
        sl_price: float,
        direction: str,
        entry_time,
        exit_time,
    ) -> dict:
        """Compute shadow fields at trade exit time.

        Computes alternative TP outcomes and early MAE from M5 data.
        Uses self.mt5 wrapper (not direct MetaTrader5 import) for
        testability and consistent error handling.
        Never raises.
        """
        shadow = {}
        try:
            sl_distance = abs(entry_price - sl_price)
            if sl_distance <= 0:
                return shadow

            from src.components.data_ingestion import TF_M5
            rates = self.mt5.get_candles_range(
                self._mt5_symbol, TF_M5, entry_time, exit_time,
            )
            if not rates:
                return shadow
            window_rates = self._m5_rates_inside_trade_window(
                rates, entry_time, exit_time,
            )
            if not window_rates:
                return shadow
            bars = [bar for bar, _bar_time in window_rates]

            # --- Alternative TP outcomes ---
            for mult in [1.0, 1.5, 2.0, 2.5, 3.0]:
                key = f"shadow_tp_{mult}R_hit"
                if direction == "LONG":
                    target = entry_price + sl_distance * mult
                    hit = any(bar["high"] >= target for bar in bars)
                else:
                    target = entry_price - sl_distance * mult
                    hit = any(bar["low"] <= target for bar in bars)
                shadow[key] = hit

            # --- Early MAE (first 3 M5 candles post-entry) ---
            for i, bar in enumerate(bars[:3], 1):
                if direction == "LONG":
                    mae = (entry_price - bar["low"]) / sl_distance
                else:
                    mae = (bar["high"] - entry_price) / sl_distance
                shadow[f"shadow_mae_candle_{i}"] = round(max(mae, 0), 4)

        except Exception as e:
            shadow["shadow_exit_logging_error"] = str(e)

        return shadow

    # === M5 DATA ===

    def _pull_m5_candles(self) -> list[dict] | None:
        """Pull M5 candles for the M5 refinement step.

        In live/demo mode: pull from MT5.
        In mock/replay mode: pull from preloaded CSV data.
        Returns up to 36 M5 candles ending at the current time, or None.
        """
        from src.components.data_ingestion import pull_m5_candles
        lookback = self.config.get("m5_refinement", {}).get("candle_lookback", 36)
        try:
            return pull_m5_candles(self.mt5, lookback=lookback, symbol=self._mt5_symbol)
        except Exception as e:
            logger.warning("M5 data pull failed: %s", e)
            return None

    # === TIMEOUT TRAILING ===

    def _manage_timeout_trailing(self):
        if not self.execution.active_trade:
            return

        self._update_mfe_mae_from_tick()
        self.execution.handle_timeout_trailing()

        now = datetime.now(timezone.utc)
        kz_end = self._last_kz_end_time()
        timeout_anchor = self._timeout_trailing_anchor_time(kz_end)
        if (
            timeout_anchor
            and (now - timeout_anchor).total_seconds() > TIMEOUT_TRAIL_MINUTES * 60
        ):
            trade_snapshot = self.execution.active_trade
            logger.info(
                "2-hour timeout trailing limit reached from anchor %s -- closing position",
                timeout_anchor.isoformat(),
            )
            closed = self.execution.close_position("timeout_2h")
            if closed and self._active_trade_record is not None:
                self._finalize_exit(trade_snapshot, "timeout_2h")

    def _timeout_trailing_anchor_time(self, kz_end: Optional[datetime]) -> Optional[datetime]:
        """Return the timeout anchor for active-trade session trailing.

        Historically this was always the last kill-zone end. Late outside-KZ
        limit fills could therefore inherit a nearly-expired timeout clock. Use
        the later of KZ end and actual entry time so a trade that fills after
        the window still gets the configured post-fill management interval.
        """
        if kz_end is None:
            return None

        active_trade = self.execution.active_trade if self.execution else None
        entry_time = getattr(active_trade, "entry_time", "") if active_trade else ""
        if not entry_time:
            return kz_end

        try:
            entry_dt = datetime.fromisoformat(str(entry_time).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            logger.warning(
                "Active trade has unparseable entry_time=%r; using KZ end for timeout anchor",
                entry_time,
            )
            return kz_end

        if entry_dt.tzinfo is None:
            entry_dt = entry_dt.replace(tzinfo=timezone.utc)

        return max(kz_end, entry_dt)

    # === KILL ZONE HELPERS ===

    @staticmethod
    def _parse_time(time_str: str) -> tuple[int, int]:
        """Parse 'HH:MM' into (hour, minute) tuple."""
        parts = time_str.split(":")
        return (int(parts[0]), int(parts[1]))

    @staticmethod
    def _min_to_tuple(minutes: int) -> tuple[int, int]:
        """Convert total minutes to (hour, minute) tuple."""
        return (minutes // 60, minutes % 60)

    @staticmethod
    def _format_min_utc(minutes: int | None) -> str | None:
        """Format a minute-of-day value as HH:MM UTC."""
        if minutes is None:
            return None
        minutes = int(minutes) % (24 * 60)
        hour, minute = divmod(minutes, 60)
        return f"{hour:02d}:{minute:02d}"

    def _get_active_kill_zone(self, now: datetime) -> Optional[str]:
        """Return the name of the currently active KZ, or None."""
        t = now.hour * 60 + now.minute
        for kz_name, kz in self._kz_windows.items():
            if kz["crosses_midnight"]:
                # e.g. 22:00-02:00: active when t >= 22:00 OR t < 02:00
                if t >= kz["start_min"] or t < kz["end_min"]:
                    return kz_name
            else:
                if kz["start_min"] <= t < kz["end_min"]:
                    return kz_name
        return None

    def _get_open_positions_for_correlation(self) -> list[dict]:
        """Get list of currently open positions across all instruments for correlation checks.

        Returns list of dicts: [{"symbol": "USDJPY", "risk_pct": 0.25}, ...].
        vNext positions must be valued from ticket-bound lifecycle evidence;
        missing MT5 ad-hoc attributes are not defaulted to stale base risk.
        """
        try:
            if not self.mt5 or not self.mt5.is_connected():
                return []
            positions = self.mt5.get_positions()
            if not positions:
                return []
            result = []
            for position in positions:
                explicit_risk = self._float_or_none(getattr(position, "risk_pct", None))
                risk_source = "mt5_position_attribute"
                missing_reason = None
                if explicit_risk is None:
                    lifecycle = self._vnext_open_position_risk_from_lifecycle(position)
                    explicit_risk = self._float_or_none(lifecycle.get("risk_pct"))
                    risk_source = lifecycle.get("risk_pct_source")
                    missing_reason = lifecycle.get("risk_pct_missing_reason")
                amount_risk = self._open_position_stop_loss_risk_amount(position)
                result.append(
                    {
                        "symbol": getattr(position, "symbol", str(position)),
                        "risk_pct": float(explicit_risk or 0.0),
                        "risk_pct_source": risk_source,
                        "risk_pct_missing_reason": missing_reason,
                        "risk_amount": amount_risk.get("risk_amount"),
                        "risk_amount_source": amount_risk.get("risk_amount_source"),
                        "risk_amount_missing_reason": amount_risk.get(
                            "risk_amount_missing_reason"
                        ),
                        "risk_amount_details": amount_risk,
                        "ticket": getattr(position, "ticket", None),
                        "identifier": getattr(position, "identifier", None),
                    }
                )
            return result
        except Exception as e:
            logger.warning("Failed to get positions for correlation check: %s", e)
            return []

    def _vnext_open_position_risk_from_lifecycle(self, position) -> dict:
        path = Path(PENDING_LIMIT_LIFECYCLE_LOG_PATH)
        position_keys = self._position_identity_keys(position)
        symbol_aliases = self._vnext_position_symbol_aliases(getattr(position, "symbol", ""))
        if not path.exists():
            return {
                "risk_pct": 0.0,
                "risk_pct_source": "missing_not_defaulted_to_base",
                "risk_pct_missing_reason": "pending_lifecycle_log_missing_no_base_risk_default",
            }
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return {
                "risk_pct": 0.0,
                "risk_pct_source": "missing_not_defaulted_to_base",
                "risk_pct_missing_reason": "pending_lifecycle_log_unreadable_no_base_risk_default",
            }
        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            row_tickets = {str(row.get(field) or "") for field in _VNEXT_POSITION_TICKET_FIELDS}
            ticket_match = bool(position_keys and position_keys & row_tickets)
            row_symbol = str(row.get("symbol") or row.get("broker_symbol") or "").upper()
            symbol_match = bool(row_symbol and row_symbol in symbol_aliases)
            if not ticket_match and not symbol_match:
                continue
            if ticket_match:
                risk = self._risk_pct_from_vnext_lifecycle_row(row)
                if risk is not None and risk > 0:
                    return {
                        "risk_pct": risk,
                        "risk_pct_source": "ticket_bound_pending_lifecycle_vnext_selected_cell",
                        "risk_pct_missing_reason": None,
                    }
            if symbol_match and str(row.get("broker_fill_state") or "").lower() == "filled":
                risk = self._risk_pct_from_vnext_lifecycle_row(row)
                if risk is not None and risk > 0:
                    return {
                        "risk_pct": risk,
                        "risk_pct_source": "symbol_bound_pending_lifecycle_vnext_selected_cell",
                        "risk_pct_missing_reason": None,
                    }
        return {
            "risk_pct": 0.0,
            "risk_pct_source": "missing_not_defaulted_to_base",
            "risk_pct_missing_reason": "ticket_bound_vnext_risk_not_found_no_base_risk_default",
        }

    def _risk_pct_from_vnext_lifecycle_row(self, row: dict) -> float | None:
        for field in _VNEXT_POSITION_RISK_FIELDS:
            value = self._float_or_none(row.get(field))
            if value is not None and value > 0:
                return value
        source_details = row.get("gtos_vnext_source_event_details")
        if isinstance(source_details, dict):
            value = self._float_or_none(source_details.get("selected_cell_risk_pct"))
            if value is not None and value > 0:
                return value
        return None

    @staticmethod
    def _position_identity_keys(position) -> set[str]:
        keys: set[str] = set()
        for field in ("ticket", "identifier", "order", "external_id"):
            value = getattr(position, field, None)
            if value not in (None, ""):
                keys.add(str(value))
        return keys

    @staticmethod
    def _vnext_position_symbol_aliases(symbol: str) -> set[str]:
        raw = str(symbol or "").strip()
        canonical = raw.upper().replace(".", "_")
        aliases = {canonical} if canonical else set()
        for key, broker in VNEXT_BROADER_ORIGIN_BROKER_ALIASES.items():
            key_u = str(key).upper().replace(".", "_")
            broker_u = str(broker).upper().replace(".", "_")
            if canonical in {key_u, broker_u}:
                aliases.update({key_u, broker_u})
        return aliases

    def _should_skip_first_ny_candle(self, kill_zone: str) -> bool:
        """Check if we should skip evaluation because this is the first NY candle.

        The 13:00 UTC M15 candle (first candle of NY session) has 0% WR on XAUUSD
        due to flow collision, algorithmic momentum ignition, order flow reversal,
        and PM Fix positioning. Configurable per instrument.

        The flag is read from the TOP LEVEL of ``self.config`` because
        ``apply_instrument_overrides`` deep-merges the matching
        ``instruments.<symbol>`` block over the base config and then pops
        ``instruments``. So a key set under
        ``instruments.XAUUSD.skip_first_ny_candle`` in ``agent_config.yaml``
        surfaces as ``self.config["skip_first_ny_candle"]`` after per-symbol
        config load completes. (Same pattern as ``trading_enabled`` in
        ``permissions._reject_if_trading_disabled`` — session 37 commit
        ``32fbe58``.) The previous nested lookup always returned False because
        ``instruments`` was already popped, silently ignoring XAUUSD's
        ``skip_first_ny_candle: true`` setting for the entire life of this flag.
        """
        # Read from top-level config (flattened by apply_instrument_overrides).
        skip = self.config.get("skip_first_ny_candle", False)
        if not skip:
            return False

        # Only applies during NY kill zone
        kz_cfg = self._kz_windows.get(kill_zone, {})
        ny_cfg = self._kz_windows.get("ny", {})
        if not ny_cfg or kz_cfg.get("start_min") != ny_cfg.get("start_min"):
            return False

        # Check if the just-closed M15 candle is the NY-open candle (13:00-13:15).
        #
        # Wake-time vs candle-start nuance (E.2 fix, 2026-04-26):
        # ``_next_m15_close`` returns ``close_time + 5s``, so the orchestrator
        # wakes at 13:15:05 UTC to evaluate the M15 bar that just CLOSED — i.e.
        # the 13:00-13:15 NY-open candle. The previous bounds
        # ``ny_start <= t < ny_start + 15`` (i.e. [13:00, 13:15)) compared the
        # wake time itself against the candle's START window and so NEVER fired
        # in production: at wake t=795, ny_start+15=795, so 795 < 795 is False.
        # The corrected bounds [ny_start+15, ny_start+30) (i.e. [13:15, 13:30))
        # match wake times that are evaluating the NY-open candle.
        now = datetime.now(timezone.utc)
        t = now.hour * 60 + now.minute
        ny_start = ny_cfg["start_min"]
        if ny_start + 15 <= t < ny_start + 30:
            logger.info("SKIP_NY_OPEN_CANDLE: Skipping 13:00 UTC candle for %s "
                        "(0%% WR, microstructural evidence)", self._symbol)
            return True
        return False

    def _is_extended_london(self, now: datetime) -> bool:
        """Check if current time is in the extended London window (core_end to end)."""
        t = now.hour * 60 + now.minute
        core_end = self._london_core_end[0] * 60 + self._london_core_end[1]
        full_end = self._london_end[0] * 60 + self._london_end[1]
        return core_end <= t < full_end

    def _is_extended_window(self, kz_name: str, now: datetime) -> bool:
        """Check if current time is in an extended portion of the given KZ."""
        kz = self._kz_windows.get(kz_name)
        if not kz:
            return False
        t = now.hour * 60 + now.minute
        core_end = kz["core_end_min"]
        full_end = kz["end_min"]
        if core_end == full_end:
            return False  # No extended window
        if kz["crosses_midnight"]:
            # For midnight-crossing windows, extended is between core_end and end
            if core_end > full_end:
                return t >= core_end or t < full_end
            else:
                return core_end <= t < full_end
        return core_end <= t < full_end

    def _is_between_kz(self, now: datetime) -> bool:
        """True if current time falls in a gap between two non-midnight-crossing KZs."""
        if self._get_active_kill_zone(now) is not None:
            return False
        t = now.hour * 60 + now.minute
        # Collect all non-midnight-crossing KZ boundaries
        ends = []
        starts = []
        for kz in self._kz_windows.values():
            if not kz["crosses_midnight"]:
                ends.append(kz["end_min"])
                starts.append(kz["start_min"])
        # Between KZ if after some KZ ended and before another starts
        after_some = any(t >= e for e in ends)
        before_some = any(t < s for s in starts)
        return after_some and before_some

    def _is_after_all_kz(self, now: datetime) -> bool:
        """True if current time is past all KZ windows for the day."""
        if self._get_active_kill_zone(now) is not None:
            return False
        t = now.hour * 60 + now.minute
        for kz in self._kz_windows.values():
            if kz["crosses_midnight"]:
                # A midnight-crossing KZ means there's always a window ahead
                return False
            if t < kz["end_min"]:
                return False  # Still a KZ ending later today
        return True

    def _next_m15_close(self, now: datetime) -> datetime:
        minute = now.minute
        next_close_minute = ((minute // 15) + 1) * 15
        if next_close_minute >= 60:
            result = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            result = now.replace(minute=next_close_minute, second=0, microsecond=0)
        return result + timedelta(seconds=5)

    def _last_kz_end_time(self) -> Optional[datetime]:
        now = datetime.now(timezone.utc)
        today = now.date()
        latest_past = None
        for kz in self._kz_windows.values():
            if kz["crosses_midnight"]:
                continue  # Skip midnight-crossing for timeout calculation
            end_h, end_m = kz["end_min"] // 60, kz["end_min"] % 60
            end_dt = datetime(today.year, today.month, today.day,
                              end_h, end_m, tzinfo=timezone.utc)
            if now >= end_dt:
                if latest_past is None or end_dt > latest_past:
                    latest_past = end_dt
        return latest_past

    def _next_kz_start_time(self, now: datetime) -> Optional[datetime]:
        """Return the datetime of the next KZ start after *now*, or None."""
        t = now.hour * 60 + now.minute
        today = now.date()
        candidates = []
        for kz in self._kz_windows.values():
            if kz["crosses_midnight"]:
                # Start is in the evening (e.g. 22:00)
                s_h, s_m = kz["start_min"] // 60, kz["start_min"] % 60
                start_dt = datetime(today.year, today.month, today.day,
                                    s_h, s_m, tzinfo=timezone.utc)
                if start_dt > now:
                    candidates.append(start_dt)
                # Also tomorrow's morning portion end (handled by next day reset)
            else:
                s_h, s_m = kz["start_min"] // 60, kz["start_min"] % 60
                start_dt = datetime(today.year, today.month, today.day,
                                    s_h, s_m, tzinfo=timezone.utc)
                if start_dt > now:
                    candidates.append(start_dt)
        return min(candidates) if candidates else None

    def _next_kz_start_with_lookahead(self, now: datetime) -> Optional[datetime]:
        """Like ``_next_kz_start_time`` but extends the search into tomorrow.

        Used by the graceful-shutdown-marker writer. The plain
        ``_next_kz_start_time`` only considers TODAY's remaining KZs and
        returns None once the day's last KZ has started — but a 23:46 UTC
        shutdown after end-of-NY (with Tokyo opening at 00:00 UTC the next
        day) MUST still produce a finite ``next_kz_start`` so the marker
        doesn't fall back to a 24h dead-zone-exit suppression. See
        2026-04-30 live bug + ``TestGracefulShutdownMarker`` regression.
        """
        # First try today.
        result = self._next_kz_start_time(now)
        if result is not None:
            return result
        # No KZ remaining today → look at tomorrow's KZs by querying with a
        # ``now`` set to tomorrow's 00:00 UTC minus 1 microsecond, which
        # reuses the same construction logic but lets ``start_dt > now``
        # admit tomorrow's earliest KZ.
        tomorrow_zero = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        candidates = []
        for kz in self._kz_windows.values():
            s_h, s_m = kz["start_min"] // 60, kz["start_min"] % 60
            start_dt = datetime(
                tomorrow_zero.year, tomorrow_zero.month, tomorrow_zero.day,
                s_h, s_m, tzinfo=timezone.utc,
            )
            if start_dt > now:
                candidates.append(start_dt)
        return min(candidates) if candidates else None

    def _enter_kill_zone(self, kz: str):
        logger.info(f"Entering {kz.upper()} kill zone")
        self.session_state["current_kill_zone"] = kz
        self._compute_cross_instrument_context()

    def _new_day(self, date_str: str):
        logger.info(f"New trading day: {date_str}")

        # T2.8: at 00:00 UTC, clear any stale daily-loss dormant marker from
        # yesterday. Today's AI calls re-enable immediately. If the marker is
        # for today (mid-day restart) ``clear_if_stale`` is a no-op and
        # permissions Gate 3 continues to honor it.
        try:
            _dormant_state.clear_if_stale()
        except Exception as e:  # noqa: BLE001 — new-day reset must never crash the loop
            logger.warning("dormant marker clear-if-stale failed: %s", e)

        # Cancel stale executable pending limits. The structural POI is archived
        # separately in shadow mode so it can be revalidated if price returns.
        if self.execution.pending_intent:
            intent = self.execution.pending_intent
            trade_id = intent.trade_id
            self._archive_expired_poi_watch(intent, "new_day")
            self.execution.cancel_limit_intent("new_day")
            self._clear_pending_trade_record(trade_id, reason="new_day")
            notify_limit_expired(
                symbol=self._symbol, trade_id=trade_id,
                reason="new trading day - stale analysis",
                vnext_context=build_vnext_notification_context(
                    intent,
                    lifecycle_event="expiry",
                ),
            )

        self.session_state = {
            "date": date_str,
            "trades_today": 0,
            "daily_pnl_pct": 0.0,
            "portfolio_drawdown_pct": 0.0,
            "consecutive_losses": 0,
            "losses_today": 0,
            "current_kill_zone": None,
            "start_balance": 0.0,
            "start_equity": 0.0,
        }
        # T2.8: per-KZ trade counters remain in session_state for backward
        # compatibility with observability tooling (session summaries, logs)
        # but are NO LONGER consulted by permissions Gate 3 or _process_candle
        # as a trading cap. The concurrent cap (cross-symbol filled positions)
        # is authoritative.
        for kz_name in self._kz_windows:
            self.session_state[f"trades_{kz_name}"] = 0
        self.session_memory = []
        self._ci_context_text = ""
        # Reset raw XAU D1 direction snapshot — re-populated when the
        # next kill zone enters and ``_compute_cross_instrument_context``
        # runs. ``"unavailable"`` is the conservative default: the
        # direction-emission audit logger emits this for any CANDIDATE
        # that fires before the first KZ entry of the new day (rare but
        # possible if a between-KZ pending limit fires).
        self._xau_d1_direction_value = "unavailable"
        self.candle_log = []
        # Store starting balance and equity for MTM daily-loss calculation.
        # Balance is used by _update_daily_pnl legacy realized-deal math;
        # equity is used by the T2.8 MTM formula (equity - start_equity).
        # Bug #25 hardening: equity goes through ``safe_read_equity`` so a
        # transient None / 0 read at new_day boundary doesn't pin the
        # day's baseline at 0 (which would freeze daily_pnl_pct at 0% all
        # day OR — in the prior pre-fix code — produce -100% on the next
        # update). Lazy-seed in ``_update_daily_pnl`` handles the case
        # where this seed read also fails.
        try:
            self.session_state["start_balance"] = self.mt5.get_account_balance()
        except Exception:
            self.session_state["start_balance"] = 0.0
        # Reset filter on new day so prior day's equity history doesn't
        # bleed into today's median (e.g. yesterday at $99,500, today
        # opens at $100,000 after a deposit — we want today's median to
        # converge fresh, not anchor to yesterday).
        self._equity_filter = EquityFilter(symbol=self._symbol)
        seed_equity = safe_read_equity(self.mt5, symbol=self._symbol)
        if seed_equity is not None:
            # Prime the filter with the seed read so the first
            # _update_daily_pnl tick has consensus=this value rather than
            # waiting for a second valid read to compute median.
            self._equity_filter.update_and_get_consensus(seed_equity)
            self.session_state["start_equity"] = seed_equity
        else:
            # Defer: lazy-seed in _update_daily_pnl on the first valid
            # read. start_balance fallback preserves prior behavior for
            # downstream consumers expecting a number; daily_pnl_pct
            # update path checks ``start_equity > 0`` before dividing.
            self.session_state["start_equity"] = self.session_state["start_balance"]

        # Bug 2 fix: persist the new UTC date so a mid-day restart doesn't
        # re-fire _new_day (which cancels all pending limits). Failure is
        # non-fatal — the orchestrator degrades to pre-persistence behavior.
        _persist_session_date(self._symbol, date_str)

    def _update_daily_pnl(self):
        """Update daily_pnl_pct and portfolio_drawdown_pct from MT5 (non-blocking).

        T2.8: ``daily_pnl_pct`` is MTM — (equity - start_equity) / start_equity.
        This captures BOTH realized P&L (closed deals) and unrealized floating
        P&L (open positions), which is what FTMO / redacted_account actually enforce.
        The previous realized-only calculation would miss a -4% unrealized
        float on a still-open position — exactly the case the 4% stop must
        catch BEFORE the position closes red.

        Bug #25 hardening (2026-04-27 GBPUSD false-positive trigger):
        equity reads go through ``safe_read_equity`` (hard-zero / None /
        exception guard) and ``EquityFilter`` (rolling median over recent
        valid reads). When the current read is None — i.e. MT5
        transiently returned ``account_info()=None`` — we SKIP the update
        entirely (no overwrite of last good ``daily_pnl_pct``). When the
        read is valid but appears anomalous against history, the median
        filter absorbs it. Daily-loss-stop will only trigger on a
        sustained pattern of valid reads, not a single transient blip.
        """
        try:
            now = datetime.now(timezone.utc)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

            # Hard guard — None / 0 / negative / exception → skip update.
            raw_equity = safe_read_equity(self.mt5, symbol=self._symbol)
            # Soft guard — rolling median over last N valid reads. Returns
            # the *consensus* (not the raw value) for downstream math.
            # Lazy-create filter if missing (back-compat for hand-built
            # stubs in older tests).
            if not hasattr(self, "_equity_filter") or self._equity_filter is None:
                self._equity_filter = EquityFilter(symbol=self._symbol)
            equity = self._equity_filter.update_and_get_consensus(raw_equity)
            if equity is None:
                # No valid history yet AND current read failed. Leave
                # session_state untouched — better stale data than a false
                # daily_loss_stop. consecutive_losses still updated below.
                logger.warning(
                    "_update_daily_pnl: no valid equity read available "
                    "(filter empty, skipping P&L update for this tick)"
                )
                # Still refresh consecutive_losses from deals so the
                # consec_losses emergency path is not starved.
                try:
                    all_deals = self.mt5.get_history_deals(today_start, now)
                    if all_deals is None:
                        # Broker fetch FAILED (distinct from "no deals today", which is
                        # []). Leaving the old value stands; recomputing would reset the
                        # counter to 0 and silently release the consec_losses emergency
                        # brake on a transient read error.
                        logger.warning(
                            "_update_daily_pnl: history_deals fetch failed; "
                            "holding consecutive_losses=%s rather than resetting it",
                            self.session_state.get("consecutive_losses", 0),
                        )
                    else:
                        consec = 0
                        for d in reversed(all_deals):
                            if d.get("profit", 0.0) < 0:
                                consec += 1
                            else:
                                break
                        self.session_state["consecutive_losses"] = consec
                    self.session_state["losses_today"] = sum(
                        1 for d in all_deals if d.get("profit", 0.0) < 0
                    )
                except Exception:
                    pass
                return

            start_equity = self.session_state.get("start_equity", 0.0) or 0.0
            if start_equity <= 0:
                # First call on a fresh session when start_equity seeding failed
                # at new_day time (MT5 hiccup). Seed lazily from the *filtered*
                # consensus so the next tick has a sensible baseline.
                start_equity = equity
                self.session_state["start_equity"] = start_equity
            if start_equity > 0:
                self.session_state["daily_pnl_pct"] = (
                    (equity - start_equity) / start_equity
                ) * 100
            else:
                self.session_state["daily_pnl_pct"] = 0.0

            # Portfolio drawdown from starting balance (separate from daily MTM;
            # kept for portfolio_drawdown_stop emergency path at 4%+).
            start_balance = self.session_state.get("start_balance", 0.0)
            if start_balance > 0:
                self.session_state["portfolio_drawdown_pct"] = (
                    (start_balance - equity) / start_balance
                ) * 100
            else:
                self.session_state["portfolio_drawdown_pct"] = 0.0

            # Consecutive losses from recent deals (all symbols) — retained
            # for the existing consec_losses emergency path.
            all_deals = self.mt5.get_history_deals(today_start, now)
            if all_deals is None:
                # See the sibling path above: a failed fetch must not zero the counter.
                logger.warning(
                    "_update_daily_pnl: history_deals fetch failed; "
                    "holding consecutive_losses=%s rather than resetting it",
                    self.session_state.get("consecutive_losses", 0),
                )
            else:
                consec = 0
                for d in reversed(all_deals):
                    if d.get("profit", 0.0) < 0:
                        consec += 1
                    else:
                        break
                self.session_state["consecutive_losses"] = consec
            # losses_today retained for telemetry but no longer gates trading
            # (T2.8 replaced the ``max_daily_losses=2`` cap with concurrent cap).
            self.session_state["losses_today"] = sum(
                1 for d in all_deals if d.get("profit", 0.0) < 0
            )
        except Exception as e:
            logger.debug("_update_daily_pnl failed (non-blocking): %s", e)

    def _check_and_trigger_daily_loss_stop(self, kill_zone: str) -> bool:
        """T2.8 MTM daily-loss stop. Returns True iff stop triggered this tick.

        Behavior when triggered:
          1. Write ``pipeline_state/dormant_state.json`` with equity + pnl pct
             at trigger time so a restart honors the stop through 23:59:59 UTC.
          2. Cancel any pending limit order (locked decision #5).
          3. Send Telegram system alert via ``notify_alert``.
          4. Log ``DAILY_LOSS_STOP`` candle entry for the session manifest.

        Side-effects are ALL wrapped in try/except — the stop must fire even
        if Telegram is down or the pending cancel raises. The dormant marker
        is the authoritative signal; everything else is best-effort.

        NOT triggered:
          - when ``_dormant_state.is_dormant_today()`` already returns True
            (idempotent — we only write the marker once per day).
          - when ``max_daily_loss_pct`` is missing/invalid (fail-open to the
            permissions Gate 3 safety net).
        """
        if _dormant_state.is_dormant_today():
            return False
        risk_cfg = self.config.get("risk", {}) or {}
        try:
            cap_pct = float(risk_cfg.get("max_daily_loss_pct", 4.0))
        except (TypeError, ValueError):
            return False
        if cap_pct <= 0:
            return False
        daily_pnl_pct = float(self.session_state.get("daily_pnl_pct", 0.0) or 0.0)
        if daily_pnl_pct > -cap_pct:
            return False

        # Threshold crossed. Use the filtered consensus for the marker
        # equity so the persisted record matches the value the trigger
        # decision was made on (Bug #25 — never let a transient equity=0
        # leak into the marker as ``equity_at_trigger=$0``).
        # ``_equity_filter`` may be absent on hand-built stubs in older
        # tests; fall back to a raw safe read in that case.
        equity = None
        eq_filter = getattr(self, "_equity_filter", None)
        if eq_filter is not None:
            equity = eq_filter.get_consensus()
        if equity is None:
            # Filter never accumulated a valid read — fall back to a raw
            # safe read for the marker. If THAT also fails, fall back to
            # 0.0 (the marker is informational; the dormant flag itself
            # is the authoritative gate).
            raw = safe_read_equity(self.mt5, symbol=self._symbol)
            equity = raw if raw is not None else 0.0
        try:
            _dormant_state.write_dormant_state(
                trigger_reason="daily_loss_stop",
                equity_at_trigger=equity,
                daily_pnl_pct_at_trigger=daily_pnl_pct,
                max_daily_loss_pct=cap_pct,
                symbol=self._symbol,
            )
        except Exception as e:  # noqa: BLE001 — must never crash the loop
            logger.error("Failed to persist dormant_state.json: %s", e)

        # Cancel pending limit — locked decision #5.
        try:
            if self.execution and self.execution.pending_intent:
                self.execution.cancel_limit_intent("daily_loss_stop")
                self._pending_trade_record_path = None
        except Exception as e:
            logger.error("daily_loss_stop: pending cancel failed: %s", e)

        try:
            clear_result = clear_all_pending_intent_files("daily_loss_stop")
            if clear_result.get("failed_files"):
                logger.warning(
                    "daily_loss_stop: persisted pending intent cleanup had failures: %s",
                    clear_result.get("failed_files"),
                )
        except Exception as e:  # noqa: BLE001 - dormant marker remains authoritative
            logger.error(
                "daily_loss_stop: persisted pending intent cleanup failed: %s",
                e,
            )

        # Telegram system alert — fire-and-forget.
        try:
            # NOTE: alert body must NOT contain raw `<`, `>`, or `&` —
            # `src/notifications.py` sends as plain text by policy
            # (HTML-ESCAPE BUG fix, 2026-04-28). Phrase comparisons in
            # words ("reached", "of") to keep this safe even if a future
            # transport reintroduces parse_mode.
            notify_alert(
                f"DAILY LOSS STOP ({self._symbol})\n"
                f"MTM PnL: {daily_pnl_pct:.2f}% reached cap of -{cap_pct:.2f}%\n"
                f"Equity at trigger: ${equity:,.2f}\n"
                f"Dormant until 00:00 UTC next day. "
                f"AI calls paused. Open positions left to close naturally."
            )
        except Exception as e:
            logger.warning("daily_loss_stop: Telegram alert failed: %s", e)

        try:
            self._log_candle(
                "DAILY_LOSS_STOP",
                f"mtm={daily_pnl_pct:.2f}% cap=-{cap_pct:.2f}% equity=${equity:,.2f}",
                kill_zone,
            )
        except Exception as e:
            logger.error("daily_loss_stop: log_candle failed: %s", e)

        return True

    # === SESSION OBSERVABILITY ===

    def _save_session_summary(self, kill_zone: str, pre_screen_passed: bool = True,
                               skip_reason: str | None = None):
        """Persist a JSON summary after each kill zone session completes.

        This is diagnostic data only — failure to write must NEVER crash
        the trading pipeline.
        """
        try:
            date_str = self.session_state.get("date") or datetime.now(timezone.utc).strftime("%Y-%m-%d")

            # Gather pre-screen info from candle_log
            d1_dir = None
            h4_dir = None
            h4_aligned = None
            if hasattr(self, '_last_mso') and self._last_mso:
                tfs = getattr(self._last_mso, 'timeframes', {}) or {}
                d1 = tfs.get("D1")
                h4 = tfs.get("H4")
                d1_dir = d1.structure.direction if d1 and hasattr(d1, 'structure') else None
                h4_dir = h4.structure.direction if h4 and hasattr(h4, 'structure') else None
                h4_aligned = (h4_dir == d1_dir) if (h4_dir and d1_dir) else None

            # If pre-screen failed, write minimal summary
            if not pre_screen_passed:
                summary = {
                    "date": date_str,
                    "symbol": self._symbol,
                    "kill_zone": kill_zone,
                    "pre_screen": {
                        "d1_direction": d1_dir,
                        "h4_direction": h4_dir,
                        "h4_aligned": h4_aligned,
                        "passed": False,
                        "skip_reason": skip_reason,
                    },
                    "candles_evaluated": 0,
                }
                self._write_session_summary_file(date_str, kill_zone, summary)
                return

            # Build full summary from candle_log
            kz_entries = [e for e in self.candle_log if e.get("kill_zone") == kill_zone]
            candles_evaluated = len(kz_entries)

            # Count decisions
            # Bug 4 (Thursday 2026-04-23 audit): a CANDIDATE that got
            # REJECTED_L2 (or any other downstream gate) used to log ONLY
            # the terminal outcome, so ``decisions.CANDIDATE`` stayed at 0
            # while the raw live_evaluations jsonl clearly showed CANDIDATE
            # rows. Now every post-CANDIDATE _log_candle call carries a
            # ``produced_candidate=True`` flag, and the summary counts
            # CANDIDATE as "rows where the AI returned CANDIDATE (whether
            # or not a downstream gate later rejected it)".
            decisions = {"NO_TRADE": 0, "CANDIDATE": 0, "WAIT": 0}
            rejection_reasons: dict[str, int] = {}
            for entry in kz_entries:
                dec = entry.get("decision", "NO_TRADE")
                if entry.get("produced_candidate"):
                    decisions["CANDIDATE"] += 1
                elif dec in decisions:
                    decisions[dec] += 1
                elif dec not in ("EXECUTED", "REJECTED_L2", "BLOCKED_CALENDAR",
                                  "SKIP_NEWS_EVENT", "EXECUTION_FAILED", "ERROR", "SKIP"):
                    decisions["NO_TRADE"] += 1

                # Track rejection reasons
                detail = entry.get("detail", "")
                if dec == "NO_TRADE" and detail:
                    # Clean up the reason
                    reason = detail.split(":")[-1].strip() if ":" in detail else detail
                    reason = reason[:80]  # Truncate long reasons
                    rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

            # Build candidate details
            # Bug 4 fix: include any entry that produced a CANDIDATE
            # regardless of terminal outcome. ``post_decision_result`` makes
            # rejection downstream of AI visible without losing the fact
            # that a CANDIDATE was produced.
            candidate_details = []
            for entry in kz_entries:
                is_candidate = (
                    entry.get("decision") in ("CANDIDATE", "EXECUTED", "LIMIT_PLACED")
                    or entry.get("produced_candidate")
                )
                if is_candidate:
                    dec = entry.get("decision")
                    candidate_details.append({
                        "candle_time": entry.get("time"),
                        "grade": None,  # Not available in log
                        "framework": None,
                        "executed": dec == "EXECUTED",
                        "trade_id": entry.get("detail") if dec in ("EXECUTED", "LIMIT_PLACED") else None,
                        "post_decision_result": dec,
                    })

            # Determine top rejection reason
            top_reason = None
            if rejection_reasons:
                top_reason = max(rejection_reasons, key=rejection_reasons.get)

            # KZ time bounds
            if kill_zone == "london":
                kz_start_h, kz_start_m = self._london_start
                kz_end_h, kz_end_m = self._london_core_end
            else:
                kz_start_h, kz_start_m = self._ny_start
                kz_end_h, kz_end_m = self._ny_end

            # Calendar / news blocks
            calendar_blocks = []
            for entry in kz_entries:
                if entry.get("decision") in ("BLOCKED_CALENDAR", "SKIP_NEWS_EVENT"):
                    calendar_blocks.append(entry.get("detail", ""))

            summary = {
                "date": date_str,
                "symbol": self._symbol,
                "kill_zone": kill_zone,
                "kz_start": f"{date_str}T{kz_start_h:02d}:{kz_start_m:02d}:00Z",
                "kz_end": f"{date_str}T{kz_end_h:02d}:{kz_end_m:02d}:00Z",
                "pre_screen": {
                    "d1_direction": d1_dir,
                    "h4_direction": h4_dir,
                    "h4_aligned": h4_aligned,
                    "passed": True,
                    "skip_reason": None,
                },
                "candles_evaluated": candles_evaluated,
                # Thursday 2026-04-23 audit (bug 3): XAUUSD + GBPUSD session
                # summaries reported api_calls_made=7/30 when actual calls
                # were 0. Cause: the detail-prefix filter excluded
                # ``pre_screen:`` and ``deterministic_no_bias:`` but NOT
                # ``pre_ai_gate:`` (the H1 POI availability gate shipped
                # 2026-04-20 that emits NO_TRADE with ``pre_ai_gate:<reason>``
                # BEFORE the AI call). Also added SKIP_DORMANT (T2.8 daily-
                # loss dormant gate) to the decision-name exclusions — it
                # short-circuits before any API call too.
                "api_calls_made": sum(
                    1 for e in kz_entries
                    if e.get("decision") not in (
                        "SKIP", "BLOCKED_CALENDAR", "SKIP_NEWS_EVENT",
                        "EMERGENCY_STOP",
                        "SKIP_KZ_TRADED", "SKIP_NY_OPEN_CANDLE",
                        "SKIP_DORMANT",
                        "LIMIT_FILLED",
                    )
                    and not str(e.get("detail", "")).startswith(
                        ("pre_screen:", "deterministic_no_bias:",
                         "pre_ai_gate:")
                    )
                ),
                "decisions": decisions,
                "candidate_details": candidate_details,
                "calendar_blocks": calendar_blocks,
                "rejection_summary": {
                    "top_reason": top_reason,
                    "reason_counts": rejection_reasons,
                },
                "session_memory_entries": len(self.session_memory),
            }

            self._write_session_summary_file(date_str, kill_zone, summary)

        except Exception as e:
            # Logging failure must NEVER crash the trading pipeline
            logger.error("Failed to save session summary: %s", e)

    def _write_session_summary_file(self, date_str: str, kill_zone: str, summary: dict):
        """Write session summary JSON to disk."""
        try:
            summary_dir = Path(f"knowledge_base/live_sessions/{self._symbol}")
            summary_dir.mkdir(parents=True, exist_ok=True)
            path = summary_dir / f"{date_str}_{kill_zone}_summary.json"
            atomic_write(str(path), summary)
            logger.info("Session summary saved: %s", path)
        except Exception as e:
            logger.error("Failed to write session summary file: %s", e)

    # === INFRASTRUCTURE ===

    def _acquire_lock(self):
        lock = Path(self._lock_path)
        if lock.exists():
            with open(lock) as f:
                data = json.load(f)
            pid = data.get("pid", 0)
            try:
                os.kill(pid, 0)
                raise RuntimeError(
                    f"Another orchestrator for {self._symbol} is running (PID {pid})")
            except (OSError, SystemError):
                logger.warning("Stale lock for %s from PID %s - overriding", self._symbol, pid)

        lock.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(str(lock), {"pid": os.getpid(),
                                  "symbol": self._symbol,
                                  "started": datetime.now(timezone.utc).isoformat()})

    def _release_lock(self):
        lock = Path(self._lock_path)
        if lock.exists():
            lock.unlink()

    def _signal_handler(self, signum, frame):
        logger.info("Received signal %s - initiating shutdown", signum)
        self.running = False

    def _interruptible_sleep(self, seconds: float):
        if seconds <= 0:
            return
        end_time = time.time() + seconds
        # T1.1: emit a heartbeat at the start of each sleep chunk so long
        # _monitored_sleep calls (up to 300s) don't look like a silent crash.
        # WARNING level (was debug) — failed write is the silent-degradation
        # tell that prior shared-file architecture suppressed.
        try:
            _write_heartbeat(extra={"symbol": self._symbol})
        except Exception as _hb_err:  # noqa: BLE001
            logger.warning(
                "heartbeat write raised (non-fatal) symbol=%s: %s",
                self._symbol, _hb_err,
            )
        while time.time() < end_time and self.running:
            remaining = end_time - time.time()
            if remaining <= 0:
                break
            time.sleep(min(1.0, remaining))

    def _monitored_sleep(self, seconds: float):
        """Sleep in 60s chunks with trade monitoring between each chunk."""
        if seconds <= 0:
            return
        end_time = time.time() + seconds
        while time.time() < end_time and self.running:
            chunk = min(60.0, end_time - time.time())
            if chunk <= 0:
                break
            # _interruptible_sleep handles the per-chunk heartbeat write.
            self._interruptible_sleep(chunk)
            if self.execution.active_trade:
                self._check_trade_and_capture()
            elif self.execution.pending_intent:
                self._check_pending_limit_ltf_path(check_context="inside_kz_ltf_sleep")

    def _reconcile_open_positions_or_continue(self) -> bool:
        """BUG #26 fix: check broker for our open positions before ending session.

        Called from the ``_is_after_all_kz`` branch when the orchestrator's
        local ``execution.active_trade`` is None and there is no pending
        limit. Queries ``mt5.get_positions(symbol)`` which already filters
        by ``MAGIC_NUMBER`` (see ``src/mt5/mt5_interface.py:80-81`` —
        contract is binding for both ``MockMT5`` and ``RealMT5``), so any
        result is an OUR open position that the local state lost track of
        (silent crash, watchdog respawn after a previous orchestrator
        emitted "Ending session" without reconciling, etc.).

        Returns:
            True  -- found at least one orphan position; ``reconcile_on_startup``
                     was called to adopt it and ``execution.active_trade``
                     is now set. Caller should NOT end the session; should
                     stay in monitoring loop.
            False -- broker truly has no positions. Caller is safe to end
                     the session.

        Defensive: any exception talking to MT5 returns False (preserve
        prior behavior — end session — rather than spin forever on a
        broken connection). Operator will see the WARNING log and the
        watchdog respawn cycle will continue but at least we don't lose
        an open position to a transient disconnect either, because the
        next bootstrap will adopt it via the existing reconcile path.
        """
        try:
            positions = self.mt5.get_positions(self._mt5_symbol)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Pre-session-end reconcile: get_positions raised (%s); "
                "falling through to session-end. Next bootstrap will adopt "
                "any orphan via reconcile_on_startup.", exc,
            )
            return False

        if not positions:
            return False

        logger.warning(
            "Pre-session-end reconcile: found %d open position(s) for %s "
            "with our magic but no local active_trade. Adopting orphan(s) "
            "and continuing in monitoring-only mode (no new evals).",
            len(positions), self._symbol,
        )
        try:
            actions = self.execution.reconcile_on_startup()
            if actions:
                logger.warning("Pre-session-end recovery actions: %s", actions)
                self._reconnect_trade_record()
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Pre-session-end reconcile_on_startup failed: %s. Falling "
                "through to session-end (watchdog respawn will retry).", exc,
            )
            return False

        # Confirm we now have an active trade. If reconcile didn't adopt
        # (e.g., positions vanished between get_positions and reconcile),
        # let the caller end the session normally.
        return self.execution.active_trade is not None

    def _shutdown(self):
        logger.info("Shutting down orchestrator")
        self._end_session()
        if self.mt5:
            self.mt5.disconnect()
        self._release_lock()
        # Delete this orchestrator's heartbeat file so heartbeat_monitor
        # treats us as "not running" rather than "stale and silent".
        # Without this, a graceful shutdown leaves a frozen heartbeat file
        # that the monitor cascades into TRIGGER_CANDIDATE → ARMED →
        # FLATTENED on the next 90s tick (attempted=0 because no positions
        # to flatten on a shut-down orch, but log noise + telegram churn).
        # ``discover_heartbeat_paths`` naturally skips missing files; no
        # monitor-side change needed.
        try:
            hb_path = _per_symbol_heartbeat_path(self._symbol)
            if hb_path.exists():
                hb_path.unlink()
                logger.info("Deleted heartbeat file on shutdown: %s", hb_path.name)
        except OSError as e:
            logger.warning("Heartbeat cleanup on shutdown failed (non-fatal): %s", e)
        # Write a shutdown marker so the watchdog's 15-min cron knows this
        # orch shut down GRACEFULLY and shouldn't be respawned until the
        # next dead-zone exit. Without this, the watchdog sees "no lock
        # file" and starts the orch every 15 min, which boots, sees "all
        # KZ complete", shuts down → respawn loop.
        if self._abnormal_shutdown_reason:
            logger.error(
                "Skipping graceful shutdown marker for %s because shutdown is "
                "abnormal: %s",
                self._symbol,
                self._abnormal_shutdown_reason,
            )
        else:
            self._write_graceful_shutdown_marker()
        logger.info("Shutdown complete")

    def _write_graceful_shutdown_marker(self, now: Optional[datetime] = None):
        """Drop ``pipeline_state/.orch_shutdown_{SYMBOL}.json`` with a
        ``valid_until_utc`` timestamp that suppresses watchdog respawn ONLY
        until the orch is actually next needed.

        ``now`` is exposed for tests; production callers leave it None and we
        read ``datetime.now(timezone.utc)`` on entry.

        ``valid_until_utc`` is set to ``min(next_dead_zone_exit, next_kz_start
        − buffer)``:

        * If a kill zone is upcoming today (e.g. orch shut down at end of
          London with NY at 13:00 UTC still ahead), the marker expires
          ``buffer`` minutes before NY start so the next watchdog tick
          respawns the orch in time for NY.
        * If no KZ remains today (e.g. orch shut down post-NY), the marker
          expires at the next dead-zone exit (23:45 UTC) — watchdog will
          respawn naturally after the dead zone.

        Live bug 2026-04-30: the prior version unconditionally set
        ``valid_until = today_2345 (or +1d if past)``. When ``_shutdown``
        fired at 23:46:10 UTC (after Tokyo KZ end for orchs that just
        respawned and saw no KZ active), the marker was set to 23:45 UTC
        TOMORROW — suppressing the watchdog through the next 24h including
        Tokyo (00:00), London (07:00), and NY (13:00). Cost: an entire
        trading day silently lost. Fix: cap at next-KZ-start instead.
        """
        try:
            marker = Path("pipeline_state") / f".orch_shutdown_{self._symbol}.json"
            if now is None:
                now = datetime.now(timezone.utc)
            # Dead-zone-exit fallback (used when no KZ remains today).
            today_2345 = now.replace(hour=23, minute=45, second=0, microsecond=0)
            next_dead_zone_exit = today_2345 if now < today_2345 else (
                today_2345 + timedelta(days=1)
            )
            # If a KZ is upcoming today OR is the very next day's first KZ
            # (e.g. shutdown at 23:46 UTC, Tokyo opens at 00:00 UTC the next
            # day), expire the marker just before that KZ so the watchdog
            # respawns the orch in time. 2-min buffer gives the watchdog
            # (15-min cron) one tick of headroom plus bootstrap time.
            # The ``next_dead_zone_exit`` fallback only fires when no KZ is
            # found at all — every live instrument has at least one KZ, so in
            # practice this is a defensive backstop for misconfigured/empty
            # ``_kz_windows``.
            buffer = timedelta(minutes=2)
            next_kz_start = self._next_kz_start_with_lookahead(now)
            if next_kz_start is not None:
                valid_until = next_kz_start - buffer
            else:
                valid_until = next_dead_zone_exit
            payload = {
                "symbol": self._symbol,
                "shutdown_at_utc": now.isoformat(),
                "valid_until_utc": valid_until.isoformat(),
                "reason": "all_kill_zones_complete_no_active_trade",
                "next_kz_start_utc": (
                    next_kz_start.isoformat() if next_kz_start else None
                ),
            }
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            logger.info(
                "Graceful shutdown marker written: %s (valid until %s; "
                "next KZ start: %s)",
                marker.name, valid_until.isoformat(),
                next_kz_start.isoformat() if next_kz_start else "none-today",
            )
        except OSError as e:
            logger.warning(
                "Graceful shutdown marker write failed (non-fatal): %s", e,
            )

    def _end_session(self):
        if self.candle_log:
            manifest = {
                "date": self.session_state["date"],
                "mode": self.mode,
                "candle_evaluations": self.candle_log,
                "trades_today": self.session_state["trades_today"],
                "session_memory_final": self.session_memory,
            }
            date_str = self.session_state.get("date", "unknown")
            path = f"knowledge_base/sessions/{date_str}_live_session.json"
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            atomic_write(path, manifest)
            logger.info(f"Session manifest saved: {path}")
        try:
            notify_daily_summary()
        except Exception:
            pass

    def _reconnect_trade_record(self):
        """After crash recovery, try to reconnect an adopted position to its trade record."""
        if not self.execution.active_trade:
            return
        try:
            reconnect_source = self._trade_record_from_last_crash_marker()
            if reconnect_source is None:
                reconnect_source = self._trade_record_from_pending_lifecycle_ticket()
            if reconnect_source is None:
                logger.warning(
                    "No open trade record found for adopted position ticket=%s "
                    "symbol=%s; vNext dynamic policy recovery remains pending",
                    getattr(self.execution.active_trade, "ticket", None),
                    self._symbol,
                )
                return
            record_path, record, recovery_reason = reconnect_source
            self._active_trade_record = record
            self._active_trade_record_path = str(record_path)
            trade = self.execution.active_trade
            record_trade_id = self._trade_id_from_record(record)
            if record_trade_id:
                trade.trade_id = record_trade_id
            if hasattr(self.execution, "hydrate_vnext_dynamic_policy_from_record"):
                hydrate_kwargs = {}
                if recovery_reason == "pending_lifecycle_ticket_match":
                    # This path repairs in-memory policy loss after an adopted
                    # open broker position. Final target repair is deliberately
                    # handled after partial-state hydration so recovered
                    # residuals cannot be partial-closed again.
                    hydrate_kwargs["modify_broker_tp"] = False
                    hydrate_kwargs["repair_recovered_sltp"] = True
                hydrated = self.execution.hydrate_vnext_dynamic_policy_from_record(
                    record,
                    **hydrate_kwargs,
                )
                trade = self.execution.active_trade
                logger.info(
                    "Adopted trade vNext dynamic policy recovery: "
                    "ticket=%s trade_id=%s hydrated=%s policy=%s "
                    "execution_policy_id=%s source=%s",
                    getattr(trade, "ticket", None),
                    getattr(trade, "trade_id", None),
                    hydrated,
                    getattr(trade, "gtos_vnext_dynamic_policy_selected", None),
                    getattr(trade, "gtos_vnext_execution_policy_id", None),
                    recovery_reason,
                )
            try:
                self._attach_pending_fill_execution_to_record(record)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Recovered trade execution capture attach failed: %s",
                    exc,
                )
            self._init_trade_tracking(trade)
            logger.info(
                "Reconnected trade record from %s: %s",
                recovery_reason,
                record_path,
            )
        except Exception as e:
            logger.warning("Failed to reconnect trade record: %s", e)

    @staticmethod
    def _record_has_terminal_exit(record: dict) -> bool:
        exit_data = record.get("exit") if isinstance(record.get("exit"), dict) else {}
        if not exit_data:
            return False
        terminal_keys = {
            "exit_reason",
            "exit_type",
            "close_time",
            "close_time_utc",
            "closed_at_utc",
            "realized_R",
            "actual_r",
            "broker_close_state",
            "close_deal_ticket",
            "broker_close_deal_id",
            "broker_close_order_id",
        }
        return any(exit_data.get(key) not in (None, "") for key in terminal_keys)

    @staticmethod
    def _record_has_unreconciled_broker_closed_exit(record: dict) -> bool:
        exit_data = record.get("exit") if isinstance(record.get("exit"), dict) else {}
        if not exit_data:
            return False
        return bool(
            str(exit_data.get("exit_type") or "").strip().lower() == "broker_closed"
            and exit_data.get("broker_deal_reconciled") is not True
            and exit_data.get("broker_close_deal_id") in (None, "", 0, "0")
            and exit_data.get("broker_close_order_id") in (None, "", 0, "0")
        )

    @classmethod
    def _record_usable_for_active_lifecycle_reconnect(cls, record: dict) -> bool:
        if not cls._record_has_terminal_exit(record):
            return True
        return cls._record_has_unreconciled_broker_closed_exit(record)

    @staticmethod
    def _supersede_unreconciled_broker_closed_exit(
        record: dict,
        *,
        lifecycle_row: dict | None,
        recovery_source: str,
    ) -> None:
        if not SessionOrchestrator._record_has_unreconciled_broker_closed_exit(record):
            return
        exit_data = dict(record.get("exit") or {})
        lifecycle = record.setdefault("lifecycle", {})
        lifecycle.setdefault(
            "stale_terminal_exit_superseded",
            {
                "reason": (
                    "unreconciled_broker_closed_exit_superseded_by_active_"
                    "broker_lifecycle_reconnect"
                ),
                "recovery_source": recovery_source,
                "lifecycle_trade_id": (lifecycle_row or {}).get("trade_id"),
                "lifecycle_candidate_id": (lifecycle_row or {}).get("candidate_id"),
                "lifecycle_ticket": (
                    (lifecycle_row or {}).get("mt5_position_ticket")
                    or (lifecycle_row or {}).get("trade_state_ticket")
                    or (lifecycle_row or {}).get("ticket")
                ),
                "superseded_exit": exit_data,
            },
        )
        record["exit"] = None
        instrumentation = record.setdefault("instrumentation", {})
        instrumentation["gtos_vnext_stale_terminal_exit_superseded"] = True
        instrumentation["gtos_vnext_stale_terminal_exit_superseded_reason"] = (
            "unreconciled_broker_closed_exit_superseded_by_active_broker_lifecycle_reconnect"
        )

    def _trade_record_from_last_crash_marker(self) -> tuple[Path, dict, str] | None:
        crash_path = Path("knowledge_base/meta/last_crash.json")
        if not crash_path.exists():
            return None
        with open(crash_path) as f:
            crash_data = json.load(f)
        record_path = crash_data.get("trade_record_path")
        if not record_path or not Path(record_path).exists():
            return None
        record = load_trade_record(record_path)
        if self._record_has_terminal_exit(record):
            return None
        return Path(record_path), record, "last_crash_marker"

    def _trade_record_from_pending_lifecycle_ticket(self) -> tuple[Path, dict, str] | None:
        trade = self.execution.active_trade
        if trade is None:
            return None
        lifecycle_row = self._latest_filled_lifecycle_row_for_active_trade()
        if lifecycle_row is None:
            return None
        record = None
        record_path = lifecycle_row.get("record_path")
        if record_path and Path(record_path).exists():
            candidate = load_trade_record(record_path)
            if self._record_usable_for_active_lifecycle_reconnect(candidate):
                self._supersede_unreconciled_broker_closed_exit(
                    candidate,
                    lifecycle_row=lifecycle_row,
                    recovery_source="pending_lifecycle_record_path",
                )
                self._augment_record_with_lifecycle_recovery_state(
                    candidate,
                    lifecycle_row,
                )
                record = candidate
                return Path(record_path), record, "pending_lifecycle_ticket_match"

        match_keys = {
            str(v)
            for v in (
                lifecycle_row.get("candidate_id"),
                lifecycle_row.get("trade_id"),
            )
            if v not in (None, "")
        }
        if not match_keys:
            return None

        base_path = self.config.get("trade_capture", {}).get(
            "base_path", "knowledge_base/trade_records",
        )
        symbol_dir = Path(base_path) / self._symbol
        if symbol_dir.exists():
            for path in sorted(
                symbol_dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            ):
                if path.name == "_pending_records_index.json":
                    continue
                try:
                    candidate = load_trade_record(str(path))
                except Exception:
                    continue
                if not self._record_usable_for_active_lifecycle_reconnect(candidate):
                    continue
                if self._record_matches_lifecycle_keys(candidate, match_keys):
                    self._supersede_unreconciled_broker_closed_exit(
                        candidate,
                        lifecycle_row=lifecycle_row,
                        recovery_source="pending_lifecycle_symbol_scan",
                    )
                    self._augment_record_with_lifecycle_recovery_state(
                        candidate,
                        lifecycle_row,
                    )
                    return path, candidate, "pending_lifecycle_ticket_match"

        record = self._trade_record_from_lifecycle_row(lifecycle_row)
        if record is not None:
            return (
                Path(
                    lifecycle_row.get("_recovery_source_path")
                    or PENDING_LIMIT_LIFECYCLE_LOG_PATH
                ),
                record,
                "pending_lifecycle_ticket_match",
            )
        return None

    def _augment_record_with_lifecycle_recovery_state(self, record: dict, row: dict) -> None:
        instrumentation = record.setdefault("instrumentation", {})
        lifecycle_status = str(row.get("broker_lifecycle_status") or "").upper()
        partial_closed = (
            "PARTIAL_CLOSED" in lifecycle_status
            or bool(row.get("partial_close_deal_tickets"))
            or bool(row.get("close_deal_tickets"))
        )
        recovered_partial_events = self._recovered_partial_close_events_from_slippage()
        if recovered_partial_events:
            partial_closed = True
        residual_open = (
            "RESIDUAL_OPEN" in lifecycle_status
            or row.get("open_position_present") is True
        )
        instrumentation["gtos_vnext_recovered_lifecycle_status"] = (
            lifecycle_status
            or instrumentation.get("gtos_vnext_recovered_lifecycle_status")
            or ""
        )
        if partial_closed or instrumentation.get("gtos_vnext_recovered_partial_closed") is None:
            instrumentation["gtos_vnext_recovered_partial_closed"] = partial_closed
        if recovered_partial_events:
            instrumentation["gtos_vnext_recovered_partial_close_events"] = (
                recovered_partial_events
            )
        if residual_open or instrumentation.get("gtos_vnext_recovered_residual_open") is None:
            instrumentation["gtos_vnext_recovered_residual_open"] = residual_open

    def _recovered_partial_close_events_from_slippage(self) -> list[dict]:
        trade = self.execution.active_trade if self.execution else None
        ticket = str(getattr(trade, "ticket", "") or "")
        if not ticket:
            return []
        path = Path(SLIPPAGE_LOG_PATH)
        if not path.exists():
            return []
        events: list[dict] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        matched_rows: list[dict] = []
        for line in lines:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if str(row.get("ticket") or "") != ticket:
                continue
            if str(row.get("symbol") or "") != str(self._symbol):
                continue
            matched_rows.append(row)

        def _positive(value):
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
            if math.isfinite(number) and number > 0:
                return number
            return None

        entry_rows = [
            row
            for row in matched_rows
            if str(row.get("slippage_event_type") or "").lower() == "entry"
            or str(row.get("partial_exit_lifecycle") or "").upper()
            == "ENTRY_FULL_POSITION_OPENED"
        ]
        entry_row = entry_rows[-1] if entry_rows else {}
        entry_price = _positive(
            entry_row.get("executed_entry_price") or entry_row.get("fill_price")
        )
        entry_stop = _positive(entry_row.get("executed_stop_price"))
        entry_sl_distance = _positive(entry_row.get("sl_distance"))
        if entry_sl_distance is None and entry_price is not None and entry_stop is not None:
            entry_sl_distance = abs(entry_price - entry_stop)
        entry_cash_risk = _positive(entry_row.get("cash_risk_amount"))
        entry_initial_volume = _positive(
            entry_row.get("initial_volume") or entry_row.get("executed_lot_size")
        )

        for row in matched_rows:
            is_partial = (
                row.get("partial_close") is True
                or str(row.get("partial_exit_lifecycle") or "").upper() == "PARTIAL_EXIT"
                or "PARTIAL" in str(row.get("close_event_type") or "").upper()
            )
            if not is_partial:
                continue
            time_in_trade_minutes = row.get("time_in_trade_minutes")
            try:
                if time_in_trade_minutes is not None and float(time_in_trade_minutes) < 0:
                    time_in_trade_minutes = None
            except (TypeError, ValueError):
                time_in_trade_minutes = None
            volume_closed = _positive(row.get("volume_closed") or row.get("executed_lot_size"))
            initial_volume = _positive(row.get("initial_volume")) or entry_initial_volume
            remaining_volume = _positive(row.get("remaining_volume"))
            if initial_volume is not None and volume_closed is not None:
                expected_remaining = max(initial_volume - volume_closed, 0.0)
                if remaining_volume is None or not math.isclose(
                    remaining_volume,
                    expected_remaining,
                    abs_tol=0.011,
                    rel_tol=1e-6,
                ):
                    remaining_volume = expected_remaining
            sl_distance = _positive(row.get("sl_distance")) or entry_sl_distance
            cash_risk_amount = _positive(row.get("cash_risk_amount")) or entry_cash_risk
            events.append(
                {
                    "type": "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG",
                    "time": row.get("close_time") or row.get("ts"),
                    "price": row.get("fill_price"),
                    "volume_closed": volume_closed,
                    "close_reason": row.get("close_reason"),
                    "mt5_order_id": row.get("mt5_order_id") or row.get("order_ticket"),
                    "mt5_deal_id": row.get("mt5_deal_id") or row.get("deal_ticket"),
                    "commission": row.get("commission"),
                    "swap": row.get("swap"),
                    "sl_at_breakeven": row.get("sl_at_breakeven"),
                    "time_in_trade_minutes": time_in_trade_minutes,
                    "initial_volume": initial_volume,
                    "remaining_volume": remaining_volume,
                    "sl_distance": sl_distance,
                    "cash_risk_amount": cash_risk_amount,
                    "recovery_source": SLIPPAGE_LOG_PATH,
                    "recovery_source_ts": row.get("ts"),
                }
            )
        return events

    @staticmethod
    def _trade_record_from_lifecycle_row(row: dict) -> dict | None:
        """Build the minimal record needed to recover vNext policy management."""
        if not isinstance(row, dict):
            return None
        selected_policy = (
            row.get("gtos_vnext_dynamic_policy_selected")
            or row.get("selected_policy")
        )
        execution_policy_id = (
            row.get("gtos_vnext_execution_policy_id")
            or row.get("execution_policy_id")
        )
        if not selected_policy or not execution_policy_id:
            return None

        trade_id = row.get("trade_id")
        candidate_id = row.get("candidate_id")

        def _first_text(*values) -> str | None:
            for value in values:
                if value not in (None, ""):
                    return str(value)
            return None

        parsed_date = None
        parsed_kill_zone = None
        parsed_candle_time = _first_text(
            row.get("candle_time_utc"),
            row.get("checked_candle_time_utc"),
            row.get("fill_time_utc"),
            row.get("entry_time_utc"),
            row.get("opened_at_utc"),
            row.get("timestamp_utc"),
        )
        if trade_id:
            match = re.search(r"_(\d{4}-\d{2}-\d{2})_(.+)_(\d{4})$", str(trade_id))
            if match:
                parsed_date = match.group(1)
                parsed_kill_zone = match.group(2)
                hhmm = match.group(3)
                if not parsed_candle_time:
                    parsed_candle_time = (
                        f"{parsed_date}T{hhmm[:2]}:{hhmm[2:]}:00+00:00"
                    )
        if parsed_candle_time:
            try:
                parsed_dt = datetime.fromisoformat(
                    str(parsed_candle_time).replace("Z", "+00:00")
                )
                if parsed_dt.tzinfo is None:
                    parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
                parsed_dt = parsed_dt.astimezone(timezone.utc)
                parsed_date = parsed_date or parsed_dt.strftime("%Y-%m-%d")
                parsed_candle_time = parsed_dt.isoformat()
            except ValueError:
                pass
        parsed_date = parsed_date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        parsed_kill_zone = _first_text(
            row.get("kill_zone"),
            row.get("session"),
            row.get("route_session"),
            parsed_kill_zone,
            "recovered_lifecycle",
        )
        parsed_candle_time = (
            parsed_candle_time
            or f"{parsed_date}T00:00:00+00:00"
        )
        instrumentation_fields = (
            "candidate_id",
            "trade_id",
            "gtos_vnext_dynamic_policy_selected",
            "gtos_vnext_dynamic_policy_applied",
            "gtos_vnext_dynamic_policy_replaced_policy",
            "gtos_vnext_dynamic_policy_candidate_action",
            "gtos_vnext_dynamic_policy_decision_status",
            "gtos_vnext_dynamic_policy_source_quality_action",
            "gtos_vnext_dynamic_policy_exit_management_action",
            "gtos_vnext_dynamic_policy_prop_action",
            "gtos_vnext_dynamic_policy_fixed_target_role",
            "gtos_vnext_execution_policy_id",
            "gtos_vnext_dynamic_be_trigger_r",
            "gtos_vnext_dynamic_final_target_r",
            "gtos_vnext_dynamic_trail_gap_r",
            "gtos_vnext_dynamic_momentum_pullback_r",
            "gtos_vnext_dynamic_time_stop_bars",
        )
        instrumentation = {
            field: row.get(field)
            for field in instrumentation_fields
            if row.get(field) is not None
        }
        lifecycle_status = str(row.get("broker_lifecycle_status") or "").upper()
        partial_closed = (
            "PARTIAL_CLOSED" in lifecycle_status
            or bool(row.get("partial_close_deal_tickets"))
            or bool(row.get("close_deal_tickets"))
        )
        residual_open = (
            "RESIDUAL_OPEN" in lifecycle_status
            or row.get("open_position_present") is True
        )
        instrumentation["gtos_vnext_dynamic_policy_selected"] = selected_policy
        instrumentation["gtos_vnext_execution_policy_id"] = execution_policy_id
        instrumentation.setdefault("gtos_vnext_dynamic_policy_applied", True)
        instrumentation["gtos_vnext_recovered_lifecycle_status"] = lifecycle_status
        instrumentation["gtos_vnext_recovered_partial_closed"] = partial_closed
        instrumentation["gtos_vnext_recovered_residual_open"] = residual_open
        return {
            "trade_id": trade_id,
            "metadata": {
                "trade_id": trade_id,
                "candidate_id": candidate_id,
                "date": parsed_date,
                "symbol": row.get("symbol") or row.get("broker_symbol"),
                "broker_symbol": row.get("broker_symbol"),
                "kill_zone": parsed_kill_zone,
                "candle_time": parsed_candle_time,
            },
            "limit_intent": {"trade_id": trade_id, "candidate_id": candidate_id},
            "instrumentation": instrumentation,
            "exit": None,
            "recovery_source": {
                "source": "pending_limit_lifecycle_row",
                "ticket_keys": [
                    row.get("ticket"),
                    row.get("trade_state_ticket"),
                    row.get("mt5_position_ticket"),
                    row.get("mt5_entry_order_ticket"),
                ],
                "source_path": row.get("_recovery_source_path"),
            },
        }

    def _latest_filled_lifecycle_row_for_active_trade(self) -> dict | None:
        trade = self.execution.active_trade
        if trade is None:
            return None
        ticket = str(getattr(trade, "ticket", "") or "")
        if not ticket:
            return None
        paths = [
            Path(PENDING_LIMIT_LIFECYCLE_LOG_PATH),
            Path(LANE06_BROKER_LIFECYCLE_LOG_PATH),
        ]
        ticket_fields = (
            "ticket",
            "trade_state_ticket",
            "mt5_position_ticket",
            "mt5_entry_order_ticket",
            "mt5_order_ticket",
            "pending_ticket",
        )
        ticket_list_fields = (
            "entry_order_tickets",
            "entry_deal_tickets",
            "close_order_tickets",
        )
        for path in paths:
            if not path.exists():
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            for line in reversed(lines):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if str(row.get("symbol") or "") != str(self._symbol):
                    continue
                row_tickets = {
                    str(row.get(field) or "") for field in ticket_fields
                }
                for field in ticket_list_fields:
                    values = row.get(field)
                    if isinstance(values, list):
                        row_tickets.update(str(value) for value in values)
                open_snapshot = row.get("open_position_snapshot")
                if isinstance(open_snapshot, dict):
                    row_tickets.add(str(open_snapshot.get("ticket") or ""))
                    row_tickets.add(str(open_snapshot.get("identifier") or ""))
                if ticket not in row_tickets:
                    continue
                filled = (
                    str(row.get("broker_fill_state") or "").lower() == "filled"
                    or row.get("order_send_success") is True
                    or (
                        row.get("schema_version") == "lane06_broker_lifecycle_v1"
                        and row.get("selected_policy")
                        and row.get("execution_policy_id")
                    )
                )
                if not filled:
                    continue
                row_side = str(row.get("side") or "").upper()
                trade_side = str(getattr(trade, "direction", "") or "").upper()
                if row_side and trade_side and row_side != trade_side:
                    continue
                row["_recovery_source_path"] = str(path)
                return row
        return None

    @staticmethod
    def _record_matches_lifecycle_keys(record: dict, match_keys: set[str]) -> bool:
        return bool(match_keys & SessionOrchestrator._trade_record_identity_keys(record))

    @staticmethod
    def _trade_id_from_record(record: dict) -> str:
        for key in (
            ("limit_intent", "trade_id"),
            ("instrumentation", "trade_id"),
            ("metadata", "trade_id"),
        ):
            value = (record.get(key[0]) or {}).get(key[1])
            if value:
                return str(value)
        return str(record.get("trade_id") or "")

    @staticmethod
    def _trade_record_identity_keys(record: dict) -> set[str]:
        keys: set[str] = set()

        def add(value):
            if value not in (None, ""):
                keys.add(str(value))

        add(record.get("trade_id"))
        moonshot_candidate = record.get("moonshot_broader_origin_candidate") or {}
        add(moonshot_candidate.get("candidate_id"))
        add(moonshot_candidate.get("trade_id"))
        add(moonshot_candidate.get("broader_origin_candidate_id"))
        ai_response = record.get("ai_response") or {}
        add(ai_response.get("candidate_id"))
        add(ai_response.get("trade_id"))
        add(ai_response.get("broader_origin_candidate_id"))
        for container_name in ("metadata", "limit_intent", "instrumentation"):
            container = record.get(container_name) or {}
            for field in (
                "trade_id",
                "candidate_id",
                "broader_origin_candidate_id",
            ):
                add(container.get(field))
        packet = (
            (record.get("decision_pipeline") or {})
            .get("gtos_vnext_candidate_intelligence_packet")
            or {}
        )
        identity = packet.get("candidate_identity") or {}
        for field in (
            "trade_id",
            "candidate_id",
            "broader_origin_candidate_id",
        ):
            add(identity.get(field))
            add(packet.get(field))
        return keys

    def _recover_pending_record_path(self) -> None:
        """Reattach _pending_trade_record_path to a restored pending_intent.

        On restart, execution._load_pending_intent() may restore a live intent
        from disk, but the orchestrator's record path is in-memory only.

        T2.6: recovery is a deterministic trade_id -> path lookup against the
        ``_pending_records_index.json`` written at LIMIT_PLACED save time.
        Falls back to the legacy glob scan when the index is missing or does
        not carry the intent (pre-fix state / manual file moves / wipe).  In
        both paths, a record whose ``exit`` block is populated is skipped --
        that record is from a completed fill, not the live intent.

        Safe-no-op if nothing matches.  Failure is NOT silent: the warning
        log site is promoted to a Telegram alert via T2.7.
        """
        if self.execution is None or self.execution.pending_intent is None:
            return
        intent = self.execution.pending_intent
        try:
            base_path = self.config.get("trade_capture", {}).get(
                "base_path", "knowledge_base/trade_records",
            )

            # Primary: trade_id -> path index lookup (race-free, O(1))
            indexed_path = lookup_pending_record(
                intent.trade_id, self._symbol, base_path,
            )
            if indexed_path and Path(indexed_path).exists():
                try:
                    rec = load_trade_record(indexed_path)
                except Exception:
                    rec = None
                if rec and not self._record_has_terminal_exit(rec):
                    self._pending_trade_record_path = indexed_path
                    logger.info(
                        "Recovered pending trade record path on restart "
                        "(index hit): %s",
                        self._pending_trade_record_path,
                    )
                    return

            # Fallback: legacy glob scan (pre-fix state or index corruption)
            symbol_dir = Path(base_path) / self._symbol
            attempted_path = indexed_path or str(symbol_dir)
            if symbol_dir.is_dir():
                for path in symbol_dir.glob("*.json"):
                    if path.name == "_pending_records_index.json":
                        continue
                    try:
                        rec = load_trade_record(str(path))
                    except Exception:
                        continue
                    if not rec:
                        continue
                    limit_info = rec.get("limit_intent") or {}
                    if limit_info.get("trade_id") != intent.trade_id:
                        continue
                    if self._record_has_terminal_exit(rec):
                        continue
                    self._pending_trade_record_path = str(path)
                    logger.info(
                        "Recovered pending trade record path on restart "
                        "(glob fallback): %s",
                        self._pending_trade_record_path,
                    )
                    # Backfill the index for next restart
                    try:
                        index_pending_record(
                            trade_id=intent.trade_id,
                            record_path=str(path),
                            symbol=self._symbol, base_path=base_path,
                        )
                    except Exception:
                        pass
                    return
            self._alert_pending_record_recovery_failed(
                intent.trade_id, attempted_path,
            )
        except Exception as e:
            logger.warning("Pending record path recovery failed: %s", e)
            try:
                self._alert_pending_record_recovery_failed(
                    intent.trade_id, "<exception>", detail=str(e),
                )
            except Exception:
                pass

    def _alert_pending_record_recovery_failed(
        self, trade_id: str, attempted_path: str, detail: str = "",
    ) -> None:
        """Warn-log + Telegram alert when recovery cannot find a record.

        T2.7: promote the silent analytics failure to a Telegram alert so the
        CEO sees it immediately.  Uses the lazy-import pattern from
        scripts/correlation_shock_monitor.py so a misconfigured notifier
        cannot block the orchestrator.
        """
        logger.warning(
            "pending_intent %s restored but no matching trade record found "
            "(attempted=%s) — exit data for this fill will not be captured.",
            trade_id, attempted_path,
        )
        try:
            from src.notifications import notify_alert
            # Plain-text body per HTML-ESCAPE BUG fix policy (2026-04-28).
            text = (
                f"PENDING RECORD RECOVERY FAILED\n"
                f"Symbol: {self._symbol}\n"
                f"Trade ID: {trade_id}\n"
                f"Attempted: {attempted_path}\n"
                f"Exit data will NOT be captured if this intent fills. "
                f"Manual investigation required."
            )
            if detail:
                text += f"\nDetail: {detail}"
            notify_alert(text)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "pending_record_recovery: notify_alert failed (%s)", exc,
            )

    def _handle_crash(self, error: Exception):
        self._abnormal_shutdown_reason = f"unhandled_exception: {error}"
        crash_data = {
            "time": datetime.now(timezone.utc).isoformat(),
            "error": str(error),
            "session_state": self.session_state,
            "active_trade": (self.execution.active_trade.__dict__
                             if self.execution and self.execution.active_trade else None),
            "trade_record_path": self._active_trade_record_path,
        }
        path = "knowledge_base/meta/last_crash.json"
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        atomic_write(path, crash_data)

    # ------------------------------------------------------------------
    # OB Retest Event Logger — edge decay monitoring
    # ------------------------------------------------------------------
    def _log_ob_retest_event(self, mso, current_price: float) -> None:
        """Log every H1 OB retest for edge decay monitoring.

        Runs on every candle BEFORE the AI evaluates, so we track ALL
        retested OBs — not just the ones the AI decides to trade.
        """
        h1 = mso.timeframes.get("H1") if hasattr(mso, "timeframes") else None
        if not h1 or not h1.order_blocks:
            return

        symbol = self._symbol
        log_path = f"knowledge_base/meta/ob_retest_events_{symbol}.json"

        events: list[dict] = []
        if os.path.exists(log_path):
            try:
                with open(log_path) as f:
                    events = json.load(f)
            except Exception:
                events = []

        new_events = False
        for ob in h1.order_blocks:
            if ob.mitigated:
                continue
            if not (ob.low <= current_price <= ob.high):
                continue

            # Deduplicate: skip if same zone already logged
            already = any(
                abs(e["ob_zone_high"] - ob.high) < 0.5
                and abs(e["ob_zone_low"] - ob.low) < 0.5
                for e in events
            )
            if already:
                continue

            events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "symbol": symbol,
                "ob_zone_high": ob.high,
                "ob_zone_low": ob.low,
                "ob_type": ob.type,
                "entry_price": current_price,
                "causing_event": ob.causing_event_type,
                "formation_time": ob.formation_time,
                "outcome": "PENDING",
            })
            new_events = True
            logger.info(
                "OB_RETEST_EVENT: %s %s zone %.5f-%.5f (price=%.5f)",
                symbol, ob.type, ob.low, ob.high, current_price,
            )

        if new_events:
            Path(log_path).parent.mkdir(parents=True, exist_ok=True)
            atomic_write(log_path, events)

    def _log_candle(self, decision: str, detail: str, kill_zone: str,
                    extended_kz: bool = False, kz_sub_window: str = "",
                    produced_candidate: bool = False):
        # Bug 4 (Thursday 2026-04-23 audit): ``produced_candidate`` flags a
        # candle whose AI evaluation returned CANDIDATE, REGARDLESS of
        # whether a downstream gate (L2, permissions, correlation, etc.)
        # later rejected it. Session summaries use this flag to count
        # AI-produced candidates correctly — before the fix, a CANDIDATE
        # that got REJECTED_L2 logged only the REJECTED_L2 decision,
        # leaving ``decisions.CANDIDATE`` at 0 even when the AI clearly
        # produced candidates. Decision remains the terminal outcome so
        # downstream readers that only consume ``decision`` are unchanged.
        entry = {
            "time": datetime.now(timezone.utc).isoformat(),
            "kill_zone": kill_zone,
            "decision": decision,
            "detail": detail,
        }
        if extended_kz:
            entry["extended_kz"] = True
            entry["kz_sub_window"] = kz_sub_window
        if produced_candidate:
            entry["produced_candidate"] = True
        self.candle_log.append(entry)

        # Write signal for MT5 ChartMarker EA
        self._write_chart_signal(entry)

    def _write_no_trade_record(
        self,
        reason: str,
        kill_zone: str,
        candle_time: str = "",
        analysis_dict: dict | None = None,
    ):
        """Persist a NoTradeRecord to knowledge_base/no_trades/ (non-blocking)."""
        from src.models.trade_models import NoTradeRecord, NoTradeReasoning
        try:
            now = datetime.now(timezone.utc)
            record_id = f"nt_{now.strftime('%Y-%m-%d_%H%M')}"
            reasoning_data = (analysis_dict or {}).get("reasoning", {})
            bias_info = reasoning_data.get("daily_bias", {})
            record = NoTradeRecord(
                record_id=record_id,
                date=now.strftime("%Y-%m-%d"),
                candle_time=candle_time or now.isoformat(),
                reason=reason[:500],
                reasoning=NoTradeReasoning(
                    daily_bias=str(bias_info.get("direction", "")),
                    h4_alignment=str(reasoning_data.get("h4_alignment", {}).get("aligned", "")),
                    full_explanation=str(reasoning_data.get("overall_reasoning", ""))[:1000],
                ),
            )
            self.kb.write_no_trade(record)
        except Exception as e:
            logger.debug("write_no_trade failed (non-blocking): %s", e)

    def _write_chart_signal(self, entry: dict):
        """Append a signal line to the MT5 Files directory for ChartMarker EA.

        The EA polls this file every 5 seconds and draws markers on the chart.
        Each line is a JSON object with time, decision, detail, and price,
        plus an additive set of structured fields when available so the EA
        can render direction-coloured arrows, SL/TP horizontal lines, an
        info panel with active-trade R, and KZ-aware tooltips. The structured
        fields are OPTIONAL — older readers (and the bare-bones v1
        ChartMarker.mq5) ignore them safely.
        """
        try:
            # Get current price for marker placement
            tick = self.mt5.get_tick(self._mt5_symbol) if self.mt5 else None
            price = tick.bid if tick else 0

            # Build signal line — required fields first (back-compat).
            signal = {
                "time": entry["time"],
                "decision": entry["decision"],
                "detail": entry.get("detail", "")[:80],
                "price": round(price, 5),
            }

            # Additive structured context for the v2 EA. Each block is wrapped
            # so a None/missing source never blocks the write.
            kz = entry.get("kill_zone")
            if kz:
                signal["kill_zone"] = kz

            active = getattr(self.execution, "active_trade", None) if self.execution else None
            pending = getattr(self.execution, "pending_intent", None) if self.execution else None

            if active is not None:
                signal["direction"] = active.direction
                signal["trade_id"] = active.trade_id
                if active.stop_loss:
                    signal["sl"] = round(float(active.stop_loss), 5)
                if active.take_profit_1:
                    signal["tp1"] = round(float(active.take_profit_1), 5)
                if active.take_profit_2:
                    signal["tp2"] = round(float(active.take_profit_2), 5)
                if active.take_profit_3:
                    signal["tp3"] = round(float(active.take_profit_3), 5)
                if active.initial_volume:
                    signal["lots"] = round(float(active.initial_volume), 2)
                if getattr(active, "j46_j49_active", False):
                    signal["j46_j49_active"] = True
                if getattr(active, "original_ai_tp1", 0.0):
                    signal["original_ai_tp1"] = round(float(active.original_ai_tp1), 5)
            elif pending is not None:
                signal["direction"] = pending.direction
                signal["trade_id"] = pending.trade_id
                if pending.stop_loss:
                    signal["sl"] = round(float(pending.stop_loss), 5)
                if pending.take_profit_1:
                    signal["tp1"] = round(float(pending.take_profit_1), 5)
                if getattr(pending, "limit_price", 0.0):
                    signal["limit_price"] = round(float(pending.limit_price), 5)
                if getattr(pending, "risk_pct", 0.0):
                    signal["risk_pct"] = round(float(pending.risk_pct), 3)

            # MT5 Files directory — where the EA can read
            mt5_files = Path(os.environ.get(
                "MT5_FILES_DIR",
                str(Path.home() / "AppData/Roaming/MetaQuotes/Terminal"
                    / "D0E8209F77C8CF37AD8BF550E51FF075/MQL5/Files"),
            ))
            mt5_files.mkdir(parents=True, exist_ok=True)

            # Filename MUST match the chart symbol: ChartMarker.mq5 does
            # `StringReplace(Symbol(), ".", "_")` and reads that file. The
            # chart's Symbol() is the broker symbol (our _mt5_symbol), so we
            # mirror the same transform here. Under FTMO US30 chart="US30.cash"
            # → agent_signals_US30_cash.jsonl; under redacted_account US30 chart="US30"
            # → agent_signals_US30.jsonl. Using self._symbol would freeze the
            # filename to "US30_cash" and break the EA under FN.
            safe_sym = self._mt5_symbol.replace(".", "_")
            signal_file = mt5_files / f"agent_signals_{safe_sym}.jsonl"

            # ensure_ascii=False so MT5 reads em-dashes / smart quotes /
            # ellipsis as their actual UTF-8 bytes rather than \uXXXX
            # escapes (the v1 ChartMarker had no decoder; v2 maps the
            # common typography escapes back to ASCII as a safety net).
            with open(signal_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(signal, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.debug("Chart signal write failed (non-critical): %s", e)

    def _load_config(self, path: str, symbol: str | None = None,
                     profile: str | None = None) -> dict:
        with open(path) as f:
            raw = yaml.safe_load(f)
        resolved_profile = resolve_profile(profile)
        config = apply_profile_overrides(raw, resolved_profile)
        config = apply_instrument_overrides(config, symbol)

        # Profile overlays own account-scoped queue paths in dual-broker live
        # mode; apply before any alert can instantiate the queue singleton.
        from src.utils.notification_queue import configure_from_config as _configure_notification_queue
        _configure_notification_queue(config)

        # Configure Telegram $/R conversion against the resolved risk%
        # (profile overlay + instrument overlay already applied). Without this,
        # notifications.py keeps its $100K × 2% = $2000/R legacy default — wrong
        # whenever the active profile/instrument risk differs from base config.
        resolved_risk_pct = config.get("risk", {}).get("risk_per_trade_pct")
        if resolved_risk_pct is not None:
            from src.notifications import configure_notifications
            configure_notifications(
                risk_per_trade_pct=float(resolved_risk_pct),
                account_balance=100_000.0,
            )

        resolved_symbol = config.get("market", {}).get("symbol", "XAUUSD")
        logger.info(
            "Config loaded for %s [profile=%s]: risk_per_trade=%s%%, "
            "reduced_risk=%s%%, KZ_london=%s-%s, KZ_ny=%s-%s, "
            "SL_floor=%s, max_spread=%s",
            resolved_symbol,
            resolved_profile or "base",
            config.get("risk", {}).get("risk_per_trade_pct", "?"),
            config.get("drawdown_reduction", {}).get("reduced_risk_pct", "?"),
            config.get("market", {}).get("kill_zones", {}).get("london", {}).get("start_utc", "?"),
            config.get("market", {}).get("kill_zones", {}).get("london", {}).get("end_utc", "?"),
            config.get("market", {}).get("kill_zones", {}).get("ny", {}).get("start_utc", "?"),
            config.get("market", {}).get("kill_zones", {}).get("ny", {}).get("end_utc", "?"),
            config.get("risk", {}).get("sl_absolute_min", "?"),
            config.get("risk", {}).get("max_spread_cents", "?"),
        )
        return config

    def _load_economic_calendar(self) -> list[dict]:
        """Load economic calendar at init. Failures degrade gracefully."""
        cal_cfg = self.config.get("economic_calendar", {})
        if not cal_cfg.get("enabled", False):
            logger.info("Economic calendar disabled in config")
            return []
        filepath = cal_cfg.get("calendar_file", "data/economic_calendar.csv")
        try:
            return load_calendar(filepath)
        except Exception as e:
            logger.warning(
                "Failed to load economic calendar: %s. "
                "Trading without event awareness.", e
            )
            return []


def prescreen_mso(mso) -> tuple[bool, str]:
    """Pre-screen: at least one of D1/H4 must provide clear direction.

    If D1 is clear, H4 must agree (original behaviour).
    If D1 is unclear but H4 is clearly directional, allow through —
    the AI will use H4+H1 consensus via U1.
    Only skip when BOTH D1 and H4 lack clear direction.
    """
    tfs = mso.timeframes if hasattr(mso, "timeframes") else {}

    d1 = tfs.get("D1")
    d1_dir = d1.structure.direction if d1 else "insufficient_data"

    h4 = tfs.get("H4")
    h4_dir = h4.structure.direction if h4 else "insufficient_data"

    d1_clear = d1_dir in ("bullish", "bearish")
    h4_clear = h4_dir in ("bullish", "bearish")

    # Both unclear → no directional consensus possible, skip
    if not d1_clear and not h4_clear:
        return False, f"L1_no_direction_d1_{d1_dir}_h4_{h4_dir}"

    # D1 clear but H4 conflicts → skip
    if d1_clear and h4_clear and h4_dir != d1_dir:
        return False, f"L2_h4_conflict_{h4_dir}_vs_d1_{d1_dir}"

    # D1 clear + H4 agrees → pass (original path)
    # D1 unclear + H4 clear → pass (new: AI uses H4+H1 consensus)
    # D1 clear + H4 unclear → pass (D1 provides direction)
    return True, ""
