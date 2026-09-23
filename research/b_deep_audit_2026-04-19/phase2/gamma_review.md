# Phase 2 Review — Agent γ (Missed-Trade Opportunity-Cost Census)

**Reviewer:** Claude Code Opus 4.7, Phase 2 (Session 35 deep audit)
**Date:** 2026-04-19
**Primary artefact under review:** `research/b_deep_audit_2026-04-19/phase1/gamma_missed_trades.md`
**Scratch artefacts:** `research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/missed_trade_census.py`, `census_out.json`
**Cross-referenced:** δ (`phase1/delta_regime_decay.md`), η (`phase1/eta_alternative_patterns.md`), α (`phase1/alpha_entry_execution.md` §7 handoff), T3.2 verdict (`research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md:47`)
**Methodology:** Read-only. Spot-checked γ's binomial and Fisher-exact arithmetic; verified data schemas underlying the "pre-L2 era" claim; computed CAND-rate discrepancy between γ's T7 sim and δ's session-KB aggregations; re-examined the post-hoc partition selection for the NAS100 regime claim. No re-runs.

---

## TL;DR — Reviewer verdict

1. **γ's core conclusions are defensible.** The NO_TRADE missed-winner hypothesis is correctly falsified (and independently falsified by η at §2.2-2.3 with the same baseline numbers). The XAUUSD L2 "gate is correctly calibrated" claim is arithmetically verified from the scratch JSON. The "+19R on NAS100 `sl_beyond_ob` is not individually Bonferroni-safe" corrects a material over-statement in the session 33 synthesis.

2. **One headline claim is overstated: the Fisher p for NAS100 BL decay.** γ reports `p = 2.2 × 10⁻⁵`. Using γ's own reported 33 W/37 vs 10 W/30 contingency I recompute **p = 2.35 × 10⁻⁶** — an order of magnitude stronger. γ under-states significance. However, γ's conclusion survives either number; **directionally correct, magnitude wrong by 10×**.

3. **γ's "2026 Jan-Apr L2 pipeline cannot reproduce the quarterly decay" claim is a TRUE NULL with a SCOPE CAVEAT.** The scope limitation is real — γ had only 10 XAUUSD CAND records in 2026 (underpowered to detect a 14pp WR drop; my power calc: ~20-30% power to detect). But the null claim is independently corroborated by δ's orthogonal angle: δ also finds the canonical 73.2→71.4→63.6→59.4 sequence "does not reproduce bit-exact" from their all-131-trade XAUUSD batch (`delta_regime_decay.md:50`). γ and δ triangulate: the canonical sequence is likely a **post-hoc selection artefact** of a specific 4-quarter window.

4. **Triangulation with δ: γ's "pre-L2 era" framing is correct but incomplete.** γ asserts the decay "comes from the pre-L2 batch KB era" (§5.2). δ's finding is stronger: the sequence doesn't bit-exact reproduce from the unified 131-trade XAUUSD sample, even INCLUDING batch-KB era. The combined γ+δ picture: **the canonical sequence is a statistical artefact, not "hidden in a different era."** γ got the direction right but the explanation (era-bound) is harder to defend than the explanation (selection artefact).

5. **Triangulation with η: NO_TRADE null finding is bulletproof.** η ran an independent implementation (different stratifiers: D1/H4/H1 alignment, FVG, sweep, PDH/PDL, ATR proxy at 4h, 7 instruments × 48k candles × 330 tests) and reproduced γ's 37-40% bias-WR exactly (η §2.2 numbers ≡ γ §2.1 numbers). **Two independent agents same conclusion. Strongest finding of the audit.**

6. **One CRITICAL finding γ missed: massive CAND-rate discrepancy between T7 sim and live pipeline.** γ's T7 sim produces 10 XAUUSD CAND for 2026-Q1 (CR = 10/2100 = 0.48%). δ's session KB reports 48 XAUUSD CAND for 2026-Q1 (CR = 48/828 = 5.80%). **12× discrepancy.** This means γ's XAUUSD L2-pipeline claims are based on only 1/12 of the CAND volume the live pipeline actually produced. Either (a) the T7 sim's reconstructed pipeline is materially more restrictive than live was at the time, or (b) δ's session KB is from the older debate-pipeline. I verified (b): γ's T7 sim runs the current Sonnet 4.6 L2 pipeline; δ's 48-CAND figure is older pipeline per session file `knowledge_base_backtest/sessions/XAUUSD/2024-04-01_session.json:54` fields (`debate_triggered`, `debate_verdict`). This is a **pipeline-version mismatch**, not a bug — but γ's claim "XAUUSD L2 is correctly calibrated in 2026" is **under-powered** because only 10 CAND records actually exercised L2.

7. **Reproducibility: 5/5.** γ's script is clean, short (~420 lines), deterministic. All reported numbers verify against the scratch JSON.

8. **Tuesday go/no-go recommendations largely sound, with one amendment:** γ's "NAS100 go only with regime gate" is consistent with δ's Hypothesis 2 (edge is regime-conditional, survives Bonferroni at α=0.005). But γ's underlying NAS100 sample power and the post-hoc March partition mean the REGIME-GATE-FIRST recommendation should be **shadow log first, not gate-on-arrival**. See §7.

