"""substrate_engine — byte-faithful vendored copy of the SUBSTRATE leak-free state machine.

Source of truth (READ-ONLY oracle, do NOT diverge):
  research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10/substrate.py

This vendors EXACTLY the per-bar StateVec features that `substrate.cell_coords` consumes
(vr, slope20/50/100, mtf_align, rng_pos, compression, ac60) plus the discretizers
(`_bucket_*`), `cell_coords`, and the outcome GEOMETRY (stop_dist / target_dist). It is the
single faithful home for the substrate math the live `sub_xvol_pullback` and `sub_mid_dn_revert`
generators stand on. A parity test (tests/ultimate_book/test_substrate_sleeves.py) asserts this
agrees per-bar with the ACTUAL route `substrate.build_states` + `substrate.cell_coords`.

LIVE WARMUP NUANCE (deliberate, documented):
  route `substrate.build_states` hard-guards n >= WARMUP+MAXBARS+5 (~295) and only assigns a state
  for i in range(WARMUP, n) because it BATCH-LABELS the +MAXBARS forward outcome window. The LIVE
  port has no forward window: it computes the state at the latest closed bar i = len(bars)-1 with
  NO +MAXBARS guard, so the documented WARMUP of 210 bars is the only gate (bar_provider.enough(
  bars, "substrate") == 210). Every feature here is leak-free (index <= i), so the state at bar i is
  IDENTICAL whether computed on bars[:i+1] (live) or on the full series (route) — the parity test
  proves it. The route's loop START at i=210 (vs the live i>=209 when len==210) is only a warmup
  buffer choice; the feature formulae are well-defined for i >= 199 and unchanged across that bound.

Constants/thresholds/lookbacks are copied verbatim. `atr14` is reused from ..primitives (a
byte-identical vendored copy of geometry_lib.atr14). Do NOT "improve" anything in this module — any
change silently breaks parity with the locked substrate map and trades real money on a wrong cell.
"""
from __future__ import annotations
from typing import Optional

from ..primitives import atr14   # byte-identical to route geometry_lib.atr14 (primitives.py:23-30)

# Warmup floor for the live state (bar_provider.WARMUP["substrate"] == 210; substrate.py:61 WARMUP).
WARMUP = 210


# --------------------------------------------------------------------------------------------- #
# persistence: lag-1 autocorrelation of a return series   (substrate.py:85-92  `_ac`)
# Vendored EXACTLY (NOT src primitives.autocorr): the route's persistence bucket is computed by this
# `_ac` (no None-guard, `if n < 3: return 0.0`, mean = sum/n). Fidelity over reuse.
# --------------------------------------------------------------------------------------------- #
def _ac(rets) -> float:
    """lag-1 autocorrelation of a return series (persistence). substrate.py:85-92."""
    n = len(rets)
    if n < 3:
        return 0.0
    m = sum(rets) / n
    num = sum((rets[k] - m) * (rets[k - 1] - m) for k in range(1, n))
    den = sum((x - m) ** 2 for x in rets)
    return num / den if den > 0 else 0.0


# --------------------------------------------------------------------------------------------- #
# Discretizers — the confluence vocabulary   (substrate.py:168-197)
# --------------------------------------------------------------------------------------------- #
def _bucket_vr(vr):
    """substrate.py:168-172."""
    if vr < 0.85:
        return "lo"
    if vr < 1.15:
        return "mid"
    if vr < 1.6:
        return "hi"
    return "xhi"


def _bucket_slope(s):
    """substrate.py:174-177."""
    if s > 1.5:
        return "up"
    if s < -1.5:
        return "dn"
    return "flat"


def _bucket_rng(p):
    """substrate.py:179-182."""
    if p < 0.25:
        return "low"
    if p > 0.75:
        return "high"
    return "mid"


def _bucket_comp(c):
    """substrate.py:184-187."""
    if c < 0.7:
        return "coil"
    if c > 1.3:
        return "expand"
    return "norm"


def _bucket_persist(a):
    """substrate.py:189-192."""
    if a >= 0.10:
        return "trend"
    if a <= -0.10:
        return "revert"
    return "rand"


def _bucket_session(h):
    """substrate.py:194-197. h is the bar's UTC hour."""
    if h < 8:
        return "asia"
    if h < 16:
        return "london"
    return "ny"


# Multi-TF alignment label map (substrate.py:204).
_MTF_LABEL = {1: "aligned", -1: "conflict", 0: "neutral"}


