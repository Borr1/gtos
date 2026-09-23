"""
leadlag.py  — Cross-instrument lead-lag / intermarket graph + tradeable-edge miner.
============================================================================
LAYER (Wave: ultimate mechanical edge). A NEW intelligence substrate, not one strategy.

Two reusable engines, both importable:

  1. GRAPH (build_graph): lagged cross-correlation of aligned H4 *log returns* across the
     ~48 instruments. For each ordered pair (A leads B) and lag in {1,2,3} bars, compute
     corr( r_A[t-lag] , r_B[t] ) on the ALIGNED timestamp panel. We split TRAIN(<=2024) vs
     FORWARD(2025-26) so we only believe a directed link that is *sign-stable across regimes*.
     Lead score = how much the best lagged corr exceeds lag-0 corr (genuine LEADERSHIP, not
     just contemporaneous comovement). Also a cheap transfer-entropy proxy (sign-MI) per pair.

  2. MINER (mine_pair / mine_all): when a LEADER makes a defined move over `look` closed bars
     (>= k*ATR, i.e. a z-style impulse), what are the LAGGARD forward odds over the next bars?
     Entry on the laggard at the SAME-timestamp close as the leader's signal bar (the laggard
     bar that closes simultaneously); trade resolves on laggard bars i+1.. only. Fill via the
     TESTED geometry_lib.simulate (pessimistic, stop wins ties). Real per-asset cost.
     Reports TRAIN vs FORWARD per-trade R + win + sample size n, per-year, and within-forward
     halves — a cell is only trusted if it holds FORWARD and has n>=~40.

NO LOOKAHEAD (the only thing that matters here):
  * Leader signal at close of bar i uses ONLY leader closes index <= i (rolling cum return,
    z-scored vs a trailing window that ends at i-1).
  * Entry = laggard.close at the bar whose timestamp == leader signal timestamp. That bar has
    also already CLOSED at decision time (both are H4 closes on the same UTC grid), so this is
    a same-close decision/entry; outcome uses laggard bars strictly after i. Honest, leak-free.
  * ATR for stop sizing uses atr14 on laggard bars up to i (closed).

CONFLUENCE (high odds come from stacking independent conditions):
  * dual-leader confirmation (two independent leaders agree),
  * laggard-regime gate (trend-aligned / vol state),
  * relation-sign prior (economic direction) so we never trade a spurious sign.

Run as a script -> builds graph + mines the catalog, prints the forward-stable winners, and
writes LEADLAG_GRAPH.json + LEADLAG_EDGES.json (the queryable map).
"""
from __future__ import annotations
import sys, os, json, math
from collections import defaultdict

ROOT = "/Users/borr/Documents/gtos/repo/ai-trading-agent"
EDGE = ROOT + "/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10"
sys.path.insert(0, ROOT); sys.path.insert(0, EDGE)

from geometry_lib import Bar, atr14, simulate  # TESTED fill primitives
import wave1_structure_setups_ict as w1        # deep 2014-2026 union loader, cost_for, SYMBOLS
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

cost_for = w1.cost_for
SYMBOLS = list(w1.SYMBOLS)

# ----------------------------------------------------------------------------
# Panel: load every symbol once (time-indexed). Cached on first import.
# ----------------------------------------------------------------------------
_PANEL = {}
def panel(sym):
    """sym -> dict(times=[datetime], bars=[Bar], tmap={time:idx}, lr=[log ret], atrs=[atr14])."""
    if sym in _PANEL:
        return _PANEL[sym]
    T, B = w1.load(sym)
    n = len(B)
    lr = [0.0] * n
    for i in range(1, n):
        c0, c1 = B[i-1].c, B[i].c
        lr[i] = math.log(c1 / c0) if (c0 > 0 and c1 > 0) else 0.0
    atrs = [atr14(B, i) for i in range(n)]
    d = {"times": T, "bars": B, "tmap": {t: i for i, t in enumerate(T)}, "lr": lr, "atrs": atrs}
    _PANEL[sym] = d
    return d

def coverage(sym):
    p = panel(sym)
    if not p["times"]:
        return (None, None, 0)
    return (p["times"][0].year, p["times"][-1].year, len(p["times"]))

