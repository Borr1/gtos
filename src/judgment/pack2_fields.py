"""Instrument Edge PACK 2 — Tier-1 A+ sleeve_field / gate_input stubs.

Owner / Chair 2026-09-18. SHADOW only. Closed set of 9. Each stub is a named
input existing FLUID-ADM / FLUID-SIZ / FLUID-NWS questions may read.

No new fluid gates. No new refuse walls. No APPLY. ENV-US30 stays integer OFF.
Do not invent DXY, funding, peer OHLC, or a BOJ HIGH.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from .chair_fields import (
    CLOCK_SOURCE,
    LDN_NY_OVERLAP_UTC,
    PEER_SOURCE,
    US30_RTH_UTC,
    _in_hm_window,
    _named_from_peer,
    chair_session_source,
)
from .fluid_gates import lookup
from .news_spine import F5_POST, F5_PRE

SCHEMA = "gtos.judgment.aplus_pack2_fields.v0"
ORIGIN = "instrument_edge_pack2_20260918"

# Closed PACK 2 Tier-1 set. Do not silently add a tenth field here.
PACK2_FIELD_IDS = (
    "gate.session_overlap_ok",
    "gate.asia_jpy_act_ok",
    "gate.ny_rth_us30_act_ok",
    "sleeve.usd_common_factor",
    "sleeve.xau_usd_proxy_align",
    "gate.cross_stack_gbpjpy",
    "sleeve.london_expand_eur_gbp",
    "gate.event_boj_window",
    "info.risk_on_off_bundle",
)

ALLOWED_FAMILIES = frozenset({"admit", "size", "news_window"})
NEWS_SOURCE = "news.events"
ASIA_JPY_UTC = (1, 7)
LONDON_EXPAND_UTC = (7, 12)
_BOJ_TOKENS = ("boj", "bank of japan")

PACK2_FIELD_SPEC: dict[str, dict[str, Any]] = {
    "gate.session_overlap_ok": {
        "surface": "gate_input",
        "kind": "noul",
        "applies_symbols": ("XAUUSD", "GBPJPY", "EURUSD", "USDJPY", "GBPUSD", "EURGBP"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("overlap_volume",),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
        ),
        "role": "LABEL London–NY overlap 12–16 UTC. Input to session_fitness / session_size. Not a refuse.",
    },
    "gate.asia_jpy_act_ok": {
        "surface": "gate_input",
        "kind": "noul",
        "applies_symbols": ("USDJPY", "GBPJPY", "EURJPY"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("tokyo_fix_print",),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
        ),
        "role": "LABEL writer asia (01–07 UTC) for JPY. dead_21_00z / Friday stay not-ok. Writer clock integer.",
    },
    "gate.ny_rth_us30_act_ok": {
        "surface": "gate_input",
        "kind": "noul",
        "applies_symbols": ("US30", "US30.cash", "US30_cash"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("US30_tape", "ENV-US30_lift"),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
        ),
        "envelope": "ENV-US30",
        "role": "LABEL NY RTH vs ETH from clock. ENV-US30 stays integer OFF. Not a refuse wall.",
    },
    "sleeve.usd_common_factor": {
        "surface": "sleeve_field",
        "kind": "score",
        "applies_symbols": ("XAUUSD", "USDJPY", "EURUSD", "GBPUSD"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "families": ("admit", "size"),
        "never_invent": ("DXY", "funding", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
            {"question": "combined_size", "ids": ("FLUID-SIZ-008",)},
        ),
        "role": "Named USD common-factor sleeve hook. Not a DXY print. Unassembled until peers.peer_state.",
    },
    "sleeve.xau_usd_proxy_align": {
        "surface": "sleeve_field",
        "kind": "noul",
        "applies_symbols": ("XAUUSD", "EURUSD", "USDJPY"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "families": ("admit", "size"),
        "never_invent": ("DXY", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
        ),
        "role": "XAU vs named USD-proxy align. Gold↔USD, not a yield print.",
    },
    "gate.cross_stack_gbpjpy": {
        "surface": "gate_input",
        "kind": "noul",
        "applies_symbols": ("GBPJPY",),
        "source": PEER_SOURCE,
        "clock_true": False,
        "families": ("admit", "size"),
        "never_invent": ("GBPUSD", "USDJPY", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
        ),
        "role": "GBPJPY cross-stack agrees with named GBPUSD + USDJPY legs. Not a new refuse.",
    },
    "sleeve.london_expand_eur_gbp": {
        "surface": "sleeve_field",
        "kind": "score",
        "applies_symbols": ("EURUSD", "GBPUSD", "EURGBP", "GBPJPY"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("expansion_volume",),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "geometry_vs_tape", "ids": ("FLUID-ADM-005",)},
            {"question": "geo_size", "ids": ("FLUID-SIZ-004",)},
        ),
        "role": "London kill-zone expand fit for EUR/GBP. Volume stays unassembled without named M15.",
    },
    "gate.event_boj_window": {
        "surface": "gate_input",
        "kind": "noul",
        "applies_symbols": ("USDJPY", "GBPJPY", "EURJPY"),
        "source": NEWS_SOURCE,
        "clock_true": False,
        "families": ("news_window", "size"),
        "never_invent": ("boj_high", "NEWS_PROTOCOL"),
        "gate_inputs": (
            {"question": "event_proximity", "ids": ("FLUID-NWS-001",)},
            {"question": "high_in_f5_window", "ids": ("FLUID-NWS-002",)},
            {"question": "warsh_class", "ids": ("FLUID-NWS-004",)},
            {"question": "event_size", "ids": ("FLUID-SIZ-006",)},
        ),
        "role": "LABEL named BOJ HIGH inside the F5 window. Empty spine stays unassembled. Not a refuse.",
    },
    "info.risk_on_off_bundle": {
        "surface": "info",
        "kind": "info",
        "applies_symbols": ("XAUUSD", "GBPJPY", "EURUSD", "USDJPY", "GBPUSD", "EURGBP", "US30"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "families": ("admit", "news_window", "size"),
        "never_invent": ("DXY", "funding", "risk_on_off_print"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "warsh_class", "ids": ("FLUID-NWS-004",)},
            {"question": "event_size", "ids": ("FLUID-SIZ-006",)},
        ),
        "role": "INFO bundle only. Named stance waits peers.peer_state. Cannot refuse a fire.",
    },
}


def _norm_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper().replace(" ", "")


def field_applies(field_id: str, symbol: str) -> bool:
    spec = PACK2_FIELD_SPEC[field_id]
    want = {_norm_symbol(s) for s in spec["applies_symbols"]}
    have = _norm_symbol(symbol)
    if have in want:
        return True
    stripped = have.replace(".CASH", "").replace("_CASH", "")
    return stripped in want


def pack2_gate_map() -> list[dict[str, Any]]:
    rows = []
    for field_id in PACK2_FIELD_IDS:
        spec = PACK2_FIELD_SPEC[field_id]
        rows.append(
            {
                "field": field_id,
                "surface": spec["surface"],
                "kind": spec["kind"],
                "source": spec["source"],
                "clock_true": spec["clock_true"],
                "families": list(spec["families"]),
                "applies_symbols": list(spec["applies_symbols"]),
                "gate_questions": [g["question"] for g in spec["gate_inputs"]],
                "gate_ids": [gid for g in spec["gate_inputs"] for gid in g["ids"]],
                "never_invent": list(spec["never_invent"]),
                "envelope": spec.get("envelope"),
                "role": spec["role"],
                "shadow_only": True,
                "never_refuse": True,
                "never_apply_size": True,
            }
        )
    return rows


def assert_pack2_maps_existing_families() -> dict[str, Any]:
    """Every PACK 2 gate id must already exist and sit in ADM / SIZ / NWS."""
    bad: list[str] = []
    for row in pack2_gate_map():
        for gid in row["gate_ids"]:
            gate = lookup(gid)
            if gate is None:
                bad.append(f"missing:{gid}")
                continue
            fam = str(gate.get("family") or "")
            if fam not in ALLOWED_FAMILIES:
                bad.append(f"family:{gid}:{fam}")
            if gate.get("class") not in {"fluid", "envelope"}:
                bad.append(f"class:{gid}")
    return {"ok": not bad, "bad": bad, "n": len(PACK2_FIELD_IDS), "families": sorted(ALLOWED_FAMILIES)}


def _row(
    field_id: str,
    *,
    applies: bool,
    assembled: bool,
    value: Any,
    source: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    spec = PACK2_FIELD_SPEC[field_id]
    packed = {
        "id": field_id,
        "surface": spec["surface"],
        "kind": spec["kind"],
        "applies": applies,
        "assembled": bool(applies and assembled),
        "value": value if applies else None,
        "source": source if applies else "not_applicable",
        "invented": False,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "families": list(spec["families"]),
        "gate_questions": [g["question"] for g in spec["gate_inputs"]],
        "gate_ids": [gid for g in spec["gate_inputs"] for gid in g["ids"]],
        "never_invent": list(spec["never_invent"]),
    }
    if extra:
        packed.update(extra)
    if not applies:
        packed["assembled"] = False
        packed["value"] = None
    return packed


def _boj_from_news(news: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Named BOJ HIGH only. Empty spine → unassembled. Never invent."""
    if not news or news.get("spine_empty"):
        return None
    hits: list[tuple[bool, Mapping[str, Any]]] = []
    for ev in news.get("events") or []:
        if not isinstance(ev, Mapping):
            continue
        blob = " ".join(str(ev.get(k) or "") for k in ("event", "event_type", "title")).lower()
        if not any(token in blob for token in _BOJ_TOKENS):
            continue
        in_win = False
        mins = ev.get("minutes_from_as_of")
        if mins is not None:
            try:
                in_win = -F5_POST <= int(mins) <= F5_PRE
            except (TypeError, ValueError):
                in_win = False
        hits.append((in_win, ev))
    if not hits:
        return {"in_window": False, "named_boj": False, "event": None}
    in_win = any(hit for hit, _ in hits)
    ev = next((row for hit, row in hits if hit), hits[0][1])
    return {
        "in_window": in_win,
        "named_boj": True,
        "event": ev.get("event"),
        "currency": ev.get("currency"),
        "impact": ev.get("impact"),
    }


