#!/usr/bin/env python3
"""Phase 2: Displacement DB Feature Screen — 95 fields, 7496 records."""
import json, csv, os, sys, math, warnings
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from scipy import stats as scipy_stats

warnings.filterwarnings('ignore')

BASE = Path('/Users/borr/Documents/trading/gold-agent')
KB = BASE / 'knowledge_base_backtest'
OUT = KB / 'analysis' / 'deep_dive_20260406'

###############################################################################
# Load data
###############################################################################
disp_file = KB / 'analysis' / 'XAUUSD_displacement_database_20260403_1003.csv'
with open(disp_file) as f:
    reader = csv.DictReader(f)
    all_fields = reader.fieldnames
    records = list(reader)

print(f"Loaded {len(records)} records, {len(all_fields)} fields")

# Check edge_discovery file
edge_file = KB / 'analysis' / 'edge_discovery_d1unclear_20260405.json'
if edge_file.exists():
    with open(edge_file) as f:
        edge_data = json.load(f)
    print(f"Edge discovery file exists: {type(edge_data)}")
    if isinstance(edge_data, list):
        print(f"  Records: {len(edge_data)}")
    elif isinstance(edge_data, dict):
        print(f"  Keys: {list(edge_data.keys())[:10]}")

###############################################################################
# Phase 2-PREREQ: Version Verification
###############################################################################
def version_verification():
    """Compare 7496-record CSV with prior 6641-record analyses."""
    # Known prior results (from 6641 records):
    known_checks = {
        'in_ote × cont_3h': {'expected_p': 0.824},
        'd1_dir × cont_3h': {'expected_p': 0.93},
        'tight × cont_3h': {'expected_p': 0.225},
        'consol × cont_3h': {'expected_p': 0.391},
    }

    # Run the 4 checks on the 7496 CSV
    actual = {}

    # Parse cont_3h
    for r in records:
        r['_cont_3h'] = 1 if r.get('cont_3h', '').lower() in ('true', '1', 'yes') else 0

    # in_ote × cont_3h
    for feature, expected in known_checks.items():
        fname = feature.split(' × ')[0]
        vals = [r.get(fname, '') for r in records]
        uniq = set(vals)

        if len(uniq) <= 5:  # Boolean/categorical
            groups = defaultdict(list)
            for r in records:
                v = r.get(fname, '')
                if v:
                    groups[v].append(r['_cont_3h'])

            if len(groups) == 2:
                keys = sorted(groups.keys())
                a = sum(groups[keys[0]])
                b = len(groups[keys[0]]) - a
                c = sum(groups[keys[1]])
                d = len(groups[keys[1]]) - c
                _, p = scipy_stats.chi2_contingency([[a, b], [c, d]])[:2]
                actual[feature] = {
                    'p_value': round(p, 4),
                    'expected_p': expected['expected_p'],
                    'consistent': abs(p - expected['expected_p']) < 0.15,
                }
            else:
                actual[feature] = {'note': f'Found {len(groups)} groups: {list(groups.keys())[:5]}'}
        else:
            actual[feature] = {'note': f'Not binary: {len(uniq)} unique values'}

    # Check if 6641 is a subset
    prereq = {
        'total_records_csv': len(records),
        'prior_record_count': 6641,
        'difference': len(records) - 6641,
        'consistency_checks': actual,
        'set_distribution': Counter(r.get('set', '') for r in records),
    }

    # Check date ranges by set
    disc = [r for r in records if r.get('set') == 'disc']
    val = [r for r in records if r.get('set') == 'val']
    prereq['discovery_count'] = len(disc)
    prereq['validation_count'] = len(val)
    prereq['discovery_date_range'] = f"{min(r['date'] for r in disc)} to {max(r['date'] for r in disc)}" if disc else 'N/A'
    prereq['validation_date_range'] = f"{min(r['date'] for r in val)} to {max(r['date'] for r in val)}" if val else 'N/A'

    all_consistent = all(v.get('consistent', False) for v in actual.values() if 'consistent' in v)
    prereq['all_consistent'] = all_consistent
    prereq['recommendation'] = 'Use 7496 CSV (more power, consistent with prior)' if all_consistent else 'INVESTIGATE: inconsistent p-values'

    return prereq

