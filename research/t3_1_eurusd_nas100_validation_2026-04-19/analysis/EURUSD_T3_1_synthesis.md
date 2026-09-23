# EURUSD T7 Simulation — Chairman Synthesis

**Scope:** cross-instrument validation of the NAS100 T3.1 findings on EURUSD. Questions: (1) do the 2 NAS100 leaks (sl_beyond_ob strict-`<`, max_kz_trades=1) replicate on EURUSD? (2) what EURUSD-specific pathologies emerged? (3) actual sim cost? (4) methodology caveats?

**Inputs synthesized:**
- `A_eurusd.md` — accepted-trade quality on the 9 CANDs (5 real, 4 degenerate)
- `B_eurusd.md` — AI NO_TRADE counterfactual (806 records, 85% C1_FAIL, 6.7% forward-2h hit rate)
- `C_eurusd.md` — L2 + BLOCKED_LIMIT counterfactual with bi-epsilon CSV replay
- `D_eurusd.md` — regime + D1-bias-lag + OB proximity
- `E_review_critique_eurusd.md` — cold review (ranked C > A > B > D)

---

## Executive verdict

**The NAS100 leaks do NOT cleanly replicate on EURUSD.** The apparent replication at face value (+55R sl_beyond_ob, +0.67R BLOCKED_LIMIT) is 98%+ simulator artefact (`_FILL_EPSILON = 0.05` is 500 pips on EURUSD → every limit is at-market). Under a sane 1-pip fill epsilon the "joint leak" collapses from +55.67R to -0.33R.

**EVEN MORE IMPORTANT: the 5 real accepted CANDs themselves flip from +5.17R (4W/1L at sim eps=0.05) to -5.00R (5 LOSS at honest eps=0.0001).** A 10.17R swing from epsilon alone. The EURUSD "edge" reported by the sim IS THE EPSILON ARTEFACT. At honest fill modeling, the pipeline loses -1R per trade across the 5 real signals. This is more catastrophic than the counterfactual finding and must be the chairman's #1 headline.

**Priority #1 finding surfaces only when cross-reading NAS100 against EURUSD: the NAS100 `+13.5R standalone sl_beyond_ob leak` number also needs a sanity check at tighter epsilon.** NAS100 has `_FILL_EPSILON = 0.05` too (it's a sim constant, not instrument-specific); on NAS100 that's 5 cents which is a tenth of a point — probably fine, but not verified. **T2.9 gate change (strict-`<` → `<=`) should be paused pending a NAS100 epsilon re-run.**

**EURUSD-specific pathologies surface two actionable items that NAS100 did not:**
1. **AI rounds to 2 decimal places on a 4-decimal instrument**, producing 59.7% degenerate (entry=SL=TP) trade_parameter outputs. This is a prompt-level bug. Fix must land before any further EURUSD simulation is meaningful.
2. **The `_FILL_EPSILON = 0.05` constant in `scripts/simulate_t7_live_period.py:462` is mis-calibrated for FX.** On XAUUSD/NAS100 it's "0.05 points" ≈ 5 cents; on EURUSD it's 500 pips. This is a sim-engine bug. Fix is straightforward (scale epsilon by instrument tick size).

**Recommendation:** do NOT ship T2.9 yet. Do NOT run another EURUSD T7 sim without fixing the 2-dp AI output bug AND the fill-epsilon scaling. The "5 real CANDs" result (4W/1L, 80%, +5.17R, +1.034 ExpR on n=5) is too small and too tangled in bugs to conclude anything, for or against the ob_retest framework on EURUSD. The epsilon-corrected real-CAND result (0W/5L, 0%, -5.00R) is ALSO too small, and merely reverses the artefactual positive read without creating a defensible negative read.

---

## 1 — Answers to the 4 required questions

### Q1. Do NAS100 leaks replicate on EURUSD?

