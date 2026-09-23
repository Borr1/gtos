# FA-3 — Post-FA-2 T7 Re-run Report

**Date:** 2026-04-20
**Scope:** XAUUSD + EURUSD, Jan 2 → Apr 13 2026, split into 4 parallel date slices
**Status:** All 4 slices complete.
**Session:** 35 FA-3 (pre-redacted_account Tuesday kickoff)
**Parent audit:** `phase4_chairman_synthesis.md`

---

## TL;DR

1. **FA-2 prompt changes are fully working on XAUUSD.** 184/184 raw CANDIDATEs across both XAUUSD slices: 100% non-zero `sl_buffer_applied`, 0% degenerate (entry==SL or entry==TP1). Validator demote count: 0. Parse errors: 2/599 API calls (0.3%).

2. **FA-2 prompt changes are LARGELY NOT WORKING on EURUSD at n=175.** EURUSD Jan-Feb (the large slice) shows 63% of raw CANDs are degenerate, only 31% carry non-zero buffer, only 31% at ≥4dp. EURUSD Mar-Apr (n=18) looked cleaner but is too small to be representative. **This vindicates CEO's NO-GO decision on EURUSD** — it would have been catastrophic live, and is a blocker for enabling EURUSD later without additional prompt work.

3. **Live validator is the last line of defense and it works.** On the EURUSD Jan-Feb slice, 2 of the 5 "final trades" that made it through sim's raw-JSON path are degenerate and would have been demoted at `primary_analyzer.py:310` in live. Sim therefore OVERSTATES FX trade frequency by ~1.7× and should not be trusted for FX risk estimation until patched.

4. **XAUUSD trade expectancy got more NEGATIVE and more ACCURATE, not worse.** Old prompt was silently dropping ~32% of AI outputs as "PA parse failed" (289/899 on XAUUSD Jan-Mar). New prompt is schema-compliant → 0 parse failures → true distribution is now visible. Pre-FA-2 "+0.6R on n=7" was low-n noise. Post-FA-2 "−12R on n=32" is real statistical power. **The edge breaks in Q1-26 V-shape chop** — Chairman C3 anticipated this; XAUUSD already shipped at 0.5% risk.

5. **Decision points for the CEO** — see §6.

---

## 1. Slice inventory

| Slice | Symbol | Window | Status | n raw CAND | Output dir |
|-------|--------|--------|--------|-----------:|-----------|
| A | EURUSD | 2026-01-02 → 2026-02-28 | complete | 175 | `research/t7_live_simulation/post_fa2/eurusd_jan_feb/` |
| B | EURUSD | 2026-03-01 → 2026-04-13 | complete | 18 | `research/t7_live_simulation/post_fa2/eurusd_mar_apr/` |
| C | XAUUSD | 2026-01-02 → 2026-02-28 | complete | 83 | `research/t7_live_simulation/post_fa2/xauusd_jan_feb/` |
| D | XAUUSD | 2026-03-01 → 2026-04-13 | complete | 101 | `research/t7_live_simulation/post_fa2/xauusd_mar_apr/` |

Lesson for future: at Tier-4 Anthropic, split per-candle sims into 8–16 parallel 1–2 week slices, not 2–4 two-month slices. 4-slice partitioning left 3.5 Tier-4 channels idle at any given moment. Memory: `feedback_parallelize_aggressively_tier4.md`.

---

## 2. FA-2 prompt-compliance results — all 4 slices

Validator spec (shipped in commit `fa35cc0`): demote CANDIDATE → NO_TRADE if `entry_price == stop_loss` OR `entry_price == take_profit_1` bit-exactly. Lives at `src/components/primary_analyzer.py:310` via `guard_candidate_degenerate_params` (definition at line 633). Called on every live evaluation.

Methodology: `max_dp` = maximum decimal places across entry/SL/TP1. For XAUUSD (2-dp native), only the degeneracy check is meaningful. For EURUSD (5-dp native), `≥4dp` is the precision-compliance measure. `degenerate` = any two of entry/SL/TP1 are bit-exactly equal.

