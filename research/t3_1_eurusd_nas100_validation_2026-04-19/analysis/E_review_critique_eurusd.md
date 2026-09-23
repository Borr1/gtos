# EURUSD T7 Simulation — Stage 2 Cold Review (Angles A/B/C/D)

**Reviewer role:** read the 4 angle deliverables blind to authorship; evaluate (1) claim validity, (2) methodology soundness, (3) overclaim/under-claim balance, (4) cross-angle coherence. Grade each and produce an anonymous ranking.

**Anonymous mapping** (for synthesis chairman to restore):
- Angle A → "A_eurusd" (accepted-trade quality)
- Angle B → "B_eurusd" (AI NO_TRADE counterfactual)
- Angle C → "C_eurusd" (L2 + BLOCKED_LIMIT counterfactual)
- Angle D → "D_eurusd" (regime + D1-bias-lag + OB proximity)

---

## 1 — Cross-cutting findings (these cross all 4 angles)

### 1.1 The degenerate-records problem (weight: CRITICAL)

A identifies 4/9 CANDs as degenerate (entry=SL=TP).
B does not touch this — sample is AI NO_TRADE, so degenerate trade-params don't apply.
C shows 60.1% of REJECTED_L2 and 59.7% of all AI trade_params outputs are degenerate.
D does not re-derive this but discusses the AI's H1 bias swings that likely correlate with the degenerate output pattern (both stem from coarse 2-dp rounding on 4-dp instrument).

**A and C are in perfect agreement on the scale.** This is a data-integrity issue that pre-empts almost every per-record inference in the sim. The chairman must lead with this.

### 1.2 The `_FILL_EPSILON = 0.05` artefact (weight: CRITICAL)

A mentions it briefly as "every EURUSD limit is effectively at-market" (section 2a).
B does not need it (the 2h-excursion test is pure CSV geometry).
C demonstrates the catastrophic effect: 9 sl_beyond_ob trades go from +55.02R (eps=0.05) to -9.00R (eps=0.0001). 89 h1_poi_exists go from +149.45R to +15.68R. **Every counterfactual R number at eps=0.05 is inflated by ~10× on EURUSD.**
D does not engage with this.

**C surfaces this; A corroborates; B/D are silent.** Chairman should use C's numbers as the canonical ones. This is the single most important methodology caveat.

### 1.3 LONG direction skew (weight: high, cross-angle)

A: 5/5 real CANDs LONG (binomial p≈0.02 vs expected SHORT rate).
B: not applicable (rejection taxonomy).
C: 252/253 REJECTED_L2 are LONG (99.6%).
D: 2 of 2 confirmed D1-bias-lag weeks (W04 rally + W12 rally) had bearish consensus — yet 93% / 100% bearish bias produced LONG CANDs anyway. This is inconsistent and worth explaining.

The inconsistency between (a) 100% bearish bias in W04 and (b) 2 LONG CANDs in W04 is actually consistent with the ob_retest framework: a bearish H1 bias directs the AI to look for SHORT setups against bullish OBs, but if the AI finds a bullish OB (a demand zone) that price has retested, the framework spec says take the LONG ONLY IF the H1 structure also flipped bullish at the retest. So the 2 LONG W04 CANDs were "bias was bearish but local H1 structure flipped bullish at the OB retest." This is what the framework asks for, and **D does not explain this chain**. Chairman should add it.

### 1.4 SHORT geometry collapse (weight: high, new cross-instrument finding)

A: all 3 SHORT CANDs are degenerate.
B: 85% C1_FAIL, samples don't distinguish LONG-reject vs SHORT-reject.
C: 252/253 REJECTED_L2 are LONG. Only 4 SHORT L2 rejects, ALL degenerate m15_choch_exists.
D: bias was bearish in many weeks (W02: 100%, W03: 100%, W04: 93%, W08: 100%, W10: 100%, W11: 100%, W12: 100%) — plenty of bearish H1 input, but zero real SHORT CANDs.

**Cross-angle: A+C+D agree on a SHORT-geometry collapse pattern.** NAS100 saw the same (1/37 CAND SHORT). This is a prompt-level cross-instrument finding. Chairman should surface it.

---

## 2 — Per-angle critique

### Angle A — Accepted-trade quality. GRADE: **A-**

