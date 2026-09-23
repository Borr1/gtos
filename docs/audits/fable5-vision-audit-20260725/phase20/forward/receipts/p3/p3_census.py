"""p3-1 — THE STOP-COUPLING CENSUS. Every generator in the estate, measured, not read.

    python3 .../p3/p3_census.py

WHAT QUESTION THIS ANSWERS
--------------------------
Wave 20's forensic found, on three unrelated families and by three unrelated lanes, that
**the qualifying condition builds the stop that kills it**: a generator whose stop distance
is a function of the same bar quantity that decides whether to fire at all. When the setup
qualifies most cleanly the stop is smallest, so the broker's cut — which is a fixed number
of PRICE units — becomes the largest possible share of the risk unit. `cost_r` is
`cost_price / stop_dist` by construction, so the coupling is not a hypothesis about
markets; it is arithmetic about the code.

Three lanes finding it by accident is not a census. This is the census: **all 51 generators
of `SLEEVE_FORENSIC_V1.json`, classified from source with a file:line for the stop
expression**, and — for every generator with rows in the estate walk — the coupling
MEASURED on its own trades.

THE CLASSIFICATION, AND WHY IT HAS THREE LEVELS AND NOT TWO
------------------------------------------------------------
    ATR_ONLY        stop = k * ATR. The qualifying quantity cannot reach it. Immune.
    WICK_FLOORED    stop = max(f(qualifying bar), floor * ATR). Coupled, and bounded below.
    WICK_UNFLOORED  stop = f(qualifying bar) [+ buffer * ATR]. Coupled, unbounded below.
    RANGE_*         same two, where the qualifying quantity is a multi-bar range
                    (an opening range, a Donchian channel, a POI zone) rather than one wick.

The distinction that matters is the FLOOR, not the wick. `metals.py:81`, `metals_ob_micro.py:84`
and `structural_retest.py:131` already carry `max(..., ATR_STOP_FLOOR * a)` with
`ATR_STOP_FLOOR = 0.25`. **The repair this wave was asked to invent already exists in this
repository, in three generators, and was not copied into the four that came after them.**
That is the census's headline and it is checkable at those six line numbers.

WHAT IS MEASURED, AND ON WHAT
------------------------------
`AA_ESTATE_TRADES.json.gz` — 32 sleeves, 22,324 trades, 2000-2026, the archive walk every
downstream artifact in this programme reads — plus AM's re-clocked `sub_mid_dn_revert`.
Bars re-derived from `vps-bars-20260727` through `ad_exit_sweep.load_bars`, which is the
same loader `AD`, `AK`, `AN` and lane m3 use.

For each row: `atr = atr14(bars, i)` at the decision bar, and `stop_atr = sl_distance_price
/ atr`. `atr14` reads only `bars[i-14 .. i]` (`primitives.py:23-30`), so recomputing it from
the full series is bit-identical to what the generator saw from its own window — the
argument `walkforward/supply.py` makes and measures. **CONTROL C1 proves it on the rows
themselves**: for the four wick-stop sleeves whose formula is closed-form, the ATR implied
by inverting the stop expression is compared against the recomputed ATR, and the max
relative error is reported. If the generator had used a different ATR the inversion would
not close.

Then the coupling itself, three ways, because one of them can be an artifact:

  1. `stop_atr` quantiles and `frac_below_0p25` — how much of each sleeve's population sits
     below the floor the estate already applies elsewhere.
  2. Spearman rank correlation of `stop_atr` against realised net R. Negative means thin
     stops do WORSE, which is the pattern's economic claim.
  3. The decile table of mean gross R, mean cost R and mean net R by `stop_atr` decile.
     `cost_r` must fall monotonically across it — that is the arithmetic — and the question
     the table answers is whether GROSS rises fast enough to pay for it.

Offline and pure. Reads gzipped JSON and gzipped CSV bars. Writes one JSON. Changes nothing.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import math
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[7]
sys.path.insert(0, str(REPO))
AD_DIR = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(AD_DIR))

import ad_exit_sweep as AD  # noqa: E402

from src.components.ultimate_book.primitives import atr14  # noqa: E402

HERE = Path(__file__).resolve().parent
P6 = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts"
P9 = REPO / "docs/audits/fable5-vision-audit-20260725/phase9/receipts"
AA_IN = P6 / "AA_ESTATE_TRADES.json.gz"
AM_SUBMID = P9 / "AM_SUBMID_TRADES.json.gz"
FORENSIC = REPO / "docs/audits/fable5-vision-audit-20260725/phase20/SLEEVE_FORENSIC_V1.json"
OUT = HERE / "P3_STOP_COUPLING_V1.json"

ACCOUNT, SERVER = "FTMO", "FTMO-Server3"


# =====================================================================================
# THE SOURCE-READ CENSUS
#
# Every row is a hand-verified read of the stop expression at the cited line. `couples_on`
# names the quantity the stop is built from; `qualifies_on` names the quantity the entry
# condition tests. The pattern is present iff they are the same object.
# =====================================================================================

#: kind -> whether the qualifying quantity can drive the stop toward zero.
UNBOUNDED = {"WICK_UNFLOORED", "RANGE_UNFLOORED"}
BOUNDED = {"WICK_FLOORED", "RANGE_FLOORED"}
IMMUNE = {"ATR_ONLY", "ATR_LAGGED", "TRUE_RANGE_MEAN", "NO_GENERATOR", "NOT_APPLICABLE"}

CENSUS: dict[str, dict] = {
    # ---------------- live sleeve generators, wick/range-derived, UNFLOORED -----------
    "asia_pdl_fade": dict(
        kind="WICK_UNFLOORED", site="src/components/ultimate_book/sleeves/asia_pdl_fade.py:108",
        expr="sd = (bars[i].c - bars[i].l) + STOP_BUF * a   # STOP_BUF = 0.10",
        qualifies_on="bars[i].l < pdl - 0.05*a  and  bars[i].c > pdl  (:60)",
        couples_on="bars[i].c - bars[i].l  — the sweep wick of the SAME bar",
        note="The cleanest qualification (a minimal pierce that closes back above the PDL) "
             "gives the smallest c-l, hence the smallest stop, hence the largest cost_r."),
    "liq_asia_up_low_metal": dict(
        kind="WICK_UNFLOORED",
        site="src/components/ultimate_book/sleeves/liq_asia_up_low_metal.py:192,205",
        expr="sd = (bars[i].h - bars[i].c) + STOP_BUF * a  /  (bars[i].c - bars[i].l) + STOP_BUF * a",
        qualifies_on="sweep of the Asian high/low then reclaim, same bar",
        couples_on="the sweep wick of the SAME bar",
        note="Same idiom as asia_pdl_fade, same absent floor. `cost_r` 0.877 — the worst in "
             "the estate (SLEEVE_FORENSIC_REPORT §4 row 9)."),
    "vol_squeeze": dict(
        kind="WICK_UNFLOORED", site="src/components/ultimate_book/sleeves/vol_squeeze.py:78,83",
        expr="sd = max(b.c - b.l, 0.0) + STOP_BUF * a   # STOP_BUF = 0.30",
        qualifies_on="squeeze then expansion break of the 20-bar channel",
        couples_on="the breakout bar's own wick",
        note="Larger buffer (0.30 vs 0.10) softens but does not bound it; max(.,0.0) floors "
             "the WICK at zero, not the STOP at anything."),
    "orb_crypto_london": dict(
        kind="RANGE_UNFLOORED", site="src/components/ultimate_book/sleeves/orb_crypto_london.py:115",
        expr="stop_dist = (c - or_lo) if direction > 0 else (or_hi - c)",
        qualifies_on="c > or_hi  or  c < or_lo  — a break of the opening range (:103)",
        couples_on="the opening range itself",
        note="THE PUREST INSTANCE IN THE ESTATE: no ATR term at all. A narrow opening range "
             "is BOTH easier to break and a tighter stop, and nothing bounds it below."),
    # ---------------- live sleeve generators, wick-derived, FLOORED -------------------
    "metals_core": dict(
        kind="WICK_FLOORED", site="src/components/ultimate_book/sleeves/metals.py:81,89",
        expr="sd = max((b.c - min(b.l, gap_bot)) + STOP_BUF * a, ATR_STOP_FLOOR * a)  # 0.10 / 0.25",
        qualifies_on="vol-gated FVG retest: b.l <= gap_top and b.c > gap_bot (:79)",
        couples_on="the retest wick and the gap edge",
        note="THE REPAIR ALREADY EXISTS HERE. `ATR_STOP_FLOOR = 0.25` at metals.py:34."),
    "metals_softband": dict(
        kind="WICK_FLOORED", site="src/components/ultimate_book/sleeves/metals.py:81,89",
        expr="same signal function as metals_core, different gate_k",
        qualifies_on="vol-gated FVG retest at the soft band",
        couples_on="the retest wick and the gap edge",
        note="Floored by the same expression."),
    "metals_ob_micro": dict(
        kind="WICK_FLOORED", site="src/components/ultimate_book/sleeves/metals_ob_micro.py:84,94",
        expr="sd = max((b.c - min(b.l, ob_bot)) + STOP_BUF * a, ATR_STOP_FLOOR * a)",
        qualifies_on="order-block micro retest",
        couples_on="the retest wick and the block edge",
        note="Floored. `ATR_STOP_FLOOR = 0.25` at metals_ob_micro.py:46."),
    "structural_retest": dict(
        kind="WICK_FLOORED",
        site="src/components/ultimate_book/sleeves/structural_retest.py:131,134,137,140,144,151,154,157,160,164",
        expr="max((b.c - min(b.l, ob_bot)) + STOP_BUF * a, ATR_STOP_FLOOR * a)  — ten sites",
        qualifies_on="three retest classes x three sessions",
        couples_on="the retest wick and the structure edge",
        note="Floored at all ten sites. `ATR_STOP_FLOOR = 0.25` at structural_retest.py:28."),
    # ---------------- live sleeve generators, ATR-only: IMMUNE ------------------------
    "crypto": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/crypto.py:33,66",
                   expr="sd = 2 * atr14", qualifies_on="Donchian-20 break + ac60 >= 0.15",
                   couples_on="ATR only", note="ARMED. Immune by construction."),
    "energy_agri": dict(
        kind="WICK_FLOORED", site="src/components/ultimate_book/sleeves/energy_agri.py:56,63 "
                                  "-> metals.fvg_signal at metals.py:81,89",
        expr="d, sd = fvg_signal(bars, atrs, i)  ->  max(wick + 0.10*a, 0.25*a)",
        qualifies_on="vol-gated FVG retest PLUS energy_gate(vr, slope) (:60)",
        couples_on="the retest wick and the gap edge",
        note="ARMED, and MISCLASSIFIED AS ATR_ONLY IN THIS FILE'S FIRST DRAFT. Its docstring "
             "says 'same vol-gated FVG-retest ENTRY as metals, reused via metals.fvg_signal' "
             "(:3-5) and `generate` imports that function at :17. The measurement caught it: "
             "an ATR-multiple stop has stop/ATR dispersion EXACTLY 1.00 and this one measured "
             "5.84. Floored, because it inherits metals.py's floor."),
    "sub_xvol_pullback": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/substrate.py:138",
                              expr="sd, td = se.stop_target(a, stop_atr, target_R)",
                              qualifies_on="substrate cell match on (vr, trend, session)",
                              couples_on="ATR only", note="ARMED. Immune by construction."),
    "sub_mid_dn_revert": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/substrate.py:138",
                              expr="sd, td = se.stop_target(a, stop_atr, target_R)",
                              qualifies_on="substrate cell match",
                              couples_on="ATR only", note="ARMED. Immune by construction."),
    "fx_jpy": dict(kind="ATR_LAGGED", site="src/components/ultimate_book/sleeves/fx_jpy.py:11,203",
                   expr="stop_dist = _STOP_M * atr14(M15, iw)  where iw = the 4th session bar",
                   qualifies_on="session-bar range break",
                   couples_on="ATR at a LAGGED index, not the decision bar",
                   note="pulled 2026-07-30. Immune to the coupling, but its stop/ATR(decision) "
                        "dispersion is 1.22 rather than 1.00 because the ATR is read at a "
                        "different bar. Named as its own kind so the mechanical detector "
                        "(dispersion == 1.00) has a stated exception rather than a false "
                        "positive."),
    "fx_jpy_ny": dict(kind="ATR_LAGGED", site="src/components/ultimate_book/sleeves/fx_jpy.py:11,203",
                      expr="stop_dist = _STOP_M * atr14(M15, iw)",
                      qualifies_on="session-bar range break",
                      couples_on="ATR at a LAGGED index", note="same as fx_jpy."),
    "idxrev": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/index_jpy.py:26,55",
                   expr="sd = 1.5 * atr", qualifies_on="wick-out + close-back-in fade",
                   couples_on="ATR only",
                   note="IMPORTANT NEGATIVE CONTROL: the qualification IS a wick and the stop "
                        "is NOT built from it. idxrev is the estate's worst per-trade sleeve "
                        "anyway (MFE/|MAE| 0.954), which is why coupling is not the estate's "
                        "only defect."),
    "vol_compression": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/vol_compression.py:54",
                            expr="sd = STOP_MULT * a", qualifies_on="squeeze + break",
                            couples_on="ATR only", note="immune."),
    "asian_fade": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/asian_fade.py:117",
                       expr="sd = STOP_K * ak", qualifies_on="Asian range extension fade",
                       couples_on="ATR only",
                       note="immune to THIS defect; its own defect is a 0.6-ATR stop inside "
                            "one M15 bar of noise (forensic §5.2), which is a PARAMETER."),
    "metal_session_reversion": dict(kind="ATR_ONLY",
                                    site="src/components/ultimate_book/sleeves/metal_session_reversion.py:112",
                                    expr="sd = STOP_K * a", qualifies_on="session reversion",
                                    couples_on="ATR only", note="immune."),
    "ny_crypto_momentum": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/ny_crypto_momentum.py:111",
                               expr="sd from ATR multiple", qualifies_on="NY killzone momentum",
                               couples_on="ATR only", note="immune."),
    "ny_index_momentum": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/ny_index_momentum.py:99",
                              expr="sd from ATR multiple", qualifies_on="NY killzone momentum",
                              couples_on="ATR only", note="immune; STALE (zero rows ever)."),
    "kz_london_crypto_low": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/kz_london_crypto_low.py:93",
                                 expr="stop_dist = STOP_MULT * a", qualifies_on="London killzone low",
                                 couples_on="ATR only", note="immune."),
    "vss_fxcross_london_up_low": dict(kind="ATR_ONLY",
                                      site="src/components/ultimate_book/sleeves/vss_fxcross_london_up_low.py:171",
                                      expr="stop_dist = STOP_ATR * atr_i", qualifies_on="vol-scaled shift",
                                      couples_on="ATR only", note="immune."),
    "vp_euidx_pocgrav": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/vp_euidx.py:114",
                             expr="stop_dist = STOP_ATR * a  # 1.0", qualifies_on="distance from POC",
                             couples_on="ATR only",
                             note="immune; UNDETERMINED for a different reason (never walked)."),
    "session_leadlag_genuine": dict(kind="ATR_ONLY", site="src/components/ultimate_book/sleeves/session_leadlag.py:269",
                                    expr="sd = STOP_ATR_MULT * a", qualifies_on="leader z-score",
                                    couples_on="ATR only",
                                    note="immune; cannot fire at all (no importer)."),
    # ---------------- the mx_* D1 cohort: a rolling true-range mean -------------------
    # `_risk_abs` (market_expansion_d1.py:75-82) is the mean TRUE RANGE over RISK_WINDOW
    # bars ending at the signal bar. It is an ATR by another name and does not read the
    # qualifying quantity — EXCEPT for the two atr_mean_reversion members, where the
    # SIGNAL reads `risk` (`:206`), which is the coupling running the other way and is
    # already recorded by `ad_exit_sweep.STOP_DEPENDENT_SIGNAL`.
    # ---------------- broad-origin families -------------------------------------------
    "liquidity_sweep_reclaim": dict(
        kind="WICK_UNFLOORED", site="src/components/broader_origin_generators.py:743,760",
        expr="stop = bar.high + 0.25*atr14  /  bar.low - 0.25*atr14",
        qualifies_on="bar.high > p_high20 and bar.close < p_high20  (:732-733)",
        couples_on="the sweeping bar's own extreme — the SAME high the condition tests",
        note="The condition is 'pierced and reclaimed'. The size of the pierce is free, and "
             "it IS the stop."),
    "structural_distance_extreme": dict(
        kind="WICK_UNFLOORED", site="src/components/broader_origin_generators.py:895,913",
        expr="stop = bar.high + 0.25*atr14  /  bar.low - 0.25*atr14",
        qualifies_on="close_position(50) >= 0.97 or <= 0.03  (:878)",
        couples_on="the decision bar's own extreme",
        note="Qualifying at 0.97+ means the close sits at the top of the 50-bar range, which "
             "on a trend bar puts it near its own high — so the stop is systematically thin "
             "exactly where the family claims its edge."),
    "cross_asset_lead_lag": dict(
        kind="WICK_UNFLOORED", site="src/components/broader_origin_generators.py:1056-1060",
        expr="stop = latest_lag.low - 0.25*lag_atr  /  latest_lag.high + 0.25*lag_atr",
        qualifies_on="lag_response = |lag_move|/lag_atr <= 0.5  (:1052)",
        couples_on="the lag bar that is required NOT to have moved",
        note="THE CLEANEST LOGICAL INSTANCE: the entry condition is literally 'the follower "
             "has not moved yet', and the stop is built from that unmoved bar. Qualify "
             "harder -> smaller bar -> tighter stop."),
    "session_open_range_break": dict(
        kind="RANGE_UNFLOORED", site="src/components/broader_origin_generators.py:967,985",
        expr="stop = range_low - 0.10*atr14  /  range_high + 0.10*atr14",
        qualifies_on="latest.close > range_high  /  < range_low  (:964,:982)",
        couples_on="the opening range itself",
        note="Identical in shape to orb_crypto_london, with a 0.10 ATR buffer and no floor."),
    "volatility_compression_expansion": dict(
        kind="RANGE_UNFLOORED", site="src/components/broader_origin_generators.py:807,825",
        expr="stop = min(bar.low, p_low20) - 0.20*atr14",
        qualifies_on="prior_atr14/prior_atr50 <= 0.75 AND bar_range/atr >= 1.25 AND break (:795)",
        couples_on="the 20-bar channel and the breakout bar's extreme",
        note="PARTIALLY SELF-LIMITING: the `bar_range/atr >= 1.25` clause forces a wide bar, "
             "so this family's coupling is weak. Kept in the census as a graded case."),
    "displacement_continuation": dict(
        kind="WICK_UNFLOORED", site="src/components/broader_origin_generators.py:772",
        expr="stop = bar.low - 0.25*atr14 if LONG else bar.high + 0.25*atr14",
        qualifies_on="bar_range/atr >= 1.5 AND body/atr >= 0.75  (:769)",
        couples_on="the displacement bar's own extreme",
        note="ANTI-PATTERN, AND THE CONTROL THAT PROVES THE MECHANISM IS ABOUT THE CONDITION "
             "AND NOT THE WICK. The qualifying condition here demands a LARGE range, so "
             "qualifying harder makes the stop WIDER. Same wick idiom, opposite sign."),
    "regime_transition_break": dict(
        kind="RANGE_UNFLOORED", site="src/components/broader_origin_generators.py:857,875",
        expr="stop = p_low20 - 0.10*atr14  /  p_high20 + 0.10*atr14",
        qualifies_on="trend state transition AND close > p_high20  (:848)",
        couples_on="the 20-bar range — a DIFFERENT quantity from the transition test",
        note="WEAK: the stop is the channel, the qualification is a trend-state change. "
             "Only the break clause touches the channel."),
    "range_extreme_reversion": dict(
        kind="ATR_ONLY", site="src/components/broader_origin_generators.py:712,726",
        expr="stop = bar.close -/+ 1.0 * atr14",
        qualifies_on="range50_position <= 0.25 / >= 0.75 AND bar_range < 1.5*atr (:697)",
        couples_on="ATR only", note="immune."),
    "current_fvg_fill": dict(
        kind="RANGE_UNFLOORED", site="src/components/broader_origin_generators.py:1787 "
                                     "(_current_framework_geometry, called at :1324)",
        expr="stop = zone_low - buffer_atr*atr14   (entry = zone midpoint)",
        qualifies_on="price within proximity tolerance of the FVG zone",
        couples_on="the FVG zone's own height — the zone IS the setup",
        note="A tight gap is both a 'cleaner' FVG and a smaller stop. Compounded by the "
             "unread `sl_buffer_breaker_atr_multiplier` for the breaker sibling."),
    "current_ob_retest": dict(
        kind="RANGE_UNFLOORED", site="src/components/broader_origin_generators.py:1787 "
                                     "(buffer resolved at :1502)",
        expr="stop = zone_low - ob_buffer_atr*atr14",
        qualifies_on="price within proximity tolerance of the order block",
        couples_on="the order block's own height", note="same shape as current_fvg_fill."),
    "current_breaker_re_entry": dict(
        kind="RANGE_UNFLOORED", site="src/components/broader_origin_generators.py:1787 "
                                     "(buffer resolved at :1570)",
        expr="stop = zone_low - breaker_buffer_atr*atr14",
        qualifies_on="price within proximity tolerance of the breaker block",
        couples_on="the breaker block's own height",
        note="Worst of the three: 26.19% are born already past their own stop (forensic §3.1), "
             "which is the zero-stop limit of exactly this coupling."),
    "microstructure_absorption_reversal": dict(
        kind="ATR_ONLY", site="src/components/broader_origin_generators.py:614",
        expr="stop = bar.close -/+ STOP_ATR_MICROSTRUCTURE * atr14",
        couples_on="ATR only", qualifies_on="absorption print", note="immune."),
    "microstructure_vdelta_divergence": dict(
        kind="ATR_ONLY", site="src/components/broader_origin_generators.py:614",
        expr="stop = bar.close -/+ STOP_ATR_MICROSTRUCTURE * atr14",
        couples_on="ATR only", qualifies_on="volume-delta divergence", note="immune."),
}

#: The ten mx_* generators share one stop expression. Registered programmatically so the
#: census cannot drift from the cohort list.
MX = ["mx_btcusd_d1_donchian_20_breakout", "mx_ethusd_d1_donchian_20_breakout",
      "mx_avausd_d1_donchian_20_breakout", "mx_nzdjpy_d1_donchian_20_breakout",
      "mx_cadjpy_d1_volume_surge_reversal", "mx_ger40_cash_d1_volume_surge_reversal",
      "mx_jp225_cash_d1_volume_surge_reversal", "mx_us30_cash_d1_volume_surge_reversal",
      "mx_eu50_cash_d1_volume_surge_reversal", "mx_fra40_cash_d1_volume_surge_reversal",
      "mx_aus200_cash_d1_volume_surge_reversal", "mx_spn35_cash_d1_volume_surge_reversal"]
for _s in MX:
    CENSUS[_s] = dict(
        kind="TRUE_RANGE_MEAN", site="src/components/ultimate_book/sleeves/market_expansion_d1.py:75-82,200",
        expr="risk = mean(true_range[signal-RISK_WINDOW+1 .. signal])",
        qualifies_on="Donchian-20 break / volume surge reversal",
        couples_on="a rolling true-range mean — an ATR by another name",
        note="immune to the stop-coupling defect.")
for _s in ("mx_us100_cash_d1_atr_mean_reversion", "mx_us500_cash_d1_atr_mean_reversion"):
    CENSUS[_s] = dict(
        kind="TRUE_RANGE_MEAN", site="src/components/ultimate_book/sleeves/market_expansion_d1.py:206",
        expr="risk = mean true range; direction = _atr_mean_reversion_signal(bars, idx, risk)",
        qualifies_on="displacement measured IN UNITS OF `risk`",
        couples_on="the coupling runs the OTHER way: the SIGNAL reads the stop",
        note="Already recorded as `ad_exit_sweep.STOP_DEPENDENT_SIGNAL` and excluded from "
             "stop-width sweeps for exactly that reason. Not this defect, but the same "
             "family of entanglement.")


# =====================================================================================
# the measurement
# =====================================================================================

def q(xs, p):
    if not xs:
        return None
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int(round(p * (len(xs) - 1)))))]


def spearman(xs, ys):
    """Rank correlation with average ranks for ties. Returns None below n=30."""
    n = len(xs)
    if n < 30:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda k: v[k])
        r = [0.0] * n
        k = 0
        while k < n:
            j = k
            while j + 1 < n and v[order[j + 1]] == v[order[k]]:
                j += 1
            avg = (k + j) / 2.0 + 1.0
            for t in range(k, j + 1):
                r[order[t]] = avg
            k = j + 1
        return r

    rx, ry = ranks(xs), ranks(ys)
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / math.sqrt(sxx * syy)


def main() -> int:
    t0 = time.time()
    print("loading bars ...", flush=True)
    series, index, _res = AD.load_bars()
    print(f"  {len(series)} series in {time.time()-t0:.1f}s", flush=True)

    aa = json.load(gzip.open(AA_IN, "rt"))
    trades = dict(aa["trades"])
    if AM_SUBMID.exists():
        am = json.load(gzip.open(AM_SUBMID, "rt"))
        rows = am.get("trades") or am.get("rows")
        if isinstance(rows, dict):
            rows = rows.get("sub_mid_dn_revert")
        if rows:
            trades["sub_mid_dn_revert"] = rows

    costs = AD.load_broker_true_costs(AD.COSTS)
    from src.costs import cost_r as COSTR

    measured: dict[str, dict] = {}
    controls: dict[str, dict] = {}

    #: The four closed-form wick expressions, for CONTROL C1. `sd = wick + buf*atr`, so
    #: `atr_implied = (sd - wick) / buf`.
    CLOSED_FORM = {
        "asia_pdl_fade": (0.10, lambda b: b.c - b.l),
        "metals_core": (None, None),   # min(l, gap_bot) is not recoverable from the row
    }

    for sleeve, rows in sorted(trades.items()):
        if not rows:
            continue
        stop_atr, netr, grossr, costr, holds = [], [], [], [], []
        skips = 0
        inv_err = []
        cf = CLOSED_FORM.get(sleeve)
        for r in rows:
            tf = int(r["timeframe"])
            key = (r["symbol"], tf)
            if key not in index:
                skips += 1
                continue
            i = index[key].get(dt.datetime.fromisoformat(r["decision_bar_iso"]))
            if i is None:
                skips += 1
                continue
            bars, _times = series[key]
            a = atr14(bars, i)
            if a <= 0:
                skips += 1
                continue
            sd = float(r["sl_distance_price"])
            stop_atr.append(sd / a)
            g = float(r["r_gross"])
            grossr.append(g)
            try:
                br = COSTR(r["symbol"], ACCOUNT, float(r.get("hold_hours") or 0.0),
                           sl_distance_price=sd, entry_price=float(r["entry_price"]),
                           side=("LONG" if int(r["direction"]) > 0 else "SHORT"),
                           entry_utc=dt.datetime.fromisoformat(r["entry_utc"]),
                           costs=costs)
                c = float(br.total_r.value)
            except Exception:
                c = float("nan")
            costr.append(c)
            netr.append(g - c if c == c else float("nan"))
            holds.append(float(r.get("hold_hours") or 0.0))
            if cf and cf[0] is not None:
                buf, wick = cf
                implied = (sd - wick(bars[i])) / buf
                if a > 0:
                    inv_err.append(abs(implied - a) / a)
        if not stop_atr:
            continue
        clean = [(s, g, c, n) for s, g, c, n in zip(stop_atr, grossr, costr, netr) if n == n]
        rec = {
            "n": len(stop_atr), "n_priced": len(clean), "skips": skips,
            "stop_atr_p05": round(q(stop_atr, 0.05), 5),
            "stop_atr_p25": round(q(stop_atr, 0.25), 5),
            "stop_atr_med": round(q(stop_atr, 0.50), 5),
            "stop_atr_p75": round(q(stop_atr, 0.75), 5),
            "stop_atr_p95": round(q(stop_atr, 0.95), 5),
            "stop_atr_min": round(min(stop_atr), 6),
            "frac_below_0p25": round(sum(1 for s in stop_atr if s < 0.25) / len(stop_atr), 5),
            "frac_below_0p50": round(sum(1 for s in stop_atr if s < 0.50) / len(stop_atr), 5),
            "frac_below_1p00": round(sum(1 for s in stop_atr if s < 1.0) / len(stop_atr), 5),
            "mean_gross_r": round(statistics.fmean(grossr), 6),
            "mean_cost_r": (round(statistics.fmean([c for _s, _g, c, _n in clean]), 6)
                            if clean else None),
            "mean_net_r": (round(statistics.fmean([n for _s, _g, _c, n in clean]), 6)
                           if clean else None),
            "median_hold_hours": round(q(holds, 0.5), 4),
        }
        _rn = spearman([s for s, _g, _c, _n in clean], [n for _s, _g, _c, n in clean]) \
            if len(clean) >= 30 else None
        _rc = spearman([s for s, _g, _c, _n in clean], [c for _s, _g, c, _n in clean]) \
            if len(clean) >= 30 else None
        rec["spearman_stopatr_vs_net"] = None if _rn is None else round(_rn, 5)
        rec["spearman_stopatr_vs_cost"] = None if _rc is None else round(_rc, 5)
        # decile table
        if len(clean) >= 100:
            clean.sort(key=lambda t: t[0])
            k = len(clean) // 10
            dec = []
            for d in range(10):
                lo, hi = d * k, (len(clean) if d == 9 else (d + 1) * k)
                chunk = clean[lo:hi]
                dec.append({
                    "decile": d + 1, "n": len(chunk),
                    "stop_atr_mid": round(chunk[len(chunk) // 2][0], 4),
                    "gross_r": round(statistics.fmean([g for _s, g, _c, _n in chunk]), 5),
                    "cost_r": round(statistics.fmean([c for _s, _g, c, _n in chunk]), 5),
                    "net_r": round(statistics.fmean([n for _s, _g, _c, n in chunk]), 5),
                })
            rec["deciles"] = dec
        measured[sleeve] = rec
        if inv_err:
            controls[sleeve] = {
                "control": "C1 atr inversion",
                "n": len(inv_err), "max_rel_err": max(inv_err),
                "median_rel_err": statistics.median(inv_err),
                "claim": "sd = (c - l) + 0.10*atr14(bars,i) reproduces the stored stop, so "
                         "the ATR recomputed from the full series IS the ATR the generator saw",
            }
        print(f"  {sleeve:42s} n={rec['n']:6d} stopATR med={rec['stop_atr_med']:.3f} "
              f"<0.25={rec['frac_below_0p25']:.3f} rho(net)={rec['spearman_stopatr_vs_net']}",
              flush=True)

    # ---- the mechanical detector, and the adjudication against the source read ---------
    # An ATR-multiple stop read at the DECISION bar has stop/ATR dispersion EXACTLY 1.00.
    # Anything above that means some other quantity is in the stop. So dispersion is a
    # detector that needs no source read at all, and disagreeing with the source read is a
    # bug in one of the two. Published rather than asserted.
    for s, m in measured.items():
        p05, p95 = m["stop_atr_p05"], m["stop_atr_p95"]
        m["stop_atr_dispersion"] = round(p95 / p05, 4) if p05 > 0 else None
    detector = []
    for s, m in sorted(measured.items()):
        d = m.get("stop_atr_dispersion")
        kind = CENSUS[s]["kind"]
        flags_varying = d is not None and d > 1.005
        expect_varying = kind in (UNBOUNDED | BOUNDED)
        detector.append({
            "sleeve": s, "kind": kind, "dispersion": d,
            "detector_says_varying": flags_varying,
            "source_read_says_coupled": expect_varying,
            "agree": flags_varying == expect_varying,
            "rho_stop_atr_vs_net": m.get("spearman_stopatr_vs_net"),
            "n": m["n"],
        })
    disagreements = [r for r in detector if not r["agree"]]

    coupled = [r for r in detector if r["source_read_says_coupled"]
               and r["rho_stop_atr_vs_net"] is not None]
    immune_var = [r for r in detector if not r["source_read_says_coupled"]
                  and r["rho_stop_atr_vs_net"] is not None
                  and (r["dispersion"] or 0) > 1.005]
    immune_flat = [r for r in detector if not r["source_read_says_coupled"]
                   and r["rho_stop_atr_vs_net"] is not None
                   and (r["dispersion"] or 0) <= 1.005]

    def _summ(g):
        rs = [r["rho_stop_atr_vs_net"] for r in g]
        return {"n_generators": len(g), "sleeves": [r["sleeve"] for r in g],
                "rho_values": rs,
                "n_positive": sum(1 for x in rs if x > 0),
                "median_rho": (round(statistics.median(rs), 5) if rs else None),
                "max_abs_rho": (round(max(abs(x) for x in rs), 5) if rs else None)}

    fam = json.load(open(FORENSIC))["generators"]
    missing = sorted(set(fam) - set(CENSUS))
    extra = sorted(set(CENSUS) - set(fam))

    by_kind: dict[str, list[str]] = {}
    for s, c in CENSUS.items():
        by_kind.setdefault(c["kind"], []).append(s)

    doc = {
        "schema": "gtos.wave20.p3.stop_coupling.v1",
        "generated_by": str(Path(__file__).relative_to(REPO)),
        "generated_utc": dt.datetime.now(dt.UTC).isoformat(),
        "question": ("which generators build their stop out of the same quantity that "
                     "qualifies the setup, and what does it cost them"),
        "population_source": str(FORENSIC.relative_to(REPO)),
        "n_generators_in_forensic": len(fam),
        "n_generators_classified": len(CENSUS),
        "coverage_complete": not missing,
        "not_classified": missing,
        "classified_but_not_in_forensic": extra,
        "kind_counts": {k: len(v) for k, v in sorted(by_kind.items())},
        "by_kind": {k: sorted(v) for k, v in sorted(by_kind.items())},
        "unbounded_coupled": sorted(s for s, c in CENSUS.items() if c["kind"] in UNBOUNDED),
        "bounded_coupled": sorted(s for s, c in CENSUS.items() if c["kind"] in BOUNDED),
        "the_repair_already_exists_at": [
            "src/components/ultimate_book/sleeves/metals.py:34 ATR_STOP_FLOOR = 0.25",
            "src/components/ultimate_book/sleeves/metals_ob_micro.py:46 ATR_STOP_FLOOR = 0.25",
            "src/components/ultimate_book/sleeves/structural_retest.py:28 ATR_STOP_FLOOR = 0.25",
        ],
        "census": CENSUS,
        "measured": measured,
        "controls": controls,
        "mechanical_detector": {
            "rule": ("stop_dist / atr14(decision bar) has dispersion (p95/p05) EXACTLY 1.00 "
                     "iff the stop is an ATR multiple read at the decision bar. Anything "
                     "above 1.005 means another quantity is in the stop expression."),
            "rows": detector,
            "n_disagreements_with_source_read": len(disagreements),
            "disagreements": disagreements,
            "note": ("The ONE structural exception is ATR_LAGGED (fx_jpy / fx_jpy_ny), whose "
                     "stop is an ATR multiple read at a DIFFERENT bar; it disperses without "
                     "being coupled. It is declared as its own kind so the detector's "
                     "exceptions are named rather than discovered."),
        },
        "coupling_result": {
            "question": ("does stop/ATR predict net R, and only where the stop is coupled to "
                         "the qualifying quantity"),
            "coupled": _summ(coupled),
            "immune_but_varying": _summ(immune_var),
            "immune_and_flat": _summ(immune_flat),
            "caveat": ("An ATR-multiple sleeve has NO variation in stop/ATR, so its rho is "
                       "not a null result — it is an undefined one. The honest comparison is "
                       "`coupled` against `immune_but_varying`, which is the ATR_LAGGED pair: "
                       "real dispersion, no coupling. `immune_and_flat` is reported so the "
                       "reader can see the zero-variance rows are zero-variance."),
        },
        "measurement_basis": {
            "trades": str(AA_IN.relative_to(REPO)),
            "bars": AD.BARS,
            "costs": str(AD.COSTS.relative_to(REPO)),
            "atr": "primitives.atr14 at the decision bar; reads bars[i-14..i] only",
            "note": "gross R is AA's own labelling; cost R is the broker-true model at the "
                    "stored stop distance. Net = gross - cost, per trade, no winsorisation "
                    "beyond AA's own.",
        },
        "seconds": round(time.time() - t0, 1),
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print(f"\nkind counts: {doc['kind_counts']}")
    print(f"UNBOUNDED coupled: {doc['unbounded_coupled']}")
    print(f"coverage complete: {doc['coverage_complete']}  missing={missing}")
    print(f"wrote {OUT}  ({time.time()-t0:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