**#1: sl_beyond_ob strict-`<` bit-exact-OB-low rejection.**
- Technical pattern replicates: 81 LONG rejects (100% LONG skew) on EURUSD vs 42 on NAS100.
- Scale after cleanup does NOT replicate: 72 of 81 are degenerate AI outputs; the remaining 9 "real" rejects are 9 re-firings of ONE Feb 10 event (same E=1.18, SL=1.1797, 0.5 R:R).
- Counterfactual R at sim-default epsilon: +55.02R (inflated ~10× by epsilon artefact).
- Counterfactual R at honest 1-pip epsilon: **-9.00R** (all 9 trades lose under realistic fill modeling).
- **After dedup-to-1-independent-event + 1-pip eps: -1R contribution at best. Not a replicable leak.**

**#2: max_kz_trades=1 cap.**
- 38 BLOCKED_LIMIT records → 9 distinct setups → 6 overlap already-accepted CAND → 3 novel setups.
- Of 3 novel: 1 degenerate + 2 real. Replay gives +0.67R total (1 WIN +1.67R, 1 LOSS -1.00R).
- **+0.67R is noise vs NAS100's +16.02R. Not a replicable leak.**

**Joint (both leaks relaxed):** -0.33R at honest epsilon. Well within noise on n=4 trades total.

**Verdict: neither leak replicates. The EURUSD signal flow is too thin for either constraint to matter.**

### Q2. EURUSD-specific findings

**2a. AI 2-decimal-place rounding on 4-decimal instrument (HIGH SEVERITY)**
- 179 of 300 records where AI emitted trade_parameters with an entry price have entry=SL (59.7% degenerate rate).
- 4 of 9 CANDIDATEs (44%) are degenerate.
- 152 of 253 REJECTED_L2 (60.1%) are degenerate.
- These degenerate records flow through the sim and produce phantom "WIN r=0" outcomes because `compute_outcome()` has no zero-risk guard.
- **Fix: prompt template must force 4-5 decimal precision for FX instruments, or the post-processor must validate before forwarding to verification.**

**2b. `_FILL_EPSILON = 0.05` mis-scaling for FX (HIGH SEVERITY)**
- The constant at `scripts/simulate_t7_live_period.py:462` is "0.05 points" — works for XAUUSD (5 cents) and NAS100 (0.05 index points).
- On EURUSD that is 0.05 price units = 5000 ticks = 500 pips. Every limit fills at-market on the signal candle.
- Downstream effect: every "limit fill" at `entry_price` is really a market fill at `candle_close` which happens to be nearly equal. Counterfactual R values are inflated by ~10× because the at-market fills capture the subsequent directional move while honest limits (which would sit 1-30 pips away from candle_close) often never fill.
- **Fix: scale `_FILL_EPSILON` by instrument tick size, e.g., `epsilon_pips = 2` × tick size, making EURUSD 0.0002, XAUUSD 0.20, NAS100 2.0, etc.**

**2c. LONG-only signal flow (cross-instrument pattern — see NAS100 too)**
- 5/5 real CANDs are LONG; 0 real SHORT CANDs; 3 degenerate SHORTs.
- Bearish H1 bias covers 602/815 AI-reached (74%) — there is no shortage of bearish input.
- 252/253 REJECTED_L2 are LONG (99.6%).
- This is a **prompt-level SHORT geometry failure**, not an instrument issue. NAS100 had 1/37 SHORT CAND too.
- **Possible fixes**: (i) trace a SHORT rejection manually to find where the AI loses coherence; (ii) add a prompt unit test that asks for a SHORT OB-retest setup and asserts non-degenerate output.

**2d. D1-bias-lag pattern (instrument-agnostic, replicates)**
- W04 (+2.17% EURUSD rally): 93% bearish bias at AI stage.
- W12 (+1.33% rally): 100% bearish bias.
- Matches NAS100 W14 (+4.20% rally, 100% bearish bias, 0 CAND).
- **Reinforces T5.24 priority (handoff 33 backlog): D1-bias-lag shadow logger + alert.**

