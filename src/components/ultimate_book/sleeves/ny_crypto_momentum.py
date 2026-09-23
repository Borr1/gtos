"""ny_crypto_momentum.py — NEW SLEEVE: NY-killzone crypto momentum-CONTINUATION (M15, BTC/ETH).

4th genuinely-new sleeve (2026-06-17), PRINCIPAL-VERIFIED and refined by the principal candidate-book audit to
exclude the failing LOW-vol subset. A CONDITIONAL edge by design (owner doctrine: the ultimate system knows WHAT
to do, WHEN, for WHICH symbol — not a general all-symbol/all-time rule). It fires ONLY at the NY killzone
decision bar (server 17:00 EET) on crypto, in the direction of the NY-session move when that move is clean
(high directional efficiency) AND the trailing ATR-percentile vol-state is NOT-LOW (mid or high), then rides it
to session close. Verified on BTCUSD+ETHUSD M15 (cmap_killzone_momentum_continuation +
verify_ny_crypto_momentum_sleeve.py): refined pooled n=1702 +0.2017, every-split positive and increasing
(train +0.102 / oos +0.273 / sealed +0.310).

REAL EDGE, NOT the crypto bullish-drift trap (the decisive checks):
  - BALANCED direction after refinement (880 long / 822 short); both sides positive (LONG +0.259, SHORT +0.141).
  - CORRECT random-entry-SAME-exit null (random NY bar, random dir, same stop/maxbars): p=0.0007.
  - Directional-drift null p=0.0033 -> momentum-TIMING alpha on top of drift, not drift itself.
CONDITIONAL CHARACTER (mapped, honest): LOW-vol was the weak/failing subset; MID and HIGH are both useful, so
the correct fold is NOT-LOW rather than a narrower mid-only sleeve. Shares crypto-momentum beta with the deployed
D1 Donchian crypto sleeve but is a DISTINCT timeframe/timing surface (M15 NY-session vs D1 breakout).
DEFAULT-OFF candidate (not in live BUILT).

MECHANIC (leak-free, decides on the latest CLOSED M15 bar i): only at the NY decision bar (server hour==17,
minute==0) and only when ATR14[i]'s percentile rank over the trailing VOL_WIN ATRs is mid/high. Over the NY window
[i-WINDOW, i] (14:00->17:00, 12 M15 bars) compute directional efficiency de = (close[i]-close[i-WINDOW]) /
(window_high - window_low). If |de| >= DE_THRESH the session move is clean -> enter in its direction; stop =
STOP_MULT*ATR14[i] (WIDE, amortizes cost); EXIT = hold to session close (time-stop MAXBARS bars) or stop.
Decision uses only bars <= i; entry at close[i]; fill forward -> no look-ahead. EXIT is a time-stop (no fixed
target): target_dist=None by design; the live path holds MAXBARS bars or to the stop.
"""
from __future__ import annotations
from typing import Optional
from ..primitives import atr14
from ..admission import TradeIntent
from ._server_clock import server_hour_minute
from .crypto_choices import crypto_side

# verified killzone-momentum-continuation config (SESSIONS['NY']=(17,0,12,20), DE_THRESH=0.50, STOP_MULT=1.3)
DE_THRESH = 0.50         # clean one-way NY-session move gate (|directional efficiency|)
STOP_MULT = 1.3          # wide stop in ATR units (amortizes cost; the gen's hold-to-close mode)
WINDOW = 12              # NY window length in M15 bars (14:00->17:00)
DECISION_HOUR = 17       # server-local EET NY killzone decision bar
DECISION_MIN = 0
MAXBARS = 20             # time-stop: hold to ~session close (~22:00)
VOL_WIN = 480            # trailing ATR-percentile window (matches gen.vol_state)
VOL_LO = 0.34            # LOW below this rank; MID/HIGH are allowed by the not-low refinement
VOL_HI = 0.67
MIN_BARS = VOL_WIN       # first exact reference bar can occur once trailing vol-state is available
ON_SURFACE = ("BTCUSD", "ETHUSD")   # verified deep crypto NY cell; ETH-primary, BTC oos/sealed-positive


