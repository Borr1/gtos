#!/usr/bin/env python3
"""
Sprint Alpha — Four Analyses on Real Batch Data
1. R-Multiple Decomposition
2. Reasoning Text Mining
3. Per-Step Evaluation Analysis
4. All-Instrument Autocorrelation Baselines
"""

import json
import re
import warnings
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings('ignore')

BATCH_DIR = Path("knowledge_base_backtest/batch_api")
DATA_DIR = Path("data/historical")
OUTPUT_DIR = Path("research/archive/root_legacy_artifacts_2026_05_31/generated/sprint_alpha")
PRIMARY = "msgbatch_01WUZbzFQniomk49SoLRAsPg"


def load_primary_data():
    """Load trades + raw reasoning from primary XAUUSD batch."""
    with open(BATCH_DIR / f"{PRIMARY}_results.json") as f:
        results = json.load(f)
    with open(BATCH_DIR / f"{PRIMARY}_raw_results.json") as f:
        raw = json.load(f)

    # Extract trades with outcomes
    trades = []
    for day in results:
        if not isinstance(day, dict) or not day.get('trade_taken'):
            continue
        for t in day.get('trades', []):
            if isinstance(t, dict):
                trades.append({**t, 'date': day['date']})

    # Build raw reasoning index: key -> parsed JSON
    raw_parsed = {}
    for k, v in raw.items():
        text = v.get('text', '') if isinstance(v, dict) else str(v)
        try:
            p = json.loads(text)
            raw_parsed[k] = p
        except:
            pass

    # Match trades to CANDIDATE reasoning entries
    # For each trade date+kz, find the CANDIDATE entry
    matched = []
    for t in trades:
        date = t['date']
        kz = t.get('kill_zone', '')
        best_candidate = None
        best_conf = -1

        for k, p in raw_parsed.items():
            if p.get('decision') not in ('CANDIDATE', 'ENTER_LONG', 'ENTER_SHORT'):
                continue
            if not k.startswith(date):
                continue
            # Check KZ match
            prefix_parts = k.rsplit('_', 1)[0].rsplit('_', 1)
            entry_kz = prefix_parts[1] if len(prefix_parts) > 1 else ''
            if entry_kz.lower() != kz.lower():
                continue
            conf = p.get('confidence_score', 0)
            if conf > best_conf:
                best_conf = conf
                best_candidate = p

        matched.append({
            'trade': t,
            'reasoning': best_candidate,
        })

    return matched, raw_parsed


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 1: R-MULTIPLE DECOMPOSITION
# ═══════════════════════════════════════════════════════════════════════════════

