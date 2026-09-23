"""Chair synthesis sleeve fields — first-class inputs on the 48-gate pipe.

Owner / Chair 2026-09-18. SHADOW only. Each field is a named sleeve hook that
existing fluid questions may read. No new gates. No APPLY. No invented DXY,
funding, peer OHLC, or US30 lift.
"""

from __future__ import annotations

import threading
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
# pack2_fields still imports these names. The live assembly does not read them.
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



def _card_var():
    var = globals().get("_OBSERVE_CARD")
    if var is None:
        import contextvars

        var = contextvars.ContextVar("observe_card_" + __name__, default=None)
        globals()["_OBSERVE_CARD"] = var
    return var


def _bind_card(state):
    """The card whose facts may anchor an amount. A miss binds nothing."""

    try:
        from collections.abc import Mapping
    except Exception:
        return None
    card = state if isinstance(state, Mapping) else None
    return _card_var().set(card)


def _bound_card():
    try:
        return _card_var().get()
    except Exception:
        return None


_ORDINAL_WIDTH: dict[str, int] = {}
_AMOUNT_UNIT: dict[str, str] = {}
_ORDINAL_WORDS = ("none", "trace", "small", "modest", "notable", "heavy")
_PRICE_KEYS = {
    "entry",
    "stop",
    "target",
    "bid",
    "ask",
    "price",
    "sl",
    "tp",
    "open",
    "high",
    "low",
    "close",
    "limit_price",
}
_MONEY_KEYS = {
    "equity",
    "balance",
    "open_pnl",
    "profit",
    "day_start_balance",
    "day_start_equity",
    "realized_closed_profit",
    "day_equity",
    "broker_net",
    "mean_net",
    "realized",
}
_SKIP_WALK = {
    "prior_outcomes",
    "questions",
    "answers",
    "probabilities",
    "criteria",
    "instructions",
}


