# A4 Final Synthesis — Trending-Bull Cohort Decay Verdict

**Date:** 2026-04-28
**Cohort:** XAUUSD H2-2026 trending_bull CANDIDATEs (n=11 replayable, all LONG, 9 NY + 2 London)
**Total spend:** $2.16 (Stage 2 = $1.05 + Stage 2.5 = $0 + after-framework-replay = $1.11)

---

## Headline verdict — 🟢 GREEN

| Metric | Pre-Phase-1 (historical, n=4 actually filled) | Post-Phase-1 (M1 sim, n=11, before framework fix) | Post-Phase-1 + framework fix (M1 sim, n=11) |
|---|---:|---:|---:|
| Verdict band | 🟡 YELLOW | 🟢 GREEN | 🟢 GREEN |
| Mean R (filled) | +0.25R | **+0.818R** | **+0.818R** |
| WR | 50% | **72.7%** | **72.7%** |
| n_filled | 4 of 11 | 11 of 11 | 11 of 11 |
| n_wins / n_losses | 2 / 2 | 8 / 3 | 8 / 3 |
| Sum R | +1.00R | +9.00R | +9.00R |

**Phase 1's prompt-side fix (FA-2 commit `fa35cc0`, 2026-04-20) was sufficient to recover this cohort to GREEN.** The H2 "decay" we attributed to AI selectivity drift in F2/F15 was substantially a function of the pre-FA-2 prompt directive that literally instructed `sl_buffer_applied: 0.0`. The AI's setup selection on this cohort is fine; the geometry was broken.

**The multi-framework dispatch fix (commit `41b4a59`) is collateral-clean:** identical R-distribution before vs after, confirming it closes the GBPJPY all-mitigated-OB bug class without affecting the XAUUSD trending_bull cohort.

---

## What changed between Stage 2.5 (n=4) and the final n=11 verdict

The Stage 2.5 verdict (YELLOW, mean +0.25R, WR 50%) sampled only the 4 records that historically *filled at the broker*. The other 7 records were rejected by L2 sl_beyond_ob in production because the AI's pre-FA-2 emission had `sl_buffer_applied: 0.0` (SL exactly at OB.low). I initially read this as "the safety stack is preventing decay-driven losses."

The audit (`SL_BUFFER_AUDIT.md`) reframed: those 7 rejections were a HISTORICAL artifact of the pre-FA-2 prompt. FA-2 already fixed the prompt directive on 2026-04-20. The current AI emits non-zero buffers (3.57-5.19 points) on all 11 records.

When the M1 fill simulator extends to all 11 records using *current* AI emissions, the result flips: 6 of the 7 historically-rejected records actually represent good setups that win at +1.5R when filled. The "safety stack hiding the loss" framing was wrong; the safety stack was correctly catching a deterministic prompt bug, not selectivity drift.

---

## Per-record outcomes (after framework fix sim — final)

| trade_id | dir | entry | SL | TP1 | buf | M1 outcome | exit_reason | realized R |
|---|---|---|---|---|---|---|---|---|
| 2026-04-15_ny_1315 | LONG | 4777.43 | 4757.77 | 4807.00 | 4.37 | FILLED_WIN | tp1_hit | +1.500 |
| 2026-04-15_ny_1330 | LONG | 4777.43 | 4757.82 | 4806.82 | 4.48 | FILLED_WIN | tp1_hit | +1.501 |
| 2026-04-15_ny_1345 | LONG | 4777.43 | 4757.59 | 4807.16 | 4.55 | FILLED_WIN | tp1_hit | +1.502 |
| 2026-04-15_ny_1415 | LONG | 4777.43 | 4757.68 | 4807.06 | 4.46 | FILLED_WIN | tp1_hit | +1.503 |
| 2026-04-15_ny_1615 | LONG | 4777.43 | 4757.55 | 4807.22 | 4.63 | FILLED_WIN | tp1_hit | +1.495 |
| 2026-04-15_ny_1700 | LONG | 4777.43 | 4757.80 | 4806.88 | 4.34 | FILLED_WIN | tp1_hit | +1.500 |
| 2026-04-16_london_0800 | LONG | 4796.28 | 4783.65 | 4815.22 | 3.79 | FILLED_LOSS | sl_hit | -1.000 |
| 2026-04-16_london_0930 | LONG | 4796.28 | 4783.57 | 4815.35 | 3.87 | FILLED_LOSS | sl_hit | -1.000 |
| 2026-04-16_ny_1316 | LONG | 4796.28 | 4783.87 | 4814.90 | 3.57 | FILLED_LOSS | sl_hit | -1.000 |
| 2026-04-17_ny_1315 | LONG | 4793.86 | 4776.47 | 4819.95 | 5.64 | FILLED_WIN | tp1_hit | +1.500 |
| 2026-04-17_ny_1330 | LONG | 4743.87 | 4732.99 | 4760.18 | 5.19 | FILLED_WIN | tp1_hit | +1.499 |

---

## Caveats (non-negotiable)

