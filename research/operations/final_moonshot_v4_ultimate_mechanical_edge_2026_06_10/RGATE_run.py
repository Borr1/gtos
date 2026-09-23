"""RGATE_run.py — run the substrate regime-gate on the existing CORE book and
compare UNGATED vs GATED on: per-sleeve EV (train/fwd/per-year), combined daily
stats, and the LOCKED W2 challenge-pass MC + 1.5x stress + 2-account joint MC.

GATED book = substrate-gated {metals_core, crypto, energy_agri} + UNGATED breadth
({metals_softband, metals_ob_micro, idxrev, fx_jpy, fx_jpy_ny} unchanged). The gate
only decides take/skip + size on the 3 validated CORE sleeves (the brief's targets).

Two gate variants:
  - minboth   : take if min(train_meanR, fwd_meanR) > 0 ; size by that min (brief's literal rule).
  - trainonly : forward-honest — take/size by TRAIN-side meanR only (no forward info in the gate).

We reuse INTEG_portfolio_build_w2 verbatim for build_matrix / mc_series / corr / joint_pass_mc.
"""
import sys, json, collections, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))

import RGATE_substrate_gate as RG
import INTEG_portfolio_build_w2 as W2
import substrate as sub
import json as _json

CORE = ['metals_core', 'crypto', 'energy_agri']
GRID = (0.005, 0.0075, 0.01, 0.015, 0.02)

def sleeve_stats(rows, use_sized=True):
    """EV stats on a sleeve row list. Counts only TAKEN trades (R_sized!=0 OR gate_take)."""
    def val(r): return r['R_sized'] if use_sized else r['R']
    taken = [r for r in rows if r.get('gate_take', True)]
    fwd = [val(r) for r in taken if r['year'] >= 2025]
    tr  = [val(r) for r in taken if r['year'] < 2025]
    by = collections.defaultdict(list)
    for r in taken: by[r['year']].append(val(r))
    per_year = {y: (len(by[y]), round(statistics.fmean(by[y]), 3)) for y in sorted(by)}
    return dict(n_taken=len(taken), n_all=len(rows),
                train=(len(tr), round(statistics.fmean(tr), 3) if tr else 0.0),
                fwd=(len(fwd), round(statistics.fmean(fwd), 3) if fwd else 0.0),
                fwd_per_year=round(len(fwd)/1.5, 1), per_year=per_year)

def build_book(cache, gated_core):
    """Assemble a streams dict in W2 shape from gated CORE + ungated breadth."""
    streams = {}
    for sl in W2.SLEEVES:
        if sl in CORE:
            streams[sl] = gated_core[sl]
        else:
            rows = [dict(r) for r in cache[sl]]
            for r in rows:
                r['R_sized'] = r['R'] * r.get('intra_size', 1.0)
            streams[sl] = rows
    return streams

def mc_block(streams, label, report):
    days, M = W2.build_matrix(streams)
    fwd_mask = [d.year >= 2025 for d in days]
    M_fwd = [row for row, f in zip(M, fwd_mask) if f]
    comb = [sum(r) for r in M]; comb_fwd = [sum(r) for r in M_fwd]
    comb_stress = [(v*1.5 if v < 0 else v) for v in comb]
    out = {'n_days': len(comb), 'n_days_fwd': len(comb_fwd),
           'mean_unitR': round(statistics.fmean(comb), 4),
           'mean_unitR_fwd': round(statistics.fmean(comb_fwd), 4) if comb_fwd else None,
           'worst_day': round(min(comb), 4), 'best_day': round(max(comb), 4),
           'std': round(statistics.pstdev(comb), 4),
           'win_days_pct': round(100*sum(1 for x in comb if x > 0)/len(comb), 1)}
    mc_all = {}; mc_fwd = {}; mc_str = {}
    for risk in GRID:
        mc_all[f"{risk*100:.2f}%"] = W2.mc_series(comb, risk, seed_base=1)
        mc_fwd[f"{risk*100:.2f}%"] = W2.mc_series(comb_fwd, risk, seed_base=777) if comb_fwd else None
        mc_str[f"{risk*100:.2f}%"] = W2.mc_series(comb_stress, risk, seed_base=999)
    out['mc_all'] = mc_all; out['mc_fwd'] = mc_fwd; out['mc_stress15'] = mc_str
    # 2-account joint (balanced 0.75/0.75 + conservative 0.5/0.5)
    idx = {s: i for i, s in enumerate(W2.SLEEVES)}
    full = {idx[s]: 1.0 for s in W2.SLEEVES}
    M_stress = [[(v*1.5 if v < 0 else v) for v in row] for row in M]
    two = {}
    for (a, b, lab) in [(0.0075, 0.0075, 'balanced_0.75_0.75'), (0.005, 0.005, 'conservative_0.50_0.50')]:
        base = W2.joint_pass_mc(M, (full, a), (full, b), seed_base=7)
        fwd  = W2.joint_pass_mc(M_fwd, (full, a), (full, b), seed_base=33) if M_fwd else None
        strs = W2.joint_pass_mc(M_stress, (full, a), (full, b), seed_base=44)
        two[lab] = dict(base_p_both=base['p_pass_both'],
                        fwd_p_both=(fwd['p_pass_both'] if fwd else None),
                        stress15_p_both=strs['p_pass_both'])
    out['two_account'] = two
    report[label] = out
    return out

