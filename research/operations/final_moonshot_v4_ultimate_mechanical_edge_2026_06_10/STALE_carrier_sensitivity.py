"""STALE_carrier_sensitivity.py — TRACK: audit static/conservative assumptions for drag.
Re-walks the 3 EV-carriers (metals_core, crypto, energy fvg) under parametric COST and GATE
variations to quantify the drag of each static choice and test loosening, forward-validated.
TRAIN<=2024 / FWD 2025-26 split, per-year, real geometry via geometry_lib + cs.exit_state_d.
No lookahead: gates are pure index<=i price functions; exits label forward only.
"""
import sys, statistics, collections, datetime, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs

def wins(r): return max(-1.3, min(5.0, r))
FWD = {2025, 2026}

def split(rows, key='R'):
    """rows: list of (year, R). returns dict with all/train/fwd (n, EV) + per-year."""
    allr = [r[1] for r in rows]
    tr = [r[1] for r in rows if r[0] <= 2024]
    fw = [r[1] for r in rows if r[0] in FWD]
    py = collections.defaultdict(list)
    for y, R in rows: py[y].append(R)
    return dict(n=len(allr), all_ev=round(sum(allr)/len(allr), 4) if allr else 0,
                train_n=len(tr), train_ev=round(sum(tr)/len(tr), 4) if tr else 0,
                fwd_n=len(fw), fwd_ev=round(sum(fw)/len(fw), 4) if fw else 0,
                per_year={y: (len(v), round(sum(v)/len(v), 3)) for y, v in sorted(py.items())})

# ---------- METALS_CORE H4 (gold fvg + ac60 gate + STATE_D exit on H4 base) ----------
# Use the H4-base STATE_D exit (no cascade LTF; the cost/gate effect is on the H4 entry decision,
# isolated from LTF fill availability so the experiment is clean and reproducible pre-2024).
def metals_core_rows(cost_mult=1.0, cost_abs=None, ac_thr=cs.AC_THR, gate_k=g.GATE_K, atr_floor=g.ATR_STOP_FLOOR):
    rows = []
    for sym in cs.METALS:
        T, B = w1.load(sym)
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        base_cost = w1.cost_for(sym)
        cost = cost_abs if cost_abs is not None else base_cost * cost_mult
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym, gate_k=gate_k):
            # re-apply ATR floor variation on the stop distance
            a = atrs[i]
            if atr_floor != g.ATR_STOP_FLOOR and a > 0:
                # recompute sd with new floor (sd was max(struct, floor*a))
                struct = sd if sd > g.ATR_STOP_FLOOR * a + 1e-9 else None
                if struct is None:  # was floored
                    sd = max(sd / g.ATR_STOP_FLOOR * atr_floor, atr_floor * a) if g.ATR_STOP_FLOOR > 0 else sd
                else:
                    sd = max(struct, atr_floor * a)
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < ac_thr: continue
            vr = cs.vol_ratio(atrs, i)
            R = cs.exit_state_d(B, i, d, sd, vr, cost)['R']
            rows.append((t.year, wins(R)))
    return rows

# ---------- CRYPTO (Donchian-20 breakout + ac60>=0.15 + 2*ATR stop + 4R target) ----------
def crypto_rows(cost_mult=1.0, cost_abs=None, ac_thr=0.15, donch=20, stop_atr=2.0, tgt_r=4.0):
    rows = []
    for sym in ('BTCUSD', 'DASHUSD'):
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 80: continue
        base_cost = w1.cost_for(sym)
        cost = cost_abs if cost_abs is not None else base_cost * cost_mult
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
            R = simulate(B, i, d, stop_dist=sd, target_dist=tgt_r * sd, cost=cost)
            rows.append((T[i].year, wins(R)))
    return rows

# ---------- ENERGY fvg STATE_D (precious-metals-style FVG on energy, STATE_D exit) ----------
def energy_rows(cost_mult=1.0, cost_abs=None, gate_k=g.GATE_K):
    rows = []
    for sym in cs.ENERGY:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        base_cost = w1.cost_for(sym)
        cost = cost_abs if cost_abs is not None else base_cost * cost_mult
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym, gate_k=gate_k):
            vr = cs.vol_ratio(atrs, i)
            R = cs.exit_state_d(B, i, d, sd, vr, cost)['R']
            rows.append((t.year, wins(R)))
    return rows

CARRIERS = {'metals_core': metals_core_rows, 'crypto': crypto_rows, 'energy': energy_rows}

if __name__ == '__main__':
    report = {}
    # ---- BASELINE (deployed cost map, deployed gates) ----
    print("=== BASELINE (deployed cost map + deployed gates) ===")
    base = {}
    for nm, fn in CARRIERS.items():
        base[nm] = split(fn())
        s = base[nm]
        print(f"  {nm:12s} n={s['n']:4d} ALL {s['all_ev']:+.4f} | TRAIN {s['train_ev']:+.4f}(n{s['train_n']}) FWD {s['fwd_ev']:+.4f}(n{s['fwd_n']})")
    report['baseline'] = base

    # ---- (a) COST SENSITIVITY ----
    print("\n=== (a) COST SENSITIVITY (per-trade EV vs cost assumption) ===")
    report['cost_sensitivity'] = {}
    cost_scenarios = {
        'deployed_map': dict(),
        'cost_x0.5': dict(cost_mult=0.5),
        'cost_x1.5': dict(cost_mult=1.5),
        'cost_x2.0': dict(cost_mult=2.0),
        'old_017_proxy': dict(cost_abs=0.17),
        'zero_cost': dict(cost_abs=0.0),
    }
    for nm, fn in CARRIERS.items():
        report['cost_sensitivity'][nm] = {}
        line = f"  {nm:12s}"
        for sc, kw in cost_scenarios.items():
            try: s = split(fn(**kw))
            except TypeError: s = split(fn(**{k: v for k, v in kw.items() if k in fn.__code__.co_varnames}))
            report['cost_sensitivity'][nm][sc] = dict(all_ev=s['all_ev'], fwd_ev=s['fwd_ev'], n=s['n'])
        b = report['cost_sensitivity'][nm]
        print(f"  {nm:12s} deployed FWD {b['deployed_map']['fwd_ev']:+.4f} | x0.5 {b['cost_x0.5']['fwd_ev']:+.4f} | "
              f"x1.5 {b['cost_x1.5']['fwd_ev']:+.4f} | x2 {b['cost_x2.0']['fwd_ev']:+.4f} | "
              f"0.17proxy {b['old_017_proxy']['fwd_ev']:+.4f} | zero {b['zero_cost']['fwd_ev']:+.4f}")

    (HERE / 'STALE_carrier_sensitivity_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote STALE_carrier_sensitivity_RESULT.json")
