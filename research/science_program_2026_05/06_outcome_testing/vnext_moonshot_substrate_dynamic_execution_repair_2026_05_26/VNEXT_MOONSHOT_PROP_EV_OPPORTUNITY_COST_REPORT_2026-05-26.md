# vNext Moonshot Stage07 Prop EV Opportunity Cost

Generated: `2026-05-26T04:43:20Z`

## Corrected Substrate

- Dynamic replay events: `214536`
- Corrected branch metric rows: `166`
- Prop EV attempt-stream rows: `1008`
- Fixed 1.5R labels are retained only as comparators; activation truth uses corrected dynamic policy labels.

## Best Reference Stream

- Branch: `origin_current_fvg_fill`
- Dynamic policy: `be_after_trigger`
- Prop policy: `ACCOUNT_ABANDON_OR_RESTART`
- Pass probability proxy: `0.981666130589`
- Account loss rate: `0.01801222258`
- Expected payout proxy, fee 599 payout 8000: `7842.539723`
- EV per terminal day: `7842.539723`

## Opportunity Cost

- Safe-but-dead selector rejections: `236`
- Rejections are emitted when a near-blocking safety selector allows almost no trades and loses to an opportunity-preserving alternative on EV or missed-winner opportunity cost.
- redacted_account attempts are segmented by challenge attempt and phase, with GMT+3 daily reset and static 10% max-loss rules.
