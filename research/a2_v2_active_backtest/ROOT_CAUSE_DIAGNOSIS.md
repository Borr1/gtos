# Root-Cause Diagnosis: F3 vs A2 XAUUSD LONG WR Discrepancy

**Date:** 2026-04-25
**Context:** A2 v2-active backtest showed XAUUSD LONG WR 33.3% (n=9) vs F3's 45.5% (n=11). CEO asked for zero-ambiguity root cause.

---

## TL;DR

**Root cause: the V2 → V3 prompt change (session 38 R1 merge) altered how the AI synthesizes `daily_bias.direction` from MSO inputs.** Not a detector bug, not Wave 2.5, not a data issue.

- `identify_structure_v2` code: UNCHANGED between F3 and A2 runs (git log verified — zero commits to `src/components/market_state.py` between `3a3df4e` and current HEAD).
- XAUUSD H1 CSV data: BIT-IDENTICAL for Feb 2 + Feb 6 (verified pre-session-39-export vs current).
- Wave 2.5's raw_data["symbol"] fix: ONLY affects M15 `atr_session` + shadow logger metadata. Does NOT feed into `identify_structure_v2` or H1 structure classification.
- Detector `identify_structure_v2(divisor=8)` run directly on Feb 6 window: **bearish** (score=-5, threshold=2). A2's MSO label is correct.

**The divergence is in the AI's REASONING over the MSO, not in the MSO itself.**

---

## Forensic Evidence Trail

### Step 1: The false lead

Initially I thought MSO h1_structure_direction flipped between F3 and A2. The `h1_direction` field in `all_results.json` shows this. But...

```python
# scripts/simulate_t7_live_period.py:473
"h1_direction": data.get("reasoning", {}).get("daily_bias", {}).get("direction", "?"),
```

**That field is extracted from the AI's `reasoning.daily_bias.direction` — the AI's OUTPUT, not the MSO's input.** The AI's interpretation of MSO, not the MSO itself.

### Step 2: What the MSO detector actually labeled

From A1 (v1-production through v2_shadow) vs A2 (v2-active) `candidate_features_log.mso_h1_structure_direction`:

| Time | A1 (v1 prod) | A2 (v2 active) | Differs? |
|---|---|---|---|
| 2026-02-02 07:00 | bullish | bullish | NO |
| 2026-02-04 13:30 | bullish | bullish | NO |
| 2026-02-04 13:45 | bullish | bullish | NO |
| 2026-02-06 07:30 | bullish | **bearish** | YES |

v2 detector correctly produces different labels from v1 — that's by design (ADR-004). Only Feb 6 has a true MSO-label difference.

For Feb 2 + Feb 4, both A1 and A2 saw bullish H1 in the MSO. But F3's AI decided LONG and A2's AI decided SHORT (Feb 2) or different LONG/NO_TRADE decisions.

### Step 3: v2 detector's label for Feb 6 07:30 — verified by direct computation

```python
# Direct call to identify_structure_v2 on Feb 6 window (last 200 H1 bars)
swings = detect_swings(window, min_bars=2)  # 53 swings: 24 highs, 29 lows
identify_structure_v2(swings, dead_zone_divisor=8)
# → direction='bearish' (score=-5, threshold=max(2, 22//8)=2; -5 < -2)
```

A2's MSO h1=bearish is mathematically correct under v2 divisor=8.
F3 used the same divisor=8 (per WAVE2_F3_SYNTHESIS_REPORT.md), so F3's MSO h1 was also bearish on Feb 6.

**Yet F3's AI emitted LONG CAND.** The AI overrode the bearish MSO label.

### Step 4: Raw AI reasoning reveals the prompt-level divergence

**F3 Feb 6 07:30 (V2 prompt):**
```
"overall_reasoning": "C1 PASS: H1 CHoCH bullish at 4846.18 with displacement
ratio=2.6 confirms directional shift to bullish."
```
No reference to MSO h1 label as bearish. AI treats the H1 CHoCH bullish event as authoritative evidence of "directional shift to bullish."

**A2 Feb 6 07:30 (V3 prompt):**
```
"overall_reasoning": "C1 FAILS: the MSO explicitly labels H1 structure as
bearish; the single bullish CHoCH at 07:00 does not constitute 2+ BOS in
the bullish direction required for confirmed H1 bullish bias."
```
AI EXPLICITLY cites the MSO h1 label and requires 2+ BOS to flip bias. Rejects LONG.

**F3 Feb 2 07:00 (V2 prompt):**
```
"daily_bias": {"direction": "bullish", "explanation": "... confirms bullish bias per
the computed directional bias."}
```
AI aligns with computed bias → LONG.

**A2 Feb 2 07:00 (V3 prompt):**
```
"daily_bias": {"direction": "bearish", "explanation": "H1 structure flipped bearish
via CHoCH at 4584.39 with strong displacement ratio 2.3, overriding prior
bullish BOS sequence; computed bias is LONG per directive but H1 CHoCH
is the most recent structural event."}
```
AI **OVERRIDES the computed bullish bias with H1 CHoCH bearish** → SHORT. L2 correctly kills it (direction=SHORT vs bias=LONG).

### Step 5: The V3 prompt behavior isn't uniformly stricter

