# NAS100 T7 Validation — Final Synthesis (Chairman)

**Scope:** 1 600 M15 kill-zone candles, NAS100 Jan 02 → Apr 17 2026, 5 parallel slices, 818 AI calls @ claude-sonnet-4-6 effort=max.
**Actual cost:** $22.97 (4 001 952 input tok + 731 268 output tok — bit-exact to Sonnet-4.6 pricing).
**Inputs:** A/B/C/D parallel Opus 4.7 analyses + E cold-review critique. This file is the chairman pass.

---

## TL;DR (5 bullets)

1. **The edge is real on NAS100, just smaller than XAUUSD.** 37 CANDIDATEs, 22 W / 11 L / 4 UNFILLED → **66.7 % WR on 33 resolved, +22.03R net, +0.668R/trade expectancy.** Binomial p=0.080 vs 0.5 (not significant alone, but on the same ballpark as XAUUSD's 62 % WR baseline). Post-AI CANDIDATE rate 4.5 % (vs XAUUSD 10.3 %).
2. **We are correctly accepting good trades, but we are mechanically leaking edge at two gates.** The verification strict-`<` SL gate rejects 42 LONG setups at 59.5 % WR / **+13.5R standalone** (SL bit-exact to OB low). The `max_kz_trades=1` cap rejects 24 novel would-be-CANDIDATEs at 66.7 % WR / +16.02R. Joint fix: **+36.5R of real edge recovered per quarter.**
3. **We skipped ~1 395 NO_TRADEs + 84 L2 + 82 BLOCKED, but most of the skips were correct.** The AI was NOT "too strict for Sonnet" (the sim ran Sonnet — the "Opus 4.5" model_used strings are AI hallucination; cost math confirms Sonnet bit-exact). Genuine missed winners are small: the two gate leaks above are the only material ones.
4. **Direction asymmetry (36 LONG : 1 SHORT) is a D1-bias-lag problem, not a prompt bug.** Week 14 had 54 / 54 AI-seen records flagged `bias=bearish bias_source=D1` during a **+4.20 % NAS100 rally** and produced **zero CANDIDATEs.** This is instrument-agnostic — same code path bites XAUUSD / US30 during regime inflections. Biggest cross-cutting finding in the review.
5. **Execution is faithful.** Agent C reproduced 37/37 CANDIDATE outcomes bit-exactly, confirming the simulator and live-like semantics. Agent A's "3 simulator-artefact wins" claim was debunked by cold-review CSV replay (zero pre-fill SL breaches). The headline 66.7 % WR stands.

---

## Direct answers to the 6 questions you asked

### Q1 — "Did we make the correct trades?"

**Yes, overwhelmingly.** The 37 CANDIDATEs:
- **22 W / 11 L / 4 U → 66.7 % WR resolved, +22.03R, +0.668R Exp.**
- Best-hour (08Z London open): 6 W / 1 L (85.7 %).
- Best-month (Jan): 9 W / 1 L (90 %) in a rising market.
- Cost per WIN: $0.048.

Two caveats:
- **Monotonic WR decay by month**: 90 % → 75 % → 50 % → 33 %. Not random noise — Fisher exact p=0.038 between slice 1-2 (12 W / 2 L) and slice 4-5 (5 W / 7 L). The decay tracks the NAS100 regime: peak 2026-01-28 @ 26 219 → trough 2026-03-31 @ 22 781 (−13.12 % DD) → rally back to 26 671 by 2026-04-17. Model edge is conditional on "clean trending or post-BOS retest" regime and degrades during the churn phase.
- **POI-zone = premium is a perfect-loss discriminator at n=6**: discount 22 W / 5 L (81.5 %), premium **0 W / 6 L (0 %)**, Fisher p<0.001. Striking but small-n — a single exception flips significance. Ship as shadow logger, not hard filter.

### Q2 — "Did we skip so many trades?"

**Numerically yes (2 × 1 600 candles − 37 = 3 163 non-fires if we count twice per KZ), but structurally the skip was almost all correct.**

Pipeline funnel (total 1 600 evaluated):

| Stage | Count | % |
|---|---:|---:|
| Evaluated | 1 600 | 100 % |
| Pre-AI prescreen fail (L1) | 240 | 15.0 % |
| Pre-AI OB-proximity reject | 542 | 33.9 % |
| AI reached | 818 | 51.1 % |
| AI NO_TRADE | 613 | 38.3 % (of total) |
| AI CANDIDATE | 205 | 12.8 % (of total) |
| L2 post-AI reject | 84 | 5.3 % |
| BLOCKED_LIMIT (KZ / daily caps) | 82 | 5.1 % |
| Final CANDIDATE | 37 | **2.3 %** |
| PARSE_ERROR | 2 | 0.1 % |

**AI's raw pass-through rate = 205/818 = 25 %**, of which only 37 / 205 ≈ 18 % survive L2 + risk-cap. Net gate-live CANDIDATE rate = 4.5 % of AI-reached candles (vs XAUUSD's 10.3 % baseline).

### Q3 — "Did the skipped trades win or lose?"

Bucket-by-bucket counterfactual (Agent C, cold-review reproduced bit-exact):

