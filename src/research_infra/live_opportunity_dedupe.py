"""Lifecycle grouping for live shadow candidate opportunities.

Raw shadow rows intentionally preserve every candidate detection. This helper
adds a separate opportunity layer so reports can count the trade opportunity
once while the same setup is being re-detected on consecutive candles.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

PIP_SIZE_BY_SYMBOL = {
    "XAUUSD": 0.01,
    "XAGUSD": 0.001,
    "US30": 1.0,
    "US30_CASH": 1.0,
    "US30.CASH": 1.0,
    "NAS100": 1.0,
    "NAS100_CASH": 1.0,
    "USDJPY": 0.01,
    "GBPJPY": 0.01,
    "EURJPY": 0.01,
    "GBPUSD": 0.0001,
    "EURUSD": 0.0001,
    "NZDUSD": 0.0001,
}

OPPORTUNITY_ALGORITHM_VERSION = "active_setup_lifecycle_tolerance_v1"
FORMAL_LIFECYCLE_STATES = {
    "NEW_COUNTABLE",
    "DUPLICATE_ACTIVE_SETUP",
    "BLOCKED_SAME_SYMBOL_OVERLAP",
    "REOPENED_AFTER_TERMINAL",
    "NEW_AFTER_COOLDOWN",
}


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _canonical_price(value: Any) -> str:
    price = _safe_float(value)
    if price is None:
        return "missing"
    return f"{price:.8f}".rstrip("0").rstrip(".")


def _canonical_symbol(symbol: Any) -> str:
    return str(symbol or "").upper().replace(".CASH", "_CASH")


def _symbol_family(candidate: dict[str, Any]) -> str:
    symbol = _canonical_symbol(candidate.get("symbol") or candidate.get("broker_symbol"))
    if symbol == "US30_CASH":
        return "US30"
    if symbol == "NAS100_CASH":
        return "NAS100"
    return symbol


def candidate_geometry(candidate: dict[str, Any]) -> dict[str, float | None]:
    params = candidate.get("trade_parameters") or {}
    entry = _safe_float(params.get("entry_price"))
    stop = _safe_float(params.get("stop_loss"))
    tp1 = _safe_float(params.get("take_profit_1"))
    risk = abs(entry - stop) if entry is not None and stop is not None else None
    return {"entry": entry, "stop_loss": stop, "take_profit_1": tp1, "risk_price": risk}


def duplicate_price_tolerance(candidate: dict[str, Any]) -> float:
    """Return a conservative same-setup tolerance in price units.

    The floor is two pips in the instrument convention. A tiny risk-relative
    allowance catches prompt/buffer jitter without merging materially different
    levels.
    """
    symbol = _symbol_family(candidate)
    pip = PIP_SIZE_BY_SYMBOL.get(symbol, 0.0001)
    risk = candidate_geometry(candidate).get("risk_price")
    risk_component = 0.02 * risk if risk and risk > 0 else 0.0
    return max(2.0 * pip, risk_component)


def _hash_id(schema: str, *parts: Any) -> str:
    payload = "|".join(str(part) for part in (schema, *parts))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def candidate_level_key(candidate: dict[str, Any]) -> str:
    """Stable key for same symbol/side/framework/entry-level comparisons."""
    params = candidate.get("trade_parameters") or {}
    symbol = _symbol_family(candidate)
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    framework = str(candidate.get("framework") or "").lower()
    entry = _canonical_price(params.get("entry_price"))
    return f"{symbol}|{side}|{framework}|entry={entry}"


def candidate_setup_signature(candidate: dict[str, Any]) -> str:
    """More conservative duplicate signature including risk geometry."""
    params = candidate.get("trade_parameters") or {}
    return "|".join(
        (
            candidate_level_key(candidate),
            f"sl={_canonical_price(params.get('stop_loss'))}",
            f"tp1={_canonical_price(params.get('take_profit_1'))}",
        )
    )


def candidate_lifecycle_signature(candidate: dict[str, Any]) -> str:
    """Formal opportunity contract signature used by audit/reporting lanes.

    The assignment algorithm intentionally remains active-setup based. This
    richer signature records the session/POI context so future reports can see
    whether a cluster crossed a contextual boundary without changing live
    counting behavior.
    """
    params = candidate.get("trade_parameters") or {}
    h1_setup = candidate.get("h1_setup") if isinstance(candidate.get("h1_setup"), dict) else {}
    symbol = _symbol_family(candidate)
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    framework = str(candidate.get("framework") or "").lower()
    session = str(candidate.get("session") or candidate.get("kill_zone") or "session_missing").lower()
    poi_type = str(h1_setup.get("poi_type") or "poi_missing").lower()
    return "|".join(
        (
            symbol,
            f"session={session}",
            f"side={side}",
            f"framework={framework}",
            f"poi={poi_type}",
            f"entry={_canonical_price(params.get('entry_price'))}",
            f"sl={_canonical_price(params.get('stop_loss'))}",
            f"tp1={_canonical_price(params.get('take_profit_1'))}",
        )
    )


def same_level_tolerance_band(candidate: dict[str, Any]) -> dict[str, Any]:
    symbol = _symbol_family(candidate)
    pip_size = PIP_SIZE_BY_SYMBOL.get(symbol, 0.0001)
    tolerance = duplicate_price_tolerance(candidate)
    risk = candidate_geometry(candidate).get("risk_price")
    return {
        "symbol_family": symbol,
        "pip_size": pip_size,
        "same_level_tolerance_price_units": tolerance,
        "same_level_tolerance_pips": round(tolerance / pip_size, 6) if pip_size else None,
        "risk_price": risk,
        "policy": "max(2 pips, 2pct_of_entry_risk)",
    }


def candidate_compare_key(candidate: dict[str, Any]) -> str:
    params = candidate.get("trade_parameters") or {}
    symbol = _symbol_family(candidate)
    side = str(candidate.get("side") or params.get("direction") or "").upper()
    framework = str(candidate.get("framework") or "").lower()
    return f"{symbol}|{side}|{framework}"


def geometry_similarity(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    ga = candidate_geometry(a)
    gb = candidate_geometry(b)
    tolerance = max(duplicate_price_tolerance(a), duplicate_price_tolerance(b))
    risk_a = ga.get("risk_price")
    risk_b = gb.get("risk_price")
    max_risk = max((value for value in (risk_a, risk_b) if value is not None), default=None)
    exit_tolerance = max(tolerance * 3.0, 0.10 * max_risk) if max_risk else tolerance * 3.0
    def delta(left: float | None, right: float | None) -> float | None:
        if left is None or right is None:
            return None
        return round(abs(float(left) - float(right)), 8)

    deltas = {
        "entry_delta": delta(ga.get("entry"), gb.get("entry")),
        "stop_loss_delta": delta(ga.get("stop_loss"), gb.get("stop_loss")),
        "take_profit_1_delta": delta(ga.get("take_profit_1"), gb.get("take_profit_1")),
    }
    entry_similar = deltas["entry_delta"] is not None and deltas["entry_delta"] <= tolerance
    exits_similar = all(
        value is not None and value <= exit_tolerance
        for value in (deltas["stop_loss_delta"], deltas["take_profit_1_delta"])
    )
    return {
        "materially_same_setup": candidate_compare_key(a) == candidate_compare_key(b)
        and entry_similar
        and exits_similar,
        "duplicate_price_tolerance": tolerance,
        "exit_price_tolerance": exit_tolerance,
        **deltas,
        "comparison_key": candidate_compare_key(a),
        "candidate_comparison_key": candidate_compare_key(b),
    }


def terminal_event_summary(
    path_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return reset evidence for a candidate's latest observed path.

    Only an entry touch followed by TP/SL from lower-timeframe ordering is reset
    eligible. A no-entry TP-area move is a missed move, not proof that a new
    trade opportunity should be counted.
    """
    path_row = path_row or {}
    ltf_row = ltf_row or {}
    entry_ts = parse_utc(ltf_row.get("entry_first_touch_utc"))
    tp_ts = parse_utc(ltf_row.get("tp1_first_touch_utc"))
    sl_ts = parse_utc(ltf_row.get("sl_first_touch_utc"))
    ltf_terminal_status = str(ltf_row.get("terminal_outcome_status") or "")
    ltf_terminal_ts = parse_utc(ltf_row.get("terminal_event_utc"))

    event_ts: datetime | None = None
    status = "NO_TERMINAL_EVENT"
    reset_eligible = False
    if ltf_terminal_status in {"ENTRY_THEN_TP1", "ENTRY_THEN_SL"}:
        reset_eligible = True
        status = "ENTRY_THEN_TP1_BEFORE_SL" if ltf_terminal_status == "ENTRY_THEN_TP1" else "ENTRY_THEN_SL_BEFORE_TP1"
        event_ts = ltf_terminal_ts
    elif ltf_terminal_status in {
        "ENTRY_THEN_TP1_SL_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_TP1_SAME_M1_AMBIGUOUS",
        "ENTRY_THEN_SL_SAME_M1_AMBIGUOUS",
    }:
        status = ltf_terminal_status
        event_ts = ltf_terminal_ts
    elif ltf_terminal_status == "ENTRY_TOUCHED_UNRESOLVED_BY_LTF_ASOF":
        status = "ENTRY_TOUCHED_NOT_TERMINAL"
    elif ltf_terminal_status == "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH":
        status = "NO_ENTRY_TP_AREA_REACHED_NO_TRADE_NO_RESET"
        event_ts = ltf_terminal_ts
    elif ltf_terminal_status == "NO_ENTRY_SL_AREA_REACHED_WITHOUT_ENTRY_TOUCH":
        status = "NO_ENTRY_SL_AREA_REACHED_NO_TRADE_NO_RESET"
        event_ts = ltf_terminal_ts
    elif entry_ts and (tp_ts or sl_ts):
        tp_after_entry = tp_ts if tp_ts and tp_ts >= entry_ts else None
        sl_after_entry = sl_ts if sl_ts and sl_ts >= entry_ts else None
        if tp_after_entry or sl_after_entry:
            reset_eligible = True
            if tp_after_entry and sl_after_entry:
                if tp_after_entry == sl_after_entry:
                    status = "ENTRY_TP1_SL_SAME_M1_AMBIGUOUS"
                    reset_eligible = False
                    event_ts = tp_after_entry
                elif tp_after_entry < sl_after_entry:
                    status = "ENTRY_THEN_TP1_BEFORE_SL"
                    event_ts = tp_after_entry
                else:
                    status = "ENTRY_THEN_SL_BEFORE_TP1"
                    event_ts = sl_after_entry
            elif tp_after_entry:
                status = "ENTRY_THEN_TP1"
                event_ts = tp_after_entry
            elif sl_after_entry:
                status = "ENTRY_THEN_SL"
                event_ts = sl_after_entry
        else:
            status = "ENTRY_TOUCHED_NOT_TERMINAL"
    elif entry_ts:
        status = "ENTRY_TOUCHED_NOT_TERMINAL"
    elif path_row.get("touched_entry") is True and (path_row.get("hit_tp1") is True or path_row.get("hit_sl") is True):
        status = "PATH_TERMINAL_BUT_LTF_TERMINAL_TIME_MISSING_NO_RESET"
    elif path_row.get("touched_entry") is True:
        status = "ENTRY_TOUCHED_NOT_TERMINAL"
    elif path_row.get("touched_entry") is False and path_row.get("hit_tp1") is True:
        status = "NO_ENTRY_TP_AREA_REACHED_NO_TRADE_NO_RESET"
    elif path_row.get("touched_entry") is False and path_row.get("hit_sl") is True:
        status = "NO_ENTRY_SL_AREA_REACHED_NO_TRADE_NO_RESET"

    return {
        "terminal_event_status": status,
        "terminal_event_utc": event_ts.isoformat() if event_ts else None,
        "entry_first_touch_utc": entry_ts.isoformat() if entry_ts else None,
        "tp1_first_touch_utc": tp_ts.isoformat() if tp_ts else None,
        "sl_first_touch_utc": sl_ts.isoformat() if sl_ts else None,
        "reset_eligible": reset_eligible,
        "_entry_dt": entry_ts,
        "_terminal_event_dt": event_ts,
    }


