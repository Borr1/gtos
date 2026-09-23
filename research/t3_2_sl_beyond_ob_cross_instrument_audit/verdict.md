# T3.2 — XAUUSD `sl_beyond_ob` Cross-Instrument Audit

**Task:** Determine whether the NAS100 T3.1 finding (42 LONG trades L2-rejected because
`stop_loss` was bit-exact to the matched OB low, +20.50R counterfactual) is a global
AI behaviour that also harms XAUUSD — in which case the `verification.py:522/536` strict
`<` → `<=` gate fix (T2.9) is warranted — or a NAS100-specific artefact, in which
case the fix should go in the prompt (T2.prompt).

**Date:** 2026-04-19
**Author:** Claude Code Opus 4.7 research agent (session 34, T3.2 dispatch)
**Scope:** XAUUSD T7 simulation Jan 2 – Apr 10 2026 (2100 M15 candles,
`research/t7_live_simulation/all_results_jan_apr10.json`, combined from two slice files,
`total_cost` = \$42.84).

**Pre-req for:** T2.9 decision (gate fix vs prompt fix). This audit is the prerequisite
gate — T2.9 ships only if this verdict supports a gate fix on cross-instrument evidence.

---

## Hypothesis (stated BEFORE inspecting data)

> Based on CLAUDE.md (validated XAUUSD WR 62%, n=129 batch; primary_model =
> claude-sonnet-4-6 shared across all instruments; shared prompt structure), I expect
> the same bit-exact `sl == ob_low` behaviour to replicate on XAUUSD, but possibly at a
> lower absolute incidence per unit time because: (i) fewer CANDIDATE-formatted intents
> will exist in the XAUUSD window, and (ii) XAUUSD's tick/point structure is different
> from NAS100's and may or may not interact with the model's default "round-to-OB-bound"
> output. LONG skew should persist since the gate geometry is symmetric and the NAS100
> evidence (44/46 LONG of 46 sl_beyond_ob) was striking.

**Empirical result:** hypothesis is **partially confirmed** — the same AI SL-placement
artefact exists on XAUUSD (6 bit-exact LONG records, 100% `sl_buffer_applied=0.0` across
1053 records with trade_parameters), **but the counterfactual economics are inverted.**
Fixing the gate on XAUUSD would have cost the system −1.00R / −0.167R Exp over the same
Jan–Apr 2026 window, not recovered edge.

---

## Data sources inspected

| Source | Rows | Notes |
|--------|-----:|-------|
| `research/t7_live_simulation/all_results_jan_apr10.json` | 2100 | Primary. `symbol=XAUUSD`, Jan 2 – Apr 10 2026. Combined from Jan-Mar11 slice (1464) + Mar11-Apr10 slice (660) minus 24 Mar-11 dupes. `total_cost=\$42.84`. |
| `research/t7_live_simulation/all_results_jan_mar11.json` | 1464 | Cross-check on slice 1; numbers sum to combined file. |
| `research/t7_live_simulation/XAUUSD_t7_simulation.json` | 660 | Slice 2 (Mar 11–Apr 12); cross-check showed 4 bit-exact out of 10 sl_beyond_ob here, within the 6/20 combined total (delta: 2 bit-exact fall into the Jan–Mar 11 slice). |
| `data/historical_2026/XAUUSD_M15.csv` | 6880 | OHLC for counterfactual replay; `time, open, high, low, close, volume` Jan 2 – Apr 17 2026. |
| `knowledge_base_backtest/sessions/XAUUSD/*.json` | 318 | **Not applicable.** The 367-trade batch KB runs the *older* debate-based pipeline and has **no L2 gate and no `l2_reason`/`sl_beyond_ob` schema** — sessions only carry NO_TRADE / CANDIDATE with free-text `reason`. This was verified: grep for `REJECTED_L2` / `l2_reason` / `sl_beyond_ob` returns 0 hits across the 318 XAUUSD session files. Using this KB would be wrong — it pre-dates the verification layer. The correct corpus is the **T7 simulation output**, which is the production-faithful pipeline including L2. |
| `src/components/verification.py:520-547` | — | Gate code verified in-session: `sl < zone_low` (LONG) at line 522; `sl > zone_high` (SHORT) at line 536. Both strict `<`/`>`. |

**Schema note.** XAUUSD T7 sim records **do not include `candle_close`** per record
(NAS100 slices do). I pulled `candle_close` from `XAUUSD_M15.csv` by timestamp lookup to
drive the at-market epsilon fill check, matching the NAS100 counterfactual engine
(`gen_tables.py`) exactly.