# ----------------------------------------------------------------------------
# 1) GRAPH: lagged cross-correlation on the aligned timestamp panel.
# ----------------------------------------------------------------------------
def _aligned_returns(a, b, year_lo=None, year_hi=None):
    """Return two parallel lists (ra, rb) of log returns on the COMMON timestamp grid,
    optionally restricted to [year_lo, year_hi]. Index t is shared (same UTC bar)."""
    pa, pb = panel(a), panel(b)
    ta, tb = pa["tmap"], pb["tmap"]
    common = [t for t in pa["times"] if t in tb]
    if year_lo is not None:
        common = [t for t in common if t.year >= year_lo]
    if year_hi is not None:
        common = [t for t in common if t.year <= year_hi]
    ra = [pa["lr"][ta[t]] for t in common]
    rb = [pb["lr"][tb[t]] for t in common]
    return common, ra, rb

def _pearson(x, y):
    n = len(x)
    if n < 30: return 0.0
    mx = sum(x)/n; my = sum(y)/n
    sx = sum((v-mx)**2 for v in x); sy = sum((v-my)**2 for v in y)
    if sx <= 0 or sy <= 0: return 0.0
    cov = sum((x[i]-mx)*(y[i]-my) for i in range(n))
    return cov / math.sqrt(sx*sy)

def lagged_corr(a, b, lag, year_lo=None, year_hi=None):
    """corr( r_A[t-lag], r_B[t] ): does A's move LEAD B by `lag` bars?  lag>=0."""
    common, ra, rb = _aligned_returns(a, b, year_lo, year_hi)
    if len(ra) < 30 + lag:
        return 0.0, 0
    if lag == 0:
        return _pearson(ra, rb), len(ra)
    x = ra[:-lag]; y = rb[lag:]
    return _pearson(x, y), len(x)

def _sign_mi(a, b, lag, year_lo=None, year_hi=None):
    """Cheap transfer-entropy proxy: mutual information between sign(r_A[t-lag]) and
    sign(r_B[t]), in bits. Captures *directional* predictive content beyond linear corr."""
    common, ra, rb = _aligned_returns(a, b, year_lo, year_hi)
    if len(ra) < 60 + lag: return 0.0
    x = ra[:-lag] if lag else ra
    y = rb[lag:] if lag else rb
    sx = [1 if v > 0 else 0 for v in x]
    sy = [1 if v > 0 else 0 for v in y]
    n = len(sx)
    joint = defaultdict(int); px = defaultdict(int); py = defaultdict(int)
    for i in range(n):
        joint[(sx[i], sy[i])] += 1; px[sx[i]] += 1; py[sy[i]] += 1
    mi = 0.0
    for (i, j), c in joint.items():
        pij = c / n; pi = px[i] / n; pj = py[j] / n
        if pij > 0 and pi > 0 and pj > 0:
            mi += pij * math.log2(pij / (pi * pj))
    return mi

def build_graph(min_overlap=300, lags=(1, 2, 3), candidates=None):
    """Directed lead-lag graph over the universe.
    For each ordered pair (A,B) with enough aligned bars, find the lag (1..3) that maximizes
    |corr(r_A[t-lag], r_B[t])|, and report lead_gain = |best lagged corr| - |lag0 corr|.
    Split TRAIN(<=2024) / FORWARD(2025-26): a link is `stable` if best lag & sign agree across
    both AND lead_gain>0 in both (A genuinely leads, not just co-moves), in either regime where
    both have data. Returns list of edge dicts, sorted by forward |lagged corr|.
    Use `candidates` (list of (A,B)) to restrict (full 48x48 is 2k pairs; default does that)."""
    syms = [s for s in SYMBOLS if coverage(s)[2] > min_overlap]
    pairs = candidates if candidates is not None else [
        (a, b) for a in syms for b in syms if a != b]
    edges = []
    for a, b in pairs:
        # overall overlap gate
        common_all, _, _ = _aligned_returns(a, b)
        if len(common_all) < min_overlap:
            continue
        def best_for(ylo, yhi):
            l0, n0 = lagged_corr(a, b, 0, ylo, yhi)
            best = (0, 0.0, 0)  # lag, corr, n
            for L in lags:
                c, n = lagged_corr(a, b, L, ylo, yhi)
                if abs(c) > abs(best[1]):
                    best = (L, c, n)
            return l0, best
        l0_tr, best_tr = best_for(None, 2024)
        l0_fw, best_fw = best_for(2025, None)
        # which regime(s) have enough data
        n_tr = best_tr[2]; n_fw = best_fw[2]
        lead_gain_tr = abs(best_tr[1]) - abs(l0_tr)
        lead_gain_fw = abs(best_fw[1]) - abs(l0_fw)
        # stability: same best lag and same sign across regimes (only if both have data)
        both = n_tr >= min_overlap and n_fw >= 200
        stable = bool(both and best_tr[0] == best_fw[0]
                      and (best_tr[1] > 0) == (best_fw[1] > 0)
                      and lead_gain_tr > 0 and lead_gain_fw > 0)
        edges.append({
            "leader": a, "follower": b,
            "lag0_corr_tr": round(l0_tr, 4), "lag0_corr_fw": round(l0_fw, 4),
            "best_lag_tr": best_tr[0], "best_corr_tr": round(best_tr[1], 4), "n_tr": n_tr,
            "best_lag_fw": best_fw[0], "best_corr_fw": round(best_fw[1], 4), "n_fw": n_fw,
            "lead_gain_tr": round(lead_gain_tr, 4), "lead_gain_fw": round(lead_gain_fw, 4),
            "mi_fw_lag1": round(_sign_mi(a, b, 1, 2025, None), 4),
            "stable": stable,
        })
    edges.sort(key=lambda e: abs(e["best_corr_fw"]), reverse=True)
    return edges

