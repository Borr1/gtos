"""Same-symbol / same-instrument lifecycle policy for vNext V4.

This module is deliberately read-only.  It turns broker-local open-position
state, internal pending-intent state, and candidate lifecycle metadata into a
decision packet before any new same-symbol order can be admitted.
"""

from __future__ import annotations

import hashlib
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.mt5.mt5_interface import MAGIC_NUMBER
from src.utils.broker_profile import broker_account_namespace, namespaced_file_path
from src.utils.file_io import atomic_write

logger = logging.getLogger(__name__)


PENDING_INTENT_DIR = "knowledge_base/meta"
LIFECYCLE_STORE_PATH = "knowledge_base/meta/same_symbol_lifecycle_v4_store.json"
DECISION_PACKET_VERSION = "same_symbol_lifecycle_v4_decision_packet_v1"
LIFECYCLE_STORE_SCHEMA_VERSION = "same_symbol_lifecycle_v4_store_v1"
EVIDENCE_CLASS = "production_code_integration_broker_local_read_only"

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

SCALE_ACTIONS = {
    "scale",
    "scale_in",
    "same_direction_scale_in",
}
REDUCE_ACTIONS = {"reduce", "reduce_existing"}
CLOSE_ACTIONS = {"close", "close_existing"}
REVERSE_ACTIONS = {"reverse", "close_and_reverse"}
PENDING_REPLACE_ACTIONS = {"cancel_pending", "replace_pending"}


def symbol_key(value: object) -> str:
    return str(value or "").strip().upper()


def append_symbol_alias(values: list[str], value: object) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


def symbol_aliases_for_config(symbol: str, config: dict | None) -> list[str]:
    """Return broker/strategy aliases for *symbol* using config and known maps."""

    aliases: list[str] = []
    append_symbol_alias(aliases, symbol)
    if isinstance(config, dict):
        market = config.get("market") or {}
        if isinstance(market, dict):
            market_values = [
                market.get("symbol"),
                market.get("mt5_symbol"),
                market.get("broker_symbol"),
            ]
            market_keys = {symbol_key(value) for value in market_values if value}
            target_keys = {symbol_key(value) for value in aliases}
            if target_keys & market_keys:
                for value in market_values:
                    append_symbol_alias(aliases, value)
        instruments = config.get("instruments") or {}
        target_keys = {symbol_key(value) for value in aliases}
        if isinstance(instruments, dict):
            for instrument_name, instrument_cfg in instruments.items():
                instrument_market = (
                    instrument_cfg.get("market") or {}
                    if isinstance(instrument_cfg, dict)
                    else {}
                )
                instrument_values = [instrument_name]
                if isinstance(instrument_market, dict):
                    instrument_values.extend(
                        [
                            instrument_market.get("symbol"),
                            instrument_market.get("mt5_symbol"),
                            instrument_market.get("broker_symbol"),
                        ]
                    )
                instrument_keys = {
                    symbol_key(value) for value in instrument_values if value
                }
                if target_keys & instrument_keys:
                    for value in instrument_values:
                        append_symbol_alias(aliases, value)
                    target_keys = {symbol_key(value) for value in aliases}
    idx = 0
    while idx < len(aliases):
        mapped = VNEXT_BROKER_SYMBOL_ALIASES.get(symbol_key(aliases[idx]))
        if mapped:
            append_symbol_alias(aliases, mapped)
        idx += 1
    return aliases


def position_side(position: Any) -> str | None:
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


def _read(source: Any, *keys: str, default: Any = None) -> Any:
    if source is None:
        return default
    for key in keys:
        if isinstance(source, dict) and key in source:
            return source.get(key)
        if hasattr(source, key):
            return getattr(source, key)
    return default


def _read_float(source: Any, *keys: str) -> float | None:
    value = _read(source, *keys)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_bool(source: Any, *keys: str) -> bool | None:
    value = _read(source, *keys)
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return None


def _normalize_action(value: Any) -> str | None:
    text = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return text or None


def _stable_sha256(payload: Any) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class CandidateLifecycleContext:
    symbol: str
    aliases: list[str]
    side: str | None
    requested_action: str | None
    risk_pct: float | None
    probability: float | None
    ev_r: float | None
    thesis_id: str | None
    candidate_id: str | None
    freshness_status: str
    source_completeness_status: str
    poi_id: str | None = None
    poi_state_hash_sha256: str | None = None
    poi_state: dict[str, Any] = field(default_factory=dict)
    causal_poi_lifecycle_required: bool = False
    causal_poi_lifecycle: dict[str, Any] = field(default_factory=dict)
    causal_poi_lifecycle_hash_sha256: str | None = None
    canonical_replay_candidate_instance_key: str | None = None
    source_bound_replay_candidate_instance_key: str | None = None
    candidate_instance_identity_status: str | None = None
    proof: dict[str, Any] = field(default_factory=dict)

    def snapshot(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "aliases": self.aliases,
            "side": self.side,
            "requested_action": self.requested_action,
            "risk_pct": self.risk_pct,
            "probability": self.probability,
            "ev_r": self.ev_r,
            "thesis_id": self.thesis_id,
            "candidate_id": self.candidate_id,
            "freshness_status": self.freshness_status,
            "source_completeness_status": self.source_completeness_status,
            "poi_id": self.poi_id,
            "poi_state_hash_sha256": self.poi_state_hash_sha256,
            "poi_state": dict(self.poi_state),
            "causal_poi_lifecycle_required": self.causal_poi_lifecycle_required,
            "causal_poi_lifecycle": dict(self.causal_poi_lifecycle),
            "causal_poi_lifecycle_hash_sha256": (
                self.causal_poi_lifecycle_hash_sha256
            ),
            "canonical_replay_candidate_instance_key": (
                self.canonical_replay_candidate_instance_key
            ),
            "source_bound_replay_candidate_instance_key": (
                self.source_bound_replay_candidate_instance_key
            ),
            "candidate_instance_identity_status": (
                self.candidate_instance_identity_status
            ),
            "proof": self.proof,
        }


