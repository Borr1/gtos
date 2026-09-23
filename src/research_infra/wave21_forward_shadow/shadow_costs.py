"""Live four-component pretrade cost stamping for the forward-shadow lane.

Mirrors the replay cost authority (`v4_timewarp_simulated_live_research_loop.
broker_calibrated_replay_cost_packet`) with one upgrade the rule's V1_1
amendment anticipated: the predecision quote is the LIVE FTMO tick.  The chain
is exactly the replay's, with the tick source swapped from historical to live:

    live tick (fresh, sane)  ->  era/hour-aware spread model  ->  REFUSED

A refused or incomplete packet makes the candidate INELIGIBLE — never a
default, never zero (rule: ``missing_or_incomplete_cost_is_ineligible_not_
zero``; the February run-1 NOT_EVALUABLE was caused by exactly that default).

The packet itself is the production engine
(`src.components.broker_net_cost_engine.build_pretrade_cost_packet`) under the
merge-310 config (profile deep-merged over base, broker_profile present), the
same call shape the replay uses.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

import src.costs.model as _costs_model
from src.components.broker_net_cost_engine import build_pretrade_cost_packet
from src.costs import CostTruthError, account_for
from src.costs.model import commission_usd_per_lot_for_packet
from src.costs.spread_model import SpreadModelError, load_spread_model, spread_price
from src.costs.symbols import SymbolAuthorityError
from src.research_infra import v4_timewarp_simulated_live_research_loop as _tw
from src.research_infra.wave21_forward_shadow.feature_contract import at_utc

DEFAULT_MAX_TICK_STALENESS_SECONDS = 900.0
_SWAP_TIME_STOP_BARS_DEFAULT = 32


class CostAuthorityError(RuntimeError):
    """The four-component cost authority cannot price ANY candidate.

    Raised at startup only.  It exists because the failure it names is silent:
    with the commission schedule unresolvable every candidate refuses with
    ``pretrade_packet_incomplete_component_sum`` while the banner, the
    heartbeat, the candidate count and the packet writer all read perfectly
    healthy.  That is a lane which measures nothing and says so nowhere.
    """


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _tick_from_live_quote(
    quote: Mapping[str, Any] | None,
    *,
    max_staleness_seconds: float,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    if not isinstance(quote, Mapping):
        return None, {"live_tick_status": "absent"}
    bid = _safe_float(quote.get("bid"))
    ask = _safe_float(quote.get("ask"))
    stale = _safe_float(quote.get("stale_seconds"), math.inf)
    if bid <= 0 or ask < bid:
        return None, {"live_tick_status": "invalid_bid_ask", "bid": bid, "ask": ask}
    if stale > max_staleness_seconds:
        return None, {
            "live_tick_status": "stale",
            "stale_seconds": stale,
            "max_staleness_seconds": max_staleness_seconds,
        }
    tick = {
        "bid": bid,
        "ask": ask,
        "time_utc": quote.get("time_utc"),
    }
    return tick, {
        "live_tick_status": "used",
        "quote_source": "live_ftmo_predecision_tick",
        "live_tick_time_utc": quote.get("time_utc"),
        "live_tick_stale_seconds": stale,
    }


def _tick_from_spread_model(
    candidate: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    asof_utc: str,
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    """Replay's exact fallback: price the instant through the spread model."""

    symbol = str(candidate.get("symbol") or "")
    entry = _safe_float(candidate.get("entry_price"))
    stop = _safe_float(candidate.get("stop_loss"))
    risk = abs(entry - stop)
    profile = (
        config.get("broker_profile")
        if isinstance(config.get("broker_profile"), Mapping)
        else {}
    )
    try:
        asof = at_utc(asof_utc)
        if risk <= 0.0:
            raise SpreadModelError("non-positive candidate stop distance")
        account = account_for(
            server=str(profile.get("server") or "") or None,
            namespace=_tw.broker_account_namespace(dict(config)) or None,
        )
        estimate = spread_price(symbol, account, asof, band="mid")
        model_spread_price = _safe_float(estimate.spread_price, math.nan)
        if not math.isfinite(model_spread_price) or model_spread_price <= 0.0:
            raise SpreadModelError("non-positive spread-model price")
    except (CostTruthError, SpreadModelError, SymbolAuthorityError, ValueError):
        return None
    spread_r = model_spread_price / risk
    spread_price_units = max(0.0, spread_r) * risk
    mid = entry if entry > 0 else 1.0
    tick = {
        "bid": max(0.0, mid - spread_price_units / 2.0),
        "ask": mid + spread_price_units / 2.0,
        "time_utc": asof_utc,
    }
    return tick, {
        "quote_source": "spread_model_v1_hour_aware",
        "spread_model_account": account,
        "spread_model_band": "mid",
        "spread_model_spread_price": model_spread_price,
        "spread_model_era": estimate.era,
        "spread_model_coverage": estimate.coverage.value,
    }