# ----------------------------------------------------------------------------
# 2) MINER: leader impulse -> laggard forward odds (leak-free, geometry_lib fill).
# ----------------------------------------------------------------------------
def leader_signal(leader, look, volwin=100):
    """time -> z-scored cumulative log return of leader over `look` closed bars.
    z uses a TRAILING window ending at i-1 (no lookahead). Decision at close of bar i."""
    p = panel(leader)
    T = p["times"]; lr = p["lr"]; n = len(lr)
    cum = [0.0] * n
    for i in range(look, n):
        cum[i] = sum(lr[i-look+1:i+1])
    out = {}
    for i in range(look + volwin, n):
        win = cum[i-volwin:i]          # ends at i-1 -> no lookahead
        m = sum(win) / len(win)
        var = sum((x-m)**2 for x in win) / len(win)
        sd = math.sqrt(var) if var > 0 else 0.0
        if sd > 0:
            out[T[i]] = (cum[i] - m) / sd
    return out

GEOMS = {
    "T1.0":  {"mode": "fixed", "tmult": 1.0},
    "T1.5":  {"mode": "fixed", "tmult": 1.5},
    "T2.0":  {"mode": "fixed", "tmult": 2.0},
    "TRAIL": {"mode": "trail"},
}

def _laggard_regime_ok(B, atrs, i, want, lb=20):
    """Optional confluence gate on the laggard at decision bar i (closed bars only).
    want='trend_up'/'trend_down' aligns entry with laggard's own slope; 'lowvol'/'hivol'
    gate on vol_ratio; None disables."""
    if want is None:
        return True
    if want in ("trend_up", "trend_down"):
        if i < lb: return False
        a = atrs[i]
        if a <= 0: return False
        slope = B[i].c - B[i-lb].c
        if want == "trend_up":  return slope > 0.5 * a
        else:                   return slope < -0.5 * a
    if want in ("lowvol", "hivol"):
        if i < 100: return True
        s = sum(atrs[i-99:i+1]) / 100
        vr = atrs[i] / s if s > 0 else 1.0
        return vr < 1.2 if want == "lowvol" else vr > 1.4
    return True

