"""vp_euidx_pocgrav sleeve — EU-index prior-day volume-profile POC-gravitation (conf 0.30).

Byte-faithful port of the LOCKED route generator
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/
    KB5_fold_new_sleeves.py:64-92  (_vp_pocgrav_rows / gen_vp_euidx_pocgrav, far=2.0 vr_min=1.2)

THE RULE (route _vp_pocgrav_rows per-bar body, lines 73-89): on H4 decision bar i, fetch the PRIOR
completed UTC day's M1 volume profile (vp.prior_profile_at — leak-free, strictly < the decision day),
classify the current H4 close against it (vp.nearest_node_state), and FIRE iff
  |d_poc_atr| >= 2.0   (price >= 2*ATR from prior-day POC)          [route: abs(dpoc) < far -> skip]
  AND NOT in_va        (price outside the prior-day 70% value area) [route: st["in_va"] -> skip]
  AND vr = vol_ratio(atrs, i) >= 1.2                                [route: vr < vr_min -> skip]
  AND target_dist = |price - POC| >= 0.8 * stop_dist               [route: < 0.8*stop -> skip]
direction d = -1 if price>POC (dpoc>0) else +1 (gravitate toward the POC); stop_dist = 1.0*ATR14(H4);
target_dist = |price - POC| (a MEASURED move to the POC, NOT an R-multiple). ON_SURFACE GER40,UK100.

LIVE ADAPTATION vs the route backtest:
  * The route loads M1 from CSV (vp.load_m1) inside vp.daily_profiles; the live port builds the same
    profiles from the engine's secondary M1 feed (aux_bars=closed M1 Bars with tick_volume in .v,
    aux_times=aligned UTC datetimes) via the vendored volume_profile.daily_profiles(aux_bars,aux_times).
  * The route loops over all history (range(101, n-1)); the LIVE generator evaluates ONLY the latest
    closed H4 bar i = len(bars)-1 (the bar the engine just closed). The SIGNAL at i depends solely on
    data index<=i (atrs[i], price=bars[i].c, vol_ratio over [i-99..i], the prior-day M1 profile), so
    this is the exact route signal for that bar — the route's n-1 upper bound is only a forward-sim
    reservation for the OUTCOME label, which the live decision path does not compute.

FAIL-CLOSED (correctness > firing — this sleeve is forward-only-flagged): off-surface symbol, fewer
than 200 closed H4 bars, no/aligned M1 aux feed, no decision-bar timestamp, ATR<=0, no prior-day
profile, or any gate miss -> return None. The sleeve never guesses a profile it cannot build.
"""
from __future__ import annotations
from datetime import timezone
from typing import Optional

from ..primitives import atr14, vol_ratio
from ..admission import TradeIntent
from . import volume_profile as vp
from .spot_choice import all_false, ask, bar_id

# admission.CLEAN3_REGISTRY["vp_euidx_pocgrav"].symbols (admission.py:223-229); both in the 27-universe.
ON_SURFACE = ("GER40", "UK100")

# route gen_vp_euidx_pocgrav constants (KB5_fold_new_sleeves.py:64,96 -> far=2.0, vr_min=1.2) and the
# _vp_pocgrav_rows geometry (lines 87-89: stop = 1.0*ATR; target = |price-POC|; min RR 0.8*stop).
WARMUP_H4 = 200      # route _vp_pocgrav_rows guard: len(B) < 200 -> no signal (KB5 line 65)
FAR = 2.0            # |d_poc_atr| >= FAR
VR_MIN = 1.2         # vol_ratio(atrs, i) >= VR_MIN
STOP_ATR = 1.0       # stop_dist = STOP_ATR * ATR14(H4)
MIN_RR = 0.8         # target_dist >= MIN_RR * stop_dist
SLEEVE = "vp_euidx_pocgrav"


def _utc_date(t):
    """Decision-bar UTC date (route uses T[i].date()). Normalize tz-aware -> UTC before .date() so the
    day comparison against the (UTC) M1 profile days is consistent; naive datetimes (route/synthetic
    fixtures) are left untouched. Mirrors volume_profile._to_utc on the M1 side."""
    tz = getattr(t, "tzinfo", None)
    return (t.astimezone(timezone.utc) if tz is not None else t).date()


