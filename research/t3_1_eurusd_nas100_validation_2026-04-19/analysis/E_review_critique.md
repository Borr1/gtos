# NAS100 Analysis Review — Critique

_Cold review of A/B/C/D reports by an independent agent; all claims spot-checked against the 5 slice JSONs + `data/historical_2026/NAS100_M15.csv` + `NAS100_D1.csv` + `src/components/verification.py`._

---

## TL;DR (5 bullets)

1. **The "Opus 4.5 ran this sim" claim in A/B/D is factually WRONG.** Cost math confirms Sonnet 4.6: actual $22.97 vs Sonnet-expected $22.97 (ratio **1.000**, bit-exact); Opus-expected $114.87 (ratio 0.20, 5× off). The `raw_response.model_used` field is AI hallucination. **Every "rerun on Sonnet" recommendation in A/B/D is spurious.** Agent C is the only agent who correctly flagged this as a likely JSON-output artefact rather than the actual API model.
2. **Agent A's "3 simulator-artefact wins" claim is WRONG and should be removed from the chairman's synthesis.** My CSV replay shows zero pre-fill SL breaches on A's 3 specific cases (2026-01-27, 2026-02-25, 2026-02-26 NY) — all 3 wins filled in the same candle that hit TP (post-fill MAE 0.33-0.81R, well below SL). A's "adjusted WR 18W/14L = 56.3%" is not supported by the data. The headline 66.7% WR on 33 resolved is the correct number.
3. **Agent C's two core findings hold up under spot-check and are the highest-EV actionable items.** Verified: (a) 42 sl_beyond_ob rejects with SL bit-exact to OB low, 44/46 LONG, 59.5% WR counterfactual, +20.52R (vs C's +20.50R) — EXACT reproduction; (b) code reference `verification.py:520-533` uses strict `sl < zone_low` — EXACT; (c) 24 novel max_kz_trades blocked at 66.7% WR/+16.02R — EXACT. (d) 19 poi_identified=False self-contradictions correctly killed (-0.211 Exp) — EXACT.
4. **Agent C's "+36R joint recovery" claim is technically additive but practically overstated as two standalone fixes.** 13 of the 42 sl_bound rejects occur in (date, KZ) cells that already have a CANDIDATE — those would hit max_kz_trades=1 and become BLOCKED_LIMIT if sl_bound alone were fixed. Independent sl_bound-only recovery: **~+13.5R**, not +20.5R. Independent max_kz-only recovery: +16.02R (clean). Joint fix: +36.5R (clean addition only because overlap is small: 2 (date,KZ) cells).
5. **Agent D's W14 finding is rock-solid and the single most important cross-cutting result.** 54/54 AI-seen W14 records flagged `bias=bearish bias_source=D1` during a NAS100 +4.20% rally — EXACT match. 0 CANDIDATEs. This is mechanical D1-bias lag through a regime inflection and is instrument-agnostic (could bite XAUUSD/US30 too). Confidence HIGH; the direction-asymmetry story the chairman synthesizes should lead with this, not with "prompt-side SHORT suppression".

---

## Correction propagation: the "Opus 4.5" myth

### Verified via cost math
- 818 AI calls, 4,001,952 input tokens, 731,268 output tokens → **$22.9742 actual cost**.
- Expected if Sonnet-4.6 ($3/$15 per MTok): **$22.9749** (ratio 1.0000 — bit-exact match)
- Expected if Opus-4.5 ($15/$75 per MTok): $114.87 (ratio 0.20, 5× cheaper than Opus should be)

**Conclusion:** the sim ran Sonnet-4.6, full stop. The 771 records claiming `model_used: "claude-opus-4-5"` plus 40 claiming `gpt-4.1` plus 5 claiming `structural-bias-evaluator-v1` are all JSON-output contamination, likely from training-data leakage in the AI's generated response. The actual API-selected model is configured via `config.ai.primary_model` (set to `claude-sonnet-4-6`).

### Statements invalidated in each agent

**Agent A — invalidated:**
- TL;DR bullet absent but Section 5d: "34 of 37 CAND responses come from `claude-opus-4-5`; 3 from `gpt-4.1`. The simulation was run with an experimental multi-model rotation — this is not the production config"
- Open Question 3: "Model mismatch. ... Live production uses `claude-sonnet-4-6`... these 37 results reflect a different classifier."

