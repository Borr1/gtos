# T1 pool screens — R-CAPS cells, R-GEOMETRY cells, and the fill axis (Phase D item 1)

Session FA continuation. Population: the January diagnostic pool
(`phase16/receipts/pools/CJ_RECLOCKED_S0R0_POOL_V1.jsonl.gz`, 27,658 rows) joined 1:1 to
the CK/CQ ordered-path sidecar (`phase18/receipts/pools/CQ_TRUE_UTC_S0R0_ORDERED_PATH_
SIDECAR_V1.jsonl.gz`, M1_CONSERVATIVE paths, no selection feedback). Costs: truthed
spread via `spread_model` (band=mid, v2_damped, hour-aware — the same substrate as
R-COST-TRUTH's `spread_input_truth`), frozen per-row commission/swap, flat 0.02 slippage;
price-anchored components rescale by each cell's own risk distance. Walker: CQ semantics
(running maxima from entry, conservative stop-first on ties, MTM clamped to [−1, target]
at the 120-minute wall — C7's symmetric censoring applies to every cell equally).
Machine artifact: `T1_SCREENS_V1.json` beside this file. Scripts committed as
`t1_screens.py`, `t1_fill_axis.py`.

**EVIDENCE CLASS: DEVELOPMENT-FITTED lane evidence, billed:false, never admission-grade.**
No March, no live-forward. Family-level readings are 10-way descriptive splits, not
declared multiplicity cells.

## Calibration first: what the frozen proxy is

The base cell (plain barrier, stop ×1, policy 2R target, wall MTM) reproduces the pool's
own `opportunity_net_proxy_r + cost_r` **bit-exactly on 22,000 / 27,658 rows (79.5 %)**.
The frozen proxy IS the plain-barrier contract on those rows. The 5,261 disagreeing rows
(mean signed gap **+0.258** in the fill-free walk's favor) are the fill model: the frozen
proxy is fill-aware (limit lifecycle), the sidecar walk enters at decision
unconditionally. That gap is not noise — it is the measurement of the entry contract,
and it concentrates in two families (below).

## Screen A — R-CAPS cell table (walker-independent: frozen walked gross − truthed cost)

| cap on truthed cost_r | admitted | share | winners (precision) | mean net_true | sum |
|---|---:|---:|---:|---:|---:|
| 0.05 | 2,096 | 7.6 % | 835 (39.8 %) | −0.127 | −267 |
| 0.10 | 7,693 | 27.8 % | 2,899 (37.7 %) | −0.183 | −1,409 |
| 0.15 | 12,643 | 45.7 % | 4,501 (35.6 %) | −0.248 | −3,134 |
| 0.25 | 19,955 | 72.2 % | 6,566 (32.9 %) | −0.332 | −6,622 |
| 0.50 | 25,167 | 91.0 % | 7,926 (31.5 %) | −0.386 | −9,720 |
| 1.00 | 27,090 | 98.0 % | 8,370 (30.9 %) | −0.424 | −11,482 |

Pool at truthed costs: mean −0.458 (frozen −0.881 — cost truthing halves the negativity),
win rate 30.6 %. **No cap value produces a positive admitted set.** Tightening enriches
precision mildly (30.8 → 39.8 % at the extreme) and always keeps the mean negative.

**R-CAPS verdict: the cap is a loss-reduction dial, not an edge source — cap
re-derivation alone cannot flip this pool's sign at any value.** (C2-B compliant: every
number above is grounded in tick-truth spread + frozen broker commission/swap only; the
gate's own estimates appear nowhere.)

## Screen B — R-GEOMETRY exit-shape cells (fill-free contract, truthed costs)

Pool-wide (n 27,658 each): base −0.199; stop ×1.5 −0.179, ×2 −0.166, ×3 −0.149;
target 1.5R −0.205, 3R −0.236, 5R −0.295. Same-bar ambiguity ≤ 10 rows in every cell.

Wider stops improve monotonically but never approach zero; the 2R target is locally
optimal among {1.5, 2, 3, 5} (both directions worse — the driftless-barrier picture of
C1-B, where target moves cost win-rate faster than payoff). **Exit-shape deltas are
±0.05 R — an order of magnitude smaller than the fill-axis gap below. No stop/target
cell on the current pool yields a positive book.**

## The fill axis — where the missing money actually sits

Per-family mean gap (fill-free − frozen fill-aware), with disagreement share:

| family | n | mean gap | rows disagreeing |
|---|---:|---:|---:|
| current_fvg_fill | 7,146 | **+0.754** | 39.2 % |
| current_ob_retest | 1,340 | **+0.635** | 36.4 % |
| current_breaker_re_entry | 4,263 | +0.105 | 6.1 % |
| structural_distance_extreme | 1,993 | +0.102 | 14.5 % |
| all six others | 12,916 | +0.02 avg | 7–12 % |

Three entry contracts on the same paths, truthed costs:

1. **Fill-free ceiling** (enter at decision, always): `current_fvg_fill` **+0.426**,
   `current_ob_retest` **+0.369** mean — positive in EVERY geometry cell (13 positive
   family×cell combinations, all in these two families).
2. **Fill-aware passive limit** (the frozen book): negative everywhere —
   BELIEF_RECAL's 0/108 no-honest-sub-book on this same pool.
3. **Marketable entry at decision** (first-bar open, same stop/target prices, full
   spread paid): fvg **−0.397**, ob **−0.402**; pool −0.384 on 21,652 valid rows
   (6,006 skipped: decision price already beyond stop/target).

**Reading: the retrace families' apparent edge lives at an uncapturable ceiling.**
Passive limits systematically miss the winners (price runs to target without
retracing); chasing at market pays the entire geometric premium away (risk distance
inflates, R multiple collapses, full spread). The delta between contracts is ~10× any
exit-geometry lever. This also makes the engine's constant
`execution_fill_probability = 0.92` (B4's one-constant template,
`poi_execution_lifecycle.py:176-178`) economically load-bearing and wrong in the
harmful direction on exactly these families.

One logged curiosity, not a thread: `current_breaker_re_entry` at market entry is
**+0.281 on its 656 geometrically-valid rows** (85 % skip) while being the worst family
at the fill-free contract (−0.976, 9.4 % win) — directionally consistent with CQ's
already-billed inverted-breaker candidate (V27); owned there, not here.

## Consequences in force

- **R-CAPS**: declared-method cells delivered above; the repair class is loss-reduction
  only. Any T2 arm citing a cap change must not claim edge from it.
- **R-GEOMETRY**: the exit-shape family is measured EMPTY on this pool (every cell
  negative, deltas second-order). The FB-grid-class contract lever that matters is the
  **entry/fill contract**, and both simple variants are negative — what remains for
  arm (v) is mechanism × geometry candidates (V27 class), not pool-wide contract repair.
- **Feb sidecar BUILD-vs-SKIP: SKIP.** (1) No repair cell derives from it; (2) February's
  used-once VAL budget is already partially spent (wave-18 first read + BELIEF_RECAL
  transfer); (3) the fill-axis result is a ceiling/attribution finding, not a candidate
  needing VAL. Preserving February's remaining evidential value outranks a redundant
  screen. Recorded here as the Phase D decision of record.
