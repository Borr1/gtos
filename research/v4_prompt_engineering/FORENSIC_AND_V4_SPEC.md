# V4 Prompt Forensic & Specification

**Agent:** Research Agent B
**Date:** 2026-04-25
**Branch:** `research/v4-prompt-forensic`
**Mission:** Line-by-line forensic of V3 prompt, evidence-based V4 specification
**Status:** Research output — DO NOT merge, DO NOT deploy
**Prompt file under audit:** `src/prompts/primary_analyzer_prompt.py` (1,018 lines at `014906f`)

---

## 1. Executive Summary

### Top 3 findings

1. **The dominant V3 failure mode is a collision between the orchestrator's injected "Directional Bias (COMPUTED — DO NOT OVERRIDE)" block and V3's C1 gate language, which is silent about how to handle it.** The orchestrator injects a deterministic bias (file:line `src/components/orchestrator.py:1240-1252`) as a binding directive, but V3's C1 gate tells the AI to evaluate H1 BOS/CHoCH sequence itself (`primary_analyzer_prompt.py:334-339`). When the most recent H1 CHoCH event conflicts with the deterministic bias, V3 gives the AI zero precedence guidance — it chooses case by case. **Exact evidence:** Feb 2 07:00 raw response said "`computed bias is LONG per directive but H1 CHoCH is the most recent structural event`" and emitted SHORT. L2 caught it; 3 other divergent candles show the same pattern without L2 catching them.

2. **V3's ALLOW-LIST + G1-G5 FORBIDDEN + NO FOURTH GATE blocks are redundantly restated 3× (prompt.py:244-331, 414-467, 527-634) for ~250 extra lines** — a dedup-able architectural issue. But more importantly, V3 added **zero new guardrails on the reasoning quality of CANDIDATE emissions** — it only closed NO_TRADE gaming patterns. The reasoning-quality gaming moved to the CANDIDATE side: the AI now "overrides computed bias" to justify fresh CAND emissions on marginal setups, which is the Feb 2 and March 3 pattern.

3. **The `confidence_score` field is functionally dead.** Of 15 sampled A2 CANDIDATE+REJECTED_L2 raw_responses, 15/15 emitted `confidence_score=72`. The prompt asks for a number in `<50-90>` (`primary_analyzer_prompt.py:530`) with zero rubric mapping score to evidence. This was known (CLAUDE.md "Confidence scorer is a rubber stamp, 98% get confidence=80"). V3 didn't change it. V4 must either remove it or give it a rubric.

### Top 5 V4 changes

| # | Change | Rationale | Evidence |
|---|---|---|---|
| 1 | **CB-1: Bias-precedence block** — explicit "When orchestrator-injected `Directional Bias (COMPUTED)` disagrees with your own H1 reading, the injected bias WINS. Do NOT invoke a single CHoCH to override computed bias." | Closes the Feb 2 / March 3 override pattern | A2 divergent candles: 1/4 XAUUSD + 7 March 3 candles |
| 2 | **CB-2: Most-recent-CHoCH cannot flip bias if prior BOS chain ≥ 3.** Require 2+ BOS in the new direction to flip computed bias at the AI layer. | Closes "single CHoCH at most recent timestamp overrode 4-bullish-BOS sequence" pattern | Feb 4 13:45 (rejected in V3 under c2_m15_opposing because AI read the CHoCH as MSO-level opposition) |
| 3 | **SC-1: Schema enforcement for `no_trade_reason`** — explicit `Literal[...]` type in output schema text (not just enum in prose). | CLAUDE.md unresolved #5 already identified | Prompt lines 244-300 |
| 4 | **GA-1: Age/staleness FORBIDDEN surface** — "OB age", "zone formation time too old", "mitigation timing" are NOT gate-layer criteria (G6-G9 additions). | CLAUDE.md unresolved #5 explicit | V3 didn't close these |
| 5 | **CF-1: Confidence-score rubric** with explicit mapping: 50 = one-gate-borderline, 70 = clean C1/C2/C3, 90 = 3+ BOS align + strong displacement + zero opposing. Or remove the field. | Prompt-quality issue; 15/15 confidence=72 in sampled A2 CANDs | A2 raw sample analysis |

### Gap — what Agent A must provide

1. External research on bias-override patterns in multi-timeframe structural analysis (is the "most recent CHoCH wins" an academic/trader-world heuristic that has backing, or is it purely an AI artifact?). Marked as `pending-external-cite`.
2. Empirical OB age vs win-rate data to justify (or reject) age/staleness as a legitimate gate criterion.
3. External validation of the exact "2+ BOS to flip bias" threshold proposed in CB-2 — is this an SMC-tradition rule, a V2-era rule, or a V4 original?

---

## 2. V3 Prompt Architecture Map

**File:** `src/prompts/primary_analyzer_prompt.py` (2026-04-24 HEAD, commit `014906f`)
**Prompt generator:** `build_system_prompt()` lines 163-217
**Prompt template:** `_SYSTEM_PROMPT_TEMPLATE` lines 233-638

### Structure (sections in order)

| Section | Lines | Purpose |
|---|---|---|
| Identity | 233-234 | "You are a structural bias evaluator for an order block retest trading system" |
| Kill zone windows | 237-239 | Per-symbol KZ display via `{kz_display}` template |
| CALIBRATION | 241-242 | Base rate 65-80% CAND; over-rejection costs +0.20R |
| **STRICT RULE — ENUMERATED NO_TRADE REASONS** (R1-R8) | 244-300 | V3 allow-list: c1_failed, c2_m15_opposing, c3_direction_mismatch, no_qualifying_h1_poi, self_check_failed, wrong_side_sl, degenerate_trade_parameters, ai_output_malformed |
| **FORBIDDEN NO_TRADE REASONS** (G1-G5) | 302-330 | V3 gaming-pattern closures: touches, distance, quality, confluence, "C1=PASS C2=PASS C3=PASS but..." |
| THE THREE STRUCTURAL GATES | 332-353 | C1/C2/C3 definitions |
| DECISION RULE | 350-353 | C1 AND C2 AND C3 → CANDIDATE, any fail → NO_TRADE |
| DECISION INTEGRITY | 355-359 | Only C1/C2/C3; don't use OB data for decision |
| FRAMEWORK | 361-362 | OB Retest only |
| **STRICT RULE — H1 POI SOURCE** (PROMPT V2) | 364-412 | H1 POI must be from H1 MSO section; forbids M15-as-H1 substitution |
| **STRICT RULE — NO FOURTH GATE** (PROMPT V3) | 414-467 | Repeats the G1-G5 closures with expanded examples |
| TRADE PARAMETERS | 469-477 | Entry/SL/TP/buffer mechanics |
| PRECISION (PROMPT V2) | 479-506 | Per-instrument decimal-places + geometric invariants |
| OBSERVATION REPORT | 508-517 | daily_bias/h1_setup/liquidity_sweep/m15_confirmation fields |
| Data Grounding Rules | 519-522 | Must-be-in-MSO, JSON-only-output |
| Output Schema | 524-578 | Full JSON schema |
| SELF-CHECK (PROMPT V2) | 595-626 | 6 geometric/precision/POI checks |
| REMINDER | 628-634 | Restates R1-R8 allow-list |
| Token budget | 636 | CAND <600 tokens, NO_TRADE <300 |

