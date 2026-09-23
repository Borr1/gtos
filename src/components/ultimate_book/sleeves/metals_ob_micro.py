"""metals_ob_micro sleeve — order-block-retest tail-frequency add (conf 0.30).

Byte-faithful port of the LOCKED route metals_ob_micro (Stage-2c of the metals stack):

  ENTRY DETECTOR  <- csb_commodity_setups.sig_ob (lines 80-108): a vol-gated, HTF-trend-aligned
    ORDER-BLOCK RETEST. In an uptrend (htf_trend lb=30 == +1): find the last opposite-color (DOWN)
    candle B[k] (B[k].c < B[k].o) immediately before an UP impulse (B[k+1].c > B[k].h); the signal
    fires when the current bar retests that order block — its low dips into the zone (b.l <= ob_top =
    B[k].h) yet it closes back up bullishly (b.c > ob_bot = B[k].l and b.c > b.o). Downtrend mirrors.
    The stop buffer, the ATR floor, and the lookback are the scores for this bar.
    The scan fires on the first qualifying block.

  SLEEVE GATES  <- INTEG_portfolio_build.gen_metals_ob_micro (lines 122-141):
    (1) autocorrelation at the returned lag must clear the returned level.
    (2) DEDUP vs FVG — see the dedup note in generate(). The route drops an OB-micro entry whose
        (sym, date, dir) is also an FVG entry (fvg_keys require only `ac is not None`).
    Exit is the STATE_D vol-tiered scale-out (NOT a fixed target) managed downstream, so the emitted
    TradeIntent carries target_dist=None; the entry geometry (direction, stop_dist) is what we port.

ON_SURFACE = the admission metals_ob_micro 6-tuple (XAUUSD, XAGUSD, XAUEUR, XAGEUR, XAUAUD, XAGAUD).
ALL 6 are present on the FTMO PRIMARY profile (config/profiles/operator_profile.yaml, 34
instruments). The redacted_account FOLLOWER profile (27 instruments) carries only XAUUSD/XAGUSD — the 4
metals crosses are absent there, so on FN this sleeve manages only XAU/XAG (book_owner._manageable_symbols
filters config-absent symbols per profile; the reduced FN breadth is intentional + logged once). NB:
the core FVG sleeves (metals.py) restrict their live data surface to XAUUSD/XAGUSD; this OB-micro sleeve
mirrors the admission.SLEEVE_REGISTRY["metals_ob_micro"] tuple (the route's cs.METALS = the same 6).

Reuses the LOCKED primitives (atr14, autocorr) and metals.htf_trend / metals.fvg_signal verbatim —
no logic is re-implemented that already lives in a parity-tested module. Pure: stdlib only, no IO.
"""
from __future__ import annotations
from typing import Optional

from ..primitives import atr14, autocorr, vol_ratio
from ..admission import TradeIntent
from ._stop_floor import DEFAULT_ATR_STOP_FLOOR, floor_stop
from . import fx_spot
from . import metals

# admission.SLEEVE_REGISTRY["metals_ob_micro"].symbols; all 6 on the FTMO primary (34-instrument)
# universe. On the FN follower (27) only XAU/XAG exist -> the 4 crosses are filtered per-profile.
ON_SURFACE = ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD")

#: Shared export. structural_retest and the stop-floor test read this name.
#: generate does not use it as the floor. The floor is the returned score.
ATR_STOP_FLOOR = DEFAULT_ATR_STOP_FLOOR
_SCORES = {
    "trend_lb": "The score you return is how many bars the higher-timeframe trend looks back.",
    "stop_buf": "The score you return is the ATR multiple added beyond the order-block stop.",
    "atr_floor": "The score you return is the ATR multiple that floors the stop.",
    "ob_lookback": "The score you return is how many bars back the order-block scan reaches.",
    "gate_k": "The score you return is the multiple of the ATR average that opens the vol gate.",
    "vol_window": "The score you return is how many ATR values that average uses.",
    "scan_floor": "The score you return is the oldest bar index the order-block scan may reach.",
    "ac_lag": "The score you return is the autocorrelation lag.",
    "ac_thr": "The score you return is the autocorrelation level this sleeve requires.",
    "warmup_bars": "The score you return is how many closed bars this scan needs.",
}



def _positive(value):
    number = fx_spot.finite(value)
    if number is None or not (number > 0):
        return None
    return number


def _whole(value, *, least: int = 1):
    number = fx_spot.whole(value)
    if number is None or number < least:
        return None
    return number


def _bounds(scores):
    """Returned numbers. Any miss leaves the map unset."""
    trend_lb = _whole(scores.get("trend_lb"))
    stop_buf = _positive(scores.get("stop_buf"))
    atr_floor = _positive(scores.get("atr_floor"))
    ob_lookback = _whole(scores.get("ob_lookback"))
    gate_k = _positive(scores.get("gate_k"))
    vol_window = _whole(scores.get("vol_window"))
    scan_floor = _whole(scores.get("scan_floor"), least=0)
    ac_lag = _whole(scores.get("ac_lag"))
    ac_thr = fx_spot.finite(scores.get("ac_thr"))
    warmup = _whole(scores.get("warmup_bars"))
    if None in (trend_lb, stop_buf, atr_floor, ob_lookback, gate_k, vol_window, scan_floor, ac_lag, ac_thr, warmup):
        return None
    return {
        "trend_lb": trend_lb,
        "stop_buf": stop_buf,
        "atr_floor": atr_floor,
        "ob_lookback": ob_lookback,
        "gate_k": gate_k,
        "vol_window": vol_window,
        "scan_floor": scan_floor,
        "ac_lag": ac_lag,
        "ac_thr": ac_thr,
        "warmup": warmup,
    }