def print_mc(label, blk):
    print(f"\n=== {label} ===  days={blk['n_days']} fwd={blk['n_days_fwd']} "
          f"mean={blk['mean_unitR']:+.4f} fwd={blk['mean_unitR_fwd']} worst={blk['worst_day']:+.3f}")
    print(f"  {'risk':>6} {'P(pass)ALL':>11} {'P(pass)FWD':>11} {'STRESS1.5x':>11} {'med_d':>6}")
    for risk in GRID:
        k = f"{risk*100:.2f}%"
        a = blk['mc_all'][k]; f = blk['mc_fwd'][k]; s = blk['mc_stress15'][k]
        print(f"  {risk*100:>5.2f}% {a['p_pass']:>11.2%} {(f['p_pass'] if f else 0):>11.2%} "
              f"{s['p_pass']:>11.2%} {str(a['med_days_pass']):>6}")
    for lab, t in blk['two_account'].items():
        print(f"  2acct {lab}: P(both)={t['base_p_both']:.2%} FWD={t['fwd_p_both']} STRESS={t['stress15_p_both']:.2%}")

def main(scale=0.5, cap=2.0):
    print("loading W3 cache + substrate map + id maps...", flush=True)
    cache = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    cmap = _json.load(open(HERE / 'SUBSTRATE_MAP.json'))['cells']
    id_map, eth_map = RG.build_id_maps()
    print(f"  id_map keys={len(id_map)} eth_map keys={len(eth_map)}", flush=True)

    report = {'meta': {'core_sleeves': CORE, 'gate_geom': RG.GATE_GEOM,
                       'size_scale': scale, 'size_cap': cap,
                       'rule_minboth': 'take if min(train,fwd) meanR>0; size=min/scale capped',
                       'rule_trainonly': 'take if train meanR>0; size=train/scale (no fwd info)'}}

    # ---------- UNGATED baseline (rebuild book from cache as-is) ----------
    ungated_core = {}
    for sl in CORE:
        rows = [dict(r) for r in cache[sl]]
        for r in rows:
            r['R_sized'] = r['R'] * r.get('intra_size', 1.0); r['gate_take'] = True
        ungated_core[sl] = rows
    streams_ung = build_book(cache, ungated_core)
    print("\n##### UNGATED (existing CORE book) #####")
    for sl in CORE:
        s = sleeve_stats(ungated_core[sl])
        print(f"  [{sl}] n={s['n_taken']} train={s['train']} fwd={s['fwd']} ~{s['fwd_per_year']}/yr")
        report.setdefault('per_sleeve', {}).setdefault('ungated', {})[sl] = s
    ublk = mc_block(streams_ung, 'ungated', report); print_mc('UNGATED', ublk)

    # ---------- GATED variants ----------
    for mode in ('minboth', 'trainonly'):
        gated_core = {}
        print(f"\n##### GATED ({mode}) scale={scale} cap={cap} #####")
        for sl in CORE:
            gr = RG.gate_cache_rows(cache[sl], sl, cmap, id_map, eth_map,
                                    size=True, scale=scale, cap=cap, mode=mode)
            gated_core[sl] = gr
            n_take = sum(1 for r in gr if r['gate_take'])
            s = sleeve_stats(gr)
            print(f"  [{sl}] taken {n_take}/{len(gr)}  train={s['train']} fwd={s['fwd']} ~{s['fwd_per_year']}/yr")
            report.setdefault('per_sleeve', {}).setdefault(mode, {})[sl] = dict(
                s, n_taken=n_take, n_total=len(gr))
        streams_g = build_book(cache, gated_core)
        gblk = mc_block(streams_g, f'gated_{mode}', report); print_mc(f'GATED ({mode})', gblk)

    (HERE / 'RGATE_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote RGATE_RESULT.json")
    return report

if __name__ == '__main__':
    import sys
    sc = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    cp = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    main(scale=sc, cap=cp)