def mine_pair(leader, follower, relsign, look, zthr, thesis, geom,
              confirm=None, confirm_sign=None, regime=None, min_gap=2, maxbars=80):
    """One driver->follower hypothesis. Returns per-trade list (time,year,direction,R).
    relsign: economic sign of returns corr (leader up => follower up if +1, down if -1).
    thesis : 'momentum' (trade WITH the implied relation) or 'reversion' (against it).
    confirm/confirm_sign: optional 2nd leader that must AGREE in implied follower direction.
    regime : optional laggard-regime confluence gate (see _laggard_regime_ok)."""
    sig = leader_signal(leader, look)
    csig = leader_signal(confirm, look) if confirm else None
    pf = panel(follower)
    fb = pf["bars"]; ftmap = pf["tmap"]; fatrs = pf["atrs"]
    cost = cost_for(follower)
    trades = []
    last_idx = -10**9
    for ts, z in sig.items():
        if abs(z) < zthr:
            continue
        i = ftmap.get(ts)
        if i is None or i < 14 or i >= len(fb) - 2:
            continue
        if i - last_idx < min_gap:
            continue
        a = fatrs[i]
        if a <= 0:
            continue
        # implied follower direction from leader move + relation sign + thesis
        base = (1 if z > 0 else -1) * relsign
        d = base if thesis == "momentum" else -base
        # dual-leader confirmation: 2nd leader must imply the SAME follower direction
        if confirm is not None:
            cz = csig.get(ts)
            if cz is None or abs(cz) < zthr:
                continue
            cbase = (1 if cz > 0 else -1) * confirm_sign
            cd = cbase if thesis == "momentum" else -cbase
            if cd != d:
                continue
        # laggard regime confluence
        if regime is not None:
            want = "trend_up" if (d > 0 and regime == "align") else \
                   "trend_down" if (d < 0 and regime == "align") else regime
            if not _laggard_regime_ok(fb, fatrs, i, want):
                continue
        stop = 0.5 * a
        if geom["mode"] == "fixed":
            R = simulate(fb, i, d, stop_dist=stop, target_dist=geom["tmult"] * a,
                         cost=cost, maxbars=maxbars)
        else:
            R = simulate(fb, i, d, stop_dist=stop, trail_arm=2 * stop, trail_gap=1 * stop,
                         cost=cost, maxbars=maxbars)
        trades.append((ts, ts.year, d, R))
        last_idx = i
    return trades

# ----- stats / split helpers (TRAIN<=2024 vs FORWARD2025-26, per-year, fwd halves) -----
def _stats(trades):
    if not trades:
        return {"n": 0, "R": 0.0, "win": 0.0}
    rs = [t[3] for t in trades]
    n = len(rs)
    return {"n": n, "R": round(sum(rs)/n, 4), "win": round(sum(1 for r in rs if r > 0)/n, 3)}

def split_stats(trades):
    train = [t for t in trades if t[1] <= 2024]
    fwd = [t for t in trades if t[1] >= 2025]
    fs = sorted(fwd, key=lambda x: x[0])
    h = len(fs) // 2
    per_year = {y: _stats([t for t in trades if t[1] == y])
                for y in sorted(set(t[1] for t in trades))}
    return {"train": _stats(train), "forward": _stats(fwd),
            "fwd_h1": _stats(fs[:h]), "fwd_h2": _stats(fs[h:]),
            "per_year": per_year}

def forward_stable(sp, min_fwd=40, min_half=15):
    f = sp["forward"]; h1 = sp["fwd_h1"]; h2 = sp["fwd_h2"]
    return (f["n"] >= min_fwd and f["R"] > 0 and
            h1["n"] >= min_half and h2["n"] >= min_half and
            h1["R"] > 0 and h2["R"] > 0)

def train_forward_robust(sp, min_train=40, min_fwd=40):
    """Strongest tier: positive in BOTH a real TRAIN(<=2024) sample AND forward."""
    t = sp["train"]; f = sp["forward"]
    return (t["n"] >= min_train and t["R"] > 0 and f["n"] >= min_fwd and f["R"] > 0)

