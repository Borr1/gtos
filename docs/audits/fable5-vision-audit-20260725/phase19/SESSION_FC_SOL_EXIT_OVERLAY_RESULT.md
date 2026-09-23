# Session FC — honest exit-overlay repair result

**Wave 19, blocks B3150–B3199. Branch `phase19/sol-exit`.**  This is a
research-only, default-off result.  It grants no promotion, activation, config,
VPS, broker, March-2026, or live-forward authority.

## Result first

No predeclared exit overlay passed the frozen persistence rule.  The family is
not abandoned: FC leaves a reusable default-off overlay/instrumentation layer
and defines the next bounded ex-ante family.  It does not implement or arm a
named candidate because none earned that authority.

The final January-TRAIN ranking selected the three tighter-giveback cells with
a 0.5R trigger:

| Frozen rank | Cell | Gap | Jan TRAIN net / improvement | TRAIN improvement q | Jan HOLDOUT net / improvement | February net / improvement | Executed null-clean | Persistence |
|---:|---|---:|---:|---:|---:|---:|---|---|
| 1 | `V17_GB_T050_G010` | 0.1R | +0.197 / +4.492 R | 0.4861 | -1.920 / -0.520 R | -0.381 / +2.799 R | yes | fail |
| 2 | `V18_GB_T050_G020` | 0.2R | -0.150 / +4.145 R | 0.4861 | -2.754 / -1.355 R | -0.893 / +2.286 R | yes | fail |
| 3 | `V19_GB_T050_G030` | 0.3R | -0.995 / +3.300 R | 0.4861 | -3.392 / -1.992 R | -1.289 / +1.891 R | yes | fail |

V17 is the only non-identity cell that makes the January TRAIN executed book
positive, and only by +0.197R over 30 trades.  It reverses on the frozen
27-trade HOLDOUT and remains below zero on the 58-trade February attribution
book.  V18 and V19 do not even make TRAIN positive.  All three beat the four
TRAIN null-control improvements, but null cleanliness cannot rescue failed
multiplicity, level, and holdout gates.

Across the complete 40-cell family:

- zero cells are positive on January TRAIN, January HOLDOUT, and February;
- zero cells make the combined 57-trade January executed book positive;
- 1 cell is TRAIN-positive, 5 different cells are HOLDOUT-positive, and 22
  cells are February-positive; those disjoint facts are not persistence;
- February was applied only after January froze the top three and had no
  ranking, threshold, family-expansion, or implementation authority.

Authority: `OVERLAY_RESULTS.json` contains all 40 cells, daily blocks, raw
one-sided sign-flip p values, BH-40 q values, concentration tests, and gates.

## Residual choice set and full pool

The 4,509-row January residual choice set is level-positive under many exit
rules, but no overlay establishes multiplicity-controlled incremental repair.
Thirty-five non-identity cells are positive in both splits.  None has both a
TRAIN level q <= 0.10 and a TRAIN improvement q <= 0.10; the best family-wide
improvement result is V23 at q = 0.1025390625.  The selected trio's residual
results are:

| Cell | TRAIN mean net / improvement | Level q / improvement q | HOLDOUT mean net / improvement | Residual null-clean |
|---|---:|---:|---:|---|
| V17 | +0.17919 / +0.03624 R | 0.06999 / 0.29297 | +0.14112 / +0.01941 R | no; shuffle 1902 is larger |
| V18 | +0.16368 / +0.02074 R | 0.06999 / 0.55745 | +0.13317 / +0.01146 R | no; all three shuffles are larger |
| V19 | +0.15550 / +0.01256 R | 0.06999 / 1.00000 | +0.13107 / +0.00937 R | no; all three shuffles are larger |

This answers the residual question narrowly: the residual book is positive in
level, but this overlay family does not make it persistently more positive
after multiplicity and null controls.