def _sort_key(candidate: dict[str, Any]) -> tuple[datetime, str]:
    ts = parse_utc(candidate.get("decision_time_utc")) or datetime.min.replace(tzinfo=timezone.utc)
    return ts, str(candidate.get("candidate_id") or "")


def classify_lifecycle_state(opportunity_assignment: dict[str, Any]) -> str:
    counting_status = str(opportunity_assignment.get("opportunity_counting_status") or "")
    duplicate_status = str(opportunity_assignment.get("opportunity_duplicate_status") or "")
    reset_reason = str(opportunity_assignment.get("opportunity_reset_reason") or "")
    sequence_for_setup = int(opportunity_assignment.get("opportunity_sequence_for_setup") or 0)

    if counting_status == "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE" or duplicate_status == "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP":
        return "DUPLICATE_ACTIVE_SETUP"
    if counting_status == "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP":
        return "BLOCKED_SAME_SYMBOL_OVERLAP"
    if reset_reason == "PRIOR_SIMILAR_OPPORTUNITY_TERMINATED_BEFORE_THIS_DECISION":
        return "REOPENED_AFTER_TERMINAL"
    if counting_status == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY" and sequence_for_setup > 0:
        return "NEW_AFTER_COOLDOWN"
    if counting_status == "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY":
        return "NEW_COUNTABLE"
    return "UNKNOWN_LIFECYCLE_STATE"


