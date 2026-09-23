# LIRA A/B Deep Forensic — Agent R (Red Team) Report

**Branch:** `research/lira-red-team` (artifacts only; not merged)
**Generated:** 2026-04-25
**Mode:** Independent verification of contested claims from agents α/β/γ/δ. No charity toward prior agents.
**Method:** Re-derive every contested claim from raw `all_results.json` files on `main`.

---

## 1. Executive Summary

Of the 6 contested claims, β is substantively right on **C1 (analyze.py MaxDD bug)** and **C2 (USDJPY coverage artifact)** — both confirm with exact numerical match. β's framing on **C3 (SL magnitude)** is correct in spirit (magnitude is tiny) but β's specific Wilcoxon p=0.0068 does not replicate; my Wilcoxon p=0.0698 is suggestive not significant. α's headline **C4 (XAUUSD-LIRA edge)** point estimate (+0.114R/trade) is exactly correct, but I confirm the bootstrap diff CI [-0.877, +1.104] crosses zero — α already flagged this as "not statistically significant" but the framing in §10 still treats it as actionable; it is not. **C5 (stale-OB anchoring)** is the most overstated claim: under coverage-matching, LIRA and A2 V3 pick the SAME OBs at NEARLY-IDENTICAL rates (LIRA 56 vs A2 52 rows at entry≈154.88 in coverage-matched usdjpy_s2 — ratio 1.08:1, not the dramatic divergence implied). **C6 (γ + δ)** both replicate cleanly.

**Bottom line for the LIRA-STAY verdict:** the verdict survives all corrections (Exp R gate fails independently of MaxDD bug). But the *narrative mechanism* — "LIRA is over-permissive on USDJPY because of stale-OB anchoring + tighter SLs" — is substantially weaker than alpha portrays.

---

## 2. Per-Claim Verdict Table

| Claim | Stated by | Red Team verdict | Confidence |
|---|---|---|---|
| **C1** — analyze.py MaxDD chronological bug | β | **CONFIRMED, β exact** (LIRA chrono 6.0R vs alpha 9.0R; A2 chrono 5.0R vs alpha 3.0R; pre-reg gate flips PASS) | HIGH |
| **C2** — USDJPY +14 LONGs is coverage artifact | β | **CONFIRMED, β essentially exact** (coverage-matched delta = +1, not +14; my numbers: LIRA 25 vs A2 24 in coverage; β reported 20 vs 19) | HIGH |
| **C3** — SL-tightness magnitude 50× inflated | β | **PARTIAL CONFIRM** — magnitude indeed tiny (mean abs 0.072pp, median signed 0.000pp), but β's "Wilcoxon p=0.0068" does NOT replicate; my p=0.0698 (one-sided 0.0349). Direction of effect (LIRA tighter on XAUUSD) holds: 8/11 XAUUSD pairs LIRA-tighter; USDJPY 6/17 LIRA-tighter (essentially tied). | MEDIUM |
| **C4** — α: LIRA wins XAUUSD +0.114R/trade | α | **POINT ESTIMATE EXACT, NOT STATISTICALLY SIGNIFICANT** — bootstrap diff 95% CI [-0.877, +1.104] crosses zero by a wide margin. α's report does flag this caveat; but the §10 "Hybrid LIRA-XAU + V3-FX" recommendation is not data-supported at n=14 vs 11. | HIGH on point, HIGH on null-stat |
| **C5** — α/β: LIRA stale-OB anchoring on USDJPY | α + β | **OVERSTATED / PARTIALLY MISLEADING** — α's "65 candles in usdjpy_s2 with entry=154.88" is a TOTAL row count; coverage-matched LIRA picks 154.88 on 56 rows vs A2's 52 — both prompts behave nearly identically. CANDIDATE counts are 6 vs 6 in s2. The "LIRA-specific OB selection error" framing is not supported. | HIGH |
| **C6a** — γ: LIRA self-consistent 100% | γ | **CONFIRMED** (4/4 candles, 5/5 unanimous) | HIGH |
| **C6b** — δ: confidence_tier doesn't discriminate | δ | **CONFIRMED** (high vs moderate two-prop z p=0.7872; tier ordering directional, not significant) | HIGH |

