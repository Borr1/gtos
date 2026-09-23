"""order_router — turn a sized W7 book unit + its TradeIntent into a real FTMO order via the
FULL V4 route (the only live-order path; the plain route is blocked at execution.py:2689).

Per realized unit: resolve the live entry geometry from the broker tick, build the broker-real
account_state for the prop-firm headroom snapshot (SAME tick as the order — the <=900s rule),
assemble the 42-key V4 trade_params (execution_packets.build_book_trade_params), and call
ExecutionEngine.open_trade (which builds the pretrade cost model from the tick, runs the 3 fail-closed
gates, and places the order). open_trade inherits the runtime-halt guard, so while halted nothing
sends. Verified [RAN] (tests/ultimate_book/test_order_route.py): the trade_params clears all 3 gates.

SizedUnit has no symbol/direction/stop -> the caller pairs each realized unit with its TradeIntent(s)
(a cluster unit with n_trades>1 places one order per intent at the unit's risk_pct_per_trade).
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
from typing import Any, Optional

from . import execution_packets as EP


def native_pending_order_spec(intent) -> Optional[dict]:
    """Return the native pending-limit spec, or None when the rail is OFF.

    The only switch is ``intent.entry_price``. ``entry_offset_atr`` is stored on
    the intent for half-two and is never applied here (no chase offset).
    """
    raw = getattr(intent, "entry_price", None)
    if raw is None:
        return None
    try:
        price = float(raw)
    except (TypeError, ValueError):
        return None
    if not isfinite(price) or price <= 0:
        return None
    direction = int(getattr(intent, "direction", 0) or 0)
    expiry = getattr(intent, "expiry_bars", None)
    expiry_bars = None
    if expiry is not None:
        try:
            parsed = int(expiry)
        except (TypeError, ValueError):
            parsed = 0
        if parsed >= 1:
            expiry_bars = parsed
    return {
        "entry_price": price,
        "order_type": "BUY_LIMIT" if direction > 0 else "SELL_LIMIT",
        "expiry_bars": expiry_bars,
    }


class UltimateBookOrderRouter:
    def __init__(self, config: dict, namespace: str = "operator_profile",
                 frontier_exits: tuple = ()):
        self.config = config or {}
        self.namespace = namespace
        # The frontier-exit sleeve selection (Session AU, B1550). An EXPLICIT constructor argument
        # and NOT a config key, deliberately, following `--recover-pre-gap-bar` rather than
        # `--vol-level-tilt`: this flag is consumed here, on the placement path, so it never reaches
        # `bridge._bool` and therefore cannot produce the KeyError-against-DEFAULT_CONFIG failure AR
        # measured -- an armed book standing down every tick with a healthy heartbeat. A key that is
        # never read cannot be read wrong. Pinned by
        # `test_frontier_exit_contracts.py::test_the_selection_is_not_a_config_key_anywhere`.
        self.frontier_exits = tuple(frontier_exits or ())

    # ---- live account_state for the prop-firm headroom snapshot ----
    def account_state(self, mt5, *, day_start_baseline: float, reset_window_id: str,
                      account_login: Optional[int] = None,
                      equity_override: Optional[float] = None,
                      balance_override: Optional[float] = None) -> Optional[dict]:
        # `equity_override` / `balance_override` are the F5 minimal-size seam and are None on
        # every production path (byte-identical behaviour).
        #
        # This snapshot is NOT telemetry: `execution_manager_v4._prop_firm_headroom_context`
        # turns it into a `max_allowed_new_trade_risk_pct` and BLOCKS the order when the
        # requested risk exceeds it. F5 uses overrides only to build its isolated NOTIONAL leg;
        # `book_owner` then applies that leg as a tightening cap on a separate broker-real
        # account state. Never mix a real equity override with a notional day-start baseline.
        try:
            equity = (float(equity_override) if equity_override is not None
                      else float(mt5.get_account_equity()))
            balance = (float(balance_override) if balance_override is not None
                       else float(mt5.get_account_balance()))
        except Exception:
            return None
        if equity <= 0 or balance <= 0:
            return None
        login = account_login
        if login is None:
            login = (self.config.get("deployment", {}) or {}).get("mt5_login") or 0
        return {
            "current_equity": equity, "balance": balance, "account_login": login,
            "day_start_equity_or_balance_baseline": float(day_start_baseline),
            "daily_reset_window_id": reset_window_id,
        }

    # ---- entry geometry from the live tick ----
    def _geometry(self, intent, tick) -> Optional[dict]:
        d = int(intent.direction)
        sign = 1.0 if d > 0 else -1.0
        bid = getattr(tick, "bid", None)
        ask = getattr(tick, "ask", None)
        if not bid or not ask:
            return None
        pending = native_pending_order_spec(intent)
        if pending is not None:
            entry = float(pending["entry_price"])           # limit at the named price; no spread cross
        else:
            entry = float(ask if d > 0 else bid)           # live default: cross the spread on entry
        rd = float(intent.stop_dist)
        if rd <= 0:
            return None
        raw_target = getattr(intent, "target_dist", None)
        target_dist = None
        if raw_target not in (None, ""):
            try:
                target_dist = float(raw_target)
            except (TypeError, ValueError):
                target_dist = None
        if target_dist is None or target_dist <= 0:
            try:
                from src.judgment.nineteen import score
                multiple = score(
                    {
                        "symbol": getattr(intent, "symbol", None),
                        "sleeve": getattr(intent, "sleeve", None),
                        "stop_dist": rd,
                        "direction": d,
                    },
                    question_id="target_multiple",
                    instructions=(
                        "The score you return is the target multiple for this limit. "
                        "It may sit between the levels. An empty score leaves the target unset. "
                        "Do not send."
                    ),
                )
            except Exception:
                multiple = None
            target_dist = None if multiple is None else float(multiple) * rd
        take_profit = None if target_dist is None else entry + sign * target_dist
        return {
            "entry_price": entry, "risk_distance": rd,
            "stop_loss": entry - sign * rd, "take_profit_1": take_profit,
        }

    def _f5_compose_stricter_headroom(self, trade_params: dict,
                                      account_state: Any) -> Optional[dict]:
        """Apply the F5 notional limit without changing the shared snapshot builder.

        The ordinary execution-packet builder has already produced a valid broker-real
        snapshot.  When the F5 owner supplies a separately built notional snapshot, compose
        the minimum of their two limits, retain both immutable input hashes, and re-hash the
        effective snapshot.  The default production path carries no F5 key and returns the
        original packet object unchanged.
        """
        if not isinstance(account_state, dict) \
                or "f5_notional_headroom_snapshot_v4" not in account_state:
            return trade_params
        notional = account_state.get("f5_notional_headroom_snapshot_v4")
        real = trade_params.get("gtos_vnext_prop_firm_headroom_snapshot_v4")

        def _valid_snapshot(value: Any) -> tuple[bool, Optional[float]]:
            if not isinstance(value, dict):
                return False, None
            try:
                limit = float(value.get("max_allowed_new_trade_risk_pct"))
            except (TypeError, ValueError):
                return False, None
            if not isfinite(limit) or limit < 0.0:
                return False, None
            if value.get("schema_version") != "prop_firm_headroom_snapshot_v4":
                return False, None
            if value.get("account_namespace") != self.namespace:
                return False, None
            for key in ("source_event_hash_sha256", "snapshot_hash_sha256"):
                digest = value.get(key)
                if not isinstance(digest, str) or len(digest) != 64:
                    return False, None
                if any(char not in "009abcdef" for char in digest.lower()):
                    return False, None
            material = dict(value)
            supplied_hash = material.pop("snapshot_hash_sha256")
            if EP._sha(material) != supplied_hash:
                return False, None
            return True, limit

        real_ok, real_limit = _valid_snapshot(real)
        notional_ok, notional_limit = _valid_snapshot(notional)
        if not real_ok or not notional_ok or real_limit is None or notional_limit is None:
            return None

        if getattr(self, "namespace", None) == "operator":
            effective_limit = real_limit
            basis = "broker_real_notional_is_a_fact"
        else:
            effective_limit = min(real_limit, notional_limit)
            basis = "minimum_of_broker_real_and_f5_notional_mark_to_market"
        provenance = {
            "basis": basis,
            "broker_real_max_allowed_new_trade_risk_pct": real_limit,
            "notional_max_allowed_new_trade_risk_pct": notional_limit,
            "effective_max_allowed_new_trade_risk_pct": effective_limit,
            "broker_real_source_event_hash_sha256": real["source_event_hash_sha256"],
            "broker_real_snapshot_hash_sha256": real["snapshot_hash_sha256"],
            "notional_source_event_hash_sha256": notional["source_event_hash_sha256"],
            "notional_snapshot_hash_sha256": notional["snapshot_hash_sha256"],
        }
        effective = dict(real)
        effective["max_allowed_new_trade_risk_pct"] = effective_limit
        effective["f5_headroom_composition"] = provenance
        effective["source_event_hash_sha256"] = EP._sha(provenance)
        effective.pop("snapshot_hash_sha256", None)
        effective["snapshot_hash_sha256"] = EP._sha(effective)
        composed = dict(trade_params)
        composed["gtos_vnext_prop_firm_headroom_snapshot_v4"] = effective
        return composed

    def geometry_for(self, intent, tick, *, frozen=None) -> Optional[dict]:
        """Resolve entry/stop/target. ``frozen`` is the FrozenPriceIntent geometry.

        The live path re-anchors to the current tick. A frozen send must pass
        the original absolute levels so SL/TP are not rebuilt from a later quote.
        """
        if frozen is not None:
            try:
                entry = float(frozen["entry_price"])
                stop = float(frozen["stop_loss"])
                risk = float(
                    frozen.get("risk_distance")
                    if frozen.get("risk_distance") not in (None, "")
                    else abs(entry - stop)
                )
            except (TypeError, ValueError, KeyError):
                return None
            if risk <= 0:
                return None
            geom = {
                "entry_price": entry,
                "stop_loss": stop,
                "risk_distance": risk,
            }
            target = frozen.get("take_profit_1")
            if target not in (None, ""):
                try:
                    geom["take_profit_1"] = float(target)
                except (TypeError, ValueError):
                    pass
            return geom
        return self._geometry(intent, tick)

    def build_trade_params(self, sized_unit, intent, tick, account_state,
                           geometry=None) -> Optional[dict]:
        geom = geometry if geometry is not None else self._geometry(intent, tick)
        if geom is None:
            return None
        trade_params = EP.build_book_trade_params(
            sized_unit,
            intent,
            geom,
            account_state,
            profile_namespace=self.namespace,
            frontier_exits=self.frontier_exits,
        )
        composed = self._f5_compose_stricter_headroom(trade_params, account_state)
        if composed is None:
            return None
        pending = native_pending_order_spec(intent)
        if pending is None:
            return composed
        stamped = dict(composed)
        stamped["gtos_native_pending_limit"] = True
        stamped["gtos_native_pending_order_type"] = pending["order_type"]
        if pending["expiry_bars"] is not None:
            stamped["gtos_native_pending_expiry_bars"] = pending["expiry_bars"]
        return stamped

    def _geometry_withholds(self, intent, tick) -> bool:
        """True only when withhold is the unique Choice.

        An empty answer, a tie, or an error does not withhold. Does not send.
        """
        try:
            from src.judgment.execution_choices import choose

            row = choose(
                "gate",
                symbol=getattr(intent, "symbol", None),
                reason="geometry_unavailable",
                facts={
                    "symbol": getattr(intent, "symbol", None),
                    "sleeve": getattr(intent, "sleeve", None),
                    "stop_dist": getattr(intent, "stop_dist", None),
                    "entry_price": getattr(intent, "entry_price", None),
                    "bid": getattr(tick, "bid", None) if tick is not None else None,
                    "ask": getattr(tick, "ask", None) if tick is not None else None,
                },
            )
        except Exception:
            return False
        return isinstance(row, dict) and row.get("choice") == "withhold"

    @staticmethod
    def _execution_observation(execution_engine, trade_params, trade_state, *, placed, reason) -> dict:
        """Compact the already-observed send/fill state for the unified packet ledger.

        No broker call is made here.  Raw ticket-like values use ticket-shaped keys so the
        runtime packet redactor hashes them before persistence.
        """
        def _mapping_copy(value) -> dict:
            # Duck-type the already-dict-shaped diagnostics.  Importing ``typing.Mapping`` here
            # widened the whole-file import surface beyond the deployed host lineage, which the
            # activation-carry verifier correctly refuses.  Malformed observations stay empty.
            try:
                return dict(value) if hasattr(value, "items") else {}
            except (TypeError, ValueError):
                return {}

        diag = getattr(execution_engine, "_last_order_send_diagnostic", None)
        diag = _mapping_copy(diag)
        raw_request = _mapping_copy(diag.get("request"))
        request = {
            key: raw_request.get(key)
            for key in (
                "action", "symbol", "volume", "type", "price", "sl", "tp",
                "deviation", "type_time", "type_filling",
            )
            if raw_request.get(key) is not None
        }
        raw_result = _mapping_copy(diag.get("result"))
        result = {
            "success": raw_result.get("success"),
            "retcode": raw_result.get("retcode"),
            "retcode_external": raw_result.get("retcode_external"),
            "request_id": raw_result.get("request_id"),
            "comment": raw_result.get("comment"),
            "order_ticket": raw_result.get("order"),
            "deal_ticket": raw_result.get("deal"),
            "volume": raw_result.get("volume"),
            "price": raw_result.get("price"),
        }
        result = {key: value for key, value in result.items() if value is not None}
        raw_limits = _mapping_copy(diag.get("symbol_info"))
        if not raw_limits:
            observed_geometry = (trade_params or {}).get("gtos_live_flow_broker_geometry")
            raw_limits = _mapping_copy(observed_geometry)
        broker_limits = {
            key: raw_limits.get(key)
            for key in (
                "available", "trade_stops_level", "trade_freeze_level", "point",
                "trade_tick_size", "trade_tick_value", "volume_min", "volume_max",
                "volume_step", "trade_contract_size",
            )
            if raw_limits.get(key) is not None
        }
        raw_tick = _mapping_copy(diag.get("tick"))
        requested_price = request.get("price")
        filled_price = getattr(trade_state, "entry_price", None)
        if filled_price is None:
            filled_price = result.get("price")
        direction = str((trade_params or {}).get("direction") or "").upper()
        sl_distance = getattr(trade_state, "sl_distance", None)
        entry_spread_price = None
        try:
            entry_spread_price = float(raw_tick.get("ask")) - float(raw_tick.get("bid"))
        except (TypeError, ValueError):
            pass
        entry_slippage_price = None
        try:
            request_f = float(requested_price)
            fill_f = float(filled_price)
            entry_slippage_price = fill_f - request_f if direction == "LONG" else request_f - fill_f
        except (TypeError, ValueError):
            pass

        def _in_r(value):
            try:
                distance = float(sl_distance)
                return float(value) / distance if distance > 0 else None
            except (TypeError, ValueError):
                return None

        diagnostic_status = str(diag.get("status") or "")
        request_blocked_before_send = diagnostic_status in {
            "runtime_halt_blocked_before_order_request",
            "runtime_halt_blocked_no_order_send",
            "news_blocked_no_order_send",
        }
        if request_blocked_before_send:
            # Synthetic local refusal is not a broker fill/result or a placed lot.
            result = {}
            entry_slippage_price = None
        request_status = (
            "blocked_before_send"
            if request_blocked_before_send
            else "sent" if request else "not_reached"
        )
        result_status = (
            diagnostic_status or ("success" if placed else str(reason or "unknown"))
            if request_status == "sent" or result
            else "not_reached"
        )
        mt5_last_error = diag.get("mt5_last_error")
        if isinstance(mt5_last_error, tuple):
            mt5_last_error = list(mt5_last_error)
        return {
            "pre_request_status": None if request_status == "sent" else str(reason or "unknown"),
            "request_status": request_status,
            "result_status": result_status,
            "mt5_last_error": mt5_last_error,
            "fill_status": (
                "broker_fill_observed"
                if placed
                else "broker_not_filled" if request_status == "sent" else "not_reached"
            ),
            "request": request,
            "result": result,
            "broker_limits": broker_limits,
            "lots_requested": request.get("volume") or raw_limits.get("lots_normalized"),
            "lots_placed": getattr(trade_state, "initial_volume", None) or result.get("volume"),
            "cash_risk_amount": (
                getattr(trade_state, "cash_risk_amount", None)
                or raw_limits.get("pre_send_cash_risk_amount")
            ),
            "cash_risk_amount_status": (
                getattr(trade_state, "cash_risk_amount_status", None)
                or (
                    "BROKER_ORDER_CALC_PROFIT_PRE_SEND_ONLY"
                    if raw_limits.get("pre_send_cash_risk_amount") is not None
                    else None
                )
            ),
            "entry_execution": {
                "observed_quote_spread_price": entry_spread_price,
                "observed_quote_spread_r": _in_r(entry_spread_price),
                "request_to_fill_adverse_slippage_price": entry_slippage_price,
                "request_to_fill_adverse_slippage_r": _in_r(entry_slippage_price),
                "request_to_fill_slippage_status": (
                    "request_to_broker_fill_observed"
                    if entry_slippage_price is not None and placed
                    else "not_available_or_not_filled"
                ),
            },
        }

    # ---- placement (open_trade builds the cost model + runs the 3 gates + sends) ----
    def place(self, execution_engine, sized_unit, intent, tick, account_state,
              account_balance: float, geometry=None, annotations=None) -> dict:
        """Returns {placed, trade_state, reason}. NEVER raises; the book is best-effort.

        ``geometry`` pins FrozenPriceIntent absolute levels. ``annotations`` are
        extra trade_params keys (fresh-clock ms, frozen identity) stamped before
        open_trade. Both default None — the production call is unchanged.
        """
        tp = None
        open_trade_attempted = False
        try:
            tp = self.build_trade_params(
                sized_unit, intent, tick, account_state, geometry=geometry,
            )
            if isinstance(tp, dict) and isinstance(annotations, dict):
                tp.update(annotations)
            if tp is None:
                if self.namespace == "operator":
                    geometry_withholds = self._geometry_withholds(intent, tick)
                    reason = "geometry_unavailable" if geometry_withholds else "geometry_unset"
                else:
                    reason = "geometry_unavailable"
                observation = self._execution_observation(
                    None, {}, None, placed=False, reason=reason,
                )
                return {"placed": False, "trade_state": None, "reason": reason,
                        "trade_params": None, "live_flow_execution": observation}
            # Fresh event-time decision, not only event-version equality.
            if self.namespace == "operator":
                try:
                    execution_engine._jev_place_gate = None
                except Exception:
                    pass
                from pathlib import Path
                from .news_protocol_runtime_v3 import current_event_decision
                news = current_event_decision(Path(__file__).resolve().parents[3], intent.symbol,
                                              prior=tp, now=datetime.now(timezone.utc))
                tp.update({k: news.get(k) for k in ("event_version", "event_registry_sha256", "event_registry_path", "checked_at_utc")})
                news["news_t60_request_keys"] = tp.get("news_t60_request_keys")
                news["news_t60_require_native_limit"] = bool(tp.get("news_t60_require_native_limit"))
                try:
                    from src.judgment.place_path_choice import decide_place_path
                    path_decision = decide_place_path(
                        symbol=getattr(intent, "symbol", None),
                        exclusions_present=bool(news.get("exclusions_present") or news.get("active_exclusions")),
                        exclusion_count=len(news.get("active_exclusions") or []) if isinstance(news.get("active_exclusions"), (list, tuple)) else 0,
                        snapshot_drift=bool(news.get("snapshot_drift")),
                        registry_read_error=bool(news.get("error")),
                        require_native_limit=bool(tp.get("news_t60_require_native_limit")),
                        native_limit=bool(tp.get("gtos_native_pending_limit")),
                        include_chase=False,
                    )
                except Exception as _path_exc:  # noqa: BLE001 — unanswered hop does not send
                    path_decision = {
                        "continues": False,
                        "reason": "send_hop:" + type(_path_exc).__name__,
                        "sides": {},
                    }
                news["place_path"] = path_decision.get("sides")
                news["place_path_reason"] = path_decision.get("reason")
                tp["news_pre_send"] = dict(news)
                execution_engine._news_pre_send_context = dict(news)
                path_reason = str(path_decision.get("reason") or "")
                # A unique block side is the Choice. An empty answer, a tie, or
                # an error does not restore the old skip and does not invent a send.
                path_blocks = bool(path_reason) and not path_reason.startswith(
                    ("no_decision", "send_hop")
                )
                if path_blocks:
                    reason = path_reason
                    observation = self._execution_observation(None, tp or {}, None, placed=False, reason=reason)
                    tp["gtos_live_flow_execution"] = observation
                    return {"placed": False, "trade_state": None, "reason": reason,
                            "candidate_id": tp.get("candidate_id"), "trade_params": tp,
                            "live_flow_execution": observation}
                # Challenge only. The place decision is the place Choice.
                # W7 never imports this. Activation token stays in the engine.
                try:
                    from src.judgment.unique_loader import gate_order_send
                    gate = gate_order_send(
                        intent=intent,
                        login=0,
                        namespace=self.namespace,
                        tick=tick,
                        unit=sized_unit,
                        origin="order_router.place",
                    ) or {}
                    hops = gate.get("hops") if isinstance(gate.get("hops"), dict) else {}
                    place_hop = hops.get("place") if isinstance(hops.get("place"), dict) else {}
                    choice = str(place_hop.get("choice") or place_hop.get("action") or gate.get("choice") or "").strip().upper()
                    unique = place_hop.get("unique_highest")
                    if unique is None:
                        unique = gate.get("unique_highest")
                    slim_gate = {
                        "action": choice or None,
                        "choice": choice or None,
                        "unique_highest": unique is True,
                        "probability": place_hop.get("probability"),
                        "probabilities": place_hop.get("probabilities"),
                        "asked": gate.get("asked"),
                        "seat": place_hop.get("seat") or "gate",
                        "model": "jev-1.13.0",
                    }
                    tp["jev_send_gate"] = slim_gate
                    det = getattr(intent, "details", None)
                    if isinstance(det, dict):
                        det["jev_send_gate"] = slim_gate
                    if not (unique is True and choice == "PLACE"):
                        reason = "place_choice:" + (choice or "no_choice")
                        observation = self._execution_observation(
                            None, tp or {}, None, placed=False, reason=reason,
                        )
                        tp["gtos_live_flow_execution"] = observation
                        return {"placed": False, "trade_state": None, "reason": reason,
                                "candidate_id": tp.get("candidate_id"), "trade_params": tp,
                                "live_flow_execution": observation}
                except Exception as _gate_exc:  # noqa: BLE001 — hop did not return a Choice; do not place
                    reason = "send_hop:" + type(_gate_exc).__name__
                    observation = self._execution_observation(
                        None, tp or {}, None, placed=False, reason=reason,
                    )
                    if isinstance(tp, dict):
                        tp["gtos_live_flow_execution"] = observation
                        tp["jev_send_gate"] = {"action": None, "reason": reason}
                    return {"placed": False, "trade_state": None, "reason": reason,
                            "candidate_id": tp.get("candidate_id") if isinstance(tp, dict) else None,
                            "trade_params": tp, "live_flow_execution": observation}
                execution_engine._jev_place_gate = {
                    "choice": "PLACE",
                    "unique_highest": True,
                    "model": "jev-1.13.0",
                }
            open_trade_attempted = True
            try:
                ts = execution_engine.open_trade(
                    tp, account_balance, risk_pct_override=tp["risk_pct_override"],
                    trigger="ultimate_book")
            finally:
                if self.namespace == "operator":
                    try:
                        execution_engine._jev_place_gate = None
                    except Exception:
                        pass
            placed = ts is not None and getattr(ts, "ticket", None) not in (None, 0)
            native_pending = bool(getattr(ts, "native_pending_resting", False))
            reason = "native_pending_resting" if native_pending else "ok"
            if not placed:
                # surface the SPECIFIC block reason open_trade recorded (vnext_policy:* / no_tick_data /
                # runtime_halt_blocked / an order_send diagnostic status) instead of the opaque
                # "open_trade_returned_none" -- so the Telegram card + log show WHY a leg did not place.
                reason = getattr(execution_engine, "_last_open_trade_block_reason", None)
                if not reason:
                    diag = getattr(execution_engine, "_last_order_send_diagnostic", None)
                    reason = (diag.get("status") if isinstance(diag, dict) else None) or "open_trade_returned_none"
            observation = self._execution_observation(
                execution_engine, tp, ts, placed=placed, reason=reason,
            )
            # ``tp`` is persisted in the ticket trade record on success and flattened into the
            # skip packet on refusal.  One observation therefore feeds production and F5 without
            # an extra log or a second broker read.
            tp["gtos_live_flow_execution"] = observation
            return {"placed": placed, "trade_state": ts, "reason": reason,
                    "candidate_id": tp.get("candidate_id"), "trade_params": tp,
                    "live_flow_execution": observation,
                    "native_pending": native_pending}
        except Exception as e:   # the book NEVER breaks the live path
            reason = f"router_exception:{e!r}"
            # Before open_trade there cannot be a request for this candidate.  Passing None avoids
            # copying a prior candidate's engine diagnostic into this refusal.
            observation = self._execution_observation(
                execution_engine if open_trade_attempted else None,
                tp or {},
                None,
                placed=False,
                reason=reason,
            )
            if isinstance(tp, dict):
                tp["gtos_live_flow_execution"] = observation
            return {"placed": False, "trade_state": None, "reason": reason,
                    "candidate_id": tp.get("candidate_id") if isinstance(tp, dict) else None,
                    "trade_params": tp, "live_flow_execution": observation}
