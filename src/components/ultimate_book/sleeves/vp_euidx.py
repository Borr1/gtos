"""POC gravitation on GER40 and UK100.

The warmup, the distance from the prior-day POC, the volume ratio, the stop,
and the reward multiple are one score pack for this bar. The profile bounds
ride that same pack, so the profile build does not ask again. An empty score
does not open the gate and does not put a printed level back.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from ..admission import TradeIntent
from ..primitives import atr14, vol_ratio
from . import volume_profile as vp
from .volume_profile import _PROFILE_TEXT, ask_scores

ON_SURFACE = ("GER40", "UK100")
SLEEVE = "vp_euidx_pocgrav"

# Importers still load the names. They are not the gate.
WARMUP_H4 = None
FAR = None
VR_MIN = None
STOP_ATR = None
MIN_RR = None

_GATE_TEXT = {
    "warmup_bars": "The score you return is how many closed H4 bars this profile read needs.",
    "far_atr": "The score you return is how many ATR from the prior-day POC counts as far.",
    "vr_min": "The score you return is the volume-ratio level this bar must reach.",
    "stop_atr": "The score you return is the stop distance in ATR of this bar.",
    "min_rr": "The score you return is the multiple of the stop that the distance to the POC must reach.",
}
_TEXTS = {**_PROFILE_TEXT, **_GATE_TEXT}
_BLOCKERS = (
    "off_surface",
    "warmup_short",
    "no_m1",
    "no_bar_time",
    "atr_not_a_scale",
    "no_profile_days",
    "on_or_before_first_profile_day",
    "no_prior_profile",
    "no_node_state",
    "inside_or_not_far",
    "vol_ratio_below",
    "target_below_min_rr",
)


def _num(value):
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


def _count(value):
    number = _num(value)
    if number is None or number < 1:
        return None
    return int(round(number))


def _utc_date(t):
    tz = getattr(t, "tzinfo", None)
    return (t.astimezone(timezone.utc) if tz is not None else t).date()


def _stamp(bar_time, bar_times, n):
    if bar_times is not None and n and len(bar_times) == n:
        return bar_times[n - 1]
    return bar_time


def _until_next(bar_times):
    """Seconds until the next bar of this series. No pair, no deadline."""
    if not bar_times or len(bar_times) < 2:
        return None
    left, right = bar_times[-2], bar_times[-1]
    try:
        period = (right - left).total_seconds()
    except Exception:
        return None
    if period <= 0 or getattr(right, "tzinfo", None) is None:
        return None
    try:
        remain = ((right + (right - left)) - datetime.now(timezone.utc)).total_seconds()
    except Exception:
        return None
    if remain <= 0:
        return None
    return remain


def _blank():
    return {
        "off_surface": True,
        "warmup_short": True,
        "no_m1": True,
        "no_bar_time": True,
        "atr_not_a_scale": True,
        "no_profile_days": True,
        "on_or_before_first_profile_day": True,
        "no_prior_profile": True,
        "no_node_state": True,
        "inside_or_not_far": True,
        "vol_ratio_below": True,
        "target_below_min_rr": True,
        "direction": 0,
        "stop_dist": 0.0,
        "target_dist": 0.0,
        "entry": None,
        "scores": {},
    }


def _card(symbol, bars, stamp, bar_times, aux_bars, aux_times) -> dict:
    bar = bars[-1]
    facts = {
        "sleeve": SLEEVE,
        "symbol": symbol,
        "n_h4": len(bars),
        "open": _num(bar.o),
        "high": _num(bar.h),
        "low": _num(bar.l),
        "close": _num(bar.c),
        "bar_stamp": str(stamp),
        "has_m1": bool(aux_bars and aux_times),
        "n_m1": len(aux_bars) if aux_bars else 0,
    }
    if aux_times:
        facts["m1_last_stamp"] = str(aux_times[-1])
    remain = _until_next(bar_times)
    if remain is not None:
        facts["seconds_until_cycle"] = remain
    return facts


def measured(symbol, bars, *, bar_time=None, bar_times=None, aux_bars=None, aux_times=None) -> dict:
    """Gate facts for the latest closed H4 bar. Closed means the score did not open it."""
    row = _blank()
    n = len(bars) if bars else 0
    row["off_surface"] = symbol not in ON_SURFACE
    if not bars or row["off_surface"]:
        return row
    stamp = _stamp(bar_time, bar_times, n)
    row["no_m1"] = not aux_bars or not aux_times
    row["no_bar_time"] = stamp is None
    if row["no_m1"] or row["no_bar_time"]:
        return row
    pack = ask_scores(
        _card(symbol, bars, stamp, bar_times, aux_bars, aux_times),
        _TEXTS,
        bars=bars,
        index=n - 1,
        bar_times=bar_times,
    )
    row["scores"] = {name: pack.get(name) for name in _TEXTS}
    warm = _count(pack.get("warmup_bars"))
    row["warmup_short"] = warm is None or n < warm
    if not pack.get("_asked") or row["warmup_short"]:
        return row
    i = n - 1
    atrs = [atr14(bars, k) for k in range(n)]
    scale = atrs[i]
    row["atr_not_a_scale"] = not (scale > 0)
    if row["atr_not_a_scale"]:
        return row
    try:
        profs, days = vp.daily_profiles(aux_bars, aux_times, bounds=pack)
    except Exception:
        profs, days = {}, []
    row["no_profile_days"] = not days
    if not days or not (_utc_date(stamp) > days[0]):
        row["on_or_before_first_profile_day"] = True
        return row
    row["on_or_before_first_profile_day"] = False
    dp = vp.prior_profile_at(profs, days, stamp)
    row["no_prior_profile"] = dp is None
    if dp is None:
        return row
    price = bars[i].c
    state = vp.nearest_node_state(dp, price, scale, pack)
    row["no_node_state"] = state is None
    if state is None:
        return row
    far = _num(pack.get("far_atr"))
    level = _num(pack.get("vr_min"))
    mult = _num(pack.get("stop_atr"))
    reward = _num(pack.get("min_rr"))
    dpoc = state["d_poc_atr"]
    row["inside_or_not_far"] = far is None or abs(dpoc) < far or bool(state["in_va"])
    ratio = vol_ratio(atrs, i)
    row["vol_ratio_below"] = level is None or ratio < level
    row["direction"] = -1 if dpoc > 0 else 1
    if mult is None or mult <= 0 or reward is None:
        row["target_below_min_rr"] = True
        return row
    stop_dist = mult * scale
    target_dist = abs(price - dp.poc)
    row["stop_dist"] = float(stop_dist)
    row["target_dist"] = float(target_dist)
    row["target_below_min_rr"] = not (stop_dist > 0) or target_dist < reward * stop_dist
    if dp.poc and float(dp.poc) > 0:
        row["entry"] = float(dp.poc)
    return row


def generate(
    symbol: str,
    bars,
    decision_day: str,
    *,
    bar_time=None,
    bar_times=None,
    aux_bars=None,
    aux_times=None,
    **_,
) -> Optional[TradeIntent]:
    """The gravitation intent when every score gate is open. Otherwise None."""
    if not bars:
        return None
    facts = measured(
        symbol,
        bars,
        bar_time=bar_time,
        bar_times=bar_times,
        aux_bars=aux_bars,
        aux_times=aux_times,
    )
    if any(facts.get(name) for name in _BLOCKERS):
        return None
    if facts["direction"] not in (1, -1) or not (facts["stop_dist"] > 0) or not (facts["target_dist"] > 0):
        return None
    return TradeIntent(
        sleeve=SLEEVE,
        symbol=symbol,
        direction=facts["direction"],
        decision_day=decision_day,
        stop_dist=facts["stop_dist"],
        target_dist=facts["target_dist"],
        entry_price=facts["entry"],
    )