---

## 3. Shared Hallucinations / Inflations

The following claims appear in both α and β reports and are **misleading** when verified against raw data:

### 3a. "LIRA picks deeper-but-stale OBs while V3 picks proximate OBs" (C5 mechanism)

Both reports describe LIRA emitting `entry=154.88` at high frequency on usdjpy_s2 as evidence of stale-OB anchoring vs V3. **This is mostly an artifact of LIRA evaluating more candles** (608 vs 290 rows in s2). Within A2's coverage window (142 evaluations both):

- LIRA picks entry=154.88 (the alleged "stale OB") on **56 rows**
- A2 V3 picks entry=154.88 on **52 rows**
- Both prompts arrive at 6 CANDIDATEs with the same OB-selection patterns

The decision-class breakdown in coverage-matched s2:
- LIRA: 76 REJECTED_L2, 38 BLOCKED_LIMIT, 22 NO_TRADE, 6 CANDIDATE
- A2: 78 REJECTED_L2, 42 BLOCKED_LIMIT, 16 NO_TRADE, 6 CANDIDATE

**The prompts behave identically on usdjpy_s2 within coverage.** α's "LIRA hallucinates 154.88 entries while V3 picks proximate" framing rests on comparing 65 LIRA rows (out of 608) against fewer A2 rows because A2 stopped evaluating earlier. When normalized by row count, both are at ~10% of evaluations — the same.

The 1 actually-suspicious LIRA-only divergence (the `usdjpy_s3 2026-02-26T00:15` case where LIRA picked entry=155.80 vs A2 entry=155.19) IS a real OB-selection difference, but represents 1 candle, not 65.

### 3b. "Tighter SL is LIRA's mechanism for losses" (C3)

β is right that the diagnostic's "0.2-0.4% tighter" headline came from cherry-picking the >0.5pp subset. The full 28-pair median signed delta is 0.000pp. The XAUUSD-only pattern is real (mean -0.10pp), but the only **same-entry SL-attributable win-flip** in 28 pairs is `xauusd_s3 2026-01-30T08:00 LONG` (one case, -2.5R cost). The other "win-flips" α/β cite involve **different entry points** (different OB picks), so they're confounded by entry selection, not pure SL-tightness effects.

### 3c. Methodological discrepancy in SL-pair counts

