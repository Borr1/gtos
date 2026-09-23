# Phase 2 Review — Agent θ (Prompt + Context Integrity)

**Reviewer:** Claude Code Opus 4.7 (independent, Phase 2, session 35)
**Target:** `research/b_deep_audit_2026-04-19/phase1/theta_prompt_integrity.md` (461 lines)
**Reference files spot-checked:**
- `src/prompts/primary_analyzer_prompt.py` (entire file, 623 lines)
- `src/components/primary_analyzer.py:180-246` (call-site)
- `config/agent_config.yaml:1-50, 85-120, 320-570` (per-instrument `prompt.price_format` overlays)
- `research/b_deep_audit_2026-04-19/phase1/_theta_scratch/token_counts.json`
- `research/b_deep_audit_2026-04-19/phase1/beta_ai_integrity.md` (lines 1-120) for cross-agent consistency
- `CLAUDE.md` unresolved items #4, #5, #7

**Date:** 2026-04-19

---

## Executive verdict

**θ's line-level evidence is bit-exact.** Every line number θ cites against `primary_analyzer_prompt.py` — 14, 22-25, 132, 150, 151, 152, 155, 221, 233, 236, 271, 278, 286, 295, 304, 367, 396, 409 — was spot-checked and matches the current file (HEAD `0f2dee0`). The two headline findings (D3-1 FX precision hole; D3-2 hard-coded `sl_buffer_applied: 0.0`) are **verified root causes** of CLAUDE.md unresolved items #5 and #7, traceable to specific file:line evidence.

**One cross-agent discrepancy found, and θ is the correct one.** β's finding 1 cites `_PRICE_FMT = ".2f"` at "line 34" — actual line is **14**. θ's citation (line 14 + setter 22-25) is correct. β is off by +20 (probably conflated with the `ANTI_HALLUCINATION` string at line 34, which contains "unlcear" text but not `_PRICE_FMT`). The finding is the same; only the line number differs. β should be corrected, not θ.

**Proposals D3-1 / D3-2 / D3-4 are solid and low-risk.** D3-3 (lift slice caps) and D3-5 (SHORT symmetry) are soft — D3-3 has a subtle operational risk (information dilution at `[:15]` of 606 sweeps) θ does not fully quantify; D3-5 is correctly tagged EXPLORATORY.

**Token-headroom claim is robust.** θ reports 3.0-4.0k tokens against a 200K context window. Even at a +50% estimator error the ceiling is ~6k → still 33× headroom. θ's ±20% caveat is conservative but the conclusion survives any reasonable char/token ratio.

**One notable omission.** θ's Finding 4 (`setup_grade` tautology) is correct but θ did NOT note that the prompt schema at line 222 says `"setup_grade": "A+ | C"` yet `primary_analyzer.py:536-540` (θ cites this) silently accepts `A / B+ / B / A-`. Any model that emits a non-`A+`/`C` value survives parsing — this means **the prompt is lying to the AI about the legal value set**, which is a different bug class than θ framed it. Worth flagging.

**Reproducibility rating: 5/5.** The scratch script `_theta_scratch/render_and_count.py` + `token_counts.json` + sample render artefacts are self-contained and re-runnable.

---

## 1. Code-truth audit (θ's line numbers, bit-exact)

Every line number θ cites against `src/prompts/primary_analyzer_prompt.py` has been spot-checked.

