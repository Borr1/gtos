# Gold Trading Agent — Session Handoff (March 31, 2026)

## What Changed Since Last Handoff

### Infrastructure Built Today
1. **Subscription billing backend** — `claude -p` CLI integration for Max plan billing. Works but slow (~8 min/session). Better for small tests, not bulk.
2. **Batch API integration** — `scripts/batch_backtest.py`. Submits all candles as one batch, 50% discount. This is the primary backtesting mode now.
3. **Multi-framework Primary Analyzer** — Expanded from 1 setup (session_sweep only) to 4 frameworks:
   - Framework 1: Session Liquidity Sweep (sweeps of Asian H/L, PDH/PDL, London H/L)
   - Framework 2: H1 Order Block Retest after confirmed BOS
   - Framework 3: Equal Highs/Lows Sweep + Reversal
   - Framework 4: FVG Fill in Discount/Premium
4. **Dual kill zones** — London (07:00-09:30 UTC) + NY Open (13:00-15:30 UTC). Max 1 trade per window, max 2 per day.
5. **London H/L computation** — Added to MSO for NY window context.
6. **Pre-screening filters** — 2 layers (D1 bias + H4 alignment) applied BEFORE API calls. Eliminated ~60% of sessions in testing. Zero false negatives because these are universal requirements for ALL 4 frameworks.
7. **MT5 data export** — Replaced HuggingFace data (scattered, 75 gaps) with broker data from MT5 demo account. 516 continuous trading days, Apr 2024 – Mar 2026.
8. **Cost estimator fix** — Output tokens updated from 400 to 800 per response. Char-to-token ratio from 4.0 to 3.5.
9. **Short-response prompt instruction** — AI outputs minimal JSON when U1/U2 fail (saves output tokens on obvious NO_TRADE).
10. **Batch session manifest writing** — Fixed mid-session. The batch script originally only saved summary results, not per-session manifest files. Now writes proper session files + raw PA responses to disk for every batch.

### Known Minor Issues
- **batch_report.txt overwrite** — If two batches finish, the second overwrites the first's report. Raw results are saved separately with batch ID so no data loss, but the summary report only shows the last batch. Regenerable.
- **Cost estimator still ~27% low** — Even after the 400→800 fix, actual batch costs run ~27% above estimates due to unpredictable cache hit rates in batch mode. Budget accordingly.

### Tests: 262 passing

### Batch Results So Far

**Batch 1 (HuggingFace data, old single-framework):**
- Dec 2024 – Mar 2025: 78 sessions, 7 trades (pre-fix), +3.85R
- Apr – Sep 2025: 56 sessions (scattered), 0 trades (2 candidates safety-rejected, both would have lost)

**Batch 2 (MT5 data, multi-framework + dual kill zone):**
- May 2025 only: 22 sessions, 2 trades, -2.00R (both session_sweep, both blown out immediately — sweep-vs-breakdown confusion)

**Batch 3 (MT5 data, multi-framework + dual kill zone + pre-screening):**
- Oct 2024 – Mar 2025: 49 sessions (128 dates, 79 pre-screened out), 27 trades, +1.77R

### Batch 3 Detailed Analysis (27 trades — the key dataset)

**Framework breakdown:**
- session_sweep: 26 trades (9W/17L, -0.28R) — 96% of all trades
- ob_retest: 1 trade (1W/0L, +2.05R)
- equal_sweep: 0 trades
- fvg_fill: 0 trades

**Kill zone breakdown:**
- London: 17 trades (5W/12L, -5.73R, -0.34R/trade) — NET NEGATIVE
- NY: 10 trades (5W/5L, +7.50R, +0.75R/trade) — carries entire profit

**Grade breakdown:**
- A+: 21 trades (9W/12L, +4.57R, +0.22R/trade)
- A: 6 trades (1W/5L, -2.80R, -0.47R/trade)
- Signal is suggestive but A-grade sample too small (6 trades) to be conclusive

**Safety check performance:**
- 13 candidates rejected by safety checks
- If taken: 3W/9L = -4.68R. Safety checks saved +4.68R. Strongly net positive.
- $5 SL floor particularly valuable (5 of 6 sub-$5 trades would have lost)

**Loser characteristics:**
- Average 17 candles (~4 hours) to SL — not immediate blowouts
- 7 of 17 losers reached 50%+ of the way to TP1 before reversing
- 3 reached 80-89% of TP1 — near-miss losers suggest TP placement may need tuning

**Winner characteristics:**
- Average max favorable excursion: 3.1R
- 4 trades hit all 3 TPs. 2 only hit TP1. 2 were profitable timeouts.
- Two standout winners: Feb 10 (+2.29R, 5.3 MFE) and Mar 13 (+4.80R, 8.8 MFE)

### Currently Running (Two Batches in Parallel)

**Batch 4A:** Apr 2024 – Sep 2024 (~49 sessions, est. $13-16)
- Command: `python3 scripts/batch_backtest.py --start 2024-04-01 --end 2024-09-30`
- If terminal was closed, check `knowledge_base_backtest/batch_api/` for the batch ID file, then: `python3 scripts/batch_backtest.py --resume-batch <batch_id>`

**Batch 4B:** Apr 2025 – Mar 2026 (~95 sessions, est. $25-32)
- Command: `python3 scripts/batch_backtest.py --start 2025-04-01 --end 2026-03-28`
- Same resume process if terminal closed.

