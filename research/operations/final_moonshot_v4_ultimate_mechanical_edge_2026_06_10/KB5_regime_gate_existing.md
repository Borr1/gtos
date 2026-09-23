# KB5 — Regime-gate / size the EXISTING book by the substrate

Track key: **REGIME-GATE-EXISTING**. Goal (brief): compose `substrate.best_cell` /
`regime_map.regime_at` as a confluence GATE + sizer on the EXISTING validated CORE
sleeves (`metals_core`, `crypto`, `energy_agri`). Take a sleeve trade only when the
live state's deepest forward-validated substrate cell is +EV, and size by
`min(train,fwd) mean_R`. Measure whether this lifts the existing book forward EV /
stress P(pass) vs ungated, forward per-year. Keep if it lifts, **learning if not.**

## VERDICT (honest): LEARNING — the substrate gate does NOT lift the existing book.

At MATCHED gross exposure (the only fair book-level test for a selectivity overlay),
the substrate regime-gate **lowers** EV-per-unit-risk and stress P(pass) on the
already-optimized CORE book. The book's native per-sleeve edges (FVG∧persistence,
Donchian∧persistence, FVG∧vr + STATE_D/cascade exits) already encode regime more
precisely than the generic 7-dim substrate vocabulary read at a fixed geometry, so
the gate mostly removes GOOD trades. **Keep the ungated CORE book; do NOT gate it.**
(The substrate's proven, additive role is as a NEW low-corr breadth sleeve —
`SUBSTRATE_BUILD.md` Sleeve A/B/C/D — not as a gate on the existing core.)

---

## Method (leak-free, faithful to the validated book)

- **Gate at the EXACT entry, not a date approximation.** Each CORE sleeve's entry
  `(bar i, direction d)` is re-derived by re-running its own signal logic verbatim
  (metals/energy via `gold_sleeve_strategy.fvg_signals`; crypto BTC/DASH via
  `kb2_new_breadth.crypto_breakout_signals`; ETH on its resampled H4 series). Entry
  bars reproduce the W3 cache keys **exactly** (metals 86/86, crypto BTC/DASH 50/50,
  ETH 25/25, energy 84/84). The gate is then attached to the **ACTUAL W3 cache rows**
  (`INTEG_W3_streams_cache.pkl`), so the validated exit R is preserved — the gate
  changes ONLY take/skip + size, never a taken trade's R.
- **Leak-free state.** Substrate state at bar `i` is computed on `bars[:i+1]`
  (`substrate.build_states`, byte-identical leak guarantee). Book trade enters at
  `close[i]`, outcome window `i+1..` — feature bar never overlaps the label.
- **Gate query.** `substrate.best_cell(cmap, state_i, geom=(1.0,3.0), dmode=d)` — the
  deepest forward-validated cell for this state in the trade's direction.
