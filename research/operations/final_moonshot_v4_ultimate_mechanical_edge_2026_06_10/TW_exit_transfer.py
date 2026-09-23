"""TW (transfer-winners) track — transfer the EXEC_COMBO / EXEC_LOCK exit to the crypto and
energy sleeves. Compare each sleeve's CURRENT exit vs EXEC_COMBO vs EXEC_LOCK on the IDENTICAL
fixed entry set. Per-year + per-regime, forward holdout. Keep if better, else learning.

EXEC_COMBO (KB_execution.md, train-validated on metals, +0.161R t4.34 train uplift):
  per vol regime (volrat = ATR14/SMA100(ATR14), known at entry):
   LOW  vr<1.35 : scale 50% @ +2.0R, runner stop -> +0.25R lock, runner target +4.0R
   MID  1.35-1.6: scale 50% @ +2.0R, runner stop -> +0.50R lock, runner target +3.0R
   HIGH vr>=1.6 : scale 50% @ +2.0R, runner stop -> +0.75R lock, runner target +2.5R
  initial stop structural 1R; after the scale leg, runner stop jumps to the lock level. no trail.

EXEC_LOCK (variance-neutral): keep STATE_D scale levels (1.5R / 1.0R-hi) but change runner stop
  from flat BE to vol-banded lock: LOW->BE(0); MID->+0.5R; HIGH->+0.75R. runner targets unchanged.

These exits operate in R-space on the entry's structural stop, so they are sleeve-agnostic.
We reuse EXEC_exit_variants.sim_exit (parity-proven to STATE_D, leak-free, pessimistic, winsorized).

NO LOOKAHEAD: vol regime fixed at entry; exit uses running MFE/MAE/bar-count only.
TRAIN = entries year<=2024; FORWARD = 2025 + 2026 reported separately + per-year + per-regime.
"""
import sys, json, statistics, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import atr14, simulate
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import energy_agri_sleeve as ea
from EXEC_exit_variants import sim_exit, wins

# ---------------------------------------------------------------------------
# Exit policy wrappers (all return a dict with R, reason, vr from sim_exit)
# ---------------------------------------------------------------------------
def exit_combo(ent, maxbars=80):
    """EXEC_COMBO: deeper 2.0R scale + vol-banded profit lock + vol-banded runner target."""
    vr = ent['vr']
    if vr < 1.35:   be, runR = 0.25, 4.0
    elif vr < 1.6:  be, runR = 0.50, 3.0
    else:           be, runR = 0.75, 2.5
    return sim_exit(ent, ladder=[(2.0, 0.5)], be_after_first=be, runner_R=runR, maxbars=maxbars)

def exit_lock(ent, maxbars=80):
    """EXEC_LOCK: STATE_D scale levels (1.5 lo/mid, 1.0 hi) but vol-banded lock instead of BE."""
    vr = ent['vr']
    if vr < 1.35:   scaleR, runR, be = 1.5, 4.0, 0.0
    elif vr < 1.6:  scaleR, runR, be = 1.5, 3.0, 0.5
    else:           scaleR, runR, be = 1.0, 2.5, 0.75
    return sim_exit(ent, ladder=[(scaleR, 0.5)], be_after_first=be, runner_R=runR, maxbars=maxbars)

def exit_state_d_via_sim(ent, maxbars=80):
    """STATE_D replicated through sim_exit (parity-proven). The metals/energy baseline exit."""
    vr = ent['vr']
    if vr < 1.35:   scaleR, runR = 1.5, 4.0
    elif vr < 1.6:  scaleR, runR = 1.5, 3.0
    else:           scaleR, runR = 1.0, 2.5
    return sim_exit(ent, ladder=[(scaleR, 0.5)], be_after_first=0.0, runner_R=runR, maxbars=maxbars)

def exit_target4(ent, maxbars=80):
    """Crypto baseline exit: fixed 4R target, structural 1R stop, no scale (single leg full pos)."""
    B = ent['B']; i = ent['i']; d = ent['d']; sd = ent['sd']; cost = ent['cost']
    R = simulate(B, i, d, stop_dist=sd, target_dist=4.0*sd, cost=cost, maxbars=maxbars)
    R = wins(R)
    # reason classification for runner-capture stat parity
    return dict(R=R, reason='target4', mfe=None, mae=None, bars1R=None, n_legs=0, vr=ent['vr'])

# ---------------------------------------------------------------------------
# Entry builders (FIXED entries per sleeve; carry full bar path + entry-state vol)
# ---------------------------------------------------------------------------
def build_crypto_entries():
    """BTCUSD+DASHUSD 20-bar Donchian breakout + ac60>=0.15 + sd=2*ATR (KB_crypto locked rule)."""
    KEEP = ['BTCUSD', 'DASHUSD']; ents = []
    for s in KEEP:
        T, B = w1.load(s)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        cost = w1.cost_for(s)
        n = len(B)
        for i in range(60, n-1):
            a = atrs[i]
            if a <= 0: continue
            hh = max(B[k].h for k in range(i-20, i)); ll = min(B[k].l for k in range(i-20, i))
            d = 0
            if B[i].c > hh: d = +1
            elif B[i].c < ll: d = -1
            if d == 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < 0.15: continue
            sd = 2.0 * a
            vr = cs.vol_ratio(atrs, i)
            ents.append(dict(sym=s, year=T[i].year, date=str(T[i])[:10], i=i, d=d, sd=sd,
                             vr=vr, ac=ac, cost=cost, atr=a, B=B))
    return ents

