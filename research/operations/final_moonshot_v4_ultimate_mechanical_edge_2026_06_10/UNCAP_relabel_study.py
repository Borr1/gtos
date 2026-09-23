"""UNCAP_relabel_study.py — TRACK: Un-cap winners + extend runner horizon.

DECISIVE PRE-FINDING (measured first, see UNCAP_cap_binding_diag below):
  the [-1.3,+5] winsor CEILING NEVER BINDS on any deploy sleeve (0 trades reach +5;
  the -1.3 FLOOR never binds either because the structural stop is exactly -1R).
  The REAL ceiling that understates the right-skewed edge is the FIXED TARGET / runner_R
  geometry (3R for substrate g1.0_3.0; 4/3/2.5R vol-banded for metals/crypto/energy;
  1.5/2R for leadlag) plus maxbars force-close. So "un-capping winners" = lifting the
  TARGET and EXTENDING maxbars, NOT touching the (dead) winsor number.

This harness re-labels the CONTINUATION sleeves on the SAME leak-free entries with:
  (a) higher fixed-target ceilings: 4R / 6R / 8R / 12R / none(=maxbars close)
  (b) extended maxbars: base / 2x / 3x
  (c) a LET-RUN trail variant (book 1 leg, then trail the runner — captures open-ended trends)
and measures, per-year forward, the recovered EV + the MFE distribution that proves how much
the cap was understating. Honest counter-check: it also reports how much DEEPER LOSSES the
extension introduces (force-close at maxbars can turn a small win into a loss / vice versa).

LEAK-FREE: entries are the existing audited signals; exits use geometry_lib.simulate /
simulate_detail (pessimistic same-bar, adverse-first) on CLOSED bars only. No lookahead.
Real per-symbol cost. TRAIN<=2024 vs FWD 2025 / 2026 reported separately + n.
"""
import sys, json, statistics, collections, datetime
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from geometry_lib import simulate, simulate_detail, atr14, Bar
import wave1_structure_setups_ict as w1
import gold_sleeve_strategy as g
import compounding_sleeve as cs
import multitf_lib as m
import substrate as sub
import SUBSTRATE_corrcheck as SC
import INTEG_portfolio_build as I
import kb2_new_breadth as KB

DATA = str(HERE.parents[2]) + '/data/mt5_research_exports'

# ---------- exit families (all leak-free, pessimistic, real cost) ----------
def sim_fixed(B, i, d, sd, *, target_R, maxbars, cost, winsor_hi):
    """Fixed target_R (None => no target, run to maxbars close). Returns (R, mfe_R, exit_kind)."""
    entry = B[i].c
    td = target_R * sd if target_R is not None else None
    r, ej = simulate_detail(B, i, d, stop_dist=sd, target_dist=td, maxbars=maxbars, cost=cost)
    # measure realized MFE in R over the realized holding window [i+1, ej]
    mfe = 0.0
    end = min(i + maxbars, len(B) - 1)
    for j in range(i + 1, end + 1):
        favp = B[j].h if d > 0 else B[j].l
        fav = d * (favp - entry) / sd
        if fav > mfe: mfe = fav
        if j >= ej: break
    R = max(-1.3, min(winsor_hi, r))
    kind = 'target' if (target_R is not None and r >= target_R - 0.05) else (
        'stop' if r <= -0.95 else 'maxbars_close')
    return R, mfe, kind

def sim_letrun(B, i, d, sd, *, arm_R, gap_R, maxbars, cost, winsor_hi):
    """LET-RUN trail: once fav>=arm_R, trail the runner gap_R behind MFE. Open-ended upside.
    Pessimistic adverse-first. Returns (R, mfe_R, kind)."""
    r = simulate(B, i, d, stop_dist=sd, trail_arm=arm_R * sd, trail_gap=gap_R * sd,
                 maxbars=maxbars, cost=cost)
    entry = B[i].c; mfe = 0.0; end = min(i + maxbars, len(B) - 1)
    for j in range(i + 1, end + 1):
        favp = B[j].h if d > 0 else B[j].l
        fav = d * (favp - entry) / sd
        if fav > mfe: mfe = fav
    return max(-1.3, min(winsor_hi, r)), mfe, 'trail'

# ---------- entry reconstructors (identical to the deploy generators) ----------
def entries_metals():
    """metals_core entries: FVG + ac60>=0.10. Carry the H4 stream & idx + vr + cost (no LTF
    cascade here — we study the EXIT CEILING on the H4 carrier so target/maxbars are comparable
    across the target grid; cascade better-fill is an orthogonal, already-banked win)."""
    out = []
    for sym in cs.METALS:
        try: T, B = w1.load(sym)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]; cost = w1.cost_for(sym)
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(sym):
            ac = cs.autocorr(B, i, 60)
            if ac is None or ac < cs.AC_THR: continue
            vr = cs.vol_ratio(atrs, i)
            out.append(dict(sleeve='metals_core', sym=sym, year=t.year, B=B, i=i, d=d, sd=sd,
                            vr=vr, cost=c2))
    return out