- **Two gate variants** (forward honesty):
  - `minboth` — take if `min(train_meanR, fwd_meanR) > 0`; size by that min (the
    brief's literal rule). NOTE: reading the cell's *forward* mean uses the forward
    outcomes of OTHER trades in that cell — mild forward contamination of the gate.
  - `trainonly` — **forward-honest**: take/size by the deepest train-validated cell's
    `train_meanR` only (no forward information in the gate decision at all). This is
    the variant to trust for a forward claim.
- **Matched-exposure MC.** Reuses the LOCKED W2 engine verbatim
  (`INTEG_portfolio_build_w2.{build_matrix, mc_series, joint_pass_mc}`; seeds 1/777/999,
  8%/5%/10% FTMO, block=5, 20k paths). A frequency-cutting overlay starves the
  bootstrap path and crushes raw MC, so every variant's combined series is rescaled
  so total deployed GROSS risk equals the ungated book's — then MC is apples-to-apples.

Files: `RGATE_substrate_gate.py` (gate engine + entry-bar re-derivation + ETH state),
`RGATE_run.py` (raw gated-vs-ungated + MC), `RGATE_matched.py` (matched-exposure book
test + metals/energy-only variant), `RGATE_RESULT.json`, `RGATE_MATCHED_RESULT.json`.

---

## 1. Per-trade EV — the gate DOES select higher-mean trades for metals+energy…

Raw per-trade R (unsized), gateable subset (CORN/COTTON agri excluded — different
entry mechanic, passed through ungated):

| sleeve | variant | n_fwd | EV_fwd | n_train | EV_train | n_all | EV_all |
|---|---|---|---|---|---|---|---|
| metals_core | UNGATED | 49 | **+1.235** | 82 | +0.679 | 131 | +0.887 |
| | gate trainonly | 31 | +1.518 | 39 | +0.756 | 70 | +1.093 |
| | gate minboth | 3 | +2.722 | 4 | +0.739 | 7 | +1.589 |
| crypto | UNGATED | 83 | **+0.950** | 21 | +1.775 | 104 | +1.117 |
| | gate trainonly | 39 | +0.901 | 5 | +0.905 | 44 | +0.901 |
| | gate minboth | 16 | +0.507 | 3 | +2.238 | 19 | +0.780 |
| energy_agri | UNGATED | 53 | **+0.923** | 31 | +0.407 | 84 | +0.733 |
| | gate trainonly | 25 | +1.097 | 10 | +0.258 | 35 | +0.858 |
| | gate minboth | 11 | +1.104 | 5 | +0.279 | 16 | +0.846 |

- **metals + energy**: the gate raises forward mean-R-per-trade (metals +1.235→+1.518,
  energy +0.923→+1.097) — a real per-trade selection lift, **but at ~40–55% of the
  frequency.**
- **crypto**: the gate HURTS (forward +0.95→+0.90, n83→39). Crypto's own
  Donchian∧persistence edge already encodes the regime; the generic 3R-substrate gate
  just thins it.
- **Robustness — not a geometry artifact.** Re-querying the gate at the BEST geometry
  across the whole `GEOMS` grid (not fixed 3R), train-only honest: metals
  +1.235→+1.108, crypto +0.95→+0.996, energy +0.923→+0.903 — still no forward lift,
  reduced n. The negative result holds across the geometry family.

## 2. …but at the BOOK level (matched exposure) the gate LOSES.

`RGATE_MATCHED_RESULT.json`. Ungated CORE gross = 466.6 unit-R; each gated variant is
rescaled to that same gross (matched-exposure scale `mScale`). MC at 0.75%/unit:

| variant | gross | mScale | EV / gross | P(pass) ALL | P(pass) FWD | **STRESS 1.5x** | med_days |
|---|---|---|---|---|---|---|---|
| **ungated (existing)** | 466.6 | 1.00 | **+0.2721** | 99.98% | 100.0% | **89.0%** | 132 |
| gate_me_trainonly (M+E gated, crypto ungated) | 369.9 | 1.26 | +0.2044 | 99.50% | 99.8% | 61.1% | 172 |
| gate_all_trainonly | 269.9 | 1.73 | +0.1044 | 99.26% | 100.0% | 11.9% | 302 |
| gate_me_minboth | 355.2 | 1.31 | +0.1815 | 98.28% | 99.4% | 50.5% | 185 |
| gate_all_minboth | 241.6 | 1.93 | +0.0445 | 89.90% | 99.9% | 0.8% | 528 |

- **EV-per-unit-gross**: ungated +0.2721 is the BEST; every gated variant is lower.
  The gate removes more good-trade R than bad-trade R per unit of risk deployed.
- **Stress 1.5x P(pass) @0.75%**: ungated **89.0%** vs best gated 61.1% (gate_me_trainonly)
  — the gate makes adversarial survival materially WORSE.
- **Why**: gating cuts frequency ~50%, so to match gross the book must lever 1.26–1.93x,
  which concentrates the worst day (a thinner book = lumpier daily-R), and the
  diversification that carries the book's stress survival is partly removed with the
  trades. Forward base P(pass) stays ~100% (the book is base-saturated either way), but
  every honest stress and efficiency metric falls.

### Soft-sizer (never-skip; tilt size by substrate confidence) — also loses
A pure positive-EV sizer (keep ALL trades, size in [floor,cap] by train-only cell
`mean_R`, negatives at floor) at matched exposure: best soft config EV/gross +0.2446
vs ungated +0.2721; stress @0.75% 86.3% vs 89.0%; @1.0% 79.4% vs 82.8%. Even tilting
(not skipping) MIS-allocates size vs the book's native edge. **The substrate confidence
is not a better size signal than the book's own conf weights + STATE_D exit.**

## 3. Per-year forward (gate_me_trainonly, the least-bad gated variant)

Forward per-year mean-R survives positive (metals 2025/2026, energy 2025/2026 both +EV),
so the gate is not forward-broken — it is simply DOMINATED by ungated on every
book-level axis. Full per-year in `RGATE_RESULT.json` `per_sleeve.trainonly`.

---

## 4. Why this is the EXPECTED, doctrine-consistent result

1. **The CORE book is already the selection layer.** W2/W3 already mined these sleeves
   to train-validated edges with conf-weighted sizing and STATE_D/cascade exits. Layering
   a coarser generic gate on an already-optimized stream removes signal, not noise — the
   classic "per-sleeve positive ≠ book-level improvement once tail variance is priced"
   lesson (PORTFOLIO_BUILD_W3 §0, the IDB and miner-harvest ablations taught the same).
2. **The substrate's value is ORTHOGONALITY, not overlap.** `SUBSTRATE_BUILD.md` proved
   the substrate edges are ~0-correlated with the book and additive as NEW breadth sleeves
   (Sleeve A `sub_xvol_pullback` conf 0.45, etc.). Using it as a GATE forces it to
   OVERLAP the core (same symbols, same bars) — exactly where it has no edge over the
   sleeve's own mechanic. Independent layers MULTIPLY when ADDED, not when one filters
   the other.
3. **A 3R fixed-target regime read ≠ the book's exit.** The book exits via vol-tiered
   STATE_D scale-out / cascade, not fixed 1:3R. The substrate cell answers "is +3R likely
   before -1R in this state", which is a regime proxy, not the book's tradeable question
   — so its take/skip is misaligned with what the book actually harvests.

## 5. What WOULD be worth trying next (not this gate)

- **Gate the FALSIFIED breadth, not the validated core.** The conf-0.15 sleeves
  (`idxrev` ~1013/yr, `fx_jpy`, `fx_jpy_ny`) are honest-negative train edges carried as
  breadth. A substrate gate there could only help (they have no strong native edge to
  damage) — but those are index/FX, where the substrate's index/FX legs already exist
  as the recommended NEW sleeves, so folding them as ADDITIVE sleeves (SUBSTRATE_BUILD)
  dominates gating them.
- **Add, don't gate.** The directly-deployable use of the substrate is Sleeve A/B/C/D
  as additive low-corr breadth (already recommended), which RAISES the 2-account stress
  P(both) by deepening diversification — the opposite of what gating the core does.
- **Re-run the substrate under the deployed STATE_D exit** (SUBSTRATE_BUILD §7.3) so the
  cell answers the book's real exit question; a STATE_D-labeled substrate MIGHT become a
  useful sizer. Until then, gating on fixed-R cells is mis-specified.

---

## Reported gated-book numbers (the brief's ask), matched exposure, @0.75%/unit

| metric | ungated (KEEP) | best gated (gate_me_trainonly) |
|---|---|---|
| combined daily mean unit-R | +0.0794 | +0.0472 (pre-rescale) |
| EV / unit gross deployed | **+0.2721** | +0.2044 |
| P(pass) ALL | 99.98% | 99.50% |
| P(pass) FWD 25-26 | 100.0% | 99.80% |
| **STRESS 1.5x P(pass)** | **89.0%** | 61.1% |
| 2-acct balanced P(both) base / stress | 99.98% / 79.0% | (lower) |
| frequency (CORE gateable trades/yr fwd) | ~153/yr | ~70/yr |

**Decision: do NOT gate the existing CORE book by the substrate. Keep it ungated;
deploy the substrate as ADDITIVE breadth (Sleeve A/B/C/D) per SUBSTRATE_BUILD.md.**
Nothing deleted — the gate engine (`RGATE_*`) is preserved as the reusable
substrate-as-gate harness and the negative-result evidence.