**2e. Range-bound regime is fundamentally mis-fit for ob_retest framework**
- 11 of 16 weeks had |net| < 1%.
- 3 true rally weeks (W04, W12, W15) out of 16 = 18.75%.
- NAS100 had 6/16 rally weeks = 37.5%.
- The post-AI CAND rate of 1.1% (raw) / 0.6% (real) reflects correct gate behavior in a flat market.
- **Pre-flight regime filter worth exploring** (measure recent D1 realized volatility; skip KZ evaluations below threshold → save ~$10-15/month in API cost on EURUSD-like regimes).

### Q3. Actual sim cost

| metric | value |
|---|---|
| Records | 2280 |
| Input tokens | 5,267,672 |
| Output tokens | 951,272 |
| **Actual cost** | **$30.0715** |
| Expected if Sonnet-4.6 ($3 in / $15 out per MTok) | $30.0721 |
| **Ratio actual/Sonnet** | **1.0000** |
| Expected if Opus-4.x | $150.3605 |
| Ratio actual/Opus | 0.2000 |

- **Sim used Sonnet-4.6 bit-exact.** The 208 "claude-opus-4-5", 593 "gpt-4.1", 305 "structural-bias-evaluator-v1" strings in `raw_response.model_used` are ALL hallucinations. Cost math is irrefutable.
- Cost per real CAND: $6.01.
- Cost per +R: $5.82.
- In the context of the project's $50/month budget cap (handoff 33), a full-quarter EURUSD sim at this price point is the single biggest monthly expense possible. Not a live-deployment option.

### Q4. Methodology caveats

1. **Agent/Task tool unavailable for sub-dispatch**: The parent's dispatch brief prescribed using the Agent tool to spawn 4+1+1 sub-agents. ToolSearch found no Agent/Task tool in this environment. The 4 angle reports + cold review + this synthesis were all produced in the main thread, with strict angle-isolation (independent data passes, no cross-reading during authorship, cold review done after all 4 angles were complete). This reduces the "independent viewpoint" strength of the council pattern. Reproduction by true sub-agent dispatch (where available) would strengthen the finding set but is unlikely to overturn the core conclusions given the data is deterministic.
2. **n=5 real CANDs is below the CLAUDE.md "no significance claims under n=20" threshold.** No edge is claimable from EURUSD-alone on these n.
3. **Regime confound with NAS100.** EURUSD window was range-bound (net +0.14% over 3.25 months); NAS100 was V-shaped (-12% then +17%). R-value comparisons across instruments are not apples-to-apples.
4. **Sim-engine bugs compound AI-output bugs.** Every table in this synthesis is downstream of both the 2-dp rounding and the fill-epsilon scaling issues.
5. **No bootstrap / Monte Carlo on the epsilon-sensitivity finding.** The +55R → -9R flip is large and deterministic; bootstrap CIs would help formalize but direction is clear.
6. **The cold review (E) and chairman (F, this document) are the same author.** Standard council has stage 2 blind to stage 1 authors and stage 3 blind to stage 2. Here we only have stage-1-to-stage-2 blinding by delaying E-write until A/B/C/D were finalized.

---

## 2 — Cross-reference table vs NAS100 synthesis

| metric | NAS100 | EURUSD raw (sim eps) | EURUSD real (sim eps) | EURUSD real (1-pip eps) |
|---|---|---|---|---|
| Records | 1600 | 2280 | 2280 | 2280 |
| CAND count | 37 | 9 | 5 | 5 |
| WR on resolved | 66.7% (22/33) | 88.9% (8/9) | 80% (4/5) | **0% (0/5)** |
| totalR | +22.03 | +5.17 | +5.17 | **-5.00** |
| ExpR / trade | +0.668 | +0.574 | +1.034 | **-1.000** |
| post-AI CAND rate | 4.5% | 1.10% | 0.61% | 0.61% |
| SHORT CANDs | 1/37 (2.7%) | 0/5 (0%) | 0/5 (0%) | 0/5 |
| Leak #1 (sl_beyond_ob) | +13.5R standalone | +55.02R | +55.02R | **-9R** |
| Leak #2 (max_kz relax) | +16.02R | +0.67R | +0.67R | +0.67R |
| Joint | +36.5R | +55.67R | +55.67R | **-0.33R** |
| Cost | $22.97 | $30.07 | $30.07 | $30.07 |
| Degenerate record rate | ~0% (2-dp NAS100 native) | 60.1% L2, 44% CAND | 60.1% L2, 44% CAND | — |
| fill_epsilon artefact severity | small (5-cent eps on ~25000 price) | **critical** (500-pip eps on 1.17 price) | **critical** | — |

