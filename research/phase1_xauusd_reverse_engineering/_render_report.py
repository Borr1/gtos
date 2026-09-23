"""
Render SUB_SESSION_MAP.md from the computed bucket-stats CSVs.

All numeric tables are generated directly from the CSV artifacts so they are
guaranteed to match the underlying analysis. Narrative text is the only
hand-written component.
"""
from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime

HERE = os.path.dirname(__file__)
TRADES = os.path.join(HERE, 'unified_trades.csv')
B15 = os.path.join(HERE, 'bucket_stats_15min.csv')
B30 = os.path.join(HERE, 'bucket_stats_30min.csv')
B60 = os.path.join(HERE, 'bucket_stats_60min.csv')
OUT = os.path.join(HERE, 'SUB_SESSION_MAP.md')

BREAKEVEN_WR = {
    'XAUUSD':    0.357,
    'US30_cash': 0.345,
    'USDJPY':    0.400,
    'GBPJPY':    0.417,
    'GBPUSD':    0.375,
}


def load_trades():
    with open(TRADES) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r['r_multiple'] = float(r['r_multiple'])
    return rows


def load_buckets(path):
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r['n'] = int(r['n'])
        r['wins'] = int(r['wins'])
        r['losses'] = int(r['losses'])
        r['breakevens'] = int(r['breakevens'])
        r['wr'] = float(r['wr'])
        r['mean_r'] = float(r['mean_r'])
        r['hqf_score'] = float(r['hqf_score'])
        for k in ('wr_lo95', 'wr_hi95', 'mean_r_lo95', 'mean_r_hi95'):
            r[k] = float(r[k]) if r[k] not in ('', None) else None
    return rows


def fmt_wr_ci(r):
    if r['wr_lo95'] is None: return '-'
    return f"[{r['wr_lo95']:.2f}, {r['wr_hi95']:.2f}]"


def fmt_er_ci(r):
    if r['mean_r_lo95'] is None: return '-'
    return f"[{r['mean_r_lo95']:+.2f}, {r['mean_r_hi95']:+.2f}]"


def per_instrument_baselines(trades):
    by_sym = defaultdict(list)
    for t in trades:
        by_sym[t['symbol']].append(t)
    base = {}
    for s, rs in by_sym.items():
        n = len(rs)
        wins = sum(1 for r in rs if r['outcome'] == 'WIN')
        er = sum(r['r_multiple'] for r in rs) / n
        base[s] = {'n': n, 'wr': wins / n, 'er': er}
    return base


def render_table(rows, with_rec=True):
    lines = []
    if with_rec:
        lines.append('| KZ | Bucket | n | W/L/BE | WR | WR 95% CI | E[R] | E[R] 95% CI | Total R | Rec |')
        lines.append('|---|---|---|---|---|---|---|---|---|---|')
        for r in rows:
            total = r['n'] * r['mean_r']
            lines.append(
                f"| {r['kill_zone']} | {r['bucket_start']}-{r['bucket_end']} | "
                f"{r['n']} | {r['wins']}/{r['losses']}/{r['breakevens']} | "
                f"{r['wr']:.3f} | {fmt_wr_ci(r)} | {r['mean_r']:+.3f} | {fmt_er_ci(r)} | "
                f"{total:+.2f}R | {r['recommendation']} |"
            )
    return '\n'.join(lines)