The full 27,658-row opportunity pool stays negative for all 40 cells in both
splits.  V17 improves the identity control but still totals -9,394.47R TRAIN
and -5,081.11R HOLDOUT.  The full pool intentionally includes cost-untradeable
rows and is diagnostic only; it cannot authorize or veto an executed overlay.

## Execution truth and identity control

FC evaluates exits only after a recorded fill.  Thirteen January trades and 24
February trades fill after their decision timestamp; their pre-fill prices are
not visible to the overlay.  The terminal horizon remains the frozen decision
time plus 120 minutes.

The authenticated lane's tick rows preserve raw broker-wall `time_msc` for
provenance while putting converted true UTC in `ts_utc` and `time`.  FC requires
the two textual fields to agree and never interprets `time_msc` as UTC.  Long
exits use bid; short exits use ask.  The final populations are:

- January executed: 40 ordered-tick and 17 conservative-M1 rows;
- February executed: 51 ordered-tick and 7 conservative-M1 rows;
- January pool: 4,985 ordered-tick and 22,673 conservative-M1 rows, with zero
  tick-pointer fallbacks after the clock repair;
- all 27,658 pool rows join one-to-one on candidate, decision time, symbol, and
  side; candidate ID alone is never used; guarded fallbacks and ambiguous or
  duplicate joins are both zero.

V00 reproduces all ordered-tick source outcomes: 40/40 January and 51/51
February rows are within 1e-6R.  Only the lower-of-two-orderings M1 diagnostic
differs: 6/15 comparable January M1 rows and 3/7 February M1 rows.  Aggregate
M1 gross deltas versus source are -0.07556R in January and +0.78167R in
February.  V00 is therefore an exact ordered-tick identity and a conservative
M1 comparator, never an M1 bid/ask or broker-ticket claim.

Partial cells harvest the declared fraction at the trigger, weight the
remainder, and then deduct 100% of source `cost_r` once.  M1 evaluates both
open-high-low-close and open-low-high-close orderings and retains the lower
economic result.  The 3,200-comparison deterministic check proves the NumPy
path agrees with the pure reference state machine across all 40 cells.

## Null controls

For each frozen top-three cell, FC runs a side-flipped path plus within-path
return shuffles seeded 1901, 1902, and 1903.  On executed TRAIN, actual
improvement exceeds every null for all three cells.  On the residual set, each
cell loses to at least one shuffle.  This separates a potentially
direction-specific executed effect from generic path harvesting, but the
executed effect still fails the predeclared book and multiplicity gates.

Full values are in `NULL_CONTROLS.json`; no null result is promotion-grade.

## What was built

`src/research_infra/exit_overlay.py` is a pure, default-off abstraction for the
six declared rule kinds.  It has no runtime integration, config read, broker
import, activation surface, or economic authority.  It provides:

- fail-closed cell and geometry validation;
- explicit true-UTC tick parsing, bid/ask normalization, and recorded-fill
  path eligibility;
- exact hard-stop, protective-floor, time-box, target, and terminal priority;
- full-cost weighted partial accounting;
- conservative two-order M1 replay;
- seeded tick-increment and M1-block shuffle primitives.

The analysis tool authenticates source manifests and physical hashes, streams
the CQ pool and sidecar, enforces composite identity, evaluates the 40-cell
family, freezes the top three on January TRAIN, then applies February and the
null suite.  It refuses when another train-engine process owns the local heavy
slot.  FC waited for CS to release that slot and started no full replay.

Because no cell qualifies, the next family is
`FC2_ENTRY_STATE_CONDITIONAL_EXIT_OVERLAY`, capped at 24 predeclared cells.  It
may use only entry-time cost band, session bucket, volatility band, and source
mode.  It must reuse the same January split, February attribution-only
boundary, full-cost partial accounting, and null suite.  Future MFE,
post-entry outcome fitting, March 2026, and live-forward outcomes remain
forbidden.  This is the repair path, not a verdict against the broad family.

## Corrections and look accounting

The identity control did its job and exposed two analyzer defects before
closeout:

