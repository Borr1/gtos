"""Unified production/F5 live-flow projection and deterministic reconciliation.

This is deliberately *not* another logger.  The live book already has one cross-process,
append-only writer: :class:`RuntimeLearningPacketWriter`.  This module defines the small,
versioned ``live_flow`` block embedded in every new runtime-learning packet and the pure
reconciler used by operators/tests.

Two identities are recorded:

``flow_id``
    Namespace-specific occurrence identity.  It joins one candidate through generation,
    admission, owner controls, broker request/fill, management, and realized deal truth.

``strategy_occurrence_id``
    The same occurrence without namespace/account surface.  It pairs the production and F5
    observations without ever treating one account's broker result as the other's truth.

The decision bar (not merely the day) is load-bearing.  The legacy candidate id is day-grained
and can recur on several H4/M15 bars, so it is carried as provenance but is never the sole join
key here.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping


CONTRACT_VERSION = "gtos.live_flow.v1"

# The order is the production call order, coarsened only where several adjacent predicates share
# one owner.  ``cleared`` means control flow advanced beyond the stage; it does not pretend that
# every optional predicate inside the stage was armed.
GATE_ORDER: tuple[str, ...] = (
    "candidate_generation",
    "book_admission_and_sizing",
    "book_authority",
    "owner_controls",
    "idempotency_and_daily_caps",
    "open_position_lifecycle_guard",
    "market_and_entry_freshness",
    "owner_pretrade_cost_screen",
    "execution_policy_and_risk_contract",
    "execution_manager_and_cost_authority",
    "broker_geometry_and_lot_limits",
    "broker_request",
    "broker_result",
    "broker_fill_reconciliation",
    "position_management",
    "exit_and_realized_deal_truth",
)
_GATE_INDEX = {name: index for index, name in enumerate(GATE_ORDER)}


def _stable_hash(value: Any, *, prefix: str) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(f"{prefix}:{payload}".encode("utf-8")).hexdigest()


def _direction(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        if float(value) > 0:
            return "LONG"
        if float(value) < 0:
            return "SHORT"
    text = str(value).strip().upper()
    if text in {"1", "+1", "BUY", "LONG"}:
        return "LONG"
    if text in {"-1", "SELL", "SHORT"}:
        return "SHORT"
    return text or None


def surface_for_namespace(namespace: Any) -> str:
    text = str(namespace or "")
    return "f5_minimal" if text.endswith("_f5_minimal") else "production"


def account_scope_for_namespace(namespace: Any) -> str:
    text = str(namespace or "")
    return text[: -len("_f5_minimal")] if text.endswith("_f5_minimal") else text


def candidate_flow_identity(
    *,
    namespace: Any,
    sleeve: Any,
    symbol: Any,
    direction: Any,
    decision_bar_iso: Any,
    candidate_id: Any = None,
) -> dict[str, Any]:
    """Return namespace-specific and cross-surface candidate occurrence identities."""
    strategy_material = {
        "sleeve": str(sleeve) if sleeve not in (None, "") else None,
        "symbol": str(symbol) if symbol not in (None, "") else None,
        "direction": _direction(direction),
        "decision_bar_iso": str(decision_bar_iso) if decision_bar_iso not in (None, "") else None,
        # Provenance/disambiguator, never the sole identity because this id is day-grained live.
        "candidate_id": str(candidate_id) if candidate_id not in (None, "") else None,
    }
    complete = all(
        strategy_material.get(key) not in (None, "")
        for key in ("sleeve", "symbol", "direction", "decision_bar_iso")
    )
    strategy_occurrence_id = _stable_hash(strategy_material, prefix="strategy_occurrence")
    flow_material = {"namespace": str(namespace or ""), **strategy_material}
    return {
        "identity_status": (
            "candidate_occurrence_complete" if complete else "candidate_occurrence_partial"
        ),
        "flow_id": _stable_hash(flow_material, prefix="live_flow"),
        "strategy_occurrence_id": strategy_occurrence_id,
        **strategy_material,
    }


def _reason_gate(reason: Any) -> str | None:
    text = str(reason or "").strip().lower()
    if not text:
        return None
    rules: tuple[tuple[tuple[str, ...], str], ...] = (
        (("profile_missing_instrument", "insufficient_bars", "stale_decision_bar",
          "future_decision_bar", "generator_", "spread_geometry_floor",
          "entry_hour_", "candidate_generation"), "candidate_generation"),
        (("vp_acceptance", "learning_rerate", "metals_confluence", "symbol_damage",
          "unknown_sleeve", "unknown_profile", "nonpositive_stop", "bad_direction",
          "ceiling_profile", "soft_daily_stop", "max_dd_", "gross_risk_cap",
          "circuit_breaker", "blocked_by_governor", "admission_", "sizing_"),
         "book_admission_and_sizing"),
        (("ultimate_book_disabled", "apply_to_execution", "live_activation", "live_broker_authority",
          "broad_selector", "missing_dial", "kill_switch_or_halt", "breach_flatten_block"),
         "book_authority"),
        (("ai_companion_", "weekend_", "operator_"), "owner_controls"),
        (("already_placed", "cluster_unit_already", "zero_risk"),
         "idempotency_and_daily_caps"),
        (("sleeve_already_holds", "same_broker_symbol", "position_source_unavailable",
          "open_position_lifecycle"), "open_position_lifecycle_guard"),
        (("no_tick", "stale_tick", "stale_late_entry", "sl_wrong_side", "geometry_unavailable"),
         "market_and_entry_freshness"),
        (("cost_screen", "spread_cost", "pre_send_cost", "frozen_price",
          "frozen_intent", "blow_through_frozen"), "owner_pretrade_cost_screen"),
        (("vnext_policy", "vnext_risk"), "execution_policy_and_risk_contract"),
        (("exec_mgr", "pretrade_cost", "cost_authority"),
         "execution_manager_and_cost_authority"),
        (("lot_size", "below_min_lot", "lot_normalize", "cash_risk", "filling_mode",
          "deviation_", "f5_round_up", "broker_geometry"), "broker_geometry_and_lot_limits"),
        (("runtime_halt", "activation_refused", "order_send_exception"), "broker_request"),
        (("order_rejected", "timeout_no", "retcode_"), "broker_result"),
    )
    for prefixes, gate in rules:
        if any(token in text for token in prefixes):
            return gate
    return None


def event_gate_for_event(event_type: str, *, reason: Any = None) -> tuple[str | None, str]:
    """Return the stage directly represented by the event, never an inferred cleared prefix."""
    reason_gate = _reason_gate(reason)
    if event_type == "generation_cycle_complete":
        return "candidate_generation", "observed_complete"
    if event_type == "candidate_generated":
        return "candidate_generation", "observed"
    if event_type == "unit_shadow":
        return reason_gate or "book_authority", "shadow"
    if event_type == "unit_admitted":
        return reason_gate or "book_authority", "refused" if reason_gate else "observed_admitted"
    if event_type == "unit_skipped":
        return reason_gate, "refused" if reason_gate else "refused_unclassified"
    if event_type == "unit_placed":
        return "broker_fill_reconciliation", "observed_placed"
    if event_type in {"position_adopted", "position_managed", "position_management_error",
                      "position_out_of_universe"}:
        return "position_management", "error" if event_type.endswith("error") else "observed"
    if event_type in {"position_closed", "breach_flatten"}:
        return "exit_and_realized_deal_truth", "observed"
    if event_type == "cycle_no_candidates":
        return reason_gate or "book_admission_and_sizing", "refused" if reason_gate else "observed_empty"
    if event_type == "cycle_no_decision":
        return reason_gate, "refused" if reason_gate else "refused_unclassified"
    return reason_gate, "observed" if reason_gate else "unclassified"


def gate_observations(
    event_type: str,
    *,
    reason: Any = None,
    outcome: Mapping[str, Any] | None = None,
    bridge: Mapping[str, Any] | None = None,
    execution: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build sparse, evidence-bound stage observations.

    Reaching a later event often implies code control flow passed earlier predicates, but the packet
    does not carry each predicate's verdict.  Those stages remain unclaimed here; only the event,
    explicit bridge fields, exact refusal reason, and captured broker observation can set a status.
    """
    outcome = outcome or {}
    bridge = bridge or {}
    execution = execution or {}
    observed: dict[str, dict[str, Any]] = {}

    def _observe(gate: str, status: str, evidence: str) -> None:
        observed[gate] = {
            "order": _GATE_INDEX[gate] + 1,
            "gate": gate,
            "status": status,
            "evidence": evidence,
        }

    event_gate, event_disposition = event_gate_for_event(event_type, reason=reason)
    if event_gate is not None:
        _observe(event_gate, event_disposition, f"event_type:{event_type}")

    candidate_disposition = outcome.get("candidate_disposition")
    candidate_gate = outcome.get("candidate_disposition_gate")
    if candidate_gate in _GATE_INDEX and candidate_disposition not in (None, ""):
        status = "refused" if candidate_disposition == "refused" else "observed"
        _observe(str(candidate_gate), status, "outcome.candidate_disposition")

    reason_gate = _reason_gate(reason)
    if reason_gate is not None and str(reason or "").lower() not in {"ok", "allowed"}:
        _observe(reason_gate, "refused", "outcome.reason")

    if event_type in {"unit_admitted", "unit_shadow"}:
        _observe("book_admission_and_sizing", "observed", "event admission unit")
        if bridge.get("runtime_effect_now") is True:
            _observe("book_authority", "observed_passed", "bridge.runtime_effect_now")
        elif event_type == "unit_shadow":
            _observe("book_authority", "shadow", "event_type:unit_shadow")

    request_status = execution.get("request_status")
    if request_status == "sent":
        _observe(
            "broker_request",
            "observed_sent",
            "outcome.gtos_live_flow_execution.request_status",
        )
    elif request_status == "blocked_before_send":
        _observe(
            "broker_request",
            "refused",
            "outcome.gtos_live_flow_execution.request_status:blocked_before_send",
        )
    result_status = execution.get("result_status")
    if result_status not in (None, "", "not_reached"):
        _observe(
            "broker_result",
            "observed" if result_status == "success" else str(result_status),
            "outcome.gtos_live_flow_execution.result_status",
        )
    fill_status = execution.get("fill_status")
    if fill_status not in (None, "", "not_reached"):
        _observe(
            "broker_fill_reconciliation",
            str(fill_status),
            "outcome.gtos_live_flow_execution.fill_status",
        )

    rows = sorted(observed.values(), key=lambda row: int(row["order"]))
    refused = [row for row in rows if row["status"] in {"refused", "shadow", "error"}]
    return {
        "event_gate": event_gate,
        "event_gate_order": _GATE_INDEX[event_gate] + 1 if event_gate is not None else None,
        "event_disposition": event_disposition,
        "observations": rows,
        "observed_gate_count": len(rows),
        "unobserved_gate_count": len(GATE_ORDER) - len(rows),
        "terminal_refusal_gate": refused[-1]["gate"] if refused else None,
    }


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ""):
            return value
    return None


