"""London low-vol crypto killzone momentum continuation.

Default-off research candidate. This is the London-session sibling of the
NY crypto momentum sleeve, but it is a distinct decision surface:
BTC/ETH M15, server 12:00 decision bar, trailing ATR low-vol regime only,
clean 09:00-12:00 directional-efficiency move, then hold-to-close/time-stop.

Research proof, 2026-06-17:
- raw trades n=813, train/oos/sealed meanR +0.2599/+0.1543/+0.4239.
- daily unit n=627, train/oos/sealed +0.115631/+0.133007/+0.243072.
- canonical verifier requires 813/813 reference parity and zero false positives.

Book caveat: at the old scratch confidence this was a weak additive. It is
promoted only at low book-watch confidence after the tuned current+KZ+VSS book
showed a better MC profile. Not live authority.
"""

from __future__ import annotations

from typing import Optional

from ..admission import TradeIntent
from ..primitives import atr14
from ._server_clock import server_hour_minute
from .crypto_choices import crypto_side


DE_THRESH = 0.50
STOP_MULT = 1.3
WINDOW = 12
DECISION_HOUR = 12
DECISION_MIN = 0
MAXBARS = 32
VOL_WIN = 480
VOL_LO = 0.34
MIN_BARS = 520
ON_SURFACE = ("BTCUSD", "ETHUSD")


def _hm(t):
    """SERVER-LOCAL (hour, minute). The constants here are FTMO server hours (F7/B29);
    the live feed is true UTC, so this converts before comparing. None -> fail closed."""
    return server_hour_minute(t)


def _low_vol(bars, i: int) -> bool:
    """Measurement only. ATR rank < 0.34. Not the decision."""
    if i < VOL_WIN:
        return False
    a_i = atr14(bars, i)
    if a_i <= 0:
        return False
    hist = [a for a in (atr14(bars, k) for k in range(i - VOL_WIN, i)) if a > 0]
    if len(hist) < 50:
        return False
    rank = sum(1 for a in hist if a <= a_i) / len(hist)
    return rank < VOL_LO


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
    """Emit one London low-vol crypto continuation intent on the latest closed M15 bar."""
    if symbol not in ON_SURFACE or not bars:
        return None
    i = len(bars) - 1
    if i < MIN_BARS or i < WINDOW:
        return None
    t = bar_time if bar_time is not None else (bar_times[i] if bar_times and len(bar_times) == len(bars) else None)
    h, m = _hm(t)
    if h != DECISION_HOUR or m != DECISION_MIN:
        return None
    a = atr14(bars, i)
    if a <= 0:
        return None
    vol = crypto_side(
        "kz_london_crypto_low_not_low_vol",
        not _low_vol(bars, i),
        "vol_not_low",
        "vol_low",
        "Condition: ATR rank is not below 0.34. Which side of this condition is the decision?",
        true_text="ATR rank is not in the low band. Do not emit.",
        false_text="ATR rank is in the low band. The vol side of this fire is open.",
        facts={"symbol": symbol, "low": VOL_LO},
    )
    if vol == "true" or vol is None:
        return None

    window = bars[i - WINDOW : i + 1]
    hi = max(b.h for b in window)
    lo = min(b.l for b in window)
    rng = hi - lo
    if rng <= 0:
        return None
    net = bars[i].c - bars[i - WINDOW].c
    dirty = crypto_side(
        "kz_london_crypto_low_de_below",
        abs(net / rng) < DE_THRESH,
        "efficiency_below",
        "efficiency_clean",
        "Condition: absolute directional efficiency is below 0.50. Which side of this condition is the decision?",
        true_text="The window move is below 0.50 efficiency. Do not emit.",
        false_text="The window move is not below 0.50 efficiency.",
        facts={"symbol": symbol, "net": float(net), "range": float(rng), "floor": DE_THRESH},
    )
    if dirty == "true" or dirty is None:
        return None
    signed = crypto_side(
        "kz_london_crypto_low_net_up",
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
    stop_dist = STOP_MULT * a
    if stop_dist <= 0:
        return None
    return TradeIntent(
        sleeve="kz_london_crypto_low",
        symbol=symbol,
        direction=direction,
        decision_day=decision_day,
        stop_dist=stop_dist,
        target_dist=None,
    )