1. the first executable version admitted prices between decision and delayed
   fill;
2. the next version indexed true-UTC lane ticks by preserved broker-wall
   `time_msc` instead of converted `ts_utc`/`time`.

Both were implementation defects, not opportunities to change the frozen
economics.  FC changed no cell, threshold, ranking rule, split, cost rule, or
null seed.  `LOOK_MANIFEST.json` preserves the schema-aborted run and both
invalidated output sets by physical hash.  It records 196 evaluation events:
40 schema-aborted, 52 pre-fill-invalid, 52 clock-invalid, and 52 valid final;
all are `FORENSIC_DIAGNOSTIC`, all are `billed:false`, and only the final 52
enter this result.

## Evidence map

| Artifact | SHA-256 |
|---|---|
| `OVERLAY_PROTOCOL.json` | `173b6be4dcd7a1e55248cd5f00dfcad4a09ebefd80b1739acc054ee04037f422` |
| `OVERLAY_RESULTS.json` | `106b3dfbe8e3e7c66e0c90ab27a81e8cebea973a1fb494e2cdccf38cac17d3ae` |
| `NULL_CONTROLS.json` | `07218f01fe33f5efafd502caf8963cbc5710d14f67ad9bbff7ad92d7e8c0b558` |
| `EXECUTED_OVERLAY_REPLAY.json` | `7e73e3d16d6f4ebbfec478d61e5cb449f41222ac8fab4defc253c6707a81ccf9` |
| `LOOK_MANIFEST.json` | `ca21eb4b58bc4342550542a8ca7d4d2b182c325fb33648c2dfcb34e9331bb147` |

The protocol was committed before outcomes at `4ef888ab7`; its final
clarifications remained pre-outcome.  The valid analyzer source HEAD is
`18cd2d23470fe3c613f5210c149e6bf4b4c24971`.  All five JSON artifacts carry
parseable schemas; the four generated outputs carry verified canonical
self-hashes.

## Verification

- The focused behavioral suite is **25 passed**, including exact ordered-tick
  identity, delayed-fill exclusion, true-UTC binding, full-cost partial
  accounting, conservative M1 ordering, null determinism, and fast/reference
  equivalence.
- The tool-derived FC blast radius is **78 passed, 0 failed, 0 errored** across
  the overlay, analyzer, standing-failure carrier, and implementation-state
  citation tests.
- The failure-set A/B is **1 bad -> 0 bad, 0 regressed**. The one baseline node
  now passing is a registered intermittent test that FC neither changed nor
  claims to repair; the proof claim is the empty regressed set. The exact scope
  and embedded captures are in `receipts/SESSION_FC_AB_RECEIPT.md`.
- The R2 drift scan still reports exactly three pre-existing paths:
  `src/components/broker_net_cost_engine.py` and the two historical JSONL
  ledgers. No FC path is R2-bound or newly drifted.
- The changed-path audit finds no config, activation, live entrypoint,
  broker-capable, or other forbidden surface in FC's diff.

## Safety and residual unknowns

- March 2026 outcomes read: **false**.
- Live-forward outcomes read: **false**.
- February fitted: **false**.
- Full or sealed replay started: **false**.
- VPS or broker mutation: **false**.
- Config, activation-token, promotion, or runtime change: **false**.
- Other worktrees were read-only.

M1 remains a conservative bar-order diagnostic, not headline bid/ask truth.
The executed sample remains small.  No challenge-month or live-forward
persistence is known because those outcomes were deliberately not read.

## What I got wrong

I initially treated “strictly post-decision” as sufficient even for delayed
fills, then trusted a raw `time_msc` integer in a lane whose authority is the
converted true-UTC text.  Both mistakes produced plausible but false rankings.
I caught them by refusing to hand-wave the weak identity reproduction,
invalidated the outputs rather than rationalizing them, added behavioral
regression tests, and reran the unchanged protocol.  The final ranking is the
third and only valid ranking above.
