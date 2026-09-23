# R1 CM-cell pricing — `crypto @ stop_1p5x_target_scale` on the corrected quote convention

**Receipt:** `R1_CM_CELL_PRICING_V1.json` (script `r1_cm_cell_pricing.py`, wave 21,
branch `wave21/cm-cell-pricing`, base `2edefd48a`).
**Why:** CM was armed 2026-08-06 and **rolled back 2026-08-10 on the owner's word** (host
`4d28676f8`, B3413). Re-arming is gated on pricing the exact CM cell on the corrected-quote
walker. The wave-20 surface (`R1_FRONTIER_SURFACE_V1.json`) holds the stop width at 1.0x in
all 210 crypto cells, so the CM geometry was in none of them — this receipt walks it over
the **same 181-trade population, same chronological-fifth folds, same three spread bands,
same walker** as the surface.

## The cell, extracted from the wiring (cites at `2edefd48a`)

| parameter | value | source |
|---|---|---|
| stop width | 1.5 x native `sl_distance_price` (= −1R of the scaled unit) | `execution_packets.py:213-217` (override), `:530-535` (`risk_distance = base * multiplier`), `:564-568` (broker SL rebuilt from it) |
| target | 4.0R of the scaled unit = **6.0x native distance** | `:80` (committed `final_target_r=4.0`), `:413-419` (merge), `:569` (TP = entry ± 4.0 × scaled risk) |
| horizon | 1280 M15 bars = 80 own H4 bars (walker `maxbars=80`; same bar, same close) | `:80`, `:184-186` |
| trail / partial | none (`policy="time_stop"`) | `:80` |
| research cell | AD's `stop_1.5x_tgtscale` (stop = sl×k, target scales with stop, R in scaled unit) | `ad_exit_sweep.py:318,324,338,357`, declared `:501-507` |

Equivalence of the live fixed-4R construction and AD's scales-with-stop construction requires
`target_dist == 4 x sl_distance_price` per row — **holds bit-for-bit on all 181 rows** (C1),
and the two routes replay to **identical winsorized R on all 362 walks** (C3). The three
stop-width-1.0 comparison cells **reproduce the committed surface record exactly, 18/18**
(C2) — proving same population, same folds, same bands, same walker after the `stop_mult`
extension (default-inert; behavioural tests in
`tests/research_infra/test_r1_cm_cell_walker.py`).

## Numbers (R/day; each contract's R is its own risk unit — live sizing puts the same cash on 1R of either contract, so R/day is directly comparable)

**Corrected convention (the gate's convention):**

| band | CM cell | shipped 4R | CM − shipped | paired trade Δ (mean ± SE) | paired folds improved | latest fold Δ | surface best (cell) | CM − best |
|---|---|---|---|---|---|---|---|---|
| low | 0.6113 | 0.7400 | **−0.1286** | −0.093 ± 0.106 | 2/5 | −0.327 | 0.8794 (`target_5.0R\|maxbars_160`) | −0.2681 |
| mid | 0.6046 | 0.5995 | **+0.0051** | +0.004 ± 0.117 | 2/5 | −0.063 | 0.7196 (`target_4.0R\|maxbars_160`) | −0.1150 |
| high | 0.6029 | 0.5870 | **+0.0160** | +0.012 ± 0.117 | 2/5 | −0.064 | 0.6814 (`target_4.0R\|maxbars_160`) | −0.0784 |

CM cell r/trade (corrected): 0.4425 / 0.4376 / 0.4364 (low/mid/high), n=181, own folds
**5/5 positive at every band** (it lifts the flat third fold to +0.056 where shipped is
−0.052 — the one metric that favours it).

**Published convention (reference):** CM 0.6835 vs shipped 0.7839 at every band
(−0.1004 R/day; paired −0.073 ± 0.111). The corrected convention *narrows* the gap at
mid/high because the 1.5x stop dilutes spread-over-risk — the correction costs the CM cell
−0.079 R/day at mid where it costs the shipped cell −0.184. That relative cushion is the
only sense in which the corrected tape favours CM.

**Truncation (AR's maxbars-share standard):** the CM cell ends **~40 %** of trades at the
80-bar horizon (0.398–0.409 across bands) versus ~20 % for shipped and ~9–15 % for the
160-bar cells. Two-fifths of its outcome is horizon closes, not resolved geometry.

## Characterisation (evidence only — the decision is Borhen's)

1. **The corrected evidence does not reproduce the basis CM was armed on.** Session CM's
   lane (true-UTC TRAIN/VAL through the production generator) showed +0.2527 R/day at mid
   with 4/5 paired folds improving and the latest fold +0.0355 better
   (`execution_packets.py:206-212`). On the corrected estate walker over the surface
   population, the same geometry is **+0.005 R/day at mid (paired |t| ≈ 0.03), −0.129 at
   low, 2/5 paired folds, and the latest fold is worse at every band.** The two substrates
   disagree; this receipt does not adjudicate which population governs — but the rollback
   gate named this walker, and on this walker the cell's edge over shipped is
   indistinguishable from zero where it exists at all.
2. **Keeping shipped 4R loses nothing measurable here.** The largest CM advantage anywhere
   is +0.016 R/day (high band) against a paired SE of 0.117; the low band flips the sign at
   −0.129. Nothing in this receipt argues the rollback left money on the table.
3. **Both are dominated by the surface best cells at every band** (`target_4.0R|maxbars_160`
   mid/high, `target_5.0R|maxbars_160` low; +0.08 to +0.27 R/day over CM, +0.08 to +0.14
   over shipped). The lever this population points at is the **horizon** (80 → 160 own
   bars), not the stop width. Caveats before anyone acts on that: the argmax was selected
   on this same population (in-sample argmax, wave-20 receipt), a horizon change doubles
   holding time and therefore carry exposure (unpriced here — this walker is gross-of-swap),
   and no admission standard has been applied to any of these cells in this receipt.
4. Scope: 181 trades / 131 decision days, BTCUSD 146 + DASHUSD 35, 2017-02-24..2026-06-03,
   AA's estate labelling, FTMO bars, winsor [−1.3, +5.0], no swap/commission. No new grid
   was opened: the CM cell was declared by AD's `stop_width` family and selected by Session
   CM; the other three cells are re-reads of committed surface cells.
