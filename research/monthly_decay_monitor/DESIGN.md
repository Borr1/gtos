# Monthly-Decay Shadow Monitor — Design

**Purpose.** Detect edge decay at month/week granularity rather than quarterly.
CLAUDE.md records a quarterly-decay trend (73% → 71% → 64% → 59%) and session-39
comprehensive extraction surfaced a WITHIN-2026 drop (XAUUSD Jan 45.5% / Feb 75.0% /
Mar 33.3% / Apr 10.0%; H1 vs H2 chi-square p=0.006). Alarm fast, not quarterly.

**Scope.** Infrastructure / observability only. No trading-logic change.
Log-only shadow monitor; fires alerts to a markdown report the CEO reviews.

## Data sources

| Source | Path | Priority | Outcome field | R field |
|---|---|---|---|---|
| Live trade records (A3 v1.1) | `knowledge_base/trade_records/{SYMBOL}/*.json` | 1 | derived from `exit.exit_reason` and `exit.realized_R` | `exit.realized_R` / `instrumentation.realized_R` |
| Live trade records (v1.0) | same path, older records | 1 (fallback) | derived from `exit.exit_type` / `exit.actual_r` | `exit.actual_r` / `exit.realized_R` |
| Simulator — A1 ADR-005 backtest | `research/a1_adr005_backtest/slices/**/all_results.json` | 2 | row `outcome` ∈ {WIN, LOSS, UNFILLED, ...} | row `r_multiple` |
| Simulator — F3 backtest 2026-04-24 | `research/f3_backtest_2026-04-24/**/all_results.json` | 2 | same schema | same schema |
| Simulator — T7 live simulation | `research/t7_live_simulation/all_results_*.json` | 2 | same schema | same schema |

### Union + dedup key
`(instrument, candle_time_iso)`. First source encountered wins. Priority order:
live records → A1 → F3 → T7 (live data is the ground truth once it exists;
simulators fill history before live).

### Outcome normalization
- **Trades counted.** Anything with `outcome ∈ {WIN, LOSS, BE}` and a numeric R.
  `UNFILLED`, `None`, `PENDING` are excluded (didn't produce a trade).
- **Win = R > 0.** This is strict: BE (R=0) is NOT a win.
- **R clipping.** Cap at [-5R, +5R] before aggregation to prevent outlier
  domination of expectancy (fat-tail discipline, per memory
  `project_distributional_findings.md`).

## Thresholds

| Alert | Condition | n_current gate | Severity |
|---|---|---|---|
| WR decay | current-month WR < 3-month rolling-baseline WR − 15pp | n_current ≥ 10 | HIGH |
| Expectancy decay | current-month Exp R < rolling Exp R − 0.25R | n_current ≥ 10 | HIGH |
| Consecutive weakness | 3 consecutive weeks with WR < breakeven | n_week ≥ 5 each | HIGH |
| Insufficient sample | n_current < 10 | — | INFO |

### Per-instrument breakeven WRs (from CLAUDE.md)
XAUUSD 35.7% / US30 34.5% / USDJPY 40.0% / GBPJPY 41.7% / GBPUSD 37.5%.

Default for unlisted instruments: 40% (conservative guess until data accrues).

## Statistical methods

- **WR.** Proportion win_count / n_trade. Wilson 95% CI for the proportion.
- **Expectancy.** Mean realized R. 95% CI via BCa bootstrap with ≥1000 iterations.
- **Breakeven comparison.** Uses the breakeven table above. Weekly check
  is a strict inequality against the breakeven value.

## Output schema

`research/monthly_decay_monitor/YYYY-MM_report.md`:

1. Header: generated-at, coverage date range, total trades per-instrument,
   data-source mix.
2. Per-instrument monthly table: month, n, WR, WR Wilson 95% CI, Exp R,
   Exp 95% bootstrap CI.
3. Per-instrument weekly table: week (ISO year-week), n, WR, Exp R (last 12 weeks).
4. Alert section: each fired alert with evidence citation.
5. Trend ASCII: monthly WR over time per instrument (bar chart).
6. Forecast: under current month's run-rate, how many trades accumulate in
   30 days; and given current decay slope, will the HIGH alert fire?

## Commit plan (additive, worktree branch)

1. Design doc.
2. Script `scripts/monthly_decay_monitor.py` (stdlib + numpy — no new deps).
3. Tests `tests/test_monthly_decay_monitor.py` (≥6 test cases).
4. First-run report under `research/monthly_decay_monitor/2026-04_report.md`.
5. Optional watchdog hook (only if time permits).

Do NOT merge to main; leave for CEO diff review.

## Known limits / unresolved

- Live records before A3 v1.1 (`b1fcf5c`) lack `exit` data — 0/148 existing
  records have a populated `exit`. Until FTMO paid challenge data accumulates
  post-2026-04-27, the monitor runs primarily on simulator history.
- GBPUSD breakeven is estimated (37.5%); refine when its batch stats are
  published.
- The "current-month WR vs 3-month baseline" comparison cannot discriminate
  edge-decay from regime-shift. Both are actionable (risk-reduce), so the
  alert is still correct action — but attribution requires manual review.
- UNFILLED CANDIDATEs are excluded, which may mask a regime where setups
  are present but consistently miss entry (the "slow bleed" death mode).
  Weekly CAND-rate monitor (out of scope here — use existing CUSUM
  candidate-rate monitor) complements this one.
