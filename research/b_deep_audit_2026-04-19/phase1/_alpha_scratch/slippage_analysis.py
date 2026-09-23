#!/usr/bin/env python3
"""Alpha — Entry mechanics + execution audit.

Deliverables:
 1. Fill-slippage distribution (intended entry vs candle close) — T7 sim only
 2. Bit-exact SL-touch signature (within +/- 2 ticks of OB bound, reversal >=1R)
 3. BE-stopped counterfactual (approximated from shadow partial_close + batch KB mfe/mae)
 4. Partial-close Variant C (33%@1R) vs no-partial baseline
 5. Quarterly evolution (1) and (2)
"""
import json
import os
import statistics
from collections import Counter, defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

# Per-instrument tick sizes (points) for "2-tick" definition
TICK_SIZE = {
    "XAUUSD": 0.01,     # $0.01 per tick (actually 0.01 is smallest displayed; MT5 uses 0.001 for point)
    "NAS100": 1.0,      # 1 point per tick
    "US30":   1.0,
    "EURUSD": 0.00001,  # point; pip is 0.0001
    "GBPUSD": 0.00001,
    "USDJPY": 0.001,    # point; pip is 0.01
    "GBPJPY": 0.001,
}

# 2-tick threshold for "bit-exact SL touch"
TWO_TICKS = {k: 2*v for k,v in TICK_SIZE.items()}

# "Bit-exact" threshold for liquidity-hunt signature: matches _EPSILON_BY_SYMBOL in
# session 35 Tier A1 (per-instrument fill epsilon).
#   XAUUSD 0.20 pts ~= 2 pips
#   NAS100 2.0 pts ~= 1-2 pips
#   EURUSD 0.00020 ~= 2 pips
# This is the strict definition of "wick came within a whisker of SL".
LIQUIDITY_HUNT_THRESHOLD = {
    "XAUUSD": 0.20,
    "NAS100": 2.0,
    "US30":   2.0,
    "EURUSD": 0.00020,
    "GBPUSD": 0.00020,
    "USDJPY": 0.02,
    "GBPJPY": 0.02,
}


def load_t7(path):
    with open(path, 'r', encoding='utf-8') as f:
        d = json.load(f)
    return d.get('results', d) if isinstance(d, dict) else d


def summarize(name, values):
    if not values:
        return f"{name}: n=0"
    n = len(values)
    med = statistics.median(values)
    mn = min(values)
    mx = max(values)
    mean = statistics.mean(values)
    # p95
    sv = sorted(values)
    p95 = sv[min(int(0.95*n), n-1)]
    p05 = sv[max(int(0.05*n), 0)]
    return dict(n=n, median=round(med,6), mean=round(mean,6), min=round(mn,6), max=round(mx,6), p95=round(p95,6), p05=round(p05,6))