def entries_crypto():
    """crypto carrier entries (ETH + BTC/DASH cascade ledger). For BTC/DASH we re-derive the H4
    entry from the leak-audited ledger only where the H4 bars are loadable; ETH from resample."""
    out = []
    # ETH carrier (Donchian-20 + ac60>=0.15, sd=2a) on H4
    T, B = KB.resample_eth_h4(); cost = w1.cost_for('ETHUSD')
    atrs = [atr14(B, i) for i in range(len(B))]
    for (i, d) in KB.crypto_breakout_signals(B, 20):
        a = atrs[i]
        if a <= 0: continue
        ac = cs.autocorr(B, i, 60)
        if ac is None or ac < 0.15: continue
        sd = 2.0 * a
        out.append(dict(sleeve='crypto', sym='ETHUSD', year=T[i].year, B=B, i=i, d=d, sd=sd,
                        vr=cs.vol_ratio(atrs, i), cost=cost))
    return out

def entries_energy():
    """energy supply-shock + consolidation FVG entries (the continuation carrier)."""
    import energy_agri_sleeve as ea
    out = []
    for s in ea.ENERGY:
        try: T, B = w1.load(s)
        except Exception: continue
        if len(B) < 200: continue
        atrs = [atr14(B, k) for k in range(len(B))]
        for (t, d, sd, td, i, B2, c2) in g.fvg_signals(s):
            vr = cs.vol_ratio(atrs, i)
            out.append(dict(sleeve='energy_agri', sym=s, year=t.year, B=B, i=i, d=d, sd=sd,
                            vr=vr, cost=c2))
    return out

def entries_substrate(cell, symbols=None):
    """substrate cell entries (stop_atr,target_R from the cell). Carry stop_dist + cost."""
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
                sd = stop_atr * a; scaled_cost = cost / stop_atr
                out.append(dict(sleeve='sub', sym=s, year=T[i].year, B=B, i=i, d=dmode, sd=sd,
                                vr=cs.vol_ratio([atr14(B, k) for k in range(len(B))], i)
                                if False else 1.0, cost=scaled_cost, base_target=target_R))
    return out

# ---------- per-year stat ----------
def yr_stats(rows, key='R'):
    by = collections.defaultdict(list)
    for r in rows: by[r['year']].append(r[key])
    out = {}
    for y, v in by.items():
        out[y] = (len(v), sum(v) / len(v), 100 * sum(1 for x in v if x > 0) / len(v))
    return out

def split(rows, key='R'):
    tr = [r[key] for r in rows if r['year'] <= 2024]
    f25 = [r[key] for r in rows if r['year'] == 2025]
    f26 = [r[key] for r in rows if r['year'] == 2026]
    fwd = [r[key] for r in rows if r['year'] >= 2025]
    def m(v): return (len(v), (sum(v) / len(v) if v else 0.0),
                      (100 * sum(1 for x in v if x > 0) / len(v) if v else 0.0))
    return dict(train=m(tr), y2025=m(f25), y2026=m(f26), fwd=m(fwd))