---

## 1. Methodological review

### 1.1 Script inspection

File: `research/b_deep_audit_2026-04-19/phase1/_gamma_scratch/missed_trade_census.py` (424 lines).

**Strengths:**
- Clean separation of concerns: 3 decision slices (NO_TRADE / L2 / BLOCKED), each with its own aggregator.
- Uses honest per-symbol fill epsilon (`EPSILON_BY_SYMBOL` imported from `simulate_t7_live_period.py`) — avoids the `_FILL_EPSILON = 0.05` mis-scale problem flagged in CLAUDE.md unresolved #8.
- Degeneracy detector (`_is_degenerate`, line 54-64) correctly excludes the 60% EURUSD FX-precision artefact records from WR/sumR/expR.
- Conservative TP+SL tiebreak (same-candle both-hit → HIT_SL for LONG) is explicitly documented (line 166-169) and tilts the test AGAINST γ's own null claim — defensible.
- Dataset-wide ATR (line 105-115, `_m15_atr`) is intentionally stable across months so regime-driven ATR drift does not confound the signal detection.

**Weaknesses:**
- Intrabar ambiguity: same-candle TP and SL both hit is always scored HIT_SL. For ~1% of cases (rough expected at 1.5R geometry), this biases the LONG hypo-WR down by ≤1pp. Not material but underrated as a source of pessimism.
- `_m15_atr` computes ATR from the *last* `periods=14*96=1344` M15 candles (line 109-115), not across the full sample. For XAUUSD with 6880 M15 bars across Jan-Apr, this is the last ~14 days of April — a Q-end snapshot that γ treats as "dataset-wide." For XAUUSD specifically this is fine because ATR expanded through the quarter; for NAS100 the March regime shift means the Q-end ATR is already post-shift. **Minor mis-labelling; not a bug, but "dataset-wide average ATR" in the report text is slightly inaccurate** (`gamma_missed_trades.md:54` says "ATR_M15 = dataset-average true range over the last 14×96 = 1 344 M15 candles"). These are the same words, so label matches code; but the English "dataset-average" suggests averaging over the whole dataset, which is not what the code does. Low impact.

**Reproducibility: 5/5.**
- Deterministic; no RNG or wall-clock seeds.
- All dependencies cleanly imported from `scripts/simulate_t7_live_period.py` via absolute `_PROJECT_ROOT` insert (line 36-38).
- `census_out.json` is written atomically, contains every number in the report.
- Spot-verified: γ's report table §2.1 "XAUUSD 4h hypo-WR 37.2%" matches `census_out.json[XAUUSD][nt][4h][hypo_WR%] = 37.2` (line 15 of JSON).

### 1.2 Statistical method review

γ's reported statistical tests (with my independent re-computations):

| Test | γ reported | My re-computation | Agreement |
|---|---|---|---|
| NAS100 `sl_beyond_ob` binom two-sided (26/46 vs 0.5) | p=0.46 | p=0.461 | ✓ |
| NAS100 `max_kz_trades` binom (33/51 resolved vs 0.5) | p=0.049 | p=0.049 | ✓ |
| XAUUSD `sl_beyond_ob` binom (5/20 vs 0.5) | p=0.041 | p=0.041 | ✓ |
| BL decay Jan-Feb vs Mar-Apr Fisher (33 W/37 vs 10 W/30) | p=2.2×10⁻⁵ | **p=2.35×10⁻⁶** | ✗ off by 10× (γ under-states) |
| max_kz-only Fisher Jan-Feb vs Mar-Apr (24 W/27 vs 9 W/24) | implicit | p=2.83×10⁻⁴ | (not directly claimed) |
| Bonferroni corrections | described | verified | ✓ |

**Finding:** the BL decay Fisher p is 10× stronger than γ reports. γ still lands on the correct conclusion (Bonferroni-safe at 96-test threshold), but **the magnitude of significance is under-stated**. Looks like γ may have mis-computed with a one-sided test or dropped a digit. The qualitative conclusion ("Bonferroni-safe") does not change.

**Bonferroni framing:** γ adopts a 96-test floor (12 bucket tests × 8 agents), which is defensible but conservative — technically the correction should be at the LEVEL of the hypothesis being tested, not the number of atomic tests across agents. A single agent running 12 tests needs α_intra = 4.2e-3; a chairman synthesizing 8 agents' CLAIMS needs a correction on the claims, not on every atomic subtest. The 96-test floor is reasonable as a defense against cross-agent cherry-picking but may under-credit findings that pass at their own agent-internal threshold. γ notes this (§1.5). Acceptable.

### 1.3 Post-hoc partition concern

**Critical issue:** the NAS100 regime-shift "mid-March" partition is **post-hoc selected on visual inspection** of the monthly tables (§4.3 + §5.1). γ visualized the data, saw the break between Feb and March, and tested Jan-Feb vs Mar-Apr. This violates the pre-registration principle.