def _anchor_finite(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    banned = globals().get("_banned_number")
    if callable(banned):
        try:
            if banned(number):
                return None
        except Exception:
            return None
    return number


def _label_ok(text: str) -> bool:
    if not text or not str(text).strip():
        return False
    sample = str(text)
    for name, bad in (
        ("_limit_key", True),
        ("_banned_text", True),
        ("_blocked_text", True),
        ("_text_banned", True),
        ("_skip_key", True),
    ):
        fn = globals().get(name)
        if not callable(fn):
            continue
        try:
            if bool(fn(sample)) is bad:
                return False
        except Exception:
            return False
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            if scrub(sample) is None:
                return False
        except Exception:
            return False
    ok = globals().get("_question_text_ok")
    if callable(ok):
        try:
            if not ok(sample):
                return False
        except Exception:
            return False
    return True


def _amount_unit(qid: str, text: str = "") -> str | None:
    """The unit this score returns. None means the score is an ordinal."""

    name = str(qid).lower()
    if name.endswith("_hour") or name.endswith("_hours"):
        return "hours"
    if "minute" in name and not name.endswith("_parameter"):
        return "minutes"
    tokens = name.replace(".", "_").split("_")
    if (
        "lot" in tokens
        or "lots" in tokens
        or name.endswith("_lot")
        or name.endswith("_lots")
        or name.endswith("min_lot")
    ):
        return "lots"
    if "persist" in name or name.endswith("_weight"):
        return "weight"
    if "ceiling" in name:
        return "size"
    if "concurrent" in name:
        return "count"
    if name.endswith("_net") or "broker_net" in name:
        return "money"
    if (
        "prob" in name
        or ".p_" in name
        or "p_time" in name
        or "p_positive" in name
    ):
        return "probability"
    if (
        "plan_r" in name
        or "mean_r" in name
        or name.endswith("_r")
        or "predicted_e_r" in name
    ):
        return "r"
    if "fitness" in name or name.endswith("_fit"):
        return None
    if "expected_" in name:
        return "count"
    tail = name.rsplit(".", 1)[-1]
    tail_tokens = tail.split("_")
    if (
        tail.endswith("_loop")
        or tail.endswith("_loop_bound")
        or tail == "loop"
        or "retry" in tail_tokens
        or "walk_depth" in tail
        or "posts" in tail_tokens
        or "min_n" in tail
        or tail.endswith("_count")
        or tail.endswith("_n")
    ):
        return "count"
    if "window" in name:
        return "window"
    if "threshold" in name:
        return "price"
    blob = name + "\n" + str(text).lower()
    if "stop or target" in blob or "the stop" in blob or "the target" in blob:
        return "price"
    if "e[r]" in blob or "mean r" in blob:
        return "r"
    if "broker net" in blob:
        return "money"
    if "the lot " in blob or blob.rstrip(".").endswith("the lot"):
        return "lots"
    if "fluid count" in blob or "envelope count" in blob or "promotion count" in blob:
        return "count"
    if "how many" in blob:
        return "count"
    if name.startswith("a1_") and name.endswith("_parameter"):
        return "price"
    return None


def _is_ordinal(qid: str) -> bool:
    """True when this id was built as words, or no amount unit is known."""

    key = str(qid)
    if key in _AMOUNT_UNIT:
        return False
    if key in _ORDINAL_WIDTH:
        return True
    return _amount_unit(key, "") is None


def _key_unit(name: str, unit: str) -> bool:
    low = str(name).lower()
    if unit == "price":
        return low in _PRICE_KEYS
    if unit == "hours":
        return low == "hour" or low.endswith("_hour") or low.endswith("_hours")
    if unit == "minutes":
        return low == "minute" or low.endswith("_minute") or low.endswith("_minutes") or low.endswith("_min")
    if unit == "seconds":
        return "second" in low or low in {"age_s", "seconds_until_cycle"}
    if unit == "lots":
        return low in {"volume", "volume_min", "volume_step", "lot", "lots", "min_lot"} or low.endswith("_lot") or low.endswith("_lots")
    if unit == "r":
        return low.endswith("_r") or low in {"plan_r", "locked_r", "mean_r"}
    if unit == "weight":
        return low == "weight" or low.endswith("_weight")
    if unit == "money":
        return low in _MONEY_KEYS
    if unit == "probability":
        return "prob" in low or low.startswith("p_") or "p_time" in low or "p_positive" in low
    if unit == "count":
        return low in {"n", "asked", "step_index"} or low.startswith("n_") or low.endswith("_count") or low.endswith("_len") or low.endswith("_posts")
    if unit == "multiple":
        return low.endswith("_mult") or low.endswith("_multiple")
    return False


def _walk_pairs(state, unit: str) -> list[tuple[str, float]]:
    found: list[tuple[str, float]] = []

    def walk(blob, depth: int) -> None:
        if depth > 4 or not isinstance(blob, dict):
            return
        for key, value in blob.items():
            name = str(key)
            if name in _SKIP_WALK or name.startswith("_"):
                continue
            if not _label_ok(name):
                continue
            if isinstance(value, dict):
                walk(value, depth + 1)
                continue
            if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
                if unit == "count":
                    found.append((f"the count of {name} named on this card", float(len(value))))
                continue
            if unit == "count" and not _key_unit(name, unit):
                continue
            if unit != "count" and not _key_unit(name, unit):
                continue
            number = _anchor_finite(value)
            if number is None:
                continue
            found.append((f"the {name} named on this card", number))

    if isinstance(state, dict):
        walk(state, 0)
    return found


def _distinct(pairs) -> int:
    seen = []
    for _label, value in pairs:
        if value not in seen:
            seen.append(value)
    return len(seen)


def _anchors_for(state, unit: str) -> list[tuple[str, float]]:
    card = state if isinstance(state, dict) else {}
    if unit == "count":
        extra = []
        try:
            from .jev_questions import count_anchors

            extra = list(count_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import count_anchors

                extra = list(count_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "count")
    if unit == "money":
        extra = []
        try:
            from .jev_questions import usd_anchors

            extra = list(usd_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import usd_anchors

                extra = list(usd_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "money")
    if unit == "minutes":
        extra = []
        try:
            from .jev_questions import minute_anchors

            extra = list(minute_anchors(card) or [])
        except Exception:
            try:
                from src.judgment.jev_questions import minute_anchors

                extra = list(minute_anchors(card) or [])
            except Exception:
                extra = []
        return list(extra) + _walk_pairs(card, "minutes")
    if unit == "size":
        lots = _walk_pairs(card, "lots")
        multiples = _walk_pairs(card, "multiple")
        try:
            from .jev_questions import mult_anchors

            multiples = list(mult_anchors(card) or []) + multiples
        except Exception:
            try:
                from src.judgment.jev_questions import mult_anchors

                multiples = list(mult_anchors(card) or []) + multiples
            except Exception:
                pass
        if _distinct(lots) >= 2:
            return lots
        if _distinct(multiples) >= 2:
            return multiples
        return []
    if unit == "window":
        minutes = _walk_pairs(card, "minutes")
        seconds = _walk_pairs(card, "seconds")
        if _distinct(minutes) >= 2:
            return minutes
        return seconds
    return _walk_pairs(card, unit)


def _custom_words(words) -> bool:
    """A scale of words is an ordinal. The generic parameter menu is not."""

    if not words:
        return False
    texts = []
    numeric = 0
    for item in words:
        text = str(item).strip()
        if not text:
            continue
        try:
            float(text)
            numeric += 1
        except (TypeError, ValueError):
            pass
        texts.append(text)
    if len(texts) < 2 or numeric == len(texts):
        return False
    generic = {
        ("none", "trace", "small", "modest", "notable", "heavy"),
        (
            "below the levels on this state",
            "between the levels on this state",
            "above the levels on this state",
        ),
    }
    return tuple(texts) not in generic


def _word_levels(words) -> list[str]:
    if not words:
        return list(_ORDINAL_WORDS)
    texts = []
    numeric = 0
    for item in words:
        text = str(item).strip()
        if not text:
            continue
        try:
            float(text)
            numeric += 1
        except (TypeError, ValueError):
            pass
        texts.append(text)
    if texts and numeric == len(texts):
        return [item for item in _ORDINAL_WORDS if _label_ok(item)]
    kept = [item for item in texts if _label_ok(item)]
    if len(kept) >= 2:
        return kept
    return [item for item in _ORDINAL_WORDS if _label_ok(item)]


def _jev_amount(qid, text, anchors):
    try:
        from .jev_questions import amount_question

        return amount_question(qid, text, anchors)
    except Exception:
        from src.judgment.jev_questions import amount_question

        return amount_question(qid, text, anchors)


def _jev_ordinal(qid, text, levels):
    try:
        from .jev_questions import ordinal_question

        return ordinal_question(qid, text, levels)
    except Exception:
        from src.judgment.jev_questions import ordinal_question

        return ordinal_question(qid, text, levels)


def _shape_score(qid: str, instructions: str, words=None, *, wrapped: bool = True):
    """An amount posts only with two anchors. An ordinal keeps its words."""

    text = str(instructions or "").strip()
    scrub = globals().get("_scrub_text")
    if callable(scrub):
        try:
            cleaned = scrub(text)
        except Exception:
            return {}
        if not isinstance(cleaned, str) or not cleaned.strip():
            return {}
        text = cleaned.strip()
    if not text or not _label_ok(text):
        return {}
    unit = None if _custom_words(words) else _amount_unit(qid, text)
    try:
        if unit is None:
            built = _jev_ordinal(qid, text, _word_levels(words))
        else:
            anchors = [
                (label, value)
                for label, value in _anchors_for(_bound_card(), unit)
                if _label_ok(label)
            ]
            built = _jev_amount(qid, text, anchors)
    except Exception:
        return {}
    row = built.get(str(qid)) if isinstance(built, dict) else None
    if not isinstance(row, dict):
        return {}
    for key in ("answer", "choice", "score", "value", "noul", "probabilities", "default"):
        row.pop(key, None)
    criteria = row.get("criteria")
    if not isinstance(criteria, list) or len(criteria) < 2:
        return {}
    if unit is None:
        _ORDINAL_WIDTH[str(qid)] = len(criteria)
        _AMOUNT_UNIT.pop(str(qid), None)
    else:
        _AMOUNT_UNIT[str(qid)] = unit
        _ORDINAL_WIDTH.pop(str(qid), None)
    row["type"] = "score"
    row["instructions"] = text
    if wrapped:
        return {str(qid): row}
    return row


def _ordinal_read(block, qid: str):
    """Nearest word. The index is not an amount. A miss stays unset."""

    width = _ORDINAL_WIDTH.get(str(qid))
    if not isinstance(width, int) or width < 2:
        criteria = block.get("criteria") if isinstance(block, dict) else None
        if isinstance(criteria, list) and len(criteria) >= 2:
            width = len(criteria)
        else:
            probs = block.get("probabilities") if isinstance(block, dict) else None
            if isinstance(probs, dict) and len(probs) >= 2:
                width = len(probs)
    if not isinstance(width, int) or width < 2:
        return None
    try:
        from .jev_questions import ordinal_index
    except Exception:
        try:
            from src.judgment.jev_questions import ordinal_index
        except Exception:
            return None
    try:
        return ordinal_index(block, width)
    except Exception:
        return None

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


_MODEL = "jev-1.13.0"
_UNSET = " An empty score leaves it unset. A tie leaves it unset. An error leaves it unset."
_CLOCK_LOCK = threading.Lock()
_CLOCK_CACHE: dict[tuple, dict[str, Any]] = {}
_CLOCK_SPOTS = (
    "us30_start_hour",
    "us30_start_minute",
    "us30_end_hour",
    "us30_end_minute",
    "overlap_start_hour",
    "overlap_end_hour",
    "tokyo_start_hour",
    "tokyo_start_minute",
    "tokyo_end_hour",
    "tokyo_end_minute",
    "london_fit",
)
_CLOCK_TEXT = {
    "us30_start_hour": "The score you return is the UTC hour when the US30 regular session starts.",
    "us30_start_minute": "The score you return is the minute within that hour when the US30 regular session starts.",
    "us30_end_hour": "The score you return is the UTC hour when the US30 regular session ends, exclusive.",
    "us30_end_minute": "The score you return is the minute within that hour when the US30 regular session ends, exclusive.",
    "overlap_start_hour": "The score you return is the UTC hour when the London and New York overlap starts.",
    "overlap_end_hour": "The score you return is the UTC hour when the London and New York overlap ends, exclusive.",
    "tokyo_start_hour": "The score you return is the UTC hour when the Tokyo fix window starts.",
    "tokyo_start_minute": "The score you return is the minute within that hour when the Tokyo fix window starts.",
    "tokyo_end_hour": "The score you return is the UTC hour when the Tokyo fix window ends, exclusive.",
    "tokyo_end_minute": "The score you return is the minute within that hour when the Tokyo fix window ends, exclusive.",
    "london_fit": "The score you return is this named session's London fit for this clock. An empty score leaves the fit unset.",
}


def _finite(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _clock_unit(value: Any, lo: int, hi: int) -> int | None:
    number = _finite(value)
    if number is None or number != int(number):
        return None
    whole = int(number)
    if whole < lo or whole > hi:
        return None
    return whole


def _hm(pack: dict, hour_spot: str, minute_spot: str, *, end: bool) -> tuple[int, int] | None:
    hour = _clock_unit(pack.get(hour_spot), 0, 24 if end else 23)
    minute = _clock_unit(pack.get(minute_spot), 0, 59)
    if hour is None or minute is None:
        return None
    return hour, minute


def _inside(as_of: datetime, start: tuple[int, int] | None, end: tuple[int, int] | None) -> bool | None:
    if start is None or end is None:
        return None
    return _in_hm_window(as_of, start, end)


def _clock_post(as_of: datetime, named: str) -> dict[str, Any]:
    out: dict[str, Any] = {spot: None for spot in _CLOCK_SPOTS}
    try:
        from src.judgment.jev_client import evaluate
        from src.judgment.jev_questions import append_outcome, prior_outcomes, returned_number
    except Exception:
        return out
    questions: dict[str, Any] = {}
    state: dict[str, Any] = {
        "sleeve": "chair_fields",
        "session_named": named,
        "hour": as_of.hour,
        "minute": as_of.minute,
        "as_of_utc": as_of.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    second = as_of.second + as_of.microsecond / 1000000.0
    state["seconds_until_cycle"] = 60.0 - second
    _bind_card(state)
    for spot in _CLOCK_SPOTS:
        built = _shape_score(spot, _CLOCK_TEXT[spot] + _UNSET, None, wrapped=True)
        if built:
            questions.update(built)
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    try:
        receipt = evaluate(state, questions=questions, model=_MODEL, merge_sleeve=False)
    except Exception:
        return out
    if not isinstance(receipt, dict) or not receipt.get("ok"):
        return out
    answers = receipt.get("answers")
    if not isinstance(answers, dict):
        answers = {}
    for spot in _CLOCK_SPOTS:
        block = answers.get(spot)
        if _amount_unit(spot, "") is None:
            number = _ordinal_read(block, spot)
        else:
            try:
                number = returned_number(block)
            except Exception:
                number = None
        out[spot] = number
        try:
            append_outcome(spot, number, state, error=None if number is not None else "empty")
        except Exception:
            pass
    return out


def _clock_ask(as_of: datetime, named: str) -> dict[str, Any]:
    """One pack for this minute and named session. No timeout."""
    key = (as_of.hour, as_of.minute, named)
    with _CLOCK_LOCK:
        hit = _CLOCK_CACHE.get(key)
    if hit is not None:
        return dict(hit)
    pack = _clock_post(as_of, named)
    with _CLOCK_LOCK:
        for old in list(_CLOCK_CACHE):
            if old != key:
                _CLOCK_CACHE.pop(old, None)
        _CLOCK_CACHE[key] = pack
    return dict(pack)


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

    clock_ids = (
        "us30_rth_vs_eth",
        "sess.ldn_ny_overlap_vol",
        "fx_session_london_fit",
        "tokyo_fix_window_label",
    )
    clock = (
        _clock_ask(as_of, named)
        if any(field_applies(fid, symbol) for fid in clock_ids)
        else {}
    )

    # us30_rth_vs_eth — the returned window, not the printed hours
    applies = field_applies("us30_rth_vs_eth", symbol)
    if applies:
        in_rth = _inside(
            as_of,
            _hm(clock, "us30_start_hour", "us30_start_minute", end=False),
            _hm(clock, "us30_end_hour", "us30_end_minute", end=True),
        )
        supplied_label = supplied.get("us30_rth_vs_eth")
        if supplied_label is not None:
            value = supplied_label
        elif in_rth is True:
            value = "rth"
        elif in_rth is False:
            value = "eth"
        else:
            value = None
        extra = {"dst_unresolved": True, "envelope": "ENV-US30", "envelope_stays": "integer_off"}
    else:
        value = None
        extra = {"envelope": "ENV-US30", "envelope_stays": "integer_off"}
    fields["us30_rth_vs_eth"] = _row(
        "us30_rth_vs_eth",
        applies=applies,
        assembled=value is not None,
        value=value,
        source=CLOCK_SOURCE,
        extra=extra,
    )

    # sess.ldn_ny_overlap_vol — returned hours. An empty score leaves the window unset.
    applies = field_applies("sess.ldn_ny_overlap_vol", symbol)
    overlap_lo = _clock_unit(clock.get("overlap_start_hour"), 0, 23)
    overlap_hi = _clock_unit(clock.get("overlap_end_hour"), 0, 24)
    if overlap_lo is None or overlap_hi is None:
        in_overlap = None
    else:
        in_overlap = overlap_lo <= as_of.hour < overlap_hi
    vol = supplied.get("sess.ldn_ny_overlap_vol")
    if isinstance(vol, Mapping):
        if vol.get("in_window") is not None:
            in_overlap = bool(vol.get("in_window"))
        named_vol = vol.get("vol")
    else:
        named_vol = vol if isinstance(vol, (int, float)) else m15_vol
    fields["sess.ldn_ny_overlap_vol"] = _row(
        "sess.ldn_ny_overlap_vol",
        applies=applies,
        assembled=applies and (in_overlap is not None or named_vol is not None),
        value={
            "in_window": in_overlap if applies else None,
            "vol": named_vol if applies else None,
            "window_utc": [overlap_lo, overlap_hi] if applies else None,
            "session_named": named or None,
        }
        if applies
        else None,
        source=CLOCK_SOURCE,
        extra={"vol_assembled": named_vol is not None},
    )

    # fx_session_london_fit — the score for this named session
    applies = field_applies("fx_session_london_fit", symbol)
    if not applies:
        fit = None
    elif supplied.get("fx_session_london_fit") is not None:
        fit = supplied["fx_session_london_fit"]
    else:
        fit = _finite(clock.get("london_fit"))
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

    # tokyo_fix_window_label — the returned window. 09:55 JST is the fix's clock name.
    applies = field_applies("tokyo_fix_window_label", symbol)
    tokyo_start = _hm(clock, "tokyo_start_hour", "tokyo_start_minute", end=False)
    tokyo_end = _hm(clock, "tokyo_end_hour", "tokyo_end_minute", end=True)
    in_fix = _inside(as_of, tokyo_start, tokyo_end)
    if applies and supplied.get("tokyo_fix_window_label") is not None:
        in_fix = bool(supplied["tokyo_fix_window_label"])
    fields["tokyo_fix_window_label"] = _row(
        "tokyo_fix_window_label",
        applies=applies,
        assembled=applies and in_fix is not None,
        value=in_fix if applies else None,
        source=CLOCK_SOURCE,
        extra={
            "window_utc": None
            if tokyo_start is None or tokyo_end is None
            else [tokyo_start[0], tokyo_start[1], tokyo_end[0], tokyo_end[1]],
            "fix_jst": "09:55",
        },
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
