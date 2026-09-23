"""h6_lib — ONE joint scorer for the repaired contract, vectorised over all 43,755
live-expressible (at-market) candidates x 3 months.

Everything the swarm's repaired contract is made of, as parameters of a single object:

    k           entry re-timing / cancel window: enter at the CLOSE of path bar k
                (k=0 = the shipped decision-instant entry). R frame rebased by cls[k-1].
    entry_lo/hi CANCEL: only enter if the market's drift at that instant, c0 (in R,
                signed for the trade's side), lies in [lo, hi]. c0<0 = the market has
                moved AGAINST the signal, i.e. we get a better price.
    target      take-profit in R (None = none)
    stop        initial stop in R (None = none; -1.0 = the declared risk unit)
    trail       trail the stop this far behind the running MFE (None = off)
    maxbars     time stop, absolute 1-based path-bar index (None = ride to path end)
    cost gate   real_spread_r <= gs AND cost_true <= gt  (shipped gate: 0.10 / 0.15)
    fill floor  execution_fill_probability >= f

The walk is byte-equivalent to e_lib.walk (lane e-stack), including the conservative
tie rule (stop wins inside a bar) and the l11 trail-honesty rule (a stop armed at bar i
is only CHECKED from bar i+1).
"""
from __future__ import annotations

import gzip, json, os

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
NPZ = f"{D}/h6_ATMKT_PATHS.npz"
META = f"{D}/h6_ATMKT_META.jsonl.gz"
GATE_SPREAD, GATE_TOTAL = 0.10, 0.15          # the shipped cost gate (e_score.py:34)
NEG = -1e18

_cache = {}


def load():
    """(paths, meta) — paths = dict of numpy arrays, meta = dict of numpy arrays."""
    if "d" in _cache:
        return _cache["d"]
    z = np.load(NPZ)
    F = z["F"].astype(np.float64)
    A = z["A"].astype(np.float64)
    C = z["C"].astype(np.float64)
    NB = z["NB"].astype(np.int32)
    rows = [json.loads(x) for x in gzip.open(META, "rt") if x.strip()]
    m = {
        "symbol": np.array([r["symbol"] for r in rows]),
        "day": np.array([r["day"] for r in rows]),
        "month": np.array([r["month"] for r in rows]),
        "hour": np.array([r["hour"] for r in rows], dtype=np.int32),
        "family": np.array([r["family"] or "" for r in rows]),
        "session": np.array([r["session"] or "" for r in rows]),
        "side": np.array([r["side"] for r in rows]),
        "rd": np.array([r["risk_distance"] for r in rows], dtype=np.float64),
        "entry": np.array([r["entry_price"] for r in rows], dtype=np.float64),
        "rdp": np.array([r["rdp"] for r in rows], dtype=np.float64),
        "cost_true": np.array([r["cost_true"] if r["cost_true"] is not None else np.nan
                               for r in rows], dtype=np.float64),
        "spread_r": np.array([r["real_spread_r"] if r["real_spread_r"] is not None else np.nan
                              for r in rows], dtype=np.float64),
        "comm_r": np.array([r["real_comm_r"] if r["real_comm_r"] is not None else np.nan
                            for r in rows], dtype=np.float64),
        "slip_r": np.array([r["real_slip_r"] if r["real_slip_r"] is not None else np.nan
                            for r in rows], dtype=np.float64),
        "cost_frozen": np.array([r["cost_frozen"] if r["cost_frozen"] is not None else np.nan
                                 for r in rows], dtype=np.float64),
        "efp": np.array([r["efp"] if r["efp"] is not None else np.nan for r in rows],
                        dtype=np.float64),
        "prob": np.array([r["prob"] if r["prob"] is not None else np.nan for r in rows],
                         dtype=np.float64),
        "K5_TRAIL025": np.array([r["K5_TRAIL025"] if r["K5_TRAIL025"] is not None else np.nan
                                 for r in rows], dtype=np.float64),
        "K0_INC": np.array([r["K0_INC"] if r["K0_INC"] is not None else np.nan
                            for r in rows], dtype=np.float64),
        "K0_TRAIL025": np.array([r["K0_TRAIL025"] if r["K0_TRAIL025"] is not None else np.nan
                                 for r in rows], dtype=np.float64),
        "K5_INC": np.array([r["K5_INC"] if r["K5_INC"] is not None else np.nan
                            for r in rows], dtype=np.float64),
    }
    # bps conversion factor: R * rd / entry * 1e4
    m["bpsfac"] = m["rd"] / m["entry"] * 1e4
    _cache["d"] = ({"F": F, "A": A, "C": C, "NB": NB}, m)
    return _cache["d"]