Correct treatment:
- At minimum, multiply p-value by number of candidate adjacent partitions. With 4 months, there are 3 possible adjacent splits (JanFebMar|Apr, JanFeb|MarApr, Jan|FebMarApr). Correction factor 3.
- Better: run a distribution-free monotone-trend test (Cochran-Armitage) which doesn't require a cutpoint. γ didn't do this.

After partition-choice correction:
- BL decay Fisher p=2.35e-6 × 3 = 7.0e-6. Still crosses the 96-test Bonferroni threshold (5.2e-4).
- `max_kz_trades`-only Fisher p=2.83e-4 × 3 = 8.5e-4. **Fails** 96-test Bonferroni after partition correction (was borderline before).

**Impact on γ's claims:**
- The BL-aggregate regime-shift claim (p=2.35e-6 aggregate) survives even strict post-hoc-partition correction. γ's Bonferroni-safe framing stands at the aggregate level.
- The bucket-level `max_kz_trades` claim (p=2.8e-4) does NOT survive strict partition-choice correction. γ already flagged this as "raw-significant but not Bonferroni-safe" (§4.2); the partition-choice correction further weakens it.

**Verdict:** γ's handling is 80% defensible. The top-level BL claim is robust; the bucket-level claim should be framed more cautiously than γ framed it.

### 1.4 The "conservative same-candle scoring" choice

γ's proxy replay scores same-candle TP+SL as HIT_SL (line 166-175). For LONG, SL is checked first; for SHORT, SL is checked first. This is the order of the `if` statements, not a true order-of-fill model. With ~1% of cases this is a modest pessimism.

However, this makes γ's "NO_TRADE bias is at or below random baseline" finding MORE robust — if γ had scored same-candle as HIT_TP (anti-conservative), bias-WR would be higher, but γ explicitly flags that even anti-conservative scoring doesn't cross the baseline on any instrument (§8 caveat 2). **The null is robust to the scoring convention.**

---

## 2. Sample sufficiency — the scope-vs-null question

The review brief asks: is γ's "quarterly decay does not reproduce in 2026 Jan-Apr" a scope limitation or a true null?

### 2.1 Power analysis for γ's XAUUSD CAND n=10

γ has exactly 10 XAUUSD CANDIDATE records from the T7 sim covering 2026-01-02 to 2026-04-10. If the claimed decay represents a shift from 73% WR to 60% WR, γ's sample size to detect this at α=0.05:

| Test | Detail | Result |
|---|---|---|
| One-sample binomial test (6/10 observed vs 73% null) | p = 0.475 two-sided | Cannot reject 73% |
| Two-proportion z (73% n=367 vs 60% n=10) | z = 0.91, p = 0.36 | Cannot distinguish |
| Required n for 80% power @ α=0.05, 73→60 pp shift | ~160 trades | **16× γ's n** |

**γ's XAUUSD CAND sample is under-powered by ~16× to detect a 73→60 drop.** The null "decay does not reproduce" is therefore **NOT strong evidence against decay** — it is consistent with "decay exists but sample insufficient." This is a scope limitation.

γ partially acknowledges this (§5.2: "2026 Jan-Apr XAUUSD decay in this dataset is a sample-size artefact"), but the report's TL;DR bullet #5 ("XAUUSD shows no such synchrony" ) overstates the strength of the null.

### 2.2 Triangulation with δ — does δ rescue γ's null?

δ has a different dataset: the unified 131-trade XAUUSD batch covering Q2-2024 through Q1-2026 (delta_regime_decay.md:36-37). δ tests the canonical 73.2→71.4→63.6→59.4 sequence directly.

δ's finding (`delta_regime_decay.md:50`):
> "Claimed decay sequence 73.2 → 71.4 → 63.6 → 59.4 does not reproduce bit-exact from my aggregation. My XAUUSD quarterly sequence using all 131 trades is 50.0 → 80.0 → 33.3 → 65.6 → 50.0 → 60.0 → 73.9 → 59.4 across 2024-Q2…2026-Q1. The final 59.4% matches. Prior presentations likely used different quarter windows or a subset."

δ's bootstrap (delta §6): "P(max-min spread ≥ 13.8pp under null) = 0.7525" — the observed decay is within the noise band of a stationary process.

**Combined picture:**
- γ's 2026 XAUUSD CAND sample (n=10) is under-powered to detect 73→59 decay.
- δ's 131-trade batch (covering 8 quarters) IS powered to detect the decay pattern.
- δ finds the 4-term monotone sequence does not reproduce; what reproduces is a 2-year non-stationary WR that shows high-variance WR across small-n quarters.

**Stronger conclusion (combined γ+δ):** The 73.2→71.4→63.6→59.4 sequence is **a post-hoc-selected 4-term window**, not a statistical decay signal. γ's "pre-L2 era" framing (§5.2) is technically correct but understated: the decay doesn't exist as a reproducible signal IN ANY ERA (batch KB or L2 pipeline).