| Bucket | N | W/L/U | WR | Cum R | Exp | Verdict |
|---|---:|---:|---:|---:|---:|---|
| **L2: `sl=OB_bound_exact`** | **42** | **25/17/0** | **59.5 %** | **+20.50R** | **+0.489R** | **Real edge killed by strict-`<` gate bug** |
| L2: `sl_inside_OB_zone` | 4 | 1/3/0 | 25 % | −1.50R | −0.375R | Correctly killed |
| L2: `poi_self_contradict_False` | 19 | 6/13/0 | 31.6 % | −4.00R | −0.211R | Correctly killed — AI's own contradiction IS signal |
| L2: `poi_cited_no_matching_OB` | 13 | 6/7/0 | 46.2 % | −0.50R | −0.038R | Correctly killed |
| L2: `entry_in_ob` | 5 | 0/5/0 | 0 % | −5.00R | −1.00R | Correctly killed |
| L2: `m15_choch_exists` | 1 | 0/1/0 | 0 % | −1.00R | −1.00R | Correctly killed |
| **BLOCKED novel `max_kz_trades`** | **24** | **16/8/0** | **66.7 %** | **+16.02R** | **+0.667R** | **Matches CAND baseline — real edge capped** |
| BLOCKED novel `max_daily_trades_sim` | 7 | 3/4/0 | 42.9 % | −0.50R | −0.071R | Correctly capped |
| BLOCKED dupes (same entry/sl/tp) | 51 | — | — | — | — | Not distinct setups |

**Net:** the skipped trades mostly LOSE; the two exceptions are surgical — `sl=OB_bound_exact` (real wins killed) and novel `max_kz_trades` rejects (real wins capped).

### Q4 — "Did we reject trades that could've won?"

**Yes, and we can recover ~+36.5R/quarter by fixing two things.** Both cold-reviewed as A-tier evidence.

**Leak #1 — Strict-`<` SL-beyond-OB gate** (`src/components/verification.py:520-533`)
The gate asserts `sl < zone_low` for LONG (strict). 42 LONGs had SL bit-exact equal to OB low → rejected. Counterfactual: 59.5 % WR, +20.50R joint. **Standalone recovery (if only this ships): +13.5R** — because 13 of the 42 rejects are in (date, KZ) cells where a CANDIDATE already fired, so relaxing `<` to `<=` without also raising `max_kz_trades` would only convert those 13 to BLOCKED_LIMIT.
Fix: `verification.py:522` change `<` to `<=` (and matching SHORT operator on line 536).
Risk: minimal — it's a boundary-precision bug. The 4 "`sl_inside_OB_zone`" rejects still correctly fail.

**Leak #2 — `max_kz_trades=1` cap**
24 novel setups blocked (not dupes). 66.7 % WR, +16.02R, +0.667R Exp — exactly matches the CAND baseline.
Fix: raise cap to 2 in `config.risk.max_kz_trades`.
Risk: **higher** — requires correlation-group sanity check (can two NAS100 trades inside same KZ breach correlation-exposure budget? probably not solo, but could if XAUUSD or US30 also trades). Do NOT relax without cross-instrument data.

**Leak #3 (smaller) — D1-bias lag through regime inflection.** Week 14 (2026-03-30 → 2026-04-03): 54 / 54 AI-seen records flagged `bias=bearish bias_source=D1` while NAS100 rallied +4.20 %. Zero CANDIDATEs. This is mechanical — D1-bias is slow to rotate. The instrument-agnostic nature makes this a **deploy-wide monitor**: log when D1-bias contradicts H4+H1 for ≥N candles and alert. No code change today; just a shadow logger.

### Q5 — "Are we accurately accepting the good trades?"

**Yes — the 37 we accept are high-quality, but we are LONG-biased and late-regime-degrading.**

