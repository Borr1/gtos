"""CYCLE-60 — reopen intraday breadth at the REAL (live-measured) execution cost.

The live handoff revealed index CFD round-trip cost is ~0.01-0.03R (entry spread 0.004-0.017R, section 4 /
admission.py TICK_SPREAD_FLOOR_R) — 3-10x cheaper than my conservative retail estimate (~0.05-0.07R). My
c44-46 gated the intraday edges as cost-killed; c45 showed the time-of-day INDEX drift clears at <=0.6x
retail and c46 found it ORTHOGONAL to the core (corr -0.02) but sub-significant AT RETAIL cost. The real
cost is ~0.2-0.3x retail -> the net edge ~doubles. Does it now CERTIFY as genuine new orthogonal intraday
breadth? Run the gauntlet (PSR + block-perm + per-year) at the real index cost.
"""
from __future__ import annotations
import sys, json, statistics as st, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT))
from CYCLE46_tod_orthogonality import tod_daily, us_daily   # tod_daily(cost_mult) -> {date: R}
from src.research_infra.validation_integrity import dsr as _dsr
from src.research_infra.validation_integrity import perm_null as _perm
from src.research_infra.validation_integrity import portfolio_contribution as _pc

SEALED = "2025-01-01"
# real index round-trip ~0.02R vs my retail harness ~0.073R for the TOD index basket -> cost_mult ~0.27.
# sweep around the real level to bound it honestly.
COST_MULTS = {'retail_1.0x(c46)': 1.0, 'half_0.5x': 0.5, 'real_0.27x': 0.27, 'rawspread_0.15x': 0.15}


def gauntlet(series_by_day):
    days = sorted(series_by_day)
    ser = [series_by_day[d] for d in days]
    psr = _dsr.probabilistic_sharpe_ratio(ser, 0.0)["psr"]
    permp = _perm.block_permutation_test(ser, block=5, n_perm=4000, stat="sharpe")["p_value"]
    by_year = collections.defaultdict(list)
    for d in days:
        by_year[int(d[:4])].append(series_by_day[d])
    oos = [series_by_day[d] for d in days if int(d[:4]) > 2021]
    sd = st.pstdev(oos) if len(oos) > 1 else 0.0
    return {'n': len(ser), 'OOS_mean': round(st.fmean(oos), 5) if oos else 0.0,
            'OOS_sharpe': round(st.fmean(oos)/sd, 4) if sd > 0 else 0.0,
            'PSR_vs_zero': round(psr, 4), 'perm_p': round(permp, 5),
            'per_year': {y: round(sum(v)/len(v), 5) for y, v in sorted(by_year.items())}}


def main():
    us = us_daily()
    out = {'schema': 'gtos.cycle60.intraday_at_real_cost.v1',
           'edge': 'time_of_day_drift (pre-European equity, h07 {US30,GER40,UK100}, orthogonal corr -0.02 to core)',
           'by_cost': {}}
    for label, cm in COST_MULTS.items():
        tod = tod_daily(cm)
        g = gauntlet(tod)
        # genuine edge vs zero
        genuine = (g['PSR_vs_zero'] > 0.95) and (g['perm_p'] < 0.05)
        # diversifier vs the deployed core (us_equity proxy for the equity-leg core)
        div = _pc.certify_diversifier(us, tod, standalone_edge_ok=genuine, regime_clean=True,
                                      sealed_start=SEALED, weight=0.35, corr_ceiling=0.35, n_boot=3000)
        out['by_cost'][label] = {'cost_mult': cm, **g, 'genuine_edge': genuine,
                                 'diversifier_verdict': div['verdict'],
                                 'div_delta_pct': round(div['incremental']['delta_pct'], 3),
                                 'div_ci': [div['bootstrap']['ci_low'], div['bootstrap']['ci_high']],
                                 'corr_to_core': round(div['corr_to_book'], 4)}
        print(f"{label} (cm {cm}): OOS_mean {g['OOS_mean']:+.4f} sharpe {g['OOS_sharpe']:+.3f} "
              f"PSR {g['PSR_vs_zero']} perm {g['perm_p']} genuine {genuine} | div {div['verdict']} "
              f"delta {round(div['incremental']['delta_pct'],2)}% CI [{div['bootstrap']['ci_low']:.4f},{div['bootstrap']['ci_high']:.4f}]")
    real = out['by_cost']['real_0.27x']
    certifies = real['genuine_edge'] and real['diversifier_verdict'] == 'CERTIFIED_DIVERSIFIER'
    out['verdict'] = ('NEW_INTRADAY_BREADTH at real cost (genuine + certified diversifier — orthogonal intraday index sleeve)'
                      if certifies else
                      f"STILL_NOT_CERTIFIED at real cost (genuine={real['genuine_edge']}, div={real['diversifier_verdict']}) — edge improves but {'too thin/not significant' if not real['genuine_edge'] else 'not a certified diversifier'}")
    (HERE / 'KNOWLEDGE_BASE' / 'validation' / 'CYCLE60_INTRADAY_AT_REAL_COST.json').write_text(json.dumps(out, indent=1, default=str))
    print(f"\n>>> {out['verdict']}")
    return out


if __name__ == '__main__':
    main()
