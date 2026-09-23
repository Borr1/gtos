"""STALE_maxbars_winsor.py — UNLEASH-wave extension of the stale-audit.
Quantifies two drags NOT covered by the prior KB7 pass:
  (e) maxbars=80 FORCE-CLOSE: does the 80-H4-bar time cap chop winning runners?
       Sweep maxbars {80,120,160,240,400} per carrier; report force-close frequency,
       what the force-closed trades become with more room, TRAIN<=2024 / FWD 2025-26 EV.
  (f) WINSOR [-1.3,+5]: re-confirm the right cap is inert AND test whether the LEFT
       cap [-1.3] is mis-stating risk (it can only ever be <= -1.0-cost on a full stop,
       so -1.3 floor is generous, not a drag — but a scratch/partial can't exceed it
       either; confirm no trade is clipped at -1.3 by the geometry, i.e. the winsor is
       a pure no-op for the carriers).
No lookahead (gates/exits index<=i decisions, forward-only labels). Per-year reported.
"""
import sys, statistics, collections, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs

FWD = {2025, 2026}
def NOWINS(r): return r                 # raw, for winsor-inertness test
def WINS(r): return max(-1.3, min(5.0, r))

def split(rows):
    allr = [r[1] for r in rows]; tr = [r[1] for r in rows if r[0] <= 2024]; fw = [r[1] for r in rows if r[0] in FWD]
    py = collections.defaultdict(list)
    for y, R in rows: py[y].append(R)
    return dict(n=len(allr), all_ev=round(sum(allr)/len(allr), 4) if allr else 0,
                train_n=len(tr), train_ev=round(sum(tr)/len(tr), 4) if tr else 0,
                fwd_n=len(fw), fwd_ev=round(sum(fw)/len(fw), 4) if fw else 0,
                per_year={y: (len(v), round(sum(v)/len(v), 3)) for y, v in sorted(py.items())})

# ---- metals_core & energy use exit_state_d (maxbars-controlled); crypto uses simulate ----
def metals_rows(maxbars=80, wins=WINS):
    rows = []; fc = 0; tot = 0; deltas = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i)
            ex = cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=maxbars)
            rows.append((t.year, wins(ex['R']))); tot += 1
            if ex['reason'] in ('market_close', 'win_partial', 'partial_flat'):
                fc += 1
    return rows, fc, tot

def energy_rows(maxbars=80, wins=WINS):
    rows = []; fc = 0; tot = 0
    for sym in cs.ENERGY:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            vr = cs.vol_ratio(atrs, i)
            ex = cs.exit_state_d(B, i, d, sd, vr, cost, maxbars=maxbars)
            rows.append((t.year, wins(ex['R']))); tot += 1
            if ex['reason'] in ('market_close', 'win_partial', 'partial_flat'): fc += 1
    return rows, fc, tot

def crypto_rows(maxbars=80, wins=WINS, ac_thr=0.15, donch=20, stop_atr=2.0, tgt_r=4.0):
    rows = []; fc = 0; tot = 0
    for sym in ('BTCUSD', 'DASHUSD'):
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 80: continue
        cost = w1.cost_for(sym)
        for i in range(60, len(B) - 1):
            a = atr14(B, i)
            if a <= 0: continue
            hh = max(B[k].h for k in range(i - donch, i)); ll = min(B[k].l for k in range(i - donch, i))
            d = 0
            if B[i].c > hh: d = 1
            elif B[i].c < ll: d = -1
            if d == 0: continue
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < ac_thr: continue
            sd = stop_atr * a
            # detect force-close: re-run with detail to see if it exited on maxbars
            from geometry_lib import simulate_detail
            R, xi = simulate_detail(B, i, d, stop_dist=sd, target_dist=tgt_r*sd, cost=cost, maxbars=maxbars)
            rows.append((T[i].year, wins(R))); tot += 1
            if xi - i >= maxbars: fc += 1
    return rows, fc, tot

CARRIERS = {'metals_core': metals_rows, 'energy': energy_rows, 'crypto': crypto_rows}

if __name__ == '__main__':
    report = {}
    print("=== (e) MAXBARS FORCE-CLOSE SWEEP (TRAIN<=2024 / FWD 2025-26) ===")
    for nm, fn in CARRIERS.items():
        report[nm] = {}
        print(f"\n{nm}:")
        print(f"  {'maxbars':>8} {'n':>5} {'force-close%':>12} {'ALL_EV':>8} {'TRAIN_EV':>9} {'FWD_EV':>8}")
        for mb in (80, 120, 160, 240, 400):
            rows, fc, tot = fn(maxbars=mb)
            s = split(rows)
            fcp = 100.0 * fc / tot if tot else 0
            report[nm][f'maxbars_{mb}'] = dict(n=s['n'], force_close_pct=round(fcp, 2),
                                               all_ev=s['all_ev'], train_ev=s['train_ev'],
                                               fwd_ev=s['fwd_ev'], per_year=s['per_year'])
            print(f"  {mb:>8} {s['n']:>5} {fcp:>11.2f}% {s['all_ev']:>+8.4f} {s['train_ev']:>+9.4f} {s['fwd_ev']:>+8.4f}")

    # ---- (f) WINSOR inertness: compare WINS vs NOWINS at deployed maxbars=80 ----
    print("\n=== (f) WINSOR [-1.3,+5] inertness (deployed maxbars=80) ===")
    report['winsor'] = {}
    for nm, fn in CARRIERS.items():
        rw, _, _ = fn(maxbars=80, wins=WINS)
        rr, _, _ = fn(maxbars=80, wins=NOWINS)
        raw_vals = [r[1] for r in rr]
        n_hi = sum(1 for v in raw_vals if v > 5.0)
        n_lo = sum(1 for v in raw_vals if v < -1.3)
        sw = split(rw); sr = split(rr)
        report['winsor'][nm] = dict(n=len(raw_vals), n_above_plus5=n_hi, n_below_minus13=n_lo,
                                    raw_max=round(max(raw_vals), 3), raw_min=round(min(raw_vals), 3),
                                    fwd_ev_wins=sw['fwd_ev'], fwd_ev_raw=sr['fwd_ev'])
        print(f"  {nm:12s} n={len(raw_vals):4d} raw_max {max(raw_vals):+.3f} raw_min {min(raw_vals):+.3f} "
              f"| clipped_above+5={n_hi} below-1.3={n_lo} | FWD wins {sw['fwd_ev']:+.4f} raw {sr['fwd_ev']:+.4f}")

    (HERE / 'STALE_maxbars_winsor_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote STALE_maxbars_winsor_RESULT.json")