@dataclass(frozen=True)
class TicketLifecycleSnapshot:
    ticket: int | None
    symbol: str | None
    side: str | None
    volume: float | None
    price_open: float | None
    sl: float | None
    tp: float | None
    magic: int | None
    thesis_id: str | None
    risk_pct: float | None
    probability_at_entry: float | None
    ev_r_at_entry: float | None
    lifecycle_phase: str
    source_status: str
    stale_thesis: bool
    partial_state: str | None
    be_state: str | None
    trailing_state: str | None

    @classmethod
    def from_position(
        cls,
        position: Any,
        *,
        lifecycle_store: Mapping[str, Any] | None = None,
    ) -> "TicketLifecycleSnapshot":
        ticket = _read(position, "ticket")
        store_entry = _ticket_store_entry(lifecycle_store, ticket)
        phase = str(
            _first_present(
                _read(
                    position,
                    "gtos_vnext_lifecycle_phase",
                    "lifecycle_phase",
                    "phase",
                ),
                store_entry.get("lifecycle_phase"),
                "open",
            )
        ).strip().lower()
        stale = bool(
            _first_present(
                _read_bool(position, "gtos_vnext_stale_thesis", "stale_thesis"),
                store_entry.get("stale_thesis"),
            )
            or phase in {"stale", "stale_thesis"}
        )
        thesis_id = _as_text(
            _first_present(
                _read(
                    position,
                    "gtos_vnext_thesis_id",
                    "thesis_id",
                    "candidate_id",
                    "gtos_vnext_selector_row_id",
                ),
                store_entry.get("thesis_id"),
                _read(position, "comment"),
            )
        )
        source_status = _as_text(
            _first_present(
                _read(position, "source_status"),
                (
                    "broker_position_snapshot_with_durable_lifecycle_store"
                    if store_entry
                    else None
                ),
            )
        ) or "broker_position_snapshot"
        return cls(
            ticket=ticket,
            symbol=_first_present(_read(position, "symbol"), store_entry.get("symbol")),
            side=_first_present(position_side(position), store_entry.get("side")),
            volume=_first_present(_read_float(position, "volume"), store_entry.get("volume")),
            price_open=_first_present(
                _read_float(position, "price_open"),
                store_entry.get("price_open"),
            ),
            sl=_first_present(_read_float(position, "sl"), store_entry.get("sl")),
            tp=_first_present(_read_float(position, "tp"), store_entry.get("tp")),
            magic=_first_present(_read(position, "magic"), store_entry.get("magic")),
            thesis_id=thesis_id,
            risk_pct=_first_present(
                _read_float(
                    position,
                    "gtos_vnext_selected_cell_risk_pct",
                    "risk_pct",
                    "risk_pct_at_entry",
                ),
                store_entry.get("risk_pct"),
            ),
            probability_at_entry=_first_present(
                _read_float(
                    position,
                    "gtos_vnext_probability_at_entry",
                    "probability_at_entry",
                    "candidate_probability_at_entry",
                ),
                store_entry.get("probability_at_entry"),
            ),
            ev_r_at_entry=_first_present(
                _read_float(
                    position,
                    "gtos_vnext_ev_r_at_entry",
                    "ev_r_at_entry",
                    "candidate_ev_r_at_entry",
                ),
                store_entry.get("ev_r_at_entry"),
            ),
            lifecycle_phase=phase,
            source_status=source_status,
            stale_thesis=stale,
            partial_state=_as_text(
                _first_present(
                    _read(position, "partial_state", "gtos_vnext_partial_state"),
                    store_entry.get("partial_state"),
                )
            ),
            be_state=_as_text(
                _first_present(
                    _read(position, "be_state", "gtos_vnext_be_state"),
                    store_entry.get("be_state"),
                )
            ),
            trailing_state=_as_text(
                _first_present(
                    _read(position, "trailing_state", "gtos_vnext_trailing_state"),
                    store_entry.get("trailing_state"),
                )
            ),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "ticket": self.ticket,
            "symbol": self.symbol,
            "side": self.side,
            "volume": self.volume,
            "price_open": self.price_open,
            "sl": self.sl,
            "tp": self.tp,
            "magic": self.magic,
            "thesis_id": self.thesis_id,
            "risk_pct": self.risk_pct,
            "probability_at_entry": self.probability_at_entry,
            "ev_r_at_entry": self.ev_r_at_entry,
            "lifecycle_phase": self.lifecycle_phase,
            "source_status": self.source_status,
            "stale_thesis": self.stale_thesis,
            "partial_state": self.partial_state,
            "be_state": self.be_state,
            "trailing_state": self.trailing_state,
        }


@dataclass(frozen=True)
class PendingLifecycleSnapshot:
    pending_id: str | None
    source_path: str | None
    symbol: str | None
    side: str | None
    entry_price: float | None
    stop_loss: float | None
    take_profit_1: float | None
    risk_pct: float | None
    created_time_utc: str | None
    expiry_candles: int | None
    broker_pending_order_created: bool | None
    mt5_order_ticket: int | None
    native_pending_order_type: str | None
    source_status: str
    candidate_id: str | None = None
    decision_time_utc: str | None = None
    poi_id: str | None = None
    poi_state_hash_sha256: str | None = None
    causal_poi_lifecycle_required: bool | None = None
    causal_poi_lifecycle: dict[str, Any] = field(default_factory=dict)
    causal_poi_lifecycle_hash_sha256: str | None = None
    canonical_replay_candidate_instance_key: str | None = None
    source_bound_replay_candidate_instance_key: str | None = None
    candidate_instance_identity_status: str | None = None

    @classmethod
    def from_intent(
        cls,
        intent: Any,
        *,
        source_path: str | None,
        source_status: str = "persisted_internal_pending_intent",
    ) -> "PendingLifecycleSnapshot":
        return cls(
            pending_id=_as_text(
                _read(intent, "pending_id", "trade_id", "candidate_id", "simulated_order_id")
            ),
            source_path=source_path or _as_text(_read(intent, "source_path")),
            symbol=_as_text(_read(intent, "source_symbol", "symbol", "broker_symbol")),
            side=_as_text(_read(intent, "direction", "side")),
            entry_price=_read_float(intent, "limit_price", "entry_price"),
            stop_loss=_read_float(intent, "stop_loss"),
            take_profit_1=_read_float(intent, "take_profit_1"),
            risk_pct=_read_float(
                intent, "gtos_vnext_selected_cell_risk_pct", "risk_pct"
            ),
            created_time_utc=_as_text(
                _read(
                    intent,
                    "placed_time",
                    "created_time_utc",
                    "pending_created_time_utc",
                    "decision_time_utc",
                    "order_created_time_utc",
                )
            ),
            expiry_candles=_read(intent, "expiry_candles"),
            broker_pending_order_created=_read_bool(intent, "broker_pending_order_created"),
            mt5_order_ticket=_read(intent, "mt5_order_ticket"),
            native_pending_order_type=_as_text(_read(intent, "native_pending_order_type")),
            source_status=source_status,
            candidate_id=_as_text(_read(intent, "candidate_id")),
            decision_time_utc=_as_text(
                _read(
                    intent,
                    "decision_time_utc",
                    "candle_close_utc",
                    "source_candle_time_utc",
                )
            ),
            poi_id=_as_text(_read(intent, "poi_id")),
            poi_state_hash_sha256=_as_text(
                _read(intent, "poi_state_hash_sha256")
            ),
            causal_poi_lifecycle_required=_read_bool(
                intent,
                "causal_poi_lifecycle_required",
            ),
            causal_poi_lifecycle=(
                dict(_read(intent, "causal_poi_lifecycle"))
                if isinstance(_read(intent, "causal_poi_lifecycle"), Mapping)
                else {}
            ),
            causal_poi_lifecycle_hash_sha256=_as_text(
                _read(intent, "causal_poi_lifecycle_hash_sha256")
            ),
            canonical_replay_candidate_instance_key=_as_text(
                _read(intent, "canonical_replay_candidate_instance_key")
            ),
            source_bound_replay_candidate_instance_key=_as_text(
                _read(intent, "source_bound_replay_candidate_instance_key")
            ),
            candidate_instance_identity_status=_as_text(
                _read(intent, "candidate_instance_identity_status")
            ),
        )

    def snapshot(self) -> dict[str, Any]:
        return {
            "pending_id": self.pending_id,
            "source_path": self.source_path,
            "symbol": self.symbol,
            "side": self.side,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit_1": self.take_profit_1,
            "risk_pct": self.risk_pct,
            "created_time_utc": self.created_time_utc,
            "expiry_candles": self.expiry_candles,
            "broker_pending_order_created": self.broker_pending_order_created,
            "mt5_order_ticket": self.mt5_order_ticket,
            "native_pending_order_type": self.native_pending_order_type,
            "source_status": self.source_status,
            "candidate_id": self.candidate_id,
            "decision_time_utc": self.decision_time_utc,
            "poi_id": self.poi_id,
            "poi_state_hash_sha256": self.poi_state_hash_sha256,
            "causal_poi_lifecycle_required": self.causal_poi_lifecycle_required,
            "causal_poi_lifecycle": dict(self.causal_poi_lifecycle),
            "causal_poi_lifecycle_hash_sha256": (
                self.causal_poi_lifecycle_hash_sha256
            ),
            "canonical_replay_candidate_instance_key": (
                self.canonical_replay_candidate_instance_key
            ),
            "source_bound_replay_candidate_instance_key": (
                self.source_bound_replay_candidate_instance_key
            ),
            "candidate_instance_identity_status": (
                self.candidate_instance_identity_status
            ),
        }


