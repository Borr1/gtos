"""RATES / DXY / FUNDING typed assembly. Research-only.

Computes four Noul-shaped facts from *named* books:

  usd_impulse     — USD FX basket last-bar impulse (lab or Challenge)
  rates_impulse   — named yield impulse, else null
  funding_stress  — named TED/SOFR/funding, else null
  risk_on_off     — named index impulse; yes = risk_off

Never places. Never resizes. Never invents NEWS_PROTOCOL or X.
April historical is lab_only. Challenge-true requires challenge_shadow paths.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .bars import StampedBar, last_closed_at_or_before, normalize_symbol
from .named_sources import (
    CROSS_FX_SYMBOLS,
    DXY_ABSENT_REASON,
    DXY_REJECTED_REASON,
    FUNDING_ABSENT_REASON,
    ICE_DXY_HIGH,
    ICE_DXY_LOW,
    RISK_PROXY_SYMBOLS,
    USD_PROXY_SYMBOLS,
    YIELD_ABSENT_REASON,
    YIELD_PRICE_INVERSE,
    inspect_dxy_csv,
    named_source_inventory,
    usd_return_for_pair,
)
from .process_lock import stamp_lock

SCHEMA = "gtos.judgment.rates_dxy_funding.v0"
PACK_ID = "gtos.judgment.rdf_pack.v0"

NEVER = {
    "never_place": True,
    "never_remint": True,
    "never_flatten": True,
    "never_resize": True,
    "never_apply_size": True,
    "never_invent_news_protocol": True,
    "never_ingest_raw_x": True,
}

# Named house fractions. Desk impulse, not a size wire.
USD_IMPULSE_D1 = 0.0020
USD_IMPULSE_H4 = 0.0010
RISK_IMPULSE_D1 = 0.0040
RISK_IMPULSE_H4 = 0.0020
RATES_IMPULSE_D1 = 0.0015
DEFAULT_FUNDING_STRESS_THRESHOLD = 0.50
CHALLENGE_AS_OF = datetime(2026, 9, 17, 11, 0, tzinfo=timezone.utc)

_MAX_LAG = {
    "H4": timedelta(hours=36),
    "D1": timedelta(days=5),
}
CHALLENGE_NEEDLES = ("challenge_shadow", "challenge_shadow_bars")


def _as_of(as_of_utc: datetime) -> datetime:
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    return as_of.astimezone(timezone.utc)


def _paths_from_books(books: Mapping[str, Sequence[StampedBar]] | None) -> list[str]:
    out: list[str] = []
    for rows in (books or {}).values():
        for row in rows or []:
            path = getattr(row, "source_path", None)
            if path and path not in out:
                out.append(str(path))
    return out


def load_named_challenge_cross_books() -> dict[str, dict[str, list[StampedBar]]]:
    """Load landed Challenge FX/index books. Missing symbols stay absent."""
    from .bars import challenge_tape_present, load_challenge_books

    out: dict[str, dict[str, list[StampedBar]]] = {}
    for symbol in USD_PROXY_SYMBOLS + RISK_PROXY_SYMBOLS + CROSS_FX_SYMBOLS:
        if challenge_tape_present(symbol):
            out[symbol] = load_challenge_books(symbol)
    return out


def feed_class_for(paths: Sequence[str]) -> str:
    if not paths:
        return "unassembled"
    joined = " ".join(paths).replace("\\", "/")
    if any(needle in joined for needle in CHALLENGE_NEEDLES):
        return "challenge_true"
    if "sierra_ohlcv_roots" in joined or "ZN_CONTROL" in joined or "VIX_VXM" in joined:
        return "sierra_control"
    return "lab_or_fixture"


def _bar_return(
    rows: Sequence[StampedBar] | None,
    as_of: datetime,
    tf: str,
    *,
    n_bars: int = 1,
) -> dict[str, Any] | None:
    if not rows:
        return None
    idx = last_closed_at_or_before(list(rows), as_of)
    if idx is None or idx < n_bars:
        return None
    lag = as_of - rows[idx].utc
    if lag > _MAX_LAG.get(tf, timedelta(hours=12)):
        return None
    prev = float(rows[idx - n_bars].bar.c)
    last = float(rows[idx].bar.c)
    if prev <= 0:
        return None
    return {
        "ret": last / prev - 1.0,
        "last_close": last,
        "prev_close": prev,
        "last_utc": rows[idx].utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_path": rows[idx].source_path,
        "tf": tf,
    }


def _collect_pair_returns(
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    symbols: Sequence[str],
    as_of: datetime,
    *,
    as_usd: bool,
) -> tuple[list[dict[str, Any]], list[str]]:
    snaps: list[dict[str, Any]] = []
    paths: list[str] = []
    for symbol in symbols:
        books = (cross_books or {}).get(symbol) or {}
        d1 = _bar_return(books.get("d1"), as_of, "D1")
        h4 = _bar_return(books.get("h4"), as_of, "H4")
        if not d1 and not h4:
            continue
        raw = (d1 or {}).get("ret") if d1 else (h4 or {}).get("ret")
        signed = usd_return_for_pair(symbol, raw) if as_usd else raw
        h4_signed = usd_return_for_pair(symbol, (h4 or {}).get("ret")) if as_usd and h4 else (h4 or {}).get("ret")
        snaps.append(
            {
                "symbol": symbol,
                "d1": d1,
                "h4": h4,
                "signed_d1": usd_return_for_pair(symbol, (d1 or {}).get("ret")) if as_usd and d1 else (d1 or {}).get("ret"),
                "signed_h4": h4_signed,
                "signed": signed,
            }
        )
        paths.extend(_paths_from_books(books))
    return snaps, paths


def _mean(values: Sequence[float | None]) -> float | None:
    named = [v for v in values if v is not None]
    if not named:
        return None
    return sum(named) / len(named)


def _noul_block(
    *,
    name: str,
    value: bool | None,
    assembled: bool,
    feed_class: str,
    source: str,
    reason: str | None,
    source_paths: Sequence[str],
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    challenge_true = feed_class == "challenge_true" and assembled
    row = {
        "noul": name,
        "value": value,
        "assembled": assembled,
        "feed_class": feed_class,
        "challenge_true": challenge_true,
        "challenge_true_target": value if challenge_true else None,
        "lab_target": value if assembled else None,
        "source": source,
        "reason": reason,
        "source_paths": list(source_paths),
    }
    if extra:
        row.update(dict(extra))
    return row


def _usd_impulse_block(
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    snaps, paths = _collect_pair_returns(cross_books, USD_PROXY_SYMBOLS, as_of, as_usd=True)
    feed = feed_class_for(paths)
    d1_mean = _mean([s.get("signed_d1") for s in snaps])
    h4_mean = _mean([s.get("signed_h4") for s in snaps])
    assembled = d1_mean is not None or h4_mean is not None
    stance = "unassembled"
    value: bool | None = None
    reason = None
    if assembled:
        triggered = False
        if d1_mean is not None and d1_mean >= USD_IMPULSE_D1:
            triggered = True
        if h4_mean is not None and h4_mean >= USD_IMPULSE_H4:
            triggered = True
        value = triggered
        if d1_mean is not None:
            lead, band = d1_mean, USD_IMPULSE_D1
        else:
            lead, band = h4_mean, USD_IMPULSE_H4
        if lead is None:
            stance = "unassembled"
        elif lead >= band:
            stance = "stronger"
        elif lead <= -band:
            stance = "weaker"
        else:
            stance = "flat"
        if feed != "challenge_true":
            reason = "lab_or_fixture_not_challenge_true"
    else:
        reason = "no_named_usd_fx_books_or_stale_vs_as_of"
        feed = "unassembled"
    return _noul_block(
        name="usd_impulse",
        value=value,
        assembled=assembled,
        feed_class=feed,
        source="usd_fx_basket" if assembled else "unassembled",
        reason=reason,
        source_paths=paths,
        extra={
            "stance": stance,
            "present": [s["symbol"] for s in snaps],
            "snaps": snaps,
            "mean_usd_d1": None if d1_mean is None else round(d1_mean, 6),
            "mean_usd_h4": None if h4_mean is None else round(h4_mean, 6),
            "threshold_d1": USD_IMPULSE_D1,
            "threshold_h4": USD_IMPULSE_H4,
            "dxy_used": False,
        },
    )


def _risk_block(
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    snaps, paths = _collect_pair_returns(cross_books, RISK_PROXY_SYMBOLS, as_of, as_usd=False)
    feed = feed_class_for(paths)
    d1_mean = _mean([s.get("signed_d1") for s in snaps])
    h4_mean = _mean([s.get("signed_h4") for s in snaps])
    have_print = d1_mean is not None or h4_mean is not None
    stance = "unassembled"
    value: bool | None = None
    reason = None
    if have_print:
        if d1_mean is not None:
            lead, band = d1_mean, RISK_IMPULSE_D1
        else:
            lead, band = h4_mean, RISK_IMPULSE_H4
        if lead <= -band:
            stance = "risk_off"
            value = True
        elif lead >= band:
            stance = "risk_on"
            value = False
        else:
            stance = "mixed"
            value = None
        if feed != "challenge_true":
            reason = "lab_or_fixture_not_challenge_true"
    else:
        reason = "no_named_index_books_or_stale_vs_as_of"
        feed = "unassembled"
    return _noul_block(
        name="risk_on_off",
        value=value,
        assembled=have_print and stance in {"risk_on", "risk_off"},
        feed_class=feed if have_print else "unassembled",
        source="named_index_tapes" if snaps else "unassembled",
        reason=reason,
        source_paths=paths,
        extra={
            "stance": stance,
            "yes_event": "risk_off",
            "present": [s["symbol"] for s in snaps],
            "snaps": snaps,
            "mean_d1": None if d1_mean is None else round(d1_mean, 6),
            "mean_h4": None if h4_mean is None else round(h4_mean, 6),
            "threshold_d1": RISK_IMPULSE_D1,
            "threshold_h4": RISK_IMPULSE_H4,
            "vix_used": False,
        },
    )


def _rates_impulse_block(
    yield_books: Mapping[str, Mapping[str, list[StampedBar]]] | None,
    as_of: datetime,
) -> dict[str, Any]:
    if not yield_books:
        return _noul_block(
            name="rates_impulse",
            value=None,
            assembled=False,
            feed_class="unassembled",
            source="unassembled",
            reason=YIELD_ABSENT_REASON,
            source_paths=[],
            extra={
                "stance": "unassembled",
                "named_yield": None,
                "sierra_zn": "control_only_not_used_as_rates_print",
                "usd_fx_is_not_a_yield": True,
                "threshold_d1": RATES_IMPULSE_D1,
            },
        )
    snaps: list[dict[str, Any]] = []
    paths: list[str] = []
    signed_vals: list[float] = []
    used = None
    for symbol, books in yield_books.items():
        d1 = _bar_return((books or {}).get("d1"), as_of, "D1")
        if not d1:
            continue
        raw = d1["ret"]
        signed = -raw if normalize_symbol(symbol) in YIELD_PRICE_INVERSE else raw
        snaps.append({"symbol": symbol, "d1": d1, "rates_signed": signed})
        paths.extend(_paths_from_books(books))
        signed_vals.append(signed)
        used = symbol
    feed = feed_class_for(paths)
    if feed == "sierra_control":
        # Present control tape is not a Challenge-true rates print.
        return _noul_block(
            name="rates_impulse",
            value=None,
            assembled=False,
            feed_class="sierra_control",
            source="unassembled",
            reason="sierra_zn_control_only_not_a_rates_print",
            source_paths=paths,
            extra={
                "stance": "unassembled",
                "named_yield": used,
                "snaps": snaps,
                "sierra_zn": "control_only_not_used_as_rates_print",
                "usd_fx_is_not_a_yield": True,
                "threshold_d1": RATES_IMPULSE_D1,
            },
        )
    if not signed_vals:
        return _noul_block(
            name="rates_impulse",
            value=None,
            assembled=False,
            feed_class="unassembled",
            source="unassembled",
            reason="yield_books_present_but_stale_or_empty",
            source_paths=paths,
            extra={
                "stance": "unassembled",
                "named_yield": None,
                "sierra_zn": "control_only_not_used_as_rates_print",
                "usd_fx_is_not_a_yield": True,
                "threshold_d1": RATES_IMPULSE_D1,
            },
        )
    mean = sum(signed_vals) / len(signed_vals)
    value = mean >= RATES_IMPULSE_D1
    stance = "higher" if value else ("lower" if mean <= -RATES_IMPULSE_D1 else "flat")
    return _noul_block(
        name="rates_impulse",
        value=value,
        assembled=True,
        feed_class=feed if feed != "unassembled" else "lab_or_fixture",
        source="named_yield",
        reason=None if feed == "challenge_true" else "lab_or_fixture_not_challenge_true",
        source_paths=paths,
        extra={
            "stance": stance,
            "named_yield": used,
            "snaps": snaps,
            "mean_d1": round(mean, 6),
            "sierra_zn": "control_only_not_used_as_rates_print",
            "usd_fx_is_not_a_yield": True,
            "threshold_d1": RATES_IMPULSE_D1,
        },
    )


def _funding_stress_block(
    funding_rows: Sequence[Mapping[str, Any]] | None,
) -> dict[str, Any]:
    if not funding_rows:
        return _noul_block(
            name="funding_stress",
            value=None,
            assembled=False,
            feed_class="unassembled",
            source="unassembled",
            reason=FUNDING_ABSENT_REASON,
            source_paths=[],
            extra={
                "stance": "unassembled",
                "named_series": None,
                "gold_spread_is_not_funding": True,
                "vix_is_not_funding": True,
                "threshold": DEFAULT_FUNDING_STRESS_THRESHOLD,
            },
        )
    named = []
    paths: list[str] = []
    stressed = False
    for row in funding_rows:
        series = str(row.get("series") or row.get("name") or "").strip().upper()
        try:
            value = float(row["value"])
        except (KeyError, TypeError, ValueError):
            continue
        try:
            threshold = float(row.get("threshold", DEFAULT_FUNDING_STRESS_THRESHOLD))
        except (TypeError, ValueError):
            threshold = DEFAULT_FUNDING_STRESS_THRESHOLD
        path = str(row.get("source_path") or "")
        if path:
            paths.append(path)
        hit = value >= threshold
        named.append(
            {
                "series": series,
                "value": value,
                "threshold": threshold,
                "stressed": hit,
                "source_path": path or None,
            }
        )
        stressed = stressed or hit
    if not named:
        return _noul_block(
            name="funding_stress",
            value=None,
            assembled=False,
            feed_class="unassembled",
            source="unassembled",
            reason="funding_rows_present_but_unreadable",
            source_paths=paths,
            extra={
                "stance": "unassembled",
                "named_series": None,
                "gold_spread_is_not_funding": True,
                "vix_is_not_funding": True,
                "threshold": DEFAULT_FUNDING_STRESS_THRESHOLD,
            },
        )
    feed = feed_class_for(paths) if paths else "lab_or_fixture"
    return _noul_block(
        name="funding_stress",
        value=stressed,
        assembled=True,
        feed_class=feed,
        source="named_funding_rows",
        reason=None if feed == "challenge_true" else "lab_or_fixture_not_challenge_true",
        source_paths=paths,
        extra={
            "stance": "stress" if stressed else "calm",
            "named_series": [r["series"] for r in named],
            "rows": named,
            "gold_spread_is_not_funding": True,
            "vix_is_not_funding": True,
            "threshold": DEFAULT_FUNDING_STRESS_THRESHOLD,
        },
    )


def _usd_proxy_quality(usd: dict[str, Any], dxy: dict[str, Any]) -> dict[str, Any]:
    fx_ok = bool(usd.get("assembled"))
    dxy_ok = bool(dxy.get("usable_as_ice_dxy"))
    quality = "unassembled"
    agreement = None
    if fx_ok and dxy_ok:
        quality = "dxy_and_fx"
    elif fx_ok and dxy.get("file_present") and not dxy_ok:
        quality = "fx_basket_only_dxy_rejected"
    elif fx_ok:
        quality = "fx_basket_only"
    elif dxy.get("file_present") and not dxy_ok:
        quality = "dxy_rejected"
    return {
        "fx_basket_assembled": fx_ok,
        "dxy_usable": dxy_ok,
        "dxy_file_present": bool(dxy.get("file_present")),
        "agreement": agreement,
        "quality": quality,
        "note": (
            "Agreement vs ICE DXY is uncomputed until a usable DXY series lands. "
            "Rejected ~25 prints are not a quality score."
        ),
    }


def assemble_rates_dxy_funding_v0(
    *,
    as_of_utc: datetime,
    as_of_clock: str = "as_of_open_study",
    focus: Mapping[str, Any] | None = None,
    gold: Mapping[str, Any] | None = None,
    gold_books: Mapping[str, list[StampedBar]] | None = None,
    cross_books: Mapping[str, Mapping[str, list[StampedBar]]] | None = None,
    yield_books: Mapping[str, Mapping[str, list[StampedBar]]] | None = None,
    funding_rows: Sequence[Mapping[str, Any]] | None = None,
    dxy_path: Path | None = None,
    inventory: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Closed RDF object. Missing Challenge-true feeds stay null."""
    as_of = _as_of(as_of_utc)
    if cross_books is None:
        cross_books = load_named_challenge_cross_books()
    extra = focus or {}
    identity = (gold or {}).get("identity") or {}
    focus_block = {
        "candidate_id": extra.get("candidate_id") or identity.get("candidate_id"),
        "symbol": normalize_symbol(str(extra.get("symbol") or identity.get("symbol") or "XAUUSD")),
        "side": str(extra.get("side") or identity.get("side") or "").lower() or None,
    }
    usd = _usd_impulse_block(cross_books, as_of)
    rates = _rates_impulse_block(yield_books, as_of)
    funding = _funding_stress_block(funding_rows)
    risk = _risk_block(cross_books, as_of)
    dxy = inspect_dxy_csv(dxy_path)
    quality = _usd_proxy_quality(usd, dxy)
    inv = dict(inventory) if inventory is not None else named_source_inventory()

    missing: list[str] = []
    if usd["value"] is None:
        missing.append("usd_impulse.challenge_true" if usd["assembled"] else "usd_impulse")
    if rates["value"] is None:
        missing.append("rates_impulse")
    if funding["value"] is None:
        missing.append("funding_stress")
    if risk["value"] is None:
        missing.append("risk_on_off" if not risk["assembled"] and risk.get("stance") != "mixed" else "risk_on_off.decided")
    if not dxy.get("usable_as_ice_dxy"):
        missing.append("usd.dxy")

    return {
        "schema": SCHEMA,
        "pack": PACK_ID,
        "as_of_clock": as_of_clock,
        **stamp_lock(),
        **NEVER,
        "clock": {
            "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rule": "new_york_plus_7",
        },
        "focus": focus_block,
        "usd_impulse": usd,
        "rates_impulse": rates,
        "funding_stress": funding,
        "risk_on_off": risk,
        "dxy": {
            "series": None,
            "source": dxy.get("source") or "unassembled",
            "reason": dxy.get("reason") or DXY_ABSENT_REASON,
            "file_present": bool(dxy.get("file_present")),
            "usable_as_ice_dxy": bool(dxy.get("usable_as_ice_dxy")),
            "last_close": dxy.get("last_close"),
            "n_rows": dxy.get("n_rows"),
            "path": dxy.get("path"),
            "ice_band": [ICE_DXY_LOW, ICE_DXY_HIGH],
            "challenge_true": False,
            "rejected_reason": DXY_REJECTED_REASON if dxy.get("file_present") and not dxy.get("usable_as_ice_dxy") else None,
        },
        "usd_proxy_quality": quality,
        "sources_named": {
            "usd": usd.get("source_paths") or [],
            "rates": rates.get("source_paths") or [],
            "funding": funding.get("source_paths") or [],
            "risk": risk.get("source_paths") or [],
            "dxy": [dxy.get("path")] if dxy.get("file_present") else [],
        },
        "inventory": {
            "dxy_reason": (inv.get("dxy") or {}).get("reason"),
            "challenge_multi_dir_exists": ((inv.get("challenge_true") or {}).get("multi_dir_exists")),
            "challenge_multi_any_landed": ((inv.get("challenge_true") or {}).get("multi_any_landed")),
            "named_yield_csvs": ((inv.get("rates") or {}).get("named_yield_csvs") or []),
            "named_funding_csvs": ((inv.get("funding") or {}).get("named_funding_csvs") or []),
            "repair_ids": [r["id"] for r in (inv.get("repair_items") or [])],
        },
        "gold_books_present": bool(gold_books),
        "completeness": {
            "usd_impulse": usd["value"] is not None,
            "usd_impulse_challenge_true": bool(usd.get("challenge_true")),
            "rates_impulse": rates["value"] is not None,
            "funding_stress": funding["value"] is not None,
            "risk_on_off": risk["value"] is not None,
            "dxy": False,
            "named_yield": bool(rates.get("assembled")),
            "named_funding": bool(funding.get("assembled")),
            "missing_fields": missing,
        },
    }