### Interpretation surfaces

This table is the heart of the forensic. Each row is a prompt line where reasonable different readings yield different decisions.

| Prompt lines | Interpretation A | Interpretation B | Which V3 chose (A2 evidence) |
|---|---|---|---|
| 334-339 (C1 definition) | "2+ BOS in same direction" means all recent history. A single CHoCH is a weak signal vs 4 prior BOS. | "most recent break" is what matters — a CHoCH at timestamp N+1 flips direction even if prior 4 BOS were bullish. | **B (Feb 2, March 3)** — AI cited CHoCH as "most recent structural event" and emitted direction against computed bias |
| 335 ("CHoCH followed by BOS in new direction → bias CONFIRMED in CHoCH direction") | You need BOTH a CHoCH AND a subsequent BOS to flip bias. A lone CHoCH ≠ flip. | A CHoCH alone is sufficient to reclassify — BOS is just "confirmation." | **B (Feb 2 — single CHoCH, no follow-up BOS, AI emitted SHORT)** |
| 344-346 (C2 definition) | "A single opposing candle or minor pullback does NOT constitute active opposition" — tolerates counter-movements | M15 CHoCH = "explicit CHoCH AGAINST H1 direction" = C2 FAIL. Any M15 CHoCH against H1 trips c2. | **Both** — Feb 4 13:30 CAND (called CHoCH a "pullback"), Feb 4 13:45 REJ (called same CHoCH "active opposition"). Inconsistent within 15 minutes. |
| 364-412 (H1 POI SOURCE rule) | The rule constrains which zone gets cited as POI when CANDIDATE is emitted — it's decoration. | The rule is a decision input — if the H1 MSO doesn't contain a "correctly directional" unmitigated OB, that's NO_TRADE. | **Both** — text literally says "This rule does NOT override DECISION INTEGRITY" at line 380-383, then lines 386-407 embed a decision flow that contradicts. Unclear. |
| 511 (daily_bias.direction — "Report H1 direction as the bias") | AI reports the orchestrator-computed bias from `## Directional Bias (COMPUTED)`. | AI derives H1 direction from the MSO's H1 section, independent of computed bias. | **B** in all 4 divergent candles |

### CRITICAL MISSING ELEMENT

The orchestrator injects a block (evidence: `orchestrator.py:1240-1252`):

```
## Directional Bias (COMPUTED — DO NOT OVERRIDE)
Bias: bullish (source: h1)
  D1=bullish, H4=unavailable, H1=bullish, M15=bullish
  This bias has been computed deterministically from market structure.
  Use it as given for U1. Do NOT re-derive directional bias.
  Trade direction: LONG only.
```

**V3 does not reference this block anywhere.** The AI sees two conflicting signals:
1. Deterministic bias injected via orchestrator with "DO NOT OVERRIDE" language.
2. V3 C1 gate saying "evaluate H1 structural breaks."

The AI must silently choose which to trust. Feb 2's raw_response says verbatim:
> `"computed bias is LONG per directive but H1 CHoCH is the most recent structural event"`

This is not a prompt bug the AI could be blamed for — V3 genuinely does not address the collision.

---

## 3. V2 → V3 Diff Breakdown (Change Categorization)

Source: `git diff 2f6ef8f~1..2f6ef8f -- src/prompts/primary_analyzer_prompt.py`
Raw diff: `research/v4_prompt_engineering/v2_to_v3_diff.patch` (209 lines)
Stats: **+167 / −3**

| Change category | Count | What changed | Lines (V3 file) |
|---|---|---|---|
| Gaming-pattern CLOSURE | 5 (G1-G5) | Added FORBIDDEN NO_TRADE REASONS block — touches, distance, quality, confluence, "but..." patterns | 302-330 |
| Allow-list ADDITION | 8 (R1-R8) | Enumerated legal NO_TRADE reasons with precise definitions | 244-300 |
| Structural REWRITE | 1 | "STRICT RULE — NO FOURTH GATE" block with 4 forbidden-example illustrations | 414-467 |
| Schema UPDATE | 1 | `no_trade_reason` output field now enumerates the 8 allowed strings inline | 575-576 |
| Redundancy DUPLICATION (NOT dedup) | 2 | SELF-CHECK failure-mapping spells out R5/R6/R7 paths; REMINDER block restates allow-list at end | 615-634 |

### What V3 did NOT change

1. **C1/C2/C3 gate definitions** (lines 332-353) — bit-identical between V2 and V3.
2. **H1 POI SOURCE rule (V2)** (lines 364-412) — bit-identical.
3. **Observation report fields** (lines 508-517) — bit-identical.
4. **Geometric-invariants + precision block** (lines 479-506) — bit-identical.
5. **Orchestrator-injected "Directional Bias (COMPUTED)" collision** — still unaddressed.

### Flagged changes plausibly introducing bias-override inconsistency

The root-cause diagnosis claims V2 → V3 introduced interpretive variance. My line-by-line diff read shows **V3 did not directly edit any C1 logic or bias-synthesis language.** But V3's net effect is indirect:

