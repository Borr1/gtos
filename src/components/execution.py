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
    comment_prefix_for_magic,
    magic_for_namespace,
    MAGIC_F5_MINIMAL,
    COMMENT_PREFIX_F5_MINIMAL,
    TRADE_ACTION_DEAL,
    TRADE_ACTION_PENDING,
    TRADE_ACTION_REMOVE,
    TRADE_ACTION_SLTP,
    ORDER_TYPE_BUY_LIMIT,
    ORDER_TYPE_SELL_LIMIT,
    is_order_send_none,
)
from src.utils.broker_profile import broker_account_namespace, namespaced_file_path
from src.utils.file_io import atomic_write
from src.components.pending_limit_lifecycle_logger import (
    DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_FIELD,
    DENOMINATOR_FORWARD_CAPTURE_REQUIREMENT_FAMILIES_FIELD,
    DENOMINATOR_FORWARD_CAPTURE_RUNTIME_CONFIG_FIELD,
    record_pending_limit_lifecycle,
)
from src.components.denominator_forward_capture_contract import (
    ENABLED_CONFIG_KEY as DENOMINATOR_FORWARD_CAPTURE_ENABLED_CONFIG_KEY,
    LOG_ENABLED_CONFIG_KEY as DENOMINATOR_FORWARD_CAPTURE_LOG_ENABLED_CONFIG_KEY,
    LOG_PATH_CONFIG_KEY as DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_CONFIG_KEY,
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
from src.components.poi_execution_lifecycle import (
    causal_poi_lifecycle_contract_failures,
)
from src.components.exit_policy_v4 import (
    ExitPolicyConfigV4,
    ExitPolicyDecisionV4,
    ExitPolicyInputV4,
    evaluate_exit_policy_v4,
)
from src.safety.runtime_halt import RuntimeHaltError, enforce_runtime_not_halted
from src.safety.activation_token import (
    ActivationTokenError,
    deal_reduces_existing_position,
    deal_request_is_structurally_a_close,
    sltp_reduces_or_preserves_risk,
)

logger = logging.getLogger(__name__)

#: Step-count tolerance for broker volume-step alignment. See `_normalize_volume`:
#: a quotient that is mathematically an exact integer can land a few ULPs below one in
#: binary floating point, and truncating it strands a position that cannot be closed.
#: Sized to absorb float error (~1e-12 at ten thousand steps) without being large enough
#: to promote a genuinely mis-aligned volume to the next step.
_VOLUME_STEP_EPSILON = 1e-9

CHECKPOINT_PATH = "knowledge_base/meta/execution_checkpoint.json"
PENDING_INTENT_DIR = "knowledge_base/meta"

# safe_place_order returns Python None on exactly these three diagnostic statuses.
# open_trade must surface the status itself — never the convenience lie
# ``timeout_no_fill`` — so book_owner's transient list can tell a token refusal
# (terminal) from a wait that ended with no position. On Challenge that label
# is the timeout hop. It is not planted when the ask is empty.
NONE_PLACE_STATUSES = (
    "activation_refused",
    "timeout_no_position",
    "order_send_exception",
)


_FILLING_ENUM = {
    "fok": 0,      # ORDER_FILLING_FOK
    "ioc": 1,      # ORDER_FILLING_IOC
    "return": 2,   # ORDER_FILLING_RETURN
    "boc": 3,      # ORDER_FILLING_BOC
}


def _challenge_diagnostic(diagnostic: dict) -> bool:
    ns = str(diagnostic.get("ns") or diagnostic.get("namespace") or "")
    if ns == "operator":
        return True
    try:
        return int(diagnostic.get("login")) == 0
    except (TypeError, ValueError):
        return False


def label_none_place_result(diagnostic) -> tuple[str, str]:
    """Map a ``safe_place_order`` None onto ``(log_reason, block_reason)``.

    ``log_reason`` is the diagnostic status (what the operator log must say).
    ``block_reason`` is what ``book_owner._is_transient_place_failure`` classifies.
    ``activation_refused`` must not be prefixed with ``order_rejected:`` — that
    prefix is transient and is what turned 129 token refusals into a storm.

    On Challenge an unnamed status is the timeout-label hop. An empty answer
    does not restore ``timeout_no_position``. Other books keep the old label.
    """
    diag = diagnostic if isinstance(diagnostic, dict) else {}
    status = str(diag.get("status") or "").strip()
    if not _challenge_diagnostic(diag):
        if status not in NONE_PLACE_STATUSES:
            status = "timeout_no_position"
        if status == "activation_refused":
            detail = str(diag.get("activation_decision_reason") or "").strip()
            block = f"activation_refused:{detail}" if detail else "activation_refused"
            return status, block
        return status, status
    if status == "activation_refused":
        detail = str(diag.get("activation_decision_reason") or "").strip()
        block = f"activation_refused:{detail}" if detail else "activation_refused"
        return status, block
    if status:
        return status, status
    try:
        from src.judgment.execution_choices import choose

        row = choose(
            "timeout_label",
            symbol=diag.get("symbol"),
            reason="none_place",
            facts={
                "status": None,
                "error": diag.get("error"),
                "symbol": diag.get("symbol"),
            },
        )
    except Exception:
        row = {}
    choice = None
    if isinstance(row, dict) and row.get("decision_emitted"):
        choice = row.get("choice")
    if choice in ("timeout_no_position", "order_send_exception"):
        return str(choice), str(choice)
    return "exec_timeout:no_decision", "exec_timeout:no_decision"
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
    gtos_vnext_profit_harvest_stop_activation_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_target_activation_fraction: float = 0.0
    gtos_vnext_profit_harvest_trail_gap_r: float = 0.0
    gtos_vnext_profit_harvest_protect_floor_r: float = 0.0
    gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled: bool = False
    gtos_vnext_profit_harvest_cost_aware_margin_r: float = 0.0
    gtos_vnext_profit_harvest_close_on_giveback_r: float = 0.0
    gtos_vnext_profit_harvest_stale_minutes: Optional[int] = None
    gtos_vnext_profit_harvest_stale_min_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_stale_close_below_r: float = 0.0
    gtos_vnext_profit_harvest_armed_stale_close_enabled: bool = False
    gtos_vnext_profit_harvest_armed_stale_minutes: Optional[int] = None
    gtos_vnext_profit_harvest_armed_stale_min_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_armed_stale_close_below_r: float = 0.0
    gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise: float = 0.0
    gtos_vnext_profit_harvest_mfe_r: float = 0.0
    gtos_vnext_profit_harvest_last_progress_r: float = 0.0
    gtos_vnext_profit_harvest_triggered: bool = False
    gtos_vnext_profit_harvest_stop_activation_confirmed: bool = False
    gtos_vnext_profit_harvest_armed_stale_deferred_until_protected: bool = False
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
    expiry_candles: int | None = None
    candles_elapsed: int = 0
    trade_id: str = ""
    placed_time: str = ""
    account_balance: float = 0.0
    candidate_id: str | None = None
    decision_time_utc: str | None = None
    canonical_replay_candidate_instance_key: str | None = None
    source_bound_replay_candidate_instance_key: str | None = None
    candidate_instance_identity_status: str | None = None
    poi_id: str | None = None
    poi_state_hash_sha256: str | None = None
    causal_poi_lifecycle_required: bool | None = None
    causal_poi_lifecycle: dict | None = None
    causal_poi_lifecycle_hash_sha256: str | None = None
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
    gtos_vnext_profit_harvest_stop_activation_mfe_r: float | None = None
    gtos_vnext_profit_harvest_target_activation_fraction: float | None = None
    gtos_vnext_profit_harvest_trail_gap_r: float | None = None
    gtos_vnext_profit_harvest_protect_floor_r: float | None = None
    gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled: bool | None = None
    gtos_vnext_profit_harvest_cost_aware_margin_r: float | None = None
    gtos_vnext_profit_harvest_close_on_giveback_r: float | None = None
    gtos_vnext_profit_harvest_stale_minutes: int | None = None
    gtos_vnext_profit_harvest_stale_min_mfe_r: float | None = None
    gtos_vnext_profit_harvest_stale_close_below_r: float | None = None
    gtos_vnext_profit_harvest_armed_stale_close_enabled: bool | None = None
    gtos_vnext_profit_harvest_armed_stale_minutes: int | None = None
    gtos_vnext_profit_harvest_armed_stale_min_mfe_r: float | None = None
    gtos_vnext_profit_harvest_armed_stale_close_below_r: float | None = None
    gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise: float | None = None
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
    allocation_cash_usd: float | None = None
    min_lot_risk_usd: float | None = None
    allocation_sleeve: str | None = None
    schema_version: int = 1


def fill_cash_from_pending(intent) -> dict:
    """Cash the allocation stored on a pending limit, for the fill's trade."""

    out = {}
    cash = getattr(intent, "allocation_cash_usd", None)
    lot = getattr(intent, "min_lot_risk_usd", None)
    sleeve = getattr(intent, "allocation_sleeve", None)
    if cash not in (None, ""):
        out["allocation_cash_usd"] = cash
    if lot not in (None, ""):
        out["min_lot_risk_usd"] = lot
    if sleeve not in (None, ""):
        out["sleeve"] = sleeve
    return out


@dataclass
class NativePendingPlacement:
    """Resting native BUY_LIMIT/SELL_LIMIT. Not an open position.

    Returned by ``open_trade`` only when ``gtos_native_pending_limit`` is set.
    The live DEAL path never constructs this object.
    """
    ticket: int
    native_pending_resting: bool = True


class ExecutionEngine:
    """Manages all MT5 order operations."""

    def __init__(self, mt5: MT5Interface, config: dict, *, magic: int | None = None,
                 f5_scaler=None):
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
        if str(self._runtime_namespace or "") == "operator":
            try:
                from src.judgment.manage_choices import arm_pending_remove
                arm_pending_remove(self.mt5)
            except Exception:
                logger.warning("Challenge manage choice pending-remove hook did not arm")
            try:
                from src.judgment.execution_choices import write_armed_stamp
                write_armed_stamp()
            except Exception:
                logger.warning("Challenge execution choice stamp did not write")
        # BROKER-SIDE IDENTITY (F5, 2026-08-12). Resolved from the runtime NAMESPACE -- the same
        # key that already names the single-instance lock, the conviction ledger, the placement
        # ledger, the trade records and the governor state -- so a second decision surface on the
        # same account cannot be given a broker identity independently of everything else it is
        # isolated by. `magic_for_namespace` returns the ARMED magic for every namespace not in
        # its map, including typos, so the default path is unchanged at every existing call site.
        #
        # `_comment_prefix` moves with it: `mt5_real.get_positions` filters by magic and several
        # consumers then re-check the comment, so the two must never disagree.
        self._magic = int(magic) if magic is not None else magic_for_namespace(self._runtime_namespace)
        self._comment_prefix = comment_prefix_for_magic(self._magic)
        # F5 minimal-size experiment. `None` == off, and every F5 seam below is a no-op.
        self._f5_scaler = f5_scaler
        self._f5_last_round_up = None
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
        # T4 native pending rail. None on the live DEAL path. Populated only after
        # a successful TRADE_ACTION_PENDING send when TradeIntent.entry_price was set.
        self._native_pending_order: Optional[dict] = None

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
        # The five conditions (DEAL + ticket>0 + volume>0 + volume <= the live
        # position's volume + opposing type) now have exactly one definition,
        # in src/safety/activation_token.py, because the activation gate at the
        # order_send choke point classifies with the same test. Two copies of a
        # risk-reducing classifier that disagree is a live-risk defect waiting
        # to happen; this reads the broker exactly as it did before and
        # delegates the decision.
        if not deal_request_is_structurally_a_close(request):
            return False
        try:
            positions = self.mt5.get_positions(request.get("symbol") or self.symbol) or []
        except Exception:
            return False
        return deal_reduces_existing_position(request, positions)

    @staticmethod
    def _sl_modify_reduces_or_preserves_risk(position, new_sl: float) -> bool:
        # Delegates, for the same reason `_request_reduces_existing_position`
        # does. There WERE two implementations and they disagreed: this one read
        # `getattr(position, "sl", 0.0)` while the token layer reads dicts too,
        # so a dict-shaped position gave `current = 0.0` here -> "no stop yet" ->
        # `True`, calling a WIDENED stop risk-reducing, while the token layer
        # correctly called it widened. Two definitions of "risk-reducing" that
        # disagree in the permissive direction is exactly the live-risk defect
        # the single-definition rule exists to prevent — and the test guarding
        # that rule was a source-substring grep that never covered this half at
        # all. Latent (both adapters return PositionInfo today), and one
        # refactor to a dict-returning provider from live. See B104.
        try:
            return sltp_reduces_or_preserves_risk({"sl": new_sl}, position)
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
            packet = {
                "schema_version": "broker_order_lifecycle_capture_v4_runtime_event_v1",
                "component": "broker_order_lifecycle_capture_v4",
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "stage": stage,
                "symbol": self.symbol,
                "persist_symbol": self._persist_symbol,
                "runtime_namespace": self._runtime_namespace,
                "ticket": getattr(trade, "ticket", None),
                "trade_id": getattr(trade, "trade_id", None),
                "direction": getattr(trade, "direction", None),
                "request": dict(request or {}),
                "result": self._result_snapshot(result),
                "extra": extra or {},
                "broker_runtime_change_status": False,
                "source_boundary": "runtime_observed_broker_request_result_no_replay_inference",
            }
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
            "canonical_replay_candidate_instance_key",
            "source_bound_replay_candidate_instance_key",
            "candidate_instance_identity_status",
            "poi_id",
            "poi_state_hash_sha256",
            "causal_poi_lifecycle_required",
            "causal_poi_lifecycle",
            "causal_poi_lifecycle_hash_sha256",
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
            "gtos_vnext_pretrade_cost_model",
            "gtos_vnext_profit_harvest_mfe_capture_v4_enabled",
            "gtos_vnext_profit_harvest_min_mfe_r",
            "gtos_vnext_profit_harvest_stop_activation_mfe_r",
            "gtos_vnext_profit_harvest_target_activation_fraction",
            "gtos_vnext_profit_harvest_trail_gap_r",
            "gtos_vnext_profit_harvest_protect_floor_r",
            "gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled",
            "gtos_vnext_profit_harvest_cost_aware_margin_r",
            "gtos_vnext_profit_harvest_close_on_giveback_r",
            "gtos_vnext_profit_harvest_stale_minutes",
            "gtos_vnext_profit_harvest_stale_min_mfe_r",
            "gtos_vnext_profit_harvest_stale_close_below_r",
            "gtos_vnext_profit_harvest_armed_stale_close_enabled",
            "gtos_vnext_profit_harvest_armed_stale_minutes",
            "gtos_vnext_profit_harvest_armed_stale_min_mfe_r",
            "gtos_vnext_profit_harvest_armed_stale_close_below_r",
            "gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise",
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
            "allocation_cash_usd",
            "min_lot_risk_usd",
            "allocation_sleeve",
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

        # Staleness check 1: the age hop. An empty score leaves the intent.
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
        age_limit = self._spine_score(
            "pending_intent_max_age_hours",
            "The score you return is the maximum age in hours for this pending intent. "
            "An empty score leaves the intent in place. Do not send.",
            {"trade_id": getattr(intent, "trade_id", None), "placed_time": intent.placed_time},
            placed=placed_dt,
        )
        age_hours = (now - placed_dt).total_seconds() / 3600.0
        if age_limit is not None and (now - placed_dt) >= timedelta(hours=float(age_limit)):
            logger.info(
                "Discarding stale pending_intent (age=%.1fh >= %sh): %s "
                "%s limit=%.5f sl=%.5f placed=%s",
                age_hours, age_limit,
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

        state = {"policy": "be_after_trigger", "symbol": getattr(self, "symbol", None)}
        trigger_r = self._spine_score(
            "be_trigger_r",
            "The score you return is the breakeven trigger multiple. "
            "An empty score leaves it unset. Do not send.",
            state,
        )
        final_target_r = self._spine_score(
            "be_final_target_r",
            "The score you return is the breakeven final target multiple. "
            "An empty score leaves it unset. Do not send.",
            state,
        )
        out = {}
        if trigger_r is not None:
            out["trigger_r"] = trigger_r
        if final_target_r is not None:
            out["final_target_r"] = final_target_r
        if time_stop_bars is not None:
            out["time_stop_bars"] = time_stop_bars
        return out

    def _configured_vnext_partial_be_runner_params(self, trade=None) -> dict:
        state = {"policy": "partial_be_runner", "symbol": getattr(self, "symbol", None)}
        if trade is not None:
            state["current_volume"] = getattr(trade, "current_volume", None)
            state["initial_volume"] = getattr(trade, "initial_volume", None)
        out = {}
        for role, text in (
            ("trigger_r", "The score you return is the partial trigger multiple. An empty score leaves it unset. Do not send."),
            ("final_target_r", "The score you return is the partial final target multiple. An empty score leaves it unset. Do not send."),
            ("partial_close_ratio", "The score you return is the partial close fraction. An empty score leaves it unset. Do not send."),
            ("time_stop_bars", "The score you return is the partial time-stop bar count. An empty score leaves it unset. Do not send."),
        ):
            number = self._spine_score(role, text, state, trade=trade)
            if number is not None:
                out[role] = number
        return out

    def _configured_vnext_trailing_runner_params(self, trade=None) -> dict:
        state = {"policy": "trailing_runner", "symbol": getattr(self, "symbol", None)}
        out = {}
        for role, text in (
            ("trigger_r", "The score you return is the trail trigger multiple. An empty score leaves it unset. Do not send."),
            ("final_target_r", "The score you return is the trail final target multiple. An empty score leaves it unset. Do not send."),
            ("trail_gap_r", "The score you return is the trail gap. An empty score leaves it unset. Do not send."),
            ("time_stop_bars", "The score you return is the trail time-stop bar count. An empty score leaves it unset. Do not send."),
        ):
            number = self._spine_score(role, text, state, trade=trade)
            if number is not None:
                out[role] = number
        return out

    def _configured_vnext_momentum_exhaustion_params(self, trade=None) -> dict:
        state = {"policy": "momentum_exhaustion", "symbol": getattr(self, "symbol", None)}
        out = {}
        for role, text in (
            ("trigger_r", "The score you return is the momentum trigger multiple. An empty score leaves it unset. Do not send."),
            ("final_target_r", "The score you return is the momentum final target multiple. An empty score leaves it unset. Do not send."),
            ("pullback_r", "The score you return is the momentum pullback. An empty score leaves it unset. Do not send."),
            ("time_stop_bars", "The score you return is the momentum time-stop bar count. An empty score leaves it unset. Do not send."),
        ):
            number = self._spine_score(role, text, state, trade=trade)
            if number is not None:
                out[role] = number
        return out

    def _configured_vnext_time_stop_params(self) -> dict:
        state = {"policy": "time_stop", "symbol": getattr(self, "symbol", None)}
        out = {}
        bars = self._spine_score(
            "time_stop_bars",
            "The score you return is the time-stop bar count. An empty score leaves it unset. Do not send.",
            state,
        )
        target_r = self._spine_score(
            "time_stop_target_r",
            "The score you return is the time-stop target multiple. An empty score leaves it unset. Do not send.",
            state,
        )
        if bars is not None:
            out["time_stop_bars"] = bars
        if target_r is not None:
            out["final_target_r"] = target_r
        return out

    def _configured_vnext_profit_harvest_mfe_capture_v4_params(self) -> dict:
        cfg = self.config.get("gtos_vnext_runtime", {}) or {}

        def _bool_cfg(key: str, default: bool) -> bool:
            raw = cfg.get(key, default)
            if isinstance(raw, str):
                return raw.strip().lower() in {"1", "true", "yes", "on"}
            return bool(raw)

        def _float_cfg(key: str):
            return self._spine_score(
                key,
                "The score you return is this profit-harvest quantity. "
                "An empty score leaves it unset. Do not send.",
                {"symbol": getattr(self, "symbol", None), "field": key},
            )

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
            ),
            "stop_activation_mfe_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_stop_activation_mfe_r",
            ),
            "target_activation_fraction": _float_cfg(
                "profit_harvest_mfe_capture_v4_target_activation_fraction",
            ),
            "trail_gap_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_trail_gap_r",
            ),
            "protect_floor_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_protect_floor_r",
            ),
            "cost_aware_protect_floor_enabled": _bool_cfg(
                "profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled",
                False,
            ),
            "cost_aware_margin_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_cost_aware_margin_r",
            ),
            "close_on_giveback_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_close_on_giveback_r",
            ),
            "stale_minutes": _optional_int_cfg(
                "profit_harvest_mfe_capture_v4_stale_minutes",
            ),
            "stale_min_mfe_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_stale_min_mfe_r",
            ),
            "stale_close_below_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_stale_close_below_r",
            ),
            "armed_stale_close_enabled": _bool_cfg(
                "profit_harvest_mfe_capture_v4_armed_stale_close_enabled",
                False,
            ),
            "armed_stale_minutes": _optional_int_cfg(
                "profit_harvest_mfe_capture_v4_armed_stale_minutes",
            ),
            "armed_stale_min_mfe_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_armed_stale_min_mfe_r",
            ),
            "armed_stale_close_below_r": _float_cfg(
                "profit_harvest_mfe_capture_v4_armed_stale_close_below_r",
            ),
            "min_hold_minutes_before_stop_raise": _float_cfg(
                "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise",
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
            trigger_r = self._safe_float(configured.get("trigger_r"))
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        no_broker_tp = self._vnext_no_broker_take_profit(trade_params)
        if final_target_r is None and not no_broker_tp:
            final_target_r = self._safe_float(configured.get("final_target_r"))
        elif final_target_r is None:
            final_target_r = 0.0
        close_ratio = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_partial_close_ratio")
        )
        if close_ratio is None:
            close_ratio = self._safe_float(configured.get("partial_close_ratio"))
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
        if (
            trigger_r is None or trigger_r <= 0
            or final_target_r is None or final_target_r <= 0
            or close_ratio is None or not 0 < close_ratio < 1
        ):
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
            trigger_r = self._safe_float(configured.get("trigger_r"))
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        no_broker_tp = self._vnext_no_broker_take_profit(trade_params)
        if final_target_r is None and not no_broker_tp:
            final_target_r = self._safe_float(configured.get("final_target_r"))
        elif final_target_r is None:
            final_target_r = 0.0
        trail_gap_r = self._safe_float(trade_params.get("gtos_vnext_dynamic_trail_gap_r"))
        if trail_gap_r is None:
            trail_gap_r = self._safe_float(configured.get("trail_gap_r"))
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
        if (
            trigger_r is None or trigger_r <= 0
            or (not no_broker_tp and (final_target_r is None or final_target_r <= 0))
            or trail_gap_r is None or trail_gap_r <= 0
        ):
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
            trigger_r = self._safe_float(configured.get("trigger_r"))
        final_target_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        )
        if final_target_r is None:
            final_target_r = self._safe_float(configured.get("final_target_r"))
        pullback_r = self._safe_float(
            trade_params.get("gtos_vnext_dynamic_momentum_pullback_r")
        )
        if pullback_r is None:
            pullback_r = self._safe_float(configured.get("pullback_r"))
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
        if (
            trigger_r is None or trigger_r <= 0
            or final_target_r is None or final_target_r <= 0
            or pullback_r is None or pullback_r <= 0
        ):
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
            raw_time_stop = configured.get("time_stop_bars")
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
            target_r = self._safe_float(configured.get("final_target_r"))
        if target_r is None and not no_broker_tp:
            logger.error("GTOS vNext time_stop target unset")
            return None
        if target_r is None:
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
                raw = configured.get(configured_key)
            return self._safe_float(raw)

        min_mfe_r = _float_param(
            (
                "gtos_vnext_profit_harvest_min_mfe_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_min_mfe_r",
            ),
            "min_mfe_r",
        )
        stop_activation_mfe_r = _float_param(
            (
                "gtos_vnext_profit_harvest_stop_activation_mfe_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_stop_activation_mfe_r",
            ),
            "stop_activation_mfe_r",
        )
        target_activation_fraction = _float_param(
            (
                "gtos_vnext_profit_harvest_target_activation_fraction",
                "gtos_vnext_profit_harvest_mfe_capture_v4_target_activation_fraction",
            ),
            "target_activation_fraction",
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
        cost_aware_protect_floor_enabled = self._bool_param_enabled(
            _raw_param(
                (
                    "gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled",
                    "gtos_vnext_profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled",
                )
            )
            if _raw_param(
                (
                    "gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled",
                    "gtos_vnext_profit_harvest_mfe_capture_v4_cost_aware_protect_floor_enabled",
                )
            )
            not in (None, "")
            else configured["cost_aware_protect_floor_enabled"]
        )
        cost_aware_margin_r = _float_param(
            (
                "gtos_vnext_profit_harvest_cost_aware_margin_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_cost_aware_margin_r",
            ),
            "cost_aware_margin_r",
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
        armed_stale_close_enabled = self._bool_param_enabled(
            _raw_param(
                (
                    "gtos_vnext_profit_harvest_armed_stale_close_enabled",
                    "gtos_vnext_profit_harvest_mfe_capture_v4_armed_stale_close_enabled",
                )
            )
            if _raw_param(
                (
                    "gtos_vnext_profit_harvest_armed_stale_close_enabled",
                    "gtos_vnext_profit_harvest_mfe_capture_v4_armed_stale_close_enabled",
                )
            )
            not in (None, "")
            else configured["armed_stale_close_enabled"]
        )
        armed_stale_min_mfe_r = _float_param(
            (
                "gtos_vnext_profit_harvest_armed_stale_min_mfe_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_armed_stale_min_mfe_r",
            ),
            "armed_stale_min_mfe_r",
        )
        armed_stale_close_below_r = _float_param(
            (
                "gtos_vnext_profit_harvest_armed_stale_close_below_r",
                "gtos_vnext_profit_harvest_mfe_capture_v4_armed_stale_close_below_r",
            ),
            "armed_stale_close_below_r",
        )
        min_hold_minutes_before_stop_raise = _float_param(
            (
                "gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise",
                "gtos_vnext_profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise",
            ),
            "min_hold_minutes_before_stop_raise",
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
        raw_armed_stale_minutes = _raw_param(
            (
                "gtos_vnext_profit_harvest_armed_stale_minutes",
                "gtos_vnext_profit_harvest_mfe_capture_v4_armed_stale_minutes",
            )
        )
        if raw_armed_stale_minutes in (None, ""):
            raw_armed_stale_minutes = configured.get("armed_stale_minutes")
        try:
            armed_stale_minutes = (
                None
                if raw_armed_stale_minutes in (None, "")
                else int(raw_armed_stale_minutes)
            )
            if armed_stale_minutes is not None and armed_stale_minutes < 0:
                raise ValueError("armed_stale_minutes must be non-negative")
        except (TypeError, ValueError):
            logger.error(
                "GTOS vNext profit harvest invalid armed stale minutes: %r",
                raw_armed_stale_minutes,
            )
            return None

        if (
            min_mfe_r is None
            or min_mfe_r <= 0
            or stop_activation_mfe_r is None
            or stop_activation_mfe_r <= 0
            or target_activation_fraction is None
            or target_activation_fraction < 0
            or target_activation_fraction > 1
            or trail_gap_r is None
            or trail_gap_r <= 0
            or protect_floor_r is None
            or protect_floor_r < 0
            or cost_aware_margin_r is None
            or cost_aware_margin_r < 0
            or close_on_giveback_r is None
            or close_on_giveback_r <= 0
            or stale_min_mfe_r is None
            or stale_min_mfe_r <= 0
            or stale_close_below_r is None
            or armed_stale_min_mfe_r is None
            or armed_stale_min_mfe_r <= 0
            or armed_stale_close_below_r is None
            or min_hold_minutes_before_stop_raise is None
            or min_hold_minutes_before_stop_raise < 0
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
            "stop_activation_mfe_r": max(min_mfe_r, stop_activation_mfe_r),
            "target_activation_fraction": target_activation_fraction,
            "trail_gap_r": trail_gap_r,
            "protect_floor_r": protect_floor_r,
            "cost_aware_protect_floor_enabled": cost_aware_protect_floor_enabled,
            "cost_aware_margin_r": cost_aware_margin_r,
            "close_on_giveback_r": close_on_giveback_r,
            "stale_minutes": stale_minutes,
            "stale_min_mfe_r": stale_min_mfe_r,
            "stale_close_below_r": stale_close_below_r,
            "armed_stale_close_enabled": armed_stale_close_enabled,
            "armed_stale_minutes": armed_stale_minutes,
            "armed_stale_min_mfe_r": armed_stale_min_mfe_r,
            "armed_stale_close_below_r": armed_stale_close_below_r,
            "min_hold_minutes_before_stop_raise": min_hold_minutes_before_stop_raise,
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
            # Bind forecast swap to this candidate's already-recorded entry instant.  Omitting
            # it falls back to fractional holding days, which cannot distinguish an eight-hour
            # horizon that crosses broker rollover from one that does not.  Never substitute a
            # fresh wall-clock read here: the packet identity already owns this timestamp.
            asof_utc=(
                trade_params.get("asof_utc")
                or trade_params.get("decision_time_utc")
            ),
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

    @staticmethod
    def _int_or_none(value) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

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
            "commission": None,
            "swap": None,
            "deal_ticket": getattr(result, "deal", None),
            "broker_fill_time_utc": None,
            "broker_entry_price": None,
        }
        history_lookup = getattr(self.mt5, "get_history_deals", None)
        if not callable(history_lookup):
            return payload

        order_id = self._int_or_none(getattr(result, "order", None))
        deal_id = self._int_or_none(getattr(result, "deal", None))
        match = None
        match_reason = None

        def _find_entry_deal(deals: list[dict]) -> tuple[Optional[dict], Optional[str]]:
            for deal in deals:
                if not isinstance(deal, dict):
                    continue
                ticket = self._int_or_none(deal.get("ticket"))
                order = self._int_or_none(deal.get("order"))
                position_id = self._int_or_none(deal.get("position_id"))
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
        lookup_attempts = 5
        payload["account_history_lookup_attempt_count"] = lookup_attempts
        for attempt in range(lookup_attempts):
            try:
                deals = history_lookup(window_start, window_end, self.symbol) or []
            except Exception as exc:  # noqa: BLE001 - reconciliation must not block filled trades
                payload["account_history_lookup_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                payload["account_history_lookup_error"] = str(exc)
                payload["account_history_lookup_attempt_count"] = attempt + 1
                return payload
            match, match_reason = _find_entry_deal(deals)
            if match is not None:
                payload["account_history_lookup_attempt_count"] = attempt + 1
                break
            if attempt < lookup_attempts - 1:
                time.sleep(0.25)

        if match is None:
            payload["account_history_lookup_status"] = "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
            payload["account_history_lookup_match_keys"] = {
                "order": order_id,
                "deal": deal_id,
            }
            return payload

        payload.update(
            {
                "account_history_lookup_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                "account_history_lookup_match_keys": {
                    "matched_by": match_reason,
                    "order": self._int_or_none(match.get("order")),
                    "ticket": self._int_or_none(match.get("ticket")),
                    "position_id": self._int_or_none(match.get("position_id")),
                    "price": self._safe_float(match.get("price")),
                },
                "commission": match.get("commission"),
                "swap": match.get("swap"),
                "deal_ticket": match.get("ticket") or getattr(result, "deal", None),
                "broker_fill_time_utc": self._history_time_to_iso(match.get("time")),
                "broker_entry_price": match.get("price"),
            }
        )
        return payload

    def _lookup_close_deal_accounting(
        self,
        *,
        trade: TradeState,
        result,
        close_ticket: Optional[int],
    ) -> dict:
        now_utc = datetime.now(timezone.utc)
        window_start = now_utc - timedelta(minutes=5)
        window_end = now_utc + timedelta(minutes=5)
        ticket = self._int_or_none(close_ticket if close_ticket is not None else trade.ticket)
        order_id = self._int_or_none(getattr(result, "order", None))
        deal_id = self._int_or_none(getattr(result, "deal", None))
        payload = {
            "account_history_lookup_attempted": False,
            "account_history_lookup_status": "ACCOUNT_HISTORY_LOOKUP_UNAVAILABLE",
            "account_history_lookup_window_start_utc": window_start.isoformat(),
            "account_history_lookup_window_end_utc": window_end.isoformat(),
            "account_history_lookup_error": None,
            "account_history_lookup_match_keys": None,
            "commission": None,
            "swap": None,
            "broker_profit": None,
            "deal_ticket": deal_id,
            "broker_fill_time_utc": None,
            "broker_close_price": None,
        }
        history_lookup = getattr(self.mt5, "get_history_deals", None)
        if not callable(history_lookup):
            return payload

        def _find_close_deal(deals: list[dict]) -> tuple[Optional[dict], Optional[str]]:
            for deal in deals:
                if not isinstance(deal, dict):
                    continue
                deal_ticket = self._int_or_none(deal.get("ticket"))
                deal_order = self._int_or_none(deal.get("order"))
                position_id = self._int_or_none(deal.get("position_id"))
                entry = self._int_or_none(deal.get("entry"))
                if entry != 1:
                    continue
                if deal_id is not None and deal_ticket == deal_id:
                    return deal, "deal_ticket"
                if order_id is not None and deal_order == order_id:
                    return deal, "order_ticket"
                if ticket is not None and position_id == ticket:
                    return deal, "position_id_matches_trade_ticket"
            return None, None

        payload["account_history_lookup_attempted"] = True
        lookup_attempts = 3
        payload["account_history_lookup_attempt_count"] = lookup_attempts
        match = None
        match_reason = None
        for attempt in range(lookup_attempts):
            try:
                deals = history_lookup(window_start, window_end, self.symbol) or []
            except Exception as exc:  # noqa: BLE001 - close accounting must not block lifecycle handling
                payload["account_history_lookup_status"] = "ACCOUNT_HISTORY_LOOKUP_FAILED"
                payload["account_history_lookup_error"] = str(exc)
                payload["account_history_lookup_attempt_count"] = attempt + 1
                return payload
            match, match_reason = _find_close_deal(deals)
            if match is not None:
                payload["account_history_lookup_attempt_count"] = attempt + 1
                break
            if attempt < lookup_attempts - 1:
                time.sleep(0.25)

        if match is None:
            payload["account_history_lookup_status"] = "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
            payload["account_history_lookup_match_keys"] = {
                "order": order_id,
                "deal": deal_id,
                "position_ticket": ticket,
            }
            return payload

        payload.update(
            {
                "account_history_lookup_status": "RECONCILED_FROM_ACCOUNT_HISTORY",
                "account_history_lookup_match_keys": {
                    "matched_by": match_reason,
                    "order": self._int_or_none(match.get("order")),
                    "ticket": self._int_or_none(match.get("ticket")),
                    "position_id": self._int_or_none(match.get("position_id")),
                    "price": self._safe_float(match.get("price")),
                },
                "commission": match.get("commission"),
                "swap": match.get("swap"),
                "broker_profit": match.get("profit"),
                "deal_ticket": match.get("ticket") or deal_id,
                "broker_fill_time_utc": self._history_time_to_iso(match.get("time")),
                "broker_close_price": match.get("price"),
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
            # — and `_close_request_execution_geometry` then refuses the close at its
            # equality gate, because it demands the normalized volume equal the
            # requested one to 1e-9.
            #
            # That is a STRAND, not a rounding nit. Nine close producers route through
            # that check, the live book always takes the verified-geometry branch
            # (`ultimate_book/execution_packets.py:318-319` sets the selected-cell risk
            # fields that `_trade_requires_verified_broker_geometry` keys on), and each
            # producer returns before `safe_place_order` — so nothing reaches the
            # activation layer and no retry can ever succeed, because the next tick
            # recomputes the identical volume. Measured 2026-07-29 (B333): 33 of 300
            # two-decimal lot sizes are affected at (0.01, 0.01), 100 of 291 at a
            # 0.10 minimum, and **44 of 327 real broker close deals** in
            # `vps-export-20260725` carried an affected volume — 8 of 78 of the
            # engine-initiated ones. All three reproduced independently at wave-4
            # integration (B354).
            #
            # It also happened LIVE, and nothing cited it until wave-4 integration
            # (B368): `vps-export-20260725/extracted/07_knowledge_base/logs/
            # agent_NAS100_live.log` records a +1R partial-take refused **32 times over
            # 38 minutes** on 2026-06-02 — "close volume 0.21000000 is not broker-step
            # aligned (normalized 0.20000000)" once a minute — after which ticket
            # 242403337 was closed by the BROKER, not by the engine. Use `grep -a`: the
            # log is non-UTF-8, so a plain grep suppresses it as binary and finds
            # nothing, which is the likeliest reason it went uncited for two months.
            #
            # NO LINE NUMBERS ON PURPOSE. The nine call sites and the equality gate were
            # cited here by line, and this 30-line comment shifted every one of them: the
            # cited `:8215` came to point at `result = self.safe_place_order(request)`,
            # the exact call this comment says is never reached. Grep for
            # `_close_request_execution_geometry` instead; it is exact and cannot rot.
            #
            # The epsilon is a step-count tolerance, not a volume tolerance: it can only
            # promote a quotient already within 1e-9 of an integer, i.e. a lot size within
            # `1e-9 * volume_step` of the next step (1e-11 at the 0.01 step both funded
            # accounts use), so a genuinely mis-aligned volume still rounds DOWN.
            #
            # TWO STATED INVARIANTS ARE FALSE AS WRITTEN, found by an adversarial pass at
            # wave-4 integration (B369). Both are unreachable on either funded account —
            # all 42 traded symbol specs are (min 0.01, step 0.01), max step-count 99,999,
            # and an exhaustive sweep of all 99,999 grid points to volume_max=1000 is
            # clean — but the comment must not claim more than the code does:
            #   (1) "can never exceed the request" is false. The clamp below falls back to
            #       `round(lots, 8)`, which rounds to NEAREST; 145 inputs return up to
            #       ~5e-9 lots ABOVE the request. Economically nil, but it is an overshoot,
            #       and `test_normalization_never_rounds_up`'s 1e-12 tolerance cannot see it.
            #   (2) "sub-minimum is still refused" is false when volume_max < volume_min
            #       (nothing validates that ordering): lots=5.0 at (0.10, 0.01, 0.05)
            #       returns 0.05 — below the minimum AND off-grid — where the pre-fix code
            #       returned 0.10. That one is a regression the clamp introduced.
            # The repair for both is the same and is deliberately NOT made here, because
            # it is an arithmetic change to the money path and this was an integration
            # session: the clamp should step DOWN to the largest grid point <= lots and
            # return None if that is below volume_min, never `round(lots, 8)`.
            #
            # Both properties the fix DOES hold are pinned by
            # `tests/test_execution_volume_normalization.py`.
            steps = math.floor((lots - volume_min) / volume_step + _VOLUME_STEP_EPSILON)
            normalized = volume_min + max(0, steps) * volume_step
            normalized = round(normalized, 8)
            # Never hand back more than was asked for, whatever the arithmetic did.
            return normalized if normalized <= lots else round(lots, 8)

        lots = math.floor(lots * 100) / 100
        if self._challenge_book():
            if lots <= 0:
                return None
            return lots
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
            # Fable M2 leak 6: query by position ticket. Time-window+symbol
            # misses already-closed tickets and leaves active_trade holding
            # the symbol (1,806 failed closes 25-28 Aug).
            try:
                pos_deals = history_deals_get(position=int(trade.ticket))
            except TypeError:
                pos_deals = None
            except Exception:
                logger.exception(
                    "Unable to confirm MT5 close deal for vNext ticket %s via position",
                    trade.ticket,
                )
                pos_deals = None
            if pos_deals is not None:
                any_history_source_available = True
                if _has_close_deal(pos_deals):
                    return "CLOSE_DEAL_FOUND"
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
            getattr(trade, "gtos_vnext_book_native_exit_management", False)
            or payload.get("gtos_vnext_book_native_exit_management")
        )
        selected_policy = str(
            payload["gtos_vnext_dynamic_policy_selected"] or ""
        ).strip().lower()
        trade.gtos_vnext_dynamic_be_after_trigger_active = selected_policy == "be_after_trigger"
        # `_vnext_time_stop_params` returns no `trigger_r` -- a time stop has no break-even trigger
        # -- so a bare `params["trigger_r"]` raised KeyError for EVERY `policy="time_stop"` record.
        # That is four of the five ARMED sleeves (`crypto`, `sub_xvol_pullback`, `fx_jpy`,
        # `sub_mid_dn_revert`; only `energy_agri` is `partial_be_runner` and carries the key), and
        # the live caller does not catch it: `book_owner.py:2729` calls `hyd(rec)` with no
        # try/except when `_live_broker_authority()` is true, which it is on both accounts. So
        # adopting ANY open time-stop position raised out of the adopt path.
        # The fallback restores exactly what the packet builder wrote: `native_policy_instrumentation`
        # (`execution_packets.py:172`) already defaults `trigger_r` to `final_target_r` for these
        # policies, so this reads the intended value rather than inventing one. Found by an
        # adversarial pass on Session AS's activation dossier (B1535).
        trigger_r = params.get("trigger_r")
        if trigger_r is None:
            trigger_r = payload.get("gtos_vnext_dynamic_be_trigger_r")
        if trigger_r in (None, ""):
            trigger_r = params.get("final_target_r") or 0.0
        trade.gtos_vnext_dynamic_be_trigger_r = float(trigger_r)
        trade.gtos_vnext_dynamic_final_target_r = float(params["final_target_r"])
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
        # Book-native / F5 live authority: keep broker TP. 1.5R is economic BE, never TP1.
        if self._software_tp1_forbidden(trade):
            if no_broker_tp and selected_policy == "time_stop":
                trade.take_profit_1 = 0.0
        else:
            trade.take_profit_1 = (
                0.0
                if no_broker_tp and selected_policy == "time_stop"
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

    def _cfg_fact(self, *names):
        cfg = self.config if isinstance(getattr(self, "config", None), dict) else {}
        runtime = cfg.get("gtos_vnext_runtime")
        runtime = runtime if isinstance(runtime, dict) else {}
        rules = cfg.get("ftmo_rules")
        rules = rules if isinstance(rules, dict) else {}
        for blob in (runtime, cfg, rules):
            for name in names:
                if blob.get(name) not in (None, ""):
                    return blob.get(name)
        return None

    def _account_attr(self, info, name):
        if info is None:
            return None
        if isinstance(info, dict):
            return info.get(name)
        return getattr(info, name, None)

    def _positive_fact(self, value):
        if isinstance(value, bool) or value is None:
            return None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number != number or number in (float("inf"), float("-inf")) or number <= 0:
            return None
        return number

    def _currency_digits(self):
        """Digits of this account's currency, from account_info. Missing stays missing."""

        raw = self._raw_mt5()
        info_fn = getattr(raw, "account_info", None) if raw is not None else None
        if not callable(info_fn):
            return None
        try:
            info = info_fn()
        except Exception:
            return None
        if info is None:
            return None
        value = self._account_attr(info, "currency_digits")
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
        if number != number or number in (float("inf"), float("-inf")) or number < 0 or number != int(number):
            return None
        return int(number)

    def _raw_mt5(self):
        """The raw MetaTrader5 module behind the adapter (``self.mt5._mt5``)."""
        adapter = getattr(self, "mt5", None)
        raw = getattr(adapter, "_mt5", None)
        return raw if raw is not None else adapter

    def _open_stop_risk_usd(self, positions, orders) -> "tuple[float, float] | None":
        """USD lost if every open position and pending order hits its stop.

        Every position and every pending order counts, whatever its magic.
        Pending volume is ``volume_current``. A position or a pending order
        with no stop has no bounded loss, so the total stays unset. A stop
        already in profit adds nothing. The pair is account total, then the
        pending-only part of that total.
        """
        raw = self._raw_mt5()
        calc = getattr(raw, "order_calc_profit", None)
        if not callable(calc):
            return None
        buy = getattr(raw, "ORDER_TYPE_BUY", 0)
        sell = getattr(raw, "ORDER_TYPE_SELL", 1)
        buy_orders = []
        sell_orders = []
        for name in (
            "ORDER_TYPE_BUY",
            "ORDER_TYPE_BUY_LIMIT",
            "ORDER_TYPE_BUY_STOP",
            "ORDER_TYPE_BUY_STOP_LIMIT",
        ):
            value = getattr(raw, name, None)
            if isinstance(value, int) and not isinstance(value, bool):
                buy_orders.append(value)
        for name in (
            "ORDER_TYPE_SELL",
            "ORDER_TYPE_SELL_LIMIT",
            "ORDER_TYPE_SELL_STOP",
            "ORDER_TYPE_SELL_STOP_LIMIT",
        ):
            value = getattr(raw, name, None)
            if isinstance(value, int) and not isinstance(value, bool):
                sell_orders.append(value)

        def piece(order_type, symbol, volume, price, stop):
            try:
                pnl = float(calc(order_type, symbol, volume, price, stop))
            except Exception:
                return None
            if pnl != pnl or pnl in (float("inf"), float("-inf")):
                return None
            if pnl < 0:
                return -pnl
            return 0.0

        total = 0.0
        for pos in positions:
            symbol = self._account_attr(pos, "symbol")
            volume_n = self._positive_fact(self._account_attr(pos, "volume"))
            price_n = self._positive_fact(self._account_attr(pos, "price_open"))
            stop_n = self._positive_fact(self._account_attr(pos, "sl"))
            side = self._account_attr(pos, "type")
            if not symbol or volume_n is None or price_n is None or stop_n is None:
                return None
            if side in (0, buy, "BUY", "LONG", "buy"):
                order_type = buy
            elif side in (1, sell, "SELL", "SHORT", "sell"):
                order_type = sell
            else:
                return None
            loss = piece(order_type, symbol, volume_n, price_n, stop_n)
            if loss is None:
                return None
            total += loss
        pending = 0.0
        for order in orders:
            symbol = self._account_attr(order, "symbol")
            volume_n = self._positive_fact(self._account_attr(order, "volume_current"))
            price_n = self._positive_fact(self._account_attr(order, "price_open"))
            stop_n = self._positive_fact(self._account_attr(order, "sl"))
            side = self._account_attr(order, "type")
            if side in buy_orders:
                order_type = buy
            elif side in sell_orders:
                order_type = sell
            else:
                return None
            if side in (
                getattr(raw, "ORDER_TYPE_BUY_STOP_LIMIT", None),
                getattr(raw, "ORDER_TYPE_SELL_STOP_LIMIT", None),
            ):
                price_n = self._positive_fact(self._account_attr(order, "price_stoplimit"))
            if not symbol or volume_n is None or price_n is None or stop_n is None:
                return None
            loss = piece(order_type, symbol, volume_n, price_n, stop_n)
            if loss is None:
                return None
            pending += loss
            total += loss
        return total, pending

    def _size_room_facts(self, account_balance: float) -> dict:
        """Floor, daily, and open-risk facts from this process's account.

        Reads go through the adapter's own methods and the raw module behind
        it, so they take the terminal lock like every other call. Pending
        orders are part of the open risk. A failed positions or orders read
        leaves that risk unset.
        """
        adapter = getattr(self, "mt5", None)
        raw = self._raw_mt5()
        equity = None
        balance = None
        if adapter is not None:
            for name, target in (("get_account_equity", "equity"), ("get_account_balance", "balance")):
                fn = getattr(adapter, name, None)
                if not callable(fn):
                    continue
                try:
                    value = self._positive_fact(fn())
                except Exception:
                    value = None
                if target == "equity":
                    equity = value
                else:
                    balance = value
        positions = None
        orders = None
        open_risk = None
        pending_risk = None
        listed = None
        listed_orders = None
        get_pos = getattr(raw, "positions_get", None)
        get_orders = getattr(raw, "orders_get", None)
        if callable(get_pos):
            try:
                found = get_pos()
            except Exception:
                found = None
            if found is not None:
                try:
                    listed = list(found)
                except TypeError:
                    listed = None
        if callable(get_orders):
            try:
                found_orders = get_orders()
            except Exception:
                found_orders = None
            if found_orders is not None:
                try:
                    listed_orders = list(found_orders)
                except TypeError:
                    listed_orders = None
        if listed is not None and listed_orders is not None:
            positions = len(listed)
        if listed_orders is not None:
            orders = len(listed_orders)
        if listed is not None and listed_orders is not None:
            if not listed and not listed_orders:
                open_risk = 0.0
                pending_risk = 0.0
            else:
                counted = self._open_stop_risk_usd(listed, listed_orders)
                if counted is not None:
                    open_risk, pending_risk = counted
        day: dict = {}
        if self._challenge_book():
            try:
                from src.judgment.equity_frame import read_chair_day_start

                offset = None
                offset_fn = getattr(adapter, "get_broker_offset_seconds", None)
                if callable(offset_fn):
                    try:
                        seconds = offset_fn()
                    except Exception:
                        seconds = None
                    if isinstance(seconds, (int, float)) and not isinstance(seconds, bool):
                        offset = float(seconds) / 3600.0
                book_login = None
                login_fn = getattr(adapter, "get_account_login", None)
                if callable(login_fn):
                    try:
                        book_login = login_fn()
                    except Exception:
                        book_login = None
                got = read_chair_day_start(
                    mt5=adapter,
                    rule_name=self._cfg_fact(
                        "prop_safe_selector_daily_reset_timezone",
                        "governor_daily_reset_rule",
                    ),
                    server_offset_hours=offset,
                    login=book_login,
                    namespace=getattr(self, "_runtime_namespace", None),
                )
                if isinstance(got, dict):
                    day = got
            except Exception:
                day = {}
        facts = {
            "equity": equity,
            "balance": balance,
            "positions_total": positions,
            "initial_balance": self._cfg_fact(
                "prop_safe_selector_initial_balance",
                "account_balance_initial_inferred_usd",
            ),
            "overall_loss_pct": self._cfg_fact(
                "prop_safe_selector_external_overall_max_loss_pct",
                "maximum_loss_pct",
            ),
            "daily_percent_external": self._cfg_fact(
                "prop_safe_selector_external_daily_loss_limit_pct",
                "maximum_daily_loss_pct",
            ),
            "day_start_balance": day.get("day_start_balance"),
            "day_start_equity": day.get("day_start_equity"),
        }
        declared = self._cfg_fact("account_rules")
        if declared not in (None, ""):
            facts["account_rules"] = str(declared)
        if orders is not None:
            facts["pending_orders_total"] = orders
        if pending_risk is not None:
            facts["pending_stop_risk_usd"] = pending_risk
        if open_risk is not None:
            facts["open_risk_usd"] = open_risk
        digits = self._currency_digits()
        if digits is not None:
            facts["currency_digits"] = digits
        return facts

    def _stamp_size_room_facts(self, trade_params: dict, account_balance: float) -> None:
        if not isinstance(trade_params, dict):
            return
        for key, value in self._size_room_facts(account_balance).items():
            if key not in trade_params or trade_params.get(key) in (None, ""):
                trade_params[key] = value

    def _challenge_keeps_return(self, reason: str, facts: dict | None = None) -> bool:
        """Other books keep the return. Challenge asks before it returns.

        continue is the only release. block returns. An empty answer does
        not send and is recorded as no_decision, not as the old reason.
        """
        if not self._challenge_book():
            return True
        choice = self._exec_choice("reject", reason=reason, facts=facts or {})
        if choice == "continue":
            return False
        if choice == "block":
            self._last_open_trade_block_reason = "exec_reject:block"
            return True
        self._last_open_trade_block_reason = "exec_reject:" + (choice or "no_decision")
        return True

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
        # The unified live-flow packet reads this observation after ``open_trade`` returns.  Clear it
        # before any fail-closed gate can return so an early refusal can never inherit the preceding
        # candidate's broker request/result and present it as its own.
        self._last_order_send_diagnostic = None
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
            if self._stop_or_mark("runtime_halt_blocked"):
                        return None

        if self._challenge_book():
            try:
                _entry_ready = float(trade_params.get("entry_price"))
                _entry_ready_ok = math.isfinite(_entry_ready) and _entry_ready > 0
            except (TypeError, ValueError):
                _entry_ready_ok = False
            if not _entry_ready_ok:
                self._last_open_trade_block_reason = "exec_entry:no_decision"
                return None
            if not trade_params.get("gtos_native_pending_limit"):
                _side = str(trade_params.get("direction") or "").upper()
                trade_params["gtos_native_pending_limit"] = True
                trade_params["gtos_native_pending_order_type"] = (
                    "BUY_LIMIT" if _side == "LONG" else "SELL_LIMIT"
                )

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
            if self._stop_or_mark(f"vnext_policy:{vnext_policy_error}"):
                        return None

        tick = self.mt5.get_tick(self.symbol)
        if tick is None:
            logger.error("Cannot get tick data -- aborting trade")
            if not self._stop_or_mark("no_tick_data"):
                    self._last_open_trade_block_reason = "exec_gate:" + str("no_tick_data")[:120]
            return None

        if trade_params.get("gtos_native_pending_limit"):
            if self._native_pending_order is not None:
                if self._stop_or_mark("native_pending_already_resting"):
                            return None
            try:
                entry_price = float(trade_params["entry_price"])
            except (TypeError, ValueError, KeyError):
                if not self._stop_or_mark("native_limit_price_invalid"):
                        self._last_open_trade_block_reason = "exec_gate:" + str("native_limit_price_invalid")[:120]
                return None
            if not math.isfinite(entry_price) or entry_price <= 0:
                if not self._stop_or_mark("native_limit_price_invalid"):
                        self._last_open_trade_block_reason = "exec_gate:" + str("native_limit_price_invalid")[:120]
                return None
            # A limit that would cross is a stop, not a limit. Do not convert to DEAL
            # and do not invent a chase offset - refuse and let the caller retry later.
            try:
                ask = float(tick.ask)
                bid = float(tick.bid)
            except (TypeError, ValueError):
                if not self._stop_or_mark("native_limit_quote_invalid"):
                        self._last_open_trade_block_reason = "exec_gate:" + str("native_limit_quote_invalid")[:120]
                return None
            if direction == "LONG" and entry_price > ask:
                if self._stop_or_mark("native_limit_would_cross"):
                            return None
            if direction == "SHORT" and entry_price < bid:
                if self._stop_or_mark("native_limit_would_cross"):
                            return None
        else:
            if self._challenge_book():
                self._last_open_trade_block_reason = "exec_entry:no_decision"
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
                if self._stop_or_mark("sl_wrong_side_vs_fresh_tick"):
                            return None
        if self._challenge_book() and sl is None:
            self._last_open_trade_block_reason = "exec_entry:stop_unset"
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
            if self._stop_or_mark(f"vnext_risk:{vnext_risk_error}"):
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
        if self._challenge_book():
            reject_choice = self._exec_choice(
                "reject",
                reason="open_trade_execution_manager_v4",
                facts={
                    "should_block": bool(execution_manager_v4_decision.should_block),
                    "fatal_reasons": list(execution_manager_v4_decision.fatal_reasons),
                    "direction": direction,
                },
            )
            if reject_choice != "continue":
                self._last_open_trade_block_reason = (
                    "exec_reject:" + (reject_choice or "no_decision")
                )
                return None
        elif execution_manager_v4_decision.should_block:
            logger.error(
                "Execution Manager V4 blocked order before broker request: %s",
                ",".join(execution_manager_v4_decision.fatal_reasons),
            )
            self._last_open_trade_block_reason = (
                "exec_mgr_v4:" + ",".join(execution_manager_v4_decision.fatal_reasons)
            )
            return None
        if pretrade_cost_error:
            block_reason = pretrade_cost_error
            try:
                from src.judgment.cost_choices import filter_pretrade_block
                block_reason = filter_pretrade_block(pretrade_cost_model, pretrade_cost_error)
            except Exception:
                block_reason = None
            if block_reason:
                logger.error(
                    "GTOS vNext production pre-trade cost model failed closed: %s",
                    block_reason,
                )
                if self._stop_or_mark(f"pretrade_cost:{block_reason}"):
                    return None
        risk_amount = account_balance * (risk_pct / 100)
        # ---- F5 minimal-size seam (default OFF; `_f5_scaler` is None) ----------------------
        # This is the LAST step at which money size is decided, and it is deliberately the last.
        # Everything that decides WHETHER to trade has already run at NOMINAL: admission, the
        # cluster cap, the Kelly-lite conviction multiplier, the 4 % gross open-risk cap and the
        # governor all ran before `open_trade` was called; the pre-trade cost model (above) and
        # Execution Manager V4 (above) both received `risk_pct` unchanged. Moving this earlier
        # would change a decision surface -- the cost model would price a $10 trade and its veto
        # would differ, and Execution Manager V4's blocks would differ. Do not move it.
        f5_nominal_risk_amount = risk_amount
        if self._f5_scaler is not None:
            self._stamp_size_room_facts(trade_params, account_balance)
            risk_amount = self._f5_scaler.scaled_risk_amount(risk_amount, trade_params)
            _room_last = getattr(self._f5_scaler, "last", None) or {}
            if risk_amount is not None and _room_last.get("binding_room_usd") is not None:
                _room_equity = trade_params.get("equity")
                try:
                    _room_pct = 100.0 * float(risk_amount) / float(_room_equity)
                except (TypeError, ValueError, ZeroDivisionError):
                    _room_pct = None
                if _room_pct is None:
                    logger.info(
                        "Position sizing: size hop cash %.2f USD inside binding room %.2f USD",
                        float(risk_amount),
                        float(_room_last["binding_room_usd"]),
                    )
                else:
                    logger.info(
                        "Position sizing: size hop cash %.2f USD (%.4f%% of equity %.2f) "
                        "inside binding room %.2f USD",
                        float(risk_amount),
                        _room_pct,
                        float(_room_equity),
                        float(_room_last["binding_room_usd"]),
                    )
            refuse = (getattr(self._f5_scaler, "last", None) or {}).get("f5_refuse_reason")
            if refuse:
                if self._stop_or_mark(str(refuse)):
                    return None
            if risk_amount is None:
                if not self._stop_or_mark("size_not_decided"):
                    self._last_open_trade_block_reason = "exec_gate:" + str("size_not_decided")[:120]
                return None
        self._f5_last_round_up = None
        require_broker_geometry = self._vnext_requires_verified_broker_geometry(trade_params)
        sym_info = self._mt5_symbol_info()
        # Observation-only projection of the broker geometry already read for the sizing decision.
        # The order router consumes this on early refusals; no second symbol-info call is made.
        geometry_observation = {"available": sym_info is not None}
        if sym_info is not None:
            for field_name in (
                "trade_stops_level", "trade_freeze_level", "point", "trade_tick_size",
                "trade_tick_value", "volume_min", "volume_max", "volume_step",
                "trade_contract_size",
            ):
                geometry_observation[field_name] = getattr(sym_info, field_name, None)
        trade_params["gtos_live_flow_broker_geometry"] = geometry_observation

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
        challenge_lot = None
        volume_min = None
        volume_step = None
        volume_max = None
        _lots_fact = None
        send_rows = {}
        timeout_score = None
        adopt_wait_s = None
        expiry_score = None
        if self._challenge_book():
            if sym_info is not None:
                try:
                    volume_min = float(sym_info.volume_min)
                except (TypeError, ValueError, AttributeError):
                    volume_min = None
                try:
                    volume_step = float(sym_info.volume_step)
                except (TypeError, ValueError, AttributeError):
                    volume_step = None
                try:
                    volume_max = float(sym_info.volume_max)
                except (TypeError, ValueError, AttributeError):
                    volume_max = None
            _sed = trade_params.get("gtos_vnext_source_event_details") or {}
            if not isinstance(_sed, dict):
                _sed = {}
            _sleeve = (
                trade_params.get("sleeve")
                or trade_params.get("tag")
                or _sed.get("sleeve")
                or _sed.get("tag")
            )
            _risk = None
            try:
                if risk_amount is not None:
                    _risk = float(risk_amount)
            except (TypeError, ValueError):
                _risk = None
            _balance = None
            try:
                if account_balance is not None:
                    _balance = float(account_balance)
            except (TypeError, ValueError):
                _balance = None
            _lots_fact = None
            if lots is not None:
                try:
                    _lots_fact = float(lots)
                except (TypeError, ValueError):
                    _lots_fact = None
                else:
                    if not math.isfinite(_lots_fact):
                        _lots_fact = None
            _spread_points = None
            _point = None
            _stops_level = None
            _freeze_level = None
            _filling_mode = None
            _tick_size = None
            if sym_info is not None:
                try:
                    _spread_points = float(getattr(sym_info, "spread"))
                except (TypeError, ValueError, AttributeError):
                    _spread_points = None
                _point = getattr(sym_info, "point", None)
                _stops_level = getattr(sym_info, "trade_stops_level", None)
                _freeze_level = getattr(sym_info, "trade_freeze_level", None)
                _filling_mode = getattr(sym_info, "filling_mode", None)
                _tick_size = getattr(sym_info, "trade_tick_size", None) or _point
            send_facts = {
                "lots": _lots_fact,
                "volume_min": volume_min,
                "volume_step": volume_step,
                "volume_max": volume_max,
                "sl_distance": sizing_sl_distance,
                "risk": _risk,
                "risk_amount": _risk,
                "balance": _balance,
                "sleeve": _sleeve,
                "direction": direction,
                "candidate_id": (
                    trade_params.get("candidate_id") or _sed.get("candidate_id")
                ),
                "round_up_enabled": bool(
                    getattr(getattr(self, "_f5_scaler", None), "round_up_enabled", False)
                ),
                "filling_mode": _filling_mode,
                "spread_points": _spread_points,
                "point": _point,
                "trade_stops_level": _stops_level,
                "trade_freeze_level": _freeze_level,
                "trade_tick_size": _tick_size,
                "bid": getattr(tick, "bid", None) if tick is not None else None,
                "ask": getattr(tick, "ask", None) if tick is not None else None,
                "expiry_bars_fact": trade_params.get("expiry_bars_fact"),
                "entry_price": entry_price,
                "stop_loss": sl,
                "decision_time_utc": trade_params.get("decision_time_utc"),
                "pending_created_time_utc": trade_params.get("pending_created_time_utc"),
            }
            send_rows = self._ask_send(
                reason="open_trade",
                proposed=_lots_fact,
                include=(
                    "lot",
                    "spread",
                    "deviation",
                    "filling",
                    "expiry",
                    "timeout",
                    "adopt_wait",
                ),
                facts=send_facts,
            )
            lot_row = send_rows.get("lot") if isinstance(send_rows, dict) else None
            challenge_lot = self._row_choice(lot_row)
            lot_score = None
            if challenge_lot == "place":
                lot_score = self._spine_score(
                    "lot",
                    "The score you return is the volume in lots for this order. "
                    "An empty score does not send.",
                    send_facts,
                    sym_info=sym_info,
                )
            if challenge_lot != "place" or lot_score is None or lot_score <= 0:
                self._last_open_trade_block_reason = (
                    "exec_lot:" + (
                        "unset" if challenge_lot == "place" else (challenge_lot or "no_decision")
                    )
                )
                return None
            lots = lot_score
        if lots is None:
            logger.error("Cannot calculate verified lot size -- aborting trade")
            if not self._stop_or_mark("lot_size_unverified"):
                self._last_open_trade_block_reason = "exec_gate:" + str("lot_size_unverified")[:120]
            return None
        if self._f5_scaler is not None and not self._challenge_book():
            from .ultimate_book.minimal_size import f5_lots_or_ticks_refuse_reason
            tick_size = None
            if sym_info is not None:
                tick_size = getattr(sym_info, "trade_tick_size", None) or getattr(
                    sym_info, "point", None
                )
            geo_refuse = f5_lots_or_ticks_refuse_reason(
                lots=lots,
                stop_dist=sizing_sl_distance,
                tick_size=tick_size,
            )
            if geo_refuse:
                if self._stop_or_mark(geo_refuse):
                    return None
        geometry_observation["lots_calculated"] = float(lots)
        # COMP-6 breadth-coverage: distinguish a DETERMINISTIC sub-min-lot unit (a low-conviction breadth
        # sleeve sized below the broker volume_min at this account size -- it can NEVER place and must not be
        # retried every tick) from a TRANSIENT broker volume-geometry read miss (which _normalize_volume also
        # returns None for). A distinct 'below_min_lot' reason -> the book treats it as terminal (skip once
        # per bar) + surfaces the shed breadth unit, instead of the opaque/transient lot_normalize_failed.
        if challenge_lot is None and require_broker_geometry and sym_info is not None:
            try:
                _vmin = float(sym_info.volume_min)
            except (TypeError, ValueError, AttributeError):
                _vmin = None
            if _vmin is not None and _vmin > 0 and float(lots) < _vmin:
                if self._f5_scaler is not None and self._f5_scaler.round_up_enabled:
                    # F5: NEVER shed. The shed below is correct for production -- a sub-minimum
                    # unit is a real breadth loss -- and destroys this experiment, because at a
                    # $10 target it deletes exactly the expensive-stop instruments (BTCUSD,
                    # XAGUSD, XAUUSD, ETHUSD on FTMO; those plus the 10x-contract indices on
                    # redacted_account) and the surviving sample answers no cost question. Round UP to
                    # volume_min and RECORD the inflation, so the dollar-weighted reweighting is
                    # exact rather than modelled. Measured shares: 5.7 % of FTMO trades carrying
                    # 13.4 % of dollar risk; 10.0 % / 24.3 % on redacted_account.
                    from .ultimate_book.minimal_size import round_up_to_min_lot
                    lots, _f5_prov = round_up_to_min_lot(float(lots), sym_info)
                    self._f5_last_round_up = _f5_prov
                    if _f5_prov.get("f5_round_up") not in ("applied", "not_needed"):
                        logger.error(
                            "F5 round-up refused (%s) on %s -- an unreadable or pathological "
                            "volume geometry must not produce an off-grid lot",
                            _f5_prov.get("f5_round_up"), self.symbol)
                        self._last_open_trade_block_reason = (
                            f"f5_round_up_refused:{_f5_prov.get('f5_round_up')}")
                        return None
                    logger.info(
                        "F5 round-up applied on %s: %.6f -> %.6f (volume_min; inflation x%.2f)",
                        self.symbol, float(_f5_prov.get("f5_lots_requested") or 0.0),
                        float(_f5_prov.get("f5_lots_placed") or 0.0),
                        float(_f5_prov.get("f5_lot_inflation") or 1.0))
                else:
                    logger.warning(
                        "vNext book unit below broker min lot -> breadth unit shed (NOT retried): "
                        "%.6f < volume_min %.6f (%s)", float(lots), _vmin, self.symbol)
                    self._last_open_trade_block_reason = (
                        f"below_min_lot:{float(lots):.4f}<{_vmin:.4f}")
                    return None
        if not self._challenge_book():
            lots = self._normalize_volume(
                lots,
                sym_info,
                require_broker_geometry=require_broker_geometry,
            )
        if lots is None:
            # only the geometry-read miss reaches here now (sub-min handled above) -> TRANSIENT.
            if self._last_open_trade_block_reason is None:
                if not self._stop_or_mark("lot_normalize_failed"):
                    self._last_open_trade_block_reason = "exec_gate:" + str("lot_normalize_failed")[:120]
            return None
        geometry_observation["lots_normalized"] = float(lots)
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
            if self._stop_or_mark("cash_risk_unverified"):
                return None
        geometry_observation["pre_send_cash_risk_amount"] = pre_send_cash_risk_amount
        if self._f5_scaler is not None:
            # `pre_send_cash_risk_amount` is the broker's OWN `order_calc_profit` on the
            # NORMALIZED volume -- the true realised risk, not an estimate -- which is what makes
            # the dollar reweighting exact. Stamped onto trade_params so the packet, the trade
            # record and the F5 capture all carry the same three numbers.
            _f5_last = getattr(self._f5_scaler, "last", None) or {}
            trade_params["f5_nominal_risk_usd"] = float(f5_nominal_risk_amount or 0.0)
            trade_params["f5_intended_risk_usd"] = float(
                _f5_last.get("f5_intended_risk_usd") or self._f5_scaler.target_risk_usd)
            trade_params["f5_actual_risk_usd"] = float(pre_send_cash_risk_amount or 0.0)
            trade_params["f5_round_up"] = self._f5_last_round_up
        if self._challenge_book():
            filling_choice = self._row_choice(send_rows.get("filling"))
            type_filling = _FILLING_ENUM.get(filling_choice or "")
            if type_filling is None:
                self._last_open_trade_block_reason = (
                    "exec_filling:" + (filling_choice or "no_decision")
                )
                return None
            deviation_choice = self._row_choice(send_rows.get("deviation"))
            deviation_score = None
            if deviation_choice == "use":
                deviation_score = self._spine_score(
                    "deviation_points",
                    "The score you return is the deviation in points for this order. "
                    "An empty score leaves the deviation unset.",
                    send_facts,
                    sym_info=sym_info,
                )
            deviation_points = None
            if (
                deviation_score is not None
                and deviation_score > 0
                and abs(deviation_score - round(deviation_score)) <= 1e-9
            ):
                deviation_points = int(round(deviation_score))
            expiry_choice = self._row_choice(send_rows.get("expiry"))
            expiry_score = None
            if expiry_choice == "use":
                expiry_score = self._spine_score(
                    "expiry",
                    "The score you return is the expiry in seconds for this order. "
                    "An empty score leaves the expiry unset.",
                    send_facts,
                )
            if expiry_score is not None and expiry_score <= 0:
                expiry_score = None
            timeout_choice = self._row_choice(send_rows.get("timeout"))
            timeout_score = None
            if timeout_choice == "wait":
                timeout_score = self._spine_score(
                    "timeout",
                    "The score you return is the wait in seconds for this order send. "
                    "An empty score leaves the wait unset.",
                    send_facts,
                )
            if timeout_score is not None and timeout_score <= 0:
                timeout_score = None
            adopt_choice = self._row_choice(send_rows.get("adopt_wait"))
            adopt_wait_s = None
            if adopt_choice == "wait":
                adopt_score = self._spine_score(
                    "adopt_wait",
                    "The score you return is the adopt wait in seconds for this order. "
                    "An empty score leaves the adopt wait unset.",
                    send_facts,
                )
                if adopt_score is not None and adopt_score > 0:
                    adopt_wait_s = adopt_score
            spread_choice = self._row_choice(send_rows.get("spread"))
            if spread_choice != "spread_ok":
                self._last_open_trade_block_reason = (
                    "exec_spread:" + (spread_choice or "no_decision")
                )
                return None
        else:
            type_filling = self._order_filling_mode(
                sym_info,
                require_broker_geometry=require_broker_geometry,
            )
            if type_filling is None:
                if not self._stop_or_mark("filling_mode_unresolved"):
                    self._last_open_trade_block_reason = "exec_gate:" + str("filling_mode_unresolved")[:120]
                return None
            deviation_points = self._order_deviation_points(
                sym_info,
                trade_params,
                require_broker_geometry=require_broker_geometry,
            )
            if deviation_points is None:
                if not self._stop_or_mark("deviation_unresolved"):
                    self._last_open_trade_block_reason = "exec_gate:" + str("deviation_unresolved")[:120]
                return None

        # Traceable broker comment for W7 book trades (sleeve identity). FTMO-Server3 truncates to ~16.
        _sed = trade_params.get("gtos_vnext_source_event_details") or {}
        _sleeve = _sed.get("sleeve")
        if _sleeve:
            order_comment = f"{self._comment_prefix}{_sleeve}"[:16]
        else:
            # FAIL-LOUD W7 tag, NOT the retired 'GoldAgent_OBRetest' name (owner mandate: zero
            # old-system residue on a live order). A book order should ALWAYS carry its sleeve; an
            # empty sleeve is a wiring defect to surface, not a legacy-tagged trade.
            order_comment = f"{self._comment_prefix}UNTAGGED"[:16]
            logging.getLogger(__name__).warning(
                "W7 book order missing source_event_details.sleeve -> comment 'W7:UNTAGGED' "
                "(symbol=%s); investigate the missing sleeve tag.", self.symbol)
        if trade_params.get("gtos_native_pending_limit"):
            request = {
                "action": TRADE_ACTION_PENDING,
                "symbol": self.symbol,
                "volume": lots,
                "type": (
                    ORDER_TYPE_BUY_LIMIT if direction == "LONG" else ORDER_TYPE_SELL_LIMIT
                ),
                "price": entry_price,
                "sl": sl,
                "tp": tp1,
                "magic": self._magic,
                "comment": order_comment,
                "type_time": 0,  # ORDER_TIME_GTC
                "type_filling": type_filling,
            }
            if self._f5_scaler is not None and not self._challenge_book():
                # CONTRACT leftover (Fable 5.1): broker-side expiration so a
                # restart cannot leave a GTC ghost. Same clock as the v2 sweep
                # (tick.time vs order.time_setup). Fail open to GTC if no tick.
                try:
                    # CONTRACT V3 (Fable 5.1): RAW module is self.mt5._mt5. Never
                    # self._mt5 (AttributeError → GTC, order 180770382). Honour
                    # expiration_mode & 4. Positions are not limits.
                    from src.components.ultimate_book.minimal_size import (
                        f5_native_limit_expiration,
                    )
                    _raw = getattr(self.mt5, "_mt5", None)
                    _tt, _exp = f5_native_limit_expiration(_raw, self.symbol)
                except Exception:
                    _tt, _exp = 0, None
                if _tt == 1 and _exp:
                    request["type_time"] = 1  # ORDER_TIME_SPECIFIED
                    request["expiration"] = int(_exp)
        else:
            order_type = 0 if direction == "LONG" else 1
            request = {
                "action": 1,  # TRADE_ACTION_DEAL
                "symbol": self.symbol,
                "volume": lots,
                "type": order_type,
                "price": entry_price,
                "sl": sl,
                "tp": tp1,
                "magic": self._magic,
                "comment": order_comment,
                "type_time": 0,  # ORDER_TIME_GTC
                "type_filling": type_filling,
            }

        place_kwargs = {}
        if self._challenge_book():
            request, place_kwargs = self.optional_send_request(
                request,
                deviation_points=deviation_points,
                expiry_score=expiry_score,
                timeout_score=timeout_score,
                adopt_wait_s=adopt_wait_s,
            )
        elif deviation_points is not None:
            request["deviation"] = deviation_points

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
        if self._challenge_book():
            result = self.safe_place_order(request, **place_kwargs)
        else:
            result = self.safe_place_order(request)
        if (getattr(self, "_last_order_send_diagnostic", None) or {}).get("status") == "news_blocked_no_order_send":
            news = dict(getattr(self, "_last_news_pre_send", None) or {})
            trade_params["news_pre_send"] = news
            self._last_open_trade_block_reason = news.get("reason") or "news_blocked_no_order_send"
            return None
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
            if result is None:
                # P1: a None is one of three diagnostic statuses, not a fill timeout.
                reason, block_reason = label_none_place_result(
                    self._last_order_send_diagnostic
                )
                self._last_open_trade_block_reason = block_reason
            else:
                reason = result.comment
                self._last_open_trade_block_reason = f"order_rejected:{reason}"
            logger.error(f"Order failed: {reason}")
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

        if trade_params.get("gtos_native_pending_limit"):
            # A pending accept is not a fill. Park the working order and leave
            # active_trade empty so manage_open_positions does not treat this as a position.
            return self._park_native_pending_limit(trade_params, result, request)

        entry_deal_accounting = self._lookup_entry_deal_accounting(
            result,
            order_send_time=order_send_time,
            order_result_time=order_result_time,
        )
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
                self._modify_tp(result.order, dynamic_final_target_price)
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
            ticket=result.order,
            direction=direction,
            entry_price=filled_price,
            stop_loss=sl,
            take_profit_1=ts_tp1,
            take_profit_2=ts_tp2,
            take_profit_3=ts_tp3,
            initial_volume=lots,
            current_volume=lots,
            sl_distance=state_sl_distance,
            trade_id=f"tr_{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M')}",
            entry_time=datetime.now(timezone.utc).isoformat(),
            original_ai_tp1=original_ai_tp1,
            j46_j49_active=bool(j46_j49_active and risk_basis_sl_distance > 0),
            entry_order_ticket=result.order,
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
            gtos_vnext_profit_harvest_stop_activation_mfe_r=float(
                (profit_harvest_params or {}).get("stop_activation_mfe_r") or 0.0
            ),
            gtos_vnext_profit_harvest_target_activation_fraction=float(
                (profit_harvest_params or {}).get("target_activation_fraction") or 0.0
            ),
            gtos_vnext_profit_harvest_trail_gap_r=float(
                (profit_harvest_params or {}).get("trail_gap_r") or 0.0
            ),
            gtos_vnext_profit_harvest_protect_floor_r=float(
                (profit_harvest_params or {}).get("protect_floor_r") or 0.0
            ),
            gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled=bool(
                (profit_harvest_params or {}).get("cost_aware_protect_floor_enabled")
            ),
            gtos_vnext_profit_harvest_cost_aware_margin_r=float(
                (profit_harvest_params or {}).get("cost_aware_margin_r") or 0.0
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
            gtos_vnext_profit_harvest_armed_stale_close_enabled=bool(
                (profit_harvest_params or {}).get("armed_stale_close_enabled")
            ),
            gtos_vnext_profit_harvest_armed_stale_minutes=(
                (profit_harvest_params or {}).get("armed_stale_minutes")
            ),
            gtos_vnext_profit_harvest_armed_stale_min_mfe_r=float(
                (profit_harvest_params or {}).get("armed_stale_min_mfe_r") or 0.0
            ),
            gtos_vnext_profit_harvest_armed_stale_close_below_r=float(
                (profit_harvest_params or {}).get("armed_stale_close_below_r") or 0.0
            ),
            gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise=float(
                (profit_harvest_params or {}).get("min_hold_minutes_before_stop_raise")
                or 0.0
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
        self._known_tickets.add(result.order)
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
                ticket=result.order,
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
                ticket=result.order,
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
        poi_state = self._context_value(
            telemetry_context,
            trade_params,
            "poi_state",
        )
        poi_state = poi_state if isinstance(poi_state, dict) else {}
        causal_poi_lifecycle = self._context_value(
            telemetry_context,
            trade_params,
            "causal_poi_lifecycle",
        )
        causal_poi_lifecycle = (
            dict(causal_poi_lifecycle)
            if isinstance(causal_poi_lifecycle, dict)
            else {}
        )
        causal_poi_lifecycle_required = bool(
            self._context_value(
                telemetry_context,
                trade_params,
                "causal_poi_lifecycle_required",
            )
            or causal_poi_lifecycle
        )
        lifecycle_decision_time = self._context_value(
            telemetry_context,
            trade_params,
            "decision_time_utc",
        )
        if causal_poi_lifecycle_required:
            lifecycle_failures = causal_poi_lifecycle_contract_failures(
                causal_poi_lifecycle,
                poi_state=poi_state,
                decision_time_utc=lifecycle_decision_time,
            )
            declared_lifecycle_hash = self._context_value(
                telemetry_context,
                trade_params,
                "causal_poi_lifecycle_hash_sha256",
            )
            if (
                declared_lifecycle_hash
                and declared_lifecycle_hash
                != causal_poi_lifecycle.get("lifecycle_hash_sha256")
            ):
                lifecycle_failures = tuple(lifecycle_failures) + (
                    "causal_poi_lifecycle_hash_projection_mismatch",
                )
            if lifecycle_failures or causal_poi_lifecycle.get(
                "scheduler_rankable_now"
            ) is not True:
                logger.warning(
                    "Pending limit intent blocked by causal POI lifecycle: %s",
                    list(lifecycle_failures)
                    or [
                        causal_poi_lifecycle.get("primary_reason")
                        or "poi_not_scheduler_rankable_now"
                    ],
                )
                return None
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
            profit_harvest_enabled = configured_profit_harvest.get("enabled")
        profit_harvest_min_mfe_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_min_mfe_r",
        )
        if profit_harvest_min_mfe_r in (None, ""):
            profit_harvest_min_mfe_r = configured_profit_harvest.get("min_mfe_r")
        profit_harvest_stop_activation_mfe_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_stop_activation_mfe_r",
        )
        if profit_harvest_stop_activation_mfe_r in (None, ""):
            profit_harvest_stop_activation_mfe_r = configured_profit_harvest[
                "stop_activation_mfe_r"
            ]
        profit_harvest_target_activation_fraction = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_target_activation_fraction",
        )
        if profit_harvest_target_activation_fraction in (None, ""):
            profit_harvest_target_activation_fraction = configured_profit_harvest[
                "target_activation_fraction"
            ]
        profit_harvest_trail_gap_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_trail_gap_r",
        )
        if profit_harvest_trail_gap_r in (None, ""):
            profit_harvest_trail_gap_r = configured_profit_harvest.get("trail_gap_r")
        profit_harvest_protect_floor_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_protect_floor_r",
        )
        if profit_harvest_protect_floor_r in (None, ""):
            profit_harvest_protect_floor_r = configured_profit_harvest.get("protect_floor_r")
        profit_harvest_cost_aware_protect_floor_enabled = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled",
        )
        if profit_harvest_cost_aware_protect_floor_enabled in (None, ""):
            profit_harvest_cost_aware_protect_floor_enabled = configured_profit_harvest[
                "cost_aware_protect_floor_enabled"
            ]
        profit_harvest_cost_aware_margin_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_cost_aware_margin_r",
        )
        if profit_harvest_cost_aware_margin_r in (None, ""):
            profit_harvest_cost_aware_margin_r = configured_profit_harvest[
                "cost_aware_margin_r"
            ]
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
            profit_harvest_stale_minutes = configured_profit_harvest.get("stale_minutes")
        profit_harvest_stale_min_mfe_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_stale_min_mfe_r",
        )
        if profit_harvest_stale_min_mfe_r in (None, ""):
            profit_harvest_stale_min_mfe_r = configured_profit_harvest.get("stale_min_mfe_r")
        profit_harvest_stale_close_below_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_stale_close_below_r",
        )
        if profit_harvest_stale_close_below_r in (None, ""):
            profit_harvest_stale_close_below_r = configured_profit_harvest[
                "stale_close_below_r"
            ]
        profit_harvest_armed_stale_close_enabled = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_armed_stale_close_enabled",
        )
        if profit_harvest_armed_stale_close_enabled in (None, ""):
            profit_harvest_armed_stale_close_enabled = configured_profit_harvest[
                "armed_stale_close_enabled"
            ]
        profit_harvest_armed_stale_minutes = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_armed_stale_minutes",
        )
        if profit_harvest_armed_stale_minutes in (None, ""):
            profit_harvest_armed_stale_minutes = configured_profit_harvest[
                "armed_stale_minutes"
            ]
        profit_harvest_armed_stale_min_mfe_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_armed_stale_min_mfe_r",
        )
        if profit_harvest_armed_stale_min_mfe_r in (None, ""):
            profit_harvest_armed_stale_min_mfe_r = configured_profit_harvest[
                "armed_stale_min_mfe_r"
            ]
        profit_harvest_armed_stale_close_below_r = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_armed_stale_close_below_r",
        )
        if profit_harvest_armed_stale_close_below_r in (None, ""):
            profit_harvest_armed_stale_close_below_r = configured_profit_harvest[
                "armed_stale_close_below_r"
            ]
        profit_harvest_min_hold_minutes_before_stop_raise = self._context_value(
            telemetry_context,
            trade_params,
            "gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise",
        )
        if profit_harvest_min_hold_minutes_before_stop_raise in (None, ""):
            profit_harvest_min_hold_minutes_before_stop_raise = configured_profit_harvest[
                "min_hold_minutes_before_stop_raise"
            ]
        if (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "be_after_trigger"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_be.get("trigger_r")
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_be.get("final_target_r")
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_be.get("time_stop_bars")
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "partial_be_runner"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_partial.get("trigger_r")
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_partial.get("final_target_r")
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_partial.get("time_stop_bars")
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "trailing_runner"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_trailing.get("trigger_r")
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_trailing.get("final_target_r")
            if dynamic_trail_gap_r in (None, ""):
                dynamic_trail_gap_r = configured_trailing.get("trail_gap_r")
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_trailing.get("time_stop_bars")
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "momentum_exhaustion"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_momentum.get("trigger_r")
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_momentum.get("final_target_r")
            if dynamic_momentum_pullback_r in (None, ""):
                dynamic_momentum_pullback_r = configured_momentum.get("pullback_r")
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_momentum.get("time_stop_bars")
        elif (
            dynamic_applied
            and str(dynamic_selected_policy or "").strip().lower()
            == "time_stop"
        ):
            if dynamic_be_trigger_r in (None, ""):
                dynamic_be_trigger_r = configured_time_stop.get("final_target_r")
            if dynamic_final_target_r in (None, ""):
                dynamic_final_target_r = configured_time_stop.get("final_target_r")
            if dynamic_time_stop_bars in (None, ""):
                dynamic_time_stop_bars = configured_time_stop.get("time_stop_bars")

        dynamic_be_trigger_r = self._safe_float(dynamic_be_trigger_r)
        dynamic_final_target_r = self._safe_float(dynamic_final_target_r)
        dynamic_trail_gap_r = self._safe_float(dynamic_trail_gap_r)
        dynamic_momentum_pullback_r = self._safe_float(dynamic_momentum_pullback_r)
        profit_harvest_min_mfe_r = self._safe_float(profit_harvest_min_mfe_r)
        profit_harvest_stop_activation_mfe_r = self._safe_float(
            profit_harvest_stop_activation_mfe_r
        )
        profit_harvest_target_activation_fraction = self._safe_float(
            profit_harvest_target_activation_fraction
        )
        profit_harvest_trail_gap_r = self._safe_float(profit_harvest_trail_gap_r)
        profit_harvest_protect_floor_r = self._safe_float(
            profit_harvest_protect_floor_r
        )
        profit_harvest_cost_aware_protect_floor_enabled = self._bool_param_enabled(
            profit_harvest_cost_aware_protect_floor_enabled
        )
        profit_harvest_cost_aware_margin_r = self._safe_float(
            profit_harvest_cost_aware_margin_r
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
        profit_harvest_armed_stale_close_enabled = self._bool_param_enabled(
            profit_harvest_armed_stale_close_enabled
        )
        profit_harvest_armed_stale_min_mfe_r = self._safe_float(
            profit_harvest_armed_stale_min_mfe_r
        )
        profit_harvest_armed_stale_close_below_r = self._safe_float(
            profit_harvest_armed_stale_close_below_r
        )
        profit_harvest_min_hold_minutes_before_stop_raise = self._safe_float(
            profit_harvest_min_hold_minutes_before_stop_raise
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
        if profit_harvest_armed_stale_minutes not in (None, ""):
            try:
                profit_harvest_armed_stale_minutes = int(
                    profit_harvest_armed_stale_minutes
                )
            except (TypeError, ValueError):
                profit_harvest_armed_stale_minutes = None
        else:
            profit_harvest_armed_stale_minutes = None

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
            candidate_id=self._context_value(
                telemetry_context,
                trade_params,
                "candidate_id",
            ),
            decision_time_utc=self._context_value(
                telemetry_context,
                trade_params,
                "decision_time_utc",
            ),
            canonical_replay_candidate_instance_key=self._context_value(
                telemetry_context,
                trade_params,
                "canonical_replay_candidate_instance_key",
            ),
            source_bound_replay_candidate_instance_key=self._context_value(
                telemetry_context,
                trade_params,
                "source_bound_replay_candidate_instance_key",
            ),
            candidate_instance_identity_status=self._context_value(
                telemetry_context,
                trade_params,
                "candidate_instance_identity_status",
            ),
            poi_id=self._context_value(
                telemetry_context,
                trade_params,
                "poi_id",
            )
            or causal_poi_lifecycle.get("poi_id"),
            poi_state_hash_sha256=self._context_value(
                telemetry_context,
                trade_params,
                "poi_state_hash_sha256",
            )
            or causal_poi_lifecycle.get("poi_state_hash_sha256"),
            causal_poi_lifecycle_required=causal_poi_lifecycle_required,
            causal_poi_lifecycle=(
                causal_poi_lifecycle if causal_poi_lifecycle else None
            ),
            causal_poi_lifecycle_hash_sha256=(
                causal_poi_lifecycle.get("lifecycle_hash_sha256")
                if causal_poi_lifecycle
                else None
            ),
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
            gtos_vnext_profit_harvest_stop_activation_mfe_r=(
                profit_harvest_stop_activation_mfe_r
            ),
            gtos_vnext_profit_harvest_target_activation_fraction=(
                profit_harvest_target_activation_fraction
            ),
            gtos_vnext_profit_harvest_trail_gap_r=profit_harvest_trail_gap_r,
            gtos_vnext_profit_harvest_protect_floor_r=profit_harvest_protect_floor_r,
            gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled=(
                profit_harvest_cost_aware_protect_floor_enabled
            ),
            gtos_vnext_profit_harvest_cost_aware_margin_r=(
                profit_harvest_cost_aware_margin_r
            ),
            gtos_vnext_profit_harvest_close_on_giveback_r=(
                profit_harvest_close_on_giveback_r
            ),
            gtos_vnext_profit_harvest_stale_minutes=profit_harvest_stale_minutes,
            gtos_vnext_profit_harvest_stale_min_mfe_r=profit_harvest_stale_min_mfe_r,
            gtos_vnext_profit_harvest_stale_close_below_r=(
                profit_harvest_stale_close_below_r
            ),
            gtos_vnext_profit_harvest_armed_stale_close_enabled=(
                profit_harvest_armed_stale_close_enabled
            ),
            gtos_vnext_profit_harvest_armed_stale_minutes=(
                profit_harvest_armed_stale_minutes
            ),
            gtos_vnext_profit_harvest_armed_stale_min_mfe_r=(
                profit_harvest_armed_stale_min_mfe_r
            ),
            gtos_vnext_profit_harvest_armed_stale_close_below_r=(
                profit_harvest_armed_stale_close_below_r
            ),
            gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise=(
                profit_harvest_min_hold_minutes_before_stop_raise
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
            allocation_cash_usd=self._positive_fact(trade_params.get("allocation_cash_usd")),
            min_lot_risk_usd=self._positive_fact(trade_params.get("min_lot_risk_usd")),
            allocation_sleeve=(
                str(trade_params.get("sleeve") or trade_params.get("tag") or "") or None
            ),
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
        if self._challenge_book():
            reject_choice = self._exec_choice(
                "reject",
                reason="set_limit_intent",
                facts={
                    "should_block": bool(v4_decision.should_block),
                    "fatal_reasons": list(v4_decision.fatal_reasons),
                    "direction": getattr(intent, "direction", None),
                },
            )
            if reject_choice != "continue":
                return None
        elif v4_decision.should_block:
            logger.warning(
                "Execution Manager V4 blocked pending limit intent before persistence: %s",
                ",".join(v4_decision.fatal_reasons),
            )
            return None
        self.pending_intent = intent
        self._pending_account_balance = account_balance
        logger.info(
            "Limit intent set: %s %s limit=%.5f sl=%.5f tp=%.5f expires=%s candles",
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

    @staticmethod
    def _merge_denominator_forward_capture_config(
        target: dict[str, Any],
        source: dict | None,
    ) -> None:
        if not isinstance(source, dict):
            return
        alias_map = {
            "enabled": DENOMINATOR_FORWARD_CAPTURE_ENABLED_CONFIG_KEY,
            "log_enabled": DENOMINATOR_FORWARD_CAPTURE_LOG_ENABLED_CONFIG_KEY,
            "log_path": DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_CONFIG_KEY,
        }
        for key in (
            DENOMINATOR_FORWARD_CAPTURE_ENABLED_CONFIG_KEY,
            DENOMINATOR_FORWARD_CAPTURE_LOG_ENABLED_CONFIG_KEY,
            DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_CONFIG_KEY,
        ):
            if key in source:
                target[key] = source[key]
        for alias, canonical in alias_map.items():
            if alias in source:
                target[canonical] = source[alias]

    @staticmethod
    def _denominator_forward_capture_configured_families(
        source: dict | None,
    ) -> Any:
        if not isinstance(source, dict):
            return None
        for key in (
            DENOMINATOR_FORWARD_CAPTURE_REQUIREMENT_FAMILIES_FIELD,
            "requirement_families",
            "families",
        ):
            value = source.get(key)
            if value:
                return value
        return None

    def _denominator_forward_capture_entry_fields(
        self,
        telemetry_context: dict,
    ) -> dict[str, Any]:
        runtime_config: dict[str, Any] = {}
        contract_config = self.config.get("denominator_forward_capture_contract")
        capture_config = self.config.get("denominator_forward_capture")
        telemetry_runtime_config = telemetry_context.get(
            DENOMINATOR_FORWARD_CAPTURE_RUNTIME_CONFIG_FIELD
        )
        self._merge_denominator_forward_capture_config(runtime_config, self.config)
        self._merge_denominator_forward_capture_config(
            runtime_config,
            contract_config,
        )
        self._merge_denominator_forward_capture_config(
            runtime_config,
            capture_config,
        )
        self._merge_denominator_forward_capture_config(runtime_config, telemetry_context)
        self._merge_denominator_forward_capture_config(
            runtime_config,
            telemetry_runtime_config,
        )

        fields: dict[str, Any] = {}
        if runtime_config:
            fields[DENOMINATOR_FORWARD_CAPTURE_RUNTIME_CONFIG_FIELD] = runtime_config
        log_path = (
            telemetry_context.get(DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_FIELD)
            or runtime_config.get(DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_CONFIG_KEY)
        )
        if log_path:
            fields[DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_FIELD] = log_path
        families = None
        for source in (
            telemetry_context,
            telemetry_runtime_config,
            contract_config,
            capture_config,
            self.config,
        ):
            families = self._denominator_forward_capture_configured_families(source)
            if families:
                break
        if families:
            fields[DENOMINATOR_FORWARD_CAPTURE_REQUIREMENT_FAMILIES_FIELD] = families
        return fields

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
            order_intent = (
                telemetry_context.get("order_intent")
                or getattr(intent, "gtos_vnext_pending_policy_action", None)
                or "internal_pending_limit_lifecycle"
            )
            denominator_capture_fields = (
                self._denominator_forward_capture_entry_fields(telemetry_context)
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
                "broker_profile_namespace": self._runtime_namespace,
                "broker_account_namespace": self._runtime_namespace,
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
                "order_intent": order_intent,
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
                "gtos_vnext_profit_harvest_stop_activation_mfe_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_stop_activation_mfe_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_target_activation_fraction": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_target_activation_fraction",
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
                "gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled",
                    None,
                ),
                "gtos_vnext_profit_harvest_cost_aware_margin_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_cost_aware_margin_r",
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
                "gtos_vnext_profit_harvest_armed_stale_close_enabled": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_armed_stale_close_enabled",
                    None,
                ),
                "gtos_vnext_profit_harvest_armed_stale_minutes": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_armed_stale_minutes",
                    None,
                ),
                "gtos_vnext_profit_harvest_armed_stale_min_mfe_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_armed_stale_min_mfe_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_armed_stale_close_below_r": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_armed_stale_close_below_r",
                    None,
                ),
                "gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise": getattr(
                    intent,
                    "gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise",
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
            if denominator_capture_fields:
                entry.update(denominator_capture_fields)
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

        # Clock-time expiry is the age hop. An empty score leaves the limit.
        placed_dt = datetime.fromisoformat(intent.placed_time)
        limit_hours = self._spine_score(
            "pending_limit_max_age_hours",
            "The score you return is the maximum age in hours for this resting limit. "
            "An empty score leaves the limit in place. Do not send.",
            {"trade_id": getattr(intent, "trade_id", None), "placed_time": intent.placed_time},
            placed=placed_dt,
            candle=candle,
        )
        if limit_hours is not None and datetime.now(timezone.utc) - placed_dt >= timedelta(hours=float(limit_hours)):
            logger.info(
                "Limit intent expired (age hop %.3fh, %d KZ candles elapsed): %s",
                float(limit_hours),
                intent.candles_elapsed, intent.trade_id,
            )
            try:
                from src.notifications import (
                    build_vnext_notification_context,
                    notify_limit_expired,
                )
                notify_limit_expired(
                    symbol=self.symbol, trade_id=intent.trade_id,
                    reason="pending_limit_age",
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
                reason="pending_limit_age",
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
            else self._spine_score(
                "risk_reward_ratio",
                "The score you return is the reward multiple for this pending limit. "
                "An empty score leaves it unset. Do not send.",
                {
                    "trade_id": getattr(intent, "trade_id", None),
                    "entry_price": getattr(intent, "limit_price", None),
                    "stop_loss": getattr(intent, "stop_loss", None),
                    "take_profit_1": getattr(intent, "take_profit_1", None),
                },
                trade=intent,
                candle=candle,
            )
        )
        fill_trade_params = {
                "direction": intent.direction,
                "entry_price": intent.limit_price,
                **fill_cash_from_pending(intent),
                "symbol": getattr(intent, "source_symbol", None) or self.symbol,
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
        if self._challenge_book():
            reject_choice = self._exec_choice(
                "reject",
                reason="limit_fill",
                ticket=getattr(intent, "trade_id", None),
                facts={
                    "should_block": bool(fill_v4_decision.should_block),
                    "fatal_reasons": list(fill_v4_decision.fatal_reasons),
                    "direction": intent.direction,
                    "current_price": current_price,
                },
            )
            if reject_choice != "continue":
                self._record_pending_limit_lifecycle(
                    intent=intent,
                    intent_after_check="exec_reject_" + (reject_choice or "no_decision"),
                    candles_elapsed_before=candles_elapsed_before,
                    candles_elapsed_after=candles_elapsed_after,
                    candle=candle,
                    telemetry_context=telemetry_context,
                    trigger_condition_met=True,
                    tick=tick,
                    current_price_used=current_price,
                    order_send_attempted=False,
                    order_send_success=False,
                    reason="exec_reject:" + (reject_choice or "no_decision"),
                )
                if reject_choice == "block":
                    self.pending_intent = None
                return None
        elif fill_v4_decision.should_block:
            logger.error(
                "Execution Manager V4 blocked pending fill before broker request: %s",
                ",".join(fill_v4_decision.fatal_reasons),
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
                reason=";".join(fill_v4_decision.fatal_reasons),
            )
            self.pending_intent = None
            return None

        if self._challenge_book():
            fill_choice = self._exec_choice(
                "fill",
                reason="limit_fill",
                ticket=getattr(intent, "trade_id", None),
                proposed=intent.limit_price,
                facts={
                    "direction": intent.direction,
                    "current_price": current_price,
                    "stop_loss": intent.stop_loss,
                    "candles_elapsed": candles_elapsed_after,
                },
            )
            if fill_choice != "fill":
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
            if self._challenge_book():
                retry_choice = self._exec_choice(
                    "retry",
                    reason="limit_fill_failed",
                    ticket=getattr(intent, "trade_id", None),
                    facts={"direction": intent.direction},
                )
                if retry_choice != "retry":
                    self.pending_intent = None
                    return None
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

    def _park_native_pending_limit(self, trade_params: dict, result, request: dict):
        """Record a just-accepted native pending. Does not set active_trade."""
        ticket = int(getattr(result, "order", 0) or 0)
        if ticket <= 0:
            self._last_open_trade_block_reason = "native_pending_no_ticket"
            return None
        expiry = trade_params.get("gtos_native_pending_expiry_bars")
        expiry_bars = None
        if expiry is not None:
            try:
                parsed = int(expiry)
            except (TypeError, ValueError):
                parsed = 0
            if parsed >= 1:
                expiry_bars = parsed
        self._native_pending_order = {
            "ticket": ticket,
            "order_type": trade_params.get("gtos_native_pending_order_type"),
            "price": request.get("price"),
            "expiry_bars": expiry_bars,
            "placed_time": datetime.now(timezone.utc).isoformat(),
            "bars_elapsed": 0,
            "last_bar_time": None,
            "symbol": self.symbol,
            "comment": request.get("comment"),
            "allocation_cash_usd": trade_params.get("allocation_cash_usd"),
            "min_lot_risk_usd": trade_params.get("min_lot_risk_usd"),
            "sleeve": trade_params.get("sleeve"),
        }
        self._known_tickets.add(ticket)
        logger.info(
            "Native pending parked: %s %s ticket=%s limit=%s expiry_bars=%s",
            trade_params.get("gtos_native_pending_order_type"),
            self.symbol,
            ticket,
            request.get("price"),
            expiry_bars,
        )
        return NativePendingPlacement(ticket=ticket)

    def cancel_native_pending_order(self, reason: str = "manual") -> dict:
        """Cancel a resting native pending via TRADE_ACTION_REMOVE. No-op when none."""
        pending = self._native_pending_order
        if pending is None:
            return {"cancelled": False, "reason": "no_native_pending"}
        ticket = int(pending.get("ticket") or 0)
        if ticket <= 0:
            self._native_pending_order = None
            return {"cancelled": False, "reason": "native_pending_no_ticket"}
        request = {"action": TRADE_ACTION_REMOVE, "order": ticket}
        result = self.safe_place_order(request)
        if result is not None and getattr(result, "success", False):
            self._native_pending_order = None
            logger.info(
                "Native pending cancelled (%s): ticket=%s symbol=%s",
                reason, ticket, self.symbol,
            )
            return {"cancelled": True, "reason": reason, "ticket": ticket}
        fail = getattr(result, "comment", None) if result is not None else "timeout_no_result"
        return {
            "cancelled": False,
            "reason": f"remove_failed:{fail}",
            "ticket": ticket,
        }

    def expire_native_pending_if_due(
        self,
        *,
        now_utc: Optional[datetime] = None,
        current_bar_time=None,
        bar_minutes: float = 15.0,
    ) -> Optional[dict]:
        """Cancel the resting native pending when expiry_bars have elapsed.

        No-op when there is no native pending or expiry_bars is None (live default).
        Prefers a bar-time clock; falls back to ``expiry_bars * bar_minutes``.
        """
        pending = self._native_pending_order
        if pending is None:
            return None
        expiry = pending.get("expiry_bars")
        if expiry is None:
            return None
        try:
            expiry_bars = int(expiry)
        except (TypeError, ValueError):
            return None
        if expiry_bars < 1:
            return None
        if current_bar_time is not None:
            last = pending.get("last_bar_time")
            if last is None:
                pending["last_bar_time"] = current_bar_time
            elif current_bar_time != last:
                pending["bars_elapsed"] = int(pending.get("bars_elapsed") or 0) + 1
                pending["last_bar_time"] = current_bar_time
        elif now_utc is not None:
            placed_raw = pending.get("placed_time")
            try:
                placed = datetime.fromisoformat(str(placed_raw).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return None
            if placed.tzinfo is None:
                placed = placed.replace(tzinfo=timezone.utc)
            now = now_utc if now_utc.tzinfo else now_utc.replace(tzinfo=timezone.utc)
            elapsed_min = max(0.0, (now - placed.astimezone(timezone.utc)).total_seconds() / 60.0)
            pending["bars_elapsed"] = int(elapsed_min // float(bar_minutes or 15.0))
        if int(pending.get("bars_elapsed") or 0) >= expiry_bars:
            return self.cancel_native_pending_order(reason="expiry_bars")
        return None

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

    @staticmethod
    def optional_send_request(
        request,
        *,
        deviation_points=None,
        expiry_score=None,
        timeout_score=None,
        adopt_wait_s=None,
        now_s=None,
    ):
        """Positive scores set the field. None omits it. Zero is not written.

        The returned request is never None. Timeout and adopt wait are send
        arguments, present only when the score is positive.
        """
        built = dict(request)
        if deviation_points is not None and deviation_points > 0:
            built["deviation"] = int(deviation_points)
        else:
            built.pop("deviation", None)
        if expiry_score is not None and expiry_score > 0:
            built["type_time"] = 1
            stamp = time.time() if now_s is None else float(now_s)
            built["expiration"] = int(stamp + float(expiry_score))
        else:
            built.pop("expiration", None)
        send = {}
        if timeout_score is not None and timeout_score > 0:
            send["timeout_seconds"] = float(timeout_score)
        if adopt_wait_s is not None and adopt_wait_s > 0:
            send["adopt_wait_s"] = float(adopt_wait_s)
        return built, send

    def safe_place_order(
        self,
        request: dict,
        timeout_seconds: float | None = None,
        adopt_wait_s: float | None = None,
    ) -> Optional[OrderResult]:
        """THE MOST IMPORTANT SAFETY FUNCTION.

        1. Write checkpoint
        2. Send order with timeout
        3. If timeout: check positions, adopt if filled, give up if not
        4. NEVER retry without checking positions first
        5. Clear checkpoint on completion

        On Challenge an empty wait leaves the timeout unset and the send
        continues. It does not restore ten seconds and it does not write 0.
        The activation token stays.
        """
        if self._challenge_book() and timeout_seconds is None:
            pass
        elif timeout_seconds is None:
            timeout_seconds = 10
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
            extra: dict | None = None,
        ) -> None:
            raw_mt5 = getattr(self.mt5, "_mt5", None)
            last_error_fn = getattr(raw_mt5, "last_error", None)
            last_error = None
            if callable(last_error_fn):
                try:
                    last_error = last_error_fn()
                except Exception as exc:  # noqa: BLE001
                    last_error = f"last_error_failed:{exc}"
            diagnostic = {
                "diagnostic_version": "vnext_order_send_diagnostic_v1",
                "time": datetime.now(timezone.utc).isoformat(),
                "symbol": self.symbol,
                "ns": getattr(self, "_runtime_namespace", None),
                "news_pre_send": getattr(self, "_last_news_pre_send", None),
                "status": status,
                "request": dict(request),
                "result": self._result_snapshot(result),
                "mt5_last_error": last_error,
                "positions_after": self._positions_snapshot(),
                "symbol_info": self._symbol_info_snapshot(),
                "tick": self._tick_snapshot(),
                "error": error,
            }
            if extra:
                for key, value in extra.items():
                    if key not in diagnostic:
                        diagnostic[key] = value
            self._last_order_send_diagnostic = diagnostic

        self._last_news_pre_send = None
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                def _news_checked_send():
                    from src.components.ultimate_book.news_protocol_runtime_v3 import current_event_decision, is_f5_new_risk_request
                    if is_f5_new_risk_request(request):
                        news = current_event_decision(Path(__file__).resolve().parents[2], request.get("symbol"),
                                                      prior=getattr(self, "_news_pre_send_context", None))
                        context = getattr(self, "_news_pre_send_context", None) or {}
                        news["news_t60_request_keys"] = context.get("news_t60_request_keys")
                        require_limit = bool(context.get("news_t60_require_native_limit"))
                        native_limit = bool(request.get("action") == 5 and request.get("type") in (2, 3))
                        from src.judgment.place_path_choice import decide_place_path
                        decided = decide_place_path(
                            symbol=request.get("symbol"),
                            exclusions_present=bool(news.get("exclusions_present") or news.get("active_exclusions")),
                            exclusion_count=len(news.get("active_exclusions") or []) if isinstance(news.get("active_exclusions"), (list, tuple)) else 0,
                            snapshot_drift=bool(news.get("snapshot_drift")),
                            registry_read_error=bool(news.get("error")),
                            require_native_limit=require_limit,
                            native_limit=native_limit,
                            include_chase=True,
                        )
                        news["place_path"] = decided.get("sides")
                        news["send"] = False
                        self._last_news_pre_send = news
                        gate = getattr(self, "_jev_place_gate", None) or {}
                        place_ok = gate.get("unique_highest") is True and str(gate.get("choice") or "").upper() == "PLACE"
                        if not place_ok or not decided.get("continues"):
                            reason = decided.get("reason") or "no_decision:place_path"
                            if not place_ok:
                                reason = "place_choice:" + str(gate.get("choice") or "no_choice")
                            self._last_open_trade_block_reason = reason
                            return OrderResult(retcode=10027, order=0, volume=float(request.get("volume") or 0),
                                               price=float(request.get("price") or 0),
                                               comment=str(reason) + "_no_order_send")
                        news["send"] = True
                        self._last_news_pre_send = news
                    return self.mt5.order_send(request)
                future = executor.submit(_news_checked_send)
                try:
                    result = future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError:
                    logger.warning(f"Order timeout after {timeout_seconds}s -- checking positions")
                    if self._challenge_book():
                        if (
                            isinstance(adopt_wait_s, (int, float))
                            and not isinstance(adopt_wait_s, bool)
                            and adopt_wait_s > 0
                        ):
                            time.sleep(float(adopt_wait_s))
                    else:
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
                        timeout_status = "timeout_no_position"
                        if self._challenge_book():
                            label_row = self._exec_row(
                                "timeout_label",
                                reason="safe_place_order",
                                facts={
                                    "waited_s": timeout_seconds,
                                    "symbol": self.symbol,
                                    "comment": request.get("comment"),
                                    "positions_matched": 0,
                                },
                            )
                            label = self._row_choice(label_row)
                            timeout_status = (
                                label
                                if label in ("timeout_no_position", "order_send_exception")
                                else "exec_timeout:no_decision"
                            )
                        _record_order_send_diagnostic(
                            result=None,
                            status=timeout_status,
                        )
                        return None
        except ActivationTokenError as e:
            # NOT a broker hiccup. `order_send_exception` is on book_owner's
            # transient list, so an activation refusal was retried with the
            # identical doomed request every tick, forever, reported as a
            # transient IPC problem. The refusal is deterministic: the same
            # request will be refused again until a token is minted or the
            # request changes. Give it its own terminal status so the retry
            # loop stops and the reason reaches the operator (B104).
            decision = getattr(e, "decision", None)
            logger.error(
                "Order REFUSED by the activation gate (not a broker error): %s "
                "[classification=%s positions_verified=%s]. This will not succeed on retry.",
                getattr(decision, "reason", e),
                getattr(decision, "classification", ""),
                getattr(decision, "positions_verified", None),
            )
            self._clear_checkpoint()
            extra = {}
            if decision is not None:
                extra["activation_decision_reason"] = getattr(decision, "reason", None)
                extra["activation_decision_detail"] = getattr(decision, "detail", None)
                extra["activation_decision_classification"] = getattr(
                    decision, "classification", None
                )
            _record_order_send_diagnostic(
                result=None,
                status="activation_refused",
                error=str(e),
                extra=extra,
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
            self._known_tickets.add(result.order)

        _record_order_send_diagnostic(
            result=result,
            status=("place_path_no_order_send" if (getattr(self, "_last_news_pre_send", None) or {}).get("send") is False
                    else "success" if result.success else "retcode_failure"),
        )
        self._clear_checkpoint()
        return result

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
            close_deal_status = None
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
            try:
                from src.components.ultimate_book.minimal_size import (
                    f5_close_send_none_should_defer_disk_closed,
                )
            except Exception:
                f5_close_send_none_should_defer_disk_closed = None
            if close_deal_status != "CLOSE_DEAL_FOUND" and callable(f5_close_send_none_should_defer_disk_closed) and (
                f5_close_send_none_should_defer_disk_closed(trade.ticket)
            ):
                logger.warning(
                    "Position %d absent after order_send None/10011; deferring "
                    "disk closed until positions_get sit confirms (no flatten)",
                    trade.ticket,
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

        # Check TP1
        # F5/W7 book-native + live broker authority: broker TP/SL + economic BE own the exit.
        # Challenge: the partial Choice is that decision. The price test stays a fact.
        if self._challenge_book():
            if not trade.tp1_hit and float(trade.take_profit_1 or 0.0) > 0.0:
                tp1_hit = (
                    (trade.direction == "LONG" and current_price >= trade.take_profit_1)
                    or (trade.direction == "SHORT" and current_price <= trade.take_profit_1)
                )
                if tp1_hit:
                    partial_choice = self._exec_choice(
                        "partial",
                        reason="tp1",
                        ticket=trade.ticket,
                        proposed=trade.take_profit_1,
                        facts={
                            "direction": trade.direction,
                            "current_price": current_price,
                            "volume": trade.current_volume,
                        },
                    )
                    if partial_choice == "partial":
                        return self._execute_tp1_partial(
                            trade, our_position, choice_authorized=True
                        )
            if trade.tp1_hit and not trade.tp2_hit and float(trade.take_profit_2 or 0.0) > 0:
                tp2_hit = (
                    (trade.direction == "LONG" and current_price >= trade.take_profit_2)
                    or (trade.direction == "SHORT" and current_price <= trade.take_profit_2)
                )
                if tp2_hit:
                    partial_choice = self._exec_choice(
                        "partial",
                        reason="tp2",
                        ticket=trade.ticket,
                        proposed=trade.take_profit_2,
                        facts={
                            "direction": trade.direction,
                            "current_price": current_price,
                            "volume": trade.current_volume,
                        },
                    )
                    if partial_choice == "partial":
                        return self._execute_tp2_partial(
                            trade, our_position, choice_authorized=True
                        )
        else:
            if (
                not trade.tp1_hit
                and float(trade.take_profit_1 or 0.0) > 0.0
                and not self._software_tp1_forbidden(trade, our_position)
            ):
                tp1_hit = ((trade.direction == "LONG" and current_price >= trade.take_profit_1) or
                           (trade.direction == "SHORT" and current_price <= trade.take_profit_1))
                if tp1_hit:
                    return self._execute_tp1_partial(trade, our_position)

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
        close_deal_accounting = self._lookup_close_deal_accounting(
            trade=trade,
            result=result,
            close_ticket=close_ticket,
        )
        close_deal_ticket = self._positive_int_or_none(
            close_deal_accounting.get("deal_ticket")
        ) or mt5_deal_id
        return {
            "position_ticket": ticket,
            "close_reason": close_reason,
            "close_event_type": close_event_type,
            "mt5_order_id": getattr(result, "order", None),
            "mt5_deal_id": close_deal_ticket,
            "raw_mt5_deal_id": getattr(result, "deal", None),
            "commission": close_deal_accounting.get("commission"),
            "swap": close_deal_accounting.get("swap"),
            "broker_profit": close_deal_accounting.get("broker_profit"),
            "account_history_lookup_status": close_deal_accounting.get(
                "account_history_lookup_status"
            ),
            "account_history_lookup_attempted": close_deal_accounting.get(
                "account_history_lookup_attempted"
            ),
            "account_history_lookup_attempt_count": close_deal_accounting.get(
                "account_history_lookup_attempt_count"
            ),
            "account_history_lookup_match_keys": close_deal_accounting.get(
                "account_history_lookup_match_keys"
            ),
            "broker_fill_time_utc": close_deal_accounting.get("broker_fill_time_utc"),
            "broker_close_price": close_deal_accounting.get("broker_close_price"),
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
        try:
            record_close_slippage(
                ticket=close_ticket if close_ticket is not None else trade.ticket,
                symbol=self._persist_symbol,
                direction=trade.direction,
                requested_price=expected_close_price,
                fill_price=close_price,
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
                mt5_order_id=metadata.get("mt5_order_id"),
                mt5_deal_id=metadata.get("mt5_deal_id"),
                commission=metadata.get("commission"),
                swap=metadata.get("swap"),
                broker_profit=metadata.get("broker_profit"),
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
                close_time=metadata.get("broker_fill_time_utc"),
                accounting_source=(
                    "MT5_HISTORY_DEALS_READONLY"
                    if metadata.get("account_history_lookup_status")
                    == "RECONCILED_FROM_ACCOUNT_HISTORY"
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
        trail_gap = self._safe_float(trade.gtos_vnext_dynamic_trail_gap_r)
        if trail_gap is None:
            trail_gap = self._spine_score(
                "trail_gap_r",
                "The score you return is the trail gap on this ticket. An empty score leaves it unset. Do not send.",
                {"ticket": getattr(trade, "ticket", None)},
                trade=trade,
            )
        if trail_gap is None:
            return None
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
        trail_gap = self._safe_float(trade.gtos_vnext_dynamic_trail_gap_r)
        if trail_gap is None:
            trail_gap = self._spine_score(
                "trail_gap_r",
                "The score you return is the trail gap on this ticket. An empty score leaves it unset. Do not send.",
                {"ticket": getattr(trade, "ticket", None)},
                trade=trade,
            )
        if trail_gap is None:
            return None
        desired_stop_r = max(0.0, progress_r - trail_gap)
        if self._challenge_book():
            trail_choice = self._exec_choice(
                "trail",
                reason="trailing_runner",
                ticket=trade.ticket,
                proposed=desired_stop_r,
                facts={
                    "progress_r": progress_r,
                    "trail_stop_r": trade.gtos_vnext_dynamic_trail_stop_r,
                    "trail_gap_r": trail_gap,
                },
            )
            if trail_choice != "trail":
                return None
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
        pullback_r = self._safe_float(trade.gtos_vnext_dynamic_momentum_pullback_r)
        if pullback_r is None:
            pullback_r = self._spine_score(
                "pullback_r",
                "The score you return is the pullback on this ticket. An empty score leaves it unset. Do not send.",
                {
                    "ticket": getattr(trade, "ticket", None),
                    "progress_r": progress_r,
                    "mfe_r": getattr(trade, "gtos_vnext_dynamic_mfe_r", None),
                },
                trade=trade,
            )
        if pullback_r is None:
            return None
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

    @staticmethod
    def _profit_harvest_pretrade_total_cost_r(trade: TradeState) -> Optional[float]:
        model = trade.gtos_vnext_pretrade_cost_model
        if not isinstance(model, dict):
            return None
        for key in (
            "total_cost_r",
            "expected_total_cost_r",
            "broker_calibrated_total_cost_r",
            "selected_cell_total_cost_r",
            "candidate_cost_r",
        ):
            value = model.get(key)
            try:
                if value is not None:
                    return abs(float(value))
            except (TypeError, ValueError):
                continue
        components = model.get("total_cost_components")
        if isinstance(components, dict):
            total = 0.0
            found = False
            for key in (
                "spread_cost_r",
                "expected_slippage_r",
                "swap_cost_r",
                "commission_cost_r",
            ):
                try:
                    value = components.get(key)
                    if value is not None:
                        total += abs(float(value))
                        found = True
                except (TypeError, ValueError):
                    continue
            if found:
                return total
        return None

    @staticmethod
    def _profit_harvest_clamp_fraction(value: float) -> float:
        return min(1.0, max(0.0, float(value)))

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
        min_mfe_r = self._safe_float(trade.gtos_vnext_profit_harvest_min_mfe_r)
        if min_mfe_r is None:
            min_mfe_r = self._spine_score(
                "profit_harvest_min_mfe_r",
                "The score you return is the minimum favorable excursion for this harvest. "
                "An empty score leaves it unset. Do not send.",
                {
                    "ticket": getattr(trade, "ticket", None),
                    "progress_r": progress_r,
                    "mfe_r": mfe_r,
                },
                trade=trade,
            )
        if min_mfe_r is None:
            return None
        stop_activation_mfe_r = max(
            min_mfe_r,
            float(trade.gtos_vnext_profit_harvest_stop_activation_mfe_r or min_mfe_r),
        )
        target_activation_fraction = self._profit_harvest_clamp_fraction(
            trade.gtos_vnext_profit_harvest_target_activation_fraction or 0.0
        )
        final_target_r = max(0.0, float(trade.gtos_vnext_dynamic_final_target_r or 0.0))
        target_activation_mfe_r = (
            final_target_r * target_activation_fraction
            if final_target_r > 0.0 and target_activation_fraction > 0.0
            else 0.0
        )
        trail_activation_mfe_r = max(stop_activation_mfe_r, target_activation_mfe_r)
        if (
            primary_trigger_r > 0
            and progress_r >= primary_trigger_r
            and str(trade.gtos_vnext_dynamic_policy_selected or "").strip().lower()
            in SUPPORTED_VNEXT_DYNAMIC_EXECUTION_POLICIES
        ):
            return None
        if mfe_r < min_mfe_r:
            return None

        trail_gap_r = self._safe_float(trade.gtos_vnext_profit_harvest_trail_gap_r)
        if trail_gap_r is None:
            trail_gap_r = self._spine_score(
                "profit_harvest_trail_gap_r",
                "The score you return is the harvest trail gap. An empty score leaves it unset. Do not send.",
                {
                    "ticket": getattr(trade, "ticket", None),
                    "progress_r": progress_r,
                    "mfe_r": mfe_r,
                },
                trade=trade,
            )
        if trail_gap_r is None:
            return None
        protect_floor_r = max(
            0.0,
            float(trade.gtos_vnext_profit_harvest_protect_floor_r or 0.0),
        )
        expected_cost_r = self._profit_harvest_pretrade_total_cost_r(trade)
        if trade.gtos_vnext_profit_harvest_cost_aware_protect_floor_enabled:
            cost_margin_r = max(
                0.0,
                float(trade.gtos_vnext_profit_harvest_cost_aware_margin_r or 0.0),
            )
            if expected_cost_r is not None:
                protect_floor_r = max(protect_floor_r, expected_cost_r + cost_margin_r)

        if not trade.gtos_vnext_profit_harvest_triggered:
            trade.gtos_vnext_profit_harvest_triggered = True
            trade.partial_close_events.append({
                "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_ARMED",
                "time": datetime.now(timezone.utc).isoformat(),
                "mfe_r": mfe_r,
                "current_progress_r": progress_r,
                "min_mfe_r": min_mfe_r,
                "stop_activation_mfe_r": stop_activation_mfe_r,
                "target_activation_fraction": target_activation_fraction,
                "target_activation_mfe_r": target_activation_mfe_r,
                "trail_activation_mfe_r": trail_activation_mfe_r,
                "protect_floor_r": protect_floor_r,
                "expected_cost_r": expected_cost_r,
                "primary_trigger_r": primary_trigger_r,
                "policy": trade.gtos_vnext_dynamic_policy_selected,
                "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                "result_use_status": "runtime_management_event_not_counterfactual_pnl",
            })

        if (
            not trade.gtos_vnext_profit_harvest_stop_activation_confirmed
            and mfe_r >= stop_activation_mfe_r
        ):
            trade.gtos_vnext_profit_harvest_stop_activation_confirmed = True
            trade.partial_close_events.append({
                "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_STOP_ACTIVATION_CONFIRMED",
                "time": datetime.now(timezone.utc).isoformat(),
                "mfe_r": mfe_r,
                "current_progress_r": progress_r,
                "stop_activation_mfe_r": stop_activation_mfe_r,
                "policy": trade.gtos_vnext_dynamic_policy_selected,
                "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                "result_use_status": "runtime_management_event_not_counterfactual_pnl",
            })
        if not trade.gtos_vnext_profit_harvest_stop_activation_confirmed:
            return None

        giveback_r = mfe_r - progress_r
        close_on_giveback_r = self._safe_float(trade.gtos_vnext_profit_harvest_close_on_giveback_r)
        if close_on_giveback_r is None:
            close_on_giveback_r = self._spine_score(
                "profit_harvest_giveback_r",
                "The score you return is the giveback that closes this harvest. "
                "An empty score leaves it unset. Do not send.",
                {
                    "ticket": getattr(trade, "ticket", None),
                    "progress_r": progress_r,
                    "mfe_r": mfe_r,
                    "giveback_r": giveback_r,
                },
                trade=trade,
            )
        if close_on_giveback_r is None:
            return None
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

        age_minutes = self._time_in_trade_minutes(trade.entry_time)
        armed_stale_minutes = trade.gtos_vnext_profit_harvest_armed_stale_minutes
        if (
            trade.gtos_vnext_profit_harvest_armed_stale_close_enabled
            and armed_stale_minutes is not None
        ):
            armed_stale_min_mfe_r = max(
                0.01,
                float(
                    trade.gtos_vnext_profit_harvest_armed_stale_min_mfe_r
                    or min_mfe_r
                ),
            )
            armed_stale_close_below_r = float(
                trade.gtos_vnext_profit_harvest_armed_stale_close_below_r or 0.0
            )
            if (
                age_minutes is not None
                and age_minutes >= int(armed_stale_minutes)
                and mfe_r >= armed_stale_min_mfe_r
                and progress_r <= armed_stale_close_below_r
            ):
                protected = (
                    trade.gtos_vnext_dynamic_trail_stop_r >= protect_floor_r - 1e-9
                    or (protect_floor_r <= 1e-9 and trade.sl_at_breakeven)
                )
                if not protected:
                    trade.gtos_vnext_profit_harvest_armed_stale_deferred_until_protected = True
                else:
                    trade.partial_close_events.append({
                        "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_ARMED_STALE_CLOSE_SIGNAL",
                        "time": datetime.now(timezone.utc).isoformat(),
                        "mfe_r": mfe_r,
                        "current_progress_r": progress_r,
                        "age_minutes": age_minutes,
                        "armed_stale_minutes": armed_stale_minutes,
                        "armed_stale_min_mfe_r": armed_stale_min_mfe_r,
                        "armed_stale_close_below_r": armed_stale_close_below_r,
                        "policy": trade.gtos_vnext_dynamic_policy_selected,
                        "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                        "result_use_status": "runtime_management_event_not_counterfactual_pnl",
                    })
                    if self.close_position(
                        "vnext_profit_harvest_mfe_capture_v4_armed_stale"
                    ):
                        trade.gtos_vnext_profit_harvest_last_action = "armed_stale_close"
                        return "vnext_profit_harvest_mfe_capture_v4_armed_stale_close"
                    trade.gtos_vnext_profit_harvest_last_action = (
                        "armed_stale_close_failed"
                    )
                    return "vnext_profit_harvest_mfe_capture_v4_armed_stale_close_failed"

        stale_minutes = trade.gtos_vnext_profit_harvest_stale_minutes
        if stale_minutes is not None:
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

        if age_minutes is not None:
            min_hold_minutes = max(
                0.0,
                float(
                    trade.gtos_vnext_profit_harvest_min_hold_minutes_before_stop_raise
                    or 0.0
                ),
            )
            if age_minutes < min_hold_minutes:
                trade.gtos_vnext_profit_harvest_last_action = (
                    "stop_raise_deferred_min_hold"
                )
                trade.partial_close_events.append({
                    "type": "VNEXT_PROFIT_HARVEST_MFE_CAPTURE_V4_STOP_RAISE_DEFERRED_MIN_HOLD",
                    "time": datetime.now(timezone.utc).isoformat(),
                    "mfe_r": mfe_r,
                    "current_progress_r": progress_r,
                    "age_minutes": age_minutes,
                    "min_hold_minutes_before_stop_raise": min_hold_minutes,
                    "policy": trade.gtos_vnext_dynamic_policy_selected,
                    "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                    "result_use_status": "runtime_management_event_not_counterfactual_pnl",
                })
                return None

        if mfe_r < trail_activation_mfe_r:
            desired_stop_r = protect_floor_r
        else:
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
                    "expected_cost_r": expected_cost_r,
                    "stop_activation_mfe_r": stop_activation_mfe_r,
                    "target_activation_fraction": target_activation_fraction,
                    "target_activation_mfe_r": target_activation_mfe_r,
                    "trail_activation_mfe_r": trail_activation_mfe_r,
                    "policy": trade.gtos_vnext_dynamic_policy_selected,
                    "execution_policy_id": trade.gtos_vnext_execution_policy_id,
                    "result_use_status": "runtime_management_event_not_counterfactual_pnl",
                })
                return "vnext_profit_harvest_mfe_capture_v4_sl_modified"
            trade.gtos_vnext_profit_harvest_last_action = "trail_or_protect_failed"
            return "vnext_profit_harvest_mfe_capture_v4_sl_modify_failed"
        return None

    def _software_tp1_forbidden(self, trade: TradeState, position: PositionInfo | None = None) -> bool:
        """F5/W7 book-native / live-broker-authority tickets never take a software TP1 close."""
        if bool(getattr(trade, "gtos_vnext_book_native_exit_management", False)):
            return True
        rt = self.config.get("gtos_vnext_runtime", self.config) or {}
        raw = rt.get("ultimate_book_live_broker_authority", False)
        if isinstance(raw, str):
            live_auth = raw.strip().lower() in {"1", "true", "yes", "on"}
        else:
            live_auth = bool(raw)
        if live_auth:
            return True
        tid = str(getattr(trade, "trade_id", "") or "")
        if not tid.startswith("adopted_"):
            return False
        comment = ""
        if position is not None:
            comment = str(getattr(position, "comment", "") or "")
        if not comment:
            comment = str(getattr(trade, "comment", "") or "")
        if comment.startswith("F5:") or comment.startswith(COMMENT_PREFIX_F5_MINIMAL):
            return True
        try:
            if int(self._magic) == int(MAGIC_F5_MINIMAL):
                return True
        except (TypeError, ValueError):
            pass
        ns = str(getattr(self, "_runtime_namespace", "") or "")
        if ns == "operator":
            return True
        ck = str(getattr(self, "_checkpoint_path", "") or "").replace("\\", "/")
        if "operator" in ck:
            return True
        return False

    def _execute_tp1_partial(
        self,
        trade: TradeState,
        position: PositionInfo,
        *,
        choice_authorized: bool = False,
    ) -> str:
        """TP1 hit: close position based on tp1_close_pct config.

        Phase 1 validated: 100% close at TP1 is optimal (+0.503R exp, p=0.014).
        Partial close logic preserved behind config gate for future use.

        CRITICAL: Partial close changes the ticket number on MT5.
        """
        if not choice_authorized and self._software_tp1_forbidden(trade, position):
            logger.info(
                "skip TP1_full: broker owns exit ticket=%s trade_id=%s book_native=%s",
                getattr(trade, "ticket", None),
                getattr(trade, "trade_id", None),
                getattr(trade, "gtos_vnext_book_native_exit_management", False),
            )
            return "tp1_skipped_broker_owns_exit"
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
            close_fraction = self._safe_float(
                self._configured_vnext_partial_be_runner_params(trade).get("partial_close_ratio")
            )
            if close_fraction is None or not (0 < close_fraction < 1):
                return "tp1_partial_unset"
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
                "magic": self._magic,
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
            our_positions = [p for p in positions if p.magic == self._magic]
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
                "magic": self._magic,
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
                "magic": self._magic,
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
            our_positions = [p for p in positions if p.magic == self._magic]

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
            "magic": self._magic,
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

    def _execute_tp2_partial(
        self,
        trade: TradeState,
        position: PositionInfo,
        *,
        choice_authorized: bool = False,
    ) -> str:
        """TP2 hit: close 25% of initial, trail SL to TP1."""
        if self._challenge_book() and not choice_authorized:
            return "tp2_skipped_choice"
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
                "magic": self._magic,
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
                "magic": self._magic,
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
                "magic": self._magic,
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

        tp2_fraction = self._spine_score(
            "tp2_close_fraction",
            "The score you return is the second partial fraction of this ticket. "
            "An empty score leaves the partial unset. Do not send.",
            {
                "ticket": getattr(trade, "ticket", None),
                "current_volume": getattr(trade, "current_volume", None),
                "initial_volume": getattr(trade, "initial_volume", None),
            },
            trade=trade,
        )
        if tp2_fraction is None or not (0 < tp2_fraction < 1):
            return None
        close_volume = round(trade.initial_volume * tp2_fraction, 2)
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
            "magic": self._magic,
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
        our_positions = [p for p in positions if p.magic == self._magic]

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

    def _close_ticket_broker_sit(self, ticket: int) -> str:
        """Read-only sit for a close: ``present``, ``absent``, or ``unavailable``.

        Prefer ``positions_for_activation``: it raises on a failed positions_get
        instead of masking None as []. A failed sit is unknown, not a flatten
        and not a disk closed stamp.
        """
        provider = getattr(self.mt5, "positions_for_activation", None)
        if callable(provider):
            try:
                positions = provider()
            except Exception:
                return "unavailable"
            if positions is None:
                return "unavailable"
            for position in positions:
                try:
                    if int(getattr(position, "ticket", 0) or 0) == int(ticket):
                        return "present"
                except (TypeError, ValueError):
                    continue
            return "absent"
        try:
            positions = self.mt5.get_positions(self.symbol)
        except Exception:
            return "unavailable"
        if positions is None:
            return "unavailable"
        for position in positions:
            try:
                if int(getattr(position, "ticket", 0) or 0) == int(ticket):
                    return "present"
            except (TypeError, ValueError):
                continue
        return "absent"

    def close_position(self, reason: str = "manual") -> bool:
        """Close entire remaining position."""
        if self.active_trade is None:
            return False

        trade = self.active_trade
        ticket = getattr(trade, "ticket", None)
        try:
            from src.components.ultimate_book.minimal_size import (
                f5_close_send_none_allow_order_send,
                f5_close_send_none_clear,
                f5_close_send_none_mark_absent,
                f5_close_send_none_note_none,
                f5_close_send_none_note_present,
                f5_close_send_none_seen,
            )
        except Exception:
            f5_close_send_none_allow_order_send = None
            f5_close_send_none_clear = None
            f5_close_send_none_mark_absent = None
            f5_close_send_none_note_none = None
            f5_close_send_none_note_present = None
            f5_close_send_none_seen = None

        if ticket not in (None, 0) and callable(f5_close_send_none_seen) and f5_close_send_none_seen(ticket):
            sit = self._close_ticket_broker_sit(int(ticket))
            if sit == "unavailable":
                logger.warning(
                    "Close send skipped ticket=%s reason=%s: broker sit unavailable "
                    "(10011/None is unknown, not a close; no disk stamp, no flatten)",
                    ticket, reason,
                )
                return False
            if sit == "absent":
                if callable(f5_close_send_none_mark_absent):
                    f5_close_send_none_mark_absent(ticket)
                logger.warning(
                    "Close send skipped ticket=%s reason=%s: positions_get sit absent "
                    "(dead ticket; disk closed waits for reconcile sit, no flatten)",
                    ticket, reason,
                )
                return False
            if callable(f5_close_send_none_note_present):
                f5_close_send_none_note_present(ticket)
        if ticket not in (None, 0) and callable(f5_close_send_none_allow_order_send):
            if not f5_close_send_none_allow_order_send(ticket):
                logger.info(
                    "Close send skipped ticket=%s reason=%s: 10011 backoff/dead cache",
                    ticket, reason,
                )
                return False

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
            "magic": self._magic,
            "deviation": close_geometry["deviation"],
            "type_filling": close_geometry["type_filling"],
            "comment": f"close_{reason}",
        }

        if not self._challenge_manage_emit(
            "close",
            ticket=trade.ticket,
            reason=reason,
            trade=trade,
        ):
            return False

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
            if ticket not in (None, 0) and callable(f5_close_send_none_clear):
                f5_close_send_none_clear(ticket)
            self._notify_close_if_unsent(_closed_trade, reason, close_price)
            return True

        if is_order_send_none(result):
            if ticket not in (None, 0) and callable(f5_close_send_none_note_none):
                state = f5_close_send_none_note_none(ticket)
            else:
                state = {}
            logger.error(
                "Failed to close position: %s (broker unknown, not a disk closed "
                "stamp; attempts=%s dead=%s; sit door is positions_get)",
                result,
                state.get("attempts"),
                state.get("dead"),
            )
            return False

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
        falls back to wall-clock so the backstop still works). NEVER raises.

        SESSION BD (B2086-B2093) -- AQ §6a's `want = budget + 64` exposure, made OBSERVABLE.

        AQ filed this and deliberately did not patch it: after the `mx_*` time-stop unit repair the
        budget is 7,680, so `want` is 7,744, and *"if the terminal returns fewer than 7,680 closed
        M15 bars the count can never reach the budget and the time stop never fires at all"* -- the
        backstop degrades to INERT rather than late, which is the wrong direction. AQ's reason for
        filing rather than fixing stands and is respected here: the obvious mitigation (return None
        on a short read) moves armed sleeves onto the over-counting wall-clock path and closes them
        EARLIER, which is a behaviour change on live money.

        SO THE DETECTION IS BUILT AND THE BEHAVIOUR CHANGE IS NOT. Two things were missing:

        1. `len(candles) < want` is NOT the test. A broker legitimately returns fewer bars than
           asked for -- a young symbol, a long holiday. The question is only ever whether the
           returned window reaches back PAST THE FILL. If the oldest closed bar printed after
           `entry_dt`, `n` is a LOWER BOUND on the elapsed count, not the count. That test is free:
           the timestamps are already parsed here.
        2. The book already asks the engine for this (`book_owner.py:2768-2772`,
           `get_time_stop_clock_diagnostic` then `_last_time_stop_clock_diagnostic`) and **no engine
           in this repository defines either name**, so `policy_clock` is None on every tick of this
           lineage and the inertness is invisible. This method is now that missing producer.

        Nothing armed is exposed today -- the three live sleeves are H4 at 1280 and want 1344 -- and
        the F15 host probe measured 7,800 available on both terminals. That clears 7,744 by **56
        bars**, which is 0.72 % of headroom on a terminal setting a future session can change
        without knowing this exists. That thin margin is the reason the diagnostic ships now.
        """
        want = max(96, int(budget) + 64)            # a little past the budget (+ the forming bar)
        diagnostic = {
            "schema_version": "gtos.vnext.time_stop_clock_diagnostic.v1",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "symbol": self.symbol,
            "time_stop_bars": int(budget),
            "bars_requested": want,
        }
        try:
            candles = self.mt5.get_candles(self.symbol, 15, want)
            if not candles or len(candles) < 2:
                diagnostic.update(
                    status="feed_unreadable",
                    coverage_status="feed_unreadable",
                    bars_returned=len(candles) if candles else 0,
                    count_is_lower_bound=None,
                )
                self._last_time_stop_clock_diagnostic = diagnostic
                return None
            n = 0
            oldest_closed = None
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
                if oldest_closed is None or tdt < oldest_closed:
                    oldest_closed = tdt
                if tdt > entry_dt:                       # bars that CLOSED after the fill (route counts j>i)
                    n += 1
            # The whole question: does the returned window reach back past the fill?
            covers_entry = oldest_closed is not None and oldest_closed <= entry_dt
            diagnostic.update(
                status="ok",
                coverage_status="covers_entry" if covers_entry else "truncated_before_entry",
                bars_returned=len(candles),
                oldest_closed_bar_utc=oldest_closed.isoformat() if oldest_closed else None,
                elapsed_m15_bars=n,
                count_is_lower_bound=not covers_entry,
                # The condition AQ named, evaluated rather than described: a truncated window whose
                # lower bound is already short of the budget is a time stop that CANNOT fire.
                time_stop_unreachable=bool(not covers_entry and n < int(budget)),
            )
            self._last_time_stop_clock_diagnostic = diagnostic
            if diagnostic["time_stop_unreachable"]:
                logger.warning(
                    "TIME STOP UNREACHABLE %s: window truncated before fill "
                    "(oldest closed bar %s > entry %s); counted %d of %d required bars from %d "
                    "returned. The backstop is INERT for this position, not late.",
                    self.symbol,
                    diagnostic.get("oldest_closed_bar_utc"),
                    entry_dt.isoformat(),
                    n,
                    int(budget),
                    len(candles),
                )
                # Default OFF. Returning None hands the caller the wall-clock fallback, which
                # OVER-counts (index CFDs ~3x, fx over weekends) and therefore closes EARLIER than
                # the validated route -- AQ's stated objection, and the reason this is a flag and
                # not a fix. Arming it trades an inert backstop for an early one; both are wrong
                # and only the owner can price which is less wrong for a given sleeve.
                if self._time_stop_wallclock_on_truncated_window():
                    diagnostic["fallback"] = "wallclock_on_truncated_window"
                    return None
            return n
        except Exception:
            diagnostic.update(status="exception", coverage_status="feed_unreadable")
            try:
                self._last_time_stop_clock_diagnostic = diagnostic
            except Exception:
                pass
            return None

    def _time_stop_wallclock_on_truncated_window(self) -> bool:
        """Default-off switch for the behaviour half of AQ §6a. Never raises."""
        try:
            rt = self.config.get("gtos_vnext_runtime", {}) or {}
            return bool(rt.get("ultimate_book_time_stop_wallclock_on_truncated_window", False))
        except Exception:  # noqa: BLE001
            return False

    def get_time_stop_clock_diagnostic(self) -> Optional[dict]:
        """The getter `book_owner.py:2768` has been calling since the packet carry landed.

        It returned None on every tick of this lineage because nothing defined it. Now the
        `policy_clock_*` fields on `position_managed` packets have a producer, and
        `coverage_status` / `time_stop_unreachable` reach the evidence log.
        """
        return getattr(self, "_last_time_stop_clock_diagnostic", None)

    def check_time_stop_and_close(self) -> Optional[str]:
        """J48 time stop: force-close at market when 12 M15 bars have elapsed
        since fill. Returns 'j46_j49_time_stop' on close, None otherwise.
        Safe to call when no active trade or J46-J49 disabled.

        Skips trades that were NOT opened under J46-J49 (orphan adoption from
        ``reconcile_on_startup``, or pre-J46-J49-flip live trades): those have
        ``j46_j49_active=False`` and their broker TPs are AI's original
        emission, not the 6R higher target — applying the time stop to them
        would close legitimate positions at market for the wrong reason."""
        if self.active_trade is None:
            return None
        if self._challenge_book():
            trade = self.active_trade
            elapsed = None
            budget = None
            entry_time_str = trade.entry_time or ""
            if entry_time_str:
                try:
                    entry_dt = datetime.fromisoformat(entry_time_str)
                    if entry_dt.tzinfo is None:
                        entry_dt = entry_dt.replace(tzinfo=timezone.utc)
                    if (
                        self._vnext_time_stop_active(trade)
                        and trade.gtos_vnext_dynamic_time_stop_bars
                    ):
                        budget = int(trade.gtos_vnext_dynamic_time_stop_bars)
                        elapsed = self._trading_m15_bars_since(entry_dt, budget)
                    elif getattr(trade, "j46_j49_active", False):
                        from src.components import j46_j49_policy
                        if j46_j49_policy.is_enabled(self.config):
                            raw_budget = j46_j49_policy.get_policy_params(self.config).get(
                                "time_stop_bars"
                            )
                            if raw_budget in (None, ""):
                                raw_budget = self._spine_score(
                                    "time_stop_bars",
                                    "The score you return is the bar budget for this open ticket. "
                                    "An empty score leaves the budget unset. Do not send.",
                                    {"source": "j46"},
                                )
                            budget = None if raw_budget in (None, "") else int(raw_budget)
                            elapsed = j46_j49_policy.bars_elapsed_since_fill(entry_dt)
                except (ValueError, TypeError):
                    elapsed = None
                    budget = None
            time_choice = self._exec_choice(
                "time_stop",
                reason="check_time_stop",
                ticket=getattr(trade, "ticket", None),
                proposed=budget,
                facts={
                    "elapsed_bars": elapsed,
                    "budget_bars": budget,
                    "entry_time": entry_time_str or None,
                    "policy": getattr(trade, "gtos_vnext_dynamic_policy_selected", None),
                    "book_native": bool(
                        getattr(trade, "gtos_vnext_book_native_exit_management", False)
                    ),
                    "direction": getattr(trade, "direction", None),
                },
            )
            if time_choice == "fire_time_stop" and self.close_position("exec_time_stop"):
                return "exec_time_stop"
            return None
        if self._vnext_time_stop_active(self.active_trade):
            time_stop = self.active_trade.gtos_vnext_dynamic_time_stop_bars
            if time_stop is None:
                return None
            entry_time_str = self.active_trade.entry_time or ""
            if not entry_time_str:
                return None
            try:
                entry_dt = datetime.fromisoformat(entry_time_str)
            except (ValueError, TypeError):
                return None
            if entry_dt.tzinfo is None:
                entry_dt = entry_dt.replace(tzinfo=timezone.utc)
            # Count TRADING M15 bars since entry (skips closed-market time), matching the validated route's
            # bar count. Fall back to wall-clock M15 only if the feed can't be read, so the backstop still
            # fires. (timestop-wallclock-vs-trading-bars: wall-clock over-counts -- index CFDs ~3x, fx_jpy
            # over weekends -- force-closing earlier than the route; the printed-bar count fixes that.)
            elapsed = self._trading_m15_bars_since(entry_dt, int(time_stop))
            elapsed_basis = "trading" if elapsed is not None else "wallclock"
            if elapsed is None:
                from src.components import j46_j49_policy
                elapsed = j46_j49_policy.bars_elapsed_since_fill(entry_dt)
            if elapsed >= int(time_stop):
                policy = str(
                    self.active_trade.gtos_vnext_dynamic_policy_selected
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
                if self.close_position(close_reason):
                    return close_reason
            return None
        if not getattr(self.active_trade, "j46_j49_active", False):
            return None
        from src.components import j46_j49_policy
        if not j46_j49_policy.is_enabled(self.config):
            return None
        params = j46_j49_policy.get_policy_params(self.config)
        raw_stop = params.get("time_stop_bars")
        if raw_stop in (None, ""):
            raw_stop = self._spine_score(
                "time_stop_bars",
                "The score you return is the bar budget for this open ticket. "
                "An empty score leaves the budget unset. Do not send.",
                {"source": "j46"},
            )
        if raw_stop in (None, ""):
            return None
        time_stop = int(raw_stop)
        entry_time_str = self.active_trade.entry_time or ""
        if not entry_time_str:
            return None
        try:
            entry_dt = datetime.fromisoformat(entry_time_str)
        except (ValueError, TypeError):
            return None
        if entry_dt.tzinfo is None:
            entry_dt = entry_dt.replace(tzinfo=timezone.utc)
        elapsed = j46_j49_policy.bars_elapsed_since_fill(entry_dt)
        if elapsed >= time_stop:
            logger.info(
                "J46-J49 time stop fired: %d M15 bars elapsed (>=%d). "
                "Closing at market.", elapsed, time_stop,
            )
            if self.close_position("j46_j49_time_stop"):
                return "j46_j49_time_stop"
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
        if self._challenge_book():
            if self.active_trade.sl_at_breakeven:
                return "trailing"
            if self.mt5.get_tick(self.symbol) is None:
                logger.warning("No tick for BE check -- skipping, will retry next candle")
                return "trailing"
            self._move_sl_to_breakeven(self.active_trade, self.active_trade.ticket)
            return "trailing"
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
                if getattr(p, "magic", self._magic) == self._magic
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
        if self._challenge_book():
            modify_choice = self._exec_choice(
                "modify",
                reason="breakeven",
                ticket=ticket,
                proposed=getattr(trade, "entry_price", None),
                facts={
                    "direction": getattr(trade, "direction", None),
                    "entry_price": getattr(trade, "entry_price", None),
                    "stop_loss": getattr(trade, "stop_loss", None),
                    "sl_at_breakeven": bool(getattr(trade, "sl_at_breakeven", False)),
                },
            )
            if modify_choice != "modify":
                return
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

    def _sltp_request_already_matches_position(
        self,
        position,
        request: dict,
        *,
        modify_kind: str,
    ) -> bool:
        tolerance = max(self._sltp_price_tick_size() / 2.0, 1e-9)
        if modify_kind == "SL":
            desired = float(request.get("sl", 0.0) or 0.0)
            actual = float(getattr(position, "sl", 0.0) or 0.0)
            return abs(actual - desired) <= tolerance
        if modify_kind == "TP":
            desired = float(request.get("tp", 0.0) or 0.0)
            actual = float(getattr(position, "tp", 0.0) or 0.0)
            return abs(actual - desired) <= tolerance
        return False



    def _challenge_book(self) -> bool:
        return str(getattr(self, "_runtime_namespace", "") or "") == "operator"

    @staticmethod
    def _anchor_number(value):
        if isinstance(value, bool) or value is None:
            return None
        if isinstance(value, (int, float)):
            number = float(value)
        else:
            try:
                number = float(value)
            except (TypeError, ValueError):
                return None
        if number != number or number in (float("inf"), float("-inf")):
            return None
        return number

    @staticmethod
    def _anchor_push(levels: list, seen: list, label: str, value) -> None:
        number = ExecutionEngine._anchor_number(value)
        text = str(label or "").strip()
        if number is None or not text or number in seen:
            return
        seen.append(number)
        levels.append((text, number))

    def _first_number(self, facts, *keys):
        if not isinstance(facts, dict):
            return None
        for key in keys:
            number = self._anchor_number(facts.get(key))
            if number is not None:
                return number
        return None

    @staticmethod
    def _attr_number(obj, *names):
        if obj is None:
            return None
        for name in names:
            number = ExecutionEngine._anchor_number(getattr(obj, name, None))
            if number is not None:
                return number
        return None

    def _bar_ohlc(self, candle):
        if not isinstance(candle, dict):
            return None
        def pick(*keys):
            for key in keys:
                number = self._anchor_number(candle.get(key))
                if number is not None:
                    return number
            return None
        high = pick("high", "h")
        low = pick("low", "l")
        if high is None or low is None or high < low:
            return None
        return pick("open", "o"), high, low, pick("close", "c")

    @staticmethod
    def _clock_stamp(value):
        if isinstance(value, datetime):
            stamp = value
        else:
            try:
                stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except (TypeError, ValueError):
                return None
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp.astimezone(timezone.utc)

    def _kill_zone_spans(self, now: datetime) -> list:
        """Length and remaining seconds of each kill zone on this book's clock."""
        cfg = self.config if isinstance(getattr(self, "config", None), dict) else {}
        zones = (cfg.get("market") or {}).get("kill_zones") or {}
        if not isinstance(zones, dict):
            return []
        now_s = now.hour * 3600 + now.minute * 60 + now.second
        day_s = 24 * 60 * 60
        found = []
        for name, data in zones.items():
            if not isinstance(data, dict):
                continue
            try:
                start_h, start_m = [int(part) for part in str(data.get("start_utc", "")).split(":")]
                end_h, end_m = [int(part) for part in str(data.get("end_utc", "")).split(":")]
            except (TypeError, ValueError):
                continue
            start = start_h * 3600 + start_m * 60
            end = end_h * 3600 + end_m * 60
            if end > start:
                length = end - start
                remaining = end - now_s if start <= now_s < end else None
            elif end < start:
                length = (day_s - start) + end
                if now_s >= start:
                    remaining = (day_s - now_s) + end
                elif now_s < end:
                    remaining = end - now_s
                else:
                    remaining = None
            else:
                continue
            found.append((str(name), float(length), None if remaining is None else float(remaining)))
        return found

    def _second_levels(self, facts, *, placed=None) -> list:
        """Seconds already fixed by this clock, this stamp, and the kill zones."""
        now = datetime.now(timezone.utc)
        levels: list = []
        seen: list = []
        stamps = []
        if placed is not None:
            stamp = self._clock_stamp(placed)
            if stamp is not None:
                stamps.append(stamp)
        if isinstance(facts, dict):
            for key in (
                "placed_time",
                "decision_time_utc",
                "pending_created_time_utc",
                "entry_time",
                "bar_time",
                "decision_bar_iso",
                "prior_bar_time",
            ):
                stamp = self._clock_stamp(facts.get(key))
                if stamp is not None:
                    stamps.append(stamp)
        unique = []
        for stamp in stamps:
            if stamp not in unique:
                unique.append(stamp)
        for stamp in unique:
            age = (now - stamp).total_seconds()
            if age > 0:
                self._anchor_push(levels, seen, "seconds since this card's stamp", age)
        if len(unique) >= 2:
            span = abs((unique[-1] - unique[0]).total_seconds())
            if span > 0:
                self._anchor_push(levels, seen, "seconds between the stamps on this card", span)
                age = (now - max(unique)).total_seconds()
                if age >= 0:
                    until = span - (age % span)
                    if until > 0:
                        self._anchor_push(levels, seen, "seconds until the next print of this span", until)
        for name, length, remaining in self._kill_zone_spans(now):
            self._anchor_push(levels, seen, "seconds in the " + name + " kill zone", length)
            if remaining is not None and remaining > 0:
                self._anchor_push(levels, seen, "seconds left in the " + name + " kill zone", remaining)
        return levels

    def _scaled_clock_levels(self, facts, *, placed=None, divisor: float, suffix: str) -> list:
        levels = []
        seen = []
        for label, value in self._second_levels(facts, placed=placed):
            self._anchor_push(levels, seen, label + suffix, value / divisor)
        return levels

    def _point_levels(self, sym_info=None) -> list:
        info = sym_info if sym_info is not None else self._mt5_symbol_info()
        levels: list = []
        seen: list = []
        if info is None:
            return levels
        self._anchor_push(levels, seen, "this symbol's spread, in points", getattr(info, "spread", None))
        self._anchor_push(levels, seen, "this symbol's stop level, in points", getattr(info, "trade_stops_level", None))
        self._anchor_push(levels, seen, "this symbol's freeze level, in points", getattr(info, "trade_freeze_level", None))
        point = self._anchor_number(getattr(info, "point", None))
        tick = self._anchor_number(getattr(info, "trade_tick_size", None))
        if point is not None and point > 0 and tick is not None and tick > 0:
            self._anchor_push(levels, seen, "this symbol's tick, in points", tick / point)
        return levels

    def _lot_levels(self, facts, sym_info=None) -> list:
        info = sym_info if sym_info is not None else self._mt5_symbol_info()
        levels: list = []
        seen: list = []
        minimum = self._first_number(facts, "volume_min")
        step = self._first_number(facts, "volume_step")
        lots = self._first_number(facts, "lots", "volume", "current_volume")
        if info is not None:
            if minimum is None:
                minimum = self._anchor_number(getattr(info, "volume_min", None))
            if step is None:
                step = self._anchor_number(getattr(info, "volume_step", None))
        self._anchor_push(levels, seen, "this symbol's minimum volume", minimum)
        self._anchor_push(levels, seen, "this symbol's volume step", step)
        self._anchor_push(levels, seen, "the volume calculated for this order", lots)
        if minimum is not None and step is not None and step > 0:
            self._anchor_push(levels, seen, "the next volume on this symbol's grid", minimum + step)
        return levels

    def _fraction_levels(self, facts, *, trade=None, candle=None, sym_info=None) -> list:
        levels: list = []
        seen: list = []
        volume = self._first_number(facts, "current_volume", "volume", "lots")
        initial = self._first_number(facts, "initial_volume")
        minimum = self._first_number(facts, "volume_min")
        step = self._first_number(facts, "volume_step")
        if trade is not None:
            if volume is None:
                volume = self._attr_number(trade, "current_volume")
            if initial is None:
                initial = self._attr_number(trade, "initial_volume")
        info = sym_info if sym_info is not None else self._mt5_symbol_info()
        if info is not None:
            if minimum is None:
                minimum = self._anchor_number(getattr(info, "volume_min", None))
            if step is None:
                step = self._anchor_number(getattr(info, "volume_step", None))
        base = volume if volume is not None and volume > 0 else initial
        if base is not None and base > 0 and minimum is not None and minimum > 0:
            self._anchor_push(levels, seen, "minimum volume over this volume", minimum / base)
        if base is not None and base > 0 and step is not None and step > 0:
            self._anchor_push(levels, seen, "volume step over this volume", step / base)
        if (
            initial is not None and initial > 0
            and volume is not None and volume > 0
        ):
            self._anchor_push(levels, seen, "current volume over the initial volume", volume / initial)
        ohlc = self._bar_ohlc(candle)
        if ohlc is not None:
            open_, high, low, close = ohlc
            span = high - low
            if span > 0 and open_ is not None and close is not None:
                body = abs(close - open_)
                self._anchor_push(levels, seen, "this bar's body over its range", body / span)
                upper = high - max(open_, close)
                lower = min(open_, close) - low
                self._anchor_push(levels, seen, "this bar's upper wick over its range", upper / span)
                self._anchor_push(levels, seen, "this bar's lower wick over its range", lower / span)
        return levels

    def _r_levels(self, facts, *, trade=None, candle=None, sym_info=None) -> list:
        """R from this stop, this spread, this bar, and this target. No planted multiple."""
        levels: list = []
        seen: list = []
        entry = self._first_number(facts, "entry_price", "entry", "limit_price")
        stop = self._first_number(facts, "stop_loss", "stop")
        target = self._first_number(facts, "take_profit", "take_profit_1", "tp")
        sl = self._first_number(facts, "sl_distance", "sizing_sl_distance")
        if trade is not None:
            if entry is None:
                entry = self._attr_number(trade, "entry_price", "limit_price")
            if stop is None:
                stop = self._attr_number(trade, "stop_loss")
            if target is None:
                target = self._attr_number(trade, "take_profit_1", "take_profit", "take_profit_2")
            if sl is None:
                sl = self._attr_number(trade, "sl_distance")
        if (sl is None or sl <= 0) and entry is not None and stop is not None:
            gap = abs(entry - stop)
            if gap > 0:
                sl = gap
        if sl is not None and sl > 0:
            info = sym_info if sym_info is not None else self._mt5_symbol_info()
            if info is not None:
                spread = self._anchor_number(getattr(info, "spread", None))
                point = self._anchor_number(getattr(info, "point", None))
                if spread is not None and point is not None and point > 0 and spread >= 0:
                    self._anchor_push(levels, seen, "this symbol's spread, in R", (spread * point) / sl)
            if entry is not None and stop is not None:
                self._anchor_push(levels, seen, "this stop, in R", abs(entry - stop) / sl)
            if entry is not None and target is not None:
                self._anchor_push(levels, seen, "this target, in R", abs(entry - target) / sl)
            ohlc = self._bar_ohlc(candle)
            if ohlc is not None:
                _open, high, low, close = ohlc
                span = high - low
                if span > 0:
                    self._anchor_push(levels, seen, "this bar's range, in R", span / sl)
                if close is not None and entry is not None:
                    self._anchor_push(levels, seen, "this bar's close from the entry, in R", abs(close - entry) / sl)
        if isinstance(facts, dict):
            for key, label in (
                ("progress_r", "this ticket's progress, in R"),
                ("mfe_r", "this ticket's favorable excursion, in R"),
                ("giveback_r", "this ticket's giveback, in R"),
                ("spread_r", "the spread in R named on this card"),
            ):
                self._anchor_push(levels, seen, label, facts.get(key))
        if trade is not None:
            self._anchor_push(
                levels, seen,
                "this ticket's favorable excursion, in R",
                getattr(trade, "gtos_vnext_dynamic_mfe_r", None),
            )
            self._anchor_push(
                levels, seen,
                "this harvest's favorable excursion, in R",
                getattr(trade, "gtos_vnext_profit_harvest_mfe_r", None),
            )
        return levels

    def _bar_count_levels(self, facts, *, trade=None) -> list:
        """Bar counts already on the card. Elapsed-since-fill is not the budget."""
        levels: list = []
        seen: list = []
        if isinstance(facts, dict):
            for key, label in (
                ("session_bars", "bars in this session on the card"),
                ("day_bars", "bars in this day on the card"),
                ("swing_bars", "bars in this swing on the card"),
                ("bars_since_high", "bars since this high"),
                ("bars_since_low", "bars since this low"),
            ):
                number = self._anchor_number(facts.get(key))
                if number is not None and number > 0:
                    self._anchor_push(levels, seen, label, number)
        if trade is not None:
            candles = self._attr_number(trade, "candles_elapsed")
            if candles is not None and candles > 0:
                self._anchor_push(levels, seen, "candles elapsed on this intent", candles)
        return levels

    @staticmethod
    def _quantity_unit(role: str) -> str:
        low = str(role or "").lower()
        if low in {"lot", "lots"} or low.endswith("_lots"):
            return "lots"
        if "deviation" in low:
            return "points"
        if low.endswith("_hours") or "max_age_hours" in low:
            return "hours"
        if "minute" in low:
            return "minutes"
        if (
            low in {"expiry", "timeout", "adopt_wait", "retry_pause"}
            or low.endswith("_seconds")
            or "expiry" in low
        ):
            return "seconds"
        if "time_stop_bars" in low or low.endswith("_bars") or low == "bar_count":
            return "bars"
        if "fraction" in low or (low.endswith("_ratio") and "reward" not in low):
            return "fraction"
        if low.endswith("_r") or "reward" in low:
            return "r"
        return ""

    def _quantity_anchors(
        self,
        role: str,
        facts,
        *,
        trade=None,
        candle=None,
        placed=None,
        sym_info=None,
    ) -> list:
        unit = self._quantity_unit(role)
        if unit == "lots":
            return self._lot_levels(facts, sym_info=sym_info)
        if unit == "points":
            return self._point_levels(sym_info)
        if unit == "seconds":
            return self._second_levels(facts, placed=placed)
        if unit == "hours":
            return self._scaled_clock_levels(facts, placed=placed, divisor=3600.0, suffix=", in hours")
        if unit == "minutes":
            return self._scaled_clock_levels(facts, placed=placed, divisor=60.0, suffix=", in minutes")
        if unit == "fraction":
            return self._fraction_levels(facts, trade=trade, candle=candle, sym_info=sym_info)
        if unit == "bars":
            return self._bar_count_levels(facts, trade=trade)
        if unit == "r":
            return self._r_levels(facts, trade=trade, candle=candle, sym_info=sym_info)
        return []

    def _spine_score(
        self,
        role: str,
        instructions: str,
        facts: dict | None = None,
        anchors=None,
        *,
        trade=None,
        candle=None,
        placed=None,
        sym_info=None,
    ):
        """Score for this role. None does not restore a constant.

        A bare Score has no levels and must not post. Anchors are the card's
        own quantities in the unit this hop uses. Fewer than two leaves the
        hop unset. An empty answer is not a send.
        """
        state = {
            "role": role,
            "symbol": getattr(self, "symbol", None),
            "namespace": getattr(self, "_runtime_namespace", None),
        }
        if isinstance(facts, dict):
            state.update(facts)
        if anchors is None:
            anchors = self._quantity_anchors(
                role,
                state,
                trade=trade,
                candle=candle,
                placed=placed,
                sym_info=sym_info,
            )
        usable = []
        seen = set()
        for item in anchors or ():
            if not isinstance(item, tuple) or len(item) != 2:
                continue
            label, value = item
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                continue
            if value != value or value in (float("inf"), float("-inf")):
                continue
            if value in seen:
                continue
            seen.add(value)
            usable.append((str(label), float(value)))
        usable.sort(key=lambda pair: pair[1])
        if len(usable) < 2:
            return None
        try:
            from src.judgment.nineteen import score
            return score(
                state,
                question_id=role,
                instructions=instructions,
                anchors=usable,
            )
        except TypeError:
            return None
        except Exception:
            return None


    def _open_trade_withholds(self, reason: str, facts: dict | None = None) -> bool:
        """True only when withhold is the unique Choice on Challenge.

        Other books keep the old return. An empty answer, a tie, or an error
        does not withhold.
        """
        if not self._challenge_book():
            return True
        choice = self._exec_choice(
            "gate",
            reason=str(reason),
            facts=dict(facts or {}),
        )
        return choice == "withhold"

    def _stop_or_mark(self, reason, facts: dict | None = None) -> bool:
        """True when this fact stops the order.

        On Challenge, withhold keeps the old reason. fact is the only
        release. An empty answer, a tie, or an error does not send and
        does not restore the old reason.
        """
        if not self._challenge_book():
            self._last_open_trade_block_reason = reason
            return True
        payload = {"symbol": getattr(self, "symbol", None)}
        if isinstance(facts, dict):
            payload.update(facts)
        choice = self._exec_choice("gate", reason=str(reason), facts=payload)
        if choice == "withhold":
            self._last_open_trade_block_reason = reason
            return True
        if choice == "fact":
            return False
        self._last_open_trade_block_reason = "exec_gate:" + (choice or "no_decision")
        return True

    def _exec_row(
        self,
        question: str,
        *,
        reason: str = "",
        ticket=None,
        proposed=None,
        facts: dict | None = None,
    ) -> dict:
        """Challenge execution row. Empty when there is no unique winner."""
        if not self._challenge_book():
            return {}
        try:
            from src.judgment.execution_choices import choose
            row = choose(
                question,
                ticket=ticket,
                symbol=getattr(self, "symbol", None),
                reason=reason,
                proposed=proposed,
                facts=facts,
            )
        except Exception:
            logger.warning("Challenge execution choice did not answer question=%s", question)
            return {}
        return row if isinstance(row, dict) else {}

    def _exec_choice(
        self,
        question: str,
        *,
        reason: str = "",
        ticket=None,
        proposed=None,
        facts: dict | None = None,
    ) -> str | None:
        """Challenge execution Choice. None when there is no unique winner.

        Other namespaces do not call this. The name returned is the decision.
        """
        row = self._exec_row(
            question,
            reason=reason,
            ticket=ticket,
            proposed=proposed,
            facts=facts,
        )
        if not row.get("decision_emitted"):
            return None
        choice = row.get("choice")
        return str(choice) if choice else None

    def _ask_send(self, facts: dict, *, include: tuple[str, ...], reason: str, proposed=None) -> dict:
        """One send-state ask. Empty when the pack does not return."""
        if not self._challenge_book():
            return {}
        try:
            from src.judgment.execution_choices import ask_send
            rows = ask_send(
                symbol=getattr(self, "symbol", None),
                reason=reason,
                proposed=proposed,
                facts=facts,
                include=include,
            )
        except Exception:
            logger.warning("Challenge send pack did not answer reason=%s", reason)
            return {}
        return rows if isinstance(rows, dict) else {}

    @staticmethod
    def _row_choice(row) -> str | None:
        if not isinstance(row, dict) or not row.get("decision_emitted"):
            return None
        choice = row.get("choice")
        return str(choice) if choice else None

    @staticmethod
    def _row_score(row):
        if not isinstance(row, dict):
            return None
        score = row.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)):
            return None
        if score != score or score in (float("inf"), float("-inf")):
            return None
        return float(score)

    def _challenge_manage_emit(
        self,
        act: str,
        *,
        ticket,
        proposed=None,
        reason: str = "",
        trade=None,
    ) -> bool:
        """Challenge SL/TP/close send only when that act's Choice wins.

        Other namespaces keep the existing send. A missing Choice does not send.
        """
        ns = str(getattr(self, "_runtime_namespace", "") or "")
        if ns != "operator":
            return True
        facts = {}
        if trade is not None:
            for key in (
                "direction",
                "entry_price",
                "stop_loss",
                "take_profit",
                "current_volume",
                "sleeve",
                "trade_id",
            ):
                value = getattr(trade, key, None)
                if value is not None:
                    facts[key] = value
        try:
            from src.judgment.manage_choices import emit_manage
            return bool(
                emit_manage(
                    act,
                    ticket=ticket,
                    symbol=getattr(self, "symbol", None),
                    reason=reason,
                    proposed=proposed,
                    facts=facts,
                    namespace=ns,
                )
            )
        except Exception:
            logger.warning(
                "Challenge manage choice did not emit act=%s ticket=%s",
                act,
                ticket,
            )
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

        if not self._challenge_manage_emit(
            "move_sl",
            ticket=ticket,
            proposed=new_sl,
            reason=modify_reason or "modify_sl",
            trade=trade,
        ):
            return False

        result = self.mt5.order_send(request)
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra={"modify_kind": "SL", "attempt": 1, "modify_reason": modify_reason or "modify_sl"},
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
        if self._challenge_book():
            retry_row = self._exec_row(
                "retry",
                reason="sl_modify",
                ticket=ticket,
                proposed=new_sl,
                facts={"modify_kind": "SL", "attempt": 2},
            )
            if self._row_choice(retry_row) != "retry":
                return False
            retry_pause = self._spine_score(
                "retry_pause",
                "The score you return is the pause in seconds before this stop modify is sent again. "
                "An empty score does not send.",
                {"modify_kind": "SL", "ticket": ticket},
                trade=trade,
            )
            if retry_pause is None or retry_pause <= 0:
                return False
            time.sleep(retry_pause)
        else:
            time.sleep(1)
        retry_positions = self.mt5.get_positions(self.symbol)
        result = self.mt5.order_send(request)
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra={"modify_kind": "SL", "attempt": 2, "modify_reason": modify_reason or "modify_sl"},
        )
        if result.success:
            return True
        retry_position = next((p for p in retry_positions if p.ticket == ticket), target_position)
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

        # A take-profit move never increases risk: the stop is untouched, so max
        # loss is unchanged, and the TP1->TP2->TP3 ladder moves TP *further* from
        # entry by construction. It is therefore permitted under the halt's
        # declared "allows_risk_reducing_management" boundary, and
        # tests/test_runtime_control_atomic_halt.py codifies that.
        #
        # What was genuinely missing is the audit trail: _modify_sl records a
        # halt diagnostic for every mutation it performs while halted, and this
        # sibling recorded nothing at all. Record, then proceed.
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
            self._record_runtime_halt_diagnostic(
                action="modify_tp",
                exc=exc,
                extra={
                    "ticket": ticket,
                    "new_tp": new_tp,
                    "modify_reason": modify_reason or "modify_tp",
                    "risk_reducing_management_allowed": True,
                    "disposition": "permitted_tp_move_does_not_increase_risk",
                },
            )

        if not self._challenge_manage_emit(
            "move_tp",
            ticket=ticket,
            proposed=new_tp,
            reason=modify_reason or "modify_tp",
            trade=trade,
        ):
            return False

        result = self.mt5.order_send(request)
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra={"modify_kind": "TP", "attempt": 1, "modify_reason": modify_reason or "modify_tp"},
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
        if self._challenge_book():
            retry_row = self._exec_row(
                "retry",
                reason="tp_modify",
                ticket=ticket,
                proposed=new_tp,
                facts={"modify_kind": "TP", "attempt": 2},
            )
            if self._row_choice(retry_row) != "retry":
                return False
            retry_pause = self._spine_score(
                "retry_pause",
                "The score you return is the pause in seconds before this target modify is sent again. "
                "An empty score does not send.",
                {"modify_kind": "TP", "ticket": ticket},
                trade=trade,
            )
            if retry_pause is None or retry_pause <= 0:
                return False
            time.sleep(retry_pause)
        else:
            time.sleep(1)
        retry_positions = self.mt5.get_positions(self.symbol)
        result = self.mt5.order_send(request)
        self._record_broker_runtime_lifecycle_event(
            stage="sltp_modify_result",
            request=request,
            result=result,
            trade=trade,
            extra={"modify_kind": "TP", "attempt": 2, "modify_reason": modify_reason or "modify_tp"},
        )
        if result.success:
            return True
        retry_position = next((p for p in retry_positions if p.ticket == ticket), target_position)
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
        try:
            self.active_trade.comment = str(getattr(p, "comment", "") or "")
        except Exception:
            pass
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
