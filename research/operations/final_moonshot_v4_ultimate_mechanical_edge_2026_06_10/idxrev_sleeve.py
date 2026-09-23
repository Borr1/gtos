"""IDXREV — Index regime-gated mean-reversion sleeve (track key: idxrev).

THESIS (distinct from prior reversion failures):
  Indices MEAN-REVERT where commodities trend. Fade STRUCTURAL extremes (prior-day /
  rolling-range high/low sweeps that fail to hold), GATED by the leak-free RANGING
  regime = LOW ac60 (the INVERSE of the persistence gate cs.autocorr(B,i,60) that makes
  commodity CONTINUATION pay). Prior reversion work failed using ADX/efficiency-ratio
  range filters and far 2R targets. This sleeve uses (a) ac60 ranging gate, (b) failed-
  breakout STRUCTURE (sweep prior extreme intrabar then close back inside = reclaim),
  (c) tight high-hit-rate geometry tuned on TRAIN only.

LEAK-FREE: every feature uses bars[<=i]. Entry at close of bar i. geometry_lib.simulate
labels the outcome (looks forward only to score). FORWARD HOLDOUT: thresholds chosen on
entries year<=2024, then the SAME fixed rule reported FORWARD 2025 and 2026 separately,
per-year and per-symbol.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
from src.research_infra.learned_edge_dataset_builder import ASSET_CLASS_BY_SYMBOL

INDICES = [s for s, c in ASSET_CLASS_BY_SYMBOL.items() if c == 'index']

def wins(r): return max(-1.3, min(5.0, r))

def rolling_extreme(B, i, lb):
    """prior-N-bar high/low over bars[i-lb..i-1] (strictly closed, no bar i)."""
    if i < lb: return None, None
    hi = max(B[k].h for k in range(i-lb, i))
    lo = min(B[k].l for k in range(i-lb, i))
    return hi, lo

def signals(sym, lb_range=12, atr_stop_floor=0.25):
    """Failed-breakout reclaim of a rolling-range extreme.
    Sweep ABOVE prior-range high intrabar but CLOSE back below it -> SHORT (fade).
    Sweep BELOW prior-range low intrabar but CLOSE back above it  -> LONG  (fade).
    Yields (t, d, i, B, ac60, vr, atr, dist_to_opp) with all features leak-free.
    """
    T, B = w1.load(sym)
    if len(B) < 150: return
    atrs = [atr14(B, k) for k in range(len(B))]
    pdh, pdl, psh, psl = w1.levels(T, B)
    for i in range(120, len(B)):
        a = atrs[i]
        if a <= 0: continue
        rhi, rlo = rolling_extreme(B, i, lb_range)
        if rhi is None: continue
        b = B[i]
        ac = cs.autocorr(B, i, 60)
        if ac is None: continue
        vr = cs.vol_ratio(atrs, i)
        # failed breakout up -> short
        if b.h > rhi and b.c < rhi:
            d = -1
            dist_opp = (b.c - rlo) / a  # room to opposite side in ATR
            yield (T[i], d, i, B, ac, vr, a, dist_opp, b.c, rhi, rlo, pdh[i], pdl[i])
        # failed breakout down -> long
        elif b.l < rlo and b.c > rlo:
            d = 1
            dist_opp = (rhi - b.c) / a
            yield (T[i], d, i, B, ac, vr, a, dist_opp, b.c, rhi, rlo, pdh[i], pdl[i])

def run(lb_range=12, ac_max=0.0, stop_atr=1.0, tgt_R=1.0, trail=None,
        require_pd=False, symbols=None, maxbars=60):
    """ac_max: ranging gate, take only ac60 <= ac_max (low persistence = ranging).
    stop_atr: stop distance in ATR. tgt_R: target in R (=stop_atr*ATR). trail=(armR,gapR).
    require_pd: also require the swept level be within 0.3 ATR of prior-day extreme.
    """
    syms = symbols or INDICES
    rows = []
    for s in syms:
        cost = w1.cost_for(s)
        # scale cost by stop tightness: cost is in price-ATR-ish R at 1.0 stop; tighter stop -> bigger R cost
        for (t, d, i, B, ac, vr, a, dist_opp, c, rhi, rlo, pdh, pdl) in signals(s, lb_range):
            if ac > ac_max: continue
            sd = stop_atr * a
            if require_pd:
                lvl = rhi if d < 0 else rlo
                ref = pdh if d < 0 else pdl
                if ref is None or abs(lvl - ref) > 0.3 * a: continue
            rcost = cost / stop_atr  # cost in R scales inversely with stop tightness
            if trail:
                R = simulate(B, i, d, stop_dist=sd, trail_arm=trail[0]*sd,
                             trail_gap=trail[1]*sd, maxbars=maxbars, cost=rcost)
            else:
                R = simulate(B, i, d, stop_dist=sd, target_dist=tgt_R*sd,
                             maxbars=maxbars, cost=rcost)
            rows.append(dict(sym=s, year=t.year, date=str(t)[:10], dir=d,
                             ac60=round(ac, 4), vr=round(vr, 3), R=wins(R)))
    return rows

def stat(rows):
    if not rows: return (0, 0.0, 0.0)
    n = len(rows); m = sum(r['R'] for r in rows)/n
    w = sum(1 for r in rows if r['R'] > 0)/n*100
    return n, m, w

def report(rows, label):
    print(f"\n=== {label} ===")
    yrs = sorted(set(r['year'] for r in rows))
    print(f"{'year':>5} {'n':>5} {'R/t':>8} {'win%':>6}")
    for y in yrs:
        ry = [r for r in rows if r['year'] == y]
        n, m, wn = stat(ry)
        tag = ' <FWD' if y >= 2025 else ''
        print(f"{y:>5} {n:>5} {m:>+8.3f} {wn:>5.0f}%{tag}")
    tr = [r for r in rows if r['year'] <= 2024]
    f25 = [r for r in rows if r['year'] == 2025]
    f26 = [r for r in rows if r['year'] == 2026]
    fwd = [r for r in rows if r['year'] >= 2025]
    for lab, rr in (('TRAIN<=2024', tr), ('FWD2025', f25), ('FWD2026', f26), ('FWD25-26', fwd)):
        n, m, wn = stat(rr)
        print(f"  {lab:>12}: n={n:>4} R/t={m:+.3f} win={wn:.0f}%")
    return stat(tr), stat(fwd)
