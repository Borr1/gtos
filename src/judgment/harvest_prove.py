"""SHADOW prove for harvest P0 atoms. Research-only. Never places.

P0-1 first (Chair 2026-09-18): ``feature_as_of_honest`` / ``harvest.pit.feature_as_of``
on Challenge login ``0``. No XAU default. Multi FX books if present.
Live multiplier stays 1.0. Empty spine stays empty. No vendor.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .bars import (
    books_for_symbol,
    landed_challenge_symbols,
    load_all_landed_challenge_books,
    normalize_symbol,
)
from .challenge_shadow import ACCOUNT, challenge_as_of, iter_jsonl, load_json
from .gold_state import assemble_gold_state_v0
from .harvest_patterns import (
    CHALLENGE_LOGIN,
    CHALLENGE_MAGIC,
    CHALLENGE_NS,
    CHAIR_ROUTE_CLASS_TABLE,
    CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED,
    NEVER_INVENT_NEWS,
    NEVER_PLACE,
    NEVER_VENDOR,
    ROUTE_CLASS_CHOICES,
    SCHEMA_LOCK,
    allowed_route_classes,
    attach_harvest_blocks,
    chair_route_class_for,
    choice_route_class,
    feature_as_of_from_books,
    noul_feature_as_of_honest,
    route_symbol,
    score_fill_realism,
)
from .news_spine import load_spines
from .process_lock import PROVE_BARS_FLUID_SIZE, stamp_lock
from .sleeve_from_tape import features_from_books

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DEALS = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "deals_since_20260909.jsonl"
)
DEFAULT_SIT = REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "sit_20260917.json"
DEFAULT_RECEIPT = (
    REPO_ROOT / "judgment" / "astra" / "oss_harvest" / "P0_1_FEATURE_AS_OF_HONEST_PROVE.json"
)
DEFAULT_P0_2 = REPO_ROOT / "judgment" / "astra" / "oss_harvest" / "P0_2_TF_ROUTE_PROVE.json"
DEFAULT_P0_5 = REPO_ROOT / "judgment" / "astra" / "oss_harvest" / "P0_5_FILL_REALISM_PROVE.json"
QUESTION_ID = "feature_as_of_honest"
ATOM_ID = "P0-1"
INJECT_LEAKS = 6


def _f(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _side(value: str) -> str:
    raw = (value or "").lower()
    if raw in {"sell", "short"}:
        return "short"
    if raw in {"buy", "long"}:
        return "long"
    return raw or "unknown"


def _sleeve(pos: Mapping[str, Any]) -> str:
    sleeve = str(pos.get("sleeve") or pos.get("comment") or pos.get("tag") or "")
    if sleeve.startswith("F5:"):
        sleeve = sleeve[3:]
    return sleeve or "unknown"


def load_challenge_intents(
    *,
    deals_path: Path | None = DEFAULT_DEALS,
    sit_path: Path | None = DEFAULT_SIT,
) -> list[dict[str, Any]]:
    """Named Challenge intents. Missing symbol is skipped — never defaulted to XAU."""
    out: list[dict[str, Any]] = []
    if sit_path and sit_path.is_file():
        sit = load_json(sit_path)
        for pos in sit.get("positions") or []:
            if not str(pos.get("symbol") or "").strip():
                continue
            rec = dict(pos)
            rec["_kind"] = "sit_open"
            rec["_login"] = sit.get("login") or ACCOUNT["login"]
            out.append(rec)
    if deals_path and deals_path.is_file():
        sit_tickets = {str(r.get("ticket")) for r in out if r.get("ticket")}
        for deal in iter_jsonl(deals_path):
            if not str(deal.get("symbol") or "").strip():
                continue
            ticket = str(deal.get("ticket") or "")
            if ticket and ticket in sit_tickets:
                continue
            rec = dict(deal)
            rec["_kind"] = "deal"
            rec["_login"] = ACCOUNT["login"]
            out.append(rec)
    return out


def _geometry(pos: Mapping[str, Any]) -> dict[str, Any]:
    entry = _f(pos.get("entry") or pos.get("open") or pos.get("open_price"))
    stop = _f(pos.get("orig_sl") or pos.get("sl") or pos.get("live_sl") or pos.get("stop"))
    target = _f(pos.get("tp"))
    stop_dist = _f(pos.get("stop_dist"))
    if stop_dist is None and entry is not None and stop is not None:
        stop_dist = abs(entry - stop)
    return {
        "entry": entry,
        "stop": stop,
        "target": target,
        "stop_dist": stop_dist,
        "order_type": "MARKET",
    }


def score_harvest_row(
    pos: Mapping[str, Any],
    *,
    books_cache: dict[str, Any] | None,
    spines: dict[str, Any],
    inject_future_ac60: bool = False,
) -> dict[str, Any] | None:
    symbol = str(pos.get("symbol") or "").strip()
    if not symbol:
        return None
    as_of = challenge_as_of(dict(pos))
    books_here = books_for_symbol(symbol, books_cache)
    feats = features_from_books(books_here, as_of, tag=_sleeve(pos)) if books_here else {}
    stamps = feature_as_of_from_books(books_here, as_of, feats) if books_here else {}
    if inject_future_ac60:
        future = (as_of + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        stamps = dict(stamps)
        stamps["ac60"] = future
        if feats.get("ac60") is None:
            feats = dict(feats)
            feats["ac60"] = 0.11
    geo = _geometry(pos)
    spread = None
    for key in ("spread_r_of_stop", "cost_R", "spread_R"):
        got = _f(pos.get(key))
        if got is not None:
            spread = got
            break
    if spread is None:
        raw_spread = _f(pos.get("spread_at_entry") or pos.get("spread"))
        stop_dist = geo.get("stop_dist")
        if raw_spread is not None and stop_dist and stop_dist > 0:
            spread = raw_spread / float(stop_dist)
    state = assemble_gold_state_v0(
        as_of_utc=as_of,
        side=_side(str(pos.get("side") or pos.get("direction") or "")),
        sleeve=_sleeve(pos),
        symbol=symbol,
        candidate_id=str(pos.get("ticket") or pos.get("candidate_id") or "unknown"),
        origin_organism="f5_challenge",
        as_of_clock="as_of_open_study",
        books=books_here,
        spines=spines,
        geometry=geo,
        cost={
            "spread_r_of_stop": spread,
            "source": "tick" if spread is not None else "unassembled",
        },
        sleeve_features=feats,
    )
    attached = attach_harvest_blocks(state, feature_as_of=stamps)
    pit = (attached.get("harvest") or {}).get("pit") or {}
    noul = noul_feature_as_of_honest(pit)
    news = attached.get("news") or {}
    identity_symbol = (attached.get("identity") or {}).get("symbol")
    requested = normalize_symbol(symbol)
    assembled_sym = normalize_symbol(str(identity_symbol or ""))
    xau_substituted = requested not in {"XAUUSD", "XAU"} and assembled_sym == "XAUUSD"
    return {
        "schema": "gtos.judgment.harvest_shadow_row.v0",
        "atom": ATOM_ID,
        "question": QUESTION_ID,
        "kind": pos.get("_kind"),
        "ticket": pos.get("ticket"),
        "symbol": symbol,
        "identity_symbol": identity_symbol,
        "tape_present": bool(books_here and (books_here.get("m15") or books_here.get("h4"))),
        "xau_substituted": xau_substituted,
        "injected_future_ac60": inject_future_ac60,
        "noul": noul,
        "harvest": attached.get("harvest"),
        "state": {
            "identity": attached.get("identity"),
            "clock": attached.get("clock"),
            "news": {
                "spine_empty": news.get("spine_empty"),
                "high_in_f5_window": news.get("high_in_f5_window"),
                "events": news.get("events") or [],
            },
            "completeness": attached.get("completeness"),
            "sleeve_features": attached.get("sleeve_features"),
        },
        "live_multiplier": (attached.get("harvest") or {}).get("live_multiplier"),
    }


def build_p0_1_shadow(
    intents: Iterable[Mapping[str, Any]] | None = None,
    *,
    inject_leaks: int = INJECT_LEAKS,
) -> list[dict[str, Any]]:
    spines = load_spines()
    cache = load_all_landed_challenge_books()
    source = list(intents) if intents is not None else load_challenge_intents()
    rows: list[dict[str, Any]] = []
    honest_pos: list[Mapping[str, Any]] = []
    for pos in source:
        row = score_harvest_row(pos, books_cache=cache, spines=spines, inject_future_ac60=False)
        if row is None:
            continue
        rows.append(row)
        if row["noul"]["decidable"] and row["noul"]["noul"] is True:
            honest_pos.append(pos)
    for i, pos in enumerate(honest_pos[: max(0, inject_leaks)]):
        leak = score_harvest_row(pos, books_cache=cache, spines=spines, inject_future_ac60=True)
        if leak is None:
            continue
        leak["ticket"] = f"{leak.get('ticket')}:leak{i}"
        rows.append(leak)
    return rows


def _invented_high(rows: list[dict[str, Any]]) -> int:
    n = 0
    for row in rows:
        news = ((row.get("state") or {}).get("news") or {})
        if news.get("spine_empty") and news.get("high_in_f5_window") is True:
            n += 1
    return n


def prove_p0_1(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bars = dict(PROVE_BARS_FLUID_SIZE)
    decidable = [r for r in rows if (r.get("noul") or {}).get("decidable")]
    moved = [r for r in decidable if (r.get("noul") or {}).get("moved")]
    live_not_one = [
        r for r in rows if abs(float(r.get("live_multiplier") if r.get("live_multiplier") is not None else 1.0) - 1.0) > 1e-9
    ]
    xau_sub = [r for r in rows if r.get("xau_substituted") or (
        str(r.get("symbol") or "").upper() not in {"", "XAUUSD", "XAU"}
        and str((r.get("identity_symbol") or "")).upper() == "XAUUSD"
    )]
    invented = _invented_high(rows)
    reasons: list[str] = []
    if invented:
        reasons.append(f"invented_high n={invented} — empty spine claimed F5 HIGH")
    if live_not_one:
        reasons.append(f"live_multiplier_not_one n={len(live_not_one)}")
    if xau_sub:
        reasons.append(f"xau_default n={len(xau_sub)} — non-XAU row wore XAU identity")
    if len(decidable) < int(bars["min_decidable"]):
        reasons.append(f"decidable {len(decidable)} < {bars['min_decidable']}")
    if len(moved) < int(bars["min_moved"]):
        reasons.append(f"moved {len(moved)} < {bars['min_moved']} — inject future ac60 or named leak")
    symbols = Counter(str(r.get("symbol") or "") for r in rows)
    landed = landed_challenge_symbols()
    verdict = "PROVED_SHADOW" if not reasons else "NOT_PROVED"
    return {
        "schema": "gtos.judgment.harvest_p0_1_prove.v0",
        "atom": ATOM_ID,
        "question": QUESTION_ID,
        "field": "harvest.pit.feature_as_of",
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "schema_lock": SCHEMA_LOCK,
        "never_place": NEVER_PLACE,
        "never_vendor": NEVER_VENDOR,
        "never_invent_news": NEVER_INVENT_NEWS,
        "chair_named_atom": False,
        "verdict": verdict,
        "ready_to_apply": False,
        "bars": bars,
        "n": len(rows),
        "n_decidable": len(decidable),
        "n_moved": len(moved),
        "n_invented_high": invented,
        "n_live_not_one": len(live_not_one),
        "n_xau_substituted": len(xau_sub),
        "symbols": dict(symbols),
        "landed_books": landed,
        "multi_fx_books_present": any(s != "XAUUSD" for s in landed),
        "reasons": reasons,
        "lock": stamp_lock(),
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _honest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if not r.get("injected_future_ac60")]


def _is_xau_row(row: Mapping[str, Any]) -> bool:
    return normalize_symbol(str(row.get("symbol") or "")) in {"XAUUSD", "XAU"}


def prove_p0_2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Chair-named route_class table. SHADOW labels only. Live 1.0. No APPLY."""
    bars = dict(PROVE_BARS_FLUID_SIZE)
    honest = _honest_rows(rows)
    decidable: list[dict[str, Any]] = []
    moved: list[dict[str, Any]] = []
    invented_rc: list[dict[str, Any]] = []
    invented_non_xau: list[dict[str, Any]] = []
    us30_honesty_miss: list[dict[str, Any]] = []
    live_not_one = [
        r for r in honest
        if abs(float(r.get("live_multiplier") if r.get("live_multiplier") is not None else 1.0) - 1.0) > 1e-9
    ]
    invented_high = _invented_high(honest)
    tf_routes: Counter[str] = Counter()
    route_classes: Counter[str] = Counter()
    non_xau_tf_attached = 0
    non_xau_class_unknown = 0
    n_unknown_until_landed = 0
    n_us30_house_hard_off = 0
    for row in honest:
        harvest = row.get("harvest") or {}
        symbol = str(row.get("symbol") or "")
        tf = (harvest.get("route") or {}).get("tf_route") or "unknown"
        rc = harvest.get("route_class") or choice_route_class(symbol, tf)
        choice = str(rc.get("choice") or "unknown")
        allowed = allowed_route_classes(symbol)
        expected = chair_route_class_for(symbol)
        tf_routes[tf] += 1
        route_classes[choice] += 1
        if rc.get("decidable"):
            decidable.append(row)
        if not _is_xau_row(row) and tf != "unknown":
            non_xau_tf_attached += 1
        if choice not in ROUTE_CLASS_CHOICES and choice != "multi":
            invented_rc.append(row)
            if not _is_xau_row(row):
                invented_non_xau.append(row)
        elif choice not in allowed:
            invented_rc.append(row)
            if not _is_xau_row(row):
                invented_non_xau.append(row)
        elif choice != "unknown":
            moved.append(row)
        elif expected == "unknown":
            if route_symbol(symbol) in CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED:
                n_unknown_until_landed += 1
            if not _is_xau_row(row):
                non_xau_class_unknown += 1
        if _is_xau_row(row):
            continue
        if expected == "index":
            if rc.get("house_hard_off") is True:
                n_us30_house_hard_off += 1
            else:
                us30_honesty_miss.append(row)
    reasons: list[str] = []
    if invented_high:
        reasons.append(f"invented_high n={invented_high}")
    if live_not_one:
        reasons.append(f"live_multiplier_not_one n={len(live_not_one)}")
    if invented_rc:
        reasons.append(
            f"invented_route_class n={len(invented_rc)} — class must match Chair table "
            "(UK100/BTC/ETH stay unknown; no class outside metal/fx_major/fx_cross/index)"
        )
    if us30_honesty_miss:
        reasons.append(
            f"us30_index_missing_house_hard_off_honesty n={len(us30_honesty_miss)}"
        )
    if len(decidable) < int(bars["min_decidable"]):
        reasons.append(f"decidable {len(decidable)} < {bars['min_decidable']}")
    if len(moved) < int(bars["min_moved"]):
        reasons.append(f"moved {len(moved)} < {bars['min_moved']}")
    landed = landed_challenge_symbols()
    verdict = "PROVED_SHADOW" if not reasons else "NOT_PROVED"
    return {
        "schema": "gtos.judgment.harvest_p0_2_prove.v0",
        "atom": "P0-2",
        "question": "route_class",
        "field": "identity.tf_route",
        "extra_fields": ["harvest.route_class", "harvest.route.tf_route"],
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "schema_lock": SCHEMA_LOCK,
        "never_place": NEVER_PLACE,
        "never_vendor": NEVER_VENDOR,
        "never_invent_news": NEVER_INVENT_NEWS,
        "chair_named_atom": True,
        "chair_named_scope": "shadow_labels_only",
        "chair_route_class_table": dict(CHAIR_ROUTE_CLASS_TABLE),
        "unknown_until_landed": sorted(CHAIR_ROUTE_CLASS_UNKNOWN_UNTIL_LANDED),
        "verdict": verdict,
        "ready_to_apply": False,
        "bars": bars,
        "n": len(honest),
        "n_decidable": len(decidable),
        "n_moved": len(moved),
        "n_invented_high": invented_high,
        "n_live_not_one": len(live_not_one),
        "n_invented_route_class": len(invented_rc),
        "n_invented_route_class_non_xau": len(invented_non_xau),
        "n_non_xau_tf_attached": non_xau_tf_attached,
        "n_non_xau_route_class_unknown": non_xau_class_unknown,
        "n_unknown_until_landed": n_unknown_until_landed,
        "n_us30_house_hard_off": n_us30_house_hard_off,
        "tf_routes": dict(tf_routes),
        "route_classes": dict(route_classes),
        "landed_books": landed,
        "multi_fx_books_present": any(s != "XAUUSD" for s in landed),
        "reasons": reasons,
        "lock": stamp_lock(),
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "Chair NAME 2026-09-18: route_class table is metal / fx_major / "
            "fx_cross / index. UK100/BTC/ETH stay unknown until landed+named. "
            "SHADOW labels only. Live 1.0. No APPLY."
        ),
    }


