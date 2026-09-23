"""Chair synthesis sleeve fields — first-class inputs on the 48-gate pipe.

Owner / Chair 2026-09-18. SHADOW only. Each field is a named sleeve hook that
existing fluid questions may read. No new gates. No APPLY. No invented DXY,
funding, peer OHLC, or US30 lift.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

SCHEMA = "gtos.judgment.aplus_chair_fields.v0"
ORIGIN = "chair_synthesis_20260918"

# Closed Chair set. Do not silently add a ninth field here.
CHAIR_FIELD_IDS = (
    "usd_proxy_vs_xau",
    "gbpjpy_dual_leg_agree",
    "us30_rth_vs_eth",
    "sess.ldn_ny_overlap_vol",
    "fx_session_london_fit",
    "corr.eur_gbp_usd_co_move",
    "corr.xau_vs_eur_proxy_usd",
    "tokyo_fix_window_label",
)

# London–NY overlap 12:00–16:00 UTC. Volume stays unassembled without named M15.
LDN_NY_OVERLAP_UTC = (12, 16)
# Tokyo 09:55 JST fix. Japan has no DST → 00:55 UTC. Label window 00:50–01:10.
TOKYO_FIX_UTC = ((0, 50), (1, 10))
# US30 RTH approx NYSE 09:30–16:00 ET as 13:30–20:00 UTC (EDT). DST unresolved.
US30_RTH_UTC = ((13, 30), (20, 0))

PEER_SOURCE = "peers.peer_state"
CLOCK_SOURCE = "clock.as_of_utc"

# question → inventory ids. Inventory stays 48. These are inputs, not new gates.
CHAIR_FIELD_SPEC: dict[str, dict[str, Any]] = {
    "usd_proxy_vs_xau": {
        "kind": "score",
        "applies_symbols": ("XAUUSD", "USDJPY"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "never_invent": ("DXY", "funding", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
            {"question": "veto_corr", "ids": ("FLUID-PLC-001",)},
        ),
        "role": "Named USD proxy (USDJPY / inverse EURUSD) vs XAU side. Not a DXY print.",
    },
    "gbpjpy_dual_leg_agree": {
        "kind": "noul",
        "applies_symbols": ("GBPJPY",),
        "source": PEER_SOURCE,
        "clock_true": False,
        "never_invent": ("GBPUSD", "USDJPY", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
            {"question": "veto_corr", "ids": ("FLUID-PLC-001",)},
            {"question": "cluster_same_day", "ids": ("FLUID-REN-006",)},
        ),
        "role": "GBPJPY side agrees with named GBPUSD and USDJPY legs.",
    },
    "us30_rth_vs_eth": {
        "kind": "choice",
        "applies_symbols": ("US30", "US30.cash", "US30_cash"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "never_invent": ("US30_tape", "ENV-US30_lift"),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "friday_cutoff_label", "ids": ("FLUID-HLD-008",)},
        ),
        "envelope": "ENV-US30",
        "role": "LABEL RTH vs ETH from clock. Envelope US30 stays integer OFF.",
    },
    "sess.ldn_ny_overlap_vol": {
        "kind": "score",
        "applies_symbols": ("XAUUSD", "GBPJPY", "EURUSD", "USDJPY", "GBPUSD", "EURGBP"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "never_invent": ("overlap_volume",),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "geometry_vs_tape", "ids": ("FLUID-ADM-005", "SEL-V4-002")},
            {"question": "geo_size", "ids": ("FLUID-SIZ-004",)},
            {"question": "cost_vs_tape", "ids": ("FLUID-PLC-005",)},
        ),
        "role": "Clock-true London–NY overlap window. Volume stays unassembled without named M15.",
    },
    "fx_session_london_fit": {
        "kind": "score",
        "applies_symbols": ("GBPJPY", "EURUSD", "USDJPY", "GBPUSD", "EURGBP"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "never_invent": (),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
        ),
        "role": "FX sleeve London kill-zone fit from sessions.named. Writer clock stays integer.",
    },
    "corr.eur_gbp_usd_co_move": {
        "kind": "noul",
        "applies_symbols": ("EURUSD", "GBPJPY", "GBPUSD", "EURGBP"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "never_invent": ("EURUSD", "GBPUSD", "EURGBP", "peer_ohlc"),
        "gate_inputs": (
            {"question": "veto_corr", "ids": ("FLUID-PLC-001",)},
            {"question": "veto_occupancy_label", "ids": ("FLUID-PLC-004",)},
            {"question": "cluster_same_day", "ids": ("FLUID-REN-006",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
        ),
        "role": "Named EUR/GBP/USD co-move. Waits SYMBOL_STATE_V0 peer_state.",
    },
    "corr.xau_vs_eur_proxy_usd": {
        "kind": "noul",
        "applies_symbols": ("XAUUSD", "EURUSD"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "never_invent": ("DXY", "EURUSD", "peer_ohlc"),
        "gate_inputs": (
            {"question": "veto_corr", "ids": ("FLUID-PLC-001",)},
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
        ),
        "role": "XAU vs EUR-as-USD-proxy. Gold↔USD, not a yield print.",
    },
    "tokyo_fix_window_label": {
        "kind": "noul",
        "applies_symbols": ("USDJPY", "GBPJPY", "EURJPY"),
        "source": CLOCK_SOURCE,
        "clock_true": True,
        "never_invent": ("tokyo_fix_print",),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "friday_cutoff_label", "ids": ("FLUID-HLD-008",)},
        ),
        "role": "LABEL Tokyo 09:55 JST fix window from clock. Not a news HIGH.",
    },
}


def _norm_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper().replace(" ", "")


def field_applies(field_id: str, symbol: str) -> bool:
    spec = CHAIR_FIELD_SPEC[field_id]
    want = {_norm_symbol(s) for s in spec["applies_symbols"]}
    have = _norm_symbol(symbol)
    if have in want:
        return True
    if have.replace(".CASH", "").replace("_CASH", "") in want:
        return True
    return False


def chair_gate_map() -> list[dict[str, Any]]:
    rows = []
    for field_id in CHAIR_FIELD_IDS:
        spec = CHAIR_FIELD_SPEC[field_id]
        rows.append(
            {
                "field": field_id,
                "kind": spec["kind"],
                "source": spec["source"],
                "clock_true": spec["clock_true"],
                "applies_symbols": list(spec["applies_symbols"]),
                "gate_questions": [g["question"] for g in spec["gate_inputs"]],
                "gate_ids": [gid for g in spec["gate_inputs"] for gid in g["ids"]],
                "never_invent": list(spec["never_invent"]),
                "envelope": spec.get("envelope"),
                "role": spec["role"],
                "shadow_only": True,
            }
        )
    return rows


def _minutes(as_of: datetime) -> int:
    return as_of.hour * 60 + as_of.minute


def _in_hm_window(as_of: datetime, start: tuple[int, int], end: tuple[int, int]) -> bool:
    now = _minutes(as_of)
    lo = start[0] * 60 + start[1]
    hi = end[0] * 60 + end[1]
    return lo <= now < hi


def _named_from_peer(peer_state: Mapping[str, Any] | None, field_id: str) -> Any:
    if not peer_state:
        return None
    if field_id in peer_state and peer_state[field_id] is not None:
        raw = peer_state[field_id]
        if isinstance(raw, Mapping) and "value" in raw:
            return raw.get("value")
        return raw
    return None


def _row(
    field_id: str,
    *,
    applies: bool,
    assembled: bool,
    value: Any,
    source: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    spec = CHAIR_FIELD_SPEC[field_id]
    packed = {
        "id": field_id,
        "kind": spec["kind"],
        "applies": applies,
        "assembled": bool(applies and assembled),
        "value": value if applies else None,
        "source": source if applies else "not_applicable",
        "invented": False,
        "shadow_only": True,
        "never_apply_size": True,
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


def assemble_chair_fields(
    *,
    symbol: str,
    as_of_utc: datetime,
    session_named: str | None = None,
    peer_state: Mapping[str, Any] | None = None,
    chair_values: Mapping[str, Any] | None = None,
    m15_vol: float | None = None,
) -> dict[str, Any]:
    """Assemble the closed Chair set. Missing peers stay visible. Never invent."""
    as_of = as_of_utc if as_of_utc.tzinfo else as_of_utc.replace(tzinfo=timezone.utc)
    as_of = as_of.astimezone(timezone.utc)
    named = str(session_named or "")
    supplied = dict(chair_values or {})
    peers = dict(peer_state or {})
    fields: dict[str, Any] = {}

    # usd_proxy_vs_xau — peer only
    applies = field_applies("usd_proxy_vs_xau", symbol)
    value = supplied.get("usd_proxy_vs_xau")
    if value is None:
        value = _named_from_peer(peers, "usd_proxy_vs_xau")
    fields["usd_proxy_vs_xau"] = _row(
        "usd_proxy_vs_xau",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    # gbpjpy_dual_leg_agree — peer only
    applies = field_applies("gbpjpy_dual_leg_agree", symbol)
    value = supplied.get("gbpjpy_dual_leg_agree")
    if value is None:
        value = _named_from_peer(peers, "gbpjpy_dual_leg_agree")
    fields["gbpjpy_dual_leg_agree"] = _row(
        "gbpjpy_dual_leg_agree",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    # us30_rth_vs_eth — clock label, ENV-US30 stays
    applies = field_applies("us30_rth_vs_eth", symbol)
    if applies:
        in_rth = _in_hm_window(as_of, *US30_RTH_UTC)
        value = supplied.get("us30_rth_vs_eth") or ("rth" if in_rth else "eth")
        extra = {"dst_unresolved": True, "envelope": "ENV-US30", "envelope_stays": "integer_off"}
    else:
        value = None
        extra = {"envelope": "ENV-US30", "envelope_stays": "integer_off"}
    fields["us30_rth_vs_eth"] = _row(
        "us30_rth_vs_eth",
        applies=applies,
        assembled=applies,
        value=value,
        source=CLOCK_SOURCE,
        extra=extra,
    )

    # sess.ldn_ny_overlap_vol — clock window; vol only if named
    applies = field_applies("sess.ldn_ny_overlap_vol", symbol)
    in_overlap = LDN_NY_OVERLAP_UTC[0] <= as_of.hour < LDN_NY_OVERLAP_UTC[1]
    vol = supplied.get("sess.ldn_ny_overlap_vol")
    if isinstance(vol, Mapping):
        in_overlap = bool(vol.get("in_window", in_overlap))
        named_vol = vol.get("vol")
    else:
        named_vol = vol if isinstance(vol, (int, float)) else m15_vol
    fields["sess.ldn_ny_overlap_vol"] = _row(
        "sess.ldn_ny_overlap_vol",
        applies=applies,
        assembled=applies,
        value={
            "in_window": in_overlap if applies else None,
            "vol": named_vol if applies else None,
            "window_utc": list(LDN_NY_OVERLAP_UTC),
            "session_named": named or None,
        }
        if applies
        else None,
        source=CLOCK_SOURCE,
        extra={"vol_assembled": named_vol is not None},
    )

    # fx_session_london_fit — clock / sessions.named
    applies = field_applies("fx_session_london_fit", symbol)
    if not applies:
        fit = None
    elif named in {"friday_cutoff", "dead_21_00z"}:
        fit = 0.0
    elif named == "london":
        fit = 2.0
    elif named in {"asia", "tokyo", "ny"}:
        fit = 1.0
    else:
        fit = None
    if applies and supplied.get("fx_session_london_fit") is not None:
        fit = supplied["fx_session_london_fit"]
    fields["fx_session_london_fit"] = _row(
        "fx_session_london_fit",
        applies=applies,
        assembled=applies and fit is not None,
        value=fit,
        source=CLOCK_SOURCE,
    )

    # corr.eur_gbp_usd_co_move — peer only
    applies = field_applies("corr.eur_gbp_usd_co_move", symbol)
    value = supplied.get("corr.eur_gbp_usd_co_move")
    if value is None:
        value = _named_from_peer(peers, "corr.eur_gbp_usd_co_move")
    fields["corr.eur_gbp_usd_co_move"] = _row(
        "corr.eur_gbp_usd_co_move",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    # corr.xau_vs_eur_proxy_usd — peer only
    applies = field_applies("corr.xau_vs_eur_proxy_usd", symbol)
    value = supplied.get("corr.xau_vs_eur_proxy_usd")
    if value is None:
        value = _named_from_peer(peers, "corr.xau_vs_eur_proxy_usd")
    fields["corr.xau_vs_eur_proxy_usd"] = _row(
        "corr.xau_vs_eur_proxy_usd",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    # tokyo_fix_window_label — clock
    applies = field_applies("tokyo_fix_window_label", symbol)
    in_fix = _in_hm_window(as_of, *TOKYO_FIX_UTC)
    if applies and supplied.get("tokyo_fix_window_label") is not None:
        in_fix = bool(supplied["tokyo_fix_window_label"])
    fields["tokyo_fix_window_label"] = _row(
        "tokyo_fix_window_label",
        applies=applies,
        assembled=applies,
        value=in_fix if applies else None,
        source=CLOCK_SOURCE,
        extra={"window_utc": "00:50-01:10", "fix_jst": "09:55"},
    )

    missing = [
        f"chair_fields.{fid}"
        for fid in CHAIR_FIELD_IDS
        if fields[fid]["applies"] and not fields[fid]["assembled"]
    ]
    return {
        "schema": SCHEMA,
        "origin": ORIGIN,
        "shadow_only": True,
        "never_apply_size": True,
        "n": len(CHAIR_FIELD_IDS),
        "ids": list(CHAIR_FIELD_IDS),
        "fields": fields,
        "n_applies": sum(1 for fid in CHAIR_FIELD_IDS if fields[fid]["applies"]),
        "n_assembled": sum(1 for fid in CHAIR_FIELD_IDS if fields[fid]["assembled"]),
        "invented": False,
        "missing_fields": missing,
    }


def chair_corr_noul(chair: Mapping[str, Any] | None) -> bool | None:
    """Draft-only corr HOLD from assembled Chair corr fields. Unassembled → None."""
    if not chair:
        return None
    fields = chair.get("fields") if isinstance(chair.get("fields"), Mapping) else chair
    seen = False
    against = False
    for fid in ("gbpjpy_dual_leg_agree", "corr.eur_gbp_usd_co_move", "corr.xau_vs_eur_proxy_usd"):
        row = fields.get(fid) if isinstance(fields, Mapping) else None
        if not isinstance(row, Mapping) or not row.get("applies") or not row.get("assembled"):
            continue
        seen = True
        value = row.get("value")
        if value in {False, "against", "disagree", 0, 0.0}:
            against = True
    if not seen:
        return None
    return against


def chair_session_source(chair: Mapping[str, Any] | None) -> str:
    if not chair:
        return "sessions.named"
    fields = chair.get("fields") if isinstance(chair.get("fields"), Mapping) else {}
    clockish = (
        "fx_session_london_fit",
        "sess.ldn_ny_overlap_vol",
        "tokyo_fix_window_label",
        "us30_rth_vs_eth",
    )
    if any((fields.get(fid) or {}).get("assembled") for fid in clockish):
        return "sessions.named+aplus.chair_fields"
    return "sessions.named"