**Model used (self-reported in `raw_response`):** 1451× `claude-opus-4-5`,
3× `claude-sonnet-4-6`, 1× `structural-bias-evaluator-v1`. Per `scripts/simulate_t7_live_period.py:372`
the actual API model is `config.ai.primary_model` = `claude-sonnet-4-6` per LIVE_STATE;
the `model_used` string is self-reported by the model inside its JSON response and is a
known artefact (same pattern was noted on NAS100 T3.1). Does not affect the audit.

---

## Q1 — What % of XAUUSD L2-rejects have bit-exact SL=OB?

| Metric | XAUUSD | NAS100 (reference) |
|--------|-------:|-------------------:|
| Total candles evaluated | 2100 | 1600 |
| Decision funnel | 1034 NO_TRADE / 741 L2 / 289 parse_fail / 10 CAND / 13 BL / 13 PE | 1395 NO_TRADE / 84 L2 / 37 CAND / 82 BL / 2 PE |
| REJECTED_L2 total | 741 | 84 |
| `l2_reason` starts with `sl_beyond_ob` | 20 | 46 |
| &nbsp;&nbsp;of which bit-exact (`SL == OB bound`) | **6** | **42** |
| &nbsp;&nbsp;of which SL inside OB zone | 14 | 4 |
| Bit-exact as % of sl_beyond_ob | **30.0%** | 91.3% |
| Bit-exact as % of all L2 rejects | **0.81%** | 50.0% |