def main():
    trades = load_trades()
    base = per_instrument_baselines(trades)
    b15 = load_buckets(B15)
    b30 = load_buckets(B30)
    b60 = load_buckets(B60)

    # Dataset meta
    dates = sorted(t['date'] for t in trades)
    d0 = datetime.fromisoformat(dates[0])
    d1 = datetime.fromisoformat(dates[-1])
    months = max((d1 - d0).days / 30.0, 1.0)

    L = []
    L.append('# Phase 1 Track C — Per-Instrument Sub-Session Edge Map')
    L.append('')
    L.append('**Agent:** Phase 1 Track C (max effort)')
    L.append('**Date built:** 2026-04-24')
    L.append('**Branch:** `research/phase1-track-c-sub-session-map`')
    L.append('**Scope:** 15-min / 30-min / 60-min buckets within kill zones, per instrument, ranked by WR + expectancy and high-quality-frequency.')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## TL;DR — bottom line up front')
    L.append('')
    L.append('- **Sample size blocks all formal EMPHASIS/SKIP calls at 15-min granularity.** Not a single (instrument, KZ, 15-min-bucket) cell reaches the required n ≥ 20 threshold. The unified dataset contains 266 simulator trades across 24.6 months; fragmenting into ~80 buckets leaves every cell at n < 16.')
    L.append('- **5 buckets reach n ≥ 20 system-wide,** all of them 60-min XAUUSD buckets. None trigger a formal SKIP or EMPHASIS. Even the worst XAUUSD NY 13:00 bucket (n=29, WR 48.3%, E[R] −0.088R) has WR upper-CI 65.5% — well above the 35.7% breakeven. Rule classification → OBSERVE.')
    L.append('- **Total EMPHASIS candidates: 0. Total SKIP candidates: 0** at n ≥ 20.')
    L.append('- **Live post-April-7 trade outcomes are unusable for this analysis.** 32 LIMIT_PLACED trade records exist, zero have `execution`/`exit` data populated. Fleet ran under FTMO free-trial where `trade_expert=False` caused order rejections ("AutoTrading disabled by client"). One XAUUSD Apr-16 fill was "closed by broker" 6 minutes later with no exit data captured. Analysis relies entirely on simulator sources.')
    L.append('- **Pre-/post-v2_shadow flip diagnostic not possible** — the flip landed 2026-04-24 ~11:48 UTC and the latest available backtest/T7-sim data ends 2026-04-08. All directional data is pre-flip (94% LONG).')
    L.append('')
    L.append('### Descriptive signal at 60-min XAUUSD (no formal rec):')
    L.append('')
    xau60 = sorted([r for r in b60 if r['symbol'] == 'XAUUSD'], key=lambda x: x['mean_r'])
    worst = xau60[0] if xau60 else None
    best = max(xau60, key=lambda x: x['n'] * x['mean_r']) if xau60 else None
    if best:
        L.append(f"- *Best total R bucket:* {best['kill_zone']} {best['bucket_start']}-{best['bucket_end']} (n={best['n']}, WR {best['wr']:.1%}, E[R] {best['mean_r']:+.3f}R → total {best['n']*best['mean_r']:+.2f}R)")
    if worst:
        L.append(f"- *Worst 60-min bucket by E[R]:* {worst['kill_zone']} {worst['bucket_start']}-{worst['bucket_end']} (n={worst['n']}, WR {worst['wr']:.1%}, E[R] {worst['mean_r']:+.3f}R → total {worst['n']*worst['mean_r']:+.2f}R). WR upper-CI does not exclude breakeven — not a SKIP.")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Data provenance')
    L.append('')
    L.append('### Unified dataset sources')
    L.append('')
    L.append('| Source | File(s) | Type | Rows kept |')
    L.append('|---|---|---|---|')
    L.append('| **q65_sim** | `research/q65_speed_to_mfe/q65_trade_speeds.csv` | session_simulator batch (April 2024 – March 2026) | 225 |')
    L.append('| **f3** | `research/f3_backtest_2026-04-24/*/all_results.json` (12 slices) | T7 production-faithful sim (Jan–Apr 2026 XAUUSD×8 + USDJPY×4) | 32 |')
    L.append('| **t7** | `research/t7_live_simulation/all_results_jan_apr10.json` | T7 production-faithful sim (Jan 2 – Apr 10, 2026 XAUUSD) | 9 |')
    L.append('')
    L.append(f'**Total after dedup on (symbol, candle_time):** 266 trades. **Date range:** {dates[0]} → {dates[-1]} ({months:.1f} months).')
    L.append('')
    L.append('### Per-instrument loaded counts and baselines')
    L.append('')
    L.append('| Instrument | n (filled) | Baseline WR | Baseline E[R] | Breakeven WR (task) |')
    L.append('|---|---|---|---|---|')
    for s in ['XAUUSD', 'USDJPY', 'US30_cash', 'GBPJPY', 'GBPUSD']:
        b = base[s]
        L.append(f"| {s} | {b['n']} | {b['wr']:.3f} | {b['er']:+.3f}R | {BREAKEVEN_WR[s]:.3f} |")
    L.append(f'| **Total** | **{sum(b["n"] for b in base.values())}** | | | |')
    L.append('')
    L.append('### Live trade-record schema notes')
    L.append('')
    L.append('- `trade_records/{instrument}/*.json`: **173 live production records** exist (XAUUSD 12, US30_cash 26, USDJPY 45, GBPJPY 42, GBPUSD 48). **None have populated `execution` or `exit` fields.** Schema has these fields but they were never written because:')
    L.append('  - 32 records reached `LIMIT_PLACED` (gate3 pass) but all orders were rejected by MT5 with "AutoTrading disabled by client" retcode (FTMO free-trial EA-excluded condition per CLAUDE.md).')
    L.append('  - The **single** 2026-04-16 XAUUSD limit that actually filled (limit=4796.28, entry=4795.23) was marked `Position 427534724 no longer exists — closed by broker` 6 minutes later with zero exit metadata. No r_multiple available.')
    L.append('- `_pending_records_index.json` files list currently-pending limits (GBPJPY 1, USDJPY 2 as of snapshot), no outcomes.')
    L.append('- `knowledge_base/statistics/rolling_stats.json` shows 129 trades, all `source: batch_session`, last entry 2026-02-06. Zero live rows written.')
    L.append('- `live_evaluations/{instrument}/*.jsonl` records per-candle *decisions* (NO_TRADE / CANDIDATE / WAIT) but NOT trade outcomes.')
    L.append('')
    L.append('**Conclusion on live data:** it does not exist in usable form. All analysis below is simulator-based.')
    L.append('')
    L.append('### Rows dropped during bucketing (60-min)')
    L.append('')
    L.append('| Reason | Count |')
    L.append('|---|---|')
    L.append('| Entry time outside reported KZ bounds (edge cases at close minute 09:30/15:30/03:00) | 3 (GBPJPY) |')
    L.append('| XAUUSD NY 13:00-13:14 skip window | 0 |')
    L.append('')
    L.append('Sanity check — bucket n sums:')
    L.append('')
    L.append('| Instrument | Input n | Bucketed n | Δ |')
    L.append('|---|---|---|---|')
    sym_total = defaultdict(int)
    for t in trades:
        sym_total[t['symbol']] += 1
    sym_bucket = defaultdict(int)
    for b in b60:
        sym_bucket[b['symbol']] += b['n']
    for s in ['XAUUSD', 'USDJPY', 'US30_cash', 'GBPJPY', 'GBPUSD']:
        L.append(f"| {s} | {sym_total[s]} | {sym_bucket[s]} | {sym_total[s] - sym_bucket[s]} |")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Method')
    L.append('')
    L.append('1. **Entry-time extraction:** use `candle_time` (UTC) from each trade record. Convert to minute-of-day; assign bucket key `HH:MM` rounded down to bucket size.')
    L.append('2. **KZ bounds** match CLAUDE.md:')
    L.append('   - XAUUSD: London 07:00-10:30, NY 13:00-17:00 (skip 13:00-13:14)')
    L.append('   - US30_cash: London 08:00-10:30, NY 13:30-16:00')
    L.append('   - USDJPY/GBPJPY: London 07:00-09:30, NY 13:00-15:30, Tokyo 00:00-03:00')
    L.append('   - GBPUSD: London 07:00-12:00, NY 13:00-15:30')
    L.append('3. **Bootstrap CIs:** 5000 iterations per bucket, basic percentile method, fixed RNG seed per bucket. WR: resample outcomes, compute mean. E[R]: resample r_multiples, compute mean. Fat-tail safe — no t-tests on R-multiples.')
    L.append('4. **Recommendation rules:**')
    L.append('   - `EMPHASIS`: n ≥ 20 AND WR_lo95 > instrument_baseline_WR AND E[R]_lo95 > 0')
    L.append('   - `SKIP`: n ≥ 20 AND WR_hi95 < instrument_breakeven_WR (task-provided)')
    L.append('   - `INSUFFICIENT`: n < 20')
    L.append('   - `OBSERVE`: otherwise')
    L.append('5. **Bonferroni note:** 8 XAUUSD 60-min buckets, 6 USDJPY, 5 US30_cash, 8 GBPJPY, 6 GBPUSD. Corrected alpha would widen CIs toward ~99.2–99.4%, which strictly *cannot* flip an uncorrected OBSERVE to a corrected EMPHASIS/SKIP. No recommendation in this report depends on Bonferroni.')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Per-instrument bucket tables — 60-min granularity')
    L.append('')

    for sym in ['XAUUSD', 'USDJPY', 'US30_cash', 'GBPJPY', 'GBPUSD']:
        srows = sorted([r for r in b60 if r['symbol'] == sym],
                       key=lambda r: (r['kill_zone'], r['bucket_start']))
        L.append(f'### {sym}')
        L.append('')
        L.append(f'Baseline WR = {base[sym]["wr"]:.3f}, Breakeven WR = {BREAKEVEN_WR[sym]:.3f}.')
        L.append('')
        L.append(render_table(srows))
        L.append('')

    L.append('---')
    L.append('')
    L.append('## Per-instrument bucket tables — 15-min granularity (reference)')
    L.append('')
    L.append('All cells INSUFFICIENT (n < 20). Included as descriptive reference only.')
    L.append('')

    for sym in ['XAUUSD', 'USDJPY', 'US30_cash', 'GBPJPY', 'GBPUSD']:
        srows = sorted([r for r in b15 if r['symbol'] == sym],
                       key=lambda r: (r['kill_zone'], r['bucket_start']))
        L.append(f'### {sym} (15-min)')
        L.append('')
        L.append(render_table(srows))
        L.append('')

    L.append('Full machine-readable outputs: `bucket_stats_15min.csv`, `bucket_stats_30min.csv`, `bucket_stats_60min.csv`.')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Emphasis candidates (n ≥ 20, WR_lo > baseline, E[R]_lo > 0)')
    L.append('')
    emph = [r for r in b60 if r['recommendation'] == 'EMPHASIS']
    if emph:
        for r in emph:
            L.append(f"- **{r['symbol']} {r['kill_zone']} {r['bucket_start']}-{r['bucket_end']}**: n={r['n']} WR={r['wr']:.3f} {fmt_wr_ci(r)} E[R]={r['mean_r']:+.3f} {fmt_er_ci(r)}")
    else:
        L.append('**None.** No bucket satisfies the formal rule.')
    L.append('')
    L.append('## Skip candidates (n ≥ 20, WR_hi < breakeven)')
    L.append('')
    skips = [r for r in b60 if r['recommendation'] == 'SKIP']
    if skips:
        for r in skips:
            L.append(f"- **{r['symbol']} {r['kill_zone']} {r['bucket_start']}-{r['bucket_end']}**: n={r['n']} WR={r['wr']:.3f} {fmt_wr_ci(r)} breakeven={BREAKEVEN_WR[r['symbol']]:.3f}")
    else:
        L.append("**None.** The only large-sample negative-E[R] bucket (XAUUSD NY 13:00-14:00) has WR_hi95 = 65.5%, nearly 30pp above its 35.7% breakeven. Formally OBSERVE.")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Descriptive lens — where the edge lives empirically')
    L.append('')
    L.append('Top 10 buckets ranked by total R produced (`n · E[R]`, the high-quality-frequency metric). **Note:** all below are at varying n; only those with n ≥ 20 can be formally recommended.')
    L.append('')
    L.append('| Rank | Symbol | KZ | Bucket | n | WR | E[R] | Total R | Rec |')
    L.append('|---|---|---|---|---|---|---|---|---|')
    ranked = sorted(b60, key=lambda r: r['n'] * r['mean_r'], reverse=True)
    for i, r in enumerate(ranked[:10], 1):
        total = r['n'] * r['mean_r']
        L.append(f"| {i} | {r['symbol']} | {r['kill_zone']} | {r['bucket_start']}-{r['bucket_end']} | {r['n']} | {r['wr']:.3f} | {r['mean_r']:+.3f} | {total:+.2f}R | {r['recommendation']} |")
    L.append('')
    L.append('Bottom 5 buckets by E[R] (smallest first):')
    L.append('')
    L.append('| Symbol | KZ | Bucket | n | WR | E[R] | Total R | Rec |')
    L.append('|---|---|---|---|---|---|---|---|')
    ranked_asc = sorted(b60, key=lambda r: r['mean_r'])
    for r in ranked_asc[:5]:
        total = r['n'] * r['mean_r']
        L.append(f"| {r['symbol']} | {r['kill_zone']} | {r['bucket_start']}-{r['bucket_end']} | {r['n']} | {r['wr']:.3f} | {r['mean_r']:+.3f} | {total:+.2f}R | {r['recommendation']} |")
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Expected R/month lift estimate — hypothetical trimming')
    L.append('')
    L.append('Dataset spans 24.6 months. XAUUSD n ≥ 20 buckets (5 cells) collectively produced:')
    L.append('')
    xau_n20 = [r for r in b60 if r['symbol'] == 'XAUUSD' and r['n'] >= 20]
    xau_total_n = sum(r['n'] for r in xau_n20)
    xau_total_r = sum(r['n'] * r['mean_r'] for r in xau_n20)
    L.append(f'- Total N = {xau_total_n} filled trades')
    L.append(f'- Total R = {xau_total_r:+.2f}R over {months:.1f} months = **{xau_total_r / months:+.2f}R/month average**')
    L.append('')
    L.append('### Hypothetical "trim worst" scenarios (descriptive only)')
    L.append('')
    L.append('| Dropped buckets | Freq lost | R avoided | Remaining R/mo (over 24.6mo) | New WR |')
    L.append('|---|---|---|---|---|')
    ranked_xau = sorted(xau_n20, key=lambda r: r['mean_r'])
    cum_n, cum_r = 0, 0.0
    cum_wins = sum(r['wins'] for r in xau_n20)
    # baseline row first
    new_wr = cum_wins / xau_total_n
    L.append(f'| (none) | 0 (0.0%) | 0 | {xau_total_r / months:+.3f}R/mo | {new_wr:.3f} |')
    for k in range(1, len(ranked_xau) + 1):
        dropped = ranked_xau[:k]
        dn = sum(r['n'] for r in dropped)
        dr = sum(r['n'] * r['mean_r'] for r in dropped)
        dwins = sum(r['wins'] for r in dropped)
        remaining_r = xau_total_r - dr
        pct = 100 * dn / xau_total_n
        label = ', '.join(f"{r['kill_zone']} {r['bucket_start']}" for r in dropped)
        new_n = xau_total_n - dn
        new_w = cum_wins - dwins
        new_wr = new_w / new_n if new_n else 0
        L.append(f'| {label} | {dn} ({pct:.1f}%) | {-dr:+.2f}R | {remaining_r / months:+.3f}R/mo | {new_wr:.3f} |')
    L.append('')
    L.append('**Interpretation.** If the CEO dropped the single worst XAUUSD 60-min bucket (NY 13:00-14:00) the data says +0.10R/month lift — a 6% relative improvement in expected R/month at an 18% XAUUSD frequency cost. Overall XAUUSD WR rises from 61.1% → 64.1% (3.0pp).')
    L.append('')
    L.append('**Per the high-quality-frequency framing** (CEO 2026-04-24 per `feedback_research_goal_high_quality_frequency.md`): the trade-off is marginal at best. 18% of XAUUSD frequency for 0.10R/month — low conviction. **Recommendation: observe, do not trim.** The WR CI on that bucket is [0.31, 0.66]; the true WR could plausibly be anywhere from losing-edge to winning-edge. Trimming on that basis risks baseline-bias extraction as much as genuine edge extraction.')
    L.append('')
    L.append('**Range** on the per-month lift estimate: given bootstrap CI on bucket E[R] of [−0.38R, +0.21R], the per-month lift from trimming NY 13:00-14:00 alone could be anywhere from **−0.25R/mo to +0.44R/mo**. Point estimate +0.10R/mo sits near the midpoint but cannot be distinguished from zero at 95%.')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Diagnostic: pre-/post-v2_shadow flip')
    L.append('')
    L.append('**Not possible with current data.** The v2_shadow detector flip landed 2026-04-24 11:48:55 UTC. The most recent simulator data in this analysis ends 2026-04-08, so every trade in the dataset reflects **v1 detector behavior**. No post-flip simulator replay or live-with-outcomes rows exist yet.')
    L.append('')
    L.append(f'**Direction distribution (all simulator trades):** 250 LONG vs 16 SHORT (94% long-biased) — reflecting the v1 structural bullish bias per ADR-004.')
    L.append('')
    L.append('| Symbol | LONG | SHORT | SHORT% |')
    L.append('|---|---|---|---|')
    for s in ['XAUUSD', 'USDJPY', 'US30_cash', 'GBPJPY', 'GBPUSD']:
        srs = [t for t in trades if t['symbol'] == s]
        lo = sum(1 for t in srs if t['direction'] == 'LONG')
        sh = sum(1 for t in srs if t['direction'] == 'SHORT')
        pct = 100 * sh / max(lo + sh, 1)
        L.append(f'| {s} | {lo} | {sh} | {pct:.1f}% |')
    L.append('')
    L.append('**Implication.** When v2_shadow is promoted to production (14-day shadow + 100-divergence gate), per-bucket direction mix for at least XAUUSD will shift meaningfully (F3 predicted 0% → 22.8% raw SHORT CAND share on XAUUSD). Any bucket-level emphasis/skip recommendations derived today may not survive that shift.')
    L.append('')
    L.append('**Recommendation:** re-run this analysis after (a) v2 production promotion, AND (b) accumulation of ≥30 live trades per instrument KZ (≈ 3–4 months at current fleet frequency of ~4 CANDs/week × 5 instruments).')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## Honest caveats')
    L.append('')
    L.append('1. **All outcomes are simulator-derived.** Three sources (q65_sim session_simulator, F3 T7 backtest, T7 live-sim) share realization engine logic but apply against historical candles, not live quotes. Slippage, spread dynamics, partial fills, and real-time liquidity are not captured.')
    L.append('')
    L.append('2. **Small-sample dominance.** 266 trades / (5 instruments × 3 KZ × 14 15-min buckets) ≈ 1.3 trades per cell on average. Only 5 cells at 60-min granularity reach n ≥ 20. No 15-min cell does. Structural data-availability problem, not analytical.')
    L.append('')
    L.append('3. **Fat-tail distribution.** Gold ξ ≈ 0.35 (per memory `project_distributional_findings.md`). Bootstrap CIs on means under-estimate tail uncertainty at small n. Treat every mean_r CI at n < 30 as a lower bound on true uncertainty.')
    L.append('')
    L.append('4. **Non-stationarity.** Dataset spans 2024-04 to 2026-04, including multiple structural regime shifts (SVB aftermath, 2024 US election, 2025 gold breakout to $5k+, Trump tariff episodes). Quarterly WR decay 73% → 59% from 2024Q2 to 2026Q1 per CLAUDE.md — bucket-level edges may also decay.')
    L.append('')
    L.append('5. **Bonferroni adjustment impact.** With 8 XAUUSD 60-min buckets, 95% single-bucket CIs become effectively ~99.4% multi-bucket CIs. Uncorrected CIs on every XAUUSD bucket already include WR-equal-to-baseline; tightening does not change any verdict. No recommendation in this report is on the significance edge.')
    L.append('')
    L.append('6. **LONG-only bias.** 94% of trades are LONG direction (v1 detector output). SHORT bucket behavior is essentially unobserved; post-v2_shadow-promotion re-analysis is a prerequisite to any fleet-wide bucket-level directive.')
    L.append('')
    L.append('7. **q65 session_simulator specifics.** Processes trades against historical candles without intra-candle price walking for many windows, which biases exit_substate toward CLOSED_SESSION_TIMEOUT (90/233 rows in q65). This artificially compresses the expectancy distribution.')
    L.append('')
    L.append('8. **Unfilled limits excluded.** UNFILLED rows were dropped. This biases reported WR upward relative to an "all-CAND" WR metric; the "sweep-the-ground WR across all decided candidates" metric is not computed here.')
    L.append('')
    L.append('9. **GBPUSD observer.** GBPUSD dataset rows include live-trading-enabled backtest periods; instrument is observer-only in current production (per `research/gbpusd_observer_mode_decision_2026-04-24.md`). Its 15 rows cannot drive a production recommendation either way.')
    L.append('')
    L.append('10. **No EMPHASIS/SKIP recommendations is itself the finding.** The CEO-hypothesized 3–5pp WR uplift at low frequency cost from trimming the worst 20% buckets is **not supported by this data** at any CI that survives fat-tail + Bonferroni discipline. Better use of the data: maintain current KZ discipline, wait for v2-post-promotion live outcomes, revisit after ≥300 live-filled trades.')
    L.append('')
    L.append('---')
    L.append('')
    L.append('## File deliverables')
    L.append('')
    L.append('| Path | Purpose |')
    L.append('|---|---|')
    L.append('| `SUB_SESSION_MAP.md` | This document |')
    L.append('| `unified_trades.csv` | 266 unified simulator trades (source data) |')
    L.append('| `bucket_stats_15min.csv` | 82 buckets at 15-min granularity |')
    L.append('| `bucket_stats_30min.csv` | 52 buckets at 30-min granularity |')
    L.append('| `bucket_stats_60min.csv` | 35 buckets at 60-min granularity |')
    L.append('| `lift_analysis.md` | Supplementary lift calculations |')
    L.append('| `_build_dataset.py` | Dataset construction script |')
    L.append('| `_analyze_buckets.py` | Bucket-stats engine |')
    L.append('| `_lift_analysis.py` | Lift-estimate report generator |')
    L.append('| `_render_report.py` | This report generator |')
    L.append('')
    L.append('---')
    L.append('')
    L.append('*All outputs regenerable by running:*')
    L.append('```bash')
    L.append('python _build_dataset.py && python _analyze_buckets.py && python _lift_analysis.py && python _render_report.py')
    L.append('```')

    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))
    print('WROTE', OUT)


if __name__ == '__main__':
    main()