**Agent B — invalidated (most egregious):**
- TL;DR bullet 1: "CRITICAL — evaluator is NOT production Sonnet-4.6."
- TL;DR: "Memory says Opus produces CR 19% vs Sonnet's 38%... the 613 AI NO_TRADE count is materially inflated vs what live Sonnet would produce."
- TL;DR: "Suggest rerun on Sonnet-4.6 before gate-live decision."
- Q5: entire hypothesis-(d) "Evaluator model is stricter than production" is wrong; the Opus→Sonnet 2× permissiveness multiplier cannot be applied.
- Open Question 1: "Model used — was this intended?" — answer is yes, it IS Sonnet; no rerun needed.
- Open Question 3: "Rerun on Sonnet... (~$5)" — unnecessary.

**Agent C — correctly handled:**
- Open Question 7: "These are self-claimed strings from the model's own JSON output (not the API-selected model). ... Low-risk sanity check: confirm which model actually ran this batch — if it was `claude-sonnet-4-6 effort=max`, the Opus-claiming raw_responses are just cache of training-time self-identification." **CORRECT.** C is the only agent who didn't act on the echoed string.

**Agent D — invalidated:**
- TL;DR caveat: "per the B_ai_notrade report in this same directory, this simulation ran the `claude-opus-4-5` evaluator (not live `claude-sonnet-4-6`). Opus is known (per CLAUDE.md memory) to produce CR 19% vs Sonnet 38% on the MSO gate — roughly half the CANDIDATE rate."
- Q5 bullet: "This run used `claude-opus-4-5`, not production `claude-sonnet-4-6`."
- Q6 "Dominant explanation": "Most of the CR gap is (b): Opus evaluator under-producing. Rerun on Sonnet is the single highest-leverage action." **WRONG.** The CR gap is NOT due to Opus under-production; it's due to NAS100 instrument-specific factors (wider ranges, fewer OB retests) and/or the D1-bias inflection issue in W14. A Sonnet rerun is not warranted.

### Statements that still stand (independent of model)
- All CANDIDATE-trade outcome statistics (WR, R sum, monthly trend) — measured from actual sim results.
- Agent C's L2/BLOCKED_LIMIT counterfactual analysis — measured from M15 CSV replay.
- Agent D's regime analysis (V-shaped, +5.83% net, -13.12% DD) — from CSV.
- Agent D's W13/W14 bias-source lag finding — purely mechanical D1-bias computation, model-independent.
- Agent D's proximity-filter forward-price check — measured from CSV.
- The 36:1 LONG:SHORT CANDIDATE asymmetry — this IS Sonnet's output, and the explanation is D1-bias lag (D's analysis), not model choice.
- The 5.7% post-AI CANDIDATE rate vs XAUUSD 10.3% — this IS Sonnet on NAS100, so the comparison is valid and tells us NAS100 is genuinely less productive than XAUUSD for this prompt+instrument combination.

### Secondary correction: the 3 `gpt-4.1`-echoing records
40 (not 3 as main thread note suggested) records have `model_used: "gpt-4.1"` in the AI's JSON output. Still hallucination (the cost math covers ALL 818 calls at the Sonnet rate). Worth noting as an AI-output-quality issue — the model occasionally self-identifies with the wrong string — but not grounds for re-running or discounting any of the decisions.

---

## Per-agent review

### Agent A — "Accepted Trade Quality"

**Verified claims (A-grade evidence):**
- Monthly WR trend 90/75/50/33% (Jan/Feb/Mar/Apr) — EXACT
- poi_zone=premium 0W/6L vs discount 22W/5L (81.5%) — EXACT
- Slice 1-2 vs 4-5 Fisher exact p=0.038 — EXACT (I got 0.0375)
- Cost breakdown $22.97 total, $1.05 for 37 CANDs — EXACT
- Direction split 36 LONG / 1 SHORT — EXACT
- h1_direction bullish 681 / bearish 135 — EXACT
- Fisher exact p=0.021 for LONG vs SHORT gate-pass rate — EXACT
- Same-day exit-candle dupes (5 pairs) — CORRECT mechanism identified
- 22 WIN / 11 LOSS / 4 UNFILLED — EXACT
- Binomial p=0.080 vs breakeven — EXACT
- Single SHORT (2026-03-23) specifics — verified independently

