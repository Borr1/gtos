"""Slippage Shadow Logger -- observation-only fill-quality recorder.

Closes the data gap identified by Q71 (worktree agent-ab090bc330ceb62ac,
2026-04-27): zero usable fill records across all sources (160 trade_records,
7 yaml backups, 49 fn_smoke fills) -- requested vs actual fill price was
NEVER persisted, so slippage modelling is impossible.

For every successful market-order fill (direct CANDIDATE or limit-intent
fill, both funnel through ExecutionEngine.open_trade), this writer appends
ONE jsonl row to ``shadow_logs/slippage.jsonl`` capturing:

    {ts, ticket, symbol, direction, requested_price, fill_price,
     slippage_price, slippage_directional, slippage_pips, spread_at_request,
     kill_zone, trigger, notes}

Fields:
    ts                   ISO-8601 UTC timestamp at log emission time.
    ticket               MT5 order ticket (int).
    symbol               Internal symbol key (e.g. "XAUUSD", "US30_cash").
    direction            "LONG" or "SHORT".
    requested_price      The price field the orchestrator submitted in the
                         order request (current ask for LONG, bid for SHORT,
                         OR limit_price for limit-intent fills since the
                         order request still uses the current tick).
    fill_price           ``OrderResult.price`` returned by MT5 -- the actual
                         broker fill price. May be 0.0 on some brokers, in
                         which case execution.py falls back to entry_price;
                         we still log the raw value here for forensic clarity.
    slippage_price       (fill_price - requested_price). Sign-preserving
                         absolute price difference, no normalization.
    slippage_directional Adverse-slippage convention. POSITIVE = bad fill
                         (LONG filled higher than requested, SHORT filled
                         lower than requested). NEGATIVE = favorable.
                         For LONG: fill_price - requested_price.
                         For SHORT: requested_price - fill_price.
    slippage_pips        slippage_directional / pip_size. Null when
                         pip_size is unknown for this symbol.
    spread_at_request    Bid-ask spread at the time of order submission, in
                         the same units as ``TickData.spread_cents``
                         ((ask - bid) * 100). Null if the spread was
                         unavailable.
    kill_zone            Active KZ name when the order was placed, or null.
    trigger              Why this trade fired -- "candidate_market",
                         "limit_fill_inside_kz", "limit_fill_outside_kz",
                         "adopted_after_timeout", or any operator-supplied
                         label. Null when not provided.
    notes                Optional free-text breadcrumb (e.g. fallback
                         flag, comment string from OrderResult, etc.).

CRITICAL DESIGN CONTRACTS:
    1. **Fail-open.** Any exception inside ``record_slippage`` is caught
       and downgraded to a WARNING log. Trade execution MUST NOT block on
       a shadow-log write failure.
    2. **Fast.** Single jsonl line append, no fsync, no serialization
       beyond ``json.dumps``. Targets <1 ms on a modern SSD.
    3. **Schema-stable.** New fields go at the END. Existing field names
       must NEVER change semantics; analysis tooling versions on field
       presence rather than dict shape.

This module is observation-only. It does NOT alter order placement,
retry behaviour, position sizing, or any other trading logic.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

SHADOW_LOG_PATH = "shadow_logs/slippage.jsonl"
_LFS_POINTER_SIGNATURE = "version https://git-lfs.github.com/spec/v1"
_LFS_POINTER_REDIRECT_WARNED: set[str] = set()


# Per-symbol pip size in price units. Used to translate raw price
# differences into pips for human-readable analysis. Symbols not in
# the table get null for ``slippage_pips`` (the raw ``slippage_price``
# is always logged regardless).
#
# Conventions:
#   - FX majors / minors:      0.0001 (4-digit broker pip)
#   - JPY-quote pairs:         0.01   (2-digit broker pip)
#   - XAU/XAG metals:          0.01   (broker convention varies; CEO
#                                       trade-records use 0.01 for XAU)
#   - Index CFDs:              1.0    (1 point = 1 "pip" by convention)
#
# Keys are matched against both the internal symbol key (e.g. "US30_cash")
# AND the prefix-stripped form (e.g. "US30") so broker variants resolve
# without explicit re-mapping.
_PIP_SIZE_BY_SYMBOL: dict[str, float] = {
    # Metals
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    # Indices (point-based)
    "US30": 1.0,
    "US30_cash": 1.0,
    "NAS100": 1.0,
    "NAS100_cash": 1.0,
    # JPY pairs
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "EURJPY": 0.01,
    # Other FX
    "GBPUSD": 0.0001,
    "EURUSD": 0.0001,
    "AUDUSD": 0.0001,
}


def _resolve_pip_size(symbol: str) -> Optional[float]:
    """Return the pip size for ``symbol`` or None if unknown.

    Tries the symbol verbatim, then strips common broker suffixes
    ("_cash", ".cash") so "US30.cash" and "US30_cash" both resolve to
    the "US30" entry above.
    """
    if not symbol:
        return None
    if symbol in _PIP_SIZE_BY_SYMBOL:
        return _PIP_SIZE_BY_SYMBOL[symbol]
    # Strip broker-style suffixes and retry.
    for suffix in ("_cash", ".cash", ".raw"):
        if symbol.endswith(suffix):
            base = symbol[: -len(suffix)]
            if base in _PIP_SIZE_BY_SYMBOL:
                return _PIP_SIZE_BY_SYMBOL[base]
    return None


def _coerce_float_or_none(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_lfs_pointer_file(path: Path) -> bool:
    try:
        if not path.exists():
            return False
        with path.open("r", encoding="utf-8") as handle:
            first_line = handle.readline().strip()
        return first_line == _LFS_POINTER_SIGNATURE
    except Exception:
        return False


def _append_path(path: Path) -> Path:
    if not _is_lfs_pointer_file(path):
        return path
    redirected = path.with_name(f"{path.stem}_runtime{path.suffix}")
    key = str(path)
    if key not in _LFS_POINTER_REDIRECT_WARNED:
        _LFS_POINTER_REDIRECT_WARNED.add(key)
        logger.warning(
            "Slippage shadow log destination is an LFS pointer; redirecting live appends to %s",
            redirected,
        )
    return redirected


def _coerce_int_or_none(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_positive_int_or_none(value: Any) -> Optional[int]:
    coerced = _coerce_int_or_none(value)
    if coerced is None or coerced <= 0:
        return None
    return coerced


def _coerce_str_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


def _source_repair_identity_fields(identity: Optional[dict[str, Any]]) -> dict[str, Optional[str]]:
    identity = identity or {}
    plan_id = _coerce_str_or_none(identity.get("source_repair_plan_row_id"))
    catalog_entry_id = _coerce_str_or_none(
        identity.get("input_numeric_router_catalog_entry_id")
        or identity.get("numeric_router_catalog_entry_id")
    )
    family_spec_id = _coerce_str_or_none(
        identity.get("input_numeric_router_family_spec_id")
        or identity.get("numeric_router_family_spec_id")
    )
    identity_key = "|".join([plan_id, catalog_entry_id, family_spec_id]) if all(
        [plan_id, catalog_entry_id, family_spec_id]
    ) else None
    return {
        "source_repair_plan_row_id": plan_id,
        "input_numeric_router_catalog_entry_id": catalog_entry_id,
        "input_numeric_router_family_spec_id": family_spec_id,
        "source_repair_identity_key": identity_key,
    }


def _time_in_trade_minutes(entry_time: Optional[str], close_time: datetime) -> Optional[int]:
    if not entry_time:
        return None
    try:
        entry_dt = datetime.fromisoformat(str(entry_time).replace("Z", "+00:00"))
    except ValueError:
        return None
    if entry_dt.tzinfo is None:
        entry_dt = entry_dt.replace(tzinfo=timezone.utc)
    return int((close_time - entry_dt.astimezone(timezone.utc)).total_seconds() / 60)


def _parse_utc_or_none(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _r_multiple_for_close(
    *,
    direction: str,
    entry_price: Optional[float],
    close_price: Optional[float],
    sl_distance: Optional[float],
) -> Optional[float]:
    if entry_price is None or close_price is None or not sl_distance:
        return None
    if sl_distance <= 0:
        return None
    if direction == "LONG":
        return round((close_price - entry_price) / sl_distance, 4)
    if direction == "SHORT":
        return round((entry_price - close_price) / sl_distance, 4)
    return None


def _net_r_from_cash_risk(
    *,
    broker_profit: Optional[float],
    commission: Optional[float],
    swap: Optional[float],
    cash_risk_amount: Optional[float],
) -> tuple[Optional[float], Optional[float], str]:
    if broker_profit is None:
        return None, None, "BROKER_PROFIT_SOURCE_NOT_CAPTURED"
    if commission is None or swap is None:
        return None, None, "COMMISSION_OR_SWAP_SOURCE_NOT_CAPTURED"
    if cash_risk_amount is None or cash_risk_amount <= 0:
        return None, None, "CASH_RISK_SOURCE_NOT_CAPTURED"
    net_profit = round(broker_profit + commission + swap, 8)
    return net_profit, round(net_profit / cash_risk_amount, 6), "CAPTURED"


def record_slippage(
    *,
    ticket: int,
    symbol: str,
    direction: str,
    requested_price: float,
    fill_price: float,
    spread_at_request: Optional[float] = None,
    kill_zone: Optional[str] = None,
    trigger: Optional[str] = None,
    notes: Optional[str] = None,
    deal_ticket: Optional[int] = None,
    raw_order_result_fill_price: Optional[float] = None,
    broker_fill_time_utc: Optional[str] = None,
    executed_entry_price: Optional[float] = None,
    executed_exit_price: Optional[float] = None,
    executed_stop_price: Optional[float] = None,
    executed_target_price: Optional[float] = None,
    executed_lot_size: Optional[float] = None,
    commission: Optional[float] = None,
    swap: Optional[float] = None,
    cash_risk_amount: Optional[float] = None,
    partial_exit_lifecycle: Optional[str] = None,
    source_repair_identity: Optional[dict[str, Any]] = None,
    decision_spread: Optional[float] = None,
    decision_spread_unit: Optional[str] = None,
    order_send_spread: Optional[float] = None,
    fill_spread: Optional[float] = None,
    fill_spread_status: Optional[str] = None,
    order_send_time_utc: Optional[str] = None,
    order_result_time_utc: Optional[str] = None,
    reject_or_fill_latency_ms: Optional[float] = None,
    pending_age_seconds: Optional[float] = None,
    pending_candles_elapsed: Optional[int] = None,
    sl_distance: Optional[float] = None,
    slippage_r: Optional[float] = None,
    order_outcome_status: Optional[str] = None,
    dynamic_policy: Optional[str] = None,
    commission_status: Optional[str] = None,
    swap_status: Optional[str] = None,
    account_history_lookup_status: Optional[str] = None,
    account_history_lookup_attempted: Optional[bool] = None,
    account_history_lookup_attempt_count: Optional[int] = None,
    account_history_lookup_window_start_utc: Optional[str] = None,
    account_history_lookup_window_end_utc: Optional[str] = None,
    account_history_lookup_error: Optional[str] = None,
    account_history_lookup_match_keys: Optional[Any] = None,
    fill_price_source_override: Optional[str] = None,
    fill_price_status_override: Optional[str] = None,
    pretrade_cost_model: Optional[Any] = None,
    pretrade_cost_model_status: Optional[str] = None,
    dynamic_exit_action_timeline: Optional[Any] = None,
    log_path: Optional[str] = None,
) -> None:
    """Append one fill-quality row to the slippage shadow log.

    Keyword-only signature so downstream call sites are self-documenting
    and so adding new fields can never change positional ordering.

    All numeric arguments are best-effort; the function NEVER raises.
    On any internal failure a WARNING is emitted and control returns
    to the caller -- live trade execution must not depend on this write.

    Args:
        ticket: MT5 order ticket. May be 0 if the broker did not return
            a ticket (still logged for forensic completeness).
        symbol: Internal symbol key. Used both as a tag and to look up
            the per-symbol pip size for ``slippage_pips`` conversion.
        direction: "LONG" or "SHORT". Determines the sign convention
            for ``slippage_directional`` (positive = adverse).
        requested_price: The price field submitted in the MT5 order
            request. For market orders this is the current ask (LONG)
            or bid (SHORT) at submission. NEVER null; pass 0.0 if truly
            unavailable (which would itself be a bug worth recording).
        fill_price: ``OrderResult.price`` returned by MT5. Some brokers
            return 0.0 on success; the value is logged verbatim so
            downstream analysis can detect that pattern.
        spread_at_request: Bid-ask spread at submission time. Pass None
            if unavailable; do not synthesize a value.
        kill_zone: Active KZ ("london" / "ny" / "tokyo" / etc.) at
            submission time. Pass None outside KZ context.
        trigger: Free-form label describing why this trade was
            submitted. Recommended values: "candidate_market",
            "limit_fill_inside_kz", "limit_fill_outside_kz",
            "adopted_after_timeout".
        notes: Optional free-text. Useful for fallback flags or the
            OrderResult.comment when it carries diagnostic info.
        log_path: Override the default jsonl path. Pass None (the
            default) and the function reads the module-level
            ``SHADOW_LOG_PATH`` constant at call time -- this lets tests
            monkeypatch the module attribute to redirect writes without
            having to thread an explicit ``log_path`` through every call
            site. NEVER overwrites existing data -- writes are
            append-only.
    """
    try:
        # Compute slippage in price units. Some MT5 brokers return
        # OrderResult.price=0.0 for a successful deal; use the already
        # resolved executed entry price for analytics while preserving the
        # raw broker result in explicit forensic fields below.
        try:
            req = float(requested_price) if requested_price is not None else 0.0
            raw_fill = float(fill_price) if fill_price is not None else 0.0
        except (TypeError, ValueError):
            req, raw_fill = 0.0, 0.0

        executed_entry_candidate = _coerce_float_or_none(executed_entry_price)
        raw_order_result_fill_value = _coerce_float_or_none(raw_order_result_fill_price)
        broker_result_fill = (
            raw_order_result_fill_value
            if raw_order_result_fill_value is not None
            else raw_fill
        )
        outcome_status = order_outcome_status or "ORDER_FILLED"
        fill = raw_fill
        fill_price_source = (
            _coerce_str_or_none(fill_price_source_override) or "order_result_price"
        )
        fill_price_status = (
            _coerce_str_or_none(fill_price_status_override) or "CAPTURED"
        )
        if (
            not fill_price_source_override
            and outcome_status == "ORDER_FILLED"
            and broker_result_fill == 0.0
            and raw_fill != 0.0
        ):
            fill = raw_fill
            fill_price_source = "executed_entry_price_fallback_for_zero_order_result"
            fill_price_status = "ZERO_ORDER_RESULT_REPAIRED"
        elif (
            not fill_price_source_override
            and outcome_status == "ORDER_FILLED"
            and broker_result_fill == 0.0
            and executed_entry_candidate is not None
            and executed_entry_candidate != 0.0
        ):
            fill = executed_entry_candidate
            fill_price_source = "executed_entry_price_fallback_for_zero_order_result"
            fill_price_status = "ZERO_ORDER_RESULT_REPAIRED"

        slippage_price = round(fill - req, 8)

        if direction == "LONG":
            slippage_directional = round(fill - req, 8)
        elif direction == "SHORT":
            slippage_directional = round(req - fill, 8)
        else:
            # Unknown direction -- log the raw delta and leave the
            # directional view as None rather than guessing the sign.
            slippage_directional = None

        # Pip conversion. Best-effort -- null is acceptable.
        pip_size = _resolve_pip_size(symbol)
        if pip_size and pip_size > 0 and slippage_directional is not None:
            slippage_pips: Optional[float] = round(
                slippage_directional / pip_size, 4
            )
        else:
            slippage_pips = None

        # Coerce spread to float-or-None; never propagate exotic types
        # into the jsonl line.
        try:
            spread_value: Optional[float] = (
                float(spread_at_request)
                if spread_at_request is not None else None
            )
        except (TypeError, ValueError):
            spread_value = None

        order_ticket_value = _coerce_int_or_none(ticket)
        deal_ticket_value = _coerce_positive_int_or_none(deal_ticket)
        if raw_order_result_fill_value is None:
            raw_order_result_fill_value = raw_fill
        broker_fill_dt = _parse_utc_or_none(broker_fill_time_utc)
        broker_fill_time_value = broker_fill_dt.isoformat() if broker_fill_dt else None
        executed_entry_value = _coerce_float_or_none(
            executed_entry_candidate if executed_entry_candidate is not None else fill
        )
        executed_exit_value = _coerce_float_or_none(executed_exit_price)
        executed_stop_value = _coerce_float_or_none(executed_stop_price)
        executed_target_value = _coerce_float_or_none(executed_target_price)
        executed_lot_value = _coerce_float_or_none(executed_lot_size)
        commission_value = _coerce_float_or_none(commission)
        swap_value = _coerce_float_or_none(swap)
        cash_risk_value = _coerce_float_or_none(cash_risk_amount)
        explicit_commission_status = _coerce_str_or_none(commission_status)
        explicit_swap_status = _coerce_str_or_none(swap_status)
        account_history_status_value = _coerce_str_or_none(account_history_lookup_status)
        if commission_value is not None:
            commission_status_value = "CAPTURED"
        elif explicit_commission_status:
            commission_status_value = explicit_commission_status
        elif account_history_lookup_attempted:
            commission_status_value = "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
        else:
            commission_status_value = "ACCOUNT_HISTORY_REQUIRED"
        if swap_value is not None:
            swap_status_value = "CAPTURED"
        elif explicit_swap_status:
            swap_status_value = explicit_swap_status
        elif account_history_lookup_attempted:
            swap_status_value = "UNRESOLVED_AFTER_HISTORY_ATTEMPT"
        else:
            swap_status_value = "ACCOUNT_HISTORY_REQUIRED"
        decision_spread_value = _coerce_float_or_none(decision_spread)
        order_send_spread_value = _coerce_float_or_none(order_send_spread)
        fill_spread_value = _coerce_float_or_none(fill_spread)
        latency_value = _coerce_float_or_none(reject_or_fill_latency_ms)
        pending_age_value = _coerce_float_or_none(pending_age_seconds)
        sl_distance_value = _coerce_float_or_none(sl_distance)
        slippage_r_value = _coerce_float_or_none(slippage_r)
        if (
            slippage_r_value is None
            and slippage_directional is not None
            and sl_distance_value
            and sl_distance_value > 0
        ):
            slippage_r_value = round(slippage_directional / sl_distance_value, 6)
        try:
            pending_candles_value = (
                int(pending_candles_elapsed)
                if pending_candles_elapsed is not None else None
            )
        except (TypeError, ValueError):
            pending_candles_value = None
        lifecycle_value = partial_exit_lifecycle or "ENTRY_FULL_POSITION_OPENED"
        source_repair_identity_values = _source_repair_identity_fields(source_repair_identity)
        source_repair_identity_status = (
            "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"
            if source_repair_identity_values["source_repair_identity_key"]
            else "NOT_BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"
        )

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "ticket": int(ticket) if ticket is not None else 0,
            "symbol": symbol,
            "direction": direction,
            "requested_price": req,
            "fill_price": fill,
            "raw_order_result_fill_price": raw_order_result_fill_value,
            "raw_order_result_fill_price_status": (
                "CAPTURED" if raw_order_result_fill_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "fill_price_source": fill_price_source,
            "fill_price_status": fill_price_status,
            "slippage_price": slippage_price,
            "slippage_directional": slippage_directional,
            "slippage_pips": slippage_pips,
            "slippage_r": slippage_r_value,
            "spread_at_request": spread_value,
            "decision_spread": decision_spread_value,
            "decision_spread_unit": decision_spread_unit,
            "order_send_spread": order_send_spread_value,
            "fill_spread": fill_spread_value,
            "fill_spread_status": (
                fill_spread_status
                or ("CAPTURED" if fill_spread_value is not None else "SOURCE_NOT_CAPTURED")
            ),
            "order_send_time_utc": order_send_time_utc,
            "order_result_time_utc": order_result_time_utc,
            "reject_or_fill_latency_ms": latency_value,
            "pending_age_seconds": pending_age_value,
            "pending_candles_elapsed": pending_candles_value,
            "kill_zone": kill_zone,
            "trigger": trigger,
            "notes": notes,
            "slippage_event_type": "entry",
            "slippage_schema_version": "entry_slippage_shadow_v3",
            "order_outcome_status": outcome_status,
            "dynamic_policy": dynamic_policy,
            "dynamic_exit_action_timeline": _json_safe(dynamic_exit_action_timeline),
            "source_repair_geometry_contract_version": "numeric_router_source_repair_geometry_v1",
            "order_ticket": order_ticket_value,
            "order_ticket_status": "CAPTURED" if order_ticket_value is not None else "SOURCE_NOT_CAPTURED",
            "deal_ticket": deal_ticket_value,
            "deal_ticket_status": "CAPTURED" if deal_ticket_value is not None else "SOURCE_NOT_CAPTURED",
            "broker_fill_time_utc": broker_fill_time_value,
            "broker_fill_time_utc_status": (
                "CAPTURED" if broker_fill_time_value is not None else "BROKER_DEAL_TIME_SOURCE_NOT_CAPTURED"
            ),
            "executed_entry_price": executed_entry_value,
            "executed_entry_price_status": (
                "CAPTURED" if executed_entry_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "executed_exit_price": executed_exit_value,
            "executed_exit_price_status": (
                "CAPTURED" if executed_exit_value is not None else "NOT_APPLICABLE_ENTRY_EVENT"
            ),
            "executed_stop_price": executed_stop_value,
            "executed_stop_price_status": (
                "CAPTURED" if executed_stop_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "executed_target_price": executed_target_value,
            "executed_target_price_status": (
                "CAPTURED" if executed_target_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "executed_lot_size": executed_lot_value,
            "executed_lot_size_status": (
                "CAPTURED" if executed_lot_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "commission": commission_value,
            "commission_status": commission_status_value,
            "swap": swap_value,
            "swap_status": swap_status_value,
            "cash_risk_amount": cash_risk_value,
            "cash_risk_amount_status": (
                "CAPTURED" if cash_risk_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "account_history_lookup_status": account_history_status_value,
            "account_history_lookup_attempted": bool(account_history_lookup_attempted)
            if account_history_lookup_attempted is not None else None,
            "account_history_lookup_attempt_count": _coerce_int_or_none(
                account_history_lookup_attempt_count
            ),
            "account_history_lookup_window_start_utc": account_history_lookup_window_start_utc,
            "account_history_lookup_window_end_utc": account_history_lookup_window_end_utc,
            "account_history_lookup_error": account_history_lookup_error,
            "account_history_lookup_match_keys": _json_safe(account_history_lookup_match_keys),
            "pretrade_cost_model_status": _coerce_str_or_none(pretrade_cost_model_status),
            "pretrade_cost_model": _json_safe(pretrade_cost_model),
            "partial_exit_lifecycle": lifecycle_value,
            "partial_exit_lifecycle_status": "ENTRY_EVENT_NOT_PARTIAL_EXIT",
            "source_repair_plan_row_id": source_repair_identity_values["source_repair_plan_row_id"],
            "source_repair_plan_row_id_status": (
                "CAPTURED" if source_repair_identity_values["source_repair_plan_row_id"] else "SOURCE_NOT_CAPTURED"
            ),
            "input_numeric_router_catalog_entry_id": source_repair_identity_values[
                "input_numeric_router_catalog_entry_id"
            ],
            "input_numeric_router_catalog_entry_id_status": (
                "CAPTURED"
                if source_repair_identity_values["input_numeric_router_catalog_entry_id"]
                else "SOURCE_NOT_CAPTURED"
            ),
            "input_numeric_router_family_spec_id": source_repair_identity_values[
                "input_numeric_router_family_spec_id"
            ],
            "input_numeric_router_family_spec_id_status": (
                "CAPTURED"
                if source_repair_identity_values["input_numeric_router_family_spec_id"]
                else "SOURCE_NOT_CAPTURED"
            ),
            "source_repair_identity_key": source_repair_identity_values["source_repair_identity_key"],
            "source_repair_identity_key_status": (
                "CAPTURED" if source_repair_identity_values["source_repair_identity_key"] else "SOURCE_NOT_CAPTURED"
            ),
            "source_repair_row_identity_status": source_repair_identity_status,
            "no_execution_effect": True,
        }

        # ``log_path or SHADOW_LOG_PATH`` re-reads the module-level constant
        # at call time so tests can monkeypatch ``SHADOW_LOG_PATH`` to
        # redirect writes without having to pass ``log_path=`` explicitly
        # at every call site (matches the sl_beyond_ob_shadow_logger
        # canonical pattern).
        path = _append_path(Path(log_path or SHADOW_LOG_PATH))
        # mkdir is cheap when the dir already exists (single stat call on
        # most POSIX filesystems; Windows similar). Acceptable on the hot
        # path because the live writer creates this dir once at first call.
        path.parent.mkdir(parents=True, exist_ok=True)
        # Append-only; "a" mode is atomic for short writes on POSIX and
        # Windows when the line fits in a single OS write buffer (which
        # ours always does -- single short jsonl row).
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        # Fail-open contract: NEVER propagate. The live trade has already
        # executed by the time we get here; a logger crash must not
        # corrupt downstream state-machine flow.
        logger.warning(
            "Failed to write slippage shadow log (non-blocking): %s "
            "[ticket=%s symbol=%s direction=%s]",
            e, ticket, symbol, direction,
        )


def record_close_slippage(
    *,
    ticket: int,
    symbol: str,
    direction: str,
    requested_price: Optional[float],
    fill_price: Optional[float],
    close_reason: str,
    close_event_type: Optional[str] = None,
    spread_at_request: Optional[float] = None,
    volume_closed: Optional[float] = None,
    initial_volume: Optional[float] = None,
    remaining_volume: Optional[float] = None,
    entry_price: Optional[float] = None,
    stop_loss: Optional[float] = None,
    sl_distance: Optional[float] = None,
    entry_time: Optional[str] = None,
    sl_at_breakeven: Optional[bool] = None,
    partial_close: bool = False,
    mt5_order_id: Optional[int] = None,
    mt5_deal_id: Optional[int] = None,
    commission: Optional[float] = None,
    swap: Optional[float] = None,
    broker_profit: Optional[float] = None,
    cash_risk_amount: Optional[float] = None,
    executed_target_price: Optional[float] = None,
    source_repair_identity: Optional[dict[str, Any]] = None,
    dynamic_exit_action_timeline: Optional[Any] = None,
    close_comment: Optional[str] = None,
    close_time: Optional[str] = None,
    requested_price_status: Optional[str] = None,
    accounting_source: Optional[str] = None,
    log_path: Optional[str] = None,
) -> None:
    """Append one close-side fill-quality row.

    This is observation-only. It never calls MT5 and never raises. The row is
    written to the same append-only file as entry slippage so ticket-level
    accounting can be joined without another hot-path file.
    """
    try:
        emitted_at = datetime.now(timezone.utc)
        close_time_utc = _parse_utc_or_none(close_time) or emitted_at
        req = _coerce_float_or_none(requested_price)
        fill = _coerce_float_or_none(fill_price)
        slip_price = None
        slip_directional = None
        if req is not None and fill is not None:
            slip_price = round(fill - req, 8)
            if direction == "LONG":
                slip_directional = round(req - fill, 8)
            elif direction == "SHORT":
                slip_directional = round(fill - req, 8)

        pip_size = _resolve_pip_size(symbol)
        if pip_size and pip_size > 0 and slip_directional is not None:
            slippage_pips: Optional[float] = round(slip_directional / pip_size, 4)
        else:
            slippage_pips = None

        spread_value = _coerce_float_or_none(spread_at_request)
        entry_value = _coerce_float_or_none(entry_price)
        stop_value = _coerce_float_or_none(stop_loss)
        sl_dist_value = _coerce_float_or_none(sl_distance)
        volume_value = _coerce_float_or_none(volume_closed)
        initial_volume_value = _coerce_float_or_none(initial_volume)
        remaining_volume_value = _coerce_float_or_none(remaining_volume)
        commission_value = _coerce_float_or_none(commission)
        swap_value = _coerce_float_or_none(swap)
        broker_profit_value = _coerce_float_or_none(broker_profit)
        cash_risk_value = _coerce_float_or_none(cash_risk_amount)
        close_r_multiple = _r_multiple_for_close(
            direction=direction,
            entry_price=entry_value,
            close_price=fill,
            sl_distance=sl_dist_value,
        )
        broker_net_profit, broker_net_r, broker_net_r_status = _net_r_from_cash_risk(
            broker_profit=broker_profit_value,
            commission=commission_value,
            swap=swap_value,
            cash_risk_amount=cash_risk_value,
        )
        cost_adjustment_r = (
            round(broker_net_r - close_r_multiple, 6)
            if broker_net_r is not None and close_r_multiple is not None
            else None
        )
        target_value = _coerce_float_or_none(executed_target_price)
        source_repair_identity_values = _source_repair_identity_fields(source_repair_identity)
        source_repair_identity_status = (
            "BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"
            if source_repair_identity_values["source_repair_identity_key"]
            else "NOT_BOUND_TO_NUMERIC_ROUTER_SOURCE_REPAIR_QUEUE"
        )
        time_minutes = _time_in_trade_minutes(entry_time, close_time_utc)
        mt5_order_value = _coerce_int_or_none(mt5_order_id)
        mt5_deal_value = _coerce_positive_int_or_none(mt5_deal_id)
        ticket_value = _coerce_int_or_none(ticket)
        order_ticket_value = mt5_order_value if mt5_order_value is not None else ticket_value
        broker_fill_time_status = (
            "CAPTURED_FROM_MT5_HISTORY_DEALS"
            if accounting_source == "MT5_HISTORY_DEALS_READONLY" and close_time
            else "EXECUTION_CLOSE_TIME_NOT_BROKER_DEAL_HISTORY"
        )
        partial_lifecycle = "PARTIAL_EXIT" if partial_close else "FULL_EXIT"

        entry = {
            "ts": emitted_at.isoformat(),
            "ticket": int(ticket) if ticket is not None else 0,
            "symbol": symbol,
            "direction": direction,
            "requested_price": req,
            "fill_price": fill,
            "slippage_price": slip_price,
            "slippage_directional": slip_directional,
            "slippage_pips": slippage_pips,
            "spread_at_request": spread_value,
            "kill_zone": None,
            "trigger": close_event_type,
            "notes": close_comment,
            "slippage_event_type": "close",
            "slippage_schema_version": "close_slippage_shadow_v1",
            "directional_slippage_convention": "POSITIVE_IS_ADVERSE_EXIT_FILL",
            "requested_price_status": (
                requested_price_status
                or ("CAPTURED" if req is not None else "SOURCE_NOT_CAPTURED")
            ),
            "close_reason": close_reason,
            "close_event_type": close_event_type,
            "partial_close": bool(partial_close),
            "volume_closed": volume_value,
            "initial_volume": initial_volume_value,
            "remaining_volume": remaining_volume_value,
            "entry_price": entry_value,
            "stop_loss": stop_value,
            "sl_distance": sl_dist_value,
            "close_r_multiple": close_r_multiple,
            "gross_close_r_multiple": close_r_multiple,
            "entry_time": entry_time,
            "close_time": close_time_utc.isoformat(),
            "time_in_trade_minutes": time_minutes,
            "time_in_trade_status": (
                "ENTRY_AND_CLOSE_TIME_CAPTURED"
                if time_minutes is not None else "ENTRY_TIME_SOURCE_NOT_CAPTURED"
            ),
            "sl_at_breakeven": sl_at_breakeven,
            "be_status": (
                "SL_AT_BREAKEVEN"
                if sl_at_breakeven is True
                else "SL_NOT_AT_BREAKEVEN"
                if sl_at_breakeven is False
                else "SOURCE_NOT_CAPTURED"
            ),
            "dynamic_exit_action_timeline": _json_safe(dynamic_exit_action_timeline),
            "dynamic_exit_action_timeline_status": (
                "CAPTURED" if dynamic_exit_action_timeline else "NO_DYNAMIC_EXIT_EVENTS_CAPTURED"
            ),
            "mt5_order_id": mt5_order_value,
            "mt5_deal_id": mt5_deal_value,
            "mt5_deal_id_status": (
                "CAPTURED" if mt5_deal_value is not None else "ACCOUNT_HISTORY_REQUIRED"
            ),
            "commission": commission_value,
            "commission_status": (
                "CAPTURED" if commission_value is not None else "ACCOUNT_HISTORY_REQUIRED"
            ),
            "swap": swap_value,
            "swap_status": "CAPTURED" if swap_value is not None else "ACCOUNT_HISTORY_REQUIRED",
            "broker_profit": broker_profit_value,
            "broker_net_profit": broker_net_profit,
            "cash_risk_amount": cash_risk_value,
            "cash_risk_amount_status": (
                "CAPTURED" if cash_risk_value is not None else "SOURCE_NOT_CAPTURED"
            ),
            "broker_net_r": broker_net_r,
            "broker_net_r_status": broker_net_r_status,
            "cost_adjustment_r": cost_adjustment_r,
            "accounting_source": accounting_source or "EXECUTION_ORDER_RESULT",
            "source_repair_geometry_contract_version": "numeric_router_source_repair_geometry_v1",
            "order_ticket": order_ticket_value,
            "order_ticket_status": "CAPTURED" if order_ticket_value is not None else "SOURCE_NOT_CAPTURED",
            "deal_ticket": mt5_deal_value,
            "deal_ticket_status": "CAPTURED" if mt5_deal_value is not None else "ACCOUNT_HISTORY_REQUIRED",
            "broker_fill_time_utc": close_time_utc.isoformat(),
            "broker_fill_time_utc_status": broker_fill_time_status,
            "executed_entry_price": entry_value,
            "executed_entry_price_status": "CAPTURED" if entry_value is not None else "SOURCE_NOT_CAPTURED",
            "executed_exit_price": fill,
            "executed_exit_price_status": "CAPTURED" if fill is not None else "SOURCE_NOT_CAPTURED",
            "executed_stop_price": stop_value,
            "executed_stop_price_status": "CAPTURED" if stop_value is not None else "SOURCE_NOT_CAPTURED",
            "executed_target_price": target_value,
            "executed_target_price_status": (
                "CAPTURED" if target_value is not None else "SOURCE_NOT_CAPTURED_ON_CLOSE_EVENT"
            ),
            "executed_lot_size": volume_value,
            "executed_lot_size_status": "CAPTURED" if volume_value is not None else "SOURCE_NOT_CAPTURED",
            "partial_exit_lifecycle": partial_lifecycle,
            "partial_exit_lifecycle_status": "CAPTURED",
            "source_repair_plan_row_id": source_repair_identity_values["source_repair_plan_row_id"],
            "source_repair_plan_row_id_status": (
                "CAPTURED" if source_repair_identity_values["source_repair_plan_row_id"] else "SOURCE_NOT_CAPTURED"
            ),
            "input_numeric_router_catalog_entry_id": source_repair_identity_values[
                "input_numeric_router_catalog_entry_id"
            ],
            "input_numeric_router_catalog_entry_id_status": (
                "CAPTURED"
                if source_repair_identity_values["input_numeric_router_catalog_entry_id"]
                else "SOURCE_NOT_CAPTURED"
            ),
            "input_numeric_router_family_spec_id": source_repair_identity_values[
                "input_numeric_router_family_spec_id"
            ],
            "input_numeric_router_family_spec_id_status": (
                "CAPTURED"
                if source_repair_identity_values["input_numeric_router_family_spec_id"]
                else "SOURCE_NOT_CAPTURED"
            ),
            "source_repair_identity_key": source_repair_identity_values["source_repair_identity_key"],
            "source_repair_identity_key_status": (
                "CAPTURED" if source_repair_identity_values["source_repair_identity_key"] else "SOURCE_NOT_CAPTURED"
            ),
            "source_repair_row_identity_status": source_repair_identity_status,
            "no_execution_effect": True,
        }

        path = _append_path(Path(log_path or SHADOW_LOG_PATH))
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(
            "Failed to write close-side slippage shadow log (non-blocking): %s "
            "[ticket=%s symbol=%s direction=%s close_reason=%s]",
            e, ticket, symbol, direction, close_reason,
        )