def analysis_1(matched):
    lines = ["# Analysis 1: R-Multiple Decomposition\n"]

    trades = [m['trade'] for m in matched]
    n = len(trades)
    wins = [t for t in trades if t['outcome'] == 'WIN']
    losses = [t for t in trades if t['outcome'] == 'LOSS']
    bes = [t for t in trades if t['outcome'] == 'BREAKEVEN']

    # Basic stats
    all_r = [t['r_multiple'] for t in trades]
    win_r = [t['r_multiple'] for t in wins]
    loss_r = [t['r_multiple'] for t in losses]

    lines.append("## Overall Stats\n")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Total trades | {n} |")
    lines.append(f"| Wins | {len(wins)} ({len(wins)/n*100:.1f}%) |")
    lines.append(f"| Losses | {len(losses)} ({len(losses)/n*100:.1f}%) |")
    lines.append(f"| Breakeven | {len(bes)} ({len(bes)/n*100:.1f}%) |")
    lines.append(f"| **Overall expectancy** | **{np.mean(all_r):.3f}R** per trade |")
    lines.append(f"| Avg winner R | +{np.mean(win_r):.3f}R |")
    lines.append(f"| Avg loser R | {np.mean(loss_r):.3f}R |")
    lines.append(f"| Best trade | +{max(all_r):.2f}R |")
    lines.append(f"| Worst trade | {min(all_r):.2f}R |")
    lines.append(f"| Profit factor | {sum(r for r in all_r if r > 0) / abs(sum(r for r in all_r if r < 0)):.2f} |")

    # Distribution by exit type
    lines.append("\n## Exit Type Distribution\n")
    exit_groups = defaultdict(list)
    for t in trades:
        exit_groups[t.get('exit_substate', 'unknown')].append(t)

    lines.append("| Exit Type | Count | % | Avg R | WR |")
    lines.append("|---|---|---|---|---|")
    for exit_type in sorted(exit_groups.keys()):
        ts = exit_groups[exit_type]
        cnt = len(ts)
        pct = cnt / n * 100
        avg_r = np.mean([t['r_multiple'] for t in ts])
        wr = sum(1 for t in ts if t['outcome'] == 'WIN') / cnt * 100
        lines.append(f"| {exit_type} | {cnt} | {pct:.1f}% | {avg_r:+.3f}R | {wr:.1f}% |")

    # By AI grade
    lines.append("\n## By AI Setup Grade\n")
    grade_groups = defaultdict(list)
    for m in matched:
        r = m.get('reasoning') or {}
        reasoning = r.get('reasoning', {}) or {}
        grade = reasoning.get('setup_grade', 'unknown')
        if isinstance(grade, str):
            grade = grade.strip('"')
        grade_groups[grade].append(m['trade'])

    lines.append("| Grade | Count | WR | Avg R | Expectancy |")
    lines.append("|---|---|---|---|---|")
    for grade in sorted(grade_groups.keys()):
        ts = grade_groups[grade]
        cnt = len(ts)
        wr = sum(1 for t in ts if t['outcome'] in ('WIN', 'BREAKEVEN')) / cnt * 100
        avg_r = np.mean([t['r_multiple'] for t in ts])
        lines.append(f"| {grade} | {cnt} | {wr:.1f}% | {avg_r:+.3f}R | {avg_r:+.3f}R |")

    # By kill zone
    lines.append("\n## By Kill Zone\n")
    kz_groups = defaultdict(list)
    for t in trades:
        kz_groups[t.get('kill_zone', 'unknown')].append(t)

    lines.append("| Kill Zone | Count | WR | Avg R | Expectancy |")
    lines.append("|---|---|---|---|---|")
    for kz in sorted(kz_groups.keys()):
        ts = kz_groups[kz]
        cnt = len(ts)
        wr = sum(1 for t in ts if t['outcome'] in ('WIN', 'BREAKEVEN')) / cnt * 100
        avg_r = np.mean([t['r_multiple'] for t in ts])
        lines.append(f"| {kz} | {cnt} | {wr:.1f}% | {avg_r:+.3f}R | {avg_r:+.3f}R |")

    # By confidence score
    lines.append("\n## By Confidence Score\n")
    conf_groups = defaultdict(list)
    for m in matched:
        r = m.get('reasoning') or {}
        conf = r.get('confidence_score', 0)
        bucket = f"{(conf // 5) * 5}-{(conf // 5) * 5 + 4}" if conf else 'unknown'
        conf_groups[bucket].append(m['trade'])

    lines.append("| Confidence Bucket | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for bucket in sorted(conf_groups.keys()):
        ts = conf_groups[bucket]
        cnt = len(ts)
        if cnt < 3:
            continue
        wr = sum(1 for t in ts if t['outcome'] in ('WIN', 'BREAKEVEN')) / cnt * 100
        avg_r = np.mean([t['r_multiple'] for t in ts])
        lines.append(f"| {bucket} | {cnt} | {wr:.1f}% | {avg_r:+.3f}R |")

    # By framework
    lines.append("\n## By Framework\n")
    fw_groups = defaultdict(list)
    for t in trades:
        fw_groups[t.get('framework', 'unknown')].append(t)

    lines.append("| Framework | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for fw in sorted(fw_groups.keys()):
        ts = fw_groups[fw]
        cnt = len(ts)
        wr = sum(1 for t in ts if t['outcome'] in ('WIN', 'BREAKEVEN')) / cnt * 100
        avg_r = np.mean([t['r_multiple'] for t in ts])
        lines.append(f"| {fw} | {cnt} | {wr:.1f}% | {avg_r:+.3f}R |")

    # MFE/MAE analysis
    lines.append("\n## MFE/MAE Analysis\n")
    mfes = [t['mfe_r'] for t in trades if t.get('mfe_r') is not None]
    maes = [t['mae_r'] for t in trades if t.get('mae_r') is not None]
    if mfes:
        lines.append(f"- **Max Favorable Excursion (MFE)**: median {np.median(mfes):.2f}R, mean {np.mean(mfes):.2f}R")
        lines.append(f"- **Max Adverse Excursion (MAE)**: median {np.median(maes):.2f}R, mean {np.mean(maes):.2f}R")
        # How many trades reached 1R favorable?
        reached_1r = sum(1 for m in mfes if m >= 1.0)
        lines.append(f"- Trades reaching ≥1.0R MFE: {reached_1r}/{len(mfes)} ({reached_1r/len(mfes)*100:.1f}%)")
        reached_15r = sum(1 for m in mfes if m >= 1.5)
        lines.append(f"- Trades reaching ≥1.5R MFE: {reached_15r}/{len(mfes)} ({reached_15r/len(mfes)*100:.1f}%)")

    # Unfiltered expectancy estimate
    lines.append("\n## Unfiltered OB Expectancy Estimate\n")
    lines.append("If all 219 OB retest events were traded with fixed TP structure:")
    lines.append("- At 70.5% sim WR (from Task 1 rerun)")
    lines.append("- TP1 at 1.5 ATR (50% close), TP2 at 2.5 ATR (25% close), TP3 at 4.0 ATR (25% close)")
    lines.append("- SL at -1.0R\n")

    sim_wr = 0.705
    # Expected R per trade with partial closes:
    # Win: 0.50 * 1.5 + 0.25 * 2.5 + 0.25 * 4.0 = 0.75 + 0.625 + 1.0 = 2.375R (if all TPs hit)
    # But realistically many wins don't reach TP3. Use avg winner from actual data.
    avg_win_r = np.mean(win_r) if win_r else 0.5
    avg_loss_r = abs(np.mean(loss_r)) if loss_r else 1.0
    unfiltered_exp = sim_wr * avg_win_r - (1 - sim_wr) * avg_loss_r

    lines.append(f"- Using actual avg winner ({avg_win_r:+.3f}R) and avg loser ({-avg_loss_r:.3f}R):")
    lines.append(f"- **Unfiltered expectancy**: {sim_wr:.1%} × {avg_win_r:.3f} - {1-sim_wr:.1%} × {avg_loss_r:.3f} = **{unfiltered_exp:+.3f}R per trade**")
    lines.append(f"- **AI-selected expectancy**: {np.mean(all_r):+.3f}R per trade")
    lines.append(f"- Delta: {np.mean(all_r) - unfiltered_exp:+.3f}R per trade")

    # Does AI produce better R?
    lines.append("\n## Does AI Produce Better R Through Smarter TP Placement?\n")
    lines.append(f"The AI-selected trades average **{np.mean(all_r):+.3f}R** per trade.")
    lines.append(f"With the actual win distribution and avg winner of {avg_win_r:+.3f}R,")
    lines.append(f"the system is capturing partial profits (BE stops, trailing) that reduce")
    lines.append(f"average winner R but protect against reversals.\n")

    # Check if high-R winners are disproportionately from AI high-confidence
    big_wins = [m for m in matched if m['trade']['r_multiple'] >= 1.5]
    if big_wins:
        confs = [m['reasoning'].get('confidence_score', 0) for m in big_wins if m.get('reasoning')]
        lines.append(f"- Trades ≥1.5R: {len(big_wins)}, avg confidence: {np.mean(confs):.0f}" if confs else "")
        all_confs = [m['reasoning'].get('confidence_score', 0) for m in matched if m.get('reasoning')]
        lines.append(f"- All trades avg confidence: {np.mean(all_confs):.0f}" if all_confs else "")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 2: REASONING TEXT MINING
# ═══════════════════════════════════════════════════════════════════════════════

def extract_text_features(parsed):
    """Extract text features from a CANDIDATE reasoning entry."""
    if not parsed:
        return None

    reasoning = parsed.get('reasoning', {}) or {}
    overall = reasoning.get('overall_reasoning', '')
    if isinstance(overall, dict):
        overall = json.dumps(overall)
    overall = str(overall)

    # Collect all explanation text
    all_text = overall
    for step_name, step_data in reasoning.items():
        if isinstance(step_data, dict):
            exp = step_data.get('explanation', '')
            all_text += ' ' + str(exp)

    # Features
    word_count = len(all_text.split())

    # Price levels: numbers like 3042.50 or 2316
    price_levels = re.findall(r'\b\d{3,5}\.\d{1,2}\b', all_text)
    price_count = len(set(price_levels))

    # Hedging phrases
    hedging_words = ['however', 'although', 'but', 'might', 'could', 'possibly',
                     'uncertain', 'unclear', 'risk', 'caution', 'concern', 'weak']
    hedging_count = sum(1 for w in hedging_words if w.lower() in all_text.lower())

    # FVG mention
    has_fvg = any(term in all_text.lower() for term in ['fvg', 'fair value gap', 'three-candle gap', 'three candle gap'])

    # All timeframes aligned
    h4_aligned = False
    h4_data = reasoning.get('h4_alignment', {}) or {}
    if isinstance(h4_data, dict):
        h4_aligned = h4_data.get('aligned', False)

    m15_data = reasoning.get('m15_confirmation', {}) or {}
    choch = False
    disp_quality = 'unknown'
    if isinstance(m15_data, dict):
        choch = m15_data.get('choch_detected', False)
        disp_quality = m15_data.get('displacement_quality', 'unknown')
    all_aligned = h4_aligned and choch

    confidence = parsed.get('confidence_score', 0)

    grade = reasoning.get('setup_grade', 'unknown')
    if isinstance(grade, str):
        grade = grade.strip('"')

    return {
        'word_count': word_count,
        'price_count': price_count,
        'hedging_count': hedging_count,
        'has_fvg': has_fvg,
        'all_aligned': all_aligned,
        'confidence': confidence,
        'grade': grade,
    }


def analysis_2(matched):
    lines = ["# Analysis 2: Reasoning Text Mining\n"]

    # Extract features for all matched trades
    features = []
    for m in matched:
        f = extract_text_features(m.get('reasoning'))
        if f is None:
            continue
        f['outcome'] = m['trade']['outcome']
        f['win'] = m['trade']['outcome'] in ('WIN', 'BREAKEVEN')
        f['r'] = m['trade']['r_multiple']
        features.append(f)

    lines.append(f"Extracted features for **{len(features)}** of {len(matched)} trades.\n")

    # Feature distributions
    lines.append("## Feature Distributions\n")
    lines.append("| Feature | Median | Mean | Min | Max |")
    lines.append("|---|---|---|---|---|")
    for feat in ['word_count', 'price_count', 'hedging_count', 'confidence']:
        vals = [f[feat] for f in features]
        lines.append(f"| {feat} | {np.median(vals):.0f} | {np.mean(vals):.1f} | {min(vals)} | {max(vals)} |")

    # Feature vs WR correlations
    lines.append("\n## Feature → WR Correlations\n")
    lines.append("| Feature | Split | High n | High WR | Low n | Low WR | Delta | Fisher p |")
    lines.append("|---|---|---|---|---|---|---|---|")

    def split_test(features, feat_name, threshold, high_label="High", low_label="Low"):
        high = [f for f in features if f[feat_name] >= threshold]
        low = [f for f in features if f[feat_name] < threshold]
        if len(high) < 3 or len(low) < 3:
            return None
        h_w = sum(f['win'] for f in high)
        l_w = sum(f['win'] for f in low)
        h_wr = h_w / len(high) * 100
        l_wr = l_w / len(low) * 100
        table = [[h_w, len(high) - h_w], [l_w, len(low) - l_w]]
        _, p = stats.fisher_exact(table)
        return {
            'high_n': len(high), 'high_wr': h_wr,
            'low_n': len(low), 'low_wr': l_wr,
            'delta': h_wr - l_wr, 'p': p,
            'split': f"≥{threshold} vs <{threshold}",
        }

    # Test each feature with sensible splits
    tests = [
        ('word_count', np.median([f['word_count'] for f in features])),
        ('price_count', 8),  # Claimed threshold
        ('hedging_count', 3),  # ≤2 vs ≥3 (claimed: ≤2 adds +13.3pp)
        ('confidence', 80),
        ('confidence', 75),
    ]

    for feat, thresh in tests:
        r = split_test(features, feat, thresh)
        if r:
            sig = " *" if r['p'] < 0.05 else ""
            lines.append(f"| {feat} | {r['split']} | {r['high_n']} | {r['high_wr']:.1f}% | {r['low_n']} | {r['low_wr']:.1f}% | {r['delta']:+.1f}pp | {r['p']:.4f}{sig} |")

    # Boolean features
    for feat in ['has_fvg', 'all_aligned']:
        yes = [f for f in features if f[feat]]
        no = [f for f in features if not f[feat]]
        if len(yes) >= 3 and len(no) >= 3:
            y_w = sum(f['win'] for f in yes)
            n_w = sum(f['win'] for f in no)
            y_wr = y_w / len(yes) * 100
            n_wr = n_w / len(no) * 100
            table = [[y_w, len(yes) - y_w], [n_w, len(no) - n_w]]
            _, p = stats.fisher_exact(table)
            sig = " *" if p < 0.05 else ""
            lines.append(f"| {feat} | True vs False | {len(yes)} | {y_wr:.1f}% | {len(no)} | {n_wr:.1f}% | {y_wr - n_wr:+.1f}pp | {p:.4f}{sig} |")

    # Specific replication tests
    lines.append("\n## Replication of Claimed Predictors\n")

    # Claim 1: price_level_count ≥8 adds +17.4pp
    r = split_test(features, 'price_count', 8)
    lines.append("### Claim: price_level_count ≥8 adds +17.4pp\n")
    if r:
        lines.append(f"- ≥8 levels: {r['high_n']} trades, WR = {r['high_wr']:.1f}%")
        lines.append(f"- <8 levels: {r['low_n']} trades, WR = {r['low_wr']:.1f}%")
        lines.append(f"- **Delta: {r['delta']:+.1f}pp** (claimed: +17.4pp)")
        lines.append(f"- Fisher p = {r['p']:.4f}")
        if abs(r['delta'] - 17.4) < 5:
            lines.append(f"- **REPLICATES** (within 5pp of claim)\n")
        elif r['delta'] > 5:
            lines.append(f"- **PARTIALLY REPLICATES** (direction correct, magnitude differs)\n")
        else:
            lines.append(f"- **DOES NOT REPLICATE**\n")
    else:
        lines.append("- Insufficient data for split\n")

    # Claim 2: hesitation_score ≤2 adds +13.3pp
    # hedging_count is our proxy for hesitation_score
    r2 = split_test(features, 'hedging_count', 3)  # ≤2 = low hedging
    lines.append("### Claim: hesitation_score ≤2 adds +13.3pp\n")
    if r2:
        # Note: low hedging = "high" group in our split means hedging ≥3, which is BAD
        # We need to flip: ≤2 hedging should be the GOOD group
        low_hedge = [f for f in features if f['hedging_count'] <= 2]
        high_hedge = [f for f in features if f['hedging_count'] > 2]
        if len(low_hedge) >= 3 and len(high_hedge) >= 3:
            lh_wr = sum(f['win'] for f in low_hedge) / len(low_hedge) * 100
            hh_wr = sum(f['win'] for f in high_hedge) / len(high_hedge) * 100
            table = [[sum(f['win'] for f in low_hedge), len(low_hedge) - sum(f['win'] for f in low_hedge)],
                     [sum(f['win'] for f in high_hedge), len(high_hedge) - sum(f['win'] for f in high_hedge)]]
            _, p = stats.fisher_exact(table)
            delta = lh_wr - hh_wr
            lines.append(f"- Hedging ≤2: {len(low_hedge)} trades, WR = {lh_wr:.1f}%")
            lines.append(f"- Hedging >2: {len(high_hedge)} trades, WR = {hh_wr:.1f}%")
            lines.append(f"- **Delta: {delta:+.1f}pp** (claimed: +13.3pp)")
            lines.append(f"- Fisher p = {p:.4f}")
            if abs(delta - 13.3) < 5:
                lines.append(f"- **REPLICATES**\n")
            elif delta > 5:
                lines.append(f"- **PARTIALLY REPLICATES**\n")
            else:
                lines.append(f"- **DOES NOT REPLICATE**\n")
        else:
            lines.append("- Insufficient data for split\n")

    # Grade vs outcome
    lines.append("### Setup Grade vs Outcome\n")
    grade_stats = defaultdict(list)
    for f in features:
        grade_stats[f['grade']].append(f)
    lines.append("| Grade | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for g in sorted(grade_stats.keys()):
        fs = grade_stats[g]
        wr = sum(f['win'] for f in fs) / len(fs) * 100
        avg_r = np.mean([f['r'] for f in fs])
        lines.append(f"| {g} | {len(fs)} | {wr:.1f}% | {avg_r:+.3f}R |")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 3: PER-STEP EVALUATION ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analysis_3(matched):
    lines = ["# Analysis 3: Per-Step Evaluation Analysis\n"]
    lines.append("Which steps in the AI's 7-step evaluation actually predict outcomes?\n")

    records = []
    for m in matched:
        p = m.get('reasoning')
        if not p:
            continue
        r = p.get('reasoning', {}) or {}
        t = m['trade']

        daily = r.get('daily_bias', {}) or {}
        h4 = r.get('h4_alignment', {}) or {}
        h1 = r.get('h1_setup', {}) or {}
        sweep = r.get('liquidity_sweep', {}) or {}
        m15 = r.get('m15_confirmation', {}) or {}

        records.append({
            'win': t['outcome'] in ('WIN', 'BREAKEVEN'),
            'r': t['r_multiple'],
            # Step 1: Daily bias
            'daily_confidence': daily.get('confidence', 'unknown'),
            'daily_direction': daily.get('direction', 'unknown'),
            # Step 2: H4 alignment
            'h4_aligned': h4.get('aligned', False),
            # Step 3: H1 setup
            'poi_type': h1.get('poi_type', 'unknown'),
            'fib_zone': h1.get('zone', 'unknown'),
            'fib_pct': h1.get('fib_retracement_pct', 0),
            # Step 4: Liquidity sweep
            'sweep_detected': sweep.get('detected', False),
            'sweep_type': sweep.get('pool_type', 'none'),
            'sweep_quality': sweep.get('sweep_quality', 'unknown'),
            # Step 5: M15 confirmation
            'choch_detected': m15.get('choch_detected', False),
            'displacement_quality': m15.get('displacement_quality', 'unknown'),
            'displacement_ratio': m15.get('displacement_candle_body_vs_avg_ratio', 0),
        })

    df = pd.DataFrame(records)
    lines.append(f"Extracted step-level data for **{len(df)}** trades.\n")

    def step_split(df, col, val_map=None):
        """Split by column value and compare WR."""
        results = []
        if val_map:
            for label, mask in val_map.items():
                sub = df[mask]
                if len(sub) < 3:
                    continue
                wr = sub['win'].mean() * 100
                avg_r = sub['r'].mean()
                results.append({'label': label, 'n': len(sub), 'wr': wr, 'avg_r': avg_r})
        else:
            for val in sorted(df[col].unique()):
                sub = df[df[col] == val]
                if len(sub) < 3:
                    continue
                wr = sub['win'].mean() * 100
                avg_r = sub['r'].mean()
                results.append({'label': str(val), 'n': len(sub), 'wr': wr, 'avg_r': avg_r})
        return results

    # Step 1: Daily bias confidence
    lines.append("## Step 1: Daily Bias Confidence\n")
    lines.append("| Confidence | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for r in step_split(df, 'daily_confidence'):
        lines.append(f"| {r['label']} | {r['n']} | {r['wr']:.1f}% | {r['avg_r']:+.3f}R |")

    # Fisher test: high vs non-high
    high_d = df[df['daily_confidence'] == 'high']
    other_d = df[df['daily_confidence'] != 'high']
    if len(high_d) >= 3 and len(other_d) >= 3:
        hw = high_d['win'].sum()
        ow = other_d['win'].sum()
        table = [[hw, len(high_d) - hw], [ow, len(other_d) - ow]]
        _, p = stats.fisher_exact(table)
        lines.append(f"\nFisher p (high vs other): {p:.4f}")
        lines.append(f"**{'PREDICTIVE' if p < 0.1 else 'NOT PREDICTIVE'}**\n")

    # Step 2: H4 alignment
    lines.append("## Step 2: H4 Alignment\n")
    lines.append("| Aligned | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for val in [True, False]:
        sub = df[df['h4_aligned'] == val]
        if len(sub) >= 3:
            wr = sub['win'].mean() * 100
            avg_r = sub['r'].mean()
            lines.append(f"| {val} | {len(sub)} | {wr:.1f}% | {avg_r:+.3f}R |")

    aligned = df[df['h4_aligned']]
    not_aligned = df[~df['h4_aligned']]
    if len(aligned) >= 3 and len(not_aligned) >= 3:
        table = [[aligned['win'].sum(), len(aligned) - aligned['win'].sum()],
                 [not_aligned['win'].sum(), len(not_aligned) - not_aligned['win'].sum()]]
        _, p = stats.fisher_exact(table)
        lines.append(f"\nFisher p: {p:.4f}")
        lines.append(f"**{'PREDICTIVE' if p < 0.1 else 'NOT PREDICTIVE'}**\n")
    else:
        lines.append(f"\n(Insufficient variation to test)\n")

    # Step 3: H1 POI type
    lines.append("## Step 3: H1 POI Type\n")
    lines.append("| POI Type | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for r in step_split(df, 'poi_type'):
        lines.append(f"| {r['label']} | {r['n']} | {r['wr']:.1f}% | {r['avg_r']:+.3f}R |")

    # Fib zone
    lines.append("\n### Fibonacci Zone\n")
    lines.append("| Zone | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for r in step_split(df, 'fib_zone'):
        lines.append(f"| {r['label']} | {r['n']} | {r['wr']:.1f}% | {r['avg_r']:+.3f}R |")

    # Step 4: Liquidity sweep
    lines.append("\n## Step 4: Liquidity Sweep\n")
    lines.append("| Sweep Detected | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for val in [True, False]:
        sub = df[df['sweep_detected'] == val]
        if len(sub) >= 3:
            wr = sub['win'].mean() * 100
            avg_r = sub['r'].mean()
            lines.append(f"| {val} | {len(sub)} | {wr:.1f}% | {avg_r:+.3f}R |")

    swept = df[df['sweep_detected']]
    not_swept = df[~df['sweep_detected']]
    if len(swept) >= 3 and len(not_swept) >= 3:
        table = [[swept['win'].sum(), len(swept) - swept['win'].sum()],
                 [not_swept['win'].sum(), len(not_swept) - not_swept['win'].sum()]]
        _, p = stats.fisher_exact(table)
        lines.append(f"\nFisher p: {p:.4f}")
        lines.append(f"**{'PREDICTIVE' if p < 0.1 else 'NOT PREDICTIVE'}**\n")
    else:
        lines.append("\n")

    # Sweep quality
    lines.append("### Sweep Quality\n")
    lines.append("| Quality | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for r in step_split(df, 'sweep_quality'):
        lines.append(f"| {r['label']} | {r['n']} | {r['wr']:.1f}% | {r['avg_r']:+.3f}R |")

    # Step 5: M15 confirmation
    lines.append("\n## Step 5: M15 Displacement Quality\n")
    lines.append("| Quality | Count | WR | Avg R |")
    lines.append("|---|---|---|---|")
    for r in step_split(df, 'displacement_quality'):
        lines.append(f"| {r['label']} | {r['n']} | {r['wr']:.1f}% | {r['avg_r']:+.3f}R |")

    # Displacement ratio split
    med_ratio = df['displacement_ratio'].median()
    high_disp = df[df['displacement_ratio'] >= med_ratio]
    low_disp = df[df['displacement_ratio'] < med_ratio]
    if len(high_disp) >= 3 and len(low_disp) >= 3:
        hw = high_disp['win'].mean() * 100
        lw = low_disp['win'].mean() * 100
        table = [[high_disp['win'].sum(), len(high_disp) - high_disp['win'].sum()],
                 [low_disp['win'].sum(), len(low_disp) - low_disp['win'].sum()]]
        _, p = stats.fisher_exact(table)
        lines.append(f"\nDisplacement ratio ≥{med_ratio:.1f}: WR={hw:.1f}% (n={len(high_disp)})")
        lines.append(f"Displacement ratio <{med_ratio:.1f}: WR={lw:.1f}% (n={len(low_disp)})")
        lines.append(f"Fisher p: {p:.4f}")
        lines.append(f"**{'PREDICTIVE' if p < 0.1 else 'NOT PREDICTIVE'}**\n")

    # Summary table
    lines.append("## Summary: Which Steps Predict Outcomes?\n")
    lines.append("| Step | Feature | Predictive? | Delta | p-value |")
    lines.append("|---|---|---|---|---|")

    # Compile summary from above analyses
    step_results = []

    # Daily bias
    if len(high_d) >= 3 and len(other_d) >= 3:
        delta = high_d['win'].mean() * 100 - other_d['win'].mean() * 100
        _, p = stats.fisher_exact([[high_d['win'].sum(), len(high_d) - high_d['win'].sum()],
                                   [other_d['win'].sum(), len(other_d) - other_d['win'].sum()]])
        lines.append(f"| 1. Daily Bias | high vs other confidence | {'YES' if p < 0.1 else 'NO'} | {delta:+.1f}pp | {p:.4f} |")

    # H4
    if len(aligned) >= 3 and len(not_aligned) >= 3:
        delta = aligned['win'].mean() * 100 - not_aligned['win'].mean() * 100
        _, p = stats.fisher_exact([[aligned['win'].sum(), len(aligned) - aligned['win'].sum()],
                                   [not_aligned['win'].sum(), len(not_aligned) - not_aligned['win'].sum()]])
        lines.append(f"| 2. H4 Alignment | aligned vs not | {'YES' if p < 0.1 else 'NO'} | {delta:+.1f}pp | {p:.4f} |")

    # Sweep
    if len(swept) >= 3 and len(not_swept) >= 3:
        delta = swept['win'].mean() * 100 - not_swept['win'].mean() * 100
        _, p = stats.fisher_exact([[swept['win'].sum(), len(swept) - swept['win'].sum()],
                                   [not_swept['win'].sum(), len(not_swept) - not_swept['win'].sum()]])
        lines.append(f"| 4. Liq Sweep | detected vs not | {'YES' if p < 0.1 else 'NO'} | {delta:+.1f}pp | {p:.4f} |")

    # Displacement
    if len(high_disp) >= 3 and len(low_disp) >= 3:
        delta = high_disp['win'].mean() * 100 - low_disp['win'].mean() * 100
        _, p = stats.fisher_exact([[high_disp['win'].sum(), len(high_disp) - high_disp['win'].sum()],
                                   [low_disp['win'].sum(), len(low_disp) - low_disp['win'].sum()]])
        lines.append(f"| 5. M15 Displacement | high vs low ratio | {'YES' if p < 0.1 else 'NO'} | {delta:+.1f}pp | {p:.4f} |")

    lines.append("\n## So What?\n")
    lines.append("Steps that DON'T predict outcomes are adding noise, not signal.")
    lines.append("Consider removing non-predictive steps from the prompt to reduce cost and latency.")
    lines.append("Steps that DO predict should be weighted more heavily in confidence scoring.")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYSIS 4: AUTOCORRELATION BASELINES
# ═══════════════════════════════════════════════════════════════════════════════

def analysis_4():
    lines = ["# Analysis 4: All-Instrument Autocorrelation Baselines\n"]

    symbols = ['XAUUSD', 'US30_cash', 'USDJPY', 'GBPJPY', 'GBPUSD']
    results = {}

    for sym in symbols:
        fpath = DATA_DIR / f"{sym}_H1.csv"
        if not fpath.exists():
            continue
        df = pd.read_csv(fpath)
        df['time'] = pd.to_datetime(df['time'])
        df['return'] = df['close'].pct_change()
        returns = df['return'].dropna()

        # Full dataset lag-1 autocorrelation
        full_ac = returns.autocorr(lag=1)

        # Current 20-period
        current_20 = returns.iloc[-20:].autocorr(lag=1) if len(returns) >= 20 else np.nan

        # 90-day rolling (90 days * 24 H1 candles, but trading hours only ~17/day)
        # Use 90 * 17 ≈ 1530 candles, or just use 90-day calendar windows
        window = 1530
        rolling_ac = []
        for i in range(window, len(returns), window // 10):
            chunk = returns.iloc[i - window:i]
            ac = chunk.autocorr(lag=1)
            if not np.isnan(ac):
                rolling_ac.append(ac)

        rolling_mean = np.mean(rolling_ac) if rolling_ac else np.nan
        rolling_std = np.std(rolling_ac) if rolling_ac else np.nan
        warning_threshold = rolling_mean + 2 * rolling_std if not np.isnan(rolling_std) else np.nan

        results[sym] = {
            'full_dataset': round(full_ac, 6),
            'current_20': round(current_20, 6) if not np.isnan(current_20) else None,
            'rolling_90d_mean': round(rolling_mean, 6) if not np.isnan(rolling_mean) else None,
            'rolling_90d_std': round(rolling_std, 6) if not np.isnan(rolling_std) else None,
            'warning_threshold': round(warning_threshold, 6) if not np.isnan(warning_threshold) else None,
            'n_candles': len(returns),
        }

    # Save JSON
    json_path = Path("knowledge_base/meta")
    json_path.mkdir(parents=True, exist_ok=True)
    with open(json_path / "autocorrelation_baseline.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Format markdown
    lines.append("## Lag-1 H1 Return Autocorrelation\n")
    lines.append("| Instrument | N Candles | Full Dataset | Current 20 | 90-day Mean | 90-day Std | Warning Threshold |")
    lines.append("|---|---|---|---|---|---|---|")

    for sym in symbols:
        r = results.get(sym, {})
        if not r:
            continue
        current = r['current_20']
        warning = r['warning_threshold']
        flag = ""
        if current is not None and warning is not None and abs(current) > abs(warning):
            flag = " ⚠️"

        lines.append(f"| {sym} | {r['n_candles']} | {r['full_dataset']:.4f} | {current if current else '—':.4f}{flag} | {r['rolling_90d_mean']:.4f} | {r['rolling_90d_std']:.4f} | ±{abs(warning):.4f} |")

    lines.append("\n## Interpretation\n")
    lines.append("- Lag-1 autocorrelation near 0 = random walk (no momentum)")
    lines.append("- Positive = momentum (continuation), negative = mean-reversion")
    lines.append("- Values exceeding the warning threshold (mean + 2σ) suggest regime change")
    lines.append("- The OB retest strategy depends on positive autocorrelation (momentum after BOS)")
    lines.append(f"\nSaved to `knowledge_base/meta/autocorrelation_baseline.json`")

    return "\n".join(lines), results


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("SPRINT ALPHA — FOUR ANALYSES")
    print("=" * 70)

    print("\nLoading data...")
    matched, raw_parsed = load_primary_data()
    print(f"  Matched trades: {len(matched)}")
    print(f"  With reasoning: {sum(1 for m in matched if m['reasoning'])}")

    print("\n>>> Analysis 1: R-Multiple Decomposition")
    doc1 = analysis_1(matched)
    with open(OUTPUT_DIR / "r_multiple_analysis.md", 'w') as f:
        f.write(doc1)
    print("  Saved r_multiple_analysis.md")

    print("\n>>> Analysis 2: Reasoning Text Mining")
    doc2 = analysis_2(matched)
    with open(OUTPUT_DIR / "reasoning_text_mining.md", 'w') as f:
        f.write(doc2)
    print("  Saved reasoning_text_mining.md")

    print("\n>>> Analysis 3: Per-Step Evaluation Analysis")
    doc3 = analysis_3(matched)
    with open(OUTPUT_DIR / "per_step_evaluation_analysis.md", 'w') as f:
        f.write(doc3)
    print("  Saved per_step_evaluation_analysis.md")

    print("\n>>> Analysis 4: Autocorrelation Baselines")
    doc4, ac_results = analysis_4()
    with open(OUTPUT_DIR / "autocorrelation_baselines.md", 'w') as f:
        f.write(doc4)
    print("  Saved autocorrelation_baselines.md + knowledge_base/meta/autocorrelation_baseline.json")

    print("\n" + "=" * 70)
    print("ALL FOUR ANALYSES COMPLETE")
    print("=" * 70)