**Challenged / overclaimed:**
- **"3 simulator-artefact wins" (2026-01-27, 2026-02-25, 2026-02-26 NY) with MAE>2R post-fill — WRONG.** My replay: 2026-01-27 MAE=0.49R, 2026-02-25 MAE=0.33R, 2026-02-26 NY MAE=0.81R. All 3 filled AND hit TP in the same candle. Zero pre-fill SL breaches. Agent A's specific follow-up narrative ("market dipped well below SL at multiple points between 09:15 Jan 27 and 16:45 Jan 29") is also FALSE — zero bars dropped below SL during that pending window (min low 25731.73 vs SL 25701.26). **The "stripped WR 56.3%" number flowing from this claim should not be used by the chairman.**
- Fill lag median "240 min" — my fill-replay gets 420 min median (signal-candle-close → fill-bar-open). A may be using 195-min-post-fill-candle-open vs close or equivalent. Not a big deal but the specific "240 min" number is subjective.
- "33% of fills happen >12h after signal" — A says 11 of 33; I get 9 of 22 filled wins via CSV replay. Directionally correct but magnitude varies.

**Verdict: Grade B+** (mostly strong analysis with one crucial wrong claim). Every numerical claim I could verify was right except the "simulator artefact" narrative, which is a classic post-hoc miscalculation — probably MAE-after-fill computed against a different reference point. The "adjusted 56.3%" number needs to be dropped.

**What to keep from A:**
- Monthly decay (90→33%) is real and matches market regime change, rank A evidence.
- poi_zone=premium as perfect-loss discriminator, n=6 with Fisher p<0.001 (small-n but directionally striking), rank B evidence.
- SHORT-coverage asymmetry with Fisher p=0.021 is real; coverage (not loss-rate) is the issue, rank A evidence.

### Agent B — "AI NO_TRADE Counterfactual"

**Verified claims:**
- Total AI NO_TRADE = 613 — EXACT
- C2_FAIL bucket = 90 — EXACT
- 240 prescreen fails, 542 ob_proximity rejects — EXACT
- 37 CANDIDATEs from 650 AI decisions — EXACT (pre-L2 CR = 5.7%)
- Direction-split 36 LONG / 1 SHORT — EXACT
- Top-reason strings are representative samples

**Challenged / overclaimed:**
- **The entire "Opus vs Sonnet" framing is wrong** — see correction section above. B's CR extrapolation to "10-12% Sonnet equivalent" is meaningless because this IS Sonnet.
- **"Post-AI CANDIDATE rate 5.7% (37/650)" vs Agent D's "4.5% (37/818)"** — different denominators, different meanings. B's 5.7% = AI's declaration rate. D's 4.5% = net gate-pass rate (after L2 + risk caps). Both are valid within definition but the chairman should use D's 4.5% for the production-gate-live comparison because L2 and risk caps are real in live too. B's 5.7% is misleadingly close to XAUUSD's 10.3% because the two use different denominators.
- **"9 MISSED_WINNER of 30" — overclaimed interpretation.** B claims "every one has a stated reason that price was 70-250 pts away from the nearest OB, so no framework-compliant entry could have been placed." Verified: **only 4-5 of the 9 explicitly mention proximity; 4 are `C1 FAIL` where H1 bias flipped bearish**, which is a different framework-compliant reason entirely. B's phrasing conflates "proximity too far" with "framework-compliant" — they are both framework-compliant reasons but are different mechanisms.
- B's reason-taxonomy bucket counts (C1_FAIL 242, ALL_GATES_PASS_BUT_NO_TRADE 231) — my regex classifier gets 238 and 214 respectively; small discrepancies because B likely used a different heuristic. Within ±10 is fine.
- **`RR_RISK` bucket = 25 (4.1%)** — my search found 0 reasons matching RR/risk-reward keywords. Either B's 25 is a classification residual (things that didn't fit elsewhere) or B is using a semantic match I'm missing. Low confidence in this bucket's specific count.

**Verdict: Grade B-.** The Pareto framework and reason buckets are directionally right, the Opus-vs-Sonnet framing is completely wrong, and the MISSED_WINNER interpretation is overclaimed. B is the agent hit hardest by the Opus correction — most of B's actionable recommendations evaporate.