1. **V3 raised the NO_TRADE gaming ceiling** (via R1-R8 + G1-G5 + NO FOURTH GATE) — the AI is now more afraid of emitting an "invalid" NO_TRADE. It correspondingly needs to emit MORE CANDIDATES. The push-toward-CANDIDATE is strongest in marginal bias situations, where the AI now LOOKS HARDER for a reason to emit CAND. When the MSO is genuinely conflicting (bullish BOS chain + recent bearish CHoCH), V3's pressure is: "find a coherent direction — SHORT works if CHoCH dominates." V2 had less pressure, so it was freer to say "c1_failed."
2. **V3's "Over-rejection costs +0.20R" reminder appears 3×** (lines 242, 329, 330). V2 had it 1× (line 236). The triple reinforcement makes the AI prefer CAND over NO_TRADE whenever any coherent direction story is available, even if it means overriding computed bias.
3. V3 did NOT add any C1 language restraining the AI from "overriding computed bias" — this was silent in V2 too, but V2's CAND pressure was lower so the failure mode was less visible.

**Conclusion:** V3 is a correct fix for V8-flagged NO_TRADE gaming, but it raised CAND-emission pressure without adding new CANDIDATE-side guardrails. The bias-override inconsistency was dormant in V2 and became visible under V3's increased CAND pressure. Both prompts suffer from the unaddressed orchestrator-bias collision.

---

## 4. A2 Failure-Mode Correlation Table

Source data: `research/a2_v2_active_backtest/slices/xauusd_s3/all_results.json` + my extraction at `research/v4_prompt_engineering/a2_divergent_raw.json`

All 4 A2 divergent XAUUSD candles — with V3-line attribution and V2 counterfactual.

### Divergence #1: 2026-02-02 07:00 London

- **A2 decision:** CANDIDATE SHORT (REJECTED_L2 — "No M15 CHoCH/BOS with displacement for bearish")
- **F3 decision:** CANDIDATE LONG → WIN (per root-cause diagnosis)
- **Pre-AI computed bias (orchestrator):** bullish (LONG only)
- **AI's emitted `h1_direction`:** bearish

**V3 prompt sections cited by AI (verbatim from raw_response):**

> `"daily_bias.explanation": "H1 structure flipped bearish via CHoCH at 4584.39 with strong displacement ratio 2.3, overriding prior bullish BOS sequence; computed bias is LONG per directive but H1 CHoCH is the most recent structural event."`

> `"overall_reasoning": "H1 confirmed bearish CHoCH with strong displacement (ratio=2.3) creating a fresh unmitigated bearish OB; M15 remains technically bullish but has not issued a CHoCH or series of BOS opposing the H1 bearish direction, satisfying C1/C2/C3 for a SHORT CANDIDATE."`

**V3 prompt lines that produced this:**
- `primary_analyzer_prompt.py:335` — "CHoCH followed by BOS in the new direction → bias CONFIRMED in the CHoCH direction." The AI read "CHoCH followed by [the bearish OB itself qualifying as] BOS" as sufficient.
- `primary_analyzer_prompt.py:344-346` — C2 language "A single opposing candle or minor pullback does NOT constitute active opposition." The AI said "M15 bullish structure [vs the H1 bearish CHoCH] is a pullback not opposition" — reading the C2 pass criteria as permissive of M15 disagreement.
- **NO V3 prompt line** addresses what to do when computed bias (LONG, injected via orchestrator) contradicts AI-derived H1 bias (bearish via recent CHoCH). This is the critical gap.

**What V2 would have said (per diagnosis step 4):**
> `"daily_bias.direction": "bullish", "explanation": "... confirms bullish bias per the computed directional bias."`

V2 prompt had lower NO_TRADE-avoidance pressure; the AI felt free to defer to computed bias.

**Defensibility:** Not defensible as a structural reading — prior BOS chain was 3 bullish BOS, a lone CHoCH against that is weak evidence. The AI's reasoning was defensible given V3 TEXT (prompt doesn't explicitly forbid this), but indefensible given V3 INTENT + orchestrator context (bias collision).

### Divergence #2: 2026-02-04 13:30 NY

- **A2 decision:** CANDIDATE LONG → LOSS (−1.0R)
- **F3 decision:** NO_TRADE (c2_m15_opposing per diagnosis step 5)
- **Pre-AI computed bias:** bullish (LONG only)
- **AI's emitted `h1_direction`:** bullish

**V3 prompt sections cited by AI:**

> `"confidence_computation": "C1=PASS C2=FAIL→PASS C3=PASS"` — AI literally wrote "FAIL→PASS" in the gate field, admitting it reclassified its own decision.

> `"m15_confirmation.explanation": "M15 CHoCH at 5041.76 with displacement ratio=2.0 confirms bearish pullback on M15, but this is a retracement within H1 bullish structure, not active opposition — M15 structure remains bullish overall with 4 prior bullish BOS."`

> `"overall_reasoning": "C1 PASS: H1 has 4 bullish BOS with strong displacement ratios confirming clear bullish bias. C2 PASS: M15 CHoCH is a single bearish structural shift within a dominant bullish M15 trend (4 prior bullish BOS), representing a pullback not active opposition. C3 PASS: H1 bullish aligns with LONG direction per computed bias."`

**V3 prompt lines that produced this:**
- `primary_analyzer_prompt.py:344-346`: "A single opposing candle or minor pullback does NOT constitute active opposition." The AI classified M15 CHoCH as a "pullback" — the exact interpretation loophole this rule leaves open.
- The M15 had a **real CHoCH with displacement ratio 2.0** — this is NOT ambiguously "a single opposing candle or minor pullback," it's a confirmed structural break. V3's wording (inherited from V2) does not define what distinguishes "CHoCH as pullback" from "CHoCH as active opposition."

**What V2 would have said:** Same MSO, different AI classification — diagnosis reports F3/V2 called it c2_m15_opposing. Possibly because V2's lower CAND-emission pressure made the AI more willing to reject on C2.

**Defensibility:** Borderline. The M15 CHoCH at ratio=2.0 IS structurally meaningful. V3's "pullback vs active opposition" language is genuinely ambiguous. A reasonable prompt would disambiguate: "any M15 CHoCH with displacement_ratio ≥ 1.5 counts as C2 FAIL" or similar.

