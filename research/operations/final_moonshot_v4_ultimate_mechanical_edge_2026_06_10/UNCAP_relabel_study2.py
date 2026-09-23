"""UNCAP_relabel_study2.py — extend the un-cap study to the remaining forward sleeves:
  subh4_ll_fx (M15 USDJPY->EURJPY london-open momentum; stop=0.5*ATR so R-unit is tight),
  sub_mid_dn_revert (substrate NY mid-vol dn-revert long, g1.0_3.0 -> 3R target),
  leadlag_core (H4 index/jpy momentum+reversion; stop=ATR, tmult target).

Re-target the SAME entries with higher target multiples + extended maxbars + a let-run trail,
report per-year forward. Leak-free (geometry_lib pessimistic), real cost.
"""
import sys, json, statistics, collections, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, simulate_detail, atr14
import wave1_structure_setups_ict as w1
import compounding_sleeve as cs
import substrate as sub
import SUBSTRATE_corrcheck as SC
import KB5_leadlag_subh4 as SH

def split(rows, key='R'):
    def m(v): return (len(v), (sum(v) / len(v) if v else 0.0),
                      (100 * sum(1 for x in v if x > 0) / len(v) if v else 0.0))
    return dict(train=m([r[key] for r in rows if r['year'] <= 2024]),
                y2025=m([r[key] for r in rows if r['year'] == 2025]),
                y2026=m([r[key] for r in rows if r['year'] == 2026]),
                fwd=m([r[key] for r in rows if r['year'] >= 2025]))

def pline(lab, sp):
    print(f"  {lab:>26} {sp['train'][1]:>+7.3f}/{sp['train'][0]:<5} "
          f"{sp['y2025'][1]:>+7.3f}/{sp['y2025'][0]:<4} "
          f"{sp['y2026'][1]:>+7.3f}/{sp['y2026'][0]:<4} "
          f"{sp['fwd'][1]:>+7.3f}/{sp['fwd'][2]:>3.0f}%/{sp['fwd'][0]:<4}")

# ---------- subh4: re-mine with custom target / maxbars / trail ----------
def subh4_entries():
    """Reconstruct the deploy subh4 entries (USDJPY->EURJPY london_open, look16,z2.5, momentum).
    Returns list of (fb, i, d, stop, cost, year). One per deduped entry timestamp."""
    L, F, sgn, look, z, sess = "USDJPY", "EURJPY", +1, 16, 2.5, "london_open"
    sig = SH.leader_signal(L, look)
    pf = SH.load_m15(F); fb = pf["bars"]; ftmap = pf["tmap"]; fatrs = pf["atrs"]
    cost = SH.cost_for(F)
    ents = []; last_idx = -10**9; seen = set()
    for ts, zz in sig.items():
        if abs(zz) < z: continue
        if not SH._session_ok(ts, sess): continue
        i = ftmap.get(ts)
        if i is None or i < 14 or i >= len(fb) - 2: continue
        if i - last_idx < 4: continue
        a = fatrs[i]
        if a <= 0: continue
        base = (1 if zz > 0 else -1) * sgn
        d = base  # momentum
        if ts in seen: continue
        seen.add(ts)
        ents.append(dict(fb=fb, i=i, d=d, stop=0.5 * a, cost=cost, year=ts.year))
        last_idx = i
    return ents

def relabel_fixed(ents, tmult, maxbars, winsor_hi=1e9):
    rows = []
    for e in ents:
        bars = e.get('fb', e.get('B'))
        r = simulate(bars, e['i'], e['d'], stop_dist=e['stop'],
                     target_dist=tmult * e['stop'], maxbars=maxbars, cost=e['cost'])
        rows.append(dict(year=e['year'], R=max(-1.3, min(winsor_hi, r))))
    return rows

def relabel_trail(ents, arm, gap, maxbars, winsor_hi=1e9):
    rows = []
    for e in ents:
        bars = e.get('fb', e.get('B'))
        r = simulate(bars, e['i'], e['d'], stop_dist=e['stop'],
                     trail_arm=arm * e['stop'], trail_gap=gap * e['stop'],
                     maxbars=maxbars, cost=e['cost'])
        rows.append(dict(year=e['year'], R=max(-1.3, min(winsor_hi, r))))
    return rows

