# Variant C Partial Close — Replay Decision (2026-04-18)

**Analyst:** Claude Code, GTOS session 26
**Data source:** `shadow_logs/partial_close_backtest.jsonl` (45 rows, commit `dd3480f`)
**Universe:** `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` (111) + `phase1_all_trades_merged.json` (18) = 129 unique XAUUSD batch trades
**Pre-registered gate:** n >= 30 AND Wilcoxon signed-rank p < 0.05 (per `CLAUDE.md` "Standard BE Shadow Logger" promotion criteria mirrored to Variant C in `src/components/partial_close_shadow_logger.py:16-19`)

---

## TL;DR

**VERDICT: DEFER.** Mean delta_r = +0.128 R across 45 triggered trades, but Wilcoxon two-sided p = 0.363 (one-sided "greater" p = 0.182) fails the pre-registered p < 0.05 gate. 95% CI on mean delta_r is [-0.070, +0.326] — crosses zero. Sample clears n >= 30 but signal is not significant. Headline positive expectancy is driven entirely by the 9 reversed-past-entry losers (where Variant C "saves" 33% @ +1R before the reversal); the 36 non-reversed trades (most of which are winners) LOSE -0.148 R each on average because the 67% runner collects a smaller share of the favourable extension than a full position would have. Recommend DEFER: keep the live shadow logger running, re-evaluate after >= 30 LIVE +1R trigger events (estimated ~6 months at current CR and WR post-challenge).

---

## Methodology

The offline replay (`scripts/variant_c_replay.py`) iterates the 129 unique batch trades, filters to those that touched +1R intra-trade (`mfe_r >= 1.0` OR `r_path` showed `r_at_high/close >= 1.0`), and computes the hypothetical Variant C blended R using:

```
variant_c_r = 0.33 * 1.0 + 0.67 * remaining_r
delta_r     = variant_c_r - actual_r_multiple
```

`remaining_r` is derived in two modes:
- **exact_r_path (n=9):** walks per-bar `r_at_low / r_at_close` after the +1R touch; if any bar shows `r <= 0`, `remaining_r = 0` (BE stop).
- **approx (n=36):** no `r_path` available. Assumes winners (`r_multiple > 0`) did not reverse past entry → `remaining_r = r_multiple`. Losers (`r_multiple <= 0`) reversed past entry → `remaining_r = 0`.

The approx heuristic is conservative on winners (if a winner briefly touched BE before continuing, the replay wrongly credits it the full `r_multiple` on the runner, overstating Variant C slightly — but the bulk of winners are monotone once at +1R, so the bias is small). It is correct on losers (if the trade ended at SL after touching +1R, it must have crossed entry).

The schema is byte-aligned with the live logger (`src/components/partial_close_shadow_logger.py`) so once live triggers accumulate, results merge cleanly.

**Important baseline caveat:** `actual_r_multiple` in the batch corpus reflects the CURRENT system's multi-TP + trailing-stop exit (exit substates: `CLOSED_SESSION_TIMEOUT`, `CLOSED_TP3_RUNNER`, `CLOSED_TRAIL`, `CLOSED_BE`, etc.), NOT a hypothetical "100% held to TP1" run. So the comparison is Variant C (33% @ 1R, 67% runner with BE) vs the *current exit ruleset*, which itself already scales and trails. The TP1 reference in the logger's "100%_at_TP1" label is a simplification.

---

## Results

### Headline stats (n=45)

| Metric | Value |
|---|---|
| Mean delta_r | **+0.1279 R** |
| Median delta_r | +0.0858 R |
| Stdev delta_r | 0.6577 |
| Cumulative delta_r | +5.7571 R over 45 trades |
| Min / Max delta_r | -0.9141 / +1.3300 |
| 95% CI on mean (t, df=44) | **[-0.0697, +0.3255]** (crosses zero) |
| 95% bootstrap CI on median (n=10k) | [-0.1089, +0.1551] (crosses zero) |
| Current expectancy / trade (actual) | +0.9782 R |
| Variant C expectancy / trade | +1.1062 R |
| Delta expectancy / trade | +0.1279 R |

### Wilcoxon signed-rank (the decision stat)

