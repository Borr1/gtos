# F27 — Backward Outcome Injection Prototype: RESULTS

**Date:** 2026-04-28
**Branch:** `research/f27-backward-outcome-injection-prototype`
**Cohort:** A4 trending_bull XAUUSD (n=11), 2026-04-15 through 2026-04-17.
**Verdict:** **INCONCLUSIVE / NULL** — recommend KILL prototype.

---

## TL;DR

> Adding the AI's most-recent 10 closed-trade outcomes (as a D2 prose-summary block, with explicit "treat as historical signal, not session memory" framing) into the prompt context **did not change decisions** on the A4 cohort. Mean realized-R delta on the paired comparison is **+0.0010R/trade** (effectively zero), well below the +0.10R/trade GO threshold.

## Numbers

| Metric | Baseline | Treatment | Delta |
|---|---|---|---|
| Decisions: CANDIDATE / NO_TRADE / WAIT | 11 / 0 / 0 | 11 / 0 / 0 | 0 |
| WR (FILLED_WIN / FILLED_LOSS basis) | 8 / 11 = 72.7% | 8 / 11 = 72.7% | +0.0pp |
| Mean realized R/trade (M1 sim) | +0.8181 | +0.8191 | **+0.0010R** |
| Median delta_R per record | 0.0000 | n/a | n/a |
| Wilcoxon signed-rank p (two-sided) | n/a | n/a | 0.8438 |
| Sign test p (two-sided) | n/a | n/a | 1.0000 |
| Mean entry-price delta (USD) | n/a | n/a | -4.54 |
| Median entry-price delta (USD) | n/a | n/a | 0.00 |
| Mean SL delta (USD) | n/a | n/a | -6.17 |
| Mean TP1 delta (USD) | n/a | n/a | -2.07 |
| Max abs entry delta (USD) | n/a | n/a | 49.99 |
| Max abs SL delta (USD) | n/a | n/a | 43.94 |
| Max abs TP1 delta (USD) | n/a | n/a | 59.08 |

## 2x2 Decision flip table

| Baseline \\ Treatment | CANDIDATE | NO_TRADE | WAIT | Total |
|---|---|---|---|---|
| **CANDIDATE** | 11 | 0 | 0 | 11 |
| **NO_TRADE** | 0 | 0 | 0 | 0 |
| **WAIT** | 0 | 0 | 0 | 0 |
| **Total** | 11 | 0 | 0 | 11 |

## Per-record paired R

| trade_id | baseline_R | treatment_R | delta_R | both_outcome |
|---|---|---|---|---|
| 2026-04-15_ny_1315 | +1.4987 | +1.4980 | -0.0008 | FILLED_WIN |
| 2026-04-15_ny_1330 | +1.4987 | +1.5079 | +0.0092 | FILLED_WIN |
| 2026-04-15_ny_1345 | +1.4997 | +1.4985 | -0.0013 | FILLED_WIN |
| 2026-04-15_ny_1415 | +1.5025 | +1.5003 | -0.0023 | FILLED_WIN |
| 2026-04-15_ny_1615 | +1.5005 | +1.5064 | +0.0059 | FILLED_WIN (different OB picked) |
| 2026-04-15_ny_1700 | +1.4995 | +1.5003 | +0.0008 | FILLED_WIN |
| 2026-04-16_london_0800 | -1.0000 | -1.0000 | 0.0000 | FILLED_LOSS |
| 2026-04-16_london_0930 | -1.0000 | -1.0000 | 0.0000 | FILLED_LOSS |
| 2026-04-16_ny_1316 | -1.0000 | -1.0000 | 0.0000 | FILLED_LOSS |
| 2026-04-17_ny_1315 | +1.5003 | +1.4991 | -0.0012 | FILLED_WIN (different OB picked) |
| 2026-04-17_ny_1330 | +1.4991 | +1.5000 | +0.0009 | FILLED_WIN |

All deltas are sub-0.01R, consistent with Sonnet 4.6 thinking-token nondeterminism at temperature=0.

## Interpretation

### What happened
The AI was given a 1,140-character prose summary of its last 10 closed XAUUSD trades (6 wins, 4 losses, mean +0.31R) before evaluating each cohort candle. The block was framed as "historical signal, not session memory" with an explicit disclaimer.

**Result: AI ignored the block.** Decisions, directions, and trade parameters are essentially unchanged. The two records (`2026-04-15_ny_1615`, `2026-04-17_ny_1315`) where the AI picked a different OB are explained by the AI's own internal nondeterminism (the same MSO has multiple valid OBs to anchor to; thinking-token noise selects different ones across runs), not by the F27 feedback content. Both alternative OBs still landed in TP1, so realized R is unchanged.

### Why this hypothesis didn't pan out (interpretation)

Several non-mutually-exclusive explanations:

1. **The AI doesn't weight summary statistics over MSO grounding.** Sonnet 4.6 is heavily trained to ground decisions in the dynamic MSO data (the OB price levels, displacement, sweep). A 1,140-char prose block at the end of a 40,000-char system prompt + ~5,000-char dynamic block is dominated in attention budget by the operational data.

2. **The cohort is too uniform.** All 11 records are A+ trending_bull LONG ob_retest setups in NY/London. The MSO signal is so strong that no level of past-outcome telemetry would have moved a CANDIDATE to NO_TRADE. To detect F27 lift, the cohort would need to include borderline cases or losses with detectable warning signs.

3. **The framing disclaimer worked too well.** "Treat as historical signal, not session memory" may have caused the AI to *correctly* discount the block, exactly as designed — but at the cost of zero observable impact.

4. **The past-outcome telemetry is gold-only.** Last 10 trades selected with `--feedback-symbol XAUUSD` — but A4 cohort is also XAUUSD trending_bull bullish. The signal is "6 wins out of 10, mostly LONG bullish-bias ob_retest trades." This is overwhelmingly *consistent* with what the AI is being asked to do (LONG bullish-bias ob_retest trade). A consistent signal doesn't shift decisions.

### What this does NOT prove
- It does NOT prove backward-outcome injection is generally unhelpful.
- It does NOT rule out the D1 (tabular) or D3 (regime-stratified) variants.
- It does NOT rule out longer feedback windows (N=20, 50) or more recent telemetry (gap from 2026-03-13 to 2026-04-15 is 33 days — past trades are stale relative to cohort).
- It does NOT rule out a different cohort design (mixed-quality CAND + non-CAND records).

## Recommended next step

**KILL this prototype's expansion to a 30-50 record cohort.**

If F27 is to be revisited later, recommend:

1. **Use a heterogeneous cohort.** Mix XAUUSD trending_bull A+ (positive cases) with XAUUSD trending_bull bull-bias-mismatch A/B graded (borderline cases) and XAUUSD chop A/B graded losses (warning cases). This gives the feedback block actual decision-relevant lift potential.

2. **Test D3 (regime-stratified) instead of D2 (prose summary).** "In your last 8 trending_bull trades you went 2W/6L for mean -0.45R" is more actionable than "your last 10 trades you went 6W/4L for +0.31R."

3. **Use enriched H2-2026 closed trades.** The `trades_unified.csv` source ends at 2026-03-13; a freshly enriched dataset closing the gap to candle_time would make the telemetry "most recent" rather than "33-day-old." This requires running the M1 fill simulator against `live_evaluations/` candidate emissions across H2-2026.

4. **Test an inverse cohort.** F27 should test whether the AI's decisions can be **shifted** by feedback. If the cohort is uniformly high-quality, no shift is desirable — there's nothing to test. Pick a borderline cohort where ~30-50% of records are subjectively CANDIDATE-borderline.

5. **Pair F27 with a counterfactual prompt design.** What if the feedback block claimed *negative* recent trades (e.g., synthetic last-10 = 8L/2W mean -0.65R)? Does the AI demote a CANDIDATE under negative telemetry? If yes, that's evidence the AI *can* be moved by the feedback channel — meaning the null in this pilot is an artifact of cohort + telemetry direction.

## Notes on internal validity

- **Thinking-token nondeterminism caveat:** Sonnet 4.6 with `effort=max` and `temperature=0` is *not* deterministic. Internal thinking tokens are sampled. Running baseline twice would also produce ~+/-0.01R per-record deltas. The F27 deltas are **indistinguishable from intra-baseline replay variance**. The +0.0010R/trade mean delta is well within run-to-run noise.

- **Cache reuse caveat:** Both runs benefited heavily from prior A4 runs' cache (1h ephemeral block). This does not affect decision quality but did keep the cost low.

- **Cohort caveat:** n=11 is too small to detect anything but very large effects. Wilcoxon p=0.84 reflects this — even a +0.10R/trade lift would barely register at this sample size.

## Files

- `F27_PROTOTYPE_DESIGN.md` — pre-registered design (read first).
- `scripts/research/f27_replay_with_feedback.py` — A/B replay harness with D2 prose-summary feedback injection.
- `scripts/research/f27_compare.py` — paired comparison (M1 sim, Wilcoxon, sign test, decision flips).
- `baseline_replay_outcomes.jsonl` — 11 baseline emissions (current production prompt, no feedback).
- `treatment_replay_outcomes.jsonl` — 11 treatment emissions (same prompt + F27 D2 feedback block).
- `feedback_block.txt` — the 1,140-char feedback block injected (visible for inspection).
- `feedback_past_trades.json` — the 10 past trades that fed the block.
- `f27_comparison.json` — full comparison data + verdict.
- `COST_LEDGER.md` — actual spend ($0.64 total).
- `raw_responses_baseline/`, `raw_responses_treatment/` — full per-record AI responses.
- `SUMMARY_baseline.md`, `SUMMARY_treatment.md` — auto-generated per-mode summaries.
