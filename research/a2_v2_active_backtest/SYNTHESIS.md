# A2 v2-Active Backtest — Synthesis & CEO Decision Brief

**Verdict:** HALT / CEO review required.
**Analysis script SHA256:** `b06631e8b2dda6a420c50897818c4d6c29a1aa56869b7c5b34d159548373f13a`
**Timing:** Generated 2026-04-25 pre-Monday-challenge-purchase.

---

## TL;DR

The pre-registered test auto-verdict is **HALT** because Fleet LONG WR = 50.0% sits exactly in the halt window [45%, 55%]. **3 of 4 criteria PASS** though; the ambiguity is one thin-sample metric (XAUUSD n=9 LONG fills).

**Honest read:** v2-active is **broadly working** — SHORTs emerged (30.8% of XAUUSD CANDs vs 22.8% in F3) + 2/2 SHORT fills WIN + fleet expectancy +0.333R — but XAUUSD LONG WR dropped from F3's 45.5% (n=11) to A2's 33.3% (n=9) on small samples with overlapping CIs. We cannot statistically distinguish "real LONG edge degradation" from "sampling variance."

**My recommendation for Monday:** lean GO with caveats (see §Recommendation below). Document the LONG-WR-watch decision explicitly so we can SPRT-kill early if it's a real regression.

---

## Headline numbers

### Fleet (XAUUSD + USDJPY, 12 slices)

| Metric | A2 v2-active | F3 v2-active (session 38) | Delta |
|---|---:|---:|---:|
| Raw CAND | 37 | 39 final / 588 raw-eval | comparable |
| Filled | 30 | 32 | -2 |
| WR filled | 53.3% [36.1, 69.8] | 56.2% | -2.9pp |
| Expectancy | **+0.333R** [−0.08, +0.75] | +0.407R | -0.074R |
| Total R | +10.00R | +13.00R | -3.0R |
| MaxDD | 3.00R | n/a | — |

Both backtests land **solidly positive** on expectancy + total R. A2's CI lower bound on expectancy just barely dips below zero, but CIs overlap entirely.

### Per-instrument