| Test | W | p |
|---|---|---|
| Two-sided | 437.00 | **0.3632** |
| One-sided "greater" | 598.00 | **0.1816** |
| One-sided "less" | 598.00 | 0.8184 |

No zero deltas in the sample; n_nonzero = 45. Neither test reaches p < 0.05.

### Win / tie / loss split of deltas

| Bucket | Count | % |
|---|---|---|
| delta_r > 0 (Variant C better) | 27 | 60.0% |
| delta_r == 0 (tie) | 0 | 0.0% |
| delta_r < 0 (Variant C worse) | 18 | 40.0% |

### Mechanism breakdown — the "why"

| Sub-group | n | Mean delta_r |
|---|---|---|
| Trades that reversed past entry (actual was loser) | 9 | **+1.2311 R** |
| Trades that did NOT reverse past entry (most winners) | 36 | **-0.1479 R** |

The +0.128 R headline is a mixture of (a) Variant C saving 9 full-SL losers (+1.23 R each by locking 33% @ +1R before the reversal) and (b) Variant C giving up some of the 36 non-reversing trades' upside (-0.148 R each, because a 33% partial collects 1R but the remaining 67% trail/timeout would have captured a higher R under the full-size exit). The "edge" is pure variance compression; the mean expectancy lift is marginal and not significant.

### Kill-zone breakdown (the only partition available — no symbol field)

| Kill zone | n | Mean delta_r | Wins / Losses |
|---|---|---|---|
| london | 19 | +0.0120 | 12 / 7 |
| ny | 26 | +0.2127 | 15 / 11 |

NY is where most of the positive signal sits, largely because NY has more of the reversed-past-entry losers in this sample (5 of 9 reversed-losers are NY).

### Direction

| Direction | n | Mean delta_r |
|---|---|---|
| LONG | 43 | +0.1485 |
| SHORT | 2 | -0.3151 |

Effectively LONG-only sample — SHORT n=2 is not interpretable.

### Mode (data quality split)

| Mode | n | Mean delta_r |
|---|---|---|
| exact_r_path | 9 | +0.1163 |
| approx | 36 | +0.1309 |

Exact and approx agree closely on mean — the approx heuristic is not introducing direction-dependent bias.

### Per-symbol breakdown

**Not available.** All 129 universe trades lack a `symbol` field — both `unified_trades_v2_20260331.json` and `phase1_all_trades_merged.json` predate multi-instrument expansion (Apr 2026) and are XAUUSD-only batch corpora. The 45 replayed trades are therefore 100% XAUUSD. A per-instrument decision requires live logger data or a re-run of the replay script against per-symbol backtest corpora (none exist in the tree with `mfe_r + r_multiple + r_path` fields populated for the other four instruments).

### Sanity checks passed

1. **Is n=45 distinct trades, not a parameter sweep?** YES. Script runs exactly at Variant C's actual parameters (`PARTIAL_CLOSE_FRACTION = 0.33`, `TRIGGER_R = 1.0`) with no sweep loop; each row has a unique `trade_id`; 45 unique trade_ids confirmed. There is also a `partial_close_backtest_exact_only.jsonl` (11 rows) which is a subset of the 45 (rows 37-45 exact + 2 others via a different run) — not a sweep, not additional evidence.
2. **Trigger rate check.** 46 of 129 trades have `mfe_r >= 1.0` (35.7%). 45 pass the script's `direction in (LONG, SHORT)` filter — one trade `bt_2025-06-23_london_001` has `direction="unknown"` and is legitimately dropped. The 45/129 = 34.9% trigger rate is internally consistent with XAUUSD's 62% WR and typical MFE distribution. Not off.
3. **Dedup.** The script tracks `seen_ids` across both input files. 111 + 18 = 129 with zero overlap (all phase1_merged trade_ids are unique vs unified_trades_v2).
4. **Mode ratio.** 9/45 (20%) have full `r_path`; 36/45 (80%) fall back to the approx heuristic. The approx assumption that winners are monotone-after-+1R is the main quality risk; it overestimates Variant C's runner leg when a winner briefly dipped through entry before continuing. In exact_r_path trades where we can check, 0 of 4 winners reversed past entry, which supports the heuristic — but n=4 is not a strong test.