###############################################################################
# Phase 2A: Comprehensive Feature Screen
###############################################################################
def classify_fields():
    """Classify all fields as PREDICTOR, OUTCOME, or METADATA."""
    outcome_fields = {
        'cont_1h', 'cont_3h', 'cont_session',
        'mfe_1h', 'mfe_3h', 'mfe_sess',
        'mae_1h', 'mae_3h', 'mae_sess',
        'net_1h', 'net_3h', 'net_sess',
        'mfe_1h_bm', 'mfe_3h_bm',
        'revisit_continued', 'revisit_mfe', 'revisit_candles', 'revisit_depth',
        'nc_body_ratio', 'nc_cont_pct', 'nc_dir', 'nc_rej_wick',
    }
    metadata_fields = {
        'date', 'timestamp', 'symbol', 'set', 'open', 'high', 'low', 'close', 'volume',
    }
    semi_outcome = {'origin_revisited'}  # Include but flag

    predictors = []
    outcomes = []
    metadata = []

    for f in all_fields:
        if f in outcome_fields:
            outcomes.append(f)
        elif f in metadata_fields:
            metadata.append(f)
        else:
            predictors.append(f)

    return predictors, outcomes, metadata

def parse_value(v):
    """Try to parse as float, then bool, then leave as string."""
    if v is None or v == '' or v == 'None':
        return None
    vl = v.lower()
    if vl in ('true', 'yes'):
        return True
    if vl in ('false', 'no'):
        return False
    try:
        return float(v)
    except:
        return v

def feature_screen(records, target='cont_3h'):
    """Screen all predictor fields against target."""
    predictors, outcomes, metadata = classify_fields()

    # Parse target
    for r in records:
        r['_target'] = 1 if str(r.get(target, '')).lower() in ('true', '1', 'yes') else 0

    target_rate = sum(r['_target'] for r in records) / len(records)
    print(f"  Overall {target} rate: {target_rate:.3f}")

    results = {}
    skipped = []
    n_predictors = 0

    for field in predictors:
        vals = [parse_value(r.get(field, '')) for r in records]
        non_null = [(v, r['_target']) for v, r in zip(vals, records) if v is not None]

        if len(non_null) < 30:
            skipped.append({'field': field, 'reason': f'too few non-null ({len(non_null)})'})
            continue

        unique_vals = set(v for v, _ in non_null)

        # Check if constant
        if len(unique_vals) <= 1:
            skipped.append({'field': field, 'reason': 'constant'})
            continue

        n_predictors += 1

        # Classify as boolean, categorical, or continuous
        if unique_vals <= {True, False} or unique_vals <= {0, 1} or unique_vals <= {0.0, 1.0}:
            ftype = 'boolean'
        elif all(isinstance(v, (int, float)) for v in unique_vals) and len(unique_vals) > 10:
            ftype = 'continuous'
        elif len(unique_vals) <= 20:
            ftype = 'categorical'
        else:
            ftype = 'continuous'

        res = {
            'field': field,
            'type': ftype,
            'n_non_null': len(non_null),
            'unique_values': len(unique_vals),
            'semi_outcome': field == 'origin_revisited',
        }

        if ftype == 'boolean':
            # 2x2 chi-squared
            groups = defaultdict(list)
            for v, t in non_null:
                groups[bool(v) if isinstance(v, bool) else (v == 1 or v == 1.0 or str(v).lower() == 'true')].append(t)

            if len(groups) >= 2:
                keys = sorted(groups.keys())
                rates = {}
                for k in keys:
                    n = len(groups[k])
                    s = sum(groups[k])
                    rates[str(k)] = {'n': n, 'cont_rate': round(s/n, 4) if n > 0 else 0}

                a = sum(groups[keys[0]])
                b = len(groups[keys[0]]) - a
                c = sum(groups[keys[1]])
                d = len(groups[keys[1]]) - c

                if min(a+c, b+d) > 0:
                    chi2, p, _, _ = scipy_stats.chi2_contingency([[a, b], [c, d]])
                    r1 = a / (a+b) if (a+b) > 0 else 0
                    r2 = c / (c+d) if (c+d) > 0 else 0
                    res['test'] = 'chi2_2x2'
                    res['chi2'] = round(chi2, 4)
                    res['p_value'] = round(p, 6)
                    res['rates'] = rates
                    res['effect_size'] = round(abs(r1 - r2), 4)
                else:
                    res['test'] = 'chi2_2x2'
                    res['p_value'] = 1.0
                    res['rates'] = rates

        elif ftype == 'categorical':
            # Contingency table
            groups = defaultdict(list)
            for v, t in non_null:
                groups[str(v)].append(t)

            # Filter groups with n >= 5
            valid_groups = {k: v for k, v in groups.items() if len(v) >= 5}
            if len(valid_groups) >= 2:
                table = []
                rates = {}
                for k in sorted(valid_groups.keys()):
                    s = sum(valid_groups[k])
                    n = len(valid_groups[k])
                    table.append([s, n - s])
                    rates[k] = {'n': n, 'cont_rate': round(s/n, 4)}

                try:
                    chi2, p, _, _ = scipy_stats.chi2_contingency(table)
                    res['test'] = 'chi2_contingency'
                    res['chi2'] = round(chi2, 4)
                    res['p_value'] = round(p, 6)
                    res['rates'] = rates
                    max_r = max(r['cont_rate'] for r in rates.values())
                    min_r = min(r['cont_rate'] for r in rates.values())
                    res['effect_size'] = round(max_r - min_r, 4)
                except:
                    res['test'] = 'chi2_contingency'
                    res['p_value'] = 1.0
                    res['rates'] = rates
            else:
                res['test'] = 'insufficient_categories'
                res['p_value'] = 1.0

        elif ftype == 'continuous':
            # Point-biserial correlation
            x_vals = np.array([float(v) for v, _ in non_null])
            y_vals = np.array([t for _, t in non_null])

            if np.std(x_vals) > 0:
                r_pb, p_pb = scipy_stats.pointbiserialr(y_vals, x_vals)
                res['test'] = 'point_biserial'
                res['correlation'] = round(float(r_pb), 4)
                res['p_value'] = round(float(p_pb), 6)

                # Quintile analysis
                try:
                    quintiles = np.percentile(x_vals, [20, 40, 60, 80])
                    bins = np.digitize(x_vals, quintiles)
                    q_rates = {}
                    for q in range(5):
                        mask = bins == q
                        if sum(mask) > 0:
                            q_rates[f'Q{q+1}'] = {
                                'n': int(sum(mask)),
                                'cont_rate': round(float(y_vals[mask].mean()), 4),
                                'range': f"{x_vals[mask].min():.4f} to {x_vals[mask].max():.4f}",
                            }
                    res['quintile_rates'] = q_rates
                    qr = [v['cont_rate'] for v in q_rates.values()]
                    res['effect_size'] = round(max(qr) - min(qr), 4) if qr else 0
                except:
                    pass
            else:
                res['test'] = 'constant_values'
                res['p_value'] = 1.0

        results[field] = res

    return results, skipped, n_predictors