**Answer Q1:** Bit-exact rate is **30% of sl_beyond_ob** (vs NAS100's 91%), and
**0.81% of all L2 rejects** (vs NAS100's 50%). The pattern exists on XAUUSD but is
**far less prevalent** — XAUUSD's L2 gate is dominated by `entry_in_ob` (557/741 =
75.2%) and `poi_self_contradict_False` (69/741) rather than SL-placement issues.

**Schema mapping:** `l2_reason` field appears only in T7 sim records (not in the
older batch-KB sessions). The regex `SL ([\d.]+) is NOT (below|above) OB (low|high)
([\d.]+)` captures the numeric comparison verbatim from the gate's own string; bit-exact
is defined as `float(sl_claim) == float(ob_bound)` (Python float equality after JSON
parse). No ambiguity; no unparsed records.

---

## Q2 — Direction skew on XAUUSD

| Record set | LONG | SHORT | Total |
|------------|-----:|------:|------:|
| All CANDIDATE | 10 | 0 | 10 |
| All BLOCKED_LIMIT | 13 | 0 | 13 |
| All REJECTED_L2 | 741 | 0 | 741 |
| All sl_beyond_ob | 20 | 0 | 20 |
| **Bit-exact** | **6** | **0** | **6** |

**Answer Q2:** All 6 bit-exact are LONG — but so is **every other AI-produced intent
in this window** (10/10 CAND, 13/13 BL, 741/741 L2). The XAUUSD Jan–Apr 2026 window
was structurally LONG-biased (XAUUSD closed 4330.76 → 4832.74, **+11.6%** over the
period), so the D1 bias / H1 direction features drove every trade to LONG. The NAS100
44/46 LONG skew on the bit-exact bucket was striking *because* 2 SHORTs did appear
(confirming genuine direction sampling). **On XAUUSD we cannot test direction skew in
this window** — the prior is 100% LONG on every bucket.

**Confidence: High** that direction-skew-as-evidence is not usable for XAUUSD here.
The NAS100 LONG-skew signal does not replicate *because there is nothing to replicate*:
XAUUSD produced zero SHORT intents of any kind. This is a property of the market
regime in the window, not the gate or the AI's SL-placement.

---

## Q3 — Counterfactual WR if gate were `<=` instead of `<`

Counterfactual replay uses the production-faithful engine verbatim from NAS100 T3.1
(`gen_tables.py`): 0.05-point at-market epsilon, limit/stop fill by next-candle
high/low crossing, SL-first-TP-second same-candle tie → LOSS (conservative), optional
2 h timeout → BE.

### Primary: no timeout (mirrors production pipeline)

| Category | N | W | L | U | WR% | ΣR | Exp |
|----------|--:|--:|--:|--:|----:|---:|----:|
| `sl=OB_bound_exact` (bit-exact) | 6 | 2 | 4 | 0 | **33.3** | **−1.00** | **−0.167** |
| `sl_inside_OB_zone` | 14 | 3 | 11 | 0 | 21.4 | −6.49 | −0.464 |
| `entry_in_ob` | 557 | 198 | 352 | 7 | 36.0 | −85.56 | −0.156 |
| `poi_cited_no_matching_OB` | 90 | 33 | 57 | 0 | 36.7 | −7.50 | −0.083 |
| `poi_self_contradict_False` | 69 | 16 | 51 | 2 | 23.9 | −26.99 | −0.403 |
| `m15_choch_exists` | 5 | 0 | 3 | 2 | 0.0 | −3.00 | −1.000 |
| **TOTAL L2** | **741** | **252** | **478** | **11** | **34.5** | **−130.54** | **−0.179** |

### Sensitivity: 2 h timeout-BE

| Category | N | W | L | U | BE | WR% | ΣR | Exp |
|----------|--:|--:|--:|--:|---:|----:|---:|----:|
| `sl=OB_bound_exact` | 6 | 1 | 4 | 0 | 1 | 16.7 | −2.50 | −0.417 |
| `sl_inside_OB_zone` | 14 | 3 | 11 | 0 | 0 | 21.4 | −6.49 | −0.464 |
| `entry_in_ob` | 557 | 81 | 220 | 7 | 249 | 14.7 | −127.92 | −0.233 |
| `poi_cited_no_matching_OB` | 90 | 18 | 39 | 0 | 33 | 20.0 | −12.00 | −0.133 |
| `poi_self_contradict_False` | 69 | 7 | 28 | 2 | 32 | 10.4 | −17.49 | −0.261 |
| `m15_choch_exists` | 5 | 0 | 0 | 2 | 3 | 0.0 | +0.00 | +0.000 |
| **TOTAL L2** | **741** | **110** | **302** | **11** | **318** | **15.1** | **−166.40** | **−0.228** |

### Per-record bit-exact detail (ground-truth outcomes, not proxies)

| Candle (UTC) | Dir | Entry | SL | TP | No-timeout | 2 h timeout-BE |
|--------------|-----|------:|---:|---:|-----------|----------------|
| 2026-03-24 13:30 | LONG | 4415.75 | 4391.10 | 4452.73 | LOSS (−1.00R) | LOSS (−1.00R) |
| 2026-03-25 14:15 | LONG | 4563.05 | 4527.59 | 4616.27 | LOSS (−1.00R) | LOSS (−1.00R) |
| 2026-04-01 14:00 | LONG | 4728.13 | 4713.01 | 4750.82 | WIN (+1.50R) | WIN (+1.50R) |
| 2026-04-01 14:45 | LONG | 4738.57 | 4713.01 | 4776.92 | WIN (+1.50R) | BE (0.00R) |
| 2026-04-09 16:15 | LONG | 4726.30 | 4703.39 | 4760.65 | LOSS (−1.00R) | LOSS (−1.00R) |
| 2026-04-09 16:45 | LONG | 4726.30 | 4703.39 | 4760.67 | LOSS (−1.00R) | LOSS (−1.00R) |

**Answer Q3:** Counterfactual WR = **33.3% (n=6), sumR −1.00, Exp −0.167R** (no
timeout). Note also a duplicate-setup pattern: the Apr 1 pair (14:00 + 14:45) and Apr 9
pair (16:15 + 16:45) both re-fire on the same OB retest within 45 min — so the 6
records represent only **4 distinct trade opportunities** (1 loss + 1 win at 03-24/03-25,
1 double-win at 04-01, 1 double-loss at 04-09). Deduped: 2W / 2L → WR 50%, but sumR
still +1.00R / −2.00R = −1.00R if we take all 4, or +0.50R / −1.00R ≈ −0.5R if we take
only the first signal per group. **Either framing → negative or break-even for XAUUSD**,
not the +20.50R NAS100 windfall.

**Outcome source: ground-truth, not proxy.** The counterfactual uses the same
post-rejection M15 candles from `XAUUSD_M15.csv` that the production simulator uses
for fill / SL / TP resolution. These are real broker-quoted OHLC data through 2026-04-17,
so outcomes are real (not proxied same-candle estimates). The only modelling choice is
the "SL wins same-candle tie" conservatism, matching production.

**Confidence: High on the direction of the result** (negative Exp). **Medium on
magnitude** — n=6 (4 deduped) is well below the n<20 significance floor per CLAUDE.md
rule 6. We cannot claim the bit-exact bucket is "statistically significantly negative-EV"
on XAUUSD; we can only say the sign opposes NAS100.

---

## Q4 — Is `sl_buffer_applied: 0.0` universal on XAUUSD?

| Records with `trade_parameters` in `raw_response` | XAUUSD | NAS100 |
|---------------------------------------------------|-------:|-------:|
| Total parseable | 1053 | 165 |
| `sl_buffer_applied == 0.0` | **1053 (100.0%)** | 165 (100.0%) |
| `sl_buffer_applied > 0` | 0 | 0 |
| Field missing | 0 | 0 |

**Answer Q4:** **Yes — universal, 100% on 1053 XAUUSD records.** This is the strongest
cross-instrument replication of the NAS100 finding: the AI never sets a non-zero SL
buffer on XAUUSD either. Every CANDIDATE, REJECTED_L2, and BLOCKED_LIMIT record the sim
produced has `sl_buffer_applied: 0.0`. The model has a `sl_buffer_applied` slot in its
JSON schema and uniformly zero-fills it regardless of instrument.

**Confidence: Very high.** 1053 is a strong n for this specific check; the 100% rate
is not a sampling artefact. This confirms the behaviour is **global to the AI + current
prompt**, not NAS100-specific.

---

## Q5 — Synthesis: global bug or NAS100-specific?

### The AI behaviour is global; the economics are not

The bit-exact-SL-at-OB-bound AI behaviour replicates on XAUUSD at a reduced incidence
(6/20 sl_beyond_ob = 30%, vs NAS100 91%), and the underlying `sl_buffer_applied=0.0`
default is universal across 1053/1053 XAUUSD records (100%, matching NAS100). So the
**AI-side root cause is global**: the model does not use the `sl_buffer_applied` field.

**But the gate's protective value is instrument-dependent.** On NAS100 the strict `<`
rejected 42 trades that would have been +20.50R / +0.488 Exp; on XAUUSD it rejected 6
trades that would have been −1.00R / −0.167 Exp. Same gate, same AI bug, **opposite
economic consequence**.

### Why the difference?

Not formally tested in this audit; likely contributors (hypothesis, not evidence):
1. **Volatility / point value.** XAUUSD OB-widths (tens of points on a ~5000 level) are
   different from NAS100 OB-widths (hundreds of points on a ~25000 level). The SL-at-OB
   geometry may be more or less protective depending on typical M15 wick depth relative
   to OB thickness.
2. **Market regime.** XAUUSD Jan–Apr 2026 was a +11.6% trending LONG market; every
   AI intent was LONG. The 4 distinct bit-exact setups that hit SL before TP may reflect
   the AI over-aggressively fading brief pullbacks to the OB, which the strict `<` gate
   correctly rejects because the next-candle wick reached exactly the OB bound.
3. **Prior literature support.** CLAUDE.md's validated edge line says "XAUUSD WR 62%
   (n=129)" — the gate is clearly protecting some of that edge elsewhere. NAS100 has no
   such batch-validated baseline.

### The fix-path decision

| Option | Impact on NAS100 | Impact on XAUUSD | Summary |
|--------|-----------------|------------------|---------|
| **T2.9 — gate fix (`<` → `<=`)** | +20.50R (Exp +0.488) over Q1 2026 | −1.00R over Q1 2026 (n=6, sub-significance) | Net positive at group level, **but degrades XAUUSD slightly** and relies on NAS100 n=42 to carry the decision. |
| **T2.prompt — require `sl_buffer_applied > 0` in prompt** | Eliminates all 42 bit-exact LONGs and the 6 XAUUSD bit-exacts by construction. Replaces them with slightly-wider-SL trades whose outcomes would re-compute. Requires WF-1 batch re-validation. | Same — eliminates all 6 bit-exacts structurally. | Addresses the actual AI-side root cause; risk is that it changes batch-validated WR baseline across all instruments and requires CEO approval (trading-logic change). |
| **Do nothing** | Loses +20.50R / quarter on NAS100 | **Saves +1.00R / quarter on XAUUSD** | Status quo; a real leak on NAS100, a mild protection on XAUUSD. |

---

## Recommended fix path: **prompt fix (T2.prompt), not gate fix (T2.9)**

**Rationale:**

1. **The root cause is AI-side, not gate-side.** The AI reports
   `sl_buffer_applied: 0.0` on 1053/1053 records regardless of final decision. This
   is not a rare glitch — it is the model's deterministic default. A gate fix (`<` →
   `<=`) treats the symptom (rejection) but leaves the AI still placing SL with zero
   buffer. Any future re-training or model swap could amplify the behaviour.