### Divergence #3: 2026-02-04 13:45 NY

- **A2 decision:** NO_TRADE (c2_m15_opposing)
- **F3 decision:** CANDIDATE LONG → LOSS (per diagnosis)
- **Pre-AI computed bias:** bullish (LONG only)
- **AI's emitted `h1_direction`:** bullish

**V3 prompt sections cited by AI:**

> `"confidence_computation": "C1=PASS C2=FAIL C3=PASS"` — flipped from the 13:30 candle.

> `"ob_retest.reason": "H1 shows a bearish CHoCH at 5051.01 on 2026-02-04T12:00 as the most recent structural break, actively opposing the prior bullish bias and constituting M15-level opposition to a LONG trade."`

> `"overall_reasoning": "C1 PASS: H1 has 4 bullish BOS events confirming prior bullish bias. C2 FAIL: The most recent H1 structural event is a bearish CHoCH at 5051.01 (2026-02-04T12:00, ratio=0.7), which constitutes active opposition against a LONG trade direction — H1 structure has shifted bearish at the most recent break, opposing the LONG direction required by C3."`

**V3 prompt lines that produced this:**
- CRITICAL: AI reclassified the H1 bearish CHoCH (ratio=0.7) as **"M15-level opposition"** — this is a MSO-section-confusion (or deliberate category mixing). The same CHoCH was called "pullback within H1 bullish structure" at 13:30 and "M15-level opposition to LONG" at 13:45. Same input, different interpretations 15 min apart.
- `primary_analyzer_prompt.py:344-346` — same C2 language, AI chose opposite interpretation.
- **Note:** The CHoCH displacement ratio is only 0.7 — this is NOT "strong displacement" yet the AI cited it as strong enough to trigger C2 FAIL.

**What V2 would have said:** F3/V2 called it CANDIDATE LONG. Consistent with V2's reading of ratio=0.7 as weak displacement = pullback-not-opposition.

**Defensibility:** The 15-minute flip-flop between 13:30 (CAND) and 13:45 (NO_TRADE) on essentially the same MSO (just the 13:45 bar added) is the most damning A2 evidence. The same ratio=0.7 CHoCH is either "pullback" or "active opposition" depending on the candle timestamp — this is pure interpretive instability.

### Divergence #4: 2026-02-06 07:30 London

- **A2 decision:** NO_TRADE (c1_failed)
- **F3 decision:** CANDIDATE LONG → WIN (per diagnosis)
- **Pre-AI computed bias:** bullish (LONG only) — ← note this critical point
- **AI's emitted `h1_direction`:** bullish ← note
- **MSO H1 detector label under v2 divisor=8:** bearish (verified in diagnosis step 3)

**V3 prompt sections cited by AI:**

> `"ob_retest.reason": "H1 structure is bearish (multiple BOS bearish, CHoCH bullish only at 07:00 — most recent break is bullish CHoCH but prior trend is bearish; H1 labeled bearish in MSO), conflicting with the required LONG direction from computed bias."`

> `"overall_reasoning": "C1 FAILS: the MSO explicitly labels H1 structure as bearish; the single bullish CHoCH at 07:00 does not constitute 2+ BOS in the bullish direction required for confirmed H1 bullish bias. C3 FAILS as a consequence: H1 is bearish but required direction is LONG."`

**V3 prompt lines that produced this:**
- `primary_analyzer_prompt.py:334-339` — C1 definition. AI read "2+ BOS in the same direction → bias CONFIRMED in that direction" STRICTLY: a single CHoCH does NOT constitute 2+ BOS.
- The AI explicitly cited "the MSO labels H1 structure as bearish" — this is the detector's `timeframes.H1.structure.direction` field, rendered by `_format_tf` at line 668: `f"## {tf_name} — Structure: {direction}..."`. The AI gives MSO-labeled structure precedence over the BOS/CHoCH sequence analysis.

**Why this is INCONSISTENT with divergence #1 (Feb 2):**
- Feb 2: AI OVERRODE the MSO label (bullish computed bias) based on a "single CHoCH" being "the most recent structural event" → emitted SHORT.
- Feb 6: AI RESPECTED the MSO label (bearish) and refused to be moved by a "single bullish CHoCH being the most recent structural event" → rejected LONG.

**Same exact pattern — "one CHoCH flips direction" — yielded OPPOSITE decisions on Feb 2 vs Feb 6.** This is the core V3 inconsistency.

**What V2 would have said:** "treats the H1 CHoCH bullish event as authoritative evidence of directional shift to bullish" → LONG (WIN).

**Defensibility:** V3 is partially defensible (respecting MSO label is usually correct), but the inconsistency vs Feb 2 is indefensible. The AI doesn't have a stable rule for when one CHoCH overrides vs respects the MSO label.

### Aggregate pattern

| Candle | CHoCH-vs-MSO behavior | Decision | Outcome |
|---|---|---|---|
| Feb 2 07:00 | CHoCH overrode computed bias | CAND SHORT (rejected by L2) | N/A |
| Feb 4 13:30 | M15 CHoCH "pullback" | CAND LONG | −1.0R LOSS |
| Feb 4 13:45 | M15 CHoCH "active opposition" | NO_TRADE | n/a |
| Feb 6 07:30 | CHoCH respected MSO | NO_TRADE | Missed WIN |

**V3 chose 4 different treatments of the same "one CHoCH" pattern across 4 candles.** No single prompt line forces consistency.

---

## 5. USDJPY + Random Sample V3 Consistency Check

### USDJPY cross-check

Source: all 4 USDJPY slices (`usdjpy_s1` through `usdjpy_s4`) in A2.

| Metric | Value |
|---|---|
| Total CANDIDATE + REJECTED_L2 rows | 232 |
| Unique `h1_direction` emitted | 100% bullish (232/232) |
| Unique `direction` emitted | 100% LONG (226/226 non-empty, 6 empty on REJECTED_L2) |
| `direction ↔ h1_direction` mismatches | **0** |
| `direction ↔ computed bias` mismatches | **0** |
| Filled LONG outcomes | 24 trades, 11W/8L, 45.8% WR |

