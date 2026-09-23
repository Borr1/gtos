"""Execution permission system.

Gate 0 runtime halt plus Gates 0, 0.5, 0.6, 1, and 3 active. Gate 2
(debate/meta-review) stubbed for live. The runtime halt gate runs first when
enabled. Deployment phase then fail-closes on missing/invalid config; Gate 3
(circuit breakers) runs next; Gate 1 (safety checks) runs last.
Every execution action passes through check_permissions() before reaching MT5.

Legacy count caps remain available for non-vNext surfaces. Current vNext
selected-cell rows are governed by account-risk exposure proof instead of old
filled-position counts, and same-symbol overlap is handled by an explicit
ticket-lifecycle conflict gate until multi-position management is proven.
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.components.concurrent_tracker import (
    get_filled_position_count,
    resolve_max_concurrent,
)
from src.components.touch_count_gate_logger import (
    log_touch_count_gate_decision,
)
from src.components.cross_instrument_correlation_gate import (
    evaluate_for_candidate as _evaluate_cross_instrument_correlation,
)
from src.components.same_symbol_lifecycle_v4 import (
    TicketLifecycleSnapshot,
    build_candidate_lifecycle_context,
    evaluate_same_symbol_lifecycle_v4,
    load_same_symbol_lifecycle_store,
    load_same_symbol_pending_intents,
)
from src.components.broker_net_cost_engine import (
    build_pretrade_cost_packet,
    is_vnext_broker_net_cost_required,
    pretrade_cost_refusal_reason,
    set_trade_value,
    trade_value,
)
from src.components.market_whiteboard_v2 import (
    HARD_ACTIONS as _MARKET_WHITEBOARD_V2_HARD_ACTIONS,
    evaluate_for_permissions as _evaluate_market_whiteboard_v2,
)
from src.components.prop_firm_headroom_v4 import (
    evaluate_prop_firm_headroom_snapshot_v4,
    find_prop_firm_headroom_snapshot_v4,
)
from src.research.moonshot_scheduler_v4_best_trade_allocator import (
    build_scheduler_v4_runtime_capture_packet,
)
from src.safety.dormant_state import is_dormant_today, load_dormant_state
from src.safety.runtime_halt import (
    RuntimeHaltError,
    enforce_runtime_not_halted,
    runtime_halt_guard_enabled,
)
from src.mt5.mt5_interface import MAGIC_NUMBER

logger = logging.getLogger(__name__)
OB_RETEST_SL_EXCEPTION_LOG_PATH = "shadow_logs/ob_retest_sl_exception_decisions.jsonl"
VNEXT_BROKER_SYMBOL_ALIASES = {
    "NAS100": "NDX100",
    "NDX100": "NAS100",
    "GER40": "GER30",
    "GER30": "GER40",
    "UKOIL_CASH": "UKOUSD",
    "UKOUSD": "UKOIL_cash",
    "USOIL_CASH": "USOUSD",
    "USOUSD": "USOIL_cash",
    "US30_CASH": "US30",
    "US30.CASH": "US30",
    "US30": "US30_cash",
}


@dataclass
class ExecutionDenial:
    gate: str  # "gate1_safety" or "gate3_circuit_breaker"
    reason: str
    details: dict


@dataclass(frozen=True)
class OBRetestSLExceptionDecision:
    applies: bool
    reason: str
    details: dict


def check_permissions(trade_params, mso, session_state: dict, mt5,
                      config: dict | None = None,
                      symbol: str = "XAUUSD",
                      skip_gate1_safety: bool = False) -> Optional[ExecutionDenial]:
    """Run all permission gates. Returns None if all pass, ExecutionDenial if any fail.

    Gate 0 runtime halt runs FIRST when enabled and is source-bound to local
    halt/autostart flag files. Gate 0 deployment.phase then runs config-only,
    fail-closed against misconfiguration (Q014 / Bryan prod-paper code-path
    sharing failure mode). Gate 0.5 (trading_enabled) runs next, then Gate 3
    (circuit breakers), then Gate 1 (safety checks).
    """
    denial = _reject_if_runtime_halted(config, symbol)
    if denial:
        return denial

    denial = _reject_if_deployment_phase_blocked(config)
    if denial:
        return denial

    denial = _reject_if_trading_disabled(config, symbol)
    if denial:
        return denial

    denial = _reject_if_killed_instrument(config, symbol)
    if denial:
        return denial

    denial = _gate3_circuit_breakers(
        session_state, mt5, config=config, symbol=symbol,
        trade_params=trade_params,
    )
    if denial:
        return denial

    if skip_gate1_safety:
        return None

    denial = _gate1_safety_checks(trade_params, mso, session_state,
                                   config=config, symbol=symbol)
    if denial:
        return denial

    return None


def _reject_if_runtime_halted(config: dict | None,
                              symbol: str) -> Optional[ExecutionDenial]:
    """Gate 0 runtime control - block all execution when halt flags are active."""
    if not runtime_halt_guard_enabled(config, default=False):
        return None
    try:
        enforce_runtime_not_halted(
            action="check_permissions",
            config=config,
            context={"symbol": symbol, "component": "permissions"},
        )
    except RuntimeHaltError as exc:
        snapshot = exc.snapshot.to_dict()
        logger.warning(
            "%s trade blocked by atomic runtime halt: %s",
            symbol,
            snapshot.get("status"),
        )
        return ExecutionDenial(
            "gate0_runtime_halt",
            "runtime_halt_active",
            {
                "symbol": symbol,
                "status": snapshot.get("status"),
                "active_flags": snapshot.get("active_flags", []),
                "unreadable_paths": snapshot.get("unreadable_paths", []),
                "source_boundary": snapshot.get("source_boundary"),
                "runtime_effect_boundary": snapshot.get("runtime_effect_boundary"),
                "forbidden_surface_status": snapshot.get("forbidden_surface_status"),
                "broker_runtime_change_status": snapshot.get(
                    "broker_runtime_change_status"
                ),
            },
        )
    return None


def _vnext_dynamic_geometry_context(tp) -> dict:
    """Return vNext dynamic geometry metadata attached to trade parameters."""
    if tp is None:
        return {"active": False}
    active = bool(getattr(tp, "gtos_vnext_production_execution_path", False)) or bool(
        getattr(tp, "gtos_vnext_dynamic_policy_applied", False)
    )
    selected_policy = str(
        getattr(tp, "gtos_vnext_dynamic_policy_selected", "") or ""
    ).strip()
    final_target_r = None
    try:
        raw_final_target_r = getattr(tp, "gtos_vnext_dynamic_final_target_r", None)
        if raw_final_target_r not in (None, ""):
            final_target_r = float(raw_final_target_r)
    except (TypeError, ValueError):
        final_target_r = None
    return {
        "active": active,
        "selected_policy": selected_policy,
        "final_target_r": final_target_r,
    }


def _reject_if_trading_disabled(config: dict | None,
                                symbol: str) -> Optional[ExecutionDenial]:
    """Gate 0.5 — per-instrument ``trading_enabled`` flag.

    Runs between Gate 0 (deployment.phase) and Gate 3 (circuit breakers). An
    instrument with ``trading_enabled=false`` is prevented from placing trades
    regardless of CANDIDATE quality — this is the observer-mode kill switch
    promoted from a label to a gate.

    The flag is read from the TOP LEVEL of ``config`` because
    ``apply_instrument_overrides`` deep-merges the matching ``instruments.<symbol>``
    block over the base config and then pops ``instruments``. So a key set under
    ``instruments.GBPUSD.trading_enabled`` in ``agent_config.yaml`` surfaces as
    ``config["trading_enabled"]`` after the per-symbol config load completes.

    Defaults to ``True`` when the key is missing so instruments without explicit
    config continue to trade (non-breaking for existing deploys).

    Context: Thursday 2026-04-23 audit flagged that "observer-only" was a
    comment/handoff label, not a code-enforced gate — the pre-AI h1_poi_availability
    gate was the only thing preventing a real ``mt5.order_send`` on GBPUSD if a
    CANDIDATE ever passed L2. This gate makes the block structural.
    """
    cfg = config or {}
    trading_enabled = cfg.get("trading_enabled", True)
    if trading_enabled:
        return None
    logger.info(
        "%s trade blocked by observer-mode flag (trading_enabled=false)",
        symbol,
    )
    return ExecutionDenial(
        "gate0_5_trading_enabled",
        f"trading_disabled_for_instrument:{symbol}",
        {"symbol": symbol, "trading_enabled": False},
    )


def _symbol_policy_key(symbol: str) -> str:
    return str(symbol or "").strip().replace(".", "_").upper()


def _reject_if_killed_instrument(config: dict | None,
                                 symbol: str) -> Optional[ExecutionDenial]:
    """Gate 0.6 - source-bound hard kill list for invalidated instruments."""
    policy = (config or {}).get("killed_instrument_policy", {})
    if not isinstance(policy, dict) or not bool(policy.get("enabled", False)):
        return None
    symbols = policy.get("symbols", {})
    if not isinstance(symbols, dict):
        return None
    requested = _symbol_policy_key(symbol)
    matched_key = next(
        (key for key in symbols if _symbol_policy_key(key) == requested),
        None,
    )
    if matched_key is None:
        return None
    raw_details = symbols.get(matched_key)
    details = dict(raw_details) if isinstance(raw_details, dict) else {}
    if details.get("enabled", True) is False:
        return None
    reason = str(details.get("reason") or "killed_by_evidence")
    logger.warning(
        "%s trade blocked by killed-instrument policy: %s",
        symbol,
        reason,
    )
    return ExecutionDenial(
        "gate0_6_killed_instrument",
        f"killed_instrument:{requested}",
        {
            "symbol": symbol,
            "matched_symbol": matched_key,
            "reason": reason,
            "source_path": details.get("source_path"),
            "source_line_no": details.get("source_line_no"),
        },
    )


def _reject_if_deployment_phase_blocked(config: dict | None) -> Optional[ExecutionDenial]:
    """Gate on config.deployment.phase. Fail-closed on missing/invalid input.

    Mapping (approved by CEO 2026-04-18):
      phase == 1 -> reject "deployment_phase_1_block_all_orders"
      phase == 2 -> reject "deployment_phase_2_log_only" (evaluation still logs;
                    orchestrator is expected to treat this as a non-placement outcome)
      phase == 3 -> pass through (current live FTMO demo behavior)
      missing / non-int / unknown -> reject "deployment_phase_invalid" (fail-closed)

    This gate runs before Gate 3 so a silent misconfig cannot be masked by an
    unrelated earlier rejection reason — the denial log always carries the
    phase diagnostic.

    WARNING — phase=2 is NOT log-only end-to-end yet. The orchestrator
    (`src/components/orchestrator.py` ~line 809) treats every ExecutionDenial
    identically: record REJECTED, log candle, return. Phase=2 is therefore
    observationally identical to phase=1 today. A log-only divert path in the
    orchestrator is a required T1 follow-up BEFORE any flip from phase=3 to
    phase=2 in production.
    """
    deployment_cfg = (config or {}).get("deployment")
    if not isinstance(deployment_cfg, dict) or "phase" not in deployment_cfg:
        logger.warning(
            "Gate0: deployment.phase missing from config — failing closed. "
            "config type=%s",
            type(deployment_cfg).__name__,
        )
        return ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_invalid",
            {"phase": None, "reason": "missing"},
        )

    phase = deployment_cfg.get("phase")
    if not isinstance(phase, int) or isinstance(phase, bool):
        logger.warning(
            "Gate0: deployment.phase is not an int — failing closed. "
            "value=%r type=%s",
            phase, type(phase).__name__,
        )
        return ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_invalid",
            {"phase": phase, "reason": "non_int"},
        )

    if phase == 3:
        return None
    if phase == 1:
        return ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_1_block_all_orders",
            {"phase": 1},
        )
    if phase == 2:
        return ExecutionDenial(
            "gate0_deployment_phase",
            "deployment_phase_2_log_only",
            {"phase": 2},
        )

    logger.warning(
        "Gate0: deployment.phase has unknown value — failing closed. phase=%r",
        phase,
    )
    return ExecutionDenial(
        "gate0_deployment_phase",
        "deployment_phase_invalid",
        {"phase": phase, "reason": "unknown_value"},
    )


def _gate3_circuit_breakers(session_state: dict, mt5,
                            config: dict | None = None,
                            symbol: str = "XAUUSD",
                            trade_params=None) -> Optional[ExecutionDenial]:
    """Hard stops. If any triggers, NO trading.

    T2.8 order of checks (session 33):
      1. dormant-state marker (daily-loss stop persisted across restarts)
      2. daily_pnl_pct breach of ``risk.max_daily_loss_pct`` (live safety
         net — marker should normally precede this, but we check both so
         a first-boot-past-breach still rejects)
      3. vNext prop-safe account headroom packet for governed production rows
      4. vNext same-symbol lifecycle conflict, then legacy/non-vNext concurrent cap
      3.5 cross-instrument correlation cluster — REJECT only (additive,
          REDUCE_HALF flows through the orchestrator's sizing path)
      4. MT5 connection
      5. Spread
      5.5 vNext broker-net pretrade cost packet/gate when selected-cell
          production execution requires it
      5.6 Market Whiteboard V2 source/damage/zero-trade admission, when
          explicitly enabled in config. RISK_REDUCE remains a sizing signal;
          SOURCE_REQUIRED / QUARANTINE / NO_TRADE reject here.

    ``max_kz_trades=1`` and ``max_daily_losses=2`` were REMOVED in T2.8 —
    the concurrent cap subsumes them formulaically. Correlation caps
    still apply downstream in ``portfolio_risk.check_correlation_risk``.
    """
    risk_cfg = (config or {}).get("risk", {})

    # 1. Dormant-state marker — persisted daily-loss stop.
    denial = _reject_if_dormant(config, symbol)
    if denial:
        return denial

    # 2. Daily loss limit (live safety net; uses MTM daily_pnl_pct from
    # orchestrator._update_daily_pnl). Default 4.0% is the internal daily
    # overlay/cushion; active vNext trades do not derive a live trade-count cap
    # from this value.
    max_daily_loss = risk_cfg.get("max_daily_loss_pct", 4.0)
    daily_pnl_pct = session_state.get("daily_pnl_pct", 0.0)
    if daily_pnl_pct <= -max_daily_loss:
        return ExecutionDenial("gate3_circuit_breaker", "daily_loss_limit",
                               {"daily_pnl_pct": daily_pnl_pct,
                                "max_daily_loss_pct": max_daily_loss})

    # 3. VNext prop-safe account headroom must already be source-bound for
    # governed production rows. The selector is evaluated in the orchestrator
    # with account equity/balance/open-risk state; permissions consumes that
    # packet so an order cannot bypass daily/overall drawdown authority.
    denial = _reject_if_vnext_prop_safe_selector_missing_or_blocked(
        trade_params,
        config=config,
        symbol=symbol,
        session_state=session_state,
    )
    if denial:
        return denial

    # 4. VNext same-symbol lifecycle conflict, then legacy/non-vNext concurrent cap.
    # concurrent cap across all symbols filtered by MAGIC_NUMBER.
    denial = _reject_if_same_symbol_vnext_lifecycle_conflict(
        mt5, symbol, config, trade_params,
    )
    if denial:
        return denial

    # 4.5 Scheduler V4 is the terminal full-window allocation authority for
    # vNext selected-cell rows. It runs after prop-safe and same-symbol gates so
    # their source-bound packets can be included in the scheduler window.
    denial = _reject_if_scheduler_v4_not_selected_authority(
        mt5, symbol, config, trade_params,
    )
    if denial:
        return denial

    denial = _reject_if_concurrent_cap_reached(mt5, config, trade_params)
    if denial:
        return denial

    # 3.5 Cross-instrument correlation cluster — REJECT only.
    # Catches the USD-weakness-day failure mode where GBPUSD+US30+XAU+GBPJPY
    # signal LONG together with no formal correlation group binding them.
    # The HALVE response (cluster_size == min_positions) flows through the
    # orchestrator's sizing pipeline, not this gate — see
    # ``cross_instrument_correlation_gate.evaluate_for_candidate`` and
    # ``orchestrator._compute_cross_instrument_risk_adjustment``.
    denial = _reject_if_cross_instrument_correlation_excess(mt5, config, trade_params)
    if denial:
        return denial

    # 4. MT5 connection check
    if not mt5.is_connected():
        return ExecutionDenial("gate3_circuit_breaker", "mt5_disconnected", {})

    # 5. Spread check — use correct symbol and config threshold
    tick = mt5.get_tick(symbol)
    max_spread = risk_cfg.get("max_spread_cents", 30)
    if tick is None:
        return ExecutionDenial("gate3_circuit_breaker", "spread_too_wide",
                               {"spread_cents": "N/A", "max_spread": max_spread})
    above_cents = tick.spread_cents > max_spread
    try:
        from src.judgment.cost_choices import withholds
        withhold_cents = withholds(
            "permissions_spread",
            {
                "symbol": symbol,
                "spread_cents": tick.spread_cents,
                "max_spread_cents": max_spread,
                "cents_above_the_max": bool(above_cents),
            },
        )
    except Exception:
        withhold_cents = False
    if withhold_cents:
        return ExecutionDenial("gate3_circuit_breaker", "spread_too_wide",
                               {"spread_cents": tick.spread_cents, "max_spread": max_spread})

    denial = _reject_if_vnext_broker_net_pretrade_cost_refused(
        trade_params,
        tick=tick,
        config=config,
        symbol=symbol,
    )
    if denial:
        return denial

    denial = _reject_if_market_whiteboard_v2_blocks(
        trade_params, session_state, config, symbol,
    )
    if denial:
        return denial

    return None


def _vnext_prop_safe_selector_required(config: dict | None, trade_params) -> tuple[bool, dict]:
    cfg = ((config or {}).get("gtos_vnext_runtime") or {})
    if not (
        bool(cfg.get("prop_safe_selector_enabled", False))
        and bool(cfg.get("prop_safe_selector_apply_to_execution", False))
    ):
        return False, {"reason": "prop_safe_selector_not_enabled_for_execution"}
    governed, proof = _vnext_risk_budget_governed_trade(trade_params)
    if not governed:
        proof["reason"] = "trade_not_vnext_risk_budget_governed"
        return False, proof
    return True, proof


def _reject_if_vnext_prop_safe_selector_missing_or_blocked(
    trade_params,
    *,
    config: dict | None,
    symbol: str,
    session_state: dict | None = None,
) -> Optional[ExecutionDenial]:
    required, proof = _vnext_prop_safe_selector_required(config, trade_params)
    if not required:
        return None
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    action = str(trade_value(tp, "gtos_vnext_prop_safe_selector_action") or "").strip().upper()
    would_action = str(
        trade_value(tp, "gtos_vnext_prop_safe_selector_would_action") or ""
    ).strip().upper()
    reason = str(trade_value(tp, "gtos_vnext_prop_safe_selector_reason") or "").strip()
    applied = trade_value(tp, "gtos_vnext_prop_safe_selector_applied")
    after_risk_pct = trade_value(tp, "gtos_vnext_prop_safe_selector_after_risk_pct")
    if not action or not would_action or not reason:
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "vnext_prop_safe_selector_packet_missing",
            {
                "symbol": symbol,
                "required": True,
                "proof": proof,
                "missing_fields": [
                    name
                    for name, value in (
                        ("gtos_vnext_prop_safe_selector_action", action),
                        ("gtos_vnext_prop_safe_selector_would_action", would_action),
                        ("gtos_vnext_prop_safe_selector_reason", reason),
                    )
                    if not value
                ],
            },
        )
    blocking_action = None
    if action in {"BLOCK", "DEFER_UNTIL_RESET"}:
        blocking_action = action
    elif would_action in {"BLOCK", "DEFER_UNTIL_RESET"}:
        blocking_action = would_action
    if blocking_action:
        return ExecutionDenial(
            "gate3_circuit_breaker",
            f"vnext_prop_safe_selector_{blocking_action.lower()}",
            {
                "symbol": symbol,
                "action": action,
                "would_action": would_action,
                "reason": reason,
                "applied": applied,
                "proof": proof,
            },
        )
    if action == "REDUCE_RISK" or would_action == "REDUCE_RISK":
        try:
            after = float(after_risk_pct)
        except (TypeError, ValueError):
            after = 0.0
        if after <= 0:
            return ExecutionDenial(
                "gate3_circuit_breaker",
                "vnext_prop_safe_selector_invalid_reduced_risk",
                {
                    "symbol": symbol,
                    "action": action,
                    "would_action": would_action,
                    "reason": reason,
                    "after_risk_pct": after_risk_pct,
                    "proof": proof,
                },
            )
        selected = proof.get("selected_cell_risk_pct")
        if selected is None or float(selected) > after:
            set_trade_value(tp, "gtos_vnext_selected_cell_risk_pct", after)
            proof["selected_cell_risk_pct_after_prop_safe_selector"] = after
    headroom_denial = _reject_if_prop_firm_headroom_snapshot_missing_or_invalid(
        tp,
        config=config,
        symbol=symbol,
        session_state=session_state,
        proof=proof,
    )
    if headroom_denial:
        return headroom_denial
    return None


def _reject_if_prop_firm_headroom_snapshot_missing_or_invalid(
    tp,
    *,
    config: dict | None,
    symbol: str,
    session_state: dict | None,
    proof: dict,
) -> Optional[ExecutionDenial]:
    requested_risk_pct = trade_value(tp, "gtos_vnext_selected_cell_risk_pct")
    snapshot = find_prop_firm_headroom_snapshot_v4(tp, session_state)
    evaluation = evaluate_prop_firm_headroom_snapshot_v4(
        snapshot=snapshot,
        requested_risk_pct=requested_risk_pct,
        config=config,
    )
    packet = evaluation.to_packet()
    set_trade_value(tp, "gtos_vnext_prop_firm_headroom_v4_packet", packet)
    if evaluation.allowed:
        return None
    return ExecutionDenial(
        "gate3_circuit_breaker",
        f"vnext_prop_firm_headroom_{evaluation.reason}",
        {
            **proof,
            "symbol": symbol,
            "requested_risk_pct": requested_risk_pct,
            "prop_firm_headroom_v4": packet,
            "vnext_contract": (
                "PropFirmHeadroomSnapshotV4 broker-real account authority "
                "is required before governed V4 risk-bearing execution"
            ),
        },
    )


def _cfg_bool(config: dict | None, key: str, default: bool = False) -> bool:
    cfg = ((config or {}).get("gtos_vnext_runtime") or {})
    value = cfg.get(key, default) if isinstance(cfg, dict) else default
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _cfg_float(config: dict | None, key: str, default: float) -> float:
    cfg = ((config or {}).get("gtos_vnext_runtime") or {})
    try:
        value = cfg.get(key, default) if isinstance(cfg, dict) else default
        return float(value if value not in (None, "") else default)
    except (TypeError, ValueError):
        return default


def _cfg_list(config: dict | None, key: str, default: list[str]) -> list[str]:
    cfg = ((config or {}).get("gtos_vnext_runtime") or {})
    value = cfg.get(key, default) if isinstance(cfg, dict) else default
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    if isinstance(value, (list, tuple)):
        return [str(part).strip() for part in value if str(part).strip()]
    return list(default)


def _cfg_str(config: dict | None, key: str, default: str | None = None) -> str | None:
    cfg = ((config or {}).get("gtos_vnext_runtime") or {})
    value = cfg.get(key, default) if isinstance(cfg, dict) else default
    if value in (None, ""):
        return default
    return str(value)


def _scheduler_v4_required(config: dict | None, trade_params) -> tuple[bool, dict]:
    if not (
        _cfg_bool(config, "scheduler_v4_best_trade_allocator_enabled")
        and _cfg_bool(config, "scheduler_v4_best_trade_allocator_apply_to_execution")
        and _cfg_bool(config, "scheduler_v4_best_trade_allocator_live_activation_allowed")
    ):
        return False, {"reason": "scheduler_v4_not_terminal_by_config"}
    governed, proof = _vnext_risk_budget_governed_trade(trade_params)
    if not governed:
        proof["reason"] = "trade_not_vnext_risk_budget_governed"
        return False, proof
    return True, proof


def _scheduler_v4_config(config: dict | None) -> dict:
    return {
        "enabled": _cfg_bool(config, "scheduler_v4_best_trade_allocator_enabled"),
        "apply_to_execution": _cfg_bool(
            config,
            "scheduler_v4_best_trade_allocator_apply_to_execution",
        ),
        "live_activation_allowed": _cfg_bool(
            config,
            "scheduler_v4_best_trade_allocator_live_activation_allowed",
        ),
        "portfolio_ceiling_pct": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_portfolio_ceiling_pct",
            4.0,
        ),
        "correlation_cluster_ceiling_pct": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_correlation_cluster_ceiling_pct",
            1.5,
        ),
        "min_reduced_risk_pct": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_min_reduced_risk_pct",
            0.10,
        ),
        "min_trade_score": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_min_trade_score",
            0.35,
        ),
        "zero_trade_score": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_zero_trade_score",
            0.20,
        ),
        "pending_replacement_enabled": _cfg_bool(
            config,
            "scheduler_v4_best_trade_allocator_pending_replacement_enabled",
            True,
        ),
        "pending_replacement_min_candidate_ev_r": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_pending_replacement_min_candidate_ev_r",
            0.65,
        ),
        "pending_replacement_min_candidate_probability": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_pending_replacement_min_candidate_probability",
            0.68,
        ),
        "pending_replacement_min_edge_delta": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_pending_replacement_min_edge_delta",
            0.20,
        ),
        "pending_replacement_min_pending_age_minutes": _cfg_float(
            config,
            "scheduler_v4_best_trade_allocator_pending_replacement_min_pending_age_minutes",
            0.0,
        ),
        "require_full_window_source": _cfg_bool(
            config,
            "scheduler_v4_best_trade_allocator_require_full_window_source",
        ),
        "critical_missing_source_tokens": _cfg_list(
            config,
            "scheduler_v4_best_trade_allocator_critical_missing_source_tokens",
            [],
        ),
        "ultimate_candidate_package_enabled": _cfg_bool(
            config,
            "ultimate_candidate_package_enabled",
        ),
        "ultimate_candidate_package_shadow_enabled": _cfg_bool(
            config,
            "ultimate_candidate_package_shadow_enabled",
        ),
        "ultimate_candidate_package_apply_to_execution": _cfg_bool(
            config,
            "ultimate_candidate_package_apply_to_execution",
        ),
        "ultimate_candidate_package_live_activation_allowed": _cfg_bool(
            config,
            "ultimate_candidate_package_live_activation_allowed",
        ),
        "ultimate_candidate_package_final_package_selected": _cfg_bool(
            config,
            "ultimate_candidate_package_final_package_selected",
        ),
        "ultimate_candidate_package_registry_path": _cfg_str(
            config,
            "ultimate_candidate_package_registry_path",
        ),
        "ultimate_candidate_package_require_shadow_match_for_selector_v4": _cfg_bool(
            config,
            "ultimate_candidate_package_require_shadow_match_for_selector_v4",
        ),
    }


def _stable_scheduler_packet_hash(packet: dict) -> str:
    payload = json.dumps(
        packet,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _scheduler_v4_candidate_id(trade_params, symbol: str) -> str:
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    for key in (
        "candidate_id",
        "gtos_vnext_candidate_id",
        "gtos_vnext_broader_origin_candidate_id",
        "gtos_vnext_selector_row_id",
        "trade_id",
    ):
        value = trade_value(tp, key)
        if value not in (None, ""):
            return str(value)
    return f"{symbol}:candidate_id_missing"


def _scheduler_v4_decision_window_candidates(trade_params, symbol: str) -> list[dict] | None:
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    raw_window = (
        trade_value(tp, "gtos_vnext_decision_window_candidates")
        or trade_value(tp, "decision_window_candidates")
        or trade_value(tp, "runtime_candidate_window")
    )
    if not isinstance(raw_window, (list, tuple)):
        return None
    current_id = _scheduler_v4_candidate_id(tp, symbol)
    rows: list[dict] = []
    for index, raw in enumerate(raw_window):
        if not isinstance(raw, dict):
            continue
        row = dict(raw)
        row.setdefault("candidate_id", current_id if index == 0 else f"{current_id}:candidate:{index}")
        row.setdefault("symbol", row.get("broker_symbol") or symbol)
        row.setdefault("side", row.get("direction") or trade_value(tp, "direction"))
        row.setdefault(
            "requested_risk_pct",
            row.get("selected_cell_risk_pct")
            or row.get("risk_pct")
            or trade_value(tp, "gtos_vnext_selected_cell_risk_pct"),
        )
        row.setdefault("decision_time_utc", trade_value(tp, "decision_time_utc"))
        row.setdefault("evidence_class", "production_permissions_scheduler_v4_input")
        row.setdefault("no_leak_status", row.get("no_leak_status") or "pass")
        rows.append(row)
    return rows


def _scheduler_v4_open_position_snapshot(mt5) -> list[dict] | None:
    if mt5 is None:
        return None
    try:
        positions = mt5.get_positions()
    except TypeError:
        positions = mt5.get_positions("XAUUSD")
    except Exception:  # noqa: BLE001 - source unavailable is handled fail-closed.
        return None
    if positions is None:
        return None
    rows: list[dict] = []
    for index, position in enumerate(positions):
        side = _position_side_for_gate(position)
        rows.append(
            {
                "exposure_id": str(getattr(position, "ticket", None) or index),
                "ticket": getattr(position, "ticket", None),
                "symbol": getattr(position, "symbol", None),
                "side": side,
                "risk_pct": getattr(
                    position,
                    "gtos_vnext_selected_cell_risk_pct",
                    getattr(position, "risk_pct", 0.0),
                ),
                "probability_at_entry": getattr(
                    position,
                    "gtos_vnext_probability_at_entry",
                    None,
                ),
                "ev_r_at_entry": getattr(position, "gtos_vnext_ev_r_at_entry", None),
                "thesis_id": getattr(position, "gtos_vnext_thesis_id", None),
                "lifecycle_phase": getattr(
                    position,
                    "gtos_vnext_lifecycle_phase",
                    "open",
                ),
                "source_status": "permissions_read_only_open_position_snapshot",
            }
        )
    return rows


def _scheduler_v4_source_context(
    mt5,
    symbol: str,
    config: dict | None,
    trade_params,
) -> dict:
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    context: dict = {
        "source_completeness_state": (
            trade_value(tp, "source_completeness_status")
            or trade_value(tp, "source_path_feature_status")
            or "permissions_runtime_source_snapshot"
        ),
        "no_leak_status": trade_value(tp, "no_leak_status") or "pass",
        "zero_trade_value_calibration": {
            "status": "configured_zero_trade_score",
            "zero_trade_score": _cfg_float(
                config,
                "scheduler_v4_best_trade_allocator_zero_trade_score",
                0.20,
            ),
        },
    }
    decision_window = _scheduler_v4_decision_window_candidates(trade_params, symbol)
    if decision_window is not None:
        context["decision_window_candidates"] = decision_window
    open_positions = _scheduler_v4_open_position_snapshot(mt5)
    if open_positions is not None:
        context["open_position_snapshot"] = open_positions
    pending_snapshot = trade_value(tp, "gtos_vnext_pending_order_snapshot")
    if isinstance(pending_snapshot, list):
        context["pending_order_snapshot"] = pending_snapshot
    for field_name, context_name in (
        ("gtos_vnext_same_symbol_lifecycle_v4_packet", "same_symbol_lifecycle_packet"),
        ("gtos_vnext_probability_debate_v4_packet", "probability_debate_packet"),
        ("gtos_vnext_numeric_confluence_v4_packet", "numeric_follow_avoid_mixed_packet"),
        ("gtos_vnext_follow_avoid_mixed_numeric_confluence_v4_packet", "numeric_follow_avoid_mixed_packet"),
        ("gtos_vnext_selector_v4_packet", "selector_v4_packet"),
        ("gtos_vnext_pretrade_cost_model", "pretrade_cost_model"),
        ("gtos_vnext_selected_cell_risk_proof", "selected_cell_risk_proof"),
    ):
        value = trade_value(tp, field_name)
        if isinstance(value, dict):
            context[context_name] = value
    source_event_hash = (
        trade_value(tp, "gtos_vnext_source_event_hash")
        or trade_value(tp, "gtos_vnext_source_event_hash_sha256")
        or trade_value(tp, "source_event_hash_sha256")
    )
    if source_event_hash:
        context["source_event_hash"] = source_event_hash
    return context


def _reject_if_scheduler_v4_not_selected_authority(
    mt5,
    symbol: str,
    config: dict | None,
    trade_params,
) -> Optional[ExecutionDenial]:
    required, proof = _scheduler_v4_required(config, trade_params)
    if not required:
        return None
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    candidate_id = _scheduler_v4_candidate_id(tp, symbol)
    runtime_event = {
        "candidate_id": candidate_id,
        "symbol": symbol,
        "side": trade_value(tp, "direction"),
        "timestamp_utc": trade_value(tp, "decision_time_utc"),
    }
    selected_cell_risk_packet = {
        "risk_pct": trade_value(tp, "gtos_vnext_selected_cell_risk_pct"),
        "cell_id": trade_value(tp, "gtos_vnext_selected_cell_risk_cell_id"),
        "selected_policy": trade_value(tp, "gtos_vnext_dynamic_policy_selected"),
        "execution_policy_id": trade_value(tp, "gtos_vnext_execution_policy_id"),
    }
    final_risk_authority = {
        "effective_risk_pct": trade_value(tp, "gtos_vnext_selected_cell_risk_pct"),
        "final_order_effective_risk_pct": trade_value(
            tp,
            "gtos_vnext_selected_cell_risk_pct",
        ),
    }
    try:
        packet = build_scheduler_v4_runtime_capture_packet(
            candidate={
                "candidate_id": candidate_id,
                "symbol": symbol,
                "side": trade_value(tp, "direction"),
                "requested_risk_pct": trade_value(tp, "gtos_vnext_selected_cell_risk_pct"),
            },
            runtime_event=runtime_event,
            selected_cell_risk_packet=selected_cell_risk_packet,
            final_risk_authority=final_risk_authority,
            source_context=_scheduler_v4_source_context(
                mt5,
                symbol,
                config,
                trade_params,
            ),
            config=_scheduler_v4_config(config),
        )
    except Exception as exc:  # noqa: BLE001 - terminal scheduler source must fail closed.
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "scheduler_v4_authority_packet_failed_closed",
            {**proof, "symbol": symbol, "candidate_id": candidate_id, "source_error": str(exc)},
        )

    packet_hash = _stable_scheduler_packet_hash(packet)
    decision = packet.get("decision") if isinstance(packet.get("decision"), dict) else {}
    selected_candidate_id = str(decision.get("selected_candidate_id") or "")
    selected_action = str(decision.get("selected_action_class") or "")
    missing_runtime_truth = list(
        (packet.get("source_boundary") or {}).get("missing_runtime_truth") or []
    )
    set_trade_value(tp, "gtos_vnext_scheduler_v4_packet", packet)
    set_trade_value(tp, "gtos_vnext_scheduler_v4_packet_hash", packet_hash)
    set_trade_value(tp, "gtos_vnext_scheduler_v4_selected_candidate_id", selected_candidate_id)
    set_trade_value(tp, "gtos_vnext_scheduler_v4_selected_action_class", selected_action)
    set_trade_value(tp, "gtos_vnext_scheduler_v4_current_candidate_id", candidate_id)
    set_trade_value(tp, "gtos_vnext_scheduler_v4_decision_window_id", packet.get("decision_window_id"))

    if missing_runtime_truth:
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "scheduler_v4_full_window_source_required",
            {
                **proof,
                "symbol": symbol,
                "candidate_id": candidate_id,
                "packet_hash": packet_hash,
                "scheduler_v4": packet,
                "missing_runtime_truth": missing_runtime_truth,
                "vnext_contract": "scheduler_v4_terminal_full_window_allocator_gate",
            },
        )
    try:
        from src.judgment.scheduler_choices import challenge_scheduler, expression_gate
    except Exception:
        import os
        import sys

        argv = [str(arg) for arg in sys.argv]
        challenge = os.environ.get("GTOS_BOOK_NAMESPACE") == "operator" or any(
            (arg == "--namespace" and index + 1 < len(argv) and argv[index + 1] == "operator")
            or arg == "--namespace=operator"
            for index, arg in enumerate(argv)
        )
        if challenge:
            raise
        challenge_scheduler = None
        expression_gate = None
    else:
        if challenge_scheduler():
            gate = expression_gate(
                selected_action=selected_action,
                selected_candidate_id=selected_candidate_id,
                candidate_id=candidate_id,
                runtime_effect_now=bool(decision.get("runtime_effect_now")),
                symbol=symbol,
            )
            if gate.get("expressed"):
                return None
            return ExecutionDenial(
                "gate3_circuit_breaker",
                str(gate.get("reason") or "scheduler_choice_no_decision"),
                {
                    **proof,
                    "symbol": symbol,
                    "candidate_id": candidate_id,
                    "selected_candidate_id": selected_candidate_id,
                    "selected_action_class": selected_action,
                    "packet_hash": packet_hash,
                    "scheduler_v4": packet,
                    "choice_question": gate.get("question"),
                    "restored_boolean": False,
                    "vnext_contract": "scheduler_v4_terminal_full_window_allocator_gate",
                },
            )
    if selected_action == "zero_trade":
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "scheduler_v4_selected_zero_trade",
            {
                **proof,
                "symbol": symbol,
                "candidate_id": candidate_id,
                "packet_hash": packet_hash,
                "scheduler_v4": packet,
                "vnext_contract": "scheduler_v4_terminal_full_window_allocator_gate",
            },
        )
    if selected_candidate_id and selected_candidate_id != candidate_id:
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "scheduler_v4_candidate_not_selected",
            {
                **proof,
                "symbol": symbol,
                "candidate_id": candidate_id,
                "selected_candidate_id": selected_candidate_id,
                "selected_action_class": selected_action,
                "packet_hash": packet_hash,
                "scheduler_v4": packet,
                "vnext_contract": "scheduler_v4_terminal_full_window_allocator_gate",
            },
        )
    if not decision.get("runtime_effect_now"):
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "scheduler_v4_selected_action_not_runtime_eligible",
            {
                **proof,
                "symbol": symbol,
                "candidate_id": candidate_id,
                "selected_candidate_id": selected_candidate_id,
                "selected_action_class": selected_action,
                "packet_hash": packet_hash,
                "scheduler_v4": packet,
                "vnext_contract": "scheduler_v4_terminal_full_window_allocator_gate",
            },
        )
    return None


def _reject_if_vnext_broker_net_pretrade_cost_refused(
    trade_params,
    *,
    tick,
    config: dict | None,
    symbol: str,
) -> Optional[ExecutionDenial]:
    if not is_vnext_broker_net_cost_required(config, trade_params):
        return None
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    entry_price = trade_value(tp, "entry_price")
    stop_loss = trade_value(tp, "stop_loss")
    sl_distance = None
    try:
        if entry_price not in (None, "") and stop_loss not in (None, ""):
            sl_distance = abs(float(entry_price) - float(stop_loss))
    except (TypeError, ValueError):
        sl_distance = None
    packet = build_pretrade_cost_packet(
        config=config,
        trade_params=tp,
        tick=tick,
        symbol=symbol,
        broker_symbol=(config or {}).get("market", {}).get("mt5_symbol", symbol),
        entry_price=entry_price,
        stop_loss=stop_loss,
        sl_distance=sl_distance,
        risk_pct=trade_value(tp, "gtos_vnext_selected_cell_risk_pct"),
        symbol_info=None,
    )
    set_trade_value(tp, "gtos_vnext_pretrade_cost_model", packet)
    refusal = pretrade_cost_refusal_reason(packet)
    if refusal:
        try:
            from src.judgment.cost_choices import filter_pretrade_block
            refusal = filter_pretrade_block(packet, refusal)
        except Exception:
            refusal = None
        if refusal:
            return ExecutionDenial(
                "gate3_circuit_breaker",
                "vnext_broker_net_pretrade_cost_refused",
                {"pretrade_cost_model": packet, "refusal_reason": refusal},
            )
    return None


def _vnext_risk_budget_governed_trade(trade_params) -> tuple[bool, dict]:
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    context = _vnext_dynamic_geometry_context(tp)
    execution_policy_id = str(
        getattr(tp, "gtos_vnext_execution_policy_id", "") or ""
    ).strip()
    selected_policy = context.get("selected_policy") or str(
        getattr(tp, "gtos_vnext_dynamic_policy_selected", "") or ""
    ).strip()
    risk_pct_raw = getattr(tp, "gtos_vnext_selected_cell_risk_pct", None)
    try:
        risk_pct = float(risk_pct_raw)
    except (TypeError, ValueError):
        risk_pct = None
    governed = bool(
        context.get("active")
        and selected_policy
        and execution_policy_id
        and risk_pct is not None
        and risk_pct > 0
    )
    return governed, {
        "vnext_dynamic_context_active": bool(context.get("active")),
        "selected_policy": selected_policy or None,
        "execution_policy_id": execution_policy_id or None,
        "selected_cell_risk_pct": risk_pct,
    }


def _position_side_for_gate(position) -> str | None:
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


def _symbol_key_for_gate(value: object) -> str:
    return str(value or "").strip().upper()


def _append_symbol_alias(values: list[str], value: object) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


def _vnext_symbol_aliases_for_gate(symbol: str, config: dict | None) -> list[str]:
    aliases: list[str] = []
    _append_symbol_alias(aliases, symbol)
    if isinstance(config, dict):
        market = config.get("market") or {}
        if isinstance(market, dict):
            for key in ("symbol", "mt5_symbol", "broker_symbol"):
                _append_symbol_alias(aliases, market.get(key))
        instruments = config.get("instruments") or {}
        target_keys = {_symbol_key_for_gate(value) for value in aliases}
        if isinstance(instruments, dict):
            for instrument_name, instrument_cfg in instruments.items():
                instrument_market = (
                    instrument_cfg.get("market") or {}
                    if isinstance(instrument_cfg, dict)
                    else {}
                )
                instrument_values = [instrument_name]
                if isinstance(instrument_market, dict):
                    instrument_values.extend([
                        instrument_market.get("symbol"),
                        instrument_market.get("mt5_symbol"),
                        instrument_market.get("broker_symbol"),
                    ])
                instrument_keys = {
                    _symbol_key_for_gate(value)
                    for value in instrument_values
                    if value
                }
                if target_keys & instrument_keys:
                    for value in instrument_values:
                        _append_symbol_alias(aliases, value)

    idx = 0
    while idx < len(aliases):
        key = _symbol_key_for_gate(aliases[idx])
        mapped = VNEXT_BROKER_SYMBOL_ALIASES.get(key)
        if mapped:
            _append_symbol_alias(aliases, mapped)
        idx += 1
    return aliases


def _reject_if_same_symbol_vnext_lifecycle_conflict(
    mt5,
    symbol: str,
    config: dict | None,
    trade_params,
) -> Optional[ExecutionDenial]:
    governed, proof = _vnext_risk_budget_governed_trade(trade_params)
    if not governed or mt5 is None:
        return None
    aliases = _vnext_symbol_aliases_for_gate(symbol, config)
    queried_positions: dict[object, object] = {}
    try:
        for query_symbol in aliases:
            positions = mt5.get_positions(query_symbol)
            if positions is None:
                return ExecutionDenial(
                    "gate3_circuit_breaker",
                    "same_symbol_position_source_unavailable_for_vnext_lifecycle_guard",
                    {
                        **proof,
                        "symbol": symbol,
                        "symbol_aliases_checked": aliases,
                        "failed_query_symbol": query_symbol,
                        "source_error": "mt5.get_positions returned None",
                        "vnext_contract": (
                            "selected-cell vNext rows fail closed when same-symbol "
                            "position state cannot be read"
                        ),
                    },
                )
            for position in positions:
                ticket = getattr(position, "ticket", None)
                queried_positions[ticket if ticket is not None else id(position)] = position
    except Exception as exc:  # noqa: BLE001
        logger.warning("same-symbol vNext conflict check failed closed: %s", exc)
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "same_symbol_position_source_unavailable_for_vnext_lifecycle_guard",
            {
                **proof,
                "symbol": symbol,
                "symbol_aliases_checked": aliases,
                "source_error": str(exc),
                "vnext_contract": (
                    "selected-cell vNext rows fail closed when same-symbol "
                    "position state cannot be read"
                ),
            },
        )
    alias_keys = {_symbol_key_for_gate(alias) for alias in aliases}
    same_symbol = [
        p for p in queried_positions.values()
        if _symbol_key_for_gate(getattr(p, "symbol", "")) in alias_keys
        and getattr(p, "magic", MAGIC_NUMBER) == MAGIC_NUMBER
    ]
    pending_source = load_same_symbol_pending_intents(
        symbol=symbol,
        aliases=aliases,
        config=config,
    )
    lifecycle_store = load_same_symbol_lifecycle_store(config)
    candidate = build_candidate_lifecycle_context(
        symbol=symbol,
        aliases=aliases,
        trade_params=trade_params,
        proof=proof,
    )
    decision = evaluate_same_symbol_lifecycle_v4(
        candidate=candidate,
        open_positions=[
            TicketLifecycleSnapshot.from_position(
                position,
                lifecycle_store=lifecycle_store,
            )
            for position in same_symbol
        ],
        pending_orders=pending_source.snapshots,
        pending_source_errors=pending_source.source_errors,
        config=config,
    )
    packet = decision.to_packet()
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        tp = trade_params
    set_trade_value(tp, "gtos_vnext_same_symbol_lifecycle_v4_packet", packet)
    set_trade_value(tp, "gtos_vnext_same_symbol_lifecycle_action", decision.action)
    set_trade_value(
        tp,
        "gtos_vnext_same_symbol_lifecycle_reason",
        decision.reason,
    )
    if decision.parent_ticket is not None:
        set_trade_value(
            tp,
            "gtos_vnext_same_symbol_lifecycle_parent_ticket",
            decision.parent_ticket,
        )
    if decision.close_ticket is not None:
        set_trade_value(
            tp,
            "gtos_vnext_same_symbol_lifecycle_close_ticket",
            decision.close_ticket,
        )
    if decision.permitted_order_intent:
        return None
    return ExecutionDenial(
        "gate3_circuit_breaker",
        _same_symbol_v4_denial_reason(decision.action, decision.reason),
        {
            **proof,
            "symbol": symbol,
            "symbol_aliases_checked": aliases,
            "pending_intent_paths_checked": pending_source.paths_checked,
            "same_symbol_lifecycle_v4": packet,
            "vnext_contract": "same_symbol_lifecycle_v4_ticket_bound_exposure_gate",
        },
    )


def _same_symbol_v4_denial_reason(action: str, reason: str) -> str:
    if action == "source_required_fail_closed":
        return "same_symbol_lifecycle_v4_source_required_fail_closed"
    if action == "no_trade_duplicate":
        return "same_symbol_lifecycle_v4_duplicate_exposure_rejected"
    if action == "no_trade_hedge_conflict":
        return "same_symbol_lifecycle_v4_hedge_conflict_rejected"
    if action in {"close_existing", "reduce_existing", "close_and_reverse"}:
        return "same_symbol_lifecycle_v4_close_reduce_reverse_required"
    if action in {"cancel_pending", "replace_pending"}:
        return "same_symbol_lifecycle_v4_pending_action_required"
    if "pending" in reason:
        return "same_symbol_lifecycle_v4_pending_conflict_rejected"
    if "scale" in reason:
        return "same_symbol_lifecycle_v4_scale_in_rejected"
    return "same_symbol_lifecycle_v4_duplicate_exposure_rejected"


def _reject_if_concurrent_cap_reached(mt5,
                                      config: dict | None,
                                      trade_params=None) -> Optional[ExecutionDenial]:
    """Block when filled GTOS positions >= ``max_concurrent``.

    Counts cross-symbol filled positions via
    ``concurrent_tracker.get_filled_position_count`` (magic-number filter,
    10s TTL cache). Pending limits are NOT counted (locked decision #3 —
    a pending limit that would overshoot the cap is cancelled cheaply
    at the moment of its fill by this same gate on the next candle).

    For current vNext rows, selected-cell account-risk governance replaces
    old cross-symbol count authority. Same-symbol overlap is handled by the
    explicit vNext lifecycle-conflict gate above until multi-ticket lifecycle
    support is proven.

    Fails OPEN (returns None) on missing MT5 — the daily-loss stop and
    correlation caps are authoritative; this gate is additive protection.
    """
    if mt5 is None:
        return None
    governed, proof = _vnext_risk_budget_governed_trade(trade_params)
    if governed:
        logger.info(
            "vNext selected-cell risk budget governs concurrency; old count cap "
            "is evidence-only: %s",
            proof,
        )
        return None
    try:
        count = get_filled_position_count(mt5)
    except Exception as e:  # noqa: BLE001 — fail open on tracker error
        logger.warning("concurrent cap check failed, letting trade through: %s", e)
        return None
    cap = resolve_max_concurrent(config)
    if count >= cap:
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "concurrent_cap_reached",
            {"filled_positions": count, "max_concurrent": cap},
        )
    return None


def _reject_if_cross_instrument_correlation_excess(
    mt5, config: dict | None, trade_params,
) -> Optional[ExecutionDenial]:
    """Block when 3+ correlated same-direction positions are already open.

    Wraps ``cross_instrument_correlation_gate.evaluate_for_candidate``
    so this gate only surfaces ``ExecutionDenial`` for the REJECT path
    (cluster_size >= min_positions + 1). The softer RISK_REDUCE_HALF
    path is invisible here — the orchestrator re-runs the same check
    at sizing time and applies the multiplier directly.

    Fails OPEN on any unexpected error: this is additive protection;
    the underlying portfolio_risk gate + concurrent cap + DD reduction
    remain authoritative. Conservative defaults guarantee solo-symbol
    canary fixtures (no open positions) never trigger this gate.
    """
    if trade_params is None:
        return None
    tp = getattr(trade_params, "trade_parameters", None)
    if tp is None:
        return None
    direction = getattr(tp, "direction", None)
    if direction not in ("LONG", "SHORT"):
        return None
    candidate_symbol = (config or {}).get("market", {}).get("symbol")
    if not candidate_symbol:
        return None

    try:
        result = _evaluate_cross_instrument_correlation(
            candidate_symbol=candidate_symbol,
            candidate_direction=direction,
            mt5=mt5,
            config=config,
            evaluation_context="permissions_gate3_5_reject_check",
        )
    except Exception as e:  # noqa: BLE001 — fail open
        logger.warning(
            "cross_instrument_corr gate raised; failing open: %s", e,
        )
        return None

    if result.action != "REJECT":
        return None

    return ExecutionDenial(
        "gate3_circuit_breaker",
        "cross_instrument_correlation_excess",
        {
            "candidate_symbol": candidate_symbol,
            "candidate_direction": direction,
            "cluster_size": len(result.correlated_positions),
            "correlated_positions": result.correlated_positions,
            "threshold": result.threshold,
            "min_positions": result.min_positions,
            "reason": result.reason,
        },
    )


def _reject_if_market_whiteboard_v2_blocks(
    trade_params,
    session_state: dict,
    config: dict | None,
    symbol: str,
) -> Optional[ExecutionDenial]:
    """Gate 3.6 - Market Whiteboard V2 hard admission actions.

    The evaluator is disabled unless ``market_whiteboard_v2.enabled`` is true.
    When enabled, source-missing, quarantine, and explicit zero-trade quality
    results reject before Gate 1. Risk-reduction decisions are returned to
    sizing/allocator owners as evidence and do not reject here.
    """
    try:
        decision = _evaluate_market_whiteboard_v2(
            trade_params=trade_params,
            session_state=session_state,
            config=config,
            symbol=symbol,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("market_whiteboard_v2 gate failed closed: %s", exc)
        return ExecutionDenial(
            "gate3_circuit_breaker",
            "market_whiteboard_v2_source_required",
            {
                "symbol": symbol,
                "source_error": str(exc),
                "v4_contract": (
                    "market whiteboard V2 must fail closed when enabled and "
                    "its admission source state cannot be evaluated"
                ),
            },
        )

    if decision is None or decision.action not in _MARKET_WHITEBOARD_V2_HARD_ACTIONS:
        return None

    reason_by_action = {
        "SOURCE_REQUIRED": "market_whiteboard_v2_source_required",
        "QUARANTINE": "market_whiteboard_v2_symbol_session_quarantine",
        "NO_TRADE": "market_whiteboard_v2_zero_trade_by_evidence",
    }
    return ExecutionDenial(
        "gate3_circuit_breaker",
        reason_by_action.get(decision.action, "market_whiteboard_v2_rejected"),
        decision.to_dict(),
    )


def _reject_if_dormant(config: dict | None, symbol: str) -> Optional[ExecutionDenial]:
    """Block when ``pipeline_state/dormant_state.json`` is set for today.

    The orchestrator writes this marker on MTM daily-loss breach. The gate
    honors it until the marker's ``dormant_until_utc_day`` != today (cleared
    by ``_new_day``'s ``clear_if_stale()`` call). This path is what keeps
    a mid-day restart from resuming trading after a 4% stop.
    """
    if not is_dormant_today():
        return None
    state = load_dormant_state() or {}
    return ExecutionDenial(
        "gate3_circuit_breaker",
        "daily_loss_stop_dormant",
        {
            "dormant_until_utc_day": state.get("dormant_until_utc_day"),
            "triggered_at_utc": state.get("triggered_at_utc"),
            "trigger_reason": state.get("trigger_reason"),
            "equity_at_trigger": state.get("equity_at_trigger"),
            "daily_pnl_pct_at_trigger": state.get("daily_pnl_pct_at_trigger"),
            "symbol": symbol,
        },
    )


def _find_target_ob(tp, mso, risk_cfg: dict | None = None):
    """Return the matched H1 OB for *tp* or None.

    An OB matches when:
    - direction matches (bullish OB for LONG, bearish OB for SHORT)
    - it is unmitigated
    - entry_price lies within [ob.low - tol, ob.high + tol] where
      tol = risk_cfg.sl_buffer_dollars (default 0.02). The tolerance
      tracks the OB-boundary broker-spread buffer used elsewhere in the
      pipeline so a price one spread-tick outside a matched OB still maps
      to it. The touch-count gate is a statistical filter, not a precision
      gate — matching an entry that sits just outside the edge to the
      adjacent OB is the safer choice because it lets downstream gates
      see the stale-zone signal.

    If multiple match, returns the one with the HIGHEST touch_count so the
    gate rejects on the worst-case OB associated with the entry. This is the
    conservative choice: if any matching OB is stale, the setup is stale.
    """
    if not tp or not mso or not hasattr(mso, "timeframes"):
        return None
    h1_tf = mso.timeframes.get("H1") if isinstance(mso.timeframes, dict) else None
    if h1_tf is None:
        return None
    ob_list = getattr(h1_tf, "order_blocks", []) or []
    expected_type = "bullish" if tp.direction == "LONG" else "bearish"
    ob_tol = (risk_cfg or {}).get("sl_buffer_dollars", 0.02)

    matches = []
    for ob in ob_list:
        if getattr(ob, "mitigated", False):
            continue
        if getattr(ob, "type", None) != expected_type:
            continue
        if ob.low - ob_tol <= tp.entry_price <= ob.high + ob_tol:
            matches.append(ob)

    if not matches:
        return None
    # Conservative: if the entry price sits in multiple overlapping zones,
    # pick the most-touched one so stale zones cannot be masked by a fresh
    # overlapping zone.
    return max(matches, key=lambda ob: getattr(ob, "touch_count", 0))


# Liquidity-pool types recognized by the SL-behind-cluster gate. These are
# the deterministic, same-side structural liquidity references detected by
# Component 2 that the Apr 16 NY -1R loss showed are primary sweep targets
# when an SL is placed just above (SHORT) or below (LONG) them. Intraday
# wicks and FVGs are excluded — they are not structural pools.
_LIQUIDITY_CLUSTER_POOL_TYPES = frozenset({
    "equal_highs", "equal_lows",
    "pdh", "pdl",
    "asian_high", "asian_low",
    "session_high", "session_low",
    "london_high", "london_low",
})


def _reject_if_touch_count_too_high(pa, tp, mso, risk_cfg: dict | None = None,
                                     gate1_cfg: dict | None = None,
                                     symbol: str = "XAUUSD") -> Optional[ExecutionDenial]:
    """Reject trades whose target H1 OB has touch_count >= threshold.

    The threshold is configurable via ``gate1.touch_count_reject_threshold``.
    Default: 2 (reject at touch_count >= 2). The configurable knob (added
    2026-04-25) lets us flip the threshold via 1-line config change once
    we have ≥30 production rejection events / ≥6 weeks live data — but
    for Monday 2026-04-27 FTMO challenge launch the safe value is 2.

    Evidence — THREE orthogonal lines:

    (1) Founding population-walk: Touch-1 OB retest WR = 72.7% (n=23,575)
        vs Touch-2+ = 31.5% (n=82,572). The 31% cliff motivates the
        ``>= 2`` threshold because a stale zone is structurally different —
        the Osler stop-cascade has already fired on the first retest.

    (2) Wave 1 audit (A11) realized-R counterfactual on filled CANDs
        post-V3: pooled A1+A2 (~13 weeks Jan 7 – Apr 10 2026, n=93 deduped)
        suggested touch=2 had highest point-estimate Exp R (+0.439R) and
        recommended LOOSEN_TO_3. ``research/touch_count_audit/REVIEWER_PASS.md``
        (A19) independently re-derived the same point estimates AND
        REJECTED the recommendation: stratifying by half, the touch=2
        advantage is H1-2026-driven and **REVERSES in H2 2026** — touch=2
        Exp R = -0.688R (n=8) in Mar-Apr 2026, vs +0.022R for touch=1.
        LOOSEN_TO_3 in H2 regime delivered -6.00R vs status-quo's -0.50R.
        Pairwise tests fail Bonferroni (p=1.0); statistical power for
        δ=0.20R at n=98 is ~10%. Audit verdict: keep at 2 for Monday.

    (3) ADR-005 path: shadow logger collects live touch distribution +
        AI accept rates from Monday onward. ``log_touch_count_gate_decision``
        from ``src/components/touch_count_gate_logger.py`` writes one
        JSONL row per ``ob_retest`` evaluation regardless of pass/reject
        outcome to ``shadow_logs/touch_count_gate_decisions.jsonl``.
        Re-evaluate the threshold after ≥30 production rejections /
        ≥6 weeks live data, drawn from the actual production regime —
        not from the H1-2026-dominated backtest sample that the
        LOOSEN_TO_3 audit relied on.

    Threshold semantics (KEEP at 2 for Monday):
      - default 2: rejects touches >= 2 (touch=1 passes; touch=0 passes)
      - knob: ``gate1.touch_count_reject_threshold`` in ``agent_config.yaml``
        (configurable; reviewed 2026-04-25 + REJECTED LOOSEN_TO_3 by A19
        due to H1/H2 regime reversal). Flip once ADR-005 shadow logger
        accumulates ≥30 production events / ≥6 weeks live coverage.

    Only applies when framework=ob_retest. If MSO has no matching OB for
    the entry_price, the gate silently PASSES (it is not a framework
    conformance check — that is done elsewhere). Both PASS and REJECT
    decisions are written to the ADR-005 shadow log so the analyst can
    compute REJECT-rate-per-cohort and stratify the touch_count
    distribution among accepted CANDs.
    """
    if getattr(pa, "framework", None) != "ob_retest":
        return None

    threshold = int((gate1_cfg or {}).get("touch_count_reject_threshold", 2))
    target = _find_target_ob(tp, mso, risk_cfg=risk_cfg)

    if target is None:
        # Silent pass: gate is a statistical filter, not a framework
        # conformance check. We still log the decision so the analyst
        # can see the cohort of CANDs that bypass the gate because no
        # H1 OB matched the entry price (atr_fallback / non-OB SL path).
        log_touch_count_gate_decision(
            symbol=symbol,
            framework="ob_retest",
            target_ob=None,
            threshold=threshold,
            decision="PASS",
            mso=mso,
        )
        return None

    touches = int(getattr(target, "touch_count", 0) or 0)
    if touches >= threshold:
        log_touch_count_gate_decision(
            symbol=symbol,
            framework="ob_retest",
            target_ob=target,
            threshold=threshold,
            decision="REJECT",
            mso=mso,
        )
        return ExecutionDenial(
            "gate1_safety",
            "touch_count_too_high",
            {
                "touch_count": touches,
                "threshold": threshold,
                "ob_low": target.low,
                "ob_high": target.high,
                "ob_type": getattr(target, "type", None),
                "entry_price": tp.entry_price,
            },
        )

    log_touch_count_gate_decision(
        symbol=symbol,
        framework="ob_retest",
        target_ob=target,
        threshold=threshold,
        decision="PASS",
        mso=mso,
    )
    return None


def _ob_retest_sl_exception_applies(pa, tp, mso, risk_cfg: dict, gate1_cfg: dict) -> bool:
    """Return True if the ob_retest structural SL exception should bypass the sl_floor check.

    The sl_floor rejects SLs tighter than the P25 historical OB width to filter noise.
    For ob_retest, the SL at the OB boundary is the structural invalidation point —
    a narrow OB is a precise entry, not a risky SL. This exception bypasses the floor
    when SL is confirmed structurally placed beyond the matched H1 OB boundary.

    Conditions (all must be true):
    1. gate1.ob_retest_sl_exception is enabled in config
    2. pa.framework == "ob_retest"
    3. A matching unmitigated H1 OB of correct type (bullish for LONG,
       bearish for SHORT) is found in mso near entry_price
    4. SL is below ob.low (LONG) or above ob.high (SHORT)
    5. SL has at least ob_retest_sl_min_buffer_atr * M15_ATR of distance
       beyond the OB boundary (liquidity sweep margin)
    """
    if not gate1_cfg.get("ob_retest_sl_exception", False):
        return False
    if getattr(pa, "framework", None) != "ob_retest":
        return False

    h1_tf = mso.timeframes.get("H1") if hasattr(mso, "timeframes") else None
    ob_list = getattr(h1_tf, "order_blocks", []) if h1_tf else []
    ob_tol = risk_cfg.get("sl_buffer_dollars", 0.02)

    # Minimum buffer below/above OB boundary to survive liquidity sweeps.
    # Stops clustered at the OB boundary are the primary sweep target —
    # 0.3 ATR clears the typical retail stop-hunt zone.
    m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
    m15_atr = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0
    min_buffer_mult = gate1_cfg.get("ob_retest_sl_min_buffer_atr", 0.3)
    min_buffer = m15_atr * min_buffer_mult if m15_atr > 0 else 0

    expected_ob_type = "bullish" if tp.direction == "LONG" else "bearish"

    for ob in ob_list:
        if ob.mitigated:
            continue
        if getattr(ob, "type", None) != expected_ob_type:
            continue
        if ob.low - ob_tol <= tp.entry_price <= ob.high + ob_tol:
            if tp.direction == "LONG" and tp.stop_loss < ob.low:
                buffer = ob.low - tp.stop_loss
                if min_buffer > 0 and buffer < min_buffer:
                    logger.info(
                        "ob_retest SL exception rejected (sweep margin): "
                        "SL buffer=%.5f below OB low, need %.1f*ATR=%.5f",
                        buffer, min_buffer_mult, min_buffer,
                    )
                    return False
                logger.info(
                    "ob_retest SL exception matched: %s OB [%.5f–%.5f], SL=%.5f",
                    ob.type, ob.low, ob.high, tp.stop_loss,
                )
                return True
            if tp.direction == "SHORT" and tp.stop_loss > ob.high:
                buffer = tp.stop_loss - ob.high
                if min_buffer > 0 and buffer < min_buffer:
                    logger.info(
                        "ob_retest SL exception rejected (sweep margin): "
                        "SL buffer=%.5f above OB high, need %.1f*ATR=%.5f",
                        buffer, min_buffer_mult, min_buffer,
                    )
                    return False
                logger.info(
                    "ob_retest SL exception matched: %s OB [%.5f–%.5f], SL=%.5f",
                    ob.type, ob.low, ob.high, tp.stop_loss,
                )
                return True
    return False


def _evaluate_ob_retest_sl_exception(pa, tp, mso, risk_cfg: dict,
                                     gate1_cfg: dict) -> OBRetestSLExceptionDecision:
    """Evaluate structural SL exception and expose decision evidence."""
    base_details = {
        "framework": getattr(pa, "framework", None),
        "direction": getattr(tp, "direction", None),
        "entry_price": getattr(tp, "entry_price", None),
        "stop_loss": getattr(tp, "stop_loss", None),
        "structural_override": False,
        "bypassed_gates": [],
        "preserved_gates": ["sweep_margin_min_buffer_atr"],
    }
    if not gate1_cfg.get("ob_retest_sl_exception", False):
        return OBRetestSLExceptionDecision(
            False, "ob_retest_sl_exception_disabled", base_details,
        )
    if getattr(pa, "framework", None) != "ob_retest":
        return OBRetestSLExceptionDecision(
            False, "framework_not_ob_retest", base_details,
        )

    h1_tf = mso.timeframes.get("H1") if hasattr(mso, "timeframes") else None
    ob_list = getattr(h1_tf, "order_blocks", []) if h1_tf else []
    ob_tol = risk_cfg.get("sl_buffer_dollars", 0.02)

    m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
    m15_atr = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0
    min_buffer_mult = gate1_cfg.get("ob_retest_sl_min_buffer_atr", 0.3)
    min_buffer = m15_atr * min_buffer_mult if m15_atr > 0 else 0
    base_details.update({
        "m15_atr": m15_atr,
        "ob_retest_sl_min_buffer_atr": min_buffer_mult,
        "min_buffer_required": min_buffer,
        "ob_match_tolerance": ob_tol,
    })

    expected_ob_type = "bullish" if tp.direction == "LONG" else "bearish"
    found_expected_type = False
    found_matching_entry = False
    found_boundary_sl = False

    for ob in ob_list:
        if getattr(ob, "mitigated", False):
            continue
        if getattr(ob, "type", None) != expected_ob_type:
            continue
        found_expected_type = True
        if ob.low - ob_tol <= tp.entry_price <= ob.high + ob_tol:
            found_matching_entry = True
            ob_details = dict(base_details)
            ob_details.update({
                "ob_type": getattr(ob, "type", None),
                "ob_low": getattr(ob, "low", None),
                "ob_high": getattr(ob, "high", None),
                "ob_mitigated": getattr(ob, "mitigated", False),
            })
            if tp.direction == "LONG" and tp.stop_loss < ob.low:
                found_boundary_sl = True
                buffer = ob.low - tp.stop_loss
                ob_details.update({
                    "sl_boundary_buffer": buffer,
                    "sweep_margin_status": "PASS",
                })
                if min_buffer > 0 and buffer < min_buffer:
                    ob_details["sweep_margin_status"] = "FAIL"
                    return OBRetestSLExceptionDecision(
                        False, "sweep_margin_too_small", ob_details,
                    )
                ob_details["structural_override"] = True
                return OBRetestSLExceptionDecision(
                    True, "matched_structural_sl_exception", ob_details,
                )
            if tp.direction == "SHORT" and tp.stop_loss > ob.high:
                found_boundary_sl = True
                buffer = tp.stop_loss - ob.high
                ob_details.update({
                    "sl_boundary_buffer": buffer,
                    "sweep_margin_status": "PASS",
                })
                if min_buffer > 0 and buffer < min_buffer:
                    ob_details["sweep_margin_status"] = "FAIL"
                    return OBRetestSLExceptionDecision(
                        False, "sweep_margin_too_small", ob_details,
                    )
                ob_details["structural_override"] = True
                return OBRetestSLExceptionDecision(
                    True, "matched_structural_sl_exception", ob_details,
                )

    if not ob_list:
        reason = "no_h1_order_blocks"
    elif not found_expected_type:
        reason = "no_matching_ob_type"
    elif not found_matching_entry:
        reason = "entry_not_inside_matching_h1_ob"
    elif not found_boundary_sl:
        reason = "sl_not_beyond_ob_boundary"
    else:
        reason = "no_matching_structural_sl_exception"
    return OBRetestSLExceptionDecision(False, reason, base_details)


def _log_ob_retest_sl_exception_decision(
    *,
    symbol: str,
    gate_context: str,
    decision: OBRetestSLExceptionDecision,
    sl_distance: float,
    blocked_threshold: float,
) -> None:
    """Record structural-SL exception decisions without affecting permission flow."""
    try:
        details = dict(decision.details)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "symbol": symbol,
            "gate_context": gate_context,
            "applies": decision.applies,
            "reason": decision.reason,
            "sl_distance": sl_distance,
            "blocked_threshold": blocked_threshold,
            **details,
        }
        log_path = Path(OB_RETEST_SL_EXCEPTION_LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to write ob_retest SL exception decision log (non-blocking): %s",
            exc,
        )


def _log_liquidity_distance(pa, tp, m15_atr: float, margin_required: float,
                            pools_checked: list, decision: str) -> None:
    """Append a shadow-log record for SL-vs-liquidity distance analysis.

    Observation-only. Writes a JSONL record regardless of the gate's
    enabled/disabled state so the CEO can measure false-rejection rate
    before flipping `gate1.sl_liquidity_cluster_enabled` to true.

    Wrapped in try/except — logging failures must never crash the gate.
    """
    try:
        log_dir = Path("shadow_logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "liquidity_distance_log.jsonl"

        reasoning = getattr(pa, "reasoning", None)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": tp.direction,
            "entry_price": tp.entry_price,
            "stop_loss": tp.stop_loss,
            "take_profit_1": getattr(tp, "take_profit_1", None),
            "framework": getattr(pa, "framework", None),
            "setup_grade": reasoning.setup_grade if reasoning else None,
            "m15_atr": m15_atr,
            "margin_required": margin_required,
            "pools_checked": pools_checked,
            "decision": decision,
        }

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(
            "Failed to write liquidity_distance_log (non-blocking): %s", e,
        )


def _reject_if_sl_behind_liquidity_cluster(pa, tp, mso,
                                           config: dict | None = None) -> Optional[ExecutionDenial]:
    """Reject when SL sits within N*M15_ATR of a same-side structural liquidity pool.

    Evidence (Apr 16 NY -1R): XAUUSD LONG SL @ 4788.08 sat 0.05 pts below a
    detected equal_lows pool @ 4788.13. Price swept to 4785.05 and took the
    stop. The MSO had the pool data; no gate consumed it.

    Behavior:
    - LONG: for each pool where pool.side == "low" AND pool.price <= entry,
      require |pool.price - stop_loss| >= margin_required to pass.
    - SHORT: mirrored — pool.side == "high", pool.price >= entry.
    - Only pool types in _LIQUIDITY_CLUSTER_POOL_TYPES are considered.
    - margin_required = m15_atr * gate1.sl_liquidity_cluster_margin_atr.
    - If m15_atr <= 0 or there are no pools, the gate silently passes (no log).
    - Iteration order follows the MSO; the FIRST violating pool is returned.
    - Shadow log is written unconditionally when any pool is checked so the
      CEO can measure decision-vs-gate before enabling.
    - enabled flag from gate1.sl_liquidity_cluster_enabled; when False the
      gate always returns None but still writes the shadow log.

    Ships DISABLED by default — CEO flips to true after shadow-log review.
    """
    if tp is None or mso is None:
        return None
    if tp.direction not in ("LONG", "SHORT"):
        return None

    gate1_cfg = (config or {}).get("gate1", {})
    enabled = bool(gate1_cfg.get("sl_liquidity_cluster_enabled", False))
    margin_atr_mult = gate1_cfg.get("sl_liquidity_cluster_margin_atr", 0.5)

    # Pull M15 ATR defensively (no crash on missing timeframe).
    m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
    m15_atr = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0
    try:
        m15_atr = float(m15_atr)
    except Exception:
        return None
    if m15_atr <= 0:
        return None

    pools = getattr(mso, "liquidity_pools", None)
    if not pools:
        return None

    margin_required = m15_atr * float(margin_atr_mult)

    pools_checked: list = []
    first_violating_pool = None

    for pool in pools:
        pool_type = getattr(pool, "type", None)
        if pool_type not in _LIQUIDITY_CLUSTER_POOL_TYPES:
            continue
        pool_side = getattr(pool, "side", None)
        try:
            pool_price = float(getattr(pool, "price"))
        except Exception:
            continue

        # Same-side filter: LONG cares about lows at or below entry;
        # SHORT cares about highs at or above entry.
        if tp.direction == "LONG":
            if pool_side != "low":
                continue
            if pool_price > tp.entry_price:
                continue
        else:  # SHORT
            if pool_side != "high":
                continue
            if pool_price < tp.entry_price:
                continue

        distance = abs(pool_price - tp.stop_loss)
        violating = distance < margin_required
        pools_checked.append({
            "type": pool_type,
            "side": pool_side,
            "price": pool_price,
            "distance_to_sl": distance,
            "violating": violating,
        })
        if violating and first_violating_pool is None:
            first_violating_pool = pool

    # Shadow log is written whenever any same-side pool was checked.
    decision = "pass"
    if first_violating_pool is not None:
        decision = "reject" if enabled else "would_reject"

    if pools_checked:
        _log_liquidity_distance(
            pa, tp, m15_atr, margin_required, pools_checked, decision,
        )

    if first_violating_pool is None:
        return None

    if not enabled:
        return None

    return ExecutionDenial(
        "gate1_safety",
        "sl_behind_liquidity_cluster",
        {
            "direction": tp.direction,
            "stop_loss": tp.stop_loss,
            "entry_price": tp.entry_price,
            "pool_type": getattr(first_violating_pool, "type", None),
            "pool_price": getattr(first_violating_pool, "price", None),
            "pool_side": getattr(first_violating_pool, "side", None),
            "distance_to_sl": abs(
                float(getattr(first_violating_pool, "price")) - tp.stop_loss
            ),
            "margin_required": margin_required,
            "m15_atr": m15_atr,
            "margin_atr_mult": float(margin_atr_mult),
        },
    )


def _gate1_safety_checks(trade_params, mso, session_state,
                         config: dict | None = None,
                         symbol: str = "XAUUSD") -> Optional[ExecutionDenial]:
    """Deterministic safety checks on trade parameters.

    Operates on PrimaryAnalysisOutput-style objects or dicts.
    trade_params: PrimaryAnalysisOutput (has .reasoning, .trade_parameters)
    mso: MarketStateObject
    symbol: passed through to ADR-005 touch-count shadow logger so
        per-instrument cohorts can be split in analysis.
    """
    risk_cfg = (config or {}).get("risk", {})

    # Extract reasoning — trade_params here is actually the full PA output
    pa = trade_params
    reasoning = getattr(pa, "reasoning", None)

    grade = reasoning.setup_grade if reasoning else "C"
    if grade not in ("A+", "A"):
        return ExecutionDenial("gate1_safety", f"below_grade_threshold: {grade}",
                               {"grade": grade})

    tp = getattr(pa, "trade_parameters", None)
    if not tp:
        return ExecutionDenial("gate1_safety", "no_trade_parameters", {})
    vnext_geometry = _vnext_dynamic_geometry_context(tp)

    # Use deterministic bias from orchestrator (not AI's self-reported bias)
    daily_dir = session_state.get("deterministic_bias", "")
    if not daily_dir:
        # Fallback to AI's bias if deterministic not available
        daily_dir = reasoning.daily_bias.direction if reasoning else "ranging"
    if daily_dir == "bullish" and tp.direction == "SHORT":
        return ExecutionDenial("gate1_safety", "direction_mismatch",
                               {"direction": tp.direction, "daily_bias": daily_dir})
    if daily_dir == "bearish" and tp.direction == "LONG":
        return ExecutionDenial("gate1_safety", "direction_mismatch",
                               {"direction": tp.direction, "daily_bias": daily_dir})

    # --- Multi-touch OB rejection (ob_retest framework only) ------------------
    # Evidence: Touch-1 OB retest WR 72.7% (n=23,575) vs Touch-2+ 31.5%
    # (n=82,572) — founding population-walk. Wave 1 audit
    # (research/touch_count_audit/, see analyze_output.txt) showed realized-R
    # inversion on filled CANDs post-V3 prompt: touch=2 is the BEST stratum
    # (A1 Exp +0.300R/n=25, A2 Exp +0.875R/n=8). Threshold loosened 2 -> 3
    # default 2026-04-25 for FTMO paid challenge; knob:
    # gate1.touch_count_reject_threshold. Placed BEFORE SL/TP geometry
    # validation so stale zones are cut from the funnel early. Silently
    # passes for non-ob_retest frameworks and when no matching OB is found
    # in the MSO.
    gate1_cfg = (config or {}).get("gate1", {})
    denial = _reject_if_touch_count_too_high(pa, tp, mso,
                                              risk_cfg=risk_cfg,
                                              gate1_cfg=gate1_cfg,
                                              symbol=symbol)
    if denial:
        return denial

    # --- Inverted TP/SL geometry gate before any price validation ------------
    # WF-1 inverted-geometry replay found corrected candidates had negative
    # expectancy (-0.325R avg). Default policy is therefore reject; explicit
    # ``risk.inverted_geometry_policy: auto_correct`` remains as rollback.
    min_rr = risk_cfg.get("min_rr", 1.5)
    inverted_long = tp.direction == "LONG" and (
        tp.stop_loss > tp.entry_price or tp.take_profit_1 <= tp.entry_price
    )
    inverted_short = tp.direction == "SHORT" and (
        tp.stop_loss < tp.entry_price or tp.take_profit_1 >= tp.entry_price
    )
    if inverted_long or inverted_short:
        _log_inverted_tp(tp, pa)
        details = {
            "direction": tp.direction,
            "entry": tp.entry_price,
            "stop_loss": tp.stop_loss,
            "take_profit_1": tp.take_profit_1,
            "policy": risk_cfg.get("inverted_geometry_policy", "reject"),
            "source_path": "knowledge_base/wf1_inverted_tp_analysis.md",
            "source_line_no": 10,
            "corrected_avg_r": -0.325,
            "corrected_total_r": -1.95,
            "inverted_candidate_rate_pct": 7.03,
        }
        policy = str(details["policy"] or "reject").strip().lower()
        if policy not in {"auto_correct", "autocorrect", "mirror"}:
            return ExecutionDenial(
                "gate1_safety",
                "inverted_tp_sl_blocked_negative_expectancy",
                details,
            )

    if inverted_long:
        raw_sl_dist = abs(tp.entry_price - tp.stop_loss)
        if raw_sl_dist > 0:
            tp.stop_loss = tp.entry_price - raw_sl_dist
            tp.take_profit_1 = tp.entry_price + min_rr * raw_sl_dist
            tp.risk_reward_ratio = min_rr
            logger.info("Auto-corrected LONG geometry: SL=%.5f, TP1=%.5f",
                         tp.stop_loss, tp.take_profit_1)
        else:
            return ExecutionDenial("gate1_safety", "zero_sl_distance_after_inversion",
                                   {"entry": tp.entry_price, "stop_loss": tp.stop_loss})
    elif inverted_short:
        raw_sl_dist = abs(tp.stop_loss - tp.entry_price)
        if raw_sl_dist > 0:
            tp.stop_loss = tp.entry_price + raw_sl_dist
            tp.take_profit_1 = tp.entry_price - min_rr * raw_sl_dist
            tp.risk_reward_ratio = min_rr
            logger.info("Auto-corrected SHORT geometry: SL=%.5f, TP1=%.5f",
                         tp.stop_loss, tp.take_profit_1)
        else:
            return ExecutionDenial("gate1_safety", "zero_sl_distance_after_inversion",
                                   {"entry": tp.entry_price, "stop_loss": tp.stop_loss})

    # --- Liquidity-cluster SL gate (Apr 16 regression) ------------------------
    # Deterministic check: reject when SL sits within N*M15_ATR of a same-side
    # structural liquidity pool (equal_highs/lows, PDH/PDL, session extremes).
    # Runs AFTER inverted-TP rejection or explicit auto-correction rollback so
    # corrected SLs are evaluated only when the rollback policy is enabled,
    # BEFORE the RR check so we can short-circuit cleanly. Ships DISABLED —
    # shadow log collects pool_distance data while the CEO calibrates.
    denial = _reject_if_sl_behind_liquidity_cluster(pa, tp, mso, config=config)
    if denial:
        return denial

    # Phase 1 validated: 1.5R TP optimal. Accept R:R >= 1.3 (tolerance for rounding)
    if tp.risk_reward_ratio < 1.3:
        return ExecutionDenial("gate1_safety", f"rr_too_low: {tp.risk_reward_ratio:.1f}",
                               {"rr": tp.risk_reward_ratio})

    sl_distance = abs(tp.entry_price - tp.stop_loss)

    # Validate actual TP1 distance (not just self-reported R:R)
    if sl_distance > 0 and tp.take_profit_1:
        tp1_distance = abs(tp.take_profit_1 - tp.entry_price)
        tp1_r = tp1_distance / sl_distance
        # TP1 below entry is always invalid (should not happen after auto-correction)
        if tp.direction == "LONG" and tp.take_profit_1 <= tp.entry_price:
            return ExecutionDenial("gate1_safety",
                                   f"tp1_below_entry: TP1={tp.take_profit_1:.2f} <= entry={tp.entry_price:.2f}",
                                   {"tp1": tp.take_profit_1, "entry": tp.entry_price})
        if tp.direction == "SHORT" and tp.take_profit_1 >= tp.entry_price:
            return ExecutionDenial("gate1_safety",
                                   f"tp1_above_entry: TP1={tp.take_profit_1:.2f} >= entry={tp.entry_price:.2f}",
                                   {"tp1": tp.take_profit_1, "entry": tp.entry_price})
        # Phase 1 legacy rows targeted 1.5R with a 2R ceiling. vNext
        # production rows may carry a dynamic final target (for example
        # partial_be_runner at 3R), so the upper bound must follow the selected
        # execution policy instead of re-imposing the stale static target. Keep
        # a small vNext-only R tolerance for broker tick rounding.
        if tp1_r < 1.3:
            return ExecutionDenial("gate1_safety",
                                   f"tp1_too_close: TP1 at {tp1_r:.2f}R (min 1.3R)",
                                   {"tp1_r": round(tp1_r, 2), "tp1": tp.take_profit_1,
                                    "sl_distance": round(sl_distance, 2)})
        max_tp1_r = 2.0
        vnext_tp1_tolerance_r = 0.0
        if vnext_geometry["active"] and vnext_geometry.get("final_target_r"):
            vnext_tp1_tolerance_r = 0.05
            max_tp1_r = max(
                max_tp1_r,
                float(vnext_geometry["final_target_r"]) + vnext_tp1_tolerance_r,
            )
        if tp1_r > max_tp1_r:
            details = {"tp1_r": round(tp1_r, 2), "tp1": tp.take_profit_1,
                       "sl_distance": round(sl_distance, 2)}
            if vnext_geometry["active"]:
                details.update({
                    "gtos_vnext_dynamic_policy_selected": vnext_geometry.get("selected_policy"),
                    "gtos_vnext_dynamic_final_target_r": vnext_geometry.get("final_target_r"),
                    "gtos_vnext_dynamic_tp1_tolerance_r": vnext_tp1_tolerance_r,
                    "gtos_vnext_gate1_mode": "dynamic_final_target_aware",
                })
            return ExecutionDenial("gate1_safety",
                                   f"tp1_too_far: TP1 at {tp1_r:.2f}R (max {max_tp1_r:.2f}R)",
                                   details)

    # SL absolute minimum — from config with instrument override
    gate1_cfg = (config or {}).get("gate1", {})
    m15_tf = mso.timeframes.get("M15") if hasattr(mso, "timeframes") else None
    m15_atr = getattr(m15_tf, "atr_14", 0) or 0 if m15_tf else 0
    sl_exception_decision = _evaluate_ob_retest_sl_exception(
        pa, tp, mso, risk_cfg, gate1_cfg,
    )

    sl_floor = risk_cfg.get("sl_absolute_min", 5.0)
    if sl_distance < sl_floor:
        if not sl_exception_decision.applies:
            _log_ob_retest_sl_exception_decision(
                symbol=symbol,
                gate_context="sl_below_minimum_floor",
                decision=sl_exception_decision,
                sl_distance=sl_distance,
                blocked_threshold=sl_floor,
            )
            return ExecutionDenial("gate1_safety",
                                   f"sl_below_minimum_floor: SL_dist={sl_distance:.5f} (min={sl_floor})",
                                   {"sl_distance": sl_distance, "sl_floor": sl_floor,
                                    "ob_retest_sl_exception": sl_exception_decision.details,
                                    "ob_retest_sl_exception_reason": sl_exception_decision.reason})
        sl_exception_decision.details.setdefault("bypassed_gates", []).append(
            "sl_below_minimum_floor"
        )
        _log_ob_retest_sl_exception_decision(
            symbol=symbol,
            gate_context="sl_below_minimum_floor",
            decision=sl_exception_decision,
            sl_distance=sl_distance,
            blocked_threshold=sl_floor,
        )
        logger.info(
            "Gate1: sl_floor bypassed (ob_retest structural SL at OB boundary): "
            "SL_dist=%.5f < floor=%.5f",
            sl_distance, sl_floor,
        )

    if m15_atr > 0 and sl_distance < m15_atr * 1.5:
        if not sl_exception_decision.applies:
            _log_ob_retest_sl_exception_decision(
                symbol=symbol,
                gate_context="sl_too_tight",
                decision=sl_exception_decision,
                sl_distance=sl_distance,
                blocked_threshold=m15_atr * 1.5,
            )
            return ExecutionDenial("gate1_safety",
                                   f"sl_too_tight: SL_dist={sl_distance:.5f} < 1.5*ATR={m15_atr * 1.5:.5f}",
                                   {"sl_distance": sl_distance, "m15_atr": m15_atr,
                                    "ob_retest_sl_exception": sl_exception_decision.details,
                                    "ob_retest_sl_exception_reason": sl_exception_decision.reason})
        sl_exception_decision.details.setdefault("bypassed_gates", []).append(
            "sl_too_tight"
        )
        _log_ob_retest_sl_exception_decision(
            symbol=symbol,
            gate_context="sl_too_tight",
            decision=sl_exception_decision,
            sl_distance=sl_distance,
            blocked_threshold=m15_atr * 1.5,
        )
        logger.info(
            "Gate1: sl_too_tight bypassed (ob_retest structural SL at OB boundary): "
            "SL_dist=%.5f < 1.5*ATR=%.5f",
            sl_distance, m15_atr * 1.5,
        )

    # Max SL distance: 2.5% of entry price (catches abnormally wide stops)
    max_sl_pct = 2.5
    sl_pct = (sl_distance / tp.entry_price) * 100 if tp.entry_price > 0 else 0
    if sl_pct > max_sl_pct:
        return ExecutionDenial("gate1_safety",
                               f"sl_too_wide: SL_dist={sl_distance:.2f} ({sl_pct:.1f}% of price, max {max_sl_pct}%)",
                               {"sl_distance": sl_distance, "sl_pct": round(sl_pct, 2),
                                "max_sl_pct": max_sl_pct})

    return None


def _log_inverted_tp(tp, pa) -> None:
    """Log inverted TP/SL to a dedicated JSONL file for analysis."""
    try:
        log_dir = Path("knowledge_base")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "inverted_tp_log.jsonl"

        reasoning = getattr(pa, "reasoning", None)
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": tp.direction,
            "entry_price": tp.entry_price,
            "stop_loss": tp.stop_loss,
            "take_profit_1": tp.take_profit_1,
            "risk_reward_ratio": tp.risk_reward_ratio,
            "setup_grade": reasoning.setup_grade if reasoning else None,
            "confidence_score": getattr(pa, "confidence_score", None),
            "framework": getattr(pa, "framework", None),
            "daily_bias": reasoning.daily_bias.direction if reasoning else None,
        }

        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

        logger.warning("Inverted TP/SL logged: %s %s entry=%.5f tp1=%.5f sl=%.5f",
                        tp.direction, getattr(pa, "framework", "?"),
                        tp.entry_price, tp.take_profit_1, tp.stop_loss)
    except Exception as e:
        logger.warning("Failed to log inverted TP (non-blocking): %s", e)