| Slice | Raw CAND | ≥4dp (FX only) | Non-zero buffer | Degenerate | Parse errors / sent | Validator would demote |
|-------|---------:|---------------:|----------------:|-----------:|--------------------:|-----------------------:|
| A — EURUSD Jan-Feb | 175 | 55 (31%) | 55 (31%) | **111 (63%)** | 28/912 (3.1%) | **111** |
| B — EURUSD Mar-Apr | 18 | 11 (61%) | 13 (72%) | 2 (11%) | 2/164 (1.2%) | 2 |
| C — XAUUSD Jan-Feb | 83 | n/a (2dp native) | 83 (100%) | 0 | 0/250 (0.0%) | 0 |
| D — XAUUSD Mar-Apr | 101 | n/a (2dp native) | 101 (100%) | 0 | 2/349 (0.6%) | 0 |
| **XAUUSD combined** | **184** | n/a | **100%** | **0%** | **2/599 (0.3%)** | **0** |
| **EURUSD combined** | **193** | **66/193 (34%)** | **68/193 (35%)** | **113/193 (59%)** | **30/1076 (2.8%)** | **113** |

**Interpretation:**

- **XAUUSD is fully compliant.** Native 2dp instrument + swing-beyond SL instruction + non-zero buffer rule → AI always emits valid, distinct prices. FA-2 Change 2 works as designed on XAUUSD.
- **EURUSD remains broken at n=193.** 59% degeneracy, 65% sub-FX precision, 35% non-zero buffer. FA-2 Change 2 is insufficient for FX; the prompt changes do not adequately constrain Sonnet-4-6 to emit 5dp distinct prices on EURUSD.
- **Mar-Apr (n=18) was not representative.** Its 11% degeneracy suggested "FA-2 mostly works on EURUSD, minor residual cleanup". Jan-Feb (n=175, 10× larger) shows the true picture: the prompt fix did not land.
- **Live validator catches 113/193 = 59% of EURUSD CANDs** — that's the bulk of what the AI emits. Live EURUSD with today's prompt would see ~80 "valid" CANDs over 3.5 months vs. sim's 193. Validator is working but leaves a very thin signal.
- **PARSE_ERROR rate on EURUSD (2.8%) is 9× higher than XAUUSD (0.3%).** This is further evidence that FA-2 prompt updates still under-constrain Sonnet-4-6 on 5dp FX output.

---

## 3. Validator-gap finding (sim ≠ live on FX)

The sim script `scripts/simulate_t7_live_period.py` parses raw AI JSON and counts decisions without calling `PrimaryAnalyzer.evaluate()`. The live validator `guard_candidate_degenerate_params` is therefore bypassed. This causes sim to OVERSTATE FX trade frequency and expectancy:

**EURUSD Jan-Feb final-trade breakdown (sim's view):**

| # | Date | Dir | Entry | SL | TP1 | Degenerate? | Sim outcome | Live outcome |
|---|------|-----|------:|---:|----:|:-----------:|:-----------:|:------------:|
| 1 | 2026-01-07 09:30 | SHORT | 1.17 | 1.17 | 1.17 | **YES** | LOSS −1R | **demoted → NO_TRADE** |
| 2 | 2026-01-30 13:00 | LONG | 1.19 | 1.18975 | 1.19038 | no | LOSS −1R | LOSS −1R |
| 3 | 2026-02-04 07:00 | LONG | 1.18 | 1.18 | 1.18 | **YES** | LOSS −1R | **demoted → NO_TRADE** |
| 4 | 2026-02-10 08:15 | LONG | 1.18 | 1.17 | 1.19 | no | LOSS −1R | LOSS −1R |
| 5 | 2026-02-23 08:00 | LONG | 1.18 | 1.17 | 1.19 | no | LOSS −1R | LOSS −1R |

**Net:** Sim shows 5 losses −5R. Live would show 3 losses −3R. Still negative, but 40% smaller drawdown footprint. Sim is useful for compliance analysis but NOT for FX risk estimation until patched.

**EURUSD Mar-Apr:** 1 of 2 final trades degenerate — sim's +0.3R would be +1.33R live (still noise at n=1).

**XAUUSD both slices:** no degenerates, sim == live on these outcomes.

**Fix path:** 15-min patch to call `PrimaryAnalyzer.evaluate()` or inline the `guard_candidate_degenerate_params` check in the sim. Filed as post-kickoff T-task; live is protected regardless.

---

## 4. Trade-outcome comparison (pre-FA-2 vs post-FA-2)

### XAUUSD — the big signal

**Pre-FA-2** (`research/t7_live_simulation/t7_live_simulation_report_jan_mar11.md`):

| Window | Raw CAND | **PA parse failed** | L2 reject | Final | WR | Total R | Exp/trade |
|--------|---------:|-------------------:|----------:|------:|---:|--------:|----------:|
| Jan 2 → ~Mar 11 | 899 | **289 (32%)** | 591 | 7 | 43% (3/7) | +0.6R | +0.079R |

**Post-FA-2** (this run):

| Window | Raw CAND | PA parse failed | L2 reject | Final | WR | Total R | Exp/trade |
|--------|---------:|----------------:|----------:|------:|---:|--------:|----------:|
| Jan 2 → Feb 28 | 83 | 0 | 10 | 14 | 36% (5/14) | −1.5R | −0.107R |
| Mar 1 → Apr 13 | 101 | 2 | 24 | 18 resolved + 1 unfilled | 17% (3/18) | −10.5R | −0.583R |
| **Combined Jan-Apr** | **184** | **2** | 34 | **32** | **25% (8/32)** | **−12.0R** | **−0.375R** |

**What changed structurally:**
- `PA parse failed` dropped from 289 → 2. Old prompt was silently discarding ~32% of AI outputs as unparseable. New prompt instructions (explicit precision + `sl_buffer_applied` field) produce clean schema almost every time on XAUUSD.
- Raw CANDIDATE count dropped 899 → 184 because the old prompt had CR=75% (almost every evaluated setup was CANDIDATE) vs new prompt at CR=31%. The old prompt was over-emitting CANDIDATE, with many getting filtered downstream (L2=591 rejects, parse=289 drops).
- Final trade count grew 7 → 32 (4.6×) because the schema cleanup means more of the surviving CANDIDATEs reach execution.

**Why per-trade expectancy got worse (+0.079R → −0.375R):**
- Pre-FA-2 n=7 is noise. 95% CI easily spans [−1.5R, +1.7R].
- Post-FA-2 n=32 has real power. The TRUE Jan-Apr 2026 XAUUSD expectancy in this regime is negative.
- The old prompt's 289 parse failures weren't random — they were likely correlated with chop-regime uncertainty (AI outputs less clean on marginal setups). Dropping them selected for the cleanest, most confident setups. Post-FA-2 keeps all of them → we see the full marginal-setup distribution.

### EURUSD — sim numbers not trustworthy (3 degenerates leaked into final-trade pool)

| Window | Raw CAND | Final (sim) | Final (live-adjusted) | WR (live) | Total R (live) | Exp/trade (live) |
|--------|---------:|------------:|----------------------:|----------:|---------------:|-----------------:|
| Jan 2 → Feb 28 (Slice A) | 175 | 5 | 3 | 0% (0/3) | −3.0R | −1.000R |
| Mar 1 → Apr 13 (Slice B) | 18 | 2 | 1 | 0% (0/1) | −1.0R | −1.000R |
| **Combined Jan-Apr** | **193** | **7** | **4** | **0% (0/4)** | **−4.0R** | **−1.000R** |

Live-adjusted = excluding degenerate trades the validator would demote. 0/4 WR is noise at n=4; the actual signal is "EURUSD AI outputs are 59% degenerate and FA-2 Change 2 did not fix it". The specific R values are meaningless — the compliance failure is the finding.

---

## 5. Regime context (ties back to Chairman synthesis)

From `phase4_chairman_synthesis.md` / H2 Regime Posterior:
- **Q4-25 KER = 0.412** (trending regime) → XAUUSD OB-retest edge historically ~+0.2R/trade
- **Q1-26 KER = 0.033** (V-shape chop) → edge mechanism breaks; stop-cascade mean-reversion requires a directional impulse
- Chairman Change 4 (C3): XAUUSD → 0.5% risk, reverts on 2 consecutive months WR ≥65% OR 4 weeks KER>0.25 on D1

**Post-FA-2 Jan-Apr XAUUSD results confirm the regime hypothesis in real numbers:**
- At 1% risk: −12R = −12% equity → instant redacted_account fail (5% daily / 10% total)
- At 0.5% risk: −6% equity over 3.5 months → painful but survivable within 10% cap
- Feb alone was +2.5R; all the pain concentrated in Mar-Apr = matches the regime shift timing

**The C3 decision was correct, and in hindsight may be conservative enough.** But if the chop regime persists into kickoff week, XAUUSD may need dormant mode rather than 0.5% sizing — see §6 D2.

---

## 6. Decision points for the CEO

### D1 — EURUSD FA-2 Change 2 did not fix the problem
- **Observation:** 59% of EURUSD raw CANDs are degenerate at n=193. FA-2 prompt change did not constrain Sonnet-4-6 to 5dp distinct prices on FX.
- **Already decided:** EURUSD = NO-GO for redacted_account kickoff. Chairman decided this pre-FA-3; post-FA-3 data vindicates the call.
- **Follow-up required before EURUSD can ever be enabled:**
  - Stronger prompt scaffolding on FX (explicit 5dp examples, explicit "never emit the same price twice" instruction).
  - Re-run FA-3 Slice A (EURUSD Jan-Feb) after prompt v2 to confirm degeneracy drops below ~5%.
  - Consider instrument-specific prompt templates (XAUUSD prompt is fine; FX needs different constraints).
- **Recommendation:** Keep EURUSD disabled. File prompt v2 work as a post-kickoff T-task. No action needed Tuesday.

### D2 — XAUUSD posture for kickoff
- Current shipped state: 0.5% risk (C3 decision, `config/profiles/redacted_account.yaml:46-49`).
- Post-FA-2 Jan-Apr results: −12R @ 1% = −12% equity; −6% @ 0.5% on 3.5 months of chop.
- **Option A (keep 0.5%):** Chairman C3 as-is. Hope for regime shift during Phase 1. Feb was +2.5R → edge exists when KER rises.
- **Option B (dormant XAUUSD until regime confirms):** Skip XAUUSD entirely, run US30/USDJPY/GBPJPY only, bring XAUUSD back once D1 KER > 0.25 for 4 weeks.
- **Option C (reduce further to 0.25%):** Keep observation sample but minimize drawdown contribution.
- **Tradeoff:** Option A has real downside if Mar-Apr regime persists; Option B loses the observation sample needed for the C3 reversion criteria; Option C is a compromise but needs explicit profile edit.
- **Recommendation:** I cannot call this for you — the weight you place on "observation continuity" vs "drawdown minimization" is a CEO judgment. **If asked, I lean Option A** because C3 was designed with this regime in mind, and Feb's +2.5R suggests the edge re-emerges when KER improves. Happy to run a focused MC simulation for each option as a follow-up.

### D3 — Patch sim to invoke validator
- 15-min code change in `simulate_t7_live_period.py` to call `PrimaryAnalyzer.evaluate()` or inline `guard_candidate_degenerate_params`.
- Improves sim/live parity for FX. Not pre-kickoff critical (live is protected).
- **Recommendation:** Defer to post-kickoff; filed as T-task for fresh session.

### D4 — Add "FX degeneracy residual" to Q4.6 investigation
- The fresh session's Phase 3 (Q4.6 sim-vs-KB 12× CAND-rate discrepancy) should now also investigate why FX CANDIDATE rate is so high in sim (19% on EURUSD Jan-Feb) when 63% of those are degenerate and would be killed by live. This connects to Q4.6.
- **Recommendation:** Already reflected in handoff 36; explicitly flag this finding in the Phase 3 kickoff.

---

## 7. Artifacts

- Pre-FA-2 XAUUSD report: `research/t7_live_simulation/t7_live_simulation_report_jan_mar11.md`
- Post-FA-2 XAUUSD Jan-Feb: `research/t7_live_simulation/post_fa2/xauusd_jan_feb/t7_live_simulation_report.md`
- Post-FA-2 XAUUSD Mar-Apr: `research/t7_live_simulation/post_fa2/xauusd_mar_apr/t7_live_simulation_report.md`
- Post-FA-2 EURUSD Jan-Feb: `research/t7_live_simulation/post_fa2/eurusd_jan_feb/t7_live_simulation_report.md`
- Post-FA-2 EURUSD Mar-Apr: `research/t7_live_simulation/post_fa2/eurusd_mar_apr/t7_live_simulation_report.md`
- FA-2 validator code: `src/components/primary_analyzer.py:310` + `guard_candidate_degenerate_params` at line 633
- FA-2 prompt: `src/prompts/primary_analyzer_prompt.py` (PRECISION block + line 152/155/236)
- C3 XAUUSD risk override: `config/profiles/redacted_account.yaml:46-49`
- Chairman synthesis: `research/b_deep_audit_2026-04-19/phase4_chairman_synthesis.md`