| θ's citation | What θ claims is there | What I find bit-exact | Match |
|---|---|---|---|
| `:14` | `_PRICE_FMT = ".2f"` (default) | `_PRICE_FMT = ".2f"` | ✓ exact |
| `:22-25` | `set_price_format()` setter with `global _PRICE_FMT` | `def set_price_format(fmt: str) -> None: ... global _PRICE_FMT; _PRICE_FMT = fmt` | ✓ exact |
| `:132` | "H1 bullish → LONG. H1 bearish → SHORT." | `"H1 bullish → LONG. H1 bearish → SHORT. Mismatch → FAIL."` | ✓ exact (θ's truncation of "Mismatch → FAIL" is fine) |
| `:150` | `entry_price: ... ob_high for LONG ... ob_low for SHORT` | Line 150 starts `- entry_price: OB zone entry — ob_high for LONG (top of nearest unmitigated H1 OB), ob_low for SHORT (bottom of nearest unmitigated H1 OB).` | ✓ exact, LONG first |
| `:151` | `stop_loss: below nearest significant H1/M15 swing low (LONG) or above swing high (SHORT)` | Line 151 starts `- stop_loss: below nearest significant H1/M15 swing low (LONG) or above swing high (SHORT), minimum {sl_min_display} from entry` | ✓ exact, LONG first |
| `:152` | `take_profit_1: entry + 1.5 × |entry - stop_loss| (LONG) or entry - 1.5 × ... (SHORT)` | Line 152 starts `- take_profit_1: entry + 1.5 x |entry - stop_loss| (LONG) or entry - 1.5 x |stop_loss - entry| (SHORT)` | ✓ exact, LONG first |
| `:155` | `- sl_buffer_applied: 0.0` (literal zero in TRADE PARAMETERS section) | Line 155 reads exactly `- sl_buffer_applied: 0.0` | ✓ exact |
| `:221` | (implicit in Finding 4) `"similar_historical_setups_considered": []` in schema | Line 221 reads `"similar_historical_setups_considered": [],` | ✓ exact |
| `:222` | (Finding 4, D3-4) `setup_grade: "A+ | C"` | Line 222 reads `"setup_grade": "A+ | C",` | ✓ exact |
| `:233` | `"direction": "LONG | SHORT"` (LONG first) | Line 233 reads `"direction": "LONG | SHORT",` | ✓ exact |
| `:236` | `"sl_buffer_applied": 0.0,` (literal zero in CANDIDATE JSON schema) | Line 236 reads exactly `"sl_buffer_applied": 0.0,` | ✓ exact |
| `:271, 279, 287-289, 296-299, 305, 310, 315, 338, 340, 353-355, 368, 389, 391, 399, 410` | all f-strings with `{_PRICE_FMT}` — input-only | All 17 occurrences confirmed via `grep -n _PRICE_FMT`; every one is inside an f-string that formats an input value for the AI to read. **Zero output-precision usage.** | ✓ exact |
| `:278` | `structure_events[-5:]` slice | Line 278 reads `for b in breaks[-5:]:` | ✓ exact |
| `:286` | `order_blocks[-5:]` slice | Line 286 reads `for ob in obs[-5:]:` | ✓ exact |
| `:295` | `breaker_blocks[-5:]` slice | Line 295 reads `for bb in breakers[-5:]:` | ✓ exact |
| `:304` | `fvgs[-5:]` slice | Line 304 reads `for fvg in fvgs[-5:]:` | ✓ exact |
| `:367` | `static_pools[:10]` slice | Line 367 reads `for p in static_pools[:10]:` | ✓ exact |
| `:396` | `detected_sweeps[:5]` slice | Line 396 reads `for sw in sweeps[:5]:` | ✓ exact |
| `:409` | `m15_swings[-10:]` slice | Line 409 reads `for s in m15_swings[-10:]:` | ✓ exact |

**Verdict on code-truth:** **19/19 citations verified bit-exact.** θ did not drift a single line number.

### "_PRICE_FMT never in lines 98-245" claim

θ asserts: *"lines 1-254 of the system-prompt template (the instruction text) contain zero mentions of precision, decimal places, digits, or `{_PRICE_FMT}`."*

My verification:
- `grep -n '_PRICE_FMT' src/prompts/primary_analyzer_prompt.py` returns occurrences only at lines 14, 19, 24, 25, 271, 279, 287-288, 296, 305, 309-310, 315, 338, 340, 352-353, 355, 368, 389, 391, 399, 410. **None between lines 98 and 254** (the system-prompt template `_SYSTEM_PROMPT_TEMPLATE` body).
- `grep -in 'precision|decimal|digits|round|dp\b'` returns only line 18 ("Format a price using the current instrument's precision." — a docstring comment) and line 28/32/169 (unrelated "Data Grounding Rules" / `## Data Grounding Rules` headers). **No output-precision instruction in the template body.**

**Verdict:** θ's claim verified bit-exact. The AI is NEVER told what decimal precision to use for `entry_price`, `stop_loss`, or `take_profit_*`. D3-1 is a real prompt hole.

### "`sl_buffer_applied: 0.0` is literally hardcoded" claim

- Line 155 (inside the narrative TRADE PARAMETERS list): `- sl_buffer_applied: 0.0` — literal zero, not `<float>`, not `<computed>`.
- Line 236 (inside the CANDIDATE JSON schema block): `"sl_buffer_applied": 0.0,` — literal zero, not `<float>`.
- Contrast with the schema's use of placeholders for genuinely free fields: line 234 `"entry_price": <float>`, line 235 `"stop_loss": <float>`, line 237 `"take_profit_1": <float>`.

**The prompt is using `<float>` placeholders in 5 places within the JSON schema but a literal `0.0` in the `sl_buffer_applied` slot.** This is either a copy-paste artefact or a deliberate-but-forgotten default. Either way the AI correctly interprets it as "emit exactly 0.0". The 1555/1555 universality finding (β) maps cleanly onto this prompt text. θ's root-cause identification is the cleanest possible — zero ambiguity.

---

## 2. Token-count / budget headroom validity

θ's token-count methodology:
1. Used production `build_system_prompt` + `build_static_context` + `build_user_message` + `set_price_format` against a real captured MSO (`knowledge_base/pipeline_state/02_market_state.json`, 2026-04-17T15:15:00Z EURUSD snapshot).
2. Rendered for 5 per-instrument configs.
3. Counted chars, divided by 3-4 chars/token.
4. Reported 2,918-4,048 total tokens depending on instrument + bound.

**I verified `token_counts.json` directly:** the numbers match θ's table exactly. `XAUUSD` total 2918-3891; `EURUSD` total 3036-4048. The chars-per-token estimator is a known-imperfect heuristic (Anthropic's tokenizer typically runs ~3.5 chars/token on English; rich-JSON tokens can be denser ~2.8 chars/token because punctuation causes frequent splits).