def discovery_validation_split(records, feature, threshold_fn=None):
    """Compare feature effect in discovery vs validation sets."""
    disc = [r for r in records if r.get('set') == 'disc']
    val = [r for r in records if r.get('set') == 'val']

    result = {}
    for label, subset in [('discovery', disc), ('validation', val)]:
        vals = [(parse_value(r.get(feature, '')), r['_target']) for r in subset]
        non_null = [(v, t) for v, t in vals if v is not None]
        if len(non_null) < 10:
            result[label] = {'n': len(non_null), 'insufficient': True}
            continue

        unique = set(v for v, _ in non_null)
        if unique <= {True, False, 0, 1, 0.0, 1.0}:
            groups = defaultdict(list)
            for v, t in non_null:
                groups[bool(v) if isinstance(v, bool) else v in (1, 1.0, True, 'True', 'true')].append(t)
            rates = {}
            for k in sorted(groups.keys()):
                n = len(groups[k])
                s = sum(groups[k])
                rates[str(k)] = {'n': n, 'rate': round(s/n, 4) if n > 0 else 0}
            result[label] = {'n': len(non_null), 'rates': rates}
        else:
            # Just report overall rate by above/below median
            nums = [float(v) for v, _ in non_null if isinstance(v, (int, float))]
            if nums:
                med = np.median(nums)
                above = [(v, t) for v, t in non_null if isinstance(v, (int, float)) and float(v) >= med]
                below = [(v, t) for v, t in non_null if isinstance(v, (int, float)) and float(v) < med]
                result[label] = {
                    'n': len(non_null),
                    'above_median_rate': round(sum(t for _, t in above) / len(above), 4) if above else None,
                    'below_median_rate': round(sum(t for _, t in below) / len(below), 4) if below else None,
                }
            else:
                result[label] = {'n': len(non_null)}

    return result

