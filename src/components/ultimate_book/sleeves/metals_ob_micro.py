"""metals_ob_micro sleeve — order-block-retest tail-frequency add (conf 0.30).

Byte-faithful port of the LOCKED route metals_ob_micro (Stage-2c of the metals stack):

  ENTRY DETECTOR  <- csb_commodity_setups.sig_ob (lines 80-108): a vol-gated, HTF-trend-aligned
    ORDER-BLOCK RETEST. In an uptrend (htf_trend lb=30 == +1): find the last opposite-color (DOWN)
    candle B[k] (B[k].c < B[k].o) immediately before an UP impulse (B[k+1].c > B[k].h); the signal
    fires when the current bar retests that order block — its low dips into the zone (b.l <= ob_top =
    B[k].h) yet it closes back up bullishly (b.c > ob_bot = B[k].l and b.c > b.o). Downtrend mirrors.
    Stop = max((b.c - min(b.l, ob_bot)) + 0.10*atr, 0.25*atr) (long; mirror for short). The OB window
    is ob_lookback=9 -> k scanned i-2 .. i-8, fires on the FIRST (closest-to-i) block (route `break`).

  SLEEVE GATES  <- INTEG_portfolio_build.gen_metals_ob_micro (lines 122-141):
    (1) ac60 = autocorr(bars, i, 60) >= 0.20 — the STRONG-persistence "micro" tail only (vs core's
        ac>=0.10 / softband's 0.04<=ac<0.10).
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
from . import metals
from ._metals_choice import ask, decision_stops

# admission.SLEEVE_REGISTRY["metals_ob_micro"].symbols; all 6 on the FTMO primary (34-instrument)
# universe. On the FN follower (27) only XAU/XAG exist -> the 4 crosses are filtered per-profile.
ON_SURFACE = ("XAUUSD", "XAGUSD", "XAUEUR", "XAGEUR", "XAUAUD", "XAGAUD")

# csb_commodity_setups.sig_ob defaults (lines 80-81) + the gen_metals_ob_micro micro gate (line 137).
TREND_LB = 30
STOP_BUF = 0.10
#: Shared legacy constant; retained as this module's public name.
ATR_STOP_FLOOR = DEFAULT_ATR_STOP_FLOOR
OB_LOOKBACK = 9
GATE_K = 1.2            # csb.GATE_K vol-expansion gate (atr14 >= 1.2 * SMA100(atr))
AC_MICRO_THR = 0.20    # gen_metals_ob_micro: ac60 >= 0.20 strong-persistence tail only


def vol_gate_ok(atrs, i, gate_k: float = GATE_K) -> Optional[bool]:
    """csb_commodity_setups.vol_gate_ok (lines 45-50): atr14(i) >= 1.2 * SMA100(atr), i>=100.

    None means this hop has no unique highest. False is not filled back in.
    """
    side = ask(
        "ob_vol_window",
        i < 100,
        "bars_short_of_100",
        "window_ready",
        "The vol window is short of 100 bars.",
        "The vol window has 100 bars.",
        i=i,
    )
    if side == "true":
        return False
    if side is None:
        return None
    if i < 100:
        return None
    a = atrs[i]
    side = ask(
        "ob_vol_atr",
        a <= 0,
        "atr_not_positive",
        "atr_positive",
        "ATR is not positive.",
        "ATR is positive.",
        i=i,
        atr=a,
    )
    if side == "true":
        return False
    if side is None:
        return None
    if not (a > 0):
        return None
    sma100 = sum(atrs[i - 99:i + 1]) / 100
    open_gate = sma100 > 0 and a >= gate_k * sma100
    side = ask(
        "ob_vol_gate",
        open_gate,
        "vol_gate_open",
        "vol_gate_closed",
        "ATR clears the vol-expansion gate.",
        "ATR is below the vol-expansion gate.",
        i=i,
        atr=a,
        sma100=sma100,
        gate_k=gate_k,
    )
    if side == "true":
        return True
    if side is None:
        return None
    return False


def _block_side(spot, measured, true_name, false_name, true_text, false_text, **facts):
    return ask(spot, measured, true_name, false_name, true_text, false_text, **facts)


def sig_ob(B, atrs, i) -> Optional[tuple[int, float]]:
    """(direction, stop_dist) if a vol-gated OB-retest fires on closed bar i, else None.

    Byte-faithful to csb_commodity_setups.sig_ob's per-bar body (lines 85-107): the same vol gate,
    htf_trend, order-block scan (k = i-2 .. max(i-9,60)+1, descending) and stop geometry. Fires on
    the first (closest-to-i) qualifying block — matching the route's `break`."""
    a = atrs[i]
    if decision_stops(_block_side(
        "ob_sig_atr",
        a <= 0,
        "atr_not_positive",
        "atr_positive",
        "ATR is not positive.",
        "ATR is positive.",
        i=i,
        atr=a,
    )):
        return None
    if not (a > 0):
        return None
    gate = vol_gate_ok(atrs, i)
    if decision_stops(_block_side(
        "ob_sig_vol",
        gate is not True,
        "vol_gate_closed",
        "vol_gate_open",
        "The vol gate did not open.",
        "The vol gate opened.",
        i=i,
    )):
        return None
    tr = metals.htf_trend(B, i, TREND_LB)
    b = B[i]
    up = _block_side(
        "ob_trend_up",
        tr == 1,
        "trend_up",
        "trend_not_up",
        "The higher-timeframe trend is up.",
        "The higher-timeframe trend is not up.",
        i=i,
        trend=tr,
    )
    if up == "true":
        for k in range(i - 2, max(i - OB_LOOKBACK, 60), -1):
            down_candle = B[k].c < B[k].o
            side = _block_side(
                "ob_long_candle",
                not down_candle,
                "not_a_down_candle",
                "down_candle",
                "This bar is not the down candle of a bullish order block.",
                "This bar is the down candle of a bullish order block.",
                i=i,
                k=k,
            )
            if side == "true":
                continue
            if side is None:
                return None
            impulse = B[k + 1].c > B[k].h
            side = _block_side(
                "ob_long_impulse",
                not impulse,
                "impulse_absent",
                "impulse_up",
                "The next bar did not close above the order-block high.",
                "The next bar closed above the order-block high.",
                i=i,
                k=k,
            )
            if side == "true":
                continue
            if side is None:
                return None
            ob_top, ob_bot = B[k].h, B[k].l
            held = b.l <= ob_top and b.c > ob_bot and b.c > b.o
            side = _block_side(
                "ob_long_retest",
                held,
                "long_retest_holds",
                "long_retest_absent",
                "Price retested the bullish order block and closed back up.",
                "Price did not retest the bullish order block.",
                i=i,
                k=k,
            )
            if side == "true":
                sd = floor_stop((b.c - min(b.l, ob_bot)) + STOP_BUF * a, a, ATR_STOP_FLOOR)
                return 1, sd
            if side is None:
                return None
    elif up is None:
        return None
    else:
        down = _block_side(
            "ob_trend_down",
            tr == -1,
            "trend_down",
            "trend_not_down",
            "The higher-timeframe trend is down.",
            "The higher-timeframe trend is not down.",
            i=i,
            trend=tr,
        )
        if down == "true":
            for k in range(i - 2, max(i - OB_LOOKBACK, 60), -1):
                up_candle = B[k].c > B[k].o
                side = _block_side(
                    "ob_short_candle",
                    not up_candle,
                    "not_an_up_candle",
                    "up_candle",
                    "This bar is not the up candle of a bearish order block.",
                    "This bar is the up candle of a bearish order block.",
                    i=i,
                    k=k,
                )
                if side == "true":
                    continue
                if side is None:
                    return None
                impulse = B[k + 1].c < B[k].l
                side = _block_side(
                    "ob_short_impulse",
                    not impulse,
                    "impulse_absent",
                    "impulse_down",
                    "The next bar did not close below the order-block low.",
                    "The next bar closed below the order-block low.",
                    i=i,
                    k=k,
                )
                if side == "true":
                    continue
                if side is None:
                    return None
                ob_top, ob_bot = B[k].h, B[k].l
                held = b.h >= ob_bot and b.c < ob_top and b.c < b.o
                side = _block_side(
                    "ob_short_retest",
                    held,
                    "short_retest_holds",
                    "short_retest_absent",
                    "Price retested the bearish order block and closed back down.",
                    "Price did not retest the bearish order block.",
                    i=i,
                    k=k,
                )
                if side == "true":
                    sd = floor_stop((max(b.h, ob_top) - b.c) + STOP_BUF * a, a, ATR_STOP_FLOOR)
                    return -1, sd
                if side is None:
                    return None
        elif down is None:
            return None
    return None