# ----------------------------------------------------------------------------
# Economic relation catalog (sign = expected returns corr). Used as a directional prior
# so we never trade a spurious sign. Both momentum & reversion theses are tested per pair.
# ----------------------------------------------------------------------------
RELATIONS = [
    # USD strength block (DXY is forward-only but keep for the forward map)
    ("DXY_cash", "EURUSD", -1), ("DXY_cash", "GBPUSD", -1), ("DXY_cash", "AUDUSD", -1),
    ("DXY_cash", "NZDUSD", -1), ("DXY_cash", "USDJPY", +1), ("DXY_cash", "USDCHF", +1),
    ("DXY_cash", "USDCAD", +1), ("DXY_cash", "XAUUSD", -1), ("DXY_cash", "XAGUSD", -1),
    # Oil -> CAD (oil up => USDCAD down)
    ("USOIL_cash", "USDCAD", -1), ("UKOIL_cash", "USDCAD", -1),
    # Risk-on equity index leads risk FX & crypto
    ("SPX500", "AUDUSD", +1), ("SPX500", "NZDUSD", +1), ("SPX500", "USDJPY", +1),
    ("SPX500", "BTCUSD", +1), ("NAS100", "BTCUSD", +1), ("NAS100", "ETHUSD", +1),
    ("NAS100", "AUDUSD", +1), ("NAS100", "USDJPY", +1), ("US30_cash", "AUDUSD", +1),
    ("GER40", "EURUSD", +1), ("US30_cash", "USDJPY", +1),
    # Metals cross
    ("XAUUSD", "XAGUSD", +1), ("XAUUSD", "XCUUSD", +1), ("XAGUSD", "XAUUSD", +1),
    # BTC leads alts
    ("BTCUSD", "ETHUSD", +1), ("BTCUSD", "LTCUSD", +1), ("BTCUSD", "ADAUSD", +1),
    ("BTCUSD", "DOTUSD", +1), ("BTCUSD", "DASHUSD", +1), ("BTCUSD", "XTZUSD", +1),
    ("ETHUSD", "ADAUSD", +1), ("ETHUSD", "LTCUSD", +1),
    # EUR strength proxy
    ("EURUSD", "GBPUSD", +1), ("EURUSD", "AUDUSD", +1), ("EURUSD", "XAUUSD", +1),
    ("EURUSD", "EURGBP", +1), ("GBPUSD", "EURUSD", +1),
    # JPY risk: USDJPY leads other JPY crosses
    ("USDJPY", "EURJPY", +1), ("USDJPY", "GBPJPY", +1), ("USDJPY", "AUDJPY", +1),
    ("USDJPY", "CHFJPY", +1), ("EURJPY", "GBPJPY", +1),
    # Copper / AUD growth proxy
    ("XCUUSD", "AUDUSD", +1), ("AUDUSD", "NZDUSD", +1),
    # index co-movement
    ("SPX500", "GER40", +1), ("NAS100", "SPX500", +1), ("GER40", "UK100", +1),
    ("US30_cash", "GER40", +1), ("SPX500", "NAS100", +1),
]

def _has(sym):
    return coverage(sym)[2] > 0
RELATIONS = [r for r in RELATIONS if _has(r[0]) and _has(r[1])]

LOOKS = [3, 6, 12]
ZTHRS = [1.0, 1.5, 2.0]
THESES = ["momentum", "reversion"]

def mine_all(relations=None, looks=None, zthrs=None, with_confluence=True):
    """Run the catalog. Returns list of result dicts with full split stats.
    with_confluence adds the best dual-leader & regime-gated variants on top of the base grid."""
    relations = relations if relations is not None else RELATIONS
    looks = looks if looks is not None else LOOKS
    zthrs = zthrs if zthrs is not None else ZTHRS
    rows = []
    for (leader, follower, sign) in relations:
        ov = len([t for t in panel(leader)["times"] if t in panel(follower)["tmap"]])
        if ov < 300:
            continue
        for look in looks:
            for z in zthrs:
                for thesis in THESES:
                    for gname, geom in GEOMS.items():
                        tr = mine_pair(leader, follower, sign, look, z, thesis, geom)
                        if len(tr) < 40:
                            continue
                        sp = split_stats(tr)
                        rows.append({
                            "leader": leader, "follower": follower, "relsign": sign,
                            "look": look, "z": z, "thesis": thesis, "geom": gname,
                            "confluence": "base", "overlap": ov, "n": len(tr),
                            "all": _stats(tr), **sp,
                            "follower_ac": ASSET_CLASS_BY_SYMBOL.get(follower),
                            "fwd_stable": forward_stable(sp),
                            "tr_fw_robust": train_forward_robust(sp),
                        })
    if with_confluence:
        rows += _mine_confluence(relations)
    rows.sort(key=lambda r: r["forward"]["R"], reverse=True)
    return rows

# dual-leader confirmation pairs worth trying (independent leaders -> same follower)
CONFIRM_SETS = [
    ("USDJPY", +1, "SPX500", +1, "AUDJPY"),   # risk-on via yen + equity -> AUDJPY
    ("SPX500", +1, "NAS100", +1, "BTCUSD"),
    ("XAUUSD", +1, "DXY_cash", -1, "XAGUSD"), # gold up & dollar down -> silver up
    ("EURUSD", +1, "GBPUSD", +1, "AUDUSD"),
    ("USOIL_cash", -1, "DXY_cash", +1, "USDCAD"),
    ("BTCUSD", +1, "ETHUSD", +1, "LTCUSD"),
]