# --------------------------------------------------------------------------------------------- #
# Per-bar leak-free StateVec (the subset cell_coords consumes)   (substrate.py:116-158)
# --------------------------------------------------------------------------------------------- #
def compute_state(bars, i: int, hour: Optional[int]) -> Optional[dict]:
    """Return the leak-free StateVec dict at bar i (features index<=i ONLY), or None if ATR<=0.

    Mirrors substrate.build_states' inner loop body (substrate.py:117-156) for exactly the fields
    cell_coords reads: vr, slope50 (trend), mtf_align, rng_pos, compression, ac60, hour. slope20 and
    slope100 are computed because mtf_align needs them. `hour` is threaded in from the bar timestamp
    (the route reads T[i].hour; substrate.py:156) — pass None when the session bucket is not needed.

    Caller MUST guarantee i >= 199 (so every lookback below is in-range); the live generators gate on
    len(bars) >= WARMUP (210) => i = len-1 >= 209. Returns None when atr14(bars,i) <= 0 (skip, like
    substrate.py:118-119).
    """
    a = atr14(bars, i)                                    # substrate.py:117  a = A[i]
    if a <= 0:                                            # substrate.py:118-119
        return None
    # vr = a / sma100  (substrate.py:120-121); sma100 over the 100-bar ATR window i-99..i.
    sma100 = sum(atr14(bars, k) for k in range(i - 99, i + 1)) / 100
    vr = a / sma100 if sma100 > 0 else 1.0
    # trend slopes normalised by ATR (substrate.py:125-127)
    c_i = bars[i].c
    slope20 = (c_i - bars[i - 20].c) / a
    slope50 = (c_i - bars[i - 50].c) / a
    slope100 = (c_i - bars[i - 100].c) / a
    # multi-TF alignment (substrate.py:131-135)
    def _sgn(v, thr=0.5):
        return 1 if v > thr else (-1 if v < -thr else 0)
    s_short = _sgn(slope20)
    s_long = _sgn(slope100)
    mtf_align = 1 if (s_short != 0 and s_short == s_long) else (
        -1 if (s_short != 0 and s_long != 0 and s_short == -s_long) else 0)
    # range position in last 50 bars (substrate.py:137-138)
    lo50 = min(bars[k].l for k in range(i - 49, i + 1))
    hi50 = max(bars[k].h for k in range(i - 49, i + 1))
    rng_pos = (c_i - lo50) / (hi50 - lo50) if hi50 > lo50 else 0.5
    # compression: recent 5-bar TR vs 20-bar TR (substrate.py:140; tr per substrate.py:109-110)
    def _tr(k):
        return max(bars[k].h - bars[k].l,
                   abs(bars[k].h - bars[k - 1].c),
                   abs(bars[k].l - bars[k - 1].c))
    num5 = sum(_tr(k) for k in range(i - 4, i + 1)) / 5
    den20 = sum(_tr(k) for k in range(i - 19, i + 1)) / 20 or 1   # `or 1` guard verbatim
    comp = num5 / den20
    # persistence: lag-1 autocorr of the 60-bar return series (substrate.py:142;
    # rets[k]=C[k]-C[k-1] per substrate.py:112-113; slice rets[i-59:i+1] == 60 returns i-59..i)
    rets_slice = [bars[k].c - bars[k - 1].c for k in range(i - 59, i + 1)]
    ac60 = _ac(rets_slice)
    return {
        "vr": vr,
        "slope20": slope20, "slope50": slope50, "slope100": slope100,
        "mtf_align": mtf_align,
        "rng_pos": rng_pos, "compression": comp, "ac60": ac60,
        "hour": hour,
    }


def cell_coords(st: dict) -> dict:
    """Map a raw StateVec to discrete confluence coordinates. substrate.py:199-209.

    `session` is only valid when st['hour'] is not None (the route always has T[i].hour). The live
    sub_mid_dn_revert generator supplies hour from the bar timestamp; sub_xvol_pullback never reads
    `session` (depth-4 cell) so it may pass hour=None.
    """
    coords = {
        "vol":     _bucket_vr(st["vr"]),
        "trend":   _bucket_slope(st["slope50"]),
        "mtf":     _MTF_LABEL[st["mtf_align"]],
        "rngpos":  _bucket_rng(st["rng_pos"]),
        "comp":    _bucket_comp(st["compression"]),
        "persist": _bucket_persist(st["ac60"]),
    }
    if st.get("hour") is not None:
        coords["session"] = _bucket_session(st["hour"])
    return coords


# --------------------------------------------------------------------------------------------- #
# Outcome GEOMETRY (live needs the stop/target distances, not the simulate label).
#   substrate.outcome (substrate.py:248-255):  sd = stop_atr * atr ; td = target_R * sd
# --------------------------------------------------------------------------------------------- #
def stop_target(atr: float, stop_atr: float, target_R: float) -> tuple[float, float]:
    """(stop_dist, target_dist) for a (stop_atr, target_R) geometry at this bar's ATR.
    substrate.py:253-254:  sd = stop_atr * atr ; td = target_R * sd."""
    sd = stop_atr * atr
    td = target_R * sd
    return sd, td


def cell_matches(coords: dict, conds: dict) -> bool:
    """True iff every cell condition holds. Mirrors SUBSTRATE_corrcheck.materialize_cell:74
    `all(co.get(d) == b for d, b in conds.items())`."""
    return all(coords.get(d) == b for d, b in conds.items())
