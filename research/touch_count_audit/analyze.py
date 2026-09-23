"""Touch-count gate audit — counterfactual + per-instrument + production stats.

Audits permissions._reject_if_touch_count_too_high (threshold >= 2 reject)
against:
  1. A1 backtest realized R (75 filled CANDs, v1 production-driver, post-V3 prompt)
  2. A2 v2-active backtest realized R (37 CANDs, v2 production-driver)
  3. Production candidate_features_log shadow data (1142 rows from research period)

Outputs to stdout; piped to artifacts.
"""
import json
import math
import re
from collections import Counter, defaultdict
from glob import glob


def wilson_ci(wins, n, z=1.96):
    if n == 0:
        return (None, None)
    p = wins / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (center - half, center + half)


def bootstrap_ci(rs, B=5000, alpha=0.05, seed=42):
    import random
    if len(rs) == 0:
        return (None, None)
    rng = random.Random(seed)
    means = []
    for _ in range(B):
        s = [rs[rng.randrange(len(rs))] for _ in rs]
        means.append(sum(s) / len(s))
    means.sort()
    lo = means[int(B * alpha / 2)]
    hi = means[int(B * (1 - alpha / 2))]
    return (lo, hi)


def get_dir_touch(r):
    direction = r.get('out_direction') or r.get('ai_direction_evaluated')
    if direction == 'LONG':
        return r.get('h1_opp_ob_touch_long', -1)
    elif direction == 'SHORT':
        return r.get('h1_opp_ob_touch_short', -1)
    else:
        return r.get('h1_opp_ob_touch', -1)