###############################################################################
# Phase 2B-2E: Specific analyses
###############################################################################
def h4_deep_dive(records):
    """Phase 2B: H4 alignment analysis."""
    results = {}

    # h4_dir × cont_3h
    groups = defaultdict(list)
    for r in records:
        v = r.get('h4_dir', '')
        if v:
            groups[v].append(r['_target'])

    rates = {}
    for k, vals in groups.items():
        rates[k] = {'n': len(vals), 'cont_rate': round(sum(vals)/len(vals), 4)}

    # Chi-squared
    valid = {k: v for k, v in groups.items() if len(v) >= 5}
    if len(valid) >= 2:
        table = [[sum(v), len(v)-sum(v)] for v in valid.values()]
        chi2, p, _, _ = scipy_stats.chi2_contingency(table)
        results['h4_dir'] = {
            'rates': rates,
            'chi2': round(chi2, 4),
            'p_value': round(p, 6),
        }

    # h4_aligned_d1 × cont_3h
    groups2 = defaultdict(list)
    for r in records:
        v = r.get('h4_aligned_d1', '')
        if v:
            groups2[v].append(r['_target'])
    rates2 = {}
    for k, vals in groups2.items():
        rates2[k] = {'n': len(vals), 'cont_rate': round(sum(vals)/len(vals), 4)}
    if len(groups2) >= 2:
        valid2 = {k: v for k, v in groups2.items() if len(v) >= 5}
        if len(valid2) >= 2:
            table2 = [[sum(v), len(v)-sum(v)] for v in valid2.values()]
            chi2_2, p_2, _, _ = scipy_stats.chi2_contingency(table2)
            results['h4_aligned_d1'] = {
                'rates': rates2,
                'chi2': round(chi2_2, 4),
                'p_value': round(p_2, 6),
            }

    # H4 when D1 is unclear
    d1_unclear = [r for r in records if r.get('d1_dir', '') in ('unclear', 'insufficient_data', '')]
    if len(d1_unclear) >= 30:
        groups3 = defaultdict(list)
        for r in d1_unclear:
            v = r.get('h4_dir', '')
            if v:
                groups3[v].append(r['_target'])
        rates3 = {}
        for k, vals in groups3.items():
            rates3[k] = {'n': len(vals), 'cont_rate': round(sum(vals)/len(vals), 4)}
        results['h4_when_d1_unclear'] = {
            'n_d1_unclear': len(d1_unclear),
            'rates': rates3,
        }

    # Discovery vs validation
    results['disc_val'] = discovery_validation_split(records, 'h4_dir')

    return results

def untested_features(records):
    """Phase 2C: Test 10 specific features."""
    features = ['strength', 'levels_swept', 'liq_depth', 'align', 'mss',
                 'm15_aligned', 'kz_min', 'crosses_rn', 'exhaust', 'first_kz']

    results = {}
    for feat in features:
        vals = [(parse_value(r.get(feat, '')), r['_target']) for r in records]
        non_null = [(v, t) for v, t in vals if v is not None]

        if len(non_null) < 30:
            results[feat] = {'n': len(non_null), 'insufficient': True}
            continue

        unique = set(v for v, _ in non_null)
        res = {'n': len(non_null), 'unique_values': len(unique)}

        if unique <= {True, False, 0, 1, 0.0, 1.0} or (len(unique) <= 5 and all(isinstance(v, str) for v in unique)):
            # Boolean or small categorical
            groups = defaultdict(list)
            for v, t in non_null:
                groups[str(v)].append(t)

            rates = {}
            for k in sorted(groups.keys()):
                n = len(groups[k])
                s = sum(groups[k])
                rates[k] = {'n': n, 'cont_rate': round(s/n, 4)}
            res['rates'] = rates

            valid_groups = {k: v for k, v in groups.items() if len(v) >= 5}
            if len(valid_groups) >= 2:
                table = [[sum(v), len(v)-sum(v)] for v in valid_groups.values()]
                try:
                    chi2, p, _, _ = scipy_stats.chi2_contingency(table)
                    res['chi2'] = round(chi2, 4)
                    res['p_value'] = round(p, 6)
                except:
                    res['p_value'] = 1.0
            else:
                res['p_value'] = 1.0

        elif all(isinstance(v, (int, float)) for v in unique):
            # Continuous
            x = np.array([float(v) for v, _ in non_null])
            y = np.array([t for _, t in non_null])
            if np.std(x) > 0:
                r_pb, p_pb = scipy_stats.pointbiserialr(y, x)
                res['correlation'] = round(float(r_pb), 4)
                res['p_value'] = round(float(p_pb), 6)

                # Quintile
                try:
                    quints = np.percentile(x, [20, 40, 60, 80])
                    bins = np.digitize(x, quints)
                    q_rates = {}
                    for q in range(5):
                        mask = bins == q
                        if sum(mask) > 0:
                            q_rates[f'Q{q+1}'] = {
                                'n': int(sum(mask)),
                                'cont_rate': round(float(y[mask].mean()), 4),
                            }
                    res['quintile_rates'] = q_rates
                except:
                    pass
            else:
                res['p_value'] = 1.0
        else:
            res['p_value'] = 1.0

        # Disc/val for anything p < 0.05
        if res.get('p_value', 1) < 0.05:
            res['disc_val'] = discovery_validation_split(records, feat)

        results[feat] = res

    return results