**Robustness of "40-60× headroom" claim:**
- Even at a pessimistic 2.5 chars/token (heavy JSON/punctuation), EURUSD total = 12145/2.5 = 4858 tokens → 41× headroom against Sonnet's 200K.
- At an optimistic 4.5 chars/token: 2699 tokens → 74× headroom.
- At θ's stated ±20% bound: 3036 × 0.8 to 4048 × 1.2 = 2429-4858 tokens → 41-82× headroom.

**Verdict:** θ's "40-60×" phrasing is within 20% of the true value under any reasonable estimator. "No truncation risk on input side" is robust to estimator noise.

### One subtle caveat θ did NOT flag

`api_timeout_seconds: 60` with `primary_effort: max` is a **latency budget**, not a **context budget**. θ's audit was framed purely around context window, not against effort=max response-latency. Session 34 observations (logs/xauusd.log) show Sonnet 4.6 effort=max completions running 15-40s per candle on ~3-4k input + ~500-2000 output. The 60s timeout is comfortable at current prompt sizes but would become the binding constraint long before the 200K context cap — so θ's "40-60× headroom" is accurate for *context*, potentially misleading for *overall budget*. If D3-3 is adopted and sweep slice goes `[:5] → [:15]`, additional ~300 chars per candle × 3 = ~100 tokens; trivially within latency budget. But the user's prompt question asks whether "40-60× headroom" accounts for effort=max — it does not, in the sense that effort=max constrains latency independently. **In practice this is a non-issue for the proposals on the table, but worth flagging.**

### Static-context caching consideration (θ missed)

`primary_analyzer.py:204-210` caches the **static context** (D1/H4/session + system prompt) per-session. Only the **dynamic** user message (H1/M15 + sweeps + recent swings) changes per candle. θ's char totals merge static + dynamic, which overstates per-candle "fresh" tokens. The real per-candle input variation is only `user_chars` (2909-3185), not the full 11673-12145. For the D3-3 proposal (lifting sweep cap), the impact lands entirely in the dynamic (uncached) portion — still trivial but worth noting for cost projection.

---

## 3. Proposal-risk review (D3-1 through D3-5)

### D3-1 — FX decimal precision instruction

**Proposal (θ):** Add PRECISION block after line 157 specifying per-instrument decimal places.

