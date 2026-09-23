"""Component 4 — Execution Engine.

Handles all MT5 order operations with safety-first design.

CRITICAL RULES:
1. NEVER retry an order without checking positions first (safe_place_order)
2. After every partial close, discover the new ticket number
3. After every SL/TP modification failure, keep the existing broker SL/TP
   untouched, record actionable diagnostics, and alert when required
4. All operations write checkpoints before executing
"""

from __future__ import annotations

import json
import hashlib
import logging
import math
import os
import pickle
import time
import concurrent.futures
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from src.mt5.mt5_interface import (
    MAGIC_NUMBER,
    MT5Interface,
    OrderResult,
    PositionInfo,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_SLTP,
)
from src.utils.broker_profile import broker_account_namespace, namespaced_file_path
from src.utils.file_io import atomic_write
from src.components.pending_limit_lifecycle_logger import (
    record_pending_limit_lifecycle,
)
from src.components.broker_net_cost_engine import (
    build_pretrade_cost_packet,
    pretrade_cost_refusal_reason,
)
from src.components.broker_order_lifecycle_capture_v4 import (
    build_broker_order_lifecycle_capture_v4,
    record_broker_order_lifecycle_capture_v4,
)
from src.components.execution_manager_v4 import (
    evaluate_execution_manager_v4,
    record_execution_manager_v4_decision,
)
from src.components.pending_nofill_lifecycle_v4 import build_risk_reservation
from src.components.slippage_shadow_logger import record_close_slippage, record_slippage
from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.components.same_symbol_lifecycle_v4 import (
    record_same_symbol_lifecycle_entry_v4,
)
from src.components.exit_policy_v4 import (
    ExitPolicyConfigV4,
    ExitPolicyDecisionV4,
    ExitPolicyInputV4,
    evaluate_exit_policy_v4,
)
from src.safety.runtime_halt import RuntimeHaltError, enforce_runtime_not_halted

logger = logging.getLogger(__name__)

#: Step-count tolerance for broker volume-step alignment. See `_normalize_volume`:
#: a quotient that is mathematically an exact integer can land a few ULPs below one in
#: binary floating point, and truncating it strands a position that cannot be closed.
#: Sized to absorb float error (~1e-12 at ten thousand steps) without being large enough
#: to promote a genuinely mis-aligned volume to the next step.
_VOLUME_STEP_EPSILON = 1e-9

CHECKPOINT_PATH = "knowledge_base/meta/execution_checkpoint.json"
PENDING_INTENT_DIR = "knowledge_base/meta"
PENDING_INTENT_MAX_AGE_HOURS = 24
INTERNAL_PENDING_ORDER_MODE = "INTERNAL_CANDLE_POLLED_INTENT"
SUPPORTED_VNEXT_DYNAMIC_EXECUTION_POLICIES = {
    "be_after_trigger",
    "partial_be_runner",
    "trailing_runner",
    "momentum_exhaustion",
    "time_stop",
}


def clear_all_pending_intent_files(
    reason: str = "manual",
    *,
    pending_dir: str | Path | None = None,
) -> dict:
    """Delete all persisted internal pending-limit intent files.

    T2.8 daily-loss-stop semantics are portfolio-wide: once the MTM daily cap
    is hit, no symbol should be able to resurrect an old software limit after
    a restart. Live in-memory intents are still cancelled by their owning
    orchestrator process when it sees the dormant marker; this helper clears
    the persisted files that would otherwise survive process restarts.
    """
    directory = Path(pending_dir) if pending_dir is not None else Path(PENDING_INTENT_DIR)
    result = {
        "reason": reason,
        "pending_dir": str(directory),
        "cleared_files": [],
        "failed_files": [],
    }
    try:
        paths = sorted(directory.glob("pending_intent_*.pkl"))
    except OSError as exc:
        result["failed_files"].append({"path": str(directory), "error": str(exc)})
        logger.warning("Failed to enumerate pending intent files: %s", exc)
        return result

    for path in paths:
        try:
            path.unlink()
            result["cleared_files"].append(str(path))
        except OSError as exc:
            result["failed_files"].append({"path": str(path), "error": str(exc)})
            logger.warning("Failed to delete pending intent file %s: %s", path, exc)
    if result["cleared_files"]:
        logger.info(
            "Cleared %d persisted pending intent file(s) for %s",
            len(result["cleared_files"]),
            reason,
        )
    return result


@dataclass
class TradeState:
    """Tracks the current state of an active trade."""
    ticket: int
    direction: str  # "LONG" or "SHORT"
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    initial_volume: float
    current_volume: float
    sl_distance: float
    tp1_hit: bool = False
    tp2_hit: bool = False
    sl_at_breakeven: bool = False
    trade_id: str = ""
    entry_time: str = ""
    partial_close_events: list = field(default_factory=list)
    original_ai_tp1: float = 0.0
    j46_j49_active: bool = False
    entry_order_ticket: Optional[int] = None
    entry_deal_ticket: Optional[int] = None
    entry_order_retcode: Optional[int] = None
    source_repair_identity: Optional[dict] = None
    gtos_vnext_source_event_hash: Optional[str] = None
    gtos_vnext_source_event_details: Optional[dict] = None
    gtos_vnext_activation_family: Optional[str] = None
    gtos_vnext_origin_family: Optional[str] = None
    gtos_vnext_selector_row_id: Optional[str] = None
    gtos_vnext_selector_proof_hash: Optional[str] = None
    gtos_vnext_execution_policy_id: Optional[str] = None
    gtos_vnext_dynamic_policy_selected: Optional[str] = None
    gtos_vnext_dynamic_policy_applied: bool = False
    gtos_vnext_dynamic_policy_replaced_policy: Optional[str] = None
    gtos_vnext_dynamic_policy_candidate_action: Optional[str] = None
    gtos_vnext_dynamic_policy_decision_status: Optional[str] = None
    gtos_vnext_dynamic_policy_source_quality_action: Optional[str] = None
    gtos_vnext_dynamic_policy_exit_management_action: Optional[str] = None
    gtos_vnext_dynamic_policy_prop_action: Optional[str] = None
    gtos_vnext_dynamic_policy_fixed_target_role: Optional[str] = None
    gtos_vnext_target_stop_geometry_v4: Optional[dict] = None
    gtos_vnext_selected_cell_risk_pct: Optional[float] = None
    gtos_vnext_selected_cell_risk_cell_id: Optional[str] = None
    gtos_vnext_selected_cell_risk_decision_basis: Optional[str] = None
    gtos_vnext_selected_cell_risk_selected_policy: Optional[str] = None
    gtos_vnext_selected_cell_risk_source_policy: Optional[str] = None
    gtos_vnext_selected_cell_risk_policy_identity_status: Optional[str] = None
    gtos_vnext_dynamic_be_after_trigger_active: bool = False
    gtos_vnext_dynamic_be_trigger_r: float = 0.0
    gtos_vnext_dynamic_final_target_r: float = 0.0
    gtos_vnext_dynamic_broker_take_profit_mode: Optional[str] = None
    gtos_vnext_dynamic_no_broker_take_profit: bool = False
    gtos_vnext_dynamic_be_trigger_price: float = 0.0
    gtos_vnext_dynamic_final_target_price: float = 0.0
    gtos_vnext_dynamic_placement_be_trigger_price: float = 0.0
    gtos_vnext_dynamic_placement_final_target_price: float = 0.0
    gtos_vnext_dynamic_trail_gap_r: float = 0.0
    gtos_vnext_dynamic_momentum_pullback_r: float = 0.0
    gtos_vnext_dynamic_mfe_r: float = 0.0
    gtos_vnext_dynamic_mae_r: float = 0.0
    gtos_vnext_dynamic_trail_stop_r: float = 0.0
    gtos_vnext_dynamic_time_stop_bars: Optional[int] = None
    # Replay-parity consecutive below-threshold close streak for the Exit
    # Policy V4 adverse-close abort (counts closed M15 bars whose close
    # progress <= abort_close_below_r; reset on any bar above; candle-time
    # marker dedupes multiple evaluations inside one bar).
    gtos_vnext_abort_below_close_streak: int = 0
    gtos_vnext_abort_streak_candle_time: Optional[str] = None
    gtos_vnext_execution_manager_v4_status: Optional[str] = None
    gtos_vnext_execution_manager_v4_action: Optional[str] = None
    gtos_vnext_execution_manager_v4_fatal_reasons: list[str] = field(default_factory=list)
    gtos_vnext_execution_manager_v4_warning_reasons: list[str] = field(default_factory=list)
    gtos_vnext_execution_manager_v4_packet: Optional[dict] = None
    gtos_vnext_broker_order_lifecycle_capture_v4_packet: Optional[dict] = None
    gtos_vnext_prop_firm_headroom_snapshot_v4: Optional[dict] = None
    gtos_vnext_prop_firm_headroom_v4_packet: Optional[dict] = None
    gtos_vnext_profit_harvest_mfe_capture_v4_enabled: bool = False
    gtos_vnext_profit_harvest_min_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_trail_gap_r: float = 0.0
    gtos_vnext_profit_harvest_protect_floor_r: float = 0.0
    gtos_vnext_profit_harvest_close_on_giveback_r: float = 0.0
    gtos_vnext_profit_harvest_stale_minutes: Optional[int] = None
    gtos_vnext_profit_harvest_stale_min_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_stale_close_below_r: float = 0.0
    gtos_vnext_profit_harvest_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_last_progress_r: float = 0.0
    gtos_vnext_profit_harvest_triggered: bool = False
    gtos_vnext_profit_harvest_last_action: Optional[str] = None
    account_balance_at_entry: float = 0.0
    risk_pct_at_entry: float = 0.0
    cash_risk_amount: float = 0.0
    cash_risk_amount_source: str = ""
    cash_risk_amount_status: str = ""
    broker_cash_risk_per_lot: float = 0.0
    broker_lot_sizing_diagnostic: Optional[dict] = None
    gtos_vnext_pretrade_cost_model: Optional[dict] = None
    # Set to True the first time ``check_and_manage_trade`` sees this
    # ticket in ``mt5.positions_get()``. Until then, an empty positions list
    # is NOT treated as ``broker_closed`` — MT5's internal propagation can
    # lag ~10-50ms behind a successful ``order_send``. Without this guard,
    # a polling race within ~13ms of fill can falsely retire the trade
    # (observed live 2026-04-29 NAS100 ticket 234432798).
    position_confirmed: bool = False
    # W7 ultimate_book trades own their exit at the BROKER (SL=-1R / TP=final_target_r) plus the
    # per-trade time-stop. When True, ``check_and_manage_trade`` skips the per-symbol orchestrator
    # exit overlays (profit-harvest MFE capture, exit_policy_v4, momentum/trailing dispatch) so the
    # book's validated native exit is NOT overwritten. Defaults False -> the orchestrator path runs
    # all overlays exactly as before.
    gtos_vnext_book_native_exit_management: bool = False


@dataclass
class PendingLimitIntent:
    """Pending limit order — checked each M15 candle by the orchestrator.

    Fills when candle.low <= limit_price (LONG) or candle.high >= limit_price (SHORT).
    Expires after 24 clock-hours from placed_time regardless of candle count.
    expiry_candles is retained for logging only (KZ candles elapsed at expiry).
    This is candle-level polling, not a native MT5 pending order. No broker
    pending order exists until the orchestrator later sees the limit touched
    and calls open_trade() as a market order.

    schema_version guards against reading a pickle produced by a prior code
    revision whose field layout no longer matches. Bump on breaking changes;
    _load_pending_intent discards and deletes any file whose schema_version
    does not match the current code.
    """
    direction: str
    limit_price: float
    stop_loss: float
    take_profit_1: float
    risk_pct: float
    expiry_candles: int = 192
    candles_elapsed: int = 0
    trade_id: str = ""
    placed_time: str = ""
    account_balance: float = 0.0
    candidate_id: str | None = None
    decision_time_utc: str | None = None
    source_file: str | None = None
    source_hash: str | None = None
    source_symbol: str | None = None
    session: str | None = None
    kill_zone: str | None = None
    regime: str | None = None
    decision_spread_value_source_safe: float | None = None
    decision_spread_unit: str | None = None
    gtos_vnext_pre_ai_action: str | None = None
    gtos_vnext_pre_ai_recommended_side: str | None = None
    gtos_vnext_pre_ai_recommended_frameworks: list[str] | None = None
    gtos_vnext_decision: str | None = None
    gtos_vnext_reason: str | None = None
    gtos_vnext_matched: bool | None = None
    gtos_vnext_matched_rows: int | None = None
    gtos_vnext_matched_rows_status: str | None = None
    gtos_vnext_broader_origin_selected_rows: int | None = None
    gtos_vnext_broader_origin_performance_rows: int | None = None
    gtos_vnext_cost_adjusted_r_sum: float | None = None
    gtos_vnext_proxy_score_sum: float | None = None
    gtos_vnext_stress_r_sum: float | None = None
    gtos_vnext_effective_n_sum: float | None = None
    gtos_vnext_risk_multiplier: float | None = None
    gtos_vnext_risk_would_multiplier: float | None = None
    gtos_vnext_risk_reason: str | None = None
    gtos_vnext_pending_policy_action: str | None = None
    gtos_vnext_pending_policy_would_action: str | None = None
    gtos_vnext_pending_policy_applied: bool | None = None
    gtos_vnext_pending_policy_reason: str | None = None
    gtos_vnext_ltf_path_action: str | None = None
    gtos_vnext_ltf_path_would_action: str | None = None
    gtos_vnext_ltf_path_applied: bool | None = None
    gtos_vnext_ltf_path_reason: str | None = None
    gtos_vnext_ltf_path_monitor_timeframe: str | None = None
    gtos_vnext_ltf_path_adjusted_entry_price: float | None = None
    gtos_vnext_prop_safe_selector_action: str | None = None
    gtos_vnext_prop_safe_selector_would_action: str | None = None
    gtos_vnext_prop_safe_selector_applied: bool | None = None
    gtos_vnext_prop_safe_selector_after_risk_pct: float | None = None
    gtos_vnext_prop_safe_selector_reason: str | None = None
    gtos_vnext_prop_firm_headroom_snapshot_v4: dict | None = None
    gtos_vnext_prop_firm_headroom_v4_packet: dict | None = None
    gtos_vnext_selector_v4_action: str | None = None
    gtos_vnext_selector_v4_reason: str | None = None
    gtos_vnext_selector_v4_packet: dict | None = None
    gtos_vnext_selector_v4_packet_hash: str | None = None
    gtos_vnext_scheduler_v4_packet: dict | None = None
    gtos_vnext_scheduler_v4_packet_hash: str | None = None
    gtos_vnext_scheduler_v4_current_candidate_id: str | None = None
    gtos_vnext_scheduler_v4_selected_candidate_id: str | None = None
    gtos_vnext_scheduler_v4_selected_candidate_ids: list[str] | None = None
    gtos_vnext_scheduler_v4_selected_action_class: str | None = None
    gtos_vnext_same_symbol_lifecycle_v4_packet: dict | None = None
    gtos_vnext_same_symbol_lifecycle_action: str | None = None
    gtos_vnext_same_symbol_lifecycle_reason: str | None = None
    gtos_vnext_pretrade_cost_model: dict | None = None
    gtos_vnext_execution_policy_id: str | None = None
    gtos_vnext_dynamic_policy_selected: str | None = None
    gtos_vnext_dynamic_policy_applied: bool | None = None
    gtos_vnext_dynamic_policy_replaced_policy: str | None = None
    gtos_vnext_dynamic_policy_candidate_action: str | None = None
    gtos_vnext_dynamic_policy_decision_status: str | None = None
    gtos_vnext_dynamic_policy_source_quality_action: str | None = None
    gtos_vnext_dynamic_policy_exit_management_action: str | None = None
    gtos_vnext_dynamic_policy_prop_action: str | None = None
    gtos_vnext_dynamic_policy_fixed_target_role: str | None = None
    gtos_vnext_target_stop_geometry_v4: dict | None = None
    gtos_vnext_selected_cell_risk_pct: float | None = None
    gtos_vnext_selected_cell_risk_cell_id: str | None = None
    gtos_vnext_selected_cell_risk_status: str | None = None
    gtos_vnext_selected_cell_risk_decision_basis: str | None = None
    gtos_vnext_selected_cell_risk_unresolved_reasons: list[str] | None = None
    gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons: list[str] | None = None
    gtos_vnext_selected_cell_risk_selected_policy: str | None = None
    gtos_vnext_selected_cell_risk_source_policy: str | None = None
    gtos_vnext_selected_cell_risk_policy_identity_status: str | None = None
    gtos_vnext_commission_model_status: str | None = None
    gtos_vnext_cost_model_source: str | None = None
    gtos_vnext_production_execution_path: bool | None = None
    gtos_vnext_dynamic_be_trigger_r: float | None = None
    gtos_vnext_dynamic_final_target_r: float | None = None
    gtos_vnext_dynamic_broker_take_profit_mode: str | None = None
    gtos_vnext_dynamic_no_broker_take_profit: bool | None = None
    gtos_vnext_dynamic_be_trigger_price: float | None = None
    gtos_vnext_dynamic_final_target_price: float | None = None
    gtos_vnext_dynamic_trail_gap_r: float | None = None
    gtos_vnext_dynamic_momentum_pullback_r: float | None = None
    gtos_vnext_dynamic_time_stop_bars: int | None = None
    gtos_vnext_execution_manager_v4_status: str | None = None
    gtos_vnext_execution_manager_v4_action: str | None = None
    gtos_vnext_execution_manager_v4_fatal_reasons: list[str] | None = None
    gtos_vnext_execution_manager_v4_warning_reasons: list[str] | None = None
    gtos_vnext_execution_manager_v4_packet: dict | None = None
    gtos_vnext_book_native_exit_management: bool | None = None
    gtos_vnext_profit_harvest_mfe_capture_v4_enabled: bool | None = None
    gtos_vnext_profit_harvest_min_mfe_r: float | None = None
    gtos_vnext_profit_harvest_trail_gap_r: float | None = None
    gtos_vnext_profit_harvest_protect_floor_r: float | None = None
    gtos_vnext_profit_harvest_close_on_giveback_r: float | None = None
    gtos_vnext_profit_harvest_stale_minutes: int | None = None
    gtos_vnext_profit_harvest_stale_min_mfe_r: float | None = None
    gtos_vnext_profit_harvest_stale_close_below_r: float | None = None
    gtos_vnext_source_event_hash: str | None = None
    gtos_vnext_source_event_details: dict | None = None
    gtos_vnext_activation_family: str | None = None
    gtos_vnext_origin_family: str | None = None
    gtos_vnext_selector_row_id: str | None = None
    gtos_vnext_selector_proof_hash: str | None = None
    pending_order_mode: str = INTERNAL_PENDING_ORDER_MODE
    broker_pending_order_created: bool = False
    mt5_order_ticket: int | None = None
    native_pending_order_type: str | None = None
    pending_lifecycle_v4_id: str | None = None
    risk_reserved_pct: float | None = None
    risk_reserved_cash: float | None = None
    risk_reservation_status: str | None = None
    risk_reservation_scope: str | None = None
    risk_reservation_source: str | None = None
    risk_reservation_broker_namespace: str | None = None
    schema_version: int = 1


class ExecutionEngine:
    """Manages all MT5 order operations."""

    def __init__(self, mt5: MT5Interface, config: dict):
        self.mt5 = mt5
        self.config = config
        # mt5_symbol is the broker's name (e.g. "US30.cash"); falls back to
        # the config symbol when no mapping is needed.
        self.symbol = config.get("market", {}).get("mt5_symbol",
                          config.get("market", {}).get("symbol", "XAUUSD"))
        # Clean symbol key (e.g. "US30_cash") used for persistence filenames
        # so broker dot-notation (e.g. "US30.cash") doesn't leak into paths.
        self._persist_symbol = config.get("market", {}).get("symbol", self.symbol)
        self._runtime_namespace = broker_account_namespace(config)
        self._pending_intent_path = str(
            namespaced_file_path(
                Path(PENDING_INTENT_DIR) / f"pending_intent_{self._persist_symbol}.pkl",
                self._runtime_namespace,
            )
        )
        self._checkpoint_path = str(
            namespaced_file_path(CHECKPOINT_PATH, self._runtime_namespace)
        )
        self.active_trade: Optional[TradeState] = None
        # BUG #31 dedup set: tracks trade_ids whose close notification has
        # already been fired by this engine. Prevents duplicate Telegram
        # notifications when the orchestrator's exit-detection path also
        # fires notify_trade_closed for the same trade.
        self._notified_close_trade_ids: set[str] = set()
        # Backing field for the pending_intent property.  Assignments to
        # self.pending_intent are routed through the setter below so that
        # every change is persisted to disk (see _save_pending_intent).
        self._pending_intent: Optional[PendingLimitIntent] = None
        self._pending_account_balance: float = 0.0
        self._known_tickets: set[int] = set()
        self._last_sltp_modify_diagnostic: Optional[dict] = None
        self._last_order_send_diagnostic: Optional[dict] = None
        self._last_lot_sizing_diagnostic: Optional[dict] = None
        self._last_runtime_halt_diagnostic: Optional[dict] = None

        # Restore any persisted pending limit from a previous process.
        # Called at the END of __init__ so _pending_intent_path is set.
        self._load_pending_intent()

    def _runtime_halt_context(
        self,
        action: str,
        extra: dict | None = None,
    ) -> dict:
        context = {
            "component": "execution",
            "action": action,
            "symbol": self.symbol,
            "persist_symbol": self._persist_symbol,
            "runtime_namespace": self._runtime_namespace,
        }
        if extra:
            context.update(extra)
        return context

    def _enforce_runtime_halt_clear(
        self,
        action: str,
        extra: dict | None = None,
    ):
        return enforce_runtime_not_halted(
            action=action,
            config=self.config,
            context=self._runtime_halt_context(action, extra),
        )

    def _runtime_halt_snapshot(self, action: str, extra: dict | None = None):
        return enforce_runtime_not_halted(
            action=action,
            config=self.config,
            context=self._runtime_halt_context(action, extra),
            audit=False,
        )

    def _request_reduces_existing_position(self, request: dict) -> bool:
        try:
            action = int(request.get("action", 0) or 0)
            ticket = int(request.get("position", 0) or 0)
            request_type = int(request.get("type", -1))
            volume = float(request.get("volume", 0.0) or 0.0)
        except (TypeError, ValueError):
            return False
        if action != TRADE_ACTION_DEAL or ticket <= 0 or volume <= 0:
            return False
        try:
            positions = self.mt5.get_positions(request.get("symbol") or self.symbol) or []
        except Exception:
            return False
        for position in positions:
            try:
                if int(getattr(position, "ticket", 0) or 0) != ticket:
                    continue
                pos_type = int(getattr(position, "type", -1))
                pos_volume = float(getattr(position, "volume", 0.0) or 0.0)
            except (TypeError, ValueError):
                return False
            if volume - pos_volume > 1e-9:
                return False
            if pos_type == 0:
                return request_type == 1
            if pos_type == 1:
                return request_type == 0
            return False
        return False

    @staticmethod
    def _sl_modify_reduces_or_preserves_risk(position, new_sl: float) -> bool:
        try:
            desired = float(new_sl or 0.0)
            current = float(getattr(position, "sl", 0.0) or 0.0)
            if desired <= 0:
                return False
            if current <= 0:
                return True
            pos_type = int(getattr(position, "type", 0) or 0)
            if pos_type == 0:
                return desired >= current
            return desired <= current
        except Exception:
            return False

    def _record_runtime_halt_diagnostic(
        self,
        *,
        action: str,
        exc: RuntimeHaltError,
        extra: dict | None = None,
    ) -> dict:
        diagnostic = {
            "diagnostic_version": "runtime_control_atomic_halt_diagnostic_v1",
            "time": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "symbol": self.symbol,
            "runtime_namespace": self._runtime_namespace,
            "status": "runtime_halt_blocked_before_broker_interaction",
            "context": self._runtime_halt_context(action, extra),
            "snapshot": exc.snapshot.to_dict(),
            "positions_after": "not_read_due_to_runtime_halt_guard",
            "symbol_info": "not_read_due_to_runtime_halt_guard",
            "tick": "not_read_due_to_runtime_halt_guard",
            "broker_runtime_change_status": False,
            "forbidden_surface_status": (
                "no_broker_account_order_deal_position_mutation_performed"
            ),
        }
        self._last_runtime_halt_diagnostic = diagnostic
        return diagnostic

    @staticmethod
    def _runtime_halt_order_result(request: dict) -> OrderResult:
        try:
            volume = float(request.get("volume", 0.0) or 0.0)
        except (TypeError, ValueError):
            volume = 0.0
        try:
            price = float(request.get("price", 0.0) or 0.0)
        except (TypeError, ValueError):
            price = 0.0
        return OrderResult(
            retcode=10027,
            order=0,
            volume=volume,
            price=price,
            comment="runtime_halt_active_no_order_send",
        )

    @staticmethod
    def _runtime_lifecycle_json_safe(value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, datetime):
            dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        if isinstance(value, dict):
            return {
                str(k): ExecutionEngine._runtime_lifecycle_json_safe(v)
                for k, v in value.items()
            }
        if isinstance(value, (list, tuple, set)):
            return [ExecutionEngine._runtime_lifecycle_json_safe(v) for v in value]
        return str(value)

    @staticmethod
    def _runtime_lifecycle_packet_hash(packet: dict[str, Any]) -> str:
        material = {
            key: value
            for key, value in packet.items()
            if key not in {"generated_at_utc", "packet_hash_sha256", "packet_hash"}
        }
        raw = json.dumps(
            ExecutionEngine._runtime_lifecycle_json_safe(material),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def _record_broker_runtime_lifecycle_event(
        self,
        *,
        stage: str,
        request: dict | None = None,
        result: Any | None = None,
        trade: TradeState | None = None,
        extra: dict | None = None,
    ) -> None:
        try:
            request_map = dict(request or {})
            extra_map = dict(extra or {})
            ticket = (
                self._positive_int_or_none(getattr(trade, "ticket", None))
                or self._positive_int_or_none(request_map.get("position"))
                or self._positive_int_or_none(extra_map.get("ticket"))
            )
            identity_trade = trade
            active_trade = getattr(self, "active_trade", None)
            if (
                identity_trade is None
                and active_trade is not None
                and (
                    ticket is None
                    or self._positive_int_or_none(getattr(active_trade, "ticket", None)) == ticket
                )
            ):
                identity_trade = active_trade
            trade_id = getattr(identity_trade, "trade_id", None) or extra_map.get("trade_id")
            direction = getattr(identity_trade, "direction", None) or extra_map.get("direction")
            source_hash = (
                extra_map.get("source_hash")
                or extra_map.get("gtos_vnext_source_event_hash")
                or getattr(identity_trade, "gtos_vnext_source_event_hash", None)
            )
            source_event_details = (
                extra_map.get("gtos_vnext_source_event_details")
                or getattr(identity_trade, "gtos_vnext_source_event_details", None)
            )
            packet = {
                "schema_version": "broker_order_lifecycle_capture_v4_runtime_event_v1",
                "component": "broker_order_lifecycle_capture_v4",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "stage": stage,
                "symbol": self.symbol,
                "persist_symbol": self._persist_symbol,
                "runtime_namespace": self._runtime_namespace,
                "ticket": ticket,
                "trade_id": trade_id,
                "direction": direction,
                "source_hash": source_hash,
                "source_hash_status": (
                    "source_hash_attached_to_runtime_event"
                    if source_hash
                    else "source_hash_unavailable_for_runtime_event"
                ),
                "source_event_details_present": isinstance(source_event_details, dict)
                and bool(source_event_details),
                "request": request_map,
                "result": self._result_snapshot(result),
                "extra": extra_map,
                "broker_runtime_change_status": False,
                "broker_runtime_change_status_semantics": (
                    "capture_row_is_observation_only; broker_operation_observed fields "
                    "describe any real MT5 request/result that already occurred"
                ),
                "broker_operation_observed": (
                    bool(extra_map["broker_operation_observed"])
                    if "broker_operation_observed" in extra_map
                    else bool(request_map or result is not None)
                ),
                "broker_operation_stage": stage,
                "broker_operation_source_status": extra_map.get(
                    "broker_operation_source_status",
                    "observed_from_runtime_request_result",
                ),
                "source_boundary": "runtime_observed_broker_request_result_no_replay_inference",
            }
            packet["packet_hash_sha256"] = self._runtime_lifecycle_packet_hash(packet)
            packet["packet_hash"] = packet["packet_hash_sha256"]
            record_broker_order_lifecycle_capture_v4(packet, config=self.config)
        except Exception:
            logger.debug("broker runtime lifecycle event logging failed", exc_info=True)

    @staticmethod
    def _source_value(source, key: str, default=None):
        if isinstance(source, dict):
            return source.get(key, default)
        return getattr(source, key, default)

    def _notify_vnext_lifecycle(
        self,
        source,
        lifecycle_event: str,
        *,
        trade_id: str | None = None,
        direction: str | None = None,
        price: float | None = None,
        result_r: float | None = None,
        detail: str | None = None,
    ) -> None:
        try:
            from src.notifications import (
                build_vnext_notification_context,
                notify_vnext_lifecycle_event,
            )
            context = build_vnext_notification_context(
                source,
                lifecycle_event=lifecycle_event,
            )
            if not context:
                return
            notify_vnext_lifecycle_event(
                symbol=self.symbol,
                lifecycle_event=lifecycle_event,
                trade_id=(
                    trade_id
                    if trade_id is not None
                    else str(self._source_value(source, "trade_id", "") or "")
                ),
                direction=(
                    direction
                    if direction is not None
                    else self._source_value(source, "direction", None)
                ),
                price=price,
                result_r=result_r,
                detail=detail,
                vnext_context=context,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "vNext lifecycle notification failed (non-blocking): %s",
                exc,
            )

    # === PENDING INTENT PERSISTENCE ===
    # pending_intent is stored in-memory only AND persisted to disk so that
    # process restarts (watchdog kills, crashes) do not destroy an active
    # limit order that is about to fill.  See handoff 18 for the Apr 16
    # incident where a crash during sleep destroyed a live London limit.

    @property
    def pending_intent(self) -> Optional[PendingLimitIntent]:
        return self._pending_intent

    @pending_intent.setter
    def pending_intent(self, value: Optional[PendingLimitIntent]) -> None:
        """Setter that also persists the new state to disk.

        Clearing (setting to None) deletes the pkl file so a stale file
        never lingers between sessions.
        """
        self._pending_intent = value
        if value is None:
            self._clear_pending_intent_file()
        else:
            self._save_pending_intent()

    def _save_pending_intent(self) -> None:
        """Atomically write the current pending_intent to its pkl file.

        Uses a per-pid .tmp file + os.replace to avoid leaving a partial
        file on crash.  Silently returns if no intent to persist.
        """
        if self._pending_intent is None:
            return
        path = Path(self._pending_intent_path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = path.with_suffix(f".{os.getpid()}.tmp")
            with open(tmp_path, "wb") as f:
                pickle.dump(self._pending_intent, f, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp_path, path)
        except Exception as e:
            logger.warning("Failed to persist pending_intent: %s", e)
            # Best effort cleanup of tmp
            try:
                tmp_path.unlink(missing_ok=True)  # type: ignore[name-defined]
            except Exception:
                pass

    def _clear_pending_intent_file(self) -> None:
        """Remove the persisted pending_intent file, if present."""
        path = Path(self._pending_intent_path)
        try:
            if path.exists():
                path.unlink()
        except Exception as e:
            logger.warning("Failed to delete pending_intent file: %s", e)

    def _load_pending_intent(self) -> None:
        """Restore pending_intent from disk at startup.

        Rules (per handoff 18 contract, handoff 19 additions marked):
        - File missing       -> start with None, no log spam.
        - Corrupt file       -> log WARNING, delete file, start with None.
        - Intent > 24h old   -> discard, delete file, log what was dropped.
        - Intent placed on a previous UTC day before today's first KZ
                            -> discard, delete file, log what was dropped.
        - Orphan *.pid.tmp   -> unlink at startup (handoff 19). A crash mid-save
                                leaves a half-written tmp file; we sweep these up
                                so the directory does not grow unbounded and the
                                atomic_write_no_partial_file test invariant holds
                                across restarts.
        - schema_version != 1-> discard, delete file (handoff 19). Protects
                                against reading a pickle written by a prior
                                code revision whose layout changed.
        """
        # Sweep orphan .{pid}.tmp files first so a crashed save doesn't
        # leave debris that confuses downstream readers or test assertions.
        meta_dir = Path(PENDING_INTENT_DIR)
        try:
            orphan_tmps = list(meta_dir.glob("pending_intent_*.*.tmp"))
            if orphan_tmps:
                cleaned = 0
                for tmp in orphan_tmps:
                    try:
                        tmp.unlink()
                        cleaned += 1
                    except Exception as e:
                        logger.warning(
                            "Failed to unlink orphan pending_intent tmp %s: %s",
                            tmp, e,
                        )
                if cleaned > 0:
                    logger.info(
                        "Cleaned %d orphan pending_intent tmp file(s) at startup",
                        cleaned,
                    )
        except Exception as e:
            logger.warning(
                "Orphan pending_intent .tmp sweep failed (non-blocking): %s", e,
            )

        path = Path(self._pending_intent_path)
        if not path.exists():
            return

        try:
            with open(path, "rb") as f:
                intent = pickle.load(f)
        except Exception as e:
            logger.warning(
                "Corrupt pending_intent file %s (%s) -- discarding",
                path, e,
            )
            self._clear_pending_intent_file()
            return

        if not isinstance(intent, PendingLimitIntent):
            logger.warning(
                "pending_intent file contains unexpected type %s -- discarding",
                type(intent).__name__,
            )
            self._clear_pending_intent_file()
            return

        # Schema version check — discard any pickle from an incompatible layout.
        loaded_version = getattr(intent, "schema_version", None)
        if loaded_version != 1:
            logger.warning(
                "pending_intent schema version mismatch: loaded=%s, expected=1. "
                "Discarding.",
                loaded_version,
            )
            self._clear_pending_intent_file()
            return

        # Additive telemetry fields share schema_version=1 so valid active
        # intents written by the previous code can survive restart. Fill
        # missing attributes in memory instead of discarding the limit.
        for attr in (
            "candidate_id",
            "decision_time_utc",
            "source_file",
            "source_hash",
            "source_symbol",
            "session",
            "kill_zone",
            "regime",
            "pending_order_mode",
            "broker_pending_order_created",
            "mt5_order_ticket",
            "native_pending_order_type",
            "pending_lifecycle_v4_id",
            "risk_reserved_pct",
            "risk_reserved_cash",
            "risk_reservation_status",
            "risk_reservation_scope",
            "risk_reservation_source",
            "risk_reservation_broker_namespace",
            "gtos_vnext_pre_ai_action",
            "gtos_vnext_pre_ai_recommended_side",
            "gtos_vnext_pre_ai_recommended_frameworks",
            "gtos_vnext_decision",
            "gtos_vnext_reason",
            "gtos_vnext_matched",
            "gtos_vnext_matched_rows",
            "gtos_vnext_cost_adjusted_r_sum",
            "gtos_vnext_proxy_score_sum",
            "gtos_vnext_stress_r_sum",
            "gtos_vnext_effective_n_sum",
            "gtos_vnext_risk_multiplier",
            "gtos_vnext_risk_would_multiplier",
            "gtos_vnext_risk_reason",
            "gtos_vnext_pending_policy_action",
            "gtos_vnext_pending_policy_would_action",
            "gtos_vnext_pending_policy_applied",
            "gtos_vnext_pending_policy_reason",
            "gtos_vnext_ltf_path_action",
            "gtos_vnext_ltf_path_would_action",
            "gtos_vnext_ltf_path_applied",
            "gtos_vnext_ltf_path_reason",
            "gtos_vnext_ltf_path_monitor_timeframe",
            "gtos_vnext_ltf_path_adjusted_entry_price",
            "gtos_vnext_prop_safe_selector_action",
            "gtos_vnext_prop_safe_selector_would_action",
            "gtos_vnext_prop_safe_selector_applied",
            "gtos_vnext_prop_safe_selector_after_risk_pct",
            "gtos_vnext_prop_safe_selector_reason",
            "gtos_vnext_prop_firm_headroom_snapshot_v4",
            "gtos_vnext_prop_firm_headroom_v4_packet",
            "gtos_vnext_execution_policy_id",
            "gtos_vnext_dynamic_policy_selected",
            "gtos_vnext_dynamic_policy_applied",
            "gtos_vnext_dynamic_policy_replaced_policy",
            "gtos_vnext_dynamic_policy_candidate_action",
            "gtos_vnext_dynamic_policy_decision_status",
            "gtos_vnext_dynamic_policy_source_quality_action",
            "gtos_vnext_dynamic_policy_exit_management_action",
            "gtos_vnext_dynamic_policy_prop_action",
            "gtos_vnext_dynamic_policy_fixed_target_role",
            "gtos_vnext_target_stop_geometry_v4",
            "gtos_vnext_selected_cell_risk_pct",
            "gtos_vnext_selected_cell_risk_cell_id",
            "gtos_vnext_selected_cell_risk_decision_basis",
            "gtos_vnext_selected_cell_risk_unresolved_reasons",
            "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons",
            "gtos_vnext_selected_cell_risk_selected_policy",
            "gtos_vnext_selected_cell_risk_source_policy",
            "gtos_vnext_selected_cell_risk_policy_identity_status",
            "gtos_vnext_commission_model_status",
            "gtos_vnext_cost_model_source",
            "gtos_vnext_production_execution_path",
            "gtos_vnext_dynamic_be_trigger_r",
            "gtos_vnext_dynamic_final_target_r",
            "gtos_vnext_dynamic_broker_take_profit_mode",
            "gtos_vnext_dynamic_no_broker_take_profit",
            "gtos_vnext_dynamic_be_trigger_price",
            "gtos_vnext_dynamic_final_target_price",
            "gtos_vnext_dynamic_trail_gap_r",
            "gtos_vnext_dynamic_momentum_pullback_r",
            "gtos_vnext_dynamic_time_stop_bars",
            "gtos_vnext_book_native_exit_management",
            "gtos_vnext_execution_manager_v4_status",
            "gtos_vnext_execution_manager_v4_action",
            "gtos_vnext_execution_manager_v4_fatal_reasons",
            "gtos_vnext_execution_manager_v4_warning_reasons",
            "gtos_vnext_execution_manager_v4_packet",
            "gtos_vnext_source_event_hash",
            "gtos_vnext_source_event_details",
            "gtos_vnext_activation_family",
            "gtos_vnext_origin_family",
            "gtos_vnext_selector_row_id",
            "gtos_vnext_selector_proof_hash",
        ):
            if not hasattr(intent, attr):
                if attr == "pending_order_mode":
                    setattr(intent, attr, INTERNAL_PENDING_ORDER_MODE)
                elif attr == "broker_pending_order_created":
                    setattr(intent, attr, False)
                elif attr == "risk_reservation_scope":
                    setattr(intent, attr, "broker_local_pending_intent")
                elif attr == "risk_reservation_source":
                    setattr(
                        intent,
                        attr,
                        "account_balance_x_risk_pct_at_pending_creation",
                    )
                elif attr == "risk_reservation_broker_namespace":
                    setattr(intent, attr, self._runtime_namespace)
                else:
                    setattr(intent, attr, None)

        # Staleness check 1: hard 24-hour cap
        try:
            placed_dt = datetime.fromisoformat(intent.placed_time)
            if placed_dt.tzinfo is None:
                placed_dt = placed_dt.replace(tzinfo=timezone.utc)
        except Exception as e:
            logger.warning(
                "pending_intent has unparseable placed_time=%r (%s) -- discarding",
                getattr(intent, "placed_time", None), e,
            )
            self._clear_pending_intent_file()
            return

        now = datetime.now(timezone.utc)
        age_hours = (now - placed_dt).total_seconds() / 3600.0
        if age_hours >= PENDING_INTENT_MAX_AGE_HOURS:
            logger.info(
                "Discarding stale pending_intent (age=%.1fh >= %dh): %s "
                "%s limit=%.5f sl=%.5f placed=%s",
                age_hours, PENDING_INTENT_MAX_AGE_HOURS,
                intent.trade_id, intent.direction, intent.limit_price,
                intent.stop_loss, intent.placed_time,
            )
            self._clear_pending_intent_file()
            return

        # Staleness check 2: placed on a previous UTC day AND before the
        # earliest KZ that has already started today. The intent is "from
        # yesterday" only if its UTC date is strictly before today's — a
        # same-UTC-day placement that happens to precede first KZ start
        # (e.g. placed at 04:00 UTC when first KZ is 07:00 UTC, and the
        # process restarts at 05:00 UTC) is still fresh.
        first_kz_start = self._first_kz_start_today(now)
        if (
            first_kz_start is not None
            and placed_dt < first_kz_start
            and placed_dt.date() < now.date()
        ):
            logger.info(
                "Discarding pending_intent placed on a previous UTC day "
                "(placed=%s, first_kz_start=%s): %s %s limit=%.5f",
                intent.placed_time, first_kz_start.isoformat(),
                intent.trade_id, intent.direction, intent.limit_price,
            )
            self._clear_pending_intent_file()
            return

        self._pending_intent = intent
        self._pending_account_balance = float(getattr(intent, "account_balance", 0.0) or 0.0)
        logger.info(
            "Restored pending_intent from disk: %s %s limit=%.5f sl=%.5f "
            "tp=%.5f placed=%s (age=%.1fh, balance=%.2f)",
            intent.trade_id, intent.direction, intent.limit_price,
            intent.stop_loss, intent.take_profit_1, intent.placed_time,
            age_hours, self._pending_account_balance,
        )

    def _first_kz_start_today(self, now: datetime) -> Optional[datetime]:
        """Return UTC datetime of today's earliest kill-zone start.

        Reads config.market.kill_zones.  Returns None if no KZs are
        configured or on parse error (staleness check is then skipped).
        Midnight-crossing KZs are ignored for this purpose because their
        "start" falls on the previous calendar day.
        """
        kz_cfg = self.config.get("market", {}).get("kill_zones", {})
        if not kz_cfg:
            return None
        earliest_min: Optional[int] = None
        for kz_data in kz_cfg.values():
            start = kz_data.get("start_utc", "")
            end = kz_data.get("end_utc", "")
            try:
                sh, sm = [int(x) for x in start.split(":")]
                eh, em = [int(x) for x in end.split(":")]
            except Exception:
                continue
            start_min = sh * 60 + sm
            end_min = eh * 60 + em
            if end_min <= start_min:
                # Midnight-crossing KZ -- its "start" is yesterday.
                continue
            if earliest_min is None or start_min < earliest_min:
                earliest_min = start_min
        if earliest_min is None:
            return None
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return today + timedelta(minutes=earliest_min)

    @staticmethod
    def _context_value(telemetry_context: dict, trade_params: dict, key: str):
        if key in telemetry_context:
            return telemetry_context.get(key)
        return trade_params.get(key)

    def _evaluate_execution_manager_v4(
        self,
        *,
        trade_params: dict,
        pretrade_cost_model: dict | None = None,
        pending_context: dict | None = None,
        trigger: str | None = None,
    ):
        decision = evaluate_execution_manager_v4(
            config=self.config,
            trade_params=trade_params,
            symbol=self._persist_symbol,
            broker_symbol=self.symbol,
            pretrade_cost_model=pretrade_cost_model,
            pending=pending_context,
            trigger=trigger,
        )
        packet = decision.packet
        trade_params["gtos_vnext_execution_manager_v4_status"] = (
            packet.get("config", {}).get("runtime_status")
        )
        trade_params["gtos_vnext_execution_manager_v4_action"] = decision.action
        trade_params["gtos_vnext_execution_manager_v4_fatal_reasons"] = list(
            decision.fatal_reasons
        )
        trade_params["gtos_vnext_execution_manager_v4_warning_reasons"] = list(
            decision.warning_reasons
        )
        trade_params["gtos_vnext_execution_manager_v4_packet"] = packet
        headroom_contract = packet.get("prop_firm_headroom_contract")
        if isinstance(headroom_contract, dict):
            headroom_packet = headroom_contract.get("packet")
            if isinstance(headroom_packet, dict):
                snapshot = headroom_packet.get("snapshot")
                if isinstance(snapshot, dict) and snapshot:
                    trade_params["gtos_vnext_prop_firm_headroom_snapshot_v4"] = snapshot
                trade_params["gtos_vnext_prop_firm_headroom_v4_packet"] = headroom_packet
        try:
            record_execution_manager_v4_decision(packet, config=self.config)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Execution Manager V4 packet logging failed (non-blocking): %s",
                exc,
            )
        return decision

    @staticmethod
    def _execution_manager_v4_block_reason(
        decision,
        *,
        pretrade_cost_model: dict | None = None,
        pretrade_cost_error: str | None = None,
    ) -> str:
        fatal = list(getattr(decision, "fatal_reasons", ()) or ())
        exec_reason = "exec_mgr_v4:" + ",".join(fatal)
        cost_reason = pretrade_cost_error
        if not cost_reason and isinstance(pretrade_cost_model, dict):
            cost_reason = pretrade_cost_refusal_reason(pretrade_cost_model)
        if cost_reason and any(
            str(reason).startswith("missing_cost:")
            or str(reason).startswith("pretrade_cost_model_status_not_passed:")
            for reason in fatal
        ):
            return f"pretrade_cost:{cost_reason};{exec_reason}"
        return exec_reason

    @staticmethod
    def _apply_execution_manager_v4_to_intent(
        intent: PendingLimitIntent,
        decision,
    ) -> None:
        packet = decision.packet
        intent.gtos_vnext_execution_manager_v4_status = (
            packet.get("config", {}).get("runtime_status")
        )
        intent.gtos_vnext_execution_manager_v4_action = decision.action
        intent.gtos_vnext_execution_manager_v4_fatal_reasons = list(
            decision.fatal_reasons
        )
        intent.gtos_vnext_execution_manager_v4_warning_reasons = list(
            decision.warning_reasons
        )
        intent.gtos_vnext_execution_manager_v4_packet = packet
        headroom_contract = packet.get("prop_firm_headroom_contract")
        if isinstance(headroom_contract, dict):
            headroom_packet = headroom_contract.get("packet")
            if isinstance(headroom_packet, dict):
                snapshot = headroom_packet.get("snapshot")
                if isinstance(snapshot, dict) and snapshot:
                    intent.gtos_vnext_prop_firm_headroom_snapshot_v4 = snapshot
                intent.gtos_vnext_prop_firm_headroom_v4_packet = headroom_packet

    def _configured_vnext_be_after_trigger_params(self) -> dict:
        """Resolve placement-time defaults for the supported vNext BE policy."""
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}

        def _float_cfg(key: str, default: float) -> float:
            raw = cfg.get(key, default)
            try:
                return float(raw if raw not in (None, "") else default)
            except (TypeError, ValueError):
                logger.error("Invalid %s=%r; using default %.2f", key, raw, default)
                return default

        raw_time_stop = cfg.get("moonshot_dynamic_execution_router_be_time_stop_bars")
        try:
            time_stop_bars = (
                None if raw_time_stop in (None, "") else int(raw_time_stop)
            )
        except (TypeError, ValueError):
            logger.error(
                "Invalid moonshot_dynamic_execution_router_be_time_stop_bars=%r; "
                "using no time stop",
                raw_time_stop,
            )
            time_stop_bars = None

        return {
            "trigger_r": _float_cfg(
                "moonshot_dynamic_execution_router_be_trigger_r",
                1.0,
            ),
            "final_target_r": _float_cfg(
                "moonshot_dynamic_execution_router_be_final_target_r",
                1.5,
            ),
            "time_stop_bars": time_stop_bars,
        }

    def _configured_vnext_partial_be_runner_params(self) -> dict:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        return {
            "trigger_r": float(
                cfg.get("moonshot_dynamic_execution_router_partial_trigger_r", 1.0)
                or 1.0
            ),
            "final_target_r": float(
                cfg.get("moonshot_dynamic_execution_router_partial_final_target_r", 3.0)
                or 3.0
            ),
            "partial_close_ratio": float(
                cfg.get("moonshot_dynamic_execution_router_partial_close_ratio", 0.5)
                or 0.5
            ),
            "time_stop_bars": cfg.get(
                "moonshot_dynamic_execution_router_partial_time_stop_bars"
            ),
        }

    def _configured_vnext_trailing_runner_params(self) -> dict:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        return {
            "trigger_r": float(
                cfg.get("moonshot_dynamic_execution_router_trailing_trigger_r", 1.0)
                or 1.0
            ),
            "final_target_r": float(
                cfg.get("moonshot_dynamic_execution_router_trailing_final_target_r", 3.0)
                or 3.0
            ),
            "trail_gap_r": float(
                cfg.get("moonshot_dynamic_execution_router_trailing_gap_r", 0.5)
                or 0.5
            ),
            "time_stop_bars": cfg.get(
                "moonshot_dynamic_execution_router_trailing_time_stop_bars"
            ),
        }

    def _configured_vnext_momentum_exhaustion_params(self) -> dict:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        return {
            "trigger_r": float(
                cfg.get("moonshot_dynamic_execution_router_momentum_trigger_r", 1.0)
                or 1.0
            ),
            "final_target_r": float(
                cfg.get("moonshot_dynamic_execution_router_momentum_final_target_r", 2.0)
                or 2.0
            ),
            "pullback_r": float(
                cfg.get("moonshot_dynamic_execution_router_momentum_pullback_r", 0.4)
                or 0.4
            ),
            "time_stop_bars": cfg.get(
                "moonshot_dynamic_execution_router_momentum_time_stop_bars"
            ),
        }

    def _configured_vnext_time_stop_params(self) -> dict:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        raw_bars = cfg.get("moonshot_dynamic_execution_router_time_stop_bars", 32)
        raw_target = cfg.get("moonshot_dynamic_execution_router_time_stop_target_r", 1.5)
        try:
            bars = int(raw_bars)
        except (TypeError, ValueError):
            bars = 32
        try:
            target_r = float(raw_target)
        except (TypeError, ValueError):
            target_r = 1.5
        return {"time_stop_bars": max(1, bars), "final_target_r": max(0.1, target_r)}

    def _configured_vnext_profit_harvest_mfe_capture_v4_params(self) -> dict:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}

        def _bool_cfg(key: str, default: bool) -> bool:
            raw = cfg.get(key, default)
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return bool(raw)

        def _float_cfg(key: str, default: float) -> float:
            raw = cfg.get(key, default)
            try:
                return float(raw if raw not in (None, "") else default)
            except (TypeError, ValueError):
                logger.error("Invalid %s=%r; using default %.3f", key, raw, default)
                return float(default)

        def _optional_int_cfg(key: str) -> Optional[int]:
            raw = cfg.get(key)
            if raw in (None, ""):
                return None
            try:
                value = int(raw)
            except (TypeError, ValueError):
                logger.error("Invalid %s=%r; using no stale-thesis timer", key, raw)
                return None
            return value if value > 0 else None

        return {
            "enabled": _bool_cfg(
                "profit_harvest_mfe_capture_v4_enabled",
                False,
            ),
            "require_vnext_dynamic_policy": _bool_cfg(
                "profit_harvest_mfe_capture_v4_require_vnext_dynamic_policy",
                True,
            ),
            "min_mfe_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_min_mfe_r",
                0.25,
            ),
            "trail_gap_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_trail_gap_r",
                0.35,
            ),
            "protect_floor_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_protect_floor_r",
                0.0,
            ),
            "close_on_giveback_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_close_on_giveback_r",
                0.50,
            ),
            "stale_minutes": _optional_int_cfg(
                "profit_harvest_mfe_capture_v4_stale_minutes",
            ),
            "stale_min_mfe_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_stale_min_mfe_r",
                0.25,
            ),
            "stale_close_below_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_stale_close_below_r",
                0.0,
            ),
        }

    def _vnext_be_after_trigger_params(self, trade_params: dict) -> Optional[dict]:
        """Return live-management parameters for the repaired vNext BE policy."""
        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        if (
            not trade_params.get("gtos_vnext_dynamic_policy_applied")
            or selected_policy != "be_after_trigger"
        ):
            return None

        trigger_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_be_trigger_r")
        )
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        if trigger_r is None or trigger_r <= 0 or final_target_r is None or final_target_r <= 0:
            logger.error(
                "GTOS vNext be_after_trigger missing placement-time R params: "
                "trigger_r=%r final_target_r=%r",
                trade_params.get("gtos_vnext_dynamic_be_trigger_r"),
                trade_params.get("gtos_vnext_dynamic_final_target_r"),
            )
            return None

        raw_time_stop = trade_params.get("gtos_vnext_dynamic_time_stop_bars")
        try:
            time_stop_bars = None if raw_time_stop in (None, "") else int(raw_time_stop)
            if time_stop_bars is not None and time_stop_bars <= 0:
                raise ValueError("time_stop_bars must be positive")
        except (TypeError, ValueError):
            logger.error(
                "GTOS vNext be_after_trigger invalid placement-time time stop: %r",
                raw_time_stop,
            )
            return None
        return {
            "trigger_r": trigger_r,
            "final_target_r": final_target_r,
            "time_stop_bars": time_stop_bars,
        }

    def _vnext_partial_be_runner_params(self, trade_params: dict) -> Optional[dict]:
        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        if (
            not trade_params.get("gtos_vnext_dynamic_policy_applied")
            or selected_policy != "partial_be_runner"
        ):
            return None

        configured = self._configured_vnext_partial_be_runner_params()
        trigger_r = self._safe_float(trade_params.get("gtos_vnext_dynamic_be_trigger_r"))
        if trigger_r is None:
            trigger_r = float(configured["trigger_r"])
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        no_broker_tp = self._vnext_no_broker_take_profit(trade_params)
        if final_target_r is None and not no_broker_tp:
            final_target_r = float(configured["final_target_r"])
        elif final_target_r is None:
            final_target_r = 0.0
        close_ratio = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_partial_close_ratio")
        )
        if close_ratio is None:
            close_ratio = float(configured["partial_close_ratio"])
        raw_time_stop = trade_params.get("gtos_vnext_dynamic_time_stop_bars")
        if raw_time_stop in (None, ""):
            raw_time_stop = configured.get("time_stop_bars")
        try:
            time_stop_bars = None if raw_time_stop in (None, "") else int(raw_time_stop)
            if time_stop_bars is not None and time_stop_bars <= 0:
                raise ValueError("time_stop_bars must be positive")
        except (TypeError, ValueError):
            logger.error("GTOS vNext partial_be_runner invalid time stop: %r", raw_time_stop)
            return None
        if trigger_r <= 0 or final_target_r <= 0 or not 0 < close_ratio < 1:
            logger.error(
                "GTOS vNext partial_be_runner invalid params: trigger=%r final=%r ratio=%r",
                trigger_r,
                final_target_r,
                close_ratio,
            )
            return None
        return {
            "trigger_r": trigger_r,
            "final_target_r": final_target_r,
            "partial_close_ratio": close_ratio,
            "time_stop_bars": time_stop_bars,
        }

    def _vnext_trailing_runner_params(self, trade_params: dict) -> Optional[dict]:
        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        if (
            not trade_params.get("gtos_vnext_dynamic_policy_applied")
            or selected_policy != "trailing_runner"
        ):
            return None

        configured = self._configured_vnext_trailing_runner_params()
        trigger_r = self._safe_float(trade_params.get("gtos_vnext_dynamic_be_trigger_r"))
        if trigger_r is None:
            trigger_r = float(configured["trigger_r"])
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        no_broker_tp = self._vnext_no_broker_take_profit(trade_params)
        if final_target_r is None and not no_broker_tp:
            final_target_r = float(configured["final_target_r"])
        elif final_target_r is None:
            final_target_r = 0.0
        trail_gap_r = self._safe_float(trade_params.get("gtos_vnext_dynamic_trail_gap_r"))
        if trail_gap_r is None:
            trail_gap_r = float(configured["trail_gap_r"])
        raw_time_stop = trade_params.get("gtos_vnext_dynamic_time_stop_bars")
        if raw_time_stop in (None, ""):
            raw_time_stop = configured.get("time_stop_bars")
        try:
            time_stop_bars = None if raw_time_stop in (None, "") else int(raw_time_stop)
            if time_stop_bars is not None and time_stop_bars <= 0:
                raise ValueError("time_stop_bars must be positive")
        except (TypeError, ValueError):
            logger.error("GTOS vNext trailing_runner invalid time stop: %r", raw_time_stop)
            return None
        if trigger_r <= 0 or (final_target_r <= 0 and not no_broker_tp) or trail_gap_r <= 0:
            logger.error(
                "GTOS vNext trailing_runner invalid params: trigger=%r final=%r gap=%r",
                trigger_r,
                final_target_r,
                trail_gap_r,
            )
            return None
        return {
            "trigger_r": trigger_r,
            "final_target_r": final_target_r,
            "trail_gap_r": trail_gap_r,
            "time_stop_bars": time_stop_bars,
            "no_broker_take_profit": no_broker_tp,
        }

    def _vnext_momentum_exhaustion_params(self, trade_params: dict) -> Optional[dict]:
        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        if (
            not trade_params.get("gtos_vnext_dynamic_policy_applied")
            or selected_policy != "momentum_exhaustion"
        ):
            return None

        configured = self._configured_vnext_momentum_exhaustion_params()
        trigger_r = self._safe_float(trade_params.get("gtos_vnext_dynamic_be_trigger_r"))
        if trigger_r is None:
            trigger_r = float(configured["trigger_r"])
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        if final_target_r is None:
            final_target_r = float(configured["final_target_r"])
        pullback_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_momentum_pullback_r")
        )
        if pullback_r is None:
            pullback_r = float(configured["pullback_r"])
        raw_time_stop = trade_params.get("gtos_vnext_dynamic_time_stop_bars")
        if raw_time_stop in (None, ""):
            raw_time_stop = configured.get("time_stop_bars")
        try:
            time_stop_bars = None if raw_time_stop in (None, "") else int(raw_time_stop)
            if time_stop_bars is not None and time_stop_bars <= 0:
                raise ValueError("time_stop_bars must be positive")
        except (TypeError, ValueError):
            logger.error(
                "GTOS vNext momentum_exhaustion invalid time stop: %r", raw_time_stop
            )
            return None
        if trigger_r <= 0 or final_target_r <= 0 or pullback_r <= 0:
            logger.error(
                "GTOS vNext momentum_exhaustion invalid params: trigger=%r final=%r pullback=%r",
                trigger_r,
                final_target_r,
                pullback_r,
            )
            return None
        return {
            "trigger_r": trigger_r,
            "final_target_r": final_target_r,
            "pullback_r": pullback_r,
            "time_stop_bars": time_stop_bars,
        }

    def _vnext_time_stop_params(self, trade_params: dict) -> Optional[dict]:
        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        if (
            not trade_params.get("gtos_vnext_dynamic_policy_applied")
            or selected_policy != "time_stop"
        ):
            return None
        configured = self._configured_vnext_time_stop_params()
        raw_time_stop = trade_params.get("gtos_vnext_dynamic_time_stop_bars")
        if raw_time_stop in (None, ""):
            raw_time_stop = configured["time_stop_bars"]
        try:
            time_stop_bars = int(raw_time_stop)
            if time_stop_bars <= 0:
                raise ValueError("time_stop_bars must be positive")
        except (TypeError, ValueError):
            logger.error("GTOS vNext time_stop invalid bars: %r", raw_time_stop)
            return None
        target_r = self._safe_float(trade_params.get("gtos_vnext_dynamic_final_target_r"))
        no_broker_tp = self._vnext_no_broker_take_profit(trade_params)
        if target_r is None and not no_broker_tp:
            target_r = float(configured["final_target_r"])
        elif target_r is None:
            target_r = 0.0
        return {
            "time_stop_bars": time_stop_bars,
            "final_target_r": target_r,
            "no_broker_take_profit": no_broker_tp,
        }

    @staticmethod
    def _bool_param_enabled(value) -> bool:
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    def _vnext_profit_harvest_mfe_capture_v4_params(
        self,
        trade_params: dict,
    ) -> Optional[dict]:
        configured = self._configured_vnext_profit_harvest_mfe_capture_v4_params()
        raw_enabled = trade_params.get(
            "gtos_vnext_profit_harvest_mfe_capture_v4_enabled",
            configured["enabled"],
        )
        if isinstance(raw_enabled, str):
            enabled = raw_enabled.strip().lower() in {"1", "true", "yes", "on"}
        else:
            enabled = bool(raw_enabled)
        if not enabled:
            return None

        if configured["require_vnext_dynamic_policy"] and not trade_params.get(
            "gtos_vnext_dynamic_policy_applied"
        ):
            logger.error(
                "GTOS vNext profit harvest V4 requires ticket-bound dynamic policy state"
            )
            return None

        def _raw_param(keys: tuple[str, ...]):
            for key in keys:
                if key in trade_params and trade_params.get(key) not in (None, ""):
                    return trade_params.get(key)
            return None

        def _float_param(keys: tuple[str, ...], configured_key: str) -> Optional[float]:
            raw = _raw_param(keys)
            if raw in (None, ""):
                raw = configured[configured_key]
            return self._safe_float(raw)

        min_mfe_r = _float_param(
            (
                "gtos_vnext_profit_harvest_min_mfe_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_min_mfe_r",
            ),
            "min_mfe_r",
        )
        trail_gap_r = _float_param(
            (
                "gtos_vnext_profit_harvest_trail_gap_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_trail_gap_r",
            ),
            "trail_gap_r",
        )
        protect_floor_r = _float_param(
            (
                "gtos_vnext_profit_harvest_protect_floor_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_protect_floor_r",
            ),
            "protect_floor_r",
        )
        close_on_giveback_r = _float_param(
            (
                "gtos_vnext_profit_harvest_close_on_giveback_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_close_on_giveback_r",
            ),
            "close_on_giveback_r",
        )
        stale_min_mfe_r = _float_param(
            (
                "gtos_vnext_profit_harvest_stale_min_mfe_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_stale_min_mfe_r",
            ),
            "stale_min_mfe_r",
        )
        stale_close_below_r = _float_param(
            (
                "gtos_vnext_profit_harvest_stale_close_below_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_stale_close_below_r",
            ),
            "stale_close_below_r",
        )

        raw_stale_minutes = _raw_param(
            (
                "gtos_vnext_profit_harvest_stale_minutes",
                "gtos_vnext_profit_harvest_mfe_capture_v4_stale_minutes",
            )
        )
        if raw_stale_minutes in (None, ""):
            raw_stale_minutes = configured.get("stale_minutes")
        try:
            stale_minutes = (
                None
                if raw_stale_minutes in (None, "")
                else int(raw_stale_minutes)
            )
            if stale_minutes is not None and stale_minutes <= 0:
                raise ValueError("stale_minutes must be positive")
        except (TypeError, ValueError):
            logger.error("GTOS vNext profit harvest invalid stale minutes: %r", raw_stale_minutes)
            return None

        if (
            min_mfe_r is None
            or min_mfe_r <= 0
            or trail_gap_r is None
            or trail_gap_r <= 0
            or protect_floor_r is None
            or protect_floor_r < 0
            or close_on_giveback_r is None
            or close_on_giveback_r <= 0
            or stale_min_mfe_r is None
            or stale_min_mfe_r <= 0
            or stale_close_below_r is None
        ):
            logger.error(
                "GTOS vNext profit harvest invalid params: min_mfe=%r gap=%r "
                "floor=%r giveback=%r stale_min=%r stale_close_below=%r",
                min_mfe_r,
                trail_gap_r,
                protect_floor_r,
                close_on_giveback_r,
                stale_min_mfe_r,
                stale_close_below_r,
            )
            return None

        return {
            "enabled": True,
            "min_mfe_r": min_mfe_r,
            "trail_gap_r": trail_gap_r,
            "protect_floor_r": protect_floor_r,
            "close_on_giveback_r": close_on_giveback_r,
            "stale_minutes": stale_minutes,
            "stale_min_mfe_r": stale_min_mfe_r,
            "stale_close_below_r": stale_close_below_r,
        }

    def _vnext_dynamic_policy_support_error(self, trade_params: dict) -> str | None:
        profit_harvest_requested = self._bool_param_enabled(
            self._configured_vnext_profit_harvest_mfe_capture_v4_params()["enabled"]
        ) or self._bool_param_enabled(
            trade_params.get("gtos_vnext_profit_harvest_mfe_capture_v4_enabled")
        )
        if not trade_params.get("gtos_vnext_dynamic_policy_applied"):
            if (
                profit_harvest_requested
            ) and self._vnext_profit_harvest_mfe_capture_v4_params(trade_params) is None:
                return "missing_or_invalid_vnext_profit_harvest_mfe_capture_v4_params"
            return None
        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        if selected_policy not in SUPPORTED_VNEXT_DYNAMIC_EXECUTION_POLICIES:
            return f"unsupported_vnext_dynamic_policy:{selected_policy or 'missing'}"
        if (
            selected_policy == "be_after_trigger"
            and self._vnext_be_after_trigger_params(trade_params) is None
        ):
            return "missing_or_invalid_vnext_be_after_trigger_params"
        if (
            selected_policy == "partial_be_runner"
            and self._vnext_partial_be_runner_params(trade_params) is None
        ):
            return "missing_or_invalid_vnext_partial_be_runner_params"
        if (
            selected_policy == "trailing_runner"
            and self._vnext_trailing_runner_params(trade_params) is None
        ):
            return "missing_or_invalid_vnext_trailing_runner_params"
        if (
            selected_policy == "momentum_exhaustion"
            and self._vnext_momentum_exhaustion_params(trade_params) is None
        ):
            return "missing_or_invalid_vnext_momentum_exhaustion_params"
        if selected_policy == "time_stop" and self._vnext_time_stop_params(trade_params) is None:
            return "missing_or_invalid_vnext_time_stop_params"
        if (
            profit_harvest_requested
        ) and self._vnext_profit_harvest_mfe_capture_v4_params(trade_params) is None:
            return "missing_or_invalid_vnext_profit_harvest_mfe_capture_v4_params"
        return None

    @staticmethod
    def _target_price_from_r(
        *,
        direction: str,
        entry_price: float,
        sl_distance: float,
        target_r: float,
    ) -> float:
        if direction == "LONG":
            return entry_price + target_r * sl_distance
        return entry_price - target_r * sl_distance

    def _mt5_symbol_info(self):
        try:
            mt5_module = getattr(self.mt5, "_mt5", None)
            if mt5_module is not None and hasattr(mt5_module, "symbol_info"):
                return mt5_module.symbol_info(self.symbol)
        except Exception as exc:  # noqa: BLE001
            logger.debug("MT5 symbol_info unavailable for %s: %s", self.symbol, exc)
        return None

    @staticmethod
    def _vnext_requires_verified_broker_geometry(trade_params: dict) -> bool:
        return bool(
            trade_params.get("gtos_vnext_selected_cell_risk_cell_id")
            or trade_params.get("gtos_vnext_selected_cell_risk_pct") is not None
        )

    @staticmethod
    def _trade_requires_verified_broker_geometry(trade: TradeState) -> bool:
        return bool(
            getattr(trade, "gtos_vnext_selected_cell_risk_cell_id", None)
            or getattr(trade, "gtos_vnext_selected_cell_risk_pct", None) is not None
        )

    def _is_vnext_production_execution_path(self, trade_params: dict) -> bool:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        return bool(
            trade_params.get("gtos_vnext_production_execution_path")
            or (
                self._vnext_requires_verified_broker_geometry(trade_params)
                and bool(cfg.get("enabled", False))
                and bool(cfg.get("apply_to_execution", False))
                and str(cfg.get("mode") or "").strip().lower()
                == "production_replacement_vnext_moonshot"
            )
        )

    def _selected_cell_risk_pct(self, trade_params: dict) -> float | None:
        raw = trade_params.get("gtos_vnext_selected_cell_risk_pct")
        try:
            risk_pct = float(raw)
        except (TypeError, ValueError):
            return None
        return risk_pct if risk_pct > 0 else None

    def _resolve_vnext_production_risk_pct(
        self,
        trade_params: dict,
        *,
        risk_pct_override: float | None,
    ) -> tuple[float | None, str | None]:
        if not self._is_vnext_production_execution_path(trade_params):
            return risk_pct_override, None

        selected_cell = str(
            trade_params.get("gtos_vnext_selected_cell_risk_cell_id") or ""
        ).strip()
        selected_risk_pct = self._selected_cell_risk_pct(trade_params)
        if not selected_cell or selected_risk_pct is None:
            return (
                None,
                "missing_selected_cell_risk_pct_or_cell_id_for_vnext_production",
            )

        selected_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_selected") or ""
        ).strip().lower()
        risk_selected_policy = str(
            trade_params.get("gtos_vnext_selected_cell_risk_selected_policy") or ""
        ).strip().lower()
        risk_identity_status = str(
            trade_params.get("gtos_vnext_selected_cell_risk_policy_identity_status") or ""
        ).strip().lower()
        if selected_policy:
            if not risk_selected_policy or not risk_identity_status:
                return (
                    None,
                    "missing_selected_policy_risk_identity_for_vnext_production",
                )
            if risk_selected_policy != selected_policy:
                return (
                    None,
                    "selected_policy_risk_identity_mismatch:"
                    f"selected={selected_policy} risk={risk_selected_policy}",
                )
            if (
                risk_identity_status not in {
                    "exact_selected_policy_risk_match",
                    "policy_invariant_broker_geometry_for_selected_execution_policy",
                }
                and not risk_identity_status.startswith("policy_invariant")
            ):
                return (
                    None,
                    "unsupported_selected_policy_risk_identity_status:"
                    + risk_identity_status,
                )

        unresolved = trade_params.get(
            "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons"
        )
        if unresolved is None:
            unresolved = trade_params.get("gtos_vnext_selected_cell_risk_unresolved_reasons")
        if isinstance(unresolved, str):
            unresolved_reasons = [unresolved] if unresolved.strip() else []
        elif isinstance(unresolved, (list, tuple, set)):
            unresolved_reasons = [str(item) for item in unresolved if str(item).strip()]
        else:
            unresolved_reasons = []
        if unresolved_reasons:
            return (
                None,
                "selected_cell_risk_has_unresolved_reasons:"
                + ",".join(sorted(unresolved_reasons)),
            )

        if risk_pct_override is not None:
            try:
                override = float(risk_pct_override)
            except (TypeError, ValueError):
                return None, "invalid_risk_pct_override_for_vnext_production"
            if override <= 0:
                return None, "nonpositive_risk_pct_override_for_vnext_production"
            if override - selected_risk_pct > 1e-9:
                return (
                    None,
                    "risk_pct_override_exceeds_selected_cell:"
                    f"override={override} selected={selected_risk_pct}",
                )
            return override, None

        return selected_risk_pct, None

    def _vnext_pretrade_cost_model(
        self,
        *,
        trade_params: dict,
        tick,
        entry_price: float,
        sl_distance: float,
        risk_pct: float,
    ) -> tuple[dict, str | None]:
        if not self._is_vnext_production_execution_path(trade_params):
            return {}, None
        model = build_pretrade_cost_packet(
            config=self.config,
            trade_params=trade_params,
            tick=tick,
            symbol=self._persist_symbol,
            broker_symbol=self.symbol,
            entry_price=entry_price,
            stop_loss=trade_params.get("stop_loss"),
            sl_distance=sl_distance,
            risk_pct=risk_pct,
            symbol_info=self._mt5_symbol_info(),
        )
        trade_params["gtos_vnext_pretrade_cost_model"] = model
        return model, pretrade_cost_refusal_reason(model)

    @staticmethod
    def _history_time_to_iso(value) -> str | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return str(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    @classmethod
    def _history_time_to_iso_near_reference(
        cls,
        value,
        reference: datetime | None,
        *,
        max_shift_hours: int = 6,
        tolerance_minutes: int = 10,
    ) -> tuple[str | None, int | None]:
        """Normalize broker-history timestamps that were returned with a stale server offset.

        MT5 history queries can still return the right deal while the wrapper has not yet
        detected server time. In that case the deal timestamp is broker-local time labelled
        as UTC, usually exactly one broker offset away from the order result timestamp.
        """
        iso = cls._history_time_to_iso(value)
        if not iso or reference is None:
            return iso, None
        try:
            dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return iso, None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc)
        ref = reference
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)
        ref = ref.astimezone(timezone.utc)

        best = dt
        best_shift = 0
        best_distance = abs((dt - ref).total_seconds())
        for hours in range(-int(max_shift_hours), int(max_shift_hours) + 1):
            candidate = dt - timedelta(hours=hours)
            distance = abs((candidate - ref).total_seconds())
            if distance < best_distance:
                best = candidate
                best_shift = hours
                best_distance = distance
        if best_shift and best_distance <= int(tolerance_minutes) * 60:
            return best.isoformat(), best_shift * 3600
        return dt.isoformat(), None

    @staticmethod
    def _int_or_none(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _recover_entry_ticket_after_fill(
        self,
        result: OrderResult,
        entry_deal_accounting: dict,
    ) -> int | None:
        ticket = self._positive_int_or_none(getattr(result, "order", None))
        if ticket is not None:
            return ticket
        match_keys = entry_deal_accounting.get("account_history_lookup_match_keys")
        if isinstance(match_keys, dict):
            ticket = (
                self._positive_int_or_none(match_keys.get("position_id"))
                or self._positive_int_or_none(match_keys.get("order"))
            )
            if ticket is not None:
                return ticket
        get_positions = getattr(self.mt5, "get_positions", None)
        if not callable(get_positions):
            return None
        try:
            positions = get_positions(self.symbol)
        except TypeError:
            positions = get_positions()
        except Exception:
            return None
        recovered: list[int] = []
        for pos in positions or []:
            pos_ticket = self._positive_int_or_none(getattr(pos, "ticket", None))
            if pos_ticket is None or pos_ticket in self._known_tickets:
                continue
            pos_symbol = str(getattr(pos, "symbol", "") or "")
            if pos_symbol and pos_symbol not in {str(self.symbol), str(self._persist_symbol)}:
                continue
            recovered.append(pos_ticket)
        return recovered[0] if len(recovered) == 1 else None

    @staticmethod
    def _deal_time_to_utc_iso(value) -> str | None:
        if value in (None, ""):
            return None
        try:
            if isinstance(value, datetime):
                dt = value
            elif isinstance(value, (int, float)):
                dt = datetime.fromtimestamp(value, tz=timezone.utc)
            else:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        except Exception:
            return None

    @classmethod
    def _deal_time_to_utc_dt(cls, value) -> datetime | None:
        iso = cls._deal_time_to_utc_iso(value)
        if not iso:
            return None
        try:
            dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        except (TypeError, ValueError):
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _lookup_close_deal_accounting(
        self,
        *,
        trade: TradeState,
        result: Any,
        close_ticket: int | None = None,
        closed_at_utc: Any | None = None,
    ) -> dict:
        payload = {
            "close_account_history_lookup_status": "ACCOUNT_HISTORY_LOOKUP_UNAVAILABLE",
            "close_account_history_lookup_attempted": False,
        }
        history_lookup = getattr(self.mt5, "get_history_deals", None)
        if not callable(history_lookup):
            return payload
        ticket = self._positive_int_or_none(close_ticket) or self._positive_int_or_none(
            getattr(trade, "ticket", None)
        )
        order_id = self._positive_int_or_none(getattr(result, "order", None))
        deal_id = self._positive_int_or_none(getattr(result, "deal", None))
        end_utc = datetime.now(timezone.utc) + timedelta(minutes=15)
        entry_time = self._deal_time_to_utc_iso(getattr(trade, "entry_time", None))
        start_utc = None
        if entry_time:
            try:
                start_utc = datetime.fromisoformat(entry_time.replace("Z", "+00:00")) - timedelta(minutes=10)
            except Exception:
                start_utc = None
        if start_utc is None:
            start_utc = end_utc - timedelta(days=7)
        payload.update(
            {
                "close_account_history_lookup_attempted": True,
                "close_account_history_lookup_window_start_utc": start_utc.isoformat(),
                "close_account_history_lookup_window_end_utc": end_utc.isoformat(),
                "close_account_history_lookup_match_keys": {
                    "position_id": ticket,
                    "order": order_id,
                    "deal": deal_id,
                },
            }
        )
        runtime_cfg = self.config.get("gtos_vnext_runtime", self.config) if isinstance(self.config, dict) else {}
        try:
            lookup_attempts = max(
                1,
                int(runtime_cfg.get("broker_exit_history_lookup_attempts", 5) or 5),
            )
        except (TypeError, ValueError):
            lookup_attempts = 5
        try:
            lookup_sleep_seconds = max(
                0.0,
                float(runtime_cfg.get("broker_exit_history_lookup_sleep_seconds", 0.25) or 0.25),
            )
        except (TypeError, ValueError):
            lookup_sleep_seconds = 0.25
        payload["close_account_history_lookup_attempt_count"] = lookup_attempts
        reference_dt = (
            self._deal_time_to_utc_dt(closed_at_utc)
            or self._deal_time_to_utc_dt(getattr(result, "time", None))
            or end_utc
        )

        def _exit_deal_rows(deals: Any) -> list[Any]:
            try:
                iterable = list(deals or [])
            except TypeError:
                return []
            out: list[Any] = []
            for deal in iterable:
                entry = self._int_or_none(self._source_value(deal, "entry"))
                if entry in {1, 2, 3}:
                    out.append(deal)
            return out

        def _distance_seconds(deal: Any) -> float:
            deal_dt = self._deal_time_to_utc_dt(self._source_value(deal, "time"))
            if deal_dt is None:
                return float("inf")
            return abs((deal_dt - reference_dt).total_seconds())

        def _select_close_deal(deals: Any) -> tuple[Any | None, str | None, list[Any], float | None]:
            exit_deals = _exit_deal_rows(deals)
            position_candidates = [
                deal
                for deal in exit_deals
                if ticket is not None
                and self._positive_int_or_none(self._source_value(deal, "position_id")) == ticket
            ]
            for deal in exit_deals:
                deal_ticket = self._positive_int_or_none(self._source_value(deal, "ticket"))
                if deal_id is not None and deal_ticket == deal_id:
                    return deal, "deal_ticket", position_candidates, _distance_seconds(deal)
            for deal in exit_deals:
                order_ticket = self._positive_int_or_none(self._source_value(deal, "order"))
                if order_id is not None and order_ticket == order_id:
                    return deal, "order_ticket", position_candidates, _distance_seconds(deal)
            if position_candidates:
                selected = min(
                    position_candidates,
                    key=lambda deal: (
                        _distance_seconds(deal),
                        str(self._deal_time_to_utc_iso(self._source_value(deal, "time")) or ""),
                    ),
                )
                return selected, "position_id_nearest_exit_time", position_candidates, _distance_seconds(selected)
            return None, None, position_candidates, None

        def _sum_float(deals: list[Any], field: str) -> float | None:
            total = 0.0
            seen = False
            for deal in deals:
                value = self._safe_float(self._source_value(deal, field))
                if value is None:
                    continue
                total += value
                seen = True
            return total if seen else None

        match = None
        match_reason = None
        position_exit_deals: list[Any] = []
        selected_distance_seconds = None
        history_fetch_failed = False
        history_fetch_error = None
        history_source_returned = False
        last_candidate_count = 0
        for attempt in range(1, lookup_attempts + 1):
            try:
                deals = history_lookup(start_utc, end_utc, self.symbol)
            except Exception as exc:  # noqa: BLE001 - close telemetry must not affect execution
                history_fetch_failed = True
                history_fetch_error = str(exc)
                deals = None
            if deals is None:
                history_fetch_failed = True
                history_fetch_error = history_fetch_error or "history_lookup_returned_none"
                if attempt < lookup_attempts and lookup_sleep_seconds > 0:
                    time.sleep(lookup_sleep_seconds)
                continue
            history_source_returned = True
            match, match_reason, position_exit_deals, selected_distance_seconds = _select_close_deal(deals)
            last_candidate_count = len(position_exit_deals)
            payload["close_account_history_lookup_attempt_count"] = attempt
            if match is not None:
                break
            if attempt < lookup_attempts and lookup_sleep_seconds > 0:
                time.sleep(lookup_sleep_seconds)
        if match is None:
            payload["close_account_history_lookup_candidate_count"] = last_candidate_count
            if history_fetch_failed and not history_source_returned:
                payload["close_account_history_lookup_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                payload["close_account_history_lookup_error"] = history_fetch_error or "history_lookup_failed"
            else:
                payload["close_account_history_lookup_status"] = "NO_EXIT_DEAL_FOUND"
                if history_fetch_error:
                    payload["close_account_history_lookup_error"] = history_fetch_error
            return payload

        commission = self._safe_float(self._source_value(match, "commission"))
        fee = self._safe_float(self._source_value(match, "fee"))
        if fee is not None:
            commission = (commission or 0.0) + fee
        swap = self._safe_float(self._source_value(match, "swap"))
        profit = self._safe_float(self._source_value(match, "profit"))
        broker_exit_price = self._safe_float(self._source_value(match, "price"))
        deal_ticket = self._positive_int_or_none(self._source_value(match, "ticket"))
        order_ticket = self._positive_int_or_none(self._source_value(match, "order"))
        position_id = self._positive_int_or_none(self._source_value(match, "position_id"))
        aggregate_deals = position_exit_deals or [match]
        aggregate_profit = _sum_float(aggregate_deals, "profit")
        aggregate_commission = _sum_float(aggregate_deals, "commission")
        aggregate_swap = _sum_float(aggregate_deals, "swap")
        aggregate_fee = _sum_float(aggregate_deals, "fee")
        aggregate_net = None
        if any(value is not None for value in (
            aggregate_profit,
            aggregate_commission,
            aggregate_swap,
            aggregate_fee,
        )):
            aggregate_net = sum(
                value or 0.0
                for value in (
                    aggregate_profit,
                    aggregate_commission,
                    aggregate_swap,
                    aggregate_fee,
                )
            )
        payload.update(
            {
                "close_account_history_lookup_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                "close_account_history_lookup_match_keys": {
                    "matched_by": match_reason,
                    "position_id": position_id,
                    "order": order_ticket,
                    "deal": deal_ticket,
                    "entry": self._int_or_none(self._source_value(match, "entry")),
                    "price": broker_exit_price,
                    "nearest_exit_time_distance_seconds": selected_distance_seconds,
                },
                "close_account_history_lookup_candidate_count": len(position_exit_deals),
                "accounting_source": "MT5_HISTORY_DEALS_READONLY",
                "deal_ticket": deal_ticket,
                "order_ticket": order_ticket,
                "broker_exit_position_id": position_id,
                "broker_exit_time_utc": self._deal_time_to_utc_iso(self._source_value(match, "time")),
                "broker_exit_price": broker_exit_price,
                "broker_profit": profit,
                "commission": commission,
                "swap": swap,
                "broker_exit_fee": fee,
                "broker_exit_position_deal_count": len(aggregate_deals),
                "broker_exit_position_deal_tickets": [
                    self._positive_int_or_none(self._source_value(deal, "ticket"))
                    for deal in aggregate_deals
                    if self._positive_int_or_none(self._source_value(deal, "ticket")) is not None
                ],
                "broker_exit_aggregate_profit": aggregate_profit,
                "broker_exit_aggregate_commission": aggregate_commission,
                "broker_exit_aggregate_swap": aggregate_swap,
                "broker_exit_aggregate_fee": aggregate_fee,
                "broker_exit_aggregate_net_profit": aggregate_net,
            }
        )
        return payload

    @staticmethod
    def _order_type_for_direction(direction: str | None) -> int | None:
        side = str(direction or "").upper()
        if side == "LONG":
            return 0
        if side == "SHORT":
            return 1
        return None

    def _order_calc_profit(
        self,
        *,
        direction: str | None,
        volume: float,
        entry_price: float,
        target_price: float,
    ) -> float | None:
        order_type = self._order_type_for_direction(direction)
        if order_type is None:
            return None
        raw_mt5 = getattr(self.mt5, "_mt5", None)
        order_calc_profit = getattr(raw_mt5, "order_calc_profit", None)
        if not callable(order_calc_profit):
            return None
        try:
            value = order_calc_profit(
                order_type,
                self.symbol,
                float(volume),
                float(entry_price),
                float(target_price),
            )
        except Exception as exc:  # noqa: BLE001
            logger.debug(
                "MT5 order_calc_profit unavailable for %s %s volume=%.4f "
                "entry=%.5f target=%.5f: %s",
                self.symbol,
                direction,
                volume,
                entry_price,
                target_price,
                exc,
            )
            return None
        try:
            profit = float(value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(profit):
            return None
        return profit

    def _broker_cash_risk_amount(
        self,
        *,
        direction: str | None,
        volume: float,
        entry_price: float,
        stop_loss: float,
    ) -> float | None:
        profit_at_stop = self._order_calc_profit(
            direction=direction,
            volume=volume,
            entry_price=entry_price,
            target_price=stop_loss,
        )
        if profit_at_stop is None:
            return None
        if profit_at_stop >= 0:
            return None
        return abs(profit_at_stop)

    def _lookup_entry_deal_accounting(
        self,
        result: OrderResult,
        *,
        order_send_time: datetime,
        order_result_time: datetime,
    ) -> dict:
        window_start = order_send_time - timedelta(minutes=5)
        window_end = order_result_time + timedelta(minutes=5)
        payload = {
            "account_history_lookup_attempted": False,
            "account_history_lookup_status": "ACCOUNT_HISTORY_LOOKUP_UNAVAILABLE",
            "account_history_lookup_window_start_utc": window_start.isoformat(),
            "account_history_lookup_window_end_utc": window_end.isoformat(),
            "account_history_lookup_error": None,
            "account_history_lookup_match_keys": None,
            "account_history_lookup_recovery_attempted": False,
            "account_history_lookup_recovery_window_start_utc": None,
            "account_history_lookup_recovery_window_end_utc": None,
            "account_history_lookup_recovery_error": None,
            "commission": None,
            "swap": None,
            "deal_ticket": getattr(result, "deal", None),
            "broker_fill_time_utc": None,
            "broker_fill_time_alignment_offset_seconds": None,
            "broker_entry_price": None,
        }
        history_lookup = getattr(self.mt5, "get_history_deals", None)
        if not callable(history_lookup):
            return payload

        order_id = self._positive_int_or_none(getattr(result, "order", None))
        deal_id = self._positive_int_or_none(getattr(result, "deal", None))
        match = None
        match_reason = None

        def _find_entry_deal(deals: list[dict]) -> tuple[Optional[dict], Optional[str]]:
            for deal in deals:
                if not isinstance(deal, dict):
                    continue
                ticket = self._positive_int_or_none(deal.get("ticket"))
                order = self._positive_int_or_none(deal.get("order"))
                position_id = self._positive_int_or_none(deal.get("position_id"))
                entry = self._int_or_none(deal.get("entry"))
                if entry not in (None, 0):
                    continue
                if deal_id is not None and ticket == deal_id:
                    return deal, "deal_ticket"
                if order_id is not None and order == order_id:
                    return deal, "order_ticket"
                if order_id is not None and position_id == order_id:
                    return deal, "position_id_matches_order"
            return None, None

        payload["account_history_lookup_attempted"] = True
        runtime_cfg = self.config.get("gtos_vnext_runtime", self.config) or {}
        try:
            lookup_attempts = max(
                1,
                int(runtime_cfg.get("broker_entry_history_lookup_attempts", 5) or 5),
            )
        except (TypeError, ValueError):
            lookup_attempts = 5
        try:
            lookup_sleep_seconds = max(
                0.0,
                float(runtime_cfg.get("broker_entry_history_lookup_sleep_seconds", 0.25) or 0.25),
            )
        except (TypeError, ValueError):
            lookup_sleep_seconds = 0.25
        payload["account_history_lookup_attempt_count"] = lookup_attempts
        history_fetch_failed = False
        history_source_returned = False
        history_fetch_error = None
        for attempt in range(lookup_attempts):
            try:
                deals = history_lookup(window_start, window_end, self.symbol)
            except Exception as exc:  # noqa: BLE001 - reconciliation must not block filled trades
                history_fetch_failed = True
                history_fetch_error = str(exc)
                deals = None
            if deals is None:
                history_fetch_failed = True
                history_fetch_error = history_fetch_error or "history_lookup_returned_none"
                if attempt < lookup_attempts - 1 and lookup_sleep_seconds > 0:
                    time.sleep(lookup_sleep_seconds)
                continue
            history_source_returned = True
            match, match_reason = _find_entry_deal(deals)
            if match is not None:
                payload["account_history_lookup_attempt_count"] = attempt + 1
                break
            if attempt < lookup_attempts - 1 and lookup_sleep_seconds > 0:
                time.sleep(lookup_sleep_seconds)

        recovery_window_used = False
        if match is None and (order_id is not None or deal_id is not None):
            try:
                recovery_hours = max(
                    1.0,
                    float(runtime_cfg.get("broker_entry_history_recovery_window_hours", 6.0) or 6.0),
                )
            except (TypeError, ValueError):
                recovery_hours = 6.0
            recovery_start = window_start - timedelta(hours=recovery_hours)
            recovery_end = window_end + timedelta(hours=recovery_hours)
            payload["account_history_lookup_recovery_attempted"] = True
            payload["account_history_lookup_recovery_window_start_utc"] = recovery_start.isoformat()
            payload["account_history_lookup_recovery_window_end_utc"] = recovery_end.isoformat()
            try:
                deals = history_lookup(recovery_start, recovery_end, self.symbol)
            except Exception as exc:  # noqa: BLE001 - recovery is observability-only
                history_fetch_failed = True
                history_fetch_error = str(exc)
                payload["account_history_lookup_recovery_error"] = str(exc)
            else:
                if deals is None:
                    history_fetch_failed = True
                    history_fetch_error = history_fetch_error or "history_lookup_returned_none"
                    payload["account_history_lookup_recovery_error"] = "history_lookup_returned_none"
                else:
                    history_source_returned = True
                    match, match_reason = _find_entry_deal(deals)
                    recovery_window_used = match is not None

        if match is None:
            if history_fetch_failed and not history_source_returned:
                payload["account_history_lookup_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                payload["account_history_lookup_error"] = history_fetch_error
            else:
                payload["account_history_lookup_status"] = "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
            payload["account_history_lookup_match_keys"] = {
                "order": order_id,
                "deal": deal_id,
            }
            return payload

        fill_time, fill_time_alignment_offset = self._history_time_to_iso_near_reference(
            match.get("time"),
            order_result_time,
        )
        payload.update(
            {
                "account_history_lookup_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                "account_history_lookup_match_keys": {
                    "matched_by": (
                        f"{match_reason}_recovery_window" if recovery_window_used else match_reason
                    ),
                    "order": self._positive_int_or_none(match.get("order")),
                    "ticket": self._positive_int_or_none(match.get("ticket")),
                    "position_id": self._positive_int_or_none(match.get("position_id")),
                    "price": self._safe_float(match.get("price")),
                    "recovery_window_used": recovery_window_used,
                },
                "commission": match.get("commission"),
                "swap": match.get("swap"),
                "deal_ticket": self._positive_int_or_none(match.get("ticket"))
                or self._positive_int_or_none(getattr(result, "deal", None)),
                "broker_fill_time_utc": fill_time,
                "broker_fill_time_alignment_offset_seconds": fill_time_alignment_offset,
                "broker_entry_price": match.get("price"),
            }
        )
        return payload

    def _normalize_volume(
        self,
        lots: float,
        sym_info,
        *,
        require_broker_geometry: bool,
    ) -> float | None:
        if require_broker_geometry:
            if sym_info is None:
                logger.error("vNext selected-cell order missing broker symbol_info")
                return None
            try:
                volume_min = float(sym_info.volume_min)
                volume_step = float(sym_info.volume_step)
                volume_max = float(sym_info.volume_max)
            except (TypeError, ValueError, AttributeError):
                logger.error("vNext selected-cell order missing broker volume geometry")
                return None
            if volume_min <= 0 or volume_step <= 0 or volume_max <= 0:
                logger.error("vNext selected-cell order has invalid broker volume geometry")
                return None
            if lots < volume_min:
                logger.error(
                    "vNext selected-cell order lot %.8f below broker min %.8f",
                    lots,
                    volume_min,
                )
                return None
            lots = min(lots, volume_max)
            # `math.floor` on a raw binary quotient truncates a value that is
            # mathematically an exact integer. With volume_min == volume_step == 0.01,
            # `(0.03 - 0.01) / 0.01` is 1.9999999999999996, so 0.03 normalizes to 0.02
            # — and `_close_request_execution_geometry:2641` then refuses the close,
            # because it demands the normalized volume equal the requested one to 1e-9.
            #
            # That is a STRAND, not a rounding nit. Nine close producers route through
            # that check (`:7722, 7879, 7932, 8048, 8122, 8199, 8264, 8319, 8446`), the live book always takes the
            # verified-geometry branch (`ultimate_book/execution_packets.py:318-319` sets
            # the selected-cell risk fields that `_trade_requires_verified_broker_geometry`
            # keys on), and each producer returns before `safe_place_order` — so nothing
            # reaches the activation layer and no retry can ever succeed, because the next
            # tick recomputes the identical volume.
            #
            # Measured on THIS file (B333, re-measured on the host lineage 2026-07-29,
            # B551): 33 of 300 two-decimal lot sizes are affected at (0.01, 0.01), and it
            # is worse on coarser geometry — 253 of 500 at (0.10, 0.10). 44 of 327 real
            # broker close deals in `vps-export-20260725` carried an affected volume.
            #
            # The epsilon is a step-count tolerance, not a volume tolerance. It can only
            # promote a quotient already within 1e-9 of an integer, i.e. a lot size
            # within 1e-11 of the next step — far below any broker's volume resolution —
            # so a genuinely mis-aligned volume still rounds DOWN, and the normalized
            # result can never exceed the request.
            steps = math.floor((lots - volume_min) / volume_step + _VOLUME_STEP_EPSILON)
            normalized = volume_min + max(0, steps) * volume_step
            normalized = round(normalized, 8)
            # Never hand back more than was asked for, whatever the arithmetic did.
            return normalized if normalized <= lots + 1e-12 else round(lots, 8)

        lots = math.floor(lots * 100) / 100
        return max(lots, 0.01)

    def _order_filling_mode(self, sym_info, *, require_broker_geometry: bool) -> int | None:
        if not require_broker_geometry:
            return 1  # ORDER_FILLING_IOC legacy default
        if sym_info is None or not hasattr(sym_info, "filling_mode"):
            logger.error("vNext selected-cell order missing broker filling mode")
            return None
        try:
            filling_mode = int(sym_info.filling_mode)
        except (TypeError, ValueError):
            logger.error("vNext selected-cell order has invalid broker filling mode")
            return None
        # MetaTrader stores allowed modes as a bitmask on many brokers.
        # Prefer IOC when available, then FOK. Avoid BOC for market orders.
        if filling_mode & 2:
            return 1  # ORDER_FILLING_IOC
        if filling_mode & 1:
            return 0  # ORDER_FILLING_FOK
        logger.error("vNext selected-cell order has no market-compatible filling mode")
        return None

    def _order_deviation_points(self, sym_info, trade_params: dict, *, require_broker_geometry: bool) -> int | None:
        configured = trade_params.get("gtos_vnext_broker_deviation_points")
        if configured is not None:
            try:
                points = int(configured)
                return max(points, 0)
            except (TypeError, ValueError):
                if require_broker_geometry:
                    logger.error("vNext selected-cell order has invalid configured deviation")
                    return None
        if require_broker_geometry:
            if sym_info is None or not hasattr(sym_info, "spread"):
                logger.error("vNext selected-cell order missing broker spread for deviation")
                return None
            try:
                return max(1, int(float(sym_info.spread)))
            except (TypeError, ValueError):
                logger.error("vNext selected-cell order has invalid broker spread for deviation")
                return None
        configured = self.config.get("execution", {}).get("deviation_points")
        if configured is not None:
            try:
                points = int(configured)
                return max(points, 0)
            except (TypeError, ValueError):
                logger.warning("Invalid legacy configured deviation; using MT5 default fallback")
        if not require_broker_geometry:
            return 20

    def _close_request_execution_geometry(
        self,
        trade: TradeState,
        requested_volume: float,
        *,
        close_reason: str,
    ) -> Optional[dict]:
        require_broker_geometry = self._trade_requires_verified_broker_geometry(trade)
        sym_info = self._mt5_symbol_info()
        volume = self._normalize_volume(
            requested_volume,
            sym_info,
            require_broker_geometry=require_broker_geometry,
        )
        if volume is None:
            logger.error("Cannot calculate verified close volume for %s", close_reason)
            return None
        if require_broker_geometry and abs(float(volume) - float(requested_volume)) > 1e-9:
            logger.error(
                "vNext selected-cell close volume %.8f is not broker-step aligned "
                "(normalized %.8f) for %s",
                requested_volume,
                volume,
                close_reason,
            )
            return None
        type_filling = self._order_filling_mode(
            sym_info,
            require_broker_geometry=require_broker_geometry,
        )
        if type_filling is None:
            logger.error("Cannot resolve verified close filling mode for %s", close_reason)
            return None
        deviation_points = self._order_deviation_points(
            sym_info,
            {},
            require_broker_geometry=require_broker_geometry,
        )
        if deviation_points is None:
            logger.error("Cannot resolve verified close deviation for %s", close_reason)
            return None
        return {
            "volume": volume,
            "deviation": deviation_points,
            "type_filling": type_filling,
        }


    @staticmethod
    def _vnext_be_after_trigger_active(trade: TradeState) -> bool:
        return bool(
            trade.gtos_vnext_dynamic_be_after_trigger_active
            and trade.gtos_vnext_dynamic_policy_applied
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            == "be_after_trigger"
        )

    @staticmethod
    def _vnext_partial_be_runner_active(trade: TradeState) -> bool:
        return bool(
            trade.gtos_vnext_dynamic_policy_applied
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            == "partial_be_runner"
        )

    @staticmethod
    def _vnext_trailing_runner_active(trade: TradeState) -> bool:
        return bool(
            trade.gtos_vnext_dynamic_policy_applied
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            == "trailing_runner"
        )

    @staticmethod
    def _vnext_momentum_exhaustion_active(trade: TradeState) -> bool:
        return bool(
            trade.gtos_vnext_dynamic_policy_applied
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            == "momentum_exhaustion"
        )

    @staticmethod
    def _vnext_time_stop_active(trade: TradeState) -> bool:
        return bool(
            trade.gtos_vnext_dynamic_policy_applied
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            in {
                "be_after_trigger",
                "partial_be_runner",
                "trailing_runner",
                "momentum_exhaustion",
                "time_stop",
            }
            and trade.gtos_vnext_dynamic_time_stop_bars is not None
        )

    @staticmethod
    def _vnext_no_broker_take_profit(trade_params: dict) -> bool:
        mode = str(
            trade_params.get("gtos_vnext_dynamic_broker_take_profit_mode") or ""
        ).strip().lower()
        return mode in {"none", "no_tp", "targetless"} or bool(
            trade_params.get("gtos_vnext_dynamic_no_broker_take_profit")
        )

    @staticmethod
    def _vnext_profit_harvest_mfe_capture_v4_active(trade: TradeState) -> bool:
        return bool(
            trade.gtos_vnext_profit_harvest_mfe_capture_v4_enabled
            and trade.gtos_vnext_dynamic_policy_applied
        )

    @staticmethod
    def _vnext_broker_close_requires_deal_confirmation(trade: TradeState) -> bool:
        return bool(
            getattr(trade, "gtos_vnext_dynamic_policy_applied", False)
            or getattr(trade, "gtos_vnext_execution_policy_id", None)
            or getattr(trade, "gtos_vnext_production_execution_path", False)
        )

    def _broker_close_deal_confirmation_status(self, trade: TradeState) -> str:
        now_utc = datetime.now(timezone.utc)
        start_utc = now_utc - timedelta(days=3)
        end_utc = now_utc + timedelta(minutes=5)

        def _deal_field(deal, field: str, default=None):
            if isinstance(deal, dict):
                return deal.get(field, default)
            return getattr(deal, field, default)

        def _has_close_deal(deals) -> bool:
            for deal in deals or []:
                try:
                    position_id = int(_deal_field(deal, "position_id", 0) or 0)
                    entry_type = int(_deal_field(deal, "entry", -1))
                except (TypeError, ValueError):
                    continue
                if position_id == int(trade.ticket) and entry_type == 1:
                    return True
            return False

        any_history_source_available = False
        get_history_deals = getattr(self.mt5, "get_history_deals", None)
        if callable(get_history_deals):
            try:
                deals = get_history_deals(start_utc, end_utc, self.symbol)
            except Exception:
                logger.exception(
                    "Unable to confirm MT5 close deal for vNext ticket %s via wrapper",
                    trade.ticket,
                )
                deals = None
            if deals is not None:
                any_history_source_available = True
                if _has_close_deal(deals):
                    return "CLOSE_DEAL_FOUND"

        mt5_module = getattr(self.mt5, "_mt5", None)
        history_deals_get = getattr(mt5_module, "history_deals_get", None)
        if callable(history_deals_get):
            try:
                try:
                    deals = history_deals_get(start_utc, end_utc, self.symbol)
                except TypeError:
                    deals = history_deals_get(start_utc, end_utc)
            except Exception:
                logger.exception(
                    "Unable to confirm MT5 close deal for vNext ticket %s via raw MT5",
                    trade.ticket,
                )
                deals = None
            if deals is not None:
                any_history_source_available = True
                if _has_close_deal(deals):
                    return "CLOSE_DEAL_FOUND"

        if any_history_source_available:
            return "NO_CLOSE_DEAL_FOUND"
        return "HISTORY_UNAVAILABLE"

    @staticmethod
    def _positive_float(value) -> Optional[float]:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if math.isfinite(number) and number > 0:
            return number
        return None

    @staticmethod
    def _parse_trade_time(value) -> Optional[datetime]:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def _record_original_sl_distance(
        self,
        *,
        trade: TradeState,
        record: dict,
        entry_price: float | None,
        execution: dict,
    ) -> float | None:
        candidates: list[tuple[str, float]] = []

        def _add(source: str, value) -> None:
            numeric = self._positive_float(value)
            if numeric is not None:
                candidates.append((source, numeric))

        instrumentation = record.get("instrumentation") if isinstance(record, dict) else {}
        if not isinstance(instrumentation, dict):
            instrumentation = {}
        for recovered in instrumentation.get("gtos_vnext_recovered_partial_close_events") or []:
            if isinstance(recovered, dict):
                _add("recovered_partial_close_event.sl_distance", recovered.get("sl_distance"))

        _add("execution.original_sl_distance", execution.get("original_sl_distance"))
        _add("execution.entry_sl_distance", execution.get("entry_sl_distance"))
        _add("execution.initial_sl_distance", execution.get("initial_sl_distance"))
        _add("execution.sl_distance", execution.get("sl_distance"))

        limit_intent = record.get("limit_intent") if isinstance(record, dict) else {}
        if not isinstance(limit_intent, dict):
            limit_intent = {}

        def _distance_to_stop(source: str, stop_value) -> None:
            stop = self._positive_float(stop_value)
            if entry_price is not None and stop is not None:
                _add(source, abs(entry_price - stop))

        for source, value in (
            ("execution.original_stop_loss", execution.get("original_stop_loss")),
            ("execution.entry_stop_loss", execution.get("entry_stop_loss")),
            ("execution.initial_stop_loss", execution.get("initial_stop_loss")),
            ("execution.stop_loss", execution.get("stop_loss")),
            ("limit_intent.stop_loss", limit_intent.get("stop_loss")),
        ):
            _distance_to_stop(source, value)

        current = self._positive_float(getattr(trade, "sl_distance", None))
        if current is not None:
            _add("trade.sl_distance", current)

        if not candidates:
            return None
        # Recovered partial positions often have broker SL at BE. A BE-derived
        # distance is near zero and is never the original risk denominator.
        return max(value for _source, value in candidates)

    def _hydrate_recovered_geometry_from_record(
        self,
        trade: TradeState,
        record: dict,
    ) -> None:
        execution = record.get("execution") if isinstance(record, dict) else {}
        if not isinstance(execution, dict):
            execution = {}

        entry_price = self._positive_float(
            execution.get("executed_entry_price")
            or execution.get("entry_price")
            or trade.entry_price
        )
        executed_stop = self._positive_float(
            execution.get("executed_stop_price")
            or execution.get("stop_loss")
        )
        sl_distance = self._record_original_sl_distance(
            trade=trade,
            record=record,
            entry_price=entry_price,
            execution=execution,
        )
        if sl_distance is None and entry_price is not None and executed_stop is not None:
            sl_distance = abs(entry_price - executed_stop)

        recovered = str(trade.trade_id or "").startswith("adopted_") or bool(
            (record.get("instrumentation") or {}).get(
                "gtos_vnext_recovered_lifecycle_status"
            )
        )
        if recovered:
            if entry_price is not None:
                trade.entry_price = entry_price
            if sl_distance is not None:
                trade.sl_distance = sl_distance
            initial_volume = self._positive_float(execution.get("initial_volume"))
            if initial_volume is not None and initial_volume > float(trade.initial_volume or 0.0):
                trade.initial_volume = initial_volume
            cash_risk = self._positive_float(execution.get("cash_risk_amount"))
            if cash_risk is not None:
                trade.cash_risk_amount = cash_risk
            if execution.get("cash_risk_amount_source"):
                trade.cash_risk_amount_source = str(execution.get("cash_risk_amount_source"))
            if execution.get("cash_risk_amount_status"):
                trade.cash_risk_amount_status = str(execution.get("cash_risk_amount_status"))
            broker_risk_per_lot = self._positive_float(
                execution.get("broker_cash_risk_per_lot")
            )
            if broker_risk_per_lot is not None:
                trade.broker_cash_risk_per_lot = broker_risk_per_lot
            sizing_diag = execution.get("broker_lot_sizing_diagnostic")
            if isinstance(sizing_diag, dict):
                trade.broker_lot_sizing_diagnostic = sizing_diag
            risk_pct = self._positive_float(execution.get("risk_pct"))
            if risk_pct is not None:
                trade.risk_pct_at_entry = risk_pct
            fill_time = self._parse_trade_time(execution.get("fill_time_utc"))
            if fill_time is not None:
                trade.entry_time = fill_time.isoformat()
            entry_order_ticket = execution.get("entry_order_ticket")
            if entry_order_ticket not in (None, "", 0, "0"):
                trade.entry_order_ticket = entry_order_ticket
            entry_deal_ticket = execution.get("entry_deal_ticket")
            if entry_deal_ticket not in (None, "", 0, "0"):
                trade.entry_deal_ticket = entry_deal_ticket

    def _append_recovered_partial_events_from_record(
        self,
        trade: TradeState,
        record: dict,
    ) -> None:
        instrumentation = record.get("instrumentation") if isinstance(record, dict) else {}
        if not isinstance(instrumentation, dict):
            return
        recovered_events = instrumentation.get(
            "gtos_vnext_recovered_partial_close_events"
        )
        if not isinstance(recovered_events, list):
            return
        seen_keys = {
            (
                event.get("mt5_order_id"),
                event.get("time"),
                event.get("volume_closed"),
            )
            for event in trade.partial_close_events
            if isinstance(event, dict)
        }
        for recovered in recovered_events:
            if not isinstance(recovered, dict):
                continue
            key = (
                recovered.get("mt5_order_id"),
                recovered.get("time"),
                recovered.get("volume_closed"),
            )
            if key in seen_keys:
                continue
            price = self._positive_float(recovered.get("price"))
            volume_closed = self._positive_float(recovered.get("volume_closed"))
            if price is None or volume_closed is None:
                continue
            event = {
                "type": recovered.get("type")
                or "TP1_PARTIAL_RECOVERED_FROM_SLIPPAGE_LOG",
                "time": recovered.get("time") or datetime.now(timezone.utc).isoformat(),
                "price": price,
                "volume_closed": volume_closed,
                "close_reason": recovered.get("close_reason"),
                "mt5_order_id": recovered.get("mt5_order_id"),
                "mt5_deal_id": recovered.get("mt5_deal_id"),
                "commission": recovered.get("commission"),
                "swap": recovered.get("swap"),
                "sl_at_breakeven": recovered.get("sl_at_breakeven"),
                "time_in_trade_minutes": recovered.get("time_in_trade_minutes"),
                "recovery_source": recovered.get("recovery_source"),
                "recovery_source_ts": recovered.get("recovery_source_ts"),
            }
            trade.partial_close_events.append(event)
            seen_keys.add(key)
            trade.tp1_hit = True
            initial_volume = self._positive_float(recovered.get("initial_volume"))
            if initial_volume is not None and initial_volume > float(trade.initial_volume or 0.0):
                trade.initial_volume = initial_volume
            remaining_volume = self._positive_float(recovered.get("remaining_volume"))
            if remaining_volume is not None:
                trade.current_volume = remaining_volume
            sl_distance = self._positive_float(recovered.get("sl_distance"))
            if sl_distance is not None and (not trade.sl_distance or trade.sl_distance <= 0):
                trade.sl_distance = sl_distance
            cash_risk = self._positive_float(recovered.get("cash_risk_amount"))
            if cash_risk is not None:
                trade.cash_risk_amount = cash_risk
            if recovered.get("cash_risk_amount_source"):
                trade.cash_risk_amount_source = str(recovered.get("cash_risk_amount_source"))
            if recovered.get("cash_risk_amount_status"):
                trade.cash_risk_amount_status = str(recovered.get("cash_risk_amount_status"))

    def hydrate_vnext_dynamic_policy_from_record(
        self,
        record: dict,
        *,
        modify_broker_tp: bool = True,
        repair_recovered_sltp: bool = False,
    ) -> bool:
        """Restore vNext dynamic management onto an adopted active position."""
        if self.active_trade is None or not isinstance(record, dict):
            return False
        instrumentation = record.get("instrumentation") or {}
        if not isinstance(instrumentation, dict):
            instrumentation = {}
        execution = record.get("execution") or {}
        if not isinstance(execution, dict):
            execution = {}

        def _record_value(name: str):
            value = instrumentation.get(name)
            if value is not None:
                return value
            return execution.get(name)

        payload = {
            "gtos_vnext_dynamic_policy_selected": _record_value(
                "gtos_vnext_dynamic_policy_selected"
            ),
            "gtos_vnext_dynamic_policy_applied": _record_value(
                "gtos_vnext_dynamic_policy_applied"
            ),
            "gtos_vnext_dynamic_policy_replaced_policy": _record_value(
                "gtos_vnext_dynamic_policy_replaced_policy"
            ),
            "gtos_vnext_dynamic_policy_candidate_action": _record_value(
                "gtos_vnext_dynamic_policy_candidate_action"
            ),
            "gtos_vnext_dynamic_policy_decision_status": _record_value(
                "gtos_vnext_dynamic_policy_decision_status"
            ),
            "gtos_vnext_dynamic_policy_source_quality_action": _record_value(
                "gtos_vnext_dynamic_policy_source_quality_action"
            ),
            "gtos_vnext_dynamic_policy_exit_management_action": _record_value(
                "gtos_vnext_dynamic_policy_exit_management_action"
            ),
            "gtos_vnext_dynamic_policy_prop_action": _record_value(
                "gtos_vnext_dynamic_policy_prop_action"
            ),
            "gtos_vnext_dynamic_policy_fixed_target_role": _record_value(
                "gtos_vnext_dynamic_policy_fixed_target_role"
            ),
            "gtos_vnext_target_stop_geometry_v4": _record_value(
                "gtos_vnext_target_stop_geometry_v4"
            ),
            "gtos_vnext_execution_policy_id": _record_value(
                "gtos_vnext_execution_policy_id"
            ),
            "gtos_vnext_dynamic_be_trigger_r": _record_value(
                "gtos_vnext_dynamic_be_trigger_r"
            ),
            "gtos_vnext_dynamic_final_target_r": _record_value(
                "gtos_vnext_dynamic_final_target_r"
            ),
            "gtos_vnext_dynamic_broker_take_profit_mode": _record_value(
                "gtos_vnext_dynamic_broker_take_profit_mode"
            ),
            "gtos_vnext_dynamic_no_broker_take_profit": _record_value(
                "gtos_vnext_dynamic_no_broker_take_profit"
            ),
            "gtos_vnext_dynamic_trail_gap_r": _record_value(
                "gtos_vnext_dynamic_trail_gap_r"
            ),
            "gtos_vnext_dynamic_momentum_pullback_r": _record_value(
                "gtos_vnext_dynamic_momentum_pullback_r"
            ),
            "gtos_vnext_dynamic_time_stop_bars": _record_value(
                "gtos_vnext_dynamic_time_stop_bars"
            ),
            "gtos_vnext_book_native_exit_management": _record_value(
                "gtos_vnext_book_native_exit_management"
            ),
        }
        params = (
            self._vnext_be_after_trigger_params(payload)
            or self._vnext_partial_be_runner_params(payload)
            or self._vnext_trailing_runner_params(payload)
            or self._vnext_momentum_exhaustion_params(payload)
            or self._vnext_time_stop_params(payload)
        )
        if not params:
            return False

        trade = self.active_trade
        self._hydrate_recovered_geometry_from_record(trade, record)
        sl_distance = float(trade.sl_distance or 0.0)
        if sl_distance <= 0:
            return False

        trade.gtos_vnext_dynamic_policy_selected = payload[
            "gtos_vnext_dynamic_policy_selected"
        ]
        trade.gtos_vnext_dynamic_policy_applied = True
        trade.gtos_vnext_dynamic_policy_replaced_policy = payload[
            "gtos_vnext_dynamic_policy_replaced_policy"
        ]
        trade.gtos_vnext_dynamic_policy_candidate_action = payload[
            "gtos_vnext_dynamic_policy_candidate_action"
        ]
        trade.gtos_vnext_dynamic_policy_decision_status = payload[
            "gtos_vnext_dynamic_policy_decision_status"
        ]
        trade.gtos_vnext_dynamic_policy_source_quality_action = payload[
            "gtos_vnext_dynamic_policy_source_quality_action"
        ]
        trade.gtos_vnext_dynamic_policy_exit_management_action = payload[
            "gtos_vnext_dynamic_policy_exit_management_action"
        ]
        trade.gtos_vnext_dynamic_policy_prop_action = payload[
            "gtos_vnext_dynamic_policy_prop_action"
        ]
        trade.gtos_vnext_dynamic_policy_fixed_target_role = payload[
            "gtos_vnext_dynamic_policy_fixed_target_role"
        ]
        trade.gtos_vnext_target_stop_geometry_v4 = payload[
            "gtos_vnext_target_stop_geometry_v4"
        ]
        trade.gtos_vnext_execution_policy_id = payload["gtos_vnext_execution_policy_id"]
        # Restore the book-native exit flag so a re-adopted W7 book position keeps broker-native
        # exits across a restart (orchestrator records lack this key -> stays False, path unchanged).
        trade.gtos_vnext_book_native_exit_management = bool(
            payload.get("gtos_vnext_book_native_exit_management") or False
        )
        selected_policy = str(
            payload["gtos_vnext_dynamic_policy_selected"] or ""
        ).strip().lower()
        trade.gtos_vnext_dynamic_be_after_trigger_active = selected_policy == "be_after_trigger"
        if selected_policy == "time_stop":
            # Targetless time-stop records intentionally carry no trigger leg and
            # may have final_target_r=0 when broker TP is disabled. Rehydration
            # must still restore the policy clock so adopted positions cannot
            # degrade into passive monitoring after a restart.
            trigger_r = 0.0
            final_target_r = float(params.get("final_target_r") or 0.0)
        else:
            trigger_r = float(params["trigger_r"])
            final_target_r = float(params["final_target_r"])
        trade.gtos_vnext_dynamic_be_trigger_r = trigger_r
        trade.gtos_vnext_dynamic_final_target_r = final_target_r
        no_broker_tp = bool(params.get("no_broker_take_profit"))
        trade.gtos_vnext_dynamic_broker_take_profit_mode = (
            payload.get("gtos_vnext_dynamic_broker_take_profit_mode")
            or ("none" if no_broker_tp else "final_target")
        )
        trade.gtos_vnext_dynamic_no_broker_take_profit = no_broker_tp
        trade.gtos_vnext_dynamic_trail_gap_r = float(params.get("trail_gap_r") or 0.0)
        trade.gtos_vnext_dynamic_momentum_pullback_r = float(
            params.get("pullback_r") or 0.0
        )
        trade.gtos_vnext_dynamic_be_trigger_price = self._target_price_from_r(
            direction=trade.direction,
            entry_price=trade.entry_price,
            sl_distance=sl_distance,
            target_r=trade.gtos_vnext_dynamic_be_trigger_r,
        )
        trade.gtos_vnext_dynamic_final_target_price = (
            0.0
            if no_broker_tp
            else self._target_price_from_r(
                direction=trade.direction,
                entry_price=trade.entry_price,
                sl_distance=sl_distance,
                target_r=trade.gtos_vnext_dynamic_final_target_r,
            )
        )
        trade.gtos_vnext_dynamic_time_stop_bars = params.get("time_stop_bars")
        trade.take_profit_1 = (
            0.0
            if selected_policy == "time_stop"
            else trade.gtos_vnext_dynamic_be_trigger_price
        )
        trade.take_profit_2 = 0.0 if no_broker_tp else trade.gtos_vnext_dynamic_final_target_price
        trade.take_profit_3 = 0.0
        recovered_partial = bool(
            instrumentation.get("gtos_vnext_recovered_partial_closed")
        )
        if recovered_partial:
            self._append_recovered_partial_events_from_record(trade, record)
            trade.tp1_hit = True
            self._sync_recovered_partial_state_from_broker(trade)
        if modify_broker_tp and not no_broker_tp:
            self._modify_tp(
                trade.ticket,
                trade.gtos_vnext_dynamic_final_target_price,
                trade=trade,
                modify_reason="apply_vnext_dynamic_execution_policy_final_target",
            )
        if recovered_partial and repair_recovered_sltp:
            self._repair_recovered_partial_be_runner_sltp(trade)
        return True

    def _sync_recovered_partial_state_from_broker(self, trade: TradeState) -> None:
        positions = self.mt5.get_positions(self.symbol)
        for position in positions:
            if position.ticket != trade.ticket:
                continue
            trade.current_volume = position.volume
            if position.sl:
                trade.stop_loss = position.sl
            if position.tp:
                trade.take_profit_2 = trade.take_profit_2 or position.tp
            if trade.direction == "LONG":
                trade.sl_at_breakeven = bool(position.sl and position.sl >= trade.entry_price)
            else:
                trade.sl_at_breakeven = bool(position.sl and position.sl <= trade.entry_price)
            trade.partial_close_events.append({
                "type": "VNEXT_RECOVERED_PARTIAL_RESIDUAL_STATE",
                "time": datetime.now(timezone.utc).isoformat(),
                "ticket": trade.ticket,
                "broker_volume": position.volume,
                "broker_sl": position.sl,
                "broker_tp": position.tp,
                "tp1_hit": trade.tp1_hit,
                "sl_at_breakeven": trade.sl_at_breakeven,
            })
            return

    def _repair_recovered_partial_be_runner_sltp(self, trade: TradeState) -> None:
        if not self._vnext_partial_be_runner_active(trade):
            return
        if not trade.sl_at_breakeven:
            self._move_sl_to_breakeven(trade, trade.ticket)
        positions = self.mt5.get_positions(self.symbol)
        current_position = next((p for p in positions if p.ticket == trade.ticket), None)
        if current_position is None:
            return
        desired_tp = float(trade.take_profit_2 or 0.0)
        if desired_tp <= 0:
            return
        current_tp = float(current_position.tp or 0.0)
        tick = self._sltp_price_tick_size()
        if trade.direction == "LONG":
            desired_better_than_be = desired_tp > float(trade.entry_price or 0.0) + tick
        else:
            desired_better_than_be = desired_tp < float(trade.entry_price or 0.0) - tick
        if not desired_better_than_be:
            trade.partial_close_events.append({
                "type": "VNEXT_RECOVERED_PARTIAL_TP_REPAIR_SKIPPED",
                "time": datetime.now(timezone.utc).isoformat(),
                "reason": "desired_tp_not_beyond_entry_for_direction",
                "direction": trade.direction,
                "entry_price": trade.entry_price,
                "desired_tp": desired_tp,
                "current_tp": current_tp,
                "sl_distance": trade.sl_distance,
            })
            logger.warning(
                "Recovered partial TP repair skipped: desired TP %.5f is not "
                "beyond entry %.5f for %s",
                desired_tp,
                float(trade.entry_price or 0.0),
                trade.direction,
            )
            return
        if abs(current_tp - desired_tp) > max(tick, 1e-9):
            self._modify_tp(
                trade.ticket,
                desired_tp,
                trade=trade,
                modify_reason="recovered_partial_be_runner_final_target",
            )

    def _sltp_price_tick_size(self) -> float:
        info = self._mt5_symbol_info()
        for field in ("trade_tick_size", "point"):
            value = getattr(info, field, None) if info is not None else None
            try:
                numeric = float(value or 0.0)
            except (TypeError, ValueError):
                numeric = 0.0
            if numeric > 0:
                return numeric
        return 1e-9

    # === ORDER PLACEMENT ===

    def open_trade(self, trade_params: dict, account_balance: float,
                   risk_pct_override: float | None = None,
                   sl_distance_override: float | None = None,
                   kill_zone: str | None = None,
                   trigger: str | None = None) -> Optional[TradeState]:
        """Place a new trade. Returns TradeState if successful, None if failed.

        Args:
            trade_params: Trade parameters (direction, SL, TP, etc.)
            account_balance: Current account balance
            risk_pct_override: If set, use this risk % instead of config default
                               (used by correlation-aware position sizing)
            sl_distance_override: If set, use this SL distance as the minimum
                account-risk denominator instead of relying only on the current
                tick-to-SL distance. Used by limit fills where the market
                order can execute away from the original software limit.
            kill_zone: Optional KZ context tag forwarded to the slippage
                shadow logger ("london" / "ny" / "tokyo" / etc.). Pass None
                outside KZ context. Pure observation -- never affects
                position sizing or order placement.
            trigger: Optional free-form label describing why this trade
                fired ("candidate_market", "limit_fill_inside_kz",
                "limit_fill_outside_kz"). Forwarded to the slippage shadow
                logger only.
        """
        # Specific reason for a None return, surfaced by the order_router (open-trade-postsend-exception-
        # swallowed): the book's Telegram card otherwise showed only the opaque "open_trade_returned_none".
        self._last_open_trade_block_reason = None
        try:
            self._enforce_runtime_halt_clear(
                "open_trade",
                {
                    "direction": trade_params.get("direction"),
                    "trade_id": trade_params.get("trade_id"),
                    "candidate_id": trade_params.get("candidate_id"),
                    "trigger": trigger,
                    "kill_zone": kill_zone,
                },
            )
        except RuntimeHaltError as exc:
            diagnostic = self._record_runtime_halt_diagnostic(
                action="open_trade",
                exc=exc,
                extra={
                    "direction": trade_params.get("direction"),
                    "trigger": trigger,
                    "kill_zone": kill_zone,
                },
            )
            self._last_order_send_diagnostic = {
                "diagnostic_version": "vnext_order_send_diagnostic_v1",
                "time": diagnostic["time"],
                "symbol": self.symbol,
                "status": "runtime_halt_blocked_before_order_request",
                "request": None,
                "result": None,
                "mt5_last_error": "not_read_due_to_runtime_halt_guard",
                "positions_after": "not_read_due_to_runtime_halt_guard",
                "symbol_info": "not_read_due_to_runtime_halt_guard",
                "tick": "not_read_due_to_runtime_halt_guard",
                "error": str(exc),
                "runtime_halt_diagnostic": diagnostic,
            }
            logger.warning(
                "Open trade blocked by atomic runtime halt before broker request: %s",
                diagnostic,
            )
            self._last_open_trade_block_reason = "runtime_halt_blocked"
            return None

        direction = trade_params["direction"]
        sl = trade_params["stop_loss"]
        tp1 = trade_params["take_profit_1"]
        original_ai_tp1 = float(tp1) if tp1 else 0.0
        vnext_policy_error = self._vnext_dynamic_policy_support_error(trade_params)
        if vnext_policy_error:
            logger.error(
                "GTOS vNext dynamic execution failed closed before order: %s",
                vnext_policy_error,
            )
            self._last_open_trade_block_reason = f"vnext_policy:{vnext_policy_error}"
            return None

        tick = self.mt5.get_tick(self.symbol)
        if tick is None:
            logger.error("Cannot get tick data -- aborting trade")
            self._last_open_trade_block_reason = "no_tick_data"
            return None

        entry_price = tick.ask if direction == "LONG" else tick.bid
        # sl-no-floor-or-side-validation-vs-fresh-tick: the SL was anchored to the ROUTER tick at decision
        # time; the FRESH fill tick can have moved. If live price has crossed the SL (LONG with sl>=entry,
        # SHORT with sl<=entry) the geometry is invalid -- the order would arm a wrong-side stop / be an
        # instant stop-out, and the validated edge enters AT the signal price, not chasing a run. Reject
        # (do NOT re-anchor/chase) with a clear reason. (sl_distance_override limit fills set their own sl.)
        if not sl_distance_override and sl is not None:
            _side = 1.0 if direction == "LONG" else -1.0
            if (entry_price - float(sl)) * _side <= 0:
                logger.error("Order SL %.5f is on the WRONG side of the fresh %s entry %.5f (price moved "
                             "since the decision tick) -- aborting (no chase)", float(sl), direction, entry_price)
                self._last_open_trade_block_reason = "sl_wrong_side_vs_fresh_tick"
                return None
        sl_distance = abs(entry_price - sl)
        risk_basis_sl_distance = sl_distance
        if sl_distance_override:
            risk_basis_sl_distance = max(float(sl_distance_override), sl_distance)
        vnext_be_params = self._vnext_be_after_trigger_params(trade_params)
        vnext_partial_params = self._vnext_partial_be_runner_params(trade_params)
        vnext_trailing_params = self._vnext_trailing_runner_params(trade_params)
        vnext_momentum_params = self._vnext_momentum_exhaustion_params(trade_params)
        vnext_time_stop_params = self._vnext_time_stop_params(trade_params)
        vnext_profit_harvest_params = (
            self._vnext_profit_harvest_mfe_capture_v4_params(trade_params)
        )

        from src.components import j46_j49_policy
        j46_j49_active = j46_j49_policy.is_enabled(self.config)
        vnext_runtime_cfg = self.config.get("gtos_vnext_runtime", {}) or {}
        if (
            j46_j49_active
            and bool(vnext_runtime_cfg.get("enabled", False))
            and bool(vnext_runtime_cfg.get("apply_to_execution", False))
            and not bool(
                vnext_runtime_cfg.get(
                    "allow_legacy_j46_j49_live_execution",
                    False,
                )
            )
        ):
            logger.warning(
                "J46/J49 legacy execution disabled on active vNext production "
                "surface; dynamic policy must provide explicit live context"
            )
            j46_j49_active = False
        vnext_dynamic_policy_applied = bool(
            trade_params.get("gtos_vnext_dynamic_policy_applied")
        )
        vnext_dynamic_replaced_policy = str(
            trade_params.get("gtos_vnext_dynamic_policy_replaced_policy") or ""
        ).strip().lower()
        if (
            j46_j49_active
            and vnext_dynamic_policy_applied
            and vnext_dynamic_replaced_policy == "retired_static_baseline_comparator"
        ):
            logger.info(
                "GTOS vNext moonshot dynamic execution replaces retired static baseline: "
                "selected_policy=%s candidate_action=%s",
                trade_params.get("gtos_vnext_dynamic_policy_selected"),
                trade_params.get("gtos_vnext_dynamic_policy_candidate_action"),
            )
            j46_j49_active = False
        tp1_3r: float = 0.0
        tp2_6r: float = 0.0
        no_broker_tp = False
        if j46_j49_active and risk_basis_sl_distance > 0:
            tp1_3r, tp2_6r = j46_j49_policy.compute_targets(
                entry_price, risk_basis_sl_distance, direction, self.config,
            )
            tp1 = tp2_6r
            logger.info(
                "J46-J49 active: broker TP overridden to 6R=%.5f "
                "(software TP1 3R=%.5f, original AI TP1=%.5f)",
                tp2_6r, tp1_3r, original_ai_tp1,
            )
        elif (
            vnext_be_params
            or vnext_partial_params
            or vnext_trailing_params
            or vnext_momentum_params
            or vnext_time_stop_params
        ) and risk_basis_sl_distance > 0:
            dynamic_params = (
                vnext_be_params
                or vnext_partial_params
                or vnext_trailing_params
                or vnext_momentum_params
                or vnext_time_stop_params
            )
            if dynamic_params.get("no_broker_take_profit"):
                tp1 = 0.0
                logger.info(
                    "GTOS vNext %s live management: broker TP omitted; "
                    "native ticket-bound exit manages trail/time-stop; software trigger %.2fR",
                    trade_params.get("gtos_vnext_dynamic_policy_selected"),
                    float(dynamic_params.get("trigger_r", 0.0) or 0.0),
                )
            else:
                tp1 = self._target_price_from_r(
                    direction=direction,
                    entry_price=entry_price,
                    sl_distance=risk_basis_sl_distance,
                    target_r=float(dynamic_params["final_target_r"]),
                )
                logger.info(
                    "GTOS vNext %s live management: broker TP set "
                    "to final %.2fR=%.5f; software trigger %.2fR",
                    trade_params.get("gtos_vnext_dynamic_policy_selected"),
                    float(dynamic_params["final_target_r"]),
                    tp1,
                    float(dynamic_params.get("trigger_r", dynamic_params["final_target_r"])),
                )

        # For limit fills: use the LARGER of the original limit->SL distance
        # and the actual tick->SL distance for lot sizing.  This ensures:
        #   - Better entry (deeper in OB): sizes for original distance -> risk < 1R
        #   - Worse entry (bounced above):  sizes for actual distance  -> risk = 1R
        #   - Same entry:                   no difference
        # Never size lots for LESS distance than actual — that would over-lever.
        if sl_distance_override:
            sizing_sl_distance = risk_basis_sl_distance
            logger.info(
                "Limit fill sizing: original_sl_dist=%.5f, actual_sl_dist=%.5f, "
                "using=%.5f, entry=%.5f",
                sl_distance_override, sl_distance, sizing_sl_distance, entry_price,
            )
        else:
            sizing_sl_distance = sl_distance

        resolved_vnext_risk_pct, vnext_risk_error = self._resolve_vnext_production_risk_pct(
            trade_params,
            risk_pct_override=risk_pct_override,
        )
        if vnext_risk_error:
            logger.error(
                "GTOS vNext production execution failed closed before order: %s",
                vnext_risk_error,
            )
            self._last_open_trade_block_reason = f"vnext_risk:{vnext_risk_error}"
            return None
        risk_pct = (
            resolved_vnext_risk_pct
            if resolved_vnext_risk_pct is not None
            else self.config.get("risk", {}).get(
                "risk_per_trade_pct",
                self.config.get("risk_per_trade_pct", 1.0),
            )
        )
        if risk_pct_override is not None:
            logger.info("Position sizing: using runtime-adjusted risk %.2f%% "
                        "(default %.2f%%)", risk_pct,
                        self.config.get("risk", {}).get("risk_per_trade_pct", 1.0))
        elif self._is_vnext_production_execution_path(trade_params):
            logger.info(
                "GTOS vNext production sizing: using selected-cell risk %.4f%% "
                "for cell %s",
                risk_pct,
                trade_params.get("gtos_vnext_selected_cell_risk_cell_id"),
            )
        pretrade_cost_model, pretrade_cost_error = self._vnext_pretrade_cost_model(
            trade_params=trade_params,
            tick=tick,
            entry_price=entry_price,
            sl_distance=sizing_sl_distance,
            risk_pct=float(risk_pct),
        )
        execution_manager_v4_decision = self._evaluate_execution_manager_v4(
            trade_params=trade_params,
            pretrade_cost_model=pretrade_cost_model,
            pending_context={
                "stage": "pending_fill_market_order"
                if trade_params.get("pending_created_time_utc")
                else "market_entry",
                "pending_created_time_utc": trade_params.get("pending_created_time_utc"),
                "pending_candles_elapsed": trade_params.get("pending_candles_elapsed"),
                "pending_order_mode": trade_params.get("pending_order_mode"),
                "limit_price": trade_params.get("pending_limit_price")
                or trade_params.get("entry_price"),
            },
            trigger=trigger,
        )
        if execution_manager_v4_decision.should_block:
            block_reason = self._execution_manager_v4_block_reason(
                execution_manager_v4_decision,
                pretrade_cost_model=pretrade_cost_model,
                pretrade_cost_error=pretrade_cost_error,
            )
            logger.warning(
                "Execution Manager V4 blocked order before broker request: %s",
                block_reason,
            )
            self._last_open_trade_block_reason = block_reason
            return None
        if pretrade_cost_error:
            logger.error(
                "GTOS vNext production pre-trade cost model failed closed: %s",
                pretrade_cost_error,
            )
            self._last_open_trade_block_reason = f"pretrade_cost:{pretrade_cost_error}"
            return None
        risk_amount = account_balance * (risk_pct / 100)
        require_broker_geometry = self._vnext_requires_verified_broker_geometry(trade_params)
        sym_info = self._mt5_symbol_info()

        # Live vNext sizing must use broker PnL mechanics rather than trusting
        # symbol_info.trade_tick_value, which can be stale on broker CFDs.
        lots = self._calculate_lots(
            sizing_sl_distance,
            risk_amount,
            sym_info=sym_info,
            require_broker_geometry=require_broker_geometry,
            direction=direction,
            entry_price=entry_price,
            stop_loss=sl,
        )
        if lots is None:
            logger.error("Cannot calculate verified lot size -- aborting trade")
            self._last_open_trade_block_reason = "lot_size_unverified"
            return None
        # COMP-6 breadth-coverage: distinguish a DETERMINISTIC sub-min-lot unit (a low-conviction breadth
        # sleeve sized below the broker volume_min at this account size -- it can NEVER place and must not be
        # retried every tick) from a TRANSIENT broker volume-geometry read miss (which _normalize_volume also
        # returns None for). A distinct 'below_min_lot' reason -> the book treats it as terminal (skip once
        # per bar) + surfaces the shed breadth unit, instead of the opaque/transient lot_normalize_failed.
        if require_broker_geometry and sym_info is not None:
            try:
                _vmin = float(sym_info.volume_min)
            except (TypeError, ValueError, AttributeError):
                _vmin = None
            if _vmin is not None and _vmin > 0 and float(lots) < _vmin:
                logger.warning(
                    "vNext book unit below broker min lot -> breadth unit shed (NOT retried): "
                    "%.6f < volume_min %.6f (%s)", float(lots), _vmin, self.symbol)
                self._last_open_trade_block_reason = f"below_min_lot:{float(lots):.4f}<{_vmin:.4f}"
                return None
        lots = self._normalize_volume(
            lots,
            sym_info,
            require_broker_geometry=require_broker_geometry,
        )
        if lots is None:
            # only the geometry-read miss reaches here now (sub-min handled above) -> TRANSIENT.
            if self._last_open_trade_block_reason is None:
                self._last_open_trade_block_reason = "lot_normalize_failed"
            return None
        pre_send_cash_risk_amount = self._broker_cash_risk_amount(
            direction=direction,
            volume=lots,
            entry_price=entry_price,
            stop_loss=sl,
        )
        if require_broker_geometry and pre_send_cash_risk_amount is None:
            logger.error(
                "Cannot verify normalized vNext lot cash risk with broker "
                "order_calc_profit -- aborting trade"
            )
            self._last_open_trade_block_reason = "cash_risk_unverified"
            return None
        type_filling = self._order_filling_mode(
            sym_info,
            require_broker_geometry=require_broker_geometry,
        )
        if type_filling is None:
            self._last_open_trade_block_reason = "filling_mode_unresolved"
            return None
        deviation_points = self._order_deviation_points(
            sym_info,
            trade_params,
            require_broker_geometry=require_broker_geometry,
        )
        if deviation_points is None:
            self._last_open_trade_block_reason = "deviation_unresolved"
            return None

        order_type = 0 if direction == "LONG" else 1
        # Traceable broker comment for W7 book trades (sleeve identity). FTMO-Server3 truncates to ~16.
        _sed = trade_params.get("gtos_vnext_source_event_details") or {}
        _sleeve = _sed.get("sleeve")
        if _sleeve:
            order_comment = f"W7:{_sleeve}"[:16]
        else:
            # FAIL-LOUD W7 tag, NOT the retired 'GoldAgent_OBRetest' name (owner mandate: zero
            # old-system residue on a live order). A book order should ALWAYS carry its sleeve; an
            # empty sleeve is a wiring defect to surface, not a legacy-tagged trade.
            order_comment = "W7:UNTAGGED"
            logging.getLogger(__name__).warning(
                "W7 book order missing source_event_details.sleeve -> comment 'W7:UNTAGGED' "
                "(symbol=%s); investigate the missing sleeve tag.", self.symbol)
        request = {
            "action": 1,  # TRADE_ACTION_DEAL
            "symbol": self.symbol,
            "volume": lots,
            "type": order_type,
            "price": entry_price,
            "sl": sl,
            "tp": tp1,
            "deviation": deviation_points,
            "magic": MAGIC_NUMBER,
            "comment": order_comment,
            "type_time": 0,  # ORDER_TIME_GTC
            "type_filling": type_filling,
        }

        order_send_time = datetime.now(timezone.utc)
        pre_send_lifecycle_packet = build_broker_order_lifecycle_capture_v4(
            stage="pre_send",
            trade_params=trade_params,
            symbol=self._persist_symbol,
            broker_symbol=self.symbol,
            order_request=request,
            pretrade_cost_model=pretrade_cost_model,
            execution_manager_packet=trade_params.get(
                "gtos_vnext_execution_manager_v4_packet"
            ),
            order_send_time_utc=order_send_time.isoformat(),
        )
        try:
            record_broker_order_lifecycle_capture_v4(
                pre_send_lifecycle_packet,
                config=self.config,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Broker lifecycle V4 pre-send logging failed (non-blocking): %s",
                exc,
            )
        result = self.safe_place_order(request)
        order_result_time = datetime.now(timezone.utc)
        order_latency_ms = round(
            (order_result_time - order_send_time).total_seconds() * 1000.0,
            3,
        )
        pending_age_seconds = None
        pending_created_time = trade_params.get("pending_created_time_utc")
        if pending_created_time:
            try:
                pending_created_dt = datetime.fromisoformat(
                    str(pending_created_time).replace("Z", "+00:00")
                )
                if pending_created_dt.tzinfo is None:
                    pending_created_dt = pending_created_dt.replace(tzinfo=timezone.utc)
                pending_age_seconds = max(
                    0.0,
                    (order_send_time - pending_created_dt.astimezone(timezone.utc)).total_seconds(),
                )
            except (TypeError, ValueError):
                pending_age_seconds = None

        if result is None or not result.success:
            reason = result.comment if result else "timeout_no_fill"
            logger.error(f"Order failed: {reason}")
            self._last_open_trade_block_reason = f"order_rejected:{reason}"
            rejected_lifecycle_packet = build_broker_order_lifecycle_capture_v4(
                stage="order_send_result",
                trade_params=trade_params,
                symbol=self._persist_symbol,
                broker_symbol=self.symbol,
                order_request=request,
                order_result=result,
                pretrade_cost_model=pretrade_cost_model,
                execution_manager_packet=trade_params.get(
                    "gtos_vnext_execution_manager_v4_packet"
                ),
                order_send_time_utc=order_send_time.isoformat(),
                order_result_time_utc=order_result_time.isoformat(),
            )
            trade_params[
                "gtos_vnext_broker_order_lifecycle_capture_v4_packet"
            ] = rejected_lifecycle_packet
            try:
                record_broker_order_lifecycle_capture_v4(
                    rejected_lifecycle_packet,
                    config=self.config,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Broker lifecycle V4 rejected-order logging failed "
                    "(non-blocking): %s",
                    exc,
                )
            try:
                spread_value = (
                    getattr(tick, "spread_cents", None) if tick is not None else None
                )
                record_slippage(
                    namespace=self._runtime_namespace,
                    candidate_id=trade_params.get("candidate_id"),
                    ticket=getattr(result, "order", 0) if result is not None else 0,
                    symbol=self._persist_symbol,
                    direction=direction,
                    requested_price=entry_price,
                    fill_price=getattr(result, "price", 0.0) if result is not None else 0.0,
                    spread_at_request=spread_value,
                    kill_zone=kill_zone,
                    trigger=trigger,
                    notes=reason,
                    deal_ticket=getattr(result, "deal", None) if result is not None else None,
                    executed_entry_price=None,
                    executed_stop_price=sl,
                    executed_target_price=tp1,
                    executed_lot_size=lots,
                    source_repair_identity=trade_params.get("source_repair_identity"),
                    decision_spread=trade_params.get("decision_spread_value_source_safe")
                    or trade_params.get("decision_spread"),
                    decision_spread_unit=trade_params.get("decision_spread_unit"),
                    order_send_spread=spread_value,
                    fill_spread=None,
                    fill_spread_status="NOT_APPLICABLE_ORDER_NOT_FILLED",
                    order_send_time_utc=order_send_time.isoformat(),
                    order_result_time_utc=order_result_time.isoformat(),
                    reject_or_fill_latency_ms=order_latency_ms,
                    pending_age_seconds=pending_age_seconds,
                    pending_candles_elapsed=trade_params.get("pending_candles_elapsed"),
                    sl_distance=sl_distance,
                    order_outcome_status="ORDER_REJECTED_OR_TIMEOUT",
                    dynamic_policy=trade_params.get("gtos_vnext_dynamic_policy_selected"),
                    pretrade_cost_model=pretrade_cost_model or None,
                    pretrade_cost_model_status=(
                        (pretrade_cost_model or {}).get("status")
                        if pretrade_cost_model else None
                    ),
                    dynamic_exit_action_timeline={
                        "stage": "entry_order_send",
                        "status": "order_not_filled",
                        "reason": reason,
                        "policy": trade_params.get("gtos_vnext_dynamic_policy_selected"),
                        "execution_policy_id": trade_params.get(
                            "gtos_vnext_execution_policy_id"
                        ),
                    },
                )
            except Exception as e:
                logger.warning(
                    "Rejected-order slippage telemetry failed (non-blocking): %s", e,
                )
            self._notify_vnext_lifecycle(
                trade_params,
                "rejected order",
                direction=direction,
                price=entry_price,
                detail=reason,
            )
            return None

        entry_deal_accounting = self._lookup_entry_deal_accounting(
            result,
            order_send_time=order_send_time,
            order_result_time=order_result_time,
        )
        entry_ticket = self._recover_entry_ticket_after_fill(result, entry_deal_accounting)
        if entry_ticket is None:
            reason = "missing_positive_entry_ticket_after_fill"
            logger.error(
                "Order filled but no positive entry ticket could be recovered for %s; refusing unmanaged TradeState",
                self.symbol,
            )
            self._last_open_trade_block_reason = f"lifecycle_error:{reason}"
            return None
        order_result_fill_price = self._positive_float(getattr(result, "price", None))
        tick_fallback_fill_price = float(entry_price)
        filled_price = order_result_fill_price or tick_fallback_fill_price
        fill_price_source = (
            "order_result_price"
            if order_result_fill_price is not None
            else "executed_entry_price_fallback_for_zero_order_result"
        )
        fill_price_status = (
            "CAPTURED"
            if order_result_fill_price is not None
            else "ZERO_ORDER_RESULT_REPAIRED"
        )
        broker_history_fill_price = self._positive_float(
            entry_deal_accounting.get("broker_entry_price")
        )
        if (
            broker_history_fill_price is not None
            and entry_deal_accounting.get("account_history_lookup_status")
            == "RECONCILED_FROM_ACCOUNT_HISTORY"
        ):
            fallback_price = filled_price
            filled_price = broker_history_fill_price
            fill_price_source = "broker_entry_deal_history"
            fill_price_status = "BROKER_HISTORY_RECONCILED"
            if abs(filled_price - fallback_price) > 1e-9:
                logger.info(
                    "MT5 entry deal price %.5f overrides order result/tick fill %.5f for %s order=%s deal=%s",
                    filled_price,
                    fallback_price,
                    self.symbol,
                    getattr(result, "order", None),
                    getattr(result, "deal", None),
                )
        elif order_result_fill_price is None:
            logger.warning(
                "MT5 result.price=%s -- using tick entry_price=%.5f until broker history resolves",
                getattr(result, "price", None),
                tick_fallback_fill_price,
            )

        actual_cash_risk_amount = self._broker_cash_risk_amount(
            direction=direction,
            volume=lots,
            entry_price=filled_price,
            stop_loss=sl,
        )
        if actual_cash_risk_amount is not None:
            cash_risk_amount = actual_cash_risk_amount
            cash_risk_amount_source = "broker_order_calc_profit_filled_price_to_stop"
            cash_risk_amount_status = "BROKER_ORDER_CALC_PROFIT_VERIFIED"
        elif pre_send_cash_risk_amount is not None:
            cash_risk_amount = pre_send_cash_risk_amount
            cash_risk_amount_source = "broker_order_calc_profit_pre_send_price_to_stop"
            cash_risk_amount_status = "BROKER_ORDER_CALC_PROFIT_PRE_SEND_ONLY"
        else:
            cash_risk_amount = risk_amount
            cash_risk_amount_source = "intended_risk_budget_unverified"
            cash_risk_amount_status = "BROKER_ORDER_CALC_PROFIT_UNAVAILABLE"
        broker_cash_risk_per_lot = (
            cash_risk_amount / lots
            if lots and cash_risk_amount is not None
            else 0.0
        )

        if j46_j49_active and risk_basis_sl_distance > 0:
            ts_tp1 = tp1_3r
            ts_tp2 = tp2_6r
            ts_tp3 = 0.0
            state_sl_distance = risk_basis_sl_distance
            dynamic_be_active = False
            dynamic_be_trigger_r = 0.0
            dynamic_final_target_r = 0.0
            dynamic_be_trigger_price = 0.0
            dynamic_final_target_price = 0.0
            dynamic_trail_gap_r = 0.0
            dynamic_momentum_pullback_r = 0.0
            dynamic_time_stop_bars = None
            profit_harvest_params = None
        elif (
            vnext_be_params
            or vnext_partial_params
            or vnext_trailing_params
            or vnext_momentum_params
            or vnext_time_stop_params
        ) and risk_basis_sl_distance > 0:
            dynamic_params = (
                vnext_be_params
                or vnext_partial_params
                or vnext_trailing_params
                or vnext_momentum_params
                or vnext_time_stop_params
            )
            no_broker_tp = bool(dynamic_params.get("no_broker_take_profit"))
            targetless_time_stop = no_broker_tp and bool(vnext_time_stop_params)
            state_sl_distance = risk_basis_sl_distance
            dynamic_be_trigger_r = float(dynamic_params.get("trigger_r", dynamic_params["final_target_r"]))
            dynamic_final_target_r = float(dynamic_params["final_target_r"])
            dynamic_be_trigger_price = self._target_price_from_r(
                direction=direction,
                entry_price=filled_price,
                sl_distance=state_sl_distance,
                target_r=dynamic_be_trigger_r,
            )
            dynamic_final_target_price = (
                0.0
                if no_broker_tp
                else self._target_price_from_r(
                    direction=direction,
                    entry_price=filled_price,
                    sl_distance=state_sl_distance,
                    target_r=dynamic_final_target_r,
                )
            )
            ts_tp1 = 0.0 if targetless_time_stop else dynamic_be_trigger_price
            ts_tp2 = 0.0 if no_broker_tp else dynamic_final_target_price
            ts_tp3 = 0.0
            dynamic_be_active = bool(vnext_be_params)
            dynamic_trail_gap_r = float(dynamic_params.get("trail_gap_r") or 0.0)
            dynamic_momentum_pullback_r = float(dynamic_params.get("pullback_r") or 0.0)
            dynamic_time_stop_bars = dynamic_params.get("time_stop_bars")
            profit_harvest_params = vnext_profit_harvest_params
            if (
                not no_broker_tp
                and abs(dynamic_final_target_price - float(tp1 or 0.0)) > 1e-9
            ):
                self._modify_tp(
                    entry_ticket,
                    dynamic_final_target_price,
                    identity_direction=direction,
                    identity_trade_id=trade_params.get("trade_id"),
                )
        else:
            ts_tp1 = float(tp1) if tp1 else 0.0
            ts_tp2 = float(trade_params.get("take_profit_2", 0) or 0.0)
            ts_tp3 = float(trade_params.get("take_profit_3", 0) or 0.0)
            state_sl_distance = risk_basis_sl_distance
            dynamic_be_active = False
            dynamic_be_trigger_r = 0.0
            dynamic_final_target_r = 0.0
            dynamic_be_trigger_price = 0.0
            dynamic_final_target_price = 0.0
            dynamic_trail_gap_r = 0.0
            dynamic_momentum_pullback_r = 0.0
            dynamic_time_stop_bars = None
            profit_harvest_params = vnext_profit_harvest_params

        target_stop_geometry_v4 = build_target_stop_geometry_v4_contract(
            config=self.config,
            selected_policy=trade_params.get("gtos_vnext_dynamic_policy_selected"),
            execution_policy_id=trade_params.get("gtos_vnext_execution_policy_id"),
            source_event=trade_params.get("gtos_vnext_source_event_details") or {},
            trade_params=trade_params,
            prior_contract=trade_params.get("gtos_vnext_target_stop_geometry_v4"),
            entry_price=filled_price,
            stop_loss=sl,
            direction=direction,
            risk_distance=state_sl_distance,
            trigger_r=dynamic_be_trigger_r or None,
            final_target_r=None if no_broker_tp else dynamic_final_target_r or None,
            trigger_price=dynamic_be_trigger_price or None,
            final_target_price=None if no_broker_tp else dynamic_final_target_price or tp1,
            stage="execution_entry_fill",
        )

        self.active_trade = TradeState(
            ticket=entry_ticket,
            direction=direction,
            entry_price=filled_price,
            stop_loss=sl,
            take_profit_1=ts_tp1,
            take_profit_2=ts_tp2,
            take_profit_3=ts_tp3,
            initial_volume=lots,
            current_volume=lots,
            sl_distance=state_sl_distance,
            trade_id=(
                f"tr_{self._runtime_namespace or 'unknown_ns'}_"
                f"{self._persist_symbol}_{entry_ticket or result.order or int(time.time() * 1000)}"
            ),
            entry_time=datetime.now(timezone.utc).isoformat(),
            original_ai_tp1=original_ai_tp1,
            j46_j49_active=bool(j46_j49_active and risk_basis_sl_distance > 0),
            entry_order_ticket=entry_ticket,
            entry_deal_ticket=(
                getattr(result, "deal", None)
                if getattr(result, "deal", None) not in (0, "0")
                else None
            ),
            entry_order_retcode=result.retcode,
            source_repair_identity=trade_params.get("source_repair_identity"),
            gtos_vnext_source_event_hash=trade_params.get(
                "gtos_vnext_source_event_hash"
            ),
            gtos_vnext_source_event_details=trade_params.get(
                "gtos_vnext_source_event_details"
            ),
            gtos_vnext_activation_family=trade_params.get(
                "gtos_vnext_activation_family"
            ),
            gtos_vnext_origin_family=trade_params.get("gtos_vnext_origin_family"),
            gtos_vnext_selector_row_id=trade_params.get(
                "gtos_vnext_selector_row_id"
            ),
            gtos_vnext_selector_proof_hash=trade_params.get(
                "gtos_vnext_selector_proof_hash"
            ),
            gtos_vnext_execution_policy_id=trade_params.get(
                "gtos_vnext_execution_policy_id"
            ),
            gtos_vnext_dynamic_policy_selected=trade_params.get(
                "gtos_vnext_dynamic_policy_selected"
            ),
            gtos_vnext_dynamic_policy_applied=vnext_dynamic_policy_applied,
            gtos_vnext_dynamic_policy_replaced_policy=trade_params.get(
                "gtos_vnext_dynamic_policy_replaced_policy"
            ),
            gtos_vnext_dynamic_policy_candidate_action=trade_params.get(
                "gtos_vnext_dynamic_policy_candidate_action"
            ),
            gtos_vnext_dynamic_policy_decision_status=trade_params.get(
                "gtos_vnext_dynamic_policy_decision_status"
            ),
            gtos_vnext_dynamic_policy_source_quality_action=trade_params.get(
                "gtos_vnext_dynamic_policy_source_quality_action"
            ),
            gtos_vnext_dynamic_policy_exit_management_action=trade_params.get(
                "gtos_vnext_dynamic_policy_exit_management_action"
            ),
            gtos_vnext_dynamic_policy_prop_action=trade_params.get(
                "gtos_vnext_dynamic_policy_prop_action"
            ),
            gtos_vnext_dynamic_policy_fixed_target_role=trade_params.get(
                "gtos_vnext_dynamic_policy_fixed_target_role"
            ),
            gtos_vnext_target_stop_geometry_v4=target_stop_geometry_v4,
            gtos_vnext_selected_cell_risk_pct=trade_params.get(
                "gtos_vnext_selected_cell_risk_pct"
            ),
            gtos_vnext_selected_cell_risk_cell_id=trade_params.get(
                "gtos_vnext_selected_cell_risk_cell_id"
            ),
            gtos_vnext_selected_cell_risk_decision_basis=trade_params.get(
                "gtos_vnext_selected_cell_risk_decision_basis"
            ),
            gtos_vnext_selected_cell_risk_selected_policy=trade_params.get(
                "gtos_vnext_selected_cell_risk_selected_policy"
            ),
            gtos_vnext_selected_cell_risk_source_policy=trade_params.get(
                "gtos_vnext_selected_cell_risk_source_policy"
            ),
            gtos_vnext_selected_cell_risk_policy_identity_status=trade_params.get(
                "gtos_vnext_selected_cell_risk_policy_identity_status"
            ),
            gtos_vnext_dynamic_be_after_trigger_active=dynamic_be_active,
            gtos_vnext_dynamic_be_trigger_r=dynamic_be_trigger_r,
            gtos_vnext_dynamic_final_target_r=dynamic_final_target_r,
            gtos_vnext_dynamic_broker_take_profit_mode=trade_params.get(
                "gtos_vnext_dynamic_broker_take_profit_mode"
            ),
            gtos_vnext_dynamic_no_broker_take_profit=bool(
                trade_params.get("gtos_vnext_dynamic_no_broker_take_profit", False)
            ),
            gtos_vnext_dynamic_be_trigger_price=dynamic_be_trigger_price,
            gtos_vnext_dynamic_final_target_price=dynamic_final_target_price,
            gtos_vnext_dynamic_placement_be_trigger_price=(
                self._safe_float(
                    trade_params.get("gtos_vnext_dynamic_be_trigger_price")
                )
                or 0.0
            ),
            gtos_vnext_dynamic_placement_final_target_price=(
                self._safe_float(
                    trade_params.get("gtos_vnext_dynamic_final_target_price")
                )
                or 0.0
            ),
            gtos_vnext_dynamic_trail_gap_r=dynamic_trail_gap_r,
            gtos_vnext_dynamic_momentum_pullback_r=dynamic_momentum_pullback_r,
            gtos_vnext_dynamic_time_stop_bars=dynamic_time_stop_bars,
            gtos_vnext_execution_manager_v4_status=trade_params.get(
                "gtos_vnext_execution_manager_v4_status"
            ),
            gtos_vnext_execution_manager_v4_action=trade_params.get(
                "gtos_vnext_execution_manager_v4_action"
            ),
            gtos_vnext_execution_manager_v4_fatal_reasons=list(
                trade_params.get("gtos_vnext_execution_manager_v4_fatal_reasons")
                or []
            ),
            gtos_vnext_execution_manager_v4_warning_reasons=list(
                trade_params.get("gtos_vnext_execution_manager_v4_warning_reasons")
                or []
            ),
            gtos_vnext_execution_manager_v4_packet=trade_params.get(
                "gtos_vnext_execution_manager_v4_packet"
            ),
            gtos_vnext_broker_order_lifecycle_capture_v4_packet=None,
            gtos_vnext_prop_firm_headroom_snapshot_v4=trade_params.get(
                "gtos_vnext_prop_firm_headroom_snapshot_v4"
            ),
            gtos_vnext_prop_firm_headroom_v4_packet=trade_params.get(
                "gtos_vnext_prop_firm_headroom_v4_packet"
            ),
            gtos_vnext_profit_harvest_mfe_capture_v4_enabled=bool(
                profit_harvest_params
            ),
            gtos_vnext_profit_harvest_min_mfe_r=float(
                (profit_harvest_params or {}).get("min_mfe_r") or 0.0
            ),
            gtos_vnext_profit_harvest_trail_gap_r=float(
                (profit_harvest_params or {}).get("trail_gap_r") or 0.0
            ),
            gtos_vnext_profit_harvest_protect_floor_r=float(
                (profit_harvest_params or {}).get("protect_floor_r") or 0.0
            ),
            gtos_vnext_profit_harvest_close_on_giveback_r=float(
                (profit_harvest_params or {}).get("close_on_giveback_r") or 0.0
            ),
            gtos_vnext_profit_harvest_stale_minutes=(
                (profit_harvest_params or {}).get("stale_minutes")
            ),
            gtos_vnext_profit_harvest_stale_min_mfe_r=float(
                (profit_harvest_params or {}).get("stale_min_mfe_r") or 0.0
            ),
            gtos_vnext_profit_harvest_stale_close_below_r=float(
                (profit_harvest_params or {}).get("stale_close_below_r") or 0.0
            ),
            account_balance_at_entry=float(account_balance or 0.0),
            risk_pct_at_entry=float(risk_pct or 0.0),
            cash_risk_amount=float(cash_risk_amount or 0.0),
            cash_risk_amount_source=cash_risk_amount_source,
            cash_risk_amount_status=cash_risk_amount_status,
            broker_cash_risk_per_lot=float(broker_cash_risk_per_lot or 0.0),
            broker_lot_sizing_diagnostic=dict(self._last_lot_sizing_diagnostic or {}),
            gtos_vnext_pretrade_cost_model=dict(pretrade_cost_model or {}),
            gtos_vnext_book_native_exit_management=bool(
                trade_params.get("gtos_vnext_book_native_exit_management", False)
            ),
        )
        self._known_tickets.add(entry_ticket)
        filled_lifecycle_packet = build_broker_order_lifecycle_capture_v4(
            stage="entry_fill_reconciled",
            trade_params=trade_params,
            symbol=self._persist_symbol,
            broker_symbol=self.symbol,
            order_request=request,
            order_result=result,
            entry_deal_accounting=entry_deal_accounting,
            trade_state=self.active_trade,
            pretrade_cost_model=pretrade_cost_model,
            execution_manager_packet=trade_params.get(
                "gtos_vnext_execution_manager_v4_packet"
            ),
            order_send_time_utc=order_send_time.isoformat(),
            order_result_time_utc=order_result_time.isoformat(),
        )
        trade_params[
            "gtos_vnext_broker_order_lifecycle_capture_v4_packet"
        ] = filled_lifecycle_packet
        self.active_trade.gtos_vnext_broker_order_lifecycle_capture_v4_packet = (
            filled_lifecycle_packet
        )
        try:
            record_broker_order_lifecycle_capture_v4(
                filled_lifecycle_packet,
                config=self.config,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Broker lifecycle V4 filled-order logging failed (non-blocking): %s",
                exc,
            )
        try:
            record_same_symbol_lifecycle_entry_v4(
                config=self.config,
                ticket=entry_ticket,
                symbol=self._persist_symbol,
                side=direction,
                trade_params=trade_params,
                trade_state=self.active_trade,
                lifecycle_packet=trade_params.get(
                    "gtos_vnext_same_symbol_lifecycle_v4_packet"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Same-symbol lifecycle V4 durable ticket store write failed "
                "(non-blocking): %s",
                exc,
            )

        # Slippage shadow logger (Q71). Closes the requested-vs-fill data gap
        # so downstream slippage modelling has a real source. Fail-open: any
        # error inside record_slippage is caught + downgraded to a warning;
        # trade execution must NOT depend on this write succeeding.
        # Order-send spread is sourced from the TickData captured at the top
        # of open_trade; fill spread is best-effort from a post-result tick.
        try:
            spread_value = (
                getattr(tick, "spread_cents", None) if tick is not None else None
            )
            fill_spread_value = None
            try:
                fill_tick = self.mt5.get_tick(self.symbol)
                fill_spread_value = (
                    getattr(fill_tick, "spread_cents", None)
                    if fill_tick is not None else None
                )
            except Exception:
                fill_spread_value = None
            comment_note = (
                getattr(result, "comment", None)
                if getattr(result, "comment", None) else None
            )
            record_slippage(
                namespace=self._runtime_namespace,
                candidate_id=trade_params.get("candidate_id"),
                ticket=entry_ticket,
                symbol=self._persist_symbol,
                direction=direction,
                requested_price=entry_price,
                fill_price=filled_price,
                spread_at_request=spread_value,
                kill_zone=kill_zone,
                trigger=trigger,
                notes=comment_note,
                deal_ticket=entry_deal_accounting.get("deal_ticket"),
                raw_order_result_fill_price=result.price,
                broker_fill_time_utc=entry_deal_accounting.get("broker_fill_time_utc"),
                executed_entry_price=filled_price,
                executed_stop_price=sl,
                executed_target_price=tp1,
                executed_lot_size=lots,
                commission=entry_deal_accounting.get("commission"),
                swap=entry_deal_accounting.get("swap"),
                cash_risk_amount=cash_risk_amount,
                source_repair_identity=trade_params.get("source_repair_identity"),
                decision_spread=trade_params.get("decision_spread_value_source_safe")
                or trade_params.get("decision_spread"),
                decision_spread_unit=trade_params.get("decision_spread_unit"),
                order_send_spread=spread_value,
                fill_spread=fill_spread_value,
                order_send_time_utc=order_send_time.isoformat(),
                order_result_time_utc=order_result_time.isoformat(),
                reject_or_fill_latency_ms=order_latency_ms,
                pending_age_seconds=pending_age_seconds,
                pending_candles_elapsed=trade_params.get("pending_candles_elapsed"),
                sl_distance=state_sl_distance,
                order_outcome_status="ORDER_FILLED",
                dynamic_policy=trade_params.get("gtos_vnext_dynamic_policy_selected"),
                commission_status=entry_deal_accounting.get("account_history_lookup_status"),
                swap_status=entry_deal_accounting.get("account_history_lookup_status"),
                account_history_lookup_status=entry_deal_accounting.get(
                    "account_history_lookup_status"
                ),
                account_history_lookup_attempted=entry_deal_accounting.get(
                    "account_history_lookup_attempted"
                ),
                account_history_lookup_attempt_count=entry_deal_accounting.get(
                    "account_history_lookup_attempt_count"
                ),
                account_history_lookup_window_start_utc=entry_deal_accounting.get(
                    "account_history_lookup_window_start_utc"
                ),
                account_history_lookup_window_end_utc=entry_deal_accounting.get(
                    "account_history_lookup_window_end_utc"
                ),
                account_history_lookup_error=entry_deal_accounting.get(
                    "account_history_lookup_error"
                ),
                account_history_lookup_match_keys=entry_deal_accounting.get(
                    "account_history_lookup_match_keys"
                ),
                account_history_lookup_recovery_attempted=entry_deal_accounting.get(
                    "account_history_lookup_recovery_attempted"
                ),
                account_history_lookup_recovery_window_start_utc=entry_deal_accounting.get(
                    "account_history_lookup_recovery_window_start_utc"
                ),
                account_history_lookup_recovery_window_end_utc=entry_deal_accounting.get(
                    "account_history_lookup_recovery_window_end_utc"
                ),
                account_history_lookup_recovery_error=entry_deal_accounting.get(
                    "account_history_lookup_recovery_error"
                ),
                broker_fill_time_alignment_offset_seconds=entry_deal_accounting.get(
                    "broker_fill_time_alignment_offset_seconds"
                ),
                fill_price_source_override=fill_price_source,
                fill_price_status_override=fill_price_status,
                pretrade_cost_model=pretrade_cost_model or None,
                pretrade_cost_model_status=(
                    (pretrade_cost_model or {}).get("status")
                    if pretrade_cost_model else None
                ),
                dynamic_exit_action_timeline={
                    "stage": "entry_order_fill",
                    "status": "order_filled",
                    "policy": trade_params.get("gtos_vnext_dynamic_policy_selected"),
                    "execution_policy_id": trade_params.get(
                        "gtos_vnext_execution_policy_id"
                    ),
                    "be_trigger_r": dynamic_be_trigger_r,
                    "final_target_r": dynamic_final_target_r,
                    "be_trigger_price": dynamic_be_trigger_price,
                    "final_target_price": dynamic_final_target_price,
                    "profit_harvest_mfe_capture_v4": profit_harvest_params or None,
                    "cash_risk_amount_source": cash_risk_amount_source,
                    "cash_risk_amount_status": cash_risk_amount_status,
                    "broker_cash_risk_per_lot": broker_cash_risk_per_lot,
                    "lot_sizing_diagnostic": self._last_lot_sizing_diagnostic,
                },
            )
        except Exception as e:
            # Belt-and-suspenders: record_slippage already swallows its own
            # errors, but the outer try ensures even a programmer-error in
            # this wire-in (e.g. attribute typo) cannot block trade flow.
            logger.warning(
                "Slippage shadow logger wire-in failed (non-blocking): %s", e,
            )

        logger.info(f"Trade opened: {self.active_trade.trade_id} "
                     f"{direction} {lots} lots at {filled_price}, SL={sl}, TP1={tp1}")
        return self.active_trade

    def set_limit_intent(
        self,
        trade_params: dict,
        account_balance: float,
        risk_pct_override: float | None = None,
        telemetry_context: Optional[dict] = None,
    ) -> Optional[PendingLimitIntent]:
        """Store a limit order intent. Orchestrator checks each candle for fill."""
        telemetry_context = telemetry_context or {}
        try:
            self._enforce_runtime_halt_clear(
                "set_limit_intent",
                {
                    "direction": trade_params.get("direction"),
                    "entry_price": trade_params.get("entry_price"),
                    "candidate_id": trade_params.get("candidate_id"),
                    "record_path": telemetry_context.get("record_path"),
                },
            )
        except RuntimeHaltError as exc:
            diagnostic = self._record_runtime_halt_diagnostic(
                action="set_limit_intent",
                exc=exc,
                extra={
                    "direction": trade_params.get("direction"),
                    "entry_price": trade_params.get("entry_price"),
                    "record_path": telemetry_context.get("record_path"),
                },
            )
            logger.warning(
                "Pending limit intent blocked by atomic runtime halt: %s",
                diagnostic,
            )
            return None

        decision_spread_value = telemetry_context.get("decision_spread_value_source_safe")
        if decision_spread_value is None:
            decision_spread_value = telemetry_context.get("decision_spread")
        decision_spread_unit = telemetry_context.get("decision_spread_unit")
        if decision_spread_unit is None and decision_spread_value is not None:
            decision_spread_unit = "spread_cents"
        risk_pct = (
            risk_pct_override
            if risk_pct_override is not None
            else self.config.get("risk", {}).get("risk_per_trade_pct", 1.0)
        )
        now_utc = datetime.now(timezone.utc)
        dynamic_selected_policy = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_policy_selected",
        )
        dynamic_applied = bool(
            self._context_value(
                telemetry_context,
                trade_params,
                "gtos_vnext_dynamic_policy_applied",
            )
        )
        configured_be = self._configured_vnext_be_after_trigger_params()
        configured_partial = self._configured_vnext_partial_be_runner_params()
        configured_trailing = self._configured_vnext_trailing_runner_params()
        configured_momentum = self._configured_vnext_momentum_exhaustion_params()
        configured_time_stop = self._configured_vnext_time_stop_params()
        configured_profit_harvest = (
            self._configured_vnext_profit_harvest_mfe_capture_v4_params()
        )
        dynamic_be_trigger_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_be_trigger_r",
        )
        dynamic_final_target_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_final_target_r",
        )
        dynamic_time_stop_bars = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_time_stop_bars",
        )
        dynamic_trail_gap_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_trail_gap_r",
        )
        dynamic_momentum_pullback_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_momentum_pullback_r",
        )
        profit_harvest_enabled = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_mfe_capture_v4_enabled",
        )
        if profit_harvest_enabled in (None, ""):
            profit_harvest_enabled = configured_profit_harvest["enabled"]
        profit_harvest_min_mfe_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_min_mfe_r",
        )
        if profit_harvest_min_mfe_r in (None, ""):
            profit_harvest_min_mfe_r = configured_profit_harvest["min_mfe_r"]
        profit_harvest_trail_gap_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_trail_gap_r",
        )
        if profit_harvest_trail_gap_r in (None, ""):
            profit_harvest_trail_gap_r = configured_profit_harvest["trail_gap_r"]
        profit_harvest_protect_floor_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_protect_floor_r",
        )
        if profit_harvest_protect_floor_r in (None, ""):
            profit_harvest_protect_floor_r = configured_profit_harvest["protect_floor_r"]
        profit_harvest_close_on_giveback_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_close_on_giveback_r",
        )
        if profit_harvest_close_on_giveback_r in (None, ""):
            profit_harvest_close_on_giveback_r = configured_profit_harvest[
                "close_on_giveback_r"
            ]
        profit_harvest_stale_minutes = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_stale_minutes",
        )
        if profit_harvest_stale_minutes in (None, ""):
            profit_harvest_stale_minutes = configured_profit_harvest["stale_minutes"]
        profit_harvest_stale_min_mfe_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_stale_min_mfe_r",
        )
        if profit_harvest_stale_min_mfe_r in (None, ""):
            profit_harvest_stale_min_mfe_r = configured_profit_harvest["stale_min_mfe_r"]
        profit_harvest_stale_close_below_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_stale_close_below_r",
        )
        if profit_harvest_stale_close_below_r in (None, ""):
            profit_harvest_stale_close_below_r = configured_profit_harvest[
                "stale_close_below_r"
            ]
        if (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "be_after_trigger"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_be["trigger_r"]
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_be["final_target_r"]
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_be["time_stop_bars"]
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "partial_be_runner"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_partial["trigger_r"]
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_partial["final_target_r"]
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_partial["time_stop_bars"]
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "trailing_runner"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_trailing["trigger_r"]
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_trailing["final_target_r"]
            if dynamic_trail_gap_r in (None, ""):
                dynamic_trail_gap_r = configured_trailing["trail_gap_r"]
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_trailing["time_stop_bars"]
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "momentum_exhaustion"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_momentum["trigger_r"]
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_momentum["final_target_r"]
            if dynamic_momentum_pullback_r in (None, ""):
                dynamic_momentum_pullback_r = configured_momentum["pullback_r"]
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_momentum["time_stop_bars"]
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "time_stop"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_time_stop["final_target_r"]
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_time_stop["final_target_r"]
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_time_stop["time_stop_bars"]

        dynamic_be_trigger_r = self._safe_float(dynamic_be_trigger_r)
        dynamic_final_target_r = self._safe_float(dynamic_final_target_r)
        dynamic_trail_gap_r = self._safe_float(dynamic_trail_gap_r)
        dynamic_momentum_pullback_r = self._safe_float(dynamic_momentum_pullback_r)
        profit_harvest_min_mfe_r = self._safe_float(profit_harvest_min_mfe_r)
        profit_harvest_trail_gap_r = self._safe_float(profit_harvest_trail_gap_r)
        profit_harvest_protect_floor_r = self._safe_float(
            profit_harvest_protect_floor_r
        )
        profit_harvest_close_on_giveback_r = self._safe_float(
            profit_harvest_close_on_giveback_r
        )
        profit_harvest_stale_min_mfe_r = self._safe_float(
            profit_harvest_stale_min_mfe_r
        )
        profit_harvest_stale_close_below_r = self._safe_float(
            profit_harvest_stale_close_below_r
        )
        if dynamic_time_stop_bars not in (None, ""):
            try:
                dynamic_time_stop_bars = int(dynamic_time_stop_bars)
            except (TypeError, ValueError):
                dynamic_time_stop_bars = None
        else:
            dynamic_time_stop_bars = None
        if profit_harvest_stale_minutes not in (None, ""):
            try:
                profit_harvest_stale_minutes = int(profit_harvest_stale_minutes)
            except (TypeError, ValueError):
                profit_harvest_stale_minutes = None
        else:
            profit_harvest_stale_minutes = None

        dynamic_be_trigger_price = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_be_trigger_price",
        )
        dynamic_final_target_price = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_dynamic_final_target_price",
        )
        placement_sl_distance = abs(
            float(trade_params["entry_price"]) - float(trade_params["stop_loss"])
        )
        if (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            in {
                "be_after_trigger",
                "partial_be_runner",
                "trailing_runner",
                "momentum_exhaustion",
                "time_stop",
            }
            and placement_sl_distance > 0
        ):
            if dynamic_be_trigger_price in (None, "") and dynamic_be_trigger_r:
                dynamic_be_trigger_price = self._target_price_from_r(
                    direction=trade_params["direction"],
                    entry_price=float(trade_params["entry_price"]),
                    sl_distance=placement_sl_distance,
                    target_r=float(dynamic_be_trigger_r),
                )
            if dynamic_final_target_price in (None, "") and dynamic_final_target_r:
                dynamic_final_target_price = self._target_price_from_r(
                    direction=trade_params["direction"],
                    entry_price=float(trade_params["entry_price"]),
                    sl_distance=placement_sl_distance,
                    target_r=float(dynamic_final_target_r),
                )
        dynamic_be_trigger_price = self._safe_float(dynamic_be_trigger_price)
        dynamic_final_target_price = self._safe_float(dynamic_final_target_price)
        explicit_target_stop_geometry_v4 = (
            telemetry_context.get("gtos_vnext_target_stop_geometry_v4")
            or telemetry_context.get("gtos_vnext_dynamic_target_stop_geometry_v4")
            or telemetry_context.get("gtos_vnext_target_stop_geometry_v4_packet")
            or telemetry_context.get("target_stop_geometry_v4")
            or trade_params.get("gtos_vnext_target_stop_geometry_v4")
            or trade_params.get("gtos_vnext_dynamic_target_stop_geometry_v4")
            or trade_params.get("gtos_vnext_target_stop_geometry_v4_packet")
            or trade_params.get("target_stop_geometry_v4")
        )
        if (
            isinstance(explicit_target_stop_geometry_v4, dict)
            and explicit_target_stop_geometry_v4.get("status")
            == "source_bound_geometry_contract_ready"
        ):
            target_stop_geometry_v4 = dict(explicit_target_stop_geometry_v4)
        else:
            target_stop_geometry_v4 = build_target_stop_geometry_v4_contract(
                config=self.config,
                selected_policy=dynamic_selected_policy,
                execution_policy_id=telemetry_context.get(
                    "gtos_vnext_execution_policy_id",
                    trade_params.get("gtos_vnext_execution_policy_id"),
                ),
                source_event=telemetry_context.get(
                    "gtos_vnext_source_event_details",
                    trade_params.get("gtos_vnext_source_event_details") or {},
                )
                or {},
                trade_params={**trade_params, **telemetry_context},
                prior_contract=(
                    explicit_target_stop_geometry_v4
                    if isinstance(explicit_target_stop_geometry_v4, dict)
                    else None
                ),
                entry_price=trade_params.get("entry_price"),
                stop_loss=trade_params.get("stop_loss"),
                direction=trade_params.get("direction"),
                risk_distance=placement_sl_distance,
                trigger_r=dynamic_be_trigger_r,
                final_target_r=dynamic_final_target_r,
                trigger_price=dynamic_be_trigger_price,
                final_target_price=dynamic_final_target_price,
                stage="pending_limit_intent_placement",
            )

        trade_id = f"lim_{self._persist_symbol}_{now_utc.strftime('%Y-%m-%d_%H%M%S')}"
        risk_reservation = build_risk_reservation(
            account_balance=account_balance,
            risk_pct=risk_pct,
            broker_namespace=self._runtime_namespace,
            symbol=self._persist_symbol,
            trade_id=trade_id,
        )

        intent = PendingLimitIntent(
            direction=trade_params["direction"],
            limit_price=trade_params["entry_price"],
            stop_loss=trade_params["stop_loss"],
            take_profit_1=trade_params["take_profit_1"],
            risk_pct=risk_pct,
            trade_id=trade_id,
            placed_time=now_utc.isoformat(),
            account_balance=float(account_balance or 0.0),
            candidate_id=telemetry_context.get("candidate_id"),
            decision_time_utc=telemetry_context.get("decision_time_utc"),
            source_file=telemetry_context.get("source_file"),
            source_hash=telemetry_context.get("source_hash"),
            source_symbol=telemetry_context.get("source_symbol"),
            session=telemetry_context.get("session"),
            kill_zone=telemetry_context.get("kill_zone"),
            regime=telemetry_context.get("regime"),
            decision_spread_value_source_safe=decision_spread_value,
            decision_spread_unit=decision_spread_unit,
            gtos_vnext_pre_ai_action=telemetry_context.get("gtos_vnext_pre_ai_action"),
            gtos_vnext_pre_ai_recommended_side=telemetry_context.get(
                "gtos_vnext_pre_ai_recommended_side"
            ),
            gtos_vnext_pre_ai_recommended_frameworks=telemetry_context.get(
                "gtos_vnext_pre_ai_recommended_frameworks"
            ),
            gtos_vnext_decision=telemetry_context.get("gtos_vnext_decision"),
            gtos_vnext_reason=telemetry_context.get("gtos_vnext_reason"),
            gtos_vnext_matched=telemetry_context.get("gtos_vnext_matched"),
            gtos_vnext_matched_rows=telemetry_context.get("gtos_vnext_matched_rows"),
            gtos_vnext_matched_rows_status=telemetry_context.get(
                "gtos_vnext_matched_rows_status"
            ),
            gtos_vnext_broader_origin_selected_rows=telemetry_context.get(
                "gtos_vnext_broader_origin_selected_rows"
            ),
            gtos_vnext_broader_origin_performance_rows=telemetry_context.get(
                "gtos_vnext_broader_origin_performance_rows"
            ),
            gtos_vnext_cost_adjusted_r_sum=telemetry_context.get(
                "gtos_vnext_cost_adjusted_r_sum"
            ),
            gtos_vnext_proxy_score_sum=telemetry_context.get("gtos_vnext_proxy_score_sum"),
            gtos_vnext_stress_r_sum=telemetry_context.get("gtos_vnext_stress_r_sum"),
            gtos_vnext_effective_n_sum=telemetry_context.get("gtos_vnext_effective_n_sum"),
            gtos_vnext_risk_multiplier=telemetry_context.get("gtos_vnext_risk_multiplier"),
            gtos_vnext_risk_would_multiplier=telemetry_context.get(
                "gtos_vnext_risk_would_multiplier"
            ),
            gtos_vnext_risk_reason=telemetry_context.get("gtos_vnext_risk_reason"),
            gtos_vnext_pending_policy_action=telemetry_context.get(
                "gtos_vnext_pending_policy_action"
            ),
            gtos_vnext_pending_policy_would_action=telemetry_context.get(
                "gtos_vnext_pending_policy_would_action"
            ),
            gtos_vnext_pending_policy_applied=telemetry_context.get(
                "gtos_vnext_pending_policy_applied"
            ),
            gtos_vnext_pending_policy_reason=telemetry_context.get(
                "gtos_vnext_pending_policy_reason"
            ),
            gtos_vnext_ltf_path_action=telemetry_context.get(
                "gtos_vnext_ltf_path_action"
            ),
            gtos_vnext_ltf_path_would_action=telemetry_context.get(
                "gtos_vnext_ltf_path_would_action"
            ),
            gtos_vnext_ltf_path_applied=telemetry_context.get(
                "gtos_vnext_ltf_path_applied"
            ),
            gtos_vnext_ltf_path_reason=telemetry_context.get(
                "gtos_vnext_ltf_path_reason"
            ),
            gtos_vnext_ltf_path_monitor_timeframe=telemetry_context.get(
                "gtos_vnext_ltf_path_monitor_timeframe"
            ),
            gtos_vnext_ltf_path_adjusted_entry_price=telemetry_context.get(
                "gtos_vnext_ltf_path_adjusted_entry_price"
            ),
            gtos_vnext_prop_safe_selector_action=telemetry_context.get(
                "gtos_vnext_prop_safe_selector_action"
            ),
            gtos_vnext_prop_safe_selector_would_action=telemetry_context.get(
                "gtos_vnext_prop_safe_selector_would_action"
            ),
            gtos_vnext_prop_safe_selector_applied=telemetry_context.get(
                "gtos_vnext_prop_safe_selector_applied"
            ),
            gtos_vnext_prop_safe_selector_after_risk_pct=telemetry_context.get(
                "gtos_vnext_prop_safe_selector_after_risk_pct"
            ),
            gtos_vnext_prop_safe_selector_reason=telemetry_context.get(
                "gtos_vnext_prop_safe_selector_reason"
            ),
            gtos_vnext_prop_firm_headroom_snapshot_v4=telemetry_context.get(
                "gtos_vnext_prop_firm_headroom_snapshot_v4",
                trade_params.get("gtos_vnext_prop_firm_headroom_snapshot_v4"),
            ),
            gtos_vnext_prop_firm_headroom_v4_packet=telemetry_context.get(
                "gtos_vnext_prop_firm_headroom_v4_packet",
                trade_params.get("gtos_vnext_prop_firm_headroom_v4_packet"),
            ),
            gtos_vnext_selector_v4_action=telemetry_context.get(
                "gtos_vnext_selector_v4_action",
                trade_params.get("gtos_vnext_selector_v4_action"),
            ),
            gtos_vnext_selector_v4_reason=telemetry_context.get(
                "gtos_vnext_selector_v4_reason",
                trade_params.get("gtos_vnext_selector_v4_reason"),
            ),
            gtos_vnext_selector_v4_packet=telemetry_context.get(
                "gtos_vnext_selector_v4_packet",
                trade_params.get("gtos_vnext_selector_v4_packet"),
            ),
            gtos_vnext_selector_v4_packet_hash=telemetry_context.get(
                "gtos_vnext_selector_v4_packet_hash",
                trade_params.get("gtos_vnext_selector_v4_packet_hash"),
            ),
            gtos_vnext_scheduler_v4_packet=telemetry_context.get(
                "gtos_vnext_scheduler_v4_packet",
                trade_params.get("gtos_vnext_scheduler_v4_packet"),
            ),
            gtos_vnext_scheduler_v4_packet_hash=telemetry_context.get(
                "gtos_vnext_scheduler_v4_packet_hash",
                trade_params.get("gtos_vnext_scheduler_v4_packet_hash"),
            ),
            gtos_vnext_scheduler_v4_current_candidate_id=telemetry_context.get(
                "gtos_vnext_scheduler_v4_current_candidate_id",
                trade_params.get("gtos_vnext_scheduler_v4_current_candidate_id"),
            ),
            gtos_vnext_scheduler_v4_selected_candidate_id=telemetry_context.get(
                "gtos_vnext_scheduler_v4_selected_candidate_id",
                trade_params.get("gtos_vnext_scheduler_v4_selected_candidate_id"),
            ),
            gtos_vnext_scheduler_v4_selected_candidate_ids=telemetry_context.get(
                "gtos_vnext_scheduler_v4_selected_candidate_ids",
                trade_params.get("gtos_vnext_scheduler_v4_selected_candidate_ids"),
            ),
            gtos_vnext_scheduler_v4_selected_action_class=telemetry_context.get(
                "gtos_vnext_scheduler_v4_selected_action_class",
                trade_params.get("gtos_vnext_scheduler_v4_selected_action_class"),
            ),
            gtos_vnext_same_symbol_lifecycle_v4_packet=telemetry_context.get(
                "gtos_vnext_same_symbol_lifecycle_v4_packet",
                trade_params.get("gtos_vnext_same_symbol_lifecycle_v4_packet"),
            ),
            gtos_vnext_same_symbol_lifecycle_action=telemetry_context.get(
                "gtos_vnext_same_symbol_lifecycle_action",
                trade_params.get("gtos_vnext_same_symbol_lifecycle_action"),
            ),
            gtos_vnext_same_symbol_lifecycle_reason=telemetry_context.get(
                "gtos_vnext_same_symbol_lifecycle_reason",
                trade_params.get("gtos_vnext_same_symbol_lifecycle_reason"),
            ),
            gtos_vnext_pretrade_cost_model=telemetry_context.get(
                "gtos_vnext_pretrade_cost_model",
                trade_params.get("gtos_vnext_pretrade_cost_model"),
            ),
            gtos_vnext_execution_policy_id=telemetry_context.get(
                "gtos_vnext_execution_policy_id",
                trade_params.get("gtos_vnext_execution_policy_id"),
            ),
            gtos_vnext_dynamic_policy_selected=dynamic_selected_policy,
            gtos_vnext_dynamic_policy_applied=dynamic_applied,
            gtos_vnext_dynamic_policy_replaced_policy=telemetry_context.get(
                "gtos_vnext_dynamic_policy_replaced_policy",
                trade_params.get("gtos_vnext_dynamic_policy_replaced_policy"),
            ),
            gtos_vnext_dynamic_policy_candidate_action=telemetry_context.get(
                "gtos_vnext_dynamic_policy_candidate_action",
                trade_params.get("gtos_vnext_dynamic_policy_candidate_action"),
            ),
            gtos_vnext_dynamic_policy_decision_status=telemetry_context.get(
                "gtos_vnext_dynamic_policy_decision_status",
                trade_params.get("gtos_vnext_dynamic_policy_decision_status"),
            ),
            gtos_vnext_dynamic_policy_source_quality_action=telemetry_context.get(
                "gtos_vnext_dynamic_policy_source_quality_action",
                trade_params.get("gtos_vnext_dynamic_policy_source_quality_action"),
            ),
            gtos_vnext_dynamic_policy_exit_management_action=telemetry_context.get(
                "gtos_vnext_dynamic_policy_exit_management_action",
                trade_params.get("gtos_vnext_dynamic_policy_exit_management_action"),
            ),
            gtos_vnext_dynamic_policy_prop_action=telemetry_context.get(
                "gtos_vnext_dynamic_policy_prop_action",
                trade_params.get("gtos_vnext_dynamic_policy_prop_action"),
            ),
            gtos_vnext_dynamic_policy_fixed_target_role=telemetry_context.get(
                "gtos_vnext_dynamic_policy_fixed_target_role",
                trade_params.get("gtos_vnext_dynamic_policy_fixed_target_role"),
            ),
            gtos_vnext_target_stop_geometry_v4=target_stop_geometry_v4,
            gtos_vnext_selected_cell_risk_pct=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_pct",
                trade_params.get("gtos_vnext_selected_cell_risk_pct"),
            ),
            gtos_vnext_selected_cell_risk_cell_id=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_cell_id",
                trade_params.get("gtos_vnext_selected_cell_risk_cell_id"),
            ),
            gtos_vnext_selected_cell_risk_status=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_status",
                trade_params.get("gtos_vnext_selected_cell_risk_status"),
            ),
            gtos_vnext_selected_cell_risk_decision_basis=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_decision_basis",
                trade_params.get("gtos_vnext_selected_cell_risk_decision_basis"),
            ),
            gtos_vnext_selected_cell_risk_unresolved_reasons=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_unresolved_reasons",
                trade_params.get("gtos_vnext_selected_cell_risk_unresolved_reasons"),
            ),
            gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons",
                trade_params.get(
                    "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons"
                ),
            ),
            gtos_vnext_selected_cell_risk_selected_policy=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_selected_policy",
                trade_params.get("gtos_vnext_selected_cell_risk_selected_policy"),
            ),
            gtos_vnext_selected_cell_risk_source_policy=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_source_policy",
                trade_params.get("gtos_vnext_selected_cell_risk_source_policy"),
            ),
            gtos_vnext_selected_cell_risk_policy_identity_status=telemetry_context.get(
                "gtos_vnext_selected_cell_risk_policy_identity_status",
                trade_params.get("gtos_vnext_selected_cell_risk_policy_identity_status"),
            ),
            gtos_vnext_commission_model_status=telemetry_context.get(
                "gtos_vnext_commission_model_status",
                trade_params.get("gtos_vnext_commission_model_status"),
            ),
            gtos_vnext_cost_model_source=telemetry_context.get(
                "gtos_vnext_cost_model_source",
                trade_params.get("gtos_vnext_cost_model_source"),
            ),
            gtos_vnext_production_execution_path=telemetry_context.get(
                "gtos_vnext_production_execution_path",
                trade_params.get("gtos_vnext_production_execution_path"),
            ),
            gtos_vnext_dynamic_be_trigger_r=dynamic_be_trigger_r,
            gtos_vnext_dynamic_final_target_r=dynamic_final_target_r,
            gtos_vnext_dynamic_broker_take_profit_mode=telemetry_context.get(
                "gtos_vnext_dynamic_broker_take_profit_mode",
                trade_params.get("gtos_vnext_dynamic_broker_take_profit_mode"),
            ),
            gtos_vnext_dynamic_no_broker_take_profit=telemetry_context.get(
                "gtos_vnext_dynamic_no_broker_take_profit",
                trade_params.get("gtos_vnext_dynamic_no_broker_take_profit"),
            ),
            gtos_vnext_dynamic_be_trigger_price=dynamic_be_trigger_price,
            gtos_vnext_dynamic_final_target_price=dynamic_final_target_price,
            gtos_vnext_dynamic_trail_gap_r=dynamic_trail_gap_r,
            gtos_vnext_dynamic_momentum_pullback_r=dynamic_momentum_pullback_r,
            gtos_vnext_dynamic_time_stop_bars=dynamic_time_stop_bars,
            gtos_vnext_book_native_exit_management=bool(
                telemetry_context.get(
                    "gtos_vnext_book_native_exit_management",
                    trade_params.get("gtos_vnext_book_native_exit_management", False),
                )
            ),
            gtos_vnext_profit_harvest_mfe_capture_v4_enabled=(
                self._bool_param_enabled(profit_harvest_enabled)
            ),
            gtos_vnext_profit_harvest_min_mfe_r=profit_harvest_min_mfe_r,
            gtos_vnext_profit_harvest_trail_gap_r=profit_harvest_trail_gap_r,
            gtos_vnext_profit_harvest_protect_floor_r=profit_harvest_protect_floor_r,
            gtos_vnext_profit_harvest_close_on_giveback_r=(
                profit_harvest_close_on_giveback_r
            ),
            gtos_vnext_profit_harvest_stale_minutes=profit_harvest_stale_minutes,
            gtos_vnext_profit_harvest_stale_min_mfe_r=profit_harvest_stale_min_mfe_r,
            gtos_vnext_profit_harvest_stale_close_below_r=(
                profit_harvest_stale_close_below_r
            ),
            gtos_vnext_source_event_hash=telemetry_context.get(
                "gtos_vnext_source_event_hash",
                trade_params.get("gtos_vnext_source_event_hash"),
            ),
            gtos_vnext_source_event_details=telemetry_context.get(
                "gtos_vnext_source_event_details",
                trade_params.get("gtos_vnext_source_event_details"),
            ),
            gtos_vnext_activation_family=telemetry_context.get(
                "gtos_vnext_activation_family",
                trade_params.get("gtos_vnext_activation_family"),
            ),
            gtos_vnext_origin_family=telemetry_context.get(
                "gtos_vnext_origin_family",
                trade_params.get("gtos_vnext_origin_family"),
            ),
            gtos_vnext_selector_row_id=telemetry_context.get(
                "gtos_vnext_selector_row_id",
                trade_params.get("gtos_vnext_selector_row_id"),
            ),
            gtos_vnext_selector_proof_hash=telemetry_context.get(
                "gtos_vnext_selector_proof_hash",
                trade_params.get("gtos_vnext_selector_proof_hash"),
            ),
            pending_lifecycle_v4_id=risk_reservation["pending_lifecycle_v4_id"],
            risk_reserved_pct=risk_reservation["risk_reserved_pct"],
            risk_reserved_cash=risk_reservation["risk_reserved_cash"],
            risk_reservation_status=risk_reservation["risk_reservation_status"],
            risk_reservation_scope=risk_reservation["risk_reservation_scope"],
            risk_reservation_source=risk_reservation["risk_reservation_source"],
            risk_reservation_broker_namespace=risk_reservation[
                "risk_reservation_broker_namespace"
            ],
        )
        v4_trade_params = {**trade_params, **telemetry_context}
        v4_trade_params.setdefault("pending_order_mode", intent.pending_order_mode)
        v4_trade_params.setdefault("pending_limit_price", intent.limit_price)
        v4_trade_params.setdefault("pending_created_time_utc", intent.placed_time)
        v4_trade_params.setdefault("pending_candles_elapsed", intent.candles_elapsed)
        v4_decision = self._evaluate_execution_manager_v4(
            trade_params=v4_trade_params,
            pretrade_cost_model=telemetry_context.get(
                "gtos_vnext_pretrade_cost_model",
                trade_params.get("gtos_vnext_pretrade_cost_model"),
            ),
            pending_context={
                "stage": "pending_intent_created",
                "pending_order_mode": intent.pending_order_mode,
                "pending_created_time_utc": intent.placed_time,
                "pending_candles_elapsed": intent.candles_elapsed,
                "limit_price": intent.limit_price,
                "stop_loss": intent.stop_loss,
            },
            trigger="set_limit_intent",
        )
        self._apply_execution_manager_v4_to_intent(intent, v4_decision)
        if v4_decision.should_block:
            logger.warning(
                "Execution Manager V4 blocked pending limit intent before persistence: %s",
                ",".join(v4_decision.fatal_reasons),
            )
            return None
        self.pending_intent = intent
        self._pending_account_balance = account_balance
        logger.info(
            "Limit intent set: %s %s limit=%.5f sl=%.5f tp=%.5f expires=%d candles",
            intent.direction, self.symbol, intent.limit_price,
            intent.stop_loss, intent.take_profit_1, intent.expiry_candles,
        )
        return intent

    def _safe_float(self, value) -> Optional[float]:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _record_pending_limit_lifecycle(
        self,
        *,
        intent: PendingLimitIntent,
        intent_after_check: str,
        candles_elapsed_before: int,
        candles_elapsed_after: int,
        candle: Optional[dict] = None,
        telemetry_context: Optional[dict] = None,
        trigger_condition_met: Optional[bool] = None,
        tick=None,
        current_price_used: Optional[float] = None,
        wrong_side_abort: bool = False,
        sl_too_close_abort: bool = False,
        order_send_attempted: bool = False,
        order_send_success: bool = False,
        trade_state: Optional[TradeState] = None,
        reason: Optional[str] = None,
    ) -> None:
        """Best-effort lifecycle telemetry; never affects execution flow."""
        try:
            telemetry_context = telemetry_context or {}

            def _ctx(name: str):
                value = telemetry_context.get(name)
                if value is not None:
                    return value
                return getattr(intent, name, None)

            tick_bid = self._safe_float(getattr(tick, "bid", None)) if tick else None
            tick_ask = self._safe_float(getattr(tick, "ask", None)) if tick else None
            tick_spread = self._safe_float(getattr(tick, "spread_cents", None)) if tick else None
            checked_time = candle.get("time") if candle else None
            try:
                pending_start_dt = datetime.fromisoformat(intent.placed_time)
                if pending_start_dt.tzinfo is None:
                    pending_start_dt = pending_start_dt.replace(tzinfo=timezone.utc)
                pending_horizon_end_utc = (pending_start_dt + timedelta(hours=48)).isoformat()
            except Exception:
                pending_horizon_end_utc = None
            decision_spread_value = telemetry_context.get(
                "decision_spread_value_source_safe"
            )
            if decision_spread_value is None:
                decision_spread_value = getattr(
                    intent,
                    "decision_spread_value_source_safe",
                    None,
                )
            if decision_spread_value is None:
                decision_spread_value = telemetry_context.get("decision_spread")
            decision_spread_unit = telemetry_context.get("decision_spread_unit") or getattr(
                intent,
                "decision_spread_unit",
                None,
            )
            trade_state_ticket = (
                getattr(trade_state, "ticket", None) if trade_state else None
            )
            mt5_entry_order_ticket = (
                getattr(trade_state, "entry_order_ticket", None)
                if trade_state
                else None
            )
            mt5_entry_deal_ticket = (
                getattr(trade_state, "entry_deal_ticket", None)
                if trade_state
                else None
            )
            if mt5_entry_deal_ticket in (0, "0"):
                mt5_entry_deal_ticket = None
            entry_order_retcode = (
                getattr(trade_state, "entry_order_retcode", None)
                if trade_state
                else None
            )
            executed_entry_price = (
                getattr(trade_state, "entry_price", None) if trade_state else None
            )
            execution_price_delta_from_limit = None
            try:
                if executed_entry_price is not None and intent.limit_price is not None:
                    execution_price_delta_from_limit = (
                        float(executed_entry_price) - float(intent.limit_price)
                    )
            except (TypeError, ValueError):
                execution_price_delta_from_limit = None
            order_execution_model = "INTERNAL_CANDLE_POLLED_MARKET_ORDER_ON_TOUCH"
            market_order_requested_price = (
                current_price_used if order_send_attempted else None
            )
            market_order_price_source = (
                "current_tick_ask_bid_at_touch" if order_send_attempted else None
            )
            join_keys = []
            for key_name, key_value in (
                ("trade_state_ticket", trade_state_ticket),
                ("mt5_position_ticket", trade_state_ticket),
                ("mt5_entry_order_ticket", mt5_entry_order_ticket),
                ("mt5_entry_deal_ticket", mt5_entry_deal_ticket),
            ):
                if key_value not in (None, "", 0, "0"):
                    join_keys.append(f"{key_name}:{key_value}")
            join_keys = list(dict.fromkeys(join_keys))
            entry = {
                "symbol": self._persist_symbol,
                "broker_symbol": self.symbol,
                "source_symbol": _ctx("source_symbol"),
                "session": _ctx("session"),
                "kill_zone": _ctx("kill_zone"),
                "side": intent.direction,
                "regime": _ctx("regime"),
                "candidate_id": _ctx("candidate_id"),
                "trade_id": intent.trade_id,
                "decision_time_utc": _ctx("decision_time_utc"),
                "asof_cutoff_utc": telemetry_context.get("asof_cutoff_utc") or checked_time,
                "source_file": _ctx("source_file"),
                "source_hash": _ctx("source_hash"),
                "gtos_vnext_source_event_details": getattr(
                    intent,
                    "gtos_vnext_source_event_details",
                    None,
                ),
                "pending_created_time_utc": intent.placed_time,
                "pending_ticket": None,
                "pending_lifecycle_v4_id": getattr(
                    intent,
                    "pending_lifecycle_v4_id",
                    None,
                ),
                "pending_order_mode": getattr(
                    intent,
                    "pending_order_mode",
                    INTERNAL_PENDING_ORDER_MODE,
                ),
                "broker_pending_order_created": bool(
                    getattr(intent, "broker_pending_order_created", False)
                ),
                "mt5_order_ticket": getattr(intent, "mt5_order_ticket", None),
                "native_pending_order_type": getattr(
                    intent,
                    "native_pending_order_type",
                    None,
                ),
                "risk_reserved_pct": getattr(intent, "risk_reserved_pct", None),
                "risk_reserved_cash": getattr(intent, "risk_reserved_cash", None),
                "risk_reservation_status": getattr(
                    intent,
                    "risk_reservation_status",
                    None,
                ),
                "risk_reservation_scope": getattr(
                    intent,
                    "risk_reservation_scope",
                    None,
                ),
                "risk_reservation_source": getattr(
                    intent,
                    "risk_reservation_source",
                    None,
                ),
                "risk_reservation_broker_namespace": getattr(
                    intent,
                    "risk_reservation_broker_namespace",
                    None,
                ),
                "pending_execution_model": order_execution_model,
                "pending_limit_requested_price": intent.limit_price,
                "broker_order_entry_mode": (
                    "MARKET_ORDER" if order_send_attempted else None
                ),
                "broker_order_action": (
                    "TRADE_ACTION_DEAL" if order_send_attempted else None
                ),
                "market_order_requested_price": market_order_requested_price,
                "market_order_price_source": market_order_price_source,
                "executed_entry_price": executed_entry_price,
                "execution_price_delta_from_limit": execution_price_delta_from_limit,
                "fill_time_utc": (
                    datetime.now(timezone.utc).isoformat()
                    if intent_after_check == "order_send_success_filled"
                    else None
                ),
                "expiry_time_utc": (
                    datetime.now(timezone.utc).isoformat()
                    if intent_after_check == "expired_48h"
                    else None
                ),
                "cancel_reason": reason
                if intent_after_check in {
                    "expired_48h",
                    "cancelled_wrong_side",
                    "cancelled_sl_too_close",
                    "manual_or_system_cancelled",
                }
                else None,
                "broker_fill_state": (
                    "filled" if order_send_success else "not_filled"
                ),
                "entry_price": intent.limit_price,
                "stop_loss": intent.stop_loss,
                "take_profit_1": intent.take_profit_1,
                "spread": tick_spread,
                "decision_spread_value_source_safe": decision_spread_value,
                "decision_spread_unit": decision_spread_unit
                or ("spread_cents" if decision_spread_value is not None else None),
                "gtos_vnext_pre_ai_action": getattr(intent, "gtos_vnext_pre_ai_action", None),
                "gtos_vnext_pre_ai_recommended_side": getattr(
                    intent,
                    "gtos_vnext_pre_ai_recommended_side",
                    None,
                ),
                "gtos_vnext_pre_ai_recommended_frameworks": getattr(
                    intent,
                    "gtos_vnext_pre_ai_recommended_frameworks",
                    None,
                ),
                "gtos_vnext_decision": getattr(intent, "gtos_vnext_decision", None),
                "gtos_vnext_reason": getattr(intent, "gtos_vnext_reason", None),
                "gtos_vnext_matched": getattr(intent, "gtos_vnext_matched", None),
                "gtos_vnext_matched_rows": getattr(intent, "gtos_vnext_matched_rows", None),
                "gtos_vnext_matched_rows_status": getattr(
                    intent,
                    "gtos_vnext_matched_rows_status",
                    None,
                ),
                "gtos_vnext_broader_origin_selected_rows": getattr(
                    intent,
                    "gtos_vnext_broader_origin_selected_rows",
                    None,
                ),
                "gtos_vnext_broader_origin_performance_rows": getattr(
                    intent,
                    "gtos_vnext_broader_origin_performance_rows",
                    None,
                ),
                "gtos_vnext_cost_adjusted_r_sum": getattr(
                    intent,
                    "gtos_vnext_cost_adjusted_r_sum",
                    None,
                ),
                "gtos_vnext_proxy_score_sum": getattr(intent, "gtos_vnext_proxy_score_sum", None),
                "gtos_vnext_stress_r_sum": getattr(intent, "gtos_vnext_stress_r_sum", None),
                "gtos_vnext_effective_n_sum": getattr(intent, "gtos_vnext_effective_n_sum", None),
                "gtos_vnext_risk_multiplier": getattr(intent, "gtos_vnext_risk_multiplier", None),
                "gtos_vnext_risk_would_multiplier": getattr(
                    intent,
                    "gtos_vnext_risk_would_multiplier",
                    None,
                ),
                "gtos_vnext_risk_reason": getattr(intent, "gtos_vnext_risk_reason", None),
                "gtos_vnext_pending_policy_action": getattr(
                    intent,
                    "gtos_vnext_pending_policy_action",
                    None,
                ),
                "gtos_vnext_pending_policy_would_action": getattr(
                    intent,
                    "gtos_vnext_pending_policy_would_action",
                    None,
                ),
                "gtos_vnext_pending_policy_applied": getattr(
                    intent,
                    "gtos_vnext_pending_policy_applied",
                    None,
                ),
                "gtos_vnext_pending_policy_reason": getattr(
                    intent,
                    "gtos_vnext_pending_policy_reason",
                    None,
                ),
                "gtos_vnext_ltf_path_action": getattr(
                    intent,
                    "gtos_vnext_ltf_path_action",
                    None,
                ),
                "gtos_vnext_ltf_path_would_action": getattr(
                    intent,
                    "gtos_vnext_ltf_path_would_action",
                    None,
                ),
                "gtos_vnext_ltf_path_applied": getattr(
                    intent,
                    "gtos_vnext_ltf_path_applied",
                    None,
                ),
                "gtos_vnext_ltf_path_reason": getattr(
                    intent,
                    "gtos_vnext_ltf_path_reason",
                    None,
                ),
                "gtos_vnext_ltf_path_monitor_timeframe": getattr(
                    intent,
                    "gtos_vnext_ltf_path_monitor_timeframe",
                    None,
                ),
                "gtos_vnext_ltf_path_adjusted_entry_price": getattr(
                    intent,
                    "gtos_vnext_ltf_path_adjusted_entry_price",
                    None,
                ),
                "gtos_vnext_prop_safe_selector_action": getattr(
                    intent,
                    "gtos_vnext_prop_safe_selector_action",
                    None,
                ),
                "gtos_vnext_prop_safe_selector_would_action": getattr(
                    intent,
                    "gtos_vnext_prop_safe_selector_would_action",
                    None,
                ),
                "gtos_vnext_prop_safe_selector_applied": getattr(
                    intent,
                    "gtos_vnext_prop_safe_selector_applied",
                    None,
                ),
                "gtos_vnext_prop_safe_selector_after_risk_pct": getattr(
                    intent,
                    "gtos_vnext_prop_safe_selector_after_risk_pct",
                    None,
                ),
                "gtos_vnext_prop_safe_selector_reason": getattr(
                    intent,
                    "gtos_vnext_prop_safe_selector_reason",
                    None,
                ),
                "gtos_vnext_prop_firm_headroom_snapshot_v4": getattr(
                    intent,
                    "gtos_vnext_prop_firm_headroom_snapshot_v4",
                    None,
                ),
                "gtos_vnext_prop_firm_headroom_v4_packet": getattr(
                    intent,
                    "gtos_vnext_prop_firm_headroom_v4_packet",
                    None,
                ),
                "gtos_vnext_selector_v4_action": getattr(
                    intent,
                    "gtos_vnext_selector_v4_action",
                    None,
                ),
                "gtos_vnext_selector_v4_reason": getattr(
                    intent,
                    "gtos_vnext_selector_v4_reason",
                    None,
                ),
                "gtos_vnext_selector_v4_packet": getattr(
                    intent,
                    "gtos_vnext_selector_v4_packet",
                    None,
                ),
                "gtos_vnext_selector_v4_packet_hash": getattr(
                    intent,
                    "gtos_vnext_selector_v4_packet_hash",
                    None,
                ),
                "gtos_vnext_scheduler_v4_packet": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_packet",
                    None,
                ),
                "gtos_vnext_scheduler_v4_packet_hash": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_packet_hash",
                    None,
                ),
                "gtos_vnext_scheduler_v4_current_candidate_id": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_current_candidate_id",
                    None,
                ),
                "gtos_vnext_scheduler_v4_selected_candidate_id": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_selected_candidate_id",
                    None,
                ),
                "gtos_vnext_scheduler_v4_selected_candidate_ids": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_selected_candidate_ids",
                    None,
                ),
                "gtos_vnext_scheduler_v4_selected_action_class": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_selected_action_class",
                    None,
                ),
                "gtos_vnext_same_symbol_lifecycle_v4_packet": getattr(
                    intent,
                    "gtos_vnext_same_symbol_lifecycle_v4_packet",
                    None,
                ),
                "gtos_vnext_same_symbol_lifecycle_action": getattr(
                    intent,
                    "gtos_vnext_same_symbol_lifecycle_action",
                    None,
                ),
                "gtos_vnext_same_symbol_lifecycle_reason": getattr(
                    intent,
                    "gtos_vnext_same_symbol_lifecycle_reason",
                    None,
                ),
                "gtos_vnext_pretrade_cost_model": getattr(
                    intent,
                    "gtos_vnext_pretrade_cost_model",
                    None,
                ),
                "gtos_vnext_execution_policy_id": getattr(
                    intent,
                    "gtos_vnext_execution_policy_id",
                    None,
                ),
                "gtos_vnext_dynamic_policy_selected": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_selected",
                    None,
                ),
                "gtos_vnext_dynamic_policy_applied": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_applied",
                    None,
                ),
                "gtos_vnext_dynamic_policy_replaced_policy": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_replaced_policy",
                    None,
                ),
                "gtos_vnext_dynamic_policy_candidate_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_candidate_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_decision_status": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_decision_status",
                    None,
                ),
                "gtos_vnext_dynamic_policy_source_quality_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_source_quality_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_exit_management_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_exit_management_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_prop_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_prop_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_fixed_target_role": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_fixed_target_role",
                    None,
                ),
                "gtos_vnext_target_stop_geometry_v4": getattr(
                    intent,
                    "gtos_vnext_target_stop_geometry_v4",
                    None,
                ),
                "gtos_vnext_dynamic_be_trigger_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_be_trigger_r",
                    None,
                ),
                "gtos_vnext_dynamic_final_target_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_final_target_r",
                    None,
                ),
                "gtos_vnext_dynamic_broker_take_profit_mode": getattr(
                    intent,
                    "gtos_vnext_dynamic_broker_take_profit_mode",
                    None,
                ),
                "gtos_vnext_dynamic_no_broker_take_profit": getattr(
                    intent,
                    "gtos_vnext_dynamic_no_broker_take_profit",
                    None,
                ),
                "gtos_vnext_dynamic_be_trigger_price": getattr(
                    intent,
                    "gtos_vnext_dynamic_be_trigger_price",
                    None,
                ),
                "gtos_vnext_dynamic_final_target_price": getattr(
                    intent,
                    "gtos_vnext_dynamic_final_target_price",
                    None,
                ),
                "gtos_vnext_dynamic_trail_gap_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_trail_gap_r",
                    None,
                ),
                "gtos_vnext_dynamic_momentum_pullback_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_momentum_pullback_r",
                    None,
                ),
                "gtos_vnext_dynamic_time_stop_bars": getattr(
                    intent,
                    "gtos_vnext_dynamic_time_stop_bars",
                    None,
                ),
                "gtos_vnext_book_native_exit_management": getattr(
                    intent,
                    "gtos_vnext_book_native_exit_management",
                    None,
                ),
                "gtos_vnext_profit_harvest_mfe_capture_v4_enabled": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_mfe_capture_v4_enabled",
                    None,
                ),
                "gtos_vnext_profit_harvest_min_mfe_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_min_mfe_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_trail_gap_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_trail_gap_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_protect_floor_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_protect_floor_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_close_on_giveback_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_close_on_giveback_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_stale_minutes": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_stale_minutes",
                    None,
                ),
                "gtos_vnext_profit_harvest_stale_min_mfe_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_stale_min_mfe_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_stale_close_below_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_stale_close_below_r",
                    None,
                ),
                "gtos_vnext_source_event_hash": getattr(
                    intent,
                    "gtos_vnext_source_event_hash",
                    None,
                ),
                "gtos_vnext_activation_family": getattr(
                    intent,
                    "gtos_vnext_activation_family",
                    None,
                ),
                "gtos_vnext_origin_family": getattr(
                    intent,
                    "gtos_vnext_origin_family",
                    None,
                ),
                "gtos_vnext_selector_row_id": getattr(
                    intent,
                    "gtos_vnext_selector_row_id",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_status": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_status",
                    None,
                ),
                "gtos_vnext_selector_proof_hash": getattr(
                    intent,
                    "gtos_vnext_selector_proof_hash",
                    None,
                ),
                "gtos_vnext_execution_manager_v4_status": getattr(
                    intent,
                    "gtos_vnext_execution_manager_v4_status",
                    None,
                ),
                "gtos_vnext_execution_manager_v4_action": getattr(
                    intent,
                    "gtos_vnext_execution_manager_v4_action",
                    None,
                ),
                "gtos_vnext_execution_manager_v4_fatal_reasons": getattr(
                    intent,
                    "gtos_vnext_execution_manager_v4_fatal_reasons",
                    None,
                ),
                "gtos_vnext_execution_manager_v4_warning_reasons": getattr(
                    intent,
                    "gtos_vnext_execution_manager_v4_warning_reasons",
                    None,
                ),
                "gtos_vnext_execution_manager_v4_packet": getattr(
                    intent,
                    "gtos_vnext_execution_manager_v4_packet",
                    None,
                ),
                "entry_touch_spread_value_source_safe": tick_spread
                if trigger_condition_met and tick_spread is not None
                else None,
                "entry_touch_spread_unit": "spread_cents"
                if trigger_condition_met and tick_spread is not None
                else None,
                "pending_horizon_start_utc": intent.placed_time,
                "pending_horizon_end_utc": pending_horizon_end_utc,
                "terminal_area_first_touch_utc": checked_time
                if intent_after_check == "cancelled_target_reached_without_fill"
                else None,
                "protective_area_first_touch_utc": checked_time
                if wrong_side_abort or sl_too_close_abort
                else None,
                "slippage_price": None,
                "actual_r": None,
                "synthetic_path_r": None,
                "checked_candle_time_utc": checked_time,
                "checked_candle_open": self._safe_float(candle.get("open")) if candle else None,
                "checked_candle_high": self._safe_float(candle.get("high")) if candle else None,
                "checked_candle_low": self._safe_float(candle.get("low")) if candle else None,
                "checked_candle_close": self._safe_float(candle.get("close")) if candle else None,
                "tick_bid": tick_bid,
                "tick_ask": tick_ask,
                "source_branch": telemetry_context.get("source_branch")
                or "execution_check_limit_fill",
                "check_context": telemetry_context.get("check_context") or "unknown",
                "candles_elapsed_before": candles_elapsed_before,
                "candles_elapsed_after": candles_elapsed_after,
                "trigger_condition_met": trigger_condition_met,
                "tick_available": tick is not None if trigger_condition_met else None,
                "current_price_used": current_price_used,
                "wrong_side_abort": wrong_side_abort,
                "sl_too_close_abort": sl_too_close_abort,
                "order_send_attempted": order_send_attempted,
                "order_send_success": order_send_success,
                "trade_state_ticket": trade_state_ticket,
                "mt5_position_ticket": trade_state_ticket,
                "mt5_entry_order_ticket": mt5_entry_order_ticket,
                "mt5_entry_deal_ticket": mt5_entry_deal_ticket,
                "order_result_retcode": entry_order_retcode,
                "filled_order_position_join_keys": join_keys,
                "exact_r_join_key_status": (
                    "FILLED_ORDER_POSITION_KEYS_CAPTURED"
                    if join_keys
                    else "NO_FILLED_ORDER_POSITION_KEYS_FOR_CURRENT_STATE"
                ),
                "intent_after_check": intent_after_check,
                "record_path": telemetry_context.get("record_path"),
                "raw_data_m15_count": telemetry_context.get("raw_data_m15_count"),
                "latest_m15_time_utc": telemetry_context.get("latest_m15_time_utc"),
                "latest_ltf_time_utc": telemetry_context.get("latest_ltf_time_utc"),
                "source_timeframe": telemetry_context.get("source_timeframe"),
                "last_limit_check_candle_time_before": telemetry_context.get(
                    "last_limit_check_candle_time_before"
                ),
                "reason": reason,
            }
            record_pending_limit_lifecycle(entry)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Pending-limit lifecycle wire-in failed (non-blocking): %s",
                exc,
            )

    def check_limit_fill(
        self,
        candle: dict,
        telemetry_context: Optional[dict] = None,
    ) -> Optional[TradeState]:
        """Check if candle triggers the pending limit. Returns TradeState if filled.

        Viability checks before execution:
        1. Tick data available (retry next candle if not)
        2. Price not beyond SL (cancel if blown through)
        3. Remaining SL cushion >= sl_absolute_min (cancel if too tight)

        Lot sizing uses the original limit->SL distance so volume stays
        reasonable when price is deeper in the OB (better entry).  The intent
        is only cleared on successful fill or deliberate abort -- order
        failures retain the intent for retry on the next triggered candle.
        """
        if self.pending_intent is None:
            return None

        telemetry_context = telemetry_context or {}
        intent = self.pending_intent
        candles_elapsed_before = intent.candles_elapsed
        try:
            self._enforce_runtime_halt_clear(
                "check_limit_fill",
                {
                    "trade_id": intent.trade_id,
                    "direction": intent.direction,
                    "limit_price": intent.limit_price,
                    "check_context": telemetry_context.get("check_context"),
                    "record_path": telemetry_context.get("record_path"),
                },
            )
        except RuntimeHaltError as exc:
            diagnostic = self._record_runtime_halt_diagnostic(
                action="check_limit_fill",
                exc=exc,
                extra={
                    "trade_id": intent.trade_id,
                    "direction": intent.direction,
                    "limit_price": intent.limit_price,
                },
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="runtime_halt_cancelled_no_order_send",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_before,
                candle=candle,
                telemetry_context={
                    **telemetry_context,
                    "runtime_halt_diagnostic": diagnostic,
                },
                trigger_condition_met=False,
                reason="runtime_halt_active_no_order_send",
            )
            self.pending_intent = None
            logger.warning(
                "Pending limit cancelled by atomic runtime halt before fill check: %s",
                diagnostic,
            )
            return None

        elapsed_increment = int(telemetry_context.get("elapsed_candle_increment", 1) or 0)
        intent.candles_elapsed += max(0, elapsed_increment)
        candles_elapsed_after = intent.candles_elapsed
        # Persist the bumped counter so a crash mid-loop doesn't lose it.
        # Cheap: single pickle of a small dataclass.
        self._save_pending_intent()

        # Clock-time expiry -- 48 hours from placement regardless of candle count
        placed_dt = datetime.fromisoformat(intent.placed_time)
        if datetime.now(timezone.utc) - placed_dt >= timedelta(hours=48):
            logger.info(
                "Limit intent expired (48h clock, %d KZ candles elapsed): %s",
                intent.candles_elapsed, intent.trade_id,
            )
            try:
                from src.notifications import (
                    build_vnext_notification_context,
                    notify_limit_expired,
                )
                notify_limit_expired(
                    symbol=self.symbol, trade_id=intent.trade_id,
                    reason="48h clock expiry",
                    vnext_context=build_vnext_notification_context(
                        intent,
                        lifecycle_event="expiry",
                    ),
                )
            except Exception:
                pass
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="expired_48h",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=False,
                reason="48h clock expiry",
            )
            self.pending_intent = None
            return None

        source_repair = (
            candle.get("ohlc_source_repair")
            if isinstance(candle, dict)
            else None
        )
        source_repair_status = (
            source_repair.get("status")
            if isinstance(source_repair, dict)
            else None
        )
        if str(source_repair_status or "").startswith("repair_failed"):
            logger.warning(
                "Limit fill skipped: malformed OHLC source repair failed for %s "
                "candle=%s status=%s",
                intent.trade_id,
                candle.get("time", "?") if isinstance(candle, dict) else "?",
                source_repair_status,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="source_repair_failed_retry",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=False,
                reason="malformed_ohlc_source_repair_failed",
            )
            return None

        triggered = (
            (intent.direction == "LONG" and candle["low"] <= intent.limit_price)
            or (intent.direction == "SHORT" and candle["high"] >= intent.limit_price)
        )

        if not triggered:
            target_reached_without_fill = (
                intent.take_profit_1
                and (
                    (
                        intent.direction == "LONG"
                        and candle["high"] >= intent.take_profit_1
                    )
                    or (
                        intent.direction == "SHORT"
                        and candle["low"] <= intent.take_profit_1
                    )
                )
            )
            if target_reached_without_fill:
                logger.info(
                    "Limit intent cancelled (target reached without entry touch): "
                    "%s candle=%s limit=%.5f tp1=%.5f",
                    intent.trade_id,
                    candle.get("time", "?"),
                    intent.limit_price,
                    intent.take_profit_1,
                )
                self._record_pending_limit_lifecycle(
                    intent=intent,
                    intent_after_check="cancelled_target_reached_without_fill",
                    candles_elapsed_before=candles_elapsed_before,
                    candles_elapsed_after=candles_elapsed_after,
                    candle=candle,
                    telemetry_context=telemetry_context,
                    trigger_condition_met=False,
                    reason="target_reached_without_entry_touch",
                )
                self.pending_intent = None
                return None

            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="still_pending_no_trigger",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=False,
            )
            return None

        logger.info(
            "Limit triggered: %s candle=%s low=%.5f limit=%.5f",
            intent.trade_id, candle.get("time", "?"),
            candle.get("low", 0), intent.limit_price,
        )

        # --- Viability checks before execution ---

        tick = self.mt5.get_tick(self.symbol)
        if tick is None:
            logger.warning(
                "Limit triggered but no tick data -- retrying next candle: %s",
                intent.trade_id,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="triggered_tick_missing_retry",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=True,
                tick=None,
                reason="tick_missing_retry",
            )
            return None  # Keep intent, retry next candle

        current_price = tick.ask if intent.direction == "LONG" else tick.bid
        original_sl_distance = abs(intent.limit_price - intent.stop_loss)
        current_sl_distance = abs(current_price - intent.stop_loss)

        # Wrong-side check: price has blown past the SL
        wrong_side = (
            (intent.direction == "LONG" and current_price <= intent.stop_loss)
            or (intent.direction == "SHORT" and current_price >= intent.stop_loss)
        )
        if wrong_side:
            logger.warning(
                "Limit fill abort (price beyond SL): %s current=%.5f SL=%.5f "
                "-- cancelling",
                intent.trade_id, current_price, intent.stop_loss,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="cancelled_wrong_side",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=True,
                tick=tick,
                current_price_used=current_price,
                wrong_side_abort=True,
                reason="price_beyond_sl",
            )
            self.pending_intent = None
            return None

        # Proximity abort: remaining SL cushion below instrument's minimum
        sl_absolute_min = self.config.get("risk", {}).get("sl_absolute_min", 0)
        if sl_absolute_min > 0 and current_sl_distance < sl_absolute_min:
            logger.warning(
                "Limit fill abort (SL too close): %s remaining=%.5f < "
                "sl_min=%.5f (current=%.5f, limit=%.5f, SL=%.5f) "
                "-- cancelling",
                intent.trade_id, current_sl_distance, sl_absolute_min,
                current_price, intent.limit_price, intent.stop_loss,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="cancelled_sl_too_close",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=True,
                tick=tick,
                current_price_used=current_price,
                sl_too_close_abort=True,
                reason="sl_too_close",
            )
            self.pending_intent = None
            return None

        # --- Execute with original SL distance for lot sizing ---

        saved_trade_id = intent.trade_id
        account_balance = self._pending_account_balance
        if account_balance <= 0:
            account_balance = float(getattr(intent, "account_balance", 0.0) or 0.0)
        if account_balance <= 0:
            try:
                account_balance = float(self.mt5.get_account_balance() or 0.0)
                logger.warning(
                    "Pending limit %s restored without account balance; using "
                    "current MT5 balance %.2f for lot sizing",
                    intent.trade_id, account_balance,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Pending limit %s balance fallback failed (%s); lot sizing "
                    "will fall back to minimum volume",
                    intent.trade_id, exc,
                )
                account_balance = 0.0

        pending_final_target_r = getattr(
            intent, "gtos_vnext_dynamic_final_target_r", None
        )
        risk_reward_ratio = (
            pending_final_target_r
            if pending_final_target_r not in (None, "")
            else 1.5
        )
        fill_trade_params = {
                "direction": intent.direction,
                "entry_price": intent.limit_price,
                "stop_loss": intent.stop_loss,
                "take_profit_1": intent.take_profit_1,
                "take_profit_2": 0.0,
                "take_profit_3": 0.0,
                "risk_reward_ratio": risk_reward_ratio,
                "decision_spread_value_source_safe": getattr(
                    intent,
                    "decision_spread_value_source_safe",
                    None,
                ),
                "decision_spread_unit": getattr(intent, "decision_spread_unit", None),
                "pending_created_time_utc": getattr(intent, "placed_time", None),
                "pending_candles_elapsed": getattr(intent, "candles_elapsed", None),
                "pending_order_mode": getattr(intent, "pending_order_mode", None),
                "pending_limit_price": getattr(intent, "limit_price", None),
                "candidate_id": getattr(intent, "candidate_id", None),
                "decision_time_utc": getattr(intent, "decision_time_utc", None),
                "source_file": getattr(intent, "source_file", None),
                "source_hash": getattr(intent, "source_hash", None),
                "source_symbol": getattr(intent, "source_symbol", None),
                "gtos_vnext_prop_firm_headroom_snapshot_v4": getattr(
                    intent,
                    "gtos_vnext_prop_firm_headroom_snapshot_v4",
                    None,
                ),
                "gtos_vnext_prop_firm_headroom_v4_packet": getattr(
                    intent,
                    "gtos_vnext_prop_firm_headroom_v4_packet",
                    None,
                ),
                "gtos_vnext_selector_v4_action": getattr(
                    intent,
                    "gtos_vnext_selector_v4_action",
                    None,
                ),
                "gtos_vnext_selector_v4_reason": getattr(
                    intent,
                    "gtos_vnext_selector_v4_reason",
                    None,
                ),
                "gtos_vnext_selector_v4_packet": getattr(
                    intent,
                    "gtos_vnext_selector_v4_packet",
                    None,
                ),
                "gtos_vnext_selector_v4_packet_hash": getattr(
                    intent,
                    "gtos_vnext_selector_v4_packet_hash",
                    None,
                ),
                "gtos_vnext_scheduler_v4_packet": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_packet",
                    None,
                ),
                "gtos_vnext_scheduler_v4_packet_hash": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_packet_hash",
                    None,
                ),
                "gtos_vnext_scheduler_v4_current_candidate_id": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_current_candidate_id",
                    None,
                ),
                "gtos_vnext_scheduler_v4_selected_candidate_id": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_selected_candidate_id",
                    None,
                ),
                "gtos_vnext_scheduler_v4_selected_candidate_ids": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_selected_candidate_ids",
                    None,
                ),
                "gtos_vnext_scheduler_v4_selected_action_class": getattr(
                    intent,
                    "gtos_vnext_scheduler_v4_selected_action_class",
                    None,
                ),
                "gtos_vnext_same_symbol_lifecycle_v4_packet": getattr(
                    intent,
                    "gtos_vnext_same_symbol_lifecycle_v4_packet",
                    None,
                ),
                "gtos_vnext_same_symbol_lifecycle_action": getattr(
                    intent,
                    "gtos_vnext_same_symbol_lifecycle_action",
                    None,
                ),
                "gtos_vnext_same_symbol_lifecycle_reason": getattr(
                    intent,
                    "gtos_vnext_same_symbol_lifecycle_reason",
                    None,
                ),
                "gtos_vnext_pretrade_cost_model": getattr(
                    intent,
                    "gtos_vnext_pretrade_cost_model",
                    None,
                ),
                "gtos_vnext_execution_policy_id": getattr(
                    intent,
                    "gtos_vnext_execution_policy_id",
                    None,
                ),
                "gtos_vnext_dynamic_policy_selected": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_selected",
                    None,
                ),
                "gtos_vnext_dynamic_policy_applied": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_applied",
                    None,
                ),
                "gtos_vnext_dynamic_policy_replaced_policy": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_replaced_policy",
                    None,
                ),
                "gtos_vnext_dynamic_policy_candidate_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_candidate_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_decision_status": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_decision_status",
                    None,
                ),
                "gtos_vnext_dynamic_policy_source_quality_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_source_quality_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_exit_management_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_exit_management_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_prop_action": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_prop_action",
                    None,
                ),
                "gtos_vnext_dynamic_policy_fixed_target_role": getattr(
                    intent,
                    "gtos_vnext_dynamic_policy_fixed_target_role",
                    None,
                ),
                "gtos_vnext_target_stop_geometry_v4": getattr(
                    intent,
                    "gtos_vnext_target_stop_geometry_v4",
                    None,
                ),
                "gtos_vnext_dynamic_target_stop_geometry_v4": getattr(
                    intent,
                    "gtos_vnext_target_stop_geometry_v4",
                    None,
                ),
                "gtos_vnext_target_stop_geometry_v4_packet": getattr(
                    intent,
                    "gtos_vnext_target_stop_geometry_v4",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_pct": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_pct",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_cell_id": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_cell_id",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_decision_basis": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_decision_basis",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_unresolved_reasons": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_unresolved_reasons",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_selected_policy": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_selected_policy",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_source_policy": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_source_policy",
                    None,
                ),
                "gtos_vnext_selected_cell_risk_policy_identity_status": getattr(
                    intent,
                    "gtos_vnext_selected_cell_risk_policy_identity_status",
                    None,
                ),
                "gtos_vnext_commission_model_status": getattr(
                    intent,
                    "gtos_vnext_commission_model_status",
                    None,
                ),
                "gtos_vnext_cost_model_source": getattr(
                    intent,
                    "gtos_vnext_cost_model_source",
                    None,
                ),
                "gtos_vnext_production_execution_path": getattr(
                    intent,
                    "gtos_vnext_production_execution_path",
                    None,
                ),
                "gtos_vnext_dynamic_be_trigger_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_be_trigger_r",
                    None,
                ),
                "gtos_vnext_dynamic_final_target_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_final_target_r",
                    None,
                ),
                "gtos_vnext_dynamic_broker_take_profit_mode": getattr(
                    intent,
                    "gtos_vnext_dynamic_broker_take_profit_mode",
                    None,
                ),
                "gtos_vnext_dynamic_no_broker_take_profit": getattr(
                    intent,
                    "gtos_vnext_dynamic_no_broker_take_profit",
                    None,
                ),
                "gtos_vnext_dynamic_be_trigger_price": getattr(
                    intent,
                    "gtos_vnext_dynamic_be_trigger_price",
                    None,
                ),
                "gtos_vnext_dynamic_final_target_price": getattr(
                    intent,
                    "gtos_vnext_dynamic_final_target_price",
                    None,
                ),
                "gtos_vnext_dynamic_trail_gap_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_trail_gap_r",
                    None,
                ),
                "gtos_vnext_dynamic_momentum_pullback_r": getattr(
                    intent,
                    "gtos_vnext_dynamic_momentum_pullback_r",
                    None,
                ),
                "gtos_vnext_dynamic_time_stop_bars": getattr(
                    intent,
                    "gtos_vnext_dynamic_time_stop_bars",
                    None,
                ),
                "gtos_vnext_book_native_exit_management": getattr(
                    intent,
                    "gtos_vnext_book_native_exit_management",
                    None,
                ),
                "gtos_vnext_source_event_hash": getattr(
                    intent,
                    "gtos_vnext_source_event_hash",
                    None,
                ),
                "gtos_vnext_source_event_details": getattr(
                    intent,
                    "gtos_vnext_source_event_details",
                    None,
                ),
                "gtos_vnext_activation_family": getattr(
                    intent,
                    "gtos_vnext_activation_family",
                    None,
                ),
                "gtos_vnext_origin_family": getattr(
                    intent,
                    "gtos_vnext_origin_family",
                    None,
                ),
                "gtos_vnext_selector_row_id": getattr(
                    intent,
                    "gtos_vnext_selector_row_id",
                    None,
                ),
                "gtos_vnext_selector_proof_hash": getattr(
                    intent,
                    "gtos_vnext_selector_proof_hash",
                    None,
                ),
        }
        fill_v4_decision = self._evaluate_execution_manager_v4(
            trade_params=fill_trade_params,
            pretrade_cost_model=fill_trade_params.get("gtos_vnext_pretrade_cost_model"),
            pending_context={
                "stage": "pending_fill_triggered",
                "pending_order_mode": getattr(intent, "pending_order_mode", None),
                "pending_created_time_utc": getattr(intent, "placed_time", None),
                "pending_candles_elapsed": getattr(intent, "candles_elapsed", None),
                "limit_price": intent.limit_price,
                "stop_loss": intent.stop_loss,
                "current_price": current_price,
                "original_sl_distance": original_sl_distance,
                "trigger_condition_met": True,
                "candle_time_utc": candle.get("time") if isinstance(candle, dict) else None,
            },
            trigger="limit_fill",
        )
        self._apply_execution_manager_v4_to_intent(intent, fill_v4_decision)
        if fill_v4_decision.should_block:
            block_reason = self._execution_manager_v4_block_reason(
                fill_v4_decision,
                pretrade_cost_model=fill_trade_params.get("gtos_vnext_pretrade_cost_model"),
            )
            logger.error(
                "Execution Manager V4 blocked pending fill before broker request: %s",
                block_reason,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="execution_manager_v4_blocked",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=True,
                tick=tick,
                current_price_used=current_price,
                order_send_attempted=False,
                order_send_success=False,
                reason=block_reason,
            )
            self.pending_intent = None
            return None

        trade_state = self.open_trade(
            trade_params=fill_trade_params,
            account_balance=account_balance,
            risk_pct_override=intent.risk_pct,
            sl_distance_override=original_sl_distance,
            trigger="limit_fill",
        )

        if trade_state:
            # Order succeeded -- clear intent and tag the trade
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="order_send_success_filled",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=True,
                tick=tick,
                current_price_used=current_price,
                order_send_attempted=True,
                order_send_success=True,
                trade_state=trade_state,
                reason="order_send_success",
            )
            self.pending_intent = None
            trade_state.trade_id = saved_trade_id.replace("lim_", "lim_filled_")
        else:
            # Order failed (spread, timeout, etc.) -- keep intent for retry
            logger.warning(
                "Limit fill order failed -- retaining intent for retry: %s",
                intent.trade_id,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="order_send_failed_retry",
                candles_elapsed_before=candles_elapsed_before,
                candles_elapsed_after=candles_elapsed_after,
                candle=candle,
                telemetry_context=telemetry_context,
                trigger_condition_met=True,
                tick=tick,
                current_price_used=current_price,
                order_send_attempted=True,
                order_send_success=False,
                reason="order_send_failed_retry",
            )

        return trade_state

    def cancel_limit_intent(self, reason: str = "manual") -> None:
        """Cancel active pending limit intent without executing."""
        if self.pending_intent is not None:
            intent = self.pending_intent
            logger.info(
                "Limit intent cancelled (%s): %s", reason, intent.trade_id,
            )
            self._record_pending_limit_lifecycle(
                intent=intent,
                intent_after_check="manual_or_system_cancelled",
                candles_elapsed_before=intent.candles_elapsed,
                candles_elapsed_after=intent.candles_elapsed,
                telemetry_context={
                    "source_branch": "execution_cancel_limit_intent",
                    "check_context": "cancel",
                },
                reason=reason,
            )
            self.pending_intent = None

    def safe_place_order(self, request: dict, timeout_seconds: int = 10) -> Optional[OrderResult]:
        """THE MOST IMPORTANT SAFETY FUNCTION.

        1. Write checkpoint
        2. Send order with timeout
        3. If timeout: check positions, adopt if filled, give up if not
        4. NEVER retry without checking positions first
        5. Clear checkpoint on completion
        """
        if not self._request_reduces_existing_position(request):
            try:
                self._enforce_runtime_halt_clear(
                    "safe_place_order",
                    {
                        "request_action": request.get("action"),
                        "request_symbol": request.get("symbol"),
                        "request_type": request.get("type"),
                        "request_position": request.get("position"),
                        "timeout_seconds": timeout_seconds,
                    },
                )
            except RuntimeHaltError as exc:
                result = self._runtime_halt_order_result(request)
                diagnostic = self._record_runtime_halt_diagnostic(
                    action="safe_place_order",
                    exc=exc,
                    extra={
                        "request_action": request.get("action"),
                        "request_symbol": request.get("symbol"),
                        "request_position": request.get("position"),
                    },
                )
                self._last_order_send_diagnostic = {
                    "diagnostic_version": "vnext_order_send_diagnostic_v1",
                    "time": diagnostic["time"],
                    "symbol": self.symbol,
                    "status": "runtime_halt_blocked_no_order_send",
                    "request": dict(request),
                    "result": self._result_snapshot(result),
                    "mt5_last_error": "not_read_due_to_runtime_halt_guard",
                    "positions_after": "not_read_due_to_runtime_halt_guard",
                    "symbol_info": "not_read_due_to_runtime_halt_guard",
                    "tick": "not_read_due_to_runtime_halt_guard",
                    "error": str(exc),
                    "runtime_halt_diagnostic": diagnostic,
                }
                logger.warning(
                    "Order send blocked by atomic runtime halt before checkpoint/send: %s",
                    diagnostic,
                )
                return result

        checkpoint = {
            "action": "place_order",
            "request": {k: v for k, v in request.items() if k != "type_filling"},
            "status": "pending",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._write_checkpoint(checkpoint)

        def _record_order_send_diagnostic(
            *,
            result: OrderResult | None,
            status: str,
            error: str | None = None,
        ) -> None:
            raw_mt5 = getattr(self.mt5, "_mt5", None)
            last_error_fn = getattr(raw_mt5, "last_error", None)
            last_error = None
            if callable(last_error_fn):
                try:
                    last_error = last_error_fn()
                except Exception as exc:  # noqa: BLE001
                    last_error = f"last_error_failed:{exc}"
            self._last_order_send_diagnostic = {
                "diagnostic_version": "vnext_order_send_diagnostic_v1",
                "time": datetime.now(timezone.utc).isoformat(),
                "symbol": self.symbol,
                "status": status,
                "request": dict(request),
                "result": self._result_snapshot(result),
                "mt5_last_error": last_error,
                "positions_after": self._positions_snapshot(),
                "symbol_info": self._symbol_info_snapshot(),
                "tick": self._tick_snapshot(),
                "error": error,
            }

        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.mt5.order_send, request)
                try:
                    result = future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Order timeout after {timeout_seconds}s -- checking positions")
                    time.sleep(2)
                    positions = self.mt5.get_positions(self.symbol)
                    new_positions = [p for p in positions if p.ticket not in self._known_tickets]
                    # Adopt ONLY the position matching THIS order's comment. In the per-(symbol, sleeve)
                    # book several sleeves/orders can place on one symbol concurrently, so new_positions[0]
                    # could be a DIFFERENT sleeve's (or a foreign) ticket. Require an exact comment match;
                    # if none, treat as no-fill — an existing position is picked up by the comment-routed
                    # manage_open_positions reconcile next tick (and the placement guard prevents a
                    # re-place), which is far safer than adopting the wrong ticket into this engine.
                    _req_comment = (request.get("comment") or "")
                    if _req_comment:
                        new_positions = [p for p in new_positions
                                         if (getattr(p, "comment", "") or "") == _req_comment]
                    if new_positions:
                        adopted = new_positions[0]
                        logger.info(f"Adopted position after timeout: ticket={adopted.ticket} "
                                    f"comment={getattr(adopted, 'comment', '')!r}")
                        self._known_tickets.add(adopted.ticket)
                        self._clear_checkpoint()
                        adopted_result = OrderResult(
                            retcode=10009, order=adopted.ticket,
                            volume=adopted.volume, price=adopted.price_open,
                            comment="adopted_after_timeout",
                        )
                        _record_order_send_diagnostic(
                            result=adopted_result,
                            status="adopted_after_timeout",
                        )
                        return OrderResult(
                            retcode=10009, order=adopted.ticket,
                            volume=adopted.volume, price=adopted.price_open,
                            comment="adopted_after_timeout",
                        )
                    else:
                        logger.info("No position found after timeout -- order did not fill")
                        self._clear_checkpoint()
                        _record_order_send_diagnostic(
                            result=None,
                            status="timeout_no_position",
                        )
                        return None
        except Exception as e:
            logger.error(f"Order send exception: {e}")
            self._clear_checkpoint()
            _record_order_send_diagnostic(
                result=None,
                status="order_send_exception",
                error=str(e),
            )
            return None

        if result.success:
            result_ticket = self._positive_int_or_none(getattr(result, "order", None))
            if result_ticket is not None:
                self._known_tickets.add(result_ticket)

        _record_order_send_diagnostic(
            result=result,
            status="success" if result.success else "retcode_failure",
        )
        self._clear_checkpoint()
        return result

    @staticmethod
    def _book_native_time_stop_owns_exit(trade: TradeState) -> bool:
        return bool(
            getattr(trade, "gtos_vnext_book_native_exit_management", False)
            and str(getattr(trade, "gtos_vnext_dynamic_policy_selected", "") or "").strip().lower() == "time_stop"
        )

    # === PARTIAL CLOSE MANAGEMENT ===

    def check_and_manage_trade(self, current_candle: dict) -> Optional[str]:
        """Manage an open position: check TP hits + manage partials/scale-out.

        NOTE: for the W7 ultimate_book this is polled on the LIVE tick (~60s, via book_owner._manage_engine
        every launcher tick), NOT only on the M15 close -- so exits react within ~1 poll rather than waiting
        for a bar close. Returns: "tp1_partial", "tp2_partial", "broker_closed", "monitoring", etc.
        """
        if self.active_trade is None:
            return None

        trade = self.active_trade

        positions = self.mt5.get_positions(self.symbol)
        our_position = None
        for p in positions:
            if p.ticket == trade.ticket:
                our_position = p
                break

        if our_position is None:
            # Post-fill MT5 propagation race guard: if we never saw this
            # ticket in positions_get, give MT5 a 5s grace window before
            # accepting "broker closed it". This addresses the live race
            # observed 2026-04-29 NAS100 ticket 234432798 — order_send
            # returned at 23:15:05.448 and positions_get at 23:15:05.461
            # (13ms later) returned an empty list because MT5's internal
            # state hadn't yet propagated. Without the guard, the orch
            # falsely retired active_trade and lost track of a real LIVE
            # position. After ``position_confirmed`` flips True (the first
            # time we DO see the position), this branch behaves as before
            # — a true broker close from then on retires the trade.
            if not trade.position_confirmed:
                from datetime import datetime, timezone
                try:
                    age_s = (
                        datetime.now(timezone.utc)
                        - datetime.fromisoformat(trade.entry_time)
                    ).total_seconds()
                except (ValueError, TypeError):
                    age_s = 999.0  # unparseable → don't trip the guard
                if age_s < 5.0:
                    logger.info(
                        "Position %d not yet visible to MT5 (open %.3fs ago) -- "
                        "deferring broker_closed check (post-fill propagation race "
                        "guard)",
                        trade.ticket, age_s,
                    )
                    return "monitoring"
            if self._vnext_broker_close_requires_deal_confirmation(trade):
                close_deal_status = self._broker_close_deal_confirmation_status(trade)
                if close_deal_status != "CLOSE_DEAL_FOUND":
                    logger.warning(
                        "Position %d absent from positions_get but MT5 close deal "
                        "confirmation status is %s; deferring broker_closed for "
                        "vNext lifecycle truth",
                        trade.ticket,
                        close_deal_status,
                    )
                    return "monitoring"
            logger.info(f"Position {trade.ticket} no longer exists -- closed by broker")
            self._record_close("broker_closed")
            self.active_trade = None
            return "broker_closed"

        # Mark position as confirmed-seen — closes the propagation race
        # guard above. From this point onward, an empty positions_get IS
        # interpreted as a true broker close.
        trade.position_confirmed = True
        trade.current_volume = our_position.volume

        tick = self.mt5.get_tick(self.symbol)
        if tick is None:
            return "monitoring"

        current_price = tick.bid if trade.direction == "LONG" else tick.ask

        # W7 ultimate_book trades own their exit at the broker (SL=-1R / TP=final_target_r) plus the
        # per-trade time-stop (check_time_stop_and_close, driven by book_owner). For those trades the
        # per-symbol orchestrator exit overlays (profit-harvest MFE capture, exit_policy_v4, and the
        # momentum/trailing dispatch below) MUST NOT run — they would overwrite the sleeve's validated
        # native exit. The TP1/TP2 partial checks remain (partial_be_runner's _execute_tp1_partial).
        # For every non-book trade the flag is False, so this path is unchanged from before.
        if not trade.gtos_vnext_book_native_exit_management:
            action = self._manage_vnext_profit_harvest_mfe_capture_v4(trade, current_price)
            if action:
                return action

            v4_action = self._manage_exit_policy_v4(
                trade,
                current_price=current_price,
                current_candle=current_candle or {},
                position=our_position,
            )
            if v4_action:
                return v4_action

        if self._book_native_time_stop_owns_exit(trade):
            return "monitoring"

        # Check TP1
        if not trade.tp1_hit and float(trade.take_profit_1 or 0.0) > 0.0:
            tp1_hit = ((trade.direction == "LONG" and current_price >= trade.take_profit_1) or
                       (trade.direction == "SHORT" and current_price <= trade.take_profit_1))
            if tp1_hit:
                return self._execute_tp1_partial(trade, our_position)

        # Check TP2
        if trade.tp1_hit and not trade.tp2_hit and trade.take_profit_2 > 0:
            tp2_hit = ((trade.direction == "LONG" and current_price >= trade.take_profit_2) or
                       (trade.direction == "SHORT" and current_price <= trade.take_profit_2))
            if tp2_hit:
                return self._execute_tp2_partial(trade, our_position)

        if trade.tp1_hit:
            if self._vnext_trailing_runner_active(trade):
                action = self._manage_vnext_trailing_runner(trade, current_price)
                if action:
                    return action
        if trade.tp1_hit and not trade.gtos_vnext_book_native_exit_management:
            if self._vnext_momentum_exhaustion_active(trade):
                action = self._manage_vnext_momentum_exhaustion(trade, current_price)
                if action:
                    return action

        return "monitoring"

    def _resolve_close_price(self, result, direction: str, context: str) -> float:
        """Resolve the effective close price for a successful close order_send.

        MT5 can return ``result.price == 0.0`` on some broker/close paths
        (observed USDJPY 2026-04-23 09:30 UTC on trailing-BE force close;
        A2 commit ``1b6ac3b`` patched ``close_position`` inline).  This
        helper mirrors that fallback for the partial-close paths (TP1 full,
        TP1 partial, TP2 partial) where ``result.price`` is written into
        ``partial_close_events`` event logs used for forensic audit / P&L
        attribution.  For a LONG close we hit the bid; for a SHORT close we
        lift the ask -- matching MT5 semantics for TRADE_ACTION_DEAL on an
        existing position.  If the tick is also unavailable, record 0.0
        (degraded data) and emit a second warning -- same contract as A2.

        ``context`` is included in the warning messages so TP1/TP2 paths
        are distinguishable in logs.
        """
        close_price = result.price
        if not close_price:
            tick = self.mt5.get_tick(self.symbol)
            if tick is not None:
                fallback = tick.bid if direction == "LONG" else tick.ask
                logger.warning(
                    "%s close price returned 0.0 from MT5; using current "
                    "tick price %.5f as fallback",
                    context, fallback,
                )
                close_price = fallback
            else:
                logger.warning(
                    "%s close price returned 0.0 from MT5 and no tick "
                    "available -- recording 0.0 (degraded data)",
                    context,
                )
        return close_price

    def _close_quote_snapshot(self, direction: str) -> tuple[Optional[float], Optional[float]]:
        """Return expected close price and spread before submitting a close.

        Observation-only: the returned values are used only for telemetry.
        LONG exits sell into bid; SHORT exits buy at ask.
        """
        try:
            tick = self.mt5.get_tick(self.symbol)
            if tick is None:
                return None, None
            expected = tick.bid if direction == "LONG" else tick.ask
            return expected, getattr(tick, "spread_cents", None)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Close quote snapshot failed (non-blocking): %s", exc)
            return None, None

    @staticmethod
    def _time_in_trade_minutes(entry_time: str) -> Optional[int]:
        if not entry_time:
            return None
        try:
            entry_dt = datetime.fromisoformat(entry_time.replace("Z", "+00:00"))
        except ValueError:
            return None
        if entry_dt.tzinfo is None:
            entry_dt = entry_dt.replace(tzinfo=timezone.utc)
        minutes = int((datetime.now(timezone.utc) - entry_dt).total_seconds() / 60)
        if minutes < 0:
            return None
        return minutes

    def _close_event_metadata(
        self,
        *,
        trade: TradeState,
        result,
        close_reason: str,
        close_event_type: str,
        close_price: float,
        close_volume: float,
        expected_close_price: Optional[float],
        spread_at_request: Optional[float],
        partial_close: bool,
        remaining_volume: Optional[float] = None,
        close_ticket: Optional[int] = None,
    ) -> dict:
        ticket = close_ticket if close_ticket is not None else trade.ticket
        mt5_deal_id = self._positive_int_or_none(getattr(result, "deal", None))
        return {
            "position_ticket": ticket,
            "close_reason": close_reason,
            "close_event_type": close_event_type,
            "mt5_order_id": getattr(result, "order", None),
            "mt5_deal_id": mt5_deal_id,
            "raw_mt5_deal_id": getattr(result, "deal", None),
            "commission": None,
            "swap": None,
            "sl_at_breakeven": trade.sl_at_breakeven,
            "be_status_at_close_request": trade.sl_at_breakeven,
            "time_in_trade_minutes": self._time_in_trade_minutes(trade.entry_time),
            "expected_close_price": expected_close_price,
            "spread_at_request": spread_at_request,
            "partial_close": partial_close,
            "remaining_volume": remaining_volume,
            "close_comment": getattr(result, "comment", None),
            "close_price": close_price,
            "volume_closed": close_volume,
        }

    @staticmethod
    def _trade_candidate_id(trade: TradeState) -> str | None:
        details = getattr(trade, "gtos_vnext_source_event_details", None)
        if isinstance(details, dict):
            for key in ("candidate_id", "selector_row_id", "source_candidate_id"):
                value = details.get(key)
                if value not in (None, ""):
                    return str(value)
        for attr in (
            "gtos_vnext_selector_row_id",
            "gtos_vnext_scheduler_v4_selected_candidate_id",
            "gtos_vnext_scheduler_v4_current_candidate_id",
        ):
            value = getattr(trade, attr, None)
            if value not in (None, ""):
                return str(value)
        return None

    def _record_close_slippage_event(
        self,
        *,
        trade: TradeState,
        result,
        close_reason: str,
        close_event_type: str,
        close_price: float,
        close_volume: float,
        expected_close_price: Optional[float],
        spread_at_request: Optional[float],
        partial_close: bool,
        remaining_volume: Optional[float] = None,
        close_ticket: Optional[int] = None,
    ) -> dict:
        """Write close-side telemetry and return metadata for trade records."""
        metadata = self._close_event_metadata(
            trade=trade,
            result=result,
            close_reason=close_reason,
            close_event_type=close_event_type,
            close_price=close_price,
            close_volume=close_volume,
            expected_close_price=expected_close_price,
            spread_at_request=spread_at_request,
            partial_close=partial_close,
            remaining_volume=remaining_volume,
            close_ticket=close_ticket,
        )
        close_request_time_utc = datetime.now(timezone.utc).isoformat()
        metadata["close_request_time_utc"] = close_request_time_utc
        close_accounting = self._lookup_close_deal_accounting(
            trade=trade,
            result=result,
            close_ticket=close_ticket,
            closed_at_utc=close_request_time_utc,
        )
        metadata.update(close_accounting)
        account_history_reconciled = (
            close_accounting.get("close_account_history_lookup_status")
            == "RECONCILED_FROM_ACCOUNT_HISTORY"
        )
        close_broker_profit = None
        close_commission = None
        close_swap = None
        if account_history_reconciled:
            close_broker_profit = close_accounting.get("broker_profit")
            close_commission = close_accounting.get("commission")
            close_swap = close_accounting.get("swap")
        effective_close_price = close_price
        if account_history_reconciled and close_accounting.get("broker_exit_price") not in (None, 0, 0.0):
            effective_close_price = close_accounting["broker_exit_price"]
        try:
            record_close_slippage(
                namespace=self._runtime_namespace,
                candidate_id=self._trade_candidate_id(trade),
                ticket=close_ticket if close_ticket is not None else trade.ticket,
                symbol=self._persist_symbol,
                direction=trade.direction,
                requested_price=expected_close_price,
                fill_price=effective_close_price,
                close_reason=close_reason,
                close_event_type=close_event_type,
                spread_at_request=spread_at_request,
                volume_closed=close_volume,
                initial_volume=trade.initial_volume,
                remaining_volume=remaining_volume,
                entry_price=trade.entry_price,
                stop_loss=trade.stop_loss,
                sl_distance=trade.sl_distance,
                entry_time=trade.entry_time,
                sl_at_breakeven=trade.sl_at_breakeven,
                partial_close=partial_close,
                mt5_order_id=close_accounting.get("order_ticket") or metadata.get("mt5_order_id"),
                mt5_deal_id=close_accounting.get("deal_ticket") or metadata.get("mt5_deal_id"),
                commission=close_commission,
                swap=close_swap,
                broker_profit=close_broker_profit,
                broker_exit_aggregate_profit=close_accounting.get("broker_exit_aggregate_profit"),
                broker_exit_aggregate_commission=close_accounting.get("broker_exit_aggregate_commission"),
                broker_exit_aggregate_swap=close_accounting.get("broker_exit_aggregate_swap"),
                broker_exit_aggregate_fee=close_accounting.get("broker_exit_aggregate_fee"),
                broker_exit_aggregate_net_profit=close_accounting.get("broker_exit_aggregate_net_profit"),
                cash_risk_amount=getattr(trade, "cash_risk_amount", None),
                executed_target_price=trade.take_profit_1,
                source_repair_identity=getattr(trade, "source_repair_identity", None),
                dynamic_exit_action_timeline=getattr(
                    trade,
                    "partial_close_events",
                    None,
                ),
                close_comment=getattr(result, "comment", None),
                requested_price_status=(
                    "CLOSE_QUOTE_CAPTURED"
                    if expected_close_price is not None
                    else "CLOSE_QUOTE_SOURCE_NOT_CAPTURED"
                ),
                close_time=(
                    close_accounting.get("broker_exit_time_utc")
                    if account_history_reconciled
                    else None
                ),
                accounting_source=(
                    close_accounting.get("accounting_source")
                    if account_history_reconciled
                    else "EXECUTION_ORDER_RESULT"
                ),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Close-side slippage telemetry failed (non-blocking): %s", exc)
        return metadata

    def _current_progress_r(self, trade: TradeState, current_price: float) -> float:
        if trade.sl_distance <= 0:
            return 0.0
        if trade.direction == "LONG":
            return (current_price - trade.entry_price) / trade.sl_distance
        return (trade.entry_price - current_price) / trade.sl_distance

    def _exit_policy_v4_config(self) -> ExitPolicyConfigV4:
        return ExitPolicyConfigV4.from_runtime_config(
            self.config.get("gtos_vnext_runtime", {}) if isinstance(self.config, dict) else {}
        )

    @staticmethod
    def _parse_exit_policy_time(value) -> Optional[datetime]:
        if value in (None, ""):
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    def _exit_policy_v4_current_time(
        self,
        current_candle: dict,
    ) -> tuple[Optional[datetime], str]:
        for key in (
            "time_utc",
            "timestamp_utc",
            "candle_time_utc",
            "latest_closed_m15_utc",
            "time",
            "timestamp",
        ):
            dt = self._parse_exit_policy_time(current_candle.get(key))
            if dt is not None:
                return dt, f"current_candle.{key}"
        return datetime.now(timezone.utc), "live_runtime_clock_now"

    def _exit_policy_v4_bars_elapsed(
        self,
        trade: TradeState,
        current_candle: dict,
    ) -> tuple[Optional[int], str]:
        entry_dt = self._parse_exit_policy_time(trade.entry_time)
        if entry_dt is None:
            return None, "missing_or_unparseable_entry_time"
        current_dt, source = self._exit_policy_v4_current_time(current_candle)
        if current_dt is None or current_dt < entry_dt:
            return None, "missing_or_invalid_current_time"
        return int((current_dt - entry_dt).total_seconds() // (15 * 60)), source

    @staticmethod
    def _exit_policy_v4_current_stop_r(
        trade: TradeState,
        position: PositionInfo,
    ) -> Optional[float]:
        if trade.sl_distance <= 0:
            return None
        try:
            broker_stop = float(getattr(position, "sl", 0.0) or 0.0)
        except (TypeError, ValueError):
            broker_stop = 0.0
        stop_loss = broker_stop if broker_stop > 0 else trade.stop_loss
        if trade.direction == "LONG":
            return (stop_loss - trade.entry_price) / trade.sl_distance
        if trade.direction == "SHORT":
            return (trade.entry_price - stop_loss) / trade.sl_distance
        return None

    def _update_abort_below_close_streak(
        self,
        trade: TradeState,
        *,
        config,
        current_candle: dict,
    ) -> Optional[int]:
        """Maintain the consecutive below-threshold close streak per closed bar.

        Returns the streak when the adverse-close abort rule is fully armed,
        else None (the evaluator then treats the rule as disabled). Updates at
        most once per candle (candle-time marker) so 60s monitoring loops do
        not over-count; uses the BAR CLOSE progress for replay parity with
        ``simulate_policy``'s consecutive semantics.
        """

        if (
            config.abort_close_below_r is None
            or config.abort_consecutive_bars is None
            or config.abort_min_mfe_r is None
        ):
            return None
        candle_time = str(current_candle.get("time") or "")
        close_price = self._safe_float(current_candle.get("close"))
        if not candle_time or close_price is None or trade.sl_distance <= 0:
            return trade.gtos_vnext_abort_below_close_streak
        if candle_time != (trade.gtos_vnext_abort_streak_candle_time or ""):
            close_progress = self._current_progress_r(trade, close_price)
            if close_progress <= float(config.abort_close_below_r):
                trade.gtos_vnext_abort_below_close_streak += 1
            else:
                trade.gtos_vnext_abort_below_close_streak = 0
            trade.gtos_vnext_abort_streak_candle_time = candle_time
        return trade.gtos_vnext_abort_below_close_streak

    def _exit_policy_v4_input(
        self,
        trade: TradeState,
        *,
        current_price: float,
        current_candle: dict,
        position: PositionInfo,
        consecutive_closes_below_abort_r: Optional[int] = None,
    ) -> ExitPolicyInputV4:
        progress_r = self._current_progress_r(trade, current_price)
        trade.gtos_vnext_dynamic_mfe_r = max(
            float(trade.gtos_vnext_dynamic_mfe_r or 0.0),
            progress_r,
        )
        trade.gtos_vnext_dynamic_mae_r = min(
            float(trade.gtos_vnext_dynamic_mae_r or 0.0),
            progress_r,
        )
        bars_elapsed, clock_source = self._exit_policy_v4_bars_elapsed(
            trade,
            current_candle,
        )
        partial_closed = bool(
            trade.tp1_hit
            or any(
                "PARTIAL" in str(event.get("type") or "")
                for event in (trade.partial_close_events or [])
                if isinstance(event, dict)
            )
        )
        return ExitPolicyInputV4(
            ticket=trade.ticket,
            symbol=self.symbol,
            direction=trade.direction,
            entry_time_utc=trade.entry_time,
            bars_elapsed=bars_elapsed,
            current_progress_r=progress_r if trade.sl_distance > 0 else None,
            mfe_r=trade.gtos_vnext_dynamic_mfe_r if trade.sl_distance > 0 else None,
            mae_r=trade.gtos_vnext_dynamic_mae_r if trade.sl_distance > 0 else None,
            current_stop_r=self._exit_policy_v4_current_stop_r(trade, position),
            partial_closed=partial_closed,
            sl_at_breakeven=trade.sl_at_breakeven,
            current_volume=float(getattr(position, "volume", 0.0) or 0.0),
            initial_volume=float(trade.initial_volume or 0.0),
            partial_close_allowed=self._vnext_partial_be_runner_active(trade),
            ticket_bound_state=bool(trade.ticket and getattr(position, "ticket", None) == trade.ticket),
            broker_position_confirmed=bool(trade.position_confirmed),
            path_source_status="live_tick_current_price_source_bound",
            clock_source_status=clock_source,
            lifecycle_source_status="broker_position_confirmed_ticket_bound",
            cost_source_status="cost_engine_handoff_not_recomputed_by_exit_policy_v4",
            thesis_invalidation_status=str(
                current_candle.get("thesis_invalidation_status")
                or current_candle.get("gtos_vnext_thesis_invalidation_status")
                or "source_not_available"
            ),
            opposite_signal_strength=self._safe_float(
                current_candle.get("opposite_signal_strength")
                or current_candle.get("gtos_vnext_opposite_signal_strength")
            ),
            opportunity_cost_r=self._safe_float(
                current_candle.get("opportunity_cost_r")
                or current_candle.get("gtos_vnext_opportunity_cost_r")
                or current_candle.get("scheduler_opportunity_cost_r")
            ),
            scheduler_regret_r=self._safe_float(
                current_candle.get("scheduler_regret_r")
                or current_candle.get("gtos_vnext_scheduler_regret_r")
                or current_candle.get("scheduler_allocation_regret_r")
            ),
            competing_candidate_ev_r=self._safe_float(
                current_candle.get("competing_candidate_ev_r")
                or current_candle.get("gtos_vnext_competing_candidate_ev_r")
                or current_candle.get("best_competing_candidate_ev_r")
            ),
            opportunity_cost_source_status=str(
                current_candle.get("opportunity_cost_source_status")
                or current_candle.get("gtos_vnext_opportunity_cost_source_status")
                or "not_provided"
            ),
            scheduler_regret_source_status=str(
                current_candle.get("scheduler_regret_source_status")
                or current_candle.get("gtos_vnext_scheduler_regret_source_status")
                or "not_provided"
            ),
            consecutive_closes_below_abort_r=consecutive_closes_below_abort_r,
        )

    @staticmethod
    def _exit_policy_v4_event(decision: ExitPolicyDecisionV4) -> dict:
        return {
            "type": "EXIT_POLICY_V4_DECISION",
            "time": datetime.now(timezone.utc).isoformat(),
            "action": decision.action,
            "reason": decision.reason,
            "status": decision.status,
            "target_stop_r": decision.target_stop_r,
            "close_reason": decision.close_reason,
            "partial_close_ratio": decision.partial_close_ratio,
            "source_completeness_status": decision.source_completeness_status,
            "source_gaps": list(decision.source_gaps),
            "evidence_class": decision.evidence_class,
            "runtime_effect_boundary": decision.runtime_effect_boundary,
            "semantic_handoffs": list(decision.semantic_handoffs),
        }

    def _manage_exit_policy_v4(
        self,
        trade: TradeState,
        *,
        current_price: float,
        current_candle: dict,
        position: PositionInfo,
    ) -> Optional[str]:
        if not trade.gtos_vnext_dynamic_policy_applied:
            return None
        config = self._exit_policy_v4_config()
        if not config.enabled or not config.apply_to_execution:
            return None
        abort_streak = self._update_abort_below_close_streak(
            trade,
            config=config,
            current_candle=current_candle,
        )
        policy_input = self._exit_policy_v4_input(
            trade,
            current_price=current_price,
            current_candle=current_candle,
            position=position,
            consecutive_closes_below_abort_r=abort_streak,
        )
        decision = evaluate_exit_policy_v4(config, policy_input)
        if decision.action == "HOLD":
            if decision.status == "source_gap_fail_closed":
                trade.partial_close_events.append(self._exit_policy_v4_event(decision))
            return None

        trade.partial_close_events.append(self._exit_policy_v4_event(decision))

        if decision.action == "PARTIAL_CLOSE_TO_BE":
            if not self._vnext_partial_be_runner_active(trade):
                return "exit_policy_v4_partial_blocked_policy_not_partial_runner"
            return self._execute_tp1_partial(trade, position)

        if decision.action in {"MOVE_STOP_TO_BE", "RAISE_TRAILING_STOP"}:
            target_r = 0.0 if decision.target_stop_r is None else decision.target_stop_r
            if self._move_sl_to_dynamic_r(
                trade,
                trade.ticket,
                target_r,
                reason=f"exit_policy_v4:{decision.reason}",
            ):
                if decision.action == "MOVE_STOP_TO_BE":
                    return "exit_policy_v4_moved_stop_to_be"
                return "exit_policy_v4_raised_trailing_stop"
            if decision.action == "MOVE_STOP_TO_BE":
                return "exit_policy_v4_move_stop_to_be_failed"
            return "exit_policy_v4_raise_trailing_stop_failed"

        if decision.action == "TIGHTEN_STOP_LOSS_ABORT":
            if decision.target_stop_r is None:
                return "exit_policy_v4_abort_tighten_missing_target_stop_r"
            if self._move_sl_to_dynamic_r(
                trade,
                trade.ticket,
                float(decision.target_stop_r),
                reason=f"exit_policy_v4:{decision.reason}",
            ):
                return "exit_policy_v4_abort_tightened_stop"
            return "exit_policy_v4_abort_tighten_stop_failed"

        if decision.action in {
            "CLOSE_GIVEBACK",
            "CLOSE_STALE_THESIS",
            "CLOSE_TIME_STOP",
            "CLOSE_EARLY_LOSS_ABORT",
        }:
            close_reason = decision.close_reason or decision.reason
            if self.close_position(close_reason):
                self._notify_vnext_lifecycle(
                    trade,
                    "exit policy close",
                    price=current_price,
                    result_r=policy_input.current_progress_r,
                    detail=close_reason,
                )
                return close_reason
            return f"{close_reason}_close_failed"

        return None

    def _trade_price_from_r(self, trade: TradeState, target_r: float) -> float:
        return self._target_price_from_r(
            direction=trade.direction,
            entry_price=trade.entry_price,
            sl_distance=trade.sl_distance,
            target_r=target_r,
        )

    def _move_sl_to_dynamic_r(
        self,
        trade: TradeState,
        ticket: int,
        target_r: float,
        *,
        reason: str,
    ) -> bool:
        target_r = float(target_r)
        new_sl = self._trade_price_from_r(trade, target_r)
        old_stop_loss = trade.stop_loss
        if old_stop_loss:
            would_worsen = (
                trade.direction == "LONG" and new_sl <= old_stop_loss
            ) or (
                trade.direction == "SHORT" and new_sl >= old_stop_loss
            )
            if would_worsen:
                return False
        for attempt in range(1, self.SL_MODIFY_MAX_ATTEMPTS + 1):
            if self._modify_sl(
                ticket,
                new_sl,
                trade=trade,
                modify_reason=reason,
            ):
                trade.stop_loss = new_sl
                trade.sl_at_breakeven = target_r >= 0.0
                trade.gtos_vnext_dynamic_trail_stop_r = target_r
                trade.partial_close_events.append({
                    "type": "VNEXT_DYNAMIC_SL_MODIFY_SUCCESS",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "ticket": ticket,
                    "reason": reason,
                    "attempt": attempt,
                    "old_stop_loss": old_stop_loss,
                    "new_stop_loss": new_sl,
                    "target_r": target_r,
                    "policy": trade.gtos_vnext_dynamic_policy_selected,
                    "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                })
                if abs(target_r) <= 1e-9:
                    self._notify_vnext_lifecycle(
                        trade,
                        "BE transition",
                        price=new_sl,
                        detail=reason,
                    )
                return True
            if attempt < self.SL_MODIFY_MAX_ATTEMPTS:
                self._sl_modify_backoff(attempt - 1)
        trade.partial_close_events.append({
            "type": "VNEXT_DYNAMIC_SL_MODIFY_FAILED",
            "time": datetime.now(timezone.utc).isoformat(),
            "ticket": ticket,
            "reason": reason,
            "attempts": self.SL_MODIFY_MAX_ATTEMPTS,
            "old_stop_loss": old_stop_loss,
            "requested_stop_loss": new_sl,
            "actual_stop_loss_preserved": trade.stop_loss,
            "target_r": target_r,
            "policy": trade.gtos_vnext_dynamic_policy_selected,
            "execution_policy_id": trade.gtos_vnext_execution_policy_id,
            "last_sltp_modify_diagnostic": self._last_sltp_modify_diagnostic,
        })
        logger.error(
            "GTOS vNext dynamic SL modify failed for %s ticket=%d target_r=%.3f; "
            "existing SL preserved.",
            reason,
            ticket,
            target_r,
        )
        try:
            from src.notifications import notify_alert
            notify_alert(
                f"[CRITICAL] vNext dynamic SL modify failed after "
                f"{self.SL_MODIFY_MAX_ATTEMPTS} attempts on {self.symbol} "
                f"ticket={ticket} policy={trade.gtos_vnext_dynamic_policy_selected}. "
                f"Existing SL ({trade.stop_loss:.5f}) preserved; position remains open."
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "notify_alert failed for vNext dynamic SL-modify failure "
                "(non-fatal): %s",
                exc,
            )
        return False

    def _start_vnext_trailing_runner(self, trade: TradeState) -> str:
        trade.tp1_hit = True
        trigger_r = max(0.0, float(trade.gtos_vnext_dynamic_be_trigger_r or 0.0))
        trade.gtos_vnext_dynamic_mfe_r = max(trade.gtos_vnext_dynamic_mfe_r, trigger_r)
        trail_gap = max(0.01, float(trade.gtos_vnext_dynamic_trail_gap_r or 0.5))
        trail_stop_r = max(0.0, trade.gtos_vnext_dynamic_mfe_r - trail_gap)
        initial_sl_modify_success = self._move_sl_to_dynamic_r(
            trade,
            trade.ticket,
            trail_stop_r,
            reason="vnext_trailing_runner_trigger",
        )
        trade.partial_close_events.append({
            "type": "TP1_TRAILING_RUNNER_STARTED",
            "time": datetime.now(timezone.utc).isoformat(),
            "trigger_r": trade.gtos_vnext_dynamic_be_trigger_r,
            "trail_gap_r": trail_gap,
            "trail_stop_r": trade.gtos_vnext_dynamic_trail_stop_r,
            "final_target_r": trade.gtos_vnext_dynamic_final_target_r,
            "execution_policy_id": trade.gtos_vnext_execution_policy_id,
            "initial_sl_modify_success": initial_sl_modify_success,
            "residual_risk_status": (
                "dynamic_sl_modified"
                if initial_sl_modify_success
                else "initial_dynamic_sl_modify_failed_original_sl_preserved"
            ),
        })
        if initial_sl_modify_success:
            return "tp1_trailing_runner_started"
        return "tp1_trailing_runner_started_sl_modify_failed"

    def _start_vnext_momentum_exhaustion(self, trade: TradeState) -> str:
        trade.tp1_hit = True
        trigger_r = max(0.0, float(trade.gtos_vnext_dynamic_be_trigger_r or 0.0))
        trade.gtos_vnext_dynamic_mfe_r = max(trade.gtos_vnext_dynamic_mfe_r, trigger_r)
        initial_sl_modify_success = self._move_sl_to_dynamic_r(
            trade,
            trade.ticket,
            0.0,
            reason="vnext_momentum_exhaustion_be_safety",
        )
        trade.partial_close_events.append({
            "type": "TP1_MOMENTUM_EXHAUSTION_STARTED",
            "time": datetime.now(timezone.utc).isoformat(),
            "trigger_r": trade.gtos_vnext_dynamic_be_trigger_r,
            "pullback_r": trade.gtos_vnext_dynamic_momentum_pullback_r,
            "final_target_r": trade.gtos_vnext_dynamic_final_target_r,
            "execution_policy_id": trade.gtos_vnext_execution_policy_id,
            "initial_sl_modify_success": initial_sl_modify_success,
            "residual_risk_status": (
                "dynamic_sl_modified"
                if initial_sl_modify_success
                else "initial_dynamic_sl_modify_failed_original_sl_preserved"
            ),
        })
        if initial_sl_modify_success:
            return "tp1_momentum_exhaustion_started"
        return "tp1_momentum_exhaustion_started_sl_modify_failed"

    def _manage_vnext_trailing_runner(
        self,
        trade: TradeState,
        current_price: float,
    ) -> Optional[str]:
        progress_r = self._current_progress_r(trade, current_price)
        if progress_r <= trade.gtos_vnext_dynamic_mfe_r:
            return None
        trade.gtos_vnext_dynamic_mfe_r = progress_r
        trail_gap = max(0.01, float(trade.gtos_vnext_dynamic_trail_gap_r or 0.5))
        desired_stop_r = max(0.0, progress_r - trail_gap)
        if desired_stop_r <= trade.gtos_vnext_dynamic_trail_stop_r + 1e-9:
            return None
        if self._move_sl_to_dynamic_r(
            trade,
            trade.ticket,
            desired_stop_r,
            reason="vnext_trailing_runner_progress",
        ):
            return "vnext_trailing_runner_sl_modified"
        return "vnext_trailing_runner_sl_modify_failed"

    def _manage_vnext_momentum_exhaustion(
        self,
        trade: TradeState,
        current_price: float,
    ) -> Optional[str]:
        progress_r = self._current_progress_r(trade, current_price)
        if progress_r > trade.gtos_vnext_dynamic_mfe_r:
            trade.gtos_vnext_dynamic_mfe_r = progress_r
            return None
        pullback_r = max(0.01, float(trade.gtos_vnext_dynamic_momentum_pullback_r or 0.4))
        exit_threshold_r = max(0.0, trade.gtos_vnext_dynamic_mfe_r - pullback_r)
        if (
            trade.gtos_vnext_dynamic_mfe_r
            >= float(trade.gtos_vnext_dynamic_be_trigger_r or 0.0)
            and progress_r <= exit_threshold_r
        ):
            trade.partial_close_events.append({
                "type": "MOMENTUM_EXHAUSTION_PULLBACK_EXIT_SIGNAL",
                "time": datetime.now(timezone.utc).isoformat(),
                "mfe_r": trade.gtos_vnext_dynamic_mfe_r,
                "current_progress_r": progress_r,
                "exit_threshold_r": exit_threshold_r,
                "pullback_r": pullback_r,
                "execution_policy_id": trade.gtos_vnext_execution_policy_id,
            })
            if self.close_position("vnext_momentum_exhaustion_pullback"):
                self._notify_vnext_lifecycle(
                    trade,
                    "momentum pullback close",
                    price=current_price,
                    result_r=progress_r,
                    detail="vnext_momentum_exhaustion_pullback",
                )
                return "vnext_momentum_exhaustion_pullback"
            return "vnext_momentum_exhaustion_pullback_close_failed"
        return None

    def _manage_vnext_profit_harvest_mfe_capture_v4(
        self,
        trade: TradeState,
        current_price: float,
    ) -> Optional[str]:
        if not self._vnext_profit_harvest_mfe_capture_v4_active(trade):
            return None
        if trade.tp1_hit:
            return None

        progress_r = self._current_progress_r(trade, current_price)
        trade.gtos_vnext_profit_harvest_last_progress_r = progress_r
        previous_mfe = trade.gtos_vnext_profit_harvest_mfe_r
        trade.gtos_vnext_profit_harvest_mfe_r = max(previous_mfe, progress_r)
        mfe_r = trade.gtos_vnext_profit_harvest_mfe_r

        primary_trigger_r = float(trade.gtos_vnext_dynamic_be_trigger_r or 0.0)
        min_mfe_r = max(0.01, float(trade.gtos_vnext_profit_harvest_min_mfe_r or 0.25))
        if (
            primary_trigger_r > 0
            and progress_r >= primary_trigger_r
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            in SUPPORTED_VNEXT_DYNAMIC_EXECUTION_POLICIES
        ):
            return None
        if mfe_r < min_mfe_r:
            return None

        if not trade.gtos_vnext_profit_harvest_triggered:
            trade.gtos_vnext_profit_harvest_triggered = True
            trade.partial_close_events.append({
                "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_ARMED",
                "time": datetime.now(timezone.utc).isoformat(),
                "mfe_r": mfe_r,
                "current_progress_r": progress_r,
                "min_mfe_r": min_mfe_r,
                "primary_trigger_r": primary_trigger_r,
                "policy": trade.gtos_vnext_dynamic_policy_selected,
                "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                "result_use_status": "runtime_management_event_not_counterfactual_pnl",
            })

        giveback_r = mfe_r - progress_r
        close_on_giveback_r = max(
            0.01,
            float(trade.gtos_vnext_profit_harvest_close_on_giveback_r or 0.50),
        )
        if giveback_r >= close_on_giveback_r:
            trade.partial_close_events.append({
                "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_GIVEBACK_CLOSE_SIGNAL",
                "time": datetime.now(timezone.utc).isoformat(),
                "mfe_r": mfe_r,
                "current_progress_r": progress_r,
                "giveback_r": giveback_r,
                "close_on_giveback_r": close_on_giveback_r,
                "policy": trade.gtos_vnext_dynamic_policy_selected,
                "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                "result_use_status": "runtime_management_event_not_counterfactual_pnl",
            })
            if self.close_position("vnext_profit_harvest_mfe_capture_v4_giveback"):
                trade.gtos_vnext_profit_harvest_last_action = "giveback_close"
                return "vnext_profit_harvest_mfe_capture_v4_giveback_close"
            trade.gtos_vnext_profit_harvest_last_action = "giveback_close_failed"
            return "vnext_profit_harvest_mfe_capture_v4_giveback_close_failed"

        stale_minutes = trade.gtos_vnext_profit_harvest_stale_minutes
        if stale_minutes is not None:
            age_minutes = self._time_in_trade_minutes(trade.entry_time)
            stale_min_mfe_r = max(
                0.01,
                float(trade.gtos_vnext_profit_harvest_stale_min_mfe_r or min_mfe_r),
            )
            stale_close_below_r = float(
                trade.gtos_vnext_profit_harvest_stale_close_below_r or 0.0
            )
            if (
                age_minutes is not None
                and age_minutes >= int(stale_minutes)
                and mfe_r >= stale_min_mfe_r
                and progress_r <= stale_close_below_r
            ):
                trade.partial_close_events.append({
                    "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_STALE_CLOSE_SIGNAL",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "mfe_r": mfe_r,
                    "current_progress_r": progress_r,
                    "age_minutes": age_minutes,
                    "stale_minutes": stale_minutes,
                    "stale_min_mfe_r": stale_min_mfe_r,
                    "stale_close_below_r": stale_close_below_r,
                    "policy": trade.gtos_vnext_dynamic_policy_selected,
                    "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                    "result_use_status": "runtime_management_event_not_counterfactual_pnl",
                })
                if self.close_position("vnext_profit_harvest_mfe_capture_v4_stale"):
                    trade.gtos_vnext_profit_harvest_last_action = "stale_close"
                    return "vnext_profit_harvest_mfe_capture_v4_stale_close"
                trade.gtos_vnext_profit_harvest_last_action = "stale_close_failed"
                return "vnext_profit_harvest_mfe_capture_v4_stale_close_failed"

        trail_gap_r = max(
            0.01,
            float(trade.gtos_vnext_profit_harvest_trail_gap_r or 0.35),
        )
        protect_floor_r = max(
            0.0,
            float(trade.gtos_vnext_profit_harvest_protect_floor_r or 0.0),
        )
        desired_stop_r = max(protect_floor_r, mfe_r - trail_gap_r)
        should_protect_floor = desired_stop_r <= 0.0 and not trade.sl_at_breakeven
        if (
            desired_stop_r > trade.gtos_vnext_dynamic_trail_stop_r + 1e-9
            or should_protect_floor
        ):
            if self._move_sl_to_dynamic_r(
                trade,
                trade.ticket,
                desired_stop_r,
                reason="vnext_profit_harvest_mfe_capture_v4_trail",
            ):
                trade.gtos_vnext_profit_harvest_last_action = "trail_or_protect"
                trade.partial_close_events.append({
                    "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_TRAIL_APPLIED",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "mfe_r": mfe_r,
                    "current_progress_r": progress_r,
                    "trail_gap_r": trail_gap_r,
                    "desired_stop_r": desired_stop_r,
                    "protect_floor_r": protect_floor_r,
                    "policy": trade.gtos_vnext_dynamic_policy_selected,
                    "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                    "result_use_status": "runtime_management_event_not_counterfactual_pnl",
                })
                return "vnext_profit_harvest_mfe_capture_v4_sl_modified"
            trade.gtos_vnext_profit_harvest_last_action = "trail_or_protect_failed"
            return "vnext_profit_harvest_mfe_capture_v4_sl_modify_failed"
        return None

    def _execute_tp1_partial(self, trade: TradeState, position: PositionInfo) -> str:
        """TP1 hit: close position based on tp1_close_pct config.

        Phase 1 validated: 100% close at TP1 is optimal (+0.503R exp, p=0.014).
        Partial close logic preserved behind config gate for future use.

        CRITICAL: Partial close changes the ticket number on MT5.
        """
        if self._vnext_trailing_runner_active(trade):
            return self._start_vnext_trailing_runner(trade)

        if self._vnext_momentum_exhaustion_active(trade):
            return self._start_vnext_momentum_exhaustion(trade)

        if self._vnext_partial_be_runner_active(trade):
            positions = self.mt5.get_positions(self.symbol)
            current_position = next((p for p in positions if p.ticket == trade.ticket), None)
            if current_position is not None:
                broker_volume = float(getattr(current_position, "volume", 0.0) or 0.0)
                initial_volume = float(trade.initial_volume or 0.0)
                if initial_volume > 0 and broker_volume < initial_volume - 1e-9:
                    trade.current_volume = broker_volume
                    trade.tp1_hit = True
                    broker_sl = float(getattr(current_position, "sl", 0.0) or 0.0)
                    broker_tp = float(getattr(current_position, "tp", 0.0) or 0.0)
                    if broker_sl > 0:
                        trade.stop_loss = broker_sl
                        if trade.direction == "LONG":
                            trade.sl_at_breakeven = broker_sl >= trade.entry_price - 1e-9
                        else:
                            trade.sl_at_breakeven = broker_sl <= trade.entry_price + 1e-9
                    if broker_tp > 0:
                        trade.take_profit_2 = broker_tp
                    trade.partial_close_events.append({
                        "type": "TP1_PARTIAL_ALREADY_REFLECTED_BY_BROKER",
                        "time": datetime.now(timezone.utc).isoformat(),
                        "ticket": trade.ticket,
                        "initial_volume": initial_volume,
                        "broker_volume": broker_volume,
                        "broker_sl": broker_sl,
                        "broker_tp": broker_tp,
                        "reason": "residual_volume_seen_before_duplicate_partial_close",
                    })
                    self._repair_recovered_partial_be_runner_sltp(trade)
                    return "tp1_partial_already_reflected_vnext_partial_be_runner"
            close_fraction = float(
                self._configured_vnext_partial_be_runner_params().get(
                    "partial_close_ratio",
                    0.5,
                )
                or 0.5
            )
            close_fraction = max(0.01, min(0.99, close_fraction))
            close_volume = round(trade.initial_volume * close_fraction, 2)
            close_geometry = self._close_request_execution_geometry(
                trade,
                close_volume,
                close_reason="tp1_partial_vnext_partial_be_runner",
            )
            if close_geometry is None:
                return "tp1_partial_failed_vnext_partial_be_runner"
            close_volume = close_geometry["volume"]
            expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
            close_type = 1 if trade.direction == "LONG" else 0
            request = {
                "action": 1,
                "symbol": self.symbol,
                "volume": close_volume,
                "type": close_type,
                "position": trade.ticket,
                "magic": MAGIC_NUMBER,
                "deviation": close_geometry["deviation"],
                "type_filling": close_geometry["type_filling"],
                "comment": "TP1_vnext_partial",
            }
            result = self.safe_place_order(request)
            if result is None or not result.success:
                logger.error("GTOS vNext partial_be_runner TP1 partial failed: %s", result)
                return "tp1_partial_failed_vnext_partial_be_runner"

            close_price = self._resolve_close_price(
                result,
                trade.direction,
                "TP1 partial (vNext partial_be_runner)",
            )
            time.sleep(0.5)
            positions = self.mt5.get_positions(self.symbol)
            our_positions = [p for p in positions if p.magic == MAGIC_NUMBER]
            old_ticket = trade.ticket
            previous_volume = trade.current_volume
            residual = self._find_residual_position_after_partial(
                trade,
                our_positions,
                closed_ticket=old_ticket,
                closed_volume=close_volume,
                previous_volume=previous_volume,
                close_result=result,
                close_reason="tp1_partial_vnext_partial_be_runner",
            )
            if residual is not None:
                new_ticket = residual.ticket
                trade.ticket = new_ticket
                trade.tp1_hit = True
                trade.current_volume = residual.volume
                self._known_tickets.add(new_ticket)
                close_meta = self._record_close_slippage_event(
                    trade=trade,
                    result=result,
                    close_reason="tp1_partial_vnext_partial_be_runner",
                    close_event_type="TP1_PARTIAL_VNEXT_PARTIAL_BE_RUNNER",
                    close_price=close_price,
                    close_volume=close_volume,
                    expected_close_price=expected_close_price,
                    spread_at_request=spread_at_request,
                    partial_close=True,
                    remaining_volume=trade.current_volume,
                    close_ticket=old_ticket,
                )
                be_status_at_close_request = close_meta.get("be_status_at_close_request")
                self._move_sl_to_breakeven(trade, new_ticket)
                if trade.take_profit_2 > 0:
                    self._modify_tp(
                        new_ticket,
                        trade.take_profit_2,
                        trade=trade,
                        modify_reason="tp1_partial_vnext_partial_be_runner_target_2",
                    )
                trade.partial_close_events.append({
                    "type": "TP1_PARTIAL_VNEXT_PARTIAL_BE_RUNNER",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "price": close_price,
                    "volume_closed": close_volume,
                    "old_ticket": old_ticket,
                    "new_ticket": new_ticket,
                    "partial_close_ratio": close_fraction,
                    "final_target_r": trade.gtos_vnext_dynamic_final_target_r,
                    "be_status_at_close_request": be_status_at_close_request,
                    "post_partial_residual_be_status": trade.sl_at_breakeven,
                    **close_meta,
                })
                self._notify_vnext_lifecycle(
                    trade,
                    "partial close",
                    price=close_price,
                    detail="TP1_PARTIAL_VNEXT_PARTIAL_BE_RUNNER",
                )
                return "tp1_partial_vnext_partial_be_runner"

            expected_remaining = round(max(previous_volume - close_volume, 0.0), 2)
            if expected_remaining > 0.011:
                return "tp1_partial_failed_vnext_partial_be_runner"

            trade.tp1_hit = True
            self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp1_partial_became_full_close_vnext_partial_be_runner",
                close_event_type="TP1_PARTIAL_BECAME_FULL_CLOSE_VNEXT_PARTIAL_BE_RUNNER",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            self._record_close("tp1_partial_became_full_close_vnext_partial_be_runner")
            self._notify_vnext_lifecycle(
                trade,
                "partial close",
                price=close_price,
                detail="TP1_PARTIAL_BECAME_FULL_CLOSE_VNEXT_PARTIAL_BE_RUNNER",
            )
            self.active_trade = None
            return "tp1_partial_became_full_close_vnext_partial_be_runner"

        if self._vnext_be_after_trigger_active(trade):
            self._move_sl_to_breakeven(trade, trade.ticket)
            trade.tp1_hit = True
            trade.partial_close_events.append({
                "type": "TP1_BE_ONLY_VNEXT_MOONSHOT",
                "time": datetime.now(timezone.utc).isoformat(),
                "trigger_r": trade.gtos_vnext_dynamic_be_trigger_r,
                "trigger_price": trade.gtos_vnext_dynamic_be_trigger_price,
                "final_target_r": trade.gtos_vnext_dynamic_final_target_r,
                "final_target_price": trade.gtos_vnext_dynamic_final_target_price,
            })
            logger.info(
                "GTOS vNext be_after_trigger TP1 hit: SL pulled to entry, "
                "no volume closed. Awaiting final target %.2fR=%.5f.",
                trade.gtos_vnext_dynamic_final_target_r,
                trade.gtos_vnext_dynamic_final_target_price,
            )
            return "tp1_be_only_vnext_moonshot"

        if trade.j46_j49_active:
            self._move_sl_to_breakeven(trade, trade.ticket)
            trade.tp1_hit = True
            trade.partial_close_events.append({
                "type": "TP1_BE_ONLY_J46_J49",
                "time": datetime.now(timezone.utc).isoformat(),
            })
            logger.info(
                "J46-J49 TP1 (3R) hit: SL pulled to entry, no volume closed. "
                "Awaiting 6R target or 12-bar time stop."
            )
            return "tp1_be_only_j46_j49"

        tp1_close_pct = self.config.get("risk", {}).get("tp1_close_pct", 100)

        if tp1_close_pct >= 100:
            # === FULL CLOSE AT TP1 (Phase 1 validated mechanism) ===
            close_geometry = self._close_request_execution_geometry(
                trade,
                trade.current_volume,
                close_reason="tp1_full_close",
            )
            if close_geometry is None:
                return "tp1_close_failed"
            close_volume = close_geometry["volume"]
            expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
            close_type = 1 if trade.direction == "LONG" else 0
            request = {
                "action": 1, "symbol": self.symbol, "volume": close_volume,
                "type": close_type, "position": trade.ticket,
                "magic": MAGIC_NUMBER,
                "deviation": close_geometry["deviation"],
                "type_filling": close_geometry["type_filling"],
                "comment": "TP1_full",
            }

            result = self.safe_place_order(request)
            if result is None or not result.success:
                logger.error(f"TP1 full close failed: {result}")
                return "tp1_close_failed"

            close_price = self._resolve_close_price(result, trade.direction, "TP1 full")
            close_meta = self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp1_full_close",
                close_event_type="TP1_FULL_CLOSE",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            trade.tp1_hit = True
            trade.partial_close_events.append({
                "type": "TP1_FULL_CLOSE",
                "time": datetime.now(timezone.utc).isoformat(),
                "price": close_price,
                "volume_closed": close_volume,
                **close_meta,
            })
            logger.info(f"TP1 full close: {close_volume} lots at {close_price}. Trade complete.")
            self._record_close("tp1_full_close")
            self.active_trade = None
            return "tp1_full_close"
        else:
            # === PARTIAL CLOSE (legacy, preserved for future use) ===
            close_fraction = tp1_close_pct / 100.0
            close_volume = round(trade.initial_volume * close_fraction, 2)
            close_geometry = self._close_request_execution_geometry(
                trade,
                close_volume,
                close_reason="tp1_partial",
            )
            if close_geometry is None:
                return "tp1_partial_failed"
            close_volume = close_geometry["volume"]
            expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)

            close_type = 1 if trade.direction == "LONG" else 0
            request = {
                "action": 1, "symbol": self.symbol, "volume": close_volume,
                "type": close_type, "position": trade.ticket,
                "magic": MAGIC_NUMBER,
                "deviation": close_geometry["deviation"],
                "type_filling": close_geometry["type_filling"],
                "comment": "TP1_partial",
            }

            result = self.safe_place_order(request)
            if result is None or not result.success:
                logger.error(f"TP1 partial close failed: {result}")
                return "tp1_partial_failed"

            close_price = self._resolve_close_price(result, trade.direction, "TP1 partial")

            time.sleep(0.5)
            positions = self.mt5.get_positions(self.symbol)
            our_positions = [p for p in positions if p.magic == MAGIC_NUMBER]

            old_ticket = trade.ticket
            previous_volume = trade.current_volume
            residual = self._find_residual_position_after_partial(
                trade,
                our_positions,
                closed_ticket=old_ticket,
                closed_volume=close_volume,
                previous_volume=previous_volume,
                close_result=result,
                close_reason="tp1_partial",
            )
            if residual is not None:
                new_ticket = residual.ticket
                trade.ticket = new_ticket
                trade.tp1_hit = True
                trade.current_volume = residual.volume
                self._known_tickets.add(new_ticket)
                close_meta = self._record_close_slippage_event(
                    trade=trade,
                    result=result,
                    close_reason="tp1_partial",
                    close_event_type="TP1_PARTIAL",
                    close_price=close_price,
                    close_volume=close_volume,
                    expected_close_price=expected_close_price,
                    spread_at_request=spread_at_request,
                    partial_close=True,
                    remaining_volume=trade.current_volume,
                    close_ticket=old_ticket,
                )

                be_status_at_close_request = close_meta.get("be_status_at_close_request")
                self._move_sl_to_breakeven(trade, new_ticket)

                if trade.take_profit_2 > 0:
                    self._modify_tp(
                        new_ticket,
                        trade.take_profit_2,
                        trade=trade,
                        modify_reason="tp1_partial_target_2",
                    )

                trade.partial_close_events.append({
                    "type": "TP1_PARTIAL",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "price": close_price,
                    "volume_closed": close_volume,
                    "old_ticket": old_ticket,
                    "new_ticket": new_ticket,
                    "be_status_at_close_request": be_status_at_close_request,
                    "post_partial_residual_be_status": trade.sl_at_breakeven,
                    **close_meta,
                })
                logger.info(f"TP1 partial close: {close_volume} lots at {close_price}. "
                            f"Ticket {old_ticket} -> {new_ticket}. SL moved to BE.")
                return "tp1_partial"

            expected_remaining = round(max(previous_volume - close_volume, 0.0), 2)
            if expected_remaining > 0.011:
                return "tp1_partial_failed"

            trade.tp1_hit = True
            self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp1_full_close",
                close_event_type="TP1_PARTIAL_BECAME_FULL_CLOSE",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            self._record_close("tp1_full_close")
            self.active_trade = None
            return "tp1_full_close"

    def _execute_vnext_dynamic_final_close(
        self,
        trade: TradeState,
        *,
        policy: str,
    ) -> str:
        close_reason = f"tp2_final_target_vnext_{policy}"
        close_geometry = self._close_request_execution_geometry(
            trade,
            trade.current_volume,
            close_reason=close_reason,
        )
        if close_geometry is None:
            return f"tp2_final_target_failed_vnext_{policy}"
        close_volume = close_geometry["volume"]
        expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
        close_type = 1 if trade.direction == "LONG" else 0
        request = {
            "action": 1,
            "symbol": self.symbol,
            "volume": close_volume,
            "type": close_type,
            "position": trade.ticket,
            "magic": MAGIC_NUMBER,
            "deviation": close_geometry["deviation"],
            "type_filling": close_geometry["type_filling"],
            "comment": f"TP2_vnext_{policy[:12]}",
        }
        result = self.safe_place_order(request)
        if result is None or not result.success:
            logger.error("GTOS vNext %s final close failed: %s", policy, result)
            return f"tp2_final_target_failed_vnext_{policy}"

        close_price = self._resolve_close_price(
            result,
            trade.direction,
            f"TP2 final target (vNext {policy})",
        )
        close_meta = self._record_close_slippage_event(
            trade=trade,
            result=result,
            close_reason=close_reason,
            close_event_type=f"TP2_FINAL_TARGET_VNEXT_{policy.upper()}",
            close_price=close_price,
            close_volume=close_volume,
            expected_close_price=expected_close_price,
            spread_at_request=spread_at_request,
            partial_close=False,
            remaining_volume=0.0,
        )
        trade.tp2_hit = True
        trade.partial_close_events.append({
            "type": f"TP2_FINAL_TARGET_VNEXT_{policy.upper()}",
            "time": datetime.now(timezone.utc).isoformat(),
            "price": close_price,
            "volume_closed": close_volume,
            "target_r": trade.gtos_vnext_dynamic_final_target_r,
            "target_price": trade.gtos_vnext_dynamic_final_target_price,
            "execution_policy_id": trade.gtos_vnext_execution_policy_id,
            **close_meta,
        })
        logger.info(
            "GTOS vNext %s final target hit: %s lots closed at %.5f",
            policy,
            close_volume,
            close_price,
        )
        self._notify_vnext_lifecycle(
            trade,
            "dynamic final close",
            price=close_price,
            result_r=trade.gtos_vnext_dynamic_final_target_r,
            detail=close_reason,
        )
        self._record_close(close_reason)
        self.active_trade = None
        return close_reason

    def _execute_tp2_partial(self, trade: TradeState, position: PositionInfo) -> str:
        """TP2 hit: close 25% of initial, trail SL to TP1."""
        if self._vnext_partial_be_runner_active(trade):
            close_geometry = self._close_request_execution_geometry(
                trade,
                trade.current_volume,
                close_reason="tp2_final_target_vnext_partial_be_runner",
            )
            if close_geometry is None:
                return "tp2_final_target_failed_vnext_partial_be_runner"
            close_volume = close_geometry["volume"]
            expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
            close_type = 1 if trade.direction == "LONG" else 0
            request = {
                "action": 1,
                "symbol": self.symbol,
                "volume": close_volume,
                "type": close_type,
                "position": trade.ticket,
                "magic": MAGIC_NUMBER,
                "deviation": close_geometry["deviation"],
                "type_filling": close_geometry["type_filling"],
                "comment": "TP2_vnext_partial_final",
            }
            result = self.safe_place_order(request)
            if result is None or not result.success:
                logger.error("GTOS vNext partial_be_runner final close failed: %s", result)
                return "tp2_final_target_failed_vnext_partial_be_runner"

            close_price = self._resolve_close_price(
                result,
                trade.direction,
                "TP2 final target (vNext partial_be_runner)",
            )
            close_meta = self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp2_final_target_vnext_partial_be_runner",
                close_event_type="TP2_FINAL_TARGET_VNEXT_PARTIAL_BE_RUNNER",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            trade.tp2_hit = True
            trade.partial_close_events.append({
                "type": "TP2_FINAL_TARGET_VNEXT_PARTIAL_BE_RUNNER",
                "time": datetime.now(timezone.utc).isoformat(),
                "price": close_price,
                "volume_closed": close_volume,
                "target_r": trade.gtos_vnext_dynamic_final_target_r,
                "target_price": trade.gtos_vnext_dynamic_final_target_price,
                **close_meta,
            })
            self._notify_vnext_lifecycle(
                trade,
                "dynamic final close",
                price=close_price,
                result_r=trade.gtos_vnext_dynamic_final_target_r,
                detail="tp2_final_target_vnext_partial_be_runner",
            )
            self._record_close("tp2_final_target_vnext_partial_be_runner")
            self.active_trade = None
            return "tp2_final_target_vnext_partial_be_runner"

        if self._vnext_trailing_runner_active(trade):
            return self._execute_vnext_dynamic_final_close(
                trade,
                policy="trailing_runner",
            )

        if self._vnext_momentum_exhaustion_active(trade):
            return self._execute_vnext_dynamic_final_close(
                trade,
                policy="momentum_exhaustion",
            )

        if self._vnext_be_after_trigger_active(trade):
            close_geometry = self._close_request_execution_geometry(
                trade,
                trade.current_volume,
                close_reason="tp2_final_target_vnext_be_after_trigger",
            )
            if close_geometry is None:
                return "tp2_final_target_failed_vnext_be_after_trigger"
            close_volume = close_geometry["volume"]
            expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
            close_type = 1 if trade.direction == "LONG" else 0
            request = {
                "action": 1, "symbol": self.symbol, "volume": close_volume,
                "type": close_type, "position": trade.ticket,
                "magic": MAGIC_NUMBER,
                "deviation": close_geometry["deviation"],
                "type_filling": close_geometry["type_filling"],
                "comment": "TP2_vnext_be_final",
            }
            result = self.safe_place_order(request)
            if result is None or not result.success:
                logger.error("GTOS vNext be_after_trigger final close failed: %s", result)
                return "tp2_final_target_failed_vnext_be_after_trigger"

            close_price = self._resolve_close_price(
                result, trade.direction, "TP2 final target (vNext be_after_trigger)",
            )
            close_meta = self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp2_final_target_vnext_be_after_trigger",
                close_event_type="TP2_FINAL_TARGET_VNEXT_BE_AFTER_TRIGGER",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            trade.tp2_hit = True
            trade.partial_close_events.append({
                "type": "TP2_FINAL_TARGET_VNEXT_BE_AFTER_TRIGGER",
                "time": datetime.now(timezone.utc).isoformat(),
                "price": close_price,
                "volume_closed": close_volume,
                "target_r": trade.gtos_vnext_dynamic_final_target_r,
                "target_price": trade.gtos_vnext_dynamic_final_target_price,
                **close_meta,
            })
            logger.info(
                "GTOS vNext be_after_trigger final target hit: %s lots closed at %.5f",
                close_volume,
                close_price,
            )
            self._notify_vnext_lifecycle(
                trade,
                "dynamic final close",
                price=close_price,
                result_r=trade.gtos_vnext_dynamic_final_target_r,
                detail="tp2_final_target_vnext_be_after_trigger",
            )
            self._record_close("tp2_final_target_vnext_be_after_trigger")
            self.active_trade = None
            return "tp2_final_target_vnext_be_after_trigger"

        if trade.j46_j49_active:
            close_geometry = self._close_request_execution_geometry(
                trade,
                trade.current_volume,
                close_reason="tp2_higher_target_j46_j49",
            )
            if close_geometry is None:
                return "tp2_higher_target_failed"
            close_volume = close_geometry["volume"]
            expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
            close_type = 1 if trade.direction == "LONG" else 0
            request = {
                "action": 1, "symbol": self.symbol, "volume": close_volume,
                "type": close_type, "position": trade.ticket,
                "magic": MAGIC_NUMBER,
                "deviation": close_geometry["deviation"],
                "type_filling": close_geometry["type_filling"],
                "comment": "TP2_higher_target_j46_j49",
            }
            result = self.safe_place_order(request)
            if result is None or not result.success:
                logger.error(f"J46-J49 higher-target close failed: {result}")
                return "tp2_higher_target_failed"

            close_price = self._resolve_close_price(
                result, trade.direction, "TP2 higher target (J46-J49)",
            )
            close_meta = self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp2_higher_target_j46_j49",
                close_event_type="TP2_HIGHER_TARGET_J46_J49",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            trade.partial_close_events.append({
                "type": "TP2_HIGHER_TARGET_J46_J49",
                "time": datetime.now(timezone.utc).isoformat(),
                "price": close_price,
                "volume_closed": close_volume,
                **close_meta,
            })
            logger.info(
                "J46-J49 6R higher target hit: %s lots closed at %.5f",
                close_volume, close_price,
            )
            self._record_close("tp2_higher_target_j46_j49")
            self.active_trade = None
            return "tp2_higher_target_j46_j49"

        close_volume = round(trade.initial_volume * 0.25, 2)
        close_volume = min(close_volume, trade.current_volume)
        close_geometry = self._close_request_execution_geometry(
            trade,
            close_volume,
            close_reason="tp2_partial",
        )
        if close_geometry is None:
            return "tp2_partial_failed"
        close_volume = close_geometry["volume"]
        expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)

        close_type = 1 if trade.direction == "LONG" else 0
        request = {
            "action": 1, "symbol": self.symbol, "volume": close_volume,
            "type": close_type, "position": trade.ticket,
            "magic": MAGIC_NUMBER,
            "deviation": close_geometry["deviation"],
            "type_filling": close_geometry["type_filling"],
            "comment": "TP2_partial",
        }

        result = self.safe_place_order(request)
        if result is None or not result.success:
            logger.error(f"TP2 partial close failed: {result}")
            return "tp2_partial_failed"

        close_price = self._resolve_close_price(result, trade.direction, "TP2 partial")

        time.sleep(0.5)
        positions = self.mt5.get_positions(self.symbol)
        our_positions = [p for p in positions if p.magic == MAGIC_NUMBER]

        old_ticket = trade.ticket
        previous_volume = trade.current_volume
        residual = self._find_residual_position_after_partial(
            trade,
            our_positions,
            closed_ticket=old_ticket,
            closed_volume=close_volume,
            previous_volume=previous_volume,
            close_result=result,
            close_reason="tp2_partial",
        )
        if residual is not None:
            new_ticket = residual.ticket
            trade.ticket = new_ticket
            trade.tp2_hit = True
            trade.current_volume = residual.volume
            self._known_tickets.add(new_ticket)
            close_meta = self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason="tp2_partial",
                close_event_type="TP2_PARTIAL",
                close_price=close_price,
                close_volume=close_volume,
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=True,
                remaining_volume=trade.current_volume,
                close_ticket=old_ticket,
            )

            be_status_at_close_request = close_meta.get("be_status_at_close_request")
            sl_ok = self._modify_sl(
                new_ticket,
                trade.take_profit_1,
                trade=trade,
                modify_reason="tp2_partial_trail_sl_to_tp1",
            )
            if not sl_ok:
                logger.error(
                    "SL trail to TP1 failed after TP2 partial; existing broker SL "
                    "left untouched and exact ticket diagnostics recorded"
                )
                return "tp2_sl_trail_failed"
            if trade.take_profit_3 > 0:
                self._modify_tp(
                    new_ticket,
                    trade.take_profit_3,
                    trade=trade,
                    modify_reason="tp2_partial_target_3",
                )

            trade.partial_close_events.append({
                "type": "TP2_PARTIAL",
                "time": datetime.now(timezone.utc).isoformat(),
                "price": close_price,
                "volume_closed": close_volume,
                "old_ticket": old_ticket,
                "new_ticket": new_ticket,
                "be_status_at_close_request": be_status_at_close_request,
                "post_partial_residual_sl_status": trade.stop_loss,
                **close_meta,
            })
            logger.info(f"TP2 partial close: {close_volume} lots at {close_price}. "
                        f"SL trailed to TP1. Runner targeting TP3.")
            return "tp2_partial"

        expected_remaining = round(max(previous_volume - close_volume, 0.0), 2)
        if expected_remaining > 0.011:
            return "tp2_partial_failed"

        trade.tp2_hit = True
        self._record_close_slippage_event(
            trade=trade,
            result=result,
            close_reason="tp2_full_close",
            close_event_type="TP2_PARTIAL_BECAME_FULL_CLOSE",
            close_price=close_price,
            close_volume=close_volume,
            expected_close_price=expected_close_price,
            spread_at_request=spread_at_request,
            partial_close=False,
            remaining_volume=0.0,
        )
        self._record_close("tp2_full_close")
        self.active_trade = None
        return "tp2_full_close"

    def close_position(self, reason: str = "manual") -> bool:
        """Close entire remaining position."""
        if self.active_trade is None:
            return False

        trade = self.active_trade
        close_type = 1 if trade.direction == "LONG" else 0
        expected_close_price, spread_at_request = self._close_quote_snapshot(trade.direction)
        close_geometry = self._close_request_execution_geometry(
            trade,
            trade.current_volume,
            close_reason=reason,
        )
        if close_geometry is None:
            return False

        request = {
            "action": 1, "symbol": self.symbol, "volume": close_geometry["volume"],
            "type": close_type, "position": trade.ticket,
            "magic": MAGIC_NUMBER,
            "deviation": close_geometry["deviation"],
            "type_filling": close_geometry["type_filling"],
            "comment": f"close_{reason}",
        }

        result = self.safe_place_order(request)
        if result and result.success:
            # MT5 order_send result.price can return 0.0 on some brokers/close
            # paths (observed USDJPY 2026-04-23 09:30 UTC on trailing-BE force
            # close).  Mirror the fill-side fallback at :417-425 and substitute
            # the current tick so audits and P&L attribution don't record 0.0.
            # For a LONG close we hit the bid; for a SHORT close we lift the
            # ask -- matching MT5 semantics for TRADE_ACTION_DEAL on an
            # existing position.
            close_price = result.price
            if not close_price:
                tick = self.mt5.get_tick(self.symbol)
                if tick is not None:
                    fallback = tick.bid if trade.direction == "LONG" else tick.ask
                    logger.warning(
                        "Close price returned 0.0 from MT5; using current "
                        "tick price %.5f as fallback",
                        fallback,
                    )
                    close_price = fallback
                else:
                    logger.warning(
                        "Close price returned 0.0 from MT5 and no tick "
                        "available -- recording 0.0 (degraded data)",
                    )
            self._record_broker_runtime_lifecycle_event(
                stage="close_position_result",
                request=request,
                result=result,
                trade=trade,
                extra={"close_reason": reason, "close_price": close_price},
            )
            logger.info(f"Position closed: {reason} at {close_price}")
            self._record_close_slippage_event(
                trade=trade,
                result=result,
                close_reason=reason,
                close_event_type="FULL_POSITION_CLOSE",
                close_price=close_price,
                close_volume=close_geometry["volume"],
                expected_close_price=expected_close_price,
                spread_at_request=spread_at_request,
                partial_close=False,
                remaining_volume=0.0,
            )
            self._record_close(reason)
            # BUG #31 fix: capture trade state before clearing so the close
            # notification has the data it needs. The orchestrator's
            # exit-detection path also fires notify_trade_closed; the
            # dedup set ensures we don't double-fire for the same trade_id.
            _closed_trade: Optional[TradeState] = self.active_trade
            self.active_trade = None
            self._notify_close_if_unsent(_closed_trade, reason, close_price)
            return True

        logger.error(f"Failed to close position: {result}")
        return False

    def _notify_close_if_unsent(
        self,
        closed_trade: Optional[TradeState],
        reason: str,
        close_price: float,
    ) -> None:
        """BUG #31 fix: fire notify_trade_closed if it hasn't fired yet for
        this trade_id. Idempotent + non-blocking + dedup-safe.

        Why this exists: the orchestrator's main-loop exit-detection path
        also fires notify_trade_closed (with richer shadow-log data). But
        that path can be skipped by orchestrator restarts mid-close, by
        end-of-day shutdowns that miss the just-closed position, or by
        the J48 time-stop / partial-close paths that don't go through the
        orchestrator's normal flow. Without this fallback, the operator
        gets no Telegram notification for those edge cases — discovered
        live on 2026-04-28 when the GBPJPY +0.74R close fired silently.

        The orchestrator can dedup by checking the same trade_id; or, if
        the orchestrator's notify fires first, this call is a no-op.
        """
        if closed_trade is None:
            return
        trade_id = getattr(closed_trade, "trade_id", "") or ""
        if not trade_id:
            return
        if trade_id in self._notified_close_trade_ids:
            return
        self._notified_close_trade_ids.add(trade_id)
        try:
            # actual_r: signed distance from entry to close, in R-units.
            sl_dist = float(getattr(closed_trade, "sl_distance", 0) or 0)
            entry = float(getattr(closed_trade, "entry_price", 0) or 0)
            if sl_dist > 0 and entry > 0 and close_price > 0:
                if closed_trade.direction == "LONG":
                    actual_r = (close_price - entry) / sl_dist
                else:
                    actual_r = (entry - close_price) / sl_dist
            else:
                actual_r = 0.0

            # hold_minutes: best-effort from entry_time ISO string.
            hold_minutes: Optional[float] = None
            entry_time_str = getattr(closed_trade, "entry_time", "") or ""
            if entry_time_str:
                try:
                    from datetime import datetime, timezone
                    et = datetime.fromisoformat(
                        str(entry_time_str).replace("Z", "+00:00")
                    )
                    if et.tzinfo is None:
                        et = et.replace(tzinfo=timezone.utc)
                    hold_minutes = (
                        datetime.now(timezone.utc) - et
                    ).total_seconds() / 60.0
                except Exception:
                    hold_minutes = None

            from src.notifications import (
                build_vnext_notification_context,
                notify_trade_closed,
            )
            notify_trade_closed(
                symbol=self.symbol,
                result=reason,
                actual_r=actual_r,
                hold_minutes=hold_minutes,
                trade_id=trade_id,
                entry_price=entry,
                exit_price=float(close_price or 0),
                vnext_context=build_vnext_notification_context(
                    closed_trade,
                    lifecycle_event=reason,
                ),
            )
        except Exception as e:  # noqa: BLE001 — must never break the close
            logger.warning(
                "Close notification failed (non-blocking): %s", e
            )

    def _trading_m15_bars_since(self, entry_dt, budget) -> Optional[int]:
        """Count actual CLOSED M15 bars that PRINTED since entry_dt -- TRADING bars (they exist only while
        the market is open), so this skips nights/weekends/holidays, matching the validated route's bar
        count instead of wall-clock. time_stop_bars is in M15 units for EVERY sleeve (the H4 sleeves' route
        maxbars 60/80 were pre-scaled x16 -> 960/1280 M15). Returns None if the feed can't be read (caller
        falls back to wall-clock so the backstop still works). NEVER raises."""
        try:
            want = max(96, int(budget) + 64)            # a little past the budget (+ the forming bar)
            candles = self.mt5.get_candles(self.symbol, 15, want)
            if not candles or len(candles) < 2:
                return None
            n = 0
            for c in candles[:-1]:                       # drop the last (forming) bar
                t = c.get("time")
                if not t:
                    continue
                try:
                    tdt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                except (TypeError, ValueError):
                    continue
                if tdt.tzinfo is None:
                    tdt = tdt.replace(tzinfo=timezone.utc)
                if tdt > entry_dt:                       # bars that CLOSED after the fill (route counts j>i)
                    n += 1
            return n
        except Exception:
            return None

    def _set_time_stop_clock_diagnostic(self, diagnostic: dict) -> dict:
        self._last_time_stop_clock_diagnostic = diagnostic
        return diagnostic

    def get_time_stop_clock_diagnostic(self) -> Optional[dict]:
        diagnostic = getattr(self, "_last_time_stop_clock_diagnostic", None)
        return dict(diagnostic) if isinstance(diagnostic, dict) else None

    def _base_time_stop_clock_diagnostic(
        self,
        *,
        checked_at: datetime,
        status: str,
        trade: Optional[TradeState] = None,
    ) -> dict:
        active = trade or self.active_trade
        return {
            "schema_version": "gtos.vnext.time_stop_clock_diagnostic.v1",
            "checked_at_utc": checked_at.astimezone(timezone.utc).isoformat(),
            "status": status,
            "ticket": getattr(active, "ticket", None) if active is not None else None,
            "policy": getattr(active, "gtos_vnext_dynamic_policy_selected", None) if active is not None else None,
            "execution_policy_id": getattr(active, "gtos_vnext_execution_policy_id", None) if active is not None else None,
            "vnext_time_stop_active": bool(active is not None and self._vnext_time_stop_active(active)),
            "targetless": bool(
                active is not None
                and getattr(active, "gtos_vnext_dynamic_no_broker_take_profit", False)
            ),
            "broker_take_profit_mode": (
                getattr(active, "gtos_vnext_dynamic_broker_take_profit_mode", None)
                if active is not None else None
            ),
            "time_stop_bars": (
                getattr(active, "gtos_vnext_dynamic_time_stop_bars", None)
                if active is not None else None
            ),
            "entry_time_utc": None,
            "clock_source": None,
            "elapsed_m15_bars": None,
            "bars_until_due": None,
            "overdue_bars": None,
            "close_attempted": False,
            "close_result": None,
            "close_reason": None,
            "error": None,
        }

    def check_time_stop_and_close(self) -> Optional[str]:
        """J48 time stop: force-close at market when 12 M15 bars have elapsed
        since fill. Returns 'j46_j49_time_stop' on close, None otherwise.
        Safe to call when no active trade or J46-J49 disabled.

        Skips trades that were NOT opened under J46-J49 (orphan adoption from
        ``reconcile_on_startup``, or pre-J46-J49-flip live trades): those have
        ``j46_j49_active=False`` and their broker TPs are AI's original
        emission, not the 6R higher target — applying the time stop to them
        would close legitimate positions at market for the wrong reason."""
        checked_at = datetime.now(timezone.utc)
        if self.active_trade is None:
            self._set_time_stop_clock_diagnostic(
                self._base_time_stop_clock_diagnostic(
                    checked_at=checked_at,
                    status="no_active_trade",
                )
            )
            return None
        if self._vnext_time_stop_active(self.active_trade):
            trade = self.active_trade
            diagnostic = self._base_time_stop_clock_diagnostic(
                checked_at=checked_at,
                status="checking",
                trade=trade,
            )
            time_stop = trade.gtos_vnext_dynamic_time_stop_bars
            if time_stop is None:
                diagnostic["status"] = "missing_time_stop_bars"
                self._set_time_stop_clock_diagnostic(diagnostic)
                return None
            entry_time_str = trade.entry_time or ""
            if not entry_time_str:
                diagnostic["status"] = "missing_entry_time"
                self._set_time_stop_clock_diagnostic(diagnostic)
                return None
            try:
                entry_dt = datetime.fromisoformat(entry_time_str)
            except (ValueError, TypeError):
                diagnostic["status"] = "invalid_entry_time"
                diagnostic["entry_time_utc"] = str(entry_time_str)
                self._set_time_stop_clock_diagnostic(diagnostic)
                return None
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=timezone.utc)
            entry_dt = entry_dt.astimezone(timezone.utc)
            diagnostic["entry_time_utc"] = entry_dt.isoformat()
            # Count TRADING M15 bars since entry (skips closed-market time), matching the validated route's
            # bar count. Fall back to wall-clock M15 only if the feed can't be read, so the backstop still
            # fires. (timestop-wallclock-vs-trading-bars: wall-clock over-counts -- index CFDs ~3x, fx_jpy
            # over weekends -- force-closing earlier than the route; the printed-bar count fixes that.)
            elapsed = self._trading_m15_bars_since(entry_dt, int(time_stop))
            elapsed_basis = "trading" if elapsed is not None else "wallclock"
            if elapsed is None:
                from src.components import j46_j49_policy
                elapsed = j46_j49_policy.bars_elapsed_since_fill(entry_dt)
            diagnostic.update({
                "clock_source": elapsed_basis,
                "elapsed_m15_bars": int(elapsed),
                "bars_until_due": int(time_stop) - int(elapsed),
                "overdue_bars": max(0, int(elapsed) - int(time_stop)),
            })
            if elapsed >= int(time_stop):
                policy = str(
                    trade.gtos_vnext_dynamic_policy_selected
                    or "dynamic"
                ).strip().lower()
                close_reason = (
                    "vnext_time_stop"
                    if policy == "time_stop"
                    else f"vnext_{policy}_time_stop"
                )
                logger.info(
                    "GTOS vNext %s time stop fired: %d %s M15 bars "
                    "elapsed (>=%d). Closing at market.",
                    policy,
                    elapsed,
                    elapsed_basis,
                    int(time_stop),
                )
                diagnostic["status"] = "due_close_attempted"
                diagnostic["close_attempted"] = True
                diagnostic["close_reason"] = close_reason
                closed = bool(self.close_position(close_reason))
                diagnostic["close_result"] = closed
                if closed:
                    diagnostic["status"] = "closed"
                    self._set_time_stop_clock_diagnostic(diagnostic)
                    return close_reason
                diagnostic["status"] = "close_failed"
                self._set_time_stop_clock_diagnostic(diagnostic)
                return None
            diagnostic["status"] = "not_due"
            self._set_time_stop_clock_diagnostic(diagnostic)
            return None
        if not getattr(self.active_trade, "j46_j49_active", False):
            self._set_time_stop_clock_diagnostic(
                self._base_time_stop_clock_diagnostic(
                    checked_at=checked_at,
                    status="vnext_time_stop_inactive",
                )
            )
            return None
        from src.components import j46_j49_policy
        if not j46_j49_policy.is_enabled(self.config):
            self._set_time_stop_clock_diagnostic(
                self._base_time_stop_clock_diagnostic(
                    checked_at=checked_at,
                    status="legacy_time_stop_disabled",
                )
            )
            return None
        params = j46_j49_policy.get_policy_params(self.config)
        time_stop = int(params.get("time_stop_bars", 12))
        entry_time_str = self.active_trade.entry_time or ""
        if not entry_time_str:
            self._set_time_stop_clock_diagnostic(
                self._base_time_stop_clock_diagnostic(
                    checked_at=checked_at,
                    status="legacy_missing_entry_time",
                )
            )
            return None
        try:
            entry_dt = datetime.fromisoformat(entry_time_str)
        except (ValueError, TypeError):
            self._set_time_stop_clock_diagnostic(
                self._base_time_stop_clock_diagnostic(
                    checked_at=checked_at,
                    status="legacy_invalid_entry_time",
                )
            )
            return None
        if entry_dt.tzinfo is None:
            entry_dt = entry_dt.replace(tzinfo=timezone.utc)
        elapsed = j46_j49_policy.bars_elapsed_since_fill(entry_dt)
        legacy_diagnostic = self._base_time_stop_clock_diagnostic(
            checked_at=checked_at,
            status="legacy_not_due",
        )
        legacy_diagnostic.update({
            "entry_time_utc": entry_dt.astimezone(timezone.utc).isoformat(),
            "clock_source": "wallclock",
            "time_stop_bars": time_stop,
            "elapsed_m15_bars": int(elapsed),
            "bars_until_due": int(time_stop) - int(elapsed),
            "overdue_bars": max(0, int(elapsed) - int(time_stop)),
        })
        if elapsed >= time_stop:
            logger.info(
                "J46-J49 time stop fired: %d M15 bars elapsed (>=%d). "
                "Closing at market.", elapsed, time_stop,
            )
            legacy_diagnostic["status"] = "legacy_due_close_attempted"
            legacy_diagnostic["close_attempted"] = True
            legacy_diagnostic["close_reason"] = "j46_j49_time_stop"
            closed = bool(self.close_position("j46_j49_time_stop"))
            legacy_diagnostic["close_result"] = closed
            if closed:
                legacy_diagnostic["status"] = "legacy_closed"
                self._set_time_stop_clock_diagnostic(legacy_diagnostic)
                return "j46_j49_time_stop"
            legacy_diagnostic["status"] = "legacy_close_failed"
        self._set_time_stop_clock_diagnostic(legacy_diagnostic)
        return None

    def handle_timeout_trailing(self) -> str:
        """Called when kill zone ends with active trade.

        Moves SL to breakeven only if the trade is currently in profit AND
        — when J46-J49 v2 is active — the position has actually reached
        the configured BE trigger (TP1 at 3R by default). The "trade-is-in-
        profit" check alone caused BUG #27 on 2026-04-28 GBPJPY: an orphan
        adopted at +0.74R triggered a premature SL→BE attempt that then
        cascaded into BUG #28 (close-on-SL-failure) and lost ~$10k of
        upside.

        Gating logic:
          * If ``j46_j49_policy.is_enabled(config)`` is True: require
            ``current_R >= tp1_distance_r`` (3.0R per validated config).
            Below that threshold, the broker SL is the safety floor —
            leave it alone. This applies to BOTH J46-J49-emitted trades
            (``j46_j49_active=True``) AND orphan-adopted positions
            (``j46_j49_active=False``): the live trader's policy is the
            same regardless of how the position entered our state.
          * If J46-J49 disabled (legacy mode): keep the prior "any-profit
            triggers BE" behavior so the legacy Variant-C path is
            unchanged.

        If underwater (or below the J46-J49 trigger), the original SL
        stays — the thesis (OB holding) hasn't been invalidated, so let
        the 2h timeout handle it.
        """
        if self.active_trade is None:
            return "no_trade"
        if not self.active_trade.sl_at_breakeven:
            tick = self.mt5.get_tick(self.symbol)
            if tick is None:
                logger.warning("No tick for BE check -- skipping, will retry next candle")
                return "trailing"
            current = tick.bid if self.active_trade.direction == "LONG" else tick.ask
            in_profit = (
                (self.active_trade.direction == "LONG" and current > self.active_trade.entry_price)
                or (self.active_trade.direction == "SHORT" and current < self.active_trade.entry_price)
            )

            # BUG #27 fix: gate BE on actual R-progress when J46-J49 active.
            from src.components import j46_j49_policy
            if j46_j49_policy.is_enabled(self.config):
                if not in_profit:
                    logger.info(
                        "Trade underwater at KZ end (current=%.5f, entry=%.5f) "
                        "-- keeping original SL=%.5f, 2h timeout applies",
                        current, self.active_trade.entry_price, self.active_trade.stop_loss,
                    )
                    return "trailing"

                # Compute current R-progress against the position's actual SL distance.
                # For adopted orphans, sl_distance was set in reconcile_on_startup
                # from |entry - broker_sl|. For native fills, sl_distance is set
                # in open_trade. Either way it represents "1R" in absolute price
                # units for this exact position.
                sl_dist = self.active_trade.sl_distance
                if sl_dist <= 0:
                    logger.warning(
                        "BE check: sl_distance is %.5f (<=0) -- cannot compute "
                        "R-progress; leaving SL untouched", sl_dist,
                    )
                    return "trailing"

                if self.active_trade.direction == "LONG":
                    progress_r = (current - self.active_trade.entry_price) / sl_dist
                else:
                    progress_r = (self.active_trade.entry_price - current) / sl_dist

                params = j46_j49_policy.get_policy_params(self.config)
                tp1_r = float(params.get("tp1_distance_r", 3.0))

                if progress_r < tp1_r:
                    logger.info(
                        "J46-J49 BE gate: current R-progress %.3f < TP1 trigger "
                        "%.2fR (current=%.5f, entry=%.5f, sl_dist=%.5f) -- "
                        "leaving SL untouched at %.5f",
                        progress_r, tp1_r, current,
                        self.active_trade.entry_price, sl_dist,
                        self.active_trade.stop_loss,
                    )
                    return "trailing"

                logger.info(
                    "J46-J49 BE gate satisfied: R-progress %.3f >= %.2fR "
                    "-- moving SL to BE", progress_r, tp1_r,
                )
                self._move_sl_to_breakeven(self.active_trade, self.active_trade.ticket)
                return "trailing"

            # Legacy path (J46-J49 disabled): preserve original any-profit BE move.
            if in_profit:
                self._move_sl_to_breakeven(self.active_trade, self.active_trade.ticket)
            else:
                logger.info(
                    "Trade underwater at KZ end (current=%.5f, entry=%.5f) "
                    "-- keeping original SL=%.5f, 2h timeout applies",
                    current, self.active_trade.entry_price, self.active_trade.stop_loss,
                )
        return "trailing"

    # === INTERNAL HELPERS ===

    def _calculate_lots(
        self,
        sl_distance: float,
        risk_amount: float,
        *,
        sym_info=None,
        require_broker_geometry: bool = False,
        direction: str | None = None,
        entry_price: float | None = None,
        stop_loss: float | None = None,
    ) -> float | None:
        """Calculate lot size from broker cash-risk mechanics when available.

        Live vNext selected-cell execution sizes from MT5
        ``order_calc_profit`` because broker CFD metadata can expose a stale
        or internally inconsistent ``trade_tick_value``. Tick-value and
        contract-size sizing are legacy/mock fallbacks only.
        """
        self._last_lot_sizing_diagnostic = {
            "symbol": self.symbol,
            "method": None,
            "status": "started",
            "require_broker_geometry": bool(require_broker_geometry),
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "sl_distance": sl_distance,
            "risk_amount": risk_amount,
            "tick_value_cash_risk_per_lot": None,
            "broker_cash_risk_per_lot": None,
            "broker_order_calc_profit_to_stop_per_lot": None,
            "broker_to_tick_value_risk_ratio": None,
        }
        if sl_distance <= 0 or risk_amount <= 0:
            self._last_lot_sizing_diagnostic.update({
                "status": "invalid_nonpositive_risk_or_sl_distance",
                "method": "none",
            })
            logger.error(
                "Cannot calculate lot size for %s: sl_distance=%.8f risk_amount=%.8f",
                self.symbol,
                sl_distance,
                risk_amount,
            )
            return None

        tick_value_cash_risk_per_lot: float | None = None
        try:
            # Try to get MT5 symbol info for accurate tick-value sizing
            if sym_info is None:
                sym_info = self._mt5_symbol_info()
            if sym_info is not None:
                # RealMT5 — access the MetaTrader5 module directly
                if (sym_info is not None
                        and sym_info.trade_tick_size > 0
                        and sym_info.trade_tick_value > 0):
                    ticks_at_risk = sl_distance / sym_info.trade_tick_size
                    tick_value_cash_risk_per_lot = (
                        ticks_at_risk * sym_info.trade_tick_value
                    )
                    self._last_lot_sizing_diagnostic[
                        "tick_value_cash_risk_per_lot"
                    ] = tick_value_cash_risk_per_lot
        except Exception as e:
            logger.debug("tick-value lot calc unavailable: %s", e)

        if direction and entry_price is not None and stop_loss is not None:
            profit_at_stop_per_lot = self._order_calc_profit(
                direction=direction,
                volume=1.0,
                entry_price=entry_price,
                target_price=stop_loss,
            )
            broker_cash_risk_per_lot = (
                abs(profit_at_stop_per_lot)
                if profit_at_stop_per_lot is not None and profit_at_stop_per_lot < 0
                else None
            )
            self._last_lot_sizing_diagnostic.update({
                "broker_cash_risk_per_lot": broker_cash_risk_per_lot,
                "broker_order_calc_profit_to_stop_per_lot": profit_at_stop_per_lot,
            })
            if broker_cash_risk_per_lot and broker_cash_risk_per_lot > 0:
                if tick_value_cash_risk_per_lot and tick_value_cash_risk_per_lot > 0:
                    ratio = broker_cash_risk_per_lot / tick_value_cash_risk_per_lot
                    self._last_lot_sizing_diagnostic[
                        "broker_to_tick_value_risk_ratio"
                    ] = ratio
                    if ratio > 1.25 or ratio < 0.80:
                        logger.warning(
                            "Broker cash-risk sizing differs from tick-value metadata "
                            "for %s: order_calc_per_lot=%.8f tick_value_per_lot=%.8f "
                            "ratio=%.4f",
                            self.symbol,
                            broker_cash_risk_per_lot,
                            tick_value_cash_risk_per_lot,
                            ratio,
                        )
                lots = risk_amount / broker_cash_risk_per_lot
                self._last_lot_sizing_diagnostic.update({
                    "status": "computed",
                    "method": "broker_order_calc_profit",
                    "raw_lots": lots,
                })
                logger.debug(
                    "Lot calc (broker order_calc_profit): symbol=%s sl_dist=%.5f "
                    "cash_risk_per_lot=%.8f lots=%.4f",
                    self.symbol,
                    sl_distance,
                    broker_cash_risk_per_lot,
                    lots,
                )
                return lots

        if require_broker_geometry:
            self._last_lot_sizing_diagnostic.update({
                "status": "broker_order_calc_profit_required_unavailable",
                "method": "none",
            })
            logger.error(
                "vNext selected-cell lot sizing requires broker order_calc_profit "
                "cash-risk geometry; fallback sizing is disabled"
            )
            return None

        if tick_value_cash_risk_per_lot and tick_value_cash_risk_per_lot > 0:
            lots = risk_amount / tick_value_cash_risk_per_lot
            self._last_lot_sizing_diagnostic.update({
                "status": "computed",
                "method": "tick_value_legacy_fallback",
                "raw_lots": lots,
            })
            logger.debug(
                "Lot calc (tick-value fallback): sl_dist=%.5f "
                "cash_risk_per_lot=%.8f lots=%.4f",
                sl_distance,
                tick_value_cash_risk_per_lot,
                lots,
            )
            return lots

        # Fallback: naive formula (correct for USD-quoted instruments)
        contract_size = self.config.get("risk", {}).get("contract_size", 100)
        lots = risk_amount / (sl_distance * contract_size)
        self._last_lot_sizing_diagnostic.update({
            "status": "computed",
            "method": "contract_size_legacy_fallback",
            "contract_size": contract_size,
            "raw_lots": lots,
        })
        logger.debug(
            "Lot calc (fallback): sl_dist=%.5f, contract=%d, lots=%.4f",
            sl_distance, contract_size, lots,
        )
        return lots

    # BUG #28 fix: number of outer retries for SL modification before giving
    # up + alerting. Module-level so tests can monkeypatch to 1 for speed.
    # _modify_sl itself already does 1 internal retry, so total broker
    # attempts = SL_MODIFY_MAX_ATTEMPTS * 2.
    SL_MODIFY_MAX_ATTEMPTS = 3
    # Backoff seconds between outer attempts (idx 0 = before attempt 2).
    # Tests monkeypatch self._sl_modify_backoff to a no-op for speed.
    SL_MODIFY_BACKOFF_SECONDS = (2.0, 5.0)
    PARTIAL_RESIDUAL_RECONCILE_MAX_ATTEMPTS = 8
    PARTIAL_RESIDUAL_RECONCILE_BACKOFF_SECONDS = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.5)

    def _sl_modify_backoff(self, attempt_idx: int) -> None:
        """Sleep before the next outer SL-modify attempt. Test seam.

        ``attempt_idx`` is 0 for the wait BEFORE attempt 2, 1 for attempt 3, etc.
        """
        if attempt_idx < len(self.SL_MODIFY_BACKOFF_SECONDS):
            time.sleep(self.SL_MODIFY_BACKOFF_SECONDS[attempt_idx])
        else:
            time.sleep(self.SL_MODIFY_BACKOFF_SECONDS[-1])

    @staticmethod
    def _positive_int_or_none(value) -> int | None:
        try:
            coerced = int(value)
        except (TypeError, ValueError):
            return None
        if coerced <= 0:
            return None
        return coerced

    @staticmethod
    def _position_side(position) -> str | None:
        pos_type = getattr(position, "type", None)
        if pos_type == 0:
            return "LONG"
        if pos_type == 1:
            return "SHORT"
        text = str(pos_type or "").strip().upper()
        if text in {"BUY", "LONG"}:
            return "LONG"
        if text in {"SELL", "SHORT"}:
            return "SHORT"
        return None

    @staticmethod
    def _position_snapshot(position) -> dict:
        return {
            "ticket": getattr(position, "ticket", None),
            "symbol": getattr(position, "symbol", None),
            "side": ExecutionEngine._position_side(position),
            "type": getattr(position, "type", None),
            "volume": getattr(position, "volume", None),
            "price_open": getattr(position, "price_open", None),
            "sl": getattr(position, "sl", None),
            "tp": getattr(position, "tp", None),
            "magic": getattr(position, "magic", None),
            "comment": getattr(position, "comment", None),
            "profit": getattr(position, "profit", None),
        }

    def _positions_snapshot(self, positions=None) -> list[dict]:
        if positions is None:
            try:
                positions = self.mt5.get_positions(self.symbol)
            except Exception as exc:  # noqa: BLE001
                return [{"error": str(exc)}]
        return [self._position_snapshot(position) for position in positions]

    @staticmethod
    def _result_snapshot(result) -> dict | None:
        if result is None:
            return None
        return {
            "success": bool(getattr(result, "success", False)),
            "retcode": getattr(result, "retcode", None),
            "retcode_external": getattr(result, "retcode_external", None),
            "request_id": getattr(result, "request_id", None),
            "comment": getattr(result, "comment", None),
            "order": getattr(result, "order", None),
            "deal": getattr(result, "deal", None),
            "volume": getattr(result, "volume", None),
            "price": getattr(result, "price", None),
        }

    def _symbol_info_snapshot(self) -> dict:
        info = self._mt5_symbol_info()
        if info is None:
            return {
                "available": False,
                "missing_reason": "mt5_symbol_info_unavailable",
            }
        fields = [
            "name",
            "trade_stops_level",
            "trade_freeze_level",
            "point",
            "trade_tick_size",
            "trade_tick_value",
            "volume_min",
            "volume_max",
            "volume_step",
            "trade_contract_size",
        ]
        snapshot = {"available": True}
        for field_name in fields:
            snapshot[field_name] = getattr(info, field_name, None)
        return snapshot

    def _tick_snapshot(self) -> dict:
        try:
            tick = self.mt5.get_tick(self.symbol)
        except Exception as exc:  # noqa: BLE001
            return {"available": False, "missing_reason": str(exc)}
        if tick is None:
            return {"available": False, "missing_reason": "mt5_tick_unavailable"}
        return {
            "available": True,
            "bid": getattr(tick, "bid", None),
            "ask": getattr(tick, "ask", None),
            "spread_cents": getattr(tick, "spread_cents", None),
            "time": getattr(tick, "time", None).isoformat()
            if hasattr(getattr(tick, "time", None), "isoformat")
            else getattr(tick, "time", None),
        }

    def _record_sltp_modify_diagnostic(
        self,
        *,
        trade: TradeState | None,
        diagnostic: dict,
    ) -> None:
        self._last_sltp_modify_diagnostic = diagnostic
        if trade is not None:
            trade.partial_close_events.append({
                "type": "SLTP_MODIFY_DIAGNOSTIC",
                "time": datetime.now(timezone.utc).isoformat(),
                **diagnostic,
            })

    def _sltp_modify_diagnostic(
        self,
        *,
        request: dict,
        result,
        modify_kind: str,
        modify_reason: str,
        attempt: int,
        positions_before: list,
        positions_after: list | None = None,
    ) -> dict:
        ticket = request.get("position")
        matching = [
            p for p in positions_before
            if getattr(p, "ticket", None) == ticket
        ]
        position = matching[0] if matching else None
        return {
            "diagnostic_version": "vnext_sltp_modify_diagnostic_v1",
            "modify_kind": modify_kind,
            "modify_reason": modify_reason,
            "attempt": attempt,
            "symbol": self.symbol,
            "ticket": ticket,
            "side": self._position_side(position) if position is not None else None,
            "volume": getattr(position, "volume", None),
            "current_sl": getattr(position, "sl", None),
            "current_tp": getattr(position, "tp", None),
            "desired_sl": request.get("sl"),
            "desired_tp": request.get("tp"),
            "request": dict(request),
            "result": self._result_snapshot(result),
            "symbol_info": self._symbol_info_snapshot(),
            "tick": self._tick_snapshot(),
            "current_positions_before": self._positions_snapshot(positions_before),
            "current_positions_after": (
                self._positions_snapshot(positions_after)
                if positions_after is not None
                else None
            ),
        }

    def _find_residual_position_after_partial(
        self,
        trade: TradeState,
        positions: list,
        *,
        closed_ticket: int,
        closed_volume: float,
        previous_volume: float,
        close_result=None,
        close_reason: str,
    ):
        """Find the residual position after a partial close without using list order."""
        expected_remaining = round(max(previous_volume - closed_volume, 0.0), 2)
        volume_tolerance = max(0.011, abs(expected_remaining) * 0.0001)

        def _position_volume(position) -> float:
            return float(getattr(position, "volume", 0.0) or 0.0)

        def _residual_volume_matches(position) -> bool:
            return abs(_position_volume(position) - expected_remaining) <= volume_tolerance

        def _resolve(candidates_source: list):
            candidates = [
                p for p in candidates_source
                if getattr(p, "magic", MAGIC_NUMBER) == MAGIC_NUMBER
            ]

            symbol_matches = [
                p for p in candidates
                if str(getattr(p, "symbol", "") or "").upper() == self.symbol.upper()
            ]
            if symbol_matches:
                candidates = symbol_matches

            side_matches = [
                p for p in candidates
                if self._position_side(p) == trade.direction
            ]
            if side_matches:
                candidates = side_matches

            volume_matches = [
                p for p in candidates
                if _residual_volume_matches(p)
            ]
            if len(volume_matches) == 1:
                return volume_matches[0]
            if len(volume_matches) > 1:
                non_closed_volume_matches = [
                    p for p in volume_matches
                    if getattr(p, "ticket", None) != closed_ticket
                ]
                candidates = non_closed_volume_matches or volume_matches

            ticket_matches = [
                p for p in candidates
                if getattr(p, "ticket", None) == closed_ticket
                and _residual_volume_matches(p)
            ]
            if len(ticket_matches) == 1:
                return ticket_matches[0]

            non_closed = [
                p for p in candidates
                if getattr(p, "ticket", None) != closed_ticket
            ]
            if non_closed:
                candidates = non_closed

            price_matches = [
                p for p in candidates
                if _residual_volume_matches(p)
                and abs(float(getattr(p, "price_open", 0.0) or 0.0) - trade.entry_price) <= 1e-6
            ]
            if len(price_matches) == 1:
                return price_matches[0]
            return None

        attempts = 0
        current_positions = positions or []
        max_attempts = max(1, int(self.PARTIAL_RESIDUAL_RECONCILE_MAX_ATTEMPTS))
        while attempts < max_attempts:
            attempts += 1
            resolved = _resolve(current_positions)
            if resolved is not None:
                if attempts > 1 or not positions:
                    trade.partial_close_events.append({
                        "type": "PARTIAL_CLOSE_RESIDUAL_TICKET_RECONCILED",
                        "time": datetime.now(timezone.utc).isoformat(),
                        "symbol": self.symbol,
                        "trade_id": trade.trade_id,
                        "closed_ticket": closed_ticket,
                        "resolved_ticket": getattr(resolved, "ticket", None),
                        "closed_volume": closed_volume,
                        "previous_volume": previous_volume,
                        "expected_remaining_volume": expected_remaining,
                        "resolved_volume": getattr(resolved, "volume", None),
                        "resolution_attempts": attempts,
                        "close_reason": close_reason,
                        "resolution_status": "resolved_after_broker_position_refresh",
                    })
                return resolved
            if attempts >= max_attempts:
                break
            backoff_idx = min(
                attempts - 1,
                len(self.PARTIAL_RESIDUAL_RECONCILE_BACKOFF_SECONDS) - 1,
            )
            time.sleep(self.PARTIAL_RESIDUAL_RECONCILE_BACKOFF_SECONDS[backoff_idx])
            try:
                current_positions = self.mt5.get_positions(self.symbol) or []
            except Exception:  # noqa: BLE001
                current_positions = []

        diagnostic = {
            "diagnostic_version": "vnext_partial_close_residual_resolution_v1",
            "type": "PARTIAL_CLOSE_RESIDUAL_TICKET_UNRESOLVED",
            "time": datetime.now(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "trade_id": trade.trade_id,
            "direction": trade.direction,
            "closed_ticket": closed_ticket,
            "closed_volume": closed_volume,
            "previous_volume": previous_volume,
            "expected_remaining_volume": expected_remaining,
            "volume_tolerance": volume_tolerance,
            "close_reason": close_reason,
            "close_result": self._result_snapshot(close_result),
            "resolution_attempts": attempts,
            "candidate_positions": self._positions_snapshot(current_positions or positions),
            "resolution_status": "ambiguous_or_missing_residual_position",
        }
        trade.partial_close_events.append(diagnostic)
        logger.error("Partial-close residual position unresolved: %s", diagnostic)
        return None

    def _move_sl_to_breakeven(self, trade: TradeState, ticket: int):
        """Attempt to move SL to breakeven with retry + alert on failure.

        BUG #28 fix (2026-04-28): the prior implementation called
        ``self.close_position("sl_modification_failed")`` when the broker
        rejected the SL modify. That behavior threw away a fully-valid
        existing SL (which is the safety floor) and force-closed the
        position — directly responsible for the GBPJPY +0.74R cap when
        the trade was on its way to a +6R target.

        New contract:
          1. Try ``_modify_sl`` up to ``SL_MODIFY_MAX_ATTEMPTS`` times
             with exponential backoff between outer attempts.
          2. On success: set ``trade.sl_at_breakeven = True`` and update
             ``trade.stop_loss``, log info.
          3. On all-attempts-failure: log ERROR, send ``notify_alert``
             to the CEO, AND **leave the existing SL untouched** —
             never close the position because of an SL-move failure.

        The position remains open with whatever SL the broker has
        (the original safety stop). Live trading continues; the
        CEO is paged so a human can investigate the broker rejection.
        """
        old_stop_loss = trade.stop_loss
        for attempt in range(1, self.SL_MODIFY_MAX_ATTEMPTS + 1):
            success = self._modify_sl(
                ticket,
                trade.entry_price,
                trade=trade,
                modify_reason="sl_to_breakeven",
            )
            if success:
                trade.sl_at_breakeven = True
                trade.stop_loss = trade.entry_price
                trade.partial_close_events.append({
                    "type": "SL_TO_BREAKEVEN_MODIFY_SUCCESS",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "ticket": ticket,
                    "attempt": attempt,
                    "old_stop_loss": old_stop_loss,
                    "new_stop_loss": trade.entry_price,
                    "actual_be_movement_captured": True,
                })
                logger.info(
                    "SL moved to breakeven: %.5f (attempt %d/%d, ticket %d)",
                    trade.entry_price, attempt, self.SL_MODIFY_MAX_ATTEMPTS,
                    ticket,
                )
                self._notify_vnext_lifecycle(
                    trade,
                    "BE transition",
                    price=trade.entry_price,
                    detail="SL_TO_BREAKEVEN_MODIFY_SUCCESS",
                )
                return
            logger.warning(
                "SL->BE modify failed: attempt %d/%d (ticket=%d, target=%.5f)",
                attempt, self.SL_MODIFY_MAX_ATTEMPTS, ticket, trade.entry_price,
            )
            if attempt < self.SL_MODIFY_MAX_ATTEMPTS:
                self._sl_modify_backoff(attempt - 1)

        # All retries exhausted. Leave the existing SL alone, alert the CEO.
        trade.partial_close_events.append({
            "type": "SL_TO_BREAKEVEN_MODIFY_FAILED",
            "time": datetime.now(timezone.utc).isoformat(),
            "ticket": ticket,
            "attempts": self.SL_MODIFY_MAX_ATTEMPTS,
            "old_stop_loss": old_stop_loss,
            "requested_stop_loss": trade.entry_price,
            "actual_stop_loss_preserved": trade.stop_loss,
            "actual_be_movement_captured": True,
            "last_sltp_modify_diagnostic": self._last_sltp_modify_diagnostic,
        })
        logger.error(
            "SL->BE modify FAILED after %d attempts for ticket=%d; "
            "leaving existing SL=%.5f untouched (NOT closing position). "
            "Broker rejection requires human investigation.",
            self.SL_MODIFY_MAX_ATTEMPTS, ticket, trade.stop_loss,
        )
        try:
            from src.notifications import notify_alert
            notify_alert(
                f"[CRITICAL] SL->BE failed after {self.SL_MODIFY_MAX_ATTEMPTS} "
                f"attempts on {self.symbol} ticket={ticket}. Existing SL "
                f"({trade.stop_loss:.5f}) preserved; position remains open. "
                "Investigate broker freeze level / spread / disabled symbol."
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "notify_alert failed for SL-modify failure (non-fatal): %s",
                exc,
            )

    @staticmethod
    def _retcode_no_changes(result) -> bool:
        try:
            return int(getattr(result, "retcode", 0) or 0) == 10025
        except (TypeError, ValueError):
            return False

    def _sltp_modify_defer_reason_for_stale_tick(self) -> str | None:
        try:
            tick = self.mt5.get_tick(self.symbol)
        except Exception as exc:  # noqa: BLE001
            return f"tick_read_failed:{exc}"
        if tick is None:
            return "tick_unavailable"
        tick_time = getattr(tick, "time", None)
        if tick_time is None:
            return "tick_time_unavailable"
        if isinstance(tick_time, str):
            try:
                tick_time = datetime.fromisoformat(tick_time.replace("Z", "+00:00"))
            except ValueError:
                return "tick_time_unparseable"
        if not hasattr(tick_time, "astimezone"):
            return "tick_time_unparseable"
        if tick_time.tzinfo is None:
            tick_time = tick_time.replace(tzinfo=timezone.utc)
        age_seconds = (datetime.now(timezone.utc) - tick_time.astimezone(timezone.utc)).total_seconds()
        if age_seconds > 30 * 60:
            return f"stale_tick_age_seconds:{age_seconds:.0f}"
        return None

    def _sltp_request_already_matches_position(
        self,
        position,
        request: dict,
        *,
        modify_kind: str,
    ) -> bool:
        # MT5 retcode 10025 means the broker accepted the request as a no-op.
        # Compare at one full tick so floating point half-tick rounding does not
        # turn a broker-rounded no-op into a false SL/TP failure.
        tolerance = max(self._sltp_price_tick_size(), 1e-9)
        if modify_kind == "SL":
            desired = float(request.get("sl", 0.0) or 0.0)
            actual = float(getattr(position, "sl", 0.0) or 0.0)
            return abs(actual - desired) <= tolerance
        if modify_kind == "TP":
            desired = float(request.get("tp", 0.0) or 0.0)
            actual = float(getattr(position, "tp", 0.0) or 0.0)
            return abs(actual - desired) <= tolerance
        return False

    def _modify_sl(
        self,
        ticket: int,
        new_sl: float,
        *,
        trade: TradeState | None = None,
        modify_reason: str = "",
    ) -> bool:
        positions = self.mt5.get_positions(self.symbol)
        current_tp = 0.0
        target_position = None
        for p in positions:
            if p.ticket == ticket:
                target_position = p
                current_tp = p.tp
                break

        request = {
            "action": TRADE_ACTION_SLTP, "symbol": self.symbol, "position": ticket,
            "sl": new_sl, "tp": current_tp,
        }
        if target_position is None:
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=None,
                modify_kind="SL",
                modify_reason=modify_reason or "modify_sl",
                attempt=0,
                positions_before=positions,
                positions_after=positions,
            )
            diagnostic["failure_reason"] = "position_ticket_not_found_before_modify"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.error("SL modify aborted: %s", diagnostic)
            return False
        try:
            self._runtime_halt_snapshot(
                "modify_sl",
                {
                    "ticket": ticket,
                    "new_sl": new_sl,
                    "modify_reason": modify_reason or "modify_sl",
                },
            )
        except RuntimeHaltError as exc:
            if not self._sl_modify_reduces_or_preserves_risk(target_position, new_sl):
                runtime_diagnostic = self._record_runtime_halt_diagnostic(
                    action="modify_sl",
                    exc=exc,
                    extra={
                        "ticket": ticket,
                        "new_sl": new_sl,
                        "modify_reason": modify_reason or "modify_sl",
                        "risk_reducing_management_allowed": False,
                    },
                )
                diagnostic = self._sltp_modify_diagnostic(
                    request=request,
                    result=None,
                    modify_kind="SL",
                    modify_reason=modify_reason or "modify_sl",
                    attempt=0,
                    positions_before=positions,
                    positions_after=positions,
                )
                diagnostic["failure_reason"] = "runtime_halt_active_sl_modify_not_risk_reducing"
                diagnostic["runtime_halt_diagnostic"] = runtime_diagnostic
                self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
                logger.warning("SL modify blocked by atomic runtime halt: %s", diagnostic)
                return False

        result = self.mt5.order_send(request)
        lifecycle_extra = {
            "modify_kind": "SL",
            "attempt": 1,
            "modify_reason": modify_reason or "modify_sl",
        }
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            target_position,
            request,
            modify_kind="SL",
        ):
            lifecycle_extra["benign_retcode_status"] = "no_changes_already_matched"
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra=lifecycle_extra,
        )
        if result.success:
            return True
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            target_position,
            request,
            modify_kind="SL",
        ):
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=result,
                modify_kind="SL",
                modify_reason=modify_reason or "modify_sl",
                attempt=1,
                positions_before=positions,
                positions_after=self.mt5.get_positions(self.symbol),
            )
            diagnostic["benign_retcode_status"] = "no_changes_already_matched"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.info("SL modify already matched target state: %s", diagnostic)
            return True
        diagnostic = self._sltp_modify_diagnostic(
            request=request,
            result=result,
            modify_kind="SL",
            modify_reason=modify_reason or "modify_sl",
            attempt=1,
            positions_before=positions,
            positions_after=self.mt5.get_positions(self.symbol),
        )
        self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
        logger.warning("SL modify failed (attempt 1): %s", diagnostic)
        time.sleep(1)
        retry_positions = self.mt5.get_positions(self.symbol)
        retry_position = next((p for p in retry_positions if p.ticket == ticket), None)
        try:
            self._runtime_halt_snapshot(
                "modify_sl",
                {
                    "ticket": ticket,
                    "new_sl": new_sl,
                    "modify_reason": modify_reason or "modify_sl",
                    "attempt": 2,
                },
            )
        except RuntimeHaltError as exc:
            if retry_position is None or not self._sl_modify_reduces_or_preserves_risk(
                retry_position,
                new_sl,
            ):
                runtime_diagnostic = self._record_runtime_halt_diagnostic(
                    action="modify_sl",
                    exc=exc,
                    extra={
                        "ticket": ticket,
                        "new_sl": new_sl,
                        "modify_reason": modify_reason or "modify_sl",
                        "attempt": 2,
                        "risk_reducing_management_allowed": False,
                    },
                )
                diagnostic = self._sltp_modify_diagnostic(
                    request=request,
                    result=None,
                    modify_kind="SL",
                    modify_reason=modify_reason or "modify_sl",
                    attempt=2,
                    positions_before=retry_positions,
                    positions_after=retry_positions,
                )
                diagnostic["failure_reason"] = (
                    "runtime_halt_active_sl_retry_modify_not_risk_reducing"
                )
                diagnostic["runtime_halt_diagnostic"] = runtime_diagnostic
                diagnostic["broker_request_sent"] = False
                self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
                self._record_broker_runtime_lifecycle_event(
                    stage="sltp_modify_blocked",
                    request=None,
                    result=None,
                    trade=trade,
                    extra={
                        "ticket": ticket,
                        "modify_kind": "SL",
                        "attempt": 2,
                        "modify_reason": modify_reason or "modify_sl",
                        "deferred_request": dict(request),
                        "broker_request_sent": False,
                        "broker_operation_observed": False,
                        "broker_operation_source_status": "blocked_before_broker_request",
                        "failure_reason": (
                            "runtime_halt_active_sl_retry_modify_not_risk_reducing"
                        ),
                        "runtime_halt_diagnostic": runtime_diagnostic,
                    },
                )
                logger.warning("SL modify retry blocked by atomic runtime halt: %s", diagnostic)
                return False
        result = self.mt5.order_send(request)
        retry_lifecycle_extra = {
            "modify_kind": "SL",
            "attempt": 2,
            "modify_reason": modify_reason or "modify_sl",
        }
        retry_position = retry_position or target_position
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            retry_position,
            request,
            modify_kind="SL",
        ):
            retry_lifecycle_extra["benign_retcode_status"] = "no_changes_already_matched"
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra=retry_lifecycle_extra,
        )
        if result.success:
            return True
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            retry_position,
            request,
            modify_kind="SL",
        ):
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=result,
                modify_kind="SL",
                modify_reason=modify_reason or "modify_sl",
                attempt=2,
                positions_before=retry_positions,
                positions_after=self.mt5.get_positions(self.symbol),
            )
            diagnostic["benign_retcode_status"] = "no_changes_already_matched"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.info("SL modify retry already matched target state: %s", diagnostic)
            return True
        diagnostic = self._sltp_modify_diagnostic(
            request=request,
            result=result,
            modify_kind="SL",
            modify_reason=modify_reason or "modify_sl",
            attempt=2,
            positions_before=retry_positions,
            positions_after=self.mt5.get_positions(self.symbol),
        )
        self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
        logger.error("SL modify FAILED after retry: %s", diagnostic)
        return False

    def _modify_tp(
        self,
        ticket: int,
        new_tp: float,
        *,
        trade: TradeState | None = None,
        identity_direction: str | None = None,
        identity_trade_id: str | None = None,
        modify_reason: str = "",
    ) -> bool:
        positions = self.mt5.get_positions(self.symbol)
        current_sl = 0.0
        target_position = None
        for p in positions:
            if p.ticket == ticket:
                target_position = p
                current_sl = p.sl
                break

        request = {
            "action": TRADE_ACTION_SLTP, "symbol": self.symbol, "position": ticket,
            "sl": current_sl, "tp": new_tp,
        }
        if target_position is None:
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=None,
                modify_kind="TP",
                modify_reason=modify_reason or "modify_tp",
                attempt=0,
                positions_before=positions,
                positions_after=positions,
            )
            diagnostic["failure_reason"] = "position_ticket_not_found_before_modify"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.error("TP modify aborted: %s", diagnostic)
            return False

        try:
            self._runtime_halt_snapshot(
                "modify_tp",
                {
                    "ticket": ticket,
                    "new_tp": new_tp,
                    "modify_reason": modify_reason or "modify_tp",
                },
            )
        except RuntimeHaltError as exc:
            runtime_diagnostic = self._record_runtime_halt_diagnostic(
                action="modify_tp",
                exc=exc,
                extra={
                    "ticket": ticket,
                    "new_tp": new_tp,
                    "modify_reason": modify_reason or "modify_tp",
                    "risk_reducing_management_allowed": False,
                },
            )
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=None,
                modify_kind="TP",
                modify_reason=modify_reason or "modify_tp",
                attempt=0,
                positions_before=positions,
                positions_after=positions,
            )
            diagnostic["failure_reason"] = "runtime_halt_active_tp_modify_blocked"
            diagnostic["runtime_halt_diagnostic"] = runtime_diagnostic
            diagnostic["broker_request_sent"] = False
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            self._record_broker_runtime_lifecycle_event(
                stage="sltp_modify_blocked",
                request=None,
                result=None,
                trade=trade,
                extra={
                    "ticket": ticket,
                    "modify_kind": "TP",
                    "attempt": 0,
                    "modify_reason": modify_reason or "modify_tp",
                    "direction": identity_direction,
                    "trade_id": identity_trade_id,
                    "deferred_request": dict(request),
                    "broker_request_sent": False,
                    "broker_operation_observed": False,
                    "broker_operation_source_status": "blocked_before_broker_request",
                    "failure_reason": "runtime_halt_active_tp_modify_blocked",
                    "runtime_halt_diagnostic": runtime_diagnostic,
                },
            )
            logger.warning("TP modify blocked by atomic runtime halt: %s", diagnostic)
            return False

        current_tp = float(getattr(target_position, "tp", 0.0) or 0.0)
        if current_tp > 0:
            defer_reason = self._sltp_modify_defer_reason_for_stale_tick()
            if defer_reason:
                diagnostic = self._sltp_modify_diagnostic(
                    request=request,
                    result=None,
                    modify_kind="TP",
                    modify_reason=modify_reason or "modify_tp",
                    attempt=0,
                    positions_before=positions,
                    positions_after=positions,
                )
                diagnostic["benign_deferred_status"] = (
                    "tp_modify_deferred_existing_broker_tp_preserved"
                )
                diagnostic["defer_reason"] = defer_reason
                diagnostic["broker_request_sent"] = False
                self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
                self._record_broker_runtime_lifecycle_event(
                    stage="sltp_modify_deferred",
                    request=None,
                    result=None,
                    trade=trade,
                    extra={
                        "modify_kind": "TP",
                        "attempt": 0,
                        "modify_reason": modify_reason or "modify_tp",
                        "defer_reason": defer_reason,
                        "deferred_request": dict(request),
                        "broker_request_sent": False,
                        "broker_operation_observed": False,
                        "broker_operation_source_status": "deferred_before_broker_request",
                        "benign_deferred_status": (
                            "tp_modify_deferred_existing_broker_tp_preserved"
                        ),
                    },
                )
                logger.info(
                    "TP modify deferred with existing broker TP preserved: %s",
                    diagnostic,
                )
                return False

        result = self.mt5.order_send(request)
        lifecycle_extra = {
            "modify_kind": "TP",
            "attempt": 1,
            "modify_reason": modify_reason or "modify_tp",
            "direction": identity_direction,
            "trade_id": identity_trade_id,
        }
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            target_position,
            request,
            modify_kind="TP",
        ):
            lifecycle_extra["benign_retcode_status"] = "no_changes_already_matched"
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra=lifecycle_extra,
        )
        if result.success:
            return True
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            target_position,
            request,
            modify_kind="TP",
        ):
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=result,
                modify_kind="TP",
                modify_reason=modify_reason or "modify_tp",
                attempt=1,
                positions_before=positions,
                positions_after=self.mt5.get_positions(self.symbol),
            )
            diagnostic["benign_retcode_status"] = "no_changes_already_matched"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.info("TP modify already matched target state: %s", diagnostic)
            return True
        diagnostic = self._sltp_modify_diagnostic(
            request=request,
            result=result,
            modify_kind="TP",
            modify_reason=modify_reason or "modify_tp",
            attempt=1,
            positions_before=positions,
            positions_after=self.mt5.get_positions(self.symbol),
        )
        self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
        logger.warning("TP modify failed (attempt 1): %s; retrying", diagnostic)
        time.sleep(1)
        retry_positions = self.mt5.get_positions(self.symbol)
        try:
            self._runtime_halt_snapshot(
                "modify_tp",
                {
                    "ticket": ticket,
                    "new_tp": new_tp,
                    "modify_reason": modify_reason or "modify_tp",
                    "attempt": 2,
                },
            )
        except RuntimeHaltError as exc:
            runtime_diagnostic = self._record_runtime_halt_diagnostic(
                action="modify_tp",
                exc=exc,
                extra={
                    "ticket": ticket,
                    "new_tp": new_tp,
                    "modify_reason": modify_reason or "modify_tp",
                    "attempt": 2,
                    "risk_reducing_management_allowed": False,
                },
            )
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=None,
                modify_kind="TP",
                modify_reason=modify_reason or "modify_tp",
                attempt=2,
                positions_before=retry_positions,
                positions_after=retry_positions,
            )
            diagnostic["failure_reason"] = "runtime_halt_active_tp_retry_modify_blocked"
            diagnostic["runtime_halt_diagnostic"] = runtime_diagnostic
            diagnostic["broker_request_sent"] = False
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            self._record_broker_runtime_lifecycle_event(
                stage="sltp_modify_blocked",
                request=None,
                result=None,
                trade=trade,
                extra={
                    "ticket": ticket,
                    "modify_kind": "TP",
                    "attempt": 2,
                    "modify_reason": modify_reason or "modify_tp",
                    "direction": identity_direction,
                    "trade_id": identity_trade_id,
                    "deferred_request": dict(request),
                    "broker_request_sent": False,
                    "broker_operation_observed": False,
                    "broker_operation_source_status": "blocked_before_broker_request",
                    "failure_reason": "runtime_halt_active_tp_retry_modify_blocked",
                    "runtime_halt_diagnostic": runtime_diagnostic,
                },
            )
            logger.warning("TP modify retry blocked by atomic runtime halt: %s", diagnostic)
            return False
        result = self.mt5.order_send(request)
        retry_position = next((p for p in retry_positions if p.ticket == ticket), target_position)
        retry_lifecycle_extra = {
            "modify_kind": "TP",
            "attempt": 2,
            "modify_reason": modify_reason or "modify_tp",
        }
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            retry_position,
            request,
            modify_kind="TP",
        ):
            retry_lifecycle_extra["benign_retcode_status"] = "no_changes_already_matched"
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra=retry_lifecycle_extra,
        )
        if result.success:
            return True
        if self._retcode_no_changes(result) and self._sltp_request_already_matches_position(
            retry_position,
            request,
            modify_kind="TP",
        ):
            diagnostic = self._sltp_modify_diagnostic(
                request=request,
                result=result,
                modify_kind="TP",
                modify_reason=modify_reason or "modify_tp",
                attempt=2,
                positions_before=retry_positions,
                positions_after=self.mt5.get_positions(self.symbol),
            )
            diagnostic["benign_retcode_status"] = "no_changes_already_matched"
            self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
            logger.info("TP modify retry already matched target state: %s", diagnostic)
            return True
        diagnostic = self._sltp_modify_diagnostic(
            request=request,
            result=result,
            modify_kind="TP",
            modify_reason=modify_reason or "modify_tp",
            attempt=2,
            positions_before=retry_positions,
            positions_after=self.mt5.get_positions(self.symbol),
        )
        self._record_sltp_modify_diagnostic(trade=trade, diagnostic=diagnostic)
        logger.error(
            "TP modify FAILED after retry; continuing with existing TP: %s",
            diagnostic,
        )
        return False

    def _write_checkpoint(self, data: dict):
        Path(self._checkpoint_path).parent.mkdir(parents=True, exist_ok=True)
        if self._runtime_namespace:
            data = {**data, "runtime_namespace": self._runtime_namespace}
        atomic_write(self._checkpoint_path, data)

    def _clear_checkpoint(self):
        path = Path(self._checkpoint_path)
        if path.exists():
            path.unlink()

    def _record_close(self, reason: str):
        if self.active_trade:
            self.active_trade.partial_close_events.append({
                "type": f"CLOSE_{reason.upper()}",
                "time": datetime.now(timezone.utc).isoformat(),
            })

    # === CRASH RECOVERY ===

    def adopt_specific_position(self, p) -> bool:
        """Adopt ONE specific broker position into active_trade. Returns True if adopted, False if this
        engine already holds a position (single-position engine). The W7 book routes each ticket to its
        OWN per-(symbol, sleeve) engine, so a symbol held by multiple sleeves no longer collides on one
        active_trade slot (which silently orphaned all-but-one ticket from exit management)."""
        if self.active_trade is not None:
            return False
        self._known_tickets.add(p.ticket)
        self.active_trade = TradeState(
            ticket=p.ticket,
            direction="LONG" if p.type == 0 else "SHORT",
            entry_price=p.price_open,
            stop_loss=p.sl,
            take_profit_1=p.tp,
            take_profit_2=0,
            take_profit_3=0,
            initial_volume=p.volume,
            current_volume=p.volume,
            sl_distance=abs(p.price_open - p.sl) if p.sl > 0 else 10.0,
            trade_id=f"adopted_{p.ticket}",
            entry_time=p.time.isoformat(),
            # We are looking at this position right now via positions_get, so the propagation-race guard
            # isn't applicable — mark position_confirmed=True so the next check_and_manage_trade call
            # doesn't think the trade is mid-fill.
            position_confirmed=True,
        )
        return True

    def reconcile_on_startup(self, comment_filter: Optional[str] = None) -> list[str]:
        """Called during bootstrap. Reconciles agent state with MT5 reality.

        comment_filter: when set (W7 book per-(symbol, sleeve) management), only positions whose broker
        comment EQUALS it are considered — so each sleeve's engine adopts ONLY its own ticket on a symbol
        shared by several sleeves (e.g. XAUUSD across metals_core / metals_softband / metals_ob_micro).
        A filtered-empty match never phantom-closes (an empty filter result does not mean the position is
        gone). comment_filter=None preserves the original symbol-wide behavior (orchestrator/legacy)."""
        actions = []

        checkpoint_path = Path(self._checkpoint_path)
        if checkpoint_path.exists():
            with open(checkpoint_path) as f:
                checkpoint = json.load(f)
            logger.warning(f"Found execution checkpoint: {checkpoint}")
            actions.append(f"checkpoint_found: {checkpoint['action']}")
            checkpoint_path.unlink()

        raw_positions = self.mt5.get_positions(self.symbol)
        positions = raw_positions
        if comment_filter is not None:
            positions = [p for p in (raw_positions or [])
                         if (getattr(p, "comment", "") or "") == comment_filter]

        if positions and self.active_trade is None:
            for p in positions:
                logger.warning(f"Orphan position found: ticket={p.ticket}, "
                               f"volume={p.volume}, profit={p.profit}")
                self._known_tickets.add(p.ticket)   # track ALL orphans (unchanged: a not-yet-adopted
                                                    # sibling must not later read as a brand-new position)
                if self.active_trade is None and self.adopt_specific_position(p):
                    actions.append(f"orphan_adopted: ticket={p.ticket}")
                    if comment_filter is not None:
                        break   # the book's per-(symbol, sleeve) engine holds exactly one ticket

        elif comment_filter is None and not raw_positions and self.active_trade is not None:
            logger.warning(f"Phantom trade: we have {self.active_trade.ticket} "
                           f"but MT5 has no positions")
            actions.append(f"phantom_closed: ticket={self.active_trade.ticket}")
            self.active_trade = None

        return actions
