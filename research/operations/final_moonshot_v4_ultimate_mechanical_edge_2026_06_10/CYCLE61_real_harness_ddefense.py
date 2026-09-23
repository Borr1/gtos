"""CYCLE-61 — run the REAL W7 harness (the live session's #1 residual) + DD-defense, confirm c59.

The live session flagged its #1 residual: the confirmatory KB7 MC could NOT run on the VPS (W3/W5 stream
caches absent) so its sizing odds are a calibrated RECONSTRUCTION. On THIS research laptop the caches ARE
present — so I can build the REAL W7 final daily series (INTEG_W7_final_book, Kelly-tilted, tick-restated)
and re-run the c59 DD-defense sizing on the ACTUAL streams, not a reconstruction. This closes the residual
and confirms (or corrects) the c59 conclusion. Note: the real series has a FATTER left tail (min ~-2.0 base)
than the reconstruction (-1.634) → daily-breach may bind sooner; this is exactly what real data checks.
"""
import sys, json, statistics as st
from pathlib import Path
R = Path(__file__).resolve().parent
sys.path.insert(0, str(R)); sys.path.insert(0, str(R.parents[2]))
import INTEG_W7_final_book as W7
import INTEG_W7_final_book as _w7  # for K
from CYCLE59_live_book_ddefense_sizing import mc, cap_mult   # reuse the exact DD-defense MC engine

K = W7.K


def real_comb_final():
    all_days, sleeves, M_base, M_tick, sd_book, ero = W7.build_final_matrix()
    nactive = [K.conviction_count(r) for r in M_tick]
    M_final = W7.apply_kelly_matrix(M_tick, nactive)
    comb_final = [sum(r) for r in M_final]
    sd_final = st.pstdev(comb_final)
    vs_final = sd_book / sd_final
    return comb_final, sd_book, sd_final, vs_final


def main():
    series, sd_book, sd_final, vs = real_comb_final()
    print(f"REAL W7 comb_final: n={len(series)} mean={st.fmean(series):.5f} std={sd_final:.5f} "
          f"min={min(series):.3f} max={max(series):.2f} sd_book={sd_book:.5f} VS_final={vs:.4f}")
    ACCTS = {'FN_fresh_tgt108': dict(start=100000.0, floor=90000.0, target=108000.0),
             'FTMO_97p2k_tgt110': dict(start=97200.0, floor=90000.0, target=110000.0)}
    bases = [0.0125, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04]
    out = {'schema': 'gtos.cycle61.real_harness_ddefense.v1',
           'series': {'source': 'REAL INTEG_W7_final_book comb_final (Kelly-tilted, tick-restated; caches present on research laptop)',
                      'n': len(series), 'mean': round(st.fmean(series), 5), 'std': round(sd_final, 5),
                      'min': round(min(series), 3), 'max': round(max(series), 2), 'vs_final': round(vs, 4)},
           'vs_reconstruction': 'c59 used reconstructed series (mean 0.110/std 0.758/min -1.634, vs 0.7504); this is the REAL series',
           'accounts': {}}
    for acct, a in ACCTS.items():
        print(f"\n=== {acct} (start {a['start']:.0f} floor {a['floor']:.0f} runway {(a['start']-a['floor'])/a['start']*100:.1f}%) — REAL streams ===")
        rows = {}
        for base in bases:
            eff = base * vs
            none = mc(series, eff, a['start'], a['floor'], a['target'], 'none', seed_base=11)
            band = mc(series, eff, a['start'], a['floor'], a['target'], 'band', seed_base=11)
            smooth = mc(series, eff, a['start'], a['floor'], a['target'], 'smooth', seed_base=11)
            rows[f'{base*100:.2f}%'] = {'no_defense': none, 'band': band, 'smooth': smooth}
            print(f"  base {base*100:.2f}% (eff {eff*100:.2f}%): NONE {none['p_pass']}/{none['p_fail_dd']}/{none['med']}d | "
                  f"BAND {band['p_pass']}/dd{band['p_fail_dd']}/dly{band['p_fail_daily']}/{band['med']}d worst{band['worst_day_pct']}% | "
                  f"SMOOTH {smooth['p_pass']}/dd{smooth['p_fail_dd']}/dly{smooth['p_fail_daily']}/{smooth['med']}d worst{smooth['worst_day_pct']}%")
        out['accounts'][acct] = rows
        # safe-aggressive (smooth): highest base, fail_daily==0, pass>=0.99, fail_dd<=0.01
        safe = [b for b in bases if rows[f'{b*100:.2f}%']['smooth']['p_fail_daily'] == 0.0
                and rows[f'{b*100:.2f}%']['smooth']['p_pass'] >= 0.99
                and rows[f'{b*100:.2f}%']['smooth']['p_fail_dd'] <= 0.01]
        out['accounts'][acct + '_safe_aggressive_smooth'] = (f'{max(safe)*100:.2f}%' if safe else 'none')
        print(f"  >>> safe-aggressive base (smooth-defense, fail_daily=0/pass>=0.99/fail_dd<=0.01): "
              f"{max(safe)*100:.2f}%" if safe else "  >>> none clears")
    (R / 'KNOWLEDGE_BASE' / 'validation' / 'CYCLE61_REAL_HARNESS_DDEFENSE.json').write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == '__main__':
    main()
