"""energy_agri sleeve (conf 0.80).

Same vol-gated FVG-retest ENTRY as metals (gold_sleeve_strategy.fvg_signals, reused via
metals.fvg_signal), but a different STATE GATE (energy_agri_sleeve.energy_gate): energy
continuation pays when vol-ratio is at or above the asked gate (supply-shock vol ignition)
OR the absolute trend slope is inside the asked bound (flat-trend early continuation) —
the ac60 persistence gate that powers metals does NOT help energy.

On-surface (of the 24 live symbols): USOIL_cash, UKOIL_cash. The AGRI legs (CORN_c/COTTON_c) and the
dropped energy legs (HEATOIL_c/NATGAS_cash) are off-surface AND the live spread check put CORN/COTTON
over the 0.20R untradeable wall -> excluded. UKOIL data was forward-only historically (flagged).
Live emits a sleeve-tagged TradeIntent on the latest CLOSED H4 bar.
Cost and spread do not skip an on-surface name. Empty bars still return None from generate;
that is a missing tape, not a cost skip.
"""
from __future__ import annotations
from typing import Optional

from ..primitives import atr14, vol_ratio
from ..admission import TradeIntent
from .metals import fvg_signal

ON_SURFACE = ("USOIL_cash", "UKOIL_cash")
SLEEVE = "energy_agri"
#: Names of the four hops. The numbers are not the decision.
VR_GATE = "vr_gate"
SLOPE_THR = "slope_thr"
TREND_LB = "trend_lb"
TARGET_R = "target_r"
_MODEL = "jev-1.13.0"


def _decision_questions(spots, facts, bars, i):
    from .spot_choice import amount_question, anchors_for

    text = {
        VR_GATE: (
            "Given the facts and prior_outcomes on this state, what vol-ratio "
            "level gates this energy continuation? The score you return is that "
            "gate. An empty card does not supply a level."
        ),
        SLOPE_THR: (
            "Given the facts and prior_outcomes on this state, what absolute "
            "slope in ATR per bar is still a flat continuation? The score you "
            "return is that bound. An empty card does not supply a bound."
        ),
        TREND_LB: (
            "Given the facts and prior_outcomes on this state, how many closed "
            "bars does the trend slope look across? The score you return is that "
            "lookback. An empty card does not supply a lookback."
        ),
        TARGET_R: (
            "Given the facts and prior_outcomes on this state, what reward "
            "multiple is the target on this energy? The score you return is that "
            "multiple. An empty card does not supply a multiple."
        ),
    }
    packed = {}
    built = {}
    for spot in spots:
        anchors = anchors_for(spot, facts, bars=bars, index=i)
        built[spot] = anchors
        packed.update(amount_question(spot, text[spot], anchors))
    return packed, built


def _ask(spots, bars, i, facts):
    """One System One post. The returned Noul, Choice, or Score is the value.

    An empty answer, a tie, or an error stays empty. Nothing here puts a
    printed constant back.
    """
    from src.judgment.jev_client import evaluate
    from src.judgment.jev_questions import append_outcome, prior_outcomes, returned_number

    state = dict(facts or {})
    questions, anchors = _decision_questions(spots, state, bars, i)
    try:
        state["prior_outcomes"] = prior_outcomes(state=state, questions=questions)
    except Exception:
        state["prior_outcomes"] = []
    answers = {}
    error = None
    try:
        receipt = evaluate(
            state,
            questions=questions,
            model=_MODEL,
            merge_sleeve=False,
            require_equity=False,
        )
    except Exception as exc:
        receipt = None
        error = type(exc).__name__
    if isinstance(receipt, dict):
        if receipt.get("ok"):
            raw = receipt.get("answers")
            if isinstance(raw, dict):
                answers = raw
        else:
            error = receipt.get("error") or receipt.get("skipped") or "post_failed"
    out = {}
    for spot in spots:
        from .spot_choice import value_at

        number = value_at(returned_number(answers.get(spot)), anchors.get(spot))
        out[spot] = number
        try:
            append_outcome(
                spot,
                number,
                state,
                error=None if number is not None else (error or "empty"),
            )
        except Exception:
            pass
    return out


def _lookback_bars(lb) -> Optional[int]:
    """Bar count from the asked return. Empty is empty. Nothing here fills a window."""
    if lb is None or lb == "":
        return None
    try:
        window = int(lb)
    except (TypeError, ValueError):
        return None
    if window != window or window < 1:
        return None
    return window


def trend_slope(B, i, lb) -> Optional[float]:
    """energy_agri_sleeve.trend_slope: normalized linreg slope of closes / ATR.

    ``lb`` is the asked lookback. An empty lookback is not a slope.
    """
    window = _lookback_bars(lb)
    if window is None or i < window:
        return None
    ys = [B[k].c for k in range(i - window + 1, i + 1)]
    n = len(ys)
    xs = list(range(n))
    mx = (n - 1) / 2.0
    my = sum(ys) / n
    num = sum((xs[k] - mx) * (ys[k] - my) for k in range(n))
    den = sum((xs[k] - mx) ** 2 for k in range(n))
    if den == 0:
        return None
    slope = num / den
    a = atr14(B, i)
    if not (a > 0):
        return None
    return slope / a


def energy_gate(vr: float, slope, vr_gate, slope_thr) -> bool:
    """energy_agri_sleeve.energy_gate: asked vol gate OR asked slope bound.

    An empty hop does not restore a printed level. Either clause fires only
    on a returned number.
    """
    if vr_gate is not None and vr >= vr_gate:
        return True
    if slope is not None and slope_thr is not None and abs(slope) < slope_thr:
        return True
    return False


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, **_) -> Optional[TradeIntent]:
    """Live energy_agri: FVG-retest entry + energy state gate, on the latest closed H4 bar.
    bar_time accepted for the uniform engine call (unused — no session gate)."""
    if symbol not in ON_SURFACE or not bars:
        return None
    i = len(bars) - 1
    atrs = [atr14(bars, k) for k in range(len(bars))]
    sig = fvg_signal(bars, atrs, i)
    if sig is None:
        return None
    d, sd = sig
    vr = vol_ratio(atrs, i)
    b = bars[i]
    decided = _ask(
        (VR_GATE, SLOPE_THR, TREND_LB, TARGET_R),
        bars,
        i,
        {
            "symbol": symbol,
            "sleeve": SLEEVE,
            "decision_day": decision_day,
            "vr": vr,
            "direction": d,
            "stop_dist": sd,
            "bar_index": i,
            "open": b.o,
            "high": b.h,
            "low": b.l,
            "close": b.c,
            "atr": atrs[i],
        },
    )
    vr_gate = decided.get(VR_GATE)
    slope_thr = decided.get(SLOPE_THR)
    lookback = decided.get(TREND_LB)
    target = decided.get(TARGET_R)
    slope = trend_slope(bars, i, lookback)
    if not energy_gate(vr, slope, vr_gate, slope_thr):
        return None
    if target is None:
        return None
    return TradeIntent(sleeve=SLEEVE, symbol=symbol, direction=d, decision_day=decision_day,
                       stop_dist=sd, target_dist=target * sd)