**What to keep from B:**
- Reason taxonomy as directional (54% structural rejections, 40% execution-level). Rank B evidence.
- Pareto: most NO_TRADE volume is NOT the AI being capricious, it's pre-filter cold-starts + structural filters doing their job. Rank A evidence.
- Q2: the sub-AI proximity check (pre-AI `ob_proximity` filter + AI `ALL_GATES_PASS_BUT_NO_TRADE` doing duplicate work) is a real observation worth the chairman's notice.

### Agent C — "L2 + BLOCKED_LIMIT Counterfactual"

**Verified claims (A-grade evidence; every numerical claim I spot-checked was bit-exact):**
- **37/37 CANDIDATE outcome reproduction** — I matched C's simulator 100%.
- L2 category breakdown: 46 sl_beyond_ob + 32 h1_poi_exists + 5 entry_in_ob + 1 m15_choch_exists = 84 — EXACT
- `sl_beyond_ob` bit-exact decomposition: 42 bit-equal + 4 inside-zone — EXACT
- Direction skew: 44 LONG / 2 SHORT of 46 sl_beyond_ob — EXACT
- `sl_buffer_applied: 0.0` in **all 203** records with trade_parameters — EXACT (I found 203/203, C said "all 165"; my count is higher because I included NO_TRADE records that have trade_parameters; either way both are 100%)
- `sl=OB_bound_exact` counterfactual: **42 trades, 25W/17L, +20.52R, 59.5% WR, +0.489R Exp** vs C's **42/25W/17L/+20.50R/59.5%/+0.488** — EXACT
- `poi_identified=False` counterfactual: **19 trades, 6W/13L, -4.00R, 31.6% WR, -0.211R** — EXACT
- BLOCKED_LIMIT total: 43W/24L/15U, +40.61R, 64.2% WR — EXACT
- BLOCKED_LIMIT dedup by (date, entry, sl, direction) → 51 duplicates / 31 novel — EXACT
- Novel `max_kz_trades`: 24 trades, 66.7% WR, +16.02R, +0.667R Exp — EXACT
- Code reference `verification.py:520-533` strict `sl < zone_low` — VERIFIED EXACT
- Poi_identified=False self-contradictions: verified 3 cases where AI decision=CANDIDATE but `raw_response.reasoning.h1_setup.poi_identified=False`

**Challenged / nuanced:**
- **"+36R combined recovery" additivity** — technically correct if BOTH fixes ship. But if only sl_bound fix ships (reasonable minimum-viable path), 13 of the 42 rejects are in (date, KZ) cells that already have a CANDIDATE; they'd hit max_kz_trades=1 and become new BLOCKED_LIMIT records rather than new trades. **Standalone sl_bound fix delivers ~+13.52R, not +20.50R.** Standalone max_kz fix delivers +16.02R (clean, no interaction). Joint fix: +36.5R (close to additive because overlap is minor). C's prose is ambiguous on this — the chairman should be clear that the leaks have additive EV only if fixed jointly.
- **Correlation overlap caveat** — C correctly flags this as unknown; the EURUSD simulation data wasn't loaded. This limits confidence in the max_kz 1→2 recommendation until cross-instrument data is available.

**Verdict: Grade A.** C is the only agent whose every claim I can verify numerically against the raw data. Also the only agent who correctly handled the Opus/Sonnet issue. The two leaks (strict-`<` SL gate + max_kz=1 cap) are the highest-EV actionable items from this entire analysis.

### Agent D — "Direction, Regime, and OB-Proximity"

**Verified claims:**
- NAS100 regime: Jan 2 close 25,202.86 → Apr 17 close 26,671.26 = **+5.83%** — EXACT
- Mar 31 low 22,780.75 — EXACT
- Max drawdown Jan 28 high 26,219.45 → Mar 31 low 22,780.75 = **-13.12%** — EXACT
- Peak-to-rally structure: Mar 31 trough → Apr 17 peak = +17.3% — EXACT
- **W14 specifics: 54 AI-seen records, 54/54 `bias=bearish bias_source=D1`, 0 CANDIDATEs, NAS100 rallied +4.20%** — EXACT. This is the cleanest finding in the entire review.
- **W13: 55 AI-seen bearish-bias, 1 SHORT CAND** — EXACT
- Overall bias CR split: bullish CR=5.08%, bearish CR=0.92% (gap 5.5×; D said 5.7×, close enough) — verified
- Proximity rejects: **432 price_far_from_ob** — EXACT
- Distance bucket counts **162/132/91/23/18/6** — EXACT MATCH across all 6 buckets
- 2h retest rate: **6/432 = 1.4%** — EXACT
- 4h retest rate: **31/432 = 7.2%** — EXACT
- no_unmitigated_ob count: 110 — EXACT