- **Direction asymmetry: 36 LONG / 1 SHORT.** The single SHORT (2026-03-23) lost on an outside-reversal day. H1 bias distribution was 681 bullish / 135 bearish in the eval set (5× bullish) — so some LONG skew is expected, BUT the gate-pass rate is Fisher-significant: LONG setups pass at 36/681 = 5.3 %, SHORT pass at 1/135 = 0.7 % (p=0.021). Root cause is D1-bias-lag (Q4 leak #3): when price rapidly rotates bullish, H1 catches up immediately but D1 stays bearish for ~2 weeks, suppressing every SHORT attempt during down-moves.
- **WR decays with regime churn.** Jan 90 % → Apr 33 %. Slice 1-2 vs 4-5 p=0.038.
- **poi_zone=premium n=6 0 % WR** — ship as shadow logger today.

### Q6 — "Are we executing correctly?"

**Yes.** Agent C independently reimplemented the simulator and reproduced 37/37 CANDIDATE outcomes bit-exactly. Cold-reviewer spot-checked all L2 + BLOCKED counterfactuals against raw CSV — 100 % reproduction. Agent A's claim of "3 simulator-artefact wins" (MAE > 2R post-fill on 2026-01-27, 2026-02-25, 2026-02-26 NY) was debunked by the review's CSV replay: actual post-fill MAE was 0.49R / 0.33R / 0.81R — all three filled AND TP'd in the same candle. **The 66.7 % WR headline stands.**

Execution observations worth monitoring:
- **Fill lag is long**: median ≈ 240-420 min (signal → limit fill), max 63 h. Several losses were "held through regime shift" (limit filled 1-2 days later when the bias had already flipped). This is structural to limit-orders; not a bug. Consider shadow-logging a "time-in-limit" metric.
- **sl_buffer_applied is 0.0 in 203/203 trade-parameters records.** The prompt doesn't enforce a buffer. If the prompt were tweaked to require e.g. `sl_buffer >= 5pt` on NAS100, leak #1 disappears entirely. But that's a WF-1 prompt change; not today.

---

## Ranked actions

| # | Action | Expected R | Risk | Approval |
|---:|---|---:|---|---|
| 1 | `verification.py:522/536` strict-`<` → `<=` on sl_beyond_ob | +13.5R NAS100 / Q | Low (boundary-precision) | CEO (trading-logic change) |
| 2 | Research max_kz_trades 1→2 relaxation | +16R NAS100 / Q | Medium (correlation-group) | CEO + cross-instrument data first |
| 3 | D1-bias-lag shadow logger (alert on D1 vs H4/H1 divergence ≥N candles) | Prevents future W14s | Zero (log-only) | No approval (allowed by CLAUDE.md §"shadow data collection") |
| 4 | poi_zone=premium shadow filter (promote to hard filter only after +20 more premium CANDs continue 0 % WR) | Up to −6R drag eliminated | Zero (log-only) | No approval |
| 5 | Backward-audit: does sl_beyond_ob bit-exact pattern exist on XAUUSD historical? | Verify leak #1 is not NAS100-only | Zero | No approval (research) |
| 6 | Backward-audit: has D1-bias-lag silently bitten XAUUSD NO_TRADE days? | Sizes the W14 leak cross-instrument | Zero | No approval (research) |

**Do NOT** rerun the sim on Sonnet — it already ran (cost math confirms bit-exact Sonnet pricing; the "claude-opus-4-5" strings in `raw_response.model_used` are AI hallucination).

---

## Key numbers (authoritative, cold-reviewed)

| Metric | Value |
|---|---|
| Evaluated M15 candles | 1 600 |
| AI calls | 818 @ $0.028 avg |
| Sim cost | $22.97 (bit-exact Sonnet-4.6) |
| Final CANDIDATEs | 37 |
| WR resolved (22W/11L) | 66.7 % |
| Cum R | +22.03R |
| Exp R/trade | +0.668R |
| CAND rate (of AI-reached) | 4.5 % |
| CAND rate (of total) | 2.3 % |
| XAUUSD comparison | 62 % WR / 10.3 % CR (from CLAUDE.md) |
| Leak #1 recovery (standalone) | +13.5R |
| Leak #2 recovery (standalone) | +16.02R |
| Leak #1 + #2 joint recovery | +36.5R |
| W14 D1-bias-lag episode | 54/54 bearish during +4.20 % rally |

---

## Caveats

1. **n=33 resolved.** Binomial p=0.080 vs 0.5 — the 66.7 % WR is suggestive, not proven. Slice 1-2 (early regime) is cleanly significant; slice 4-5 (late regime) is indistinguishable from coin-flip.
2. **Temporal dependence.** 10 trading days produced 2 CANDIDATEs each; 5 of those pairs exited on identical candles. Deduplicated independence: 29 trades at 65.5 % WR.
3. **Single-instrument, single-quarter.** NAS100 regime was V-shaped (−13 % DD + 17 % rally). Results may not generalize to trending-only or choppy-only quarters.
4. **Leak #1 fix is a gate relaxation.** Per CLAUDE.md "new safety gates (additive protection only) → CEO required." Relaxing an existing gate requires CEO explicit approval even if it looks like a bug fix. Do NOT ship without call.
5. **prompt alternative** — a prompt change mandating `sl_buffer_applied >= 5pt` (NAS100) eliminates leak #1 cleanly but touches `prompts/` (WF-1 territory, heavier validation burden). The gate fix is the lower-risk minimal-viable path.
6. **EURUSD simulation completed and is sitting at `research/t7_live_simulation/EURUSD_t7_simulation.json` (4.3MB)** — same analysis pipeline could be run to triangulate leak #1 + leak #2 across a currency instrument. Recommended before CEO approves #1 / #2.

---

## Verification chain

Every numerical claim in this synthesis is spot-checked by at least two independent pipelines:
- Agents A/B/C/D: 4 parallel Opus-4.7 agents, independent analysis scripts under `analysis/_*.py`.
- Agent E (review): independent CSV replay + code-reference verification; graded A (C), A- (D), B+ (A), B- (B); caught and invalidated three agent errors ("Opus-4.5 ran this", "3 simulator-artefact wins", "CR gap is model mismatch").
- Raw data preserved at `research/t3_1_eurusd_nas100_validation_2026-04-19/nas100_slice_{1..5}/NAS100_t7_simulation.json`.

_Chairman: Claude Code, session 33, 2026-04-19._