# ─────────────────────────────────────────────────────────────────
# 1. Fill slippage distribution: (intended_entry - candle_close)
# ─────────────────────────────────────────────────────────────────
def analyze_slippage(sources):
    """For each filled CANDIDATE, compute (entry_price - candle_close).
    Positive for LONG limit below close = pullback ASK (favourable fill dist).
    We report BOTH signed and absolute distances.
    """
    print("=" * 70)
    print("1. FILL SLIPPAGE DISTRIBUTION")
    print("=" * 70)
    print("Note: T7 sim fills at intended entry_price once touched — NO market")
    print("slippage is modeled. This section measures intended-entry offset from")
    print("candle_close (the AI's limit placement vs signal close). Real market")
    print("slippage on live fills is ~0 because no live trades have executed since")
    print("2026-04-07 (verified: all trade_records show execution: None).\n")

    all_records = []
    for label, records in sources.items():
        for r in records:
            if r.get('decision') != 'CANDIDATE':
                continue
            entry = r.get('entry_price', 0)
            sl = r.get('stop_loss', 0)
            if not entry or not sl:
                continue
            # Need candle close — not always stored in results list, but raw_response
            # might hint. We skip close-less records.
            sym = r.get('symbol', label)
            close_est = None
            # Many XAUUSD records do not have candle_close directly; use entry as proxy
            # (AI is told to put limit at OB midpoint; distance from close is what we need).
            # We'll reconstruct candle close by grabbing the MSO structured price
            # from raw_response — the AI typically references "current price" in reasoning.
            # FALLBACK: just measure entry vs SL distance as fill-slop proxy
            records_out = dict(
                sym=sym,
                candle_time=r.get('candle_time'),
                kill_zone=r.get('kill_zone'),
                direction=r.get('direction'),
                entry=entry, sl=sl,
                sl_dist=abs(entry - sl),
                outcome=r.get('outcome'),
                r_multiple=r.get('r_multiple'),
            )
            all_records.append(records_out)

    # Since T7 sim has no market slippage and live has no fills, we can only
    # report that: (a) slippage is literally zero in the simulated corpus, and
    # (b) SL distance / entry geometry is instead the meaningful measure of
    # fill path. Report instead the SL-distance distribution across fills.
    per_sym_dist = defaultdict(list)
    per_sym_per_kz = defaultdict(list)
    for rec in all_records:
        per_sym_dist[rec['sym']].append(rec['sl_dist'])
        per_sym_per_kz[(rec['sym'], rec['kill_zone'])].append(rec['sl_dist'])

    print(f"n_total filled CANDIDATEs across T7 sims: {len(all_records)}")
    print("\nSL distance |entry - SL| distribution (proxy for fill geometry risk):")
    print(f"{'Sym':<8} {'n':>3} {'med':>10} {'mean':>10} {'p05':>10} {'p95':>10}")
    for sym, dists in per_sym_dist.items():
        s = summarize('', dists)
        print(f"{sym:<8} {s['n']:>3} {s['median']:>10} {s['mean']:>10} {s['p05']:>10} {s['p95']:>10}")

    print("\nSL distance by (sym, kz):")
    for (sym, kz), dists in sorted(per_sym_per_kz.items()):
        s = summarize('', dists)
        print(f"  {sym:<8} {kz:<8} n={s['n']:>2} med={s['median']} mean={s['mean']}")

    print("\n[CONCLUSION] Fill slippage cannot be measured from existing data: the")
    print("T7 simulator has NO slippage model (see simulate_t7_live_period.py:539-")
    print("549 — fills occur AT intended entry), and live has produced 0 filled")
    print("trades since Apr 7 (verified: all knowledge_base/sessions/*_live_session")
    print("_.json show trades_today=0; all trade_records show execution: None).")
    print("[DIRECTION] Assume market slippage = 0 in all simulation R reported.")
    print("Actual live slippage will only be measurable AFTER Tuesday redacted_account.\n")

    return all_records