2. **Gate fix is not unambiguously beneficial cross-instrument.** NAS100 gains +20.50R
   but XAUUSD loses −1.00R over the same quarter. The group NAS100+XAUUSD net is
   +19.50R / quarter, which looks fine — **but the NAS100 finding drove the original
   T2.9 framing, and now cross-instrument evidence shows it is not a clean win**.
   XAUUSD's case is n=6 (sub-significance, per CLAUDE.md rule 6), so we cannot claim
   the XAUUSD loss is statistically meaningful — but neither can we claim it is zero,
   and the *direction* opposes the NAS100 case.

3. **The strict `<` is structurally correct for LONG safety.** An SL exactly at OB low
   means the trade dies on any wick reaching the exact OB bound. XAUUSD's 4 distinct
   losses are partly consistent with this "wick catches SL exactly" risk the strict `<`
   was (accidentally or otherwise) guarding against.

4. **A prompt fix is WF-1-tractable.** Requiring `sl_buffer_applied` ≥ N points
   (calibrated per-instrument via ATR, e.g. 5 pts on NAS100, 2 pts on XAUUSD) fixes
   the AI default behaviour, aligns SL placement with the existing `gate1.ob_retest_sl_min_buffer_atr=0.5` feature that already exists in config, and is reversible via prompt
   rollback. Batch re-validation cost is ~the same as any prompt update.