# ------------------------------------------------------------------ the walk
def walk_all(P, k=0, target=2.0, stop=-1.0, trail=None, maxbars=None,
             build_rule=True):
    """Vectorised honest walk. Returns (r, reason, exit_bar, tradeable, c0).

    reason: 0 no_fill/untradeable, 1 stop, 2 target, 3 time_stop, 4 path_end
    tradeable: bool mask. `build_rule` reproduces e_build_atmkt.py's own exclusion
    (k >= n_bars - 2 -> the cell is None), which is what the shipped K{k}_* columns use.
    """
    F, A, C, NB = P["F"], P["A"], P["C"], P["NB"]
    n = F.shape[0]
    c0 = np.zeros(n) if k == 0 else np.nan_to_num(C[:, k - 1], nan=0.0)
    have_c0 = np.ones(n, dtype=bool) if k == 0 else (NB >= k)
    last = NB.copy() if maxbars is None else np.minimum(NB, maxbars)
    tradeable = have_c0 & (last > k)
    if build_rule:
        tradeable &= (k < NB - 2)

    r = np.zeros(n)
    reason = np.zeros(n, dtype=np.int8)
    exit_bar = np.zeros(n, dtype=np.int32)
    active = tradeable.copy()
    stop_lv = np.full(n, stop if stop is not None else NEG)
    peak = np.full(n, NEG)
    hi = int(last.max())
    for i in range(k, hi):
        val = active & (i < last)
        if not val.any():
            break
        f = F[:, i] - c0
        a = A[:, i] - c0
        hs = val & (a <= stop_lv + 1e-12)
        if hs.any():
            r[hs] = stop_lv[hs]; reason[hs] = 1; exit_bar[hs] = i + 1
            active &= ~hs
            val = active & (i < last)
        if target is not None:
            ht = val & (f >= target - 1e-12)
            if ht.any():
                r[ht] = target; reason[ht] = 2; exit_bar[ht] = i + 1
                active &= ~ht
                val = active & (i < last)
        np.maximum(peak, f, out=peak, where=val)
        if trail is not None:
            up = val & (peak >= trail)
            if up.any():
                np.maximum(stop_lv, peak - trail, out=stop_lv, where=up)
    surv = active & tradeable
    if surv.any():
        idx = np.clip(last - 1, 0, F.shape[1] - 1)
        r[surv] = C[surv, idx[surv]] - c0[surv]
        exit_bar[surv] = last[surv]
        if maxbars is not None:
            trunc = surv & (NB > last)
            reason[surv] = 4
            reason[trunc] = 3
        else:
            reason[surv] = 4
    r[~tradeable] = 0.0
    return r, reason, exit_bar, tradeable, c0


# ------------------------------------------------------------------- masks
def population(M, tradeable, c0, entry_lo=None, entry_hi=None,
               gate_spread=None, gate_total=None, fill_floor=None,
               symbols=None, months=None, gate_bps=None, rdp_lo=None, rdp_hi=None,
               floor_nan_passes=False):
    sel = tradeable & np.isfinite(M["cost_true"])
    if entry_lo is not None:
        sel &= (c0 >= entry_lo - 1e-12)
    if entry_hi is not None:
        sel &= (c0 <= entry_hi + 1e-12)
    if gate_spread is not None:
        sel &= (M["spread_r"] <= gate_spread + 1e-12)
    if gate_total is not None:
        sel &= (M["cost_true"] <= gate_total + 1e-12)
    if gate_bps is not None:
        sel &= (M["cost_true"] * M["bpsfac"] <= gate_bps + 1e-12)
    if rdp_lo is not None:
        sel &= (M["rdp"] >= rdp_lo)
    if rdp_hi is not None:
        sel &= (M["rdp"] <= rdp_hi)
    if fill_floor is not None:
        ok = M["efp"] >= fill_floor - 1e-12
        if floor_nan_passes:
            ok |= ~np.isfinite(M["efp"])
        sel &= ok
    if symbols is not None:
        sel &= np.isin(M["symbol"], list(symbols))
    if months is not None:
        sel &= np.isin(M["month"], list(months))
    return sel