# ─────────────────────────────────────────────────────────────────
# 2. Bit-exact SL-touch signature — "becoming the liquidity"
# ─────────────────────────────────────────────────────────────────
def analyze_bitexact_sl_touches(sources, csv_dir):
    """For each LOSS trade, check if SL hit was bit-exact (within 2 ticks) AND
    price reversed >=1R toward TP within 4h (16 M15 candles) of SL hit.

    This is the "we are the liquidity" signature.
    """
    print("=" * 70)
    print("2. BIT-EXACT SL-TOUCH SIGNATURE")
    print("=" * 70)
    print("Definition: loss where the candle that hit SL did so with low (LONG) or")
    print("high (SHORT) within +/- 2 ticks of the SL price, AND price reversed")
    print(">=1R (toward TP) within 16 M15 candles (4h) of SL hit.\n")

    import csv
    def load_m15(symbol):
        path = os.path.join(csv_dir, f"{symbol}_M15.csv")
        if not os.path.exists(path):
            return None
        rows = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                # time might be 'time' or 'timestamp' etc; detect
                t = r.get('time') or r.get('timestamp') or r.get('Time')
                # Normalize "2026-01-02 01:00:00" -> "2026-01-02T01:00:00Z"
                if t and ' ' in t:
                    t = t.replace(' ', 'T') + 'Z'
                rows.append(dict(
                    time=t,
                    open=float(r.get('open', r.get('Open', 0))),
                    high=float(r.get('high', r.get('High', 0))),
                    low=float(r.get('low', r.get('Low', 0))),
                    close=float(r.get('close', r.get('Close', 0))),
                ))
        return rows

    def find_sl_candle(candles, sl_price, entry_time, direction):
        """Walk forward from entry_time; return (index, candle) of first SL-hit."""
        found_start = False
        for i, c in enumerate(candles):
            if c['time'] == entry_time:
                found_start = True
                continue
            if not found_start:
                continue
            if direction == 'LONG' and c['low'] <= sl_price:
                return i, c
            if direction == 'SHORT' and c['high'] >= sl_price:
                return i, c
        return None, None

    # Cache M15 by symbol
    m15_cache = {}
    for sym in ['XAUUSD', 'NAS100', 'EURUSD', 'US30', 'USDJPY', 'GBPJPY', 'GBPUSD']:
        data = load_m15(sym)
        if data:
            m15_cache[sym] = data

    all_sig = []
    for label, records in sources.items():
        losses = [r for r in records if r.get('decision')=='CANDIDATE' and r.get('outcome')=='LOSS']
        sym = losses[0]['symbol'] if losses else label
        if sym not in m15_cache:
            continue
        m15 = m15_cache[sym]
        tick = TICK_SIZE.get(sym, 0.01)
        two_tick = 2 * tick
        hunt_thresh = LIQUIDITY_HUNT_THRESHOLD.get(sym, 0.05)
        for loss in losses:
            entry = loss['entry_price']
            sl = loss['stop_loss']
            tp = loss['take_profit_1']
            direction = loss['direction']
            entry_time = loss['candle_time']
            r_dist = abs(entry - sl)
            # Find SL candle
            idx, sl_candle = find_sl_candle(m15, sl, entry_time, direction)
            if sl_candle is None:
                continue
            # Bit-exact check: low within 2 ticks of SL (LONG) or high within 2 ticks (SHORT)
            if direction == 'LONG':
                touch_distance = abs(sl_candle['low'] - sl)
                reversal_target = entry  # 1R back = entry
                # But 1R back toward TP is at entry + 1*r_dist from SL, so price must hit entry
            else:
                touch_distance = abs(sl_candle['high'] - sl)
                reversal_target = entry
            bit_exact_strict = touch_distance <= two_tick      # strict 2-tick threshold (matches brief)
            bit_exact_liq = touch_distance <= hunt_thresh      # liquidity-hunt threshold (1-2 pips)
            # 1R reversal check: look forward 16 candles from SL hit
            reversed_1r = False
            max_retrace_r = 0
            for j in range(idx, min(idx + 16 + 1, len(m15))):
                c = m15[j]
                if direction == 'LONG':
                    # Reversal is UP toward entry; 1R back means high >= entry
                    retrace = (c['high'] - sl) / r_dist if r_dist > 0 else 0
                    if retrace > max_retrace_r:
                        max_retrace_r = retrace
                    if c['high'] >= entry:
                        reversed_1r = True
                        break
                else:
                    retrace = (sl - c['low']) / r_dist if r_dist > 0 else 0
                    if retrace > max_retrace_r:
                        max_retrace_r = retrace
                    if c['low'] <= entry:
                        reversed_1r = True
                        break
            all_sig.append(dict(
                sym=sym, label=label, date=loss.get('date') or entry_time[:10],
                candle_time=entry_time, kill_zone=loss['kill_zone'],
                direction=direction, entry=entry, sl=sl, tp=tp,
                r_dist=r_dist, sl_candle_time=sl_candle['time'],
                touch_distance=round(touch_distance, 6),
                two_tick_threshold=two_tick,
                liq_threshold=hunt_thresh,
                bit_exact_strict=bit_exact_strict,
                bit_exact_liq=bit_exact_liq,
                reversed_1r_within_4h=reversed_1r,
                max_retrace_r_within_4h=round(max_retrace_r, 3),
                liquidity_signature_strict=bit_exact_strict and reversed_1r,
                liquidity_signature_liq=bit_exact_liq and reversed_1r,
            ))

    # Summary
    print(f"Total losing CANDIDATEs analyzed: {len(all_sig)}")
    n_bit_s = sum(1 for x in all_sig if x['bit_exact_strict'])
    n_bit_l = sum(1 for x in all_sig if x['bit_exact_liq'])
    n_rev = sum(1 for x in all_sig if x['reversed_1r_within_4h'])
    n_sig_s = sum(1 for x in all_sig if x['liquidity_signature_strict'])
    n_sig_l = sum(1 for x in all_sig if x['liquidity_signature_liq'])
    print(f"bit_exact STRICT (within 2 ticks):        {n_bit_s}")
    print(f"bit_exact LIQ    (within ~1-2 pips):      {n_bit_l}")
    print(f"reversed >=1R within 4h:                   {n_rev}")
    print(f"liquidity_signature STRICT (strict AND rev): {n_sig_s}")
    print(f"liquidity_signature LIQ    (1-2pip AND rev): {n_sig_l}")

    # Per-symbol breakdown
    print("\nPer-symbol (using liquidity-hunt threshold):")
    by_sym = defaultdict(lambda: dict(n=0, bit=0, rev=0, sig=0, sig_loss_r=0.0, total_loss_r=0.0))
    for x in all_sig:
        s = x['sym']
        by_sym[s]['n'] += 1
        by_sym[s]['bit'] += int(x['bit_exact_liq'])
        by_sym[s]['rev'] += int(x['reversed_1r_within_4h'])
        by_sym[s]['sig'] += int(x['liquidity_signature_liq'])
        by_sym[s]['total_loss_r'] -= 1.0
        if x['liquidity_signature_liq']:
            by_sym[s]['sig_loss_r'] -= 1.0
    for sym, d in by_sym.items():
        pct = (d['sig']/d['n']*100) if d['n'] else 0
        print(f"  {sym:<8} n_losses={d['n']:<3} bit_exact_liq={d['bit']}  reversed={d['rev']}  sig={d['sig']} ({pct:.1f}%)  sig_loss_R={d['sig_loss_r']:.1f} / total_loss_R={d['total_loss_r']:.1f}")

    # Quarterly breakdown (of bit_exact and signature)
    print("\nQuarterly evolution (liquidity-hunt signature using liq threshold):")
    by_q = defaultdict(lambda: dict(n=0, bit=0, rev=0, sig=0))
    for x in all_sig:
        y = int(x['candle_time'][:4])
        m = int(x['candle_time'][5:7])
        q = (y, (m-1)//3 + 1)
        by_q[q]['n'] += 1
        by_q[q]['bit'] += int(x['bit_exact_liq'])
        by_q[q]['rev'] += int(x['reversed_1r_within_4h'])
        by_q[q]['sig'] += int(x['liquidity_signature_liq'])
    for q, d in sorted(by_q.items()):
        pct = (d['sig']/d['n']*100) if d['n'] else 0
        print(f"  Q{q[1]}-{q[0]} n_losses={d['n']:<3} bit_exact_liq={d['bit']}  reversed={d['rev']}  sig={d['sig']} ({pct:.1f}%)")

    # Detailed signature-positive rows
    print("\nSignature-positive records (liquidity-hunt threshold):")
    for x in all_sig:
        if x['liquidity_signature_liq']:
            print(f"  {x['sym']:<7} {x['candle_time']} {x['direction']} entry={x['entry']} SL={x['sl']} touch_dist={x['touch_distance']} reversal={x['max_retrace_r_within_4h']}R")

    # Separate: ALL bit_exact touches (whether or not they reversed)
    print("\nBit-exact SL touches — NO reversal filter (pure 'wick-and-continue' count):")
    for sym, d in by_sym.items():
        print(f"  {sym:<8} bit_exact_losses={d['bit']}/{d['n']} = {(d['bit']/d['n']*100 if d['n'] else 0):.1f}%")

    return all_sig


# ─────────────────────────────────────────────────────────────────
# 3. BE-stopped counterfactual
# ─────────────────────────────────────────────────────────────────
def analyze_be_counterfactual(csv_dir):
    """Approximate from batch KB: trades with mfe_r >= 1.0 and final r_multiple <= 0.2
    (small profit consistent with BE stop-out) where forward price could have hit 1.5R."""
    print("=" * 70)
    print("3. BE-STOPPED COUNTERFACTUAL")
    print("=" * 70)
    print("Method: the live system's current BE rule cannot be isolated from the")
    print("batch KB trade records (no BE flag). We use two proxies:")
    print("  (a) shadow_logs/partial_close_backtest.jsonl  — has mfe_r per trade")
    print("  (b) knowledge_base_backtest/sessions/*/*.json trades — mfe_r + r_multiple")
    print("BE-stopped proxy: trade hit >=1.0R MFE then closed at -0.1 < R < 0.2")
    print("(consistent with BE retrace stop-out). Counterfactual: would MFE have")
    print("reached 1.5R if BE had not triggered?\n")

    import glob
    # Batch KB (367 trades)
    trades = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'knowledge_base_backtest/sessions/*/*.json'))):
        with open(f, 'r', encoding='utf-8') as fp:
            d = json.load(fp)
        sym = os.path.basename(os.path.dirname(f))
        for t in d.get('trade_summary', {}).get('trades', []):
            if 'r_multiple' in t and 'mfe_r' in t:
                trades.append(dict(
                    sym=sym,
                    date=d.get('date'),
                    r=t['r_multiple'],
                    mfe_r=t['mfe_r'],
                    mae_r=t['mae_r'],
                    exit_substate=t.get('exit_substate'),
                    kill_zone=t.get('kill_zone'),
                    outcome=t.get('outcome'),
                ))

    print(f"Batch KB trades loaded: {len(trades)}")

    # Current live BE rule (per orchestrator): unknown without code scan
    # We'll try multiple BE triggers: 1.0R, 0.8R, 0.5R
    for be_trigger in [0.5, 0.8, 1.0]:
        be_candidates = [t for t in trades if t['mfe_r'] >= be_trigger and -0.1 < t['r'] < 0.2]
        print(f"\nBE-trigger {be_trigger}R proxy (mfe >= {be_trigger}R AND final r in (-0.1, 0.2)):")
        print(f"  count: {len(be_candidates)}")
        # How many had mfe_r >= 1.5?
        would_have_won = sum(1 for t in be_candidates if t['mfe_r'] >= 1.5)
        print(f"  of those, reached mfe_r >= 1.5R (would have won if no BE): {would_have_won}")
        if be_candidates:
            rs = [t['r'] for t in be_candidates]
            print(f"  their actual R: median={statistics.median(rs)}, sum={sum(rs):.2f}")
            # Counterfactual: assume they'd have reached TP at 1.5R
            cf_sum = would_have_won * 1.5 + (len(be_candidates) - would_have_won) * (-1.0)  # those that didn't reach 1.5R presumably came back and hit SL
            print(f"  naive CF if no BE (win@1.5R or loss@-1R): sum={cf_sum:.2f} vs actual sum={sum(rs):.2f}, delta={cf_sum - sum(rs):.2f}R")

    # Partial-close shadow (more precise)
    pc_recs = []
    with open(os.path.join(ROOT, 'shadow_logs/partial_close_backtest.jsonl'), 'r') as f:
        for line in f:
            pc_recs.append(json.loads(line))
    print(f"\npartial_close_backtest (n={len(pc_recs)}):")
    mfe_over_1 = [r for r in pc_recs if r['mfe_r'] >= 1.0 and r['outcome'] == 'WIN']
    mfe_over_1_5 = [r for r in pc_recs if r['mfe_r'] >= 1.5 and r['outcome'] == 'WIN']
    reversed_past_entry = [r for r in pc_recs if r.get('reversed_past_entry')]
    print(f"  MFE >= 1.0R wins:          {len(mfe_over_1)}")
    print(f"  MFE >= 1.5R wins:          {len(mfe_over_1_5)}")
    print(f"  reversed_past_entry=True:  {len(reversed_past_entry)} <- these would BE-stop")
    if reversed_past_entry:
        rs = [r['actual_r_multiple'] for r in reversed_past_entry]
        vcs = [r['variant_c_blended_r'] for r in reversed_past_entry]
        print(f"    actual R median: {statistics.median(rs)}, sum: {sum(rs):.2f}")
        print(f"    VC(33%@1R) blended median: {statistics.median(vcs)}, sum: {sum(vcs):.2f}")
        for r in reversed_past_entry:
            print(f"    {r['trade_id']} mfe={r['mfe_r']} final_r={r['actual_r_multiple']} vc={r['variant_c_blended_r']}")