@dataclass(frozen=True)
class PendingSourceResult:
    snapshots: list[PendingLifecycleSnapshot]
    source_errors: list[dict[str, Any]]
    paths_checked: list[str]


@dataclass(frozen=True)
class SameSymbolLifecycleDecision:
    action: str
    permitted_order_intent: bool
    reason: str
    selected_tickets: list[int | None]
    parent_ticket: int | None
    parent_thesis_id: str | None
    close_ticket: int | None
    reverse_intent_id: str | None
    scale_in_risk_delta_pct: float | None
    rejected_alternatives: list[dict[str, Any]]
    vetoes: list[dict[str, Any]]
    source_completeness: dict[str, Any]
    evidence_class: str
    freshness: dict[str, Any]
    broker_local_risk_result: dict[str, Any]
    candidate: CandidateLifecycleContext
    open_positions: list[TicketLifecycleSnapshot]
    pending_orders: list[PendingLifecycleSnapshot]

    def to_packet(self) -> dict[str, Any]:
        candidate_snapshot = self.candidate.snapshot()
        open_snapshots = [row.snapshot() for row in self.open_positions]
        pending_snapshots = [row.snapshot() for row in self.pending_orders]
        durable_capture = durable_lifecycle_capture_contract(
            candidate_snapshot=candidate_snapshot,
            open_position_snapshots=open_snapshots,
            pending_order_snapshots=pending_snapshots,
        )
        source_material = {
            "action": self.action,
            "candidate": candidate_snapshot,
            "open_position_snapshot": open_snapshots,
            "pending_order_snapshot": pending_snapshots,
            "source_completeness": self.source_completeness,
            "freshness": self.freshness,
            "durable_lifecycle_capture": durable_capture,
        }
        packet = {
            "decision_packet_version": DECISION_PACKET_VERSION,
            "action": self.action,
            "permitted_order_intent": self.permitted_order_intent,
            "reason": self.reason,
            "selected_tickets": self.selected_tickets,
            "parent_ticket": self.parent_ticket,
            "parent_thesis_id": self.parent_thesis_id,
            "close_ticket": self.close_ticket,
            "reverse_intent_id": self.reverse_intent_id,
            "scale_in_risk_delta_pct": self.scale_in_risk_delta_pct,
            "rejected_alternatives": self.rejected_alternatives,
            "vetoes": self.vetoes,
            "source_completeness": self.source_completeness,
            "evidence_class": self.evidence_class,
            "freshness": self.freshness,
            "broker_local_risk_result": self.broker_local_risk_result,
            "candidate": candidate_snapshot,
            "open_position_snapshot": open_snapshots,
            "pending_order_snapshot": pending_snapshots,
            "durable_lifecycle_capture": durable_capture,
            "source_event_hash_sha256": _stable_sha256(source_material),
        }
        packet["packet_hash_sha256"] = _stable_sha256(packet)
        return packet


def _as_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _lifecycle_cfg(config: dict | None) -> dict[str, Any]:
    cfg = (config or {}).get("same_symbol_lifecycle_v4")
    if not isinstance(cfg, dict):
        risk_cfg = (config or {}).get("risk")
        if isinstance(risk_cfg, dict):
            cfg = risk_cfg.get("same_symbol_lifecycle_v4")
    return dict(cfg or {}) if isinstance(cfg, dict) else {}


def same_symbol_lifecycle_store_path(config: dict | None) -> Path:
    cfg = _lifecycle_cfg(config)
    raw_path = (
        cfg.get("lifecycle_store_path")
        or cfg.get("durable_lifecycle_store_path")
        or LIFECYCLE_STORE_PATH
    )
    return namespaced_file_path(Path(str(raw_path)), broker_account_namespace(config))


def load_same_symbol_lifecycle_store(config: dict | None) -> dict[str, Any]:
    path = same_symbol_lifecycle_store_path(config)
    if not path.exists():
        return {
            "schema_version": LIFECYCLE_STORE_SCHEMA_VERSION,
            "store_path": str(path),
            "tickets": {},
            "source_status": "durable_lifecycle_store_missing_empty",
        }
    try:
        payload = json.loads(path.read_text())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Same-symbol lifecycle store unreadable: %s", exc)
        return {
            "schema_version": LIFECYCLE_STORE_SCHEMA_VERSION,
            "store_path": str(path),
            "tickets": {},
            "source_status": "durable_lifecycle_store_unreadable",
            "source_error": str(exc),
        }
    if not isinstance(payload, dict):
        return {
            "schema_version": LIFECYCLE_STORE_SCHEMA_VERSION,
            "store_path": str(path),
            "tickets": {},
            "source_status": "durable_lifecycle_store_invalid_shape",
        }
    tickets = payload.get("tickets")
    if not isinstance(tickets, dict):
        payload["tickets"] = {}
    payload.setdefault("schema_version", LIFECYCLE_STORE_SCHEMA_VERSION)
    payload.setdefault("store_path", str(path))
    payload.setdefault("source_status", "durable_lifecycle_store_loaded")
    return payload


