# F27 — Backward outcome injection prototype (A/B test)

**Date:** 2026-04-28
**Status:** PRE-REGISTERED design before any data is collected.
**Branch:** `research/f27-backward-outcome-injection-prototype` (worktree).
**Phase:** Phase 2, F27 (rank #2 in Phase-2 program).

---

## 1. Hypothesis (pre-registered)

> Adding the AI's most-recent N closed trade outcomes (W/L + realized R + regime + framework) into its prompt context lifts decision quality on the same-instrument cohort.

**Operationalized:** Filtered-subset realized R increases by **>= +0.10R/trade** vs. the no-feedback baseline, on a held-out cohort of 30-50 historical CANDIDATEs. Equivalently, **>= +10pp WR shift** in the surviving CAND subset.

## 2. Threshold + verdict bands

| Mean delta R/trade (treatment - baseline) | Verdict |
|---|---|
| +0.10R or more | **GO** — cohort lift demonstrated; recommend expansion to 30-50 CAND cohort |
| -0.05R to +0.10R | **INCONCLUSIVE/NULL** — kill prototype, no clear signal |
| -0.05R or less | **NO_GO** — feedback hurts; document hypothesis falsified |

**Kill criterion:** If first 30 paired evals show <±0.05R diff, halt immediately and report INCONCLUSIVE. (For pilot n=11, this fires implicitly: full cohort is < 30, so we report final verdict on n=11 directly.)

## 3. Cohort: A4 trending_bull XAUUSD (n=11)

**Why this cohort:**
- Already-replayed via current production prompt (post-HALLUC-1 + S79 + 4 sister fixes); baseline +0.818R/trade documented as A4 GREEN.
- M1 fill simulator already wired (`fill_simulator_m1_full_cohort.py`); paired realized R is computable from same M1 ground truth without new infrastructure.
- Cheapest pilot: 11 records ~ $1.05/replay; baseline + treatment ~ $2.10 total.
- Single regime (trending_bull) + single side (LONG) + single framework (ob_retest) — homogeneous; reduces noise.

**Caveat (risk to internal validity):**
- Cohort spans 2026-04-15 through 2026-04-17 only (3 calendar days). Past-outcome telemetry must be sourced from BEFORE 2026-04-15. Trade history available (`trades_unified.csv` from b_deep_audit) ends at 2026-03-13. There's a 33-day gap between most-recent-past-outcome and cohort. **This is a deliberate choice for pilot; expansion would close the gap with H2-2026 enriched data**.
- The cohort has CR=100% baseline (all 11 candles emitted CANDIDATE). Treatment can only flip to NO_TRADE/WAIT or modify trade_parameters — it cannot generate new CANDIDATEs from non-CAND prior states (no NO-CAND prior states in cohort).

## 4. Past-outcome telemetry source

`research/b_deep_audit_2026-04-19/phase1/_delta_scratch/trades_unified.csv` — 151 closed trades 2024-03-01 through 2026-03-13. Per-trade fields: symbol, date, kill_zone, framework, direction, outcome (WIN/LOSS/BREAKEVEN), r_multiple, daily_bias.

**Selection rule (pilot):** For each cohort record at candle_time_utc T, take the MOST-RECENT N=10 closed trades with `date < T.date()`. This will be the same 10 trades for every cohort record (since cohort spans only 3 days). Acceptable for pilot.

**Last 10 trades pre-2026-04-15 (computed):**

| date | symbol | direction | framework | outcome | R | bias | kz |
|---|---|---|---|---|---|---|---|
| 2026-02-04 | XAUUSD | SHORT | ob_retest | WIN | +0.08 | bullish | london |
| 2026-02-04 | XAUUSD | SHORT | ob_retest | LOSS | -1.00 | bullish | ny |
| 2026-02-05 | XAUUSD | LONG | ob_retest | WIN | +0.20 | bullish | london |
| 2026-02-05 | XAUUSD | LONG | ob_retest | LOSS | -0.32 | bullish | ny |
| 2026-03-06 | XAUUSD | LONG | session_sweep | WIN | +3.03 | bullish | ny |
| 2026-03-09 | XAUUSD | LONG | ob_retest | WIN | +0.23 | bullish | london |
| 2026-03-10 | XAUUSD | LONG | ob_retest | WIN | +0.15 | bullish | ny |
| 2026-03-12 | XAUUSD | LONG | ob_retest | LOSS | -1.00 | bullish | london |
| 2026-03-13 | XAUUSD | SHORT | session_sweep | LOSS | -1.00 | bullish | ny |
| (1 more from 2026-01-29 to fill 10) | XAUUSD | LONG | ob_retest | LOSS | -1.00 | bullish | london |

Aggregate: 5W / 5L, mean R = +0.037 (basically breakeven). Mix of LONG/SHORT, ob_retest dominates.

## 5. Design choice: D2 (prose summary)

Per task spec, three options were on the table (D1 tabular JSON, D2 prose summary, D3 stratified-by-regime). **D2 is chosen for the pilot** because:
- Most "model-friendly" — Sonnet 4.6 integrates prose context far better than tabular numerics in prompt experiments.
- Surfaces signal fastest if hypothesis is real.
- Smallest token footprint (~150-300 tokens) — minimal cache invalidation cost.
- Easiest to iterate on if pilot is GO.

**D2 template (the F27 feedback block):**

```
## Recent trade outcomes (most recent 10 closed; treat as historical signal, not session memory)

In your last 10 closed trades, the system recorded 5 wins and 5 losses for a mean of +0.04R per trade.
- Recent wins: 5 LONG ob_retest in trending_bull / bullish-bias (R +0.20, +0.23, +0.15) and 1 LONG session_sweep at +3.03R, plus 1 SHORT ob_retest at +0.08R.
- Recent losses: 4 LONG ob_retest losses (R -1.00, -0.32, -1.00, -1.00) — all in bullish-bias regime, mostly during NY/London kill zones.

Use this as a calibration signal on your decision-making, not as a substitute for evaluating this candle's MSO. The outcomes above are HISTORICAL telemetry from previously-closed trades, NOT the current session's reasoning context.
```

**Where it lives in the prompt:** Injected via the existing `additional_context` parameter of `build_user_message()`. Goes AFTER static system prompt + KB + dynamic MSO, BEFORE "## Current Time:" and the "Evaluate this M15 candle" instruction. Production code path NOT modified — research scripts only.

**Why "treat as historical signal, not session memory" framing:** Per memory `feedback_session_memory_disabled_55pct_cr_suppression`, session memory was disabled because it caused the AI to defer/abandon decisions ("AI saw prior NO_TRADE rationale and copied it"). F27 risk is the same failure mode if framing is sloppy. The disclaimer explicitly tells the AI: this is outcome telemetry, not journal. Different mechanism, different failure modes.

## 6. Methodology

### 6.1 Baseline

Re-run the existing A4 replay with CURRENT production prompt (HEAD of main at branch creation), no F27 block. This re-creates `replay_outcomes.jsonl` (writes to `baseline_replay_outcomes.jsonl`). Identical methodology to A4. **Reproducibility check**: should match `research/a4_trending_bull_replay_2026-04-28/replay_outcomes.jsonl` decision distribution closely (modulo Sonnet 4.6 thinking-token nondeterminism — even at temperature=0 it has non-zero variance).

### 6.2 Treatment

Same cohort, same model (`claude-sonnet-4-6`), same effort (`max`), same caching (1h ephemeral on system block), same temperature (0), same max_tokens (2000) — but with the F27 D2 prose summary injected via `additional_context`.

### 6.3 Comparison metrics

1. **Decision-flip table (2x2):** baseline_decision × treatment_decision (CAND/NO_TRADE/WAIT).
2. **Trade-parameter delta:** for surviving-CAND-in-both records, mean delta on entry_price, stop_loss, take_profit_1, sl_buffer_applied.
3. **Paired realized R via M1 fill simulator** (`fill_simulator_m1_full_cohort.py`, copied + parameterized for both runs):
   - Per-record: `delta_R = treatment_R - baseline_R` (with NEVER_FILLED treated as R=0; STILL_OPEN at sim end uses MTM).
   - Mean delta R, paired Wilcoxon signed-rank test, sign-test on flips.
4. **Cost ledger:** total spend logged to `COST_LEDGER.md` after each run.

### 6.4 Statistical interpretation (for n=11)

Paired Wilcoxon at n=11 has weak power; we expect at threshold of n=11 to need a |delta R| >= ~0.4 to detect at p<0.05. This is below our +0.10R threshold, so **the verdict is descriptive (mean delta + sign of flip table), not inferential**. p-value reported only as ancillary metric.

## 7. Cost cap (HARD)

**Total budget: $10. Stop-and-report at $5.**
- Baseline n=11: ~ $1.05.
- Treatment n=11: ~ $1.05 (same input/output token volume, +200-300 tokens for feedback block; cache write is one-shot).
- Estimated total: ~ $2.10. Buffer ~ 2x for retries / ranking ablations.

## 8. Constraints

- No `src/` or `prompts/` modifications.
- F27 builds the feedback block in research-only code.
- A4 OOS holdout NOT touched.
- No push to remote.
- Worktree branch only.

## 9. Anti-patterns avoided

- **Not session memory.** F27 is structured outcome telemetry (W/L + R + regime + framework, last N=10), bounded, with explicit "not session memory" disclaimer. Session memory was free-form reasoning context that suppressed CR by 55%; F27 is one-shot factual prior, framed as a calibration signal.
- **Not recency-biased pseudo-evidence.** Past trades drawn from MOST-RECENT N closed before candle_time, no peeking forward, no leakage.
- **Not coupled to the prompt.** Production prompt unchanged; F27 is purely a prompt-injection harness via the existing `additional_context` parameter.
- **Not a hard gate.** Even if F27 GREEN, the next step is more cohort coverage + statistical power, not immediate production wiring.