The three reports give different "LIRA tighter" counts on the same 28 pairs:
- α: 16/28 tighter, 12 wider, 0 ties (uses `lira_sl_dist < a2_sl_dist` both measured from LIRA's entry)
- β: 15/28 tighter, 13 wider/tied (uses LONG: `sl_lira > sl_a2` direct comparison)
- Red Team: 14/9/5 (each variant's SL relative to its own entry, fraction-based)

All three are valid metrics of slightly different concepts. None is "wrong" but α's metric is the most-cited and uses LIRA's entry as reference, which obscures the entry-selection vs SL-placement decomposition. β's directional metric and red-team's fraction-of-own-entry both pull the count down by 1-2.

---

## 4. Load-Bearing Claims that HOLD (high confidence consolidated set)

1. **LIRA-STAY verdict is correct.** Even after fixing the MaxDD bug (chrono 6.0R PASS), the Exp R gate (≥+0.40R) fails (LIRA Exp R = +0.094R). β-corrected stay-trigger `lira_fleet_exp_le_a2_baseline` (+0.094 ≤ +0.333) fires.

2. **LIRA fleet does materially underperform A2 V3 on coverage-matched setups.** Per-trade ExpR on overlapping 28 pairs: LIRA -0.5R sum vs A2 +2.0R sum (β's beta_analysis). The LIRA edge on XAUUSD is too small (n=14) to offset the USDJPY deficit (n=34, -0.418R/trade).

3. **γ confirms LIRA is internally deterministic** at Sonnet 4.6/effort=max/temp=0. The LIRA-vs-V3 gap is prompt-attributable, not LLM noise.

4. **δ confirms confidence_tier is statistically indistinguishable from random labeling** at fleet n=48. Two-prop z high vs moderate p=0.7872. Monotonic ordering exists in expectancy (+0.154 → +0.053 → -0.167) but is not significant.

5. **0 opposite-direction trades** when both prompts produce CAND on the same candle. The label-first vs reasoning-first architecture choice does not affect direction selection.

6. **Parse error rate 0.0%** for LIRA. The schema_adapter (`research/v4_prompt_engineering/dp4_lira/schema_adapter.py`) is working as intended.

7. **LIRA ~13% cheaper API per CAND** ($0.027 vs $0.046) but generates ~46% cheaper $/fill ($0.68 vs $1.25). However, fleet ExpR penalty makes the savings irrelevant (R-economics dominate).

---

## 5. Findings That Need More Work

1. **Wilcoxon p discrepancy.** β reports p=0.0068 on signed-rank for SL deltas; I get p=0.0698. Likely due to different normalization (β might use raw-price-unit deltas rather than fraction-of-entry). Direction of effect (LIRA tighter on average for XAUUSD specifically) holds across all 3 metrics. Recommend re-running with multiple normalizations to establish robust significance.

2. **C5 nuance — is the 1 real OB-pick divergence (`usdjpy_s3 02-26T00:15`) a pattern or a singleton?** Need to inspect the full 28 same-(slice, candle, direction) overlap pairs and identify cases where entry_price differs by >0.05 USDJPY. The "stale-OB" framing may apply to a small subset (estimate ≤5 pairs of 28), but neither α nor β quantified this.

3. **C4 XAUUSD edge — what would n=30 require?** α suggests "≥30 XAUUSD fills before tier-conditional gating decisions can be statistically defended." At current rates, this is 6-8 weeks of dual-prompt running. Without it, the +0.114R/trade XAUUSD edge cannot be acted upon. This is a research-priority question, not actionable on Monday.

---

## 6. Corrected / Consolidated LIRA Verdict

**LIRA-STAY is correct, but the published mechanism story is misleading and should be retracted/restated.**

The actual story is:

> LIRA's prompt produces marginally MORE setups within coverage-matched conditions (+1 USDJPY LONG, not +14 — the +14 is a coverage artifact). LIRA's SL placement is essentially tied with A2 on USDJPY (6/17 LIRA-tighter) but slightly tighter on XAUUSD (8/11). Both prompts pick the SAME OBs at nearly-identical rates within coverage; the "stale-OB anchoring" claim was inflated by raw row counts that didn't normalize for evaluation depth. The fleet expectancy gap (+0.094R LIRA vs +0.333R A2) comes mostly from **LIRA marginally underperforming A2 on coverage-matched USDJPY LONG setups (-0.23R/trade)**, especially in London KZ. The LIRA-STAY verdict survives all bug fixes (Exp R gate fails independently of the MaxDD ordering bug).

The "LIRA architecture is fundamentally broken on USDJPY" framing should be replaced with: "LIRA architecture is **slightly worse** on coverage-matched USDJPY setups, mechanism unidentified, and not worth shipping at this sample size." The +0.114R/trade XAUUSD point estimate is intriguing but bootstrap-diff CI crosses zero — not actionable until n≥30.

---

## 7. Patch Suggestion: analyze.py MaxDD Bug

β is correct that the MaxDD bug is real. The issue is in `research/lira_ab_backtest/analyze.py` lines 109-186 (`load_slices` + `aggregate`):

```python
# CURRENT (BROKEN):
def aggregate(slices: dict) -> dict:
    out = {...}
    for slice_name, s in slices.items():
        ...
        out["fleet"]["filled_cands"].extend(filled)  # Extends in iteration order
```

`slices` comes from `load_slices()` which iterates `sorted(os.listdir(slice_dir))` (line 111) → alphabetical order: `usdjpy_s1, usdjpy_s2, usdjpy_s3, usdjpy_s4, xauusd_s1, ..., xauusd_s8`. The fleet `filled_cands` list is then built in this order, and `slice_stats(...)` calls `max_drawdown_from_peak(r_series)` (line 226) on this list — producing an artificial drawdown from the USDJPY-then-XAUUSD ordering that does NOT reflect real-time equity.

### Suggested patch (drop-in to `slice_stats`):

```python
def slice_stats(cands: list, filled: list) -> dict:
    if not cands:
        return {...}
    ...
    # SORT FILLED BY CANDLE_TIME for chronological MaxDD
    filled_chrono = sorted(filled, key=lambda r: r.get("candle_time", ""))
    long_cands = [r for r in cands if r.get("direction") == "LONG"]
    short_cands = [r for r in cands if r.get("direction") == "SHORT"]
    long_filled = [r for r in filled_chrono if r.get("direction") == "LONG"]
    short_filled = [r for r in filled_chrono if r.get("direction") == "SHORT"]
    ...
    r_series = [r.get("r_multiple", 0.0) for r in filled_chrono]  # chronological
    return {
        ...
        "maxdd": max_drawdown_from_peak(r_series),
        ...
    }
```

`candle_time` is ISO 8601 (lexicographic sort = chronological sort) so `sorted(..., key=lambda r: r.get("candle_time", ""))` works without parsing.

### Re-run after patch:

```bash
python research/lira_ab_backtest/analyze.py \
    --slice-dir research/lira_ab_backtest/slices \
    --out-md research/lira_ab_backtest/ANALYSIS.md \
    --out-json research/lira_ab_backtest/analysis_output.json
```

Expected re-run output: `lira_fleet_maxdd_le_8R: True` (passes); LIRA verdict still LIRA-STAY (driven by Exp R failure).

The same patch fixes A2's MaxDD (3R alphabetical → 5R chronological).

### Documentation hygiene
- Update `SYNTHESIS.md` lines 29 / 48 to reflect MaxDD 6.0R / 5.0R (not 9.0R / 3.0R).
- Update `SYNTHESIS.md` line 79 to note +14 USDJPY LONG delta is partly coverage gap; coverage-matched is +1.
- Update `SL_GEOMETRY_DIAGNOSTIC.md` to report median signed delta on full 28 (~0pp), with the >0.5pp subset as a sub-table.

---

## 8. Files

- `red_team_verify.py` — independent verification script (reads raw all_results.json files; recomputes C1-C6 from scratch)
- `verify_output.log` — full stdout trace
- `verdict_summary.json` — machine-readable C1-C6 verdicts
- `sl_pair_details.json` — all 28 same-(slice, candle, dir) pairs with my SL-distance metrics

## 9. Reproduction

```bash
cd C:/Users/MSI/Documents/ai-trading-agent/.claude/worktrees/agent-redteam-1777079025
python research/lira_ab_deep_forensic/red_team/red_team_verify.py
```

## 10. Confidence Calibration

- C1 (MaxDD bug): HIGH — verified bit-exact against alphabetical+chronological reorderings
- C2 (coverage artifact): HIGH — slice-by-slice evaluation counts confirm β's framing
- C3 (SL magnitude): MEDIUM-HIGH on direction; MEDIUM on β's specific p-value (does not replicate)
- C4 (XAUUSD edge): HIGH on point estimate exactness; HIGH on null-significance at this n
- C5 (stale-OB anchoring): HIGH that the "65 candles in s2" framing is misleading; MEDIUM on the existence of any LIRA-specific OB-selection drift (unverified beyond 1-3 candles)
- C6 (γ + δ): HIGH — both verifiable in <5 minutes from raw data

---

*End of Red Team Report.*
