# T2c Cross-Effort Comparison: Sonnet 4.6 Shootout Results

**Date:** 2026-04-12
**Model tested:** claude-sonnet-4-6 (Sonnet 4.6)
**Baseline:** claude-sonnet-4-20250514 (Sonnet 4, no effort param)
**Effort levels tested:** medium, high, max
**N MSOs per condition:** 121 (all originally CANDIDATE under Sonnet 4)
**Total experiment cost:** $12.87 across 363 API calls

---

## Summary Table

| Metric | Sonnet 4 (baseline) | Medium | High | Max |
|--------|:-------------------:|:------:|:----:|:---:|
| CANDIDATE rate | 100% (by construction) | 13.2% (16) | 17.4% (21) | 16.5% (20) |
| WR of CANDIDATEs | 64.5% (n=121) | 50.0% (n=16) | 52.4% (n=21) | 60.0% (n=20) |
| CR × WR | 0.6446 | 0.0661 | 0.0909 | 0.0992 |
| Rejected trades WR | — | 66.7% | 67.0% | 65.3% |
| NO_TRADE count | 0 | 89 | 88 | 100 |
| WAIT count | 0 | 16 | 12 | 1 |
| Avg confidence | ~80 | 74.8 | 74.0 | 75.7 |
| Avg output tokens | ~500 | 1,201 | 1,270 | 1,259 |
| Cost | ~$4 | $4.21 | $4.34 | $4.32 |
| McNemar p | — | <0.001 | <0.001 | <0.001 |

---

## Key Finding: Sonnet 4.6 FAILS at all effort levels

**Verdict: DO NOT upgrade from Sonnet 4 to Sonnet 4.6.**

All three effort levels exhibit the same Opus-pattern over-rejection:
- 83-87% of trades rejected (vs 0% for Sonnet 4)
- Rejected trades WIN at 65-67% — the model removes winning trades, not losers
- CR×WR collapses 6.5-10x from baseline (0.64 → 0.07-0.10)
- Even the WR on the trades Sonnet 4.6 DOES accept is worse than baseline (50-60% vs 64.5%)

---

## Effort Level Comparison

### Does effort level matter within Sonnet 4.6?

Barely. All three are catastrophically worse than Sonnet 4. But within the Sonnet 4.6 failure:

| Ranking | Level | CR | WR | CR×WR | WAIT decisions |
|---------|-------|----|----|-------|----------------|
| 1 (least bad) | max | 16.5% | 60.0% | 0.0992 | 1 |
| 2 | high | 17.4% | 52.4% | 0.0909 | 12 |
| 3 (worst) | medium | 13.2% | 50.0% | 0.0661 | 16 |

- **Max** has the best WR (60%) and fewest non-standard decisions (1 WAIT)
- **High** has the most CANDIDATEs (21) but lowest WR (52.4%)
- **Medium** is worst on all metrics and produces the most WAIT decisions (16)
- None comes remotely close to the Sonnet 4 baseline

### WAIT decisions (non-standard output)

Sonnet 4.6 introduced WAIT decisions not used by Sonnet 4:
- Medium: 16 WAITs (13.2% of evaluations)
- High: 12 WAITs (9.9%)
- Max: 1 WAIT (0.8%)

Higher effort reduces non-standard outputs. Max almost never uses WAIT.

---

## Rejected Trades Analysis

All 121 MSOs were CANDIDATE under Sonnet 4. Sonnet 4.6 rejected most of them.

| Level | Rejected N | Rejected Wins | Rejected Losses | Rejected WR |
|-------|-----------|--------------|----------------|-------------|
| Medium | 105 | 70 | 35 | 66.7% |
| High | 100 | 67 | 33 | 67.0% |
| Max | 101 | 66 | 35 | 65.3% |

All three reject proportionally — ~66% of rejected trades were winners. Since the base WR is 64.5%, Sonnet 4.6 is rejecting **randomly with respect to outcome**. It does not improve selectivity — it just kills volume.

This is identical to the Opus/thinking pattern from April 5: the model interprets "at or near the OB zone" hyper-literally and finds reasons to reject.

---

## Token and Cost Analysis

| Level | Avg input tokens | Avg output tokens | Cost/call | Projected monthly (17 trades) |
|-------|:----------------:|:-----------------:|:---------:|:----------------------------:|
| Sonnet 4 baseline | ~5,500 | ~500 | ~$0.02 | ~$0.40 |
| Medium | 5,601 | 1,201 | $0.035 | $0.59 |
| High | ~5,600 | 1,270 | $0.036 | $0.61 |
| Max | ~5,600 | 1,259 | $0.036 | $0.61 |

Sonnet 4.6 produces 2.4-2.5x more output tokens across all effort levels. The extra output is over-reasoning, not better analysis. Cost impact is negligible (~$0.20/month more).

Interesting: output tokens are nearly identical across effort levels (1,201 vs 1,270 vs 1,259). The effort parameter affects reasoning depth, not output length. The model simply writes more detailed rejections at all levels.

---

## Confidence Scores

Confidence remains a rubber stamp, as found in T2a:

| Level | Avg confidence (CANDIDATEs) |
|-------|-----------------------------|
| Sonnet 4 | ~80 |
| Medium | 74.8 |
| High | 74.0 |
| Max | 75.7 |

All cluster around 75-80. No discriminatory value.

---

## Root Cause Hypothesis

Sonnet 4.6 over-rejects because:

1. **Model alignment shift:** Sonnet 4.6 is more cautious/conservative than Sonnet 4. The prompts were calibrated for Sonnet 4's risk tolerance.

2. **Hyper-literal zone interpretation:** Same pattern as Opus. The model reads "price must be at or near the OB zone" and applies stricter distance thresholds than Sonnet 4 did.

3. **Not an effort problem:** All three effort levels produce nearly identical behavior (13-17% CR, 50-60% WR, 65-67% rejected WR). The effort parameter modulates reasoning depth, not decision threshold.

4. **Not a cost problem:** Total experiment cost was $12.87. Monthly cost difference between models is <$0.25.

---

## Actionable Conclusions

1. **Keep Sonnet 4 (`claude-sonnet-4-20250514`) in production.** It works. Sonnet 4.6 does not.

2. **Do NOT change the effort parameter** on the current Sonnet 4 production config. The default (high) is fine. Effort tuning is irrelevant when the model version is wrong.

3. **If Sonnet 4 is deprecated:** The prompt must be re-calibrated for Sonnet 4.6's stricter interpretation. This would be a T3-level prompt engineering effort (modify zone proximity language, adjust rejection thresholds, re-validate on batch data).

4. **Monitor model availability:** If Anthropic retires `claude-sonnet-4-20250514`, we need advance warning to run prompt recalibration.

5. **The effort parameter is not worthless** — max effort does produce the best WR (60% vs 50-52%) within Sonnet 4.6. If we ever recalibrate for Sonnet 4.6, start with effort=max.

---

## Data Files

- `research/academic_pipeline/data/T2c_medium_results.json` — Full medium results
- `research/academic_pipeline/data/T2c_high_results.json` — Full high results
- `research/academic_pipeline/data/T2c_max_results.json` — Full max results
- `research/academic_pipeline/data/T2c_medium_cost_log.csv` — Medium cost log
- `research/academic_pipeline/data/T2c_high_cost_log.csv` — High cost log
- `research/academic_pipeline/data/T2c_max_cost_log.csv` — Max cost log
- `research/academic_pipeline/results/T2c_medium_results_v1.md` — Medium report
- `research/academic_pipeline/results/T2c_high_results_v1.md` — High report
- `research/academic_pipeline/results/T2c_max_results_v1.md` — Max report