def mfe_diag(ents, maxbars):
    fwd = []
    for e in ents:
        if e['year'] < 2025: continue
        bars = e.get('fb', e.get('B'))
        entry = bars[e['i']].c; mfe = 0.0
        end = min(e['i'] + maxbars, len(bars) - 1)
        for j in range(e['i'] + 1, end + 1):
            favp = bars[j].h if e['d'] > 0 else bars[j].l
            fav = e['d'] * (favp - entry) / e['stop']
            if fav > mfe: mfe = fav
        fwd.append(mfe)
    return fwd

# ---------- substrate dn_revert re-target ----------
def sub_entries(cell, symbols=None):
    geom, dmode, conds = SC.parse_cell(cell)
    stop_atr, target_R = geom
    syms = symbols or w1.SYMBOLS
    out = []
    for s in syms:
        built = sub.build_states(s)
        if built is None: continue
        T, B, A, states = built
        cost = w1.cost_for(s); n = len(B)
        for i in range(sub.WARMUP, n - sub.MAXBARS - 1):
            st = states[i]
            if st is None: continue
            co = sub.cell_coords(st)
            if all(co.get(dd) == bb for dd, bb in conds.items()):
                a = A[i]
                if a <= 0: continue
                out.append(dict(B=B, i=i, d=dmode, stop=stop_atr * a, cost=cost / stop_atr,
                                year=T[i].year))
    return out


def study(name, ents, base_tmult, base_maxbars, tmults, trail_set):
    print(f"\n{'='*78}\n  {name}: n={len(ents)} base_tmult={base_tmult} base_maxbars={base_maxbars}\n{'='*78}")
    res = {'n': len(ents), 'variants': {}}
    fwd_mfe = mfe_diag(ents, base_maxbars)
    if fwd_mfe:
        ge = {f'>={k}R': sum(1 for x in fwd_mfe if x >= k) for k in (3, 4, 6, 8, 12)}
        res['fwd_mfe_ge'] = ge; res['fwd_mfe_median'] = round(statistics.median(fwd_mfe), 2)
        print(f"  FWD MFE: n={len(fwd_mfe)} median={statistics.median(fwd_mfe):.2f} "
              f">=4R:{ge['>=4R']} >=6R:{ge['>=6R']} >=8R:{ge['>=8R']} >=12R:{ge['>=12R']}")
    print(f"  {'variant':>26} {'TRAIN ev/n':>14} {'2025 ev/n':>13} {'2026 ev/n':>13} {'FWD ev/win/n':>18}")
    for tm in tmults:
        for mbf, mbn in [(1, 'mb1x'), (2, 'mb2x')]:
            sp = split(relabel_fixed(ents, tm, base_maxbars * mbf))
            res['variants'][f"T{tm}_{mbn}"] = sp
            pline(f"T{tm}_{mbn}", sp)
    for (arm, gap) in trail_set:
        for mbf, mbn in [(1, 'mb1x'), (2, 'mb2x')]:
            sp = split(relabel_trail(ents, arm, gap, base_maxbars * mbf))
            res['variants'][f"TRAIL_a{arm}_g{gap}_{mbn}"] = sp
            pline(f"TRAIL_a{arm}_g{gap}_{mbn}", sp)
    return res


def main():
    report = {'track': 'uncap_winners_study2', 'sleeves': {}}
    print("Building subh4 entries...")
    se = subh4_entries(); print(f"  subh4 entries: {len(se)}")
    # subh4 R-unit = 0.5*ATR (stop). deploy targets T2.0/T1.5 => 4R/3R-units. test up to 12R-units.
    report['sleeves']['subh4_ll_fx'] = study('subh4_ll_fx', se, 4.0, 64,
                                             [3.0, 4.0, 6.0, 8.0, 12.0], [(2, 1), (4, 2), (6, 3)])

    print("\nBuilding sub_mid_dn_revert entries...")
    me = sub_entries("g1.0_3.0|dir=1|depth7|vol=mid|trend=dn|mtf=neutral|rngpos=mid|comp=norm|persist=revert|session=ny")
    print(f"  sub_mid_dn_revert entries: {len(me)}")
    report['sleeves']['sub_mid_dn_revert'] = study('sub_mid_dn_revert', me, 3.0, sub.MAXBARS,
                                                  [3.0, 6.0, 8.0, 12.0], [(2, 1), (3, 1.5)])

    (HERE / 'UNCAP_RELABEL_RESULT2.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote UNCAP_RELABEL_RESULT2.json")


if __name__ == '__main__':
    main()