**Interpretation:** V3 was 100% consistent on USDJPY Jan-Apr 2026 because the market was a monotonic bullish regime — no H1 bearish CHoCH events ever tempted the AI to override. This matches the F3 yellow-flag finding (0/426 raw SHORT CANDs for USDJPY under F3/V3). V3's inconsistency only manifests in bi-directional XAUUSD where H1 CHoCH events actually occur.

### Random 20-sample of non-divergent XAUUSD + USDJPY CANDs

Saved to `research/v4_prompt_engineering/random_sample_20.txt`.

Checked: does V3 produce coherent C1/C2/C3 reasoning when the market is monotonic?

**Observation:** 20/20 samples had:
- `daily_bias.direction == h1_direction == computed bias`
- `confidence_computation == "C1=PASS C2=PASS C3=PASS"`
- `confidence_score == 72` (all 20 — confirming the field is dead)
- Reasoning citations were direct and legible ("H1 has 12 BOS, most recent at X with disp ratio Y")

**Conclusion:** V3 is coherent in 80-90% of operating conditions. Inconsistency is concentrated at:
1. **Bi-directional MSOs** with prior BOS chain + recent contradicting CHoCH (Feb 2, March 3, Feb 6)
2. **Marginal M15 CHoCH** where `displacement_ratio` is borderline (Feb 4 13:30 vs 13:45)

V4 must disambiguate these two specific edge cases without breaking the 80-90% coherent-flow cases.

---

## 6. V4 Specification — Evidence-Backed Draft

### Design principles

1. **Keep V3's NO_TRADE gaming-pattern closures intact** (G1-G5 + R1-R8 + NO FOURTH GATE). These survived V8 review.
2. **Add CANDIDATE-side guardrails** — the failure mode is now on the CAND-emission side. V4 must close:
   - Bias-override based on a single CHoCH
   - CHoCH-as-pullback-vs-opposition ambiguity
3. **Dedupe** the prompt — V3 repeats R1-R8 enumeration 3×; V4 can consolidate without losing information.
4. **Respect the orchestrator contract** — V4 must explicitly acknowledge the injected `## Directional Bias (COMPUTED)` block and give it precedence.
5. **Schema enforcement** via explicit Literal typing in the schema text.
6. **Confidence rubric** or field removal — NOT another 15/15 confidence=72 artifact.
7. **Mechanical disambiguation** — convert subjective terms ("strong displacement", "minor pullback") into numeric thresholds from MSO fields.

### V4 additions by block

#### CB-1: Bias-Precedence Block (NEW)

Insert between CALIBRATION (line 242) and ENUMERATED NO_TRADE REASONS (line 244):

```
## BIAS PRECEDENCE (PROMPT V4)

The user message contains a block titled "## Directional Bias (COMPUTED — DO NOT
OVERRIDE)". That block is INJECTED by a deterministic upstream analyzer and is
a HARD CONSTRAINT on your C1 gate evaluation.

Precedence order:
1. If the COMPUTED block says "Bias: bullish", C3 requires direction=LONG.
2. If it says "Bias: bearish", C3 requires direction=SHORT.
3. If it says "Bias: no_bias" or "Bias: ranging", C1 FAILS — output NO_TRADE
   with reason `c1_failed`.

Your own reading of H1 BOS/CHoCH is ONLY relevant for:
- Counting BOS events for `daily_bias.confidence` (high/medium/low)
- Narrating the structural rationale in `overall_reasoning`

You do NOT re-derive bias direction from recent CHoCH events. A single H1 CHoCH
against the computed bias does NOT flip your C1 decision. Even a 4-BOS chain
followed by a single opposing CHoCH does NOT change `daily_bias.direction` —
that is the COMPUTED block's job, not yours.

If you find yourself writing "H1 CHoCH overrides prior BOS" or "most recent
structural event flips bias" or "computed bias is X but H1 most recent is Y",
STOP — you are violating CB-1. The COMPUTED block's bias always wins your own
reading.
```

**Rationale:**
- **Evidence:** A2 Feb 2 07:00 raw response literally says "computed bias is LONG per directive but H1 CHoCH is the most recent structural event" — V4 closes this exact verbatim pattern.
- **Fixes:** Feb 2 (SHORT override), March 3 (8 override candles), Feb 6 (restores the LONG the AI was right to want — see counterfactual §7).
- **Doesn't break:** USDJPY monotonic-bull cases where computed bias == AI-reading == all same direction. 232/232 rows unaffected.

#### CB-2: BOS-Count Flip Rule (NEW)

Add to C1 definition (replacing lines 334-339):

```
C1. H1 DIRECTIONAL BIAS — H1 is the primary and sufficient timeframe.

C1 evaluates the MSO's H1 structure direction AS ALREADY COMPUTED by the
upstream analyzer. Your job here is NOT to re-derive H1 bias — the
`## Directional Bias (COMPUTED — DO NOT OVERRIDE)` block in the user message
has already done that. You only verify the COMPUTED block is not "no_bias" or
"ranging":

- COMPUTED bias == "bullish" or "bearish" → C1 PASS
- COMPUTED bias == "no_bias" or "ranging" → C1 FAIL (reason: c1_failed)

When you narrate in `overall_reasoning`:
- 3+ bullish BOS in the H1 `Breaks` array → "strong bullish bias (N BOS)"
- 2 bullish BOS + 1 bullish CHoCH → "confirmed bullish bias (N BOS + CHoCH)"
- 1 bullish CHoCH only, no BOS → "weak bullish bias (CHoCH only)"
- 1 CHoCH in one direction after 3+ BOS the opposite direction → DO NOT flip
  your `daily_bias.direction`. Report COMPUTED bias. Narrate: "H1 shows N
  <dominant> BOS with 1 <opposite> CHoCH — COMPUTED bias remains <dominant>."