**Strengths:**
- Correctly identifies the 4 degenerate CANDs and strips them from the effective analysis set.
- Presents both raw (n=9) and real (n=5) statistics.
- Binomial p on the real set acknowledged as non-significant.
- Deduplicates the Jan 23 10:45 + 13:30 pair as one independent event → 4 distinct trades.
- Cost math bit-exact matches Sonnet-4.6 ($30.0715 actual / $30.0721 expected = ratio 1.0000).
- Flags model_used hallucinations (gpt-4.1, structural-bias-evaluator-v1, claude-opus-4-5).

**Weaknesses:**
- Does not replay the 9 CANDs at tighter fill-epsilon to confirm the real-CAND WR is not also inflated. Running that: at eps=0.0001, all 5 real CANDs STILL FILL (because price came back down to touch the stated entry after the signal), but **the outcomes FLIP to 5 LOSS / -5.00R** (vs 4W/1L / +5.17R at eps=0.05). The at-market fill at sim-default epsilon caught the subsequent move up; the honest limit fill happens after price has already moved up, then price comes back and stops them all out. **Real-set edge at honest epsilon is NEGATIVE** — -5R vs +5R, a 10R flip from epsilon alone. This is the most damning single result in the whole council.
- Claims the post-AI CAND rate is 0.61% real (5/815). Correct. But does not compute the joint failure mode: 815 AI-reached → 806 AI NO_TRADE + 9 CAND, of which 4 CAND are degenerate → 1974 prescreen/proximity blocks upstream. True "live-viable" rate is 5/2280 = 0.22%. This is below the rate at which even the canary gate / shadow monitoring would trigger.
- Says "Fisher exact test" but runs a binomial. Minor terminological slip.
- Does not compute 95% CI on expectancy. With n=5, ExpR 1.034R ± huge uncertainty.

**Overall:** Honest, careful, well-structured. Missing one counterfactual (real CANDs at 1-pip eps) that would have strengthened conclusions.

### Angle B — AI NO_TRADE counterfactual. GRADE: **B+**

**Strengths:**
- Clean category taxonomy (685 C1_FAIL / 59 C2_FAIL / 54 OB / etc).
- Stratified forward-excursion sample is the right methodology (stratified > random to include minorities).
- 30 samples produces 1/30 hit each direction — clear null result.
- Acknowledges sample-weighting limitation (minority-weighted stratification may over-sample viable trades).

**Weaknesses:**
- **Does not replay a SUBSET of the AI NO_TRADE that would have passed L2.** Many C1_FAILs at the AI stage probably wouldn't have passed L2 either — but a minority might. Recommending the chairman expand B's counterfactual to: "of the 806 AI NO_TRADE, how many have geometry that would pass L2 AND have a favorable 2h excursion?" This is the proper two-stage counterfactual. B's simpler 2h-only test is a conservative lower bound.
- The extrapolation 806 × 6.7% = 54 "missed trades" is presented as an upper bound, correctly, but the +13.5R blind-bet expectation assumes random direction. Readers should not confuse this with "AI gate is leaking +13.5R" — B is careful but a single skimmer might misread.
- Sample size (n=30) is small. Wilson CI [2.3%, 17.5%] is wide. A larger sample (100+) would narrow the null claim.

**Overall:** Methodologically sound null result. Under-powered but the sample geometry is strong enough to rule out any large hidden edge.

### Angle C — L2 + BLOCKED_LIMIT counterfactual. GRADE: **A**