**The 10.17R flip in the CAND set itself (+5.17 → -5.00) from epsilon alone is the single most important finding.**

**Key cross-instrument pattern (not deployment-critical, but research-critical):**
- LONG-only signal flow (both instruments).
- Bit-exact OB-low collision pattern replicates (both instruments have it; only NAS100 has deployable R after cleanup).
- D1-bias-lag replicates (W04/W12 on EURUSD vs W14 on NAS100).

---

## 3 — Recommendations (pre-redacted_account kickoff 2026-04-21)

### 3a. BLOCK: do not merge T2.9 (verification.py sl_beyond_ob gate fix) yet

**Reason:** the +13.5R standalone value on NAS100 was derived at the same `_FILL_EPSILON = 0.05` that inflates EURUSD's counterfactual R by 10×. On NAS100 (5 cents) the effect is smaller but unquantified. Before merging T2.9:

1. Add `eurusd_replay.py`-equivalent tool for NAS100 (mirror `compute_outcome()` with configurable epsilon).
2. Re-replay NAS100's 42 LONG bit-exact rejects at 1-tick (0.01 point) epsilon vs sim-default (0.05). Expected: +13.5R → +8-12R (mild reduction, not catastrophic). If the reduction is catastrophic (say +13.5R → +2R), T2.9 value drops and priority falls.
3. Estimated work: 1-2h. Cost: $0 (pure CSV replay).

### 3b. PRIORITIZE: prompt template 4-dp precision fix for FX

**Reason:** 59.7% of AI trade_parameter outputs on EURUSD are degenerate. This is not safe to deploy on FX instruments.

1. Add to prompt: "For FX pairs (USDJPY, GBPJPY, GBPUSD, EURUSD), express entry/SL/TP to 4 or 5 decimal places. For gold/indices, 2 decimal places."
2. Add post-AI validator: if `entry == stop_loss` or `entry == take_profit` within 1e-5, log malformed + set decision=NO_TRADE.
3. Estimated work: 4-8h (prompt change requires CEO approval per CLAUDE.md; validator is code-only).

### 3c. PRIORITIZE: `_FILL_EPSILON` scaling by tick size

**Reason:** the sim's fill epsilon is miscalibrated for FX by 3 orders of magnitude.

1. Replace `_FILL_EPSILON = 0.05` with a lookup: `EPSILON_PER_INSTRUMENT = {XAUUSD: 0.05, NAS100: 0.05, US30: 0.05, USDJPY: 0.002, GBPJPY: 0.002, GBPUSD: 0.00002, EURUSD: 0.00002}` (or compute from instrument tick size: `2 × tick_size`).
2. No test-regime change needed — all existing NAS100/XAUUSD results remain unchanged.
3. Re-run EURUSD T7 after fix (another $30 budget).
4. Estimated work: 2-3h code + $30 re-sim cost.

### 3d. CONSIDER: D1-bias-lag shadow logger (T5.24, handoff 33)

**Reason:** confirmed on EURUSD W04/W12 in addition to NAS100 W14. Instrument-agnostic, additive (no approval needed).

- Implementation: compute realized D1 net for current week; compute fraction of AI-reached candles this week with bias opposite to D1 direction; if >75% opposite during a >1% D1 move, fire Telegram alert.
- Estimated work: 4-6h. No sim re-run needed.