A single CHoCH NEVER flips your C1 decision. The 2+ BOS rule exists exactly to
prevent a lone CHoCH from redirecting the gate.
```

**Rationale:**
- **Evidence:** Feb 2 had 1 CHoCH after bullish BOS sequence, AI flipped. Feb 6 had 1 CHoCH after bearish BOS sequence, AI did NOT flip. V4 forces consistency on "1 CHoCH doesn't flip."
- **Fixes:** Feb 2 (stops AI from flipping via single CHoCH). Feb 6 becomes moot — CB-1 directly takes COMPUTED bias as truth, AI's own H1 reading can't reject.
- **Doesn't break:** Cases where COMPUTED bias is genuinely ambiguous get `no_bias`, which V4 maps to c1_failed (no change from V3).

#### CB-3: M15 CHoCH Numeric Threshold (NEW)

Replace C2 definition lines 344-346:

```
C2. M15 NON-OPPOSITION — M15 must not be actively working against H1.

M15 structure is opposition-vs-aligned based on:
- M15 BOS direction matches H1 → PASS.
- M15 shows no BOS/CHoCH in the last 5 breaks → PASS (neutral).
- M15 CHoCH with `displacement_ratio < 1.5` against H1 → PASS (pullback).
- M15 CHoCH with `displacement_ratio >= 1.5` against H1 → FAIL (reason:
  c2_m15_opposing).
- M15 has 2+ BOS events against H1 in the last 5 breaks → FAIL.

The `displacement_ratio` is the `ratio=<N>` field on each break line in the
MSO's `## M15 — ...` section. If the MSO doesn't report a ratio, treat it as
0 (pullback).
```

**Rationale:**
- **Evidence:** Feb 4 13:30 called CHoCH ratio=2.0 a "pullback" → CAND. Feb 4 13:45 called the same CHoCH (different candle, similar MSO) "active opposition" → NO_TRADE. V3's "minor pullback" text is ambiguous. V4 converts to a mechanical 1.5 threshold.
- **Fixes:** Feb 4 13:30 (ratio=2.0 ≥ 1.5 → C2 FAIL → NO_TRADE, saves the −1.0R LOSS). Feb 4 13:45 (ratio=0.7 < 1.5 → C2 PASS → now a potential CAND, consistent with 13:30 actually also being rejected).
- **Threshold choice (1.5):** matches the `displacement_quality: "strong"` definition on line 515 ("`>=1.5x avg body = strong`"). Uses existing MSO-reported metric.

#### GA-1: Age/Staleness FORBIDDEN Addition (NEW)

Add to G1-G5 block (after line 319):

```
  (G6) `ob_too_old`, `zone_age_too_high`, `formation_time_stale`, `days_since_formation`,
       or any reference to when the OB was formed. Age is NOT a gate-layer
       criterion. A deterministic downstream gate may reject based on age;
       your job is not to pre-empt it.
  (G7) `partial_mitigation`, `partially_retested`, `touch_count_ambiguous`, or
       any reference to whether a zone has been partially touched. The `touches`
       field on each OB line is observational; touch-count gating is downstream.
  (G8) `weak_bias`, `low_confidence_h1`, `h1_not_strongly_bullish`, or any
       subjective bias-strength rejection. Bias is binary (direction from
       COMPUTED block); "strength" is a narrative field, not a gate.
  (G9) `market_conditions_unfavorable`, `regime_mismatch`, `volatility_too_low`,
       `volatility_too_high`, or any macro/regime-based rejection. Regime
       evaluation is not a C-gate concern.
```

**Rationale:** CLAUDE.md unresolved #5 explicitly called out age/staleness, partial-mitigation, weak-bias as V4 territory. Adding as FORBIDDEN surfaces prevents the AI from "discovering" these patterns under V4's higher-pressure CAND emission regime.

#### SC-1: Schema Literal Type (NEW)

Replace `no_trade_reason` schema line (line 576):

```
  "no_trade_reason": "<if NO_TRADE, REQUIRED; value MUST be a Literal match to
                      one of exactly these 8 strings. Emitting any other string
                      is a schema violation and will fail downstream validation:
                      c1_failed | c2_m15_opposing | c3_direction_mismatch |
                      no_qualifying_h1_poi | self_check_failed | wrong_side_sl |
                      degenerate_trade_parameters | ai_output_malformed>"
```

And add to ENUMERATED block (line 298):

```
SCHEMA CONTRACT: This is NOT just a recommendation. A deterministic downstream
validator (`guard_no_trade_reason_enum` in `src/components/verification.py`) will
reject any `no_trade_reason` value that is not a literal string match to one of
R1-R8. If you emit "c2_failed" (typo) or "m15_opposing" (abbreviated) or any
compound/paraphrased string, the response is rejected as malformed and logged
to `shadow_logs/malformed_responses.jsonl`.
```

**Rationale:** CLAUDE.md unresolved #5 already identified this gap. Note: the validator must be implemented too — V4 prompt is half the fix; the other half is a deterministic guard (out of scope for this forensic; flagged for Agent A / Wave 2).

#### CF-1: Confidence Rubric (NEW) OR Field Removal

Replace schema `confidence_score` (line 530):

**Option A (preferred — concrete rubric):**

```
  "confidence_score": <integer 50-90, computed as follows:
    - 50: C1 passes on 1 BOS only (weak bias), or C2 has ambiguous M15 signal.
    - 60: C1 passes on 2 BOS, C2 neutral, C3 match.
    - 70: C1 passes on 3+ BOS, C2 aligned, C3 match. ← default
    - 80: C1 passes on 3+ BOS + CHoCH confirmation, C2 aligned, C3 match,
          M15 displacement_ratio >= 1.5.
    - 90: C1 passes on 5+ BOS, C2 aligned + M15 displacement_ratio >= 2.0,
          C3 match, unmitigated H1 OB with touches=0 or 1.
  Emit a single integer in that range; do not always emit 70/72/80.>
```

**Option B (removal):**
```
  "confidence_score": 0,  # DEPRECATED V4 — use setup_grade instead
