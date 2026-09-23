"""Inventory remaining SHADOW fluid axes + multi-instrument blockers.

Challenge-true only. Never invents HIGH, trails, Friday cutoff, or NEWS_PROTOCOL
endpoints. Never places / remints / flattens. Does not APPLY a SHADOW gate.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .bars import (
    MULTI_SYMBOL_OPTIONAL,
    MULTI_SYMBOL_PRIORITY,
    challenge_search_dirs,
    challenge_tape_present,
    landed_challenge_symbols,
)
from .family import hard_off_family
from .fluid_gates import envelope_walls, fluid_gates
from .fluid_pipeline import may_auto_apply
from .host_events import TRAIL_EPS, last_stop_now, load_host_events, sl_differs
from .news_spine import attach_news, load_spines
from .process_lock import (
    PROVE_BARS_FLUID_LABEL,
    stamp_lock,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PACK = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "shadow.jsonl"
)
DEFAULT_DEALS = (
    REPO_ROOT / "judgment" / "astra" / "lab" / "challenge_shadow_20260917" / "deals_since_20260909.jsonl"
)
DEFAULT_RECEIPT = REPO_ROOT / "judgment" / "astra" / "lab" / "wires" / "SHADOW_UNLOCK_RECEIPT.json"

SHADOW_REMAIN = ("FLUID-HLD-005", "FLUID-HLD-008", "FLUID-NWS-005")
RESEARCH_ONLY = ("SEL-V4-002",)
ORGANISM_NOT_IN_FLUID_48 = ("SEL-V4-001", "SEL-V4-003", "SCH-V4-001", "SCH-V4-002")

# Paying FX that already fire on Challenge and are not house_hard_off.
FX_LAND_FIRST = ("EURUSD", "GBPUSD", "EURGBP", "USDJPY")
# Chair 2026-09-18 zip also landed this pair. No pack rows yet.
CHAIR_LANDED_EXTRA_FX = ("GBPJPY",)
HARD_OFF_DO_NOT_LAND_FIRST = ("US30", "UK100", "BTCUSD", "ETHUSD")


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def _fluid_inst(row: dict[str, Any], gate_id: str) -> dict[str, Any]:
    return (((row.get("compose") or {}).get("fluid") or {}).get("gates") or {}).get(gate_id) or {}


def _gate_pack_stats(rows: list[dict[str, Any]], gate_id: str) -> dict[str, Any]:
    values: list[Any] = []
    n_decidable = 0
    n_moved = 0
    for row in rows:
        inst = _fluid_inst(row, gate_id)
        if inst.get("decidable"):
            n_decidable += 1
            values.append(inst.get("shadow"))
        if inst.get("moved"):
            n_moved += 1
    distinct = {json.dumps(v, default=str) for v in values}
    return {
        "n": len(rows),
        "n_decidable": n_decidable,
        "n_moved": n_moved,
        "n_distinct": len(distinct),
        "vals": dict(Counter(json.dumps(v, default=str) for v in values)),
        "bars": dict(PROVE_BARS_FLUID_LABEL),
    }


def _honest_fill_forbidden(stats: dict[str, Any], *, need_both_poles: bool) -> dict[str, Any]:
    """A SHADOW field is fillable only when named Challenge state already exists."""
    bars = PROVE_BARS_FLUID_LABEL
    reasons: list[str] = []
    if stats["n_decidable"] < int(bars["min_decidable"]):
        reasons.append(
            f"decidable {stats['n_decidable']} < {bars['min_decidable']} — need Challenge-true named state"
        )
    if stats["n_moved"] < int(bars["min_non_default"]):
        reasons.append(
            f"non_default {stats['n_moved']} < {bars['min_non_default']} — label is constant/absent"
        )
    if stats["n_decidable"] >= int(bars["min_decidable"]) and stats["n_distinct"] < int(bars["min_distinct"]):
        reasons.append(
            f"distinct {stats['n_distinct']} < {bars['min_distinct']} — constant_on_this_tape"
        )
    if need_both_poles:
        poles = set(stats.get("vals") or {})
        if "true" not in poles or "false" not in poles:
            reasons.append("need both True and False named poles — do not invent the missing pole")
    return {
        "can_honestly_fill_from_existing_challenge_state": False,
        "invent_forbidden": True,
        "prove_blocked": True,
        "reasons": reasons,
    }


def _inventory_rows() -> dict[str, Any]:
    fluid = []
    for gate in fluid_gates():
        gid = str(gate.get("id") or "")
        fluid.append(
            {
                "id": gid,
                "family": gate.get("family"),
                "question": gate.get("question"),
                "primitive": gate.get("primitive"),
                "effect": gate.get("effect"),
                "chair": gate.get("chair"),
                "status": gate.get("status"),
                "research_only": bool(gate.get("research_only")),
                "cannot_refuse": bool(gate.get("cannot_refuse")),
                "may_auto_apply": may_auto_apply(gid),
                "draft_only": bool(gate.get("draft_only")),
            }
        )
    by_status = Counter(r["status"] for r in fluid)
    return {
        "n_fluid": len(fluid),
        "n_envelope": len(envelope_walls()),
        "by_status": dict(by_status),
        "applied_named": [r["id"] for r in fluid if r["status"] == "APPLIED_NAMED"],
        "proved_shadow": [r["id"] for r in fluid if r["status"] == "PROVED_SHADOW"],
        "shadow": [r["id"] for r in fluid if r["status"] == "SHADOW"],
        "research_only": [r["id"] for r in fluid if r["research_only"]],
        "gates": fluid,
        "envelope": [
            {"id": g.get("id"), "name": g.get("name"), "stays": g.get("stays"), "class": "envelope"}
            for g in envelope_walls()
        ],
    }


def _pack_surface(rows: list[dict[str, Any]]) -> dict[str, Any]:
    symbols = Counter()
    sufficient_by_symbol = Counter()
    families = Counter()
    kinds = Counter()
    sessions = Counter()
    weekdays = Counter()
    friday_rows: list[dict[str, Any]] = []
    friday_cutoff_n = 0
    n_suff = n_xau_suff = n_non_xau_suff = n_miss_m15 = n_spine_empty = 0
    a8 = Counter()
    sel = Counter()
    for row in rows:
        kinds[row.get("kind")] += 1
        state = row.get("state") or {}
        ident = state.get("identity") or {}
        news = state.get("news") or {}
        clock = state.get("clock") or {}
        sess = state.get("sessions") or {}
        comp = state.get("completeness") or {}
        feats = state.get("sleeve_features") or {}
        sym = str(ident.get("symbol") or "?")
        symbols[sym] += 1
        families[ident.get("family_class")] += 1
        sessions[sess.get("named")] += 1
        weekdays[clock.get("weekday_name")] += 1
        if news.get("spine_empty"):
            n_spine_empty += 1
        if not comp.get("timeframes_m15_h4"):
            n_miss_m15 += 1
        if comp.get("state_sufficient_for_live"):
            n_suff += 1
            sufficient_by_symbol[sym] += 1
            if sym == "XAUUSD":
                n_xau_suff += 1
            else:
                n_non_xau_suff += 1
        if clock.get("is_friday"):
            friday_rows.append(
                {
                    "as_of_utc": clock.get("as_of_utc"),
                    "utc_hour": sess.get("utc_hour"),
                    "named": sess.get("named"),
                    "kind": row.get("kind"),
                    "symbol": sym,
                    "ticket": row.get("ticket"),
                }
            )
            if sess.get("named") == "friday_cutoff":
                friday_cutoff_n += 1
        a8[(sym, feats.get("a8_source"), feats.get("a8_k_of_4_pass"))] += 1
        inst = _fluid_inst(row, "SEL-V4-002")
        sel[(sym, bool(inst.get("decidable")), inst.get("shadow"))] += 1
    return {
        "n": len(rows),
        "kinds": dict(kinds),
        "symbols": dict(symbols),
        "sufficient_by_symbol": dict(sufficient_by_symbol),
        "families": dict(families),
        "sessions": dict(sessions),
        "weekdays": dict(weekdays),
        "n_sufficient": n_suff,
        "n_xau_sufficient": n_xau_suff,
        "n_non_xau_sufficient": n_non_xau_suff,
        "n_missing_m15_h4": n_miss_m15,
        "n_news_empty": n_spine_empty,
        "friday_n": len(friday_rows),
        "friday_cutoff_n": friday_cutoff_n,
        "friday_rows": friday_rows,
        "a8_by_symbol": [
            {"symbol": s, "a8_source": src, "a8_k_of_4_pass": passed, "n": n}
            for (s, src, passed), n in a8.most_common()
        ],
        "sel_v4_002_by_symbol": [
            {"symbol": s, "decidable": dec, "shadow": shadow, "n": n}
            for (s, dec, shadow), n in sel.most_common()
        ],
    }


def _deal_trail(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"n": 0, "missing_file": True}
    deals = list(_iter_jsonl(path))
    both = same = differ = missing_orig = missing_final = 0
    diffs: list[dict[str, Any]] = []
    symbols = Counter()
    for deal in deals:
        symbols[deal.get("symbol")] += 1
        orig = deal.get("orig_sl")
        final = deal.get("final_sl")
        if orig in (None, ""):
            missing_orig += 1
        if final in (None, ""):
            missing_final += 1
        hit = sl_differs(orig, final)
        if hit is None:
            continue
        both += 1
        if hit:
            differ += 1
            diffs.append(
                {
                    "ticket": deal.get("ticket"),
                    "symbol": deal.get("symbol"),
                    "orig_sl": orig,
                    "final_sl": final,
                }
            )
        else:
            same += 1
    return {
        "n": len(deals),
        "n_open": sum(1 for d in deals if d.get("still_open")),
        "n_closed": sum(1 for d in deals if not d.get("still_open")),
        "symbols": dict(symbols),
        "n_orig_and_final_named": both,
        "n_same_within_eps": same,
        "n_differ_gt_eps": differ,
        "n_missing_orig_sl": missing_orig,
        "n_missing_final_sl": missing_final,
        "named_trails": diffs,
        "trail_eps": TRAIL_EPS,
    }


def _event_trail() -> dict[str, Any]:
    events = load_host_events()
    moves = [e for e in events if e.get("event") == "f5_stop_move"]
    tickets = Counter(str(e.get("ticket") or "") for e in moves)
    deal_rows = {}
    deal_path = DEFAULT_DEALS
    if deal_path.is_file():
        deal_rows = {str(d.get("ticket")): d for d in _iter_jsonl(deal_path)}
    n_true = n_false = n_none = 0
    news_inv = Counter()
    for event in events:
        ev = str(event.get("event") or "")
        if ev in {"news_t15_pending_cancel", "news_t60_expiry_reeval"}:
            news_inv[event.get("inventory_status")] += 1
    for ticket in tickets:
        last = last_stop_now(events, ticket)
        orig = (deal_rows.get(ticket) or {}).get("orig_sl")
        hit = sl_differs(last, orig)
        if hit is True:
            n_true += 1
        elif hit is False:
            n_false += 1
        else:
            n_none += 1
    return {
        "n_events": len(events),
        "n_f5_stop_move": len(moves),
        "n_stop_move_tickets": len(tickets),
        "stop_move_tickets": dict(tickets),
        "n_trail_true_vs_deal_orig": n_true,
        "n_trail_false_vs_deal_orig": n_false,
        "n_trail_unassembled_vs_deal_orig": n_none,
        "host_news_inventory_status": dict(news_inv),
        "host_news_never_read": news_inv.get("READ", 0) == 0,
    }


def _multi_instrument() -> dict[str, Any]:
    landed = landed_challenge_symbols()
    present = {
        sym: challenge_tape_present(sym)
        for sym in ("XAUUSD",) + FX_LAND_FIRST + CHAIR_LANDED_EXTRA_FX + HARD_OFF_DO_NOT_LAND_FIRST
    }
    search = []
    for directory in challenge_search_dirs():
        m15 = sorted(p.name for p in directory.glob("*_M15.csv")) if directory.is_dir() else []
        search.append({"dir": str(directory), "exists": directory.is_dir(), "m15": m15})
    return {
        "landed_symbols": landed,
        "tape_present": present,
        "search_dirs": search,
        "fx_land_first": list(FX_LAND_FIRST),
        "chair_landed_extra_fx": list(CHAIR_LANDED_EXTRA_FX),
        "hard_off_do_not_land_first": list(HARD_OFF_DO_NOT_LAND_FIRST),
        "loader_priority": list(MULTI_SYMBOL_PRIORITY),
        "loader_optional": list(MULTI_SYMBOL_OPTIONAL),
        "april_historical_is_not_challenge_true": True,
        "d1_optional_for_non_xau": True,
        "never_substitute_xau_for_other_pair": True,
        "a8_formulas_are_metals_on_surface": True,
        "metals_on_surface": ["XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD"],
        "flow_wire_is_xau_named": "f5_xau_flow_alignment_size_tilt",
        "sel_v4_002_research_only": True,
        "do_not_edit_selector_v4": True,
        "sch_v4_not_in_fluid_48": list(ORGANISM_NOT_IN_FLUID_48),
        "hard_off_family_by_symbol": {
            "US30": hard_off_family("mx_us30", "US30"),
            "BTCUSD": hard_off_family("kz_london_cry", "BTCUSD"),
            "ETHUSD": hard_off_family("orb_crypto_lo", "ETHUSD"),
            "UK100": hard_off_family("idxrev", "UK100"),
        },
    }


def measure_shadow_unlock(
    *,
    pack_path: Path | None = None,
    deals_path: Path | None = None,
) -> dict[str, Any]:
    """Measure remaining SHADOW axes. Never invents a pass."""
    pack = pack_path or DEFAULT_PACK
    deals = deals_path or DEFAULT_DEALS
    rows = list(_iter_jsonl(pack)) if pack.is_file() else []
    inventory = _inventory_rows()
    surface = _pack_surface(rows) if rows else {}
    deal_trail = _deal_trail(deals)
    event_trail = _event_trail()
    multi = _multi_instrument()

    trail_stats = _gate_pack_stats(rows, "FLUID-HLD-005") if rows else {}
    friday_stats = _gate_pack_stats(rows, "FLUID-HLD-008") if rows else {}
    spine_stats = _gate_pack_stats(rows, "FLUID-NWS-005") if rows else {}
    sel_stats = _gate_pack_stats(rows, "SEL-V4-002") if rows else {}

    spines = load_spines()
    # Confirm no deal as-of is honestly empty on the live spine.
    empty_deal_asofs = []
    if deals.is_file():
        for deal in _iter_jsonl(deals):
            raw = deal.get("open_time_utc")
            if not raw:
                continue
            try:
                dt = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            except ValueError:
                continue
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            news = attach_news(dt, spines=spines, symbol=str(deal.get("symbol") or "XAUUSD"))
            if news["spine_empty"]:
                empty_deal_asofs.append(
                    {"ticket": deal.get("ticket"), "as_of_utc": dt.strftime("%Y-%m-%dT%H:%M:%SZ")}
                )

    shadow_axes = {
        "FLUID-HLD-005": {
            "question": "trail_vs_orig",
            "family": "hold_exit",
            "effect": "label",
            "chair": "LABEL",
            "status": "SHADOW",
            "missing_field": "extra.final_sl vs geometry.stop differing by TRAIL_EPS 0.05",
            "where_it_would_come_from": (
                "host events.jsonl event=f5_stop_move.stop_now (last per ticket) "
                "or deals.final_sl. named_final_sl prefers the deal column."
            ),
            "named_challenge_state_needed": (
                "≥20 tickets with both orig and a named final, and both True and False poles. "
                "Monitor jitter ~0.005 is not a trail. broker_mutation=False reprints are not a trail."
            ),
            "pack": trail_stats,
            "deal_column": {
                "n_missing_final_sl": deal_trail.get("n_missing_final_sl"),
                "n_differ_gt_eps": deal_trail.get("n_differ_gt_eps"),
                "n_orig_and_final_named": deal_trail.get("n_orig_and_final_named"),
            },
            "event_column": {
                "n_stop_move_tickets": event_trail.get("n_stop_move_tickets"),
                "n_trail_true_vs_deal_orig": event_trail.get("n_trail_true_vs_deal_orig"),
                "n_trail_false_vs_deal_orig": event_trail.get("n_trail_false_vs_deal_orig"),
            },
            **_honest_fill_forbidden(trail_stats, need_both_poles=True),
        },
        "FLUID-HLD-008": {
            "question": "friday_cutoff_label",
            "family": "hold_exit",
            "effect": "label",
            "chair": "LABEL",
            "status": "SHADOW",
            "missing_field": "clock.is_friday AND sessions.named == friday_cutoff (utc_hour >= 16)",
            "where_it_would_come_from": (
                "gold_state._session_named(utc_hour, is_friday) on a Challenge as-of. "
                "Writer clock ENV-DEAD stays the integer. Do not rename to close_session."
            ),
            "named_challenge_state_needed": (
                "A Friday Challenge as-of at utc>=16 so sessions.named is friday_cutoff. "
                "Friday 01–06Z asia on 2026-09-11 is not that state."
            ),
            "pack": friday_stats,
            "friday_rows_on_pack": surface.get("friday_rows") or [],
            "friday_cutoff_n": surface.get("friday_cutoff_n") or 0,
            **_honest_fill_forbidden(friday_stats, need_both_poles=True),
        },
        "FLUID-NWS-005": {
            "question": "spine_empty_honesty",
            "family": "news_window",
            "effect": "label",
            "chair": "LABEL",
            "status": "SHADOW",
            "missing_field": "news.spine_empty True on a Challenge as-of (no spine event within 10d)",
            "where_it_would_come_from": (
                "news_spine.attach_news covering window. Host f5_high_calendar is the Challenge axis. "
                "Host news_t15/t60 inventory_status unread is calendar_honest, not spine_empty."
            ),
            "named_challenge_state_needed": (
                "An as-of outside 10d of any spine event after the host writer actually READS. "
                "Do not invent NEWS_PROTOCOL. Do not overwrite June data/news_calendar.json. "
                "Do not invert unread → empty."
            ),
            "pack": spine_stats,
            "n_news_empty_on_pack": surface.get("n_news_empty"),
            "n_deal_asofs_spine_empty": len(empty_deal_asofs),
            "host_news_never_read": event_trail.get("host_news_never_read"),
            **_honest_fill_forbidden(spine_stats, need_both_poles=True),
        },
    }

    return {
        "schema": "gtos.judgment.shadow_unlock.v0",
        **stamp_lock(),
        "measured_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pack_path": str(pack.relative_to(REPO_ROOT)) if pack.is_relative_to(REPO_ROOT) else str(pack),
        "inventory": {
            "n_fluid": inventory["n_fluid"],
            "n_envelope": inventory["n_envelope"],
            "by_status": inventory["by_status"],
            "applied_named": inventory["applied_named"],
            "proved_shadow": inventory["proved_shadow"],
            "shadow": inventory["shadow"],
            "research_only": inventory["research_only"],
            "gates": inventory["gates"],
            "envelope": inventory["envelope"],
        },
        "research_only": {
            "SEL-V4-002": {
                "status": "PROVED_SHADOW",
                "research_only": True,
                "may_auto_apply": False,
                "do_not_import_from": "src/components/selector_v4.py",
                "bound": True,
                "next": "research_only_no_apply",
                "pack": sel_stats,
                "note": (
                    "Observer lives in src/judgment/a1_log.py. "
                    "V4 holds no live authority. Do not edit selector_v4.py (R2 / H1)."
                ),
            }
        },
        "organism_not_in_fluid_48": {
            "ids": list(ORGANISM_NOT_IN_FLUID_48),
            "note": (
                "SEL-V4-001 is the enabled-integer. SEL-V4-003 is runtime_effect after merge. "
                "SCH-V4-001/002 are scheduler window-winner questions. They compute; they have "
                "no live authority and are not fluid APPLY targets."
            ),
        },
        "shadow_axes": shadow_axes,
        "pack": surface,
        "deals": deal_trail,
        "events": event_trail,
        "multi_instrument": multi,
        "any_honest_fill": False,
        "filled_this_pass": [],
        "never_place": True,
        "no_news_protocol_invented": True,
        "note": (
            "No SHADOW field can be honestly filled from this Challenge tape. "
            "Land FX M15+H4 next. Do not invent Friday / trail / empty spine."
        ),
    }


def write_receipt(payload: dict[str, Any] | None = None, *, dest: Path | None = None) -> dict[str, Any]:
    receipt = payload or measure_shadow_unlock()
    out = dest or DEFAULT_RECEIPT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, default=str) + "\n", encoding="utf-8")
    receipt["out"] = str(out)
    return receipt
