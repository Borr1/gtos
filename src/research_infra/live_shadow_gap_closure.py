"""Close live-shadow capture gaps with append-only recovery rows.

This module consumes already-written live shadow rows plus optional read-only
MT5 market data. It does not call AI, canary, Databento, or order APIs, and it
never rewrites existing JSONL evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.components.gtos_vnext_event_fields import enrich_cp281_event_contract_fields
from src.research_infra.forward_capture import (
    PROMOTION_VERDICT,
    SIERRA_SOURCE_STATUS_BY_SYMBOL,
    STRUCTURAL_SOURCE_CAPTURE_FIELDS,
    append_jsonl,
)
from src.research_infra.databento_live_shadow import REGISTERED_SYMBOL_SCHEMAS
from src.research_infra.live_mechanical_shadow import (
    FVG_REQUIRED_IDS,
    STRUCTURAL_LOCK_REQUIRED_IDS,
    entry_reference_metrics,
    path_outcome_status,
)
from src.research_infra.live_opportunity_dedupe import (
    OPPORTUNITY_ALGORITHM_VERSION,
    build_opportunity_index,
    terminal_event_summary,
)
from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate
from src.components.mt5_daemon_runtime import detect_broker_offset_seconds

ROOT = Path(".")

LOG_PATHS = {
    "candidates": Path("shadow_logs/strategy_follow_candidates.jsonl"),
    "paths": Path("shadow_logs/candidate_path_follow.jsonl"),
    "mechanical": Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl"),
    "pending": Path("shadow_logs/pending_limit_lifecycle.jsonl"),
    "v2b": Path("shadow_logs/v2b_forward_pairs.jsonl"),
    "prefill": Path("shadow_logs/prefill_delivery_path.jsonl"),
    "fvg_ob": Path("shadow_logs/fvg_ob_confluence.jsonl"),
    "pending_join": Path("shadow_logs/pending_limit_lifecycle_join_backfill.jsonl"),
    "structural": Path("shadow_logs/live_structural_strategy_metadata.jsonl"),
    "v2b_resolution": Path("shadow_logs/v2b_forward_pair_resolutions.jsonl"),
    "prefill_resolution": Path("shadow_logs/prefill_delivery_path_resolutions.jsonl"),
    "fvg_ob_resolution": Path("shadow_logs/fvg_ob_confluence_resolutions.jsonl"),
    "missed": Path("shadow_logs/missed_opportunity_shadow.jsonl"),
    "ltf": Path("shadow_logs/candidate_ltf_path_order.jsonl"),
    "databento_trigger": Path("shadow_logs/databento_live_trigger_decisions.jsonl"),
    "sierra_status": Path("shadow_logs/sierra_confluence_source_status.jsonl"),
    "rollup": Path("shadow_logs/live_candidate_strategy_rollups.jsonl"),
    "opportunity": Path("shadow_logs/live_candidate_opportunity_clusters.jsonl"),
    "account_truth": Path("shadow_logs/account_truth_reconciliation_status.jsonl"),
    "proxy_blocker": Path("shadow_logs/proxy_blocker_status.jsonl"),
    "ml_status": Path("shadow_logs/ml_shadow_status.jsonl"),
    "external_blocker": Path("shadow_logs/external_source_blocker_status.jsonl"),
}

SESSION_VOLATILITY_CSV = Path("shadow_logs/session_volatility_log.csv")
SWEEP_DIVERGENCE_CSV = Path("shadow_logs/sweep_divergence_log.csv")

NO_CALL_FLAGS = {
    "ai_calls": 0,
    "canary_calls": 0,
    "order_calls": 0,
    "databento_calls": 0,
    "paid_data_calls": 0,
    "no_ai_calls": True,
    "no_canary_required": True,
    "no_execution": True,
    "paid_fetch_attempted": False,
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    except Exception:
        return None


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def m1_bar_snapshot(bar: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(bar, dict):
        return None
    return {
        "time_utc": bar.get("time_utc"),
        "open": safe_float(bar.get("open")),
        "high": safe_float(bar.get("high")),
        "low": safe_float(bar.get("low")),
        "close": safe_float(bar.get("close")),
        "spread": safe_float(bar.get("spread")),
        "tick_volume": safe_float(bar.get("tick_volume")),
        "real_volume": safe_float(bar.get("real_volume")),
    }


def m1_bars_sha256(bars: list[dict[str, Any]]) -> str | None:
    if not bars:
        return None
    payload = []
    for bar in bars:
        snapshot = m1_bar_snapshot(bar)
        if snapshot is not None:
            payload.append(snapshot)
    if not payload:
        return None
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def m1_spread_summary(bars: list[dict[str, Any]]) -> dict[str, Any]:
    spreads = [value for bar in bars if (value := safe_float(bar.get("spread"))) is not None]
    if not spreads:
        return {
            "spread_available": False,
            "spread_count": 0,
            "spread_min": None,
            "spread_max": None,
            "spread_mean": None,
        }
    return {
        "spread_available": True,
        "spread_count": len(spreads),
        "spread_min": min(spreads),
        "spread_max": max(spreads),
        "spread_mean": sum(spreads) / len(spreads),
    }


def rate_has_field(item: Any, field: str) -> bool:
    if isinstance(item, dict):
        return field in item
    dtype = getattr(item, "dtype", None)
    return field in (getattr(dtype, "names", None) or ())


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                item = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append(item)
    return rows


def row_key(schema: str, *parts: Any) -> str:
    payload = "|".join(str(part) for part in (schema, *parts))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def status_bucket_utc(minutes: int = 15) -> str:
    """Return an append-only status heartbeat bucket for control ledgers."""
    now = parse_utc(utc_now_iso()) or datetime.now(timezone.utc)
    bucket_minute = (now.minute // minutes) * minutes
    bucket = now.replace(minute=bucket_minute, second=0, microsecond=0)
    return bucket.isoformat()


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for row in read_jsonl(path) if row.get("row_key")}


def append_once(path: Path, row: dict[str, Any]) -> bool:
    key = row.get("row_key")
    if key and str(key) in existing_row_keys(path):
        return False
    append_jsonl(path, row)
    return True


def base_row(
    *,
    schema: str,
    key_parts: tuple[Any, ...],
    candidate: dict[str, Any] | None = None,
    evidence_class: str = "RECOVERY_AUDIT",
    asof_latest_candle_utc: str | None = None,
) -> dict[str, Any]:
    candidate = candidate or {}
    now = utc_now_iso()
    row = {
        "schema_version": schema,
        "row_key": row_key(schema, *key_parts),
        "created_at_utc": now,
        "backfilled_at_utc": now,
        "promotion_verdict": PROMOTION_VERDICT,
        "evidence_class": evidence_class,
        "candidate_id": candidate.get("candidate_id"),
        "trade_id": candidate.get("trade_id"),
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "route_session": (
            candidate.get("route_session")
            or candidate.get("session")
            or candidate.get("session_tag")
            or candidate.get("kill_zone")
        ),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "asof_latest_candle_utc": asof_latest_candle_utc,
        "side": candidate.get("side") or ((candidate.get("trade_parameters") or {}).get("direction")),
        "framework": candidate.get("framework"),
        "no_leak_status": "POST_DECISION_RECOVERY_ROW_NOT_DECISION_FEATURE",
        **NO_CALL_FLAGS,
    }
    return enrich_cp281_event_contract_fields(row)


def latest_path_by_candidate(paths: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in paths:
        cid = str(row.get("candidate_id") or "")
        if not cid:
            continue
        current_ts = parse_utc(row.get("asof_latest_candle_utc"))
        previous_ts = parse_utc(out.get(cid, {}).get("asof_latest_candle_utc"))
        if previous_ts is None or (current_ts is not None and current_ts >= previous_ts):
            out[cid] = row
    return out


def latest_mechanical_by_candidate_strategy(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (str(row.get("candidate_id") or ""), str(row.get("strategy_id") or ""))
        if not key[0] or not key[1]:
            continue
        current_ts = parse_utc(row.get("asof_latest_candle_utc"))
        previous_ts = parse_utc(out.get(key, {}).get("asof_latest_candle_utc"))
        if previous_ts is None or (current_ts is not None and current_ts >= previous_ts):
            out[key] = row
    return out


def latest_ltf_by_candidate(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def prices_match(a: Any, b: Any, *, tolerance: float = 1e-6) -> bool:
    left = safe_float(a)
    right = safe_float(b)
    if left is None or right is None:
        return False
    return abs(left - right) <= tolerance


def match_lifecycle_to_candidate(
    lifecycle: dict[str, Any],
    candidates: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    if lifecycle.get("candidate_id"):
        match = next(
            (row for row in candidates if row.get("candidate_id") == lifecycle.get("candidate_id")),
            None,
        )
        return match, "MATCHED_EXISTING_CANDIDATE_ID" if match else "CANDIDATE_ID_PRESENT_BUT_ROW_MISSING"

    matches: list[dict[str, Any]] = []
    for candidate in candidates:
        params = candidate.get("trade_parameters") or {}
        if str(candidate.get("symbol") or "") != str(lifecycle.get("symbol") or ""):
            continue
        side = candidate.get("side") or params.get("direction")
        if str(side or "").upper() != str(lifecycle.get("side") or "").upper():
            continue
        if not prices_match(params.get("entry_price"), lifecycle.get("entry_price")):
            continue
        if not prices_match(params.get("stop_loss"), lifecycle.get("stop_loss")):
            continue
        if not prices_match(params.get("take_profit_1"), lifecycle.get("take_profit_1")):
            continue
        matches.append(candidate)
    if len(matches) == 1:
        return matches[0], "MATCHED_BY_SYMBOL_SIDE_PRICE_GEOMETRY"
    if not matches:
        return None, "NO_UNAMBIGUOUS_MATCH"
    return None, "AMBIGUOUS_MULTIPLE_MATCHES"


def build_pending_join_rows(
    candidates: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for lifecycle in lifecycle_rows:
        matched, status = match_lifecycle_to_candidate(lifecycle, candidates)
        legacy_row_key = row_key(
            "pending_limit_lifecycle_join_backfill_v1",
            lifecycle.get("trade_id"),
            lifecycle.get("timestamp_utc"),
            lifecycle.get("symbol"),
            lifecycle.get("intent_after_check"),
        )
        row = base_row(
            schema="pending_limit_lifecycle_join_backfill_v1",
            key_parts=(
                lifecycle.get("trade_id"),
                lifecycle.get("timestamp_utc"),
                lifecycle.get("symbol"),
                lifecycle.get("intent_after_check"),
                (matched or {}).get("candidate_id"),
                status,
            ),
            candidate=matched or lifecycle,
            evidence_class="INTERNAL_LIMIT_LIFECYCLE",
            asof_latest_candle_utc=lifecycle.get("checked_candle_time_utc"),
        )
        row.update(
            {
                "join_status": status,
                "join_key_version": "candidate_status_aware_v2",
                "legacy_row_key": legacy_row_key,
                "correction_note": (
                    "Row key includes matched candidate/status so a previous SOURCE_NOT_CAPTURED "
                    "join can be superseded append-only when later candidate rows make an exact "
                    "match possible."
                ),
                "source_lifecycle_trade_id": lifecycle.get("trade_id"),
                "source_lifecycle_timestamp_utc": lifecycle.get("timestamp_utc"),
                "candidate_id_backfilled": (matched or {}).get("candidate_id"),
                "decision_time_utc_backfilled": (matched or {}).get("decision_time_utc"),
                "symbol_price_disambiguation": {
                    "symbol": lifecycle.get("symbol"),
                    "side": lifecycle.get("side"),
                    "entry_price": lifecycle.get("entry_price"),
                    "stop_loss": lifecycle.get("stop_loss"),
                    "take_profit_1": lifecycle.get("take_profit_1"),
                },
                "manual_backfill_status": "RECOVERED_EXACT" if matched else "SOURCE_NOT_CAPTURED",
                "source_row": {
                    "candidate_id": lifecycle.get("candidate_id"),
                    "decision_time_utc": lifecycle.get("decision_time_utc"),
                    "trade_id": lifecycle.get("trade_id"),
                    "intent_after_check": lifecycle.get("intent_after_check"),
                    "fill_no_fill_label": lifecycle.get("fill_no_fill_label"),
                },
            }
        )
        rows.append(row)
    return rows


def _field_source_status(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("source_status") or value.get("status") or "CAPTURED")
    if value in (None, "", [], {}):
        return "SOURCE_NOT_CAPTURED"
    return "CAPTURED"


def _candidate_structural_fields(candidate: dict[str, Any]) -> dict[str, Any]:
    structural = candidate.get("decision_time_structural_fields")
    if not isinstance(structural, dict):
        return {}
    fields = structural.get("fields")
    return fields if isinstance(fields, dict) else {}


def _path_structural_fields(
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None,
) -> dict[str, Any]:
    path_row = path_row or {}
    ltf_row = ltf_row or {}
    params = candidate.get("trade_parameters") if isinstance(candidate.get("trade_parameters"), dict) else {}
    terminal = terminal_event_summary(path_row, ltf_row) if (path_row or ltf_row) else {}
    terminal_status = str(terminal.get("terminal_event_status") or "")
    terminal_utc = terminal.get("terminal_event_utc")
    event_price = None
    if terminal_utc:
        if "TP1" in terminal_status or "TP_AREA" in terminal_status:
            event_price = params.get("take_profit_1")
        elif "SL" in terminal_status:
            event_price = params.get("stop_loss")
        elif "ENTRY" in terminal_status:
            event_price = params.get("entry_price")
    if not path_row and not ltf_row:
        return {}
    return {
        "structural_lock_event_time_price": {
            "source_status": (
                "FORWARD_PATH_EVENT_CAPTURED"
                if terminal_utc
                else "FORWARD_PATH_EVENT_PENDING"
            ),
            "terminal_event_status": terminal_status or "NO_TERMINAL_EVENT",
            "event_time_utc": terminal_utc,
            "event_price": event_price,
            "latest_path_asof_utc": path_row.get("asof_latest_candle_utc"),
            "path_label": path_row.get("path_label"),
            "ltf_path_order_label": ltf_row.get("path_order_label"),
            "source": "candidate_path_follow+candidate_ltf_path_order",
        },
        "post_lock_reentry_state": {
            "source_status": "FORWARD_PATH_SOURCE_CAPTURED_REENTRY_NOT_EVALUATED",
            "entry_first_touch_utc": terminal.get("entry_first_touch_utc")
            or path_row.get("entry_first_touch_utc"),
            "tp1_first_touch_utc": terminal.get("tp1_first_touch_utc")
            or path_row.get("tp1_first_touch_utc"),
            "sl_first_touch_utc": terminal.get("sl_first_touch_utc")
            or path_row.get("sl_first_touch_utc"),
            "terminal_event_status": terminal_status or "NO_TERMINAL_EVENT",
            "reentry_algorithm_status": "NOT_EVALUATED_BY_LIVE_GAP_CLOSURE",
            "source": "candidate_path_follow+candidate_ltf_path_order",
        },
        "fvg_lock_state": {
            "source_status": "FORWARD_PATH_SOURCE_CAPTURED_LOCK_ALGORITHM_NOT_EVALUATED",
            "path_label": path_row.get("path_label"),
            "latest_path_asof_utc": path_row.get("asof_latest_candle_utc"),
            "terminal_event_status": terminal_status or "NO_TERMINAL_EVENT",
            "lock_algorithm_status": "NOT_EVALUATED_BY_LIVE_GAP_CLOSURE",
            "source": "candidate_path_follow+candidate_ltf_path_order",
        },
    }


def _structural_field_signature(fields: dict[str, Any]) -> str:
    try:
        payload = json.dumps(fields, sort_keys=True, default=str)
    except TypeError:
        payload = str(fields)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def build_structural_metadata_rows(
    candidates: list[dict[str, Any]],
    fvg_ob_rows: dict[str, dict[str, Any]],
    prefill_rows: dict[str, dict[str, Any]],
    path_rows: dict[str, dict[str, Any]] | None = None,
    ltf_rows: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    affected_ids = sorted(FVG_REQUIRED_IDS | STRUCTURAL_LOCK_REQUIRED_IDS)
    path_rows = path_rows or {}
    ltf_rows = ltf_rows or {}
    for candidate in candidates:
        cid = str(candidate.get("candidate_id") or "")
        fvg_ob = fvg_ob_rows.get(cid, {})
        prefill = prefill_rows.get(cid, {})
        path_row = path_rows.get(cid, {})
        ltf_row = ltf_rows.get(cid, {})
        h1_setup = candidate.get("h1_setup") or {}
        m15 = candidate.get("m15_confirmation") or {}
        frameworks = candidate.get("frameworks_evaluated") or {}
        decision_fields = fvg_ob.get("decision_time_fields") or {}
        recovered = {
            "h1_setup": h1_setup or {
                "recovery_status": "RECOVERED_EXACT_FROM_FVG_OB_OR_PREFILL"
                if decision_fields or prefill
                else "SOURCE_NOT_CAPTURED",
                "poi_type": decision_fields.get("h1_poi_type")
                or ((prefill.get("original_poi_bounds") or {}).get("poi_type")),
                "poi_price_level": decision_fields.get("h1_poi_price_level")
                or ((prefill.get("original_poi_bounds") or {}).get("poi_price_level")),
                "zone": (prefill.get("original_poi_bounds") or {}).get("zone"),
            },
            "m15_confirmation": m15 or {
                "recovery_status": "RECOVERED_EXACT_FROM_FVG_OB_OR_PREFILL"
                if decision_fields or prefill
                else "SOURCE_NOT_CAPTURED",
                "displacement_quality": decision_fields.get("m15_displacement_quality")
                or ((prefill.get("fvg_ob_swing_state_at_arm") or {}).get("m15_displacement_quality")),
            },
            "frameworks_evaluated": frameworks or {
                "recovery_status": "SOURCE_NOT_CAPTURED",
                "note": "Existing candidate rows did not preserve full frameworks_evaluated.",
            },
        }
        captured_fields = _candidate_structural_fields(candidate)
        candidate_structural = candidate.get("decision_time_structural_fields")
        decision_time_structural_capture_status = (
            candidate_structural.get("capture_status")
            if isinstance(candidate_structural, dict)
            else "LEGACY_CANDIDATE_ROW_WITHOUT_STRUCTURAL_SOURCE_CAPTURE"
        )
        path_fields = _path_structural_fields(candidate, path_row, ltf_row)
        structural_source_fields: dict[str, Any] = {}
        missing_exact: dict[str, str] = {}
        for field in STRUCTURAL_SOURCE_CAPTURE_FIELDS:
            value = path_fields.get(field) or captured_fields.get(field)
            status = _field_source_status(value)
            if status == "SOURCE_NOT_CAPTURED":
                missing_exact[field] = "SOURCE_NOT_CAPTURED"
            else:
                structural_source_fields[field] = value
        field_statuses = {
            field: _field_source_status(structural_source_fields.get(field))
            if field in structural_source_fields
            else "SOURCE_NOT_CAPTURED"
            for field in STRUCTURAL_SOURCE_CAPTURE_FIELDS
        }
        source_signature = _structural_field_signature(
            {
                "field_statuses": field_statuses,
                "path_asof": path_row.get("asof_latest_candle_utc"),
                "ltf_asof": ltf_row.get("asof_latest_candle_utc"),
                "decision_time_structural_capture_status": decision_time_structural_capture_status,
            }
        )
        row = base_row(
            schema="live_structural_strategy_metadata_v1",
            key_parts=(cid, source_signature),
            candidate=candidate,
        )
        row.update(
            {
                "source_dependency_signature": source_signature,
                "manual_backfill_status": (
                    "RECOVERED_AVAILABLE_FIELDS_WITH_EXPLICIT_SOURCE_GAPS"
                    if missing_exact
                    else "RECOVERED_AVAILABLE_STRUCTURAL_SOURCE_FIELDS"
                ),
                "recovered_decision_time_fields": recovered,
                "decision_time_structural_capture_status": decision_time_structural_capture_status,
                "captured_structural_source_fields": structural_source_fields,
                "structural_source_field_statuses": field_statuses,
                "missing_exact_required_fields": missing_exact,
                "affected_strategy_ids": affected_ids,
                "scoreability_status": (
                    "PARTIAL_METADATA_BACKFILLED_EXACT_SYSTEMS_STILL_REQUIRE_CAPTURED_SELECTOR_FIELDS"
                    if missing_exact
                    else "STRUCTURAL_SOURCE_FIELDS_CAPTURED_SCORERS_MAY_STILL_REQUIRE_IMPLEMENTATION"
                ),
                "latest_path_asof_utc": path_row.get("asof_latest_candle_utc"),
                "latest_ltf_asof_utc": ltf_row.get("asof_latest_candle_utc"),
                "source_rows_used": {
                    "strategy_follow_candidate": bool(candidate),
                    "prefill_delivery_path": bool(prefill),
                    "fvg_ob_confluence": bool(fvg_ob),
                    "candidate_path_follow": bool(path_row),
                    "candidate_ltf_path_order": bool(ltf_row),
                },
            }
        )
        rows.append(row)
    return rows


def build_resolution_row(
    schema: str,
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None,
    mechanical_rows: dict[tuple[str, str], dict[str, Any]],
    lane: str,
) -> dict[str, Any]:
    cid = str(candidate.get("candidate_id") or "")
    path_row = path_row or {}
    strategy_ids = {
        "v2b": ["V2B_OB_BOUNDARY_PROSPECTIVE", "LIVE_AI_J46_J49_BASELINE_COMPARATOR"],
        "prefill": ["PREFILL_DELIVERY_REVERSAL_PATH", "PENDING_LIMIT_LIFECYCLE"],
        "fvg_ob": ["FVG_OB_CONFLUENCE_OB_AFTER_FVG", "V2_STRUCT_FVG_MID_EDGE"],
    }[lane]
    mechanical_signature = "|".join(
        str((mechanical_rows.get((cid, sid)) or {}).get("created_at_utc") or "")
        for sid in strategy_ids
    )
    row = base_row(
        schema=schema,
        key_parts=(cid, path_row.get("asof_latest_candle_utc"), lane, mechanical_signature),
        candidate=candidate,
        evidence_class="FORWARD_SHADOW_PATH_FOLLOW",
        asof_latest_candle_utc=path_row.get("asof_latest_candle_utc"),
    )
    row.update(
        {
            "resolution_status": "RESOLVED_FROM_LIVE_PATH_ROW" if path_row else "WAITING_FOR_PATH_ROW",
            "mechanical_dependency_signature": mechanical_signature,
            "manual_backfill_status": "RECOVERED_DERIVED" if path_row else "SOURCE_NOT_CAPTURED",
            "path_label": path_row.get("path_label"),
            "path_outcome_status": path_outcome_status(path_row) if path_row else None,
            "touched_entry": path_row.get("touched_entry"),
            "hit_tp1": path_row.get("hit_tp1"),
            "hit_sl": path_row.get("hit_sl"),
            "bars_elapsed": path_row.get("bars_elapsed"),
            "path_metrics": entry_reference_metrics(path_row) if path_row else {},
            "strategy_outcomes": {
                sid: {
                    "strategy_status": (mechanical_rows.get((cid, sid)) or {}).get("strategy_status"),
                    "score_status": (mechanical_rows.get((cid, sid)) or {}).get("score_status"),
                    "outcome_status": (mechanical_rows.get((cid, sid)) or {}).get("outcome_status"),
                    "status_reason": (mechanical_rows.get((cid, sid)) or {}).get("status_reason"),
                }
                for sid in strategy_ids
            },
        }
    )
    return row


def pull_m1_bars(symbol: str, start: datetime, end: datetime) -> tuple[list[dict[str, Any]], str | None]:
    try:
        import MetaTrader5 as mt5  # type: ignore

        if not mt5.initialize():
            return [], "mt5_initialize_failed"
        try:
            broker_offset_seconds = detect_broker_offset_seconds(mt5, symbols=(symbol,))
            query_start = start + timedelta(seconds=broker_offset_seconds)
            query_end = end + timedelta(seconds=broker_offset_seconds)
            rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, query_start, query_end)
        finally:
            mt5.shutdown()
        if rates is None:
            return [], "mt5_no_rates"
        bars: list[dict[str, Any]] = []
        for item in rates:
            # MT5 raw bar epochs are broker-localized. The shadow rows are
            # UTC-keyed, so convert the returned epoch back to true UTC.
            ts = datetime.fromtimestamp(int(item["time"]) - broker_offset_seconds, tz=timezone.utc)
            bars.append(
                {
                    "time_utc": ts.isoformat(),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "spread": safe_float(item["spread"]) if rate_has_field(item, "spread") else None,
                    "tick_volume": safe_float(item["tick_volume"]) if rate_has_field(item, "tick_volume") else None,
                    "real_volume": safe_float(item["real_volume"]) if rate_has_field(item, "real_volume") else None,
                }
            )
        return bars, None
    except Exception as exc:  # noqa: BLE001
        return [], f"mt5_m1_read_failed:{type(exc).__name__}:{exc}"


def first_touch_times(
    *,
    side: str,
    entry: float | None,
    stop_loss: float | None,
    take_profit_1: float | None,
    bars: list[dict[str, Any]],
) -> dict[str, Any]:
    side = side.upper()
    touches = {
        "entry_first_touch_utc": None,
        "entry_first_touch_bar_ohlc": None,
        "tp1_first_touch_utc": None,
        "tp1_first_touch_bar_ohlc": None,
        "sl_first_touch_utc": None,
        "sl_first_touch_bar_ohlc": None,
        "same_m1_ambiguity": False,
        "terminal_event_utc": None,
        "terminal_event_bar_ohlc": None,
        "terminal_outcome_status": "NO_ENTRY_TOUCH_BY_LTF_ASOF",
        "terminal_event_r": None,
        "terminal_order_ambiguity": False,
    }
    entry_seen = False

    def set_terminal(status: str, bar_time: Any, r_value: float | None, *, ambiguous: bool = False) -> None:
        if touches["terminal_event_utc"] is not None:
            return
        touches["terminal_event_utc"] = bar_time
        touches["terminal_event_bar_ohlc"] = m1_bar_snapshot(bar)
        touches["terminal_outcome_status"] = status
        touches["terminal_event_r"] = r_value
        touches["terminal_order_ambiguity"] = ambiguous

    for bar in bars:
        high = safe_float(bar.get("high"))
        low = safe_float(bar.get("low"))
        if high is None or low is None:
            continue
        hit_entry = hit_tp = hit_sl = False
        if side == "LONG":
            hit_entry = entry is not None and low <= entry
            hit_tp = take_profit_1 is not None and high >= take_profit_1
            hit_sl = stop_loss is not None and low <= stop_loss
        elif side == "SHORT":
            hit_entry = entry is not None and high >= entry
            hit_tp = take_profit_1 is not None and low <= take_profit_1
            hit_sl = stop_loss is not None and high >= stop_loss
        if hit_entry and touches["entry_first_touch_utc"] is None:
            touches["entry_first_touch_utc"] = bar.get("time_utc")
            touches["entry_first_touch_bar_ohlc"] = m1_bar_snapshot(bar)
        if hit_tp and touches["tp1_first_touch_utc"] is None:
            touches["tp1_first_touch_utc"] = bar.get("time_utc")
            touches["tp1_first_touch_bar_ohlc"] = m1_bar_snapshot(bar)
        if hit_sl and touches["sl_first_touch_utc"] is None:
            touches["sl_first_touch_utc"] = bar.get("time_utc")
            touches["sl_first_touch_bar_ohlc"] = m1_bar_snapshot(bar)
        if sum(bool(x) for x in (hit_entry, hit_tp, hit_sl)) > 1:
            touches["same_m1_ambiguity"] = True
        if touches["terminal_event_utc"] is not None:
            continue
        if not entry_seen:
            if not hit_entry:
                continue
            entry_seen = True
            if hit_tp and hit_sl:
                set_terminal(
                    "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
                    bar.get("time_utc"),
                    None,
                    ambiguous=True,
                )
            elif hit_tp:
                set_terminal(
                    "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
                    bar.get("time_utc"),
                    None,
                    ambiguous=True,
                )
            elif hit_sl:
                set_terminal(
                    "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
                    bar.get("time_utc"),
                    None,
                    ambiguous=True,
                )
            continue
        if hit_tp and hit_sl:
            set_terminal(
                "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
                bar.get("time_utc"),
                None,
                ambiguous=True,
            )
        elif hit_tp:
            set_terminal("ENTRY_THEN_TP1", bar.get("time_utc"), 1.5)
        elif hit_sl:
            set_terminal("ENTRY_THEN_SL", bar.get("time_utc"), -1.0)
    if touches["terminal_event_utc"] is None:
        if touches["entry_first_touch_utc"]:
            touches["terminal_outcome_status"] = "ENTRY_TOUCHED_UNRESOLVED_BY_LTF_ASOF"
        elif touches["tp1_first_touch_utc"]:
            touches["terminal_outcome_status"] = "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH"
            touches["terminal_event_utc"] = touches["tp1_first_touch_utc"]
            touches["terminal_event_bar_ohlc"] = touches["tp1_first_touch_bar_ohlc"]
            touches["terminal_event_r"] = 0.0
        elif touches["sl_first_touch_utc"]:
            touches["terminal_outcome_status"] = "NO_ENTRY_SL_AREA_REACHED_WITHOUT_ENTRY_TOUCH"
            touches["terminal_event_utc"] = touches["sl_first_touch_utc"]
            touches["terminal_event_bar_ohlc"] = touches["sl_first_touch_bar_ohlc"]
            touches["terminal_event_r"] = 0.0
    return touches


def order_label(touches: dict[str, Any]) -> str:
    terminal_status = str(touches.get("terminal_outcome_status") or "")
    if terminal_status == "ENTRY_THEN_TP1":
        return "entry_then_tp1_before_sl"
    if terminal_status == "ENTRY_THEN_SL":
        return "entry_then_sl_before_tp1"
    if terminal_status == "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS":
        return "entry_tp1_sl_same_m1_ambiguous"
    if terminal_status == "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS":
        return "entry_tp1_same_m1_ambiguous"
    if terminal_status == "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS":
        return "entry_sl_same_m1_ambiguous"
    if terminal_status == "ENTRY_TOUCHED_UNRESOLVED_BY_LTF_ASOF":
        return "entry_touched_unresolved"
    if terminal_status == "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH":
        return "tp1_area_reached_without_entry_touch"
    if terminal_status == "NO_ENTRY_SL_AREA_REACHED_WITHOUT_ENTRY_TOUCH":
        return "sl_area_reached_without_entry_touch"
    entry = touches.get("entry_first_touch_utc")
    tp = touches.get("tp1_first_touch_utc")
    sl = touches.get("sl_first_touch_utc")
    if not entry and tp:
        return "tp1_area_reached_without_entry_touch"
    if not entry and sl:
        return "sl_area_reached_without_entry_touch"
    if not entry:
        return "no_entry_touch_by_ltf_asof"
    if tp and sl:
        if tp == sl:
            return "entry_tp1_sl_same_m1_ambiguous"
        return "entry_then_tp1_before_sl" if tp < sl else "entry_then_sl_before_tp1"
    if tp:
        return "entry_then_tp1"
    if sl:
        return "entry_then_sl"
    return "entry_touched_unresolved"


def build_ltf_row(
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None,
    *,
    max_hours: float,
    skip_mt5: bool,
) -> dict[str, Any]:
    decision = parse_utc(candidate.get("decision_time_utc"))
    now = datetime.now(timezone.utc)
    end = now
    if path_row and parse_utc(path_row.get("asof_latest_candle_utc")):
        end = parse_utc(path_row.get("asof_latest_candle_utc")) + timedelta(minutes=15)  # type: ignore[operator]
    bars: list[dict[str, Any]] = []
    error = None
    status = "SOURCE_BLOCKED"
    if skip_mt5:
        error = "mt5_read_skipped_by_flag"
    elif decision is None:
        error = "missing_decision_time"
    elif now - decision > timedelta(hours=max_hours):
        error = "outside_max_hours"
    else:
        bars, error = pull_m1_bars(str(candidate.get("broker_symbol") or candidate.get("symbol")), decision, end)
        status = "M1_PATH_RECOVERED" if bars else "SOURCE_BLOCKED"
    params = candidate.get("trade_parameters") or {}
    side = str(candidate.get("side") or params.get("direction") or "")
    touches = first_touch_times(
        side=side,
        entry=safe_float(params.get("entry_price")),
        stop_loss=safe_float(params.get("stop_loss")),
        take_profit_1=safe_float(params.get("take_profit_1")),
        bars=bars,
    )
    spread_summary = m1_spread_summary(bars)
    label = order_label(touches) if bars else "ltf_source_blocked"
    row = base_row(
        schema="candidate_ltf_path_order_v1",
        key_parts=(
            candidate.get("candidate_id"),
            (path_row or {}).get("asof_latest_candle_utc"),
            "M1",
            status,
            len(bars),
            label,
        ),
        candidate=candidate,
        evidence_class="FORWARD_SHADOW_PATH_FOLLOW",
        asof_latest_candle_utc=(path_row or {}).get("asof_latest_candle_utc"),
    )
    row.update(
        {
            "manual_backfill_status": "RECOVERED_DERIVED" if bars else "SOURCE_BLOCKED",
            "ltf_source": "MT5_M1",
            "ltf_status": status,
            "mt5_read_error": error,
            "m1_bar_count": len(bars),
            "m1_source_first_bar_utc": bars[0].get("time_utc") if bars else None,
            "m1_source_last_bar_utc": bars[-1].get("time_utc") if bars else None,
            "m1_source_sha256": m1_bars_sha256(bars),
            "m1_spread_source_status": "SPREAD_CAPTURED" if spread_summary["spread_available"] else "SPREAD_NOT_AVAILABLE",
            "m1_spread_count": spread_summary["spread_count"],
            "m1_spread_min": spread_summary["spread_min"],
            "m1_spread_max": spread_summary["spread_max"],
            "m1_spread_mean": spread_summary["spread_mean"],
            "window_start_utc": candidate.get("decision_time_utc"),
            "window_end_utc": end.isoformat() if isinstance(end, datetime) else None,
            **touches,
            "path_order_label": label,
        }
    )
    return row


def entry_retest_redesign_context(candidate: dict[str, Any], path_row: dict[str, Any] | None) -> dict[str, Any]:
    path_row = path_row or {}
    params = candidate.get("trade_parameters") or {}
    entry = safe_float(params.get("entry_price"))
    stop = safe_float(params.get("stop_loss"))
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    base_r = abs(entry - stop) if entry is not None and stop is not None else None
    nearest_distance_r = safe_float(path_row.get("nearest_distance_to_entry_r"))
    if nearest_distance_r is None:
        nearest_distance = safe_float(path_row.get("nearest_abs_distance_to_entry"))
        if nearest_distance is None:
            signed_distance = safe_float(path_row.get("nearest_distance_to_entry"))
            nearest_distance = abs(signed_distance) if signed_distance is not None else None
        if nearest_distance is None and entry is not None:
            min_low = safe_float(path_row.get("min_low"))
            max_high = safe_float(path_row.get("max_high"))
            if side == "LONG" and min_low is not None:
                nearest_distance = abs(min_low - entry)
            elif side == "SHORT" and max_high is not None:
                nearest_distance = abs(entry - max_high)
        nearest_distance_r = nearest_distance / base_r if nearest_distance is not None and base_r and base_r > 0 else None
    entry_touch_distance_status = str(path_row.get("entry_touch_distance_status") or "")
    if not entry_touch_distance_status:
        if path_row.get("touched_entry") is True:
            entry_touch_distance_status = "ENTRY_TOUCHED"
        elif nearest_distance_r is None:
            entry_touch_distance_status = "ENTRY_DISTANCE_UNKNOWN"
        elif nearest_distance_r <= 0.25:
            entry_touch_distance_status = "NEAR_MISS_LE_0_25R"
        else:
            entry_touch_distance_status = "FAR_MISS_GT_0_25R"
    path_status = path_outcome_status(path_row) if path_row else "WAITING_FOR_PATH_ROW"
    if path_status != "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH":
        redesign_bucket = "NOT_A_NO_FILL_TP1_ENTRY_REDESIGN_ROW"
    elif entry_touch_distance_status == "NEAR_MISS_LE_0_25R":
        redesign_bucket = "NEAR_MISS_ENTRY_OFFSET_CONTROL_QUEUE"
    elif entry_touch_distance_status == "FAR_MISS_GT_0_25R":
        redesign_bucket = "FAR_MISS_RETEST_REDESIGN_CONTROL_QUEUE"
    else:
        redesign_bucket = "ENTRY_DISTANCE_UNKNOWN_REPAIR_REQUIRED"
    return {
        "entry_touch_distance_status": entry_touch_distance_status,
        "nearest_distance_to_entry_r": nearest_distance_r,
        "entry_retest_redesign_bucket": redesign_bucket,
    }


def build_missed_opportunity_row(
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None,
) -> dict[str, Any]:
    path_row = path_row or {}
    redesign_context = entry_retest_redesign_context(candidate, path_row)
    params = candidate.get("trade_parameters") or {}
    entry = safe_float(params.get("entry_price"))
    stop = safe_float(params.get("stop_loss"))
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    base_r = abs(entry - stop) if entry is not None and stop is not None else None
    proximity_entry = None
    if base_r and entry is not None:
        proximity_entry = entry + 0.25 * base_r if side == "LONG" else entry - 0.25 * base_r
    path_status = path_outcome_status(path_row) if path_row else "WAITING_FOR_PATH_ROW"
    row = base_row(
        schema="missed_opportunity_shadow_v1",
        key_parts=(
            candidate.get("candidate_id"),
            path_row.get("asof_latest_candle_utc"),
            (ltf_row or {}).get("path_order_label"),
            (ltf_row or {}).get("ltf_status"),
            redesign_context["entry_touch_distance_status"],
            redesign_context["nearest_distance_to_entry_r"],
            redesign_context["entry_retest_redesign_bucket"],
        ),
        candidate=candidate,
        evidence_class="FORWARD_SHADOW_PATH_FOLLOW",
        asof_latest_candle_utc=path_row.get("asof_latest_candle_utc"),
    )
    row.update(
        {
            "manual_backfill_status": "RECOVERED_DERIVED" if path_row else "SOURCE_NOT_CAPTURED",
            "limit_entry_outcome_status": path_status,
            "limit_entry_path_label": path_row.get("path_label"),
            "market_at_decision_close_comparator": {
                "status": "OBSERVATION_ONLY_ORIGINAL_TP_SL_LEVELS",
                "tp1_area_reached": path_row.get("hit_tp1"),
                "sl_area_reached": path_row.get("hit_sl"),
                "note": "This comparator does not change execution; it records whether original TP/SL areas were reached without requiring the limit touch.",
            },
            "proximity_entry_comparator": {
                "status": "OBSERVATION_ONLY_025R_INSIDE_LIMIT",
                "proximity_entry_price": proximity_entry,
                "model": "entry moved 0.25R toward decision price; research-only near-miss comparator",
            },
            "near_miss_classification": (
                "LIMIT_NO_FILL_TP1_AREA_REACHED"
                if path_status == "NO_FILL_PRICE_REACHED_TP_AREA_WITHOUT_LIMIT_TOUCH"
                else "NOT_A_TP1_NEAR_MISS_BY_CURRENT_PATH"
            ),
            "entry_touch_distance_status": redesign_context["entry_touch_distance_status"],
            "nearest_distance_to_entry_r": redesign_context["nearest_distance_to_entry_r"],
            "entry_retest_redesign_bucket": redesign_context["entry_retest_redesign_bucket"],
            "ltf_path_order_label": (ltf_row or {}).get("path_order_label"),
        }
    )
    return row


def build_opportunity_cluster_row(
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None,
    opportunity: dict[str, Any] | None,
) -> dict[str, Any]:
    path_row = path_row or {}
    ltf_row = ltf_row or {}
    opportunity = opportunity or {}
    terminal = terminal_event_summary(path_row, ltf_row)
    redesign_context = entry_retest_redesign_context(candidate, path_row)
    row = base_row(
        schema="live_candidate_opportunity_cluster_v1",
        key_parts=(
            OPPORTUNITY_ALGORITHM_VERSION,
            candidate.get("candidate_id"),
            path_row.get("asof_latest_candle_utc"),
            opportunity.get("opportunity_id"),
            opportunity.get("opportunity_duplicate_status"),
            opportunity.get("opportunity_lifecycle_state"),
            opportunity.get("opportunity_candidate_count"),
            opportunity.get("opportunity_counting_status"),
            opportunity.get("same_symbol_overlap_status"),
            opportunity.get("opportunity_entry_first_touch_utc"),
            opportunity.get("opportunity_terminal_event_status"),
            redesign_context["entry_touch_distance_status"],
            redesign_context["nearest_distance_to_entry_r"],
            redesign_context["entry_retest_redesign_bucket"],
        ),
        candidate=candidate,
        evidence_class="FORWARD_SHADOW_PATH_FOLLOW",
        asof_latest_candle_utc=path_row.get("asof_latest_candle_utc"),
    )
    row.update(
        {
            "manual_backfill_status": "RECOVERED_DERIVED" if opportunity else "SOURCE_NOT_CAPTURED",
            "opportunity_assignment_algorithm_version": opportunity.get(
                "opportunity_assignment_algorithm_version"
            )
            or OPPORTUNITY_ALGORITHM_VERSION,
            "opportunity_id": opportunity.get("opportunity_id"),
            "opportunity_setup_signature": opportunity.get("opportunity_setup_signature"),
            "opportunity_lifecycle_signature": opportunity.get("opportunity_lifecycle_signature"),
            "opportunity_lifecycle_state": opportunity.get("opportunity_lifecycle_state"),
            "candidate_level_key": opportunity.get("candidate_level_key"),
            "opportunity_first_candidate_id": opportunity.get("opportunity_first_candidate_id"),
            "opportunity_sequence_index": opportunity.get("opportunity_sequence_index"),
            "opportunity_candidate_count": opportunity.get("opportunity_candidate_count"),
            "opportunity_duplicate_status": opportunity.get("opportunity_duplicate_status"),
            "opportunity_sequence_for_setup": opportunity.get("opportunity_sequence_for_setup"),
            "opportunity_reset_reason": opportunity.get("opportunity_reset_reason"),
            "opportunity_counting_status": opportunity.get("opportunity_counting_status"),
            "same_symbol_overlap_status": opportunity.get("same_symbol_overlap_status"),
            "overlapping_active_symbol_opportunity_ids": opportunity.get("overlapping_active_symbol_opportunity_ids"),
            "opportunity_entry_first_touch_utc": opportunity.get("opportunity_entry_first_touch_utc"),
            "opportunity_terminal_event_status": opportunity.get("opportunity_terminal_event_status"),
            "opportunity_terminal_event_utc": opportunity.get("opportunity_terminal_event_utc"),
            "opportunity_similarity": opportunity.get("opportunity_similarity"),
            "same_level_tolerance_band": opportunity.get("same_level_tolerance_band"),
            "instrument_concurrency_guidance": opportunity.get("instrument_concurrency_guidance"),
            "opportunity_reset_policy": opportunity.get("opportunity_reset_policy"),
            "opportunity_counting_guidance": (
                "Count only COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY rows for trade-opportunity comparisons; "
                "raw candidate/path/mechanical rows remain append-only evidence and may include consecutive "
                "duplicate detections or active same-symbol overlaps."
            ),
            "candidate_terminal_event": {
                key: value for key, value in terminal.items() if not key.startswith("_")
            },
            "candidate_path_label": path_row.get("path_label"),
            "candidate_path_status": path_outcome_status(path_row) if path_row else "WAITING_FOR_PATH_ROW",
            "entry_touch_distance_status": redesign_context["entry_touch_distance_status"],
            "nearest_distance_to_entry_r": redesign_context["nearest_distance_to_entry_r"],
            "entry_retest_redesign_bucket": redesign_context["entry_retest_redesign_bucket"],
            "ltf_path_order_label": ltf_row.get("path_order_label"),
            "same_setup_duplicate_rule": (
                "same symbol, side, framework, and materially similar entry/stop/TP1 with no prior LTF "
                "entry+TP/SL terminal before this decision is one active setup, not multiple successful candidates"
            ),
        }
    )
    return row


def databento_trigger_row(candidate: dict[str, Any]) -> dict[str, Any]:
    symbol = str(candidate.get("symbol") or "")
    confluence = ((candidate.get("external_confluence") or {}).get("databento") or {})
    trigger = confluence.get("trigger_policy") or {}
    status = trigger.get("trigger_status")
    if not status:
        if symbol in REGISTERED_SYMBOL_SCHEMAS:
            status = "TRIGGER_READY_OWNER_APPROVED_ENV_GATED"
        elif symbol == "GBPJPY":
            status = "SOURCE_BLOCKED_PROXY_MAPPING_REQUIRED"
        else:
            status = "NO_TRIGGER_FOR_SYMBOL_OR_STRATEGY"
    row = base_row(
        schema="databento_live_trigger_decision_v1",
        key_parts=(candidate.get("candidate_id"), status),
        candidate=candidate,
        evidence_class="FUTURES_PROXY_TRANSFER",
    )
    row.update(
        {
            "manual_backfill_status": "RECOVERED_EXACT",
            "trigger_status": status,
            "trigger_policy": {
                **trigger,
                "owner_approval_status": "OWNER_APPROVED_BY_CEO_2026-05-05_VALUE_MAX_FORWARD_COLLECTION",
                "registered_schemas": list(REGISTERED_SYMBOL_SCHEMAS.get(symbol, ())),
            },
            "decision": "FETCH_ALLOWED_BY_POLICY_WHEN_COLLECTOR_ENABLED_AND_COST_CAP_PASS"
            if symbol in REGISTERED_SYMBOL_SCHEMAS
            else "DO_NOT_FETCH_SOURCE_OR_STRATEGY_BLOCKED",
            "cost_policy": "OWNER_APPROVED_VALUE_MAX_COST_CAPPED_FORWARD_COLLECTION",
            "estimated_cost_usd": 0.0,
        }
    )
    return row


def sierra_source_status_row(candidate: dict[str, Any]) -> dict[str, Any]:
    symbol = str(candidate.get("symbol") or "")
    sierra = ((candidate.get("external_confluence") or {}).get("sierra") or {})
    status = SIERRA_SOURCE_STATUS_BY_SYMBOL.get(
        symbol,
        {
            "source_status": "NO_REGISTERED_SIERRA_PROXY_FOR_SYMBOL",
            "parity_status": "SOURCE_BLOCKED",
            "interpretation_status": "BLOCKED_NO_PROXY",
        },
    )
    row = base_row(
        schema="sierra_confluence_source_status_v1",
        key_parts=(candidate.get("candidate_id"), sierra.get("source_symbol"), status.get("parity_status")),
        candidate=candidate,
        evidence_class="FUTURES_PROXY_TRANSFER",
    )
    row.update(
        {
            "manual_backfill_status": "RECOVERED_EXACT",
            "sierra_status": sierra.get("status"),
            "sierra_source_symbol": sierra.get("source_symbol"),
            "sierra_futures_symbol": sierra.get("futures_symbol"),
            **status,
            "features_present": bool(sierra.get("features")),
        }
    )
    return row


def rollup_row(
    candidate: dict[str, Any],
    path_row: dict[str, Any] | None,
    mechanical_rows: dict[tuple[str, str], dict[str, Any]],
    ltf_row: dict[str, Any] | None,
    opportunity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = str(candidate.get("candidate_id") or "")
    strategy_rows = {
        sid: mechanical_rows.get((cid, sid))
        for sid in sorted({key[1] for key in mechanical_rows if key[0] == cid})
    }
    mechanical_signature = "|".join(
        str((strategy_rows.get(sid) or {}).get("created_at_utc") or "")
        for sid in sorted(strategy_rows)
    )
    redesign_context = entry_retest_redesign_context(candidate, path_row)
    unresolved = {
        sid: {
            "score_status": (row or {}).get("score_status"),
            "strategy_status": (row or {}).get("strategy_status"),
            "reason": (row or {}).get("status_reason"),
        }
        for sid, row in strategy_rows.items()
        if row and str(row.get("score_status") or "").startswith("MISSING")
    }
    row = base_row(
        schema="live_candidate_strategy_rollup_v1",
        key_parts=(
            OPPORTUNITY_ALGORITHM_VERSION,
            cid,
            (path_row or {}).get("asof_latest_candle_utc"),
            mechanical_signature,
            (ltf_row or {}).get("path_order_label"),
            (ltf_row or {}).get("ltf_status"),
            (opportunity or {}).get("opportunity_lifecycle_state"),
            (opportunity or {}).get("opportunity_candidate_count"),
            (opportunity or {}).get("opportunity_counting_status"),
            (opportunity or {}).get("same_symbol_overlap_status"),
            redesign_context["entry_touch_distance_status"],
            redesign_context["nearest_distance_to_entry_r"],
            redesign_context["entry_retest_redesign_bucket"],
        ),
        candidate=candidate,
        evidence_class="FORWARD_SHADOW_PATH_FOLLOW",
        asof_latest_candle_utc=(path_row or {}).get("asof_latest_candle_utc"),
    )
    row.update(
        {
            "manual_backfill_status": "RECOVERED_DERIVED" if path_row else "SOURCE_NOT_CAPTURED",
            "latest_follow_asof_utc": (path_row or {}).get("asof_latest_candle_utc"),
            "mechanical_dependency_signature": mechanical_signature,
            "candidate_path_label": (path_row or {}).get("path_label"),
            "candidate_path_status": path_outcome_status(path_row) if path_row else "WAITING_FOR_PATH_ROW",
            "entry_touch_distance_status": redesign_context["entry_touch_distance_status"],
            "nearest_distance_to_entry_r": redesign_context["nearest_distance_to_entry_r"],
            "entry_retest_redesign_bucket": redesign_context["entry_retest_redesign_bucket"],
            "ltf_path_order_label": (ltf_row or {}).get("path_order_label"),
            "opportunity_id": (opportunity or {}).get("opportunity_id"),
            "opportunity_lifecycle_signature": (opportunity or {}).get("opportunity_lifecycle_signature"),
            "opportunity_lifecycle_state": (opportunity or {}).get("opportunity_lifecycle_state"),
            "opportunity_assignment_algorithm_version": (opportunity or {}).get(
                "opportunity_assignment_algorithm_version"
            )
            or OPPORTUNITY_ALGORITHM_VERSION,
            "opportunity_first_candidate_id": (opportunity or {}).get("opportunity_first_candidate_id"),
            "opportunity_duplicate_status": (opportunity or {}).get("opportunity_duplicate_status"),
            "opportunity_sequence_index": (opportunity or {}).get("opportunity_sequence_index"),
            "opportunity_candidate_count": (opportunity or {}).get("opportunity_candidate_count"),
            "opportunity_reset_reason": (opportunity or {}).get("opportunity_reset_reason"),
            "opportunity_counting_status": (opportunity or {}).get("opportunity_counting_status"),
            "same_symbol_overlap_status": (opportunity or {}).get("same_symbol_overlap_status"),
            "overlapping_active_symbol_opportunity_ids": (opportunity or {}).get("overlapping_active_symbol_opportunity_ids"),
            "opportunity_entry_first_touch_utc": (opportunity or {}).get("opportunity_entry_first_touch_utc"),
            "opportunity_similarity": (opportunity or {}).get("opportunity_similarity"),
            "same_level_tolerance_band": (opportunity or {}).get("same_level_tolerance_band"),
            "instrument_concurrency_guidance": (opportunity or {}).get("instrument_concurrency_guidance"),
            "opportunity_counting_guidance": (
                "Use COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY rows for opportunity-level system comparisons; "
                "do not sum consecutive duplicates or active same-symbol overlaps as separate trades."
            ),
            "strategy_count": len(strategy_rows),
            "unresolved_strategy_count": len(unresolved),
            "unresolved_strategies": unresolved,
            "strategy_statuses": {
                sid: {
                    "score_status": (strategy_row or {}).get("score_status"),
                    "outcome_status": (strategy_row or {}).get("outcome_status"),
                    "strategy_status": (strategy_row or {}).get("strategy_status"),
                }
                for sid, strategy_row in strategy_rows.items()
            },
        }
    )
    return row


def account_truth_rows(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        row = base_row(
            schema="account_truth_reconciliation_status_v1",
            key_parts=(candidate.get("candidate_id"), "account_history_status"),
            candidate=candidate,
            evidence_class="BROKER_ACTUAL_R",
        )
        row.update(
            {
                "manual_backfill_status": "SOURCE_BLOCKED",
                "account_truth_status": "NO_REALIZED_ACCOUNT_HISTORY_FOR_CANDIDATE_OR_NOT_QUERIED_IN_CLOSURE",
                "truth_lane": "ACCOUNT_HISTORY_REQUIRED_FOR_DOLLAR_OR_ACTUAL_R_CLAIMS",
                "actual_r_claim_allowed": False,
                "note": "No account-history realized deal row is attached by this closure pass; candidate rollups must not use local shadow PnL as broker actual R.",
            }
        )
        rows.append(row)
    return rows


def refresh_ltf_rows(
    *,
    root: Path = ROOT,
    max_hours: float = 8.0,
    skip_mt5: bool = False,
) -> dict[str, Any]:
    paths = {name: root / path for name, path in LOG_PATHS.items()}
    candidates = read_jsonl(paths["candidates"])
    latest_paths = latest_path_by_candidate(read_jsonl(paths["paths"]))
    rows = [
        build_ltf_row(
            candidate,
            latest_paths.get(str(candidate.get("candidate_id") or "")),
            max_hours=max_hours,
            skip_mt5=skip_mt5,
        )
        for candidate in candidates
    ]
    written = 0
    for row in rows:
        if append_once(paths["ltf"], row):
            written += 1
    return {
        "schema_version": "candidate_ltf_path_order_refresh_summary_v1",
        "created_at_utc": utc_now_iso(),
        "candidates_seen": len(candidates),
        "rows_built": len(rows),
        "rows_written": written,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def static_blocker_rows(candidates: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    now_candidate = candidates[-1] if candidates else {}
    bucket = status_bucket_utc()
    proxy = base_row(
        schema="proxy_blocker_status_v1",
        key_parts=("GBPJPY", "direct_futures_proxy", bucket),
        candidate=now_candidate,
        evidence_class="FUTURES_PROXY_TRANSFER",
    )
    proxy.update(
        {
            "symbol": "GBPJPY",
            "blocker_status": "SOURCE_BLOCKED",
            "blocker": "NO_REGISTERED_DIRECT_SIERRA_OR_DATABENTO_PROXY",
            "required_before_use": "Validated 6B/6J or alternate two-book proxy design.",
            "status_bucket_utc": bucket,
            "status_cadence_minutes": 15,
        }
    )
    ml = base_row(
        schema="ml_shadow_status_v1",
        key_parts=("K55", "target_refresh_owner_approval", bucket),
        candidate=now_candidate,
        evidence_class="CONTROL_ONLY",
    )
    ml.update(
        {
            "blocker_status": "TARGET_REFRESH_REGISTERED_MODEL_ARTIFACT_PENDING",
            "model_family": "K55",
            "inference_enabled": False,
            "required_before_enable": (
                "K55 target and feature bundle are owner-approved/registered; production scoring remains "
                "disabled until a matching model artifact passes no-leak and schema tests."
            ),
            "status_bucket_utc": bucket,
            "status_cadence_minutes": 15,
        }
    )
    external_rows = []
    for family, blocker in {
        "ES_MES": "PRE_REGISTRATION_AND_SOURCE_CADENCE_REQUIRED",
        "CL": "PRE_REGISTRATION_AND_SOURCE_CADENCE_REQUIRED",
        "ZN": "PRE_REGISTRATION_AND_SOURCE_CADENCE_REQUIRED",
        "VIX_VXM": "SOURCE_AND_LABEL_STATUS_BLOCKED",
        "OPTIONS_GAMMA": "LEGAL_SOURCE_OR_FORWARD_PROXY_REQUIRED",
        "OLDER_DATA": "ALTERNATE_PROVIDER_OR_ARCHIVE_REQUIRED",
    }.items():
        row = base_row(
            schema="external_source_blocker_status_v1",
            key_parts=(family, blocker, bucket),
            candidate=now_candidate,
            evidence_class="CONTROL_ONLY",
        )
        row.update(
            {
                "source_family": family,
                "blocker_status": "SOURCE_OR_PRE_REGISTRATION_BLOCKED",
                "blocker": blocker,
                "live_capture_status": "NOT_ACTIVE_FOR_LIVE_CANDIDATE_DECISIONS",
                "status_bucket_utc": bucket,
                "status_cadence_minutes": 15,
            }
        )
        external_rows.append(row)
    return {"proxy": [proxy], "ml": [ml], "external": external_rows}


def append_csv_once(path: Path, row: dict[str, Any], fieldnames: list[str], key_fields: tuple[str, ...]) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    if path.exists() and path.stat().st_size > 0:
        with path.open("r", encoding="utf-8", newline="") as handle:
            for item in csv.DictReader(handle):
                existing.add(tuple(str(item.get(field) or "") for field in key_fields))
    key = tuple(str(row.get(field) or "") for field in key_fields)
    if key in existing:
        return False
    file_exists = path.exists() and path.stat().st_size > 0
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return True


def write_no_event_csv_rows(*, root: Path = ROOT, today: date | None = None) -> dict[str, int]:
    target = today or datetime.now(timezone.utc).date()
    written = {"session_volatility_log.csv": 0, "sweep_divergence_log.csv": 0}
    session_path = root / SESSION_VOLATILITY_CSV
    sweep_path = root / SWEEP_DIVERGENCE_CSV
    for instrument, session in (("XAUUSD", "london"), ("NAS100", "london"), ("XAGUSD", "london")):
        if append_csv_once(
            session_path,
            {
                "date": target.isoformat(),
                "instrument": instrument,
                "session": session,
                "w1_avg_range": "",
                "w2_avg_range": "",
                "w3_avg_range": "",
                "pattern": "NO_EVENT_IN_WINDOW_OR_MONITOR_NOT_TRIGGERED",
                "candle_count": 0,
            },
            [
                "date",
                "instrument",
                "session",
                "w1_avg_range",
                "w2_avg_range",
                "w3_avg_range",
                "pattern",
                "candle_count",
            ],
            ("date", "instrument", "session"),
        ):
            written["session_volatility_log.csv"] += 1
    for instrument, session in (("US30", "london"), ("XAUUSD", "london")):
        if append_csv_once(
            sweep_path,
            {
                "date": target.isoformat(),
                "instrument": instrument,
                "session": session,
                "sweep_direction": "NO_EVENT_IN_WINDOW",
                "sweep_extreme": "",
                "reference_level": "",
                "outcome": "NO_EVENT_IN_WINDOW_OR_MONITOR_NOT_TRIGGERED",
            },
            [
                "date",
                "instrument",
                "session",
                "sweep_direction",
                "sweep_extreme",
                "reference_level",
                "outcome",
            ],
            ("date", "instrument", "session", "sweep_direction"),
        ):
            written["sweep_divergence_log.csv"] += 1
    return written


def close_gaps(
    *,
    root: Path = ROOT,
    max_hours: float = 8.0,
    skip_mt5: bool = False,
    refresh_ltf: bool = True,
    candidate_ids: set[str] | None = None,
) -> dict[str, Any]:
    paths = {name: root / path for name, path in LOG_PATHS.items()}
    all_candidates = read_jsonl(paths["candidates"])
    candidates = all_candidates
    if candidate_ids:
        candidates = [
            candidate
            for candidate in all_candidates
            if str(candidate.get("candidate_id") or "") in candidate_ids
        ]
    path_rows = read_jsonl(paths["paths"])
    mechanical = read_jsonl(paths["mechanical"])
    pending = read_jsonl(paths["pending"])
    fvg_ob = {str(row.get("candidate_id") or ""): row for row in read_jsonl(paths["fvg_ob"])}
    prefill = {str(row.get("candidate_id") or ""): row for row in read_jsonl(paths["prefill"])}
    latest_paths = latest_path_by_candidate(path_rows)
    latest_mech = latest_mechanical_by_candidate_strategy(mechanical)

    written: dict[str, int] = {}

    def write_many(name: str, rows: list[dict[str, Any]]) -> None:
        count = 0
        for row in rows:
            if append_once(paths[name], row):
                count += 1
        written[str(paths[name].name)] = count

    write_many("pending_join", build_pending_join_rows(candidates, pending))
    write_many(
        "v2b_resolution",
        [
            build_resolution_row(
                "v2b_forward_pair_resolution_v1",
                candidate,
                latest_paths.get(str(candidate.get("candidate_id") or "")),
                latest_mech,
                "v2b",
            )
            for candidate in candidates
        ],
    )
    write_many(
        "prefill_resolution",
        [
            build_resolution_row(
                "prefill_delivery_path_resolution_v1",
                candidate,
                latest_paths.get(str(candidate.get("candidate_id") or "")),
                latest_mech,
                "prefill",
            )
            for candidate in candidates
        ],
    )
    write_many(
        "fvg_ob_resolution",
        [
            build_resolution_row(
                "fvg_ob_confluence_resolution_v1",
                candidate,
                latest_paths.get(str(candidate.get("candidate_id") or "")),
                latest_mech,
                "fvg_ob",
            )
            for candidate in candidates
        ],
    )

    if refresh_ltf:
        ltf_rows: list[dict[str, Any]] = []
        for candidate in candidates:
            cid = str(candidate.get("candidate_id") or "")
            ltf_rows.append(
                build_ltf_row(
                    candidate,
                    latest_paths.get(cid),
                    max_hours=max_hours,
                    skip_mt5=skip_mt5,
                )
            )
        write_many("ltf", ltf_rows)
    else:
        written[str(paths["ltf"].name)] = 0
    latest_ltf = latest_ltf_by_candidate(read_jsonl(paths["ltf"]))
    opportunity_index = build_opportunity_index(
        all_candidates,
        latest_paths=latest_paths,
        latest_ltf=latest_ltf,
    )
    write_many(
        "structural",
        build_structural_metadata_rows(candidates, fvg_ob, prefill, latest_paths, latest_ltf),
    )

    write_many(
        "missed",
        [
            build_missed_opportunity_row(
                candidate,
                latest_paths.get(str(candidate.get("candidate_id") or "")),
                latest_ltf.get(str(candidate.get("candidate_id") or "")),
            )
            for candidate in candidates
        ],
    )
    write_many(
        "opportunity",
        [
            build_opportunity_cluster_row(
                candidate,
                latest_paths.get(str(candidate.get("candidate_id") or "")),
                latest_ltf.get(str(candidate.get("candidate_id") or "")),
                opportunity_index.get(str(candidate.get("candidate_id") or "")),
            )
            for candidate in candidates
        ],
    )
    write_many("databento_trigger", [databento_trigger_row(candidate) for candidate in candidates])
    write_many("sierra_status", [sierra_source_status_row(candidate) for candidate in candidates])
    write_many(
        "rollup",
        [
            rollup_row(
                candidate,
                latest_paths.get(str(candidate.get("candidate_id") or "")),
                latest_mech,
                latest_ltf.get(str(candidate.get("candidate_id") or "")),
                opportunity_index.get(str(candidate.get("candidate_id") or "")),
            )
            for candidate in candidates
        ],
    )
    write_many("account_truth", account_truth_rows(candidates))
    blockers = static_blocker_rows(candidates)
    write_many("proxy_blocker", blockers["proxy"])
    write_many("ml_status", blockers["ml"])
    write_many("external_blocker", blockers["external"])
    written.update(write_no_event_csv_rows(root=root))

    return {
        "schema_version": "live_shadow_gap_closure_summary_v1",
        "created_at_utc": utc_now_iso(),
        "candidates_seen": len(candidates),
        "context_candidates_seen": len(all_candidates),
        "candidate_filter": sorted(candidate_ids) if candidate_ids else [],
        "path_rows_seen": len(path_rows),
        "mechanical_rows_seen": len(mechanical),
        "pending_lifecycle_rows_seen": len(pending),
        "rows_written": dict(sorted(written.items())),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
        "promotion_verdict": PROMOTION_VERDICT,
    }
