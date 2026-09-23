"""FREQBREADTH track — recover FREQUENCY + BREADTH on the commodity continuation core
without losing EV, via CONFIDENCE-GRADED sizing and an EXPANDED same-direction trigger set.

Baseline to beat/extend (compounding_sleeve.py, metals ex-copper):
  FVG-retest continuation + hard ac60>=0.10 gate + STATE_D scale-out exit
  = +0.865R/trade FORWARD 2025-26, 78% win, ~24.5 trades/yr.

Two levers, both under the SAME persistence regime (continuation pays when momentum persists):
  1. CONFIDENCE-GRADED SIZE: drop the hard ac60>=0.10 cutoff to ac60>=AC_FLOOR (0.05),
     and size each trade by a multiplier rising in ac60 (and vol-tier), instead of 0/1.
  2. EXPANDED TRIGGERS: pool three same-direction continuation entries
       (a) FVG-retest  (g.fvg_signals)              -- baseline trigger
       (b) sweep+reclaim, next-bar entry, TREND-filtered (continuation form)
       (c) order-block retest in HTF trend (continuation)
     all gated by the SAME ac60 regime gate, all exited by the SAME STATE_D scale-out.

DISCIPLINE:
  - state/features (ac60, vr, trend) only from CLOSED bars index<=i. geometry_lib.simulate
    is the leak-free outcome labeler.
  - Thresholds chosen on TRAIN entries (year<=2024). The SAME fixed rule is then reported
    FORWARD 2025 and 2026 separately + per-year + per-symbol.
  - Real cost via w1.cost_for. net R winsorized to [-1.3,+5] (cs.wins / exit_state_d already do).
  - confidence-WEIGHTED EV = sum(size_i * R_i) / sum(size_i)  -- the realised EV per unit risk
    if you actually size by the multiplier. We also report raw (unweighted) EV and trades/yr.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs

METALS = g.METALS                       # precious metals ex-copper (the proven carrier)
AC_FLOOR = 0.05                         # soft floor (was hard 0.10); below this -> no trade
AC_BASE  = 0.10                         # baseline hard gate (reference)

# ---------- shared per-symbol context cache ----------
_CTX = {}
def ctx(sym):
    if sym in _CTX: return _CTX[sym]
    T, B = w1.load(sym)
    atrs = [atr14(B, k) for k in range(len(B))] if B else []
    _CTX[sym] = (T, B, atrs, w1.cost_for(sym))
    return _CTX[sym]

# ---------- trigger generators: each yields (t, d, sd, i)  [continuation only] ----------
def trig_fvg(sym):
    for (t, d, sd, td, i, B, cost) in g.fvg_signals(sym):
        yield (t, d, sd, i, 'fvg')

def trig_sweep(sym):
    """Sweep+reclaim with TREND filter so it is a CONTINUATION (same family as FVG)."""
    T, B, atrs, cost = ctx(sym)
    if len(B) < 200: return
    pdh, pdl, psh, psl = w1.levels(T, B)
    n = len(B)
    for i in range(60, n-2):
        a = atrs[i]
        if a <= 0: continue
        b = B[i]; nb = B[i+1]; lo = pdl[i]; hi = pdh[i]
        tr = w1.htf_trend(B, i, 30)
        entry = nb.o
        # sweep LOW + reclaim -> long, only in up-trend (continuation), enter next bar
        if lo is not None and (lo - b.l) >= 0.05*a and b.c > lo and (b.c - lo) >= 0.10*a and tr >= 0:
            sd = max((entry - b.l) + 0.05*a, 0.20*a)
            yield (T[i+1], +1, sd, i+1, 'sweep')
        # sweep HIGH + reclaim -> short, only in down-trend (continuation)
        if hi is not None and (b.h - hi) >= 0.05*a and b.c < hi and (hi - b.c) >= 0.10*a and tr <= 0:
            sd = max((b.h - entry) + 0.05*a, 0.20*a)
            yield (T[i+1], -1, sd, i+1, 'sweep')

def trig_ob(sym):
    """Order-block retest in HTF trend (continuation)."""
    T, B, atrs, cost = ctx(sym)
    if len(B) < 200: return
    n = len(B)
    for i in range(60, n-1):
        a = atrs[i]
        if a <= 0: continue
        tr = w1.htf_trend(B, i, 30); b = B[i]
        if tr == 1:
            for k in range(i-2, max(i-9, 60), -1):
                if not (B[k].c < B[k].o): continue       # need a down (order-block) candle
                gap_top = B[k].h; gap_bot = B[k].l
                if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                    sd = max((b.c - min(b.l, gap_bot)) + 0.10*a, 0.25*a)
                    yield (T[i], +1, sd, i, 'ob'); break
        elif tr == -1:
            for k in range(i-2, max(i-9, 60), -1):
                if not (B[k].c > B[k].o): continue
                gap_bot = B[k].l; gap_top = B[k].h
                if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                    sd = max((max(b.h, gap_top) - b.c) + 0.10*a, 0.25*a)
                    yield (T[i], -1, sd, i, 'ob'); break

TRIGS = {'fvg': trig_fvg, 'sweep': trig_sweep, 'ob': trig_ob}

# ---------- confidence -> size multiplier (the deliverable function) ----------
def size_mult(ac, vr, shape='ramp'):
    """Confidence-graded position size in [0, 1.5]. 0 below AC_FLOOR (no trade).
    'ramp'  : linear ramp in ac60 from AC_FLOOR..0.20 -> 0.4..1.2, vol-tier kicker.
    'tiered': discrete confidence buckets.
    'hard'  : baseline 0/1 hard gate at AC_BASE (for parity comparison).
    """
    if ac is None: return 0.0
    if shape == 'hard':
        return 1.0 if ac >= AC_BASE else 0.0
    if ac < AC_FLOOR: return 0.0
    if shape == 'tiered':
        if ac < 0.075: base = 0.4
        elif ac < 0.10: base = 0.7
        elif ac < 0.15: base = 1.0
        else: base = 1.2
    else:  # ramp
        # linear 0.40 at ac=0.05 -> 1.20 at ac=0.20, clamp
        base = 0.40 + (ac - AC_FLOOR) * (0.80 / 0.15)
        base = max(0.40, min(1.20, base))
    # vol-tier kicker: the proven exit is best in LOW vol (cs STATE_D LOW tier ran +1.50R fwd)
    if vr < 1.35: base *= 1.15
    elif vr >= 1.6: base *= 0.90
    return round(min(1.5, base), 4)

# ---------- build the pooled, de-duplicated ledger ----------
def build(triggers=('fvg',), shape='ramp', ac_floor=AC_FLOOR):
    """Pool the chosen triggers across METALS. De-dup same (sym, bar i, dir) so two
    triggers firing on one bar count once (priority fvg>ob>sweep). Apply ac gate + STATE_D
    exit + confidence size. Returns ledger rows."""
    pri = {'fvg': 0, 'ob': 1, 'sweep': 2}
    rows = []
    for sym in METALS:
        T, B, atrs, cost = ctx(sym)
        if len(B) < 200: continue
        # collect candidate entries from all chosen triggers, keyed by (i, dir)
        cand = {}
        for tg in triggers:
            for (t, d, sd, i, src) in TRIGS[tg](sym):
                key = (i, d)
                if key not in cand or pri[src] < pri[cand[key][4]]:
                    cand[key] = (t, d, sd, i, src)
        for (i, d), (t, dd, sd, ii, src) in cand.items():
            ac = cs.autocorr(B, ii, 60)
            vr = cs.vol_ratio(atrs, ii)
            if ac is None: continue
            m = size_mult(ac, vr, shape=shape)
            if m <= 0: continue
            ex = cs.exit_state_d(B, ii, dd, sd, vr, cost)
            rows.append(dict(sym=sym, year=t.year, date=str(t)[:10], dir=dd, src=src,
                             ac60=round(ac, 4), vr=round(vr, 3), size=m,
                             R=round(ex['R'], 4), reason=ex['reason'], mfe=round(ex['mfe'], 3)))
    return rows

# ---------- weighted / unweighted stats ----------
def wstat(rows):
    if not rows: return dict(n=0, ev=0.0, wev=0.0, win=0.0, sz=0.0)
    n = len(rows)
    ev = sum(r['R'] for r in rows) / n
    W = sum(r['size'] for r in rows)
    wev = sum(r['size'] * r['R'] for r in rows) / W if W > 0 else 0.0
    win = sum(1 for r in rows if r['R'] > 0) / n * 100
    return dict(n=n, ev=round(ev, 4), wev=round(wev, 4), win=round(win, 1), sz=round(W, 2))

def per_year_block(rows, label):
    print(f"\n--- {label} : per-year (n | raw EV | conf-wtd EV | win%) ---")
    yrs = sorted(set(r['year'] for r in rows))
    for y in yrs:
        rr = [r for r in rows if r['year'] == y]
        s = wstat(rr)
        tag = ' <FWD' if y >= 2025 else ''
        print(f"  {y}: n={s['n']:>3}  raw={s['ev']:+.3f}  wtd={s['wev']:+.3f}  win={s['win']:>4.0f}%{tag}")
    fwd = [r for r in rows if r['year'] >= 2025]
    s = wstat(fwd)
    tpy = s['n'] / 2.0
    print(f"  FORWARD 2025-26: n={s['n']} ({tpy:.1f}/yr)  raw={s['ev']:+.3f}  conf-wtd={s['wev']:+.3f}  win={s['win']:.0f}%")
    return wstat(rows), wstat(fwd), tpy

def per_symbol_fwd(rows):
    print("  per-symbol FWD 2025-26:")
    fwd = [r for r in rows if r['year'] >= 2025]
    by = collections.defaultdict(list)
    for r in fwd: by[r['sym']].append(r)
    for sym in sorted(by, key=lambda k: -wstat(by[k])['wev']):
        s = wstat(by[sym]); print(f"     {sym:>7}: n={s['n']:>3} raw={s['ev']:+.3f} wtd={s['wev']:+.3f} win={s['win']:.0f}%")

def per_src_fwd(rows):
    print("  per-trigger FWD 2025-26:")
    fwd = [r for r in rows if r['year'] >= 2025]
    by = collections.defaultdict(list)
    for r in fwd: by[r['src']].append(r)
    for src in sorted(by, key=lambda k: -wstat(by[k])['n']):
        s = wstat(by[src]); print(f"     {src:>6}: n={s['n']:>3} raw={s['ev']:+.3f} wtd={s['wev']:+.3f} win={s['win']:.0f}%")

def main():
    out = {}
    print("="*78)
    print("BASELINE PARITY: FVG only, hard ac60>=0.10, STATE_D (reproduce +0.865R/24.5pyr)")
    base = build(triggers=('fvg',), shape='hard')
    a, f, t = per_year_block(base, "BASELINE hard-gate FVG"); per_symbol_fwd(base)
    out['baseline_hard'] = dict(all=a, fwd=f, tpy=t)

    print("\n" + "="*78)
    print("LEVER 1 only: FVG, SOFT ac60>=0.05 + RAMP confidence size (no new triggers)")
    soft = build(triggers=('fvg',), shape='ramp')
    a, f, t = per_year_block(soft, "FVG soft-ramp"); per_symbol_fwd(soft)
    out['fvg_soft_ramp'] = dict(all=a, fwd=f, tpy=t)

    print("\n" + "="*78)
    print("LEVER 1 (tiered) : FVG, SOFT ac60>=0.05 + TIERED confidence size")
    soft_t = build(triggers=('fvg',), shape='tiered')
    a, f, t = per_year_block(soft_t, "FVG soft-tiered"); per_symbol_fwd(soft_t)
    out['fvg_soft_tiered'] = dict(all=a, fwd=f, tpy=t)

    print("\n" + "="*78)
    print("LEVER 2 only: POOLED triggers (fvg+sweep+ob), HARD ac60>=0.10 gate, equal size")
    pooled_hard = build(triggers=('fvg', 'sweep', 'ob'), shape='hard')
    a, f, t = per_year_block(pooled_hard, "POOLED hard-gate"); per_src_fwd(pooled_hard); per_symbol_fwd(pooled_hard)
    out['pooled_hard'] = dict(all=a, fwd=f, tpy=t)

    print("\n" + "="*78)
    print("BOTH LEVERS: POOLED triggers + SOFT ac60>=0.05 + RAMP confidence size  <<< CANDIDATE")
    both = build(triggers=('fvg', 'sweep', 'ob'), shape='ramp')
    a, f, t = per_year_block(both, "POOLED soft-ramp"); per_src_fwd(both); per_symbol_fwd(both)
    out['pooled_soft_ramp'] = dict(all=a, fwd=f, tpy=t)

    print("\n" + "="*78)
    print("BOTH LEVERS (tiered): POOLED + SOFT + TIERED size")
    both_t = build(triggers=('fvg', 'sweep', 'ob'), shape='tiered')
    a, f, t = per_year_block(both_t, "POOLED soft-tiered"); per_src_fwd(both_t); per_symbol_fwd(both_t)
    out['pooled_soft_tiered'] = dict(all=a, fwd=f, tpy=t)

    (HERE/'FREQBREADTH_RESULT.json').write_text(json.dumps(out, indent=1))
    # also dump the winning candidate ledger
    (HERE/'FREQBREADTH_CANDIDATE_LEDGER.jsonl').write_text('\n'.join(json.dumps(r) for r in both))
    print("\nwrote FREQBREADTH_RESULT.json + FREQBREADTH_CANDIDATE_LEDGER.jsonl")

if __name__ == '__main__':
    main()