def revisit_failure_analysis(records):
    """Phase 2D: Failed origin revisit analysis."""
    revisited = [r for r in records if str(r.get('origin_revisited', '')).lower() in ('true', '1')]

    if len(revisited) < 30:
        return {'insufficient_data': True, 'n_revisited': len(revisited)}

    # Split: revisit_continued
    for r in revisited:
        r['_revisit_continued'] = 1 if str(r.get('revisit_continued', '')).lower() in ('true', '1') else 0

    success = [r for r in revisited if r['_revisit_continued'] == 1]
    failure = [r for r in revisited if r['_revisit_continued'] == 0]

    results = {
        'n_revisited': len(revisited),
        'n_success': len(success),
        'n_failure': len(failure),
        'success_rate': round(len(success) / len(revisited), 4),
    }

    # Compare predictor fields
    predictors, _, _ = classify_fields()
    feature_diffs = []

    for feat in predictors:
        s_vals = [parse_value(r.get(feat, '')) for r in success]
        f_vals = [parse_value(r.get(feat, '')) for r in failure]

        s_valid = [v for v in s_vals if v is not None]
        f_valid = [v for v in f_vals if v is not None]

        if len(s_valid) < 10 or len(f_valid) < 10:
            continue

        # Check if boolean/categorical vs continuous
        all_vals = s_valid + f_valid
        unique = set(all_vals)

        if unique <= {True, False, 0, 1, 0.0, 1.0}:
            # Boolean — compare proportions
            s_true = sum(1 for v in s_valid if v in (True, 1, 1.0))
            f_true = sum(1 for v in f_valid if v in (True, 1, 1.0))
            table = [[s_true, len(s_valid) - s_true], [f_true, len(f_valid) - f_true]]
            try:
                _, p = scipy_stats.fisher_exact(table)
                s_rate = s_true / len(s_valid)
                f_rate = f_true / len(f_valid)
                feature_diffs.append({
                    'field': feat,
                    'type': 'boolean',
                    'p_value': round(p, 6),
                    'success_true_rate': round(s_rate, 4),
                    'failure_true_rate': round(f_rate, 4),
                    'difference': round(s_rate - f_rate, 4),
                })
            except:
                pass

        elif all(isinstance(v, (int, float)) for v in unique):
            # Continuous — t-test
            s_arr = np.array([float(v) for v in s_valid])
            f_arr = np.array([float(v) for v in f_valid])
            if np.std(s_arr) > 0 or np.std(f_arr) > 0:
                t, p = scipy_stats.ttest_ind(s_arr, f_arr)
                feature_diffs.append({
                    'field': feat,
                    'type': 'continuous',
                    'p_value': round(p, 6),
                    'success_mean': round(float(np.mean(s_arr)), 4),
                    'failure_mean': round(float(np.mean(f_arr)), 4),
                    'difference': round(float(np.mean(s_arr) - np.mean(f_arr)), 4),
                })

    # Sort by p-value
    feature_diffs.sort(key=lambda x: x['p_value'])
    results['top_distinguishing_features'] = feature_diffs[:20]

    # Disc/val on top features
    for feat_res in feature_diffs[:5]:
        if feat_res['p_value'] < 0.05:
            feat_res['disc_val'] = {
                'note': 'Disc/val on revisit subset requires further analysis — subset may be too small per set'
            }

    return results