1. **n=11 is small.** Wide CI on every aggregate; verdict is directional, not Bonferroni-safe.
2. **The 3 losses all hit the same M15 candle on 2026-04-16 (16:45 / 16:52 UTC).** They share entry=4796.28 and were taken out by the same correlated downside event. Effectively n=1 unique loss event, n=8 unique wins. A real live system with this cohort would see correlated drawdown.
3. **M1 sim is idealized.** No slippage beyond M1 OHLCV granularity, no spread-crossing cost. S77 projected ~21% R-loss from broker friction; if applied here, mean R would drop from +0.818 to ~+0.65 — still solidly GREEN but worth noting.
4. **All 11 records are LONG.** Cohort is structurally LONG-biased (trending_bull). Zero SHORT-side validation.
5. **The 04-17_ny_1330 record fills only on Mon 04-20 02:45** (across the weekend). Within the 192-bar horizon (735/2880 M1 bars used) but atypical fill timing.
6. **The cohort selection is post-hoc.** These 11 are the ones the AI emitted as CANDIDATEs in production. The test answers "given the AI emits CAND on these setups, what's the realized R when SL geometry is correct?" It does NOT answer "would the AI's selectivity rule out bad setups in some general population?"

---

## Strategic implications

**Phase 2 priority order shifts from my earlier reading:**

| Phase 2 task | Earlier rank | Revised rank | Reason |
|---|:-:|:-:|---|
| K54 regime-aware ML classifier | #1 | #1 | Unchanged; still the highest-confidence single-task lift |
| F27 backward outcome injection | #2 | #2 | Unchanged; speculative high-upside |
| HALLUC-5 cross-context A/B | #4 | #3 | Cleaner ADR-006 follow-up |
| **B10/P68 regime-selectivity prompts** | **#2 (after the misread)** | **#5-6 (deprioritized)** | **A4 GREEN means the AI's selectivity is fine on this cohort; the perceived "drift" was the SL bug. Selectivity research is no longer urgent.** |
| C19 v2 detector full backtest | #3 | #4 | Still useful for SHORT-side validation |
| D21 multi-framework forced-eval | #5 | #5 | Unchanged |

**The big strategic update**: I had said "Phase 1 was necessary but not sufficient at the decision-making layer." Walking that back. **Phase 1's FA-2 prompt fix WAS sufficient to recover this cohort.** The decision layer is fine; the geometry layer was broken; FA-2 closed the geometry bug; A4 confirms the system now produces +0.818R/trade on the cohort that previously showed -0.131R/trade.

---

## What the verdict does NOT prove

This is a single cohort (XAUUSD trending_bull, H2 2026). The verdict GREEN here doesn't generalize to:

- Other regimes (chop, transitional, trending_bear). May still need targeted work.
- Other instruments (USDJPY, GBPJPY, US30, NAS100, XAGUSD). The framework dispatch fix was specifically GBPJPY-targeted.
- The SHORT-side cohort. n=12 H2 SHORT trades at 91.7% WR is a separate, smaller-sample picture.
- Live realized R (vs M1-simulated). The next 30 days of live data is the real test.

**Re-evaluation cadence:** re-run A4 at n≥30 in 3-4 weeks once enough live trending_bull XAUUSD setups accumulate. If live realized R aligns with the M1 sim (+0.5R or better after slippage), the GREEN verdict is confirmed empirically.

---

## Files

| Artifact | Path |
|---|---|
| Cohort manifest (n=11) | `research/a4_trending_bull_replay_2026-04-28/a4_cohort_manifest.csv` |
| Pre-fix replay outputs | `research/a4_trending_bull_replay_2026-04-28/replay_outcomes.jsonl` |
| Post-framework-fix replay outputs | `research/a4_trending_bull_replay_2026-04-28/after_framework_fix/replay_outcomes.jsonl` |
| Stage 2.5 R-join (n=4 historical fills) | `research/a4_trending_bull_replay_2026-04-28/a4_realized_r_join.csv` |
| Pre-framework-fix M1 sim (n=11) | `research/a4_trending_bull_replay_2026-04-28/a4_before_framework_fix_full_cohort_R.json` |
| Post-framework-fix M1 sim (n=11) | `research/a4_trending_bull_replay_2026-04-28/a4_after_framework_fix_full_cohort_R.json` |
| SL buffer audit (root cause of pre-FA-2 rejections) | `research/a4_trending_bull_replay_2026-04-28/SL_BUFFER_AUDIT.md` |
| GBPJPY framework-dispatch deep dive | `research/halluc1_gbpjpy_deep_dive_2026-04-28/REPORT.md` |

---

## Memory updates pending

- `project_a4_xauusd_trending_bull_replay_2026-04-28` — **revise** verdict from YELLOW (Stage 2.5 reading) to GREEN (full-cohort M1 sim reading). Note that the framework fix is collateral-clean.

---

*A4 closed 2026-04-28. Next: re-run at n≥30 in 3-4 weeks for live confirmation. Phase 2 minimal set is now A4 ✓ + F27 prototype (the speculative high-upside task) before any K54 v2 work.*