def vol_gate_ok(atrs, i, gate_k=None, window=None) -> Optional[bool]:
    """True when ATR clears the returned multiple of its own average.

    A missing multiple or window is unset, not a closed gate.
    """
    mult = _positive(gate_k)
    span = _whole(window)
    if mult is None or span is None:
        return None
    if i < span:
        return False
    try:
        current = float(atrs[i])
    except (TypeError, ValueError, IndexError):
        return None
    if not (current > 0):
        return False
    sample = atrs[i - span + 1:i + 1]
    if len(sample) < span:
        return False
    average = sum(sample) / span
    if not (average > 0):
        return False
    return bool(current >= mult * average)


def sig_ob(B, atrs, i, bounds=None) -> Optional[tuple[int, float]]:
    """(direction, stop_dist) for the first order-block retest that the bounds allow.

    Missing bounds do not scan and do not fill a floor.
    """
    if not isinstance(bounds, dict):
        return None
    trend_lb = bounds.get("trend_lb")
    stop_buf = bounds.get("stop_buf")
    atr_floor = bounds.get("atr_floor")
    ob_lookback = bounds.get("ob_lookback")
    gate_k = bounds.get("gate_k")
    vol_window = bounds.get("vol_window")
    scan_floor = bounds.get("scan_floor")
    if None in (trend_lb, stop_buf, atr_floor, ob_lookback, gate_k, vol_window, scan_floor):
        return None
    try:
        atr = float(atrs[i])
    except (TypeError, ValueError, IndexError):
        return None
    if not (atr > 0):
        return None
    if vol_gate_ok(atrs, i, gate_k, vol_window) is not True:
        return None
    trend = metals.htf_trend(B, i, trend_lb)
    bar = B[i]
    start = max(i - ob_lookback, scan_floor)
    if trend == 1:
        direction = 1
        candle = lambda k: B[k].c < B[k].o
        impulse = lambda k: B[k + 1].c > B[k].h
        held = lambda top, bot: bar.l <= top and bar.c > bot and bar.c > bar.o
        raw = lambda top, bot: (bar.c - min(bar.l, bot)) + stop_buf * atr
    elif trend == -1:
        direction = -1
        candle = lambda k: B[k].c > B[k].o
        impulse = lambda k: B[k + 1].c < B[k].l
        held = lambda top, bot: bar.h >= bot and bar.c < top and bar.c < bar.o
        raw = lambda top, bot: (max(bar.h, top) - bar.c) + stop_buf * atr
    else:
        return None
    for k in range(i - 2, start, -1):
        if k < 0 or k + 1 > i:
            continue
        if not candle(k) or not impulse(k):
            continue
        top, bot = B[k].h, B[k].l
        if not held(top, bot):
            continue
        stop = floor_stop(raw(top, bot), atr, atr_floor)
        if not (stop > 0):
            return None
        return direction, stop
    return None


def generate(symbol: str, bars, decision_day: str, **_) -> Optional[TradeIntent]:
    """One post for the bounds, then the order-block geometry.

    Same-direction FVG on this bar still yields the bar to the FVG sleeve.
    An empty score does not emit.
    """
    if not bars:
        return None
    i = len(bars) - 1
    state = fx_spot.book_state(
        "metals_ob_micro",
        symbol,
        decision_day=decision_day,
        n_bars=len(bars),
        bar_index=i,
        on_named_surface=symbol in ON_SURFACE,
        named_surface=list(ON_SURFACE),
    )
    choices = {
        "surface": {
            "instructions": (
                "Is this symbol one of the named metals for this bar? "
                "The names are a fact. An empty answer, a tie, or an error is not a side."
            ),
            "criteria": {
                "on_surface": f"{symbol} is one of the named metals.",
                "off_surface": f"{symbol} is not one of the named metals.",
            },
        }
    }
    packed = fx_spot.ask_pack(_SCORES, state, choices=choices, bars=bars, index=i)
    if packed.get("sides", {}).get("surface") != "on_surface":
        return None
    bounds = _bounds(packed.get("scores") or {})
    if bounds is None or i < bounds["warmup"]:
        return None
    atrs = [atr14(bars, k) for k in range(len(bars))]
    sig = sig_ob(bars, atrs, i, bounds)
    if sig is None:
        return None
    direction, stop_dist = sig
    ac = autocorr(bars, i, bounds["ac_lag"])
    if ac is None or ac < bounds["ac_thr"]:
        return None
    fvg = metals.fvg_signal(bars, atrs, i)
    if fvg is not None and fvg[0] == direction:
        return None
    vr = vol_ratio(atrs, i)
    try:
        runner = metals._runner_R(vr)
    except Exception:
        runner = None
    runner_n = fx_spot.finite(runner)
    if runner_n is None or not (runner_n > 0) or not (stop_dist > 0):
        return None
    return TradeIntent(
        sleeve="metals_ob_micro",
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=runner_n * stop_dist,
    )