# -------------------------------------------------------------------- stats
def score(r, M, sel, reason=None):
    """Full economics of one (contract, population) cell."""
    n = int(sel.sum())
    if n == 0:
        return {"n": 0}
    g = r[sel]
    c = M["cost_true"][sel]
    net = g - c
    bf = M["bpsfac"][sel]
    gm, cm, nm = g.mean(), c.mean(), net.mean()
    gse = g.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    nse = net.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    eb = float((g * bf).mean()); cb = float((c * bf).mean())
    out = {"n": n, "gross": float(gm), "cost": float(cm), "net": float(nm),
           "t_gross": float(gm / gse) if gse else None,
           "t_net": float(nm / nse) if nse else None,
           "se_gross": float(gse), "se_net": float(nse),
           "edge_bps": eb, "cost_bps": cb,
           "ratio_bps": (eb / cb) if cb else None,
           "ratio_r": float(gm / cm) if cm else None,
           "win": float((g > 0).mean()), "total_net_R": float(net.sum())}
    if reason is not None:
        rs = reason[sel]
        out["share_stop"] = float((rs == 1).mean())
        out["share_target"] = float((rs == 2).mean())
        out["share_time_stop"] = float((rs == 3).mean())
        out["share_path_end"] = float((rs == 4).mean())
        out["share_maxbars_truncated"] = float(((rs == 3) | (rs == 4)).mean())
    return out


def by_day(r, M, sel):
    days = M["day"][sel]
    g = r[sel]; c = M["cost_true"][sel]
    out = {}
    for d in np.unique(days):
        m = days == d
        out[str(d)] = {"n": int(m.sum()), "gross": float(g[m].mean()),
                       "net": float((g[m] - c[m]).mean()),
                       "sum_net": float((g[m] - c[m]).sum()),
                       "sum_gross": float(g[m].sum())}
    return out


def by_group(r, M, sel, keyname):
    ks = M[keyname][sel]
    g = r[sel]; c = M["cost_true"][sel]; bf = M["bpsfac"][sel]
    out = {}
    for kk in np.unique(ks):
        m = ks == kk
        nn = int(m.sum())
        gg, cc = g[m], c[m]
        nt = gg - cc
        gse = gg.std(ddof=1) / np.sqrt(nn) if nn > 1 else np.nan
        nse = nt.std(ddof=1) / np.sqrt(nn) if nn > 1 else np.nan
        eb = float((gg * bf[m]).mean()); cb = float((cc * bf[m]).mean())
        out[str(kk)] = {"n": nn, "gross": float(gg.mean()), "cost": float(cc.mean()),
                        "net": float(nt.mean()),
                        "t_gross": float(gg.mean() / gse) if gse else None,
                        "t_net": float(nt.mean() / nse) if nse else None,
                        "edge_bps": eb, "cost_bps": cb,
                        "ratio_bps": (eb / cb) if cb else None,
                        "ratio_r": float(gg.mean() / cc.mean()) if cc.mean() else None,
                        "total_net_R": float(nt.sum())}
    return out


def bootstrap_days(r, M, sel, nboot=2000, seed=20260806, field="net"):
    """Day-block bootstrap on the per-trade mean (blocks = trading days)."""
    rng = np.random.default_rng(seed)
    days = M["day"][sel]
    v = (r[sel] - M["cost_true"][sel]) if field == "net" else r[sel]
    ud = np.unique(days)
    idx = {d: np.where(days == d)[0] for d in ud}
    sums = np.array([v[idx[d]].sum() for d in ud])
    cnts = np.array([len(idx[d]) for d in ud])
    nd = len(ud)
    out = np.empty(nboot)
    for b in range(nboot):
        p = rng.integers(0, nd, nd)
        out[b] = sums[p].sum() / cnts[p].sum()
    obs = v.mean()
    return {"observed": float(obs), "ci_lo": float(np.quantile(out, 0.025)),
            "ci_hi": float(np.quantile(out, 0.975)),
            "p_le_0": float((out <= 0).mean()), "n_days": nd, "nboot": nboot}