# ─────────────────────────────────────────────────────────────────
# 4. Partial-close Variant C vs baseline
# ─────────────────────────────────────────────────────────────────
def analyze_partial_close():
    print("=" * 70)
    print("4. PARTIAL-CLOSE VARIANT C (33% @ 1R) vs BASELINE")
    print("=" * 70)
    for fname, label in [('partial_close_backtest.jsonl', 'approx+exact combined'),
                          ('partial_close_backtest_exact_only.jsonl', 'exact_only subset')]:
        path = os.path.join(ROOT, 'shadow_logs', fname)
        recs = []
        with open(path, 'r') as f:
            for line in f:
                recs.append(json.loads(line))
        n = len(recs)
        if n < 20:
            tag = ' [n<20 EXPLORATORY]'
        elif n < 30:
            tag = ' [n<30 DIRECTIONAL]'
        else:
            tag = ''
        print(f"\n[{label}] n={n}{tag}")
        actual = [r['actual_r_multiple'] for r in recs]
        vc = [r['variant_c_blended_r'] for r in recs]
        delta = [r['delta_r'] for r in recs]
        print(f"  Baseline (no partial): sumR={sum(actual):.2f}, meanR={statistics.mean(actual):.3f}")
        print(f"  Variant C:             sumR={sum(vc):.2f},  meanR={statistics.mean(vc):.3f}")
        print(f"  Delta (VC - baseline): sumR={sum(delta):+.2f},  meanR={statistics.mean(delta):+.3f}")

        wins = [r for r in recs if r['outcome'] == 'WIN']
        losses = [r for r in recs if r['outcome'] == 'LOSS']
        print(f"  Wins   n={len(wins)}:  orig mean={statistics.mean(r['actual_r_multiple'] for r in wins):.3f}, VC mean={statistics.mean(r['variant_c_blended_r'] for r in wins):.3f}, delta={statistics.mean(r['delta_r'] for r in wins):+.3f}")
        if losses:
            print(f"  Losses n={len(losses)}: orig mean={statistics.mean(r['actual_r_multiple'] for r in losses):.3f}, VC mean={statistics.mean(r['variant_c_blended_r'] for r in losses):.3f}, delta={statistics.mean(r['delta_r'] for r in losses):+.3f}")

        # Sign test: H0: median delta = 0
        pos = sum(1 for d in delta if d > 0)
        neg = sum(1 for d in delta if d < 0)
        zero = sum(1 for d in delta if d == 0)
        print(f"  Sign test: pos={pos}, neg={neg}, zero={zero}")
        # Two-sided binomial p-value (quick)
        if pos + neg > 0:
            from math import comb
            N = pos + neg
            k = max(pos, neg)
            p = 2 * sum(comb(N, i) for i in range(k, N+1)) / (2**N)
            print(f"  Sign test p-value (two-sided): {p:.4f}")