def parse_touch_from_response(raw):
    if not isinstance(raw, str):
        return None
    # patterns observed: "touches=N", "touches: N", "with touches=N", "touches=1"
    patterns = [
        r'"touches"\s*:\s*(\d+)',
        r'touches\s*=\s*(\d+)',
        r'touch[_\s]?count\s*[:=]\s*(\d+)',
        r'touches\s+(\d+)',
        r'touched\s+(\d+)\s+time',
    ]
    for p in patterns:
        m = re.search(p, raw, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None


def block_a1():
    print("=" * 80)
    print("PART 1: A1 backtest (v1 production-driver, post-V3 prompt, 12 slices)")
    print("=" * 80)
    recs = []
    with open('research/phase1_full_extraction/merged_data.jsonl') as f:
        for line in f:
            recs.append(json.loads(line))
    filled = [r for r in recs if r.get('out_outcome') in ('WIN', 'LOSS', 'BE')]
    print(f"\nA1 logger rows: {len(recs)}")
    print(f"A1 filled CANDs: {len(filled)}")

    by_touch = defaultdict(list)
    for r in filled:
        t = get_dir_touch(r)
        if t is None or t < 0:
            t = 'missing'
        # bucket touch>=3 together
        if isinstance(t, int) and t >= 3:
            t = '>=3'
        by_touch[t].append(r)

    print("\nA1 filled — direction-aware touch (Track A semantics, opposing-OB):")
    for t in sorted(by_touch.keys(), key=lambda x: (isinstance(x, str), x)):
        rows = by_touch[t]
        rs = [r.get('out_r_multiple', 0) for r in rows]
        n = len(rs)
        wins = sum(1 for r in rows if r.get('out_outcome') == 'WIN')
        if n > 0:
            wr = wins / n
            wlo, whi = wilson_ci(wins, n)
            mean = sum(rs) / n
            blo, bhi = bootstrap_ci(rs)
            print(
                f"  touch={str(t):>8s}: n={n:>3d}, wins={wins:>2d}, WR={wr*100:>5.1f}% "
                f"[{wlo*100:>4.1f},{whi*100:>4.1f}], "
                f"Exp={mean:+.3f}R [{blo:+.3f},{bhi:+.3f}], totR={sum(rs):+.2f}"
            )

    # Threshold sweep
    print("\nThreshold counterfactual on A1 filled set (gate semantics: reject if touch >= X):")
    print(f"{'X':>4} {'n_pass':>7} {'n_rej':>6} {'pass WR%':>9} {'pass ExpR':>10} {'rej WR%':>8} {'rej ExpR':>10} {'pass totR':>10} {'rej totR':>10}")
    for X in [1, 2, 3, 4, 5, 999]:
        pass_rows = [r for r in filled if (get_dir_touch(r) or 0) < X or (get_dir_touch(r) or 0) < 0]
        rej_rows = [r for r in filled if (get_dir_touch(r) or 0) >= X and (get_dir_touch(r) or 0) >= 0]
        pass_rs = [r.get('out_r_multiple', 0) for r in pass_rows]
        rej_rs = [r.get('out_r_multiple', 0) for r in rej_rows]
        pass_w = sum(1 for r in pass_rows if r.get('out_outcome') == 'WIN')
        rej_w = sum(1 for r in rej_rows if r.get('out_outcome') == 'WIN')
        pass_n = len(pass_rs)
        rej_n = len(rej_rs)
        if pass_n + rej_n > 0:
            print(
                f"{X:>4} {pass_n:>7} {rej_n:>6} "
                f"{(pass_w/pass_n*100 if pass_n else 0):>9.1f} "
                f"{(sum(pass_rs)/pass_n if pass_n else 0):>+10.3f} "
                f"{(rej_w/rej_n*100 if rej_n else 0):>8.1f} "
                f"{(sum(rej_rs)/rej_n if rej_n else 0):>+10.3f} "
                f"{sum(pass_rs):>+10.2f} {sum(rej_rs):>+10.2f}"
            )

    # Per-symbol
    print("\nA1 per-symbol stratification:")
    for symbol in sorted(set(r['symbol'] for r in filled)):
        sym_rows = [r for r in filled if r['symbol'] == symbol]
        print(f"\n  {symbol} (n_filled={len(sym_rows)}):")
        sub = defaultdict(list)
        for r in sym_rows:
            t = get_dir_touch(r)
            if t is None or t < 0:
                t = 'missing'
            if isinstance(t, int) and t >= 3:
                t = '>=3'
            sub[t].append(r)
        for t in sorted(sub.keys(), key=lambda x: (isinstance(x, str), x)):
            rows = sub[t]
            rs = [r.get('out_r_multiple', 0) for r in rows]
            n = len(rs)
            wins = sum(1 for r in rows if r.get('out_outcome') == 'WIN')
            if n > 0:
                wr = wins / n
                wlo, whi = wilson_ci(wins, n)
                mean = sum(rs) / n
                print(
                    f"    touch={str(t):>8s}: n={n:>2d}, WR={wr*100:>5.1f}% "
                    f"[{wlo*100:>4.1f},{whi*100:>4.1f}], Exp={mean:+.3f}R"
                )

    # Direction stratification (LONG vs SHORT) for completeness
    print("\nA1 by direction:")
    for direction in ('LONG', 'SHORT'):
        dir_rows = [r for r in filled if (r.get('out_direction') or '') == direction]
        if not dir_rows:
            continue
        n = len(dir_rows)
        wins = sum(1 for r in dir_rows if r.get('out_outcome') == 'WIN')
        rs = [r.get('out_r_multiple', 0) for r in dir_rows]
        print(f"  {direction}: n={n}, WR={wins/n*100:.1f}%, Exp={sum(rs)/n:+.3f}R")

    return filled


def block_a2():
    print("\n" + "=" * 80)
    print("PART 2: A2 v2-active backtest (v2 production-driver, post-V3 prompt)")
    print("=" * 80)
    cands = []
    for sp in sorted(glob('research/a2_v2_active_backtest/slices/*/all_results.json')):
        d = json.load(open(sp))
        for r in d['results']:
            if r.get('decision') == 'CANDIDATE':
                r['_slice'] = sp.split('/')[-2]
                cands.append(r)
    filled = [r for r in cands if r.get('outcome') in ('WIN', 'LOSS', 'BE')]
    print(f"\nA2 CANDs: {len(cands)}")
    print(f"A2 filled: {len(filled)}")
    if filled:
        wr = sum(1 for r in filled if r.get('outcome') == 'WIN') / len(filled)
        rs = [r.get('r_multiple', 0) for r in filled]
        print(f"  Fleet WR: {wr*100:.1f}%, Exp: {sum(rs)/len(rs):+.3f}R, total R: {sum(rs):+.2f}")

    # Parse touch from raw_response
    by_touch = defaultdict(list)
    for r in filled:
        t = parse_touch_from_response(r.get('raw_response', ''))
        if t is None:
            t = 'unparsed'
        elif t >= 3:
            t = '>=3'
        by_touch[t].append(r)

    print("\nA2 filled by touch_count (parsed from raw_response — AI-cited):")
    for t in sorted(by_touch.keys(), key=lambda x: (isinstance(x, str), x)):
        rows = by_touch[t]
        rs = [r.get('r_multiple', 0) for r in rows]
        n = len(rs)
        wins = sum(1 for r in rows if r.get('outcome') == 'WIN')
        if n > 0:
            wr = wins / n
            wlo, whi = wilson_ci(wins, n)
            mean = sum(rs) / n
            print(
                f"  touch={str(t):>8s}: n={n:>2d}, WR={wr*100:>5.1f}% "
                f"[{wlo*100:>4.1f},{whi*100:>4.1f}], Exp={mean:+.3f}R, totR={sum(rs):+.2f}"
            )

    # Threshold sweep
    print("\nA2 threshold counterfactual (parseable touches only):")
    parsed = [(r, parse_touch_from_response(r.get('raw_response', ''))) for r in filled]
    parsed_with_t = [(r, t) for r, t in parsed if t is not None]
    print(f"  Parseable: {len(parsed_with_t)} / {len(filled)}")
    print(f"\n{'X':>4} {'n_pass':>7} {'n_rej':>6} {'pass WR%':>9} {'pass ExpR':>10} {'pass totR':>10}")
    for X in [1, 2, 3, 4, 5, 999]:
        pass_set = [r for r, t in parsed_with_t if t < X]
        rej_set = [r for r, t in parsed_with_t if t >= X]
        if pass_set or rej_set:
            pass_w = sum(1 for r in pass_set if r.get('outcome') == 'WIN')
            pass_rs = [r.get('r_multiple', 0) for r in pass_set]
            pass_n = len(pass_set)
            print(
                f"{X:>4} {pass_n:>7} {len(rej_set):>6} "
                f"{(pass_w/pass_n*100 if pass_n else 0):>9.1f} "
                f"{(sum(pass_rs)/pass_n if pass_n else 0):>+10.3f} "
                f"{sum(pass_rs):>+10.2f}"
            )

    # Per-symbol A2
    print("\nA2 per-symbol stratification:")
    for symbol in sorted(set(r['symbol'] for r in filled)):
        sym_rows = [r for r in filled if r['symbol'] == symbol]
        print(f"\n  {symbol} (n={len(sym_rows)}):")
        for r in sym_rows[:0]:  # placeholder
            pass
        sub = defaultdict(list)
        for r in sym_rows:
            t = parse_touch_from_response(r.get('raw_response', ''))
            if t is None:
                t = 'unparsed'
            elif t >= 3:
                t = '>=3'
            sub[t].append(r)
        for t in sorted(sub.keys(), key=lambda x: (isinstance(x, str), x)):
            rows = sub[t]
            rs = [r.get('r_multiple', 0) for r in rows]
            n = len(rs)
            wins = sum(1 for r in rows if r.get('outcome') == 'WIN')
            if n > 0:
                wr = wins / n
                wlo, whi = wilson_ci(wins, n)
                mean = sum(rs) / n
                print(
                    f"    touch={str(t):>8s}: n={n:>2d}, WR={wr*100:>5.1f}% "
                    f"[{wlo*100:>4.1f},{whi*100:>4.1f}], Exp={mean:+.3f}R"
                )

    return filled


def block_production_logger():
    print("\n" + "=" * 80)
    print("PART 3: Production candidate_features_log.jsonl shadow data")
    print("=" * 80)
    rows = []
    with open('shadow_logs/candidate_features_log.jsonl') as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    print(f"\nProduction logger rows: {len(rows)}")
    decs = Counter(r.get('decision') for r in rows)
    print(f"Decisions: {decs}")

    # The production logger captures `mso_h1_ob_touch_counts` (LIST of all unmitigated H1 OB
    # touches in MSO). The gate matches the OB by entry_price overlap, so we need to know
    # whether the AI's chosen entry overlaps any OB. The shadow log's
    # `mso_h1_ob_touch_counts` is the union; the gate's matched OB is a subset.
    # Best proxy: max(touch_counts) at decision==CANDIDATE.

    cands = [r for r in rows if r.get('decision') == 'CANDIDATE']
    print(f"\nProduction CANDIDATEs in log: {len(cands)}")
    syms = Counter(r.get('symbol') for r in cands)
    print(f"By symbol: {syms}")

    # Distribution of mso_h1_ob_touch_counts (max across all OBs in MSO at CAND time)
    max_touch_dist = Counter()
    avg_touch_dist = Counter()
    no_ob_count = 0
    has_ob_at_2plus = 0
    for r in cands:
        tc_list = r.get('mso_h1_ob_touch_counts') or []
        if not tc_list:
            no_ob_count += 1
            continue
        max_t = max(tc_list)
        max_touch_dist[max_t] += 1
        if max_t >= 2:
            has_ob_at_2plus += 1
    print(f"\nProduction CANDs distribution of MAX(mso_h1_ob_touch_counts):")
    for t in sorted(max_touch_dist.keys()):
        print(f"  max touch={t}: n={max_touch_dist[t]} ({max_touch_dist[t]/len(cands)*100:.1f}%)")
    if no_ob_count:
        print(f"  (no H1 OBs in MSO: {no_ob_count} = {no_ob_count/len(cands)*100:.1f}%)")
    print(f"\nFraction of CANDs with ANY unmitigated H1 OB at touch>=2: "
          f"{has_ob_at_2plus}/{len(cands)} = {has_ob_at_2plus/len(cands)*100:.1f}%")

    # Note: this overstates rejection because the gate matches the OB at entry_price,
    # not max-overlap of any OB. But it bounds the gate's reach.

    # Per-symbol
    print(f"\nProduction CANDs by symbol × max touch:")
    by_sym = defaultdict(lambda: Counter())
    for r in cands:
        tc_list = r.get('mso_h1_ob_touch_counts') or []
        if tc_list:
            by_sym[r.get('symbol')][max(tc_list)] += 1
        else:
            by_sym[r.get('symbol')]['no_ob'] += 1
    for sym, dist in sorted(by_sym.items()):
        total = sum(dist.values())
        rejects = sum(c for t, c in dist.items() if isinstance(t, int) and t >= 2)
        print(f"  {sym}: total={total}, max-touch>=2 = {rejects} ({rejects/total*100:.1f}%)")
        for t in sorted(dist.keys(), key=lambda x: (isinstance(x, str), x)):
            print(f"    {t}: {dist[t]}")


if __name__ == '__main__':
    a1_filled = block_a1()
    a2_filled = block_a2()
    block_production_logger()

    print("\n\n" + "=" * 80)
    print("SUMMARY (gate currently rejects touches >= 2)")
    print("=" * 80)
    # A1 fleet impact
    rej_a1 = [r for r in a1_filled if (get_dir_touch(r) or 0) >= 2]
    pass_a1 = [r for r in a1_filled if (get_dir_touch(r) or 0) < 2 or (get_dir_touch(r) or 0) < 0]
    rej_r = [r.get('out_r_multiple', 0) for r in rej_a1]
    pass_r = [r.get('out_r_multiple', 0) for r in pass_a1]
    print(f"\nA1 (75 filled):")
    print(f"  WITHOUT gate (current data): n=75, totR={sum(r.get('out_r_multiple',0) for r in a1_filled):+.2f}")
    print(f"  WITH gate ACTIVE (rej touches>=2): n_passed={len(pass_a1)}, totR={sum(pass_r):+.2f}")
    print(f"  Delta from gate = {sum(pass_r) - sum(r.get('out_r_multiple',0) for r in a1_filled):+.2f}R "
          f"(LOST = {sum(rej_r):+.2f}R because gate would have removed them)")

    # A2 fleet impact (only parseable)
    a2_with_t = []
    for r in a2_filled:
        t = parse_touch_from_response(r.get('raw_response', ''))
        a2_with_t.append((r, t))
    a2_parseable = [(r, t) for r, t in a2_with_t if t is not None]
    a2_rej = [r for r, t in a2_parseable if t >= 2]
    a2_pass = [r for r, t in a2_parseable if t < 2]
    rej_r2 = [r.get('r_multiple', 0) for r in a2_rej]
    pass_r2 = [r.get('r_multiple', 0) for r in a2_pass]
    print(f"\nA2 (parseable filled, n={len(a2_parseable)}):")
    print(f"  Total realized totR = {sum(r.get('r_multiple',0) for r in a2_filled):+.2f}R (over all {len(a2_filled)})")
    print(f"  Parseable WITHOUT gate: n={len(a2_parseable)}, totR={sum(r.get('r_multiple',0) for r,_ in a2_parseable):+.2f}")
    print(f"  WITH gate ACTIVE: n_passed={len(a2_pass)}, totR={sum(pass_r2):+.2f}")
    print(f"  Delta from gate = {-sum(rej_r2):+.2f}R (LOST = {sum(rej_r2):+.2f}R)")
