"""p1 — the persistence test.  Canonical loader over the 8 open windows."""
from __future__ import annotations
import numpy as np, json, os

ROWS = "/tmp/d1/rows3"
WINDOWS = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
DISC = ("/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801/"
        "docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery")
OUT = DISC

FAMS = ["cross_asset_lead_lag", "current_breaker_re_entry", "current_fvg_fill",
        "current_ob_retest", "displacement_continuation", "liquidity_sweep_reclaim",
        "regime_transition_break", "session_open_range_break",
        "structural_distance_extreme", "volatility_compression_expansion",
        "range_extreme_reversion", "__other__"]
ATM_FAMS = {"cross_asset_lead_lag", "displacement_continuation", "liquidity_sweep_reclaim",
            "regime_transition_break", "session_open_range_break",
            "structural_distance_extreme", "volatility_compression_expansion",
            "range_extreme_reversion"}
POI_FAMS = {"current_breaker_re_entry", "current_fvg_fill", "current_ob_retest"}
SYMS = None  # filled per window from legend


class W:
    """One window, decoded to global symbol/family indices."""
    __slots__ = ("w", "n", "day", "hour", "bhour", "sym", "fam", "side", "d_bps",
                 "g", "c", "fil", "past", "atm", "vol", "trend", "gm", "cm",
                 "reason", "days", "syms", "wi", "g15", "mg", "mfil", "entry", "touch", "gc", "cc", "ok")

    def __init__(self, w, wi, symmap):
        z = np.load(f"{ROWS}/D1_{w}.npz")
        lg = json.load(open(f"{ROWS}/D1_{w}.legend.json"))
        self.w = w; self.wi = wi
        self.days = lg["days"]; self.syms = lg["syms"]
        loc = np.array([symmap[s] for s in lg["syms"]], dtype=np.int16)
        self.sym = loc[z["sym"]]
        self.fam = z["fam"].astype(np.int16)
        self.day = z["day"].astype(np.int16)
        self.hour = z["hour"].astype(np.int16)
        self.bhour = z["bhour"].astype(np.int16)
        self.side = z["side"].astype(np.int8)
        self.d_bps = z["d_bps"].astype(np.float64)
        self.entry = z["entry"]
        self.g = z["rr20"].astype(np.float64)      # real arm gross, target 2.0R
        self.g15 = z["rr15"].astype(np.float64)
        self.c = z["rcost"].astype(np.float64)     # broker-true toll, R units
        self.fil = z["rfil"].astype(np.int8)
        self.past = z["rpast"].astype(np.int8)
        self.reason = z["rrs20"].astype(np.int8)
        self.atm = z["atm"].astype(np.int8)
        self.vol = z["vol"].astype(np.int8)
        self.trend = z["trend"].astype(np.int8)
        self.gm = z["fg20"].astype(np.float64)     # mirror (placebo-side) arm gross
        self.cm = z["fcost"].astype(np.float64)
        self.mg = z["mr20"].astype(np.float64)     # market-fill arm (at-market only)
        self.mfil = z["mfil"].astype(np.int8)
        self.touch = z["rtouch"].astype(np.int16)
        # CORRECTED CONTRACT (d1b §2): the seven at-market families emit entry == the
        # last print, so their honest order type is a MARKET order, not a resting limit.
        # gc/cc = gross/cost on the corrected contract; ok = row usable under it.
        atm = self.atm == 1
        self.gc = np.where(atm, self.mg, self.g)
        self.cc = self.c.copy()
        self.ok = np.where(atm, self.mfil == 1, self.fil == 1)
        self.n = len(self.g)


def load_all():
    symset = []
    for w in WINDOWS:
        lg = json.load(open(f"{ROWS}/D1_{w}.legend.json"))
        for s in lg["syms"]:
            if s not in symset:
                symset.append(s)
    symset = sorted(symset)
    symmap = {s: i for i, s in enumerate(symset)}
    ws = [W(w, i, symmap) for i, w in enumerate(WINDOWS)]
    return ws, symset


def spearman(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a = a[m]; b = b[m]
    if len(a) < 3: return float("nan")
    ra = _rank(a); rb = _rank(b)
    return float(np.corrcoef(ra, rb)[0, 1])


def _rank(x):
    o = np.argsort(x, kind="mergesort")
    r = np.empty(len(x), float); r[o] = np.arange(len(x), dtype=float)
    # average ties
    xs = x[o]
    i = 0
    while i < len(xs):
        j = i
        while j + 1 < len(xs) and xs[j + 1] == xs[i]:
            j += 1
        if j > i:
            r[o[i:j + 1]] = (i + j) / 2.0
        i = j + 1
    return r


def pearson(a, b):
    a = np.asarray(a, float); b = np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    a = a[m]; b = b[m]
    if len(a) < 3: return float("nan")
    if a.std() == 0 or b.std() == 0: return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def day_block_boot(vals, daykeys, draws=4000, seed=17):
    """day-block bootstrap of the mean.  vals aligned to daykeys (int)."""
    vals = np.asarray(vals, float)
    daykeys = np.asarray(daykeys)
    ud, inv = np.unique(daykeys, return_inverse=True)
    nd = len(ud)
    sums = np.bincount(inv, weights=vals, minlength=nd)
    cnts = np.bincount(inv, minlength=nd).astype(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, nd, size=(draws, nd))
    s = sums[idx].sum(1); c = cnts[idx].sum(1)
    m = np.where(c > 0, s / np.maximum(c, 1), np.nan)
    obs = float(vals.mean()) if len(vals) else float("nan")
    lo, hi = np.nanpercentile(m, [2.5, 97.5])
    return dict(mean=obs, lo=float(lo), hi=float(hi),
                p_le0=float(np.mean(m <= 0)), n=int(len(vals)), ndays=int(nd))