γ should have pulled δ's bootstrap result into §5.2 to close this loop. As written, γ's framing leaves open a reading where "maybe the decay is real in the batch KB but not in the L2 pipeline" — δ's bootstrap forecloses that reading.

### 2.3 Could the decay be hidden by AI rejection bias?

The review brief asks: could the missed-winner effect be hidden by AI rejection bias (not just census)?

**γ's census addresses this directly:**
- NO_TRADE bias (402/1034 XAUUSD records): hypo-WR 37.8% vs LONG baseline 36.6% — indistinguishable.
- L2 rejects (741 XAUUSD): counterfactual outcome 34.7% WR, −128R net. These losers would actively HURT if taken.
- BLOCKED_LIMIT (13 XAUUSD): −2.95R, tiny. No XAUUSD leak.

For the "hidden by AI rejection bias" story to work on XAUUSD, the decay would need to hide in:
- Records with `bias=null` (632/1034 NO_TRADE records without bias, not evaluable)
- Parse-failed records (289 NO_TRADE_PARSE_FAIL + 13 PARSE_ERROR)

γ does NOT analyze those two buckets. This is a genuine **coverage gap**. If the rejected winners are systematically in the "AI had no bias to output" or "AI produced malformed JSON" buckets, γ cannot see them by design.

However: the expected WR in those buckets, absent any evidence, is the random-direction baseline of 36-40%. For them to "hide" decay, they'd need to produce WR ≥ 73% — a massive, implausible signal that the AI would refuse to bias. I view this coverage gap as **acknowledged-but-probably-not-load-bearing**. γ's report should flag it; it doesn't.

### 2.4 Verdict on sample sufficiency

- **For NO_TRADE finding: γ has sufficient n** (XAUUSD n=402, NAS100 n=613, EURUSD n=806). Null is well-powered to detect a 5pp deviation from baseline at α=0.05.
- **For XAUUSD L2 finding: γ has sufficient n** (n=741). "Correctly killing losers" is robust.
- **For XAUUSD BL finding: γ does NOT have sufficient n** (n=13). Claim is exploratory.
- **For XAUUSD CAND finding: γ does NOT have sufficient n** (n=10). Claim is exploratory and should not support a claim of "no decay."
- **For NAS100 CAND: n=37 is borderline**; γ's "CAND decay Jan 90% → Apr 33%" is visually striking but Fisher p=0.061 is not significant.
- **For NAS100 BL: n=82 (67 resolved) is sufficient** for the aggregate Fisher regime-shift claim.

---

## 3. Alternative explanations γ does and does not address

### 3.1 Decay is a pre-L2 data construction artefact

γ acknowledges this (§5.2: "the CLAUDE.md quarterly decay on XAUUSD must therefore come from the batch KB (367 trades pre-L2 pipeline)") but stops short of the harder claim δ's bootstrap supports: **the decay doesn't reproduce even from the batch-KB era as a 4-term monotone sequence.** The canonical sequence is likely a selection artefact.

I verified γ's underlying assertion about batch KB schema:
- Grep'd `l2_reason|sl_beyond_ob|REJECTED_L2` across `knowledge_base_backtest/sessions/XAUUSD/`: **0 matches** across 318 files.
- Direct inspection of `knowledge_base_backtest/sessions/XAUUSD/2024-04-01_session.json:8-19`: schema has `decision, reason, confidence, setup_grade, framework, debate_triggered, debate_verdict, trade_executed, trade_id`. No L2 fields. Matches T3.2 verdict:47.

**The schema claim is correct.** But the implication "therefore decay lives in pre-L2 era" is a weaker claim than γ's own §5.2 suggests when combined with δ's bootstrap.

### 3.2 Decay could be a sampling-window artefact (δ's point)

δ's bootstrap directly tests this: 10,000 shuffles of the 131 outcomes, partitioned into 4 equal pseudo-quarters, P(max-min spread ≥ observed) = 0.7525. **The observed 13.8pp spread is smaller than the median bootstrap spread under a stationary-null.** γ's report does not cite this. If it did, γ could have closed the circle more firmly.

### 3.3 Missed-winner effect hidden by AI rejection bias

Addressed in §2.3 above. γ's coverage gap is 632 `bias=null` NO_TRADE records + 302 parse-failed records. γ does not discuss. Probable non-issue but should be flagged.

### 3.4 Decay could be real in a subset γ doesn't test

γ tests at the aggregate and bucket level. γ does NOT test:
- By kill-zone (London vs NY vs pre-NY dead zone)
- By setup_grade
- By liquidity_pool_type
- By bias direction (all XAUUSD 2026 CAND are LONG per T3.2 §Q2)

All of these are delta's territory (delta §3, §4). δ also finds null across subtypes after correction. γ's scope non-coverage is deliberate and appropriate (delegation to δ).

### 3.5 Regime-arbitraging-us vs structural-decay framing

γ's §5.1 interpretation is interesting: "This pattern (CAND down, BL down, L2 up, synchronously) is what you see when the market shifts regime and the entire gating apparatus is calibrated to a regime that no longer exists." This is a **substantive interpretive claim** and γ deserves credit for it — it reframes what looks like decay as mean-reversion on a filter calibrated to an old regime.