**XAUUSD (the concern):**
- Raw CAND: 13 (9 LONG + 4 SHORT) → **SHORT share 30.8%** vs F3's 22.8% ✓
- Filled: 11 (9 LONG + 2 SHORT)
- **LONG WR 33.3% (n=9)** [CI 12.1%, 64.6%] vs F3's 45.5% (n=11) [CI 21.3%, 72.0%] — **CIs overlap; cannot reject F3's 45.5%**
- SHORT WR: 100% (n=2) — identical to F3's 2/2 wins ✓ (both xauusd_s7 in both backtests)
- Total R: +1.50R (3×+1.5 SHORT wins + 3×+1.5 LONG wins − 6×−1.0 losses = roughly breakeven on LONG, positive on SHORT)
- MaxDD: 3.0R (1pp over F3's 2.0R — within tolerance)

**USDJPY (solid):**
- Raw CAND 24 (24 LONG + 0 SHORT) — SHORT share 0% (matches F3 — USDJPY is persistently bullish Jan-Apr 2026 regime)
- Filled: 19 (all LONG)
- LONG WR 57.9% (n=19) — **EXACTLY matches F3's 57.9%** ✓
- Expectancy +0.447R — **EXACTLY matches F3** ✓
- Total R +8.50R — **EXACTLY matches F3** ✓

USDJPY is essentially bit-exact between A2 and F3. Sanity check passes: the v2-active pipeline reproduces reliably when the regime is clean (persistent bull).

### SHORT emergence analysis

| Slice | A2 raw SHORT | F3 raw SHORT | Regime |
|---|---:|---:|---|
| xauusd_s4 (Feb 10-22) | 0 | 3 (all L2-rejected) | bullish structure + AI override attempts |
| xauusd_s5 (Feb 23-Mar 7) | 1 | 10 (all L2-rejected) | bullish structure + AI override attempts |
| xauusd_s7 (Mar 23-Apr 2) | **3 (2 WINs)** | **24 raw / 3 final / 2 WINs** | bearish structure emerged |

F3's SHORT picture was: "s4+s5 showed L2 correctly rejecting bad-side AI overrides, s7 was the real SHORT-emergent window, 2/2 WINs." A2 replicates the same structure on s7 (2/2 WINs) with fewer aggressive L2-rejects elsewhere. **SHORT emergence fundamentally works.**

---

## Why the WR discrepancy?

XAUUSD LONG WR difference F3 → A2: **45.5% → 33.3%** on small samples (n=11 → n=9).

Three candidate explanations ranked by plausibility:

1. **Sampling variance (most likely).** Both samples have Wilson 95% CIs spanning ~40pp. 2 wins out of 9 is numerically 22%; 4 wins out of 9 would be 45% (F3's rate). We're within 1 trade of F3's result.
2. **Prompt V3 post-session-38 change.** Session 38 R1 shipped prompt V3 which closed V8-flagged gaming loopholes. V3 may have rejected 1-2 setups that F3's prompt accepted (and would have won/lost differently). The V3 merge happened between F3 and A2 runs.
3. **Wave 2.5 data-ingestion fix** (empty-symbol fix, XAUUSD `atr_session` reactivation). Could have subtly changed MSO inputs to the AI.

Distinguishing (1) from (2)/(3) requires more data — which we only get from live trading post-Monday.

---

## Recommendation (lean GO with explicit LONG-WR-watch)

Rationale:

1. **v2-active is clearly the right direction.** SHORT emergence (30.8% XAUUSD, > F3's 22.8%) is the headline win. Staying on v1/v2_shadow walks into documented H2 decay (24% Apr XAUUSD WR in A1 realized-R data).
2. **Fleet expectancy +0.333R** is a real positive signal. Even at pessimistic CI lower bound −0.08R, we're not walking into a disaster.
3. **USDJPY is bit-exact with F3** — no reason to think v2 regressed there.
4. **XAUUSD LONG WR at 33% n=9 is not statistically distinguishable from F3's 45% n=11.** Refusing to deploy on this basis = waiting for more data that only accrues via live trading anyway.
5. **FTMO $100K challenge at 0.5% XAUUSD risk per-trade** means a 5-trade losing streak costs 2.5% — well within FTMO's 5% daily + 10% max DD guardrails. Even if LONG WR really is 33%, MaxDD 3R (A2) × 0.5% = 1.5% account drawdown per losing streak. Acceptable.

**Suggested Monday deploy config:**
- Flip `detector_version: v2_shadow → v2` Sunday evening.
- Rolling restart.
- Monday AM: buy FTMO $100K challenge at $100K tier (not $200K — match demo).
- **Explicit LONG-WR-watch SPRT gate:** if XAUUSD LONG WR drops below 40% on first 20 live trades (n ≥ 20), halt + council. Document this as unresolved item #11 in CLAUDE.md.
- Keep the monthly-decay shadow monitor (S1) active from day 1 for alarm coverage.

**Alternative (safer, slower):** stay on v2_shadow Monday. Run live for 1 week collecting A3-instrumented data. Re-evaluate v2 active with 20+ XAUUSD LONG fills next weekend before flipping.

The safer option costs a week of the v1-production decay that A1's data already documented (Apr XAUUSD WR 10%). That's expensive.

---

## What to NOT do

- **Do not ship V4-A prompt nudge.** Session 39 extended concluded realized-R reverses the walk-level evidence direction. V4-A would make things worse.
- **Do not ship the anti-pattern classifier as a gate.** Session 39 extended showed AUC 0.55 OOS — no real signal.
- **Do not expand instruments beyond Tier-1 five for Monday.** Phase 2a (EURUSD, NAS100, etc.) batch-validates AFTER Monday's challenge stabilizes.

---

## Final GO / STAY / HALT decision gate

CEO must explicitly choose one of:

- **GO** (recommended): flip v2 active Sunday, challenge Monday with LONG-WR-watch SPRT.
- **STAY**: stay v2_shadow Monday, 1 more week of live data, re-evaluate.
- **Wait longer**: more backtest data (another $40 API for a 2-week-sliding-window rerun over Apr-May 2026 data if available) — minor value-add beyond A2.

Expected outcome sensitivity:
- GO + v2 works → pass challenge, deploy live capital faster, compound edge.
- GO + LONG WR genuinely dropped → SPRT catches it ~20 trades in → halt + regroup at ~2.5% DD (recoverable).
- STAY + no decay → wasted week.
- STAY + more decay → wasted week + worse numbers next Monday.

My math says the GO EV beats STAY EV by a meaningful margin. But this is a strategic call for you, not a mathematical one.

---

*Ready for CEO final decision. All artifacts committed to main.*
