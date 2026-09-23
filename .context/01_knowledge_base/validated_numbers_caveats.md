# Validated Numbers — Caveats & Quarterly Decay Detail

Companion to `CLAUDE.md` § Validated Numbers. CLAUDE.md keeps the headline tables; long-form caveats live here.

## XAUUSD 62% WR — H2-2026 decay caveat

**Headline:** XAUUSD WR vs breakeven = 62.0% (n=129), Bonferroni p = 3.42e-08, batch Oct 2025–Mar 2026.

**Caveat:** Derived under v1 production detector (LONG-only labels — v1 emitted 100% bullish labels across 8,086 H1 windows; SHORT setups never reached the gate). H2-2026 live data shows decay versus that backtest baseline:

| Month | WR    | n  | Note |
|-------|-------|----|----|
| Jan   | 45.5% | 11 | First half-year |
| Feb   | 75.0% | 20 | First half-year |
| Mar   | 33.3% | 15 | Second half-year |
| Apr   | 10.0% | 10 | Second half-year |

H1-2026 (Jan+Feb): 64.5% n=31 vs H2-2026 (Mar+Apr): **24.0%** n=25. Chi-square p=0.006.

**Action:** Re-derive baseline post v2 promotion + ≥30 fresh live trades. Tracked under unresolved item #9 ("XAUUSD H1→H2 2026 WR decay — HIGH SIGNAL"). Monthly-decay shadow monitor S1 (`405a75d`) is live and observing.

**Why 62% remains in the headline table.** It is the only XAUUSD WR number with Bonferroni-survival evidence. Replacing it pre-emptively with the (much smaller, decay-tainted) live number would (a) violate "no fabricated numbers" by inventing a baseline that has not been re-derived under v2 and (b) erase the empirical reference point against which decay is measured. The dagger marker (†) flags the caveat.

## Quarterly WR decay — full series

CLAUDE.md "Backtest-only" bullet shows the trend. Full numbers:

| Quarter | WR | Note |
|---------|----|----|
| Q3 2025 | 73.2% | First batched quarter |
| Q4 2025 | 71.4% | |
| Q1 2026 | 63.6% | |
| Q1-2026 (revised) | 59.4% | After v1 detector LONG-only artifact noted |
| Q2-2026 partial | **24.0%** | n=25, Mar+Apr 2026 only |

**Stat test.** Chi-square H1-2026 vs H2-2026 (item #9) p=0.006. Trend is real; cause is unknown — candidates discussed in `research/reviews_2026-04-24/` and weekend deferred-master items. v2 promotion (item #11 GO) is one mitigation; live-data accumulation post-Monday will discriminate among hypotheses.

**Do not extrapolate.** Q2-2026 partial is n=25 split across two months and four instruments at first launch. Wilson CIs are wide; treat as alarm + monitor signal, not a new baseline. v1 LONG-only-derived numbers in CLAUDE.md remain the working baseline until ≥30 live SHORT trades accumulate post v2 promotion.

## Backtest-only numbers — extended provenance

CLAUDE.md "Backtest-only" bullet list captures the headline. Provenance notes:

- **Session memory doubles expectancy in batch (+0.66R vs +0.33R).** Live test (T2b) proved 55% CR suppression, p=0.007 — feature disabled. Batch-vs-live divergence: AI exploits memory in unrealistic ways during retrospective batch (lookahead-leak via session continuity narrative); under live conditions it strangles candidate generation. Documented as the canonical "batch ≠ live" example.
- **AI filter adds +0.300R/trade in batch.** Cross-checked under realized-R during session 39 Phase 1; touch-count-stratified outcomes (item #8) reveal walk-level evidence is not predictive of realized R. Per-stratum live performance differs from batch-derived expectations; treat batch +0.300R as upper-bound estimate.
- **AI adds ~0pp to entry WR over mechanical OB entries.** The edge is zone detection, not zone selection. Reinforces edge mechanism: OB precision drives WR, AI primarily reduces malformed candidate rate.
- **Confidence scorer is a rubber stamp.** 98% of CANDIDATEs receive confidence=80; flag set to `shadow` mode, no trading effect. Cherry-pick attempts (item #13 g) rejected at p=0.78.
- **Monte Carlo: 99.4% P(pass FTMO) at 1% risk.** MC inputs: batch WR 65%, expectancy +0.200R, n=1000 simulations. Sensitivity analysis: P drops to ~85% at 50% WR, ~50% at 45% WR. April 2026 live decay puts XAUUSD-only WR at 10% — but FTMO P is fleet-aggregate, and other instruments hold their batch numbers within Wilson CIs.
- **Trailing stop: +38.9R to +52.4R over 100 trades.** Conservative variant trails by 1×ATR after 1R hit; aggressive variant trails by 0.5×ATR. Not deployed — partial-close Variant C (33% @ 1R) was selected instead per session 23.

## Canonical numbers — context

CLAUDE.md table shows the headline ratios. Notes:

- **Batch population 367 trades.** Includes Oct 2025 → Mar 2026 across 5 instruments. Baseline reference for backtest claims.
- **2026-only WR 59.5%.** Filtered on Jan-Mar 2026 (pre-decay), n≈100. Expected to drop with H2-2026 inclusion (see decay table above).
- **CANDIDATE rate (baseline) 10.3% of evaluated setups.** Pre-AI gates filter out the rest. Active gates: Gate 0 deployment.phase, Gate 1 touch_count, Gate 2 sl_beyond_ob, plus pre-AI POI availability gate broadened 2026-04-25.
- **Inverted TP rate 7.03% of CANDIDATEs.** Auto-corrected by `permissions.py` (mirrors geometry on inverted TP/SL); rate is what AI emits, not what executes.
- **~17 trades/month across all instruments.** Pre-Apr-2026; April observed lower due to decay + fleet expansion timing.
- **~$60/month API cost.** Now ~$12/mo canary alone with cache. Total fleet API depends on CANDIDATE rate × fixture coverage; trends with fleet expansion.

---

*Last updated: April 26, 2026. Created during CLAUDE.md prune (A.4) to keep the bootstrap doc < 30k chars.*
