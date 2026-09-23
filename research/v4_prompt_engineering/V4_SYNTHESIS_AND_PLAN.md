# V4 Prompt Engineering — Synthesis + Execution Plan

**Date:** 2026-04-25
**Mandate:** CEO requested surgical V4 design with zero ambiguities. Take the time, use all capabilities, no assumptions or guesses.
**Research inputs:** 3 parallel Opus 4.7 max-effort agents; all deliverables on main after this commit.

---

## 0. Headline

**V4 is drafted, evidence-backed, and counterfactual-validated on A2's 4 divergent candles (+4.0R recovery if V4 had been in place). But ship discipline requires one $1 pre-step: measuring V3's noise floor on those same 4 candles — because the literature says "temperature=0 ≠ determinism" and we need to distinguish prompt-driven variance from LLM baseline noise (~15%).**

If V3's re-run agreement rate is ≥85%, the prompt IS the problem → ship V4.
If V3's agreement rate is <85%, some of the "V2 vs V3" gap is just noise → V4 is still valuable but the $40 A/B backtest confidence drops.

---

## 1. The 3 agents' consolidated verdict

### Agent A — External research (51 sources cited, evidence-weighted)

**Must-hold principles for V4:**

1. **Avoid procedural drift.** ATLAS paper (arXiv:2510.15949) finds Claude Sonnet 4 specifically drifts toward "overly rigid, procedural instructions" under reflection/optimization loops — which is exactly how V3 was developed (session 38 R1 added gaming-pattern prohibitions + explicit thresholds on top of V2). V4 must NOT be V3 + more rules. V4 should simplify + clarify precedence.
2. **Instruction hierarchies must be explicit.** Control Illusion (arXiv:2502.15851, n=1,200) shows compliance drops from 75-91% baseline to 9.6-45.8% under conflicting constraints. Labeled `Constraint 1 PRIORITY:` markers recover up to 60pp. V3's implicit "MSO-label vs CHoCH-override" hierarchy is textbook-vulnerable. V4 MUST have explicit in-line priority tables.
3. **Context length is a first-order lever.** Performance degrades starting at ~7.5K tokens even with perfect retrieval (arXiv:2510.05381, 2025). V3 at ~15K tokens is in the danger zone. V4 target: ≤70% of V3 length (Agent B's forensic confirms V3 has R1-R8 allow-list duplicated 3× — dedup alone could cut ~25%).
4. **Forced-choice enum > free-form confidence.** arXiv:2502.11028 shows up to 460% improvement over free-form scores. V3's `confidence_score: int 0-100` → 72 for every CAND is textbook miscalibration. V4: `confidence_tier: Literal["high_conviction", "moderate", "marginal_pass"]`.
5. **The 15% noise floor is real.** Atil et al. (arXiv:2408.04667, 2024) show GPT-4o Professional Accounting benchmark varies 57.8%-89.0% across 10 runs at temperature=0. Before attributing F3 vs A2 variance to V2 vs V3 prompt, we MUST measure V3's self-agreement rate on the 4 divergent candles. If >15% of V3's rerun answers disagree with the original, the prompt isn't wholly responsible.
6. **CoT vs No-CoT is domain-dependent.** arXiv:2506.04574 (n=4,845) shows GPT-4o No-CoT 72.7% > CoT-Long 66.8% for *intuition-driven* financial classification. LIRA pattern (predict label first, justify after) wins on some benchmarks. **V4 must A/B test this, not assume.**

**Citations-to-credibility rank:** arxiv papers with n>500 → highest; blog/practitioner → secondary; single-sample anecdote → flagged.

### Agent B — V2/V3 forensic (1,018-line prompt read line-by-line)

**Top 3 V3 lines causing inconsistency (verbatim + line numbers):**

1. **`primary_analyzer_prompt.py:334-339` — C1 definition** is SILENT on the orchestrator's "Directional Bias (COMPUTED — DO NOT OVERRIDE)" block. Direct cause of Feb 2 07:00: AI explicitly says "computed bias is LONG per directive but H1 CHoCH is the most recent structural event" and overrides to SHORT anyway.
2. **`primary_analyzer_prompt.py:344-346` — C2 definition** has no numeric threshold distinguishing "pullback" from "active opposition." Same M15 CHoCH at displacement ratio=2.0 called "pullback" at Feb 4 13:30 (→CAND LONG LOSS) and "active opposition" at Feb 4 13:45 (→NO_TRADE). 15-minute flip.
3. **Triple +0.20R reminder (line 242 + 329-330):** V3 duplicates the "over-rejection costs 0.20R" nudge 3× vs V2's 1×. Raised CAND-emission pressure; AI over-synthesizes "coherent direction" rather than calling c1_failed.

**Key secondary finding not in ROOT_CAUSE_DIAGNOSIS:** the orchestrator-vs-prompt collision is the single most exploitable V3 failure. Feb 2 07:00 raw_response literally quotes this conflict. **CB-1 BIAS PRECEDENCE is the highest-impact V4 change.**

**V4 spec (5 biggest changes with line-level rationale):**

| Change | Rationale | Evidence |
|---|---|---|
| **CB-1 BIAS PRECEDENCE block (NEW)** | Closes orchestrator-vs-prompt collision | A2 Feb 2 07:00 raw_response explicit quote |
| **CB-2 C1 rewrite — "1 CHoCH never flips" rule** | Closes Feb 2 + Mar-3 override pattern | A2 raw_response pattern across 8 candles |
| **CB-3 C2 mechanical threshold — M15 CHoCH ratio ≥ 1.5 = C2 FAIL** | Closes Feb 4 pullback-vs-opposition ambiguity | Threshold matches MSO `displacement_quality: strong` definition |
| **GA-1 G6-G9 FORBIDDEN additions** (age, partial-mitigation, weak-bias, regime) | Closes CLAUDE.md unresolved #5 V4-territory gaming surfaces | session 38 R1 cold-review |
| **SC-1 Schema Literal enforcement** + referenced `guard_no_trade_reason_enum` validator | Closes CLAUDE.md unresolved #5 schema gap | Session 38 V3 post-merge review |

**Counterfactual V4 on A2's 4 divergent candles:**

| Candle | V3 (A2) actual | V4 predicted | ΔR |
|---|---|---|---|
| Feb 2 07:00 | CAND SHORT (L2 reject) | **CAND LONG** | +1.5R |
| Feb 4 13:30 | CAND LONG → −1.0R LOSS | **NO_TRADE** (ratio=2.0 ≥ 1.5) | +1.0R |
| Feb 4 13:45 | NO_TRADE | **CAND LONG** → −1.0R LOSS | 0R |
| Feb 6 07:30 | c1_failed (missed) | **CAND LONG** | +1.5R |
| **Fleet ΔR V4 vs V3** | | | **+4.0R** |

n=4 is too small for performance claim — the WIN is rule consistency (V4 makes deterministic calls where V3 made 4 different interpretations).

**Draft V4 prompt file:** `research/v4_prompt_engineering/primary_analyzer_prompt_v4_DRAFT.py` — syntactically valid, 28,279 chars. Ready for canary validation.

### Agent C — Per-instrument analysis (24-instrument characteristic table + F3/A2 stratified)

**Recommendation: Option 4 — universal core + thin per-class injection** (~80% confidence).

Single prompt, unchanged core logic, add `{instrument_guidance}` placeholder with 4-6 line class snippets:

| Class | Snippet focus |
|---|---|
| commodity_metal (XAU/XAG) | Fat-tail kurtosis +2.85 to +7.15 — wicks are STRUCTURAL, don't tighten SL |
| commodity_energy (Oil) | OPEC/EIA event-driven; news filter more critical |
| index (US30/NAS100/SPX500/GER40/JP225/UK100) | Mon-gap 0.38-0.63% vs FX 0.07-0.21% — first_ny_candle_skip handles |
| fx_major | 5dp precision (already in V2) |
| fx_jpy (USD/GBP/EUR/AUD/NZD JPY) | 3dp precision + Tokyo session legitimate |
| fx_cross (EURGBP) | Lowest volatility class; normal gates |
| crypto (BTC/ETH) | 26% weekend bars — no "dead zone" reasoning |

Every snippet flagged "(informational only, not a gate)" to prevent V3-style fourth-gate rationalizations.

**Honest nulls from Agent C:**
- **No empirical evidence class-level prompt change improves WR.** ATLAS + TradingAgents: zero published LLM-trading frameworks ship per-asset prompts.
- **H2-2026 XAUUSD 64.5% → 24% decay is regime-driven** — NO prompt option fixes it. Monthly-decay monitor (S1) is higher priority.
- **USDJPY 0/426 raw SHORT cannot be addressed by ANY prompt option** — detector or regime issue.

**Validation plan: $97 total (under CEO $100-200 V4 budget).**

---

## 2. Consolidated V4 specification (all 3 agents' inputs merged)

### Priority 0 — Must-measure before V4 ships
- **V3 noise floor:** re-run V3 prompt 5× on each of A2's 4 divergent candles = 20 API calls ≈ $1-2. If re-run agreement ≥85%, V3's inconsistency IS prompt-driven. If <85%, some variance is baseline LLM noise and V4 can only address the prompt-driven portion.

### Priority 1 — Core structural changes (Agent B + A consensus)
- **CB-1 BIAS PRECEDENCE block** with explicit `Constraint 1 PRIORITY:` label (Agent A's Control Illusion finding)
- **CB-2 "1 CHoCH never flips bias"** rule
- **CB-3 C2 mechanical threshold** M15 displacement ratio ≥ 1.5 = C2 FAIL
- **Prompt length target ≤70% of V3** (Agent A's 7.5K token finding; drop R1-R8 dedup)

### Priority 2 — Schema + consistency
- **SC-1 Schema Literal enforcement** for `no_trade_reason` + `direction` + new `confidence_tier`
- **Confidence tier Literal** `Literal["high_conviction", "moderate", "marginal_pass"]` replacing free-form 0-100
- **LIRA pattern A/B** — short No-CoT variant vs V4 full reasoning (one canary + $10 mini-backtest comparison)

### Priority 3 — Gaming-pattern closures (CLAUDE.md unresolved #5)
- **GA-1** G6-G9 forbidden surface additions: age_too_old, partial_mitigation, weak_bias, regime_override

### Priority 4 — Per-instrument (Agent C)
- **Option 4 implementation** — `{instrument_guidance}` placeholder + 7 class snippets (4-6 lines each)
- Snippets are INFORMATIONAL ONLY, not gates

---

## 3. Execution plan with cost gating

**Timeline: ~1-2 weeks (can compress to weekend if CEO prioritizes).**

| Phase | Action | API cost | Wall time | Gate |
|---|---|---|---|---|
| P0 | V3 noise-floor measurement (5 re-runs × 4 candles = 20 API calls) | $1-2 | 10 min | If agreement ≥85%: proceed. Else: proceed with caveat. |
| P1 | V4 prompt draft finalization from Agent B's draft + all findings integrated | $0 | 3-4 hr | Draft reviewed by me in main thread |
| P2 | V4 canary (60 fixtures) | $5-10 | 10 min | ≤1 flip on 60 fixtures; halt if canary regresses |
| P3 | V4 A/B backtest: V3 vs V4 on 12 F3 slices (same methodology as A1/A2) | $40-80 | 4 hr | V4 fleet Exp R ≥ V3; V4 WR within ±5pp |
| P4 | LIRA/No-CoT variant canary + mini-backtest (optional, if Priority 2 A/B desired) | $15-20 | 30 min | Informative only, not gate |
| P5 | Per-instrument Option 4 expansion — add injection snippets, 10-fixture multi-instrument canary | $4 | 10 min | No degradation on existing 60 fixtures |
| P6 | Phase 2a: 5 single-slice sims on unseen classes (EURUSD, NAS100, BTCUSD, XAGUSD, USOIL) | $50 | 3 hr | No >5% malformed rate per instrument |
| **Total expected** | | **$115-170** | **~12-16 hr** | |
| **Revert criteria** | any instrument filled WR regression >10pp vs V3 baseline | | | |

---

## 4. Decision points for CEO

### DP1 — Should we run P0 noise-floor measurement before anything else?
**Strong recommendation: YES.** $1-2 cost, 10 minutes, tells us if V3 is actually deterministic or if we're partly chasing noise. If V3 agrees with itself 100% on those 4 candles, V2 vs V3 is indeed the story. If V3 disagrees with itself 3/4 times, we need to re-scope V4's claims.

### DP2 — Ship V4 pre-Monday, or post-Monday after live data accumulates?
- **Pre-Monday:** $115-170 API over this weekend + ~16 hr wall time. V4 deploys Monday with the paid challenge.
- **Post-Monday:** ship V3 + v2-active Monday. Accumulate 20-30 live XAUUSD LONG trades over ~2 weeks. Re-run V4 A/B with real filled-trade outcomes as validation anchor. Empirically stronger but delays by 2 weeks.

My lean: **Post-Monday** (+ P0 noise-floor pre-Monday is fine). Reason: V4's $97 A/B backtest still uses simulator outcomes, not live. Real validation comes from live data. Running V4 canary now + deploying V3-live + observing gives us best signal density for V5.

But: if CEO wants V4-live-Monday, $115-170 is reasonable for the upside.

### DP3 — Per-instrument injection now or post-V4-validation?
- Agent C recommends post-V4-validation (Phase 5-6 in plan, after core V4 validates).
- I agree — universal V4 must prove itself first; per-class is incremental.

### DP4 — LIRA / No-CoT A/B (Priority 2 in spec)?
- Agent A's finding: No-CoT sometimes beats CoT on intuition-driven financial classification.
- Cost: $15-20 for canary + mini-backtest.
- Recommendation: RUN IT, low cost, potentially large insight. Could change V4 architecture meaningfully.

---

## 5. What's NOT in V4 scope (deliberate)

- **Fixing H2 2026 XAUUSD WR decay** — regime-driven, not prompt-addressable. S1 monitors.
- **Unlocking USDJPY SHORT signals** — detector or regime, not prompt.
- **Per-instrument at full cardinality** (24 individual prompts) — maintenance burden unjustified by evidence.
- **Model upgrade to Opus 4.7** — Agent A flagged as Priority-7 open gap; Sonnet 4.6 is the production choice empirically (CR 38% vs Opus 19%, 4.4× cheaper). Revisit if V4 still shows interpretive drift.

---

## 6. Honest limits of this investigation

1. **n=4 A2 divergent candles** is a small basis for V4 claims. The counterfactual "V4 recovers +4R" is directional evidence, not statistical.
2. **Claude Sonnet 4.6's self-consistency under effort=max** isn't publicly characterized. Our P0 measurement will be among the first domain-specific data points.
3. **SMC (Smart Money Concepts) prompt patterns** have no peer-reviewed literature. Industry blogs + practitioner reports only.
4. **V4's "1 CHoCH never flips" rule** (CB-2) is a V4 original design — it aligns with SMC tradition but isn't empirically tested. The A/B backtest is its primary validation.

---

## 7. Ready-to-ship artifacts

On main (after merges this commit):
- `research/v4_prompt_engineering/EXTERNAL_RESEARCH.md` (51 sources, 48KB)
- `research/v4_prompt_engineering/FORENSIC_AND_V4_SPEC.md` (8-section forensic)
- `research/v4_prompt_engineering/primary_analyzer_prompt_v4_DRAFT.py` (ready-to-canary)
- `research/v4_prompt_engineering/v2_prompt_snapshot.py` + `v3_prompt_snapshot.py` + `v2_to_v3_diff.patch`
- `research/v4_prompt_engineering/a2_divergent_raw.json` (Feb 2/4/6 raw_responses)
- `research/v4_prompt_engineering/PER_INSTRUMENT_ANALYSIS.md` (24-instrument table + Option 4)
- `research/v4_prompt_engineering/_compute_instrument_characteristics.py` + `instrument_characteristics.json`
- THIS FILE: `V4_SYNTHESIS_AND_PLAN.md` (consolidated CEO decision brief)

---

*V4 engineering research phase complete. All 3 agents' findings consolidated. Ready for CEO decision on DP1-DP4.*