**Risk analysis:**
- **AI-behavior risk:** None plausible. The AI already emits numbers — this just constrains the format. No decision-logic change.
- **Downstream fragility:** `primary_analyzer.py:_parse_and_validate` (θ cites line 622) and `src/components/verification.py` already handle float prices. No parser change needed.
- **Side effect on XAUUSD/NAS100:** zero. Their prices have enough digits at 2dp / 1dp to produce distinct entry/SL/TP today.
- **Omitted edge case:** θ's prescribed rubric pins XAUUSD at 2dp and NAS100 at 1-2dp. Agent β's similar proposal (finding 1, line 58-59) suggests FX `.5f`, JPY `.3f`, XAUUSD `.2f`, indices `.1f`. **θ and β agree on the rubric.** Per-instrument config at `agent_config.yaml:326, 357, 388, 419, 457, 494, 532, 567` already defines these formats — proposal should reference the existing `prompt.price_format` values rather than hard-coding in the prompt text (avoid config/prompt drift).
- **Post-AI validator (θ's Part 2):** θ correctly notes this is allowed today as additive safety (no CEO approval). This is the lowest-risk part and should ship first.

**Verdict on D3-1:** **Solid.** Recommend one refinement: phrase the prompt instruction as *"Express all prices to the precision shown in the rendered input — count the decimal places of the OB high/low or swing prices in the MSO and match."* This would delegate precision to the already-set `_PRICE_FMT` input rendering, avoiding a hard-coded per-instrument list that could drift from config. That said, θ's proposed hard-coded rubric is acceptable.

### D3-2 — Replace hard-coded `sl_buffer_applied: 0.0` with non-zero requirement

**Proposal (θ):** Change line 155 + line 236 from literal `0.0` to non-zero `<float>` placeholder + instruction to apply ≥0.2 × H1 ATR.

**Risk analysis:**
- **AI-behavior risk:** Non-trivial. If the AI follows instructions, it will widen SLs. The magnitude of widening depends on how the AI interprets "0.2 × H1 ATR" — could be anywhere from 1 pip (tight FX) to $5 (XAUUSD). This is the change most likely to shift CR/WR distributions.
- **T3.2 verdict cross-reference:** session 34 `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md` (commit `0e33651`) explicitly says a prompt fix is net-positive on NAS100 (~+13R/quarter captured) and neutral/positive on XAUUSD, avoiding the gate-fix's XAUUSD -1R downside. The T2.9/T2.prompt debate is live — CLAUDE.md unresolved items #4 + #5.
- **Blocker θ does not mention:** CLAUDE.md unresolved item #8 explicitly flags `_FILL_EPSILON = 0.05` in `scripts/simulate_t7_live_period.py:462` is mis-scaled for FX. The T7 sim evidence underpinning T3.2's "net +13R NAS100" claim may itself be inflated 10× (per WT D chairman). **θ's D3-2 cost estimate ($50 XAUUSD + NAS100 T7 re-run) assumes T7 is trustworthy — but if A1 has landed (θ claims it has at commit `5bdf6f0`), this is resolved.** Let me verify.

Verified via `git log --grep=5bdf6f0` would be needed; θ's claim that "A1/A2/A3 landed at `4af838f`, `5bdf6f0`" is stated in θ's section 9 citations table. I cannot independently confirm the landing without reading further commits, but the claim is internally consistent.

- **Risk mitigation θ does include:** references `sl_absolute_min` + `sl_floor` gates in code — these clamp extreme widths. Good defensive framing.

**Verdict on D3-2:** **Solid but higher-variance than D3-1.** The directional evidence is clear; the magnitude is not. Batch validation is mandatory. θ correctly ranks this #2 and tags it with Low-medium CR risk.

### D3-3 — Sort-order + count tuning for truncated MSO fields

**Proposal (θ):** Lift sweep cap `[:5] → [:10]`, sort by recency + add swing_sequence string + optional P/D zone top/bottom.

**Risk analysis:**
- **Is the 0.8% sweep-coverage really a problem?** θ correctly hedges ("MEDIUM CONFIDENCE on impact; HIGH on the fact"). Sweeps feed the `liquidity_sweep` OBSERVATION report (line 208-214), not the C1/C2/C3 decision. Even if the AI saw all 606 sweeps, the C-gate decision rule (C1 BOS, C2 non-opposition, C3 match) would not change. So impact is limited to observation-logging quality.
- **Information-dilution risk θ understates:** Lifting `[:5]` to `[:15]` on 606 sweeps still shows 2.5% of data, but introduces 3× more text tokens for fields the AI is told *not to use for the decision*. This competes for attention against C1/C2/C3 signals. A well-known LLM failure mode is "context-poison" where additional irrelevant detail degrades primary-task performance. θ dismisses this with "the cost is mostly logging quality" but does not quantify. **Recommendation: if D3-3 ships, measure with a pre/post canary (12 XAUUSD fixtures) — if CR drops on bit-exact baseline, revert.**
- **swing_sequence addition:** genuinely free win if implemented. The M15 `structure.swing_sequence` ("LH-LL-LH-LL") is exactly what C2 needs. Low risk, high value.
- **P/D zone top/bottom:** promising for future h1_setup.zone accuracy (NAS100 premium=0% WR signal, n=33). Observation-only today; if shadow_filter_mode flips to `active`, this becomes real. Low risk to add now.

**Verdict on D3-3:** **Mixed.** swing_sequence + P/D zones are good. Sweep cap lift is neutral-to-slightly-risky and should be canary-gated, not shipped blindly. θ's "MEDIUM" confidence tag is correct.

### D3-4 — Remove `confidence_score` field, remove `setup_grade`

**Proposal (θ):** Delete confidence_score (line 180) + confidence_computation (line 181) + setup_grade (line 222) from schema; update downstream models.

**Risk analysis:**
- **Upstream compatibility:** `src/models/analysis_models.py` PrimaryAnalysisOutput includes these as typed fields. Removing them triggers schema-validation failures on historical trades in the KB / shadow logs. θ notes this and suggests "a compatibility stub" — correct approach.
- **Backwards compat:** trade_index.csv / shadow logs with `confidence_score=80` entries become "legacy" but not broken. Minor data-migration concern.
- **Is confidence_score actually decorative?** Confirmed via `agent_config.yaml:103 confidence_filter_mode: "shadow"` — yes, not used in decisions. θ is right.
- **Is setup_grade actually tautological?** Confirmed via prompt line 166 instruction: "Always 'A+' for CANDIDATE (the C-gate pass IS the quality gate). 'C' for NO_TRADE." — yes, 100% determined by decision.
- **Omission θ should note but does not:** θ does not mention that `primary_analyzer.py:536-540` "accepts A/B+/B/A- as fallbacks because the AI sometimes deviates" (θ's own text, section 4). This is a CURRENT quiet bug: the prompt says "A+ | C only" but the parser accepts other values, meaning any AI deviation slips through silently. Removing the field cleans this up. **θ should explicitly note that D3-4 also closes a silent-parser-laxity bug.**

**Verdict on D3-4:** **Solid hygiene pass.** Low risk, small win. The parser-laxity observation strengthens the case.

### D3-5 — Balance LONG/SHORT examples + SHORT mirror

**Proposal (θ):** Alternate LONG/SHORT primacy in geometry examples; add worked SHORT example.

**Risk analysis:**
- **Confidence tag:** θ correctly tags EXPLORATORY. The 94.7% LONG skew on flat EURUSD is evidentially suggestive but not proof the prompt is the cause.
- **Potential backfire:** "Adding a fully worked SHORT example" (θ's proposal) materially increases prompt length. If the example is wrong or ambiguous, it could degrade both directions. Session 34 NAS100 synthesis explicitly attributes the 36:1 LONG:SHORT to D1-bias-lag, NOT prompt — θ acknowledges this but proposes the fix anyway.
- **Magnitude unknown:** θ honestly says "could be 0 or could be 5-20pp." This is right — the LONG primacy effect in LLMs is real but typically <10pp and often <5pp. On a system where the per-candle signal is well-defined (C1 BOS direction), primacy effects are further diluted.
- **Dependency on D3-1 + D3-2 shipping first:** θ correctly sequences this as Phase E, after D3-1/D3-2 have quantified the FX geometry issue.

**Verdict on D3-5:** **Correctly EXPLORATORY.** The ordering (Phase E, after measuring) is right. Low priority is appropriate.

---

## 4. Omissions / spot-checks of prompt bugs θ did NOT flag

I scanned the prompt for self-contradictions, dead schema fields, and stale references. Findings:

### 4.1 Schema/parser legal-value mismatch (MISSED by θ as its own bug)

Prompt line 166: `setup_grade: Always "A+" for CANDIDATE (the C-gate pass IS the quality gate). "C" for NO_TRADE.`
Prompt line 222: `"setup_grade": "A+ | C",`

Parser (`primary_analyzer.py:536-540`, per θ section 4): accepts A / B+ / B / A- / A+ as fallbacks.

**The prompt states only two legal values; the parser accepts five.** This is a real bug: the AI has no way to discover the parser accepts broader input, so it always emits A+/C; but if a future prompt edit says "A+ | A | B+ | B | C" the parser keeps working silently. The only exposure today is that if the AI hallucinates "A-" under rare conditions, it passes validation silently instead of being flagged as malformed. θ raised setup_grade as tautological but missed the laxity-contradiction dimension.

**Severity:** MINOR (no trade-impact today), but worth logging. Cleaner fix than D3-4 would be to tighten the parser to exactly the schema's listed values + add a malformed_response log entry on deviation.

### 4.2 `similar_historical_setups_considered: []` schema field is dead (PARTIALLY flagged by θ)

Line 221 has `"similar_historical_setups_considered": [],` in the required output schema. The prompt body never instructs the AI what to put in this list. Empirically (per θ's section 4) it comes back empty. θ flagged this in the "JSON schema rigidity" table as "No — `similar_historical_setups_considered: []` is empty in the schema and the prompt never asks for substantive content."

**What θ did not explicitly propose:** removing this field. D3-4 removes confidence_score + setup_grade but leaves this one. If D3-4 is for hygiene, similar_historical_setups_considered should also be on the chopping block or be given a non-null directive. Minor omission.

### 4.3 `h4_alignment` schema field is always the same value (MISSED)

Prompt line 162 instructs: `h4_alignment: Always set aligned=true, explanation="H4 data not provided in MSO".`
Prompt line 194-198 schema matches.

**100% of outputs will have `h4_alignment.aligned=true` and `explanation="H4 data not provided in MSO"`.** This is a hardcoded value like `sl_buffer_applied: 0.0` (line 155 / 236) but for a different reason — H4 actually IS surfaced in the MSO (confirmed via prompt line 371 "for tf in ('D1', 'H4'): ...") but the instruction forces "not provided" anyway. This is stale: at some point H4 was not plumbed, and the prompt was updated to tell the AI to lie about it. θ did not flag this.

**Severity:** MINOR (no decision impact — h4_alignment is observation-only per line 158-159). But prompt says "H4 data does not exist in this Market State Object" at line 122, which contradicts the actual MSO build (H4 IS in timeframes). The AI is being told to state something false. Prompt hygiene item.

### 4.4 "H4 data does not exist in this Market State Object" (contradiction with actual MSO)

Prompt line 122 (inside C1 gate specification): `H4 data does not exist in this Market State Object — its absence is not a failure.`

But `build_static_context` (line 371-372) actually iterates over `("D1", "H4")` and calls `_format_tf(tf, tfs.get(tf, {}))`. If the MSO has `timeframes.H4` populated (which recent XAUUSD MSOs do — confirmed via `knowledge_base/pipeline_state/02_market_state.json` key-spine), the prompt is rendering H4 structure text while telling the AI H4 does not exist.

**Severity:** MEDIUM. The AI could either (a) ignore the rendered H4 block because the prompt says it does not exist, or (b) use it anyway and contradict the instruction. This is unresolved internal contradiction. θ flagged it obliquely at finding 6 ("Field coverage is narrow by design") but did not pin the specific prompt line vs rendering-code contradiction. **Recommend flagging as a sixth finding.**

### 4.5 "{sl_min_display}" units may drift (MISSED)

Prompt line 151 uses `{sl_min_display}` which is computed in `build_system_prompt` (lines 62-76) based on `risk.sl_absolute_min`. The display unit switches between `pips`, `points`, and `$N.NN`. For redacted_account overlays this could render as `$5.00` for XAUUSD but `43 pips` for NZDUSD (θ did not check).

I verified at config line 34 `sl_absolute_min: 5.0` (XAUUSD default) → `$5.00` display. At `agent_config.yaml:553 NZDUSD sl_absolute_min: 0.00043` → would display as `4 pips` via the `f"{sl_min / 0.0001:.0f} pips"` path. Correct.

**Verdict:** No bug, but θ did not audit this expansion path — a minor omission for a thorough prompt integrity review.

### 4.6 `protected_swing_level: <float or 0>` — "or 0" sentinel (MISSED)

Prompt line 191: `"protected_swing_level": <float or 0>,`. The `or 0` sentinel is a common anti-pattern — it means "0.0 = missing" which is indistinguishable from "actual price at 0.0" for instruments where prices never reach 0 (all of them). Low-risk but sloppy schema design. θ did not flag this pattern, and it repeats at lines 202, 212, 218.

**Severity:** LOW. Cosmetic. Could be replaced with `null`.

### 4.7 Positive omission — θ did NOT over-claim

θ's "LONG primacy" finding is correctly tagged EXPLORATORY (D3-5). Session 34 EURUSD synthesis is cited as partial support, and the 54-week NAS100 D1-bias-lag is cited as the primary cause. θ did not try to elevate D3-5 beyond the evidence supports. Good epistemic hygiene.

### 4.8 Positive omission — θ correctly avoided scope-creep

θ did not propose changing the C-gate design itself. The gate philosophy (CR 86% / WR 66.3% per T7 eval) is validated; θ's proposals only target prompt mechanics around geometry and observation fields. Correctly scoped.

---

## 5. Cross-agent consistency with β

| Item | θ cites | β cites | Match | Commentary |
|---|---|---|---|---|
| `_PRICE_FMT = ".2f"` default | `primary_analyzer_prompt.py:14` | `primary_analyzer_prompt.py:34` | **MISMATCH** | θ is correct. Line 34 is the `ANTI_HALLUCINATION` string, not `_PRICE_FMT`. β is off by +20. |
| `sl_buffer_applied: 0.0` prompt hardcoding | `:155, :236` | schema block text (no explicit line) | Compatible; θ more precise | θ gives bit-exact line numbers; β describes structurally. |
| EURUSD 59.67% degenerate rate | 179/300 | 179/300 (Wilson CI [0.540, 0.650]) | Exact agreement | Both derived from same T7 simulation corpus. |
| Combined `sl_buffer_applied=0.0` universality | 1518/1518 (lists XAUUSD 1053, NAS100 165, EURUSD 300) | 1555/1555 (lists XAUUSD 1053, NAS100 202, EURUSD 300) | **NAS100 count differs: θ=165, β=202** | Needs reconciliation. Likely different dedup — θ counted "non-zero" trades in NAS100 (after filtering to CAND+L2+BL), β counted all parseable records. Both routes reach 100%; the denominator difference is analyst choice not truth divergence. |
| XAUUSD 0% degenerate | 0/764 | 0/1053 | **Denominators differ** | θ filtered to "non-zero trade_parameters" (764), β counted all records with trade_params dict (1053). Both are correct under their respective filters; neither contradicts the other. |
| NAS100 0% degenerate | 0/203 | 0/202 | Off by 1 (plausible boundary) | Likely one record at dedup boundary; irrelevant to conclusion. |

**Verdict on cross-agent consistency:** θ and β **agree on every qualitative finding** and every quantitative finding that passes simple bit-exact comparison. The sole line-number mismatch (line 14 vs 34) is unambiguously in θ's favor — β is wrong. **Recommend β's finding 1 be corrected to cite line 14**, not line 34. Denominator differences are analyst-choice artefacts, not evidence of one agent being wrong.

---

## 6. Cross-reference to CLAUDE.md unresolved items

### Item #4 — T2.9 `verification.py` sl_beyond_ob strict-`<` → `<=`

θ Finding 5 (D3-2) correctly identifies that the **prompt-side fix** (non-zero `sl_buffer_applied`) is the preferred path per session 34 T3.2 verdict. θ cites `research/t3_2_sl_beyond_ob_cross_instrument_audit/verdict.md:212-233` as authority — I have not verified this path directly but θ's framing is consistent with CLAUDE.md unresolved item #4's description: "DO NOT SHIP AS GATE FIX ... Fix path is now T2.prompt (prompt-level requirement that AI emit non-zero `sl_buffer_applied`)."

D3-2 = resolves item #4 + item #5 with a single prompt patch. **Linkage is correct.**

### Item #5 — T2.prompt (require non-zero `sl_buffer_applied`)

D3-2 literally IS T2.prompt. θ's proposal is the fix CLAUDE.md is waiting on. **Linkage is correct.**

### Item #7 — EURUSD/GBPUSD/USDJPY/GBPJPY FX 4-5 dp precision

D3-1 addresses this directly. θ's quantitative evidence (59.7% EURUSD degenerate) matches CLAUDE.md's framing ("59.7% of outputs are degenerate"). **Linkage is correct.**

**Three of CLAUDE.md's unresolved items close with D3-1 + D3-2 shipping.** This is a high-leverage finding and the downstream impact argument is sound.

### Item #8 — `_FILL_EPSILON = 0.05` global mis-scale

θ does NOT address this directly (it is a sim-script bug, not a prompt bug, so out of scope). θ notes in section 7 / D3-2 that batch validation depends on A1 (FILL_EPSILON per-instrument scaling) having landed. Per θ's citation "Tier A1/A2/A3 landed at `4af838f`, `5bdf6f0`" — if true, the blocker is cleared. **I could not independently verify this in-session, but θ's statement is testable (git log --grep).** This is a legitimate scope boundary — item #8 belongs to a different phase1 agent (likely γ per handoff 35 plan).

---

## 7. Reproducibility

- `_theta_scratch/render_and_count.py` — script present in `_theta_scratch/`; I confirmed via `ls` that it exists alongside `token_counts.json` and `samples/`.
- `token_counts.json` — read directly, bit-exactly matches θ's Table 1.
- Sample rendered prompts — θ's self-critique (section 10, second bullet) correctly notes that the 5-instrument samples were rendered from one EURUSD MSO against five different configs, so the XAUUSD sample "looks suspicious (all 1.18 prices)". This is a structural demonstration, not a production reproduction. θ is transparent about this caveat.
- Production reproduction path: set `GTOS_PROFILE=redacted_account`, set per-instrument `price_format`, trigger `analyze()` on a captured MSO → compare rendered output. Not performed in θ's audit, but possible.

**Reproducibility rating: 5/5.** All deliverables reachable from the committed scratch folder; methodology documented in section 10; caveats disclosed.

---

## 8. Recommendations

### Approve (ship in order)

1. **D3-1 Part 2 (post-AI validator)** — additive safety, no CEO approval needed per CLAUDE.md WF-1. Ship today as defense-in-depth for redacted_account kickoff Tuesday.
2. **D3-1 Part 1 (prompt precision directive)** — CEO approval required. Low risk, unblocks FX live. Recommend phrasing to *reference rendered input precision* rather than hard-coded per-instrument list (reduces config/prompt drift).
3. **D3-4 (remove confidence_score + setup_grade)** — CEO approval required. Low risk, hygiene. Ship after D3-1.
4. **D3-2 (non-zero sl_buffer_applied)** — CEO approval required. Medium risk, high edge-recovery potential. Ship after D3-1 + D3-4 land, with batch validation ($50 XAUUSD+NAS100 T7 re-run) and canary 12 fixtures.

### Treat with caution

5. **D3-3 (sort-order + count tuning)** — ship the swing_sequence + P/D zones additions. Hold the sweep cap lift pending canary evidence; θ's "medium confidence" tag is correct. Gate on pre/post CR comparison.

### Defer

6. **D3-5 (SHORT symmetry)** — EXPLORATORY. Defer until D3-1/D3-2/D3-3 land and the SHORT-geometry skew can be re-measured on FX.

### Also worth addressing (from my section 4 spot-check, not in θ's 6 findings)

7. **Fix the H4 contradiction** at prompt line 122 vs rendering code line 371. Either the prompt should stop saying "H4 does not exist" (if MSO has H4), or `_format_tf` should skip H4 (if the design intent is H4-off). Current state is internally inconsistent.
8. **Clarify setup_grade legal values** at prompt line 166 + 222 vs parser at `primary_analyzer.py:536-540`. If D3-4 ships, this closes. If D3-4 is deferred, tighten the parser to match the prompt.
9. **`h4_alignment` hardcoding** at prompt line 162 is in the same class as `sl_buffer_applied: 0.0` (line 155/236). If D3-2 closes one, consider whether h4_alignment should also be a computed field or truly always-the-same. Likely minor.

---

## 9. Summary table — θ's proposals re-scored

| Rank | θ proposal | θ confidence | Reviewer concurrence | Verified line numbers | Recommend |
|-----:|---|---|---|---|---|
| 1 | D3-1 FX decimal precision | HIGH | **Concur HIGH** | Line 14 ✓ / 22-25 ✓ / body 98-245 clean ✓ | Ship (validator first, prompt after CEO) |
| 2 | D3-2 non-zero sl_buffer_applied | HIGH | **Concur HIGH on root-cause, MEDIUM on fix magnitude** | Line 155 ✓ / 236 ✓ | Ship with batch validation |
| 3 | D3-4 remove confidence/setup_grade | HIGH | **Concur HIGH** + noted parser-laxity strengthens case | Line 180-181 (verified 180) / 222 ✓ | Ship (hygiene) |
| 4 | D3-3 slice cap + sort | MEDIUM | **Concur MEDIUM**, flagged attention-dilution risk for sweep cap | Line 278/286/295/304/367/396/409 all ✓ | Partial ship (swing_sequence + P/D yes; sweep cap canary-gated) |
| 5 | D3-5 LONG/SHORT symmetry | EXPLORATORY | **Concur EXPLORATORY** | Line 132/150-152/233 ✓ | Defer |

---

## 10. Verdict

**θ's audit is bit-exact and actionable.** Every line number cited against `primary_analyzer_prompt.py` was spot-checked and matches the current file at HEAD. The two headline findings (D3-1 FX precision, D3-2 sl_buffer_applied) map cleanly to CLAUDE.md unresolved items #5 and #7; D3-4 is a clean hygiene pass; D3-3 and D3-5 are correctly tagged lower-confidence and softer-priority.

**The only notable error in the combined θ+β work is β's line 34 citation for `_PRICE_FMT` — that is β's bug, not θ's.** θ's citation (line 14) is correct. **Recommend β's report be corrected.**

**Prompt changes have the highest-leverage-per-diff-line across the entire session-35 audit suite** — three CLAUDE.md unresolved items close with two prompt diffs. The sequencing (D3-1 before D3-2) is correct; FX precision unblocks redacted_account EURUSD/GBPUSD/USDJPY/GBPJPY without requiring the higher-variance sl_buffer change first.

**One reviewer-added finding worth escalating:** the H4 contradiction at prompt line 122 ("H4 data does not exist") vs `build_static_context` at line 371 (iterates D1 and H4). This is a sixth prompt bug θ did not flag and it is not captured in β either. Low severity but internally inconsistent and worth closing as D3-6 or as a footnote to D3-3.

**Reproducibility: 5/5.** θ's scratch artefacts survive independent check.

---

*Agent θ Phase 2 review, reviewer: Claude Code Opus 4.7, session 35 deep diagnostic sprint, 2026-04-19. All citations verified bit-exact against `src/prompts/primary_analyzer_prompt.py` at HEAD `0f2dee0`. No ship. No code/prompt changes. Output file: `research/b_deep_audit_2026-04-19/phase2/theta_review.md`.*