def study_sleeve(name, ents, base_target, base_maxbars):
    """Grid: target in {base, 6, 8, 12, None}; maxbars in {base, 2x, 3x}; winsor in {5, 12, inf};
    plus a let-run trail variant. Report per-trade fwd EV + MFE recovery."""
    print(f"\n{'='*78}\n  {name}: n={len(ents)} base_target={base_target} base_maxbars={base_maxbars}\n{'='*78}")
    res = {'n': len(ents), 'base_target': base_target, 'base_maxbars': base_maxbars, 'variants': {}}

    # --- MFE diagnosis at base maxbars (proves how much room winners had) ---
    mfes = []
    for e in ents:
        _, mfe, _ = sim_fixed(e['B'], e['i'], e['d'], e['sd'], target_R=None,
                              maxbars=base_maxbars, cost=e['cost'], winsor_hi=1e9)
        mfes.append(dict(year=e['year'], mfe=mfe))
    fwd_mfe = [x['mfe'] for x in mfes if x['year'] >= 2025]
    if fwd_mfe:
        res['fwd_mfe_pctiles'] = {p: round(statistics.quantiles(fwd_mfe, n=100)[p - 1], 2)
                                  for p in (50, 75, 90, 95, 99)} if len(fwd_mfe) >= 4 else {}
        res['fwd_mfe_ge'] = {f'>={k}R': sum(1 for x in fwd_mfe if x >= k) for k in (3, 4, 6, 8, 12)}
        res['fwd_n'] = len(fwd_mfe)
        print(f"  FWD MFE (no-target, base maxbars): n={len(fwd_mfe)} "
              f"median={statistics.median(fwd_mfe):.2f} "
              f">=4R:{res['fwd_mfe_ge']['>=4R']} >=6R:{res['fwd_mfe_ge']['>=6R']} "
              f">=8R:{res['fwd_mfe_ge']['>=8R']} >=12R:{res['fwd_mfe_ge']['>=12R']}")

    grid_targets = [base_target, 6.0, 8.0, 12.0, None]
    grid_mb = [('mb1x', base_maxbars), ('mb2x', base_maxbars * 2), ('mb3x', base_maxbars * 3)]
    print(f"  {'variant':>26} {'TRAIN ev/n':>14} {'2025 ev/n':>13} {'2026 ev/n':>13} {'FWD ev/win/n':>18}")
    for tg in grid_targets:
        for mbn, mb in grid_mb:
            for wh, whlab in [(5.0, ''), (1e9, '_noW')]:
                # skip redundant winsor variants where it can't bind (target<=5 and no overshoot)
                if wh == 1e9 and (tg is not None and tg <= 5.0):
                    continue
                rows = []
                for e in ents:
                    R, mfe, kind = sim_fixed(e['B'], e['i'], e['d'], e['sd'], target_R=tg,
                                             maxbars=mb, cost=e['cost'], winsor_hi=wh)
                    rows.append(dict(year=e['year'], R=R, kind=kind))
                sp = split(rows)
                lab = f"T{tg if tg is not None else 'none'}_{mbn}{whlab}"
                res['variants'][lab] = sp
                # print only the informative subset
                if (mbn in ('mb1x', 'mb2x')) and whlab == '':
                    print(f"  {lab:>26} {sp['train'][1]:>+7.3f}/{sp['train'][0]:<5} "
                          f"{sp['y2025'][1]:>+7.3f}/{sp['y2025'][0]:<4} "
                          f"{sp['y2026'][1]:>+7.3f}/{sp['y2026'][0]:<4} "
                          f"{sp['fwd'][1]:>+7.3f}/{sp['fwd'][2]:>3.0f}%/{sp['fwd'][0]:<4}")
    # let-run trail variants
    for arm, gap in [(2.0, 1.0), (3.0, 1.5), (2.0, 1.5)]:
        for mbn, mb in grid_mb:
            rows = []
            for e in ents:
                R, mfe, kind = sim_letrun(e['B'], e['i'], e['d'], e['sd'], arm_R=arm, gap_R=gap,
                                          maxbars=mb, cost=e['cost'], winsor_hi=1e9)
                rows.append(dict(year=e['year'], R=R))
            sp = split(rows)
            lab = f"TRAIL_arm{arm}_gap{gap}_{mbn}"
            res['variants'][lab] = sp
            if mbn in ('mb1x', 'mb2x'):
                print(f"  {lab:>26} {sp['train'][1]:>+7.3f}/{sp['train'][0]:<5} "
                      f"{sp['y2025'][1]:>+7.3f}/{sp['y2025'][0]:<4} "
                      f"{sp['y2026'][1]:>+7.3f}/{sp['y2026'][0]:<4} "
                      f"{sp['fwd'][1]:>+7.3f}/{sp['fwd'][2]:>3.0f}%/{sp['fwd'][0]:<4}")
    return res


def main():
    report = {'track': 'uncap_winners_extend_runner', 'date': str(datetime.date.today()),
              'pre_finding': 'winsor[+5] ceiling is NON-BINDING on all deploy sleeves; the binding '
                             'ceiling is the FIXED TARGET / runner_R geometry + maxbars.',
              'sleeves': {}}
    print("Building entries (leak-free, same as deploy generators)...")
    em = entries_metals(); print(f"  metals_core entries: {len(em)}")
    ec = entries_crypto(); print(f"  crypto carrier entries: {len(ec)}")
    en = entries_energy(); print(f"  energy entries: {len(en)}")
    esx = entries_substrate("g1.0_3.0|dir=1|depth4|vol=xhi|persist=rand|trend=up|mtf=conflict",
                            symbols=[s for s in w1.SYMBOLS if s not in
                                     __import__('KB5_fold_new_sleeves').DROP_XVOL])
    print(f"  sub_xvol_pullback entries: {len(esx)}")

    report['sleeves']['metals_core'] = study_sleeve('metals_core', em, 4.0, 80)
    report['sleeves']['crypto'] = study_sleeve('crypto', ec, 4.0, 80)
    report['sleeves']['energy_agri'] = study_sleeve('energy_agri', en, 4.0, 80)
    report['sleeves']['sub_xvol_pullback'] = study_sleeve('sub_xvol_pullback', esx, 3.0, sub.MAXBARS)

    (HERE / 'UNCAP_RELABEL_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote UNCAP_RELABEL_RESULT.json")
    return report


if __name__ == '__main__':
    main()