def body_ratio_fvg_analysis(records):
    """Phase 2E: Body ratio and FVG creation analysis."""
    results = {}

    # Body ratio quintile analysis
    br_vals = [(float(r.get('body_ratio', 0)), r['_target']) for r in records
               if r.get('body_ratio', '') not in ('', 'None', None)]

    if br_vals:
        x = np.array([v for v, _ in br_vals])
        y = np.array([t for _, t in br_vals])

        quints = np.percentile(x, [20, 40, 60, 80])
        bins = np.digitize(x, quints)
        q_rates = {}
        for q in range(5):
            mask = bins == q
            if sum(mask) > 0:
                q_rates[f'Q{q+1}'] = {
                    'n': int(sum(mask)),
                    'cont_rate': round(float(y[mask].mean()), 4),
                    'range': f"{x[mask].min():.4f} to {x[mask].max():.4f}",
                }
        results['body_ratio_quintiles'] = q_rates

        # Find optimal threshold
        thresholds = np.arange(0.3, 0.95, 0.05)
        best_thresh = None
        best_diff = 0
        for t in thresholds:
            above = y[x >= t]
            below = y[x < t]
            if len(above) > 30 and len(below) > 30:
                diff = above.mean() - below.mean()
                if abs(diff) > abs(best_diff):
                    best_diff = diff
                    best_thresh = round(float(t), 2)

        results['body_ratio_optimal_threshold'] = {
            'threshold': best_thresh,
            'rate_difference': round(best_diff, 4),
        }

        # Disc/val
        results['body_ratio_disc_val'] = discovery_validation_split(records, 'body_ratio')

    # creates_fvg × cont_3h
    fvg_groups = defaultdict(list)
    for r in records:
        v = r.get('creates_fvg', '')
        if v:
            fvg_groups[v].append(r['_target'])

    fvg_rates = {}
    for k, vals in fvg_groups.items():
        fvg_rates[k] = {'n': len(vals), 'cont_rate': round(sum(vals)/len(vals), 4)}

    valid = {k: v for k, v in fvg_groups.items() if len(v) >= 5}
    if len(valid) >= 2:
        table = [[sum(v), len(v)-sum(v)] for v in valid.values()]
        try:
            chi2, p, _, _ = scipy_stats.chi2_contingency(table)
            results['creates_fvg'] = {
                'rates': fvg_rates,
                'chi2': round(chi2, 4),
                'p_value': round(p, 6),
                'disc_val': discovery_validation_split(records, 'creates_fvg'),
            }
        except:
            results['creates_fvg'] = {'rates': fvg_rates, 'p_value': 1.0}

    # fvg_size quintile
    fvg_sizes = [(float(r.get('fvg_size', 0)), r['_target']) for r in records
                 if r.get('fvg_size', '') not in ('', 'None', None, '0', '0.0')
                 and float(r.get('fvg_size', 0)) > 0]

    if len(fvg_sizes) > 30:
        x = np.array([v for v, _ in fvg_sizes])
        y = np.array([t for _, t in fvg_sizes])
        quints = np.percentile(x, [20, 40, 60, 80])
        bins = np.digitize(x, quints)
        q_rates = {}
        for q in range(5):
            mask = bins == q
            if sum(mask) > 0:
                q_rates[f'Q{q+1}'] = {
                    'n': int(sum(mask)),
                    'cont_rate': round(float(y[mask].mean()), 4),
                }
        results['fvg_size_quintiles'] = q_rates
        results['fvg_size_disc_val'] = discovery_validation_split(records, 'fvg_size')

    return results

