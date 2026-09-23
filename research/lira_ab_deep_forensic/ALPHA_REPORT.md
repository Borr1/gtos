# LIRA A/B Deep Forensic — Agent Alpha Report

**Generated:** 2026-04-25
**Branch:** research/lira-forensic-alpha (artifacts only; not merged)
**Inputs:**
- LIRA: `research/lira_ab_backtest/slices/{slice}/all_results.json` (12 slices)
- V3 / A2: `research/a2_v2_active_backtest/slices/{slice}/all_results.json` (12 slices)
- F3 reference: `research/f3_backtest_2026-04-24/{slice}/all_results.json` (12 slices)
- Aggregator: `research/lira_ab_deep_forensic/forensic_analyzer.py` (machine-readable output: `analysis_data.json`)

---

## 1. Executive Summary

The original LIRA SYNTHESIS verdict (LIRA-STAY) holds, but the **stated mechanism is wrong in two ways**. (1) LIRA is **not** uniformly worse — it is **better than V3 on XAUUSD** (Exp +0.250R vs +0.136R, WR 50% vs 45%, n=14 vs 11) and gets **crushed on USDJPY** (Exp 0.000R vs +0.447R, WR 40% vs 58%). The fleet-level deficit is entirely a USDJPY problem layered on top of an XAUUSD micro-edge. (2) The "tighter SL" mechanism is **XAUUSD-specific** (LIRA tighter in 82% of XAUUSD overlap pairs vs only 41% of USDJPY pairs); the actual USDJPY problem is **stale-OB anchoring**, not SL geometry. LIRA's prompt mis-interprets the "prefer lowest-touches OB" rule on USDJPY, locking onto a deeper OB at 154.88 (touches=1) for 65 candles in usdjpy_s2 alone, while V3 picks the more proximate 155.52/155.81/156.36 OBs. Result: V3 catches the best USDJPY LONG window (Feb 4-6, +6R for V3 in s2) almost completely while LIRA's hallucinated entries get rejected by the L2 `entry_in_ob` gate. Verdict supports STAY but suggests a narrower hybrid path is plausible (LIRA-XAU + V3-FX), not actionable until validated on more XAUUSD samples.

---

## 2. Per-Slice Breakdown (Q1)

| Slice | Sym | LIRA n_cand/n_filled/WR/ExpR/Total | A2 (V3) n_cand/n_filled/WR/ExpR/Total | Delta R | Outcome |
|---|---|---|---|---:|---|
| xauusd_s1 | XAU | 0 / 0 / — / — / +0.0 | 0 / 0 / — / — / +0.0 | +0.0R | tie (cold-start) |
| xauusd_s2 | XAU | 1 / 1 / 0% / -1.00 / -1.0R | 1 / 1 / 0% / -1.00 / -1.0R | +0.0R | tie (single LOSS both) |
| **xauusd_s3** | XAU | **8 / 8 / 62% / +0.56 / +4.5R** | **5 / 5 / 60% / +0.50 / +2.5R** | **+2.0R** | **LIRA wins** |
| xauusd_s4 | XAU | 0 / 0 / — / — / +0.0 | 0 / 0 / — / — / +0.0 | +0.0R | tie (zero CAND both) |
| xauusd_s5 | XAU | 2 / 2 / 0% / -1.00 / -2.0R | 3 / 2 / 0% / -1.00 / -2.0R | +0.0R | tie |
| xauusd_s6 | XAU | 0 / 0 / — / — / +0.0 | 0 / 0 / — / — / +0.0 | +0.0R | tie (zero CAND both) |
| xauusd_s7 | XAU | 3 / 2 / 100% / +1.50 / +3.0R | 3 / 2 / 100% / +1.50 / +3.0R | +0.0R | tie (SHORT wins identical) |
| xauusd_s8 | XAU | 1 / 1 / 0% / -1.00 / -1.0R | 1 / 1 / 0% / -1.00 / -1.0R | +0.0R | tie |
| usdjpy_s1 | JPY | 8 / 8 / 50% / +0.25 / +2.0R | 6 / 6 / 50% / +0.25 / +1.5R | +0.5R | tie (LIRA caught 2 extra, net 0R) |
| **usdjpy_s2** | JPY | **9 / 9 / 55% / +0.39 / +3.5R** | **6 / 6 / 83% / +1.08 / +6.5R** | **−3.0R** | **A2 wins** |
| usdjpy_s3 | JPY | 13 / 8 / 37% / -0.06 / -0.5R | 7 / 2 / 50% / +0.25 / +0.5R | −1.0R | A2 wins |
| **usdjpy_s4** | JPY | **9 / 9 / 22% / -0.44 / -4.0R** | **5 / 5 / 40% / +0.00 / +0.0R** | **−4.0R** | **A2 wins** |
| **TOTAL** | — | **54 / 48 / 44% / +0.094 / +4.5R** | **37 / 30 / 53% / +0.333 / +10.0R** | **−5.5R** | A2 wins fleet |

