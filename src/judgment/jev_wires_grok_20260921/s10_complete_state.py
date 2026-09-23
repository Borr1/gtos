"""COMPLETE_STATE v0 assembler — DRAFT under session OUT only.

Land target (Chair APPLY later, not this session):
  src/judgment/complete_state.py

Never broker place / order_send. apply=false. place=false in this draft.
Fail-closed if full_state_dark or Jev dark.
Never invent NEWS_PROTOCOL, ATR, regime, DXY, yields, ON_SURFACE.
Never mutate live_armed_set.json.
Never flip GTOS_JEV_SLEEVE_SELECT_APPLY (global).
Owner 2026-09-21: eternal never_place is WRONG; this object carries
place_context so a later hist-proved Choice may return PLACE|STAND|DELAY.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Mapping, Optional, Sequence

SCHEMA = "gtos.jev.complete_state.v0"
PENDING = "PENDING"
STATE_MISSING = "STATE_MISSING"
SESSION_BUCKETS = ("asia", "london", "overlap", "ny", "off")

# Completeness keys counted into n_incomplete. PENDING / None / "" increment.
INCOMPLETE_KEYS = (
    "symbol",
    "broker_symbol",
    "session_bucket",
    "alive_sleeves",
    "conflict_set",
    "regime_tag",
    "conf_band",
    "session_fit",
    "phi",
    "cost.spread_r",
    "occupancy.n_open_book",
    "account.login",
    "remint.orig_stops_today",
    "news_join",
    "place_context.writer_ready",
    "lens.atr_source",
)

# Dark if this many of INCOMPLETE_KEYS are empty. Policy C used 4 voters and
# n>=3 trim; COMPLETE_STATE uses a wider set so we are not cheap.
DARK_THRESHOLD_ENV = "GTOS_JEV_COMPLETE_STATE_DARK_THRESHOLD"
DARK_THRESHOLD_DEFAULT = 8

COMPLETE_STATE_ENV = "GTOS_JEV_COMPLETE_STATE"
FAIL_CLOSED_ENV = "GTOS_JEV_COMPLETE_STATE_FAIL_CLOSED"
MAX_CALLS_DRAFT = "500000"  # current jev_client DEFAULT_MAX_CALLS=200

CHALLENGE_LOGIN = "0"
CHALLENGE_NS = "operator"

HARD_OFF_FAMILIES = ("bleed", "orb_crypto", "idxrev", "xa_huge", "mx_us30")

F5_AFFINITY_KEEP_PRIORS: dict[str, tuple[str, ...]] = {
    "EURUSD": ("asian_fade", "sub_mid_dn_re_proxy_eurusd_short_m15_atr"),
    "XAUUSD": (
        "dsp_spring_close_on_20low_through_the_box",
        "dsp_three_fresh_lower_lows",
        "dsp_expanding_up_staircase",
    ),
    "GBPJPY": ("vss_fxcross_london_up_low", "sub_mid_dn_revert"),
    "XAGUSD": ("sub_xvol_pullback", "metals_core", "metal_session_reversion"),
    "NZDUSD": ("sub_mid_dn_re_proxy_nzdusd_short_m15_atr",),
}


def _env_on(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def complete_state_enabled() -> bool:
    return _env_on(COMPLETE_STATE_ENV, default=True)  # assemble always; APPLY stays consumer flags


def fail_closed_enabled() -> bool:
    return _env_on(FAIL_CLOSED_ENV, default=True)


def dark_threshold() -> int:
    raw = (os.environ.get(DARK_THRESHOLD_ENV) or "").strip()
    try:
        return max(1, int(raw)) if raw else DARK_THRESHOLD_DEFAULT
    except ValueError:
        return DARK_THRESHOLD_DEFAULT


def _incomplete(v: Any) -> bool:
    if v is None:
        return True
    if v in (PENDING, "PENDING_SHADOW", STATE_MISSING, ""):
        return True
    if isinstance(v, (list, dict, tuple)) and len(v) == 0:
        return True
    return False


def _nested_get(row: Mapping[str, Any], path: str) -> Any:
    cur: Any = row
    for part in path.split("."):
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(part)
    return cur


def session_bucket_from_clock(*, utc_hour: int | None, is_friday: bool = False) -> str:
    """FIRST-CLASS overlap. gold_state.sessions.named currently folds 12-16z into ny."""
    if utc_hour is None:
        return PENDING
    if is_friday and utc_hour >= 16:
        return "off"
    if utc_hour >= 21 or utc_hour == 0:
        return "off"
    if 0 < utc_hour < 7:
        return "asia"
    if 7 <= utc_hour < 12:
        return "london"
    if 12 <= utc_hour < 16:
        return "overlap"
    if 16 <= utc_hour < 21:
        return "ny"
    return "off"


def _hard_off_hit(sleeve: str | None, symbol: str | None) -> str | None:
    sl = (sleeve or "").lower()
    sy = (symbol or "").upper()
    if sy.startswith("US30") or "mx_us30" in sl:
        return "chair_mx_us30_hard_off"
    if "idxrev" in sl:
        return "chair_g_index_hard_off"
    if sl.startswith("xa_huge"):
        return "chair_xa_huge_hard_off"
    if sl.startswith("orb_") or "orb_crypto" in sl:
        return "chair_orb_crypto_hard_off"
    if "bleed" in sl:
        return "chair_bleed_hard_off"
    for fam in HARD_OFF_FAMILIES:
        if fam in sl:
            return "chair_hard_off_family"
    return None


def compose_conflict_set(
    symbol: str,
    alive: Sequence[str],
    *,
    state: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Named conflict cells only. Empty list is honest (not invented)."""
    sym = str(symbol or "").upper()
    tags = [str(t) for t in alive]
    out: list[dict[str, Any]] = []

    if sym in {"XAUUSD", "XAU"}:
        tf = [t for t in tags if "three_fresh" in t.lower()]
        sp = [t for t in tags if "spring" in t.lower()]
        if tf and sp:
            out.append(
                {
                    "a": tf[0],
                    "b": sp[0],
                    "relation": "TRUE_CONFLICT",
                    "side": None,
                    "scope": "XAU_conflict_three_fresh_x_spring",
                    "kind": "TRUE_CONFLICT",
                    "hist_cite": "JEV_SLEEVE_SELECT_HIST_PROVE_V2 / SCOPED_XAU_APPLY_RECEIPT",
                    "sumR_select": 235.3602,
                    "sumR_keep_all": -74.7197,
                    "n_conflicts": 2353,
                    "lens": "Module_ATR",
                }
            )

    if sym == "GBPJPY":
        vss = [t for t in tags if "vss" in t.lower()]
        sub = [
            t
            for t in tags
            if "sub_mid" in t.lower() and "eurusd" not in t.lower() and "package" not in t.lower()
        ]
        if vss and sub:
            out.append(
                {
                    "a": vss[0],
                    "b": sub[0],
                    "relation": "SIDE_AWARE",
                    "side": (state or {}).get("side"),
                    "scope": "GBPJPY_conflict_vss_x_sub_mid",
                    "kind": "SIDE_AWARE",
                    "hist_cite": "GBPJPY_VSS_x_SUBMID_CONFLICT_HIST_PROVE_20260920",
                    "note": "phi-ranked D_FULL ytd_2026 FAIL; hold_last_2y PASS; full FAIL. Size-trim 692/692 was asian_pkgb_incomplete_voters — starve, not true trim.",
                }
            )

    if sym == "EURUSD":
        af = [t for t in tags if "asian_fade" in t.lower()]
        pb = [
            t
            for t in tags
            if "sub_mid_dn_re_proxy_eurusd" in t.lower() or "package_b" in t.lower()
        ]
        if af and pb:
            out.append(
                {
                    "a": af[0],
                    "b": pb[0],
                    "relation": "KEEP_ALL_DUAL_POS",
                    "side": None,
                    "scope": "EURUSD_asian_fade_x_package_b_keep_all",
                    "kind": "KEEP_ALL_DUAL_POS",
                    "never_alias": "sub_mid_dn_revert",
                }
            )
    return out