def stamp_live_pretrade_cost(
    candidate: Mapping[str, Any],
    *,
    config: Mapping[str, Any],
    live_quote: Mapping[str, Any] | None,
    asof_utc: str,
    max_tick_staleness_seconds: float = DEFAULT_MAX_TICK_STALENESS_SECONDS,
) -> dict[str, Any]:
    """Stamp the four-component cost onto one candidate, fail-closed.

    Returns ``{"complete": bool, "cost_r", "spread_r", "expected_slippage_r",
    "swap_cost_r", "commission_r", "quote_authority", "packet"}``.  When
    ``complete`` is False the candidate is INELIGIBLE (the caller must not
    default any component).
    """

    symbol = str(candidate.get("symbol") or "")
    entry = _safe_float(candidate.get("entry_price"))
    stop = _safe_float(candidate.get("stop_loss"))
    risk = abs(entry - stop)
    runtime = (
        config.get("gtos_vnext_runtime")
        if isinstance(config.get("gtos_vnext_runtime"), Mapping)
        else {}
    )

    tick, quote_metadata = _tick_from_live_quote(
        live_quote, max_staleness_seconds=max_tick_staleness_seconds
    )
    if tick is None:
        fallback = _tick_from_spread_model(
            candidate, config=config, asof_utc=asof_utc
        )
        if fallback is None:
            return {
                "complete": False,
                "refusal_reason": "quote_source_gap_no_live_tick_no_spread_model",
                "quote_authority": {
                    **quote_metadata,
                    "quote_source": "spread_model_source_gap",
                },
                "cost_r": None,
                "spread_r": None,
                "expected_slippage_r": None,
                "swap_cost_r": None,
                "commission_r": None,
                "packet": None,
            }
        tick, fallback_metadata = fallback
        quote_metadata = {**quote_metadata, **fallback_metadata}

    market = _tw._broker_symbol_market_config(config, symbol)
    swap_time_stop_bars = _tw.first_present(
        candidate.get("gtos_vnext_dynamic_time_stop_bars"),
        candidate.get("dynamic_time_stop_bars"),
        candidate.get("time_stop_bars"),
        runtime.get("broad_live_as_if_replay_pretrade_swap_cost_time_stop_bars"),
        runtime.get("selected_cell_swap_cost_time_stop_bars"),
        _SWAP_TIME_STOP_BARS_DEFAULT,
    )
    trade_params = {
        "direction": candidate.get("side"),
        "side": candidate.get("side"),
        "entry_price": entry,
        "stop_loss": stop,
        "take_profit_1": candidate.get("take_profit_1"),
        "risk_reward_ratio": candidate.get("risk_reward_ratio"),
        "gtos_vnext_production_execution_path": True,
        "gtos_vnext_selected_cell_risk_pct": 0.0,
        "gtos_vnext_selected_cell_risk_cell_id": (
            f"forward_shadow:{candidate.get('candidate_id')}"
        ),
        "gtos_vnext_selected_cell_risk_decision_basis": (
            "forward_shadow_broker_net_cost"
        ),
        "gtos_vnext_commission_model_status": (
            "COMMISSION_INCLUDED_IN_SELECTED_CELL_RISK"
        ),
        "gtos_vnext_expected_slippage_r": (
            candidate.get("gtos_vnext_expected_slippage_r")
            or candidate.get("expected_slippage_r")
        ),
        "gtos_vnext_dynamic_time_stop_bars": swap_time_stop_bars,
    }
    packet = build_pretrade_cost_packet(
        config=dict(config),
        trade_params=trade_params,
        tick=tick,
        symbol=symbol,
        broker_symbol=str(market.get("mt5_symbol") or _tw.ftmo_symbol(symbol)),
        entry_price=entry,
        stop_loss=stop,
        sl_distance=risk,
        risk_pct=0.0,
        symbol_info=market,
        asof_utc=asof_utc,
    )
    raw_total = packet.get("total_cost_r")
    total = _safe_float(raw_total, math.nan)
    complete = bool(
        not isinstance(raw_total, bool) and math.isfinite(total) and total >= 0.0
    )
    swap_cost = packet.get("swap_cost")
    swap_cost = swap_cost if isinstance(swap_cost, Mapping) else {}
    commission_cost = packet.get("commission_cost")
    commission_cost = commission_cost if isinstance(commission_cost, Mapping) else {}
    result = {
        "complete": complete,
        "cost_r": total if complete else None,
        "spread_r": packet.get("spread_r"),
        "expected_slippage_r": packet.get("expected_slippage_r"),
        "swap_cost_r": swap_cost.get("cost_r"),
        "commission_r": packet.get("commission_r"),
        "quote_authority": quote_metadata,
        "swap_time_stop_bars": swap_time_stop_bars,
        "packet": {
            "status": packet.get("status"),
            "model_version": packet.get("model_version"),
            "total_cost_r": packet.get("total_cost_r"),
            "total_cost_components": packet.get("total_cost_components"),
            "commission_cost_source_status": commission_cost.get("source_status"),
            # A refused packet must name the field that refused it.  Without
            # these the only visible symptom of an unresolvable commission
            # schedule is `source_gap`, which is equally consistent with a
            # missing stop distance or a missing tick spec — the live lane
            # spent its first deployment inert for exactly that reason.
            "commission_missing_fields": list(
                commission_cost.get("missing_fields") or ()
            ),
            "commission_usd_per_lot_round_turn": commission_cost.get(
                "usd_per_lot_round_turn"
            ),
            "commission_account_namespace": commission_cost.get("account_namespace"),
            "commission_server": commission_cost.get("server"),
            "swap_cost_source_status": swap_cost.get("source_status"),
        },
    }
    if not complete:
        result["refusal_reason"] = "pretrade_packet_incomplete_component_sum"
    return result