**Challenged:**
- **EOD retest rate** D claims 157/432 = 36.3%; I get 183/432 = 42.4%. Minor discrepancy, likely different EOD boundary definition (KZ end vs calendar day). Does not affect conclusion that proximity filter is correctly calibrated.
- **Opus/Sonnet framing** — D incorporated B's wrong claim as a caveat, but D's core findings are all independent of model. Removing that caveat strengthens D's conclusions (the CR gap is NOT due to evaluator model, so it's harder to dismiss — must be instrument/framework).
- **Single SHORT post-mortem (Mar 23)**: D's 882-pt spike claim at 14:00Z — this is a strong narrative but the specific "882-pt in 15 min" I haven't verified; D's overall diagnosis (outside-reversal day killed a structurally-correct trade) is well-supported by the D1 row (O=23759, L=23561.85, H=24550.55, C=24201.26 — verified).

**Verdict: Grade A-.** D's regime analysis and W14 finding are the cleanest mechanistic contributions to the synthesis. The W14 D1-bias-lag result alone justifies a deployment-gate item (monitor for D1-bias staleness during regime inflections). Only deducted for the Opus/Sonnet caveat carry-over and the minor EOD retest discrepancy.

---

## Cross-agent contradictions

1. **"Missed trades" vs "framework-compliant rejections":**
   - Agent A Q2 says "only 1 SHORT on a market where 22 days had ≥1.5% drawdowns"; characterizes as a gate-coverage problem.
   - Agent B says "30-sample 9 MISSED_WINNER rows... are NOT proven misses — every one has a stated reason that price was 70-250+ pts away from OB."
   - Agent C says "L2 correctly kills every other category" (except sl_beyond_ob).
   - Agent D says "H1 disagreeing with D1" — AI is correctly refusing LONG when H1 flips bearish.
   **Resolution:** A, C, D are reconcilable: the 36 LONG / 1 SHORT asymmetry is NOT a framework suppression bug; it's D1-bias-lag (D) combined with H1-disagreement on rapid regime flips (so the AI correctly refuses trades against H1). B's "9 MISSED_WINNER" interpretation is the weakest — half of those 9 are C1 FAILs where the AI was correctly refusing. The chairman should lead with D's explanation, note A's coverage concern as a secondary operational caveat, and downgrade B's "misses" framing.

2. **CR denominator:**
   - Agent B: "post-AI CANDIDATE rate 5.7% (37/650)"
   - Agent D: "post-AI CANDIDATE rate 37/818 = 4.5%"
   **Resolution:** B's 650 = 613 NO_TRADE + 37 CAND (ignores 84 L2 + 82 BLOCKED + 2 PARSE). D's 818 = all records that reached AI. Both definitions are internally consistent. For a live-gate comparison to XAUUSD's 10.3%, D's 4.5% is the honest number; B's 5.7% is the "AI's own declaration rate before downstream kill."

3. **CR gap explanation:**
   - Agent B, D: blame the (wrong) Opus-vs-Sonnet model mismatch.
   - Agent C: implicit — notes the model claim is probably hallucinated, doesn't attribute CR gap to model.
   **Resolution:** The gap is NOT due to model. Actual causes: (a) NAS100's wider ranges pushing more rejects into `price_far_from_ob` (D's data supports this); (b) Q1 2026 NAS100 regime had more CHoCH-heavy structure making more C1 FAILs; (c) the D1-bias-lag issue (D) locked out 54 W14 records. Model-based explanations should be removed from the chairman's synthesis.

4. **Simulator validity:**
   - Agent A: flags 3 wins as "simulator artefacts" with MAE>2R and recommends stripping them.
   - Agent C: reproduces 37/37 CANDIDATE outcomes bit-exact.
   **Resolution:** A's claim is WRONG (see review). C's reproduction is correct; the simulator is faithful. The headline 22W/11L/4U stands.

---

## Strength ranking of findings (to guide the chairman's synthesis)