def _mine_confluence(relations):
    rows = []
    relmap = {(l, f): s for l, f, s in relations}
    # 1) dual-leader confirmation
    for (lA, sA, lB, sB, follower) in CONFIRM_SETS:
        if not (_has(lA) and _has(lB) and _has(follower)):
            continue
        for look in (3, 6):
            for z in (1.0, 1.5):
                for thesis in ("momentum",):
                    for gname in ("T1.5", "T2.0", "TRAIL"):
                        tr = mine_pair(lA, follower, sA, look, z, thesis, GEOMS[gname],
                                       confirm=lB, confirm_sign=sB)
                        if len(tr) < 30:
                            continue
                        sp = split_stats(tr)
                        rows.append({
                            "leader": f"{lA}+{lB}", "follower": follower, "relsign": sA,
                            "look": look, "z": z, "thesis": thesis, "geom": gname,
                            "confluence": "dual_leader", "overlap": 0, "n": len(tr),
                            "all": _stats(tr), **sp,
                            "follower_ac": ASSET_CLASS_BY_SYMBOL.get(follower),
                            "fwd_stable": forward_stable(sp, min_fwd=30, min_half=10),
                            "tr_fw_robust": train_forward_robust(sp, min_train=20, min_fwd=30),
                        })
    # 2) laggard-regime-aligned variant on the strongest single-leader relations
    for (leader, follower, sign) in relations:
        ov = len([t for t in panel(leader)["times"] if t in panel(follower)["tmap"]])
        if ov < 300:
            continue
        for look in (3, 6):
            for z in (1.5,):
                for thesis in ("momentum",):
                    for gname in ("T1.5", "T2.0"):
                        tr = mine_pair(leader, follower, sign, look, z, thesis, GEOMS[gname],
                                       regime="align")
                        if len(tr) < 30:
                            continue
                        sp = split_stats(tr)
                        rows.append({
                            "leader": leader, "follower": follower, "relsign": sign,
                            "look": look, "z": z, "thesis": thesis, "geom": gname,
                            "confluence": "regime_align", "overlap": ov, "n": len(tr),
                            "all": _stats(tr), **sp,
                            "follower_ac": ASSET_CLASS_BY_SYMBOL.get(follower),
                            "fwd_stable": forward_stable(sp, min_fwd=30, min_half=10),
                            "tr_fw_robust": train_forward_robust(sp, min_train=20, min_fwd=30),
                        })
    return rows

