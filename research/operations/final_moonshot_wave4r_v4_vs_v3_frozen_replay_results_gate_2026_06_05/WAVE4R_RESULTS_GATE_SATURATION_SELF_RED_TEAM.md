# Wave4R Results Gate Saturation Self Red Team

Generated: 2026-06-05T19:11:32.683504+00:00

## Verdict

Wave4R processed every readable May-26 dynamic-policy replay row and preserved
the full `214,536` row dynamic denominator after recovering absent native
Stage04 shard rows from Stage05 activated replay. It did not use broker-real
cash/PnL on frozen replay rows and did not mutate broker, MT5, VPS, paid API,
or remote state.

## Residual Source Gaps

- Missing May-26 dynamic-policy rows after Stage05 recovery:
  0.
- Fresh-day prop-firm drawdown is simulated in R units from replay outcomes.
  Original V4 live intent, pending/order lifecycle truth, and broker-real
  fill/cost/cash remain source/capture gaps on frozen replay rows.
- May-27 promoted dynamic-router replay rows are joined where available and
  used as the primary prior-system replay/proxy-R comparator. Net R remains
  source-gapped where historical cost, fill, swap, and lifecycle fields are
  absent.
- Exact same-bar ordering, live account risk headroom, open/pending broker
  state, and broker-real cost require ordered capture or historical source
  export where not already present. Synthetic replay fillability is inferred
  where ordered price action touches entry after the candidate decision.
- Day/session/candidate microscope fields now include holding duration,
  same-day/next-day/later-day exit class, 0.5R/1R/target/SL reachability,
  consolidation-near-1R-then-loss, giveback-to-loss, and fresh-day prop-firm
  drawdown simulation. Milestone clocks that require ordered LTF/tick transition
  rows remain explicit capture requirements rather than inferred timestamps.

## Anti-Deferral Check

The route computed selector/debate/scheduler/lifecycle/execution/geometry/exit
outputs before writing Wave5 handoff metadata. ML fields are byproducts, not a
closure substitute.