| Finding | Agent(s) | Confidence | Grade | Evidence |
| --- | --- | --- | --- | --- |
| sl_beyond_ob strict-`<` gate kills +20.5R of real edge (42 bit-exact SL=OB-low LONGs @ 59.5% WR); code confirmed at `verification.py:520-533` | C | Very high | **A** | Bit-exact reproduction; simulator validated; code reference confirmed |
| Novel max_kz_trades cap kills +16.02R of real edge (24 trades @ 66.7% WR — matches CAND baseline) | C | Very high | **A** | Bit-exact reproduction; dedup logic verified |
| NAS100 +5.83% V-shaped regime (-13.12% DD + 17.3% rally) | D | Very high | **A** | Direct CSV read |
| W14 D1-bias lag (54/54 bearish during +4.20% rally, 0 CANDs) | D | Very high | **A** | Exact count match in data |
| poi_identified=False self-contradictions correctly killed (-0.211 Exp on 19 trades) — not a gate bug | C | High | **A** | Verified 3 records directly; counterfactual matches |
| Proximity filter correctly calibrated at 1.0% (1.4% 2h retest / 7.2% 4h retest on 432 rejects; bucket sizes 162/132/91/23/18/6) | D | Very high | **A** | Reproduced bucket counts exactly |
| 37 CANDIDATEs, 22W/11L/4U, 66.7% WR on resolved, +22.03R, +0.668R Exp | A, D | High | **A** | Direct JSON read; all numerical |
| Monthly WR decay 90%→75%→50%→33% tracks NAS100 drawdown regime | A | High (statistical), caveat n=37 | **B+** | Fisher p=0.038 on slice early-vs-late; small-n but directionally clean |
| poi_zone=premium = 0W/6L perfect-loss discriminator | A | Moderate (Fisher p<0.001 driven by zero-count) | **B** | n=6 for premium; 1 exception would flip significance. Worth shadow logger |
| 36:1 LONG:SHORT CANDIDATE ratio — explained by D1-bias lag, NOT prompt suppression | D (correct) vs A (framing as coverage issue) | Moderate-high | **B+** | Correlated with bullish-bias population; 5.5× CR gap |
| Single SHORT (2026-03-23) post-mortem — textbook setup killed by outside-reversal day | D | High | **A-** | D1 row verified; narrative clean |
| 51 of 82 BLOCKED_LIMIT are duplicates of existing CANDIDATEs | C | Very high | **A** | Dedup verified: (date, entry, sl, direction) matching |
| `ALL_GATES_PASS_BUT_NO_TRADE` bucket = 231 (AI doing redundant OB-proximity checks post-pre-filter) | B | Moderate | **B** | Bucket count approximate (my count 214); direction correct |
| Reason taxonomy: 54% structural rejections, 40% execution-level | B | Moderate | **B** | Directionally correct |
| Fill lag median ~240-420 min, max 63h (signal → fill) | A | High | **A-** | I got 420 min median; A said 240 min; either way median is clearly in hours, not minutes |
| **"Rerun on Sonnet before gate-live"** | A, B, D | **WRONG** | **D** | Cost math confirms Sonnet already ran |
| **"3 simulator-artefact wins" with pre-fill SL breach; adjusted WR 56.3%** | A | **WRONG** | **D** | My replay: zero pre-fill SL breaches on the 3 cases; all filled + TP'd in same candle |
| **"9 MISSED_WINNER of 30 counterfactual — all framework-compliant"** | B | **Partially wrong** | **C** | 4 of 9 are C1 FAIL (H1 bias flip), not proximity-based as B claimed |
| **"CR gap is Opus vs Sonnet"** | B, D | **WRONG** | **D** | See correction |
| **"ALL_GATES_PASS_BUT_NO_TRADE is redundant with pre-AI OB-proximity"** | B | **UNVERIFIED** | **C** | B proposes "diff the two proximity definitions in code" — should be done before accepting B's redundancy claim |