Combined with Batch 3's 27 trades, total expected: 80-110 trades.
These batches use the SAME system (no changes) so results are directly comparable.

### API Balance
Started today at -$0.33. Topped up multiple times. Current: ~$60 minus Batch 3 ($13) minus Batch 4A+4B (~$38-48 estimated) = ~$0-10 remaining after batches complete.

## Key Decisions Made Today

1. **Frameworks 2-4 aren't firing** — ob_retest had 221 near-misses (H1 CHoCH but not BOS). May need BOS requirement relaxed. But NOT changing until we have 100+ trades.
2. **No changes before Batch 4 results** — The system runs as-is for all batches so data is comparable. A+ filter, London/NY decisions, framework tuning ALL wait for the full dataset.
3. **Session context (AI seeing prior candle assessments)** — NOT implemented. Batch API requires independent requests. Would need sequential processing for live trading. Current backtest is a conservative floor — live system with context should be at least as good.
4. **Liquidity pre-screening rejected** — Layers 3/4 (liquidity proximity check) were designed then removed because they'd filter out ob_retest and fvg_fill frameworks. Only D1 bias + H4 alignment are truly universal pre-screens.

## What Happens After Batch 4 Results

### Immediate (1-2 weeks)
1. **Analyze full 100+ trade dataset** — A+ vs A, London vs NY, framework performance, monthly patterns, near-miss TP analysis. Make data-backed decisions.
2. **Apply filter changes + re-validate** (~$10-15) — Whatever the data supports (A+ only, TP adjustment, etc.)
3. **Chart vision A/B test** (3-5 days, ~$20) — Render annotated M15 chart images with mplfinance, send to Claude via vision input alongside JSON for CANDIDATE evaluations only. Tests whether visual assessment fixes sweep-vs-breakdown confusion (the primary failure mode in current results).

### Build Phase (1-2 weeks)
4. **Build live execution pipeline** (1 week, $0) — Component 4 (execution engine), Component 8 (orchestrator), MT5 real-time connection, sequential candle processing WITH session context (prior candle assessments passed to next evaluation), real order placement, position management (partial closes at TP1/TP2, trail TP3), error handling for disconnections.
5. **Session context implementation** — In live mode, each candle evaluation receives the AI's assessment of the previous candle (e.g., "WAIT — sweep developing at Asian low, watching for CHoCH"). This is incompatible with Batch API (requires sequential processing) but natural for live trading. The backtest results are a conservative floor since live will have this additional context.

### Demo Phase (3-4 weeks)
6. **Demo trading** (~$15 API) — Live system on demo MT5 account. Need ~30-40 trades to confirm backtest results hold in real-time. Use Opus model for max accuracy (cost difference vs Sonnet is ~$7/month — trivial relative to capital at risk).

### Scale Phase (months 2-4)
7. **Prop firm challenge** — First $100K funded account (~$500 entry fee, refunded on first payout).
8. **Multi-instrument expansion** — Same architecture, same frameworks, different data feeds. Priority instruments:
   - NAS100 (US indices, high liquidity, clean SMC structure)
   - EURUSD (most liquid forex pair)
   - XAGUSD (silver, correlated to gold, different volatility)
   - Each instrument needs: data export via MT5, ATR/SL threshold calibration, backtest validation (~$40 per instrument)
   - 5 instruments × 3 kill zones × 250 days = 3,750 session-windows/year
9. **Bayesian scoring engine** — After 200+ trades, replace AI confidence scores with empirically calculated conditional probabilities: P(WIN | framework, grade, kill_zone, regime, etc.)
10. **Multiple prop firm accounts** — Scale to 3-5 funded accounts across different firms for income multiplication.

### Model Strategy
- **Bulk backtesting:** Sonnet + Batch API (cheapest)
- **Live trading:** Opus (maximum accuracy, ~$0.80/day — negligible vs capital at risk)
- **Debate engine (when re-enabled):** Opus for Bull, Bear, and Judge agents

## Architecture Reminders

- **Billing modes:** `--billing api` (live trading), `--billing subscription` (Max plan CLI), `--billing batch` (Batch API, use `batch_backtest.py`)
- **Pre-screening:** Enabled by default in batch script. `--no-prescreen` to disable.
- **Dual windows:** London 07:00-09:30, NY 13:00-15:30. Both evaluated per session.
- **Debate engine:** Still disabled. Redesign deferred until system is validated.
- **Data location:** MT5 CSVs in `data/historical/`. Old HuggingFace backup in `data/old_huggingface_backup/`.
- **MT5 export script:** `mt5_export.py` on the Windows MSI laptop Desktop. Exports D1/H4/H1/M15 CSVs from any MT5 broker demo account. Will be needed again when adding new instruments (NAS100, EURUSD, etc.).

## My Profile (Unchanged)
- 6+ years coding (TypeScript primary, Python comfortable)
- Developing SMC/ICT trader
- Pushes back on reasoning errors, catches contradictions
- Wants brutal honesty, no sugarcoating
- Budget-conscious, every dollar justified
- On Claude Max 5x ($100/month)
- Goal: disciplined, independent gold trader with AI system → prop firm funded accounts

## Standing Principles
- Never re-run in-sample data to validate fixes — use fresh data
- Don't overfit to small samples — need 80-100+ trades minimum
- The system is still effectively session_sweep only — frameworks 2-4 need investigation
- Pre-screening on universal requirements only — never filter on framework-specific conditions
- Each improvement must be tested before the next one starts
- The backtest without session context is a conservative floor for live performance