def measured(symbol, bars, *, bar_time=None, bar_times=None, aux_bars=None, aux_times=None) -> dict:
    """Facts for the latest closed H4 bar. Not a decision. Does not invent a profile."""
    n = len(bars) if bars else 0
    i = n - 1
    t = None
    if bar_times is not None and bars and len(bar_times) == n:
        t = bar_times[i]
    elif bar_time is not None:
        t = bar_time
    warmup_short = n < WARMUP_H4
    no_m1 = not aux_bars or not aux_times
    no_time = t is None
    a = 0.0
    atrs = None
    if bars and not warmup_short:
        atrs = [atr14(bars, k) for k in range(n)]
        a = atrs[i]
    no_days = True
    on_or_before = True
    no_dp = True
    no_st = True
    not_far = True
    vr_low = True
    rr_short = True
    direction = 0
    stop_dist = 0.0
    target_dist = 0.0
    entry = None
    if (
        bars
        and not warmup_short
        and not no_m1
        and not no_time
        and a > 0
        and atrs is not None
    ):
        try:
            profs, days = vp.daily_profiles(aux_bars, aux_times, bin_atr_frac=vp.BIN_FRAC)
            no_days = not days
            if days and _utc_date(t) > days[0]:
                on_or_before = False
                dp = vp.prior_profile_at(profs, days, t)
                no_dp = dp is None
                if dp is not None:
                    price = bars[i].c
                    st = vp.nearest_node_state(dp, price, a)
                    no_st = st is None
                    if st is not None:
                        vr = vol_ratio(atrs, i)
                        dpoc = st["d_poc_atr"]
                        not_far = abs(dpoc) < FAR or st["in_va"]
                        vr_low = vr < VR_MIN
                        direction = -1 if dpoc > 0 else 1
                        stop_dist = STOP_ATR * a
                        target_dist = abs(price - dp.poc)
                        rr_short = target_dist < MIN_RR * stop_dist
                        if dp.poc and float(dp.poc) > 0:
                            entry = float(dp.poc)
        except Exception:
            no_days = True
    return {
        "off_surface": symbol not in ON_SURFACE,
        "warmup_short": warmup_short,
        "no_m1": no_m1,
        "no_bar_time": no_time,
        "atr_not_a_scale": not (a > 0),
        "no_profile_days": no_days,
        "on_or_before_first_profile_day": on_or_before,
        "no_prior_profile": no_dp,
        "no_node_state": no_st,
        "inside_or_not_far": not_far,
        "vol_ratio_below": vr_low,
        "target_below_min_rr": rr_short,
        "direction": direction,
        "stop_dist": float(stop_dist),
        "target_dist": float(target_dist),
        "entry": entry,
    }


def generate(symbol: str, bars, decision_day: str, *, bar_time=None, bar_times=None,
             aux_bars=None, aux_times=None, **_) -> Optional[TradeIntent]:
    """POC gravitation on GER40 and UK100. Each gate is one spot Choice."""
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
    sides = ask(
        sleeve=SLEEVE,
        symbol=symbol,
        bar_id=bar_id(decision_day, len(bars), bar_time, bar_times),
        spots={
            "off_surface": {
                "condition": f"{symbol} is not GER40 or UK100",
                "measured": facts["off_surface"],
            },
            "warmup_short": {
                "condition": f"closed H4 count is below {WARMUP_H4}",
                "measured": facts["warmup_short"],
            },
            "no_m1": {
                "condition": "the prior-day M1 feed is missing",
                "measured": facts["no_m1"],
            },
            "no_bar_time": {
                "condition": "the decision bar has no timestamp",
                "measured": facts["no_bar_time"],
            },
            "atr_not_a_scale": {
                "condition": "ATR14 is not a positive scale",
                "measured": facts["atr_not_a_scale"],
            },
            "no_profile_days": {
                "condition": "the M1 volume profile has no days",
                "measured": facts["no_profile_days"],
            },
            "on_or_before_first_profile_day": {
                "condition": "the decision day is on or before the first profile day",
                "measured": facts["on_or_before_first_profile_day"],
            },
            "no_prior_profile": {
                "condition": "there is no prior-day volume profile",
                "measured": facts["no_prior_profile"],
            },
            "no_node_state": {
                "condition": "the close has no nearest-node state against the prior profile",
                "measured": facts["no_node_state"],
            },
            "inside_or_not_far": {
                "condition": "price is inside the value area or closer than 2 ATR to the POC",
                "measured": facts["inside_or_not_far"],
            },
            "vol_ratio_below": {
                "condition": "volume ratio is below 1.2",
                "measured": facts["vol_ratio_below"],
            },
            "target_below_min_rr": {
                "condition": "the distance to the POC is below 0.8 of the stop",
                "measured": facts["target_below_min_rr"],
            },
        },
    )
    if not all_false(sides):
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