def stub_p0_2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Backward alias — P0-2 is now a prove, not a stub."""
    return prove_p0_2(rows)


def prove_p0_5(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """fill_realism Score. unknown abstains. APPLY false. Live 1.0."""
    bars = dict(PROVE_BARS_FLUID_SIZE)
    honest = _honest_rows(rows)
    decidable: list[dict[str, Any]] = []
    moved: list[dict[str, Any]] = []
    models: Counter[str] = Counter()
    live_not_one = [
        r for r in honest
        if abs(float(r.get("live_multiplier") if r.get("live_multiplier") is not None else 1.0) - 1.0) > 1e-9
    ]
    invented_high = _invented_high(honest)
    for row in honest:
        harvest = row.get("harvest") or {}
        fill = harvest.get("fill") or {}
        fr = harvest.get("fill_realism") or score_fill_realism(fill)
        models[str(fill.get("model") or "unknown")] += 1
        if fr.get("decidable"):
            decidable.append(row)
            if fr.get("moved"):
                moved.append(row)
    reasons: list[str] = []
    if invented_high:
        reasons.append(f"invented_high n={invented_high}")
    if live_not_one:
        reasons.append(f"live_multiplier_not_one n={len(live_not_one)}")
    if len(decidable) < int(bars["min_decidable"]):
        reasons.append(f"decidable {len(decidable)} < {bars['min_decidable']}")
    if len(moved) < int(bars["min_moved"]):
        reasons.append(f"moved {len(moved)} < {bars['min_moved']}")
    verdict = "PROVED_SHADOW" if not reasons else "NOT_PROVED"
    return {
        "schema": "gtos.judgment.harvest_p0_5_prove.v0",
        "atom": "P0-5",
        "question": "fill_realism",
        "field": "harvest.fill",
        "extra_fields": ["harvest.fill_realism", "harvest.fill.cost_complete"],
        "login": CHALLENGE_LOGIN,
        "ns": CHALLENGE_NS,
        "magic": CHALLENGE_MAGIC,
        "schema_lock": SCHEMA_LOCK,
        "never_place": NEVER_PLACE,
        "never_vendor": NEVER_VENDOR,
        "never_invent_news": NEVER_INVENT_NEWS,
        "chair_named_atom": False,
        "verdict": verdict,
        "ready_to_apply": False,
        "bars": bars,
        "n": len(honest),
        "n_decidable": len(decidable),
        "n_moved": len(moved),
        "n_invented_high": invented_high,
        "n_live_not_one": len(live_not_one),
        "fill_models": dict(models),
        "landed_books": landed_challenge_symbols(),
        "reasons": reasons,
        "lock": stamp_lock(),
        "proved_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": "Score 0 bar-fantasy / 2 tick-true. unknown abstains. No place. Live 1.0.",
    }


def write_receipt(
    receipt: Mapping[str, Any],
    *,
    stub: Mapping[str, Any] | None = None,
    p0_2: Mapping[str, Any] | None = None,
    p0_5: Mapping[str, Any] | None = None,
    out: Path | None = DEFAULT_RECEIPT,
) -> Path:
    path = out or DEFAULT_RECEIPT
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(receipt)
    companion = p0_2 if p0_2 is not None else stub
    if companion is not None:
        payload["p0_2"] = dict(companion)
        payload["p0_2_stub"] = dict(companion)
    if p0_5 is not None:
        payload["p0_5"] = dict(p0_5)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    md = path.with_suffix(".md")
    md.write_text(_receipt_md(payload), encoding="utf-8")
    return path


def _write_atom_receipt(receipt: Mapping[str, Any], path: Path, title: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(receipt), indent=2, sort_keys=False) + "\n", encoding="utf-8")
    reasons = receipt.get("reasons") or []
    reason_lines = "\n".join(f"- {r}" for r in reasons) if reasons else "- (none)"
    extra = ""
    if receipt.get("atom") == "P0-2":
        extra = (
            f"| non-XAU tf attached | {receipt.get('n_non_xau_tf_attached')} |\n"
            f"| non-XAU route_class unknown | {receipt.get('n_non_xau_route_class_unknown')} |\n"
            f"| unknown_until_landed | {receipt.get('n_unknown_until_landed')} |\n"
            f"| US30 house_hard_off honest | {receipt.get('n_us30_house_hard_off')} |\n"
            f"| invented_route_class | {receipt.get('n_invented_route_class')} |\n"
            f"| invented_route_class_non_xau | {receipt.get('n_invented_route_class_non_xau')} |\n"
            f"| tf_routes | `{receipt.get('tf_routes')}` |\n"
            f"| route_classes | `{receipt.get('route_classes')}` |\n"
            f"| chair table | `{receipt.get('chair_route_class_table')}` |\n"
        )
    if receipt.get("atom") == "P0-5":
        extra = f"| fill_models | `{receipt.get('fill_models')}` |\n"
    md = (
        f"# {title}\n\n"
        f"**Date:** {receipt.get('proved_at_utc')}\n"
        f"**Seat:** judgment / research. **No place. No vendor. No invent NEWS.**\n"
        f"**Account:** Challenge `{receipt.get('login')}` / `{receipt.get('ns')}` / magic `{receipt.get('magic')}`\n"
        f"**Schema lock:** `{receipt.get('schema_lock')}` — `harvest.*` extras on `gold_state.v0`.\n"
        f"**Verdict:** `{receipt.get('verdict')}` — not APPLY. Live multiplier 1.0. "
        f"{'Chair named the route_class table (SHADOW labels only).' if receipt.get('atom') == 'P0-2' else 'Chair has not named this atom onto a wire.'}\n\n"
        f"| Bar | Value |\n|---|---:|\n"
        f"| n | {receipt.get('n')} |\n"
        f"| decidable | {receipt.get('n_decidable')} (need ≥{receipt.get('bars', {}).get('min_decidable')}) |\n"
        f"| moved | {receipt.get('n_moved')} (need ≥{receipt.get('bars', {}).get('min_moved')}) |\n"
        f"| invented_high | {receipt.get('n_invented_high')} |\n"
        f"| live_not_one | {receipt.get('n_live_not_one')} |\n"
        f"{extra}\n"
        f"**Landed books:** `{receipt.get('landed_books')}`\n\n"
        f"**Reasons:**\n{reason_lines}\n\n"
        f"{receipt.get('note') or ''}\n"
    )
    path.with_suffix(".md").write_text(md, encoding="utf-8")
    return path


def _receipt_md(payload: Mapping[str, Any]) -> str:
    stub = payload.get("p0_2") or payload.get("p0_2_stub") or {}
    p05 = payload.get("p0_5") or {}
    reasons = payload.get("reasons") or []
    reason_lines = "\n".join(f"- {r}" for r in reasons) if reasons else "- (none)"
    return (
        f"# P0-1 SHADOW prove — `feature_as_of_honest`\n\n"
        f"**Date:** {payload.get('proved_at_utc')}\n"
        f"**Seat:** judgment / research. **No place. No vendor. No invent NEWS.**\n"
        f"**Account:** Challenge `{payload.get('login')}` / `{payload.get('ns')}` / magic `{payload.get('magic')}`\n"
        f"**Schema lock:** `{payload.get('schema_lock')}` — `harvest.*` extras on `gold_state.v0`.\n"
        f"**Verdict:** `{payload.get('verdict')}` — not APPLY. Live multiplier 1.0. Chair has not named this atom.\n\n"
        f"| Bar | Value |\n|---|---:|\n"
        f"| n | {payload.get('n')} |\n"
        f"| decidable | {payload.get('n_decidable')} (need ≥{payload.get('bars', {}).get('min_decidable')}) |\n"
        f"| moved | {payload.get('n_moved')} (need ≥{payload.get('bars', {}).get('min_moved')}) |\n"
        f"| invented_high | {payload.get('n_invented_high')} |\n"
        f"| live_not_one | {payload.get('n_live_not_one')} |\n"
        f"| xau_substituted | {payload.get('n_xau_substituted')} |\n"
        f"| multi_fx_books_present | {payload.get('multi_fx_books_present')} |\n\n"
        f"**Symbols on pack:** `{payload.get('symbols')}`\n\n"
        f"**Landed books:** `{payload.get('landed_books')}` — non-XAU keep their own symbol and do not wear XAU tape.\n\n"
        f"**Reasons:**\n{reason_lines}\n\n"
        f"## P0-2 (`tf_route` / `route_class`)\n\n"
        f"Verdict `{stub.get('verdict')}`. Chair-named table. "
        f"Classes `{stub.get('route_classes')}`. "
        f"unknown_until_landed = {stub.get('n_unknown_until_landed')}. "
        f"invented = {stub.get('n_invented_route_class')}. "
        f"US30 house_hard_off honest = {stub.get('n_us30_house_hard_off')}. "
        f"SHADOW labels only. Not APPLY.\n\n"
        f"## P0-5 (`fill_realism`)\n\n"
        f"Verdict `{p05.get('verdict')}`. decidable {p05.get('n_decidable')} / moved {p05.get('n_moved')}. "
        f"Models `{p05.get('fill_models')}`. Not APPLY.\n"
    )


def run_harvest(*, out: Path | None = DEFAULT_RECEIPT) -> dict[str, Any]:
    rows = build_p0_1_shadow()
    p01 = prove_p0_1(rows)
    p02 = prove_p0_2(rows)
    p05 = prove_p0_5(rows)
    write_receipt(p01, p0_2=p02, p0_5=p05, out=out)
    _write_atom_receipt(p02, DEFAULT_P0_2, "P0-2 SHADOW prove — `tf_route` / `route_class`")
    _write_atom_receipt(p05, DEFAULT_P0_5, "P0-5 SHADOW prove — `fill_realism`")
    p01["p0_2"] = p02
    p01["p0_2_stub"] = p02
    p01["p0_5"] = p05
    p01["out"] = str((out or DEFAULT_RECEIPT).relative_to(REPO_ROOT))
    p01["out_p0_2"] = str(DEFAULT_P0_2.relative_to(REPO_ROOT))
    p01["out_p0_5"] = str(DEFAULT_P0_5.relative_to(REPO_ROOT))
    return p01


def run_p0_1(*, out: Path | None = DEFAULT_RECEIPT) -> dict[str, Any]:
    return run_harvest(out=out)