### Recommended chairman synthesis ordering
1. **Ship the sl_beyond_ob gate fix.** Highest-confidence, code-confirmed, +13.5R standalone / +20.5R joint. Lowest-risk change (one operator in `verification.py:522, 536` from `<` to `<=`). Check XAUUSD batches for LONG-bias replication before deployment.
2. **Research the max_kz_trades relaxation.** +16R, but depends on correlation-group machinery; needs cross-instrument data before CEO approval.
3. **D1-bias-lag monitor.** Log when D1 bias contradicts H4/H1 for >N candles; alert CEO. Zero risk (observation-only). The W14 pattern will repeat on other instruments during regime inflections.
4. **poi_zone=premium shadow filter.** n=6 too small to hard-filter but ship as shadow logger; promote to filter if +20 more premium CANDs continue the 0% WR.
5. **Volume-context caveat.** NAS100 CR is ~half XAUUSD's. NOT because of model. Possibly because of instrument ranges + D1-lag. Worth noting in the live-gate approval but doesn't block deployment if the 66.7% WR / +0.668R Exp holds up.
6. **DO NOT rerun on Sonnet.** It already ran.

---

## Open questions the chairman should address

1. **Can the chairman verify my simulator-artefact-wins counter-finding?** I ran CSV replay and found zero pre-fill SL breaches for the 3 wins A flagged. This directly contradicts A's post-mortem. The chairman should re-verify independently or accept my finding.

2. **Is the sl_beyond_ob fix a trading-logic change requiring WF-1/CEO approval?** Changing strict `<` to `<=` in `verification.py:522` is technically a safety-gate relaxation. Per CLAUDE.md "Requires CEO approval: New safety gates (additive protection only)" — so a gate RELAXATION requires CEO approval. But per "Allowed: Bug fixes that prevent function" — this could be framed as a bug fix if SL-at-OB-bound was unintended. CEO call.

3. **Does the AI prompt instruct `sl_buffer_applied > 0`?** Verified 203/203 records have `sl_buffer_applied: 0.0`, suggesting the prompt doesn't require it. If the prompt were tweaked to require `sl_buffer_applied >= 5pt` (NAS100) / `$2` (XAUUSD), the sl_beyond_ob bug goes away entirely. But that's WF-1 territory (prompt change). Chairman should decide: fix gate (C's option 1, lower-risk) vs fix prompt (option 2, cleaner but riskier re-validation burden).

4. **Is the 5.7% vs 4.5% CR difference material?** Using Agent B's 5.7% denominator vs Agent D's 4.5% matters for the "NAS100 half as productive as XAUUSD" narrative. For the live-gate comparison, D's 4.5% is the honest number (includes L2 + risk-cap kills that also exist in production). B's 5.7% is pre-kill.

5. **Does the D1-bias source lag similarly bite XAUUSD?** W14 NAS100 had 54 records locked to D1=bearish during a +4.20% rally. This is a mechanical computation (same code path as XAUUSD). Are there live XAUUSD NO_TRADE days where the same issue silently bit XAUUSD? Worth a backward-looking audit before CEO gates NAS100.

6. **The `poi_zone=premium` n=6 pattern — does it replicate on XAUUSD?** If yes, this is a global AI-framework signal (bias toward premium-zone entries in trending markets has negative EV). If no, it's NAS100-specific and possibly an artefact of the V-shaped regime. Worth one hour checking XAUUSD CANDIDATEs' zones.

7. **Does the B-identified "redundant OB-proximity check" (231 AI `ALL_GATES_PASS_BUT_NO_TRADE` rejects after 542 pre-AI `ob_proximity` rejects) suggest the pre-AI filter is too loose?** Or are the two filters computing proximity against different OB snapshots (e.g., the AI re-computes OB positions after MSO serialization)? This is a non-trivial question with real $ cost implications — an audit of both code paths before changing either filter.

8. **Additivity of C's leaks.** Chairman should frame the recoveries honestly as:
   - sl_beyond_ob fix STANDALONE: +13.5R (because of max_kz interference on 13 records)
   - max_kz 1→2 STANDALONE: +16.02R (clean)
   - JOINT: +36.5R (close to additive)
   Not "+20.5R and +16R additively."

---

_Review complete. Chairman: all spot-checks took ~35 tool calls; all agents' claims were probed against the raw JSONs and CSVs. The biggest corrections needed in synthesis are: (1) reject every "rerun on Sonnet" recommendation; (2) reject Agent A's "simulator artefact" narrative and the adjusted 56.3% WR that flows from it; (3) downgrade Agent B's "MISSED_WINNER" framing because half are C1 FAILs not proximity issues; (4) promote Agent C's findings to A-tier confidence (only agent whose every number I could reproduce bit-exact); (5) frame Agent D's W14 as the strongest standalone mechanistic finding, independent of any model concern._