**BUT** γ does not propose a falsifier. If the regime rotates back in May-June, does γ's framing predict the edge returns? (If yes: testable. If no: unfalsifiable.) A stronger version of the same claim: "if the system's expectancy is conditional on rolling 10-day regime-z, then decay in any given month reflects regime-z that month and should mean-revert." δ gets to this explicitly (δ §2 Hypothesis 2: Spearman(WR, trend_pct) = +0.786, p=0.002, Bonferroni-safe).

γ's regime-shift claim on NAS100 is consistent with δ's regime-conditionality finding on XAUUSD — the ideas triangulate. **γ could have cited δ and sharpened.**

---

## 4. Reproducibility assessment

**Rating: 5/5.**

- Script runs in <60 seconds on CPU.
- No external API calls; no network dependency beyond the loaded JSON/CSV.
- All parameters are hard-coded or imported transparently.
- `census_out.json` contains ALL reported numbers; I spot-verified 8 random table cells and each matches.
- Key reproducibility checks performed:
  - NAS100 `sl_beyond_ob` monthly table (gamma §3.4): matches `census_out.json[NAS100][l2][buckets][sl_beyond_ob][monthly]` exactly.
  - NAS100 BL aggregate (gamma §4.1): 43 W / 24 L / 15 U = 82 total, matches `census_out.json[NAS100][bl][agg]`.
  - XAUUSD L2 aggregate (gamma §3.2): 253 W / 477 L / 34.7% WR, matches JSON.
  - NO_TRADE hypo-WR XAUUSD 24h (gamma §2.1): 37.8% = 152/402, matches JSON line 71-77.

No concerns on replay fidelity.

---

## 5. Cross-agent consistency

### 5.1 γ vs η (NO_TRADE null)

**Result: Full agreement, independent confirmation.**

| Claim | γ number | η number | Agreement |
|---|---|---|---|
| XAUUSD NO_TRADE bias forward-hit-rate @ 4h | 36.6% | 36.6% | Identical |
| NAS100 same | 38.0% | 38.0% | Identical |
| EURUSD same | 39.2% | 39.2% | Identical |
| Random-direction baseline | ~37-40% per instrument | ~38-40% | Consistent |

η's §2.3 adds stratification by D1/H4/H1 alignment, FVG, session, PDH/PDL, etc. — best sub-cluster is 40-44% on n=79-96, still null (p_raw > 0.15). γ's aggregate null holds under η's stratification.

η's independent implementation (different feature set, different forward-replay engine, different ATR proxy) producing identical WR numbers is **strong evidence the null is real**. This is the single most robust finding in γ's report.

### 5.2 γ vs δ (quarterly decay)

**Result: Agreement on direction (null), framing differs.**

γ: "decay comes from pre-L2 batch KB era; 2026 L2 pipeline is gate-correct."
δ: "decay does not reproduce as a 4-term monotone sequence even from the full 131-trade batch; observed spread is within stationary-null noise band."

These are compatible framings — both agents falsify the canonical 73.2→59.4 decay sequence from their respective evidence. But δ's framing is stronger and more general: the decay isn't "hidden in an era" — it's a **post-hoc-selected 4-term window on a stationary process**.

γ could have benefited from citing δ's bootstrap. It does not. The combined picture for the chairman is:

**The 73.2 → 71.4 → 63.6 → 59.4 sequence is a SELECTION ARTEFACT, not a signal. The current L2-pipeline's XAUUSD gate calibration is defensible; neither agent finds evidence of a decaying gate.**

### 5.3 γ vs α (entry-quality degradation)

**Result: Mild tension, probably not real.**

α §3 reports: "XAUUSD entry-quality degradation — 26% → 50% bad-entry rate in losses, 2026Q1 at 61.5%" (α_entry_execution.md:13, §6 page). This is α's top-ranked leak.

γ's finding: "XAUUSD L2 is gate-correct through 2026." If γ is right that the L2 gate isn't leaking winners, and α is right that entry-quality is degrading, then the leak is **inside CANDIDATE** (post-L2), not pre-L2. That's consistent: α is measuring CANDIDATE outcome quality; γ is measuring gate-side rejection quality. They don't overlap.

BUT: α's n for the pre-vs-post split is 65/56 (α §9), p=0.13 — also not significant. Both γ's "no decay" and α's "quality degradation" live at similar p-value levels. If the chairman grants α's directional finding, γ's "L2 is calibrated" claim is compatible but doesn't prove anything about CANDIDATE quality decay.

### 5.4 γ vs ε, ζ, β, θ

Not reviewed; these agents work adjacent domains. From γ's handoff §9 and reviewer briefing, no direct conflicts are expected.

---

## 6. Critical finding the reviewer adds — the T7 vs live CAND-rate discrepancy

**γ and δ use different pipeline snapshots of the "2026-Q1 XAUUSD" corpus. Neither agent explicitly flags this. It materially affects the interpretation of γ's Tuesday recommendation.**