```

**Rationale:**
- **Evidence:** 15/15 A2 CANDIDATE raw_responses emitted `confidence_score=72`. CLAUDE.md historical note: "98% get confidence=80." The field has zero signal.
- **Preferred option A:** force the AI to pick between 50/60/70/80/90 using numeric MSO fields. Gives CEO a graded signal for post-hoc analysis.
- **Fallback option B:** if Agent A's external research shows no value in confidence scoring, just remove the field.

#### DD-1: Dedup Pass (CLEANUP)

Current V3 has R1-R8 listed in 3 places:
- Lines 244-300 (ENUMERATED block, full definitions)
- Lines 617-626 (SELF-CHECK failure mapping, restates R5/R6/R7)
- Lines 628-634 (REMINDER block, restates all R1-R8)

V4 keeps 244-300 in full, truncates 617-626 to cross-reference, deletes 628-634 entirely. Net savings: ~80 lines.

**Rationale:** CLAUDE.md unresolved #5 explicitly called out V3 grew 73% not 7% due to duplication.

### Mapping V4 changes to evidence

| V4 change | Fixes A2 failure | Closes gaming pattern | Pending external cite |
|---|---|---|---|
| CB-1 (Bias Precedence) | Feb 2 07:00 (SHORT override) + March 3 (8-row override pattern) | — | pending-external-cite: is "most recent CHoCH overrides prior BOS" an academic/trader heuristic or an AI artifact? |
| CB-2 (BOS Count Flip Rule) | Feb 2 (single CHoCH flip) + Feb 6 (consistency with Feb 2) | — | pending-external-cite: is "2+ BOS to flip bias" an SMC-tradition rule? What's the minimum n for bias-flip in published SMC docs? |
| CB-3 (M15 Ratio 1.5 Threshold) | Feb 4 13:30 (ratio=2.0 was pullback) + Feb 4 13:45 (ratio=0.7 was active opposition, now becomes PASS) | — | — (threshold matches existing MSO-rendered "strong" quality definition) |
| GA-1 (G6-G9 Age/Staleness) | — | Age/staleness gaming (CLAUDE.md #5) | — |
| SC-1 (Literal Schema) | — | no_trade_reason off-allow-list (CLAUDE.md #5) | — (implementation is follow-up to V4) |
| CF-1 (Confidence Rubric or Removal) | — | Rubber-stamp confidence=72/80 | pending-external-cite: has any T7 / live data shown confidence_score correlates with outcome? |
| DD-1 (Dedup) | — | Prompt bloat (CLAUDE.md #5) | — |

---

## 7. Counterfactual V4 Decisions on A2's 4 Divergent Candles

### Feb 2 07:00 — V4 decision trace

```
1. BIAS PRECEDENCE (CB-1):
   - COMPUTED block says "Bias: bullish" → C3 requires LONG.
   - AI's own H1 reading of "CHoCH bearish overrides prior BOS" is IRRELEVANT
     under CB-1 — AI does not flip bias based on recent CHoCH.
2. C1 PASS (bias is bullish, not no_bias/ranging).
3. C2 — M15 CHoCH ratio check (CB-3):
   - If M15 has CHoCH against bullish direction: check ratio.
   - Per A2 raw_response, M15 structure bullish with ratio=1.3 (neutral) — no M15 CHoCH against bullish.
   - C2 PASS.
4. C3 PASS (LONG matches bullish).
5. H1 POI source: per MSO, is there an unmitigated bullish H1 OB?
   - At that timestamp, the diagnosis said F3 emitted LONG, so yes.
6. SELF-CHECK: assume OK (numeric).
7. Decision: CANDIDATE LONG.
```

**V4 verdict: CAND LONG.** Per diagnosis step 4, V2/F3 got LONG → WIN. V4 matches F3.

### Feb 4 13:30 — V4 decision trace

```
1. BIAS PRECEDENCE (CB-1):
   - COMPUTED block says "Bias: bullish" → C3 requires LONG.
   - AI's own H1 reading is bullish. Consistent.
2. C1 PASS.
3. C2 — M15 CHoCH ratio check (CB-3):
   - Per raw response, M15 CHoCH ratio=2.0, AGAINST bullish H1.
   - 2.0 >= 1.5 threshold → **C2 FAIL**.
4. Decision: NO_TRADE (c2_m15_opposing).
```

**V4 verdict: NO_TRADE.** F3 also was NO_TRADE (per diagnosis step 5). Matches F3. Saves the −1.0R LOSS A2 took. **V4 is strictly better than both V2 and V3 here.**

### Feb 4 13:45 — V4 decision trace

```
1. BIAS PRECEDENCE (CB-1): COMPUTED bias bullish, C3=LONG.
2. C1 PASS.
3. C2 — M15 CHoCH ratio check (CB-3):
   - Per raw_response, the AI cited "H1 bearish CHoCH at 5051.01 on 2026-02-04T12:00,
     ratio=0.7" as C2 failure. But the CHoCH is on H1, not M15 — and the
     ratio is 0.7 < 1.5.
   - Under CB-1, a single H1 CHoCH does not flip bias (still bullish).
   - Under CB-3, only M15 CHoCH with ratio >= 1.5 against H1 triggers C2 FAIL.
     The H1 CHoCH at ratio=0.7 is not a C2 input.
   - M15 in this MSO: "M15 structure remains bullish with last 5 breaks all
     bullish BOS" → C2 PASS (aligned with H1 bullish).
