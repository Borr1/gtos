"""Instrument Edge PACK 3 — SHADOW field assembly.

Clocks on ``time_utc`` only (server offset is a clock fact).
On the Challenge writer the class is the ask. An empty answer leaves the
class unset. Off that writer the recorded comparison stays for research.
No new fluid gates. No new refuse walls. No APPLY. ENV-US30 stays integer OFF.
Do not invent DXY, funding, peer OHLC, or a BOJ HIGH.
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from .chair_fields import PEER_SOURCE, _named_from_peer
from .fluid_gates import lookup
from .news_spine import F5_POST, F5_PRE

SCHEMA = "gtos.judgment.aplus_pack3_fields.v0"
ORIGIN = "instrument_edge_pack3_20260918"

# Recorded comparison for research that is not the Challenge writer.
# The Challenge class does not read these.
RESID_CAP = 0.15
LONDON_EXPAND_PASS = 1.25
LONDON_EXPAND_FAIL = 1.0
NY_IMPULSE_PASS = 1.5
NY_IMPULSE_CHOP = 1.0
# Broker server wall is UTC+3. Clock offset, not a decision.
SERVER_MINUS_HOURS = 3
TIME_UTC_SOURCE = "time_utc"

_CHOICE_CACHE: dict[str, str | None] = {}
_CHOICE_LOCK = threading.Lock()


def _challenge() -> bool:
    try:
        from .state_choices import on_challenge
    except Exception:
        return False
    try:
        return bool(on_challenge())
    except Exception:
        return False


def _choice(
    qid: str,
    facts: dict[str, Any],
    criteria: dict[str, str],
    instructions: str,
) -> str | None:
    blob = json.dumps({"q": qid, "f": facts}, sort_keys=True, default=str)
    with _CHOICE_LOCK:
        if blob in _CHOICE_CACHE:
            return _CHOICE_CACHE[blob]
    try:
        from .jev_client import evaluate
        from .jev_questions import unique_highest
    except Exception:
        return None
    questions = {
        qid: {
            "type": "choice",
            "instructions": instructions,
            "criteria": {str(key): str(text) for key, text in criteria.items()},
        }
    }
    try:
        receipt = evaluate(
            {"facts": facts, "order_send": False, "flatten": False},
            questions=questions,
            merge_sleeve=False,
            model="jev-1.13.0",
        )
    except Exception:
        return None
    block = None
    if isinstance(receipt, dict):
        answers = receipt.get("answers")
        if isinstance(answers, dict):
            block = answers.get(qid)
    probs = block.get("probabilities") if isinstance(block, dict) else None
    try:
        picked = unique_highest(probs if isinstance(probs, dict) else None, tuple(criteria))
    except Exception:
        picked = None
    with _CHOICE_LOCK:
        _CHOICE_CACHE[blob] = picked
    return picked

# Closed PACK 3 feature set. Do not silently add an eighth field here.
PACK3_FIELD_IDS = (
    "sess.ldn_ny_overlap_vol",
    "london_open_eur_gbp_expand",
    "ny_cash_open_us30",
    "corr.eur_gbp_usd_co_move",
    "corr.xau_vs_eur_proxy_usd",
    "corr.gbpjpy_risk_cross",
    "macro.boj_guidance_window",
)

ALLOWED_FAMILIES = frozenset({"admit", "size", "news_window"})
NEWS_SOURCE = "news.events"
_BOJ_TOKENS = ("boj", "bank of japan")

# London open: winter 07:00–08:59 UTC / summer 06:00–07:59 UTC (UK DST).
LONDON_OPEN_WINTER_UTC = ((7, 0), (9, 0))
LONDON_OPEN_SUMMER_UTC = ((6, 0), (8, 0))
# US30 cash open: winter 14:30 / summer 13:30 UTC (US DST). Impulse hour.
US30_OPEN_WINTER_UTC = ((14, 30), (15, 30))
US30_OPEN_SUMMER_UTC = ((13, 30), (14, 30))
# Overlap: winter 13–17 / summer 12–16 (US DST — NY cash).
OVERLAP_WINTER_UTC = (13, 17)
OVERLAP_SUMMER_UTC = (12, 16)

PACK3_FIELD_SPEC: dict[str, dict[str, Any]] = {
    "sess.ldn_ny_overlap_vol": {
        "surface": "sleeve_field",
        "kind": "score",
        "applies_symbols": ("XAUUSD", "GBPJPY", "EURUSD", "USDJPY", "GBPUSD", "EURGBP"),
        "source": TIME_UTC_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("overlap_volume",),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "geometry_vs_tape", "ids": ("FLUID-ADM-005", "SEL-V4-002")},
            {"question": "geo_size", "ids": ("FLUID-SIZ-004",)},
        ),
        "role": "DST-true London–NY overlap on time_utc. Vol stays unassembled without named M15.",
    },
    "london_open_eur_gbp_expand": {
        "surface": "sleeve_field",
        "kind": "score",
        "applies_symbols": ("EURUSD", "GBPUSD", "EURGBP", "GBPJPY"),
        "source": TIME_UTC_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("expansion_volume", "peer_ohlc"),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
            {"question": "geometry_vs_tape", "ids": ("FLUID-ADM-005",)},
            {"question": "geo_size", "ids": ("FLUID-SIZ-004",)},
        ),
        "role": "London-open expand for EUR/GBP. Pass >= 1.25, fail < 1.0. Named ratio only.",
    },
    "ny_cash_open_us30": {
        "surface": "gate_input",
        "kind": "noul",
        "applies_symbols": ("US30", "US30.cash", "US30_cash"),
        "source": TIME_UTC_SOURCE,
        "clock_true": True,
        "families": ("admit", "size"),
        "never_invent": ("US30_tape", "ENV-US30_lift"),
        "gate_inputs": (
            {"question": "session_fitness", "ids": ("FLUID-ADM-004",)},
            {"question": "session_size", "ids": ("FLUID-SIZ-003",)},
        ),
        "envelope": "ENV-US30",
        "role": "NY cash-open LABEL on time_utc. Impulse >= 1.5, chop < 1.0. ENV-US30 stays OFF.",
    },
    "corr.eur_gbp_usd_co_move": {
        "surface": "sleeve_field",
        "kind": "noul",
        "applies_symbols": ("EURUSD", "GBPJPY", "GBPUSD", "EURGBP"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "families": ("admit", "size"),
        "never_invent": ("EURUSD", "GBPUSD", "EURGBP", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
        ),
        "role": "Named EUR/GBP/USD co-move. Waits peers.peer_state. Not a refuse.",
    },
    "corr.xau_vs_eur_proxy_usd": {
        "surface": "sleeve_field",
        "kind": "noul",
        "applies_symbols": ("XAUUSD", "EURUSD"),
        "source": PEER_SOURCE,
        "clock_true": False,
        "families": ("admit", "size"),
        "never_invent": ("DXY", "EURUSD", "peer_ohlc"),
        "gate_inputs": (
            {"question": "flow_stance", "ids": ("FLUID-ADM-002",)},
            {"question": "flow_alignment", "ids": ("FLUID-ADM-003", "f5_xau_flow_alignment_size_tilt")},
            {"question": "admit", "ids": ("FLUID-ADM-007", "UB-AUTH-010")},
        ),
        "role": "Named XAU vs EUR-as-USD-proxy. Unassembled until peers.peer_state.",
    },
    "corr.gbpjpy_risk_cross": {
        "surface": "sleeve_field",
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
        "role": "GBPJPY risk-cross vs named legs. Residual cap 0.15 GJ. Not a refuse.",
    },
    "macro.boj_guidance_window": {
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
        "role": "BOJ guidance timing LABEL on the existing F5 window. Empty spine stays unassembled.",
    },
}


def _norm_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper().replace(" ", "")


def field_applies(field_id: str, symbol: str) -> bool:
    spec = PACK3_FIELD_SPEC[field_id]
    want = {_norm_symbol(s) for s in spec["applies_symbols"]}
    have = _norm_symbol(symbol)
    if have in want:
        return True
    stripped = have.replace(".CASH", "").replace("_CASH", "")
    return stripped in want


def _nth_sunday(year: int, month: int, n: int) -> datetime:
    first = datetime(year, month, 1, tzinfo=timezone.utc)
    first_sun = 1 + (6 - first.weekday()) % 7
    return datetime(year, month, first_sun + 7 * (n - 1), tzinfo=timezone.utc)


def _last_sunday(year: int, month: int) -> datetime:
    if month == 12:
        nxt = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        nxt = datetime(year, month + 1, 1, tzinfo=timezone.utc)
    last = nxt - timedelta(days=1)
    return last - timedelta(days=(last.weekday() - 6) % 7)


def us_dst(as_of: datetime) -> bool:
    """US DST: second Sunday March 07:00 UTC → first Sunday November 06:00 UTC."""
    as_of = _as_utc(as_of)
    start = _nth_sunday(as_of.year, 3, 2).replace(hour=7)
    end = _nth_sunday(as_of.year, 11, 1).replace(hour=6)
    return start <= as_of < end


def uk_dst(as_of: datetime) -> bool:
    """UK DST: last Sunday March 01:00 UTC → last Sunday October 01:00 UTC."""
    as_of = _as_utc(as_of)
    start = _last_sunday(as_of.year, 3).replace(hour=1)
    end = _last_sunday(as_of.year, 10).replace(hour=1)
    return start <= as_of < end


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def time_utc_from_server(server_time: datetime) -> datetime:
    """PACK 3 clocks are time_utc only. Server wall = UTC + 3h → subtract 3."""
    raw = _as_utc(server_time)
    return raw - timedelta(hours=SERVER_MINUS_HOURS)


def coerce_time_utc(
    time_utc: datetime | None = None,
    *,
    server_time: datetime | None = None,
) -> datetime:
    """Prefer time_utc. Fall back to server−3h. Never read broker_hour."""
    if time_utc is not None:
        return _as_utc(time_utc)
    if server_time is not None:
        return time_utc_from_server(server_time)
    raise ValueError("PACK 3 clocks need time_utc (or server_time for server−3h)")


def _minutes(as_of: datetime) -> int:
    return as_of.hour * 60 + as_of.minute


def _in_hm_window(as_of: datetime, start: tuple[int, int], end: tuple[int, int]) -> bool:
    now = _minutes(as_of)
    lo = start[0] * 60 + start[1]
    hi = end[0] * 60 + end[1]
    return lo <= now < hi


def london_open_window(as_of: datetime) -> tuple[tuple[int, int], tuple[int, int]]:
    return LONDON_OPEN_SUMMER_UTC if uk_dst(as_of) else LONDON_OPEN_WINTER_UTC


def us30_open_window(as_of: datetime) -> tuple[tuple[int, int], tuple[int, int]]:
    return US30_OPEN_SUMMER_UTC if us_dst(as_of) else US30_OPEN_WINTER_UTC


def overlap_window(as_of: datetime) -> tuple[int, int]:
    return OVERLAP_SUMMER_UTC if us_dst(as_of) else OVERLAP_WINTER_UTC


def in_london_open(as_of: datetime) -> bool | None:
    as_of = _as_utc(as_of)
    start, end = london_open_window(as_of)
    from .state_choices import LEGACY, window_bool

    chosen = window_bool(
        "pack3.in_london_open",
        {
            "hour": as_of.hour,
            "minute": as_of.minute,
            "window_start_hm": list(start),
            "window_end_hm": list(end),
        },
        "Is the clock inside the London open window, start inclusive and end exclusive?",
    )
    if chosen is not LEGACY:
        return chosen
    return _in_hm_window(as_of, start, end)


def in_us30_cash_open(as_of: datetime) -> bool | None:
    as_of = _as_utc(as_of)
    start, end = us30_open_window(as_of)
    from .state_choices import LEGACY, window_bool

    chosen = window_bool(
        "pack3.in_us30_cash_open",
        {
            "hour": as_of.hour,
            "minute": as_of.minute,
            "window_start_hm": list(start),
            "window_end_hm": list(end),
        },
        "Is the clock inside the US30 cash-open window, start inclusive and end exclusive?",
    )
    if chosen is not LEGACY:
        return chosen
    return _in_hm_window(as_of, start, end)


def in_ldn_ny_overlap(as_of: datetime) -> bool | None:
    as_of = _as_utc(as_of)
    lo, hi = overlap_window(as_of)
    from .state_choices import LEGACY, window_bool

    chosen = window_bool(
        "pack3.in_ldn_ny_overlap",
        {"hour": as_of.hour, "window_start_hour": lo, "window_end_hour": hi},
        "Is hour inside the London-New York overlap, start inclusive and end exclusive?",
    )
    if chosen is not LEGACY:
        return chosen
    return lo <= as_of.hour < hi


def classify_london_expand(ratio: float | None) -> str | None:
    if ratio is None:
        return None
    value = float(ratio)
    if _challenge():
        return _choice(
            "pack3.london_expand",
            {"ratio": value},
            {
                "pass": "This expansion is a pass.",
                "fail": "This expansion is a fail.",
                "mid": "This expansion is neither a pass nor a fail.",
            },
            (
                "The expansion ratio is on the card. "
                "The unique highest class is the decision. "
                "An empty answer or a tie leaves the class unset. Do not send."
            ),
        )
    if value >= LONDON_EXPAND_PASS:
        return "pass"
    if value < LONDON_EXPAND_FAIL:
        return "fail"
    return "mid"


def classify_ny_impulse(ratio: float | None) -> str | None:
    if ratio is None:
        return None
    value = float(ratio)
    if _challenge():
        return _choice(
            "pack3.ny_impulse",
            {"ratio": value},
            {
                "impulse": "This impulse is an impulse.",
                "chop": "This impulse is chop.",
                "mid": "This impulse is neither impulse nor chop.",
            },
            (
                "The impulse ratio is on the card. "
                "The unique highest class is the decision. "
                "An empty answer or a tie leaves the class unset. Do not send."
            ),
        )
    if value >= NY_IMPULSE_PASS:
        return "impulse"
    if value < NY_IMPULSE_CHOP:
        return "chop"
    return "mid"


def classify_gj_residual(residual: float | None) -> str | None:
    if residual is None:
        return None
    magnitude = abs(float(residual))
    if _challenge():
        return _choice(
            "pack3.gj_residual",
            {"abs_residual": magnitude},
            {
                "fail": "This residual fails.",
                "pass": "This residual passes.",
            },
            (
                "The absolute residual is on the card. "
                "The unique highest class is the decision. "
                "An empty answer or a tie leaves the class unset. Do not send."
            ),
        )
    return "fail" if magnitude > RESID_CAP else "pass"


def pack3_gate_map() -> list[dict[str, Any]]:
    rows = []
    for field_id in PACK3_FIELD_IDS:
        spec = PACK3_FIELD_SPEC[field_id]
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


def assert_pack3_maps_existing_families() -> dict[str, Any]:
    """Every PACK 3 gate id must already exist and sit in ADM / SIZ / NWS."""
    bad: list[str] = []
    for row in pack3_gate_map():
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
    return {
        "ok": not bad,
        "bad": bad,
        "n": len(PACK3_FIELD_IDS),
        "families": sorted(ALLOWED_FAMILIES),
        "constants": locked_constants(),
    }


def locked_constants() -> dict[str, Any]:
    """Clock facts only. The class is not a number in this map."""
    return {
        "clock_source": TIME_UTC_SOURCE,
        "server_minus_hours": SERVER_MINUS_HOURS,
        "london_open_winter_utc": "07:00-08:59",
        "london_open_summer_utc": "06:00-07:59",
        "us30_open_winter_utc": "14:30",
        "us30_open_summer_utc": "13:30",
        "overlap_winter_utc": "13-17",
        "overlap_summer_utc": "12-16",
    }


def _row(
    field_id: str,
    *,
    applies: bool,
    assembled: bool,
    value: Any,
    source: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    spec = PACK3_FIELD_SPEC[field_id]
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
    """Named BOJ timing only. Empty spine → unassembled. Never invent."""
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
        return {"in_window": False, "named_boj": False, "event": None, "minutes_from_as_of": None}
    in_win = any(hit for hit, _ in hits)
    ev = next((row for hit, row in hits if hit), hits[0][1])
    return {
        "in_window": in_win,
        "named_boj": True,
        "event": ev.get("event"),
        "currency": ev.get("currency"),
        "impact": ev.get("impact"),
        "minutes_from_as_of": ev.get("minutes_from_as_of"),
    }


def assemble_pack3_fields(
    *,
    symbol: str,
    time_utc: datetime | None = None,
    server_time: datetime | None = None,
    peer_state: Mapping[str, Any] | None = None,
    pack3_values: Mapping[str, Any] | None = None,
    news: Mapping[str, Any] | None = None,
    m15_vol: float | None = None,
) -> dict[str, Any]:
    """Assemble the closed PACK 3 set. Missing peers / empty spine stay visible."""
    as_of = coerce_time_utc(time_utc, server_time=server_time)
    supplied = dict(pack3_values or {})
    peers = dict(peer_state or {})
    fields: dict[str, Any] = {}

    from concurrent.futures import ThreadPoolExecutor

    vol = supplied.get("sess.ldn_ny_overlap_vol")
    named_vol = None
    overlap_override = None
    if isinstance(vol, Mapping):
        named_vol = vol.get("vol")
        if "in_window" in vol:
            overlap_override = bool(vol.get("in_window"))
    else:
        named_vol = vol if isinstance(vol, (int, float)) else m15_vol

    raw_expand = supplied.get("london_open_eur_gbp_expand")
    named_ratio = None
    london_override = None
    if isinstance(raw_expand, Mapping):
        if "in_window" in raw_expand:
            london_override = bool(raw_expand.get("in_window"))
        named_ratio = raw_expand.get("ratio")
    elif isinstance(raw_expand, (int, float)):
        named_ratio = float(raw_expand)

    raw_ny = supplied.get("ny_cash_open_us30")
    named_impulse = None
    ny_override = None
    if isinstance(raw_ny, Mapping):
        if "in_window" in raw_ny:
            ny_override = bool(raw_ny.get("in_window"))
        named_impulse = raw_ny.get("impulse")
    elif isinstance(raw_ny, (int, float)):
        named_impulse = float(raw_ny)
    elif isinstance(raw_ny, bool):
        ny_override = raw_ny

    raw_cross = supplied.get("corr.gbpjpy_risk_cross")
    residual = supplied.get("residual")
    dual = supplied.get("dual_leg_agree")
    if raw_cross is None:
        raw_cross = _named_from_peer(peers, "corr.gbpjpy_risk_cross")
    if isinstance(raw_cross, Mapping):
        residual = raw_cross.get("residual", residual)
        dual = raw_cross.get("dual_leg_agree", dual)
        cross_value = raw_cross.get("value", raw_cross.get("agree"))
    else:
        cross_value = raw_cross
    if dual is None:
        dual = _named_from_peer(peers, "gbpjpy_dual_leg_agree")

    with ThreadPoolExecutor(max_workers=6) as pool:
        fut_overlap = pool.submit(in_ldn_ny_overlap, as_of)
        fut_london = pool.submit(in_london_open, as_of)
        fut_us30 = pool.submit(in_us30_cash_open, as_of)
        fut_expand = pool.submit(classify_london_expand, named_ratio)
        fut_impulse = pool.submit(classify_ny_impulse, named_impulse)
        fut_residual = pool.submit(
            classify_gj_residual,
            residual if isinstance(residual, (int, float)) else None,
        )
        in_overlap = fut_overlap.result()
        in_ldn = fut_london.result()
        in_open = fut_us30.result()
        expand_class = fut_expand.result()
        impulse_class = fut_impulse.result()
        residual_class = fut_residual.result()

    from .state_choices import on_challenge

    if not on_challenge():
        if overlap_override is not None:
            in_overlap = overlap_override
        if london_override is not None:
            in_ldn = london_override
        if ny_override is not None:
            in_open = ny_override

    applies = field_applies("sess.ldn_ny_overlap_vol", symbol)
    lo, hi = overlap_window(as_of)
    fields["sess.ldn_ny_overlap_vol"] = _row(
        "sess.ldn_ny_overlap_vol",
        applies=applies,
        assembled=applies,
        value={
            "in_window": in_overlap if applies else None,
            "vol": named_vol if applies else None,
            "window_utc": [lo, hi],
            "season": "summer" if us_dst(as_of) else "winter",
            "clock_source": TIME_UTC_SOURCE,
        }
        if applies
        else None,
        source=TIME_UTC_SOURCE,
        extra={"vol_assembled": named_vol is not None},
    )

    applies = field_applies("london_open_eur_gbp_expand", symbol)
    in_ldn = in_london_open(as_of)
    raw_expand = supplied.get("london_open_eur_gbp_expand")
    named_ratio = None
    if isinstance(raw_expand, Mapping):
        from .state_choices import on_challenge

        if not on_challenge() and "in_window" in raw_expand:
            in_ldn = bool(raw_expand.get("in_window"))
        named_ratio = raw_expand.get("ratio")
    elif isinstance(raw_expand, (int, float)):
        named_ratio = float(raw_expand)
    expand_class = classify_london_expand(named_ratio)
    start, end = london_open_window(as_of)
    fields["london_open_eur_gbp_expand"] = _row(
        "london_open_eur_gbp_expand",
        applies=applies,
        assembled=applies,
        value={
            "in_window": in_ldn if applies else None,
            "ratio": named_ratio if applies else None,
            "class": expand_class if applies else None,
            "window_utc": [list(start), list(end)],
            "season": "summer" if uk_dst(as_of) else "winter",
            "clock_source": TIME_UTC_SOURCE,
        }
        if applies
        else None,
        source=TIME_UTC_SOURCE,
        extra={"ratio_assembled": named_ratio is not None},
    )

    applies = field_applies("ny_cash_open_us30", symbol)
    in_open = in_us30_cash_open(as_of)
    raw_ny = supplied.get("ny_cash_open_us30")
    named_impulse = None
    if isinstance(raw_ny, Mapping):
        from .state_choices import on_challenge

        if not on_challenge() and "in_window" in raw_ny:
            in_open = bool(raw_ny.get("in_window"))
        named_impulse = raw_ny.get("impulse")
    elif isinstance(raw_ny, (int, float)):
        named_impulse = float(raw_ny)
    elif isinstance(raw_ny, bool):
        from .state_choices import on_challenge

        if not on_challenge():
            in_open = raw_ny
    impulse_class = classify_ny_impulse(named_impulse)
    start, end = us30_open_window(as_of)
    fields["ny_cash_open_us30"] = _row(
        "ny_cash_open_us30",
        applies=applies,
        assembled=applies,
        value={
            "in_window": in_open if applies else None,
            "impulse": named_impulse if applies else None,
            "class": impulse_class if applies else None,
            "open_utc": "13:30" if us_dst(as_of) else "14:30",
            "window_utc": [list(start), list(end)],
            "season": "summer" if us_dst(as_of) else "winter",
            "clock_source": TIME_UTC_SOURCE,
        }
        if applies
        else None,
        source=TIME_UTC_SOURCE,
        extra={
            "envelope": "ENV-US30",
            "envelope_stays": "integer_off",
            "impulse_assembled": named_impulse is not None,
        },
    )

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

    applies = field_applies("corr.gbpjpy_risk_cross", symbol)
    raw_cross = supplied.get("corr.gbpjpy_risk_cross")
    residual = supplied.get("residual")
    dual = supplied.get("dual_leg_agree")
    if raw_cross is None:
        raw_cross = _named_from_peer(peers, "corr.gbpjpy_risk_cross")
    if isinstance(raw_cross, Mapping):
        residual = raw_cross.get("residual", residual)
        dual = raw_cross.get("dual_leg_agree", dual)
        value = raw_cross.get("value", raw_cross.get("agree"))
    else:
        value = raw_cross
    if dual is None:
        dual = _named_from_peer(peers, "gbpjpy_dual_leg_agree")
    residual_class = classify_gj_residual(residual if isinstance(residual, (int, float)) else None)
    assembled_cross = value is not None or dual is not None or residual is not None
    fields["corr.gbpjpy_risk_cross"] = _row(
        "corr.gbpjpy_risk_cross",
        applies=applies,
        assembled=applies and assembled_cross,
        value={
            "agree": value,
            "dual_leg_agree": dual,
            "residual": residual,
            "residual_class": residual_class,
        }
        if applies and assembled_cross
        else None,
        source=PEER_SOURCE if applies else "not_applicable",
    )

    applies = field_applies("macro.boj_guidance_window", symbol)
    boj = supplied.get("macro.boj_guidance_window")
    if isinstance(boj, Mapping):
        boj_row = dict(boj)
    elif boj is not None:
        boj_row = {"in_window": bool(boj), "named_boj": True, "event": None, "minutes_from_as_of": None}
    else:
        boj_row = _boj_from_news(news)
    fields["macro.boj_guidance_window"] = _row(
        "macro.boj_guidance_window",
        applies=applies,
        assembled=applies and boj_row is not None,
        value=(boj_row.get("in_window") if isinstance(boj_row, Mapping) else None) if applies else None,
        source=NEWS_SOURCE if applies else "not_applicable",
        extra={
            "named_boj": (boj_row or {}).get("named_boj") if isinstance(boj_row, Mapping) else None,
            "event": (boj_row or {}).get("event") if isinstance(boj_row, Mapping) else None,
            "minutes_from_as_of": (boj_row or {}).get("minutes_from_as_of")
            if isinstance(boj_row, Mapping)
            else None,
            "never_refuse": True,
        },
    )

    missing = [
        f"pack3_fields.{fid}"
        for fid in PACK3_FIELD_IDS
        if fields[fid]["applies"] and not fields[fid]["assembled"]
    ]
    return {
        "schema": SCHEMA,
        "origin": ORIGIN,
        "shadow_only": True,
        "never_apply_size": True,
        "never_refuse": True,
        "n": len(PACK3_FIELD_IDS),
        "ids": list(PACK3_FIELD_IDS),
        "fields": fields,
        "n_applies": sum(1 for fid in PACK3_FIELD_IDS if fields[fid]["applies"]),
        "n_assembled": sum(1 for fid in PACK3_FIELD_IDS if fields[fid]["assembled"]),
        "invented": False,
        "missing_fields": missing,
        "families": sorted(ALLOWED_FAMILIES),
        "constants": locked_constants(),
        "time_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "clock_source": TIME_UTC_SOURCE,
    }


def pack3_clock_assembled(pack3: Mapping[str, Any] | None) -> bool:
    if not pack3:
        return False
    fields = pack3.get("fields") if isinstance(pack3.get("fields"), Mapping) else {}
    clockish = (
        "sess.ldn_ny_overlap_vol",
        "london_open_eur_gbp_expand",
        "ny_cash_open_us30",
    )
    return any((fields.get(fid) or {}).get("assembled") for fid in clockish)


# GBPJPY fixture vectors. Chair lock: t1 pass, t2 dual_split fail, t4 residual fail.
# t3 is an alias of t4 (Chair lock used t3 for residual; owner brief named t4).
_T1 = {
    "id": "t1",
    "symbol": "GBPJPY",
    "verdict": "pass",
    "fail_reason": None,
    "time_utc": "2026-01-15T07:30:00Z",
    "dual_leg_agree": True,
    "gbpusd_side": "long",
    "usdjpy_side": "long",
    "gbpjpy_side": "long",
    "residual": 0.08,
    "london_expand": 1.40,
    "corr.gbpjpy_risk_cross": "agree",
    "corr.eur_gbp_usd_co_move": True,
}
_T2 = {
    "id": "t2",
    "symbol": "GBPJPY",
    "verdict": "fail",
    "fail_reason": "dual_split",
    "time_utc": "2026-01-15T07:30:00Z",
    "dual_leg_agree": False,
    "gbpusd_side": "long",
    "usdjpy_side": "short",
    "gbpjpy_side": "long",
    "residual": 0.04,
    "london_expand": 1.40,
    "corr.gbpjpy_risk_cross": "disagree",
    "corr.eur_gbp_usd_co_move": False,
}
_T4 = {
    "id": "t4",
    "symbol": "GBPJPY",
    "verdict": "fail",
    "fail_reason": "residual",
    "time_utc": "2026-01-15T07:30:00Z",
    "dual_leg_agree": True,
    "gbpusd_side": "long",
    "usdjpy_side": "long",
    "gbpjpy_side": "long",
    "residual": 0.22,
    "london_expand": 1.40,
    "corr.gbpjpy_risk_cross": "agree",
    "corr.eur_gbp_usd_co_move": True,
}

GBPJPY_FIXTURE_VECTORS: dict[str, dict[str, Any]] = {
    "t1": dict(_T1),
    "t2": dict(_T2),
    "t4": dict(_T4),
    "t3": {**_T4, "id": "t3", "alias_of": "t4"},
}


def gbpjpy_fixture(vector_id: str) -> dict[str, Any]:
    row = GBPJPY_FIXTURE_VECTORS.get(str(vector_id).lower())
    if row is None:
        raise KeyError(vector_id)
    return dict(row)


def score_gbpjpy_fixture(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    """SHADOW scorer for the locked GBPJPY vectors. Never refuses. Never APPLY."""
    vec = gbpjpy_fixture(vector) if isinstance(vector, str) else dict(vector)
    dual = bool(vec.get("dual_leg_agree"))
    try:
        resid = abs(float(vec["residual"]))
    except (TypeError, ValueError, KeyError):
        resid = None
    expand = vec.get("london_expand")
    try:
        expand_f = float(expand) if expand is not None else None
    except (TypeError, ValueError):
        expand_f = None
    if _challenge():
        picked = _choice(
            "pack3.gbpjpy_verdict",
            {"dual_leg_agree": dual, "abs_residual": resid},
            {
                "pass": "The dual leg agrees and the residual does not fail.",
                "dual_split": "The dual leg does not agree.",
                "residual": "The residual fails.",
            },
            (
                "Dual agreement and the absolute residual are on the card. "
                "The unique highest verdict is the decision. "
                "An empty answer or a tie leaves the verdict unset. Do not send."
            ),
        )
        if picked == "dual_split":
            verdict, reason = "fail", "dual_split"
        elif picked == "residual":
            verdict, reason = "fail", "residual"
        elif picked == "pass":
            verdict, reason = "pass", None
        else:
            verdict, reason = None, None
    elif not dual:
        verdict = "fail"
        reason = "dual_split"
    elif resid is not None and resid > RESID_CAP:
        verdict = "fail"
        reason = "residual"
    else:
        verdict = "pass"
        reason = None
    return {
        "id": vec.get("id"),
        "symbol": "GBPJPY",
        "verdict": verdict,
        "fail_reason": reason,
        "expected_verdict": vec.get("verdict"),
        "expected_fail_reason": vec.get("fail_reason"),
        "matches_lock": verdict == vec.get("verdict") and reason == vec.get("fail_reason"),
        "dual_leg_agree": dual,
        "residual": resid,
        "residual_class": classify_gj_residual(resid),
        "london_expand": expand_f,
        "london_expand_class": classify_london_expand(expand_f),
        "shadow_only": True,
        "never_refuse": True,
        "never_apply_size": True,
        "invented": False,
    }


def values_from_gbpjpy_fixture(vector: str | Mapping[str, Any]) -> dict[str, Any]:
    """Named pack3_values for a locked GBPJPY vector. No invented OHLC."""
    vec = gbpjpy_fixture(vector) if isinstance(vector, str) else dict(vector)
    return {
        "london_open_eur_gbp_expand": vec.get("london_expand"),
        "corr.eur_gbp_usd_co_move": vec.get("corr.eur_gbp_usd_co_move"),
        "corr.gbpjpy_risk_cross": {
            "agree": vec.get("corr.gbpjpy_risk_cross"),
            "dual_leg_agree": vec.get("dual_leg_agree"),
            "residual": vec.get("residual"),
        },
        "dual_leg_agree": vec.get("dual_leg_agree"),
        "residual": vec.get("residual"),
    }
