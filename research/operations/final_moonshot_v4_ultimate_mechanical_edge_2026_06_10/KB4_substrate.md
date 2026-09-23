# KB4 — Conditional-outcome MAP engine (the core substrate)

Track key: **SUBSTRATE**. Layer goal: build the FOUNDATION that strategies are
queried from — a leak-free state vocabulary + a queryable map of barrier-touch
odds `P(reach +xR before -yR | state)`, with TRAIN(<=2024) vs FORWARD(2025-26)
holdout, per-year, and per-regime breakdown for every cell. This is a substrate,
not a strategy.

## Deliverables (all in this route dir)
- `substrate.py` — reusable, importable engine.
  - `build_states(sym)` -> leak-free StateVec per bar (features index<=i only).
  - `build_all_rows(symbols)` -> 3.06M state+outcome rows across 46 instruments.
  - `mine(rows)` -> the multi-depth confluence cell map.
  - `top_edges(cmap)` -> forward-validated +EV cells.
  - `query_cell(cmap, state, geom, dir, dims)` and `best_cell(...)` — the
    consumer entrypoints a strategy uses live ("give me the deepest reliable
    cell I'm in right now").
- `SUBSTRATE_MAP.json` — the full queryable map (19,788 cells, multi-depth).
- `SUBSTRATE_TOP_EDGES.json` — 219 forward-validated cells, ranked, with full
  per-year + per-class breakdown.
- `test_substrate.py` — 8 tests, incl. the **leak-free guarantee** (state at bar
  i computed on `bars[:i+1]` is byte-identical to state at i on the full series).

## Method (discipline)
- **No lookahead.** Every feature uses only closed bars index<=i. Entry = close[i];
  the outcome window is i+1.., so the feature bar never overlaps the label.
- **Trusted labeler.** Outcomes use `geometry_lib.simulate_detail` (pessimistic
  same-bar: stop wins ties). R-unit = stop_dist = stop_atr * ATR(i). Cost =
  `w1.cost_for(sym)` scaled by 1/stop_atr (tighter stop pays relatively more spread).
- **State vocabulary** (all leak-free): vol regime `vr=ATR/SMA100`, vol percentile,
  trend slope (20/50/100, ATR-normalised), `htf_trend`, multi-TF alignment
  (H4 short-20 vs long-100), range position (50-bar), compression (5-bar TR /
  20-bar TR), persistence `ac60`, distance-to-prior-extremes (ATR), session, dow.
- **Confluence by design.** Cells are mined at MULTIPLE depths (depth-0 baseline up
  to depth-7 full stack) over a small grid of geometries
  `(stop_atr, target_R) in {(1,1),(1,1.5),(1,2),(1,3),(0.75,2),(1.5,1)}` x dir
  {long, short}. High-odds cells come from STACKING independent conditions, and
  `best_cell()` returns the deepest cell that still has forward sample.
- **Forward holdout mandatory.** A cell is "forward-validated" only if
  `n_train>=40 AND n_fwd>=40 AND mean_R>=0.05 in BOTH train and forward AND a
  majority of train years AND a majority of forward years are +EV`.
- **No averages as verdicts.** The verdict metric is `mean_R` (the real,
  cost-bearing, pessimistic-fill tradeable outcome) — NOT a blended pool average.
  `odds` (clean P(+xR before -yR)) is reported alongside but is not the gate,
  because under a maxbars time-exit a cell can be tradeably +EV via favorable
  drift without a clean target touch.

## Scale
- 46 instruments (fx, jpy_fx, metals, energy, agri, index, crypto), H4 2014-2026.
- 3,062,328 leak-free state+outcome rows. 19,788 populated cells.
- 219 cells clear the forward-validation bar.

## Population-level finding (important, honest)
At the **whole-population** level there is essentially **no robust mechanical
barrier edge**: of 10,476 cells with n>=40 on both sides, only 586 are +EV in both
train and forward, and the unconditional baseline (depth-0) is ~0. Edge lives in
**conditional confluence cells**, exactly as doctrine predicts (a losing average
hides high-odds cells). This is why averages-as-verdicts is banned.

## TOP forward-validated high-odds cells (n>=40 both sides, holds forward)

Ranked by robustness = min(train, fwd) mean_R. `[L]`=long `[S]`=short. Tyr/Fyr =
positive-EV years out of available.

| cell (confluence) | dir | tgtR | oddsT | oddsF | Rtr | Rfw | nT | nF | Tyr | Fyr |
|---|---|---|---|---|---|---|---|---|---|---|
| vol=xhi, persist=rand, trend=up, mtf=conflict | L | 3.0 | 0.10 | 0.30 | **+1.04** | **+0.71** | 69 | 74 | 7/8 | 2/2 |
| vol=lo, trend=up, mtf=conflict, rngpos=mid, comp=norm, persist=trend, london | S | 3.0 | 0.09 | 0.14 | +0.52 | +0.41 | 109 | 83 | 8/10 | 1/2 |
| vol=hi, trend=flat, mtf=aligned, rngpos=mid, comp=norm, persist=revert, asia | S | 3.0 | 0.05 | 0.06 | +0.35 | +0.36 | 58 | 47 | 7/8 | 2/2 |
| vol=xhi, persist=rand, trend=up, mtf=conflict | L | 2.0 | 0.14 | 0.32 | +0.60 | +0.35 | 69 | 74 | 6/8 | 2/2 |
| vol=lo, trend=up, mtf=aligned, rngpos=mid, comp=coil, persist=rand, london | L | 3.0 | 0.02 | 0.02 | +0.31 | +0.52 | 54 | 45 | 5/9 | 2/2 |
| vol=xhi, persist=rand, trend=up, mtf=neutral | L | 3.0 | 0.09 | 0.15 | +0.53 | +0.30 | 81 | 67 | 6/9 | 2/2 |
| vol=lo, trend=up, mtf=neutral, rngpos=high, comp=norm, persist=trend, london | L | 1.0 | 0.23 | 0.45 | +0.28 | +0.44 | 73 | 40 | 7/9 | 2/2 |
| vol=hi, trend=up, mtf=conflict, rngpos=mid, comp=expand, persist=rand, asia | L | 1.0 | **0.47** | **0.50** | +0.35 | +0.15 | 51 | 42 | 8/9 | 2/2 |

(Full ranked list of 219 in `SUBSTRATE_TOP_EDGES.json`.)

### The headline edge — "deep pullback in an extreme-vol uptrend"
`vol=xhi & trend=up & mtf=conflict & persist=rand`, go **LONG**:
- The single most robust cell. TRAIN +1.04R (n=69, 7/8 years +EV),
  FORWARD +0.71R (n=74, both 2025 & 2026 +EV). ~37 trades/yr forward, pooled.
- Holds across the SAME geometry family (1R/1.5R/2R/3R all +EV) — internal
  geometry confluence, not a single tuned target.
- **Forward positive in EVERY major class**: index +1.38, energy +1.30,
  metals +1.27, fx +0.84, crypto +0.43, jpy_fx +0.22. Cross-asset = not one
  symbol's luck.
- Reading: in a strong up-regime with elevated ATR, when the short horizon
  disagrees with the long (i.e. a pullback) and persistence is neutral, buying
  the dip with a wide target pays. Coherent, mechanical, broad.

### Highest clean-ODDS cell (for tight-target use)
`vol=hi & trend=up & mtf=conflict & rngpos=mid & comp=expand & persist=rand & asia`,
LONG 1R: clean hit-odds **0.47 train / 0.50 forward**, +EV in 8/9 train and 2/2
forward years. A genuine ~50% 1R edge for a tight-geometry sleeve (n thin, 51/42 —
treat as confluence pocket, not a high-frequency stream).

## How strategies consume this
```python
import substrate as sub, json
cmap = json.load(open("SUBSTRATE_MAP.json"))["cells"]
state = sub.build_states(sym)[3][i]          # leak-free StateVec at bar i
dims, cell = sub.best_cell(cmap, state, geom=(1.0,3.0), dmode=+1)  # deepest reliable cell
if cell and cell["fwd"]["mean_R"] > 0:        # the state says +EV forward -> take it
    ...
```
`best_cell` returns the DEEPEST confluence cell with forward sample, falling back
shallower automatically — so a strategy always gets the most specific reliable
read of "what state am I in and does it pay".

## Caveats / honesty
- Many top cells have low clean `odds` but +EV `mean_R`: the edge is partly
  favorable drift captured at the time-exit, not only clean target touches. The
  map reports both so a consumer can pick target geometry accordingly.
- Forward windows are short (2025 + partial 2026); cells with `Fyr 1/2` are
  weaker (single forward year carries them) and are ranked below `2/2` cells.
- Thin-n cells (n~40-50) are confluence POCKETS, not high-frequency streams; the
  brief's `n>=40` floor is enforced, never presented as a 90% edge.
- Regenerate everything with `python3 substrate.py` (~90s); `--quick` subsamples.

## Cross-check vs existing book
The headline cell echoes the campaign's validated commodity/crypto continuation +
energy-regime findings (PORTFOLIO_BUILD_W2 / KB2) from a fully independent,
state-conditional angle — the substrate rediscovers "buy strong-trend pullbacks
in elevated vol" mechanically and shows it generalizes beyond commodities to
indices/fx. The substrate is the generalization layer under those sleeves.
