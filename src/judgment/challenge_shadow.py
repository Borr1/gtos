"""Challenge-true shadow pack. Scores sit / closes / replay rows. Never places."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .bars import books_for_symbol, load_challenge_books, load_gold_books, normalize_symbol
from .world_state import load_peer_books
from .compose import compose_shadow
from .family import family_class_for, hard_off_family, keep_family
from .gold_state import assemble_gold_state_v0
from .symbol_state import assemble_symbol_state_v0, load_peer_books_for
from .hold_from_tape import (
    classify_close,
    close_session_named,
    mfe_mae_r,
    realized_r,
)
from .host_events import last_stop_now, named_final_sl, news_inventory_at
from .jev_client import evaluate
from .news_spine import load_spines
from .occupancy import last_refusal_class, occupancy_at, refusal_tape, trades_from_dicts
from .peers import peer_books_for_xau
from .process_lock import leave_orig_ticket
from .aplus_sleeve import CATALOG, from_catalog, score_aplus_shadow, sleeve_name
from .sleeve_from_tape import features_from_books
from .two_stop import occupancy_from_closed, siblings_doc_for_label

FTMO_SERVER_OFFSET_HOURS = 3

ACCOUNT = {
    "login": 0,
    "ns": "operator",
    "magic": 0,
    "pass_line": 110000.0,
    "quarantine_login": 0,
}

REPO_ROOT = Path(__file__).resolve().parents[2]


def _parse_mt5_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = str(raw).strip()
    # MT5 sit writes 2026.09.17 10:30:55. Do not smash ISO microseconds
    # (2026-09-17T07:45:39.416839+00:00 → 39-416839), or last_seen falls
    # through to now() and invents a Friday as-of on rematerialize.
    if len(text) >= 10 and text[4] == "." and text[7] == ".":
        text = text.replace(".", "-", 2)
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            dt = datetime.strptime(text.replace("Z", ""), fmt) if "Z" in text and fmt.endswith("Z") else datetime.strptime(text, fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _side(value: str) -> str:
    raw = (value or "").lower()
    if raw in {"sell", "short"}:
        return "short"
    if raw in {"buy", "long"}:
        return "long"
    return raw or "unknown"


def _plan_r(entry: float | None, stop: float | None, target: float | None) -> float | None:
    if entry is None or stop is None or target is None:
        return None
    den = abs(entry - stop)
    if den <= 0:
        return None
    return abs(target - entry) / den


def challenge_as_of(pos: dict[str, Any]) -> datetime:
    """True UTC as-of. Sit already corrected. Deals/replay often carry server wall as UTC."""
    utc = _parse_mt5_time(
        pos.get("open_time_utc")
        or pos.get("last_seen_utc")
        or pos.get("first_seen_utc")
        or pos.get("open_time")
    )
    server = _parse_mt5_time(pos.get("open_time_server"))
    if utc is None:
        return datetime.now(timezone.utc)
    if server is not None:
        delta_h = abs((utc - server).total_seconds()) / 3600.0
        if 2.5 <= delta_h <= 3.5:
            return utc
        if delta_h < 0.05:
            return utc - timedelta(hours=FTMO_SERVER_OFFSET_HOURS)
    raw = str(pos.get("open_time_utc") or pos.get("open_time") or "")
    if pos.get("last_seen_utc") or pos.get("first_seen_utc") or pos.get("direction"):
        return utc
    if raw and "T" not in raw.replace(".", "-") and "Z" not in raw.upper() and "+" not in raw:
        return utc - timedelta(hours=FTMO_SERVER_OFFSET_HOURS)
    return utc


def _spread_r_of_stop(pos: dict[str, Any], stop_dist: float | None) -> float | None:
    named = _f(pos.get("spread_R") or pos.get("spread_r") or pos.get("spread_r_of_stop"))
    if named is not None:
        return named
    spread = _f(pos.get("spread_at_entry") or pos.get("spread"))
    if spread is not None and stop_dist and stop_dist > 0:
        return spread / stop_dist
    return None


def score_position(
    pos: dict[str, Any],
    *,
    books,
    spines,
    sit_meta: dict[str, Any],
    deal_tape=None,
    refusals=None,
    siblings_doc=None,
    feature_rows=None,
    host_events=None,
) -> dict[str, Any]:
    as_of = challenge_as_of(pos)
    side = _side(str(pos.get("side") or pos.get("direction") or ""))
    sleeve = str(pos.get("sleeve") or pos.get("comment") or pos.get("tag") or "unknown")
    if sleeve.startswith("F5:"):
        sleeve = sleeve[3:]
    setup_id = _aplus_setup_id(pos)
    if setup_id:
        return score_aplus_setup(
            pos,
            books=books,
            spines=spines,
            sit_meta=sit_meta,
            deal_tape=deal_tape,
        )
    symbol = str(pos.get("symbol") or "XAUUSD")
    books_here = books_for_symbol(symbol, books if isinstance(books, dict) else None)
    peer_books = load_peer_books(books if isinstance(books, dict) else None)
    entry = _f(pos.get("entry") or pos.get("open") or pos.get("open_price"))
    stop = _f(pos.get("orig_sl") or pos.get("sl") or pos.get("live_sl") or pos.get("stop"))
    target = _f(pos.get("tp"))
    stop_dist = _f(pos.get("stop_dist"))
    if stop_dist is None and entry is not None and stop is not None:
        stop_dist = abs(entry - stop)
    target_dist = abs(target - entry) if target is not None and entry is not None else None
    spread_r = _spread_r_of_stop(pos, stop_dist)
    assembler = (
        assemble_gold_state_v0
        if normalize_symbol(symbol) == "XAUUSD"
        else assemble_symbol_state_v0
    )
    peer_books = {}
    try:
        peer_books = load_peer_books_for(symbol, books if isinstance(books, dict) else None)
    except Exception:
        peer_books = {}
    state = assembler(
        as_of_utc=as_of,
        side=side,
        sleeve=sleeve,
        symbol=symbol,
        candidate_id=str(pos.get("ticket") or pos.get("candidate_id") or "unknown"),
        origin_organism="f5_challenge",
        as_of_clock="as_of_open_study",
        books=books_here,
        spines=spines,
        geometry={
            "entry": entry,
            "stop": stop,
            "target": target,
            "stop_dist": stop_dist,
            "target_dist": target_dist,
            "plan_r": _plan_r(entry, stop, target),
            "order_type": "MARKET",
        },
        cost={
            "spread_r": spread_r,
            "spread_r_of_stop": spread_r,
            "source": "tick" if spread_r is not None else "unassembled",
            "cost_screen_would_refuse": bool(spread_r is not None and spread_r > 0.10),
        },
        occupancy={
            **occupancy_at(
                deal_tape,
                symbol=symbol,
                as_of_utc=as_of,
                this_ticket=pos.get("ticket") or pos.get("candidate_id"),
                kind=str(pos.get("_kind") or ""),
                still_open=bool(pos.get("still_open")),
            ),
            **occupancy_from_closed(
                siblings_doc if siblings_doc is not None else siblings_doc_for_label(feature_rows, stamp=challenge_as_of),
                sleeve=sleeve,
                as_of_utc=as_of,
                symbol=symbol,
            ),
        },
        sleeve_features=features_from_books(books_here, as_of, tag=sleeve),
        peer_books=peer_books,
        deal_tape=deal_tape,
        surface={"token_digest_matches": None},
        forbid_expost={k: pos[k] for k in ("broker_net", "profit", "R", "exit_class") if k in pos},
    )
    # as_of_open_study allows expost in the source sit; they must not be inside state.
    leave = _row_leave_orig(pos)
    close_utc = None
    if pos.get("close_time_utc") or pos.get("close_time"):
        close_utc = challenge_as_of(
            {
                "open_time_utc": pos.get("close_time_utc") or pos.get("close_time"),
                "open_time_server": pos.get("close_time_server"),
            }
        )
    exit_px = _f(pos.get("exit") or pos.get("close") or pos.get("close_price"))
    realized = realized_r(entry=entry, exit_px=exit_px, stop_dist=stop_dist, side=side)
    mfe_r = mae_r = None
    kind = str(pos.get("_kind") or "")
    if kind in {"deal_close", "close", "replay_close"} and not pos.get("still_open"):
        m15 = (books_here or {}).get("m15")
        mfe_r, mae_r = mfe_mae_r(
            m15,
            side=side,
            entry=entry,
            stop_dist=stop_dist,
            open_utc=as_of,
            close_utc=close_utc,
        )
    last_ref = last_refusal_class(
        refusals,
        symbol=symbol,
        as_of_utc=as_of,
        named=pos.get("last_refusal_class") or pos.get("packet_class") or pos.get("reason"),
    )
    ticket = pos.get("ticket") or pos.get("candidate_id")
    extra = {
        "kind": pos.get("_kind"),
        "close_reason": pos.get("close_reason") or pos.get("reason"),
        "exit_class": pos.get("exit_class") or pos.get("close_class"),
        "close_label": classify_close(
            pos.get("close_reason") or pos.get("reason"),
            pos.get("exit_class") or pos.get("close_class"),
        ),
        "last_seen_utc": pos.get("last_seen_utc"),
        "first_seen_utc": pos.get("first_seen_utc"),
        "built_at_utc": sit_meta.get("sit_utc"),
        "final_sl": named_final_sl(
            deal_final=pos.get("final_sl"),
            event_stop_now=last_stop_now(host_events, ticket),
        ),
        "still_open": pos.get("still_open"),
        "close_utc": close_utc.strftime("%Y-%m-%dT%H:%M:%SZ") if close_utc else None,
        "close_session": close_session_named(close_utc),
        "mfe_r": mfe_r,
        "mae_r": mae_r,
        "realized_r": realized,
        "last_refusal_class": last_ref,
    }
    extra.update(news_inventory_at(host_events, as_of))
    jev = evaluate(state)
    composed = compose_shadow(
        state,
        jev.get("answers") or {},
        ticket=ticket,
        leave_orig=leave,
        extra=extra,
    )
    return {
        "schema": "gtos.judgment.challenge_shadow.v0",
        "account_surface": ACCOUNT,
        "kind": pos.get("_kind") or "open_or_close",
        "ticket": pos.get("ticket"),
        "sit": {k: sit_meta.get(k) for k in ("sit_utc", "bal", "eq", "to_pass", "day_net")},
        "house": {
            "family_class": family_class_for(sleeve, symbol=symbol),
            "hard_off_family": hard_off_family(sleeve, symbol),
            "keep_family": keep_family(sleeve),
            "leave_orig": leave,
        },
        "state": state,
        "jev": {k: jev.get(k) for k in ("ok", "skipped", "error", "model")},
        "answers": jev.get("answers") or {},
        "compose": composed,
        "missing_state": state["completeness"]["missing_fields"],
        "diagnosis": _diagnosis(state, composed, pos),
    }


def _aplus_setup_id(pos: dict[str, Any]) -> str | None:
    setup = str(pos.get("setup_id") or "").strip()
    if setup in CATALOG:
        return setup
    sleeve = str(pos.get("sleeve") or pos.get("tag") or pos.get("comment") or "")
    if sleeve.startswith("F5:"):
        sleeve = sleeve[3:]
    raw = sleeve[len("aplus_") :] if sleeve.startswith("aplus_") else ""
    if raw in CATALOG:
        return raw
    if sleeve_name(setup).removeprefix("aplus_") in CATALOG:
        return sleeve_name(setup).removeprefix("aplus_")
    return None


def score_aplus_setup(
    pos: dict[str, Any],
    *,
    books=None,
    spines=None,
    sit_meta: dict[str, Any] | None = None,
    deal_tape=None,
) -> dict[str, Any]:
    """Score an A+ sleeve candidate on the same Challenge shadow path. Never applies."""
    setup_id = _aplus_setup_id(pos)
    if setup_id is None:
        raise KeyError("not an APlus catalog sleeve")
    spec = from_catalog(setup_id)
    as_of = challenge_as_of(pos)
    symbol = str(pos.get("symbol") or (spec.symbol if hasattr(spec, "symbol") else "XAUUSD"))
    books_here = books_for_symbol(symbol, books if isinstance(books, dict) else None)
    entry = _f(pos.get("entry") or pos.get("open") or pos.get("open_price"))
    stop = _f(pos.get("orig_sl") or pos.get("sl") or pos.get("live_sl") or pos.get("stop"))
    target = _f(pos.get("tp"))
    stop_dist = _f(pos.get("stop_dist"))
    row = score_aplus_shadow(
        spec if hasattr(spec, "setup_id") else setup_id,
        as_of_utc=as_of,
        side=_side(str(pos.get("side") or pos.get("direction") or "")),
        candidate_id=str(pos.get("ticket") or pos.get("candidate_id") or sleeve_name(setup_id)),
        books=books_here,
        geometry={
            "entry": entry,
            "stop": stop,
            "target": target,
            "stop_dist": stop_dist,
        },
        cost={
            "spread_r": _spread_r_of_stop(pos, stop_dist),
            "spread_r_of_stop": _spread_r_of_stop(pos, stop_dist),
            "source": "tick" if _spread_r_of_stop(pos, stop_dist) is not None else "unassembled",
        },
        deal_tape=deal_tape,
        spines=spines,
        ticket=pos.get("ticket") or pos.get("candidate_id"),
    )
    row["kind"] = pos.get("_kind") or "aplus_shadow"
    row["ticket"] = pos.get("ticket") or pos.get("candidate_id")
    row["sit"] = {k: (sit_meta or {}).get(k) for k in ("sit_utc", "bal", "eq", "to_pass", "day_net")}
    row["house"] = {
        "family_class": row["family_class"],
        "hard_off_family": None,
        "keep_family": False,
        "leave_orig": False,
        "aplus_shadow_only": True,
    }
    return row


def _row_leave_orig(pos: dict[str, Any]) -> bool:
    """Leave-orig is ticket 293332188 or an already-open row. Not every slate."""
    if leave_orig_ticket(pos.get("ticket") or pos.get("candidate_id")):
        return True
    if pos.get("_kind") == "open" or pos.get("still_open"):
        return True
    return False


def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _diagnosis(state: dict[str, Any], composed: dict[str, Any], pos: dict[str, Any]) -> str:
    missing = state["completeness"]["missing_fields"]
    symbol = state["identity"]["symbol"]
    family = state["identity"]["family_class"]
    bits = []
    if "timeframes.m15" in missing or "timeframes.h4" in missing:
        bits.append(
            f"tape_unassembled — pull {symbol} M15/H4 covering the open as-of "
            "(D1 optional; April repo M15 is not Challenge-true)"
        )
    if state["news"]["spine_empty"]:
        bits.append("news_spine_empty — event questions abstain (repair calendar, do not invent)")
    if family == "house_hard_off":
        bits.append(f"host_surface_drift_or_hard_off {symbol} {state['identity']['sleeve']}")
    if composed["local_flow_stance"] == "against_flow":
        bits.append("local_h4_against_flow")
    if composed.get("leave_orig"):
        bits.append("leave_orig — live 1.0 (ticket 293332188 or already-open)")
    elif composed.get("disposition") == "named_apply":
        bits.append(
            f"named_apply flow={composed.get('live_size_tilt')} cost={composed.get('live_cost_tilt')}"
        )
    elif composed.get("shadow_cost_tilt") not in (None, 1.0) and composed.get("live_cost_tilt") == 1.0:
        bits.append(f"shadow_cost_tilt {composed['shadow_cost_tilt']} live 1.0 — F5-JEV-004 log_only")
    if not bits:
        bits.append("state_partial_ok — compose logged; no refuse fence added")
    return "; ".join(bits)


def score_sit(
    sit: dict[str, Any],
    *,
    books=None,
    spines=None,
    deal_tape=None,
    refusals=None,
    siblings_doc=None,
    feature_rows=None,
    host_events=None,
) -> list[dict[str, Any]]:
    books = books if books is not None else load_gold_books()
    spines = spines if spines is not None else load_spines()
    meta = {
        "sit_utc": sit.get("sit_utc"),
        "bal": sit.get("bal"),
        "eq": sit.get("eq"),
        "to_pass": sit.get("to_pass"),
        "day_net": sit.get("day_net"),
    }
    sit_rows = list(sit.get("positions") or []) + list(sit.get("closes_since_2026_09_15_18UTC") or [])
    tape = deal_tape
    if tape is None:
        tape = trades_from_dicts(sit_rows, stamp=challenge_as_of)
    packed = list(feature_rows) if feature_rows is not None else sit_rows
    sib = siblings_doc if siblings_doc is not None else siblings_doc_for_label(packed, stamp=challenge_as_of)
    rows: list[dict[str, Any]] = []
    for pos in sit.get("positions") or []:
        item = dict(pos)
        item["_kind"] = "open"
        rows.append(
            score_position(
                item,
                books=books,
                spines=spines,
                sit_meta=meta,
                deal_tape=tape,
                refusals=refusals,
                siblings_doc=sib,
                feature_rows=packed,
                host_events=host_events,
            )
        )
    for close in sit.get("closes_since_2026_09_15_18UTC") or []:
        item = dict(close)
        item["_kind"] = "close"
        item.setdefault("entry", item.get("open"))
        item.setdefault("orig_sl", item.get("sl"))
        rows.append(
            score_position(
                item,
                books=books,
                spines=spines,
                sit_meta=meta,
                deal_tape=tape,
                refusals=refusals,
                siblings_doc=sib,
                feature_rows=packed,
                host_events=host_events,
            )
        )
    return rows


def score_replay_row(row: dict[str, Any], *, books=None, spines=None, host_events=None) -> dict[str, Any]:
    inp = dict(row.get("input") or row)
    inp["_kind"] = "replay_close"
    return score_position(
        inp,
        books=books or {},
        spines=spines or load_spines(),
        sit_meta={},
        host_events=host_events,
    )


def _slate_bags(slate: dict[str, Any]) -> list[dict[str, Any]]:
    bags: list[dict[str, Any]] = []
    seen: set[str] = set()
    for key in ("candidates", "intents", "units", "positions", "standing", "fires", "refusals"):
        val = slate.get(key)
        if isinstance(val, list):
            for item in val:
                if not isinstance(item, dict):
                    continue
                cid = str(item.get("candidate_id") or item.get("ticket") or item.get("id") or "")
                if cid and cid in seen:
                    continue
                if cid:
                    seen.add(cid)
                bags.append(item)
    skips = slate.get("skips")
    if isinstance(skips, list):
        bags.extend(x for x in skips if isinstance(x, dict))
    elif isinstance(skips, dict):
        for item in skips.get("recent") or []:
            if isinstance(item, dict):
                bags.append(item)
    for nest_key in ("judgment", "state", "slate", "book"):
        nest = slate.get(nest_key)
        if isinstance(nest, dict):
            bags.extend(_slate_bags(nest))
    return bags


def is_slate_pointer(slate: dict[str, Any]) -> bool:
    """Host latest_slate.json is often a pointer (slate_id + path), not the body."""
    if not isinstance(slate, dict):
        return False
    has_id = bool(slate.get("slate_id") or slate.get("id"))
    has_path = bool(slate.get("path"))
    return has_id and has_path and not _slate_bags(slate)


def score_slate_pointer(slate: dict[str, Any]) -> dict[str, Any]:
    """Log the pointer. Do not invent candidates from a path that is not here."""
    from .compose import compose_shadow
    from .process_lock import stamp_lock

    composed = compose_shadow(
        {
            "identity": {"symbol": None, "side": None, "family_class": "unknown"},
            "completeness": {"state_sufficient_for_live": False, "cost": False},
            "news": {"spine_empty": False},
            "cost": {},
            "timeframes": {},
        },
        leave_orig=True,
    )
    return {
        "schema": "gtos.judgment.challenge_shadow.v0",
        "account_surface": ACCOUNT,
        "kind": "slate_pointer",
        "ticket": None,
        "slate_id": slate.get("slate_id") or slate.get("id"),
        "fingerprint": slate.get("fingerprint"),
        "built_at_utc": slate.get("built_at_utc"),
        "host_path": slate.get("path"),
        "body_present": False,
        "house": {"leave_orig": True, "family_class": None},
        "compose": composed,
        "state": None,
        "missing_state": ["slate.body"],
        "diagnosis": (
            f"slate pointer {slate.get('slate_id')} fingerprint {slate.get('fingerprint')} "
            "— body not in this workspace; do not invent candidates. "
            "Attach slate_20260917T102606Z_21a8b9034f43e82a.json (~40KB) to score fires."
        ),
        "lock": stamp_lock(),
    }


def score_slate(
    slate: dict[str, Any],
    *,
    books=None,
    spines=None,
    deal_tape=None,
    refusals=None,
    siblings_doc=None,
    feature_rows=None,
    host_events=None,
) -> list[dict[str, Any]]:
    """Score a host latest_slate.json (or any candidate bag). Log only."""
    if is_slate_pointer(slate):
        return [score_slate_pointer(slate)]
    books = books if books is not None else load_gold_books()
    spines = spines if spines is not None else load_spines()
    named_refusals = refusals if refusals is not None else refusal_tape(slate)
    packed = list(feature_rows) if feature_rows is not None else None
    sib = siblings_doc if siblings_doc is not None else siblings_doc_for_label(packed, stamp=challenge_as_of)
    meta = {
        "sit_utc": slate.get("as_of") or slate.get("generated_at") or slate.get("slate_time") or slate.get("built_at_utc"),
        "slate_id": slate.get("slate_id") or slate.get("id"),
        "fingerprint": slate.get("fingerprint"),
        "bal": slate.get("bal") or slate.get("balance"),
        "eq": slate.get("eq") or slate.get("equity"),
    }
    rows: list[dict[str, Any]] = []
    for item in _slate_bags(slate):
        rec = dict(item)
        rec["_kind"] = rec.get("_kind") or ("slate_skip" if rec.get("reason") and not rec.get("candidate_id") else "slate")
        rec.setdefault("sleeve", rec.get("tag") or rec.get("comment") or rec.get("family") or rec.get("sleeve"))
        rec.setdefault("ticket", rec.get("candidate_id") or rec.get("ticket") or rec.get("id"))
        rec.setdefault("side", rec.get("direction") or rec.get("side"))
        rec.setdefault("entry", rec.get("open") or rec.get("open_price") or rec.get("entry_price") or rec.get("frozen_entry"))
        rec.setdefault("orig_sl", rec.get("sl") or rec.get("stop") or rec.get("orig_sl"))
        rec.setdefault(
            "open_time_utc",
            rec.get("last_seen_utc")
            or rec.get("first_seen_utc")
            or rec.get("ts_utc")
            or rec.get("quote_at_utc")
            or meta.get("sit_utc"),
        )
        rec.setdefault("stop_dist", rec.get("stop_dist") or rec.get("stop_dist_price"))
        rec.setdefault("spread_r_of_stop", rec.get("spread_r_of_stop"))
        rec.setdefault("last_refusal_class", rec.get("last_refusal_class") or rec.get("packet_class") or rec.get("reason"))
        rows.append(
            score_position(
                rec,
                books=books,
                spines=spines,
                sit_meta=meta,
                deal_tape=deal_tape,
                refusals=named_refusals,
                siblings_doc=sib,
                feature_rows=packed,
                host_events=host_events,
            )
        )
    return rows


def score_deals(
    deals: Iterable[dict[str, Any]],
    *,
    books=None,
    spines=None,
    skip_tickets: set[str] | None = None,
    deal_tape=None,
    refusals=None,
    siblings_doc=None,
    feature_rows=None,
    host_events=None,
) -> list[dict[str, Any]]:
    """Score Challenge deals. Skip leave-orig opens already scored from sit.

    Sit closes usually lack spread/stop. Prefer the deal row for those tickets
    so the prove pack is not starved of cost-complete XAU.
    """
    books = books if books is not None else load_challenge_books()
    spines = spines if spines is not None else load_spines()
    packed = list(deals)
    tape = deal_tape if deal_tape is not None else trades_from_dicts(packed, stamp=challenge_as_of)
    source_rows = list(feature_rows) if feature_rows is not None else packed
    sib = siblings_doc if siblings_doc is not None else siblings_doc_for_label(source_rows, stamp=challenge_as_of)
    skip = {str(t) for t in (skip_tickets or set())}
    rows: list[dict[str, Any]] = []
    for deal in packed:
        ticket = str(deal.get("ticket") or "")
        if ticket and ticket in skip:
            continue
        rec = dict(deal)
        rec["_kind"] = "open" if deal.get("still_open") else "deal_close"
        rec.setdefault("orig_sl", rec.get("orig_sl") or rec.get("final_sl"))
        rows.append(
            score_position(
                rec,
                books=books,
                spines=spines,
                sit_meta={},
                deal_tape=tape,
                refusals=refusals,
                siblings_doc=sib,
                feature_rows=source_rows,
                host_events=host_events,
            )
        )
    return rows


def compact_ticket_row(row: dict[str, Any]) -> dict[str, Any]:
    state = row.get("state") or {}
    return {
        "schema": row.get("schema"),
        "kind": row.get("kind"),
        "ticket": row.get("ticket"),
        "sit": row.get("sit"),
        "house": row.get("house"),
        "jev": row.get("jev"),
        "compose": row.get("compose"),
        "missing_state": row.get("missing_state"),
        "diagnosis": row.get("diagnosis"),
        "completeness": state.get("completeness"),
        "news_spine_empty": (state.get("news") or {}).get("spine_empty"),
        "n_news_events": len((state.get("news") or {}).get("events") or []),
        "identity": state.get("identity"),
    }


def build_deal_tape(sit: dict[str, Any] | None, deals: Iterable[dict[str, Any]] | None):
    rows: list[dict[str, Any]] = []
    if sit:
        rows.extend(sit.get("positions") or [])
        rows.extend(sit.get("closes_since_2026_09_15_18UTC") or [])
    if deals:
        rows.extend(deals)
    return trades_from_dicts(rows, stamp=challenge_as_of)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)