###############################################################################
# Main
###############################################################################
if __name__ == '__main__':
    print("=" * 60)
    print("PHASE 2: DISPLACEMENT DB FEATURE SCREEN")
    print("=" * 60)

    # 2-PREREQ
    print("\n--- 2-PREREQ: Version Verification ---")
    prereq = version_verification()
    print(f"  Records: {prereq['total_records_csv']} (prior: {prereq['prior_record_count']})")
    print(f"  Discovery: {prereq['discovery_count']}, Validation: {prereq['validation_count']}")
    for check, v in prereq['consistency_checks'].items():
        if 'p_value' in v:
            print(f"  {check}: p={v['p_value']} (expected ~{v['expected_p']}) {'✓' if v.get('consistent') else '✗'}")
    print(f"  Recommendation: {prereq['recommendation']}")

    # 2A: Full feature screen
    print("\n--- 2A: Feature Screen ---")
    screen_results, skipped, n_predictors = feature_screen(records)

    # Rank by p-value
    ranked = sorted(screen_results.values(), key=lambda x: x.get('p_value', 1.0))
    bonferroni = 0.05 / n_predictors
    print(f"  Tested {n_predictors} predictor fields. Bonferroni threshold: {bonferroni:.6f}")

    confirmed = [r for r in ranked if r.get('p_value', 1) < bonferroni]
    suggestive = [r for r in ranked if bonferroni <= r.get('p_value', 1) < 0.01]
    null_fields = [r for r in ranked if r.get('p_value', 1) >= 0.01]

    print(f"  CONFIRMED (p < {bonferroni:.6f}): {len(confirmed)}")
    for r in confirmed[:10]:
        print(f"    {r['field']}: p={r['p_value']}, effect={r.get('effect_size','N/A')}")
    print(f"  SUGGESTIVE (p < 0.01): {len(suggestive)}")
    for r in suggestive[:10]:
        print(f"    {r['field']}: p={r['p_value']}, effect={r.get('effect_size','N/A')}")
    print(f"  NULL (p >= 0.01): {len(null_fields)}")

    # Disc/val for confirmed features
    for r in confirmed:
        r['disc_val'] = discovery_validation_split(records, r['field'])

    # Pairwise correlation among confirmed/suggestive
    sig_fields = [r['field'] for r in confirmed + suggestive]
    corr_matrix = {}
    for i, f1 in enumerate(sig_fields):
        for f2 in sig_fields[i+1:]:
            v1 = [parse_value(r.get(f1, '')) for r in records]
            v2 = [parse_value(r.get(f2, '')) for r in records]
            pairs = [(a, b) for a, b in zip(v1, v2) if a is not None and b is not None
                     and isinstance(a, (int, float, bool)) and isinstance(b, (int, float, bool))]
            if len(pairs) > 30:
                x = np.array([float(a) for a, _ in pairs])
                y = np.array([float(b) for _, b in pairs])
                if np.std(x) > 0 and np.std(y) > 0:
                    c = np.corrcoef(x, y)[0, 1]
                    corr_matrix[f"{f1} × {f2}"] = round(float(c), 4)

    # 2B: H4 Deep Dive
    print("\n--- 2B: H4 Alignment Deep Dive ---")
    h4_results = h4_deep_dive(records)
    if 'h4_dir' in h4_results:
        print(f"  h4_dir: p={h4_results['h4_dir']['p_value']}")
        for k, v in h4_results['h4_dir']['rates'].items():
            print(f"    {k}: n={v['n']}, rate={v['cont_rate']}")

    # 2C: Untested Features
    print("\n--- 2C: Untested Promising Features ---")
    untested = untested_features(records)
    for feat, res in sorted(untested.items(), key=lambda x: x[1].get('p_value', 1)):
        p = res.get('p_value', 'N/A')
        print(f"  {feat}: p={p}, n={res.get('n', 'N/A')}")

    # 2D: Revisit Failure
    print("\n--- 2D: Failed Origin Revisit ---")
    revisit_results = revisit_failure_analysis(records)
    print(f"  Revisited: {revisit_results.get('n_revisited', 0)}")
    print(f"  Success: {revisit_results.get('n_success', 0)}, Failure: {revisit_results.get('n_failure', 0)}")
    if 'top_distinguishing_features' in revisit_results:
        for feat in revisit_results['top_distinguishing_features'][:5]:
            print(f"    {feat['field']}: p={feat['p_value']}")

    # 2E: Body Ratio + FVG
    print("\n--- 2E: Body Ratio + FVG Creation ---")
    br_fvg = body_ratio_fvg_analysis(records)
    if 'body_ratio_optimal_threshold' in br_fvg:
        print(f"  Optimal body ratio threshold: {br_fvg['body_ratio_optimal_threshold']['threshold']}")
    if 'creates_fvg' in br_fvg:
        print(f"  creates_fvg p: {br_fvg['creates_fvg']['p_value']}")

    # Save all
    output = {
        'prereq_version_verification': prereq,
        'feature_screen': {
            'n_predictors_tested': n_predictors,
            'bonferroni_threshold': round(bonferroni, 6),
            'confirmed': [r for r in ranked if r.get('p_value', 1) < bonferroni],
            'suggestive': [r for r in ranked if bonferroni <= r.get('p_value', 1) < 0.01],
            'null_count': len(null_fields),
            'skipped': skipped,
            'all_results_ranked': [{k: v for k, v in r.items()} for r in ranked],
            'pairwise_correlations': corr_matrix,
        },
        'h4_deep_dive': h4_results,
        'untested_features': untested,
        'revisit_failure': revisit_results,
        'body_ratio_fvg': br_fvg,
    }

    with open(OUT / 'displacement_feature_screen_20260406.json', 'w') as f:
        json.dump(output, f, indent=2, default=str)

    # Markdown report
    md = f"""# Phase 2: Displacement DB Feature Screen — {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 2-PREREQ: Version Verification
- CSV records: {prereq['total_records_csv']} (prior analyses used 6,641)
- Discovery: {prereq['discovery_count']} | Validation: {prereq['validation_count']}
- Consistency checks: {'ALL PASSED' if prereq['all_consistent'] else 'SOME FAILED'}
- **{prereq['recommendation']}**

## 2A: Comprehensive Feature Screen
- Tested: {n_predictors} predictor fields
- Bonferroni threshold: {bonferroni:.6f}

### CONFIRMED Features (survive Bonferroni)
| Field | Type | p-value | Effect Size | N |
|-------|------|---------|-------------|---|
"""
    for r in confirmed:
        md += f"| {r['field']} | {r['type']} | {r['p_value']:.6f} | {r.get('effect_size', 'N/A')} | {r['n_non_null']} |\n"

    md += "\n### SUGGESTIVE Features (p < 0.01)\n| Field | Type | p-value | Effect Size | N |\n|-------|------|---------|-------------|---|\n"
    for r in suggestive:
        md += f"| {r['field']} | {r['type']} | {r['p_value']:.6f} | {r.get('effect_size', 'N/A')} | {r['n_non_null']} |\n"

    md += f"\n### NULL Features: {len(null_fields)} fields with p >= 0.01\n"

    if corr_matrix:
        md += "\n### Pairwise Correlations (Confirmed + Suggestive)\n| Pair | Correlation |\n|------|-------------|\n"
        for pair, c in sorted(corr_matrix.items(), key=lambda x: abs(x[1]), reverse=True)[:10]:
            md += f"| {pair} | {c} |\n"

    md += f"""
## 2B: H4 Alignment Deep Dive
"""
    if 'h4_dir' in h4_results:
        md += f"- h4_dir × cont_3h: p={h4_results['h4_dir']['p_value']}\n"
        for k, v in h4_results['h4_dir']['rates'].items():
            md += f"  - {k}: n={v['n']}, cont_rate={v['cont_rate']}\n"

    md += f"""
## 2C: Untested Features
| Feature | p-value | N | Notes |
|---------|---------|---|-------|
"""
    for feat in sorted(untested.keys(), key=lambda x: untested[x].get('p_value', 1)):
        res = untested[feat]
        p = res.get('p_value', 'N/A')
        md += f"| {feat} | {p} | {res.get('n', 'N/A')} | |\n"

    md += f"""
## 2D: Failed Origin Revisit
- Revisited: {revisit_results.get('n_revisited', 0)}
- Success (continued): {revisit_results.get('n_success', 0)} ({revisit_results.get('success_rate', 0):.1%})
- Failure: {revisit_results.get('n_failure', 0)}
"""
    if 'top_distinguishing_features' in revisit_results:
        md += "\n| Feature | p-value | Type | Success vs Failure |\n|---------|---------|------|-------------------|\n"
        for feat in revisit_results['top_distinguishing_features'][:10]:
            if feat['type'] == 'boolean':
                detail = f"S:{feat['success_true_rate']:.2f} vs F:{feat['failure_true_rate']:.2f}"
            else:
                detail = f"S:{feat['success_mean']:.4f} vs F:{feat['failure_mean']:.4f}"
            md += f"| {feat['field']} | {feat['p_value']:.6f} | {feat['type']} | {detail} |\n"

    md += f"""
## 2E: Body Ratio + FVG Creation
"""
    if 'body_ratio_quintiles' in br_fvg:
        md += "### Body Ratio Quintiles\n| Quintile | N | Cont Rate | Range |\n|----------|---|-----------|-------|\n"
        for k, v in br_fvg['body_ratio_quintiles'].items():
            md += f"| {k} | {v['n']} | {v['cont_rate']} | {v.get('range', '')} |\n"
    if 'body_ratio_optimal_threshold' in br_fvg:
        md += f"\nOptimal threshold: {br_fvg['body_ratio_optimal_threshold']['threshold']} (rate diff: {br_fvg['body_ratio_optimal_threshold']['rate_difference']})\n"
    if 'creates_fvg' in br_fvg:
        md += f"\n### FVG Creation\np-value: {br_fvg['creates_fvg']['p_value']}\n"
        for k, v in br_fvg['creates_fvg']['rates'].items():
            md += f"- {k}: n={v['n']}, rate={v['cont_rate']}\n"

    with open(OUT / 'displacement_feature_screen_20260406.md', 'w') as f:
        f.write(md)

    print(f"\nPhase 2 complete. Files saved.")