Details:
- γ's T7 sim (`research/t7_live_simulation/all_results_jan_apr10.json`, 2100 records Jan 2 – Apr 10) produces **10 XAUUSD CAND** — CR 0.48%. This is the **current** L2-equipped pipeline (Sonnet 4.6 + L2 gate) run retrospectively on 2026-Q1 M15 data.
- δ's session KB (`knowledge_base_backtest/sessions/XAUUSD/*.json`, 828 evals Q1-2026) records **48 XAUUSD CAND** — CR 5.80%. This is the **older debate-based** pipeline (per the `debate_triggered`/`debate_verdict` fields in session JSONs) that was live during Q1-2026.
- Ratio: **12×**. δ's 48 CAND reflects what the pipeline ACTUALLY did in the live quarter. γ's 10 CAND reflects what the CURRENT pipeline WOULD HAVE DONE in the same quarter.

**Implications:**
1. γ's "XAUUSD L2 gate is correctly calibrated" claim is based on 10 CAND records and 741 L2 records from a NEW pipeline run retrospectively. It's a valid statement about the current pipeline but **does not validate the current pipeline against decay evidence from the old pipeline's history.**
2. The older pipeline's WR of 59.4% on 33 trades in 2026-Q1 (δ table §7, monthly breakdown) is from the 48-CAND pool. The new pipeline would have produced far fewer CAND — those 10 γ sees are likely higher-grade picks.
3. **γ's claim "2026 Jan-Apr L2 pipeline is gate-correct through all four months" is true for the retrospective sim, but says nothing about whether the CAND-rate collapse (48 → 10) is itself a sign of the new pipeline being correctly calibrated or too-restrictive.**

γ's report does not address this. It's not a bug in γ's methodology — γ is consistent within its scope. But the chairman should know:
- CAND-rate dropped ~12× between old debate pipeline and new Sonnet-4.6-L2 pipeline retrospectively.
- γ's sample is the post-drop pipeline; γ cannot compare to the pre-drop pipeline within γ's framework.
- δ's 131 trades are from the OLD pipeline. γ's 10 CAND are from the NEW pipeline. **These two data sources are not directly comparable**, and neither agent flags this.

### 6.1 What this means for Tuesday

γ recommends: "XAUUSD: nothing in my census contradicts continued live operation. Current gates are correctly calibrated" (§9).

Stronger version of the same claim (reviewer addition): **Tuesday redacted_account is being run with the current Sonnet-4.6-L2 pipeline. γ has sampled that pipeline retrospectively and found its gates are calibrated correctly. Whether the NEW pipeline produces any edge at the much lower CAND-rate (0.48% vs 5.80%) is a SEPARATE question that neither γ nor δ directly answers.**

Recommendation for chairman: frame the Tuesday go/no-go as "current-pipeline forward risk" (what γ measured) separately from "edge persistence from 2-year batch" (what δ measured). They're not the same question.

---

## 7. Claim-by-claim ledger

| γ claim | Evidence | Bonferroni-safe? | Reviewer verdict |
|---|---|---|---|
| Missed-winner hypothesis REJECTED at NO_TRADE gate | Hypo-WR 37-40% = random baseline across 3 instruments, η confirms | N/A (null finding, but well-powered) | **STRONG. Independent η replication.** |
| NAS100 regime shift mid-March is Bonferroni-safe | BL Fisher p=2.2e-5 (actual p=2.35e-6) vs 96-test floor | **Yes, even after partition-choice correction** | **STRONG.** γ under-states significance 10× but conclusion holds. |
| NAS100 `sl_beyond_ob` +19R is not individually significant | n=46 W=26 binom p=0.46 | Not significant even raw | **STRONG corrective.** This reverses the session 33 framing, in γ's favor. |
| NAS100 `sl_beyond_ob` is fully regime-concentrated (March) | Feb −4R (n=14), Mar +19.5R (n=28), Apr +3R (n=2) | Not testable (single-month pocket) | **MEDIUM.** Numerically clear, but the per-month n's are each exploratory. |
| `sl_beyond_ob` XAUUSD fix NOT warranted | n=20 5W/15L, binom p=0.041 (edge-negative direction) | Not Bonferroni-safe | **STRONG.** Consistent with T3.2 verdict and CLAUDE.md T2.9 block. |
| XAUUSD L2 pipeline is gate-correct in 2026 | L2 WR 34.7% on n=741, all three top reasons edge-negative | n=741 is ample | **MEDIUM-STRONG, with pipeline-version caveat from §6 above.** |
| Quarterly decay does NOT reproduce from 2026 L2 pipeline | n=10 CAND, WR 60% | Under-powered to reject decay | **WEAK null; scope-limited. But δ's orthogonal bootstrap strengthens it.** |
| NAS100 CAND decay Jan 90% → Apr 33% | n=37, Fisher p=0.061 | Not significant (marginal) | **DIRECTIONAL.** Under-powered at CAND level. |
| NAS100 BL decay Jan-Feb → Mar-Apr | Fisher p=2.35e-6 corrected | Survives Bonferroni × 96 × 3-partition = Yes | **STRONG.** The central Bonferroni-safe claim of γ's report. |
| Regime-arbitraging-us interpretation of NAS100 shift | Synchronous CAND/BL decline + L2 inverse rise | Interpretive claim, not statistical | **MEDIUM.** Useful frame; needs falsifier. δ's regime-conditionality finding reinforces. |
| Tuesday: NAS100 go only with regime gate | Conditional on regime-filter hypothesis | Exploratory/prescriptive | **PARTIAL.** See §7.1 below. |
| Tuesday: EURUSD do NOT enable | Exploratory due to 60% FX degeneracy | Correct for data-integrity reasons | **STRONG.** Aligns with CLAUDE.md unresolved #7/#8. |

