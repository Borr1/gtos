"""RGATE_matched.py — fair book-level test of the substrate gate at MATCHED gross
exposure (the regime-overlay doctrine: a selectivity overlay must be judged at equal
deployed risk, else the frequency cut alone starves the path and crushes MC).

For each book variant we:
  1) build the combined daily unit-R series (W2.build_matrix on the variant streams),
  2) compute GROSS = sum_t sum_sleeve |contribution| (total deployed risk),
  3) renormalise the variant's series so GROSS == ungated GROSS (matched exposure),
  4) run the LOCKED W2 MC (P(pass)/stress/worst-day/breach) on the matched series,
  5) also report EV-per-unit-gross (efficiency) and forward per-year.

Variants:
  ungated                : existing CORE book
  gate_all_<mode>        : substrate-gate all 3 CORE sleeves
  gate_me_<mode>         : substrate-gate metals+energy only (crypto ungated) — the
                           EV table's winning config (crypto's own edge beats the gate)
"""
import sys, json, collections, statistics, pickle
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import RGATE_substrate_gate as RG
import INTEG_portfolio_build_w2 as W2

CORE = ['metals_core', 'crypto', 'energy_agri']
GRID = (0.005, 0.0075, 0.01, 0.015, 0.02)

def ungated_core(cache):
    d = {}
    for sl in CORE:
        rows = [dict(r) for r in cache[sl]]
        for r in rows:
            r['R_sized'] = r['R'] * r.get('intra_size', 1.0); r['gate_take'] = True
        d[sl] = rows
    return d

def build_streams(cache, core):
    s = {}
    for sl in W2.SLEEVES:
        if sl in core:
            s[sl] = core[sl]
        else:
            rows = [dict(r) for r in cache[sl]]
            for r in rows:
                r['R_sized'] = r['R'] * r.get('intra_size', 1.0)
            s[sl] = rows
    return s

def daily_series(streams):
    days, M = W2.build_matrix(streams)
    gross = sum(abs(M[di][si]) for di in range(len(days)) for si in range(len(W2.SLEEVES)))
    comb = [sum(r) for r in M]
    fwd = [(d.year >= 2025) for d in days]
    comb_fwd = [c for c, f in zip(comb, fwd) if f]
    return days, comb, comb_fwd, gross, M

def mc_on(comb, comb_fwd, scale=1.0):
    cs = [v*scale for v in comb]; csf = [v*scale for v in comb_fwd]
    css = [(v*1.5 if v < 0 else v) for v in cs]
    out = {'mean': round(statistics.fmean(cs), 4),
           'mean_fwd': round(statistics.fmean(csf), 4) if csf else None,
           'worst': round(min(cs), 4), 'std': round(statistics.pstdev(cs), 4)}
    for risk in GRID:
        k = f"{risk*100:.2f}%"
        a = W2.mc_series(cs, risk, seed_base=1)
        f = W2.mc_series(csf, risk, seed_base=777) if csf else None
        s = W2.mc_series(css, risk, seed_base=999)
        out[k] = dict(p_all=a['p_pass'], p_fwd=(f['p_pass'] if f else None),
                      p_stress=s['p_pass'], med=a['med_days_pass'],
                      worst_pct=round(min(cs)*risk*100, 3))
    return out

def main(scale=0.5, cap=2.0):
    cache = pickle.load(open(HERE / 'INTEG_W3_streams_cache.pkl', 'rb'))
    cmap = json.load(open(HERE / 'SUBSTRATE_MAP.json'))['cells']
    id_map, eth_map = RG.build_id_maps()

    variants = {}
    # ungated baseline
    ung = ungated_core(cache)
    variants['ungated'] = build_streams(cache, ung)

    for mode in ('minboth', 'trainonly'):
        gall = {sl: RG.gate_cache_rows(cache[sl], sl, cmap, id_map, eth_map,
                                       size=True, scale=scale, cap=cap, mode=mode) for sl in CORE}
        variants[f'gate_all_{mode}'] = build_streams(cache, gall)
        # metals+energy gated, crypto ungated
        gme = dict(ung)
        for sl in ('metals_core', 'energy_agri'):
            gme[sl] = RG.gate_cache_rows(cache[sl], sl, cmap, id_map, eth_map,
                                         size=True, scale=scale, cap=cap, mode=mode)
        variants[f'gate_me_{mode}'] = build_streams(cache, gme)

    # baseline gross
    _, comb0, combf0, gross0, _ = daily_series(variants['ungated'])
    report = {'meta': {'scale': scale, 'cap': cap, 'matched_exposure': True,
                       'ungated_gross': round(gross0, 2)}}
    print(f"{'variant':22s} {'gross':>8} {'mScale':>7} | matched-exposure MC @0.75%   | EV/gross")
    print(f"{'':22s} {'':>8} {'':>7} | {'P_all':>6} {'P_fwd':>6} {'P_str':>6} {'med':>5} {'worst%':>7}|")
    for name, streams in variants.items():
        _, comb, combf, gross, _ = daily_series(streams)
        msc = gross0 / gross if gross > 0 else 1.0          # matched-exposure scale
        mc = mc_on(comb, combf, scale=msc)
        ev_eff = sum(comb) / gross if gross > 0 else 0.0    # EV per unit gross deployed
        k = '0.75%'
        d = mc[k]
        print(f"{name:22s} {gross:>8.1f} {msc:>7.3f} | {d['p_all']:>6.1%} "
              f"{(d['p_fwd'] or 0):>6.1%} {d['p_stress']:>6.1%} {str(d['med']):>5} {d['worst_pct']:>7.3f}| {ev_eff:+.4f}")
        report[name] = {'gross': round(gross, 2), 'matched_scale': round(msc, 4),
                        'ev_per_gross': round(ev_eff, 5), 'mc_matched': mc}
    # full grid for the key variants
    print("\nFULL GRID (matched exposure) — P(pass) ALL / FWD / STRESS1.5x")
    for name in ['ungated', 'gate_me_trainonly', 'gate_all_trainonly', 'gate_me_minboth']:
        print(f"\n[{name}]  gross={report[name]['gross']} mScale={report[name]['matched_scale']}")
        for risk in GRID:
            d = report[name]['mc_matched'][f"{risk*100:.2f}%"]
            print(f"  {risk*100:>5.2f}%  ALL {d['p_all']:>7.2%}  FWD {(d['p_fwd'] or 0):>7.2%}  "
                  f"STRESS {d['p_stress']:>7.2%}  med {str(d['med']):>5}  worst {d['worst_pct']:>+.3f}%")
    (HERE / 'RGATE_MATCHED_RESULT.json').write_text(json.dumps(report, indent=1, default=str))
    print("\nwrote RGATE_MATCHED_RESULT.json")
    return report

if __name__ == '__main__':
    sc = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    cp = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    main(scale=sc, cap=cp)