def _compact(mapping: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in mapping.items() if value is not None}


def build_live_flow_block(
    *,
    namespace: Any,
    event_type: str,
    created_at_utc: Any,
    sleeve: Any,
    symbol: Any,
    direction: Any,
    decision_bar_iso: Any,
    candidate_id: Any,
    unit: Mapping[str, Any] | None,
    outcome: Mapping[str, Any],
    bridge: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one runtime-learning packet into the unified live-flow contract."""
    identity = candidate_flow_identity(
        namespace=namespace,
        sleeve=sleeve,
        symbol=symbol,
        direction=direction,
        decision_bar_iso=decision_bar_iso,
        candidate_id=candidate_id,
    )
    members = outcome.get("admission_unit_members") or []
    member_flows = []
    for member in members if isinstance(members, list) else []:
        if not isinstance(member, Mapping):
            continue
        member_flows.append(candidate_flow_identity(
            namespace=namespace,
            sleeve=member.get("sleeve"),
            symbol=member.get("symbol"),
            direction=member.get("direction"),
            decision_bar_iso=member.get("decision_bar_iso"),
            candidate_id=member.get("candidate_id"),
        ))

    reason = _first(
        outcome,
        "candidate_disposition_reason",
        "reason",
        "skip_reason",
        "reject_reason",
        "admission_reason",
        "decision_reason",
    )
    execution = outcome.get("gtos_live_flow_execution")
    execution = dict(execution) if isinstance(execution, Mapping) else {}
    modelled = outcome.get("modelled_cost_components")
    modelled = dict(modelled) if isinstance(modelled, Mapping) else {}
    f5_round = outcome.get("f5_round_up")
    f5_round = dict(f5_round) if isinstance(f5_round, Mapping) else {}
    broker_limits = execution.get("broker_limits")
    broker_limits = dict(broker_limits) if isinstance(broker_limits, Mapping) else {}
    request = execution.get("request")
    request = dict(request) if isinstance(request, Mapping) else {}
    result = execution.get("result")
    result = dict(result) if isinstance(result, Mapping) else {}
    entry_execution = execution.get("entry_execution")
    entry_execution = dict(entry_execution) if isinstance(entry_execution, Mapping) else {}

    unit_risk_fraction = (unit or {}).get("risk_pct_per_trade") if isinstance(unit, Mapping) else None
    intended_risk_pct = _first(outcome, "risk_pct_override", "gtos_vnext_selected_cell_risk_pct")
    if intended_risk_pct is None and unit_risk_fraction is not None:
        try:
            intended_risk_pct = float(unit_risk_fraction) * 100.0
        except (TypeError, ValueError):
            intended_risk_pct = None

    gates = gate_observations(
        event_type,
        reason=reason,
        outcome=outcome,
        bridge=bridge,
        execution=execution,
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "surface": surface_for_namespace(namespace),
        "account_scope": account_scope_for_namespace(namespace),
        "namespace": str(namespace or ""),
        "event_time_utc": str(created_at_utc) if created_at_utc not in (None, "") else None,
        "market_decision_time_utc": identity.get("decision_bar_iso"),
        "flow_id": identity["flow_id"],
        "strategy_occurrence_id": identity["strategy_occurrence_id"],
        "identity_status": identity["identity_status"],
        "candidate_id": identity.get("candidate_id"),
        "sleeve": identity.get("sleeve"),
        "symbol": identity.get("symbol"),
        "direction": identity.get("direction"),
        "member_flow_ids": sorted({row["flow_id"] for row in member_flows}),
        "member_strategy_occurrence_ids": sorted({row["strategy_occurrence_id"] for row in member_flows}),
        "gate_order_contract": list(GATE_ORDER),
        "gate_observations": gates["observations"],
        "observed_gate_count": gates["observed_gate_count"],
        "unobserved_gate_count": gates["unobserved_gate_count"],
        "event_gate": gates["event_gate"],
        "event_gate_order": gates["event_gate_order"],
        "event_disposition": gates["event_disposition"],
        "terminal_refusal_gate": gates["terminal_refusal_gate"],
        "reason": reason,
        "denominator": _compact({
            "candidate_disposition": outcome.get("candidate_disposition"),
            "candidate_disposition_gate": outcome.get("candidate_disposition_gate"),
            "candidate_disposition_reason": outcome.get("candidate_disposition_reason"),
            "candidate_disposition_evidence": outcome.get("candidate_disposition_evidence"),
            "candidate_count_in": bridge.get("n_candidates_in"),
            "candidate_count_after_drop": bridge.get("n_candidates_after_drop"),
            "admission_unit_member_count": outcome.get("admission_unit_member_count"),
            "generation": bridge.get("broker_profile_generation"),
        }),
        "cost": _compact({
            "modelled_cost_status": outcome.get("modelled_cost_status"),
            "modelled_total_r": outcome.get("modelled_cost_r"),
            "modelled_components_r": modelled or None,
            "modelled_components_expected": outcome.get("modelled_cost_components_expected"),
            "modelled_components_missing": outcome.get("modelled_cost_components_missing"),
            "modelled_excludes": outcome.get("modelled_cost_excludes"),
            "spread_r": _first(outcome, "spread_r", "pretrade_spread_r"),
            "slippage_source_status": outcome.get("slippage_source_status"),
            "commission_source_status": outcome.get("commission_source_status"),
            "swap_source_status": outcome.get("swap_source_status"),
        }),
        "sizing": _compact({
            "intended_risk_pct": intended_risk_pct,
            "intended_risk_pct_unit": "percent_of_equity",
            "unit_risk_fraction": (unit or {}).get("unit_risk_pct") if isinstance(unit, Mapping) else None,
            "unit_risk_fraction_unit": "fraction_of_equity",
            "nominal_risk_usd": outcome.get("f5_nominal_risk_usd"),
            "intended_risk_usd": outcome.get("f5_intended_risk_usd"),
            "broker_cash_risk_usd": _first(outcome, "f5_actual_risk_usd", "cash_risk_amount"),
            "cash_risk_status": outcome.get("cash_risk_amount_status"),
            "lots_requested": _first(execution, "lots_requested", f5_round.get("f5_lots_requested")),
            "lots_placed": _first(execution, "lots_placed", f5_round.get("f5_lots_placed")),
            "lots_unit": "broker_lots",
            "f5_round_up_status": f5_round.get("f5_round_up") or outcome.get("f5_round_up_status"),
        }),
        "broker": _compact({
            "limits": broker_limits or None,
            "pre_request_status": execution.get("pre_request_status"),
            "request_status": execution.get("request_status"),
            "request": request or None,
            "result_status": execution.get("result_status"),
            "result": result or None,
            "fill_status": execution.get("fill_status"),
        }),
        "realized": _compact({
            "observed_entry_quote_spread_price": entry_execution.get(
                "observed_quote_spread_price"
            ),
            "observed_entry_quote_spread_r": entry_execution.get("observed_quote_spread_r"),
            "request_to_fill_adverse_slippage_price": entry_execution.get(
                "request_to_fill_adverse_slippage_price"
            ),
            "request_to_fill_adverse_slippage_r": entry_execution.get(
                "request_to_fill_adverse_slippage_r"
            ),
            "request_to_fill_slippage_status": entry_execution.get(
                "request_to_fill_slippage_status"
            ),
            "entry_commission_usd": outcome.get("broker_entry_commission"),
            "entry_swap_usd": outcome.get("broker_entry_swap"),
            "position_commission_usd": _first(outcome, "broker_position_aggregate_commission", "broker_exit_commission"),
            "position_swap_usd": _first(outcome, "broker_position_aggregate_swap", "broker_exit_swap"),
            "position_fee_usd": _first(outcome, "broker_position_aggregate_fee", "broker_exit_fee"),
            "position_net_pnl_usd": _first(outcome, "broker_position_realized_pnl", "broker_realized_pnl"),
            "exit_reconciliation_status": outcome.get("exit_reconciliation_status"),
            "broker_fill_time_utc": outcome.get("broker_fill_time_utc"),
            "broker_exit_time_utc": outcome.get("broker_exit_time_utc"),
            "f5_realised_r": outcome.get("f5_realised_r"),
            "f5_notional_pnl_usd": outcome.get("f5_notional_pnl_usd"),
            "f5_broker_net_pnl_usd": outcome.get("f5_broker_net_pnl_usd"),
        }),
    }


def validate_live_flow_block(block: Any) -> list[str]:
    if not isinstance(block, Mapping):
        return ["live_flow_not_mapping"]
    issues: list[str] = []
    if block.get("contract_version") != CONTRACT_VERSION:
        issues.append("live_flow_contract_version_mismatch")
    for key in ("flow_id", "strategy_occurrence_id", "namespace", "surface"):
        if block.get(key) in (None, ""):
            issues.append(f"live_flow_missing:{key}")
    observations = block.get("gate_observations")
    if not isinstance(observations, list):
        issues.append("live_flow_gate_observations_missing")
    else:
        orders = [row.get("order") for row in observations if isinstance(row, Mapping)]
        gates = [row.get("gate") for row in observations if isinstance(row, Mapping)]
        if orders != sorted(orders) or len(orders) != len(set(orders)):
            issues.append("live_flow_gate_observations_not_ordered_unique")
        if any(gate not in _GATE_INDEX for gate in gates):
            issues.append("live_flow_gate_observation_unknown_gate")
        if any(_GATE_INDEX.get(str(gate), -1) + 1 != order for gate, order in zip(gates, orders)):
            issues.append("live_flow_gate_observation_order_mismatch")
    if block.get("gate_order_contract") != list(GATE_ORDER):
        issues.append("live_flow_gate_order_contract_mismatch")
    if block.get("observed_gate_count") != len(observations or []):
        issues.append("live_flow_observed_gate_count_mismatch")
    return issues


def reconcile_live_flow_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Reconcile a complete packet population without top-N/sample suppression."""
    parsed = list(rows)
    issues: list[dict[str, Any]] = []
    by_flow: dict[tuple[str, str], list[tuple[int, Mapping[str, Any], Mapping[str, Any]]]] = defaultdict(list)
    member_links: dict[tuple[str, str], set[str]] = defaultdict(set)
    generation_cycles: dict[tuple[str, str], list[tuple[int, Mapping[str, Any]]]] = defaultdict(list)
    cycle_candidates: dict[tuple[str, str], list[tuple[int, Mapping[str, Any]]]] = defaultdict(list)
    counts = Counter()

    for index, row in enumerate(parsed):
        block = row.get("live_flow") if isinstance(row, Mapping) else None
        block_issues = validate_live_flow_block(block)
        if block_issues:
            issues.append({"row_index": index, "issues": block_issues})
            counts["rows_invalid"] += 1
            continue
        assert isinstance(block, Mapping)
        namespace = str(block.get("namespace"))
        flow_id = str(block.get("flow_id"))
        by_flow[(namespace, flow_id)].append((index, row, block))
        for member_flow in block.get("member_flow_ids") or []:
            member_links[(namespace, str(member_flow))].add(flow_id)
        counts["rows_valid"] += 1
        counts[f"surface:{block.get('surface')}"] += 1
        counts[f"event:{row.get('event_type')}"] += 1
        cycle_key = (namespace, str(row.get("created_at_utc") or ""))
        if row.get("event_type") == "generation_cycle_complete":
            generation_cycles[cycle_key].append((index, row))
        elif row.get("event_type") == "candidate_generated":
            cycle_candidates[cycle_key].append((index, row))

    denominator_flows: set[tuple[str, str]] = set()
    placed_flows: set[tuple[str, str]] = set()
    terminal_flows: set[tuple[str, str]] = set()
    for key, events in sorted(by_flow.items()):
        ordered = sorted(events, key=lambda item: (str(item[1].get("created_at_utc") or ""), item[0]))
        event_types = [str(item[1].get("event_type")) for item in ordered]
        if "candidate_generated" in event_types:
            denominator_flows.add(key)
        if "unit_placed" in event_types:
            placed_flows.add(key)
            terminal_flows.add(key)
        if any(
            any(
                observation.get("status") in {"refused", "shadow", "error"}
                for observation in (item[2].get("gate_observations") or [])
                if isinstance(observation, Mapping)
            )
            for item in ordered
        ):
            terminal_flows.add(key)
        if any(event in {"position_closed", "breach_flatten"} for event in event_types):
            terminal_flows.add(key)

    # Aggregate admission-unit rows establish the join but are not a final disposition.  Only an
    # aggregate SHADOW row terminates its members; an admitted member still needs its own placed /
    # skipped outcome.  Treating membership alone as resolved would make a dropped post-admission
    # candidate disappear from the failure set.
    shadow_unit_flows = {
        key
        for key, events in by_flow.items()
        if any(str(item[1].get("event_type")) == "unit_shadow" for item in events)
    }
    shadow_resolved_candidates = {
        candidate_key
        for candidate_key, unit_flow_ids in member_links.items()
        if any((candidate_key[0], unit_flow_id) in shadow_unit_flows for unit_flow_id in unit_flow_ids)
    }
    linked_candidates = set(member_links)
    resolved = terminal_flows | shadow_resolved_candidates
    missing = sorted(denominator_flows - resolved)
    orphan_placements = sorted(placed_flows - denominator_flows)
    for namespace, flow_id in missing:
        issues.append({"namespace": namespace, "flow_id": flow_id, "issue": "candidate_without_downstream_disposition"})
    for namespace, flow_id in orphan_placements:
        issues.append({"namespace": namespace, "flow_id": flow_id, "issue": "placement_without_candidate_denominator"})

    # New-format cycles carry one compact terminal row for every active spec x symbol slot.
    # Reconcile only cycles that declare this contract, so historical packets remain valid.
    # Candidate joins deliberately omit the legacy day-grained candidate_id: sleeve, symbol,
    # side, and exact decision bar are the native occurrence identity used by live_flow.
    generation_expected_total = 0
    generation_terminal_total = 0
    generation_emitted_total = 0
    generation_missing_candidate_total = 0
    generation_orphan_candidate_total = 0
    for cycle_key, cycle_rows in sorted(generation_cycles.items()):
        namespace, cycle_utc = cycle_key
        if len(cycle_rows) != 1:
            issues.append({
                "namespace": namespace,
                "generation_cycle_utc": cycle_utc,
                "issue": "generation_cycle_packet_count_not_one",
                "observed": len(cycle_rows),
            })
        # Process every declared packet; duplicate packets must not hide their duplicated slots.
        emitted = Counter()
        for row_index, cycle_row in cycle_rows:
            outcome = cycle_row.get("outcome") if isinstance(cycle_row.get("outcome"), Mapping) else {}
            terminals = outcome.get("generation_slot_terminals")
            if not isinstance(terminals, list):
                terminals = []
                issues.append({
                    "row_index": row_index,
                    "namespace": namespace,
                    "generation_cycle_utc": cycle_utc,
                    "issue": "generation_slot_terminals_not_list",
                })
            bridge = cycle_row.get("bridge") if isinstance(cycle_row.get("bridge"), Mapping) else {}
            generation = (
                bridge.get("broker_profile_generation")
                if isinstance(bridge.get("broker_profile_generation"), Mapping)
                else {}
            )
            expected = generation.get("active_symbol_slot_count")
            generation_expected_total += expected if isinstance(expected, int) else 0
            generation_terminal_total += len(terminals)
            if expected != len(terminals):
                issues.append({
                    "row_index": row_index,
                    "namespace": namespace,
                    "generation_cycle_utc": cycle_utc,
                    "issue": "generation_slot_count_not_conserved",
                    "expected": expected,
                    "actual_observed": len(terminals),
                })
            slot_keys = []
            for terminal in terminals:
                if not isinstance(terminal, Mapping):
                    continue
                slot_keys.append((
                    str(terminal.get("sleeve") or ""),
                    str(terminal.get("symbol") or ""),
                    str(terminal.get("timeframe") or ""),
                ))
                if terminal.get("terminal_status") == "candidate_emitted":
                    occurrence = (
                        str(terminal.get("sleeve") or ""),
                        str(terminal.get("symbol") or ""),
                        str(terminal.get("timeframe") or ""),
                        _direction(terminal.get("direction")),
                        str(terminal.get("decision_bar_iso") or ""),
                    )
                    emitted[occurrence] += 1
                    generation_emitted_total += 1
            duplicate_slots = len(slot_keys) - len(set(slot_keys))
            if duplicate_slots:
                issues.append({
                    "row_index": row_index,
                    "namespace": namespace,
                    "generation_cycle_utc": cycle_utc,
                    "issue": "generation_terminal_slot_keys_not_unique",
                    "duplicate_count": duplicate_slots,
                })

        candidates = Counter(
            (
                str(row.get("sleeve") or ""),
                str(row.get("symbol") or ""),
                str(row.get("timeframe") or ""),
                _direction(row.get("direction")),
                str(row.get("decision_bar_iso") or ""),
            )
            for _index, row in cycle_candidates.get(cycle_key, [])
        )
        for occurrence, n_emitted in sorted(emitted.items(), key=lambda item: str(item[0])):
            missing_count = max(0, n_emitted - candidates.get(occurrence, 0))
            if missing_count:
                generation_missing_candidate_total += missing_count
                issues.append({
                    "namespace": namespace,
                    "generation_cycle_utc": cycle_utc,
                    "occurrence": occurrence,
                    "issue": "emitted_generation_slot_without_candidate_packet",
                    "missing_count": missing_count,
                })
        for occurrence, n_candidates in sorted(candidates.items(), key=lambda item: str(item[0])):
            orphan_count = max(0, n_candidates - emitted.get(occurrence, 0))
            if orphan_count:
                generation_orphan_candidate_total += orphan_count
                issues.append({
                    "namespace": namespace,
                    "generation_cycle_utc": cycle_utc,
                    "occurrence": occurrence,
                    "issue": "candidate_packet_without_emitted_generation_slot",
                    "orphan_count": orphan_count,
                })

    counts["rows_total"] = len(parsed)
    counts["flows_total"] = len(by_flow)
    counts["candidate_denominator_flows"] = len(denominator_flows)
    counts["candidate_flows_resolved"] = len(denominator_flows) - len(missing)
    counts["candidate_flows_missing_disposition"] = len(missing)
    counts["placement_flows"] = len(placed_flows)
    counts["orphan_placement_flows"] = len(orphan_placements)
    counts["generation_cycles"] = len(generation_cycles)
    counts["generation_expected_slots"] = generation_expected_total
    counts["generation_terminal_slots"] = generation_terminal_total
    counts["generation_candidate_emitted_slots"] = generation_emitted_total
    counts["generation_emitted_slots_missing_candidate_packet"] = generation_missing_candidate_total
    counts["generation_candidate_packets_without_emitted_slot"] = generation_orphan_candidate_total
    return {
        "contract_version": CONTRACT_VERSION,
        "status": "PASS" if not issues else "FAIL",
        "counts": dict(sorted(counts.items())),
        "issues": issues,
    }


__all__ = [
    "CONTRACT_VERSION",
    "GATE_ORDER",
    "account_scope_for_namespace",
    "build_live_flow_block",
    "candidate_flow_identity",
    "event_gate_for_event",
    "gate_observations",
    "reconcile_live_flow_rows",
    "surface_for_namespace",
    "validate_live_flow_block",
]