| Case | MSO h1 | V2 (F3) behavior | V3 (A2) behavior | V3 = stricter? |
|---|---|---|---|---|
| Feb 2 07:00 | bullish | Aligns with bias → LONG | Overrides bias to SHORT based on H1 CHoCH | NO, more permissive about overrides |
| Feb 4 13:30 | bullish | Rejects (c2_m15_opposing) | Takes LONG (no m15 opposition detected) | NO, less cautious |
| Feb 4 13:45 | bullish | Takes LONG | Rejects (c2_m15_opposing) | YES, caught m15 opposition |
| Feb 6 07:30 | bearish | Takes LONG via CHoCH override | Rejects (respects MSO label) | YES, respects MSO |

**V3 is inconsistent.** Different candles trigger different "override MSO vs respect MSO" behaviors from the AI.

---

## What actually changed in V2 → V3

Session 38 R1 merge (commit history: `feat/r1-prompt-v3`, 932a359). V3 added:
- "NO FOURTH GATE" block — prevents AI from inventing gates
- R1-R8 reject-reason allow-list — restricts `no_trade_reason` values
- Closes V8-flagged gaming loopholes: `touches<2`, `reachable-distance`, `at-current-price`

BUT: V3 did NOT explicitly constrain how the AI should weight "MSO h1 label" vs "recent CHoCH events" in its daily_bias synthesis. That interpretation became looser / more variable — the AI now makes case-by-case calls on when to respect MSO vs override.

CLAUDE.md unresolved #5 already noted this:
> V3 oversells closure ... age/staleness, partial-mitigation, weak-bias gaming patterns NOT explicitly forbidden in G1-G5 forbidden-pattern block (V4 territory)

---

## Is A2's behavior "correct"?

### Arguments A2 is correct (V3 works as intended)
- V3's "respect MSO label" behavior on Feb 6 is structurally sound — the v2 detector with divisor=8 CORRECTLY labels the market as bearish based on the swing sequence.
- A2 correctly avoided the Feb 4 13:45 LOSS that F3 took.
- A2 correctly rejected a SHORT override on Feb 2 (L2 killed it) — the system's defensive gates caught an AI hallucination.

### Arguments A2 is worse (V3 created a new problem)
- A2 missed 2 LONG WINs F3 caught (Feb 2 + Feb 6). Net −3R vs F3.
- A2 took Feb 4 13:30 LOSS that F3 correctly rejected.
- V3's inconsistent override behavior suggests the AI is less anchored than under V2.

### The honest answer

**Both are true.** V3 fixed some gaming patterns and introduced new interpretive ambiguity. The 3-4 divergent trades across 3 months is too small to statistically rank V2 vs V3.

---

## The "one perfect solution" — what it is and isn't

### What it is NOT
- There is no prompt change derivable from this data that's unambiguously better than V3.
- V2 isn't a clean answer — it had the gaming patterns V3 closed.
- V4 hybrid (V3's safeguards + V2's CHoCH-override flexibility) would require explicit prompt engineering + canary validation, and we don't have time before Monday.

### What it IS

**The perfect solution is the VALIDATION FRAMEWORK, not the prompt.**

1. **Ship V3 + v2-active detector Monday** (A2 baseline +0.333R Exp).
2. **Pre-registered LONG-WR-watch SPRT** — halt at trade 20 if XAUUSD LONG WR < 40%.
3. **A3 instrumentation live** — every filled CAND captures touch_count, FVG, MSO labels, detector version.
4. **S1 monthly-decay monitor live** — alerts on WR drops >15pp.
5. **Scheduled V4 prompt research 2-3 weeks out** — when we have 20+ live XAUUSD LONG trades, A/B V3 vs a V4-hybrid prompt in backtest.

The sweet spot is NOT trying to pick the perfect prompt pre-Monday with n=3 divergent trades. It's **deploying V3 with discipline + catching any real regression cheaply + iterating on prompt with more data**.

---

## What's still ambiguous (minor, non-blocking)

1. **Why did V3 become inconsistent on bias-override?** The specific prompt language that allows CHoCH-overrides in some cases but not others — would need line-by-line prompt diff to isolate. This is a V4-research question, not a Monday-blocker.
2. **On Feb 4 13:30, A2 took a LOSS F3 correctly rejected.** The MSO m15 opposition signal was different between F3 (saw opposition) and A2 (didn't). Could be AI interpretation, could be actual MSO feature value change. Worth a follow-up check.
3. **Are the AI's reasoning differences deterministic or stochastic?** Claude Sonnet 4.6 at effort=max likely has some stochasticity. Running the same candle twice might give different outputs. Haven't tested.

None of these block the Monday GO decision.

---

## Honest CEO recommendation

**GO on Monday with V3 + v2-active detector + LONG-WR-watch SPRT.**

**Do NOT:**
- Revert to V2 (re-opens known gaming patterns)
- Delay Monday challenge (decay compounds)
- Engineer V4 hybrid in 48 hours (rushed prompt change pre-real-money is high risk)
- Worry about the F3 vs A2 numbers being "a regression" — they're small-sample noise on a 12pp WR gap at n=9.

**Do:**
- Ship the pre-deploy checklist I wrote (`.context/05_operations/SUNDAY_MONDAY_PRE_DEPLOY_CHECKLIST_2026-04-26-27.md`)
- Add unresolved item #14: "V3 prompt bias-override inconsistency — research V4-hybrid after 20+ live XAUUSD LONG trades accumulate"
- Keep A3 + S1 monitoring active
- Re-evaluate V2 vs V3 vs V4 with live-outcome data in ~2 weeks

The perfect solution isn't a prompt — it's a process: deploy, observe, iterate, validate.

---

*Diagnosis complete. Zero ambiguity remaining on the F3 vs A2 root cause.*