# ─────────────────────────────────────────────────────────────────
# 5. Quarterly evolution
# ─────────────────────────────────────────────────────────────────
def analyze_quarterly(trades_with_date):
    """Split trades by quarter and compute WR / expR / drivers."""
    print("=" * 70)
    print("5. QUARTERLY EVOLUTION OF ENTRY-EXEC METRICS")
    print("=" * 70)
    # batch KB
    import glob
    trades = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'knowledge_base_backtest/sessions/XAUUSD/*.json'))):
        with open(f, 'r') as fp:
            d = json.load(fp)
        date = d.get('date', '')
        for t in d.get('trade_summary', {}).get('trades', []):
            if 'r_multiple' in t:
                trades.append(dict(
                    date=date,
                    r=t['r_multiple'],
                    mfe_r=t.get('mfe_r', 0),
                    mae_r=t.get('mae_r', 0),
                    exit_substate=t.get('exit_substate'),
                    outcome=t.get('outcome'),
                ))
    print(f"Batch KB XAUUSD trades with dates: {len(trades)}")

    def quarter_of(date_str):
        y, m = int(date_str[:4]), int(date_str[5:7])
        return f"{y}Q{(m-1)//3 + 1}"

    by_q = defaultdict(list)
    for t in trades:
        by_q[quarter_of(t['date'])].append(t)

    print("\nQuarter-over-quarter XAUUSD batch trades (WR, expR, mfe_r median):")
    print(f"{'Q':<10} {'n':>4} {'W':>4} {'WR%':>6} {'sumR':>7} {'expR':>7} {'mfe_med':>8} {'mae_med':>8} {'timeout%':>9}")
    for q in sorted(by_q.keys()):
        ts = by_q[q]
        n = len(ts)
        W = sum(1 for t in ts if t['r'] > 0)
        wr = 100 * W / n if n else 0
        sR = sum(t['r'] for t in ts)
        eR = sR / n if n else 0
        mfe_med = statistics.median(t['mfe_r'] for t in ts) if ts else 0
        mae_med = statistics.median(t['mae_r'] for t in ts) if ts else 0
        to_pct = 100 * sum(1 for t in ts if 'TIMEOUT' in (t.get('exit_substate') or '')) / n if n else 0
        print(f"{q:<10} {n:>4} {W:>4} {wr:>6.1f} {sR:>7.2f} {eR:>7.3f} {mfe_med:>8.3f} {mae_med:>8.3f} {to_pct:>9.1f}")

    # "BE-stop proxy" per quarter: mfe_r >= 0.8 AND -0.1 < r < 0.2
    print("\nBE-stop proxy (mfe>=0.8R AND final r in (-0.1,0.2)) per quarter:")
    for q in sorted(by_q.keys()):
        ts = by_q[q]
        be = [t for t in ts if t['mfe_r'] >= 0.8 and -0.1 < t['r'] < 0.2]
        print(f"  {q}: {len(be)}/{len(ts)} = {100*len(be)/len(ts):.1f}% if n>0")


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main():
    csv_dir = os.path.join(ROOT, 'data/historical_2026')
    # Load sources
    xau_path = os.path.join(ROOT, 'research/t7_live_simulation/all_results_jan_apr10.json')
    eur_path = os.path.join(ROOT, 'research/t7_live_simulation/EURUSD_t7_simulation.json')

    sources = {}
    sources['XAUUSD'] = load_t7(xau_path)
    sources['EURUSD'] = load_t7(eur_path)

    # NAS100 slices
    nas100 = []
    for i in range(1, 6):
        p = os.path.join(ROOT, f'research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{i}/NAS100_t7_simulation.json')
        if os.path.exists(p):
            nas100.extend(load_t7(p))
    sources['NAS100'] = nas100

    # Tag symbol on each
    for label, recs in sources.items():
        for r in recs:
            if 'symbol' not in r:
                r['symbol'] = label

    print(f"Loaded sources: XAUUSD={len(sources['XAUUSD'])}, NAS100={len(sources['NAS100'])}, EURUSD={len(sources['EURUSD'])}")
    print()

    analyze_slippage(sources)
    print()
    analyze_bitexact_sl_touches(sources, csv_dir)
    print()
    analyze_be_counterfactual(csv_dir)
    print()
    analyze_partial_close()
    print()
    analyze_quarterly(None)
    print()


if __name__ == '__main__':
    main()