def attach_rdf(world: Mapping[str, Any], rdf: Mapping[str, Any]) -> dict[str, Any]:
    """Desk + RDF. Questions may path-reference both. No size."""
    return {
        "schema": "gtos.judgment.jev_state.world_plus_rdf.v0",
        **NEVER,
        "world": dict(world),
        "rdf": dict(rdf),
    }


def rdf_noul_targets(rdf: Mapping[str, Any] | None) -> dict[str, bool | None]:
    """Code twins for the four Nouls. None = missing Challenge-true / unassembled."""
    rdf = rdf or {}
    return {
        "usd_impulse": (rdf.get("usd_impulse") or {}).get("value"),
        "rates_impulse": (rdf.get("rates_impulse") or {}).get("value"),
        "funding_stress": (rdf.get("funding_stress") or {}).get("value"),
        "risk_on_off": (rdf.get("risk_on_off") or {}).get("value"),
    }


def prove_rdf_challenge_as_of(
    *,
    as_of_utc: datetime | None = None,
    focus: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Research prove. LABEL only. Never APPLY / place / enforce."""
    from .rdf_questions import compose_rdf_shadow

    as_of = _as_of(as_of_utc or CHALLENGE_AS_OF)
    rdf = assemble_rates_dxy_funding_v0(
        as_of_utc=as_of,
        as_of_clock="as_of_open_study",
        focus=focus
        or {
            "candidate_id": "293332188",
            "symbol": "XAUUSD",
            "side": "short",
        },
    )
    composed = compose_rdf_shadow(rdf)
    twins = rdf_noul_targets(rdf)
    return {
        "schema": "gtos.judgment.rdf_challenge_prove.v0",
        **NEVER,
        "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "as_of_clock": "as_of_open_study",
        "focus": rdf.get("focus"),
        "noul_targets": twins,
        "challenge_true": {
            "usd_impulse": bool((rdf.get("usd_impulse") or {}).get("challenge_true")),
            "rates_impulse": bool((rdf.get("rates_impulse") or {}).get("challenge_true")),
            "funding_stress": bool((rdf.get("funding_stress") or {}).get("challenge_true")),
            "risk_on_off": bool((rdf.get("risk_on_off") or {}).get("challenge_true")),
        },
        "usd_impulse": {
            "value": twins["usd_impulse"],
            "stance": (rdf.get("usd_impulse") or {}).get("stance"),
            "mean_usd_h4": (rdf.get("usd_impulse") or {}).get("mean_usd_h4"),
            "present": (rdf.get("usd_impulse") or {}).get("present"),
            "feed_class": (rdf.get("usd_impulse") or {}).get("feed_class"),
        },
        "risk_on_off": {
            "value": twins["risk_on_off"],
            "stance": (rdf.get("risk_on_off") or {}).get("stance"),
            "mean_h4": (rdf.get("risk_on_off") or {}).get("mean_h4"),
            "present": (rdf.get("risk_on_off") or {}).get("present"),
            "feed_class": (rdf.get("risk_on_off") or {}).get("feed_class"),
        },
        "rates_impulse": {
            "value": None,
            "assembled": False,
            "reason": (rdf.get("rates_impulse") or {}).get("reason"),
        },
        "funding_stress": {
            "value": None,
            "assembled": False,
            "reason": (rdf.get("funding_stress") or {}).get("reason"),
        },
        "dxy": {
            "usable_as_ice_dxy": False,
            "reason": (rdf.get("dxy") or {}).get("reason") or DXY_REJECTED_REASON,
            "last_close": (rdf.get("dxy") or {}).get("last_close"),
            "series": None,
        },
        "compose": {
            "chair_draft": composed["chair_draft"],
            "disposition": composed["disposition"],
            "never_apply_size": composed["never_apply_size"],
            "never_resize": composed["never_resize"],
        },
        "chair_draft": composed["chair_draft"],
        "disposition": "rdf_label_only",
        "rdf": rdf,
    }
