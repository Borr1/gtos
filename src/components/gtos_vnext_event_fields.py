"""Shared vNext event-contract enrichment.

The CP281 runtime registry expects event rows to carry a compact scope and
source-hash contract. Live/shadow producers call this helper before appending so
future rows are replayable without a separate adapter artifact.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from src.components.gtos_vnext_runtime import (
    normalize_vnext_symbol_key,
    resolve_vnext_symbol_family,
)

CP281_EVENT_CONTRACT_FIELDS = (
    "symbol",
    "source_symbol",
    "symbol_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_path_sha256",
    "source_file_sha256",
)

DEFAULT_CP281_HORIZON_ID = "live_candidate_decision"
DEFAULT_CP281_MARKET_TIMEFRAME = "M15"

CP281_SOURCE_PATH_BY_SCHEMA = {
    "strategy_follow_candidate_v1": "shadow_logs/strategy_follow_candidates.jsonl",
    "strategy_follow_evaluation_v1": "shadow_logs/strategy_follow_evaluations.jsonl",
    "live_mechanical_strategy_shadow_outcome_v1": (
        "shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"
    ),
    "live_candidate_strategy_rollup_v1": "shadow_logs/live_candidate_strategy_rollups.jsonl",
    "live_structural_strategy_metadata_v1": "shadow_logs/live_structural_strategy_metadata.jsonl",
    "candidate_features_log_v1": "shadow_logs/candidate_features_log.jsonl",
    "candidate_path_follow_v1": "shadow_logs/candidate_path_follow.jsonl",
    "candidate_ltf_path_order_v1": "shadow_logs/candidate_ltf_path_order.jsonl",
    "fvg_ob_confluence_forward_v1": "shadow_logs/fvg_ob_confluence.jsonl",
    "fvg_ob_confluence_audit_v2": "shadow_logs/fvg_ob_confluence_audit.jsonl",
    "scid_forward_source_capture_v1": "shadow_logs/scid_forward_source_capture.jsonl",
    "nofill_forward_source_capture_v1": "shadow_logs/nofill_forward_source_capture.jsonl",
}

CP281_SOURCE_COMPONENT_BY_SCHEMA = {
    "strategy_follow_candidate_v1": "primary_analyzer_live_candidate",
    "strategy_follow_evaluation_v1": "live_mso_forward_shadow",
    "live_mechanical_strategy_shadow_outcome_v1": "live_mechanical_strategy_shadow",
    "live_candidate_strategy_rollup_v1": "live_shadow_gap_closure_rollup",
    "live_structural_strategy_metadata_v1": "live_shadow_gap_closure_structural",
    "candidate_features_log_v1": "candidate_features_logger",
    "candidate_path_follow_v1": "candidate_path_follow",
    "candidate_ltf_path_order_v1": "candidate_ltf_path_order",
    "fvg_ob_confluence_forward_v1": "fvg_ob_confluence_forward_capture",
    "fvg_ob_confluence_audit_v2": "fvg_ob_confluence_audit",
    "scid_forward_source_capture_v1": "scid_forward_source_capture",
    "nofill_forward_source_capture_v1": "nofill_forward_source_capture",
}


def _json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode(
        "utf-8"
    )
    return hashlib.sha256(payload).hexdigest()


def _text_sha256(value: Any) -> str:
    return hashlib.sha256(str(value or "").replace("\\", "/").encode("utf-8")).hexdigest()


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _side_from(value: Any) -> str:
    normalized = str(value or "").strip().upper()
    if normalized in {"LONG", "BUY", "BULL", "BULLISH"}:
        return "LONG"
    if normalized in {"SHORT", "SELL", "BEAR", "BEARISH"}:
        return "SHORT"
    return normalized


def _path_text(source_path: str | Path | None, schema_version: Any) -> str:
    if source_path not in (None, ""):
        return str(source_path).replace("\\", "/")
    return CP281_SOURCE_PATH_BY_SCHEMA.get(str(schema_version or ""), "")


def _source_file_sha256(row: dict[str, Any], source_path_text: str) -> str:
    for field in ("source_file_sha256", "source_hash_sha256"):
        value = row.get(field)
        if isinstance(value, str) and len(value) == 64:
            return value.lower()
    source_hash = row.get("source_hash")
    if isinstance(source_hash, str) and len(source_hash) == 64:
        return source_hash.lower()
    return _json_sha256(
        {
            "source_path": source_path_text,
            "schema_version": row.get("schema_version"),
            "source_file": row.get("source_file"),
            "source_hash": source_hash,
            "candidate_id": row.get("candidate_id") or row.get("evaluation_id"),
            "decision_time_utc": row.get("decision_time_utc") or row.get("candle_close_utc"),
            "row_key": row.get("row_key"),
        }
    )


def enrich_cp281_event_contract_fields(
    row: dict[str, Any],
    *,
    source_path: str | Path | None = None,
    default_horizon_id: str = DEFAULT_CP281_HORIZON_ID,
    default_market_timeframe: str = DEFAULT_CP281_MARKET_TIMEFRAME,
    default_source_component: str | None = None,
) -> dict[str, Any]:
    """Fill the CP281 event-contract scope/hash fields in an event row.

    The function mutates and returns ``row``. It does not read or hash large
    append-only JSONL files; the source-file hash is a stable event/source
    identity hash unless a strict 64-character source hash is already present.
    """
    schema_version = row.get("schema_version")
    trade_params = _safe_dict(row.get("trade_parameters"))
    source_symbol = _first_present(
        row.get("source_symbol"),
        row.get("source_symbol_root"),
        row.get("symbol"),
        row.get("broker_symbol"),
        row.get("candidate_symbol"),
    )
    symbol = _first_present(row.get("symbol"), row.get("broker_symbol"), source_symbol)

    if source_symbol not in (None, "") and row.get("source_symbol") in (None, ""):
        row["source_symbol"] = str(source_symbol)
    if symbol not in (None, "") and row.get("symbol") in (None, ""):
        row["symbol"] = str(symbol)

    family = _first_present(
        row.get("symbol_family"),
        resolve_vnext_symbol_family(source_symbol),
        resolve_vnext_symbol_family(symbol),
        resolve_vnext_symbol_family(row.get("broker_symbol")),
    )
    if family:
        row["symbol_family"] = str(family)
    elif source_symbol:
        row["symbol_family"] = normalize_vnext_symbol_key(source_symbol)

    market_timeframe = _first_present(
        row.get("market_timeframe"),
        row.get("timeframe"),
        row.get("entry_timeframe"),
        row.get("source_timeframe"),
        "M1" if str(row.get("ltf_source") or "").upper().endswith("M1") else None,
        default_market_timeframe,
    )
    row["market_timeframe"] = str(market_timeframe)

    route_session = _first_present(
        row.get("route_session"),
        row.get("session"),
        row.get("session_tag"),
        row.get("kill_zone"),
        row.get("session_bucket"),
    )
    row["route_session"] = str(route_session or "unknown_session")

    side = _side_from(
        _first_present(
            row.get("side"),
            row.get("selected_side"),
            row.get("direction"),
            row.get("candidate_side"),
            row.get("ai_direction_evaluated"),
            row.get("daily_bias_direction"),
            row.get("pre_ai_gate_bias"),
            trade_params.get("direction"),
            row.get("deterministic_bias"),
        )
    )
    row["side"] = side or "UNKNOWN_SIDE"
    if "selected_side" in row and row.get("selected_side") in (None, ""):
        row["selected_side"] = row["side"]

    horizon_id = _first_present(row.get("horizon_id"), row.get("horizon"), default_horizon_id)
    row["horizon_id"] = str(horizon_id)

    source_path_text = (
        _path_text(source_path, schema_version)
        or str(row.get("source_file") or schema_version or "unknown_event_source")
    )
    row["source_path_sha256"] = row.get("source_path_sha256") or _text_sha256(
        source_path_text
    )
    row["source_file_sha256"] = _source_file_sha256(row, source_path_text)
    row.setdefault(
        "source_hash_contract",
        "CP281_EVENT_SOURCE_PATH_AND_EVENT_IDENTITY_SHA256_V1",
    )

    if row.get("source_component") in (None, ""):
        row["source_component"] = (
            default_source_component
            or CP281_SOURCE_COMPONENT_BY_SCHEMA.get(str(schema_version or ""))
        )
    return row


__all__ = [
    "CP281_EVENT_CONTRACT_FIELDS",
    "DEFAULT_CP281_HORIZON_ID",
    "DEFAULT_CP281_MARKET_TIMEFRAME",
    "enrich_cp281_event_contract_fields",
]
