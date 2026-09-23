"""ny_index_momentum.py — NEW SLEEVE: NY-killzone INDEX momentum-continuation, MID-VOL only (M15).

5th new sleeve (2026-06-17), PRINCIPAL-VERIFIED. Same NY-killzone continuation mechanic as ny_crypto_momentum,
but on stock INDICES and CONDITIONED on a MID vol-state (the base NY|index cell is MARGINAL; the edge lives in the
mid-ATR-percentile regime — the ultimate system trades it only there). At the NY decision bar (server 17:00), if
the 12-bar NY-window directional efficiency |de|>=0.50 AND the current ATR is in the MID percentile band of its
trailing 480-bar distribution, enter in the move direction; wide 1.3xATR stop, hold to session close.

PRINCIPAL re-derivation (my own, matches the correct-null sweep): pooled n=863, every-split positive
(train +0.178 / oos +0.175 / sealed +0.257), CORRECT random-entry-same-exit null p=0.0000, balanced direction
(LONG 538 +0.221 / SHORT 325 +0.162 -> both sides positive, NOT index bullish-drift), drift-null p=0.005.
Per-symbol: SPX500 +0.351, US30_cash +0.317, GER40 +0.274 (deep+strong); UK100 -0.083 (the weak member, kept for
no-post-hoc-selection — the pooled cell is robustly every-split+ despite it); NAS100/JP225 thin. Only 1 negative
year (2023). DEFAULT-OFF candidate (not in live BUILT); live wiring owner-gated.

MECHANIC (leak-free, decides on the latest CLOSED M15 bar i): only at NY decision bar (hour==17, minute==0) AND
mid vol-state. de = (close[i]-close[i-WINDOW]) / (window_high-window_low) over [i-WINDOW, i]; |de|>=DE_THRESH ->
enter sign(de). stop = STOP_MULT*ATR14[i]; EXIT = hold to session close (MAXBARS time-stop) or stop; target None.
vol-state = ATR14[i] percentile rank over the trailing VOL_WIN ATRs (MID = [VOL_LO, VOL_HI)). Decision uses only
bars <= i; entry at close[i] -> no look-ahead.
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from ._server_clock import server_hour_minute
from .spot_choice import all_false, ask, bar_id

DE_THRESH = 0.50
STOP_MULT = 1.3
WINDOW = 12
DECISION_HOUR = 17
DECISION_MIN = 0
MAXBARS = 20
VOL_WIN = 480            # trailing window for the ATR-percentile vol-state
VOL_LO = 0.34            # MID band = percentile rank in [VOL_LO, VOL_HI)
VOL_HI = 0.67
MIN_BARS = 520           # need >= VOL_WIN + a little for the vol-state percentile
ON_SURFACE = ("SPX500", "GER40", "UK100", "NAS100", "JP225")   # verified NY|index|mid cell
SLEEVE = "ny_index_momentum"


def _hm(t):
    """SERVER-LOCAL (hour, minute). DECISION_HOUR here is an FTMO server hour (F7/B29) while
    the live feed is true UTC, so this converts before comparing. None -> fail closed.

    This sleeve is NOT in the deployed candidate allowlist (agent_config.yaml:1275-1283), so
    this carries no live-behaviour change. It is corrected with the deployed eight so the
    package does not end up with two different meanings for DECISION_HOUR."""
    return server_hour_minute(t)


def _mid_vol(bars, i) -> bool:
    """True iff ATR14[i] is in the MID percentile band of the trailing VOL_WIN ATRs (matches the gen vol_state)."""
    if i < VOL_WIN:
        return False
    a_i = atr14(bars, i)
    if a_i <= 0:
        return False
    lo = i - VOL_WIN
    hist = [a for a in (atr14(bars, k) for k in range(lo, i)) if a > 0]
    if len(hist) < 50:
        return False
    rank = sum(1 for a in hist if a <= a_i) / len(hist)
    return VOL_LO <= rank < VOL_HI


def measured(symbol, bars, *, bar_time=None, bar_times=None) -> dict:
    """Facts for the latest closed bar. Not a decision."""
    i = len(bars) - 1 if bars else -1
    t = bar_time if bar_time is not None else (
        bar_times[i] if bar_times and bars and len(bar_times) == len(bars) else None
    )
    hm = _hm(t) if t is not None else None
    a = atr14(bars, i) if bars and i >= 0 else 0.0
    warmup_short = i < MIN_BARS or i < WINDOW
    mid = False
    rng = 0.0
    net = 0.0
    if bars and not warmup_short:
        mid = _mid_vol(bars, i)
        w = bars[i - WINDOW:i + 1]
        hi = max(b.h for b in w)
        lo = min(b.l for b in w)
        rng = hi - lo
        net = bars[i].c - bars[i - WINDOW].c
    efficiency = abs(net / rng) if rng > 0 else 0.0
    direction = 1 if net > 0 else -1
    return {
        "off_surface": symbol not in ON_SURFACE,
        "warmup_short": warmup_short,
        "no_bar_time": t is None or hm is None,
        "not_ny_decision_bar": hm is None or hm[0] != DECISION_HOUR or hm[1] != DECISION_MIN,
        "atr_not_a_scale": not (a > 0),
        "not_mid_vol": not mid,
        "range_flat": not (rng > 0),
        "efficiency_below": efficiency < DE_THRESH,
        "atr": float(a),
        "direction": direction,
        "efficiency": efficiency,
    }


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """NY-killzone index continuation. Each gate is one spot Choice."""
    if not bars:
        return None
    facts = measured(symbol, bars, bar_time=bar_time, bar_times=bar_times)
    sides = ask(
        sleeve=SLEEVE,
        symbol=symbol,
        bar_id=bar_id(decision_day, len(bars), bar_time, bar_times),
        spots={
            "off_surface": {
                "condition": f"{symbol} is not one of SPX500, GER40, UK100, NAS100, JP225",
                "measured": facts["off_surface"],
            },
            "warmup_short": {
                "condition": f"closed M15 count is below {MIN_BARS}",
                "measured": facts["warmup_short"],
            },
            "no_bar_time": {
                "condition": "the decision bar has no server clock",
                "measured": facts["no_bar_time"],
            },
            "not_ny_decision_bar": {
                "condition": "the bar is not the NY decision print at server 17:00",
                "measured": facts["not_ny_decision_bar"],
            },
            "atr_not_a_scale": {
                "condition": "ATR14 is not a positive scale for the 1.3 stop",
                "measured": facts["atr_not_a_scale"],
            },
            "not_mid_vol": {
                "condition": "ATR14 is outside the mid percentile band of the trailing 480 bars",
                "measured": facts["not_mid_vol"],
            },
            "range_flat": {
                "condition": "the 12-bar window range is not positive",
                "measured": facts["range_flat"],
            },
            "efficiency_below": {
                "condition": "absolute directional efficiency is below 0.50",
                "measured": facts["efficiency_below"],
            },
        },
    )
    if not all_false(sides):
        return None
    sd = STOP_MULT * facts["atr"]
    if not (sd > 0):
        return None
    return TradeIntent(
        sleeve=SLEEVE,
        symbol=symbol,
        direction=facts["direction"],
        decision_day=decision_day,
        stop_dist=sd,
        target_dist=None,
    )