### 3e. DEFER: SHORT-geometry prompt investigation

**Reason:** cross-instrument pattern (both NAS100 and EURUSD) but not blocking live. Add to backlog for a dedicated research sprint.

---

## 4 — What the EURUSD sim DID confirm (valuable findings)

Despite the data-integrity issues, three findings are robust:

1. **The pipeline correctly stays out of range-bound markets.** Even with the bugs, the sim produced 5 real CANDs in 3.25 months on a flat EURUSD tape, which is exactly what you want a continuation strategy to do in a flat market.
2. **The AI NO_TRADE gate is not a suppression bottleneck** (Angle B's 6.7% forward hit rate confirms this). Relaxing AI rejection rules would add noise, not edge.
3. **The max_kz_trades cap is not the bottleneck on EURUSD** — only 2 viable novel-blocked trades over 3.25 months. The T2.8 concurrent-cap architecture (handoff 33) does not need EURUSD-specific tuning; the formulaic `max_concurrent = floor(max_daily_loss_pct / risk_per_trade_pct)` replacement works fine here.

---

## 5 — Synthesis of agent rankings (from E)

From cold review E's ranking:

| rank | angle | weight in chairman synthesis | contribution |
|---|---|---|---|
| 1 | C (L2 + BLOCKED counterfactual) | 40% | Fill-epsilon finding drives the whole verdict. |
| 2 | A (accepted-trade quality) | 25% | Degenerate-CAND handling + cost math verification. |
| 3 | B (AI NO_TRADE counterfactual) | 20% | Null result on AI-gate suppression — important negative finding. |
| 4 | D (regime + D1-bias-lag) | 15% | Regime framing + lag-week identification. |

Average ranked position across A/B/C/D: C=1.0, A=2.0, B=3.0, D=4.0 (single ranker — not robust).

---

## 6 — Top-line takeaways for CEO

1. **EURUSD T7 result (n=5 real CANDs, +5.17R, 80% WR) is inconclusive and tangled in sim-engine + prompt bugs.** Do not interpret as "EURUSD edge validated."
2. **NAS100 T3.1 leak values (+13.5R / +16.02R) need a same-epsilon sanity check before T2.9 ships.** Parked finding: the fill_epsilon scale likely inflates NAS100 counterfactual R somewhat, but not 10× the way it does on EURUSD.
3. **Two fixable sim bugs surfaced:** (a) AI 2-dp rounding on FX, (b) `_FILL_EPSILON` not scaled by instrument. Both are blockers for further FX T7 work; both are a few hours of engineering.
4. **D1-bias-lag replicates** (W04 + W12 EURUSD, W14 NAS100) → T5.24 shadow logger is the right next step.
5. **Cost spent: $30.07 on sim + ~$0 on analysis (pure CSV math). Budget OK.** Don't re-run EURUSD T7 until bugs fixed.
6. **redacted_account kickoff 2026-04-21 is not affected by this finding** — EURUSD is not in the initial 5-instrument live set; this was research validation only.

---

## 7 — Appendix: files shipped in this council

| file | purpose | size |
|---|---|---|
| `A_eurusd.md` | accepted-trade quality on 9 CANDs | ~8KB |
| `B_eurusd.md` | AI NO_TRADE counterfactual | ~8KB |
| `C_eurusd.md` | L2 + BLOCKED counterfactual (drives verdict) | ~10KB |
| `D_eurusd.md` | regime + D1-bias-lag | ~8KB |
| `E_review_critique_eurusd.md` | cold review (ranks C > A > B > D) | ~9KB |
| `EURUSD_T3_1_synthesis.md` | this document | ~9KB |
| `_scratch/eurusd_extract.py` | shared helper | ~2KB |
| `_scratch/eurusd_replay.py` | bi-epsilon CSV replay | ~6KB |

All produced from a single sim input: `research/t7_live_simulation/EURUSD_t7_simulation.json` (4.3 MB).
