#!/usr/bin/env python3
"""Census of the SCORECARD and DECISION ledgers, both windows, streamed.

SCORECARD (one row per decision window): candidate_count stats,
final_selection_claim, risk_admitted_finalizer_status distribution,
selected_probe_count, selection-mode constancy.
DECISION (one row per symbol x asof): row_type x final_selection_claim,
rows per trading_day, candidate_count stats, raw_data_status mix.
"""
import json, sys
from collections import Counter, defaultdict

WT = '/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801'
W16 = '/Users/borr/GTOSActive/worktrees/wave16-rematerialization-20260731'
W18 = '/Users/borr/GTOSActive/worktrees/wave18-true-utc-factory-20260801'
ROUTE = 'research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse'
ARMS = {
    'january': (f'{W16}/{ROUTE}/CJ_RECLOCKED_S0R0_V7', 'CJ_RECLOCKED_S0R0_V7'),
    'february': (f'{W18}/{ROUTE}/CP_FEBRUARY_TRUE_UTC_S0R0_V1', 'CP_FEBRUARY_TRUE_UTC_S0R0_V1'),
}


def qstats(vals):
    if not vals:
        return None
    v = sorted(vals)
    n = len(v)
    return {'n': n, 'min': v[0], 'p25': v[n // 4], 'p50': v[n // 2],
            'p75': v[3 * n // 4], 'max': v[-1], 'mean': round(sum(v) / n, 3),
            'sum': sum(v)}


def main():
    out = {}
    for win, (root, stem) in ARMS.items():
        sc = {'rows': 0, 'final_selection_claim': Counter(), 'candidate_counts': [],
              'status': Counter(), 'selected_probe_count': Counter(),
              'selection_mode': Counter(), 'selection_factor': Counter(),
              'distinct_asof': set(), 'probe_vs_candidate_mismatch': 0,
              'all_options_preserved': Counter()}
        with open(f'{root}/{stem}_SCORECARD_LEDGER.jsonl') as f:
            for line in f:
                r = json.loads(line)
                sc['rows'] += 1
                sc['final_selection_claim'][str(r.get('final_selection_claim'))] += 1
                cc = r.get('candidate_count')
                if isinstance(cc, (int, float)):
                    sc['candidate_counts'].append(int(cc))
                sc['status'][str(r.get('risk_admitted_finalizer_status'))] += 1
                sc['selected_probe_count'][str(r.get('risk_admitted_finalizer_selected_probe_count'))] += 1
                sc['selection_mode'][str(r.get('b7_5_selection_sizing_factorial_selection_mode'))] += 1
                sc['selection_factor'][str(r.get('b7_5_selection_sizing_factorial_selection_factor'))] += 1
                sc['distinct_asof'].add(r.get('asof_utc'))
                sc['all_options_preserved'][str(r.get('all_options_preserved_count'))] += 1
                if r.get('risk_admitted_finalizer_probe_count') != cc:
                    sc['probe_vs_candidate_mismatch'] += 1
        scorecard = {
            'rows': sc['rows'],
            'distinct_asof': len(sc['distinct_asof']),
            'final_selection_claim': dict(sc['final_selection_claim']),
            'candidate_count_stats': qstats(sc['candidate_counts']),
            'risk_admitted_finalizer_status': dict(sc['status'].most_common()),
            'selected_probe_count': dict(sorted(sc['selected_probe_count'].items())),
            'selection_mode': dict(sc['selection_mode']),
            'selection_factor': dict(sc['selection_factor']),
            'probe_count_neq_candidate_count_rows': sc['probe_vs_candidate_mismatch'],
            'all_options_preserved_count': dict(sorted(sc['all_options_preserved'].items())[:10]),
        }
        print(win, 'scorecard done', file=sys.stderr)

        de = {'rows': 0, 'row_type_x_claim': Counter(), 'per_day': Counter(),
              'candidate_counts': [], 'raw_data_status': Counter(),
              'row_type': Counter(), 'claim_true_days': Counter(),
              'symbols': set()}
        with open(f'{root}/{stem}_DECISION_LEDGER.jsonl') as f:
            for line in f:
                r = json.loads(line)
                de['rows'] += 1
                rt = str(r.get('row_type'))
                claim = str(r.get('final_selection_claim'))
                de['row_type'][rt] += 1
                de['row_type_x_claim'][f'{rt}|{claim}'] += 1
                de['per_day'][str(r.get('trading_day'))] += 1
                cc = r.get('candidate_count')
                if isinstance(cc, (int, float)):
                    de['candidate_counts'].append(int(cc))
                de['raw_data_status'][str(r.get('raw_data_status'))] += 1
                de['symbols'].add(r.get('symbol'))
                if claim == 'True':
                    de['claim_true_days'][str(r.get('trading_day'))] += 1
        days = sorted(de['per_day'])
        decision = {
            'rows': de['rows'],
            'row_type': dict(de['row_type']),
            'row_type_x_final_selection_claim': dict(de['row_type_x_claim'].most_common()),
            'trading_days': len(days),
            'rows_per_day_stats': qstats(list(de['per_day'].values())),
            'candidate_count_stats': qstats(de['candidate_counts']),
            'candidate_count_zero_rows': sum(1 for c in de['candidate_counts'] if c == 0),
            'raw_data_status': dict(de['raw_data_status'].most_common()),
            'distinct_symbols': len(de['symbols']),
            'final_selection_claim_true_by_day': dict(sorted(de['claim_true_days'].items())),
        }
        print(win, 'decision done', file=sys.stderr)
        out[win] = {'scorecard': scorecard, 'decision': decision}

    with open(f'{WT}/research/operations/wave19_broad_forensic_2026_08_01/scorecard/DECISION_CENSUS.json', 'w') as f:
        json.dump(out, f, indent=1)
    print(json.dumps({w: {'scorecard_rows': v['scorecard']['rows'],
                          'scorecard_claim': v['scorecard']['final_selection_claim'],
                          'decision_rows': v['decision']['rows'],
                          'decision_claim': v['decision']['row_type_x_final_selection_claim']}
                      for w, v in out.items()}, indent=1))


if __name__ == '__main__':
    main()