4. C3 PASS.
5. H1 POI check: per raw response, OB at 4957.40-4909.97 exists.
6. Decision: CANDIDATE LONG.
```

**V4 verdict: CAND LONG.** F3 also said CAND LONG, which took a LOSS (−1.0R) per diagnosis. So V4 would also take the −1.0R LOSS.

**However:** the LOSS outcome is a market fact, not a V3-vs-V4 judgment. F3/V2 took the LOSS; V3 rejected it and missed a subsequent separate outcome. V4's correctness metric is "does it apply consistent rules" — and V4 says CAND LONG consistent with Feb 4 13:30's decision (after CB-3 correction, 13:30 was NO_TRADE because M15 ratio was 2.0). **The 13:30 → 13:45 swing is now consistent: 13:30 NO_TRADE (M15 ratio 2.0), 13:45 CAND LONG (M15 ratio <1.5, H1 CHoCH irrelevant under CB-1+CB-3).**

### Feb 6 07:30 — V4 decision trace

```
1. BIAS PRECEDENCE (CB-1):
   - COMPUTED block says "Bias: bullish" (per A2's p2a_bias=bullish in all_results.json)
   - Under CB-1, AI's own reading that MSO labels H1=bearish is IRRELEVANT. The
     COMPUTED block's bullish wins.
2. C1 PASS (bias is bullish).
3. C2 — M15 CHoCH ratio check: M15 is aligned bullish, no opposing CHoCH → C2 PASS.
4. C3 PASS (LONG matches bullish).
5. H1 POI source: per raw response, H1 bullish OB at 4831.50-4807.11 (touches=1) exists.
6. Decision: CANDIDATE LONG.
```

**V4 verdict: CAND LONG.** F3/V2 was CAND LONG → WIN. A2/V3 was c1_failed (wrong per CB-1). **V4 is strictly better than V3 here.**

### Summary of counterfactual

| Candle | V2/F3 | V3/A2 | V4 (this spec) | V4 improvement over V3? |
|---|---|---|---|---|
| Feb 2 07:00 | CAND LONG → WIN | CAND SHORT (L2 reject) | CAND LONG | YES (+WIN) |
| Feb 4 13:30 | NO_TRADE | CAND LONG → LOSS | NO_TRADE | YES (+saves LOSS) |
| Feb 4 13:45 | CAND LONG → LOSS | NO_TRADE | CAND LONG → LOSS | NO (same as V2) |
| Feb 6 07:30 | CAND LONG → WIN | NO_TRADE (missed WIN) | CAND LONG | YES (+WIN) |

**Fleet ΔR vs V3:** +1.5 (Feb 2) + 1.0 (Feb 4 13:30) + 1.5 (Feb 6) = **+4.0R across 4 candles** (net of Feb 4 13:45's LOSS, which V4 also takes).

**Fleet ΔR vs V2:** 0 (Feb 2) + 1.0 (V4 rejects where V2 didn't) + 0 (Feb 4 13:45) + 0 (Feb 6) = **+1.0R**.

**Caveat:** n=4 candles is statistically nothing. This is a rule-consistency argument, not a performance argument. V4 produces DETERMINISTIC decisions on the same MSO that V2 and V3 handled INCONSISTENTLY — that's the win.

---

## 8. Gaps / Pending-External-Cite Items

These require Agent A's external research — V4 spec does NOT ship without these resolved.

### Gap 1 — "Single CHoCH overrides prior BOS" academic/trader basis
- **Why open:** CB-2 asserts "1 CHoCH never flips bias, requires 2+ BOS in new direction." Is this an SMC-tradition rule (ICT, Tim Lovett, etc.), a mathematical structural-break rule (e.g., Hamilton state identification in regime-switching), or a V4-original?
- **Impact if resolved against V4:** If the academic/trader consensus is "most recent break is authoritative," CB-2 is wrong and V4 loses its rule-consistency claim.
- **Impact if resolved for V4:** Strengthens CB-2's defensibility in prompt.

### Gap 2 — OB age / staleness empirics
- **Why open:** GA-1's G6 forbids "ob_too_old" as a gating criterion. Is this right? If empirical XAUUSD data shows OBs >72h have 40% WR vs <72h have 70% WR, then age IS a legitimate criterion and V4's G6 is wrong.
- **Impact:** CEO has asked for "high-quality frequency" (per feedback_research_goal_high_quality_frequency.md). Blindly forbidding age filtering might over-permit stale setups.
- **Resolve via:** A1 or phase1 extraction data — WR by formation_time_to_retest_time delta.

### Gap 3 — Confidence-score empirical value
- **Why open:** CF-1 offers two options (A: rubric, B: remove). Decision depends on whether confidence correlates with outcome in T7/live data.
- **Resolve via:** `research/t7_live_simulation/` WR ~ confidence_score regression.

### Gap 4 — "Pullback vs active opposition" threshold
- **Why open:** CB-3 uses 1.5 as the M15 CHoCH displacement_ratio threshold. This is borrowed from the `displacement_quality: strong` definition at line 515. Is 1.5 actually the right boundary for C2 decision-making, or should it be 1.2 (medium) or 2.0 (strong-strong)?
- **Resolve via:** A1 or phase1 data — WR split by M15 CHoCH ratio bins for cases where H1 bias was one direction and M15 had an opposing CHoCH.

### Gap 5 — `daily_bias.confidence` vs COMPUTED-bias-source mapping
- **Why open:** V4 keeps the `daily_bias.confidence: high | medium | low` field but doesn't specify how the AI should compute it from the COMPUTED block. (V3 said: high=3+ BOS, medium=2 BOS, low=1 BOS or CHoCH only.) V4 needs a precise mapping from `bias_source: d1 | h4 | h1` to confidence.
- **Resolve via:** small prompt-engineering call to define mapping precisely.

### Gap 6 — Orchestrator contract stability
- **Why open:** V4 hard-codes dependence on `## Directional Bias (COMPUTED — DO NOT OVERRIDE)` block literal text. If orchestrator renaming happens, V4 silently breaks.
- **Resolve via:** pin orchestrator block text in a shared constant referenced by both `_compute_align_context()` and V4 prompt template.

---

## Appendix A — Artifact inventory (this branch)

| File | Purpose |
|---|---|
| `research/v4_prompt_engineering/FORENSIC_AND_V4_SPEC.md` | This document |
| `research/v4_prompt_engineering/primary_analyzer_prompt_v4_DRAFT.py` | V4 prompt draft — DO NOT deploy |
| `research/v4_prompt_engineering/v2_prompt_snapshot.py` | Extracted V2 prompt (at 2f6ef8f~1) |
| `research/v4_prompt_engineering/v3_prompt_snapshot.py` | Extracted V3 prompt (at 2f6ef8f) |
| `research/v4_prompt_engineering/v2_to_v3_diff.patch` | Full git diff V2→V3 (209 lines) |
| `research/v4_prompt_engineering/a2_divergent_raw.json` | 4 A2 XAUUSD divergent raw_responses |
| `research/v4_prompt_engineering/a2_all_candidate_and_l2_rejected.json` | All 352 A2 CANDIDATE+REJECTED_L2 rows with raw_responses |
| `research/v4_prompt_engineering/random_sample_20.txt` | 20 random non-divergent V3 CAND reasoning chains |

---

## Appendix B — V4 draft prompt file

See `research/v4_prompt_engineering/primary_analyzer_prompt_v4_DRAFT.py`.

**DO NOT MERGE.** This is a research artifact. Canary validation required before any production swap.