def _ticket_store_entry(
    lifecycle_store: Mapping[str, Any] | None,
    ticket: Any,
) -> dict[str, Any]:
    if not isinstance(lifecycle_store, Mapping) or ticket in (None, ""):
        return {}
    tickets = lifecycle_store.get("tickets")
    if not isinstance(tickets, Mapping):
        return {}
    keys = [str(ticket)]
    try:
        keys.append(str(int(ticket)))
    except (TypeError, ValueError):
        pass
    for key in keys:
        entry = tickets.get(key)
        if isinstance(entry, Mapping):
            return dict(entry)
    return {}


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def record_same_symbol_lifecycle_entry_v4(
    *,
    config: dict | None,
    ticket: Any,
    symbol: str,
    side: str,
    trade_params: Mapping[str, Any],
    trade_state: Any = None,
    lifecycle_packet: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist V4 thesis/risk lifecycle metadata for future broker-ticket reads."""

    if ticket in (None, ""):
        raise ValueError("ticket is required for same-symbol lifecycle store")
    path = same_symbol_lifecycle_store_path(config)
    store = load_same_symbol_lifecycle_store(config)
    tickets = store.setdefault("tickets", {})
    if not isinstance(tickets, dict):
        tickets = {}
        store["tickets"] = tickets

    side_key = str(side or trade_params.get("direction") or "").strip().upper()
    thesis_id = _as_text(
        _first_present(
            trade_params.get("gtos_vnext_thesis_id"),
            trade_params.get("thesis_id"),
            trade_params.get("candidate_thesis_id"),
            trade_params.get("gtos_vnext_selector_row_id"),
            trade_params.get("gtos_vnext_selected_cell_risk_cell_id"),
        )
    )
    entry = {
        "schema_version": LIFECYCLE_STORE_SCHEMA_VERSION,
        "ticket": ticket,
        "symbol": symbol,
        "side": side_key or None,
        "volume": _read_float(trade_state, "current_volume", "initial_volume"),
        "price_open": _read_float(trade_state, "entry_price"),
        "sl": _read_float(trade_state, "stop_loss"),
        "tp": _read_float(trade_state, "take_profit_1"),
        "magic": MAGIC_NUMBER,
        "thesis_id": thesis_id,
        "candidate_id": _as_text(
            _first_present(
                trade_params.get("candidate_id"),
                trade_params.get("gtos_vnext_candidate_id"),
                trade_params.get("gtos_vnext_selector_row_id"),
            )
        ),
        "risk_pct": _read_float(
            trade_params,
            "gtos_vnext_selected_cell_risk_pct",
            "risk_pct",
        ),
        "probability_at_entry": _candidate_probability(trade_params, side_key),
        "ev_r_at_entry": _read_float(
            trade_params,
            "gtos_vnext_candidate_ev_r",
            "gtos_vnext_expected_value_r",
            "expected_value_r",
            "ev_r",
        ),
        "lifecycle_phase": "open",
        "source_status": "durable_same_symbol_lifecycle_store_v4",
        "stale_thesis": False,
        "partial_state": "not_partial",
        "be_state": "initial_stop",
        "trailing_state": "not_trailing",
        "decision_time_utc": trade_params.get("decision_time_utc"),
        "source_hash": trade_params.get("source_hash"),
        "source_event_hash_sha256": trade_params.get("gtos_vnext_source_event_hash"),
        "selector_row_id": trade_params.get("gtos_vnext_selector_row_id"),
        "selector_proof_hash": trade_params.get("gtos_vnext_selector_proof_hash"),
        "execution_policy_id": trade_params.get("gtos_vnext_execution_policy_id"),
        "dynamic_policy_selected": trade_params.get("gtos_vnext_dynamic_policy_selected"),
        "same_symbol_lifecycle_action": trade_params.get(
            "gtos_vnext_same_symbol_lifecycle_action"
        ),
        "same_symbol_lifecycle_reason": trade_params.get(
            "gtos_vnext_same_symbol_lifecycle_reason"
        ),
        "same_symbol_lifecycle_packet_hash": (
            lifecycle_packet or trade_params.get("gtos_vnext_same_symbol_lifecycle_v4_packet") or {}
        ).get("packet_hash_sha256")
        if isinstance(
            lifecycle_packet
            or trade_params.get("gtos_vnext_same_symbol_lifecycle_v4_packet"),
            Mapping,
        )
        else None,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    entry["record_hash_sha256"] = _stable_sha256(entry)
    tickets[str(ticket)] = entry
    store.update(
        {
            "schema_version": LIFECYCLE_STORE_SCHEMA_VERSION,
            "store_path": str(path),
            "source_status": "durable_lifecycle_store_loaded",
            "updated_at_utc": entry["captured_at_utc"],
        }
    )
    atomic_write(path, store)
    return {**entry, "store_path": str(path)}


def lifecycle_policy_config(config: dict | None) -> dict[str, Any]:
    cfg = _lifecycle_cfg(config)
    return {
        "enabled": bool(cfg.get("enabled", True)),
        "apply_to_vnext_governed_trade": bool(
            cfg.get("apply_to_vnext_governed_trade", True)
        ),
        "pending_intent_source_enabled": bool(
            cfg.get("pending_intent_source_enabled", True)
        ),
        "max_open_same_symbol_tickets": int(cfg.get("max_open_same_symbol_tickets", 1)),
        "max_same_symbol_risk_pct": float(cfg.get("max_same_symbol_risk_pct", 1.0)),
        "scale_in_enabled": bool(cfg.get("scale_in_enabled", True)),
        "scale_in_requires_explicit_action": bool(
            cfg.get("scale_in_requires_explicit_action", True)
        ),
        "scale_in_requires_same_thesis": bool(
            cfg.get("scale_in_requires_same_thesis", True)
        ),
        "scale_in_min_probability_delta": float(
            cfg.get("scale_in_min_probability_delta", 0.03)
        ),
        "scale_in_min_ev_delta_r": float(cfg.get("scale_in_min_ev_delta_r", 0.05)),
        "close_reverse_requires_execution_manager": bool(
            cfg.get("close_reverse_requires_execution_manager", True)
        ),
        "durable_candidate_capture_required": bool(
            cfg.get("durable_candidate_capture_required", True)
        ),
        "durable_ticket_capture_required": bool(
            cfg.get("durable_ticket_capture_required", True)
        ),
        "source_unavailable_policy": str(
            cfg.get("source_unavailable_policy", "fail_closed")
        ),
    }


def durable_lifecycle_capture_contract(
    *,
    candidate_snapshot: dict[str, Any],
    open_position_snapshots: list[dict[str, Any]],
    pending_order_snapshots: list[dict[str, Any]],
) -> dict[str, Any]:
    missing: list[str] = []
    for field_name in (
        "candidate_id",
        "thesis_id",
        "risk_pct",
        "probability",
        "ev_r",
        "source_completeness_status",
    ):
        if candidate_snapshot.get(field_name) in (None, ""):
            missing.append(f"candidate.{field_name}")
    for index, position in enumerate(open_position_snapshots):
        for field_name in (
            "ticket",
            "symbol",
            "side",
            "thesis_id",
            "lifecycle_phase",
            "source_status",
        ):
            if position.get(field_name) in (None, ""):
                missing.append(f"open_position_snapshot[{index}].{field_name}")
    for index, pending in enumerate(pending_order_snapshots):
        for field_name in (
            "pending_id",
            "symbol",
            "side",
            "created_time_utc",
            "source_status",
        ):
            if pending.get(field_name) in (None, ""):
                missing.append(f"pending_order_snapshot[{index}].{field_name}")
        if pending.get("source_path") in (None, "") and pending.get("mt5_order_ticket") in (
            None,
            "",
        ):
            missing.append(
                f"pending_order_snapshot[{index}].source_path_or_mt5_order_ticket"
            )
    material = {
        "candidate": candidate_snapshot,
        "open_position_snapshot": open_position_snapshots,
        "pending_order_snapshot": pending_order_snapshots,
        "missing_fields": sorted(dict.fromkeys(missing)),
    }
    return {
        "status": "complete" if not missing else "source_gap",
        "missing_fields": sorted(dict.fromkeys(missing)),
        "candidate_capture_required": True,
        "ticket_capture_required": True,
        "pending_capture_required": True,
        "capture_hash_sha256": _stable_sha256(material),
    }


def build_candidate_lifecycle_context(
    *,
    symbol: str,
    aliases: list[str],
    trade_params: Any,
    proof: dict[str, Any] | None = None,
) -> CandidateLifecycleContext:
    tp = _read(trade_params, "trade_parameters", default=None) or trade_params

    def candidate_value(*keys: str, default: Any = None) -> Any:
        value = _read(tp, *keys)
        if value not in (None, ""):
            return value
        if tp is not trade_params:
            value = _read(trade_params, *keys)
            if value not in (None, ""):
                return value
        return default

    def candidate_float(*keys: str) -> float | None:
        value = candidate_value(*keys)
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def candidate_bool(*keys: str) -> bool | None:
        value = candidate_value(*keys)
        if isinstance(value, bool):
            return value
        if value is None:
            return None
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
        return None

    side = _as_text(candidate_value("direction"))
    if side:
        side = side.upper()
    requested_action = _normalize_action(
        candidate_value(
            "gtos_vnext_same_symbol_lifecycle_action",
            "same_symbol_lifecycle_action",
            "gtos_vnext_lifecycle_action",
            "lifecycle_action",
        )
    )
    probability = _candidate_probability(tp, side)
    if probability is None and tp is not trade_params:
        probability = _candidate_probability(trade_params, side)
    ev_r = candidate_float(
        "gtos_vnext_candidate_ev_r",
        "gtos_vnext_expected_value_r",
        "expected_value_r",
        "ev_r",
    )
    thesis_id = _as_text(
        candidate_value(
            "gtos_vnext_thesis_id",
            "thesis_id",
            "candidate_thesis_id",
            "gtos_vnext_selector_row_id",
            "gtos_vnext_selected_cell_risk_cell_id",
        )
    )
    candidate_id = _as_text(
        candidate_value(
            "candidate_id",
            "gtos_vnext_candidate_id",
            "gtos_vnext_selector_row_id",
        )
    )
    poi_state = candidate_value("poi_state")
    lifecycle = candidate_value("causal_poi_lifecycle")
    return CandidateLifecycleContext(
        symbol=symbol,
        aliases=list(aliases),
        side=side,
        requested_action=requested_action,
        risk_pct=candidate_float(
            "gtos_vnext_selected_cell_risk_pct",
            "risk_pct",
        ),
        probability=probability,
        ev_r=ev_r,
        thesis_id=thesis_id,
        candidate_id=candidate_id,
        freshness_status=str(
            candidate_value(
                "gtos_vnext_freshness_status",
                "freshness_status",
                default="current",
            )
            or "current"
        ),
        source_completeness_status=str(
            candidate_value(
                "gtos_vnext_source_completeness_status",
                "source_completeness_status",
                default="runtime_candidate_packet",
            )
            or "runtime_candidate_packet"
        ),
        poi_id=_as_text(candidate_value("poi_id")),
        poi_state_hash_sha256=_as_text(
            candidate_value("poi_state_hash_sha256")
        ),
        poi_state=(
            dict(poi_state)
            if isinstance(poi_state, Mapping)
            else {}
        ),
        causal_poi_lifecycle_required=bool(
            candidate_bool("causal_poi_lifecycle_required")
            or isinstance(lifecycle, Mapping)
        ),
        causal_poi_lifecycle=(
            dict(lifecycle)
            if isinstance(lifecycle, Mapping)
            else {}
        ),
        causal_poi_lifecycle_hash_sha256=_as_text(
            candidate_value("causal_poi_lifecycle_hash_sha256")
        ),
        canonical_replay_candidate_instance_key=_as_text(
            candidate_value("canonical_replay_candidate_instance_key")
        ),
        source_bound_replay_candidate_instance_key=_as_text(
            candidate_value("source_bound_replay_candidate_instance_key")
        ),
        candidate_instance_identity_status=_as_text(
            candidate_value("candidate_instance_identity_status")
        ),
        proof=dict(proof or {}),
    )


def _candidate_probability(source: Any, side: str | None) -> float | None:
    side_key = (side or "").strip().lower()
    if side_key:
        value = _read_float(source, f"gtos_vnext_probability_{side_key}")
        if value is not None:
            return value
    return _read_float(
        source,
        "gtos_vnext_candidate_probability",
        "gtos_vnext_probability",
        "probability",
    )


def load_same_symbol_pending_intents(
    *,
    symbol: str,
    aliases: list[str],
    config: dict | None,
) -> PendingSourceResult:
    """Read persisted internal pending intents for the same symbol aliases."""

    policy = lifecycle_policy_config(config)
    if not policy["pending_intent_source_enabled"]:
        return PendingSourceResult([], [], [])

    pending_cfg = (config or {}).get("same_symbol_lifecycle_v4")
    if not isinstance(pending_cfg, dict):
        risk_cfg = (config or {}).get("risk")
        if isinstance(risk_cfg, dict):
            pending_cfg = risk_cfg.get("same_symbol_lifecycle_v4")
    if not isinstance(pending_cfg, dict):
        pending_cfg = {}
    pending_dir = Path(pending_cfg.get("pending_intent_dir") or PENDING_INTENT_DIR)
    namespace = broker_account_namespace(config)
    expected_paths: list[Path] = []
    for alias in aliases or [symbol]:
        base = pending_dir / f"pending_intent_{str(alias).strip()}.pkl"
        expected_paths.append(namespaced_file_path(base, namespace))

    snapshots: list[PendingLifecycleSnapshot] = []
    source_errors: list[dict[str, Any]] = []
    paths_checked: list[str] = []
    seen_paths: set[Path] = set()
    alias_keys = {symbol_key(alias) for alias in aliases}
    for path in expected_paths:
        if path in seen_paths:
            continue
        seen_paths.add(path)
        paths_checked.append(str(path))
        if not path.exists():
            continue
        try:
            with path.open("rb") as handle:
                intent = pickle.load(handle)
        except Exception as exc:  # noqa: BLE001
            source_errors.append(
                {
                    "path": str(path),
                    "error": str(exc),
                    "source_status": "persisted_pending_intent_unreadable",
                }
            )
            continue
        snapshot = PendingLifecycleSnapshot.from_intent(
            intent,
            source_path=str(path),
        )
        snapshot_keys = {
            symbol_key(value)
            for value in (snapshot.symbol, _read(intent, "source_symbol"), symbol)
            if value
        }
        if not snapshot.symbol or snapshot_keys & alias_keys:
            snapshots.append(snapshot)
    return PendingSourceResult(snapshots, source_errors, paths_checked)


def evaluate_same_symbol_lifecycle_v4(
    *,
    candidate: CandidateLifecycleContext,
    open_positions: list[TicketLifecycleSnapshot],
    pending_orders: list[PendingLifecycleSnapshot] | None = None,
    pending_source_errors: list[dict[str, Any]] | None = None,
    config: dict | None = None,
) -> SameSymbolLifecycleDecision:
    policy = lifecycle_policy_config(config)
    pending_orders = list(pending_orders or [])
    pending_source_errors = list(pending_source_errors or [])
    alias_keys = {symbol_key(alias) for alias in candidate.aliases}
    same_positions = [
        pos
        for pos in open_positions
        if symbol_key(pos.symbol) in alias_keys and pos.magic == MAGIC_NUMBER
    ]
    same_pending = [
        row
        for row in pending_orders
        if not row.symbol or symbol_key(row.symbol) in alias_keys
    ]
    source_completeness = {
        "position_source_status": "readable",
        "pending_source_status": (
            "source_error" if pending_source_errors else "readable"
        ),
        "pending_source_errors": pending_source_errors,
        "candidate_source_completeness_status": candidate.source_completeness_status,
    }
    freshness = {
        "candidate_freshness_status": candidate.freshness_status,
        "position_snapshot_status": "current_broker_local_read",
        "pending_snapshot_status": "persisted_internal_intent_read",
    }
    capture_contract = durable_lifecycle_capture_contract(
        candidate_snapshot=candidate.snapshot(),
        open_position_snapshots=[row.snapshot() for row in same_positions],
        pending_order_snapshots=[row.snapshot() for row in same_pending],
    )
    capture_missing = list(capture_contract["missing_fields"])

    if not policy["enabled"]:
        return _decision(
            action="new_position",
            permitted=True,
            reason="same_symbol_lifecycle_v4_disabled_by_config",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_config_disabled"},
        )

    candidate_capture_missing = [
        field for field in capture_missing if field.startswith("candidate.")
    ]
    if policy["durable_candidate_capture_required"] and candidate_capture_missing:
        return _decision(
            action="source_required_fail_closed",
            permitted=False,
            reason="same_symbol_candidate_durable_lifecycle_capture_missing",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness={
                **source_completeness,
                "durable_capture_status": capture_contract["status"],
                "durable_capture_missing_fields": candidate_capture_missing,
                "durable_capture_hash_sha256": capture_contract["capture_hash_sha256"],
            },
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_capture_gap"},
            vetoes=[
                {
                    "veto": "durable_candidate_lifecycle_capture_missing",
                    "missing_fields": candidate_capture_missing,
                }
            ],
        )

    ticket_capture_missing = [
        field for field in capture_missing if field.startswith("open_position_snapshot[")
    ]
    if same_positions and policy["durable_ticket_capture_required"] and ticket_capture_missing:
        return _decision(
            action="source_required_fail_closed",
            permitted=False,
            reason="same_symbol_ticket_durable_lifecycle_capture_missing",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness={
                **source_completeness,
                "durable_capture_status": capture_contract["status"],
                "durable_capture_missing_fields": ticket_capture_missing,
                "durable_capture_hash_sha256": capture_contract["capture_hash_sha256"],
            },
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_capture_gap"},
            vetoes=[
                {
                    "veto": "durable_ticket_lifecycle_capture_missing",
                    "missing_fields": ticket_capture_missing,
                }
            ],
        )

    pending_capture_missing = [
        field for field in capture_missing if field.startswith("pending_order_snapshot[")
    ]
    if same_pending and policy["source_unavailable_policy"] == "fail_closed" and pending_capture_missing:
        return _decision(
            action="source_required_fail_closed",
            permitted=False,
            reason="same_symbol_pending_durable_lifecycle_capture_missing",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness={
                **source_completeness,
                "durable_capture_status": capture_contract["status"],
                "durable_capture_missing_fields": pending_capture_missing,
                "durable_capture_hash_sha256": capture_contract["capture_hash_sha256"],
            },
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_capture_gap"},
            vetoes=[
                {
                    "veto": "durable_pending_lifecycle_capture_missing",
                    "missing_fields": pending_capture_missing,
                }
            ],
        )

    if pending_source_errors and policy["source_unavailable_policy"] == "fail_closed":
        return _decision(
            action="source_required_fail_closed",
            permitted=False,
            reason="same_symbol_pending_source_unavailable_for_v4_lifecycle_guard",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_source_unavailable"},
            vetoes=[
                {
                    "veto": "pending_source_unavailable",
                    "details": pending_source_errors,
                }
            ],
        )

    if candidate.side not in {"LONG", "SHORT"}:
        return _decision(
            action="source_required_fail_closed",
            permitted=False,
            reason="same_symbol_candidate_side_missing_for_v4_lifecycle_guard",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_missing_side"},
            vetoes=[{"veto": "candidate_side_missing"}],
        )

    if same_pending:
        return _pending_conflict_decision(
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
        )

    if not same_positions:
        return _decision(
            action="new_position",
            permitted=True,
            reason="no_same_symbol_open_or_pending_exposure",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={
                "status": "passed_no_existing_same_symbol_risk",
                "candidate_risk_pct": candidate.risk_pct,
            },
        )

    if len(same_positions) > policy["max_open_same_symbol_tickets"]:
        return _decision(
            action="source_required_fail_closed",
            permitted=False,
            reason="same_symbol_multi_ticket_state_requires_explicit_v4_reconciliation",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_ambiguous_multi_ticket"},
            vetoes=[
                {
                    "veto": "ambiguous_multi_ticket_same_symbol_state",
                    "ticket_count": len(same_positions),
                }
            ],
        )

    same_side = [row for row in same_positions if row.side == candidate.side]
    opposite_side = [row for row in same_positions if row.side != candidate.side]

    if same_side:
        return _same_direction_decision(
            candidate=candidate,
            parent=same_side[0],
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            policy=policy,
        )

    if opposite_side:
        return _opposite_direction_decision(
            candidate=candidate,
            target=opposite_side[0],
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
        )

    return _decision(
        action="source_required_fail_closed",
        permitted=False,
        reason="same_symbol_position_side_unresolved_for_v4_lifecycle_guard",
        candidate=candidate,
        same_positions=same_positions,
        same_pending=same_pending,
        source_completeness=source_completeness,
        freshness=freshness,
        broker_local_risk_result={"status": "not_checked_position_side_unresolved"},
        vetoes=[{"veto": "position_side_unresolved"}],
    )


def _pending_conflict_decision(
    *,
    candidate: CandidateLifecycleContext,
    same_positions: list[TicketLifecycleSnapshot],
    same_pending: list[PendingLifecycleSnapshot],
    source_completeness: dict[str, Any],
    freshness: dict[str, Any],
) -> SameSymbolLifecycleDecision:
    action = candidate.requested_action
    same_poi_pending = [
        row
        for row in same_pending
        if candidate.poi_id and row.poi_id == candidate.poi_id
    ]
    candidate_poi_lifecycle_state = str(
        candidate.causal_poi_lifecycle.get("poi_lifecycle_state") or ""
    ).strip()
    if (
        same_poi_pending
        and candidate_poi_lifecycle_state in {"filled", "invalidated", "invalid"}
    ):
        return _decision(
            action="cancel_pending",
            permitted=False,
            reason="terminal_poi_requires_pending_cancel_by_stable_poi_id",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={
                "status": "terminal_poi_pending_cancel_required",
                "poi_id": candidate.poi_id,
                "poi_lifecycle_state": candidate_poi_lifecycle_state,
                "matching_pending_ids": [
                    row.pending_id for row in same_poi_pending
                ],
                "matching_pending_lifecycle_hashes": [
                    row.causal_poi_lifecycle_hash_sha256
                    for row in same_poi_pending
                ],
            },
            rejected_alternatives=[
                {
                    "action": "new_position",
                    "reason": "terminal_poi_cannot_open_or_replace_new_risk",
                }
            ],
        )
    if action in PENDING_REPLACE_ACTIONS:
        selected = "replace_pending" if action == "replace_pending" else "cancel_pending"
        return _decision(
            action=selected,
            permitted=False,
            reason="same_symbol_pending_lifecycle_action_requires_pending_manager_before_order",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={
                "status": "pending_risk_reserved_requires_manager",
                "pending_risk_pct": _sum_known_risk(row.risk_pct for row in same_pending),
                "same_poi_pending_count": len(same_poi_pending),
            },
            rejected_alternatives=[
                {
                    "action": "new_position",
                    "reason": "same_symbol_pending_risk_already_reserved",
                }
            ],
        )
    same_side_pending = [row for row in same_pending if row.side == candidate.side]
    opposite_side_pending = [
        row
        for row in same_pending
        if row.side in {"LONG", "SHORT"} and row.side != candidate.side
    ]
    unresolved_side_pending = [
        row for row in same_pending if row.side not in {"LONG", "SHORT"}
    ]
    if opposite_side_pending and not same_side_pending and not unresolved_side_pending:
        return _decision(
            action="replace_pending",
            permitted=False,
            reason="same_symbol_opposite_pending_requires_pending_manager_before_order",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={
                "status": "opposite_pending_risk_reserved_requires_replacement",
                "pending_risk_pct": _sum_known_risk(row.risk_pct for row in same_pending),
                "opposite_pending_count": len(opposite_side_pending),
            },
            rejected_alternatives=[
                {
                    "action": "new_position",
                    "reason": "same_symbol_opposite_pending_requires_replacement_first",
                }
            ],
        )
    return _decision(
        action="no_trade_duplicate",
        permitted=False,
        reason=(
            "same_poi_pending_reuse_blocks_duplicate_candidate_instance"
            if same_poi_pending
            else "same_symbol_pending_conflict_blocks_new_or_scale_order"
        ),
        candidate=candidate,
        same_positions=same_positions,
        same_pending=same_pending,
        source_completeness=source_completeness,
        freshness=freshness,
        broker_local_risk_result={
            "status": "pending_risk_reserved_blocks_duplicate",
            "pending_risk_pct": _sum_known_risk(row.risk_pct for row in same_pending),
            "same_poi_pending_count": len(same_poi_pending),
        },
        vetoes=[
            {
                "veto": "pending_same_symbol_exposure_exists",
                "pending_count": len(same_pending),
                "same_poi_pending_count": len(same_poi_pending),
                "candidate_poi_id": candidate.poi_id,
                "pending_poi_ids": [
                    row.poi_id for row in same_pending if row.poi_id
                ],
            }
        ],
    )


def _same_direction_decision(
    *,
    candidate: CandidateLifecycleContext,
    parent: TicketLifecycleSnapshot,
    same_positions: list[TicketLifecycleSnapshot],
    same_pending: list[PendingLifecycleSnapshot],
    source_completeness: dict[str, Any],
    freshness: dict[str, Any],
    policy: dict[str, Any],
) -> SameSymbolLifecycleDecision:
    action = candidate.requested_action
    if action not in SCALE_ACTIONS:
        return _decision(
            action="no_trade_duplicate",
            permitted=False,
            reason="same_symbol_same_direction_requires_explicit_scale_in_action",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_no_scale_request"},
            rejected_alternatives=[
                {
                    "action": "same_direction_scale_in",
                    "reason": "explicit_scale_in_action_missing",
                }
            ],
        )
    if not policy["scale_in_enabled"]:
        return _decision(
            action="no_trade_duplicate",
            permitted=False,
            reason="same_symbol_scale_in_disabled_by_config",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result={"status": "not_checked_scale_disabled"},
        )

    vetoes: list[dict[str, Any]] = []
    if policy["scale_in_requires_same_thesis"]:
        if not candidate.thesis_id or not parent.thesis_id:
            vetoes.append(
                {
                    "veto": "scale_in_thesis_source_missing",
                    "candidate_thesis_id": candidate.thesis_id,
                    "parent_thesis_id": parent.thesis_id,
                }
            )
        elif candidate.thesis_id != parent.thesis_id:
            vetoes.append(
                {
                    "veto": "scale_in_thesis_mismatch",
                    "candidate_thesis_id": candidate.thesis_id,
                    "parent_thesis_id": parent.thesis_id,
                }
            )

    if parent.stale_thesis or parent.lifecycle_phase in {"close_only", "reduce_only"}:
        vetoes.append(
            {
                "veto": "existing_ticket_not_scale_eligible",
                "lifecycle_phase": parent.lifecycle_phase,
                "stale_thesis": parent.stale_thesis,
            }
        )

    existing_risk = parent.risk_pct
    candidate_risk = candidate.risk_pct
    total_risk = None
    if existing_risk is None or candidate_risk is None:
        vetoes.append(
            {
                "veto": "broker_local_risk_source_missing",
                "existing_risk_pct": existing_risk,
                "candidate_risk_pct": candidate_risk,
            }
        )
    else:
        total_risk = existing_risk + candidate_risk
        if total_risk > policy["max_same_symbol_risk_pct"]:
            vetoes.append(
                {
                    "veto": "same_symbol_risk_headroom_exceeded",
                    "existing_risk_pct": existing_risk,
                    "candidate_risk_pct": candidate_risk,
                    "total_risk_pct": total_risk,
                    "max_same_symbol_risk_pct": policy["max_same_symbol_risk_pct"],
                }
            )

    probability_delta = None
    if candidate.probability is None or parent.probability_at_entry is None:
        vetoes.append(
            {
                "veto": "scale_in_probability_source_missing",
                "candidate_probability": candidate.probability,
                "parent_probability_at_entry": parent.probability_at_entry,
            }
        )
    else:
        probability_delta = candidate.probability - parent.probability_at_entry
        if probability_delta < policy["scale_in_min_probability_delta"]:
            vetoes.append(
                {
                    "veto": "scale_in_probability_improvement_too_small",
                    "probability_delta": probability_delta,
                    "minimum_delta": policy["scale_in_min_probability_delta"],
                }
            )

    ev_delta = None
    if candidate.ev_r is None or parent.ev_r_at_entry is None:
        vetoes.append(
            {
                "veto": "scale_in_ev_source_missing",
                "candidate_ev_r": candidate.ev_r,
                "parent_ev_r_at_entry": parent.ev_r_at_entry,
            }
        )
    else:
        ev_delta = candidate.ev_r - parent.ev_r_at_entry
        if ev_delta < policy["scale_in_min_ev_delta_r"]:
            vetoes.append(
                {
                    "veto": "scale_in_ev_improvement_too_small",
                    "ev_delta_r": ev_delta,
                    "minimum_delta_r": policy["scale_in_min_ev_delta_r"],
                }
            )

    risk_result = {
        "status": "passed" if not vetoes else "failed",
        "existing_risk_pct": existing_risk,
        "candidate_risk_pct": candidate_risk,
        "total_risk_pct": total_risk,
        "max_same_symbol_risk_pct": policy["max_same_symbol_risk_pct"],
        "probability_delta": probability_delta,
        "ev_delta_r": ev_delta,
    }
    if vetoes:
        return _decision(
            action="source_required_fail_closed"
            if any("source_missing" in str(v["veto"]) for v in vetoes)
            else "no_trade_duplicate",
            permitted=False,
            reason="same_symbol_scale_in_v4_requirements_not_met",
            candidate=candidate,
            same_positions=same_positions,
            same_pending=same_pending,
            source_completeness=source_completeness,
            freshness=freshness,
            broker_local_risk_result=risk_result,
            vetoes=vetoes,
            parent_ticket=parent.ticket,
            parent_thesis_id=parent.thesis_id,
            scale_in_risk_delta_pct=candidate.risk_pct,
        )
    return _decision(
        action="same_direction_scale_in",
        permitted=True,
        reason="same_symbol_scale_in_ticket_bound_risk_safe_and_thesis_improving",
        candidate=candidate,
        same_positions=same_positions,
        same_pending=same_pending,
        source_completeness=source_completeness,
        freshness=freshness,
        broker_local_risk_result=risk_result,
        parent_ticket=parent.ticket,
        parent_thesis_id=parent.thesis_id,
        scale_in_risk_delta_pct=candidate.risk_pct,
    )


def _opposite_direction_decision(
    *,
    candidate: CandidateLifecycleContext,
    target: TicketLifecycleSnapshot,
    same_positions: list[TicketLifecycleSnapshot],
    same_pending: list[PendingLifecycleSnapshot],
    source_completeness: dict[str, Any],
    freshness: dict[str, Any],
) -> SameSymbolLifecycleDecision:
    action = candidate.requested_action
    if action in REVERSE_ACTIONS:
        selected_action = "close_and_reverse"
    elif action in CLOSE_ACTIONS:
        selected_action = "close_existing"
    elif action in REDUCE_ACTIONS:
        selected_action = "reduce_existing"
    else:
        selected_action = "no_trade_hedge_conflict"
    permitted = False
    reason = (
        "same_symbol_opposite_direction_requires_close_reduce_or_reverse_selection"
        if selected_action == "no_trade_hedge_conflict"
        else "same_symbol_close_reduce_reverse_requires_execution_manager_before_new_order"
    )
    return _decision(
        action=selected_action,
        permitted=permitted,
        reason=reason,
        candidate=candidate,
        same_positions=same_positions,
        same_pending=same_pending,
        source_completeness=source_completeness,
        freshness=freshness,
        broker_local_risk_result={
            "status": "opposite_direction_existing_risk_must_be_resolved_first",
            "existing_ticket": target.ticket,
            "existing_side": target.side,
            "candidate_side": candidate.side,
        },
        close_ticket=target.ticket if selected_action != "no_trade_hedge_conflict" else None,
        reverse_intent_id=(
            candidate.candidate_id if selected_action == "close_and_reverse" else None
        ),
        vetoes=[
            {
                "veto": "ambiguous_hedge_exposure_prevented",
                "existing_ticket": target.ticket,
                "existing_side": target.side,
                "candidate_side": candidate.side,
            }
        ]
        if selected_action == "no_trade_hedge_conflict"
        else [],
        rejected_alternatives=[
            {
                "action": "new_position",
                "reason": "opposite_direction_open_ticket_must_close_or_reduce_first",
            }
        ],
    )


def _sum_known_risk(values: Any) -> float | None:
    total = 0.0
    seen = False
    for value in values:
        if value is None:
            continue
        total += float(value)
        seen = True
    return total if seen else None


def _decision(
    *,
    action: str,
    permitted: bool,
    reason: str,
    candidate: CandidateLifecycleContext,
    same_positions: list[TicketLifecycleSnapshot],
    same_pending: list[PendingLifecycleSnapshot],
    source_completeness: dict[str, Any],
    freshness: dict[str, Any],
    broker_local_risk_result: dict[str, Any],
    vetoes: list[dict[str, Any]] | None = None,
    rejected_alternatives: list[dict[str, Any]] | None = None,
    parent_ticket: int | None = None,
    parent_thesis_id: str | None = None,
    close_ticket: int | None = None,
    reverse_intent_id: str | None = None,
    scale_in_risk_delta_pct: float | None = None,
) -> SameSymbolLifecycleDecision:
    selected_tickets: list[int | None] = []
    if parent_ticket is not None:
        selected_tickets.append(parent_ticket)
    if close_ticket is not None and close_ticket not in selected_tickets:
        selected_tickets.append(close_ticket)
    return SameSymbolLifecycleDecision(
        action=action,
        permitted_order_intent=permitted,
        reason=reason,
        selected_tickets=selected_tickets,
        parent_ticket=parent_ticket,
        parent_thesis_id=parent_thesis_id,
        close_ticket=close_ticket,
        reverse_intent_id=reverse_intent_id,
        scale_in_risk_delta_pct=scale_in_risk_delta_pct,
        rejected_alternatives=list(rejected_alternatives or []),
        vetoes=list(vetoes or []),
        source_completeness=source_completeness,
        evidence_class=EVIDENCE_CLASS,
        freshness=freshness,
        broker_local_risk_result=broker_local_risk_result,
        candidate=candidate,
        open_positions=same_positions,
        pending_orders=same_pending,
    )