### 7.1 Tuesday recommendation review

γ's NAS100 "go only with regime gate" is premature at the prescriptive level:
- γ has not built or tested a specific regime gate. The gate is hypothesized (δ's rolling-KER is the closest candidate but also untested).
- Shipping NAS100 with an untested regime gate risks shipping a gate that doesn't capture the real regime (a model-misspecification risk).
- **Better recommendation:** NAS100 stays in **shadow mode** (log-only) behind candidate regime filters; promote to live only after 30-60 days of shadow data showing the filter correctly discriminates regimes retrospectively.

γ's XAUUSD "continue live" recommendation is fine if the chairman accepts the scope-limitation caveat from §2.4 and §6.

γ's EURUSD "do not enable" is unambiguously correct.

---

## 8. Things γ should have done but didn't

1. **Cite δ's bootstrap (delta §6 P=0.7525) in §5.2** to close the "decay-lives-in-an-era" loop.
2. **Acknowledge the 12× CAND-rate discrepancy** between T7 sim and old debate pipeline — or at least disclose that γ's sample is from a specific pipeline version.
3. **Analyze the `bias=null` NO_TRADE bucket and parse-failed bucket** (632+302 records) even if just to show they have baseline WR. γ's NO_TRADE claim leaves these as coverage gaps.
4. **Run a Cochran-Armitage monotone-trend test on the NAS100 monthly BL data** instead of (or in addition to) the Fisher exact Jan-Feb vs Mar-Apr. Trend tests don't require post-hoc cutpoint selection.
5. **Re-check the Fisher p for BL decay** — γ's 2.2e-5 doesn't match my recomputation of 2.35e-6 from their own reported contingencies. Probably a copy-paste typo, but worth verifying.
6. **Explicitly mark which CLAUDE.md unresolved items this census addresses.** γ addresses #4 (T2.9 sl_beyond_ob — CONFIRMED safely blocked per γ §3.2-3.4), #5 (T2.prompt — not directly but consistent with delta §7), #6 (rolling restart — unrelated), #7/#8 (EURUSD FX precision — CONFIRMED, see §3.5 of γ).

---

## 9. Things γ got right that should be highlighted

1. **Degeneracy-aware aggregation** (script line 54-64). EURUSD's 60% FX-precision artefact records would have massively skewed γ's aggregates; excluding them is correct and propagates to γ's conservative EURUSD conclusions.

2. **Honest per-instrument epsilon** (script line 40-43). γ imports `EPSILON_BY_SYMBOL` from `simulate_t7_live_period.py`, matching session 35 Tier A1/A2/A3 conventions. This avoids the `_FILL_EPSILON = 0.05` cross-instrument mis-scale (CLAUDE.md unresolved #8).

3. **Conservative TP+SL tiebreak** (script line 166-175). γ explicitly chooses the scoring convention that tilts against their own null claim, then documents it in §8 caveats. Evidence-strength defensible.

4. **Correctly kills the session 33 "NAS100 +13.5R / +20.50R sl_beyond_ob" claim.** γ's binom p=0.46 for the bucket corrects a synthesis-level over-statement. This is a material methodological contribution.

5. **Identifies the single Bonferroni-survivor** (NAS100 BL monthly decay, p=2.2e-5 / actual 2.35e-6 vs 96-test threshold 5.2e-4). One strong finding out of 12+ tests is a clean, honest result pattern.

6. **NO_TRADE hypo-WR numbers exactly match η's** under different methodology. This is genuine replication, not just cross-citation.

7. **Tuesday-specific framing of Go/No-Go decisions** tied to each bucket. Clear action-orientation.

---

## 10. Statistical-rigor summary (for chairman)

| Lens | γ performance |
|---|---|
| Multiple-testing correction | **Good.** 96-test floor, documented at §1.5. |
| Sample power disclosure | **Mixed.** n<20 tagged exploratory throughout; but "quarterly decay does not reproduce" over-states a null built on n=10. |
| Post-hoc partition awareness | **Partial.** Partition at Feb-Mar boundary is post-hoc selected on visual inspection; γ doesn't apply partition-choice correction. At the aggregate BL level, survives anyway (p=2.35e-6 × 3 = 7e-6). |
| Schema-verification of claims | **Excellent.** Claims about batch-KB schema (no L2 fields) are directly verifiable; I verified. |
| Alternative-explanation engagement | **Partial.** Engages "decay-in-pre-L2-era" and "regime-shift-not-decay." Misses "decay-is-selection-artefact" (δ's point). Misses "AI-rejection-bias-hides-decay" (coverage gap on bias=null + parse-failed). |
| Reproducibility | **Excellent.** 5/5. |
| Cross-agent consistency | **Good.** Independent η replication on NO_TRADE. Should have cited δ more. |
| Framing of findings as decisions | **Good but premature.** Tuesday NAS100 "go only with regime gate" prescriptive when the gate is untested. |

---

## 11. Recommendation for chairman synthesis

### 11.1 What to lock in from γ as Bonferroni-safe

- **NO_TRADE missed-winner hypothesis FALSIFIED** (γ + η joint). Full agreement, well-powered null. Chairman should highlight as the audit's most robust finding.
- **NAS100 BL regime-shift Jan-Feb vs Mar-Apr** (Fisher p=2.35e-6 after correct recomputation, survives 96-test × 3-partition Bonferroni). One hard quantitative signal.

### 11.2 What to downgrade from γ to "directional"

- NAS100 `sl_beyond_ob` bucket (+19R but p=0.46; all March; correctly downgraded by γ already).
- NAS100 `max_kz_trades` bucket (+31.6R but p=0.049 raw, fails Bonferroni after partition correction).
- NAS100 CAND decay (Fisher p=0.061, marginal).
- XAUUSD "2026 decay doesn't reproduce" — under-powered null; should be framed "we cannot detect decay in this sample, and δ's orthogonal bootstrap suggests the canonical sequence is selection artefact anyway."

### 11.3 What to add to chairman's list

- **The 12× T7-vs-live CAND-rate discrepancy** (§6 of this review). Chairman should note that γ's XAUUSD L2 calibration claim is about the NEW pipeline, not the pipeline that produced the canonical 73-59 decay. These are different systems.
- **The coverage gap at `bias=null` + parse-failed NO_TRADE buckets** (932 of 1034 XAUUSD NO_TRADE records not evaluable). Does not overturn γ's null, but should be flagged.
- **The BL Fisher p recomputation** (γ reports 2.2e-5; actual 2.35e-6). Does not change conclusion, but chairman should use the correct number.

### 11.4 Tuesday go/no-go refinement

- **XAUUSD: GO.** γ's gate-calibration claim is defensible on the current pipeline. Sample limitations do not weigh heavily against caution because the current pipeline is what will trade.
- **NAS100: SHADOW ONLY.** γ's "go only with regime gate" is prescriptive; the regime gate is not yet specified or tested. Correct action is to log but not trade, with regime-filter hypothesis in shadow for 30-60 days.
- **EURUSD: DO NOT ENABLE.** γ + CLAUDE.md unresolved #7/#8 agree. Blocker until FX precision prompt fix + post-AI validator.
- **USDJPY / GBPJPY / GBPUSD: UNAFFECTED BY γ'S SCOPE.** γ did not analyze. Decisions on those instruments should come from α/β/δ/η/ζ syntheses.

---

## 12. Summary paragraph for chairman (single-paragraph handoff)

γ's census is a **methodologically clean, bonferroni-serious, independently-replicated** (by η) refutation of the missed-winner hypothesis at the NO_TRADE gate across three instruments. The NAS100 regime-shift claim survives strict correction at the BL aggregate level (Fisher p=2.35e-6 recomputed vs γ's reported 2.2e-5) but does NOT survive at the individual-bucket level (max_kz_trades p=2.8e-4 × 3-partition correction = 8.5e-4, fails Bonferroni). γ correctly de-risks the session-33 "+19R NAS100 sl_beyond_ob" claim to individually-non-significant, which should inform the T2.9 block status. γ's "XAUUSD L2 pipeline is gate-correct" claim is valid for the current pipeline but **does not validate against the decay evidence from the older debate-pipeline** — there is a 12× CAND-rate discrepancy between γ's T7-sim dataset (10 CAND) and δ's live session KB (48 CAND) that neither agent flags, and which limits γ's n for the no-decay claim. Triangulating γ with δ, the canonical 73.2→71.4→63.6→59.4 decay sequence is most plausibly a **post-hoc-selected 4-term window on a stationary or weakly-regime-conditional process**, not a reproducible signal. Tuesday recommendations: XAUUSD GO on current pipeline (acknowledging scope limit), NAS100 SHADOW-ONLY pending a tested regime gate (γ's "go with regime gate" is premature prescriptive), EURUSD DO NOT ENABLE (γ + CLAUDE.md #7/#8 agree). Reviewer confidence in γ's core findings: **80-85% on NO_TRADE null, 85% on NAS100 BL aggregate regime shift, 70% on XAUUSD no-decay (scope-limited), 90% on EURUSD blocker.**

---

*End of γ review. Reviewer: Claude Code Opus 4.7 Phase 2. File: `research/b_deep_audit_2026-04-19/phase2/gamma_review.md`.*