---

## Gaps between backtest and live

This is in-sample replay on historical XAUUSD data, not a live RCT. Known mismatches:

1. **No spread / partial-close slippage modelled.** The live Variant C would pay a spread on the partial at +1R and any BE-stop slippage on the runner. At MT5 broker spreads and XAUUSD volatility, typical cost is ~0.05-0.15 R on the partial leg. Directly subtracts from the +0.128 R headline; could flip sign.
2. **No MT5 partial-close order mechanics tested.** Current execution engine (`src/components/execution.py`) doesn't have a partial-close code path wired. Adding one introduces new failure modes (order rejection, lot-size rounding, position-split reconciliation, and the known `_active_trade_record` / `pending_intent` gaps flagged in handoff 17).
3. **`r_path` resolution is per-bar (M15).** Real fills happen tick-by-tick. A bar where `r_at_low <= 0` in exact mode means the bar *touched* BE, not that price reversed permanently. The replay treats it as a BE stop → `remaining_r = 0`. This is the conservative direction (understates Variant C's runner on noisy wicks), which is good for not overselling the result, but means the "exact" mode is itself an approximation.
4. **Approx mode winner heuristic.** Assumes winners never reversed past entry after +1R. In reality some did briefly; approx overstates Variant C slightly on those rows. Magnitude likely small.
5. **Corpus is XAUUSD-only (2024-04 through 2026-03).** No US30 / USDJPY / GBPJPY / GBPUSD. The podcast hypothesis behind Variant C (Patrick / FTMO survival analysis) generalised across instruments; this replay does not test that.
6. **Regime homogeneity.** 2024-04 to 2026-03 spans the strong XAUUSD bull run ($2250 -> $5000+). Runner expectancy in a low-volatility or choppy regime would differ. Variance-compression value (the 9 reversed losers) would likely increase in chop; runner-capture value would decrease.
7. **Current baseline != 100% to TP1.** Per universe exit substates (`CLOSED_TP3_RUNNER`, `CLOSED_TRAIL`, `CLOSED_BE`, `CLOSED_SESSION_TIMEOUT`), the batch corpus was run with multi-TP + trailing stop, not a clean single-TP exit. So delta_r is Variant-C-vs-current, not Variant-C-vs-TP1-holder.
8. **Live CR post-T7 differs from batch CR.** T7 C-gate (Apr 12) changed the CANDIDATE rate and selectivity; the 45 batch rows were generated under the pre-T7 (Phase 2A v1 scored) or earlier prompt. Trigger rate and MFE distribution in live may diverge.
9. **Zero live samples to cross-check.** Per handoff 20, 0 filled live trades have touched +1R since `partial_close_shadow_logger` deployment (Apr 12). Cannot validate against live ground truth.

---

## Pre-registration note

The decision gate **n >= 30 + Wilcoxon signed-rank p < 0.05** is pre-registered. It appears:
- In `CLAUDE.md` (Podcast Research Implementation → Standard BE Shadow Logger): "after 30+ BE-triggered trades, if cumulative delta_r > 0 with p < 0.05 (Wilcoxon signed-rank), promote to live. If delta_r <= 0 after 30 trades, kill."
- Mirrored in `src/components/partial_close_shadow_logger.py:16-19` at deployment (Apr 12, commit `3b9f197`).
- Referenced in `scripts/variant_c_replay.py:22-26` and the handoff 20 language.

This analysis applies that gate as pre-specified. The observed p = 0.363 (two-sided) / 0.182 (one-sided greater) does NOT clear the gate. Reporting a one-sided p, switching to a different test (sign test, t-test, bootstrap on mean), or relaxing to p < 0.10 would be post-hoc and is not considered here.

Per the pre-registered criteria, the fact that `cumulative delta_r > 0` (5.76 R) satisfies the direction condition, but the significance test does not. The pre-registration contains two clauses — promote requires BOTH positive delta AND p < 0.05; kill requires `delta_r <= 0 after 30 trades`. The cumulative delta is not <= 0, so KILL is not triggered either. The pre-registration does not explicitly name a third "defer" clause, but the natural reading of "neither promote nor kill" IS defer.

---

## Recommendation

**DEFER.** Pre-registered promotion gate (Wilcoxon p < 0.05) fails at p = 0.363 despite n=45 clearing the sample threshold. Cumulative delta_r > 0 so KILL is not triggered. The backtest headline of +0.128 R / trade is plausible but:
- within a CI that crosses zero,
- entirely attributable to variance compression on the 9 reversed losers (not a true expectancy edge on the 36 non-reversing trades),
- sensitive to real-world frictions (spread, partial-close slippage) not modelled here, and
- derived from an in-sample XAUUSD-only corpus under an exit ruleset that already scales out via TP3 + trail.

None of the above is sufficient to ship a partial-close code path into the execution engine heading into the funded challenge window on 2026-04-21.

---

## If DEFER — next step (recommended)

1. **Keep the live shadow logger running.** It is observation-only, no trading impact. Zero cost.
2. **Target re-evaluation sample:** 30 LIVE +1R-triggered events. At current live CR / fill rate and ~35% MFE-reaches-1R rate observed in batch, that is ~1 trigger / week post-challenge → ~6 months to accumulate. Revisit no earlier than 2026-10.
3. **At re-evaluation:** merge live log (`shadow_logs/partial_close_shadow_log.jsonl`) with existing 45-row backtest under same schema; re-run Wilcoxon on the combined set. If live-only n hits 30 and shows significance independently, that is stronger evidence than combined (in-sample dilution).
4. **Consider a per-instrument retrigger.** If any one instrument accumulates 30 live triggers first (XAUUSD most likely), evaluate it standalone rather than a blended portfolio promotion.
5. **Do not re-run the replay against the same 129 trades** to "find" significance via alternate statistics — that is post-hoc and violates the pre-registration.

## If SHIP (NOT RECOMMENDED, for completeness)

Any SHIP verdict on this in-sample replay alone must carry the caveat that evidence is (a) XAUUSD-only, (b) in-sample, (c) does not model partial-close frictions, and (d) does not reach the pre-registered significance threshold. Live evidence bar for a SHIP re-evaluation: cumulative mean delta_r > 0 AND Wilcoxon p < 0.05 on >= 30 LIVE partial-trigger events.

Plumbing required if shipped later (not today):
- `config/agent_config.yaml`: add `partial_close.enabled: true`, `partial_close.fraction: 0.33`, `partial_close.trigger_r: 1.0`, `partial_close.move_sl_to_be: true`.
- `src/components/execution.py`: new partial-close code path (market order for 33% lot fraction at +1R touch, then MT5 SL modification to entry for remaining 67%). Also needs to fix the pre-existing `_active_trade_record` / `pending_intent` gaps flagged in handoff 17 so exit data is captured.
- New test: `tests/test_partial_close_live.py` covering the partial-close order flow, lot-size rounding, MT5 rejection handling, and position-split reconciliation.
- Restart sequence: commit → restart all 5 symbol processes.

## If KILL (NOT TRIGGERED HERE)

The pre-registered KILL condition (`delta_r <= 0 after 30 trades`) is not met — cumulative delta_r = +5.76 R > 0. KILL is therefore not recommended. If it were, the savings would be ~zero: the shadow logger is already zero-impact, no gating, no CPU cost beyond a JSONL append on every live trade that touches +1R (currently 0 / week).

---

## Appendix — Key artifacts

| Path | Purpose |
|---|---|
| `shadow_logs/partial_close_backtest.jsonl` | The 45 backtest rows analysed here |
| `shadow_logs/partial_close_backtest_exact_only.jsonl` | 11-row exact-mode subset (subset of the 45, not independent evidence) |
| `scripts/variant_c_replay.py` | The replay script (commit `dd3480f`) |
| `src/components/partial_close_shadow_logger.py` | Live logger (commit `3b9f197`, Apr 12) |
| `shadow_logs/partial_close_shadow_log.jsonl` | Live log — currently empty (0 live +1R triggers since Apr 12) |
| `knowledge_base_backtest/analysis/unified_trades_v2_20260331.json` | 111 XAUUSD batch trades |
| `knowledge_base_backtest/analysis/phase1_all_trades_merged.json` | 18 XAUUSD batch trades with `r_path` |