# ----------------------------------------------------------------------------
# Script entry: build graph, mine catalog, print + persist the queryable map.
# ----------------------------------------------------------------------------
def main():
    print("=" * 110)
    print("LEAD-LAG GRAPH (deep w1.load panel, aligned H4 log returns)")
    print("=" * 110)
    # restrict graph candidates to economically-plausible + high-overlap pairs to keep it fast,
    # but also scan all pairs of the deepest symbols for surprise links.
    deep = [s for s in SYMBOLS if coverage(s)[2] > 2000]
    cand = [(a, b) for a in deep for b in deep if a != b]
    edges = build_graph(candidates=cand)
    print(f"{'leader':>12} {'follower':>12} {'lagFW':>5} {'corrFW':>7} {'corrTR':>7} "
          f"{'gainFW':>7} {'gainTR':>7} {'miFW':>6} {'nFW':>6} {'nTR':>6} stable")
    for e in edges[:30]:
        print(f"{e['leader']:>12} {e['follower']:>12} {e['best_lag_fw']:>5} "
              f"{e['best_corr_fw']:>7.3f} {e['best_corr_tr']:>7.3f} "
              f"{e['lead_gain_fw']:>7.3f} {e['lead_gain_tr']:>7.3f} {e['mi_fw_lag1']:>6.3f} "
              f"{e['n_fw']:>6} {e['n_tr']:>6} {'YES' if e['stable'] else ''}")
    json.dump(edges, open(EDGE + "/LEADLAG_GRAPH.json", "w"), default=str, indent=1)
    print(f"\nwrote LEADLAG_GRAPH.json ({len(edges)} directed pairs)")

    print("\n" + "=" * 110)
    print("LEAD-LAG TRADEABLE EDGE MINER (TRAIN<=2024 vs FORWARD 2025-26, per-year, fwd halves)")
    print("=" * 110)
    rows = mine_all()
    json.dump(rows, open(EDGE + "/LEADLAG_EDGES.json", "w"), default=str, indent=1)

    print(f"\nTop 35 by FORWARD per-trade R (n>=40):")
    hdr = (f"{'leader':>16}->{'follower':<10} {'conf':>12} L{'':1} z {'thesis':>9} {'g':>5} | "
           f"{'fN':>4} {'fR':>7} {'fW':>4} | {'h1R':>6} {'h2R':>6} | {'trN':>4} {'trR':>7} | flags")
    print(hdr)
    for r in rows[:35]:
        f = r["forward"]; t = r["train"]; h1 = r["fwd_h1"]; h2 = r["fwd_h2"]
        flags = ("S" if r["fwd_stable"] else "") + ("R" if r["tr_fw_robust"] else "")
        print(f"{r['leader']:>16}->{r['follower']:<10} {r['confluence']:>12} "
              f"{r['look']} {r['z']} {r['thesis']:>9} {r['geom']:>5} | "
              f"{f['n']:>4} {f['R']:>7.3f} {f['win']:>4.2f} | {h1['R']:>6.2f} {h2['R']:>6.2f} | "
              f"{t['n']:>4} {t['R']:>7.3f} | {flags}")

    # forward-stable winners
    stable = [r for r in rows if r["fwd_stable"]]
    stable.sort(key=lambda r: r["forward"]["R"], reverse=True)
    print("\n" + "=" * 110)
    print(f"FORWARD-STABLE edges (fwd n>=40, fwd R>0, both halves R>0): {len(stable)}")
    print("-" * 110)
    for r in stable[:25]:
        f = r["forward"]; t = r["train"]
        py = " ".join(f"{y}:{v['R']:+.2f}({v['n']})" for y, v in sorted(r["per_year"].items()))
        rob = " TRAIN+FWD-ROBUST" if r["tr_fw_robust"] else ""
        print(f"{r['leader']}->{r['follower']} [{r['confluence']}] L{r['look']} z{r['z']} "
              f"{r['thesis']} {r['geom']} | fN={f['n']} fR={f['R']:+.3f} fW={f['win']:.2f} | "
              f"trN={t['n']} trR={t['R']:+.3f}{rob}\n        per-year: {py}")

    # the strongest tier: positive in BOTH a real train sample and forward
    robust = [r for r in rows if r["tr_fw_robust"]]
    robust.sort(key=lambda r: min(r["train"]["R"], r["forward"]["R"]), reverse=True)
    print("\n" + "=" * 110)
    print(f"TRAIN+FORWARD ROBUST edges (real TRAIN n>=40 R>0 AND forward n>=40 R>0): {len(robust)}")
    print("-" * 110)
    for r in robust[:25]:
        f = r["forward"]; t = r["train"]
        py = " ".join(f"{y}:{v['R']:+.2f}({v['n']})" for y, v in sorted(r["per_year"].items()))
        print(f"{r['leader']}->{r['follower']} [{r['confluence']}] L{r['look']} z{r['z']} "
              f"{r['thesis']} {r['geom']} | trN={t['n']} trR={t['R']:+.3f} | "
              f"fN={f['n']} fR={f['R']:+.3f} fW={f['win']:.2f}\n        per-year: {py}")

    # aggregate: does momentum or reversion dominate forward across the family?
    print("\n" + "=" * 110)
    print("AGGREGATE forward edge by thesis (trade-weighted, base configs only):")
    agg = defaultdict(lambda: [0, 0.0, 0.0])
    for r in rows:
        if r["confluence"] != "base":
            continue
        f = r["forward"]
        agg[r["thesis"]][0] += f["n"]; agg[r["thesis"]][1] += f["R"] * f["n"]
        agg[r["thesis"]][2] += f["win"] * f["n"]
    for th, (n, sr, wn) in agg.items():
        if n:
            print(f"  {th:>9}: fwd N={n:>6}  per-trade R={sr/n:+.4f}  win={wn/n:.3f}")
    return edges, rows

if __name__ == "__main__":
    main()
