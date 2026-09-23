# KB4 — Confluence scorer LAYER (track: confluence)

Builder pass 2026-06-15. **Layer, not a strategy.** Build a reusable engine that stacks
INDEPENDENT condition-families into a confluence score and quantifies how co-occurring
conditions COMPOUND forward odds. Doctrine enforced in code: no lookahead (every condition is
a pure function of CLOSED bars `index<=i`); outcomes labeled ONLY by `geometry_lib.simulate`
(leak-free pessimistic same-bar-stop); real per-asset cost via `w1.cost_for`; **no averages as
verdicts** — every cell reports TRAIN(<=2024) vs FORWARD(2025-26) + per-YEAR + n; a cell is
trusted only if it holds forward AND has n>=40 AND survives a label-permutation null.

Engine: `confluence.py` (importable). Result map: `KB4_CONFLUENCE_RESULT.json`.

## What the engine does

- **7 independent condition-families**, each `(ctx,i,direction) -> bool` ("does this family AGREE
  with the trade direction here, using only data<=i?"):
  `persistence` (ac60>=0.10), `vol_expand` (ATR/SMA100(ATR)>=1.2), `trend_align` (30-bar slope vs
  ATR agrees with d), `range_pos` (long in lower-40% / short in upper-40% of trailing 50-bar range),
  `struct_prox` (close within 0.5*ATR of the favour-direction prior-day extreme),
  `liq_sweep` (bar swept the prior-day extreme and reclaimed, in d), `vol_loc` (bar volume >=1.2x
  100-bar mean; never fires on no-volume symbols so it can't falsely lift).
- **Two probes** (where to look): `fvg` (audited vol-gated FVG-retest continuation across the whole
  universe) and `sweep` (prior-day sweep+reclaim, a wide net). Both use a **fixed 2R target** so the
  confluence layer — not the exit — drives the odds.
- For each candidate it records the full condition VECTOR + the leak-free outcome, then the analyzer
  produces, per asset-class view: (1) **pairwise phi-correlation** of the condition booleans
  (independence check), (2) **marginal odds-lift** per condition, (3) **confluence-COUNT sweep**
  (>=k conditions agree), (4) the **top confluent COMBOS** (n-gated, ranked by FWD win%), and (5) for
  the best stack the **per-year / per-class** odds and the **incremental odds-lift of each added
  condition** (ablation within the stack).

## INDEPENDENCE (the prerequisite for confluence to multiply)

Confluence only compounds if conditions are independent. Measured phi over the full candidate sets:

- Most pairs are near-zero phi (|phi|<0.15) — the families are genuinely distinct signals.
- Built-in dependencies, correctly surfaced and handled, NOT double-counted:
  - On the **fvg probe**, `vol_expand` and `trend_align` fire **100%** (the probe already requires the
    vol-gate and an HTF trend). On the fvg probe they contribute **zero** independent lift — the only
    free conditions there are `persistence`, `vol_loc`, `range_pos`, `struct_prox`, `liq_sweep`.
  - `struct_prox ~ liq_sweep` phi≈+0.60 (a sweep happens near the level) — overlapping, kept but flagged.
  - `trend_align ~ range_pos` phi≈-0.62 on sweep probes (trend-up entries are rarely in the lower range)
    — these two are a near-orthogonal AXIS PAIR: stacking trend with location is real confluence.
  - `vol_expand ~ vol_loc` phi≈+0.37 on crypto (ATR expansion co-occurs with volume) — mild overlap.

## DECISIVE forward-AND-train-holding confluence cell

**metals-FVG + persistence (ac60>=0.10):**
`FWD 55.4% win, +0.638R, n=65` vs base `41.4% / +0.205R` — a **+14.0pt / +0.43R** lift, and it HOLDS in
TRAIN (`52.4% / +0.491R, n=82`). **Positive R in 10 of 12 years**; both forward years strong (2025
+0.711R n33, 2026 +0.564R n32). **Label-permutation null: p=0.001** (2000 shuffles — the lift is not
noise). This independently REPRODUCES the compounding-sleeve ac60 gate from a different engine, which is
strong cross-validation. Note `vol_expand`/`trend_align` are already in the FVG probe, so the *added*
condition doing the work is **persistence** — confluence here = (FVG-retest ∧ vol-expansion ∧ trend) ∧
persistence, i.e. four conditions, three baked into the probe and the 4th (persistence) supplying the lift.

**Refinement (honest, thinner):** persistence ∧ **NOT** `vol_loc` is *stronger* forward (2025 +0.72R n17,
2026 +0.95R n18). `vol_loc` is a **negative** confluence condition on metals FVG: persistence∧vol_loc
drops to FWD 46.7% (n30) while persistence∧¬vol_loc is 62.9% (n35, +0.84R). **Key layer lesson: more
conditions is NOT always better — a condition can be ANTI-confluent; the engine must measure sign, not
assume monotonic stacking.**

## Confluence-COUNT compounding (metals FVG, fixed 2R)

Requiring more agreeing conditions monotonically lifts odds where the conditions are real:
`>=3: FWD 42.5%/+0.244R (n200)`, `>=4: FWD 52.5%/+0.566R (n40)`. The >=4 cell (n40, gate-passing)
is the count-based view of the same persistence-driven edge.

## Cells that LOOK strong forward but FAIL the discipline (reported so they are not mis-sized)

- **energy-FVG + vol_loc**: FWD 46.3% / +0.333R (n136) looks great, but it is a **single forward-year
  artifact** — per-year: 2021 25%, 2022 31%, 2023 16%, 2024 25% (all TRAIN-negative), 2025 35.6%,
  **2026 67.4% / +0.917R (n46)**. The forward strength is essentially all 2026. NOT a robust confluence
  edge; this matches KB2's finding that energy converts only via the regime/vol gate, not via volume.
- **sweep-probe combos** (energy persist+trend FWD 41.4% perm-p=0.034; fx/index/crypto stacks ~40-44%
  FWD win): the sweep probe base rate is ~33% at 2R and **every class is TRAIN-negative** at base. The
  confluence stacks lift FWD win 7-11pt and several reach +R forward, but with TRAIN-negative bases and
  modest perm-significance these are **breadth-only / small-size**, not deployable primaries. They do
  confirm the AXIS finding: `trend_align`+`range_pos`+`vol_loc` (the orthogonal stack) is where the lift
  concentrates on the wide sweep net.

## Odds-lift contributed by each added condition (the layer's deliverable)

Incremental FWD win% as conditions are stacked (best stacks):
- metals FVG: base 41.4% → +persistence **55.4%** (n65). Persistence is the entire lift; vol_loc removes it.
- index sweep: base 33.1% → +persistence 33.9% → +trend_align 39.0% → +struct_prox 41.4% → +vol_loc 44.4%
  (n45) — a clean monotone confluence ladder, but TRAIN-negative so small-size only.
- crypto sweep: base 34.5% → +persistence 34.9% → +vol_expand 36.2% → +range_pos 41.1% → +struct_prox
  44.7% (n47) — driven by 2025; 2026 thin/adverse.

## Verdict for the substrate

1. **The confluence engine is real and reusable** (`confluence.py`): independence-checked, n-gated,
   forward-holdout, per-year, permutation-tested, importable. It is a queryable LAYER, not a strategy.
2. **One confluence cell clears the full discipline bar**: metals-FVG ∧ persistence — forward AND train
   positive, 10/12 positive years, perm-p=0.001. It cross-validates the existing metals sleeve from an
   independent code path (high confidence it is not a harness artifact).
3. **No cell reaches a *raw* 70%+ win-rate at a fixed 2R** — that target makes 70% win arithmetically
   hard. The honest high-odds story is **EV/R lift** (metals persistence +0.43R over base, ~55% win at
   2R ≈ strongly positive expectancy), not a 70% win flag. Presenting any thin cell (e.g. energy-vol_loc
   2026) as a 70% edge would be exactly the averaging/regime-luck trap the doctrine forbids.
4. **Layer lesson for downstream waves**: confluence must be measured with SIGN and per-year stability,
   not assumed monotonic — `vol_loc` is anti-confluent on metals FVG; energy-vol_loc is a one-year mirage.
   The orthogonal axis pair (`trend_align` ⟂ `range_pos`) is the most fertile place to stack independent
   conditions on wide nets.

## Files
- `confluence.py` — the engine (CONDITIONS registry, PROBES, build_dataset, analyze, run).
- `KB4_CONFLUENCE_RESULT.json` — full map: per-view base, fire-rate, pairwise phi, marginal lift,
  count sweep, top combos, best-stack per-year/per-class/incremental.