def generate(symbol: str, bars, decision_day: str, **_) -> Optional[TradeIntent]:
    """Emit a metals_ob_micro TradeIntent on the latest closed bar i=len(bars)-1, or None.
    Accepts (and ignores) the engine's uniform kwargs (bar_time/bar_times/aux_*) — no session/aux need.

    DEDUP-VS-FVG faithfulness: the route (gen_metals_ob_micro) drops an OB-micro entry when an FVG
    entry exists for the SAME (symbol, date, direction); its `fvg_keys` are built from every FVG
    signal whose `ac is not None` (i.e. it dedups against ANY FVG that fired that day, irrespective
    of the ac>=0.10 / 0.04<=ac<0.10 bands that core/softband actually trade). A per-symbol/per-bar
    live generator cannot observe other symbols' or other bars'/days' FVG state, so the faithful
    reduction is the SAME-bar, same-direction FVG: we call metals.fvg_signal(bars, atrs, i) and, if
    it fires in direction d, return None (the FVG core/softband sleeve owns that trade). This is exact
    for the dominant case (FVG and OB on the SAME decision bar) and is the correct conservative
    reduction of the route's cross-bar/cross-day day-level key under a one-bar-per-decision engine.
    Note ac>=0.20 here implies ac is not None at bar i, so the route's `ac is not None` FVG-key
    precondition is automatically met whenever this generator reaches the dedup check.
    """
    if decision_stops(ask(
        "ob_surface",
        symbol not in ON_SURFACE or not bars,
        "off_surface_or_no_bars",
        "on_named_surface",
        "The symbol is off the metals surface, or there are no bars.",
        "The symbol is on the metals surface and bars exist.",
        symbol=symbol,
        n_bars=0 if not bars else len(bars),
    )):
        return None
    if not bars:
        return None
    if decision_stops(ask(
        "ob_warmup",
        len(bars) < 200,
        "bars_short_of_200",
        "warmup_complete",
        "The series is short of 200 bars.",
        "The series has 200 bars.",
        symbol=symbol,
        n=len(bars),
    )):
        return None
    i = len(bars) - 1
    atrs = [atr14(bars, k) for k in range(len(bars))]
    sig = sig_ob(bars, atrs, i)
    if decision_stops(ask(
        "ob_signal",
        sig is None,
        "order_block_absent",
        "order_block_present",
        "No order-block retest is on this bar.",
        "An order-block retest is on this bar.",
        symbol=symbol,
        i=i,
    )):
        return None
    if sig is None:
        return None
    d, sd = sig
    ac = autocorr(bars, i, 60)
    if decision_stops(ask(
        "ob_ac60",
        ac is None or ac < AC_MICRO_THR,
        "outside_micro_band",
        "inside_micro_band",
        "ac60 is missing or below 0.20.",
        "ac60 is at or above 0.20.",
        symbol=symbol,
        ac=ac,
    )):
        return None
    fvg = metals.fvg_signal(bars, atrs, i)
    same = fvg is not None and fvg[0] == d
    if decision_stops(ask(
        "ob_fvg_dedup",
        same,
        "fvg_owns_this_bar",
        "order_block_owns_this_bar",
        "A same-direction FVG already owns this bar.",
        "No same-direction FVG owns this bar.",
        symbol=symbol,
        i=i,
        direction=d,
    )):
        return None
    vr = vol_ratio(atrs, i)
    rr = metals._runner_R(vr)
    if decision_stops(ask(
        "ob_runner",
        rr is None,
        "runner_unset",
        "runner_set",
        "No runner R was chosen.",
        "A runner R was chosen.",
        symbol=symbol,
        vr=vr,
    )):
        return None
    if rr is None:
        return None
    return TradeIntent(sleeve="metals_ob_micro", symbol=symbol, direction=d,
                       decision_day=decision_day, stop_dist=sd,
                       target_dist=rr * sd)