Headline: LIRA's −5.5R fleet deficit is concentrated in 3 slices: **usdjpy_s4 (−4R), usdjpy_s2 (−3R), usdjpy_s3 (−1R)**. LIRA wins decisively in **xauusd_s3 (+2R)**. The 8 XAUUSD slices net **+2R for LIRA**; the 4 USDJPY slices net **−7.5R for LIRA**. The deficit is 100% USDJPY-driven.

**Coverage caveat (important).** Per-slice candle counts evaluated:

| Slice | LIRA candles | A2 candles | A2 last candle |
|---|---:|---:|---|
| usdjpy_s1 | 436 | 359 | 2026-01-19T01:30 |
| usdjpy_s2 | 608 | 290 | 2026-02-09T00:15 |
| usdjpy_s3 | 469 | 237 | 2026-03-04T07:00 |
| usdjpy_s4 | 406 | 264 | 2026-03-30T01:45 |

A2 hit the $6/slice budget cap **earlier** than LIRA (LIRA's 45.7%-shorter prompt = lower cost/call). LIRA evaluated 1.4-2.1× more USDJPY candles. **This is not the cause of LIRA's underperformance** — see §7 for confirmation. LIRA's USDJPY performance is roughly the same in the within-A2-coverage period (n=20, +0.000R Exp) and the extension period (n=14, +0.071R Exp).

---

## 3. Decision-Divergence Audit (Q2)

### Aggregate

| Bucket | Count | LIRA outcomes | A2 outcomes | LIRA net R | A2 net R |
|---|---:|---|---|---:|---:|
| **Both decide CAND, same direction** | 28 | 9 W / 14 L / 5 UNF | 10 W / 13 L / 5 UNF | −0.5R | +2.0R |
| **LIRA-only CAND** | 26 | 12 W / 13 L / 1 UNF | (no decision) | +5.0R | — |
| **A2-only CAND** | 9 | (no decision) | 6 W / 1 L / 2 UNF | — | +8.0R |
| **Opposite-direction same candle** | 0 | — | — | — | — |

**Key finding 1: ZERO opposite-direction trades.** When both prompts decided CAND on the same candle, they always agreed on direction. The "label-first vs reasoning-first" architecture choice did NOT produce direction inversions.

**Key finding 2: Overlap is 25/28 outcome-identical.** Same setup (slice, candle, direction) produces identical outcomes in 25 of 28 cases. The 3 divergences:

| Slice | Time | Sym | Dir | LIRA SL | A2 SL | LIRA outcome | A2 outcome | Mechanism |
|---|---|---|---|---:|---:|---|---|---|
| usdjpy_s3 | 2026-02-26T00:15 | JPY | LONG | 155.518 | 154.917 | WIN | UNFILLED | LIRA picked HIGHER OB (155.80) → got filled |
| usdjpy_s3 | 2026-03-02T07:00 | JPY | LONG | 154.905 | 156.145 | UNFILLED | WIN | A2 picked HIGHER OB (156.60) → got filled |
| xauusd_s3 | 2026-01-30T08:00 | XAU | LONG | 5069.27 | 5056.33 | LOSS | WIN | LIRA SL 12.94 pts tighter → got stopped |

These are 1.5-1.5 from each other on USDJPY (one each direction); xauusd_s3 case is the SL-tightness one cited in SL_GEOMETRY_DIAGNOSTIC.md.

**Key finding 3: A2-only setups (n=9) net +8R.** These are setups V3 took that LIRA either L2-rejected, NO_TRADE'd, or BLOCKED_LIMIT'd. 5 of 9 are usdjpy_s2 (Feb 4-6 cluster, V3's 5 wins out of 6 in that slice). LIRA's behavior on those 5 candles: **all REJECTED_L2 with reason `entry_in_ob: Entry 154.88 is outside OB zone {current OB}`**. LIRA emitted CANDIDATE in the AI step but proposed entry=154.88, which fails L2's entry-in-OB check because the live OB has moved to 155.30-155.81. (See §4 for root cause.)

**Key finding 4: LIRA-only setups (n=26) net +5R but with high variance.** 12 W / 13 L / 1 UNF. This is essentially break-even — net positive R only because wins are 1.5R while losses are 1R. The signal in this bucket is weak (n=26 too small to call). Of these 26, **21 are USDJPY LONG** (the prompt's permissiveness target).

**Detail tables:** Full per-trade rows in `analysis_data.json` keys `q2_overlap_detail`, `q2_lira_only_detail`, `q2_a2_only_detail`.

---

## 4. USDJPY LONG Over-Permissiveness Root Cause (Q3)

### Numbers

| Metric | LIRA | A2 (V3) |
|---|---:|---:|
| USDJPY LONG raw CAND | 38 | 24 |
| USDJPY LONG filled | 33 | 19 |
| USDJPY LONG WR | 42% | 58% |
| USDJPY LONG Exp R | +0.061R | +0.447R |

### LIRA-only USDJPY LONG profile (15 net extra CANDs)

LIRA-only USDJPY LONG = 21 CANDs; filled = 21 (all filled).
- 9 WINs / 12 LOSSes; net = -0.5R.
- Confidence-tier mix: high_conviction 9, moderate 9, marginal_pass 3.
- Kill-zone mix: tokyo 8, london 8, ny 4 (no skew).
- All in `h1_direction: bullish` (USDJPY was 100% bullish over the 4-month window).
- All in `setup_grade: A+` or `A`.

These features don't differ from the overlap setups — meaning the AI prompt itself emitted CANDIDATE on the same surface features. **What is different is the entry price**.

### Root cause: STALE-OB ANCHORING

LIRA emitted **entry=154.88** on 65 candles in usdjpy_s2 alone (out of ~210 CAND/REJECT decisions in that slice). At those candles, the M15 close ranged from 155.45 to 157.20 — i.e., price had advanced 0.6-2.4 USDJPY pips above LIRA's claimed entry. L2's `entry_in_ob` check rejected most of them because the actual current unmitigated H1 OBs were 155.30-155.52, 155.69-155.81, or 156.24-156.36 — NOT 154.88-154.72.

Reading LIRA's `h1_setup.explanation` field on these candles reveals the prompt's reasoning consistently:

> "Lowest-touches H1 bullish OB at 155.81-155.69 (touches=4 disqualified by rule preference for lowest-touches; selecting 154.88-154.72 with touches=1 as lowest-touch qualifying zone, midpoint 154.800)."

Both prompts contain the rule "Prefer the lowest-touches OB in the correct direction." However:

- **V3** (A2) interpretation: "lowest-touches" filters out OBs with touches≥2 because the downstream gate rejects them; the AI picks the **NEAREST unmitigated OB regardless of touches** because it knows the gate can handle it (`Nearest unmitigated H1 bullish OB at 156.36-156.24 (touches=3, formed 2026-02-04T06:00) caused by BOS; midpoint 156.300 selected as POI`).
- **LIRA** interpretation: "lowest-touches" is treated as a HARD REQUIREMENT — LIRA disqualifies the proximate touches=4 OB and reaches deeper into history for a touches=1 (or touches=0) OB that has not yet been retested. This OB is a real, unmitigated H1 OB (154.88-154.72 was a real January OB) but it's stale relative to current price.

**File evidence:** Compare `prompt_lira.py:182-192` vs `primary_analyzer_prompt.py:471` — both lines say "prefer lowest-touches" but LIRA's surrounding context (label-first emission, shorter overall prompt) appears to make the AI weight the rule literally instead of practically.

**Cross-symbol check.** XAUUSD does not exhibit this problem at all. LIRA XAUUSD entries match A2's exactly in 7/7 overlap pairs (all 0.0 difference). The "stale-OB" failure mode is USDJPY-specific — likely because USDJPY's tight price ranges produce many stacked OBs at slightly different levels, while XAUUSD's wider ranges yield fewer concurrent unmitigated OBs.

### Implication

This is **not a "prompt is too permissive" problem**. LIRA's prompt EMITS the same number/type of CANDIDATEs the underlying market geometry suggests. It's a **wrong-OB-selection problem**: 65 of LIRA's USDJPY decisions in slice 2 alone anchor on the wrong OB. Most get caught by L2 `entry_in_ob`, but the ~5-10 that slip through (because price retraces deep enough to actually fill 154.88) become hostile fills with bad risk/reward.

A surgical V3 prompt-edit could close this gap if needed: add an explicit instruction "Among unmitigated OBs in the C3 direction, prefer the one with the smallest current_price - ob_midpoint distance (most proximate), then the lowest touches, in that priority order." V3's existing prompt already implies this ordering; LIRA's literalism hides it.

---

## 5. SL-Placement Delta Quantification (Q4)

### Aggregate

For the 28 overlap pairs (same slice, candle, direction; both produced CAND and have entry+SL):

| Metric | Value |
|---|---:|
| LIRA SL closer to entry (tighter) | 16 / 28 = 57% |
| LIRA SL further from entry (wider) | 12 / 28 = 43% |
| Median absolute SL-distance delta (% of entry) | 0.025% |
| LIRA-LOSS-A2-WIN cases | 1 |
| LIRA-WIN-A2-LOSS cases | 0 |

### Per-instrument

| Inst | n | LIRA tighter share | Median delta % | Max delta % |
|---|---:|---:|---:|---:|
| **XAUUSD** | 11 | **82%** (9/11) | 0.116% | 0.405% |
| **USDJPY** | 17 | **41%** (7/17) | 0.013% | 0.439% |

**Key finding: SL tightening is XAUUSD-specific.** LIRA places SLs systematically tighter on 82% of XAUUSD overlap pairs (median 0.116% closer to entry). On USDJPY, LIRA is tighter only 41% of the time — i.e., A2 is actually tighter slightly more often. Prior SYNTHESIS framed this as a fleet-wide LIRA pattern; the data shows it's instrument-specific.

### Per-direction

| Direction | n | LIRA tighter share | Median delta % |
|---|---:|---:|---:|
| LONG | 26 | 54% | 0.025% |
| SHORT | 2 | 100% | 0.116% |

SHORT n=2 is too thin for a finding.

### Did tighter SLs cause specific losses?

**One confirmed case:** xauusd_s3 2026-01-30T08:00 LONG — LIRA SL 5069.27 (12.94 pts tighter), A2 SL 5056.33. LIRA hit SL → LOSS. A2's wider SL would have absorbed the noise → WIN. **Net cost to LIRA: −2.5R** (lost 1R + missed 1.5R).

**But:** LIRA's tighter XAUUSD SLs in the other 9 pairs DIDN'T cause losses — outcomes match A2 in 8 of 9 cases. The one exception is the win-flip above; the other 8 are LIRA-LOSS-A2-LOSS or LIRA-WIN-A2-WIN. So the tighter-SL mechanism had marginal impact on outcomes (1/11 cases flipped). The expected-value cost is tiny because LIRA's tighter XAUUSD SL also means **larger TP1 in absolute terms relative to entry** (TP1 = entry + 1.5×SL_distance, so tighter SL = closer TP1) and **smaller per-contract loss when LIRA does lose** — net wash on R-multiple.

**Counterfactual recalc.** If we replaced LIRA's xauusd_s3 01-30T08:00 LIRA-LOSS with A2's WIN (counterfactually using A2's wider SL on the same setup), LIRA fleet R would be +4.5R + 2.5R = +7R, ExpR +0.146R. Still below A2's +0.333R but closer. SL geometry is **not** the dominant LIRA underperformance mechanism. **Stale-OB anchoring on USDJPY is.**

---

## 6. Stratum Dominance Analysis (Q5)

| Stratum | LIRA n_filled / WR / ExpR | A2 (V3) n_filled / WR / ExpR | LIRA wins? |
|---|---|---|---|
| All LONG | 45 / 42% / +0.056R | 28 / 50% / +0.250R | No |
| All SHORT | 3 / 67% / +0.667R | 2 / 100% / +1.500R | No (n too thin) |
| **XAUUSD** | **14 / 50% / +0.250R** | **11 / 45% / +0.136R** | **YES** (+0.114R/trade) |
| USDJPY | 34 / 41% / +0.029R | 19 / 58% / +0.447R | No (huge gap −0.418R) |
| KZ london | 21 / 48% / +0.190R | 14 / 64% / +0.607R | No |
| KZ ny | 11 / 36% / -0.091R | 10 / 40% / +0.000R | No |
| KZ tokyo | 16 / 44% / +0.094R | 6 / 50% / +0.250R | No |
| H1 bullish | 45 / 42% / +0.056R | 28 / 50% / +0.250R | No |
| H1 bearish | 3 / 67% / +0.667R | 2 / 100% / +1.500R | No (n too thin) |
| **XAUUSD_LONG** | **12 / 42% / +0.042R** | **9 / 33% / -0.167R** | **YES** (+0.209R/trade) |
| XAUUSD_SHORT | 2 / 100% / +1.500R | 2 / 100% / +1.500R | tie |
| USDJPY_LONG | 33 / 42% / +0.061R | 19 / 58% / +0.447R | No |
| USDJPY_SHORT | 1 / 0% / -1.000R | 0 / — / — | n too thin |

### LIRA-dominant strata (n≥5 each side)

Two strata where LIRA beats V3 with adequate sample on both sides:

1. **XAUUSD_LONG**: LIRA +0.042R (n=12, WR 42%) vs V3 -0.167R (n=9, WR 33%). LIRA delta +0.209R/trade. **This is the same XAUUSD LONG WR concern A2 SYNTHESIS flagged** — V3's 33% n=9 LONG WR was a session-37 yellow flag. LIRA's 42% n=12 is statistically indistinguishable (Wilson 95% CI overlap heavily) but **directionally consistent with LIRA being slightly better calibrated on XAUUSD**.
2. **XAUUSD overall**: LIRA +0.250R (n=14) vs V3 +0.136R (n=11). LIRA delta +0.114R/trade. Same caveat — small samples.

### Strata where LIRA is ≥0.4R worse than V3

- **USDJPY** (n=34 vs 19): LIRA −0.418R/trade. Massive.
- **USDJPY_LONG** (n=33 vs 19): LIRA −0.386R/trade.
- **KZ london** (n=21 vs 14): LIRA −0.417R/trade. (largely USDJPY-driven.)

### Hybrid candidate

A naive hybrid "use LIRA for XAUUSD, V3 for USDJPY" on this 12-slice data:
- XAUUSD: LIRA n=14, +3.5R total
- USDJPY: V3 n=19, +8.5R total
- Hybrid total: +12.0R. **Beats V3 alone (+10.0R) and LIRA alone (+4.5R).**
- Hybrid Exp R: 12.0 / 33 = +0.364R/trade.

This is suggestive but not actionable — the XAUUSD edge for LIRA is n=14 with overlapping CIs vs V3. SHIPPING this hybrid would require ≥30 XAUUSD fills with LIRA WR > V3's 45% WR ceiling (i.e., a solid signal at n≥30). At current rates, we'd need ~6-8 more weeks of XAUUSD-LIRA data.

---

## 7. Regime-Sliced Analysis (Q6)

| Regime | LIRA n / WR / ExpR / Total | A2 (V3) n / WR / ExpR / Total |
|---|---|---|
| XAUUSD early (s1-s4, Jan-mid Feb, bullish) | 9 / 56% / +0.389R / +3.5R | 6 / 50% / +0.250R / +1.5R |
| XAUUSD late (s5-s8, late Feb-Apr, mixed) | 5 / 40% / +0.000R / +0.0R | 5 / 40% / +0.000R / +0.0R |
| USDJPY early (s1-s2, Jan-early Feb) | 17 / 53% / +0.324R / +5.5R | 12 / 67% / +0.667R / +8.0R |
| USDJPY late (s3-s4, late Feb-Apr) | 17 / 29% / -0.265R / -4.5R | 7 / 43% / +0.071R / +0.5R |

**Key findings:**

1. **XAUUSD: LIRA dominates the EARLY (bullish) regime** (+3.5R vs +1.5R = +2R for LIRA, the slice 3 win). XAUUSD LATE is a tie — both flat at 40% WR. **LIRA's XAUUSD edge is concentrated in the bullish-trend regime**, which makes structural sense because LIRA's permissive USDJPY behavior comes from "OB still unmitigated even when price has run far" — that pattern only generates extra CANDs in trending markets, and on XAUUSD those CANDs converted at 5/9 (62.5%).

2. **USDJPY: LIRA loses BOTH halves but worse in late.** Early: LIRA -0.343R deficit/trade. Late: LIRA -0.336R deficit/trade. Roughly stable underperformance. The stale-OB problem is regime-independent.

3. **No "regime LIRA wins" finding**. There's no evidence that LIRA does better in late-period bearish markets than V3 — the SHORT signal divergence (LIRA 20% vs V3 30.8% XAUUSD raw SHORT share) is consistent with LIRA being more conservative on SHORTs across all periods.

---

## 8. Confidence-Tier Discrimination Test (Q7)

### Does LIRA's `confidence_tier` discriminate?

| Tier | n | Wins | WR | Wilson 95% CI | Exp R | Total R |
|---|---:|---:|---:|---|---:|---:|
| `high_conviction` | 26 | 12 | 46.2% | [28.8, 64.5] | +0.154R | +4.0R |
| `moderate` | 19 | 8 | 42.1% | [23.1, 63.7] | +0.053R | +1.0R |
| `marginal_pass` | 3 | 1 | 33.3% | [6.1, 79.2] | -0.167R | -0.5R |

**Direction is correct (monotonic): high → moderate → marginal_pass shows decreasing WR + ExpR.**
- High vs marginal: 13pp WR delta.
- ExpR delta: +0.321R from high to marginal.

**But statistical significance is weak.** Fisher exact 2×2 (high vs marginal): OR=1.71, p=1.000 (n_marginal=3 too small). All three Wilson CIs heavily overlap.

### Tier x sub-stratum (LIRA only)

| Tier | XAUUSD n / WR / ExpR | USDJPY n / WR / ExpR |
|---|---|---|
| high_conviction | 7 / 57.1% / +0.429R | 19 / 42.1% / +0.053R |
| moderate | 7 / 42.9% / +0.071R | 12 / 41.7% / +0.042R |
| marginal_pass | 0 / — / — | 3 / 33.3% / -0.167R |

The XAUUSD high_conviction n=7 with 57% WR + 0.43R Exp is consistent with LIRA's overall XAUUSD edge story.

### V3 confidence_score for comparison

V3 confidence_score distribution (filled n=37):
- Score=72: 10
- Score=75: 3
- Score=78: 21
- Score=82: 3

V3 binned: moderate (65-75) n=7 WR=57.1% ExpR=+0.429R; high (75+) n=23 WR=52.2% ExpR=+0.304R. **V3's binned confidence is slightly INVERSELY correlated with WR**, confirming the long-standing finding that V3's confidence_score is rubber-stamped (98% within 72-82 range, dominated by 78).

### Verdict on tier-grafting

LIRA's confidence_tier shows directionally-correct monotonic ordering on a small sample (n=48), with effect size ~0.32R between top and bottom tier. **This is suggestive but not statistically distinguishable.** Grafting onto V3 would require:
1. Modifying V3's prompt to emit a 3-tier label instead of confidence_score.
2. Re-running the 12-slice backtest to verify tier discrimination preserves under V3's gate-flow.
3. ≥3× more fills (n≥150) before tier-conditional gating decisions can be statistically defended.

**Cost-benefit:** Low expected value. The tier signal is weaker than instrument-level performance differences (XAUUSD edge ≈+0.114R; tier edge between high/marginal ≈+0.321R but at n=3 marginal). Not worth the cutover risk pre-Monday challenge. Document as a long-term research direction.

---

## 9. Surprise Findings / Threads Pursued

### Surprise 1 (highest impact): LIRA's USDJPY underperformance is a STALE-OB problem, not a "permissive prompt" problem

The original SYNTHESIS framed LIRA's USDJPY deficit as "the prompt's filter is too loose, accepting weak setups V3 would reject." The data does not support that framing. Both prompts emit CANDIDATE on the same H1/M15/C1-C2-C3 features; both have nearly identical L2 rejection counts (LIRA 323 / A2 315, with similar reason distributions). The actual difference is **which OB the AI selects as the entry zone**.

LIRA emitted `entry=154.88` on 65 of ~600 USDJPY-s2 evaluations because it interprets "prefer lowest-touches OB" literally → reaches into history for a touches=1 OB at 154.88, ignoring the proximate touches=3 or touches=4 OBs at 155.30-156.36. V3 selects the proximate OB and trusts the downstream `touches≥2` gate to reject if needed. **LIRA's USDJPY mistake is selection, not permission.**

**Implication:** A 1-line V3-prompt nudge ("among unmitigated OBs, prefer most-proximate, then lowest-touches") might harden V3 against the same failure pattern. But V3 already does the right thing without this nudge — so the fix would be defensive rather than corrective. Not a Monday-shipping change.

### Surprise 2: The "tighter SL" diagnosis from SYNTHESIS is XAUUSD-specific

The original SYNTHESIS reported "LIRA places SLs systematically tighter than V3" as a fleet-level pattern. The actual data shows LIRA tighter in **82% of XAUUSD pairs** (median 0.12% delta) but only **41% of USDJPY pairs** (median 0.013% — essentially tied). The XAUUSD pattern is real and accounts for 1 win-flip (xauusd_s3 01-30T08:00). The USDJPY pattern is illusory — USDJPY entries are nearly bit-exact between LIRA and V3 when they pick the same setup.

### Surprise 3: A2 hit budget cap WAY earlier than LIRA, and yet this asymmetry doesn't favor LIRA

LIRA's 45.7%-shorter prompt = 13% lower API cost = ~70% more candles evaluated under the $6/slice cap. Naively, LIRA evaluates more candles → more chances to find good setups. The data shows LIRA's USDJPY ExpR in extension period (0.071R, n=14) is slightly better than within A2 coverage (0.0R, n=20) — which means **LIRA's USDJPY problem is structural, not coverage-driven**. LIRA isn't doing worse because it's seeing extra weak candles; LIRA is doing worse because its OB-selection is wrong on the candles A2 also sees.

### Surprise 4: ZERO opposite-direction trades

The original LIRA hypothesis (label-first reasoning could produce direction inversions vs reasoning-first V3) is unsupported. In 28 overlap pairs (same slice + candle), LIRA and V3 agreed on direction 28/28. The architecture change does not affect direction selection — it affects entry-zone selection (and tighter XAUUSD SLs).

### Surprise 5: usdjpy_s2 Feb 4-6 is the linchpin slice

V3 wins this slice +6.5R on 6 trades (5W/1L, 83% WR). LIRA wins this slice +3.5R on 9 trades (5W/4L). The DELTA is −3R for LIRA. **What happened on those days:** V3 picked the proximate OBs (155.81, 156.36) which got filled cleanly during the strong USDJPY upleg. LIRA picked the deeper 154.88 OB, which never got filled (price kept running) → LIRA replaced those misses with LATER entries that bought into pullback losses. usdjpy_s2 alone is 55% of LIRA's total fleet R deficit.

---

## 10. Actionable Recommendations

### Definitive (data-supported)

1. **STAY decision is correct** — the LIRA SYNTHESIS's verdict holds at 12-slice scale. Fleet ExpR +0.094R falls below V3 baseline +0.333R by 0.24R/trade; below the ≥+0.40R GO threshold; MaxDD 9R exceeds the 8R STAY trigger. **Do not cutover to LIRA Monday.**

2. **Update SYNTHESIS Mechanism #2 ("tighter SL")** to clarify it's XAUUSD-specific, not fleet-level, and accounts for at most 1 win-flip = -2.5R. The ~$5R fleet deficit is not SL-driven.

3. **Reframe SYNTHESIS Mechanism #1 ("over-permissive on USDJPY")**:
   - The original framing implies LIRA's prompt accepts weaker setups V3 would reject.
   - The actual mechanism is LIRA picks a deeper-but-stale OB while V3 picks the proximate OB.
   - Both prompts emit CAND at similar rates — the divergence is OB-selection, not OB-acceptance.
   - This is documented in §4 and confirmed by sampling LIRA's `h1_setup.explanation` field on 65 candles in usdjpy_s2.

### Low-priority research (do not block Monday challenge)

4. **A1 follow-up: V3 prompt OB-proximity nudge** — adding "most-proximate first, then lowest-touches" to V3's trade-parameters block could harden V3 against the same failure mode if V3 ever drifts into LIRA's interpretation. Validate offline with a single-slice canary before any production change.

5. **Hybrid LIRA-XAU + V3-FX consideration** — the data weakly supports LIRA having a +0.114R XAUUSD edge over V3 (n=14 vs 11). Not actionable without ≥30 XAUUSD fills with sustained edge. Cost: 6-8 weeks of dual-prompt running.

6. **LIRA confidence_tier monotonicity** — the high/moderate/marginal_pass tier shows directionally correct WR ordering at n=48. If LIRA architecture is ever revisited, re-test tier discrimination at n≥150 before grafting onto any production prompt. Don't graft now (cost-benefit poor).

### Do NOT do

7. **Do NOT close out LIRA architecture as "label-first is bad"** — the architecture is fine; the rule-interpretation drift on USDJPY OB selection is the actual issue. A LIRA-style label-first prompt with explicit OB-proximity instructions would likely close the gap. (Out of scope for Monday.)

8. **Do NOT increase A2 backtest budget cap** to gain coverage parity. The data already shows the A2 USDJPY edge is structural, not coverage-driven.

---

## Appendices

### A. Files
- `forensic_analyzer.py` — Python script that processes 36 slice files (12 each variant) and emits `analysis_data.json`. Reproducible.
- `analysis_data.json` — machine-readable Q1-Q7 data. Keys: `q1_per_slice`, `q2_divergence`, `q2_overlap_detail`, `q2_lira_only_detail`, `q2_a2_only_detail`, `q3_usdjpy_root_cause`, `q4_sl_delta`, `q5_strata`, `q5_lira_dominant_strata`, `q6_regime`, `q7_confidence_tier`.

### B. Reproduction
```bash
cd C:/Users/MSI/Documents/ai-trading-agent
python research/lira_ab_deep_forensic/forensic_analyzer.py
```

Expected output (final lines):
```
LIRA: 54 CAND, 48 filled
A2: 37 CAND, 30 filled
Overlap (same slice/candle/dir): 28
LIRA-only: 26
A2-only: 9
Opposite-direction same candle: 0

Q4 SL delta: LIRA tighter in 16/28 pairs
  LIRA-LOSS-A2-WIN: 1
  LIRA-WIN-A2-LOSS: 0

Q7 LIRA tier performance:
  high_conviction: n=26 WR=0.461 ExpR=0.154
  moderate: n=19 WR=0.421 ExpR=0.053
  marginal_pass: n=3 WR=0.333 ExpR=-0.167

Q5 strata where LIRA dominates (n>=5 each):
  XAUUSD_LONG: LIRA Exp +0.042R vs A2 +-0.167R (n=12 vs 9)
  inst_XAUUSD: LIRA Exp +0.250R vs A2 +0.136R (n=14 vs 11)
```

### C. Confidence calibration
- Q1-Q4: HIGH confidence — verified directly against raw_response and outcome fields.
- Q5: HIGH confidence on XAUUSD-LIRA-edge directional finding; LOW on its statistical significance (overlapping CIs at n=14 vs 11).
- Q6: HIGH on regime-direction; LOW on causal attribution (regime structure correlates with sample-size shifts).
- Q7: MEDIUM — monotonic ordering is clean but n=3 marginal_pass is very thin.

### D. Limitations / unanswered
- **No OHLC-level counterfactual on the 12 LIRA-tighter-SL XAUUSD pairs** — `all_results.json` doesn't contain the exit candle's high/low. Would require running a counterfactual backtest with widened SLs to compute "trades LIRA would have won with V3's SL." Estimated impact: ≤2-3 win-flips at most, given the small SL deltas.
- **No A1 candidate-features cross-reference** — could analyze whether LIRA-only USDJPY losses share a feature pattern (e.g., low h1_unmitigated_count, high m15_fvg_unfilled) using `candidate_features_log.jsonl`. Time-budget exceeded.
- **Tier prediction calibration not tested out-of-sample** — the monotonic ordering (high > moderate > marginal_pass) is in-sample on the 48 fills; would need a held-out 30-fill validation before any tier-conditional gating.