def preflight_cost_authority(
    *,
    config: Mapping[str, Any],
    symbols: tuple[str, ...] | list[str],
) -> dict[str, Any]:
    """Resolve the cost authority for the whole surface, before starting.

    Checks the two committed artifacts a shadow clone has actually been
    deployed without, in the order they bite:

    1. **the broker-true commission schedule.**  The four-component rule is
       fail-closed by design, so an unresolvable schedule does not crash the
       lane — it refuses every candidate, one at a time, forever.  The first
       VPS deployment ran a full session that way: 88 candidates generated per
       cycle, 88 refused, `broker_mutation: false`, a healthy heartbeat, and
       zero measurement.
    2. **the spread model.**  Not consulted per candidate while the live tick
       is fresh, so its absence surfaces only when the first would-be order is
       stamped and `shadow_lifecycle._authority_hashes()` raises mid-cycle.

    A per-symbol commission gap is reported but does not refuse: the surface is
    broader than any one account's measured instrument set, and one unpriceable
    symbol is a legitimate partial lane.  A total gap is refused, because a lane
    that can price nothing measures nothing.
    """

    profile = (
        config.get("broker_profile")
        if isinstance(config.get("broker_profile"), Mapping)
        else {}
    )
    server = profile.get("server")
    namespace = profile.get("broker_account_namespace")
    # Resolved at call time, not bound at import: the report must name the path
    # the cost layer will ACTUALLY read, or it misdirects the reader it exists
    # for.
    artifact = _costs_model.DEFAULT_ARTIFACT
    report: dict[str, Any] = {
        "artifact": str(artifact),
        "artifact_present": artifact.is_file(),
        "server": server,
        "account_namespace": namespace,
        "symbols_checked": len(symbols),
    }
    try:
        report["account"] = account_for(
            server=str(server) if server else None,
            namespace=str(namespace) if namespace else None,
        )
    except CostTruthError as exc:
        raise CostAuthorityError(
            "forward-shadow cost preflight: cannot resolve a broker-truth account "
            f"from server={server!r} namespace={namespace!r}. Every candidate would "
            f"refuse with `pretrade_packet_incomplete_component_sum`. {exc}"
        ) from exc

    resolvable: list[str] = []
    unresolvable: list[str] = []
    for symbol in symbols:
        market = _tw._broker_symbol_market_config(config, str(symbol))
        broker_symbol = str(market.get("mt5_symbol") or _tw.ftmo_symbol(str(symbol)))
        # A representative positive price: `notional_bp` schedules need one to
        # resolve at all, and its VALUE is irrelevant to resolvability.
        usd_per_lot = commission_usd_per_lot_for_packet(
            broker_symbol,
            server=str(server) if server else None,
            namespace=str(namespace) if namespace else None,
            entry_price=100.0,
        )
        (resolvable if usd_per_lot is not None else unresolvable).append(str(symbol))
    report["commission_resolvable_symbols"] = len(resolvable)
    report["commission_unresolvable_symbols"] = unresolvable
    report["status"] = "ok" if not unresolvable else "partial"
    if not resolvable:
        report["status"] = "unavailable"
        raise CostAuthorityError(
            "forward-shadow cost preflight: the broker-true commission schedule "
            f"resolves for 0 of {len(symbols)} symbols, so every candidate would "
            "refuse with `pretrade_packet_incomplete_component_sum` and the lane "
            "would measure nothing.\n"
            f"  artifact: {artifact}\n"
            f"  present:  {artifact.is_file()}\n"
            f"  account:  {report.get('account')} (server={server!r})\n"
            "This artifact is COMMITTED. If it is absent, the clone did not "
            "materialise it — see the runbook's data-dependency list "
            "(`git sparse-checkout add research/operations/broker_truth_layer_2026_07_27`)."
        )

    # The OTHER artifact a clone has already been deployed without.  It is not
    # consulted per-candidate while the live tick is fresh, so its absence is
    # invisible until the first would-be order is stamped — at which point
    # `shadow_lifecycle._authority_hashes()` raises mid-cycle, hours in.  One
    # read here converts that into a startup error too.
    try:
        report["spread_model_sha256"] = load_spread_model().artifact_sha256
        report["spread_model_status"] = "loaded"
    except (SpreadModelError, CostTruthError) as exc:
        report["spread_model_status"] = "unavailable"
        raise CostAuthorityError(
            "forward-shadow cost preflight: the spread model is unavailable. It "
            "is the quote fallback whenever a live tick is missing or stale, and "
            "the lifecycle authority hash, so the lane would refuse those "
            "candidates and then raise mid-cycle on the first would-be order.\n"
            f"  {exc}\n"
            "This artifact is COMMITTED — see the runbook's data-dependency list "
            "(`git sparse-checkout add research/operations/spread_model_2026_07_29`)."
        ) from exc
    return report