def build_opportunity_index(
    candidates: list[dict[str, Any]],
    *,
    latest_paths: dict[str, dict[str, Any]] | None = None,
    latest_ltf: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Group consecutive same-setup detections into countable opportunities."""
    latest_paths = latest_paths or {}
    latest_ltf = latest_ltf or {}
    clusters: dict[str, dict[str, Any]] = {}
    candidate_cluster: dict[str, str] = {}
    candidate_similarity: dict[str, dict[str, Any]] = {}
    active_clusters: list[dict[str, Any]] = []

    for candidate in sorted(candidates, key=_sort_key):
        cid = str(candidate.get("candidate_id") or "")
        if not cid:
            continue
        signature = candidate_setup_signature(candidate)
        level_key = candidate_level_key(candidate)
        decision_ts = parse_utc(candidate.get("decision_time_utc"))
        active = None
        similarity: dict[str, Any] | None = None
        for cluster in active_clusters:
            terminal_dt = cluster.get("_terminal_event_dt")
            if terminal_dt is not None and decision_ts is not None and terminal_dt < decision_ts:
                continue
            compare = geometry_similarity(cluster["representative_candidate"], candidate)
            if compare["materially_same_setup"]:
                active = cluster
                similarity = compare
                break
        starts_new = active is None
        reset_reason = "FIRST_DETECTION_OF_SETUP_SIGNATURE"
        if active is not None:
            reset_reason = "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP"

        if starts_new:
            similar_prior_count = sum(
                1
                for cluster in clusters.values()
                if candidate_compare_key(cluster["representative_candidate"]) == candidate_compare_key(candidate)
            )
            opportunity_id = _hash_id("live_candidate_opportunity", candidate_compare_key(candidate), cid, similar_prior_count)
            active = {
                "opportunity_id": opportunity_id,
                "opportunity_setup_signature": signature,
                "candidate_level_key": level_key,
                "opportunity_compare_key": candidate_compare_key(candidate),
                "opportunity_first_candidate_id": cid,
                "candidate_ids": [],
                "reset_reason": reset_reason,
                "opportunity_sequence_for_setup": similar_prior_count,
                "_entry_dt": None,
                "_terminal_event_dt": None,
                "opportunity_entry_first_touch_utc": None,
                "opportunity_terminal_event_status": "NO_TERMINAL_EVENT",
                "opportunity_terminal_event_utc": None,
                "representative_candidate": candidate,
                "same_symbol_overlap_status": "NO_ACTIVE_SYMBOL_OVERLAP",
                "overlapping_active_symbol_opportunity_ids": [],
            }
            if decision_ts is not None:
                overlaps = []
                symbol = _symbol_family(candidate)
                for cluster in clusters.values():
                    if cluster["opportunity_id"] == opportunity_id:
                        continue
                    if _symbol_family(cluster["representative_candidate"]) != symbol:
                        continue
                    entry_dt = cluster.get("_entry_dt")
                    terminal_dt = cluster.get("_terminal_event_dt")
                    if entry_dt is not None and entry_dt <= decision_ts and (
                        terminal_dt is None or terminal_dt >= decision_ts
                    ):
                        overlaps.append(cluster["opportunity_id"])
                if overlaps:
                    active["same_symbol_overlap_status"] = "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE"
                    active["overlapping_active_symbol_opportunity_ids"] = overlaps
            clusters[opportunity_id] = active
            active_clusters.append(active)
            similarity = geometry_similarity(candidate, candidate)
            if any(
                geometry_similarity(cluster["representative_candidate"], candidate)["materially_same_setup"]
                for cluster in clusters.values()
                if cluster["opportunity_id"] != opportunity_id
            ):
                reset_reason = "PRIOR_SIMILAR_OPPORTUNITY_TERMINATED_BEFORE_THIS_DECISION"
                active["reset_reason"] = reset_reason

        candidate_cluster[cid] = active["opportunity_id"]
        candidate_similarity[cid] = similarity or geometry_similarity(active["representative_candidate"], candidate)
        active["candidate_ids"].append(cid)

        terminal = terminal_event_summary(latest_paths.get(cid), latest_ltf.get(cid))
        entry_dt = terminal.get("_entry_dt")
        if entry_dt is not None:
            current_entry = active.get("_entry_dt")
            if current_entry is None or entry_dt < current_entry:
                active["_entry_dt"] = entry_dt
                active["opportunity_entry_first_touch_utc"] = terminal["entry_first_touch_utc"]
        terminal_dt = terminal.get("_terminal_event_dt")
        if terminal.get("reset_eligible") and terminal_dt is not None:
            current_terminal = active.get("_terminal_event_dt")
            if current_terminal is None or terminal_dt < current_terminal:
                active["_terminal_event_dt"] = terminal_dt
                active["opportunity_terminal_event_status"] = terminal["terminal_event_status"]
                active["opportunity_terminal_event_utc"] = terminal["terminal_event_utc"]

    index: dict[str, dict[str, Any]] = {}
    for cid, opportunity_id in candidate_cluster.items():
        cluster = clusters[opportunity_id]
        sequence_index = cluster["candidate_ids"].index(cid)
        if sequence_index != 0:
            counting_status = "DUPLICATE_ACTIVE_SETUP_NOT_COUNTABLE"
        elif cluster["same_symbol_overlap_status"] == "OVERLAPS_ACTIVE_SAME_SYMBOL_TRADE":
            counting_status = "BLOCKED_ACTIVE_SAME_SYMBOL_TRADE_OVERLAP"
        else:
            counting_status = "COUNTABLE_PRIMARY_UNIQUE_OPPORTUNITY"
        index[cid] = {
            "opportunity_id": opportunity_id,
            "opportunity_setup_signature": cluster["opportunity_setup_signature"],
            "opportunity_lifecycle_signature": candidate_lifecycle_signature(cluster["representative_candidate"]),
            "candidate_level_key": cluster["candidate_level_key"],
            "opportunity_compare_key": cluster["opportunity_compare_key"],
            "opportunity_first_candidate_id": cluster["opportunity_first_candidate_id"],
            "opportunity_sequence_index": sequence_index,
            "opportunity_candidate_count": len(cluster["candidate_ids"]),
            "opportunity_duplicate_status": (
                "PRIMARY_UNIQUE_OPPORTUNITY"
                if sequence_index == 0
                else "CONSECUTIVE_DUPLICATE_ACTIVE_SETUP"
            ),
            "opportunity_sequence_for_setup": cluster["opportunity_sequence_for_setup"],
            "opportunity_reset_reason": cluster["reset_reason"],
            "opportunity_counting_status": counting_status,
            "same_symbol_overlap_status": cluster["same_symbol_overlap_status"],
            "overlapping_active_symbol_opportunity_ids": cluster["overlapping_active_symbol_opportunity_ids"],
            "opportunity_entry_first_touch_utc": cluster["opportunity_entry_first_touch_utc"],
            "opportunity_terminal_event_status": cluster["opportunity_terminal_event_status"],
            "opportunity_terminal_event_utc": cluster["opportunity_terminal_event_utc"],
            "opportunity_similarity": candidate_similarity.get(cid, {}),
            "same_level_tolerance_band": same_level_tolerance_band(cluster["representative_candidate"]),
            "instrument_concurrency_guidance": (
                "Opportunity counts are per symbol/side/framework active setup. A live account cannot "
                "assume multiple simultaneous same-instrument fills from consecutive duplicate rows; "
                "count duplicate-status rows as supporting path evidence, not separate trades."
            ),
            "opportunity_assignment_algorithm_version": OPPORTUNITY_ALGORITHM_VERSION,
            "opportunity_reset_policy": (
                "same symbol/side/framework detections with materially similar entry, SL, and TP1 "
                "share one opportunity until lower-timeframe evidence shows entry followed by TP/SL "
                "before a later decision"
            ),
        }
        index[cid]["opportunity_lifecycle_state"] = classify_lifecycle_state(index[cid])
    return index