def _london_expand_score(as_of: datetime, named: str) -> float | None:
    if named in {"friday_cutoff", "dead_21_00z"}:
        return 0.0
    if named == "london" or LONDON_EXPAND_UTC[0] <= as_of.hour < LONDON_EXPAND_UTC[1]:
        return 2.0
    if named == "ny" or LDN_NY_OVERLAP_UTC[0] <= as_of.hour < LDN_NY_OVERLAP_UTC[1]:
        return 1.0
    if named in {"asia", "tokyo"}:
        return 1.0
    return None


def assemble_pack2_fields(
    *,
    symbol: str,
    as_of_utc: datetime,
    session_named: str | None = None,
    peer_state: Mapping[str, Any] | None = None,
    pack2_values: Mapping[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble the closed PACK 2 set. Missing peers / empty spine stay visible."""
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    named = str(session_named or "")
    supplied = dict(pack2_values or {})
    peers = dict(peer_state or {})
    fields: dict[str, Any] = {}

    applies = field_applies("gate.session_overlap_ok", symbol)
    in_overlap = LDN_NY_OVERLAP_UTC[0] <= as_of.hour < LDN_NY_OVERLAP_UTC[1]
    if applies and supplied.get("gate.session_overlap_ok") is not None:
        in_overlap = bool(supplied["gate.session_overlap_ok"])
    fields["gate.session_overlap_ok"] = _row(
        "gate.session_overlap_ok",
        applies=applies,
        assembled=applies,
        value=in_overlap if applies else None,
        source=CLOCK_SOURCE,
        extra={"window_utc": list(LDN_NY_OVERLAP_UTC), "session_named": named or None},
    )

    applies = field_applies("gate.asia_jpy_act_ok", symbol)
    asia_ok = named == "asia" or ASIA_JPY_UTC[0] <= as_of.hour < ASIA_JPY_UTC[1]
    if named in {"friday_cutoff", "dead_21_00z"}:
        asia_ok = False
    if applies and supplied.get("gate.asia_jpy_act_ok") is not None:
        asia_ok = bool(supplied["gate.asia_jpy_act_ok"])
    fields["gate.asia_jpy_act_ok"] = _row(
        "gate.asia_jpy_act_ok",
        applies=applies,
        assembled=applies,
        value=asia_ok if applies else None,
        source=CLOCK_SOURCE,
        extra={"window_utc": list(ASIA_JPY_UTC), "session_named": named or None},
    )

    applies = field_applies("gate.ny_rth_us30_act_ok", symbol)
    if applies:
        in_rth = _in_hm_window(as_of, *US30_RTH_UTC)
        value = supplied.get("gate.ny_rth_us30_act_ok")
        value = bool(value) if value is not None else in_rth
        extra = {"dst_unresolved": True, "envelope": "ENV-US30", "envelope_stays": "integer_off"}
    else:
        value = None
        extra = {"envelope": "ENV-US30", "envelope_stays": "integer_off"}
    fields["gate.ny_rth_us30_act_ok"] = _row(
        "gate.ny_rth_us30_act_ok",
        applies=applies,
        assembled=applies,
        value=value,
        source=CLOCK_SOURCE,
        extra=extra,
    )

    applies = field_applies("sleeve.usd_common_factor", symbol)
    value = supplied.get("sleeve.usd_common_factor")
    if value is None:
        value = _named_from_peer(peers, "sleeve.usd_common_factor")
    fields["sleeve.usd_common_factor"] = _row(
        "sleeve.usd_common_factor",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    applies = field_applies("sleeve.xau_usd_proxy_align", symbol)
    value = supplied.get("sleeve.xau_usd_proxy_align")
    if value is None:
        value = _named_from_peer(peers, "sleeve.xau_usd_proxy_align")
    fields["sleeve.xau_usd_proxy_align"] = _row(
        "sleeve.xau_usd_proxy_align",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    applies = field_applies("gate.cross_stack_gbpjpy", symbol)
    value = supplied.get("gate.cross_stack_gbpjpy")
    if value is None:
        value = _named_from_peer(peers, "gate.cross_stack_gbpjpy")
    fields["gate.cross_stack_gbpjpy"] = _row(
        "gate.cross_stack_gbpjpy",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    applies = field_applies("sleeve.london_expand_eur_gbp", symbol)
    fit = _london_expand_score(as_of, named) if applies else None
    if applies and supplied.get("sleeve.london_expand_eur_gbp") is not None:
        fit = supplied["sleeve.london_expand_eur_gbp"]
    fields["sleeve.london_expand_eur_gbp"] = _row(
        "sleeve.london_expand_eur_gbp",
        applies=applies,
        assembled=applies and fit is not None,
        value=fit,
        source=CLOCK_SOURCE,
        extra={"vol_assembled": False},
    )

    applies = field_applies("gate.event_boj_window", symbol)
    boj = supplied.get("gate.event_boj_window")
    if isinstance(boj, Mapping):
        boj_row = dict(boj)
    elif boj is not None:
        boj_row = {"in_window": bool(boj), "named_boj": True, "event": None}
    else:
        boj_row = _boj_from_news(news)
    fields["gate.event_boj_window"] = _row(
        "gate.event_boj_window",
        applies=applies,
        assembled=applies and boj_row is not None,
        value=(boj_row.get("in_window") if isinstance(boj_row, Mapping) else None) if applies else None,
        source=NEWS_SOURCE if applies else "not_applicable",
        extra={"named_boj": (boj_row or {}).get("named_boj") if isinstance(boj_row, Mapping) else None,
               "event": (boj_row or {}).get("event") if isinstance(boj_row, Mapping) else None,
               "never_refuse": True},
    )

    applies = field_applies("info.risk_on_off_bundle", symbol)
    value = supplied.get("info.risk_on_off_bundle")
    if value is None:
        value = _named_from_peer(peers, "info.risk_on_off_bundle")
    fields["info.risk_on_off_bundle"] = _row(
        "info.risk_on_off_bundle",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
        extra={"info_only": True, "cannot_refuse": True},
    )

    missing = [
        f"pack2_fields.{fid}"
        for fid in PACK2_FIELD_IDS
        if fields[fid]["applies"] and not fields[fid]["assembled"]
    ]
    return {
        "schema": SCHEMA,
        "origin": ORIGIN,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "n": len(PACK2_FIELD_IDS),
        "ids": list(PACK2_FIELD_IDS),
        "fields": fields,
        "n_applies": sum(1 for fid in PACK2_FIELD_IDS if fields[fid]["applies"]),
        "n_assembled": sum(1 for fid in PACK2_FIELD_IDS if fields[fid]["assembled"]),
        "invented": False,
        "missing_fields": missing,
        "families": sorted(ALLOWED_FAMILIES),
    }


def pack2_clock_assembled(pack2: Mapping[str, Any] | None) -> bool:
    if not pack2:
        return False
    fields = pack2.get("fields") if isinstance(pack2.get("fields"), Mapping) else {}
    clockish = (
        "gate.session_overlap_ok",
        "gate.asia_jpy_act_ok",
        "gate.ny_rth_us30_act_ok",
        "sleeve.london_expand_eur_gbp",
    )
    return any((fields.get(fid) or {}).get("assembled") for fid in clockish)


def session_input_source(
    chair: Mapping[str, Any] | None = None,
    pack2: Mapping[str, Any] | None = None,
    pack3: Mapping[str, Any] | None = None,
    pack4: Mapping[str, Any] | None = None,
    pack5: Mapping[str, Any] | None = None,
) -> str:
    bits = ["sessions.named"]
    if chair and chair_session_source(chair) == "sessions.named+aplus.chair_fields":
        bits.append("aplus.chair_fields")
    if pack2_clock_assembled(pack2):
        bits.append("aplus.pack2")
    if pack3:
        fields = pack3.get("fields") if isinstance(pack3.get("fields"), Mapping) else {}
        clockish = (
            "sess.ldn_ny_overlap_vol",
            "london_open_eur_gbp_expand",
            "ny_cash_open_us30",
        )
        if any((fields.get(fid) or {}).get("assembled") for fid in clockish):
            bits.append("aplus.pack3")
    if pack4:
        from .pack4_fields import pack4_choice_assembled

        if pack4_choice_assembled(pack4):
            bits.append("aplus.pack4")
    if pack5:
        from .pack5_fields import pack5_choice_assembled

        if pack5_choice_assembled(pack5):
            bits.append("aplus.pack5")
    return "+".join(bits)