def news_join_honest(news: Mapping[str, Any] | None) -> Any:
    """Empty spine is STATE_MISSING, not 'no HIGH'. Never invent endpoints."""
    if not news:
        return STATE_MISSING
    if news.get("spine_empty") is True:
        return STATE_MISSING
    if not news.get("events"):
        return STATE_MISSING
    return {
        "spine_empty": False,
        "n_events": len(news.get("events") or []),
        "high_in_f5_window": news.get("high_in_f5_window"),
        "minutes_to_nearest_high": news.get("minutes_to_nearest_high"),
        "source": news.get("source") or "news_spine",
        "invented": False,
    }


def lens_honesty(*, blotter_row: Mapping[str, Any] | None = None, geometry: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Module_ATR honesty. Do not invent ATR. Dig_3R never merged."""
    geo = geometry or {}
    row = blotter_row or {}
    atr = row.get("atr")
    if atr is None:
        atr = geo.get("atr14")
    source = None
    if row.get("atr") is not None:
        source = "module_atr_blotter"
    elif geo.get("atr14") is not None:
        source = "geometry.atr14"
    else:
        source = STATE_MISSING
    fill_model = row.get("fill_model")
    return {
        "name": row.get("lens") or "Module_ATR",
        "atr": atr,
        "atr_source": source,
        "invented": False,
        "fill_model": fill_model,
        "never_merge_dig3r": True,
        "note": (
            "blotter fill_model=geometry_proxy_ohlc_touch_module_ATR_exit_NOT_broker_NOT_module_exact "
            "when present; Challenge R is a separate universe"
        ),
    }


def _count_incomplete(packed: Mapping[str, Any]) -> int:
    n = 0
    for key in INCOMPLETE_KEYS:
        if _incomplete(_nested_get(packed, key)):
            n += 1
    return n


def assemble_complete_state_v0(
    *,
    symbol: str,
    broker_symbol: str | None = None,
    as_of_utc: datetime | None = None,
    sleeve: str | None = None,
    side: str | None = None,
    gold_or_symbol_state: Mapping[str, Any] | None = None,
    alive_pack: Mapping[str, Any] | None = None,
    phi_prior: Mapping[str, Any] | None = None,
    occupancy: Mapping[str, Any] | None = None,
    cost: Mapping[str, Any] | None = None,
    account: Mapping[str, Any] | None = None,
    remint: Mapping[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
    place_context: Mapping[str, Any] | None = None,
    regime_tag: Any = PENDING,
    conf_band: Any = PENDING,
    session_fit: Any = PENDING,
    blotter_row: Mapping[str, Any] | None = None,
    writer_ready: bool | None = None,
    authority: bool | None = None,
    last_refusal_class: str | None = None,
    ticket_draft_fp: str | None = None,
) -> dict[str, Any]:
    """Build one COMPLETE_STATE object. Missing stays visible. Never invents."""
    as_of = as_of_utc or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    sym = str(symbol or "").upper()
    gold = dict(gold_or_symbol_state or {})
    identity = dict(gold.get("identity") or {})
    sessions = dict(gold.get("sessions") or {})
    clock = dict(gold.get("clock") or {})

    utc_hour = sessions.get("utc_hour")
    if utc_hour is None:
        utc_hour = as_of.hour
    is_friday = bool(clock.get("is_friday") or as_of.weekday() == 4)
    bucket = session_bucket_from_clock(utc_hour=int(utc_hour) if utc_hour is not None else None, is_friday=is_friday)

    pack = dict(alive_pack or {})
    alive = list(pack.get("alive_sleeves_for_symbol") or pack.get("alive_sleeves") or [])
    armed_source = pack.get("armed_source") or "unassembled"
    compose_fail = bool(pack.get("fail_closed"))
    for prior in F5_AFFINITY_KEEP_PRIORS.get(sym, ()):
        if prior not in alive:
            alive.append(prior)
    alive = sorted(set(str(t) for t in alive))

    # Package B never aliases live sub_mid_dn_revert except GBPJPY KEEP prior
    menu: list[dict[str, Any]] = []
    phi_map: dict[str, float] = {}
    prior = dict(phi_prior or {})
    for tag in alive:
        if tag == "sub_mid_dn_revert" and tag not in F5_AFFINITY_KEEP_PRIORS.get(sym, ()):
            continue
        phi_val = 0.0
        for row in prior.get("candidates") or []:
            if not isinstance(row, Mapping):
                continue
            if str(row.get("instrument") or "").upper() not in {sym, ""}:
                continue
            if str(row.get("tag") or "").lower() in tag.lower() or str(row.get("sleeve") or "").lower() in tag.lower():
                cap = row.get("capability") if isinstance(row.get("capability"), Mapping) else {}
                try:
                    phi_val = float(cap.get("phi", row.get("phi", 0.0)) or 0.0)
                except (TypeError, ValueError):
                    phi_val = 0.0
        phi_map[tag] = phi_val
        menu.append(
            {
                "tag": tag,
                "phi": phi_val,
                "keep_prior": tag in F5_AFFINITY_KEEP_PRIORS.get(sym, ()),
                "affinity": True,
                "escape": False,
            }
        )
    for esc in ("HOLD", "ABSTAIN", "ESCALATE_CHAIR", "BLOCKED"):
        menu.append({"tag": esc, "phi": None, "keep_prior": False, "affinity": False, "escape": True})

    conflicts = compose_conflict_set(sym, alive, state={"side": side or identity.get("side")})
    news_block = news_join_honest(news if news is not None else gold.get("news"))
    cost_block = dict(cost or gold.get("cost") or {})
    occ_block = dict(occupancy or gold.get("occupancy") or {})
    acct = dict(account or {})
    if not acct.get("login"):
        acct.setdefault("login", CHALLENGE_LOGIN)
    if not acct.get("ns"):
        acct.setdefault("ns", CHALLENGE_NS)
    rem = dict(remint or {})
    rem.setdefault("orig_stops_today", occ_block.get("same_sleeve_orig_stops_utc_day"))
    rem.setdefault("two_stop_armed", occ_block.get("two_stop_exhausted"))
    rem.setdefault("minutes_since_exit", occ_block.get("minutes_since_flat"))
    rem.setdefault("last_exit_class", PENDING)

    sleeve_now = sleeve or identity.get("sleeve")
    hard_hit = _hard_off_hit(sleeve_now, sym)

    place = dict(place_context or {})
    place.setdefault("writer_ready", writer_ready)
    place.setdefault("authority", authority)
    place.setdefault("last_refusal_class", last_refusal_class or "none")
    place.setdefault("ticket_draft_fp", ticket_draft_fp)
    # Owner override: not eternal never_place. Default-off until hist-prove.
    place.setdefault("place_allowed_when_proved", True)
    place.setdefault("default_until_prove", True)
    place.setdefault("session_place", False)

    lens = lens_honesty(blotter_row=blotter_row, geometry=gold.get("geometry"))

    selected = identity.get("sleeve") or sleeve
    if selected and selected not in alive:
        selected = None

    broker = broker_symbol or identity.get("broker_symbol") or sym
    if _incomplete(broker):
        broker = STATE_MISSING

    packed: dict[str, Any] = {
        "schema": SCHEMA,
        "symbol": sym or STATE_MISSING,
        "broker_symbol": broker,
        "session_day": as_of.date().isoformat(),
        "decision_bar_iso": identity.get("decision_bar_iso") or as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "session_bucket": bucket,
        "alive_sleeves": alive,
        "alive_menu": menu,
        "selected_sleeve_candidate": selected,
        "conflict_set": conflicts,
        "regime_tag": regime_tag if regime_tag not in (None, "", "regime_unknown") else PENDING,
        "conf_band": conf_band if conf_band not in (None, "") else PENDING,
        "session_fit": session_fit if session_fit not in (None, "") else PENDING,
        "phi": (max(phi_map.values()) if phi_map else None),
        "phi_by_sleeve": phi_map,
        "cost": {
            "spread_r": cost_block.get("spread_r") if cost_block.get("spread_r") is not None else cost_block.get("spread_r_of_stop"),
            "total_cost_r": cost_block.get("cost_r") or cost_block.get("total_cost_r"),
            "commission_r": cost_block.get("commission_r"),
            "max_total_cost_r": cost_block.get("max_total_cost_r") or 0.10,
            "source": cost_block.get("source") or ("unassembled" if not cost_block else "host"),
        },
        "occupancy": {
            "sleeve_holds_symbol": occ_block.get("symbol_open"),
            "broker_open_symbols": occ_block.get("broker_open_symbols"),
            "same_cycle_placed": occ_block.get("same_cycle_placed"),
            "n_open_book": occ_block.get("n_open_book"),
            "already_placed_today": occ_block.get("already_placed_today"),
            "isolated_reentry_legal": occ_block.get("isolated_reentry_legal"),
            "minutes_since_flat": occ_block.get("minutes_since_flat"),
            "occupancy_source": occ_block.get("occupancy_source") or "unassembled",
        },
        "account": {
            "login": acct.get("login"),
            "ns": acct.get("ns"),
            "equity_r": acct.get("equity_r"),
            "dd_wall_r": acct.get("dd_wall_r"),
            "soft_daily_stop": acct.get("soft_daily_stop"),
        },
        "hard_off_hit": hard_hit,
        "remint": rem,
        "news_join": news_block,
        "place_context": place,
        "lens": lens,
        "armed_source": armed_source,
        "affinity": {
            "symbol": sym,
            "keep_priors": list(F5_AFFINITY_KEEP_PRIORS.get(sym, ())),
            "held": True,
        },
        "compose_fail_closed": compose_fail,
        "apply": False,
        "place": False,
        "never_invent_news_protocol": True,
        "never_invent_atr": True,
        "never_merge_dig3r": True,
        "global_sleeve_select_apply": 0,
    }

    n_incomplete = _count_incomplete(packed)
    geometry_alone = bool(gold.get("geometry")) and not gold.get("timeframes")
    full_dark = bool(
        compose_fail
        or packed["symbol"] in (STATE_MISSING, "")
        or (not alive and not F5_AFFINITY_KEEP_PRIORS.get(sym))
        or n_incomplete >= dark_threshold()
        or (geometry_alone and packed["regime_tag"] == PENDING and armed_source != "research_armed_tags")
    )
    packed["n_incomplete"] = n_incomplete
    packed["full_state_dark"] = full_dark
    packed["fail_closed"] = bool(fail_closed_enabled() and full_dark)
    return packed


def fail_closed_choice(state: Mapping[str, Any] | None, *, jev_ok: bool | None = None) -> dict[str, Any]:
    """Envelope + fail-closed. Jev dark or full_state_dark → A_STAND_DOWN. Never place."""
    if not state:
        return {
            "Choice": None,
            "reason": STATE_MISSING,
            "skip": True,
            "refuse": False,
            "place": False,
            "apply": False,
        }
    if state.get("full_state_dark") or state.get("fail_closed"):
        return {
            "Choice": "A_STAND_DOWN",
            "reason": "full_state_dark",
            "skip": False,
            "refuse": True,
            "place": False,
            "apply": _env_on("GTOS_JEV_POLICY_C_APPLY", default=False),
        }
    if jev_ok is False:
        return {
            "Choice": "A_STAND_DOWN",
            "reason": "jev_dark",
            "skip": False,
            "refuse": True,
            "place": False,
            "apply": False,
            "note": "fail-closed if Jev dark — do not silently pass D_FULL",
        }
    return {
        "Choice": None,
        "reason": "state_present_ask_jev",
        "skip": False,
        "refuse": False,
        "place": False,
        "apply": False,
    }


def evaluate_over_complete_state(
    state: Mapping[str, Any],
    *,
    timeout_s: float = 8.0,
) -> dict[str, Any]:
    """POST jev_client.evaluate(COMPLETE_STATE). Draft only — no live APPLY.

    Chair may later splice this in front of every Choice/Score/Noul site.
    """
    closed = fail_closed_choice(state)
    if closed.get("refuse") or closed.get("skip"):
        return {**closed, "answers": {}, "jev": {"ok": False, "skipped": closed.get("reason")}}
    try:
        from src.judgment.jev_client import evaluate  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return {
            "Choice": "A_STAND_DOWN",
            "reason": "jev_dark",
            "error": f"{type(exc).__name__}:{exc}",
            "answers": {},
            "place": False,
            "apply": False,
        }
    receipt = evaluate(dict(state), timeout_s=timeout_s)
    if not receipt.get("ok"):
        return fail_closed_choice(state, jev_ok=False) | {"jev": receipt, "answers": {}}
    return {
        "Choice": None,
        "reason": "jev_ok",
        "answers": receipt.get("answers") or {},
        "jev": {k: receipt.get(k) for k in ("ok", "model", "usage", "calls_used")},
        "place": False,
        "apply": False,
    }