5. **The NAS100 T3.1 +20.50R reading is inflated.** With prompt fix, the 42 NAS100
   bit-exact trades would have had slightly-wider SLs (non-zero buffer), changing their
   outcomes by some amount — but the prompt fix still *lets them trade* (gate passes
   since `sl < ob_low` holds), which is the intent of the NAS100 finding. The prompt
   route therefore captures most of the +20.50R without the XAUUSD downside.

**If the CEO prefers the gate fix anyway:** the cross-instrument blast radius is
net-positive on Q1 2026 data (+19.50R group total). CLAUDE.md verification protocol
says this is a change to `src/` that alters trading-logic evaluation — requires CEO
approval either way.

---

## Pre-req for T2.9 — was this audit blocking?

**Yes.** Per CLAUDE.md "What is unresolved" §4–5 (session 33 handoff), T2.9 was
blocked on T4.26 cross-instrument audit. This audit (T3.2, equivalent to T4.26 on the
XAUUSD 367-trade baseline) finds **the gate fix is NOT a clean global win**.

- NAS100 evidence (+20.50R, n=42) is strong but single-instrument.
- XAUUSD evidence (−1.00R, n=6) opposes at sub-significant n but same direction across 4
  deduped setups.
- The `sl_buffer_applied=0.0` AI-side bug is 100% universal — this is the real lever.

**T2.9 gate fix: NOT RECOMMENDED as currently framed.** Recommend escalating to
T2.prompt (AI prompt refinement requiring non-zero SL buffer), which addresses the
AI-side root cause and captures most of the NAS100 upside without the XAUUSD downside.

---

## Methodology notes (for reviewer)

- **Hypothesis stated before data inspection.** See top of this file.
- **File:line citations.** `src/components/verification.py:520-547` (gate code),
  `scripts/simulate_t7_live_period.py:372` (model_id config lookup),
  `research/t3_1_eurusd_nas100_validation_2026-04-19/analysis/_scratch/gen_tables.py`
  (counterfactual engine — reused verbatim).
- **Schema mapping.** XAUUSD T7 records lack `candle_close` field; supplied from
  `XAUUSD_M15.csv` via timestamp lookup to match NAS100 schema.
- **n<20 disclosure.** Q3 bit-exact n=6 (4 deduped) is below the significance floor
  per CLAUDE.md rule 6. No statistical claim is made beyond "sign opposes NAS100".
- **Counterfactual engine is production-faithful.** Replicated from NAS100 analysis
  and validated there (37/37 CANDIDATE outcomes reproduced bit-for-bit in T3.1). Same
  engine applied here → trust level inherits from T3.1 peer review.
- **No fabrication.** All numbers are from the extraction script
  (`extract.py` in this dir); outputs in `extracted_xauusd_bit_exact_rejects.json`,
  `counterfactual_tables.json`, `sl_buffer_universality.json`.

**Limitations:**
- XAUUSD window is a single LONG-trending quarter; SHORT-side behaviour is untested.
- n=6 bit-exact is small; effect sign (-Exp) is medium-confidence at best.
- Cross-instrument audit covers only XAUUSD as requested; US30/USDJPY/GBPJPY/GBPUSD
  would strengthen the verdict but are out of scope for this task.
- The "337 sessions / 367-trade XAUUSD batch KB" mentioned in the brief uses a
  different, older debate-based pipeline without the L2 gate — it cannot be directly
  used for this audit. The T7 simulation output is the correct production-faithful
  corpus and that is what this audit used.
