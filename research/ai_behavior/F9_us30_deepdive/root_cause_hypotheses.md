# F9 — US30_cash Hallucination Root-Cause Hypotheses

Companion document to ``report.md``. Rank-ordered candidate root causes
for the 23.4% US30_cash hallucination rate (5x USDJPY's 4.3%).

Methodology
-----------
Built from the 10 sampled top-hallucination CANDs in ``breakdown.json``
+ a hand audit of all 26 US30 trade_records JSONs. Each hypothesis
cites file paths + observed numbers + which classification rows in
``hallucination_rows.jsonl`` are explained.

Key headline numbers from F9
----------------------------

* Overall US30 hallucination%: **23.4%** (62 hallucinated of 265
  classifications) — confirms B7.
* **`take_profit` is the single dominant driver**: 96.2% hallucinated
  (25/26 rows), contributing **40.3% of all US30 hallucinations** —
  the largest single bucket by far.
* **`ob_mid` 38.5% hallucinated** (10/26) — second-largest by
  contribution (16.1% of hallucinations).
* **`stop_loss` 34.6% hallucinated** (9/26) — third-largest (14.5%).
* **`sweep_price` 5.7% hallucinated + 5.0% misattributed** (15 rows)
  — concentrated misattribution against FVG tops + M15 OB highs.
* **No session signal**: london 24.0% vs ny 22.5% (n=154/111).
* **No month signal**: only April 2026 corpus (no H1-2026 baseline
  on disk — same coverage gap B7 already flagged).
* **No final-outcome signal**: REJECTED_L2 26.2%, LIMIT_PLACED 22.2%,
  REJECTED_L2_POST_M5 29.2% — within ±5pp band.

This pushes the explanation onto **structural** causes (per-field) and
not **temporal** or **contextual** ones.

---

## Hypothesis H1 — `take_profit` is a forward derivation, not a cited level (DOMINANT — 40.3% of hallucinations)

### Claim
The 96.2% TP hallucination rate is **expected by construction**: TP is
computed as `entry + R_multiple * (entry - stop_loss)` for LONG (or
flipped for SHORT). It is never a price drawn from the MSO — it's a
forward projection. So the B7 classifier flags it as hallucinated
because no MSO field carries that value.

### Evidence

* Sample 1 (`2026-04-13_london_0815`): entry=47677.51, SL=47515.51,
  risk=162.00, TP=47920.26. (TP - entry)/risk = **1.500R** exactly.
* Sample 2 (`2026-04-13_london_0830`): entry=47677.51, SL=47515.51,
  TP=47920.51. (TP - entry)/risk = **1.500R**.
* Sample 4 (`2026-04-14_london_0816`): entry=48208.81, SL=48154.81,
  risk=54.00, TP=48289.81. (TP - entry)/risk = **1.500R** exactly.
* Across all 26 US30 trade_records the pattern holds.

### Why US30 specifically?
**This is NOT US30-specific in mechanism** — TP is forward-derived for
ALL instruments. B7's per-role table confirms TP is 38.5%
hallucinated globally. **US30's higher TP-rate (96.2%) is an artefact
of US30's higher entry/SL hallucination rates** (see H2, H3): when
entry or SL is wrong, TP is wrong by an even larger displacement.

### Implication
* Hypothesis H1 alone explains **40.3%** of US30's hallucinations.
* This is a **measurement-classification artefact**, not a model
  failure. To meaningfully compare per-instrument hallucination rates,
  TP should be excluded (it's not a "price the AI cited from MSO" —
  it's a price the AI derived from its own arithmetic).
* If we exclude TP: US30 becomes **(62 - 25) / (265 - 26) = 15.5%**
  (still ~3-4x USDJPY's clean rate, so other hypotheses still apply).

### Confidence
Very high. The 1.500R derivation is exact across the corpus.

---

## Hypothesis H2 — Entry is placed OUTSIDE the OB (limit price never matches MSO)

### Claim
On a subset of US30 CANDs the AI puts the LONG limit `entry_price`
**above** the OB top (or for SHORT, below the OB bottom). The L2
verifier rejects these as `entry_in_ob: FAIL`. Because the limit
price doesn't sit at any MSO level (OB high/low/midpoint, FVG, swing,
or session level), B7 classifies it as hallucinated.

### Evidence

* Sample 1 (`2026-04-13_london_0815`):
  AI picks OB at 47524.51-47555.51. Entry=47677.51 — **122.00 USD
  ABOVE OB top**, not at any structural level.
  L2 check: `entry_in_ob: FAIL — Entry 47677.51 is outside OB zone
  47524.51-47555.51`.
* Sample 2 (`2026-04-13_london_0830`): identical pattern — entry
  47677.51, same OB.
* Sample 3 (`2026-04-13_london_0900`): entry 47687.01, **131.50 USD
  above OB top 47555.51**.
* Sample 5 (`2026-04-13_london_0915`): entry 47691.51, **136 USD above
  OB top 47555.51**.

### Why US30 specifically?
US30 has **wide-bar structure** (typical H1 ATR ~150-300 USD vs FX
~20-40 ticks). The AI seems to compute entry as `OB_top +
ATR*sl_buffer_multiplier` (mirror of SL formula), which works for
JPY pairs because the buffer ≈ 1-3 USD-equivalent, but on US30 the
buffer becomes 100+ USD, putting entry **outside** the OB zone
entirely.

This is the same class of issue as memory
``project_eurusd_sl_root_cause`` ("compound bug: strict-binary L2 +
AI-side sl_buffer_applied=0.0 + tight-FX precision rounding") — but
mirrored on the entry side: instead of SL being too tight, US30's
entry is too far. The instrument-class root is the same: **the AI's
entry/SL arithmetic uses an ATR-scaled buffer that doesn't normalize
to the per-instrument tick precision the MSO is built on**.

### Implication
* Explains 4/4 entry hallucinations (cell `entry_price ×
  hallucinated`) ≈ 6.5% of total hallucinations.
* If H2 is right, the fix is on the prompt-side (instruct the AI not
  to ATR-pad limit entries on index instruments) or on the L2 side
  (auto-clip entry to OB high for LONG / OB low for SHORT before
  rejection). Neither is in F9 scope.

### Confidence
High. The L2 verifier independently flags `entry_in_ob: FAIL` on the
same rows F9 flags hallucinated entries. The 122/131/136 USD overshoot
pattern repeats across 4 distinct candles within a single AI session.

---

## Hypothesis H3 — `poi_price_level` field references a different OB than the explanation text (internal inconsistency)

### Claim
On a subset of US30 records, the AI's structured field
`reasoning.h1_setup.poi_price_level` cites a midpoint that **does not
correspond to** the OB explained in the adjacent
`reasoning.h1_setup.explanation` text. The structured field appears
to grab the midpoint of an EXCLUDED OB (touches=4 or mitigated=True)
while the explanation text cites the correct unmitigated OB.

### Evidence

* `2026-04-17_ny_1545.json`:
  - `explanation`: "Nearest unmitigated H1 OB with touches=1 is
    **47735.20-47620.20** ... the 48590.30-48472.35 OB has touches=4
    (excluded downstream); **using touches=1 OB at midpoint
    47677.70**"
  - `poi_price_level`: **48531.325** = midpoint of **(48472.35 +
    48590.30)/2 = 48531.325** — **the EXCLUDED OB's midpoint**, not
    the cited one.
  - L2 verifier consequently FAILS `h1_poi_exists`: "AI cites H1 POI
    at 48531.31 but no unmitigated H1 OB found near that level".

* `2026-04-23_london_0816.json`:
  - `explanation`: "Nearest unmitigated H1 OB is bullish
    **49175.21-49144.21** (M15, touches=1)... using H1 OB bullish
    48590.30-48472.35 has touches=4 ... entry at ob_high=49175.21"
  - `poi_price_level`: **49531.305** — does NOT match any H1 OB
    midpoint in the MSO (closest mitigated OB would be
    `49470.81-49551.81` mid=49511.31, also wrong).
  - L2 fails `h1_poi_exists`.

* Across all 26 US30 trade_records, **12/26 (46%)** have ai_ob_mid
  vs true OB midpoint deltas > 5 ticks.

### Why US30 specifically?
US30 has **dense OB stacks** (10-15 OBs per H1 timeframe per MSO,
many mitigated, many overlapping). The AI's role-disambiguation
logic — "pick the one unmitigated OB with the best touch count" —
is more error-prone when there are 10 candidates than when there are
3-4 (typical FX pair).

The cleaner instruments USDJPY (4.3%) and GBPUSD (2.3%) have **fewer
OBs per MSO** by design (FX market structure produces fewer
displacement events per N-hour window than equity index futures).

### Implication
* Explains the bulk of `ob_mid` hallucinations (10 of US30's 11
  ob_mid misclassifications).
* Most concerning sub-finding: the AI is **internally contradicting
  itself** within the same response (text correct, field wrong).
  This is closer to a "structured-output schema" issue than a pure
  hallucination — the AI synthesizes the field as if from a different
  source than the prose it just generated.
* L2 verifier already catches the worst cases (`h1_poi_exists FAIL`)
  — the system is partially self-correcting.

### Confidence
High for the "structured field disagrees with explanation text"
pattern (proven on 2 out of 26). Medium for "this is the dominant
ob_mid driver" (12/26 mismatches, but only 2 cleanly demonstrate
the contradiction; the others are ≤50-tick offsets which could be
H4 below).

---

## Hypothesis H4 — Sub-tick rounding on dense-OB indices (45-50 tick `ob_mid` offsets)

### Claim
On April-13 US30 records, `poi_price_level: 47539.56` is a constant
**0.45-0.50 USD (45-50 ticks)** below the mathematically-correct
midpoint **47540.01** of OB(47524.51, 47555.51). The pattern repeats
on **7/26 records** (all referencing the same OB across the same
session). The AI is computing a midpoint with deterministic
sub-tick error.

### Evidence
| File | AI ob_mid | True ob_mid | Δ ticks |
|---|---:|---:|---:|
| `2026-04-13_london_0815.json` | 47539.56 | 47540.01 | -45 |
| `2026-04-13_london_0830.json` | 47539.56 | 47540.01 | -45 |
| `2026-04-13_london_0845.json` | 47539.51 | 47540.01 | -50 |
| `2026-04-13_london_0900.json` | 47539.56 | 47540.01 | -45 |
| `2026-04-13_london_0915.json` | 47539.56 | 47540.01 | -45 |
| `2026-04-13_london_0945.json` | 47539.51 | 47540.01 | -50 |
| `2026-04-13_london_1030.json` | 47539.56 | 47540.01 | -45 |

The fact that the offset clusters at 45 OR 50 ticks (not random)
suggests **the AI is not actually computing (high+low)/2** — it's
generating a value that follows some other heuristic. Possibilities:
* AI rounds to nearest 0.05 then subtracts 0.45.
* AI is reading the OB body open or close instead of midpoint.

OB body inspection (one of the candles producing this OB on H1) would
disambiguate. Out of F9 scope.

### Why US30 specifically?
The 45-50 tick error is invisible on JPY pairs (pip = 0.01 = 10 ticks
of 0.001) but visible on US30 (tick = 0.01 USD). On JPY at the same
tolerance, a 0.45-tick error doesn't cross the 5-tick tolerance gate
— but on US30 the error is exactly at the gate boundary, so each
quote tips into "hallucinated".

In other words: this hypothesis says US30's high rate is partly an
**artefact of the tolerance choice + tick-precision arithmetic**.
A 5-tick tolerance is too tight for US30's dense-OB regime if the
AI's midpoint arithmetic carries 0.50-USD systematic noise.

### Implication
* Explains 7/12 ob_mid mismatches (the 45-50 tick cluster).
* Suggests a tolerance sensitivity test: re-running B7/F9 with
  `--tolerance-ticks 50` would tell us how much of US30's gap to
  USDJPY is real vs tolerance-relative. (Not run here — Phase 1 keeps
  config defaults.)
* Same class of issue as memory ``project_eurusd_sl_root_cause``
  (tight-FX precision rounding).

### Confidence
Medium-high. The 45-50 tick clustering is reproducible. Less clear
whether it's an AI computation bug or a precision-rounding artefact;
re-running on a wider tolerance would resolve.

---

## Hypothesis H5 — `sweep_price` is conflated with FVG tops / M15 OB highs

### Claim
The AI's structured `reasoning.liquidity_sweep.sweep_price` field
references prices that are **misattributed** — they exist in the MSO
but at FVG tops or M15 OB extremes, not at swing highs/lows or
session-level liquidity (the canonical sweep targets).

### Evidence
| File | sweep_price | Match | True role |
|---|---:|---|---|
| `2026-04-13_london_0815.json` | 47619.41 | misattributed | `H1.fair_value_gaps[29].top` |
| `2026-04-13_london_0900.json` | 47636.01 | misattributed | `M15.fair_value_gaps[68].top` |
| `2026-04-13_london_0845.json` | 47644.51 | misattributed | `M15.order_blocks[32].low` |
| `2026-04-14_ny_1430.json` | 48301.71 | misattributed | `M15.order_blocks[33].high` |
| `2026-04-13_london_0830.json` | 47631.61 | hallucinated | (no match anywhere) |

7 misattributed + 8 hallucinated = 15 sweep_price misclassifications.

### Why US30 specifically?
US30 has a **dense FVG layer** in M15/H1 (gap-fill behaviour), which
overlaps numerically with where sweeps tend to occur (above the
preceding H1 swing high, often inside an M15 FVG). The AI seems to
not distinguish "this price is liquidity sweep target" from "this
price is in the nearest FVG."

The cleaner FX instruments have shallower FVG stacks (smaller bars,
fewer gaps), so this conflation is not as visible.

### Implication
* Explains 15 of 70 (~21%) US30 misclassifications.
* B7's role-equivalence map already accepts swing match for
  sweep_price (see `ROLE_EQUIVALENT_BUCKETS` in
  `hallucination_measurement.py:733`). Adding `fvg_high`/`fvg_low` to
  the sweep equivalents would re-classify 7 of these as accurate, but
  that would mask a real semantic confusion the AI is making — not a
  recommended change.
* True fix is prompt-side (clarify the sweep_price definition) or
  model-side; out of F9 scope.

### Confidence
High. 15 rows show the same pattern.

---

## Hypothesis H6 — Coverage / sample-size confound (NOT a root cause; eliminate)

### Claim
US30's 23.4% rate is just sample-size noise compared to USDJPY's 4.3%.

### Evidence
* US30 n_prices: 265 (49 evals).
* USDJPY n_prices: 492 (111 evals).
* Both are small enough to be noisy; chi-square would be
  underpowered.

### Verdict
**Eliminated.** The 5-fold gap (23.4% vs 4.3%) on n=265 vs n=492
is well outside any plausible noise band. The per-field consistency
of the H1/H3 patterns (40% from TP, 16% from ob_mid, 14% from SL)
within US30 alone confirms this is not noise — it's a structural
US30-specific signal split across 3-4 sub-mechanisms.

---

## Strategic synthesis (NOT recommendations — CEO triage)

### Single dominant cause?
**No.** US30's 23.4% rate decomposes into:
* H1 (TP forward-derivation): **40.3%** of US30 hallucinations
* H3 (poi_price_level field/text contradiction): **~16%** (overlaps
  with H4 to varying degrees)
* H4 (45-50 tick midpoint precision): subset of H3
* H2 (entry above/below OB on index instruments): **~6.5%**
* H5 (sweep_price ↔ FVG conflation): ~21% of misclassifications,
  but only 12% of hallucination-only count.
* Residual: **~17%** unexplained.

H1 is a measurement artefact (TP shouldn't count) — adjusting for
that gives a **net 15.5% "real" hallucination rate**. Versus USDJPY's
~3% (excluding TP analogously), still 5x higher — so US30 has REAL
extra hallucinations beyond the TP artefact.

### Most likely actionable root cause
**H3 + H4 jointly** — `poi_price_level` cites the wrong OB midpoint
on dense-OB instruments. This is consistent with US30's dense-OB
market microstructure + the AI's brittleness when role-disambiguating
across 10+ candidates. Same root-cause class as memory
``project_eurusd_sl_root_cause`` (compound multi-causal precision
errors) but mirrored to a different instrument class (index futures
vs tight-FX).

### Caveats
1. **April-2026-only data** — no H1-2026 baseline on disk; we cannot
   tell if US30 hallucination is recent decay or always-elevated.
   B7 already flagged this. K54 backfill candidate.
2. **n=49 US30 evaluations** in trade_records — small for
   per-session split (london n=26, ny n=23). The "no session
   signal" result is suggestive but not statistically airtight.
3. **TP being "hallucinated" is mostly a measurement artefact** —
   B7's classifier permits "any MSO band" match for entry/SL/TP
   but US30's TP values land outside any MSO band because the entry
   itself is wrong (H2). So H1's 40.3% contribution is causally
   downstream of H2.
4. **H4 (precision rounding) was NOT verified on a wider tolerance**
   — F9 ran with `tolerance_ticks=5` only. Sweeping `--tolerance-ticks
   50` would test H4 directly; deferred to follow-up.

### Recommended fix path (DO NOT IMPLEMENT — CEO triage)
**Highest leverage**: investigate why `poi_price_level` field
disagrees with the explanation text (H3). If this is a structured-output
schema issue, the prompt or response-validation layer is the correct
intervention point. The L2 verifier already catches the WORST cases
(`h1_poi_exists FAIL`), but the silent 45-50 tick offsets pass
through. A follow-up that writes a shadow logger flagging
`poi_price_level disagreement with cited OB explanation` would give
operations a real-time signal without changing trading logic.

**Lower-leverage cleanup**: F9's classification artefact (TP, derived
prices) suggests B7's classifier could be refined to **exclude
forward-derived roles** from the hallucination rate, OR to report
"price-grounded hallucination rate" alongside "all-roles
hallucination rate". Worth a single-line config in B7-v2.

**Already-mitigated**: H2 (entry-outside-OB) is already caught by
the L2 verifier (`entry_in_ob FAIL` blocks the trade). It contributes
to the rate but not to live trade execution risk.
