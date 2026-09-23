"""Runtime-learning packet builder for the ultimate book.

This module is observation-only. It writes append-only JSONL packets that join
book decisions, skips, placements, management events, and bridge policy state
without exposing account identifiers or raw broker tickets.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from .placement_ledger import (
    PLACEMENT_CAPTURE_COMPLETE_STATUS,
    PLACEMENT_CAPTURE_CONTRACT_VERSION,
)


SCHEMA_VERSION = "ultimate_book_runtime_learning_packet_v1"
DEFAULT_LOG_PATH = "shadow_logs/ultimate_book_runtime_learning_packets.jsonl"
DEFAULT_REDACTION_POLICY = "hash_ticket_and_account_identifiers_v1"

# The optional `economics` block (holding time, realized vs modelled cost, raw governor state)
# is versioned SEPARATELY from the packet schema, and deliberately so.
#
# 99,112 live packets exist and they are the only live evidence this programme has. Bumping
# SCHEMA_VERSION would make every one of them fail `schema_version_mismatch` on read, which
# destroys the evidence to record an addition. So the packet schema stays at v1 -- the packet
# shape genuinely has not changed, it has only grown an optional key -- and the block carries
# its own contract version. A reader keys on the presence of `economics` and on
# `economics.contract_version`, never on SCHEMA_VERSION, to know what it is holding.
PACKET_ECONOMICS_KEY = "economics"

# Emitted into the MAIN log when a packet is refused at emit time. See packet_guard: the marker
# is what makes a refusal visible to a reader of the main log alone, instead of a silent hole.
PACKET_REJECTED_EVENT_TYPE = "packet_rejected"
RECENT_APPEND_DEDUPE_BYTES = 4 * 1024 * 1024
LEGACY_EXIT_ORDER_MISSING_FIELD_CUTOFF_UTC = datetime(2026, 6, 25, 17, 10, tzinfo=timezone.utc)
NONTERMINAL_BROKER_REALIZED_PNL_CUTOFF_UTC = datetime(2026, 6, 29, 16, 50, tzinfo=timezone.utc)

EVENT_TYPES = {
    "cycle_no_decision",
    "cycle_no_candidates",
    "unit_shadow",
    "unit_admitted",
    "unit_skipped",
    "unit_placed",
    "position_adopted",
    "position_managed",
    "position_closed",
    "position_out_of_universe",
    "position_management_error",
    "breach_flatten",
    PACKET_REJECTED_EVENT_TYPE,
}

FORBIDDEN_RAW_KEYS = {
    "account_login",
    "login",
    "password",
    "token",
    "api_key",
    "server",
    "ticket",
    "order_ticket",
    "deal_ticket",
    "position_ticket",
    "broker_entry_deal_ticket",
    "broker_entry_order_ticket",
    "broker_entry_position_id",
    "broker_exit_deal_ticket",
    "broker_exit_order_ticket",
    "broker_exit_position_id",
    "mt5_deal_id",
    "mt5_order_id",
    "mt5_position_id",
}

HASHABLE_TICKET_KEYS = {
    "ticket",
    "order_ticket",
    "deal_ticket",
    "position_ticket",
    "broker_entry_deal_ticket",
    "broker_entry_order_ticket",
    "broker_entry_position_id",
    "broker_exit_deal_ticket",
    "broker_exit_order_ticket",
    "broker_exit_position_id",
    "mt5_deal_id",
    "mt5_order_id",
    "mt5_position_id",
}
HASHABLE_ACCOUNT_KEYS = {"account_login", "login", "server"}
TERMINAL_BROKER_REALIZED_EVENTS = {"position_closed", "breach_flatten"}
BROKER_REALIZED_PNL_KEYS = {
    "broker_realized_pnl",
    "broker_realized_pnl_source",
    "broker_position_realized_pnl",
    "broker_selected_exit_realized_pnl",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_hash(value: Any, *, prefix: str = "ub") -> str:
    text = json.dumps(value, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(f"{prefix}:{text}".encode("utf-8")).hexdigest()


def _clean_mapping(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            k = str(key)
            lk = k.lower()
            ticket_key = _hashable_ticket_key(lk)
            if ticket_key:
                out[f"{lk}_hash_sha256"] = stable_hash(item, prefix=lk)
                continue
            if lk in HASHABLE_ACCOUNT_KEYS:
                out[f"{lk}_hash_sha256"] = stable_hash(item, prefix=lk)
                continue
            if lk in {"password", "token", "api_key"}:
                out[f"{lk}_redacted"] = True
                continue
            out[k] = _clean_mapping(item)
        return out
    if isinstance(value, (list, tuple)):
        return [_clean_mapping(item) for item in value]
    return value


def _hashable_ticket_key(lk: str) -> str | None:
    if lk.endswith("_hash_sha256") or lk.endswith("_redacted"):
        return None
    if lk in HASHABLE_TICKET_KEYS:
        return lk
    if lk.startswith(("broker_", "mt5_")) and lk.endswith(
        ("_ticket", "_tickets", "_deal_id", "_order_id", "_position_id")
    ):
        return lk
    return None


def _first_unit_sleeve(unit: Mapping[str, Any] | None) -> str | None:
    if not unit:
        return None
    members = unit.get("sleeve_members")
    if isinstance(members, list) and members:
        return str(members[0])
    if unit.get("sleeve"):
        return str(unit["sleeve"])
    return None


def _contains_forbidden_raw_key(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            lk = str(key).lower()
            if lk in FORBIDDEN_RAW_KEYS or _hashable_ticket_key(lk):
                found.append(str(key))
            found.extend(_contains_forbidden_raw_key(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(_contains_forbidden_raw_key(item))
    return found


def _packet_created_before_legacy_exit_order_cutoff(packet: Mapping[str, Any]) -> bool:
    return _packet_created_before(packet, LEGACY_EXIT_ORDER_MISSING_FIELD_CUTOFF_UTC)


def _packet_created_before_nonterminal_pnl_cutoff(packet: Mapping[str, Any]) -> bool:
    return _packet_created_before(packet, NONTERMINAL_BROKER_REALIZED_PNL_CUTOFF_UTC)


def _packet_created_before(packet: Mapping[str, Any], cutoff: datetime) -> bool:
    value = packet.get("created_at_utc")
    if value in (None, ""):
        return False
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc) < cutoff


def nonterminal_broker_realized_pnl_fields(packet: Mapping[str, Any]) -> list[str]:
    if packet.get("event_type") in TERMINAL_BROKER_REALIZED_EVENTS:
        return []
    found: list[str] = []
    for key in BROKER_REALIZED_PNL_KEYS:
        if packet.get(key) not in (None, ""):
            found.append(key)
    outcome = packet.get("outcome") if isinstance(packet.get("outcome"), Mapping) else {}
    for key in BROKER_REALIZED_PNL_KEYS:
        if outcome.get(key) not in (None, ""):
            found.append(f"outcome.{key}")
    return sorted(set(found))


def is_legacy_nonterminal_broker_realized_pnl_packet(packet: Mapping[str, Any]) -> bool:
    return bool(nonterminal_broker_realized_pnl_fields(packet)) and _packet_created_before_nonterminal_pnl_cutoff(packet)


def build_runtime_learning_packet(
    *,
    namespace: str | None,
    event_type: str,
    ts: str | None = None,
    bridge: Mapping[str, Any] | None = None,
    unit: Mapping[str, Any] | None = None,
    intent: Any | None = None,
    outcome: Mapping[str, Any] | None = None,
    economics: Mapping[str, Any] | None = None,
    decision_bar_iso: str | None = None,
    decision_day: str | None = None,
    source: str = "ultimate_book",
) -> dict[str, Any]:
    bridge_clean = _clean_mapping(dict(bridge or {}))
    unit_clean = _clean_mapping(dict(unit or {})) if unit else None
    outcome_clean = _clean_mapping(dict(outcome or {})) if outcome else {}
    sleeve = getattr(intent, "sleeve", None) if intent is not None else None
    symbol = getattr(intent, "symbol", None) if intent is not None else None
    direction = getattr(intent, "direction", None) if intent is not None else None
    if sleeve is None:
        sleeve = outcome_clean.get("sleeve") or _first_unit_sleeve(unit or {})
    if symbol is None:
        symbol = outcome_clean.get("symbol") or (unit or {}).get("symbol")
    if direction is None:
        direction = outcome_clean.get("direction") or (unit or {}).get("direction")
    if decision_day is None and intent is not None:
        decision_day = getattr(intent, "decision_day", None)
    if decision_bar_iso is None:
        decision_bar_iso = outcome_clean.get("decision_bar_iso") or decision_day
    if decision_day is None:
        decision_day = outcome_clean.get("decision_day")
    if decision_day is None and decision_bar_iso:
        decision_day = str(decision_bar_iso)[:10]

    join = {
        "namespace": namespace,
        "event_type": event_type,
        "sleeve": sleeve,
        "symbol": symbol,
        "direction": direction,
        "decision_bar_iso": decision_bar_iso,
        "decision_day": decision_day,
    }
    decision_window_id = stable_hash(join, prefix="decision_window")
    intent_id = stable_hash(join, prefix="intent")
    outcome_reason = outcome_clean.get("reason") or outcome_clean.get("skip_reason")
    is_skip_event = event_type == "unit_skipped" or outcome_clean.get("placement_status") == "skipped"
    skip_reason = outcome_clean.get("skip_reason")
    if is_skip_event:
        skip_reason = outcome_reason
    decision_reason = outcome_clean.get("decision_reason")
    if decision_reason is None and not is_skip_event:
        decision_reason = outcome_clean.get("reason")
    admission_reason = outcome_clean.get("admission_reason")
    if admission_reason is None and event_type == "unit_admitted":
        admission_reason = decision_reason
    management_action = outcome_clean.get("management_action")
    if management_action is None and (event_type.startswith("position_") or event_type == "breach_flatten"):
        management_action = outcome_clean.get("action")
    exit_missing_fields = outcome_clean.get("exit_reconciliation_missing_fields") or []
    if not isinstance(exit_missing_fields, list):
        exit_missing_fields = []
    else:
        exit_missing_fields = list(exit_missing_fields)
    if (
        event_type == "position_closed"
        and outcome_clean.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
        and outcome_clean.get("broker_exit_order_hash_sha256") in (None, "")
        and "broker_exit_order_ticket" not in exit_missing_fields
    ):
        exit_missing_fields.append("broker_exit_order_ticket")
    admission_unit_members = outcome_clean.get("admission_unit_members") or []
    admission_unit_hash = None
    if isinstance(admission_unit_members, list) and admission_unit_members:
        admission_unit_hash = stable_hash(admission_unit_members, prefix="admission_unit")
    if event_type not in TERMINAL_BROKER_REALIZED_EVENTS:
        for key in BROKER_REALIZED_PNL_KEYS:
            outcome_clean.pop(key, None)
    elif (
        any(outcome_clean.get(key) is not None for key in BROKER_REALIZED_PNL_KEYS - {"broker_realized_pnl_source"})
        and outcome_clean.get("broker_realized_pnl_source") in (None, "")
    ):
        outcome_clean["broker_realized_pnl_source"] = "broker_history_source_unavailable"

    packet = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": ts or _now_iso(),
        "source": source,
        "namespace": namespace,
        "event_type": event_type,
        "decision_window_id": decision_window_id,
        "ultimate_book_intent_id": intent_id,
        "candidate_id": outcome_clean.get("candidate_id") or (unit or {}).get("candidate_id"),
        "sleeve": sleeve,
        "symbol": symbol,
        "broker_symbol": outcome_clean.get("broker_symbol"),
        "broker_entry_deal_hash_sha256": outcome_clean.get("broker_entry_deal_hash_sha256"),
        "entry_reconciliation_status": outcome_clean.get("entry_reconciliation_status"),
        "broker_fill_time_utc": outcome_clean.get("broker_fill_time_utc"),
        "broker_entry_source_status": outcome_clean.get("broker_entry_source_status"),
        "broker_real_entry_label_ready": outcome_clean.get("broker_real_entry_label_ready"),
        "direction": direction,
        "timeframe": outcome_clean.get("timeframe"),
        "decision_bar_iso": decision_bar_iso,
        "decision_day": decision_day,
        "cluster": outcome_clean.get("cluster"),
        "admission_unit_members": admission_unit_members,
        "admission_unit_member_count": outcome_clean.get("admission_unit_member_count"),
        "admission_unit_hash_sha256": admission_unit_hash,
        "placement_key": outcome_clean.get("placement_key"),
        "placement_day_key": outcome_clean.get("placement_day_key"),
        "cluster_day_key": outcome_clean.get("cluster_day_key"),
        "runtime_effect_now": bool(bridge_clean.get("runtime_effect_now", False)),
        "placement_status": outcome_clean.get("placement_status"),
        "skip_reason": skip_reason,
        "decision_reason": decision_reason,
        "admission_reason": admission_reason,
        "management_action": management_action,
        "placement_observed_at_utc": outcome_clean.get("placement_observed_at_utc"),
        "management_checked_at_utc": outcome_clean.get("management_checked_at_utc"),
        "ticket_hash_sha256": outcome_clean.get("ticket_hash_sha256"),
        "joinability_status": outcome_clean.get("joinability_status"),
        "trade_record_joinability_status": outcome_clean.get("trade_record_joinability_status"),
        "trade_record_status": outcome_clean.get("trade_record_status"),
        "trade_lifecycle_status": outcome_clean.get("trade_lifecycle_status"),
        "close_action": outcome_clean.get("close_action"),
        "closed_at_utc": outcome_clean.get("closed_at_utc"),
        "exit_reconciliation_status": outcome_clean.get("exit_reconciliation_status"),
        "exit_reconciliation_attempted": outcome_clean.get("exit_reconciliation_attempted"),
        "exit_reconciliation_source_status": outcome_clean.get("exit_reconciliation_source_status"),
        "exit_reconciliation_missing_fields": exit_missing_fields,
        "broker_exit_deal_hash_sha256": outcome_clean.get("broker_exit_deal_hash_sha256"),
        "broker_exit_order_hash_sha256": outcome_clean.get("broker_exit_order_hash_sha256"),
        "broker_exit_position_hash_sha256": outcome_clean.get("broker_exit_position_hash_sha256"),
        "broker_exit_time_utc": outcome_clean.get("broker_exit_time_utc"),
        "broker_exit_price": outcome_clean.get("broker_exit_price"),
        "broker_exit_profit": outcome_clean.get("broker_exit_profit"),
        "broker_exit_commission": outcome_clean.get("broker_exit_commission"),
        "broker_exit_swap": outcome_clean.get("broker_exit_swap"),
        "broker_exit_fee": outcome_clean.get("broker_exit_fee"),
        "broker_entry_commission": outcome_clean.get("broker_entry_commission"),
        "broker_entry_swap": outcome_clean.get("broker_entry_swap"),
        "broker_position_sl": outcome_clean.get("broker_position_sl"),
        "broker_position_tp": outcome_clean.get("broker_position_tp"),
        "broker_position_price_open": outcome_clean.get("broker_position_price_open"),
        "broker_position_price_current": outcome_clean.get("broker_position_price_current"),
        "broker_position_deal_count": outcome_clean.get("broker_position_deal_count"),
        "broker_position_entry_deal_count": outcome_clean.get("broker_position_entry_deal_count"),
        "broker_position_exit_deal_count": outcome_clean.get("broker_position_exit_deal_count"),
        "broker_position_accounting_coverage_status": outcome_clean.get(
            "broker_position_accounting_coverage_status"
        ),
        "broker_position_aggregate_profit": outcome_clean.get("broker_position_aggregate_profit"),
        "broker_position_aggregate_commission": outcome_clean.get("broker_position_aggregate_commission"),
        "broker_position_aggregate_swap": outcome_clean.get("broker_position_aggregate_swap"),
        "broker_position_aggregate_fee": outcome_clean.get("broker_position_aggregate_fee"),
        "broker_position_realized_pnl": outcome_clean.get("broker_position_realized_pnl"),
        "broker_realized_pnl_source": outcome_clean.get("broker_realized_pnl_source"),
        "broker_realized_pnl": outcome_clean.get("broker_realized_pnl"),
        "rehydration_status": outcome_clean.get("rehydration_status"),
        "rehydration_error": outcome_clean.get("rehydration_error"),
        "gtos_vnext_dynamic_policy_selected": outcome_clean.get("gtos_vnext_dynamic_policy_selected"),
        "gtos_vnext_execution_policy_id": outcome_clean.get("gtos_vnext_execution_policy_id"),
        "gtos_vnext_dynamic_time_stop_bars": outcome_clean.get("gtos_vnext_dynamic_time_stop_bars"),
        "gtos_vnext_dynamic_broker_take_profit_mode": outcome_clean.get(
            "gtos_vnext_dynamic_broker_take_profit_mode"
        ),
        "gtos_vnext_dynamic_no_broker_take_profit": outcome_clean.get(
            "gtos_vnext_dynamic_no_broker_take_profit"
        ),
        "gtos_vnext_book_native_exit_management": outcome_clean.get("gtos_vnext_book_native_exit_management"),
        "policy_clock_status": outcome_clean.get("policy_clock_status"),
        "policy_clock_checked_at_utc": outcome_clean.get("policy_clock_checked_at_utc"),
        "policy_clock_entry_time_utc": outcome_clean.get("policy_clock_entry_time_utc"),
        "policy_clock_source": outcome_clean.get("policy_clock_source"),
        "policy_clock_time_stop_bars": outcome_clean.get("policy_clock_time_stop_bars"),
        "policy_clock_elapsed_m15_bars": outcome_clean.get("policy_clock_elapsed_m15_bars"),
        "policy_clock_bars_until_due": outcome_clean.get("policy_clock_bars_until_due"),
        "policy_clock_overdue_bars": outcome_clean.get("policy_clock_overdue_bars"),
        "policy_clock_close_attempted": outcome_clean.get("policy_clock_close_attempted"),
        "policy_clock_close_result": outcome_clean.get("policy_clock_close_result"),
        "policy_clock_close_reason": outcome_clean.get("policy_clock_close_reason"),
        "policy_clock_targetless": outcome_clean.get("policy_clock_targetless"),
        "policy_clock_vnext_time_stop_active": outcome_clean.get("policy_clock_vnext_time_stop_active"),
        "policy_clock_error": outcome_clean.get("policy_clock_error"),
        "policy_clock_diagnostic": outcome_clean.get("policy_clock_diagnostic"),
        "placement_capture_contract_version": outcome_clean.get("placement_capture_contract_version"),
        "placement_source_completeness_status": outcome_clean.get("placement_source_completeness_status"),
        "placement_source_missing_fields": outcome_clean.get("placement_source_missing_fields") or [],
        "reject_reason": outcome_clean.get("reject_reason"),
        "transient_retry": bool(outcome_clean.get("transient_retry", False)),
        "bar_consumable": outcome_clean.get("bar_consumable"),
        "broker_runtime_change_status": False,
        "candidate_context_status": outcome_clean.get("candidate_context_status"),
        "source_completeness_status": outcome_clean.get("source_completeness_status", "observed_from_runtime_summary"),
        "bridge_reason": bridge_clean.get("reason"),
        "policy_alias": bridge_clean.get("market_expansion_policy"),
        "candidate_book_profile": bridge_clean.get("candidate_book_profile"),
        "market_expansion_policy": bridge_clean.get("market_expansion_policy"),
        "risk_budget_before": outcome_clean.get("risk_budget_before"),
        "risk_budget_after": outcome_clean.get("risk_budget_after"),
        "derisk_reason": outcome_clean.get("derisk_reason"),
        "symbol_damage_verdict": outcome_clean.get("symbol_damage_verdict"),
        "learning_rerate_verdict": outcome_clean.get("learning_rerate_verdict"),
        "spread_r": outcome_clean.get("spread_r"),
        "slippage_source_status": outcome_clean.get("slippage_source_status", "not_measured_in_packet"),
        "swap_source_status": outcome_clean.get("swap_source_status", "config_or_pretrade_packet"),
        "commission_source_status": outcome_clean.get("commission_source_status", "config_or_pretrade_packet"),
        "bridge": bridge_clean,
        "unit": unit_clean,
        "outcome": outcome_clean,
        "redaction_policy": DEFAULT_REDACTION_POLICY,
    }
    # Attached only when populated. An always-present block of nulls is indistinguishable from a
    # block that was never filled, and 79 % of this stream is position_managed -- paying for an
    # empty key on 78,687 packets a month buys nothing a reader could use.
    if economics:
        packet[PACKET_ECONOMICS_KEY] = _clean_mapping(dict(economics))
    packet["source_event_hash_sha256"] = stable_hash(
        {
            k: packet.get(k)
            for k in (
                "namespace",
                "event_type",
                "sleeve",
                "symbol",
                "decision_bar_iso",
                "placement_status",
                "skip_reason",
                "admission_unit_hash_sha256",
            )
        },
        prefix="source_event",
    )
    packet["packet_hash_sha256"] = stable_hash(packet, prefix="runtime_learning_packet")
    return packet


REJECTION_MARKER_NAMESPACE_FALLBACK = "unattributed_namespace"


def build_packet_rejected_marker(
    *,
    namespace: str | None,
    rejected_event_type: str | None,
    rejected_packet_hash: str | None,
    issues: list[str],
    quarantined: bool,
    ts: str | None = None,
) -> dict[str, Any]:
    """A minimal, always-valid packet recording that another packet was refused.

    This is the load-bearing half of the emit-time validator. Dropping a malformed packet and
    logging the fact somewhere else recreates the false-green class: the evidence stream reads
    as complete because the only record of the hole lives outside it. The marker puts the hole
    *in* the stream, so a consumer reading the log alone still sees it.

    Built from a fixed template. The only caller-supplied values are plain strings placed in
    value position -- never as mapping keys -- so the marker cannot inherit the forbidden-key
    or hash-drift failure that rejected the original packet.
    """
    return build_runtime_learning_packet(
        namespace=str(namespace) if namespace else REJECTION_MARKER_NAMESPACE_FALLBACK,
        event_type=PACKET_REJECTED_EVENT_TYPE,
        ts=ts,
        outcome={
            "placement_status": PACKET_REJECTED_EVENT_TYPE,
            "reason": "emit_time_schema_validation_refused",
            "rejected_event_type": str(rejected_event_type) if rejected_event_type else None,
            "rejected_packet_hash_sha256": (
                str(rejected_packet_hash) if rejected_packet_hash else None
            ),
            "rejection_issues": [str(i) for i in issues],
            "rejection_issue_count": len(issues),
            "quarantined": bool(quarantined),
            "source_completeness_status": (
                "packet_quarantined_full_body_in_sidecar"
                if quarantined
                else "packet_refused_body_not_recorded"
            ),
        },
        source="ultimate_book.packet_guard",
    )


def validate_runtime_learning_packet(packet: Mapping[str, Any]) -> tuple[bool, list[str]]:
    issues: list[str] = []
    required = [
        "schema_version",
        "created_at_utc",
        "namespace",
        "event_type",
        "decision_window_id",
        "ultimate_book_intent_id",
        "source_event_hash_sha256",
        "packet_hash_sha256",
        "broker_runtime_change_status",
        "redaction_policy",
    ]
    for key in required:
        if key not in packet or packet.get(key) in (None, ""):
            issues.append(f"missing_required:{key}")
    if packet.get("schema_version") != SCHEMA_VERSION:
        issues.append("schema_version_mismatch")
    if packet.get("event_type") not in EVENT_TYPES:
        issues.append(f"unknown_event_type:{packet.get('event_type')}")
    nonterminal_pnl_fields = nonterminal_broker_realized_pnl_fields(packet)
    if nonterminal_pnl_fields and not _packet_created_before_nonterminal_pnl_cutoff(packet):
        issues.append(
            "non_terminal_broker_realized_pnl_fields:"
            + ",".join(nonterminal_pnl_fields)
        )
    if packet.get("broker_runtime_change_status") is not False:
        issues.append("broker_runtime_change_status_must_be_false")
    if (
        packet.get("event_type") == "unit_placed"
        and packet.get("placement_capture_contract_version") == PLACEMENT_CAPTURE_CONTRACT_VERSION
    ):
        required_placed = [
            "candidate_id",
            "sleeve",
            "symbol",
            "direction",
            "decision_bar_iso",
            "decision_day",
            "placement_observed_at_utc",
            "ticket_hash_sha256",
            "joinability_status",
            "placement_source_completeness_status",
        ]
        for key in required_placed:
            if packet.get(key) in (None, ""):
                issues.append(f"missing_unit_placed_capture_field:{key}")
        if packet.get("placement_source_completeness_status") != PLACEMENT_CAPTURE_COMPLETE_STATUS:
            issues.append("unit_placed_capture_contract_incomplete")
        if packet.get("placement_source_missing_fields"):
            issues.append("unit_placed_capture_missing_fields_not_empty")
        if packet.get("joinability_status") != "ticket_candidate_decision_policy_joinable":
            issues.append("unit_placed_joinability_not_candidate_decision_policy")
    if _is_targetless_time_stop_management_packet(packet):
        required_clock = [
            "policy_clock_status",
            "policy_clock_checked_at_utc",
            "policy_clock_time_stop_bars",
        ]
        for key in required_clock:
            if packet.get(key) in (None, ""):
                issues.append(f"missing_targetless_time_stop_clock_field:{key}")
        status = str(packet.get("policy_clock_status") or "").strip().lower()
        if status in {"not_due", "closed", "close_failed", "due_close_attempted"}:
            for key in (
                "policy_clock_entry_time_utc",
                "policy_clock_source",
                "policy_clock_elapsed_m15_bars",
                "policy_clock_bars_until_due",
                "policy_clock_overdue_bars",
            ):
                if packet.get(key) in (None, ""):
                    issues.append(f"missing_targetless_time_stop_clock_field:{key}")
    if (
        packet.get("event_type") == "position_closed"
        and packet.get("exit_reconciliation_status") == "RECONCILED_FROM_ACCOUNT_HISTORY"
    ):
        missing_exit_fields = packet.get("exit_reconciliation_missing_fields")
        if not isinstance(missing_exit_fields, list):
            missing_exit_fields = []
        for key in ("broker_exit_deal_hash_sha256", "broker_exit_position_hash_sha256"):
            if packet.get(key) in (None, ""):
                issues.append(f"missing_reconciled_exit_capture_field:{key}")
        if packet.get("broker_exit_order_hash_sha256") in (None, "") and (
            "broker_exit_order_ticket" not in missing_exit_fields
        ):
            if not _packet_created_before_legacy_exit_order_cutoff(packet):
                issues.append("missing_reconciled_exit_order_hash_or_missing_field")
    # The economics block is optional and additive: absent is always valid, which is what keeps
    # every pre-existing packet readable. Present-but-malformed is not, because a block that
    # cannot be trusted is worse than one that is not there.
    if PACKET_ECONOMICS_KEY in packet:
        economics = packet.get(PACKET_ECONOMICS_KEY)
        if not isinstance(economics, Mapping):
            issues.append("economics_block_not_a_mapping")
        elif not economics.get("contract_version"):
            issues.append("economics_block_missing_contract_version")
        else:
            holding = economics.get("holding")
            if isinstance(holding, Mapping):
                # A holding time without a provenance label is the exact thing this block exists
                # to prevent: a number a later reader cannot tell measured from modelled.
                if holding.get("holding_seconds") is not None and not holding.get(
                    "holding_provenance"
                ):
                    issues.append("economics_holding_seconds_without_provenance")
    forbidden = _contains_forbidden_raw_key(packet)
    if forbidden:
        issues.append("forbidden_raw_keys:" + ",".join(sorted(set(forbidden))))
    source_hash_keys = (
        "namespace",
        "event_type",
        "sleeve",
        "symbol",
        "decision_bar_iso",
        "placement_status",
        "skip_reason",
        "admission_unit_hash_sha256",
    )
    expected_source_hashes = {
        stable_hash({k: packet.get(k) for k in source_hash_keys}, prefix="source_event")
    }
    if "admission_unit_hash_sha256" not in packet:
        legacy_keys = tuple(k for k in source_hash_keys if k != "admission_unit_hash_sha256")
        expected_source_hashes.add(
            stable_hash({k: packet.get(k) for k in legacy_keys}, prefix="source_event")
        )
    if packet.get("source_event_hash_sha256") and packet.get("source_event_hash_sha256") not in expected_source_hashes:
        issues.append("source_event_hash_mismatch")
    if packet.get("packet_hash_sha256"):
        material = dict(packet)
        existing_hash = material.pop("packet_hash_sha256", None)
        expected_packet_hash = stable_hash(material, prefix="runtime_learning_packet")
        if existing_hash != expected_packet_hash:
            issues.append("packet_hash_mismatch")
    return not issues, issues


def _is_targetless_time_stop_management_packet(packet: Mapping[str, Any]) -> bool:
    if packet.get("event_type") not in {
        "position_adopted",
        "position_managed",
        "position_closed",
        "position_management_error",
        "breach_flatten",
    }:
        return False
    outcome = packet.get("outcome") if isinstance(packet.get("outcome"), Mapping) else {}
    policy = str(
        packet.get("gtos_vnext_dynamic_policy_selected")
        or outcome.get("gtos_vnext_dynamic_policy_selected")
        or ""
    ).strip().lower()
    if policy != "time_stop":
        return False
    no_tp = (
        packet.get("gtos_vnext_dynamic_no_broker_take_profit") is True
        or outcome.get("gtos_vnext_dynamic_no_broker_take_profit") is True
    )
    broker_tp_mode = str(
        packet.get("gtos_vnext_dynamic_broker_take_profit_mode")
        or outcome.get("gtos_vnext_dynamic_broker_take_profit_mode")
        or ""
    ).strip().lower()
    return bool(no_tp or broker_tp_mode == "none")


class RuntimeLearningPacketWriter:
    def __init__(self, repo_root: str | Path, log_path: str = DEFAULT_LOG_PATH):
        self.path = Path(repo_root) / log_path
        self.lock_timeout_seconds = 10.0

    def _lock_path(self) -> Path:
        return self.path.with_name(self.path.name + ".lock")

    @contextlib.contextmanager
    def _append_lock(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self._lock_path()
        handle = lock_path.open("a+b")
        locked = False
        try:
            deadline = time.monotonic() + self.lock_timeout_seconds
            if os.name == "nt":
                import msvcrt

                while True:
                    try:
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                        locked = True
                        break
                    except OSError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(f"runtime learning packet append lock timed out: {lock_path}")
                        time.sleep(0.025)
                try:
                    yield
                finally:
                    if locked:
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                        locked = False
            else:
                import fcntl

                while True:
                    try:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                        locked = True
                        break
                    except BlockingIOError:
                        if time.monotonic() >= deadline:
                            raise TimeoutError(f"runtime learning packet append lock timed out: {lock_path}")
                        time.sleep(0.025)
                try:
                    yield
                finally:
                    if locked:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                        locked = False
        finally:
            handle.close()

    def _recent_packet_hashes_locked(self) -> set[str]:
        if not self.path.exists():
            return set()
        try:
            with self.path.open("rb") as handle:
                handle.seek(0, os.SEEK_END)
                size = handle.tell()
                start = max(0, size - RECENT_APPEND_DEDUPE_BYTES)
                handle.seek(start)
                payload = handle.read()
        except OSError:
            return set()
        if start > 0:
            _partial, sep, payload = payload.partition(b"\n")
            if not sep:
                return set()
        hashes: set[str] = set()
        for raw in payload.splitlines():
            if not raw.strip():
                continue
            try:
                row = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if isinstance(row, dict) and row.get("packet_hash_sha256"):
                hashes.add(str(row.get("packet_hash_sha256")))
        return hashes

    def append(self, packet: Mapping[str, Any]) -> int:
        return self.append_many([packet])

    def append_many(self, packets: list[Mapping[str, Any]]) -> int:
        if not packets:
            return 0
        unique_packets: list[Mapping[str, Any]] = []
        seen_hashes: set[str] = set()
        for packet in packets:
            ok, issues = validate_runtime_learning_packet(packet)
            if not ok:
                raise ValueError(";".join(issues))
            packet_hash = str(packet.get("packet_hash_sha256") or "")
            if packet_hash and packet_hash in seen_hashes:
                continue
            if packet_hash:
                seen_hashes.add(packet_hash)
            unique_packets.append(packet)
        if not unique_packets:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._append_lock():
            recent_hashes = self._recent_packet_hashes_locked()
            unique_packets = [
                packet
                for packet in unique_packets
                if not packet.get("packet_hash_sha256")
                or str(packet.get("packet_hash_sha256")) not in recent_hashes
            ]
            if not unique_packets:
                return 0
            tmp_path = self.path.with_name(self.path.name + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
            try:
                with tmp_path.open("w", encoding="utf-8") as handle:
                    for packet in unique_packets:
                        handle.write(json.dumps(packet, sort_keys=True, default=str) + "\n")
                with self.path.open("a", encoding="utf-8") as target, tmp_path.open("r", encoding="utf-8") as src:
                    target.write(src.read())
            finally:
                tmp_path.unlink(missing_ok=True)
        return len(unique_packets)


def packet_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "log_path_default": DEFAULT_LOG_PATH,
        "redaction_policy": DEFAULT_REDACTION_POLICY,
        "required_fields": [
            "schema_version",
            "created_at_utc",
            "namespace",
            "event_type",
            "decision_window_id",
            "ultimate_book_intent_id",
            "source_event_hash_sha256",
            "packet_hash_sha256",
            "broker_runtime_change_status",
            "redaction_policy",
        ],
        "conditional_unit_placed_capture_contract": {
            "contract_version": PLACEMENT_CAPTURE_CONTRACT_VERSION,
            "complete_status": PLACEMENT_CAPTURE_COMPLETE_STATUS,
            "required_when_contract_version_present": [
                "candidate_id",
                "sleeve",
                "symbol",
                "direction",
                "decision_bar_iso",
                "decision_day",
                "placement_observed_at_utc",
                "ticket_hash_sha256",
                "joinability_status",
                "placement_source_completeness_status",
            ],
        },
        "conditional_targetless_time_stop_management_contract": {
            "applies_when": (
                "event_type is position management/adoption/close/error and "
                "gtos_vnext_dynamic_policy_selected=time_stop with no broker take profit"
            ),
            "required_fields": [
                "policy_clock_status",
                "policy_clock_checked_at_utc",
                "policy_clock_time_stop_bars",
            ],
            "required_when_clock_status_is_due_or_not_due": [
                "policy_clock_entry_time_utc",
                "policy_clock_source",
                "policy_clock_elapsed_m15_bars",
                "policy_clock_bars_until_due",
                "policy_clock_overdue_bars",
            ],
        },
        "forbidden_raw_keys": sorted(FORBIDDEN_RAW_KEYS),
        "event_types": sorted(EVENT_TYPES),
        "optional_fields": [
            PACKET_ECONOMICS_KEY,
        ],
        "optional_economics_block": {
            "key": PACKET_ECONOMICS_KEY,
            "versioned_by": "economics.contract_version, NOT schema_version",
            "sub_blocks": ["holding", "cost", "governor", "features"],
            "provenance_labels": ["measured", "transferred", "modelled", "unavailable"],
            "absent_is_valid": True,
        },
        "evidence_boundary": "runtime_observation_packet_not_broker_real_pnl_claim",
    }


__all__ = [
    "SCHEMA_VERSION",
    "DEFAULT_LOG_PATH",
    "DEFAULT_REDACTION_POLICY",
    "PACKET_ECONOMICS_KEY",
    "PACKET_REJECTED_EVENT_TYPE",
    "RuntimeLearningPacketWriter",
    "build_packet_rejected_marker",
    "build_runtime_learning_packet",
    "packet_schema",
    "is_legacy_nonterminal_broker_realized_pnl_packet",
    "nonterminal_broker_realized_pnl_fields",
    "stable_hash",
    "validate_runtime_learning_packet",
]