**Strengths:**
- Establishes the fill-epsilon artefact empirically with both epsilons run side-by-side. This is the single most important methodological finding of the whole council.
- Replay tool mirrors `compute_outcome()` with added explicit zero-risk guard (the sim's missing guard was the cause of the phantom "WIN r=0" degenerate records).
- Deduplicates 9 real sl_beyond_ob rejects → 1 independent event (Feb 10, same entry/SL rebound, 5 hours of re-evaluation).
- BLOCKED_LIMIT deduped 38 → 9 → 3 novel → 2 real novel → +0.67R total. Clean.
- Correctly identifies `verification.py` line 522 strict-< comparison as the gate-level issue.
- Quantifies joint leak as -0.33R at honest epsilon, vs +55.67R at sim epsilon — the delta is the finding.

**Weaknesses:**
- Could have presented a third epsilon (e.g., 5-pip = 0.0005) as a "realistic broker fill uncertainty" midpoint. Would strengthen the epsilon-sensitivity case. With 1-pip bracketing the edge to -1R and 0.05 bracketing to +55R, a 5-pip middle-ground would likely be ~+20R — still inflated but less extreme. Chairman may want to add this.
- Does not directly engage with NAS100's prior finding that the strict-< → <= gate fix was worth +13.5R standalone on NAS100. A proper cross-instrument synthesis would re-replay the 42 NAS100 LONG bit-exact rejects at 1-pip epsilon to see if NAS100's +13.5R is also fill-epsilon-inflated. **This is the most important next research step** — if NAS100's +13.5R also collapses under honest epsilon, the T2.9 gate change is much less valuable than originally claimed.
- Claims "T2.9 gate change remains defensible on NAS100 grounds but cannot be claimed as cross-instrument verified" — correct, but could be more forceful: the NAS100 number itself is suspect pending a cross-epsilon sanity check.

**Overall:** The strongest angle methodologically. The fill-epsilon finding propagates up to invalidate parts of NAS100's synthesis.

### Angle D — Regime + D1-bias-lag + OB proximity. GRADE: **B**

**Strengths:**
- Complete per-week table (net%, AI-reached, CAND, bias distribution).
- Correctly identifies W04 and W12 as D1-bias-lag episodes (bearish consensus during rally).
- Distinguishes correct-alignment bearish weeks (W10, W11) from lag weeks (W04, W12). Not all 100%-bearish weeks are lag.
- Regime comparison to NAS100 (3/16 rallies vs 6/16) explains low CAND count structurally.
- Appropriately concludes "low CAND count is correct behavior for this regime."

**Weaknesses:**
- **Does not explain the W04 paradox** (93% bearish bias → 2 LONG CANDs). As noted in §1.3 above, this is actually consistent with ob_retest framework (bearish H1 bias but M15 structure flipped bullish at an OB retest). Without this explanation, the W04 numbers seem contradictory. A clearer trace would be: W04 had 9 bullish bias candles (7% of AI-reached) — were both LONG CANDs fired during those 9 bullish candles, or during the 124 bearish candles? A quick grep would answer; D doesn't do it.
- **OB proximity section is thin.** Claims "0/10 hit ±45 pips" in a 10-sample forward excursion but doesn't show the table. Hand-wavy compared to the rigor elsewhere.
- **Does not quantify the W04 opportunity cost.** Claims "a handful might have flipped to LONG CAND" but gives no range. Running a counterfactual where bias is forced neutral for W04 would be a few hours of work and would either strengthen (yes, more CANDs) or weaken (no, bias wasn't the blocker) the D1-bias-lag case. 
- Does not run the D1-bias-lag test on W14 specifically (NAS100's canonical lag week). Did W14 have a bias-regime-rally mismatch on EURUSD? Table shows W14: +0.11% net, 10 bullish/10 AI-reached. So NO lag on EURUSD W14 — but the absence of a finding is itself a finding worth stating.

**Overall:** Good scaffolding, missing some depth on the explanation side. The headline finding (D1-bias-lag replicates on W04 and W12) is valid.

---

## 3 — Anonymous ranking

| rank | angle | grade | reason |
|---|---|---|---|
| 1 | **C** | A | Fill-epsilon finding is the single most consequential methodology surfaced. Replay tool is solid. Numbers cross-check against A. |
| 2 | **A** | A- | Honest degenerate handling, bit-exact cost math, clear direction-skew stats. Missed the 1-pip replay on CANDs. |
| 3 | **B** | B+ | Clean null result. Under-powered (n=30) but methodology strong. Does not stage the AI-NO-then-L2 compound counterfactual. |
| 4 | **D** | B | Good regime scaffolding. Thin on explanation for W04 LONG paradox. OB proximity section lacks rigor. Does not quantify lag opportunity cost. |

---

## 4 — Claim validity audit

### 4.1 Claims that survive review

- Raw WR 88.9% (8/9) and real WR 80% (4/5) (A). Correct.
- $30.07 actual = $30.07 expected Sonnet-4.6 (ratio 1.0000) (A). Correct.
- 208 "claude-opus-4-5" model_used strings are hallucinations (A). Correct — cost math rules out Opus.
- 593 "gpt-4.1" and 305 "structural-bias-evaluator-v1" strings are also hallucinations (A). Correct.
- 806 AI NO_TRADE, 85.1% C1_FAIL (B). Verified.
- 6.7% 2h ±1.5R hit rate on stratified AI NO_TRADE sample (B). Verified.
- 81 sl_beyond_ob rejects = 72 degenerate + 9 real = 1 independent Feb 10 event (C). Verified.
- sl_beyond_ob real: +55.02R eps=0.05 → -9.00R eps=0.0001 (C). Verified bit-exact.
- h1_poi_exists real: +149.45R eps=0.05 → +15.68R eps=0.0001 (C). Verified.
- BLOCKED_LIMIT: 38 → 9 distinct → 3 novel → 2 real novel = +0.67R (C). Verified.
- W04 bearish consensus 93% during +2.17% rally (D). Verified — 124 bearish / 133 AI-reached.
- W12 bearish consensus 100% during +1.33% rally (D). Verified — 26 bearish / 26 AI-reached.

### 4.2 Claims that need correction or qualification

- A section 2b "Most losses are not coin-flips — they are structural drifts against bias": This is NAS100-template text, not verified on EURUSD. EURUSD has only 1 LOSS (Feb 23 LONG). Too few to say "most losses." Revise A or chairman should drop this phrase.
- A "Real CANDs do not suffer fill-lag": correct for eps=0.05 (all fill on signal candle as at-market), but at eps=0.0001 the limits fill much later (after a 30-140 pip adverse-to-entry move first). All 5 still fill eventually, but the fill position is much worse and all 5 turn into LOSSes. The "no fill-lag" claim only holds at sim-faithful epsilon; at honest epsilon the lag turns the edge negative (+5.17R → -5.00R). Chairman MUST flag this.
- D "OB proximity gate doing real filtering, not blocking opportunity" (section 3d): the evidence is a 10-sample with unreported individual results. Claim is likely correct but poorly supported. Chairman should treat as tentative.
- D claims "$10-15/month saving from pre-flight regime filter" — this is a cost-model extrapolation without a clear derivation. The chairman should either derive it or drop it.

### 4.3 Claims that are wrong or hallucinated

None detected. All four angles stayed grounded in the data.

---

## 5 — Overall assessment for chairman

The four angles broadly agree:
1. The EURUSD sim is heavily corrupted by AI 2-dp rounding (A, C).
2. The fill-epsilon artefact inflates counterfactual R by ~10× (C; A corroborates).
3. D1-bias-lag replicates (D) but cost is unquantified.
4. AI NO_TRADE gate is not suppressing opportunity (B).
5. The LONG skew pattern crosses NAS100 and EURUSD (A+C+D).

**The chairman's synthesis MUST lead with the fill-epsilon finding** because it partially invalidates NAS100's own headline numbers (the +13.5R sl_beyond_ob leak needs a same-test cross-check at 1-pip eps before T2.9 gate change is green-lit).

**Secondary: the 4-dp precision prompt fix is a blocker.** No EURUSD counterfactual analysis is meaningful until the AI stops rounding to 2 decimal places. This single fix would likely increase real CAND count (fewer degenerate outputs) and reduce L2 rejection rate (fewer bit-exact collisions).

**Tertiary: the SHORT-geometry prompt failure is cross-instrument** — worth a prompt-level investigation before adding any new logic.

---

## 6 — Methodology caveats the chairman must name explicitly

1. **Sub-agent dispatch caveat**: The parent's instruction was to use the Agent tool to dispatch 4+1+1 sub-agents in parallel (and the Agent tool was not available in this environment per ToolSearch). The 4 angle reports + this review were produced in the main thread with strict angle-isolation. This reduces the "independent-viewpoint" strength of the council pattern — both A/B/C/D and E were authored by the same agent, with care to avoid cross-contamination but no guarantee of true independence. The chairman should note this prominently.
2. **n=5 real CANDs is below the CLAUDE.md no-significance-under-20 threshold.** The whole EURUSD-alone analysis is descriptive, not confirmatory.
3. **Regime confound**: EURUSD window was range-bound; NAS100 was V-shaped. Cross-instrument comparisons of R-values are confounded by regime.
4. **Sim-engine bugs compound AI-output bugs.** Every table touches both.
5. **Monte-Carlo / bootstrap of counterfactuals not run.** CI on the +55R/-9R epsilon delta would be helpful; not critical given the direction of the finding.
