"""metals_confluence_gate.py — the metals entry-quality confluence gate.

The gate is four conditions on closed-bar features: regime (slope and momentum
on the same side of zero), freshness, vol, and the session hour. The freshness
age, the vol cap, the number of conditions required, and the last hour of the
session window are one Score ask for this feature state. An empty answer, a
tie, or an error does not restore a planted age, cap, count, or hour.

enabled=False does not ask and does not apply the gate. The caller that arms
the gate passes enabled=True. This module does not place an order.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_HOP: dict[tuple, dict[str, float | None]] = {}


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _scores(
    cache_key: tuple,
    facts: dict,
    questions: dict[str, str],
    anchors: dict | None = None,
) -> dict[str, float | None]:
    """One nineteen.score per question. Fewer than two anchors does not post."""
    if cache_key in _HOP:
        return dict(_HOP[cache_key])
    payload = {
        str(key): value
        for key, value in dict(facts or {}).items()
        if str(key) not in {"denominator", "other"}
    }
    levels = anchors if isinstance(anchors, dict) else {}
    out = {str(qid): None for qid in questions}
    ask = None
    try:
        from src.judgment.nineteen import score as ask
    except Exception:
        ask = None
    if ask is not None:
        for qid, text in questions.items():
            try:
                out[str(qid)] = _finite(
                    ask(
                        payload,
                        question_id=str(qid),
                        instructions=str(text),
                        anchors=levels.get(str(qid)),
                    )
                )
            except Exception:
                out[str(qid)] = None
    _HOP[cache_key] = dict(out)
    return out


@dataclass
class ConfluenceResult:
    passed: bool
    score: int | None
    up_regime: bool
    fresh: bool
    vol_cap: bool
    asian: bool
    reason: str


def metals_confluence(*, htf_slope_norm: float, mom_20_atr: float, fvg_freshness_bars: float,
                      ac60: float = None, atr_ratio: float, session_hour: int,
                      enabled: bool = False) -> ConfluenceResult:
    """Confluence on decision-time features.

    enabled=False admits and does not ask. ac60 is accepted for callers and is
    not a condition. An unanswered bound does not fill the old age, cap, count,
    or hour, and it does not reject the intent. The count is None in that case
    so a caller cannot read a planted total.
    """
    del ac60
    if not enabled:
        return ConfluenceResult(
            True, None, False, False, False, False,
            "confluence gate off",
        )
    facts = {
        "htf_slope_norm": htf_slope_norm,
        "mom_20_atr": mom_20_atr,
        "fvg_freshness_bars": fvg_freshness_bars,
        "atr_ratio": atr_ratio,
        "session_hour": session_hour,
    }
    fresh_age = _finite(fvg_freshness_bars)
    ratio = _finite(atr_ratio)
    hour = _finite(session_hour)
    bounds = _scores(
        ("metals_confluence", tuple(sorted((str(k), repr(v)) for k, v in facts.items()))),
        facts,
        {
            "fresh_bars_max": (
                "The score you return is the freshest FVG age in bars this state still calls fresh. "
                "An empty score leaves that age unset. Do not send."
            ),
            "vol_cap": (
                "The score you return is the atr ratio this state still calls inside the vol cap. "
                "An empty score leaves that cap unset. Do not send."
            ),
            "k_required": (
                "The score you return is how many confluence conditions this state requires. "
                "An empty score leaves that count unset. Do not send."
            ),
            "asian_hour_end": (
                "The score you return is the last session hour this state still calls inside the session window. "
                "An empty score leaves that hour unset. Do not send."
            ),
        },
        {
            "fresh_bars_max": (
                [("the FVG age in bars on this state", fresh_age)] if fresh_age is not None else []
            ),
            "vol_cap": (
                [("the atr ratio on this state", ratio)] if ratio is not None else []
            ),
            "k_required": [],
            "asian_hour_end": (
                [("the session hour on this state", hour)] if hour is not None else []
            ),
        },
    )
    fresh_max = bounds.get("fresh_bars_max")
    vol_max = bounds.get("vol_cap")
    required = bounds.get("k_required")
    hour_end = bounds.get("asian_hour_end")
    up = (
        htf_slope_norm is not None
        and mom_20_atr is not None
        and htf_slope_norm > 0
        and mom_20_atr > 0
    )
    fresh = (
        fvg_freshness_bars is not None
        and fresh_max is not None
        and fvg_freshness_bars <= fresh_max
    )
    vcap = atr_ratio is not None and vol_max is not None and atr_ratio < vol_max
    asian = (
        session_hour is not None
        and hour_end is not None
        and session_hour >= 0
        and session_hour <= hour_end
    )
    flags = (up, fresh, vcap, asian)
    if fresh_max is None or vol_max is None or required is None or hour_end is None:
        return ConfluenceResult(
            True, None, bool(up), bool(fresh), bool(vcap), bool(asian),
            "confluence bounds unset",
        )
    count = sum(1 for flag in flags if flag)
    passed = count >= required
    return ConfluenceResult(
        passed, count, bool(up), bool(fresh), bool(vcap), bool(asian),
        f"confluence {count}/{len(flags)} (up={up} fresh={fresh} vol_cap={vcap} asian={asian}); "
        f"{'ADMIT' if passed else 'reject'}",
    )