def _hm(t):
    """SERVER-LOCAL (hour, minute). The constants here are FTMO server hours (F7/B29);
    the live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour_minute(t)


def _vol_state(bars, i):
    """Measurement only. ATR-rank label low/mid/high/na. Not the decision."""
    if i < VOL_WIN:
        return "na"
    a_i = atr14(bars, i)
    if a_i <= 0:
        return "na"
    lo = max(0, i - VOL_WIN)
    hist = [a for a in (atr14(bars, k) for k in range(lo, i)) if a > 0]
    if len(hist) < 50:
        return "na"
    rank = sum(1 for a in hist if a <= a_i) / len(hist)
    if rank < VOL_LO:
        return "low"
    if rank < VOL_HI:
        return "mid"
    return "high"


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """Emit a NY-killzone crypto momentum-continuation TradeIntent on the latest closed M15 bar, else None.

    Requires bar_times aligned 1:1 with bars or an explicit bar_time. Exit is a time-stop (MAXBARS) + stop-loss;
    target_dist is None by design. Leak-free (decision uses bars <= i, entry at close[i])."""
    if symbol not in ON_SURFACE or not bars:
        return None
    i = len(bars) - 1
    if i < MIN_BARS or i < WINDOW:
        return None
    t = bar_time if bar_time is not None else (bar_times[i] if bar_times and len(bar_times) == len(bars) else None)
    if t is None:
        return None
    h, m = _hm(t)
    if h != DECISION_HOUR or m != DECISION_MIN:        # fire ONLY at the NY decision bar
        return None
    a = atr14(bars, i)
    if a <= 0:
        return None
    vol_label = _vol_state(bars, i)
    blocked_vol = crypto_side(
        "ny_crypto_momentum_vol_not_mid_high",
        vol_label not in ("mid", "high"),
        "vol_blocks",
        "vol_open",
        "Condition: vol state is not mid or high. Which side of this condition is the decision?",
        true_text="Vol state is outside mid and high. Do not emit.",
        false_text="Vol state is mid or high.",
        facts={"symbol": symbol, "vol_state": vol_label, "low": VOL_LO, "high": VOL_HI},
    )
    if blocked_vol == "true" or blocked_vol is None:
        return None
    w = bars[i - WINDOW:i + 1]
    hi = max(b.h for b in w)
    lo = min(b.l for b in w)
    rng = hi - lo
    if rng <= 0:
        return None
    net = bars[i].c - bars[i - WINDOW].c
    de = net / rng
    dirty = crypto_side(
        "ny_crypto_momentum_de_below",
        abs(de) < DE_THRESH,
        "efficiency_below",
        "efficiency_clean",
        "Condition: absolute directional efficiency is below 0.50. Which side of this condition is the decision?",
        true_text="The session move is below 0.50 efficiency. Do not emit.",
        false_text="The session move is not below 0.50 efficiency.",
        facts={"symbol": symbol, "de": float(de), "floor": DE_THRESH},
    )
    if dirty == "true" or dirty is None:
        return None
    signed = crypto_side(
        "ny_crypto_momentum_net_up",
        net > 0,
        "net_up",
        "net_down",
        "Condition: window net is up. Which side of this condition is the decision?",
        true_text="The window net is up.",
        false_text="The window net is not up.",
        facts={"symbol": symbol, "net": float(net)},
    )
    if signed == "true":
        direction = 1
    elif signed == "false":
        direction = -1
    else:
        return None
    sd = STOP_MULT * a
    if sd <= 0:
        return None
    return TradeIntent(sleeve="ny_crypto_momentum", symbol=symbol, direction=direction,
                       decision_day=decision_day, stop_dist=sd, target_dist=None)