def build_energy_entries():
    """ENERGY FVG-retest continuation + A/B gate (vr>=2.0 OR |slope|<0.05). KB_energy locked.
    Cost scaled by stop tightness exactly like EXEC_exit_variants.build_entries."""
    ents = []
    for s in ea.ENERGY:
        try: T, B = w1.load(s)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        base_cost = w1.cost_for(s)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
            vr = cs.vol_ratio(atrs, i)
            slope = ea.trend_slope(B, i, 30)
            # ENERGY A-OR-B gate
            if not ((vr >= 2.0) or (abs(slope) < 0.05)): continue
            a = atrs[i] if atrs[i] > 0 else sd
            cost_scaled = base_cost * (0.5*a/sd) if sd > 0 else base_cost
            tag = 'energy_supply_shock' if vr >= 2.0 else 'energy_flat_breakout'
            ents.append(dict(sym=s, year=t.year, date=str(t)[:10], i=i, d=d, sd=sd, vr=vr,
                             slope=slope, cost=cost_scaled, atr=a, B=B, tag=tag))
    return ents

# ---------------------------------------------------------------------------
# Reporting (per-year + per-regime, never a lone bulk average)
# ---------------------------------------------------------------------------
def stats(rs):
    if not rs: return dict(n=0, ev=0.0, win=0.0, std=0.0, worst=0.0, rc=0.0)
    n = len(rs); ev = sum(r['R'] for r in rs)/n
    win = sum(1 for r in rs if r['R'] > 0)/n*100
    std = statistics.pstdev([r['R'] for r in rs]) if n > 1 else 0.0
    worst = min(r['R'] for r in rs)
    fwins = [r for r in rs if r['R'] > 0]
    runners = [r for r in rs if r['reason'] in ('runner_target', 'target4')]
    rc = 100*len(runners)/max(1, len(fwins))
    return dict(n=n, ev=ev, win=win, std=std, worst=worst, rc=rc)

def maxdd_equity(rs_dated, risk=0.0025):
    byday = collections.defaultdict(list)
    for r in rs_dated: byday[r['date']].append(r['R'])
    eq = 1.0; peak = 1.0; mdd = 0.0
    for day in sorted(byday):
        u = sum(byday[day])/len(byday[day])
        eq *= (1+u*risk); peak = max(peak, eq); mdd = max(mdd, (peak-eq)/peak)
    return mdd*100

def run_policy(ents, exitfn):
    out = []
    for e in ents:
        ex = exitfn(e)
        out.append(dict(sym=e['sym'], year=e['year'], date=e['date'], vr=e['vr'],
                        R=ex['R'], reason=ex['reason']))
    return out

def report(name, rows):
    train = [r for r in rows if r['year'] <= 2024]
    f25 = [r for r in rows if r['year'] == 2025]; f26 = [r for r in rows if r['year'] == 2026]
    fwd = [r for r in rows if r['year'] >= 2025]
    st = stats(train); s25 = stats(f25); s26 = stats(f26); sf = stats(fwd)
    mdd = maxdd_equity(fwd, 0.0025)
    print(f"{name:<20} TRAIN n{st['n']} ev{st['ev']:+.3f}/w{st['win']:.0f} | "
          f"2025 n{s25['n']} ev{s25['ev']:+.3f}/w{s25['win']:.0f} | 2026 n{s26['n']} ev{s26['ev']:+.3f}/w{s26['win']:.0f} | "
          f"FWD n{sf['n']} ev{sf['ev']:+.3f}/w{sf['win']:.0f} rc{sf['rc']:.0f}% std{sf['std']:.2f} mdd{mdd:.2f}%")
    return dict(name=name, train=st, y2025=s25, y2026=s26, fwd=sf, fwd_mdd=mdd)

def paired(rows_a, rows_b, label):
    """paired diff b-a on the SAME entries (same order). t-stat."""
    diffs = [rb['R']-ra['R'] for ra, rb in zip(rows_a, rows_b)]
    n = len(diffs); m = sum(diffs)/n if n else 0.0
    sd = statistics.pstdev(diffs) if n > 1 else 0.0
    t = m/(sd/(n**0.5)) if sd > 0 else 0.0
    print(f"   paired {label}: n{n} dR{m:+.4f} t{t:.2f}")
    return dict(n=n, dR=round(m, 4), t=round(t, 2))

def per_regime(rows, label):
    print(f"   per-vol-regime [{label}] (FWD 2025-26):")
    fwd = [r for r in rows if r['year'] >= 2025]
    for lab, lo, hi in (('LOW <1.35', 0, 1.35), ('MID 1.35-1.6', 1.35, 1.6), ('HI >=1.6', 1.6, 99)):
        rr = [r for r in fwd if lo <= r['vr'] < hi]; s = stats(rr)
        if s['n']: print(f"      {lab:>14}: n{s['n']:>3} ev{s['ev']:+.3f} w{s['win']:.0f}%")
